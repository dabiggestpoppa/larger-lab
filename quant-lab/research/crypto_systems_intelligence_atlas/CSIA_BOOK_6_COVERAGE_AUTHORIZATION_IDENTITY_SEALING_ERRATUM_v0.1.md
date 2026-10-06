# CSIA — Book 6 Coverage Authorization Identity Sealing Erratum v0.1

**Status:** `RATIFIED` (binding correction; no operator selection made or implied)
**Record type:** narrow governance erratum
**Date:** 2026-10-06
**Decision id:** none required. Every clause below restates or seals law that is
already ratified by the accepted substrate; no operator selection is made, no
doctrine is created or amended.
**Grants implementation authority:** `TRUE` (offline amendment scope only, for
the append-only repair this record specifies)
**Grants new doctrine:** `FALSE`
**Changes implementation:** `TRUE` (append-only repair on
`4ddac952bf11ce6c4a20a90bf12dae774515767e`)
**Reopens GAP-1..GAP-7 / the coverage-measurement-binding ratification:** `FALSE`

```text
DOCTRINE_CHANGED                              = FALSE
NEW_FIELD                                     = FALSE
NEW_AUTHORITY_CLASS                           = FALSE
NEW_REGISTRY                                  = FALSE
COVERAGE_REPLAY_COMPARISON_SOURCE             = CANONICAL MEASUREMENT REGISTRY
COVERAGE_REPLAY_METRIC_SOURCE                 = CANONICAL COMPARISON
                                                MEASUREMENT.metric_definition_ref
COVERAGE_REPLAY_OBSERVATION_SOURCE            = Book6MeasurementRegistry
                                                .coverage_of(comparison_measurement_ref)
CALLER_SUPPLIED_METRIC_AUTHORITY              = FALSE
CALLER_SUPPLIED_COVERAGE_OBSERVATION_AUTHORITY = FALSE
COVERAGE_AUTHORIZATION_IDENTITY_SEALED        = TRUE
RUNG8_MUST_VERIFY_SEALED_BUNDLE_AGAINST_RULE  = TRUE
DOCTRINE_CHANGED                              = FALSE
NEW_AUTHORITY_CLASS                           = FALSE
```

---

## 0. What this record is

External review identified four identity-binding defects in the Rung 7 coverage
replay (`book6_comparison_coverage.py`) and its Rung 8 consumption, all present
at implementation HEAD `4ddac952bf11ce6c4a20a90bf12dae774515767e`. Each was
reproduced against the unrepaired engine by execution, and each is a violation
of law that is **already accepted** in the Book 6 substrate. This record
documents the reproductions, anchors each repair to its existing ratified
clause, and authorizes the append-only repair. No doctrine changes.

## 1. The accepted canonical identity sources (already ratified)

The accepted Book 6 substrate already establishes exactly one canonical home
for each identity the coverage replay consumes:

```text
MEASUREMENT IDENTITY      Book6MeasurementRegistry (registered_measurement /
                          resolve_current; registration is not authority)
METRIC IDENTITY           MeasurementObservation.metric_definition_ref on the
                          CANONICAL RESOLVED observation (a measurement may not
                          define its own metric: register_measurement refuses
                          an unregistered metric_definition_ref)
COVERAGE OBSERVATION      Book6MeasurementRegistry.coverage_of(measurement_id);
                          register_coverage stores BY coverage.measurement_id,
                          so no accepted path can return measurement B's
                          coverage when asked for measurement A's
COVERAGE RULE AUTHORITY   CoverageRuleRegistry (the same registry the state
                          vector seals DATA_COMPLETE with); owned by the
                          measurement registry as its coverage_rules member,
                          constructed exactly once, never reassigned
RULE-TO-RULE BINDING      ComparisonRule.coverage_sufficiency_rule_ref (R-2:
                          required when REQUIRED, absent otherwise) and
                          ComparisonRule.coverage_applicability_source_ref
                          (R-2: single meaning; absent means
                          NO_UPSTREAM_DETERMINATION_EXISTS)
```

