# Chapter 12.6 — Failure Recovery

## Mission

Make QCAE resilient to worker crashes, tool failures, rate limits, partial outputs, model errors, stale artifacts, and infrastructure interruption without corrupting lifecycle state.

## Failure Classes

```text
TRANSIENT_TOOL
RATE_LIMIT
WORKER_CRASH
INVALID_OUTPUT
POLICY_BLOCK
STALE_INPUT
DEPENDENCY_UNAVAILABLE
EVIDENCE_CONTRADICTION
NON_RETRYABLE_FUNCTIONAL
INFRASTRUCTURE_FAILURE
```

## Checkpointing

Persist job state after every validated step. A crashed worker loses at most the active step, not the investigation history.

## Retry Policy

Retries are bounded and class-specific. Repeating the same prompt/tool call indefinitely is forbidden.

Retry may vary:

- provider/model;
- retrieval route;
- timeout;
- deterministic tool invocation;
- source mirror;

but must preserve task identity and log deviations.

## Poisoned Output

Malformed or unsupported worker output is quarantined and never merged into canonical state.

## Stale Inputs

If an upstream source revision or contract changes mid-job, affected work is marked stale and selectively rescheduled rather than silently mixed.

## Contradictions

Contradictory evidence triggers a review branch, not automatic majority vote.

## Compensation

Any step with persistent side effects must define compensation/rollback before execution. Most research/proving work should be disposable and side-effect free.

## Invariants

1. Validated state survives worker failure.
2. Retries are bounded and typed.
3. Invalid outputs never enter canonical state.
4. Staleness is explicit.
5. Contradiction causes review, not silent averaging.
6. Side-effecting steps require compensation semantics.

## Exit Criteria

QCAE can resume an interrupted investigation deterministically and explain exactly which steps were retried, invalidated, or abandoned.
