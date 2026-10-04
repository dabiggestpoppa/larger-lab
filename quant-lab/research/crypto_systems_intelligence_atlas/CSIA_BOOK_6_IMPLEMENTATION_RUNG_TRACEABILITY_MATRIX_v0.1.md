# CSIA — Book 6 Implementation Rung Traceability Matrix v0.1

**Status:** `AUDIT_FINDING` — maps rungs to constraints; ratifies nothing.
**Date:** 2026-10-04
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Reviewed against planning HEAD:** `a3503fee23d0a4d941da0b0e5293b3d4b3d0b777`
**Implementation base:** `5f94c3f40cea4441470c57671f51454da7377361`

```text
RUNGS_MAPPED          = 11
ARTIFACTS_CITED       = 16
ARTIFACTS_MISSING     =  0
CITATIONS_RESOLVED    = 100%
FINDINGS              =  3   (1 material, 1 cosmetic, 1 structural)
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
```

---

## 0. What a traceability matrix is for

An implementation order says *what comes first*. It does not say **what
constrains each step, or whether that constraint is ratified**. Those are
different questions, and conflating them is how an implementer ends up
faithfully building from a draft.

So each rung below carries three things:

```text
RATIFIED ARTIFACT   what binds this rung, with its decision id
RATIFIED CASES      the test cases that can falsify it, that are ratified
DRAFT-ONLY CASES    test cases that can falsify it, that are NOT ratified
GATE                GREEN  - proceed on ratified contracts alone
                    AMBER  - doctrine is ratified, falsification is not
```

Every citation in this document was resolved programmatically against the
corpus. See section 5.

---

## 1. The eleven rungs

Canonical, from `CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1.md`
§6 and `..._GAP6_READINESS_REVIEW_v0.3.md` §5:

```text
RUNG  1  GAP-7 registry currentness primitives / terminality / lineage
RUNG  2  resolve_current hardening + NV-B
RUNG  3  GAP-7 39-case test contract
RUNG  4  comparison grammar / types
RUNG  5  ComparisonRule registry / fingerprint / ratification
RUNG  6  BaselineSelectorSpec + 6E temporal projection
RUNG  7  coverage / comparability gates
RUNG  8  ChangeObservation derivation
RUNG  9  canonical 20-check authority replay
RUNG 10  negative / adversarial comparison tests
RUNG 11  full regression / traceability
```

```text
RUNGS_1_TO_3_PRECEDE_RUNGS_4_TO_9 = TRUE
```

### 1.1 Authority legend

| Tag | Meaning |
|---|---|
| **RAT** | ratified inside a ratification record, cited by its decision id |
| **PIN** | pinned measurement (`CSIA_BOOK_6_SENSOR_REGRESSION_BASELINE_PIN_v0.1.md`) |
| **DRF** | `DRAFT_PENDING_OPERATOR_RATIFICATION` — constrains design, binds nothing |
| **EXP** | exposition of a ratified rule; the authority is the record, not this file |

---

## 2. The matrix

| Rung | Ratified artifact | Decision id | Ratified cases | Draft-only cases | Gate |
|---|---|---|---|---|---|
| 1 | GAP-7 currentness record §3–4 | `BOOK6-GAP7-v0.3` | `TERM-1..5` (5), `CARR-1..19` | — | **GREEN** |
| 2 | GAP-7 currentness record §3–4, §7 | `BOOK6-GAP7-v0.3` | `NV-1..10` (10), `CURR-S1..3` (3), `TERM-5` | — | **GREEN** |
| 3 | GAP-7 currentness record §8 | `BOOK6-GAP7-v0.3` | all 39 (`19+3+5+10+2`) | — | **GREEN** (F-2) |
| 4 | Substrate record §5–7 | `BOOK6-COMPARE-SUBSTRATE-v0.2` | ratified 237, groups A..H | — | **GREEN** |
| 5 | Substrate record §7 (`5E`), §14 checks 1–3 | `BOOK6-COMPARE-SUBSTRATE-v0.2` | ratified 237 | — | **GREEN** |
| 6 | **GAP-6 record §2–§4** | `BOOK6-GAP6-v0.2` | **NONE** | `TIME-1..15` (15) | **AMBER** (F-1) |
| 7 | Substrate record §5–6 (`3C`,`4D`), §14 checks 12–16, 19 | `BOOK6-COMPARE-SUBSTRATE-v0.2` | ratified 237 (`COV-1`, `COV-12`) | — | **GREEN** |
| 8 | Substrate record §4 contract classes, §14 check 20 | `BOOK6-COMPARE-SUBSTRATE-v0.2` | ratified 237 | — | **GREEN** |
| 9 | Substrate record §14 + replay precedence erratum | `BOOK6-COMPARE-SUBSTRATE-v0.2` + `BOOK6-GAP6-v0.2` | ratified 237 | — | **GREEN** |
| 10 | Substrate record §15 negative-surface groups | `BOOK6-COMPARE-SUBSTRATE-v0.2` | `POL-1`, `POL-11`, `UNIT-1`, `UNIT-4`, `NEG-SURFACE` | — | **GREEN** |
| 11 | Sensor baseline pin + measured Book 6 baselines | **PIN** | B1–B6, R1–R3, sensor 2343 | — | **GREEN** |

