# CEREBUS Bipolar Motor — Mermaid Diagrams

## 1. System Overview — One System, Two Engines

```mermaid
graph TB
    A["🧠 ONE SYSTEM<br/>Constraint Resolution"] --> B["⚡ MODEL A<br/>P90 Kinetic Engine"]
    A --> C["🔄 MODEL B<br/>Atomic Structural Engine"]
    B --> D["Same Crankshaft:<br/>Asian Range Deficit"]
    C --> D
    D --> E["🎯 Terminal Targets<br/>-25% AR | -50% AR | 168% | 200%"]
```

## 2. Strategy Collapse Matrix — All 20+ Setups → 2 Engines

```mermaid
graph LR
    subgraph MODEL_A["⚡ MODEL A: P90 Kinetic Engine"]
        A1["Base 80 / Play 1"]
        A2["Cascade P90"]
        A3["Stall-Harvest"]
        A4["EWS (Exit Signal)"]
        A5["45-Min Add (Legacy)"]
    end
    
    subgraph MODEL_B["🔄 MODEL B: Atomic Structural Engine"]
        B1["Atomic Scalp"]
        B2["Symmetry Trap (Distribution)"]
        B3["Option A (Single Fire)"]
        B4["Option B / Blind Chain"]
        B5["Asian Atom"]
    end
    
    A1 & A2 & A3 & A4 & A5 --> PA["P90 Kinetic Protocol<br/>Entry: Immediate Close<br/>SL: 80% Body<br/>Target: -25/-50% AR"]
    B1 & B2 & B3 & B4 & B5 --> PB["Atomic Structural Protocol<br/>Entry: DZ + OCC<br/>SL: Zero-Buffer Extreme<br/>Target: 1 AU → Extended"]
```

## 3. State Machine — Model A (P90 Kinetic)

```mermaid
stateDiagram-v2
    [*] --> SEARCH_A
    SEARCH_A --> P90_PRINT: M5 body ≥ P90 Threshold
    P90_PRINT --> EXECUTE_A: Immediate entry on close
    EXECUTE_A --> TP_A: -25% or -50% AR hit
    EXECUTE_A --> SL_A: 80% body breach (close-only)
    TP_A --> [*]
    SL_A --> [*]
    SEARCH_A --> SEARCH_A: Body < P90 = Elastic (ignore)
```

## 4. State Machine — Model B (Atomic Structural)

```mermaid
stateDiagram-v2
    [*] --> SEARCH_B
    SEARCH_B --> WAIT_DZ: Tier Trigger breached (AU x 1.20)
    WAIT_DZ --> WAIT_OCC: Pullback ≥ 1 AU OR 38.2-50% Fib
    WAIT_DZ --> SEARCH_B: 80% Kill Switch (close-only)
    WAIT_OCC --> IN_TRADE: Opposite Candle Close confirmed
    WAIT_OCC --> SEARCH_B: 80% Kill Switch (close-only)
    IN_TRADE --> TP_B: 1 AU hit (wick or close)
    IN_TRADE --> SL_B: Impulse Extreme breached (close-only)
    TP_B --> SEARCH_B: Continuous loop reset
    SL_B --> SEARCH_B: Continuous loop reset
```

## 5. Dual-Engine Convergence Logic

```mermaid
flowchart TD
    START["New M5 Bar"] --> CHECK{P90 ≥ Threshold?}
    CHECK -->|Yes| TIER{Tier Trigger breached?}
    CHECK -->|No| CHECK2{OCC in DZ?}
    
    TIER -->|Yes| CONVERGENCE["🔱 DUAL ENGINE<br/>Convergence<br/>WR: 94-95%<br/>Size: FULL"]
    TIER -->|No| KINETIC_ONLY["⚡ Kinetic Only<br/>WR: ~83%<br/>Size: STANDARD"]
    
    CHECK2 -->|Yes| STRUCTURAL_ONLY["🔄 Structural Only<br/>WR: ~89%<br/>Size: STANDARD"]
    CHECK2 -->|No| NO_SIGNAL["No Signal"]
    
    CONVERGENCE --> EXECUTE
    KINETIC_ONLY --> EXECUTE
    STRUCTURAL_ONLY --> EXECUTE
    NO_SIGNAL --> START
```

## 6. Target Interplay Hierarchy

```mermaid
graph LR
    subgraph MICRO["Micro (Model B only)"]
        T1["1 AU<br/>10-15 pips"]
    end
    
    subgraph MACRO["Macro (Both Engines)"]
        T2["-25% Asian Range<br/>Anchor TP1 / Dist Trap TP1"]
        T3["-50% Asian Range<br/>Anchor TP2 / Dist Trap TP2"]
    end
    
    subgraph EXTENDED["Extended (Model B Distribution)"]
        T4["1.44x Shift Target<br/>Gear Shift Extension"]
        T5["168% Extension<br/>Stall Zone / Macro Rebalance"]
        T6["200% Extension<br/>Deep State / Terminal Coordinate"]
    end
    
    T1 --> T2 --> T3 --> T4 --> T5 --> T6
```

