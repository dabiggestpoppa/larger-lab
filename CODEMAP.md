# CODEMAP — Larger-Lab Workspace Guide

> **Last Updated:** 2026-05-16 | **Phase:** 4 (Workspace Integration)
> **Purpose:** Quick orientation for agents joining the workspace. For full architecture, see `SYSTEM_ARCHITECTURE.md`.

---

## Quick Start

```bash
# 1. Clone & enter
git clone https://github.com/dabiggestpoppa/larger-lab.git
cd larger-lab

# 2. Python environment (uv recommended)
uv venv .venv
.venv\Scripts\activate  # Windows

# 3. Install deps
uv pip install -r requirements.txt

# 4. Run all SRRA-OPH tests
python -m srrs_opc.tests.test_phase2_e2e
python -m srrs_opc.tests.test_phase3_e2e
python -m srrs_opc.tests.test_phase4_e2e
```

---

## Workspace Map

```
larger-lab/
  srrs_opc/           ← SRRA-OPH core (25 Python files + tests + docs)
  nautilus/           ← NautilusTrader backtesting (strategies, data, reports)
  agent-lab/agents/   ← Hermes + OpenClaw agent configs
  skills/             ← Workspace skills (srra-oph-build, twitter-bookmarks, etc.)
  .agents/skills/     ← Agent-specific skills (40+ trading, quant, ML, Pine)
  .github/skills/     ← GitHub skills (docx, xlsx, pptx, pdf, etc.)
  progress/           ← Agent sub-progress files (CC/OC/HR/AS/PM)
  all-mermaids/       ← All Mermaid diagrams (phase1-5, phase6-9)
  docs/               ← Documentation, images, phase progress files
  tools/              ← Automation scripts, binaries, workspace files
  shared-conversations/ ← Team chat (team-chat.md)
```

> 📊 **All Mermaid diagrams** have been extracted to `all-mermaids/` for easy reference.

---

## System Architecture Overview

```mermaid
graph TB
    subgraph "Human Interface"
        A[Claude Code<br/>VS Code] --> B[OpenClaw<br/>CLI Gateway :18789]
        C[Hermes<br/>Telegram Bot] --> B
    end

    subgraph "Agent Orchestration"
        B --> D[Orchestrator]
        D --> E[Hermes Agent<br/>Execution]
        D --> F[OpenClaw Agent<br/>Analysis]
        D --> G[Memory Engineer<br/>Persistence]
    end

    subgraph "SRRA-OPH Phase 1"
        H[Collar Layer] --> I[Planner Patch]
        H --> J[Execution Patch]
        H --> K[Memory Patch]
        H --> L[Repair Patch]
    end

    subgraph "Trading Engine"
        M[Nautilus Trader<br/>Backtest Engine]
        N[Strategies<br/>p90, symmetry, ema]
        O[Data<br/>CSV → Parquet]
    end

    B <--> H
    E <--> M
    F <--> O
```

---

## Key Directories

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `srrs_opc/` | SRRA-OPH Phase 1 implementation | `base_patch.py`, `planner_patch.py`, `execution_patch.py`, `memory_patch.py`, `repair_patch.py`, `collar_layer.py` |
| `nautilus/` | Trading strategies & backtests | `strategies/`, `data/`, `reports/` |
| `.hermes/` | Hermes agent configuration | `MEMORY.md`, `SOUL.md`, `skills/` |
| `.openclaw/` | OpenClaw configuration | `openclaw.json`, `openclaw_prompt.md` |
| `usb-cloud/` | Cloud storage mesh | `usb-mesh.ps1`, `cloud-server-setup.sh` |

---

## SRRA-OPH Architecture (Phases 1-5, Book 2 Updated)

### Phase 1: Foundational Observer Mesh ✅
- 4 observer patches (Planner, Execution, Memory, Repair)
- CollarLayer for structured overlap synchronization
- AgentBridge for OpenClaw/Hermes integration
- All patches tested stable (3 cycles, 0 repairs)

