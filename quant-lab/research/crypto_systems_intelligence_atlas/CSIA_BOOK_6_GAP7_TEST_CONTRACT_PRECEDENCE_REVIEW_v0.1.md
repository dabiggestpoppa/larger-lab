# CSIA — Book 6 GAP-7 Test Contract Precedence Review v0.1

**Status:** `PRE_RATIFICATION_REVIEW`
**Date:** 2026-10-05
**Reviews:** `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.4.md`
**Decision id:** none. This review records **no** operator decision.
**Grants implementation authority:** `FALSE`

**VERDICT: 10 / 10 PASS — `BLOCKING = 0`. Recommendation: RATIFY.**

---

## 0. Scope and method

This review asks exactly ten questions, each answerable from the corpus by
quotation. No question is a matter of judgment, preference, or new policy.

```text
QUESTIONS = 10
PASS      = 10
FAIL      =  0
HOLD      =  0
VERDICT   = 10 / 10 PASS
```

Every answer below cites the artifact that settles it. Where the honest answer
required distinguishing what an artifact *says* from what is *inferable* from
it, that distinction is drawn explicitly rather than smoothed over.

---

## 1. Did v0.2 itself carry ratified status?

**Answer: NO.**

```text
v0.2 STATUS = DRAFT_PENDING_OPERATOR_RATIFICATION
v0.2 GRANTS IMPLEMENTATION AUTHORITY = FALSE
```

v0.2 was a specification draft. It was never ratified in its own right, and no
ratification record names it as `TEST_SPEC`. The only ratified test spec named
by any ratification record is v0.3, via `BOOK6-GAP7-v0.3` §8.

```text
RATIFIED_TEST_SPECS_NAMED_BY_RATIFICATION_RECORDS = 1   (v0.3)
```

This distinction is load-bearing for the whole cleanup. It is the reason the
stale outcome is treated as *carried* rather than *ratified*, and it is the
reason carriage yields to a later explicit adoption.

---

## 2. Did its CURR-21 result enter v0.3's ratified carried set?

**Answer: YES.**

Three links, each quotable:

1. **v0.3 §1**, verbatim: *"No carried case changed. No status case changed. No
   terminality case changed."*
2. **v0.3 §3**: the carried cases are *carried unchanged* from audit §10, test
   spec v0.1 §2, and v0.2 §3.
3. **`BOOK6-GAP7-v0.3` §8** binds the result: `TEST_SPEC = ..._v0.3.md`,
   `CASES = 39`, of which `19 carried (CURR-1..15 less CURR-7, CURR-16..23 less
   CURR-24)`.

```text
OLD_COMPONENT_WIDE_CASE_ENTERED_RATIFIED_CONTRACT = TRUE
ENTRANCE_MECHANISM = TRANSITIVE_CARRIAGE, NOT_DIRECT_ADOPTION
```

The ratification adopted a case *set* and declared it unchanged. Adopting a set
unchanged adopts every member's required outcome. `CURR-21`'s outcome was a
member.

---

## 3. Does CURR-21 / CARR-21 require component-wide refusal?

**Answer: YES.**

Test spec v0.2 §5, verbatim:

```text
| CURR-21 | branching lineage `A <- B`, `A <- C` |
         | `resolve_current(A/B/C)` all refuse; `is_authoritative_now` `False` for all |
```

v0.2 §8's table independently records the same case as requiring that
"branching" be *"refused at step 2 too"*. v0.1 §2 states the same outcome.

```text
CARR_21_OLD_OUTCOME = COMPONENT_WIDE
A, B AND C ALL REFUSE = THE REQUIRED OUTCOME
```

---

## 4. Does later `BOOK6-GAP7-SUCCESSOR-CURRENTNESS-v0.1` ratify PER_RECORD?

**Answer: YES.**

Record §3, verbatim:

```text
SUCCESSOR_CURRENTNESS_SCOPE = PER_RECORD
COMPONENT_WIDE_FAIL_CLOSED  = NOT ADOPTED
```

