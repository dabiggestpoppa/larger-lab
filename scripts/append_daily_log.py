"""Append today's basket results to daily log."""
import datetime

log_path = r'C:\Users\wifik\Desktop\projects\larger-lab\memory\2026-06-03.md'

entry = """
## Basket Backtest Results — Round 2 (K-Means Calibrated Configs) — 21:05 EDT

All 7 baskets completed with K-Means calibrated tier configs:

| Basket | Trades | WR | PnL (pips) |
|--------|--------|-----|------------|
| EUR | 6,345 | 87.4% | +46,084 |
| JPY | 4,671 | 88.8% | +48,397 |
| USD | 6,494 | 85.3% | +36,071 |
| AUD | 4,734 | 90.1% | +34,671 |
| NZD | 4,584 | 89.9% | +35,208 |
| CHF | 6,082 | 87.0% | +32,558 |
| CAD | 6,956 | 86.6% | +44,677 |
| **TOTAL** | **39,866** | **87.5%** | **+277,666** |

### Fixes Applied Today
1. asset_configs.py — Added 17 new FX cross pair configs (K-Means calibrated, percentile-capped). 37 total configs.
2. CSV loader bug — Fixed load_m5_csv to handle single 'time' column (PRO format files like EURGBP_PRO_M5.csv)
3. Both fixes committed to git (commits: d1f6add2, 4704dc39)

### Data Ranges
- Original pairs (EURUSD, GBPUSD, etc.): ~2022-01 to ~2026-05 (~4.5 years)
- New PRO pairs (EURGBP, EURJPY, etc.): ~2015-10 to ~2026-06 (~10.5 years)
- Trade counts vary by pair based on tier thresholds and qualifying sessions

### Live Bridge Status
- Bridge ran today: 61 trades, 41% WR, +$0.53
- Bridge not currently running (no open positions at 21:05 EDT)
- Fixed engine code (SL = impulse_extreme) NOT yet deployed to live
- Live WR (41%) still reflects old engine code with OCC extreme + buffer SL

### Next Steps
- Deploy fixed engine to MT5 demo for 24-48h testing
- Then deploy to live
- Consider running MC simulations on basket results
"""

with open(log_path, 'a') as f:
    f.write(entry)

print("Daily log updated.")
