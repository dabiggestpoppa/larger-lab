"""QL-EXEC-R4 — TB parity adapters (reuse canonical TB science, never rewrite).

These adapters translate the proven TB Forward strategy and execution
translation into the generic runtime contracts established in R1-R3:

- ``TBStrategyAdapter`` wraps the canonical ``TriangularBasisLiveEngine``
  (sealed P5/P6/P7 science: basis, rolling-z, direction, entry/exit
  eligibility, TB-B exact-neutral weights) behind the broker-neutral
  ``StrategyAdapter`` protocol. It does NOT reimplement any formula; it
  delegates every decision to the canonical engine object.
- ``TBTranslationAdapter`` reuses ``model_weight_to_notional`` +
  ``notional_to_mt5_lots`` from the sealed execution contract to turn model
  weights into a three-leg ``EconomicTarget`` (economic exposure, not broker
  order syntax).
- ``TBCapitalPolicyAdapter`` is a TRANSPARENT admission adapter: TB has no
  Capital Routing H1 / 70-30 / pos_t / 1R heat policy. It preserves the
  reference execution authority (primary shadow / control executable is
  enforced at the harness boundary, not invented here).

TB strategy science is FROZEN. This module imports the canonical engine at the
frozen authority SHA recorded in the R4 source manifest and never mutates it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

# Canonical TB modules live in quant-lab/engines. Mirror their own path setup
# so we share the SAME module objects (no duplicate import of the science).
_QL = Path(__file__).resolve().parents[2]  # quant-lab/
for _p in (_QL, _QL / "engines", _QL / "tb_live"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from engines.triangular_basis_live import (  # noqa: E402
    TriangularBasisLiveEngine,
    BasketDecision,
    BasketIntent,
)
from engines.tb_forward_config import (  # noqa: E402
    StrategyModelConfig,
    PRIMARY_CONFIG,
    CONTROL_CONFIG,
)
from engines.triangular_execution_contract import (  # noqa: E402
    ContractSpec,
    model_weight_to_notional,
    notional_to_mt5_lots,
)
from engines.triangular_basis_engine import Direction  # noqa: E402
from execution_runtime.enums import CapitalDecisionKind  # noqa: E402
from execution_runtime.types import (  # noqa: E402
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

# Frozen TB-B exact-neutral conversion rates (account currency USD), shared
# with the canonical execution contract / full_engine harness.
CUR_TO_USD = {"GBP": 1.34852, "AUD": 0.70583, "NZD": 0.58844}

EVENT_KIND_ENTRY = "ENTRY"
EVENT_KIND_EXIT = "EXIT"
EVENT_KIND_NOOP = "NOOP"


def _tb_event_id(strategy_id: str, decision: str, basket_id: str) -> str:
    return stable_hash("TB", strategy_id, decision, basket_id, n=24)


class TBStrategyAdapter:
    """Broker-neutral adapter over the canonical TriangularBasisLiveEngine.

    One adapter wraps ONE canonical engine (primary or control). Strategy
    decisions (basis / z / direction / entry / exit / weights) are delegated to
    the wrapped engine; the adapter only converts its ``BasketIntent`` output
    into ``StrategyEvent`` objects and persists/restores rolling state.
    """

    def __init__(
        self,
        model_config: StrategyModelConfig = CONTROL_CONFIG,
        *,
        shadow_only: Optional[bool] = None,
    ) -> None:
        self.model_config = model_config
        self.strategy_id = model_config.strategy_id
        # Authoritative TB authority: PRIMARY (TB-FWD-V1) is SHADOW ONLY;
        # CONTROL (TB-FROZEN-CONTROL) is the executable canary path. This is
        # frozen from the live worker, not from the model_config shadow flag.
        self.shadow_only = (
            model_config.strategy_id == PRIMARY_CONFIG.strategy_id
            if shadow_only is None
            else shadow_only
        )
        self._engine = TriangularBasisLiveEngine(model_config=model_config)
        self._pending: list[StrategyEvent] = []
        self._deployment_generation = ""

    # ── StrategyAdapter protocol ─────────────────────────────────────────

    def required_market_data(self) -> tuple[str, ...]:
        return ("GBPAUD", "GBPNZD", "AUDNZD")

    def initialize(self, runtime_ctx: dict) -> None:
        self._deployment_generation = str(
            runtime_ctx.get("deployment_generation", "")
        )

    def warm(self, historical: object) -> None:
        # ``historical`` is a list of canonical TriangularBar objects (replay
        # warm buffer). The canonical engine owns the rolling window rebuild.
        if historical is not None:
            self._engine.load_historical_bars(list(historical))

    def on_market_snapshot(self, snapshot: object) -> None:
        intent: BasketIntent = self._engine.process_snapshot(snapshot)
        if intent is None or intent.decision is BasketDecision.NO_ACTION:
            return
        if intent.decision is BasketDecision.OPEN_BASKET:
            self._pending.append(self._entry_event(intent))
        elif intent.decision is BasketDecision.CLOSE_BASKET:
            self._pending.append(self._exit_event(intent))

    def produce_events(self) -> tuple[StrategyEvent, ...]:
        out = tuple(self._pending)
        self._pending = []
        return out

    def serialize_state(self) -> str:
        return json.dumps(
            {
                "rolling": self._engine.get_rolling_state(),
                "active_baskets": {
                    k: {
                        "status": v.status,
                        "direction": v.direction.name,
                        "entry_basis": v.entry_basis,
                        "entry_zscore": v.entry_zscore,
                    }
                    for k, v in self._engine.get_active_baskets().items()
                },
            },
            sort_keys=True,
            default=str,
        )

    def restore_state(self, state: str) -> None:
        # Canonical engine state is reconstructable from the replay buffer; the
        # durable generic runtime re-warms the adapter from persisted bars.
        # Accept and validate; a corrupt payload fails closed upstream.
        data = json.loads(state)
        if not isinstance(data, dict) or "rolling" not in data:
            raise RuntimeError("TB strategy state corrupt")

    def health(self) -> dict:
        return {
            "strategy_id": self.strategy_id,
            "shadow_only": self.shadow_only,
            "rolling": self._engine.get_rolling_state(),
        }

    # ── canonical introspection (parity assertions) ──────────────────────

    @property
    def engine(self) -> TriangularBasisLiveEngine:
        return self._engine

    # ── event construction ───────────────────────────────────────────────

    def _entry_event(self, intent: BasketIntent) -> StrategyEvent:
        payload = {
            "basket_id": intent.basket_id,
            "direction": intent.direction.name,
            "basis": float(intent.basis),
            "zscore": float(intent.zscore),
            "entry_threshold": float(intent.entry_threshold),
            "strategy_id": intent.strategy_id or self.strategy_id,
            "legs": [
                {
                    "canonical_symbol": leg.canonical_symbol,
                    "broker_symbol": leg.broker_symbol,
                    "side": leg.side.name,
                    "model_weight": float(leg.model_weight),
                    "reference_weight": float(leg.reference_weight),
                    "entry_price": float(leg.entry_price),
                }
                for leg in intent.legs
            ],
            "signal_time": intent.timestamp.isoformat(),
        }
        return StrategyEvent(
            event_id=_tb_event_id(
                self.strategy_id, BasketDecision.OPEN_BASKET.value, intent.basket_id
            ),
            strategy_id=self.strategy_id,
            event_kind=EVENT_KIND_ENTRY,
            signal_time=intent.timestamp.isoformat(),
            deployment_generation=self._deployment_generation,
            payload=payload,
        )

    def _exit_event(self, intent: BasketIntent) -> StrategyEvent:
        payload = {
            "basket_id": intent.basket_id,
            "direction": intent.direction.name,
            "zscore": float(intent.zscore),
            "exit_reason": intent.exit_reason,
            "strategy_id": intent.strategy_id or self.strategy_id,
            "signal_time": intent.timestamp.isoformat(),
        }
        return StrategyEvent(
            event_id=_tb_event_id(
                self.strategy_id, BasketDecision.CLOSE_BASKET.value, intent.basket_id
            ),
            strategy_id=self.strategy_id,
            event_kind=EVENT_KIND_EXIT,
            signal_time=intent.timestamp.isoformat(),
            deployment_generation=self._deployment_generation,
            payload=payload,
        )


class TBCapitalPolicyAdapter:
    """Transparent TB admission adapter (NO Capital Routing science).

    TB has no H1 / 70-30 / pos_t / 1R heat policy; it admits based on account
    identity + quote-health gates which live at the harness/broker boundary.
    This adapter preserves reference execution authority verbatim.
    """

    policy_id = "tb-transparent-policy"

    def admit(self, request: CapitalRequest) -> CapitalDecision:
        return CapitalDecision(
            decision_id=stable_hash("CDN", request.event_id, "tb-admit", n=24),
            kind=CapitalDecisionKind.ADMITTED,
            family=request.family,
            admitted_f=1.0,
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


# broker symbol -> quote currency (for USD-consistent lot translation, parity
# with the canonical execution layer's QUOTE_CCY mapping).
QUOTE_CCY = {"GBPAUD.PRO": "AUD", "GBPNZD.PRO": "NZD", "AUDNZD.PRO": "NZD"}


def _side_sign(direction: str, canonical_symbol: str) -> str:
    """Canonical TB direction mapping (frozen, identical to _build_entry_intent).

    z > 0 -> SHORT basket: sell GBPAUD, buy GBPNZD, sell AUDNZD.
    z < 0 -> LONG basket: opposite.
    """
    if direction == "SHORT":
        return {
            "GBPAUD": "SELL",
            "GBPNZD": "BUY",
            "AUDNZD": "SELL",
        }[canonical_symbol]
    return {
        "GBPAUD": "BUY",
        "GBPNZD": "SELL",
        "AUDNZD": "BUY",
    }[canonical_symbol]


class TBTranslationAdapter:
    """Model weight -> notional -> lots, reusing the sealed execution contract.

    Produces a three-leg ``EconomicTarget`` (economic exposure). Broker order
    syntax is assembled later by the multi-leg orchestrator, never here.
    """

    translation_id = "tb-translation"

    def __init__(
        self,
        *,
        basket_notional_usd: float = 5000.0,
        contracts: Optional[dict] = None,
        cur_to_usd: Optional[dict] = None,
    ) -> None:
        self.basket_notional_usd = basket_notional_usd
        self.cur_to_usd = dict(cur_to_usd or CUR_TO_USD)
        self.contracts = contracts or {}

    def _contract_for(self, broker_symbol: str) -> ContractSpec:
        if broker_symbol in self.contracts:
            return self.contracts[broker_symbol]
        # Default generic forex contract (parity with the sealed simulator).
        # quote_to_account_rate mirrors the canonical execution layer so the
        # model-weight -> lots translation is byte-identical.
        return ContractSpec(
            contract_size=100000.0,
            volume_min=0.01,
            volume_max=100.0,
            volume_step=0.01,
            point=0.0001,
            digits=5,
            quote_to_account_rate=self.cur_to_usd.get(
                QUOTE_CCY.get(broker_symbol, ""), 1.0
            ),
        )

    def translate(
        self,
        event: StrategyEvent,
        decision: CapitalDecision,
        account_snapshot: BoundAccountSnapshot,
        strategy_context: StrategyExposureContext,
        market_reference: MarketReference | None = None,
    ) -> EconomicTarget:
        payload = event.payload or {}
        direction = str(payload.get("direction", "SHORT"))
        legs_payload = payload.get("legs") or []
        total_weight = sum(
            float(leg.get("model_weight", 0.0)) for leg in legs_payload
        ) or 1.0

        instruments: list[InstrumentTarget] = []
        for leg in legs_payload:
            canon = leg["canonical_symbol"]
            broker = leg["broker_symbol"]
            side = _side_sign(direction, canon)
            weight = float(leg.get("model_weight", 0.0))
            price = float(leg.get("entry_price", 0.0)) or 1.0
            notional = model_weight_to_notional(
                weight, self.basket_notional_usd, total_weight
            )
            contract = self._contract_for(broker)
            raw, rounded, _realized = notional_to_mt5_lots(
                notional, price, contract
            )
            instruments.append(
                InstrumentTarget(
                    instrument_id=canon,
                    broker_symbol=broker,
                    side=side,
                    target_notional=round(notional, 4),
                    target_quantity=rounded,
                    metadata={
                        "model_weight": weight,
                        "requested_lots": raw,
                        "signal_reference_price": price,
                    },
                )
            )
        return EconomicTarget(
            event_id=event.event_id,
            strategy_id=event.strategy_id,
            account_id=account_snapshot.account_id,
            instruments=tuple(instruments),
            currency=account_snapshot.account_currency,
            model_heat_reference=str(decision.admitted_f),
            translation_version=self.translation_id,
            known_time=event.signal_time,
            metadata={"basket_id": payload.get("basket_id", ""),
                      "direction": direction},
        )