```text
METRIC_IDENTITY_SOURCE          = CANONICAL MEASUREMENT
COVERAGE_OBSERVATION_SOURCE     = BOOK6 MEASUREMENT REGISTRY
COVERAGE_REGISTRY_OWNERSHIP     = SINGLE (measurement_registry.coverage_rules;
                                  no second independent registry exists)
NEW_POLICY_DECISION             = FALSE
DOCTRINE_CHANGED                = FALSE
```

## 2. The four defects, reproduced by execution

Each reproducer ran against the unrepaired engine and printed
`*_REPRODUCED = True`. The code is deleted after the run; the reproductions
are recorded here and pinned by permanent tests in the repair.

### DEFECT A1 — caller-supplied metric redefines coverage scope

`replay_coverage_checks(metric_id=...)` let the caller name any metric. A
canonical comparison `obs:c` measuring `metric:A`, replayed with
`metric_id="metric:B"`, a `metric:B`-scoped rule `cov:B`, and an observation
attached to `obs:c` naming `cov:B`, produced checks 12–16 **all green** and
verdict `SUFFICIENT` — although no rule for `metric:A` was current at all.

```text
A1_REPRODUCED = TRUE
CALLER_SUPPLIED_METRIC_CAN_REDEFINE_COVERAGE_SCOPE = TRUE (defect)
```

This violates the accepted binding: coverage scope is determined by the
comparison measurement's canonical metric
(`MeasurementObservation.metric_definition_ref`), never by a caller string.
It is the direct sibling of the Rung 7 measurement-binding repair
(`BOOK6-COVERAGE-MEASUREMENT-BINDING-v0.1`), which bound the *evidence* to the
comparison measurement but left the *metric* caller-supplied.

### DEFECT A2 — caller-supplied coverage observation object substitutes evidence

`replay_coverage_checks(coverage_observation=...)` accepted an arbitrary
`CoverageObservation`. With canonical registered coverage for `obs:c` at
`observed_fraction = 0.40` (INSUFFICIENT under a 0.90 rule), a fresh
**unregistered** object claiming `observed_fraction = 1.00` for the same
measurement and rule produced verdict `SUFFICIENT`.

```text
A2_REPRODUCED = TRUE
CALLER_CAN_SUBSTITUTE_UNREGISTERED_COVERAGE_EVIDENCE = TRUE (defect)
```

This violates the accepted evidence home: the measurement registry owns
`register_coverage` / `coverage_of`; check 16 must consume the canonical
registered observation and never a caller object.

### DEFECT A3 — structured authorization carried no identity seal

`CoverageAuthorization` carried the semantic fields (applicability, observation
state, observation ref, verdict, checks) but none of the identities the replay
resolved: not the comparison measurement, not the metric, not the named rule.
Two equally valid bundles — AUTH-A for `obs:a`/`metric:A`/`cov:A` and AUTH-B
for `obs:b`/`metric:B`/`cov:B` — were structurally indistinguishable to a
consumer. Handing Rung 8 the sealed verdict derived from AUTH-B while deriving
arithmetic for `obs:a` ran the arithmetic and stamped the record with AUTH-B's
coverage facts (`coverage_observation_ref = obs:b`).

```text
A3_REPRODUCED = TRUE
STRUCTURED_COVERAGE_AUTHORIZATION_IDENTITY = UNSEALED (defect)
```

### DEFECT A4 — the agreement check was status-only

