# OCE Research Mesh V2 — Book 8 Plan
## Research Orchestration

**Document ID:** RMV2-B8-PLAN-001  
**Version:** 0.1  
**Branch:** `agent/oce-research-mesh-v2`  
**Status:** PLANNING BASELINE — NOT YET FROZEN  
**System role:** standalone-first research institution, OCE-compatible by contract, Hermes-operated  
**Scope:** bounded research task generation, scheduling, worker coordination, checkpoints, feedback loops, refresh/reopen execution  
**Parents:** Books 1–7

---

## 0. Book 8 mission

Book 8 turns explicit research needs into bounded, auditable research work.

Book 7 answers:

> What does the institution currently know, what remains unresolved, and what evidence should come next?

Book 8 answers:

> How do we convert those EvidenceNeeds into research tasks, choose an admissible source strategy, coordinate bounded workers, checkpoint progress, feed new evidence back through the Research Mesh, and decide whether to continue, pause, stop, reopen, or escalate?

The governing path is:

```text
EvidenceNeed / ResearchQuestion / ReopenTrigger
        ↓
ResearchOrchestrationPlan
        ↓
Task decomposition
        ↓
Source / method strategy
        ↓
Bounded worker execution
        ↓
Checkpoint + receipts
        ↓
Books 2–7 re-entry
        ↓
Updated claims / uncertainty / dossier
        ↓
Continue / close / reopen / stop / escalate
```

Hard rule:

> Orchestration controls work. It does not control truth.

Hermes may operate the orchestration layer. Hermes may not alter epistemic state directly, self-ratify doctrine, bypass authority/rights/budget constraints, or mark research complete merely because workers finished tasks.

---

# 1. Book structure

Book 8 contains five chapters with five sections each.

| Chapter | Name | Primary question |
|---|---|---|
| B8.C1 | Research Task & Plan Contracts | How is a bounded research objective represented? |
| B8.C2 | Worker Fabric & Scheduling | How are research tasks routed, parallelized, and constrained? |
| B8.C3 | Checkpoints, Feedback & Re-entry | How does new evidence re-enter Books 2–7 safely? |
| B8.C4 | Gap Prioritization, Refresh & Reopen | What gets researched next, refreshed later, or reopened? |
| B8.C5 | Qualification & Book 9 Handoff | How do we prove orchestration remains bounded, replayable, and non-sovereign? |

Book 8 exits only when research tasks are bounded and typed, scheduling is policy-controlled, workers cannot self-authorize, task completion is separated from epistemic closure, feedback into Books 2–7 is explicit, and Hermes can operate the loop without becoming the institution.

---

# 2. B8.C1 — Research Task & Plan Contracts

## B8.C1.S1 — ResearchTask contract

Define `ResearchTask`.

Minimum fields:

```text
task_id
research_question_id
research_plan_id
origin_evidence_need_ids[]
origin_dossier_id
task_type
objective
scope
excluded_scope
required_outputs[]
source_classes_allowed[]
source_classes_denied[]
method_constraints[]
rights_policy_ref
budget_ref
authority_ref
priority
deadline
stopping_conditions[]
created_at
created_by
status
task_contract_version
```

Initial task types:

- SOURCE_DISCOVERY
- PRIMARY_SOURCE_ACQUISITION
- CITATION_EXPANSION
- CONTRADICTION_FOLLOWUP
- REPLICATION_SEARCH
- METHOD_COMPARISON
- DATASET_LINEAGE_SEARCH
- IDENTITY_RESOLUTION
- REVISION_CHECK
- RETRACTION_CHECK
- LOCAL_CORPUS_REVIEW
- GAP_INVESTIGATION
- EVIDENCE_REFRESH
- DOSSIER_REFRESH
- OPERATOR_REQUESTED_RESEARCH

No task may be open-ended by default.

---

## B8.C1.S2 — ResearchOrchestrationPlan

Define `ResearchOrchestrationPlan`.

Minimum fields:

