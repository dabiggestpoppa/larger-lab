# CODEMAP — Larger-Lab Workspace Guide

> **Last Updated:** 2026-05-17 | **Phase:** OCE Phase 5 (Observability) — Active
> **Purpose:** Quick orientation for agents joining the workspace.

---

## 1. SYSTEM ARCHITECTURE GRAPH

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

## 2. DATA FLOW / TOURING GRAPH

```mermaid
flowchart LR
    subgraph "Input"
        EXT[External Event]
        CSV[Downloads/*.csv]
    end

    subgraph "Event Fabric"
        EF[Event Fabric]
        ING[Ingest]
        ROUTE[Topological Router]
        PERSIST[Persistence]
        STREAM[WebSocket Stream]
    end

    subgraph "Observer Runtime"
        OR[Observer Runtime]
        LIFECYCLE[Lifecycle]
        HEALTH[Health Monitor]
    end

    subgraph "Output"
        UI[OCE Frontend<br/>:3000]
        TG[Telegram]
        REPORTS[Reports]
    end

    EXT --> ING
    ING --> ROUTE
    ROUTE --> PERSIST
    PERSIST --> STREAM
    STREAM --> UI
    STREAM --> TG

    CSV --> NT[Nautilus Trader]
    NT --> REPORTS
    REPORTS --> TF[Trajectory Fields]
    TF --> EF
```

---

## 3. LOGIC CHAIN (Execution Flow)

```mermaid
stateDiagram-v2
    [*] --> StartSession
    StartSession --> ReadRules: Read OPERATOR_RULES.md
    ReadRules --> ReadAgents: Read AGENTS.md
    ReadAgents --> ReadChat: Read team-chat.md
    ReadChat --> LoadContext
    LoadContext --> HealthCheck
    HealthCheck --> PrioritizeTasks
    PrioritizeTasks --> CanDoDirectly
    CanDoDirectly -->|Yes| BuildDirectly
    CanDoDirectly -->|No| SpawnSubagent
    BuildDirectly --> VerifyOutput
    SpawnSubagent --> MonitorProgress
    VerifyOutput --> MoreTasks
    MonitorProgress --> MoreTasks
    MoreTasks -->|Yes| PrioritizeTasks
    MoreTasks -->|No| EndSession
    EndSession --> [*]
```

```mermaid
sequenceDiagram
    participant H as Human
    participant CC as Claude Code
    participant OC as OpenClaw
    participant HR as Hermes
    participant OC2 as OpenClaw 2
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
      ▼                                                ▼
[Run tests]                                       [Fix failures]
      │                                                │
      ▼                                                ▼
[All pass?] ──NO──▶ [Fix failures]            [Post to team-chat]
      │                                                │
      YES                                               ▼
      │                                          [Report completion]
      ▼                                                │
[Post to team-chat] ◀──────────────────────────────────┘
      │
      ▼
[Update progress file]
      │
      ▼
[Done]


┌─────────────────────────────────────────────────────────────────────────────┐
│                         ERROR HANDLING CHAIN                                 │
└─────────────────────────────────────────────────────────────────────────────┘

[Error Detected]
      │
      ▼
[Read the LOG] ◀── "Read the logs, not the dashboard"
      │
      ▼
[Identify root cause] ◀── Not symptom
      │
      ▼
[Fix ONE thing] ◀── Never batch fixes
      │
      ▼
[Test]
      │
      ▼
[Pass?] ──NO──▶ [Read the LOG again]
      │
      YES
      │
      ▼
[Document fix pattern]
      │
      ▼
[Continue]


┌─────────────────────────────────────────────────────────────────────────────┐
│                         ENTROPY GOVERNANCE CHAIN                             │
└─────────────────────────────────────────────────────────────────────────────┘

[Before Action]
      │
      ▼
[Is this necessary?] ──NO──▶ [Skip]
      │
      YES
      │
      ▼
[Can existing tool do this?] ──YES──▶ [Use existing]
      │
      NO
      │
      ▼
[Build minimal solution]
      │
      ▼
[Test + Document]
      │
      ▼
[Compress / Clean up]
      │
      ▼
[Continue]
```

---

## 4. ERROR HANDLING CHAIN

