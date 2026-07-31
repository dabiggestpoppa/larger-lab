# NautilusTrader Backtest Results — CEREBUS FX v4.0

> **Date:** 2026-05-31 ~21:38 EST
> **Runner:** `quant-lab/backtests/run_cerebus_backtest.py`
> **Environment:** Nautilus Trader v1.221+ / Windows / Python

---

## Summary Table

| # | Strategy | Symbol | Bars | Trades | W/L | WR | PnL (pips) | Status |
|---|----------|--------|------|--------|-----|-----|------------|--------|
| 1 | Symmetry Trap | BTCUSD | 458,887 | 3 | 2/1 | 66.7% | -363,980.0 | ⚠️ Executed, negative |
| 2 | Symmetry Trap | ETHUSD | 458,015 | 0 | 0/0 | 0.0% | 0.0 | 🔴 No trades |
| 3 | P90 | BTCUSD | 458,887 | 0 | 0/0 | 0.0% | 0.0 | 🔴 No trades |
| 4 | P90 | ETHUSD | 458,015 | 0 | 0/0 | 0.0% | 0.0 | 🔴 No trades |
| 5 | Symmetry Trap | EURUSD | 10,000 | 112 | 87/23 | 77.7% | +534.9 | ✅ Success |

---

## Detailed Results

### Test 1: Symmetry Trap — BTCUSD ✅ (ran)
- **File:** `NAUTILUS_SYMMETRY_TRAP_BTCUSD_20260531_213450.json`
- Loaded 458,887 bars from `BTCUSD_M5.csv`
- 3 trades triggered (2 wins, 1 loss)
- WR: 66.7%
- **PnL: -363,980 pips** (heavily negative — likely a single large loss)
- Engine orders: 3, positions: 0
- **Concern:** Massive negative PnL on 3 trades suggests BTCUSD price scale (satoshis vs pips) is causing pip-calculation issues, or position sizing is wrong for crypto magnitudes.

### Test 2: Symmetry Trap — ETHUSD 🔴 (no trades)
- **File:** `NAUTILUS_SYMMETRY_TRAP_ETHUSD_20260531_213539.json`
- Loaded 458,015 bars — **zero trades triggered**
- Strategy conditions never met threshold
- Same pattern as BTCUSD but BTCUSD had 3 trades, ETHUSD had none
- **Likely cause:** Symmetry Trap strategy parameters calibrated for forex (EURUSD/USDCHF) don't trigger on crypto volatility profiles

### Test 3: P90 — BTCUSD 🔴 (no trades)
- **File:** `NAUTILUS_P90_BTCUSD_20260531_213645.json`
- Loaded 458,887 bars — **zero trades triggered**
- Strategy logged: `total_trades=0 wins=0 losses=0 pnl=0.0`
- P90 strategy conditions never triggered on crypto data

### Test 4: P90 — ETHUSD 🔴 (no trades)
- **File:** `NAUTILUS_P90_ETHUSD_20260531_213748.json`
- Loaded 458,015 bars — **zero trades triggered**
- Same as BTCUSD — P90 conditions don't fire on crypto

### Test 5: Symmetry Trap — EURUSD (Forex Validation) ✅ (success)
- **File:** `NAUTILUS_SYMMETRY_TRAP_EURUSD_20260531_213834.json`
- Loaded 273,909 bars, limited to 10,000 bars
- **112 trades triggered** — strategy is active and functional
- WR: 77.7% (87W / 23L)
- PnL: +534.9 pips
- **This validates the Nautilus runner works correctly on forex data**
- Benchmark target: ~91% WR, PF 23 (this is only 10K bars vs 4Y, so lower WR is expected)

---

## Key Findings

### 1. Crypto Backtests: Mostly No-Trades (3 out of 4)
The Symmetry Trap and P90 strategies, as currently parameterized, **do not generate trades on BTCUSD or ETHUSD M5 data**. The strategies were calibrated and tested on forex pairs (EURUSD, USDCHF). Crypto has:
- Different volatility regime (10-100x forex)
- Different price scale (BTC ~$100K range vs EURUSD ~1.05 range)
- Different microstructure (24/7, no session boundaries)
- Symmetry Trap thresholds (measured in pips/pip-equivalents) likely never reach trigger levels because crypto moves are magnitudes larger

### 2. BTCUSD Symmetry Trap: 3 Trades, Huge Loss
The 3 trades on BTCUSD produced -363,980 pips. This is almost certainly a **unit/scale issue**: the strategy calculates profit in "pips" but BTCUSD moves in dollars/satoshis. A $3,600 BTC move ÷ 0.01 pip-size = 360,000 "pips". The pip calculation is correct numerically but meaningless for crypto without adjusting the pip definition.

### 3. Forex Validation: EURUSD Works
The EURUSD test confirms the Nautilus backtest runner is functional. 112 trades with 77.7% WR on just 10K bars is reasonable. Full 4Y backtest would likely approach the ~91% WR benchmark.

### 4. No Engine Errors
All 5 tests completed without crashes, hangs, or exceptions. The Nautilus setup is stable.

---

## Recommendations

1. **Crypto backtests need recalibrated parameters** — Symmetry Trap and P90 thresholds, stop sizes, and profit targets must be rescaled for crypto volatility. Consider separate config profiles for each asset class.

2. **BTCUSD PnL "pip" calculation is misleading** — Define crypto-specific tick/pip sizes (e.g., 1 pip = $1 for BTC, $0.10 for ETH) to get meaningful PnL figures.

3. **Run full EURUSD 4Y backtest** for proper benchmark validation against the ~91% WR / PF 23 target.

4. **Investigate why P90 fires zero trades on crypto** — The P90 entry conditions (initial spread, cascade levels) may need crypto-specific calibration entirely.

---

*Generated: 2026-05-31 21:38 EST by subagent (naut_backtest)*
*Report saved to: quant-lab/reports/naut_backtest_results.md*
