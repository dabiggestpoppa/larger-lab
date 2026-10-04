# CSIA — Book 6 Comparison/Change Replay Precedence Erratum v0.1

**Status:** `RATIFIED`
**Date:** 2026-10-04
**Decision id:** `BOOK6-GAP6-v0.2` (companion provision)
**Kind:** `ERRATUM TO RATIFIED RECORDS — ADDITIVE, NON-RETROACTIVE`
**Grants implementation authority:** `FALSE`
**Edits any ratified record:** `FALSE`

```text
CANONICAL_COMPARISON_REPLAY_CHECK_COUNT = 20
HISTORICAL_v0_4_REPLAY_CHECK_COUNT      = 19

HISTORICAL_19_CHECK_REPLAY_IS_CURRENT = FALSE
SUBSTRATE_20_CHECK_REPLAY_IS_CURRENT  = TRUE

RETROACTIVE_REWRITE         = FALSE
HISTORICAL_RECORD_PRESERVED = TRUE
IMPLEMENTATION_CANONICAL_REPLAY = 20

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

---

## 0. Why an erratum and not an edit

Two **ratified** Book 6 records enumerate a comparison authority replay at two
different counts. Both records are individually valid ratification acts. What
they disagree about is which enumeration is **current for implementation**.

The disagreement is settled here, additively:

- **Neither ratified record is edited, replaced, annotated in place, or
  rewritten.** Each is left exactly as ratified.
- This artifact records the **exact history**, states the **precedence**, and
  binds future implementation to one list.
- The correction is **prospective**. It governs what is built next. It does not
  claim that history was different from what it was.

```text
KIND = ADDITIVE / NON-RETROACTIVE / PROSPECTIVE
```

---

## 1. Exact history — the earlier ratification

```text
ORIGINAL_AMENDMENT_RATIFICATION =
    CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_RATIFICATION_RECORD_v0.1.md
ORIGINAL_AMENDMENT_DECISION_ID = BOOK6-COMPARE-AMEND-v0.4
ORIGINAL_REPLAY_COUNT = 19
ORIGINAL_REPLAY_SECTION_HEADING =
    "Authority replay as ratified (nineteen checks, re-resolved at each use)"
```

Its checks 4–6 were:

```text
 4 baseline-selection methodology identity and version
 5 baseline-selection methodology canonical fingerprint
 6 baseline-selection methodology current authority
```

```text
ORIGINAL_CHECKS_4_6 = PHANTOM BENCHMARK METHODOLOGY CHECKS
```

and its final check was:

```text
19 deterministic change recomputation
```

**These three checks named an object that does not exist in the Book 6
substrate.** There is no "baseline-selection methodology" authority surface
distinct from the `MetricDefinition`/methodology binding already enforced by
accepted runtime. The checks were inherited from a benchmark model that was
itself later withdrawn as a phantom. Their presence in the list is the reason
the list is not a faithful description of the substrate as implemented.

---

## 2. Exact history — the later ratification

```text
LATER_SUBSTRATE_RATIFICATION =
    CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_RECORD_v0.1.md
LATER_SUBSTRATE_DECISION_ID = BOOK6-COMPARE-SUBSTRATE-v0.2
LATER_SUBSTRATE_STATUS      = RATIFIED
CURRENT_REPLAY_COUNT = 20
CURRENT_REPLAY_SECTION_HEADING = "14. Ratified 20-check replay"
```

The later ratification replaced the phantom trio with three **real** selector
checks, and added temporal comparability:

```text
CURRENT_CHECK_4 = baseline selector kind/spec validity
CURRENT_CHECK_5 = deterministic baseline candidate eligibility
CURRENT_CHECK_6 = deterministic PRIOR_COMPARABLE_WINDOW resolution
```

```text
CURRENT_CHECKS_4_6 = BASELINE SELECTOR / CANDIDATE / DETERMINISTIC RESOLUTION
```

```text
CURRENT_CHECK_19 = TEMPORAL COMPARABILITY RESOLUTION
CURRENT_CHECK_20 = DETERMINISTIC CHANGE RECOMPUTATION
```

Note the structural consequence, stated plainly so it is not misread: in the
earlier list position 19 held "deterministic change recomputation"; in the later
list that check is at **20**, and **19** is now **temporal comparability
resolution**. A position therefore does not carry a stable meaning across the
two lists. Enumeration positions are not comparable between them.

```text
CROSS_LIST_POSITION_IDENTITY = FALSE
```

The later ratification addressed the phantom explicitly, in its own words:

> Checks 4–6 were inherited from the phantom benchmark model in v0.4. Grammar
> v0.6 replaces them honestly with three selector checks. The total stays 20,
> but not for cosmetic continuity.

```text
LATER_RECORD_ACKNOWLEDGES_THE_PHANTOM = TRUE
```

---

## 3. The ratified precedence

```text
BOOK6-COMPARE-SUBSTRATE-v0.2
    PROSPECTIVELY SUPERSEDES
