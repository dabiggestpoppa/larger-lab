# Agent Topology — Relationship Map

TYPE: graph
SUMMARY: Visual map of how agents relate to each other and to system components.
CAUSE: Understanding agent relationships is critical for orchestration.
FUNCTION: Reference for delegation, communication paths, and responsibility boundaries.

## Agent Relationship Diagram

```mermaid
graph TB
    MAD["👤 MAD\nHuman Anchor"] -->|"strategic attractors"| CC["🔵 CC\nOverseer"]
    MAD -->|"directives"| OC2["🟠 OC2\nOrchestrator"]
    
    CC -->|"task briefs"| OC2
    CC -->|"quality review"| AS["🟡 AS\nQuality"]
    CC -->|"architecture"| PM["🔵 PM\nDebugger"]
    
    OC2 -->|"delegates"| PM
    OC2 -->|"delegates"| PM2["🔴 PM2\nFrontend"]
    OC2 -->|"delegates"| RL["🟢 RL\nResearch"]
    OC2 -->|"delegates"| HR["🟢 HR\nExecution"]
    OC2 -->|"quality gate"| AS
    
    PM -->|"tools"| PM2
    RL -->|"research"| HR
    
    subgraph "Unified Field"
        OCE["OCE V3\nCognitive Field"]
        SRRA["SRRA-OPH\nSubstrate"]
        O2C["O2C\nCognitive Filesystem"]
        OBSIDIAN["Obsidian Vault\nMemory Spine"]
    end
    
    OC2 -->|"orchestrates"| OCE
    OC2 -->|"orchestrates"| SRRA
    OC2 -->|"orchestrates"| O2C
    OC2 -->|"writes"| OBSIDIAN
    CC -->|"certifies"| OCE
```

## Communication Paths

| From | To | Channel | Purpose |
|------|----|---------|---------|
| MAD | CC | Direct | Strategic direction |
| MAD | OC2 | Direct | Operational directives |
| CC | OC2 | Task briefs | Architecture decisions |
| OC2 | All agents | runSubagent | Task delegation |
| All agents | All | team-chat.md | Status updates |
| All agents | All | Obsidian vault | Knowledge sharing |

## Delegation Rules
1. OC2 delegates to Manager → Worker pipeline
2. One Worker = One Deliverable
3. Max 5 concurrent sub-agents
4. Manager NEVER executes
5. All workers write checkpoint progress

RELATIONSHIPS: [[Team Roster]] [[OC2 Identity]] [[System Architecture]]

STATUS: active
SOURCE: AGENTS.md, IDENTITY.md

LINKS:
[[OC2 (OWL) — Unified Field Operator]]
[[Team Roster — Agent Network]]
[[System Architecture — Complete Guide]]
[[Operator Rules — Bounded Sovereign Operational Continuity]]
[[Hermes Agent Test Note]]
[[KeyError — data_validation — 20260531_0245]]
[[Task Flow — How Work Moves Through the System]]
[[Session Distillation — TestAgent]]
[[Build Patterns — Successful Operational Patterns]]
[[O2C Pipeline — Cognitive Filesystem & Obsidian Mesh]]
[[Observer Core — O-1 through O-7]]
[[SRRA-OPH — Observer Patch Substrate]]
[[API Reference — OCE Backend Endpoints]]
[[Module Guide — 78 Modules Reference]]
