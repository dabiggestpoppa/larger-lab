# CSIA — BOOK 6 COMPARISON / CHANGE GRAMMAR — v0.4

> **Status:** PLANNING / GOVERNANCE ONLY. Grammar and contract shape.
> Implements nothing. Ratifies nothing.
> **Date:** 2026-10-01
> **Successor to:** `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.3.md`
> (**preserved unmodified**, now `SUPERSEDED`). v0.1 and v0.2 also preserved.
> **Repairs:** Class A (nullable/absent multi-meaning) and Class B
> (rule-author policy parameters with open or authority-bearing value
> domains), as exposed by `AC-17` / `AC-18` in
> `CSIA_BOOK_6_COMPARISON_CHANGE_QUESTIONSET_CLOSURE_v0.1.md`.
> **Authority under:** `D7N-7 = A`; boundary v0.2.
> **Deferred records:** 0 canonical `ComparisonRule`, 0 canonical
> coverage-sufficiency rules, 0 canonical benchmark rules, 0 canonical
> `ChangeObservation`.

---

## 0. Repair delta from v0.3

The governing decision of this revision is stated first, because it is the
substantive change and everything else follows from it:

```text
DERIVED SEMANTIC
>
RULE-AUTHOR POLICY CHOICE

whenever the derivation is unambiguous from accepted inputs.
```

Five v0.3 policy surfaces are **not** converted into enums. Four are
**deleted outright** and one is reduced to a closed, non-permissive operator
vocabulary. An enum is only created where choice is genuinely necessary —
and none of these five is a genuine choice, because in each case the correct
behaviour is determined by arithmetic, by the unit contract, or by the
display layer, none of which a rule author may influence.

```text
REMOVED  direction_derivation        (was an open policy string)
          → FIXED: direction is the sign of the canonical UNROUNDED
            ABSOLUTE_DELTA
REMOVED  zero_baseline_policy        (was an open policy string)
          → FIXED: relative delta UNDEFINED at baseline 0; never 0, inf,
            NaN, capped, or percentage
REMOVED  unit_divisibility_policy    (was an open policy string)
          → DERIVED from the accepted typed unit contract
REMOVED  rounding_precision_policy   (was inside the canonical fingerprint)
          → presentation-only metadata, outside every authority check
REDUCED  delta_formula_basis         (was "e.g. post - baseline", free text)
          → CLOSED operator vocabulary: ABSOLUTE_DELTA | RELATIVE_DELTA

ADDED    coverage_applicability_source_ref semantics   (R-2)
ADDED    coverage_observation_state discriminator       (R-3)
ADDED    supersedes_ref single-meaning rule             (R-5)
ADDED    valid_to single-meaning rule                   (R-5)
ADDED    NO_TOLERANCE / NO_MATERIALITY firewall
```

The five-way separation is unchanged:
`MEASUREMENT != COMPARISON != CHANGE OBSERVATION != STATE != RESPONSE LINK`.

---

## 1. The five repairs, as canonical law

### 1.1 `delta_formula_basis` → closed operator vocabulary

```text
DELTA OPERATORS (the complete, closed set)

ABSOLUTE_DELTA  = comparison_value - baseline_value
RELATIVE_DELTA  = (comparison_value - baseline_value) / baseline_value
                 where semantically valid
```

```text
NO FREE-FORM FORMULA
NO EXPRESSION LANGUAGE
NO CALLER-SUPPLIED FORMULA
NO "(post-baseline)*1000" OR ANY ARITHMETIC VARIANT
NO EXCEPTIONS IN THIS AMENDMENT

A future new operator requires a NEW CONTRACT VERSION under amendment
governance — never a string in this field.
```

Both operators are **canonical and always defined by the arithmetic**; a
`ComparisonRule` selects which is the *reported primary* form, and may not
manufacture one where the arithmetic does not define it. Selecting
`RELATIVE_DELTA` where the baseline is zero does not produce a value — it
produces the explicit `CHANGE_UNDEFINED` state.

