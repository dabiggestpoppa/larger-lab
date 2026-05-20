# RA_WORKFLOW_IMPLEMENTATION.md — Agent Workflow Improvements

> **Author:** RA (Resource Adapter)
> **Date:** 2026-05-19
> **Source Analysis:** SHAW_AGENT_WORKFLOW_ANALYSIS.md
> **Purpose:** Encode Shaw's pipeline patterns into actionable templates and checklists for OWL

---

## 1. Critical Changes Needed — Top 5

### Change #1: Enforce Manager → Worker Pipeline for All Multi-Deliverable Tasks
**Current behavior:** OWL sometimes assigns complex multi-file tasks to a single sub-agent.
**Required behavior:** If a task has >1 deliverable (files, pages, strategies, features), OWL MUST spawn a Manager, which then spawns Workers. No exceptions.
**Impact:** This alone would have prevented the `labmanagerfull` (0/10 strategies fixed) and `ocefrontend` (full timeout) failures.

### Change #2: Mandate Checkpointing in Every Worker
**Current behavior:** Workers may or may not write progress files. No enforcement.
**Required behavior:** Every worker MUST write a progress file with STARTED, STEP, FILE, BLOCKED, and DONE markers. No output file = failed worker, regardless of whether the agent "thought" it finished.
**Impact:** Even if a worker times out, partial output is preserved. `labmanagerfull` produced ZERO output — with checkpointing, it would have delivered partial fixes.

### Change #3: One Worker = One Deliverable (Strict)
**Current behavior:** Workers are sometimes given "fix strategies 1-3" or "build pages A, B, C."
**Required behavior:** One worker produces exactly one output file. If a task produces 3 files, it's 3 workers (or batched in groups of 5).
**Impact:** Reduces per-worker scope, increases parallelism, makes failures isolated and recoverable.

### Change #4: Never Respawn with the Same Prompt
**Current behavior:** When a worker fails, there's no guidance on how to respawn.
**Required behavior:** On failure, the respawn prompt MUST be modified: reduce scope, provide more context, split the task, or change approach. The checkpoint file IS the recovery mechanism.
**Impact:** Prevents the same failure from repeating. Each respawn learns from the previous attempt.

### Change #5: Manager Never Executes
**Current behavior:** Managers sometimes do actual work themselves instead of decomposing and spawning.
**Required behavior:** Manager's ONLY job: read task spec → decompose → write work plan → spawn workers → monitor progress files → aggregate results. If a Manager is writing code or fixing bugs, the decomposition is wrong.
**Impact:** Manager stays free to monitor and recover. Execution is parallelized across workers.

---

## 2. Spawn Templates for OWL

### Manager Spawn Template

Use this template when spawning a Manager for any multi-deliverable task:

```
You are [MANAGER_NAME] — Manager for [PROJECT/TASK_NAME].

## YOUR TASK
Coordinate the completion of [HIGH_LEVEL_GOAL] by decomposing into subtasks and spawning workers.

## INPUT
- Task specification: [PATH_TO_TASK_SPEC]
- Existing progress: [PATH_TO_PROGRESS_FILES_IF_ANY]

## DECOMPOSITION (DO THIS FIRST — DO NOT SKIP)
1. Read the task specification thoroughly
2. List ALL deliverables (files, features, fixes, pages)
3. Group deliverables into independent subtasks (max 30 min each)
4. Write your work plan to [WORK_PLAN_PATH]:
   Format:
   # Work Plan: [TASK_NAME]
   ## Workers
   - Worker 1: [SINGLE_TASK] → [EXACT_OUTPUT_PATH]
   - Worker 2: [SINGLE_TASK] → [EXACT_OUTPUT_PATH]
   ## Dependencies
   - [Worker X] must complete before [Worker Y] because [REASON]
   ## Batches
   - Batch 1: [Workers to run concurrently, max 5]
   - Batch 2: [Remaining workers]
5. Identify any dependencies (which workers must finish before others start)

## EXECUTION
- Spawn workers in dependency order (independent workers first)
- Max 5 concurrent workers per batch
- After each worker completes, verify their output file exists and is valid
- If a worker fails, respawn ONLY that worker with modified prompt (see recovery rules below)

## RECOVERY RULES (MANDATORY)
- If worker produced partial output: respawn with "continue from checkpoint" prompt pointing to progress file
- If worker produced no output: split the task into smaller subtasks, respawn
- If worker produced broken output: spawn Reviewer → Fixer pipeline
- If 3+ workers fail simultaneously: STOP. Write BLOCKED status to progress file. Do not continue.
- NEVER respawn with the same prompt. Always modify based on failure analysis.

## OUTPUT
- Write completion report to [REPORT_PATH] listing: completed, failed, blocked items
- Update [MASTER_PROGRESS_FILE] with final status

## CHECKPOINTING (MANDATORY)
Append to [MANAGER_PROGRESS_FILE] after every action:
  [TIMESTAMP] [ACTION]: [DETAILS]

## RULES
1. You do NOT execute any subtask yourself. No writing code, no fixing bugs, no building.
2. You decompose FIRST, then spawn. No execution before planning.
3. You monitor by READING output files, not by guessing or polling.
4. If all workers complete, aggregate and report.
5. When done, write DONE: [SUMMARY] to your progress file.
```

### Worker Spawn Template

