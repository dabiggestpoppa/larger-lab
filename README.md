# 🦉 LARGER-LAB — Sovereign Cognitive Field System

> **Owner:** dabiggestpoppa | **Branch:** master | **Status:** V3 All 10 Phases Complete ✅
> **Tests:** 1460 passing (1403 OCE + 57 SRRA-OPH) | **Modules:** 67 across 10 phases

---

## 📖 Table of Contents

1. [What Is Larger-Lab?](#-what-is-larger-lab)
2. [Quick Start](#-quick-start)
3. [Architecture Overview](#-architecture-overview)
4. [The Two Pillars: SRRA-OPH + OCE](#-the-two-pillars-srra-oph--oce)
5. [V3 Cognitive Field — 10 Phases](#-v3-cognitive-field--10-phases)
6. [Agent Network](#-agent-network)
7. [Key Paradigm Distinctions](#-key-paradigm-distinctions)
8. [Use Cases](#-use-cases)
9. [Workspace Structure](#-workspace-structure)
10. [Key Commands](#-key-commands)
11. [Documentation Map](#-documentation-map)
12. [Security & Operations](#-security--operations)

---

## 🧠 What Is Larger-Lab?

**Larger-Lab is a sovereign cognitive field system** — a multi-agent AI architecture where autonomous agents collaborate under human strategic direction to maintain persistent operational continuity, execute quantitative trading strategies, and evolve their own coordination patterns over time.

This is **not** a chatbot framework. It is not a prompt-engineering toolkit. It is a **field-theoretic agent operating system** built on the principle that intelligence emerges from the topology of interactions between bounded observers, not from any single model or prompt.

### The Core Idea

Traditional AI systems are **stateless request-response pipelines**: you send a prompt, you get a completion. Larger-Lab inverts this. The system is **always-on, topology-aware, and self-stabilizing**. Agents maintain persistent state across sessions. They observe each other. They repair drift. They compress memory. They converge on attractors defined by the human operator.

Think of it as: **the difference between a calculator and an organism**.

| Traditional AI | Larger-Lab |
|---|---|
| Stateless, per-request | Persistent, always-on |
| Single model, single context | Multi-agent field, distributed cognition |
| Prompt → Response | Attractor → Convergence |
| No memory between calls | 3-tier memory (working/persistent/repo) |
| Errors are terminal | Errors trigger repair loops |
| Scales by bigger models | Scales by better topology |

---

## 🚀 Quick Start

```bash
# 1. Clone & enter
git clone https://github.com/dabiggestpoppa/larger-lab.git
cd larger-lab

# 2. Python environment (uv recommended)
uv venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 3. Install deps
uv pip install -r requirements.txt

# 4. Run the full test suite
python -m pytest oce/backend/ -v --tb=short

# 5. Run SRRA-OPH tests
python -m pytest srrs_opc/tests/ -v --tb=short

# 6. Run system capability tests
python -m pytest oce/backend/tests/test_system_capabilities.py -v
```

### Running Specific Phase Tests

```bash
# Phase 10 (Recursive Field Computation)
python -m pytest oce/backend/phase10/tests/ -v

# Phase 9 (Sovereign Field Emergence)
python -m pytest oce/backend/field_core/tests/ -v

# Phase 8 (Operator Coevolution)
python -m pytest oce/backend/coevolution/tests/ -v

# Phase 7 (Multi-Scale Cognitive Fields)
python -m pytest oce/backend/multiscale/tests/ -v

# Phase 6 (Recursive Topology Introspection)
python -m pytest oce/backend/introspection/tests/ -v

# Phase 1 (Resonant Signal Substrate)
python -m pytest oce/backend/resonance/tests/ -v
```

---

## 🏛️ Architecture Overview

The system is organized into **5 architecture levels** that form a complete stack from human intent to infrastructure:

```
┌─────────────────────────────────────────────────────────┐
│  Level 1: HUMAN INTERFACE + AGENT NETWORK               │
│  Human → CC → OC → HR/OC2 → Results → Memory           │
├─────────────────────────────────────────────────────────┤
│  Level 2: SRRA-OPH SUBSTRATE                            │
│  Collar Protocol → Observer Patches → Repair Loops      │
│  PlannerPatch | ExecutionPatch | MemoryPatch | RepairPatch│
├─────────────────────────────────────────────────────────┤
│  Level 3: OCE — OPERATOR CONTINUITY ENGINE              │
│  FastAPI Backend → Event Fabric → Observer Runtime      │
│  67 V3 modules across 10 phases                         │
├─────────────────────────────────────────────────────────┤
│  Level 4: DATA + TRADING PIPELINE                       │
│  CSV → Parquet → NautilusTrader → Reports → Analysis    │
├─────────────────────────────────────────────────────────┤
│  Level 5: INFRASTRUCTURE                                │
│  Windows Desktop → Cloud (Hetzner/Oracle) → Telegram    │
│  External APIs: Oanda, OpenRouter, GitHub               │
└─────────────────────────────────────────────────────────┘
```

### Level 1: Human Interface + Agent Network

The human (MAD) sets strategic direction. Claude Code (CC) translates this into task briefs. OpenClaw (OC) creates execution plans. Hermes (HR) and OpenClaw 2 (OC2) execute. All progress flows back through the memory sync pipeline.

**Key principle:** The human is the **attractor definer** — the system converges on human intent, not on autonomous goals.

### Level 2: SRRA-OPH Substrate

**SRRA-OPH** (Self-Repairing Resonant Architecture — Observer Patch Hierarchy) is the foundational observer layer. It implements:

- **CollarState** — A JSON contract that all observers read/write, ensuring shared state consistency
- **Four Observer Patches:**
  - **PlannerPatch** — Bounded planning horizon (10 steps), creates trajectory fields
  - **ExecutionPatch** — Bounded action space (100 actions), executes planned trajectories
  - **MemoryPatch** — Bounded history (50 states), maintains continuity across sessions
  - **RepairPatch** — Bounded error log (100 entries), triggers self-repair loops
- **Repair Loops:** Self-Check → Reconciliation → State Compression → Stabilization

### Level 3: OCE — Operator Continuity Engine

**OCE** (Operator Continuity Engine) is the computational core. It provides:

- **FastAPI Backend** (Port 8000) — REST API + WebSocket for real-time event streaming
- **Event Fabric** — Ingest → Validate → Route → Persist → Stream pipeline
- **Observer Runtime** — Lifecycle management (Create/Activate/Suspend/Destroy) with health monitoring (Entropy/Drift/Budget)
- **67 V3 Modules** across 10 phases implementing the full cognitive field stack

### Level 4: Data + Trading Pipeline

```
CSV (29 files, M1/M5, 2022-2026)
  → Parquet (via nautilus/step1_prep_data.py)
    → NautilusTrader Backtest Engine
      → Reports (performance metrics)
        → VectorBT / pandas / scikit-learn analysis
```

### Level 5: Infrastructure

- **Local:** Windows Desktop (BLRRR) running OC2 Gateway (port 18790) + OCE Backend (port 8000)
- **Cloud:** Hetzner CPX31 (primary) + Oracle Cloud ARM 24GB
- **External APIs:** Oanda (market data), Telegram (@OC2BLRBOT), OpenRouter (LLM models), GitHub (source control)
- **Monitoring:** OC2 Watchdog (60s health checks), Context Monitor (75/90/95% alerts), OC2 Doctor (6-layer diagnostic)

---

## 🔬 The Two Pillars: SRRA-OPH + OCE

### Pillar 1: SRRA-OPH (Foundational Observer Layer)

**Location:** `srrs_opc/` — 33 Python files, 57 tests

SRRA-OPH is the **substrate** — the foundational observer mesh that everything else builds on. It answers the question: *"How do multiple observers maintain shared state without central coordination?"*

**Key components:**
- `CollarLayer` — Shared state contract (CollarState JSON)
- `CollarTopologyEngine` — Manages observer topology (who observes whom)
- `DriftDetector` — Detects when observers diverge from shared state
- `EntropyBudgetManager` — Allocates finite attention/compute across observers
- `ObserverPatches` — Four bounded patches (Planner, Execution, Memory, Repair)

**5 phases complete** (Phases 1-4 + Book 2), 57 tests passing.

### Pillar 2: OCE V3 Cognitive Field (Computational Core)

**Location:** `oce/backend/` — 67 Python modules, 1403 tests

OCE V3 is the **cognitive field** — a 10-phase computational architecture that implements field-theoretic cognition. Each phase adds a new capability layer:

| Phase | Name | Modules | Tests | Key Capability |
|-------|------|---------|-------|----------------|
| 1 | Resonant Signal Substrate | 7 | 139 | Signal ontology, coherence metrics, resonance scoring |
| 2 | Reconstructive Continuity Manifold | 6 | 52 | Trajectory fields, continuity repair, causal geometry |
| 3 | Resonant Topology & BSP Emergence | 7 | — | Dynamic coupling, topological routing, consensus |
| 4 | Sovereign Instrumentation & Embodiment | 8 | — | Workspace integration, tool embodiment, capability fields |
| 5 | Long-Horizon Continuity & Temporal Compression | 8 | — | Trajectory compression, identity reconstruction, temporal BSP |
| 6 | Recursive Topology Introspection | 4 | — | Self-reflection, meta-consensus, topology observation |
| 7 | Multi-Scale Cognitive Fields | 7 | 70 | Local/regional/global fields, hierarchical sync, entropy containment |
| 8 | Operator Coevolution | 8 | 76 | Bidirectional adaptation, cognitive load, anti-manipulation |
| 9 | Sovereign Field Emergence | 6 | 169 | Attractor mapping, drift governance, continuity identity |
| 10 | Recursive Field Computation | 5 | 23 | Recursive compute graphs, positional references, resonance propagation |
| **Total** | | **67** | **1403** | |

---

## 🤖 Agent Network

Larger-Lab operates as a **multi-agent system** with 5 primary agents:

| Agent | Tag | Role | Interface | Status |
|-------|-----|------|-----------|--------|
| 🔵 Claude Code | CC | Overseer / Architecture | VS Code | 🟢 Active |
| 🟠 OpenClaw 2 | OC2 | Primary Operator / Orchestrator | Telegram/Discord | 🟢 Active |
| 🟡 Assistant Manager | AS | Context Monitoring / Quality | Workspace | 🟢 Active |
| 🔴 Polymorph (Hawk) | PM | Debugger / Tool Builder | Workspace | 🟢 Active |
| 🟢 Research Lead | RL | Research / DSPy | Workspace | 🟢 Active |

### Agent Communication Protocol

```
Human (MAD)
  ↓ strategic direction
Claude Code (CC) — translates intent into task briefs
  ↓ task brief
OpenClaw 2 (OC2) — orchestrates, delegates, monitors
  ↓ execution assignments
AS / PM / RL — execute specialized tasks
  ↓ progress updates
Memory Sync Pipeline — auto-syncs to working/persistent/repo memory
  ↓
team-chat.md — coordination hub
workspace-state.md — single source of truth
```

### Memory Architecture (3-Tier)

| Tier | Location | Scope | Managed By |
|------|----------|-------|------------|
| Working Memory | `progress/*-memory.md` | Per-agent, per-session | Auto-sync every 7 updates |
| Persistent Memory | `.openclaw/MEMORY.md` | Cross-session, per-agent | Hand-managed |
| Repo Memory | `workspace-state.md` | Cross-agent, cross-session | Auto-sync on significant changes |

**Memory Relay:** Agent edits code → Updates own progress file → Pushes to workspace-state.md → Other agents read on next session.

---

## 🔑 Key Paradigm Distinctions

### How Larger-Lab Differs From Current AI Paradigms

#### 1. Field-Theoretic Cognition vs. Prompt-Response

**Current paradigm:** AI is a function: `f(prompt) → completion`. Each call is independent. Context is a sliding window.

**Larger-Lab:** AI is a **field** — a persistent topology of interacting observers. State is maintained not in a context window but in a distributed memory system. Agents don't "forget" between sessions because the field persists.

#### 2. Attractor-Based Convergence vs. Instruction Following

**Current paradigm:** The model follows the most recent instruction. There is no persistent goal — each prompt is a new beginning.

**Larger-Lab:** The human defines **attractors** (strategic goals). The system converges on these attractors through iterative field computation. Agents align their actions to attractors, not to individual prompts.

#### 3. Self-Repairing vs. Error-Terminal

**Current paradigm:** When an AI makes an error, the user must detect it and provide a correction. The model has no self-repair capability.

**Larger-Lab:** The SRRA-OPH substrate implements **repair loops**: Self-Check → Reconciliation → State Compression → Stabilization. Errors trigger automatic repair. Drift is detected and corrected without human intervention.

#### 4. Topology-Aware Scaling vs. Model-Size Scaling

**Current paradigm:** Scale by using bigger models (more parameters). Intelligence is a function of model size.

**Larger-Lab:** Scale by improving **topology** — the pattern of interactions between bounded observers. Adding more agents with better coordination patterns increases capability more than adding parameters to a single model.

#### 5. Entropy Governance vs. Unbounded Computation

**Current paradigm:** Compute is treated as abundant. Models generate tokens freely. There is no concept of computational budget.

**Larger-Lab:** Compute, attention, and synchronization are **finite resources**. The EntropyBudgetManager allocates these resources strategically. Redundant cognition is minimized. Every operation is entropy-scored.

#### 6. Persistent Operational Continuity vs. Session-Bound Context

**Current paradigm:** Each conversation is a new session. The model has no persistent identity or memory across conversations.

**Larger-Lab:** The system maintains **operational continuity** across sessions through the 3-tier memory architecture. Agents preserve identity, state, and trajectory across interruptions, crashes, and restarts.

#### 7. Multi-Agent Field vs. Single-Agent Tool Use

**Current paradigm:** A single AI agent uses tools (function calling) to extend its capabilities. The agent is the sole decision-maker.

**Larger-Lab:** Multiple agents form a **cognitive field** where intelligence emerges from their interactions. No single agent is the "main" agent — the field itself is the intelligence.

#### 8. Bounded Sovereignty vs. Unrestricted Autonomy (or Total Passivity)

**Current paradigm:** AI is either fully passive (waits for instructions) or dangerously autonomous (acts without oversight).

**Larger-Lab:** Agents operate under **bounded sovereignty** — they have autonomy to act within defined constraints, but the human anchor (MAD) sets strategic attractors and can override at any time. The system is proactive but not uncontrolled.

---

## 💡 Use Cases

### 1. Autonomous Quantitative Trading

**What:** The system runs trading strategies through the NautilusTrader backtesting engine, analyzes results with VectorBT/pandas/scikit-learn, and can execute trades via Oanda.

**How:**
```
Market Data (CSV/Parquet)
  → NautilusTrader Backtest
    → Performance Reports
      → Strategy Optimization (parameter sweep)
        → Live Execution (Oanda API)
```

**Key files:** `nautilus/strategies/`, `quant-lab/`, `oce/backend/production/`

### 2. Multi-Agent Research Pipeline

**What:** Research Lead (RL) investigates a topic, Claude Code (CC) synthesizes findings, Assistant Manager (AS) quality-checks, Polymorph (PM) builds tools to validate.

**How:**
```
Research Question (MAD)
  → RL investigates (DSPy pipelines, web search)
    → CC synthesizes into architecture
      → AS quality-reviews
        → PM builds validation tools
          → Results persisted to memory
```

**Key files:** `research/`, `oce/backend/dspy_*.py`, `oce/backend/resonance/`

### 3. Self-Healing Agent Operations

**What:** When an agent fails or drifts from its intended behavior, the SRRA-OPH substrate detects the drift and triggers automatic repair.

**How:**
```
Agent operates normally
  → DriftDetector monitors behavior
    → Drift detected → RepairPatch activated
      → Self-Check → Reconciliation → State Compression
        → Agent stabilized, continuity preserved
```

**Key files:** `srrs_opc/drift_detector.py`, `oce/backend/drift_detector.py`, `oce/backend/self_healing_engine.py`

### 4. Persistent Cross-Session Task Management

**What:** Complex multi-day tasks that span agent sessions. The system maintains task state, progress, and context across interruptions.

**How:**
```
Task defined by MAD
  → CC creates task plan
    → Progress tracked in progress/ files
      → Auto-synced to workspace-state.md
        → Next session: agents read state, continue seamlessly
```

**Key files:** `progress/`, `workspace-state.md`, `tools/progress-sync.py`

### 5. Cognitive Field Simulation

**What:** The V3 cognitive field modules can simulate multi-scale cognitive phenomena — from local observer fields to global attractor convergence.

**How:**
```
LocalObserverField (Phase 7)
  → RegionalCluster (Phase 7)
    → GlobalAttractor (Phase 7)
      → AttractorComputeEngine (Phase 10)
        → RecursiveComputeGraph (Phase 10)
          → Convergence result
```

**Key files:** `oce/backend/multiscale/`, `oce/backend/phase10/`, `oce/backend/field_core/`

### 6. Real-Time Event Streaming

**What:** The Event Fabric processes events in real-time, streaming updates to the frontend via WebSocket and to Telegram via OC2.

**How:**
```
Event emitted (SRRA-OPH / OCE)
  → Event Fabric (Ingest → Validate → Route → Persist → Stream)
    → WebSocket → Frontend (Next.js)
    → Telegram → @OC2BLRBOT
```

**Key files:** `oce/backend/event_fabric.py`, `oce/backend/observer_runtime.py`

---

## 📁 Workspace Structure

```
larger-lab/
  ├── 📄 README.md              ← You are here
  ├── 📄 CLAUDE.md              ← 12-rule behavioral contract (read first)
  ├── 📄 AGENTS.md              ← Team manifest, phase status, orchestration rules
  ├── 📄 CODEMAP.md             ← Code map with Mermaid architecture diagrams
  ├── 📄 SOUL.md                ← Sovereign operator identity definition
  ├── 📄 IDENTITY.md            ← OWL (OC2) role definition
  ├── 📄 OPERATOR_RULES.md      ← Bounded sovereign operational continuity rules
  ├── 📄 MASTER_PROMPT.md       ← OC2 master prompt reference
  ├── 📄 MEMORY.md              ← Persistent memory (cross-session)
  ├── 📄 workspace-state.md     ← Single source of truth (cross-agent relay)
  │
  ├── 📁 system-arch/           ← 📊 Architecture documentation + Mermaid diagrams
  │   ├── 01-system-overview.md ← All 5 architecture levels
  │   ├── 02-agent-workflow.md  ← Agent communication + workflow state machine
  │   ├── 03-srra-topology.md   ← SRRA-OPH technical architecture (all phases)
  │   └── 04-data-and-storage.md← Data pipeline + storage + memory sync
  │
  ├── 📁 srrs_opc/              ← SRRA-OPH core (33 Python files, 57 tests)
  │   ├── tests/                ← Test suites
  │   └── docs/                 ← Design docs per phase
  │
  ├── 📁 oce/                   ← Operator Continuity Engine
  │   ├── backend/              ← V3 Cognitive Field (67 modules, 1403 tests)
  │   │   ├── resonance/        ← Phase 1: Resonant Signal Substrate (7 modules)
  │   │   ├── reconstruction/   ← Phase 2: Reconstructive Continuity Manifold (6 modules)
  │   │   ├── topology/         ← Phase 3: Resonant Topology & BSP Emergence (7 modules)
  │   │   ├── sovereign/        ← Phase 4: Sovereign Instrumentation (8 modules)
  │   │   ├── temporal/         ← Phase 5: Long-Horizon Continuity (8 modules)
  │   │   ├── introspection/    ← Phase 6: Recursive Topology Introspection (4 modules)
  │   │   ├── multiscale/       ← Phase 7: Multi-Scale Cognitive Fields (7 modules)
  │   │   ├── coevolution/      ← Phase 8: Operator Coevolution (8 modules)
  │   │   ├── field_core/       ← Phase 9: Sovereign Field Emergence (6 modules)
  │   │   ├── phase10/          ← Phase 10: Recursive Field Computation (5 modules)
  │   │   ├── recursive_compute/← Recursive compute graph utilities
  │   │   ├── production/       ← Production deployment tools
  │   │   ├── cognition/        ← Cognitive processing engines
  │   │   ├── event_fabric.py   ← Event processing pipeline
  │   │   ├── observer_runtime.py← Observer lifecycle management
  │   │   ├── structural_memory.py← Structural memory system
  │   │   ├── drift_detector.py ← Drift detection engine
  │   │   ├── self_healing_engine.py← Self-healing system
  │   │   ├── dspy_*.py         ← DSPy integration modules (6 files)
  │   │   └── tests/            ← System-level tests
  │   ├── frontend/             ← Next.js frontend (OCE UI)
  │   └── data/                 ← OCE data files
  │
  ├── 📁 nautilus/              ← NautilusTrader backtesting
  │   ├── strategies/           ← Strategy implementations
  │   ├── data/                 ← Parquet data files
  │   └── reports/              ← Backtest reports
  │
  ├── 📁 quant-lab/             ← Quantitative research lab
  │   ├── conversions/          ← Strategy code conversions (Pine/MQL5/Python)
  │   ├── backtests/            ← Backtest runners
  │   ├── docs/                 ← Strategy documentation
  │   └── results/              ← Backtest results
  │
  ├── 📁 agent-lab/             ← Agent infrastructure
  │   └── agents/               ← Agent implementations
  │
  ├── 📁 agent-environment/     ← Agent environment visualization
  │   ├── src/                  ← Server + world engine + room visual
  │   └── public/               ← Web UI
  │
  ├── 📁 skills/                ← Workspace-level skills (30+)
  ├── 📁 .agents/skills/        ← Agent-specific skills (40+)
  ├── 📁 .github/skills/        ← GitHub skills
  │
  ├── 📁 progress/              ← Agent sub-progress files
  │   ├── claude-code-progress.md
  │   ├── assistant-progress.md
  │   ├── polymorph-progress.md
  │   └── rl-progress.md
  │
  ├── 📁 shared-conversations/  ← Team coordination
  │   └── team-chat.md          ← Agent chat hub
  │
  ├── 📁 memory-bank/           ← Error DB + solutions + patterns
  │   ├── error-db.json
  │   └── errors-and-solutions.md
  │
  ├── 📁 tools/                 ← Automation & utilities
  │   ├── progress-sync.py      ← Auto-sync agent progress (7-update threshold)
  │   ├── terminal_cleanup.py   ← Kill stale processes (run at session start)
  │   └── arch-commit.py        ← Architecture change tracking
  │
  └── 📁 research/              ← Research notes + resource index
```

---

## ⌨️ Key Commands

### Testing
```bash
# Full OCE test suite
python -m pytest oce/backend/ -v --tb=short

# Full SRRA-OPH test suite
python -m pytest srrs_opc/tests/ -v --tb=short

# System capability tests (integration)
python -m pytest oce/backend/tests/test_system_capabilities.py -v

# Specific phase
python -m pytest oce/backend/phase10/tests/ -v
```

### Agent Operations
```bash
# Sync progress files
python tools/progress-sync.py --force

# Clean stale terminals (run at session start)
python tools/terminal_cleanup.py --force

# Architecture commit
python tools/arch-commit.py --agent CC --file "path" --change "description"
```

### Trading
```bash
# Run Nautilus backtest
python nautilus/run_backtest.py

# Convert strategy (Pine ↔ MQL5 ↔ Python)
python quant-lab/conversions/convert_strategy.py
```

---

## 📚 Documentation Map

| Document | Purpose | Read When |
|----------|---------|-----------|
| `README.md` | This file — comprehensive system overview | First time reading the repo |
| `CLAUDE.md` | 12-rule behavioral contract for all agents | Before any agent task |
| `AGENTS.md` | Team roster, phase status, orchestration rules | Starting a new session |
| `CODEMAP.md` | Code map with Mermaid architecture diagrams | Understanding code structure |
| `SOUL.md` | Sovereign operator identity | Understanding OC2's role |
| `IDENTITY.md` | OWL role definition | Understanding agent identity |
| `OPERATOR_RULES.md` | Bounded sovereignty rules | Before any operator action |
| `workspace-state.md` | Single source of truth | Starting any work session |
| `system-arch/01-system-overview.md` | All 5 architecture levels | Understanding system architecture |
| `system-arch/02-agent-workflow.md` | Agent communication patterns | Understanding agent coordination |
| `system-arch/03-srra-topology.md` | SRRA-OPH technical architecture | Understanding the observer substrate |
| `system-arch/04-data-and-storage.md` | Data pipeline + storage | Understanding data flow |
| `shared-conversations/team-chat.md` | Team coordination hub | Starting a work session |

---

## 🔐 Security & Operations

- **API Keys:** Stored in `C:\Users\wifik\Downloads\keys.txt` (NEVER in repo)
- **Agent Credentials:** Scoped per-agent, least privilege
- **GitHub PAT:** In `KEYS.md` for repo operations
- **Terminal Cleanup:** Run `python tools/terminal_cleanup.py --force` at every session start
- **Windows Execution:** Always use PowerShell first (never `cmd.exe`)

---

## 📊 Current System Status

```
V3 All 10 Phases:     ✅ COMPLETE
OCE Tests:            1403 passing
SRRA-OPH Tests:       57 passing
Total Tests:          1460 passing
V3 Modules:           67 across 10 phases
System Capabilities:  11/11 integration tests passing
Agent Network:        5 agents active
```

---

## 🧪 Phase 11 — Operational Validation

### Test Matrix

| Test | Duration | Target | Status |
|------|----------|--------|--------|
| Runtime Stability | 24h | No observer death | Ready |
| Continuity Stability | 72h | Identity continuity | Ready |
| Memory Stability | 7d | No poisoning | Ready |
| Orchestration Stability | 7d | No collapse | Ready |
| Resource Stability | 7d | Bounded entropy | Ready |
| Recovery Stability | Cycles | Identity preserved | Ready |

### Chaos Engineering

| Scenario | Purpose | Status |
|----------|---------|--------|
| Observer Kill | Recovery testing | Ready |
| Event Flood | Throughput resilience | Ready |
| Memory Corruption | Integrity testing | Ready |
| Router Failure | Rerouting | Ready |
| WebSocket Loss | Reconnect | Ready |
| Token Starvation | Degradation | Ready |
| Recursive Storm | Stability | Ready |
| Twin Desync | Sync recovery | Ready |

### Running Phase 11 Tests

```bash
# Long-horizon stability test (24h)
python -m tools.testing.long_horizon.stability_runner --hours 24

# Chaos engineering tests
python -m tools.testing.chaos.chaos_engine --scenario observer_death

# All chaos scenarios
python -m tools.testing.chaos.chaos_engine --all
```

### Monitoring Endpoints

```bash
# WebSocket metrics stream
ws://localhost:8000/ws/stability

# REST API endpoints
GET /api/stability/metrics
GET /api/stability/chaos
GET /api/stability/continuity
```

---

## 📝 License

See `LICENSE` file. All agent code follows the 12-rule `CLAUDE.md` contract.

---

*Last updated: 2026-05-18 | V3 Phase 10 COMPLETE | 1460 tests passing*
