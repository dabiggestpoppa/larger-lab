"""
PO Monitor — Real-time action tracker for the Primary Observer.

Reads from observer_actions.db + OCE backend to provide a live
dashboard of PO activity. PO can learn from this log over time.

Endpoint: GET /api/po/monitor
WebSocket: /ws/po-monitor (real-time updates)
"""
import json
import sqlite3
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter

router = APIRouter(prefix="/api/po/monitor", tags=["po-monitor"])

DB_PATH = Path("data/observer/observer_actions.db")


def _db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/")
async def monitor_dashboard():
    """PO monitoring dashboard — recent actions, stats, health."""
    conn = _db()
    try:
        # Recent events
        events = conn.execute(
            "SELECT * FROM events ORDER BY timestamp DESC LIMIT 20"
        ).fetchall()
        events_list = [dict(e) for e in events]

        # Event type counts
        type_counts = conn.execute(
            "SELECT event_type, COUNT(*) as count FROM events GROUP BY event_type ORDER BY count DESC"
        ).fetchall()
        type_counts_list = [dict(t) for t in type_counts]

        # Source counts
        source_counts = conn.execute(
            "SELECT source, COUNT(*) as count FROM events GROUP BY source ORDER BY count DESC"
        ).fetchall()
        source_counts_list = [dict(s) for s in source_counts]

        # Total stats
        total_events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        total_state_changes = conn.execute("SELECT COUNT(*) FROM state_changes").fetchone()[0]
        total_chat_messages = conn.execute("SELECT COUNT(*) FROM chat_messages").fetchone()[0]

        # Last 24h events
        recent = conn.execute(
            "SELECT COUNT(*) FROM events WHERE timestamp > datetime('now', '-1 day')"
        ).fetchone()[0]

        return {
            "status": "active",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_events": total_events,
                "total_state_changes": total_state_changes,
                "total_chat_messages": total_chat_messages,
                "last_24h_events": recent,
            },
            "event_types": type_counts_list,
            "sources": source_counts_list,
            "recent_events": events_list,
        }
    finally:
        conn.close()


@router.get("/events")
async def monitor_events(limit: int = 50, offset: int = 0):
    """Paginated event log."""
    conn = _db()
    try:
        events = conn.execute(
            "SELECT * FROM events ORDER BY timestamp DESC LIMIT ? OFFSET ?",
            (limit, offset)
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "events": [dict(e) for e in events],
        }
    finally:
        conn.close()


@router.get("/events/{event_type}")
async def monitor_events_by_type(event_type: str, limit: int = 20):
    """Filter events by type."""
    conn = _db()
    try:
        events = conn.execute(
            "SELECT * FROM events WHERE event_type = ? ORDER BY timestamp DESC LIMIT ?",
            (event_type, limit)
        ).fetchall()
        return {
            "event_type": event_type,
            "count": len(events),
            "events": [dict(e) for e in events],
        }
    finally:
        conn.close()


@router.post("/event")
async def log_event(event: dict):
    """Log a new PO action event."""
    conn = _db()
    try:
        event_type = event.get("event_type", "custom")
        source = event.get("source", "primary_observer")
        data = event.get("data", {})
        conn.execute(
            "INSERT INTO events (event_type, source, timestamp, data) VALUES (?, ?, ?, ?)",
            (event_type, source, datetime.now(timezone.utc).isoformat(), json.dumps(data))
        )
        conn.commit()
        return {"status": "logged", "event_type": event_type}
    finally:
        conn.close()


@router.get("/learning-log")
async def learning_log():
    """
    PO's learning log — structured entries PO can review to improve.
    Reads from the observer chat log and recent events.
    """
    conn = _db()
    try:
        # Get recent task_received events
        tasks = conn.execute(
            "SELECT * FROM events WHERE event_type = 'task_received' ORDER BY timestamp DESC LIMIT 10"
        ).fetchall()

        # Get recent state changes
        states = conn.execute(
            "SELECT * FROM state_changes ORDER BY timestamp DESC LIMIT 10"
        ).fetchall()

        return {
            "recent_tasks": [dict(t) for t in tasks],
            "recent_state_changes": [dict(s) for s in states],
            "learning_prompts": [
                "Review recent tasks — which ones succeeded? Which failed?",
                "Check state changes — is PO spending time in productive states?",
                "Look for patterns — are certain task types consistently problematic?",
            ]
        }
    finally:
        conn.close()