`delta_formula_basis` was `e.g. post − baseline; (post − baseline) / baseline`
in v0.3, which is an illustration, not a contract. Adversarial case `POL-9`
covers the injection attempt.

### 1.2 `direction_derivation` → **REMOVED**, fixed law

```text
DIRECTION_DERIVATION_RULE = FIXED / NON-CONFIGURABLE

direction is the SIGN OF THE CANONICAL UNROUNDED ABSOLUTE_DELTA:

    absolute_delta >  0   →  INCREASE
    absolute_delta <  0   →  DECREASE
    absolute_delta == 0   →  NO_CHANGE     (exact canonical equality)
```

Direction is **not** determined by:

```text
display rounding                     (ROUNDING_AFFECTS_CHANGE_CLASSIFICATION = FALSE)
relative delta magnitude              (a negative relative delta is a DECREASE)
caller tolerance / epsilon            (no such field exists — see §1.6)
materiality threshold                 (prohibited; §1.6)
significance rule                     (prohibited; §1.6)
precision cutoff                      (prohibited; §1.5)
```

There is no `direction_derivation` field in v0.4. A rule author cannot express
a direction rule, because there is nothing to express it in.

### 1.3 `zero_baseline_policy` → **REMOVED**, fixed fail-closed

```text
ZERO_BASELINE_POLICY = FIXED_FAIL_CLOSED

baseline == 0:
    absolute_delta  — computed normally where the unit supports subtraction
    relative_delta  — UNDEFINED / ABSENT

NEVER:  0 · infinity · NaN · capped value · 100% · percentage convention
NO RULE-AUTHOR ALTERNATIVE EXISTS
```

The v0.3 phrasing — "REQUIRED; fail-closed for relative" — *described*
fail-closed without *foreclosing* alternatives. v0.4 forecloses them by
having no field. Adversarial case `POL-10`.

### 1.4 `unit_divisibility_policy` → **REMOVED**, derived

```text
UNIT_ARITHMETIC_VALIDITY = DERIVED_FROM_UNIT_CONTRACT

Whether an arithmetic operation is valid derives from:
    typed unit compatibility
    dimensional class
    accepted unit semantics

A ComparisonRule may CITE unit requirements (which dimensional class this
comparison operates over).
It may NOT redefine mathematics for those units.
```

`POL-11` covers a rule attempting to authorize incompatible units: the unit
contract governs and the attempt is rejected.

### 1.5 `rounding_precision_policy` → **REMOVED** from authority

```text
ROUNDING_AFFECTS_CHANGE_CLASSIFICATION = FALSE
DISPLAY_ROUNDING_IS_AUTHORITY          = FALSE
```

```text
Canonical calculations use the accepted canonical numeric representation.
Direction and change_kind are derived from the UNROUNDED CANONICAL VALUE.

Rounding may exist ONLY as presentation / serialization display metadata,
recorded on the record as non-authority display metadata, and it must NEVER
alter:
    absolute_delta canonical value
    relative_delta canonical value
    INCREASE / DECREASE / NO_CHANGE
    comparability
    authority
    coverage
    materiality
```

Worked example (`POL-6`, `POL-7`):

```text
baseline = 100.000   comparison = 100.004
canonical absolute_delta = +0.004
direction  = INCREASE
change_kind = INCREASE

displayed at 2 decimals: 100.00 vs 100.00   ← appears equal
direction                 : INCREASE         ← unchanged

DISPLAYED EQUALITY
!=
MEASURED EQUALITY
```

In v0.3 the precision value was inside the rule's canonical fingerprint, so
changing it was a policy change. In v0.4 it is not authority at all: it is
metadata, changing it changes nothing, and it cannot be a threshold because
it is not consulted by any derivation.

### 1.6 Tolerance / materiality firewall

```text
NO_CHANGE
means EXACT CANONICAL EQUALITY under the comparison arithmetic.

It does NOT mean:
    change too small · immaterial change · insignificant change ·
    within tolerance · within epsilon · economically negligible
```

