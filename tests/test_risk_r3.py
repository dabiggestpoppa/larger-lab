"""
CR-RISK-BLOCK1 R3 — Profit Anatomy tests.

Covers: per-trade MFE consistency, positive first-passage times, time-to-MFE
hour conventions, capture ratio bounds, giveback monotonicity, giveback
transitions, remaining-expectancy partition property, state-bin partition,
A/B joins, concurrency joins, episode-rank partition, temporal split labels,
delivery-curve denominator regression (final_net_R must be counted once per
event), and deterministic outputs.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from capital_routing.phases.phase_6_events import (load_frozen_phase3_panel,
                                                   load_frozen_phase5)
from capital_routing.phases.phase_7_5_audit import FROZEN_CONFIGS
from capital_routing.phases.phase_7_execution import build_execution_grid, orient_trade
from capital_routing.phases.phase_7_families import FAMILIES
from capital_routing.phases.phase_r1_heat import build_marks
from capital_routing.phases.phase_r1_ledger import build_ledger
from capital_routing.phases.phase_r2_common import (SPLITS, build_net_paths,
                                                    first_passage_positive,
                                                    per_event_paths)
from capital_routing.phases.phase_r2_context import trade_context
from capital_routing.phases.phase_r3_analysis import (PNL_BUCKET_LABELS,
                                                      capture_ratio,
                                                      giveback_transitions,
                                                      mfe_distributions,
                                                      pnl_bucket_of,
                                                      profit_giveback,
                                                      remaining_expectancy_surface,
                                                      time_to_mfe_table,
                                                      time_to_profit)
from capital_routing.phases.phase_r3_context import (episode_profit_effects,
                                                     profit_delivery_curve,
                                                     temporal_profit_stability)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def r3_base():
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
    return {"ev": ev, "panel": panel, "trades": trades, "grids": grids}


@pytest.fixture(scope="session")
def r3_data(r3_base):
    from capital_routing.phases.phase_r2_analysis import failure_classes
    ledger = build_ledger(r3_base["trades"], r3_base["grids"], r3_base["panel"])
    marks = build_marks(ledger, r3_base["panel"])
    paths = build_net_paths(ledger, marks)
    _, class_frame = failure_classes(ledger, paths)
    ctx = trade_context(ledger, paths, class_frame)
    return {"ledger": ledger, "paths": paths, "ctx": ctx}


# ---------------------------------------------------------------------------
# MFE calculation
# ---------------------------------------------------------------------------

def test_per_trade_mfe_equals_path_max(r3_data):
    ledger = r3_data["ledger"].set_index("event_id")
    per = r3_data["paths"].groupby("event_id")["net_R"].max()
    rng = np.random.default_rng(7)
    for eid in rng.choice(ledger.index, 60, replace=False):
        assert per.loc[eid] == pytest.approx(
            float(r3_data["paths"].groupby("event_id")["net_R"].max().loc[eid]),
            abs=1e-12)
    # MFE in R is never below the final R (running max includes the last bar)
    final = ledger["pnl_bps"] / ledger["risk_unit_bps"]
    mfe = per.reindex(ledger.index)
    assert (mfe >= final - 1e-12).all()


def test_mfe_distribution_grid_complete(r3_data):
    mfe = mfe_distributions(r3_data["ledger"], r3_data["paths"])
    # 3 families x 2 outcomes x 4 units
    assert len(mfe) == 24
    assert set(mfe["family"]) == {"A", "B", "A+B"}
    assert set(mfe["outcome"]) == {"WINNER", "LOSER"}
    assert set(mfe["unit"]) == {"raw_market_bps", "strategy_pnl_bps", "R",
                                "per_volnorm_unit_bps"}
    win = mfe[(mfe["family"] == "A+B") & (mfe["outcome"] == "WINNER")
              & (mfe["unit"] == "R")].iloc[0]
    los = mfe[(mfe["family"] == "A+B") & (mfe["outcome"] == "LOSER")
              & (mfe["unit"] == "R")].iloc[0]
    assert int(win["N"]) == int((r3_data["ledger"]["pnl_bps"] > 0).sum())
    assert int(los["N"]) == int((r3_data["ledger"]["pnl_bps"] <= 0).sum())
    # winners reach materially higher MFE than losers (documented effect)
    assert win["median"] > los["p90"]


# ---------------------------------------------------------------------------
# First passage (positive side)
# ---------------------------------------------------------------------------

def test_first_passage_positive_synthetic():
    path = np.array([0.0, 0.2, 0.6, 0.3, 1.1, 0.8])
    assert first_passage_positive(path, 0.1) == pytest.approx(1.0)
    assert first_passage_positive(path, 0.15) == pytest.approx(1.0)
    assert first_passage_positive(path, 0.25) == pytest.approx(2.0)  # 0.2 < 0.25
    assert first_passage_positive(path, 0.5) == pytest.approx(2.0)
    assert first_passage_positive(path, 1.0) == pytest.approx(4.0)
    assert np.isnan(first_passage_positive(path, 2.0))


def test_time_to_profit_monotonic(r3_data):
    ttp = time_to_profit(r3_data["ledger"], r3_data["paths"])
    for fam in ["A", "B", "A+B"]:
        sub = ttp[ttp["family"] == fam].sort_values("level_R")
        # deeper levels are reached by fewer trades
        assert (np.diff(sub["N_reached_all"].to_numpy()) <= 0).all()
        # after reaching +1R, no trade finishes negative (documented effect)
        r1 = sub[sub["level_R"] == 1.0].iloc[0]
        assert r1["final_loss_probability_after_reaching"] == 0.0
        assert r1["share_of_all_trades_reaching"] < 0.5  # +1R is a minority event


# ---------------------------------------------------------------------------
# R3.1 — time-to-profit metric repair regression
# ---------------------------------------------------------------------------

def test_ttp_all_shares_in_unit_interval(r3_data):
    """Regression: every share/probability in R3_TIME_TO_PROFIT must be in
    [0, 1] - the pre-repair share_of_winners (N_reached_all / N_winners)
    exceeded 1.0 when losers also reached the level."""
    ttp = time_to_profit(r3_data["ledger"], r3_data["paths"])
    for col in ["share_of_all_trades_reaching", "share_of_winners_reaching",
                "share_of_losers_reaching", "final_loss_probability_after_reaching"]:
        v = ttp[col].dropna().to_numpy(dtype=float)
        assert v.size > 0
        assert (v >= 0.0).all() and (v <= 1.0).all()


def test_ttp_numerators_match_populations(r3_data):
    ttp = time_to_profit(r3_data["ledger"], r3_data["paths"])
    for fam in ["A", "B", "A+B"]:
        fam_mask = (r3_data["ledger"]["family"] == fam) if fam != "A+B" \
            else pd.Series(True, index=r3_data["ledger"].index)
        n_fam_win = int((fam_mask & (r3_data["ledger"]["pnl_bps"] > 0)).sum())
        n_fam_los = int((fam_mask & (r3_data["ledger"]["pnl_bps"] <= 0)).sum())
        for _, r in ttp[ttp["family"] == fam].iterrows():
            assert r["N_winners_reached"] <= n_fam_win
            assert r["N_losers_reached"] <= n_fam_los
            # shares use their own population denominators
            if n_fam_win:
                assert r["share_of_winners_reaching"] == pytest.approx(
                    r["N_winners_reached"] / n_fam_win, abs=1e-12)
            if n_fam_los:
                assert r["share_of_losers_reaching"] == pytest.approx(
                    r["N_losers_reached"] / n_fam_los, abs=1e-12)
            # A/B split reconciles to pooled
            if fam == "A+B":
                a = ttp[(ttp["family"] == "A") & (ttp["level_R"] == r["level_R"])].iloc[0]
                b = ttp[(ttp["family"] == "B") & (ttp["level_R"] == r["level_R"])].iloc[0]
                assert r["N_reached_all"] == a["N_reached_all"] + b["N_reached_all"]
                assert r["N_winners_reached"] == a["N_winners_reached"] + b["N_winners_reached"]
                assert r["N_losers_reached"] == a["N_losers_reached"] + b["N_losers_reached"]


def test_ttp_partition_reconciliation(r3_data):
    ttp = time_to_profit(r3_data["ledger"], r3_data["paths"])
    for _, r in ttp.iterrows():
        assert r["N_reached_all"] == r["N_winners_reached"] + r["N_losers_reached"]


def test_ttp_first_passage_times_unchanged(r3_data):
    """The repair must not alter first-passage timestamps: median all-trade
    time equals a direct recomputation from the net-R paths."""
    from capital_routing.phases.phase_r2_common import first_passage_positive
    ev_paths = per_event_paths(r3_data["paths"])
    ledger = r3_data["ledger"].set_index("event_id")
    ttp = time_to_profit(r3_data["ledger"], r3_data["paths"])
    for _, r in ttp.iterrows():
        th = r["level_R"]
        fam_ids = (ledger.index if r["family"] == "A+B"
                   else ledger.index[ledger["family"] == r["family"]])
        times = [first_passage_positive(ev_paths[e], th) for e in fam_ids]
        times = np.array([t for t in times if t is not None and np.isfinite(t)])
        if len(times):
            assert r["median_time_h"] == pytest.approx(np.median(times), abs=1e-12)


def test_time_to_mfe_hour_conventions(r3_data):
    ttm = time_to_mfe_table(r3_data["ledger"], r3_data["paths"])
    all_row = ttm[(ttm["family"] == "A+B") & (ttm["group"] == "all")].iloc[0]
    # hour = argmax index + 1 within the 6-bar path -> 1..6
    assert 1 <= all_row["median_hour"] <= 6
    pct_sum = sum(all_row[f"pct_hour{h}"] for h in [1, 2, 3, 4, 5, 6])
    assert pct_sum == pytest.approx(1.0, abs=1e-9)


def test_time_to_mfe_winner_later_than_loser(r3_data):
    ttm = time_to_mfe_table(r3_data["ledger"], r3_data["paths"])
    w = ttm[(ttm["family"] == "A+B") & (ttm["group"] == "winners")].iloc[0]
    l = ttm[(ttm["family"] == "A+B") & (ttm["group"] == "losers")].iloc[0]
    # winners peak later than losers (documented: winners median hour 5, losers 2)
    assert w["median_hour"] >= l["median_hour"] + 1


# ---------------------------------------------------------------------------
# Capture / giveback
# ---------------------------------------------------------------------------

def test_capture_bounds(r3_data):
    cap = capture_ratio(r3_data["ledger"], r3_data["paths"])
    w = cap[(cap["family"] == "A+B") & (cap["outcome"] == "WINNER")].iloc[0]
    l = cap[(cap["family"] == "A+B") & (cap["outcome"] == "LOSER")].iloc[0]
    # winners: capture in (0, 1] (final <= MFE); losers: <= 0
    assert 0.0 < w["median_capture"] <= 1.0
    assert l["median_capture"] <= 0.0
    assert w["n_no_positive_mfe"] == 0  # every winner had positive MFE
    assert l["n_no_positive_mfe"] > 0


def test_giveback_nonnegative_and_mfe_hour_table(r3_data):
    gb = profit_giveback(r3_data["ledger"], r3_data["paths"])
    win = gb[(gb["family"] == "A+B") & (gb["outcome"] == "WINNER")].iloc[0]
    los = gb[(gb["family"] == "A+B") & (gb["outcome"] == "LOSER")].iloc[0]
    assert win["median_giveback_R"] >= 0.0
    assert los["median_giveback_R"] > win["median_giveback_R"]
    # mfe-hour rows present for all six hours
    for h in [1, 2, 3, 4, 5, 6]:
        rows = gb[(gb["family"] == "A+B") & (gb["outcome"] == f"mfe_hour_{h}")]
        assert len(rows) == 1


def test_giveback_transitions_monotonic(r3_data):
    gbt = giveback_transitions(r3_data["ledger"], r3_data["paths"])
    assert gbt["N_reached"].is_monotonic_decreasing
    # reaching a deeper profit level monotonically lowers failure probability
    assert gbt["p_finish_negative"].is_monotonic_decreasing
    assert gbt["p_finish_positive"].is_monotonic_increasing


# ---------------------------------------------------------------------------
# Remaining expectancy
# ---------------------------------------------------------------------------

def test_state_bin_partition():
    vals = np.array([-5.0, -0.9, -0.6, -0.3, -0.1, 0.1, 0.3, 0.6, 0.9, 5.0])
    labels = pnl_bucket_of(vals)
    assert labels[0] == "< -0.75R"
    assert labels[1] == "< -0.75R"
    assert labels[2] == "-0.75 to -0.50R"
    assert labels[3] == "-0.50 to -0.25R"
    assert labels[4] == "-0.25 to 0R"
    assert labels[5] == "0 to +0.25R"
    assert labels[6] == "+0.25 to +0.50R"
    assert labels[7] == "+0.50 to +0.75R"
    assert labels[8] == "+0.75 to +1.0R"
    assert labels[9] == "> +1.0R"
    assert len(set(labels)) == len(PNL_BUCKET_LABELS)


def test_remaining_expectancy_partition(r3_data):
    """N-weighted cell means must reproduce the unconditional remaining
    expectancy at each age (the state cells partition all events)."""
    res = remaining_expectancy_surface(r3_data["ledger"], r3_data["paths"])
    paths = r3_data["paths"]
    final_sum = paths.drop_duplicates("event_id").set_index("event_id")[
        "final_net_R"]
    for age in [1, 2, 3, 4]:
        cells = res[(res["age_h"] == age) & (res["family"] == "A+B")]
        weighted = float(np.average(cells["remaining_expectancy_R"],
                                    weights=cells["N"]))
        rows = paths[paths["h_since_entry"] == age]
        uncond = float((final_sum.reindex(rows["event_id"]).to_numpy()
                        - rows["net_R"].to_numpy()).mean())
        assert weighted == pytest.approx(uncond, abs=1e-9)
    # at the final bar remaining is exactly 0
    c5 = res[(res["age_h"] == 5) & (res["family"] == "A+B")]
    assert (c5["remaining_expectancy_R"] == 0.0).all()


def test_remaining_expectancy_monotonic_in_state(r3_data):
    res = remaining_expectancy_surface(r3_data["ledger"], r3_data["paths"])
    order = {b: i for i, b in enumerate(PNL_BUCKET_LABELS)}
    for age in [1, 2, 3, 4]:
        cells = res[(res["age_h"] == age) & (res["family"] == "A+B")].copy()
        cells["_ord"] = cells["pnl_bucket"].map(order)
        cells = cells.sort_values("_ord").drop(columns=["_ord"])
        rem = cells["remaining_expectancy_R"].to_numpy()
        # deepest bucket is the worst state and strictly below the bucket above
        assert rem[0] <= rem[1] + 1e-9
        # deepest state is never better than the best state (path-dependence
        # can make the middle non-monotone: recovered-from-loss states differ)
        assert rem[0] <= rem[-1] + 1e-9
        # the deepest state carries negative remaining expectancy by hour 2
        # (the R2 recovery cliff), so its final outlook is a loss
        if age >= 2:
            assert rem[0] <= 0.0


# ---------------------------------------------------------------------------
# Context joins
# ---------------------------------------------------------------------------

def test_episode_ranks_partition_all_events(r3_data):
    ep = episode_profit_effects(r3_data["ledger"], r3_data["paths"])
    for iv in [3.0, 6.0, 12.0]:
        sub = ep[ep["interval_h"] == iv]
        assert int(sub["N"].sum()) == len(r3_data["ledger"])
        assert set(sub["rank_in_cluster"]) == {"1", "2", "3", "4+"}


def test_temporal_labels(r3_data):
    temp = temporal_profit_stability(r3_data["ledger"], r3_data["paths"])
    assert set(temp["split"]) == set(SPLITS)


def test_concurrency_groups_nonempty(r3_data):
    from capital_routing.phases.phase_r3_context import concurrency_profit_effects
    conc = concurrency_profit_effects(r3_data["ledger"], r3_data["paths"],
                                      r3_data["ctx"])
    assert set(conc["group"]) == {"no_overlap", "same_dir_overlap_any",
                                  "opp_dir_overlap_any", "A_A_overlap",
                                  "B_B_overlap", "A_B_overlap"}
    assert (conc["N"] > 0).all()


# ---------------------------------------------------------------------------
# Delivery curve regression
# ---------------------------------------------------------------------------

def test_delivery_curve_final_denominator_once_per_event(r3_data):
    """Regression: final_net_R is repeated once per path bar; the %-final
    column must divide by the per-event (deduplicated) sum. At the frozen
    exit bar the ratio equals (sum of finals of events with a full window) /
    (sum of all finals) - not 6x-inflated, not the count ratio."""
    curve = profit_delivery_curve(r3_data["ledger"], r3_data["paths"])
    paths = r3_data["paths"]
    finals = paths.drop_duplicates("event_id").set_index("event_id")["final_net_R"]
    full = paths[paths["h_since_entry"] == 5].drop_duplicates("event_id")["event_id"]
    expected = finals.reindex(full).sum() / finals.sum()
    h6 = curve[curve["hour"] == 6].iloc[0]
    assert h6["pct_of_final_pnl_achieved"] == pytest.approx(expected, abs=1e-9)
    # the frozen-exit bar carries the largest %-of-final share (truncated
    # events dropping out of later bars can make the raw sum dip mid-hold)
    assert h6["pct_of_final_pnl_achieved"] >= \
        curve["pct_of_final_pnl_achieved"].max() - 1e-9
    # remaining expected gain declines to exactly 0 at the exit bar
    assert h6["remaining_expected_gain_R"] == pytest.approx(0.0, abs=1e-9)


def test_delivery_curve_remaining_matches_partition(r3_data):
    curve = profit_delivery_curve(r3_data["ledger"], r3_data["paths"])
    paths = r3_data["paths"]
    final_sum = paths.drop_duplicates("event_id")["final_net_R"].sum()
    for _, r in curve.iterrows():
        rows = paths[paths["h_since_entry"] == int(r["hour"]) - 1]
        expected = rows["net_R"].sum() / final_sum
        assert r["pct_of_final_pnl_achieved"] == pytest.approx(expected,
                                                               abs=1e-9)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_outputs_deterministic(r3_data):
    a = profit_delivery_curve(r3_data["ledger"], r3_data["paths"])
    b = profit_delivery_curve(r3_data["ledger"], r3_data["paths"])
    assert a.equals(b)
    t1 = time_to_profit(r3_data["ledger"], r3_data["paths"])
    t2 = time_to_profit(r3_data["ledger"], r3_data["paths"])
    assert t1.equals(t2)


def test_time_to_profit_uses_only_past_state(r3_data):
    """First-passage time is defined by path prefix only: truncating the path
    at the breach bar must not change the reported time."""
    ev_paths = per_event_paths(r3_data["paths"])
    eid = r3_data["ledger"]["event_id"].iloc[0]
    path = ev_paths[eid]
    t = first_passage_positive(path, 0.5)
    if not np.isnan(t):
        truncated = path[:int(t) + 1]
        assert first_passage_positive(truncated, 0.5) == pytest.approx(t)
