# CSIA — BOOK 6 BOUNDARY REVIEW v0.1

> **Status:** PLANNING DOCUMENT — DRAFT (governance review). Not ratified.
> **Authorization:** operator-authorized Book 6 planning + governance review ONLY.
> **Grants no implementation authority.** `BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-09-30
> **Predecessor state:** Book 5 `FROZEN_ACCEPTED` at implementation anchor
> `50695ad4ea07b57105e71d04d4e32758849e55e3`, acceptance commit
> `5c387f42b4a0e01e30d6a8554d8b67a04e4e98e4`, exit gate
> `PASS_CSIA_BOOK5_CAPITAL_PLUMBING_ECONOMIC_TOPOLOGY_KERNEL`.

---

## 1. Why this document exists

Book 6 is the first book whose subject matter is *derived state about other
books' truths* rather than a new kind of truth. That is exactly where boundary
capture happens: measurement invites a silent promotion of someone else's
canonical record into a Book 6 number. This review fixes ownership **before**
metric names, so the grammar has somewhere safe to land.

Scope: governance ownership boundaries only. No contracts, no metrics, no
implementation.

## 2. Canonical ownership map

| Owner | Canonical authority (sole) |
|---|---|
| **BOOK 1** | identity, ontology, temporal graph, deployment identity, bitemporal truth |
| **BOOK 2** | evidence, propositions, claims, claim states, epistemic authority (the only epistemic engine) |
| **BOOK 3** | native architecture truth, architecture family models, execution/state semantics |
| **BOOK 4** | dependency graph truth, failure domains, substitutability, hard-runtime semantics |
| **BOOK 5** | economic records, capital topology, principal vectors, liability obligations |
| **BOOK 6** | **measurement definitions + descriptive measured state** (this book) |
| **BOOK 7** | events, narrative, evolution over time |
| **BOOK 8** | CSIA ↔ Sensor context seam |
| **SENSOR** | mechanical market observation, market-state mechanics |

**Book 6 owns:** the *definition* of what a measurement is; the *record* of what
was measured, in which unit, over which window, under which methodology, with
what coverage and missingness; and *descriptive state* derived from those
measurements.

**Book 6 does not own:** any subject truth it measures. Book 6 is a consumer of
Books 1–5 canonical truth and never a second authority for it.

## 3. Required separations (owner by owner)

### 3.1 BOOK 2 — evidence / claims / epistemic authority

- Book 2 remains the **only** epistemic engine. Book 6 introduces **no** claim
  state, **no** promotion rule, **no** confidence scale that competes with the
  Book 2 tier/claim-state model.
- Every measurement input must resolve to Book 2-backed authority. A measurement
  with no resolvable `source_claim_refs` cannot assert a value.
- Measurement records are **derived objects that cite** Book 2 authority; they
  do not themselves mint Book 2 claims. *(Whether Book 6 may ever mint a Book 2
  claim is an open operator decision — see D6M-1; this review takes the
  conservative default: no minting.)*
- Book 6 never re-decides whether evidence is current. It consumes Book 2
  currentness live at decision time, exactly as Books 4 and 5 do.

### 3.2 BOOK 3 — native architecture truth

- Book 6 measures **what Book 3 says is natively possible and natively named**.
  A metric family that does not exist for an architecture family is
  `NOT_APPLICABLE`, never zero (Axiom 1: the architecture is never forced into
  the atlas; Axiom 6: missing is not false).
- Book 6 must not invent a metric for an architecture family by EVM-shaped
  assumption ("transactions", "gas", "wallet" are not universal primitives).
  Native vocabulary comes from Book 3 family models; Book 6 may only *name* a
  measurement over vocabulary Book 3 has established.
- Book 6 never restates architecture facts. "This chain is a PoS chain" is Book
  3; "measured stake distribution as of T" is Book 6.

### 3.3 BOOK 4 — dependency / infrastructure topology

- Book 4 owns the dependency graph, failure domains, substitutability, and
  hard-runtime semantics. Book 6 **derives measured centrality** and may count
  dependencies, but may not add, remove, re-weight, or re-scope a dependency
  edge, and may not treat a measurement as a dependency fact.
- A dependency count is a **measurement of a Book 4 record**, not a substitute
  for it. `dependency_count` never repairs or overrides topology truth.
- Book 4 stays frozen; no amendment is required by this book (see §8).

### 3.4 BOOK 5 — economic records / capital topology / principal vectors

- The Book 5 → Book 6 seam is already ratified in Book 5 plan v0.3 §4: **Book 6
  owns cross-asset valuation, numeraire normalization, valuation methodology,
  price-source selection, and price observations.** Book 5 owns capital
  topology, same-unit algebra, principal vectors, liability obligations.
- **No valuation semantics leak backward.** Book 5 never gains a numeraire,
  a common-value field, or a price field as a side effect of Book 6 planning.
  `BOOK5_CROSS_ASSET_VALUATION_AUTHORITY = FALSE` remains an enforced Book 5
  invariant (B5-P32, ALG-14..18).
- A Book 5 record with heterogeneous components is a **vector**; a Book 6
  common-value observation is a **separate product** that references the vector
  plus an explicit numeraire and price observation. The two are never merged
  into one field.
- `SHARE FRACTION != VALUATION`; `PROPORTIONAL != COMMON-NUMERAIRE VALUE`
  (Book 5 v0.3 §4) — reasserted here as a Book 6 input rule.

### 3.5 BOOK 7 — events / narrative / evolution

- Book 7 owns events and narrative. Book 6 does not author an event stream and
  does not treat a narrative as measurement input.
- A measurement may be *referenced by* a Book 7 event (e.g., a state change
  event cites the measurement refs that support it); the reverse — a narrative
  becoming a measurement — is forbidden.
- Evolution-of-state over time (Book 7) is distinct from state-derivation
  (Book 6): Book 6 derives a state at a valid time; Book 7 narrates how the
  sequence of states evolved and why.

### 3.6 BOOK 8 — CSIA ↔ Sensor context seam

- Book 6 performs **no** Book 8 context-bridge authority. The D8 seam decision
  is **not** made here and remains deferred to the Book 8 gate.
- Provisional (non-final) ownership recorded for planning only: Book 6 may
  consume market observations **only** under an explicitly authorized
  measurement/valuation methodology; Sensor retains authority for all
  market-state mechanics (price state, funding, OI, liquidations, basis,
  market regime).
- No shared-seam ownership is finalized by this review.

### 3.7 SENSOR — mechanical market observation

- Sensor owns market observation production. Book 6 **consumes** Sensor
  observations as evidence-backed price/market inputs; it never redefines,
  recomputes, or corrects Sensor market mechanics, and it does not become a
  trading price engine.
- A Book 6 valuation observation must cite a price observation with source and
  timestamp. Book 6 never invents a price.

## 4. The three-anti-bleed rules (mechanically checkable at implementation time)

```text
BOOK 6 MAY NOT REWRITE A SUBJECT TRUTH IT MEASURES.
BOOK 6 MAY NOT MANUFACTURE A NUMBER FOR A DOMAIN IT DOES NOT OWN.
BOOK 6 MAY NOT UPGRADE MEASUREMENT INTO SUBJECT TRUTH.
```

Each is the negation of a capability already owned elsewhere:

| Anti-bleed rule | Would violate |
|---|---|
| No rewrite of subject truth | Book 1/3/4/5 frozen records; Book 2 authority |
| No number in an unowned domain | Axiom 1 (native before normalization); §3.2 |
| No measurement→truth upgrade | Axiom 7 (discovery ≠ promotion); Book 2 authority |

## 5. Epistemic posture of a measurement

Book 6 is a **descriptive** layer. Per Constitution §5.3a, it may state what a
system is, what changed, what evidence exists, what state it is in. It may not
rank, score, rate, target, or imply buy/sell framing. The measurement grammar
(separate document) inherits this directly: no composite score, no ranking, no
prescriptive state name.

Book 6 also does not become *predictive*. Axiom 8: descriptive before
predictive. A state that projects forward is out of scope for Book 6 v0.1.

## 6. What Book 6 must never be asked to do (anti-goals)

1. Recompute a Book 5 same-unit aggregate with a different methodology and call
   it a correction.
2. Resolve a Book 4 dependency question by counting.
3. Fill a Book 3 native-vocabulary gap by analogy with another family.
4. Convert "not applicable to this architecture" into "0".
5. Average two disagreeing sources to produce a smoother number.
6. Produce a single overall fundamental score or an ordered leaderboard.
7. Act as a price source of record.

## 7. Boundary interactions this review *does not* settle

- Whether a measurement record is a Book 2 claim or a Book 6-local derived
  record (→ **D6M-1**).
- Whether normalization is a separate contract class or an attribute of a
  metric definition (→ **D6M-2**).
- Who authors and ratifies state thresholds, and whether thresholds are
  per-dimension (→ **D6M-3**, entangled with D2-6).
- Which price-source class is authoritative for valuation (→ **D6M-4**).
- Governance of the deferred empirical usage/health parameters (→ **D6M-5**,
  the D2-6 successor).

## 8. Book amendment audit (this book only)

| Book | Amendment required? | Basis |
|---|---|---|
| BOOK 1 | **No** | identity, deployment identity, bitemporal truth sufficient as subject references; Book 1 remains frozen |
| BOOK 2 | **Conditional on D6M-1** | if Book 6 mints Book 2 claims, a Proposition/claim-vocabulary extension is needed; under the conservative default (no minting), no amendment |
| BOOK 3 | **No** | native family vocabulary is the input; Book 6 adds no architecture truth |
| BOOK 4 | **No** | dependency truth is consumed read-only; centrality is derived measurement |
| BOOK 5 | **No** | valuation seam already ratified in Book 5 plan v0.3 §4; seam is one-directional |
| CONSTITUTION | **No** (conditional on D6M-1) | §5.3a already bans prescriptive output; an epistemic-tier clause for measurement records would only be needed if measurements become Book 2 claims |

A conditional amendment is a *flag*, not a defect: Book 6 is not authorized to
amend any accepted book. If D6M-1 resolves toward Book 2 minting, that becomes
a separate operator decision with its own amendment path.

## 9. Boundary verdict

Boundaries are **sufficiently determinate** to draft a Book 6 plan: every
measurement input has exactly one canonical owner, and the three anti-bleed
rules give implementation-time checks. The unresolved items are governance
choices (D6M-1..5), not missing boundaries — so this review does not block
planning.

```text
BOOK_6_BOUNDARY_REVIEW = COMPLETE
BOOK_6_BOUNDARY_BLOCKERS = 0
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
D8_SEAM_DECISION = DEFERRED (Book 8 gate)
```
