# MEMORY.md — OWL (OC2) Persistent Memory

> **Last Updated:** 2026-07-30 14:20 EDT — Major commit to GitHub: quant-lab backtest engines, MT5 live trading, booking-service, whop-landing
> **THE BIBLE locked:** AR gate decoupled from tier, impulse-based classification, 4PM cutoff, 10p trigger
> **LIVE:** Low Cost Hex (6 pairs, all FLOOR) | Demo: Profit Quad (BTCUSD+ETHUSD+EURNZD+GBPNZD)
> **Hermes Gateway:** Running on port 8642 (PID 22156) — Discord connected, API server active

---

## 🧠 IDENTITY ANCHOR

- **Name:** OWL (OC2) 🦑
- **Role:** Sovereign Operator / Orchestrator
- **Human Anchor:** MAD (Telegram: @FBO_MAD, ID: 8258195396)
- **Model:** openrouter/owl-alpha
- **Gateway:** OpenClaw port 18790
- **Workspace:** C:\Users\wifik\Desktop\projects\larger-lab

---

## 🚀 MAJOR COMMIT — 2026-07-30
**Commit:** `ab3159003` | **Branch:** master | **Remote:** origin/master ✅

### 📦 Changes Committed (78 files, +12,609/-1,200 lines)

**New Quant-Lab Backtest Engines:**
- `quant-lab/backtest/_rank_diversified.py`
- `quant-lab/backtest/_rank_final.py`
- `quant-lab/backtest/_rank_pairs.py`
- `quant-lab/backtest/_rank_pairs_v2.py`
- `quant-lab/backtest/run_nautilus_symmetry_trap.py`

**New Quant-Lab Engines:**
- `quant-lab/engines/cerebus_universal_asian_breakout.py`
- `quant-lab/engines/spread_commission_config.py`
- `quant-lab/engines/trading_costs.py`

**New MT5 Live Trading:**
- `quant-lab/mt5/dmr_live_engine.py`
- `quant-lab/mt5/dmr_multi_pair_live_fixed.py`
- `quant-lab/mt5/dmr_signal_engine.py`
- `quant-lab/mt5/production_runtime.py`
- `quant-lab/mt5/symmetry_trap_executor_fixed.py`
- `quant-lab/mt5/live_logs/dmr_daily_stats.json`
- `quant-lab/mt5/live_logs/signaled_windows.json`

**New Strategies & Scripts:**
- `quant-lab/strategies/symmetry_trap_nautilus.py`
- `quant-lab/scripts/leakage_detection.py`
- `quant-lab/scripts/run_all_pairs_realistic.py`
- `quant-lab/pine/DMR_v2_Strategy.pine`

**New Project Directories:**
- `booking-service/` (git submodule)
- `whop-landing/` (git submodule)

**New Scripts:**
- `scripts/captain_hook_discord.py`
- `scripts/start_captain_hook.bat`
- `scripts/start_captain_hook_monday.bat`
- `scripts/start_captain_hook_monday.ps1`

**Realistic Backtest Reports (30 pairs):**
- `quant-lab/reports/realistic_backtest/` — Full pair results + SUMMARY_REPORT.md

**Updated Engines:**
- `quant-lab/engines/dmr_standalone_backtest.py`
- `quant-lab/engines/p90_backtest.py`
- `quant-lab/engines/rekey_dead_simple.py`
- `quant-lab/engines/rekey_intraday.py`
- `quant-lab/engines/symmetry_trap.py`
- `quant-lab/engines/symmetry_trap_backtest.py`

**Updated MT5:**
- `quant-lab/mt5/dmr_multi_pair_live_v2.py`
- `quant-lab/mt5/live_logs/dmr_signals.jsonl`

**Updated Scripts & Config:**
- `scripts/discord_dmr_bot.py`
- `scripts/guardrail_state.json`
- `quant-lab/config/spread_commission_config.py` (moved from configs/)