### Phase 2: Reconstruction + Recoverability ✅
- **Recovery Anchors** — SQLite-based sparse persistence
- **Drift Detector** — Staleness + weight drift detection
- **Consistency Validator** — Direct/temporal contradiction detection
- **Reconstruction Synthesizer** — Continuity from sparse anchors
- **Contradiction Resolver** — Weight-wins auto-resolution
- **Constraint Propagator** — Event-driven constraint propagation
- 7/7 integration tests passing

### Phase 3: Emergent Topology (Book 2 Updated) 🔄
**Core shift:** Overlap collars are now the continuity engine, not observer nodes.

- **Active Collar Fields** — Edges are active computational reconciliation regions
- **Local Consensus Engines** — Consensus produces stable overlap closure (separate from sync)
- **Overlap Geometry Routing** — Routes through high-reconstruction-efficiency regions
- **Repair-First Continuity** — Repair CREATES continuity (not just supports it)
- **Constraint Resonance Clustering** — Clusters form from overlap compatibility
- **Minimal Stable Realization (MSR)** — min topology for recoverable coherence
- **Entropy-Aware Overlap Scaling** — Sublinear overlap density growth
- 4/4 original tests passing + new overlap-first tests needed

### Phase 4: Workspace Integration (Book 2 Updated) 📋
**Core shift:** Tools become capability fields, not isolated endpoints.

- **Capability Fields** — Distributed execution potentials with entropy/reconstruction profiles
- **Overlap-Aware Tooling** — Execution requires overlap reconciliation
- **Reconstruction-Safe Execution** — Unrecoverable execution is invalid execution
- **Repair-Mediated Orchestration** — Continuous contradiction mediation
- **Entropy-Aware Scheduling** — Optimizes coherence per resource cost
- **Minimal Execution Realization (MER)** — Min execution topology for recoverable outcomes

### Phase 5: Long-Horizon Continuity (Book 2 Updated) 📋
**Core shift:** Identity is reconstructable trajectory, not persistent state.

- **Trajectory Reconstruction Fields** — Continuity from sparse overlap evidence
- **Continuity Collars** — Long-horizon continuity at overlap boundaries
- **Drift-Tolerant Identity** — Probabilistic, directional, constraint-bound
- **Repair-Generated Persistence** — Active repair-driven persistence
- **Temporal Attractor Stabilization** — Soft constraints on reconstruction paths
- **Minimal Continuity Realization (MCR)** — Min continuity structure for recoverability

### Full SRRA-OPH Topology (Phases 1-9, Book 2)

```mermaid
graph TD
    subgraph "Local Observers"
        O1[Observer A]
        O2[Observer B]
        O3[Observer C]
    end

    subgraph "Active Collars (Phase 3)"
        AC1[Active Collar Field]
        AC2[Active Collar Field]
        AC3[Active Collar Field]
    end

    subgraph "Reconstruction (Phase 2+5)"
        TF[Trajectory Fields]
        CC[Continuity Collars]
        RP[Repair-First Continuity]
    end

    subgraph "Capability Fields (Phase 4)"
        CF1[Claude]
        CF2[VSCode]
        CF3[Memory DB]
        CF4[OpenClaw]
    end

    subgraph "Governance (Phase 9)"
        MSR[MSR Optimizer]
        MCR[MCR Optimizer]
        ES[Entropy Scheduler]
    end

    O1 --> AC1
    O2 --> AC1
    O2 --> AC2
    O3 --> AC2

    AC1 --> TF
    AC2 --> CC
    AC3 --> RP

    CF1 --> AC1
    CF2 --> AC2
    CF3 --> AC3
    CF4 --> AC1

    TF --> MSR
    CC --> MCR
    RP --> ES
```

### Usage Example

```python
from srrs_opc import PlannerPatch, ExecutionPatch, MemoryPatch, RepairPatch, CollarLayer

# Create collar layer
collar = CollarLayer()

# Register patches
collar.register_patch(PlannerPatch())
collar.register_patch(ExecutionPatch())
collar.register_patch(MemoryPatch())
collar.register_patch(RepairPatch())

# Run synchronization cycle
results = collar.run_cycle()
```

