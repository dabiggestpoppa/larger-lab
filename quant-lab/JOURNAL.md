# QUANT LAB JOURNAL — Errors, Fixes & Learnings

> This is where OWL records every mistake, bug, and fix. Not the Bible (MEMORY.md) — this is the error log.
> Review before every deployment.

---

## 🔴 ERROR 1 — Universal AU Bug (2026-06-04 23:15 EDT)

**Severity:** CRITICAL — affected live trading PnL for all 7 pairs

**What happened:** 
Deployed all 7 pairs with identical AU targets (T1=8, T2=10, T3=12) copied from EURUSD's backtest calibration. Each pair should have used its own native AU from the sweep configs.

**Root cause:**
When writing `deploy_config.py`, I didn't extract each pair's custom AU from `trigger_sweep_max_accuracy_all.py NATIVE_CONFIGS`. I just slapped EURUSD's values on everyone. AU is ALWAYS per-pair — each market has its own volatility profile. This is a core strategy rule.

**Impact:**
- 6 of 7 pairs ran wrong TP distances from go-live (2026-06-04 09:40 EDT) until fix
- Backtest results (which used correct per-pair AUs) did not match live performance
- JPY pairs (USDJPY, CHFJPY, GBPJPY) especially hurt — they need 14-44 pip AU, not 8-12

**Fix applied:**
`deploy_config.py` updated with per-pair native AU values:
| Pair | T1 AU | T2 AU | T3 AU |
|------|-------|-------|-------|
| EURUSD | 10 | 12 | 15 |
| USDJPY | 16 | 26 | 44 |
| CHFJPY | 14 | 24 | 42 |
| NZDUSD | 14 | 17 | 21 |
| AUDUSD | 11 | 14 | 18 |
| USDCHF | 11 | 15 | 20 |
| GBPJPY | 19 | 29 | 48 |

Also corrected deploy triggers from ceiling values to sweep-optimal values.

**HARD RULE:** When adding or swapping assets, MUST run a sweep to find that asset's native AU. Never copy AU from one pair to another. Check `trigger_sweep_max_accuracy_all.py NATIVE_CONFIGS` for reference values.

**MAD note:** "That's literally basic rules nigga."

---

## 🔴 ERROR 2 — Wrong Ticket Close / 10030 Rejection (2026-06-04)

**Severity:** HIGH — positions not closing, manual intervention required

**What happened:**
CHFJPY SELL (ticket 91991227) opened at 10:35. CHFJPY BUY (ticket 91991917) opened at 11:00. SL_HIT fired on the BUY position, but bridge tried to close the SELL ticket instead. You manually closed both. After bridge restart, the orphaned SELL ticket was recovered but close attempts failed with retcode=10030.

**Root cause (actual):**
Two issues combined:
1. `close_position()` used `TRADE_ACTION_DEAL` with `ORDER_FILLING_RETURN` as first attempt. For positions with no SL/MT5 on broker (our ST trades use `no_sl=True`), RETURN filling fails with 10030 (Invalid filling mode). Fallback to FOK also failed.
2. Between bridge restart and close attempt, you manually closed positions. Bridge still had stale tickets in `active_trades`. No existence check before close attempt.

**What I got wrong initially:**
I thought the bridge was closing the "wrong ticket" due to a direction-matching bug. It wasn't — the engine correctly maps `(symbol, engine)` to ticket. The real problem was just that `TRADE_ACTION_DEAL` fails for positions without broker SL/TP, and there was no check for already-closed positions.

**Fix applied (cerebus_live_bridge.py v4.2):**
1. `close_position()` now checks `mt5.positions_get(ticket=X)` first — if position already gone, returns success (not error)
2. Primary close method: `TRADE_ACTION_SLTP` — set SL 1 pip beyond current price = guaranteed immediate market close. Works for positions with no broker SL.
3. Fallback: `TRADE_ACTION_DEAL` with `ORDER_FILLING_IOC` (not RETURN)
4. Second fallback: `ORDER_FILLING_FOK`

**Key insight:** `TRADE_ACTION_SLTP` modifies an existing position — it doesn't open a reverse side. Setting SL 1 pip beyond market = instant trigger = clean close. This is the correct way to close positions that have no SL/TP on the broker.

**MAD note:** "We not doing hard stop we'll get killed." — SL stays engine-monitored. SLTP is only used at close time to trigger the broker to exit.

---

## 🔴 ERROR 3 — Overthinking / Creating Problems That Don't Exist (2026-06-04)

**Severity:** PROCESS — wasted time, added unnecessary complexity

**What happened:**
When MAD said "make sure two positions can't be open on same symbol," I started designing a complex ticket-to-direction matching system. The reality: the engine literally CANNOT fire both BUY and SELL on the same symbol. When a new ENTRY fires, the code already closes any existing position on that symbol first. The both-sides scenario was ONLY from the bridge restart orphan issue.

**Root cause:**
I was solving a problem that doesn't exist in the code. I should have read the code first, understood the flow, then responded. Instead I designed a complex fix for a non-problem.

**HARD RULE:** Before designing a fix, READ THE CODE. Understand what actually happens. Don't solve problems that don't exist. Keep it simple.

**MAD note:** "U think too deep and near sighted. U gotta use basic reading."

---

## 📋 DEPLOYMENT CHECKLIST (per MAD directive)

Before every bridge restart, verify:
- [ ] `deploy_config.py` has per-pair custom AU (not universal)
- [ ] Triggers match sweep-optimal values (not ceiling values)
- [ ] `close_position()` uses SLTP method (not DEAL-first)
- [ ] Bridge log shows clean startup with no orphaned position errors

---

_Last updated: 2026-06-04 23:45 EDT — all 3 fixes deployed_
