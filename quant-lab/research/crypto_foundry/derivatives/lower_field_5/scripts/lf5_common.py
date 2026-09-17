"""LOWER-FIELD-5 shared configuration and causal helpers.

LF5 Stage A rebuilds the PIT asset-date substrate from the RAW top-2000
snapshots (ranks 1-2000) instead of the band-truncated LF2 cache. All
rolling/state features are computed on continuous per-asset histories BEFORE
any rank-band filtering. This fixes the LF4 infrastructure gap that left
correlation peers, future rank-health clocks, and comparison-band research
DATA_BLOCKED.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
LF1 = ROOT.parent / "lower_field"
LF2 = ROOT.parent / "lower_field_2"
LF3 = ROOT.parent / "lower_field_3"
MECH8 = ROOT.parent.parent / "alt_rotation" / "mech_8"
DATA11 = ROOT.parent.parent / "alt_rotation" / "data_1_1"

RAW = LF1 / "DATA_TRUTH" / "raw"
LF2_CACHE = LF2 / "RESULTS" / "lf2_feature_frame.parquet"
TERRAIN = DATA11 / "ALT_DATA_1_1_MARKET_TERRAIN_V2.parquet"
FEATURES_V2 = DATA11 / "ALT_DATA_1_1_ASSET_MULTISCALE_FEATURES_V2.parquet"
MECH8_CTX = MECH8 / "20_CROSS_AGENT_FIELD_CONTEXT_MECH8.parquet"

CACHE = ROOT / "cache"
CACHE.mkdir(exist_ok=True)
RAW_PANEL = CACHE / "pit_raw_panel.parquet"       # parsed ranks 1-2000, identity+mkt fields
SUBSTRATE = ROOT / "04_PIT_ASSET_DATE_FEATURES.parquet"
RETURNS_LONG = ROOT / "PIT_RETURNS_LONG.parquet"
RETURNS_WIDE = CACHE / "pit_returns_wide.parquet"

# PIT rank bands (primary lower field + comparison upper field)
PRIMARY_BANDS = ["501-750", "751-1000", "1001-1500", "1501-2000"]
COMPARE_BANDS = ["26-100", "101-250", "251-500"]
TOP_BANDS = ["1-25"]
ALL_BANDS = TOP_BANDS + COMPARE_BANDS + PRIMARY_BANDS

H = [1, 2, 3, 5, 7, 10, 14, 21, 30]
RET_H = [1, 3, 7, 14, 30, 60]
FWD = {h: f"fwd{h}_cum" for h in H}
RANK_H = [1, 3, 7, 14, 30, 60]

# MECH-8 frozen breadth/dispersion medians (see alt_mech_8_analysis.py)
BRD_MED = 0.31
DISP_MED = 0.307

STABLE_TAGS = {
    "stablecoin", "stablecoin-asset-backed", "stablecoin-algorithmically-stabilized",
    "asset-backed-stablecoin", "usd-stablecoin", "algorithmic-stablecoin",
    "eur-stablecoin", "fiat-stablecoin", "stablecoin-protocol",
}
STABLE_SYMS = {"USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP", "FDUSD",
               "USDE", "PYUSD", "GUSD", "LUSD", "FRAX", "USTC", "UST",
               "EURS", "USDD", "USD1"}


def band_of(rank) -> str:
    for lo, hi in [(1, 25), (26, 100), (101, 250), (251, 500),
                   (501, 750), (751, 1000), (1001, 1500), (1501, 2000)]:
        if lo <= rank <= hi:
            return f"{lo}-{hi}"
    return "OUT"


def finite(s):
    return pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan)


def safe_mean(s):
    x = finite(s).dropna()
    return float(x.mean()) if len(x) else np.nan


def safe_median(s):
    x = finite(s).dropna()
    return float(x.median()) if len(x) else np.nan


def z1(df):
    return finite(df["ret_1d"]).abs() / finite(df["sigma_t0"]).replace(0, np.nan)


def subperiod(date) -> str:
    y = pd.Timestamp(date).year
    return np.select([y <= 2021, y == 2022, y == 2023, y == 2024],
                     ["2020-2021", "2022", "2023", "2024"], default="2025-2026")


def cell_of(brd, disp) -> str:
    b = "HIGH" if brd > BRD_MED else "LOW"
    d = "HIGH" if disp > DISP_MED else "LOW"
    return f"{b}_BREADTH_{d}_DISP"


def bh_fdr(p) -> np.ndarray:
    """Benjamini-Hochberg FDR 5% significance mask."""
    pv = np.asarray(p, dtype=float)
    out = np.zeros(len(pv), dtype=bool)
    good = np.isfinite(pv)
    ix = np.where(good)[0]
    if not len(ix):
        return out
    order = ix[np.argsort(pv[ix], kind="stable")]
    q = pv[order] * len(order) / np.arange(1, len(order) + 1)
    ok = q <= 0.05
    if ok.any():
        out[order[: int(np.max(np.where(ok)[0])) + 1]] = True
    return out


def cohend(a, b):
    a = finite(a).dropna()
    b = finite(b).dropna()
    if len(a) < 2 or len(b) < 2:
        return np.nan
    den = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    return float((a.mean() - b.mean()) / den) if den > 0 else np.nan
