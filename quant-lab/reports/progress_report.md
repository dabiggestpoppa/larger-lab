# CEREBUS Progress Report — Pre-Deployment

**Date:** 2026-06-04
**Status:** Accuracy-frequency curve fully mapped. Deployment configs pending MAD selection.

---

## The Journey: From 38% WR to 90%+

### Where We Started

The CEREBUS engine had a critical bug: the MT5 live engine used different SL logic than the Nautilus backtest strategy that produced 85% WR in Phase 0 ground truth. The live engine added a spread buffer + min floor to the OCC extreme, placing stops 8-15 pips from entry — instant stop-outs on M5 noise. Result: **38-44% WR live** vs 85% in backtest.

### The Fixes

1. **ST SL Fix**: Changed MT5 engine SL to `impulse_extreme` (zero-buffer) — matching Nautilus strategy exactly
2. **Bridge send_order Fix**: Removed aggressive SL/TP clamping — bridge now trusts engine values
3. **Duplicate Executor Kill**: Killed 4 stale processes running old buggy code
4. **EWS_EXIT Missing from Bridge**: Added exit handling
5. **AR Gate Decoupling**: Separated session filtering from tier classification — AR no longer conflates the two
6. **Impulse-Based Tier Classification**: T1/T2/T3 now classified by impulse leg size only, independent of AR
7. **Session Cutoff**: Changed from 12PM to 4PM EST
8. **Dead Code Removal**: 4h timeout, 80% kill switch, dynamic DZ — all removed (0% delta in A/B test)

### Where We Are Now

The accuracy-frequency curve is **fully mapped** across all 28 forex pairs. We know the exact tradeoff between trade frequency and win rate for every pair, at every trigger setting.

---

## The Curve: What It Means

### The Two Extremes

| Metric | Floor (Max Trades) | Ceiling (Max Accuracy) |
|--------|-------------------|----------------------|
| Total Trades | ~158,375 | 29,438 |
| Avg WR | 81.1% | 90.8% |
| Avg PF | ~11.5 | ~29.0 |
| Avg R:R | 2.81 | 2.80 |
| Avg Trades/Day | ~3.0 | ~0.59 |
| Pairs with Valid Config | 28/28 | 21/28 |

### The Key Insight

**R:R is invariant.** It stays at ~2.8 whether you're trading at the floor or the ceiling. The edge comes entirely from WR improvement — from 81% to 90%+. Trigger selection is a pure frequency filter: higher triggers mean fewer trades, but each one has a higher probability of winning.

This is a very good sign. It means the engine's core behavior is stable and not curve-fitting to R:R artifacts. The SL/TP logic is the same at all trigger levels — only the entry threshold changes.

### The "Knee"

The optimal operating point is likely not at either extreme, but somewhere in between — where you capture most of the WR improvement while retaining enough trade flow for diversification. Sage estimates this at roughly **WR 85-88%, ~1.0-1.5 trades/day, PF 15-20**.

---

## The Numbers

### Top 5 Ceiling Performers

| Asset | WR | PF | Trades/Day | R:R |
|-------|-----|-----|-----------|-----|
| NZDUSD | 95.5% | 58.41 | 0.59 | 2.69 |
| AUDUSD | 94.2% | 63.14 | 0.59 | 3.73 |
| GBPAUD | 93.4% | 38.81 | 0.52 | 2.67 |
| GBPNZD | 93.3% | 39.46 | 0.51 | 2.85 |
| USDCHF | 93.2% | 26.09 | 0.72 | 1.88 |

### Pairs With No Valid Ceiling (native <0.5 tr/day)

EURJPY, EURAUD, EURNZD, AUDJPY, NZDJPY, CADJPY

These are inherently low-frequency pairs. They should run at floor or near-floor configs.

---

## What's Next: Deployment

### Immediate Steps

1. **MAD selects operating point per pair** — floor, ceiling, or knee
2. **OWL codes deployment configs** for MT5 bridge
3. **Audit JPY pip-value math** in bridge (CEO recommendation — critical bug class)
4. **Daily reconciliation process** from day one

### Recommended Architecture (Sage)

- **Tier 1 (Ceiling)**: Top 5 performers — NZDUSD, AUDUSD, GBPAUD, GBPNZD, USDCHF
- **Tier 2 (Knee)**: Middle 17 pairs — blended configs
- **Tier 3 (Floor)**: 6 low-frequency JPY crosses — maximum volume

### Risk Parameters (CEO)

- **Drawdown tolerance**: 15-20% with 25% hard stop
- **Position sizing**: 1.5x premium for ceiling, standard for floor
- **Kill threshold**: Rolling 30-day WR < 70% on any Tier 1 pair → pause and fall back to floor
- **First 200 live trades**: No intervention — let the edge express itself

---

## Files

- `reports/trigger_sweep_max_accuracy.json` — Full curve data (every trigger tested)
- `reports/trigger_sweep_*.json` — Floor sweep data per basket
- `reports/rr_summary.md` — R:R analysis across all configs
- `reports/sage_analysis.md` — Strategic analysis
- `reports/ceo_analysis.md` — Business/ops analysis
- `MEMORY.md` — Updated Bible

---

*The curve is mapped. The edge is real. The question now is execution.*
