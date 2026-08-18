"""QL-EXEC-R4.2 — shadow-only enforcement layer (order-prevention barriers).

The generic TB shadow is OBSERVER ONLY. This module implements the three
in-code barriers from the frozen R4.1 plan:

1. ``ShadowRuntimeAuthority`` — immutable authority profile pinning
   ``can_submit_new_risk=False`` (SHADOW_OBSERVE_ONLY mode). This is the
   runtime authority gate.
2. ``ReadOnlyBrokerSession`` — a BrokerSession whose write surface
   (``order_check``, ``submit_order``, ``cancel_order``, ``close_position``)
   does not exist; a defensive ``__getattr__`` raises
   ``ShadowWriteForbiddenError`` for those names so a refactor cannot
   silently reintroduce a write path.
3. ``ShadowExecutionPlan`` — the hypothetical-plan type. It is deliberately
   NOT an executable ``OrderIntent``: it carries direction / weights / target
   lots for comparison but has no submit path and never flows into any broker
   call.

Barrier 4 (process capability denial: no MT5 client / no broker credentials in
the shadow process) is enforced at the process layer; the shadow consumes
exported market truth instead of attaching to MT5 (Option B).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# Immutable shadow mode constant (also part of the hashed deployment profile).
SHADOW_OBSERVE_ONLY = "SHADOW_OBSERVE_ONLY"

# Any attribute access to these names on a shadow object is a hard violation.
_WRITE_DENYLIST = (
    "order_check",
    "submit_order",
    "cancel_order",
    "close_position",
    "order_send",
    "send",
    "modify_order",
    "place_order",
)


class ShadowWriteForbiddenError(RuntimeError):
    """Raised when a shadow object is asked to perform a broker write.

    This must never be caught-and-ignored; reaching it means the shadow is one
    step from an order path and the operator must stop the shadow.
    """


@dataclass(frozen=True)
class ShadowRuntimeAuthority:
    """Immutable shadow authority profile (barrier 1).

    The shadow can observe and construct hypothetical plans; it can never
    submit new risk or close/cancel anything. The profile is frozen at
    construction and cannot be mutated.
    """

    shadow_mode: str = SHADOW_OBSERVE_ONLY
    can_submit_new_risk: bool = False
    can_close_existing: bool = False
    can_cancel: bool = False

    def __post_init__(self) -> None:
        if self.shadow_mode != SHADOW_OBSERVE_ONLY:
            raise ValueError(f"shadow_mode must be {SHADOW_OBSERVE_ONLY!r}")
        if self.can_submit_new_risk or self.can_close_existing or self.can_cancel:
            raise ValueError("shadow authority cannot enable any write capability")

    def to_dict(self) -> dict:
        return {
            "shadow_mode": self.shadow_mode,
            "can_submit_new_risk": self.can_submit_new_risk,
            "can_close_existing": self.can_close_existing,
            "can_cancel": self.can_cancel,
        }


@dataclass(frozen=True)
class ShadowLeg:
    """One hypothetical basket leg (never submittable)."""

    canonical_symbol: str
    broker_symbol: str
    side: str
    model_weight: float
    target_notional: float
    target_lots: float

    def to_dict(self) -> dict:
        return {
            "canonical_symbol": self.canonical_symbol,
            "broker_symbol": self.broker_symbol,
            "side": self.side,
            "model_weight": round(float(self.model_weight), 6),
            "target_notional": round(float(self.target_notional), 4),
            "target_lots": round(float(self.target_lots), 4),
        }


@dataclass(frozen=True)
class ShadowExecutionPlan:
    """Hypothetical execution plan (distinct from executable OrderIntent).

    Produced by the shadow when the strategy would have entered/exited. It is
    used ONLY for parity comparison and telemetry. There is deliberately no
    reference to any broker request type and no submit method.
    """

    plan_id: str                 # deterministic basket/plan id
    strategy_id: str
    runtime_id: str
    deployment_generation: str
    bar_key: str
    decision: str                # ENTRY | EXIT
    direction: str               # LONG | SHORT | NONE
    event_id: str
    basis: Optional[float] = None
    z_score: Optional[float] = None
    weights: tuple[tuple[str, float], ...] = ()
    legs: tuple[ShadowLeg, ...] = ()
    exit_reason: str = ""

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "strategy_id": self.strategy_id,
            "runtime_id": self.runtime_id,
            "deployment_generation": self.deployment_generation,
            "bar_key": self.bar_key,
            "decision": self.decision,
            "direction": self.direction,
            "event_id": self.event_id,
            "basis": self.basis,
            "z_score": self.z_score,
            "weights": dict(self.weights),
            "legs": [l.to_dict() for l in self.legs],
            "exit_reason": self.exit_reason,
        }


class ReadOnlyBrokerSession:
    """Barrier 2 — a BrokerSession with no write surface.

    Read methods delegate to an injected read-only truth provider (in G1 the
    exported market/account truth; in tests a Fake/Sim truth object). Write
    methods do NOT exist; accessing them via ``__getattr__`` raises
    ``ShadowWriteForbiddenError``.

    Counters track the invariant ``broker_write_calls == 0`` and count any
    blocked attempt (``write_attempts``) for telemetry.
    """

    def __init__(self, truth: Any, *, broker_write_calls: int = 0) -> None:
        self._truth = truth
        self.broker_write_calls = broker_write_calls
        self.write_attempts = 0

    # ── read surface (delegates to truth provider) ───────────────────────
    def connect(self) -> bool:
        fn = getattr(self._truth, "connect", None)
        return bool(fn()) if fn else True

    def disconnect(self) -> None:
        fn = getattr(self._truth, "disconnect", None)
        if fn:
            fn()

    def health(self) -> dict:
        fn = getattr(self._truth, "health", None)
        return dict(fn()) if fn else {"ok": True}

    def identity(self):
        fn = getattr(self._truth, "identity", None)
        if fn:
            return fn()
        return getattr(self._truth, "identity", None)

    def account_state(self):
        fn = getattr(self._truth, "account_state", None)
        if fn:
            return fn()
        return getattr(self._truth, "account_state", None)

    def clock_state(self):
        fn = getattr(self._truth, "clock_state", None)
        if fn:
            return fn()
        return getattr(self._truth, "clock_state", None)

    def symbol_info(self, symbol: str):
        fn = getattr(self._truth, "symbol_info", None)
        if fn:
            return fn(symbol)
        return None

    def ensure_symbol(self, symbol: str) -> bool:
        # Read-only: never mutate provider symbol state.
        return self.symbol_info(symbol) is not None

    def tick(self, symbol: str):
        fn = getattr(self._truth, "tick", None)
        if fn:
            return fn(symbol)
        return None

    def bars(self, symbol: str, timeframe: str, count: int):
        fn = getattr(self._truth, "bars", None)
        if fn:
            return fn(symbol, timeframe, count)
        return None

    def positions(self):
        fn = getattr(self._truth, "positions", None)
        return list(fn()) if fn else []

    def orders(self):
        fn = getattr(self._truth, "orders", None)
        return list(fn()) if fn else []

    def deals(self, start: float, end: float):
        fn = getattr(self._truth, "deals", None)
        return list(fn(start, end)) if fn else []

    def reconcile_snapshot(self):
        fn = getattr(self._truth, "reconcile_snapshot", None)
        if fn:
            return fn()
        return None

    # ── write surface: ABSENT + denylist guard ───────────────────────────
    def __getattr__(self, name: str):
        if name in _WRITE_DENYLIST:
            self.write_attempts += 1
            raise ShadowWriteForbiddenError(
                f"shadow broker write attempt blocked: {name} "
                f"(broker_write_calls={self.broker_write_calls})"
            )
        raise AttributeError(name)

    def write_counter_snapshot(self) -> dict:
        return {
            "broker_write_calls": self.broker_write_calls,
            "write_attempts": self.write_attempts,
        }