`_require_declared_and_sealed_agree` compared only REQUIRED vs UNRESOLVED
between the sealed authorization and the governing rule. Equal `REQUIRED`
status alone let AUTH-B through (A3's reproducer). Same status, different
authority bundle: no substitution was detectable.

```text
A4_REPRODUCED = TRUE
SAME_STATUS_DIFFERENT_AUTHORITY_BUNDLE = ACCEPTED (defect)
```

## 3. The repair, anchored to accepted law

The repair is implementation-only. Each clause re-binds a replay input to its
already-accepted canonical home; no new field, registry, authority class or
policy is created.

```text
REPAIR A1  the replay API takes no metric_id. The metric is derived at replay
           start from measurement_registry.resolve_current(
           comparison_measurement_ref).metric_definition_ref. Check 12
           resolves applicability for THAT metric; check 15 judges the named
           rule's scope against THAT metric.
           (Anchor: METRIC IDENTITY above; GAP-3/3C resolves "for the exact
           metric being compared" — the comparison's, not the caller's.)

REPAIR A2  the replay API takes no coverage_observation. The evidence is
           measurement_registry.coverage_of(comparison_measurement_ref) —
           None when absent, which is the honest UNAVAILABLE state. Check 16
           consumes only that object and re-performs its measurement and rule
           bindings. A caller object has no parameter to arrive through.
           (Anchor: COVERAGE OBSERVATION above; register_coverage keys by
           measurement_id.)

REPAIR A3  CoverageAuthorization gains internal identity fields recording
           which authority bundle produced the verdict:
           comparison_measurement_ref, metric_id, named_rule_ref. The
           applicability source_ref is already structured and is not
           duplicated. These are diagnostic-of-origin fields on an internal
           frozen value object — not a new authority-bearing contract.
           (Anchor: STRUCTURED COVERAGE AUTHORITY IDENTITY = SEALED.)

REPAIR A4  Rung 8's agreement check extends from status-only to exact
           identity agreement where each field is applicable:
           sealed.comparison_measurement_ref == comparison_current.measurement_id;
           sealed.metric_id == comparison_current.metric_definition_ref ==
           rule.metric_definition_ref; sealed.named_rule_ref ==
           rule.coverage_sufficiency_rule_ref;
           sealed.applicability.source_ref ==
           rule.coverage_applicability_source_ref.
           SAME_STATUS_DIFFERENT_AUTHORITY_BUNDLE = REFUSED.
           (Anchor: R-2's single meanings; canonical replay order checks 9-11
           precede coverage; the Rung 8 sealing erratum v0.1 already binds
           refusal records to the canonical comparison.)
```

The UNRESOLVED path is preserved exactly: with applicability UNRESOLVED,
`ComparisonRule` R-2 forbids a `coverage_sufficiency_rule_ref` and an
applicability source ref; the sealed bundle records
`named_rule_ref = None`, `source_ref = None`,
`CoverageObservationState.UNAVAILABLE`, `CoverageVerdict.UNKNOWN`. Coverage
never manufactures authority on that path. (`ZERO_CANDIDATE_HISTORICAL_RECORD_REQUIREMENT = NOT ESTABLISHED`; `SCHEMA_CHANGE_REQUIRED_NOW = FALSE` — the
baseline-unavailable schema question is untouched by this record.)

## 4. Coverage registry ownership (verified, not assumed)

`Book6MeasurementRegistry.__init__` constructs exactly one
`CoverageRuleRegistry` as its `coverage_rules` member; no production code
reassigns the attribute. The repair derives the coverage registry from the
measurement registry (`measurement_registry.coverage_rules`), so **two
independent registries can never jointly authorize one replay** — the replay
receives one measurement registry and reaches everything through it. The
separate-injection parameter disappears rather than being documented.

## 5. Rung 9 preparation recorded (check 17)

No canonical executable helper recomputes a `MetricDefinition` semantic
fingerprint from a registered definition:

```text
RUNG9_CHECK17_RUNTIME_HELPER = MISSING
```

No fingerprint algorithm is invented here. The full `MetricDefinition` field
audit and semantic/presentation classification is recorded for the next
operator round, which must ratify the canonical fingerprint spec before check
17 implementation.

## 6. Scope fences

```text
IMPLEMENTATION_AUTHORIZED   = TRUE  (append-only repair on 4ddac952bf11,
                                    offline scope)
STOP_CONDITIONS_TRIGGERED   = FALSE
NEW_DOCTRINE / NEW_ENUM     = FALSE (no fourth CoverageObservationState member;
                                    no new authority-bearing class)
BOOK_7 / LIVE_ACQUISITION   = FALSE
```

**Not authorized and not performed:** any new coverage doctrine; any new
authority-bearing contract; any new registry; any baseline-unavailable schema
amendment; any fingerprint algorithm; any unit conversion; any epsilon or
tolerance; any aggregation; any edit to a ratified record; any
rebase/amend/squash; any Book 7 or live acquisition.
