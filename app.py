"""Course Finder: Flask app factory and API routes.

Run locally with ``flask --app app run``; serve with ``gunicorn "app:create_app()"``.
"""

import json
import os

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

import db


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
        """
        q = request.args.get("q", "")  # noqa: F841 (used once search is implemented)
        return not_implemented()

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
