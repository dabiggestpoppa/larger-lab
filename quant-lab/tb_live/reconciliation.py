"""
TB-R3 — Broker/Local Reconciliation
====================================

On startup the engine MUST NOT immediately process new signals. It first:

    1. opens the persistence store,
    2. integrity-checks the ledger,
    3. reconstructs latest local basket state (from durable records ONLY),
    4. queries broker positions,
    5. compares expected vs broker truth,
    6. reconciles (classify + decide whether the engine may proceed),
    7. only then permits the SHADOW strategy loop.

This module is pure logic over two inputs:

    ledger       -- BasketLedger (local durable truth)
    broker_view  -- a BrokerStateView (positions/orders exposed by the
                    execution layer or a mock in tests)

It NEVER sends orders and NEVER flattens positions. R3 is not authorized to
invent live recovery actions: divergence -> RECONCILIATION_REQUIRED /
BLOCKED_UNKNOWN_STATE, never a silent action.

BROKER OWNERSHIP RULE (frozen):
    A broker position is "owned" by the TB engine ONLY through explicit
    identity evidence:
        * magic number == TB magic, AND
        * comment contains the basket id (TB|<basket_id>|...), OR
        * a persisted execution linkage (LEG_FILL_CONFIRMED event recorded the
          broker position ticket for this basket).
    Positions with unknown magic/comment are UNKNOWN_POSITION: never altered,
    never assumed.

MECHANICAL CHANGE ONLY: no strategy math here.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from tb_live.persistence import (
    BasketLedger,
    EventType,
    utcnow_iso,
    stable_id,
)
from tb_live.state_machine import BasketLifecycleState


# ─── CLASSIFICATION (R3 frozen set) ──────────────────────────────────────

class ReconciliationClass(str, Enum):
    MATCHED = "MATCHED"                 # local + broker agree
    BROKER_ONLY = "BROKER_ONLY"         # broker has TB basket, local has none
    LOCAL_ONLY = "LOCAL_ONLY"           # local has intent, broker flat
    PARTIAL_MATCH = "PARTIAL_MATCH"     # some legs present, not all
    ORPHAN_POSITION = "ORPHAN_POSITION" # TB-tagged but no basket linkage
    UNKNOWN_POSITION = "UNKNOWN_POSITION"  # not TB-owned; never touch


@dataclass
class BrokerPosition:
    """Normalized broker position view (broker-agnostic)."""

    ticket: int
    symbol: str
    magic: int
    comment: str = ""
    volume: float = 0.0
    side: str = ""          # LONG / SHORT
    price_open: float = 0.0

    @property
    def basket_token(self) -> Optional[str]:
        """Extract the TB basket id token from the comment, if any.

        Comment format: "TB|<basket_id>|<canonical_symbol>|<leg_id>"
        """
        if not self.comment:
            return None
        tokens = [t.strip() for t in self.comment.split("|")]
        if len(tokens) >= 2 and tokens[0] == "TB" and tokens[1]:
            return tokens[1]
        for token in tokens:
            if token.startswith("TB") and len(token) > 16:
                return token
        return None


class BrokerStateView:
    """Interface the reconciler uses to see broker truth.

    Production: wrap TriangularExecutionLayer._broker_positions().
    Tests: inject a FakeBroker.
    """

    def positions(self) -> List[BrokerPosition]:
        raise NotImplementedError

    def orders(self) -> List[dict]:
        """Pending orders (usually empty in shadow/market-deal flow)."""
        return []


@dataclass
class ReconciliationResult:
    """Outcome for one basket (or one unowned position)."""

    basket_id: str
    classification: ReconciliationClass
    local_state: str = ""
    broker_legs: int = 0
    expected_legs: int = 0
    action: str = "NONE"                # NONE / BLOCK / RECONCILE / FLATTEN_REFUSED
    blocked: bool = False
    detail: str = ""
    recovered_state: str = ""

    def to_dict(self) -> dict:
        return {
            "basket_id": self.basket_id,
            "classification": self.classification.value,
            "local_state": self.local_state,
            "broker_legs": self.broker_legs,
            "expected_legs": self.expected_legs,
            "action": self.action,
            "blocked": self.blocked,
            "detail": self.detail,
            "recovered_state": self.recovered_state,
        }


# ─── RECONCILER ──────────────────────────────────────────────────────────

class Reconciler:
    """Compare durable local truth vs broker truth and classify per R3."""

    def __init__(self, ledger: BasketLedger, broker_view: BrokerStateView,
                 tb_magic: int = 31082026,
                 expected_leg_symbols: tuple = ("GBPAUD", "GBPNZD", "AUDNZD")):
        self.ledger = ledger
        self.broker = broker_view
        self.tb_magic = tb_magic
        self.expected_leg_symbols = tuple(expected_leg_symbols)

    # ── ownership ────────────────────────────────────────────────────────
    def is_tb_owned(self, pos: BrokerPosition) -> bool:
        """Explicit ownership evidence: magic match AND (basket token OR
        persisted execution linkage)."""
        if pos.magic != self.tb_magic:
            return False
        if pos.basket_token:
            return True
        # Persisted execution linkage: did we record this ticket for a basket?
        for e in self.ledger.events_for(event_type=EventType.LEG_FILL_CONFIRMED.value):
            if int(e.payload.get("position_ticket", 0) or 0) == pos.ticket:
                return True
        return False

    def classify_tb_owned(self, pos: BrokerPosition) -> Optional[str]:
        """Return the basket_id this TB-owned position belongs to, or None."""
        token = pos.basket_token
        if token:
            return token
        for e in self.ledger.events_for(event_type=EventType.LEG_FILL_CONFIRMED.value):
            if int(e.payload.get("position_ticket", 0) or 0) == pos.ticket:
                return e.basket_id
        return None

    # ── main entry ───────────────────────────────────────────────────────
    def reconcile(self, run_id: str = "") -> Dict[str, ReconciliationResult]:
        """Run full reconciliation. Returns {key: result}.

        Keys: basket_id for TB baskets, or "UNKNOWN:<ticket>" for unowned
        positions. The engine must NOT proceed if any result is blocked.
        """
        run_id = run_id or stable_id("RECON", utcnow_iso())
        self.ledger.append_event(
            EventType.RECONCILIATION_STARTED,
            source="reconciler", reason=run_id,
        )

        local = self.ledger.reconstruct_all()
        positions = self.broker.positions()
        results: Dict[str, ReconciliationResult] = {}

        # Group broker positions: TB-owned by basket; our-magic-but-unlinked
        # and foreign-magic separated for distinct handling.
        by_basket: Dict[str, List[BrokerPosition]] = {}
        orphan_tagged: List[BrokerPosition] = []
        unknown: List[BrokerPosition] = []
        for p in positions:
            if p.magic != self.tb_magic:
                # Foreign magic: definitely not ours. NEVER altered, NEVER
                # blocks the TB engine — but logged as off-limits.
                unknown.append(p)
                continue
            if not self.is_tb_owned(p):
                # Our magic but no basket linkage: possibly ours from a lost
                # ledger. Do NOT assume ownership -> BLOCK (orphan).
                orphan_tagged.append(p)
                continue
            bid = self.classify_tb_owned(p) or "__orphan__"
            by_basket.setdefault(bid, []).append(p)

        # 1. every local basket vs broker
        for bid, lrec in local.items():
            broker_legs = by_basket.get(bid, [])
            results[bid] = self._reconcile_basket(bid, lrec, broker_legs)

        # 2. TB-tagged broker baskets with no local record -> orphan/foreign
        for bid, poss in by_basket.items():
            if bid not in results:
                results[bid] = ReconciliationResult(
                    basket_id=bid,
                    classification=ReconciliationClass.BROKER_ONLY,
                    local_state=BasketLifecycleState.NO_BASKET.value,
                    broker_legs=len(poss),
                    expected_legs=3,
                    action="RECONCILE",
                    blocked=True,
                    detail="Broker has a TB basket with no local durable record "
                           "(lost ledger or foreign basket) — BLOCK",
                )

        # 2b. our-magic-but-unlinked positions: ORPHAN_POSITION, BLOCK (never
        #     assume ownership without persisted linkage)
        if orphan_tagged:
            results["__orphan__"] = ReconciliationResult(
                basket_id="__orphan__",
                classification=ReconciliationClass.ORPHAN_POSITION,
                broker_legs=len(orphan_tagged),
                expected_legs=3,
                action="BLOCK",
                blocked=True,
                detail="TB-magic broker position(s) with no basket linkage in "
                       "the durable ledger — do not assume ownership; surface "
                       "for human review",
            )

        # 3. foreign-magic positions: report as off-limits, NEVER block the
        #    TB engine, NEVER alter.
        for p in unknown:
            key = f"UNKNOWN:{p.ticket}"
            results[key] = ReconciliationResult(
                basket_id=key,
                classification=ReconciliationClass.UNKNOWN_POSITION,
                local_state=BasketLifecycleState.NO_BASKET.value,
                broker_legs=1,
                expected_legs=0,
                action="NONE",
                blocked=False,  # off-limits but not the TB engine's problem
                detail=f"Position ticket={p.ticket} symbol={p.symbol} magic={p.magic} "
                       "(foreign magic) — never altered",
            )

        blocked = [r for r in results.values() if r.blocked]
        self.ledger.append_event(
            EventType.RECONCILIATION_COMPLETED,
            source="reconciler", reason=run_id,
            payload={
                "run_id": run_id,
                "baskets_reconciled": len(local),
                "broker_positions": len(positions),
                "foreign_positions": len(unknown),
                "orphan_tagged": len(orphan_tagged),
                "blocked": len(blocked),
                "summary": {k: v.to_dict() for k, v in results.items()},
            },
        )
        return results

    # ── per-basket decision ──────────────────────────────────────────────
    def _reconcile_basket(self, bid: str, lrec: dict,
                          broker_legs: List[BrokerPosition],
                          ) -> ReconciliationResult:
        local_state = lrec["state"]
        n_broker = len(broker_legs)
        expected = 3
        symbols_broker = sorted({p.symbol.split(".")[0] for p in broker_legs})
        symbols_expected = sorted(self.expected_leg_symbols)

        def res(cls, action, detail, blocked=False, recovered=""):
            return ReconciliationResult(
                basket_id=bid, classification=cls, local_state=local_state,
                broker_legs=n_broker, expected_legs=expected,
                action=action, blocked=blocked, detail=detail,
                recovered_state=recovered,
            )

        # A. healthy flat/flat
        if local_state == BasketLifecycleState.NO_BASKET.value and n_broker == 0:
            return res(ReconciliationClass.MATCHED, "NONE", "flat/flat healthy",
                       blocked=False, recovered="NO_BASKET")

        # G. local says CLOSED/FLAT but broker still has legs -> BLOCK
        #    (checked BEFORE partial-match: a closed local basket with broker
        #     legs is a serious divergence, never a plain partial fill)
        if (local_state in (BasketLifecycleState.CLOSED_VERIFIED.value,
                            BasketLifecycleState.FLAT_VERIFIED.value)
                and n_broker > 0):
            return res(
                ReconciliationClass.BROKER_ONLY, "BLOCK",
                f"local says {local_state} but broker has {n_broker} leg(s) — "
                "BLOCK + reconciliation/flatten path (never silent)",
                blocked=True,
                recovered=BasketLifecycleState.RECONCILIATION_REQUIRED.value,
            )

        # B. local OPEN + exact expected 3 legs -> restore OPEN_VERIFIED
        if (local_state in (BasketLifecycleState.OPEN_VERIFIED.value,
                            BasketLifecycleState.ENTRY_SUBMITTING.value)
                and n_broker == expected
                and symbols_broker == symbols_expected):
            return res(ReconciliationClass.MATCHED, "RECONCILE",
                       "exact 3-leg match; restore OPEN_VERIFIED",
                       blocked=False, recovered=BasketLifecycleState.OPEN_VERIFIED.value)

        # D. local ENTRY_SUBMITTING + 3 fills -> OPEN_VERIFIED (crash before
        #    open verification)
        if (local_state == BasketLifecycleState.ENTRY_SUBMITTING.value
                and n_broker == expected):
            return res(ReconciliationClass.MATCHED, "RECONCILE",
                       "entry submitting but all 3 legs present -> OPEN_VERIFIED",
                       blocked=False, recovered=BasketLifecycleState.OPEN_VERIFIED.value)

        # C/E. partial (1-2 legs) -> BROKEN_HEDGE / blocked
        if 0 < n_broker < expected:
            return res(
                ReconciliationClass.PARTIAL_MATCH, "BLOCK",
                f"partial triangle {n_broker}/{expected} legs at broker — "
                "BROKEN_HEDGE, reconciliation required before any action",
                blocked=True,
                recovered=BasketLifecycleState.BROKEN_HEDGE.value,
            )

        # F. local closing/closed + broker flat -> CLOSED_VERIFIED
        if (local_state in (BasketLifecycleState.CLOSE_SUBMITTING.value,
                            BasketLifecycleState.PARTIALLY_CLOSED.value,
                            BasketLifecycleState.CLOSE_REQUESTED.value)
                and n_broker == 0):
            return res(ReconciliationClass.MATCHED, "RECONCILE",
                       "broker flat; close completed -> CLOSED_VERIFIED",
                       blocked=False,
                       recovered=BasketLifecycleState.CLOSED_VERIFIED.value)

        if local_state == BasketLifecycleState.CLOSED_VERIFIED.value and n_broker == 0:
            return res(ReconciliationClass.MATCHED, "NONE",
                       "closed/flat consistent",
                       blocked=False, recovered=BasketLifecycleState.CLOSED_VERIFIED.value)

        # local intent / entry never reached broker -> LOCAL_ONLY (crash
        # before/at submit, or zero fills); no broker action, mark flat
        if (local_state in (BasketLifecycleState.SIGNAL_DETECTED.value,
                            BasketLifecycleState.INTENT_CREATED.value,
                            BasketLifecycleState.ENTRY_SUBMITTING.value)
                and n_broker == 0):
            return res(
                ReconciliationClass.LOCAL_ONLY, "RECONCILE",
                "local intent never reached broker (crash before submit or "
                "zero fills) — mark FLAT_VERIFIED, no broker action",
                blocked=False,
                recovered=BasketLifecycleState.FLAT_VERIFIED.value,
            )

        # manual intervention / any other divergence -> BLOCK
        return res(
            ReconciliationClass.BROKER_ONLY, "BLOCK",
            f"unresolved divergence local={local_state} broker_legs={n_broker} "
            "— RECONCILIATION_REQUIRED / BLOCKED_UNKNOWN_STATE",
            blocked=True,
            recovered=BasketLifecycleState.RECONCILIATION_REQUIRED.value,
        )

    # ── manual intervention audit ────────────────────────────────────────
    def detect_manual_intervention(self) -> List[dict]:
        """Detect human/unknown changes to TB legs.

        Signals: broker position exists for a basket with a ticket NOT in the
        ledger, or a recorded leg's ticket vanished while local state is OPEN.
        Returns list of {basket_id, finding} records.
        """
        findings: List[dict] = []
        local = self.ledger.reconstruct_all()
        positions = [p for p in self.broker.positions() if self.is_tb_owned(p)]

        broker_tickets = {p.ticket for p in positions}
        for bid, lrec in local.items():
            if lrec["state"] not in (BasketLifecycleState.OPEN_VERIFIED.value,
                                     BasketLifecycleState.ENTRY_SUBMITTING.value):
                continue
            recorded_tickets = {
                int(e.payload.get("position_ticket", 0) or 0)
                for e in self.ledger.events_for(basket_id=bid,
                                                event_type=EventType.LEG_FILL_CONFIRMED.value)
            }
            missing = recorded_tickets - broker_tickets
            if missing:
                findings.append({
                    "basket_id": bid,
                    "finding": "MANUAL_INTERVENTION_DETECTED",
                    "missing_tickets": sorted(missing),
                    "local_state": lrec["state"],
                })
        return findings
