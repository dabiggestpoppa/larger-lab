# CSIA — Book 6 Comparison / Change Amendment
# Implementation Test Specification v0.1

```text
ARTIFACT        = CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC
VERSION         = v0.1
KIND            = EXECUTABLE TEST PLAN (NO TEST CODE IN THIS SESSION)
DATE            = 2026-10-02
COMPANION       = CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1
IMPLEMENTATION  = NONE. THIS SPEC IS NOT A COMMITMENT TO BUILD.
VERDICT CONTEXT = the companion review returned HOLD on four gaps
                  (GAP-1 numeric representation, GAP-2 unit contract,
                   GAP-3 coverage applicability, GAP-4 comparability_status).
                  Cases marked BLOCKED below cannot be written until the
                  operator resolves the corresponding gap.
```

This specification translates ratified gate **G-5** into executable test
families. Every case names its fixture, action, expected result, and likely
test module. **No test code is written here.**

```text
PROPOSED TEST MODULES (all NEW, all under
quant-lab/tests/crypto_systems_intelligence_atlas/)

  T1  test_book6_comparison_rules.py       rules, registry, ratification
  T2  test_book6_benchmarks.py             benchmark rules + baseline resolver
  T3  test_book6_change_records.py         ChangeObservation contract
  T4  test_book6_change_engine.py          arithmetic + 19 replay checks
  T5  test_book6_amendment_adversarial.py  negative surface + attacks
  T6  test_book6_amendment_fingerprints.py digest stability + mutation
  T7  test_book6_amendment_traceability.py matrix regeneration + families
```

## 0. Fixture discipline

```text
CANONICAL_RULE_FIXTURES     = 0
  COMPARISON_RULES_RATIFIED           = 0
  BENCHMARK_RULES_RATIFIED            = 0
  COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0
=> every rule-shaped fixture is SYNTHETIC, locally constructed, and
   explicitly non-canonical. No fixture may present itself as ratified
   corpus data, and no fixture may exist to make a test pass.
SYNTHETIC FIXTURES MUST BE BUILT BY A DEDICATED FACTORY whose names all
   carry a synthetic prefix, so an accidental promotion to canonical data is
   visible in review.
BOOK 2 OBSERVATION FIXTURES = reuse the accepted conftest factories; do not
   invent new Book 2 semantics.
```

## 1. `COV-1 .. COV-12` — coverage applicability and sufficiency

Module **T4** (with **T1** for rule construction).

```text
COV-1   fixture: synthetic rule, coverage_requirement_status=REQUIRED,
                 coverage_applicability_source_ref set
         action: construct
         expect: ACCEPTED
         blocked: no

COV-2   fixture: status=REQUIRED, source_ref ABSENT
         action: construct
         expect: ValidationError (NULL-4/NULL-5)
         blocked: no

COV-3   fixture: status=NOT_APPLICABLE, source_ref set
         action: construct
         expect: ACCEPTED
         blocked: no

COV-4   fixture: status=UNRESOLVED, source_ref ABSENT
         action: construct
         expect: ACCEPTED; absence means exactly
                 NO_UPSTREAM_DETERMINATION_EXISTS
         blocked: no

COV-5   fixture: status=UNRESOLVED, source_ref SET
         action: construct
         expect: ValidationError (the two are mutually exclusive)
         blocked: no

COV-6   fixture: any comparison under check 12
         action: resolve applicability from accepted MetricDefinition and
                 MeasurementMethodology semantics
         expect: UNRESOLVED (no derivation source exists)
         blocked: YES - GAP-3. Under OPTION-3A this is the permanent
                 expected result; under OPTION-3B the expected result comes
                 from a ratified derivation that does not yet exist.

COV-7   fixture: canonical coverage-rule count = 0
         action: replay coverage sufficiency
         expect: fail closed; coverage_verdict = UNKNOWN; no SUFFICIENT
         blocked: no

COV-8   fixture: caller supplies coverage_verdict="SUFFICIENT"
         action: construct ChangeObservation
         expect: ValidationError (CO-9, no self-declaration)
         blocked: no

COV-9   fixture: coverage_observation_state=PRESENT, ref ABSENT
         action: construct
         expect: ValidationError (R-3)
         blocked: no

COV-10  fixture: state=UNAVAILABLE or NOT_APPLICABLE, ref PRESENT
         action: construct
         expect: ValidationError (R-3)
         blocked: no

COV-11  fixture: a CoverageSufficiencyRule scoped to a different metric
         action: replay check 15
         expect: CoverageRuleError (scope mismatch)
         blocked: no

COV-12  fixture: status=REQUIRED + state=UNAVAILABLE
         action: construct and replay
         expect: construction ACCEPTED (the combination is legal) but the
                 comparison is UNAVAILABLE and the G7 gate cannot pass
         blocked: no
```

