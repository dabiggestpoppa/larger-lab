# CSIA — Book 4 Ratification Errata v0.1

**Errata date:** 2026-09-25
**Scope:** narrow post-publication correction pass
**Ratification lineage:** `10db41b66bcb32f9f1ef408de157867069b82439`

## Status

```text
BOOK = 4
RATIFICATION = PRESERVED
PLAN = v0.2

SEMANTIC_DECISION_CHANGES = 0
D4_DECISION_CHANGES = 0

BOOK_1_AMENDMENTS = 0
BOOK_2_AMENDMENTS = 0
BOOK_3_AMENDMENTS = 0

ERRATUM_1 =
REMOVE INVALID `UNKNOWN` BOOK 2 CLAIMSTATE REFERENCE

ERRATUM_2 =
BIND D4-1..D4-8 TO ACTUAL DECISION COMMIT SHA

BOOK_4_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY = FALSE
BOOK_5 = NOT_STARTED
```

This errata does not reopen ratification. It corrects one invalid namespace
reference and completes binding metadata for the already-ratified D4 decisions.
No D4 decision, invariant, consequence, evidence basis, status, or scope changed.

## Erratum 1 — role-model namespace correction

The role model previously referred to an `UNKNOWN` Book 2 claim. The accepted
Book 2 ClaimState vocabulary has no `UNKNOWN` state. The corrected invariant is:

> A Book 4 domain value of `UNKNOWN` cannot be strengthened by a role label.
> Book 2 claims retain their accepted ClaimState independently.

`UNKNOWN` remains valid only as a Book 4 domain classification. The accepted Book
2 ClaimState values remain exactly:

```text
DECLARED
OBSERVED
INFERRED
CORROBORATED
CONTESTED
UNRESOLVED
STALE
REJECTED
SUPERSEDED
```

## Erratum 2 — D4 binding metadata

The eight D4 decision records previously carried a placeholder binding commit.
Each D4-1 through D4-8 record is now bound to the actual operator-decision
commit:

```text
D4_BINDING_COMMIT_SHA = 8b6106055686721b1b490adc792b0d6c03696e15
```

This is metadata completion only. D4-1 through D4-8 remain `RATIFIED / CLOSED`
with their original semantics and scope.

## Integrity statement

- Book 4 remains `RATIFIED` with plan `v0.2`.
- `STRUCTURAL_FAILURE_COUNT = 0`.
- `BLOCKING_OPERATOR_DECISION_COUNT = 0`.
- Book 1, Book 2, and Book 3 amendment counts remain `0`.
- No Book 4 implementation, live acquisition, RPC, database, graph database,
  Sensor, Book 5, or Books 1–3 mutation is authorized.
- The preserved v0.1 artifacts remain unchanged.
