# CSIA — BOOK 6 COMPARISON / CHANGE GRAMMAR — v0.2

> **Status:** PLANNING / GOVERNANCE ONLY. Defines grammar and field-level
> contract shape. Implements nothing. Ratifies nothing.
> **Date:** 2026-10-01
> **Successor to:** `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.1.md`
> (**preserved unmodified**, now `SUPERSEDED`).
> **Repairs:** `R6A-D1` (embedded coverage sufficiency), `R6A-D2`
> (self-ratified derived record), D6M-3 governance-scope bleed. Full audit in
> `CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_RECONCILIATION_v0.1.md`.
> **Authority under:** `D7N-7 = A`; amendment boundary v0.1.
> **Deferred records:** 0 canonical `ComparisonRule`,
> **0 canonical `CoverageSufficiencyRule`**, 0 canonical `ChangeObservation`.

---

## 0. Repair delta from v0.1

```text
REMOVED  ComparisonRule.coverage_requirements: "minimum comparable coverage"
REMOVED  ComparisonRule.status as an authority-bearing RATIFIED value
REMOVED  ChangeObservation.status ∈ {DRAFT | RATIFIED | SUPERSEDED}
REMOVED  the "exactly as for StateRule (D6M-3 = A)" authority implication

ADDED    ComparisonRule.coverage_sufficiency_rule_ref
ADDED    ComparisonRule.coverage_scope_requirements  (structural only)
ADDED    ComparisonRule registry/ledger ratification model
ADDED    ChangeObservation.construction_status / record_state / current_authority
ADDED    the eleven-check authority re-resolution boundary
ADDED    COMPARISON_RULE_RATIFICATION_AUTHORITY = OPERATOR_ONLY, established by
         this amendment using a D6M-3-CONSISTENT pattern (authority not inherited)
```

The five-way separation of v0.1 §1 is unchanged and carried forward.

```text
MEASUREMENT != COMPARISON != CHANGE OBSERVATION != STATE != RESPONSE LINK
```

## 1. `ComparisonRule` v0.2 (planned contract)

```text
ComparisonRule {
  comparison_rule_id:                 stable identifier
  version:                            integer; supersession, never mutation

  metric_definition_ref:              the metric this rule compares (required)
  baseline_selection_methodology_ref: REQUIRED — a cited, ratified method
  comparison_methodology_ref:         REQUIRED — how baseline and comparison
                                       observations are combined
  compatible_methodology_refs:        explicit allow-list; NEVER a wildcard

  unit_requirements:                  required unit / dimensional class
  denominator_requirements:           required denominator semantics
  cohort_requirements:                required cohort definition, where relevant
  window_compatibility:               required window class and comparability rule
  missingness_requirements:           permitted missingness state

  ── COVERAGE (repaired — no numeric threshold lives here) ──
  coverage_sufficiency_rule_ref:      reference to the ACCEPTED Book 6
                                       CoverageSufficiencyRule, required when
                                       the metric class requires a coverage
                                       verdict; otherwise explicitly null
  coverage_scope_requirements:        STRUCTURAL scope only: which coverage
                                       dimensions (population / period / cohort
                                       / window) and which rule scope must
                                       apply. Contains NO numeric minimum.

  output_semantics:                   which output fields this rule may populate
  valid_time:                         bitemporal (valid_from / valid_to)
  observed_at:                        knowledge time

  registration_state:                 REGISTERED_UNRATIFIED | WITHDRAWN
                                       (NOT authority-bearing)
  supersedes:                         previous version, when applicable
  canonical_fingerprint:              fingerprint over all semantic fields
}
```

### 1.1 Prohibited fields (v0.2)

```text
PROHIBITED  minimum_coverage / minimum_comparable_coverage (any numeric
            sufficiency parameter on a ComparisonRule)
PROHIBITED  any coverage floor, percentage, or cutoff on this object
PROHIBITED  a self-declared status value that grants ratification
PROHIBITED  free-string comparison authority, aliases, substring matching
PROHIBITED  a second coverage-rule contract
```

The numeric threshold, if one is ever used, lives **inside the separately
ratified `CoverageSufficiencyRule`** — which is accepted Book 6 doctrine and
is not re-created here.

### 1.2 Registry / ratification model (repaired)

