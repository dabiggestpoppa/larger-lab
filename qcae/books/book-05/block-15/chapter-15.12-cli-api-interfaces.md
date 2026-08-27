# Chapter 15.12 — CLI/API Interfaces

## Mission

Implement the public control surface around stable application services so humans, build agents, and future OCE/automation clients can operate QCAE without coupling to internal worker topology.

## Interface Layers

```text
interfaces/cli/
interfaces/api/
application/use_cases/
core/domain
```

CLI/API call application use cases, not workers directly.

## Primary Use Cases

```text
create capability request
inspect/approve contract
start/resume/cancel job
investigate source
compare candidates
run verification
read capability receipt
search capability/negative memory
register/inspect monitoring
request acquisition/promotion
inspect policy/evidence
```

## Async Job Contract

Long-running commands return `job_id`, lifecycle state, and relevant next action. Polling/event subscriptions operate on job/domain state rather than worker sessions.

## Output Modes

Support:

- concise human-readable output;
- detailed report rendering;
- stable JSON/structured output;
- artifact/evidence references.

## Error Model

Public errors map to domain categories:

```text
INVALID_REQUEST
CONTRACT_NOT_READY
POLICY_DENIED
APPROVAL_REQUIRED
JOB_BLOCKED
EVIDENCE_INSUFFICIENT
PROVIDER_UNAVAILABLE
INTERNAL_FAILURE
```

Provider-specific details may appear in diagnostics but not define API semantics.

## Authentication/Authority

Standalone CLI uses local identity/policy. Governed API routes identity through the configured provider. The application layer receives generic principal/authority context.

## Versioning

Public API/schema changes are versioned independently from internal worker/model upgrades. Deprecation/migration is explicit.

## Invariants

1. CLI/API invoke application use cases, not workers directly.
2. Public semantics are domain-oriented and provider-neutral.
3. Long-running work is job-based.
4. Structured output is first-class.
5. Error/authority semantics are stable across providers.
6. Internal worker/model changes do not silently break user interfaces.

## Exit Criteria

The coding agent can expose QCAE as a durable local CLI and machine API while preserving the internal architecture and future OCE migration path.
