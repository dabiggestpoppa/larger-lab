"""Quick check: EURUSD AR percentiles for comparison."""
import pandas as pd
import numpy as np

csv_path = r'C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\data\EURUSD_M5.csv'
pip_size = 0.0001

df = pd.read_csv(csv_path, header=0)
df = df.rename(columns={"timestamp": "dt", "volume": "vol"})
df["dt"] = pd.to_datetime(df["dt"])
df = df.set_index("dt").sort_index()

if df.index.tz is None:
    df = df.tz_localize("UTC")
df = df.tz_convert("America/New_York")

shifted = df.index - pd.Timedelta(hours=3)
df["session"] = shifted.floor("D")

ranges = []
for day, data in df.groupby("session"):
    asian = data[(data.index.hour >= 19) | (data.index.hour < 3)]
    if len(asian) >= 10:
        ar = (asian["high"].max() - asian["low"].min()) / pip_size
        ranges.append(ar)

ranges = np.array(ranges)
print("EURUSD sessions: {}".format(len(ranges)))
print("AR mean: {:.1f}p | median: {:.1f}p | std: {:.1f}p".format(
    ranges.mean(), np.median(ranges), ranges.std()))
print("33rd percentile: {:.1f}p".format(np.percentile(ranges, 33.3)))
print("66th percentile: {:.1f}p".format(np.percentile(ranges, 66.6)))
print()
print("EURGBP 33rd: 14.7p | 66th: 23.0p")
print("EURUSD 33rd: {:.1f}p | 66th: {:.1f}p".format(
    np.percentile(ranges, 33.3), np.percentile(ranges, 66.6)))
