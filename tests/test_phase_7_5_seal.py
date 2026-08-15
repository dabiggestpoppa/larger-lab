"""
Phase 7.5 tests (CR-P7.5-ROUTING-BASELINE-SEAL-01).

Covers: validation label repair, selection discipline, metric unit
consistency (drawdown/Calmar), chronological equity ordering, policy
comparability (per-raw-event expectancy), cost stress break-even, bootstrap
determinism, and forward-OOS status.
"""
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from capital_routing.phases.phase_7_5_audit import (
    CAPITAL_BASE_BPS,
    FROZEN_CONFIGS,
    OOS_LABEL,
    chronological_equity,
    metric_units,
    rename_split_labels,
    write_selection_discipline,
)
from capital_routing.phases.phase_7_5_bootstrap import (
    block_bootstrap,
    cluster_ids,
    loss_streaks,
    monte_carlo_drawdown,
)
from capital_routing.phases.phase_7_5_cost_stress import stress_costs
from capital_routing.phases.phase_7_5_portfolio import (
    build_trades,
    concurrency_analysis,
    policy_comparison,
    run_policy,
)


@pytest.fixture(scope="module")
def trades():
    """Real trades frame from the frozen run."""
    df = pd.read_csv(ROOT / "artifacts" / "phase_07_5" / "P7_5_TRADES.csv",
                     parse_dates=["entry_ts", "exit_ts"])
    return df


# ---------------------------------------------------------------------------
# 1. validation label
# ---------------------------------------------------------------------------
def test_rename_split_labels():
    df = pd.DataFrame({"split": ["inner_sel", "untouched"], "x": [1, 2]})
    out = rename_split_labels(df)
    assert set(out["split"]) == {"inner_sel", OOS_LABEL}
    assert "untouched" not in set(out["split"])


def test_oos_label_is_relationship_confirmed():
    assert OOS_LABEL == "RELATIONSHIP_CONFIRMED_OOS"


# ---------------------------------------------------------------------------
# 2. selection discipline
# ---------------------------------------------------------------------------
def test_frozen_configs_match_brief():
    assert FROZEN_CONFIGS["A"]["pair"] == "USDJPY"
    assert FROZEN_CONFIGS["A"]["delay_h"] == 2
    assert FROZEN_CONFIGS["A"]["hold_h"] == 6
    assert FROZEN_CONFIGS["B"]["pair"] == "USDJPY"
    assert FROZEN_CONFIGS["B"]["delay_h"] == 1
    assert FROZEN_CONFIGS["B"]["hold_h"] == 6


def test_selection_discipline_audit_passes(tmp_path):
    surf = pd.read_csv(ROOT / "artifacts" / "phase_07" / "P7_ENTRY_DELAY_SURFACE.csv")
    audit = write_selection_discipline(tmp_path, surf, {})
    assert audit["all_frozen_configs_disciplined"] is True
    assert audit["oos_not_used_in_selection"] is True
    for fid in ["A", "B"]:
        fam = audit["families"][fid]
        assert fam["positive_inner_sel"] and fam["positive_inner_val"]
        assert fam["same_sign"] and fam["on_plateau"]
        assert fam["hold_in_validated_envelope"]


# ---------------------------------------------------------------------------
# 3. metric units
# ---------------------------------------------------------------------------
def test_drawdown_units_consistent():
    rng = np.random.default_rng(3)
    pnl = rng.normal(5, 40, 300)
    ts = pd.date_range("2024-01-01", periods=300, freq="D")
    eq = chronological_equity(pnl, ts)
    # drawdown_bps = peak - equity (bps units)
    assert np.allclose(eq["drawdown_bps"], eq["peak_equity_bps"] - eq["equity_bps"])
    # ratio in [0, 1)
    assert eq["drawdown_ratio"].min() >= 0
    assert eq["drawdown_ratio"].max() < 1
    mu = metric_units(eq, 200.0)
    # annualized decimal = mean_bps/10000 * tpy
    assert mu["annualized_return_decimal"] == pytest.approx(
        eq["pnl_bps"].mean() / 10000.0 * 200.0)
    # Calmar = decimal ann ret / max DD ratio
    assert mu["calmar"] == pytest.approx(
        mu["annualized_return_decimal"] / mu["max_drawdown_ratio"])


