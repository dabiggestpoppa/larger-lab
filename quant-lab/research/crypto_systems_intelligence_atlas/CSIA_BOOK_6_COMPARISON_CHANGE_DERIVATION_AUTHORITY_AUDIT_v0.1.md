# CSIA — BOOK 6 COMPARISON / CHANGE DERIVATION AUTHORITY AUDIT — v0.1

> **Status:** GOVERNANCE AUDIT. Ratifies nothing. Amends no historical
> artifact in place; v0.1 and v0.2 artifacts are preserved and superseded by
> v0.3 successors.
> **Date:** 2026-10-01
> **Addresses:** external review findings `R6A-D4` (derivation methodologies
> not re-resolved in authority replay) and `R6A-D5` (coverage applicability
> source undefined), plus the boundary contract-class inconsistency.
> **Authority:** `BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE`,
> `BOOK_8_IMPLEMENTATION_AUTHORITY = FALSE`,
> `LIVE_ACQUISITION_AUTHORITY = FALSE`.

---

## 1. `R6A-D4` — derivation methodology decay is not in authority replay

### 1.1 Locations audited

| Artifact | Line | Text |
|---|---|---|
| `GRAMMAR_v0.2` | 48 | `baseline_selection_methodology_ref: REQUIRED — a cited, ratified method` |
| `GRAMMAR_v0.2` | 49–50 | `comparison_methodology_ref: REQUIRED — how baseline and comparison observations are combined` |
| `GRAMMAR_v0.2` | 294 | check 7 — `coverage_sufficiency_rule_ref, where required (resolve)` |
| `GRAMMAR_v0.2` | 349 | §7 baseline selection is methodology; both refs `REQUIRED` |
| `PLAN_v0.2` | 44–45 | both refs `REQUIRED` — no implicit baseline |
| `PRE_RAT_v0.2` | 49 | Q2 re-states both refs as `REQUIRED` |
| `PRE_RAT_v0.2` | 155, 179 | the eleven-check list; check 7 concerns the **coverage** ref only |

### 1.2 The eleven checks, as written in grammar v0.2 §4

```text
 1. ComparisonRule identity and version
 2. ComparisonRule ratification state            (registry/ledger)
 3. ComparisonRule canonical content fingerprint
 4. baseline measurement refs                     (resolve + current authority)
 5. comparison measurement refs                   (resolve + current authority)
 6. input measurement Book 2 current authority
 7. coverage_sufficiency_rule_ref, where required (resolve)
 8. coverage rule ratification + currentness      (registry/ledger)
 9. coverage scope match against this metric definition
10. measurement methodology compatibility
11. deterministic recomputation from cited inputs
```

### 1.3 Verdict

```text
DERIVATION_METHODOLOGY_DECAY_NOT_IN_AUTHORITY_REPLAY = TRUE
```

**No check re-resolves the two load-bearing refs the rule's meaning actually
depends on.** Check 10 covers *input measurement* methodology compatibility
(the methodology under which each observation was produced). Nothing covers:

- `baseline_selection_methodology_ref` — identity, version, canonical
  fingerprint, current availability/authority;
- `comparison_methodology_ref` — identity, version, canonical fingerprint,
  current availability/authority.

Those two refs determine **which observations become the baseline** and **how
baseline and comparison observations are combined** (grammar v0.2 §7). They
are, semantically, the derivation. A `ComparisonRule` whose own bytes are
unchanged can therefore remain "apparently authoritative" after either
derivation methodology is superseded, withdrawn, or loses ratification — and
the replay will not notice, because the replay never looks.

`METH-1` through `METH-5` (grammar v0.3 §7) are the required behaviours this
gap would have permitted.

### 1.4 Why the v0.2 review missed it

The v0.2 review's Q1–Q30 treated the two methodology refs as *field
requirements* — "is it required, and can it be implicit?" — and never as
*re-resolution obligations*. Q2 asked whether baseline selection could be
implicit; nothing asked whether the cited methodology could decay while the
rule kept passing. The question set inspected field **presence**, not field
**dependency**.

## 2. `R6A-D5` — coverage applicability source is undefined

### 2.1 Locations

| Artifact | Line | Text |
|---|---|---|
| `GRAMMAR_v0.2` | 60–62 | `coverage_sufficiency_rule_ref: reference to the ACCEPTED Book 6 CoverageSufficiencyRule, required when the metric class requires a coverage verdict; otherwise null` |
| `GRAMMAR_v0.2` | 294 | check 7 — `where required` — the requirement predicate is never resolved |
| `PLAN_v0.2` | 48 | "the accepted Book 6 coverage rule, when the metric class requires a verdict" |