§4 states the rule: `A` not current, `B` and `C` evaluated on their own
conjuncts. §4.1 lists as `PROHIBITED` refusing `B` or `C` because they share a
predecessor.

The record's §3.1 gives the warrant: the five-conjunct definition is exhaustive,
`TERMINAL` is a fact about a record's own successor set, and refusing `B` would
require a sixth conjunct that no ratification supplies.

```text
LATER_RATIFICATION_CONTROLS   = TRUE
SIXTH_CONJUNCT_WAS_RATIFIED   = FALSE
```

---

## 5. Does TERM-6 falsify component-wide refusal?

**Answer: YES.**

Record §5, verbatim:

```text
TERM-6 | A <- B and A <- C | A not current (TERM-4);
                         B current;
                         C current
```

`TERM-6` is the **paired negative** of `TERM-4` — the record says so explicitly
in §5.1. `TERM-4` forbids under-refusing `A`. `TERM-6` forbids over-refusing
`B` and `C`. They describe the **same scenario** with **opposite outcomes** for
two of the three records.

```text
SAME_SCENARIO          = A <- B, A <- C
OPPOSITE_OUTCOME_FOR   = B AND C
BOTH_CANNOT_BE_CURRENT_FALSIFIERS = TRUE
```

---

## 6. Can both old CARR-21 and TERM-6 remain current tests?

**Answer: NO.**

A contract in which two ratified falsifiers demand opposite outcomes for the
same input is not a contract — it is an undecidable one. There is no
implementation that satisfies both: either `is_authoritative_now("B")` is `True`
(`TERM-6`) or it is `False` (`CARR-21`).

```text
SATISFIABILITY = FALSE
ONE_OF_THE_MUST_BE_RETIRED = TRUE
```

Given questions 1–5, the retired one is determined, not chosen:

| | precedence | disposition |
|---|---|---|
| `CARR-21` | carried from a **draft** (Q1, Q2) | lower |
| `TERM-6` | **explicitly adopted** by a later ratification (Q4, Q5) | controls |

```text
RETIRED = CARR-21
RETAINED_AS_CANONICAL = TERM-6
```

---

## 7. Is a new operator policy decision needed?

**Answer: NO.**

```text
POLICY_DECISION_OUTSTANDING = FALSE
```

The policy was already decided. `PER_RECORD` over `COMPONENT_WIDE` was the
operator's explicit selection at `BOOK6-GAP7-SUCCESSOR-CURRENTNESS-v0.1` §3,
recorded with an operator-selection field and a recorded rejected alternative.

What remained was not an open question but a **stale row** — a bookkeeping
residue of a choice already made. Resolving it requires no judgment about what
the right scope is; it requires only applying the decision that was already
made.

```text
THIS_REVIEW_MAKES_NO_NEW_POLICY = TRUE
THIS_REVIEW_SELECTS_A_SCOPE    = FALSE   (it applies the ratified one)
```

---

## 8. Does the successor preserve historical provenance?

**Answer: YES.**

v0.4 §2 records what the old case actually demanded, states that it was not
false but superseded, and refuses to re-describe it:

```text
HISTORY_DELETED                                    = FALSE
UNRELATED_CASES_RENUMBERED                         = FALSE
OLD_ROW_REINTERPRETED                              = FALSE
OLD_ROW_CLAIMED_TO_HAVE_MEANT_PER_RECORD           = FALSE
OLD_OUTCOME_STATED_PLAINLY                         = TRUE
SUPERSESSION_NARROWED_TO_ONE_POINT                 = TRUE
```

The lineage `v0.2 CURR-21 -> carried unchanged into v0.3 -> ratified at 39 ->
TERM-6 added at 40 -> superseded at v0.4` is recorded end to end, including the
honest statement that `v0.2` was never itself ratified and that the stale
outcome entered by carriage rather than adoption.

A reader can reconstruct exactly why the row existed, what it asserted, and why
it stopped being current. Nothing is erased to make the corpus look tidy.

---

