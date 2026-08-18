"""QL-EXEC-R4.2 — isolated shadow durable store (SQLite / WAL).

A dedicated, runtime_id-scoped SQLite store for the generic TB shadow. It is
separate from every active TB path (tb_runtime.db / tb_control.db) and from
the R3 GenericRuntime store: the shadow is an OBSERVER and its durable state
must not be able to influence active execution.

Tables:
    shadow_meta           key/value identity (runtime_id, generation, hashes)
    shadow_desired_state  durable desired state (RUNNING / STOPPED_BY_USER)
    shadow_processed      processed feed sequence numbers + parity verdicts
    shadow_mismatches     append-only mismatch log
    shadow_heartbeat      rolling heartbeats
    shadow_counters       telemetry counters (broker_write_calls, etc.)
"""
from __future__ import annotations

import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS shadow_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shadow_desired_state (
    state TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shadow_processed (
    seq INTEGER PRIMARY KEY,
    bar_key TEXT NOT NULL,
    verdict TEXT NOT NULL,
    processed_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shadow_mismatches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bar_key TEXT NOT NULL,
    mismatch_class TEXT NOT NULL,
    legacy_value TEXT NOT NULL,
    generic_value TEXT NOT NULL,
    detail TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shadow_heartbeat (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    state TEXT NOT NULL,
    latest_bar TEXT NOT NULL,
    bars_compared INTEGER NOT NULL,
    broker_write_calls INTEGER NOT NULL,
    last_error TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS shadow_counters (
    key TEXT PRIMARY KEY,
    value INTEGER NOT NULL
);
"""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ShadowStore:
    """Thread-safe (per-process lock) isolated shadow store."""

    _lock = threading.Lock()

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        parent = os.path.dirname(self.db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    def open(self) -> None:
        self._conn = sqlite3.connect(self.db_path, timeout=15.0)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def initialize(self, *, runtime_id: str, deployment_generation: str,
                   profile_hash: str, shadow_profile_hash: str,
                   parity_schema_version: int, tolerance_version: str) -> None:
        if self._conn is None:
            raise RuntimeError("store not open")
        meta = {
            "runtime_id": runtime_id,
            "deployment_generation": deployment_generation,
            "profile_hash": profile_hash,
            "shadow_profile_hash": shadow_profile_hash,
            "parity_schema_version": str(parity_schema_version),
            "tolerance_version": tolerance_version,
            "schema_version": "1",
        }
        with self._lock:
            for k, v in meta.items():
                self._conn.execute(
                    "INSERT INTO shadow_meta(key, value) VALUES(?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (k, str(v)))
            self._conn.commit()

    def meta(self, key: str, default: str = "") -> str:
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM shadow_meta WHERE key=?", (key,)).fetchone()
            return str(row["value"]) if row else default

    def set_meta(self, key: str, value: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO shadow_meta(key, value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, str(value)))
            self._conn.commit()

    # ── desired state ────────────────────────────────────────────────────
    def desired_state(self, default: str = "RUNNING") -> str:
        with self._lock:
            row = self._conn.execute(
                "SELECT state FROM shadow_desired_state ORDER BY rowid DESC "
                "LIMIT 1").fetchone()
            return str(row["state"]) if row else default

    def set_desired_state(self, state: str) -> None:
        if state not in ("RUNNING", "STOPPED_BY_USER"):
            raise ValueError(state)
        with self._lock:
            self._conn.execute(
                "INSERT INTO shadow_desired_state(state, updated_at) VALUES(?,?)",
                (state, _now_iso()))
            self._conn.commit()

    # ── processed feed ───────────────────────────────────────────────────
    def last_processed_seq(self) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT MAX(seq) AS m FROM shadow_processed").fetchone()
            return int(row["m"]) if row and row["m"] is not None else 0

    def record_processed(self, seq: int, bar_key: str, verdict: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO shadow_processed(seq, bar_key, verdict, "
                "processed_at) VALUES(?,?,?,?)",
                (int(seq), bar_key, verdict, _now_iso()))
            self._conn.commit()

    # ── mismatches ───────────────────────────────────────────────────────
    def record_mismatch(self, *, bar_key: str, mismatch_class: str,
                        legacy_value: str, generic_value: str, detail: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO shadow_mismatches(bar_key, mismatch_class, "
                "legacy_value, generic_value, detail, recorded_at) "
                "VALUES(?,?,?,?,?,?)",
                (bar_key, mismatch_class, legacy_value, generic_value,
                 detail[:1000], _now_iso()))
            self._conn.commit()

    def mismatch_count(self) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT COUNT(*) AS c FROM shadow_mismatches").fetchone()
            return int(row["c"]) if row else 0

    # ── heartbeat ────────────────────────────────────────────────────────
    def record_heartbeat(self, *, state: str, latest_bar: str,
                         bars_compared: int, broker_write_calls: int,
                         last_error: str = "") -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO shadow_heartbeat(ts, state, latest_bar, "
                "bars_compared, broker_write_calls, last_error) VALUES(?,?,?,?,?,?)",
                (_now_iso(), state, latest_bar, int(bars_compared),
                 int(broker_write_calls), last_error[:500]))
            self._conn.commit()

    def latest_heartbeat(self) -> Optional[dict]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM shadow_heartbeat ORDER BY id DESC LIMIT 1"
            ).fetchone()
            return dict(row) if row else None

    # ── counters ─────────────────────────────────────────────────────────
    def counter(self, key: str) -> int:
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM shadow_counters WHERE key=?", (key,)).fetchone()
            return int(row["value"]) if row else 0

    def increment(self, key: str, n: int = 1) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO shadow_counters(key, value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=value+excluded.value",
                (key, int(n)))
            self._conn.commit()

    def set_counter(self, key: str, value: int) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO shadow_counters(key, value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, int(value)))
            self._conn.commit()

    def journal_mode(self) -> str:
        with self._lock:
            row = self._conn.execute("PRAGMA journal_mode").fetchone()
            return str(row[0]) if row else ""

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                try:
                    self._conn.close()
                except Exception:
                    pass
                self._conn = None
