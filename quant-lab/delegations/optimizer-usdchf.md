# [Manager → Optimizer] Task C: USD/CHF Backtest (Goal 5)

> **From:** Manager v5 | **To:** Optimizer | **Priority:** 3 (GOAL 5)
> **Created:** 2026-05-18 00:30 EDT
> **Depends on:** Cost model from Task A (use same cost parameters)

---

## Objective

Backtest the top-performing strategies from EUR/USD on USD/CHF M5 data. This validates whether the edge transfers to a second major pair (Goal 5).

---

## Strategies to Backtest

### Primary: Deep_Mean_Reversion
- **Why:** 91.8% WR, PF 111.96 on EUR/USD — the flagship strategy
- **Reference:** `projects/trading/nautilus/strategies/optimizer_v4.py` → `run_deep_mean_reversion()`

### Top 3 Additional (by Profit Factor from V4):
1. **Constraint_Anchor** — PF 1.85, 51.1% WR
2. **P90P_Distribution** — PF 1.42, 26.3% WR (high R:R)
3. **Stall_Harvest_CFD** — PF 1.48, 30.7% WR

---

## Data File

**USD/CHF M5:**
```
C:\Users\wifik\Downloads\USDCHF!_M5_202301020000_202605061250.csv
```

**Format (confirmed):**
```
<DATE>  <TIME>  <OPEN>  <HIGH>  <LOW>  <CLOSE>  <TICKVOL>  <VOL>  <SPREAD>
2023.01.02  00:00:00  0.92477  0.92606  0.92210  0.92501  769  0  0
```

- Has SPREAD column → use for spread cost
- 15.2 MB file → ~250K bars expected

---

## Cost Model (Same as Task A)

- **Spread:** From CSV SPREAD column (real values)
- **Commission:** $7/lot (0.07 per 0.01 lot)
- **Risk per position:** 0.05 (5%) of $10,000 = $500 per trade
- **Position sizing:** `lot_size = $500 / (stop_distance_pips × pip_value)`

**USD/CHF specific pip values:**
- Pip size: 0.0001 (4 decimal places)
- Pip value per standard lot: ~$10.77 (varies with USD/CHF rate, approximate)
- For simplicity: use $10 per pip per standard lot (same as EUR/USD approximation)

---

## Implementation Steps

1. **Load USD/CHF data** from the CSV file
2. **Adapt the 4 strategies** to run on USD/CHF data:
   - Same logic, same parameters
   - Different pip value if needed (USD/CHF ≈ $10/pip for standard lot)
   - Use USD/CHF spread from CSV
3. **Apply cost model:**
   - Spread cost from CSV SPREAD column
   - Commission $7/lot
   - Position sizing: 5% risk per trade
4. **Run backtests** for all 4 strategies
5. **Compare results** to EUR/USD performance

---

## Key Analysis Points

For each strategy, compare:
| Metric | EUR/USD | USD/CHF | Transfer? |
|--------|---------|---------|-----------|
| Win Rate | | | |
| Profit Factor | | | |
| Total PnL | | | |
| Max Drawdown | | | |
| Expectancy | | | |
| Total Trades | | | |

**Key questions:**
1. Does Deep_Mean_Reversion maintain >80% WR on USD/CHF?
2. Do the profitable strategies on EUR/USD remain profitable on USD/CHF?
3. How does the trade frequency compare?
4. Is the edge pair-specific or universal?

---

## Output Requirements

Save results to: `quant-lab/results/usdchf_backtest_20260518.json`

Format:
```json
{
  "pair": "USD/CHF",
  "timeframe": "M5",
  "data_file": "USDCHF!_M5_202301020000_202605061250.csv",
  "data_bars": N,
  "date_range": "...",
  "cost_model": {
    "commission_per_lot": 7,
    "spread_source": "CSV column",
    "risk_per_position": 0.05,
    "account_equity": 10000
  },
  "strategies": {
    "Deep_Mean_Reversion": { ... },
    "Constraint_Anchor": { ... },
    "P90P_Distribution": { ... },
    "Stall_Harvest_CFD": { ... }
  },
  "comparison_to_eurusd": { ... }
}
```

Also create a summary report: `quant-lab/reports/USDCHF_BACKTEST_20260518.md`

---

## Reference: EUR/USD Results (V4, no costs)

| Strategy | EUR/USD WR% | EUR/USD PF | EUR/USD PnL(p) |
|----------|-------------|------------|-----------------|
| Deep_Mean_Reversion | 91.8% | 111.96 | +8746 |
| Constraint_Anchor | 51.1% | 1.85 | +1295 |
| P90P_Distribution | 26.3% | 1.42 | +288 |
| Stall_Harvest_CFD | 30.7% | 1.48 | +144 |

**Note:** These EUR/USD results have NO transaction costs. The USD/CHF results WILL have costs. Expect lower numbers.

---

## Critical Rules

1. **Use proper cost model** — spread from CSV + $7/lot + 5% risk
2. **Same strategy logic** — don't change parameters, only the data
3. **Report honestly** — if USD/CHF results are worse, say so
4. **Don't dismiss** — test, don't assume (MAD Directive 2)

---

## Success Criteria

- [ ] All 4 strategies backtested on USD/CHF M5
- [ ] Proper cost model applied (spread + commission + position sizing)
- [ ] Results saved to `quant-lab/results/usdchf_backtest_20260518.json`
- [ ] Summary report in `quant-lab/reports/USDCHF_BACKTEST_20260518.md`
- [ ] EUR/USD vs USD/CHF comparison included
- [ ] Key analysis questions answered

---

*Manager v5 — 2026-05-18 00:30 EDT*