## 2. `CHG-1 .. CHG-8` — change observation and delta arithmetic

Module **T3** (contract) and **T4** (arithmetic).

```text
CHG-1   fixture: valid synthetic rule + baseline + comparison measurements
         action: engine computes change_kind
         expect: INCREASE when canonical absolute_delta > 0
         blocked: YES - GAP-1 (numeric type), GAP-2 (unit compatibility)

CHG-2   fixture: comparison value below baseline
         action: compute
         expect: DECREASE; a NEGATIVE relative_delta is also a DECREASE,
                 never an INCREASE and never |value|
         blocked: YES - GAP-1, GAP-2

CHG-3   fixture: comparison value EXACTLY equal to baseline
         action: compute
         expect: NO_CHANGE on exact canonical equality
         blocked: YES - GAP-1. This is THE decisive case for the numeric
                 representation decision: under 1A it is float ==; under 1C
                 it is Fraction equality and is exact.

CHG-4   fixture: baseline == canonical zero, operator=RELATIVE_DELTA
         action: compute
         expect: relative_delta ABSENT; change_kind = CHANGE_UNDEFINED;
                 value is None - NOT 0, NOT inf, NOT NaN, NOT 100%,
                 NOT capped
         blocked: no  (law fully ratified)

CHG-5   fixture: baseline == canonical zero, operator=ABSOLUTE_DELTA
         action: compute
         expect: absolute_delta computed normally where the unit supports
                 subtraction
         blocked: YES - GAP-2

CHG-6   fixture: absolute_delta ABSENT (not computable)
         action: construct
         expect: ABSENT means NOT_COMPUTABLE, never 0; change_kind is not
                 NO_CHANGE
         blocked: no

CHG-7   fixture: caller supplies absolute_delta / relative_delta /
                 change_kind / current_authority
         action: construct
         expect: ValidationError on every one (extra="forbid")
         blocked: no

CHG-8   fixture: caller supplies expected_* values that DISAGREE with the
                 engine's recomputation
         action: construct
         expect: raises; the caller's value is never persisted
         blocked: no
```

## 3. `METH-1 .. METH-5` — methodology compatibility and sensitivity

Module **T1** / **T4**.

```text
METH-1  fixture: observation methodology NOT in compatible_methodology_refs
         action: replay check 11
         expect: ChangeEngineError
         blocked: no

METH-2  fixture: compatible_methodology_refs containing a wildcard ("*")
         action: construct a rule
         expect: ValidationError (P2: NEVER a wildcard)
         blocked: no

METH-3  fixture: two methodology versions, one ratified, one superseded
         action: replay
         expect: the superseded one refuses; identity is ref@version and is
                 matched EXACTLY (no substring, no alias)
         blocked: no

METH-4  fixture: same methodology identity, MUTATED content
         action: re-register / replay check 5
         expect: refused - content digest is fixed at first registration
                 (the accepted R2-D1 defence)
         blocked: no

METH-5  fixture: methodology-sensitivity NON-AVERAGING
         action: derive a comparison under methodology A and under
                 methodology B for the same underlying data
         expect: the two are NOT averaged and NOT reconciled into one
                 number; each is separately derived or separately refused
         blocked: no
```

## 4. `NULL-1 .. NULL-9` — absence has exactly one meaning

Module **T3**. Substrate: `Book6FrozenModel` `extra="forbid"`, `frozen=True`
plus `@model_validator(mode="after")`.

