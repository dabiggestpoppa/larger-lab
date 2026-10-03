# CSIA — Book 6 GAP-7 Pre-Ratification Review v0.1

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION` — a review verdict, not an authorization.
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Subject:** `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_CLARIFICATION_v0.1.md`
**Verdict:** `15 / 15 PASS` — see §3 for what that verdict does and does not cover.

---

## 1. Method

Each question is answered from **executed evidence against accepted
`5f94c3f40c`** or from a cited accepted source line. Where a question's premise
proved wrong, the answer says so rather than deferring to the premise.

```text
executed probes this round : 6
accepted source lines cited : 14
accepted tests cited       : 3
unverified claims          : 0
```

---

## 2. The fifteen questions

| # | Question | Required | Answer | Evidence |
|---|---|---|---|---|
| 1 | Is GAP-7 kernel-wide? | YES | **YES** | 8 `resolve_current` call sites across 3 modules; 6 outside comparison; `current_value("A")` executed returning superseded `10.0` |
| 2 | Would 7B leave accepted stale-read paths? | YES | **YES** | 7B repairs 2 of 8; sites 1-6 untouched, including the kernel's sanctioned value read |
| 3 | Is terminality structurally decidable? | YES | **YES** | successor set enumerable from `registry._measurements`; `measurement_history` already walks it and refuses branching |
| 4 | Can `ObservationStatus` safely establish currentness? | NO | **NO** | validator `book6_records.py:203` inverts the documented meaning; no valid record can express "I was superseded"; two accepted tests disagree on its meaning |
| 5 | Does the repair mutate predecessors? | NO | **NO** | records frozen (`book6_records.py:106`); proposed resolver is read-only; CURR-20 pins non-mutation |
| 6 | Can predecessors resurrect? | NO | **NO** | terminality is checked at step 3, before any authority computation; measured broken today, closed by ordering |
| 7 | Do branching lineages fail closed? | YES | **YES** | `measurement_history` already refuses; clarification §7 extends the same refusal to the authority path for A, B and C |
| 8 | Does history remain queryable? | YES | **YES** | `registered_measurement` / `measurement_history` retained as historical accessors; CURR-14, CURR-19 pin it |
| 9 | Does `resolve_current` become the single authority path? | YES | **YES** | clarification §2; `COMPARISON_LOCAL_CURRENTNESS = PROHIBITED` |
| 10 | Are non-value-bearing records covered by explicit authority semantics? | YES | **YES** | clarification §6: all 8 states measured, NV-A recorded, cited path specified |
| 11 | Can a non-value-bearing record bypass authority via an early return? | NO | **NO** (repaired) | bypass measured; clarification §8 moves the return after steps 2-6 |
| 12 | Are source-less missingness semantics explicitly resolved? | YES | **YES** | `test_book6_missingness.py:111` registers exactly such a record; NV-A is recorded behaviour, not new policy |
| 13 | Does the repair avoid comparison-local duplicate currentness? | YES | **YES** | one resolver; no second definition proposed anywhere |
| 14 | Are all eight current call sites repaired centrally? | YES | **YES** | all eight inherit `resolve_current`; clarification §2 table |
| 15 | Does this grant implementation authority? | NO | **NO** | every artifact carries `Grants implementation authority: FALSE` |

```text
PASS = 15 / 15
HOLD = 0
```

---

## 3. What this verdict covers, and what it does not

**Covers:** the clarification is internally consistent, matches the accepted
kernel where the kernel is correct, and closes the GAP-7 scope question on
measured evidence. The 15 questions are the ones this review was asked.

**Does not cover:**

- **Implementation.** Nothing was coded. CURR-1 .. CURR-24 remain unimplemented.
- **Whether the clarification is *right* for the program.** That is an operator
  judgement, not a review output.
- **GAP-6.** Untouched here; see §4.
- **The `ObservationStatus` incoherence.** Quarantined, not fixed. It remains
  open and will need its own amendment.

---

## 4. One correction to the review brief

The Phase 12 instruction stated that a non-value-bearing record citing a decayed
Book 2 claim already behaved correctly, and that "this requirement is already
demonstrated by the reproducer".

**It does not.** Measured:

```text
is_value_bearing   = False
source_claim_refs  = ('fixture:claim:v:a',)   -> cited
cited claim state  = STALE                   -> decayed
is_authoritative_now('nv:refs')              = True    <-- BYPASS
value-bearing control, same decay            = False
```

The early return at `book6_registry.py:203` is gated on `is_value_bearing`
**alone**, not on `source_claim_refs`. The bypass therefore covers cited
non-value-bearing records too, and is **broader** than first recorded.

This does not change any of the fifteen answers — it strengthens Q11 — but the
brief's premise was wrong and is recorded as such rather than inherited.

---

## 5. GAP-6 dependency

```text
GAP_6_TEMPORAL_DESIGN = VALID
GAP_6_RATIFICATION    = STILL HOLD_PENDING_GAP7_RATIFICATION
```

GAP-6 was not ratified in this session and is not ratified here. Its eligibility
premise is supplied by the currentness contract this review covers; once GAP-7 is
ratified and implemented, **GAP-6 readiness must be re-run over the new
contract**. It is not satisfied by this review passing.

---

## 6. Verdict

```text
PRE_RATIFICATION_REVIEW_v0.1 = 15 / 15 PASS
RATIFICATION_GRANTED        = FALSE
IMPLEMENTATION_AUTHORITY    = FALSE

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
BOOK6-COMPARE-SUBSTRATE-v0.2    = RATIFIED, STANDS
GAP_1..GAP_5                    = CLOSED
CHOIR_PLAN_PRESERVED            = TRUE
```
