# Task Brief A — Cost Model Validation

> **Created:** 2026-05-18 08:00 EDT
> **Author:** Quant Lab Manager (SAGE-Directed)
> **Priority:** CRITICAL — Phase 0 Gate
> **Owner:** Optimizer

---

## Objective

Re-test ALL 10 CEREBUS strategies with a realistic cost model to determine which strategies actually survive real-world trading conditions.

## The Problem

All current backtest results use ZERO transaction costs. The "10/10 profitable" claim is based on:
- No spread costs
- No commission
- Fixed 0.05 lots (not risk-based sizing)
- No slippage

This is the same validation gap that plagued the pairs trading results. We must fix this BEFORE any strategy touches TradingView.

## Cost Model Requirements

### 1. Real Spread Data (MAD Directive: Calculate from CSV)
- Source: CSV files in `C:\Users\wifik\Downloads\` (27 files)
- The CSVs already have a `<SPREAD>` column — USE IT DIRECTLY
- **⚠️ CRITICAL: Spread is in POINTS, not pips.** For 5-digit forex pairs: **1 pip = 10 points**
  - Example: EUR/USD CSV shows spread of 144 points = **14.4 pips** (144 ÷ 10)
  - Example: USD/JPY CSV shows spread of 115 points = **11.5 pips** (115 ÷ 10)
  - For JPY pairs (3-digit): 1 pip = 10 points as well (the CSV already normalizes this)
  - For indices (US500, DE30, etc.): spread is in index points (dollars), NOT pips — handle separately
- **Calculate the median spread per pair from the CSV data itself** — don't hardcode values
- Read the CSV, extract the SPREAD column, compute median per pair, then **divide by 10 to get pips**
- Apply spread cost on BOTH entry and exit (round-turn = 2x spread in pips)
- CSV format: tab-separated, columns: DATE, TIME, OPEN, HIGH, LOW, CLOSE, TICKVOL, VOL, SPREAD
- **Conversion formula:** `spread_pips = median(CSV_SPREAD_column) / 10`
- For indices: spread is already in dollar units (no pip conversion needed)

### 2. Commission: $7/lot round-turn
- This is a standard ECN/prime broker commission
- Applied to both entry and exit (round-turn = $7 total per lot)
- For 0.05 lots: $0.35 per round-turn
- For 5% risk sizing: commission scales with position size

### 3. Position Sizing: 5% of Equity per Trade
- Starting equity: $10,000 (standard test account)
- 5% risk = $500 maximum loss per trade
- Position size = $500 / (stop_loss_in_pips * pip_value)
- NOT fixed 0.05 lots — this is the critical change
- This means position sizes will vary per strategy based on their stop loss distance

### 4. Slippage: Minimum 1 pip
- Apply 1 pip slippage on both entry and exit
- This is conservative but realistic for forex

## Strategies to Validate

All 10 strategies from the v4 backtest:

| # | Strategy | Current WR | Current PnL | Current PF | Current MaxDD |
|---|----------|-----------|-------------|------------|---------------|
| 1 | Composite_Alpha | 98.6% | +3537p | 703 | -1.5p |
| 2 | Deep_Mean_Reversion | 91.8% | +8746p | 112 | -5.0p |
| 3 | Failure_Repair | 50.0% | +817p | 1.81 | -68.2p |
| 4 | Dual_Engine | 51.2% | +757p | 1.60 | -49.1p |
| 5 | Blind_Structural_Chain | 43.1% | +2248p | 1.14 | -963.8p |
| 6 | P90P_Distribution | 20.0% | +150p | 1.14 | -156.2p |
| 7 | Two_Plays | 42.3% | +53p | 1.04 | -216.5p |
| 8 | Fractal_Resolution | 43.7% | +207p | 1.03 | -687.2p |
| 9 | Stall_Harvest | 40.1% | -3p | 1.00 | -80.1p |
| 10 | Constraint_Anchor | 36.2% | -249p | 0.90 | -292.4p |

## Data Files

Location: `C:\Users\wifik\Downloads\`
- 27 CSV files covering: EUR/USD, USD/CHF, GBP/USD, USD/JPY, USD/CAD, AUD/USD, NZD/USD, CHF/JPY, DE30, FR40, US500, USTEC100
- Timeframes: M1 and M5
- Must inspect CSV headers to identify bid/ask columns

## Expected Output

Save results to: `quant-lab/results/cost-validation-2026-05-18.md`

Format:
```
For each strategy:
- Strategy name
- Pair(s) tested
- Cost model parameters used (spread source, commission, sizing method)
- Results table: WR, PnL, PF, MaxDD (with costs)
- Comparison: before costs vs after costs
- Verdict: SURVIVES / FAILS cost model
```

## Success Criteria

A strategy "survives" if:
1. Profit Factor > 1.5 (after all costs)
2. Max Drawdown < 15% of equity
3. Win Rate > 40%
4. Net PnL > 0

## Estimated Effort

- Inspect CSV format: 15 min
- Extract spread data per pair: 30 min
- Modify backtest engine for cost model: 1-2 hours
- Run all 10 strategies: 30 min - 2 hours (depending on data size)
- Write results doc: 30 min

**Total: 3-5 hours**

## Dependencies

- None. This is the first task in Phase 0.

## Notes

- The Composite_Alpha (98.6% WR, PF 703) is almost certainly going to collapse under real costs. This is expected — the question is by how much.
- Deep_Mean_Reversion is the most likely to survive given its strong baseline metrics.
- Strategies with high trade frequency will be hit hardest by spread + commission costs.
- The 5% risk sizing may actually HELP some strategies (larger positions on high-conviction setups) and HURT others (larger losses on bad trades).

---

*Task Brief A — Cost Model Validation — Manager 2026-05-18 08:00 EDT*
