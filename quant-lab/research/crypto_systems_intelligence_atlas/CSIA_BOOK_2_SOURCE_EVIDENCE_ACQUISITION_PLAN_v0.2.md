# CSIA Book 2 — Source & Evidence Acquisition Plan — v0.2

Status: RATIFICATION CANDIDATE — NO IMPLEMENTATION AUTHORITY
Planning branch: `agent/crypto-systems-intelligence-atlas-plan`
Supersedes for Book 2 planning: `CSIA_BOOK_2_SOURCE_EVIDENCE_ACQUISITION_PLAN_v0.1.md`
Preserved unchanged: v0.1
Book 1 anchor: implementation ACCEPTED at build commit
`7c2419f00b9f5f5f105708b067848909fa4da609`

## 0. Edition and precedence contract

This is a controlled reconciliation edition, not a rewrite. The normative
Book 2 plan consists of the complete v0.1 text plus this v0.2 amendment.
Where this document conflicts with v0.1, this v0.2 text replaces only the
named section. Unchanged v0.1 Blocs 2A, 2B, 2C, 2H, and 2I remain in force.
No v0.1 artifact is rewritten or concealed.

The ratified pipeline remains:

```text
SOURCE → RAW EVIDENCE → CLAIM → CLAIM STATE → PROMOTED GRAPH FACT
```

Book 2 remains the epistemics layer. It consumes Book 1 provenance,
identity, supersession, and temporal contracts without modifying Book 1.
Research Mesh, QCAE, and OCE may propose but cannot promote.

## 0.1 Corrected stress-matrix accounting

All 15 row-level classifications in
`CSIA_BOOK_2_EVIDENCE_STRESS_MATRIX_v0.1.md` were recomputed. The exact
counts are:

```text
STRUCTURAL_FAILURE      0   (no rows)
REQUIRED_EXTENSION      10  (rows 1,2,3,5,6,7,10,11,12,13)
DEFERABLE_EXTENSION     1   (row 8)
INFORMATION_GAP         3   (rows 4,9,14)
OPERATOR_DECISION       1   (row 15)
TOTAL                   15
```

The v0.1 summary printed `REQUIRED_EXTENSION = 9` while listing ten
REQUIRED_EXTENSION rows. The row classifications were internally coherent;
only the summary arithmetic was wrong. v0.2 corrects the count to 10 and
retains this correction in its changelog. The v0.2 stress matrix closes row
15 through D2-5 and adds an INFERRED derivation stress case.

## 0.2 Bloc 2D replacement — Claim Object and INFERRED derivation

The v0.1 2D identity fields remain, with these explicit additions:

```text
parent_claim_refs       ordered claim_ids used as inference parents
parent_claim_states    snapshot of each parent's state at derivation
methodology_ref         immutable methodology/rule/calculation identifier
methodology_parameters  explicit bounded parameters; UNKNOWN allowed
lineage_evidence_refs   evidence traversed through parents (transitive view)
valid_time_derivation   explicit derivation from parents or UNKNOWN
```

### Creation doctrine for INFERRED

INFERRED is not a mutation, re-label, or promotion of an OBSERVED or
CORROBORATED claim. It is a **new claim** produced by a creation action:

```text
OBSERVED / CORROBORATED parent claim(s)
        + mandatory methodology and parameters
        + parent and transitive evidence lineage
        v
NEW INFERRED CLAIM (new claim_id)
```

The creation action, not a state transition of the parent, is the mechanical
route into INFERRED:

```text
CREATE_INFERRED(parent_claim_refs, methodology_ref, proposition,
                valid_time_derivation)
    requires I-1..I-10
    -> inserts new INFERRED claim
    -> leaves every parent claim and state unchanged
```

Normative rules:

- **I-1:** at least one parent claim is mandatory.
- **I-2:** every parent must be OBSERVED or CORROBORATED unless a later
  explicit rule names another permitted parent state; no implicit exception.
- **I-3:** methodology is mandatory and must identify how parent claims
  entail the new proposition.
- **I-4:** evidence lineage must be explicit and terminate in immutable raw
  evidence through every parent claim.
- **I-5:** the inferred claim receives its own immutable `claim_id`.
- **I-6:** inference never overwrites, re-labels, or changes the state or
  identity of an observed parent.
- **I-7:** INFERRED cannot silently become OBSERVED; that transition is
  illegal.
- **I-8:** later direct observation creates a separate OBSERVED claim. That
  claim may corroborate, contest, or supersede the inferred claim according to
  proposition identity and valid-time semantics; it does not relabel the
  inferred claim.
- **I-9:** contrary evidence may move INFERRED to CONTESTED or REJECTED with
  evidence-referenced transition lineage.
