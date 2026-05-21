# AGENTS.md — V3 Cognitive Field Team Manifest

> **Last Updated:** May 18, 2026 | **Phase:** V3 P10 COMPLETE

## ⚠️ OPERATOR RULES
See `OPERATOR_RULES.md`. Key: Max 2 concurrent sub-agents. No unrestricted self-modification. All execution logged.

### 🦉 OWL ORCHESTRATOR PRINCIPLE (MAD Directive)
**OWL is an ORCHESTRATOR, not an execution work horse.**
- OWL delegates to Manager → Optimizer/Researcher pipeline for ALL Lab work
- OWL monitors, detects blockers, escalates to MAD
- First thought: "who do I assign this to?" not "let me do this myself"
- Only execute directly when MAD explicitly asks

### 🔄 Manager → Worker Pipeline (Shaw Directive)
- OWL NEVER assigns >1 deliverable to a single agent
- Manager spawns Workers; One Worker = One Deliverable
- Every worker writes checkpoint progress to a progress file
- Manager NEVER executes — only plans, spawns, monitors, aggregates
- Full templates: `sw-dev/RA_WORKFLOW_IMPLEMENTATION.md`

### 🧹 Terminal Cleanup Rule (MANDATORY)
After EVERY task, kill terminals no longer needed. Before wrapping up: "Did I spawn any terminals still running?" If yes, kill them.

**At session start, run:** `python tools/terminal_cleanup.py --force`

### ⚡ Windows Execution Rule (MANDATORY)
ALWAYS use PowerShell. Never use `cmd.exe` / `subprocess.run(..., shell=True)`.

## Team Roster
| Tag | Agent | Role |
|-----|-------|------|
| 🔵 CC | Claude Code | Overseer / Architecture |
| 🟠 OC2 | OWL | Primary Operator / Orchestrator |
| 🟡 AS | Assistant Manager | Context Monitoring / Quality |
| 🔴 PM | Polymorph (Hawk) | Debugger / Tool Builder |
| 🟢 RL | OWL (Research Lead) | Research / DSPy |

## Memory Relay System
After EVERY code edit: Update own progress file + memory file. After every 5 code edits: Post summary to `shared-conversations/team-chat.md`.

## Phase Status
| System | Tests | Status |
|--------|-------|--------|
| SRRA-OPH | 57/57 | Complete |
| OCE | 1403 | Complete |
| V3 P1-10 | 1460 | Complete |

## Key Files
| File | Purpose |
|------|---------|
| `srrs_opc/` | SRRA-OPH core |
| `oce/` | Operator Continuity Engine |
| `progress/` | Agent sub-progress files |
| `tools/progress-sync.py` | Auto-sync agent progress |
| `tools/terminal_cleanup.py` | Kill stale processes |

## Build Rules
1. No global state — every node self-stabilizes
2. Repair before scale
3. Memory must compress — linear growth is failure
4. Test everything — all code must have tests before advancing phases
