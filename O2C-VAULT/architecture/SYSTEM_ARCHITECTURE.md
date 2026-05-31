# System Architecture — Complete Guide

TYPE: architecture
SUMMARY: Complete 5-level architecture of the Larger-Lab sovereign cognitive field system.
CAUSE: Every agent and developer needs to understand how the system is structured and how components connect.
FUNCTION: Master reference for system topology, component relationships, and data flow.

## System at a Glance

Larger-Lab is a **sovereign cognitive field system** — a multi-agent architecture where autonomous agents collaborate under human strategic direction (MAD).

**Key metrics:**
- 1582+ tests passing (1403 OCE + 57 SRRA-OPH + 122 O2C)
- 67 V3 modules across 10 phases + 11 Observer Core modules = 78 total
- 5 active agents (CC, OC2, AS, PM, RL)
- 19 vault API routes (Phase 00 + Phase 01)

## The Five Architecture Levels

### Level 1: Human Interface + Agent Network
- **Human (MAD):** Defines strategic attractors (goals). Reviews results. Sets direction.
- **Claude Code (CC):** Overseer / Architecture. Translates intent into task briefs. Reviews quality.
- **OC2 (OWL):** Primary Operator / Orchestrator. O2C orchestration cognition layer natively embedded in OCE.
- **AS (Assistant Manager):** Context Monitoring / Quality
- **PM (Polymorph):** Debugger / Tool Builder
- **RL (Research Lead):** Research / DSPy

### Level 2: SRRA-OPH — The Substrate
- Collar Protocol → Observer Patches → Repair Loops
- 57 tests passing
- Stabilizes the cognitive field, manages entropy, handles drift

### Level 3: OCE V3 — The Cognitive Field
- 67 modules across 10 phases
- Event Fabric → Observer Runtime → Field Core
- 1403 tests passing
- The primary computational substrate

### Level 4: O2C — Cognitive Filesystem & Obsidian Mesh
- Phase 00: Cognitive Filesystem Foundation (10 components, 84 tests)
- Phase 01: Obsidian Cognitive Mesh (4 components, 149 tests total)
- 19 vault API routes
- Persistent operational memory via Obsidian vault

### Level 5: Infrastructure
- Windows Desktop → Cloud → External APIs
- FastAPI backend on port 8000
- Next.js frontend on port 3000
- Obsidian vault at C:\Users\wifik\Downloads\o2c

## Component Topology

```
HUMAN (MAD)
    ↓
AGENT NETWORK (CC → OC2 → AS/PM/RL)
    ↓
OBSERVER CORE (O-1 through O-7)
    ↓
SRRA-OPH (Repair / Entropy / Drift / BSP)
    ↓
OCE V3 (10 Phase Cognitive Field)
    ↓
O2C LAYER (Distill / Journal / Skills)
    ↓
OBSIDIAN VAULT (Persistent Cognitive Mesh)
    ↓
KNOWLEDGE GRAPH (Externalized Cognition)
```

## Key Files

| Path | Purpose |
|------|---------|
| oce/backend/main.py | FastAPI app, all endpoint registration |
| oce/backend/vault_api.py | Vault API endpoints (Phase 00 + 01) |
| core/obsidian/ | Phase 00+01 cognitive components |
| core/execution/journal.py | Execution journal |
| core/skills/loader.py | Skill loader |
| srrs_opc/ | SRRA-OPH core |
| O2C-VAULT/ | Internal workspace vault |
| C:\Users\wifik\Downloads\o2c | Real Obsidian vault |

RELATIONSHIPS: [[V3 Architecture]] [[PRINCIPLES]] [[Observer Core O-1 through O-7]] [[O2C Pipeline]]

STATUS: active
SOURCE: ARCHITECTURE.md
