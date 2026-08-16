"""R0.2 Resampling audit — independently reproduce M5 -> H1 for EURUSD and
verify hour-boundary correctness. Prints a compact JSON summary."""
import json
import os

import pandas as pd

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "..", "quant-lab", "data")
F = os.path.join(DATA, "EURUSDPRO_M5_2023_2026.csv")

df = pd.read_csv(F)
df["dt"] = pd.to_datetime(df["time"], unit="s", utc=True)
df = df.sort_values("dt").set_index("dt")

h1 = df.resample("1h").agg(
    open=("open", "first"),
    high=("high", "max"),
    low=("low", "min"),
    close=("close", "last"),
    volume=("tick_volume", "sum"),
)

out = {
    "source_rows": int(len(df)),
    "h1_rows": int(len(h1)),
    "h1_first": str(h1.index[0]),
    "h1_last": str(h1.index[-1]),
    "h1_nulls": {c: int(h1[c].isna().sum()) for c in h1.columns},
    "ohlc_inconsistent": int(((h1.high < h1.low) | (h1.high < h1.open) | (h1.high < h1.close) | (h1.low > h1.open) | (h1.low > h1.close)).sum()),
    "dst_note": "Forex data is UTC; no DST transitions apply.",
}

# Spot-check three hour boundaries: open must equal first M5 open, close last M5 close.
checks = []
for ts in [h1.index[100], h1.index[5000], h1.index[20000]]:
    m5 = df.loc[ts : ts + pd.Timedelta(hours=1)]
    if len(m5) == 0:
        continue
    checks.append({
        "hour": str(ts),
        "m5_bars": int(len(m5)),
        "open_match": bool(abs(m5.open.iloc[0] - h1.loc[ts, "open"]) < 1e-9),
        "close_match": bool(abs(m5.close.iloc[-1] - h1.loc[ts, "close"]) < 1e-9),
        "high_match": bool(abs(m5.high.max() - h1.loc[ts, "high"]) < 1e-9),
        "low_match": bool(abs(m5.low.min() - h1.loc[ts, "low"]) < 1e-9),
    })
out["boundary_checks"] = checks

print(json.dumps(out, indent=2))