```text
NO_CHANGE
!=
NOT_MATERIAL_CHANGE

NO TOLERANCE FIELD EXISTS IN ComparisonRule v0.4.
NO EPSILON FIELD EXISTS.
NO MATERIALITY FIELD EXISTS.
NO SIGNIFICANCE FIELD EXISTS.
```

Any tolerance, materiality, or significance concept requires **separate
future governance** — a distinct methodology, separately operator-ratified,
exactly as a coverage-sufficiency rule is. It is not a comparison-rule
parameter. `POL-8` covers an epsilon attempt.

---

## 2. `ComparisonRule` v0.4

```text
ComparisonRule {
  comparison_rule_id:                 stable identifier
  version:                            integer; supersession, never mutation
  supersedes_ref:                     version == 1  → ABSENT (first version)
                                       version >  1  → REQUIRED (rejected if
                                       absent — NULL-8)

  metric_definition_ref:              required
  metric_definition_semantic_fingerprint:  bound at ratification

  ── DERIVATION ──
  baseline_selection_methodology_ref: REQUIRED — an ACCEPTED Book 6 benchmark
                                       rule (PRIOR_COMPARABLE_WINDOW |
                                       ROLLING_MEAN | ROLLING_MEDIAN |
                                       HISTORICAL_DISTRIBUTION |
                                       BASELINE_EPOCH) with identity,
                                       version, canonical fingerprint;
                                       individually operator-ratified (D6M-3)

  delta_operator:                     CLOSED ENUM, the complete set:
                                       ABSOLUTE_DELTA | RELATIVE_DELTA
                                       (which canonical form is reported as
                                       primary; availability is DERIVED from
                                       the arithmetic, never chosen)

  ── NOTE: v0.3's comparison_semantics SECTION IS GONE. direction_derivation,
     zero_baseline_policy, unit_divisibility_policy, and
     rounding_precision_policy no longer exist as fields. Their behaviour is
     the fixed law in §1. There is nothing for a rule author to configure.

  compatible_methodology_refs:        explicit allow-list; NEVER a wildcard
  unit_requirements:                  cites the accepted unit dimensional class
  denominator_requirements:           required denominator semantics
  cohort_requirements:                required cohort definition, where relevant
  window_compatibility:               required window class
  missingness_requirements:           permitted missingness state
  output_semantics:                   which output fields may be populated

  ── COVERAGE ──
  coverage_requirement_status:        REQUIRED, DERIVED upstream:
                                       REQUIRED | NOT_APPLICABLE | UNRESOLVED
  coverage_applicability_source_ref:  REQUIRED when status ∈ {REQUIRED,
                                       NOT_APPLICABLE}; ABSENT when status ==
                                       UNRESOLVED. Absence has EXACTLY ONE
                                       meaning: NO_UPSTREAM_DETERMINATION_
                                       EXISTS. A REQUIRED/NOT_APPLICABLE
                                       status without its source ref is
                                       INVALID (NULL-4, NULL-5).
  coverage_sufficiency_rule_ref:      CITATION of the applicable accepted rule.
                                       Required when status == REQUIRED.
                                       Rejected when null/mismatched.

  valid_time:                         bitemporal
    valid_from:                       required
    valid_to:                         ABSENT means OPEN-ENDED / STILL VALID
                                       UNTIL SUPERSEDED OR WITHDRAWN — and
                                       NOTHING ELSE (NULL-9). Never "end
                                       unknown".
  observed_at:                        knowledge time

  registration_state:                 REGISTERED_UNRATIFIED | WITHDRAWN
                                       (NOT authority-bearing)
  canonical_fingerprint:              over all semantic fields
}
```

### 2.1 Prohibited fields and patterns (v0.4)

```text
PROHIBITED  free-form / custom delta formula (closed operator set only)
PROHIBITED  epsilon, tolerance, materiality, significance fields
PROHIBITED  rounding / precision as an authority-bearing field
PROHIBITED  unit arithmetic redefinition
PROHIBITED  direction derivation as a policy choice
PROHIBITED  zero-baseline substitution policy
PROHIBITED  minimum_coverage / any numeric coverage threshold
PROHIBITED  a self-declared status value that grants ratification
PROHIBITED  an external comparison_methodology_ref
PROHIBITED  a rule-author-chosen coverage_requirement_status
```

