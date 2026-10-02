# CSIA — BOOK 6 COMPARISON / CHANGE GRAMMAR — v0.3

> **Status:** PLANNING / GOVERNANCE ONLY. Grammar and field-level contract
> shape. Implements nothing. Ratifies nothing.
> **Date:** 2026-10-01
> **Successor to:** `CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.2.md`
> (**preserved unmodified**, now `SUPERSEDED`). v0.1 also preserved.
> **Repairs:** `R6A-D4` (derivation methodology decay not in authority
> replay), `R6A-D5` (coverage applicability source undefined).
> **Audit of record:** `CSIA_BOOK_6_COMPARISON_CHANGE_DERIVATION_AUTHORITY_AUDIT_v0.1.md`
> **Authority under:** `D7N-7 = A`; boundary v0.2.
> **Deferred records:** 0 canonical `ComparisonRule`,
> **0 canonical coverage-sufficiency rules**, 0 canonical benchmark rules,
> 0 canonical `ChangeObservation`.

---

## 0. Repair delta from v0.2

```text
RESOLVED  baseline_selection_methodology_ref now names a type:
            an ACCEPTED Book 6 benchmark rule (benchmark namespace), with
            identity + version + canonical fingerprint, individually
            operator-ratified under D6M-3
RESOLVED  comparison_methodology_ref REMOVED as an external object; the
            semantics are now a required fingerprinted section OF the
            ComparisonRule (comparison_semantics), so no third contract class
            and no late-bound derivation

ADDED     ComparisonRule.comparison_semantics  (required; inside the
            rule's canonical fingerprint)
ADDED     coverage_requirement_status ∈ {REQUIRED | NOT_APPLICABLE |
            UNRESOLVED} — DERIVED from accepted upstream semantics, never a
            rule-author choice
REMOVED   the nullable coverage_sufficiency_rule_ref-with-implicit-condition
            pattern; null no longer means both "not needed" and "rule
            missing"
ADDED     ComparisonDerivationBinding (registry-side ratification binding
            over all external semantic dependencies)
EXTENDED  authority replay from 11 checks to 19
EXTENDED  coverage adversarial cases COV-9 .. COV-12
ADDED     methodology supersession cases METH-1 .. METH-5

UNCHANGED the five-way separation:
          MEASUREMENT != COMPARISON != CHANGE OBSERVATION != STATE !=
          RESPONSE LINK
```

## 1. `ComparisonRule` v0.3 (planned contract)

```text
ComparisonRule {
  comparison_rule_id:                 stable identifier
  version:                            integer; supersession, never mutation

  metric_definition_ref:              the metric this rule compares (required)
    + metric_definition_semantic_fingerprint  (bound at ratification — §9)

  ── DERIVATION (both now precisely typed) ──
  baseline_selection_methodology_ref:  REQUIRED — an ACCEPTED Book 6 benchmark
                                       rule from the benchmark NAMESPACE
                                       (PRIOR_COMPARABLE_WINDOW |
                                        ROLLING_MEAN | ROLLING_MEDIAN |
                                        HISTORICAL_DISTRIBUTION |
                                        BASELINE_EPOCH), with that rule's
                                       identity, version, and canonical
                                       fingerprint. Individually
                                       operator-ratified under D6M-3.

  comparison_semantics:               REQUIRED semantic section, INSIDE the
                                       rule's canonical fingerprint:
    delta_formula_basis               e.g. post − baseline; (post − baseline)
                                       / baseline
    direction_derivation              how INCREASE / DECREASE are derived
    zero_baseline_policy              REQUIRED; fail-closed for relative
    unit_divisibility_policy          when a relative delta is defined
    rounding_precision_policy         declared, never implicit

  compatible_methodology_refs:        explicit allow-list of input measurement
                                       methodologies; NEVER a wildcard
  unit_requirements:                  required unit / dimensional class
  denominator_requirements:           required denominator semantics
  cohort_requirements:                required cohort definition, where relevant
  window_compatibility:               required window class and comparability rule
  missingness_requirements:           permitted missingness state

  ── COVERAGE (applicability is derived, never chosen) ──
  coverage_sufficiency_rule_ref:      CITATION of the applicable accepted
                                       coverage-sufficiency rule. Required when
                                       the derived coverage_requirement_status
                                       is REQUIRED. Null only when the derived
                                       status is NOT_APPLICABLE, and the
                                       upstream determination's ref must then
                                       be recorded. A null or mismatched
                                       citation when the derived status is
                                       REQUIRED is REJECTED.
  coverage_requirement_status:        REQUIRED, DERIVED upstream:
                                       REQUIRED | NOT_APPLICABLE | UNRESOLVED
  coverage_applicability_source_ref:  the accepted determination this status
                                       was read from

  output_semantics:                   which output fields this rule may populate
  valid_time:                         bitemporal (valid_from / valid_to)
  observed_at:                        knowledge time

  registration_state:                 REGISTERED_UNRATIFIED | WITHDRAWN
                                       (NOT authority-bearing)
  supersedes:                         previous version, when applicable
  canonical_fingerprint:              fingerprint over ALL semantic fields,
                                       including comparison_semantics
}
```

