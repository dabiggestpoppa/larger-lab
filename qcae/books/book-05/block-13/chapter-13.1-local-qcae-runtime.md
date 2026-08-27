# Chapter 13.1 — Local QCAE Runtime

## Mission

Provide the minimum durable services required to run QCAE independently on local infrastructure while preserving the same domain semantics later used under OCE governance.

## Runtime Components

```text
orchestrator service
worker execution layer
job/state store
evidence/artifact store
local policy engine
sandbox manager
registry/memory store
secrets boundary
CLI/API
monitor scheduler
```

These may initially run in one process or a small local composition. The architecture should not force distributed deployment before justified.

## Local-First Rule

Core discovery planning, source analysis, memory, evidence, and most proving should be operable locally. External APIs/services are adapters, not required control-plane dependencies unless the capability specifically needs them.

## Process Topology

Start simple:

```text
qcae daemon / application
→ durable local stores
→ isolated worker/sandbox processes
→ external adapters as needed
```

Split into services only when isolation, scale, or operational evidence justifies it.

## Runtime Identity

Every running instance exposes:

```text
runtime_id
version/build commit
schema versions
policy version
registered workers
registered adapters
storage locations
OCE mode: absent/connected
```

## Startup Validation

Fail closed if required schema migrations, policy files, evidence paths, or sandbox prerequisites are inconsistent.

## Invariants

1. Standalone mode is fully usable for core QCAE workflows.
2. Local-first is the default control plane.
3. Distributed services are earned by need, not assumed.
4. Runtime identity/configuration is inspectable.
5. Startup validates policy/schema/storage integrity.
6. External provider failure does not destroy core state.

## Exit Criteria

An implementation agent can define a concrete local runtime topology that executes Book V worker contracts without depending on unfinished OCE infrastructure.