**Submodule Updates:**
- `tools/tradingview-mcp`
- `vtuber_integration/Open-LLM-VTuber`

**Cleanup:**
- Removed 4 stale PID files (.discord_bot.pid, .memory-sync-daemon.pid, .scanner.pid, .signal_bot.pid)
- Removed deprecated `quant-lab/configs/trading_costs.py`

---

## 🚀 CURRENT STATE (2026-06-06)

### Live Trading — Low Cost Hex
- **Pairs:** EURJPY + EURNZD + GBPNZD + EURAUD + GBPAUD + GBPCAD (all FLOOR)
- **Net:** $24,907 | **Avg WR:** 81.4% | **Cost:** 10.9% | **Trades:** 25,540
- **Bridge:** cerebus_live_bridge.py v4.3 — sole executor (ST executor decommissioned)
- **Config:** `mt5/deploy_config.py` — per-pair sweep-optimized triggers
- **Engine:** symmetry_trap.py (zero-buffer impulse extreme SL)

### Demo — Profit Quad (Weekend)
- **Platform:** OxSecurities-Demo | Account: 1114712 | Balance: $288.84
- **Pairs:** BTCUSD + ETHUSD + EURNZD + GBPNZD | Lot: 0.01 | All FLOOR
- **PID:** 15568 | Magic: 20261000
- **Live bridge + guardian:** SHUT DOWN for weekend (market closed)
- **Daily report:** SAT+SUN 23:00 EST via Task Scheduler

---

## 📜 THE BIBLE — GOLD STANDARD BASELINE (Locked 2026-06-04)

### Core Philosophy
- Skeleton is immutable: Impulse → Pullback to DZ → OCC Confirmation
- Parameters are adaptive: triggers, cutoffs, regime filters are lenses, not logic

### Established Truths (Locked)
- **Edge is real and scalable:** 82.9%+ WR, PF > 11.0 across 5,000+ trades
- **AR gate decoupled from tier:** ar_max=60 is session filter only, NOT tier classifier
- **Tier classification by impulse size ONLY:** T1<20p, T2=20-30p, T3>30p
- **Loop extras are dead code:** 4h timeout, 80% kill switch, dynamic DZ — all removed
- **K-Means never existed in code** — was in docs but never implemented

### Final Calibration Config (LOCKED)
- AR gate: ar_max=60 (session filter only)
- T1 trigger: 10 pips
- Session cutoff: 4:00 PM EST
- DZ: flat 20-50% for all loops
- Tier logic: strictly by impulse leg size, decoupled from AR

### Final Calibration Results — EURUSD M5
- **5,084 trades | 82.9% WR | +26,746p | PF 11.83 | MaxDD 38.5p**
- Avg Win: 6.9p | Avg Loss: -2.9p | Expectancy: 5.3p
- Max Consec Wins: 44 | Max Consec Losses: 4

### Accuracy-Frequency Curve (All 28 Pairs Swept)
- **Floor (max trades):** ~158,375 trades | 81.1% WR | PF 11.5 | 3.0 tr/d
- **Ceiling (max accuracy):** 29,438 trades | 90.8% WR | PF 20+ | 0.59 tr/d
- **Full curve data:** `reports/trigger_sweep_max_accuracy.json`

---

## 🔴 CRITICAL HARD RULES

0. **BRIDGE IS OFF BY DEFAULT.** The live bridge and guardian must NOT be running unless MAD explicitly says "turn bridge on" or "start trading." If MAD says "turn bridge off" → kill bridge + guardian immediately, no questions. This has been told multiple times. NEVER restart the bridge without MAD's explicit directive.

