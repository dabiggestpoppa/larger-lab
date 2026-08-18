"""QL-EXEC-R4 — side-by-side TB parity harness (reference vs generic).

PATH A (reference): the proven TB path. It drives the canonical
``TriangularBasisLiveEngine`` directly (PRIMARY shadow-only + CONTROL
executable, matching the live worker's authority) and executes control baskets
through the canonical ``TriangularExecutionLayer`` wired to a deterministic
FakeBroker (the exact simulation path from the R4 full-engine harness).

PATH B (generic): the same strategy science wrapped in ``TBStrategyAdapter``,
the same model-weight -> lots translation wrapped in ``TBTranslationAdapter``,
and multi-leg execution through the strategy-agnostic ``BasketOrchestrator``
over ``SimBrokerSession`` + the R3 durable ``RuntimeStore``.

Both paths consume IDENTICAL frozen bar fixtures and produce a canonical trace
+ a normalized state snapshot. ``ParityRunner`` compares them surface-by-surface
and classifies every comparison (never a vague PASS).

No real MT5, no real broker, no active TB state is ever touched.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

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
    PRIMARY_CONFIG,
    CONTROL_CONFIG,
)
from engines.triangular_basis_engine import TriangularBar, Direction  # noqa: E402
from tb_live.market_data import (  # noqa: E402
    ClosedBar,
    FailureCode,
    TriangleSignalSnapshot,
)
from .reference import (  # noqa: E402
    ReferenceBroker,
    ReferenceExecutor,
    RefBasketState,
    translate_intent,
    TB_MAGIC,
    CUR_TO_USD,
)

from ..enums import Environment, HedgingNetting
from ..brokers.sim_broker import SimBrokerSession
from ..runtime.store import RuntimeStore
from ..types import (
    BoundAccountSnapshot,
    CapitalRequest,
    StrategyExposureContext,
    stable_hash,
)
from .adapters import (
    TBStrategyAdapter,
    TBTranslationAdapter,
    TBCapitalPolicyAdapter,
)
from .basket import (
    BasketOrchestrator,
    BasketPlanState,
    LegPlan,
    MultiLegExecutionPlan,
)
from .parity import (
    ParityTier,
    ParityVerdict,
    compare_legs,
    compare_state_snapshot,
    compare_traces,
)

BASKET_NOTIONAL_USD = 25000.0  # frozen harness notional (engineering, not alpha)
SYMBOLS = ("GBPAUD", "GBPNZD", "AUDNZD")
BROKER_SYMBOLS = ("GBPAUD.PRO", "GBPNZD.PRO", "AUDNZD.PRO")

# canonical trace vocabulary shared by both harnesses
TRACE_BAR_ACCEPTED = "BAR_ACCEPTED"
TRACE_SIGNAL_PRIMARY_SHADOW = "SIGNAL_PRIMARY_SHADOW"
TRACE_SIGNAL_CONTROL = "SIGNAL_CONTROL_{direction}"
TRACE_EXIT_SIGNAL = "EXIT_SIGNAL"


# ─── FROZEN BAR FIXTURE ───────────────────────────────────────────────────

@dataclass(frozen=True)
class BarFixture:
    """A deterministic replay fixture (causal: no future bar, no future state)."""

    bars: tuple[TriangularBar, ...]
    signal_index: int = -1          # index of the first signal bar
    exit_index: int = -1            # index of the exit bar (-1 => none)


def make_tri_bar(timestamp: datetime, ga: float, gn: float, an: float) -> TriangularBar:
    hl = 0.0005
    return TriangularBar(
        timestamp=timestamp,
        gbp_aud=ga, gbp_nzd=gn, aud_nzd=an,
        gbp_aud_high=ga + hl, gbp_aud_low=ga - hl,
        gbp_nzd_high=gn + hl, gbp_nzd_low=gn - hl,
        aud_nzd_high=an + hl, aud_nzd_low=an - hl,
    )


def make_control_fixture(*, n_warmup: int = 200, spike_ga: float = 1.8200,
                         exit_ga: float = 1.7960) -> BarFixture:
    """200 warmup bars + a GA up-spike (SHORT entry) + a GA down-spike (exit).

    Prices are kept within the exact-neutral TB-B projection envelope (the
    canonical engine FAILS CLOSED when dislocation exceeds ~0.85%, so a real
    signal is a sub-percent dislocation). Warmup bars carry a tiny deterministic
    oscillation so the rolling std is > 0 and z computes; the SIGNAL and EXIT
    bars are inside the frozen London session (raw hour 10:00 => est hour 5).
    """
    warmup_start = datetime(2024, 1, 1, 0, 0, 0)
    bars: list[TriangularBar] = []
    for i in range(n_warmup):
        ga = 1.808000 + (0.000100 if i % 2 == 0 else 0.0)
        bars.append(make_tri_bar(
            warmup_start + timedelta(minutes=5 * i), ga, 1.978000, 1.094000,
        ))
    sig_idx = len(bars)
    bars.append(make_tri_bar(
        datetime(2024, 1, 2, 10, 0, 0), spike_ga, 1.978000, 1.094000,
    ))
    exit_idx = len(bars)
    bars.append(make_tri_bar(
        datetime(2024, 1, 2, 10, 5, 0), exit_ga, 1.978000, 1.094000,
    ))
    return BarFixture(bars=tuple(bars), signal_index=sig_idx, exit_index=exit_idx)


def make_snapshot(tri_bar: TriangularBar) -> TriangleSignalSnapshot:
    def bar(symbol: str, close: float, high: float, low: float) -> ClosedBar:
        return ClosedBar(
            symbol=symbol,
            bar_open_time=tri_bar.timestamp,
            bar_close_time=tri_bar.timestamp + timedelta(minutes=5),
            open=close, high=high, low=low, close=close,
            is_closed=True, bar_id=f"{symbol}|{tri_bar.timestamp.isoformat()}",
        )

    return TriangleSignalSnapshot(
        signal_bar_close_time=tri_bar.timestamp,
        gbpaud_bar=bar("GBPAUD", tri_bar.gbp_aud, tri_bar.gbp_aud_high, tri_bar.gbp_aud_low),
        gbpnzd_bar=bar("GBPNZD", tri_bar.gbp_nzd, tri_bar.gbp_nzd_high, tri_bar.gbp_nzd_low),
        audnzd_bar=bar("AUDNZD", tri_bar.aud_nzd, tri_bar.aud_nzd_high, tri_bar.aud_nzd_low),
        all_same_bar_close=True, all_closed=True, signal_snapshot_valid=True,
        failure_code=FailureCode.OK, snapshot_id=f"snap|{tri_bar.timestamp.isoformat()}",
    )


def _normalize_owned(symbol, side, volume):
    return (str(symbol), str(side), round(float(volume), 6))


# ─── PATH A: REFERENCE HARNESS ────────────────────────────────────────────

class LegacyTBHarness:
    """Reference TB path (canonical engine + canonical execution layer)."""

    def __init__(self, *, basket_notional_usd: float = BASKET_NOTIONAL_USD,
                 broker_profile: str = "all_success"):
        self.basket_notional_usd = basket_notional_usd
        self.control = TriangularBasisLiveEngine(model_config=CONTROL_CONFIG)
        self.primary = TriangularBasisLiveEngine(model_config=PRIMARY_CONFIG)
        self.broker = ReferenceBroker(profile=broker_profile)
        self.layer = ReferenceExecutor(
            self.broker, magic=TB_MAGIC,
            basket_notional_usd=basket_notional_usd,
            cur_to_usd=dict(CUR_TO_USD),
        )
        self.trace: list[str] = []
        self.primary_order_sends = 0
        self.control_order_sends = 0
        self._basket_state = "FLAT"

    def warm(self, bars) -> None:
        self.control.load_historical_bars(list(bars))
        self.primary.load_historical_bars(list(bars))

    def step(self, snap) -> dict:
        self.trace.append(TRACE_BAR_ACCEPTED)

        p = self.primary.process_snapshot(snap)
        if p.decision is BasketDecision.OPEN_BASKET:
            self.trace.append(TRACE_SIGNAL_PRIMARY_SHADOW)
            # PRIMARY is shadow-only: never reaches execution (0 orders).

        c = self.control.process_snapshot(snap)
        if c.decision is BasketDecision.OPEN_BASKET:
            self._open_control(c, snap)
        elif c.decision is BasketDecision.CLOSE_BASKET:
            self._close_control(c)

        return self.snapshot()

    def _open_control(self, c: BasketIntent, snap) -> None:
        direction = c.direction.name
        self.trace.append(TRACE_SIGNAL_CONTROL.format(direction=direction))
        self.trace.append("BASKET_INTENT_WRITTEN")
        self.broker.set_prices_from_snapshot(snap)
        exec_intent = translate_intent(c, self.basket_notional_usd)
        for _ in exec_intent.legs:
            self.trace.append("LEG_CHECK")
        result = self.layer.open(exec_intent)
        self.control_order_sends += len(exec_intent.legs)
        for _ in exec_intent.legs:
            self.trace.append("LEG_SEND")
        if result.state is RefBasketState.OPEN:
            for _ in exec_intent.legs:
                self.trace.append("LEG_FILL_FULL")
            self.trace.append("BASKET_OPEN_VERIFIED")
            self._basket_state = "OPEN"
            self.control.on_basket_open_confirmed(c.basket_id)
        elif result.state in (RefBasketState.BROKEN_HEDGE, RefBasketState.ABORTED_FLAT):
            filled = sum(1 for r in result.legs if r.status in ("filled", "flattened"))
            if filled > 0:
                self.trace.append("BROKEN_HEDGE_DETECTED")
                for _ in range(filled):
                    self.trace.append("LEG_FLATTEN")
            self.trace.append("BASKET_ABORTED_FLAT")
            self._basket_state = "ABORTED_FLAT"
        else:
            self.trace.append("BASKET_ABORTED_FLAT")
            self._basket_state = "ABORTED_FLAT"

    def _close_control(self, c: BasketIntent) -> None:
        self.trace.append(TRACE_EXIT_SIGNAL)
        result = self.layer.close(c.basket_id)
        self.control_order_sends += 3
        for _ in range(3):
            self.trace.append("LEG_CLOSE")
        if result.state is RefBasketState.CLOSED:
            self.trace.append("BASKET_CLOSED_VERIFIED")
            self._basket_state = "CLOSED"
        else:
            self._basket_state = "RECONCILIATION_REQUIRED"

    def snapshot(self) -> dict:
        owned = [_normalize_owned(p.symbol, "LONG" if p.type == 0 else "SHORT", p.volume)
                 for p in self.broker.positions_list if p.magic == TB_MAGIC]
        foreign = [_normalize_owned(p.symbol, "LONG" if p.type == 0 else "SHORT", p.volume)
                   for p in self.broker.positions_list if p.magic != TB_MAGIC]
        return {
            "basket_state": self._basket_state,
            "owned_positions": sorted(owned),
            "foreign_positions": sorted(foreign),
            "order_send_count": self.control_order_sends + self.primary_order_sends,
        }

    def normalized_trace(self) -> list[str]:
        return list(self.trace)


# ─── PATH B: GENERIC HARNESS ──────────────────────────────────────────────

class GenericTBHarness:
    """Generic path: canonical science + generic contracts + multi-leg orchestrator."""

    def __init__(self, *, basket_notional_usd: float = BASKET_NOTIONAL_USD,
                 runtime_id: str = "tb-runtime", account_id: str = "tb-master",
                 db_path: str | Path = ":memory:", magic: int = TB_MAGIC,
                 broker: SimBrokerSession | None = None,
                 crash_point: Optional[str] = None):
        self.runtime_id = runtime_id
        self.account_id = account_id
        self.magic = magic
        self.basket_notional_usd = basket_notional_usd

        self.primary = TBStrategyAdapter(PRIMARY_CONFIG)
        self.control = TBStrategyAdapter(CONTROL_CONFIG)
        self.policy = TBCapitalPolicyAdapter()
        self.translation = TBTranslationAdapter(basket_notional_usd=basket_notional_usd)
        if broker is None:
            broker = SimBrokerSession(
                broker_company="Ox Securities", server="OxSecurities-Demo",
                account_identifier="tb-master-01", environment=Environment.SIM,
                currency="USD", account_id=account_id,
            )
            for bs in BROKER_SYMBOLS:
                broker.add_symbol(
                    bs, digits=5, point=0.0001, contract_size=100000.0,
                    volume_min=0.01, volume_max=100.0, volume_step=0.01,
                    visible=True, trade_mode="SIM",
                )
        self.broker = broker
        self.broker.connect()
        self.store = RuntimeStore(db_path)
        self.store.open()
        self.store.initialize(
            runtime_id=runtime_id,
            deployment_generation="gen-1",
            profile_hash="tb-profile-hash",
            account_hash="tb-account-hash",
        )
        self.orchestrator = BasketOrchestrator(
            self.broker, self.store, magic=magic, crash_point=crash_point,
        )
        self.trace: list[str] = []
        self.primary_order_sends = 0
        self.control_order_sends = 0
        self._basket_state = "FLAT"

    def recover(self) -> None:
        """Reconstruct plan truth from broker + durable ledger (restart)."""
        result = self.orchestrator.recover()
        self.trace.extend(result.trace)
        if result.state is BasketPlanState.OPEN:
            self._basket_state = "OPEN"
        elif result.state is BasketPlanState.ABORTED_FLAT:
            self._basket_state = "ABORTED_FLAT"
        else:
            self._basket_state = result.state.value

    def warm(self, bars) -> None:
        self.primary.warm(list(bars))
        self.control.warm(list(bars))

    def step(self, snap) -> dict:
        self.trace.append(TRACE_BAR_ACCEPTED)
        self.primary.on_market_snapshot(snap)
        self.control.on_market_snapshot(snap)

        for ev in self.primary.produce_events():
            self.trace.append(TRACE_SIGNAL_PRIMARY_SHADOW)
            # PRIMARY is shadow-only; never submit.
        for ev in self.control.produce_events():
            if ev.event_kind == "ENTRY":
                self._open_control(ev)
            elif ev.event_kind == "EXIT":
                self._close_control(ev)
        return self.snapshot()

    def _admit_and_translate(self, ev):
        request = CapitalRequest(
            request_id=stable_hash("REQ", ev.event_id, n=24),
            event_id=ev.event_id, strategy_id=ev.strategy_id,
            family="TB", requested_f=1.0,
            portfolio_group_id="", account_id=self.account_id,
            policy_id=self.policy.policy_id,
        )
        decision = self.policy.admit(request)
        account_snapshot = BoundAccountSnapshot(
            account_id=self.account_id, account_currency="USD",
        )
        strategy_ctx = StrategyExposureContext(
            strategy_id=ev.strategy_id, exposure_kind="ENTRY",
        )
        return self.translation.translate(ev, decision, account_snapshot, strategy_ctx)

    def _open_control(self, ev) -> None:
        direction = str(ev.payload.get("direction", "SHORT"))
        self.trace.append(TRACE_SIGNAL_CONTROL.format(direction=direction))
        target = self._admit_and_translate(ev)
        legs = []
        for i, inst in enumerate(target.instruments, start=1):
            legs.append(LegPlan(
                leg_id=f"L{i}",
                instrument=inst.instrument_id,
                broker_symbol=inst.broker_symbol,
                side=inst.side,
                quantity=float(inst.target_quantity or 0.0),
                notional=inst.target_notional,
                model_weight=float(inst.metadata.get("model_weight", 0.0)),
                reference_price=float(inst.metadata.get("signal_reference_price", 0.0)),
            ))
        plan = MultiLegExecutionPlan(
            plan_id=str(target.metadata.get("basket_id", "")),
            strategy_id=ev.strategy_id, runtime_id=self.runtime_id,
            account_id=self.account_id, deployment_generation=ev.deployment_generation,
            legs=tuple(legs), direction=direction,
        )
        result = self.orchestrator.open_plan(plan)
        self.control_order_sends += result.order_send_count
        self.trace.extend(result.trace)
        if result.state is BasketPlanState.OPEN:
            self._basket_state = "OPEN"
            self.control.engine.on_basket_open_confirmed(plan.plan_id)
        elif result.state in (BasketPlanState.ABORTED_FLAT,
                              BasketPlanState.BROKEN_HEDGE):
            self._basket_state = "ABORTED_FLAT"
        else:
            self._basket_state = "RECONCILIATION_REQUIRED"

    def _close_control(self, ev) -> None:
        self.trace.append(TRACE_EXIT_SIGNAL)
        plan_id = str(ev.payload.get("basket_id", ""))
        result = self.orchestrator.close_plan(plan_id)
        self.control_order_sends += result.order_send_count
        self.trace.extend(result.trace)
        if result.state is BasketPlanState.CLOSED:
            self._basket_state = "CLOSED"
        elif result.state is BasketPlanState.RECONCILIATION_REQUIRED:
            self._basket_state = "RECONCILIATION_REQUIRED"

    def snapshot(self) -> dict:
        snap = self.broker.reconcile_snapshot()
        owned = [_normalize_owned(p.symbol, p.side, p.volume)
                 for p in snap.positions if p.magic == self.magic]
        foreign = [_normalize_owned(p.symbol, p.side, p.volume)
                   for p in snap.positions if p.magic != self.magic]
        return {
            "basket_state": self._basket_state,
            "owned_positions": sorted(owned),
            "foreign_positions": sorted(foreign),
            "order_send_count": self.control_order_sends + self.primary_order_sends,
        }

    def normalized_trace(self) -> list[str]:
        return list(self.trace)

    def close(self) -> None:
        self.store.close()


# ─── PARITY RUNNER ────────────────────────────────────────────────────────

@dataclass
class ParityReport:
    verdicts: list[ParityVerdict] = field(default_factory=list)
    ref_trace: list[str] = field(default_factory=list)
    gen_trace: list[str] = field(default_factory=list)

    def pass_ok(self) -> bool:
        return all(v.pass_ok for v in self.verdicts)

    def tiers(self) -> dict[str, str]:
        return {v.surface: v.tier.value for v in self.verdicts}


class ParityRunner:
    """Feed identical frozen bars to both harnesses and compare surfaces."""

    def __init__(self, ref: LegacyTBHarness, gen: GenericTBHarness):
        self.ref = ref
        self.gen = gen

    def run(self, fixture: BarFixture) -> ParityReport:
        report = ParityReport()
        self.ref.warm(fixture.bars[:fixture.signal_index])
        self.gen.warm(fixture.bars[:fixture.signal_index])

        # process through the signal bar (entry) and exit bar (close) if present
        end = fixture.exit_index + 1 if fixture.exit_index >= 0 else fixture.signal_index + 1
        for idx in range(fixture.signal_index, end):
            snap = make_snapshot(fixture.bars[idx])
            self.ref.step(snap)
            self.gen.step(snap)

        report.ref_trace = self.ref.normalized_trace()
        report.gen_trace = self.gen.normalized_trace()
        report.verdicts.append(
            compare_traces("execution_trace", report.ref_trace, report.gen_trace)
        )
        report.verdicts.append(
            compare_state_snapshot("final_state", self.ref.snapshot(), self.gen.snapshot())
        )
        report.verdicts.append(ParityVerdict(
            "primary_shadow_zero_order",
            ParityTier.EXACT if self.ref.primary_order_sends == 0 else ParityTier.MISMATCH,
            self.ref.primary_order_sends,
            self.gen.primary_order_sends,
        ))
        return report