```text
orchestration_plan_id
question_id
task_ids[]
task_dependencies
parallelizable_groups[]
sequential_constraints[]
source_strategy
budget_envelope
concurrency_limit
max_depth
max_spawned_tasks
checkpoint_policy_id
stop_policy_id
reopen_policy_id
operator_review_triggers[]
created_at
plan_version
```

The plan is frozen for a run.

Material plan changes produce a new version/run.

---

## B8.C1.S3 — Task dependency graph

Task relationships:

- REQUIRES
- BLOCKS
- ENABLES
- PARALLEL_WITH
- SUPERSEDES
- RETRY_OF
- REOPENED_FROM
- CHILD_OF
- EVIDENCE_DEPENDENT_ON

The task graph must remain acyclic for strict dependencies.

Cycles are allowed only as explicitly bounded refresh loops.

Unbounded recursive spawning is prohibited.

---

## B8.C1.S4 — Task status model

Initial task states:

- PLANNED
- READY
- RUNNING
- WAITING_ON_DEPENDENCY
- PAUSED
- PARTIAL
- COMPLETED_TASK
- FAILED
- BLOCKED_RIGHTS
- BLOCKED_ACCESS
- BLOCKED_AUTHORITY
- BUDGET_STOP
- CANCELLED
- OPERATOR_REVIEW_REQUIRED
- SUPERSEDED
- ARCHIVED

`COMPLETED_TASK` means execution finished.

It does **not** mean the research question is resolved.

---

## B8.C1.S5 — ResearchTaskReceipt

Every task emits a durable receipt:

```text
task_receipt_id
task_id
plan_id
worker_id
input_refs[]
output_refs[]
source_calls[]
books_invoked[]
started_at
completed_at
status
budget_used
failures[]
partial_outputs[]
checkpoint_refs[]
policy_versions
receipt_digest
```

### Gate C1

**PASS_B8_C1_TASK_AND_PLAN_CONTRACTS** requires:
- bounded task contracts;
- frozen orchestration plans;
- typed dependency graph;
- task completion separated from epistemic closure;
- every task emits a receipt.

---

# 3. B8.C2 — Worker Fabric & Scheduling

## B8.C2.S1 — Worker roles

Initial worker roles:

- DISCOVERY_WORKER
- ACQUISITION_WORKER
- RETRIEVAL_WORKER
- CLAIM_ANALYSIS_WORKER
- CONTRADICTION_WORKER
- IDENTITY_WORKER
- SYNTHESIS_WORKER
- REFRESH_WORKER
- AUDIT_WORKER

Worker role is capability scope, not authority.

A worker cannot gain new authority merely because a task requests it.

---

## B8.C2.S2 — Worker capability manifest

Each worker declares:

```text
worker_id
worker_type
supported_task_types[]
allowed_books[]
network_access
local_file_access
model_access
external_tool_access
max_concurrency
cost_class
authority_classes[]
rights_classes[]
version
qualification_state
```

Unsupported tasks refuse before execution.

Worker manifests are versioned.

---

## B8.C2.S3 — Scheduler policy

The scheduler owns:

- queue priority;
- dependency release;
- bounded concurrency;
- per-provider/source throttling;
- per-worker limits;
- budget reservation;
- pause/cancel;
- fairness;
- retry scheduling;
- operator-review holds.

Scheduling must not alter epistemic priority criteria silently.

The scheduler executes the priority policy; it does not invent one.

---

## B8.C2.S4 — Parallelism and independence

Parallel workers do not equal independent evidence.

If three workers query the same source and retrieve the same study, that remains one evidence lineage.

Worker count cannot inflate:
- corroboration;
- source diversity;
- independence;
- confidence.

This directly inherits the institutional stress-suite law:

> independence is a vector, not agent count.

---

## B8.C2.S5 — Worker authority firewall

Workers may:
- execute authorized tasks;
- create provisional findings;
- emit evidence;
- propose follow-up tasks;
- request escalation.

Workers may not:
- change source policy;
- change rights policy;
- increase budget ceiling;
- widen task scope silently;
- mark doctrine promoted;
- mutate OCE/QCAE canon;
- approve their own authority change.