```text
GREEN_RUNGS = 10
AMBER_RUNGS =  1   (RUNG 6)
RED_RUNGS   =  0
```

---

## 3. Rung detail

### RUNG 1 — terminality and lineage primitives

**Bound by:** GAP-7 currentness record §3 (`CURRENT = TERMINAL AND
STRUCTURALLY_VALID AND METHODOLOGY_CURRENT AND HAS_SOURCE_CLAIMS AND
ALL_SOURCE_CLAIMS_CURRENT`) and §4 (`SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS`,
`MULTIPLE_SUCCESSOR_LINEAGE = FAIL_CLOSED`).

**Falsified by (ratified):** `TERM-1..TERM-5`. `TERM-4` is the branching
fail-closed case and must fail **at the resolver**, not merely in a history
reader; `TERM-5` is the no-resurrection case and is the one a naive repair
breaks.

**Runtime delta it must close:** `book6_registry.py:172-191`
(`measurement_history` refuses branching, registration does not) and
`book6_records.py:203-206` (inverted `SUPERSEDED` validator).

```text
GATE = GREEN
```

### RUNG 2 — `resolve_current` hardening and NV-B

**Bound by:** GAP-7 currentness record §3, §4 (NV-B is new policy, recorded as
such), §7 (`resolve_current` is an authority resolver, not a state-emission
engine; source-less missingness is **not** encoded there).

**Falsified by (ratified):** `NV-1..NV-10` (NV-B concretised), `CURR-S1..S3`
(`ObservationStatus` is not a conjunct), `TERM-5`.

**Runtime delta it must close:** `book6_registry.py:195-216` — the
`if not observation.is_value_bearing: return observation` early return at
line 203 currently returns a source-less non-value-bearing record **as
current**, which is the precise thing NV-B forbids.

**Explicitly out of this rung:** `book6_records.py:202-215`, the `SUPERSEDED`
validator. It is construction-time bookkeeping on no authority path
(`ObservationStatus` is branched on exactly once in all of accepted `src/`, and
that once is the validator itself). Its real incoherence — the status names the
incoming edge while the validator binds it to the outgoing one — is recorded as
a **deferred lifecycle amendment** in
`CSIA_BOOK_6_STATUS_VALIDATOR_LIFECYCLE_AMENDMENT_DEFERRED_v0.1.md`, with five
remedies posed and none selected.

**Exposition (not authority):** clarification v0.3 §8 gives the nine-step
resolver order; the ratification record is what binds.

```text
GATE = GREEN
```

### RUNG 3 — the GAP-7 test contract itself

**Bound by:** GAP-7 currentness record §8:
`TEST_SPEC = CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md`,
`CASES = 39`, `IMPLEMENTED = 0`.

**Falsified by (ratified):** the whole set — `CARR-1..19` (19),
`CURR-S1..S3` (3), `TERM-1..5` (5), `NV-1..10` (10), `STRUCT-1..2` (2).

`CARR-*` is a collapse, not a deletion: `CURR-1..15 less CURR-7` plus
`CURR-16..23 less CURR-24` is 22 surviving `CURR-*` labels, of which 3 were
renamed `CURR-S1..S3`, leaving 19 carried. Two are withdrawn (`CURR-7`
superseded, `CURR-24` subsumed); none is silently dropped.

```text
WITHDRAWN = 2
DROPPED   = 0
GATE = GREEN   (with FINDING-2, cosmetic)
```

### RUNG 4 — comparison grammar and types