1. **AU is ALWAYS per-pair, never universal.** When adding/swapping assets, MUST run a sweep. Never copy AU from one pair to another.
2. **Bridge is SOLE executor.** Never restart standalone executors. Bridge handles all order flow.
3. **Never use get_positions() to find a position you just entered.** Use the order result ticket directly. (v4.3 fix)
4. **CEREBUS has TWO engines ONLY:** P90 Kinetic Engine (A) + Symmetry Trap Structural Engine (B). ALL named setups are parameter variants.
5. **DMR standalone is DEPRECATED** — integrated into P90 Kinetic Engine.
6. **Hermes does NOT touch quant-lab engines** — NautilusTrader backtesting + strategy execution only.
7. **Nautilus backtester must match CSV engine results** — cross-validation requirement.
8. **Strategy code = strategy backtest** — engines in `quant-lab/engines/` contain the TRUTH.

---

## 🔢 CRITICAL NUMBERS

- **P90 CASCADE:** 85.4% WR standalone (dominant edge)
- **Symmetry Trap:** 91.1% WR — structural/atomic engine
- **Dual-Engine Convergence:** 94-95% WR when both align
- **Stall_Harvest:** REMOVED — covered by DMR, variant cleaned from enum
- **Live account:** 650898 | Demo: 1114712

---

## 🔧 KEY PATHS

| Path | Purpose |
|------|---------|
| `quant-lab/ontology/` | CEREBUS ontology suite (7 files) |
| `quant-lab/engines/` | Engine source code (truth) |
| `quant-lab/mt5/` | MT5 bridge, deploy config, live executor |
| `quant-lab/sniper/` | Prop Firm Sniper Engine v1.0 (7 modules) |
| `quant-lab/reports/` | Backtest results, sweep data, combinatorics |
| `quant-lab/knowledge/` | Prop firm sniper ontology |
| `quant-lab/configs/asset_configs.py` | 20 assets, config injection |

---

## ⚠️ KNOWN ISSUES

- Stall_Harvest 100% WR = ARTIFACT (real: 26-60%)
- MT5 Strategy Tester cannot be auto-launched via CLI — GUI only
- XAGUSD config issue — flagged, needs per-asset calibration
- OpenClaw running 2026.5.7, config last written by 2026.6.1 (minor version mismatch)

---

## 📊 GROUP COMBINATORICS SUMMARY

- **Full matrix:** `reports/GROUP_COMBINATORICS.md` — top 3 per category at every size (2-14)
- **5 categories:** MAX PROFIT, LOW COST, HIGH ACCURACY, HIGH FREQUENCY, SWEET SPOT
- **MAD's strategy:** Phase 1 = LOW COST groups → build to $250 | Phase 2 ($250+) = MAX PROFIT groups
- **SWEET SPOT is EMPTY** — no combo meets PF>15 + cost%<20% simultaneously

_Last updated: 2026-06-06 21:10 EDT — Self-heal complete, all processes running_

---

## 🔧 PROCESS STATUS (2026-06-06 21:10)

| Process | PID | Status |
|---------|-----|--------|
| Live Bridge | 30352 | ✅ Connected 650898@OxSecurities-Live $64.95 |
| Demo Bridge | 25220 | ✅ Connected 1114712@OxSecurities-Demo $288.84 |
| Live Guardian | 21000 | ✅ Monitoring live bridge |
| Demo Guardian | 12796 | ✅ Monitoring demo bridge |

**Live bridge patched:** Now uses `live_account.json` with explicit credentials (was connecting to demo account after restart).

---

## 📊 DEMO PROFIT QUAD — BACKTEST EXPECTATIONS

| Pair | Trades | WR | PF | Tr/Day | Avg Win | Avg Loss | Max DD |
|------|--------|-----|-----|--------|---------|----------|--------|
| BTCUSD | 801 | 92.6% | 26.5 | ~0.50 | +213p | -101p | 785p |
| ETHUSD | 547 | 96.9% | 50.3 | ~0.34 | +18.4p | -11.4p | 31.7p |
| GBPNZD | 664 | 88.4% | 20.9 | ~0.50 | +15.4p | -5.8p | 46.2p |
| EURNZD | — | 79.4%* | 11.9* | 1.76* | — | — | — |