### Gate C2

**PASS_B8_C2_WORKER_FABRIC** requires:
- worker manifests enforced;
- unsupported task refusal;
- scheduler bounds hold;
- worker-count independence inflation blocked;
- authority firewall passes.

---

# 4. B8.C3 — Checkpoints, Feedback & Re-entry

## B8.C3.S1 — ResearchCheckpoint

Define `ResearchCheckpoint`.

Minimum fields:

```text
checkpoint_id
orchestration_plan_id
task_states
completed_task_receipts[]
new_evidence_refs[]
new_claim_refs[]
updated_uncertainty_refs[]
updated_dossier_refs[]
budget_state
coverage_state
blocking_conditions[]
operator_review_items[]
created_at
checkpoint_policy_version
```

Checkpoints are immutable.

---

## B8.C3.S2 — Re-entry routes

New outputs must re-enter through the owning Book.

Examples:

```text
new source bytes
→ Book 2

new cross-provider identity
→ Book 3

new searchable passage
→ Book 4

new claim / citation relation
→ Book 5

new contradiction / uncertainty
→ Book 6

new synthesis / dossier
→ Book 7
```

Book 8 must never directly mutate downstream truth objects.

It routes artifacts to the owner.

---

## B8.C3.S3 — Feedback evaluation

After checkpoint, Book 8 asks:

- Did the EvidenceNeed get satisfied?
- Did uncertainty materially change?
- Did a contradiction resolve?
- Did a new contradiction emerge?
- Did source coverage improve?
- Did rights/access block the path?
- Did the budget materially degrade?
- Is another discriminator still actionable?

These answers come from Books 2–7 outputs.

Book 8 does not infer them independently.

---

## B8.C3.S4 — Continue / pause / stop decision

Allowed orchestration decisions:

- CONTINUE
- CONTINUE_WITH_NEW_TASKS
- PAUSE
- STOP_RESOLVED_WITHIN_SCOPE
- STOP_UNRESOLVED_STABLE
- STOP_BUDGET
- STOP_RIGHTS
- STOP_ACCESS
- STOP_DIMINISHING_RETURNS
- STOP_OPERATOR
- ESCALATE_OPERATOR
- REPLAN_REQUIRED

Decision must cite:
- checkpoint;
- Book 6 closure state;
- budget/rights state;
- policy version.

---

## B8.C3.S5 — No self-healing by hidden mutation

If a task fails, Book 8 may:
- retry under policy;
- route to alternate source;
- spawn a bounded fallback task;
- pause;
- escalate.

It may not:
- silently broaden scope;
- silently relax source standards;
- silently change rights policy;
- convert failure into no evidence;
- rewrite task success criteria.

### Gate C3

**PASS_B8_C3_CHECKPOINT_REENTRY** requires:
- immutable checkpoints;
- Book-owner re-entry enforced;
- orchestration decisions source Book 6/7 state;
- hidden mutation blocked;
- failure stays visible.

---

# 5. B8.C4 — Gap Prioritization, Refresh & Reopen

## B8.C4.S1 — KnowledgeGap object

Define `KnowledgeGap`.

Minimum fields:

```text
gap_id
question_id
origin_claim_ids[]
origin_uncertainty_ids[]
origin_dossier_id
gap_type
description
materiality
decision_relevance
blocking_state
evidence_need_ids[]
estimated_cost_class
access_feasibility
priority_basis
status
created_at
```

Gap types include:

- MISSING_PRIMARY_EVIDENCE
- MISSING_REPLICATION
- CONTRADICTION_UNRESOLVED
- IDENTITY_UNRESOLVED
- REVISION_UNKNOWN
- COVERAGE_INCOMPLETE
- METHOD_UNCERTAIN
- POPULATION_GAP
- TEMPORAL_GAP
- RIGHTS_OR_ACCESS_GAP
- DEPENDENCY_UNKNOWN
- EXTERNAL_VALIDITY_GAP

