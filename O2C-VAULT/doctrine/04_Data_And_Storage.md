# 04 Data And Storage

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine

# Data Pipeline + Storage Architecture

> **Purpose:** Data flow, storage layers, and backup architecture.
> **Updated:** 2026-05-18 | GitHub cleanup complete (47 tmp files removed)

## Data Pipeline

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

## Storage Architecture

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

## Backup & Restore

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

## Memory Sync Flow

```mermaid
flowchart TD
    AGENT[Agent writes progress] --> PF[progress/*-progress.md]
    PF --> SYNC[progress-sync.py<br/>Every 7 updates]
    SYNC --> WM[Working Memory<br/>progress/*-memory.md]
    SYNC --> PM[Persistent Memory<br/>.openclaw/MEMORY.md]
    SYNC --> RM[Repo Memory<br/>workspace-state.md]
    SYNC --> CM[CODEMAP.md<br/>Auto-updated]
    SYNC --> ERR[errors-and-solutions.md<br/>Every 7 entries]

    CHAT[team-chat.md<br/>Every 5 messages] --> CS[chat_sync.py]
    CS --> WM
    CS --> RM
```

LINKS:
[[Architecture]]
[[Codemap]]
[[01 System Overview]]
[[02 Agent Workflow]]
[[03 Srra Topology]]
[[Agents]]
[[Api Reference]]
[[Cg 1 Mermaid Specs]]
[[Cg 1 Revised]]
[[Cg 2 Mermaid Specs]]
[[Cg 2 World Model Activation]]
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
[[Errors And Solutions]]
[[Keyerror Data Validation 20260531 0245]]
[[Progress]]
[[Cal]]
[[Camera And 3D]]
[[External Data]]
[[Graphs And Data]]
[[Shapes And Geometry]]
[[Sources]]
[[System]]
[[Updaters And Trackers]]
[[Warm]]
[[Webgl And 3D]]
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
[[Data Fetcher]]
[[Metrics]]
