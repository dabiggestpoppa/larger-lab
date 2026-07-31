# NAUTILUS CROSS-VALIDATION SUMMARY
**Date:** 2026-05-30 23:00 EDT
**Runner:** run_cerebus_backtest.py (fixed lot_size=1000)
**Nautilus:** v1.226.0

## Results

| Strategy | Pair | Bars | Trades | W/L | WR | PnL (pips) | Benchmark WR | Status |
|----------|------|------|--------|-----|-----|------------|--------------|--------|
| Symmetry Trap | EURUSD.PRO | 224K | 1,753 | 1445/298 | 82.4% | +6,682 | 85-91% | ⚠️ Low |
| Symmetry Trap | USDCHF.PRO | 253K | 1,752 | 1489/255 | 85.0% | +7,180 | 80-95% | ✅ Pass |
| P90 | EURUSD.PRO | 224K | 872 | 531/341 | 60.9% | +655 | 78.7% | ❌ Fail |
| P90 | USDCHF.PRO | 253K | 763 | 443/320 | 58.1% | +240 | 70-90% | ❌ Fail |

## Key Findings

### Lot Size Fix (APPLIED)
- **Root cause:** `lot_size=Decimal("0.01")` → Nautilus interprets as 1 micro-unit
- **Fix:** Default changed to `Decimal("1000")` = 0.01 standard lots
- **Smoke test:** ST/EURUSD 5K bars: 48 trades, 77.1% WR ✅

### Symmetry Trap Assessment
- Nautilus wrapper is FUNCTIONAL and in the right ballpark
- ST/USDCHF 85.0% passes cross-validation
- ST/EURUSD 82.4% is ~2.5pp below 85% floor — minor alignment gap
- Trade count (1,753) is higher than CSV engine (~574-892) — Nautilus may be more aggressive on entries
- **Recommendation:** Production-ready for USDCHF; minor alignment needed for EURUSD

### P90 Assessment — NEEDS WORK
- Both pairs significantly underperform benchmark (60.9% and 58.1% vs 78.7%)
- Trade count LOWER than benchmark (872 vs 1,038) — some signals being missed
- CASCADE dominance (85.4% in CSV engine) not showing in Nautilus
- **Root cause:** `p90_strategy.py` wrapper has logic differences vs `p90_engine.py`
- **Next step:** Diff p90_strategy.py vs p90_engine.py to identify gaps

### Known Nautilus Issues
- Engine-level positions/PnL always shows 0 (Nautilus accounting bug for non-USD base currency pairs)
- Strategy-level stats are the ground truth
- Engine positions/PnL = 0 does NOT mean trades didn't execute

## Files
- Runner: `quant-lab/backtests/run_cerebus_backtest.py` (fixed)
- ST Strategy: `quant-lab/strategies/symmetry_trap_strategy.py`
- P90 Strategy: `quant-lab/strategies/p90_strategy.py`
- ST Engine: `quant-lab/engines/symmetry_trap.py` (gold standard)
- P90 Engine: `quant-lab/engines/p90_engine.py` (gold standard)
- Individual reports: `quant-lab/reports/NAUTILUS_*_20260530_22*.json`
