# CSIA Book 2 — Implementation Evidence — v0.1

Status: READY_FOR_OPERATOR_REVIEW
Branch: `agent/crypto-systems-intelligence-atlas-book2-build`
Planning anchor: `637e0908376004895476e65592d5f9cda0d3e85d`
Book 1 base: `7c2419f00b9f5f5f105708b067848909fa4da609`
Operator authorization: deterministic Book 2 epistemics kernel only; no live
collectors, network, persistence, databases, schedulers, production deployment,
Book 3, Sensor mutation, Capital Field mutation, or trading logic.

## 1. Implemented files

### Kernel modules

- `quant-lab/src/crypto_systems_intelligence_atlas/types.py` — 14 source
  classes, 13 authority claim families, authority tiers, and source authority
  seed metadata.
- `sources.py` — immutable source versions, stable source IDs, locator churn,
  health/lifecycle state, evidence-backed updates, and append-only registry.
- `evidence.py` — immutable `RawEvidence`, deterministic `sha256:` hashes,
  capture identity, derived parser lineage, and append-only evidence store.
- `acquisition.py` — all 11 data-only acquisition contract types, request and
  snapshot semantics, retry/rate/auth/cost metadata, schema drift, and
  representable failure observations.
- `claims.py` — proposition/methodology models, immutable claim versions,
  source/evidence validation, claim-family authority gate, and
  `CREATE_INFERRED` I-1..I-10.
- `promotion.py` — ratified legal transition table, evidence-referenced
  transition events, operator metadata, and fail-closed illegal transitions.
- `authority.py` — `SOURCE × CLAIM_FAMILY × VALID_TIME` assignments,
  discrepancy meta-claim history, repeated-evidence downgrades, reversibility,
  and operator review.
- `contradiction.py` — time-split-first, family-authority-second, contested-on-
  tie resolution with preserved evidence and no averaging surface.
- `freshness.py` — versioned policies for SOURCE_STALE, EVIDENCE_STALE,
  CLAIM_STALE, and RELATIONSHIP_STALE, with no universal duration.
- `changes.py` — all 13 ratified change classes as append-only candidates,
  never graph truth.
- `research_interface.py` — API-surface firewall exposing only DISCOVER,
  RETRIEVE, PARSE, PROPOSE, and CORROBORATE. It has no PROMOTE, SET_STATE,
  SET_AUTHORITY, MUTATE_GRAPH, MUTATE_TIME, or BYPASS_PROVENANCE method.
- `__init__.py` — public Book 2 exports; package version `0.4.0`.

### Book 1 contract amendment

The reuse audit found that accepted Book 1 `ClaimBinding.claim_state` rejected
`INFERRED` and the other Book 2 states. Under the operator's selected remedy,
`temporal.RecordLifecycle` now includes the ratified Book 2 states while
retaining all prior Book 1 values. This is the minimum shared-state amendment
needed to prevent an inferred binding from masquerading as observation.

### Tests

- `quant-lab/tests/crypto_systems_intelligence_atlas/test_book2_core.py` —
  19 deterministic core tests.
- `test_book2_stress.py` — all 16 ratified stress scenarios.
- `test_book2_adversarial.py` — 16 explicit fail-closed adversarial paths.
- `test_book2_integration.py` — 3 direct/inferred Book 1 provenance tests.

## 2. Book 1 reuse map

- Pydantic `BaseModel`, `ConfigDict`, `Field`, and validators: reused from the
  existing Book 1 modeling style.
- `normalize_utc`, `Timestamp`, and `UnknownBound`: imported from Book 1
  `temporal.py`; no duplicate timestamp or unknown-bound implementation.
- `ClaimBinding`: reused and extended only through the shared lifecycle enum.
- `RecordStore` semantics: mirrored as small append-only in-memory stores for
  Book 2 records; no persistence or replacement of Book 1 store behavior.
- `ObjectType` and `IdentityRegistry`: reused for source object scope and
  fail-closed object references; Book 2 never auto-mints objects.
- `TypedEdge`, `GraphValidator`, `EdgeType`, and `ClaimBinding`: reused for
  provenance integration tests without changing edge or identity doctrine.
- Existing CSIA test fixtures and UTC timestamp conventions: reused for
  deterministic tests.

## 3. Invariants implemented

- Source identity is mint-once; locator churn appends a source version.
- Verified source/health updates require evidence references.
- Raw evidence is immutable and append-only; changed bytes create a new ID.
- Parser upgrades create derived evidence and never mutate the parent.
- Claims require evidence; source references must derive from evidence.
- Structural claims require a registered family-scoped primary source.
- AGGREGATOR cannot be sole authority for structural claim families.
- INFERRED requires eligible parents, methodology, new ID, explicit temporal
  derivation, and terminating raw evidence; parents remain unchanged.
