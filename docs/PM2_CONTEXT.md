# PM2 / OWL — Larger Lab Context File
> **Created:** 2026-06-08
> **Purpose:** Quick-reference for all trading system context. Load this first.
> **If you only read one file, read this one.**

---

## 🎯 CURRENT MISSION

Run the CEREBUS trading system. OC2 was the primary agent but kept going down. PM2 (me) + Copilot are now handling operations. MAD is the trader — he makes all decisions, we execute.

**MAD is stepping away. We keep the system running. No code changes without MAD approval.**

---

## 📊 SYSTEM STATUS (June 8, 2026)

### What's Running
| Component | File | Status | Notes |
|-----------|------|--------|-------|
| OC2 Gateway | `openclaw` | ✅ UP | ws://127.0.0.1:18790, health: live |
| Live Bridge | `quant-lab/mt5/cerebus_live_bridge.py` | ✅ UP | Low Cost Hex: EURJPY,EURNZD,GBPNZD,EURAUD,GBPAUD,GBPCAD |
| Guardian | `quant-lab/mt5/cerebus_guardian.py` | ✅ UP | Monitors bridge |
| Session Cleanup | `scripts/oc2_session_cleanup.py` | ✅ UP | --watch mode |
| Telegram Gateway | `scripts/telegram_gateway.py` | ⚠️ Crashes | Needs restart |
| OCE Backend | `oce/backend/main.py` | ✅ UP | Port 8000 |
| SRRA-OPC API | `srrs_opc/frontend/api_server.py` | ✅ UP | Port 8001 |

### Live Account
- **Broker:** OxSecurities-Live
- **Account:** 650898
- **Balance:** ~$65
- **Lot Size:** 0.01 for all assets
- **Deployed Config:** Low Cost Hex (6 pairs, all FLOOR)

---

## 🔑 KEY NUMBERS

### The 9K Trade Unlock (June 4)
- **Config:** ar_max=999 (no AR gate), trigger=8p, 4PM cutoff, DZ 20-50%
- **EURUSD result:** 1,125 → 9,228 trades (+720%), WR stayed 84.3%, PF 11.74
- **AR gate was #1 suppressor** — silently killing trading days
- **12p trigger was #2** — filtering micro-impulses

