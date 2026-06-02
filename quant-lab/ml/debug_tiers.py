"""Debug the Asian Range grouping bug."""
import pandas as pd
from pathlib import Path

df = pd.read_parquet(Path(__file__).parent / "data" / "parquet" / "EURUSD_M5.parquet")
df_est = df.copy()
df_est.index = df_est.index.tz_convert("America/New_York")

# Look at bars around midnight
mask = (df_est.index >= "2022-01-03 18:00") & (df_est.index <= "2022-01-04 04:00")
window = df_est[mask]
print(f"Bars in window: {len(window)}")
print(f"Hours: {sorted(window.index.hour.unique())}")

# Old grouping: by calendar date
window_copy = window.copy()
window_copy["cal_date"] = window_copy.index.date
print("\n=== OLD GROUPING (by calendar date) ===")
for d, g in window_copy.groupby("cal_date"):
    ar = (g["high"].max() - g["low"].min()) * 10000
    print(f"  {d}: {len(g)} bars, hours={sorted(g.index.hour.unique())}, AR={ar:.1f}p")

# Fixed grouping: session date (19:00-03:00 = one session)
window_copy["sess_date"] = window_copy.index.map(
    lambda x: x.date() if x.hour >= 19 else (x - pd.Timedelta(days=1)).date()
)
print("\n=== FIXED GROUPING (by session date) ===")
for d, g in window_copy.groupby("sess_date"):
    ar = (g["high"].max() - g["low"].min()) * 10000
    print(f"  {d}: {len(g)} bars, hours={sorted(g.index.hour.unique())}, AR={ar:.1f}p")

# Now check the full distribution with fixed grouping
print("\n=== FULL DISTRIBUTION COMPARISON ===")
asian = df_est[(df_est.index.hour >= 19) | (df_est.index.hour < 3)].copy()
asian = asian.dropna(subset=["high", "low"])

# Old
asian["cal_date"] = asian.index.date
old_ranges = []
for d, g in asian.groupby("cal_date"):
    if len(g) >= 5:
        ar = (g["high"].max() - g["low"].min()) * 10000
        old_ranges.append(ar)

# Fixed
asian["sess_date"] = asian.index.map(
    lambda x: x.date() if x.hour >= 19 else (x - pd.Timedelta(days=1)).date()
)
new_ranges = []
for d, g in asian.groupby("sess_date"):
    if len(g) >= 5:
        ar = (g["high"].max() - g["low"].min()) * 10000
        new_ranges.append(ar)

old_series = pd.Series(old_ranges)
new_series = pd.Series(new_ranges)

print(f"Old grouping: {len(old_ranges)} sessions")
print(f"  Mean AR: {old_series.mean():.1f}p | Median: {old_series.median():.1f}p")
print(f"  Min: {old_series.min():.1f}p | Max: {old_series.max():.1f}p")
print(f"  Std: {old_series.std():.1f}p")

print(f"\nFixed grouping: {len(new_ranges)} sessions")
print(f"  Mean AR: {new_series.mean():.1f}p | Median: {new_series.median():.1f}p")
print(f"  Min: {new_series.min():.1f}p | Max: {new_series.max():.1f}p")
print(f"  Std: {new_series.std():.1f}p")

# Manual benchmark: EURUSD Asian Range should be ~15-25p typical
print("\n=== PERCENTILES ===")
print("Old:", old_series.describe(percentiles=[.1, .25, .5, .75, .9]).to_dict())
print("New:", new_series.describe(percentiles=[.1, .25, .5, .75, .9]).to_dict())
