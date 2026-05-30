# CEREBUS ONTOLOGY — COMPLETE LOCKED REFERENCE
# ============================================
# Date: 2026-05-29
# Source: MAD Ontology Extraction (Rounds 1-4)
# 
# THIS IS THE SINGLE SOURCE OF TRUTH.
# Every line of code must map to these definitions.
# If code contradicts this, code is wrong.

## CORE THESIS
# "The market is fundamentally a recursive constraint-resolution engine
#  executing quantized spatial geometry to satisfy temporal pressure."

## SINGLE STATE
# Resolution Construction — the ONLY state.
# Compression, Impulse, Rebalance, Completion are NOT states.
# They are recursive expressions/phases of resolution construction.

## TIME WINDOWS (Intrinsically Quantized by Institutional Execution)
# 19:00-03:00 EST: Asian Session — spatial compression engine, deficit accumulation
# 03:00-12:00 EST: Activation Window — temporal release, directional resolution permitted
# 12:00 PM EST: Hard exit — engine termination, full state reset, unresolved deficit TERMINATED

## SECTION 1 — AU MATHEMATICS
#
# AU DERIVATION:
#   1. Calculate Asian Session Range for historical data
#   2. Run K-Means clustering (k=3) on AR distribution → identify 3 volatility centroids
#   3. Tier boundaries = mathematical midpoints between centroids
#   4. AU = Cluster Centroid × 0.50 (exactly 50% of mean AR for that volatility group)
#
# AU IS: The minimum stable structural resolution quantum.
#        The smallest unit of complete constraint resolution the field can execute.
#        NOT a measurement tool — it IS the quantum.
#
# AU INVARIANCE:
#   Default: invariant per session (locked at session start)
#   Gear Shift: If first impulse exceeds NEXT tier's trigger threshold,
#               AU snaps to the shifted tier's AU instantly.
#               Otherwise invariant until 12PM hard reset.
#
# NORTH AMERICAN SESSION TIERS (for reference — asset-specific calibration needed):
#   T1:  AR < ~20p  (smallest compression, lowest AU)
#   T2:  AR ~20-30p (medium)
#   T3:  AR ~30-45p (large)
#   MT25: AR > 45p  (widest — structural coherence may collapse beyond this)
#
# MOVEMENT IS: Quantized structural state transitions. NOT continuous price flow.
# The field MUST snap into a discrete class. No "between" state.

## SECTION 2 — TEMPORAL STRUCTURE
#
# TEMPORAL PRESSURE:
#   Formula: Pressure = Remaining AU Deficit / Time to Hard Exit
#   As time → 0, pressure → ∞
#   Forces: violent resolution (Monolith) OR structural stall if pathways blocked
#
# 12PM HARD EXIT:
#   Engine termination. Full state reset.
#   Deficit does NOT roll forward intraday.
#   All pathways severed. All open positions force-closed.
#   Field returns to default resting state (Compression) until next 19:00 EST.

## SECTION 3 — DEFICIT (Vectorized, NOT Scalar)
#
# DEFINITION:
#   Unresolved directional displacement driven by temporal compression.
#   The exact spatial displacement required to satisfy the temporal pressure of the session.
#
# STRUCTURE: D = {magnitude_pips, direction}
#   magnitude: measured in AU steps from compression shell to tier target
#   direction: +1 (upward resolution) or -1 (downward resolution)
#
# QUANTIFICATION:
#   Deficit = (Tier Target Extension) - (Current Displacement)
#   Measured in Atomic Units (AU count)
#   Total deficit set once at session start from Asian Range
#
# DEFICIT PRESERVATION LAW:
#   The field NEVER abandons a deficit.
#   On pathway failure: magnitude is PRESERVED, direction FLIPS.
#   Deficit is always computed from the COMPRESSION ORIGIN.
#   
#   Pathway failure → pathway reassignment → same magnitude, opposite direction from origin.
#
# SINGLE MACRO DEFICIT PER SESSION:
#   Asian Range defines the single daily constraint deficit.
#   Micro-deficits (AU loops) are fractional resolutions — they SUBTRACT from macro deficit.
#   They do NOT stack, compound, or add.
#   They subdivide until macro deficit reaches zero.

## SECTION 4 — SPATIAL BOUNDARY (Asian Range)
#
# DEFINITION:
#   Equilibrium envelope created by compression phase.
#   The physical limit of the field's capacity to contain accumulated order flow pressure
#   without undergoing a state change.
#
# WHEN INTERNAL PRESSURE EXCEEDS BOUNDARY INTEGRITY → constraint violation (Impulse).

