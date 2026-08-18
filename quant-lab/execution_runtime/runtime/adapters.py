"""QL-EXEC-R3 — deterministic TEST/SIM adapters.

These are the deliberately-trivial alpha boundary fixtures used to prove the
generic runtime lifecycle. They contain NO real strategy science, NO Capital
Routing math (no A/B, 70/30, H1, pos_t, 1R), NO broker imports. They exist only
to drive deterministic events through the GenericRuntime.

- ``ScriptedStrategyAdapter``: replays a predeclared event script. It is
  idempotent at the adapter level (always replays the full script); the
  runtime's durable event journal + deterministic intent ids are the dedup
  authority.
- ``PassThroughCapitalPolicyAdapter``: deterministically admits (or rejects)
  configured fixture events. NOT a production policy.
- ``TestCapitalTranslationAdapter``: fixed broker-neutral target derived
  entirely from the fixture payload. SIMULATION ONLY.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from ..enums import CapitalDecisionKind, OrderSide
from ..types import (
    BoundAccountSnapshot,
    CapitalDecision,
    CapitalRequest,
    EconomicTarget,
    InstrumentTarget,
    MarketReference,
    StrategyEvent,
    StrategyExposureContext,
    stable_hash,
)

EVENT_KIND_ENTRY = "ENTRY"
EVENT_KIND_EXIT = "EXIT"
EVENT_KIND_NOOP = "NOOP"


class ScriptedStrategyAdapter:
    """Replays a predeclared event sequence (no alpha, no market math)."""

    strategy_id = "scripted-strategy"

    def __init__(self, events: tuple[StrategyEvent, ...] = ()) -> None:
        self._script = list(events)
        self._warmed = False
        self._warm_fail = False
        self._restore_fail = False

    def set_warm_failure(self, fail: bool) -> None:
        self._warm_fail = fail

    def set_restore_failure(self, fail: bool) -> None:
        self._restore_fail = fail

    def add_event(self, event: StrategyEvent) -> None:
        self._script.append(event)

    def required_market_data(self) -> tuple[str, ...]:
        return ("EURUSD",)

    def initialize(self, runtime_ctx: dict) -> None:
        pass

    def warm(self, historical: object) -> None:
        if self._warm_fail:
            raise RuntimeError("scripted strategy warm failure (injected)")
        self._warmed = True

    def on_market_snapshot(self, snapshot: object) -> None:
        pass

    def produce_events(self) -> tuple[StrategyEvent, ...]:
        # Always replay the full script; runtime dedup is the authority.
        return tuple(self._script)

    def serialize_state(self) -> str:
        return json.dumps(
            {"warmed": self._warmed, "script": [e.payload for e in self._script]},
            sort_keys=True,
            default=str,
        )

    def restore_state(self, state: str) -> None:
        if self._restore_fail:
            raise RuntimeError("scripted strategy restore failure (injected)")
        try:
            data = json.loads(state)
        except (json.JSONDecodeError, TypeError) as exc:
            raise RuntimeError("scripted strategy state corrupt") from exc
        self._warmed = bool(data.get("warmed", False))

    def health(self) -> dict:
        return {"warmed": self._warmed, "script_events": len(self._script)}


class PassThroughCapitalPolicyAdapter:
    """Deterministically admits fixture events. TEST/SIM only, no A/B math."""

    policy_id = "pass-through-test-policy"

    def __init__(self, *, reject: bool = False) -> None:
        self._reject = reject

    def admit(self, request: CapitalRequest) -> CapitalDecision:
        if self._reject:
            return CapitalDecision(
                decision_id=stable_hash("CDN", request.event_id, "reject", n=24),
                kind=CapitalDecisionKind.REJECTED,
                family=request.family,
                admitted_f=0.0,
                policy_id=self.policy_id,
                reason="fixture policy reject",
                decided_at=request.request_id,
            )
        admitted_f = request.requested_f if request.requested_f > 0 else 1.0
        return CapitalDecision(
            decision_id=stable_hash("CDN", request.event_id, "admit", n=24),
            kind=CapitalDecisionKind.ADMITTED,
            family=request.family,
            admitted_f=admitted_f,
            reservation_id=stable_hash("RSV", request.event_id, request.account_id, n=24),
            policy_id=self.policy_id,
            reason="",
            decided_at=request.request_id,
        )

    def release(self, reservation_id: str) -> None:
        pass

    def reconstruct_reservations(self) -> tuple:
        return ()

    def shared_heat_state(self) -> dict:
        return {}


@dataclass(frozen=True)
class _FixtureInstrument:
    instrument: str
    broker_symbol: str
    side: str
    target_quantity: float
    target_notional: float | None = None


class TestCapitalTranslationAdapter:
    """Fixed deterministic translator. SIMULATION ONLY, no sizing formula."""

    translation_id = "test-translation"

    def __init__(self, default_quantity: float = 0.1) -> None:
        self._default_quantity = default_quantity

    def translate(
        self,
        event: StrategyEvent,
        decision: CapitalDecision,
        account_snapshot: BoundAccountSnapshot,
        strategy_context: StrategyExposureContext,
        market_reference: MarketReference | None = None,
    ) -> EconomicTarget:
        payload = event.payload or {}
        side = str(payload.get("side", "BUY")).upper()
        if side not in ("BUY", "SELL"):
            side = "BUY"
        quantity = float(payload.get("quantity", self._default_quantity))
        symbol = str(payload.get("broker_symbol", "EURUSD"))
        instrument = str(payload.get("instrument", symbol))
        inst = InstrumentTarget(
            instrument_id=instrument,
            broker_symbol=symbol,
            side=side,
            target_quantity=quantity,
            target_notional=float(payload.get("notional", 0.0)) or None,
        )
        return EconomicTarget(
            event_id=event.event_id,
            strategy_id=event.strategy_id,
            account_id=account_snapshot.account_id,
            instruments=(inst,),
            currency=account_snapshot.account_currency,
            model_heat_reference=str(decision.admitted_f),
            translation_version=self.translation_id,
            known_time=event.signal_time,
        )


def entry_event(
    event_id: str,
    strategy_id: str = "scripted-strategy",
    *,
    deployment_generation: str = "gen-1",
    side: str = "BUY",
    quantity: float = 0.1,
    broker_symbol: str = "EURUSD",
    instrument: str = "EURUSD",
) -> StrategyEvent:
    return StrategyEvent(
        event_id=event_id,
        strategy_id=strategy_id,
        event_kind=EVENT_KIND_ENTRY,
        signal_time="2026-01-01T00:00:00Z",
        deployment_generation=deployment_generation,
        payload={
            "side": side,
            "quantity": quantity,
            "broker_symbol": broker_symbol,
            "instrument": instrument,
        },
    )


def exit_event(
    event_id: str,
    strategy_id: str = "scripted-strategy",
    *,
    deployment_generation: str = "gen-1",
) -> StrategyEvent:
    return StrategyEvent(
        event_id=event_id,
        strategy_id=strategy_id,
        event_kind=EVENT_KIND_EXIT,
        signal_time="2026-01-02T00:00:00Z",
        deployment_generation=deployment_generation,
        payload={"instrument": "EURUSD"},
    )
