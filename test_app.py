import tempfile
import unittest
from pathlib import Path
from app import JobTracker


class JobTrackerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.tracker = JobTracker(Path(self.temp.name) / "test.sqlite3")

    def tearDown(self):
        self.temp.cleanup()

    def test_add_and_read_application(self):
        app_id = self.tracker.add("Example Co", "Engineer", applied_date="2026-10-01", deadline="2026-10-30", notes="Follow up")
        row = self.tracker.get(app_id)
        self.assertEqual((row["employer"], row["role"], row["stage"]), ("Example Co", "Engineer", "Applied"))
        self.assertEqual(row["notes"], "Follow up")

    def test_edit_and_delete(self):
        app_id = self.tracker.add("Example Co", "Engineer")
        self.tracker.update(app_id, "Example Co", "Senior Engineer", "Interview", deadline="2026-11-01")
        self.assertEqual(self.tracker.get(app_id)["stage"], "Interview")
        self.tracker.delete(app_id)
        with self.assertRaises(KeyError):
            self.tracker.get(app_id)

    def test_stage_filter(self):
        self.tracker.add("A", "One", "Applied")
        self.tracker.add("B", "Two", "Interview")
        self.assertEqual([r["employer"] for r in self.tracker.list(stage="Interview")], ["B"])

    def test_overdue_excludes_closed_stages(self):
        self.tracker.add("A", "One", deadline="2026-10-01")
        self.tracker.add("B", "Two", "Rejected", deadline="2026-10-01")
        self.tracker.add("C", "Three", deadline="2026-10-15")
        rows = self.tracker.list(overdue=True, today="2026-10-14")
        self.assertEqual([r["employer"] for r in rows], ["A"])

    def test_validation(self):
        for values in [(" ", "Dev", "Applied"), ("Co", " ", "Applied"), ("Co", "Dev", "Unknown")]:
            with self.assertRaises(ValueError):
                self.tracker.add(*values)
        with self.assertRaises(ValueError):
            self.tracker.add("Co", "Dev", deadline="soon")

    def test_missing_ids_raise(self):
        with self.assertRaises(KeyError):
            self.tracker.delete(404)
        with self.assertRaises(KeyError):
            self.tracker.update(404, "A", "B", "Applied")


if __name__ == "__main__":
    unittest.main()
