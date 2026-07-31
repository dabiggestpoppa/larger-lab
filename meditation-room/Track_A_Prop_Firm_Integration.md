# 🧘 SAGE MEDITATION — Track A: Prop Firm Integration

> **Date:** 2026-05-31 18:14 EDT
> **Agent:** Sage (Strategic Meditation)
> **Directive:** MAD — "Last add to the lab before full power"
> **Target:** London open (3:00 AM EDT)
> **Classification:** PURE STRATEGIC CLARITY — no fluff

---

## 0. FIRST PRINCIPLE — WHAT "PLUG PROP ACCOUNTS INTO THE ENGINE" ACTUALLY MEANS

This is the most important section. Everything else derives from it.

**The engine does not change.** CEREBUS (P90 CASCADE + Symmetry Trap) generates signals. The MT5 executors read those signals and place orders. The engine is broker-agnostic — it sends `mt5.order_send()` to whatever MT5 terminal is running.

**"Plugging in prop accounts" means:**
1. MAD buys prop firm challenge accounts (e.g., $50K Apex, $100K Topstep)
2. Each account gets its own MT5 login/terminal (or the same terminal with different magic numbers)
3. The CEREBUS executors connect to those MT5 accounts instead of (or alongside) the current live account 650898
4. The Sniper Engine's PES calculator determines HOW MANY accounts, WHAT SIZE, and WHAT RISK PARAMETERS per account
5. The system must RESPECT prop firm rules (daily loss limits, trailing DD, consistency) or the account dies

**The critical insight:** Prop accounts are not a different asset class. They are the SAME trading strategy running against DIFFERENT capital containers with DIFFERENT constraint surfaces. The engine stays the same. The risk layer adapts.

---

## 1. STRATEGIC ASSESSMENT

### 1.1 Regular MT5 Account vs Prop Firm Account — The Real Differences

| Dimension | Regular Account (650898) | Prop Firm Account |
|-----------|--------------------------|-------------------|
| **Capital** | Your money | Firm's money (you trade it, don't own it) |
| **Loss limit** | Account equity → margin call | Daily loss limit (e.g., 5% of balance) → account terminated |
| **Drawdown** | Floating DD allowed | Trailing DD ceiling (e.g., 6% from peak equity) → instant kill |
| **Profit** | 100% yours | Split (e.g., 80/20 or 90/10 after threshold) |
| **Consistency** | None | Max day profit often capped at 30-50% of total |
| **Payout** | Continuous | Cyclical (biweekly/monthly) with buffer days |
| **Scaling** | Add capital anytime | Must hit profit target + wait delay period |
| **News** | Trade through anything | Some firms restrict news trading |
| **Leverage** | Broker-defined | Firm-defined (often 1:100 or 1:30) |

### 1.2 Specific Challenges Prop Accounts Introduce

**A. Daily Loss Limit (DLL) — HARD KILL**
- If account loses >X% in a single day, account is terminated immediately
- This is NON-NEGOTIABLE. No recovery. No appeal.
- Current executor has `MaxDailyTrades` but NO daily loss circuit breaker
- **This is the #1 risk to solve before London open**

**B. Trailing Drawdown — HARD KILL**
- DD is measured from peak equity, not from starting balance
- If you make $2K then lose $3K, you might be at -$1K from peak even though you're +$1K from start
- Most firms: trailing DD = 6-10% of starting balance
- **Must track peak equity per account, not just current P&L**

**C. Consistency Rule — SOFT KILL (delayed)**
- If one day's profit is >30-50% of total profit, payout may be delayed or denied
- This doesn't kill the account but kills the payout cycle
- **Must distribute profit across days, not front-load**

**D. Minimum Trading Days — GATE**
- Must trade X days (usually 5-10) before payout eligibility
- Can't just hit target in 2 days and request payout
- **Must ensure minimum trade frequency**

**E. Profit Target — GATE**
- Must hit X% profit (e.g., 8-10%) to qualify for payout or scaling
- **Engine must know the target and adjust position sizing to reach it within the payout cycle**

### 1.3 What the Sniper Engine Already Solves

