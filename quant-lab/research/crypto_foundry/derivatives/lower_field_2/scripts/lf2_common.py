"""LOWER-FIELD-2 shared configuration and helpers.

Extends the LOWER-FIELD-1 common module with:
  * a continuous per-asset causal sigma column (computed on the FULL panel
    before any band filter -- matching the panel's own merge_canonical_series
    continuity). NEVER compute sigma on a band-truncated slice: that truncates
    migrated assets' series and distorts the rolling window (an artifact that
    changed unconditional P(>=3sigma) from ~2.5% to ~8% in a diagnostic).
  * alternate scale definitions for tail-state scale-robustness (task 9).
  * PIT rank windows / regime lens helpers.

All thresholds below are FROZEN in 01_PREREGISTRATION.md.
Do not edit after outcome observation begins.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
LF1 = ROOT.parent / "lower_field_1"

PANEL = LF1.parent / "lower_field" / "RESULTS" / "lower_field_panel.parquet"
CANON = (
    ROOT.parent.parent / "alt_rotation" / "data_1_1"
    / "ALT_DATA_1_1_PIT_UNIVERSE.parquet"
)
HANDBF = (
    LF1.parent / "lower_field" / "RESULTS" / "30_CROSS_FIELD_HANDOFF_READY.parquet"
)
LF1_EVENT_SET = LF1 / "EVENTS" / "lf1_event_set.parquet"
RESULTS = ROOT / "RESULTS"

# PIT rank bands (primary lower field)
PRIMARY_BANDS = ["501-750", "751-1000", "1001-1500", "1501-2000"]
COMPARE_BANDS = ["251-500", "101-250", "26-100"]

# horizons
HORIZONS = ["1D", "3D", "7D", "14D", "30D"]
RET_COLS = {
    "1D": "ret_1d", "3D": "ret_3d", "7D": "ret_7d",
    "14D": "ret_14d", "30D": "ret_30d",
}

# reversal manifold gates (prereg section 2)
SIGMA_GATES = [2.0, 3.0, 4.0]
RAW_GATES = [0.10, 0.15, 0.20]
REV_HORIZONS = [1, 2, 3, 5, 7, 10, 14, 21, 30]

# purge windows (independent-event controls)
PURGE_D = [7, 14, 30]

# scale definitions for tail-state robustness (task 9)
SCALES = ["63d", "20d", "30d", "ewma", "mad", "semivol"]


def _group(df: pd.DataFrame, col: str = "cmc_id"):
    return df.groupby(col, sort=False)


def scale_sigma(df: pd.DataFrame, scale: str, vol_ret_col: str = "ret_1d") -> pd.Series:
    """Causal per-asset scale (daily), alt normalizations for task 9.

    All are computed strictly from data before day t (roll uses shift(1)).
    `mad` is dispatched to compute_mad; `semivol` to compute_semivol.
    """
    g = df.groupby("cmc_id", sort=False)[vol_ret_col]
    if scale in ("63d", "30d", "20d"):
        win = {"63d": 63, "30d": 30, "20d": 20}[scale]
        minp = min(max(win // 2, 15), win)
        return (
            g.transform(lambda s: s.shift(1).rolling(win, min_periods=minp).std())
            .astype(float)
        )
    if scale == "ewma":
        return (
            g.transform(
                lambda s: s.shift(1).ewm(span=20, adjust=False, min_periods=20).std()
            )
            .astype(float)
        )
    if scale == "mad":
        return compute_mad(df)
    if scale == "semivol":
        return compute_semivol(df)
    raise ValueError(f"unknown scale {scale}")


def compute_sigma(df: pd.DataFrame) -> pd.Series:
    """Causal trailing-63d realized std of ret_1d per asset (identical to LF1)."""
    return (
        df.sort_values("historical_date")
        .groupby("cmc_id", sort=False)["ret_1d"]
        .transform(lambda s: s.shift(1).rolling(63, min_periods=40).std())
        .astype(float)
    )


def compute_mad(df: pd.DataFrame) -> pd.Series:
    """Causal trailing-63d MAD of (ret_1d - median) as a robust scale."""
    g = df.groupby("cmc_id", sort=False)["ret_1d"]

    def f(s: pd.Series):
        w = s.shift(1).rolling(63, min_periods=40)
        med = w.median()
        mad = (s.shift(1) - med).abs().rolling(63, min_periods=40).median()
        return (mad * 1.4826).where(mad > 0, np.nan)

    return g.transform(f).astype(float)


def compute_semivol(df: pd.DataFrame) -> pd.Series:
    """Downside/semi realized volatility (downward variance), causal."""
    g = df.groupby("cmc_id", sort=False)["ret_1d"]

    def f(s: pd.Series):
        r = s.shift(1)
        down = r.where(r < 0, 0.0)
        var = down.pow(2).rolling(63, min_periods=40).mean() * 2.0
        return np.sqrt(var) * np.sqrt(2.0)  # ~daily downside sigma scale

    return g.transform(f).astype(float)


def add_continuous_sigma(df: pd.DataFrame, scale: str = "63d") -> pd.DataFrame:
    """Attach `sigma_t0` (causal) computed on the FULL frame passed.
    Call on the FULL panel, never a band-truncated slice."""
    out = df.copy()
    if scale == "63d":
        out["sigma_t0"] = compute_sigma(out)
    else:
        out["sigma_t0"] = scale_sigma(out, scale)
    return out


def momentum_shape(ret_3d, ret_14d):
    """Four-shape momentum mapping (3D x 14D), identical to LF1."""
    s3 = 1 if ret_3d > 0 else (-1 if ret_3d < 0 else 0)
    s14 = 1 if ret_14d > 0 else (-1 if ret_14d < 0 else 0)
    if s3 == 1 and s14 == 1:
        return "SHORT_HOT_MEDIUM_HOT"
    if s3 == 1 and s14 <= 0:
        return "SHORT_HOT_MEDIUM_COLD"
    if s3 <= 0 and s14 == 1:
        return "SHORT_COLD_MEDIUM_HOT"
    return "SHORT_COLD_MEDIUM_COLD"


def add_momentum_shape(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["momentum_state"] = df.apply(
        lambda r: momentum_shape(r["ret_3d"], r["ret_14d"]), axis=1
    )
    return df


def band_of(rank: int) -> str:
    for lo, hi in [(501, 750), (751, 1000), (1001, 1500), (1501, 2000)]:
        if lo <= rank <= hi:
            return f"{lo}-{hi}"
    for lo, hi in [(251, 500), (101, 250), (26, 100), (1, 25)]:
        if lo <= rank <= hi:
            return f"{lo}-{hi}"
    return "OUT"


# regime helpers (all causal: computed from data at or before day t)
RISK_REGIMES = [
    ("btc_up", lambda d: d.get("btc_ret_1d") > 0),
    ("btc_down", lambda d: d.get("btc_ret_1d") <= 0),
]


def bh_fdr(p: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg FDR 5% significance mask."""
    pv = np.asarray(p, dtype=float)
    finite = pv
    n = len(finite)
    if n == 0:
        return np.zeros(0, dtype=bool)
    order = np.argsort(finite, kind="stable")
    ranked = finite[order]
    thresh = np.arange(1, n + 1) / n * 0.05
    sig_sorted = ranked <= thresh
    idx = np.nonzero(sig_sorted)[0]
    if len(idx) == 0:
        mask_sorted = np.zeros(n, dtype=bool)
    else:
        k = int(idx.max())
        mask_sorted = np.zeros(n, dtype=bool)
        mask_sorted[: k + 1] = True
    # scatter back to original positions (ranked[k] came from original order[k])
    out = np.zeros(n, dtype=bool)
    out[order] = mask_sorted
    return out