"""LOWER-FIELD-2 panel loader: continuous causal features for ranks 501-2000.

Precomputes the causal feature frame ONCE and caches it to RESULTS/ so every
downstream script uses identical denominators.

CRITICAL CONTIGUITY RULES (see 02_INTEGRITY_REPAIR_AUDIT.md):
  * sigma and forward cumsums are computed on the FULL panel (the whole
    501-2000 per-asset series) BEFORE any band filter. Filtering first
    truncates migrated assets' series and distorts rolling windows and
    cumsums.
  * this exactly mirrors the repaired LF1 `canonical_upper_bands()` and the
    LF0 `add_causal_features()`: cumsum-based w-day returns on the continuous
    per-asset series.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import lf2_common as C

CACHE = C.RESULTS / "lf2_feature_frame.parquet"


def _sorted(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)


def _momentum_shape_vec(ret_3d: pd.Series, ret_14d: pd.Series) -> pd.Series:
    """Vectorized four-shape mapping, no row-wise apply (fast on ~3.3M rows)."""
    s3 = np.sign(np.asarray(ret_3d, dtype=float))
    s14 = np.sign(np.asarray(ret_14d, dtype=float))
    out = np.empty(len(s3), dtype=object)
    hh = (s3 > 0) & (s14 > 0)
    hc = (s3 > 0) & (s14 <= 0)
    ch = (s3 <= 0) & (s14 > 0)
    out[hh] = "SHORT_HOT_MEDIUM_HOT"
    out[hc] = "SHORT_HOT_MEDIUM_COLD"
    out[ch] = "SHORT_COLD_MEDIUM_HOT"
    out[~(hh) & ~(hc) & ~(ch)] = "SHORT_COLD_MEDIUM_COLD"
    out[pd.isna(s3) | pd.isna(s14)] = np.nan  # type: ignore[index]
    return pd.Series(out, index=ret_3d.index)


def build() -> pd.DataFrame:
    full = pd.read_parquet(C.PANEL)
    full = _sorted(full)
    # 1) continuous sigma on the FULL panel (never band-truncated)
    sig = C.compute_sigma(full)
    # 2) continuous forward cumsums on the FULL panel
    cs = full.groupby("cmc_id", sort=False)["ret_1d"].cumsum()
    for h in C.REV_HORIZONS:
        cs_lead = full.groupby("cmc_id", sort=False)["ret_1d"].cumsum().shift(-h)
        full[f"fwd{h}_cum"] = cs_lead - cs
    full["sigma_t0"] = sig
    # 3) momentum shape (vectorized)
    full["momentum_state"] = _momentum_shape_vec(full["ret_3d"], full["ret_14d"])
    # 4) NOW filter to primary lower-field bands
    p = full[full["rank_band"].isin(C.PRIMARY_BANDS)].copy()
    p.to_parquet(CACHE, index=False)
    return p


def load(force: bool = False) -> pd.DataFrame:
    if not force and CACHE.exists():
        return pd.read_parquet(CACHE)
    return build()


if __name__ == "__main__":
    df = load(force=True)
    print("feature frame rows", len(df))
    print("cols", len(df.columns))
    # sanity: continuous sigma unconditional P(>=3s) rolls
    z = (df["ret_1d"].abs() / df["sigma_t0"]).dropna()
    for k in [1, 2, 3, 4]:
        print(f"P(>= {k}s 1D) = {(z >= k).mean():.4%}")
    print(df[["rank_band", "ret_1d", "sigma_t0", "momentum_state",
              "fwd7_cum"]].tail(4).to_string())