```text
REGISTRATION
!=
RATIFICATION

A ComparisonRule is REGISTERED. Ratification is an operator act recorded in
the ratification registry / ledger, bound to:
    rule id + version + canonical content fingerprint

OBJECT STATUS IS NOT AUTHORITY
  — registration_state and any lifecycle field describe the object's
    construction, never its authority. A forged value grants nothing.

MUTATED CONTENT UNDER A BOUND IDENTITY REJECTS
  — any change to a semantic field changes the canonical fingerprint and
    requires a new version.

SUPERSESSION DOES NOT INHERIT
  — v2 does not inherit v1's ratification, and a v1-cited comparison does
    not silently run under v2. Callers re-resolve current authority at use.

NO SELF-AUTHORIZATION
  — a caller may not create the rule it then invokes.

AT BOOTSTRAP:
  COMPARISON_RULES_RATIFIED          = 0
  COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
  No rule ships canonically active.
```

### 1.3 Governance authority source (repaired)

```text
COMPARISON_RULE_RATIFICATION_AUTHORITY = OPERATOR_ONLY

established BY THIS AMENDMENT as a new Book 6 governance rule, using a
governance pattern CONSISTENT WITH D6M-3 (centralized operator ratification,
no delegation, no bulk ratification, no automatic ratification).

D6M-3 DOES NOT grant, extend, or lend this authority. D6M-3 governs
StateRules. No authority is inherited from it. The pattern is borrowed; the
authority is established here.
```

## 2. Coverage doctrine (restored)

### 2.1 Binding law

```text
COVERAGE_OBSERVATION
!=
COVERAGE_SUFFICIENCY_RULE
```

A `ComparisonRule` may specify that coverage must be assessed, which coverage
dimensions are relevant, and which rule scope is required. It may **not**
define numeric sufficiency.

### 2.2 The required authority chain

```text
1. CoverageObservation              a measurement plus its basis. NOT a verdict.
2. Coverage rule applies            scope match: this rule, this metric
                                     definition, these coverage dimensions.
3. Coverage rule ratified/current   resolved from registry/ledger, never from
                                     the rule object's own status field.
4. Sufficiency verdict              SUFFICIENT | INSUFFICIENT, produced by
                                     deterministic replay of the ratified rule.
5. ComparisonRule may pass gate G7  only on a SUFFICIENT verdict obtained
                                     through steps 1–4.
```

```text
NO RAW NUMBER → VERDICT SHORTCUT
Coverage 0.99 with no ratified, in-scope, current rule yields
  COVERAGE_SUFFICIENCY_UNKNOWN → NOT_COMPARABLE, never "sufficient".
NO GLOBAL FLOOR — there is no default coverage threshold, now or later,
  absent a separately ratified global floor rule.
```

### 2.3 Zero-rule bootstrap consequence

```text
CANONICAL_COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
CANONICAL_COMPARISON_RULES_RATIFIED          = 0

⇒ A ComparisonRule whose metric class requires a coverage verdict is UNUSABLE
  until such a coverage rule is separately ratified.

COMPARISON_RULE_RATIFICATION
!=
COVERAGE_RULE_RATIFICATION
```

Correct fail-closed behaviour. The amendment does not auto-ratify coverage
rules, does not ship a default, and does not relax the gate.

### 2.4 Coverage adversarial cases

| # | Setup | Required outcome |
|---|---|---|
| COV-1 | coverage 0.79; no ratified coverage rule | **unavailable** — `NOT_COMPARABLE` / `COVERAGE_SUFFICIENCY_UNKNOWN` |
| COV-2 | coverage 0.99; no ratified rule, sufficiency required | **still unavailable** — a high raw number is not a verdict |
| COV-3 | fake / non-resolving rule ref | **reject** — fails closed |
| COV-4 | registered but unratified coverage rule | **reject** — registration ≠ ratification |
| COV-5 | ratified rule scoped to a different metric | **reject** — scope mismatch |
| COV-6 | ratified, in-scope rule replays INSUFFICIENT | `NOT_COMPARABLE` with explicit coverage failure |
| COV-7 | ratified, in-scope rule replays SUFFICIENT | gate G7 may pass (G1–G6, G8, G9 still apply) |
| COV-8 | a ratified coverage rule later superseded | current comparison authority **decays**; historical record preserved |

## 3. `ChangeObservation` v0.2 (planned contract)

