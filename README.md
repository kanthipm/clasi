# CLASIER – Intelligent Duke Schedule Builder

CLASIER is a web app that wraps DukeHub data in a cleaner, smarter interface. It lets you search every course **faster**, filter by graduation requirements in one click, preview professor ratings, and save full‑semester schedules without ever leaving the page.

> **Heads‑up**: CLASIER is a student‑run project and is **not** endorsed by Duke University or DukeHub.

---

## ✨ Key Features

* **Blazing‑fast search** – full‑text and faceted search across course code, title, description, AOK, MOI, and meeting pattern.
* **Graduation requirement filters** – instantly filter by *Area of Knowledge* or *Modes of Inquiry* instead of checking every course one by one.
* **Professor insights** – RateMyProfessor scores and recent student reviews sit right next to each listing.
* **Auto‑sorted results** – best‑rated professors float to the top by default (toggle anytime).
* **Schedule builder** – drag classes onto a calendar grid, detect time conflicts, and export an iCalendar file.
* **Dark‑mode friendly UI** – built with Tailwind + DaisyUI for snappy, accessible styling.

---

## 🏗️ Project Structure

```text
clasier/
├── app/                # Flask blueprints, templates, static assets
├── scripts/            # One‑off helpers (scraper, db init, seed data, export)
├── requirements.txt    # Python dependencies
├── .env.example        # Copy → .env and tweak values as needed
└── run.py              # Dev entry point (`flask --app run.py run`)
```

---

## 🚀 Quick‑start

Below is the fastest path to spin up CLASIER locally. Commands are for macOS/Linux; adjust for Windows.

```bash
# 1. Clone the repo
$ git clone https://github.com/your‑org/clasier.git && cd clasier

# 2. Set up Python (3.10 or newer is recommended)
$ pyenv install 3.10.7                      # only once
$ pyenv virtualenv 3.10.7 clasier‑env       # only once
$ pyenv local clasier‑env                   # activate

# 3. Install dependencies
$ pip install -r requirements.txt

# 4. Create an .env file (copy defaults)
$ cp .env.example .env

# 5. Initialize the database and pull course data
$ python scripts/init_db.py                 # creates empty SQLite db
$ python scripts/scrape_courses.py --term 2025SP

# 6. Fire up the dev server
$ export FLASK_APP=run.py
$ flask run                                  # visit http://127.0.0.1:5000
```

### Common gotchas

* **`flask: command not found`** – make sure your virtual environment is active (`pyenv local clasier‑env` or `source venv/bin/activate`).
* Using **`pyenv`** for the first time? Add the following to your shell profile:

  ```bash
  eval "$(pyenv init -)"
  eval "$(pyenv virtualenv‑init -)"
  ```

---

## 🔧 Configuration

| Variable       | Default                   | Purpose                        |
| -------------- | ------------------------- | ------------------------------ |
| `FLASK_ENV`    | `development`             | Switches debug mode            |
| `DATABASE_URL` | `sqlite:///db/clasier.db` | SQLAlchemy connection string   |
| `SECRET_KEY`   | random string             | Flask session signing          |
| `RMP_API_KEY`  | *(optional)*              | RateMyProfessor unofficial API |

Create a `.env` file in the project root and override what you need.

---

## 🗄️ Database Schema

CLASIER uses **SQLite** in dev and **PostgreSQL** in production. Key tables:

* `courses` – canonical course records scraped from DukeHub
* `course_offerings` – term‑specific metadata (capacity, meeting times)
* `professors` – instructor roster with cached RMP scores
* `reviews` – student comments pulled by scraper

Migrations are handled with **Flask‑Migrate / Alembic**.

```bash
flask db migrate -m "Add waitlist column"
flask db upgrade
```

---

## 🧪 Testing

```bash
pytest -q
```

The test suite spins up an in‑memory SQLite instance and hits the Flask test client.

---

## 📦 Production Deployment (Heroku‑style)

```bash
heroku create clasier‑demo
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set SECRET_KEY="$(openssl rand -hex 32)"
# build + release
git push heroku main
```

*Uses Gunicorn behind the scenes; Procfile provided.*

---

## 🤝 Contributing

Pull requests are welcome! Open an issue first to discuss major changes. Make sure your code passes **black**, **isort**, and **pytest** before submitting.

```bash
pip install -r requirements-dev.txt
pre-commit install
```

---

## 📄 License

This project is licensed under the MIT License – see `LICENSE` for details.

---

### Acknowledgements

* Scraping inspired by the brilliant work of the [Duke SchedulAR](https://github.com/…) team.
* RateMyProfessor data via the open **rmp‑scraper** project.
