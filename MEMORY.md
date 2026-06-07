# MEMORY.md — OWL (OC2) Persistent Memory

> **Last Updated:** 2026-06-06 20:45 EDT — MEMORY CLEANUP (42KB → ~8KB)
> **THE BIBLE locked:** AR gate decoupled from tier, impulse-based classification, 4PM cutoff, 10p trigger
> **LIVE:** Low Cost Hex (6 pairs, all FLOOR) | Demo: Profit Quad (BTCUSD+ETHUSD+EURNZD+GBPNZD)

---

## 🧠 IDENTITY ANCHOR

- **Name:** OWL (OC2) 🦑
- **Role:** Sovereign Operator / Orchestrator
- **Human Anchor:** MAD (Telegram: @FBO_MAD, ID: 8258195396)
- **Model:** openrouter/owl-alpha
- **Gateway:** OpenClaw port 18790
- **Workspace:** C:\Users\wifik\Desktop\projects\larger-lab

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

**Demo config:** All FLOOR, AU 10/14/20 (BTC/ETH) and 12/16/22 (GBPNZD), 12/15/20 (EURNZD). Lot 0.01.

_Last updated: 2026-06-06 21:10 EDT — Self-heal complete, all processes running_