```text
NULL-1  coverage_applicability_source_ref absence is ONLY
        NO_UPSTREAM_DETERMINATION_EXISTS  -> see COV-2 / COV-4 / COV-5
NULL-2  coverage_observation_state replaces the conflated v0.3 field; the
        old field name is absent from the model -> see §6 NEG-1
NULL-3  ResponseLink.coverage_verdict_quoted is MANDATORY when the source
        carries it; optionality may not become silence about a known value
NULL-4  status REQUIRED / NOT_APPLICABLE without source_ref -> INVALID
NULL-5  status UNRESOLVED with source_ref -> INVALID
NULL-6  coverage_observation_ref present iff state == PRESENT
NULL-7  ABSENT != UNKNOWN != NOT_APPLICABLE != UNAVAILABLE != NOT_REQUIRED
        != UNRESOLVED != UNDEFINED != ZERO != FALSE  (distinct enum members,
        distinct fields, no aliasing)
NULL-8  supersedes_ref: version == 1 -> ABSENT; version > 1 -> REQUIRED;
        absent at version > 1 is REJECTED
NULL-9  valid_time.valid_to absent means OPEN_ENDED / STILL VALID UNTIL
        SUPERSEDED OR WITHDRAWN and NOTHING ELSE; it never means
        "end unknown"
NULL-10 absolute_delta absent means NOT_COMPUTABLE and NEVER 0
NULL-11 relative_delta absent means UNDEFINED and NEVER 0/inf/NaN/capped
```

## 5. The nineteen replay checks — each independently falsifiable

Module **T4**. **An aggregate `validate_all()` returning one boolean is NOT
sufficient.** Each check has its own test that fails when that one check
fails, proven by a fixture that breaks exactly one check and leaves the
other eighteen green.

```text
CHK-1  rule identity + version          falsifier: rule absent from registry
CHK-2  operator-ratification binding    falsifier: registered, never ratified
CHK-3  rule content fingerprint         falsifier: mutate a semantic field,
                                               keep the identity
CHK-4  baseline methodology identity    falsifier: benchmark count is 0
CHK-5  baseline methodology fingerprint falsifier: same id, changed content
CHK-6  baseline current authority       falsifier: benchmark superseded
CHK-7  closed delta operator            falsifier: "PERCENT_CHANGE"
CHK-8  baseline measurement refs        falsifier: empty tuple; dangling id
CHK-9  comparison measurement refs      falsifier: empty tuple; dangling id
CHK-10 input Book 2 current authority   falsifier: observation whose Book 2
                                               claim lost authority
CHK-11 methodology compatibility        falsifier: id outside the allow-list
CHK-12 coverage applicability           falsifier: none available
        ** BLOCKED - GAP-3 **
CHK-13 coverage rule ref (REQUIRED)     falsifier: status REQUIRED, ref null
CHK-14 coverage rule ratified+current  falsifier: canonical count is 0
CHK-15 coverage scope match            falsifier: rule scoped elsewhere
CHK-16 deterministic coverage verdict   falsifier: caller verdict differs
CHK-17 metric-definition content match  falsifier: definition mutated after
                                               ratification
CHK-18 input methodology policy match   falsifier: policy redefinition (P9)
CHK-19 deterministic recomputation     falsifier: supplied change_kind and
                                               deltas disagree with the
                                               engine's recomputation
        ** BLOCKED - GAP-1, GAP-2 **
```

```text
PER_CHECK_FALSIFIABILITY_TESTS = 19
AGGREGATE_ONLY                = REJECTED
CHARGED_TESTS_BLOCKED         = 2  (CHK-12, CHG-19)
```

**Authority replay (separate family, same module).**

```text
AUTH-1  authorize_change_observation() re-runs all 19; assert the returned
        structure has 19 per-check entries, not a single boolean
AUTH-2  no cached authority: call twice, mutate a dependency in between,
        assert the second call reports current_authority = FALSE
AUTH-3  decay preserves history: after a dependency decays, the original
        ChangeObservation is still queryable, unmutated, with its original
        recorded values (CO-6, CO-10)
AUTH-4  a rule that was ratified but whose benchmark rule is later
        invalidated yields current_authority = FALSE (RATIFIED RULE +
        CHANGED DEPENDENCY != CURRENTLY AUTHORITATIVE)
```

## 6. `POL-1 .. POL-11` — policy is not authority

Module **T5**. Per plan G-5's note, these are **rejection cases**, not
enumeration cases: the guarantee is that no such field exists to vary.

```text
POL-1  delta_operator is one of exactly two values; a third is
       unconstructible
POL-2  compatible_methodology_refs cannot contain a wildcard
POL-3  a rule may CITE unit requirements but may NOT redefine unit
       arithmetic
       ** BLOCKED - GAP-2: untestable, there is no unit contract to govern **
POL-4  denominator_requirements are required and closed
POL-5  cohort_requirements are required where relevant and closed
POL-6  window_compatibility cites an accepted WindowClass
POL-7  missingness_requirements name permitted accepted states
POL-8  an epsilon attempt is rejected; no epsilon field exists
POL-9  a tolerance attempt is rejected; no tolerance field exists
POL-10 a zero_baseline_policy alternative is rejected; the field does not
       exist and the fixed law governs (incl. the 0/inf/NaN/100%/capped
       family)
POL-11 a rule attempting to authorize incompatible units is rejected
       ** BLOCKED - GAP-2 **
```

