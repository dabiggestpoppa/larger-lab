# Chapter 16.10 — Evidence Integrity Tests

## Mission

Prove that QCAE's evidence, receipts, provenance, and lifecycle state cannot be silently mutated, detached from source revisions, or rewritten by later summaries.

## Test Classes

- artifact hash mismatch;
- mutated raw evidence after receipt creation;
- missing provenance edge;
- stale contract/candidate revision;
- duplicate idempotent submission;
- conflicting evidence envelopes;
- schema migration round-trip;
- backup/restore;
- negative-knowledge retention;
- partial evidence incorrectly summarized as pass.

## Receipt Reconstruction

Given canonical structured objects and raw evidence refs, regenerate a receipt and verify that material fields match the stored decision context.

## Historical Immutability

New evaluations supersede previous state through explicit relationships. Tests should fail if an implementation overwrites the historical evidence chain.

## Invariants

1. Evidence mutation is detectable.
2. Provenance remains reconstructable.
3. Receipts derive from canonical evidence/state.
4. Idempotent submissions do not create duplicate truth.
5. Schema migration preserves meaning.
6. Negative and contradictory evidence survives summarization and restore.

## Exit Criteria

QCAE demonstrates that its durable memory can be trusted after crashes, migrations, revalidation, and later OCE federation.
