# CSIA Book 4 Offline Implementation Evidence v0.1

- **Date:** 2026-09-25
- **Status:** READY_FOR_OPERATOR_REVIEW
- **Scope:** deterministic offline protocol / infrastructure / dependency kernel
- **Live acquisition:** false
- **Book 5:** NOT_STARTED

## Governance anchors

- Ratified Book 4 planning + errata anchor: `04820379bd0f63a605d83b1c710a246b103a5ef1`
- Book 4 D4 binding commit: `8b6106055686721b1b490adc792b0d6c03696e15`
- Accepted Book 3 base: `d33afd5ec87208d96d256ec919fbf55956bf2791`
- Build branch: `agent/crypto-systems-intelligence-atlas-book4-build`

## Implemented kernel

The implementation adds a local Book 4 typed layer and does not modify the
accepted Books 1–3 kernel modules.

- `Book4Provenance` resolves canonical current Book 2 claims and attached evidence.
  It reuses `ClaimStore`, `EvidenceStore`, and `can_promote_to_graph`; it does not
  define a second epistemic state machine.
- `DependencyRecord` stores direct dependencies only and carries explicit Book 2
  claim and source-snapshot references.
- `DependencyStrengthDescriptor` separates REQUIRED, PRIMARY, FALLBACK,
  OPTIONAL, LEGACY, DEPRECATED, and UNKNOWN from runtime scope.
- `HardRuntimeGate` implements the D4-6 eight-part contract and fails closed for
  missing evidence, unknown fallback, unknown valid time, or absent provenance.
- `DependencyPath` preserves ordered nodes and relations. Its transitive output is
  explicitly derived and non-authoritative.
- `FailureDomain`, `RedundancyAssessment`, and `SubstitutabilityAssessment`
  preserve mechanism evidence, positive independence evidence, and directionality.
- `RoleAssignment` implements all 48 ratified role-family names with the Book 4
  domain-only role state CURRENT / HISTORICAL / DECLARED_ONLY / UNKNOWN.
- Relationship projection reuses Book 1 `EdgeType`, Book 3
  `ArchitectureRelationType`, and Book 1 `Hyperedge`. The six prohibited relation
  additions fail closed.
- Eighteen deterministic pilot fixtures are explicitly fixture-only and make no
  live-current factual claim.

## Verification

```text
BOOK_1_TESTS = 107 PASS
BOOK_2_TESTS = 108 PASS
BOOK_3_TESTS = 83 PASS
BOOK_4_TESTS = 101 PASS
TOTAL_CSIA = 399 PASS
BOOK_4_ADVERSARIAL_CASES = 17
HARD_RUNTIME_CASES = 10
FAILURE_DOMAIN_SCENARIOS = 16
SUBSTITUTABILITY_DIRECTIONAL_CASES = 11
OFFLINE_PILOT_FIXTURES = 18
CSIA_RUFF = PASS
CSIA_MYPY = PASS
BOOK_1_ACCEPTED_CONTRACT_MUTATIONS = 0
BOOK_2_ACCEPTED_CONTRACT_MUTATIONS = 0
BOOK_3_ACCEPTED_CONTRACT_MUTATIONS = 0
```

The final Crypto Sensor run produced `2325 passed, 14 failed, 4 skipped` in
161.00 seconds. The 14 failures are the previously identified committed-evidence
CRLF/LF byte comparisons. The baseline run before implementation produced
`2324 passed, 15 failed, 4 skipped`; its additional Windows atomic/concurrency
failure did not reproduce in the final run. The operator authorized a scoped
deviation for these pre-existing Crypto Sensor failures only. No Crypto Sensor
artifact or source was changed.

## Exit state

```text
BOOK_4_IMPLEMENTATION = COMPLETE
PROPOSED_EXIT_GATE = PASS_CSIA_BOOK4_PROTOCOL_INFRASTRUCTURE_DEPENDENCY_KERNEL
STATUS = READY_FOR_OPERATOR_REVIEW
BOOK_4_ACCEPTANCE = NOT_SELF_ACCEPTED
BOOK_5 = NOT_STARTED
LIVE_ACQUISITION_AUTHORITY = FALSE
```

The exact next operator action is to review this matrix and evidence, then
explicitly accept or reject the proposed Book 4 exit gate. No Book 5 or live
acquisition work is authorized.

---

# HARDENING R1 — FACT-SPECIFIC PROVENANCE + CROSS-RECORD INTEGRITY + BOOK 5 BOUNDARY SEAL

