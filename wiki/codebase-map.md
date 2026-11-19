# Codebase map

> Status: everything is implemented: DB layer, frontend, all API routes and the Docker image.
> Update this page as files get implemented.

## Overview

The browser (`static/`) calls a Flask REST API (`app.py`). The API reads and writes a SQLite database through `db.py`.
There is a single implicit learner, with no users or auth.

```
static/app.js  --fetch-->  app.py (routes)  -->  db.py  -->  SQLite file (schema.sql, seed.py)
```

## Files

| Path | Purpose |
|---|---|
| `app.py` | Flask app factory and routes: `GET /api/courses?q=`, `GET /api/courses/<id>`, `GET`/`POST /api/enrollments`, and `/` (serves `static/index.html`). JSON 404/405 handlers. Calls `db.init_app(app)`. API routes not yet implemented return `501`; each docstring states its contract. |
| `db.py` | Connection helpers: `get_db()` (one connection per request, stored on `g`), `close_db()` (runs at teardown), `init_db()` (runs `schema.sql`, creating the `data/` dir if needed), `init_app()`. `PRAGMA foreign_keys = ON` on every connection. The DB path comes from `DATABASE` config/env (default `data/courses.db`). |
| `schema.sql` | Drops and recreates `courses` (`code` TEXT UNIQUE) and `enrollments` (`course_id` UNIQUE FK). Running it resets the DB. |
| `seed.py` | `python seed.py` resets the DB and inserts 12 mock TMU 3rd-year courses. `COURSES` and `seed_db(db)` are reused by the tests. |
| `static/index.html` | Page markup: search bar plus an "Enrolled in" sidebar. |
| `static/app.js` | Search-as-you-type (debounced), rendering results and the sidebar, and the enroll button handler. |
| `static/styles.css` | Two-column layout: sidebar and the search/results area. |
| `test_app.py` | Collocated pytest tests for the API routes (Flask test client, temp DB). |
| `test_db.py` | Collocated pytest tests for the schema constraints (UNIQUE, FK) and seeding. |
| `requirements.txt` | Python dependencies, pinned with `==`: `flask`, `gunicorn`, `pytest`. |
| `Dockerfile` / `.dockerignore` | Ubuntu 24.04 image: Python 3.12 venv, gunicorn on port 8000, non-root `app` user, healthcheck. The SQLite file lives in the `/app/data` volume. |
| `docker-entrypoint.sh` | Container start script: seeds the DB if the file doesn't exist yet, then starts gunicorn. |
| `README.md` | Setup, how to run locally and in Docker, endpoint reference, curl examples. |
| `CLAUDE.md` | Workflow rules for agents (branches, worktrees, commits, PRs). |
| `wiki/` | This wiki. Start at [index.md](index.md). |
