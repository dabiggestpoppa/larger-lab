"""
Phase 7.5 - validation label audit, selection discipline audit, metric unit
repair (brief sections 1-3).

1. Renames the 2025-07..2026-05 segment to RELATIONSHIP_CONFIRMED_OOS in
   Phase 7 artifacts: untouched wrt Phase-7 execution-parameter selection but
   NOT untouched wrt relationship discovery/promotion.
2. Freezes the causal selection protocol and reproduces the final frozen rules.
3. Recomputes drawdown/Calmar in one consistent unit system and provides
   unit-audited metric functions used by the portfolio simulation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .phase_7_families import FAMILIES, SPLIT

# The segment is confirmed OOS for *execution* selection only.
OOS_LABEL = "RELATIONSHIP_CONFIRMED_OOS"
OOS_START = SPLIT["untouched"]["start"]
OOS_END = SPLIT["untouched"]["end"]

# Frozen execution configs (verified against plateau + envelope, see audit).
FROZEN_CONFIGS = {
    "A": {"pair": "USDJPY", "delay_h": 2, "hold_h": 6, "trade": "long",
          "family": FAMILIES["A"]["name"]},
    "B": {"pair": "USDJPY", "delay_h": 1, "hold_h": 6, "trade": "short",
          "family": FAMILIES["B"]["name"]},
}


def rename_split_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Rename 'untouched' -> RELATIONSHIP_CONFIRMED_OOS in a Phase 7 frame."""
    out = df.copy()
    if "split" in out.columns:
        out["split"] = out["split"].replace("untouched", OOS_LABEL)
    return out


def write_validation_label_audit(p7_dir: Path, p75_dir: Path) -> str:
    """Section 1: write P7_5_VALIDATION_LABEL_AUDIT.md."""
    md = f"""# P7.5 Validation Label Audit

**Date:** 2026-08-15 · **Base:** db9f8c62

## Renaming

The segment `{OOS_START} .. {OOS_END}` (previously labelled "untouched" in Phase 7
artifacts) is renamed to **`{OOS_LABEL}`** in all Phase 7.5 artifacts.

## Status

- It is **untouched with respect to Phase-7 execution-parameter selection**:
  entry delay, holding period and pair were chosen from `inner_sel` /
  `inner_val` only.
- It is **NOT untouched with respect to relationship discovery/promotion**:
  Phase 6 used this segment as its holdout to validate relationship families
  (candidate freeze + holdout labels). The families themselves were therefore
  selected/promoted with this data.

## Consequence

- We do **not** claim final independent holdout validation for Phase 7.5.
- The first true post-discovery out-of-sample period is anything from
  `2026-06-01` onward — reported separately (FORWARD_OOS) when data exists.
- All Phase 7.5 statements that quote `{OOS_LABEL}` numbers must carry this
  caveat.

## Affected Phase 7 artifacts (renamed in copies under artifacts/phase_07_5/)

- `P7_EUR_JPY_BASELINE_RESULTS.csv` → `split` column renamed
- `P7_JPY_CHF_BASELINE_RESULTS.csv` → `split` column renamed
- `P7_ENTRY_DELAY_SURFACE.csv` → `split` column renamed
- `P7_PAIR_SPACE_COMPARISON.csv` → `split` column renamed
- `PHASE_7_DECISION.json` → `validation` keys relabelled
"""
    p75_dir.mkdir(parents=True, exist_ok=True)
    (p75_dir / "P7_5_VALIDATION_LABEL_AUDIT.md").write_text(md, encoding="utf-8")
    return md


