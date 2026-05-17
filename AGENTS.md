# AGENTS.md — SRRA-OPH Team Manifest

> **Last Updated:** May 17, 2026
> **Current Phase:** Post-Deployment Upgrades (Active)
> **SRRA-OPH:** Phases 1-9 complete — 77/77 tests passing
> **OCE Tests:** 426 passing (Phases 1-9 complete)
> **Phases Complete:** OCE 1-9 | **In Progress:** Post-Deployment Upgrades (9 phases) | **Planned:** OCE v3.0
> **Lead:** OWL (MAD away — OWL operating independently)
> **Plan Source:** MAD's original engineering doctrine (phase 6-9 build document)
> **Operator Rules:** `OPERATOR_RULES.md` — Bounded sovereign operational continuity

## ⚠️ OPERATOR RULES (READ BEFORE ANY ACTION)

See `OPERATOR_RULES.md` for complete rules. Key constraints:
- **Max 5 concurrent sub-agents** — prevents topology fragmentation
- **No unrestricted self-modification** — don't modify system prompts/safety rules
- **No infinite agent spawning** — sub-agents cannot spawn sub-agents
- **Repair before expansion** — stability > scale
- **Entropy governance** — compute, attention, sync are finite
- **All execution logged** — observable, replayable, reconstructable
- **Human is strategic anchor** — MAD defines attractors, OWL executes

---

## Team Roster

| Tag | Agent | Role | Progress File |
|-----|-------|------|---------------|
| 🔵 CC | Claude Code | Overseer / Architecture / Core Build | `progress/claude-code-progress.md` |
| 🟠 OC2 | OWL (OpenClaw 2) | **PRIMARY OPERATOR** / Execution / Discord / Telegram | `progress/openclaw-2-progress.md` |
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
| Phase 9 (Entropy Economics) | ✅ Complete | 32/32 passing |

**Total: 77 tests passing**

**OCE Tests: 59 passing (32 event_fabric + 27 adapter)**

---

## OCE Implementation (Parallel Track)

| Phase | Status | Lead |
|-------|--------|------|
| OCE Phase 1 (Continuity Shell) | ✅ Complete | CC |
| OCE Phase 2 (Event Fabric) | ✅ Complete | CC |
| OCE Phase 3 (Observer Runtime) | ✅ Complete | CC |
| OCE Phase 4 (Structural Memory) | ✅ Complete | RL |
| OCE Phase 5 (Observability) | ✅ Complete | RL |
| OCE Phase 6 (Execution Substrate) | ✅ Complete | RL/OC2 |
| OCE Phase 7 (Adaptive Evolution) | ✅ Complete | RL |
| OCE Phase 8 (Sovereign Coevolution) | ✅ Complete | RL |
| OCE Phase 9 (Entropy Economics) | ✅ Complete | RL |
| Post-Deployment Upgrades (9 phases) | 🔄 In Progress | OWL |

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
| `tools/terminal_cleanup.py` | Kill stale python/node processes (run at session start) |
| `tools/phase-gate.py` | Phase transition manager |
| `tools/cc-workflow.py` | CC continuous workflow engine |
| `AGENT_MOVEMENT.md` | Agent movement protocol, shared space etiquette, SRRA compliance |
| `.agent-tags.json` | Agent registry |
| `.phase-state.json` | Phase tracking state |

---

## Memory Architecture

Each agent has two memory layers:
1. **Working Memory** (`progress/{agent}-memory.md`) — auto-synced every 7 updates, compact & current
2. **Persistent Memory** (`.openclaw-2/MEMORY.md`) — hand-managed, append-only sync

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
## Chat Sync | `tools/chat_sync.py` | Auto-syncs team-chat.md → agent memory files every 5 messages; auto-summarizes chat at 100+ messages |
| Chat Summarizer | `tools/chat_summarizer.py` | Condenses team-chat.md every 100 messages; keeps last 30 intact, archives full history |

**Sync threshold:** 7 updates (was 3). **Summarize threshold:** 20 entries.
All agents maintain own memory hygiene. See `AGENT_MOVEMENT.md` for full protocol.

## Arch Commit — Keep Diagrams in Sync

After any code change that affects system architecture, run:
```bash
python tools/arch-commit.py --agent <TAG> --file "<path>" --change "<description>"
```

