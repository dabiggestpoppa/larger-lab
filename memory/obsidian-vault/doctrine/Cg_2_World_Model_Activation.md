# Cg 2 World Model Activation

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine

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

LINKS:
[[Architecture]]
[[Codemap]]
[[01 System Overview]]
[[02 Agent Workflow]]
[[03 Srra Topology]]
[[04 Data And Storage]]
[[Agents]]
[[Api Reference]]
[[Cg 1 Mermaid Specs]]
[[Cg 1 Revised]]
[[Cg 2 Mermaid Specs]]
[[Cg 3 Openclaw Anchor]]
[[Cg 3 Relational Topology]]
[[Cg 4 Execution Intelligence]]
[[Cg 4 Mermaid Specs]]
[[Cg 5 Continuity Intelligence]]
[[Cg 6 Meta Cognition]]
[[Cg 7 Multi Scale Orchestration]]
[[Cg 8 Operator Coevolution]]
[[Cg 9 Autonomous Strategic Field]]
[[Chaos Scenarios]]
[[Chat Response Bug Diagram]]
[[Cleanup Report]]
[[Code Quality]]
[[Contributing]]
[[Debugging]]
[[Domain Micro Doctrines]]
[[Harness Engineering]]
[[Heartbeat]]
[[Identity]]
[[Master Plan 2026 05 18]]
[[Master Plan Observer Core]]
[[Master Prompt]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[Oce Unified Frontend Plan]]
[[O 6 Implementation Plan]]
[[O 7 Persistent Field Doc]]
[[Phase10]]
[[Phase Breakdown]]
[[Principles]]
[[Project Progress Clean]]
[[Quality Review]]
[[Quality Review Feedback]]
[[Readme]]
[[Soul]]
[[Sub Agent Rules]]
[[Team Tasks]]
[[Telegram Bot Setup]]
[[Testing]]
[[Test Manual]]
[[Tools]]
[[Topological Cognition Architecture]]
[[User]]
[[Workspace State]]
[[Hermes Agent Activation Note]]
[[Cal]]
[[Description]]
[[Expo]]
[[Flat]]
[[Sources]]
[[System]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Memory]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Model Selector]]