---

## B8.C4.S2 — Gap priority vector

Do not reduce gap priority to one hidden score.

Initial priority dimensions:

- decision impact;
- blocking uncertainty;
- expected discriminator value;
- evidence independence gained;
- cost;
- access feasibility;
- time sensitivity;
- rights feasibility;
- reversibility;
- recurrence risk.

Ergonomic labels may be:

- CRITICAL
- HIGH
- MEDIUM
- LOW
- DEFER
- BLOCKED
- UNKNOWN

But the vector remains canonical.

---

## B8.C4.S3 — Refresh policies

Research may require refresh when:

- source revisions likely;
- citation/retraction status may change;
- fast-moving domain;
- time-bounded decision horizon;
- scheduled institutional review;
- unresolved gap has expected new evidence;
- dataset/publication cycle known.

A `RefreshPolicy` defines:
- trigger;
- minimum interval;
- maximum interval;
- source set;
- budget;
- stop criteria;
- expiry;
- authority.

Book 8 defines refresh mechanics. Book 9 will define Hermes-facing controls.

---

## B8.C4.S4 — Reopen orchestration

When Book 6 emits a reopen trigger:

```text
prior dossier
→ reopen trigger
→ new orchestration run
→ new evidence
→ new Book 2–7 generations
→ superseding dossier
```

The prior dossier remains intact.

Reopen does not mean prior work was "wrong"; it means the evidence state changed.

---

## B8.C4.S5 — Task-generation policy

Book 8 may generate new tasks only from explicit bases:

- EvidenceNeed;
- KnowledgeGap;
- ReopenTrigger;
- OperatorRequest;
- approved RefreshPolicy;
- failed task requiring allowed fallback.

Every generated task records its origin.

No free-floating autonomous research loop.

### Gate C4

**PASS_B8_C4_GAPS_REFRESH_REOPEN** requires:
- gap objects explicit;
- priority remains vector-based;
- refresh policies bounded;
- reopen preserves prior history;
- task generation requires an explicit origin.

---

# 6. B8.C5 — Qualification & Book 9 Handoff

## B8.C5.S1 — Golden orchestration corpus

Create deterministic scenarios covering:

1. one-task research;
2. parallel source search;
3. sequential dependency;
4. provider failure + fallback;
5. rights-blocked path;
6. budget stop;
7. contradiction follow-up;
8. evidence need satisfied;
9. evidence need not satisfied;
10. diminishing returns;
11. worker failure;
12. checkpoint recovery;
13. task retry;
14. operator escalation;
15. reopen on new evidence;
16. refresh policy trigger;
17. same evidence found by multiple workers;
18. worker tries to widen scope;
19. max-depth/max-spawn guard;
20. offline/local-only research run.

---

## B8.C5.S2 — Deterministic orchestration replay

For deterministic scheduling:

> same plan + same task graph + same worker manifests + same policy versions + same fixture outcomes => same orchestration decision.

Live provider timing may differ, but the receipt must make nondeterministic external timing explicit.

No favorable default when state is missing.

---

## B8.C5.S3 — Recovery and restart

Book 8 must prove restart from durable checkpoints.

After crash:
- load orchestration plan;
- load last committed checkpoint;
- verify task receipts;
- identify RUNNING-but-unconfirmed tasks;
- requeue safely;
- do not mark uncertain task completion;
- preserve duplicate execution lineage if retry occurred.

No in-memory-only orchestration truth.

---

## B8.C5.S4 — Book 8 adversarial matrix