## SECTION 5 — PATHWAY MECHANICS
#
# PATHWAY:
#   An accepted vector chain / resolution geometry.
#   The directional route defined by the initial impulse, validated by OCC,
#   and traversed via sequential AU completions.
#   The physical manifestation of the field harvesting available liquidity to satisfy the deficit.
#
# SINGLE ACTIVE PATHWAY DOMINANCE:
#   The field collapses into exactly one accepted vector chain at a time.
#   Opposing vectors are either: probes (wicks/rejections) or dominant pathway (closes/acceptance).
#   The deficit is constant; direction is merely the selected route.
#   If bullish macro deficit exists but bearish local route is accepted,
#   the field resolves the exact same deficit via the opposite vector.

# FIRST BREAK DEFINITION:
#   Break = M5 CLOSE beyond spatial boundary
#           where close-to-close distance from swing_origin >= trig_pips
#   Wicks alone do not count. The close IS the commitment.
#   NOT: wick penetration, body close, x% penetration, time held.
#   ONLY: M5 close outside boundary + distance >= trig from swing_origin.

## SECTION 6 — IMPULSE
#
# DEFINITION:
#   Boundary violation initiating vector propagation.
#   Triggered when: M5 close beyond compression shell AND distance from swing_origin >= trig.
#
# ON IMPULSE TRIGGER:
#   1. impulse_dir set (+1 bull / -1 bear)
#   2. impulse_extreme = wick extreme (high for bull, low for bear)
#   3. impulse_size measured in pips from swing_origin to extreme
#   4. Kill switch set at 80% of impulse range (from extreme toward origin)
#   5. Fib zone marked (38.2-50% of impulse range — approximate AU overlap)
#   6. Gear shift evaluated (if impulse exceeds next tier trig, reclassify AU)
#   7. Impulse detection arm → transition to REBALANCE (OCC) detection

## SECTION 7 — OCC (Opposite Candle Close) — BINARY ERROR CORRECTION
#
# ONTOLOGICAL STATUS: This is the IRREDUCIBLE ANCHOR of the entire system.
#   Not an entry trigger. Not a candle pattern. Not a confirmation signal.
#   It is STRUCTURAL COHERENCE VALIDATION — binary error correction.
#   The field itself declares whether the pathway stabilized or rejected.
#
# DEFINITION:
#   The first discrete temporal unit (M5 candle) that closes in OPPOSITION
#   to the initiated impulse vector.
#
# MODEL: A — Exhaustion Model
#   OCC confirms the prior impulse vector has EXHAUSTED its immediate pathway.
#   It does NOT predict the next direction.
#   It is the binary filter that strips momentum exhaustion from structural commitment.
#
# MECHANICAL RULE:
#   Bull impulse (impulse_dir=+1): OCC = first M5 candle where close < open (bear candle)
#   Bear impulse (impulse_dir=-1): OCC = first M5 candle where close > open (bull candle)
#   AND: candle shows retracement toward the compression shell
#
# FILTER POWER: Mathematically filters out 66% of false continuations.
#
# ZERO-BUFFER PROTOCOL:
#   The OCC extreme IS the exact structural anchor.
#   Removing buffers INCREASES performance (extra tolerance introduces entropy).
#   The structure is already discretized tightly — exact coordinate matters.
#
# WICKS vs CLOSES (ABSOLUTE LAW):
#   Wicks = probes (reversible, noise, rejected pathways)
#   Closes = commitments (irreversible, accepted pathways)
#
# DISCOVERY VALIDATION (6,814+ loops tested):
#   When stripped to OCC extreme only (zero buffer), R-multiple lifted +83%
#   while maintaining 89-95% accuracy.
#   The OCC extreme is the exact structural anchor where micro-resolution resets.
#   IRREDUCIBLE — cannot be simplified further than close of opposing vector.

