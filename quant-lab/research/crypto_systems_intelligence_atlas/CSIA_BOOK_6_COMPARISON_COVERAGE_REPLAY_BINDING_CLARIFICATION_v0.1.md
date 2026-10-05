# CSIA — Book 6 Comparison Coverage Replay Binding Clarification v0.1

**Status:** `RATIFIED`
**Record type:** governance clarification
**Date:** 2026-10-05
**Decision id:** `BOOK6-COVERAGE-REPLAY-BINDING-v0.1`
**Operator selection:** `RATIFY_NAMED_COVERAGE_RULE_AND_OBSERVATION_REPLAY`
**Scope:** `BOOK 6 COVERAGE REPLAY BINDING ONLY`
**Grants implementation authority:** `FALSE` (already held; unchanged)

```text
DOCTRINE_CHANGED          = FALSE
AUTHORITY_CLASS_ADDED     = FALSE
RUNG7_REPAIR_REQUIRED     = TRUE
BOOK6_IMPLEMENTATION_AUTHORITY = REMAINS TRUE
```

---

## 0. What this record is

This record resolves **how already-existing fields participate in deterministic
replay**. Every field it binds already exists and is already ratified. It adds
no field, no class, no registry, and no authority.

```text
CHANGES GAP_3                       = FALSE
CHANGES GAP_4                       = FALSE
CHANGES COVERAGE AUTHORITY          = FALSE
CHANGES COMPARISONRULE CONTRACT COUNT = FALSE (still exactly 2)
CHANGES COVERAGERULE_REGISTRY AUTHORITY = FALSE
ADDED SCHEMA                        = NONE
ADDED AUTHORITY CLASS               = NONE
```

It was prompted by two defects in the Rung 7 candidate implementation at
`92b954e5`. Both are recorded below as findings, not as doctrine.

---

## 1. The substrate this clarification binds to

Verified against the accepted implementation:

```text
CoverageObservation (book6_definitions.py:192)
  measurement_id, observed_fraction, basis,
  sufficiency_rule_ref, valid_time
  observed_fraction in [0.0, 1.0]

CoverageSufficiencyRule (book6_definitions.py:238)
  rule_id, version, required_fraction, scope_metric_id, rationale, status
  required_fraction in [0.0, 1.0]
  status may NOT be self-set to RATIFIED

CoverageRuleRegistry (book6_coverage_rules.py)
  authority owner; registration != ratification
  authorize() checks registered + current ratification + exact metric scope

NUMERIC_COVERAGE_IS_NOT_SUFFICIENCY = TRUE
```

That last constant is load-bearing and is read here in its precise sense: a
bare number is not authority. It does **not** forbid evaluating an observed
fraction under a ratified rule — that evaluation is the rule's whole purpose,
and `required_fraction` exists on the rule precisely so the comparison happens
against ratified content rather than a threshold invented on a comparison rule.

```text
AUTHORITY = CURRENT RATIFIED RULE
          + ACTUAL COVERAGE OBSERVATION
          + DETERMINISTIC APPLICATION OF THAT RULE
```

---

## 2. Finding A — caller-supplied verdict was authority

Rung 7 accepted `coverage_verdict_of: Callable[[str, str], CoverageVerdict]`
and consumed its return value as check 16's deterministic verdict.

Reproduced at `92b954e5`:

```text
CALLER_CALLBACK_CAN_ASSERT_COVERAGE_VERDICT = TRUE
CALLER_CALLBACK_IS_AUTHORITY_SAFE           = FALSE
```

A callback returning `SUFFICIENT` produced a passing check 16 and a
`SUFFICIENT` verdict with:

```text
actual CoverageObservation evaluated : NONE
observed_fraction read               : NONE
required_fraction read               : NONE
```

Two callbacks over identical registry state produced `SUFFICIENT` and
`INSUFFICIENT` respectively. The caller, not the corpus, decided.

This violates the ratified contract that a `CoverageVerdict` is *always
replayed from a ratified rule* and *never self-declared*. A callback return
value is precisely a self-declaration.

```text
CALLER_SUPPLIED_COVERAGE_VERDICT  = PROHIBITED
CALLER_SUPPLIED_COVERAGE_CALLBACK = PROHIBITED
```

## 3. Finding B — lexical rule selection was an invention

Rung 7 resolved applicability by collecting all authorizing rules and taking
`sorted(authorizing)[0]`.

Reproduced at `92b954e5` with two separately-ratified exact-metric rules:

```text
registered in-scope rules : ['aaa-first', 'zzz-last']
chosen by applicability   : 'aaa-first'
```

A corpus-wide search found **zero** occurrences of any rule preferring a
lexically smallest coverage rule id.

```text
LEXICAL_COVERAGE_RULE_SELECTION = UNRATIFIED IMPLEMENTATION INVENTION
```

It also defeated the ratified field's stated purpose. Amendment plan v0.3
already declares `coverage_sufficiency_rule_ref` to be *"a CITATION that must
agree with the derived status; null or mismatched when REQUIRED is rejected"* —
a citation is something the operator-ratified `ComparisonRule` names, not
something a registry orders into existence.

---

## 4. The binding — checks 12 through 16

### Check 12 — applicability

Asks one question only:

```text
Does ANY current, ratified, exact-metric CoverageSufficiencyRule exist?

  YES -> coverage_requirement_status = REQUIRED
  NO  -> coverage_requirement_status = UNRESOLVED
         reason = NO_UPSTREAM_DETERMINATION_EXISTS
```

