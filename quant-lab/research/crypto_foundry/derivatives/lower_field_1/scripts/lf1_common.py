"""LOWER-FIELD-1 shared configuration and helpers.

All thresholds below are FROZEN in 01_PREREGISTRATION.md / 02_EVENT_DEFINITION_AUDIT.md.
Do not edit after outcome observation begins.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
LF0 = ROOT.parent / "lower_field"

PANEL = LF0 / "RESULTS" / "lower_field_panel.parquet"
CANON = (
    ROOT.parent.parent / "alt_rotation" / "data_1_1"
    / "ALT_DATA_1_1_PIT_UNIVERSE.parquet"
)
HANDBF = LF0 / "RESULTS" / "30_CROSS_FIELD_HANDOFF_READY.parquet"
MECH4_LATTICE = (
    ROOT.parent.parent / "alt_rotation" / "mech_4" / "31b_TEMPORAL_DELIVERY_LATTICE_COMPLETE.csv"
)

RESULTS = ROOT / "RESULTS"

# rank bands
PRIMARY_BANDS = ["501-750", "751-1000", "1001-1500", "1501-2000"]
COMPARE_BANDS = ["251-500", "101-250", "26-100"]

# horizons used for amplitude anatomy
HORIZONS = ["1D", "3D", "7D", "14D", "30D"]
RET_COLS = {"1D": "ret_1d", "3D": "ret_3d", "7D": "ret_7d", "14D": "ret_14d", "30D": "ret_30d"}

# event lenses (prereg section 3)
RAW_PCT = 0.15
SIGMA_K = 3.0
MAD_K = 3.0
CROSS_Z = 3.0
VOL_WINDOW = 63
VOL_MIN_OBS = 40

# momentum-shape mapping (from LOWER-FIELD-0: 3D x 14D sign split)
def momentum_shape(ret_3d, ret_14d):
    """Return one of the four shape labels from prereg Phase G."""
    s3 = 1 if ret_3d > 0 else (-1 if ret_3d < 0 else 0)
    s14 = 1 if ret_14d > 0 else (-1 if ret_14d < 0 else 0)
    if s3 == 1 and s14 == 1:
        return "SHORT_HOT_MEDIUM_HOT"
    if s3 == 1 and s14 <= 0:
        return "SHORT_HOT_MEDIUM_COLD"
    if s3 <= 0 and s14 == 1:
        return "SHORT_COLD_MEDIUM_HOT"
    return "SHORT_COLD_MEDIUM_COLD"


def compute_sigma(df: pd.DataFrame) -> pd.Series:
    """Trailing-63d realized std of ret_1d per asset, causal, min 40 obs."""
    sigma = (
        df.sort_values("historical_date")
        .groupby("cmc_id")["ret_1d"]
        .transform(
            lambda s: s.shift(1)
            .rolling(VOL_WINDOW, min_periods=VOL_MIN_OBS)
            .std()
        )
    )
    return sigma.astype(float)


def add_momentum_shape(df: pd.DataFrame) -> pd.DataFrame:
    """Add momentum_state column per row using causal ret_3d/ret_14d."""
    df = df.copy()
    df["momentum_state"] = df.apply(
        lambda r: momentum_shape(r["ret_3d"], r["ret_14d"]), axis=1
    )
    return df


def canonical_upper_bands():
    """Load canonical Top-500 and reconstruct comparison rank bands 251-500/101-250/26-100.

    Returns DataFrame with rank, rank_band (our convention), price_usd, ret horizons
    recomputed CAUSALLY from price, market caps, btc/eth context per date.
    """
    can = pd.read_parquet(CANON)
    can = can.sort_values(["cmc_id", "historical_date"]).copy()
    # PIT rank band under our convention
    r = can["rank"]
    can["rb"] = pd.cut(
        r, bins=[0, 25, 100, 250, 500], labels=["1-25", "26-100", "101-250", "251-500"]
    )
    can["rank_band"] = can["rb"].astype(str)
    can = can[can["rank_band"].isin(["26-100", "101-250", "251-500"])].copy()
    # causal multi-day returns from price
    g = can.groupby("cmc_id", sort=False)["price_usd"]
    logp = np.log(can["price_usd"].to_numpy(dtype=float))
    can["_logf"] = np.append([np.nan], np.diff(logp))
    can["_logf"] = np.where(np.isfinite(can["_logf"]), can["_logf"], np.nan)
    can["ret_1d"] = np.expm1(can["_logf"])
    cs = can.groupby("cmc_id", sort=False)["_logf"].cumsum()
    for w, col in [(3, "ret_3d"), (7, "ret_7d"), (14, "ret_14d"), (30, "ret_30d")]:
        cs_shift = can.groupby("cmc_id", sort=False)["_logf"].transform(
            lambda s: s.shift(w)
        )
        # cumulative log return at t minus cumulative log return at t-w = w-day log return
        cs_w = cs - cs_shift
        can[col] = np.expm1(cs_w)
    can = can.drop(columns=["rb", "_logf"])
    return can