def test_calmar_unit_mismatch_detected():
    """Calmar from bps vs decimal must differ by exactly /10000."""
    rng = np.random.default_rng(5)
    pnl = rng.normal(4, 30, 200)
    ts = pd.date_range("2024-06-01", periods=200, freq="D")
    eq = chronological_equity(pnl, ts)
    mu = metric_units(eq, 250.0)
    max_dd_ratio = mu["max_drawdown_ratio"]
    bps_calmar = mu["annualized_return_decimal"] * 10000 / max_dd_ratio
    assert mu["calmar"] == pytest.approx(bps_calmar / 10000.0)


def test_equity_chronological():
    rng = np.random.default_rng(7)
    pnl = rng.normal(3, 20, 100)
    ts = pd.date_range("2024-01-01", periods=100, freq="D")
    ordered = chronological_equity(pnl, ts)
    # shuffled input must give same result (function sorts by ts)
    perm = rng.permutation(100)
    shuffled = chronological_equity(pnl[perm], ts[perm])
    pd.testing.assert_series_equal(
        ordered["equity_bps"], shuffled["equity_bps"])


def test_drawdown_ratio_bounded_with_capital_base():
    """Even a deep drawdown must stay in [0,1) given the 10000 bps base."""
    pnl = np.array([100.0, -1000.0, -500.0, 800.0])
    ts = pd.date_range("2024-01-01", periods=4, freq="D")
    eq = chronological_equity(pnl, ts)
    assert eq["drawdown_ratio"].max() < 1.0
    assert CAPITAL_BASE_BPS == 10000.0


# ---------------------------------------------------------------------------
# 4. portfolio / policies
# ---------------------------------------------------------------------------
def test_policy_comparison_comparable(trades):
    comp = policy_comparison(trades)
    # per-raw-event expectancy must be identical for P0 and P2 (same harvest)
    p0 = comp[comp["policy"] == "P0"].iloc[0]
    p2 = comp[comp["policy"] == "P2"].iloc[0]
    assert p0["expectancy_per_raw_event_bps"] == pytest.approx(
        p2["expectancy_per_raw_event_bps"])
    assert p0["total_return_bps"] == pytest.approx(p2["total_return_bps"])
    # P2 must have fewer positions than raw events
    assert p2["n_positions"] < p2["n_raw_events"]


def test_p2_books_at_exit(trades):
    dev = trades[trades["split"].isin(["inner_sel", "inner_val"])]
    out = run_policy(dev, "P2")
    if len(out):
        # merged rows book at exit_ts
        assert (out["book_ts"] == out["exit_ts"]).all()
        assert "n_raw_merged" in out.columns
        assert (out["n_raw_merged"] >= 1).all()


def test_p1_skip_overlap(trades):
    dev = trades[trades["split"].isin(["inner_sel", "inner_val"])]
    out = run_policy(dev, "P1")
    # no overlapping positions: next entry >= previous exit
    entries = pd.to_datetime(out["entry_ts"]).sort_values()
    exits = out.loc[entries.index, "exit_ts"]
    prev_exit = None
    for _, row in out.sort_values("entry_ts").iterrows():
        if prev_exit is not None:
            assert row["entry_ts"] >= prev_exit
        prev_exit = row["exit_ts"]


def test_concurrency_counts(trades):
    conc = concurrency_analysis(trades)
    s = conc.attrs["summary"]
    assert s["n_raw_events"] == len(trades)
    assert s["max_concurrent_positions"] >= 1
    # gross >= |net| always
    assert (conc["gross_exposure"] >= conc["net_exposure"].abs()).all()
    assert (conc["n_active"] == conc["long_count"] + conc["short_count"]).all()


