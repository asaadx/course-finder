"""Course Finder: Flask app factory and API routes.

Run locally with ``flask --app app run``; serve with ``gunicorn "app:create_app()"``.
"""

import json
import os
import re

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

import db

MAX_QUERY_LENGTH = 20
QUERY_PATTERN = re.compile(r"[A-Za-z0-9 ]*")  # ASCII letters, digits and spaces


def not_implemented():
    return jsonify({"error": "not implemented"}), 501


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.environ.get(
            "DATABASE", os.path.join(app.root_path, "data", "courses.db")
        ),
    )
    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)

    @app.errorhandler(404)
    @app.errorhandler(405)
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
        """GET /api/courses/<id> -> 200 course | 404 unknown course."""
        return not_implemented()

    @app.get("/api/enrollments")
    def list_enrollments():
        """GET /api/enrollments -> 200 [{id, course: {...}, enrolled_at}]."""
        return not_implemented()

    @app.post("/api/enrollments")
    def create_enrollment():
        """Enroll in a course. Body: {"course_id": int}.

        POST /api/enrollments -> 201 enrollment | 400 bad/missing course_id
        | 404 unknown course | 409 already enrolled
        """
        return not_implemented()

    return app
