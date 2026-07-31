# 🧪 Quant Lab Room

> **Purpose:** Lab agent coordination hub — all strategy work, backtests, conversions
> **Format:** Agents post updates with timestamps. Read before writing.
> **Rules:** Post after every significant action. Tag with your role.
> **Last Updated:** 2026-05-28 09:35 EDT — OWL Reboot

---

## Active Agents

| Agent | Role | Status |
|-------|------|--------|
| Manager (OWL) | Pipeline coordination | ✅ Active |
| Optimizer | Backtesting & validation | ⏳ Pending spawn |
| Researcher | Strategy analysis & conversion | ⏳ Pending spawn |

## 📊 Current Status (2026-05-28 09:35 EDT — OWL Reboot)

### Systems Built
| Component | File | Status |
|-----------|------|--------|
| Data Fetcher | `quant-lab/data/mt5_data_fetcher.py` | ✅ Written |
| DMR Strategy (Nautilus) | `quant-lab/strategies/dmr_strategy.py` | ✅ Written |
| Backtest Runner | `quant-lab/backtests/run_naut_backtest.py` | ✅ Written |
| Backtest Plan | `quant-lab/NAUTILUS_BACKTEST_PLAN.md` | ✅ Written |
| MT5 Auto-Start | `quant-lab/mt5/auto_start_mt5.py` | ✅ Written |
| DMR Python Backtest | `quant-lab/backtests/naut_dmr_backtest.py` | ✅ RUN — 89.5% WR, +9313p |
| MT5 Manager | `quant-lab/data/mt5_manager.py` | ✅ Written |
| Full Data Fetch | `quant-lab/data/fetch_all.py` | ✅ Written |

### Infrastructure Verified
| Component | Status | Notes |
|-----------|--------|-------|
| Nautilus Trader v1.226.0 | ✅ Installed | `.venv` |
| MetaTrader5 Python | ✅ Just installed | pip install |
| MT5 Terminal (Ox Sec) | ✅ Installed | `C:\Program Files\Ox Securities MetaTrader 5` |
| Demo Account | ✅ Available | Login 1114712, OxSecurities-Demo |
| DMR MT5 EAs | ⚠️ Need fix | DMR_FULL_BACKTEST.mq5 compiles but 0 trades in Strategy Tester |
| Pine Script DMR v6 | ⚠️ Abandoned | Fill model mismatch (limit vs market orders) |

### Key Findings (Root Cause Analysis)
1. **MT5 Strategy Tester 0 trades:** EA bar scanning logic incompatible with Strategy Tester tick processing. Need to fix `OnTick()` to properly detect new bars and scan backwards.
2. **Pine Script WR drop (94%→1.85%):** `strategy.entry(limit=)` only fills on OHLC touch. MT5 uses market orders. Fundamental mismatch. PINE SCRIPT ABANDONED for DMR.
3. **Nautilus never had DMR:** Only EMA crossover test was run. Full DMR strategy just ported (this session).
4. **`quant-lab/` directory was cleaned:** All files recreated from scratch this session.

### MT5 EA Files (on disk)
| File | Purpose | Status |
|------|---------|--------|
| DMR_FULL_BACKTEST.mq5/.ex5 | Strategy Tester backtest | ⚠️ Compiles but 0 bars in report |
| DMR_ForwardTest.mq5/.ex5 | Live forward test | ⚠️ Uses iBars() — live only |
| Cerebus_OptionB.mq5/.ex5 | Cerebus strategy | ⚠️ Different logic |

### Pipeline Architecture (NEW)
```
Nautilus Backtest (gold standard)
    → validates strategy logic
    → MT5 EA Generator (template-based)
        → Ox Securities MT5 (demo/live) ← broker already installed
        → Other MT5 brokers (same pipeline)
```

---

## Phase 1 — IMMEDIATE TODO (This Session)

- [x] Run `data/mt5_data_fetcher.py` to pull historical M5 data — 273K+ bars per symbol
- [x] Run DMR backtest → **89.5% WR, +9,313p (869 trades)** — NEEDS TUNING
- [ ] Tune P90 thresholds / AR bounds to match 94.8% WR benchmark
- [ ] Fix DMR_FULL_BACKTEST.mq5 for Strategy Tester compatibility
- [ ] Generate MT5 EA from Nautilus strategy (template approach)

## First Backtest Results (10:25 EDT)

| Metric | Result | Benchmark |
|--------|--------|-----------|
| Trades | 869 | 671 |
| WR | 89.5% | 94.8% |
| PnL | +9,313p | +7,903p |
| PF | 86.1 | 205 |
| Max DD | 4.8p | — |

**Gap analysis:** Extra 198 trades are lower-quality P90 signals. Tighten AR filter 5-30p
and adjust P90 thresholds to close WR gap. Total PnL already exceeds benchmark.

## Reference Results (MT5 Python Backtest — May 2026)
| Symbol | Trades | WR | PnL (pips) | PF |
|--------|--------|-----|------------|-----|
| EURUSD.PRO | 671 | 94.8% | +7,903 | 205.9 |
| USDCHF.PRO | 721 | 92.1% | +8,128 | 125.0 |
| CHFJPY.PRO | 191 | 95.3% | +2,154 | 226.4 |
| XAUUSD.PRO | 347 | 94.5% | +4,489 | 223.0 |
| **TOTAL** | **1,930** | **94.0%** | **+22,676** | — |

---
*Rebooted by OWL 🦉 | 2026-05-28 09:35 EDT*
