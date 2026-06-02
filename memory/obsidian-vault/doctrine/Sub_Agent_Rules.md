# Sub Agent Rules

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine

# Sub-Agent Governance Rules

> **Purpose**: Prevent runaway agent proliferation, topology fragmentation, entropy accumulation
> **Max Concurrent Sub-Agents**: 5
> **Source**: MAD's operator rules + master prompt, 2026-05-16

---

## SPAWN RULES

1. **Maximum 5 concurrent sub-agents** — Hard limit. Wait if at capacity.
2. **Each sub-agent gets**:
   - Clear task description with specific deliverable
   - Success criteria (what "done" looks like)
   - Max runtime expectation (15 min soft limit)
   - Output format specification
   - Which file(s) to create/modify
3. **Sub-agents CANNOT spawn other sub-agents** — No recursive proliferation
4. **Sub-agents report to team-chat** with their tag (e.g., `[Sub-CC]`)
5. **Log every spawn** in `progress/rl-progress.md`

## MONITORING RULES

1. **Check status every 5 minutes** — Use `subagents(action=list)`
2. **If sub-agent runs >15 min without progress** — Investigate via `sessions_history`
3. **If sub-agent fails** — Assess root cause. Do NOT immediately retry same approach.
4. **If sub-agent is stuck** — Kill it, break task into smaller pieces, spawn new one

## COMPLETION RULES

1. **Sub-agents post results to team-chat** with their tag
2. **OWL verifies output** before integrating into codebase
3. **Sub-agents update their own progress file** (`progress/sub-*-progress.md`)
4. **Run `python tools/progress-sync.py --force`** after significant work
5. **Log completion** in `progress/rl-progress.md`

## TASK PRIORITY FRAMEWORK

When deciding what to work on:
1. **Continuity stability** — Fix broken tests, repair bugs first
2. **Entropy governance** — Clean up dead code, deduplicate, compress
3. **Strategic attractor alignment** — Does this serve MAD's objectives?
4. **Bounded execution** — Can this be done safely within constraints?

## PROHIBITED ACTIONS (SUB-AGENTS)

- Do NOT modify `AGENTS.md`, `OPERATOR_RULES.md`, or safety rules
- Do NOT spawn other sub-agents
- Do NOT execute unrestricted shell commands
- Do NOT modify OpenClaw config files
- Do NOT access credentials or API keys
- Do NOT operate outside the workspace directory

## SUB-AGENT TEMPLATE

When spawning a sub-agent, use this structure:
```
You are [TAG]. Your ONLY task is to [SINGLE DELIVERABLE].

## Task: [Clear description]
- File to create: [path]
- Success criteria: [testable outcomes]
- Max runtime: [time estimate]

## Constraints
- Write under [N] lines
- Use only stdlib (unless specified)
- Do NOT modify files outside [scope]
- Report to team-chat with tag [TAG]

## Before Starting
1. Read [relevant context files]
2. Verify [prerequisites]
3. Post first update to team-chat as [TAG]
```

LINKS:
[[Codemap]]
[[01 System Overview]]
[[02 Agent Workflow]]
[[03 Srra Topology]]
[[04 Data And Storage]]
[[Agents]]
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
[[Operator Rules]]
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
[[Team Tasks]]
[[Telegram Bot Setup]]
[[Testing]]
[[Test Manual]]
[[Tools]]
[[Topological Cognition Architecture]]
[[User]]
[[Workspace State]]
[[Agent Topology]]
[[Hermes Agent Activation Note]]
[[Hermes Agent Test]]
[[Hermes Agent Test Note]]
[[Progress]]
[[Action]]
[[Description]]
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
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Multi Agent Coordinator]]
