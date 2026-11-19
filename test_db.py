import sqlite3

import pytest

from app import create_app
from db import get_db, init_db
from seed import COURSES, seed_db


@pytest.fixture
def db(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
        seed_db(get_db())
        yield get_db()


def test_seed_loads_all_courses(db):
    assert db.execute("SELECT COUNT(*) FROM courses").fetchone()[0] == len(COURSES)


def test_course_code_is_unique(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO courses (code, title) VALUES ('COE 528', 'Duplicate')")


def test_cannot_enroll_in_same_course_twice(db):
    db.execute("INSERT INTO enrollments (course_id) VALUES (1)")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO enrollments (course_id) VALUES (1)")


def test_enrollment_requires_existing_course(db):
    with pytest.raises(sqlite3.IntegrityError):  # foreign_keys pragma is on
        db.execute("INSERT INTO enrollments (course_id) VALUES (9999)")


def test_init_db_resets_data(db):
    db.execute("INSERT INTO enrollments (course_id) VALUES (1)")
    db.commit()
    init_db()
    assert db.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0] == 0
