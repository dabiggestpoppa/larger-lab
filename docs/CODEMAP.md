# CODEMAP — Larger-Lab Workspace Guide

> **Last Updated:** 2026-05-16 | **Phase:** OCE Phase 4 (Structural Memory) — Complete
> **Purpose:** Quick orientation for agents joining the workspace.

---

## 1. SYSTEM ARCHITECTURE GRAPH

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MAD (Human Operator)                               │
│                    Strategic Initiator / Attractor Definer                   │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OWL (Operator Shell)                                 │
│              Bounded Sovereign Operational Continuity                        │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        OCE Continuity Core                            │   │
│  │                        (FastAPI :8000)                                 │   │
│  │                                                                       │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────────┐  │   │
│  │  │   Event      │  │   Observer   │  │   Structural Memory          │  │   │
│  │  │   Fabric     │  │   Runtime    │  │   (Phase 4)                  │  │   │
│  │  │   (Phase 2)  │  │   (Phase 3)  │  │                              │  │   │
│  │  │              │  │              │  │  ┌──────┐ ┌────────┐ ┌─────┐ │  │   │
│  │  │ ┌──────────┐ │  │ ┌──────────┐ │  │  │ WORK │ │LEARNED │ │KNOW │ │  │   │
│  │  │ │Ingest    │ │  │ │Lifecycle │ │  │  └──────┘ └────────┘ └─────┘ │  │   │
│  │  │ │Route     │ │  │ │Health    │ │  │                              │  │   │
│  │  │ │Persist   │ │  │ │Events    │ │  │  FTS5 + SQLite + TTL        │  │   │
│  │  │ │Stream    │ │  │ │Snapshots │ │  │  Compression + Wiki Export   │  │   │
│  │  │ └──────────┘ │  │ └──────────┘ │  │  Graph + Reconstruction     │  │   │
│  │  │              │  │              │  │                              │  │   │
│  │  │ Topological  │  │  Observer   │  │  101 tests passing          │  │   │
│  │  │ Router       │  │  Debug CLI  │  │                              │  │   │
│  │  │ (Dijkstra)   │  │  Integration│  │                              │  │   │
│  │  └─────────────┘  └──────────────┘  └─────────────────────────────┘  │   │
│  │                                                                       │   │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │   │
│  │  │                    SRRA-OPH Substrate                             │ │   │
│  │  │                    (srrs_opc/ — 77 tests)                         │ │   │
│  │  │                                                                   │ │   │
│  │  │  Phases 1-9: Observer Mesh → Topology → Overlap → Coevolution   │ │   │
│  │  │  Entropy Economics → Attractor Reasoning → Repair Patches       │ │   │
│  │  └──────────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Operator Control Layer                            │   │
│  │                      (tools/operator/ :8001)                           │   │
│  │                                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────────┐ │   │
│  │  │   Desktop     │  │   VS Code    │  │   System Operator            │ │   │
│  │  │   Control     │  │   Bridge     │  │   (Process/Package/Env/     │ │   │
│  │  │              │  │              │  │    Service/Scheduler/Network) │ │   │
│  │  │  Screen      │  │  Files       │  │                              │ │   │
│  │  │  Input Sim   │  │  Editor      │  │  Observer Integration        │ │   │
│  │  │  Window Mgr  │  │  Terminal    │  │  Observer Debug CLI          │ │   │
│  │  │  OpenCV      │  │  Extensions  │  │                              │ │   │
│  │  │  (SendInput) │  │  Git         │  │                              │ │   │
│  │  └──────────────┘  └──────────────┘  └─────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      Memory & Knowledge Layer                         │   │
│  │                                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────────┐ │   │
│  │  │  Structural   │  │  AgentMemory │  │  LLM Wiki                   │ │   │
│  │  │  Memory       │  │  (MCP :3111) │  │  (projects/llm_wiki/)      │ │   │
│  │  │  (SQLite)     │  │              │  │                              │ │   │
│  │  │              │  │  BM25+Vector │  │  Self-building knowledge    │ │   │
│  │  │  WORK        │  │  Graph (RRF) │  │  base from documents        │ │   │
│  │  │  LEARNED     │  │  Auto-capture│  │  Karpathy pattern           │ │   │
│  │  │  KNOWLEDGE   │  │  12 hooks    │  │  Obsidian compatible        │ │   │
│  │  └──────────────┘  └──────────────┘  └─────────────────────────────┘ │   │
│  │                                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────────┐ │   │
│  │  │  Team Chat    │  │  Progress    │  │  Error DB                   │ │   │
│  │  │  (shared-     │  │  Files       │  │  (memory-bank/)            │ │   │
│  │  │  conversations│  │  (progress/) │  │                              │ │   │
│  │  │  /team-chat)  │  │              │  │  Pattern analysis           │ │   │
│  │  │              │  │  Per-agent   │  │  Self-healing               │ │   │
│  │  │  Coordination│  │  tracking    │  │  Error classification       │ │   │
│  │  └──────────────┘  └──────────────┘  └─────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      External Tools Layer                             │   │
│  │                                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────────┐ │   │
│  │  │  CloakBrowser │  │  TradingView │  │  Supertonic TTS             │ │   │
│  │  │  (Stealth     │  │  MCP         │  │  (31 languages,            │ │   │
│  │  │   Chromium)   │  │  (Real-time  │  │   ONNX, on-device)         │ │   │
│  │  │              │  │   market     │  │                              │ │   │
│  │  │  Bot bypass   │  │   data +     │  │  Content farm voice         │ │   │
│  │  │  30/30 tests  │  │   30+        │  │  generation                 │ │   │
│  │  │              │  │   indicators) │  │                              │ │   │
│  │  └──────────────┘  └──────────────┘  └─────────────────────────────┘ │   │
│  │                                                                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────────────────┐ │   │
│  │  │  TensorTrade  │  │  Scrapling   │  │  Agent Hooks                │ │   │
│  │  │  (RL trading  │  │  (Adaptive   │  │  (Pre/post tool use,       │ │   │
│  │  │   framework)  │  │   scraping)  │  │   session start/end)       │ │   │
│  │  └──────────────┘  └──────────────┘  └─────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. DATA FLOW / TOURING GRAPH

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA FLOW THROUGH SYSTEM                             │
└─────────────────────────────────────────────────────────────────────────────┘