### 1.1 Prohibited fields and patterns (v0.3)

```text
PROHIBITED  minimum_coverage / minimum_comparable_coverage (any numeric
            sufficiency parameter on a ComparisonRule)
PROHIBITED  any coverage floor, percentage, or cutoff on this object
PROHIBITED  a self-declared status value that grants ratification
PROHIBITED  free-string comparison authority, aliases, substring matching
PROHIBITED  a second coverage-rule contract
PROHIBITED  an EXTERNAL comparison_methodology_ref (the semantics are inside
            this object's fingerprint; a late-bound external ref is exactly
            the R6A-D4 defect)
PROHIBITED  setting coverage_requirement_status as a rule-author choice — the
            field records a derived upstream determination, and a value that
            contradicts the source is rejected
```

### 1.2 Baseline families map onto the accepted namespace

```text
IMMEDIATE_PRIOR_COMPARABLE  → PRIOR_COMPARABLE_WINDOW
PRE_EVENT_WINDOW_SUMMARY    → ROLLING_MEAN | ROLLING_MEDIAN
MATCHED_CALENDAR_WINDOW     → HISTORICAL_DISTRIBUTION
DECLARED_REFERENCE_PERIOD   → BASELINE_EPOCH
```

The amendment introduces no baseline authority of its own; it cites the
accepted benchmark namespace, which D6M-3 already requires to be
individually operator-ratified. Bootstrap canonical benchmark-rule count in
the comparison context is **0**.

### 1.3 Registry / ratification model (carried, unchanged)

```text
REGISTRATION != RATIFICATION
OBJECT STATUS IS NOT AUTHORITY
MUTATED CONTENT UNDER A BOUND IDENTITY REJECTS
SUPERSESSION DOES NOT INHERIT
NO SELF-AUTHORIZATION
AT BOOTSTRAP: COMPARISON_RULES_RATIFIED = 0; no rule ships canonically active.
```

### 1.4 Governance authority source (carried, unchanged)

```text
COMPARISON_RULE_RATIFICATION_AUTHORITY = OPERATOR_ONLY

established BY THIS AMENDMENT, using a governance pattern CONSISTENT WITH
D6M-3. D6M-3 does not grant, extend, or lend this authority — it governs
StateRules. The pattern is borrowed; the authority is created here.
```

## 2. `ComparisonDerivationBinding` (registry-side; not a new public contract)

A ratification is not merely "rule id + version + rule fingerprint". It binds
every external semantic dependency the rule's meaning depends on:

```text
ComparisonDerivationBinding {
  comparison_rule_id + version + canonical_fingerprint

  baseline_selection_methodology:  id + version + canonical_fingerprint
  comparison_semantics_fingerprint: (the rule's own embedded section)

  coverage_applicability_resolution_ref
  coverage_sufficiency_rule:        id + version + canonical_fingerprint
                                     (where REQUIRED)

  metric_definition_ref + resolved semantic content fingerprint
  compatible_input_methodology_policy (the allow-list, as content)
}
```

```text
RULE RATIFIED AGAINST METHODOLOGY X@1
!=
RULE AUTHORIZED AGAINST DIFFERENT CONTENT UNDER X@1
```

This binding lives in the **registry ratification record**, not as a new
public contract class. It is a digest over content that is already
individually bound; it is not itself independently versioned or ratifiable.

## 3. `ChangeObservation` v0.3

Field set carried from v0.2 §3, with the derivation-binding refs added:

```text
ChangeObservation {
  change_observation_id
  subject_ref
  axis:                            MEASUREMENT_CHANGE
  metric_definition_ref + metric_definition_semantic_fingerprint
  comparison_rule_ref:             id + version + fingerprint
  derivation_binding_ref:          the registry binding relied upon
  baseline_selection_methodology_ref  (accepted benchmark rule; cited)
  comparison_measurement_refs      baseline_measurement_refs
  absolute_delta / relative_delta  present only where defined
  change_kind:                     INCREASE | DECREASE | NO_CHANGE |
                                    CHANGE_UNDEFINED | NOT_COMPARABLE |
                                    INSUFFICIENT_DATA
  unit
  source_measurement_refs
  measurement_methodology_refs
  coverage_observation:            a NUMBER + BASIS (NOT a verdict)
  coverage_requirement_status:     the derived tri-state
  coverage_verdict:                SUFFICIENT | INSUFFICIENT | UNKNOWN, as
                                    replayed from a ratified rule — never
                                    self-declared
  missingness
  comparability_status
  valid_time / observed_at

  construction_status:             CONSTRUCTED (workflow only)
  record_state:                    CURRENT | SUPERSEDED | WITHDRAWN |
                                    INVALIDATED  (record lifecycle; NOT a
                                    Book 2 ClaimState; NOT authority)
  current_authority:               TRUE | FALSE  (DERIVED by §4; never
                                    asserted)
}
```