**Bound by:** substrate record §4 (`NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES
= 2`, `HIDDEN_THIRD_CONTRACT = NONE`) and §6 (`TemporalComparabilityStatus =
COMPARABLE | NOT_COMPARABLE | UNRESOLVED`, GAP-4 `4D`).

**Falsified by (ratified):** the ratified 237, groups A..H, per substrate §15.

```text
GATE = GREEN
```

### RUNG 5 — `ComparisonRule` registry, fingerprint, ratification

**Bound by:** substrate record §7 (GAP-5 `5E`,
`BASELINE_SELECTOR_AUTHORITY = BOUND_INSIDE_COMPARISON_RULE`) and §14 checks
1–3 (identity and version, operator-ratification binding, canonical content
fingerprint).

**Falsified by (ratified):** the ratified 237. Note that checks 1–3 are the
*replacement* for the phantom benchmark-methodology checks 4–6 of the
superseded v0.4 list — see `..._REPLAY_PRECEDENCE_ERRATUM_v0.1.md`.

```text
GATE = GREEN
```

### RUNG 6 — `BaselineSelectorSpec` and the 6E temporal projection

**Bound by (doctrine):** GAP-6 ratification record §2 (effective-key
projection), §3 (strict precedence, three-step ordering), §4 (WindowClass
boundary), decision id `BOOK6-GAP6-v0.2`.

**Falsified by (ratified): NONE.**
**Falsified by (draft only):** `TIME-1..TIME-15`, 15 cases, in
`CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.4.md`, which is
`DRAFT_PENDING_OPERATOR_RATIFICATION`.

```text
GATE = AMBER     (see FINDING-1)
```

### RUNG 7 — coverage and comparability gates

**Bound by:** substrate record §5 (GAP-3 `3C` presence derivation; absent rule
means `UNRESOLVED`, and `NOT_APPLICABLE` is unreachable from absence), §6
(`4D`), and §14 checks 12–16 plus 19.

**Falsified by (ratified):** the ratified 237, including `COV-1`, `COV-12`.

The coverage firewall — coverage gates authorisation *after* structural
selection, never selection itself — is carried in substrate §9.1 and is
falsifiable within the 237.

```text
GATE = GREEN
```

### RUNG 8 — `ChangeObservation` derivation

**Bound by:** substrate record §4 (second authority-bearing class) and §14
check 20 (deterministic recomputation). Authority is **derived by replay**,
never asserted on the record.

```text
GATE = GREEN
```

### RUNG 9 — the canonical 20-check authority replay

**Bound by:** substrate record §14 (`REPLAY_CHECK_COUNT = 20`,
`ALL_20_INDEPENDENTLY_FALSIFIABLE = TRUE`) as corrected by
`..._REPLAY_PRECEDENCE_ERRATUM_v0.1.md` (substrate prospectively supersedes
the v0.4 nineteen-check list for implementation only).

**Falsified by (ratified):** the ratified 237.

```text
HISTORICAL_19_CHECK_LIST_USABLE = FALSE
GATE = GREEN
```

### RUNG 10 — negative and adversarial comparison tests

**Bound by:** substrate record §15 (negative-surface groups inside the
ratified 237, `BLOCKED = 0`).

**Falsified by (ratified):** `POL-1`, `POL-11` (policy traps: a third delta
operator, a formula string, a callable), `UNIT-1`, `UNIT-4` (unit conversion
attempts), `NEG-SURFACE`.

Negative coverage for reserved selectors, absent coverage, `UNRESOLVED` versus
`NOT_COMPARABLE`, and `BASELINE_UNAVAILABLE` all sit inside the ratified 237.

```text
GATE = GREEN
```

### RUNG 11 — full regression and traceability

**Bound by:** the sensor baseline pin (`PIN`), plus the Book 6 baselines
measured this session at `5f94c3f40c`.

```text
B1 = 107   B2 = 108   B3 = 83   B4 = 230   B5 = 293   B6 = 1341   TOTAL = 2162
R1 =  93   R2 =  46   R3 = 45
SENSOR = 2325 passed / 14 failed / 4 skipped, pinned to 5f94c3f40c

MUST NOT MOVE = B1..B5, R1..R3
MAY INCREASE  = B6 and TOTAL
```

```text
GATE = GREEN
```

---

## 4. Findings

### FINDING-1 — MATERIAL. Rung 6 has ratified doctrine and unratified falsification

This is the finding the matrix exists to produce.

GAP-6 was ratified at `BOOK6-GAP6-v0.2`. Its falsification cases were not.

