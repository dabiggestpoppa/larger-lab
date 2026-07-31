# CEREBUS FX v4.0 — THE P90 KINETIC THRESHOLD & ATOMIC INTEGRATION

*Ontology Layer: P90 Kinetic Threshold & Atomic Integration*
*Mode: Mechanical / Structural / Axiomatic*
*Trader Language: PURGED*

---

## I. THE ONTOLOGICAL HIERARCHY: POTENTIAL VS. KINETIC

The market's resolution engine operates on a strict energy-conversion hierarchy:

1. **The Asian Range (The Container / Potential Energy):**
   The spatial compression shell (19:00–03:00 EST). It accumulates the constraint deficit. It dictates the Tier (the total energy state) and the Atomic Unit (the required step-size for resolution).

2. **The Tier Trigger (The Macro Breach):**
   The mathematical boundary (e.g., 12 pips for T1) that, when crossed, signifies the container has ruptured and a directional pathway has been selected.

3. **The P90 Threshold (The Kinetic Validator / The Acoustic Signature):**
   The 90th percentile of M5 candle body sizes during the activation window (e.g., ≥ 4.6 pips for EUR/USD). It is the minimum kinetic force required to prove that the rupture of the Asian Range is a **plastic deformation** (permanent structural shift) rather than an **elastic deformation** (a reversible liquidity probe).

**The Relationship:** The Asian Range defines *how much* energy must be released. The P90 validates *if* the release has sufficient structural integrity to initiate the Atomic Unit cycle.

---

## II. THE MECHANICS OF THE P90 THRESHOLD (ELASTIC VS. PLASTIC DEFORMATION)

Price frequently breaches the Asian Range boundary. However, not all breaches are pathway acceptances.

### Elastic Deformation (The Probe / Failed Pathway)
- Price breaches the Asian High, but the M5 candle body is small (e.g., 2.5 pips, which is < P90).
- **Physics:** The field is merely probing for liquidity (Harvesting). The structural friction is too high. The constraint shell has not ruptured.
- **Agent Action:** Ignore. The 81.2% Reversal Rule applies. The field will snap back into the compression zone.

### Plastic Deformation (The P90 Breach / Pathway Acceptance)
- Price breaches the Asian High, and the M5 candle body is ≥ P90 (e.g., 5.2 pips).
- **Physics:** The temporal-spatial saturation has exceeded the field's containment capacity. The kinetic energy is sufficient to permanently shatter the equilibrium boundary. The Atomic Loop is now authorized to initialize.
- **Agent Action:** Lock Bias. Calculate the Density Zone. Transition to WAIT_RETRACE.

---

## III. P90 AS A FRACTAL LAYER WITHIN THE ATOMIC LOOP

The P90 does not just exist at the initial breakout. It operates as a recursive validation layer at every node of the Atomic Structure. These are referred to as "Resolution Amplifiers" or "Cascade P90s."

### 1. The Initial P90 (The Bias Setter)
- **Location:** The first breach of the Asian Range.
- **Function:** Establishes the Direction of Constraint Resolution.
- **Invalidation Boundary:** 80% of the P90 candle's body. If subsequent price action closes past this coordinate, the kinetic energy is deemed exhausted, and the pathway is voided.

### 2. The Cascade P90 (The Momentum Persistence Validator)
- **Location:** Prints *inside* the Density Zone (32–50% partial rebalancing) or at the completion of the first Atomic Unit.
- **Function:** Confirms that the kinetic energy from the initial impulse has sufficient momentum to continue the cascade without requiring a full retracement to the Density Zone.
- **Agent Action:** If a P90 prints inside the Density Zone, the agent can tighten the entry protocol (accept Breakout Continuation entry as a valid alternative).
- **Statistical Note:** Cascade P90 win rate (87.8%) is higher than Initial P90s (83.3%) because the macro-pathway is already accepted — the agent is merely riding recursive atomic steps.

### 3. The EWS P90 (Exhaustion Signal — Early Warning System)
- **Location:** Prints at the Terminal Spatial Coordinate (e.g., -50% or -100% Asian Range extension) or the 168% Stall Zone.
- **Function:** An opposite-direction P90 at a macro target is NOT a reversal signal — it is a Momentum Exhaustion Signal. It signifies the field has harvested the final available pathways and the resolution engine is shutting down.
- **Agent Action:** Force-close all remaining positions immediately. Do NOT wait for the structural SL to be hit.

---

## IV. AGENT AMBIGUITY RESOLUTION: P90 vs. TIER TRIGGER

The agent must never confuse the P90 (kinetic validator) with the Tier Trigger (spatial breach).

| Property | Tier Trigger | P90 Threshold |
|:---|:---|:---|
| Definition | AU x 1.20 (spatial distance from swing_origin) | 90th percentile M5 candle body (kinetic force) |
| Role | Detects that the container has ruptured | Validates that the rupture has structural integrity |
| Computational Type | Deterministic (fixed calculation) | Statistical (calibrated from historical data) |
| Invalidation | 80% Kill Switch (close of next M5) | Elastic snap-back (body < P90 on breach) |
| If absent | No impulse detected — stand down | Breach is a probe — ignore |