### Current Engine Standard
- **Engine:** `quant-lab/engines/symmetry_trap.py` (FROZEN — don't touch)
- **Backtest runner:** `quant-lab/engines/symmetry_trap_backtest.py`
- **Cost wrapper:** `quant-lab/backtest/apply_costs.py` (standalone, engine untouched)
- **Trigger_pips fix applied:** trigger stays at T1 value for all loops (not updating on tier reclassification)

### Sweep Results (28 FX pairs)
- **Floor avg WR:** 81.1%
- **Ceiling avg WR:** 90.8%
- **Floor total trades:** ~158,375
- **Data file:** `quant-lab/reports/trigger_sweep_max_accuracy.json`

### Cost Analysis
- **Commission:** $7/lot round-trip (0.01 lot = $0.07/trade)
- **Forex cost:** ~0.007 pips/trade (negligible)
- **XAU/Indices cost:** 0.07 pts/trade (significant)
- **Data file:** `quant-lab/reports/cost_analysis_native.json`

### Optimal Baskets
- **Low Cost Hex (Phase 1):** EURJPY+EURNZD+GBPNZD+EURAUD+GBPAUD+GBPCAD → $24,907 net, 81.4% WR, 10.9% cost
- **Max Profit Quad:** BTC+ETH+DE30+HK50 → $824K net, 79% WR
- **Full combinatorics:** `quant-lab/reports/GROUP_COMBINATORICS_FULL.md`

---

## 📁 CRITICAL FILES

| File | Purpose |
|------|---------|
| `quant-lab/QUANT_BIBLE.md` | Single source of truth — read this for full context |
| `quant-lab/engines/symmetry_trap.py` | THE ENGINE — frozen, don't touch |
| `quant-lab/mt5/deploy_config.py` | Per-pair deployment configs |
| `quant-lab/mt5/cerebus_live_bridge.py` | Live trading bridge |
| `quant-lab/configs/asset_configs.py` | Per-pair native AU/trigger values |
| `quant-lab/reports/trigger_sweep_max_accuracy.json` | Full sweep data (floor/ceiling per pair) |
| `quant-lab/reports/cost_analysis_native.json` | Cost-adjusted backtest results |
| `quant-lab/reports/SWEEP_MATRIX_V2.md` | Full combinatorics matrix |
| `quant-lab/backtest/apply_costs.py` | Post-hoc cost wrapper (standalone) |
| `scripts/pm2_watchdog.py` | Process monitor (this file's companion) |

---

## ⚠️ RULES (Non-Negotiable)

1. **NEVER touch the engine for a test. ALWAYS clone/wrap.**
2. **Engine is SACRED. Changes require MAD green light.**
3. **Costs are post-hoc overlay, NEVER embedded in engine.**
4. **1:1 parity between backtest and live. No new rules in live.**
5. **Each asset uses its own native AU targets. NOT universal.**
6. **Don't force pairs beyond their structural floor frequency.**
7. **CFDs ≠ spot FX. Can't use opposite market order to close (opens reverse position).**
8. **Use TRADE_ACTION_SLTP to close positions (set SL 1 pip beyond current price).**

---

## 🔧 LIVE TRADING SETUP

### Start Commands
```powershell
# Bridge (Low Cost Hex)
python quant-lab/mt5/cerebus_live_bridge.py --symbols EURJPY.PRO,EURNZD.PRO,GBPNZD.PRO,EURAUD.PRO,GBPAUD.PRO,GBPCAD.PRO --lot-size 0.01

# Guardian
python quant-lab/mt5/cerebus_guardian.py

# Session Cleanup
python scripts/oc2_session_cleanup.py --watch

# Telegram Gateway
python scripts/telegram_gateway.py
```

### MT5 Account
- Live: 650898@OxSecurities-Live
- Demo: 1114712@OxSecurities-Demo

### Pip Values
- Forex: $10/pip (both JPY and non-JPY)
- Crypto: $1/pt
- Metals: $1/pt
- Indices: $1/pt

---

## 🐛 KNOWN BUGS & FIXES

| Bug | Fix | Status |
|-----|-----|--------|
| Position gate blocking entries | Remove gate, close-then-enter | ✅ Fixed |
| Wrong ticket close | Store {direction: ticket} | ✅ Fixed |
| Close fails (retcode 10030) | Use TRADE_ACTION_SLTP | ✅ Fixed |
| Orphaned positions after restart | Check positions_get before close | ✅ Fixed |
| Race condition in active_trades | Use ticket from send_order() return | ✅ Fixed |
| AU targets not per-asset | Use per-pair native AU from asset_configs | ✅ Fixed |
| trigger_pips updating on tier reclass | Keep T1 trigger for all loops | ✅ Fixed |

---

## 📝 ERROR LOG

| Date | Error | Lesson |
|------|-------|--------|
| 6/4 | OC2 modified engine directly | Never touch engine for test |
| 6/4 | Spread values 10x off | Use historical CSV, not live MT5 |
| 6/4 | All assets using EURUSD AU | Each pair has own native AU |
| 6/5 | Bridge killed by watchdog loop | Watchdog needs better detection |
| 6/6 | OC2 went down multiple times | Spawn sub-agents for resilience |
| 6/7 | Cost analysis wrong (commission 100x too high) | commission_pips = $7 / pip_value (no lot_size in denominator) |

---

## 🎭 AGENT ROSTER

| Agent | Role | Status |
|-------|------|--------|
| OC2 | Primary operator (Telegram) | ⚠️ Unstable — kept going down |
| PM2 (me) | Safety layer / watchdog | ✅ Active |
| Copilot | Test execution / validation | ✅ Active |
| MAD | Trader / decision maker | 👑 Authority |

---

## 📞 WHEN TO ALERT MAD

- Critical process dies and can't restart
- Live account balance drops >20%
- Unexpected trades on wrong symbols
- Bridge disconnects from MT5
- Any engine file is modified

## 🤫 WHEN TO STAY SILENT

- Normal scanning (no signals)
- Routine log entries
- Process restarts that succeed
- Weekend market closure
