# ADR-0001 — Core Domain Representation & Validation Style

**Status:** Accepted (P0)
**Phase:** P0 — Skeleton + Domain Schemas
**Canon refs:** Book V 15.2 (core domain boundaries), 15.1 invariant 1 (domain packages provider-neutral)

## Context

QCAE core domain objects (CapabilityContract, CapabilityAtom, CompositeCapability,
Candidate, Relationship, EvidenceRef, LifecycleState, AcquisitionDecision, Job/Step,
Authority interfaces) must be:

- provider-neutral (15.2 forbidden-dependency list);
- serializable/versioned for persistence and handoffs (15.2 invariant 5);
- validated at construction time ("invalid state transitions or malformed core
  objects fail before provider execution" — 15.2 Domain Validation);
- cheap to reason about and diff in review.

## Constraints

- `qcae/core` must not import provider SDKs, database engines, web frameworks, or OCE
  packages (15.2).
- The repo root `pyproject.toml` already carries heavy dependencies for quant-lab;
  QCAE core must not couple to any of them.
- Python 3.12 (`.python-version`), pytest 9 already in dev group.

## Alternatives

1. **pydantic v2 models.** Strong validation and JSON schema, but a third-party
   runtime dependency inside the most protected layer; version churn in the
   validation library would rewrite core semantics; heavier than needed for a
   domain that is small and hand-specified by frozen canon.
2. **attrs.** Lighter than pydantic but still an external dependency in core for
   marginal benefit over stdlib at this scale.
3. **stdlib dataclasses + explicit `validate()` methods + frozen instances.**
   Zero core dependencies; validation logic is explicit, readable, and maps 1:1 to
   canon clauses; frozen (immutable) instances match the append-oriented,
   non-silently-overwritten semantics the canon requires of durable records.

## Decision

QCAE core domain objects are **stdlib `dataclasses` (frozen), with explicit
per-class `validate()` methods raising `QcaeValidationError`, and a uniform
`SCHEMA_VERSION` + `to_dict()/from_dict()` serialization contract** implemented on
a shared base in `core/serialization.py`.

JSON remains the interchange encoding; hashing/persistence engines are P1
infrastructure concerns and stay out of core.

## Reason

The domain is small, canon-frozen, and stability-critical. Explicit validation
makes every canon rule auditable in code review and keeps the dependency center of
the architecture truly dependency-free (15.2 invariant 1). Any future switch to a
validation library is a contained, reversible change confined to core.

## Burden

- Hand-written validators must be maintained as canon evolves (acceptable: canon
  changes are already formal amendment events).
- Slightly more boilerplate than pydantic at P0 (~10 domain classes).

## Reversibility

High. Swapping the validation mechanism later touches only core domain files;
serialized dict shapes (the actual contract with P1+ layers) are unchanged.

## Canon Compatibility

Directly implements 15.2 invariants 1 and 5 and the 15.2 Domain Validation rule.
No canon object contradicted.
