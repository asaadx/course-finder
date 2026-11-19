# Codebase map

> Status: every file is still an empty scaffold. This page describes what each file is *meant* to hold.
> Update it as files get implemented.

## Overview

The browser (`static/`) calls a Flask REST API (`app.py`). The API reads and writes a SQLite database through `db.py`.
There is a single implicit learner, with no users or auth.

```
static/app.js  --fetch-->  app.py (routes)  -->  db.py  -->  SQLite file (schema.sql, seed.py)
```

## Files

| Path | Purpose |
|---|---|
| `app.py` | Flask app factory and routes: `GET /api/courses?q=`, `GET /api/courses/<id>`, `GET`/`POST /api/enrollments`, and `/` (serves `static/index.html`). |
| `db.py` | Connection helpers: `get_db()` (one connection per request, stored on `g`), `close_db()` (runs at teardown), `init_db()` (runs `schema.sql`). The DB path comes from `DATABASE` config/env. |
| `schema.sql` | `CREATE TABLE` statements for `courses` and `enrollments` (`UNIQUE(course_id)`). |
| `seed.py` | Resets the DB and inserts about 12 mock TMU Computer Engineering 3rd-year courses. |
| `static/index.html` | Page markup: search bar plus an "Enrolled in" sidebar. |
| `static/app.js` | Search-as-you-type (debounced), rendering results and the sidebar, and the enroll button handler. |
| `static/styles.css` | Two-column layout: sidebar and the search/results area. |
| `test_app.py` | Collocated pytest tests for the API routes (Flask test client, temp DB). |
| `test_db.py` | Collocated pytest tests for the `db.py` helpers. |
| `requirements.txt` | Python dependencies: `flask`, `gunicorn`, `pytest`. |
| `Dockerfile` / `.dockerignore` | Container image (`python:3.12-slim` + gunicorn on port 8000). The SQLite file goes in a mounted volume. |
| `README.md` | Setup, how to run locally and in Docker, endpoint reference, curl examples. |
| `CLAUDE.md` | Workflow rules for agents (branches, worktrees, commits, PRs). |
| `wiki/` | This wiki. Start at [index.md](index.md). |
