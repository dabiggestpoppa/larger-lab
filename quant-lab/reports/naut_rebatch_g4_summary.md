# Nautilus Rebatch — Group 4: Index Instruments

**Date:** 2026-06-01 05:41 EST  
**Group:** 4 (Index/CFD instruments)  
**Strategies:** Symmetry Trap Engine B, P90 Kinetic Engine A  
**Data:** M5 bars from `quant-lab/data/{SYMBOL}_M5.csv`

---

## Results Summary

### US500 (260,958 bars)

| Strategy | Trades | Win Rate | PnL (pips) |
|----------|--------|----------|-------------|
| Symmetry Trap | 393 | 90.3% | +2,718.8 |
| P90 | 144 | 78.5% | +260.8 |

**Verdict:** Symmetry Trap dominant. Both strategies profitable. Highest combined WR.

---

### DE30 (257,602 bars)

| Strategy | Trades | Win Rate | PnL (pips) |
|----------|--------|----------|-------------|
| Symmetry Trap | 2,459 | 76.5% | +28,306.5 |
| P90 | 610 | 65.6% | +463.5 |

**Verdict:** Symmetry Trap has massive trade count and PnL. P90 profitable but lower edge.

---

### FR40 (253,878 bars)

| Strategy | Trades | Win Rate | PnL (pips) |
|----------|--------|----------|-------------|
| Symmetry Trap | 1,705 | 83.3% | +12,589.7 |
| P90 | 1,222 | 64.5% | -800.3 |

**Verdict:** Symmetry Trap strong. P90 **unprofitable** on FR40 — negative PnL despite 64.5% WR ( losers are larger than winners).

---

### HK50 (242,271 bars)

| Strategy | Trades | Win Rate | PnL (pips) |
|----------|--------|----------|-------------|
| Symmetry Trap | 425 | 92.9% | +17,006.2 |
| P90 | 0 | 0.0% | 0.0 |

**Verdict:** Symmetry Trap excellent (92.9% WR!). P90 generated **zero trades** — strategy never triggered (likely instrument size/lot constraints on HK50).

---

### NAS100

| Strategy | Status |
|----------|--------|
| Symmetry Trap | ❌ ERROR — No data file (`NAS100_M5.csv` not found) |
| P90 | ❌ ERROR — No data file (`NAS100_M5.csv` not found) |

---

## Overall Group 4 Analysis

| Metric | Symmetry Trap | P90 |
|--------|--------------|-----|
| Total Trades | 4,982 | 1,976 |
| Avg Win Rate | 85.8% | 69.5% |
| Total PnL (pips) | +60,621.2 | -76.0 |
| Profitable Assets | 4/4 | 2/4 |

### Key Findings:

1. **Symmetry Trap is dominant across all indices** — 85.8% avg WR, massive trade counts, consistently profitable.
2. **P90 struggles on indices** — Only 2/4 profitable. Lost money on FR40, zero trades on HK50.
3. **FR40+P90 is a bad combination** — Negative PnL despite >64% WR indicates large losses on losing trades.
4. **HK50+P90 is a no-go** — P90 never triggered (lot size or instrument constraints).
5. **NAS100 missing** — Data file not available. Need to acquire NAS100_M5.csv.

### Recommended Index Config:
- **All indices**: Symmetry Trap only
- **P90**: Skip on indices (designed for FX)

---

*Generated: 2026-06-01 05:41 EST*
*Engine: CEREBUS FX v4.0 (Nautilus Trader)*
*Script: quant-lab/backtests/run_cerebus_backtest.py*