---

## Agent Integration Points

### OpenClaw Gateway
- **URL:** `ws://127.0.0.1:18789`
- **Config:** `~/.openclaw/openclaw.json`
- **Skills:** `.hermes/skills/` + `nautilus/`

### Hermes Telegram Bot
- **Interface:** Telegram messages
- **Skills:** `.hermes/skills/`
- **Memory:** `.hermes/MEMORY.md`

### Nautilus Trader
- **Strategies:** `nautilus/strategies/`
- **Data:** `nautilus/data/` (parquet format)
- **Reports:** `nautilus/reports/`

---

## Key Reference Files

| File | Purpose |
|------|---------|
| `PROJECT_PROGRESS.md` | Project state & history |
| `SYSTEM_ARCHITECTURE.md` | System constitution |
| `WORKFLOW_PROTOCOL.md` | Task lifecycle |
| `ERROR_CLASSIFICATION.md` | Error handling |
| `TASK_BRIEF_TEMPLATE.json` | Task definition |
| `srrs_opc/README.md` | SRRA-OPH documentation |

---

## Common Tasks

### Run SRRA-OPH Test
```bash
cd srrs_opc
python test_phase1.py
```

### Run Nautilus Backtest
```bash
cd nautilus
python -m nautilus.backtest_runner --strategy p90_cerebus_v5
```

### Sync to USB/Cloud
```bash
.\backup.bat -FullBackup
```

---

## Contact & Coordination

- **Primary Agent:** Claude Code (this session)
- **Analysis Agent:** OpenClaw (CLI gateway)
- **Execution Agent:** Hermes (Telegram bot)
- **Memory Engineer:** Memory Patch (SRRA-OPH)

### System Overview

```mermaid
graph TB
    subgraph "Human Interface"
        H[Human / Board] --> CC[Claude Code<br/>🔵 Overseer]
        H --> OC[OpenClaw<br/>🟣 Analysis]
        H --> HR[Hermes<br/>🟢 Execution]
    end

    subgraph "Progress & Memory Layer"
        PP[progress/<br/>sub-progress files] --> SYNC[progress-sync.py<br/>v2]
        SYNC --> PM[Persistent Memory<br/>.openclaw/MEMORY.md<br/>.hermes/MEMORY.md]
        SYNC --> WM[Working Memory<br/>progress/*-memory.md]
        SYNC --> CM[CODEMAP.md<br/>Auto-updated]
    end

    subgraph "SRRA-OPH Phase 1"
        CL[CollarLayer] --> PP1[PlannerPatch]
        CL --> EP[ExecutionPatch]
        CL --> MP[MemoryPatch]
        CL --> RP[RepairPatch]
        CL --> AB[AgentBridge]
    end

    subgraph "Trading Engine"
        NT[Nautilus Trader<br/>Backtest Engine]
        STR[strategies/<br/>p90, symmetry, ema]
        DATA[data/<br/>CSV → Parquet]
    end

    subgraph "Tools"
        TU[tools/<br/>codemap-updater<br/>progress-sync<br/>task-runner]
    end

    CC --> PP
    OC --> PP
    HR --> PP
    CC --> TU
    HR --> NT
    AB --> OC
    AB --> HR
    DATA --> NT
    STR --> NT
```

### Agent Workflow

```mermaid
flowchart TD
    H[Human gives direction] --> CC[Claude Code<br/>Overseer]

    CC --> |Task Brief| OC[OpenClaw<br/>Analysis & Planning]
    OC --> |Execution Plan| HR[Hermes<br/>Execution]

    HR --> |Backtest| NT[Nautilus Trader]
    NT --> |Results| HR

    HR --> |Progress Update| PP[progress/hermes-progress.md]
    OC --> |Progress Update| PP2[progress/openclaw-progress.md]
    CC --> |Progress Update| PP3[progress/claude-code-progress.md]

    PP --> SYNC[progress-sync.py]
    PP2 --> SYNC
    PP3 --> SYNC

    SYNC --> |Every 3 updates| PPC[PROJECT_PROGRESS_CLEAN.md]
    SYNC --> |Working Memory| WM[progress/*-memory.md]
    SYNC --> |Append Summary| PM[.openclaw/MEMORY.md<br/>.hermes/MEMORY.md]
    SYNC --> |Global State| RM[/memories/repo/workspace-state.md]

    HR --> |Complete| REVIEW{Overseer Review}
    REVIEW --> |Approve| NEXT[Next Phase]
    REVIEW --> |Fix| HR
    NEXT --> |New Task| OC
```

