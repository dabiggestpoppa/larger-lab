"""QL-EXEC-R3 — durable runtime store (SQLite + WAL).

One store per ``runtime_id`` at ``state/<runtime_id>/runtime.sqlite``. It is the
authoritative local ledger: an append-only event journal plus materialized
current-state tables (desired state, intents, owned positions, broker orders,
reconciliation runs, heartbeats). The journal is NEVER rewritten; current state
is derived/updated in the same transaction as the event that changed it.

Startup is fail-closed: schema version, runtime_id, profile/config hash, and
deployment generation are all persisted and re-verified; mismatch BLOCKS
(config drift / generation drift) rather than silently continuing.

NO broker calls exist in this module. No strategy science, no capital routing.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from ..types import utcnow_iso

RUNTIME_SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS runtime_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS desired_state (
    runtime_id  TEXT PRIMARY KEY,
    state       TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runtime_events (
    seq          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id     TEXT NOT NULL UNIQUE,
    event_type   TEXT NOT NULL,
    ts           TEXT NOT NULL,
    dedup_key    TEXT UNIQUE,
    payload      TEXT NOT NULL DEFAULT '{}',
    payload_hash TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_events_type ON runtime_events(event_type);

CREATE TABLE IF NOT EXISTS strategy_events (
    event_id               TEXT PRIMARY KEY,
    strategy_id            TEXT NOT NULL,
    event_kind             TEXT NOT NULL DEFAULT '',
    deployment_generation  TEXT NOT NULL DEFAULT '',
    signal_time            TEXT NOT NULL DEFAULT '',
    payload                TEXT NOT NULL DEFAULT '{}',
    ts                     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS capital_decisions (
    decision_id    TEXT PRIMARY KEY,
    event_id       TEXT NOT NULL,
    strategy_id    TEXT NOT NULL,
    kind           TEXT NOT NULL,
    admitted_f     REAL,
    reservation_id TEXT NOT NULL DEFAULT '',
    policy_id      TEXT NOT NULL DEFAULT '',
    reason         TEXT NOT NULL DEFAULT '',
    ts             TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS economic_targets (
    target_id        TEXT PRIMARY KEY,
    event_id         TEXT NOT NULL,
    strategy_id      TEXT NOT NULL,
    account_id       TEXT NOT NULL,
    instrument       TEXT NOT NULL DEFAULT '',
    broker_symbol    TEXT NOT NULL DEFAULT '',
    side             TEXT NOT NULL DEFAULT '',
    target_quantity  REAL,
    target_notional  REAL,
    ts               TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS execution_intents (
    intent_id              TEXT PRIMARY KEY,
    runtime_id             TEXT NOT NULL,
    account_id             TEXT NOT NULL,
    strategy_id            TEXT NOT NULL,
    deployment_generation  TEXT NOT NULL,
    event_id               TEXT NOT NULL,
    economic_target_id     TEXT NOT NULL,
    instrument             TEXT NOT NULL DEFAULT '',
    broker_symbol          TEXT NOT NULL DEFAULT '',
    side                   TEXT NOT NULL DEFAULT '',
    broker_quantity        REAL NOT NULL DEFAULT 0,
    logical_ownership_id   TEXT NOT NULL,
    ownership_tag          TEXT NOT NULL DEFAULT '',
    broker_magic           INTEGER NOT NULL DEFAULT 0,
    state                  TEXT NOT NULL,
    broker_order_id        TEXT NOT NULL DEFAULT '',
    broker_position_id     TEXT NOT NULL DEFAULT '',
    filled_quantity        REAL NOT NULL DEFAULT 0,
    fill_price             REAL,
    reason                 TEXT NOT NULL DEFAULT '',
    ts                     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_intents_event ON execution_intents(event_id);

CREATE TABLE IF NOT EXISTS broker_orders (
    order_id           TEXT PRIMARY KEY,
    intent_id          TEXT NOT NULL,
    symbol             TEXT NOT NULL DEFAULT '',
    side               TEXT NOT NULL DEFAULT '',
    requested_quantity REAL NOT NULL DEFAULT 0,
    filled_quantity    REAL NOT NULL DEFAULT 0,
    status             TEXT NOT NULL DEFAULT '',
    ownership_tag      TEXT NOT NULL DEFAULT '',
    ts                 TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS positions_owned (
    logical_ownership_id  TEXT PRIMARY KEY,
    runtime_id            TEXT NOT NULL,
    account_id            TEXT NOT NULL,
    strategy_id           TEXT NOT NULL,
    intent_id             TEXT NOT NULL,
    event_id              TEXT NOT NULL,
    symbol                TEXT NOT NULL DEFAULT '',
    side                  TEXT NOT NULL DEFAULT '',
    requested_quantity    REAL NOT NULL DEFAULT 0,
    filled_quantity       REAL NOT NULL DEFAULT 0,
    state                 TEXT NOT NULL,
    broker_position_id    TEXT NOT NULL DEFAULT '',
    broker_order_id       TEXT NOT NULL DEFAULT '',
    ownership_tag         TEXT NOT NULL DEFAULT '',
    fill_price            REAL,
    ts                    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reconciliation_runs (
    run_id          TEXT PRIMARY KEY,
    state           TEXT NOT NULL,
    clean           INTEGER NOT NULL,
    blocked_reason  TEXT NOT NULL DEFAULT '',
    owned_count     INTEGER NOT NULL DEFAULT 0,
    foreign_count   INTEGER NOT NULL DEFAULT 0,
    detail          TEXT NOT NULL DEFAULT '',
    ts              TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS heartbeats (
    seq             INTEGER PRIMARY KEY AUTOINCREMENT,
    runtime_id      TEXT NOT NULL,
    state           TEXT NOT NULL,
    desired_state   TEXT NOT NULL,
    blocking_reason TEXT NOT NULL DEFAULT '',
    ts              TEXT NOT NULL
);
"""

