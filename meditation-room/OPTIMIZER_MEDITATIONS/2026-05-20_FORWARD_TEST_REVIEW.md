# OPTIMIZER MEDITATION — 2026-05-20 04:19 EST

## Forward Test Script Review

**Logic assessment of `dmr_mt5_forward_test.py`:**

✅ **Correct elements:**
- P90 threshold lookup matches backtest parameters (4.1-6.2 pips by hour)
- Deep State = activation + 2.00× body, Kill Switch = activation + 2.20× body
- Mean reversion direction (trade AGAINST P90 direction) — correct
- TP at activation (mean reversion target) — correct
- One trade per day limit — appropriate for forward test
- Hard exit at 5PM EST — good risk control
- State persistence via JSON — survives restarts

⚠️ **Potential issues:**
1. **Single-asset only (EURUSD.PRO):** The backtest showed DMR works on all 4 pairs. Consider adding USDCHF.PRO as secondary if EURUSD has a quiet day.
2. **IOC filling (`ORDER_FILLING_IOC`):** May fail during low-liquidity hours. Consider `ORDER_FILLING_RETURN` as fallback for the 2-4 AM window.
3. **No spread check:** If spread widens beyond normal (e.g., news events), the script still trades. Should add a spread filter — skip if spread > 2× normal for that hour.
4. **DS touch detection uses same-day bars only:** If DS touch happens after a late P90 signal, the bar window is small. This is conservative but correct.

## Lot Size Assessment

**0.01 lots is appropriate.** MC confirmed:
- 0% ruin probability at 0.01 lots
- MaxDD < 5.5 pips
- 100% probability of profit over 10K iterations

**Recommendation:** Start at 0.01 for 1 week. If WR holds >85% in forward test, scale to 0.02. Don't rush — the edge is proven, let the forward test confirm it in live conditions.

## What MAD Should Look For

When reviewing the first forward test trade, check:

1. **Entry timing:** P90 should fire between 2-11 AM EST. DS touch should follow within 30-90 min.
2. **Fill quality:** Slippage should be < 0.5 pips on EURUSD.PRO demo.
3. **SL/TP placement:** SL at KS (2.2× body from activation), TP at activation. Verify on chart.
4. **Trade duration:** Most winners close within 2-6 hours. If a trade stays open >8 hours, something is off.
5. **Daily PnL pattern:** Expect +5-15 pips on winning days, -8 to -12 pips on losing days (KS hit).

## Overlay Strategy Readiness

The proposed overlay (03:00-05:00 + T3/T4 + Tue-Thu + multi-asset confirmation) is sound but **NOT ready for forward test yet.** First, validate the base DMR in live conditions. Add overlays only after 20+ forward test trades confirm the base edge holds.

## Verdict

**Script is production-ready for forward test.** Minor improvements (spread check, fallback filling) can be added after first week of data. The core logic matches the validated backtest exactly.

---
*Optimizer Meditation — 2026-05-20 04:19 EST*