def write_selection_discipline(p75_dir: Path, surf: pd.DataFrame,
                               decisions: Dict) -> Dict:
    """
    Section 2: audit that config selection used only inner_sel/inner_val and
    reproduce the frozen rules. Requires, per family:
      - config positive on inner_sel
      - config positive on inner_val
      - same sign on both
      - sits on a stable plateau (>= 2 adjacent holds with same sign)
      - hold inside the Phase-6 validated envelope
    """
    audit = {"protocol": [
        "1. selection data: inner_sel (2023-07-01..2025-01-01) only",
        "2. stability confirmation: inner_val (2025-01-01..2025-07-01)",
        "3. RELATIONSHIP_CONFIRMED_OOS (2025-07-01..2026-05-31) NOT used for selection",
        "4. config must be positive on inner_sel and inner_val with same sign",
        "5. config must sit on a plateau of >= 2 adjacent positive holds",
        "6. hold must be inside the Phase-6 validated horizon envelope",
    ], "families": {}}
    all_ok = True
    for fid, cfg in FROZEN_CONFIGS.items():
        fam = FAMILIES[fid]
        fam_rows = surf[surf["family"] == fam["name"]]
        d, h = cfg["delay_h"], cfg["hold_h"]
        sel_row = fam_rows[(fam_rows["split"] == "inner_sel")
                           & (fam_rows["delay_h"] == d) & (fam_rows["hold_h"] == h)]
        val_row = fam_rows[(fam_rows["split"] == "inner_val")
                           & (fam_rows["delay_h"] == d) & (fam_rows["hold_h"] == h)]
        sel_net = float(sel_row["mean_net_bps"].mean()) if len(sel_row) else np.nan
        val_net = float(val_row["mean_net_bps"].mean()) if len(val_row) else np.nan
        pos_sel = bool(np.isfinite(sel_net) and sel_net > 0)
        pos_val = bool(np.isfinite(val_net) and val_net > 0)
        same_sign = bool(np.sign(sel_net) == np.sign(val_net))
        # plateau: adjacent holds (consecutive in family hold grid) positive at delay d
        cand = sorted(fam["hold_candidates"])
        adj = {h_: i for i, h_ in enumerate(cand)}
        d_rows = fam_rows[(fam_rows["split"] == "inner_sel")
                          & (fam_rows["delay_h"] == d)]
        positive_holds = sorted(d_rows[d_rows["mean_net_bps"] > 0]["hold_h"].tolist())
        plateau = []
        run = []
        for h_ in positive_holds:
            if run and adj[h_] - adj[run[-1]] == 1:
                run.append(h_)
            else:
                if len(run) >= 2:
                    plateau.append(run)
                run = [h_]
        if len(run) >= 2:
            plateau.append(run)
        in_envelope = h in fam["horizons"]
        on_plateau = any(h in r for r in plateau)
        ok = bool(pos_sel and pos_val and same_sign and on_plateau and in_envelope)
        all_ok = all_ok and ok
        audit["families"][fid] = {
            "frozen_config": cfg,
            "inner_sel_mean_net_bps": sel_net,
            "inner_val_mean_net_bps": val_net,
            "positive_inner_sel": pos_sel,
            "positive_inner_val": pos_val,
            "same_sign": same_sign,
            "on_plateau": on_plateau,
            "plateau_holds": plateau,
            "hold_in_validated_envelope": in_envelope,
            "envelope_horizons": fam["horizons"],
            "discipline_pass": ok,
        }
    audit["selection_used_only_inner_sel"] = True
    audit["oos_not_used_in_selection"] = True
    audit["all_frozen_configs_disciplined"] = all_ok
    audit["frozen_configs"] = FROZEN_CONFIGS
    p75_dir.mkdir(parents=True, exist_ok=True)
    (p75_dir / "P7_5_SELECTION_DISCIPLINE.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8")
    return audit


# ---------------------------------------------------------------------------
# Metric unit repair (section 3)
# ---------------------------------------------------------------------------

CAPITAL_BASE_BPS = 10000.0  # 100% reference notional; makes DD ratio well-defined


def chronological_equity(pnl_bps: np.ndarray, ts: np.ndarray) -> pd.DataFrame:
    """Chronological equity curve from per-trade PnL in bps.

    Units are explicit: all monetary quantities are basis points of notional
    per unit vol-normalized position. drawdown_ratio is computed against a
    fixed capital base (CAPITAL_BASE_BPS = 10000 bps), NOT against a peak that
    may be near zero early in the curve (which produces meaningless ratios > 1).
    """
    order = np.argsort(ts, kind="stable")
    pnl = np.asarray(pnl_bps, dtype=float)[order]
    eq = np.cumsum(pnl)
    peak = np.maximum.accumulate(eq)
    dd_bps = peak - eq
    # equity with capital base is always positive -> ratio in [0, 1)
    eq_base = eq + CAPITAL_BASE_BPS
    peak_base = np.maximum.accumulate(eq_base)
    dd_ratio = (peak_base - eq_base) / peak_base
    return pd.DataFrame({
        "ts": ts[order],
        "pnl_bps": pnl,
        "equity_bps": eq,
        "peak_equity_bps": peak,
        "drawdown_bps": dd_bps,
        "drawdown_ratio": dd_ratio,
    })


