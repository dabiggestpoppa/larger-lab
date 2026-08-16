"""
CR-RISK-BLOCK1 R1.4 — Routing Episode Clustering (descriptive only).

Multiple signals near each other may be manifestations of the same routing
episode. Grouping intervals tested: 30m, 60m, 2h, 3h, 6h, 12h.

Clustering rule (deterministic, greedy): sort events chronologically; a new
cluster starts when the gap to the PREVIOUS event exceeds the interval
(consecutive-gap chaining). Documented, no tuning, no sizing change.

Per cluster: events, family mix, same/opposite-family pairs, total PnL, average
pairwise correlation of hourly mark paths, cluster MFE / MAE.

Conditional question: is the conditional expectancy of 2nd/3rd events different
from the 1st within a cluster (per grouping interval)?
"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np
import pandas as pd

INTERVALS_H: List[float] = [0.5, 1.0, 2.0, 3.0, 6.0, 12.0]
RANK_BUCKETS = [1, 2, 3, "4+"]


def _pair_count(n: int) -> int:
    return max(n * (n - 1) // 2, 0)


def cluster_events(ledger: pd.DataFrame, marks: pd.DataFrame,
                   interval_h: float) -> pd.DataFrame:
    """Cluster events by consecutive-gap chaining at the given interval."""
    t = ledger.sort_values("event_ts").reset_index(drop=True)
    ts = pd.to_datetime(t["event_ts"], utc=True)
    gap = ts.diff()
    new_cluster = gap.isna() | (gap > pd.Timedelta(hours=interval_h))
    t["cluster_id"] = new_cluster.cumsum() - 1
    t["rank_in_cluster"] = t.groupby("cluster_id").cumcount() + 1

    # average pairwise correlation of hourly mark paths within each cluster
    piv = marks.pivot_table(index="event_id", columns="h_since_entry",
                            values="mark_bps") if len(marks) else pd.DataFrame()

    rows = []
    for cid, gr in t.groupby("cluster_id"):
        n = len(gr)
        nA = int((gr["family"] == "A").sum())
        nB = int((gr["family"] == "B").sum())
        same_pairs = _pair_count(nA) + _pair_count(nB)
        opp_pairs = nA * nB
        corr = _avg_pairwise_corr(piv, gr["event_id"].tolist())
        rows.append({
            "interval_h": interval_h,
            "cluster_id": int(cid),
            "n_events": n,
            "n_A": nA, "n_B": nB,
            "same_family_pairs": same_pairs,
            "opposite_family_pairs": opp_pairs,
            "first_ts": gr["event_ts"].min(),
            "last_ts": gr["event_ts"].max(),
            "span_h": float((pd.to_datetime(gr["event_ts"].max(), utc=True)
                             - pd.to_datetime(gr["event_ts"].min(), utc=True)).total_seconds() / 3600.0),
            "total_cluster_pnl_bps": float(gr["pnl_bps"].sum()),
            "avg_event_correlation": corr,
            "cluster_mfe_bps": float(gr["dir_mfe_bps"].max()),
            "cluster_mae_bps": float(gr["dir_mae_bps"].min()),
            "event_ids": ";".join(gr["event_id"].tolist()),
        })
    out = pd.DataFrame(rows)
    out["events_per_cluster"] = out["n_events"]
    return out


def _avg_pairwise_corr(piv: pd.DataFrame, event_ids: List[str]) -> float:
    sub = piv.loc[[e for e in event_ids if e in piv.index]]
    if len(sub) < 2 or sub.shape[1] < 2:
        return np.nan
    vals = sub.to_numpy(dtype=float)
    corrs = []
    for i in range(len(vals)):
        for j in range(i + 1, len(vals)):
            a, b = vals[i], vals[j]
            if np.std(a) == 0 or np.std(b) == 0 or not (np.isfinite(a).all() and np.isfinite(b).all()):
                continue
            corrs.append(float(np.corrcoef(a, b)[0, 1]))
    if not corrs:
        return np.nan
    return float(np.mean(corrs))


def multi_event_share(episodes: pd.DataFrame, interval_h: float,
                      n_total: int) -> float:
    """Share of raw events belonging to a cluster containing >= 2 events.

    Definition (documented): only events whose cluster has at least 2 members
    count as 'multi-event'; singletons do not. This is NOT the same as
    sum(n_events)/n_total (which is always 1.0 because clusters partition the
    events). Returns 0.0 when n_total <= 0.
    """
    if n_total <= 0:
        return 0.0
    sub = episodes[episodes["interval_h"] == interval_h]
    multi = sub[sub["n_events"] > 1]
    return float(multi["n_events"].sum()) / float(n_total)


def rank_bucket(r: int) -> str:
    if r <= 3:
        return str(r)
    return "4+"


def conditional_results(ledger: pd.DataFrame, marks: pd.DataFrame) -> pd.DataFrame:
    """Per interval x within-cluster rank: N, expectancy, win rate.

    Answers: do 2nd/3rd events in a cluster carry the same conditional
    expectancy as the 1st (independence) or not (duplication)?
    """
    rows = []
    for interval_h in INTERVALS_H:
        t = ledger.sort_values("event_ts").reset_index(drop=True)
        ts = pd.to_datetime(t["event_ts"], utc=True)
        gap = ts.diff()
        new_cluster = gap.isna() | (gap > pd.Timedelta(hours=interval_h))
        t["cluster_id"] = new_cluster.cumsum() - 1
        t["rank"] = t.groupby("cluster_id").cumcount() + 1
        t["rank_bucket"] = t["rank"].map(rank_bucket)
        for rb, gr in t.groupby("rank_bucket"):
            pnl = gr["pnl_bps"].to_numpy(dtype=float)
            rows.append({
                "interval_h": interval_h, "rank_in_cluster": rb,
                "n": int(len(gr)),
                "mean_net_pnl_bps": float(pnl.mean()),
                "median_net_pnl_bps": float(np.median(pnl)),
                "win_rate": float((pnl > 0).mean()),
                "std_bps": float(pnl.std(ddof=1)) if len(pnl) > 1 else np.nan,
            })
    return pd.DataFrame(rows)


def independence_verdict(cond: pd.DataFrame) -> dict:
    """Descriptive verdict per interval: do later ranks differ from rank 1?"""
    out = {}
    for interval_h in INTERVALS_H:
        sub = cond[cond["interval_h"] == interval_h]
        r1 = sub[sub["rank_in_cluster"] == "1"]
        if len(r1) == 0:
            out[str(interval_h)] = {"verdict": "insufficient", "detail": "no rank-1 events"}
            continue
        base = float(r1["mean_net_pnl_bps"].iloc[0])
        detail = []
        for _, r in sub.iterrows():
            if r["rank_in_cluster"] == "1":
                continue
            diff = float(r["mean_net_pnl_bps"]) - base
            detail.append({"rank": r["rank_in_cluster"], "n": int(r["n"]),
                           "expectancy_bps": float(r["mean_net_pnl_bps"]),
                           "diff_vs_rank1_bps": diff})
        verdict = "later ranks differ materially" if any(
            abs(d["diff_vs_rank1_bps"]) > 3.0 and d["n"] >= 30 for d in detail) \
            else "later ranks consistent with rank 1 (or too small to judge)"
        out[str(interval_h)] = {"verdict": verdict, "rank1_expectancy_bps": base,
                                "ranks": detail}
    return out
