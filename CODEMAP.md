# 🗺️ CODEMAP — Unified System Architecture

> **Purpose:** Complete workspace orientation with all Mermaid diagrams in one place.
> **Updated:** 2026-05-17
> **For:** Quick reference, architecture alignment, pipeline verification.

---

## 🏛️ Unified System Overview

```mermaid
graph TB
    subgraph "Level 1: Human Interface"
        H[Human / Board]
        CC[Claude Code<br/>🔵 Overseer]
        OC[OpenClaw<br/>🟣 Analysis]
        HR[Hermes<br/>🟢 Execution]
        OC2[OpenClaw 2<br/>🟠 Telegram]
    end

    subgraph "Level 2: SRRA-OPH Substrate"
        C1[Collar Protocol]
        PP[PlannerPatch]
        EP[ExecutionPatch]
        MP[MemoryPatch]
        RP[RepairPatch]
        AC[Active Collars]
        TF[Trajectory Fields]
    end

    subgraph "Level 3: OCE Engine"
        API[FastAPI Backend<br/>Port 8000]
        EF[Event Fabric]
        OR[Observer Runtime]
        UI[Next.js Frontend]
    end

    subgraph "Level 4: Data Pipeline"
        CSV[Downloads/*.csv]
        NT[Nautilus Trader]
        REPORTS[Reports]
    end

    subgraph "Level 5: Infrastructure"
        WIN[Windows Desktop]
        CLOUD[Hetzner/Oracle Cloud]
        TG[Telegram API]
        OPENROUTER[OpenRouter LLMs]
    end

    H --> CC
    CC --> OC
    OC --> HR
    HR --> OC2
    OC2 --> TG

    CC --> C1
    OC --> C1
    HR --> C1
    C1 --> PP
    C1 --> EP
    C1 --> MP
    C1 --> RP
    PP --> AC
    EP --> AC
    MP --> AC
    RP --> AC
    AC --> TF

    TF --> EF
    EF --> OR
    OR --> API
    API --> UI
    API --> EF

    CSV --> NT
    NT --> REPORTS
    REPORTS --> TF

    WIN --> OC2
    WIN --> API
    API --> OPENROUTER
    WIN --> CLOUD
```

---

## 📊 Architecture Levels

### Level 1: Human Interface + Agent Network

```mermaid
graph TB
    subgraph "Human Interface"
        H[Human / Board] --> CC[Claude Code<br/>🔵 Overseer / Architecture]
        H --> OC[OpenClaw<br/>🟣 Analysis / Planning]
        H --> HR[Hermes<br/>🟢 Execution / Telegram]
    end

    subgraph "Agent Coordination"
        CC --> |Task Brief| OC
        OC --> |Execution Plan| HR
        HR --> |Progress| PP[progress/ files]
        CC --> |Progress| PP
        OC --> |Progress| PP
    end

    subgraph "Memory & Sync Layer"
        PP --> SYNC[progress-sync.py]
        SYNC --> WM[Working Memory<br/>progress/*-memory.md]
        SYNC --> PM[Persistent Memory<br/>.openclaw/MEMORY.md]
        SYNC --> RM[Repo Memory<br/>workspace-state.md]
        SYNC --> CM[CODEMAP.md]
    end

    subgraph "OC2 Gateway"
        OC2[OpenClaw 2<br/>Port 18790] --> TG[Telegram @OC2BLRBOT]
        OC2 --> WD[Watchdog<br/>Auto-restart]
        OC2 --> CM2[Context Monitor<br/>75%/90%/95% alerts]
    end

    CC --> OC2
    OC --> OC2
    HR --> OC2
```

### Level 2: SRRA-OPH Substrate (Phases 1-9)

```mermaid
graph TD
    subgraph "Phase 1: Observer Mesh"
        O1[Observer A]
        O2[Observer B]
        O3[Observer C]
        C1[CollarState]
        PP[PlannerPatch]
        EP[ExecutionPatch]
        MP[MemoryPatch]
        RP[RepairPatch]
    end

    subgraph "Phase 2: Reconstruction"
        TF[Trajectory Fields]
        CC[Continuity Collars]
        RP2[Repair-First Continuity]
    end

    subgraph "Phase 3: Emergent Topology"
        DC[Dynamic Coupling]
        TR[Topological Router]
        DCON[Distributed Consensus]
        ACF[Active Collar Fields]
    end

    subgraph "Phase 4: Workspace Integration"
        CF1[Claude]
        CF2[VSCode]
        CF3[Memory DB]
        CF4[OpenClaw]
        WT[Workspace Tools]
    end

    subgraph "Phase 5: Long-Horizon Continuity"
        TC[Trajectory Compression]
        ID[Identity Reconstruction]
    end

    subgraph "Phase 6-9: Advanced"
        RT[Topology Observer]
        OC6[Overlap Cognition]
        SC[Sovereign Coevolution]
        EB[Entropy Budget]
    end

    O1 --> C1
    O2 --> C1
    O3 --> C1
    PP --> C1
    EP --> C1
    MP --> C1
    RP --> C1
    C1 --> PP
    C1 --> EP
    C1 --> MP
    C1 --> RP

    C1 --> TF
    TF --> CC
    TF --> RP2

    O1 --> DC
    O2 --> DC
    O3 --> DC
    DC --> TR
    TR --> DCON
    DCON --> ACF
    ACF --> DC

    CF1 --> WT
    CF2 --> WT
    CF3 --> WT
    CF4 --> WT

    TF --> TC
    TC --> ID
    CC --> ID
    RP2 --> ID

    RT --> OC6
    OC6 --> SC
    SC --> EB
```