Use this template for every worker spawned by a Manager (or by OWL for single-deliverable tasks):

```
You are [WORKER_NAME] — [ONE_SENTENCE_ROLE_DESCRIPTION].

## YOUR SINGLE TASK
[EXACTLY ONE THING TO DO. NOT THREE THINGS. ONE.]

## INPUT
- Source files: [EXACT_PATHS]
- Reference docs: [EXACT_PATHS]
- Context file: [PATH_TO_CONTEXT_IF_NEEDED]

## OUTPUT
- Write to: [EXACT_OUTPUT_PATH]
- Format: [EXACT_FORMAT_EXPECTED]
- Success criteria: [HOW_WE_KNOW_YOU_SUCCEEDED]

## CHECKPOINTING (MANDATORY — DO NOT SKIP)
Create/append to [WORKER_PROGRESS_FILE] using this exact format:

  STARTED: [task description] at [TIMESTAMP]
  STEP 1: [what you did] → [result]
  STEP 2: [what you did] → [result]
  FILE: [path] — [description of what was written]
  DONE: [summary of what was completed]

If you encounter a blocker:
  BLOCKED: [reason] — need: [what's needed to continue]

## RULES
1. Do ONLY this task. Do not expand scope. Do not do anything else.
2. Start writing output within the first 2 minutes. Don't spend all time analyzing.
3. If analysis exceeds 5 minutes without writing, stop analyzing and start writing.
4. Write output incrementally — don't wait until the end to write everything.
5. If the task has multiple files, write each file as you complete it.
6. Prefer partial output over no output. Scope down if needed, but deliver something.
7. When done, write DONE: [SUMMARY] to the progress file.

## TIMEOUT PREVENTION
- If you're stuck on something for >3 minutes, skip it and move to the next step
- Write what you have to the progress file before attempting anything risky
- Partial output is always better than no output
```

---

## 3. OWL Pre-Spawn Checklist

Before spawning ANY sub-agent, OWL MUST run through this checklist:

```
### Pre-Spawn Checklist (MANDATORY — Shaw Directive 2026-05-19)

- [ ] **Count the deliverables:** How many output files/pages/features will this task produce?
  - If 1: Spawn a single Worker using the Worker Template
  - If >1: Spawn a Manager using the Manager Template (Manager will spawn Workers)

- [ ] **Define the output path:** Does every worker have an EXACT output file path?
  - If not, define it before spawning. No worker should decide where to put output.

- [ ] **Define success criteria:** How will we know the worker succeeded?
  - Write specific, verifiable criteria. "It works" is not a criterion.

- [ ] **Set up the progress file:** Does every worker have a designated progress file path?
  - Format: progress/[worker-name]-progress.md
  - Worker MUST write STARTED, STEP, FILE, DONE markers

- [ ] **Check dependencies:** Are there any prerequisites the worker needs?
  - Existing files, installed packages, running services
  - If yes, verify they exist BEFORE spawning

- [ ] **Scope check:** Can this task be completed in ≤30 minutes?
  - If not, it needs further decomposition. Don't spawn it as-is.

- [ ] **Batch planning:** If spawning multiple workers, are they grouped in batches of ≤5?
  - If >5 workers, plan sequential batches with dependency ordering

- [ ] **Failure plan:** If this worker fails, what's the recovery approach?
  - Partial output → respawn with "continue from checkpoint"
  - No output → split task smaller
  - Broken output → Reviewer → Fixer pipeline
  - NEVER respawn with the same prompt
```

---

## 4. Recommended Changes to AGENTS.md

The following section should be added to AGENTS.md to encode the pipeline pattern as a mandatory rule:

### Section to Add (after the OWL ORCHESTRATOR PRINCIPLE section):

```
### Manager → Worker Pipeline (MANDATORY — Shaw Directive 2026-05-19)
- OWL NEVER assigns a task to a single agent if it has >1 deliverable
- For multi-deliverable tasks: OWL spawns Manager → Manager spawns Workers
- One Worker = One Deliverable (one file, one page, one strategy)
- Every worker MUST write checkpoint progress to a progress file
- Manager NEVER executes — only plans, spawns, monitors, aggregates
- Max 5 concurrent workers; batch if more needed
- On failure: respawn with modified prompt, never the same prompt
```

---

## 5. Summary of Files Modified

| File | Change |
|------|--------|
| `AGENTS.md` | Added "Manager → Worker Pipeline" section after OWL Orchestrator Principle |
| `sw-dev/RA_WORKFLOW_IMPLEMENTATION.md` | This file — full implementation reference |

---

## 6. The 7 Non-Negotiable Rules (Shaw's Summary — For Quick Reference)

1. **No single agent gets a multi-file, multi-component, multi-page task.** Period.
2. **Manager decomposes FIRST, spawns SECOND.** No execution before planning.
3. **One worker = one deliverable.** If it produces 3 files, it should be 3 workers.
4. **Every worker writes checkpoints.** After every file. No exceptions.
5. **Partial output is always better than no output.** Scope down, deliver something.
6. **Never respawn with the same prompt.** Learn from failure, adjust the approach.
7. **OWL never executes.** OWL spawns Manager. Manager spawns Workers. That's the chain.

---

*Implementation complete. RA recommends OWL review this document and the updated AGENTS.md before next delegation cycle.*
