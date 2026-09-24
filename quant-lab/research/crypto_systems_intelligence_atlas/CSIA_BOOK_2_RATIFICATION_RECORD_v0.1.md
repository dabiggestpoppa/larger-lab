# CSIA Book 2 — Ratification Record — v0.1

Ratification date: 2026-09-24
Planning branch: `agent/crypto-systems-intelligence-atlas-plan`
Book 1 dependency: plan RATIFIED; implementation ACCEPTED at build commit
`7c2419f00b9f5f5f105708b067848909fa4da609`

## Ratification decision

```text
BOOK                            = 2
STATUS                          = RATIFIED
PLAN                            = v0.2

BLOC_2A                         = RATIFIED
BLOC_2B                         = RATIFIED
BLOC_2C                         = RATIFIED
BLOC_2D                         = RATIFIED
BLOC_2E                         = RATIFIED
BLOC_2F                         = RATIFIED
BLOC_2G                         = RATIFIED
BLOC_2H                         = RATIFIED
BLOC_2I                         = RATIFIED

SOURCE_AUTHORITY_MATRIX         = v0.2 RATIFIED
EVIDENCE_STRESS_MATRIX          = v0.2 ACCEPTED
PRE_RATIFICATION_REVIEW         = v0.2 PASS

STRUCTURAL_FAILURE              = 0
BLOCKING_OPERATOR_DECISIONS     = 0
BOOK_2_EXIT_GATE               = PASS

BOOK_2_IMPLEMENTATION_AUTHORITY = FALSE
```

Ratification seals planning doctrine only. It does not authorize code,
collectors, source access, persistence, database or graph-database work,
deployment, Sensor/Capital Field mutation, or any other implementation scope.

## Ratified planning artifacts

- `CSIA_BOOK_2_SOURCE_EVIDENCE_ACQUISITION_PLAN_v0.2.md` — commit
  `40d391446088280ca5e6bf49dcdbe36428499c98`
- `CSIA_OPERATOR_DECISION_LOG.md`, D2-1..D2-6 — commit
  `8429730b`
- `CSIA_BOOK_2_SOURCE_AUTHORITY_MATRIX_v0.2.md` — commit
  `a0a9c5c5`
- `CSIA_BOOK_2_EVIDENCE_STRESS_MATRIX_v0.2.md` — commit
  `343c24e8`
- `CSIA_BOOK_2_PRE_RATIFICATION_REVIEW_v0.2.md` — commit
  `1be04cf6`

The v0.1 artifacts remain preserved as historical planning evidence.

## Decision closure

```text
D2-1 = ACCEPT
D2-2 = ACCEPT_WITH_INFERRED_REPAIR
D2-3 = ACCEPT
D2-4 = ACCEPT
D2-5 = CLAIM_FAMILY_SCOPED_TRUST_DOWNGRADE
D2-6 = DEFER_USAGE_HEALTH_PARAMETERS
```

All six decisions are closed in the canonical operator decision log. D2-6's
usage/health parameters remain deferred; their deferral is non-blocking for
planning ratification and does not authorize later empirical implementation
planning.

## Reconciliation findings accepted

### Stress counts

The original fifteen v0.1 rows reconcile to:

```text
STRUCTURAL_FAILURE=0, REQUIRED_EXTENSION=10,
DEFERABLE_EXTENSION=1, INFORMATION_GAP=3, OPERATOR_DECISION=1
```

The v0.1 summary incorrectly printed REQUIRED_EXTENSION=9 while listing ten
such rows. The historical error remains visible in v0.1 and is explicitly
corrected in v0.2.

After D2-5 closes row 15 and row 16 adds the INFERRED stress case, the v0.2
matrix reconciles to sixteen scenarios:

```text
STRUCTURAL_FAILURE=0, REQUIRED_EXTENSION=12,
DEFERABLE_EXTENSION=1, INFORMATION_GAP=3, OPERATOR_DECISION=0
```

### INFERRED reachability

INFERRED is mechanically reachable only through `CREATE_INFERRED`, which
requires one or more eligible parent claims, mandatory methodology, explicit
valid-time derivation, a new claim ID, and evidence lineage terminating in
raw evidence. Parent claims are not mutated. INFERRED cannot silently become
OBSERVED. Later direct evidence creates a separate OBSERVED claim that may
corroborate, contest, or supersede the inferred claim under normal temporal
and proposition semantics.

**Review question — Can an inferred claim be created, challenged,
corroborated, and traced back to raw evidence? YES.**

## Invariants sealed by ratification

- Fourteen source classes and the AGGREGATOR structural exclusion are in
  force.
- Narrative cannot directly promote structural graph truth.
- Authority is keyed by SOURCE × CLAIM_FAMILY × VALID_TIME; no global opaque
  source trust score exists.
- A single discrepancy cannot globally demote a source. Downgrades are
  family-scoped, evidence-backed, temporally versioned, reversible, and
  operator-reviewed when persistent.
- F-2 time-split is primary when valid-time separation applies; F-5 never-
  average is absolute.
- SOURCE_STALE, EVIDENCE_STALE, CLAIM_STALE, and RELATIONSHIP_STALE remain
  separate, with versioned default policies and no universal stale window.
- ANNOUNCED, DEPLOYED, and USED remain distinct propositions.
- Research Mesh, QCAE, and OCE cannot promote directly.
- Every graph fact remains evidence-traceable; inferred facts include method
  and parent lineage in addition to terminating raw evidence.
- Book 1 remains unchanged.

## Exit and next authority

```text
BOOK_2_EXIT_GATE               = PASS
BOOK_2_IMPLEMENTATION_AUTHORITY = FALSE
NEXT                           = BOOK 2 IMPLEMENTATION AUTHORIZATION + BUILD PLAN
```

The next action requires a separate explicit operator authorization. This
record grants no such authority.
