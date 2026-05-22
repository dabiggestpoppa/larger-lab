# 🧜 All Mermaid Diagrams — SRRA-OPH Project

> Complete collection of all Mermaid diagrams across the workspace.
> Organized by phase and purpose for quick reference.
> **All diagrams render inline on GitHub!**
> **Updated:** 2026-05-18 | Phase 10 Complete | 1460 tests passing

---

## 📁 Structure

```
all-mermaids/
  README.md                    ← You are here
  phase1-5-original/           ← Original Phase 1-5 diagrams (from PROJECT_PROGRESS.md)
  phase1-5-updated/            ← Updated Phase 1-5 diagrams (from CODEMAP.md)
  phase6-9-resources/          ← Phase 6-9 resource diagrams
```

---

## 📊 Phase 1-5 Original (PROJECT_PROGRESS.md)

### System Architecture Overview

```mermaid
graph TB
    subgraph "Human Interface Layer"
        A[Claude Code<br/>VS Code] --> B[OpenClaw<br/>CLI Gateway :18789]
        C[Hermes<br/>Telegram Bot] --> B
    end

    subgraph "Agent Orchestration Layer"
        B --> D[Orchestrator Agent]
        D --> E[Hermes Agent<br/>Execution]
        D --> F[OpenClaw Agent<br/>Analysis]
        D --> G[Memory Engineer<br/>Persistence]
        D --> H[Code Reviewer<br/>Quality Gate]
    end

    subgraph "Data & Strategy Layer"
        I[Downloads/*.csv<br/>29 data files] --> J[nautilus/step1_prep_data.py]
        J --> K[nautilus/data/*.parquet]
        K --> L[Nautilus Trader<br/>Backtest Engine]
        L --> M[nautilus/reports/]
    end

    subgraph "Storage Layer"
        N[Local SSD<br/>Hot Data] --> O[USB Drives<br/>D: & E: 57GB each]
        O --> P[GitHub<br/>Source Control]
        P --> Q[Cloud Storage<br/>Google Drive/MEGA/pCloud]
    end

    subgraph "External Services"
        R[Oanda API<br/>Verification Data] --> L
        S[Hetzner Cloud<br/>Primary Server] --> T[Oracle Cloud<br/>ARM 24GB]
        U[Gmail<br/>Notifications] --> C
    end

    B <--> K
    E <--> L
    F <--> J
    G <--> M
    H <--> M
```

### Agent Communication Flow

```mermaid
sequenceDiagram
    participant H as Human
    participant CC as Claude Code
    participant OC as OpenClaw
    participant HM as Hermes
    participant NT as Nautilus Trader
    participant MEM as Memory Engineer

    H->>CC: Set Direction / Review
    CC->>OC: Task Brief (JSON)
    OC->>HM: Execute Strategy
    HM->>NT: Run Backtest
    NT->>MEM: Store Results
    MEM->>OC: Analysis Report
    OC->>CC: Progress Update
    CC->>H: Status Report
```

### Data Pipeline Flow

```mermaid
flowchart LR
    subgraph "Input"
        A[Downloads/*.csv<br/>29 files<br/>M1/M5 2022-2026]
    end

    subgraph "Processing"
        B[nautilus/step1_prep_data.py<br/>CSV → Parquet]
        C[Data Validation<br/>Schema Check]
        D[Feature Engineering<br/>Asian Range, P90 Signals]
    end

    subgraph "Execution"
        E[Nautilus Trader<br/>Backtest Engine]
        F[Parameter Sweep<br/>Grid/Random Search]
    end

    subgraph "Output"
        G[nautilus/reports/<br/>Performance Metrics]
        H[MEMORY.md<br/>Strategy Results]
        I[GitHub<br/>Version Control]
    end

    A --> B --> C --> D --> E --> F --> G
    G --> H
    H --> I
```

### Backup & Restore Architecture

```mermaid
graph LR
    subgraph "Backup Sources"
        A[larger-lab workspace]
        B[nautilus/data/]
        C[nautilus/reports/]
        D[models/]
        E[backtests/]
    end

    subgraph "Backup Targets"
        F[USB Drive D:<br/>57.3GB]
        G[USB Drive E:<br/>57.3GB]
        H[GitHub<br/>master branch]
        I[Cloud Storage<br/>rclone sync]
    end

    subgraph "Scripts"
        J[backup-workspace.ps1]
        K[restore-workspace.ps1]
        L[quick-setup.ps1]
    end

    A --> J
    B --> J
    C --> J
    D --> J
    E --> J

    J --> F
    J --> G
    J --> H
    J --> I

    K --> A
    L --> A
```

### P90 Strategy Logic Flow