### 2.2 Verdict

```text
COVERAGE_APPLICABILITY_AUTHORITY_UNDEFINED = TRUE
COMPARISONRULE_CAN_BYPASS_G7_BY_NULL       = TRUE
```

"required when the metric class requires a coverage verdict" names no
authority that decides *requires*. The predicate is unstated, so the field
that is supposed to be non-nullable-in-context is nullable by the rule
author's choice: set `coverage_sufficiency_rule_ref = null` and gate G7 is
simply not evaluated. The v0.2 design *claimed* to close this with
`NO RAW NUMBER → VERDICT SHORTCUT`, but that only closes the *shortcut*, not
the *waiver*. A rule that waives coverage entirely never produces a raw
number at all.

The accepted v0.2 repair went so far as to forbid a numeric threshold
*inside* the rule while leaving the rule free to declare that no coverage
check is needed. That is the same class of defect one level up: **an
unbound applicability predicate is a self-granted exemption.**

## 3. Methodology contract ownership (Phase 2 — the question that had to be
answered first)

> *"Are `baseline_selection_methodology_ref` and `comparison_methodology_ref`
> references to the accepted Book 6 `MeasurementMethodology` registry, or is
> the amendment implicitly inventing a new methodology type?"*

The accepted `MeasurementMethodology` contract
(`CSIA_BOOK_6_MEASUREMENT_GRAMMAR_v0.1.md`:244–255) is:

```text
methodology_id, version, formula, parameters, window_rule, filters,
denominator_rule, source_selection, normalization_rule, identity_rule
```

Every one of those fields describes **how to produce a measurement of a
subject**. None describes how to *relate* two measurements to each other.

### 3.1 Baseline-selection methodology → **reuse the accepted benchmark-rule
namespace; no new contract**

Accepted Book 6 already has exactly this concept, for exactly this purpose:

```text
benchmark_methodology_ref drawn from a benchmark NAMESPACE:
    PRIOR_COMPARABLE_WINDOW
    ROLLING_MEAN
    ROLLING_MEDIAN
    HISTORICAL_DISTRIBUTION
    BASELINE_EPOCH
```
(`CSIA_BOOK_6_FUNDAMENTAL_MEASUREMENT_STATE_MODELING_PLAN_v0.2.md`:121–122;
`CSIA_BOOK_6_STATE_RULE_RECONCILIATION_v0.1.md`:204, :213;
`CSIA_BOOK_6_STATE_VECTOR_DESIGN_v0.2.md`:119)

and D6M-3 already records `benchmark_rules: operator-ratified individually`
(`CSIA_OPERATOR_DECISION_LOG.md`:1121) — i.e. these are **individually
operator-ratified, versioned authority objects that already exist in
accepted doctrine**.

**Resolution:** the amendment's four candidate baseline families map onto that
accepted namespace, and `baseline_selection_methodology_ref` is defined as a
reference to a **benchmark rule in the accepted namespace**, carrying that
rule's identity, version, and canonical fingerprint.

```text
  IMMEDIATE_PRIOR_COMPARABLE  → PRIOR_COMPARABLE_WINDOW  (accepted namespace)
  PRE_EVENT_WINDOW_SUMMARY    → ROLLING_MEAN | ROLLING_MEDIAN
  MATCHED_CALENDAR_WINDOW     → HISTORICAL_DISTRIBUTION
  DECLARED_REFERENCE_PERIOD   → BASELINE_EPOCH
```

**No new contract class. No new ratification machinery.** The baseline
authority, its versioning, its individual-ratification requirement, and its
supersession semantics are all inherited from accepted D6M-3 doctrine. This
also resolves a subtle inconsistency in the earlier plan: v0.1/v0.2 invented
four baseline families as if they were the amendment's own, when accepted
Book 6 already names a benchmark namespace covering the same ground.

### 3.2 Comparison methodology → **not representable as a
`MeasurementMethodology`; embedded in the `ComparisonRule` rather than
promoted to a third class**

A comparison methodology answers "how are a baseline observation and a later
observation combined into a change". Could that be a `MeasurementMethodology`?

```text
formula / parameters   — describe how to PRODUCE a value, not how to RELATE
                         two produced values. Overloading `formula` to mean
                         "post − baseline" would CHANGE THE ACCEPTED MEANING
                         of MeasurementMethodology.formula, which is a
                         Book 2 / cross-book contract.
identity_rule          — "how subjects are counted". Not applicable.
window_rule            — the window for producing a measurement. Baseline
                         window is a different question, and already has its
                         own accepted home (the benchmark namespace).
```

