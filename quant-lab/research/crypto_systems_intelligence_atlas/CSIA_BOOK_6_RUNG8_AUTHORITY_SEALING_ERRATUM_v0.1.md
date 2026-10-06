# CSIA — Book 6 Rung 8 Authority Sealing Erratum v0.1

**Status:** `RATIFIED` (binding correction; no operator selection made or implied)
**Record type:** narrow governance erratum
**Date:** 2026-10-06
**Decision id:** none required. Every clause below restates or seals law that is
already ratified; no operator selection is made, no doctrine is created or
amended.
**Grants implementation authority:** `TRUE` (offline amendment scope only, for
the append-only repair this record specifies)
**Grants new doctrine:** `FALSE`
**Changes implementation:** `TRUE` (append-only repair on
`2838e9ba7daccc8ef2a2f41cdd7d989e6dce17b3`)
**Reopens GAP-1..GAP-6 / the operand-cardinality ratification:** `FALSE`

```text
DOCTRINE_CHANGED                        = FALSE
NEW_FIELD                               = FALSE
NEW_AUTHORITY_CLASS                     = FALSE
NEW_SELECTOR                            = FALSE
NEW_FINGERPRINT_ALGORITHM               = FALSE
IMPLEMENTATION_AUTHORITY_DEFECTS_FOUND  = 3
IMPLEMENTATION_AUTHORITY_DEFECTS_CLASS  = A (violations of ratified law, not gaps in it)
SELECTED_BASELINE_IS_ENGINE_DERIVED     = TRUE (already law; now enforced)
CALLER_SELECTED_BASELINE                = PROHIBITED
DIAGNOSTIC_REASON_TEXT_AUTHORITY        = FALSE
COMPARISON_OPERAND                      = CANONICAL_REGISTRY_RESOLUTION
RULE_METRIC_BINDING                     = EXACT
COVERAGE_STATE_MAPPING_REPAIRED         = UNRESOLVED -> UNAVAILABLE (R-3 / AC-17)
```

---

## 0. What this record is

External review identified three authority defects in the Rung 8 change
derivation (`book6_comparison_change_derivation.py`, implementation HEAD
`2838e9ba7daccc8ef2a2f41cdd7d989e6dce17b3`). Each was reproduced against the
unrepaired engine by execution, and each is a violation of law that is **already
ratified**. This record documents the reproductions, anchors each repair to its
existing ratified clause, and authorizes the append-only repair. It makes no
operator selection, creates no doctrine, adds no field, no class, no registry
and no algorithm.

Per the operator instruction, one confirmed repair target was audited first and
found to be governed by silent-but-recoverable doctrine (§6), so the erratum
proceeds rather than stops.

---

## 1. Defect A — the caller could author the selected baseline

### 1.1 Reproduction (executed against the unrepaired engine)

Fixture: candidates `obs:a` (day 5) and `obs:b` (day 3), outsider
`obs:outsider` (day 8) registered and current but **not** in the candidate set;
comparison `obs:c` (day 10, value 7.5). The ratified `PRIOR_COMPARABLE_WINDOW`
selector deterministically selects `obs:a`.

```text
derive_change_observation(..., baseline_measurement_refs=("obs:a","obs:b"),
                           selected_baseline_ref="obs:outsider", ...)

selected_baseline_measurement_ref = 'obs:outsider'
absolute_delta                    = -92.5
source_measurement_refs           = ('obs:c', 'obs:outsider')
CALLER_CAN_AUTHOR_SELECTED_BASELINE = TRUE

variant — selected_baseline_ref="obs:b" (selector would pick obs:a):
selected = 'obs:b', delta = 5.5   (engine-derivation would yield 6.5)
CURRENT_RUNG8_BASELINE_SELECTION_REPLAY = ABSENT
```

A caller could make any current same-shape observation the arithmetic operand
without the Rung 6 selector ever running.

### 1.2 The ratified law

`CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.6.md` §3.2 (Phase 13), verbatim:

```text
CALLER MAY provide:      candidate baseline refs (for offline resolution)
CALLER MAY NOT provide:  selected_baseline_ref
                         baseline_selector_result
                         baseline_is_valid
                         benchmark_rule_ref
                         benchmark_methodology_ref
```

And, in the same section:

> If an expected baseline ref is accepted for tests, the engine **recomputes and
> compares**; a mismatch **raises**, and stored authority uses the **engine**
> result.