```mermaid
flowchart TD
    A[Market Opens<br/>19:00 EST] --> B[Calculate Asian Range<br/>19:00-03:00 EST]
    B --> C[Range = High - Low]
    C --> D[Set Thresholds<br/>T1=90%, T2=110%, T3=132%]

    D --> E[Signal Window<br/>02:00-11:00 EST]
    E --> F{Price Action}
    F -->|Breaks T1| G[Bull Signal]
    F -->|Breaks -T1| H[Bear Signal]

    G --> I[Position 1 Entry]
    H --> I

    I --> J[45-min Timer]
    J --> K{Price Action}
    K -->|Breaks T2| L[Position 2 Add]
    K -->|Breaks T3| M[Position 3 Add]
    K -->|Pullback -25%| N[Mean Reversion Exit]
    K -->|Time Expiry| O[Close All]

    L --> K
    M --> K
```

### Workflow Protocol State Machine

```mermaid
stateDiagram-v2
    [*] --> TaskReceived
    TaskReceived --> Planning: OpenClaw
    Planning --> Implementation: Hermes
    Implementation --> Verification: Nautilus
    Verification --> Review: Code Reviewer
    Review --> Approved: Quality Gate
    Review --> Rejected: Fix Required
    Rejected --> Implementation
    Approved --> Memory: Memory Engineer
    Memory --> [*]

    state Planning {
        [*] --> ParseBrief
        ParseBrief --> CreatePlan
        CreatePlan --> EstimateEffort
    }

    state Implementation {
        [*] --> ExecuteCode
        ExecuteCode --> RunTests
        RunTests --> CollectResults
    }

    state Verification {
        [*] --> ValidateOutput
        ValidateOutput --> CrossCheck
        CrossCheck --> GenerateReport
    }
```

### File Structure Map

```mermaid
graph TD
    A[larger-lab/] --> B[nautilus/]
    A --> C[usb-cloud/]
    A --> D[agent-lab/]
    A --> E[.hermes/]
    A --> F[models/]
    A --> G[backtests/]
    A --> H[data/]

    B --> B1[strategies/]
    B --> B2[data/]
    B --> B3[reports/]
    B1 --> B1a[symmetry_trap.py]
    B1 --> B1b[ema_cross.py]
    B1 --> B1c[p90_cerebus_v5.py]

    C --> C1[usb-mesh.ps1]
    C --> C2[cloud-server-setup.sh]
    C --> C3[agent-network.md]

    D --> D1[agents/]
    D1 --> D1a[hermes/]
    D1 --> D1b[openclaw/]

    E --> E1[MEMORY.md]
    E --> E2[SOUL.md]
    E --> E3[skills/]

    F --> F1[*.pkl]
    F --> F2[*.onnx]

    G --> G1[*.json]
    G --> G2[*.csv]
```

---

## 📊 Phase 1-5 Updated (CODEMAP.md)

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

---

## 📊 Phase 6-9 Resources

### Full SRRA-OPH Topology

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
```

### Agent Integration Points

| Agent | URL/Config | Skills | Memory |
|-------|------------|--------|--------|
| **OpenClaw Gateway** | `ws://127.0.0.1:18789` | `.hermes/skills/` + `nautilus/` | `.openclaw/MEMORY.md` |
| **Hermes Telegram Bot** | Telegram messages | `.hermes/skills/` | `.hermes/MEMORY.md` |
| **Nautilus Trader** | `nautilus/strategies/` | N/A | `nautilus/reports/` |

---

## 🔄 V3 Cognitive Field — Resonant Signal Substrate (Level 6)

```mermaid
graph TB
    subgraph "Signal Layer"
        SP[SignalPacket<br/>signal_packet.py]
        SF[SignalField<br/>signal_packet.py]
    end

    subgraph "Coherence Layer"
        CM[CoherenceMetrics<br/>coherence_metrics.py]
        CE[CoherenceEngine<br/>coherence_metrics.py]
    end

    subgraph "Field Layer"
        FSM[FieldStateManager<br/>field_state.py]
        BM[BoundaryMapper<br/>boundary_mapper.py]
    end

    subgraph "Resonance Layer"
        RE[ResonanceEngine<br/>resonance_engine.py]
        RO[ResonanceOptimizer<br/>resonance_engine.py]
    end

    subgraph "Pressure Layer"
        PT[PressureTracker<br/>pressure_tracker.py]
    end

    SP --> SF
    SF --> CM
    CM --> CE
    CE --> FSM
    FSM --> BM
    BM --> RE
    RE --> RO
    RO --> PT
```

---

## 🔄 V3 Phase 2 — Reconstructive Continuity Manifold (Level 7)

```mermaid
graph TB
    subgraph "Causal Layer"
        CG[CausalGeometry<br/>causal_geometry.py]
    end

    subgraph "Memory Layer"
        AM[AttractorMemory<br/>attractor_memory.py]
    end

    subgraph "Reconstruction Layer"
        RE[ReconstructionEngine<br/>reconstruction_engine.py]
        OM[OverlapManifold<br/>overlap_manifold.py]
    end

    subgraph "Repair Layer"
        CR[ContinuityRepair<br/>continuity_repair.py]
    end

    CG --> AM
    AM --> RE
    RE --> OM
    OM --> CR
```
