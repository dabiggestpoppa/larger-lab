# Agent Workflow + Communication

> **Purpose:** Agent interaction patterns, workflow state machine, and communication flows.
> **Updated:** 2026-05-16

## Agent Communication Flow

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

## Workflow State Machine

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
    }

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

## Agent Handoff Protocol

```mermaid
flowchart TD
    CC[Claude Code<br/>Overseer] -->|Task Brief| OC[OpenClaw<br/>Analysis]
    OC -->|Execution Plan| HR[Hermes<br/>Execution]
    HR -->|Progress| SYNC[progress-sync.py]
    SYNC -->|Auto-sync| PP[PROJECT_PROGRESS_CLEAN.md]
    SYNC -->|Working Memory| WM[progress/*-memory.md]
    SYNC -->|Persistent Memory| PM[.openclaw/MEMORY.md]
    SYNC -->|Repo Memory| RM[workspace-state.md]

    HR -->|Complete| REVIEW{Quality Gate}
    REVIEW -->|Approve| NEXT[Next Phase]
    REVIEW -->|Fix| HR
    NEXT -->|New Task| OC

    OC2[OpenClaw 2<br/>Telegram] -->|Monitor| ALL[All Agents]
    ALL -->|Status| OC2
    OC2 -->|Alert| H[Human]
```

## OCE Event Flow

```mermaid
flowchart LR
    SRRA[SRRA-OPH<br/>Substrate] -->|emit events| EF[Event Fabric]
    EF -->|route| OR[Observer Runtime]
    OR -->|process| OBS[Observers]
    OBS -->|output events| EF
    EF -->|stream| WS[WebSocket]
    WS -->|real-time| UI[OCE Frontend]
    EF -->|persist| TRAJ[Trajectory Memory]
    EF -->|query| API[/events endpoint]
```