This will:
1. **Review alignment** — checks file exists, code matches description, correct diagram file, cross-references
2. **Flag mismatches** — warns if the change doesn't match the claimed description
3. **Update diagram** — appends a timestamped change note to the relevant `system-arch/` file
4. **Log the change** — records to `system-arch/arch-changes.jsonl`

Use `--review` for a full alignment check without committing.
Use `--force` to commit even if misaligned (not recommended).

**When to run:** After building new modules, changing API endpoints, modifying agent workflows, updating data pipelines, or any structural change.

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
- `tools/oc2-monitor.py` — cron monitor with auto-repair (--repair flag)
- `tools/error_logger.py` — log errors that persist >2 attempts
- `tools/error_analyzer.py` — detect patterns, suggest skills/logic updates

## Living Error Correction System

> **Purpose:** Capture persistent errors, detect patterns over time, and auto-generate fixes. This is NOT a hard-coded error handler — it's a learning system that grows smarter with every failure.

### How It Works

1. **Every agent logs errors** that persist >2 attempts using `tools/error_logger.py`
2. **PM analyzes patterns** weekly using `tools/error_analyzer.py --pm`
3. **PM suggests skills/logic updates** based on recurring patterns
4. **System self-improves** — common errors get preventive checks, new skills auto-generated

### Error Logging Rules (All Agents)

**When to log:**
- Any error that takes >2 attempts to resolve
- Any error that recurs (same symptom, same service)
- Any critical error (service down, data loss, security issue)

**How to log:**
```python
from error_logger import log_error
log_error(
    agent="PM",                    # Your tag
    service="OC2",                 # What broke
    symptom="Gateway not responding",
    cause="Stuck session",         # Root cause if known
    solution="Kill session",       # How you fixed it
    severity="critical",           # low/medium/high/critical
    attempts=3,                    # How many tries
    tags=["session", "telegram"]   # Categories
)
```

### PM Pattern Analysis (Weekly)

PM runs `python tools/error_analyzer.py --pm` to get:
- **Recurring patterns** — errors that hit multiple agents or repeat over time
- **Skill suggestions** — "Create X-troubleshooter skill for Y service"
- **Logic updates** — "Add Z check to Diagnostic Soft Logic in AGENTS.md"
- **Preventive measures** — "Add pre-flight check before X action"

### Error DB Location

- **Database:** `memory-bank/error-db.json` (auto-synced to repo memory)
- **Human-readable:** `memory-bank/errors-and-solutions.md`
- **Pattern reports:** `memory-bank/error-patterns.md` (generated by PM)

### Pattern → Action Rules

| Pattern | Occurrences | Action |
|---------|-------------|--------|
| Same error, same service | >=3 | PM creates dedicated troubleshooter skill |
| Same error, multiple agents | >=2 | PM updates Diagnostic Soft Logic in AGENTS.md |
| Critical error, any service | >=1 | PM adds pre-flight check to relevant skill |
| High total attempts (>5) | any | PM investigates root cause, suggests prevention |

### ERR-0007: PowerShell Window Flashing Pattern

**Pattern ID:** `WIN-SUBPROCESS-NO-WINDOW`

**Symptom:** PowerShell/cmd windows flashing during background process execution (heartbeat monitoring, OC2 restarts, Telegram alerts)

**Root Cause:** Subprocess calls missing `CREATE_NO_WINDOW` flag, no PID tracking allowing duplicates, inconsistent daemon implementation

**Solution:** 
- ALL `subprocess.run()` on Windows MUST use `creationflags=subprocess.CREATE_NO_WINDOW`
- ALL `subprocess.Popen()` for background processes MUST use `DETACHED_PROCESS | CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP`
- Always implement PID file tracking for daemon scripts
- Use `pythonw` instead of `python` for GUI-less execution

**Prevention:** See `OPERATOR_RULES.md` → "Windows Subprocess Execution Rules"

### Key Principle

**Errors are features, not bugs.** Every error that persists teaches the system something new. The error DB is the team's collective memory of what breaks and how to fix it. Over time, the most common errors get preventive checks, new skills auto-generate, and the system becomes self-healing — without hard-coding specific error handlers.
