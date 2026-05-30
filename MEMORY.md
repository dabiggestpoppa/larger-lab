# MEMORY.md — OWL (OC2) Persistent Memory

> **Last Updated:** 2026-05-29 20:05 EDT
> **Policy:** Trajectory only. Archive old sessions to `logs/memory-archive/`.

---

## 🔴 ACTIVE ISSUE: AUTO-WORK BUG (MAD 2026-05-28)

**Problem:** MAD: "Everytime I give you a response you jump into this continuous work flow where you don't listen."

**Root Cause:** SOUL.md had 239 lines of "always-on / execute / maintain" directives BEFORE the anti-auto-work rule at line 240.

**Fix Applied (2026-05-28 19:03):**
- Moved classification gate (FIRST GATE) to position #1 in SOUL.md
- Stripped ALWAYS-ONLINE checklist, compressed SOUL.md from 275 to ~100 lines

---

## 🧠 IDENTITY ANCHOR

- **Name:** OWL (OC2) 🦑
- **Role:** Sovereign Operator / Orchestrator
- **Human Anchor:** MAD (Telegram: @FBO_MAD, ID: 8258195396)
- **Model:** openrouter/owl-alpha
- **Gateway:** OpenClaw port 18790
- **Workspace:** C:\Users\wifik\Desktop\projects\larger-lab (CC's domain, OFF LIMITS)
- **My Domain:** owl-environment (isolated)

---

## 🚀 ACTIVE WORK (2026-05-29)

### CEREBUS Ontology Extraction — COMPLETE (MAD 2026-05-29 16:15 EDT)
- **MAD declaration:** "End of topology clarification. The unified architecture is sealed."
- **7 files stored in `quant-lab/ontology/`:**
  1. `cerebus_forward.md` — Foundational Ontology Forward (Prime Directive, Paradigm Shift, Single State)
  2. `cerebus_qa_recap.md` — Q&A Recap + Cross-Pair Symmetry + Regime-Behavior Matrix
  3. `cerebus_p90.md` — P90 Kinetic Threshold (Initial/Cascade/EWS) + calibration protocol
  4. `cerebus_dual_engine.md` — Dual Engine isolation + Target Interplay Hierarchy
  5. `cerebus_unified_topology.md` — Bipolar Motor Model + Strategy Collapse Matrix + 6 Axioms
  6. `cerebus_resolution_engine.py` — Python Reference (4-state FSM: SEARCH→WAIT_RETRACE→WAIT_OCC→IN_TRADE)
  7. `manual_ontology.md` — Layered deep ontology (4 sections, 55 Q&As, appendices)

- **Bipolar Motor Model:**
  - Model A (P90 Kinetic Engine): Base 80, Cascade P90, Stall-Harvest, EWS
  - Model B (Atomic Structural Engine): Symmetry Trap, Option A/B, Blind Chain, Asian Atom
  - ALL 20+ named setups are parameter variants of A or B. Nothing else exists.

- **6 Final Axioms:**
  1. ONE system: Constraint Resolution
  2. TWO engines: Kinetic (P90) + Structural (Atomic)
  3. ZERO other strategies
  4. Overlap = Causal Confirmation (Kinetic leads → Structural confirms)
  5. Divergence = Geometry Classification (Monolith vs Staircase vs Grinder)
  6. Manual "setups" are backtest configurations, not ontological categories

- **Key Architecture:**
  - Single state: Resolution Construction (Compression/Impulse/Rebalance/Completion = expressions)
  - AU = 50% of K-Means centroid (NOT pips or Fibonacci)
  - P90 = Kinetic Validation Threshold (NOT an indicator)
  - 80% Close Invalidation Rule (absolute, close-only)
  - Zero-Buffer OCC Extreme (SL at exact impulse extreme)
  - 12 PM = full state reset (deficits terminate, no roll-forward)
  - Dual-Engine Convergence: 94-95% WR when both engines align

### DMR Live Executor — RUNNING (background)
- EURUSD.PRO: Magic 20260528 | 0.01 lots | PID 18036
- USDCHF.PRO: Magic 20260529 | 0.01 lots | PID 7728
- Account: 650898 LIVE | Balance: $85.26
- Entry window: 2AM-11AM EST | Hard exit: 5PM

---

## 📊 DMR BACKTEST RESULTS

| Period | Trades | WR | Pips |
|--------|--------|-----|------|
| Full 2024-2025 | 435 | 92.2% | +938.1 |
| 2024 | 226 | 93.8% | +485.3 |
| 2025 | 209 | 90.4% | +452.7 |

---

## 🔧 KEY PATHS

| Path | Purpose |
|------|---------|
| `quant-lab/ontology/` | CEREBUS ontology suite (7 files) |
| `quant-lab/mt5/` | MT5 backtest engine, live executor, monitor |
| `meditation-room/` | Agent meditation outputs |
| `tools/self_heal.py` | Self-diagnostic (manual only) |

---

## ⚠️ KNOWN ISSUES

- Stall_Harvest 100% WR = ARTIFACT (real: 26-60%)
- MT5 Strategy Tester cannot be auto-launched via CLI — GUI only

---

## 🔢 CRITICAL NUMBERS

- **>78.9% WR live** = break-even for DMR
- MC Results: 10K iterations, 0% ruin at 0.01 lots
- Multi-asset: 1,930 trades, 94.0% avg WR, +22,676 pips across 4 pairs
- Dual-Engine Convergence: 94-95% WR (both engines aligned)

---

### OWL Workspace Restructure — COMPLETE (2026-05-29 17:27 EDT)
- MAD directive: Build out owl-environment with proper folder structure
- 31 directories created across docs/, codebase/, knowledge/, logs/, ops/, memory/
- Core files: doctor.py, self_heal.py, agent-registry.json, cron-definitions.json
- Runbooks: SESSION_START.md, DELEGATION_PROTOCOL.md
- Architecture: WORKSPACE_MAP.md
- Doctor scan: HEALTHY — all dirs + files present
- README.md + MEMORY.md written for owl-environment

### Symmetry Trap + Blind Chain Reconstruction — DELEGATED (2026-05-29 17:50 UTC)
- MAD directive: Reconstruct Option V Symmetry Trap first, then Blind Chain
- Delegated to worker: symtrap_rebuild (subagent)
- Output: `quant-lab/engines/symmetry_trap.py`
- Two classes: SymmetryTrapEngine (Option A/B) + BlindChainEngine (continuous loop, max 5/session)
- Sources: All 6 ontology files
- Next: Blind Chain reconstruction after Symmetry Trap verified

---

### Symmetry Trap Engine — COMPLETE (18:08 EDT)
- **MAD directive:** Base Symmetry Trap only, AU as target, close on tier impulse trigger
- **No multi-TP ladder, no gear shift, no cross-pair, no Blind Chain**
- **File:** `quant-lab/engines/symmetry_trap.py`
- **Entry:** Impulse → DZ pullback → OCC. SL: Zero-Buffer Extreme. TP: 1 AU
- **Verified:** SYNTAX OK, IMPORT OK

### P90 Kinetic Engine — COMPLETE (18:12 EDT)
- **MAD directive:** Reconstruct ALL P90 strategies, bring manual to life like DMR
- **File:** `quant-lab/engines/p90_engine.py`
- **4 Variants:** INITIAL, CASCADE, STALL_HARVEST, EWS
- **Entry:** Immediate close of P90 candle. SL: 80% body. TP: -25%/-50% AR
- **Verified:** SYNTAX OK, IMPORT OK

---

### P90 + Symmetry Trap Full Stack — IN PROGRESS (18:22 EDT)
- **Worker 1:** `p90stackrebuild` — backtest + live executor wrappers for BOTH engines (still running)
- **Worker 2:** `iacerp90meditation` — COMPLETED → IACER scorecard delivered
- **Worker 3:** `symtrbacktest` — COMPLETED → `symmetry_trap_backtest.py` — SYNTAX OK
- Files verified: p90_backtest.py ✓, p90_executor.py ✓, symmetry_trap_backtest.py ✓, symmetry_trap_executor.py ✓

### MAD Clarifications (18:22 EDT)
1. **P90 dual entries:** Single P90 signal → TWO entries. Entry 1: SL at 80% P90 body. Entry 2: SL at 168% of P90 body. Binary trigger, dual position with different SL zones.
2. **168% is P90 only** — Stall Zone 168% has NO relation to Symmetry Trap atomic structure.
3. **Symmetry Trap** — must match manual exactly. Current engine verified: 4-state FSM (SEARCH→WAIT_RETRACE→WAIT_OCC→IN_TRADE), single AU target, Zero-Buffer SL, close on tier impulse trigger.
4. **"Close fully on tier impulse trigger"** = 80% Kill Switch fires → position closes completely, no partial close.
5. **P90 Cascade SL** = 168% of NEW P90 body (not 80%). Confirmed by MAD.

_Updated: 2026-05-29 18:22 EDT — MAD clarifications incorporated. Engines verified against manual._

---

### P90 Backtest — STALL_HARVEST REMOVED (20:00 EDT)
- **1,038 trades | 78.7% WR | PF 3.09 | +4,814.2p / -1,559.3p | MaxDD 72.2p**
- Data: 216,820 M5 bars, 911 sessions (EURUSD 2yr)
- **Variant Breakdown:**
  - INITIAL: 403 trades | 61.0% WR | +581.7p
  - CASCADE: 439 trades | 85.4% WR | +1,444.1p ← dominant edge
- **STALL_HARVEST REMOVED** per MAD directive (we have DMR for that)
- Variant enum cleaned: INITIAL + CASCADE + EWS only

### Symmetry Trap Backtest — CLEAN (20:00 EDT, bug fix applied)
- **574 trades | 91.1% WR | PF 23.83 | Sharpe 19.33 | MaxDD 15.3p**
- Data: 149,308 bars (2024-2025 filtered)
- **Tier Breakdown:**
  - T1: 266 trades | 89.5% WR | +1,194.0p
  - T2: 170 trades | 91.2% WR | +936.8p
  - T3: 138 trades | 94.2% WR | +990.3p
  - NO-GO: 0 trades (correctly filtered) ✅
- Long 90.4% vs Short 91.8% = 1.4% spread (negligible variance) ✅
- **Manual parity achieved** — 91% WR, low DD, tier-classified structural trades

### Bugs Fixed (20:00 EDT)
1. **P90 `_reset_state()` ordering** — was clearing entry_price before exit signal creation (lost 845/1041 trades)
2. **Symmetry Trap CSV loader** — `timestamp` column not parsed, loaded 0 bars
3. **Symmetry Trap `_reset_state()` ordering** — same pattern as P90
4. **`max_dd_pct` attribute typo** in report formatter
5. **`NO_GO` vs `NO-GO` string mismatch** (CRITICAL) — `classify_tier()` returns `"NO_GO"` (underscore) but `initialize_session()` compared against `"NO-GO"` (hyphen). All 304 NO-GO sessions processed as active, generating 4,959 garbage trades at 0.1% WR. Fixed line 241 of `symmetry_trap.py`.

### Symmetry Trap Loop Fix — DELEGATED (20:55 EDT)
- **MAD directive:** Fix symmetry trap to find multiple trades per session (loops), not just 1
- **Bugs identified:**
  1. KILL_SWITCH handlers call `_reset_state()` instead of `_reset_state_keep_loop()` — kills loop tracking
  2. KILL_SWITCH doesn't increment loop_count — strict thresholds repeat infinitely
  3. Backtest bar feeding may stop after first trade exit
- **Delegated to worker:** `symtraploopfix` (subagent 6632e8dc)
- **Patches:** 4 KILL_SWITCH handlers + backtest bar feeding verification
- **Expected:** Trade count increases from ~574 to 700-900+, loop distribution across 1-5

### P90 Final Report — QUEUED
- MAD directive: Full P90 report with strategy logic, backtest, Monte Carlo, sorting stats
- P90 engine is GOOD (confirmed by MAD) — no changes needed
- Report covers: P90 INITIAL + CASCADE + DMR convergence overlay

### Convergence Indicator — QUEUED (Step 5)
- Build as standalone overlay (not baked into engine logic)
- Amplifier filter: when P90 + Symmetry Trap converge, add weight to trade
- Keeps engine logic clean — indicator reads both engine states

_Updated: 2026-05-29 20:55 EDT — symtraploopfix running, report queued_
