"""
Calculate P90 thresholds per pair from MT5 historical data.
P90 = 90th percentile of 5-min candle body sizes during Asian session (2-11 AM EST).
"""
import MetaTrader5 as mt5
import json
import statistics
from datetime import datetime, timezone, timedelta

cfg_file = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\dmr_config.json"
with open(cfg_file) as f:
    cfg = json.load(f)

mt5.initialize()
mt5.login(login=cfg['login'], password=cfg['password'], server=cfg['server'])

symbols = ["EURUSD.PRO", "USDCHF.PRO", "CHFJPY.PRO"]
results = {}

for symbol in symbols:
    print(f"\n=== {symbol} ===")
    # Fetch last 3 months of M5 data
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=90)
    
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M5, start, end)
    if rates is None or len(rates) == 0:
        print(f"  No data for {symbol}")
        continue
    
    print(f"  Total bars: {len(rates)}")
    
    # Calculate body sizes by EST hour
    bodies_by_hour = {}
    for r in rates:
        ts = datetime.fromtimestamp(r['time'], tz=timezone.utc)
        est_h = (ts.hour - 5 + 24) % 24
        
        if est_h < 2 or est_h >= 11:
            continue
        
        body_price = abs(r['close'] - r['open'])
        
        # Convert to pips
        if "JPY" in symbol.upper():
            body_pips = body_price * 100.0
        else:
            body_pips = body_price * 10000.0
        
        hour_key = est_h
        if hour_key not in bodies_by_hour:
            bodies_by_hour[hour_key] = []
        bodies_by_hour[hour_key].append(body_pips)
    
    # Calculate P90 (90th percentile) for each hour band
    # Match the existing time bands: 2-4, 4-6, 6-8, 8-10, 10-11
    bands = [(2, 4), (4, 6), (6, 8), (8, 10), (10, 11)]
    thresholds = []
    
    for band_start, band_end in bands:
        band_bodies = []
        for h in range(band_start, band_end):
            if h in bodies_by_hour:
                band_bodies.extend(bodies_by_hour[h])
        
        if band_bodies:
            band_bodies.sort()
            p90_idx = int(len(band_bodies) * 0.90)
            p90_val = band_bodies[p90_idx]
            # Round to 1 decimal
            p90_rounded = round(p90_val, 1)
            thresholds.append(p90_rounded)
            print(f"  {band_start}-{band_end}AM: P90={p90_rounded}p (n={len(band_bodies)}, median={round(statistics.median(band_bodies),1)})")
        else:
            thresholds.append(99.0)
            print(f"  {band_start}-{band_end}AM: NO DATA")
    
    results[symbol] = thresholds

print("\n\n=== P90 THRESHOLDS SUMMARY ===")
for sym, thresh in results.items():
    print(f"{sym}: {thresh}")

# Save results
output_file = r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\mt5\p90_thresholds.json"
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to {output_file}")

mt5.shutdown()
