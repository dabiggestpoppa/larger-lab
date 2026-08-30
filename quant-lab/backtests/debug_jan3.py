#!/usr/bin/env python3
"""Quick debug: check Jan 3 price action and Asian range."""
import pandas as pd

data_path = r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv"
df = pd.read_csv(data_path, sep="\t")
df["timestamp"] = pd.to_datetime(df["<DATE>"] + " " + df["<TIME>"], format="%Y.%m.%d %H:%M:%S")
df.set_index("timestamp", inplace=True)
df.sort_index(inplace=True)

# Asian range for Jan 3: 7PM EST Jan 2 to 3AM Jan 3 = 00:00 UTC to 08:00 UTC Jan 3
asian = df[(df.index >= "2023-01-03 00:00:00") & (df.index < "2023-01-03 08:00:00")]
ah = asian["<HIGH>"].max()
al = asian["<LOW>"].min()
ar = (ah - al) * 10000
print(f"Asian Range Jan 3: H={ah} L={al} Range={ar:.1f}p")

# Entry window: 2AM-11AM EST = 07:00-16:00 UTC
window = df[(df.index >= "2023-01-03 07:00") & (df.index <= "2023-01-03 16:00")]
print(f"\nJan 3 entry window (07:00-16:00 UTC):")
print(f"  Bars: {len(window)}")
print(f"  High: {window['<HIGH>'].max()}")
print(f"  Low: {window['<LOW>'].min()}")
print(f"  First close: {window['<CLOSE>'].iloc[0]}")
print(f"  Last close: {window['<CLOSE>'].iloc[-1]}")
move = (window["<CLOSE>"].iloc[-1] - window["<CLOSE>"].iloc[0]) * 10000
print(f"  Close-to-close move: {move:.1f}p")

# Check the initial P90 at 09:45 UTC
row = df.loc["2023-01-03 09:45:00"]
print(f"\nInitial P90 bar (09:45 UTC):")
print(f"  O={row['<OPEN>']} H={row['<HIGH>']} L={row['<LOW>']} C={row['<CLOSE>']}")
body_pips = abs(row["<CLOSE>"] - row["<OPEN>"]) * 10000
print(f"  Body: {body_pips:.1f}p")
print(f"  C < AL ({al})? {row['<CLOSE>'] < al}")

# TP/SL for initial SHORT
entry = row["<CLOSE>"]
sl_pips = body_pips * 0.80
sl = entry + sl_pips / 10000
tp = al - ar * 0.5 / 10000
print(f"\n  Entry: {entry}")
print(f"  SL: {sl} (+{sl_pips:.1f}p)")
print(f"  TP: {tp} (AL - {ar*0.5:.1f}p)")
print(f"  TP < Entry? {tp < entry} (should be True for SHORT)")

# Cascade at 11:00 UTC
row2 = df.loc["2023-01-03 11:00:00"]
print(f"\nCascade bar (11:00 UTC):")
print(f"  O={row2['<OPEN>']} H={row2['<HIGH>']} L={row2['<LOW>']} C={row2['<CLOSE>']}")
body2 = abs(row2["<CLOSE>"] - row2["<OPEN>"]) * 10000
print(f"  Body: {body2:.1f}p")
entry2 = row2["<CLOSE>"]
sl2 = entry2 + body2 * 1.68 / 10000
tp2 = al - ar * 0.5 / 10000
print(f"  Entry: {entry2}")
print(f"  SL: {sl2} (+{body2*1.68:.1f}p)")
print(f"  TP: {tp2} (AL - {ar*0.5:.1f}p)")
print(f"  TP < Entry? {tp2 < entry2} (should be True for SHORT)")
print(f"  Distance entry-to-TP: {(tp2 - entry2)*10000:.1f}p")

# What if TP = entry - 50% AR?
tp_fix = entry2 - ar * 0.5 / 10000
print(f"\n  FIXED TP (entry - 50%AR): {tp_fix}")
print(f"  TP < Entry? {tp_fix < entry2}")
print(f"  Distance: {(tp_fix - entry2)*10000:.1f}p")