## SECTION 8 — ENTRY / TRADE MECHANICS
#
# ENTRY TIMING:
#   Entry = close of the M5 candle AFTER the OCC, in the CONTINUATION direction
#           (same direction as original impulse).
#   The OCC exhausts the pullback. The next impulse-direction close reloads the pathway.
#
# TRADE DIRECTION:
#   Continuation of impulse direction (NOT fade).
#   Bull impulse → OCC (bear candle) → next bull candle close = LONG entry
#   Bear impulse → OCC (bull candle) → next bear candle close = SHORT entry
#
# STOP LOSS:
#   SL = impulse_extreme (ZERO BUFFER, close-only invalidation).
#   If M5 closes beyond impulse_extreme → pathway REJECTED.
#   Not a wick penetration — ONLY a close beyond.
#
# TAKE PROFIT:
#   TP = entry + (AU × impulse_dir)
#   If impulse_dir=+1 (LONG): TP = entry + AU
#   If impulse_dir=-1 (SHORT): TP = entry - AU
#   Target is hit on wick or close.
#
# ENTRY VALIDATION:
#   SL must be BEHIND entry (opposite side from TP direction)
#   TP must be AHEAD of entry (impulse direction)
#   If geometry invalid → skip, reset to SEARCH
#
# RISK:REWARD per trade = 1 AU : entry-to-SL distance
#   (Varies per trade depending on where OCC pullback reached)

## SECTION 9 — PATHWAY ACCEPTANCE / INVALIDATION
#
# ACCEPTANCE (IRREVERSIBLE COMMITMENT):
#   Price closes beyond spatial boundary (M5 close outside Asian band)
#   AND subsequent M5 holds above 80% threshold of impulse leg
#   → probability field collapses → vector LOCKED
#   Engine will NOT revert to compression until deficit = 0 OR 12PM hard exit.
#
# INVALIDATION (80% KILL SWITCH):
#   If ANY M5 candle closes past 80% of the initial impulse leg
#   (measured from impulse_extreme back toward swing_origin):
#   → pathway is MATHEMATICALLY REJECTED
#   → Deficit magnitude preserved, direction flips
#   → New impulse detection begins from new swing_origin at reclassified tier
#
# OCC EXTREME BREACH (also invalidation):
#   If M5 closes beyond the OCC extreme → temporal acceptance voided → pathway rejected.
#
# ON FAILURE — PATHWAY REASSIGNMENT:
#   1. Deficit magnitude preserved (structurally invariant)
#   2. Direction flips (or re-evaluates from origin)
#   3. swing_origin resets to the exit/rejection price
#   4. New impulse detection armed from new origin
#   5. If gear shift applies, AU snaps to new tier
#
# RE-ENTRY AFTER INVALIDATION:
#   After 80% invalidation, it's a NEW pathway. Original vector is DEAD.
#   If price later breaks same direction again = fresh impulse from new swing_origin.
#   NO nested sub-pathways. NO same-pathway restoration.

## SECTION 10 — COMPLETION MECHANICS
#
# COMPLETION LAW (Canonical — one law, no contradictions):
#   completion = (remaining_deficit <= 0) OR (time >= 12:00 PM EST)
#
# Spatial completion: deficit reaches zero (all AU loops satisfied).
# Temporal completion: 12PM hard exit regardless of spatial traversal.
#
# DEEP STATE:
#   = 200% extension of Asian Range from origin.
#   Terminal spatial coordinate — distribution curve terminates here.
#   Field registers 100% deficit satisfaction.
#   Any push beyond without new temporal catalyst = structurally invalid → immediate decay.
#
# STALL ZONE:
#   = 168% extension of Asian Range.
#   Momentum decay via structural friction.
#   NOT reversing — evaluating if sufficient energy exists to push to 200%.
#
# HARVEST:
#   = Pathway Clearing (Kinetic Extraction).
#   Before final AU toward target, field sweeps AGAINST primary vector
#   to extract kinetic energy from trapped participants.
#   Fuels final continuation vector to punch through dense friction.
#
# DEEP STATE OVERSHOOT:
#   Residual momentum + Harvest mechanics.
#   Field sweeps opposing order flow to fuel final kinetic push 
#   before structural wall terminates the move.

## SECTION 11 — REVERSAL MECHANICS
#
# REVERSALS ARE NOT: trend changes, sentiment flips, or "against the move."
# REVERSALS ARE: pathway reassignment during unresolved deficit completion.
#
# The deficit is the CONSTANT. Direction is just the chosen pathway.
# The market NEVER reverses OUT of a deficit — it reverses to find
# a more efficient route to COMPLETE the SAME deficit.
#
# There are NO false moves structurally — only failed pathway acceptances.

## SECTION 12 — OBSERVATION THEORY
#
# TIMEFRAME:
#   Observational compression / resonance layer.
#   Physics are event-driven. M5 is the optimal bucketing for institutional execution cycles.
#   The physics don't change — only the observer's compression artifact changes.
#
# TICKLESS OPERATION:
#   The system operates on event/state transitions only:
#   Compression → Impulse Breach → OCC Validation → Rebalance → AU Completion
#   Ticks are irrelevant noise. Only structural events matter.
#
# CANDLES:
#   Observer compression artifacts — NOT fundamental objects.
#   The fundamental objects are: Impulse, OCC, AU Target.
#   Candles merely slice continuous events into 5-minute temporal buckets.