### Data Pipeline

```mermaid
flowchart LR
    subgraph "Input"
        CSV[Downloads/*.csv<br/>29 files M1/M5 2022-2026]
    end

    subgraph "Processing"
        PREP[nautilus/step1_prep_data.py<br/>CSV → Parquet]
        VALID[Data Validation<br/>Schema Check]
    end

    subgraph "Execution"
        NT[Nautilus Trader<br/>Backtest Engine]
        SWEEP[Parameter Sweep<br/>Grid/Random Search]
    end

    subgraph "Output"
        REPORTS[nautilus/reports/<br/>Performance Metrics]
        PROGRESS[progress/<br/>Agent sub-progress files]
        MEMORY[Working Memory<br/>Auto-synced]
    end

    CSV --> PREP --> VALID --> NT --> SWEEP --> REPORTS
    REPORTS --> PROGRESS --> MEMORY
```

### SRRA-OPH Architecture

```mermaid
graph LR
    subgraph "Collar Protocol"
        C1[CollarState<br/>JSON Contract]
    end

    subgraph "Observer Patches"
        PP[PlannerPatch<br/>Bounded Horizon: 10]
        EP[ExecutionPatch<br/>Bounded Actions: 100]
        MP[MemoryPatch<br/>Bounded History: 50]
        RP[RepairPatch<br/>Bounded Log: 100]
    end

    subgraph "Repair Loops"
        SC[Self Check]
        RE[Reconciliation]
        COMP[State Compression]
    end

    PP --> C1
    EP --> C1
    MP --> C1
    RP --> C1

    C1 --> PP
    C1 --> EP
    C1 --> MP
    C1 --> RP

    PP --> SC
    EP --> SC
    MP --> SC
    RP --> SC

    SC -->|Inconsistent| RE
    RE --> COMP
    COMP -->|Stabilized| C1

    style PP fill:#3498db,color:#fff
    style EP fill:#2ecc71,color:#fff
    style MP fill:#9b59b6,color:#fff
    style RP fill:#e74c3c,color:#fff
    style C1 fill:#f39c12,color:#fff
```

### File Structure

```mermaid
graph TD
    ROOT[larger-lab/]

    ROOT --> AGT[agents/]
    ROOT --> NAUT[nautilus/]
    ROOT --> SRRS[srrs_opc/]
    ROOT --> PROG[progress/]
    ROOT --> TOOLS[tools/]
    ROOT --> STRAT[strategies/]

    subgraph "Tools"
        T[tools/]
        T --> codemap-updater[codemap-updater.py]
        T --> github_search[github_search.py]
        T --> phase-gate[phase-gate.py]
        T --> progress-sync[progress-sync.py]
        T --> progress-update-hook[progress-update-hook.py]
        T --> task-runner[task-runner.py]
        T --> workflow-runner[workflow-runner.py]
    end

    subgraph "Progress"
        P[progress/]
        P --> claude-code-memory[claude-code-memory.md]
        P --> claude-code-progress[claude-code-progress.md]
        P --> hermes-memory[hermes-memory.md]
        P --> hermes-progress[hermes-progress.md]
        P --> openclaw-memory[openclaw-memory.md]
        P --> openclaw-progress[openclaw-progress.md]
    end

    ROOT --> DOCS[Documentation]
    DOCS --> CODEMAP[CODEMAP.md]
    DOCS --> WORKFLOW[WORKFLOW_PROTOCOL.md]
    DOCS --> ARCH[SYSTEM_ARCHITECTURE.md]
    DOCS --> PROJ[PROJECT_PROGRESS_CLEAN.md]
```
