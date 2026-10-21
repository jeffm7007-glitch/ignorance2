"""Pluggable fact-layer sources.

Jeff's rule: the data harness runs on the owner's database, not the vendor's.
JSON ships in the box; your SQL is the production backend. The adapter below
uses only the standard-library sqlite3 module (zero dependencies preserved);
for Postgres/MySQL, hand any DB-API connection to load_facts_sql — the same
contract applies.
"""

from __future__ import annotations

import sqlite3

from .core import Fact

SCHEMA = """
CREATE TABLE IF NOT EXISTS facts (
    id     TEXT PRIMARY KEY,
    text   TEXT NOT NULL,
    source TEXT NOT NULL,
    tags   TEXT DEFAULT ''
)
"""


def init_sqlite(path: str) -> sqlite3.Connection:
    """Create (or open) a SQLite fact layer and ensure the schema exists."""
    conn = sqlite3.connect(path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def add_fact_sql(conn, fact: Fact) -> None:
    """Insert or replace one fact record."""
    conn.execute(
        "INSERT OR REPLACE INTO facts (id, text, source, tags) VALUES (?, ?, ?, ?)",
        (fact.id, fact.text, fact.source, ",".join(fact.tags)),
    )
    conn.commit()


def load_facts_sql(conn) -> list[Fact]:
    """Load the fact layer from any DB-API connection exposing a `facts`
    table with columns: id, text, source, tags (comma-separated)."""
    rows = conn.execute("SELECT id, text, source, tags FROM facts").fetchall()
    return [
        Fact(id=r[0], text=r[1], source=r[2],
             tags=[t for t in (r[3] or "").split(",") if t])
        for r in rows
    ]