```text
ChangeObservation {
  change_observation_id:           stable identifier
  subject_ref:                     the subject the change is about
  axis:                            MEASUREMENT_CHANGE (Book 6 does not know
                                    USAGE or CAPITAL as semantic axes; those
                                    are Book 7's labels over a generic change)
  metric_definition_ref:           required
  comparison_rule_ref:             REQUIRED — rule id + version + fingerprint
  baseline_measurement_refs:       one or more; non-empty
  comparison_measurement_refs:     one or more; non-empty
  absolute_delta:                  present only where defined
  relative_delta:                  present only where defined
  change_kind:                     INCREASE | DECREASE | NO_CHANGE |
                                    CHANGE_UNDEFINED | NOT_COMPARABLE |
                                    INSUFFICIENT_DATA
  unit:                            unit of the emitted deltas
  source_measurement_refs:         full set of underlying observation refs
  measurement_methodology_refs:    methodologies of the underlying observations
  coverage_observation:            a NUMBER + BASIS (NOT a verdict)
  coverage_sufficiency_ref:        the rule ref used, when required
  coverage_verdict:                SUFFICIENT | INSUFFICIENT | UNKNOWN, as
                                    produced by §2.2 — never self-declared
  missingness:                     missingness state of the inputs
  comparability_status:            COMPARABLE | NOT_COMPARABLE
  valid_time:                      bitemporal; the change's valid interval
  observed_at:                     knowledge time

  ── LIFECYCLE (repaired) ──
  construction_status:             CONSTRUCTED   (workflow marker only)
  record_state:                    CURRENT | SUPERSEDED | WITHDRAWN |
                                    INVALIDATED  (record lifecycle, NOT a
                                    Book 2 ClaimState, NOT authority)
  current_authority:               TRUE | FALSE  (DERIVED at use time by §4;
                                    never asserted by the record)
}
```

### 3.1 `RATIFIED` is removed from the derived-record vocabulary

```text
DERIVED RECORD
!=
RATIFICATION OBJECT

A ChangeObservation is never independently operator-ratified. Its usable
authority derives from §4. A caller constructing a record — with any field
value whatsoever — grants no authority.
```

### 3.2 Invariants

```text
CO-1  NOT_A_BOOK2_CLAIM — no claim-store write, no promotion path, no
      epistemic authority. A Book 6-local derived record.
CO-2  NO_EVENT_SEMANTICS — no narrative, action, response, window, or causality
      field exists.
CO-3  NO_GOODNESS — no materiality, significance, health, merit, or
      recommendation field.
CO-4  DERIVABLE — every emitted value is reproducible from the cited refs and
      the cited rule version. A non-reproducible value is a defect.
CO-5  FAIL_CLOSED — missing, incomparable, or undefined inputs yield an
      explicit change_kind with numeric fields absent. Absent is never zero.
CO-6  IMMUTABLE_HISTORY — a corrected comparison is a NEW ChangeObservation
      (or a new rule version plus new record); prior records are superseded,
      never overwritten.
CO-7  NOT_A_STATE — never becomes a StateDimension, a FundamentalStateVector
      component, or any state output.
CO-8  NOT_SELF_AUTHORIZING — record_state = CURRENT does not confer authority;
      current_authority is recomputed at use time.
CO-9  NO_COVERAGE_VERDICT_SELF_DECLARATION — coverage_verdict is the replayed
      result of a ratified rule, never an asserted value.
```

## 4. Authority replay (eleven checks)

A `ChangeObservation` is usable only when the engine can re-resolve **all**:

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

If **any** check fails:

```text
ChangeObservation.current_authority = FALSE

Historical record remains preserved. Authority decay is not deletion and not
rewriting.

RATIFIED THEN
!=
AUTHORITATIVE NOW
```

## 5. Rule vs record authority — the four separations

```text
RULE RATIFIED
!=
CHANGE EXISTS

CHANGE RECORD EXISTS
!=
CURRENTLY AUTHORITATIVE

CHANGE RECORD SELF-STATUS
!=
AUTHORITY

COMPARISON_RULE_RATIFIED
!=
COVERAGE_RULE_RATIFIED
```

## 6. Change-authority adversarial cases