```mermaid
flowchart LR
    A[Error Detected] --> B[Read the LOG]
    B --> C[Identify root cause]
    C --> D[Fix ONE thing]
    D --> E[Test]
    E -->|Fail| B
    E -->|Pass| F[Document fix pattern]
    F --> G[Continue]
```

---

## 5. ENTROPY GOVERNANCE CHAIN

```mermaid
flowchart LR
    A[Before Action] --> B{Is this necessary?}
    B -->|No| C[Skip]
    B -->|Yes| D{Can existing tool do this?}
    D -->|Yes| E[Use existing]
    D -->|No| F[Build minimal solution]
    F --> G[Test + Document]
    G --> H[Compress / Clean up]
    H --> I[Continue]
```

---

## 6. Workspace Map

```mermaid
graph TD
    ROOT[larger-lab/] --> CONFIG[config/]
    ROOT --> DOCS[docs/]
    ROOT --> OCE[oce/]
    ROOT --> SRRA[srrs_opc/]
    ROOT --> TOOLS[tools/]
    ROOT --> SKILLS[skills/]
    ROOT --> PROGRESS[progress/]
    ROOT --> PROJECTS[projects/]
    ROOT --> SHARED[shared-conversations/]
    ROOT --> LOGS[logs/]
    ROOT --> MEMBANK[memory-bank/]

    CONFIG --> IDENTITY[IDENTITY.md<br/>SOUL.md<br/>OPERATOR_RULES.md]
    DOCS --> CM[CODEMAP.md]
    OCE --> BACKEND[oce/backend/]
    OCE --> FRONTEND[oce/frontend/]
    BACKEND --> MAIN[main.py<br/>101 tests]
    BACKEND --> EF[event_fabric.py]
    BACKEND --> OR[observer_runtime.py]
    BACKEND --> SM[structural_memory.py]
    SRRA --> OPC[srrs_opc/ - 77 tests]
    TOOLS --> OP[tools/operator/]
    TOOLS --> HOOKS[tools/agent-hooks/]
    TOOLS --> SYNC[progress-sync.py<br/>chat_sync.py]
```

```
larger-lab/
  ├── config/                  ← Identity, soul, keys, heartbeat, teams, repos, tools
  ├── docs/                    ← Architecture, workflow, progress, codemap, mermaid graphs
  │   ├── CODEMAP.md           ← This file (architecture + logic graphs)
  │   ├── SYSTEM_ARCHITECTURE.md
  │   ├── WORKFLOW_PROTOCOL.md
  │   ├── IMPLEMENTATION_PLAN.md
  │   ├── RELEVANCE_MAP.md
  │   ├── SKILLS_MASTER_INDEX.md
  │   └── SKILL_TOOL_AUDIT.md
  ├── oce/                     ← Operator Continuity Engine (OCE)
  │   ├── backend/              ← FastAPI Continuity Core
  │   │   ├── main.py           ← All API endpoints (101 tests)
  │   │   ├── event_fabric.py   ← Event Fabric + TopologicalRouter + Persistence
  │   │   ├── observer_runtime.py ← Observer lifecycle (20 tests)
  │   │   ├── structural_memory.py ← 3-layer memory + FTS5 (30 tests)
  │   │   ├── phase4_api.py     ← 6 advanced memory endpoints
  │   │   ├── srrs_adapter.py   ← SRRA-OPH substrate adapter
  │   │   ├── dspy_pipelines.py ← DSPy optimization pipelines
  │   │   └── tests/            ← 101 tests total
  │   ├── frontend/             ← Next.js Shell UI (:3000)
  │   └── docs/                 ← OCE documentation
  │       ├── event-types.md    ← 86 event types
  │       ├── event-protocol.md ← WebSocket protocol
  │       ├── observer-types.md ← 8 observer types
  │       ├── observer-research.md ← Architecture research
  │       └── quality-review-*.md ← Phase 2/3/4 reviews
  ├── srrs_opc/                ← SRRA-OPH core (33 Python files, 77 tests)
  ├── tools/                   ← Automation & operator tools
  │   ├── operator/             ← Operator control layer (:8001)
  │   │   ├── desktop-control.py
  │   │   ├── vscode_bridge.py
  │   │   ├── system_operator.py
  │   │   ├── observer-debug.py
  │   │   ├── observer-integration.py
  │   │   └── desktop_api.py
  │   ├── agent-hooks/          ← Pre/post tool use hooks
  │   ├── hermes-watchdog.py    ← OWL health monitor
  │   ├── progress-sync.py      ← Agent progress sync
  │   ├── chat_sync.py          ← Team chat sync
  │   └── ...
  ├── skills/                  ← Agent skills (57 active)
  │   ├── system-health/        ← 10-point self-audit
  │   ├── harness-engineering/  ← Agent reliability patterns
  │   ├── docker-ops/           ← Container management
  │   ├── cicd-pipeline/        ← CI/CD automation
  │   ├── oce-testing/          ← OCE test patterns
  │   ├── db-ops/               ← Database operations
  │   ├── cloakbrowser/         ← Stealth Chromium
  │   ├── agentmemory/          ← Persistent memory engine
  │   └── ...
  ├── progress/                ← Agent sub-progress & memory files
  ├── projects/                ← External projects
  │   ├── ads/
  │   ├── content/
  │   ├── trading/
  │   ├── ai-tools/
  │   ├── social/
  │   └── llm_wiki/            ← Self-building knowledge base
  ├── shared-conversations/    ← Team chat (team-chat.md)
  ├── logs/                    ← System logs
  ├── memory-bank/             ← Error DB + knowledge base
  │
  ├── AGENTS.md                ← Team manifest + operator rules
  ├── OPERATOR_RULES.md        ← Bounded sovereign operational continuity
  ├── SUB_AGENT_RULES.md       ← Sub-agent governance
  ├── TOOLS.md                 ← Complete tool reference
  └── CLAUDE.md                ← 12-rule behavioral contract
```

