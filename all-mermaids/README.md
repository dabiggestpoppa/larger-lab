# 🧜 All Mermaid Diagrams — SRRA-OPH Project

> Complete collection of all Mermaid diagrams across the workspace.
> Organized by phase and purpose for quick reference.

## 📁 Structure

```
all-mermaids/
  README.md                    ← You are here
  phase1-5-original/           ← Original Phase 1-5 diagrams (from PROJECT_PROGRESS.md)
    system-architecture.md
    agent-communication.md
    data-pipeline.md
    backup-architecture.md
    p90-strategy-logic.md
    workflow-state-machine.md
    file-structure.md
  phase1-5-updated/            ← Updated Phase 1-5 diagrams (from CODEMAP.md)
    system-overview.md
    agent-workflow.md
    data-pipeline.md
    srra-architecture.md
    file-structure.md
  phase6-9-resources/          ← Phase 6-9 resource diagrams
    full-topology.md
    agent-integration.md
```

## 📊 Diagram Index

### Phase 1-5 Original (PROJECT_PROGRESS.md)
| File | Diagram | Description |
|------|---------|-------------|
| `phase1-5-original/system-architecture.md` | graph TB | Full system architecture with human interface, orchestration, data, storage layers |
| `phase1-5-original/agent-communication.md` | sequenceDiagram | Agent communication flow: Human → CC → OC → Hermes → Nautilus → Memory |
| `phase1-5-original/data-pipeline.md` | flowchart LR | Data pipeline: CSV → Parquet → Nautilus → Reports → Memory |
| `phase1-5-original/backup-architecture.md` | graph LR | Backup & restore architecture with USB, GitHub, cloud |
| `phase1-5-original/p90-strategy-logic.md` | flowchart TD | P90 strategy logic: Asian Range → Thresholds → Signals → Positions → Exit |
| `phase1-5-original/workflow-state-machine.md` | stateDiagram-v2 | Workflow protocol state machine: Task → Planning → Implementation → Verification → Review |
| `phase1-5-original/file-structure.md` | graph TD | File structure map of the workspace |

### Phase 1-5 Updated (CODEMAP.md)
| File | Diagram | Description |
|------|---------|-------------|
| `phase1-5-updated/system-overview.md` | graph TB | System overview with human interface, progress layer, SRRA-OPH, trading engine, tools |
| `phase1-5-updated/agent-workflow.md` | flowchart TD | Agent workflow: direction → brief → plan → execute → review → sync |
| `phase1-5-updated/data-pipeline.md` | flowchart LR | Data pipeline: CSV → prep → validate → backtest → sweep → reports → progress → memory |
| `phase1-5-updated/srra-architecture.md` | graph LR | SRRA-OPH architecture: Collar Protocol → Observer Patches → Repair Loops |
| `phase1-5-updated/file-structure.md` | graph TD | Updated file structure with agents, nautilus, srrs_opc, progress, tools |

### Phase 6-9 Resources
| File | Diagram | Description |
|------|---------|-------------|
| `phase6-9-resources/full-topology.md` | graph TD | Full SRRA-OPH topology: Local Observers → Active Collars → Reconstruction → Capability Fields → Governance |
| `phase6-9-resources/agent-integration.md` | graph TB | Agent integration points: OpenClaw, Hermes, Nautilus |