| # | Attack | Required outcome |
|---|---|---|
| CHG-1 | caller constructs `ChangeObservation(status="RATIFIED")` | grants **no** authority — the field no longer exists; any analogous assertion is ignored |
| CHG-2 | valid historical record; its `ComparisonRule` later superseded | current authority **fails**; historical record preserved |
| CHG-3 | input measurement later loses Book 2 current authority | current authority **fails** |
| CHG-4 | required coverage rule loses ratification / currentness | current authority **fails** where required |
| CHG-5 | caller mutates `change_kind` | deterministic replay detects the mismatch; record rejected |
| CHG-6 | caller mutates `absolute_delta` | deterministic replay rejects; recomputed value governs |
| CHG-7 | caller swaps a baseline ref | deterministic replay rejects; binding mismatch |
| CHG-8 | caller swaps the `ComparisonRule` version | binding mismatch rejects; the cited version governs |

## 7. Baseline selection (carried from v0.1, unchanged)

Baseline selection **is** methodology. `baseline_selection_methodology_ref` and
`selection_methodology_ref` are both `REQUIRED`. Four candidate families —
`IMMEDIATE_PRIOR_COMPARABLE`, `PRE_EVENT_WINDOW_SUMMARY`,
`MATCHED_CALENDAR_WINDOW`, `DECLARED_REFERENCE_PERIOD` — with **no universal
default**. `BASELINE_UNAVAILABLE` is a first-class outcome, never a substituted
value. Book 6 receives the requested valid-time window as *context* and never
learns why.

## 8. Comparability gates (G7 repaired)

| # | Gate | Failure outcome |
|---|---|---|
| G1 | metric definition identity compatible | `NOT_COMPARABLE` |
| G2 | measurement methodology in the rule's allow-list | `NOT_COMPARABLE` |
| G3 | unit / dimensional class compatible | `NOT_COMPARABLE` |
| G4 | denominator semantics compatible | `NOT_COMPARABLE` |
| G5 | cohort definition compatible | `NOT_COMPARABLE` |
| G6 | window class compatible under the rule | `NOT_COMPARABLE` |
| **G7** | **coverage verdict obtained via §2.2 and SUFFICIENT** (repaired; v0.1 tested against the rule's own embedded minimum) | `NOT_COMPARABLE` |
| G8 | missingness within permitted states | `NOT_COMPARABLE` |
| G9 | valid temporal ordering | `NOT_COMPARABLE` |

```text
COMPARABLE != CHANGED — passing all gates authorises a comparison; it does not
  assert that any change exists.
```

## 9. Change semantics and numeric delta (carried from v0.1, unchanged)

```text
INCREASE | DECREASE | NO_CHANGE | CHANGE_UNDEFINED | NOT_COMPARABLE |
INSUFFICIENT_DATA

PROHIBITED  MATERIAL_CHANGE  SIGNIFICANT_CHANGE  GOOD_CHANGE  BAD_CHANGE
            HEALTHY_CHANGE   ADOPTION_SUCCESS_CHANGE  IMPROVING  DETERIORATING

absolute_delta = comparison_value - baseline_value
relative_delta = (comparison_value - baseline_value) / baseline_value
```

Zero baseline → `absolute_delta` may be emitted, `relative_delta` **absent —
fail closed** (never 0 / inf / NaN). Missing baseline, missing post data,
incompatible unit, invalid coverage / missingness / temporal order → numeric
fields absent. No hidden currency conversion. Absent field ≠ 0.

## 10. Methodology sensitivity (carried from v0.1, unchanged)

```text
MS-1  Parallel records PRESERVED
MS-2  NEVER AVERAGED
MS-3  NEVER SILENTLY SELECTED
MS-4  DISAGREEMENT IS VISIBLE
MS-5  CONSUMERS MUST CITE the exact record and rule relied upon
```

## 11. Ownership boundary (carried from v0.1, unchanged)

```text
Book 6 owns:  measurement; comparison; comparability truth; coverage
              sufficiency verdicts; baseline selection methodology; numeric
              delta; direction derivation; measurement normalization (D6M-2)
Book 7 owns:  event identity; action identity; response-window declaration;
              the descriptive linkage from a CURRENTLY AUTHORITATIVE
              ChangeObservation to an action
Neither owns: causal inference; materiality; health; investment merit
```

---

*End of grammar v0.2. v0.1 preserved unmodified and superseded. Nothing here is
implemented or ratified; canonical counts remain zero.*
