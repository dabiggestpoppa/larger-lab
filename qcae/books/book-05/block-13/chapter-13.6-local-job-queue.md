# Chapter 13.6 — Local Job Queue

## Mission

Persist and schedule QCAE work so long investigations can pause, retry, branch, and resume without requiring one live model session.

## Queue Model

Jobs contain steps with dependencies and statuses:

```text
PENDING
READY
RUNNING
WAITING_POLICY
WAITING_INPUT
RETRY_SCHEDULED
SUCCEEDED
PARTIAL
FAILED
CANCELLED
STALE
```

## Durable Scheduling

Ready state derives from satisfied dependencies, valid inputs, budget, and policy—not conversational sequence.

## Leasing

Workers should lease a step with timeout/heartbeat semantics so crashed workers do not leave permanent `RUNNING` state.

## Idempotency

Stable step IDs/idempotency keys prevent duplicate work after lease expiry or restart.

## Priority

Priority may reflect:

- user request urgency;
- lifecycle gate criticality;
- cheap information gain;
- monitoring/security urgency;
- resource availability.

Priority never bypasses policy prerequisites.

## Concurrency

Parallelize independent candidates/tasks while preventing concurrent mutation of the same canonical object without coordination.

## Human Wait States

Jobs awaiting approval persist indefinitely or according to retention policy without consuming worker resources.

## Invariants

1. Work is durable and resumable.
2. Readiness derives from state/gates, not chat order.
3. Worker leases recover from crashes.
4. Steps are idempotent.
5. Parallelism respects canonical-state ownership.
6. Priority cannot bypass authority/evidence requirements.

## Exit Criteria

QCAE can run multi-hour/day investigations locally with crash-safe scheduling and no requirement for continuous conversational memory.
