"""
CR-RISK-BLOCK1 R2 — Loss Anatomy (R2.6-R2.10 context studies).

R2.6 loss streaks (chronological; block bootstrap on the max streak)
R2.7 concurrency and loss amplification (entry concurrency + overlap flags)
R2.8 episode rank and loss risk (does later-rank independence hold on the
     downside? per 2/3/6/12h cluster interval)
R2.9 A vs B loss signature (future unequal-risk allocation evidence only)
R2.10 temporal stability (inner_sel / inner_val / RELATIONSHIP_CONFIRMED_OOS)

Also builds the per-event trade context (concurrency at entry, overlap flags,
episode rank, failure class, first-passage times) consumed by R2.5 tail
attribution. All descriptive; no allocation or execution change.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_r1_episodes import INTERVALS_H
from .phase_r2_common import (BLOCK_BOOTSTRAP_BLOCK, MIN_SUPPORT, SPLITS,
                              first_passage, per_event_paths,
                              time_to_worst_mae, block_bootstrap_max_streak)

EPISODE_INTERVALS = [2.0, 3.0, 6.0, 12.0]


# ---------------------------------------------------------------------------
# Per-event cluster ranks (greedy chaining, identical rule to R1)
# ---------------------------------------------------------------------------

def assign_cluster_ranks(ledger: pd.DataFrame, interval_h: float) -> pd.DataFrame:
    t = ledger.sort_values("event_ts").reset_index(drop=True)
    ts = pd.to_datetime(t["event_ts"], utc=True)
    gap = ts.diff()
    new_cluster = gap.isna() | (gap > pd.Timedelta(hours=interval_h))
    t["cluster_id"] = new_cluster.cumsum() - 1
    t["rank_in_cluster"] = t.groupby("cluster_id").cumcount() + 1
    t["cluster_size"] = t.groupby("cluster_id")["cluster_id"].transform("size")
    return t[["event_id", "cluster_id", "rank_in_cluster", "cluster_size"]]


# ---------------------------------------------------------------------------
# Per-trade context frame (used by tail attribution + concurrency studies)
# ---------------------------------------------------------------------------

def _max_active_on(ts: np.ndarray, entry: np.ndarray, exit_: np.ndarray) -> int:
    """Max number of intervals active at any of the candidate timestamps."""
    ts = np.sort(np.unique(ts))
    best = 0
    for t in ts:
        best = max(best, int(((entry <= t) & (exit_ > t)).sum()))
    return best


def trade_context(ledger: pd.DataFrame, paths: pd.DataFrame,
                  class_frame: pd.DataFrame) -> pd.DataFrame:
    """Per-event risk context: concurrency, overlap flags, episode rank (6h),
    failure class, first-passage times, time to worst MAE."""
    entry = pd.to_datetime(ledger["entry_ts"], utc=True).to_numpy(dtype="int64")
    exit_ = pd.to_datetime(ledger["exit_ts"], utc=True).to_numpy(dtype="int64")
    dir_ = ledger["dir"].to_numpy(dtype=float)
    fam = ledger["family"].to_numpy()
    n = len(ledger)

    n_at_entry = np.zeros(n, dtype=int)
    max_during = np.ones(n, dtype=int)
    same_ov = np.zeros(n, dtype=bool)
    opp_ov = np.zeros(n, dtype=bool)
    a_a = np.zeros(n, dtype=bool)
    b_b = np.zeros(n, dtype=bool)
    a_b = np.zeros(n, dtype=bool)
    for i in range(n):
        ov = (entry < exit_[i]) & (entry[i] < exit_)
        ov[i] = False
        # exclude the trade itself -> 0/1/2+ existing positions at entry
        n_at_entry[i] = int(((entry <= entry[i]) & (exit_ > entry[i])).sum()) - 1
        if ov.any():
            same_ov[i] = bool((dir_[ov] * dir_[i] > 0).any())
            opp_ov[i] = bool((dir_[ov] * dir_[i] < 0).any())
            a_a[i] = bool((fam[ov] == "A").any() and fam[i] == "A")
            b_b[i] = bool((fam[ov] == "B").any() and fam[i] == "B")
            a_b[i] = bool((fam[ov] != fam[i]).any())
            bounds = np.concatenate([entry[ov], exit_[ov], [entry[i]], [exit_[i]]])
            max_during[i] = _max_active_on(bounds, entry, exit_)

    ev_paths = per_event_paths(paths)
    fp1 = {}
    fp2 = {}
    twm = {}
    for eid, p in ev_paths.items():
        fp1[eid] = first_passage(p, 1.0)
        fp2[eid] = first_passage(p, 2.0)
        twm[eid] = time_to_worst_mae(p)

    ranks = assign_cluster_ranks(ledger, 6.0).set_index("event_id")
    ctx = pd.DataFrame({
        "event_id": ledger["event_id"],
        "n_at_entry": n_at_entry,
        "max_concurrent_during": max_during,
        "same_dir_overlap": same_ov,
        "opp_dir_overlap": opp_ov,
        "A_A_overlap": a_a, "B_B_overlap": b_b, "A_B_overlap": a_b,
        "rank_6h": [int(ranks.loc[e, "rank_in_cluster"]) for e in ledger["event_id"]],
        "cluster_size_6h": [int(ranks.loc[e, "cluster_size"]) for e in ledger["event_id"]],
        "time_to_worst_mae_h": [twm.get(e, np.nan) for e in ledger["event_id"]],
        "time_to_first_1R_h": [fp1.get(e, np.nan) for e in ledger["event_id"]],
        "time_to_first_2R_h": [fp2.get(e, np.nan) for e in ledger["event_id"]],
    })
    cls = class_frame.set_index("event_id")["failure_class"]
    ctx["failure_class"] = [cls.get(e) for e in ledger["event_id"]]
    return ctx


# ---------------------------------------------------------------------------
# R2.6 — Loss streaks
# ---------------------------------------------------------------------------

def loss_streaks(ledger: pd.DataFrame, ctx: pd.DataFrame) -> pd.DataFrame:
    t = ledger.sort_values("entry_ts").reset_index(drop=True)
    rows = []

    def _streak_stats(seq: np.ndarray, label: str):
        best = cur = 0
        best_sum = 0.0
        cur_sum = 0.0
        lengths = []
        for v in seq:
            if v < 0:
                cur += 1
                cur_sum += v
                best = max(best, cur)
                best_sum = min(best_sum, cur_sum)
            else:
                if cur > 0:
                    lengths.append(cur)
                cur = 0
                cur_sum = 0.0
        if cur > 0:
            lengths.append(cur)
        return best, np.array(lengths), best_sum

    # pooled trades
    best, lens, best_sum = _streak_stats(t["pnl_bps"].to_numpy(dtype=float), "pooled")
    rows.append({
        "unit": "trades_pooled", "n": int(len(t)), "max_streak": best,
        "mean_streak_len": float(lens.mean()) if len(lens) else np.nan,
        "p90_streak_len": float(np.percentile(lens, 90)) if len(lens) else np.nan,
        "max_streak_loss_bps": float(best_sum),
        "n_streaks": int(len(lens)),
    })
    # by family
    for fid in ["A", "B"]:
        sub = t[t["family"] == fid]
        best, lens, best_sum = _streak_stats(sub["pnl_bps"].to_numpy(dtype=float), fid)
        rows.append({
            "unit": f"trades_{fid}", "n": int(len(sub)), "max_streak": best,
            "mean_streak_len": float(lens.mean()) if len(lens) else np.nan,
            "p90_streak_len": float(np.percentile(lens, 90)) if len(lens) else np.nan,
            "max_streak_loss_bps": float(best_sum),
            "n_streaks": int(len(lens)),
        })
    # negative calendar days
    d = t.copy()
    d["date"] = pd.to_datetime(d["entry_ts"], utc=True).dt.date
    daily = d.groupby("date")["pnl_bps"].sum()
    best, lens, best_sum = _streak_stats(daily.to_numpy(dtype=float), "days")
    rows.append({
        "unit": "negative_days", "n": int(len(daily)), "max_streak": best,
        "mean_streak_len": float(lens.mean()) if len(lens) else np.nan,
        "p90_streak_len": float(np.percentile(lens, 90)) if len(lens) else np.nan,
        "max_streak_loss_bps": float(best_sum),
        "n_streaks": int(len(lens)),
    })
    # negative rolling 24h windows
    h_ser = pd.Series(t["pnl_bps"].to_numpy(dtype=float),
                      index=pd.to_datetime(t["entry_ts"], utc=True)).resample("h").sum().fillna(0.0)
    r24 = h_ser.rolling(24).sum().dropna()
    best, lens, _ = _streak_stats(r24.to_numpy(dtype=float), "24h")
    rows.append({
        "unit": "negative_24h_windows", "n": int(len(r24)), "max_streak": best,
        "mean_streak_len": float(lens.mean()) if len(lens) else np.nan,
        "p90_streak_len": float(np.percentile(lens, 90)) if len(lens) else np.nan,
        # overlapping windows: report the WORST single 24h window, not the sum
        "max_streak_loss_bps": float(r24.min()),
        "worst_single_window_bps": float(r24.min()),
        "n_streaks": int(len(lens)),
        "note": "24h windows overlap; max_streak_loss_bps = worst single window",
    })
    out = pd.DataFrame(rows)

    # block bootstrap on the pooled sequence
    boot = block_bootstrap_max_streak(t["pnl_bps"].to_numpy(dtype=float))
    out.attrs["block_bootstrap"] = boot
    return out


# ---------------------------------------------------------------------------
# R2.7 — Concurrency and loss amplification
# ---------------------------------------------------------------------------

def concurrency_loss_effects(ledger: pd.DataFrame, paths: pd.DataFrame,
                             ctx: pd.DataFrame) -> pd.DataFrame:
    tab = ledger.set_index("event_id").join(ctx.set_index("event_id"))
    per = paths.groupby("event_id").agg(mae_R=("net_R", "min"))
    tab = tab.join(per)
    ev_paths = per_event_paths(paths)
    rows = []

    def _row(label: str, sub: pd.DataFrame):
        if len(sub) == 0:
            return
        pnl_r = sub["r_multiple"].to_numpy(dtype=float)
        mae_r = sub["mae_R"].to_numpy(dtype=float)
        los_t1 = []
        for eid in sub.index:
            if eid in ev_paths and float(sub.loc[eid, "pnl_bps"]) <= 0:
                t = first_passage(ev_paths[eid], 1.0)
                if t is not None and np.isfinite(t):
                    los_t1.append(t)
        rows.append({
            "group": label, "N": int(len(sub)),
            "expectancy_R": float(np.mean(pnl_r)),
            "win_rate": float((pnl_r > 0).mean()),
            "median_mae_R": float(np.median(mae_r)),
            "p95_mae_R": float(np.percentile(mae_r, 5)),
            "p_less_neg1R": float((pnl_r < -1.0).mean()),
            "p_less_neg2R": float((pnl_r < -2.0).mean()),
            "median_time_to_neg1R_losers_h": float(np.median(los_t1)) if los_t1 else np.nan,
        })

    for cat in [0, 1, 2]:
        sub = tab[tab["n_at_entry"] == cat] if cat < 2 else tab[tab["n_at_entry"] >= 2]
        _row(f"entry_concurrency_{cat}" if cat < 2 else "entry_concurrency_2plus", sub)
    _row("same_dir_overlap_any", tab[tab["same_dir_overlap"]])
    _row("opp_dir_overlap_any", tab[tab["opp_dir_overlap"]])
    _row("A_A_overlap", tab[tab["A_A_overlap"]])
    _row("B_B_overlap", tab[tab["B_B_overlap"]])
    _row("A_B_overlap", tab[tab["A_B_overlap"]])
    _row("no_overlap", tab[~tab["same_dir_overlap"] & ~tab["opp_dir_overlap"]])
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R2.8 — Episode rank and loss risk
# ---------------------------------------------------------------------------

def episode_loss_effects(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    per = paths.groupby("event_id").agg(mae_R=("net_R", "min"))
    ev_paths = per_event_paths(paths)
    rows = []
    for iv in EPISODE_INTERVALS:
        ranks = assign_cluster_ranks(ledger, iv)
        tab = ledger.merge(ranks, on="event_id")
        for rb in ["1", "2", "3", "4+"]:
            if rb == "4+":
                sub = tab[tab["rank_in_cluster"] >= 4]
            else:
                sub = tab[tab["rank_in_cluster"] == int(rb)]
            if len(sub) == 0:
                continue
            pnl_r = sub["r_multiple"].to_numpy(dtype=float)
            mae_r = sub.merge(per, on="event_id", how="left")["mae_R"].to_numpy(dtype=float)
            sub_i = sub.set_index("event_id")
            los_t1 = []
            for eid in sub["event_id"]:
                if eid in ev_paths and float(sub_i.loc[eid, "pnl_bps"]) <= 0:
                    t = first_passage(ev_paths[eid], 1.0)
                    if t is not None and np.isfinite(t):
                        los_t1.append(t)
            rows.append({
                "interval_h": iv, "rank_in_cluster": rb, "N": int(len(sub)),
                "expectancy_R": float(np.mean(pnl_r)),
                "median_mae_R": float(np.median(mae_r)),
                "p95_loss_R": float(np.percentile(pnl_r, 5)),
                "p_less_neg1R": float((pnl_r < -1.0).mean()),
                "p_less_neg2R": float((pnl_r < -2.0).mean()),
                "median_time_to_neg1R_losers_h": float(np.median(los_t1)) if los_t1 else np.nan,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R2.9 — A vs B loss signature
# ---------------------------------------------------------------------------

def family_downside_comparison(ledger: pd.DataFrame, paths: pd.DataFrame,
                               ctx: pd.DataFrame) -> pd.DataFrame:
    per = paths.groupby("event_id").agg(mae_R=("net_R", "min"))
    tab = ledger.set_index("event_id").join(per).join(ctx.set_index("event_id"))
    ev_paths = per_event_paths(paths)
    rows = []
    for fid in ["A", "B"]:
        sub = tab[tab["family"] == fid]
        pnl_r = sub["r_multiple"].to_numpy(dtype=float)
        mae_r = sub["mae_R"].to_numpy(dtype=float)
        # recovery from -1R: P(win | MAE <= -1R)
        deep = sub[sub["mae_R"] <= -1.0]
        rec = float((deep["pnl_bps"] > 0).mean()) if len(deep) else np.nan
        losses = sub[sub["pnl_bps"] < 0]["pnl_bps"].sum()
        tail5 = sub[sub["pnl_bps"] <= sub["pnl_bps"].quantile(0.05)]
        tail_loss = tail5[tail5["pnl_bps"] < 0]["pnl_bps"].sum()
        los_t1 = []
        for eid in sub.index:
            if eid in ev_paths and float(sub.loc[eid, "pnl_bps"]) <= 0:
                t = first_passage(ev_paths[eid], 1.0)
                if t is not None and np.isfinite(t):
                    los_t1.append(t)
        rows.append({
            "family": fid, "N": int(len(sub)),
            "expectancy_R": float(np.mean(pnl_r)),
            "win_rate": float((pnl_r > 0).mean()),
            "median_mae_R": float(np.median(mae_r)),
            "p95_mae_R": float(np.percentile(mae_r, 5)),
            "p99_mae_R": float(np.percentile(mae_r, 1)),
            "worst_loss_R": float(np.min(pnl_r)),
            "p_recover_from_neg1R": rec,
            "median_time_to_neg1R_losers_h": float(np.median(los_t1)) if los_t1 else np.nan,
            "p_less_neg1R": float((pnl_r < -1.0).mean()),
            "p_less_neg2R": float((pnl_r < -2.0).mean()),
            "tail5_share_of_losses": float(tail_loss / losses) if losses != 0 else np.nan,
            "fast_failure_rate": float((sub["failure_class"] == "FAST").mean()),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R2.10 — Temporal stability
# ---------------------------------------------------------------------------

def temporal_stability(ledger: pd.DataFrame, paths: pd.DataFrame,
                       ctx: pd.DataFrame) -> pd.DataFrame:
    per = paths.groupby("event_id").agg(mae_R=("net_R", "min"))
    tab = ledger.set_index("event_id").join(per).join(ctx.set_index("event_id"))
    ev_paths = per_event_paths(paths)
    rows = []
    for sp in SPLITS:
        sub = tab[tab["split"] == sp]
        if len(sub) == 0:
            continue
        pnl_r = sub["r_multiple"].to_numpy(dtype=float)
        mae_r = sub["mae_R"].to_numpy(dtype=float)
        deep = sub[sub["mae_R"] <= -1.0]
        rec = float((deep["pnl_bps"] > 0).mean()) if len(deep) else np.nan
        losses = sub[sub["pnl_bps"] < 0]["pnl_bps"].sum()
        tail5 = sub[sub["pnl_bps"] <= sub["pnl_bps"].quantile(0.05)]
        tail_loss = tail5[tail5["pnl_bps"] < 0]["pnl_bps"].sum()
        los_t1 = []
        for eid in sub.index:
            if eid in ev_paths and float(sub.loc[eid, "pnl_bps"]) <= 0:
                t = first_passage(ev_paths[eid], 1.0)
                if t is not None and np.isfinite(t):
                    los_t1.append(t)
        rows.append({
            "split": sp, "N": int(len(sub)),
            "expectancy_R": float(np.mean(pnl_r)),
            "win_rate": float((pnl_r > 0).mean()),
            "median_mae_R": float(np.median(mae_r)),
            "p90_mae_R": float(np.percentile(mae_r, 10)),
            "p99_mae_R": float(np.percentile(mae_r, 1)),
            "p95_loss_R": float(np.percentile(pnl_r, 5)),
            "p_recover_from_neg1R": rec,
            "median_time_to_neg1R_losers_h": float(np.median(los_t1)) if los_t1 else np.nan,
            "p_less_neg1R": float((pnl_r < -1.0).mean()),
            "p_less_neg2R": float((pnl_r < -2.0).mean()),
            "tail5_share_of_losses": float(tail_loss / losses) if losses != 0 else np.nan,
        })
    return pd.DataFrame(rows)