| ID | Attack / case | Required result |
|---|---|---|
| B8-A01 | worker completion marks question resolved | REFUSE |
| B8-A02 | three workers finding same study counted as three confirmations | REFUSE |
| B8-A03 | task silently widens scope | REFUSE |
| B8-A04 | scheduler raises budget ceiling | REFUSE |
| B8-A05 | worker self-grants network/authority | REFUSE |
| B8-A06 | provider failure converted to NO_RESULTS | REFUSE |
| B8-A07 | failed task hidden from checkpoint | REFUSE |
| B8-A08 | Book 8 directly mutates claim state | REFUSE |
| B8-A09 | Book 8 directly mutates uncertainty vector | REFUSE |
| B8-A10 | recursive task generation exceeds max depth | REFUSE |
| B8-A11 | task spawned without EvidenceNeed/Gap/Request/Refresh origin | REFUSE |
| B8-A12 | rights block bypassed by fallback source | REFUSE |
| B8-A13 | crash causes uncertain task to be marked complete | REFUSE |
| B8-A14 | refresh silently overwrites prior dossier | REFUSE |
| B8-A15 | worker count treated as evidence independence | REFUSE |
| B8-A16 | scheduler changes success criteria mid-run | REFUSE |
| B8-A17 | all external workers unavailable | LOCAL-ONLY MODE PASS |
| B8-A18 | model workers unavailable | DETERMINISTIC WORKERS PASS |
| B8-A19 | stop unresolved stable | PASS |
| B8-A20 | operator escalation remains pending until external authority acts | PASS |

---

## B8.C5.S5 — Freeze package and Book 9 handoff

Book 8 freeze emits:

- ResearchTask schema;
- ResearchOrchestrationPlan schema;
- task dependency vocabulary;
- worker manifest schema;
- scheduler policy;
- checkpoint schema;
- re-entry contract;
- KnowledgeGap schema;
- gap-priority vector;
- RefreshPolicy schema;
- task-generation policy;
- recovery protocol;
- golden orchestration corpus;
- adversarial qualification receipt;
- known limitations;
- Book 9 handoff manifest.

### Gate C5

**PASS_B8_C5_ORCHESTRATION_QUALIFICATION** requires:
- C1–C4 gates pass;
- A01–A20 pass;
- restart/recovery proven;
- task/epistemic closure separation proven;
- worker authority firewall proven;
- task origin provenance complete;
- local-only mode proven.

---

# 7. Evolution from old Research Mesh agents

The old Research Mesh had:

```text
Gap Detector
→ Research Agent
→ Task Generator
→ Queue
→ Evaluator
→ Synthesis
→ Consensus
→ Doctrine
```

Book 8 preserves the useful ideas:
- gap detection;
- task generation;
- queueing;
- bounded concurrency;
- evaluation;
- synthesis feedback.

But removes the unsafe compression:

```text
agent output
→ consensus
→ doctrine
```

The new path is:

```text
KnowledgeGap / EvidenceNeed
→ bounded ResearchTask
→ worker
→ Books 2–7
→ uncertainty / dossier
→ external doctrine review if applicable
```

Workers produce evidence and proposals.

They do not produce institutional truth by finishing.

---

# 8. Orchestration philosophy

The orchestration layer should be able to say:

```text
Task execution is complete.
Research closure is not.

Two EvidenceNeeds remain unsatisfied.
One provider failed.
One discriminator was satisfied.
Uncertainty decreased in method robustness but remains blocking in external validity.
Next action: pause pending operator review.
```

That is institutionally preferable to:

```text
Research complete.
```

---

# 9. Planned implementation layout

```text
oce/research_mesh_v2/
  orchestration/
    __init__.py
    vocabulary.py
    tasks.py
    plans.py
    dependency_graph.py
    receipts.py

    workers/
      base.py
      manifests.py
      registry.py
      discovery.py
      acquisition.py
      retrieval.py
      claims.py
      contradiction.py
      synthesis.py
      audit.py

    scheduler/
      queue.py
      policy.py
      concurrency.py
      budgets.py
      retries.py
      fairness.py

    checkpoints/
      models.py
      store.py
      evaluate.py
      recovery.py

    gaps/
      models.py
      priority.py
      task_generation.py

    refresh/
      policies.py
      triggers.py
      reopen.py

    routing/
      book_routes.py
      reentry.py

  tests/book_08/
    test_c1_tasks_plans.py
    test_c2_worker_fabric.py
    test_c3_checkpoint_reentry.py
    test_c4_gaps_refresh.py
    test_c5_qualification.py
    test_b8_adversarial.py
    fixtures/orchestration/
```