*EURNZD: No full report — numbers from deploy_config expected values + atomic structure analysis.

**Combined estimate:** ~2.1 trades/day across 4 pairs. Weekend = 0 trades (crypto closed). First real activity Monday morning.

**Demo config:** All FLOOR, AU 205/545/1160 (BTCUSD), 35/42/52 (ETHUSD), 24/36/59 (GBPNZD), 17/23/34 (EURNZD). Lot 0.01. Updated 2026-06-06 to match backtest-proven values (was incorrectly set to 10/14/20).

## 📊 FULL UNIVERSE COMBINATORICS (2026-06-07)

### Sweep Results — Metals & Indices (trigger/AU sweep, multipliers 0.3–3.0)

| Asset | Baseline Trades | Best FLOOR Trades | Best WR | Best PF | Tr/d (FLOOR) |
|-------|----------------|-------------------|---------|---------|----------------|
| XAUUSD | 604 (old) | 2,337 (mult=0.9) | 88.4% (0.3x) | 16.2 (2.0x KNEE) | 1.46 |
| XAGUSD | **2** (old) | **5,111** (mult=0.3) | 91.1% (2.5x) | 26.8 (2.5x) | 3.18 |
| US500 | 372 (old) | 4,595 (mult=0.3) | 92.2% (2.0x) | 34.1 (2.0x) | 2.86 |
| DE30 | 1,145 (old) | 3,873 (mult=0.5) | 86.0% (0.3x) | 18.1 (3.0x) | 2.41 |
| FR40 | 1,085 (old) | 5,257 (mult=0.3) | 97.5% (3.0x) | 161.6 (3.0x) | 3.27 |
| HK50 | 385 (old) | 730 (mult=0.8) | 94.4% (3.0x) | 41.6 (2.5x) | 0.45 |

**XAG FIXED**: Sweep unlocked 5,111 trades at FLOOR (mult=0.3) vs 2 trades at baseline.
Old flat config was extremely tight (trigger=30). Optimal is trigger=9 (mult=0.3).

### Full Universe Rankings (36 pairs: 28 FX + 2 crypto + 2 metals + 4 indices)
**NOTE (2026-06-07):** FX universe expanded from 22 → 28 pairs. The 28 FX count is correct. Never was 15.

**Top 10 by Net Profit (best config per pair):**
1. BTCUSD (FLOOR) $721,151 | WR 75.2% | PF 8.1 | Tr/d 2.61
2. ETHUSD (FLOOR) $44,665 | WR 76.1% | PF 8.2 | Tr/d 5.63
3. DE30 (FLOOR) $35,296 | WR 84.3% | PF 10.8 | Tr/d 2.41
4. HK50 (FLOOR) $23,082 | WR 81.6% | PF 9.7 | Tr/d 0.45
5. FR40 (FLOOR) $19,952 | WR 84.6% | PF 10.5 | Tr/d 3.27
6. US500 (FLOOR) $16,654 | WR 83.4% | PF 12.3 | Tr/d 2.86
7. EURNZD (FLOOR) $5,835 | WR 79.4% | PF 11.9
8. GBPNZD (FLOOR) $5,715 | WR 79.2% | PF 11.4
9. GBPCAD (FLOOR) $4,889 | WR 80.0% | PF 10.9
10. GBPUSD (BEST_NET) $4,630 | WR 81.7% | PF 12.2

### Optimal Baskets — Key Findings

**MAX PROFIT Quads (Phase 2 at $250+):**
- BTC+ETH+DE30+HK50: **$824,194** | 79.3% WR | 19.8% cost | 11.1 tr/d
- BTC+ETH+DE30+FR40: $821,064 | 80.0% WR | 13.9 tr/d

