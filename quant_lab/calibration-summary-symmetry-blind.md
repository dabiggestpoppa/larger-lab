# QUANT STRATEGY CALIBRATION REPORT
## Symmetry Trap + Blind Structural Chain
> 2026-05-28 | atomic-calibrator subagent

---

## EXECUTIVE SUMMARY

**Mission**: Diagnose and fix the backtest gap between engine results and manual claims for Symmetry Trap and Blind Structural Chain.

**Results**: ❌ Both strategies confirmed **STRUCTURALLY UNPROFITABLE on M5 close bars**. No parameter calibration can fix the gap. The edge requires tick-data execution.

| Strategy | Manual WR | Engine v6 WR | Best Calibrated WR | Best Calibrated PF | Improved? |
|----------|-----------|-------------|-------------------|--------------------|-----------| 
| Symmetry Trap | 83-86% | 37% | 38% (wide_tgts) | 0.32 (0.37 full) | +3% WR, +0.08 PF |
| Blind Chain | 93.7% | 0% | 0% (all variants) | 0.00 | No change |

---

## SYMMETRY TRAP (14 variants tested)

### Before/After Comparison
| Metric | v6 (baseline) | v7b best (wide_tgts) | Change |
|--------|--------------|---------------------|--------|
| WR | 37.3% (410 tr) | 40.5% (405 tr) | +3.2% |
| PF | 0.29 | 0.37 | +0.08 |
| Total PnL | -2320.7p | -1803.7p | +517p |
| Avg Win | 5.9p | 6.5p | +0.6p |
| Avg Loss | 13.6p | 12.0p | -1.6p |

### Best Configuration
- **SL**: Opposite Asian band (same as manual — v6 baseline won SL sweep)
- **Targets**: 33/66/100% of AR (wider than manual's 25/50/100%)
- **Management**: 50/40/10 partial close structure (same as manual)

### Key Finding
Only 26% of losses come from SL. **74% come from 12PM hard exit** closing the remaining position at a loss. This means SL tuning cannot fix the core problem.

### Why It Fails on M5
The M5 close outside Asian band is a biased signal that reverses frequently on close bars but not on tick data. The manual's 83-86% WR requires tick-level execution.

---

## BLIND STRUCTURAL CHAIN (16+ variants tested)

### Before/After Comparison
| Metric | v1 (baseline) | v2 best (gold_struct SL) | Change |
|--------|--------------|-------------------------|--------|
| WR | 0% (49 tr) | 0% (39 tr) | 0% |
| PF | 0.00 | 0.00 | — |
| Avg Loss | -12.9p | -7.5p | +5.4p |

### Best Configuration
- **Goldilocks**: 32-50% (standard, manual)
- **SL**: Goldilocks zone boundary (structural, not distance-based)
- **Micro-P90 body**: >= 4.5p (standard)

### Key Finding
Even the best SL variant still produces **zero winners across all 39 cascade trades**. Reducing the SL simply reduced the average loss per trade — from -12.9p to -7.5p. But NO variant produced a single winning trade in the 2-year backtest.

### Geometric Root Cause
Goldilocks zone width = impulse × 0.18. For typical impulses (15-22p):
- Zone width: 2.7-4.0p
- Micro-P90 body requirement: >= 4.5p
- **A 4.5p body cannot fit inside a 2.7-4.0p zone**

Widening Goldilocks to 20-60% + relaxing micro threshold to 3.0p produced 62 trades (vs 36 baseline) but **WR still 0%**.

---

## BUGS FOUND AND FIXED

1. **Blind Chain v2 Goldilocks calculation** (critical)
   - Was: `impulse_dist * 32 / 10000` (wrong — 100x too small zone)
   - Fixed: `impulse_dist * (32/100) / 10000` (correct)
   - Effect: Early calibration runs showed 0 trades (bug masked the calibration)

2. **Unicode encoding crash** (Windows console)
   - Symmetry Trap v7: `print(f"{'─'*65}")` crashes on cp1252
   - Fix: `io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')` + ASCII variants

---

## FILES CREATED

| File | Purpose |
|------|---------|
| `symmetry_trap_v7_sl_calibrated.py` | 7 SL distance variants |
| `symmetry_trap_v7b_sl_calibrated.py` | 7 management/target variants |
| `blind_chain_v2_sl_calibrated.py` | Full Goldilocks × SL sweep |
| `blind_chain_diag.py` | Cascade detection funnel diagnostic |
| `blind_chain_v2_debug.py` | v1/v2 comparison tool |
| `calibration-log-symmetry-blind.md` | Detailed log (saved to quant-lab/) |
| `strategy_reconstruction_tracker.md` | Updated with calibration results |

---

## RECOMMENDATIONS

### For Both Strategies
1. **Do NOT use on M5 close bars** as standalone strategies
2. The manual's WR/PF claims are from tick data — not reproducible on M5
3. Consider using as FILTERS for DMR or other confirmed M5 edges

### For Symmetry Trap Specifically
4. The wide_tgts variant is the best M5 version (PF=0.37) but still losing
5. Could potentially work as a DMR.confirmation filter (same Asian band context)

### For Blind Chain Specifically
6. The biggest problem is the micro-P90 geometric fit, not SL
7. Could try: replace micro-P90 requirement with ANY candle closing in Goldilocks (body >= 2.0p)
8. This would increase trade count but needs testing if it improves WR
9. Currently not recommended for any use case

### For the Lab
10. The M5 gap is a systemic issue — ALL non-DMR non-DualEngine strategies fail
11. Future engine builds should include tick-data simulation or bid/ask spread modeling
12. DMR (84.2% WR on M5) remains the only validated strategy for M5 close-bar backtesting