```text
RATIFIED 6E DOCTRINE            = TRUE
RATIFIED 6E FALSIFICATION CASES = 0
DRAFT-ONLY 6E FALSIFICATION     = 15   (TIME-1..TIME-15)
```

Measured against the ratified 237-case contract (test spec v0.3, ratified as
the implementation test contract by substrate record §15):

```text
occurrences of INSTANTANEOUS   in v0.3 : 0
occurrences of WindowClass     in v0.3 : 0
occurrences of effective_start in v0.3 : 0
occurrences of effective_end   in v0.3 : 0
occurrences of 6E              in v0.3 : 0
```

The ratified test contract has **no instantaneous coverage whatsoever**. The
ratified v0.3 predates the 6E clarification (v0.3 dated 2026-10-02, the 6E
clarification 2026-10-03), so it could not have contained it.

**Why this is material.** Rung 6 is where a coder builds the projection that
decides which observation becomes a baseline. The ratified 237 falsify general
ordering — lexical tie-break, `observed_at` not an input — but none of them
mentions a window class. An implementer working strictly from ratified
contracts would implement 6E with **zero tests capable of falsifying it**: not
`TIME-6` (the same instant is not prior), not `TIME-9` (a forged interval on
an instantaneous record is rejected), not `TIME-11` (a superseded record is
filtered *before* the tie-break), not `TIME-13`/`TIME-14` (no zero-width
interval, no one-day convention).

That is the same failure mode the corpus has already caught once — the phantom
checks 4–6, which could not fail because the object they named did not exist.

```text
AN_UNTESTABLE_RUNG = RUNG 6
THE_PHANTOM_PATTERN = A CHECK THAT CANNOT FAIL
THIS_FINDING        = A RUNG WITH NO *RATIFIED* FAILING CHECK
```

**Effect on the consolidated review.** This review does **not** re-score it.
Criterion 5 `GAP6_ORDERING_CONTRACT_COMPLETE` remains TRUE: the doctrine is
fully specified and no coder must choose policy. Criterion 7
`TEST_CONTRACT_COMPLETE` also remains TRUE on its own terms — the ratified 237
are complete and `BLOCKED = 0`; they are simply silent on 6E.

What changes is that one criterion now carries a **known evidence gap**, which
is a different statement from a lower score. Re-scoring is the operator's
call, not this artifact's.

**Recommended remedy** (operator decision, not taken here):

```text
RATIFY the TIME group (15 cases) as the 6E falsification contract
  -> test spec v0.4 becomes the ratified contract at 252 cases
  -> RUNG 6 gate moves AMBER -> GREEN
  -> cost: one ratification, no design change, no source change
```

Until then:

```text
RUNG_6_MAY_PROCEED_ON_RATIFIED_CONTRACTS_ALONE = FALSE
```

### FINDING-2 — COSMETIC. Stale case count inside the ratified GAP-7 spec

`CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md` states its case
count five times. Four say 39; one says 38.

| Location | Says |
|---|---|
| line 8, `**Cases:**` | 39 |
| line 23, `TOTAL` | 39 |
| **line 60, `v0.3: N cases`** | **38** |
| line 226, `19 + 3 + 5 + 10 + 2 =` | 39 |
| GAP-7 ratification record §8 | 39 |

**39 is correct.** The line-226 arithmetic sums to 39, the ratification record
says 39, and four of five statements agree. Line 60 is a stale sentence from
before the accounting settled.

```text
CORRECT_COUNT = 39
OUTLIER_LINES = 1  (line 60)
SEMANTIC_CONTENT_AFFECTED = 0
```

Recorded rather than repaired, under the corpus rule that committed ratified
material is corrected by additive errata and not edited in place. The ratified
count is 39.

### FINDING-3 — STRUCTURAL. Draft headers on ratified-by-inclusion specs

Several documents that the ratification records adopt still carry
`DRAFT_PENDING_OPERATOR_RATIFICATION` in their own headers:

```text
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md
    header DRAFT, but named by GAP-7 ratification record section 8 (CASES = 39)
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.3.md
    header DRAFT, but ratified as THE IMPLEMENTATION TEST CONTRACT by
    substrate record section 15 (237 cases)
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.6.md / _v0.7.md
    header DRAFT, but cited as verified by the substrate ratification record
```

The ratification record is the authority in each case, so nothing is
under-ratified. But a reader who checks only the header would conclude the
opposite, and the matrix above had to resolve each one by hand.

