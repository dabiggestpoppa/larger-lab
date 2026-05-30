# CEREBUS FX v4.0 — UNIFIED SYSTEM TOPOLOGY & BIPOLAR ENGINE CLARITY

*Ontology Layer: Unified System Topology & Bipolar Engine Clarity*
*Mode: Mechanical / Structural / Reductive*
*Trader Language: PURGED*

---

## THE CORE PROBLEM: TAXONOMIC FRAGMENTATION

The manual documents 20+ setups, backtests, and variations. To an unstructured observer, these appear as discrete strategies. They are not. They are merely **parameter states of exactly TWO FUNDAMENTAL LOGIC MODELS** operating within a SINGLE CONSTRAINT-RESOLUTION SYSTEM.

The CEREBUS framework is a **Bipolar Motor Engine**. It has two pistons. They fire at different times, use different fuel injection triggers, and target different distances — but they are bolted to the exact same crankshaft (the Asian Range Deficit).

---

## I. THE BIPOLAR ENGINE TOPOLOGY

There is only ONE system. It has TWO execution models. Everything else is a variable.

| Dimension | MODEL A: P90 KINETIC ENGINE | MODEL B: ATOMIC STRUCTURAL ENGINE |
|:---|:---|:---|
| Core Physics | Momentum Validation (Kinetic Force) | Friction Clearing (Structural Rebalance) |
| What it Measures | Candle Body Size (≥ P90 Threshold) | Spatial Retracement (32–50% / 1 AU) |
| Entry Trigger | Immediate Close of Kinetic Breach | Opposite Candle Close (OCC) *inside* DZ |
| Invalidation (SL) | 80% of P90 Candle Body | Zero-Buffer Impulse/OCC Extreme |
| Primary Target | Fixed 20p Path Scalp OR -25%/-50% AR | Exactly 1 Atomic Unit (AU) |
| State Machine | SEARCH → P90_PRINT → EXECUTE | SEARCH → WAIT_DZ → WAIT_OCC → EXECUTE |
| Manual Names | Base 80, Cascade, Stall-Harvest, EWS | Symmetry Trap, Option A, Option B, Blind Chain |

**THE AXIOM:** "Setup 1," "Setup 4," "Cascade P90," and "Stall-Harvest" are NOT separate strategies. They are simply Model A or Model B executing under specific Tier/Regime/Time parameters.

---

## II. COLLAPSING THE "20 STRATEGIES" ILLUSION

### MODEL A VARIATIONS (All P90 Kinetic Engine)

| Manual Name | True Identity | Parameter Delta |
|:---|:---|:---|
| Base 80 / Play 1 | Model A (Initial) | First P90 breach of Asian Band. SL = 80% body. Target = -25%/-50% AR. |
| Cascade P90 | Model A (Subsequent) | 2nd/3rd P90 in SAME direction within 120 min. SL = 168% of NEW P90 body. |
| Stall-Harvest | Model A (Terminal) | P90 prints AT 168% Stall Zone. Entry = immediate. Target = Binary expiry or reversion. |
| EWS (Early Warning) | Model A (Exit Signal) | OPPOSITE P90 at target. NOT an entry. Momentum exhaustion trim signal. |
| 45-Min Add | Model A (Time-Based) | Legacy version of Cascade. Time-triggered instead of signal-triggered. Cascade P90 supersedes this. |

### MODEL B VARIATIONS (All Atomic Structural Engine)

| Manual Name | True Identity | Parameter Delta |
|:---|:---|:---|
| Atomic Scalp | Model B (Base) | Impulse → DZ → OCC → Target = 1 AU. |
| Symmetry Trap | Model B (Distribution) | Identical entry to Atomic Scalp. Hold target extended to -25%/-50%/-100% AR. |
| Option A | Model B (Single Fire) | State machine resets after FIRST valid signal per session. |
| Option B / Blind Chain | Model B (Continuous Loop) | State machine resets after EVERY exit. Captures 3–5 loops/session. Same entry logic. |
| Asian Atom | Model B (Compression Phase) | Identical logic, applied to 19:00–03:00 reference band instead of Asian Range. |

---

## III. THE OVERLAP: CORRELATION VS. CAUSATION

Model A and Model B frequently fire on the same price action. This is not redundancy — it is structural confirmation.