[External Event]
      │
      ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────────────────────────┐
│  Event       │────▶│  Topological  │────▶│  Subscribers (Observers)        │
│  Fabric      │     │  Router       │     │                                  │
│  ingest()    │     │  (Dijkstra)   │     │  ┌────────┐ ┌────────┐ ┌──────┐ │
│              │     │              │     │  │Trading │ │Repair  │ │Memory│ │
│  Validate    │     │  Broadcast   │     │  │Observer│ │Observer│ │Obs.  │ │
│  Classify    │     │  Targeted    │     │  └────────┘ └────────┘ └──────┘ │
│  Timestamp   │     │  Path-based  │     └─────────────────────────────────┘
└──────┬───────┘     └──────────────┘
       │
       ├──────────────────────────────────────┐
       │                                      │
       ▼                                      ▼
┌──────────────┐                    ┌──────────────────┐
│  Event        │                    │  Structural       │
│  Persistence  │                    │  Memory           │
│  (SQLite)     │                    │                   │
│              │                    │  WORK → LEARNED    │
│  Compress     │                    │    → KNOWLEDGE    │
│  old events   │                    │                   │
│  TTL expiry   │                    │  FTS5 search      │
└──────────────┘                    │  Graph traversal  │
                                    │  Wiki export      │
                                    └──────────────────┘
       │                                      │
       ▼                                      ▼
┌──────────────┐                    ┌──────────────────┐
│  WebSocket    │                    │  Observer         │
│  Stream       │                    │  Integration      │
│              │                    │                   │
│  Real-time    │                    │  exec_and_emit    │
│  broadcast    │                    │  kill_and_emit    │
│  to frontend  │                    │  install_and_emit │
└──────────────┘                    └──────────────────┘
       │                                      │
       ▼                                      ▼
┌──────────────┐                    ┌──────────────────┐
│  OCE Frontend │                    │  SRRA-OPH         │
│  (Next.js     │                    │  Substrate        │
│   :3000)      │                    │                   │
│              │                    │  77 tests          │
│  Dashboard    │                    │  Phases 1-9        │
│  Chat UI      │                    │  Entropy economics │
│  Observer     │                    │  Attractor reason. │
│  panels       │                    │  Repair patches    │
└──────────────┘                    └──────────────────┘
```

---

## 3. LOGIC CHAIN (Execution Flow)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         OWL EXECUTION LOGIC CHAIN                            │
└─────────────────────────────────────────────────────────────────────────────┘

[Start Session]
      │
      ▼
[Read OPERATOR_RULES.md] ──▶ [Read AGENTS.md] ──▶ [Read team-chat.md]
      │                            │                       │
      ▼                            ▼                       ▼
[Load Context]              [Check Phase Status]    [Check Sub-agents]
      │                            │                       │
      ▼                            ▼                       ▼
[Health Check]              [Identify Blockers]     [Assess Progress]
      │                            │                       │
      └──────────────┬─────────────┘                       │
                     │                                     │
                     ▼                                     │
            [Prioritize Tasks] ◀───────────────────────────┘
                     │
                     ▼
         ┌───── Can I do it directly? ─────┐
         │                                   │
         ▼                                   ▼
    [YES: Build directly]              [NO: Spawn sub-agent]
         │                                   │
         ▼                                   ▼
    [Write code/docs]                  [Create task spec]
    [Run tests]                        [Spawn with timeout]
    [Update team-chat]                 [Monitor progress]
         │                                   │
         ▼                                   ▼
    [Verify output]                    [Verify output]
    [Update progress]                  [Update progress]
         │                                   │
         └──────────────┬───────────────────┘
                        │
                        ▼
               [More tasks?] ──YES──▶ [Prioritize Tasks]
                        │
                        NO
                        │
                        ▼
               [Health Check]
                        │
                        ▼
               [Update team-chat]
                        │
                        ▼
               [Yield / Wait for events]


┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUB-AGENT LOGIC CHAIN                                │
└─────────────────────────────────────────────────────────────────────────────┘

[Receive Task]
      │
      ▼
[Read context files] ──▶ [Understand scope] ──▶ [Identify deliverable]
      │                                                │
      ▼                                                ▼
[Check existing code]                             [Write code/docs]
      │                                                │
      ▼                                                ▼
[Build incrementally]                             [Run tests]
      │                                                │
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

## Workspace Map

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

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-05-16 | Initial CODEMAP |
| 2.0.0 | 2026-05-16 | Added mermaid graphs, updated for Phase 4 completion, added logic chains |
