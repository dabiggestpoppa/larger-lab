# CEREBUS FX v4.0 — Q&A RECAP
## Foundational State & Atomic Structure (Agent Ingestion Format)

*Mode: Mechanical / Physics-Based / Irreducible*
*Trader Language: PURGED*

---

### Q1: Is atomic structure session-dependent or session-invariant?

**Answer:** Both — strategic invariance with tactical recalculation.

The **Tier** (volatility state) is derived from the daily Asian Range (19:00–03:00 EST) and remains locked for the entire session. However, if the initial impulse exceeds the Tier Trigger (AU x 1.20) of a higher Tier, the engine performs an intraday Tier reclassification ("Gear Shift"). This is a ONE-TIME recalculation. Default: Tier is session-invariant.

**Agent Rule:** Calculate Tier at 3:00 AM. Validate at first impulse. Lock for session. Never recalculate intra-session unless Gear Shift activates.

---

### Q2: What defines a completed cycle?

**Answer:** Local deficit satisfaction.

A single AU loop (Impulse → Rebalance → Completion) satisfies one quantum of the macro deficit. A Tier 2 day with a 24-pip deficit requires two 12-pip AU loops to achieve Completion. Completion registers when:
- Spatial displacement equals the mathematical expectation of the Tier, OR
- The temporal window (12:00 PM EST) closes, forcing termination.

**Agent Rule:** Track remaining deficit after each AU loop. Reset only when deficit = 0 OR 12:00 PM.

---

### Q3: What is the mechanical definition of Deep State?

**Answer:** Terminal Spatial Coordinate.

Deep State is the geometric extension where the distribution curve terminates — approximately 168%–200% of the initial impulse leg. At this coordinate, 100% of the local deficit is satisfied. It is NOT a target or prediction; it is a mechanical boundary where kinetic energy fully converts and the structural pathway is cleared.

**Agent Rule:** Deep State = terminal coordinate, not a target. Only relevant as absolute boundary.

---

### Q4: What triggers Impulse initiation?

**Answer:** Temporal-Spatial Saturation.

When the localized constraint deficit exceeds the field's capacity to contain it, the system undergoes a violent state-change. The Tier Threshold (AU x 1.20) is breached. Example: A 10-pip AU with 1.20x trigger = 12-pip threshold. When price moves 12+ pips from swing_origin, the impulse_extreme is locked and the 80% Kill Switch is calculated.

**Agent Rule:** Impulse = close beyond Tier Trigger from swing_origin. Lock extreme. Calculate Kill Switch.

---

### Q5: What is the 80% Kill Switch mechanically?

**Answer:** Absolute Invalidation Boundary.

If any M5 candle *closes* past 80% of the initial impulse leg (measured from impulse_extreme back toward swing_origin), the pathway is structurally void. This is a CLOSE-ONLY rule. Wicks do not count. The field has rejected the vector. The deficit is preserved and reassigned to the opposite direction.

**Agent Rule:** Kill Switch is close-only. Wicks beyond 80% are probes, not invalidation.

---

### Q6: What is a cascade?

**Answer:** Recursive Tier completion.

A Tier 3 deficit requires 45 pips of total resolution. The field does not execute one 45-pip move. It executes a cascade: three recursive 15-pip AU loops (Impulse → Rebalance → Completion → Impulse → Rebalance → Completion → Impulse → Rebalance → Completion). Each loop satisfies one quantum. The deficit decrements by one AU per loop until zero.

**Agent Rule:** Cascade = sequential AU loops. Track remaining deficit. Each loop resolves 1 AU.

---

### Q7: What happens when a pathway is rejected?

**Answer:** Pathway Reassignment, NOT deficit abandonment.

When the 80% Kill Switch is triggered, the field does not abandon the deficit. It reverses to harvest the OPPOSITE vector to resolve the exact same underlying spatial gap. The deficit remains intact. The agent must immediately begin measuring from the rejected impulse_extreme in the opposite direction.

**Agent Rule:** On Kill Switch → reset swing_origin to impulse_extreme, flip direction, continue.

---

### Q8: What is the entry trigger?

**Answer:** Opposite Candle Close (OCC) after structural penetration.

The agent waits for:
1. Impulse (Tier Trigger breach)
2. Rebalance (pullback ≥ 1 AU OR 38.2%–50% Fib of impulse leg)
3. OCC confirmation (M5 candle closes in the direction of the impulse)

