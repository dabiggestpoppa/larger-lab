# CSIA — BOOK 7 EVENT GRAMMAR v0.1

> **Status:** PLANNING DOCUMENT — DRAFT. Not ratified. No implementation.
> **Authorization:** operator-authorized BOOK 7 PLANNING + GOVERNANCE REVIEW ONLY.
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`, `LIVE_ACQUISITION_AUTHORITY = FALSE`.
> **Date:** 2026-10-01
> **Binding predecessor:** `CSIA_BOOK_7_BOUNDARY_REVIEW_v0.1.md` (AB-1..AB-3).
> **Scope:** Bloc 7A planning concepts — event separations, identity, taxonomy,
> lifecycle, temporality, structural seam, family stress notes. Contracts are
> named, not built.

---

## 1. The six-way separation (before any categories)

```text
EVENT      something happened in the world (or is claimed to), anchored in time
CLAIM      an assertion that may be true or false — Book 2's object
NARRATIVE  a circulating story connecting claims, events and objects — Bloc 7B
ACTION     a deliberate act by an actor (declare, deploy, execute)
STATE CHANGE  a difference between two accepted canonical states — Books 1-5 own it
EVIDENCE   the grounding that lets any of the above be believed — Book 2 owns it
```

No two collapse. An event *may have* claims about it, *may belong to* a
narrative, *may be* an action, *may produce* a state change, and *requires*
evidence to be confirmed — but is none of them. A press release is a
source utterance containing claims; it is not an event. An event without
evidence may exist as a REPORTED occurrence, never as a CONFIRMED one.

## 2. Canonical event concepts (planning contracts — NOT implemented)

```text
EventIdentity         the stable identity of one real-world occurrence
EventOccurrence       the happening itself: family, actors, objects, outcome,
                      evidence gates passed, lifecycle state
