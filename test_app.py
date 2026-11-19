import pytest

from app import create_app
from db import get_db, init_db
from seed import COURSES, seed_db


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    with app.app_context():
        init_db()
        seed_db(get_db())
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def search(client, q=None):
    resp = client.get("/api/courses", query_string={} if q is None else {"q": q})
    assert resp.status_code == 200
    return resp.get_json()


def codes(courses):
    return [c["code"] for c in courses]


# ---------- GET /api/courses ----------

@pytest.mark.parametrize("q", [None, "", "   "])
def test_empty_query_returns_all_courses(client, q):
    assert len(search(client, q)) == len(COURSES)


def test_results_are_ordered_by_code(client):
    result = codes(search(client))
    assert result == sorted(result)


def test_matches_code_case_insensitively(client):
    assert codes(search(client, "coe")) == [
        "COE 528", "COE 538", "COE 608", "COE 628", "COE 691", "COE 692",
    ]


def test_matches_partial_code(client):
    assert codes(search(client, "COE 6")) == ["COE 608", "COE 628", "COE 691", "COE 692"]


def test_matches_title_across_departments(client):
    assert codes(search(client, "systems")) == [
        "COE 538", "COE 628", "ELE 532", "ELE 635", "ELE 639",
    ]


def test_query_is_trimmed_and_case_insensitive(client):
    assert codes(search(client, "  OPERATING  ")) == ["COE 628"]


@pytest.mark.parametrize("q", ["zzz", "日本語", "🙂"])
def test_no_match_returns_empty_list(client, q):
    assert search(client, q) == []


@pytest.mark.parametrize("q", ["%", "_", "\\"])
def test_like_wildcards_match_literally(client, q):
    assert search(client, q) == []


def test_sql_injection_is_treated_as_text(client):
    assert search(client, "' OR 1=1 --") == []


def test_course_has_expected_shape(client):
    course = search(client, "COE 628")[0]
    assert course == {
        "id": 4,
        "code": "COE 628",
        "title": "Operating Systems",
        "description": "Processes, threads, scheduling, synchronization, memory and file systems.",
        "credits": 1.0,
        "enrolled": False,
    }


def test_enrolled_flag_reflects_enrollments(app, client):
    with app.app_context():
        get_db().execute("INSERT INTO enrollments (course_id) VALUES (4)")
        get_db().commit()
    enrolled = {c["code"]: c["enrolled"] for c in search(client)}
    assert enrolled["COE 628"] is True
    assert sum(enrolled.values()) == 1
