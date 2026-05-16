# AGENTS.md — SRRA-OPH Team Manifest

> **Last Updated:** May 16, 2026
> **Current Phase:** Phase 8 — Sovereign Coevolution (Active)

---

## Team Roster

| Tag | Agent | Role | Progress File |
|-----|-------|------|---------------|
| 🔵 CC | Claude Code | Overseer / Architecture / Core Build | `progress/claude-code-progress.md` |
| 🟣 OC | OpenClaw | Analysis / Planning / Coordination | `progress/openclaw-progress.md` |
| 🟠 OC2 | OpenClaw 2 | Execution / Testing / Reporting / Discord | `progress/openclaw-2-progress.md` |
| 🟡 AS | Assistant Manager | Context Monitoring / Quality / Documentation | `progress/assistant-progress.md` |
| 🔴 PM | Polymorph (Hawk) | Debugger / Tool & Skill Builder | `progress/polymorph-progress.md` |
| 🟢 RL | OWL (Research Lead) | Research / DSPy Integration / Pipeline Optimization | `progress/rl-progress.md` |

---

## Communication Protocol

1. **All agents post to `shared-conversations/team-chat.md`** — this is the coordination hub
2. **All agents write to their own sub-progress file** — never touch another agent's file
3. **Run `python tools/progress-sync.py --force`** after completing significant work
4. **CC manages phase gates** — only CC can advance phases via `python tools/phase-gate.py --advance`
5. **Code Flow:** CC builds → AS tests → PM debugs → HR executes

---

## Phase Status

| Phase | Status | Tests |
|-------|--------|-------|
| Phase 0 (Foundational Reality Check) | ✅ Complete | — |
| Phase 1 (Minimal Observer Mesh) | ✅ Complete | 3/3 stable |
| Phase 2 (Reconstruction + Recoverability) | ✅ Complete | 7/7 passing |
| Phase 3 (Emergent Topology) | ✅ Complete | 4/4 passing |
| Phase 3 Book 2 (Updated Architecture) | ✅ Complete | 6/6 passing |
| Phase 4 (Workspace Integration) | ✅ Complete | 6/6 passing |
| Phase 5 (Long-Horizon Continuity) | ✅ Complete | 5/5 passing |
| Phase 6 (Recursive Topology Introspection) | ✅ Complete | 5/5 passing |
| Phase 7 (Overlap Cognition) | ✅ Complete | 6/6 passing |
| Phase 8-9 | ⏳ Planned | AS resource assessment complete |

**Total: 39 tests passing**

---

## Key Files

| File | Purpose |
|------|---------|
| `srrs_opc/` | SRRA-OPH core module (33 Python files) |
| `srrs_opc/tests/` | Test suites (7 files, 39 tests) |
| `srrs_opc/docs/` | Design docs, resource assessment |
| `progress/` | Agent sub-progress files + memory |
| `shared-conversations/team-chat.md` | Team coordination hub |
| `tools/progress-sync.py` | Auto-sync agent progress → main files |
| `tools/phase-gate.py` | Phase transition manager |
| `tools/cc-workflow.py` | CC continuous workflow engine |
| `.agent-tags.json` | Agent registry |
| `.phase-state.json` | Phase tracking state |

---

## Memory Architecture

Each agent has two memory layers:
1. **Working Memory** (`progress/{agent}-memory.md`) — auto-synced every 3 updates, compact & current
2. **Persistent Memory** (`.openclaw/MEMORY.md`, `.hermes/MEMORY.md`, etc.) — hand-managed, append-only sync

The workspace files ARE the global memory. Keep them updated.

---

## Build Rules

1. **No global state** — every node self-stabilizes
2. **Repair before scale** — never optimize throughput before stabilization
3. **Memory must compress** — linear growth is failure
4. **Consensus must emerge** — never hardcode truth authority
5. **Test everything** — all code must have tests before advancing phases
