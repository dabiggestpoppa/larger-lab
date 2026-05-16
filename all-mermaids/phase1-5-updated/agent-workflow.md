# Agent Workflow — Phase 1-5 Updated

> Source: CODEMAP.md (line 305)
> Phase: 1-5 Updated

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