The PES calculator already models:
- Effective leverage from daily loss limits ✓
- Consistency drag ✓
- Scaling friction ✓
- Crossover threshold (when props become inferior to live) ✓
- Survival probability across N accounts ✓

**What it does NOT yet do:**
- Real-time daily loss tracking per account ✗
- Trailing drawdown monitoring per account ✗
- Position sizing that adapts to remaining DLL budget ✗
- Kill switch that stops trading when DLL is approached ✗
- Multi-account orchestration (one signal → N accounts) ✗

---

## 2. ARCHITECTURE DESIGN

### 2.1 The Prop Account Adapter Layer

The existing MT5 executors (`p90_cascade_executor.py`, `symmetry_trap_executor.py`) are designed for a single account. They need a **Prop Account Adapter** that sits between the engine and the MT5 terminal.

```
CURRENT ARCHITECTURE:
  CEREBUS Engine → MT5 Executor → MT5 Terminal (Account 650898)

TARGET ARCHITECTURE:
  CEREBUS Engine → Signal Router → Prop Account Adapter → MT5 Terminal (Prop Account 1)
                                            ↳ Prop Account Adapter → MT5 Terminal (Prop Account 2)
                                            ↳ Prop Account Adapter → MT5 Terminal (Prop Account N)
                                            ↳ (optional) MT5 Executor → MT5 Terminal (Live Account)
```

**The Prop Account Adapter is a new module. It does:**
1. Receives trade signals from the engine (same format as current executors)
2. Looks up the prop account's rule profile (DLL, trailing DD, consistency)
3. Checks current day's P&L against remaining DLL budget
4. Checks peak equity vs current equity for trailing DD
5. If safe → places the order via MT5 with account-specific magic number
6. If unsafe → blocks the signal, logs the block, alerts
7. Tracks per-account state (daily P&L, peak equity, trade count, days traded)

### 2.2 Config Generator Extension for Prop Firm-Specific Configs

The current `config_generator.py` generates a `deployment_config` with firm_mix and risk parameters. It needs extension:

**New config sections needed:**
```yaml
prop_account_rules:
  daily_loss_limit_pct: 0.05        # 5% daily loss limit
  trailing_dd_pct: 0.06             # 6% trailing drawdown
  consistency_max_day_pct: 0.30     # 30% max day profit
  min_trading_days: 5
  profit_target_pct: 0.08           # 8% profit target
  payout_cycle_days: 14

risk_circuit_breakers:
  dll_warning_threshold: 0.03       # Warn at 3% daily loss (60% of limit)
  dll_hard_stop_threshold: 0.045    # Stop at 4.5% (90% of limit)
  trailing_dd_warning: 0.04         # Warn at 4% trailing DD
  trailing_dd_hard_stop: 0.055      # Stop at 5.5% trailing DD
  max_daily_trades: 3               # Cap trades per day per account

position_sizing:
  method: "dll_budget"              # Size positions based on remaining DLL budget
  risk_per_trade_pct: 0.01          # 1% of account per trade (conservative)
  max_concurrent_trades: 1          # Only 1 trade at a time per account
```

The `config_generator.py` already has `_derive_risk_parameters()` — this needs to be extended to read from the firm's rule profile and generate the above sections.

### 2.3 Where MAD's Trade Copier Fits

**Assessment:** MAD's trade copier is likely a signal bridge that copies trades from one MT5 account to another (or multiple). This is architecturally redundant with the Prop Account Adapter concept BUT may be useful as the SIGNAL DISTRIBUTION layer.

**Two possible integration patterns:**

**Pattern A: Copier as Signal Bridge (PREFERRED)**
```
CEREBUS Engine → Signal Router → Trade Copier → Multiple MT5 Terminals
```
- The copier receives signals from the engine (or from the primary executor)
- It replicates them to multiple MT5 terminals (prop accounts)
- The copier handles the multi-account distribution
- **Pros:** Already built, tested, handles the hard problem of multi-terminal sync
- **Cons:** May not have prop rule awareness (DLL, trailing DD checks)

**Pattern B: Adapter Replaces Copier**
```
CEREBUS Engine → Prop Account Adapter → Multiple MT5 Terminals
```
- The adapter handles both signal distribution AND prop rule enforcement
- **Pros:** Full control, prop-aware at every step
- **Cons:** Must build and test from scratch

