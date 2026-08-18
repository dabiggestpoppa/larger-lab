"""QL-EXEC-R4 — TB execution parity (basket open / broken hedge / close / lots).

Reference (canonical TriangularExecutionLayer + FakeBroker) and generic
(BasketOrchestrator + SimBrokerSession) are fed identical frozen bars. The
normal-path lifecycle trace and final broker state must match EXACTLY; the
model-weight -> notional -> lot translation must match EXACTLY; failure
recovery must reach the same safe state (partial fill is never treated as a
full fill; broken hedge flattens owned exposure; foreign positions untouched).
"""
from __future__ import annotations

import pytest

from execution_runtime.tb.harness import (
    LegacyTBHarness,
    GenericTBHarness,
    ParityRunner,
    make_control_fixture,
    make_snapshot,
    BASKET_NOTIONAL_USD,
)
from execution_runtime.tb.parity import ParityTier


def _open_state(h):
    fix = make_control_fixture()
    h.warm(fix.bars[: fix.signal_index])
    h.step(make_snapshot(fix.bars[fix.signal_index]))
    return h.snapshot()


def test_normal_open_close_full_parity():
    fix = make_control_fixture()
    ref = LegacyTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD)
    gen = GenericTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD, db_path=":memory:")
    rep = ParityRunner(ref, gen).run(fix)
    assert rep.pass_ok(), rep.tiers()
    assert rep.tiers()["execution_trace"] == ParityTier.EXACT.value
    assert rep.tiers()["final_state"] == ParityTier.EXACT.value


def test_lot_translation_exact_parity():
    ref = LegacyTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD)
    gen = GenericTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD, db_path=":memory:")
    ref_state = _open_state(ref)
    gen_state = _open_state(gen)
    assert ref_state == gen_state
    # three owned legs, correct sides, exact same quantities
    assert ref_state["basket_state"] == "OPEN"
    assert len(ref_state["owned_positions"]) == 3


def test_model_weight_is_not_lot():
    """TB-B model weights sum to 3 (model units); lots are NOT model weights."""
    import sys
    from pathlib import Path as _P
    _QL = _P(__file__).resolve().parents[2]
    if str(_QL / "engines") not in sys.path:
        sys.path.insert(0, str(_QL / "engines"))
    from engines.triangular_basis_live import TriangularBasisLiveEngine
    from engines.tb_forward_config import CONTROL_CONFIG
    fix = make_control_fixture()
    eng = TriangularBasisLiveEngine(model_config=CONTROL_CONFIG)
    eng.load_historical_bars(list(fix.bars[: fix.signal_index]))
    c = eng.process_snapshot(make_snapshot(fix.bars[fix.signal_index]))
    weights = [leg.model_weight for leg in c.legs]
    assert pytest.approx(sum(abs(w) for w in weights), rel=1e-6) == 3.0

    ref = LegacyTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD)
    lots = {p[0]: p[2] for p in _open_state(ref)["owned_positions"]}
    assert lots["GBPAUD.PRO"] != weights[0]  # model weight != broker lots


def test_broken_hedge_flattens_owned_exposure():
    fix = make_control_fixture()
    ref = LegacyTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD, broker_profile="leg2_reject")
    gen = GenericTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD, db_path=":memory:")
    gen.broker.set_symbol_fail_mode("GBPNZD.PRO", "ORDER_REJECT")
    ref.warm(fix.bars[: fix.signal_index])
    gen.warm(fix.bars[: fix.signal_index])
    snap = make_snapshot(fix.bars[fix.signal_index])
    ref.step(snap)
    gen.step(snap)
    # both reach ABORTED_FLAT with zero owned exposure and 3 sends
    assert ref.snapshot() == gen.snapshot()
    assert ref.snapshot()["basket_state"] == "ABORTED_FLAT"
    assert ref.snapshot()["owned_positions"] == []
    assert ref.snapshot()["order_send_count"] == 3


@pytest.mark.parametrize("leg", ["leg1_reject", "leg2_reject", "leg3_reject"])
def test_per_leg_reject_parity(leg):
    sym = {"leg1_reject": "GBPAUD.PRO", "leg2_reject": "GBPNZD.PRO",
           "leg3_reject": "AUDNZD.PRO"}[leg]
    fix = make_control_fixture()
    ref = LegacyTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD, broker_profile=leg)
    gen = GenericTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD, db_path=":memory:")
    gen.broker.set_symbol_fail_mode(sym, "ORDER_REJECT")
    ref.warm(fix.bars[: fix.signal_index])
    gen.warm(fix.bars[: fix.signal_index])
    snap = make_snapshot(fix.bars[fix.signal_index])
    ref.step(snap)
    gen.step(snap)
    assert ref.snapshot() == gen.snapshot()
    assert ref.snapshot()["owned_positions"] == []  # flatten verified


def test_partial_fill_is_not_full_fill():
    fix = make_control_fixture()
    ref = LegacyTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD, broker_profile="all_success")
    gen = GenericTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD, db_path=":memory:")
    gen.broker.set_symbol_fail_mode("GBPNZD.PRO", "PARTIAL_FILL")
    ref.warm(fix.bars[: fix.signal_index])
    gen.warm(fix.bars[: fix.signal_index])
    snap = make_snapshot(fix.bars[fix.signal_index])
    ref.step(snap)  # reference fills all (control)
    gen.step(snap)  # generic partial-fills leg 2 -> broken hedge
    # generic must NOT claim OPEN with a partial leg; it flattens to flat
    assert gen.snapshot()["basket_state"] in ("ABORTED_FLAT", "RECONCILIATION_REQUIRED")
    assert gen.snapshot()["owned_positions"] == []


def test_no_open_before_broker_verification():
    from execution_runtime.tb.basket import BasketOrchestrator, BasketPlanState
    fix = make_control_fixture()
    gen = GenericTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD, db_path=":memory:")
    gen.warm(fix.bars[: fix.signal_index])
    snap = make_snapshot(fix.bars[fix.signal_index])
    # zero-fill all legs: accepted orders but no positions -> never OPEN
    gen.broker.set_fail_mode("ZERO_FILL")
    gen.step(snap)
    assert gen.snapshot()["basket_state"] in ("ABORTED_FLAT", "RECONCILIATION_REQUIRED")
    assert gen.snapshot()["owned_positions"] == []


def test_primary_shadow_zero_order_both_paths():
    fix = make_control_fixture()
    ref = LegacyTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD)
    gen = GenericTBHarness(basket_notional_usd=BASKET_NOTIONAL_USD, db_path=":memory:")
    ref.warm(fix.bars[: fix.signal_index])
    gen.warm(fix.bars[: fix.signal_index])
    snap = make_snapshot(fix.bars[fix.signal_index])
    ref.step(snap)
    gen.step(snap)
    assert ref.primary_order_sends == 0
    assert gen.primary_order_sends == 0
