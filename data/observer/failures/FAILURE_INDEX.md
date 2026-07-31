# FAILURE_INDEX — Structural Friction Log
> Linked: `[[OPTIMIZATION_LOG]]` | `[[ONTOLOGY_CORE]]`

---

## Strategy Failures

### MT5 Strategy Tester — Zero Trades
- **What:** `DMR_FULL_BACKTEST.mq5` compiled but produced 0 trades
- **Root Cause:** Forward-scanning bar logic incompatible with Strategy Tester's tick processing
- **Fix:** Use backward-scanning, OnTick() with bar-change detection
- **Status:** Fixed — rebuilt as P90 engine

### Pine Script — WR 94% → 1.85%
- **What:** TradingScript `strategy.entry(..., limit=price)` missed fills
- **Root Cause:** Limit orders miss fills when price gaps through level intra-bar (common M5)
- **Verdict:** Pine Script NOT viable for this strategy. Fundamental fill model mismatch
- **Status:** Abandoned — use Nautilus or MT5 EA

### DMR Standalone → Deprecated
- **What:** Old standalone DMR backtest engine
- **Root Cause:** Merged into P90 Kinetic Engine — same system, P90 is kinetic validation layer
- **Status:** Deprecated — use `p90_engine.py`

### Stall_Harvest 100% WR Artifact
- **What:** STALL_HARVEST reported 100% WR
- **Root Cause:** Artifact — real performance 26-60%
- **Status:** Removed from P90 enum per MAD directive

---

## Orchestration Failures

### Auto-Work Bug (OWL)
- **What:** Heartbeat fires → OWL immediately starts investigating/building unrequested
- **Root Cause:** "Always-on" directive before anti-auto-work rule. First reflex = scan/build
- **Fix:** FIRST GATE at position #1 in SOUL.md. Heartbeat = classify ONLY. No tools unless ON FIRE
- **Status:** Fixed 2026-05-28, reinforced 2026-05-30

### OWL Executing Instead of Delegating
- **What:** OWL doing work directly instead of spawning agents
- **Root Cause:** "Who do I assign this to?" not the first thought
- **Fix:** Hard law #1 — OWL does NOT execute. Delegate everything.
- **Status:** Fixed 2026-05-28, operational principle in SOUL.md

---

## System Failures

### MT5 Strategy Tester CLI Launch
- **What:** Cannot auto-launch MT5 Strategy Tester via CLI
- **Root Cause:** MT5 tester requires GUI interaction
- **Status:** Known limitation — GUI only

### Nautilus ↔ CSV Divergence
- **What:** Nautilus backtest results must match CSV engine results within ~5%
- **Rule:** If Nautilus diverges, something is wrong with Nautilus setup, NOT the strategy code
- **Status:** Cross-validation requirement active

---

## Pattern Recognition

**Repeated failure modes:**
1. Fill model mismatch (Pine Script, limit orders)
2. Bar scanning direction (forward vs backward)
3. Look-ahead bias in backtesting
4. Asset config too tight/silver (XAGUSD)

**Structural friction rule:** When orchestration fails, map the exact anatomy: when, where, what follows. Known failure structure = fixable. Unknown = iterate.