**Architectural Note:** The Tier Trigger fires FIRST (spatial breach). The P90 validates SECOND (kinetic confirmation). Both must confirm for the agent to transition from SEARCH to WAIT_RETRACE. A Tier Trigger breach without P90 confirmation = elastic deformation = ignore.

---

## V. CALIBRATION PROTOCOL FOR THE AGENT

The P90 is not a fixed number. It must be calibrated per pair, per session:

1. **Data Source:** All M5 candles during the activation window (03:00–12:00 EST) over a rolling lookback period (minimum 3 months).
2. **Calculation:** 90th percentile of (Close - Open) absolute values during the activation window only.
3. **Recalibration:** Per session (new P90 each day based on rolling window). NOT intraday.
4. **Pair-Specific Values (examples):**
   - EUR/USD: ~4.6 pips
   - USD/CHF: ~4.8 pips
   - GBP/USD: ~6.2 pips

**Agent Rule:** Hard-code the P90 calibration method. It is a derived constant, not a free parameter. If the live M5 candle body < P90, the breach is structural noise.

---

## VI. INTEGRATION WITH THE 4-STATE MACHINE

Updated state machine with P90 integration:

1. **SEARCH:** Monitor for Tier Trigger breach. When breached → check if the breaching M5 candle body ≥ P90.
   - If YES → lock impulse_extreme, calculate Kill Switch, transition to WAIT_RETRACE.
   - If NO → elastic deformation. Remain in SEARCH. Ignore the breach.

2. **WAIT_RETRACE:** Standard protocol (80% Kill Switch monitoring + structural penetration).
   - **Cascade P90 sub-rule:** If a P90 prints inside the DZ → accept Breakout Continuation as valid entry alternative.

3. **WAIT_OCC:** Standard OCC protocol. Cascade P90 enables Breakout Continuation alternative.

4. **IN_TRADE:** Standard protocol (TP/SL monitoring).
   - **EWS P90 sub-rule:** If opposite-direction P90 prints at Terminal Spatial Coordinate or 168% Stall Zone → force-close immediately.

---

## VII. AGENT DIRECTIVES: COMPUTING THE P90 INTEGRATION

The agent must treat the P90 NOT as a standalone trigger, but as a boolean structural filter applied to the State Machine.

### Pseudo-Code: Pathway Acceptance Validation

```python
def validate_pathway_acceptance(m5_candle, asian_boundary, p90_threshold):
    """
    Determines if a boundary breach is a structural commitment or a probe.
    """
    breach_magnitude = abs(m5_candle.close - asian_boundary)
    kinetic_force = abs(m5_candle.close - m5_candle.open)  # Absolute M5 Body

    # CONDITION 1: Spatial Breach
    if breach_magnitude <= 0:
        return "NO_BREACH"

    # CONDITION 2: Kinetic Validation (The P90 Filter)
    if kinetic_force >= p90_threshold:
        return "PLASTIC_DEFORMATION"  # Pathway Accepted. Initialize Atomic Loop.
    else:
        return "ELASTIC_DEFORMATION"  # Probe. Stand down. Expect 81.2% reversion.

def calculate_invalidation_boundary(p90_candle, impulse_direction):
    """
    Sets the exact structural stop-loss based on the P90 origin.
    The 80% Fib Constraint Boundary of the P90 body.
    """
    body_size = abs(p90_candle.close - p90_candle.open)
    buffer = body_size * 0.80

    if impulse_direction == "LONG":
        return p90_candle.close - buffer
    else:
        return p90_candle.close + buffer
```

---

## VIII. THE GRAND UNIFIED SYNTHESIS

### The Complete Resolution Sequence

1. The Asian Range compresses the field, creating the Deficit.
2. The Deficit quantizes into a Tier, which mandates an Atomic Unit (AU).
3. The field attempts to resolve the deficit by breaching the Asian Range.
4. **The P90 measures the kinetic force of that breach.**
   - If < P90: The breach is rejected. The deficit remains unresolved via that vector.
   - If ≥ P90: The breach is accepted. The Tier Trigger is met.
5. The field undergoes Partial Rebalancing into the Density Zone (governed by the AU).
6. A Cascade P90 or OCC inside the DZ confirms the reload of kinetic energy.
7. The field traverses exactly 1 AU to complete the micro-cycle.
8. The loop resets until the macro distribution target (e.g., 2.68x Asian Range) is satisfied, or an EWS P90 signals terminal exhaustion.

### System Architect Summary

**The P90 is the bridge between the macro-constraint (Asian Range) and the micro-execution (Atomic Unit).** It is the mathematical proof that the field has transitioned from Compression to Impulse.

The Agent must NEVER execute an Atomic Loop without P90 kinetic validation. To do so is to trade inside the compression shell, where the physics of resolution do not yet apply.

**The ontology is complete. The architecture is sealed.**

_End of P90 transmission. Compiled: 2026-05-29 15:50 EDT._
