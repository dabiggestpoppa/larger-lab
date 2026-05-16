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
| Phase 8 (Sovereign Coevolution) | ✅ Complete | 6/6 passing |
| Phase 9 (Entropy Economics) | 🔄 In Progress | 32/32 passing |

**Total: 77 tests passing**

---

## OCE Implementation (Parallel Track)

| Phase | Status | Lead |
|-------|--------|------|
| OCE Phase 1 (Continuity Shell) | 🔄 In Progress | CC |
| OCE Phase 2 (Event Fabric) | Pending | OC |
| OCE Phase 3 (Observer Runtime) | Pending | OC2 |
| OCE Phase 4 (Structural Memory) | Pending | AS |
| OCE Phase 5 (Observability) | Pending | PM |
| OCE Phase 6 (Execution Substrate) | Pending | RL |

**OCE Project:** `oce/` directory

**Phase 1 Progress:**
- ✅ Project structure created
- ✅ FastAPI backend scaffolded (`oce/backend/main.py`)
- ✅ Next.js frontend scaffolded (`oce/frontend/package.json`)
- ✅ SRRA-OPH substrate adapter (`oce/backend/srrs_adapter.py`)

---

## Key Files

| File | Purpose |
|------|---------|
| `srrs_opc/` | SRRA-OPH core module (33 Python files) |
| `srrs_opc/tests/` | Test suites (7 files, 39 tests) |
| `srrs_opc/docs/` | Design docs, resource assessment |
| `oce/` | Operator Continuity Engine project |
| `oce/backend/` | FastAPI Continuity Core API |
| `oce/frontend/` | Next.js Shell UI |
| `progress/` | Agent sub-progress files + memory |
| `shared-conversations/team-chat.md` | Team coordination hub |
| `tools/progress-sync.py` | Auto-sync agent progress → main files (7-update threshold) |
| `tools/memory_sync_daemon.py` | Background memory tracker (60s scan, 7-update sync, 20-entry summarize) |
| `tools/summarize_progress.py` | LLM progress summarization (Nemotron 3 Nano Omni via OpenRouter) |
| `tools/workspace_cleanup.py` | Loose file detection, oversized progress, empty/missing dirs |
| `tools/phase-gate.py` | Phase transition manager |
| `tools/cc-workflow.py` | CC continuous workflow engine |
| `AGENT_MOVEMENT.md` | Agent movement protocol, shared space etiquette, SRRA compliance |
| `.agent-tags.json` | Agent registry |
| `.phase-state.json` | Phase tracking state |

---

## Memory Architecture

Each agent has two memory layers:
1. **Working Memory** (`progress/{agent}-memory.md`) — auto-synced every 7 updates, compact & current
2. **Persistent Memory** (`.openclaw/MEMORY.md`, `.hermes/MEMORY.md`, etc.) — hand-managed, append-only sync

The workspace files ARE the global memory. Keep them updated.

---

## Workspace Optimization (Active)

The workspace self-sustains through automated memory management:

| Component | File | Purpose |
|-----------|------|---------|
| Memory Sync Daemon | `tools/memory_sync_daemon.py` | Background scanner (60s), syncs at 7 updates, summarizes at 20 entries |
| Progress Summarizer | `tools/summarize_progress.py` | LLM compression via Nemotron 3 Nano Omni (OpenRouter, free) |
| Workspace Cleanup | `tools/workspace_cleanup.py` | Detects loose files, oversized progress, empty/missing dirs |
| Agent Movement Protocol | `AGENT_MOVEMENT.md` | Shared movement patterns, etiquette, SRRA compliance |
| Daily Cron (OC2) | 7am daily | Full pipeline: sync → summarize → cleanup → team-chat |
| Chat Sync | `tools/chat_sync.py` | Auto-syncs team-chat.md → agent memory files every 5 messages |

**Sync threshold:** 7 updates (was 3). **Summarize threshold:** 20 entries.
All agents maintain own memory hygiene. See `AGENT_MOVEMENT.md` for full protocol.

## Build Rules

1. **No global state** — every node self-stabilizes
2. **Repair before scale** — never optimize throughput before stabilization
3. **Memory must compress** — linear growth is failure
4. **Consensus must emerge** — never hardcode truth authority
5. **Test everything** — all code must have tests before advancing phases

## Diagnostic Soft Logic (Not Hard Rules)

> **Source:** OC2 chronic bug postmortem (May 16, 2026) — 8 hours of repair caused by 2 simple config issues that were always visible in the logs.

These are PATTERNS to follow, not rules to obey. They adapt to context.

### The Core Instinct: Read Logs First
When something seems broken, **read the actual error log** — not the health endpoint, not the status page. The answer is always in the logs. Health endpoints say "live" when the agent is dead.

### Diagnostic Sequence (Soft Pattern)
1. **Starting something new** → Read startup logs. Verify EVERY layer: process running, port listening, service ready, agent model loaded, channels connected, can process messages.
2. **Something seems stuck** → Read the error log from the LAST action. Not the health check. The error message is always more specific than your assumption.
3. **Making config changes** → One change at a time. Test. Next change. Never batch config edits.
4. **Stuck >30 minutes** → Stop guessing. Read the log file. The error is always there.
5. **Service won't start** → Check for config schema validation errors FIRST. Invalid keys fail silently.
6. **Behavior doesn't match config** → Check for override files. Agent-level config can override workspace config.

### Why Soft Logic, Not Hard Rules
Hard rules break when the environment changes. Soft logic is a diagnostic PATTERN — it works for ANY service, not just OC2. The pattern is: **observe first, assume second, verify always**.

### Tools That Embed This Pattern
- `tools/oc2-start.cmd` — validates config + API key + agent model BEFORE starting
- `tools/oc2-doctor.cmd` — full 6-layer diagnostic on demand
- `tools/oc2-watchdog.py` — monitors context usage, alerts at 75%/90%/95%
- `tools/oc2-context-monitor.py` — session-level context tracking
