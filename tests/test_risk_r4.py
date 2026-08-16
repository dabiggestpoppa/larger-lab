"""
CR-RISK-BLOCK1 R4 — Static Risk Frontier tests.

Covers: multiplicative compounding, R->equity mapping (no -1R cap assumption),
drawdown math, block-bootstrap determinism, ruin threshold counts, edge-shrink
logic, tail amplification, loss-streak stress, account-dollar translation,
hourly-grid overlap conservation, and deterministic outputs.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _book_rR() -> np.ndarray:
    """Synthetic deterministic trade book for pure-logic tests."""
    return np.array([1.0, -0.5, 0.3, -2.0, 0.8, -0.4, 1.5, -1.0, 0.2, -0.1],
                    dtype=float)


# ---------------------------------------------------------------------------
# Compounding + R->equity mapping
# ---------------------------------------------------------------------------

def test_sequential_compounding_multiplicative():
    from capital_routing.phases.phase_r4_common import sequential_equity
    r = _book_rR()
    f = 0.01
    eq = sequential_equity(r, f)
    # multiplicative: E_t = prod(1 + f*r_i)
    expected = np.concatenate([[1.0], np.cumprod(1.0 + f * r)])
    np.testing.assert_allclose(eq, expected, rtol=1e-12)
    # not additive: E != 1 + f*sum(r)
    assert eq[-1] != pytest.approx(1.0 + f * r.sum())


def test_r_maps_directly_to_equity_no_cap():
    """A -3R trade at f=1% must cost ~3% - 1R is NOT a max loss."""
    from capital_routing.phases.phase_r4_common import sequential_equity
    eq = sequential_equity(np.array([-3.0]), 0.01)
    assert eq[-1] == pytest.approx(0.97)
    eq2 = sequential_equity(np.array([-3.66]), 0.01)
    assert eq2[-1] == pytest.approx(1 - 0.0366)
    # f=5% with the A-worst -3.66R trade
    eq3 = sequential_equity(np.array([-3.66]), 0.05)
    assert eq3[-1] == pytest.approx(1 - 0.05 * 3.66)


def test_large_r_can_ruin_at_high_f():
    """Technical ruin (equity <= 0) is reachable when f*r <= -1."""
    from capital_routing.phases.phase_r4_common import sequential_equity
    eq = sequential_equity(np.array([-20.0]), 0.10)
    assert eq[-1] <= 0.0


# ---------------------------------------------------------------------------
# Drawdown math
# ---------------------------------------------------------------------------

def test_max_dd_calculation():
    from capital_routing.phases.phase_r4_common import _max_dd
    # equity: 1.0 -> 1.2 -> 0.9 -> 1.1 -> 0.8 -> 1.3
    eq = np.array([1.0, 1.2, 0.9, 1.1, 0.8, 1.3])
    # peak 1.2 -> trough 0.8 = 33.3%
    assert _max_dd(eq) == pytest.approx((1.2 - 0.8) / 1.2, abs=1e-9)
    assert _max_dd(np.array([1.0, 1.1, 1.2])) == 0.0
    assert _max_dd(np.array([1.0, 0.5])) == pytest.approx(0.5)


def test_drawdown_uses_peak_not_start():
    """DD is peak-to-trough: an equity above start but below its own peak
    still counts as drawdown."""
    from capital_routing.phases.phase_r4_common import equity_metrics
    # start 1.0, run up to 2.0, fall to 1.5 -> 25% DD from the 2.0 peak
    eq = np.array([1.0, 1.5, 2.0, 1.5, 1.6])
    m = equity_metrics(eq, years=1.0, hourly=True)
    assert m["max_dd"] == pytest.approx(0.25, abs=1e-9)
    # terminal equity 1.6 -> total return 60%
    assert m["total_return"] == pytest.approx(0.6, abs=1e-9)


# ---------------------------------------------------------------------------
# Hourly grid conserves the sealed book total
# ---------------------------------------------------------------------------

def test_hourly_grid_conserves_pnl(r2_data_for_r4):
    from capital_routing.phases.phase_r4_common import hourly_grid
    g = hourly_grid(r2_data_for_r4["ledger"], r2_data_for_r4["paths"])
    total_ledger = float(r2_data_for_r4["ledger"]["pnl_bps"].sum())
    assert g["net_bps"].sum() == pytest.approx(total_ledger, abs=1e-6)
    assert g["r_h"].notna().all()
    assert (g.index == g.index.round("h")).all()


# ---------------------------------------------------------------------------
# Ladder basics
# ---------------------------------------------------------------------------

def test_ladder_metrics_are_consistent(r2_data_for_r4):
    from capital_routing.phases.phase_r4_ladder import run_ladder
    l = run_ladder(r2_data_for_r4["ledger"], r2_data_for_r4["paths"])
    assert len(l) == 18
    # CAGR > 0 at every fraction (sealed edge is positive)
    assert (l["cagr"] > 0).all()
    # max DD is non-decreasing in f
    assert l["max_dd"].is_monotonic_increasing
    # at f=1%, the worst single trade costs at least its R x f
    assert l[l["f_pct"] == 1.0]["worst_trade_pct"].iloc[0] <= -0.036
    # worst cluster loss is negative and deeper than the worst single trade
    r1 = l[l["f_pct"] == 1.0].iloc[0]
    assert r1["worst_cluster_pct"] < r1["worst_trade_pct"]


def test_ladder_sequential_vs_hourly_close(r2_data_for_r4):
    """Sequential and overlap-exact CAGR agree within a small band (overlap is
    a second-order effect on returns)."""
    from capital_routing.phases.phase_r4_ladder import (run_ladder,
                                                        run_sequential_ladder)
    h = run_ladder(r2_data_for_r4["ledger"], r2_data_for_r4["paths"])
    s = run_sequential_ladder(r2_data_for_r4["ledger"])
    merged = h.merge(s, on="f_pct", suffixes=("_h", "_s"))
    merged = merged[merged["f_pct"] <= 1.5]
    ratio = (merged["cagr_h"] / merged["cagr_s"]).to_numpy()
    # at moderate f the overlap-exact hourly path tracks the sequential path
    assert np.all(np.abs(ratio - 1.0) < 0.05)


# ---------------------------------------------------------------------------
# MC determinism + ruin thresholds
# ---------------------------------------------------------------------------

def test_mc_deterministic(r2_data_for_r4):
    from capital_routing.phases.phase_r4_mc import monte_carlo_frontier
    a = monte_carlo_frontier(r2_data_for_r4["ledger"], n_paths=200)
    b = monte_carlo_frontier(r2_data_for_r4["ledger"], n_paths=200)
    assert a.equals(b)


def test_mc_schemes_present(r2_data_for_r4):
    from capital_routing.phases.phase_r4_mc import monte_carlo_frontier
    mc = monte_carlo_frontier(r2_data_for_r4["ledger"], n_paths=200)
    assert set(mc["scheme"]) == {"iid", "block", "episode"}
    assert set(mc["f_pct"]) == set(
        [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.75, 1.0,
         1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0])


def test_ruin_probabilities_in_unit_interval(r2_data_for_r4):
    from capital_routing.phases.phase_r4_mc import monte_carlo_frontier
    mc = monte_carlo_frontier(r2_data_for_r4["ledger"], n_paths=200)
    for col in ["P_dd_ge_10", "P_dd_ge_20", "P_dd_ge_30", "P_dd_ge_40",
                "P_dd_ge_50", "P_technical_ruin"]:
        v = mc[col].to_numpy()
        assert (v >= 0.0).all() and (v <= 1.0).all()
    # DD probabilities are monotone in threshold at fixed f
    for f_ in [1.0, 5.0]:
        sub = mc[(mc["scheme"] == "block") & (mc["f_pct"] == f_)]
        row = sub.iloc[0]
        assert row["P_dd_ge_10"] >= row["P_dd_ge_20"] >= row["P_dd_ge_30"] \
            >= row["P_dd_ge_40"] >= row["P_dd_ge_50"]


# ---------------------------------------------------------------------------
# Edge-shrink / tail / streak logic
# ---------------------------------------------------------------------------

def test_edge_shrink_preserves_losses():
    from capital_routing.phases.phase_r4_stress import _edge_shrink
    r = np.array([2.0, -1.0, 0.5, -3.0])
    e075 = _edge_shrink(r, 0.75)
    # losses untouched, wins scaled
    assert e075[1] == -1.0 and e075[3] == -3.0
    assert e075[0] == pytest.approx(1.5) and e075[2] == pytest.approx(0.375)
    e025 = _edge_shrink(r, 0.25)
    assert e025[0] == pytest.approx(0.5)
    # mean is monotone in edge
    assert _edge_shrink(r, 1.0).mean() > e075.mean() > e025.mean()


def test_tail_stress_winners_untouched():
    from capital_routing.phases.phase_r4_stress import _worst5_mask, tail_stress
    r = np.array([-0.1, -0.2, -0.05, -3.0, -0.3, 1.0, 0.5, -1.0, -0.4])
    mask = _worst5_mask(r)
    # the worst 5% of LOSSES are flagged, winners never
    assert not mask[5] and not mask[6]
    assert mask[3]  # -3.0 is the deepest loss
    assert mask.sum() >= 1


def test_streak_stress_math():
    from capital_routing.phases.phase_r4_stress import loss_streak_stress
    # synthetic ledger: 10 trades, one clear loser
    led = pd.DataFrame({
        "pnl_bps": [100.0] * 9 + [-100.0],
        "risk_unit_bps": [24.49489742783178] * 10,
    })
    s = loss_streak_stress(led)
    # loser_R equals the single loser's R
    row = s[(s["f_pct"] == 1.0) & (s["streak_len"] == 5)
            & (s["loser_quantile"] == 0.5)].iloc[0]
    assert row["loser_R"] == pytest.approx(-4.0825, abs=1e-3)
    # drawdown from a 10-streak at f=5%: 1 - (1 + 0.05*loser)^10
    row10 = s[(s["f_pct"] == 5.0) & (s["streak_len"] == 10)
              & (s["loser_quantile"] == 0.5)].iloc[0]
    assert row10["drawdown_pct"] == pytest.approx(
        1.0 - (1.0 + 0.05 * row10["loser_R"]) ** 10, abs=1e-9)
    # deeper streaks always hurt more at fixed f
    dd = s[(s["f_pct"] == 1.0) & (s["loser_quantile"] == 0.5)] \
        .sort_values("streak_len")["drawdown_pct"].to_numpy()
    assert np.all(np.diff(dd) >= 0)


# ---------------------------------------------------------------------------
# Account translation
# ---------------------------------------------------------------------------

def test_account_translation_dollars():
    from capital_routing.phases.phase_r4_profiles import account_translation
    zones = pd.DataFrame([{"zone": "RM-S2_BALANCED", "f_pct": 1.0}])
    led = pd.DataFrame({
        "pnl_bps": [-100.0, 100.0],  # A holds the losing trade
        "risk_unit_bps": [24.49489742783178] * 2,
        "family": ["A", "B"],
    })
    t = account_translation(zones, led)
    row = t[(t["account_usd"] == 10000.0)].iloc[0]
    assert row["dollar_1R"] == pytest.approx(100.0)
    assert row["impact_minus_1R"] == pytest.approx(-100.0)
    assert row["impact_minus_3R"] == pytest.approx(-300.0)
    # A-worst = min A R x 1R dollars = -100/24.49 x 100
    assert row["impact_A_worst_minus_3_66R"] == pytest.approx(
        -100.0 / 24.49489742783178 * 100.0, abs=1e-6)
    # expected gain = mean R x 1R dollars (0 here: one +100, one -100)
    assert row["expected_event_gain"] == pytest.approx(0.0, abs=1e-6)


# ---------------------------------------------------------------------------
# Fixture reuse
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def r2_data_for_r4():
    from capital_routing.phases.phase_6_events import (load_frozen_phase3_panel,
                                                       load_frozen_phase5)
    from capital_routing.phases.phase_7_5_audit import FROZEN_CONFIGS, OOS_LABEL
    from capital_routing.phases.phase_7_execution import (build_execution_grid,
                                                          orient_trade)
    from capital_routing.phases.phase_7_families import FAMILIES
    from capital_routing.phases.phase_r1_heat import build_marks
    from capital_routing.phases.phase_r1_ledger import build_ledger
    from capital_routing.phases.phase_r2_common import build_net_paths
    ev = load_frozen_phase5(ROOT / "artifacts" / "phase_05")["routing_events.parquet"]
    panel = load_frozen_phase3_panel(ROOT / "artifacts" / "phase_03")
    trades = pd.read_csv(ROOT / "artifacts" / "phase_07_5" / "P7_5_TRADES.csv")
    trades["entry_ts"] = pd.to_datetime(trades["entry_ts"], utc=True)
    trades["exit_ts"] = pd.to_datetime(trades["exit_ts"], utc=True)
    grids = {}
    for fid in ["A", "B"]:
        fam = FAMILIES[fid]
        fam_events = ev[(ev["origin_currency"] == fam["origin"])
                        & (ev["direction"] == fam["direction"])]
        cfg = FROZEN_CONFIGS[fid]
        g = build_execution_grid(fam_events, panel, [cfg["pair"]],
                                 [cfg["delay_h"]], [cfg["hold_h"]])
        grids[fid] = orient_trade(g, fam)
    ledger = build_ledger(trades, grids, panel)
    marks = build_marks(ledger, panel)
    paths = build_net_paths(ledger, marks)
    return {"ledger": ledger, "paths": paths, "marks": marks}
