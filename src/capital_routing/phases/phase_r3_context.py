"""
CR-RISK-BLOCK1 R3 — Profit Anatomy (R3.8-R3.10, R3.12, R3.13 context).

R3.8 A vs B profit signature (delivery speed, capture, giveback)
R3.9 concurrency and profit delivery (overlap groups)
R3.10 episode rank and profit delivery (3h/6h/12h clusters)
R3.12 temporal profit stability (inner_sel / inner_val / RELATIONSHIP_CONFIRMED_OOS)
R3.13 profit delivery curve (by hour: open PnL, % of final earned, winners
     positive / past MFE, remaining expected gain)

All descriptive; no family weighting, TP, early exit, or sizing change.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .phase_r1_episodes import INTERVALS_H
from .phase_r2_common import SPLITS, first_passage_positive, per_event_paths, time_to_mfe
from .phase_r2_context import assign_cluster_ranks
from .phase_r3_analysis import _per_trade

EPISODE_INTERVALS = [3.0, 6.0, 12.0]


def _merge_per_trade(ledger: pd.DataFrame, paths: pd.DataFrame,
                     ctx: pd.DataFrame) -> pd.DataFrame:
    per = _per_trade(paths)
    per["tt_mfe_h"] = per["tt_mfe"] + 1.0
    tab = ledger.set_index("event_id")[["family", "pnl_bps", "risk_unit_bps",
                                        "entry_ts"]].join(per)
    tab["final_R"] = tab["pnl_bps"] / tab["risk_unit_bps"]
    tab["capture"] = np.where(tab["mfe_R"] > 0, tab["final_R"] / tab["mfe_R"], np.nan)
    tab["giveback_R"] = tab["mfe_R"] - tab["final_R"]
    if ctx is not None:
        tab = tab.join(ctx.set_index("event_id"))
    return tab


# ---------------------------------------------------------------------------
# R3.8 — A vs B profit signature
# ---------------------------------------------------------------------------

def family_profit_comparison(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    tab = _merge_per_trade(ledger, paths, None)
    ev_paths = per_event_paths(paths)
    rows = []
    for fid in ["A", "B"]:
        sub = tab[tab["family"] == fid]
        t05 = []
        for eid in sub.index:
            t = first_passage_positive(ev_paths[eid], 0.5)
            if t is not None and np.isfinite(t):
                t05.append(t)
        cap = sub.loc[sub["final_R"] > 0, "capture"].dropna()
        # late-hold contribution: share of final PnL earned after hour 3
        p3 = paths[paths["h_since_entry"] == 2].set_index("event_id")["net_R"]
        late = []
        for eid in sub.index:
            if eid in p3.index and float(sub.loc[eid, "final_R"]) > 0:
                pnl_at_3 = float(p3.loc[eid])
                late.append((float(sub.loc[eid, "final_R"]) - pnl_at_3)
                            / float(sub.loc[eid, "final_R"]))
        rows.append({
            "family": fid, "N": int(len(sub)),
            "median_mfe_R": float(np.median(sub["mfe_R"])),
            "p90_mfe_R": float(np.percentile(sub["mfe_R"], 90)),
            "p95_mfe_R": float(np.percentile(sub["mfe_R"], 95)),
            "median_time_to_first_0_5R_h": float(np.median(t05)) if t05 else np.nan,
            "median_time_to_mfe_h": float(np.median(sub["tt_mfe_h"])),
            "median_capture_ratio_winners": float(np.median(cap)) if len(cap) else np.nan,
            "median_giveback_R": float(np.median(sub["giveback_R"])),
            "remaining_expectancy_at_h3_R": float(np.mean(
                sub["final_R"] - p3.reindex(sub.index).to_numpy(dtype=float))),
            "late_hold_share_of_winner_pnl": float(np.mean(late)) if late else np.nan,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R3.9 — Concurrency and profit delivery
# ---------------------------------------------------------------------------

def concurrency_profit_effects(ledger: pd.DataFrame, paths: pd.DataFrame,
                               ctx: pd.DataFrame) -> pd.DataFrame:
    tab = _merge_per_trade(ledger, paths, ctx)
    rows = []

    def _row(label: str, sub: pd.DataFrame):
        if len(sub) == 0:
            return
        cap = sub.loc[sub["final_R"] > 0, "capture"].dropna()
        rows.append({
            "group": label, "N": int(len(sub)),
            "median_mfe_R": float(np.median(sub["mfe_R"])),
            "median_time_to_mfe_h": float(np.median(sub["tt_mfe_h"])),
            "final_expectancy_R": float(np.mean(sub["final_R"])),
            "median_giveback_R": float(np.median(sub["giveback_R"])),
            "median_capture_winners": float(np.median(cap)) if len(cap) else np.nan,
        })

    _row("no_overlap", tab[~tab["same_dir_overlap"] & ~tab["opp_dir_overlap"]])
    _row("same_dir_overlap_any", tab[tab["same_dir_overlap"]])
    _row("opp_dir_overlap_any", tab[tab["opp_dir_overlap"]])
    _row("A_A_overlap", tab[tab["A_A_overlap"]])
    _row("B_B_overlap", tab[tab["B_B_overlap"]])
    _row("A_B_overlap", tab[tab["A_B_overlap"]])
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R3.10 — Episode rank and profit delivery
# ---------------------------------------------------------------------------

def episode_profit_effects(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    tab = _merge_per_trade(ledger, paths, None)
    rows = []
    for iv in EPISODE_INTERVALS:
        ranks = assign_cluster_ranks(ledger, iv)
        sub = tab.join(ranks.set_index("event_id"))
        for rb in ["1", "2", "3", "4+"]:
            g = sub[sub["rank_in_cluster"] == int(rb)] if rb != "4+" \
                else sub[sub["rank_in_cluster"] >= 4]
            if len(g) == 0:
                continue
            cap = g.loc[g["final_R"] > 0, "capture"].dropna()
            rows.append({
                "interval_h": iv, "rank_in_cluster": rb, "N": int(len(g)),
                "median_mfe_R": float(np.median(g["mfe_R"])),
                "median_time_to_mfe_h": float(np.median(g["tt_mfe_h"])),
                "final_expectancy_R": float(np.mean(g["final_R"])),
                "median_capture_winners": float(np.median(cap)) if len(cap) else np.nan,
                "median_giveback_R": float(np.median(g["giveback_R"])),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R3.12 — Temporal profit stability
# ---------------------------------------------------------------------------

def temporal_profit_stability(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    tab = _merge_per_trade(ledger, paths, None)
    tab = tab.join(ledger.set_index("event_id")[["split"]])
    rows = []
    for sp in SPLITS:
        sub = tab[tab["split"] == sp]
        if len(sub) == 0:
            continue
        cap = sub.loc[sub["final_R"] > 0, "capture"].dropna()
        pos = sub[sub["final_R"] > 0]
        top5 = pos[pos["final_R"] >= pos["final_R"].quantile(0.95)]
        rows.append({
            "split": sp, "N": int(len(sub)),
            "median_mfe_R": float(np.median(sub["mfe_R"])),
            "median_time_to_mfe_h": float(np.median(sub["tt_mfe_h"])),
            "median_capture_winners": float(np.median(cap)) if len(cap) else np.nan,
            "median_giveback_R": float(np.median(sub["giveback_R"])),
            "remaining_expectancy_at_h3_R": float(np.mean(
                sub["final_R"] - paths[paths["h_since_entry"] == 2]
                .set_index("event_id")["net_R"].reindex(sub.index).to_numpy(dtype=float))),
            "winner_tail5_share": float(top5["final_R"].sum() / pos["final_R"].sum())
            if len(pos) else np.nan,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# R3.13 — Profit delivery curve
# ---------------------------------------------------------------------------

def profit_delivery_curve(ledger: pd.DataFrame, paths: pd.DataFrame) -> pd.DataFrame:
    p = paths.copy()
    fam = ledger.set_index("event_id")["family"].to_dict()
    p["family"] = p["event_id"].map(fam)
    p["win"] = p["event_id"].map(ledger.set_index("event_id")["pnl_bps"]) > 0
    p["final_net_R"] = p["event_id"].map(
        paths.groupby("event_id")["net_R"].last())
    argmax_h = paths.groupby("event_id")[["h_since_entry", "net_R"]].apply(
        lambda g: float(np.argmax(g.sort_values("h_since_entry")["net_R"].to_numpy())))
    p["argmax_h"] = p["event_id"].map(argmax_h)
    final_sum = float(p.drop_duplicates("event_id")["final_net_R"].sum())
    rows = []
    for age in range(6):  # h_since_entry 0..5 -> hour 1..6
        s = p[p["h_since_entry"] == age]
        if len(s) == 0:
            continue
        winners = s[s["win"]]
        rows.append({
            "hour": int(age + 1),
            "N": int(len(s)),
            "avg_open_pnl_R": float(s["net_R"].mean()),
            "median_open_pnl_R": float(s["net_R"].median()),
            "pct_of_final_pnl_achieved": float(s["net_R"].sum() / final_sum)
            if final_sum != 0 else np.nan,
            "pct_winners_currently_positive": float((winners["net_R"] > 0).mean())
            if len(winners) else np.nan,
            "pct_winners_past_mfe": float((winners["h_since_entry"] > winners["argmax_h"]).mean())
            if len(winners) else np.nan,
            "remaining_expected_gain_R": float(
                (s["final_net_R"] - s["net_R"]).mean()),
        })
    return pd.DataFrame(rows)
