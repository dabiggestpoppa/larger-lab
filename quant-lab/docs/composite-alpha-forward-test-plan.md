# Composite Alpha — Forward Test Plan

> **Date:** 2026-05-18
> **Author:** Quant Lab Manager
> **Status:** Pre-test planning
> **Suspicion Level:** HIGH — 98.6% WR likely overfit

---

## 1. Background

Composite_Alpha showed extraordinary backtest results:
- **98.6% Win Rate** (282 wins / 286 trades)
- **PF 703** before costs, ~285 after costs
- **Only 286 trades over 3+ years** (~1 trade/day)

These numbers are almost certainly overfit. The strategy combines 5 alpha signals using IC-weighted scoring, which creates many degrees of freedom for curve-fitting. This forward test will determine whether the edge is real or an artifact of overfitting.

---

## 2. Data for Forward Testing

### Available Data
| File | Date Range | Size | Use |
|------|-----------|------|-----|
| `EURUSD.PRO_202407010000_202605132122.csv` | 2024-07-01 to 2026-05-13 | 3.06 GB | **Primary forward test data** |

### In-Sample Period (Original Backtest)
- Estimated: 2023-01-01 to 2024-06-30 (based on v4b optimizer run)

### Out-of-Sample Period (Forward Test)
- **Phase A:** 2024-07-01 to 2024-12-31 (6 months) — Initial validation
- **Phase B:** 2025-01-01 to 2025-06-30 (6 months) — Extended validation
- **Phase C:** 2025-07-01 to 2026-05-13 (~10 months) — Full validation

---

## 3. Success Criteria

### Primary Criteria (ALL must be met)
| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| **Win Rate** | > 60% | Well below 98.6% but still profitable after costs |
| **Profit Factor** | > 2.0 | Survives 2.9 pip/trade cost model |
| **Max Drawdown** | < 15% of equity | Risk management threshold |

### Secondary Criteria (2 of 3 must be met)
| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| **Trade Count** | > 100 in 6 months | Sufficient sample size |
| **Avg Win / Avg Loss** | > 1.5 | Positive expectancy |
| **Sharpe Ratio** | > 1.0 | Risk-adjusted returns |

### Failure Criteria (ANY triggers halt)
| Metric | Threshold | Action |
|--------|-----------|--------|
| Win Rate | < 45% | Strategy is broken — stop test |
| Max Drawdown | > 25% | Risk too high — stop test |
| Consecutive Losses | > 10 | Edge may have disappeared |

---

## 4. Test Procedure

### Step 1: Data Preparation
```python
# Extract forward test data from EURUSD.PRO CSV
# Filter to trading hours (2AM-5PM EST)
# Calculate spread from BID/ASK columns
# Resample to M5 candles
```

### Step 2: Run Strategy Unchanged
- Use the EXACT same parameters from the in-sample backtest
- NO parameter optimization on forward data
- Apply real cost model: 0.2 pip spread + $7/lot commission + 2 pip slippage

### Step 3: Phase Gates
- **After Phase A (6 months):** If WR > 55% and PF > 1.5, proceed to Phase B
- **After Phase B (12 months):** If WR > 58% and PF > 1.8, proceed to Phase C
- **After Phase C (22 months):** Final evaluation against success criteria

### Step 4: Analysis
- Compare forward test WR to backtest WR (expect degradation)
- Analyze which of the 5 signals contributed most/least
- Check if performance degrades over time (regime change sensitivity)
- Document any parameter sensitivity

---

## 5. Expected Outcomes

### Scenario A: Edge is Real (20% probability)
- Forward WR: 65-75%
- Forward PF: 3-10
- **Action:** Convert to PineScript/MQL5, push to TradingView

### Scenario B: Mild Overfit (50% probability)
- Forward WR: 50-60%
- Forward PF: 1.5-3.0
- **Action:** May still be viable with tighter filters. Investigate signal degradation.

### Scenario C: Severe Overfit (30% probability)
- Forward WR: < 50%
- Forward PF: < 1.5
- **Action:** Abandon. The 98.6% WR was curve-fitting.

---

## 6. Risk Controls

1. **Paper trade only** — No real money until Phase C passes
2. **Max 2% risk per trade** during forward testing (more conservative than 5%)
3. **Kill switch** — If 5 consecutive losses, pause and investigate
4. **Monthly review** — Check performance against criteria at end of each month

---

## 7. Timeline

| Phase | Period | Duration | Decision Point |
|-------|--------|----------|----------------|
| Setup | 2026-05-18 | 1 day | Data extraction + script prep |
| Phase A | 2024-07 to 2024-12 | 6 months of data | Go/No-Go |
| Phase B | 2025-01 to 2025-06 | 6 months of data | Go/No-Go |
| Phase C | 2025-07 to 2026-05 | 10 months of data | Final verdict |

**Estimated total processing time:** 2-4 hours of computation on the 3GB CSV

---

## 8. Notes

- The 98.6% WR is the highest of any strategy in the lab. This is a red flag, not a badge of honor.
- The strategy makes only ~1 trade/day, which means 286 trades = 286 trading days = ~1.5 years of data. This is a small sample.
- The IC-weighted composite approach is sophisticated but may be fitting noise. Forward testing will reveal this.
- If the strategy fails, the 5 individual signals may still be useful as filters for other strategies.

---

*Forward Test Plan — Quant Lab Manager, 2026-05-18*
*Status: Awaiting execution*
