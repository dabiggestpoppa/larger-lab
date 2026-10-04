# CSIA — Book 6 TIME Fixture Pre-Ratification Review v0.1

**Status:** `AUDIT_FINDING` — assesses constructibility; ratifies nothing.
**Date:** 2026-10-04
**Subject:** `CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.6.md`
**Verdict:** `12 / 12 PASS` — see §3 for what that verdict covers.
**Grants implementation authority:** `FALSE`

```text
OPERATOR_DECISION = REPAIR TIME-11.1 FIXTURE ONLY
DOCTRINE_CHANGED  = FALSE
STATUS_VALIDATOR_EDIT = FALSE
LIFECYCLE_REMEDY_SELECTED = NONE
```

## 1. Method

The fixture was **executed**, not reasoned about. All four permutations were
built against the accepted lifecycle validator in
`book6_records.py:_check_supersession_discipline` at the frozen Book 6 base
`5f94c3f40c`, and each was registered.

## 2. The blocker, as measured

v0.5's fixture made `A` a root. Measured:

```text
case 1   A=OBSERVED    B=OBSERVED    -> CONSTRUCTIBLE
case 2   A=SUPERSEDED  B=OBSERVED    -> REFUSED
case 3   A=OBSERVED    B=SUPERSEDED  -> CONSTRUCTIBLE
case 4   A=SUPERSEDED  B=SUPERSEDED  -> REFUSED

REFUSAL = "a SUPERSEDED observation must name the observation it superseded"
```

Two of four ratified permutations could not be built. Cause: the recorded
lifecycle incoherence, where the validator pairs `SUPERSEDED` with the
**outgoing** edge while the status names the **incoming** one.

## 3. The twelve questions

| # | Question | Required | Answer | Evidence |
|---|---|---|---|---|
| 1 | All four status permutations construct | YES | **YES** | measured; all four return a full record set |
| 2 | All four use identical lineage structure | YES | **YES** | `Z <- A <- S`, `Y <- B` in every run |
| 3 | Only status varies | YES | **YES** | diffed record-by-record; only `A.status` and `B.status` differ |
| 4 | `A` is non-terminal because `S` supersedes `A` | YES | **YES** | successor count 1; no status consulted |
| 5 | `B` is terminal | YES | **YES** | no record supersedes `B` |
| 6 | `A` has the lexically greater `measurement_ref` | YES | **YES** | `A` > `B` lexically; tie-break would pick `A` |
| 7 | `A` is filtered before ordering | YES | **YES** | filtered in ELIGIBILITY; ordering never sees it |
| 8 | Refusal reason is terminality | YES | **YES** | `REFUSAL_REASON_A = TERMINALITY` |
| 9 | Status does not affect the outcome | YES | **YES** | identical outcome in all four |
| 10 | No lifecycle validator edit is required | YES | **YES** | fixture built against the **accepted** validator, unmodified |
| 11 | No doctrine changed | YES | **YES** | TIME-11 meaning, B-STRICT and 6E untouched |
| 12 | All other 251 cases carried unchanged | YES | **YES** | v0.6 produced by copy; diff confined to header + TIME-11.1 + renames |

```text
PASS = 12 / 12
HOLD = FALSE
```

### 3.1 What this verdict covers

It covers **constructibility and scope**. It does not cover whether the eventual
implementation passes — that is rung 10's job, and this review ran no test.

## 4. The structural diff

```text
CHANGED_IN_v0.6 = THE TIME-11.1 STRUCTURAL FIXTURE ONLY
CASES_CHANGED   = 0
CASES_CARRIED   = 252
TIME_CASES      = 15
```

Every assertion TIME-11.1 made in v0.5 survives. The four permutations, the
load-bearing character of case 1, the refusal reason, and the "tie-break never
sees A" property are all unchanged. Only the *shape* of the supporting records
changed, and only so the case can exist.

## 5. The operative question, applied

*Would each case still be meaningful if `ObservationStatus` were deleted?*

```text
v0.5 TIME-11.1 -> FALSE  (2 of 4 permutations unbuildable without the field)
v0.6 TIME-11.1 -> TRUE   (all four build, none depends on status)
```

This is the same B-STRICT test used when TIME-11 v0.4 was rejected. v0.6 passes
it; v0.5 did not.

## 6. Residual, recorded not blocking

```text
TERMINALITY_SPECIFICITY_PROVEN_BY_TIME_11_ALONE = FALSE
```

Still open, still non-gating, unchanged by this round. The suggested `TIME-16`
hardening — the same fixture with the non-terminal candidate made lexically
**smaller** — remains the way to close it.

## 7. Explicit non-actions

```text
STATUS_VALIDATOR_EDITED   = FALSE
OBSERVATION_STATUS_CHANGED = FALSE
NEW_LIFECYCLE_FIELD_ADDED = FALSE
REGISTRATION_POLICY_CHANGED = FALSE
STATUS_AUTHORITY          = FALSE
LIFECYCLE_REMEDY_SELECTED = NONE
DEFERRED_LIFECYCLE_RECORD_EDITED = FALSE
DOCTRINE_CHANGED          = FALSE
GAP_6_REOPENED            = FALSE
GAP_7_REOPENED            = FALSE
IMPLEMENTATION_STARTED    = FALSE
```
