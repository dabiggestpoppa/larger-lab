# CSIA Book 2 Implementation Acceptance Record

**BOOK = 2**

**PLAN = v0.2 RATIFIED**

**IMPLEMENTATION_STATUS = ACCEPTED**

**EXIT_GATE = PASS_CSIA_BOOK2_SOURCE_EVIDENCE_ACQUISITION_KERNEL**

**HARDENING_R1 = PASS**  
**HARDENING_R2 = PASS**  
**HARDENING_R3 = PASS**  
**HARDENING_R4 = PASS**

**FINAL_VERIFIED_BUILD_HEAD = `a3457488b2ea5d91447ae2af1e4407a0554c7a69`**

## Quality evidence

```text
CSIA_TESTS = 215 PASS
BOOK_1_TESTS = 107 PASS
BOOK_2_TESTS = 108 PASS
SENSOR_REGRESSION = 2339 PASS / 4 SKIPPED
RUFF_CSIA = PASS
MYPY = PASS
FULL_REPOSITORY_RUFF = PRE_EXISTING_OUTSIDE_CSIA_SCOPE
BLOCKING_CORRECTNESS_ISSUES = 0
BOOK_1_ACCEPTED_CONTRACT_MUTATIONS = 0
```

## Accepted scope

This acceptance covers the deterministic/offline Book 2 epistemics kernel only:

- Source Registry
- Raw Evidence
- Acquisition contracts
- Claim model
- `CREATE_INFERRED`
- `Book2ClaimState`
- ClaimStore canonical authority
- Claim-state transition engine
- promotion rules
- exact proposition corroboration
- P-4 independence
- contradiction engine
- source authority policy
- freshness/staleness policy
- change candidates
- constrained research interface
- source/evidence coordination
- Book 2 → Book 1 graph provenance adapter
- `GraphFactPromoter`
- deterministic offline tests

## Accepted Book 2 invariants

- **B2-I1:** Raw evidence is immutable.
- **B2-I2:** Source count is not truth.
- **B2-I3:** Narrative cannot directly establish structural truth.
- **B2-I4:** An aggregator cannot be sole authority for structural truth.
- **B2-I5:** Authority is `SOURCE × CLAIM_FAMILY × VALID_TIME`.
- **B2-I6:** There is no global trust score.
- **B2-I7:** There is no universal stale window.
- **B2-I8:** Inference creates a new claim and never rewrites observation.
- **B2-I9:** Graph promotion trusts canonical current `ClaimStore` state only.
- **B2-I10:** Detached, historical, or forged claims cannot become current graph truth.
- **B2-I11:** `CORROBORATED` requires agreement plus independence.
- **B2-I12:** Corroboration requires the same proposition, same claim family, temporally compatible assertion, canonical `OBSERVED`/`CORROBORATED` corroborator, corroborating evidence binding, independent source/owner/mechanism, and legal transition provenance.
- **B2-I13:** Missing or unknown temporal certainty fails closed.
- **B2-I14:** Research systems may propose or corroborate but cannot bypass promotion.
- **B2-I15:** Book 1 remains frozen.

## Accepted conservative limitation

Book 2 current corroboration valid-time semantics operate on point hypotheses /
`UnknownBound` rather than a full claim interval model. Therefore:

- exact known point equality is required for automatic corroboration;
- `UnknownBound` fails closed;
- no fabricated overlap is allowed.

This is accepted as a conservative current limitation, not interpreted as an interval
model.

## Deferred and not accepted

Live collectors, network acquisition, RPC execution, scraping, databases, graph
databases, persistence engines, schedulers, production deployment, credentials, live
Research Mesh/QCAE/OCE integration, Book 3 implementation, Sensor mutation, Capital
Field mutation, and trading/execution authority remain deferred.

This record is an operator acceptance record. It does not authorize further generic
Book 2 hardening, Book 3 implementation, or any deferred live or production scope.
