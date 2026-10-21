# Chapter 6.8 — Reproducibility Package

## Mission

Bundle enough immutable evidence and instructions that another authorized QCAE worker/reviewer can reproduce the proving result without trusting the original evaluator's narrative.

## 6.8.1 Package Contents

```text
candidate/source identity
artifact digests
contract/spec versions
sandbox/run manifests
build recipe
resolved dependency inventory
upstream test results
independent contract tests
adversarial/regression tests
demo fixtures/results
benchmark definitions/raw results
logs/output hashes
policy/profile versions
known deviations
uncertainty ledger
```

## 6.8.2 Raw vs Derived

Preserve raw measurements/test outputs separately from summaries and evaluator conclusions.

## 6.8.3 Hashing

Evidence objects should be content-addressable or hashed where practical so later receipts can detect mutation.

## 6.8.4 Environment Capture

Capture base image/runtime/compiler/hardware-relevant metadata and any non-hermetic external dependency.

## 6.8.5 Replay

Package should expose a standard replay entry point eventually, subject to policy and availability of licensed/private inputs.

## 6.8.6 Reproducibility Levels

Possible states:

```text
FULLY_REPLAYABLE
REPLAYABLE_WITH_DECLARED_EXTERNALS
PARTIALLY_REPLAYABLE
NON_REPRODUCIBLE
```

Do not claim full reproducibility when proprietary services/data are required but unavailable.

## 6.8.7 Evidence Expiry

Evidence remains scoped to candidate revision, environment, contract, and policy. Upstream changes or contract changes can require revalidation.

## Invariants

1. A proof conclusion is traceable to raw evidence.
2. Evidence mutation is detectable where practical.
3. Environment/external dependencies are explicit.
4. Reproducibility level is honest.
5. Proof is revision/contract/environment scoped.
6. Reproducibility package does not itself grant acquisition authority.

## Exit Criteria

Block 6 produces a durable proving package that can be audited, replayed, compared, and later attached to a Capability Receipt.
