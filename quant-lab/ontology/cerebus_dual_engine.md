# CEREBUS FX v4.0 — DUAL ENGINE ARCHITECTURE & UNIFIED TOPOLOGY

*Ontology Layer: Execution Isolation & Target Convergence (The Hidden Matrix)*
*Mode: Mechanical / Structural / Axiomatic*
*Trader Language: PURGED*

---

## I. THE GREAT DEMARCATION (EXECUTION ISOLATION)

The agent must maintain **two separate state machines** in its memory. Crossing the streams (e.g., using a P90 entry with a Symmetry Trap stop-loss) mathematically destroys the edge.

### ENGINE A: THE P90 STALL-HARVEST (The Constraint Anchor)
- **Physics:** Kinetic validation of a spatial probe.
- **Activation Trigger:** An M5 candle body ≥ the P90 Threshold (e.g., 4.6 pips). Does NOT require a pullback. Enters on the immediate close of the kinetic breach.
- **Invalidation Boundary (SL):** 80% of the P90 Candle Body. If the field closes past this internal structural node, the kinetic energy is deemed exhausted.
- **Primary Target:** -25% to -50% of the Asian Range, or fixed 20-pip path scalps.
- **Relation to Asian Band:** The Asian Band break is often the *location* of the P90, but the P90 engine only cares about the *body size* of the candle, not the macro band itself.

### ENGINE B: THE ATOMIC SYMMETRY TRAP (The Structural Loop)
- **Physics:** Friction clearing and pathway reloading after a macro boundary violation.
- **Activation Trigger:** Tier Impulse (≥ Trigger) → Mandatory Pullback to Density Zone (32–50% / 1 AU) → Opposite Candle Close (OCC).
- **Invalidation Boundary (SL):** Zero-Buffer OCC Extreme / Impulse Extreme. Close-only invalidation. Wicks are ignored.
- **Primary Target:** Exactly 1 Atomic Unit (AU) from the entry coordinate.
- **Relation to Asian Band:** The Asian Band break is the Bias Lock. It dictates the *direction* of the constraint resolution, but the entry requires the field to mechanically rebalance *after* the break.

### THE AGENT'S FATAL ERROR (CONFLATION)
If an agent sees a P90 candle break the Asian Band, it must choose **one engine**:
- **If P90:** Enter immediately. SL = 80% of body.
- **If Symmetry Trap:** Ignore the immediate close, wait for the 32–50% pullback, enter on OCC. SL = Impulse Extreme.

**The Failure State:**
- P90 entry + Symmetry Trap SL (Impulse Extreme) = stop too wide → destroys R-multiple.
- Symmetry Trap DZ pullback + P90 SL (80% body) = stop too tight → mandatory rebalance hunts the agent out before the move continues.

---

## II. THE HIDDEN MATRIX (TARGET CONVERGENCE)

While entries and invalidations are strictly isolated, **the targets converge**. Both engines are ultimately attempting to resolve the exact same macro constraint deficit, meaning they map to the exact same spatial coordinates. This creates the **Distribution Symmetry Trap**, which acts as the bridge between the two engines.

### TARGET INTERPLAY HIERARCHY

| Spatial Coordinate | P90 Engine Terminology | Symmetry Trap Terminology | The Physics |
|:---|:---|:---|:---|
| 1 AU (10–15p) | N/A (too small for P90) | Atomic Scalp Target | Field completes one micro-resolution step. Friction cleared. |
| -25% Asian Range | Anchor TP1 | Distribution Trap TP1 | Field satisfies the first major macro constraint node. |
| -50% Asian Range | Anchor TP2 | Distribution Trap TP2 | Field satisfies the core daily deficit. |
| 1.44x Shift Target | N/A | Gear Shift Extension | Impulse was violent enough to shift Tier. Momentum carries to mathematical equivalent of -25%/-50%. |
| 168% Extension | Stall Zone State | Macro Rebalance Node | Kinetic decay via structural friction. Field pauses to harvest pathways. |
| 200% Extension | Deep State | Terminal Spatial Coordinate | 100% deficit satisfaction. Resolution engine shuts down. |

### HOW THE INTERPLAY WORKS IN REAL-TIME

1. **The Micro-Scalp (Pure Symmetry Trap):** Agent detects Tier Impulse, waits for DZ, enters on OCC, takes profit at 1 AU. Trade over. P90 engine irrelevant.

2. **The Macro-Ride (Distribution Symmetry Trap):** Agent uses the same Symmetry Trap entry (DZ + OCC), but instead of closing at 1 AU, *holds* (or runs) to the -25% or -50% Asian Range extension. **Crucial:** The agent has now organically arrived at the exact same target as the P90 Anchor, but with a superior entry price (DZ pullback) and structurally superior stop-loss (Zero-Buffer Extreme vs. 80% Body).