# ---------------------------------------------------------------------------
# 5. cost stress
# ---------------------------------------------------------------------------
def test_cost_stress_monotone(trades):
    cs = stress_costs(trades)
    for grp in ["A", "B", "A+B"]:
        sub = cs[cs["group"] == grp].sort_values("cost_multiplier")
        expect = sub["expectancy_bps"].to_numpy()
        assert np.all(np.diff(expect) < 0), f"{grp} expectancy not monotone in cost"
        assert sub["break_even_multiplier"].iloc[0] >= 1.0


# ---------------------------------------------------------------------------
# 6. forward OOS
# ---------------------------------------------------------------------------
def test_forward_oos_pending():
    fwd = pd.read_csv(ROOT / "artifacts" / "phase_07_5" / "P7_5_FORWARD_OOS.csv")
    assert fwd["status"].iloc[0] == "FORWARD_OOS_PENDING"
    assert fwd["n_events"].iloc[0] == 0


# ---------------------------------------------------------------------------
# 7. bootstrap
# ---------------------------------------------------------------------------
def test_bootstrap_deterministic():
    rng = np.random.default_rng(11)
    pnl = rng.normal(2, 25, 300)
    ts = pd.date_range("2024-01-01", periods=300, freq="4h")
    a = block_bootstrap(pnl, ts.to_numpy())
    b = block_bootstrap(pnl, ts.to_numpy())
    assert a["expectancy_ci_low"] == b["expectancy_ci_low"]
    assert a["expectancy_ci_high"] == b["expectancy_ci_high"]


def test_cluster_ids():
    ts = pd.to_datetime(
        ["2024-01-01 00:00", "2024-01-01 05:00", "2024-01-03 00:00"], utc=True)
    c = cluster_ids(ts.astype("int64").to_numpy(), window_h=24)
    assert c[0] == c[1] != c[2]


def test_loss_streaks():
    ls = loss_streaks(np.array([-1.0, -2.0, 1.0, -3.0, -1.0, -0.5, 2.0]))
    assert ls["max_loss_streak"] == 3
    assert ls["n_loss_streaks"] == 2


def test_mc_drawdown_deterministic():
    rng = np.random.default_rng(13)
    pnl = rng.normal(2, 30, 150)
    a = monte_carlo_drawdown(pnl, n_perm=200)
    b = monte_carlo_drawdown(pnl, n_perm=200)
    assert a["mc_max_dd_median"] == b["mc_max_dd_median"]


# ---------------------------------------------------------------------------
# 8. artifact integrity
# ---------------------------------------------------------------------------
def test_artifacts_exist():
    for fname in ["P7_5_VALIDATION_LABEL_AUDIT.md", "P7_5_SELECTION_DISCIPLINE.json",
                  "P7_5_METRIC_UNIT_AUDIT.md", "P7_5_AB_PORTFOLIO_RESULTS.csv",
                  "P7_5_CONCURRENCY_ANALYSIS.csv", "P7_5_COST_STRESS.csv",
                  "P7_5_FORWARD_OOS.csv", "P7_5_BOOTSTRAP_ROBUSTNESS.csv",
                  "P7_5_BASELINE_SEAL.md", "P7_5_DECISION.json"]:
        assert (ROOT / "artifacts" / "phase_07_5" / fname).exists(), fname


def test_seal_verdicts():
    dec = json.loads((ROOT / "artifacts" / "phase_07_5" / "P7_5_DECISION.json").read_text())
    assert dec["accept"]["A"] == "STRONG"
    assert dec["accept"]["B"] == "STRONG"
    assert dec["family_C"] == "WATCHLIST"
    assert dec["forward_oos"] == "PENDING"
    assert "CEREBUS" not in dec["stop"] or dec["stop"].startswith("baseline sealed")