- INFERRED cannot transition to OBSERVED.
- Legal claim transitions fail closed and preserve transition history.
- Supersession requires explicit replacement lineage.
- Authority is keyed by source, claim family, and valid time; no global trust
  score exists.
- One discrepancy does not downgrade a source; downgrades require repeated
  evidence, versioning, reversibility, and operator review.
- Contradictions preserve both evidence lines and never average.
- Four staleness kinds remain distinct; policy revisions do not rewrite
  historical evaluations.
- Change candidates never equal graph truth.
- Research systems have no promotion or mutation API.
- Unknown Book 1 objects are rejected rather than auto-minted.

## 4. Quality evidence

| Gate | Command | Result |
|---|---|---|
| Book 1 + Book 2 CSIA | `python -m pytest quant-lab/tests/crypto_systems_intelligence_atlas/ -q` | **161 passed** (107 existing + 54 Book 2) |
| Crypto Sensor regression | `python -m pytest quant-lab/tests/crypto_sensor_fabric/ -q` | **2339 passed, 4 skipped** |
| Ruff | `python -m ruff check quant-lab/src/crypto_systems_intelligence_atlas/ quant-lab/tests/crypto_systems_intelligence_atlas/` | **All checks passed** |
| Mypy | `python -m mypy quant-lab/src/crypto_systems_intelligence_atlas/ --ignore-missing-imports` | **Success: no issues found in 16 source files** |

The Book 2 test total is 54: 19 core + 16 stress + 16 adversarial + 3 Book 1
provenance integration tests. The pre-build Book 1 baseline was 107 passed.

## 5. Deferred scope and known limitations

- Stores are deterministic in-memory structures only; no production
  persistence, database, graph database, scheduler, or process lifecycle.
- Acquisition contracts are interfaces/data only; no network, RPC, scraping,
  browser automation, credentials, or live source access.
- Research Mesh, QCAE, and OCE are represented only by the constrained API
  surface; no live integration exists.
- Usage/health thresholds remain intentionally deferred under D2-6.
- Book 3 population, Sensor changes, Capital Field changes, and trading logic
  are absent.
- Authority assignments are explicit policy inputs; production policy
  calibration and empirical threshold research remain future work.
- `RecordLifecycle.VERIFIED` remains as a Book 1 compatibility value; the
  Book 2 transition engine does not create it.

## 6. Operator review disposition

```text
BOOK_2_IMPLEMENTATION = COMPLETE
STATUS                 = READY_FOR_OPERATOR_REVIEW
STRUCTURAL_FAILURE     = 0
BOOK_2_EXIT_GATE       = PROPOSED
BOOK_2_ACCEPTANCE      = NOT SELF-ACCEPTED
```

The proposed exit gate is
`PASS_CSIA_BOOK2_SOURCE_EVIDENCE_ACQUISITION_KERNEL`. Operator acceptance is
required before Book 2 implementation is considered accepted.


## HARDENING R1 ADDENDUM

Book 2 Hardening R1 closed the operator-identified correctness seams without amending
Book 1. The accepted Book 1 temporal kernel and package root remain frozen; Book 2
now uses `Book2ClaimState` with exactly the ratified nine states and projects through
`Book2ClaimBinding` to the Book 1-compatible `ClaimBinding` pointer.

Focused hardening evidence:

- `CHAIN_SPECIFIC` returns `REQUIRES_CHAIN_CONTEXT` and never fabricates seconds;
  matching deterministic chain context resolves freshness.
- `VERIFIED` is unavailable to Book 2 claims.
- raw claim insertion is closed; declared/observed entry paths and `CREATE_INFERRED`
  are explicit; promoted states require transition machinery.
- P-4 corroboration requires distinct source, owner, and mechanism/provider, and
  rejects same-source evidence and narrative copies.
- authority selection uses numeric `vN` chronology and rejects explicit overlapping
  assignments as ambiguous.
- `SourceEvidenceCoordinator` validates evidence IDs before source locator/health
  versions; the constrained research interface routes source updates through it.

Quality evidence after hardening:

- CSIA: **176 passed** (107 Book 1 + 69 Book 2/hardening/integration)
- Crypto Sensor regression: **2339 passed, 4 skipped**
- Ruff: **PASS**
- Mypy: **PASS**, 16 source files

The proposed exit gate remains
`PASS_CSIA_BOOK2_SOURCE_EVIDENCE_ACQUISITION_KERNEL`; it is not self-accepted.
Book 3 and all live/infrastructure scope remain deferred.
