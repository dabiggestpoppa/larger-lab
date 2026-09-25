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
