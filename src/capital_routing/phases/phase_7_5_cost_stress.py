"""
Phase 7.5 - realistic cost stress (brief section 5).

Stress the modeled cost multiplier at 1.0x/1.25x/1.50x/2.00x/3.00x and report
the break-even multiplier. Costs modeled: spread, commission, entry slippage,
exit slippage (all folded into the per-trade cost_bps, scaled together).
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from .phase_7_5_audit import FROZEN_CONFIGS, OOS_LABEL, chronological_equity, metric_units

COST_MULTIPLIERS = [1.0, 1.25, 1.5, 2.0, 3.0]


def stress_costs(trades: pd.DataFrame, multipliers: List[float] = None) -> pd.DataFrame:
    """
    For each family (A, B, A+B) and each cost multiplier, compute expectancy,
    win rate, PF on the frozen-config trades (all splits labelled, but selection
    of the CONFIG already happened; here we report dev + OOS separately by the
    split column present in trades).
    """
    multipliers = multipliers or COST_MULTIPLIERS
    rows = []
    for grp_name, grp in _groups(trades).items():
        for mult in multipliers:
            pnl = grp["gross_pnl_bps"].to_numpy(dtype=float) - \
                mult * grp["cost_pnl_bps"].to_numpy(dtype=float)
            n = len(pnl)
            if n == 0:
                rows.append({"group": grp_name, "cost_multiplier": mult, "n": 0})
                continue
            rows.append({
                "group": grp_name, "cost_multiplier": mult, "n": n,
                "expectancy_bps": float(pnl.mean()),
                "win_rate": float((pnl > 0).mean()),
                "profit_factor": float(pnl[pnl > 0].sum() / abs(pnl[pnl < 0].sum()))
                if (pnl < 0).any() and pnl[pnl < 0].sum() != 0 else np.nan,
                "total_return_bps": float(pnl.sum()),
            })
    df = pd.DataFrame(rows)
    # break-even multiplier per group: largest multiplier with expectancy > 0,
    # interpolated linearly between grid points
    for grp_name in _groups(trades).keys():
        sub = df[df["group"] == grp_name].sort_values("cost_multiplier")
        be = None
        prev = None
        for _, r in sub.iterrows():
            if r["expectancy_bps"] <= 0:
                if prev is not None and prev["expectancy_bps"] > 0:
                    # linear interpolation
                    m0, e0 = prev["cost_multiplier"], prev["expectancy_bps"]
                    m1, e1 = r["cost_multiplier"], r["expectancy_bps"]
                    be = m0 + (m1 - m0) * e0 / (e0 - e1)
                elif prev is None:
                    be = 0.0
                break
            prev = r
        if be is None and len(sub):
            be = float(sub["cost_multiplier"].max())
        df.loc[df["group"] == grp_name, "break_even_multiplier"] = be
    return df


def _groups(trades: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    a = trades[trades["family"] == "A"]
    b = trades[trades["family"] == "B"]
    return {"A": a, "B": b, "A+B": trades}