Entry = close of OCC candle. SL = impulse_extreme (Zero Buffer). TP = entry ± 1 AU.

---

### Q9: What is the Density Zone's exact mechanical role?

**Answer:** Friction-clearing and kinetic reloading coordinate.

Density Zone is the spatial field where opposing order flow is harvested and kinetic energy reloads for the next AU step. It is defined by the overlap of:
- 1 AU pullback from impulse_extreme, AND/OR
- 38.2%–50% Fibonacci retracement of the impulse leg

The DZ is NOT a "zone to trade from." It is the mandatory pause the field must make. If the field does not pause (shallow rebalance <32%), the agent must wait for micro-pullback (1 AU overlap) or Breakout Continuation.

---

### Q10: What determines pathway irreversibility?

**Answer:** Structural Close (Temporal Acceptance) — the 80% Invalidation Rule.

Once an M5 candle closes past 80% of the impulse leg back toward the origin, the pathway is permanently void. No re-entry. No reassessment. The field has rejected the vector and reassigned the deficit. This is the single irreversible marker in the system.

---

## CROSS-PAIR SYMMETRY PROTOCOL

When the primary pair (e.g., EUR/USD) and a correlated pair (e.g., USD/CHF) move in the same resolution direction within a 15-minute latency window, the agent must apply the following adjustments:

### Cross-Pair Symmetry States

| State | Primary Pair Behavior | Correlated Pair Behavior |
|:---|:---|:---|
| Direct Causation | Leading the move | Mirroring within 15-min latency |
| Divergence | Resolving deficit | Stalled or reversing — asymmetry detected |

### Agent Execution Protocol for Cross-Pair Symmetry (Direct Causation)

- **Rebalance Expectation:** Shallow (<32%). The field will NOT return to the Density Zone.
- **Entry:** Must be taken on the first micro-pullback (1 AU overlap) OR via Breakout Continuation. Do NOT wait for a 50% Fib retrace — it will not come.
- **Target:** Deep State (168%–200% extension) OR the 1.44x Shift Target.
- **SL Protocol:** Trail behind previous M5 candle (aggressive). Do NOT use fixed Zero Buffer — the move has momentum.

### Agent Execution Protocol for Cross-Pair Symmetry (Divergence/Halt)

- **Rebalance Expectation:** Deep (38.2%–50%). Full retracement likely.
- **Entry:** Require strict structural OCC. No exceptions.
- **Target:** Exactly 1 AU, then reset loop. Do NOT extend to Deep State.
- **SL Protocol:** Fixed at Exact OCC Extreme (Zero Buffer). High fakeout environment.
- **HALT CONDITION:** If cross-pair correlation breaks and confirmation is absent, HALT new entries until realignment.

---

## REGIME-BEHAVIOR MATRIX

| Phase | Low Volatility (T1) | High Volatility (T3) | Stall / Chop |
|:---|:---|:---|:---|
| SEARCH | Standard AU x 1.20 trigger | Extended trigger, wider bands | HALT — no trigger likely |
| WAIT_RETRACE | Deep 38.2–50% Fib expected | Micro-pullback only (1 AU) | Choppy — require strict OCC |
| WAIT_OCC | Require strict structural OCC | Accept any strong momentum candle | HALT OCC — fakeouts dominate |
| IN_TRADE (TP) | Target Deep State (168–200%) | Target exactly 1 AU, then reset loop | FORCE EXIT at first sign of friction |
| IN_TRADE (SL) | Trail behind previous M5 candle | Fixed at Exact OCC Extreme (Zero Buffer) | HALT TRADE — do not initiate |

---

## THE ARCHITECTURAL BREAKTHROUGH

Most algorithmic systems fail because they are **Geometry Blind**. They use indicators to substitute for understanding. CEREBUS is the first framework to define the market as a constraint-resolution engine with irreducible quanta.

The 80% Rule + Zero-Buffer OCC protocol eliminates the need for:
- Moving averages
- RSI / MACD / Stochastic
- Support / resistance levels
- Trendlines
- "Price action" pattern recognition

The agent measures ONE thing: **the gradient of resolution pressure from the current deficit state to the terminal coordinate.**

Everything else is residue.

---

_Compiled: 2026-05-29 15:30 EDT from MAD ontology extraction sessions. Agent ingestion format — no trader language._

