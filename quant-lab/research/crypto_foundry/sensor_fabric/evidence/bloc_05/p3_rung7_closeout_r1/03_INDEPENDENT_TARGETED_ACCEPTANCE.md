# 03 - Independent targeted acceptance

Package: `p3_final_targeted_acceptance_r4/`, commit
`95c9ee01d61bdcefff0d1a379d0af26de7e788df` on
`agent/crypto-sensor-fabric-p3-production-master-audit-r4` (2026-11-26 07:32
-05:00), 18 files, 3,358 insertions, evidence only. No production source, test,
schema or manifest was modified by it.

The auditor's own label on the package is `SECOND-AGENT TECHNICAL AUDIT - NOT
ORGANIZATIONALLY INDEPENDENT`. That label is preserved verbatim here: the
package is independent of the producer's suite and matrix, and it is not
organizationally independent of the operator.

## What it establishes

| Claim | Evidence in the package | Result |
| --- | --- | --- |
| Targeted matrix passes at the candidate | `repaired_probe_results.json`, `r4_matrix.xml` | **41 / 41 passed**, 0 failed, 0 errored |
| Control copy is unmutated and green before any mutation | `mutation_results.json` -> `CAL_COPY_BASELINE_UNMUTATED` | 41 passed in 1.95 s |
| F4 (selected-revision cutoff) is closed | `test_f4_05_counterexample_future_revision_selected_last`, `test_f4_06_..._selected_first` pass; M1 restores the defect and both fail | **closed** |
| F5 (typed-refusal leakage) is closed | `test_f5_01/02/03` pass; M2 restores the defect and all three fail | **closed** |
| The unresolved replay-binding guard is executable and fail-closed | guard case terminates in `INTEGRATION_REQUIRED` naming the unminted contract; M3 bypass restores a pass | **accepted as a refusal, not as enforcement** |
| Mutations are real removals of a control that now exists | `mutation_results.json` with `provenance_ok` and intended-detector accounting | **3 / 3 DETECTED** |
| Producer's shipped consumer suite is green at the candidate | `shipped_suite_results.json`, `shipped_consumer_suite.xml` (JUnit SHA-256 `91c0ffd35e7ca57f902af8dd9f3a9074094d73cce75dcd6ea8b7f4741fb32c39`) | **177 / 177 passed**, 0 skipped |

The suite grew 161 -> 177 because the repair adds sixteen tracked regressions of
its own; the auditor explicitly notes that the shipped suite being green is why
the independently built probe - not the producer's suite - carries the verdict.

## Mutation accounting

| Mutation | Restores | Detected by | Status |
| --- | --- | --- | --- |
| `M1_CHOSEN_ONLY_CUTOFF` | ordering only the record's own selected revision against the cutoff | `test_f4_05`, `test_f4_06` (2 failed, 39 passed) | DETECTED |
| `M2_RAW_TYPED_REFUSAL_DETAIL` | formatting authored typed detail into the public verdict on both typed branches | `test_f5_01`, `test_f5_02`, `test_f5_03` (3 failed, 38 passed) | DETECTED |
| `M3_BYPASS_UNRESOLVED_REPLAY_BINDING_GUARD` | bypassing the terminal binding guard | the guard control (282-line JUnit trace) | DETECTED |

Each mutation ran against a disposable copy with provenance asserted: the case
checks that the imported `policy.py` came from the copy, so a mutation cannot
silently measure the pristine tree.

## What it explicitly withholds

The recommendation in the package (`§11`) accepts the D1 bounded implementation
scope, F4, F5 and the guard-as-refusal, and then withholds blanket acceptance on
three specific claims:

1. Authoritative `ACCEPT_FIELD_BINDING` - not accepted wholesale.
2. Any claim of complete replay or record binding - the guard is a refusal, not
   binding enforcement.
3. **Canonical regression coverage of `66200f3cb` until §9 closes** - because at
   the time of that audit no canonical bundle for the repair candidate existed.

It also records (in `§10`) that the temporal sweep's malformed-instant arm is
reachable but not exercised by that fixture, with the H04 schema boundary as the
tested path for that case.

## The boundary it left open

`canonical_evidence.json` in the audit package is unambiguous:

```
"bundle_matches_repair_candidate": false
"new_canonical_bundle_for_repair_exists": false
"conclusion": "... §7 reconciliation FOR THE REPAIR CANNOT BE PERFORMED, and the
               targeted acceptance is published without claiming it."
```

The only bundle available to the auditor was executed at `868dd3fc9`, an
ancestor of the repair, with `policy_sha256_executed_tree
ee1b07ee...` against the repair head's `cc5d1bb9...`, and none of the repair's
four controls present.

That is the exact gap this closeout closes on the producer side: a canonical
bundle for `66200f3cb` now exists - 4,968 anchored nodes, `ANCHORED_COMPLETE`,
`GREEN`, digest `45c206d6...` - and is handed over in
`02_EVIDENCE_HANDOFF_AND_BUNDLE_INTEGRITY.md`. What has **not** happened is the
auditor's own reconciliation run over it. That single item is recorded as
pending in `04_RUNG7_ACCEPTANCE_RECORD.md` §4 and is the only reason the target
disposition carries a condition.

## What this acceptance does not license

It is a technical recommendation to the operator. It ratifies nothing: no merge,
no trust promotion, no provider approval, no custody-source activation, no
manifest modification, no gate advancement, no Bloc 6. The auditor says so in its
own `§12`, and this record does not upgrade it.