## 7. Negative surface — fields that must NOT EXIST (Phase 22)

Module **T5**. Substrate: `Book6FrozenModel` `ConfigDict(extra="forbid",
frozen=True)`. Each name is attacked three ways: **constructor**,
**model_copy**, **deserialization**.

```text
NEG-1  direction_derivation        -> ABSENT from ComparisonRule and from
                                      ChangeObservation model_fields()
NEG-2  zero_baseline_policy        -> ABSENT
NEG-3  unit_divisibility_policy    -> ABSENT
NEG-4  rounding_precision_policy   -> ABSENT
NEG-5  epsilon                     -> ABSENT
NEG-6  tolerance                   -> ABSENT
NEG-7  materiality                 -> ABSENT
NEG-8  significance                -> ABSENT
NEG-9  custom_formula              -> ABSENT
```

**Attack matrix for each of NEG-1..NEG-9** (39 cases minimum):

```text
(a) CONSTRUCTOR       ComparisonRule(**{name: value})       -> ValidationError
(b) MODEL_COPY        rule.model_copy(update={name: value})  -> rejected or
                                                            the name is not a
                                                            field at all
(c) DESERIALIZATION   Model.model_validate({... name ...})   -> ValidationError
(d) FIELD ABSENCE     name not in Model.model_fields()      -> assert False
(e) ENGINE ABSENCE    the name does not appear anywhere in
                      book6_comparison_rules.py,
                      book6_change_records.py, or
                      book6_change_engine.py source
```

```text
NEGATIVE_SURFACE_NAMES       = 9
ATTACKS_PER_NAME             = 5
NEGATIVE_SURFACE_CASES       = 45
SUBSTRATE                    = accepted (extra="forbid", frozen=True)
```

## 8. Fingerprint tests (Phase 23)

Module **T6**. Four digests, each with the same five assertions.

```text
FP-1  ComparisonRule canonical fingerprint
FP-2  baseline benchmark methodology fingerprint
FP-3  MetricDefinition semantic content fingerprint
FP-4  ComparisonDerivationBinding digest
```

```text
ASSERTION A  semantic mutation CHANGES the digest
             (change one semantic field; every other field held constant)
ASSERTION B  non-semantic display metadata does NOT change the digest
             (ChangeObservation.display_metadata is excluded from check 3's
             fingerprint scope and from check 19's inputs - CO-11)
ASSERTION C  dictionary / key ordering does NOT alter the digest
             (build the canonical spec from two objects whose field
             insertion order differs)
ASSERTION D  canonical serialization is STABLE
             (repeated calls in the same process and in a fresh process
             produce byte-identical output)
ASSERTION E  same semantics => same digest
             (rebuild the object from scratch, field by field, and compare)
```

```text
FINGERPRINT_DIGESTS      = 4
FINGERPRINT_ASSERTIONS   = 5 each = 20 cases
DRIFT_GUARD              = one test per digest proving that a field added to
                            the model but not to the CANONICAL_FIELDS constant
                            makes the function RAISE (the accepted
                            METHODOLOGY_CANONICAL_FIELDS defence), so a field
                            can never be silently omitted
DIGEST_ALGORITHM         = sha256 over json.dumps(list,
                            separators=(",",":"), ensure_ascii=True)
                            - identical to the accepted pattern
NO id() / is / process   = asserted explicitly
state dependency
```

## 9. Unit arithmetic tests

Module **T4**.

```text
UNIT-1  subtraction between identical units    -> absolute_delta computable
        ** BLOCKED - GAP-2 **
UNIT-2  subtraction between incompatible units -> refused by the unit
                                                 contract, never by the rule
        ** BLOCKED - GAP-2: no unit contract exists **
UNIT-3  relative ratio with a dimensionless result -> valid
        ** BLOCKED - GAP-2 **
UNIT-4  a rule attempting to declare two units compatible -> rejected
        (POL-11)
        ** BLOCKED - GAP-2 **
UNIT-5  no caller override exists: a caller cannot assert compatibility
        ** BLOCKED - GAP-2 **

THE ENTIRE UNIT FAMILY IS BLOCKED BY GAP-2.
```

## 10. Display-independence tests

Module **T3** / **T4**.