the BOOK6-COMPARE-AMEND-v0.4 replay list
FOR IMPLEMENTATION PURPOSES
```

Precisely scoped, because "supersedes" is dangerous when used loosely:

```text
SUPERSEDES  = the replay LIST, for IMPLEMENTATION purposes, going FORWARD
DOES_NOT_SUPERSEDE = the ratification ACT of BOOK6-COMPARE-AMEND-v0.4
DOES_NOT_EDITS      = either record
DOES_NOT_RETRACT    = any other ratified decision id content
DOES_NOT_REOPEN     = GAP_1..GAP_5
```

```text
SUPERSESSION_IS_PROSPECTIVE = TRUE
SUPERSESSION_IS_RETROACTIVE = FALSE
```

The v0.4 ratification remains a real, citable governance act. What it is not is
the current specification of the replay.

---

## 4. The canonical 20-check replay

Reproduced here, unaltered in meaning and order, as the single list that
implementation and review must use:

```text
 1. ComparisonRule identity and version
 2. ComparisonRule operator-ratification binding
 3. ComparisonRule canonical content fingerprint
 4. baseline selector kind/spec validity
 5. deterministic baseline candidate eligibility
 6. deterministic PRIOR_COMPARABLE_WINDOW resolution
 7. delta_operator validity against the closed set and the arithmetic
 8. baseline measurement refs / selection-result integrity
 9. comparison measurement refs
10. input measurement Book 2 current authority
11. input measurement methodology compatibility
12. coverage applicability resolution
13. coverage-sufficiency rule ref (where REQUIRED)
14. coverage-rule ratification and currentness
15. coverage scope match
16. coverage deterministic verdict
17. metric-definition semantic content match
18. compatible input methodology policy match
19. TEMPORAL COMPARABILITY RESOLUTION
20. deterministic comparison/change recomputation
```

```text
REPLAY_CHECK_COUNT              = 20
ALL_20_INDEPENDENTLY_FALSIFIABLE = TRUE
AGGREGATE_ONLY                  = REJECTED
ANY CHECK FAILS -> current_authority = FALSE, history preserved
RATIFIED THEN    != AUTHORITATIVE NOW
```

The count is not pinned by nostalgia: it is 20 because this structure contains
20 independently falsifiable authority checks. If a future implementation proves
more are needed, **the count changes through a new ratification**, not by
quiet editing of this artifact.

---

## 5. Binding rule for any future implementation agent

```text
NO IMPLEMENTATION AGENT MAY USE THE HISTORICAL 19-CHECK REPLAY LIST.
```

```text
HISTORICAL_19_CHECK_REPLAY_USABLE_FOR_IMPLEMENTATION = FALSE
IF A SOURCE, PLAN, OR REVIEW CITES 19 CHECKS AS THE REPLAY
    -> that document is describing the superseded v0.4 list
    -> it is a defect in that document, not an alternative reading
```

Specifically forbidden as implementation content:

```text
baseline-selection methodology identity and version        <- PHANTOM
baseline-selection methodology canonical fingerprint         <- PHANTOM
baseline-selection methodology current authority            <- PHANTOM
```

A faithful implementation of the replay must **falsify** all 20 independently.
Falsifiability is the property that made the 19-check list unusable: three of
its members could not fail, because the object they named does not exist.

```text
CHECKS_THAT_CANNOT_FAIL = NOT ACCEPTABLE IN A REPLAY
```

---

## 6. Explicit non-claims

Stated so that no later reader infers them:

```text
IT IS NOT CLAIMED THAT the v0.4 record originally contained 20 checks
IT IS NOT CLAIMED THAT the v0.4 record was wrong when ratified
IT IS NOT CLAIMED THAT the v0.4 record is fraudulent or retracted
IT IS NOT CLAIMED THAT the substrate record rewrote the v0.4 record
IT IS NOT CLAIMED THAT position 19 means the same thing in both lists
IT IS NOT CLAIMED THAT any count is immutable against future evidence
```

```text
THE_v0_4_RECORD_CONTAINED_19_CHECKS = TRUE
THE_v0_4_RECORD_STILL_CONTAINS_19_CHECKS = TRUE
THE_v0_4_RECORD_WAS_EDITED = FALSE
```

---

## 7. Relationship to the earlier draft erratum

`CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_RATIFICATION_RECORD_ERRATUM_v0.1.md`
observed the same phantom and correctly recorded that the correction **had not
occurred**. It remains:

```text
PRIOR_DRAFT_ERRATUM_STATUS = DRAFT_PENDING_OPERATOR_RATIFICATION (UNCHANGED)
PRIOR_DRAFT_ERRATUM_EDITED = FALSE
```

Its factual description of the phantom stands and is corroborated here. What
changes with this artifact is only that a precedence determination now exists.

```text
THIS_ARTIFACT_RATIFIES_THE_PRIOR_DRAFT_ERRATUM = FALSE
THIS_ARTIFACT_SUPERSEDES_THE_PRIOR_DRAFT_ON_PRECEDENCE_ONLY = TRUE
```

---

## 8. Standing state after this erratum

```text
COMPARISON_REPLAY_CHECK_COUNT = 20
COMPARISON_REPLAY_SOURCE =
    CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_RECORD_v0.1.md  (section 14)

GAP_1..GAP_5 = CLOSED / RATIFIED
GAP_6        = CLOSED / RATIFIED
GAP_7        = CLOSED / RATIFIED

BOOK_6_COMPARISON_DESIGN = COMPLETE
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## 9. What this erratum did not do

```text
IMPLEMENTATION_AUTHORIZED   = FALSE
SOURCE_CHANGED              = FALSE
TEST_CODE_WRITTEN           = FALSE
BRANCH_CREATED             = FALSE
WORKTREE_CREATED           = FALSE
RECORD_EDITED_IN_PLACE     = FALSE
HISTORY_REWRITTEN          = FALSE
FORCE_PUSHED               = FALSE
GAP_7_OR_GAP_1..5_REOPENED = FALSE
```
