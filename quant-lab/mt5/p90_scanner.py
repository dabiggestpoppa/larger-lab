"""
P90 Threshold Scanner — CEREBUS FX v4 Manual Formula
Computes P90 = 90th percentile of |Close - Open| for M5 candles
during 2AM-11AM EST activation window.
"""
import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import pytz

EST = pytz.timezone('US/Eastern')

PAIRS = {
    'EURUSD': 'EURUSD.PRO',
    'GBPUSD': 'GBPUSD.PRO',
    'USDJPY': 'USDJPY.PRO',
    'AUDUSD': 'AUDUSD.PRO',
    'USDCAD': 'USDCAD.PRO',
    'NZDUSD': 'NZDUSD.PRO',
}

# Also try non-.PRO variants
ALT_SUFFIXES = ['', '.PRO', '.i', 'm', '.m']

def get_symbol_name(base):
    """Find the correct MT5 symbol name."""
    for suffix in ALT_SUFFIXES:
        name = base + suffix
        info = mt5.symbol_info(name)
        if info is not None:
            return name
    return None

def fetch_m5_data(symbol, days_back=180):
    """Fetch M5 bars from MT5."""
    utc_from = datetime.utcnow() - timedelta(days=days_back)
    utc_to = datetime.utcnow()
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M5, utc_from, utc_to)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    return df

def compute_p90(df, pair_name):
    """Compute P90 threshold per CEREBUS manual formula."""
    # Convert to EST
    df['est_time'] = df['time'].dt.tz_convert(EST)
    df['est_hour'] = df['est_time'].dt.hour
    
    # Filter to activation window: 2AM-11AM EST
    mask = (df['est_hour'] >= 2) & (df['est_hour'] < 11)
    activation = df[mask].copy()
    
    if len(activation) < 100:
        return None, 0, 0
    
    # Absolute body size
    activation['body'] = (activation['close'] - activation['open']).abs()
    
    # P90 threshold
    p90 = np.percentile(activation['body'], 90)
    
    # Also compute stats
    mean_body = activation['body'].mean()
    median_body = activation['body'].median()
    std_body = activation['body'].std()
    
    # Convert to pips (or points for JPY)
    if 'JPY' in pair_name:
        p90_pips = p90 * 100  # JPY: 1 pip = 0.01, so *100
        unit = 'pips (x100)'
    else:
        p90_pips = p90 * 10000  # Standard forex: 1 pip = 0.0001
        unit = 'pips (x10000)'
    
    stats = {
        'p90_raw': p90,
        'p90_pips': p90_pips,
        'mean_body': mean_body * (100 if 'JPY' in pair_name else 10000),
        'median_body': median_body * (100 if 'JPY' in pair_name else 10000),
        'std_body': std_body * (100 if 'JPY' in pair_name else 10000),
        'candles': len(activation),
        'unit': unit,
    }
    
    return p90_pips, len(activation), stats

def main():
    if not mt5.initialize():
        print("ERROR: MT5 init failed")
        return
    
    print("=" * 70)
    print("P90 THRESHOLD SCANNER — CEREBUS FX v4 Formula")
    print(f"Activation Window: 2AM-11AM EST | Sample: Last 180 days M5")
    print("=" * 70)
    print()
    
    results = {}
    
    for pair, default_sym in PAIRS.items():
        # Find correct symbol name
        sym = get_symbol_name(pair)
        if sym is None:
            # Try the .PRO variant
            sym = get_symbol_name(default_sym)
        if sym is None:
            print(f"❌ {pair}: Symbol not found in MT5")
            continue
        
        info = mt5.symbol_info(sym)
        if info is None:
            print(f"❌ {pair}: Cannot get info for {sym}")
            continue
        
        print(f"📊 {pair} ({sym}) | Digits: {info.digits} | Point: {info.point}")
        
        # Fetch data
        df = fetch_m5_data(sym, days_back=180)
        if df is None or len(df) == 0:
            print(f"  ❌ No data returned")
            continue
        
        print(f"  Total M5 bars: {len(df)}")
        
        # Compute P90
        p90_val, n_candles, stats = compute_p90(df, pair)
        
        if p90_val is None:
            print(f"  ❌ Insufficient data in activation window")
            continue
        
        results[pair] = {
            'p90': p90_val,
            'candles': n_candles,
            'stats': stats,
            'symbol': sym,
        }
        
        print(f"  ✅ P90 = {p90_val:.1f} {stats['unit']}")
        print(f"     Mean: {stats['mean_body']:.1f} | Median: {stats['median_body']:.1f} | Std: {stats['std_body']:.1f}")
        print(f"     Activation candles: {n_candles}")
        print()
    
    # Summary table
    print("=" * 70)
    print("P90 THRESHOLD SUMMARY")
    print("=" * 70)
    print(f"{'Pair':<10} {'P90 (pips)':<12} {'Mean':<10} {'Median':<10} {'Candles':<10}")
    print("-" * 52)
    for pair, data in results.items():
        s = data['stats']
        print(f"{pair:<10} {data['p90']:<12.1f} {s['mean_body']:<10.1f} {s['median_body']:<10.1f} {data['candles']:<10}")
    
    # Cross-validate with manual benchmarks
    print()
    print("=" * 70)
    print("CROSS-VALIDATION vs MANUAL BENCHMARKS")
    print("=" * 70)
    benchmarks = {
        'EURUSD': 4.6,
        'USDCHF': 4.2,
    }
    for pair, expected in benchmarks.items():
        if pair in results:
            actual = results[pair]['p90']
            deviation = abs(actual - expected) / expected * 100
            status = "✅" if deviation < 15 else "⚠️"
            print(f"  {pair}: Calculated={actual:.1f} | Manual={expected} | Deviation={deviation:.1f}% {status}")
    
    # Save results
    import json
    output = {}
    for pair, data in results.items():
        output[pair] = {
            'p90_pips': round(data['p90'], 2),
            'mean_body': round(data['stats']['mean_body'], 2),
            'median_body': round(data['stats']['median_body'], 2),
            'std_body': round(data['stats']['std_body'], 2),
            'candles': data['candles'],
            'symbol': data['symbol'],
        }
    
    with open(r"C:\Users\wifik\Desktop\projects\larger-lab\quant-lab\reports\p90_thresholds.json", 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to quant-lab/reports/p90_thresholds.json")
    
    mt5.shutdown()

if __name__ == '__main__':
    main()
