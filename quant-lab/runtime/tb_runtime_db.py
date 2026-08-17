#!/usr/bin/env python3
"""
TB-R6.1 — RUNTIME DURABLE STATE (SQLite / WAL)
==============================================

Lightweight runtime persistence shared by supervisor / worker / dashboard /
tbctl. Complements (never replaces) the R3 append-only basket ledger.

Tables:
    runtime_status    key/value durable flags (desired state, NAV baselines)
    runtime_heartbeat rolling heartbeats written by the worker
    runtime_errors    bounded error trail (last N)
    daily_nav         frozen start-of-day equity baselines
    deployment_nav    frozen deployment equity baseline (per generation)

Dashboard reads THIS database only (no log scraping, no MT5 from dashboard).
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from tb_runtime_config import RUNTIME_DB, RUNNING, STOPPED_BY_USER

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runtime_status (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runtime_heartbeat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    pid INTEGER NOT NULL,
    generation TEXT NOT NULL,
    state TEXT NOT NULL,
    mt5_connected INTEGER NOT NULL,
    account_gate INTEGER NOT NULL,
    market_open INTEGER NOT NULL,
    last_closed_bar TEXT NOT NULL,
    last_signal_time TEXT NOT NULL,
    open_basket_id TEXT NOT NULL,
    today_pnl REAL NOT NULL,
    today_pnl_pct REAL NOT NULL,
    open_pnl REAL NOT NULL,
    deploy_pnl REAL NOT NULL,
    deploy_pnl_pct REAL NOT NULL,
    account_equity REAL NOT NULL,
    disk_free_gb REAL NOT NULL,
    last_error TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS runtime_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    source TEXT NOT NULL,
    message TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS daily_nav (
    day TEXT PRIMARY KEY,
    equity REAL NOT NULL,
    ts TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS deployment_nav (
    generation TEXT PRIMARY KEY,
    equity REAL NOT NULL,
    ts TEXT NOT NULL,
    note TEXT NOT NULL
);
"""


