"""
CR-RISK-BLOCK1 R3 — Profit Anatomy (R3.1-R3.7, R3.11 analysis).

R3.1 winner/loser MFE distributions (4 unit systems)
R3.2 time to first profit (+0.10R .. +2.00R first-passage)
R3.3 time to MFE (hour-of-peak distribution)
R3.4 MFE capture ratio + giveback (per-trade)
R3.5 profit-giveback transitions (reach +L R, then finish ?)
R3.6 remaining-expectancy surface by current-PnL state at each age
R3.7 profit-maturity states (declared quantile-based classes)
R3.11 winner-tail attribution (best 1/2.5/5/10% share + ex-tail expectancy)

All descriptive. No TP, early exit, trailing, breakeven, partial, or sizing
change is created anywhere.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_r2_common import (MIN_SUPPORT, first_passage_positive,
                              per_event_paths, percentile_ci,
                              time_to_mfe)

QUANTILES = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]

# Time-to-profit first-passage levels (R)
PROFIT_LEVELS_R = [0.10, 0.25, 0.50, 0.75, 1.00, 1.50, 2.00]

# Current-PnL state buckets (right-open; declared before outcome review)
PNL_BUCKET_EDGES = [-np.inf, -0.75, -0.5, -0.25, 0.0, 0.25, 0.5, 0.75, 1.0, np.inf]
PNL_BUCKET_LABELS = [
    "< -0.75R", "-0.75 to -0.50R", "-0.50 to -0.25R", "-0.25 to 0R",
    "0 to +0.25R", "+0.25 to +0.50R", "+0.50 to +0.75R", "+0.75 to +1.0R",
    "> +1.0R",
]

# Profit-maturity class thresholds (declared, not tuned)
MEANINGFUL_PEAK_R = 0.50   # a peak >= +0.5R counts as meaningful delivery
HALF_GIVEBACK = 0.50       # finished below half of a meaningful peak -> gave back
EARLY_HOURS = 2            # hour of MFE <= 2 -> early delivery
MID_HOURS = 4              # hour of MFE <= 4 -> mid delivery (else late)


def pnl_bucket_of(pnl_R: np.ndarray) -> np.ndarray:
    return pd.cut(pd.Series(pnl_R), bins=PNL_BUCKET_EDGES, labels=PNL_BUCKET_LABELS,
                  right=False, include_lowest=True).astype(str)


# ---------------------------------------------------------------------------
# R3.1 — MFE distributions
# ---------------------------------------------------------------------------

def mfe_distributions(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    out = ledger.set_index("event_id")[["family", "pos"]].join(
        paths.groupby("event_id").agg(
            mfe_mkt_bps=("mkt_bps", "max"),
            mfe_net_bps=("net_bps", "max"),
            mfe_R=("net_R", "max"),
        ))
    out["mfe_per_pos_bps"] = out["mfe_net_bps"] / out["pos"]
    out["outcome"] = np.where(ledger.set_index("event_id")["pnl_bps"] > 0,
                              "WINNER", "LOSER")
    rows = []
    for fam_lbl in ["A", "B", "A+B"]:
        sub = out if fam_lbl == "A+B" else out[out["family"] == fam_lbl]
        for oc in ["WINNER", "LOSER"]:
            s = sub[sub["outcome"] == oc]
            for unit, col in [("raw_market_bps", "mfe_mkt_bps"),
                              ("strategy_pnl_bps", "mfe_net_bps"),
                              ("R", "mfe_R"),
                              ("per_volnorm_unit_bps", "mfe_per_pos_bps")]:
                v = s[col].to_numpy(dtype=float)
                v = v[np.isfinite(v)]
                if len(v) == 0:
                    continue
                rows.append({
                    "family": fam_lbl, "outcome": oc, "unit": unit, "N": int(len(v)),
                    "mean": float(v.mean()), "median": float(np.median(v)),
                    "p5": float(np.percentile(v, 5)), "p10": float(np.percentile(v, 10)),
                    "p25": float(np.percentile(v, 25)), "p50": float(np.percentile(v, 50)),
                    "p75": float(np.percentile(v, 75)), "p90": float(np.percentile(v, 90)),
                    "p95": float(np.percentile(v, 95)), "p99": float(np.percentile(v, 99)),
                    "max": float(v.max()),
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R3.2 — Time to first profit
# ---------------------------------------------------------------------------

def time_to_profit(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    """Time to first profit by threshold, with population-correct shares.

    For each family and each +threshold:
      N_reached_all   = all trades that reach the level
      N_winners_reached / N_losers_reached = eventual winners/losers that reach
    Shares are each computed against their own population so every value lies
    in [0, 1]: share_of_all = N_reached_all / N_trades,
    share_of_winners = N_winners_reached / N_winners,
    share_of_losers = N_losers_reached / N_losers.

    First-passage TIMES are unchanged by the repair (they only depend on the
    net-R path); winner-only and loser-only timing are reported in addition.
    """
    ev_paths = per_event_paths(paths)
    net = ledger.set_index("event_id")
    rows = []
    for fam_lbl in ["A", "B", "A+B"]:
        fam = net if fam_lbl == "A+B" else net[net["family"] == fam_lbl]
        n = len(fam)
        n_win = int((fam["pnl_bps"] > 0).sum())
        n_los = n - n_win
        for th in PROFIT_LEVELS_R:
            reached = {}
            for eid in fam.index:
                t = first_passage_positive(ev_paths[eid], th)
                if t is not None and np.isfinite(t):
                    reached[eid] = t
            if not reached:
                rows.append({"family": fam_lbl, "level_R": th, "N_reached_all": 0})
                continue
            finals = np.array([float(fam.loc[e, "pnl_bps"])
                               / float(fam.loc[e, "risk_unit_bps"])
                               for e in reached])
            times = np.array(list(reached.values()))
            eids = list(reached.keys())
            winners = [e for e in eids if fam.loc[e, "pnl_bps"] > 0]
            losers = [e for e in eids if fam.loc[e, "pnl_bps"] <= 0]
            w_times = np.array([reached[e] for e in winners])
            l_times = np.array([reached[e] for e in losers])
            rows.append({
                "family": fam_lbl, "level_R": th,
                "N_reached_all": int(len(reached)),
                "N_winners_reached": int(len(winners)),
                "N_losers_reached": int(len(losers)),
                "share_of_all_trades_reaching": float(len(reached)) / n if n else np.nan,
                "share_of_winners_reaching": float(len(winners)) / n_win if n_win else np.nan,
                "share_of_losers_reaching": float(len(losers)) / n_los if n_los else np.nan,
                "median_time_h": float(np.median(times)),
                "p25_time_h": float(np.percentile(times, 25)),
                "p75_time_h": float(np.percentile(times, 75)),
                "median_time_winners_h": float(np.median(w_times)) if len(w_times) else np.nan,
                "median_time_losers_h": float(np.median(l_times)) if len(l_times) else np.nan,
                "p25_time_winners_h": float(np.percentile(w_times, 25)) if len(w_times) else np.nan,
                "p75_time_winners_h": float(np.percentile(w_times, 75)) if len(w_times) else np.nan,
                "final_expectancy_R_after_reaching": float(np.mean(finals)),
                "final_loss_probability_after_reaching": float((finals < 0).mean()),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R3.3 — Time to MFE
# ---------------------------------------------------------------------------

def time_to_mfe_table(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    ev_paths = per_event_paths(paths)
    net = ledger.set_index("event_id")
    rows = []
    for fam_lbl in ["A", "B", "A+B"]:
        fam = net if fam_lbl == "A+B" else net[net["family"] == fam_lbl]
        for grp_name, grp_ids in [
            ("all", fam.index),
            ("winners", fam.index[fam["pnl_bps"] > 0]),
            ("losers", fam.index[fam["pnl_bps"] <= 0]),
        ]:
            ttm = [time_to_mfe(ev_paths[e]) for e in grp_ids]
            ttm = np.array(ttm)
            ttm = ttm[np.isfinite(ttm)]
            if len(ttm) == 0:
                continue
            # hour = index + 1 (bar k is at hour k+1 from the entry bar)
            hours = ttm + 1.0
            rows.append({
                "family": fam_lbl, "group": grp_name, "N": int(len(hours)),
                "median_hour": float(np.median(hours)),
                "p75_hour": float(np.percentile(hours, 75)),
                "p90_hour": float(np.percentile(hours, 90)),
                "pct_hour1": float((hours <= 1).mean()),
                "pct_hour2": float((hours == 2).mean()),
                "pct_hour3": float((hours == 3).mean()),
                "pct_hour4": float((hours == 4).mean()),
                "pct_hour5": float((hours == 5).mean()),
                "pct_hour6": float((hours == 6).mean()),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R3.4 — Capture ratio + giveback
# ---------------------------------------------------------------------------

def _per_trade(paths: pd.DataFrame) -> pd.DataFrame:
    return paths.groupby("event_id").agg(
        mfe_R=("net_R", "max"), final_R=("net_R", "last"),
        tt_mfe=("net_R", lambda s: float(np.argmax(s.to_numpy()))),
    )


def capture_ratio(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    per = _per_trade(paths)
    tab = ledger.set_index("event_id")[["family", "pnl_bps", "risk_unit_bps"]].join(per)
    tab["final_R"] = tab["pnl_bps"] / tab["risk_unit_bps"]
    tab["capture"] = np.where(tab["mfe_R"] > 0, tab["final_R"] / tab["mfe_R"], np.nan)
    tab["giveback_R"] = tab["mfe_R"] - tab["final_R"]
    tab["giveback_fraction"] = np.where(
        tab["mfe_R"] > 0, tab["giveback_R"] / tab["mfe_R"], np.nan)
    tab["outcome"] = np.where(tab["final_R"] > 0, "WINNER", "LOSER")
    rows = []
    for fam_lbl in ["A", "B", "A+B"]:
        sub = tab if fam_lbl == "A+B" else tab[tab["family"] == fam_lbl]
        for oc in ["WINNER", "LOSER"]:
            s = sub[sub["outcome"] == oc]
            cap = s["capture"].dropna().to_numpy(dtype=float)
            rows.append({
                "family": fam_lbl, "outcome": oc, "N": int(len(s)),
                "n_no_positive_mfe": int((s["mfe_R"] <= 0).sum()),
                "median_capture": float(np.median(cap)) if len(cap) else np.nan,
                "p25_capture": float(np.percentile(cap, 25)) if len(cap) else np.nan,
                "p75_capture": float(np.percentile(cap, 75)) if len(cap) else np.nan,
                "p90_capture": float(np.percentile(cap, 90)) if len(cap) else np.nan,
                "share_capture_ge_25pct": float((cap >= 0.25).mean()) if len(cap) else np.nan,
                "share_capture_ge_50pct": float((cap >= 0.50).mean()) if len(cap) else np.nan,
                "share_capture_ge_75pct": float((cap >= 0.75).mean()) if len(cap) else np.nan,
                "share_capture_ge_90pct": float((cap >= 0.90).mean()) if len(cap) else np.nan,
                "median_giveback_R": float(np.median(s["giveback_R"].to_numpy(dtype=float))),
            })
    return pd.DataFrame(rows)


def profit_giveback(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    per = _per_trade(paths)
    tab = ledger.set_index("event_id")[["family", "pnl_bps", "risk_unit_bps"]].join(per)
    tab["final_R"] = tab["pnl_bps"] / tab["risk_unit_bps"]
    tab["giveback_R"] = tab["mfe_R"] - tab["final_R"]
    tab["giveback_fraction"] = np.where(tab["mfe_R"] > 0,
                                        tab["giveback_R"] / tab["mfe_R"], np.nan)
    tab["outcome"] = np.where(tab["final_R"] > 0, "WINNER", "LOSER")
    tab["tt_mfe"] = tab["tt_mfe"] + 1.0  # hour
    rows = []
    for fam_lbl in ["A", "B", "A+B"]:
        sub = tab if fam_lbl == "A+B" else tab[tab["family"] == fam_lbl]
        for oc in ["WINNER", "LOSER"]:
            s = sub[sub["outcome"] == oc]
            gb = s["giveback_R"].to_numpy(dtype=float)
            rows.append({
                "family": fam_lbl, "outcome": oc, "N": int(len(s)),
                "median_giveback_R": float(np.median(gb)),
                "p25_giveback_R": float(np.percentile(gb, 25)),
                "p75_giveback_R": float(np.percentile(gb, 75)),
                "p90_giveback_R": float(np.percentile(gb, 90)),
                "median_giveback_fraction": float(np.nanmedian(s["giveback_fraction"])),
                "mean_giveback_R": float(np.mean(gb)),
            })
        # by age-of-MFE bucket (pooled within family)
        for hb in [1, 2, 3, 4, 5, 6]:
            s = sub[sub["tt_mfe"] == hb]
            if len(s):
                rows.append({
                    "family": fam_lbl, "outcome": f"mfe_hour_{hb}", "N": int(len(s)),
                    "median_giveback_R": float(np.median(s["giveback_R"])),
                    "median_giveback_fraction": float(np.nanmedian(s["giveback_fraction"])),
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R3.5 — Giveback transitions
# ---------------------------------------------------------------------------

def giveback_transitions(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    ev_paths = per_event_paths(paths)
    net = ledger.set_index("event_id")
    rows = []
    for th in [0.25, 0.50, 0.75, 1.00]:
        reached = []
        for eid in net.index:
            t = first_passage_positive(ev_paths[eid], th)
            if t is not None and np.isfinite(t):
                reached.append(eid)
        if not reached:
            rows.append({"level_R": th, "N_reached": 0})
            continue
        sub = net.loc[reached]
        final_R = (sub["pnl_bps"] / sub["risk_unit_bps"]).to_numpy(dtype=float)
        mfe_R = np.array([np.max(ev_paths[e]) for e in reached])
        rows.append({
            "level_R": th, "N_reached": int(len(reached)),
            "share_of_trades": float(len(reached)) / len(net),
            "p_finish_positive": float((final_R > 0).mean()),
            "p_finish_below_half_peak": float((final_R < mfe_R / 2.0).mean()),
            "p_finish_near_breakeven": float((np.abs(final_R) <= 0.05).mean()),
            "p_finish_negative": float((final_R < 0).mean()),
            "median_final_R": float(np.median(final_R)),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R3.6 — Remaining expectancy surface
# ---------------------------------------------------------------------------

def remaining_expectancy_surface(ledger: pd.DataFrame,
                                 paths: pd.DataFrame) -> pd.DataFrame:
    p = paths.copy()
    p["pnl_bucket"] = pnl_bucket_of(p["net_R"].to_numpy(dtype=float))
    fam = ledger.set_index("event_id")["family"].to_dict()
    p["family"] = p["event_id"].map(fam)
    # future stats (reverse cummin/max from current bar)
    p = p.sort_values(["event_id", "h_since_entry"])
    p["future_max_R"] = p.groupby("event_id")["net_R"].transform(
        lambda s: s.iloc[::-1].cummax().iloc[::-1])
    p["future_min_R"] = p.groupby("event_id")["net_R"].transform(
        lambda s: s.iloc[::-1].cummin().iloc[::-1])
    p["remaining_R"] = p["final_net_R"] - p["net_R"]
    rows = []
    for age in [1, 2, 3, 4, 5]:  # h_since_entry (skip the entry bar)
        for fam_lbl in ["A+B", "A", "B"]:
            sub = p[(p["h_since_entry"] == age)]
            sub = sub if fam_lbl == "A+B" else sub[sub["family"] == fam_lbl]
            for bk in PNL_BUCKET_LABELS:
                cell = sub[sub["pnl_bucket"] == bk]
                if len(cell) == 0:
                    continue
                rows.append({
                    "age_h": age, "family": fam_lbl, "pnl_bucket": bk,
                    "N": int(len(cell)),
                    "exploratory": bool(len(cell) < MIN_SUPPORT),
                    "current_median_R": float(np.median(cell["net_R"])),
                    "final_expectancy_R": float(np.mean(cell["final_net_R"])),
                    "remaining_expectancy_R": float(np.mean(cell["remaining_R"])),
                    "p_finish_positive": float((cell["final_net_R"] > 0).mean()),
                    # = give-back-to-negative when current >= 0
                    "p_finish_negative": float((cell["final_net_R"] < 0).mean()),
                    "future_mfe_R": float(np.mean(cell["future_max_R"])),
                    "future_mae_R": float(np.mean(cell["future_min_R"])),
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R3.7 — Profit maturity classes
# ---------------------------------------------------------------------------

def profit_maturity(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    per = _per_trade(paths)
    tab = ledger.set_index("event_id")[["family", "pnl_bps", "risk_unit_bps"]].join(per)
    tab["final_R"] = tab["pnl_bps"] / tab["risk_unit_bps"]
    tab["mfe_R"] = np.maximum(tab["mfe_R"], 0.0)
    tab["giveback_fraction"] = np.where(tab["mfe_R"] > 0,
                                        (tab["mfe_R"] - tab["final_R"]) / tab["mfe_R"],
                                        np.nan)
    ttm = tab["tt_mfe"] + 1.0  # hour of MFE

    def classify(row):
        if row["mfe_R"] >= MEANINGFUL_PEAK_R and row["final_R"] < row["mfe_R"] * (1 - HALF_GIVEBACK):
            return "PEAKED_AND_GIVING_BACK"
        if row["mfe_R"] < 0.25:
            return "NOT_YET_DELIVERED"
        if ttm.loc[row.name] <= EARLY_HOURS:
            return "EARLY_DELIVERY"
        if ttm.loc[row.name] <= MID_HOURS:
            return "MID_HOLD_DELIVERY"
        return "LATE_DELIVERY"

    tab["maturity_class"] = tab.apply(classify, axis=1)
    rows = []
    for cls in ["NOT_YET_DELIVERED", "EARLY_DELIVERY", "MID_HOLD_DELIVERY",
                "LATE_DELIVERY", "PEAKED_AND_GIVING_BACK"]:
        s = tab[tab["maturity_class"] == cls]
        if len(s) == 0:
            continue
        mae = paths.groupby("event_id")["net_R"].min().reindex(s.index)
        rows.append({
            "maturity_class": cls, "N": int(len(s)),
            "win_rate": float((s["final_R"] > 0).mean()),
            "final_expectancy_R": float(np.mean(s["final_R"])),
            "median_final_R": float(np.median(s["final_R"])),
            "median_mfe_R": float(np.median(s["mfe_R"])),
            "median_mae_R": float(np.median(mae)),
            "median_giveback_fraction": float(np.nanmedian(s["giveback_fraction"])),
            "median_time_to_mfe_h": float(np.median(ttm.loc[s.index])),
            "family_A_share": float((s["family"] == "A").mean()),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R3.11 — Winner-tail attribution
# ---------------------------------------------------------------------------

def winner_tail_attribution(ledger: pd.DataFrame) -> pd.DataFrame:
    net = ledger.set_index("event_id")
    pos = net[net["pnl_bps"] > 0]
    total_pos = float(pos["pnl_bps"].sum())
    rows = []
    for q in [0.01, 0.025, 0.05, 0.10]:
        thr = float(pos["pnl_bps"].quantile(1 - q))
        tail = pos[pos["pnl_bps"] >= thr]
        rows.append({
            "quantile": q, "N": int(len(tail)),
            "share_of_total_positive_pnl": float(tail["pnl_bps"].sum() / total_pos)
            if total_pos != 0 else np.nan,
            "min_pnl_bps": float(tail["pnl_bps"].min()),
        })
    # expectancy excluding the best q% (trades with pnl below the (1-q) quantile)
    all_pnl = net["pnl_bps"].to_numpy(dtype=float)
    for q in [0.01, 0.05, 0.10]:
        thr = float(net["pnl_bps"].quantile(1 - q))
        ex = net[net["pnl_bps"] < thr]
        rows.append({
            "quantile": q, "N": int(len(ex)),
            "expectancy_excluding_best_q_R": float(
                np.mean(ex["pnl_bps"] / ex["risk_unit_bps"])),
        })
    return pd.DataFrame(rows)
