# System Overview — All Levels

> **Purpose:** High-level view of the entire larger-lab system.
> **Updated:** 2026-05-16

## Level 1: Human Interface + Agent Network

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

## Level 2: SRRA-OPH Substrate

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

## Level 3: OCE — Operator Continuity Engine

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

## Level 4: Data + Trading Pipeline

```mermaid
flowchart LR
    subgraph "Data Input"
        CSV[Downloads/*.csv<br/>29 files M1/M5 2022-2026]
    end

    subgraph "Processing"
        CSV --> PREP[nautilus/step1_prep_data.py]
        PREP --> PARQUET[nautilus/data/*.parquet]
    end

    subgraph "Backtesting"
        PARQUET --> NT[Nautilus Trader<br/>Backtest Engine]
        STR[strategies/<br/>p90, symmetry, ema] --> NT
        NT --> REPORTS[nautilus/reports/]
    end

    subgraph "Analysis"
        REPORTS --> VBT[VectorBT]
        REPORTS --> PANDAS[pandas/scikit-learn]
    end

    subgraph "Storage"
        LOCAL[Local SSD<br/>Hot Data]
        USB[USB Drives<br/>D: & E: 57GB]
        GITHUB[GitHub<br/>Source Control]
        CLOUD[Cloud Storage<br/>Google Drive/MEGA/pCloud]
    end
```

## Level 5: Infrastructure + External Services

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