## 9. Does the successor change implementation scope?

**Answer: NO.**

```text
IMPLEMENTATION_SCOPE_CHANGED = FALSE
SOURCE_CHANGE_REQUIRED       = FALSE
RUNG_3_REWORK_REQUIRED       = FALSE
```

v0.4 retires a requirement the implementation never met and does not assert. The
Rung 3 implementation at `f705007ea` was verified against the canonical
doctrine and conforms: `A` refuses at `LINEAGE_INVALID`, `B` and `C` resolve on
their own conjuncts, and no component-wide refusal exists in the resolver or the
case tests.

```text
AUTHORIZED_SCOPE_CHANGED = FALSE
BOOK_6_IMPLEMENTATION_AUTHORITY = UNCHANGED (remains TRUE, offline amendment
                                          scope only)
```

Nothing in v0.4 adds a capability, widens an authority, or permits anything the
later ratification did not already permit. It **forbids** more than it permits,
in the same direction the successor record §4.2 notes.

---

## 10. Does the implementation at f705007e already follow the newer doctrine?

**Answer: YES.**

Verified behaviourally, not by reading the test names:

```text
resolve_current("A")           -> REFUSE (LINEAGE_INVALID)
resolve_current("B")           -> RETURNS B
resolve_current("C")           -> RETURNS C
is_authoritative_now("A")      -> FALSE
is_authoritative_now("B")      -> TRUE
is_authoritative_now("C")      -> TRUE
```

The contract suite passes in full (`48 passed`) at `f705007ea`. Its `TERM-6`
test carries a docstring note that `CARR-21` stated the older component-wide
outcome and is superseded on this point — so the implementation already records
the same precedence conclusion v0.4 formalises.

```text
NO_COMPONENT_WIDE_REFUSAL_PRESENT = TRUE
RUNG_3_IMPLEMENTATION              = ALREADY COMPLIANT
IMPLEMENTATION_TRACEABILITY_EDIT_NEEDED = FALSE
```

---

## 11. Findings recorded, non-blocking

Two labelling defects surfaced during verification. Neither is a contradiction,
neither requires operator policy, and neither blocks ratification. Both are
recorded in v0.4 §3.2 and §3.3 so a future reader is not misled by either.

1. **`CARR-21` is not a ratified case-id.** Only `CARR-1` and `CARR-19` ever
   appear individually, both as range endpoints. The stale outcome was carried
   as *content* inside the lossy `CARR-1..CARR-19` relabeling, whose
   correspondence to the v0.2 `CURR-*` labels was never recorded. The
   supersession is therefore requirement-level, and the canonical case count
   remains **40** rather than falling to 39.

2. **v0.3's carried-set gloss does not add up.** *"(CURR-1..15 less CURR-7,
   plus CURR-16..23 less CURR-24)"* enumerates 22 labels against a declared 19.
   The operative ratified figure is 19 and reconciles against the ratified
   total; the gloss is non-governing shorthand.

```text
NEW_BLOCKING_FINDINGS = 0
```

---

## 12. Verdict

```text
QUESTIONS = 10
PASS      = 10
FAIL      =  0
HOLD      =  0

VERDICT                  = 10 / 10 PASS
BLOCKING                 =  0
RECOMMENDATION           = RATIFY
DECISION_ID_IF_RATIFIED  = BOOK6-GAP7-TEST-PRECEDENCE-v0.1
OPERATOR_SELECTION_IF_RATIFIED
    = RATIFY_TERM6_PER_RECORD_AS_CANONICAL_AND_SUPERSEDE_COMPONENT_WIDE_CARR21
```

Nothing in this review depends on a new policy choice, a new implementation, or
a source edit. It records that the corpus already knows the answer, and that one
row in it had not been updated to agree.

```text
IMPLEMENTATION_SOURCE_TOUCHED_BY_THIS_REVIEW = FALSE
ACCEPTED_SOURCE_TOUCHED                      = FALSE
FROZEN_BOOK_6_WORKTREE_TOUCHED               = FALSE
```