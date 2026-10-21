# Chapter 13.8 — Graceful OCE Absence

## Mission

Guarantee that unfinished, unavailable, or disconnected OCE infrastructure never blocks QCAE's core discovery, comprehension, proving, memory, and locally authorized workflows.

## Mode States

```text
OCE_ABSENT
OCE_AVAILABLE_UNGOVERNED
OCE_CONNECTED_SHADOW
OCE_GOVERNING
OCE_DEGRADED
```

The exact future state names may change; the invariant is explicit mode awareness.

## Standalone Authority

When OCE is absent, the local AuthorityProvider and policy engine remain canonical for actions within standalone scope.

## No Hidden Dependency

Core modules must not import OCE implementation packages directly. OCE communication occurs through adapters/contracts defined in Block 14.

## Degraded Operation

If OCE later becomes temporarily unavailable while governing, QCAE must not silently fall back to broader local authority. Read-only/research work may continue only under predefined degraded-mode policy; protected actions wait or fail closed.

## Sync Later

Standalone evidence, receipts, and decisions are retained with provenance so they can later be submitted/federated to OCE. OCE may accept, reject, or require revalidation; synchronization never rewrites historical local evidence.

## Migration Testing

Before switching to OCE governance, run shadow/dual-evaluation where practical to compare local policy decisions and OCE decisions without granting new authority.

## Invariants

1. QCAE core runs without OCE.
2. Core domain modules do not depend on OCE implementation details.
3. Loss of OCE never causes privilege expansion.
4. Standalone evidence remains historically intact after federation.
5. Governance migration is tested before cutover.
6. Protected actions fail closed during governing-provider ambiguity.

## Exit Criteria

Standalone QCAE is a durable system whose future OCE integration is an authority-provider transition, not a rewrite or operational dependency trap.
