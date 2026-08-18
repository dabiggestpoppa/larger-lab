"""B2 audit computations: coverage, missingness, extreme events,
triangular FX parity, and cross-series identity checks.

All of these are data-quality diagnostics. None evaluates strategy
behavior or PnL.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def coverage_rows(panel: pd.DataFrame, assets: list) -> list:
    rows = []
    n = len(panel)
    for asset in assets:
        obs = panel[f"{asset}.observed"].sum()
        closed = panel[f"{asset}.expected_closed"].sum()
        stale = panel[f"{asset}.stale"].sum()
        missing = (panel[f"{asset}.missing_reason"] == "UNEXPECTED_MISSING").sum()
        stale_gt2 = (panel[f"{asset}.stale_age_hours"] > 2).sum()
        # K1/K3 usability: requires W and I state not stale > 2h at that slot.
        w_stale = panel["W.stale_age_hours"] > 2
        i_stale = panel["I.stale_age_hours"] > 2
        usable = (~(w_stale | i_stale)).sum()
        rows.append({
            "asset": asset,
            "total_canonical_slots": n,
            "valid_observed": int(obs),
            "stale_carried": int(stale),
            "expected_closed": int(closed),
            "unexpected_missing": int(missing),
            "bad": 0,
            "stale_gt_2h": int(stale_gt2),
            "usable_K1_K3": int(usable),
        })
    return rows


def missingness_rows(panel: pd.DataFrame, assets: list) -> list:
    rows = []
    for asset in assets:
        sub = panel[["canonical_ny", f"{asset}.missing_reason", f"{asset}.observed",
                     f"{asset}.stale_age_hours"]].copy()
        sub = sub.rename(columns={
            f"{asset}.missing_reason": "missing_reason",
            f"{asset}.observed": "observed",
            f"{asset}.stale_age_hours": "stale_age_hours",
        })
        counts = sub["missing_reason"].value_counts().to_dict()
        rows.append({
            "asset": asset,
            "expected_closed": int(counts.get("EXPECTED_CLOSED", 0)),
            "unexpected_missing": int(counts.get("UNEXPECTED_MISSING", 0)),
            "observed": int(sub["observed"].sum()),
            "max_stale_age_hours": float(sub["stale_age_hours"].max()) if len(sub) else 0.0,
            "p99_stale_age_hours": float(sub["stale_age_hours"].quantile(0.99)) if len(sub) else 0.0,
            "unexpected_missing_days": sorted(
                {d.isoformat() for d in sub.loc[sub["missing_reason"] == "UNEXPECTED_MISSING",
                                                 "canonical_ny"].dt.date.unique()}
            )[:20],
        })
    return rows


def extreme_event_rows(frame: pd.DataFrame, threshold_quantile: float = 0.999) -> list:
    """Flag extreme H1 log returns as REAL / ROLL / BAD_PRINT / UNRESOLVED.

    Without roll metadata, large discontinuities cannot be confirmed as
    rolls; they are flagged UNRESOLVED (never auto-deleted).
    """
    ret = np.log(frame["close"]).diff()
    threshold = float(ret.abs().quantile(threshold_quantile))
    extremes = ret[ret.abs() >= threshold].dropna()
    rows = []
    for ts, r in extremes.items():
        rows.append({
            "timestamp_utc": ts.isoformat(),
            "log_return": float(r),
            "abs_return": float(abs(r)),
            "flag": "UNRESOLVED",  # no roll metadata available; never auto-classified
            "note": "extreme H1 move; roll metadata absent so REAL vs ROLL unresolved",
        })
    return sorted(rows, key=lambda r: -r["abs_return"])


def cross_series_identity(frame_a: pd.DataFrame, frame_b: pd.DataFrame) -> dict:
    """Return-correlation and price-identity check between two series."""
    ra = np.log(frame_a["close"]).diff()
    rb = np.log(frame_b["close"]).diff()
    common = ra.index.intersection(rb.index)
    if len(common) < 100:
        return {"common_bars": int(len(common)), "corr": None,
                "note": "insufficient overlap"}
    corr = float(ra.loc[common].corr(rb.loc[common]))
    price_match = float((np.abs(frame_a.loc[common, "close"].to_numpy()
                               - frame_b.loc[common, "close"].to_numpy()) < 1e-9).mean())
    return {
        "common_bars": int(len(common)),
        "return_corr": round(corr, 6),
        "exact_price_match_fraction": round(price_match, 6),
    }


def triangular_parity(e: pd.DataFrame, c: pd.DataFrame, ec: pd.DataFrame,
                      interval: str = "5min") -> pd.DataFrame:
    """FX triangular parity diagnostic (data quality only).

    r_synth = r_EURUSD + r_USDCAD  vs  r_direct = r_EURCAD.
    residual = r_direct - r_synth; report distribution and extremes.
    """
    re = np.log(e["close"]).diff()
    rc = np.log(c["close"]).diff()
    rec = np.log(ec["close"]).diff()
    common = re.index.intersection(rc.index).intersection(rec.index)
    out = pd.DataFrame({
        "r_eurusd": re.loc[common],
        "r_usdcad": rc.loc[common],
        "r_eurcad_direct": rec.loc[common],
    }).dropna()
    out["r_synth_ec"] = out["r_eurusd"] + out["r_usdcad"]
    out["residual"] = out["r_eurcad_direct"] - out["r_synth_ec"]
    q = out["residual"].quantile([0.0, 0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99, 1.0])
    stats = {
        "n": int(len(out)),
        "interval": interval,
        "mean": float(out["residual"].mean()),
        "std": float(out["residual"].std()),
        "quantiles": {str(k): float(v) for k, v in q.items()},
        "abs_residual_gt_1e_4": int((out["residual"].abs() > 1e-4).sum()),
        "abs_residual_gt_1e_3": int((out["residual"].abs() > 1e-3).sum()),
    }
    extremes = out.loc[out["residual"].abs() >= out["residual"].abs().quantile(0.999)].copy()
    return out, stats, extremes