So: **the accepted contract cannot carry it without changing accepted
meaning.** The operator's instruction was to surface this explicitly rather
than create a third class silently. Surfacing it, and choosing the
conservative resolution:

```text
The comparison semantics are a REQUIRED, FINGERPRINTED SEMANTIC SECTION OF
THE COMPARISONRULE ITSELF — not a separately ratified, separately versioned
object.

ComparisonRule.comparison_semantics {  (required; inside the rule's
    delta_formula_basis                 canonical fingerprint)
    direction_derivation
    zero_baseline_policy
    unit_divisibility_policy
    rounding_precision_policy
}
```

**Why this is the right resolution rather than a dodge:**

- The semantics are bound by the rule's own ratification and canonical
  fingerprint (check 3), so they cannot drift late and cannot be swapped
  under a stable identity.
- Because they are inside the fingerprint, a change to them forces a new
  rule version and a **new individual operator ratification** — which is the
  same protection a separate class would have provided.
- It keeps the amendment's contract count at exactly **2**, so the boundary's
  claim stays honest.
- It avoids a class whose entire purpose is to be referenced once, by one
  rule.

**The trade-off, stated rather than hidden:** embedding means comparison
semantics are **per-rule, not shared**. Two comparison rules that both want
"relative delta with zero-baseline fail-closed" will carry duplicate copies.
That is duplication, not risk — the copies are independently ratified and
independently fingerprinted, so they cannot silently diverge into a shared
loose reference. If the operator later wants shared, independently versioned
comparison semantics, that is a **new structural decision** requiring the
boundary to admit a third contract class. It is not decided here.

## 4. Hidden-third-contract audit (Phase 3)

The question: does the amendment actually add more than the two contract
classes it claims?

| Candidate object | Authority-bearing? | Resolution | New class? |
|---|---|---|---|
| `ComparisonRule` | yes | the amendment's class #1 | **yes (1 of 2)** |
| `ChangeObservation` | yes | the amendment's class #2 | **yes (2 of 2)** |
| baseline-selection methodology | would be — it decides which observations are the baseline | mapped to the **accepted** benchmark-rule namespace; already individually operator-ratified under D6M-3 | **no** |
| comparison methodology | would be — it decides how observations combine | embedded as a fingerprinted semantic section of `ComparisonRule`, ratified with it | **no** |
| coverage-sufficiency rule | yes | **accepted** Book 6 contract, reused unchanged | **no** |
| derivation-binding digest | it is a *digest of already-bound content*, not an independently versioned or ratifiable object | registry-side ratification binding | **no** |

```text
NEW_AUTHORITY_BEARING_CONTRACT_CLASSES = 2
  ComparisonRule
  ChangeObservation
HIDDEN_THIRD_CONTRACT = NONE (after repair)
```

Before repair the honest count was ambiguous: two "methodology refs" of
unresolved type pointed at objects that, if they carried independent identity,
versioning, ratification, supersession, and replay, would each have *been* a
contract class. v0.2 therefore claimed 2 while carrying 4 authority-bearing
objects of undetermined kind. That is now closed by §3.

**No unnecessary public contract class is created for the derivation binding**
(Phase 11): it is a registry-side digest over content that is already
individually bound, not a new public object.

## 5. Methodology binding design (Phase 4)

### 5.1 What a `ComparisonRule` ratification must bind

```text
ComparisonDerivationBinding (registry-side; not a new public contract)

  comparison_rule_id
  comparison_rule_version
  comparison_rule_canonical_fingerprint

  baseline_selection_methodology_ref      (accepted benchmark namespace)
    + its rule_id, version, canonical fingerprint
  comparison_semantics_fingerprint        (the rule's own embedded section)

  coverage_applicability_resolution_ref   (see §7 — a resolved upstream
                                           determination, never a rule choice)
  coverage_sufficiency_rule_ref           (where REQUIRED)
    + its rule_id, version, canonical fingerprint

  metric_definition_ref
    + resolved semantic content fingerprint (see §9)

  compatible_input_methodology_policy     (the allow-list, as content)
```

### 5.2 The load-bearing doctrine

```text
RULE RATIFIED AGAINST METHODOLOGY X@1
!=
RULE AUTHORIZED AGAINST DIFFERENT CONTENT UNDER X@1
```

A methodology that keeps its identity while its semantic content changes is
**not** the methodology the rule was ratified against. Content binding, not
name binding.

```text
MUTATED CONTENT UNDER A BOUND IDENTITY REJECTS
```

## 6. Extended authority replay (Phase 5)

v0.2's eleven checks extended to nineteen. Every semantic dependency the
rule's meaning depends on is re-resolved live:

