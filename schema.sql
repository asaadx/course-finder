-- Course Finder schema. Running this file resets the database.
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;

CREATE TABLE courses (
  id          INTEGER PRIMARY KEY,
  code        TEXT    NOT NULL UNIQUE,  -- e.g. 'COE 528'
  title       TEXT    NOT NULL,
  description TEXT,
  credits     REAL
);

CREATE TABLE enrollments (
  id          INTEGER PRIMARY KEY,
  course_id   INTEGER NOT NULL UNIQUE REFERENCES courses(id),  -- UNIQUE: enroll once per course
  enrolled_at TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
