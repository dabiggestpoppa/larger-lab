"""
Phase 7 - analysis studies (brief sections 2-5).

- P7_PAIR_SPACE_COMPARISON.csv: per (family, pair, hold) win rate, mean/median
  return, MFE, MAE, routing efficiency, cost.
- P7_ENTRY_DELAY_SURFACE.csv: per (family, pair-or-basket, delay, hold) mean net
  return — used to find stable plateaus, not isolated optima.
- P7_EXCURSION_GEOMETRY.csv: MAE/MFE percentiles + time-to-MFE/MAE.
- Mirrored EUR routing model: long (A) vs short (B) symmetry comparison.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_7_execution import routing_efficiency


def pair_space_comparison(g: pd.DataFrame, family: Dict,
                          split: str = "inner_sel") -> pd.DataFrame:
    """Per (pair, hold) summary within one split on oriented returns."""
    sub = g[(g["split"] == split) & (g["delay_h"] == 0)]
    rows = []
    for (p, h), gr in sub.groupby(["pair", "hold_h"]):
        r = gr["dir_return_bps"]
        mfe = gr["dir_mfe_bps"]
        mae = gr["dir_mae_bps"]
        if len(r) == 0:
            continue
        rows.append({
            "family": family["name"], "pair": p, "hold_h": h,
            "n": int(len(r)),
            "mean_return_bps": float(r.mean()),
            "median_return_bps": float(r.median()),
            "win_prob": float((r > 0).mean()),
            "mean_mfe_bps": float(mfe.mean()),
            "mean_mae_bps": float(mae.mean()),
            "mean_cost_bps": float(gr["cost_bps"].mean()),
            "mean_net_bps": float(gr["dir_net_bps"].mean()),
            "routing_efficiency": float(np.mean([
                routing_efficiency(row) for _, row in gr.iterrows()])),
        })
    return pd.DataFrame(rows)


def entry_delay_surface(g: pd.DataFrame, family: Dict,
                        splits: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Per (delay, hold) mean net return (bps) across the family's pairs/basket,
    reported per split. Selection uses inner_sel; inner_val confirms stability.
    """
    splits = splits or ["inner_sel", "inner_val", "untouched"]
    sub = g[g["split"].isin(splits)]
    rows = []
    for (d, h, s), gr in sub.groupby(["delay_h", "hold_h", "split"]):
        rows.append({
            "family": family["name"], "delay_h": int(d), "hold_h": int(h),
            "split": s, "n": int(len(gr)),
            "mean_net_bps": float(gr["dir_net_bps"].mean()),
            "mean_gross_bps": float(gr["dir_return_bps"].mean()),
            "win_prob": float((gr["dir_net_bps"] > 0).mean()),
            "mean_cost_bps": float(gr["cost_bps"].mean()),
        })
    return pd.DataFrame(rows)


def plateau_analysis(surface: pd.DataFrame, family: Dict,
                     split: str = "inner_sel") -> Dict:
    """
    Identify stable plateaus: for each delay, the set of holds with positive
    mean net return; a plateau requires >= 2 positive holds that are
    CONSECUTIVE in the family's candidate hold list (holds may be spaced
    2-12h apart, e.g. Family C 24/36/48/60/72), and the representative hold
    must not be an isolated spike (both neighbors in the run positive).
    """
    sel = surface[surface["split"] == split]
    result = {"family": family["name"], "plateaus": [], "recommended_delay": None,
              "recommended_hold": None}
    cand_holds = sorted(family.get("hold_candidates", []))
    validated_holds = sorted(family.get("horizons", []))
    pos_in_cand = {h: i for i, h in enumerate(cand_holds)}
    for d, gr in sel.groupby("delay_h"):
        gr = gr.sort_values("hold_h")
        positive = gr[gr["mean_net_bps"] > 0]
        if len(positive) >= 2:
            holds = sorted(positive["hold_h"].tolist())
            # consecutive-in-candidates run detection (plateau evidence)
            runs = []
            run = [holds[0]]
            for a, b in zip(holds, holds[1:]):
                ai, bi = pos_in_cand.get(a, -99), pos_in_cand.get(b, -99)
                if bi - ai == 1:  # consecutive in the family hold grid
                    run.append(b)
                else:
                    runs.append(run)
                    run = [b]
            runs.append(run)
            for run_h in runs:
                if len(run_h) >= 2:
                    rep = gr[gr["hold_h"].isin(run_h)]
                    rep_hold = rep.loc[rep["mean_net_bps"].idxmax(), "hold_h"]
                    mean_net = float(rep[rep["hold_h"] == rep_hold]["mean_net_bps"].iloc[0])
                    result["plateaus"].append({
                        "delay_h": int(d), "holds": run_h, "representative_hold": int(rep_hold),
                        "representative_mean_net_bps": mean_net,
                    })
    # Recommended config: best (delay, VALIDATED hold) on inner_sel. The
    # representative must come from the validated envelope (brief section 1:
    # do not treat adjacent validated horizons as independent, and do not
    # extend beyond the validated response envelope).
    best = None
    for d, gr in sel.groupby("delay_h"):
        vh = gr[gr["hold_h"].isin(validated_holds) & (gr["mean_net_bps"] > 0)]
        if len(vh) == 0:
            continue
        vh = vh.sort_values("mean_net_bps", ascending=False)
        row = vh.iloc[0]
        mean_net = float(row["mean_net_bps"])
        if best is None or mean_net > best[0]:
            best = (mean_net, int(d), int(row["hold_h"]))
    if best:
        result["recommended_delay"] = best[1]
        result["recommended_hold"] = best[2]
        result["recommended_mean_net_bps"] = best[0]
    return result


