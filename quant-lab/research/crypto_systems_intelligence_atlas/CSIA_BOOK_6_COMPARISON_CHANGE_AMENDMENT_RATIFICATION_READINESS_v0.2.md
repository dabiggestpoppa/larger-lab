# CSIA — BOOK 6 COMPARISON / CHANGE AMENDMENT RATIFICATION READINESS — v0.2

> **Status:** INDEPENDENT RED-TEAM REVIEW. Ratifies nothing. Authorizes
> nothing. Does not redesign v0.3.
> **Date:** 2026-10-01
> **Subject:** amendment plan v0.3 (unchanged) and its governing contracts.
> **Successor to:** `..._RATIFICATION_READINESS_v0.1.md` (HOLD, preserved
> unmodified).
> **Method:** re-runs the full independent structural audit — 14 surfaces,
> not a re-run of the question checklist — then asks whether `AC-17`/`Q41` and
> `AC-18`/`Q42` fixed the *known instance* or cover the *whole class*.

---

## Verdict

```text
SURFACES_AUDITED                    = 14
NEW_UNASKED_STRUCTURAL_DEFECTS      = 0    ← closure SUCCEEDED
NEW_DESIGN_DEFECTS_FOUND            = 11 fields (2 classes)
RATIFICATION_READINESS              = HOLD
EVERY_HISTORICAL_DEFECT_HAS_GENERAL_CLASS_COVERAGE = TRUE
```

**The question-set closure worked; the design did not survive it.** Both
required conditions for PASS were checked: `NEW_UNASKED_STRUCTURAL_DEFECTS`
is `0` — the two previously unasked classes are now covered and no *new*
class surfaced. But `NEW_DESIGN_DEFECTS_FOUND` is **11**, because closing the
questions made them able to see defects the Q1–Q40 set structurally could not.
Per the operator's Phase 13 rule — *"If ANY are nonzero: HOLD"* — the verdict
is `HOLD`.

---

## 1–14. Structural surfaces

Each re-audited independently of Q1–Q42.

| # | Surface | Verdict | Note |
|---|---|---|---|
| 1 | authority roots | PASS | Book 2; operator registry; accepted metric semantics; benchmark namespace; coverage rules. No circularity, no unowned root. |
| 2 | external dependencies | PASS | all 19 replay checks live; every dependency re-resolved. |
| 3 | mutable / superseding refs | PASS | no bare name whose content may drift. |
| 4 | hidden thresholds | **FAIL** | `rounding_precision_policy` can express "below X ⇒ NO_CHANGE" (F-1). |
| 5 | hidden defaults | PASS | `UNRESOLVED`/absent baseline/binding all fail closed. |
| 6 | self-ratification | PASS | no object confers authority by self-declaration. |
| 7 | nullable multi-meaning fields | **FAIL** | 6 ambiguous fields (F-2, F-3, F-4 ×2, F-5 ×2). |
| 8 | ownership bleed | PASS | seam RL-10/RL-11; applicability owned upstream. |
| 9 | contract-class count | PASS | 2, audited not asserted. |
| 10 | historical / current distinction | PASS | decay preserves history; `RATIFIED THEN != AUTHORITATIVE NOW`. |
| 11 | upstream / downstream write paths | PASS | no reverse channel; no Book 2/3/4/5 write. |
| 12 | anti-score firewall | **FAIL** | reachable via `rounding_precision_policy` (a significance threshold by another name). |
| 13 | rule-author policy parameters | **FAIL** | 5 of 14 have open value domains (F-1). |
| 14 | field-absence semantics | **FAIL** | same 6 fields as surface 7, audited from the absence-semantics angle; the seam's "optional" quoted fields are silent about values the source record always carries. |

```text
SURFACES_CLEAN  = 10
SURFACES_FAILED = 4   (4, 7, 12, 13, 14 → 4 distinct surfaces: 4, 7, 12, 13;
                        14 restates 7 from the seam side)
```

Surfaces **4, 7, 12, 13, 14** are the exact surfaces `D-A` and `D-B` were
abstracted from. That is the expected result of closing those classes: the
previously clean surfaces now report the defects those classes name.

---

## Class-coverage question 1

> *Did `AC-17` / Q41 merely fix the known instance, or does it cover the
> whole class?*

**It covers the whole class — and that is precisely why the plan is on hold.**

`AC-17` states the rule for *every* nullable field in *every* contract in the
amendment, and requires an explicit discriminator wherever absence is
conditioned. It does not name the six offending fields; the audit found them
by applying the class rule. The class coverage is therefore genuine:

