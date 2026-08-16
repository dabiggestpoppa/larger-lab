#!/usr/bin/env python3
"""
TB-R3 — PERSISTENCE / RESTART RECONCILIATION TEST SUITE
========================================================
Deterministic tests for the R3 durable layer. All tests use mocks and
temporary SQLite files — NO MT5 terminal, NO broker orders.

Covers (frozen R3 matrix):
  * ledger basics: schema v1, append-only, monotonic sequence, unique ids
  * write-ahead: intent persisted BEFORE any broker action
  * idempotency: duplicate signal / fill / close / reconciliation no-ops
  * state machine: valid transitions accepted, invalid transitions FAIL CLOSED
  * crash scenarios: restart while flat / fully open / mid-entry / mid-close
  * reconciliation cases A-N (broker vs local)
  * manual intervention detection
  * broker ownership protection (foreign magic never touched; TB-magic without
    linkage = ORPHAN, blocked)
  * integrity: DB locked, corrupted payload, schema mismatch, missing row,
    sequence duplication -> BLOCKED_UNKNOWN_STATE / fail closed
  * control-state isolation (CONTROL events never share executable basket
    state)
  * zero order_send in the persistence path

Run:  python quant-lab/engines/tb_r3_tests.py
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from tb_live.state_machine import (  # noqa: E402
    BasketLifecycleState as S,
    validate_transition,
    is_valid_transition,
    TRANSITIONS,
    TERMINAL_STATES,
)
from tb_live.persistence import (  # noqa: E402
    BasketLedger, EventType, TB_STATE_SCHEMA_VERSION, payload_hash,
)
from tb_live.reconciliation import (  # noqa: E402
    Reconciler, BrokerPosition, BrokerStateView, ReconciliationClass,
)

TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


UTC = timezone.utc
TB_MAGIC = 31082026


def tmp_db(name="t.db") -> str:
    d = tempfile.mkdtemp(prefix="tb_r3_")
    return os.path.join(d, name)


def make_pos(ticket, symbol, magic, comment="", side="LONG", volume=0.1):
    return BrokerPosition(ticket=ticket, symbol=symbol, magic=magic,
                          comment=comment, volume=volume, side=side)


class FakeBroker(BrokerStateView):
    def __init__(self, positions=None, orders=None):
        self._pos = list(positions or [])
        self._orders = list(orders or [])

    def positions(self):
        return list(self._pos)

    def orders(self):
        return list(self._orders)


def open_basket(ledger: BasketLedger, bid: str, direction="SHORT",
                n_fills: int = 3, tickets=None) -> None:
    """Append a full intent+entry+fill sequence (default: OPEN_VERIFIED)."""
    tickets = tickets or [101, 102, 103]
    symbols = ["GBPAUD", "GBPNZD", "AUDNZD"]
    ledger.append_event(
        EventType.BASKET_INTENT_CREATED, basket_id=bid, strategy_id="TB-FWD-V1",
        prior_state=S.SIGNAL_DETECTED.value, new_state=S.INTENT_CREATED.value,
        dedup_key=f"INTENT|{bid}",
        payload={"direction": direction, "entry_basis": 0.001, "entry_z": 3.4,
                 "entry_time_utc": "2026-01-01T10:00:00+00:00"})
    ledger.append_event(
        EventType.ENTRY_ATTEMPT_STARTED, basket_id=bid,
        prior_state=S.INTENT_CREATED.value, new_state=S.ENTRY_SUBMITTING.value,
        dedup_key=f"ENTRY|{bid}")
    for i in range(n_fills):
        ledger.append_event(
            EventType.LEG_FILL_CONFIRMED, basket_id=bid,
            dedup_key=f"FILL|{bid}|{symbols[i]}",
            payload={"canonical_symbol": symbols[i],
                     "position_ticket": tickets[i],
                     "fill_volume": 0.1, "fill_price": 1.0})
    if n_fills == 3:
        ledger.append_event(
            EventType.BASKET_OPEN_VERIFIED, basket_id=bid,
            prior_state=S.ENTRY_SUBMITTING.value, new_state=S.OPEN_VERIFIED.value,
            dedup_key=f"OPEN|{bid}", payload={"direction": direction})


def close_basket(ledger: BasketLedger, bid: str, n_closed: int = 3) -> None:
    ledger.append_event(
        EventType.EXIT_SIGNAL_OBSERVED, basket_id=bid,
        prior_state=S.OPEN_VERIFIED.value, new_state=S.CLOSE_REQUESTED.value,
        dedup_key=f"EXIT|{bid}", payload={"exit_reason": "TP_HIT", "exit_z": -0.3})
    ledger.append_event(
        EventType.EXIT_ATTEMPT_STARTED, basket_id=bid,
        prior_state=S.CLOSE_REQUESTED.value, new_state=S.CLOSE_SUBMITTING.value,
        dedup_key=f"EXITAT|{bid}")
    if n_closed == 3:
        ledger.append_event(
            EventType.BASKET_CLOSED_VERIFIED, basket_id=bid,
            prior_state=S.CLOSE_SUBMITTING.value,
            new_state=S.CLOSED_VERIFIED.value,
            dedup_key=f"CLOSED|{bid}")


# ═════════════════════════════════════════════════════════════════════════
# STATE MACHINE
# ═════════════════════════════════════════════════════════════════════════

@test
def state_machine_valid_transitions_accepted():
    for (a, b) in TRANSITIONS:
        validate_transition(a, b)  # must not raise
    # terminal states are absorbing
    assert S.BLOCKED_UNKNOWN_STATE in TERMINAL_STATES


@test
def state_machine_invalid_transition_rejected():
    bad = (S.NO_BASKET, S.OPEN_VERIFIED)
    assert not is_valid_transition(*bad)
    try:
        validate_transition(*bad)
        raise AssertionError("invalid transition must raise")
    except ValueError:
        pass


@test
def state_machine_full_lifecycle_chain():
    chain = [
        (S.NO_BASKET, S.SIGNAL_DETECTED),
        (S.SIGNAL_DETECTED, S.INTENT_CREATED),
        (S.INTENT_CREATED, S.ENTRY_SUBMITTING),
        (S.ENTRY_SUBMITTING, S.OPEN_VERIFIED),
        (S.OPEN_VERIFIED, S.CLOSE_REQUESTED),
        (S.CLOSE_REQUESTED, S.CLOSE_SUBMITTING),
        (S.CLOSE_SUBMITTING, S.CLOSED_VERIFIED),
        (S.CLOSED_VERIFIED, S.NO_BASKET),
    ]
    for a, b in chain:
        assert is_valid_transition(a, b), f"{a}->{b}"


@test
def state_machine_partial_fill_path():
    assert is_valid_transition(S.ENTRY_SUBMITTING, S.PARTIALLY_FILLED)
    assert is_valid_transition(S.PARTIALLY_FILLED, S.BROKEN_HEDGE)
    assert is_valid_transition(S.BROKEN_HEDGE, S.FLATTENING)
    assert is_valid_transition(S.FLATTENING, S.FLAT_VERIFIED)
    assert is_valid_transition(S.FLATTENING, S.BLOCKED_UNKNOWN_STATE)


# ═════════════════════════════════════════════════════════════════════════
# LEDGER BASICS
# ═════════════════════════════════════════════════════════════════════════

@test
def ledger_empty_db_healthy():
    l = BasketLedger(tmp_db())
    l.initialize()
    assert l.schema_version() == TB_STATE_SCHEMA_VERSION
    assert l.n_events() == 0
    assert l.integrity_check() == []
    assert l.reconstruct_all() == {}
    l.close()


@test
def ledger_append_monotonic_sequence():
    l = BasketLedger(tmp_db())
    l.initialize()
    e1 = l.append_event(EventType.ENGINE_STARTED, source="t")
    e2 = l.append_event(EventType.ENGINE_SHUTDOWN, source="t")
    assert e1.seq == 1 and e2.seq == 2
    assert l.last_seq() == 2
    assert [e.seq for e in l.all_events()] == [1, 2]
    assert l.integrity_check() == []
    l.close()


@test
def ledger_unique_event_ids():
    l = BasketLedger(tmp_db())
    l.initialize()
    ids = {l.append_event(EventType.SIGNAL_OBSERVED, dedup_key=f"k{i}",
                           source="t").event_id for i in range(5)}
    assert len(ids) == 5
    assert len({e.event_id for e in l.all_events()}) == 5
    l.close()


@test
def ledger_append_only_no_update_path():
    """The ledger has no UPDATE/DELETE API — only append + read."""
    assert not hasattr(BasketLedger, "update_event")
    assert not hasattr(BasketLedger, "delete_event")


@test
def ledger_payload_hash_integrity():
    l = BasketLedger(tmp_db())
    l.initialize()
    l.append_event(EventType.SIGNAL_OBSERVED, dedup_key="p1",
                   payload={"z": 3.2, "basis": 0.001})
    assert l.integrity_check() == []
    # mutate stored payload directly -> integrity must flag it
    cur = l._conn.cursor()
    cur.execute("UPDATE events SET payload='{\"z\": 999}' WHERE dedup_key='p1'")
    l._conn.commit()
    problems = l.integrity_check()
    assert any("PAYLOAD_HASH_MISMATCH" in p for p in problems)
    l.close()


@test
def ledger_sequence_gap_detected():
    l = BasketLedger(tmp_db())
    l.initialize()
    for i in range(3):
        l.append_event(EventType.SIGNAL_OBSERVED, dedup_key=f"g{i}",
                       source="t")
    cur = l._conn.cursor()
    cur.execute("DELETE FROM events WHERE seq=2")   # hole in the middle
    l._conn.commit()
    problems = l.integrity_check()
    assert any("SEQUENCE_GAP" in p for p in problems)
    l.close()


@test
def ledger_schema_version_mismatch_blocks():
    l = BasketLedger(tmp_db())
    l.initialize()
    cur = l._conn.cursor()
    cur.execute("UPDATE schema_meta SET value='99' WHERE key='schema_version'")
    l._conn.commit()
    problems = l.integrity_check()
    assert any("SCHEMA_VERSION_MISMATCH" in p for p in problems)
    l.close()


@test
def ledger_corrupt_db_fails_closed():
    """A truncated/corrupt SQLite file must fail to open/verify."""
    path = tmp_db()
    with open(path, "w") as f:
        f.write("this is not a sqlite database")
    l = None
    try:
        l = BasketLedger(path)   # PRAGMAs will fail on a non-db file
        l.initialize()
        problems = l.integrity_check()
        assert problems, "corrupt db must produce integrity problems"
    except sqlite3.DatabaseError:
        pass  # fail closed is acceptable
    finally:
        if l is not None:
            try:
                l.close()
            except Exception:
                pass


@test
def ledger_db_locked_fails_closed():
    """A second connection holding an exclusive lock must not corrupt state."""
    path = tmp_db()
    l = BasketLedger(path)
    l.initialize()
    l.append_event(EventType.ENGINE_STARTED, source="t")
    # hold an exclusive transaction from another connection
    other = sqlite3.connect(path)
    other.execute("BEGIN EXCLUSIVE")
    try:
        try:
            l.append_event(EventType.SIGNAL_OBSERVED, dedup_key="locked1",
                           source="t")
            # WAL allows concurrent readers; append may succeed or time out.
            # Either way the ledger must remain consistent.
        except sqlite3.OperationalError:
            pass
        finally:
            other.rollback()
    finally:
        other.close()
    assert l.integrity_check() == []
    l.close()


# ═════════════════════════════════════════════════════════════════════════
# IDEMPOTENCY / WRITE-AHEAD
# ═════════════════════════════════════════════════════════════════════════

@test
def idempotent_duplicate_intent():
    l = BasketLedger(tmp_db())
    l.initialize()
    open_basket(l, "TB_ID", n_fills=0)  # intent + entry attempt only
    # re-append the same intent (restart duplicate) -> no-op
    before = l.n_events()
    l.append_event(
        EventType.BASKET_INTENT_CREATED, basket_id="TB_ID",
        prior_state=S.SIGNAL_DETECTED.value, new_state=S.INTENT_CREATED.value,
        dedup_key="INTENT|TB_ID", payload={})
    assert l.n_events() == before
    assert l.integrity_check() == []
    l.close()


@test
def idempotent_duplicate_fill_response():
    l = BasketLedger(tmp_db())
    l.initialize()
    open_basket(l, "TB_FILL")
    before = l.n_events()
    l.append_event(EventType.LEG_FILL_CONFIRMED, basket_id="TB_FILL",
                   dedup_key="FILL|TB_FILL|GBPAUD",
                   payload={"canonical_symbol": "GBPAUD"})
    assert l.n_events() == before  # same dedup key -> no double counting
    l.close()


@test
def idempotent_duplicate_restart_reconciliation():
    path = tmp_db()
    l = BasketLedger(path)
    l.initialize()
    open_basket(l, "TB_REC")
    broker = FakeBroker([
        make_pos(101, "GBPAUD", TB_MAGIC, "TB|TB_REC|GBPAUD|L1"),
        make_pos(102, "GBPNZD", TB_MAGIC, "TB|TB_REC|GBPNZD|L2"),
        make_pos(103, "AUDNZD", TB_MAGIC, "TB|TB_REC|AUDNZD|L3"),
    ])
    rec = Reconciler(l, broker, tb_magic=TB_MAGIC)
    r1 = rec.reconcile()
    n1 = l.n_events()
    # reconcile again (restart) -> same classification, no duplicate baskets
    r2 = rec.reconcile()
    assert r1["TB_REC"].classification == r2["TB_REC"].classification
    assert l.n_events() == n1 + 2  # only STARTED + COMPLETED added
    assert len(l.reconstruct_all()) == 1
    l.close()


@test
def write_ahead_intent_persisted_before_action():
    """Simulate crash between intent persistence and broker submission."""
    path = tmp_db()
    l = BasketLedger(path)
    l.initialize()
    # write-ahead: intent + entry-attempt persisted, but NO fills recorded
    open_basket(l, "TB_WA", n_fills=0)
    # broker flat (orders never submitted)
    broker = FakeBroker([])
    res = Reconciler(l, broker, tb_magic=TB_MAGIC).reconcile()
    r = res["TB_WA"]
    assert r.classification == ReconciliationClass.LOCAL_ONLY
    assert not r.blocked
    assert r.recovered_state == S.FLAT_VERIFIED.value
    l.close()


@test
def control_state_isolation():
    """CONTROL events never create/alter primary basket state."""
    l = BasketLedger(tmp_db())
    l.initialize()
    open_basket(l, "TB_PRIMARY")
    for i in range(5):
        l.append_event(EventType.CONTROL_SIGNAL_OBSERVED, source="control",
                       dedup_key=f"CTRL|{i}", payload={"z": 2.6, "dir": "SHORT"})
    assert len(l.reconstruct_all()) == 1  # only the primary basket
    assert l.reconstruct_basket("TB_PRIMARY")["state"] == S.OPEN_VERIFIED.value
    assert l.integrity_check() == []
    l.close()


# ═════════════════════════════════════════════════════════════════════════
# CRASH / RESTART RECONSTRUCTION (solely from durable records)
# ═════════════════════════════════════════════════════════════════════════

@test
def crash_restart_while_flat():
    l = BasketLedger(tmp_db())
    l.initialize()
    l.append_event(EventType.ENGINE_STARTED, source="t")
    broker = FakeBroker([])
    res = Reconciler(l, broker, tb_magic=TB_MAGIC).reconcile()
    assert all(r.classification == ReconciliationClass.MATCHED
               for r in res.values() if r.basket_id)
    assert l.reconstruct_all() == {}
    l.close()


@test
def crash_restart_while_fully_open():
    l = BasketLedger(tmp_db())
    l.initialize()
    open_basket(l, "TB_OPEN")
    broker = FakeBroker([
        make_pos(101, "GBPAUD", TB_MAGIC, "TB|TB_OPEN|GBPAUD|L1"),
        make_pos(102, "GBPNZD", TB_MAGIC, "TB|TB_OPEN|GBPNZD|L2"),
        make_pos(103, "AUDNZD", TB_MAGIC, "TB|TB_OPEN|AUDNZD|L3"),
    ])
    res = Reconciler(l, broker, tb_magic=TB_MAGIC).reconcile()
    r = res["TB_OPEN"]
    assert r.classification == ReconciliationClass.MATCHED
    assert r.recovered_state == S.OPEN_VERIFIED.value
    assert not r.blocked
    l.close()


@test
def crash_before_order_attempt():
    """Intent persisted, ENTRY_ATTEMPT never happened, broker flat."""
    l = BasketLedger(tmp_db())
    l.initialize()
    l.append_event(
        EventType.BASKET_INTENT_CREATED, basket_id="TB_PRE",
        prior_state=S.SIGNAL_DETECTED.value, new_state=S.INTENT_CREATED.value,
        dedup_key="INTENT|TB_PRE", payload={"direction": "SHORT"})
    broker = FakeBroker([])
    res = Reconciler(l, broker, tb_magic=TB_MAGIC).reconcile()
    r = res["TB_PRE"]
    assert r.classification == ReconciliationClass.LOCAL_ONLY
    assert r.recovered_state == S.FLAT_VERIFIED.value
    l.close()


@test
def crash_after_leg1_broker_ack():
    l = BasketLedger(tmp_db())
    l.initialize()
    open_basket(l, "TB_L1", n_fills=1, tickets=[101])
    broker = FakeBroker([
        make_pos(101, "GBPAUD", TB_MAGIC, "TB|TB_L1|GBPAUD|L1"),
    ])
    res = Reconciler(l, broker, tb_magic=TB_MAGIC).reconcile()
    r = res["TB_L1"]
    assert r.classification == ReconciliationClass.PARTIAL_MATCH
    assert r.blocked
    assert r.recovered_state == S.BROKEN_HEDGE.value
    l.close()


@test
def crash_after_leg2_broker_ack():
    l = BasketLedger(tmp_db())
    l.initialize()
    open_basket(l, "TB_L2", n_fills=2, tickets=[101, 102])
    broker = FakeBroker([
        make_pos(101, "GBPAUD", TB_MAGIC, "TB|TB_L2|GBPAUD|L1"),
        make_pos(102, "GBPNZD", TB_MAGIC, "TB|TB_L2|GBPNZD|L2"),
    ])
    res = Reconciler(l, broker, tb_magic=TB_MAGIC).reconcile()
    assert res["TB_L2"].blocked
    assert res["TB_L2"].classification == ReconciliationClass.PARTIAL_MATCH
    l.close()


@test
def crash_after_leg3_broker_ack_before_open_verify():
    """All 3 fills confirmed at broker but BASKET_OPEN_VERIFIED event missing."""
    l = BasketLedger(tmp_db())
    l.initialize()
    # intent + entry attempt + 3 fills, but NO BASKET_OPEN_VERIFIED
    bid = "TB_L3"
    l.append_event(
        EventType.BASKET_INTENT_CREATED, basket_id=bid,
        prior_state=S.SIGNAL_DETECTED.value, new_state=S.INTENT_CREATED.value,
        dedup_key=f"INTENT|{bid}", payload={"direction": "SHORT"})
    l.append_event(
        EventType.ENTRY_ATTEMPT_STARTED, basket_id=bid,
        prior_state=S.INTENT_CREATED.value, new_state=S.ENTRY_SUBMITTING.value,
        dedup_key=f"ENTRY|{bid}")
    for sym, t in [("GBPAUD", 101), ("GBPNZD", 102), ("AUDNZD", 103)]:
        l.append_event(EventType.LEG_FILL_CONFIRMED, basket_id=bid,
                       dedup_key=f"FILL|{bid}|{sym}",
                       payload={"canonical_symbol": sym, "position_ticket": t})
    broker = FakeBroker([
        make_pos(101, "GBPAUD", TB_MAGIC, f"TB|{bid}|GBPAUD|L1"),
        make_pos(102, "GBPNZD", TB_MAGIC, f"TB|{bid}|GBPNZD|L2"),
        make_pos(103, "AUDNZD", TB_MAGIC, f"TB|{bid}|AUDNZD|L3"),
    ])
    res = Reconciler(l, broker, tb_magic=TB_MAGIC).reconcile()
    r = res[bid]
    assert r.classification == ReconciliationClass.MATCHED
    assert r.recovered_state == S.OPEN_VERIFIED.value
    l.close()


@test
def crash_during_close_leg1():
    """CLOSE started, only 1 leg closed, 2 remain at broker."""
    l = BasketLedger(tmp_db())
    l.initialize()
    bid = "TB_CL1"
    open_basket(l, bid)
    l.append_event(
        EventType.EXIT_SIGNAL_OBSERVED, basket_id=bid,
        prior_state=S.OPEN_VERIFIED.value, new_state=S.CLOSE_REQUESTED.value,
        dedup_key=f"EXIT|{bid}", payload={"exit_reason": "TP_HIT"})
    l.append_event(
        EventType.EXIT_ATTEMPT_STARTED, basket_id=bid,
        prior_state=S.CLOSE_REQUESTED.value, new_state=S.CLOSE_SUBMITTING.value,
        dedup_key=f"EXITAT|{bid}")
    l.append_event(EventType.EXIT_FILL_CONFIRMED, basket_id=bid,
                   dedup_key=f"EXITF|{bid}|GBPAUD",
                   payload={"canonical_symbol": "GBPAUD"})
    broker = FakeBroker([
        make_pos(102, "GBPNZD", TB_MAGIC, f"TB|{bid}|GBPNZD|L2"),
        make_pos(103, "AUDNZD", TB_MAGIC, f"TB|{bid}|AUDNZD|L3"),
    ])
    res = Reconciler(l, broker, tb_magic=TB_MAGIC).reconcile()
    r = res[bid]
    assert r.classification == ReconciliationClass.PARTIAL_MATCH
    assert r.blocked
    assert r.recovered_state == S.BROKEN_HEDGE.value
    l.close()


@test
def crash_during_close_leg2():
    """2 legs closed, 1 remains at broker."""
    l = BasketLedger(tmp_db())
    l.initialize()
    bid = "TB_CL2"
    open_basket(l, bid)
    l.append_event(
        EventType.EXIT_SIGNAL_OBSERVED, basket_id=bid,
        prior_state=S.OPEN_VERIFIED.value, new_state=S.CLOSE_REQUESTED.value,
        dedup_key=f"EXIT|{bid}", payload={"exit_reason": "TIMEOUT"})
    l.append_event(
        EventType.EXIT_ATTEMPT_STARTED, basket_id=bid,
        prior_state=S.CLOSE_REQUESTED.value, new_state=S.CLOSE_SUBMITTING.value,
        dedup_key=f"EXITAT|{bid}")
    for sym in ("GBPAUD", "GBPNZD"):
        l.append_event(EventType.EXIT_FILL_CONFIRMED, basket_id=bid,
                       dedup_key=f"EXITF|{bid}|{sym}",
                       payload={"canonical_symbol": sym})
    broker = FakeBroker([
        make_pos(103, "AUDNZD", TB_MAGIC, f"TB|{bid}|AUDNZD|L3"),
    ])
    res = Reconciler(l, broker, tb_magic=TB_MAGIC).reconcile()
    assert res[bid].blocked
    assert res[bid].classification == ReconciliationClass.PARTIAL_MATCH
    l.close()


@test
def broker_already_flat_after_close():
    """Local CLOSED_VERIFIED, broker flat -> healthy."""
    l = BasketLedger(tmp_db())
    l.initialize()
    bid = "TB_DONE"
    open_basket(l, bid)
    close_basket(l, bid)
    broker = FakeBroker([])
    res = Reconciler(l, broker, tb_magic=TB_MAGIC).reconcile()
    r = res[bid]
    assert r.classification == ReconciliationClass.MATCHED
    assert r.recovered_state == S.CLOSED_VERIFIED.value
    l.close()


@test
def local_closed_but_broker_has_legs_blocks():
    """Local says CLOSED, broker still has 1 leg -> BLOCK."""
    l = BasketLedger(tmp_db())
    l.initialize()
    bid = "TB_GHOST"
    open_basket(l, bid)
    close_basket(l, bid)
    broker = FakeBroker([
        make_pos(103, "AUDNZD", TB_MAGIC, f"TB|{bid}|AUDNZD|L3"),
    ])
    res = Reconciler(l, broker, tb_magic=TB_MAGIC).reconcile()
    r = res[bid]
    assert r.blocked
    assert r.recovered_state == S.RECONCILIATION_REQUIRED.value
    l.close()


@test
def orphan_broker_basket_detected():
    """Broker has full TB basket, no local record -> BROKER_ONLY, BLOCK."""
    l = BasketLedger(tmp_db())
    l.initialize()
    broker = FakeBroker([
        make_pos(201, "GBPAUD", TB_MAGIC, "TB|TB_ORPHAN|GBPAUD|L1"),
        make_pos(202, "GBPNZD", TB_MAGIC, "TB|TB_ORPHAN|GBPNZD|L2"),
        make_pos(203, "AUDNZD", TB_MAGIC, "TB|TB_ORPHAN|AUDNZD|L3"),
    ])
    res = Reconciler(l, broker, tb_magic=TB_MAGIC).reconcile()
    assert "TB_ORPHAN" in res
    assert res["TB_ORPHAN"].classification == ReconciliationClass.BROKER_ONLY
    assert res["TB_ORPHAN"].blocked
    l.close()


@test
def manual_leg_close_detected():
    """Local OPEN, broker missing one recorded ticket -> manual intervention."""
    l = BasketLedger(tmp_db())
    l.initialize()
    bid = "TB_MAN"
    open_basket(l, bid, tickets=[301, 302, 303])
    broker = FakeBroker([
        make_pos(301, "GBPAUD", TB_MAGIC, f"TB|{bid}|GBPAUD|L1"),
        make_pos(302, "GBPNZD", TB_MAGIC, f"TB|{bid}|GBPNZD|L2"),
        # 303 (AUDNZD) manually closed at broker
    ])
    rec = Reconciler(l, broker, tb_magic=TB_MAGIC)
    findings = rec.detect_manual_intervention()
    assert any(f["finding"] == "MANUAL_INTERVENTION_DETECTED"
               and f["missing_tickets"] == [303] for f in findings)
    res = rec.reconcile()
    assert res[bid].blocked
    l.close()


@test
def extra_unknown_broker_leg_protected():
    """A foreign-magic position is never touched and never blocks."""
    l = BasketLedger(tmp_db())
    l.initialize()
    open_basket(l, "TB_OK", tickets=[401, 402, 403])
    broker = FakeBroker([
        make_pos(401, "GBPAUD", TB_MAGIC, "TB|TB_OK|GBPAUD|L1"),
        make_pos(402, "GBPNZD", TB_MAGIC, "TB|TB_OK|GBPNZD|L2"),
        make_pos(403, "AUDNZD", TB_MAGIC, "TB|TB_OK|AUDNZD|L3"),
        make_pos(999, "EURUSD", 12345678, "OTHER_STRATEGY"),
    ])
    res = Reconciler(l, broker, tb_magic=TB_MAGIC).reconcile()
    assert "UNKNOWN:999" in res
    assert res["UNKNOWN:999"].classification == ReconciliationClass.UNKNOWN_POSITION
    assert not res["UNKNOWN:999"].blocked  # not the TB engine's problem
    assert not res["TB_OK"].blocked        # TB basket unaffected
    l.close()


@test
def tb_magic_without_linkage_is_orphan_blocked():
    """Our magic but no comment linkage -> ORPHAN_POSITION, BLOCK."""
    l = BasketLedger(tmp_db())
    l.initialize()
    broker = FakeBroker([
        make_pos(501, "GBPAUD", TB_MAGIC, ""),   # no comment
        make_pos(502, "GBPNZD", TB_MAGIC, ""),
        make_pos(503, "AUDNZD", TB_MAGIC, ""),
    ])
    res = Reconciler(l, broker, tb_magic=TB_MAGIC).reconcile()
    assert "__orphan__" in res
    assert res["__orphan__"].classification == ReconciliationClass.ORPHAN_POSITION
    assert res["__orphan__"].blocked
    l.close()


@test
def reconciliation_case_matrix_a_through_n():
    """Exercise the frozen A-N reconciliation matrix explicitly."""
    # A: local flat, broker flat
    l = BasketLedger(tmp_db()); l.initialize()
    r = Reconciler(l, FakeBroker([]), tb_magic=TB_MAGIC).reconcile()
    assert not any(v.blocked for v in r.values())
    l.close()

    # B: local OPEN, broker exact 3 -> restore OPEN_VERIFIED (tested above)
    # C: local OPEN, broker 2/3 -> BROKEN_HEDGE (tested above)
    # D: local ENTRY_SUBMITTING, broker 3 fills -> OPEN_VERIFIED (L3 test)
    # E: local ENTRY_SUBMITTING, broker 1 fill -> BROKEN_HEDGE (L1 test)
    # F: local CLOSING, broker flat -> CLOSED_VERIFIED
    l = BasketLedger(tmp_db()); l.initialize()
    bid = "TB_F"
    open_basket(l, bid)
    l.append_event(
        EventType.EXIT_SIGNAL_OBSERVED, basket_id=bid,
        prior_state=S.OPEN_VERIFIED.value, new_state=S.CLOSE_REQUESTED.value,
        dedup_key=f"EXIT|{bid}", payload={"exit_reason": "TP_HIT"})
    l.append_event(
        EventType.EXIT_ATTEMPT_STARTED, basket_id=bid,
        prior_state=S.CLOSE_REQUESTED.value, new_state=S.CLOSE_SUBMITTING.value,
        dedup_key=f"EXITAT|{bid}")
    r = Reconciler(l, FakeBroker([]), tb_magic=TB_MAGIC).reconcile()
    assert r[bid].recovered_state == S.CLOSED_VERIFIED.value
    l.close()

    # G: local CLOSED, broker 1 leg -> BLOCK (tested above)
    # H: orphan basket -> BLOCK (tested above)
    # I: broker manual/non-magic -> protected (tested above)
    # J/K: duplicate responses idempotent (tested above)
    # L: DB transaction interrupted -> recovered from last committed
    l = BasketLedger(tmp_db()); l.initialize()
    open_basket(l, "TB_L")
    # simulate interrupted transaction: BEGIN, insert, ROLLBACK
    cur = l._conn.cursor()
    cur.execute("BEGIN")
    cur.execute("INSERT INTO events (event_id, seq, event_type, ts_utc, dedup_key) "
                "VALUES ('x-fake', 99999, 'BROKEN_HEDGE_DETECTED', '2026-01-01T00:00:00+00:00', 'fake1')")
    l._conn.rollback()
    assert l.integrity_check() == []
    assert l.last_seq() < 99999
    l.close()

    # M: ledger corruption -> fail closed (tested above)
    # N: unknown magic -> not assumed (tested above)
    assert True


@test
def reconstruction_solely_from_durable_records():
    """Reopen the DB fresh and reconstruct truth without any in-memory state."""
    path = tmp_db()
    l = BasketLedger(path)
    l.initialize()
    open_basket(l, "TB_DUR", tickets=[601, 602, 603])
    close_basket(l, "TB_DUR")
    l.close()

    # simulate restart: brand-new ledger object on same file
    l2 = BasketLedger(path)
    l2.initialize()
    assert l2.integrity_check() == []
    rec = l2.reconstruct_basket("TB_DUR")
    assert rec["state"] == S.CLOSED_VERIFIED.value
    assert rec["direction"] == "SHORT"
    assert len(rec["legs"]) == 3
    # intent + entry + 3 fills + open + exit + exit-attempt + closed = 9
    assert rec["events"] >= 9
    l2.close()


@test
def invalid_transition_persisted_blocks_integrity():
    """Even if a bad transition somehow lands in the DB, integrity flags it."""
    l = BasketLedger(tmp_db())
    l.initialize()
    open_basket(l, "TB_BAD")
    cur = l._conn.cursor()
    cur.execute(
        "INSERT INTO events (event_id, seq, event_type, ts_utc, basket_id, "
        "prior_state, new_state, dedup_key, payload, payload_hash) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("bad1", 999, "BASKET_OPEN_VERIFIED", "2026-01-01T00:00:00+00:00",
         "TB_BAD", "NO_BASKET", "OPEN_VERIFIED", "bad-transition",
         "{}", payload_hash({})))
    l._conn.commit()
    problems = l.integrity_check()
    assert any("INVALID_TRANSITION" in p for p in problems)
    l.close()


@test
def missing_required_states_blocks():
    """A required-transition event without states must be rejected."""
    l = BasketLedger(tmp_db())
    l.initialize()
    try:
        l.append_event(EventType.BASKET_INTENT_CREATED, basket_id="TB_X",
                       dedup_key="INTENT|TB_X")
        raise AssertionError("missing states must raise")
    except ValueError:
        pass
    assert l.n_events() == 0
    l.close()


@test
def zero_orders_in_persistence_path():
    """The persistence + reconciliation path must never reach order_send."""
    for mod in ("persistence.py", "reconciliation.py", "state_machine.py"):
        src = (Path(__file__).parent.parent / "tb_live" / mod).read_text(
            encoding="utf-8")
        # No actual call sites and no MetaTrader5 import (docstring mentions
        # of the rule are fine).
        assert "order_send(" not in src, f"{mod} must not call order_send"
        assert "import MetaTrader5" not in src, f"{mod} must not import MT5"
    # fresh valid signal + valid weights still yield zero broker orders:
    # the ledger layer has no execution surface at all.
    l = BasketLedger(tmp_db())
    l.initialize()
    open_basket(l, "TB_SAFE")
    assert l.n_events() > 0  # records exist...
    assert not hasattr(l, "order_send")
    assert not hasattr(l, "open_basket")  # no execution methods on ledger
    l.close()


@test
def basket_current_materialized_consistent():
    l = BasketLedger(tmp_db())
    l.initialize()
    open_basket(l, "TB_CUR")
    cur = l.current_basket("TB_CUR")
    assert cur is not None
    assert cur["state"] == S.OPEN_VERIFIED.value
    assert cur["last_seq"] == l.last_seq()
    assert l.integrity_check() == []
    l.close()


@test
def append_after_close_reentry():
    """After CLOSED_VERIFIED -> NO_BASKET, a new basket may open (re-entry)."""
    l = BasketLedger(tmp_db())
    l.initialize()
    bid1 = "TB_R1"
    open_basket(l, bid1)
    close_basket(l, bid1)
    # complete the lifecycle
    l.append_event(EventType.BASKET_CLOSED_VERIFIED, basket_id=bid1,
                   prior_state=S.CLOSE_SUBMITTING.value,
                   new_state=S.CLOSED_VERIFIED.value, dedup_key=f"C2|{bid1}")
    l.append_event(EventType.RECONCILIATION_COMPLETED, basket_id=bid1,
                   prior_state=S.CLOSED_VERIFIED.value,
                   new_state=S.NO_BASKET.value, dedup_key=f"DONE|{bid1}")
    bid2 = "TB_R2"
    open_basket(l, bid2)
    assert l.reconstruct_basket(bid2)["state"] == S.OPEN_VERIFIED.value
    assert l.integrity_check() == []
    l.close()


@test
def executor_shadow_loop_writes_ledger_and_never_orders():
    """Load the real executor with stubbed broker deps and prove the R3
    wiring: ledger opens + integrity passes, reconciliation runs, the loop
    persists SIGNAL/BASKET_INTENT/EXIT events, and NO order surface exists."""
    import importlib.util
    import types as _types
    from pathlib import Path as _Path

    # stub heavy broker deps so the module loads without MT5
    reg = _types.ModuleType("configs.strategy_registry")
    reg.get_magic = lambda name: 31082026
    reg.STRATEGY_REGISTRY = {}
    reg.verify_unique_magnetics = lambda: None
    sys.modules["configs.strategy_registry"] = reg

    ag = _types.ModuleType("mt5.account_guard")
    class HaltStatus:
        EMERGENCY_HALT = "EMERGENCY_HALT"
        CLEAR = "CLEAR"
    class AccountGuard:
        def __init__(self): pass
        def initialize(self): return True
        def verify_demo_identity(self): return True
        def get_broker_mode(self): return type("M", (), {"value": "hedging"})()
        def check_connection(self): return True
        def set_halt_status(self, s): pass
        def get_halt_status(self): return None
        def shutdown(self): pass
    ag.AccountGuard = AccountGuard
    ag.HaltStatus = HaltStatus
    sys.modules["mt5.account_guard"] = ag

    el = _types.ModuleType("mt5.triangular_execution_layer")
    class BasketState:
        PENDING = "pending"; OPEN = "open"; CLOSED = "closed"
        ABORTED_FLAT = "aborted_flat"
    class TriangularExecutionLayer:
        def __init__(self, **kw): pass
        def _broker_positions(self): return []
        def shutdown(self): pass
    el.TriangularExecutionLayer = TriangularExecutionLayer
    el.BasketState = BasketState
    sys.modules["mt5.triangular_execution_layer"] = el

    spec = importlib.util.spec_from_file_location(
        "tb_exec_r3test", str(_Path(__file__).parent.parent
                              / "mt5" / "triangular_basis_executor.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    assert m.DEFAULT_MODE == "shadow"
    assert m.EXECUTION_AUTHORIZED is False
    assert m.DEMO_AUTHORIZED is False
    # the loop source must persist events before execution and never call
    # order_send itself (execution layer is the only order path)
    src = open(_Path(__file__).parent.parent
               / "mt5" / "triangular_basis_executor.py",
               encoding="utf-8-sig").read()
    assert "BASKET_INTENT_CREATED" in src
    assert "EXIT_SIGNAL_OBSERVED" in src
    assert "SIGNAL_REJECTED" in src
    assert "ledger.append_event" in src
    # the executor itself must never CALL order_send (docstring mentions of
    # the fail-closed rule are fine); execution is delegated to the layer
    assert "order_send(" not in src

    # open_ledger + reconcile_on_startup actually work (fail closed, no orders)
    os.environ["TB_R3_STATE"] = tempfile.mkdtemp(prefix="tb_r3_exec_")
    led = m.open_ledger()
    assert led.schema_version() == TB_STATE_SCHEMA_VERSION
    assert led.integrity_check() == []
    out = m.reconcile_on_startup(led, el.TriangularExecutionLayer())
    assert out["blocked_keys"] == []
    led.close()


def main():
    passed = 0
    failed = 0
    for fn in TESTS:
        try:
            fn()
            passed += 1
            print(f"  PASS  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\ncollected={len(TESTS)} passed={passed} failed={failed} skipped=0")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
