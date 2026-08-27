# Chapter 12.1 — Orchestrator

## Mission

The Orchestrator is QCAE's lifecycle coordinator. It converts an accepted request into a sequence of bounded jobs, selects workers, enforces prerequisites, tracks evidence state, and decides what investigation step is next.

It is not a super-agent allowed to skip subsystem contracts.

## Core Responsibilities

- load Capability Contract and current lifecycle state;
- query prior memory before new work;
- construct a job graph;
- select workers by declared capability;
- enforce input/output schemas;
- enforce evidence prerequisites;
- track unresolved questions and contradictions;
- apply budget/stop policies;
- request human/policy decisions at authority boundaries;
- persist state after each successful transition;
- resume safely after interruption.

## Job Graph

The canonical orchestration model is a directed job graph, not one giant prompt:

```text
contract
→ internal lookup
→ discovery
→ repository intelligence
→ forensics
→ trust screening
→ proving
→ quant validation if required
→ acquisition recommendation
→ authority request
→ integration/monitoring registration
```

Branches may run in parallel when independent. Gates join only when required evidence exists.

## Decision Rules

The Orchestrator may decide:

```text
CONTINUE
BRANCH
RETRY
DEFER
REQUEST_MORE_EVIDENCE
PROPOSE_CONTRACT_AMENDMENT
ESCALATE
STOP_REJECTED
STOP_SATURATED
```

It may not invent authority or reclassify failed hard gates.

## State Discipline

Conversation context is never the canonical job state. Durable state must contain:

```text
job_id
contract_id/version
lifecycle_state
completed_steps
active_steps
artifacts/evidence refs
unresolved questions
contradictions
budgets consumed
policy decisions
next eligible actions
```

## Planning vs Execution

The Orchestrator plans the next bounded unit of work. Specialized workers perform domain tasks. This limits context pollution and makes worker outputs independently testable.

## Idempotency

Repeated orchestration after crash must not duplicate irreversible operations. Each job step uses stable IDs and checks for existing valid output before rerunning.

## Invariants

1. Orchestrator coordinates; it does not become every worker.
2. Durable artifacts outrank chat memory.
3. Lifecycle gates are enforced mechanically.
4. Failed hard gates cannot be overridden by model preference.
5. Resumption is state-based and idempotent.
6. Authority remains external to orchestration reasoning.

## Exit Criteria

An implementation agent can build an Orchestrator that advances QCAE through explicit jobs and evidence-gated states without relying on one continuous LLM context.
