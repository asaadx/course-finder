"""SQLite connection helpers: one connection per request, closed at teardown."""

import os
import sqlite3

from flask import current_app, g

SQLITE_MAX_INT = 2**63 - 1  # larger Python ints overflow when bound as SQLite INTEGER


def get_db():
    """Return this request's connection, opening it on first use."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row  # rows behave like dicts
        g.db.execute("PRAGMA foreign_keys = ON")  # SQLite leaves FKs off by default
    return g.db


def close_db(exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create (or reset) all tables from schema.sql."""
    os.makedirs(os.path.dirname(current_app.config["DATABASE"]) or ".", exist_ok=True)
    with current_app.open_resource("schema.sql") as f:
        get_db().executescript(f.read().decode("utf-8"))


def init_app(app):
    app.teardown_appcontext(close_db)