```text
 1. ComparisonRule identity and version
 2. ComparisonRule operator-ratification binding
 3. ComparisonRule canonical content fingerprint
 4. baseline-selection methodology identity and version
 5. baseline-selection methodology canonical fingerprint
 6. baseline-selection methodology current availability / authority
 7. comparison semantics fingerprint (the rule's own embedded section)
 8. baseline measurement refs            (resolve + current authority)
 9. comparison measurement refs          (resolve + current authority)
10. input measurement Book 2 current authority
11. input measurement methodology compatibility
12. coverage applicability resolution     (REQUIRED | NOT_APPLICABLE |
                                            UNRESOLVED — derived upstream)
13. coverage-sufficiency rule ref         (where REQUIRED)
14. coverage-rule ratification and currentness
15. coverage scope match
16. coverage deterministic verdict
17. metric-definition semantic content match against the bound fingerprint
18. compatible input methodology policy match
19. deterministic comparison/change recomputation
```

Checks **4–6** are the `R6A-D4` repair. Checks **12** and **17** are the
`R6A-D5` and Phase-13 repairs. Checks 1–3, 8–11, 13–16, 19 carry forward
v0.2's substance unchanged.

If **any** check fails:

```text
ChangeObservation.current_authority = FALSE
Historical record remains preserved. Decay is not deletion, not rewriting.
RATIFIED THEN != AUTHORITATIVE NOW
```

## 7. Coverage applicability — owner, tri-state, no waiver (Phases 7–10)

### 7.1 The reproducer

```text
Metric M requires coverage sufficiency under accepted measurement semantics.
A ComparisonRule R for M sets  coverage_sufficiency_rule_ref = null.

v0.2 outcome: gate G7 is simply not evaluated; the comparison proceeds with no
              coverage verdict at all. Reproducer CONFIRMED.
```

### 7.2 Owner of the applicability decision

```text
COVERAGE_REQUIRED
must not be caller or rule-author discretion.
```

The applicability predicate is **derived from accepted upstream semantics**,
read from the accepted `MetricDefinition` and its bound
`MeasurementMethodology`, and resolved through a registry lookup. Precedence:

```text
1. The accepted MetricDefinition / bound MeasurementMethodology states
   coverage applicability for this metric  →  that answer is used.
2. The accepted sources carry NO applicability statement            →  UNRESOLVED.
3. A ComparisonRule may CITE the applicable coverage rule.
   It may NEVER supply, override, waive, or downgrade the answer.
```

```text
COVERAGE_APPLICABILITY_OWNER = accepted MetricDefinition / bound
                               MeasurementMethodology semantics, resolved
                               through the registry.
NOT the ComparisonRule. NOT the rule author. NOT a caller.
```

**No accepted contract is modified to make this work.** The amendment *reads*
the accepted definition; where the definition is silent, the result is
`UNRESOLVED`, and `UNRESOLVED` fails closed. The amendment does **not** add an
applicability field to `MetricDefinition` — that would be an accepted-contract
change, and silence is the safer default because it fails closed.

### 7.3 Tri-state (replacing nullable ambiguity)

```text
coverage_requirement_status ∈ { REQUIRED | NOT_APPLICABLE | UNRESOLVED }
```

| Status | Meaning | Gate G7 |
|---|---|---|
| `REQUIRED` | upstream accepted semantics demand a coverage verdict | evaluated; a missing or insufficient verdict → `NOT_COMPARABLE` |
| `UNRESOLVED` | upstream is silent | **not evaluated — comparison unavailable** (fail closed) |
| `NOT_APPLICABLE` | upstream accepted semantics state coverage is not required for this metric | skipped, with the upstream determination cited on the record |

```text
null NO LONGER EXISTS as a coverage field.
`null` previously meant both "coverage not needed" and "coverage rule
missing" — two opposite situations with one representation.

COVERAGE_REQUIRED      + no ratified rule  → COVERAGE_SUFFICIENCY_UNKNOWN
                                               → NOT_COMPARABLE
UNRESOLVED                                 → comparison unavailable
                                               (fail closed)
NOT_APPLICABLE                             → G7 skipped, upstream
                                               determination cited
```

`NOT_APPLICABLE` is never a rule-author assertion. If no upstream
determination supports it, the status is `UNRESOLVED` and the comparison is
unavailable.

### 7.4 The no-waiver invariant

```text
A ComparisonRule CANNOT downgrade

    COVERAGE_REQUIRED  →  NOT_APPLICABLE

for a metric whose accepted methodology requires coverage sufficiency.
```