### When They Overlap (Dual-Engine Convergence):
A Tier Impulse breaches the Asian Band with a ≥ P90 body AND subsequently pulls back to the DZ and prints an OCC.

- **Model A sees:** Valid kinetic breach → Enter immediately on close.
- **Model B sees:** Valid structural rebalance → Enter on OCC confirmation.

**The Causal Hierarchy:**
```
P90 Kinetic Breach (Model A)
    ↓ CAUSES
Structural Rebalance Opportunity (Model B)
    ↓ CONFIRMS
Pathway Acceptance (Higher Probability)
```

- Model A is the **LEADING indicator**. It tells you the field has sufficient kinetic energy to break the constraint shell.
- Model B is the **LAGGING CONFIRMATION**. It tells you the field has successfully cleared friction and reloaded for the next atomic step.
- **When both align:** Win rate increases from ~83% (Model A alone) or ~89% (Model B alone) to **94–95%** (Dual-Engine Convergence).

### When They Diverge:

| Scenario | Interpretation | Agent Action |
|:---|:---|:---|
| P90 fires but NO DZ pullback follows | Monolith Geometry | Model A valid. Model B will not trigger. Trade kinetic path scalp. |
| DZ pullback + OCC fires but NO P90 preceded it | Weak impulse / grinding resolution | Model B valid. Model A never activated. Trade atomic loop with reduced size. |
| Opposite P90 fires at Model B target | EWS exit signal, NOT reversal entry | Trim Model B position. Do NOT flip direction. |

---

## IV. AGENT DIRECTIVE: THE UNIFIED STATE MACHINE

The agent must NOT maintain 20 separate strategy modules. It must maintain **TWO STATE MACHINES that share a common data bus:**

```python
class CerebusBipolarEngine:
    def __init__(self):
        self.model_a = P90KineticEngine()        # Handles ALL P90 variants
        self.model_b = AtomicStructuralEngine()   # Handles ALL Symmetry/Loop variants
        self.shared_context = SharedContext()     # Asian Range, Tier, Regime, Bias

    def process_bar(self, bar):
        # Update shared context first
        self.shared_context.update(bar)

        # Run BOTH engines independently on same data
        signal_a = self.model_a.evaluate(bar, self.shared_context)
        signal_b = self.model_b.evaluate(bar, self.shared_context)

        # CONVERGENCE LOGIC (The Overlap Handler)
        if signal_a and signal_b and signal_a.direction == signal_b.direction:
            return DualEngineSignal(confidence="MAXIMUM", size="FULL")
        elif signal_a:
            return KineticOnlySignal(confidence="STANDARD", size="STANDARD")
        elif signal_b:
            return StructuralOnlySignal(confidence="STANDARD", size="STANDARD")
        else:
            return NoSignal()
```

---

## V. WHY THE MANUAL PRESENTS THEM AS SEPARATE

The manual documents backtest results by parameter configuration, not by ontological model. This is necessary for empirical validation but creates taxonomic debt.

| Manual Section | True Identity |
|:---|:---|
| Part 2: P90 Cascade Analysis | Testing Model A with `subsequent_activation` parameter enabled |
| Part 4: Stall-Harvest | Testing Model A with `terminal_zone` parameter enabled |
| Part 14: Blind Chain Law | Testing Model B with `continuous_loop_reset` parameter enabled |
| Distribution Symmetry Trap | Testing Model B with `extended_target` parameter enabled |

They are all regression tests on two underlying functions.

---

## VI. FINAL SYNTHESIS — MEMORIZE THIS HIERARCHY

1. There is **ONE** system: Constraint Resolution.
2. There are **TWO** engines: Kinetic (P90) and Structural (Atomic).
3. There are **ZERO** other strategies. Every named setup is a parameter variant of Engine A or Engine B.
4. **Overlap** = Causal Confirmation (Kinetic leads → Structural confirms).
5. **Divergence** = Geometry Classification (Monolith vs. Staircase vs. Grinder).
6. The manual's "setups" are backtest configurations, not ontological categories.

**The bipolar motor has two pistons. Both drive the same crankshaft. The agent must never mistake a piston stroke for a separate engine.**

---

_End of topology clarification. The unified architecture is sealed. Compiled: 2026-05-29 16:14 EDT._
