# CSIA Book 2 — Pre-Ratification Review — v0.2

Status: PASS — READY FOR RATIFICATION RECORD
Review date: 2026-09-24
Inputs:

- `CSIA_BOOK_2_SOURCE_EVIDENCE_ACQUISITION_PLAN_v0.2.md` (`40d39144`)
- `CSIA_OPERATOR_DECISION_LOG.md` D2-1..D2-6 (`8429730b`)
- `CSIA_BOOK_2_SOURCE_AUTHORITY_MATRIX_v0.2.md` (`a0a9c5c5`)
- `CSIA_BOOK_2_EVIDENCE_STRESS_MATRIX_v0.2.md` (`343c24e8`)
- preserved v0.1 plan, authority matrix, stress matrix, and review
- ratified Constitution v0.2 and accepted Book 1 build `7c2419f0`

## 1. Exit-gate verdict

```text
STRUCTURAL_FAILURE                = 0
BLOCKING_OPERATOR_DECISIONS       = 0
STRESS_COUNTS_INTERNAL            = PASS
ALL_SIX_OPERATOR_DECISIONS_CLOSED  = TRUE
INFERRED_MECHANICALLY_REACHABLE    = TRUE
INFERRED_LINEAGE_EXPLICIT         = TRUE
NARRATIVE_TO_STRUCTURAL_SHORTCUT  = FALSE
GLOBAL_TRUST_SCORE                = FALSE
UNIVERSAL_STALE_WINDOW            = FALSE
BOOK_1_CHANGED                    = FALSE
RESEARCH_SYSTEM_DIRECT_PROMOTION  = FALSE
EVERY_GRAPH_FACT_TRACEABLE        = TRUE

BOOK_2_PRE_RATIFICATION_REVIEW    = PASS
BOOK_2_READY_FOR_RATIFICATION     = TRUE
BOOK_2_IMPLEMENTATION_AUTHORITY   = FALSE
```

The zero-structural-failure result applies to planning doctrine. It is not an
implementation test result and does not authorize implementation.

## 2. Stress-count reconciliation

### Original fifteen v0.1 rows

The row-by-row recount is:

```text
STRUCTURAL_FAILURE      0
REQUIRED_EXTENSION      10  (1,2,3,5,6,7,10,11,12,13)
DEFERABLE_EXTENSION     1   (8)
INFORMATION_GAP         3   (4,9,14)
OPERATOR_DECISION       1   (15)
TOTAL                   15
CHECKSUM                0+10+1+3+1 = 15
```

The v0.1 summary's `REQUIRED_EXTENSION = 9` was wrong because it listed ten
such rows. The v0.1 file remains preserved; plan v0.2 and stress matrix v0.2
both disclose and correct the error.

### Expanded v0.2 matrix

D2-5 closes original row 15 and makes its required authority-history
mechanism a REQUIRED_EXTENSION. New row 16 exercises the required INFERRED
creation mechanism. The expanded classification is:

```text
STRUCTURAL_FAILURE      0
REQUIRED_EXTENSION      12  (1,2,3,5,6,7,10,11,12,13,15,16)
DEFERABLE_EXTENSION     1   (8)
INFORMATION_GAP         3   (4,9,14)
OPERATOR_DECISION       0
TOTAL                   16
CHECKSUM                0+12+1+3+0 = 16
```

Both count frames are correct for their stated row set. The historical
15-row correction and the post-decision 16-row disposition are not conflated.

## 3. Operator decision closure

| Decision | Selection | Closure evidence | Blocking issues |
|---|---|---|---:|
| D2-1 | ACCEPT | 14 classes and S-4 aggregator exclusion in plan v0.2; A-2 in matrix v0.2 | 0 |
| D2-2 | ACCEPT_WITH_INFERRED_REPAIR | I-1..I-10, CREATE_INFERRED, own claim ID, and permanent INFERRED→OBSERVED prohibition | 0 |
| D2-3 | ACCEPT | F-2 time-split primary; F-5 never-average | 0 |
| D2-4 | ACCEPT | Four staleness kinds; versioned default policies; no universal window | 0 |
| D2-5 | CLAIM_FAMILY_SCOPED_TRUST_DOWNGRADE | Family/time authority key, discrepancy meta-claim/history, reversible versioned downgrade, operator review | 0 |
| D2-6 | DEFER_USAGE_HEALTH_PARAMETERS | ANNOUNCED/DEPLOYED/USED distinction ratified; thresholds deferred to later authorized empirical planning | 0 |