```text
CHECK12_SELECTS_COVERAGE_RULE = FALSE
ABSENCE_OF_COVERAGE_RULE != NOT_APPLICABLE      (unchanged)
```

Check 12 may enumerate candidates for diagnostics. It may not convert their
order into authority.

### Check 13 — the named binding

When check 12 says `REQUIRED`, `ComparisonRule.coverage_sufficiency_rule_ref`
must be present. This is the rule the operator-ratified `ComparisonRule` binds
for this comparison.

```text
RULE_BINDING_SOURCE = ComparisonRule.coverage_sufficiency_rule_ref
NO REGISTRY_ORDER_TIE_BREAK
```

### Check 14 — ratification and currency

Re-resolve the **named** rule through `CoverageRuleRegistry`. It must be
registered, carry a live ratification, and be at its current version.

```text
FAILURE = coverage-rule ratification/currentness failure
```

### Check 15 — scope

The **named** rule must have `scope_metric_id` equal to the exact compared
metric. No alternative rule may silently replace it.

```text
FAILURE = coverage scope mismatch
```

### Check 16 — the deterministic verdict

Check 16 consumes an **actual `CoverageObservation`**, never a caller-supplied
verdict. Required validations, in order:

```text
 1. a CoverageObservation exists for this comparison
 2. observation.sufficiency_rule_ref == the named coverage_sufficiency_rule_ref
 3. the named rule passed checks 14 and 15
 4. the observation applies to the comparison input under accepted coverage
    semantics
```

Then, deterministically:

```text
observed_fraction >= required_fraction  ->  SUFFICIENT
observed_fraction <  required_fraction  ->  INSUFFICIENT
```

No epsilon, no tolerance, no rounding, no display precision. The comparison is
on the stored values the accepted models already constrain to `[0.0, 1.0]`.

```text
THIS IS NOT NUMERIC COVERAGE ASSERTING SUFFICIENCY BY ITSELF
THE NUMBER IS THE RULE'S INPUT, NOT THE RULE
```

---

## 5. Multiple current rules

Several ratified exact-metric rules may legitimately exist. That is not a
defect and not an ambiguity to resolve automatically.

```text
check 12 still yields REQUIRED
ComparisonRule.coverage_sufficiency_rule_ref chooses which
that binding lives INSIDE the ratified ComparisonRule fingerprint
```

```text
MULTIPLE_RULES_REQUIRE_LEXICAL_SELECTION = FALSE
MULTIPLE_RULES_INVALID                   = FALSE
NAMED_RULE_BINDING_CONTROLS               = TRUE
NO HIDDEN AUTOMATIC PREFERENCE AMONG VALID RULES = TRUE
```

Two rules disagreeing about sufficiency is a **substantive** difference between
two ratified rules. It is resolved by which one the operator bound into the
`ComparisonRule`, never by which identifier sorts first.

---

## 6. The distinction this repair must not collapse

```text
"check 16 successfully recomputed INSUFFICIENT"
    !=
"check 16 failed"
```

Check 16 is a **replay check**. It succeeds when it faithfully recomputes the
rule's verdict, whatever that verdict is. An `INSUFFICIENT` determination is a
successful replay, and check 19 then maps that explicit determination to
`NOT_COMPARABLE`.

Check 16 *fails* only when the replay could not be performed — no observation,
a mismatched rule ref, unratified or out-of-scope named rule. That failure is an
absence of basis and routes to `UNRESOLVED`.

```text
CHECK16_SUCCEEDED_WITH_INSUFFICIENT -> NOT_COMPARABLE
CHECK16_FAILED                     -> UNRESOLVED
```

Conflating these two would reintroduce exactly the GAP-4 collapse the
amendment exists to prevent.

---

## 7. What this record does not do

```text
NEW NUMERIC AGGREGATION SEMANTICS   = NONE
NEW COVERAGERULE_REGISTRY AUTHORITY  = NONE
NEW RULE-SELECTION POLICY BEYOND THE EXPLICIT COMPARISONRULE BINDING = NONE
NEW COVERAGE OBSERVATION SCHEMA     = NONE   (accepted type reused as-is)
NEW AUTHORITY-BEARING CLASS         = NONE
CLASS_C                            = UNTOUCHED
BOOK_7                             = TOUCHED = FALSE
LIVE_ACQUISITION                   = FALSE
GAP_3 / GAP_4 REOPENED              = FALSE
```

The `CoverageSufficiencyRule` and `CoverageObservation` types are **reused**
from the accepted substrate, not re-declared. Comparison happens against
`required_fraction` on the ratified rule; no threshold is added to any
comparison object, preserving the ratified `NO NUMERIC COVERAGE THRESHOLD ON
THIS OBJECT`.

---

## 8. Authority flags

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = TRUE   (offline amendment scope only, unchanged)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## 9. Cross-references

```text
CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.3.md  the citation field's stated meaning
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.6.md         canonical check list 12-16, 19
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_RECORD_v0.1.md
CSIA_BOOK_6_COMPARISON_COVERAGE_REPLAY_BINDING_REVIEW_v0.1.md
book6_definitions.py                                   CoverageObservation, CoverageSufficiencyRule
book6_coverage_rules.py                                CoverageRuleRegistry authority
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```

---

**Status:** `RATIFIED`. Deterministic replay binds to the named rule and an
actual observation. Two implementation inventions are recorded as defects.