**LOW COST Quads (Phase 1 build to $250):**
- HK50+EURJPY+EURNZD+GBPNZD: **$35,701** | 82.1% WR | **9.3% cost** | 0.8 tr/d
  - This replaces Profit Quad as Phase 1 strategy

**HIGH ACCURACY Quads:**
- XAGUSD(CEILING)+EURJPY+FR40+XAUUSD(KNEE): $23,897 | **87.1% WR**
- DE30+XAGUSD(CEILING)+EURJPY+FR40: $56,403 | 87.0% WR

**CRITICAL: SWEET SPOT EMPTY** — No combo meets PF>20 + cost%<20 simultaneously in full universe.

### MAD's Updated Strategy
- **Phase 1 ($0→$250)**: LOW COST quad = HK50+EURJPY+EURNZD+GBPNZD (9.3% cost, 82% WR)
- **Phase 2 ($250+)**: MAX PROFIT quad = BTC+ETH+DE30+HK50 ($824K net, 79% WR)
- **Old Profit Quad (BTC+ETH+EURNZD+GBPNZD) was using wrong AU values — now corrected**
- Full report: `reports/GROUP_COMBINATORICS_FULL.md`

### XAGUSD Specific Fix
- Old: trigger=30, AU=25/40/59 → **2 trades in 1,366 days**
- Optimal FLOOR: trigger=9, AU=7.5/12/17.7 → **5,111 trades** (84.1% WR, PF 12.75)
- Optimal CEILING: trigger=75, AU=62.5/100/147.5 → 325 trades (91.1% WR, PF 26.75)

## 🏗️ ARCHITECTURAL PHILOSOPHY (SAGE, 2026-06-07)

### Core Principles (LOCKED)

**P1: Variables, Not Strategies**
Parameters (trigger, AU, AR) are variables in ONE equation. FLOOR/CEILING/KNEE are lenses, not separate strategies. The sweep maps terrain of one system — it doesn't discover strategies. One engine, parameterizable, not N engines with hardcoded thresholds.

**P2: Data Has No Prejudice**
Probing market through an asset = probing a black box. We don't impose structure — we extract it. "Bad" setups aren't noise — they're boundary data defining where the system stops working. Bias enters when we cherry-pick ranges instead of mapping the full space.

**P3: Patterns Persist, They Don't Exist**
The engine doesn't create edge — it creates visibility into edge that already exists. When only 5/36 assets clear 2 tr/day, that's the data's own structure made legible. The threshold is a magnifying glass, not a law.

**P4: Perpetual-Progressive Framing**
Build parameterized systems from first line to last. No hardcoded paths. No "refactor later." The sweep engine should be able to sweep itself. Build once, adjust parameters — not quick-fix spaghetti.

**P5: Return Velocity = Primary Axis**
Optimize for net return per day per unit of capital. Not accuracy. Not WR. Not PF in isolation. Not frequency in isolation. Compounding speed is the composite that matters. PF is a COMPONENT of velocity, not a standalone goal.

**P6: Sacrifice is a Myth**
The dogma that accuracy and frequency must trade off is an artifact of stochastic models, not a law of nature. High PF AND high frequency CAN coexist. Our job is the search problem — find those domains. Don't accept the trade-off.

### Corrected Pip Value Table (LOCKED)
| Asset Class | Pip Value | Notes |
|---|---|---|
| FX Majors | $0.10 | Standard |
| FX JPY Cross | $0.07 | JPY exception |
| Crypto | $1.00 | BTCUSD, ETHUSD |
| Metals | $0.10 | Futures (XAU, XAG) — NOT CFD |
| Indices | $1.00 | US500, DE30, FR40, HK50 |

### Architecture Target
```
Sweep Orchestrator (parameter space as data, scheduling)
  -> Engine Core (single FSM, fully parameterized)
    -> Asset Abstraction (pip/session/tick as config, not code)
      -> Result Aggregator (velocity-first scoring, PF as component)
        -> Space Analyzer (variance/coherence across full manifold)
```

