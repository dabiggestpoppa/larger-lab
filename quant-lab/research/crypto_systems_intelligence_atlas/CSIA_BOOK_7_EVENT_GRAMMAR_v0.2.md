# CSIA — BOOK 7 EVENT GRAMMAR v0.2

> **Status:** PLANNING DOCUMENT — DRAFT (successor). Not ratified. No implementation.
> **Supersedes (on plan ratification):** `CSIA_BOOK_7_EVENT_GRAMMAR_v0.1.md`
> (v0.1 preserved unmodified as history). Two changes in v0.2:
> (a) **§5 lifecycle repaired** — the v0.1 state list could be misread as a
> mandatory universal sequential machine; v0.2 makes it explicitly a set of
> independent, family-applicable **occurrence statuses** with non-normative
> illustrative ordering (Phase 19 audit finding: NOT mechanically unambiguous in
> v0.1); (b) §8.6 records that lifecycle statuses are **distinct from the nine
> response outcomes** of the Reconciliation v0.1 — no vocabulary may merge.
> **Date:** 2026-10-01 · **Authority:** `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Scope:** Bloc 7A — grammar, contracts, identity, taxonomy, lifecycle,
> temporality, structural seam, family stress notes.

---

## 1. The six-way separation (unchanged)

```text
EVENT           something happened in the world (or is claimed to), anchored in time
CLAIM           an assertion that may be true or false — Book 2's object
NARRATIVE       a circulating story connecting claims, events, objects — Bloc 7B
ACTION          a deliberate act by an actor (declare, deploy, execute)
STATE CHANGE    a difference between two accepted canonical states — Books 1-5 own it
EVIDENCE        the grounding for any belief in the above — Book 2 owns it
```

## 2. Canonical event contracts (planned, not implemented)

```text
EventIdentity · EventOccurrence · EventClaimLink · EventObjectImpact ·
EventStatus · EventTemporalWindow · EventEvidenceBinding · EventSeries (recurrence,
staged programs) · EventOutcomeSet (see §5.2)
```

Derived (never independent): an event's **report set** — evidence, not identity.

## 3. Identity doctrine (unchanged)

```text
REPORT_COUNT != EVENT_COUNT
```

Identity key `(subject_scope, event_family, occurrence_signature, temporal_anchor)`;
family-defined `occurrence_signature` (contract address + deploy tx; proposal id +
execution tx; incident/tx set; instrument id + jurisdiction). Recurrence = series
of distinct identities; multi-stage programs = one series with per-stage events;
announcement ≠ occurrence; one event with N `EventObjectImpact` rows for
multi-subject events; identity conflict ⇒ `IDENTITY_CONTESTED` (never resolved by
report majority — AB-3). Final doctrine = `D7N-1`.

## 4. Family taxonomy (unchanged from v0.1 §4; dispositions in the candidate matrix)

8 KEEP families (UPGRADE, INTEGRATION, MIGRATION, EXPLOIT, OUTAGE, GOVERNANCE,
REGULATORY_EVENT, TOKENOMICS_CHANGE) + 4 REVISE (LAUNCH, INSTITUTIONAL_ADOPTION,
BRIDGE_CHANGE, STABLECOIN_CHANGE → attributes) + venue/LISTING deferred to the
market seam. Families are mechanism classes, not news sections.

## 5. Lifecycle (Phase 19 repair) — statuses, not a sequence machine

### 5.1 Occurrence statuses (the set; ordering is NON-normative)

```text
REPORTED              at least one source utterance exists; no occurrence evidence
DECLARED              a responsible actor announced/committed (declared action)
CONFIRMED_OCCURRENCE  Book 2 authority (E0-E2 per family bar) establishes occurrence
ONGOING               begun, not completed (outage; migration dual-running)
RESOLVED              completed/ended with evidence
REVERSED              completed then rolled back, with evidence
SUPERSEDED            a later occurrence replaced this one's effect (recorded, not erased)
CONTESTED             credible sources disagree on occurrence/cause/impact
UNKNOWN               lifecycle cannot be established — explicit, preserved
```

**Repaired doctrine (v0.2):**

```text
- These are OCCURRENCE STATUSES (dimensions), NOT a mandatory sequential
  state machine. The order above is ILLUSTRATIVE ONLY and carries no normative
  force; an implementation MUST NOT encode the list as a required transition
  path.
- Applicability is FAMILY-DEFINED: each family declares which statuses it may
  ever occupy (v0.1 said "family-applicable subsets"; v0.2 states that the
  applicable subset is part of the family contract and is machine-readable,
  not left to inference).