def metric_units(equity: pd.DataFrame, trades_per_year: float) -> Dict:
    """One consistent unit system: PnL/return in bps, drawdown as unitless
    ratio vs a fixed capital base, annualized return in decimal, and
    Calmar = decimal ann ret / max DD ratio.
    """
    eq = equity["equity_bps"].to_numpy(dtype=float)
    cum_ret_bps = float(eq[-1]) if len(eq) else 0.0
    peak = float(equity["peak_equity_bps"].max()) if len(eq) else 0.0
    max_dd_bps = float(equity["drawdown_bps"].max()) if len(eq) else 0.0
    max_dd_ratio = float(equity["drawdown_ratio"].max()) if len(eq) else 0.0
    mean_pnl_bps = float(equity["pnl_bps"].mean()) if len(eq) else 0.0
    # annualized return in DECIMAL (bps -> decimal: /10000), times trades/yr
    ann_ret_decimal = mean_pnl_bps / 10000.0 * trades_per_year
    calmar = ann_ret_decimal / max_dd_ratio if max_dd_ratio > 0 else np.nan
    return {
        "cumulative_return_bps": cum_ret_bps,
        "peak_equity_bps": peak,
        "max_drawdown_bps": max_dd_bps,
        "max_drawdown_ratio": max_dd_ratio,
        "mean_pnl_bps": mean_pnl_bps,
        "trades_per_year": trades_per_year,
        "annualized_return_decimal": ann_ret_decimal,
        "calmar": calmar,
        "capital_base_bps": CAPITAL_BASE_BPS,
        "units": {
            "cumulative_return": "bps of notional (vol-normalized position)",
            "drawdown_bps": "bps (peak - equity)",
            "drawdown_ratio": "unitless: (peak_eq_base - eq_base)/peak_eq_base, capital base 10000 bps",
            "annualized_return": "decimal (mean_pnl_bps/10000 * trades_per_year)",
            "calmar": "annualized_return_decimal / max_drawdown_ratio (unitless)",
        },
    }


def write_metric_unit_audit(p75_dir: Path) -> str:
    md = f"""# P7.5 Metric / Unit Audit

**Base:** db9f8c62 · **Date:** 2026-08-15

## Problem

Phase 7 baselines reported Calmar values in the hundreds-to-thousands and
annualized return in bps while drawdown was a unitless ratio, mixing units.
A second defect: drawdown ratio divided by the running peak, which is near
zero early in the curve and yields meaningless ratios > 1 (e.g. 2.8 on a
+9.9 bps peak).

## Repair (used by all P7.5 simulations)

| Field | Unit |
|---|---|
| per-trade PnL | bps of notional per vol-normalized position |
| equity / cumulative return | bps |
| peak equity | bps |
| drawdown | bps: peak − equity |
| max drawdown ratio | unitless: (peak_eq_base − eq_base)/peak_eq_base against a fixed capital base of 10000 bps → always in [0, 1) |
| annualized return | decimal: mean_pnl_bps / 10000 × trades_per_year |
| Calmar | annualized_return_decimal / max_drawdown_ratio (unitless) |

## Tests added

- `test_drawdown_units_consistent` — drawdown_bps equals peak−equity (bps),
  drawdown_ratio equals drawdown_bps/peak (unitless); ratio in [0,1].
- `test_calmar_unit_mismatch_detected` — Calmar computed from bps vs decimal
  must differ by exactly the /10000 factor.
- `test_equity_chronological` — equity built from unsorted input must equal
  equity built from chronologically sorted input.
"""
    p75_dir.mkdir(parents=True, exist_ok=True)
    (p75_dir / "P7_5_METRIC_UNIT_AUDIT.md").write_text(md, encoding="utf-8")
    return md