**RECOMMENDATION:** Use Pattern A with the copier as the distribution layer, BUT add a **Prop Rule Guard** module that sits between the engine and the copier. The Guard checks prop rules and only passes signals that are safe. The copier then distributes the approved signals.

```
CEREBUS Engine → Prop Rule Guard → Trade Copier → MT5 Terminals (Prop Accounts)
                      ↓
                 (blocks unsafe signals)
```

### 2.4 PES Calculator Enhancement for Prop Rules

The PES calculator already models DLL and consistency. What needs enhancement:

**A. DLL-Aware Position Sizing**
Current: `risk_per_trade = 1.0 / effective_leverage` (static)
Needed: `risk_per_trade = remaining_dll_budget / (stop_loss_pips * pip_value)` (dynamic)

The position size must shrink as the day's P&L approaches the DLL. If you've already lost 3% of a 5% DLL, your next trade can only risk 2%.

**B. Trailing DD Tracking**
Current: Not tracked
Needed: Track `peak_equity` per account. At each trade decision:
```
current_dd = (peak_equity - current_equity) / starting_balance
if current_dd > trailing_dd_hard_stop: BLOCK ALL SIGNALS
if current_dd > trailing_dd_warning: REDUCE SIZE BY 50%
```

**C. Consistency-Aware Profit Distribution**
Current: Consistency drag is a static penalty in PES
Needed: Active profit management across the payout cycle:
```
if today_profit > consistency_max_day_pct * total_cycle_profit:
    REDUCE POSITION SIZE for remaining trades today
    (let tomorrow absorb more profit)
```

**D. Multi-Account PES**
Current: `multi_account_pes()` calculates PES for N accounts but doesn't optimize across accounts
Needed: Given M prop accounts with different rules, find the optimal allocation:
- Which accounts get signals today?
- Which accounts are near DLL and should rest?
- Which accounts are close to profit target and should be prioritized?

---

## 3. EXECUTION PIPELINE

### 3.1 Exact Flow: Signal → Prop Account Execution

```
STEP 1: SIGNAL GENERATION
  CEREBUS Engine (P90 CASCADE or Symmetry Trap) generates signal
  Signal contains: direction (BUY/SL), entry_price, SL_price, TP_price, lot_size
  Signal is written to signals.jsonl (current pattern)

STEP 2: PROP RULE GUARD (new module)
  Reads signal from signals.jsonl
  For each active prop account:
    a. Check daily P&L vs DLL budget
    b. Check trailing DD vs peak equity
    c. Check consistency (today's profit vs total cycle profit)
    d. Check if account has already hit profit target
    e. Check minimum trading days remaining
  If ALL checks pass → signal is APPROVED for that account
  If ANY check fails → signal is BLOCKED for that account (logged)
  Output: {account_id: APPROVED/BLOCKED, reason: ...}

STEP 3: SIGNAL DISTRIBUTION
  If using Trade Copier: Approved signals are fed to copier input
  If using Adapter: Adapter places orders directly via MT5 API
  Each account uses unique MagicNumber for order tracking

STEP 4: ORDER EXECUTION
  MT5 order_send() with account-specific parameters
  SL and TP are set on the order (prop firms require defined risk)
  Lot size is calculated from DLL budget, not fixed

STEP 5: MONITORING
  After each trade closes:
    Update daily P&L
    Update peak equity
    Update trade count
    Update days traded
    Recalculate remaining DLL budget
    Feed back to Step 2 for next signal

STEP 6: END-OF-DAY RECONCILIATION
  At HardExitHour (17:00 EST):
    Close all open positions
    Log final daily P&L
    Update PES snapshots
    Generate daily report
    Reset daily counters (but NOT peak equity or cycle counters)
```

### 3.2 Scope Pipeline Evolution for Live Prop Management

The current `scope.py` pipeline is: SCAN → VERIFY → CALCULATE → RANK → OUTPUT

For live prop account management, this evolves to:

```
CURRENT (Analysis):
  SCAN firms → VERIFY promos → CALCULATE PES → RANK → OUTPUT config

LIVE (Management):
  SCAN accounts → VERIFY rules unchanged → CALCULATE remaining budget → 
  CHECK all circuit breakers → APPROVE/DENY signal → EXECUTE → MONITOR → 
  RECONCILE → UPDATE state → LOOP
```

