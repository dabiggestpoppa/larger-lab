# 🏛️ ARCHITECTURE — Complete System Guide

> **Purpose:** Step-by-step guide to the entire Larger-Lab system. What each part does, how they connect, and why.
> **Audience:** Any agent or developer who needs to understand, modify, or extend the system.
> **Last Updated:** 2026-05-18

---

## Table of Contents

1. [System at a Glance](#1-system-at-a-glance)
2. [The Five Architecture Levels](#2-the-five-architecture-levels)
3. [SRRA-OPH — The Substrate](#3-srra-oph--the-substrate)
4. [OCE V3 — The Cognitive Field](#4-oce-v3--the-cognitive-field)
5. [Agent Network — Who Does What](#5-agent-network--who-does-what)
6. [Memory Architecture — How State Persists](#6-memory-architecture--how-state-persists)
7. [Data Pipeline — From Market Data to Decisions](#7-data-pipeline--from-market-data-to-decisions)
8. [Infrastructure — Where It Runs](#8-infrastructure--where-it-runs)
9. [Testing Architecture — How We Verify](#9-testing-architecture--how-we-verify)
10. [Step-by-Step: How a Task Flows Through the System](#10-step-by-step-how-a-task-flows-through-the-system)

---

## 1. System at a Glance

Larger-Lab is a **sovereign cognitive field system** — a multi-agent architecture where autonomous agents collaborate under human strategic direction.

```
┌─────────────────────────────────────────────────────────────┐
│                      HUMAN (MAD)                             │
│              Strategic Initiator + Attractor Definer         │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                   AGENT NETWORK (Level 1)                    │
│  CC (Overseer) → OC2 (Orchestrator) → AS/PM/RL (Workers)   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                SRRA-OPH SUBSTRATE (Level 2)                  │
│  Collar Protocol → Observer Patches → Repair Loops           │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              OCE V3 COGNITIVE FIELD (Level 3)                │
│  67 modules across 10 phases                                 │
│  Event Fabric → Observer Runtime → Field Core               │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              DATA + TRADING PIPELINE (Level 4)               │
│  CSV → Parquet → NautilusTrader → Reports → Analysis        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                INFRASTRUCTURE (Level 5)                      │
│  Windows Desktop → Cloud → External APIs                     │
└─────────────────────────────────────────────────────────────┘
```

**Key metrics:**
- 1460 tests passing (1403 OCE + 57 SRRA-OPH)
- 67 V3 modules across 10 phases
- 5 active agents
- 11 system capability integration tests

---

## 2. The Five Architecture Levels

### Level 1: Human Interface + Agent Network

**Purpose:** Translate human intent into agent actions.

**Components:**
- **Human (MAD):** Defines strategic attractors (goals). Reviews results. Sets direction.
- **Claude Code (CC):** Translates intent into task briefs. Oversees architecture. Reviews quality.
- **OpenClaw 2 (OC2):** Orchestrates agents. Monitors progress. Reports to MAD via Telegram.
- **AS (Assistant Manager):** Quality review. Context monitoring. Documentation.
- **PM (Polymorph):** Debugging. Tool building. Code quality.
- **RL (Research Lead):** Research. DSPy integration. Alpha generation.

**Communication flow:**
```
MAD → CC → OC2 → AS/PM/RL → Results → Memory Sync → MAD
```

**Key files:** `AGENTS.md`, `shared-conversations/team-chat.md`, `progress/*`

### Level 2: SRRA-OPH Substrate

**Purpose:** Provide the foundational observer layer that maintains shared state across agents.

**Components:**
- **CollarState:** JSON contract for shared state. All observers read/write this.
- **PlannerPatch:** Bounded planning (horizon: 10). Creates trajectory fields.
- **ExecutionPatch:** Bounded actions (limit: 100). Executes planned trajectories.
- **MemoryPatch:** Bounded history (limit: 50). Maintains continuity.
- **RepairPatch:** Bounded error log (limit: 100). Triggers self-repair.
- **CollarTopologyEngine:** Manages who observes whom.
- **DriftDetector:** Detects divergence from shared state.
- **EntropyBudgetManager:** Allocates finite compute/attention.

**Repair loop:**
```
Self-Check → (if inconsistent) Reconciliation → State Compression → Stabilized
```

**Key files:** `srrs_opc/` (33 Python files, 57 tests)

### Level 3: OCE V3 Cognitive Field

**Purpose:** The computational core. 67 modules across 10 phases implementing field-theoretic cognition.

**Core infrastructure:**
- **FastAPI Backend** (`main.py`, `execution_api.py`): REST API + WebSocket on port 8000
- **Event Fabric** (`event_fabric.py`): Ingest → Validate → Route → Persist → Stream
- **Observer Runtime** (`observer_runtime.py`): Lifecycle management + health monitoring
- **Structural Memory** (`structural_memory.py`): Persistent structural state
- **Drift Detector** (`drift_detector.py`): System-level drift detection
- **Self-Healing Engine** (`self_healing_engine.py`): Automatic repair
- **DSPy Integration** (`dspy_*.py`, 6 files): ML pipeline optimization

**V3 Phases (see Section 4 for details):**
- Phase 1: Resonant Signal Substrate (7 modules, 139 tests)
- Phase 2: Reconstructive Continuity Manifold (6 modules, 52 tests)
- Phase 3: Resonant Topology & BSP Emergence (7 modules)
- Phase 4: Sovereign Instrumentation & Embodiment (8 modules)
- Phase 5: Long-Horizon Continuity & Temporal Compression (8 modules)
- Phase 6: Recursive Topology Introspection (4 modules)
- Phase 7: Multi-Scale Cognitive Fields (7 modules, 70 tests)
- Phase 8: Operator Coevolution (8 modules, 76 tests)
- Phase 9: Sovereign Field Emergence (6 modules, 169 tests)
- Phase 10: Recursive Field Computation (5 modules, 23 tests)

**Key files:** `oce/backend/` (67 Python modules, 1403 tests)

### Level 4: Data + Trading Pipeline

**Purpose:** Transform market data into trading decisions.

**Flow:**
```
CSV (29 files, M1/M5, 2022-2026)
  → nautilus/step1_prep_data.py (CSV → Parquet)
    → NautilusTrader Backtest Engine
      → Reports (performance metrics)
        → VectorBT / pandas / scikit-learn analysis
```

**Key files:** `nautilus/`, `quant-lab/`

### Level 5: Infrastructure

**Purpose:** Where the system runs and what external services it uses.

**Components:**
- **Local:** Windows Desktop (BLRRR) — OC2 Gateway (port 18790), OCE Backend (port 8000)
- **Cloud:** Hetzner CPX31 (primary), Oracle Cloud ARM 24GB
- **External APIs:** Oanda (market data), Telegram (@OC2BLRBOT), OpenRouter (LLMs), GitHub
- **Monitoring:** OC2 Watchdog (60s), Context Monitor (75/90/95%), OC2 Doctor (6-layer diagnostic)

---

## 3. SRRA-OPH — The Substrate

### What It Is

SRRA-OPH (Self-Repairing Resonant Architecture — Observer Patch Hierarchy) is the **foundational observer layer**. It answers: *"How do multiple observers maintain shared state without central coordination?"*

### How It Works

1. **CollarState** is the shared JSON contract. All observers read/write it.
2. **Four Patches** manage different aspects:
   - **PlannerPatch** plans trajectories (bounded horizon: 10)
   - **ExecutionPatch** executes actions (bounded: 100)
   - **MemoryPatch** maintains history (bounded: 50)
   - **RepairPatch** manages errors (bounded: 100)
3. **Repair Loops** stabilize the system:
   - Self-Check: Each patch checks its own consistency
   - Reconciliation: Inconsistent patches are reconciled
   - State Compression: Redundant state is compressed
   - Stabilization: System returns to consistent state

### Key Design Decisions

- **Bounded everything:** Every patch has explicit bounds. This prevents unbounded growth and ensures predictable resource usage.
- **Repair-first:** Errors don't halt the system. They trigger repair loops.
- **Sparse synchronization:** Patches don't constantly broadcast. They sync at defined intervals.

### File Map

| File | Purpose |
|------|---------|
| `srrs_opc/collar_layer.py` | CollarState shared contract |
| `srrs_opc/collar_topology_engine.py` | Observer topology management |
| `srrs_opc/drift_detector.py` | Drift detection |
| `srrs_opc/entropy_budget_manager.py` | Resource allocation |
| `srrs_opc/planner_patch.py` | Planning patch |
| `srrs_opc/execution_patch.py` | Execution patch |
| `srrs_opc/memory_patch.py` | Memory patch |
| `srrs_opc/repair_patch.py` | Repair patch |

---

## 4. OCE V3 — The Cognitive Field

### What It Is

OCE V3 (Operator Continuity Engine, Version 3) is the **computational core** — a 10-phase cognitive field architecture that implements field-theoretic cognition.

### Phase-by-Phase Guide

#### Phase 1: Resonant Signal Substrate (RSS)

**Purpose:** Define the signal ontology — how the system perceives and scores signals.

**Modules (7):**
- `signal_packet.py` — SignalPacket + SignalField (34 tests)
- `coherence_metrics.py` — 6 coherence metrics (21 tests)
- `field_state.py` — Field state management (16 tests)
- `boundary_mapper.py` — Boundary detection + pressure mapping (20 tests)
- `resonance_engine.py` — Resonance alignment + scoring (20 tests)
- `pressure_tracker.py` — Entropy pressure monitoring (10 tests)
- `rlp_integration.py` — RL ↔ CC bridge (18 tests)

**Key concept:** Signals are not raw data. They are **resonance-scored packets** that carry information about their coherence with the current field state.

#### Phase 2: Reconstructive Continuity Manifold (RCM)

**Purpose:** Maintain continuity across disruptions. Reconstruct state from partial information.

**Modules (6):**
- `reconstruction_engine.py` — State reconstruction from partial data
- `continuity_repair.py` — Continuity repair mechanisms
- `attractor_memory.py` — Attractor-based memory
- `causal_geometry.py` — Causal relationship mapping
- `overlap_manifold.py` — Overlap detection between states
- `continuity_collar.py` — Continuity collar management

**Key concept:** When the system is disrupted (crash, agent failure, data loss), it can **reconstruct** its state from trajectory fields and attractor memory.

#### Phase 3: Resonant Topology & BSP Emergence

**Purpose:** Dynamic coupling between observers. Topological routing. Distributed consensus.

**Modules (7):**
- `collar_field.py` — Collar field management
- `resonance_router.py` — Resonance-based message routing
- `bsp_projection.py` — BSP (Bounded Spatial Projection)
- `field_pressure.py` — Field pressure monitoring
- `glyph_engine.py` — Glyph-based state encoding
- `attractor_stability.py` — Attractor stability analysis
- `topology_metrics.py` — Topology quality metrics

**Key concept:** Observers are not statically connected. The **topology emerges** from their interactions, and messages are routed based on resonance patterns.

#### Phase 4: Sovereign Instrumentation & Embodiment

**Purpose:** Integrate with the workspace. Tools become extensions of the cognitive field.

**Modules (8):**
- `shell_runtime.py` — Shell execution environment
- `tool_embodiment.py` — Tool embodiment layer
- `executive_router.py` — Executive decision routing
- `model_router.py` — Model selection routing
- `multi_openclaw.py` — Multi-OpenClaw coordination
- `autonomous_loop.py` — Autonomous execution loops
- `compute_economics.py` — Compute cost management
- `continuity_snapshot.py` — Continuity state snapshots

**Key concept:** Tools are not external to the system. They are **embodied** — integrated into the cognitive field as extensions of agent capability.

#### Phase 5: Long-Horizon Continuity & Temporal Compression

**Purpose:** Maintain continuity over long time horizons. Compress temporal data.

**Modules (8):**
- `temporal_trajectory.py` — Temporal trajectory management
- `temporal_compression.py` — Trajectory compression
- `temporal_entropy.py` — Temporal entropy analysis
- `temporal_bsp.py` — Temporal BSP
- `identity_engine.py` — Identity maintenance over time
- `strategic_memory.py` — Strategic memory management
- `glyph_evolution.py` — Glyph evolution over time
- `continuity_collar.py` — Continuity collar (shared with Phase 2)

**Key concept:** Long-running tasks need **temporal compression** — the ability to summarize hours of work into a compact state that can be restored quickly.

#### Phase 6: Recursive Topology Introspection

**Purpose:** The system observes its own topology. Self-reflection. Meta-consensus.

**Modules (4):**
- `topology_observer.py` — Observes the observer topology
- `topology_viz.py` — Topology visualization
- `self_reflection.py` — Self-reflection engine
- `meta_consensus.py` — Meta-level consensus (consensus about consensus)

**Key concept:** The system doesn't just process information — it **observes itself processing information**. This enables self-optimization and self-correction.

#### Phase 7: Multi-Scale Cognitive Fields (MSCF)

**Purpose:** Cognition at multiple scales — local, regional, global. Hierarchical synchronization.

**Modules (7):**
- `local_fields.py` — Local observer fields
- `regional_clusters.py` — Regional clustering
- `global_attractor.py` — Global attractor layer
- `hierarchical_sync.py` — Hierarchical synchronization
- `nested_repair.py` — Nested repair system
- `scale_routing.py` — Scale-adaptive routing
- `entropy_containment.py` — Entropy containment

**Key concept:** Different problems require different scales. Local problems are solved locally. Global problems require global coordination. The system **adapts its scale** to the problem.

#### Phase 8: Operator Coevolution

**Purpose:** The human operator and the system coevolve. Bidirectional adaptation.

**Modules (8):**
- `operator_model.py` — Models the human operator's preferences
- `constraint_model.py` — Models constraints (what the system should NOT do)
- `coherence_reinforcement.py` — Reinforces coherent behavior
- `bidirectional_adaptation.py` — Bidirectional adaptation (system ↔ human)
- `cognitive_load.py` — Monitors cognitive load on the operator
- `alignment_tracking.py` — Tracks alignment between system and operator intent
- `anti_manipulation.py` — Prevents manipulation of the operator
- `coevolution_protocol.py` — Coevolution protocol

**Key concept:** The system doesn't just serve the operator — it **coevolves** with them. It learns their preferences, adapts to their style, and helps them avoid cognitive overload.

#### Phase 9: Sovereign Field Emergence

**Purpose:** The field becomes sovereign — self-governing, self-stabilizing, self-identifying.

**Modules (6):**
- `resonance_engine.py` — Field-level resonance engine
- `recursive_field_nodes.py` — Recursive field node computation
- `attractor_mapper.py` — Attractor mapping and convergence
- `drift_governor.py` — Drift governance and correction
- `reconstruction_core.py` — Core reconstruction engine
- `continuity_identity_engine.py` — Continuity identity management

**Key concept:** The field is not just a collection of agents — it is a **sovereign entity** with its own identity, stability, and governance.

#### Phase 10: Recursive Field Computation

**Purpose:** The field computes recursively — outputs feed back as inputs, enabling convergence.

**Modules (5):**
- `rcg.py` — RecursiveComputeGraph + ComputeNode + StabilizationResult (6 tests)
- `prs.py` — PositionalReferenceSystem + Position + ReferenceFrame (5 tests)
- `rpe.py` — ResonancePropagationEngine + PropagationResult (4 tests)
- `dct.py` — DynamicConstraintTopology + ConstraintEdge + TopologyChange (4 tests)
- `ace.py` — AttractorComputeEngine + AttractorSolution (4 tests)

**Key concept:** The field doesn't just compute once — it **iterates toward convergence**, with each iteration refining the result.

---

## 5. Agent Network — Who Does What

### Agent Roles (Detailed)

#### 🔵 Claude Code (CC) — Overseer / Architecture

**Responsibilities:**
- Translates MAD's strategic intent into task briefs
- Oversees all architecture decisions
- Builds core system modules
- Reviews code quality before merge
- Manages phase gates (what gets built when)

**Does NOT:**
- Execute trading strategies directly
- Debug code (delegates to PM)
- Write documentation (delegates to AS)
- Do research (delegates to RL)

**Key files:** `progress/claude-code-progress.md`, `progress/claude-code-memory.md`

#### 🟠 OpenClaw 2 (OC2) — Orchestrator

**Responsibilities:**
- Orchestrates all agents (assigns tasks, monitors progress)
- Maintains operational continuity across sessions
- Reports to MAD via Telegram
- Monitors system health (watchdog, context monitor)

**Does NOT:**
- Write code directly
- Build modules
- Execute tasks — only delegates

**Key files:** `SOUL.md`, `IDENTITY.md`, `MASTER_PROMPT.md`

#### 🟡 Assistant Manager (AS) — Quality / Context

**Responsibilities:**
- Quality review of all modules
- API documentation
- Context monitoring (ensuring agents have the information they need)
- Integration tests

**Key files:** `progress/assistant-progress.md`, `progress/assistant-memory.md`

#### 🔴 Polymorph / Hawk (PM) — Debugger / Tool Builder

**Responsibilities:**
- Debugging failing tests and modules
- Building development tools
- Code quality analysis
- Performance optimization

**Key files:** `progress/polymorph-progress.md`, `progress/polymorph-memory.md`

#### 🟢 Research Lead (RL) — Research / DSPy

**Responsibilities:**
- Research new techniques and approaches
- DSPy pipeline optimization
- Alpha generation for trading strategies
- Integration of external research

**Key files:** `progress/rl-progress.md`, `research/`

---

## 6. Memory Architecture — How State Persists

### Three-Tier Memory

```
┌─────────────────────────────────────────────────┐
│  TIER 1: Working Memory                          │
│  Location: progress/*-memory.md                  │
│  Scope: Per-agent, per-session                   │
│  Sync: Every 7 updates                           │
│  Content: Recent work, in-progress notes         │
├─────────────────────────────────────────────────┤
│  TIER 2: Persistent Memory                       │
│  Location: .openclaw/MEMORY.md                   │
│  Scope: Cross-session, per-agent                 │
│  Sync: Hand-managed                              │
│  Content: Key insights, patterns, preferences    │
├─────────────────────────────────────────────────┤
│  TIER 3: Repo Memory                             │
│  Location: workspace-state.md                    │
│  Scope: Cross-agent, cross-session               │
│  Sync: On significant changes                    │
│  Content: System state, phase status, blockers   │
└─────────────────────────────────────────────────┘
```

### Memory Relay Protocol

1. Agent edits code
2. Agent updates own progress file (`progress/{agent}-progress.md`)
3. Agent updates own memory file (`progress/{agent}-memory.md`)
4. Every 7 updates: `progress-sync.py` auto-syncs to working → persistent → repo memory
5. Other agents read `workspace-state.md` + `team-chat.md` on next session

### Error Logging

- Any error that takes >2 attempts to fix → logged to `memory-bank/error-db.json`
- Error patterns → compressed into `memory-bank/errors-and-solutions.md`
- Solutions → pushed to repo memory

---

## 7. Data Pipeline — From Market Data to Decisions

### Data Flow

```
Market Data (Oanda API / CSV)
  ↓
CSV Files (29 files, M1/M5, 2022-2026)
  ↓
nautilus/step1_prep_data.py (validation + conversion)
  ↓
Parquet Files (nautilus/data/*.parquet)
  ↓
NautilusTrader Backtest Engine
  ↓
Performance Reports (nautilus/reports/)
  ↓
Analysis (VectorBT / pandas / scikit-learn)
  ↓
Trading Decisions
```

### Strategy Development

1. **Research:** RL researches strategies (DSPy pipelines, academic papers, TradingView)
2. **Implementation:** Strategies converted between Pine Script, MQL5, and Python (`quant-lab/conversions/`)
3. **Backtesting:** NautilusTrader runs backtests with historical data
4. **Analysis:** VectorBT/pandas analyze performance metrics
5. **Optimization:** Parameter sweep (grid/random search)
6. **Deployment:** Production strategies deployed via Oanda API

---

## 8. Infrastructure — Where It Runs

### Local Environment

- **Machine:** Windows Desktop (BLRRR)
- **Python:** 3.11+ (managed by `uv`)
- **Virtual Environment:** `.venv/`
- **Key Services:**
  - OC2 Gateway: `localhost:18790`
  - OCE Backend: `localhost:8000`

### Cloud Environment

- **Hetzner CPX31:** Primary cloud instance
- **Oracle Cloud ARM 24GB:** Secondary/backup

### External Services

| Service | Purpose | Access |
|---------|---------|--------|
| Telegram API | OC2 communication (@OC2BLRBOT) | Bot token |
| Oanda API | Market data + trade execution | API key |
| OpenRouter | LLM model access | API key |
| GitHub | Source control + collaboration | PAT |

### Monitoring

- **OC2 Watchdog:** 60s health checks, auto-restart on failure
- **Context Monitor:** 75%/90%/95% context usage alerts
- **OC2 Doctor:** 6-layer diagnostic (config, network, process, memory, disk, API)

---

## 9. Testing Architecture — How We Verify

### Test Structure

```
oce/backend/
  ├── resonance/tests/         ← Phase 1 tests (139 tests)
  ├── reconstruction/tests/    ← Phase 2 tests (52 tests)
  ├── topology/tests/          ← Phase 3 tests
  ├── sovereign/tests/         ← Phase 4 tests
  ├── temporal/tests/          ← Phase 5 tests
  ├── introspection/tests/     ← Phase 6 tests
  ├── multiscale/tests/        ← Phase 7 tests (70 tests)
  ├── coevolution/tests/       ← Phase 8 tests (76 tests)
  ├── field_core/tests/        ← Phase 9 tests (169 tests)
  ├── phase10/tests/           ← Phase 10 tests (23 tests)
  └── tests/                   ← System-level tests (11 capability tests)

srrs_opc/
  └── tests/                   ← SRRA-OPH tests (57 tests)
```

### Test Categories

1. **Unit Tests:** Test individual modules in isolation. Each module has 4-34 tests.
2. **Integration Tests:** Test how modules work together. Located in `oce/backend/tests/`.
3. **System Capability Tests:** Test end-to-end system behavior. 11 tests covering:
   - Field coherence chain
   - RCG integration
   - PRS integration
   - Memory efficiency (100 nodes)
   - Concurrent operations (5 threads)
   - Error recovery
   - Observer pattern (5 observers)
   - Drift recovery
   - Attractor convergence
   - Compute throughput
   - Memory growth

### Running Tests

```bash
# Everything
python -m pytest oce/backend/ srrs_opc/tests/ -v

# Specific phase
python -m pytest oce/backend/phase10/tests/ -v

# System capabilities only
python -m pytest oce/backend/tests/test_system_capabilities.py -v

# With coverage
python -m pytest oce/backend/ --cov=oce.backend --cov-report=html
```

---

## 10. Step-by-Step: How a Task Flows Through the System

### Example: "Build a new trading strategy"

**Step 1: MAD defines the attractor**
- MAD tells CC: "Build a mean-reversion strategy for EUR/USD"
- This is the **attractor** — the system will converge on this goal

**Step 2: CC creates the task plan**
- CC breaks the attractor into tasks:
  - RL: Research mean-reversion techniques
  - CC: Design the strategy architecture
  - PM: Build the backtesting tool
  - AS: Quality review + documentation

**Step 3: OC2 orchestrates**
- OC2 assigns tasks to agents
- Monitors progress via progress files
- Reports to MAD via Telegram

**Step 4: Agents execute**
- RL researches → writes findings to `research/mean_reversion.md`
- CC designs → writes architecture to `quant-lab/docs/`
- PM builds → writes code to `quant-lab/backtests/`
- AS reviews → writes quality report to `progress/assistant-progress.md`

**Step 5: Memory sync**
- Progress files auto-sync to `workspace-state.md`
- Key findings persist to `.openclaw/MEMORY.md`
- Error patterns log to `memory-bank/error-db.json`

**Step 6: Verification**
- Tests run: `python -m pytest quant-lab/backtests/ -v`
- Backtest runs: `python nautilus/run_backtest.py`
- Results analyzed: VectorBT performance report

**Step 7: MAD reviews**
- CC presents results to MAD
- MAD approves or requests changes
- If approved → strategy deployed to production
- If changes needed → new attractor defined, loop continues

---

*This document is maintained by CC. Last updated: 2026-05-18.*