```text
DISP-1  two ChangeObservations identical except display_metadata produce
        the SAME change_kind
DISP-2  ... the SAME absolute_delta and relative_delta
DISP-3  ... the SAME check-19 recomputation verdict
DISP-4  ... the SAME comparison-rule canonical fingerprint (display metadata
        is outside check 3's fingerprint scope)
DISP-5  ROUNDING_AFFECTS_CHANGE_CLASSIFICATION = FALSE, demonstrated with a
        value whose display rounding would flip its apparent sign
DISP-6  DISPLAY_ROUNDING_IS_AUTHORITY = FALSE, demonstrated by varying only
        display precision across an authority replay
```

## 11. Anti-creep and boundary tests

Module **T5**.

```text
CREEP-1  no Book 2 Claim promotion: a ChangeObservation is NOT a Book 2
         claim and creates none (CO-1)
CREEP-2  no event semantics (CO-2)
CREEP-3  no goodness / health / adoption semantics (CO-3)
CREEP-4  NOT_A_STATE (CO-7): no Book 6 StateName is emitted, no
         StateRule is consulted, StateRuleRegistry is not imported
CREEP-5  no score / rank / grade / buy / sell field exists on either model
CREEP-6  no materiality or significance surface anywhere
CREEP-7  derivable (CO-4): the same inputs reproduce the same record
CREEP-8  fail closed (CO-5): every refusal path raises, none returns a
         partial or best-effort result
CREEP-9  no late-bound derivation (CO-10): the binding digest is fixed at
         ratification and never silently re-derived
CREEP-10 immutability (CO-6): a frozen model rejects in-place mutation
CREEP-11 no self-authorization (CO-8)
CREEP-12 no canonical rule count is non-zero after the suite runs
         (COMPARISON / BENCHMARK / COVERAGE all remain 0)
```

## 12. Book 7 seam read-only contract tests

Module **T7**.

```text
SEAM-1  a Book 6 ChangeObservation exposes change_observation_id, the
        comparison rule ref/version/fingerprint, coverage_requirement_status,
        coverage_verdict, valid_time, and a resolvable current_authority
SEAM-2  SOURCE_VALUE_PRESENT -> SEAM_QUOTE_PRESENT holds for a
        ResponseLink quoting a change value
SEAM-3  RL-1..RL-13 each resolve to a real test function
SEAM-4  Book 6 source contains NO import of any Book 7 module
        (mechanical scan of every book6_*.py)
SEAM-5  no Book 6 field is writable from outside Book 6
SEAM-6  no Book 7 code exists on the implementation branch
```

## 13. Rule registry and governance tests

Module **T1** (comparison rules) and **T2** (benchmarks).

```text
GOV-1   bootstrap COMPARISON_RULES_RATIFIED == 0
GOV-2   register() accepts an UNRATIFIED rule and confers NOTHING
        (REGISTRATION != RATIFICATION)
GOV-3   registration_state = REGISTERED_UNRATIFIED or WITHDRAWN is NOT
        authority (OBJECT STATUS IS NOT AUTHORITY)
GOV-4   a self-declared status value does not grant ratification
GOV-5   operator-only ratification writes a RatificationRecord bound to
        identity + version + canonical fingerprint
GOV-6   MUTATED CONTENT UNDER A BOUND IDENTITY REJECTS
GOV-7   SUPERSESSION DOES NOT INHERIT: version N+1 requires a NEW
        RatificationRecord
GOV-8   benchmark bootstrap BENCHMARK_RULES_RATIFIED == 0 and every
        comparison therefore fails checks 4/5/6
GOV-9   the benchmark namespace is exactly the ratified 5 members; a sixth
        is unconstructible
GOV-10  the ComparisonRuleRegistry does NOT import or subclass
        StateRuleRegistry, and does NOT reuse its RuleRatificationStatus
GOV-11  the ComparisonRuleRegistry does NOT overload CoverageRuleRegistry
        (distinct registry identity, distinct scope semantics)
GOV-12  a caller-built ComparisonDerivationBinding is never accepted as
        authoritative; the registry builds it at ratification
GOV-13  re-resolving the binding digest after a dependency changes yields
        a mismatch -> current_authority = FALSE, not a silent re-bind
GOV-14  no caller boolean (is_ratified / current_authority /
        coverage_sufficient / can_compare) is accepted anywhere
```

## 14. Traceability plan (Phase 24)

Module **T7**. Target: `CSIA_BOOK_6_VALIDATION_TRACEABILITY_MATRIX.json`
plus `quant-lab/scripts/generate_book6_traceability_matrix.py`.