The key shift: scope runs ONCE to determine the optimal deployment. Then a **live management loop** runs continuously during market hours.

### 3.3 What Happens Before London Open vs What Can Be Staged

**BEFORE LONDON OPEN (Critical Path):**
1. Prop Rule Guard module — must be built and tested
2. DLL tracking per account — must be live
3. Trailing DD tracking per account — must be live
4. Kill switch (hard stop at 90% DLL) — must be live
5. Position sizing from DLL budget — must be live
6. Multi-account signal distribution — must work with copier or adapter
7. End-of-day reconciliation — must be live

**CAN BE STAGED (After London Open):**
1. Consistency-aware profit distribution (soft rule, not immediately critical)
2. Multi-account PES optimization (can start with equal allocation)
3. Payout cycle tracking (important but not day-1 critical)
4. Scaling automation (only relevant after first payout)
5. F&F protocol activation (requires verified promo codes)

---

## 4. RISK / SYSTEM INTEGRITY

### 4.1 How the System Ensures Prop Rule Compliance

**Layer 1: Pre-Trade Checks (Prop Rule Guard)**
- Every signal is checked against every account's rule state BEFORE execution
- This is the PRIMARY defense. No signal reaches MT5 without passing.

**Layer 2: Executor-Level Checks**
- Each executor has its own DLL check as a safety net
- If the Guard misses something, the executor catches it
- Redundant by design — two independent checks

**Layer 3: MT5-Level Safety**
- Orders are placed with defined SL (no market orders without SL)
- Lot size is calculated to ensure SL loss < remaining DLL budget
- Hard exit at 17:00 EST closes everything

**Layer 4: Monitoring & Alerts**
- `cerebus_monitor.py` already monitors live positions
- Extend it to track DLL usage and trailing DD per account
- Alert when any account is at >60% of DLL
- Auto-flatten at >90% of DLL

### 4.2 Kill Switches

**Kill Switch 1: Daily Loss Limit (PER ACCOUNT)**
```
Trigger: daily_pnl < -(account_balance * dll_hard_stop_threshold)
Action: Close all open positions, block all new signals for rest of day
Alert: Immediate (Telegram/notification)
Reset: Next trading day (EST midnight)
```

**Kill Switch 2: Trailing Drawdown (PER ACCOUNT)**
```
Trigger: (peak_equity - current_equity) > (starting_balance * trailing_dd_hard_stop)
Action: Close all open positions, block all new signals indefinitely
Alert: CRITICAL — account may be terminated
Reset: Manual only (MAD approval)
```

**Kill Switch 3: System-Level (ALL ACCOUNTS)**
```
Trigger: >3 accounts hit DLL in same day, OR total daily loss >Y% of combined prop AUM
Action: Stop ALL trading across ALL accounts for rest of day
Alert: CRITICAL — system halt
Reset: Next trading day + MAD review
```

**Kill Switch 4: Connection Loss**
```
Trigger: MT5 connection lost for >60 seconds
Action: Attempt reconnect 3 times, then flatten all positions on reconnect
Alert: HIGH — connection issue
Reset: Manual after connection restored
```

### 4.3 Monitoring Requirements Specific to Prop Accounts

**Per-Account Dashboard (extend existing cerebus_monitor.py):**
- Daily P&L vs DLL budget (progress bar, turns red at 60%)
- Trailing DD vs peak equity (progress bar, turns red at 70%)
- Today's profit as % of total cycle profit (consistency check)
- Days traded toward minimum
- Profit target progress
- Trade count today vs max

**Alert Levels:**
- **GREEN:** All metrics <60% of limits
- **YELLOW:** Any metric 60-80% of limit → reduce size
- **ORANGE:** Any metric 80-90% of limit → stop new trades
- **RED:** Any metric >90% of limit → flatten and halt

---

## 5. SEQUENCED IMPLEMENTATION PLAN

### Phase A-0: Pre-Work (Can Start Immediately, ~30 min)
**Goal:** Understand exactly what MAD is buying and what the trade copier can do.

