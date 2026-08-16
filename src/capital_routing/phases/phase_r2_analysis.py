"""
CR-RISK-BLOCK1 R2 — Loss Anatomy (R2.1-R2.5 analysis).

R2.1 winner/loser MAE distributions (4 unit systems)
R2.2 failure speed (first-passage times to -0.25R .. -3.00R) + empirical
     failure classes (FAST / MEDIUM / SLOW via time-to-worst-MAE tertiles)
R2.3 recovery probability surface P(win | MAE_t, age_t, family) - causal states
R2.4 recovery-cliff detection (descriptive, HYPOTHESIS_ONLY)
R2.5 tail-loss attribution (worst 1/2.5/5/10% by final return and by MAE)

No stop, no filter, no early exit, no sizing change is created anywhere here.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_r2_common import (AGE_BIN_LABELS, BOOTSTRAP_ITERS, BOOTSTRAP_SEED,
                              FAILURE_THRESHOLDS_R, MAE_BIN_LABELS, MIN_SUPPORT,
                              SPLITS, age_bin_of, first_passage,
                              mae_bin_of, percentile_ci,
                              time_to_worst_mae)

QUANTILES = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]


# ---------------------------------------------------------------------------
# R2.1 — Winner vs loser MAE
# ---------------------------------------------------------------------------

def mae_distributions(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    """MAE quantiles by (family, outcome) in 4 unit systems."""
    # per-event worst values (from the net-PnL path)
    out = ledger.set_index("event_id")[["family", "pos"]].join(
        paths.groupby("event_id").agg(
            mae_mkt_bps=("mkt_bps", "min"),
            mae_net_bps=("net_bps", "min"),
            mae_R=("net_R", "min"),
        ))
    out["mae_per_pos_bps"] = out["mae_net_bps"] / ledger.set_index("event_id")["pos"]
    out["outcome"] = np.where(ledger.set_index("event_id")["pnl_bps"] > 0, "WINNER", "LOSER")

    rows = []
    for fam_lbl in ["A", "B", "A+B"]:
        sub = out if fam_lbl == "A+B" else out[out["family"] == fam_lbl]
        for oc in ["WINNER", "LOSER"]:
            s = sub[sub["outcome"] == oc]
            for unit, col in [("raw_market_bps", "mae_mkt_bps"),
                              ("strategy_pnl_bps", "mae_net_bps"),
                              ("R", "mae_R"),
                              ("per_volnorm_unit_bps", "mae_per_pos_bps")]:
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
# R2.2 — Failure speed + classes
# ---------------------------------------------------------------------------

def failure_speed(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    """First-passage times to adverse R thresholds.

    - time statistics: eventual LOSERS only (how quickly losing routes reveal)
    - recovery-to-profit + final expectancy: ALL trades that breached the
      threshold (so recovery from a breach is measurable at all)
    """
    from .phase_r2_common import per_event_paths
    ev_paths = per_event_paths(paths)
    net = ledger.set_index("event_id")
    losers = set(net.index[net["pnl_bps"] <= 0])
    rows = []
    for th in FAILURE_THRESHOLDS_R:
        times = {}
        for eid, p in ev_paths.items():
            t = first_passage(p, th)
            if t is not None and np.isfinite(t):
                times[eid] = t
        # loser-only timing
        los_times = [times[e] for e in times if e in losers]
        # all-breachers recovery/expectancy (in R: net bps / risk unit)
        final = {e: float(net.loc[e, "pnl_bps"]) / float(net.loc[e, "risk_unit_bps"])
                 for e in times}
        finals = np.array(list(final.values()), dtype=float)
        recovered = float((finals > 0).mean()) if len(finals) else np.nan
        rows.append({
            "threshold_R": th,
            "n_breached": int(len(times)),
            "n_breached_losers": int(len(los_times)),
            "pct_losers_breaching": 100.0 * len(los_times) / max(len(losers), 1),
            "median_time_losers_h": float(np.median(los_times)) if los_times else np.nan,
            "p25_time_losers_h": float(np.percentile(los_times, 25)) if los_times else np.nan,
            "p75_time_losers_h": float(np.percentile(los_times, 75)) if los_times else np.nan,
            "recovery_to_profit_freq": recovered,
            "final_expectancy_R_after_breach": float(np.mean(finals)) if len(finals) else np.nan,
            "final_median_R_after_breach": float(np.median(finals)) if len(finals) else np.nan,
        })
    return pd.DataFrame(rows)


def failure_classes(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    """Empirical FAST/MEDIUM/SLOW failure classes over losing trades.

    Basis (documented): 'reveal time' = time (hours) to first breach of -0.5R;
    losers that never breach are assigned 6h (they fail slowly by grinding).
    Tertiles of reveal time define the classes - empirical quantiles, not
    arbitrary constants. Time-to-worst-MAE alone is too tied at hourly
    resolution (142/333 losers are at their worst at the final bar) to split.
    Returns (table, per-event class frame)."""
    from .phase_r2_common import per_event_paths
    ev_paths = per_event_paths(paths)
    net = ledger.set_index("event_id")
    rows = []
    class_of = {}
    losers = net[net["pnl_bps"] <= 0]
    reveal = {}
    twm = {}
    for eid in losers.index:
        p = ev_paths[eid]
        t = first_passage(p, 0.5)
        reveal[eid] = t if (t is not None and np.isfinite(t)) else 6.0
        twm[eid] = time_to_worst_mae(p)
    if len(reveal) >= 3:
        q1, q2 = np.percentile(np.array(list(reveal.values())), [33.33, 66.67])
        for eid, v in reveal.items():
            if v <= q1:
                class_of[eid] = "FAST"
            elif v <= q2:
                class_of[eid] = "MEDIUM"
            else:
                class_of[eid] = "SLOW"
    for cls in ["FAST", "MEDIUM", "SLOW"]:
        ids = [e for e, c in class_of.items() if c == cls]
        if not ids:
            continue
        finals = np.array([float(net.loc[e, "pnl_bps"]) for e in ids]) / \
            float(net.loc[ids[0], "risk_unit_bps"])
        after, rec = [], []
        for e in ids:
            p = ev_paths[e]
            t = first_passage(p, 0.5)
            if t is not None and np.isfinite(t):
                after.append(float(np.max(p[int(t):])))
                rec.append(float(np.max(p[int(t):]) > 0))
        rows.append({
            "failure_class": cls,
            "n": int(len(ids)),
            "median_reveal_time_h": float(np.median([reveal[e] for e in ids])),
            "median_time_to_worst_mae_h": float(np.median([twm[e] for e in ids])),
            "median_final_loss_R": float(np.median(finals)),
            "mean_final_expectancy_R": float(np.mean(finals)),
            "p95_loss_R": float(np.percentile(finals, 5)),
            "recovery_to_profit_after_0_5R_breach": float(np.mean(rec)) if rec else np.nan,
            "mean_mfe_after_0_5R_breach_R": float(np.mean(after)) if after else np.nan,
        })
    classes = pd.DataFrame(rows)
    out = pd.DataFrame({"event_id": net.index,
                        "failure_class": [class_of.get(e, None) for e in net.index]})
    return classes, out


# ---------------------------------------------------------------------------
# R2.3 — Recovery probability surface
# ---------------------------------------------------------------------------

def _future_stats(paths: pd.DataFrame) -> pd.DataFrame:
    """Per (event, age) observation: state (cum min) + future outcomes.

    Causality: the state uses only information up to age h (running minimum);
    outcomes use the remainder of the frozen path.
    """
    p = paths.copy()
    p["mae_bin"] = mae_bin_of(p["mae_depth_R"].to_numpy(dtype=float))
    p["age_bin"] = age_bin_of(p["age_h"].to_numpy(dtype=float))
    # reverse cumulative max (future max from age h inclusive)
    p = p.sort_values(["event_id", "h_since_entry"])
    p["future_max_R"] = p.groupby("event_id")["net_R"].transform(
        lambda s: s.iloc[::-1].cummax().iloc[::-1])
    p["future_max_mark"] = p.groupby("event_id")["mark_bps"].transform(
        lambda s: s.iloc[::-1].cummax().iloc[::-1])
    p["remaining_R"] = p["final_net_R"] - p["net_R"]
    return p


def recovery_surface(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    """P(win | MAE bin, age bin, family) + remaining-expectancy stats."""
    p = _future_stats(paths)
    fam = ledger.set_index("event_id")["family"].to_dict()
    p["family"] = p["event_id"].map(fam)
    rows = []
    for fam_lbl in ["A", "B", "A+B"]:
        sub = p if fam_lbl == "A+B" else p[p["family"] == fam_lbl]
        for mb in MAE_BIN_LABELS:
            for ab in AGE_BIN_LABELS:
                cell = sub[(sub["mae_bin"] == mb) & (sub["age_bin"] == ab)]
                if len(cell) == 0:
                    continue
                n = len(cell)
                win_ci = percentile_ci(cell["win"].to_numpy(dtype=float), stat="mean")
                rem = cell["remaining_R"].to_numpy(dtype=float)
                rows.append({
                    "family": fam_lbl, "mae_bin": mb, "age_bin": ab,
                    "N": int(n),
                    "exploratory": bool(n < MIN_SUPPORT),
                    "win_probability": win_ci["mean"],
                    "win_ci_low": win_ci["ci_low"], "win_ci_high": win_ci["ci_high"],
                    "final_expectancy_R": float(cell["final_net_R"].mean()),
                    "median_final_return_R": float(cell["final_net_R"].median()),
                    "p_recover_breakeven": float((cell["future_max_R"] > 0).mean()),
                    "p_positive_mfe_after": float((cell["future_max_mark"] > 0).mean()),
                    "expected_remaining_R": float(rem.mean()),
                    "median_remaining_R": float(np.median(rem)),
                })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R2.4 — Recovery cliffs (descriptive, HYPOTHESIS_ONLY)
# ---------------------------------------------------------------------------

def recovery_cliffs(surface: pd.DataFrame) -> str:
    """Broad descriptive zones where recovery collapses / remaining exp < 0."""
    L = []
    a = L.append
    a("# R2.4 — Recovery Cliff Detection (descriptive, HYPOTHESIS_ONLY)")
    a("")
    a("Zones below are descriptive findings, NOT execution logic. A 'cliff' "
      "requires: adequate N (>= 30), a win-probability collapse below 0.35 that "
      "persists in the next-deeper bin, and/or negative remaining expectancy.")
    a("")
    for fam_lbl in ["A", "B", "A+B"]:
        sub = surface[surface["family"] == fam_lbl]
        a(f"## Family {fam_lbl}")
        a("")
        a("| age bin | first MAE bin with win<0.35 (N>=30) | first bin with remaining exp < 0 |")
        a("|---|---|---|")
        for ab in AGE_BIN_LABELS:
            cells = sub[sub["age_bin"] == ab].set_index("mae_bin")
            # find first (shallowest) bin satisfying each condition, in depth order
            win_cliff = None
            exp_cliff = None
            prev_win_low = False
            for mb in MAE_BIN_LABELS:
                if mb not in cells.index:
                    continue
                r = cells.loc[mb]
                if r["N"] < MIN_SUPPORT:
                    continue
                if r["win_probability"] < 0.35 and prev_win_low:
                    win_cliff = mb
                    break
                prev_win_low = r["win_probability"] < 0.35
            for mb in MAE_BIN_LABELS:
                if mb not in cells.index:
                    continue
                r = cells.loc[mb]
                if r["N"] < MIN_SUPPORT:
                    continue
                if r["expected_remaining_R"] < 0 and r["win_probability"] < 0.5:
                    exp_cliff = mb
                    break
            a(f"| {ab} | {win_cliff or '-'} | {exp_cliff or '-'} |")
        a("")
    a("## Reading")
    a("")
    a("A win-cliff marks the state zone beyond which eventual profitable frozen "
      "exits become uncommon; a negative remaining-expectancy zone marks where "
      "capital is, on average, economically spent. Both are HYPOTHESIS_ONLY "
      "inputs for future statistical invalidation research - no stop is created.")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# R2.5 — Tail loss attribution
# ---------------------------------------------------------------------------

def tail_attribution(ledger: pd.DataFrame, paths: pd.DataFrame,
                     ctx: pd.DataFrame) -> pd.DataFrame:
    """Worst 1/2.5/5/10% of trades by final return and by MAE: attributes +
    contribution to total losses / max DD / worst 24h & 48h rolling windows."""
    net = ledger.set_index("event_id")
    per = paths.groupby("event_id").agg(
        mae_R=("net_R", "min"), final_R=("net_R", "last"))
    tab = net.join(per)
    tab["failure_class"] = ctx.set_index("event_id")["failure_class"]
    tab["n_at_entry"] = ctx.set_index("event_id")["n_at_entry"]
    tab["max_concurrent"] = ctx.set_index("event_id")["max_concurrent_during"]
    tab["opp_overlap"] = ctx.set_index("event_id")["opp_dir_overlap"]
    tab["same_overlap"] = ctx.set_index("event_id")["same_dir_overlap"]
    tab["rank_6h"] = ctx.set_index("event_id")["rank_6h"]
    tab["cluster_size_6h"] = ctx.set_index("event_id")["cluster_size_6h"]
    tab["time_to_worst_mae_h"] = ctx.set_index("event_id")["time_to_worst_mae_h"]
    tab["time_to_first_1R_h"] = ctx.set_index("event_id")["time_to_first_1R_h"]
    tab["entry_hour"] = pd.to_datetime(tab["entry_ts"], utc=True).dt.hour
    tab["weekday"] = pd.to_datetime(tab["entry_ts"], utc=True).dt.dayofweek

    # rolling window contributions (chronological, all splits, P0 book)
    eq = tab.sort_values("entry_ts")
    ts = pd.to_datetime(eq["entry_ts"], utc=True)
    pnl = eq["pnl_bps"].to_numpy(dtype=float)
    eq_cum = np.cumsum(pnl)
    peak = np.maximum.accumulate(eq_cum)
    dd = peak - eq_cum
    trough_i = int(np.argmax(dd))
    peak_i = int(np.argmax(eq_cum[:trough_i + 1]))
    dd_window_ids = set(eq.index[peak_i:trough_i + 1])
    dd_share_of_tails = {}

    # hourly pnl series for rolling windows. rolling(k).sum() at t covers
    # [t-(k-1)h, t], so the trade set for the worst k-hour window is
    # [w-k+1, w] (same convention; verified against the trade book).
    h_ser = pd.Series(pnl, index=ts).resample("h").sum().fillna(0.0)
    r24 = h_ser.rolling(24).sum()
    r48 = h_ser.rolling(48).sum()
    worst24_ids, worst48_ids = set(), set()
    if r24.notna().any():
        w24 = r24.idxmin()
        worst24_ids = set(eq.index[(ts >= w24 - pd.Timedelta(hours=23))
                                   & (ts <= w24)])
    if r48.notna().any():
        w48 = r48.idxmin()
        worst48_ids = set(eq.index[(ts >= w48 - pd.Timedelta(hours=47))
                                   & (ts <= w48)])

    rows = []
    for cut_name, col in [("final_return", "final_R"), ("mae", "mae_R")]:
        for q in [0.01, 0.025, 0.05, 0.10]:
            thr = float(tab[col].quantile(q))
            tail = tab[tab[col] <= thr]
            n = len(tail)
            if n == 0:
                continue
            losses = tab[tab["pnl_bps"] < 0]["pnl_bps"].sum()
            tail_loss = tail[tail["pnl_bps"] < 0]["pnl_bps"].sum()
            dd_tail = tail.loc[list(tail.index.intersection(dd_window_ids)), "pnl_bps"]
            w24_tail = tail.loc[list(tail.index.intersection(worst24_ids)), "pnl_bps"]
            w48_tail = tail.loc[list(tail.index.intersection(worst48_ids)), "pnl_bps"]
            rows.append({
                "cut": cut_name, "quantile": q, "threshold": thr, "N": n,
                "pct_of_trades": 100.0 * n / len(tab),
                "mean_final_R": float(tail["final_R"].mean()),
                "mean_mae_R": float(tail["mae_R"].mean()),
                "family_A_share": float((tail["family"] == "A").mean()),
                "mean_entry_hour": float(tail["entry_hour"].mean()),
                "mean_rv_bps_per_h": float(tail["rv_bps_per_h"].mean()),
                "mean_pos": float(tail["pos"].mean()),
                "mean_concurrency_at_entry": float(tail["n_at_entry"].mean()),
                "mean_max_concurrent": float(tail["max_concurrent"].mean()),
                "opp_overlap_rate": float(tail["opp_overlap"].mean()),
                "same_overlap_rate": float(tail["same_overlap"].mean()),
                "mean_episode_rank_6h": float(tail["rank_6h"].mean()),
                "mean_cluster_size_6h": float(tail["cluster_size_6h"].mean()),
                "fast_failure_rate": float((tail["failure_class"] == "FAST").mean()),
                "median_time_to_worst_mae_h": float(tail["time_to_worst_mae_h"].median()),
                "median_time_to_first_1R_h": float(tail["time_to_first_1R_h"].median()),
                "mean_cost_bps": float(tail["cost_bps"].mean()),
                "share_of_total_losses": float(tail_loss / losses) if losses != 0 else np.nan,
                # positive magnitudes: |tail losses| / |max DD| etc.
                "share_of_max_dd_window": float(
                    abs(dd_tail.sum()) / max(abs(dd[trough_i]), 1e-12))
                if trough_i >= peak_i and len(dd_tail) else np.nan,
                "share_of_worst_24h_loss": float(
                    abs(w24_tail.sum()) / max(abs(float(r24.min()))
                                              if r24.notna().any() else 0.0, 1e-12))
                if worst24_ids else np.nan,
                "share_of_worst_48h_loss": float(
                    abs(w48_tail.sum()) / max(abs(float(r48.min()))
                                              if r48.notna().any() else 0.0, 1e-12))
                if worst48_ids else np.nan,
            })
    return pd.DataFrame(rows)
