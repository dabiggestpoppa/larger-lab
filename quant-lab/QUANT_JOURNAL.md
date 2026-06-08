# 📓 QUANT JOURNAL — Active Tasks & Results

> **Purpose:** Store active task results, test outcomes, and operational notes.
> **Separate from:** Team chat (communication), Bible (reference), Progress files (agent tracking)
> **Updated:** June 8, 2026

---

## 🎯 ACTIVE MISSION: $65 → $20,000 in 90-120 Days

### Status: ✅ ANALYSIS COMPLETE — AWAITING FORWARD TEST

### Key Findings

**Best Quad Basket (Max Profits, Cost-Adjusted):**
| Rank | Basket | PnL | Trades | WR% | Avg PF | Avg Cost |
|------|--------|-----|--------|-----|--------|----------|
| 1 | AUDNZD + EURGBP + EURCHF + AUDUSD | 111,374p | 24,674 | 83.8% | 11.57 | 0.35p |
| 2 | USDJPY + GBPUSD + EURJPY + USDCAD | 219,830p | 26,848 | 82.6% | 9.27 | 0.35p |
| 3 | EURGBP + EURCHF + AUDUSD + USDCAD | 155,104p | 31,623 | 83.8% | 11.32 | 0.30p |

**Best 6-Asset Basket (Cost-Adjusted Viable):**
- AUDNZD + EURGBP + EURCHF + AUDUSD + USDCAD + EURUSD
- 194,738p PnL, 38,750 trades, 83.6% WR, avg PF 11.15

**Position Sizing Path:**
| Phase | Days | Balance | Lot Size | Risk/Trade |
|-------|------|---------|----------|------------|
| 1 | 1-30 | $65 → $200 | 0.01 | 2% |
| 2 | 31-60 | $200 → $1,000 | 0.02 | 2% |
| 3 | 61-90 | $1,000 → $5,000 | 0.05 | 2% |
| 4 | 91-120 | $5,000 → $20,000+ | 0.05-0.10 | 2-3% |

**Monte Carlo Results (500 simulations each):**
- Top 8 pairs, 120 days, 1% risk: P50 = $21,682 | Hit rate = 99.6% | Max DD = 0.0%
- All 36 pairs, 120 days, 1% risk: P50 = $57,635 | Hit rate = 100% | Max DD = 0.0%
- Viable only (15 pairs), 120 days, 1% risk: P50 = $22,817 | Hit rate = 100%

---

## 📊 TEST RESULTS LOG

### Test: 9K Unlock Config (June 8, 2026)
- **Config:** ar_max=999, per-asset trigger coefficient, 4PM cutoff, flat DZ 20-50%
- **Pairs tested:** 36 (all assets)
- **Total trades:** 212,978
- **Results file:** `reports/run_9k_config_results.json`
- **PDF report:** `reports/CEREBUS_9K_CONFIG_REPORT.pdf`

### Test: Cost-Adjusted Backtest (June 7, 2026)
- **Commission:** $0.07/trade at 0.01 lot (flat, all assets)
- **Spread:** MT5 live values
- **No commission on indices**
- **Viable pairs:** 15 of 36
- **Results file:** `reports/cost_final_v2.json`

### Test: Frequency Normalization Sweep (June 4, 2026)
- **Method:** Per-asset trigger coefficients (0.55x-0.83x)
- **Results:** EURGBP 0.65x, EURJPY 0.55x, etc.
- **Key finding:** High-trigger crosses (EURJPY, EURAUD, EURNZD) can't reach 2.5 tr/day without breaching guardrails

### Test: Max Accuracy Sweep (June 4, 2026)
- **22 FX pairs** tested floor/ceiling
- **Results file:** `reports/trigger_sweep_max_accuracy.json`
- **Key finding:** Floor configs produce ~158K trades at 81.1% WR avg

---

## 🔧 FORWARD TEST PLAN

### Setup
- Download MT5 demo broker (same engine, separate account)
- Copy engine files to demo setup
- Use same configs as live (Low Cost Hex or Best Quad)
- Run for 7-14 days to validate live performance

### Config to Test
**Primary:** Best Quad (Cost-Adjusted)
- Pairs: AUDNZD, EURGBP, EURCHF, AUDUSD
- Triggers: Per-asset coefficients from 9K config
- Position sizing: 0.01 lot start, scale at $200/$1K/$5K

**Secondary:** Low Cost Hex (6 pairs)
- Pairs: EURJPY, EURNZD, GBPNZD, EURAUD, GBPAUD, EURCHF
- Lower frequency, higher PF after costs

### Metrics to Track
- Daily PnL
- Win rate vs backtest
- Max consecutive losses
- Slippage vs theoretical
- Execution quality (fills, rejections)

---

## 📋 PENDING TASKS

- [ ] Set up MT5 demo broker for forward test
- [ ] Copy engine + configs to demo
- [ ] Run 7-day forward test
- [ ] Compare forward test results vs backtest
- [ ] Generate Monte Carlo PDF with position sizing schedule
- [ ] Update Bible with forward test results

---

## 🔑 KEY CONFIGS

### 9K Unlock Config (Per-Asset Triggers)
```
ar_max = 999 (no AR gate)
trigger = native_trigger × coefficient
session_cutoff = 4PM EST
DZ = flat 20-50% all loops
```

### Trigger Coefficients (Top Pairs)
| Pair | Native T1 | Coefficient | 9K T1 |
|------|-----------|-------------|-------|
| EURUSD | 12p | 0.83x | 10.0p |
| GBPUSD | 16p | 0.75x | 12.0p |
| EURJPY | 35p | 0.55x | 19.2p |
| EURGBP | 8p | 0.65x | 5.2p |
| EURCHF | 11p | 0.65x | 7.2p |
| AUDUSD | 13p | 0.75x | 9.8p |
| AUDNZD | 14p | 0.65x | 9.1p |
| EURNZD | 34p | 0.55x | 18.7p |

---

## 📁 RELATED FILES

- `QUANT_BIBLE.md` — Complete system reference
- `reports/run_9k_config_results.json` — 9K config raw data
- `reports/cost_final_v2.json` — Cost-adjusted results
- `reports/CEREBUS_9K_CONFIG_REPORT.pdf` — 9K config PDF
- `reports/CEREBUS_FULL_REPORT.pdf` — Original sweep PDF
- `scripts/run_9k_config.py` — 9K config test script
- `scripts/monte_carlo_65_to_20k.py` — Monte Carlo simulation