- [ ] Get list of prop firms MAD is purchasing from
- [ ] Get account sizes and rule profiles for each account
- [ ] Test the trade copier: can it copy from one MT5 to multiple MT5 terminals?
- [ ] Determine if copier can filter by magic number (to route different strategies)
- [ ] Document copier's input/output format

**Deliverable:** `prop_account_inventory.md` — list of accounts, rules, copier capabilities

### Phase A-1: Prop Rule Guard (Critical Path, ~2 hours)
**Goal:** Build the module that prevents prop rule violations.

- [ ] Create `quant-lab/sniper/prop_rule_guard.py`
- [ ] Implement per-account state tracking (daily P&L, peak equity, trade count)
- [ ] Implement DLL check: `remaining_dll = dll_limit - abs(daily_loss)`
- [ ] Implement trailing DD check: `current_dd = (peak - current) / start`
- [ ] Implement consistency check: `today_pct = today_profit / total_cycle_profit`
- [ ] Implement position sizing: `lot_size = (remaining_dll * account_balance) / (sl_pips * pip_value)`
- [ ] Write unit tests for all checks (edge cases: exactly at limit, 1 pip over, etc.)
- [ ] Test with historical data: run against past signals, verify no rule violations

**Deliverable:** `prop_rule_guard.py` with tests, verified against historical data

### Phase A-2: Multi-Account Executor Adapter (Critical Path, ~2 hours)
**Goal:** Route approved signals to multiple MT5 accounts.

- [ ] Create `quant-lab/mt5/prop_account_dispatcher.py`
- [ ] Read deployment config to get list of active prop accounts
- [ ] For each account: connect to MT5 with account-specific credentials
- [ ] For each approved signal: place order on each approved account
- [ ] Use account-specific magic numbers for order tracking
- [ ] Handle partial fills and rejections per account
- [ ] Log per-account execution results

**PARALLELIZABLE with A-1** — different module, different developer

**Deliverable:** `prop_account_dispatcher.py` that can send signals to multiple MT5 accounts

### Phase A-3: Config Generator Extension (~1 hour)
**Goal:** Generate prop-rule-aware deployment configs.

- [ ] Extend `config_generator.py` to output `prop_account_rules` section
- [ ] Add `risk_circuit_breakers` section with warning/hard-stop thresholds
- [ ] Add `position_sizing` section with DLL-budget method
- [ ] Update `_derive_risk_parameters()` to read from firm rule profiles
- [ ] Generate config for MAD's actual prop accounts (from Phase A-0)

**Deliverable:** Updated config generator + actual deployment config for MAD's accounts

### Phase A-4: Monitoring Extension (~1 hour)
**Goal:** Real-time prop rule monitoring.

- [ ] Extend `cerebus_monitor.py` to track per-account DLL usage
- [ ] Add trailing DD tracking per account
- [ ] Add alert levels (GREEN/YELLOW/ORANGE/RED) per account
- [ ] Add auto-flatten on RED alert
- [ ] Add end-of-day reconciliation (log daily P&L, update snapshots)

**Deliverable:** Updated monitor with prop rule dashboards

### Phase A-5: Integration & Testing (~1 hour)
**Goal:** Wire everything together and verify.

- [ ] Connect: Engine → Rule Guard → Dispatcher → MT5 Terminals
- [ ] Test with paper/simulation: send signals, verify guard blocks correctly
- [ ] Test with small size: 1 prop account, minimum lot, verify full pipeline
- [ ] Test kill switches: simulate DLL breach, verify halt
- [ ] Test end-of-day: verify reconciliation and state reset

**Deliverable:** Full pipeline tested and verified

### Phase A-6: London Open Deployment (~30 min)
**Goal:** Go live.

- [ ] Load deployment config with MAD's actual accounts
- [ ] Start all prop account MT5 terminals
- [ ] Start Prop Rule Guard
- [ ] Start Prop Account Dispatcher
- [ ] Start Monitor
- [ ] Verify first signal passes through the full pipeline
- [ **LONDON OPEN: 3:00 AM EDT** ]

---

## 6. CRITICAL PATH ANALYSIS