---

## Quick Commands

```bash
# Run all SRRA-OPH tests (77 tests)
python -m pytest srrs_opc/tests/ -v

# Run all OCE tests (101 tests)
python -m pytest oce/backend/tests/ -v

# Sync progress → memory
python tools/progress-sync.py --force

# Sync team-chat → agent memory
python tools/chat_sync.py --force

# Health check
python tools/hermes-watchdog.py --once

# Start OCE backend
cd oce/backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Start OCE frontend
cd oce/frontend && npm run dev

# Start Desktop Control API
python tools/operator/desktop_api.py

# Start AgentMemory server
npx @agentmemory/agentmemory
```

---

## Port Reference

| Port | Service | Status |
|------|---------|--------|
| 18789 | OpenClaw gateway (OC1) | Live |
| 18790 | OpenClaw gateway (OC2, primary) | Live |
| 3000 | OCE frontend (Next.js) | Needs npm install |
| 8000 | OCE backend (FastAPI) | Ready |
| 8001 | Desktop control API | Ready |
| 3111 | AgentMemory server | Needs setup |
| 3113 | AgentMemory viewer | Needs setup |

---

## Test Status

| Suite | Tests | Status |
|-------|-------|--------|
| SRRA-OPH (srrs_opc/) | 77 | ✅ Passing |
| OCE Event Fabric | 32 | ✅ Passing |
| OCE Observer Runtime | 20 | ✅ Passing |
| OCE Topology + Persistence | 19 | ✅ Passing |
| OCE Structural Memory | 30 | ✅ Passing |
| **Total OCE** | **101** | ✅ **All Passing** |

---

## 7. SRRA-OPH Topology (Phases 1-9)

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

---

## 8. ERR-0007: Windows Subprocess Execution Rules

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

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-16 | Initial CODEMAP |
| 2.0.0 | 2026-05-16 | Added mermaid graphs, updated for Phase 4 completion, added logic chains |
| 3.0.0 | 2026-05-17 | Added ERR-0007 Windows subprocess rules, Phase 5 observability, unified diagrams |

---

## Quick Reference

| Directory | Purpose |
|-----------|---------|
| `srrs_opc/` | SRRA-OPH core (33 Python files, 77 tests) |
| `nautilus/` | NautilusTrader backtesting |
| `oce/` | Operator Continuity Engine |
| `progress/` | Agent sub-progress files |
| `system-arch/` | All Mermaid diagrams |
| `all-mermaids/` | Diagram archive by phase |
| `tools/` | Automation & utilities |
| `memory-bank/` | Error DB, solutions, patterns |