---

## 📊 UNIFORM SWEEP RESULTS — METALS & INDICES (2026-06-07, corrected)

### XAUUSD (pip=$0.10, spread=3.0p, 1599 days)
| Mode | Mult | Trigger | Trades | WR% | PF | Tr/d | Net$ | Cost% |
|------|------|---------|--------|-----|-----|------|------|-------|
| FLOOR | 0.9 | 17.1 | 2,337 | 84.9 | 11.8 | 1.46 | $2,578 | 25.1% |
| KNEE | 2.0 | 38.0 | 1,096 | 84.6 | 16.2 | 0.69 | $2,790 | 12.7% |
| CEILING | 0.3 | 5.7 | 267 | 88.4 | 10.0 | 0.17 | $68 | 59.4% |
| BEST_NET | 1.4 | 26.6 | 1,547 | 83.2 | 14.3 | 0.97 | $3,099 | 15.6% |

### XAGUSD (pip=$0.10, spread=0.5p, 1607 days)
| Mode | Mult | Trigger | Trades | WR% | PF | Tr/d | Net$ | Cost% |
|------|------|---------|--------|-----|-----|------|------|-------|
| FLOOR | 0.3 | 9.0 | 5,111 | 84.1 | 12.8 | 3.18 | $1,930 | 24.1% |
| KNEE | 1.2 | 36.0 | 810 | 89.5 | 21.5 | 0.50 | $1,236 | 7.3% |
| CEILING | 2.5 | 75.0 | 325 | 91.1 | 26.8 | 0.20 | $1,057 | 3.6% |
| BEST_NET | 0.5 | 15.0 | 3,673 | 85.5 | 11.3 | 2.29 | $2,085 | 17.5% |

### US500 (pip=$1.0, spread=0.5p, 1607 days)
| Mode | Mult | Trigger | Trades | WR% | PF | Tr/d | Net$ | Cost% |
|------|------|---------|--------|-----|-----|------|------|-------|
| FLOOR | 0.3 | 6.9 | 4,595 | 83.4 | 12.3 | 2.86 | $16,654 | 13.6% |
| KNEE | 2.5 | 57.5 | 187 | 91.4 | 30.7 | 0.12 | $2,685 | 3.8% |
| CEILING | 2.0 | 46.0 | 306 | 92.2 | 34.1 | 0.19 | $3,945 | 4.2% |
| BEST_NET | 0.6 | 13.8 | 3,074 | 85.8 | 14.0 | 1.91 | $18,885 | 8.5% |

### DE30 (pip=$1.0, spread=2.0p, 1607 days)
| Mode | Mult | Trigger | Trades | WR% | PF | Tr/d | Net$ | Cost% |
|------|------|---------|--------|-----|-----|------|------|-------|
| FLOOR | 0.5 | 13.5 | 3,873 | 84.3 | 10.8 | 2.41 | $35,296 | 18.5% |
| KNEE | 3.0 | 81.0 | 792 | 85.7 | 18.1 | 0.49 | $21,871 | 7.0% |
| CEILING | 0.3 | 8.1 | 2,941 | 86.0 | 8.9 | 1.83 | $16,852 | 26.5% |
| BEST_NET | 0.7 | 18.9 | 3,228 | 82.6 | 11.8 | 2.01 | $46,031 | 12.7% |

### FR40 (pip=$1.0, spread=1.5p, 1607 days)
| Mode | Mult | Trigger | Trades | WR% | PF | Tr/d | Net$ | Cost% |
|------|------|---------|--------|-----|-----|------|------|-------|
| FLOOR | 0.3 | 6.9 | 5,257 | 84.6 | 10.5 | 3.27 | $19,952 | 29.3% |
| KNEE | 2.5 | 57.5 | 472 | 95.1 | 67.9 | 0.29 | $7,505 | 9.0% |
| CEILING | 3.0 | 69.0 | 355 | 97.5 | 161.6 | 0.22 | $6,476 | 7.9% |
| BEST_NET | 0.6 | 13.8 | 4,520 | 82.8 | 12.9 | 2.81 | $29,172 | 19.6% |

