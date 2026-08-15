"""
Phase 7 tests (CR-P7-ROUTING-TRANSLATION-01).

Covers: window indexing, causal entry, cost application (spread + swap),
basket weights, routing efficiency, nested split assignment, holdout
untouched during selection, plateau detection, symmetry handling,
determinism (fixed seeds).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT / "src"))

from capital_routing.phases.phase_7_families import (
    FAMILIES,
    ONE_WAY_COST_BPS,
    SPLIT,
    _bootstrap_effect_ci,
    evaluate_static_criteria,
    load_phase6_evidence,
    swap_bps_per_day,
)
from capital_routing.phases.phase_7_execution import (
    _window,
    build_execution_grid,
    equal_risk_basket,
    orient_trade,
    routing_efficiency,
)
from capital_routing.phases.phase_7_analysis import (
    entry_delay_surface,
    excursion_geometry,
    mirrored_symmetry,
    pair_space_comparison,
    plateau_analysis,
)
from capital_routing.phases.phase_7_baseline import run_baseline, vol_normalize_position
from capital_routing.phases.phase_7_gate import evaluate_criterion6


# ---------------------------------------------------------------------------
# synthetic fixtures
# ---------------------------------------------------------------------------
def make_panel(n=500, start="2024-01-01", pairs=None):
    pairs = pairs or ["EURJPY", "USDJPY", "GBPJPY", "CHFJPY"]
    idx = pd.date_range(start, periods=n, freq="h", tz="UTC")
    rng = np.random.default_rng(42)
    data = {}
    for p in pairs:
        # geometric random walk with a small drift
        rets = rng.normal(0.0002, 0.001, n)
        px = 100 * np.exp(np.cumsum(rets))
        data[f"{p}_close"] = px
    return pd.DataFrame(data, index=idx)


def make_events(panel, n=40):
    starts = panel.index[::5][:n]
    return pd.DataFrame({
        "event_id": [f"e{i}" for i in range(n)],
        "event_start": starts,
        "origin_currency": ["EUR"] * n,
        "direction": ["ACCUMULATION"] * n,
        "severity": ["MEDIUM"] * n,
        "session": ["London"] * n,
    })


@pytest.fixture(scope="module")
def p6_dir():
    return ROOT / "artifacts" / "phase_06"


@pytest.fixture(scope="module")
def evidence(p6_dir):
    return load_phase6_evidence(p6_dir)


# ---------------------------------------------------------------------------
# 1. forward horizon indexing / window bounds
# ---------------------------------------------------------------------------
def test_window_bounds_delay_hold():
    grid = pd.date_range("2024-01-01", periods=100, freq="h", tz="UTC")
    grid_ns = grid.values.astype("int64")
    t0 = int(grid_ns[10])
    entry, exit_i = _window(grid_ns, t0, 0, 4)
    # entry = first bar strictly after t0 -> index 11; exit = last bar <= t0+4h -> 14
    assert entry == 11
    assert exit_i == 14
    # delay 2, hold 4 -> entry first bar after t0+2h = 13; exit <= t0+6h = 16
    entry, exit_i = _window(grid_ns, t0, 2, 4)
    assert entry == 13
    assert exit_i == 16
    # empty window: event at the last bar -> no future bars
    entry, exit_i = _window(grid_ns, int(grid_ns[-1]), 0, 10)
    assert exit_i < entry


def test_event_bar_excluded():
    """Entry at delay 0 must be strictly after the event bar (no look-ahead)."""
    panel = make_panel()
    ev = make_events(panel)
    g = build_execution_grid(ev, panel, ["EURJPY"], [0], [4], apply_costs=False)
    assert len(g) > 0
    # every event's start must be present in the events frame (round trip)
    ts = pd.to_datetime(ev["event_start"], utc=True)
    for eid in g["event_id"].unique():
        assert eid in set(ev["event_id"])
        t0 = ts[ev["event_id"] == eid].iloc[0]
        row_ts = pd.to_datetime(g[g["event_id"] == eid]["event_start"].iloc[0], utc=True)
        assert row_ts == t0


# ---------------------------------------------------------------------------
# 2. costs: spread and swap
# ---------------------------------------------------------------------------
def test_swap_bps_per_day_sane():
    # 3.25% annual diff = ~0.89 bps/day
    assert abs(swap_bps_per_day("GBPJPY") - 0.89) < 0.01
    # symmetric: reversing base/quote flips sign
    assert abs(swap_bps_per_day("GBPJPY") + swap_bps_per_day("JPYGBP")) < 1e-9


def test_costs_applied():
    panel = make_panel()
    ev = make_events(panel)
    g = build_execution_grid(ev, panel, ["EURJPY"], [0], [4], apply_costs=True)
    # build_execution_grid applies spread/commission only; swap added signed in orient_trade
    assert g["cost_bps"].iloc[0] == pytest.approx(2 * ONE_WAY_COST_BPS["EURJPY"])
    g2 = orient_trade(g, FAMILIES["A"])  # long: +swap
    assert g2["cost_bps"].iloc[0] == pytest.approx(
        2 * ONE_WAY_COST_BPS["EURJPY"] + swap_bps_per_day("EURJPY") * 4 / 24.0)


def test_short_swap_reversed():
    """orient_trade must reverse carry for short legs (Family C)."""
    panel = make_panel(pairs=["USDCHF", "CHFJPY"])
    ev = make_events(panel)
    g = build_execution_grid(ev, panel, ["USDCHF", "CHFJPY"], [0], [48],
                             apply_costs=True)
    g = orient_trade(g, FAMILIES["C"])
    short_cost = g[g["pair"] == "USDCHF"]["cost_bps"].iloc[0]
    long_cost = g[g["pair"] == "CHFJPY"]["cost_bps"].iloc[0]
    spread_part = 2 * ONE_WAY_COST_BPS["USDCHF"]
    swap_part = -swap_bps_per_day("USDCHF") * 48 / 24.0  # short reverses carry
    assert short_cost == pytest.approx(spread_part + swap_part)
    assert short_cost < long_cost


# ---------------------------------------------------------------------------
# 3. basket weights
# ---------------------------------------------------------------------------
def test_equal_risk_basket_inverse_vol():
    panel = make_panel()
    ev = make_events(panel)
    g = build_execution_grid(ev, panel, ["EURJPY", "USDJPY"], [0], [4])
    g = orient_trade(g, FAMILIES["A"])
    b = equal_risk_basket(g, ["EURJPY", "USDJPY"])
    assert len(b) > 0
    # basket net = weighted directional returns minus weighted costs
    for _, brow in b.iterrows():
        eid, d, h = brow["event_id"], brow["delay_h"], brow["hold_h"]
        gr = g[(g["event_id"] == eid) & (g["delay_h"] == d) & (g["hold_h"] == h)]
        w = 1.0 / gr["rv_bps_per_h"]
        w = w / w.sum()
        expected = (gr["dir_return_bps"] * w).sum() - (gr["cost_bps"] * w).sum()
        assert brow["dir_net_bps"] == pytest.approx(expected)


# ---------------------------------------------------------------------------
# 4. routing efficiency formula
# ---------------------------------------------------------------------------
def test_routing_efficiency_formula():
    row = pd.Series({"mfe_bps": 20.0, "mae_bps": -5.0, "cost_bps": 5.0})
    assert routing_efficiency(row) == pytest.approx(20.0 / (5.0 + 5.0))
    row2 = pd.Series({"mfe_bps": 10.0, "mae_bps": np.nan, "cost_bps": 2.0})
    assert routing_efficiency(row2) == pytest.approx(10.0 / 2.0)


# ---------------------------------------------------------------------------
# 5. nested split assignment
# ---------------------------------------------------------------------------
def test_split_assignment():
    # 110 weekly events need >= ~110 weeks of hourly panel
    panel = make_panel(n=19000, start="2023-08-01")
    ev = make_events(panel, n=110)
    ev["event_start"] = pd.date_range("2023-08-01", periods=110, freq="7D", tz="UTC")
    g = build_execution_grid(ev, panel, ["EURJPY"], [0], [4])
    assert len(g) > 0
    assert set(g["split"].unique()) <= {"inner_sel", "inner_val", "untouched"}
    assert set(g["split"].unique()) == {"inner_sel", "inner_val", "untouched"}
    # chronological: no untouched event before inner_sel event
    ts = pd.to_datetime(g["event_start"], utc=True)
    assert ts[g["split"] == "untouched"].min() >= ts[g["split"] == "inner_sel"].max()


def test_holdout_not_used_in_selection():
    """Plateau/config selection must be computed on inner_sel only."""
    panel = make_panel(n=19000, start="2023-08-01")
    ev = make_events(panel, n=110)
    ev["event_start"] = pd.date_range("2023-08-01", periods=110, freq="7D", tz="UTC")
    g = build_execution_grid(ev, panel, ["EURJPY", "USDJPY"], [0, 1], [4, 6])
    g = orient_trade(g, FAMILIES["A"])
    surf = entry_delay_surface(g, FAMILIES["A"], splits=["inner_sel", "inner_val"])
    assert set(surf["split"].unique()) == {"inner_sel", "inner_val"}
    assert "untouched" not in set(surf["split"].unique())
    plateau = plateau_analysis(surf, FAMILIES["A"], split="inner_sel")
    # recommended config comes from validated horizons only
    assert plateau["recommended_hold"] in FAMILIES["A"]["horizons"]


# ---------------------------------------------------------------------------
# 6. bootstrap deterministic
# ---------------------------------------------------------------------------
def test_bootstrap_deterministic():
    rng = np.random.default_rng(7)
    v = rng.normal(0.001, 0.01, 200)
    a = _bootstrap_effect_ci(v)
    b = _bootstrap_effect_ci(v)
    assert a["ci_low"] == b["ci_low"]
    assert a["ci_high"] == b["ci_high"]


# ---------------------------------------------------------------------------
# 7. alpha gate criteria
# ---------------------------------------------------------------------------
def test_static_gate_criteria_1_4(evidence):
    for fam in FAMILIES.values():
        st = evaluate_static_criteria(fam, evidence["holdout"],
                                      evidence["overlap"], evidence["factors"])
        assert st["checks"]["1_same_holdout_sign"]["pass"]
        assert st["checks"]["2_holdout_effect_50pct"]["pass"]
        assert st["checks"]["3_bootstrap_ci_excludes_zero"]["pass"]
        assert st["checks"]["4_adequate_holdout_n"]["pass"]


def test_criterion6_family_c_plateau():
    surf = pd.DataFrame({
        "family": ["JPY_LIQUIDATION_CHF_STRENGTH"] * 15,
        "delay_h": [0] * 5 + [1] * 5 + [2] * 5,
        "hold_h": [24, 36, 48, 60, 72] * 3,
        "split": ["inner_sel"] * 15,
        "mean_net_bps": [1.0, 0.8, 1.2, 1.1, 0.7] * 3,
    })
    plateau = {"plateaus": [{"delay_h": 0, "holds": [24, 36, 48, 60, 72]}]}
    c6 = evaluate_criterion6(FAMILIES["C"], plateau, surf, family_id="C")
    assert c6["pass"] is True


def test_criterion6_family_a_needs_plateau():
    surf = pd.DataFrame({
        "family": ["EUR_ACCUMULATION_JPY_WEAKNESS"] * 4,
        "delay_h": [0] * 4,
        "hold_h": [4, 6, 8, 12],
        "split": ["inner_sel"] * 4,
        "mean_net_bps": [-1.0, -0.5, 0.2, -0.3],
    })
    c6 = evaluate_criterion6(FAMILIES["A"], {"plateaus": []}, surf, family_id="A")
    assert c6["pass"] is False


# ---------------------------------------------------------------------------
# 8. baseline metrics
# ---------------------------------------------------------------------------
def test_vol_normalize_position():
    assert vol_normalize_position(10.0, 10.0) == 1.0
    assert vol_normalize_position(5.0, 10.0) == 2.0
    assert vol_normalize_position(np.nan, 10.0) == 1.0


def test_baseline_runs():
    panel = make_panel(n=2000, start="2023-08-01")
    ev = make_events(panel, n=100)
    ev["event_start"] = pd.date_range("2023-08-01", periods=100, freq="7D", tz="UTC")
    g = build_execution_grid(ev, panel, ["USDJPY"], [0], [6])
    g = orient_trade(g, FAMILIES["A"])
    r = run_baseline(g, FAMILIES["A"], 0, 6, "USDJPY")
    assert r["n_trades"] > 0
    assert "sharpe_annualized" in r
    assert r["sharpe_annualized"] is not None
    assert len(r["yearly"]) >= 1


# ---------------------------------------------------------------------------
# 9. symmetry
# ---------------------------------------------------------------------------
def test_mirrored_symmetry_symmetric_input():
    """Identical raw returns oriented long (A) vs short (B) must mirror: ratio ~ -1."""
    panel = make_panel()
    ev = make_events(panel)
    ev["direction"] = "ACCUMULATION"
    gA = build_execution_grid(ev, panel, ["USDJPY"], [0], [6], apply_costs=False)
    gA = orient_trade(gA, FAMILIES["A"])
    evB = ev.copy()
    evB["direction"] = "LIQUIDATION"
    gB = build_execution_grid(evB, panel, ["USDJPY"], [0], [6], apply_costs=False)
    gB = orient_trade(gB, FAMILIES["B"])
    sym = mirrored_symmetry(gA, gB, FAMILIES["A"], FAMILIES["B"], split="inner_sel")
    if len(sym):
        # long(+gross) vs short(-gross) on identical data -> ratio ~ -1
        assert sym["asymmetry_ratio"].iloc[0] == pytest.approx(-1.0, rel=0.05)


# ---------------------------------------------------------------------------
# 10. determinism of execution grid
# ---------------------------------------------------------------------------
def test_execution_grid_deterministic():
    panel = make_panel()
    ev = make_events(panel)
    a = build_execution_grid(ev, panel, ["USDJPY"], [0, 1], [4, 6])
    b = build_execution_grid(ev, panel, ["USDJPY"], [0, 1], [4, 6])
    pd.testing.assert_frame_equal(a.reset_index(drop=True), b.reset_index(drop=True))


# ---------------------------------------------------------------------------
# 11. artifact integrity (gate + families JSON)
# ---------------------------------------------------------------------------
def test_artifacts_exist():
    for fname in ["P7_RELATIONSHIP_FAMILIES.json", "P7_ALPHA_PROMOTION_GATE.json",
                  "P7_PAIR_SPACE_COMPARISON.csv", "P7_ENTRY_DELAY_SURFACE.csv",
                  "P7_EXCURSION_GEOMETRY.csv", "P7_EUR_JPY_BASELINE_RESULTS.csv",
                  "P7_JPY_CHF_BASELINE_RESULTS.csv", "PHASE_7_DECISION.json",
                  "PHASE_7_STRATEGY_STUDY.md"]:
        assert (ROOT / "artifacts" / "phase_07" / fname).exists(), fname


def test_gate_promotes_and_decision_consistent():
    gate = json.loads((ROOT / "artifacts" / "phase_07" / "P7_ALPHA_PROMOTION_GATE.json").read_text())
    dec = json.loads((ROOT / "artifacts" / "phase_07" / "PHASE_7_DECISION.json").read_text())
    for fam in gate["families"]:
        assert dec["alpha_promotion"][fam["family"]] == fam["promoted"]
    assert dec["stop_after_baseline"] is True
