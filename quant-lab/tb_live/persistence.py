"""
TB-R3 — Durable Append-Only Event Ledger (SQLite + WAL)
========================================================

The core problem R3 solves:

    If the process dies after one, two, or three fills — or after a close,
    or after manual broker intervention — WHAT EXACTLY HAPPENED?

This module persists EVENTS, not merely mutable current state. A material
basket action produces a durable record BEFORE any broker action (write-ahead
safety), and broker responses are appended after.

Design:
  * SQLite with WAL journal mode (crash-safe, concurrent reader/writer).
  * Append-only `events` table with a monotonic sequence; UPDATE/DELETE are
    never part of the normal flow. The `basket_current` table is a derived
    materialized view (last-known state per basket) updated in the SAME
    transaction as the event — it is a fast-reconstruction cache, never the
    source of truth.
  * Idempotency: every event carries a deterministic `dedup_key` with a UNIQUE
    constraint. Re-processing the same signal / broker response / close event
    cannot double-record.
  * State-machine enforcement: every event's (prior_state, new_state) pair is
    validated against the frozen graph in state_machine.py before it is
    committed. Invalid transitions FAIL CLOSED.
  * Integrity check on startup: schema version, required tables, monotonic
    sequence (no gaps/dups), unique ids, payload hashes, transition validity.
    Any corruption -> BLOCKED_UNKNOWN_STATE (engine refuses to proceed).

NO broker calls exist in this module. `order_send` remains unreachable.

MECHANICAL CHANGE ONLY: no alpha / threshold / session / cost semantics.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from tb_live.state_machine import (
    BasketLifecycleState,
    validate_transition,
    is_valid_transition,
)

TB_STATE_SCHEMA_VERSION = 1
APP_VERSION = "TB-R3-PERSISTENCE-RECONCILIATION-01"


# ─── EVENT TYPES (frozen R3 set) ─────────────────────────────────────────

class EventType(str, Enum):
    SIGNAL_OBSERVED = "SIGNAL_OBSERVED"
    SIGNAL_REJECTED = "SIGNAL_REJECTED"
    BASKET_INTENT_CREATED = "BASKET_INTENT_CREATED"
    ENTRY_ATTEMPT_STARTED = "ENTRY_ATTEMPT_STARTED"
    LEG_ORDER_SENT = "LEG_ORDER_SENT"
    LEG_FILL_CONFIRMED = "LEG_FILL_CONFIRMED"
    LEG_FILL_FAILED = "LEG_FILL_FAILED"
    BASKET_OPEN_VERIFIED = "BASKET_OPEN_VERIFIED"
    BROKEN_HEDGE_DETECTED = "BROKEN_HEDGE_DETECTED"
    FLATTEN_STARTED = "FLATTEN_STARTED"
    FLATTEN_LEG_CONFIRMED = "FLATTEN_LEG_CONFIRMED"
    BASKET_FLAT_VERIFIED = "BASKET_FLAT_VERIFIED"
    EXIT_SIGNAL_OBSERVED = "EXIT_SIGNAL_OBSERVED"
    EXIT_ATTEMPT_STARTED = "EXIT_ATTEMPT_STARTED"
    EXIT_FILL_CONFIRMED = "EXIT_FILL_CONFIRMED"
    BASKET_CLOSED_VERIFIED = "BASKET_CLOSED_VERIFIED"
    MANUAL_POSITION_DETECTED = "MANUAL_POSITION_DETECTED"
    BROKER_LOCAL_MISMATCH = "BROKER_LOCAL_MISMATCH"
    RECONCILIATION_STARTED = "RECONCILIATION_STARTED"
    RECONCILIATION_COMPLETED = "RECONCILIATION_COMPLETED"
    ENGINE_BLOCKED = "ENGINE_BLOCKED"
    ENGINE_STARTED = "ENGINE_STARTED"
    ENGINE_SHUTDOWN = "ENGINE_SHUTDOWN"
    CONTROL_SIGNAL_OBSERVED = "CONTROL_SIGNAL_OBSERVED"


# Events that MUST carry a basket lifecycle transition (prior_state/new_state)
# and are validated against the frozen graph before commit.
REQUIRED_TRANSITION_EVENT_TYPES = frozenset({
    EventType.BASKET_INTENT_CREATED,
    EventType.ENTRY_ATTEMPT_STARTED,
    EventType.BASKET_OPEN_VERIFIED,
    EventType.BROKEN_HEDGE_DETECTED,
    EventType.FLATTEN_STARTED,
    EventType.BASKET_FLAT_VERIFIED,
    EventType.EXIT_SIGNAL_OBSERVED,
    EventType.EXIT_ATTEMPT_STARTED,
    EventType.BASKET_CLOSED_VERIFIED,
    EventType.MANUAL_POSITION_DETECTED,
    EventType.BROKER_LOCAL_MISMATCH,
})

# Events that may carry optional prior/new state when a transition is known
# (e.g. reconciliation outcomes), but do not REQUIRE it.
OPTIONAL_TRANSITION_EVENT_TYPES = frozenset({
    EventType.RECONCILIATION_STARTED,
    EventType.RECONCILIATION_COMPLETED,
    EventType.ENGINE_BLOCKED,
    EventType.SIGNAL_OBSERVED,
    EventType.SIGNAL_REJECTED,
})

TRANSITION_EVENT_TYPES = (
    REQUIRED_TRANSITION_EVENT_TYPES | OPTIONAL_TRANSITION_EVENT_TYPES)

# Non-transition informational events (no basket state semantics).
# LEG_FILL_CONFIRMED / EXIT_FILL_CONFIRMED / FLATTEN_LEG_CONFIRMED are
# per-leg fill records: they carry ticket/price payloads but do NOT by
# themselves transition the basket lifecycle (BASKET_OPEN_VERIFIED /
# BASKET_CLOSED_VERIFIED / BASKET_FLAT_VERIFIED do).
INFO_EVENT_TYPES = frozenset({
    EventType.LEG_ORDER_SENT,
    EventType.LEG_FILL_CONFIRMED,
    EventType.EXIT_FILL_CONFIRMED,
    EventType.FLATTEN_LEG_CONFIRMED,
    EventType.LEG_FILL_FAILED,
    EventType.ENGINE_STARTED,
    EventType.ENGINE_SHUTDOWN,
    EventType.CONTROL_SIGNAL_OBSERVED,
})


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def stable_id(prefix: str, *parts: str) -> str:
    """Deterministic id from content parts (replay-stable)."""
    h = hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:16]
    return f"{prefix}_{h}"


def payload_hash(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode()
    ).hexdigest()


@dataclass
class LedgerEvent:
    """One append-only ledger event (immutable view of a row)."""

    event_id: str
    seq: int
    event_type: str
    ts_utc: str
    basket_id: str
    strategy_id: str
    prior_state: str
    new_state: str
    dedup_key: str
    payload: dict = field(default_factory=dict)
    payload_hash: str = ""
    source: str = ""
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "seq": self.seq,
            "event_type": self.event_type,
            "ts_utc": self.ts_utc,
            "basket_id": self.basket_id,
            "strategy_id": self.strategy_id,
            "prior_state": self.prior_state,
            "new_state": self.new_state,
            "dedup_key": self.dedup_key,
            "payload": self.payload,
            "payload_hash": self.payload_hash,
            "source": self.source,
            "reason": self.reason,
        }


# ─── SQLITE LEDGER ───────────────────────────────────────────────────────

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    event_id      TEXT PRIMARY KEY,
    seq           INTEGER NOT NULL UNIQUE,
    event_type    TEXT NOT NULL,
    ts_utc        TEXT NOT NULL,
    basket_id     TEXT NOT NULL DEFAULT '',
    strategy_id   TEXT NOT NULL DEFAULT '',
    prior_state   TEXT NOT NULL DEFAULT '',
    new_state     TEXT NOT NULL DEFAULT '',
    dedup_key     TEXT UNIQUE,
    payload       TEXT NOT NULL DEFAULT '{}',
    payload_hash  TEXT NOT NULL DEFAULT '',
    source        TEXT NOT NULL DEFAULT '',
    reason        TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_events_basket   ON events(basket_id);
CREATE INDEX IF NOT EXISTS idx_events_type     ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_seq      ON events(seq);

-- Materialized last-known basket state (derived cache, updated in the same
-- transaction as the event that changed it; NEVER the source of truth).
CREATE TABLE IF NOT EXISTS basket_current (
    basket_id     TEXT PRIMARY KEY,
    strategy_id   TEXT NOT NULL DEFAULT '',
    direction     TEXT NOT NULL DEFAULT '',
    state         TEXT NOT NULL,
    last_seq      INTEGER NOT NULL,
    entry_time_utc TEXT NOT NULL DEFAULT '',
    entry_basis   REAL NOT NULL DEFAULT 0.0,
    entry_z       REAL NOT NULL DEFAULT 0.0
);
"""