### 3.1 Invariants (v0.2 set, unchanged, plus)

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
CO-10 NO_LATE_BOUND_DERIVATION — the derivation binding recorded here must
      still re-resolve at use time (§4), or current_authority is FALSE
```

## 4. Authority replay — nineteen checks (v0.3)

A `ChangeObservation` is usable only when the engine can re-resolve **all**:

```text
 1. ComparisonRule identity and version
 2. ComparisonRule operator-ratification binding
 3. ComparisonRule canonical content fingerprint
 4. baseline-selection methodology identity and version
 5. baseline-selection methodology canonical fingerprint
 6. baseline-selection methodology current availability / authority
 7. comparison semantics fingerprint (the rule's own embedded section)
 8. baseline measurement refs              (resolve + current authority)
 9. comparison measurement refs            (resolve + current authority)
10. input measurement Book 2 current authority
11. input measurement methodology compatibility
12. coverage applicability resolution       (REQUIRED | NOT_APPLICABLE |
                                              UNRESOLVED — derived upstream)
13. coverage-sufficiency rule ref           (where REQUIRED)
14. coverage-rule ratification and currentness
15. coverage scope match
16. coverage deterministic verdict
17. metric-definition semantic content match against the bound fingerprint
18. compatible input methodology policy match
19. deterministic comparison/change recomputation
```

Checks **4–6** are the `R6A-D4` repair. Check **12** is the `R6A-D5` repair.
Check **17** closes the `MetricDefinition` content-binding gap. The rest
carry forward v0.2's substance.

If **any** check fails:

```text
ChangeObservation.current_authority = FALSE
Historical record remains preserved. Decay is not deletion, not rewriting.
RATIFIED THEN != AUTHORITATIVE NOW
```

### 4.1 Derivation drift (Phase 12)

```text
RATIFIED RULE
+
CHANGED DEPENDENCY
=
NOT CURRENTLY AUTHORITATIVE

— even when the rule object itself is byte-identical.
```

Applies to: baseline-selection methodology (4–6), comparison semantics (7),
coverage authority (12–16), metric-definition semantics (17), and input
methodology policy (18).

```text
THE RULE'S OWN INTEGRITY IS NECESSARY BUT NOT SUFFICIENT.
A byte-identical rule over a changed dependency is stale, not current.
```

## 5. Methodology supersession cases (`METH-1` … `METH-5`)

| # | Setup | Required outcome |
|---|---|---|
| METH-1 | rule `R@1` bound to benchmark `A@1`; `A@2` later exists | `R@1` remains bound to `A@1` — **no auto-follow** |
| METH-2 | `A@1` becomes unavailable / superseded | current `ChangeObservation` authority **FALSE**; history preserved |
| METH-3 | comparison `X@1` loses authority / currentness | current authority **FALSE** (check 7 and the binding) |
| METH-4 | caller supplies the same methodology identity with mutated content | **reject** via canonical fingerprint (checks 5, 6) |
| METH-5 | rule `v2` changes the baseline methodology | `v1` ratification does **not** inherit; new operator ratification required |

METH-1 and METH-2 are the direct R6A-D4 reproducers: under v0.2's eleven
checks, neither would have been detected, because nothing re-resolved the
methodology.

## 6. Coverage applicability (Phase 8–10)

### 6.1 Owner and tri-state

```text
COVERAGE_APPLICABILITY_OWNER = accepted MetricDefinition / bound
                               MeasurementMethodology semantics, resolved
                               through the registry.

NOT the ComparisonRule. NOT the rule author. NOT a caller.
```

```text
coverage_requirement_status ∈ { REQUIRED | NOT_APPLICABLE | UNRESOLVED }
```

| Status | Source | Gate G7 |
|---|---|---|
| `REQUIRED` | upstream accepted semantics state coverage is required | evaluated; missing/insufficient verdict → `NOT_COMPARABLE` |
| `UNRESOLVED` | upstream sources carry **no** applicability statement | **not evaluated — comparison unavailable** (fail closed) |
| `NOT_APPLICABLE` | upstream accepted semantics state coverage is not required | skipped, with the upstream determination's ref cited on the record |

The amendment does **not** add an applicability field to `MetricDefinition`;
that would change an accepted contract. It reads the accepted definition, and
where the definition is silent the result is `UNRESOLVED`, which fails closed.

### 6.2 No waiver

```text
A ComparisonRule CANNOT downgrade COVERAGE_REQUIRED → NOT_APPLICABLE.
```

`coverage_sufficiency_rule_ref` is a **citation** that must agree with the
derived status. Null or mismatched when the status is `REQUIRED` → rejected.
Null when the status is `NOT_APPLICABLE` only because upstream said so, and
the determination's ref is recorded.

```text
`null` NO LONGER carries two meanings. It never meant "coverage not needed"
and "coverage rule missing" at the same time.
```

### 6.3 Coverage adversarial cases (v0.3 set)

Carried: `COV-1` … `COV-8` (unchanged). New:

| # | Setup | Required outcome |
|---|---|---|
| COV-9 | upstream `REQUIRED`; rule sets the ref `null` | **reject** — no waiver; `COVERAGE_SUFFICIENCY_UNKNOWN` → `NOT_COMPARABLE` |
| COV-10 | upstream `UNRESOLVED` | **comparison unavailable** — fail closed |
| COV-11 | upstream `NOT_APPLICABLE` | ref `null`, G7 skipped, upstream determination cited |
| COV-12 | upstream `REQUIRED` + correct ratified in-scope rule | G7 evaluated normally (`COV-7` semantics) |

## 7. Comparability gates (G7 rebuilt on derived applicability)

| # | Gate | Failure outcome |
|---|---|---|
| G1 | metric definition identity compatible | `NOT_COMPARABLE` |
| G2 | input measurement methodology in the rule's allow-list | `NOT_COMPARABLE` |
| G3 | unit / dimensional class compatible | `NOT_COMPARABLE` |
| G4 | denominator semantics compatible | `NOT_COMPARABLE` |
| G5 | cohort definition compatible | `NOT_COMPARABLE` |
| G6 | window class compatible under the rule | `NOT_COMPARABLE` |
| **G7** | coverage: resolved status is `NOT_APPLICABLE` **with a cited upstream determination** → skip; `REQUIRED` → verdict SUFFICIENT via ratified in-scope rule; `UNRESOLVED` → **comparison unavailable** | `NOT_COMPARABLE` |
| G8 | missingness within permitted states | `NOT_COMPARABLE` |
| G9 | valid temporal ordering | `NOT_COMPARABLE` |

```text
COMPARABLE != CHANGED — passing all gates authorises a comparison; it does not
assert that any change exists.
```

## 8. Change-authority adversarial cases (carried)

`CHG-1` … `CHG-8` unchanged from v0.2. Each is additionally subject to the
nineteen-check replay: `CHG-2` (rule superseded) and `CHG-4` (coverage
authority decays) are now joined by `METH-2` / `METH-3` for the derivation
methodologies specifically.

## 9. `MetricDefinition` binding (§9 of the audit)

The accepted `MetricDefinition` has no `version` field and no canonical
content fingerprint. `metric_definition_ref` alone binds a **name, not
content**.

```text
RESOLUTION (audit §9): the rule's ratification binding records the metric
definition's RESOLVED SEMANTIC CONTENT FINGERPRINT as it stands at
ratification; check 17 re-resolves it at use time.

ADDS NO FIELD to MetricDefinition and changes no accepted contract.
```

This **mitigates** a gap in an accepted contract by content-binding through
the amendment's own registry record. It does not add versioning machinery
`MetricDefinition` lacks; that would be a separate amendment, out of scope
here (boundary v0.2 §4).

## 10. Separations (carried, plus the new ones)

```text
RULE RATIFIED           != CHANGE EXISTS
CHANGE RECORD EXISTS     != CURRENTLY AUTHORITATIVE
CHANGE RECORD SELF-STATUS != AUTHORITY
COMPARISON_RULE_RATIFIED != COVERAGE_RULE_RATIFIED
RATIFIED RULE + CHANGED DEPENDENCY != CURRENTLY AUTHORITATIVE
COVERAGE_REQUIRED        != RULE_AUTHOR_DISCRETION
```

## 11. Ownership boundary (carried)

```text
Book 6 owns:  measurement; comparison; comparability truth; coverage
              sufficiency verdicts; baseline selection (via the accepted
              benchmark namespace); numeric delta; direction derivation;
              measurement normalization (D6M-2)
Book 7 owns:  event identity; action identity; response-window declaration;
              the descriptive linkage from a CURRENTLY AUTHORITATIVE
              ChangeObservation to an action
Neither owns: causal inference; materiality; health; investment merit
```

---

*End of grammar v0.3. v0.2 and v0.1 preserved unmodified and superseded.
Nothing here is implemented or ratified; canonical counts remain zero.*