`ComparisonRule.coverage_sufficiency_rule_ref` becomes a **citation** that
must agree with the resolved applicability: if the resolved status is
`REQUIRED`, a null or mismatched citation is rejected. If the resolved status
is `NOT_APPLICABLE`, the field is null *because upstream said so*, and the
record carries that determination's reference.

### 7.5 Extended coverage adversarial cases

Carried forward from v0.2: `COV-1` … `COV-8` (unchanged).
New:

| # | Setup | Required outcome |
|---|---|---|
| COV-9 | upstream says `REQUIRED`; rule sets the ref `null` | **reject** — no waiver; `COVERAGE_SUFFICIENCY_UNKNOWN` → `NOT_COMPARABLE` |
| COV-10 | upstream `UNRESOLVED` (no applicability statement) | **comparison unavailable** — fail closed; G7 not evaluated, comparison blocked |
| COV-11 | upstream `NOT_APPLICABLE` | ref `null`, G7 skipped, upstream determination cited on the record |
| COV-12 | upstream `REQUIRED` + correct ratified in-scope rule | G7 evaluated normally (then `COV-7` semantics apply) |

## 8. Derivation drift (Phase 12)

```text
RATIFIED RULE
+
CHANGED DEPENDENCY
=
NOT CURRENTLY AUTHORITATIVE

— even when the rule object itself is byte-identical.
```

Applies to: baseline-selection methodology (4–6), comparison semantics (7),
coverage authority (12–16), metric-definition semantics where versioned (17),
and input methodology compatibility policy (18).

```text
THE RULE'S OWN INTEGRITY IS NECESSARY BUT NOT SUFFICIENT.
A byte-identical rule over a changed dependency is stale, not current.
```

## 9. `MetricDefinition` semantic-binding audit (Phase 13)

The accepted `MetricDefinition` carries `metric_id` and `methodology_version`
but **no `version` field and no canonical content fingerprint**
(`CSIA_BOOK_6_MEASUREMENT_GRAMMAR_v0.1.md`:111–127).

```text
AUDIT RESULT = GAP IN THE ACCEPTED CONTRACT

metric_definition_ref ALONE BINDS metric_id — A NAME, NOT CONTENT.
A comparison rule ratified against one metric definition could silently
follow later changed semantics under the same loose ref.
```

The instruction was: *"If accepted Book 6 already guarantees immutable
identity/content binding, record PASS and do not duplicate machinery."* It
does **not** — there is no such guarantee at the `MetricDefinition` level.
Recording `PASS` would be false.

**Resolution — bind at ratification without modifying the accepted class:**

```text
The rule's ratification binding records the RESOLVED SEMANTIC CONTENT
FINGERPRINT of the metric definition as it stands at ratification time
(check 17 re-resolves it at use time).

This ADDS NO FIELD to MetricDefinition and changes no accepted contract.
It binds existing content inside the amendment's own registry record.
```

The honest characterisation: the amendment **mitigates** a gap in an accepted
contract by content-binding through its own ratification record, rather than
duplicating a versioning mechanism that `MetricDefinition` lacks. If the
operator later wants first-class `MetricDefinition` versioning, that is a
separate amendment to Book 6, not something this comparison amendment
should smuggle in.

## 10. Amendment boundary consistency (Phase 14)

`CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_BOUNDARY_v0.1.md` is internally
inconsistent:

```text
line 22:  "a single new contract class: a comparison / change layer"
line 35:  AMENDMENT WIDTH = NARROW, SINGLE CONTRACT CLASS
line 189: | New contract classes added | 2 (ComparisonRule, ChangeObservation) |
```

Correct target, now that §4 has settled the question:

```text
NEW CONTRACT CLASSES = 2
  ComparisonRule
  ChangeObservation
```

The historical boundary v0.1 is **not edited**; a successor
`CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_BOUNDARY_v0.2.md` records the
correction and the derivation-binding findings.

## 11. Summary of this round

```text
DEFECTS_FOUND                 = 3
  R6A-D4  derivation methodology decay not in authority replay   (v0.2)
  R6A-D5  coverage applicability source undefined / waiver path   (v0.2)
  BOUNDARY contract-class count internally inconsistent           (v0.1)
AMBIGUITY_RESOLVED            = 1
  methodology contract ownership (Phase 2/3 question)
  baseline-selection → accepted benchmark namespace (no new class)
  comparison          → embedded fingerprinted section of ComparisonRule
  metric-definition   → content-bound at ratification (no accepted-class change)
REPAIRS_SPECIFIED_IN          = grammar v0.3, plan v0.3, seam v0.3,
                                boundary v0.2, pre-ratification review v0.3
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE (unchanged)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE (unchanged)
```

---

*End of audit. Findings are specified; nothing is implemented or ratified.*
