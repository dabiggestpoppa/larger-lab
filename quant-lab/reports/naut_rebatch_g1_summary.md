# Nautilus Rebatch Group 1 — Results Summary

**Date:** 2026-06-01 04:39 EST  
**Runner:** `run_cerebus_backtest.py` (CEREBUS FX v4.0)  
**Data:** M5 bars, full history (~273K-277K bars per asset)  
**Assets:** EURUSD, GBPUSD, USDCHF, USDJPY, AUDUSD

---

## Results Matrix

| Asset | Strategy | Trades | Win Rate | PnL (pips) |
|-------|----------|--------|----------|------------|
| EURUSD | Symmetry Trap | 2,186 | 82.1% | +8,584.7 |
| EURUSD | P90 | 1,048 | 60.4% | +792.8 |
| GBPUSD | Symmetry Trap | 2,234 | 83.5% | +11,750.6 |
| GBPUSD | P90 | 1,029 | 61.1% | +890.1 |
| USDCHF | Symmetry Trap | 2,050 | 81.6% | +7,756.4 |
| USDCHF | P90 | 726 | 59.9% | +292.7 |
| USDJPY | Symmetry Trap | 1,473 | 84.6% | +12,108.7 |
| USDJPY | P90 | 326 | 65.0% | +787.7 |
| AUDUSD | Symmetry Trap | 1,249 | 87.8% | +5,328.6 |
| AUDUSD | P90 | 458 | 50.2% | -141.2 |

---

## Aggregate

| Metric | Symmetry Trap | P90 |
|--------|--------------|-----|
| Total Trades | 9,192 | 3,587 |
| Avg Win Rate | 83.9% | 59.3% |
| Total PnL (pips) | +45,529.0 | +2,622.1 |
| Profitable Assets | 5/5 | 4/5 |

---

## Key Observations

1. **Symmetry Trap dominates across all 5 assets** — 81.6%-87.8% WR, massive pip counts
2. **P90 is profitable on 4/5 assets** — AUDUSD is the only loser (-141.2 pips at 50.2% WR)
3. **USDJPY Symmetry Trap** has the highest pip count (+12,108.7) despite fewer trades — larger per-trade gains
4. **AUDUSD Symmetry Trap** has the highest WR (87.8%) with 1,249 trades
5. **P90 on USDJPY** has the best P90 WR (65.0%) but fewest trades (326)
6. **Trade frequency:** Symmetry Trap generates 2.5-3x more trades than P90 across all pairs

---

## Individual Reports

- `NAUTILUS_SYMMETRY_TRAP_EURUSD_20260601_043513.json`
- `NAUTILUS_P90_EURUSD_20260601_043538.json`
- `NAUTILUS_SYMMETRY_TRAP_GBPUSD_20260601_043605.json`
- `NAUTILUS_P90_GBPUSD_20260601_043631.json`
- `NAUTILUS_SYMMETRY_TRAP_USDCHF_20260601_043708.json`
- `NAUTILUS_P90_USDCHF_20260601_043733.json`
- `NAUTILUS_SYMMETRY_TRAP_USDJPY_20260601_043827.json`
- `NAUTILUS_P90_USDJPY_20260601_043900.json`
- `NAUTILUS_SYMMETRY_TRAP_AUDUSD_20260601_043924.json`
- `NAUTILUS_P90_AUDUSD_20260601_043951.json`