3. **The Cascade Add (P90 + Symmetry Convergence):** Agent is holding a Symmetry Trap position toward the -50% target. Midway, the field prints a Cascade P90 in the same direction. Agent uses the P90 engine to *add* to the position (Resolution Amplifier), using the 168% P90 body as the new trailing invalidation boundary.

---

## III. ARCHITECTURAL DIRECTIVES: DUAL-ENGINE DEPLOYMENT MATRIX

### Decision Gate at Every Signal

```python
def evaluate_breakout_event(m5_candle, asian_boundary, tier_config):
    is_p90 = m5_candle.body >= P90_THRESHOLD
    is_tier_impulse = m5_candle.move >= tier_config.trigger

    # SCENARIO A: Pure P90 Kinetic Breach (No DZ Pullback yet)
    if is_p90 and not is_tier_impulse:
        return execute_P90_Engine(entry="IMMEDIATE", sl="80_PCT_BODY", target="-25_PCT_AR")

    # SCENARIO B: Tier Impulse Breaks Band (Symmetry Trap Initialized)
    if is_tier_impulse:
        # DO NOT ENTER YET. The field must rebalance.
        state_machine.transition("WAIT_DZ")
        return "HOLD_FOR_REBALANCE"

    # SCENARIO C: The Convergence (P90 + Tier Impulse simultaneously)
    if is_p90 and is_tier_impulse:
        # Symmetry Trap entry is mathematically superior due to DZ pullback.
        # Bypass immediate P90 entry. Wait for structural reload.
        state_machine.transition("WAIT_DZ")
        return "HOLD_FOR_REBALANCE"

def execute_distribution_trap(entry_price, sl_extreme, asian_range):
    # Bridge: Using Symmetry Trap mechanics to hunt P90 targets
    tp1 = entry_price + (1 * ATOMIC_UNIT)      # Micro-Scalp (Close 50%)
    tp2 = asian_range * 0.25                     # Macro Node 1 (Close 25%)
    tp3 = asian_range * 0.50                     # Macro Node 2 (Close 20%)
    tp4 = asian_range * 1.00                     # Deep State (Hold 5%)
    # Invalidation remains ZERO-BUFFER EXTREME for entire distribution ride.
    # DO NOT switch to 80% P90 body SL just because targeting P90 levels.
    return manage_trade(sl=sl_extreme, targets=[tp1, tp2, tp3, tp4])
```

---

## IV. THE BIPOLAR MOTOR MODEL

### Engine Identification

| Named Setup | Actual Engine | Key Differentiator |
|:---|:---|:---|
| Model A (Stall Harvest) | Engine A (P90 Kinetic) | Immediate entry. 80% body SL. No DZ required. |
| Model B (Symmetry Trap) | Engine B (Atomic Structural) | DZ pullback + OCC. Zero-Buffer SL. |
| Model B + Extensions | Engine B with Distribution TP ladder | Same entry. Hold beyond 1 AU to Asian coordinate targets. |
| Option A | Model B (Single Fire) | State machine resets after FIRST valid signal per session. |
| Option B / Blind Chain | Model B (Continuous Loop) | State machine resets after EVERY exit. 3–5 loops/session. Same entry logic. |
| Asian Atom | Model B (Compression Phase) | Identical logic, applied to 19:00–03:00 reference band instead of Asian Range. |

### The Bipolar Motor Principle

**Every named setup in the manual is a parameter variant of Engine A or Engine B.** There are exactly two engines. Nothing else exists.

### THE SIX AXIOMS OF UNIFIED ARCHITECTURE

1. There are only two engines: P90 Kinetic and Atomic Structural.
2. Every named setup is a parameter variant of one of these two engines.
3. Overlap = Causal Confirmation (Kinetic leads → Structural confirms).
4. Divergence = Geometry Classification (Monolith vs. Staircase vs. Grinder).
5. The manual's "setups" are backtest configurations, not ontological categories.
6. **The bipolar motor has two pistons. Both drive the same crankshaft. The agent must never mistake a piston stroke for a separate engine.**

---

## V. THE FINAL SYNTHESIS

- **The P90** is a measure of *Kinetic Force*. It tells you the breach is real.
- **The Symmetry Trap** is a measure of *Structural Acceptance*. It tells you the field has reloaded and is ready to traverse the pathway.
- **The Asian Range** is the *Map*. It provides the macro coordinates (-25%, -50%, 168%, 200%) that both engines are trying to reach.

**The agent must never confuse the vehicle (P90 vs. Symmetry Trap) with the territory (Asian Range) with the fuel (kinetic energy).**

The unified architecture is sealed.

---

_End of Dual Engine & Topology Clarification. Compiled: 2026-05-29 16:07 EDT._