The same law appears in grammar v0.6 §3.1 (authority replay re-resolves
selection rather than trusting a stored result) and v0.7 §3
(`BASELINE_SELECTOR_AUTHORITY = BOUND_INSIDE_COMPARISON_RULE`,
`COVERAGE_INFLUENCES_BASELINE_SELECTION = FALSE`).

### 1.3 Sealing

```text
SELECTED_BASELINE_IS_ENGINE_DERIVED     = TRUE
CALLER_SELECTED_BASELINE_AUTHORITY      = FALSE
SELECTOR_IMPLEMENTATIONS                = 1      (select_baseline, unchanged)
RUNG8_REUSES_RUNG6_SELECTOR             = TRUE
REPAIR                                  = remove selected_baseline_ref from the
                                          derivation API; the engine loads the
                                          candidate refs through the registry and
                                          invokes select_baseline() itself
```

The Rung 6 selector is reused **as-is** — same function, same ratified inputs
(`rule`, `semantic_fingerprint_of`, `is_current`, comparison observation,
candidate observations). No second selector implementation is created.

---

## 2. Defect B — coverage authority was parsed from diagnostic prose

### 2.1 Reproduction (executed against the unrepaired engine)

One valid sealed `ComparabilityVerdict`; an otherwise identical copy where only
check 16's reason text changes (`"-> SUFFICIENT"` → `"deterministically
sufficient"`), with check number, passed state, and verdict semantics unchanged:

```text
status unchanged: True | check16 passed unchanged: True
RAISED: ChangeDerivationError: comparability is COMPARABLE but the sealed Rung 7
        replay did not recompute SUFFICIENT coverage ...
RUNG8_AUTHORITY_DEPENDS_ON_DIAGNOSTIC_TEXT = TRUE
```

Changing wording-only diagnostic text changed Rung 8 semantics.

### 2.2 Why this violates ratified law

`ReplayCheck.reason` is diagnostic by construction — the Rung 7 module's own
`ReplayCheck` docstring: "One authority-replay check: its verdict, and **why**."
The corpus requires verdict semantics to be carried in structured fields:
`CoverageAuthorization` (an existing frozen value object) already carries
`applicability.requirement_status`, `observation_state`, `observation_ref` and
`verdict`. Grammar v0.4 §3.1 makes the discriminator/ref pairing a structured
fact (R-3), and grammar v0.4 §4 forbids display or prose from entering any
derivation.

### 2.3 Sealing

```text
DIAGNOSTIC_TEXT_IS_AUTHORITY            = FALSE
STRUCTURED_RUNG7_RESULT                 = ComparabilityVerdict gains an
                                          internal, frozen `coverage` field
                                          carrying the existing
                                          CoverageAuthorization
NEW_PUBLIC_AUTHORITY_BEARING_CLASS      = NONE (internal value object on an
                                          existing derived result; the
                                          contract-class audit outcome of
                                          grammar v0.7 §2.4 is unchanged)
REPLAYCHECK_REASONS_PRESERVED           = TRUE (diagnostics stay; wording is
                                          never canonical)
```

Rung 8 consumes structured fields only: requirement status, observation state,
observation ref, verdict. It never reads a reason string for a semantic
decision.

---

## 3. Defect C — rule metric binding unenforced; caller object shaped records

### 3.1 Reproduction (executed against the unrepaired engine)

```text
rule bound to 'metric.other', both operands measuring 'metric.tx':
  arithmetic ran, delta = 6.5
RULE_METRIC_BINDING_NOT_ENFORCED = TRUE

mutated caller comparison (model_copy of the canonical record, same
measurement_id, altered subject/metric/coverage ref), UNRESOLVED verdict:
refusal record carried subject_ref='subject:EVIL',
metric_definition_ref='metric.other'
CALLER_OBJECT_CAN_INFLUENCE_REFUSAL_RECORD = TRUE
```

### 3.2 The ratified law

```text
GAP-2 / 2D (grammar v0.7 §3): TEMPORAL_UNIT_COMPATIBILITY =
    SAME_METRIC_EXACT_UNIT_IDENTITY
AC-18 / AC-18a (grammar v0.6 §7): policy may not determine ... baseline
    selection; a caller object is not authority
GAP-7 (B-STRICT): OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE —
    the GAP-7 resolver is the currentness authority, for the comparison
    operand exactly as for the baseline operand
Canonical replay order (grammar v0.6 §5): checks 1–11 (registered lookup,
    currentness, metric identity, methodology identity) precede coverage and
    comparability — a refusal record is downstream of the same canonical
    resolution, never exempt from it
```

The engine's own derivation docstring already promised "structural identity is
re-checked here, fail closed"; it checked the two operands against each other
but never against the governing rule.