## 7. Energy Conversion Hierarchy

```mermaid
graph TB
    AR["📦 Asian Range<br/>Potential Energy<br/>(19:00-03:00 EST)"] --> DEFICIT["⚖️ Deficit<br/>Unresolved Displacement"]
    DEFICIT --> TIER["📊 Tier<br/>T1 / T2 / T3<br/>Volatility Quantization"]
    TIER --> AU["⚛️ Atomic Unit<br/>AU = 50% of Centroid<br/>Irreducible Quantum"]
    AU --> P90["💥 P90 Threshold<br/>Kinetic Force Validator<br/>Plastic vs Elastic"]
    P90 --> IMPULSE["🚀 Impulse<br/>Tier Trigger Breach"]
    IMPULSE --> DZ["🔄 Density Zone<br/>32-50% / 1 AU Pullback<br/>Friction Clearing"]
    DZ --> OCC["✅ OCC<br/>Opposite Candle Close<br/>Temporal Acceptance"]
    OCC --> COMPLETION["🏁 Completion<br/>1 AU Traversed<br/>OR 12 PM Hard Exit"]
    COMPLETION --> RESET["↩️ Loop Reset<br/>swing_origin = exit_price"]
    RESET --> AR
```

## 8. Execution Isolation — The Great Demarcation

```mermaid
graph TB
    subgraph ENGINE_A["⚡ ENGINE A: P90 Kinetic"]
        A_ENTRY["Entry: Immediate Close"]
        A_SL["SL: 80% of P90 Body"]
        A_TARGET["Target: -25/-50% AR"]
    end
    
    subgraph ENGINE_B["🔄 ENGINE B: Atomic Structural"]
        B_ENTRY["Entry: DZ Pullback + OCC"]
        B_SL["SL: Zero-Buffer Extreme"]
        B_TARGET["Target: 1 AU → Extended"]
    end
    
    A_ENTRY -.->|❌ NEVER MIX ❌| B_SL
    B_ENTRY -.->|❌ NEVER MIX ❌| A_SL
    A_TARGET --> CONVERGE["🎯 Same Spatial Targets"]
    B_TARGET --> CONVERGE
```

## 9. P90 Fractal Layers

```mermaid
graph LR
    subgraph LAYER1["Layer 1: Initial P90"]
        P1["First Asian Band Breach"]
        P1A["SL: 80% of body"]
        P1B["Sets Direction Bias"]
    end
    
    subgraph LAYER2["Layer 2: Cascade P90"]
        P2["Inside DZ or at AU completion"]
        P2A["SL: 168% of NEW P90 body"]
        P2B["WR: 87.8% (higher than Initial)"]
        P2C["Enables Breakout Continuation entry"]
    end
    
    subgraph LAYER3["Layer 3: EWS P90"]
        P3["Opposite P90 at target"]
        P3A["NOT an entry signal"]
        P3B["Momentum Exhaustion = Force Close"]
    end
    
    P1 --> P2 --> P3
```

## 10. Complete Agent Architecture

```mermaid
graph TB
    DATA["📊 M5 Bar Data"] --> CONTEXT["Shared Context<br/>Asian Range | Tier | Regime | Bias"]
    
    CONTEXT --> ENGINE_A["⚡ Model A<br/>P90KineticEngine.evaluate()"]
    CONTEXT --> ENGINE_B["🔄 Model B<br/>AtomicStructuralEngine.evaluate()"]
    
    ENGINE_A --> SA["Signal A"]
    ENGINE_B --> SB["Signal B"]
    
    SA --> GATE["Convergence Gate"]
    SB --> GATE
    
    GATE --> DUAL["🔱 DualEngineSignal<br/>confidence=MAXIMUM<br/>size=FULL"]
    GATE --> KINETIC["⚡ KineticOnlySignal<br/>confidence=STANDARD"]
    GATE --> STRUCTURAL["🔄 StructuralOnlySignal<br/>confidence=STANDARD"]
    GATE --> NONE["NoSignal"]
    
    DUAL --> EXEC["Execute Trade"]
    KINETIC --> EXEC
    STRUCTURAL --> EXEC
    
    EXEC --> MONITOR["Monitor TP/SL"]
    MONITOR --> RESET["Loop Reset<br/>swing_origin = exit"]
    RESET --> DATA
```

---

_Diagrams created: 2026-05-29 16:35 EDT. For agent ingestion alongside ontology suite._
