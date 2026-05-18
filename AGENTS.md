# AGENTS.md — V3 Cognitive Field Team Manifest

> **Last Updated:** May 18, 2026 | **Phase:** V3 P10 COMPLETE | **SRRA-OPH:** 57/57 tests | **OCE:** 1403 tests

## ⚠️ OPERATOR RULES (READ FIRST)
See `OPERATOR_RULES.md`. Key: Max 2 concurrent sub-agents. No unrestricted self-modification. Repair before expansion. All execution logged. Human is strategic anchor.

### 🦉 OWL ORCHESTRATOR PRINCIPLE (MANDATORY — MAD Directive 2026-05-17)
**OWL is an ORCHESTRATOR, not an execution work horse.**
- OWL does NOT write strategy code, run backtests, or fix bugs directly
- OWL delegates to Manager → Optimizer/Researcher pipeline for ALL Lab work
- OWL monitors progress, detects blockers, escalates to MAD
- OWL updates files, maintains continuity, ensures alignment
- When OWL sees work that needs doing, the FIRST thought is "who do I delegate this to?" not "let me do this myself"
- **Only execute directly when MAD explicitly asks, or when no agent is available and the task is time-critical**

### 🧹 Terminal Cleanup Rule (MANDATORY)
**After EVERY task completion, each agent MUST kill any terminals it spawned that are no longer actively needed.** This includes:
- Test runner terminals (`python -m pytest ...`) — kill after tests complete
- Dev server terminals (`python main.py`, `npm run dev`) — kill when done testing
- Background watchers/monitors — kill when task is complete
- Any `subprocess.Popen()` or `run_in_terminal(async=True)` processes — kill when done

**Before wrapping up ANY task, ask yourself: "Did I spawn any terminals that are still running?" If yes, kill them.**

Stale terminals waste resources, cause port conflicts, and clutter the workspace. Don't leave them for MAD to clean up.

**At session start, run:** `python tools/terminal_cleanup.py --force` to kill any stale processes from previous sessions.

### ⚡ Windows Execution Rule (MANDATORY)
**ALWAYS use PowerShell first for Windows operations.** Windows CMD is too restrictive and causes too many issues. When you need to run commands on Windows:
- Use `run_in_terminal` with PowerShell commands
- Use `subprocess.run(['powershell', '-NoProfile', '-Command', '...'])` in Python scripts
- Never use `cmd.exe` / `subprocess.run(..., shell=True)` unless absolutely necessary
- For process management: `Get-Process`, `Stop-Process`, `taskkill` via PowerShell
- For file operations: `Get-ChildItem`, `Remove-Item`, `Move-Item`, `Set-Content` via PowerShell

## Team Roster
| Tag | Agent | Role |
|-----|-------|------|
| 🔵 CC | Claude Code | Overseer / Architecture |
| 🟠 OC2 | OWL (OpenClaw 2) | Primary Operator / Discord / Telegram |
| 🟡 AS | Assistant Manager | Context Monitoring / Quality |
| 🔴 PM | Polymorph (Hawk) | Debugger / Tool Builder |
| 🟢 RL | OWL (Research Lead) | Research / DSPy |

## Communication Protocol
1. All agents post to `shared-conversations/team-chat.md`
2. All agents write to own sub-progress file only
3. CC manages phase gates
4. Code Flow: CC builds → AS tests → PM debugs → RL researches
5. DO NOT TOUCH OC2's files — OC2 is autonomous

## Memory Relay System
Agent edits code → Updates own progress file → Pushes to workspace-state.md → Other agents read on next session

### Rules (ALL Agents)
1. After EVERY code edit: Update own progress file + memory file
2. After every 5 code edits: Post summary to team-chat.md
3. Before each work session: Read team-chat.md + workspace-state.md
4. Error logging: Any error >2 attempts → log to error-db.json + team-chat.md
5. Memory sync: Push key findings to workspace-state.md

## Phase Status
| System | Phases | Tests | Status |
|--------|--------|-------|--------|
| SRRA-OPH | 1-10 | 57/57 | ✅ Complete |
| OCE | 1-10 | 1403 | ✅ Complete |
| V3 P1-10 | 1-10 | 1460 | ✅ Complete |

## Key Files
| File | Purpose |
|------|---------|
| `srrs_opc/` | SRRA-OPH core (33 Python files) |
| `oce/` | Operator Continuity Engine |
| `progress/` | Agent sub-progress files |
| `shared-conversations/team-chat.md` | Team coordination hub |
| `tools/progress-sync.py` | Auto-sync agent progress (7-update threshold) |
| `tools/terminal_cleanup.py` | Kill stale processes (run at session start) |
| `AGENT_MOVEMENT.md` | Agent movement protocol |
| `.agent-tags.json` | Agent registry |
| `.phase-state.json` | Phase tracking state |

## Memory Architecture
- **Working Memory** (`progress/{agent}-memory.md`) — auto-synced every 7 updates
- **Persistent Memory** (`.openclaw-2/MEMORY.md`) — hand-managed

## Build Rules
1. No global state — every node self-stabilizes
2. Repair before scale
3. Memory must compress — linear growth is failure
4. Consensus must emerge
5. Test everything — all code must have tests before advancing phases

## Diagnostic Soft Logic
1. **Starting something new** → Read startup logs. Verify every layer.
2. **Something stuck** → Read error log from LAST action. Not health check.
3. **Config changes** → One change at a time. Test. Next change.
4. **Stuck >30 min** → Stop guessing. Read the log file.
5. **Service won't start** → Check config schema validation errors FIRST.
6. **Behavior ≠ config** → Check for override files.

## Arch Commit
After any code change affecting architecture:
```bash
python tools/arch-commit.py --agent <TAG> --file "<path>" --change "<description>"
```

## OC2 Restart Rule
When MAD reports OC2 down: (1) `openclaw gateway stop`, (2) `openclaw gateway run --port 18790`, (3) wait 5s, (4) test with `openclaw gateway probe`. Do NOT debug code first. 90% of issues fixed by restart.