### 2.2 Registry / governance (carried unchanged)

```text
REGISTRATION != RATIFICATION
OBJECT STATUS IS NOT AUTHORITY
COMPARISON_RULE_RATIFICATION_AUTHORITY = OPERATOR_ONLY, established BY THIS
  AMENDMENT using a D6M-3-CONSISTENT pattern; D6M-3 does not grant, extend,
  or lend this authority
MUTATED CONTENT UNDER A BOUND IDENTITY REJECTS
SUPERSESSION DOES NOT INHERIT
AT BOOTSTRAP: COMPARISON_RULES_RATIFIED = 0
```

---

## 3. `ChangeObservation` v0.4

```text
ChangeObservation {
  change_observation_id
  subject_ref
  axis:                            MEASUREMENT_CHANGE
  metric_definition_ref + metric_definition_semantic_fingerprint
  comparison_rule_ref:             id + version + fingerprint
  derivation_binding_ref:          REQUIRED
  baseline_selection_methodology_ref  (accepted benchmark rule; cited)
  baseline_measurement_refs        comparison_measurement_refs
                                    (both non-empty)

  absolute_delta:                  canonical value where the unit supports
                                    subtraction; ABSENT means
                                    NOT_COMPUTABLE (never 0)
  relative_delta:                  canonical value where defined; ABSENT means
                                    UNDEFINED (incl. zero baseline)
                                    (never 0, inf, NaN, capped)
  delta_operator:                  which canonical form is the primary report

  change_kind:                     INCREASE | DECREASE | NO_CHANGE |
                                    CHANGE_UNDEFINED | NOT_COMPARABLE |
                                    INSUFFICIENT_DATA
                                    derived from the SIGN of the canonical
                                    UNROUNDED ABSOLUTE_DELTA; never from
                                    display, precision, tolerance, or
                                    relative magnitude

  unit
  source_measurement_refs
  measurement_methodology_refs

  coverage_requirement_status:     REQUIRED — the derived tri-state
  coverage_applicability_source_ref:  mirrors the rule (R-2 semantics)
  coverage_observation_state:      REQUIRED discriminator:
                                     PRESENT | UNAVAILABLE | NOT_APPLICABLE
  coverage_observation_ref:        REQUIRED when state == PRESENT;
                                     ABSENT when UNAVAILABLE or NOT_APPLICABLE
  coverage_verdict:                SUFFICIENT | INSUFFICIENT | UNKNOWN,
                                     replayed from a ratified rule; never
                                     self-declared
  missingness
  comparability_status

  display_metadata:                PRESENTATION ONLY — e.g. display precision.
                                     NEVER consulted by any derivation, gate,
                                     fingerprint, or authority check.
                                     Changing it changes NOTHING.

  valid_time / observed_at
  construction_status:             CONSTRUCTED (workflow only)
  record_state:                    CURRENT | SUPERSEDED | WITHDRAWN |
                                    INVALIDATED (lifecycle; not a Book 2
                                    ClaimState; not authority)
  current_authority:               TRUE | FALSE (DERIVED by §5; never asserted)
}
```

### 3.1 `coverage_observation_state` (R-3) — the discriminator

```text
REQUIRED      + PRESENT        → coverage_observation_ref REQUIRED
REQUIRED      + UNAVAILABLE    → ref ABSENT; G7 CANNOT PASS
NOT_APPLICABLE                 → state = NOT_APPLICABLE; ref ABSENT
UNRESOLVED                     → comparison UNAVAILABLE before any coverage
                                 observation semantics are used
```

```text
Absence of coverage_observation_ref is read THROUGH
coverage_observation_state — never on its own. Absence alone is never read as
NOT_APPLICABLE and never as NOT_MEASURED.

NULL-1 SATISFIED: absence is not a single overloaded value; the discriminator
carries the state.
```

