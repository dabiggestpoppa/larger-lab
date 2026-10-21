# ADR-0008 — P2 Runtime State Vocabulary and Event Log

## Status

Accepted (P2-I0)

## Context

P0 froze Job/Step identity primitives (`qcae/core/jobs.py`) with a minimal
status vocabulary (PENDING/RUNNING/SUCCEEDED/FAILED/CANCELLED). The P2 operator
directive requires a full runtime state machine. Two canon sources name states:

- **Book V 13.6** defines the *step* state vocabulary:
  `PENDING READY RUNNING WAITING_POLICY WAITING_INPUT RETRY_SCHEDULED
  SUCCEEDED PARTIAL FAILED CANCELLED STALE`.
- The P2 directive §5 lists *job-level* semantic states: equivalents of
  `CREATED QUEUED RUNNING WAITING WAITING_APPROVAL RETRY_PENDING SUCCEEDED
  FAILED CANCELLED BLOCKED`.

The P0 `JobStatus`/`StepStatus` enums are already persisted in P1-freeze-era
tests as part of the P0 `Job`/`Step` records (schema v1). Rewriting their
vocabulary would break frozen P0 serialization round trips and would
contradict the P2 directive §2 ("use frozen vocabulary where it exists, do not
duplicate P0 types unnecessarily").

## Alternatives considered

1. **Replace P0 `JobStatus`/`StepStatus` with the 13.6 vocabulary.**
   Rejected: breaks P0 schema-v1 round trips (frozen), conflates the
   queue-level step lifecycle with job-level orchestration semantics, and
   destroys the reviewed P1 baseline.
2. **Reuse P0 enums and never extend them.**
   Rejected: P2 requires WAITING_APPROVAL, RETRY_SCHEDULED, and
   lease-expiry semantics that the 5-value enums cannot express; the P0
   docstring explicitly reserved this extension for P2 "with new schema
   versions".
3. **Separate runtime state machines, additive schema v2 (chosen).**
   New `RuntimeJobStatus` and `RuntimeStepStatus` enums in the orchestration
   layer, with explicit, fail-closed transition tables. The P0 records remain
   the identity layer; the runtime records carry operational state. The two
   layers are linked by `job_id`/`step_id`, and the runtime layer's initial
   states map 1:1 onto the P0 vocabulary where meanings coincide
   (PENDING→PENDING, RUNNING→RUNNING, SUCCEEDED→SUCCEEDED, FAILED→FAILED,
   CANCELLED→CANCELLED).

## Decision

- Add `RuntimeJobStatus` (CREATED, QUEUED, RUNNING, WAITING, WAITING_APPROVAL,
  RETRY_PENDING, SUCCEEDED, FAILED, CANCELLED, BLOCKED) and
  `RuntimeStepStatus` (the Book V 13.6 vocabulary, verbatim).
- Explicit transition tables; illegal transitions raise
  `QcaeStateTransitionError`; terminal states never transition.
- Add a schema-v2 `RuntimeJob`/`RuntimeStep` pair that composes the P0
  records' deterministic identity semantics (`deterministic_job_id`,
  `step identity = job-scoped stable step id`) and adds lease/budget/
  checkpoint/authority refs.
- Add an append-oriented `JobEvent` stream using the directive §9 event
  vocabulary (JOB_CREATED … JOB_CANCELLED).

## Reason

Canon 13.6 explicitly supplies step states; the job-level set follows the
P2 directive, which is operator-provided for exactly this phase. Preserving
the P0 records keeps every frozen serialization intact while the runtime
layer carries only what executable durability needs.

## Burden

Two state enums instead of one; a documented mapping table. Runtime records
are separate from P0 identity records, so registry/evidence code that embeds
P0 `Job`/`Step` remains untouched.

## Reversibility

Additive schema v2; the P0 layer is untouched. Removing or extending runtime
enums later is a forward migration, not a rewrite.

## Canon compatibility

Book V 13.6 (step states, durable scheduling, leasing, idempotency, priority
without policy bypass, human wait states); Book V 12.1 (durable job state
fields, idempotent resumption); Book V 12.6 (bounded typed retries,
checkpoint-after-validated-step); Book I lifecycle doctrine (explicit,
fail-closed transitions). Amendment A-001 is unaffected (its gap/resolution
vocabularies are orthogonal to runtime states).
