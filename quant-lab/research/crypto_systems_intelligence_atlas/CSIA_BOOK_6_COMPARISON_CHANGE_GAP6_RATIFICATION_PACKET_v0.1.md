# CSIA — Book 6 Comparison/Change: GAP-6 Ratification Packet v0.1

**Status:** `AWAITING_OPERATOR_DECISION`
**Date:** 2026-10-03
**Decision:** `RATIFY_GAP6_6E_WINDOW_CLASS_AWARE_ORDERING` **or** `HOLD`
**Grants implementation authority:** `FALSE`

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

---

## 1. What is being decided

Whether to ratify **GAP-6 = `6E WINDOW_CLASS_AWARE_ORDERING_KEYS`** — a narrow
fix to the single clause of the ratified substrate that review v0.4 found not
implementable.

```text
RATIFY  -> GAP-6 closes; the readiness verdict becomes unconditional
           (review v0.5 stands at 10/10)
HOLD    -> GAP-6 stays open; review v0.5's two upgraded criteria revert to
           NOT_SUPPORTABLE and the readiness verdict reverts to HOLD
```

**Neither branch authorizes implementation.** That would be a separate, later
decision on a separate artifact.

---

## 2. The decision's two options

| Option | Meaning |
|---|---|
| **A — `RATIFY_GAP6_6E_WINDOW_CLASS_AWARE_ORDERING`** | adopt the ordering projection; GAP-6 closes |
| **B — `HOLD`** | decline; GAP-6 remains open and the readiness HOLD stands |

There is no third option on the table. `6E` was selected by operator direction;
the rejected alternatives (zero-width interval, one-day convention, blanket
exclusion, blanket refusal) are recorded in the clarification §2 and are **not**
re-proposed here.

---

## 3. The artifact set being ratified

| # | Artifact | Lines | Role |
|---|---|---|---|
| 1 | `CSIA_BOOK_6_COMPARISON_CHANGE_INSTANTANEOUS_ORDERING_CLARIFICATION_v0.1.md` | 393 | normative GAP-6 definition |
| 2 | `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.7.md` | 320 | successor grammar; §2.4 replaced |
| 3 | `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.7.md` | 188 | successor plan; gates G-16..G-19 |
| 4 | `CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.4.md` | 289 | 237 carried + 15 TIME = 252 |

Supporting reviews (not ratified; they are verdicts):

| Artifact | Verdict |
|---|---|
| `..._INSTANTANEOUS_ORDERING_PRE_RATIFICATION_REVIEW_v0.1.md` | **15 / 15 PASS** |
| `..._IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.5.md` | **10 TRUE / 0 FALSE** |

**The ratified v0.6 artifacts are NOT edited.** Grammar v0.6, plan v0.6, test
spec v0.3 and substrate clarification v0.2 keep their ratified text; the
correction is **prospective**, exactly as the phantom benchmark correction was
handled in grammar v0.6 §0.1.

---

## 4. Basis for the recommendation to proceed to a decision

```text
PRE_RATIFICATION_REVIEW = 15 / 15 PASS
AUTHORIZATION_REVIEW_v0.5 = 10 TRUE / 0 FALSE
TEST_SPEC_v0.4_CASES = 252   (237 carried + 15 TIME)
TEST_SPEC_BLOCKED = 0
REPLAY_CHECK_COUNT = 20
NEW_PUBLIC_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
HIDDEN_THIRD_CONTRACT = NONE

GAP_1..GAP_5 = CLOSED / UNCHANGED / NOT REOPENED
SUBSTRATE_RATIFICATION = STANDS
```

This packet **records readiness; it does not ratify**. No option is selected
here.

---

## 5. What ratification would and would not do

**Would:**

```text
GAP_6                         = CLOSED / 6E
GRAMMAR                       = v0.7 IN FORCE (successor to v0.6)
PLAN                          = v0.7 IN FORCE (successor to v0.6)
TEST_SPEC                     = v0.4 IN FORCE (252 cases)
REVIEW_v0.5_TWO_UPGRADED_CRITERIA = UNCONDITIONAL
```

**Would NOT:**

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = STILL FALSE
AUTHORIZE_IMPLEMENTATION        = NO
AUTHORIZE_ANY_BENCHMARK_RULE    = NO
AUTHORIZE_ANY_COVERAGE_RULE     = NO
AUTHORIZE_ANY_COMPARISON_RULE   = NO
AUTHORIZE_CLASS_C_DESIGN        = NO
REOPEN_GAP_1..GAP_5             = NO
REVERSE_SUBSTRATE_RATIFICATION  = NO
```

---

## 6. Standing conditions carried through either branch

```text
SELECTOR_AGGREGATES = FALSE
```

If metric aggregation semantics cannot yield a single comparable value from a
selected window, implementation must HOLD that runtime case and surface a
concrete operator decision. **GAP-6 does not authorize aggregation.**

```text
CLASS_C_BENCHMARK = DEFERRED / UNIMPLEMENTED / NOT A BLOCKER
ROLLING_MEAN / ROLLING_MEDIAN / HISTORICAL_DISTRIBUTION / BASELINE_EPOCH
    = RESERVED_NOT_EXECUTABLE
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
BENCHMARK_RULES_RATIFIED            = 0
COMPARISON_RULES_RATIFIED           = 0
```

---

## 7. Operator response format

```text
BOOK6-GAP6-v0.1  = RATIFY_GAP6_6E_WINDOW_CLASS_AWARE_ORDERING | HOLD
```

On `RATIFY`: a ratification record is created, the four affected artifacts in
§3 carry ratified status, and the readiness verdict becomes unconditional.
Implementation still awaits a **separate** decision.

On `HOLD`: GAP-6 stays open, the four drafts remain drafts, and
`..._AUTHORIZATION_REVIEW_v0.5.md`'s two upgraded criteria are annotated as
conditional-and-unmet, returning readiness to HOLD.

---

*Related: `..._SUBSTRATE_RATIFICATION_RECORD_v0.1.md`,
`..._IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.4.md`,
`..._INSTANTANEOUS_ORDERING_CLARIFICATION_v0.1.md`.*