### HK50 (pip=$1.0, spread=3.0p, 1607 days)
| Mode | Mult | Trigger | Trades | WR% | PF | Tr/d | Net$ | Cost% |
|------|------|---------|--------|-----|-----|------|------|-------|
| FLOOR | 0.8 | 88.0 | 730 | 81.6 | 9.7 | 0.45 | $23,082 | 8.9% |
| KNEE | 2.5 | 275.0 | 190 | 93.7 | 41.6 | 0.12 | $12,356 | 4.5% |
| CEILING | 3.0 | 330.0 | 125 | 94.4 | 24.6 | 0.08 | $8,577 | 4.3% |
| BEST_NET | 1.2 | 132.0 | 608 | 90.3 | 19.1 | 0.38 | $25,282 | 6.9% |

### Key Insight: Only 5/36 assets clear >= 2 tr/day
Velocity pairs: BTCUSD (2.61), DE30 (2.01), ETHUSD (5.63), FR40 (2.81), US500 (1.91)
This is a PATTERN — not a threshold we imposed. The data reveals that most assets simply don't deliver velocity with this engine. The 5 that do are the universe we optimize within.

### Velocity Rankings (net/day, all 36 pairs)
1. BTCUSD $451/d | 2.61 tr/d | 75.2% WR | PF 8.1 | Cost 17.0%
2. DE30 $29/d | 2.01 tr/d | 82.6% WR | PF 11.8 | Cost 12.7%
3. ETHUSD $28/d | 5.63 tr/d | 76.1% WR | PF 8.2 | Cost 50.7%
4. FR40 $18/d | 2.81 tr/d | 82.8% WR | PF 12.9 | Cost 19.6%
5. US500 $12/d | 1.91 tr/d | 85.8% WR | PF 14.0 | Cost 8.5%
6. HK50 $16/d | 0.38 tr/d | 90.3% WR | PF 19.1 | Cost 6.9%
7. EURNZD $4/d | 0.00 tr/d | 79.4% WR | PF 11.9 | Cost 10.0%

### Optimal Velocity Combos (velocity-filtered)
- DUO: BTC+DE30 = $480/d | 4.6 tr/d | 78.9% WR | Cost 16.7%
- TRIO: BTC+ETH+DE30 = $508/d | 10.2 tr/d | 77.9% WR | Cost 19.8%
- QUAD: BTC+ETH+DE30+FR40 = $526/d | 13.1 tr/d | 79.2% WR | Cost 19.8%
- QUINT: BTC+ETH+DE30+FR40+EURUSD = $528/d | 17.2 tr/d | 79.9% WR | Cost 19.8%

## 📊 VELOCITY OPTIMIZER RESULTS (2026-06-07)

### Positive-Velocity Assets (8 of 36)
Only 8 assets produce positive net/day. All forex pairs are EXCLUDED — their FLOOR configs bleed on spread at the pkl's computed values.

