# Clasier

*A fast, single‑command way to scrape Duke course data into SQLite and serve it with a lightweight Flask API.*

---

## Features

| What it does | How |
|--------------|-----|
| Pulls every subject & term from DukeHub (PeopleSoft) | `SCC_GET_LOV` web‑service |
| Scrapes full course catalogs & class sections | `SSR_GET_COURSE_LISTINGS` & `SSR_GET_CLASSES` |
| Dynamically builds **6 relational tables** | `scripts/create_db.py` + `src/db.py` |
| Auto‑pivots course attributes (Areas of Knowledge, Modes of Inquiry, etc.) | Dynamic `ALTER TABLE` helper |
| Serves the DB via **Flask 3** endpoints | `src/main.py` |

---

## Quick‑start (Mac / Linux / WSL)

```bash
# 1 ─ Clone the repo
$ git clone https://github.com/kanthipm/clasier.git
$ cd clasier

# 2 ─ Create & activate a virtual environment (Python ≥3.11 recommended)
$ python3 -m venv .venv
$ source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3 ─ Install project dependencies
$ pip install --upgrade pip
$ pip install -r requirements.txt

# 4 ─ Build / refresh the SQLite database (~2–3 min)
$ python scripts/create_db.py     # outputs courses.db at project root

# 5 ─ Run the Flask dev server
$ export FLASK_APP=src.main       # or use the .flaskenv provided
$ export FLASK_ENV=development    # enables auto‑reload & debugger
$ flask run                       # http://localhost:5000
```

### Windows PowerShell
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/create_db.py
set FLASK_APP=src.main
set FLASK_ENV=development
flask run
```

---

## Repository layout

```
clasier/
├── scripts/
│   └── create_db.py      # scrape & populate courses.db
├── src/
│   ├── api_client.py     # wrapper around DukeHub web‑services
│   ├── db.py             # thin SQLite helper (create_table, insert_many, ...)
│   └── main.py           # Flask routes
├── requirements.txt      # pinned for reproducibility
└── .flaskenv             # convenience vars for `flask run`
```

---

## Regenerating the database

Whenever Duke releases a new term or you just want fresh data:

```bash
$ python scripts/create_db.py
```
The script will drop & recreate the 6 tables in the existing `courses.db`. No manual cleanup needed.

---

## Updating dependencies

```bash
$ pip install --upgrade <package>
$ pip freeze > requirements.txt   # if you want to re‑pin versions
```

We intentionally pin exact versions to ensure Heroku / Fly.io deploys are deterministic.

---

## Common issues

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: src.db` | You’re running from a different directory—`cd clasier` first |
| `sqlite3.OperationalError: no such table` | Run `python scripts/create_db.py` again |
| `flask: command not found` | Activate the virtual‑env or `pip install flask` |

---

## License

MIT © 2025 Kanthi Makineedi & Camden Chin

