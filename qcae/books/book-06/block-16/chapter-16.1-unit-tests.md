# Chapter 16.1 — Unit Tests

## Mission

Prove the smallest deterministic QCAE rules independently of providers, network, sandboxes, LLMs, and OCE.

## Required Unit Targets

- Capability Contract validation/versioning;
- atom identity and composition;
- lifecycle transition legality;
- acquisition outcome vocabulary;
- hard-gate behavior;
- evidence-state transitions;
- relationship/provenance rules;
- budget arithmetic and stop rules;
- policy request normalization;
- job/step state transitions;
- deduplication and stable IDs;
- revalidation/blast-radius primitives.

## Test Properties

Core unit tests must be deterministic, fast, hermetic, and runnable without external credentials or services.

Use property-based tests where invariants are more important than individual examples, especially lifecycle legality, idempotency, relationship consistency, and serialization round-trips.

## Regression Rule

Every confirmed core bug receives a narrowly scoped regression test before the fix is considered complete.

## Invariants

1. Core domain rules are testable without infrastructure.
2. Invalid lifecycle transitions fail deterministically.
3. Serialization preserves semantic identity/version.
4. Hard gates cannot be bypassed through malformed inputs.
5. Confirmed bugs become regression fixtures.

## Exit Criteria

The core domain can be refactored aggressively while its constitutional semantics remain mechanically protected.
