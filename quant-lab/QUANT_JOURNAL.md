# 📓 QUANT JOURNAL — Active Tasks & Results

> **Purpose:** Store active task results, test outcomes, and operational notes.
> **Separate from:** Team chat (communication), Bible (reference), Progress files (agent tracking)
> **Updated:** August 9, 2026

---

## � EURCHF TRIANGULAR BASIS v1 — BACKTESTED: NOT READY (2026-08-09)
**Status:** ❌ FAILED FAIL-FAST CHECK — daily frequency has no gross edge

### Strategy Tested
Market-neutral mean reversion on the EURUSD / USDCHF / EURCHF triangle:
- Basis `B = ln(EURCHF) - ln(EURUSD) - ln(USDCHF)` (log no-arbitrage)
- Robust median/MAD z-score (window 90, ×1.4826), gated by rolling half-life<25 and EURUSD↔USDCHF inverse corr<-0.50
- Pos +1 = long basis (Long EURCHF / Short EURUSD / Short USDCHF); -1 = short basis
- Entry z=±2.0, exit z=∓0.3, stop z=∓3.5, max hold 20 bars
- Costs 6 bps per position change (12 bps round trip) — spec §6

### Result (MT5 PRO D1, 2015-10-11 → 2026-06-11, 2,912 bars)
| Metric | Value | Verdict |
|--------|-------|---------|
| Cum gross (10.7y) | +0.0080 | ≈ +0.24 bps/trade — NO edge |
| Cum net @ 6bps | **-0.383** | all years 2016-2026 negative |
| Ann Sharpe (net) | -6.08 | — |
| Max DD (net) | -0.383 | monotone decline |
| Gross win fraction (per held bar) | 52.4% | ~coin flip |
| Avg \|Δbasis\| on held bars | 2.7 bps | too small vs 6-12bps cost |
| Avg hold | 2.56 bars | short, but not profitable |
| Cost drag | 0.391 | = ~49× total gross |

### Data Quality (GOOD)
- Identity residual `mean|EURCHF/(EURUSD·USDCHF)-1| ≈ 0.017%` → triangle internally consistent
- Basis std ≈ 3 bps → no-arbitrage identity is tight, departures are tiny
- Spec oracle `pos.shift(1)·Δbasis` reproduces engine gross exactly (+0.0080) ✅

### Robustness Sweep (spec §10): uniformly negative
- z_window{60,90,120}, entry_z{1.8..2.5}, exit_z{0,0.3,0.5}, stop_z{3,3.5,4},
  max_hold{10..30}, max_half_life{15..30}, min_corr{-0.4,-0.6} → ALL negative
- Only cost changes magnitude monotonically (-0.19→-0.64) → result is COST-DRIVEN,
  not a parameter artifact. NOT overfit (opposite — no profitable neighborhood).

### Why it fails (spec §9 fail-fast)
Mean reversion is real but too weak at **daily** frequency: avg basis move per held
bar ~2.7bps vs 6-12bps cost to act. Gross is essentially zero before costs.

### Decision
- ❌ **Do NOT forward-test the daily v1.**
- ➡️ Follow-ons (research-only): **4H / M5** (higher freq = stronger MR) — engine,
  tests + sweep harness left in place for a fast rerun; compare with the existing
  GBPAUD/GBPNZD/AUDNZD triangular live engine which already trades a basis MR.
- Revisit only when gross >> 12bps round-trip per trade.

### Files
- Engine: `quant-lab/engines/eurchf_triangular_basis.py` (canonical, runnable)
- Tests: `quant-lab/tests/test_eurchf_triangular_basis.py` (8/8 passing)
- Report: `quant-lab/reports/triangular_basis_eurchf_report.md`

---

## �🚀 SYMMETRY TRAP LIVE ENGINE — PARITY LOCKED + READY FOR MONDAY (2026-08-09)
**Status:** ✅ PARITY PROVEN + LIVE ENGINE RUNNING

### ✅ 1:1 PARITY WITH CANONICAL BACKTEST
**Test:** EURUSDPRO_M5_2023_2026.csv (216,820 bars, 3 years)
| Metric | Backtest | Live | Diff |
|--------|----------|------|------|
| Trades | 3,120 | 3,120 | **0** |
| Win Rate | 79.13% | 79.13% | **0** |
| PnL | 15,101.36p | 15,101.36p | **0.00p** |
| Divergences | 0 | 0 | **0** |

**Parity Proof:** `artifacts/symmetry_trap/PARITY_REPORT.md`

### 🔧 CRITICAL FIX: BROKER TIMEZONE (2026-08-09)
- **Broker:** OxSecurities-Demo = **UTC-1** (NOT UTC+3 as assumed)
- **Measured:** tick time 12:52 UTC vs actual 13:52 → exactly -1h
- **Fixed:** `_broker_time_to_utc()` subtracts BROKER_UTC_OFFSET=-1 (broker+1h=UTC)
- **BTCUSD as primary time source** (24/7 = always fresh bars, even weekends)
- **Verified:** EST hour 8 == actual EST 8 ✅

### 🟢 LIVE ENGINE STATUS
- **Running** in loop mode (30s interval)
- **BTCUSD signal generated TODAY (24/7):** LONG @ 65106.4, SL 65141.3, TP 65226.4
  - Proves full pipeline: live data → Asian Range → state machine → signal ✅
- Orders fail on weekend (markets closed) but will place Monday 2AM EST

### 🏗️ ARCHITECTURE (FROZEN)
```
MT5 DATA (BTCUSD 24/7 = time source)
  ↓ mt5_data_feed.py (UTC normalization)
  ↓ symmetry_trap_live.py (thin wrapper)
  ↓ SymmetryTrapBacktest logic (UNCHANGED source of truth)
  ↓ execution_layer.py (pure MT5 execution)
  ↓ symmetry_trap_executor_multi.py (orchestration)
```

### 📁 Artifacts: `artifacts/symmetry_trap/`
- PARITY_REPORT.md, parity_baseline.json, canonical_call_graph.md
- parity_summary.json, config_parity.json, backtest_trace.csv, live_trace.csv, parity_diff.csv (empty=0)

### 📊 FORWARD TEST (STARTING MONDAY 2026-08-10)
- 8 assets: ETHUSD, HK50, NZDUSD, BTCUSD, US500, EURUSD, USDCHF, AUDUSD
- Lot 0.03, Magic 20260531, Entry 2-11AM EST, Hard exit 5PM
- Track: daily PnL, WR vs backtest, max consec losses, slippage, fills

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

## � June 8 Evening — MAD Closing

### Server Status
- **OCE Frontend (3000):** ✅ Up
- **OCE Backend (8000):** ✅ Up
- **API Server (8001):** ✅ Up
- **VTuber/POALA (12393):** 🔴 Taken offline per MAD directive
- **Stale processes:** 9 Python + 1 Node killed

### Notes
- VTuber/desktop pet process killed (was PID 21704, already gone from earlier cleanup)
- All 3 critical servers remain untouched and running
- POALA taken offline — not needed until tomorrow

---

## �📋 PENDING TASKS

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
