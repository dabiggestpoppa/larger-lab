# SHAW Agent Workflow Analysis

> **Author:** SHAW (Dev Manager, OWL Cognitive Field)
> **Date:** 2026-05-19
> **Purpose:** Diagnose sub-agent timeout failures and define optimal pipeline patterns
> **Audience:** RA (Resource Adapter) for implementation, OWL for enforcement

---

## 1. Root Cause Analysis — Why Agents Timeout

### The Core Problem: Monolithic Task Assignment

Every major timeout failure in this system shares one root cause: **OWL (or a manager) assigns an entire complex task to a single sub-agent with no intermediate checkpoints.** The agent tries to hold the full task context in one execution window and runs out of time.

### Failure Pattern Catalog

| Failed Agent | Task Given | What Happened | Root Cause |
|---|---|---|---|
| `labmanagerfull` | Fix all 10 strategies → convert to Pine | **ZERO fixes completed** | 10 strategies is ~20+ files. Agent spent all time reading/analyzing, never reached writing. No checkpointing. |
| `farmmanagerfull` | Day 2 execution + Day 3 plan | Day 2 files created, **no Day 3 plan** | Day 2 was too broad (6 files across research + creation). Agent burned context on Day 2, had nothing left for Day 3. |
| `ocefrontend` | Upgrade entire OCE frontend (multiple pages, components, features) | **Timed out** | Too many pages + components + features in one shot. No decomposition. |
| `srrafrontend` | Build SRRA-OPH frontend (focused single-system) | **Succeeded** | Narrow scope, single system, clear deliverable. This is the proof that decomposition works. |

### Specific Timeout Mechanisms

1. **Context Saturation:** An agent given "fix 10 strategies" spends 60% of its time just reading and understanding the codebase. By the time it starts working, the execution window is closing.

2. **No Checkpointing:** Agents that don't save intermediate progress lose everything when they timeout. `labmanagerfull` produced ZERO output — meaning if it timed out at minute 14, all work from minutes 0-14 is gone.

3. **Scope Creep Within Task:** Even when an agent starts well, it discovers sub-problems (missing dependencies, broken imports, unclear requirements) and burns time on discovery instead of execution.

4. **Sequential Bottleneck:** A single agent doing N things sequentially has N× the failure probability. If each subtask has a 10% chance of delay, 10 subtasks = 65% chance of at least one delay causing timeout.

5. **No Partial Delivery:** Agents are given all-or-nothing tasks. There's no mechanism to say "I completed 3 of 10 strategies, here's the checkpoint, continue from here."

### The MAD Directive (Correct)

> "Spawn sub agents that mean multiple — stop giving entire task to one. You supposed to pass to manager, the manager then assesses and spawn as many agents as it needs. It's a pipeline not a block task."

This is exactly right. The fix is architectural: **Manager → Workers pipeline**, not **Single Agent → Entire Task**.

---

## 2. Optimal Task Decomposition — Manager → Workers Pipeline

### The Pipeline Model

```
MAD → OWL → MANAGER → [Worker 1, Worker 2, ..., Worker N]
                         ↓           ↓              ↓
                      Output 1   Output 2       Output N
                         ↓           ↓              ↓
                      MANAGER (aggregates) → Reports to OWL
```

### Role Definitions

