# Chapter 16.8 — License Conflict Tests

## Mission

Prove that QCAE distinguishes license evidence, acquisition form, ambiguity, and transitive obligations without guessing favorable outcomes.

## Fixture Classes

- permissive top-level license with conflicting vendored component;
- missing license;
- custom license;
- package metadata disagreeing with repository file;
- code/data/model using different licenses;
- acquisition form that changes compatibility outcome;
- reimplementation path with separate provenance;
- license change between monitored versions.

## Expected Behavior

QCAE should emit `COMPATIBLE`, `COMPATIBLE_WITH_OBLIGATIONS`, `INCOMPATIBLE`, `REQUIRES_REVIEW`, or `UNKNOWN` according to evidence and policy. Ambiguity must never be silently normalized to a permissive license.

## Invariants

1. License is asset- and acquisition-form scoped.
2. Transitive conflicts remain visible.
3. Missing/custom terms trigger uncertainty/review.
4. Reimplementation and direct source reuse are distinct paths.
5. License drift triggers revalidation.

## Exit Criteria

The license subsystem demonstrates conservative, evidence-based behavior across representative compatibility traps.
