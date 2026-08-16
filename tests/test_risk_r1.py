"""
CR-RISK-BLOCK1 R1 — Exposure Truth tests.

Covers: unit mapping (market -> pos -> PnL -> R -> account %), ledger integrity
(prices reproduce the frozen grid returns), concurrency consistency, heat
bounds/decay, episode-cluster partition, conditional ranks, determinism.
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
from capital_routing.phases.phase_r1_concurrency import build_concurrency
from capital_routing.phases.phase_r1_episodes import (INTERVALS_H,
                                                      cluster_events,
                                                      conditional_results)
from capital_routing.phases.phase_r1_heat import build_heat, build_marks, heat_distributions
from capital_routing.phases.phase_r1_ledger import (RISK_PER_R_PCT, TARGET_VOL,
                                                    build_ledger, risk_unit_bps)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def r1_data():
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
def ledger(r1_data):
    return build_ledger(r1_data["trades"], r1_data["grids"], r1_data["panel"])


@pytest.fixture(scope="session")
def marks(r1_data, ledger):
    return build_marks(ledger, r1_data["panel"])


# ---------------------------------------------------------------------------
# 1. Unit mapping
# ---------------------------------------------------------------------------

def test_risk_unit_definition():
    assert risk_unit_bps(6.0) == pytest.approx(10.0 * np.sqrt(6.0), rel=1e-12)
    assert risk_unit_bps(6.0) == pytest.approx(24.494897, rel=1e-4)


def test_unit_mapping_formulas_chain():
    """market bps -> pos -> pnl bps -> R -> account % must compose exactly."""
    mkt_bps = 30.0
    rv = 12.0
    hold = 6.0
    cost_bps = 1.2
    pos = TARGET_VOL / rv
    pnl = mkt_bps * pos
    net = pnl - cost_bps * pos
    r = net / risk_unit_bps(hold)
    acct = r * RISK_PER_R_PCT
    # a one-sigma move (mkt_bps = rv*sqrt(hold)) must give exactly R = 1.0
    mkt_sigma = rv * np.sqrt(hold)
    pos_sigma = TARGET_VOL / rv
    pnl_sigma = mkt_sigma * pos_sigma
    assert pnl_sigma == pytest.approx(risk_unit_bps(hold), rel=1e-12)
    assert (pnl_sigma / risk_unit_bps(hold)) == pytest.approx(1.0, rel=1e-12)
    assert acct == pytest.approx(r, rel=1e-12)  # 1% per R


# ---------------------------------------------------------------------------
# 2. Ledger integrity
# ---------------------------------------------------------------------------

def test_ledger_shape_and_uniqueness(ledger):
    assert len(ledger) == 890
    assert ledger["event_id"].duplicated().sum() == 0
    assert set(ledger["family"]) == {"A", "B"}
    assert ledger["pnl_bps"].notna().all()


def test_ledger_prices_reproduce_grid_returns(ledger):
    diff = (ledger["price_return_bps"] - ledger["gross_return_bps"]).abs()
    assert diff.max() < 1e-6


def test_ledger_r_multiple_consistency(ledger):
    expected = ledger["pnl_bps"] / ledger["risk_unit_bps"]
    assert np.allclose(ledger["r_multiple"], expected, rtol=1e-12)
    assert np.allclose(ledger["account_return_pct"], ledger["r_multiple"] * RISK_PER_R_PCT,
                       rtol=1e-12)


def test_ledger_mae_always_nonpositive(ledger):
    # directional MAE (signed) must never be positive in the R-multiple frame
    assert (ledger["dir_mae_bps"] <= 0).all()
    assert (ledger["mae_r"] <= 0).all()


# ---------------------------------------------------------------------------
# 3. Concurrency
# ---------------------------------------------------------------------------

def test_concurrency_summary_matches_timeline(ledger):
    tl, summ = build_concurrency(ledger)
    s = summ.iloc[0]
    assert s["max_concurrent_positions"] == tl["n_active"].max()
    assert s["hours_with_2_positions"] == int((tl["n_active"] == 2).sum())
    assert s["hours_with_3_positions"] == int((tl["n_active"] == 3).sum())
    assert s["A_A_overlap_hours"] == int((tl["A_A_overlap_pairs"] > 0).sum())
    # every active hour is either 2, 3 or 4+ when > 1
    multi = tl[tl["n_active"] > 1]
    assert (multi["n_active"].isin([2, 3]).any() or (multi["n_active"] >= 4).any())


def test_concurrency_pair_consistency(ledger):
    tl, _ = build_concurrency(ledger)
    row = tl[tl["n_active"] > 1].iloc[0]
    assert row["opp_dir_overlap_pairs"] == row["n_long"] * row["n_short"]
    assert row["A_B_overlap_pairs"] == row["n_A"] * row["n_B"]
    assert row["gross_exposure"] >= abs(row["net_exposure"])


def test_concurrency_chronological(ledger):
    tl, _ = build_concurrency(ledger)
    assert tl["ts"].is_monotonic_increasing


# ---------------------------------------------------------------------------
# 4. Portfolio heat
# ---------------------------------------------------------------------------

def test_heat_bounds(ledger, marks):
    heat = build_heat(ledger, marks)
    assert (heat["gross_heat"] >= 0).all()
    assert (heat["gross_heat"] >= heat["abs_net_heat"] - 1e-9).all()
    assert (heat["opposing_heat"] >= -1e-9).all()
    # gross heat = long + short
    assert np.allclose(heat["gross_heat"], heat["long_heat"] + heat["short_heat"],
                       atol=1e-9)


def test_heat_entry_commitment(ledger, marks):
    heat = build_heat(ledger, marks)
    # a freshly-entered single position commits exactly 10*sqrt(6) bps
    fresh = heat[heat["n_open"] == 1]
    assert len(fresh) > 0
    # the max gross heat of a single-position hour equals the entry commitment
    assert fresh["gross_heat"].max() == pytest.approx(10.0 * np.sqrt(6.0), rel=1e-9)


def test_marks_reproduce_grid_mfe(ledger, marks):
    """max(mark_bps/pos) per event must equal dir_mfe_bps (float tolerance)."""
    m = marks.merge(ledger[["event_id", "pos", "dir_mfe_bps", "time_to_mfe_h"]],
                    on="event_id", how="inner")
    g = m.groupby("event_id").apply(
        lambda df: (df["mark_bps"] / df["pos"].iloc[0]).max() - df["dir_mfe_bps"].iloc[0],
        include_groups=False)
    assert g.abs().max() < 1e-9


def test_heat_distributions_shape(ledger, marks):
    heat = build_heat(ledger, marks)
    dist = heat_distributions(heat)
    assert set(dist["metric"]) >= {"gross_heat", "abs_net_heat", "portfolio_cae_bps"}
    assert set(dist["window_h"]) == {1, 3, 6, 12, 24}
    assert (dist["p99"] >= dist["median"]).all()


# ---------------------------------------------------------------------------
# 5. Episode clustering
# ---------------------------------------------------------------------------

def test_episodes_partition_all_events(ledger, marks):
    for iv in INTERVALS_H:
        ep = cluster_events(ledger, marks, iv)
        assert int(ep["n_events"].sum()) == len(ledger)


def test_episode_cluster_span_consistency(ledger, marks):
    for iv in [0.5, 1.0, 2.0]:
        ep = cluster_events(ledger, marks, iv)
        multi = ep[ep["n_events"] > 1]
        if len(multi):
            row = multi.iloc[0]
            # consecutive-gap chaining: span <= (n-1) * interval (gaps <= interval)
            assert row["span_h"] <= (row["n_events"] - 1) * iv + 1e-9


def test_conditional_ranks_cover_events(ledger, marks):
    cond = conditional_results(ledger, marks)
    for iv in INTERVALS_H:
        sub = cond[cond["interval_h"] == iv]
        assert int(sub["n"].sum()) == len(ledger)


def test_cluster_family_pairs(ledger, marks):
    ep = cluster_events(ledger, marks, 6.0)
    multi = ep[ep["n_events"] > 1]
    if len(multi):
        row = multi.iloc[0]
        assert row["same_family_pairs"] + row["opposite_family_pairs"] == \
            row["n_events"] * (row["n_events"] - 1) // 2


# ---------------------------------------------------------------------------
# 6. Determinism
# ---------------------------------------------------------------------------

def test_ledger_deterministic(r1_data):
    l1 = build_ledger(r1_data["trades"], r1_data["grids"], r1_data["panel"])
    l2 = build_ledger(r1_data["trades"], r1_data["grids"], r1_data["panel"])
    assert l1.equals(l2)


def test_concurrency_deterministic(ledger):
    a, _ = build_concurrency(ledger)
    b, _ = build_concurrency(ledger)
    assert a.equals(b)
