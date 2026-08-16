"""
CR-RISK-BLOCK1 R4 — Risk envelopes, static profile zones, account translation
(R4.12, R4.14, R4.13).

R4.12 RISK ENVELOPES: the maximum f satisfying each explicit constraint at each
edge state (100/75/50%):
    SURVIVAL       P(DD >= 50%) <= 5%
    AGGRESSIVE     P(DD >= 40%) <= 10%
    VERY_AGGRESSIVE P(DD >= 40%) <= 30%
    PROP           P(DD >= 10%) <= 5%
The maximum-geometric-growth f is reported alongside (reference, not a
recommendation). Nothing is called "safe" - these are research envelopes.

R4.14 ZONES (data-driven from the MC block-bootstrap frontier, not arbitrary):
    RM-S0 PRESERVATION  max f with P(DD >= 10%) <= 5%
    RM-S1 CONSERVATIVE  max f with P(DD >= 20%) <= 5%
    RM-S2 BALANCED      max f with P(DD >= 30%) <= 10%
    RM-S3 GROWTH        max f with P(DD >= 40%) <= 10%
    RM-S4 FULL PRESS    max f with P(DD >= 40%) <= 30%
If two zones map to the same f, the frontier is steep there - reported as-is.

R4.13 ACCOUNT TRANSLATION: dollar value of 1R and of -0.5/-1/-2/-3/-3.66R (A
worst) / -3.31R (B worst) at each zone's f, on $5k-$100k accounts, plus the
sealed expectancy gain and typical 2-position gross risk. Educational only.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from .phase_r4_common import EDGE_STATES, LADDER_PCT

ACCOUNTS = [5000.0, 10000.0, 25000.0, 50000.0, 100000.0]

ENVELOPE_CONSTRAINTS = {
    "SURVIVAL": ("P_dd_ge_50", 0.05),
    "AGGRESSIVE": ("P_dd_ge_40", 0.10),
    "VERY_AGGRESSIVE": ("P_dd_ge_40", 0.30),
    "PROP": ("P_dd_ge_10", 0.05),
}


def risk_envelopes(edge_mc: pd.DataFrame) -> pd.DataFrame:
    """Max f satisfying each constraint at each edge state. Input is the edge-
    degradation MC frame (rows carry edge_pct + P_dd_ge_* + exp_cagr)."""
    rows = []
    for edge_pct in [100, 75, 50]:
        sub = edge_mc[edge_mc["edge_pct"] == edge_pct]
        for env, (col, bound) in ENVELOPE_CONSTRAINTS.items():
            ok = sub[sub[col] <= bound]
            f_max = float(ok["f_pct"].max()) if len(ok) else 0.0
            row = {"edge_pct": edge_pct, "envelope": env, "max_f_pct": f_max,
                   "constraint": col, "bound": bound}
            # probabilities actually observed at the chosen f
            if len(ok):
                r = ok[ok["f_pct"] == f_max].iloc[0]
                for col2 in ["P_dd_ge_10", "P_dd_ge_20", "P_dd_ge_30",
                             "P_dd_ge_40", "P_dd_ge_50", "P_technical_ruin"]:
                    row[col2] = float(r[col2])
                row["exp_cagr"] = float(r["exp_cagr"])
            rows.append(row)
        # reference: max geometric growth f at this edge
        if len(sub):
            best = sub.loc[sub["exp_cagr"].idxmax()]
            rows.append({"edge_pct": edge_pct, "envelope": "MAX_GEOMETRIC_GROWTH",
                         "max_f_pct": float(best["f_pct"]),
                         "constraint": "none", "bound": np.nan,
                         "P_dd_ge_40": float(best["P_dd_ge_40"]),
                         "P_dd_ge_50": float(best["P_dd_ge_50"]),
                         "P_technical_ruin": float(best["P_technical_ruin"]),
                         "exp_cagr": float(best["exp_cagr"])})
    return pd.DataFrame(rows)


def static_zones(mc: pd.DataFrame) -> pd.DataFrame:
    """Data-driven RM-S0..S4 zone definitions from the block-bootstrap MC."""
    mc_b = mc[mc["scheme"] == "block"]
    rules = [
        ("RM-S0_PRESERVATION", "P_dd_ge_10", 0.05),
        ("RM-S1_CONSERVATIVE", "P_dd_ge_20", 0.05),
        ("RM-S2_BALANCED", "P_dd_ge_30", 0.10),
        ("RM-S3_GROWTH", "P_dd_ge_40", 0.10),
        ("RM-S4_FULL_PRESS", "P_dd_ge_40", 0.30),
    ]
    rows = []
    for zone, col, bound in rules:
        ok = mc_b[mc_b[col] <= bound]
        if len(ok) == 0:
            rows.append({"zone": zone, "f_pct": np.nan, "constraint": col,
                         "bound": bound, "note": "no ladder point satisfies"})
            continue
        f = float(ok["f_pct"].max())
        r = ok[ok["f_pct"] == f].iloc[0]
        rows.append({
            "zone": zone, "f_pct": f, "constraint": col, "bound": bound,
            "exp_cagr": float(r["exp_cagr"]),
            "median_cagr": float(r["cagr_p50"]),
            "p95_max_dd": float(r["max_dd_p95"]),
            "P_dd_ge_10": float(r["P_dd_ge_10"]),
            "P_dd_ge_20": float(r["P_dd_ge_20"]),
            "P_dd_ge_40": float(r["P_dd_ge_40"]),
            "P_dd_ge_50": float(r["P_dd_ge_50"]),
            "P_technical_ruin": float(r["P_technical_ruin"]),
        })
    return pd.DataFrame(rows)


def account_translation(zones: pd.DataFrame, ledger: pd.DataFrame) -> pd.DataFrame:
    """Dollar translation of the zone fractions on $5k-$100k accounts."""
    exp_R = float((ledger["pnl_bps"] / ledger["risk_unit_bps"]).mean())
    a_worst = float((ledger[ledger["family"] == "A"]["pnl_bps"]
                     / ledger[ledger["family"] == "A"]["risk_unit_bps"]).min())
    b_worst = float((ledger[ledger["family"] == "B"]["pnl_bps"]
                     / ledger[ledger["family"] == "B"]["risk_unit_bps"]).min())
    rows = []
    for _, z in zones.iterrows():
        f = z["f_pct"] / 100.0
        if np.isnan(f):
            continue
        for acct in ACCOUNTS:
            one_r = f * acct
            rows.append({
                "zone": z["zone"], "f_pct": z["f_pct"], "account_usd": acct,
                "dollar_1R": one_r,
                "impact_minus_0_5R": -0.5 * one_r,
                "impact_minus_1R": -one_r,
                "impact_minus_2R": -2.0 * one_r,
                "impact_minus_3R": -3.0 * one_r,
                "impact_A_worst_minus_3_66R": a_worst * one_r,
                "impact_B_worst_minus_3_31R": b_worst * one_r,
                "expected_event_gain": exp_R * one_r,
                "typical_2pos_gross_risk": 2.0 * one_r,
                "typical_3pos_gross_risk": 3.0 * one_r,
            })
    return pd.DataFrame(rows)