- Statuses may apply SIMULTANEOUSLY where meaningful (e.g., ONGOING + CONTESTED;
  RESOLVED + SUPERSEDED). A single scalar lifecycle field is therefore
  REJECTED in Book 7: the EventStatus contract is a SET of statuses with an
  evidence binding per status.
- NO STATUS IS IMPLICIT: absence of a status is absence of the status, never a
  default value and never "cleared."
- No lifecycle complexity is invented beyond this set. No status may be added
  without a family contract that cannot be expressed by the existing nine.
- Lifecycle statuses remain SEPARATE from Book 2 ClaimState (AB-2) and from the
  nine RESPONSE OUTCOMES of Response Semantics Reconciliation v0.1 §7
  (a ResponseOutcome lives on a ResponseLink, never on an EventStatus).
```

### 5.2 Outcome vs status (non-merger, recorded)

An event's `CONFIRMED_OCCURRENCE` (an occurrence fact) is independent of any
later usage/capital response assessment (`CHANGE_OBSERVED` etc.). A confirmed
event with no measured response, and a reported event with a measured response,
are both coherent; no lifecycle status may be set or cleared by response
outcomes, and no response outcome may be set by lifecycle status.

**Separation from Book 2 (AB-2), restated:** the lifecycle describes occurrence
history, not epistemic status; `CONFIRMED_OCCURRENCE` means "Book 2-backed
evidence establishes the occurrence," never "the narrative is true." Event
records carry `EventEvidenceBinding` refs; they mint no claims, hold no claim
states, cannot promote anything (AB-1/AB-2).

## 6. Temporal model (unchanged)

Seven event fields (`reported_at, announced_at, scheduled_for, began_at,
effective_at, completed_at, resolved_at`) on Book 1's bitemporal axes
(`observed_at, valid_from, valid_to, source_published_at, ingested_at,
superseded_at`). Invariants: `report time != event time != effective time !=
observation time`; family subsets; unused fields ABSENT, never null-filled;
unknown valid times carry explicit uncertainty markers (§12.2); late discovery
enters transaction-time late.

## 7. Event → structural change seam (unchanged)

```text
EVENT SAYS CHANGE OCCURRED != BOOK 7 WRITES THE STRUCTURAL FACT
CHANGED · CHANGE_CLAIMED · NO_CHANGE_FOUND · NOT_APPLICABLE   (reference-only)
```

Examples: upgrade→Book 3 dossier change; integration→Book 4 DependencyRecord;
migration→Book 3 lineage + Book 4 relations; tokenomics→Book 5 parameters +
Book 6 consequences; stablecoin→Book 5 realization/topology. Book 7 may observe
that an owning book lacks a claimed record (a contradiction row) but never mints
it (AB-1).

## 8. Family stress notes (unchanged from v0.1 §8)

### 8.1 Security events
`REPORT != SUSPECTED INCIDENT != CONFIRMED INCIDENT != IMPACT ESTIMATE != LOSS CLAIM != RECOVERY != POSTMORTEM`. Media establishes at most REPORT/SUSPECTED; occurrence, cause, and amount need separate Book 2 evidence bindings; loss claims are preserved per source, un-averaged; attribution beyond evidence stays UNKNOWN.

### 8.2 Governance events
`proposal != vote != approval != execution != activation != rollback`. Each stage is a distinct status transition with its own evidence binding; rejected proposals are first-class occurrences.

### 8.3 Regulatory events
Jurisdiction is an identity component; stages proposal/guidance/rule/law/court/enforcement + `effective_at`; no cross-jurisdiction generalization.

### 8.4 Institutional adoption
`announcement != pilot != integration != custody support != asset issuance != production usage != capital allocation`; `PARTNERSHIP ANNOUNCEMENT != INSTITUTIONAL ADOPTION` without explicit criteria.

### 8.5 Tokenomics events
`proposal != scheduled != executed`; issuance/burn/staking/unlock/treasury staged; economic consequences by Book 5/6 reference only.

### 8.6 Response-layer separation (added in v0.2)
An event may be linked to a `ResponseLink` (Reconciliation v0.1), but event
status and response outcome never merge (§5.2). An "unchanged" measurement after
an event does not make the event REVERSED, and a measured change does not make
the event CONFIRMED.

## 9. Verdict

```text
EVENT_GRAMMAR_V0.2 = PLANNED
LIFECYCLE_REPAIR   = COMPLETE (statuses, not sequence; set-valued; no implicits;
                     family contracts machine-readable; no added complexity)
OUTCOME_NON_MERGER = EXPLICIT (§5.2, §8.6)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```
