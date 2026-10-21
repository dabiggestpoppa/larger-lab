# Chapter 13.7 — Standalone CLI/API

## Mission

Expose QCAE through stable human and machine interfaces without leaking internal worker/provider details into user workflows.

## Initial CLI Surface

Conceptual commands:

```text
qcae acquire <capability-request>
qcae investigate <source>
qcae compare <candidate...>
qcae verify <candidate-or-capability>
qcae receipt <id>
qcae registry search <query>
qcae monitor <capability>
qcae jobs list/show/resume/cancel
qcae evidence show <id>
qcae policy explain <decision>
```

Exact syntax is implementation-stage work.

## API Principles

API resources should expose domain objects:

```text
contracts
jobs
candidates
capabilities
evidence
receipts
monitoring
policy requests/decisions
```

Do not expose one endpoint per worker or model provider as the primary public architecture.

## Async Operations

Long-running operations return job IDs and status rather than holding one request open indefinitely.

## Human-Readable + Structured

CLI can render concise summaries, but all commands should be able to emit machine-readable output for agent/automation use.

## Safe Defaults

Potentially side-effecting actions show the authority state and require explicit approval where policy demands it. Read-only investigation remains easy.

## Stable Interface

CLI/API versioning must be separate from worker/model changes. Replacing DeepWiki or an LLM should not break user-facing commands.

## Invariants

1. Public interfaces expose QCAE domain objects, not provider internals.
2. Long work is job-based/asynchronous.
3. Machine-readable output is first-class.
4. Authority status is visible for side-effecting operations.
5. Provider/worker replacement does not redefine the public API.
6. CLI/API operate fully in standalone mode.

## Exit Criteria

Users and future agents can operate QCAE consistently without needing to understand its internal worker topology.