### 3.3 Sealing

```text
COMPARISON_OPERAND              = CANONICAL_REGISTRY_RESOLUTION
RULE_METRIC_BINDING             = EXACT:
    comparison.metric_definition_ref
      == baseline.metric_definition_ref
      == rule.metric_definition_ref                (three-way, not pairwise)
MUTATED_CALLER_OBJECT_AUTHORITY  = NONE:
    every record field derives from the registry-resolved comparison; refusal
    records (NOT_COMPARABLE / UNRESOLVED) are built from the same canonical
    resolution
SEMANTIC_FINGERPRINT_REPLAY      = SEALED_AS_RUNG9_CHECK_17 (§5)
```

---

## 4. The preferred API shape, and why it is adopted

The repair adopts `comparison_measurement_ref: str` as the derivation input —
the reviewer's preferred form — instead of a caller-built
`MeasurementObservation` object. This is an **internal implementation API**
boundary, not a public authority-bearing contract: `derive_change_observation`
is the Rung 8 engine entry point, not one of the two ratified contract classes,
and grammar v0.7 §2.4's contract-class audit (exactly 2 public
authority-bearing classes) is unaffected.

```text
CALLER_OBJECT_AUTHORITY      = NONE
PREFERRED_API                = comparison_measurement_ref: str
PUBLIC_CONTRACT_CHANGED      = FALSE   (ChangeObservation / ComparisonRule
                                        untouched)
NEW_AUTHORITY_CLASS          = FALSE
```

A ref cannot carry altered content; a mutated copy has nothing to mutate.

---

## 5. Semantic-fingerprint replay — sealed as Rung 9 check 17

Phase 8 requires the engine to verify the rule's
`metric_definition_semantic_fingerprint` against a recomputation from the
registered `MetricDefinition`. A corpus-wide search finds **no canonical
semantic-fingerprint helper in executable form** in this amendment's runtime
(the selector receives one as an injected callable; nothing computes one from a
`MetricDefinition`). Inventing a duplicate fingerprint algorithm is a stop
condition.

Per the operator instruction, the exact metric-ref binding is sealed **now**
(§3.3) and fingerprint replay is recorded as a residual:

```text
RULE_FINGERPRINT_REPLAY                  = DEFERRED
RESERVED_CHECK                           = RUNG9_CHECK_17
DEFERRED_ITEM                            = recompute
    metric_definition_semantic_fingerprint from the registered
    MetricDefinition via the canonical helper and compare against the rule's
    declared fingerprint
NEW_FINGERPRINT_ALGORITHM_INVENTED       = FALSE
STOP_CONDITION_TRIGGERED                 = FALSE
```

Until Rung 9 supplies the canonical helper, the engine seals the metric-ref
binding exactly (comparison == baseline == rule) and continues to require the
selector's injected fingerprint gate, which already fails closed on an
unresolvable definition.

---

## 6. Coverage observation state audit — UNRESOLVED applicability was encoded as NOT_APPLICABLE

Audited per operator instruction before committing. The unrepaired Rung 7
`replay_coverage_checks` mapped `not required` (applicability UNRESOLVED,
`NO_UPSTREAM_DETERMINATION_EXISTS`) to `CoverageObservationState.NOT_APPLICABLE`,
and the unrepaired Rung 8 `_sealed_coverage` derived the same member.

The doctrine is **not silent**:

```text
R-3 (amendment plan v0.4 §3; grammar v0.4 §3.1):
    coverage_observation_state ∈ {PRESENT, UNAVAILABLE, NOT_APPLICABLE},
    ref required iff PRESENT
GRAMMAR v0.4 §3.1:
    UNRESOLVED -> comparison UNAVAILABLE before any coverage observation
    semantics are used
GRAMMAR v0.6 §6 (AC-17):
    coverage_applicability_source_ref absent means
    NO_UPSTREAM_DETERMINATION_EXISTS only;
    "NOT_APPLICABLE is never an absence encoding under this grammar"
GAP-3 / 3C (grammar v0.6 §2.1): NOT_APPLICABLE is not derivable from the
    absence of a rule; CAN_DERIVE_NOT_APPLICABLE = FALSE
```

`NOT_APPLICABLE` means coverage is authoritatively known not to apply. Applicability
`UNRESOLVED` means no authoritative determination exists — an absence, and
absences encode as `UNAVAILABLE` (or flow to refusal records), never as
`NOT_APPLICABLE`.