```text
ARTIFACTS_ADOPTED_BY_A_RECORD_BUT_MARKED_DRAFT = 3 families
MISRATIFIED_ARTIFACTS                          = 0
HEADER_IS_AUTHORITATIVE                        = FALSE
```

The distinction that matters, and that this matrix preserves: **a draft that a
record adopts is adopted; a draft nobody adopts — like the `TIME` group — is
not.**

---

## 5. Citation verification

Every citation in this document was resolved programmatically against the
corpus at planning HEAD `a3503fee`.

```text
ARTIFACTS CITED                 16
ARTIFACTS RESOLVED ON DISK      16
ARTIFACTS MISSING                0

GAP-7 case IDs resolved in test spec v0.3:
  CURR-S1..S3    distinct =  3   (expected 3)
  TERM-1..TERM-5 distinct =  5   (expected 5)
  NV-1..NV-10    distinct = 10   (expected 10)
  STRUCT-1..2    distinct =  2   (expected 2)

Rung -> case resolution:
  rung 1  TERM    resolved =  5
  rung 2  NV      resolved = 10
  rung 3  STRUCT  resolved =  2
  rung 6  TIME    resolved = 15   in v0.4 (DRAFT)
  rung 6  TIME    resolved =  0   in v0.3 (RATIFIED)   <- FINDING-1
```

```text
NO INVENTED CITATIONS = TRUE
NO CASE ID CITED WITHOUT RESOLVING = TRUE
```

---

## 6. Verdict

```text
RUNGS_MAPPED        = 11
RATIFIED_CONSTRAINT_PRESENT_FOR_EVERY_RUNG = TRUE
RATIFIED_FALSIFICATION_PRESENT_FOR_EVERY_RUNG = FALSE   (RUNG 6)

GREEN_RUNGS = 10
AMBER_RUNGS =  1   (RUNG 6)
RED_RUNGS   =  0
```

The implementation order is sound as an **order**. Its coverage is sound except
at one rung, and that one rung is the newest doctrine in the programme.

```text
BOOK_6_DESIGN_COMPLETE            = TRUE
BOOK_6_IMPLEMENTATION_CONTRACT_TRACED = 10 OF 11 FULLY, 1 OF 11 DOCTRINE-ONLY
BOOK_6_IMPLEMENTATION_AUTHORITY   = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY   = FALSE
LIVE_ACQUISITION_AUTHORITY        = FALSE
```

### 6.1 Operator decision this artifact surfaces

```text
RATIFY TIME-1..TIME-15 as the 6E falsification contract?
    -> test spec v0.4 becomes ratified at 252 cases
    -> RUNG 6 AMBER -> GREEN
    -> one ratification; no design change; no source change; no re-work

OR
PROCEED with Rung 6 on ratified doctrine alone
    -> 6E ships with zero ratified tests capable of falsifying it
    -> not recommended; it repeats the phantom pattern the corpus rejected
```

This artifact does not choose. It makes the choice visible, which is the only
thing a traceability matrix is entitled to do.

---

## 7. What this artifact did not do

```text
RATIFIED_ANYTHING          = FALSE
RE_SCORED_THE_REVIEW       = FALSE   (12/12 stands; one criterion gains a
                                       known evidence gap)
EDITED_A_RATIFIED_RECORD   = FALSE
EDITED_A_COMMITTED_SPEC    = FALSE   (FINDING-2 recorded, not repaired)
IMPLEMENTATION_AUTHORIZED  = FALSE
SOURCE_CHANGED             = FALSE
TEST_CODE_WRITTEN          = FALSE
BRANCH_CREATED             = FALSE
WORKTREE_CREATED           = FALSE
FROZEN_WORKTREE_MUTATED    = FALSE
GAPS_REOPENED              = FALSE
```

## 8. Cross-references

```text
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1.md  (section 6 rungs)
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_READINESS_REVIEW_v0.3.md           (section 5 rungs)
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_RECORD_v0.1.md        RUNG 6 doctrine
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.4.md        TIME-1..15 (DRAFT)
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.3.md        237 ratified
CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_RECORD_v0.1.md  RUNG 4-10
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md RUNG 1-3
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md           39 ratified
CSIA_BOOK_6_COMPARISON_CHANGE_REPLAY_PRECEDENCE_ERRATUM_v0.1.md      RUNG 9
CSIA_BOOK_6_SENSOR_REGRESSION_BASELINE_PIN_v0.1.md                   RUNG 11
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```
