# MANAGER IACER P90 + SYMMETRY TRAP RECONSTRUCTION
## IACER Reflection Meditation — 2026-05-29 18:17 EDT

> **Manager Audit Target:** `quant-lab/engines/p90_engine.py` + `quant-lab/engines/symmetry_trap.py`
> **Ontology Sources:** cerebus_p90.md, cerebus_dual_engine.md, cerebus_unified_topology.md, cerebus_qa_recap.md, manual_ontology.md
> **Scope:** Full pipeline assessment — ontology fidelity, engine correctness, backtest/live execution risk

---

## I — INTERFERENCE

*What could corrupt the backtest or live execution?*

### I.1 Data Integrity Interference

**I.1a — Bar Timestamp Alignment (CRITICAL)**
The entire ontology is temporally quantized: Asian Session = 19:00–03:00 EST, Activation Window = 03:00–12:00 EST. If bar timestamps are stored in UTC without session-aware extraction, the Asian Range calculation silently includes activation-window candles or excludes the first/last Asian candles. A 1-hour offset corrupts Tier classification. A 5-hour offset (UTC vs EST) corrupts *everything*.

**Risk: FATAL.** The engine would compute deficit against the wrong spatial compression shell. Every downstream calculation (AU, Trigger, Density Zone, OCC) inherits the corruption.

**Specific vulnerability in p90_engine.py:** If the INITIAL variant computes `asian_high`/`asian_low` from raw bar data without explicit session-window filtering, the Tier is wrong from the start.

**I.1b — Tick vs M5 Close ambiguity**
The ontology states: "Wicks are probes (reversible). Closes are commitments (irreversible)." The 80% Kill Switch is close-only. OCC is close-only. SL is close-only. TP can be wick OR close.

If the backtest engine evaluates SL/TP intra-bar (using high/low/close of the same bar), it creates a look-ahead bias or an ordering ambiguity. Which is evaluated first: SL or TP? If a single M5 bar both wicks past the SL extreme AND wicks past the AU target, the outcome depends on evaluation order. The ontology does NOT specify intra-bar sequencing for same-bar SL/TP hits.

**Risk: MODERATE.** In backtest, this creates phantom wins or phantom losses. In live execution, the broker fills whichever is touched first (typically the closer one = SL if SL is tighter than TP distance).

**I.1c — Data Gaps (Weekends, Holidays, Illiquid Periods)**
If the feed has a gap (e.g., Thursday close to Sunday open), the first M5 bar of the new session may have an anomalous body size. The P90 calibration would be contaminated by gap candles. The ontology says P90 is calibrated from activation-window M5 candles over 3 months — gap candles should be excluded from the calibration sample.

**Risk: LOW-MODERATE.** Degrades P90 threshold accuracy over time, causing false positives (gap candle counted as P90 breach) or missed signals (true P90 below inflated threshold).

### I.2 Execution Interference

**I.2a — Spread Costs**
The ontology's Zero-Buffer Protocol means SL = exact impulse_extreme. On a 10-pip AU move with entry at DZ, the SL distance is approximately 1 AU + Density Zone depth (38.2–50% of impulse). For EUR/USD T1: impulse ≈ 12p, DZ ≈ 4–6p, SL distance ≈ 12–14pips. With a 1.0-pip spread, the effective SL is 13–15 pips. The -50% AR target for T1 is ~10 pips. This means the R-multiple is <1R *before slippage* on the smallest moves.

**Risk: FATAL for T1 Scalps.** The backtest must model spread as a fixed cost per trade, or the WR and expectancy numbers from the ontology (83–95%) are unreachable in live execution. The manual's backtest results (89% WR, 1.92R) already include spread — if the engine doesn't subtract spread from every P&L, the backtest lies.

**I.2b — Slippage on Entry**
Symmetry Trap entry is "close of OCC candle." In live execution, the agent cannot enter at the close price — it enters on the next bar's open. This is 1 bar of slippage. For a T1 move (12p impulse), 1 bar of slippage on a fast M5 move could be 2–4 pips. The DZ pullback may complete and the continuation may begin before the fill.

**Risk: MODERATE.** Affects Symmetry Trap more than P90 (P90 enters on the same candle close, which is also impossible live — same problem applies but P90 is an immediate trigger so the slippage is on the same temporal scale).

**I.2c — Partial Fill / Rejection in Live Execution**
Not modeled in backtest at all. If the broker rejects the order during a fast move (thin liquidity at the DZ), the structural entry is missed. The cascade continues without the agent.

**Risk: LOW probability, HIGH impact.** One missed entry in a cascade means the remaining AU loops are orphaned.