- **I-10:** `valid_time_hypothesis` is explicitly derived from parent claims;
  it may remain `UNKNOWN(bounded)` when the parents do not determine it.

Additional 2D controls:

- C-6: a non-INFERRED claim does not require `parent_claim_refs`; an
  INFERRED claim cannot be persisted without them.
- C-7: direct evidence about the inferred proposition does not by itself
  convert the claim; I-8 creates a distinct direct-observation claim.
- C-8: every graph effect from an INFERRED claim must bind the inferred
  claim, methodology, parents, and terminating raw evidence lineage.

## 0.3 Bloc 2E replacement — Promotion Matrix

The states remain DECLARED, OBSERVED, INFERRED, CORROBORATED, CONTESTED,
UNRESOLVED, STALE, REJECTED, and SUPERSEDED. The legal transition table is:

```text
DECLARED → OBSERVED | REJECTED | UNRESOLVED
OBSERVED → CORROBORATED | CONTESTED | STALE | SUPERSEDED | REJECTED
INFERRED → CORROBORATED | CONTESTED | REJECTED | SUPERSEDED
CORROBORATED → CONTESTED | STALE | SUPERSEDED | REJECTED
CONTESTED → CORROBORATED | REJECTED | UNRESOLVED | SUPERSEDED
UNRESOLVED → any observation-bearing state permitted after inquiry
STALE → OBSERVED (re-observation) | SUPERSEDED
any → SUPERSEDED (with lineage), never erasing history
```

The additional legal creation action is:

```text
OBSERVED / CORROBORATED parent(s) → CREATE_INFERRED → NEW INFERRED claim
```

Explicitly illegal:

```text
INFERRED → OBSERVED
mutation/re-label of an OBSERVED parent as INFERRED
silent promotion from inference to direct observation
```

P-1, P-2, P-3, P-4, P-5, and P-6 remain normative. I-1..I-10 are
preconditions and integrity constraints for `CREATE_INFERRED`; satisfying
them does not by itself assert that the inferred proposition is true.
Graph use of an INFERRED claim must visibly retain its inference status and
methodology.

### Updated adversarial cases

- ADV-2E-4: two OBSERVED parents plus explicit methodology create a new
  INFERRED claim; both parent records and states remain byte-for-byte
  unchanged and the new lineage reaches raw evidence.
- ADV-2E-5: direct evidence later appears; it creates a separate OBSERVED
  claim and may corroborate, contest, or supersede the INFERRED claim.
- ADV-2E-6: a methodology omits parents or terminates short of raw evidence;
  CREATE_INFERRED fails atomically and no partial claim is persisted.
- ADV-2E-7: contrary evidence moves INFERRED to CONTESTED/REJECTED; no
  INFERRED→OBSERVED shortcut exists.

## 0.4 Bloc 2F replacement — Contradiction and inference

F-1 through F-6 remain normative. D2-3 ratifies F-2 time-split as the
primary contradiction path when both propositions can be true in different
valid-time windows, and ratifies F-5 never-average without exception.

When documentation and deployed state disagree, both evidence lines are
preserved. The immediate factual proposition is resolved by the authority
of the relevant `SOURCE × CLAIM_FAMILY × VALID_TIME` key. A discrepancy
meta-claim records the conflict. One discrepancy never creates a global
source demotion. The complete family-scoped downgrade procedure is in
D2-5 and Source Authority Matrix v0.2.

Inference does not bypass contradiction handling. If an inferred claim and
a directly observed claim address the same proposition and valid time, the
system compares them explicitly: agreement may corroborate; disagreement
enters CONTESTED and later resolution may reject or supersede according to
lineage. The direct claim never mutates the inferred claim.

## 0.5 Bloc 2G replacement — Staleness policy

D2-4 ratifies four distinct concepts:

```text
SOURCE_STALE        source not re-verified within its class policy
EVIDENCE_STALE      capture older than policy allows for feeding claims
CLAIM_STALE         promoted claim outside its claim-family freshness policy
RELATIONSHIP_STALE  promoted edge outside its relationship-family policy
```

The v0.1 policy table is ratified as **default policy**, not immutable global
constants. Defaults are selected by claim family, source class, proposition
type, and empirical implementation-planning evidence. A policy revision is
versioned and cannot rewrite historical evaluation: each promoted graph fact
pins the policy version used at promotion. No universal stale window exists.
Historical genesis/spec evidence uses supersession semantics, not automatic
time decay.

## 0.6 Operator decision closure

The operator's six decisions are incorporated as follows.

### D2-1 — SOURCE CLASSES + AGGREGATOR EXCLUSION: ACCEPT

