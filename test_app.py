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


@pytest.mark.parametrize("q", ["coe628", "COE628", "coe 628", "coe  628"])
def test_code_match_ignores_spaces(client, q):
    assert codes(search(client, q)) == ["COE 628"]


def test_repeated_spaces_in_title_are_collapsed(client):
    assert codes(search(client, "operating   systems")) == ["COE 628"]


def test_no_match_returns_empty_list(client):
    assert search(client, "zzz") == []


def test_query_of_exactly_20_chars_is_allowed(client):
    assert search(client, "a" * 20) == []


def test_length_is_checked_after_trimming(client):
    assert search(client, "  " + "a" * 20 + "  ") == []


def bad_search(client, q):
    resp = client.get("/api/courses", query_string={"q": q})
    assert resp.status_code == 400
    return resp.get_json()["error"]


def test_query_over_20_chars_is_rejected(client):
    assert "20 characters" in bad_search(client, "a" * 21)


@pytest.mark.parametrize("q", [
    "%", "_", "\\",           # LIKE wildcards / escape char
    "' OR 1=1 --",            # SQL injection
    "<script>",               # markup
    "COE-628", "c++",         # punctuation
    "日本語", "🙂", "é",       # non-ASCII
    "coe\t628", "coe\n628",   # whitespace other than spaces
])
def test_query_with_disallowed_characters_is_rejected(client, q):
    assert "letters, numbers and spaces" in bad_search(client, q)


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


# ---------- GET /api/courses/<id> ----------

def test_get_course_by_id(client):
    resp = client.get("/api/courses/4")
    assert resp.status_code == 200
    assert resp.get_json() == {
        "id": 4,
        "code": "COE 628",
        "title": "Operating Systems",
        "description": "Processes, threads, scheduling, synchronization, memory and file systems.",
        "credits": 1.0,
        "enrolled": False,
    }


def test_get_course_shows_enrolled(app, client):
    with app.app_context():
        get_db().execute("INSERT INTO enrollments (course_id) VALUES (4)")
        get_db().commit()
    assert client.get("/api/courses/4").get_json()["enrolled"] is True


@pytest.mark.parametrize("path", [
    "/api/courses/0",
    "/api/courses/9999",
    "/api/courses/99999999999999999999",  # beyond SQLite's 64-bit INTEGER
    "/api/courses/-1",                    # <int:> rejects negatives
    "/api/courses/abc",                   # <int:> rejects non-numbers
    "/api/courses/1.5",
])
def test_get_unknown_or_invalid_course_is_404_json(client, path):
    resp = client.get(path)
    assert resp.status_code == 404
    assert "error" in resp.get_json()