class RuntimeDB:
    """Thread-safe (per-process lock) SQLite WAL runtime store."""

    _lock = threading.Lock()

    def __init__(self, db_path=RUNTIME_DB):
        self.db_path = str(db_path)
        parent = os.path.dirname(self.db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, timeout=15.0)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self._migrate()
        self._conn.commit()

    def _migrate(self) -> None:
        """v1 -> v2: add today_pnl_pct to runtime_heartbeat (older DBs)."""
        cols = {r[1] for r in self._conn.execute(
            "PRAGMA table_info(runtime_heartbeat)")}
        if "today_pnl_pct" not in cols:
            self._conn.execute(
                "ALTER TABLE runtime_heartbeat ADD COLUMN today_pnl_pct REAL NOT NULL DEFAULT 0")
            self._conn.commit()

    # ── status kv ────────────────────────────────────────────────────────
    def get_status(self, key: str, default: str = "") -> str:
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM runtime_status WHERE key=?", (key,)).fetchone()
            return row["value"] if row else default

    def set_status(self, key: str, value: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO runtime_status(key, value, updated_at) "
                "VALUES(?,?,?) ON CONFLICT(key) DO UPDATE SET "
                "value=excluded.value, updated_at=excluded.updated_at",
                (key, str(value), _now_iso()))
            self._conn.commit()

    def get_status_json(self, key: str, default=None):
        v = self.get_status(key, "")
        if not v:
            return default
        try:
            return json.loads(v)
        except Exception:
            return default

    def set_status_json(self, key: str, obj) -> None:
        self.set_status(key, json.dumps(obj, default=str))

    # ── desired state ────────────────────────────────────────────────────
    def desired_state(self) -> str:
        v = self.get_status("desired_state", "")
        return v if v in (RUNNING, STOPPED_BY_USER) else RUNNING

    def set_desired_state(self, state: str) -> None:
        if state not in (RUNNING, STOPPED_BY_USER):
            raise ValueError(state)
        self.set_status("desired_state", state)

    # ── heartbeat ────────────────────────────────────────────────────────
    def record_heartbeat(self, hb: dict) -> int:
        with self._lock:
            cur = self._conn.execute(
                "INSERT INTO runtime_heartbeat(ts,pid,generation,state,"
                "mt5_connected,account_gate,market_open,last_closed_bar,"
                "last_signal_time,open_basket_id,today_pnl,today_pnl_pct,"
                "open_pnl,deploy_pnl,deploy_pnl_pct,account_equity,"
                "disk_free_gb,last_error) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,"
                "?,?,?,?,?,?)",
                (hb.get("ts", _now_iso()), int(hb.get("pid", 0)),
                 str(hb.get("generation", "")), str(hb.get("state", "")),
                 1 if hb.get("mt5_connected") else 0,
                 1 if hb.get("account_gate") else 0,
                 1 if hb.get("market_open") else 0,
                 str(hb.get("last_closed_bar", "")),
                 str(hb.get("last_signal_time", "")),
                 str(hb.get("open_basket_id", "")),
                 float(hb.get("today_pnl", 0.0)),
                 float(hb.get("today_pnl_pct", 0.0)),
                 float(hb.get("open_pnl", 0.0)),
                 float(hb.get("deploy_pnl", 0.0)),
                 float(hb.get("deploy_pnl_pct", 0.0)),
                 float(hb.get("account_equity", 0.0)),
                 float(hb.get("disk_free_gb", 0.0)),
                 str(hb.get("last_error", ""))))
            self._conn.commit()
            return cur.lastrowid

    def latest_heartbeat(self) -> Optional[dict]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM runtime_heartbeat ORDER BY id DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    def heartbeat_age_s(self) -> Optional[float]:
        hb = self.latest_heartbeat()
        if not hb:
            return None
        ts = datetime.fromisoformat(hb["ts"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - ts).total_seconds()

    # ── errors (bounded trail) ───────────────────────────────────────────
    def record_error(self, source: str, message: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO runtime_errors(ts, source, message) VALUES(?,?,?)",
                (_now_iso(), source, message[:500]))
            self._conn.execute(
                "DELETE FROM runtime_errors WHERE id NOT IN "
                "(SELECT id FROM runtime_errors ORDER BY id DESC LIMIT 200)")
            self._conn.commit()

    def recent_errors(self, n: int = 5) -> List[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT ts, source, message FROM runtime_errors "
                "ORDER BY id DESC LIMIT ?", (n,)).fetchall()
            return [dict(r) for r in rows]

    # ── NAV baselines ────────────────────────────────────────────────────
    def freeze_daily_nav(self, day: str, equity: float) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO daily_nav(day, equity, ts) VALUES(?,?,?)",
                (day, float(equity), _now_iso()))
            self._conn.commit()

    def daily_nav(self, day: str) -> Optional[float]:
        with self._lock:
            row = self._conn.execute(
                "SELECT equity FROM daily_nav WHERE day=?", (day,)).fetchone()
            return float(row["equity"]) if row else None

    def freeze_deployment_nav(self, generation: str, equity: float,
                              note: str = "") -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO deployment_nav(generation, equity, ts, note) "
                "VALUES(?,?,?,?)", (generation, float(equity), _now_iso(), note))
            self._conn.commit()

    def deployment_nav(self, generation: str) -> Optional[float]:
        with self._lock:
            row = self._conn.execute(
                "SELECT equity FROM deployment_nav WHERE generation=?",
                (generation,)).fetchone()
            return float(row["equity"]) if row else None

    def integrity_check(self) -> dict:
        """Quick integrity: tables exist, monotonic heartbeat ids, no
        obviously-corrupt rows. Returns a report dict."""
        out = {"ok": True, "tables": [], "heartbeat_rows": 0,
               "monotonic_ids": True, "errors": []}
        try:
            with self._lock:
                tables = {r["name"] for r in self._conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
                out["tables"] = sorted(tables)
                rows = self._conn.execute(
                    "SELECT id FROM runtime_heartbeat ORDER BY id").fetchall()
                ids = [r["id"] for r in rows]
                out["heartbeat_rows"] = len(ids)
                out["monotonic_ids"] = all(
                    b - a == 1 for a, b in zip(ids, ids[1:])) if ids else True
                if not out["monotonic_ids"]:
                    out["ok"] = False
                    out["errors"].append("heartbeat ids not monotonic")
                # verify WAL mode
                jm = self._conn.execute("PRAGMA journal_mode").fetchone()[0]
                out["journal_mode"] = jm
        except Exception as e:  # pragma: no cover
            out["ok"] = False
            out["errors"].append(str(e))
        return out

    def close(self) -> None:
        with self._lock:
            try:
                self._conn.close()
            except Exception:
                pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
