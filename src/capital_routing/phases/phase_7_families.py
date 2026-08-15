"""
Phase 7 - relationship families and alpha promotion gate (brief sections 1-2).

Freezes the Phase 6 VALIDATED relationships into three economic families and
evaluates the ALPHA_PROMOTION_GATE criteria. Phase 6's phase_6_gate.json remains
the RESEARCH_GATE (untouched).

Criteria (all must hold for promotion):
  1. same holdout sign as development
  2. holdout effect >= 50% of development effect
  3. holdout bootstrap CI (fixed seed, event-level resampling) excludes zero
  4. adequate holdout N (>= 100)
  5. no material collapse under overlap cooldowns (6h/12h/24h vs all events)
  6. no dependence on one exact horizon (assessed from Phase 7 hold-sweep in the
     orchestrator: >= 2 validated adjacent horizons, or a plateau for Family C)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_6_stats import non_overlapping_mask

TASK = "CR-P7-ROUTING-TRANSLATION-01"
PHASE6_COMMIT = "5726bf02"

# ---------------------------------------------------------------------------
# Frozen families (from Phase 6 VALIDATED holdout labels)
# ---------------------------------------------------------------------------
# direction: the trade expression direction relative to the pair's base currency
FAMILIES: Dict[str, Dict] = {
    "A": {
        "name": "EUR_ACCUMULATION_JPY_WEAKNESS",
        "description": "EUR ACCUMULATION -> JPY relative weakness",
        "origin": "EUR",
        "direction": "ACCUMULATION",
        "destination": "JPY",
        "horizons": [6, 8, 12],
        "envelope": "6-12h",
        "pairs": ["EURJPY", "USDJPY", "GBPJPY", "CHFJPY"],
        "basket_pairs": ["EURJPY", "USDJPY", "GBPJPY", "CHFJPY"],
        "trade": "long",  # JPY weakens -> JPY crosses rise
        "hold_candidates": [4, 6, 8, 12],
    },
    "B": {
        "name": "EUR_LIQUIDATION_JPY_STRENGTH",
        "description": "EUR LIQUIDATION -> JPY relative strength",
        "origin": "EUR",
        "direction": "LIQUIDATION",
        "destination": "JPY",
        "horizons": [4, 6, 8, 12],
        "envelope": "4-12h",
        "pairs": ["EURJPY", "USDJPY", "GBPJPY", "CHFJPY"],
        "basket_pairs": ["EURJPY", "USDJPY", "GBPJPY", "CHFJPY"],
        "trade": "short",  # JPY strengthens -> JPY crosses fall
        "hold_candidates": [4, 6, 8, 12],
    },
    "C": {
        "name": "JPY_LIQUIDATION_CHF_STRENGTH",
        "description": "JPY LIQUIDATION -> CHF relative strength",
        "origin": "JPY",
        "direction": "LIQUIDATION",
        "destination": "CHF",
        "horizons": [48],
        "envelope": "~48h",
        "pairs": ["CHFJPY", "USDCHF", "EURCHF", "GBPCHF"],
        "basket_pairs": ["CHFJPY", "USDCHF", "EURCHF", "GBPCHF"],
        "trade": "long_chf",  # CHF strong: long CHFJPY, short CHF-quote pairs
        "hold_candidates": [24, 36, 48, 60, 72],
    },
}

# One-way transaction cost in basis points of price (spread half + commission proxy).
# Documented research assumptions for H1 event-driven FX; no broker feed is used.
ONE_WAY_COST_BPS = {
    "EURUSD": 0.6, "GBPUSD": 0.7, "USDJPY": 0.6, "USDCHF": 0.8,
    "EURGBP": 0.8, "EURJPY": 0.8, "GBPJPY": 1.0, "CHFJPY": 0.9,
    "EURCHF": 0.9, "GBPCHF": 1.0,
}

# Proxy annual policy-rate differentials (2026 snapshot) for swap/carry on
# Family C's multi-day holds: swap_bps_per_day = (r_base - r_quote)/365*10000.
# Real broker swap differs; this is a documented research proxy.
PROXY_RATES = {"EUR": 2.0, "USD": 3.75, "GBP": 3.75, "CHF": 1.0, "JPY": 0.5}


def swap_bps_per_day(pair: str) -> float:
    """Carry per day in bps for holding pair LONG (base vs quote).

    rate diff in percent points -> bps/year (*100) -> per day (/365).
    E.g. GBP vs JPY 3.25% = 325 bps/yr = 0.89 bps/day.
    """
    base, quote = pair[:3], pair[3:]
    return (PROXY_RATES[base] - PROXY_RATES[quote]) * 100.0 / 365.0


# Nested chronological split (brief section 8). Selection happens ONLY inside
# inner_sel; inner_val confirms stability; the untouched Phase 6 holdout is
# evaluated once after rules freeze.
SPLIT = {
    "inner_sel": {"start": "2023-07-01", "end": "2025-01-01"},
    "inner_val": {"start": "2025-01-01", "end": "2025-07-01"},
    "untouched": {"start": "2025-07-01", "end": "2026-06-01"},
}

HOLDOUT_N_MIN = 100
BOOTSTRAP_SEED = 20260715
BOOTSTRAP_ITERS = 500
FAMILY_CI_ALPHA = 0.10  # two-sided -> 90% CI


def _bootstrap_effect_ci(values: np.ndarray, seed: int = BOOTSTRAP_SEED,
                         iters: int = BOOTSTRAP_ITERS) -> Dict[str, float]:
    """Bootstrap CI on effect = mean/std (event-level resampling, fixed seed)."""
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    rng = np.random.default_rng(seed)
    n = len(v)
    lo, hi = np.percentile([1.0, 100.0 - 1.0], [0, 0])  # placeholder, unused
    if n < 10:
        return {"n": int(n), "effect": np.nan, "ci_low": np.nan, "ci_high": np.nan}
    eff = float(v.mean() / v.std(ddof=1))
    boots = np.empty(iters)
    for i in range(iters):
        s = v[rng.integers(0, n, size=n)]
        sd = s.std(ddof=1)
        boots[i] = s.mean() / sd if sd > 0 else np.nan
    boots = boots[np.isfinite(boots)]
    alpha = FAMILY_CI_ALPHA
    if len(boots) == 0:
        ci_lo, ci_hi = np.nan, np.nan
    else:
        ci_lo, ci_hi = np.percentile(boots, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"n": int(n), "effect": eff, "ci_low": float(ci_lo), "ci_high": float(ci_hi)}


def load_phase6_evidence(p6_dir: Path) -> Dict[str, pd.DataFrame]:
    """Load Phase 6 holdout results, overlap sensitivity and forward factors."""
    ho = pd.read_csv(p6_dir / "holdout_results.csv")
    ov = pd.read_csv(p6_dir / "overlap_sensitivity.csv")
    cf = pd.read_parquet(p6_dir / "event_forward_currency_factors.parquet")
    return {"holdout": ho, "overlap": ov, "factors": cf}


def _family_candidates(family: Dict, ho: pd.DataFrame) -> pd.DataFrame:
    """The Phase 6 candidates belonging to a family (origin/direction/destination)."""
    f = ho[
        (ho["origin"] == family["origin"])
        & (ho["direction"] == family["direction"])
        & (ho["destination"] == family["destination"])
    ]
    return f


def evaluate_static_criteria(family: Dict, ho: pd.DataFrame, ov: pd.DataFrame,
                             cf: pd.DataFrame) -> Dict:
    """Criteria 1-5 from Phase 6 evidence only."""
    fam = _family_candidates(family, ho)
    n_horizons = len(fam)
    horizon_rows = []
    for _, r in fam.iterrows():
        horizon_rows.append({
            "horizon_h": int(r["horizon_h"]),
            "dev_n": int(r["dev_n"]),
            "dev_effect": float(r["dev_effect"]),
            "holdout_n": int(r["holdout_n"]),
            "holdout_effect": float(r["holdout_effect"]),
            "holdout_label": str(r["holdout_label"]),
        })

    valid = fam[fam["holdout_label"] == "VALIDATED"]
    checks = {}

    # criterion 1: same holdout sign as development (per validated horizon)
    sign_ok = bool((valid["holdout_effect"] * valid["dev_effect"] > 0).all()) \
        if len(valid) else False
    checks["1_same_holdout_sign"] = {
        "pass": sign_ok,
        "detail": "all validated horizons same sign on holdout"
        if sign_ok else "sign mismatch present",
    }

    # criterion 2: holdout effect >= 50% dev effect
    if len(valid):
        ratio = (valid["holdout_effect"].abs() / valid["dev_effect"].abs()).min()
        c2 = bool(ratio >= 0.5)
    else:
        ratio, c2 = np.nan, False
    checks["2_holdout_effect_50pct"] = {
        "pass": c2, "min_holdout_dev_ratio": float(ratio) if np.isfinite(ratio) else None,
    }

    # criterion 3: bootstrap CI on the effect from holdout forward factors
    ts = pd.to_datetime(cf["event_start"], utc=True)
    hold_mask = (ts >= SPLIT["untouched"]["start"]) & (ts < SPLIT["untouched"]["end"])
    sub = cf[
        hold_mask
        & (cf["origin_currency"] == family["origin"])
        & (cf["direction"] == family["direction"])
    ]
    ci_results = {}
    c3_ok = True
    for h in family["horizons"]:
        col = f"{family['destination']}_forward_{h}h"
        if col not in sub.columns:
            c3_ok = False
            ci_results[str(h)] = {"error": f"missing column {col}"}
            continue
        ci = _bootstrap_effect_ci(sub[col].to_numpy(dtype=float))
        ci_results[str(h)] = ci
        excl = bool(ci["ci_low"] > 0 or ci["ci_high"] < 0)
        c3_ok = c3_ok and excl
    checks["3_bootstrap_ci_excludes_zero"] = {
        "pass": c3_ok, "per_horizon": ci_results,
    }

    # criterion 4: adequate holdout N
    min_n = int(valid["holdout_n"].min()) if len(valid) else 0
    checks["4_adequate_holdout_n"] = {
        "pass": bool(min_n >= HOLDOUT_N_MIN), "min_holdout_n": min_n,
        "threshold": HOLDOUT_N_MIN,
    }

    # criterion 5: no material collapse under overlap cooldowns.
    #   Recompute the destination effect on NON-OVERLAPPING event subsets
    #   (cooldown 6/12/24h, deterministic first-in-block) vs all events.
    #   Pass requires: same sign as all-events AND |effect| >= 50% of all-events
    #   for every cooldown at every validated horizon.
    sub = cf[
        (cf["origin_currency"] == family["origin"])
        & (cf["direction"] == family["direction"])
    ].copy()
    rows = []
    ok = True
    worst_ratio = 1.0
    for h in family["horizons"]:
        col = f"{family['destination']}_forward_{h}h"
        if col not in sub.columns:
            ok = False
            rows.append({"horizon_h": h, "error": f"missing {col}"})
            continue
        base = sub[col].to_numpy(dtype=float)
        base = base[np.isfinite(base)]
        base_eff = float(base.mean() / base.std(ddof=1)) if len(base) >= 10 else np.nan
        for cd in [6, 12, 24]:
            mask = non_overlapping_mask(sub, cd)
            v = sub.loc[mask, col].to_numpy(dtype=float)
            v = v[np.isfinite(v)]
            eff = float(v.mean() / v.std(ddof=1)) if len(v) >= 10 else np.nan
            if not np.isfinite(base_eff) or not np.isfinite(eff) or abs(base_eff) < 1e-12:
                ratio = np.nan
                ok = False
            else:
                ratio = eff / base_eff
                if np.sign(eff) != np.sign(base_eff) or abs(ratio) < 0.5:
                    ok = False
                worst_ratio = min(worst_ratio, abs(ratio))
            rows.append({"horizon_h": h, "cooldown_h": cd, "n": int(len(v)),
                         "effect": eff, "ratio_vs_all": ratio})
    checks["5_overlap_cooldown_stability"] = {
        "pass": ok, "rows": rows,
        "worst_ratio_vs_all_events": float(worst_ratio) if np.isfinite(worst_ratio) else None,
        "note": "effect recomputed on non-overlapping subsets (6/12/24h cooldowns); "
                "same sign and >=50% magnitude required",
    }

    return {
        "family": family["name"],
        "trade": family["trade"],
        "envelope": family["envelope"],
        "n_validated_horizons": int(len(valid)),
        "horizon_rows": horizon_rows,
        "checks": checks,
        "static_pass": bool(all(c["pass"] for c in checks.values())),
    }


def evaluate_overlap_all(family: Dict, ho: pd.DataFrame, ov: pd.DataFrame,
                         cf: pd.DataFrame) -> Dict:
    """Full static evaluation across all families (helper for the gate)."""
    return evaluate_static_criteria(family, ho, ov, cf)


def build_families_json(p6_dir: Path, out_dir: Path) -> Dict:
    """Write P7_RELATIONSHIP_FAMILIES.json with family definitions + static gate."""
    ev = load_phase6_evidence(p6_dir)
    families_out = []
    for fid, family in FAMILIES.items():
        fam = _family_candidates(family, ev["holdout"])
        validated = fam[fam["holdout_label"] == "VALIDATED"]
        families_out.append({
            "family_id": fid,
            "name": family["name"],
            "description": family["description"],
            "origin": family["origin"],
            "direction": family["direction"],
            "destination": family["destination"],
            "trade_expression": family["trade"],
            "validated_horizons": family["horizons"],
            "envelope": family["envelope"],
            "candidate_pairs": family["pairs"],
            "basket_pairs": family["basket_pairs"],
            "hold_candidates": family["hold_candidates"],
            "holdout_candidates": [
                {
                    "horizon_h": int(r["horizon_h"]),
                    "dev_effect": float(r["dev_effect"]),
                    "holdout_effect": float(r["holdout_effect"]),
                    "holdout_label": str(r["holdout_label"]),
                }
                for _, r in validated.iterrows()
            ],
            "static_alpha_gate": evaluate_static_criteria(family, ev["holdout"],
                                                          ev["overlap"], ev["factors"]),
        })
    payload = {
        "phase": "7",
        "task": TASK,
        "phase6_commit": PHASE6_COMMIT,
        "note": "Frozen Phase 6 VALIDATED relationships clustered by economic family. "
                "Adjacent horizons are ONE family, not independent alphas.",
        "split": SPLIT,
        "costs": {"one_way_bps": ONE_WAY_COST_BPS,
                  "swap": "proxy policy-rate differentials; see swap_bps_per_day()"},
        "families": families_out,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "P7_RELATIONSHIP_FAMILIES.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8")
    return payload