```text
UNRESOLVED_APPLICABILITY_TO_NOT_APPLICABLE = FORBIDDEN (repaired)
UNRESOLVED_APPLICABILITY_OBSERVATION_STATE = UNAVAILABLE
NEW_ENUM_MEMBER_INVENTED                   = FALSE (existing member reused per
                                                    doctrine)
DOCTRINE_SILENT                            = FALSE (no STOP)
```

The repair maps applicability-UNRESOLVED to `UNAVAILABLE` in both rungs,
preserving the existing R-3 ref pairing (ref present iff PRESENT).

---

## 7. The repair, specified

Append-only on top of `2838e9ba7daccc8ef2a2f41cdd7d989e6dce17b3`. No rewrite of
Rung 8's ratified arithmetic; the stored-binary64 law, zero-baseline law,
non-finite firewall, direction derivation and caller-authority firewall are
untouched and re-proven by regression.

```text
A. engine-derived baseline selection
   - remove selected_baseline_ref from derive_change_observation
   - the engine structurally loads each candidate ref through the registry
     (unknown/dangling ref -> fail closed, no silent removal, no substitution)
   - the engine invokes select_baseline() with the ratified inputs
   - BASELINE_UNAVAILABLE on a COMPARABLE verdict -> fail closed (an
     unresolvable baseline is a fault in derivation inputs, not a decision the
     sealed replay made); no placeholder ref is ever invented
   - the engine-derived selection must be a member of the supplied candidate
     set, else fail closed
B. structured Rung-7 coverage consumption
   - ComparabilityVerdict gains an internal frozen `coverage` field carrying
     the existing CoverageAuthorization (append-only, default None for
     compatibility with any hand-built historical verdict)
   - a sealed verdict without structured coverage cannot drive arithmetic:
     fail closed (never parse prose as a fallback)
   - Rung 8 reads requirement status / observation state / observation ref /
     verdict from the structured object only
C. canonical comparison resolution
   - the derivation input is comparison_measurement_ref: str
   - the engine resolves through registry.resolve_current() at the start;
     every record field derives from the canonical resolution
   - refusal records use the same canonical resolution
D. exact rule metric binding
   - comparison.metric == baseline.metric == rule.metric_definition_ref
     (three-way) before selection and arithmetic
E. coverage-state mapping
   - applicability UNRESOLVED -> CoverageObservationState.UNAVAILABLE in
     Rung 7 and Rung 8
```

---

## 8. What this record does not do

```text
NEW BASELINE POLICY               = NONE (selector unchanged, inputs unchanged)
NEW SELECTOR SEMANTICS            = NONE
NEW COMPARISON-SIDE SELECTOR      = NONE
COVERAGE AGGREGATION              = NONE
NEW OBSERVATION-STATE ENUM MEMBER = NONE
NEW AUTHORITY-BEARING CLASS       = NONE (contract count remains exactly 2)
NEW FINGERPRINT ALGORITHM         = NONE (replay deferred to Rung 9 check 17)
UNIT CONVERSION                   = NONE
EPSILON / TOLERANCE               = NONE
DECIMAL / FRACTION                = NONE
BOOK_7                            = NONE
LIVE_ACQUISITION                  = NONE
RATIFIED_RECORD_EDITED            = FALSE
SCHEMA_REWRITTEN                  = FALSE
REBASE / AMEND / SQUASH           = FALSE
```

## 9. Authority flags

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = TRUE   (offline amendment scope only)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## 10. Cross-references

```text
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.6.md   §3.1, §3.2, §5, §6, §7
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.7.md   §3 (unchanged invariants)
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.4.md   §3.1 (R-3 discriminator)
CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_PLAN_v0.4.md  §3 (R-2/R-3 single meanings)
CSIA_BOOK_6_COMPARISON_CHANGE_OPERAND_CARDINALITY_RATIFICATION_RECORD_v0.1.md
CSIA_BOOK_6_COMPARISON_COVERAGE_MEASUREMENT_BINDING_RATIFICATION_RECORD_v0.1.md
book6_comparison_change_derivation.py           Rung 8 (repaired)
book6_comparison_coverage.py                    Rung 7 (structured result; state mapping)
book6_comparison_selector.py                    select_baseline (reused as-is)
book6_comparison_registry.py                    ComparisonRuleRegistry
book6_registry.py                               resolve_current / registered_measurement
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```

---

**Status:** `RATIFIED`. The three defects are implementation authority defects
against already-ratified law. The repair is authorized, append-only, and scoped
exactly as §7 specifies. No doctrine changed; no stop condition triggered.
