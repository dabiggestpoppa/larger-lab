"""QL-EXEC-R4 — generic multi-leg execution orchestration (above BrokerSession).

A basket/pair/hedge strategy submits several legs whose combined exposure is
the intended unit. R3's GenericRuntime proves a SINGLE-leg lifecycle; this
module introduces the strategy-agnostic multi-leg primitive required to express
the TB three-leg basket faithfully:

- ``MultiLegExecutionPlan`` — parent plan id + ordered legs + per-leg intent
  ids + completion/rollback policy. No TB symbols, no TB strategy math.
- ``BasketOrchestrator`` — write-ahead plan persistence, sequential leg
  submission, broker-truth fill verification, broken-hedge flatten recovery,
  basket-level close, and restart reconstruction.

Durability reuses the R3 ``RuntimeStore`` (append-only journal + execution
intents + owned positions). The write-ahead discipline is identical to R3:
every leg intent is committed BEFORE the first broker call; no broker call is
made inside a SQLite write transaction. Crash windows are recovered by
reconciliation on restart, never by blind resubmission.

Ownership is explicit: every leg maps to a deterministic logical ownership id;
the broker tag (magic + comment) is a lookup key only. Foreign positions (any
tag/magic not belonging to this plan) are NEVER submitted against, closed, or
claimed.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

from ..enums import (
    BrokerErrorCategory,
    FillPolicy,
    OrderSide,
    OrderType,
    QuantityUnit,
)
from ..ownership import LogicalOwnershipId
from ..types import (
    OrderIntent,
    stable_hash,
)
from ..runtime.intent import (
    ExecutionIntent,
    IntentState,
    PositionState,
)
from ..runtime.store import RuntimeStore


class SimulatedBasketCrash(RuntimeError):
    """Raised at an injected crash boundary to emulate process death."""


class BasketPlanState(str, Enum):
    """Durable multi-leg plan lifecycle (smallest useful taxonomy)."""

    CREATED = "CREATED"
    PRECHECKED = "PRECHECKED"
    SUBMITTING = "SUBMITTING"
    OPEN = "OPEN"
    BROKEN_HEDGE = "BROKEN_HEDGE"
    FLATTENING = "FLATTENING"
    ABORTED_FLAT = "ABORTED_FLAT"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"


@dataclass(frozen=True)
class LegPlan:
    """One leg of a multi-leg plan (broker-neutral economic leg)."""

    leg_id: str
    instrument: str          # canonical symbol
    broker_symbol: str
    side: str                # BUY / SELL
    quantity: float          # broker-native lots at the session boundary
    notional: float | None = None
    model_weight: float = 0.0
    reference_price: float | None = None
    ownership_tag: str = ""
    broker_magic: int = 0

    def to_dict(self) -> dict:
        return {
            "leg_id": self.leg_id,
            "instrument": self.instrument,
            "broker_symbol": self.broker_symbol,
            "side": self.side,
            "quantity": self.quantity,
            "notional": self.notional,
            "model_weight": self.model_weight,
            "reference_price": self.reference_price,
            "ownership_tag": self.ownership_tag,
            "broker_magic": self.broker_magic,
        }


@dataclass(frozen=True)
class MultiLegExecutionPlan:
    """A parent plan with ordered legs (strategy-agnostic; no TB symbols)."""

    plan_id: str
    strategy_id: str
    runtime_id: str
    account_id: str
    deployment_generation: str
    legs: tuple[LegPlan, ...]
    direction: str = ""
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "strategy_id": self.strategy_id,
            "runtime_id": self.runtime_id,
            "account_id": self.account_id,
            "deployment_generation": self.deployment_generation,
            "direction": self.direction,
            "legs": [leg.to_dict() for leg in self.legs],
            "metadata": self.metadata,
        }


@dataclass
class LegOutcome:
    leg_id: str
    broker_symbol: str
    side: str
    requested: float
    filled: float
    status: str            # pending / filled / flattened / failed / partial
    position_id: str = ""
    ownership_tag: str = ""

    def to_dict(self) -> dict:
        return {
            "leg_id": self.leg_id,
            "broker_symbol": self.broker_symbol,
            "side": self.side,
            "requested": self.requested,
            "filled": self.filled,
            "status": self.status,
            "position_id": self.position_id,
            "ownership_tag": self.ownership_tag,
        }


@dataclass
class BasketResult:
    plan_id: str
    state: BasketPlanState
    legs: list[LegOutcome] = field(default_factory=list)
    error_message: str = ""
    order_send_count: int = 0
    trace: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "state": self.state.value,
            "legs": [l.to_dict() for l in self.legs],
            "error_message": self.error_message,
            "order_send_count": self.order_send_count,
            "trace": list(self.trace),
        }


def leg_intent_id(plan_id: str, leg_id: str, broker_symbol: str, side: str, quantity: float) -> str:
    """Deterministic per-leg intent id (immutable execution-semantic inputs)."""
    return stable_hash("LEG", plan_id, leg_id, broker_symbol, side, str(quantity), n=24)


def basket_ownership_tag(plan_id: str, canonical_symbol: str, leg_id: str) -> str:
    """Compact broker comment linking a leg to its parent plan.

    Equivalent to the proven TB comment scheme (``TB|<basket>|<symbol>|<leg>``);
    it is a lookup key, never the sole ownership authority.
    """
    return f"TB|{plan_id}|{canonical_symbol}|{leg_id}"


class BasketOrchestrator:
    """Multi-leg write-ahead execution above a ``BrokerSession``.

    It is strategy-agnostic (no TB symbols); the caller supplies the plan. It
    owns multi-leg atomicity concerns (write-ahead, fill verification, broken
    hedge flatten, close, restart reconstruction) which R3's single-leg engine
    deliberately does not.
    """

    def __init__(
        self,
        broker,
        store: RuntimeStore,
        *,
        magic: int,
        clock: Optional[Callable[[], str]] = None,
        crash_point: Optional[str] = None,
    ) -> None:
        self._broker = broker
        self._store = store
        self._magic = magic
        self._clock = clock
        self._crash_point = crash_point

    # ── write-ahead persistence ─────────────────────────────────────────

    def _persist_plan(self, plan: MultiLegExecutionPlan) -> None:
        self._store.append_event(
            "BASKET_PLAN_CREATED",
            dedup_key=f"plan:{plan.plan_id}",
            payload=plan.to_dict(),
        )

    def _persist_leg_intent(self, plan: MultiLegExecutionPlan, leg: LegPlan) -> ExecutionIntent:
        intent_id = leg_intent_id(
            plan.plan_id, leg.leg_id, leg.broker_symbol, leg.side, leg.quantity
        )
        logical = LogicalOwnershipId(
            account_id=plan.account_id,
            runtime_id=plan.runtime_id,
            strategy_id=plan.strategy_id,
            deployment_generation=plan.deployment_generation,
            intent_id=intent_id,
        )
        tag = leg.ownership_tag or basket_ownership_tag(
            plan.plan_id, leg.instrument, leg.leg_id
        )
        intent = ExecutionIntent(
            intent_id=intent_id,
            runtime_id=plan.runtime_id,
            account_id=plan.account_id,
            strategy_id=plan.strategy_id,
            deployment_generation=plan.deployment_generation,
            event_id=plan.plan_id,
            economic_target_id=stable_hash("TGT", plan.plan_id, leg.leg_id, n=24),
            instrument=leg.instrument,
            broker_symbol=leg.broker_symbol,
            side=leg.side,
            broker_quantity=leg.quantity,
            logical_ownership_id=logical.id(),
            ownership_tag=tag,
            broker_magic=leg.broker_magic or self._magic,
        )
        self._store.create_intent(intent)
        return intent

    def _order_intent(self, plan: MultiLegExecutionPlan, leg: LegPlan) -> OrderIntent:
        side = OrderSide(leg.side) if leg.side in ("BUY", "SELL") else OrderSide.BUY
        intent_id = leg_intent_id(
            plan.plan_id, leg.leg_id, leg.broker_symbol, leg.side, leg.quantity
        )
        return OrderIntent(
            intent_id=intent_id,
            account_id=plan.account_id,
            symbol=leg.broker_symbol,
            side=side,
            volume=leg.quantity,
            quantity_unit=QuantityUnit.LOT,
            order_type=OrderType.MARKET,
            reference_price=leg.reference_price,
            fill_policy=FillPolicy.BROKER_DEFAULT,
            broker_magic=leg.broker_magic or self._magic,
            ownership_tag=leg.ownership_tag or basket_ownership_tag(
                plan.plan_id, leg.instrument, leg.leg_id
            ),
        )

    # ── plan open (write-ahead -> precheck -> submit -> verify) ─────────

    def open_plan(self, plan: MultiLegExecutionPlan) -> BasketResult:
        # Idempotency: a plan id that was already durably persisted is a replay;
        # never submit a second exposure for the same logical basket event.
        if plan.plan_id in self._store.distinct_plan_ids():
            return BasketResult(
                plan_id=plan.plan_id,
                state=BasketPlanState.CREATED,
                error_message="duplicate plan (idempotent no-op)",
                trace=["DUPLICATE_PLAN_NOOP"],
            )
        result = BasketResult(plan_id=plan.plan_id, state=BasketPlanState.CREATED)
        result.trace.append("BASKET_INTENT_WRITTEN")

        # 1. WRITE-AHEAD: commit plan + every leg intent BEFORE any broker call.
        self._persist_plan(plan)
        intents: dict[str, ExecutionIntent] = {}
        for leg in plan.legs:
            intents[leg.leg_id] = self._persist_leg_intent(plan, leg)
        result.state = BasketPlanState.CREATED
        self._maybe_crash("AFTER_PLAN_COMMIT")

        # 2. order_check ALL legs (no sends yet).
        result.state = BasketPlanState.PRECHECKED
        for leg in plan.legs:
            chk = self._broker.order_check(self._order_intent(plan, leg))
            result.trace.append("LEG_CHECK")
            if not chk.ok:
                result.state = BasketPlanState.RECONCILIATION_REQUIRED
                result.error_message = f"precheck failed {leg.leg_id}: {chk.reason}"
                for leg_id, intent in intents.items():
                    self._store.update_intent(
                        intent.intent_id, state=IntentState.INTENT_ABORTED.value,
                        reason=result.error_message,
                    )
                return result

        # 3. submit legs sequentially (broker call per leg, outside any DB tx).
        result.state = BasketPlanState.SUBMITTING
        outcomes: list[LegOutcome] = []
        send_index = 0
        for leg in plan.legs:
            order_intent = self._order_intent(plan, leg)
            result.trace.append("LEG_SEND")
            res = self._broker.submit_order(order_intent)
            result.order_send_count += 1
            send_index += 1
            self._maybe_crash(f"AFTER_LEG{send_index}_SEND")

            intent = intents[leg.leg_id]
            if not res.ok:
                self._store.update_intent(
                    intent.intent_id,
                    state=(
                        IntentState.INTENT_REJECTED.value
                        if res.error_category is BrokerErrorCategory.ORDER_REJECTED
                        else IntentState.INTENT_TRANSPORT_ERROR.value
                    ),
                    reason=res.reason,
                )
                outcomes.append(LegOutcome(
                    leg_id=leg.leg_id, broker_symbol=leg.broker_symbol, side=leg.side,
                    requested=leg.quantity, filled=0.0, status="failed",
                ))
                continue
            self._store.update_intent(
                intent.intent_id,
                state=IntentState.INTENT_SUBMITTED.value,
                broker_order_id=res.broker_order_id,
            )
            self._store.record_broker_order(
                res.broker_order_id, intent.intent_id, leg.broker_symbol, leg.side,
                leg.quantity, leg.quantity, "ACCEPTED", intent.ownership_tag,
            )

        self._maybe_crash("AFTER_ALL_SENDS_BEFORE_VERIFY")

        # 4. verify fills against broker truth.
        snapshot = self._broker.reconcile_snapshot()
        for leg in plan.legs:
            intent = intents[leg.leg_id]
            tag = leg.ownership_tag or basket_ownership_tag(
                plan.plan_id, leg.instrument, leg.leg_id
            )
            pos = next(
                (p for p in snapshot.positions if p.ownership_tag == tag), None
            )
            if pos is None:
                outcomes.append(LegOutcome(
                    leg_id=leg.leg_id, broker_symbol=leg.broker_symbol, side=leg.side,
                    requested=leg.quantity, filled=0.0, status="failed",
                ))
                continue
            filled = float(pos.volume)
            full = filled >= leg.quantity - 1e-9
            status = "filled" if full else "partial"
            self._store.update_intent(
                intent.intent_id,
                state=(
                    IntentState.INTENT_FILLED.value
                    if full else IntentState.INTENT_PARTIALLY_FILLED.value
                ),
                broker_position_id=pos.position_id,
                filled_quantity=filled,
                fill_price=pos.price_open,
            )
            self._store.upsert_owned_position(
                intent.logical_ownership_id,
                runtime_id=plan.runtime_id, account_id=plan.account_id,
                strategy_id=plan.strategy_id, intent_id=intent.intent_id,
                event_id=plan.plan_id, symbol=leg.broker_symbol, side=leg.side,
                requested_quantity=leg.quantity, filled_quantity=filled,
                state=(
                    PositionState.FILLED.value
                    if full else PositionState.PARTIALLY_FILLED.value
                ),
                broker_position_id=pos.position_id,
                broker_order_id=intent.broker_order_id,
                ownership_tag=tag, fill_price=pos.price_open,
            )
            outcomes.append(LegOutcome(
                leg_id=leg.leg_id, broker_symbol=leg.broker_symbol, side=leg.side,
                requested=leg.quantity, filled=filled, status=status,
                position_id=pos.position_id, ownership_tag=tag,
            ))
            result.trace.append(
                "LEG_FILL_FULL" if full else "LEG_FILL_PARTIAL"
            )

        result.legs = outcomes
        filled = sum(1 for o in outcomes if o.status == "filled")
        partial = sum(1 for o in outcomes if o.status == "partial")
        n_legs = len(plan.legs)

        # 5. outcome.
        if filled == n_legs:
            result.state = BasketPlanState.OPEN
            result.trace.append("BASKET_OPEN_VERIFIED")
        elif filled > 0 or partial > 0:
            result.state = BasketPlanState.BROKEN_HEDGE
            result.trace.append("BROKEN_HEDGE_DETECTED")
            result.error_message = f"partial fill {filled + partial}/{n_legs}"
            self._flatten_owned(plan, intents, result)
        else:
            result.state = BasketPlanState.ABORTED_FLAT
            result.trace.append("BASKET_ABORTED_FLAT")
        return result

    # ── broken hedge flatten (risk reduction) ────────────────────────────

    def _flatten_owned(
        self, plan: MultiLegExecutionPlan, intents: dict, result: BasketResult
    ) -> None:
        result.state = BasketPlanState.FLATTENING
        snapshot = self._broker.reconcile_snapshot()
        known = {i.ownership_tag for i in intents.values()}
        for pos in snapshot.positions:
            if pos.ownership_tag in known:
                self._broker.close_position(pos.position_id, reason="broken hedge flatten")
                result.trace.append("LEG_FLATTEN")
        # Verify flat.
        after = self._broker.reconcile_snapshot()
        remaining = [p for p in after.positions if p.ownership_tag in known]
        if not remaining:
            result.state = BasketPlanState.ABORTED_FLAT
            result.trace.append("BASKET_ABORTED_FLAT")
            for leg_id, intent in intents.items():
                self._store.update_intent(
                    intent.intent_id, state=IntentState.INTENT_ABORTED.value,
                    reason="broken hedge flattened",
                )
        else:
            result.state = BasketPlanState.RECONCILIATION_REQUIRED
            result.error_message = "broken hedge flatten incomplete"

    # ── basket close ─────────────────────────────────────────────────────

    def close_plan(self, plan_id: str) -> BasketResult:
        result = BasketResult(plan_id=plan_id, state=BasketPlanState.CLOSING)
        self._store.append_event(
            "EXIT_REQUESTED",
            dedup_key=f"exit-plan:{plan_id}",
            payload={"plan_id": plan_id},
        )
        owned = [p for p in self._store.owned_positions()
                 if p.event_id == plan_id
                 and p.state in (PositionState.FILLED.value,
                                 PositionState.PARTIALLY_FILLED.value)]
        for pos in owned:
            self._store.upsert_owned_position(
                pos.logical_ownership_id,
                runtime_id=pos.runtime_id, account_id=pos.account_id,
                strategy_id=pos.strategy_id, intent_id=pos.intent_id,
                event_id=pos.event_id, symbol=pos.symbol, side=pos.side,
                requested_quantity=pos.requested_quantity,
                filled_quantity=pos.filled_quantity,
                state=PositionState.CLOSE_PENDING.value,
                broker_position_id=pos.broker_position_id,
                broker_order_id=pos.broker_order_id,
                ownership_tag=pos.ownership_tag, fill_price=pos.fill_price,
            )
            result.trace.append("LEG_CLOSE")
            res = self._broker.close_position(pos.broker_position_id, reason="strategy exit")
            result.order_send_count += 1
            if res.ok:
                self._store.update_intent(pos.intent_id, state=IntentState.INTENT_CLOSED.value)
                self._store.upsert_owned_position(
                    pos.logical_ownership_id,
                    runtime_id=pos.runtime_id, account_id=pos.account_id,
                    strategy_id=pos.strategy_id, intent_id=pos.intent_id,
                    event_id=pos.event_id, symbol=pos.symbol, side=pos.side,
                    requested_quantity=pos.requested_quantity,
                    filled_quantity=pos.filled_quantity,
                    state=PositionState.CLOSED.value,
                    broker_position_id=pos.broker_position_id,
                    broker_order_id=pos.broker_order_id,
                    ownership_tag=pos.ownership_tag, fill_price=pos.fill_price,
                )
            else:
                result.state = BasketPlanState.RECONCILIATION_REQUIRED
                result.error_message = f"close failed for {pos.broker_symbol}"

        # Verify flat against broker truth before declaring CLOSED.
        snapshot = self._broker.reconcile_snapshot()
        known = {p.ownership_tag for p in self._store.owned_positions()}
        remaining = [p for p in snapshot.positions if p.ownership_tag in known]
        if not remaining and result.state is not BasketPlanState.RECONCILIATION_REQUIRED:
            result.state = BasketPlanState.CLOSED
            result.trace.append("BASKET_CLOSED_VERIFIED")
        elif remaining:
            result.state = BasketPlanState.RECONCILIATION_REQUIRED
            result.error_message = "owned legs remain after close"
        return result

    # ── restart reconstruction (no blind resubmission) ───────────────────

    def recover(self) -> BasketResult:
        """Reconstruct plan truth from broker + durable ledger on restart.

        Never opens a NEW basket and never duplicates exposure:
        - all legs present at broker  -> OPEN (adopt + reconstruct ledger)
        - some legs present           -> BROKEN_HEDGE -> flatten owned
        - no legs, plan had intents   -> ABORTED_FLAT (do NOT resubmit blindly)
        """
        intents = self._store.intents()
        owned_positions = self._store.owned_positions()
        known_tags = {p.ownership_tag for p in owned_positions if p.ownership_tag}
        known_tags |= {i.ownership_tag for i in intents if i.ownership_tag}
        intent_by_tag = {i.ownership_tag: i for i in intents if i.ownership_tag}
        plans = self._store.distinct_plan_ids()
        snapshot = self._broker.reconcile_snapshot()
        ours = [p for p in snapshot.positions if p.ownership_tag in known_tags]

        result = BasketResult(plan_id="recover", state=BasketPlanState.CLOSED)
        result.trace.append("RECONCILE")
        if not plans and not ours:
            result.state = BasketPlanState.ABORTED_FLAT
            result.trace.append("FLAT_MATCH")
            return result
        if not ours:
            result.state = BasketPlanState.ABORTED_FLAT
            result.trace.append("INTENT_NO_EXPOSURE")
            return result

        total_legs = len(known_tags)
        if len(ours) == total_legs:
            # Adopt: reconstruct owned positions from broker truth (no new orders).
            for pos in ours:
                intent = intent_by_tag.get(pos.ownership_tag)
                if intent is None:
                    continue
                row = self._store.intent_row(intent.intent_id)
                if row is None:
                    continue
                full = float(pos.volume) >= float(row["broker_quantity"] or 0.0) - 1e-9
                istate = IntentState.INTENT_FILLED.value if full else IntentState.INTENT_PARTIALLY_FILLED.value
                pstate = PositionState.FILLED.value if full else PositionState.PARTIALLY_FILLED.value
                self._store.update_intent(
                    intent.intent_id, state=istate, broker_position_id=pos.position_id,
                    broker_order_id=row["broker_order_id"], filled_quantity=float(pos.volume),
                    fill_price=pos.price_open,
                )
                self._store.upsert_owned_position(
                    row["logical_ownership_id"],
                    runtime_id=row["runtime_id"], account_id=row["account_id"],
                    strategy_id=row["strategy_id"], intent_id=row["intent_id"],
                    event_id=row["event_id"], symbol=row["broker_symbol"], side=row["side"],
                    requested_quantity=float(row["broker_quantity"] or 0.0),
                    filled_quantity=float(pos.volume), state=pstate,
                    broker_position_id=pos.position_id,
                    broker_order_id=row["broker_order_id"],
                    ownership_tag=pos.ownership_tag, fill_price=pos.price_open,
                )
            result.state = BasketPlanState.OPEN
            result.trace.append("BASKET_OPEN_VERIFIED")
        else:
            # Partial basket after crash -> reduce risk (flatten owned).
            result.state = BasketPlanState.BROKEN_HEDGE
            result.trace.append("BROKEN_HEDGE_DETECTED")
            for pos in ours:
                self._broker.close_position(pos.position_id, reason="recover flatten")
                result.trace.append("LEG_FLATTEN")
            result.state = BasketPlanState.ABORTED_FLAT
            result.trace.append("BASKET_ABORTED_FLAT")
        return result

    def _maybe_crash(self, point: str) -> None:
        if self._crash_point == point:
            raise SimulatedBasketCrash(f"simulated basket crash at {point}")
