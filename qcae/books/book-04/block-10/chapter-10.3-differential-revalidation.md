# Chapter 10.3 — Differential Revalidation

## Mission

Re-run only the evidence gates plausibly affected by a change while escalating to full revalidation when impact cannot be safely bounded.

## Impact Graph

Map changed source/dependency/config/data to capability atoms, assumptions, tests, benchmarks, security/legal evidence, and receipts.

## Revalidation Levels

```text
METADATA_ONLY
TARGETED_STATIC
TARGETED_TEST
TARGETED_SECURITY
TARGETED_BENCHMARK
TARGETED_QUANT
FULL_REVALIDATION
```

## Escalation

Unknown dynamic coupling, broad dependency changes, build-chain changes, major interface rewrites, provenance incidents, or unbounded domain changes may force full proving.

## Receipt State

Affected receipts can enter `REVALIDATION_REQUIRED` before a new revision is accepted. Existing last-known-good may remain active if policy allows and unaffected.

## Invariants

1. Revalidation follows evidence dependency impact.
2. Unknown impact escalates rather than assumes safety.
3. New upstream revision is not trusted because old revision passed.
4. Last-known-good remains identifiable.
5. Quant revalidation is triggered by material signal/data/execution/domain changes.

## Exit Criteria

QCAE can update evidence efficiently without weakening the proof standard.