### 3.2 Invariants (v0.3 set, unchanged, restated)

```text
CO-1  NOT_A_BOOK2_CLAIM
CO-2  NO_EVENT_SEMANTICS
CO-3  NO_GOODNESS
CO-4  DERIVABLE — reproducible from cited refs + bound rule version
CO-5  FAIL_CLOSED
CO-6  IMMUTABLE_HISTORY — corrections supersede, never overwrite
CO-7  NOT_A_STATE
CO-8  NOT_SELF_AUTHORIZING
CO-9  NO_COVERAGE_VERDICT_SELF_DECLARATION
CO-10 NO_LATE_BOUND_DERIVATION
CO-11 NO_DISPLAY_INFLUENCE — display_metadata is never consulted by any
      derivation, comparison, coverage, or authority check
```

---

## 4. Separations (carried, plus the new arithmetic ones)

```text
RULE RATIFIED            != CHANGE EXISTS
CHANGE RECORD EXISTS      != CURRENTLY AUTHORITATIVE
CHANGE RECORD SELF-STATUS != AUTHORITY
COMPARISON_RULE_RATIFIED  != COVERAGE_RULE_RATIFIED
RATIFIED RULE + CHANGED DEPENDENCY != CURRENTLY AUTHORITATIVE
COVERAGE_REQUIRED         != RULE_AUTHOR_DISCRETION
DISPLAYED EQUALITY        != MEASURED EQUALITY
NO_CHANGE                 != NOT_MATERIAL_CHANGE
POLICY PARAMETER          != THRESHOLD AUTHORITY
```

---

## 5. Authority replay — nineteen checks (carried from v0.3)

Unchanged, and note that checks 4–7 now resolve *fixed law* rather than a
rule author's policy string, so there is nothing for a rule author to have
got wrong:

```text
 1. ComparisonRule identity and version
 2. ComparisonRule operator-ratification binding
 3. ComparisonRule canonical content fingerprint
 4. baseline-selection methodology identity and version
 5. baseline-selection methodology canonical fingerprint
 6. baseline-selection methodology current availability / authority
 7. delta_operator validity against the closed set and the arithmetic
 8. baseline measurement refs
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
19. deterministic comparison/change recomputation
```

Check 19 recomputes the delta, direction, and `change_kind` from the canonical
unrounded values. `display_metadata` is **not** an input to check 19 and is
not in check 3's fingerprint scope.

If any check fails: `current_authority = FALSE`; history preserved.

---

## 6. `AC-17` — single-meaning absence (strengthened, restated)

Carried forward in full force. Every nullable field in the amendment now has
exactly one defined meaning for absence, and where absence is conditioned, a
named discriminator carries the state.

```text
ABSENT != UNKNOWN != NOT_APPLICABLE != UNAVAILAILABLE != NOT_REQUIRED
       != UNRESOLVED != UNDEFINED != ZERO != FALSE
```

Complete inventory: closure recheck, §8 below.

## 7. `AC-18` / `AC-18a` — policy is not authority (strengthened, restated)

```text
AC-18   no rule-author-settable policy parameter may make a comparison more
        permissive, manufacture sufficiency, weaken a fail-closed gate, create
        a hidden threshold, create materiality or significance, create health
        or adoption semantics, override upstream authority, or bypass a
        separately operator-ratified rule authority

AC-18a  every rule-author-settable policy parameter must be a CLOSED ENUM or a
        TYPED POLICY OBJECT with a finite, enumerated value domain and a
        declared semantic for every value; a value domain that is open,
        example-illustrated, or free-text is INVALID

AC-18b  (added in v0.4) where the correct semantic is DERIVABLE from accepted
        inputs, the choice is REMOVED rather than enumerated. An enum is
        created only where choice is genuinely necessary.

        DERIVED SEMANTIC > RULE-AUTHOR POLICY CHOICE
```

