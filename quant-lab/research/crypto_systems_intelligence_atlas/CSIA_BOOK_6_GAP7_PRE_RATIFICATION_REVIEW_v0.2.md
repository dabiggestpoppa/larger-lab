# CSIA — Book 6 GAP-7 Pre-Ratification Review v0.2

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION` — a review verdict, not an authorization.
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Subject:** `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_CLARIFICATION_v0.2.md`

**VERDICT: `HOLD_PENDING_NV_DECISION`**

**Supersedes:** `CSIA_BOOK_6_GAP7_PRE_RATIFICATION_REVIEW_v0.1.md` (15/15 PASS).

---

## 0. Disposition of the previous review

```text
PRE_RAT_v0.1 = SUPERSEDED / INTERNAL CONTRADICTION FOUND
```

This is **not** a finding that v0.1's evidence was false. Its executed probes
were sound and are preserved. The defect is narrower and worse for
ratification purposes:

1. **Internal contradiction.** Its subject spec (`TEST_SPEC_v0.1`) made
   `CURR-7` and `CURR-24` demand opposite outcomes. A review that answers 15/15
   while its own subject is self-contradictory cannot have examined both cases
   correctly. The 15/15 is therefore not a reliable summary.
2. **One question was answered on the wrong premise.** Q.8-style authority
   reasoning was accepted from *construction* evidence, which does not reach
   current authority.

The verdict was not lowered because the package is weak. It was lowered because
the package is **not ratifiable as written**, and a passing score obtained over
a contradiction is not evidence of readiness.

---

## 1. Method

Each question is answered from **executed evidence against accepted
`5f94c3f40c`** or from a cited accepted source line. Where a premise is wrong,
the answer says so.

```text
executed probes this round : 3 probe programs, 4 executions
accepted source lines cited : 15
accepted tests cited        : 3
unverified claims           : 0
baseline suite              : 2162 passed (re-measured)
```

---

## 2. The ten questions

### Q1. Is the defect still kernel-wide, so the repair surface is still 7A-KERNEL?

**YES.** `resolve_current` has 8 call sites across 3 modules; 6 are not
comparison code. A repair anywhere other than the single resolver leaves call
sites disagreeing about what "current" means, which `SINGLE_MEANING_OF_CURRENT`
forbids. Verified by re-reading all 8 sites this round.

```text
GAP_7_KERNEL_WIDE_DEFECT = TRUE
REPAIR_SURFACE           = 7A-KERNEL
```

### Q2. Is the status-non-authority doctrine internally consistent?

**YES.** Exactly one rule is stated —
`STATUS_ONLY_CHANGES_CURRENTNESS = FALSE` — and it is applied uniformly.
`CURR-8` was additionally re-attributed: its refusal now comes from lineage,
not from status, so it no longer smuggles in a second status-based path.

### Q3. Does any test case make status authority-bearing?

**NO.** Every status case (`CURR-S1`, `CURR-S2`, `CURR-S3`, `CURR-23`) pairs
identical authority-bearing facts and varies only the field, asserting equality
of verdicts. `CURR-S3` asserts that **terminality**, not status, moves authority.
`CURR-7` and `CURR-24`, the two offenders, are withdrawn. Verified by reading
all 27 cases.

### Q4. Is the CURR-7 / CURR-24 contradiction removed?

**YES.** `CURR-7` superseded by `CURR-S1`; `CURR-24` subsumed by `CURR-S1`/`CURR-S2`.
Both dispositions are recorded with reasons so the lineage is auditable, and
neither expectation survives anywhere in the v0.2 spec. Additionally measured:
the accepted kernel already returns `CURRENT` for both statuses, so `CURR-7` as
written would have **failed**.

### Q5. Is source-less construction distinguished from source-less authority?

**YES.** `SOURCELESS_MISSINGNESS_CONSTRUCTIBILITY = ACCEPTED` and
`SOURCELESS_MISSINGNESS_CURRENT_AUTHORITY = UNRESOLVED` are stated separately, in
§5 of the clarification and §6.2 of the test spec, with the five distinctions
(construction / registration / queryability / current authority / value
readability) enumerated and never merged.

### Q6. Is the defective early-return behaviour excluded as normative evidence?

**YES.** `DEFECTIVE_BEHAVIOR_IS_NORMATIVE_EVIDENCE = FALSE` is stated and applied.
The v0.1 sentence *"No new policy is invented — NV-A is the already-ratified
behaviour"* is withdrawn verbatim. The matrix records measured uniformity and
then explicitly refuses to read it as doctrine, because the uniformity is an
artifact of `missingness_state in VALUE_BEARING_MISSINGNESS`.

### Q7. Are cited non-value-bearing refs live-revalidated?

**Required: YES. Currently: NO — this is a defect, not a policy choice.**

The package requires revalidation and cites `book6_registry.py:198-201` and
`book6_support.py:165-171`. Measured today, a cited claim decayed to `STALE`
leaves `resolve_current` returning the record, on all eight states, and
`is_authoritative_now` returning `True`. This was measured independently of any
NV policy and is therefore **not** a reason to hold the package — it is part of
what the package specifies to repair.

```text
CITED_REF_PRESENT -> LIVE_BOOK2_REVALIDATION_REQUIRED = TRUE
```

Methodology shows the same bypass and is covered identically (§6.1 of the
clarification): with the methodology invalidated after registration, the
value-bearing record is refused and the non-value-bearing record is not.

### Q8. Is the missingness current-authority policy resolved, or still operator-open?

**EXPLICITLY UNRESOLVED — and that is the finding.**

```text
NON_VALUE_BEARING_SOURCELESS_CURRENT_AUTHORITY = OPEN_OPERATOR_DECISION
```

This question is the reason the verdict is not PASS. Searched: `resolve_current`
(names zero states, never mentions "missingness"), the ratified measurement
grammar §6 (descriptive only), the Book 6 plan ratification record (one scope
mention), the whole governance corpus for the eight state names (every
`NOT_APPLICABLE` hit belongs to the unrelated coverage enum), and all accepted
tests (only value-bearing records are ever passed to `is_authoritative_now`).

**Nothing settles it.** The v0.1 claim that it was settled was wrong, and is
withdrawn.

### Q9. Is terminality universal across value-bearing and non-value-bearing?

**YES, as doctrine — and currently unenforced.**

Measured: a non-value-bearing record can be superseded, and
`measurement_history` returns the full chain for it. Terminality is therefore
capable of applying to non-value-bearing records.

```text
NON_VALUE_BEARING_CAN_BE_HISTORICAL = TRUE
```

However, measured at the same time: a **superseded** non-value-bearing
predecessor still resolves `CURRENT`, because `resolve_current` never consults
lineage. And registering two successors of one predecessor is **accepted** at
registration — branching is refused only when `measurement_history` walks it.
Both are recorded as defects for the future implementation round.

### Q10. Is no-resurrection preserved?

**YES as doctrine; NOT enforced today.**

`PREDECESSOR_NEVER_RESURRECTS = TRUE` and
`MULTIPLE_SUCCESSOR_LINEAGE = FAIL_CLOSED` are both carried unchanged and were
not reopened. Neither is implemented in `resolve_current` today. That is the
defect, and it is precisely what `CURR-S3`, `CURR-6` and `CURR-21` specify.


---

## 3. Scorecard

```text
Q1  7A still kernel-wide                        YES
Q2  status non-authority internally consistent YES
Q3  any case makes status authority-bearing     NO
Q4  CURR-7 / CURR-24 contradiction removed     YES
Q5  construction distinguished from authority   YES
Q6  defective behaviour excluded as evidence   YES
Q7  cited non-value refs live-revalidated      YES (specified; defect measured)
Q8  missingness current-authority policy       UNRESOLVED  <-- operator-open
Q9  terminality universal                      YES (doctrine; unenforced)
Q10 no-resurrection preserved                  YES (doctrine; unenforced)

ANSWERED = 10
BLOCKING = 1  (Q8 only)
```

Eight of the ten questions answer cleanly, and the two "YES (doctrine;
unenforced)" answers describe the defect the package exists to repair — they
are not gaps in the package. **Q8 alone blocks ratification**, and it is
blocked for the substantive reason the external review gave: accepted doctrine
does not decide it, and choosing it silently would substitute the program's
defective behavior for operator judgment.

**A PASS would be the wrong output here.** Printing PASS because the other nine
questions are clean would record a resolution that does not exist.

```text
VERDICT = HOLD_PENDING_NV_DECISION
GAP_7_RATIFIED = FALSE
```

---

## 4. What ratification would require

1. The operator selects `NV-A`, `NV-B`, `NV-C` or `HOLD` (decision packet v0.3).
2. The three policy-blocked cases (`NV-1`, `NV-2`, `NV-5`) are fixed to the
   selected policy in the test spec.
3. Pre-ratification review v0.3 re-runs with Q8 answered from the operator
   record rather than from accepted sources.
4. Only then may GAP-7 be ratified, and GAP-6 follow.

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

**This review grants nothing.** It is a verdict, not an authorization.
