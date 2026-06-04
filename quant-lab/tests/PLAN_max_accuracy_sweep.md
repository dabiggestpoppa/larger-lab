# MAX ACCURACY SWEEP — Test Plan

## Objective
Find the **maximum WR** trigger configuration for each FX pair by sweeping triggers **upward** from native, establishing the **ceiling** of the accuracy-frequency curve.

## Context
- **Floor already established:** Max-trades trigger sweep (completed 2026-06-04) found the lowest T1 trigger keeping WR≥81% → max trades
- **Ceiling needed:** This sweep finds the highest T1 trigger that maximizes WR while maintaining minimum trade frequency
- **Middle derivable:** Any point between floor and ceiling can be interpolated from the two boundary datasets

## Methodology

### Sweep Direction: UP (opposite of max-trades sweep)
- **Start:** Native T1 trigger (from asset_configs.py)
- **Direction:** Increase trigger (tighter entries = fewer but more selective trades)
- **Step size:** Coarse +2.0p steps upward, then fine +1.0p, then binary search

### Phases (same structure as trigger_sweep_v2)
1. **Coarse sweep UP:** native → native+2 → native+4 → ... up to 2x native OR until trades < 0.5 tr/day
2. **Fine sweep:** +1.0p steps around the WR peak region
3. **Binary search:** Pinpoint the trigger that maximizes WR within the peak region

### Guardrails
- **WR:** Maximize (no floor — we want the peak)
- **PF:** ≥ 10.0 (must remain profitable)
- **Min trade frequency:** ≥ 0.5 tr/day (don't want near-zero trade strategies)
- **MaxDD:** Track but not a hard gate (report for analysis)

### Per-Pair Output (MUST be tracked and stored)
For **every** trigger tested, store:
- T1 trigger value
- Total trades
- Trade frequency (tr/day)
- Win rate (WR%)
- Profit factor (PF)
- Total PnL (pips)
- Max drawdown (pips)
- Max consecutive losses
- Avg win / avg loss (pips)
- Expectancy (pips)
- Full tier config used

### Output Files
- `reports/trigger_sweep_max_accuracy.json` — ALL results for ALL pairs (complete curve data)
- `reports/trigger_sweep_max_accuracy_summary.md` — Summary table with best config per pair

## Scope
All 28 pairs from the completed max-trades sweep:
- EUR: EURUSD, EURGBP, EURJPY, EURAUD, EURNZD, EURCHF, EURCAD
- GBP: GBPUSD, GBPAUD, GBPCAD, GBPCHF, GBPJPY, GBPNZD
- AUD: AUDUSD, AUDCAD, AUDCHF, AUDJPY, AUDNZD
- NZD: NZDUSD, NZDCAD, NZDCHF, NZDJPY
- USD: USDCAD, USDCHF, USDJPY
- CAD: CADCHF, CADJPY
- CHF: CHFJPY

## Engine Config
- AR Expansion: 3.0x (same as max-trades sweep)
- Session cutoff: 4PM EST (16:00)
- DZ: flat 20-50% for all loops (same as THE BIBLE config)

## Execution
- One pair at a time, sequential within each basket
- All 28 pairs across 7 baskets
- Estimated runtime: ~2-3 hours total

## Combinatorics Value
With both floor (max-trades) and ceiling (max-accuracy) curves stored:
- Any intermediate trigger can be derived via interpolation
- Full accuracy-frequency curve available for portfolio optimization
- Can compute optimal trigger per pair for any target trade frequency
