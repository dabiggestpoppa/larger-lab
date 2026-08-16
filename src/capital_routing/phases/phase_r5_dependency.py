"""
CR-RISK-BLOCK2 R5 — Family dependency structure (VIII).

Multiple lenses over the MERGED chronological book (never naive row-wise
correlation of non-simultaneous trades):

1. same-hour / same-day realized PnL correlation (realized PnL lands at exit)
2. rolling 90-day calendar PnL correlation
3. event-overlap conditional dependence (A entry while B position open, etc.)
4. loss coincidence P(B loss | A loss) with causal alignment
5. tail coincidence P(B tail loss | A tail loss)
6. 12h-episode co-occurrence (R1 clusters containing both families)
7. same-direction / opposing overlap hours (R1 concurrency summary)

All descriptive. No allocation or strategy change.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from .phase_r2_context import assign_cluster_ranks


def _daily_frame(ledger: pd.DataFrame) -> pd.DataFrame:
    tb = ledger.copy()
    tb["exit_d"] = pd.to_datetime(tb["exit_ts"], utc=True).dt.date
    d = tb.groupby("exit_d").apply(
        lambda g: pd.Series({
            "A": float(g.loc[g.family == "A", "pnl_bps"].sum()),
            "B": float(g.loc[g.family == "B", "pnl_bps"].sum()),
        }), include_groups=False).reset_index()
    return d


def _loss_days(d: pd.DataFrame, col: str) -> set:
    return set(d.loc[d[col] < 0, "exit_d"])


def _tail_days(d: pd.DataFrame, col: str) -> set:
    vals = d[col]
    thr = float(np.quantile(vals, 0.10)) if len(vals) else 0.0
    return set(d.loc[vals <= thr, "exit_d"])


def _cond(a: set, b: set, universe: set) -> float:
    if not a:
        return np.nan
    return float(len(a & b) / len(a & universe)) if len(a & universe) else np.nan


def _overlap_at_entry(ledger: pd.DataFrame, fam: str) -> pd.DataFrame:
    """For each fam event: count open positions of the OTHER family at entry."""
    tb = ledger.sort_values("entry_ts").reset_index(drop=True)
    other = tb[tb["family"] != fam]
    rows = []
    e0 = pd.to_datetime(tb.loc[tb.family == fam, "entry_ts"], utc=True)
    o0 = pd.to_datetime(other["entry_ts"], utc=True)
    o1 = pd.to_datetime(other["exit_ts"], utc=True)
    for eid, t in zip(tb.loc[tb.family == fam, "event_id"], e0):
        n_open = int(((o0 < t) & (o1 > t)).sum())
        rows.append((eid, n_open))
    return pd.DataFrame(rows, columns=["event_id", "n_other_open"])


def dependency_structure(ledger: pd.DataFrame,
                         risk1_dir: Path) -> pd.DataFrame:
    rows = []

    # --- 1/2. same-hour and same-day realized PnL correlation ---
    tb = ledger.copy()
    tb["exit_h"] = pd.to_datetime(tb["exit_ts"], utc=True).dt.floor("h")
    hourly = tb.groupby("exit_h").apply(
        lambda g: pd.Series({
            "A": float(g.loc[g.family == "A", "pnl_bps"].sum()),
            "B": float(g.loc[g.family == "B", "pnl_bps"].sum()),
        }), include_groups=False).reset_index()
    h_nonzero = hourly[(hourly["A"] != 0) | (hourly["B"] != 0)]
    corr_h = float(h_nonzero["A"].corr(h_nonzero["B"])) if len(h_nonzero) > 2 else np.nan

    daily = _daily_frame(ledger)
    d_nonzero = daily[(daily["A"] != 0) | (daily["B"] != 0)]
    corr_d = float(d_nonzero["A"].corr(d_nonzero["B"])) if len(d_nonzero) > 2 else np.nan

    # --- 3. rolling 90-day correlation ---
    d = daily.set_index("exit_d").sort_index()
    roll = d["A"].rolling(90).corr(d["B"])
    rolling_vals = roll.dropna()
    corr_roll = float(rolling_vals.mean()) if len(rolling_vals) else np.nan

    # --- 4/5. loss + tail coincidence (daily, causal alignment) ---
    A_days = set(daily["exit_d"])
    lA, lB = _loss_days(daily, "A"), _loss_days(daily, "B")
    tA, tB = _tail_days(daily, "A"), _tail_days(daily, "B")
    base_B_loss = float(len(lB) / len(A_days)) if A_days else np.nan
    base_A_loss = float(len(lA) / len(A_days)) if A_days else np.nan
    p_bloss_given_aloss = _cond(lA, lB, A_days)
    p_aloss_given_bloss = _cond(lB, lA, A_days)
    p_btail_given_atal = _cond(tA, tB, A_days)
    p_atal_given_btail = _cond(tB, tA, A_days)

    # --- 6. overlap conditional dependence ---
    ovA = _overlap_at_entry(ledger, "A")
    ovB = _overlap_at_entry(ledger, "B")
    r_R = ledger["pnl_bps"] / ledger["risk_unit_bps"]
    fam_of = dict(zip(ledger["event_id"], ledger["family"]))
    r_of = dict(zip(ledger["event_id"], r_R))
    for f_, ov in [("A", ovA), ("B", ovB)]:
        ov["loss"] = ov["event_id"].map(r_of) < 0
        base = float(ov["loss"].mean())
        with_ov = ov[ov["n_other_open"] > 0]
        no_ov = ov[ov["n_other_open"] == 0]
        rows.append({
            "metric": f"{f_}_loss_rate_with_other_open",
            "value": float(with_ov["loss"].mean()) if len(with_ov) else np.nan,
            "base_rate": base, "N": int(len(with_ov)),
        })
        rows.append({
            "metric": f"{f_}_loss_rate_without_other_open",
            "value": float(no_ov["loss"].mean()) if len(no_ov) else np.nan,
            "base_rate": base, "N": int(len(no_ov)),
        })

    # --- 7. 12h-episode co-occurrence ---
    ranks = assign_cluster_ranks(ledger, 12.0)
    fam = ledger.set_index("event_id")["family"]
    cl = pd.DataFrame({"event_id": ranks["event_id"], "cluster": ranks["cluster_id"]})
    cl["family"] = cl["event_id"].map(fam)
    n_cl = cl.groupby("cluster")["family"].apply(lambda s: set(s))
    a_mixed = sum(1 for s in n_cl if "A" in s and "B" in s)
    a_clusters = sum(1 for s in n_cl if "A" in s)
    n_a_events = int((cl.family == "A").sum())
    a_in_mixed = int(cl[(cl.family == "A") & (cl.cluster.map(n_cl).map(lambda s: "B" in s))].shape[0])

    # --- 8. overlap hours from R1 concurrency summary ---
    conc = pd.read_csv(risk1_dir / "R1_CONCURRENCY_SUMMARY.csv").iloc[0]
    overlap_hours = {
        "A_A_overlap_hours": int(conc["A_A_overlap_hours"]),
        "B_B_overlap_hours": int(conc["B_B_overlap_hours"]),
        "A_B_overlap_hours": int(conc["A_B_overlap_hours"]),
        "same_direction_overlap_hours": int(conc["same_direction_overlap_hours"]),
        "opposite_direction_overlap_hours": int(conc["opposite_direction_overlap_hours"]),
    }

    summary = [
        ("same_hour_realized_pnl_corr", corr_h, np.nan, len(h_nonzero)),
        ("same_day_realized_pnl_corr", corr_d, np.nan, len(d_nonzero)),
        ("rolling_90d_daily_corr_mean", corr_roll, np.nan, len(rolling_vals)),
        ("P_B_loss_day", base_B_loss, np.nan, len(A_days)),
        ("P_A_loss_day", base_A_loss, np.nan, len(A_days)),
        ("P_B_loss_given_A_loss", p_bloss_given_aloss, base_B_loss, len(lA)),
        ("P_A_loss_given_B_loss", p_aloss_given_bloss, base_A_loss, len(lB)),
        ("P_B_tail_loss_given_A_tail_loss", p_btail_given_atal, base_B_loss, len(tA)),
        ("P_A_tail_loss_given_B_tail_loss", p_atal_given_btail, base_A_loss, len(tB)),
        ("A_share_in_12h_mixed_clusters", a_in_mixed / n_a_events if n_a_events else np.nan,
         np.nan, n_a_events),
        ("share_12h_clusters_with_both_families",
         a_mixed / len(n_cl) if len(n_cl) else np.nan, np.nan, len(n_cl)),
    ]
    for m, v, base, n in summary:
        rows.append({"metric": m, "value": v, "base_rate": base, "N": int(n)})

    df = pd.DataFrame(rows)
    df.attrs["overlap_hours"] = overlap_hours
    df.attrs["corr_same_hour"] = corr_h
    df.attrs["corr_same_day"] = corr_d
    return df