`AC-18b` is the principle that drove v0.4: four of the five v0.3 policy
surfaces were deleted rather than closed, because in each case the correct
behaviour was already determined by arithmetic, the unit contract, or the
display layer.

---

## 8. Post-repair inventories

### 8.1 Nullable fields

```text
NULLABLE_FIELDS_RE_INVENTORIED   = 36  (all re-inventoried, not just the six)
AMBIGUOUS_NULLABLE_FIELDS        = 0
NULL-1 = PASS   NULL-2 = PASS   NULL-3 = PASS
NULL-4..NULL-9 = PASS
```

The six previously-ambiguous fields now read:

| field | v0.3 ambiguity | v0.4 |
|---|---|---|
| `coverage_applicability_source_ref` | absent = "no determination" OR "not recorded" | absent = `NO_UPSTREAM_DETERMINATION_EXISTS` **only**; `REQUIRED`/`NOT_APPLICABLE` without it is INVALID |
| `coverage_observation` | conflated not-applicable with not-measured | replaced by `coverage_observation_state` ∈ {PRESENT, UNAVAILABLE, NOT_APPLICABLE} + a ref required iff PRESENT |
| `ResponseLink.coverage_verdict_quoted` | optional → silence about a known value | **mandatory** when the source carries it |
| `ResponseLink.coverage_requirement_quoted` | same | **mandatory** when the source carries it |
| `supersedes` | first version vs unknown | `version == 1` → absent; `version > 1` → required, else rejected |
| `valid_time.valid_to` | still valid vs end unknown | absent = `OPEN_ENDED / STILL VALID UNTIL SUPERSEDED OR WITHDRAWN` **only** |

### 8.2 Policy parameters

```text
POLICY_PARAMETERS_RE_INVENTORIED  = 10
POLICY_PARAMETERS_WITH_UNGOVERNED_AUTHORITY = 0
FREE_STRING_POLICY_AUTHORITY      = 0
ARBITRARY_NUMERIC_THRESHOLD_PARAMETERS = 0
POL-1..POL-5 = PASS    POL-6..POL-11 = PASS
```

| # | parameter | status in v0.4 |
|---|---|---|
| — | `direction_derivation` | **REMOVED** (fixed law §1.2) |
| — | `zero_baseline_policy` | **REMOVED** (fixed law §1.3) |
| — | `unit_divisibility_policy` | **REMOVED** (derived §1.4) |
| — | `rounding_precision_policy` | **REMOVED** from authority (§1.5) |
| P1 | `delta_operator` | closed enum {ABSOLUTE_DELTA, RELATIVE_DELTA}; availability derived |
| P2 | `compatible_methodology_refs` | explicit allow-list, no wildcard |
| P3 | `unit_requirements` | cites the accepted unit contract; cannot redefine it |
| P4 | `denominator_requirements` | required, closed |
| P5 | `cohort_requirements` | required where relevant, closed |
| P6 | `window_compatibility` | required, closed |
| P7 | `missingness_requirements` | permitted states named, closed |
| P8 | `output_semantics` | names the populable output fields, closed |
| P9 | `compatible_input_methodology_policy` | closed |
| P10 | `coverage_applicability_resolution_ref` | cites a derived determination; not authorable |

```text
No parameter can create hidden materiality, change coverage sufficiency,
waive a gate, change direction through tolerance, override upstream
authority, or introduce custom arithmetic.
```

---

## 9. Ownership boundary (carried unchanged)

```text
Book 6 owns:  measurement; comparison; comparability truth; coverage
              sufficiency verdicts; baseline selection (accepted benchmark
              namespace); canonical delta arithmetic and direction derivation;
              measurement normalization (D6M-2)
Book 7 owns:  event identity; action identity; response-window declaration;
              the descriptive linkage from a CURRENTLY AUTHORITATIVE
              ChangeObservation to an action
Neither owns: causal inference; materiality; health; investment merit;
              display formatting
```

---

*End of grammar v0.4. v0.3 and earlier preserved unmodified. Nothing here is
implemented or ratified; canonical counts remain zero.*
