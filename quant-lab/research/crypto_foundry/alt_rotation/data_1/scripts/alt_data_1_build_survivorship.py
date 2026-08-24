#!/usr/bin/env python3
"""ALT-DATA-1 — survivorship annotation table.

NON-CAUSAL by design: `exited_top500` and `days_until_exit` require
future knowledge (t+1). They are stored OUTSIDE the causal feature panel
and explicitly labeled NOT_CAUSAL so no causal feature can consume them.

Columns:
  internal_asset_id, cmc_id, symbol
  top500_exit_date        (last day the asset was observed in the panel)
  days_in_top500_total    (total distinct days in top-500)
  exited_top500           (True on the last observed membership day)
  days_until_exit         (0 on the exit day; NOT_CAUSAL annotation)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT


def main() -> int:
    u = pd.read_parquet(OUT / "ALT_DATA_1_PIT_UNIVERSE.parquet",
                        columns=["internal_asset_id", "cmc_id", "symbol",
                                 "historical_date", "rank"])
    g = u.groupby("cmc_id")
    last = g["historical_date"].max().rename("top500_exit_date")
    total = g.size().rename("days_in_top500_total")
    first = g["historical_date"].min()
    df = u.merge(last.reset_index(), on="cmc_id")
    df = df.merge(total.reset_index(), on="cmc_id")
    df["exited_top500"] = df["historical_date"] == df["top500_exit_date"]
    span = (df["top500_exit_date"] - df["historical_date"]).dt.days
    df["days_until_exit"] = span  # 0 on exit day; NOT_CAUSAL
    df = df.drop(columns=["rank"])
    df = df.sort_values(["cmc_id", "historical_date"])
    p = OUT / "ALT_DATA_1_SURVIVORSHIP.parquet"
    df.to_parquet(p, index=False)
    n_exited = int(df["exited_top500"].sum())
    print(f"{p.name} rows={len(df)} exited_labels={n_exited}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
