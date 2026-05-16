# CODEMAP — Larger-Lab Workspace Guide

> **Last Updated:** 2026-05-16 | **Phase:** OCE Phase 2 (Event Fabric) — Active
> **Purpose:** Quick orientation for agents joining the workspace.

---

## Workspace Map

```
larger-lab/
  ├── config/                  ← Identity, soul, keys, heartbeat, teams, repos, tools
  ├── docs/                    ← Architecture, workflow, progress, codemap
  ├── oce/                     ← Operator Continuity Engine (OCE)
  │   ├── backend/              ← FastAPI Continuity Core
  │   ├── frontend/             ← Next.js Shell UI
  │   └── docs/                 ← OCE documentation
  ├── srrs_opc/                ← SRRA-OPH core (33 Python files, 77 tests)
  ├── tools/                   ← Automation & operator tools
  │   └── operator/             ← PM's operator tools
  ├── progress/                ← Agent sub-progress & memory files
  ├── projects/                ← All external projects (by category)
  │   ├── ads/                  ← Ad projects
  │   ├── content/              ← Content farm projects
  │   ├── trading/              ← Trading projects
  │   ├── ai-tools/             ← AI tools
  │   └── social/               ← Social/discord/telegram
  ├── agent-lab/               ← Agent configurations
  ├── skills/                  ← Workspace skills
  ├── shared-conversations/    ← Team chat
  ├── tasks/                   ← Phase task plans
  ├── data/                    ← Data files
  ├── db/                      ← SQLite databases
  ├── logs/                    ← Log files
  ├── memory/                  ← Memory bank
  ├── notebooks/               ← Jupyter notebooks
  ├── sandbox/                 ← Sandbox/testing
  ├── temp/                    ← Temporary files
  ├── archive/                 ← Archived/scratch files
  │
  ├── AGENTS.md                ← Team manifest
  ├── CLAUDE.md                ← 12-rule behavioral contract
  ├── README.md                ← Project overview
  ├── pyproject.toml           ← Python project config
  ├── requirements.txt         ← Python dependencies
  ├── .env                     ← Environment variables
  ├── .gitignore               ← Git ignore rules
  └── larger-lab.code-workspace ← VS Code workspace
```

---

## System Architecture

```
User
  ↓
OCE Shell UI (Next.js) ←──→ OCE Continuity Core (FastAPI)
  ↓                           ↓
  ├── Event Fabric ←─────── ingest/route/persist/stream
  │       ↓
  │   Observer Runtime (Phase 3)
  │       ↓
  └── SRRA-OPH Substrate (srrs_opc/)
          ↓
      Observer Runtime → Tools / Models / State
```

---

## Key Directories

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `oce/` | Operator Continuity Engine | `backend/main.py`, `backend/event_fabric.py`, `PHASE2_TASKS.md`, `PHASE3_TASKS.md` |
| `srrs_opc/` | SRRA-OPH core (Phases 1-9) | 33 Python files, 77 tests |
| `tools/` | Automation & operator tools | `progress-sync.py`, `chat_sync.py`, `operator/` |
| `progress/` | Agent progress & memory | 6 agents x (progress.md + memory.md) |
| `config/` | Identity & configuration | `IDENTITY.md`, `SOUL.md`, `KEYS.md`, `MEMORY.md` |
| `docs/` | Architecture & progress | `SYSTEM_ARCHITECTURE.md`, `WORKFLOW_PROTOCOL.md`, `CODEMAP.md` |
| `projects/` | External projects | `ads/`, `content/`, `trading/`, `ai-tools/`, `social/` |

---

## Quick Commands

```bash
# Run all SRRA-OPH tests (77 tests)
python -m pytest srrs_opc/tests/ -v

# Run OCE tests (59 tests)
python -m pytest oce/backend/tests/ -v

# Sync progress → memory
python tools/progress-sync.py --force

# Sync team-chat → agent memory
python tools/chat_sync.py --force

# Check phase status
python tools/phase-gate.py --status

# Start OCE backend
cd oce/backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000

# Start OCE frontend
cd oce/frontend && npm run dev
```