## SECTION 13 — INFORMATION THEORY
#
# IRREDUCIBLE SET (everything else is derivable):
#   1. Spatial compression shell (Asian Range)
#   2. Temporal pressure (deficit / remaining time)
#   3. Boundary breach (impulse detection)
#   4. Acceptance status (OCC validation)
#   5. Remaining deficit
#
# THIS IS NOT: A trading system.
# THIS IS: A deterministic low-dimensional state-space compression engine.

## SECTION 14 — ENTROPY INJECTION POINTS (Live Degradation Sources)
#   1. Spread / commission
#   2. Broker feed latency
#   3. Tier misclassification (statistical, not deterministic)
#   4. News discontinuities (structural breaks that violate compression model)
#   5. Execution latency
#
# VARIANCE IS NOT: randomness, unknowability, incomplete structure.
# VARIANCE IS: observer residue from applying false assumptions to a deterministic system.
# Our "miss rate" (2-5%) = spread + slippage + news gaps — NOT structural failures.
# If the market were truly random, backtests would show unpatterned failure dispersion.
# Instead: recurring failure geometries, recurring invalidation structures.

## SECTION 15 — AGENT ARCHITECTURE (Deterministic, NOT Predictive)
#
# THE AGENT IS NOT: a predictive model, AI intuition, LLM reasoning, or directional predictor.
# THE AGENT IS: a reactive deterministic compression engine — a recursive deficit-resolution tracker.
#
# EDGE SOURCE: Deterministic resolution physics — NOT forecasting.

## MINIMAL VIABLE ENGINE (4 Components):
#
# 1. DEFICIT CALCULATOR
#    Input: Asian Range (19:00-03:00) 
#    Process: K-Means clustering → Tier classification → AU computation
#    Output: Base tier, AU value, total deficit in AU steps, tier target coordinate
#
# 2. IMPULSE & 80% TRACKER
#    Input: M5 stream, deficit calculator output
#    Process: Detect boundary breach (close outside band, distance >= trig)
#             Set impulse_extreme, kill_switch (80%), fib zone
#             Evaluate gear shift
#    Output: impulse_dir, impulse_extreme, kill_switch, gear_shift state
#
# 3. OCC STATE MACHINE
#    Input: impulse_dir, M5 stream, kill_switch
#    States: SEARCH → WAIT_OPP → IN_TRADE → (reset)
#    Process: Detect OCC (first opposite close after impulse)
#             Validate: kill switch not hit
#    Output: OCC confirmation, OCC extreme (zero-buffer anchor)
#
# 4. EXECUTION & RESET ENGINE
#    Input: entry price, SL, TP, M5 stream
#    Process: Enter on post-OCC continuation close
#             Monitor: SL (close beyond impulse_extreme) | TP (wick or close at AU target)
#             On exit: reset swing_origin to exit price, decrement deficit, loop
#    Hard exit: 12PM — force close, terminate all pathways

## MINIMAL AGENT STATE VECTOR (6 variables — all the agent needs at all times):
#   1. Base Tier & AU
#   2. Current Deficit (distance remaining to Tier Target)
#   3. Active Pathway Direction (Bias Lock from first band break)
#   4. Impulse Extreme & 80% Kill Zone
#   5. Temporal Pressure (time remaining to 12PM)
#   6. Acceptance Status (has OCC validated the current vector?)
#
# Everything else (volume, indicators, macro news, order flow) = structurally irrelevant noise.

## HARD DETERMINISTIC CONSTRAINTS (NEVER probabilistic):
#   - Asian Range calculation & K-Means Tier classification
#   - 80% Close Invalidation Rule
#   - 12:00 PM EST Hard Temporal Exit
#   - Zero-Buffer OCC Extreme (SL)
#   - AU Target (50% of Centroid)
#
# These are binary structural laws. No confidence intervals. True or false.
# Probabilistic weighting here = fatal architecture drift.

## PROBABILISTIC PATHWAY VARIABLES (require statistical weighting):
#   - Regime confirmation (9AM checkpoint boost)
#   - Pathway selection (which direction breaks the band first)
#   - Exact duration of Rebalance phase (Goldilocks zone timing)
#   - Gear Shift activation likelihood
#
# These are pathway variables within valid solution space — NOT structural laws.