**I.2d — 12 PM Hard Cutoff Timing**
The engine terminates at 12:00 PM EST. If the agent has an open position at 11:59:59, the close-at-market at 12:00:00 is a forced exit. In a fast market, this could be at a highly unfavorable price. The ontology says "force-close all positions" but doesn't specify: market order or limit order at current price?

**Risk: LOW-MODERATE.** A few pips of forced-exit slippage per session. Accumulates over time.

### I.3 Structural Interference

**I.3a — Cross-Pair Correlation Breakdown**
The Cross-Pair Symmetry Protocol (QA Recap) adjusts SL and target based on the correlated pair's behavior. If the correlation breaks intraday (e.g., EUR/USD resolves deficit but USD/CHF stalls), the agent must HALT. Correlation is regime-dependent — in high-volatility regimes, correlations spike; in low-volatility regimes, they dissipate.

**Risk: MODERATE-HIGH.** Running the cross-pair filter without a correlation-threshold gate will produce false halts or false continuations.

**I.3b — Tier Gear Shift Edge Case**
If the first impulse is *exactly* at the Tier Trigger boundary (e.g., AU=10, Trigger=12.0, impulse=12.0), does the engine round up or down? The ontology says "exceeds" (>), but floating-point comparison `>=` vs `>` matters at the boundary. A 12.0001-pip impulse vs 11.9999-pip impulse changes the entire session's AU step-size.

**Risk: LOW probability of hitting exact boundary, but HIGH impact when it does.** Floating-point arithmetic must use a small epsilon or explicit rounding to 1 decimal place (pip precision).

---

## II — ALIGNMENT

*Do the engines correctly implement the ontology? Any gaps or missing elements?*

### II.1 P90 Engine — Alignment Audit

**II.1a — Four Variant Coverage**
The ontology defines exactly 4 P90 variants:
1. **Initial P90** (Bias Setter): First breach of Asian Band with body ≥ P90. SL = 80% of body. Target = -25%/-50% AR.
2. **Cascade P90** (Momentum Persistence): 2nd/3rd P90 in same direction within 120 min. SL = 168% of NEW P90 body.
3. **Stall-Harvest P90** (Terminal): P90 at 168% Stall Zone. Entry = immediate. Target = reversion.
4. **EWS P90** (Exit Signal): Opposite P90 at target = force-close, NOT reversal entry.

**Alignment check:** p90_engine.py must implement all 4 as parameter states of ONE engine, not 4 separate engines. The unified topology explicitly requires this. Each variant is a conditional branch inside the same state machine, keyed on: (a) is this the first P90 of the session? (b) is there an existing P90 within 120 min in the same direction? (c) is price at the 168% Stall Zone? (d) is the P90 in the opposite direction of the active pathway?

**Gap check:** The EWS P90 is an EXIT signal, not an entry. If p90_engine.py treats EWS as a 5th entry variant (reversal), it violates the ontology: "An opposite-direction P90 at a macro target is NOT a reversal signal — it is a Momentum Exhaustion Signal."

**II.1b — P90 Kinetic Validation of Tier Trigger**
Ontology: Tier Trigger fires FIRST (spatial breach). P90 validates SECOND (kinetic confirmation). Both must confirm.

**Alignment check:** The engine must check spatial breach AND body size in the same evaluation path. A P90 body ≥ threshold on a candle that did NOT breach the Asian Band = no signal. A Tier Trigger breach with body < P90 = elastic deformation = no signal. Both conditions must be atomic.

