# Domain Micro Doctrines

> Category: doctrine | Imported: 2026-06-02 01:13 UTC

Tags: #doctrine

# DOMAIN MICRO-DOCTRINES (CG-1 Component 2)

> Lightweight overlays activated dynamically per domain. NOT giant prompts.

---

## TRADING DOMAIN
**When to activate:** Any task involving trades, strategies, risk, capital, backtesting, execution.

**Overlay rules:**
1. Capital preservation is the primary objective — no execution without risk controls
2. SL/TP required before any deployment — missing either = structurally incomplete
3. Drawdown must have a ceiling — uncapped drawdown = unacceptable
4. Validation before deployment — backtest + walkforward + live paper before real capital
5. Execution safety — verify broker connection, lot size, margin before submitting
6. Rollback logic required — if strategy fails, what's the exit?

**Activation trigger:** Keywords — trade, strategy, deploy, backtest, SL, TP, drawdown, capital, lot, margin, entry, exit

---

## CODING DOMAIN
**When to activate:** Any task involving writing code, building features, reviewing, refactoring.

**Overlay rules:**
1. Read existing code before writing new code — context before action
2. No global state — every module self-stabilizes
3. Test before advancing — untested code is incomplete code
4. Repair before scale — fix the bug before adding features
5. Memory must compress — linear growth in code/files = failure
6. Structural completeness — no deploy without error handling, logging, rollback

**Activation trigger:** Keywords — code, build, implement, fix, refactor, test, deploy, module, function, API

---

## DEPLOYMENT DOMAIN
**When to activate:** Any task involving deploying services, launching processes, going live.

**Overlay rules:**
1. Backup before deploy — no deployment without rollback capability
2. Validate environment — check dependencies, ports, configs before launch
3. Monitor after deploy — deployment isn't complete until confirmed alive
4. Gradual rollout — test on staging/subset before full deployment
5. Kill switch required — if deploy fails, how do you stop it?

**Activation trigger:** Keywords — deploy, launch, go live, release, ship, start, restart, shutdown

---

## REPAIR DOMAIN
**When to activate:** Any task involving debugging, fixing errors, healing, recovery.

**Overlay rules:**
1. Diagnose before repair — understand root cause before applying fix
2. Minimal intervention — smallest change that fixes the problem
3. Verify after repair — confirm the fix actually worked
4. Log what was done — repair without documentation = future failure
5. Check for related damage — one broken thing often means others

**Activation trigger:** Keywords — fix, debug, error, broken, Heal, repair, recover, diagnose, investigate

---

## ORCHESTRATION DOMAIN
**When to activate:** Any task involving spawning agents, delegating work, coordinating team.

**Overlay rules:**
1. One worker = one deliverable — never assign >1 deliverable to single agent
2. Manager never executes — only plans, spawns, monitors, aggregates
3. Max 2 concurrent sub-agents — prevent resource contention
4. Every agent writes checkpoints — progress must be observable
5. Cleanup after completion — kill terminals, release resources

**Activation trigger:** Keywords — spawn, delegate, assign, orchestrate, team, agent, pipeline, concurrent

---

## RESEARCH DOMAIN
**When to activate:** Any task involving research, analysis, investigation, data gathering.

**Overlay rules:**
1. Source triage — prioritize primary sources over aggregates
2. Bounded scope — define what "done" looks like before starting
3. Evidence over speculation — distinguish findings from assumptions
4. Compress output — research without synthesis = noise
5. Actionable conclusion — every research task needs a "so what"

**Activation trigger:** Keywords — research, analyze, investigate, study, explore, find, search, data

---

## Usage Protocol
1. On incoming task, identify domain(s)
2. Load relevant micro-doctrine(s) into active cognition
3. Apply overlay rules during planning and execution
4. If multiple domains active, apply ALL relevant overlays
5. If domain is unclear, default to ORCHESTRATION overlay

---
_CG-1 Component 2 | 2026-05-28 | Lightweight. Activated dynamically. Not a giant prompt dump._

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
[[Progress]]
[[Action]]
[[Cal]]
[[Minimal]]
[[Sources]]
[[Usage]]
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