REQUIRED_TABLES = (
    "runtime_meta",
    "desired_state",
    "runtime_events",
    "strategy_events",
    "capital_decisions",
    "economic_targets",
    "execution_intents",
    "broker_orders",
    "positions_owned",
    "reconciliation_runs",
    "heartbeats",
)


def payload_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


@dataclass
class OwnedPositionRecord:
    """Normalized owned-position view read from the ledger."""

    logical_ownership_id: str
    runtime_id: str
    account_id: str
    strategy_id: str
    intent_id: str
    event_id: str
    symbol: str
    side: str
    requested_quantity: float
    filled_quantity: float
    state: str
    broker_position_id: str
    broker_order_id: str
    ownership_tag: str
    fill_price: float | None


@dataclass
class IntentRecord:
    """Normalized intent view read from the ledger."""

    intent_id: str
    state: str
    event_id: str
    ownership_tag: str
    broker_order_id: str
    broker_position_id: str
    broker_quantity: float
    filled_quantity: float


class RuntimeStore:
    """Durable SQLite runtime store (WAL, append-only journal, fail-closed)."""

    def __init__(
        self,
        db_path: str | Path,
        *,
        clock: Optional[Callable[[], str]] = None,
    ) -> None:
        self.db_path = str(db_path)
        self._clock = clock or utcnow_iso
        self._conn: Optional[sqlite3.Connection] = None
        self._write_lock = threading.RLock()

    # ── lifecycle ─────────────────────────────────────────────────────────

    def open(self) -> None:
        parent = os.path.dirname(self.db_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, timeout=10.0)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=FULL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("PRAGMA busy_timeout=10000")

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
        self._conn = None

    @property
    def connected(self) -> bool:
        return self._conn is not None

    @property
    def wal_mode(self) -> str:
        if not self.connected:
            return ""
        row = self._conn.execute("PRAGMA journal_mode").fetchone()
        return str(row[0]) if row else ""

    # ── init / meta ───────────────────────────────────────────────────────

    def initialize(
        self,
        *,
        runtime_id: str,
        deployment_generation: str,
        profile_hash: str,
        account_hash: str,
    ) -> None:
        with self._write_lock:
            cur = self._conn.cursor()
            cur.executescript(SCHEMA_SQL)
            meta = {
                "schema_version": str(RUNTIME_SCHEMA_VERSION),
                "runtime_id": runtime_id,
                "deployment_generation": deployment_generation,
                "profile_hash": profile_hash,
                "account_hash": account_hash,
            }
            for k, v in meta.items():
                cur.execute(
                    "INSERT OR REPLACE INTO runtime_meta(key, value) VALUES(?,?)",
                    (k, v),
                )
            self._conn.commit()

    def meta(self, key: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT value FROM runtime_meta WHERE key=?", (key,)
        ).fetchone()
        return row["value"] if row else None

    def schema_version(self) -> Optional[int]:
        v = self.meta("schema_version")
        return int(v) if v is not None else None

    def startup_check(
        self,
        *,
        runtime_id: str,
        deployment_generation: str,
        profile_hash: str,
        account_hash: str,
    ) -> list[str]:
        """Return blockers for a fail-closed startup. Empty list == OK."""
        blockers: list[str] = []
        ver = self.schema_version()
        if ver != RUNTIME_SCHEMA_VERSION:
            blockers.append(
                f"SCHEMA_VERSION_MISMATCH expected={RUNTIME_SCHEMA_VERSION} got={ver}"
            )
            return blockers
        stored_runtime = self.meta("runtime_id")
        if stored_runtime != runtime_id:
            blockers.append(
                f"RUNTIME_ID_MISMATCH stored={stored_runtime!r} expected={runtime_id!r}"
            )
        stored_gen = self.meta("deployment_generation") or ""
        if stored_gen != deployment_generation:
            blockers.append(
                f"GENERATION_DRIFT stored={stored_gen!r} expected={deployment_generation!r}"
            )
        stored_profile = self.meta("profile_hash") or ""
        if stored_profile and stored_profile != profile_hash:
            blockers.append(
                "BLOCK_CONFIG_DRIFT profile hash mismatch under same generation"
            )
        stored_account = self.meta("account_hash") or ""
        if stored_account and stored_account != account_hash:
            blockers.append(
                "BLOCK_CONFIG_DRIFT account profile hash mismatch under same generation"
            )
        return blockers

    def integrity_check(self) -> list[str]:
        """Verify store integrity. Returns problems (empty == OK)."""
        problems: list[str] = []
        if not self.connected:
            return ["STORE_NOT_OPEN"]
        if self.schema_version() != RUNTIME_SCHEMA_VERSION:
            problems.append(
                f"SCHEMA_VERSION_MISMATCH expected={RUNTIME_SCHEMA_VERSION} "
                f"got={self.schema_version()}"
            )
        for t in REQUIRED_TABLES:
            row = self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (t,)
            ).fetchone()
            if row is None:
                problems.append(f"MISSING_TABLE {t}")
        return problems

    # ── desired state ─────────────────────────────────────────────────────

    def read_desired_state(self) -> str:
        row = self._conn.execute(
            "SELECT state FROM desired_state WHERE runtime_id=?",
            (self.meta("runtime_id") or "",),
        ).fetchone()
        return row["state"] if row else ""

    def write_desired_state(self, state: str, runtime_id: str) -> None:
        with self._write_lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                INSERT INTO desired_state(runtime_id, state, updated_at)
                VALUES(?,?,?)
                ON CONFLICT(runtime_id) DO UPDATE SET
                    state=excluded.state, updated_at=excluded.updated_at
                """,
                (runtime_id, state, self._clock()),
            )
            self._conn.commit()

    # ── append-only journal ───────────────────────────────────────────────

    def append_event(
        self,
        event_type: str,
        *,
        dedup_key: str = "",
        payload: Optional[dict] = None,
    ) -> int:
        """Append one journal event. Idempotent on ``dedup_key``.

        Returns the seq of the new event, or the existing seq if deduped.
        """
        payload = payload or {}
        ph = payload_hash(payload)
        with self._write_lock:
            cur = self._conn.cursor()
            if dedup_key:
                row = cur.execute(
                    "SELECT seq FROM runtime_events WHERE dedup_key=?", (dedup_key,)
                ).fetchone()
                if row is not None:
                    self._conn.commit()
                    return int(row["seq"])
            cur.execute(
                """
                INSERT INTO runtime_events(event_id, event_type, ts, dedup_key, payload, payload_hash)
                VALUES(?,?,?,?,?,?)
                """,
                (
                    self._event_id(),
                    event_type,
                    self._clock(),
                    dedup_key or None,
                    json.dumps(payload, default=str, sort_keys=True),
                    ph,
                ),
            )
            seq = int(cur.lastrowid)
            self._conn.commit()
        return seq

    def _event_id(self) -> str:
        # Journal event ids may use wall time (informational), but execution
        # identities NEVER do. Use a monotonic seq-backed id instead.
        with self._write_lock:
            row = self._conn.execute(
                "SELECT COALESCE(MAX(seq),0)+1 AS n FROM runtime_events"
            ).fetchone()
        return f"EVT_{int(row['n']):09d}"

    # ── strategy events (idempotent observation) ──────────────────────────

    def record_strategy_event(
        self,
        event_id: str,
        strategy_id: str,
        event_kind: str,
        deployment_generation: str,
        signal_time: str,
        payload: Optional[dict] = None,
    ) -> bool:
        """Persist an observed strategy event. Returns False if already seen."""
        with self._write_lock:
            cur = self._conn.cursor()
            row = cur.execute(
                "SELECT event_id FROM strategy_events WHERE event_id=?", (event_id,)
            ).fetchone()
            if row is not None:
                self._conn.commit()
                return False
            cur.execute(
                """
                INSERT INTO strategy_events
                  (event_id, strategy_id, event_kind, deployment_generation,
                   signal_time, payload, ts)
                VALUES (?,?,?,?,?,?,?)
                """,
                (
                    event_id,
                    strategy_id,
                    event_kind,
                    deployment_generation,
                    signal_time,
                    json.dumps(payload or {}, default=str, sort_keys=True),
                    self._clock(),
                ),
            )
            self._conn.commit()
        return True

    def has_strategy_event(self, event_id: str) -> bool:
        row = self._conn.execute(
            "SELECT event_id FROM strategy_events WHERE event_id=?", (event_id,)
        ).fetchone()
        return row is not None

    # ── capital decisions / economic targets ──────────────────────────────

    def record_capital_decision(
        self,
        decision_id: str,
        event_id: str,
        strategy_id: str,
        kind: str,
        admitted_f: Optional[float],
        reservation_id: str,
        policy_id: str,
        reason: str,
    ) -> None:
        with self._write_lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO capital_decisions
                  (decision_id, event_id, strategy_id, kind, admitted_f,
                   reservation_id, policy_id, reason, ts)
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    decision_id,
                    event_id,
                    strategy_id,
                    kind,
                    admitted_f,
                    reservation_id,
                    policy_id,
                    reason,
                    self._clock(),
                ),
            )
            self._conn.commit()

    def record_economic_target(
        self,
        target_id: str,
        event_id: str,
        strategy_id: str,
        account_id: str,
        instrument: str,
        broker_symbol: str,
        side: str,
        target_quantity: Optional[float],
        target_notional: Optional[float],
    ) -> None:
        with self._write_lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO economic_targets
                  (target_id, event_id, strategy_id, account_id, instrument,
                   broker_symbol, side, target_quantity, target_notional, ts)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    target_id,
                    event_id,
                    strategy_id,
                    account_id,
                    instrument,
                    broker_symbol,
                    side,
                    target_quantity,
                    target_notional,
                    self._clock(),
                ),
            )
            self._conn.commit()

    # ── execution intents (write-ahead) ───────────────────────────────────

    def create_intent(self, intent) -> bool:
        """Persist a write-ahead intent. Returns False if intent already exists."""
        d = intent.to_dict()
        with self._write_lock:
            cur = self._conn.cursor()
            row = cur.execute(
                "SELECT intent_id FROM execution_intents WHERE intent_id=?",
                (d["intent_id"],),
            ).fetchone()
            if row is not None:
                self._conn.commit()
                return False
            cur.execute(
                """
                INSERT INTO execution_intents
                  (intent_id, runtime_id, account_id, strategy_id,
                   deployment_generation, event_id, economic_target_id,
                   instrument, broker_symbol, side, broker_quantity,
                   logical_ownership_id, ownership_tag, broker_magic, state,
                   broker_order_id, broker_position_id, filled_quantity,
                   fill_price, reason, ts)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    d["intent_id"],
                    d["runtime_id"],
                    d["account_id"],
                    d["strategy_id"],
                    d["deployment_generation"],
                    d["event_id"],
                    d["economic_target_id"],
                    d["instrument"],
                    d["broker_symbol"],
                    d["side"],
                    d["broker_quantity"],
                    d["logical_ownership_id"],
                    d["ownership_tag"],
                    d["broker_magic"],
                    d["state"],
                    d["broker_order_id"],
                    d["broker_position_id"],
                    d["filled_quantity"],
                    d["fill_price"],
                    d["reason"],
                    self._clock(),
                ),
            )
            self._conn.commit()
        return True

    def get_intent(self, intent_id: str) -> Optional[IntentRecord]:
        row = self._conn.execute(
            "SELECT * FROM execution_intents WHERE intent_id=?", (intent_id,)
        ).fetchone()
        return self._intent_record(row) if row else None

    def intent_row(self, intent_id: str) -> Optional[dict]:
        """Full raw intent row (all columns) for reconstruction of OrderIntent."""
        row = self._conn.execute(
            "SELECT * FROM execution_intents WHERE intent_id=?", (intent_id,)
        ).fetchone()
        return dict(row) if row else None

    def intents(self, state: Optional[str] = None) -> list[IntentRecord]:
        if state:
            rows = self._conn.execute(
                "SELECT * FROM execution_intents WHERE state=? ORDER BY ts", (state,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM execution_intents ORDER BY ts"
            ).fetchall()
        return [self._intent_record(r) for r in rows]

    def update_intent(
        self,
        intent_id: str,
        *,
        state: Optional[str] = None,
        broker_order_id: Optional[str] = None,
        broker_position_id: Optional[str] = None,
        filled_quantity: Optional[float] = None,
        fill_price: Optional[float] = None,
        reason: Optional[str] = None,
    ) -> None:
        cur = self._conn.cursor()
        row = cur.execute(
            "SELECT * FROM execution_intents WHERE intent_id=?", (intent_id,)
        ).fetchone()
        if row is None:
            self._conn.commit()
            return
        new_state = state if state is not None else row["state"]
        new_order = broker_order_id if broker_order_id is not None else row["broker_order_id"]
        new_pos = broker_position_id if broker_position_id is not None else row["broker_position_id"]
        new_fq = filled_quantity if filled_quantity is not None else row["filled_quantity"]
        new_fp = fill_price if fill_price is not None else row["fill_price"]
        new_reason = reason if reason is not None else row["reason"]
        with self._write_lock:
            cur.execute(
                """
                UPDATE execution_intents SET
                  state=?, broker_order_id=?, broker_position_id=?,
                  filled_quantity=?, fill_price=?, reason=?
                WHERE intent_id=?
                """,
                (new_state, new_order, new_pos, new_fq, new_fp, new_reason, intent_id),
            )
            self._conn.commit()

    @staticmethod
    def _intent_record(row) -> IntentRecord:
        return IntentRecord(
            intent_id=row["intent_id"],
            state=row["state"],
            event_id=row["event_id"],
            ownership_tag=row["ownership_tag"] or "",
            broker_order_id=row["broker_order_id"] or "",
            broker_position_id=row["broker_position_id"] or "",
            broker_quantity=float(row["broker_quantity"] or 0.0),
            filled_quantity=float(row["filled_quantity"] or 0.0),
        )

    # ── broker orders / owned positions ───────────────────────────────────

    def record_broker_order(
        self,
        order_id: str,
        intent_id: str,
        symbol: str,
        side: str,
        requested_quantity: float,
        filled_quantity: float,
        status: str,
        ownership_tag: str,
    ) -> None:
        with self._write_lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                INSERT OR REPLACE INTO broker_orders
                  (order_id, intent_id, symbol, side, requested_quantity,
                   filled_quantity, status, ownership_tag, ts)
                VALUES (?,?,?,?,?,?,?,?,?)
                """,
                (
                    order_id,
                    intent_id,
                    symbol,
                    side,
                    requested_quantity,
                    filled_quantity,
                    status,
                    ownership_tag,
                    self._clock(),
                ),
            )
            self._conn.commit()

    def upsert_owned_position(
        self,
        logical_ownership_id: str,
        *,
        runtime_id: str,
        account_id: str,
        strategy_id: str,
        intent_id: str,
        event_id: str,
        symbol: str,
        side: str,
        requested_quantity: float,
        filled_quantity: float,
        state: str,
        broker_position_id: str,
        broker_order_id: str,
        ownership_tag: str,
        fill_price: Optional[float],
    ) -> None:
        with self._write_lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                INSERT INTO positions_owned
                  (logical_ownership_id, runtime_id, account_id, strategy_id,
                   intent_id, event_id, symbol, side, requested_quantity,
                   filled_quantity, state, broker_position_id, broker_order_id,
                   ownership_tag, fill_price, ts)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(logical_ownership_id) DO UPDATE SET
                   runtime_id=excluded.runtime_id, account_id=excluded.account_id,
                   strategy_id=excluded.strategy_id, intent_id=excluded.intent_id,
                   event_id=excluded.event_id, symbol=excluded.symbol,
                   side=excluded.side, requested_quantity=excluded.requested_quantity,
                   filled_quantity=excluded.filled_quantity, state=excluded.state,
                   broker_position_id=excluded.broker_position_id,
                   broker_order_id=excluded.broker_order_id,
                   ownership_tag=excluded.ownership_tag,
                   fill_price=excluded.fill_price, ts=excluded.ts
                """,
                (
                    logical_ownership_id,
                    runtime_id,
                    account_id,
                    strategy_id,
                    intent_id,
                    event_id,
                    symbol,
                    side,
                    requested_quantity,
                    filled_quantity,
                    state,
                    broker_position_id,
                    broker_order_id,
                    ownership_tag,
                    fill_price,
                    self._clock(),
                ),
            )
            self._conn.commit()

    def owned_positions(self, state: Optional[str] = None) -> list[OwnedPositionRecord]:
        if state:
            rows = self._conn.execute(
                "SELECT * FROM positions_owned WHERE state=? ORDER BY ts", (state,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM positions_owned ORDER BY ts"
            ).fetchall()
        out = []
        for r in rows:
            out.append(
                OwnedPositionRecord(
                    logical_ownership_id=r["logical_ownership_id"],
                    runtime_id=r["runtime_id"],
                    account_id=r["account_id"],
                    strategy_id=r["strategy_id"],
                    intent_id=r["intent_id"],
                    event_id=r["event_id"],
                    symbol=r["symbol"] or "",
                    side=r["side"] or "",
                    requested_quantity=float(r["requested_quantity"] or 0.0),
                    filled_quantity=float(r["filled_quantity"] or 0.0),
                    state=r["state"],
                    broker_position_id=r["broker_position_id"] or "",
                    broker_order_id=r["broker_order_id"] or "",
                    ownership_tag=r["ownership_tag"] or "",
                    fill_price=r["fill_price"],
                )
            )
        return out

    def get_owned_position(self, logical_ownership_id: str) -> Optional[OwnedPositionRecord]:
        row = self._conn.execute(
            "SELECT * FROM positions_owned WHERE logical_ownership_id=?",
            (logical_ownership_id,),
        ).fetchone()
        if row is None:
            return None
        return OwnedPositionRecord(
            logical_ownership_id=row["logical_ownership_id"],
            runtime_id=row["runtime_id"],
            account_id=row["account_id"],
            strategy_id=row["strategy_id"],
            intent_id=row["intent_id"],
            event_id=row["event_id"],
            symbol=row["symbol"] or "",
            side=row["side"] or "",
            requested_quantity=float(row["requested_quantity"] or 0.0),
            filled_quantity=float(row["filled_quantity"] or 0.0),
            state=row["state"],
            broker_position_id=row["broker_position_id"] or "",
            broker_order_id=row["broker_order_id"] or "",
            ownership_tag=row["ownership_tag"] or "",
            fill_price=row["fill_price"],
        )

    # ── reconciliation runs / heartbeats ──────────────────────────────────

    def record_reconciliation_run(
        self,
        run_id: str,
        state: str,
        clean: bool,
        blocked_reason: str,
        owned_count: int,
        foreign_count: int,
        detail: str,
    ) -> None:
        with self._write_lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                INSERT INTO reconciliation_runs
                  (run_id, state, clean, blocked_reason, owned_count,
                   foreign_count, detail, ts)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    run_id,
                    state,
                    1 if clean else 0,
                    blocked_reason,
                    owned_count,
                    foreign_count,
                    detail,
                    self._clock(),
                ),
            )
            self._conn.commit()

    def record_heartbeat(
        self,
        runtime_id: str,
        state: str,
        desired_state: str,
        blocking_reason: str,
    ) -> None:
        with self._write_lock:
            cur = self._conn.cursor()
            cur.execute(
                """
                INSERT INTO heartbeats(runtime_id, state, desired_state, blocking_reason, ts)
                VALUES (?,?,?,?,?)
                """,
                (runtime_id, state, desired_state, blocking_reason, self._clock()),
            )
            self._conn.commit()

    def last_heartbeat(self) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM heartbeats ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None

    def heartbeat_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS n FROM heartbeats").fetchone()
        return int(row["n"])
