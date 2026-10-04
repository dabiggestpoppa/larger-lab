# CSIA — Book 6 Implementation Rung Traceability Matrix v0.2

**Status:** `AUDIT_FINDING` — maps rungs to constraints; ratifies nothing.
**Date:** 2026-10-04
**Decision id:** none.
**Grants implementation authority:** `FALSE`
**Reviewed against planning HEAD:** `aec9ac49`
**Implementation base:** `5f94c3f40cea4441470c57671f51454da7377361`

```text
RUNGS_MAPPED       = 11
GREEN_RUNGS        = 11
AMBER_RUNGS        =  0
RED_RUNGS          =  0
KNOWN_EVIDENCE_GAPS = 0

ALL_IMPLEMENTATION_RUNGS_HAVE_RATIFIED_FALSIFICATION = TRUE
```

## Supersession

```text
SUPERSEDES_PROSPECTIVELY =
    CSIA_BOOK_6_IMPLEMENTATION_RUNG_TRACEABILITY_MATRIX_v0.1.md
SUPERSESSION_REASON = THE RUNG 6 EVIDENCE GAP IS CLOSED
v0.1_EDITED = FALSE      (left exactly as committed at d5f2de94)
```

v0.1's mapping of rungs 1-5 and 7-11 stands unchanged. Only RUNG 6 moves.

---

## 1. The matrix

| Rung | Ratified artifact | Decision id | Ratified cases | Draft-only cases | Gate |
|---|---|---|---|---|---|
| 1 | GAP-7 currentness record §3-4 | `BOOK6-GAP7-v0.3` | `TERM-1..5` (5), `CARR-1..19` | — | **GREEN** |
| 2 | GAP-7 currentness record §3-4, §7 | `BOOK6-GAP7-v0.3` | `NV-1..10` (10), `CURR-S1..3` (3), `TERM-5` | — | **GREEN** |
| 3 | GAP-7 currentness record §8 | `BOOK6-GAP7-v0.3` | all 39 (`19+3+5+10+2`) | — | **GREEN** |
| 4 | Substrate record §5-7 | `BOOK6-COMPARE-SUBSTRATE-v0.2` | ratified 237, groups A..H | — | **GREEN** |
| 5 | Substrate record §7 (`5E`), §14 checks 1-3 | `BOOK6-COMPARE-SUBSTRATE-v0.2` | ratified 237 | — | **GREEN** |
| 6 | GAP-6 record §2-4 + TIME test record | `BOOK6-GAP6-v0.2` + `BOOK6-GAP6-TIME-TESTS-v0.1` | **15 (`TIME-1..15`)** | — | **GREEN** |
| 7 | Substrate record §5-6, §14 checks 12-16, 19 | `BOOK6-COMPARE-SUBSTRATE-v0.2` | ratified 237 (`COV-1`, `COV-12`) | — | **GREEN** |
| 8 | Substrate record §4, §14 check 20 | `BOOK6-COMPARE-SUBSTRATE-v0.2` | ratified 237 | — | **GREEN** |
| 9 | Substrate record §14 + replay precedence erratum | `BOOK6-COMPARE-SUBSTRATE-v0.2` + `BOOK6-GAP6-v0.2` | ratified 237 | — | **GREEN** |
| 10 | Substrate record §15 negative-surface groups | `BOOK6-COMPARE-SUBSTRATE-v0.2` | `POL-1`, `POL-11`, `UNIT-1`, `UNIT-4`, `NEG-SURFACE` | — | **GREEN** |
| 11 | Sensor baseline pin + measured Book 6 baselines | **PIN** | B1-B6, R1-R3, sensor 2343 | — | **GREEN** |

```text
RATIFIED_CONSTRAINT_PRESENT_FOR_EVERY_RUNG  = TRUE
RATIFIED_FALSIFICATION_PRESENT_FOR_EVERY_RUNG = TRUE
```

Every rung now has **both** a ratified constraint and at least one ratified
case that can fail it. That property did not hold for any rung in v0.1.

## 2. What changed for RUNG 6

v0.1 recorded:

```text
RUNG 6  = AMBER
RATIFIED 6E DOCTRINE            = TRUE
RATIFIED 6E FALSIFICATION CASES = 0
DRAFT_ONLY 6E CASES             = 15   (TIME-1..15, spec v0.4)
```

and measured, against the ratified 237-case contract:

```text
INSTANTANEOUS in v0.3 = 0
WindowClass   in v0.3 = 0
effective_start in v0.3 = 0
effective_end   in v0.3 = 0
```

v0.2 records:

```text
RUNG 6                           = GREEN
RATIFIED 6E DOCTRINE             = TRUE    (BOOK6-GAP6-v0.2)
RATIFIED 6E FALSIFICATION CASES  = 15      (BOOK6-GAP6-TIME-TESTS-v0.1)
DRAFT_ONLY 6E CASES              =  0
```

### 2.1 The gate moved AMBER -> GREEN on a repaired case

Ratifying the fifteen cases required repairing TIME-11 first. v0.4's TIME-11
was not merely uncovered — it was invalid, contradicting ratified doctrine
twice:

```text
TIME-11 v0.4 = CONTRADICTS_B_STRICT      = TRUE   (status as deciding gate)
TIME-11 v0.4 = CONTRADICTS_GAP6_ORDERING = TRUE   (inverted the lexical tie-break)
```

The ratified TIME-11 excludes the historical candidate by **terminality**:

```text
REFUSAL_REASON_A = TERMINALITY
STATUS_REFUSAL   = FALSE
STATUS_CHANGES_TIME11_OUTCOME = FALSE   (across all four status permutations)
```

So RUNG 6 did not move because a gap was declared closed. It moved because the
one defective case was replaced by a case that is **stronger** than the one it
replaced, and then ratified.

---

## 3. Findings carried forward from v0.1

Neither finding was created by the TIME ratification, and neither is closed by
it. Both are recorded honestly rather than quietly closed.

### FINDING-2 (v0.1) — cosmetic, unresolved

The GAP-7 test spec v0.3 states its case count five times. Four say 39; one
says 38. 39 is correct; the outlier is a stale sentence, left unrepaired under
the additive-errata rule.

```text
STATUS = OPEN / COSMETIC / DOES NOT AFFECT ANY RUNG GATE
```

### FINDING-3 (v0.1) — structural, unresolved

Three document families carry `DRAFT_PENDING_OPERATOR_RATIFICATION` headers
while a ratification record adopts them. Nothing is under-ratified; a reader
checking only headers would conclude the opposite.

```text
STATUS = OPEN / STRUCTURAL / DOES NOT AFFECT ANY RUNG GATE
MISRATIFIED_ARTIFACTS = 0
```

### FINDING-1 (v0.1) — MATERIAL, NOW CLOSED

```text
v0.1:  RUNG 6 = AMBER; 6E doctrine ratified, 0 ratified cases able to fail it
v0.2:  RUNG 6 = GREEN; 6E doctrine ratified, 15 ratified cases able to fail it
```

```text
MATERIAL_FINDINGS_OPEN = 0
```

## 4. A fourth finding, new to this matrix

The three earlier findings shared a shape: a **check that could not fail**.
There is now a fourth shape, and it is arguably the more dangerous one.

```text
A CHECK THAT CANNOT FAIL   -> named a non-existent object       (checks 4-6)
A CONTRACT WITH NO TEST    -> ratified doctrine, no case        (RUNG 6)
AN INSTRUCTION THAT CONTRADICTS DOCTRINE -> review v0.1 D3
A WRONG TEST               -> TIME-11 v0.4 certified the INVERSE of B-STRICT
```

The fourth is only detectable by reading the case against ratified doctrine.
It passes every mechanical check: the field exists, the case is well-formed,
it is independently falsifiable, and it fails loudly on any wrong
implementation. Nothing in the artefact's structure would flag it. Only
doctrine comparison does.

```text
MECHANICAL_CHECKS_THAT_WOULD_HAVE_CAUGHT_TIME_11_v0.4 = 0
DOCTRINE_COMPARISON_CAUGHT_IT                       = 1
```

This is an argument for keeping the audit of test contracts against ratified
doctrine as a standing activity rather than a one-off, because the class of
defect that matters most here is invisible to every other kind of check.

## 5. Citation verification

Every citation re-resolved programmatically at `aec9ac49`.

```text
ARTIFACTS CITED                 17
ARTIFACTS RESOLVED ON DISK      17
ARTIFACTS MISSING                0

TIME cases resolved in test spec v0.5:  15  (expected 15)
TIME cases resolved in test spec v0.3:   0  (expected 0 — v0.3 predates 6E)
GAP-7 case ids resolved: CURR-S 3, TERM 5, NV 10, STRUCT 2
```

```text
NO INVENTED CITATIONS = TRUE
NO CASE ID CITED WITHOUT RESOLVING = TRUE
```

## 6. What this matrix did not do

```text
RATIFIED_ANYTHING          = FALSE
RE_SCORED_ANY_REVIEW      = FALSE
EDITED_MATRIX_v0.1         = FALSE
EDITED_ANY_RATIFIED_RECORD = FALSE
IMPLEMENTATION_AUTHORIZED  = FALSE
SOURCE_CHANGED             = FALSE
TEST_CODE_WRITTEN          = FALSE
BRANCH_OR_WORKTREE_CREATED = FALSE
FROZEN_WORKTREE_MUTATED    = FALSE
GAP_REOPENED               = FALSE
```

## 7. Cross-references

```text
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_RUNG_TRACEABILITY_MATRIX_v0.1.md
    superseded
CSIA_BOOK_6_COMPARISON_CHANGE_TIME_TEST_RATIFICATION_RECORD_v0.1.md  RUNG 6
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.5.md        15 TIME
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.3.md        237
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_RECORD_v0.1.md        6E doctrine
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md rungs 1-3
CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_RECORD_v0.1.md rungs 4-10
CSIA_BOOK_6_COMPARISON_CHANGE_REPLAY_PRECEDENCE_ERRATUM_v0.1.md      rung 9
CSIA_BOOK_6_SENSOR_REGRESSION_BASELINE_PIN_v0.1.md                   rung 11
CSIA_BOOK_6_STATUS_VALIDATOR_LIFECYCLE_AMENDMENT_DEFERRED_v0.1.md    out of scope
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.3.md
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```
