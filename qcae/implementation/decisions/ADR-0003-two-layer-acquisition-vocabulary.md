# ADR-0003 — Two-Layer Acquisition Vocabulary (Resolution Mode over Acquisition Form)

**Status:** Accepted (P0-A001)
**Phase:** P0-A001 amendment reconciliation
**Canon/Amendment refs:** Canon 0.5.12 (frozen), A-001 §8, §13 (P8), reconciliation prompt §4

## Context

A-001 §8 expands acquisition decisions to a coarse institutional economic layer:
`USE / BORROW / RENT / BUY / ACQUIRE / BUILD / RESEARCH / DECLINE`. QCAE core
already carries the frozen canon-0.5.12 `AcquisitionForm` vocabulary
(`USE_DIRECT, USE_DEPENDENCY, WRAP_LIBRARY, WRAP_SERVICE, FORK, VENDOR,
EXTRACT_*, REIMPLEMENT_*, USE_AS_REFERENCE, USE_AS_ARCHITECTURAL_PRIOR, DEFER,
REJECT`).

The reconciliation prompt explicitly forbids casually destroying the existing
vocabulary and directs a layered design unless a semantic collision with canon
exists.

## Alternatives

1. **Replace `AcquisitionForm` with the new vocabulary.** Rejected: silently
   rewrites frozen canon 0.5.12 semantics and breaks contract/decision records
   already committed in P0.
2. **Merge both vocabularies into one enum.** Rejected: conflates institutional
   economics (rent vs buy vs build) with implementation form (wrap vs vendor vs
   extract); a single RENT decision may be realized through several forms, and
   a single form (VENDOR) may serve BUY or ACQUIRE.
3. **Two-layer model: `CapabilityResolutionMode` (institutional) over
   `AcquisitionForm` (implementation).** Accepted.

## Decision

Add `qcae/core/amendments/a001/resolution.CapabilityResolutionMode` as the
higher-level institutional resolution vocabulary. `AcquisitionForm` remains the
lower-level implementation-form vocabulary. P0 ships vocabulary and reference
semantics only; no mapping table is imposed, and the full economic decision
engine comparing modes is P8 scope (A-001 §13).

## Reason

A-001 §8 itself describes the new vocabulary as an *expansion of decision
scope* ("capability-gap resolution"), not a redefinition of implementation
forms. The two layers answer different questions: "does the institution use,
borrow, rent, buy, absorb, build, research, or decline?" versus "what concrete
implementation shape does the acquisition take?". Layering preserves frozen
canon (no amendment may silently rewrite it, A-001 §2) while adding the
amendment's obligations additively.

## Burden

- Two vocabularies must be kept conceptually distinct in later phases; P8's
  decision engine will need an explicit mode→form linkage when it lands.
- Slight redundancy in English words (USE vs USE_DIRECT) is intentional.

## Reversibility

High. `CapabilityResolutionMode` is a new, isolated enum; folding or renaming
it later is a contained change.

## Canon Compatibility

No canon clause contradicted. Canon 0.5.12 remains the authoritative
acquisition-spectrum form vocabulary; A-001 §15 invariant 10 explicitly keeps
frozen canon frozen and governs interfaces/interpretation.