class BasketLedger:
    """Append-only durable event ledger for TB basket truth.

    Thread-safety: a module-level lock serializes writes (SQLite is
    single-writer; WAL allows concurrent readers). All tests use one
    connection; production may open one per process.
    """

    _write_lock = threading.Lock()

    def __init__(self, db_path, create: bool = True):
        self.db_path = str(db_path)
        self._conn: Optional[sqlite3.Connection] = None
        self._opened = False
        self._fail_closed_error: Optional[str] = None
        if create:
            self.open()

    # ── connection lifecycle ─────────────────────────────────────────────
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
        self._opened = True

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
        self._conn = None
        self._opened = False

    @property
    def connected(self) -> bool:
        return self._opened and self._conn is not None

    # ── schema / init ────────────────────────────────────────────────────
    def initialize(self) -> None:
        """Create schema + record version. Idempotent."""
        with self._write_lock:
            cur = self._conn.cursor()
            cur.executescript(SCHEMA_SQL)
            cur.execute(
                "INSERT OR REPLACE INTO schema_meta(key, value) VALUES(?,?)",
                ("schema_version", str(TB_STATE_SCHEMA_VERSION)),
            )
            cur.execute(
                "INSERT OR REPLACE INTO schema_meta(key, value) VALUES(?,?)",
                ("app_version", APP_VERSION),
            )
            self._conn.commit()

    def schema_version(self) -> Optional[int]:
        cur = self._conn.cursor()
        row = cur.execute(
            "SELECT value FROM schema_meta WHERE key='schema_version'"
        ).fetchone()
        return int(row["value"]) if row else None

    # ── append (write-ahead, validated, idempotent) ──────────────────────
    def append_event(self, event_type: EventType, basket_id: str = "",
                     strategy_id: str = "", prior_state: str = "",
                     new_state: str = "", dedup_key: str = "",
                     payload: Optional[dict] = None, source: str = "",
                     reason: str = "",
                     stateful: Optional[bool] = None) -> LedgerEvent:
        """Append one event atomically with state-machine + dedup enforcement.

        - If `dedup_key` is non-empty and already present, the existing event
          is returned and nothing is appended (idempotency).
        - If the event type is a transition event, (prior_state, new_state)
          MUST be a valid transition in the frozen graph, otherwise ValueError
          (fail closed, nothing written).
        - The basket_current materialized row is updated in the same
          transaction when new_state is a lifecycle state.
        """
        if not self.connected:
            raise RuntimeError("LEDGER NOT OPEN (fail closed)")

        event_type = EventType(event_type) if not isinstance(event_type, EventType) else event_type
        payload = payload or {}
        ph = payload_hash(payload)

        if dedup_key:
            existing = self.get_by_dedup(dedup_key)
            if existing is not None:
                return existing  # idempotent no-op

        # State-machine gate: REQUIRED transition events must carry valid
        # (prior_state, new_state). If BOTH states are provided for any other
        # event type, validate them too (fail closed on invalid pairs).
        if event_type in REQUIRED_TRANSITION_EVENT_TYPES or (stateful is True):
            if not prior_state or not new_state:
                raise ValueError(
                    f"MISSING_STATES for {event_type.value}: "
                    f"prior={prior_state!r} new={new_state!r}")
            validate_transition(BasketLifecycleState(prior_state),
                                BasketLifecycleState(new_state))
        elif prior_state or new_state:
            validate_transition(BasketLifecycleState(prior_state),
                                BasketLifecycleState(new_state))

        event_id = str(uuid.uuid4())
        ts = utcnow_iso()

        with self._write_lock:
            try:
                cur = self._conn.cursor()
                seq = self._next_seq(cur)
                cur.execute(
                    """INSERT INTO events
                       (event_id, seq, event_type, ts_utc, basket_id,
                        strategy_id, prior_state, new_state, dedup_key,
                        payload, payload_hash, source, reason)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (event_id, seq, event_type.value, ts,
                     basket_id, strategy_id, prior_state, new_state,
                     dedup_key or None, json.dumps(payload, default=str),
                     ph, source, reason),
                )
                if new_state and new_state in BasketLifecycleState.__members__:
                    cur.execute(
                        """INSERT INTO basket_current
                           (basket_id, strategy_id, direction, state, last_seq,
                            entry_time_utc, entry_basis, entry_z)
                           VALUES (?,?,?,?,?,?,?,?)
                           ON CONFLICT(basket_id) DO UPDATE SET
                             strategy_id=excluded.strategy_id,
                             direction=excluded.direction,
                             state=excluded.state,
                             last_seq=excluded.last_seq,
                             entry_time_utc=excluded.entry_time_utc,
                             entry_basis=excluded.entry_basis,
                             entry_z=excluded.entry_z""",
                        (basket_id, strategy_id,
                         payload.get("direction", ""),
                         new_state, seq,
                         payload.get("entry_time_utc", ""),
                         float(payload.get("entry_basis", 0.0) or 0.0),
                         float(payload.get("entry_z", 0.0) or 0.0)),
                    )
                self._conn.commit()
            except sqlite3.IntegrityError:
                self._conn.rollback()
                raise
            except Exception:
                self._conn.rollback()
                raise

        return LedgerEvent(
            event_id=event_id, seq=self.last_seq(), event_type=event_type.value,
            ts_utc=ts, basket_id=basket_id, strategy_id=strategy_id,
            prior_state=prior_state, new_state=new_state,
            dedup_key=dedup_key or "", payload=payload, payload_hash=ph,
            source=source, reason=reason,
        )

    def _next_seq(self, cur) -> int:
        row = cur.execute("SELECT COALESCE(MAX(seq),0)+1 AS n FROM events").fetchone()
        return int(row["n"])

    def last_seq(self) -> int:
        row = self._conn.execute("SELECT COALESCE(MAX(seq),0) AS n FROM events").fetchone()
        return int(row["n"])

    # ── read helpers ─────────────────────────────────────────────────────
    def get_by_dedup(self, dedup_key: str) -> Optional[LedgerEvent]:
        if not self.connected or not dedup_key:
            return None
        row = self._conn.execute(
            "SELECT * FROM events WHERE dedup_key=?", (dedup_key,)
        ).fetchone()
        return self._row_to_event(row) if row else None

    def get_event(self, event_id: str) -> Optional[LedgerEvent]:
        row = self._conn.execute(
            "SELECT * FROM events WHERE event_id=?", (event_id,)
        ).fetchone()
        return self._row_to_event(row) if row else None

    def events_for(self, basket_id: str = None, event_type: str = None,
                   limit: int = None) -> List[LedgerEvent]:
        q = "SELECT * FROM events"
        clauses, args = [], []
        if basket_id:
            clauses.append("basket_id=?")
            args.append(basket_id)
        if event_type:
            clauses.append("event_type=?")
            args.append(event_type)
        if clauses:
            q += " WHERE " + " AND ".join(clauses)
        q += " ORDER BY seq"
        if limit:
            q += f" LIMIT {int(limit)}"
        rows = self._conn.execute(q, args).fetchall()
        return [self._row_to_event(r) for r in rows]

    def all_events(self) -> List[LedgerEvent]:
        return self.events_for()

    def current_basket(self, basket_id: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT * FROM basket_current WHERE basket_id=?", (basket_id,)
        ).fetchone()
        return dict(row) if row else None

    def all_current_baskets(self) -> List[dict]:
        rows = self._conn.execute(
            "SELECT * FROM basket_current ORDER BY last_seq"
        ).fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def _row_to_event(row) -> LedgerEvent:
        payload = {}
        try:
            payload = json.loads(row["payload"] or "{}")
        except (json.JSONDecodeError, TypeError):
            payload = {"__corrupt_payload__": True}
        return LedgerEvent(
            event_id=row["event_id"], seq=int(row["seq"]),
            event_type=row["event_type"], ts_utc=row["ts_utc"],
            basket_id=row["basket_id"] or "",
            strategy_id=row["strategy_id"] or "",
            prior_state=row["prior_state"] or "",
            new_state=row["new_state"] or "",
            dedup_key=row["dedup_key"] or "",
            payload=payload, payload_hash=row["payload_hash"] or "",
            source=row["source"] or "", reason=row["reason"] or "",
        )

    # ── integrity ────────────────────────────────────────────────────────
    def integrity_check(self) -> List[str]:
        """Verify ledger integrity. Returns a list of problems (empty = OK).

        Checks: schema version, required tables, sequence monotonicity (no
        gaps / duplicates), unique event ids, payload hash integrity, valid
        state transitions. Any problem => engine must fail closed.
        """
        problems: List[str] = []
        if not self.connected:
            return ["LEDGER NOT OPEN"]

        # 1. schema version
        ver = self.schema_version()
        if ver != TB_STATE_SCHEMA_VERSION:
            problems.append(
                f"SCHEMA_VERSION_MISMATCH expected={TB_STATE_SCHEMA_VERSION} got={ver}"
            )
            return problems  # cannot trust anything further

        # 2. required tables
        for t in ("schema_meta", "events", "basket_current"):
            row = self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (t,),
            ).fetchone()
            if row is None:
                problems.append(f"MISSING_TABLE {t}")

        # 3. sequence monotonicity (contiguous from 1)
        rows = self._conn.execute(
            "SELECT seq FROM events ORDER BY seq"
        ).fetchall()
        seqs = [int(r["seq"]) for r in rows]
        if seqs:
            if seqs[0] != 1:
                problems.append(f"SEQUENCE_GAP first_seq={seqs[0]} != 1")
            for a, b in zip(seqs, seqs[1:]):
                if b != a + 1:
                    problems.append(f"SEQUENCE_GAP after seq={a} (next={b})")

        # 4. payload hash integrity
        for r in self._conn.execute(
            "SELECT event_id, payload, payload_hash FROM events"
        ).fetchall():
            try:
                pl = json.loads(r["payload"] or "{}")
                if payload_hash(pl) != r["payload_hash"]:
                    problems.append(f"PAYLOAD_HASH_MISMATCH event_id={r['event_id']}")
            except (json.JSONDecodeError, TypeError):
                problems.append(f"PAYLOAD_CORRUPT event_id={r['event_id']}")

        # 5. transition validity (every REQUIRED transition event must be in
        #    graph; optional-state events validated when states present)
        required_values = {e.value for e in REQUIRED_TRANSITION_EVENT_TYPES}
        for r in self._conn.execute(
            "SELECT event_id, event_type, prior_state, new_state FROM events"
        ).fetchall():
            et = r["event_type"]
            if et in required_values:
                if not r["prior_state"] or not r["new_state"]:
                    problems.append(
                        f"MISSING_STATES event_id={r['event_id']} type={et}"
                    )
                    continue
                try:
                    ok = is_valid_transition(
                        BasketLifecycleState(r["prior_state"]),
                        BasketLifecycleState(r["new_state"]),
                    )
                    if not ok:
                        problems.append(
                            f"INVALID_TRANSITION event_id={r['event_id']} "
                            f"{r['prior_state']}->{r['new_state']}"
                        )
                except ValueError:
                    problems.append(
                        f"INVALID_STATE_VALUE event_id={r['event_id']} "
                        f"{r['prior_state']}->{r['new_state']}"
                    )
            elif r["prior_state"] or r["new_state"]:
                try:
                    ok = is_valid_transition(
                        BasketLifecycleState(r["prior_state"]),
                        BasketLifecycleState(r["new_state"]),
                    )
                    if not ok:
                        problems.append(
                            f"INVALID_TRANSITION event_id={r['event_id']} "
                            f"{r['prior_state']}->{r['new_state']}"
                        )
                except ValueError:
                    problems.append(
                        f"INVALID_STATE_VALUE event_id={r['event_id']} "
                        f"{r['prior_state']}->{r['new_state']}"
                    )

        # 6. basket_current must be consistent with last event per basket
        for r in self._conn.execute(
            "SELECT basket_id, state, last_seq FROM basket_current"
        ).fetchall():
            last = self._conn.execute(
                "SELECT new_state, seq FROM events WHERE basket_id=? "
                "ORDER BY seq DESC LIMIT 1",
                (r["basket_id"],),
            ).fetchone()
            if last is None:
                problems.append(
                    f"ORPHAN_BASKET_CURRENT {r['basket_id']}"
                )
            elif int(last["seq"]) != int(r["last_seq"]):
                problems.append(
                    f"BASKET_CURRENT_STALE {r['basket_id']} "
                    f"last_seq={r['last_seq']} events_max={last['seq']}"
                )
            elif last["new_state"] != r["state"]:
                problems.append(
                    f"BASKET_CURRENT_MISMATCH {r['basket_id']} "
                    f"current={r['state']} events={last['new_state']}"
                )

        return problems

    # ── reconstruction (solely from durable records) ─────────────────────
    def reconstruct_basket(self, basket_id: str) -> dict:
        """Reconstruct a basket's full truth from events alone.

        Returns:
            {basket_id, strategy_id, state, direction, entry_time_utc,
             entry_basis, entry_z, legs: [fill records], events: n,
             last_seq}
        """
        evs = self.events_for(basket_id=basket_id)
        intent = None
        fills: List[dict] = []
        state = BasketLifecycleState.NO_BASKET.value
        direction = ""
        entry_time_utc = ""
        entry_basis = 0.0
        entry_z = 0.0
        for e in evs:
            if e.new_state:
                state = e.new_state
            if e.event_type == EventType.BASKET_INTENT_CREATED.value:
                intent = e.payload
                direction = e.payload.get("direction", "")
                entry_time_utc = e.payload.get("entry_time_utc", "")
                entry_basis = float(e.payload.get("entry_basis", 0.0) or 0.0)
                entry_z = float(e.payload.get("entry_z", 0.0) or 0.0)
            if e.event_type == EventType.LEG_FILL_CONFIRMED.value:
                fills.append(e.payload)
        return {
            "basket_id": basket_id,
            "strategy_id": evs[0].strategy_id if evs else "",
            "state": state,
            "direction": direction,
            "entry_time_utc": entry_time_utc,
            "entry_basis": entry_basis,
            "entry_z": entry_z,
            "legs": fills,
            "intent": intent,
            "events": len(evs),
            "last_seq": evs[-1].seq if evs else 0,
        }

    def reconstruct_all(self) -> Dict[str, dict]:
        """Reconstruct every basket seen in the ledger."""
        out: Dict[str, dict] = {}
        baskets = set(e.basket_id for e in self.all_events() if e.basket_id)
        for b in sorted(baskets):
            out[b] = self.reconstruct_basket(b)
        return out

    def n_events(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"])
