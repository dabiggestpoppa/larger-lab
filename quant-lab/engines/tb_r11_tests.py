#!/usr/bin/env python3
"""
TB-R1.1 — MECHANICAL REPAIR TEST SUITE
=======================================
Deterministic tests for the R1.1 repairs:

  A. fail-closed execution mode (default SHADOW, no order_send path)
  B/C/F. primary 3.0 / signed +-0.25 vs control 2.5 / 0 (separate, control shadow-only)
  D. canonical TB-B exact-neutral weights (sum 3, residual <= 0.1%)
  G. control can never execute
  direction -> leg-intent mapping
  exit-condition check order (hard exit -> TP -> SL) + strictness
  entry strictness |z| > threshold
  legacy-contamination scan of the strategy path
  atomic-execution regression (execution layer consumes TB-B weights unchanged)

Run:  python quant-lab/engines/tb_r11_tests.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np

from triangular_basis_live import (  # noqa: E402
    TriangularBasisLiveEngine, BasketDecision, BasketState,
    Direction, TriangularBar,  # re-exported from the canonical engine
)
from tb_forward_config import (  # noqa: E402
    PRIMARY_CONFIG, CONTROL_CONFIG,
)
from tb_p6_anatomy import project_basket  # noqa: E402
from verify_tb_04a import exposure_matrix, residual_pct  # noqa: E402

# Valid triangle prices (real P7 entry bar) so TB-B projection succeeds.
GA, GN, AN = 1.70179, 1.91038, 1.12619

TESTS = []


def test(fn):
    TESTS.append(fn)
    return fn


def make_engine(model_config):
    return TriangularBasisLiveEngine(model_config=model_config)


def make_bar(ga=GA, gn=GN, an=AN):
    from datetime import datetime
    return TriangularBar(
        timestamp=datetime(2024, 6, 10, 10, 0, 0),
        gbp_aud=ga, gbp_nzd=gn, aud_nzd=an,
        gbp_aud_high=ga, gbp_aud_low=ga,
        gbp_nzd_high=gn, gbp_nzd_low=gn,
        aud_nzd_high=an, aud_nzd_low=an,
    )


def build_intent(engine, z, basis=0.01):
    return engine._build_entry_intent(
        z, basis, make_bar(),
        atr_gbp_aud=0.01, atr_gbp_nzd=0.01, atr_aud_nzd=0.01,
    )


def close(engine, direction, z, est_hour=10):
    bs = BasketState(
        basket_id="T", direction=direction, entry_basis=0.0, entry_zscore=3.5,
        entry_time=None, exit_deadline=None,
    )
    return engine._check_close_condition(bs, z, est_hour)


# ─── ENTRY STRICTNESS (primary 3.0, strict >) ────────────────────────────
@test
def primary_entry_2_999999_rejected():
    e = make_engine(PRIMARY_CONFIG)
    assert build_intent(e, 2.999999).decision == BasketDecision.NO_ACTION


@test
def primary_entry_3_0_rejected():
    e = make_engine(PRIMARY_CONFIG)
    assert build_intent(e, 3.0).decision == BasketDecision.NO_ACTION


@test
def primary_entry_3_000001_accepted():
    e = make_engine(PRIMARY_CONFIG)
    assert build_intent(e, 3.000001).decision == BasketDecision.OPEN_BASKET


@test
def primary_entry_negative_3_0_rejected():
    e = make_engine(PRIMARY_CONFIG)
    assert build_intent(e, -3.0).decision == BasketDecision.NO_ACTION


@test
def primary_entry_negative_3_000001_accepted():
    e = make_engine(PRIMARY_CONFIG)
    assert build_intent(e, -3.000001).decision == BasketDecision.OPEN_BASKET


# ─── ENTRY STRICTNESS (control 2.5, strict >) ────────────────────────────
@test
def control_entry_2_5_rejected():
    e = make_engine(CONTROL_CONFIG)
    assert build_intent(e, 2.5).decision == BasketDecision.NO_ACTION


@test
def control_entry_2_500001_accepted():
    e = make_engine(CONTROL_CONFIG)
    assert build_intent(e, 2.500001).decision == BasketDecision.OPEN_BASKET


# ─── SIGNED EXIT (primary) ───────────────────────────────────────────────
@test
def primary_short_exit_not_yet_at_neg_0_249999():
    e = make_engine(PRIMARY_CONFIG)
    assert close(e, Direction.SHORT, -0.249999) == ""


@test
def primary_short_exit_at_neg_0_25():
    e = make_engine(PRIMARY_CONFIG)
    assert close(e, Direction.SHORT, -0.25) == "TP_HIT"


@test
def primary_long_exit_not_yet_at_pos_0_249999():
    e = make_engine(PRIMARY_CONFIG)
    assert close(e, Direction.LONG, 0.249999) == ""


@test
def primary_long_exit_at_pos_0_25():
    e = make_engine(PRIMARY_CONFIG)
    assert close(e, Direction.LONG, 0.25) == "TP_HIT"


# ─── CONTROL EXIT (symmetric 0.0) ────────────────────────────────────────
@test
def control_short_exit_at_0():
    e = make_engine(CONTROL_CONFIG)
    assert close(e, Direction.SHORT, 0.0) == "TP_HIT"


@test
def control_long_exit_at_0():
    e = make_engine(CONTROL_CONFIG)
    assert close(e, Direction.LONG, 0.0) == "TP_HIT"


# ─── STOP (symmetric magnitude 6.0) ──────────────────────────────────────
@test
def short_stop_at_pos_6():
    e = make_engine(PRIMARY_CONFIG)
    assert close(e, Direction.SHORT, 6.0) == "SL_HIT"


@test
def short_stop_not_at_5_999():
    e = make_engine(PRIMARY_CONFIG)
    assert close(e, Direction.SHORT, 5.999) == ""


@test
def long_stop_at_neg_6():
    e = make_engine(PRIMARY_CONFIG)
    assert close(e, Direction.LONG, -6.0) == "SL_HIT"


@test
def long_stop_not_at_neg_5_999():
    e = make_engine(PRIMARY_CONFIG)
    assert close(e, Direction.LONG, -5.999) == ""


# ─── EXIT ORDER (hard exit wins over TP) ─────────────────────────────────
@test
def hard_exit_wins_over_tp():
    e = make_engine(PRIMARY_CONFIG)
    # SHORT trade, z already past the -0.25 target but session ended
    assert close(e, Direction.SHORT, -1.0, est_hour=12) == "TIMEOUT"


@test
def hard_exit_wins_over_stop():
    e = make_engine(PRIMARY_CONFIG)
    assert close(e, Direction.SHORT, 6.5, est_hour=12) == "TIMEOUT"


# ─── DIRECTION -> LEG INTENT MAPPING ─────────────────────────────────────
@test
def z_positive_maps_to_short_basket():
    e = make_engine(PRIMARY_CONFIG)
    it = build_intent(e, 3.5)
    assert it.direction == Direction.SHORT
    sides = [l.side for l in it.legs]
    assert sides == [Direction.SHORT, Direction.LONG, Direction.SHORT]
    assert [l.canonical_symbol for l in it.legs] == ["GBPAUD", "GBPNZD", "AUDNZD"]


@test
def z_negative_maps_to_long_basket():
    e = make_engine(PRIMARY_CONFIG)
    it = build_intent(e, -3.5)
    assert it.direction == Direction.LONG
    sides = [l.side for l in it.legs]
    assert sides == [Direction.LONG, Direction.SHORT, Direction.LONG]


# ─── TB-B WEIGHTS ────────────────────────────────────────────────────────
@test
def tb_b_weights_sum_to_three():
    e = make_engine(PRIMARY_CONFIG)
    w = e._compute_tb_b_weights(Direction.SHORT, GA, GN, AN, 0.6, 0.5, 1.8)
    assert abs(sum(w[:3]) - 3.0) < 1e-9


@test
def tb_b_residual_within_tolerance():
    e = make_engine(PRIMARY_CONFIG)
    w = e._compute_tb_b_weights(Direction.SHORT, GA, GN, AN, 0.6, 0.5, 1.8)
    assert w[3] <= 0.1 + 1e-6


@test
def model_weight_is_not_lots():
    e = make_engine(PRIMARY_CONFIG)
    it = build_intent(e, 3.5)
    # model weights are ~1.0 scale (sum 3), NOT 0.01-lot scale
    total = sum(l.model_weight for l in it.legs)
    assert abs(total - 3.0) < 1e-6
    assert all(l.model_weight > 0.1 for l in it.legs)


# ─── CONFIG SEPARATION / EXECUTION FLAGS ─────────────────────────────────
@test
def primary_is_3_0():
    assert PRIMARY_CONFIG.entry_z == 3.0


@test
def primary_signed_exit():
    assert PRIMARY_CONFIG.short_exit_z == -0.25
    assert PRIMARY_CONFIG.long_exit_z == 0.25


@test
def control_is_2_5():
    assert CONTROL_CONFIG.entry_z == 2.5


@test
def control_symmetric_exit_zero():
    assert CONTROL_CONFIG.short_exit_z == 0.0
    assert CONTROL_CONFIG.long_exit_z == 0.0


@test
def control_shadow_only():
    assert CONTROL_CONFIG.shadow_only is True
    assert CONTROL_CONFIG.execution_allowed is False


@test
def primary_execution_not_authorized_this_checkpoint():
    assert PRIMARY_CONFIG.execution_allowed is False


# ─── FAIL-CLOSED EXECUTION MODE (executor resolve_mode) ──────────────────
def _resolve_mode(mode):
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "tb_exec", str(Path(__file__).parent.parent / "mt5" / "triangular_basis_executor.py"))
    m = importlib.util.module_from_spec(spec)
    # avoid actually importing MetaTrader5 / strategy registry side effects by
    # execing only the config section? Simpler: import the real module in a
    # subprocess-free way — the module guards MT5 import, but configs.strategy_registry
    # must exist. We exec the module but stub heavy imports instead.
    return None  # placeholder


@test
def executor_default_mode_is_shadow():
    import ast
    src = (Path(__file__).parent.parent / "mt5" / "triangular_basis_executor.py").read_text(encoding="utf-8-sig")
    assert 'default="shadow"' in src
    assert "DEFAULT_MODE = \"shadow\"" in src


@test
def executor_cli_choices_exclude_trade():
    import ast
    src = (Path(__file__).parent.parent / "mt5" / "triangular_basis_executor.py").read_text(encoding="utf-8-sig")
    assert "choices=[\"shadow\", \"demo\"]" in src
    assert 'choices=["replay", "shadow", "trade"]' not in src


@test
def executor_global_execution_authorized_false():
    import ast
    src = (Path(__file__).parent.parent / "mt5" / "triangular_basis_executor.py").read_text(encoding="utf-8-sig")
    assert "EXECUTION_AUTHORIZED = False" in src
    assert "DEMO_AUTHORIZED = False" in src
    assert "LIVE_AUTHORIZED = False" in src


# ─── LEGACY CONTAMINATION SCAN (strategy path) ───────────────────────────
@test
def no_legacy_strategy_imports_in_live_wrapper():
    src = (Path(__file__).parent / "triangular_basis_live.py").read_text(encoding="utf-8-sig")
    forbidden = [
        "SymmetryTrap", "symmetry_trap", "P90", "p90", "AsianRange",
        "asian_range", "RR_GATE", "profit_lock", "single_leg_tp",
        "cerebus_live_bridge", "clean_bridge",
    ]
    hit = [t for t in forbidden if t in src]
    assert hit == [], f"forbidden tokens in live wrapper: {hit}"


@test
def no_legacy_strategy_imports_in_forward_config():
    src = (Path(__file__).parent / "tb_forward_config.py").read_text(encoding="utf-8")
    forbidden = ["SymmetryTrap", "P90", "AsianRange", "RR_GATE", "profit_lock"]
    hit = [t for t in forbidden if t in src]
    assert hit == [], f"forbidden tokens in config: {hit}"


# ─── ATOMIC EXECUTION REGRESSION (execution layer consumes TB-B weights) ─
@test
def execution_layer_sizes_tb_b_weights():
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mt5.triangular_execution_layer import TriangularExecutionLayer
    from engines.triangular_execution_contract import (
        BrokerLegIntent, BasketExecutionIntent, ContractSpec,
    )
    from datetime import datetime
    layer = TriangularExecutionLayer(
        magic_number=31082026,
        contract_specs={
            "GBPAUD.PRO": ContractSpec(contract_size=100000, volume_min=0.01,
                                       volume_max=100, volume_step=0.01,
                                       point=0.0001, digits=5),
            "GBPNZD.PRO": ContractSpec(contract_size=100000, volume_min=0.01,
                                       volume_max=100, volume_step=0.01,
                                       point=0.0001, digits=5),
            "AUDNZD.PRO": ContractSpec(contract_size=100000, volume_min=0.01,
                                       volume_max=100, volume_step=0.01,
                                       point=0.0001, digits=5),
        },
        basket_notional_usd=10000.0,
    )
    legs = [
        BrokerLegIntent(canonical_symbol="GBPAUD", broker_symbol="GBPAUD.PRO",
                        side=Direction.SHORT, model_weight=1.04364452,
                        signal_reference_price=GA, magic=31082026, basket_id="T"),
        BrokerLegIntent(canonical_symbol="GBPNZD", broker_symbol="GBPNZD.PRO",
                        side=Direction.LONG, model_weight=0.97756661,
                        signal_reference_price=GN, magic=31082026, basket_id="T"),
        BrokerLegIntent(canonical_symbol="AUDNZD", broker_symbol="AUDNZD.PRO",
                        side=Direction.SHORT, model_weight=0.97878887,
                        signal_reference_price=AN, magic=31082026, basket_id="T"),
    ]
    intent = BasketExecutionIntent(
        basket_id="T", timestamp=datetime(2024, 6, 10, 10, 0, 0),
        direction_side=Direction.SHORT, entry_basis=0.0, entry_zscore=3.5,
        legs=legs,
    )
    sized = layer._size_legs(intent, {
        "GBPAUD": (GA, GA), "GBPNZD": (GN, GN), "AUDNZD": (AN, AN),
    })
    assert len(sized) == 3
    assert all(l.rounded_lots > 0 for l in sized)
    # total notional allocation sums to the basket budget
    total = sum(l.target_notional_account_ccy for l in sized)
    assert abs(total - 10000.0) < 1.0


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
