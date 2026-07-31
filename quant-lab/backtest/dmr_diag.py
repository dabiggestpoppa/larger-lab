"""Quick diagnostic: analyze trade-level R:R for problem pairs."""
import csv, sys
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from pathlib import Path

WORKSPACE = Path(r"C:\Users\wifik\Desktop\projects\larger-lab")
EST = timezone(timedelta(hours=-5))

PIP_SIZES = {
    "EURUSD": 0.0001, "GBPUSD": 0.0001, "USDCHF": 0.0001,
    "USDJPY": 0.01, "AUDUSD": 0.0001, "NZDUSD": 0.0001,
    "CADJPY": 0.01, "XAGUSD": 0.001,
}

# Check XAGUSD pip size — prices are ~23, so 1 pip = 0.001? No.
# XAGUSD: 23.304 → 23.314 = 10 pips = 0.01 price change → 1 pip = 0.001
# But wait, MT5 XAGUSD is 3 decimal places, so 1 point = 0.001
# 1 pip = 10 points = 0.01
# Actually for silver, 1 pip = 0.001 (broker-dependent)
# Let me check: 23.304 to 23.305 = 0.001 = 1 pip? Or 10 pips?
# Standard: XAGUSD 1 pip = 0.001 (3 decimal places)
# So pip_size = 0.001 is correct. But P90 threshold of 0.5p = 0.0005 price
# That's half a pip — way too small. A 0.5 pip body on silver is noise.

# The real issue: XAGUSD P90 threshold needs to be higher
# Let me compute actual body sizes

def load_csv(path):
    bars = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                ts_raw = row.get("timestamp") or row.get("time")
                if not ts_raw: continue
                try:
                    ts = datetime.fromtimestamp(int(float(ts_raw)), tz=EST)
                except (ValueError, OSError):
                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                        try:
                            dt_naive = datetime.strptime(ts_raw.strip(), fmt)
                            ts = dt_naive.replace(tzinfo=EST)
                            break
                        except ValueError:
                            continue
                    else:
                        continue
                o = float(row.get("open") or row.get("Open"))
                h = float(row.get("high") or row.get("High"))
                lo = float(row.get("low") or row.get("Low"))
                c = float(row.get("close") or row.get("Close"))
                bars.append({"ts": ts, "est_h": ts.hour, "o": o, "h": h, "l": lo, "c": c})
            except (ValueError, KeyError):
                continue
    bars.sort(key=lambda b: b["ts"])
    return bars

# Analyze body size distributions per hour for key pairs
for symbol, pip_size in [("EURUSD", 0.0001), ("USDCHF", 0.0001), ("XAGUSD", 0.001), ("CADJPY", 0.01)]:
    csv_path = WORKSPACE / f"quant-lab/data/{symbol}_M5.csv"
    if not csv_path.exists():
        csv_path = WORKSPACE / f"quant-lab/data/{symbol}_M5_fetched.csv"
    if not csv_path.exists():
        csv_path = WORKSPACE / f"quant-lab/data/{symbol}PRO_M5.csv"
    if not csv_path.exists():
        print(f"[SKIP] {symbol}")
        continue
    
    bars = load_csv(str(csv_path))
    
    # Body sizes per EST hour (2-10)
    hourly_bodies = defaultdict(list)
    for b in bars:
        if 2 <= b["est_h"] <= 10:
            body_pips = abs(b["c"] - b["o"]) / pip_size
            hourly_bodies[b["est_h"]].append(body_pips)
    
    print(f"\n=== {symbol} (pip_size={pip_size}) ===")
    print(f"Total bars: {len(bars):,}")
    print(f"{'Hour':>6} {'Count':>6} {'P50':>6} {'P75':>6} {'P90':>6} {'P95':>6} {'Max':>6}")
    for h in range(2, 11):
        bodies = sorted(hourly_bodies.get(h, []))
        if not bodies:
            continue
        n = len(bodies)
        p50 = bodies[int(n*0.50)]
        p75 = bodies[int(n*0.75)]
        p90 = bodies[int(n*0.90)]
        p95 = bodies[int(n*0.95)]
        mx = bodies[-1]
        print(f"  {h:02d}:00 {n:6d} {p50:6.1f} {p75:6.1f} {p90:6.1f} {p95:6.1f} {mx:6.1f}")
