# CSIA — Book 6 Comparison Coverage Replay Binding Review v0.1

**Status:** `PRE_RATIFICATION_REVIEW`
**Date:** 2026-10-05
**Reviews:** `CSIA_BOOK_6_COMPARISON_COVERAGE_REPLAY_BINDING_CLARIFICATION_v0.1.md`
**Decision id:** none. This review records **no** operator decision.
**Grants implementation authority:** `FALSE`

**VERDICT: 12 / 12 PASS — `BLOCKING = 0`. Recommendation: RATIFY.**

---

## 0. Scope and method

Twelve questions, each answerable from verified substrate evidence or from
quotable ratified text. None is a matter of judgment.

```text
QUESTIONS = 12
PASS      = 12
FAIL      =  0
HOLD      =  0
```

The review does not ask whether the repair is *desirable*. It asks whether each
answer is already true of the corpus, so that ratifying the clarification
records something rather than inventing it.

---

## 1. Does this introduce a second coverage authority?

**NO.**

```text
AUTHORITY_OWNER = CoverageRuleRegistry   (book6_coverage_rules.py)
CHECK_14_RE_RESOLVES_THROUGH = CoverageRuleRegistry
CHECK_15_RE_RESOLVES_THROUGH = CoverageRuleRegistry
NEW_REGISTRY_INTRODUCED = NONE
```

Checks 14 and 15 both re-resolve the **named** rule through the accepted
registry. The repair adds no registry, no local mirror, and no cache.

---

## 2. Does this make numeric coverage authoritative by itself?

**NO.**

```text
NUMERIC_COVERAGE_IS_NOT_SUFFICIENCY = True   (accepted constant)
AUTHORITY = CURRENT RATIFIED RULE + ACTUAL OBSERVATION + DETERMINISTIC APPLICATION
```

`observed_fraction` is the rule's **input**, never its own verdict. The
accepted `CoverageObservation` docstring already forbids a sufficiency field on
the observation for exactly this reason, and the repair adds none. The
authority-bearing contributions remain: a currently-ratified rule, an actual
observation, and deterministic application of the rule's own
`required_fraction`.

---

## 3. Does this reuse `CoverageRuleRegistry`?

**YES.**

```text
REUSED, NOT RE_DECLARED = CoverageRuleRegistry
REUSED, NOT RE_DECLARED = CoverageSufficiencyRule
REUSED, NOT RE_DECLARED = CoverageObservation
```

Verified: all three are imported from the accepted modules. `CoverageRuleRegistry`
is the same object the state vector consults when sealing `DATA_COMPLETE`.

---

## 4. Does `ComparisonRule` already contain `coverage_sufficiency_rule_ref`?

**YES.**

```text
FIELD = ComparisonRule.coverage_sufficiency_rule_ref
REQUIRED_WHEN = coverage_requirement_status is REQUIRED
FINGERPRINTED = True   (COMPARISON_RULE_CANONICAL_FIELDS, Rung 5)
```

Declared at `book6_comparison_contracts.py:299`, required when coverage is
`REQUIRED` and forbidden otherwise, and included in the rule's canonical
fingerprint so the binding is sealed at ratification.

Amendment plan v0.3 already declares it *"a CITATION that must agree with the
derived status; null or mismatched when REQUIRED is rejected"*.

---

## 5. Does `CoverageObservation` already contain `observed_fraction`?

**YES.**

```text
FIELDS = measurement_id, observed_fraction, basis, sufficiency_rule_ref, valid_time
observed_fraction: float = Field(ge=0.0, le=1.0)
```

---

## 6. Does `CoverageSufficiencyRule` already contain `required_fraction`?

**YES.**

```text
FIELDS = rule_id, version, required_fraction, scope_metric_id, rationale, status
required_fraction: float = Field(ge=0.0, le=1.0)
```

It is declared and, before this repair, applied nowhere in the implementation.
The repair gives the field its intended use rather than adding a threshold
anywhere new — preserving the ratified `NO NUMERIC COVERAGE THRESHOLD ON THIS
OBJECT` on `ComparisonRule`.

---

## 7. Can check 16 now be recomputed without caller policy?

**YES.**

```text
observed_fraction >= required_fraction -> SUFFICIENT
observed_fraction <  required_fraction -> INSUFFICIENT
INPUTS = TWO ACCEPTED, RATIFIED-BOUND NUMBERS
FREE PARAMETER = NONE
```

