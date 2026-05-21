# TOOLS.md — Larger-Lab Tool Reference

> **Last Updated:** 2026-05-21
> **Purpose:** Quick reference for all tools, paths, and configurations
> **Policy:** Keep <10K chars. Full details in docs/ subdirectories.

---

## Workspace Essentials

| Path | Purpose |
|------|---------|
| `C:\Users\wifik\Desktop\projects\larger-lab` | Main workspace root |
| `oce/` | Operator Continuity Engine (V3 cognitive field) |
| `oce/backend/` | FastAPI backend (main.py, event_fabric.py, observer_runtime.py) |
| `srrs_opc/` | SRRA-OPH core (33 modules, 56 tests) |
| `tools/` | Python/JS automation tools |
| `skills/` | Agent skills (57 active) |
| `docs/` | Documentation (TESTING, DEBUGGING, API_REFERENCE, MODULE_GUIDE) |
| `shared-conversations/` | Team chat hub |
| `progress/` | Agent sub-progress files |
| `logs/` | System logs (hermes-watchdog, oc2-monitor) |
| `memory-bank/` | Error DB, errors-and-solutions, gateway failures |

## Key Tools (Full list: docs/TOOLS_FULL.md)

| Tool | Path | Purpose |
|------|------|---------|
| Terminal Cleanup | `tools/terminal_cleanup.py` | Kill stale python/node processes |
| Progress Sync | `tools/progress-sync.py` | Agent progress → memory auto-sync |
| Self Heal | `tools/self_heal.py` | Log scanner, error classifier, auto-fixer |
| Phase Gate | `tools/phase-gate.py` | Phase transition manager |
| Arch Commit | `tools/arch-commit.py` | Post-change architecture alignment |
| Hermes Watchdog | `tools/hermes-watchdog.py` | OWL health monitor |
| Doctor | `tools/doctor.py` | System diagnostic + prescriptions |

## Ports

| Port | Service |
|------|---------|
| 18790 | OpenClaw gateway (OC2, primary) |
| 3000 | OCE frontend (Next.js) |
| 8000 | OCE backend (FastAPI) |
| 8001 | SRRA API |
| 8002 | DMR Dashboard |
| 3111 | AgentMemory server |

## Agent Registry

| Tag | Agent | Role | Progress File |
|-----|-------|------|---------------|
| 🔵 CC | Claude Code | Overseer / Architecture | `progress/claude-code-progress.md` |
| 🟠 OC2 | OWL | Primary Operator / Orchestrator | `progress/openclaw-2-progress.md` |
| 🟡 AS | Assistant Manager | Context Monitoring / Quality | `progress/assistant-progress.md` |
| 🔴 PM | Polymorph (Hawk) | Debugger / Tool Builder | `progress/polymorph-progress.md` |
| 🟢 RL | OWL (Research Lead) | Research / DSPy | `progress/researcher-progress.md` |

## Key Config Files
| File | Purpose |
|------|---------|
| `~/.openclaw-2/openclaw.json` | OpenClaw gateway config |
| `pyproject.toml` | Python dependencies and project config |
| `.agent-tags.json` | Agent registry |
| `.phase-state.json` | Phase tracking state |

## Operator Rules
- **See:** `OPERATOR_RULES.md` for complete rules
- **MAD Directive:** OWL is an ORCHESTRATOR, not an execution worker
- **Max concurrent sub-agents:** 5

---
*Compressed: 2026-05-21 — Old TOOLS.md was 13.8KB, now <4KB*
*Full tool list archived to: docs/TOOLS_FULL.md*
