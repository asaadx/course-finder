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


# ---------- /api/enrollments ----------

def enroll(client, body=None, **kwargs):
    return client.post("/api/enrollments", json=body, **kwargs)


def test_no_enrollments_initially(client):
    resp = client.get("/api/enrollments")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_enroll_returns_201_with_enrollment(client):
    resp = enroll(client, {"course_id": 4})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["course"] == {
        "id": 4,
        "code": "COE 628",
        "title": "Operating Systems",
        "description": "Processes, threads, scheduling, synchronization, memory and file systems.",
        "credits": 1.0,
    }
    assert isinstance(body["id"], int) and body["enrolled_at"]


def test_one_enrollment_is_listed(client):
    created = enroll(client, {"course_id": 4}).get_json()
    assert client.get("/api/enrollments").get_json() == [created]


def test_enrollment_is_listed_and_flagged_in_search(client):
    enroll(client, {"course_id": 4})
    enroll(client, {"course_id": 1})
    listed = client.get("/api/enrollments").get_json()
    assert [e["course"]["code"] for e in listed] == ["COE 628", "COE 528"]  # oldest first
    flags = {c["code"]: c["enrolled"] for c in search(client)}
    assert flags["COE 628"] and flags["COE 528"] and sum(flags.values()) == 2


def test_enrolling_twice_is_409(client):
    assert enroll(client, {"course_id": 4}).status_code == 201
    resp = enroll(client, {"course_id": 4})
    assert resp.status_code == 409
    assert "already enrolled" in resp.get_json()["error"]
    assert len(client.get("/api/enrollments").get_json()) == 1


@pytest.mark.parametrize("course_id", [9999, 2**63 - 1])
def test_enrolling_in_unknown_course_is_404(client, course_id):
    resp = enroll(client, {"course_id": course_id})
    assert resp.status_code == 404
    assert resp.get_json() == {"error": "Course not found."}


@pytest.mark.parametrize("course_id", [
    "4", 4.0, 1.5, True, False, None, 0, -1, 2**63, [4], {"id": 4},
])
def test_invalid_course_id_is_400(client, course_id):
    resp = enroll(client, {"course_id": course_id})
    assert resp.status_code == 400
    assert "positive integer" in resp.get_json()["error"]


def test_missing_course_id_is_400(client):
    assert enroll(client, {}).status_code == 400


@pytest.mark.parametrize("kwargs", [
    {"json": [4]},                                                # JSON, but not an object
    {"json": "4"},
    {"data": "{not json", "content_type": "application/json"},   # malformed JSON
    {"data": "course_id=4", "content_type": "application/x-www-form-urlencoded"},
    {},                                                           # no body at all
])
def test_non_object_body_is_400(client, kwargs):
    resp = client.post("/api/enrollments", **kwargs)
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "Request body must be a JSON object."}


def test_oversized_body_is_413_json(client):
    resp = client.post("/api/enrollments", data='{"course_id": 4, "x": "' + "a" * 2000 + '"}',
                       content_type="application/json")
    assert resp.status_code == 413
    assert "error" in resp.get_json()


def test_extra_fields_are_ignored(client):
    assert enroll(client, {"course_id": 4, "extra": "ignored"}).status_code == 201