**OWL (Orchestrator):**
- Receives directive from MAD
- Translates into a task specification file
- Spawns the Manager
- Monitors Manager progress (reads files, doesn't execute)
- Reports results to MAD

**Manager:**
- Receives task specification from OWL
- Analyzes the work and decomposes into subtasks
- Creates a work plan file listing all workers needed
- Spawns workers (up to 5 concurrent)
- Monitors worker output files
- Aggregates results
- Writes completion report
- If a worker fails, respawns only that worker with the checkpoint

**Workers:**
- Receive a SINGLE, FOCUSED subtask
- Execute only that subtask
- Write output to designated file path
- Write checkpoint/progress after each step
- Report completion status

### Decomposition Rules

1. **One Worker = One Deliverable.** If a task produces 3 files, it should be 3 workers (or 1 worker with 3 checkpoints, max).

2. **Max 5 Concurrent Workers.** If a task needs 7 workers, run in batches: 5 first, then 2.

3. **Each Worker Gets ≤ 30 minutes of work.** If a subtask looks like it needs more time, split it further.

4. **Every Worker Writes Checkpoints.** After each file created or modified, write a status line to a progress file.

5. **Manager Never Executes.** The Manager only plans, spawns, monitors, and aggregates. If the Manager is doing actual work, the decomposition is wrong.

### Decomposition Decision Tree

```
Is the task a single action on a single file?
  → YES: One worker, direct spawn by OWL
  → NO: Continue ↓

Can the task be split by OUTPUT FILE?
  → YES: One worker per output file
  → NO: Continue ↓

Can the task be split by COMPONENT/MODULE?
  → YES: One worker per component
  → NO: Continue ↓

Can the task be split by STAGE (analyze → plan → build → test)?
  → YES: Sequential stages, one worker per stage
  → NO: This is a research task — spawn a researcher worker first
```

---

## 3. Agent Prompt Template — Reusable Anti-Timeout Design

### Worker Prompt Template

```
You are [ROLE] — [ONE_SENTENCE_DESCRIPTION].

## YOUR SINGLE TASK
[EXACTLY ONE THING TO DO. NOT THREE THINGS. ONE.]

## INPUT
- Source files: [EXACT PATHS]
- Reference docs: [EXACT PATHS]
- Context file: [PATH TO CONTEXT IF NEEDED]

## OUTPUT
- Write to: [EXACT OUTPUT PATH]
- Format: [EXACT FORMAT EXPECTED]
- Success criteria: [HOW WE KNOW YOU SUCCEEDED]

## CHECKPOINTING (MANDATORY)
After completing each step, append to [PROGRESS_FILE_PATH]:
  [TIMESTAMP] STEP [N]: [WHAT YOU DID] → [FILE CREATED/MODIFIED]

## RULES
1. Do ONLY this task. Do not expand scope.
2. If you encounter a blocker, write BLOCKED: [REASON] to the progress file and stop.
3. Write output incrementally — don't wait until the end.
4. If the task has multiple files, write each file as you complete it.
5. When done, write DONE: [SUMMARY] to the progress file.

## TIMEOUT PREVENTION
- Start writing output within the first 2 minutes
- If analysis exceeds 5 minutes without writing, stop analyzing and start writing
- Prefer partial output over no output
```

### Manager Prompt Template

```
You are [ROLE] — Manager for [PROJECT_NAME].

## YOUR TASK
Coordinate the completion of [HIGH_LEVEL_GOAL] by decomposing into subtasks and spawning workers.

## INPUT
- Task specification: [PATH]
- Existing progress: [PATH TO PROGRESS FILES]

## DECOMPOSITION (DO THIS FIRST — DO NOT SKIP)
1. Read the task specification
2. List all deliverables (files, features, fixes)
3. Group deliverables into independent subtasks (max 30 min each)
4. Write your work plan to [WORK_PLAN_PATH]:
   - Worker 1: [TASK] → [OUTPUT_PATH]
   - Worker 2: [TASK] → [OUTPUT_PATH]
   - ...
5. Identify dependencies (which workers must finish before others start)

## EXECUTION
- Spawn workers in dependency order
- Max 5 concurrent workers
- After each worker completes, verify their output file exists
- If a worker fails, respawn ONLY that worker with the checkpoint

## OUTPUT
- Write completion report to [REPORT_PATH]
- List: completed, failed, blocked items
- Update [MASTER_PROGRESS_FILE]

## RULES
1. You do NOT execute any subtask yourself
2. You decompose FIRST, then spawn
3. You monitor by READING output files, not by guessing
4. If all workers complete, aggregate and report
```

---

## 4. Pipeline Patterns for Common Tasks

### Pattern A: Frontend Builds (Multiple Pages)

**WRONG:** "Build the entire frontend with dashboard, topology, modules, tests, and events pages"

**RIGHT:**
```
Manager: frontend-build-manager
  ├── Worker 1: Dashboard page (/) → oce/frontend/app/page.tsx
  ├── Worker 2: Topology page (/topology) → oce/frontend/app/topology/page.tsx
  ├── Worker 3: Modules page (/modules) → oce/frontend/app/modules/page.tsx
  ├── Worker 4: Tests page (/tests) → oce/frontend/app/tests/page.tsx
  └── Worker 5: Events page (/events) → oce/frontend/app/events/page.tsx
```

**Key insight from srrafrontend success:** It worked because it was a SINGLE system. The ocefrontend failed because it tried to upgrade an entire existing system with unknown broken parts. For upgrades, add a **Stage 0 worker** that audits the existing codebase first, then workers fix specific issues found.

### Pattern B: Backtests (Multiple Strategies)

**WRONG:** "Fix all 10 strategies and convert to Pine Script"

**RIGHT:**
```
Manager: strategy-fix-manager
  ├── Stage 1 — Audit (1 worker):
  │     Worker: Analyze all 10 strategies → write analysis to strategies/audit.md
  │
  └── Stage 2 — Fix (batch of 5, then 5):
          Worker 1: Fix strategy 1 → strategies/strategy_1_pine.pine
          Worker 2: Fix strategy 2 → strategies/strategy_2_pine.pine
          Worker 3: Fix strategy 3 → strategies/strategy_3_pine.pine
          Worker 4: Fix strategy 4 → strategies/strategy_4_pine.pine
          Worker 5: Fix strategy 5 → strategies/strategy_5_pine.pine
          (then repeat for strategies 6-10)
```

**Key insight from labmanagerfull failure:** 10 strategies in one agent = 0 fixes. The agent spent all its time reading. The fix is: audit first (small task), then one strategy per worker (tiny tasks). Even if only 3 of 5 workers in a batch complete, you have 3 fixes instead of 0.

### Pattern C: Research (Multiple Topics)

**WRONG:** "Research competitor landscape, content gaps, and fresh trends"

**RIGHT:**
```
Manager: research-manager
  ├── Worker 1: Competitor deep dive → output/competitor-deep-dive.md
  ├── Worker 2: Content gap analysis → output/content-gap-analysis.md
  └── Worker 3: Fresh trends analysis → output/fresh-trends-analysis.md
```

**Key insight from farmmanagerfull partial success:** The Day 2 files WERE created (6 research + creation files), which means the research workers pattern works. The failure was that Day 3 planning was tacked on as an afterthought. Fix: Day 2 execution and Day 3 plan are SEPARATE tasks with SEPARATE workers.

### Pattern D: File Processing (Large Batches)

**WRONG:** "Process all 500 data files in the dataset"

**RIGHT:**
```
Manager: data-processing-manager
  ├── Worker 1: Process files 001-100 → output/batch-001/
  ├── Worker 2: Process files 101-200 → output/batch-002/
  ├── Worker 3: Process files 201-300 → output/batch-003/
  ├── Worker 4: Process files 301-400 → output/batch-004/
  └── Worker 5: Process files 401-500 → output/batch-005/
```

### Pattern E: Bug Fixing (Unknown Scope)

**WRONG:** "Fix all the bugs in the system"

**RIGHT:**
```
Manager: bug-fix-manager
  ├── Stage 1 — Triage (1 worker):
  │     Worker: Read error logs, identify bugs → output/bug-list.md
  │
  └── Stage 2 — Fix (one worker per bug, batched by priority):
          Worker 1: Fix critical bug #1 → [file]
          Worker 2: Fix critical bug #2 → [file]
          ...
```

---

## 5. Checkpoint Strategy — Incremental Progress Saving

### The Checkpoint Contract

Every worker MUST follow this checkpoint protocol:

1. **On Start:** Write `STARTED: [task description] at [timestamp]` to progress file
2. **Per File:** After writing each output file, append `FILE: [path] — [description]`
3. **Per Step:** After each logical step, append `STEP [N]: [what was done]`
4. **On Blocker:** Write `BLOCKED: [reason] — need: [what's needed to continue]`
5. **On Done:** Write `DONE: [summary of what was completed]`

### Progress File Format

```
# Progress: [WORKER_NAME]
# Task: [DESCRIPTION]
# Started: [TIMESTAMP]

STARTED: Fixing strategy 1 (Mean Reversion) → Pine Script
STEP 1: Read original Python strategy file
FILE: strategies/strategy_1_analysis.md — Analysis of original strategy
STEP 2: Convert entry/exit logic to Pine Script
FILE: strategies/strategy_1_pine.pine — Pine Script v5 conversion
STEP 3: Add plot statements for visualization
FILE: strategies/strategy_1_pine.pine — Updated with plots
DONE: Strategy 1 converted to Pine Script with entry/exit + plots
```

### Why This Matters

When `labmanagerfull` timed out with ZERO output, it was because there was no checkpointing. If the agent had written after each strategy fix, even timing out at strategy 3 would have delivered 3 completed fixes. **Partial output > no output.**

### Manager Checkpoint Monitoring

The Manager should read worker progress files every 2-3 minutes (not by polling sessions, but by reading files). This is how the Manager knows:
- Which workers are making progress
- Which workers are stuck
- Which workers have completed
- What to respawn if something fails

---

## 6. Failure Recovery — Mid-Pipeline Agent Failure

### Failure Types and Responses

**Type 1: Worker Produces Partial Output**
- Symptom: Progress file shows "STEP 3 of 5" then stops
- Response: Respawn worker with modified prompt: "Continue from STEP 4. Steps 1-3 are complete. See [output files]."
- The checkpoint file IS the recovery mechanism

**Type 2: Worker Produces No Output**
- Symptom: Progress file shows "STARTED" then nothing, or no progress file exists
- Response: Respawn worker with smaller scope. If the task was "fix strategy 1", split it into "analyze strategy 1" (worker A) and "implement fix for strategy 1" (worker B)

**Type 3: Worker Writes Garbage/Broken Output**
- Symptom: Output file exists but doesn't meet success criteria
- Response: Spawn a **Reviewer** worker that reads the output and the success criteria, writes a review, then spawn a **Fixer** worker to address the review

**Type 4: Manager Itself Fails**
- Symptom: Manager progress file stops updating
- Response: OWL reads the Manager's work plan, sees which workers completed, and spawns a **Recovery Manager** that picks up from the last known state

**Type 5: Cascading Failure (Multiple Workers Fail)**
- Symptom: 3+ workers in a batch fail
- Response: This indicates a systemic issue (wrong input files, broken environment, bad task spec). OWL should stop the pipeline, diagnose the root cause, fix the systemic issue, then restart the entire pipeline.

### Recovery Decision Tree

```
Worker failed?
  → Did it produce partial output?
      → YES: Respawn with "continue from checkpoint" prompt
      → NO: Is the task splittable?
          → YES: Split into smaller subtasks, respawn
          → NO: Reduce scope (deliver less but deliver something)
  → Did output fail quality check?
      → Spawn Reviewer → Fixer pipeline
  → Did 3+ workers fail simultaneously?
      → STOP PIPELINE. Diagnose systemic issue first.
```

### The Golden Rule of Recovery

**Never respawn a failed worker with the same prompt.** The prompt must be modified based on what was learned from the failure. Either:
- Reduce scope ("do only X instead of X+Y")
- Provide more context ("the input file is at THIS path, not that path")
- Split the task ("you do part A, another agent will do part B")
- Change approach ("instead of modifying the existing file, create a new one")

---

## Summary: The 7 Non-Negotiable Rules

1. **No single agent gets a multi-file, multi-component, multi-page task.** Period.
2. **Manager decomposes FIRST, spawns SECOND.** No execution before planning.
3. **One worker = one deliverable.** If it produces 3 files, it should be 3 workers.
4. **Every worker writes checkpoints.** After every file. No exceptions.
5. **Partial output is always better than no output.** Scope down, deliver something.
6. **Never respawn with the same prompt.** Learn from failure, adjust the approach.
7. **OWL never executes.** OWL spawns Manager. Manager spawns Workers. That's the chain.

---

*This document is handed to RA (Resource Adapter) for implementation in the agent workflow system. The patterns here should be encoded into spawn templates and enforced by OWL on every delegation.*