```text
QUESTIONS_ASKED_ABOUT_THE_INSTANCE  = Q35 (coverage_sufficiency_rule_ref)
QUESTIONS_ASKED_ABOUT_THE_CLASS     = Q41 (every nullable field)
FIELDS_THE_CLASS_QUESTION_CAUGHT   = 6
FIELDS_THE_INSTANCE_QUESTION_CAUGHT = 1
```

Had `AC-17` been written as "the coverage ref must be discriminated" — the
instance — the other five would have survived. It was written as a class, and
the class paid for itself immediately.

## Class-coverage question 2

> *Did `AC-18` / Q42 merely fix named policies, or does it cover future policy
> fields generically?*

**Generically, via `AC-18a` — but `AC-18a` is stated as a requirement the v0.3
contracts do not yet satisfy.**

```text
AC-18   no policy parameter may act as authority            (principle)
AC-18a  every policy parameter must be a closed enum or typed policy object,
        with a declared semantic for every value, and permissive values
        removed from the domain                                       (mechanism)
```

`AC-18a` is the generic mechanism: it binds any current or future
rule-author-settable parameter, not just the five named ones. A sixth policy
field added in a later revision is covered automatically.

**The honest observation:** `AC-18a` is a *requirement the artifacts fail*, not
a *property the artifacts have*. The closure defined the bar; v0.3 does not
clear it. The five repairs in closure §8 are what would clear it.

---

## Question-set meta check (Phase 14)

Every historical defect mapped to a **general** class now present in Q1–Q42.

| historical defect | general class | question |
|---|---|---|
| **R6A-D1** embedded coverage threshold in `ComparisonRule` | **policy/hidden-threshold class** — a rule-author-settable parameter acting as a sufficiency verdict | Q42 (+ Q21 as the instance) |
| **R6A-D2** `ChangeObservation` self-declared `RATIFIED` | **self-authority class** — an object conferring authority on itself | Q26, Q6 |
| **R6A-D4** derivation methodology decay not re-resolved | **external-dependency / mutable-ref class** — a cited dependency whose authority was never re-resolved | Q31–Q34, Q39 |
| **R6A-D5** nullable coverage waiver | **nullable-single-meaning class** + **applicability-authority class** | Q41 (class), Q35–Q38 (instance) |
| **boundary** single-vs-two contract class count | **contract-count honesty class** — a structural claim asserted rather than audited | Q40 |

```text
EVERY_HISTORICAL_DEFECT_HAS_GENERAL_CLASS_COVERAGE = TRUE
```

No defect is mapped only to an instance-specific question. The two classes
`D-A` and `D-B` were themselves the generalisations of D5 and D1 respectively,
and both have since found further instances of their own class — which is the
strongest available evidence that the generalisation was the right one.

---

## Verdict conditions

```text
Condition                                    Required  Actual   Result
42 / 42 PASS                                     42      40    FAIL
NEW_UNASKED_STRUCTURAL_DEFECTS = 0                0       0    PASS
NEW_DESIGN_DEFECTS_FOUND = 0                      0      11    FAIL
EVERY_HISTORICAL_DEFECT_HAS_GENERAL_CLASS =     TRUE    TRUE    PASS
```

```text
RATIFICATION_READINESS = HOLD
AMENDMENT_PLAN         = HOLD
```

Three of four conditions pass. The two failures are the operative ones: the
plan is not design-clean, and the checklist correctly reports it.

---

## Consolidated state

```text
BOOK_6                              = FROZEN_ACCEPTED (unchanged)
BOOK_6_AMENDMENT_REQUIRED           = TRUE
BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN = v0.3 HOLD
PRE_RATIFICATION_REVIEW             = v0.4 — 40 / 42 PASS
QUESTIONSET_CLOSURE_v0.1            = AC-17 + AC-18 defined; 11 instances found
RATIFICATION_READINESS              = HOLD
NEW_UNASKED_STRUCTURAL_DEFECTS      = 0
NEW_DESIGN_DEFECTS_FOUND            = 11 (2 classes)
EVERY_HISTORICAL_DEFECT_HAS_GENERAL_CLASS_COVERAGE = TRUE
COMPARISON_RULES_RATIFIED           = 0 canonical
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0 canonical
CHANGE_OBSERVATION_CANONICAL_COUNT  = 0 canonical
BOOK_6_IMPLEMENTATION_AUTHORITY     = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY     = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY     = FALSE
LIVE_ACQUISITION_AUTHORITY          = FALSE
D2_6                                = IN_FORCE
D6M_5                               = OPEN_DEFERRED
BOOK_7_PLAN                        = READY_PENDING_BOOK6_COMPARISON_AMENDMENT
```

---

*End of readiness v0.2. Holds the plan. Ratifies nothing; authorizes nothing.*