Both operands are fields of accepted frozen models constrained to `[0.0, 1.0]`.
There is no epsilon, no tolerance, no rounding and no display precision, so
the replay is total and caller-free.

---

## 8. Is lexical rule-id selection removed?

**YES.**

```text
LEXICAL_COVERAGE_RULE_SELECTION = UNRATIFIED IMPLEMENTATION INVENTION
CURRENTLY_RATIFIED              = NONE  (corpus-wide search, zero occurrences)
CHECK12_SELECTS_COVERAGE_RULE   = FALSE
```

Reproduced at `92b954e5`: two separately-ratified exact-metric rules resolved
to `sorted(authorizing)[0]`. The repair makes check 12 a yes/no existence
question and moves rule selection to the operator's ratified citation.

---

## 9. Are checks 12–16 still independently falsifiable?

**YES.**

```text
12  falsifiable by removing every exact-metric rule
13  falsifiable by nulling the named ref while coverage is REQUIRED
14  falsifiable by superseding the named rule
15  falsifiable by naming a wrong-metric rule
16  falsifiable by omitting the observation or mismatching its rule ref
```

Each has a distinct input and a distinct reason string. None is derived from
another's boolean.

---

## 10. Does coverage remain downstream of baseline selection?

**YES.**

```text
ORDER = currentness -> compatibility -> baseline selection -> coverage -> verdict
COVERAGE_SELECTS_BASELINE = FALSE
```

The coverage module does not import the selector, and the replay takes the
already-resolved baseline rather than any candidate set. Enforced
structurally, not by convention.

---

## 11. Does this introduce aggregation semantics?

**NO.**

```text
AGGREGATION_OBSERVED = a single comparison of two stored scalars
MULTIPLE_OBSERVATIONS_COMBINED = NEVER
ROLLING / MEAN / MEDIAN / DISTRIBUTION = ABSENT
```

Check 16 compares one observation's fraction against one rule's threshold. It
never combines observations, never weights them, and never summarises a set.
That is not aggregation.

---

## 12. Does this introduce a third authority class?

**NO.**

```text
NEW_PUBLIC_AUTHORITY_BEARING_CLASSES = 0
COMPARISON_RULE + CHANGEOBSERVATION   = STILL EXACTLY 2
```

The repair introduces no new `Book6FrozenModel`. Its intermediate results are
frozen dataclasses carrying verdicts, not contracts — the same shape the
Rung 7 candidate already used and that the Rung 4 scope test pins.

---

## 13. Findings recorded, non-blocking

**The two defects this clarification exists to correct are defects of the
Rung 7 candidate implementation, not of the ratified corpus.** They are
recorded as findings at `92b954e5` and corrected forward. Neither required a
change of doctrine, because the corpus already answered both questions:

```text
CALLER_CALLBACK_CAN_ASSERT_COVERAGE_VERDICT = TRUE   (implementation)
CALLER_CALLBACK_IS_AUTHORITY_SAFE           = FALSE  (implementation)
LEXICAL_COVERAGE_RULE_SELECTION            = UNRATIFIED IMPLEMENTATION INVENTION

RATIFIED_ANSWER_TO_BOTH                    = ALREADY EXISTED IN THE CORPUS
NEW_BLOCKING_FINDINGS                      = 0
```

No prior ratification is edited. No accepted source is edited. Rung 7's commit
`92b954e5` is retained as history; the repair is an append-only successor.

---

## 14. Verdict

```text
QUESTIONS = 12
PASS      = 12
FAIL      =  0
HOLD      =  0

VERDICT                 = 12 / 12 PASS
BLOCKING                =  0
RECOMMENDATION          = RATIFY
DECISION_ID_IF_RATIFIED = BOOK6-COVERAGE-REPLAY-BINDING-v0.1
OPERATOR_SELECTION_IF_RATIFIED
    = RATIFY_NAMED_COVERAGE_RULE_AND_OBSERVATION_REPLAY
```

```text
DOCTRINE_CHANGED      = FALSE
AUTHORITY_CLASS_ADDED = FALSE
RUNG7_REPAIR_REQUIRED = TRUE
```

```text
IMPLEMENTATION_SOURCE_TOUCHED_BY_THIS_REVIEW = FALSE
ACCEPTED_SOURCE_TOUCHED                      = FALSE
FROZEN_BOOK_6_WORKTREE_TOUCHED               = FALSE
```