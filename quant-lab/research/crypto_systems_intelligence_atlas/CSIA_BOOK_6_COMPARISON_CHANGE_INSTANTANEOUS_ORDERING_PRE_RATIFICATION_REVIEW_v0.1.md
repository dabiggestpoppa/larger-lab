# CSIA — Instantaneous Ordering: Pre-Ratification Review v0.1

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION` — REVIEW VERDICT, NOT AN
AUTHORIZATION
**Date:** 2026-10-03
**Reviews:** instantaneous ordering clarification v0.1; grammar v0.7; plan
v0.7; test spec v0.4
**Audited source:** `agent/crypto-systems-intelligence-atlas-book6-build` @
`5f94c3f40cea4441470c57671f51454da7377361`

```text
SCORE = 15 / 15 PASS
VERDICT = PASS
```

Every question was answered by **reading accepted source**, not by trusting the
draft under review. Each answer cites its anchor.

---

## 1. The fifteen questions

| # | Question | Required | Answer | Evidence |
|---|----------|----------|--------|----------|
| 1 | Does `INSTANTANEOUS` carry `window_start`/`window_end`? | **NO** | NO | `book6_records.py:169-175` raises if either is not `None` |
| 2 | Does `valid_time` always exist? | **YES** | YES | `book6_records.py:117` `valid_time: datetime`, no default |
| 3 | Does 6E mutate `MeasurementObservation`? | **NO** | NO | derived keys only; TIME-12; model is `frozen=True` |
| 4 | Does 6E fabricate a zero-width interval? | **NO** | NO | no field written; TIME-13 |
| 5 | Does 6E invent a one-day interval? | **NO** | NO | TIME-14; the 1-day span at `book6_support.py:419` is fixture-only |
| 6 | Does interval behaviour remain unchanged? | **YES** | YES | projection is the identity; TIME-7 |
| 7 | Is instantaneous ordering deterministic? | **YES** | YES | total projection + strict `<` + lexical tie-break |
| 8 | Is `observed_at` excluded? | **YES** | YES | TIME-4, TIME-15 |
| 9 | Is caller order excluded? | **YES** | YES | TIME-3 |
| 10 | Is strict prior precedence used? | **YES** | YES | TIME-6 |
| 11 | Is lexical ref only the final tie-break? | **YES** | YES | TIME-5; step 3 only |
| 12 | Are eligibility gates applied before ordering? | **YES** | YES | TIME-11; `status` at `book6_records.py:129` |
| 13 | Are incompatible window classes rejected, not coerced? | **YES** | YES | TIME-8; `validate_against_definition` `:251-256` |
| 14 | Does aggregation stay outside the selector? | **YES** | YES | `SELECTOR_AGGREGATES = FALSE` carried |
| 15 | Does the contract count remain 2? | **YES** | YES | grammar v0.7 §2.4 |

```text
PASS = 15   FAIL = 0   UNANSWERED = 0
```

---

## 2. Notes on the three questions that needed work

### Q1 — answered from the validator, not the annotation

The annotation `window_end: datetime | None` (`book6_records.py:121`) alone
would be weak evidence: it says "may be absent", not "must be absent here". The
decisive evidence is `_check_window_discipline` (`book6_records.py:169-175`),
which **raises** when a non-interval window class declares either field. So for
`INSTANTANEOUS` the fields are absent by enforcement, not by omission.

This distinction matters: a nullable field could be populated by another path.
A forbidden field cannot.

### Q2 — `valid_time` is required, not defaulted

`valid_time: datetime` at `book6_records.py:117` carries **no default**, so an
instantaneous observation cannot exist without a point. That is what makes the
`effective_*` projection well-founded rather than a fallback.

### Q12 — a surface gap, surfaced rather than hidden

Accepted source has the **fields** but not a **resolver**:

```text
ObservationStatus (OBSERVED | SUPERSEDED)   book6_grammar.py:264-272   present
status: ObservationStatus                   book6_records.py:129        present
supersedes_measurement_id                  book6_records.py:130        present
observation_is_current() helper             —                           ABSENT
methodology_is_current() helper             book6_methodology.py:332   present
```

The asymmetry is real: methodologies have a currency resolver, observations do
not. **This is recorded as a surface fact, not treated as a blocker and not
papered over.** The gate GAP-6 specifies is a condition over the existing enum:

```text
eligible requires: observation.status is ObservationStatus.OBSERVED
```

That needs no new helper, no new class, and no invented precedence — and it is
testable (TIME-11), which is how the absence of a resolver stops mattering.

---

## 3. What this review did NOT check

Honesty about the boundary of a pass:

- **No test was run.** Test spec v0.4 is a specification. Nothing was executed.
- **No regression suite was executed.** The 1341 / 2162 / 2343 baselines were
  reproduced earlier in this planning work and the implementation worktree is
  unchanged (`5f94c3f4`, clean), so those baselines stand — but this review did
  not re-run them.
- **The draft was not mechanically diffed against v0.6.** The carry-forward
  table in grammar v0.7 §0.1 was constructed from v0.6's section list and
  checked section by section.
- **Q7 determinism is argued, not executed.** "Total projection + strict `<` +
  lexical tie-break" is a proof sketch over a closed enum; TIME-2/3/5 are where it
  becomes executable evidence.

```text
EXECUTED_TESTS            = 0
REGRESSION_SUITE_RUN      = 0
REVIEW_IS_STATIC_ANALYSIS = TRUE
```

---

## 4. Verdict

```text
SCORE  = 15 / 15 PASS
VERDICT = PASS

GAP_6 = 6E PROPOSED / NOT RATIFIED
GAP_1..GAP_5 = CLOSED / UNCHANGED / NOT REOPENED
SUBSTRATE_RATIFICATION = STANDS

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

**This pass does not authorize implementation.** It says the GAP-6 drafts are
internally consistent and grounded in accepted runtime. The operator decision
remains outstanding.

---

*Next: `..._IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.5.md`.*