The decision log binds all six to the exact v0.2 plan commit, records affected
blocs/invariants, rationale, consequence, reversibility, timestamp, and SHA.

## 4. Adversarial review — fourteen explicit answers

### Q1. Can a press release prove deployment?

NO. It proves a narrative/announcement exists. A structural deployment claim
starts DECLARED and requires deployed-state evidence at the authority tier for
DEPLOYMENT / ACTIVATION or INTEGRATION. This remains P-1/P-3/A-3.

### Q2. Can deployed state override stale documentation?

YES for the immediate factual proposition “what IS,” but not by erasure.
Documentation and deployed-state lines are both preserved, valid time is
resolved, and the losing proposition is corrected or superseded with lineage.
Documentation remains primary for “what is SPECIFIED.”

### Q3. Can two official sources remain contested?

YES. If valid-time splitting does not apply and authority tiers tie, both
lines remain and the claim pair is CONTESTED or UNRESOLVED. Source count,
recency, and seniority are not resolution rules.

### Q4. Can a claim downgrade after new evidence?

YES. CORROBORATED and INFERRED claims have evidence-referenced downgrade
paths to CONTESTED, REJECTED, or SUPERSEDED where applicable. Graph history
is corrected by lineage, never deleted.

### Q5. Can old evidence remain historically correct?

YES. Raw evidence is immutable; STALE is distinct from REJECTED; valid-time
history remains queryable. A source correction or world-state change creates
successor history rather than rewriting the old claim.

### Q6. Can parser upgrades preserve extraction lineage?

YES. Re-parsing creates new derived evidence under a versioned parser and
transformation lineage pointing to the raw capture. The original extraction
is preserved.

### Q7. Can a source disappear without losing evidence?

YES. Surviving snapshot references and content hashes preserve raw evidence.
The source may become UNREACHABLE or SOURCE_STALE and dependent claims may be
queued for re-verification; historical evidence is not erased.

### Q8. Can stale graph relationships remain historically queryable?

YES. Staleness is a queryable policy state, not deletion. Relationship
closure uses Book 1 valid-time closure and preserves the historical edge.

### Q9. Can Research Mesh, QCAE, or OCE promote facts directly?

NO. Their allowed outputs enter as registered sources, immutable evidence,
DECLARED claims, or corroborating material. They have no promotion,
state-editing, authority-tier, temporal-rule, or provenance authority.

### Q10. Can aggregator mistakes remain quarantined?

YES. A-2/P-2 prevent aggregators from being sole structural authority.
Identity/contextual corroboration is allowed; conflation and structural
promotion are rejected or quarantined with lineage.

### Q11. Can every graph fact trace to exact raw evidence?

YES. A direct claim traces claim → evidence refs → content hash → raw
snapshot. An inferred graph effect additionally traces
`inferred claim → methodology + parent claims → evidence refs → content hash
→ raw snapshot`. Missing or non-terminating lineage blocks persistence or
promotion.

### Q12. Can CSIA distinguish announced, deployed, and used?

YES, at separate claim seams. ANNOUNCED is narrative existence; DEPLOYED is
deployed-state structure; USED requires usage evidence. Concrete usage/health
thresholds are explicitly deferred to later authorized empirical planning
and are not fabricated here.

### Q13. Can an inferred claim be created?

YES. `CREATE_INFERRED` requires at least one OBSERVED or CORROBORATED parent,
mandatory methodology, its own claim ID, explicit valid-time derivation, and
transitive evidence lineage terminating in raw evidence. It creates a new
INFERRED claim and leaves parent records and states unchanged.

### Q14. Can an inferred claim be challenged, corroborated, superseded, and traced without becoming observed?

YES. Contrary evidence may move it to CONTESTED or REJECTED. Independent
support may corroborate it. A successor claim may supersede it. Direct
observation creates a separate OBSERVED claim that may corroborate, contest,
or supersede according to proposition and valid time. There is no legal
INFERRED→OBSERVED transition and no parent mutation.

