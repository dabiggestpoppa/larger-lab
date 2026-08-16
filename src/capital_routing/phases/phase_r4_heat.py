"""
CR-RISK-BLOCK1 R4 — Account heat translation (R4.10).

Uses the R1 exposure-truth layer (per-hour portfolio heat + CAE from the sealed
ledger) to translate concurrency states into account-level exposure at each
static fraction:

- gross / net R exposure per concurrency state (1 / 2 same-dir / 2 opposing /
  3 positions)
- historical worst portfolio adverse excursion (R1 portfolio CAE) and its
  account-equity impact at each f
- worst unrealized gain / loss at each f
- effective risk during 2- and 3-position overlap (gross R x f)

Opposing positions are NOT treated as riskless: gross heat and opposing heat
are reported side by side.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from .phase_r4_common import LADDER_PCT, RISK_UNIT_BPS


def account_heat_map(ledger: pd.DataFrame, heat: pd.DataFrame) -> pd.DataFrame:
    h = heat.copy()
    h["ts"] = pd.to_datetime(h["ts"], utc=True)
    # state labels by position count + direction mix
    h["state"] = np.select(
        [h["n_open"] == 1,
         (h["n_open"] == 2) & (h["long_heat"] > 0) & (h["short_heat"] > 0),
         h["n_open"] == 2,
         h["n_open"] >= 3],
        ["1_position", "2_opposing", "2_same_dir", "3_positions"],
        default="0_position")
    worst_cae_R = float(h["portfolio_cae_bps"].max() / RISK_UNIT_BPS)
    worst_unreal = float(h["unrealized_pnl_bps"].min() / RISK_UNIT_BPS)
    best_unreal = float(h["unrealized_pnl_bps"].max() / RISK_UNIT_BPS)

    state_rows = []
    for state, g in h.groupby("state"):
        state_rows.append({
            "state": state, "hours": int(len(g)),
            "pct_of_hours": float(len(g) / len(h)),
            "gross_R_median": float(np.median(g["gross_heat"]) / RISK_UNIT_BPS),
            "gross_R_p95": float(np.percentile(g["gross_heat"], 95) / RISK_UNIT_BPS),
            "gross_R_max": float(g["gross_heat"].max() / RISK_UNIT_BPS),
            "net_R_median": float(np.median(g["abs_net_heat"]) / RISK_UNIT_BPS),
            "net_R_max": float(g["abs_net_heat"].max() / RISK_UNIT_BPS),
            "opposing_R_max": float(g["opposing_heat"].max() / RISK_UNIT_BPS),
            "same_dir_R_max": float(g["same_dir_heat"].max() / RISK_UNIT_BPS),
        })
    states = pd.DataFrame(state_rows)

    rows = []
    for f_pct in LADDER_PCT:
        f = f_pct / 100.0
        rows.append({
            "f_pct": f_pct,
            "worst_CAE_R": worst_cae_R,
            "worst_CAE_account_pct": worst_cae_R * f * 100.0,
            "worst_unrealized_R": worst_unreal,
            "worst_unrealized_account_pct": worst_unreal * f * 100.0,
            "best_unrealized_R": best_unreal,
            "effective_risk_1pos_pct": f_pct,
            "effective_risk_2pos_same_dir_pct": 2.0 * f_pct,
            "effective_risk_2pos_opposing_pct": 2.0 * f_pct,
            "effective_risk_3pos_pct": 3.0 * f_pct,
            "max_gross_R_exposure": float(h["n_open"].max()),
            "max_net_R_exposure": float(h["abs_net_heat"].max() / RISK_UNIT_BPS),
            "max_same_dir_R": float(h["same_dir_heat"].max() / RISK_UNIT_BPS),
            "max_opposing_R": float(h["opposing_heat"].max() / RISK_UNIT_BPS),
        })
    return {"states": states, "per_f": pd.DataFrame(rows)}
