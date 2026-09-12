# ADR-0004 — DEFERRED Lifecycle Semantics

**Status:** Accepted (P0-A001)
**Phase:** P0-A001 amendment reconciliation
**Canon refs:** Book I 0.5.15, 0.5.18, 1.1.6; Book IV 8.1, 9.4, 11.6

## Context

P0 shipped DEFERRED as enterable but with no outgoing transitions and without
membership in `TERMINAL_STATES` — an ambiguous state. The reconciliation
prompt requires one evidence-backed interpretation:

- **A.** DEFERRED is terminal for that decision/version; renewed investigation
  creates a new/superseding lifecycle object.
- **B.** DEFERRED is resumable with one explicit governed transition back into
  a review/evaluation state.

## Evidence

- Canon 0.5.15 defines DEFERRED as "neither approved nor rejected because a
  material dependency is unresolved" — a statement about the world *at decision
  time*, tied to specific candidate/contract versions.
- Book IV 11.6 (bounded autonomous proposal loop): "deferred proposals all
  return to memory so proposal quality improves **without repeatedly reopening
  settled work**."
- Book IV 8.1: "One bounded acquisition plan — or explicit reject/defer state —
  exists with evidence."
- Canon 1.1.6 and 1.3.11: verdicts are scoped to contract versions; materially
  changed candidates get a **new evaluation**, never an overwrite.
- Canon 0.4.7 (staleness): evidence is revision-scoped; resuming an old object
  across changed circumstances would silently extend stale evidence.

## Decision

**Interpretation A.** DEFERRED joins REJECTED/SUPERSEDED/RETIRED as a terminal
state:

- A DEFERRED decision object is durable negative/parked knowledge scoped to
  the candidate revision and contract version it was evaluated against.
- When the blocking dependency resolves (or circumstances change), renewed
  investigation creates a **new** lifecycle/decision object that supersedes the
  deferred one via the existing `supersedes_decision` /
  `supersedes_contract` lineage fields. The deferred object's evidence remains
  historical knowledge (canon 0.2.8, 1.3.11).

## Reason

Deferral exists because a material dependency is unresolved *now*. If that
dependency later resolves, the new situation is a new evaluation context: the
candidate may have changed, the contract may have been amended (invalidating
prior comparisons per 1.1.13), and the market/ecosystem may have moved.
Resuming the old object (option B) would either falsify its version-scoped
verdict semantics or require evidence the old object was never scoped to
carry. Option A matches the canon's supersession pattern everywhere else
(1.1.6, 1.3.11, 0.5.18) and Book IV's explicit anti-reopening doctrine.

## Burden

- Renewed investigation must create and link a new object (one extra record
  with a supersession ref) instead of flipping a state flag.
- Registry queries for "currently deferred work" must filter on the *newest*
  object in a lineage; P1's registry spine should index supersession edges
  (already representable via the relationship vocabulary: `supersedes`).

## Reversibility

High. Adding a legal DEFERRED outgoing transition later is additive to the
transition table; terminality is the conservative choice and can be relaxed
with evidence, while retracting it after resume-style data accumulated would
be far harder.

## Canon Compatibility

No canon clause contradicted: 0.5.15 is honored (deferred ≠ approved ≠
rejected; evidence-backed and persisted); 0.2.8 and 11.6 are directly enforced;
no silently reopened settled work.
