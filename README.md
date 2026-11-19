# Course Finder

A small web app where learners search for courses and enroll in them.
Built with Flask, SQLite and plain HTML/CSS/JavaScript.

> **Current status:** search, course lookup, enrolling and the Docker image all work. Not built: unenrolling.

---

## 1. Requirements

- **Python 3.10+**: `python3 --version`
- **git**
- On Ubuntu, install Python's venv module if it's missing:
  ```bash
  sudo apt update && sudo apt install -y python3 python3-venv python3-pip
  ```

## 2. Install

From the repo root:

```bash
python3 -m venv .venv            # create an isolated Python environment (once)
source .venv/bin/activate        # activate it (in every new terminal)
pip install -r requirements.txt  # install Flask, gunicorn, pytest
```

`requirements.txt` lists the Python packages this project needs, pinned to exact versions, so everyone gets the same
setup. You'll know the venv is active when your prompt starts with `(.venv)`. Run `deactivate` to leave it.

## 3. Create the database

```bash
python seed.py
```

This creates `data/courses.db` with about 12 mock TMU Computer Engineering 3rd-year courses. Run it again at any
time to **reset** the database. Re-running clears all enrollments.

## 4. Run the app

```bash
flask --app app run --debug
```

Open **http://127.0.0.1:5000**. Press `Ctrl+C` to stop.

- **Port 5000 already in use?** On macOS, AirPlay Receiver uses it. Add `--port 5001` and open that port instead.
- **Use a different database file:** `DATABASE=/path/to/other.db flask --app app run`

## 5. Use it

- **Search:** type in the search bar. Results update as you type, matching on course code (`COE 528`) or title.
  An empty search shows every course.
- **Enroll:** click **Enroll** on a result. The course appears in the **Enrolled in** sidebar right away.
  You can only enroll in each course once.
- Unenrolling isn't supported yet.

## 6. Run the tests

Tests sit next to the code they cover (`test_app.py` next to `app.py`, `test_db.py` next to `db.py`).

```bash
pytest                         # run everything
pytest -v                      # list each test by name
pytest test_app.py             # one file
pytest -k enroll               # only tests whose name contains "enroll"
```

The tests use a temporary database, so they never touch `data/courses.db`.

## 7. API reference

All responses are JSON. Errors always look like `{"error": "message"}`.

| Method | Path | Description | Responses |
|---|---|---|---|
| GET | `/api/courses?q=<text>` | Search courses by code or title (empty `q` returns all; spaces ignored in codes, so `coe628` works). `q`: max 20 chars, letters/digits/spaces only | 200, 400 |
| GET | `/api/courses/<id>` | One course | 200, 404 |
| GET | `/api/enrollments` | Courses you're enrolled in | 200 |
| POST | `/api/enrollments` | Enroll. Body: `{"course_id": 1}` (positive integer; body max 1 KB) | 201, 400, 404, 409 (already enrolled), 413 |

Try it with curl while the app is running:

```bash
curl 'http://127.0.0.1:5000/api/courses?q=coe'
curl -X POST http://127.0.0.1:5000/api/enrollments \
     -H 'Content-Type: application/json' -d '{"course_id": 1}'
curl http://127.0.0.1:5000/api/enrollments
```

## 8. Run with Docker

The image is based on Ubuntu 24.04 and runs the app with gunicorn on port 8000, as a non-root user.
You only need Docker; Python is installed inside the image. On an Ubuntu server, install Docker with
`sudo apt install -y docker.io`. On a Mac, use Docker Desktop.

```bash
docker build -t course-finder .
docker run -d --name course-finder -p 8000:8000 -v course-finder-data:/app/data course-finder
```

Open **http://localhost:8000**.

- **First start:** the container seeds the database automatically.
- **Restarts keep enrollments:** the database lives in the `course-finder-data` volume.
- **Useful commands:**
  ```bash
  docker logs -f course-finder        # view server logs
  docker ps                           # STATUS shows (healthy) once the app responds
  docker exec course-finder python3 seed.py   # reset the DB (wipes enrollments)
  docker rm -f course-finder          # stop and remove the container (the volume stays)
  docker volume rm course-finder-data # delete the data too
  ```

## Troubleshooting

| Problem | Fix |
|---|---|
| `command not found: flask` / `No module named flask` | The venv isn't active. Run `source .venv/bin/activate`. |
| `Address already in use` | Use another port: `flask --app app run --port 5001` |
| `no such table: courses` | Run `python seed.py` first. |
| Page loads but shows "Could not load courses" | The API isn't returning data. Check the terminal running Flask for errors. |

## Project layout

See [`wiki/codebase-map.md`](wiki/codebase-map.md) for what each file does.
