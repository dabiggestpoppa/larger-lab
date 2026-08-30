"""Trace P90 signal detection in detail."""
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

STRATEGY_DIR = Path(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\strategies")
sys.path.insert(0, str(STRATEGY_DIR))

from p90_cascade_activation import P90CascadeActivationStrategy, P90CascadeConfig

# Parse CSV
data_path = Path(r"C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv")
with open(data_path, 'r', encoding='utf-8', errors='ignore') as f:
    raw = f.readlines()
records = []
for line in raw[1:]:
    parts = line.strip().split()
    if len(parts) < 7:
        continue
    try:
        ts = datetime.strptime(f"{parts[0]} {parts[1]}", "%Y.%m.%d %H:%M:%S")
        records.append({"timestamp": ts, "open": float(parts[2]),
                        "high": float(parts[3]), "low": float(parts[4]),
                        "close": float(parts[5])})
    except (ValueError, IndexError):
        continue
df = pd.DataFrame(records)
df.set_index("timestamp", inplace=True)
df.sort_index(inplace=True)

# Trace Jan 3-4
df_work = df[(df.index >= datetime(2023, 1, 2, 18)) & (df.index < datetime(2023, 1, 4))].copy()
df_work["est_hour"] = df_work.index.hour.map(lambda h: (h - 5 + 24) % 24)

# The data starts at 00:00 UTC on Jan 2 = 7PM EST Jan 1
# Jan 2 00:00 UTC = 7PM EST Jan 1 -> Asian session starts
# We need to find when the first full Asian session completes

asian_high = None
asian_low = None
asian_range_complete = False
tier = "NA"

for i in range(len(df_work)):
    row = df_work.iloc[i]
    ts = df_work.index[i]
    est_h = int(row["est_hour"])
    o, h, l, c = row["open"], row["high"], row["low"], row["close"]
    
    in_asian = est_h >= 19 or est_h < 3
    
    if in_asian:
        if asian_high is None:
            asian_high = h
            asian_low = l
        else:
            asian_high = max(asian_high, h)
            asian_low = min(asian_low, l)
        # At est_h == 3, finalize
        if est_h == 3 and asian_high is not None and not asian_range_complete:
            ar_pips = (asian_high - asian_low) * 10000
            if ar_pips < 20: tier = "T1"
            elif ar_pips < 30: tier = "T2"
            elif ar_pips < 45: tier = "T3"
            else: tier = "NO_GO"
            asian_range_complete = True
            print(f"Asian finalized at {ts} (est={est_h}): AR={ar_pips:.1f}p, Tier={tier}")
        continue
    
    # After Asian, before entry window
    if not asian_range_complete:
        continue
    
    if tier == "NO_GO":
        if est_h < 11:
            pass  # still skip
        continue
    
    in_entry = 2 <= est_h < 11
    if not in_entry:
        continue
    
    # Check P90
    total_range = h - l
    if total_range <= 0:
        continue
    body_size = abs(c - o)
    body_pct = body_size / total_range
    body_pips = body_size * 10000
    
    thresholds = {(2,4):4.1, (4,6):4.6, (6,8):4.6, (8,10):5.9, (10,11):6.2}
    threshold = 6.2
    for (s,e), t in thresholds.items():
        if s <= est_h < e:
            threshold = t
            break
    
    is_p90 = body_pct > 0.60 and body_pips >= threshold
    
    if is_p90:
        direction = "LONG" if c > o else "SHORT"
        print(f"P90 at {ts} (est={est_h}): {direction}, body={body_pips:.1f}p (thresh={threshold}), bpct={body_pct:.2f}")

print(f"\nTrace done. Range complete: {asian_range_complete}, Tier: {tier}")