### Level 3: OCE — Operator Continuity Engine

```mermaid
graph TB
    subgraph "User Layer"
        U[User] --> UI[OCE Shell UI<br/>Next.js Frontend]
    end

    subgraph "Continuity Core"
        UI --> API[FastAPI Backend<br/>Port 8000]
        API --> CHAT[/chat endpoint]
        API --> OBS[/observers endpoints]
        API --> EVT[/events endpoints]
        API --> ATTR[/attractor endpoint]
        API --> MEM[/memory endpoint]
        API --> WS[WebSocket /ws/events]
    end

    subgraph "Event Fabric"
        EF[Event Fabric Engine] --> ING[Ingest]
        EF --> ROUTE[Route]
        EF --> PERSIST[Persist]
        EF --> STREAM[Stream]
        ING --> VALIDATE[Validate + Classify]
        ROUTE --> TOPO[Topology-Aware Routing]
        PERSIST --> TRAJ[Trajectory Memory]
        STREAM --> WS
    end

    subgraph "Observer Runtime"
        OR[Observer Runtime] --> LIFECYCLE[Create/Activate/Suspend/Destroy]
        OR --> HEALTH[Entropy/Drift/Budget]
        OR --> STATE[State Persistence]
    end

    subgraph "SRRA-OPH Substrate"
        SRR[srrs_opc/] --> PATCHES[Observer Patches]
        SRR --> COLLAR[CollarLayer]
        SRR --> TOPO2[CollarTopologyEngine]
        SRR --> DRIFT[DriftDetector]
        SRR --> ENTROPY[EntropyBudgetManager]
    end

    API --> EF
    EF --> OR
    OR --> SRR
    SRR --> EF
```

### Level 4: Data + Trading Pipeline

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

### Level 5: Infrastructure + External Services

```mermaid
graph TB
    subgraph "Local Host"
        WIN[Windows Desktop<br/>BLRRR]
        OC2[OC2 Gateway<br/>Port 18790]
        OCE[OCE Backend<br/>Port 8000]
    end

    subgraph "Cloud Infrastructure"
        HETZ[Hetzner Cloud<br/>CPX31 Primary]
        ORACLE[Oracle Cloud<br/>ARM 24GB]
    end

    subgraph "External APIs"
        OANDA[Oanda API<br/>Verification Data]
        TG[Telegram API<br/>@OC2BLRBOT]
        GH[GitHub API<br/>Source Control]
        OPENROUTER[OpenRouter<br/>LLM Models]
    end

    subgraph "Monitoring"
        WATCHDOG[OC2 Watchdog<br/>60s health checks]
        CTXMON[Context Monitor<br/>75/90/95% alerts]
        DOCTOR[OC2 Doctor<br/>6-layer diagnostic]
    end

    WIN --> OC2
    WIN --> OCE
    OC2 --> TG
    OCE --> OPENROUTER
    WIN --> HETZ
    WIN --> ORACLE
    WATCHDOG --> OC2
    CTXMON --> OC2
```

---

## 🤖 Agent Workflow

```mermaid
sequenceDiagram
    participant H as Human
    participant CC as Claude Code (🔵)
    participant OC as OpenClaw (🟣)
    participant HR as Hermes (🟢)
    participant OC2 as OpenClaw 2 (🟠)
    participant OCE as OCE Backend
    participant SRRA as SRRA-OPH

    H->>CC: Set Direction / Review
    CC->>OC: Task Brief
    OC->>HR: Execution Plan
    HR->>SRRA: Run Analysis
    SRRA->>OCE: Emit Events
    OCE->>OC2: Stream Updates
    OC2->>H: Telegram Notification
    HR->>CC: Progress Update
    CC->>H: Status Report
```