The old Research Agent / Task Generator / Queue code is reference material only.

---

# 10. Book 8 implementation sequence

## B8-I0 — agent archaeology + orchestration corpus
- inspect old gap detector / agent / queue architecture;
- inspect Book 7 EvidenceNeed handoff;
- build golden orchestration scenarios;
- identify bounded deterministic core.

**Exit:** `PASS_B8_I0_ORCHESTRATION_CHARACTERIZATION`

## B8-I1 — C1 task/plan contracts
Implement ResearchTask, plan, dependency graph and task receipts.

**Exit:** `PASS_B8_C1_TASK_AND_PLAN_CONTRACTS`

## B8-I2 — C2 worker fabric
Implement worker manifests, registry, scheduler and authority firewall.

**Exit:** `PASS_B8_C2_WORKER_FABRIC`

## B8-I3 — C3 checkpoints/re-entry
Implement durable checkpoints, Book-owner routes and continue/stop decisions.

**Exit:** `PASS_B8_C3_CHECKPOINT_REENTRY`

## B8-I4 — C4 gaps/refresh/reopen
Implement KnowledgeGap, gap priority vector, refresh and task-generation policies.

**Exit:** `PASS_B8_C4_GAPS_REFRESH_REOPEN`

## B8-I5 — recovery/restart
Prove restart from durable state with uncertain task handling.

**Exit:** `PASS_B8_ORCHESTRATION_RECOVERY`

## B8-I6 — Hermes-neutral operator surface
Implement orchestration API/CLI independent of Hermes.

**Exit:** `PASS_B8_OPERATOR_SURFACE`

## B8-I7 — adversarial qualification
Run golden scenarios and A01–A20.

**Exit:** `PASS_B8_C5_ORCHESTRATION_QUALIFICATION`

## B8-I8 — freeze
Emit fingerprints, receipts, limitations and Book 9 handoff.

**Exit:** `PASS_BOOK_8_RESEARCH_ORCHESTRATION`

---

# 11. Book 8 hard invariants

1. Orchestration controls work, not truth.
2. Task completion is not epistemic closure.
3. Every task has explicit scope and origin.
4. No free-floating autonomous task generation.
5. Worker role is not authority.
6. Worker count is not evidence independence.
7. Scheduler cannot alter success criteria.
8. Scheduler cannot increase authority or budget.
9. Rights constraints survive routing/fallback.
10. Provider failures remain explicit.
11. New evidence re-enters through the owning Book.
12. Book 8 cannot directly mutate claim/uncertainty/doctrine state.
13. Checkpoints are durable and immutable.
14. Crash recovery never assumes uncertain completion.
15. Recursive task generation is depth/count bounded.
16. Refresh does not rewrite prior dossier history.
17. Reopen runs create new generations.
18. Local-only operation remains possible.
19. Hermes remains replaceable.
20. Book 9 receives orchestration verbs and receipts, not hidden internal mutation powers.

---

# 12. Explicit non-goals for Book 8

Do not build yet:
- Hermes-specific conversational interface;
- user-facing research commands;
- operator dashboard;
- external app integrations;
- QCAE/OCE live authority handoffs;
- institutional doctrine promotion.

Those belong to Books 9–10.

---

# 13. Book 9 handoff

Book 9 — Hermes Operator Layer — receives:

- research task verbs;
- orchestration plans;
- worker/task status;
- checkpoint status;
- EvidenceNeeds;
- KnowledgeGaps;
- refresh/reopen controls;
- dossier retrieval;
- operator-review requests;
- task/orchestration receipts;
- authority/rights/budget refusal states.

Book 9 may expose these capabilities conversationally and ergonomically to Hermes. It may not create shadow research state, bypass Research Mesh contracts, or gain authority unavailable through the Book 8 operator surface.

**Final gate:** `PASS_BOOK_8_RESEARCH_ORCHESTRATION`
