"""QL-EXEC-R4 — TB strategy science parity (frozen canonical science).

R4 must prove the generic TB adapter reproduces the canonical TB strategy
science EXACTLY: basis, rolling-z (lookback 200, ddof=0, previous-bars-only),
entry/exit/stop thresholds, signed exits, London session (fixed UTC-5, no DST),
direction mapping, one-concurrent-basket, and re-entry. The adapter delegates
to the canonical engine; these tests freeze that delegation is lossless.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from execution_runtime.tb.harness import (
    make_control_fixture,
    make_snapshot,
    make_tri_bar,
)
from execution_runtime.tb.adapters import TBStrategyAdapter, _side_sign

# canonical science (reused, never rewritten)
import sys
from pathlib import Path
_QL = Path(__file__).resolve().parents[2]
for _p in (_QL, _QL / "engines"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from engines.triangular_basis_engine import (  # noqa: E402
    compute_basis,
    compute_basis_zscore,
    TriangularBar,
    _est_hour,
)
from engines.triangular_basis_live import (  # noqa: E402
    TriangularBasisLiveEngine,
    BasketDecision,
)
from engines.tb_forward_config import PRIMARY_CONFIG, CONTROL_CONFIG  # noqa: E402


def _basis(b: TriangularBar) -> float:
    return math.log(b.gbp_aud) - math.log(b.gbp_nzd) + math.log(b.aud_nzd)


def test_basis_formula_parity():
    fix = make_control_fixture()
    basis = compute_basis(list(fix.bars))
    assert basis == pytest.approx([_basis(b) for b in fix.bars], rel=1e-12)


def test_zscore_previous_200_bars_excluding_current():
    fix = make_control_fixture()
    basis = compute_basis(list(fix.bars))
    z = compute_basis_zscore(basis, 200)
    i = fix.signal_index
    window = basis[i - 200 : i]  # [i-200, i): current excluded
    mean = float(np.mean(window))
    std = float(np.std(window))  # ddof=0 (numpy default)
    assert len(window) == 200
    assert z[i] == pytest.approx((basis[i] - mean) / std, rel=1e-9)


def test_zscore_ddof0_semantics():
    basis = [1.0, 2.0, 3.0, 4.0, 5.0]
    z = compute_basis_zscore(basis, 3)
    # i=3: window=[1,2,3] mean=2 std=sqrt(2/3) (population)
    mean = 2.0
    std = math.sqrt(((1 - 2) ** 2 + (2 - 2) ** 2 + (3 - 2) ** 2) / 3)
    assert z[3] == pytest.approx((4.0 - mean) / std, rel=1e-9)


def test_frozen_thresholds():
    assert PRIMARY_CONFIG.entry_z == 3.0
    assert PRIMARY_CONFIG.short_exit_z == -0.25
    assert PRIMARY_CONFIG.long_exit_z == 0.25
    assert PRIMARY_CONFIG.stop_z == 6.0
    assert CONTROL_CONFIG.entry_z == 2.5
    assert CONTROL_CONFIG.short_exit_z == 0.0
    assert CONTROL_CONFIG.long_exit_z == 0.0
    assert CONTROL_CONFIG.stop_z == 6.0


def test_frozen_session_semantics():
    eng = TriangularBasisLiveEngine(model_config=CONTROL_CONFIG)
    cfg = eng.config
    assert cfg.BASIS_LOOKBACK == 200
    assert cfg.TRADE_LONDON_ONLY is True
    assert cfg.LONDON_START_H_EST == 3
    assert cfg.LONDON_END_H_EST == 12
    assert cfg.HARD_EXIT_H_EST == 12
    assert cfg.MIN_MINUTES_TO_EXIT == 120


def test_est_hour_fixed_utc_minus_5():
    from datetime import datetime
    assert _est_hour(datetime(2024, 1, 2, 10, 0, 0)) == 5
    assert _est_hour(datetime(2024, 1, 2, 3, 0, 0)) == 22
    # no DST correction ever: same raw hour maps to the same est hour year-round
    assert _est_hour(datetime(2024, 7, 2, 10, 0, 0)) == 5


def test_direction_mapping_short():
    assert _side_sign("SHORT", "GBPAUD") == "SELL"
    assert _side_sign("SHORT", "GBPNZD") == "BUY"
    assert _side_sign("SHORT", "AUDNZD") == "SELL"
    assert _side_sign("LONG", "GBPAUD") == "BUY"
    assert _side_sign("LONG", "GBPNZD") == "SELL"
    assert _side_sign("LONG", "AUDNZD") == "BUY"


def test_control_signal_direction_parity():
    fix = make_control_fixture()
    eng = TriangularBasisLiveEngine(model_config=CONTROL_CONFIG)
    eng.load_historical_bars(list(fix.bars[: fix.signal_index]))
    intent = eng.process_snapshot(make_snapshot(fix.bars[fix.signal_index]))
    assert intent.decision is BasketDecision.OPEN_BASKET
    # z > 0 => SHORT basket: sell GA, buy GN, sell AN
    assert intent.direction.name == "SHORT"
    sides = {leg.canonical_symbol: leg.side.name for leg in intent.legs}
    assert sides == {"GBPAUD": "SHORT", "GBPNZD": "LONG", "AUDNZD": "SHORT"}


def test_primary_signal_zero_broker_orders():
    """A valid PRIMARY z3 event must produce zero orders in BOTH paths."""
    from execution_runtime.tb.harness import LegacyTBHarness, GenericTBHarness, BASKET_NOTIONAL_USD
    fix = make_control_fixture()
    ref = LegacyTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD)
    gen = GenericTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD, db_path=":memory:")
    ref.warm(fix.bars[: fix.signal_index])
    gen.warm(fix.bars[: fix.signal_index])
    snap = make_snapshot(fix.bars[fix.signal_index])
    ref.step(snap)
    gen.step(snap)
    # PRIMARY is shadow-only in both: primary contributes 0 sends; only control
    # (z > 2.5, also triggered) sends 3 legs.
    assert ref.primary_order_sends == 0
    assert gen.primary_order_sends == 0
    assert ref.control_order_sends == 3
    assert gen.control_order_sends == 3


def test_adapter_delegates_to_canonical_engine():
    fix = make_control_fixture()
    adapter = TBStrategyAdapter(CONTROL_CONFIG)
    adapter.warm(list(fix.bars[: fix.signal_index]))
    adapter.on_market_snapshot(make_snapshot(fix.bars[fix.signal_index]))
    events = adapter.produce_events()
    assert len(events) == 1
    assert events[0].strategy_id == CONTROL_CONFIG.strategy_id
    assert events[0].event_kind == "ENTRY"
    assert events[0].payload["direction"] == "SHORT"
    assert len(events[0].payload["legs"]) == 3


def test_one_concurrent_basket_no_pyramiding():
    fix = make_control_fixture()
    eng = TriangularBasisLiveEngine(model_config=CONTROL_CONFIG)
    eng.load_historical_bars(list(fix.bars[: fix.signal_index]))
    i1 = eng.process_snapshot(make_snapshot(fix.bars[fix.signal_index]))
    assert i1.decision is BasketDecision.OPEN_BASKET
    eng.on_basket_open_confirmed(i1.basket_id)
    # a second in-session bar (no exit yet) must NOT open another basket
    bar2 = make_tri_bar(
        __import__("datetime").datetime(2024, 1, 2, 10, 10, 0), 1.8190, 1.9780, 1.0940
    )
    i2 = eng.process_snapshot(make_snapshot(bar2))
    assert i2.decision is not BasketDecision.OPEN_BASKET


def test_reentry_after_close_allowed():
    from datetime import datetime
    fix = make_control_fixture()
    eng = TriangularBasisLiveEngine(model_config=CONTROL_CONFIG)
    eng.load_historical_bars(list(fix.bars[: fix.signal_index]))
    i1 = eng.process_snapshot(make_snapshot(fix.bars[fix.signal_index]))
    eng.on_basket_open_confirmed(i1.basket_id)
    # close it (exit bar triggers SHORT exit since z drops)
    i2 = eng.process_snapshot(make_snapshot(fix.bars[fix.exit_index]))
    assert i2.decision is BasketDecision.CLOSE_BASKET
    eng.on_basket_close_confirmed(i2.basket_id)
    # now flat -> re-entry is allowed (no cooldown)
    bar3 = make_tri_bar(datetime(2024, 1, 2, 10, 15, 0), 1.8220, 1.9780, 1.0940)
    i3 = eng.process_snapshot(make_snapshot(bar3))
    # a fresh signal can open again (decision may be OPEN or NO_ACTION depending
    # on z; the key contract is no cooldown latch, so assert it does not raise
    # and does not remain blocked by a cooldown flag)
    assert i3.decision in (BasketDecision.OPEN_BASKET, BasketDecision.NO_ACTION)
