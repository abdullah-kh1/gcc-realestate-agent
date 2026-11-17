import json
import sqlite3
import threading
from datetime import datetime, timezone
from typing import Any, Optional

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    phone TEXT PRIMARY KEY,
    state_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bookings (
    reference TEXT PRIMARY KEY,
    phone TEXT NOT NULL,
    name TEXT NOT NULL,
    slot_iso TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
"""

_lock = threading.RLock()
_connection: Optional[sqlite3.Connection] = None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def initialize() -> None:
    global _connection
    with _lock:
        if _connection is None:
            config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(str(config.DB_PATH), check_same_thread=False)
            connection.row_factory = sqlite3.Row
            connection.executescript(SCHEMA)
            connection.commit()
            _connection = connection


def _db() -> sqlite3.Connection:
    initialize()
    assert _connection is not None
    return _connection


def load_state(phone: str) -> Optional[dict[str, Any]]:
    with _lock:
        row = _db().execute("SELECT state_json FROM sessions WHERE phone = ?", (phone,)).fetchone()
    return json.loads(row["state_json"]) if row else None


def save_state(state: dict[str, Any]) -> None:
    payload = json.dumps(state, ensure_ascii=False)
    now = _now()
    with _lock:
        db = _db()
        db.execute(
            "INSERT INTO sessions (phone, state_json, created_at, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(phone) DO UPDATE SET state_json = excluded.state_json, updated_at = excluded.updated_at",
            (state["phone_number"], payload, now, now),
        )
        db.commit()


def list_states() -> list[dict[str, Any]]:
    with _lock:
        rows = _db().execute("SELECT state_json, updated_at FROM sessions ORDER BY updated_at DESC, rowid DESC").fetchall()
    return [{"state": json.loads(row["state_json"]), "updated_at": row["updated_at"]} for row in rows]


def delete_state(phone: str) -> bool:
    with _lock:
        db = _db()
        cursor = db.execute("DELETE FROM sessions WHERE phone = ?", (phone,))
        db.commit()
        return cursor.rowcount > 0


def insert_booking(reference: str, phone: str, name: str, slot_iso: str) -> bool:
    with _lock:
        db = _db()
        try:
            db.execute(
                "INSERT INTO bookings (reference, phone, name, slot_iso, created_at) VALUES (?, ?, ?, ?, ?)",
                (reference, phone, name, slot_iso, _now()),
            )
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            return False
    return True


def booked_slots() -> set[str]:
    with _lock:
        rows = _db().execute("SELECT slot_iso FROM bookings").fetchall()
    return {row["slot_iso"] for row in rows}


def list_bookings() -> list[dict[str, Any]]:
    with _lock:
        rows = _db().execute(
            "SELECT reference, phone, name, slot_iso FROM bookings ORDER BY slot_iso ASC"
        ).fetchall()
    return [dict(row) for row in rows]
