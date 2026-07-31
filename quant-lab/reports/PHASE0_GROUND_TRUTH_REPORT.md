# PHASE 0: GROUND TRUTH CALIBRATION - DEFINITIVE BASELINE MATRIX

**Generated:** 2026-06-01 03:49:06 EST  
**Engine:** Nautilus (locked physics, no strategy changes)  
**Assets:** 19/19 (NAS100 missing data)

**ST Aggregate:** 17119 trades | avg WR 85.3% | -3992.6 pips  
**P90 Aggregate:** 6088 trades | avg WR 55.8% | +3233.2 pips

## Symmetry Trap (ST) - All Assets

| Asset | Trades | WR | PnL (pips) |
|-------|--------|-----|------------|
| AUDUSD | 1249 | 87.8% | +5328.6 |
| BTCUSD | 2014 | 86.9% | +219718.6 |
| CHFJPY | 0 | 0.0% | +0.0 * |
| DE30 | 0 | 0.0% | +0.0 * |
| ETHUSD | 777 | 94.7% | +11901.9 |
| EURUSD | 2186 | 82.1% | +8584.7 |
| FR40 | 56 | 96.4% | -329031.0 *** |
| GBPAUD | 1428 | 85.2% | +12529.2 |
| GBPCHF | 1161 | 89.9% | +7981.2 |
| GBPJPY | 0 | 0.0% | +0.0 * |
| GBPNZD | 1410 | 85.0% | +13936.1 |
| GBPUSD | 2234 | 83.5% | +11750.6 |
| HK50 | 0 | 0.0% | +0.0 * |
| NZDUSD | 833 | 91.6% | +4363.9 |
| US500 | 1 | 100.0% | +19.0 |
| USDCHF | 2050 | 81.6% | +7756.4 |
| USDJPY | 0 | 0.0% | +0.0 * |
| XAGUSD | 2 | 100.0% | +50.0 |
| XAUUSD | 1718 | 81.8% | +21118.2 |

## P90 Kinetic Engine - All Assets

| Asset | Trades | WR | PnL (pips) |
|-------|--------|-----|------------|
| AUDUSD | 527 | 49.1% | -35.8 |
| BTCUSD | 2 | 100.0% | +17.0 |
| CHFJPY | 0 | 0.0% | +0.0 * |
| DE30 | 0 | 0.0% | +0.0 * |
| ETHUSD | 99 | 83.8% | +391.0 |
| EURUSD | 1048 | 60.4% | +792.8 |
| FR40 | 0 | 0.0% | +0.0 * |
| GBPAUD | 380 | 47.9% | +81.0 |
| GBPCHF | 980 | 59.7% | +673.6 |
| GBPJPY | 0 | 0.0% | +0.0 * |
| GBPNZD | 255 | 48.6% | +133.9 |
| GBPUSD | 1297 | 53.1% | +396.9 |
| HK50 | 0 | 0.0% | +0.0 * |
| NZDUSD | 457 | 54.0% | +215.0 |
| US500 | 0 | 0.0% | +0.0 * |
| USDCHF | 841 | 57.4% | +258.6 |
| USDJPY | 0 | 0.0% | +0.0 * |
| XAGUSD | 0 | 0.0% | +0.0 * |
| XAUUSD | 202 | 54.5% | +309.2 |

## Issues & Errors

- Batch 2: GBPJPY: 0 trades for both strategies (no signals generated)
- Batch 2: GBPCHF: Exchange rate errors (CHD/USD) during backtest - results still generated
- Batch 2: GBPAUD: Exchange rate errors (AUD/USD) during backtest - results still generated
- Batch 2: GBPNZD: Exchange rate errors (NZD/USD) during backtest - results still generated
- Batch 4: CRITICAL: FR40 ST shows -329,031 pips loss — pip calculation likely broken when using Equity instrument type. Needs investigation.
- Batch 4: US500, DE30, HK50: near-zero trades on both strategies — equity instrument type may not feed bars correctly to the strategy engine
- Batch 4: FIX APPLIED: Added TestInstrumentProvider.equity() fallback for non-6-char symbols in get_instrument_and_venue()

**Legend:** *** = critical issue | * = zero trades

---
*Phase 0 Complete | Nautilus Ground Truth Matrix | Source of truth for CARE Engine PES calculations*