EventClaimLink        links an EventOccurrence to Book 2 claims that assert or
                      describe it (with the claims' own evidence classes)
EventObjectImpact     which Book 1-5 canonical objects the occurrence bears on,
                      and through which structural records (reference-only)
EventStatus           lifecycle state (§5) — occurrence history, NOT Book 2
                      claim state
EventTemporalWindow   the family-applicable subset of the ten temporal fields (§6)
EventEvidenceBinding  the Book 2 evidence refs that justify the current
                      lifecycle state; no promotion without them
```

Derived (never independent): an event's *report set* is the collection of
source utterances/claims that describe it — it is evidence, not identity.

## 3. Event identity doctrine (Phase 4 stress resolved)

**Core law: `REPORT_COUNT != EVENT_COUNT`.** Twenty articles about one upgrade
are one event with twenty reports. Narrative propagation (Bloc 7B) must never
duplicate event identity: a report set N-ary aggregation feeds *propagation*,
never *occurrence counting*.

Identity resolution doctrine (candidate operator decision `D7N-1`):

- **Identity key (planned):** `(subject_scope, event_family, occurrence_signature, temporal_anchor)` — where `occurrence_signature` is family-defined (e.g., contract address + deploy tx for a deployment; proposal id + execution tx for governance; CVE-style identifier or exploit tx for an exploit; regulation id + jurisdiction for regulatory).
- **Same-subject recurrence:** a recurring outage is a *series* — one
  `EventIdentity` per occurrence, linked by a family-scoped series relation
  (planned `EventSeries`), never one merged event, never N unrelated events.
- **Multi-stage programs** (migration with phases, governance
  proposal→vote→execution→activation): one *program* (series) containing
  multiple distinct events; each stage is separately datable and separately
  evidenced. Completion of stage 1 does not confirm stage 2.
- **Proposal + execution:** two events (or two stages of one program). A passed
  vote is not the execution (§33 doctrine, Phase stress below).
- **Announcement followed by deployment:** announcement = a claim/report about
  a *future/intended* occurrence; deployment = the occurrence. The deployment
  event's identity is independent of how many announcements preceded it.
- **One event, many affected entities** (multi-protocol exploit, one
  regulation, many entities): one `EventIdentity` with N `EventObjectImpact`
  rows — N impacts, one event. Per-entity consequences are owned by Books 3-5
  records; Book 7 stores references.
- **Contested identity:** if sources disagree about whether two reports are the
  same occurrence, the identity state is `IDENTITY_CONTESTED` — preserved, not
  resolved by majority of reports (AB-3).

## 4. Family taxonomy (Phase 5 — candidates stressed, not flattened)

| Candidate | Verdict (pre-matrix) | Rationale |
|---|---|---|
| UPGRADE | KEEP as family | architecture change initiated by the system itself |
| INTEGRATION | KEEP as family | Book 4 relationship formation |
| LAUNCH | REVISE → subfamily of LAUNCH/DEPLOYMENT class | overlaps upgrade+integration; distinguish new-object launch from feature launch |
| MIGRATION | KEEP as family | Book 3 continuity-bearing, unique identity semantics |
| EXPLOIT | KEEP as family (security class) | adversarial occurrence; evidence bar is highest |
| OUTAGE | KEEP as family (security/reliability class) | recurring series semantics required |
| GOVERNANCE | KEEP as family | staged program semantics (proposal/vote/execution) |
| REGULATORY_EVENT | KEEP as family | jurisdiction-aware, legally staged |
| INSTITUTIONAL_ADOPTION | REVISE → declared-action + adoption-criteria gate | announcement ≠ adoption (§9.4) |
| TOKENOMICS_CHANGE | KEEP as family | Book 5/6 economic consequences staged |
| BRIDGE_CHANGE | REVISE → attribute/cross-cutting class | a bridge change is usually a migration or dependency event *on bridge objects* — family or attribute resolved in the candidate matrix |
| STABLECOIN_CHANGE | REVISE → subfamily of TOKENOMICS_CHANGE / capital-realization class | realization semantics are Book 5's |

Key doctrine: families are **mechanism classes, not news sections**. Two items
both "in the news" are not the same family; "listing announced" is not
INTEGRATION. Final KEEP/REVISE/DEFER/REJECT per family — with identity
semantics, temporal fields, owning book, required evidence, and status model —
is delivered in `CSIA_BOOK_7_EVENT_CANDIDATE_MATRIX_v0.1.md`.

## 5. Lifecycle states (Phase 6)

Planned occurrence lifecycle (family-applicable subsets only):

```text
REPORTED              at least one source utterance exists; no occurrence evidence
DECLARED              a responsible actor announced/committed (declared action)
CONFIRMED_OCCURRENCE  Book 2 authority (E0-E2 per family evidence bar) establishes
                      the occurrence happened
ONGOING               begun, not completed (outage, migration dual-running)
RESOLVED              completed/ended with evidence
REVERSED              completed then rolled back, with evidence
SUPERSEDED            a later occurrence replaced this one's effect (recorded, not erased)
CONTESTED             credible sources disagree on occurrence/cause/impact
UNKNOWN               lifecycle cannot be established — explicit, preserved
```

**Separation from Book 2 (AB-2):** this lifecycle describes *occurrence
history*, not epistemic status. It does not duplicate, replace, or parallel
Book 2 ClaimState: `CONFIRMED_OCCURRENCE` means "Book 2-backed evidence
establishes the occurrence," never "the narrative is true" or "the claim is
promoted." Event records carry `EventEvidenceBinding` refs; they mint no
claims, hold no claim states, and cannot promote anything (AB-1/AB-2).

## 6. Temporal model (Phase 7)

Planned fields (Book 1 bitemporal doctrine §12.2 inherited; `observed_at`,
`valid_from`, `valid_to`, `source_published_at`, `ingested_at`, `superseded_at`
already owned):

```text
reported_at      when a source first reported the occurrence
announced_at     when a responsible actor declared it
scheduled_for    when it was planned to happen
began_at         when the occurrence started
effective_at     when its effects took hold
completed_at     when it ended
resolved_at      when its outcome was settled (may differ from completed)
```

Invariants:

```text
report time  != event time  != effective time  != observation time
```

- Families use subsets (a regulatory event has `effective_at`; an outage has
  `began_at/completed_at`; a proposal has `scheduled_for` that may never fire).
  Unused fields are ABSENT, not null-filled, not defaulted.
- Unknown valid times carry explicit uncertainty markers per Constitution
  §12.2 — never fabricated exact dates.
- Late-discovered occurrences enter with `observed_at ≈ now`, valid time in the
  past; history is never rewritten to make later evidence look contemporaneous
  (§31 bitemporality, honored Bloc-wide).

## 7. Event → structural change seam (Phase 8)

**Law: `EVENT SAYS CHANGE OCCURRED != BOOK 7 WRITES THE STRUCTURAL FACT`.**
An event points to canonical changes owned by Books 3-6 via
`EventObjectImpact` rows holding `structural_record_ref` + `impact_relation`
+ `change_status`:

```text
CHANGED         the referenced structural record exists and carries the change
CHANGE_CLAIMED  sources/actors assert the change; no owning-book record yet
NO_CHANGE_FOUND the owning book's current record contradicts the claimed change
NOT_APPLICABLE  family carries no structural-change semantics
```

Examples (all reference-only):

| Event | Points to | Owner |
|---|---|---|
| upgrade event | Book 3 architecture-change record (dossier version bump) | Book 3 |
| integration event | Book 4 DependencyRecord (new/changed edge) | Book 4 |
| migration event | Book 3 `MIGRATED_FROM`/`MIGRATED_TO` lineage + affected Book 4 relations | Book 3 (+4) |
| tokenomics event | Book 5 economic-parameter records + Book 6 measured consequences | Book 5/6 |
| stablecoin event | Book 5 realization/capital-topology records | Book 5 |

Book 7 may observe that the owning book *lacks* a record the event claims —
that observation is a contradiction row (Bloc 7B.5), never a license to mint
the record (AB-1).

## 8. Family stress notes (Phases 32-36 doctrine, per family)

### 8.1 Security events (exploits / outages)

```text
REPORT != SUSPECTED INCIDENT != CONFIRMED INCIDENT != IMPACT ESTIMATE
       != LOSS CLAIM != RECOVERY != POSTMORTEM
```

- Media reporting alone establishes at most REPORT/SUSPECTED. Confirmation of
  occurrence, cause, and amount requires Book 2 authority (E0 on-chain
  evidence where available; E1/E2 for attribution) — a journalist's loss
  figure is a LOSS CLAIM row, never a confirmed impact.
- Loss estimates are preserved with source, class, and revision history;
  conflicting estimates coexist, un-averaged.
- Exploit attribution beyond what evidence supports stays UNKNOWN; narratives
  attributing blame are recorded as narratives, not facts.

### 8.2 Governance events

```text
proposal != vote != approval != execution != activation != rollback
```

A passed vote is not an executed change; an executed change is not a used
feature (D2-6 separation runs the full length). Each stage is a distinct
lifecycle transition with its own evidence binding (proposal id, vote tally
record, execution tx, activation height). Rejected/failed proposals are
first-class occurrences (RESOLVED/REVERSED semantics), not non-events.

### 8.3 Regulatory events

Jurisdiction is a required identity component (same rule text, two
jurisdictions = two events). Stages distinguished:

```text
proposal != guidance != rule != law != court decision != enforcement action
```

plus `effective_at` (which may lag passage by years). No universal-effect
inference: one jurisdiction's ruling does not describe another's. Legal
status is preserved as staged state, never collapsed to "regulatory news."

### 8.4 Institutional adoption

```text
announcement != pilot != integration != custody support != asset issuance
             != production usage != capital allocation
```

`PARTNERSHIP ANNOUNCEMENT != INSTITUTIONAL ADOPTION` without explicit,
recorded adoption criteria (candidate operator decision in the candidate
matrix). Adoption claims route through declared-action (Bloc 7C) and, where
measurable, through Book 6 usage/capital measurements — not through report
volume.

### 8.5 Tokenomics events

```text
proposal != scheduled change != executed parameter change
issuance change != burn != staking parameter change != unlock != treasury action
```

Book 7 records the event and its stage; every economic *consequence* is a
reference to Book 5 economic records and Book 6 measurements. No duplicate
economics authority; "supply will drop 40%" (proposal) never becomes "supply
dropped" (executed) without the executed-stage evidence binding.

## 9. Verdict

```text
EVENT_GRAMMAR          = PLANNED (7 concepts, doctrine complete)
IDENTITY_DOCTRINE      = PLANNED (REPORT_COUNT != EVENT_COUNT; D7N-1 open)
TAXONOMY               = STRESSED (12 candidates: 7 KEEP / 4 REVISE / family-vs-attribute resolved in matrix)
LIFECYCLE              = PLANNED (10 states; Book 2 ClaimState separation enforced)
TEMPORAL_MODEL         = PLANNED (7 event fields + inherited bitemporal axes)
STRUCTURAL_SEAM        = PLANNED (reference-only; CHANGED/CHANGE_CLAIMED gate)
FAMILY_STRESS_NOTES    = COMPLETE (security, governance, regulatory, institutional, tokenomics)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
```
