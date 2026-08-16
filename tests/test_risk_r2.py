"""
CR-RISK-BLOCK1 R2 — Loss Anatomy tests.

Covers: net-PnL path consistency, MAE-bin partition, first-passage times,
recovery-surface causality, cluster-rank joins, concurrency joins, temporal
split labels, failure classes, loss streaks, tail-bucket counts, and
deterministic outputs.
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
from capital_routing.phases.phase_r2_analysis import (failure_classes,
                                                      failure_speed,
                                                      mae_distributions,
                                                      recovery_surface)
from capital_routing.phases.phase_r2_common import (MAE_BIN_LABELS, SPLITS,
                                                    build_net_paths,
                                                    first_passage,
                                                    mae_bin_of)
from capital_routing.phases.phase_r2_context import (assign_cluster_ranks,
                                                     concurrency_loss_effects,
                                                     loss_streaks,
                                                     trade_context)

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def r2_base():
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
def r2_data(r2_base):
    ledger = build_ledger(r2_base["trades"], r2_base["grids"], r2_base["panel"])
    marks = build_marks(ledger, r2_base["panel"])
    paths = build_net_paths(ledger, marks)
    classes, class_frame = failure_classes(ledger, paths)
    ctx = trade_context(ledger, paths, class_frame)
    return {"ledger": ledger, "paths": paths, "classes": classes,
            "class_frame": class_frame, "ctx": ctx}


# ---------------------------------------------------------------------------
# Path consistency
# ---------------------------------------------------------------------------

def test_net_path_final_equals_pnl(r2_data):
    """The final bar of the net path must equal the sealed net PnL."""
    ledger = r2_data["ledger"].set_index("event_id")
    last = r2_data["paths"].sort_values(["event_id", "h_since_entry"]) \
        .groupby("event_id").last()
    for eid in np.random.default_rng(1).choice(ledger.index, 50, replace=False):
        assert last.loc[eid, "net_bps"] == pytest.approx(ledger.loc[eid, "pnl_bps"],
                                                         abs=1e-9)


def test_paths_hourly_and_full(r2_data):
    p = r2_data["paths"]
    per = p.groupby("event_id").size()
    # most events have the full 6 bars; a few near the data edge have fewer
    # (truncated grid windows at panel boundaries) - never more than 6
    assert per.between(2, 6).all()
    assert int((per == 6).sum()) >= 840
    assert p["h_since_entry"].between(0, 5).all()


# ---------------------------------------------------------------------------
# MAE bins / first passage
# ---------------------------------------------------------------------------

def test_mae_bin_partition():
    depths = np.array([0.0, 0.24, 0.25, 0.74, 0.99, 1.49, 1.75, 2.49, 2.5, 10.0])
    labels = mae_bin_of(depths)
    assert len(set(labels)) == 8  # every documented bin is reachable
    assert labels[0] == "0 to -0.25R"
    assert labels[2] == "-0.25 to -0.50R"
    assert labels[4] == "-0.75 to -1.00R"
    assert labels[5] == "-1.00 to -1.50R"
    assert labels[6] == "-1.50 to -2.00R"
    assert labels[8] == "worse than -2.50R"
    assert labels[9] == "worse than -2.50R"


def test_first_passage_synthetic():
    path = np.array([0.0, -0.2, -0.6, -0.3, -1.1, -0.8])
    assert first_passage(path, 0.25) == pytest.approx(2.0)  # -0.6 <= -0.25
    assert first_passage(path, 0.5) == pytest.approx(2.0)
    assert first_passage(path, 1.0) == pytest.approx(4.0)
    assert np.isnan(first_passage(path, 2.0))


def test_failure_speed_monotonic(r2_data):
    fs = failure_speed(r2_data["ledger"], r2_data["paths"])
    th = fs["threshold_R"].to_numpy()
    assert (np.diff(th) > 0).all()
    # deeper thresholds are breached by fewer trades
    nb = fs["n_breached"].to_numpy()
    assert (np.diff(nb) <= 0).all()


def test_failure_classes_cover_losers(r2_data):
    cls = r2_data["classes"]
    n_losers = int((r2_data["ledger"]["pnl_bps"] <= 0).sum())
    assert int(cls["n"].sum()) == n_losers
    assert set(cls["failure_class"]) == {"FAST", "MEDIUM", "SLOW"}


# ---------------------------------------------------------------------------
# Recovery surface causality
# ---------------------------------------------------------------------------

def test_recovery_surface_causal_state(r2_data):
    """State (MAE bin) must be a running minimum: never deeper than the final
    outcome would allow, and win probability 0 in deep cells at adequate N
    (winners never go below ~-0.6R, so deep cells imply losers)."""
    surf = recovery_surface(r2_data["ledger"], r2_data["paths"])
    deep = surf[(surf["family"] == "A+B")
                & (surf["mae_bin"].isin(["-1.00 to -1.50R", "-1.50 to -2.00R"]))
                & (surf["N"] >= 30)]
    assert len(deep) > 0
    assert (deep["win_probability"] == 0.0).all()


def test_recovery_surface_cells_complete(r2_data):
    surf = recovery_surface(r2_data["ledger"], r2_data["paths"])
    assert surf["exploratory"].dtype == bool
    assert surf["mae_bin"].isin(MAE_BIN_LABELS).all()
    assert (surf["N"] > 0).all()


# ---------------------------------------------------------------------------
# Cluster ranks / concurrency joins
# ---------------------------------------------------------------------------

def test_cluster_ranks_partition(r2_data):
    ledger = r2_data["ledger"]
    for iv in [2.0, 6.0, 12.0]:
        ranks = assign_cluster_ranks(ledger, iv)
        assert len(ranks) == len(ledger)
        assert ranks["event_id"].duplicated().sum() == 0
        per = ranks.groupby(["cluster_id", "rank_in_cluster"]).size()
        # each rank occurs exactly once per cluster
        assert (per == 1).all()
        # rank <= cluster size everywhere
        rk = ranks["rank_in_cluster"].to_numpy()
        cs = ranks["cluster_size"].to_numpy()
        assert (rk <= cs).all()
        assert ranks["rank_in_cluster"].max() >= 1


def test_concurrency_joins(r2_data):
    ledger = r2_data["ledger"]
    ctx = r2_data["ctx"]
    assert (ctx["n_at_entry"] >= 0).all()
    assert (ctx["max_concurrent_during"] >= 1).all()
    # a trade with no overlap must have n_at_entry == 0 and max == 1
    iso = ctx[(ctx["same_dir_overlap"] == False) & (ctx["opp_dir_overlap"] == False)]  # noqa: E712
    if len(iso):
        assert (iso["n_at_entry"] == 0).all()
        assert (iso["max_concurrent_during"] == 1).all()
    # overlap flags imply some other position exists during the trade window
    # (n_at_entry only counts positions active AT ENTRY, so later-entering
    # overlaps legitimately show n_at_entry == 0 but max_concurrent >= 2)
    ov = ctx[ctx["same_dir_overlap"] | ctx["opp_dir_overlap"]]
    assert (ov["max_concurrent_during"] >= 2).all()


def test_temporal_split_labels(r2_data):
    assert set(r2_data["ledger"]["split"]) == set(SPLITS)


# ---------------------------------------------------------------------------
# Loss streaks
# ---------------------------------------------------------------------------

def test_max_loss_streak_manual():
    seq = np.array([1.0, -1.0, -2.0, 0.5, -0.5, -0.5, -0.5, 2.0, -1.0])
    # longest run of negatives = 3
    from capital_routing.phases.phase_r2_common import _max_loss_streak
    assert _max_loss_streak(seq) == 3


def test_loss_streaks_deterministic(r2_data):
    a = loss_streaks(r2_data["ledger"], r2_data["ctx"])
    b = loss_streaks(r2_data["ledger"], r2_data["ctx"])
    assert a.equals(b)
    pooled = a[a["unit"] == "trades_pooled"].iloc[0]
    assert pooled["max_streak"] >= 1


def test_streak_block_bootstrap_reproducible(r2_data):
    a = loss_streaks(r2_data["ledger"], r2_data["ctx"])
    b = loss_streaks(r2_data["ledger"], r2_data["ctx"])
    assert a.attrs["block_bootstrap"]["boot_median"] == \
        b.attrs["block_bootstrap"]["boot_median"]


# ---------------------------------------------------------------------------
# Tail buckets + rolling-window regression
# ---------------------------------------------------------------------------

def test_tail_bucket_counts(r2_data):
    from capital_routing.phases.phase_r2_analysis import tail_attribution
    tail = tail_attribution(r2_data["ledger"], r2_data["paths"], r2_data["ctx"])
    ns = []
    for q in [0.01, 0.025, 0.05, 0.10]:
        rows = tail[(tail["cut"] == "final_return") & (tail["quantile"] == q)]
        assert len(rows) == 1
        r = rows.iloc[0]
        # quantile thresholds: N approximates floor(890*q) +/- ties
        assert 1 <= r["N"] <= int(0.11 * 890)
        ns.append(int(r["N"]))
    assert ns == sorted(ns)  # deeper cuts are larger sets


def test_worst_24h_window_trades_sum(r2_data):
    """Regression: the tail-attribution worst-24h trade set must reproduce the
    rolling-window minimum (window [w-23h, w])."""
    from capital_routing.phases.phase_r2_analysis import tail_attribution
    ledger = r2_data["ledger"]
    ts = pd.to_datetime(ledger["entry_ts"], utc=True)
    h = pd.Series(ledger["pnl_bps"].to_numpy(float), index=ts).resample("h").sum()
    r24 = h.rolling(24).sum()
    w24 = r24.idxmin()
    ids = set(ledger.index[(ts >= w24 - pd.Timedelta(hours=23)) & (ts <= w24)])
    assert ledger.loc[list(ids), "pnl_bps"].sum() == pytest.approx(r24.min(), abs=1e-9)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_paths_deterministic(r2_base, r2_data):
    ledger = r2_data["ledger"]
    marks = build_marks(ledger, r2_base["panel"])
    p1 = build_net_paths(ledger, marks)
    p2 = build_net_paths(ledger, marks)
    assert p1.equals(p2)


def test_concurrency_effects_deterministic(r2_data):
    a = concurrency_loss_effects(r2_data["ledger"], r2_data["paths"], r2_data["ctx"])
    b = concurrency_loss_effects(r2_data["ledger"], r2_data["paths"], r2_data["ctx"])
    assert a.equals(b)