The 14 source classes in 2A are accepted. S-4 is accepted: AGGREGATOR
sources may corroborate identity or contextual claims but may never be sole
authority for structural graph truth.

### D2-2 — CLAIM PROMOTION DOCTRINE: ACCEPT WITH v0.2 INFERRED REPAIR

P-1 and P-3 are accepted. The transition table is accepted only with I-1
through I-10 and the `CREATE_INFERRED` route above. Inference remains
lineage-explicit and cannot masquerade as observation.

### D2-3 — CONTRADICTION DOCTRINE: ACCEPT

F-2 time-split is primary where two claims can both be true at different
valid times. F-5 never-average is ratified.

### D2-4 — STALENESS DOCTRINE: ACCEPT

SOURCE_STALE, EVIDENCE_STALE, CLAIM_STALE, and RELATIONSHIP_STALE are
ratified. The 2G table is default policy and may be versioned/tuned; it is
not an immutable global constant set and there is no universal stale window.

### D2-5 — DOC-vs-CHAIN TRUST DOWNGRADE: CLAIM-FAMILY-SCOPED PROCEDURE

1. Preserve both documentation and deployed-state evidence lines.
2. Resolve the immediate factual proposition using authority keyed by
   `SOURCE × CLAIM_FAMILY × VALID_TIME`.
3. Create a discrepancy meta-claim with lineage.
4. Track discrepancy history for that source and claim family over time.
5. One discrepancy never globally demotes a source.
6. Repeated, demonstrated family-specific unreliability may lower authority
   for that claim family only.
7. Every downgrade is evidence-backed.
8. Every downgrade is temporally versioned.
9. Every downgrade is reversible by a later evidence-backed decision.
10. A persistent authority-tier change requires operator review.
11. No global opaque source trust score exists.

A source repeatedly wrong about activation timing may lose authority for
DEPLOYMENT / ACTIVATION claims while remaining authoritative for
SPECIFICATION, GOVERNANCE INTENT, or HISTORICAL DOCUMENTATION.

### D2-6 — ANNOUNCED / DEPLOYED / USED: DISTINCT; PARAMETERS DEFERRED

`ANNOUNCED ≠ DEPLOYED ≠ USED` is ratified. Concrete usage and health
thresholds are not frozen. They must be researched empirically during a
later authorized implementation-planning phase. This session does not
authorize that implementation planning or Book 2 implementation.

## 0.7 Bloc status and exit conditions

```text
BLOC_2A = RATIFICATION_CANDIDATE
BLOC_2B = RATIFICATION_CANDIDATE
BLOC_2C = RATIFICATION_CANDIDATE
BLOC_2D = RATIFICATION_CANDIDATE (v0.2 INFERRED fields/rules)
BLOC_2E = RATIFICATION_CANDIDATE (v0.2 transition model)
BLOC_2F = RATIFICATION_CANDIDATE
BLOC_2G = RATIFICATION_CANDIDATE
BLOC_2H = RATIFICATION_CANDIDATE
BLOC_2I = RATIFICATION_CANDIDATE

STRUCTURAL_FAILURE = 0
BLOCKING_OPERATOR_DECISIONS = 0
BOOK_2_IMPLEMENTATION_AUTHORITY = FALSE
```

Ratification is valid only after the companion authority matrix v0.2, stress
matrix v0.2, and pre-ratification review v0.2 pass. A planning exit gate
never grants implementation authority.

## 0.8 v0.1 → v0.2 CHANGELOG

- Reconciled the 15-row stress summary: REQUIRED_EXTENSION corrected from 9
  to 10; exact classification totals are 0/10/1/3/1. The v0.1 error remains
  visible in the preserved artifact and is explicitly disclosed here.
- Added 2D fields and I-1..I-10 for explicit, terminating INFERRED lineage.
- Added the `CREATE_INFERRED` creation action and the prohibition on
  INFERRED→OBSERVED; parents remain unchanged.
- Updated 2F contradiction handling and adversarial review for direct versus
  inferred claims and family-scoped source discrepancies.
- Ratified D2-1 source classes and aggregator exclusion.
- Ratified D2-2 promotion doctrine with the INFERRED reachability repair.
- Ratified D2-3 time-split-first and never-average contradiction doctrine.
- Ratified D2-4 four-kind staleness with versioned default policies and no
  universal stale window.
- Ratified D2-5 claim-family/time-scoped authority and reversible,
  evidence-backed, versioned discrepancy downgrades; prohibited global trust
  scores and single-discrepancy global demotion.
- Confirmed D2-6 announced/deployed/used distinction while deferring usage
  and health parameters to a later authorized empirical planning phase.
- Preserved v0.1 and all Book 1 artifacts unchanged.
