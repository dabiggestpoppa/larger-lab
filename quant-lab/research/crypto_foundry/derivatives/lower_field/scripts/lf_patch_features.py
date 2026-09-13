#!/usr/bin/env python3
"""LF — Patch the lower-field panel to fix two bugs:
1. Multi-day returns: was shifting raw logf instead of cumsum
2. Rank velocity: was not grouped by cmc_id

Reads the existing panel, recomputes affected features, writes back.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PANEL = ROOT / "RESULTS" / "lower_field_panel.parquet"
HORIZONS = [1, 3, 7, 14, 30, 60]


def main() -> int:
    print("loading panel...", flush=True)
    lf = pd.read_parquet(PANEL)
    lf = lf.replace([np.inf, -np.inf], np.nan)
    lf = lf.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    print(f"loaded {len(lf)} rows, {lf['cmc_id'].nunique()} assets", flush=True)

    # === FIX 1: multi-day returns ===
    print("recomputing multi-day returns...", flush=True)
    ok = lf["ret_1d"].notna() & (lf["ret_1d"] > -1.0)
    logf = np.where(ok, np.log1p(lf["ret_1d"].clip(lower=-0.9999)), np.nan)
    lf["_logf"] = logf
    lf["_cs"] = lf.groupby("cmc_id", sort=False)["_logf"].cumsum()

    for w in HORIZONS:
        if w == 1:
            lf["ret_1d_raw"] = lf["ret_1d"]
            continue
        cs_shift = lf.groupby("cmc_id")["_cs"].transform(lambda s: s.shift(w))
        lf[f"ret_{w}d"] = np.expm1(lf["_cs"] - cs_shift)
    lf = lf.drop(columns=["_logf", "_cs"])

    # === FIX 2: rank velocity ===
    print("recomputing rank velocity...", flush=True)
    for w in HORIZONS:
        lf[f"rank_vel_{w}d"] = lf.groupby("cmc_id")["rank"].transform(
            lambda s: s.shift(w) - s)

    # Verify
    print("verification:", flush=True)
    for w in [3, 7, 14, 30, 60]:
        col = f"ret_{w}d"
        nn = lf[col].notna().sum()
        print(f"  {col}: {nn} non-null ({100*nn/len(lf):.1f}%)", flush=True)
    for w in [3, 7, 14, 30, 60]:
        col = f"rank_vel_{w}d"
        nn = lf[col].notna().sum()
        print(f"  {col}: {nn} non-null ({100*nn/len(lf):.1f}%)", flush=True)

    # Write back
    lf = lf.sort_values(["cmc_id", "historical_date"]).reset_index(drop=True)
    lf.to_parquet(PANEL, index=False)
    print(f"panel patched: {len(lf)} rows written to {PANEL}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
