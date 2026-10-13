"""Local SQLite job application tracker."""
from datetime import date
import sqlite3
from contextlib import contextmanager
from pathlib import Path

STAGES = ("Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn")
ACTIVE_STAGES = ("Applied", "Screening", "Interview", "Offer")


def _date(value, field):
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a valid date in YYYY-MM-DD format") from exc


class JobTracker:
    def __init__(self, database="job_applications.sqlite3"):
        self.database = str(database)
        self.initialize()

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self):
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY, employer TEXT NOT NULL CHECK(length(trim(employer)) > 0),
                role TEXT NOT NULL CHECK(length(trim(role)) > 0), stage TEXT NOT NULL,
                applied_date TEXT, deadline TEXT, notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CHECK(stage IN ('Applied','Screening','Interview','Offer','Rejected','Withdrawn'))
            )""")

    def add(self, employer, role, stage="Applied", applied_date=None, deadline=None, notes=""):
        employer, role = employer.strip(), role.strip()
        if not employer or not role:
            raise ValueError("Employer and role are required")
        if stage not in STAGES:
            raise ValueError(f"Stage must be one of: {', '.join(STAGES)}")
        with self.connect() as db:
            cursor = db.execute("INSERT INTO applications (employer, role, stage, applied_date, deadline, notes) VALUES (?, ?, ?, ?, ?, ?)",
                                (employer, role, stage, _date(applied_date, "Applied date"), _date(deadline, "Deadline"), notes.strip()))
            return cursor.lastrowid

    def update(self, application_id, employer, role, stage, applied_date=None, deadline=None, notes=""):
        employer, role = employer.strip(), role.strip()
        if not employer or not role:
            raise ValueError("Employer and role are required")
        if stage not in STAGES:
            raise ValueError(f"Stage must be one of: {', '.join(STAGES)}")
        with self.connect() as db:
            cursor = db.execute("""UPDATE applications SET employer=?, role=?, stage=?, applied_date=?, deadline=?, notes=?, updated_at=CURRENT_TIMESTAMP
                                  WHERE id=?""", (employer, role, stage, _date(applied_date, "Applied date"), _date(deadline, "Deadline"), notes.strip(), application_id))
            if not cursor.rowcount:
                raise KeyError(f"No application with ID {application_id}")

    def delete(self, application_id):
        with self.connect() as db:
            cursor = db.execute("DELETE FROM applications WHERE id=?", (application_id,))
            if not cursor.rowcount:
                raise KeyError(f"No application with ID {application_id}")

    def list(self, stage=None, overdue=False, today=None):
        if stage is not None and stage not in STAGES:
            raise ValueError(f"Stage must be one of: {', '.join(STAGES)}")
        query, params = "SELECT * FROM applications WHERE 1=1", []
        if stage:
            query += " AND stage=?"
            params.append(stage)
        if overdue:
            query += " AND deadline < ? AND stage IN ('Applied','Screening','Interview','Offer')"
            params.append(_date(today or date.today().isoformat(), "Today"))
        query += " ORDER BY COALESCE(deadline, '9999-12-31'), employer COLLATE NOCASE, role COLLATE NOCASE"
        with self.connect() as db:
            return [dict(row) for row in db.execute(query, params)]

    def get(self, application_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM applications WHERE id=?", (application_id,)).fetchone()
            if row is None:
                raise KeyError(f"No application with ID {application_id}")
            return dict(row)


def _print_applications(rows):
    if not rows:
        print("No matching applications.")
    for item in rows:
        print(f"#{item['id']} {item['employer']} — {item['role']} | {item['stage']} | applied {item['applied_date'] or '—'} | deadline {item['deadline'] or '—'}")
        if item["notes"]:
            print(f"   {item['notes']}")


def main():
    tracker = JobTracker()
    while True:
        print("\nJob Application Tracker | 1 List  2 Add  3 Edit  4 Delete  5 Overdue  0 Exit")
        choice = input("> ").strip()
        try:
            if choice == "0":
                break
            if choice == "1":
                _print_applications(tracker.list())
            elif choice == "2":
                employer = input("Employer: ")
                role = input("Role: ")
                stage = input("Stage (Applied): ").strip() or "Applied"
                applied = input("Applied date YYYY-MM-DD (optional): ").strip() or None
                deadline = input("Deadline YYYY-MM-DD (optional): ").strip() or None
                notes = input("Notes (optional): ")
                print(f"Saved application #{tracker.add(employer, role, stage, applied, deadline, notes)}")
            elif choice == "3":
                item = tracker.get(int(input("Application ID: ")))
                tracker.update(item["id"], input(f"Employer [{item['employer']}]: ").strip() or item["employer"],
                               input(f"Role [{item['role']}]: ").strip() or item["role"],
                               input(f"Stage [{item['stage']}]: ").strip() or item["stage"],
                               input(f"Applied date [{item['applied_date'] or ''}]: ").strip() or item["applied_date"],
                               input(f"Deadline [{item['deadline'] or ''}]: ").strip() or item["deadline"],
                               input(f"Notes [{item['notes']}]: ").strip() or item["notes"])
                print("Application updated.")
            elif choice == "4":
                tracker.delete(int(input("Application ID to delete: ")))
                print("Application deleted.")
            elif choice == "5":
                _print_applications(tracker.list(overdue=True))
            else:
                print("Choose one of the listed options.")
        except (ValueError, KeyError) as exc:
            print(f"Could not complete request: {exc}")


if __name__ == "__main__":
    main()