- **Date:** 2026-09-25
- **Start HEAD:** `655bd0cecfe63ea3192408b7ec4c54f027038933`
- **Status:** PASS
- **Scope:** Book 4 modules and tests only; no accepted Book 1–3 or Sensor mutation

## Finding A — HARD_RUNTIME fact binding (SEALED)

`HardRuntimeFactBinding` binds each decision-driving D4-6 fact to canonical
Book 2 claims whose proposition qualifier equals the fact class. The gate
requires IDENTITY, DEPLOYED_CONFIGURATION, RUNTIME_NECESSITY,
FAILURE_CONSEQUENCE, NO_ACTIVE_EQUIVALENT_FALLBACK, and VALID_TIME support. A
generic canonical claim can no longer accompany `HARD_RUNTIME`, a fallback
proof claim cannot double as proof of no active fallback, and non-promotable
(contested, unresolved, stale, rejected, superseded) fact claims never satisfy
current truth.

## Finding B — failure-domain provenance (SEALED)

`mechanism_claim_refs` must resolve as canonical `FAILURE_MECHANISM` claims.
Raw `mechanism_evidence_refs` remain lineage only and can no longer establish
`SHARED_FAILURE_DOMAIN`. `INDEPENDENT` requires canonical
`POSITIVE_INDEPENDENCE` support; absence of shared evidence still never proves
independence.

## Finding C — redundancy referential integrity (SEALED)

`RedundancyBook` requires a `FailureDomainBook` resolver, rejects unknown
`failure_domain_refs`, and resolves every independence assertion through Book 2
provenance. Failure-domain state is never duplicated inside the assessment.

## Finding D — snapshot lineage (SEALED)

`Book4Provenance.validate_snapshot_lineage` requires every
`source_snapshot_ref` to originate from the resolved Book 2 claim evidence.
Fake or unrelated snapshots are rejected. No second snapshot registry exists.
Documented limitation: Book 2 exposes snapshot identity only through
`RawEvidence.raw_snapshot_ref`, so lineage equality is the narrowest valid
check available without mutating accepted Books 1–3.

## Finding E — structural Book 4/Book 5 boundary (SEALED)

`book4_boundary.Book4RelationSupportPolicy` is now the primary boundary. Only
18 ratified technical relations are admissible for a Book 4 dependency record
(15 Book 1 plus the 3 Book 3 local relations). COLLATERAL_IN, LIQUIDITY_ON,
STAKED_IN, RESTAKED_IN, REDEEMS_FOR, ISSUED_ON, NATIVE_TO, and WRAPS are
structurally rejected. Keyword screening remains defense in depth only.

## Verification

```text
BOOK_1_TESTS = 107 PASS
BOOK_2_TESTS = 108 PASS
BOOK_3_TESTS = 83 PASS
BOOK_4_PRIOR_TESTS = 101 PASS
BOOK_4_R1_FOCUSED_TESTS = 36 PASS
BOOK_4_TOTAL = 137 PASS
TOTAL_CSIA = 435 PASS
CSIA_RUFF = PASS
CSIA_MYPY = PASS (36 source files)
CRYPTO_SENSOR = 2325 PASS / 14 FAIL / 4 SKIPPED
PRE_EXISTING_BASELINE_FAILURES = 14
BOOK4_INTRODUCED_SENSOR_FAILURES = 0
BOOK_1_ACCEPTED_CONTRACT_MUTATIONS = 0
BOOK_2_ACCEPTED_CONTRACT_MUTATIONS = 0
BOOK_3_ACCEPTED_CONTRACT_MUTATIONS = 0
```

Artifacts:

- `CSIA_BOOK_4_HARDENING_R1_MATRIX.json`
- `CSIA_BOOK_4_HARDENING_R1_SENSOR_EQUIVALENCE.md`

```text
BOOK_4_HARDENING_R1 = PASS
BOOK_4_IMPLEMENTATION = COMPLETE_HARDENED
PROPOSED_EXIT_GATE = PASS_CSIA_BOOK4_PROTOCOL_INFRASTRUCTURE_DEPENDENCY_KERNEL
STATUS = READY_FOR_OPERATOR_ACCEPTANCE
BOOK_4_ACCEPTANCE = NOT_SELF_ACCEPTED
BOOK_5 = NOT_STARTED
LIVE_ACQUISITION_AUTHORITY = FALSE
```