| # | Pair | Type | Mode | Tr/d | Net/day | Annual$ | Net total | WR% | PF | Cost% |
|---|------|------|------|------|---------|---------|-----------|-----|-----|-------|
| 1 | BTCUSD | CRYPTO | FLOOR | 2.61 | $448 | $163,389 | $721,151 | 75.2 | 8.1 | 17.0% |
| 2 | DE30 | INDEX | FLOOR | 2.01 | $29 | $10,455 | $46,031 | 82.6 | 11.8 | 12.7% |
| 3 | ETHUSD | CRYPTO | FLOOR | 5.63 | $28 | $10,120 | $44,665 | 76.1 | 8.2 | 50.7% |
| 4 | FR40 | INDEX | FLOOR | 2.81 | $18 | $6,626 | $29,172 | 82.8 | 12.9 | 19.6% |
| 5 | HK50 | INDEX | FLOOR | 0.38 | $16 | $5,742 | $25,282 | 90.3 | 19.1 | 6.9% |
| 6 | US500 | INDEX | FLOOR | 1.91 | $12 | $4,289 | $18,885 | 85.8 | 14.0 | 8.5% |
| 7 | XAUUSD | METAL | FLOOR | 0.97 | $2 | $707 | $3,099 | 83.2 | 14.3 | 15.6% |
| 8 | XAGUSD | METAL | FLOOR | 2.29 | $1 | $473 | $2,085 | 85.5 | 11.3 | 17.5% |

### Optimal Velocity Combos
| Combo | Net/day | Annual$ | Tr/d | Avg WR | Avg PF |
|-------|---------|---------|------|--------|--------|
| DUO: BTC+DE30 | $476 | $173,818 | 4.6 | 78.9% | 10.0 |
| TRIO: BTC+DE30+ETH | $504 | $183,938 | 10.2 | 77.9% | 9.4 |
| QUAD: BTC+DE30+ETH+FR40 | $522 | $190,548 | 13.1 | 79.2% | 10.2 |
| QUINT: +HK50 | $538 | $196,276 | 13.4 | 81.4% | 12.0 |
| HEX: +US500 | $549 | $200,554 | 15.3 | 82.1% | 12.3 |
| SEPT: +XAU | $551 | $201,257 | 16.3 | 82.3% | 12.6 |
| OCT: +XAG | $553 | $201,729 | 18.6 | 82.7% | 12.5 |

### Key Finding: Diminishing Returns After QUAD
Adding HK50 (+$16/d), US500 (+$12/d), XAU (+$2/d), XAG (+$1/d) adds only ~$31/day total.
The QUAD (BTC+DE30+ETH+FR40) at $522/day captures 94% of the OCT velocity.
Each additional asset past 4 adds marginal velocity but increases operational complexity.

### Forex Pairs: All Negative
All 28 forex pairs show negative net/day at their pkl-computed values.
This is because the pkl was computed with different spread assumptions.
The forex pairs NEED to be re-swept with current spread data to get accurate velocity.
This is a DATA QUALITY issue, not a strategy issue.

---

## 📝 CONTENT ENGINE (2026-06-10)

### Structure
- `content-engine/BRAND_VOICE.md` — Brand guidelines, platform-specific voice
- `content-engine/knowledge/CONTENT_FUEL.md` — 1,626 stats organized for content
- `content-engine/posts/BATCH_1.md` — 15 ready-to-post pieces (Twitter x5, TikTok x5, Instagram x3, YouTube x2)
- `content-engine/templates/` — TikTok + Tweet templates

### Brand Positioning
- Anti-fake-trader, data-first, no vibes
- "We cracked the code" narrative
- 5 content pillars: Results, Lifestyle, Education, Community, Provocation

### Accounts
- YouTube: KEMETTRUCKING@GMAIL.COM (@FBO_LEGACY)
- Instagram: fbo_WXRLD
- TikTok: FBO_WXRLD (DABIGGESTPOPPA@GMAIL.COM)
- Credentials stored: `credentials/fbo_accounts.md` (gitignored)

### Status
- BATCH_1 complete, not yet posted
- Content CEO subagent produced all copy from Holy Grail data

---

## 🔐 CREDENTIALS

- Stored in `credentials/` directory (gitignored)
- `credentials/fbo_accounts.md` — FBO social media accounts
- Never commit credentials to any repo

_Last updated: 2026-06-10 12:40 EDT — Content engine + credentials documented_
_Last updated: 2026-06-07 02:30 EDT — Velocity optimizer complete, forex re-sweep needed_
