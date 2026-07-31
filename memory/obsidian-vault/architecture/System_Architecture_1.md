# System Architecture

> Category: architecture | Imported: 2026-06-02 01:13 UTC

Tags: #architecture

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
| memory/obsidian-vault/ | Internal workspace vault |
| C:\Users\wifik\Downloads\o2c | Real Obsidian vault |

RELATIONSHIPS: [[V3 Architecture]] [[PRINCIPLES]] [[Observer Core O-1 through O-7]] [[O2C Pipeline]]

STATUS: active
SOURCE: ARCHITECTURE.md

LINKS:
[[Vault]]
[[Metrics]]
[[Loader]]
[[Journal]]
[[Memory]]
[[System]]
[[Skill]]
[[Server]]
[[Patterns]]
[[Modules]]
[[Api Endpoints]]
[[Welcome]]
[[Vault Distillation 20260531 0245]]
[[Tradovate Api Discovery 20260531]]
[[Track A Ninjascript Build 20260531]]
[[Track A Build Status]]
[[Track A Build Complete 20260531]]
[[Test Pattern]]
[[Test Note]]
[[Team Roster]]
[[Team Phase01 Status]]
[[Task Flow]]
[[Srra Oph]]
[[Session Testagent 20260531 0245 Full]]
[[Session Testagent 20260531 0245]]
[[Session 20260531 2200]]
[[Self Heal Report]]
[[Sage Audit Environment Utilization]]
[[Sage Audit 20260531 Environment Utilization V2]]
[[Sage Audit 20260531 Environment Utilization]]
[[Quantlab Bible]]
[[Python Vs Nautilus Tradecount Investigation 20260601]]
[[Progress]]
[[Pm2 Test Note]]
[[Option A Confirmed 20260531]]
[[Operational State 20260531]]
[[Ontology Core Summary]]
[[Oc2 Vault Access Guide]]
[[Oc2 Identity]]
[[Oc2 Gateway Failures]]
[[Obsidian Vault Connection Info]]
[[Observer Core O1 O7]]
[[Module Guide Summary]]
[[Master Plan Assessment 20260531]]
[[Live Deployment Status]]
[[Keyerror Data Validation 20260531 0245]]
[[Journal 20260602T005953Z Task Update]]
[[Journal 20260602T005953Z Task Create]]
[[Journal 20260602T005953Z Spawn Research]]
[[Journal 20260602T005953Z Orchestrated Spawn]]
[[Journal 20260602T005953Z Command Task]]
[[Journal 20260602T005953Z Command Status]]
[[Journal 20260602T005953Z Command Spawn]]
[[Journal 20260602T005953Z Command Report]]
[[Journal 20260602T004841Z Report Oc2 20260602004841]]
[[Journal 20260602T004841Z Report]]
[[Journal 20260602T004841Z Conversation]]
[[Journal 20260602T004840Z Sync]]
[[Journal 20260602T004840Z Graph Summary]]
[[Journal 20260602T004840Z Command Sync]]
[[Journal 20260602T004840Z Command Status]]
[[Journal 20260602T004840Z Command Help]]
[[Journal 20260602T004840Z Command Graph]]
[[Hermes Obsidian Test   Vault Working]]
[[Hermes Agent Test Note]]
[[Hermes Agent Test]]
[[Hermes Agent Activation Note]]
[[Foundational Principles]]
[[Failure Index Oc2]]
[[Executor Crash 20260531]]
[[Errors And Solutions]]
[[Doctor Prescription]]
[[Dashboard Build Complete]]
[[Daily Runtime 20260531]]
[[Cerebus Nt8 Deployment Campaign 20260531]]
[[Cc Phase 01 Build Certification Report]]
[[Build Progress 20260531]]
[[Build Patterns]]
[[Backtest Phase Status]]
[[Backtest Campaign V3 Results]]
[[Backtest Campaign Status 20260531]]
[[Api Test Note]]
[[Api Reference Summary]]
[[Api Execution Architecture 20260531]]
[[Agent Topology]]
[[Active Strategies Performance]]
[[2026 06 01]]
[[2026 05 31]]
[[2026 05 30 Nautilus Fix]]
[[2026 05 30 Evening]]
[[2026 05 30]]
[[2026 05 21]]
[[2026 05 20]]
[[2026 05 18]]
[[2026 05 17]]
[[User]]
[[Topological Cognition Architecture]]
[[Principles]]
[[Operator Rules]]
[[Module Guide]]
[[Claude]]
[[Api Reference]]
[[Agents]]
[[01 System Overview]]
[[V3 Cognitive Field]]
[[Architecture]]
[[OC2 (OWL) — Unified Field Operator]]
[[Team Roster — Agent Network]]
[[V3 Cognitive Field System]]
[[Operator Rules — Bounded Sovereign Operational Continuity]]
[[KeyError — data_validation — 20260531_0245]]
[[Agent Topology — Relationship Map]]
[[Task Flow — How Work Moves Through the System]]
[[Session Distillation — TestAgent]]
[[Build Patterns — Successful Operational Patterns]]
[[O2C Pipeline — Cognitive Filesystem & Obsidian Mesh]]
[[Observer Core — O-1 through O-7]]
[[SRRA-OPH — Observer Patch Substrate]]
[[API Reference — OCE Backend Endpoints]]
[[Module Guide — 78 Modules Reference]]