**II.1c — SL Protocol Per Variant**
- Initial P90: SL = impulse_extreme – 80% of P90 body (measured from close)
- Cascade P90: SL = 168% of NEW P90 body (Note: the ontology says "168% of new P90 body" — this is a different SL mechanism from Initial. Verify the engine doesn't apply the 80% body SL to Cascade.)
- Stall-Harvest: SL = 80% of P90 body (same as Initial but at terminal coordinate)
- EWS: No entry, so no SL. Only action = force-close existing position.

**II.1d — Reset Behavior**
After ANY P90 exit (TP or SL), does the engine correctly reset? The Initial P90 in Option A mode should reset the state machine (one fire per session). Cascade and Stall-Harvest should remain active for subsequent prints. The engine needs a `reset_mode` parameter (single_fire vs continuous).

### II.2 Symmetry Trap Engine — Alignment Audit

**II.2a — State Machine Completeness**
The Symmetry Trap is a 4-state FSM: SEARCH → WAIT_RETRACE → WAIT_OCC → IN_TRADE.

**Alignment checklist:**
- **SEARCH:** Monitors for Tier Trigger breach + 80% Kill Switch calculation. Locks impulse_extreme. Transitions to WAIT_RETRACE.
- **WAIT_RETRACE:** Two exit conditions: (1) 80% Kill Switch close → reset to SEARCH, (2) Pullback ≥ 1 AU OR 38.2–50% Fib → transition to WAIT_OCC. Both are valid.
- **WAIT_OCC:** Waits for M5 close in impulse direction. Entry at close. SL = impulse_extreme (Zero Buffer). TP = entry ± 1 AU. Transitions to IN_TRADE.
- **IN_TRADE:** TP hit (wick or close) → exit, reset. SL hit (close only) → exit, reset. 12 PM → force exit.

**Gap check:** The ontology states the Density Zone is defined by 1 AU overlap AND/OR 38.2–50% Fib. The engine should accept EITHER condition (whichever comes first). If the engine requires BOTH (AU AND Fib simultaneous), it will miss entries where only one condition is met.

**II.2b — Zero-Buffer SL Protocol**
The SL is the *exact* impulse_extreme. No buffer. No rounding. This means: for a LONG position, SL = impulse_high (the highest price of the impulse candle). If the OCC candle's wick exceeds the impulse extreme but the entry close does NOT, the SL hasn't been breached (SL is close-only). Verify the engine checks SL only on close, not wick.

**II.2c — OCC Definition**
OCC = first M5 candle that closes in the impulse direction after the rebalance begins. The engine must track: (1) impulse direction locked, (2) DZ entry confirmed, (3) first subsequent close in impulse direction. A close that merely returns to the DZ (not through it) may not qualify — the close must be beyond the DZ boundary in the impulse direction.

**Potential gap:** If the engine defines OCC as "any close in impulse direction after DZ penetration" without requiring the close to be *beyond* the DZ, it will trigger on the first candle inside the DZ, which may be too early.

**II.2d — Cascade Reset (Option B / Blind Chain)**
After exit, the engine must set `swing_origin = exit_price` and return to SEARCH. The deficit (remaining AU steps to target) must decrement. If the engine doesn't decrement the deficit, it will re-enter the same AU loop indefinitely.

**Critical gap:** Does the Symmetry Trap engine track the *remaining deficit* (total AU steps to Tier Target)? The ontology says a T2 deficit of 24 pips requires exactly two 12-pip AU loops. The engine must know this limit. Without deficit tracking, it will keep looping past the Tier's mathematical completion — trading beyond the resolution boundary.

**II.2e — Deep State / Terminal Coordinate**
At 168–200% extension, the Symmetry Trap engine should not initiate new entries. The Stall Zone (168%) is for P90's Stall-Harvest variant, but the Symmetry Trap engine itself should HALT new entries in this zone. The ontology implies the Symmetry Trap targets 1 AU per loop, with optional extended targets to -25%/-50% AR — but never beyond Deep State.

**Gap:** If the Symmetry Trap engine doesn't have a terminal coordinate gate, it will attempt AU loops in a depleted energy environment where the deficit has already been partially resolved by prior loops.

### II.3 Cross-Engine Alignment

**II.3a — Isolation Requirement**
The ontology's cardinal rule: "Crossing the streams mathematically destroys the edge." P90 entry must use P90 SL (80% body). Symmetry Trap entry must use Symmetry Trap SL (Zero-Buffer Extreme). The two SL mechanisms must NEVER be mixed.

**Alignment check:** Are the engines implemented as fully independent modules with separate SL/TP management? Or do they share an SL parameter? If they share, it's a fatal architecture violation.

**II.3b — Convergence Logic**
When both engines fire simultaneously (P90 breach + DZ pullback + OCC), the ontology allows two valid actions:
1. Take P90 entry (immediate, 80% body SL)
2. Wait for Symmetry Trap entry (DZ + OCC, Zero-Buffer SL)

The ontology explicitly states: Symmetry Trap entry is "mathematically superior due to DZ pullback" — better entry price, structurally superior SL. The engine should default to Symmetry Trap when both are available.

**Gap:** The dual-engine convergence is the highest-value scenario (94–95% WR). If the engines don't correctly identify convergence and execute the Symmetry Trap path (not the P90 path), the edge is left on the table.

**II.3c — EWS P90 Interaction with Symmetry Trap Positions**
An opposite P90 at the target should force-close a Symmetry Trap position EVEN IF the AU target hasn't been reached. This is an override rule. Verify the P90 engine can emit a signal that forces the Symmetry Trap engine to exit.

---

## III — CONTRADICTION

*Any contradictions between ontology files or between engine implementations?*

### III.1 Intra-Ontology Contradictions

**III.1a — P90 Cascade SL: 80% vs 168%**
- `cerebus_p90.md` Section II says: "80% of the P90 candle's body" as invalidation boundary for Initial P90.
- `unified_topology.md` says: Cascade P90 SL = "168% of NEW P90 body."
- `cerebus_p90.md` Section VII (Pseudo-Code) says: `calculate_invalidation_boundary` returns `80% of body` — no variant for Cascade.

**Contradiction:** The generalized `calculate_invalidation_boundary` function doesn't have a Cascade branch. If the engines implement the pseudo-code literally, Cascade P90 gets the wrong SL. The ontology resolved this in the unified topology doc, but the P90-specific doc is not self-consistent.

**Severity: MODERATE-HIGH.** The wrong SL changes the R-multiple calculation for ~30% of P90 trades (cascade variants).

**III.1b — Density Zone Definition: AU Overlap vs Fibonacci**
- `manual_ontology.md` Section 1 Q6: DZ is defined by AU overlap. "The AU dictates the exact structural boundary; Fibs are merely a statistical shadow."
- `cerebus_qa_recap.md` Q9: DZ is defined by "1 AU pullback AND/OR 38.2–50% Fibonacci retracement."
- `cerebus_resolution_engine.py` (Appendix B of manual_ontology): DZ penetration = "pullback ≥ 1 AU OR 38.2%–50% Fib."

**Tension:** The ontology says AU is the ground truth and Fibs are approximation. But the mechanical implementation uses Fibs as an independent trigger ("OR"). This means the engine can enter on a 38.2% Fib pullback that is NOT 1 AU — which contradicts the ontology's claim that the AU is the irreducible anchor.

**Resolution (probable):** On clean T1/T2 loops, 38.2–50% Fib aligns with 1 AU overlap (~85% of the time per manual). The "OR" is a pragmatic relaxation for the ~15% of cases where Fib and AU diverge.

**Severity: LOW-MODERATE.** Creates a small percentage of entries where the structural anchor is Fib-based rather than AU-based. These 15% of cases may have different statistical properties.

**III.1c — Stall Zone: 168% of What?**
- `cerebus_p90.md` Section III: "EWS P90 prints at the Terminal Spatial Coordinate (e.g., -50% or -100% Asian Range extension) or the 168% Stall Zone."
- `manual_ontology.md` Section 2 Q8: "Stall (e.g., at 168% extension) occurs when resolution output collides with a dense historical constraint cluster."
- `unified_topology.md` Section II target table: "168% Extension = Macro Rebalance Node."

**Ambiguity:** 168% of WHAT? Is it 168% of the Asian Range, or 168% of the initial impulse leg, or 168% of the cumulative AU displacement? The ontology uses "extension" without a clear base reference. For a T1 range (20 pips), 168% = 33.6 pips from origin. For a T2 range (25 pips), 168% = 42 pips. These are very different coordinates.

**Severity: MODERATE-ZONE.** The 168% Stall Zone is used by the Stall-Harvest P90 variant. If the base reference is wrong, the entire variant triggers at the wrong spatial coordinate.

**III.1d — P90 Engine: Is EWS a Separate Variant?**
- `cerebus_p90.md` Section III: Lists EWS P90 as one of 3 P90 types (Initial, Cascade, EWS). Stall-Harvest is mentioned separately in Section VI integration table.
- `unified_topology.md` Section II: Lists 4 P90 variants: Base 80, Cascade, Stall-Harvest, EWS.

**Clarification needed:** Is EWS an entry variant (attempting to enter a reversal) or strictly an exit signal? `cerebus_p90.md` says "NOT a reversal signal — it is a Momentum Exhaustion Signal. Agent Action: Force-close." But the unified topology table lists EWS under "MODEL A VARIATIONS" alongside Base 80, Cascade, and Stall-Harvest.

**Resolution:** EWS is NOT an entry setup. It is a position management signal. The table's inclusion under "variations" refers to the parameter state space, not to signal direction.

**Severity: LOW** if the engines implement correctly. **HIGH** if a developer reads the table literally and builds an EWS entry variant.

### III.2 Engine-to-Ontology Contradictions

**III.2a — Single AU Target in Symmetry Trap Base**
The base Symmetry Trap targets exactly 1 AU. But the ontology's "Distribution Symmetry Trap" extends targets to -25%/-50%/-100% AR. Is this a separate engine, a parameter switch, or a completely different trade management layer?

If `symmetry_trap.py` implements ONLY the 1 AU target (base Symmetry Trap), then the Distribution Symmetry Trap is an unfilled gap in the codebase. The ontology says the Distribution Symmetry Trap entry is identical — only the TP ladder differs. This should be a `target_mode` parameter, not a separate engine.

**Severity: MODERATE.** Missing implementation of the highest-value target mode.

**III.2b — Cascade Tracker State**
The P90 engine tracks cascades (2nd/3rd P90 within 120 minutes in the same direction). This requires memory across AU loops. The Symmetry Trap engine also runs cascading loops (Option B = continuous reset). Both engines need a shared or independent cascade counter.

**Risk:** If the cascade counters are independent, the P90 engine might register a "Cascade P90" that doesn't correspond to the Symmetry Trap's AU loop count, creating conflicting signals.

**Severity: LOW-MODERATE.** Mainly a synchronization concern. Mitigated by engine isolation.

---

## IV — EXTRACTION

*What critical insight from the ontology is most likely to be missed by developers?*

### IV.1 The Deterministic/Probabilistic Boundary

This is the single most critical architectural insight in the entire ontology, and it is the MOST LIKELY to be violated by developers adding "improvements":

| **NEVER Probabilistic (Hard Law)** | **OK to be Probabilistic** |
|---|---|
| Asian Range / Tier classification | 9 AM checkpoint boost |
| 80% Close Invalidation Rule | Which direction breaks first |
| 12 PM Hard Exit | Rebalance duration |
| Zero-Buffer OCC Extreme (SL) | Gear Shift likelihood |
| AU Target (50% of Centroid) | Regime confirmation |

Developers will inevitably want to add: "confidence scores" to the 80% rule, "soft exits" before 12 PM, "dynamic buffers" to OCC SL, or "weighted AU targets." Every one of these optimizations DRIFTS THE ARCHITECTURE. The ontology is explicit: these are binary structural laws. The 2–5% backtest miss rate is spread/slippage — NOT structural failure. If a developer tries to "improve" the hard laws to reduce the 2–5% miss rate, they will destroy the edge.

**The edge EXISTS because the laws are incorruptible.** Any probabilistic softening introduces trader judgment, which is the exact failure mode the ontology was designed to eliminate.

### IV.2 The Bipolar Motor Principle

Developers will see 20+ named setups in the manual and implement them as separate strategies. This is TAXONOMIC FRAGMENTATION — the core error the unified topology document explicitly warns against. The fix: exactly 2 engines, each with parameter variants. The cascade is not a new strategy — it's Model A with `subsequent_activation` enabled. The Blind Chain is not a new strategy — it's Model B with `continuous_loop_reset` enabled.

The implication for code structure: `p90_engine.py` and `symmetry_trap.py` should share a `shared_context` data bus (Asian Range, Tier, AU, Regime, Bias) but maintain INDEPENDENT execution paths. Any shared mutable state other than the data bus creates coupling that corrupts the isolation requirement.

### IV.3 Candles as Observer Artifacts

The ontology is crystal clear: candles are "observer compression artifacts." The fundamental objects are structural events: Band Break, OCC Close, 80% Close, AU Hit. The engine should internally operate on events and treat candles as the API layer only.

**Practical implication:** The engines should be designed to accept tick data directly. The M5 bars are a feed format, not a structural requirement. If the engines hardcode "M5 candle close" as the validation point, they cannot be tick-optimized. The ontology's tickless-operability proof (manual_ontology.md Q18) is an architecture directive: decouple the event logic from the bar format.

### IV.4 Pathway Reassignment, Not Failure

When the 80% Kill Switch fires, the engine must NOT treat it as a "loss and reset." It must flip direction and re-measure from the impulse_extreme. The deficit is preserved. The pathway is reassigned. This is a fundamental design principle that affects the SEARCH state implementation.

If the engine resets to a neutral state after a Kill Switch, it will miss the next AU loop in the opposite direction — which may be the actual resolution pathway. The direction flip is mandatory, not optional.

---

## V — RECONSTRUCTION RISK ASSESSMENT

*Risk assessment of the full pipeline: engine → backtest → live executor*

### V.1 Engine Layer Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Timestamp/Session misalignment | Medium | Fatal (all downstream wrong) | Use explicit EST session windows; validate Asian Range against known calendar |
| P90 Cascade SL uses wrong % (80% vs 168%) | Medium (code follows pseudo-code, not unified topology) | Moderate (wrong R-multiple on 30% of P90 trades) | Use unified topology as the canonical spec |
| Density Zone triggers on Fib without AU (or vice versa) | High (OR logic by design) | Low-Moderate (15% of entries are Fib-only) | Acceptable per ontology; log AU/Fib divergence for post-trade analysis |
| Symmetry Trap doesn't track remaining deficit for cascade loops | Medium | High (over-trading beyond Tier completion) | Add deficit counter; decrement per AU loop; halt at zero |
| EWS P90 implemented as reversal entry | Low-Moderate (developer misreads the table) | Fatal (trading against active deficit) | Add explicit comment in code: "EWS is EXIT ONLY" |
| 12 PM hard cutoff not implemented or implemented as soft exit | Low-Moderate | Moderate (position held past engine termination) | Hard market order at 11:59:59 EST |
| Gear Shift uses wrong comparison (>= vs >) | Low (boundary hit is rare) | High (wrong AU for entire session) | Use epsilon: `if impulse > trigger + 1e-4` |

### V.2 Backtest Layer Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| No spread cost modeled | Very High (typical developer omission) | Fatal (backtest lies by 1-2 pips per trade) | Subtract fixed spread from every entry/exit P&L |
| Intra-bar SL/TP ordering ambiguity | High (most backtest engines don't model this) | Moderate (phantom wins/losses) | Use conservative assumption: SL checked before TP on same bar |
| Look-ahead bias in P90 calibration | High (using full-day candles for P90 threshold) | Moderate (P90 threshold includes future data) | P90 must be calibrated from rolling lookback, not the current session |
| Survivorship bias in historical data | Low (FX pairs don't delist) | Low | Not a major concern for Forex |
| Gap candles contaminating P90 calibration | Medium | Low-Moderate | Filter gap candles from calibration sample |
| Asian Range calculated from wrong session window | Medium | Fatal | Explicit 19:00-03:00 EST filter with timezone awareness |

### V.3 Live Executor Layer Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Entry fill delay (enter on next bar open, not current close) | 100% (structural) | Moderate (1 bar slippage per entry) | Model this in backtest; if edge survives 1-bar slippage + spread, proceed |
| Spread widens during news/events | High (daily) | High (effective SL widens) | Add spread-threshold filter: if spread > 2x normal, HALT new entries |
| Broker rejects/partially fills at DZ | Low | High (missed structural entry) | Use market orders at OCC (not limit); accept higher slippage |
| 12 PM forced exit at market price | 100% (per protocol) | Low-Moderate (end-of-session slippage) | Acceptable; do NOT hold past 12 PM |
| Internet/feed disconnection during trade | Low | Fatal (active trade unmanaged) | Implement local SL/TP with broker (not platform-side); verify OCO orders supported |
| Daylight saving time shift | Medium (2x/year) | Fatal (all session windows shift 1 hour) | Use timezone-aware datetime (America/New_York) with DST handling |

### V.4 Pipeline Composite Risk

**Engine → Backtest:** Medium-High risk. The backtest must replicate the engine's event logic exactly AND add spread + slippage. Any divergence between backtest event logic and engine event logic makes the backtest meaningless.

**Backtest → Live:** Medium risk. The live executor must handle the 1-bar entry delay, spread variation, and disconnection scenarios that the backtest models as constants.

**Overall Pipeline Confidence: MEDIUM.** The ontology provides a complete and self-consistent specification (modulo the minor contradictions noted). The primary risks are implementation-level: timestamp handling, spread modeling, and the deterministic/probabilistic boundary. The physics are sound; the engineering must be precise.

---

## VI — STRATEGY QUALITY SCORECARD

### VI.1 P90 Initial (Model A — Bias Setter)

| Dimension | Assessment |
|-----------|------------|
| **Predicted WR Range** | 81–85%. Ontology baseline for standalone Model A. The lowest of all P90 variants because it's the first kinetic breach — highest elastic deformation rate. |
| **Edge Source** | Kinetic validation of spatial breach. The P90 body filter separates plastic deformation (pathway acceptance) from elastic deformation (liquidity probe) with ~81.2% accuracy. The edge comes from NOT trading the <P90 elastic probes that revert. |
| **Fatal Risk** | Trade without spread model. On a T1 day (10-pip AU), the -25% AR target is 5 pips. With 1-pip spread and 1-pip slippage, the effective target is 3 pips against a ~12-pip SL. R-multiple = 0.25R. The strategy is only viable if extended to -50% AR (10 pips) or higher Tier days. |
| **Execution Risk** | Low. Immediate entry on close = simple execution. But "close of P90 candle" is a look-ahead in live (can only enter on next open). Adds 1 bar of uncertainty. |
| **Architecture Integrity Risk** | Medium. The EWS P90 exit signal is the most commonly misimplemented subsystem. If EWS triggers a reversal entry instead of force-close, the entire session's deficit tracking inverts. |

### VI.2 P90 Cascade (Model A — Momentum Persistence)

| Dimension | Assessment |
|-----------|------------|
| **Predicted WR Range** | 86–90%. Higher than Initial because the macro pathway is already accepted. The field has cleared the first confirmation barrier. |
| **Edge Source** | Momentum persistence. The Cascade P90 proves that the kinetic energy from the initial impulse was not a one-shot event. This is a Resolution Amplifier — the field is actively resolving deficit through sequential atomic steps. The 87.8% WR (per ontology) validates the cascade physics. |
| **Fatal Risk** | Incorrect SL mechanism. The ontology changed the SL from 80% body (Initial) to 168% of new P90 body (Cascade). If the engine uses the 80% body SL for cascades, the SL is too tight for the wider moves cascade captures. But the 168% body SL is unusual: it's 1.68x the body, not the standard 0.8x. This needs verification against the original backtest data. |
| **Execution Risk** | Medium. Cascade requires time-window tracking (within 120 min of previous P90). If the time window is miscalculated (timezone, DST, session boundary), cascade signals are false. |
| **Architecture Integrity Risk** | Low. Cascade is well-specified and the dependency on Initial P90 is clear. No cross-engine coupling. |

### VI.3 P90 Stall-Harvest (Model A — Terminal)

| Dimension | Assessment |
|-----------|------------|
| **Predicted WR Range** | 75–84%. Terminal zone trades have lower WR because the field's energy is depleted. The "reversion" target is the thesis, but overshoot and continuation past Deep State happen. |
| **Edge Source** | Terminal Spatial Coordinate boundary. The 168%–200% extension is a structural wall where kinetic energy converts completely. The Stall-Harvest captures the reversion from this wall. The edge is the geometric certainty that the field will NOT sustain indefinite expansion. |
| **Fatal Risk** | 168% base reference ambiguity (see III.1c). If the Stall Zone coordinate is wrong, the variant triggers on random price levels. Also: this is a MEAN-REVERSION trade at the session's most volatile structural boundary. Missed exits become large losses quickly. |
| **Execution Risk** | Medium-High. The target is "binary expiry or reversion" — a time-constrained reversion. If the reversion is slow (stall oscillation instead of snapback), the trade bleeds time and spread costs. |
| **Architecture Integrity Risk** | Medium. The Stall-Harvest overlaps with the EWS P90 exit signal. If both are active for the same target, the force-close should supersede the stall-harvest entry. This interaction needs explicit sequencing in the code. |

### VI.4 Symmetry Trap Base (Model B — Atomic Structural)

| Dimension | Assessment |
|-----------|------------|
| **Predicted WR Range** | 87–92%. The highest standalone WR because the DZ pullback + OCC validation is the most structurally rigorous entry. The Density Zone ensures friction is cleared before entry. The Zero-Buffer SL is the tightest structural stop. |
| **Edge Source** | Friction clearing and kinetic reloading. The DZ is the mandatory pause mechanics. By waiting for the field to re-enter the Density Zone AND confirm with OCC, the agent enters at the exact coordinate where kinetic energy reloads. The 89% WR (physics baseline) comes from the structural superiority of this entry. |
| **Fatal Risk** | Over-reliance on DZ pullback. In Monolith geometry (cross-pair Direct Causation), the pullback is shallow (<32%) — the field does NOT return to the DZ. The engine must handle this case: either wait for 1 AU micro-pullback OR accept Breakout Continuation. If neither sub-rule is implemented, the engine misses ALL Monolith entries. |
| **Execution Risk** | Medium. DZ pullback takes time to develop. The entry requires patience (OCC confirmation). In live execution, the OCC close-to-next-open delay means the move may have already started before fill. |
| **Architecture Integrity Risk** | Low-Medium. The engine is well-specified as a 4-state FSM. The primary risk is the deficit-tracking gap (II.2d). Without deficit tracking, the engine doesn't know when the macro resolution is complete and will over-trade. |

### VI.5 Dual-Engine Convergence (Both Engines Align)

| Dimension | Assessment |
|-----------|------------|
| **Predicted WR Range** | 92–96%. The Ontology's highest-value scenario. When the P90 validator AND the Symmetry Trap structural filter both confirm the same directional vector, the field has achieved both kinetic validation AND structural acceptance simultaneously. |
| **Edge Source** | Causal hierarchy convergence. P90 (leading indicator) proves kinetic energy is sufficient. Symmetry Trap (lagging confirmation) proves friction has cleared and the field has reloaded. When both fire, the agent has leading + lagging confirmation at the same spatial coordinate. The 94–95% WR (per unified topology) reflects this dual-confirmation premium. |
| **Fatal Risk** | CONFLATION. If the implementation mixes SL protocols (P90 entry + Symmetry Trap SL, or Symmetry Trap entry + P90 SL), the edge disappears. The ontology's cardinal rule: "Crossing the streams mathematically destroys the edge." The convergence signal should use Symmetry Trap entry (per ontology: superior entry price AND superior SL). P90 serves as the confirmation flag, not the entry trigger. |
| **Execution Risk** | Low. The convergence scenario is inherently lower risk because both engines agree. The main execution challenge is identification speed — detecting the convergence in real-time before the OCC passes. |
| **Architecture Integrity Risk** | Medium-High. This is the most architecturally complex scenario. The shared_context data bus must be perfect (both engines see the same Asian Range, same Tier, same AU). If there's any divergence in shared context (timestamp misalignment, rounding differences), the engines will not recognize convergence. |

---

## VII — MANAGER DIRECTIVES

### Pre-Development (Before Writing Code)
1. **Resolve the 168% base reference ambiguity.** Query MAD: is the Stall Zone 168% of Asian Range, 168% of initial impulse, or 168% of cumulative AU displacement? This affects Stall-Harvest P90 AND the Symmetry Trap terminal boundary.
2. **Clarify the Cascade P90 SL.** The pseudo-code says 80% body. The unified topology says 168% of new body. Use the unified topology (more recent, more specific) but flag this for validation.
3. **Define the Distribution Symmetry Trap Is-A relationship.** Is it a parameter of symmetry_trap.py (`target_mode="extended"`) or a separate module? Recommend: parameter, not separate module. Same entry, different TP ladder.

### During Development
4. **Asian Range is the FOUNDATION.** Unit test the Asian Range calculation with 3+ known examples (known Asian ranges for specific dates) before building anything else. If Tier is wrong, everything is wrong.
5. **Engine isolation test.** Run both engines on the same data and verify: (a) they produce independent signals, (b) their SL/TP never mix, (c) the shared_context is read-only during signal evaluation.
6. **Event-decoupled design.** Implement the state machines on events (BandBreakEvent, OCCEvent, KillSwitchEvent) not on bar closes. The bar format is a feed adapter, not part of the engine logic.

### Pre-Backtest
7. **Mandatory spread model.** Every backtest trade must subtract spread from P&L. No exceptions. Use pair-specific spread (EUR/USD: 0.8–1.2 pips; GBP/USD: 1.5–2.5 pips).
8. **Mandatory slippage model.** Entry fills at next bar open (not current close). Exit fills at next bar open for SL (close-only evaluation), current bar for TP (wick evaluation). Document the conservative assumption clearly.
9. **P90 calibration integrity.** P90 threshold must be computed from activation-window M5 candles over a rolling 3-month lookback. Never from the current session's data (look-ahead bias).

### Before Live Deployment
10. **Broker SL/TP support verification.** Confirm the broker supports OCO (one-cancels-other) orders. If not, SL must be managed by the platform — which introduces disconnection risk.
11. **DST transition test.** Run the engine through a known DST transition date. Verify session windows shift correctly.
12. **12 PM stress test.** Force the engine to hold a position at 11:58:00 EST. Verify the 12:00:00 forced exit executes correctly and within 1 bar.

---

## VIII — FINAL VERDICT

**The ontology is architecturally sound.** 55 Q&As across 4 layers provide a complete specification for two engines, a shared data layer, and execution isolation rules. The Bipolar Motor Model (2 engines, not 20 strategies) is the correct architecture.

**The primary reconstruction risks are:**
1. **Temporal alignment** (session windows, DST, timestamp precision) — if this is wrong, everything downstream inherits the error silently
2. **Spread/slippage modeling** — the backtest must subtract real costs or the edge is theoretical only
3. **Deterministic/probabilistic boundary drift** — developers must resist the urge to add "softness" to the hard structural laws
4. **Deficit tracking in cascading loops** — without this, the Symmetry Trap doesn't know when the macro resolution is complete
5. **Engine isolation during convergence** — the highest-value signal scenario is also the highest-architectural-risk scenario

**Confidence Level: 7.5/10.** The ontology provides sufficient specification for implementation. The 2.5-point deduction is for: (a) the 168% base reference ambiguity, (b) the Cascade P90 SL inconsistency between docs, (c) the missing deficit tracking specification in the Symmetry Trap engine, and (d) unspecified intra-bar SL/TP evaluation ordering.

---

*End of IACER Meditation. Manager audit complete. 2026-05-29 18:17 EDT.*
*Next action: Resolve Section VII directives with MAD before code reconstruction proceeds.*