def excursion_geometry(g: pd.DataFrame, family: Dict,
                       split: str = "inner_sel",
                       pair: Optional[str] = None) -> pd.DataFrame:
    """MAE/MFE percentiles + time-to-MFE/MAE for one split (delay=0)."""
    sub = g[(g["split"] == split) & (g["delay_h"] == 0)]
    if pair:
        sub = sub[sub["pair"] == pair]
    rows = []
    for (p, h), gr in sub.groupby(["pair", "hold_h"]):
        mae = gr["dir_mae_bps"].dropna()
        mfe = gr["dir_mfe_bps"].dropna()
        if len(mae) == 0:
            continue
        rows.append({
            "family": family["name"], "pair": p, "hold_h": h, "n": int(len(gr)),
            "mae_p50": float(mae.quantile(0.50)), "mae_p75": float(mae.quantile(0.75)),
            "mae_p90": float(mae.quantile(0.90)), "mae_p95": float(mae.quantile(0.95)),
            "mfe_p50": float(mfe.quantile(0.50)), "mfe_p75": float(mfe.quantile(0.75)),
            "mfe_p90": float(mfe.quantile(0.90)), "mfe_p95": float(mfe.quantile(0.95)),
            "median_time_to_mfe_h": float(gr["time_to_mfe_h"].median()),
            "median_time_to_mae_h": float(gr["time_to_mae_h"].median()),
            "mean_time_to_mfe_h": float(gr["time_to_mfe_h"].mean()),
            "mean_time_to_mae_h": float(gr["time_to_mae_h"].mean()),
        })
    return pd.DataFrame(rows)


def mirrored_symmetry(g_a: pd.DataFrame, g_b: pd.DataFrame,
                      family_a: Dict, family_b: Dict,
                      split: str = "inner_sel") -> pd.DataFrame:
    """
    Family A (long JPY crosses) vs Family B (short JPY crosses): compare effect
    size, timing, MFE, MAE and cost-adjusted expectancy on the SAME pairs.
    """
    a = g_a[g_a["split"] == split]
    b = g_b[g_b["split"] == split]
    rows = []
    for h in sorted(set(a["hold_h"]) & set(b["hold_h"])):
        for p in sorted(set(a["pair"]) & set(b["pair"])):
            ra = a[(a["hold_h"] == h) & (a["pair"] == p) & (a["delay_h"] == 0)]["dir_net_bps"]
            rb = b[(b["hold_h"] == h) & (b["pair"] == p) & (b["delay_h"] == 0)]["dir_net_bps"]
            if len(ra) == 0 or len(rb) == 0:
                continue
            rows.append({
                "pair": p, "hold_h": h,
                "A_long_n": int(len(ra)), "A_long_mean_net_bps": float(ra.mean()),
                "A_long_win": float((ra > 0).mean()),
                "A_long_mfe": float(a[(a["hold_h"] == h) & (a["pair"] == p) & (a["delay_h"] == 0)]["dir_mfe_bps"].mean()),
                "A_long_mae": float(a[(a["hold_h"] == h) & (a["pair"] == p) & (a["delay_h"] == 0)]["dir_mae_bps"].mean()),
                "B_short_n": int(len(rb)), "B_short_mean_net_bps": float(rb.mean()),
                "B_short_win": float((rb > 0).mean()),
                "B_short_mfe": float(b[(b["hold_h"] == h) & (b["pair"] == p) & (b["delay_h"] == 0)]["dir_mfe_bps"].mean()),
                "B_short_mae": float(b[(b["hold_h"] == h) & (b["pair"] == p) & (b["delay_h"] == 0)]["dir_mae_bps"].mean()),
                "asymmetry_ratio": float(ra.mean() / rb.mean()) if rb.mean() != 0 else np.nan,
            })
    return pd.DataFrame(rows)


def basket_surface(g_basket: pd.DataFrame, family: Dict) -> pd.DataFrame:
    """Entry-delay surface restricted to the equal-risk basket rows."""
    return entry_delay_surface(g_basket, family)
