"""
Observer persistence: store events, state changes, and chat messages in SQLite.
"""
from __future__ import annotations

import sqlite3
import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DB_DIR = REPO_ROOT / "data" / "observer"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "observer_actions.db"

_init_done = False

def _get_conn():
    return sqlite3.connect(str(DB_PATH))

def _init():
    global _init_done
    if _init_done:
        return
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT,
        source TEXT,
        timestamp TEXT,
        data TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS state_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT,
        old_value TEXT,
        new_value TEXT,
        timestamp TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        source TEXT,
        message TEXT,
        raw TEXT
    )
    """)
    conn.commit()
    conn.close()
    _init_done = True

def persist_event(event) -> None:
    try:
        _init()
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO events (event_type, source, timestamp, data) VALUES (?,?,?,?)",
            (event.event_type, event.source, event.timestamp, json.dumps(event.data or {})),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def persist_state_change(key: str, old_value: Any, new_value: Any, timestamp: str | None = None) -> None:
    try:
        _init()
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO state_changes (key, old_value, new_value, timestamp) VALUES (?,?,?,?)",
            (key, json.dumps(old_value, default=str), json.dumps(new_value, default=str), timestamp or ""),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def persist_chat_message(timestamp: str, source: str, message: str, raw: Any = None) -> None:
    try:
        _init()
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO chat_messages (timestamp, source, message, raw) VALUES (?,?,?,?)",
            (timestamp or "", source or "", message or "", json.dumps(raw or {})),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def query_recent_events(limit: int = 100):
    _init()
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, event_type, source, timestamp, data FROM events ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


# Ensure DB exists on import
_init()
