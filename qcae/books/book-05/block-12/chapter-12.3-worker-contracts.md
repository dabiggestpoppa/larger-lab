# Chapter 12.3 — Worker Contracts

## Mission

Every worker invocation must be governed by a typed contract so outputs can be validated, replayed, audited, and consumed without relying on prose conventions.

## WorkerRequest

Minimum fields:

```text
job_id
step_id
worker_type
contract_ref
input_artifact_refs
requested_outputs
constraints
policy_context_ref
budget
deadline/timeout
idempotency_key
```

## WorkerResult

Minimum fields:

```text
step_id
status
output_artifact_refs
evidence_refs
claims
uncertainties
contradictions
policy_events
budget_used
logs/diagnostics ref
recommended_next_actions
```

## Status Vocabulary

```text
SUCCESS
PARTIAL
FAILED
BLOCKED_POLICY
BLOCKED_INPUT
INCONCLUSIVE
RETRYABLE
CANCELLED
```

Do not encode failure only as free-form text.

## Schema Validation

The Orchestrator rejects malformed outputs before lifecycle progression. Missing required evidence fields cannot be patched by conversational inference.

## Claims Discipline

Worker prose may explain results, but material claims should be emitted as structured assertions with evidence refs and verification states.

## Deterministic Tools

Where a worker delegates to static analysis, test runners, scanners, or parsers, tool outputs should be persisted as raw artifacts and referenced by the result.

## Versioning

Worker contract schemas are versioned. A worker upgrade that changes semantics must declare compatibility or trigger migration/testing.

## Invariants

1. Worker interfaces are machine-readable.
2. Lifecycle transitions consume validated schemas.
3. Material claims carry evidence references.
4. Free-form prose is explanatory, not canonical state.
5. Contract versions are explicit.
6. Raw deterministic-tool artifacts are preserved where relevant.

## Exit Criteria

An implementation agent can define stable worker request/result schemas supporting orchestration, testing, replay, and future OCE evidence envelopes.
