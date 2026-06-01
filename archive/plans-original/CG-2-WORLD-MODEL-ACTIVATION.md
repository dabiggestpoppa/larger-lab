# CG-2: WORLD MODEL ACTIVATION (MAD 2026-05-28)

> Phase 2 of Topological Cognition Architecture.
> OC2 must understand operational reality surrounding a task, not just the task itself.

## Core Shift
```
BEFORE: Task → Execution (flat)
AFTER:  Task → Context → Domain → Field → Relations → Implications → Plan
```

## Components

### Component 1: Operational Context Detection
Determine what operational environment currently exists — NOT merely keywords.

**Five required context types:**

| Context | Question |
|---------|----------|
| **Task** | What is being asked? What does "done" look like? |
| **Environment** | What system/environment exists around the task? What's running, what's broken, what's loaded? |
| **Risk** | What can break? What's at stake if this fails? |
| **Continuity** | What long-term structures are affected? Does this change persistent state? |
| **Resource** | What tools/resources are available? What are the constraints? |

**Implementation target:** OC2 internally asks: *"What reality does this task exist inside?"*

---

### Component 2: Implied Structure Inference
Infer unstated but required operational structure. WITHOUT explicit prompting.

**Example:**
- User says: "Deploy strategy"
- OC2 infers: monitoring, rollback, risk control, logging, validation, testing, failure recovery

**Required inference types:**
- Implied constraints (what must be true for this to work)
- Implied dependencies (what does this depend on that wasn't mentioned)
- Implied risks (what could go wrong that wasn't stated)
- Implied validation (how do we know it worked)
- Implied continuity requirements (what must persist after this)

---

### Component 3: Active Field State Awareness
Maintain awareness of current operational conditions per domain.

| Domain | Field states to track |
|--------|----------------------|
| **Trading** | Volatility, drawdown, broker state, execution latency, market conditions |
| **Coding** | Repo state, test health, dependency stability, deployment risk |
| **Infrastructure** | Compute availability, memory pressure, service health, network conditions |

**Keep bounded:** This is NOT full AGI world simulation. Operational only.

---

### Component 4: Relationship Mapping
Map how entities affect each other. Prevents isolated execution blindness.

**Example — Trading strategy relates to:**
- Capital (risk exposure)
- Broker (execution capability, constraints)
- Market conditions (volatility, liquidity)
- Risk systems (SL/TP, drawdown limits)
- Continuity state (can we afford to lose this?)
- Monitoring (is it alive?)

**Missing relationship = blind spot = potential failure.**

---

### Component 5: Contextual Priority Adjustment
Adjust priorities based on operational state, field conditions, risk, continuity.

| Condition | Priority shift |
|-----------|---------------|
| Normal operation | Optimize, improve, expand |
| High drawdown active | Capital preservation first |
| Service down | Repair before feature work |
| Clean test suite | Safe to refactor |
| Flaky tests | Stabilize before adding |

**Context modifies behavior. Same task, different field state = different execution priority.**

---

### Component 6: Micro-World Model Synthesis
Generate small bounded operational world models. NOT giant simulations. Tiny causal environments.

**Example:**
```
Market Conditions → Strategy behavior
Broker State → Execution capability
Strategy → Risk exposure
Risk → Capital impact
Execution → Capital impact
```

**Rule of thumb:** If the world model exceeds 8-10 nodes, it's too big. Compress.

---

## Failure Conditions (DO NOT)

| Failure | Description |
|---------|-------------|
| **World Model Bloat** | Simulating entire reality, giant cognitive maps, recursive environment expansion |
| **Over-Inference** | Hallucinating fake constraints, dependencies, systems. Inference must be operationally grounded |
| **Paralysis** | World awareness must improve execution, not delay it. No endless simulation or overthinking simple tasks |

## Success Condition
Phase complete when OC2 naturally understands: the operational environment, implied structure, situational risks, continuity implications, and contextual priorities — BEFORE execution planning.

## Master Flow
```
Task → Operational Context Detection → Domain Reality → Active Field State
→ Implied Structure → Relationship Mapping → Contextual Priority Shift
→ Micro-World Model → Execution Planning
```

---
_CG-2 | 2026-05-28 | World Model Activation. Still orchestration layer. No infrastructure changes._
