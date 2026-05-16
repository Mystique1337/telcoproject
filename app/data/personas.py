"""SQLite-backed persona cache.

Personas are extracted offline (slow, LLM-bound) and cached here so the API can
fetch them in <10ms per request.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

from app.api.schemas.persona import Persona
from app.config import get_settings

logger = logging.getLogger(__name__)


_DDL = """
CREATE TABLE IF NOT EXISTS personas (
    user_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_personas_updated_at ON personas(updated_at);
"""


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    settings = get_settings()
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(settings.sqlite_path))
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(_DDL)
        yield conn
        conn.commit()
    finally:
        conn.close()


def save_persona(persona: Persona) -> None:
    if not persona.user_id:
        raise ValueError("Cannot save persona without user_id")
    with _conn() as c:
        c.execute(
            "INSERT INTO personas(user_id, payload, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at",
            (persona.user_id, persona.model_dump_json(), datetime.utcnow().isoformat()),
        )


def get_persona(user_id: str) -> Persona | None:
    with _conn() as c:
        row = c.execute(
            "SELECT payload FROM personas WHERE user_id = ?", (user_id,)
        ).fetchone()
    if not row:
        return None
    return Persona.model_validate_json(row["payload"])


def list_personas(limit: int = 100) -> list[Persona]:
    with _conn() as c:
        rows = c.execute(
            "SELECT payload FROM personas ORDER BY updated_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [Persona.model_validate_json(r["payload"]) for r in rows]


def count_personas() -> int:
    with _conn() as c:
        row = c.execute("SELECT COUNT(*) AS n FROM personas").fetchone()
    return int(row["n"])