```mermaid
stateDiagram-v2
    [*] --> TaskReceived
    TaskReceived --> Planning: OpenClaw
    Planning --> Implementation: Hermes / OC2
    Implementation --> Verification: Tests + Backtest
    Verification --> Review: CC Review
    Review --> Approved: Quality Gate
    Review --> Rejected: Fix Required
    Rejected --> Implementation
    Approved --> Memory: Sync + Persist
    Memory --> [*]

    state Planning {
        [*] --> ParseBrief
        ParseBrief --> CreatePlan
        CreatePlan --> EstimateEffort
        EstimateEffort --> AssignTasks
    end

    state Implementation {
        [*] --> ExecuteCode
        ExecuteCode --> RunTests
        RunTests --> CollectResults
        CollectResults --> UpdateProgress
    }

    state Verification {
        [*] --> ValidateOutput
        ValidateOutput --> CrossCheck
        CrossCheck --> GenerateReport
    }

    state Memory {
        [*] --> SyncProgress
        SyncProgress --> Summarize
        Summarize --> Archive
    }
```

---

## 💾 Storage Architecture

```mermaid
graph TB
    subgraph "Hot Storage (Local SSD)"
        WS[larger-lab workspace]
        NAUT[nautilus/]
        DATA[data/]
        PROG[progress/]
    end

    subgraph "Warm Storage (USB)"
        USBD[USB Drive D:<br/>57.3GB]
        USBE[USB Drive E:<br/>57.3GB]
    end

    subgraph "Cold Storage (Cloud)"
        GH[GitHub<br/>master branch]
        CLOUD[Cloud Storage<br/>Google Drive/MEGA/pCloud]
        HETZ[Hetzner Cloud<br/>CPX31]
    end

    subgraph "Memory System"
        WM[Working Memory<br/>progress/*-memory.md]
        PM[Persistent Memory<br/>.openclaw/MEMORY.md]
        RM[Repo Memory<br/>workspace-state.md]
        ERR[Error Log<br/>errors-and-solutions.md]
    end

    WS --> USBD
    WS --> USBE
    WS --> GH
    WS --> CLOUD
    PROG --> WM
    WM --> PM
    PM --> RM
```

---

## 🔧 Key Pipelines

### OCE Event Pipeline
```
SRRA-OPH → Event Fabric → Observer Runtime → WebSocket → Frontend
                ↓                ↓
           Persist to      State Updates
           Trajectory      → Telegram
```

### Agent Coordination Pipeline
```
Human → CC → OC → HR/OC2 → Results → Progress Files → Sync → Memory
```

### Memory Sync Pipeline
```
progress files → progress-sync.py → working memory + persistent memory + repo memory
team-chat.md → chat_sync.py → working memory + repo memory
errors → errors-and-solutions.md → repo memory (every 7 entries)
```

---

## 📁 Quick Reference

| Directory | Purpose |
|-----------|---------|
| `srrs_opc/` | SRRA-OPH core (33 Python files, 77 tests) |
| `nautilus/` | NautilusTrader backtesting |
| `oce/` | Operator Continuity Engine |
| `oce/backend/resonance/` | V3 Phase 1 — Resonant Signal Substrate (139 tests) |
| `progress/` | Agent sub-progress files |
| `system-arch/` | All Mermaid diagrams |
| `all-mermaids/` | Diagram archive by phase |
| `tools/` | Automation & utilities |
| `memory-bank/` | Error DB, solutions, patterns |

---

## 🔄 V3 Phase 1 — Resonant Signal Substrate (RSS)

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

### V3 Phase 1 Modules

| Module | File | Tests | Purpose |
|--------|------|-------|---------|
| SignalPacket | `oce/backend/resonance/signal_packet.py` | 34 | Signal ontology + resonance scoring |
| CoherenceMetrics | `oce/backend/resonance/coherence_metrics.py` | 21 | 6 coherence metrics tracking |
| FieldStateManager | `oce/backend/resonance/field_state.py` | 16 | Field state management |
| BoundaryMapper | `oce/backend/resonance/boundary_mapper.py` | 20 | Boundary detection + pressure mapping |
| ResonanceEngine | `oce/backend/resonance/resonance_engine.py` | 20 | Resonance alignment + scoring |
| PressureTracker | `oce/backend/resonance/pressure_tracker.py` | 10 | Entropy pressure monitoring |
| RL Integration | `oce/backend/resonance/rlp_integration.py` | 18 | RL ↔ CC bridge |

---

## ⚠️ ERR-0007: Windows Subprocess Execution Rules

```mermaid
flowchart LR
    A[subprocess.run] --> B[CREATE_NO_WINDOW]
    C[subprocess.Popen] --> D[DETACHED_PROCESS<br/>CREATE_NO_WINDOW<br/>CREATE_NEW_PROCESS_GROUP]
    E[Daemon Scripts] --> F[PID File Tracking]
    G[Session Start] --> H[terminal_cleanup.py --force]
```

**Prevention Rules:**
- ALL `subprocess.run()` on Windows MUST use `creationflags=subprocess.CREATE_NO_WINDOW`
- ALL `subprocess.Popen()` for background processes MUST use `DETACHED_PROCESS | CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP`
- Always implement PID file tracking for daemon scripts
- Run `tools/terminal_cleanup.py --force` at session start