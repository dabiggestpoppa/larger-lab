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
