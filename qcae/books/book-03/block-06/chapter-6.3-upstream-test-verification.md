# Chapter 6.3 — Upstream Test Verification

## Mission

Reproduce the candidate's own test claims under the controlled build before constructing independent proof.

## 6.3.1 Test Inventory

Classify upstream tests:

```text
unit
integration
e2e
property/fuzz
regression
benchmark
demo/example disguised as test
network/external-service
disabled/skipped
```

## 6.3.2 Full vs Relevant Suite

Run the broad suite when practical, but separately identify tests touching target atoms.

## 6.3.3 Skips and Xfails

Skipped/expected-failure tests are evidence and must not disappear from summary statistics.

## 6.3.4 Environment Modification

Any patch/config/environment change needed to make tests run must be recorded. QCAE cannot silently repair upstream and report pristine success.

## 6.3.5 Test Integrity

Detect obvious tests that merely assert mocks/stubs or do not exercise claimed behavior. This is source/proving analysis, not a reason to discard the suite entirely.

## 6.3.6 Result Semantics

```text
UPSTREAM_TESTS_REPRODUCED
PARTIAL
FAILED
UNRUNNABLE
ENVIRONMENT_INCONCLUSIVE
```

## 6.3.7 Meaning

Passing upstream tests proves that the tested revision satisfies its own executable assertions in the QCAE environment. It does **not** prove the Quant Lab contract.

## Invariants

1. Upstream tests are reproduced, not trusted by reputation.
2. Skips/xfails are visible.
3. Candidate modifications are explicit.
4. Atom-relevant test coverage is identified separately.
5. Upstream test success is not independent contract proof.

## Exit Criteria

QCAE knows whether upstream's own executable behavior claims can be reproduced and where its test suite leaves contract gaps.