```text
RULE: every new ratified amendment invariant resolves to a REAL TEST
      FUNCTION NAME that exists in the suite. No manual PASS rows. The
      generator must fail if a declared test function is not found.

FAMILIES
  FAM-CMP-RULE   comparison rule governance      (GOV-1..14)
  FAM-CHANGE     change observation              (CHG-1..8, AUTH-1..4)
  FAM-DELTA      delta arithmetic                (CHG-1..5; BLOCKED on 1/2)
  FAM-COV        coverage applicability         (COV-1..12)
  FAM-NULL       nullable contracts             (NULL-1..11)
  FAM-BIND       derivation binding             (FP-4, GOV-12, GOV-13)
  FAM-AUTH       authority replay               (CHK-1..19, AUTH-1..4)
  FAM-SEAM       Book 7 seam                    (SEAM-1..6)
  FAM-ANTISCORE  anti-score / anti-materiality  (CREEP-5, CREEP-6, NEG-7..9)

INVARIANTS TO TRACE (each -> a real test function)
  AC-17  single-meaning absence            -> NULL-1..11
  AC-18  policy is not authority           -> POL-1..11
  AC-18a no policy parameter may make a
         comparison more permissive       -> POL-1..11 + CHG-7
  AC-18b no hidden threshold / materiality -> POL-8..11, CREEP-6
  AC-19  no display influence              -> DISP-1..6
  AC-20  no Book 2 promotion / no state    -> CREEP-1..4
  CO-1..CO-11                             -> CREEP-* and the CHG/NULL families
```

## 15. Case totals

```text
COV-1..COV-12                    12   (1 blocked: COV-6)
CHG-1..CHG-8                      8   (4 blocked: CHG-1,2,3,5)
METH-1..METH-5                    5   (0 blocked)
NULL-1..NULL-11                   11
POL-1..POL-11                     11   (2 blocked: POL-3, POL-11)
CHK-1..CHK-19                     19   (2 blocked: CHK-12, CHK-19)
AUTH-1..AUTH-4                     4
NEG-1..NEG-9 x 5 attacks          45
FP-1..FP-4 x 5 assertions         20  (+4 drift guards)
UNIT-1..UNIT-5                     5   (5 blocked - ENTIRE FAMILY)
DISP-1..DISP-6                     6
CREEP-1..CREEP-12                 12
SEAM-1..SEAM-6                     6
GOV-1..GOV-14                     14
------------------------------------
TOTAL SPECIFIED                  178
BLOCKED BY GAPS                   14
WRITABLE NOW                     164
```

```text
BLOCKED BREAKDOWN
  GAP-1 (numeric)        -> CHG-1, CHG-2, CHG-3, CHK-19, and the
                           NO_CHANGE half of the direction family
  GAP-2 (unit)           -> CHG-1, CHG-2, CHG-5, CHK-19, POL-3, POL-11,
                           UNIT-1..UNIT-5
  GAP-3 (applicability)  -> COV-6, CHK-12
  GAP-4 (comparability)  -> the NOT_COMPARABLE family required by G-5, and
                           comparability_status construction cases
```

## 16. Regression obligations (Phase 25)

Every case above must run with these baselines unchanged:

```text
B1 = 107    B2 = 108    B3 = 83    B4 = 230    B5 = 293   (EXACT)
R1 = 93     R2 = 46     R3 = 45                          (EXACT)
SENSOR = 2325 PASS / 14 FAIL / 4 SKIPPED   (exact known canonical set)
B6 = 1341   -> INCREASES (the amendment adds Book 6 tests)
TOTAL_CSIA = 2162 -> INCREASES
BOOK1..BOOK5_MUTATIONS = 0 ; SENSOR_MUTATIONS = 0
```

## 17. Spec verdict

```text
TEST_SPEC_COMPLETE              = TRUE  (178 cases specified)
CASES_WRITABLE_WITHOUT_GAPS     = 164
CASES_BLOCKED_BY_GAPS           = 14
NEGATIVE_SURFACE_TESTS_SPECIFIED = TRUE  (9 names x 5 attacks = 45)
TRACEABILITY_PLAN_COMPLETE       = TRUE  (9 families, all invariants traced)
TEST_CODE_WRITTEN                = 0
```

The specification is complete and executable **except** for the 14 cases
that depend on the four operator decisions in the companion review §26.4.
Those 14 are precisely the cases that would otherwise be written by
inventing policy.
