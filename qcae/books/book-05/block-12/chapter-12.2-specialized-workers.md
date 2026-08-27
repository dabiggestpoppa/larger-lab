# Chapter 12.2 — Specialized Workers

## Mission

QCAE uses specialized workers so discovery, comprehension, security, proving, quant validation, evidence, and integration can operate with narrow contexts and independently testable responsibilities.

## Initial Worker Roster

```text
Capability Planner
Internal Discovery Worker
External Discovery Worker
Repository Intelligence Worker
DeepWiki/Comprehension Worker
Capability Forensics Worker
License Worker
Supply Chain/Security Worker
Sandbox/Build Worker
Contract Test Worker
Adversarial Test Worker
Benchmark Worker
Quant Validation Worker
Integration Architect
Evidence/Receipt Worker
Registry Worker
Upstream Monitor
Critic/Review Worker
```

This roster is logical, not necessarily one process/model per name. Implementation may combine roles when doing so preserves boundaries.

## Worker Capability Declaration

Each worker declares:

```text
worker_type
accepted_input_schemas
emitted_output_schemas
allowed_tools
allowed data classes
allowed side effects
required policy scopes
cost class
timeout/retry policy
```

## Least Context

Workers receive only the context needed for their task plus references to source artifacts. They should not ingest the full project history by default.

## No Self-Certification

A worker that generates an artifact should not be the sole authority validating that artifact when independent review materially reduces risk.

Examples:

- Discovery worker does not prove candidate correctness.
- Integration architect does not approve its own production promotion.
- Quant reconstruction worker does not count its own reproduced backtest as independent validation without the prescribed test path.

## Critic/Review Worker

A reviewer may challenge:

- unsupported claims;
- missing evidence;
- contract drift;
- hidden coupling;
- optimistic assumptions;
- incomplete negative knowledge.

The critic can request more work; it cannot invent contrary evidence.

## Worker Replacement

Workers are addressed by contract, not model/provider identity. A stronger model or deterministic analyzer can replace one implementation without changing orchestration semantics.

## Invariants

1. Worker roles are capability-bounded.
2. Tool/data authority is least-privilege.
3. Workers exchange artifacts, not implicit shared cognition.
4. No worker self-certifies across hard authority boundaries.
5. Worker implementation is replaceable behind stable contracts.
6. Logical specialization does not require unnecessary microservices.

## Exit Criteria

QCAE has a clear worker topology whose responsibilities align directly with Books I–IV and can evolve without collapsing back into a single context-heavy agent.