```
A-0 (Pre-Work) ──→ A-1 (Rule Guard) ──→ A-5 (Integration) ──→ A-6 (Go Live)
                ──→ A-2 (Dispatcher) ──↗
                ──→ A-3 (Config) ──────↗
                ──→ A-4 (Monitor) ─────↗
```

**Critical Path:** A-0 → A-1 → A-5 → A-6 (~6 hours)
**Parallel Work:** A-2, A-3, A-4 can run in parallel with A-1

**If MAD assigns 2 workers:**
- Worker 1: A-0 → A-1 → A-5 → A-6
- Worker 2: A-0 → A-2 → A-3 → A-4 → A-5 (join for integration)

**Estimated time to London open:** 4-6 hours with 2 workers, assuming no blockers.

---

## 7. KEY RISKS & MITIGATIONS

| Risk | Impact | Mitigation |
|------|--------|------------|
| Trade copier can't handle multi-account | High | Build adapter from scratch (A-2) as fallback |
| MT5 connection instability on prop accounts | High | Connection loss kill switch + auto-reconnect |
| Prop firm rules differ from expected | Critical | Read actual TOS for each firm, hardcode rules per account |
| Position sizing bug causes DLL breach | Critical | Two-layer check (Guard + Executor), test extensively |
| Signal latency across multiple accounts | Medium | Acceptable — CEREBUS trades M5, seconds of latency don't matter |
| Prop firm detects automated trading | Medium | Vary timing slightly, use human-like lot sizes |
| Peak equity tracking fails | High | Recalculate from trade history on each check, don't rely on state |

---

## 8. WHAT "FULL POWER" LOOKS LIKE

After Track A is complete:

```
CEREBUS Engine (P90 CASCADE + Symmetry Trap)
    ↓
Signal Router (routes to appropriate accounts)
    ↓
Prop Rule Guard (checks all prop rules per account)
    ↓
Prop Account Dispatcher (sends to N MT5 terminals)
    ↓
┌─────────────────────────────────────────────┐
│  Prop Account 1 (Apex $50K)                 │
│  Prop Account 2 (Topstep $100K)             │
│  Prop Account 3 (ATF $50K)                  │
│  ...                                        │
│  Prop Account N                             │
│  Live Account 650898 (optional)             │
└─────────────────────────────────────────────┘
    ↓
Monitor (tracks all accounts, alerts, kill switches)
    ↓
Sniper Engine (PES snapshots, rebalancing, payout tracking)
    ↓
CARE Engine (capital routing, profit extraction)
```

**The system trades the SAME strategy across MULTIPLE capital containers with DIFFERENT constraints.** Each account is an independent risk surface. The engine doesn't care — it just generates signals. The Guard and Dispatcher handle the complexity.

This is the last add. After this, the lab runs at full power.

---

## 9. SAGE CLOSING MEDITATION

The architecture is sound. The Sniper Engine already has 80% of the math. The MT5 executors already work. The gap is:

1. **Per-account rule awareness** (the Guard)
2. **Multi-account signal distribution** (the Dispatcher or Copier)
3. **Real-time rule monitoring** (extended Monitor)

These are engineering problems, not research problems. The math is known. The patterns exist. It's assembly, not invention.

The deepest risk is not the engineering — it's the **assumption that prop firm rules are static**. Firms change rules without notice. The `live_firm_monitor()` in the Sniper Engine already detects rule changes via snapshot comparison. This must be connected to the live pipeline: if a firm changes its DLL from 5% to 3%, the Guard must know immediately.

The second deepest risk is **correlation**. If all prop accounts trade the same signal at the same time, a single losing trade hits ALL accounts simultaneously. This is why the PES calculator's survival probability uses `S = 1 - (1-p)^n` — diversification across firms with different rules and instruments reduces correlated failure. But in practice, if all accounts trade EURUSD.PRO in the same direction, they're 100% correlated. The system should consider:
- Different instruments across accounts (if the engine supports it)
- Staggered entry timing
- Different strategy variants per account (P90 CASCADE on some, Symmetry Trap on others)

This is the last add. Build it right. Test it thoroughly. Then run at full power.

---

*End of Sage Meditation — Track A: Prop Firm Integration*
*Written: 2026-05-31 18:14 EDT*
*For: MAD — Full Power Directive*
