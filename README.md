# Job Application Tracking System

A small, private-by-default job search tracker built with Python 3.13, SQLite, and the standard library. Track employer, role, application stage, dates/deadlines, and notes. Filter by stage or see overdue deadlines; rejected and withdrawn applications are not considered overdue.

## Run

```powershell
py -3.13 app.py
```

If the Python launcher is unavailable, run with your Python 3.13 executable, for example:

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" app.py
```

The first run creates `job_applications.sqlite3` beside the program. The interactive menu supports create, list, edit, delete, and overdue views. Dates use `YYYY-MM-DD`; leave optional dates blank. The database is local and excluded from Git.

## Tests

```powershell
py -3.13 -m unittest -v
```

No external packages are required. This is a local tool; back up the SQLite file if you need to preserve your records.
