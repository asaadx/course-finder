"""Course Finder: Flask app factory and API routes.

Run locally with ``flask --app app run``; serve with ``gunicorn "app:create_app()"``.
"""

import json
import os
import re
import sqlite3

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

import db

MAX_QUERY_LENGTH = 20
MAX_BODY_BYTES = 1024  # request bodies are tiny ({"course_id": 1}); reject anything bigger

ENROLLMENT_SELECT = """
    SELECT e.id, e.enrolled_at,
           c.id AS course_id, c.code, c.title, c.description, c.credits
    FROM enrollments e
    JOIN courses c ON c.id = e.course_id
"""


def enrollment_json(row):
    return {
        "id": row["id"],
        "enrolled_at": row["enrolled_at"],
        "course": {
            "id": row["course_id"],
            "code": row["code"],
            "title": row["title"],
            "description": row["description"],
            "credits": row["credits"],
        },
    }
QUERY_PATTERN = re.compile(r"[A-Za-z0-9 ]*")  # ASCII letters, digits and spaces


def not_implemented():
    return jsonify({"error": "not implemented"}), 501


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.environ.get(
            "DATABASE", os.path.join(app.root_path, "data", "courses.db")
        ),
        MAX_CONTENT_LENGTH=MAX_BODY_BYTES,
    )
    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)

    @app.errorhandler(404)
    @app.errorhandler(405)
    @app.errorhandler(413)
    def handle_http_error(err: HTTPException):
        # Reuse Werkzeug's response so headers like Allow (on 405) are kept.
        response = err.get_response()
        response.data = json.dumps({"error": err.description})
        response.content_type = "application/json"
        return response

    @app.get("/")
    def index():
        """GET / -> 200 static/index.html (the single-page UI)."""
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/api/courses")
    def list_courses():
        """Search courses by code or title.

        GET /api/courses?q= -> 200 [{id, code, title, description, credits, enrolled}]
                             | 400 q over 20 chars or not letters/digits/spaces

        Code matching ignores spaces, so "coe628" finds "COE 628".
        """
        q = request.args.get("q", "").strip()
        if len(q) > MAX_QUERY_LENGTH:
            return jsonify({"error": f"Search must be at most {MAX_QUERY_LENGTH} characters."}), 400
        if not QUERY_PATTERN.fullmatch(q):
            return jsonify({"error": "Search can only contain letters, numbers and spaces."}), 400
        q = " ".join(q.split())  # collapse repeated spaces
        # The validation above rules out LIKE wildcards (% and _), so no escaping is needed.
        rows = db.get_db().execute(
            """
            SELECT c.id, c.code, c.title, c.description, c.credits,
                   e.id IS NOT NULL AS enrolled
            FROM courses c
            LEFT JOIN enrollments e ON e.course_id = c.id
            WHERE REPLACE(c.code, ' ', '') LIKE :code_p OR c.title LIKE :title_p
            ORDER BY c.code
            """,
            {"code_p": f"%{q.replace(' ', '')}%", "title_p": f"%{q}%"},
        ).fetchall()
        return jsonify([{**row, "enrolled": bool(row["enrolled"])} for row in rows])

    @app.get("/api/courses/<int:course_id>")
    def get_course(course_id):
        """GET /api/courses/<id> -> 200 {id, code, title, description, credits, enrolled} | 404 unknown course."""
        row = None
        if course_id <= db.SQLITE_MAX_INT:
            row = db.get_db().execute(
                """
                SELECT c.id, c.code, c.title, c.description, c.credits,
                       e.id IS NOT NULL AS enrolled
                FROM courses c
                LEFT JOIN enrollments e ON e.course_id = c.id
                WHERE c.id = ?
                """,
                (course_id,),
            ).fetchone()
        if row is None:
            return jsonify({"error": "Course not found."}), 404
        return jsonify({**row, "enrolled": bool(row["enrolled"])})

    @app.get("/api/enrollments")
    def list_enrollments():
        """GET /api/enrollments -> 200 [{id, course: {...}, enrolled_at}], oldest first."""
        rows = db.get_db().execute(ENROLLMENT_SELECT + " ORDER BY e.id").fetchall()
        return jsonify([enrollment_json(row) for row in rows])

    @app.post("/api/enrollments")
    def create_enrollment():
        """Enroll in a course. Body: {"course_id": int}.

        POST /api/enrollments -> 201 enrollment | 400 bad/missing course_id
        | 404 unknown course | 409 already enrolled | 413 body over 1 KB
        """
        body = request.get_json(silent=True)  # None if not JSON / wrong Content-Type
        if not isinstance(body, dict):
            return jsonify({"error": "Request body must be a JSON object."}), 400
        course_id = body.get("course_id")
        # type() rather than isinstance(): bool is a subclass of int, and True must be rejected.
        if type(course_id) is not int or not 1 <= course_id <= db.SQLITE_MAX_INT:
            return jsonify({"error": "course_id must be a positive integer."}), 400

        conn = db.get_db()
        if conn.execute("SELECT 1 FROM courses WHERE id = ?", (course_id,)).fetchone() is None:
            return jsonify({"error": "Course not found."}), 404
        try:
            cur = conn.execute("INSERT INTO enrollments (course_id) VALUES (?)", (course_id,))
            conn.commit()
        except sqlite3.IntegrityError:  # UNIQUE(course_id)
            return jsonify({"error": "You are already enrolled in this course."}), 409

        row = conn.execute(ENROLLMENT_SELECT + " WHERE e.id = ?", (cur.lastrowid,)).fetchone()
        return jsonify(enrollment_json(row)), 201

    return app
