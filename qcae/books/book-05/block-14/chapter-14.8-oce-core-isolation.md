# Chapter 14.8 — OCE Cannot Pollute QCAE Core

## Mission

Prevent future governance integration from turning QCAE into an OCE-specific subsystem whose domain logic, tests, or runtime become unusable without OCE.

## Dependency Rule

Core QCAE packages may depend on abstract governance contracts. They may not import concrete OCE implementation packages.

Preferred direction:

```text
qcae core
→ governance interfaces
← standalone adapters / OCE adapters
```

Forbidden direction:

```text
qcae capability model
→ OCE internal database/policy classes
```

## Domain Purity

Capability Contract, Atom, Evidence, Receipt, Discovery Plan, Forensic Package, Proving Package, and Acquisition Decision semantics remain QCAE-owned and independently testable.

## Adapter Containment

OCE-specific:

- authentication;
- policy transport;
- event transport;
- registry synchronization;
- evidence submission;
- secret provider;

live under adapter/integration packages.

## Test Matrix

QCAE must retain tests for:

```text
core with fake providers
standalone providers
OCE adapters via contract tests
OCE unavailable/degraded behavior
```

No core test should require a live OCE instance.

## Upgrade Independence

OCE schema/API changes are absorbed in the adapter until they genuinely require a versioned governance-contract amendment. Internal OCE refactors should not propagate into QCAE domain code.

## Exit Independence

If OCE integration is temporarily removed, QCAE can return to standalone governance without losing capability/evidence semantics, subject to policy/authority migration rules.

## Invariants

1. Concrete OCE code never becomes a core QCAE dependency.
2. QCAE domain objects remain system-independent.
3. OCE-specific transport/auth/storage is adapter-contained.
4. Core tests run without OCE.
5. OCE internal changes do not automatically become QCAE changes.
6. QCAE preserves a credible standalone operating path.

## Exit Criteria

Future OCE wiring can be developed, tested, upgraded, or temporarily removed without rewriting or contaminating QCAE core intelligence.
