---
name: agent-team-workflow
description: Standard workflow for agents in the larger-lab team. Use when coordinating tasks between CC/OC/HR agents, updating progress, or managing phase transitions.
---

# Agent Team Workflow Skill

## Purpose
Standard operating procedure for the CC/OC/HR agent team. Ensures clean handoffs, no write collisions, and automatic memory sync.

## Agent Roles

| Tag | Agent | Role | Writes To |
|-----|-------|------|-----------|
| 🔵 [CC] | Claude Code | Overseer — architecture, quality gates, phase management | `progress/claude-code-progress.md` |
| 🟡 [AS] | Assistant Manager | Context monitoring, quality checks, optimization, documentation | `progress/assistant-progress.md` |
| 🟣 [OC] | OpenClaw | Analysis — planning, parsing, coordination | `progress/openclaw-progress.md` |
| 🟢 [HR] | Hermes | Execution — backtests, data prep, reporting | `progress/hermes-progress.md` |

## AS (Assistant Manager) Responsibilities

The AS agent is the optimizer and helper during the build process:
1. **Monitor context** across the team so nothing falls through cracks
2. **Handle delegated tasks** from CC (code review, testing, documentation)
3. **Quality-check work** from OC and HR before CC's final review
4. **Keep documentation current** (CODEMAP, WORKFLOW_PROTOCOL, skills)
5. **Flag blockers** to CC immediately
6. **Create and maintain skills** as patterns emerge during the build
7. **Run tests** when code is written — first line of quality

## Workflow: Start of Each Phase

1. **CC (Overseer)** creates task briefs in `tasks/` directory
2. **CC** updates `progress/claude-code-progress.md` with phase kickoff entry
3. **CC** runs `python tools/phase-gate.py --status` to verify phase state
4. **OC** picks up planning tasks, writes plan to sub-progress
5. **HR** picks up execution tasks, runs commands, writes results
6. All agents run `python tools/progress-sync.py` after completing work
7. **CC** reviews merged progress, runs phase gate check

## Progress Update Format

Each entry in sub-progress files MUST follow this format:

```
#### 🔵 [CC] 2026-05-15 22:00:00Z — <brief description>
- What was done
- Files changed
- Next steps
```

## Sync Commands

```bash
# Check sync status (all agents)
python tools/progress-sync.py --status

# Force sync (after completing a task)
python tools/progress-sync.py --force

# Sync specific agent only
python tools/progress-sync.py --agent CC --force
```

## Phase Gate Commands

```bash
# Check current phase
python tools/phase-gate.py --status

# Check if phase criteria met
python tools/phase-gate.py --check

# Advance to next phase (CC only)
python tools/phase-gate.py --advance
```

## Task Runner Commands

```bash
# List all tasks
python tools/task-runner.py --list

# Create a task
python tools/task-runner.py --create

# Run next pending task for an agent
python tools/task-runner.py --run OC

# Complete a task
python tools/task-runner.py --complete TASK-20260515-ABCD --output "Done: results in nautilus/reports/"
```

## CODEMAP Update

After significant architecture changes, run:
```bash
python tools/codemap-updater.py
```

## Key Rules
1. **Never write to another agent's sub-progress file**
2. **Always tag entries** with your agent tag and timestamp
3. **Run progress-sync** after completing any significant work
4. **CC is the only agent** who can advance phases
5. **Persistent memory files** (.openclaw/MEMORY.md, .hermes/MEMORY.md) are NEVER overwritten by sync
