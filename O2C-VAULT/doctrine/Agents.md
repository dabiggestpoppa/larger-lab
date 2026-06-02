# Agents

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine

# AGENTS.md — V3 Cognitive Field Team Manifest

> **Last Updated:** May 31, 2026 | **Phase:** Post-Port Integration Complete
> **Architecture:** Unified Field (OCE + O2C + SRRA-OPH + Obsidian + CARE + Quant Lab)

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

**Before spawning ANY process, check for duplicates:**
```powershell
# Kill stale terminals (>30min)
Get-Process powershell -EA 0 | Where-Object { (New-TimeSpan -Start $_.StartTime).TotalMinutes -gt 30 } | Stop-Process -Force
# Check port before starting service
Get-NetTCPConnection -LocalPort <PORT> -EA 0
```
**Max 3 PowerShell + 2 Python** processes at any time. **NEVER use `Start-Process -FilePath "openclaw"`** — use `node` + `openclaw.mjs` directly (the .ps1 wrapper opens in VS Code notes).

### ⚡ Windows Execution Rule (MANDATORY)
ALWAYS use PowerShell. Never use `cmd.exe` / `subprocess.run(..., shell=True)`.

## Team Roster
| Tag | Agent | Role | Status |
|-----|-------|------|--------|
| 🔵 CC | Claude Code | Overseer / Architecture | Active |
| 🟠 OC2 | OWL | Primary Operator / Orchestrator | Active |
| 🟡 AS | Assistant Manager | Context Monitoring / Quality | Standby |
| 🔴 PM | Polymorph | Debugger / Tool Builder | Active |
| 🔴 PM2 | Polymorph 2 | Experimental Track / Frontend P3-5 | Standby |
| 🟢 RL | OWL (Research Lead) | Research / DSPy | Standby |
| 🟦 Copilot | GitHub Copilot | Test Monitoring / Autopilot | Standby |
| 🟢 HR | Hermes | Execution / Backtesting / Reporting | **Active** |
| 🐕 Watchdog | `tools/gateway_watchdog.py` | OC2 + Hermes 24/7 monitor | **Active** |

## 📋 Current Team Tasks (2026-05-28)
**All agents: Check `shared-conversations/team-chat.md` for detailed assignments.**
- **CC:** O-6 tests fixed (52/52 passing) — O-7 planning next
- **OC2:** O-5 complete — supporting O-6 integration
- **AS:** O-7 Persistent Field documentation complete — ready for build
- **PM:** O-6 Local Substrate complete — O-7 backend build next
- **PM2:** O-6 frontend complete — O-7 frontend build next
- **RL:** O-7 research
- **Copilot:** 11.1-B monitoring

## Memory Relay System
After EVERY code edit: Update own progress file + memory file. After every 5 code edits: Post summary to `shared-conversations/team-chat.md`.

## Phase Status
| System | Tests | Status |
|--------|-------|--------|
| SRRA-OPH | 57/57 | ✅ Complete |
| OCE | 1403 | ✅ Complete |
| V3 P1-10 | 1460 | ✅ Complete |
| Phase 11 Short-Run | All | ✅ Complete (11.1-A, 11.1-D, 11.1-E, 11.2, 11.3, 11.4.1, 11.4.2, 11.2-3B) |
| Phase 11.1-B 72h | 7 chk | 🔄 PAUSED (checkpoint 7, drift fix applied) |
| Phase 11.5 | — | ⏳ Queued (needs 11.1-B) |
| SRRA-OPH Frontend | 13 pages | ✅ Complete (all 5 phases) |
| OCE Frontend | All pages | ✅ Complete |

### Observer Core Phases
| Phase | Backend | Frontend | Tests | Status |
|-------|---------|----------|-------|--------|
| O-1 | 9/9 | 10/10 | 42/42 | ✅ Complete |
| O-2 | 10/10 | 7/7 | needs alignment | ✅ Complete |
| O-3 | 10/10 | 8/8 | needs alignment | ✅ Complete |
| O-4 | 11/11 | 9/9 | 14/14 | ✅ Complete |
| O-5 | 12/12 | 12/12 | — | ✅ Complete |
| O-6 | 11/11 | 8/8 | 52/52 | ✅ Complete |
| O-7 | 12/12 | 8/8 | 35/35 | ✅ Complete |

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

LINKS:
[[Codemap]]
[[01 System Overview]]
[[02 Agent Workflow]]
[[03 Srra Topology]]
[[04 Data And Storage]]
[[Api Reference]]
[[Cg 1 Mermaid Specs]]
[[Cg 1 Revised]]
[[Cg 2 Mermaid Specs]]
[[Cg 2 World Model Activation]]
[[Cg 3 Openclaw Anchor]]
[[Cg 3 Relational Topology]]
[[Cg 4 Execution Intelligence]]
[[Cg 4 Mermaid Specs]]
[[Cg 5 Continuity Intelligence]]
[[Cg 6 Meta Cognition]]
[[Cg 7 Multi Scale Orchestration]]
[[Cg 8 Operator Coevolution]]
[[Cg 9 Autonomous Strategic Field]]
[[Chaos Scenarios]]
[[Chat Response Bug Diagram]]
[[Cleanup Report]]
[[Code Quality]]
[[Contributing]]
[[Debugging]]
[[Domain Micro Doctrines]]
[[Harness Engineering]]
[[Heartbeat]]
[[Identity]]
[[Master Plan 2026 05 18]]
[[Master Plan Observer Core]]
[[Master Prompt]]
[[Module Guide]]
[[Observer Core Workspace State]]
[[Oce Unified Frontend Plan]]
[[O 6 Implementation Plan]]
[[O 7 Persistent Field Doc]]
[[Phase10]]
[[Phase Breakdown]]
[[Principles]]
[[Project Progress Clean]]
[[Quality Review]]
[[Quality Review Feedback]]
[[Readme]]
[[Soul]]
[[Sub Agent Rules]]
[[Team Tasks]]
[[Telegram Bot Setup]]
[[Testing]]
[[Test Manual]]
[[Tools]]
[[Topological Cognition Architecture]]
[[User]]
[[Workspace State]]
[[Action]]
[[Cal]]
[[Elevenlabs]]
[[Formatting]]
[[Skill]]
[[System]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Memory]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Journal]]
