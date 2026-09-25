# CSIA Book 4 Epistemic Reconciliation

- **Version:** v0.1
- **Date:** 2026-09-24
- **Status:** PLANNING_RECONCILIATION
- **Scope:** Book 4 planning only
- **Supersedes for Book 4 planning:** conflicting evidence-state and confidence-state language in Book 4 v0.1 artifacts
- **Preserves:** Book 4 v0.1 files as historical planning artifacts; no v0.1 file is rewritten

## 1. Inconsistency found

Book 4 v0.1 introduced `VERIFIED` and `CONFLICTED` in the evidence-state rules and
included a candidate `confidence_state` in the `DependencyRecord`. Those labels
were not part of the accepted Book 2 ClaimState contract and could be mistaken
for a second Book 4 claim-state machine.

## 2. Accepted Book 2 ClaimState contract

Book 4 inherits the accepted Book 2 states exactly:

```text
DECLARED
OBSERVED
INFERRED
CORROBORATED
CONTESTED
UNRESOLVED
STALE
REJECTED
SUPERSEDED
```

Book 4 does not define, rename, extend, or transition these states. Book 2 owns
claim creation, evidence lineage, promotion, contradiction, staleness, rejection,
and supersession.

## 3. Inheritance rule

Every canonical Book 4 fact references canonical Book 2 claims through
`book2_claim_refs[]`. Book 4 reads the Book 2 state and lineage; it never
reclassifies the claim. A Book 4 record may be scoped, typed, or rejected because
of its own domain requirements, but its epistemic authority comes from Book 2.

The following are Book 2 states, not Book 4 alternatives:

- `DECLARED`: a source assertion only; insufficient for deployed dependency truth.
- `OBSERVED`: an observed claim with bounded scope.
- `INFERRED`: a derived claim retaining methodology and parent lineage.
- `CORROBORATED`: accepted sufficiently corroborated claim under Book 2 rules.
- `CONTESTED`: supported disagreement; do not strengthen Book 4 truth.
- `UNRESOLVED`: contradiction or insufficient resolution; fail closed.
- `STALE`: cannot establish current dependency truth.
- `REJECTED`: cannot support Book 4 truth.
- `SUPERSEDED`: historical only; not current truth.

`VERIFIED` and `CONFLICTED` are not Book 2 ClaimState values and must not appear as
Book 4 claim states. `CONTESTED` and `UNRESOLVED` are the accepted Book 2
alternatives where relevant.

## 4. Epistemic state versus domain classification

Book 4 domain values are separate from Book 2 ClaimState. For example:

```text
Book 2 claim state: CORROBORATED
Book 4 dependency strength: UNKNOWN
```

The first describes the evidence status of the underlying claim. The second
describes the architectural dependency property. Both may be true at once. A
Book 4 domain `UNKNOWN` is not a Book 2 state and cannot override a `CONTESTED`,
`UNRESOLVED`, `STALE`, `REJECTED`, or `SUPERSEDED` claim.

The same separation applies to role lifecycle state. `role_state` is a Book 4
role-lifecycle/domain value, not a Book 2 ClaimState.

## 5. Confidence-state correction

The v0.1 `DependencyRecord.confidence_state` candidate is removed from the
canonical Book 4 v0.2 contract. Epistemic authority is resolved through
`book2_claim_refs[]`. If a future implementation exposes a convenience field, it
must be a derived view of Book 2 state, clearly namespaced, and incapable of
becoming independent authority.

## 6. Result

**RECONCILED.** The correction is narrow: it removes a parallel epistemic
vocabulary, preserves all accepted Book 2 meanings, and leaves v0.1 historical
artifacts intact. No Book 1, Book 2, or Book 3 contract is mutated.
