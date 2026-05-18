# [Manager → Optimizer] Task A: Pairs Trading Rebuild

> **From:** Manager v5 | **To:** Optimizer | **Priority:** 1 (MAD Directive)
> **Created:** 2026-05-18 00:30 EDT
> **Deadline:** Before USD/CHF backtest

---

## Objective

Rebuild the Pairs Trading EUR/USD-GBP/USD backtest with a **proper cost model** and **real position sizing**. The current implementation reports +$206K PnL using arbitrary scaling — this must be replaced with economically meaningful calculations.

---

## Current Issues (From Validation Report)

1. **No commission or spread costs** — Zero transaction costs applied
2. **Arbitrary P&L scaling** — `$50/z-unit` is not derived from position sizing or pip value
3. **No position sizing** — Risk per trade is not calculated from account equity

---

## Required Fixes

### 1. Use Real Spread from CSV Files

The CSV files have a `SPREAD` column (in points, where 1 point = 0.00001 for most pairs).

**CSV Format (confirmed):**
```
<DATE>  <TIME>  <OPEN>  <HIGH>  <LOW>  <CLOSE>  <TICKVOL>  <VOL>  <SPREAD>
2023.01.02  00:00:00  0.92477  0.92606  0.92210  0.92501  769  0  0
```

- The SPREAD column is the **spread in points** at the open of each bar
- For entry/exit cost: use the spread value from the entry/exit bar
- Spread cost per leg = `spread_points × point_value × lot_size`
- Example: spread = 10 points, point value = $0.00001 × 100,000 = $1/pip, lot = 0.1 → cost = 1.0 × $1 × 0.1 = $0.10 per pip of spread

### 2. Apply Commission: $7/lot per leg

- **$7 per standard lot** = $0.07 per 0.01 lot (micro lot)
- For pairs trading: **2 legs** (EUR/USD + GBP/USD) → commission × 2
- Commission per trade = `$7 × lot_size_in_standard_lots × 2_legs`
- Example: 0.1 lot → $7 × 0.1 × 2 = $1.40 round-trip commission

### 3. Position Sizing: Risk 5% per position

- **Risk per position: 0.05 (5%)** of account equity
- Account equity: **$10,000** (standard reference)
- Risk amount: $10,000 × 0.05 = **$500 per trade**
- Position size = `$500 / (stop_distance_in_pips × pip_value)`
- For EUR/USD: 1 pip = $1 per 0.01 lot (approximately, for standard pip calculation)
- For GBP/USD: 1 pip = $1 per 0.01 lot (approximately)

**Position sizing formula:**
```
stop_distance_pips = |entry_price - stop_loss_price| / pip_size
lot_size = $500 / (stop_distance_pips × pip_value_per_lot)
```

Where:
- pip_size = 0.0001 for EUR/USD and GBP/USD (4 decimal places)
- pip_value_per_standard_lot = $10 per pip (for standard 100,000 unit lot)
- pip_value_per_micro_lot = $0.01 per pip

### 4. P&L Calculation (Replace $50/z-unit)

**New P&L formula:**
```
# For each leg:
pnl_leg = direction × lot_size × (exit_price - entry_price) × contract_size
# Where:
# direction: +1 for LONG, -1 for SHORT
# lot_size: in standard lots (e.g., 0.1 = 10,000 units)
# contract_size: 100,000 for standard lot
# Result in USD

# Total P&L:
total_pnl = pnl_eurusd + pnl_gbpusd - spread_cost - commission
```

**Spread cost per leg:**
```
spread_cost = spread_in_pips × pip_value × lot_size_in_standard_lots
```

### 5. Data Files

| File | Path | Format |
|------|------|--------|
| EUR/USD M5 | `C:\Users\wifik\Downloads\EURUSD!_M5_202301020000_202605061250.csv` | OHLCV + SPREAD |
| GBP/USD M5 | `C:\Users\wifik\Downloads\GBPUSD!_M5_202301020000_202605061250.csv` | OHLCV + SPREAD |

**Both files confirmed to have SPREAD column.**

---

## Implementation Steps

1. **Read the existing strategy:** `projects/trading/nautilus/strategies/pairs_trading_eurusd_gbpusd.py`
2. **Modify the P&L calculation** to use real position sizing and pip values
3. **Add spread cost** using the SPREAD column from CSV files
4. **Add commission** at $7/lot per leg
5. **Add position sizing** at 5% risk per trade
6. **Re-run the backtest** with corrected parameters
7. **Report REAL numbers** — do NOT dismiss results as unrealistic (MAD Directive 2)

---

## Output Requirements

Save results to: `quant-lab/results/pairs_trading_v2_results.json`

Include in results:
```json
{
  "strategy": "Pairs Trading EUR/USD-GBP/USD v2",
  "total_trades": N,
  "win_rate": N,
  "total_pnl": N,
  "total_commission": N,
  "total_spread_cost": N,
  "gross_pnl": N,
  "net_pnl": N,
  "max_drawdown": N,
  "profit_factor": N,
  "expectancy": N,
  "by_exit": {"sl": N, "tp": N, "time_stop": N, "correlation_breakdown": N},
  "avg_lot_size": N,
  "avg_risk_per_trade": N,
  "cost_model": {
    "commission_per_lot": 7,
    "spread_source": "CSV column",
    "risk_per_position": 0.05
  }
}
```

Also update: `quant-lab/reports/PAIRS_TRADING_VALIDATION.md` with corrected results.

---

## Critical Rules (MAD Directives)

1. **Do NOT dismiss results as unrealistic** — test them (MAD Directive 2)
2. **Use real spread from CSV files** — not hardcoded values (MAD Directive 1)
3. **Risk 5% per position** — not $50/unit (MAD Directive 1)
4. **Commission $7/lot per leg** — ×2 for pairs (MAD Directive 1)
5. **Report what you find** — even if PnL drops significantly

---

## Success Criteria

- [ ] P&L calculated from real position sizing (not arbitrary scaling)
- [ ] Spread cost from CSV SPREAD column
- [ ] Commission $7/lot per leg applied
- [ ] Position size = 5% risk per trade
- [ ] Results saved to `quant-lab/results/pairs_trading_v2_results.json`
- [ ] Validation report updated with corrected results
- [ ] No dismissal of results without testing

---

*Manager v5 — 2026-05-18 00:30 EDT*