**Required direct answer: YES.** An inferred claim can be created, challenged,
corroborated, and traced back to raw evidence without masquerading as direct
observation.

## 5. INFERRED mechanical reachability proof

The repaired route is:

```text
validated OBSERVED / CORROBORATED parent claim(s)
  + methodology_ref and parameters
  + explicit valid_time_derivation
  + recursively validated evidence lineage to raw captures
  v
CREATE_INFERRED
  v
new immutable claim_id in INFERRED state
```

Reachability checks:

- I-1 requires a parent: PASS.
- I-2 constrains parent states: PASS.
- I-3 requires methodology: PASS.
- I-4 requires terminating raw lineage: PASS.
- I-5 allocates a distinct claim ID: PASS.
- I-6 preserves parent state and identity: PASS.
- I-7 and transition table prohibit INFERRED→OBSERVED: PASS.
- I-8 defines a separate direct-observation claim: PASS.
- I-9 defines contrary-evidence paths: PASS.
- I-10 makes valid-time derivation explicit and permits UNKNOWN: PASS.

The v0.1 defect—defining INFERRED while providing no clear legal route into
it—is closed. The route is a creation action because inference is not a
mutation of a parent claim.

## 6. Authority, contradiction, and staleness firewall

- Authority is resolved only at `SOURCE × CLAIM_FAMILY × VALID_TIME`.
- There is no global opaque source trust score.
- A single documentation/deployed-state discrepancy never globally demotes
  a source.
- Downgrades require repeated family-specific evidence, are versioned by time,
  are reversible, and require operator review when persistent.
- F-2 time-split is primary when propositions can both be true in different
  valid-time windows.
- F-5 prohibits midpoint averaging of block numbers, times, balances, or
  other disagreeing propositions.
- SOURCE_STALE, EVIDENCE_STALE, CLAIM_STALE, and RELATIONSHIP_STALE remain
  separate. Defaults are versioned policy, not immutable constants.
- No universal stale window is introduced.

## 7. Narrative and research-system firewalls

A narrative can support “an announcement exists” but cannot directly create a
structural graph fact. Deployment evidence cannot directly imply usage.
Aggregator identity/context support cannot bypass structural authority.
Research Mesh, QCAE, and OCE can DISCOVER, RETRIEVE, PARSE, PROPOSE, or
CORROBORATE only through the registered pipeline; none can PROMOTE.

There is no route:

```text
NEWS/SOCIAL/AGGREGATOR/research proposal → direct structural graph fact
```

without the appropriate claim, authority, state transition, and provenance
checks.

## 8. Scope and dependency audit

The reconciliation diff from starting planning HEAD `feeba764` contains only:

- Book 2 plan v0.2
- Book 2 source authority matrix v0.2
- Book 2 evidence stress matrix v0.2
- Book 2 entries in the canonical operator decision log

It contains no Book 1 planning or implementation artifact; no collector,
adapter, database, graph database, network code, source access, sensor or
capital-field mutation, Book 3 work, or Book 2 implementation. The build
branch remains at accepted commit `7c2419f0`.

Book 1 dependencies remain consume-only: ClaimBinding, RecordStore
supersession, holds_at/UnknownBound, valid/transaction time, and closure
doctrine. No Book 1 kernel mutation is requested.

## 9. Readiness verdict

```text
BOOK_2_PLAN_VERSION             = v0.2
BOOK_2_SOURCE_AUTHORITY_MATRIX  = v0.2
BOOK_2_EVIDENCE_STRESS_MATRIX   = v0.2
BOOK_2_PLANNING                 = COMPLETE
BOOK_2_OPERATOR_DECISIONS       = CLOSED (6/6)
STRUCTURAL_FAILURE              = 0
BLOCKING_OPERATOR_DECISIONS     = 0
PRE_RATIFICATION_REVIEW         = PASS
BOOK_2_READY_FOR_RATIFICATION   = TRUE
BOOK_2_IMPLEMENTATION_AUTHORITY = FALSE
```

A separate Book 2 ratification record may now seal the planning artifacts.
That record must continue to state that implementation authority is false.
