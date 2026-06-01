"""
XAUUSD Timezone Diagnostic — Test Hypothesis Without Modifying Original Code
=========================================================================

This script tests the hypothesis that the 2.84x trade count difference
between Python and Nautilus is caused by timezone boundary handling.

HYPOTHESIS:
- Python uses EST date boundaries (midnight EST = 5AM UTC)
- Nautilus uses UTC date boundaries (midnight UTC = 7PM EST)
- This causes different Asian session splits for XAUUSD

TEST:
1. Count how many Asian sessions span UTC midnight vs EST midnight
2. Compare session initialization counts
3. Identify the exact divergence point
"""

import sys
sys.path.insert(0, '.')
sys.path.insert(0, 'quant-lab')
sys.path.insert(0, 'quant-lab/configs')
sys.path.insert(0, 'quant-lab/strategies')
sys.path.insert(0, 'quant-lab/backtests')

from datetime import datetime, timedelta, timezone
from pathlib import Path
from collections import defaultdict

# Import the loaders
from engines.symmetry_trap_backtest import load_m5_csv

# XAUUSD config from asset_configs.py
XAUUSD_CONFIG = {
    'pip_value': 0.1,
    'tiers': {
        'T1': {'ar_max': 32.0, 'au': 16.0, 'trigger': 19.0},
        'T2': {'ar_max': 58.0, 'au': 29.0, 'trigger': 35.0},
        'T3': {'ar_max': 95.0, 'au': 48.0, 'trigger': 58.0},
    }
}

def est_hour(dt: datetime) -> int:
    """Get EST hour from datetime."""
    return (dt.hour - 5) % 24

def utc_hour(dt: datetime) -> int:
    """Get UTC hour from datetime."""
    return dt.hour % 24

def analyze_asian_boundaries(bars):
    """Analyze how Asian sessions cross timezone boundaries."""
    
    # Group bars by EST date (Python method)
    est_days = defaultdict(list)
    for bar in bars:
        est_dt = bar.timestamp + timedelta(hours=-5)
        est_days[est_dt.strftime("%Y-%m-%d")].append(bar)
    
    # Group bars by UTC date (Nautilus method)
    utc_days = defaultdict(list)
    for bar in bars:
        utc_days[bar.timestamp.strftime("%Y-%m-%d")].append(bar)
    
    # Count Asian sessions spanning boundaries
    est_asian_spans = 0
    utc_asian_spans = 0
    
    for day, day_bars in est_days.items():
        # Check if this EST day has bars in both pre-3AM and post-3AM
        has_asian = any(est_hour(b.timestamp) >= 19 or est_hour(b.timestamp) < 3 for b in day_bars)
        has_post_asian = any(est_hour(b.timestamp) >= 3 for b in day_bars)
        if has_asian and has_post_asian:
            est_asian_spans += 1
    
    for day, day_bars in utc_days.items():
        # Check if this UTC day has bars in both pre-10PM and post-10PM EST
        has_asian = any(est_hour(b.timestamp) >= 19 or est_hour(b.timestamp) < 3 for b in day_bars)
        has_post_asian = any(est_hour(b.timestamp) >= 3 for b in day_bars)
        if has_asian and has_post_asian:
            utc_asian_spans += 1
    
    return {
        'est_days': len(est_days),
        'utc_days': len(utc_days),
        'est_asian_spans': est_asian_spans,
        'utc_asian_spans': utc_asian_spans,
    }

def count_session_inits(bars):
    """Count how many times session would be initialized at 3AM EST."""
    
    # Python method: group by EST day, init once per day
    est_days = defaultdict(list)
    for bar in bars:
        est_dt = bar.timestamp + timedelta(hours=-5)
        est_days[est_dt.strftime("%Y-%m-%d")].append(bar)
    
    python_inits = 0
    for day, day_bars in est_days.items():
        # Check if this day has bars at 3AM EST
        has_3am = any(est_hour(b.timestamp) >= 3 and est_hour(b.timestamp) < 4 for b in day_bars)
        if has_3am:
            python_inits += 1
    
    # Nautilus method: group by UTC day, init on first bar >= 3AM EST
    utc_days = defaultdict(list)
    for bar in bars:
        utc_days[bar.timestamp.strftime("%Y-%m-%d")].append(bar)
    
    nautilus_inits = 0
    for day, day_bars in utc_days.items():
        # Check if this UTC day has bars at 3AM EST
        has_3am = any(est_hour(b.timestamp) >= 3 and est_hour(b.timestamp) < 4 for b in day_bars)
        if has_3am:
            nautilus_inits += 1
    
    return {
        'python_session_inits': python_inits,
        'nautilus_session_inits': nautilus_inits,
    }

def main():
    print("=" * 70)
    print("XAUUSD Timezone Diagnostic")
    print("=" * 70)
    
    # Load XAUUSD data
    csv_path = Path('quant-lab/data/XAUUSD_M5.csv')
    bars, sym = load_m5_csv(csv_path)
    print(f"\nLoaded {len(bars)} bars from {csv_path.name}")
    
    # Analyze boundaries
    analysis = analyze_asian_boundaries(bars)
    print(f"\nTimezone Boundary Analysis:")
    print(f"  EST days: {analysis['est_days']}")
    print(f"  UTC days: {analysis['utc_days']}")
    print(f"  Days with Asian session spanning midnight (EST): {analysis['est_asian_spans']}")
    print(f"  Days with Asian session spanning midnight (UTC): {analysis['utc_asian_spans']}")
    
    # Count session inits
    inits = count_session_inits(bars)
    print(f"\nSession Initialization Counts:")
    print(f"  Python (EST day grouping): {inits['python_session_inits']}")
    print(f"  Nautilus (UTC day grouping): {inits['nautilus_session_inits']}")
    
    # Calculate ratio
    if inits['python_session_inits'] > 0:
        ratio = inits['nautilus_session_inits'] / inits['python_session_inits']
        print(f"  Ratio (Nautilus/Python): {ratio:.2f}x")
    
    # Show sample of first 5 bars at 3AM EST
    print(f"\nFirst 5 bars at 3AM EST (session init point):")
    count = 0
    for bar in bars:
        if est_hour(bar.timestamp) >= 3 and est_hour(bar.timestamp) < 4:
            print(f"  {bar.timestamp} EST | O:{bar.open:.2f} H:{bar.high:.2f} L:{bar.low:.2f} C:{bar.close:.2f}")
            count += 1
            if count >= 5:
                break

if __name__ == "__main__":
    main()