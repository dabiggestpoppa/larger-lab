# CSIA — Book 6 Comparison / Change Amendment
# Offline Implementation Authorization Review v0.1

```text
ARTIFACT            = CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_REVIEW
VERSION             = v0.1
KIND                = DECISION-READINESS REVIEW (PLANNING / DOCS ONLY)
DATE                = 2026-10-02
PREPARED_FOR        = OPERATOR DECISION
IMPLEMENTATION      = NONE. NO CODE WAS WRITTEN IN THIS SESSION.
```

```text
VERDICT = HOLD
```

The amendment is **well-specified in doctrine and under-specified in
runtime-reachable derivation**. Four concrete, individually resolvable gaps
require operator decisions. None of them is a coding defect; all four are
governance gaps that a coder would have to fill by invention, which this
program does not permit.

The single most important finding is that **three of the four gaps are
references to artifacts that the amendment says already exist, and that do
not exist in accepted Book 6**:

1. an accepted **unit contract / dimensional class** (cited by P3 and §1.4);
2. **canonical comparison** (`comparability_status`, `change_kind =
   NOT_COMPARABLE`) which is a REQUIRED field and a REQUIRED test family
   (G-5) with no ratified value domain and no producing replay check;
3. a **coverage-applicability derivation rule** that P10 says "cites a
   derived determination".

The fourth is a numeric-representation decision that changes a public model
type and is therefore never an implementation detail.

---

## 0. Scope and authority of this document

This review answers exactly one question:

> Is the ratified amendment sufficiently specified that offline
> implementation can proceed **without inventing governance policy in code**?

It does not implement. It does not ratify any rule. It does not re-accept
Book 6. It does not touch Book 7 or Book 8. It creates no new policy. Every
statement below is either a quotation of ratified doctrine (with a file and
section anchor) or a mechanical observation about accepted Book 6 source.

---

## 1. Phase 0 — Verification basis

```text
PLANNING_BRANCH                = agent/crypto-systems-intelligence-atlas-plan
PLANNING_HEAD_LOCAL            = 8557f4df82a67434951b2f9682142a59125f5153
PLANNING_HEAD_ORIGIN           = 8557f4df82a67434951b2f9682142a59125f5153
PLANNING_HEAD_LS_REMOTE        = 8557f4df82a67434951b2f9682142a59125f5153
PLANNING_WORKTREE              = CLEAN

BOOK6_IMPL_BRANCH              = agent/crypto-systems-intelligence-atlas-book6-build
BOOK6_IMPL_HEAD                = 5f94c3f40cea4441470c57671f51454da7377361
BOOK6_IMPL_WORKTREE            = CLEAN
BOOK6_IMPL_REMOTE_MATCHES      = TRUE
BOOK6_ACCEPTED_ANCHOR          = 3919fb8052e216e94034a753fb258d338c5fa0dc
ANCHOR_IS_ANCESTOR_OF_ACCEPT   = TRUE
COMMITS_BETWEEN_ANCHOR_AND_ACCEPT = 1 (the acceptance commit, DOCS ONLY)
COMMITS_AFTER_ACCEPTANCE_ANY_BRANCH = 0
LINEAGE_DRIFT                  = NONE
```

```text
GOVERNANCE STATE RE-VERIFIED
BOOK_6                              = FROZEN_ACCEPTED
BOOK_6_COMPARISON_CHANGE_PLAN       = v0.4 RATIFIED
RATIFIED_PLAN_ANCHOR                = 28bfac52c23c891ebb54e9924dedc925a859b359
AMENDMENT_RATIFICATION_COMMIT       = 8557f4df82a67434951b2f9682142a59125f5153
OPERATOR_DECISION                   = BOOK6-COMPARE-AMEND-v0.4
READINESS                           = PASS (16/16)
PRE_RATIFICATION_REVIEW             = 48/48 PASS
COMPARISON_RULES_RATIFIED           = 0 canonical
COVERAGE_SUFFICIENCY_RULES_RATIFIED = 0 canonical
BENCHMARK_RULES_RATIFIED            = 0 canonical
BOOK_6_IMPLEMENTATION_AUTHORITY     = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY     = FALSE
BOOK_8_IMPLEMENTATION_AUTHORITY     = FALSE
LIVE_ACQUISITION_AUTHORITY          = FALSE
D6M_5                               = OPEN_DEFERRED
```

### 1.1 Accepted Book 6 implementation surface (measured, not assumed)

```text
SOURCE_DIR   = quant-lab/src/crypto_systems_intelligence_atlas/
MODULE_COUNT = 19 book6_* modules
SOURCE_LINES = 8669
TEST_DIR     = quant-lab/tests/crypto_systems_intelligence_atlas/
BOOK6_TEST_FILES = 15
TRACEABILITY = book6_traceability.py (2164 lines)
             + quant-lab/scripts/generate_book6_traceability_matrix.py
```

Three accepted mechanisms materially change the implementation design and
are described in full in §5, §7 and §15 below:

- `book6_comparability.py` (388 lines) — a **ratified 15-row false-comparison
  corpus** with a working `authorize_comparison()` gate;
- `book6_methodology.py` (476 lines) — `canonical_methodology_spec()` /
  `methodology_fingerprint()` and a versioned methodology registry that
  already enforces *registered-then != authoritative-now*;
- `book6_ratification.py` (299 lines) — `RatificationRecord`,
  `DerivationBinding`, `derivation_binding_digest()`, `RatificationLedger`,
  `RatificationSeal`.

**These three make the fingerprint, registry and binding requirements of this
amendment implementable by imitation rather than by invention. That is a
strong result and it is why this review is a near-miss rather than a
rejection.**

---

## 2. Phase 2 — Implementation surface map

Classification of every planned surface. `NEW` = no accepted equivalent.
`MODIFIED` = accepted module must be extended. `UNCHANGED` = imported, not
edited.

### 2.1 Ratified concept → implementation surface

| # | Ratified concept | Surface | Class | Runtime exists? |
|---|---|---|---|---|
| S1 | `ComparisonRule` contract | `book6_comparison_rules.py` | NEW | NO |
| S2 | `ComparisonRule` registry | `book6_comparison_rules.py` | NEW | NO |
| S3 | Operator ratification binding | `book6_comparison_rules.py` | NEW | NO (pattern in `book6_ratification.py`) |
| S4 | `ComparisonDerivationBinding` | `book6_ratification.py` | MODIFIED | pattern exists, class does not |
| S5 | `ChangeObservation` contract | `book6_change_records.py` | NEW | NO |
| S6 | comparison/change engine | `book6_change_engine.py` | NEW | NO |
| S7 | baseline benchmark resolution | `book6_benchmarks.py` | NEW | NO |
| S8 | benchmark-rule registry + ratification | `book6_benchmarks.py` | NEW | NO |
| S9 | coverage applicability resolution | `book6_coverage_rules.py` | MODIFIED | partial (registry yes, derivation no) |
| S10 | coverage sufficiency resolution | `book6_coverage_rules.py` | UNCHANGED | YES (accepts zero canonical rules) |
| S11 | `MetricDefinition` semantic fingerprint | `book6_definitions.py` | MODIFIED | NO (function only; no contract change) |
| S12 | comparison-rule canonical fingerprint | `book6_comparison_rules.py` | NEW | NO |
| S13 | Book 6 → Book 7 seam support | `book6_change_records.py` | NEW | NO |
| S14 | traceability generation | `book6_traceability.py` + generator script | MODIFIED | YES |
| S15 | comparability resolution (see §3.4) | — | — | **NO SOURCE OF TRUTH** |
| S16 | unit arithmetic validity (see §14) | — | — | **NO SOURCE OF TRUTH** |

### 2.2 Per-file classification

```text
NEW
  quant-lab/src/.../book6_comparison_rules.py
  quant-lab/src/.../book6_benchmarks.py
  quant-lab/src/.../book6_change_records.py
  quant-lab/src/.../book6_change_engine.py
  quant-lab/tests/.../test_book6_comparison_rules.py
  quant-lab/tests/.../test_book6_benchmarks.py
  quant-lab/tests/.../test_book6_change_records.py
  quant-lab/tests/.../test_book6_change_engine.py
  quant-lab/tests/.../test_book6_amendment_adversarial.py
  quant-lab/tests/.../test_book6_amendment_fingerprints.py

MODIFIED
  quant-lab/src/.../book6_ratification.py   (+ComparisonDerivationBinding)
  quant-lab/src/.../book6_coverage_rules.py (+applicability resolution)
  quant-lab/src/.../book6_definitions.py    (+semantic fingerprint fn only)
  quant-lab/src/.../book6_traceability.py   (+families)
  quant-lab/scripts/generate_book6_traceability_matrix.py

UNCHANGED (import-only)
  quant-lab/src/.../book6_frozen.py
  quant-lab/src/.../book6_grammar.py
  quant-lab/src/.../book6_records.py
  quant-lab/src/.../book6_methodology.py
  quant-lab/src/.../book6_comparability.py
  quant-lab/src/.../book6_states.py
  quant-lab/src/.../book6_sensitivity.py
  quant-lab/src/.../book6_core.py
```

### 2.3 Surface-map verdict

```text
SURFACE_MAP_COMPLETE          = TRUE
NEW_FILES_PROPOSED            = 10
MODIFIED_FILES_PROPOSED       = 5
UNCHANGED_IMPORT_ONLY         = 8
BOOK1..BOOK5_SURFACE_TOUCHED  = 0
```

The surface map itself is **complete and unproblematic**. The blockers in
§3 are not surface problems; they are missing *sources of truth* for four
required outputs.

---

## 3. Phase 3 — No-policy-invention test

For every value domain, enum and behavior implementation requires: is the
domain **already ratified**, or **would the implementer have to invent it**?

### 3.1 RATIFIED — implementable with no invention

| Requirement | Ratified domain | Anchor |
|---|---|---|
| `delta_operator` | `ABSOLUTE_DELTA \| RELATIVE_DELTA` (closed) | grammar §1.1 / P1 |
| direction | sign of canonical UNROUNDED `absolute_delta`; `DIRECTION_DERIVATION_RULE = FIXED/NON-CONFIGURABLE` | grammar §1.2 |
| zero baseline | `ZERO_BASELINE_POLICY = FIXED_FAIL_CLOSED` | grammar §1.3 |
| rounding | `ROUNDING_AFFECTS_CHANGE_CLASSIFICATION = FALSE`; `DISPLAY_ROUNDING_IS_AUTHORITY = FALSE` | grammar §1.5 |
| tolerance / materiality | prohibited; no field may exist | grammar §1.6 / §2.1 |
| `change_kind` | `INCREASE \| DECREASE \| NO_CHANGE \| CHANGE_UNDEFINED \| NOT_COMPARABLE \| INSUFFICIENT_DATA` | grammar §3 |
| `coverage_requirement_status` | `REQUIRED \| NOT_APPLICABLE \| UNRESOLVED` | grammar §2 |
| `coverage_observation_state` | `PRESENT \| UNAVAILABLE \| NOT_APPLICABLE` | grammar §3.1 (R-3) |
| `coverage_verdict` | `SUFFICIENT \| INSUFFICIENT \| UNKNOWN` | grammar §3 |
| `registration_state` | `REGISTERED_UNRATIFIED \| WITHDRAWN` (non-authoritative) | grammar §2 |
| `record_state` | `CURRENT \| SUPERSEDED \| WITHDRAWN \| INVALIDATED` | grammar §3 |
| `current_authority` | `TRUE \| FALSE`, derived only | grammar §3 |
| `supersedes_ref` | `version==1` → absent; `version>1` → required (NULL-8) | grammar §2 / §8.1 |
| `valid_time.valid_to` | absent = OPEN_ENDED only (NULL-9) | grammar §2 / §8.1 |
| `coverage_applicability_source_ref` | absent = `NO_UPSTREAM_DETERMINATION_EXISTS` only (NULL-4/5) | grammar §2 / §8.1 |
| 19 replay checks | enumerated 1–19 | grammar §5 / record §5 |
| prohibitions | 10 enumerated in grammar §2.1 | grammar §2.1 |
| invariants | CO-1..CO-11, AC-17/18/18a/18b/19/20 | grammar §3.2 / §6–§8 |

```text
RATIFIED_DOMAINS              = 17
INVENTION_REQUIRED_RATIFIED  = 0
```

**Every law the amendment calls "fixed" is fully ratified.** Direction,
zero-baseline, rounding, tolerance, the closed operator set, the coverage
tri-state, the absence semantics, and the 19 checks are all implementable
exactly as written.

### 3.2 WOULD REQUIRE INVENTION — four gaps

Each is stated as the exact decision an implementer would have to make.

---

#### GAP-1 — canonical numeric representation is unratified

```text
GAP                        = GAP-1
SEVERITY                   = BLOCKER
AFFECTS                    = MeasurementObservation.value, absolute_delta,
                              relative_delta, check 19, §1.2 NO_CHANGE
ACCEPTED_RUNTIME           = book6_records.py:113
    value: float | None = None
DECIMAL_IN_BOOK6           = NONE (Decimal appears in book5_core /
                              book5_lineage / book5_provenance / book5_records
                              ONLY — never in a book6_* module)
FLOAT_SENTINEL_IN_USE      = YES — book6_core.py:181 injects float("nan")
                              as a denominator sentinel
RATIFIED_DOCTRINE_REQUIRES = "canonical UNROUNDED value" (§1.2, §3)
                            + "exact canonical equality" (§1.2)
```

**The conflict.** Ratified doctrine makes `NO_CHANGE` a function of *exact*
equality on a *canonical unrounded* value, and §4 draws the separation
`DISPLAYED EQUALITY != MEASURED EQUALITY`. Accepted Book 6 stores
`value` as an IEEE-754 binary `float`. Two distinct consequences:

1. **Exact equality is unavailable in principle.** `0.1 + 0.2 != 0.3` in
   binary64. A `ChangeObservation` claiming `change_kind = NO_CHANGE` on
   "exact canonical equality" cannot be honoured for all representable
   measurement values.
2. **The "unrounded" canonical value is itself a rounded value.** Computing
   `relative_delta = (current - baseline) / baseline` in binary64 produces a
   correctly-rounded double, not an exact rational. Doctrine says the
   comparison must be "canonical unrounded". The result of the arithmetic is
   therefore rounded *by representation*, before any display rounding is
   applied — which sits uneasily beside `ROUNDING_AFFECTS_CHANGE_CLASSIFICATION
   = FALSE`.

**Why this cannot be a coding decision.** The choice changes the type of a
public, already-accepted model field (`MeasurementObservation.value`) and
therefore either (a) mutates accepted Book 6 (forbidden by G-4 / Phase 26) or
(b) introduces a parallel exact-value channel (a new contract class, which
changes the count of authority-bearing contract classes from the ratified
2). The operator must pick one:

```text
OPTION-1A  Keep float; define the canonical value AS the binary64 double and
           define exact equality AS float ==. Cheapest; no Book 6 mutation.
           Consequence: "exact canonical equality" is exact w.r.t. the stored
           double, NOT w.r.t. the real number; doctrine wording must be
           amended to say so explicitly.
OPTION-1B  Adopt decimal.Decimal for canonical measurement values.
           Requires an accepted-Book-6 change to MeasurementObservation.value
           (a MODIFIED file, and a migration of every existing fixture) and
           requires a ratified decimal precision/scale contract.
OPTION-1C  Adopt fractions.Fraction (exact rational) for canonical values.
           Exact equality becomes literally true. Same migration cost as 1B,
           plus a ratified canonical-representation contract for source data
           (how a decimal literal in a source becomes a rational).
```

```text
GAP_1_UNRATIFIED_POLICY_NEEDED = TRUE
```

---

#### GAP-2 — the "accepted unit contract / dimensional class" does not exist

```text
GAP                        = GAP-2
SEVERITY                   = BLOCKER
AFFECTS                    = unit_requirements (P3), §1.4
                              UNIT_ARITHMETIC_VALIDITY,
                              absolute_delta computability, relative_delta
                              validity, POL-11
RATIFIED_DOCTRINE_CITES    = §1.4 "derived from: typed unit compatibility /
                              dimensional class / accepted unit semantics"
                            P3 "cites the accepted unit contract"
                            §2 "unit_requirements: cites the accepted unit
                              dimensional class"
ACCEPTED_RUNTIME           = book6_definitions.py -> MetricDefinition.unit: str
                            book6_records.py:114 -> MeasurementObservation.unit: str | None
ONLY_ACCEPTED_UNIT_CHECK   = string equality observation.unit != definition.unit
DIMENSIONAL_TAXONOMY       = NONE — grep for dimensional|UnitClass|convertible|
                              unit_compat returns no Book 6 unit taxonomy
```

**The conflict.** The amendment derives arithmetic validity *from the unit
contract* and forbids the rule from redefining it. There is no unit contract.
`unit` is a bare string; equality of strings is the only available
operation. So `UNIT_ARITHMETIC_VALIDITY = DERIVED_FROM_UNIT_CONTRACT` has no
contract to derive from.

**The three honest resolutions, all operator decisions:**

```text
OPTION-2A  A new unit/dimensional contract is IN SCOPE for this amendment.
           Requires a new authority-bearing contract class (unit dimensional
           class + compatibility relation) — a THIRD class beyond the ratified
           2 (ComparisonRule, ChangeObservation), which the readiness record
           states is NONE. This is a governance expansion, not a code task.
OPTION-2B  Arithmetic validity is UNAVAILABLE_BY_ABSENCE: with no unit
           contract, subtraction compatibility and ratio validity cannot be
           established, so absolute_delta is ABSENT (NOT_COMPUTABLE) and
           relative_delta is ABSENT (UNDEFINED) for every comparison.
           Invent-nothing and fail-closed, but the amendment then produces no
           authorized change at all, and the engine has no positive path.
OPTION-2C  The unit contract is DEFERRED to a separate amendment; the
           comparison contract ships referencing a unit_requirements field
           whose values are citations only and are NOT enforced at check 19.
           Risks silently unenforced units.
```

```text
GAP_2_UNRATIFIED_POLICY_NEEDED = TRUE
```

---

#### GAP-3 — the coverage-applicability determination has no derivation rule

```text
GAP                        = GAP-3
SEVERITY                   = BLOCKER
AFFECTS                    = coverage_requirement_status, check 12,
                              coverage_applicability_source_ref (NULL-4/5),
                              COV family, ChangeObservation availability
RATIFIED_DOCTRINE          = P10 "coverage_applicability_resolution_ref cites a
                              derived determination; not authorable"
                            grammar §2 "coverage_requirement_status: REQUIRED,
                              DERIVED upstream"
                            §3.1 UNRESOLVED -> comparison UNAVAILABLE
ACCEPTED_RUNTIME           = MetricDefinition has NO applicability field
                            (measured: metric_id, name, semantic_definition,
                            subject_domain, category, unit, role, window_class,
                            aggregation, denominator_rule,
                            allowed_source_families,
                            required_evidence_semantics, methodology,
                            comparability_class, applies_to_architectures)
                            MeasurementMethodology has NO applicability field
                            (formula, parameters, window_rule, denominator_rule,
                            source_selection, identity_rule,
                            input_methodology_refs, authorized_corpus_row_ids)
PHASE_8_PROHIBITIONS        = no new applicability flag on MetricDefinition;
                              no heuristic; no metric-name matching;
                              no caller override
```

**The analysis.** Phase 8 is decisive and it produces a real finding.
The accepted runtime exposes **no** field from which applicability could be
derived. Every accepted semantic field was inspected: `MeasurementCategory`
has no coverage-bearing member, `denominator_rule` is a free string
(matching it would be exactly the prohibited heuristic), and
`required_evidence_semantics` is the nearest candidate but is also free-form.

**This is the one gap where ratified doctrine already prescribes the answer.**
The `UNRESOLVED` branch is fully specified: grammar §3.1 says `UNRESOLVED`
→ *comparison UNAVAILABLE before any coverage observation semantics are used*,
and grammar §2 says the absent `coverage_applicability_source_ref` means
exactly `NO_UPSTREAM_DETERMINATION_EXISTS`.

So a strictly non-inventing implementation exists: **every comparison
resolves `coverage_requirement_status = UNRESOLVED` until an applicability
derivation is separately ratified.** It invents nothing and it is fail-closed.

That is still an operator decision, because the alternative is to author a
derivation rule:

```text
OPTION-3A  Ship fail-closed: applicability is always UNRESOLVED absent a
           ratified derivation; all comparisons UNAVAILABLE. Invent-nothing.
           Consequence: the amendment has no positive path until a later
           applicability amendment ratifies a derivation.
OPTION-3B  A coverage-applicability derivation is IN SCOPE for this amendment
           and must be authored + ratified BEFORE implementation. It defines
           which accepted MetricDefinition / methodology semantics imply
           coverage, which is squarely governance, not code.
```

```text
GAP_3_UNRATIFIED_POLICY_NEEDED = TRUE (the 3A / 3B choice)
NOTE: 3A is non-inventing but vacuous; 3B is a new governance artifact.
```

---

#### GAP-4 — `comparability_status` and `NOT_COMPARABLE` have no ratified source

```text
GAP                        = GAP-4
SEVERITY                   = BLOCKER
AFFECTS                    = ChangeObservation.comparability_status (REQUIRED),
                              change_kind = NOT_COMPARABLE, check 19,
                              G-5 required test family
RATIFIED_DOCTRINE          = grammar §3 lists `comparability_status` with
                              NO value domain, NO derivation rule, NO source
                            grammar §3 change_kind INCLUDES NOT_COMPARABLE
                            plan G-5 REQUIRES a concrete real test function for
                            "comparability gates" and "NOT_COMPARABLE"
REPLAY_CHECKS_1_TO_19      = contain NO comparability check:
                              1-3 rule, 4-6 baseline, 7 operator, 8-9 refs,
                              10 book2, 11 methodology, 12-16 coverage,
                              17 metric-def, 18 input-methodology, 19 recompute
CHECK_19_DEFINITION        = "recomputes the delta, direction, and change_kind
                              from the canonical unrounded values"
```

**The conflict, stated precisely.** Grammar §3 gives `ChangeObservation` a
**REQUIRED** field `comparability_status` and gives `change_kind` a
**REQUIRED** member `NOT_COMPARABLE`. Neither has a value domain. Worse,
`NOT_COMPARABLE` is **unproducible by any ratified check**: check 19 derives
`change_kind` from *the sign of the canonical unrounded `absolute_delta`*, and
a sign cannot yield `NOT_COMPARABLE`. No check in 1–19 produces it.

**The near-miss that makes this resolvable.** Accepted Book 6 already contains
a genuine, ratified, working comparability mechanism —
`book6_comparability.py` (388 lines):

```text
CorpusVerdict = NOT_COMPARABLE | CONDITIONAL | AS_DISTINCT
FALSE_COMPARISON_CORPUS = 15 ratified rows (FC-01 .. FC-15)
gate_comparison(left_metric_id, right_metric_id) -> CorpusVerdict
corpus_row_for(...) -> CorpusRow  (raises ComparabilityError if ungoverned)
authorize_comparison(...) -> "AUTHORIZED" | ComparabilityError
```

But it is **structurally the wrong construct** for this amendment:

```text
1. SCOPE MISMATCH. CorpusVerdict governs a CROSS-METRIC PAIR
   (chain.executed_transactions.L1 vs ...ROLLUP). A ComparisonRule is
   SINGLE-METRIC TEMPORAL — grammar §2 requires one metric_definition_ref and
   compares a baseline window to a comparison window of the SAME metric.
   A self-comparison (X vs X) has no corpus row.
2. corpus_row_for() FAILS CLOSED ON UNGOVERNED PAIRS. Any self-pair raises
   ComparabilityError. Reusing this gate for temporal comparison would make
   EVERY comparison refuse.
3. THE AMENDMENT NEVER CITES IT. Neither the grammar, the boundary, the plan,
   nor the ratification record mentions CorpusVerdict, the corpus, or
   authorize_comparison. The derivation binding (record §4) contains no
   comparability element.
```

So the accepted corpus is *adjacent* but not *authoritative* for
`comparability_status`. An implementer must choose, and every choice invents:

```text
OPTION-4A  comparability_status is OUT OF SCOPE for the v0.1 implementation:
           the field and the NOT_COMPARABLE member are deferred to an
           amendment that ratifies either (i) a temporal comparability corpus
           or (ii) an explicit mapping from CorpusVerdict. ChangeObservation
           v0.1 omits comparability_status; check 19 cannot emit
           NOT_COMPARABLE; G-5's NOT_COMPARABLE family is deferred.
OPTION-4B  comparability_status is DEFINED NOW, reusing CorpusVerdict as the
           value domain, with a self-pair convention ratified alongside it.
           This is new governance (a new value domain plus a new applicability
           rule) and it changes a REQUIRED field list.
OPTION-4C  comparability_status reuses ComparabilityClass (the accepted
           MetricDefinition.cohort enum). This is a DIFFERENT concept — a
           cohort family, not a comparison outcome — and adopting it would
           silently conflate two ratified vocabularies. NOT RECOMMENDED.
```

```text
GAP_4_UNRATIFIED_POLICY_NEEDED = TRUE
```

---

### 3.3 Gap summary

| Gap | Question | Would coder invent? | Fail-closed escape exists? |
|---|---|---|---|
| GAP-1 | canonical numeric representation | **YES** — a public model type | NO |
| GAP-2 | unit contract / dimensional class | **YES** — a new authority contract | YES (2B, vacuous) |
| GAP-3 | coverage applicability derivation | **YES** — a derivation rule | YES (3A, vacuous) |
| GAP-4 | `comparability_status` domain | **YES** — a new value domain | PARTIAL (4A, defers field) |

```text
NO_POLICY_INVENTION_TEST      = FAIL
GAPS_REQUIRING_OPERATOR_CHOICE = 4
GAPS_WITH_NON_VACUOUS_ESCAPE   = 0
```

Note the pattern: **the only two escape hatches available (2B, 3A) are both
fail-closed and both make the amendment produce zero authorized changes.**
An amendment whose only implementable configurations emit nothing is not
implementation-ready; it is specification-incomplete. That is why this is
HOLD rather than PASS-with-caveats.

---

## 4. Phase 4 — Contract shape review

Shapes are **described, not written**. No code is produced in this session.

### 4.1 `ComparisonRule` — implementable as a closed typed contract

```text
PYDANTIC BASE           = Book6FrozenModel
                          (model_config = ConfigDict(extra="forbid", frozen=True))
FREE STRINGS WHERE AN
ENUM SHOULD EXIST       = NONE FOUND
  delta_operator         -> ratified closed enum (2 members)
  registration_state     -> ratified closed enum (2 members)
  window_compatibility   -> cites accepted WindowClass (7 members, exists)
  missingness_requirements -> cites accepted MissingnessState (exists)
  unit_requirements      -> CITATION ONLY; blocked by GAP-2
  compatible_methodology_refs -> tuple of identities, NO wildcard (P2)
AMBIGUOUS NULLABLES      = 0 (per grammar §8.1; verified against §8.1 table)
  supersedes_ref         -> version-conditional, NULL-8
  valid_time.valid_to    -> OPEN_ENDED only, NULL-9
  coverage_applicability_source_ref -> NULL-4/5
```

**No free string carries authority.** Every authority-bearing field on
`ComparisonRule` is either a ratified enum or a non-authoritative citation.
This is a genuine strength of the ratification and it survives the audit.

**One caveat that is not a gap but must be recorded.** `unit_requirements`
("cites the accepted unit dimensional class") and the P2..P8 fields
(`denominator_requirements`, `cohort_requirements`, `window_compatibility`,
`missingness_requirements`, `output_semantics`) are described in the grammar
as "required, closed" **without enumerated value domains** in the ratified
text. The readiness record reports `POLICY_PARAMETERS_WITH_UNGOVERNED_AUTHORITY
= 0`, which is consistent with them being citations of *accepted* enums
(`WindowClass`, `MissingnessState`, `MeasurementCategory`) rather than new
vocabularies. Implementation should therefore type them as references to
accepted grammar enums and must not mint new members. **This is a
specification-tightening recommendation, not a blocker**, and it is recorded
as REC-1 below.

### 4.2 `ChangeObservation` — implementable, with one field blocked

```text
PYDANTIC BASE           = Book6FrozenModel
IMMUTABILITY            = frozen=True; CO-6 corrections supersede, never
                          overwrite
AUTHORITY-BEARING
CALLER BOOLEANS         = NONE PERMITTED
  current_authority      -> DERIVED by §5 replay; never asserted
  coverage_verdict       -> replayed from a ratified rule; CO-9 forbids
                            self-declaration
  is_ratified            -> DOES NOT EXIST (grammar §2.1 prohibits a
                            self-declared status value granting ratification)
  can_compare            -> DOES NOT EXIST
  coverage_sufficient    -> DOES NOT EXIST
BLOCKED FIELD           = comparability_status (GAP-4)
  -> no ratified value domain; cannot be typed without invention
  -> every OTHER field in grammar §3 has a ratified domain
```

```text
CHANGE_OBSERVATION_FIELDS_RATIFIED = 28 of 29
CHANGE_OBSERVATION_FIELDS_BLOCKED  = 1  (comparability_status, GAP-4)
```

### 4.3 `ComparisonDerivationBinding` — implementable, registry-side

```text
LOCATION                = book6_ratification.py (MODIFIED, not a new module)
IS A PUBLIC CONTRACT?   = NO — per Phase 16 and grammar §4, it is an internal
                          registry-side record, mirroring the accepted
                          DerivationBinding
ELEMENTS                = 7, exactly as ratified in record §4:
  1 rule identity / version / canonical fingerprint
  2 baseline benchmark methodology identity / version / fingerprint
  3 delta operator (closed set)
  4 coverage applicability determination
  5 coverage-sufficiency rule identity / version / fingerprint (where REQUIRED)
  6 metric-definition semantic fingerprint
  7 compatible input methodology policy
DIGEST MECHANISM         = derivation_binding_digest() already exists and is
                          deterministic (sha256 over a JSON list,
                          separators=(",",":"), ensure_ascii=True)
BLOCKED ELEMENT         = element 4 (coverage applicability determination) is
                          blocked by GAP-3
```

### 4.4 Phase 4 verdict

```text
CLOSED_TYPED_CONTRACTS_DERIVABLE  = TRUE (2 of 3 fully; 1 with a blocked field)
FREE_STRING_AUTHORITY_FIELDS       = 0
AMBIGUOUS_NULLABLE_FIELDS          = 0
TRUSTED_CALLER_BOOLEANS            = 0
BLOCKED_BY_GAPS                    = 2  (comparability_status, coverage
                                        applicability determination)
REC-1 (tightening)                 = P2..P8 value domains should be cited
                                    accepted enums, not minted members
```

---

## 5. Phase 5 — Comparison rule registry design

### 5.1 Required governance (ratified, grammar §2.2)

```text
REGISTRATION != RATIFICATION
OBJECT STATUS IS NOT AUTHORITY
COMPARISON_RULE_RATIFICATION_AUTHORITY = OPERATOR_ONLY,
  established BY THIS AMENDMENT using a D6M-3-CONSISTENT pattern;
  D6M-3 does not grant, extend, or lend this authority
MUTATED CONTENT UNDER A BOUND IDENTITY REJECTS
SUPERSESSION DOES NOT INHERIT
AT BOOTSTRAP: COMPARISON_RULES_RATIFIED = 0
```

### 5.2 Accepted mechanisms available for reuse (measured)

| Mechanism | Module | Reusable? |
|---|---|---|
| `RatificationRecord` | `book6_ratification.py` | **YES** — same shape needed |
| `DerivationBinding` | `book6_ratification.py` | **YES** — mirror for `ComparisonDerivationBinding` |
| `derivation_binding_digest()` | `book6_ratification.py` | **YES** — deterministic digest already proven |
| `RatificationLedger(registry_identity)` | `book6_ratification.py` | **YES** — generic, not domain-bound |
| `RatificationSeal` | `book6_ratification.py` | **YES** |
| `CoverageRuleRegistry` | `book6_coverage_rules.py` | **YES** — closest structural analogue |
| `StateRuleRegistry` | `book6_states.py` | **NO — see 5.4** |
| `Book6MethodologyRegistry` | `book6_methodology.py` | **YES** — strongest pattern (see §7) |

### 5.3 Design conclusion

```text
PROPOSED                = a NEW ComparisonRuleRegistry in
                          book6_comparison_rules.py
REUSE                   = RatificationLedger, RatificationRecord,
                          RatificationSeal, DerivationBinding pattern
MUST_NOT_REUSE          = StateRuleRegistry (see 5.4)
MUST_NOT_OVERLOAD       = CoverageRuleRegistry (its identity is
                          "csia:book6:coverage-rule-registry" and its scope
                          field is scope_metric_id; a comparison rule is a
                          different authority object with a different
                          ratification trigger)
BOOTSTRAP_COUNT         = 0
REGISTRATION_EFFECT     = none (register() must accept an UNRATIFIED rule and
                          confer nothing)
RATIFICATION_TRIGGER    = operator-only; a new registry method that writes a
                          RatificationRecord bound to the rule identity,
                          version and canonical fingerprint
MUTATED_CONTENT         = rejected (content digest fixed at first registration,
                          exactly as Book6MethodologyRegistry._fingerprints
                          does today)
SUPERSESSION            = does not inherit; version N+1 requires a NEW
                          RatificationRecord
REGISTRY_IDENTITY       = "csia:book6:comparison-rule-registry" (NEW string;
                          recorded here for the operator to ratify, not
                          invented by the implementer)
```

### 5.4 Why `StateRuleRegistry` must not be overloaded

```text
StateRule.benchmark_methodology_ref: str | None   EXISTS
BUT:
  - it is a STATE-rule concept (StateName.HIGER_THAN_OWN_HISTORY,
    C_THRESHOLD_BENCHMARK, ...), not a comparison authority
  - RuleRatificationStatus lives in book6_states.py:145 and is a
    state-specific status vocabulary
  - reusing it would make a COMPARISON rule look STATE-authorized and would
    silently couple COMPARISON_RULE_RATIFICATION to STATE ratification
  - the ratified separation COMPARISON_RULE_RATIFIED != COVERAGE_RULE_RATIFIED
    shows this program deliberately keeps rule authorities distinct; adding
    a third shared registry would work against that discipline
VERDICT: SEPARATE REGISTRY REQUIRED
```

### 5.5 Phase 5 verdict

```text
REGISTRY_DESIGN_READY   = TRUE
REUSE_SAFE             = TRUE  (RatificationLedger family is generic)
OVERLOAD_RISKS         = 2  (StateRuleRegistry, CoverageRuleRegistry) — both
                            avoided by design
ONE_STRING_NEEDS_OPERATOR_RATIFICATION = registry identity literal
```

---

## 6. Phase 6 — Baseline benchmark seam

### 6.1 What exists in code

```text
EXISTS:
  GrammarCategory.BENCHMARK                       (a GrammarCategory VALUE)
  StateRule.benchmark_methodology_ref: str | None (a state-rule CITATION)
  BENCHMARK_RULES_RATIFIED = 0                    (governance state)

DOES NOT EXIST (measured by grep over all 19 book6_* modules):
  rolling_mean
  rolling_median
  prior_comparable_window
  baseline_epoch
  historical_distribution
  ANY benchmark-rule registry, ratification record, or resolver
```

### 6.2 What exists only in planning doctrine

The ratified namespace
`PRIOR_COMPARABLE_WINDOW | ROLLING_MEAN | ROLLING_MEDIAN |
HISTORICAL_DISTRIBUTION | BASELINE_EPOCH` appears **only in the amendment
documents**. It has no runtime counterpart of any kind.

```text
CRITICAL STATEMENT: this review does NOT claim an existing runtime authority
mechanism for benchmarks. None exists. Grammar §2 requires
baseline_selection_methodology_ref to be "an ACCEPTED Book 6 benchmark rule
... individually operator-ratified (D6M-3)".
```

### 6.3 What this amendment must implement vs what would exceed it

```text
MUST IMPLEMENT (in scope):
  a BenchmarkRule contract (namespace enum, identity, version, fingerprint)
  a BenchmarkRuleRegistry with register/supersede + operator-only ratification
  a baseline RESOLVER that turns a benchmark rule + a measurement set into a
  baseline measurement selection
  a canonical bootstrap count of 0, failing CLOSED when no rule is ratified

WOULD EXCEED THE AMENDMENT:
  ratifying any benchmark rule (explicitly NO BENCHMARK-RULE RATIFICATION)
  adding a new benchmark kind outside the ratified 5-member namespace
  any empirical baseline calibration
```

### 6.4 The honest consequence

```text
BENCHMARK_RULES_RATIFIED = 0 (accepted limitation, plan §13)
=> every ComparisonRule fails check 4/5/6 at first use
=> ZERO authorized ChangeObservations until the operator separately ratifies
   at least one benchmark rule
```

This is a **bounded in-amendment implementation path** and it satisfies the
Phase 29 criterion *"or an explicitly bounded in-amendment implementation path
exists"*. The path is bounded because the contract shape is fully ratified
(the 5-member namespace), the registry pattern is accepted and reusable, and
the fail-closed behaviour is already the ratified norm for coverage rules.

```text
BENCHMARK_RUNTIME_PATH_SUFFICIENT = TRUE
  (bounded: build the registry + resolver, ratified count stays 0,
   comparisons refuse until a benchmark rule is separately ratified)
NOT a blocker. Recorded as a known consequence, not a defect.
```

---

## 7. Phase 7 — MetricDefinition content binding

### 7.1 The accepted limitation being honoured

```text
RATIFIED LIMITATION (plan §13, record §9)
  = "no first-class MetricDefinition versioning - metric definition content
     is fingerprint-bound at ratification instead"
MetricDefinition HAS     = metric_id, name, semantic_definition,
                           subject_domain, category, unit, role, window_class,
                           aggregation, denominator_rule, allowed_source_families,
                           required_evidence_semantics, methodology,
                           comparability_class, applies_to_architectures
MetricDefinition LACKS   = version, fingerprint  (by accepted design)
```

### 7.2 The accepted pattern to imitate (verbatim, measured)

`book6_methodology.py` already solves exactly this problem for
`MeasurementMethodology`:

```text
def canonical_methodology_spec(methodology) -> str:
    values = {
        "methodology_ref": ..., "version": ..., "formula": ...,
        "parameters": sorted(...), "window_rule": ..., "filters": sorted(...),
        "denominator_rule": ..., "source_selection": ..., "identity_rule": ...,
        "input_methodology_refs": sorted(...),
        "authorized_corpus_row_ids": sorted(...),
    }
    if set(values) != set(METHODOLOGY_CANONICAL_FIELDS):   # <-- DRIFT GUARD
        raise MethodologyRegistryError(...)
    return json.dumps([values[f] for f in METHODOLOGY_CANONICAL_FIELDS],
                      separators=(",", ":"), ensure_ascii=True)

def methodology_fingerprint(methodology) -> str:
    return hashlib.sha256(canonical_methodology_spec(...).encode("utf-8")).hexdigest()
```

### 7.3 Design for `MetricDefinition` (described, not written)

```text
FUNCTION        = canonical_metric_definition_spec(md) -> str
                 + metric_definition_fingerprint(md) -> str
LOCATION        = book6_definitions.py (a FUNCTION ONLY — the class is NOT
                 modified; no new field, no version, no fingerprint attribute)
FIELD SELECTION = EVERY semantic field of MetricDefinition, enumerated in a
                 module constant METRIC_DEFINITION_CANONICAL_FIELDS
DRIFT GUARD     = if set(values) != set(METRIC_DEFINITION_CANONICAL_FIELDS):
                     raise — identical to the accepted methodology pattern.
                 THIS is the "cannot silently omit a field" mechanism.
DETERMINISM     = json.dumps(list, separators=(",",":"), ensure_ascii=True)
                 over a FIXED field order -> dictionary/key ordering in the
                 source object cannot alter the digest
STABILITY       = pure function of the field values; no id(), no is, no
                 process state, no clock
ORDERED FIELDS  = sorted() for every collection-valued field
                 (applies_to_architectures, allowed_source_families,
                  required_evidence_semantics)
SEMANTIC MUTATION -> different digest   (any changed value changes the list)
SAME SEMANTICS     -> same digest        (rebuild-from-scratch equality)
NON-SEMANTIC
DISPLAY METADATA   -> NOT IN SCOPE; MetricDefinition has no display field,
                      so the concern is vacuous for this class. The grammar's
                      display-independence rule (CO-11) applies to
                      ChangeObservation.display_metadata, which is explicitly
                      EXCLUDED from check 3's fingerprint scope and from
                      check 19's inputs.
```

### 7.4 Phase 7 verdict

```text
METRIC_DEFINITION_FINGERPRINT_STRATEGY_READY = TRUE
STRATEGY_SOURCE                              = ACCEPTED PATTERN (imitation)
INVENTION REQUIRED                           = NONE
MetricDefinition PUBLIC CONTRACT CHANGED     = NO (function only)
AMENDMENT REQUIRED                           = NO (no versioning amendment)
```

**This gap is closed.** Phase 7 is fully satisfiable by imitation of an
accepted, adversarially-hardened mechanism (R1-D1, R2-D1).

---

## 8. Phase 8 — Coverage applicability implementation

**This phase produced GAP-3. It is restated here in its Phase 8 form; the
full argument is in §3.2.**

```text
QUESTION                     = can the accepted runtime produce
                               REQUIRED | NOT_APPLICABLE | UNRESOLVED without
                               inventing policy?
ANSWER                       = NO derivation is available; only the
                               UNRESOLVED branch is specified
EVIDENCE                     = MetricDefinition: no applicability field
                               MeasurementMethodology: no applicability field
                               MeasurementCategory: no coverage-bearing member
                               denominator_rule / required_evidence_semantics:
                                 FREE STRINGS -> matching them is a heuristic
CORRECT RESULT               = UNRESOLVED, with coverage_applicability_source_ref
                               ABSENT meaning exactly
                               NO_UPSTREAM_DETERMINATION_EXISTS
                               (grammar §2, §3.1; NULL-4/NULL-5)
PROHIBITIONS HONOURED        = no new applicability flag on MetricDefinition
                               no heuristic
                               no metric-name matching
                               no caller override
```

```text
COVERAGE_APPLICABILITY_RUNTIME_AUDIT = FAIL (no derivation source)
COVERAGE_RUNTIME_PATH_SUFFICIENT    = FALSE as a NON-VACUOUS path
                                       (TRUE only as the vacuous 3A)
```

---

## 9. Phase 9 — Coverage rule runtime dependency

### 9.1 Accepted runtime (measured)

```text
book6_coverage_rules.py (316 lines):
  CoverageRuleRegistry(registry_identity = "csia:book6:coverage-rule-registry")
    register()   -> REJECTS any non-UNRATIFIED rule
    supersede()  -> ratification does NOT carry forward
  CoverageSufficiencyAttestation
  CoverageReport  -> has a partition validator
book6_ratification.py:
  RatificationLedger, RatificationRecord, RatificationSeal
book6_definitions.py:
  CoverageObservation(observed_fraction: float, basis, sufficiency_rule_ref,
                     valid_time)  -- NO sufficiency field, BY DESIGN
  CoverageRuleRatificationStatus = UNRATIFIED | RATIFIED | SUPERSEDED
  COVERAGE_OBSERVATION_IS_NOT_SUFFICIENCY   (constant, present)
  CoverageSufficiencyRule validator FORBIDS constructing RATIFIED
```

### 9.2 Capability check against the amendment's needs

| Need | Supported today? | Note |
|---|---|---|
| rule resolution | **YES** | `CoverageRuleRegistry` |
| ratification record | **YES** | `RatificationLedger` family |
| metric scope match | **YES** | `CoverageSufficiencyRule.scope_metric_id` |
| currentness | **YES** | supersede + status; the `require_comparison_authority` pattern is the model |
| sufficiency replay | **PARTIAL** | the *verdict* replay for a `ChangeObservation` is new work, but it consumes `CoverageReport` and adds no policy |
| mutation-free | **YES** | no mutation required |

### 9.3 Constraints this phase must honour

```text
CANONICAL COVERAGE RULES RATIFIED = 0
=> the registry exists, resolves nothing, and every sufficiency replay
   returns UNKNOWN / fail-closed. This is CORRECT and REQUIRED.
NO COVERAGE RULE MAY BE CREATED JUST SO TESTS PASS.
SYNTHETIC FIXTURES ONLY  -> tests must use locally-constructed, clearly
                            non-canonical rule objects; none may be
                            presented as ratified corpus data.
```

### 9.4 Phase 9 verdict

```text
COVERAGE_RULE_REGISTRY_REUSABLE    = TRUE
COVERAGE_SUFFICIENCY_REPLAY        = IMPLEMENTABLE (no policy invention)
COVERAGE_RUNTIME_PATH_SUFFICIENT    = TRUE for the RULE side
COVERAGE_RUNTIME_PATH_SUFFICIENT    = FALSE for the APPLICABILITY side (GAP-3)
```

The coverage **rule** runtime is in good shape. The coverage **applicability**
determination is the gap.

---

## 10. Phase 10 — Canonical numeric representation

**This phase produced GAP-1. Full argument in §3.2.**

```text
AUDIT RESULT (measured):
  book6_records.py:113   MeasurementObservation.value : float | None
  book6_definitions.py   MetricDefinition.unit        : str
  book6_records.py:114   MeasurementObservation.unit  : str | None
  book6_core.py          RatioResult numerator/denominator/ratio : float
  book6_core.py:181      float("nan") injected as a denominator SENTINEL
  book6_core.py          RatioResult.denominator_state, .is_undefined
  Decimal usage          book5_core, book5_lineage, book5_provenance,
                         book5_records  -- NEVER in a book6_* module
  isclose / approx usage NONE anywhere in book6 source
```

```text
DOCTRINE REQUIRES  = "canonical UNROUNDED value" + "exact canonical equality"
                     (grammar §1.2) and the separation
                     DISPLAYED EQUALITY != MEASURED EQUALITY (§4)
BINARY float       = CANNOT deliver exact equality on the represented real
                     number, and its own arithmetic result is a rounded
                     double
=> A concrete numeric-representation decision is needed and is NOT ratified.
   It is NOT a coding detail: it changes the type of an accepted public
   field, or adds a new contract class.

NUMERIC_REPRESENTATION_SUFFICIENT = FALSE
STATUS                             = BLOCKER / OPERATOR DECISION (GAP-1)
```

**Explicitly NOT done in this review:** no epsilon was introduced, no
`math.isclose`, no tolerance, no `Decimal`/`Fraction` default, and no
reliance on float display behaviour.

---

## 11. Phase 11 — Closed delta operator execution

```text
EXPOSED OPERATORS     = {ABSOLUTE_DELTA, RELATIVE_DELTA}  (ratified, 2 only)
IMPLEMENTATION FORM   = a Python enum on the closed set + a dispatch that is
                         a total function over exactly those two members
THIRD OPERATOR        = IMPOSSIBLE to express: a Python enum rejects any
                         value outside its members at construction, so there
                         is no "unknown operator" runtime branch
```

```text
NEGATIVE CASE                          EXPECTED
custom formula string ("a - b * 2")  -> validation failure at construction
                                         (no formula field exists)
unknown enum value ("PERCENT_CHANGE") -> validation failure (enum member
                                         does not exist)
callback (a callable)               -> validation failure (no callable-typed
                                         field exists)
expression language                 -> ABSENT: no parser, no evaluator, no
                                         expression type anywhere in the module
eval / exec                         -> ABSENT: must be asserted mechanically
                                         by test (test module below)
```

```text
CLOSED_OPERATOR_EXECUTION_READY = TRUE
INVENTION REQUIRED             = NONE
ENFORCEMENT MECHANISM           = Python enum totality + extra="forbid"
TEST REQUIREMENT                = a mechanical scan asserting the strings
                                  "eval(" and "exec(" do not appear in any
                                  book6_change_engine.py source
```

---

## 12. Phase 12 — Fixed direction law

```text
RATIFIED LAW (grammar §1.2)
  DIRECTION_DERIVATION_RULE = FIXED / NON-CONFIGURABLE
  absolute_delta > 0 -> INCREASE
  absolute_delta < 0 -> DECREASE
  absolute_delta == 0 -> NO_CHANGE  (exact canonical equality)
NOT a determinant: display rounding, relative magnitude, caller tolerance,
  materiality, significance, precision cutoff
```

```text
direction_derivation FIELD  = MUST NOT EXIST
tolerance FIELD             = MUST NOT EXIST
epsilon FIELD               = MUST NOT EXIST
rounding-based comparison   = MUST NOT EXIST
Direction source            = the canonical absolute_delta VALUE, recomputed
                              at check 19 from the canonical inputs
```

```text
NEGATIVE-TEST PLAN
  constructor rejects direction_derivation   (extra="forbid")
  constructor rejects epsilon                 (extra="forbid")
  constructor rejects tolerance              (extra="forbid")
  model_copy cannot introduce them           (frozen model; copy of a valid
                                              model has the same field set)
  deserialization rejects them               (extra="forbid" applies on load)
  display precision cannot alter change_kind (two ChangeObservations identical
                                              except display_metadata must
                                              produce the same change_kind and
                                              the same check-19 verdict)
  a negative relative delta is a DECREASE   (not an INCREASE, not |value|)
FIXED_DIRECTION_READY = TRUE
INVENTION REQUIRED   = NONE
```

---

## 13. Phase 13 — Zero baseline

```text
RATIFIED LAW (grammar §1.3)
  ZERO_BASELINE_POLICY = FIXED_FAIL_CLOSED
  baseline == 0:
      absolute_delta  computed normally WHERE THE UNIT SUPPORTS SUBTRACTION
      relative_delta  UNDEFINED / ABSENT
  NEVER: 0, infinity, NaN, capped value, 100%, percentage convention
```

```text
DESIGN
  absolute_delta  -> present, subject to GAP-2 (unit compatibility)
  relative_delta  -> the field is None; the undefined condition is exposed
                     EXPLICITLY via the ratified change_kind =
                     CHANGE_UNDEFINED, never via a sentinel numeric value
NO ZeroDivisionError MAY LEAK AS SEMANTICS
NO float("inf"), NO float("nan"), NO 0.0 placeholder
NO capping
```

**Contrast with accepted Book 6, and why this matters.** `book6_core.py:181`
injects `float("nan")` as a denominator sentinel and `RatioResult` carries
`denominator_state` + `is_undefined`. That is an *accepted* pattern for the
ratio kernel. The amendment must **not** copy it for `relative_delta`,
because grammar §3 says `relative_delta` ABSENT means `UNDEFINED` and §1.3
forbids `NaN` as a value. The two designs are deliberately different, and
the difference is a **testable** assertion.

```text
ZERO_BASELINE_READY  = TRUE (law fully ratified)
CONDITIONAL          = absolute_delta computability depends on GAP-2
INVENTION REQUIRED  = NONE
```

---

## 14. Phase 14 — Unit arithmetic

**This phase produced GAP-2. Full argument in §3.2.**

```text
CURRENT BOOK 6 UNIT REPRESENTATION
  MetricDefinition.unit          : str          (free string, no taxonomy)
  MeasurementObservation.unit    : str | None   (free string)
  ONLY ACCEPTED UNIT CHECK      : observation.unit != definition.unit
                                   (STRING EQUALITY)
  DIMENSIONAL CLASS             : DOES NOT EXIST
  UNIT COMPATIBILITY RELATION   : DOES NOT EXIST
  CONVERTIBILITY                : DOES NOT EXIST
```

```text
WHAT IMPLEMENTATION MUST PROVE (ratified):
  subtraction compatible        -> needs a dimensional-class relation
  relative ratio semantically
    valid                       -> needs the same relation
  denominator/unit compatibility -> needs a denominator rule bound to units
NONE OF THESE HAS A SOURCE.
```

```text
MUST NOT BE ADDED (ratified prohibition, §2.1 / §1.4)
  unit_divisibility_policy   -- the field must NOT EXIST
  a caller override          -- a caller may not declare units compatible
  a rule redefinition of unit mathematics
=> POL-11 ("a rule attempting to authorize incompatible units: the unit
   contract governs and the attempt is rejected") is UNTESTABLE as written,
   because there is no unit contract for it to govern with.

UNIT_CONTRACT_SUFFICIENT = FALSE
STATUS                    = BLOCKER / OPERATOR DECISION (GAP-2)
```

---

## 15. Phase 15 — Nullable / absence model

The 36 audited nullable/optional fields must become **runtime constraints**,
not prose. Accepted `Book6FrozenModel` already gives the enforcement
substrate: `ConfigDict(extra="forbid", frozen=True)` plus
`@model_validator(mode="after")`, which is exactly how
`MeasurementObservation._check_value_and_missingness` already refuses a value
under a value-forbidden missingness state.

### 15.1 Named-discriminator constraints (grammar §3.1 + §2 + §8.1)

```text
FIELD                              RULE                              NULL
---------------------------------------------------------------------------------------
coverage_requirement_status        tri-state, REQUIRED               —
coverage_applicability_source_ref  REQUIRED iff status in             NULL-4
                                   {REQUIRED, NOT_APPLICABLE};
                                   ABSENT iff status == UNRESOLVED
                                   (absent means ONLY
                                   NO_UPSTREAM_DETERMINATION_EXISTS)
                                   status in {REQUIRED,NOT_APPLICABLE}
                                   and ref ABSENT -> INVALID
coverage_observation_state         REQUIRED discriminator             R-3
                                   {PRESENT, UNAVAILABLE, NOT_APPLICABLE}
coverage_observation_ref           REQUIRED iff state == PRESENT;     —
                                   ABSENT iff UNAVAILABLE or
                                   NOT_APPLICABLE
coverage_verdict                   replayed from a ratified rule;    CO-9
                                   never self-declared
supersedes_ref                     version==1 -> ABSENT;              NULL-8
                                   version>1  -> REQUIRED (absent
                                   is rejected)
valid_time.valid_to                ABSENT means OPEN_ENDED /         NULL-9
                                   STILL VALID UNTIL SUPERSEDED OR
                                   WITHDRAWN AND NOTHING ELSE
absolute_delta                     ABSENT means NOT_COMPUTABLE,      §3
                                   NEVER 0
relative_delta                     ABSENT means UNDEFINED,           §3/§1.3
                                   NEVER 0, inf, NaN, capped
current_authority                  DERIVED, never asserted            §3
```

### 15.2 Enforceability

```text
MECHANISM          = @model_validator(mode="after") on the frozen base,
                     the SAME mechanism already accepted in
                     book6_records.py
UNCONSTRUCTABLE    = YES for every combination above, because each is a
                     cross-field conditional the validator can evaluate
PROSE-ONLY FIELDS  = 0
AMBIGUOUS_NULLABLES= 0 (per ratified §8.1, independently re-checked here)

SPECIFIC ENFORCEMENTS
  state == PRESENT and ref is None            -> reject
  state != PRESENT and ref is not None        -> reject
  status == UNRESOLVED and source_ref is set  -> reject
  status != UNRESOLVED and source_ref is None -> reject
  version == 1 and supersedes_ref is set      -> reject
  version >  1 and supersedes_ref is None     -> reject
  change_kind == NO_CHANGE and absolute_delta
    is None                                    -> reject (NO_CHANGE is an
                                                 exact-equality claim, so it
                                                 requires a value)
  change_kind == INCREASE/DECREASE and
    absolute_delta is None                     -> reject
  change_kind == CHANGE_UNDEFINED and
    relative_delta is not None                 -> reject
```

```text
NULLABLE_RUNTIME_CONSTRAINT_READY = TRUE
INVENTION REQUIRED                = NONE
DEPENDENCY                        = GAP-1 (a NO_CHANGE assertion needs an
                                    equality semantics decision) and
                                    GAP-2 (absolute_delta computability)
```

---

## 16. Phase 16 — Derivation binding implementation

### 16.1 Design (described, not written)

```text
CLASS            = ComparisonDerivationBinding
IS PUBLIC
CONTRACT?        = NO  — it is a registry-side record, not a caller-facing
                     contract class. This preserves the ratified count of
                     authority-bearing contract classes at exactly 2
                     (ComparisonRule, ChangeObservation), with the hidden
                     third = NONE.
LOCATION         = book6_ratification.py  (MODIFIED, adjacent to the accepted
                     DerivationBinding — NOT a new module)
CONSTRUCTED BY   = the ComparisonRuleRegistry AT THE MOMENT OF OPERATOR
                     RATIFICATION, and nowhere else
ACCEPTED FROM
A CALLER?        = NO. A caller-built binding is never authoritative. The
                     registry builds it from the rule object + the resolved
                     dependencies, then stores its digest.
HOW authorize()
OBTAINS IT       = by re-resolving the rule identity/version and re-deriving
                     the binding digest, then comparing it to the digest
                     recorded at ratification. Mismatch -> current_authority
                     FALSE (never a silent re-binding: grammar CO-10
                     NO_LATE_BOUND_DERIVATION)
```

### 16.2 The seven ratified elements and their availability

| # | Element | Source available? |
|---|---|---|
| 1 | rule identity / version / canonical fingerprint | YES — §7 fingerprint pattern |
| 2 | baseline benchmark methodology identity / version / fingerprint | YES once `book6_benchmarks.py` exists (§6) |
| 3 | delta operator (closed set) | YES — ratified enum |
| 4 | **coverage applicability determination** | **NO — GAP-3** |
| 5 | coverage-sufficiency rule identity / version / fingerprint | YES — `CoverageRuleRegistry` (§9) |
| 6 | metric-definition semantic fingerprint | YES — §7 |
| 7 | compatible input methodology policy | YES — P2 allow-list, no wildcard |

```text
BINDING_ELEMENTS_RATIFIED          = 7
BINDING_ELEMENTS_IMPLEMENTABLE     = 6
BINDING_ELEMENTS_BLOCKED           = 1  (element 4, GAP-3)
DIGEST_MECHANISM                   = derivation_binding_digest() (accepted)
NO_CALLER_BUILT_AUTHORITY_BINDING  = ENFORCED BY DESIGN
```

```text
DERIVATION_BINDING_DESIGN_READY = TRUE except element 4
INVENTION REQUIRED             = NONE beyond GAP-3
```

---

## 17. Phase 17 — Nineteen-check replay map

Every check must be **independently falsifiable**. An aggregate
`validate_all()` that returns one boolean is explicitly insufficient: each
check gets its own function, its own failure type, and its own negative test.
`authorize_change_observation()` (§19) is a thin dispatcher over these 19 and
returns a per-check result structure, not a bare boolean.

Module: `book6_change_engine.py`. Test module:
`test_book6_change_engine.py` + `test_book6_amendment_adversarial.py`.

| # | Check | Implementing function | Input | Failure type | Negative test (falsifier) | Traceability family | Blocked |
|---|---|---|---|---|---|---|---|
| 1 | rule identity + version | `check_rule_identity()` | rule object, registry | `ComparisonRuleError` | rule not in registry; version mismatch | RULE-GOV | — |
| 2 | operator-ratification binding | `check_rule_ratified()` | rule, `RatificationLedger` | `ComparisonRuleError` | registered but never ratified; ledger seal absent | RULE-GOV | — |
| 3 | rule canonical content fingerprint | `check_rule_fingerprint()` | rule, bound digest at ratification | `ComparisonRuleError` | mutate a semantic field, keep the id | FP-1 | — |
| 4 | baseline methodology identity + version | `check_baseline_identity()` | rule, `BenchmarkRuleRegistry` | `BenchmarkRuleError` | benchmark rule absent (count is 0) | BASE | — |
| 5 | baseline methodology fingerprint | `check_baseline_fingerprint()` | benchmark rule, bound digest | `BenchmarkRuleError` | same identity, changed content | FP-2 | — |
| 6 | baseline methodology current authority | `check_baseline_current()` | benchmark rule, ratification ledger | `BenchmarkRuleError` | benchmark rule superseded or invalidated | BASE | — |
| 7 | closed delta operator validity | `check_delta_operator()` | `delta_operator` enum | `ComparisonRuleError` | `"PERCENT_CHANGE"`; a formula string; a callable | OP-CLOSED | — |
| 8 | baseline measurement refs | `check_baseline_refs()` | resolved baseline refs | `ChangeEngineError` | empty tuple; dangling id | CHG | — |
| 9 | comparison measurement refs | `check_comparison_refs()` | resolved comparison refs | `ChangeEngineError` | empty tuple; dangling id | CHG | — |
| 10 | input measurement Book 2 current authority | `check_book2_authority()` | `MeasurementObservation` refs, Book 2 | `ChangeEngineError` | observation whose Book 2 claim lost authority | CHG | — |
| 11 | input methodology compatibility | `check_methodology_compatibility()` | obs methodology ids, rule allow-list | `ChangeEngineError` | methodology not in `compatible_methodology_refs`; wildcard attempted | METH | — |
| 12 | coverage applicability resolution | `check_coverage_applicability()` | metric definition + methodology semantics | `CoverageRuleError` | no derivation exists -> must yield UNRESOLVED | COV | **GAP-3** |
| 13 | coverage-sufficiency rule ref (where REQUIRED) | `check_coverage_rule_ref()` | rule ref, resolved rule | `CoverageRuleError` | status REQUIRED but ref null; ref mismatched | COV | — |
| 14 | coverage-rule ratification + currentness | `check_coverage_rule_ratified()` | `CoverageRuleRegistry`, ledger | `CoverageRuleError` | canonical count is 0 -> fail closed | COV | — |
| 15 | coverage scope match | `check_coverage_scope()` | rule `scope_metric_id`, metric id | `CoverageRuleError` | rule scoped to another metric | COV | — |
| 16 | deterministic coverage verdict | `check_coverage_verdict()` | `CoverageObservation`, rule fraction | `CoverageRuleError` | caller-declared verdict differs from replayed verdict | COV | — |
| 17 | metric-definition semantic content match | `check_metric_definition_match()` | live `MetricDefinition`, bound fingerprint | `ComparisonRuleError` | definition mutated after ratification | FP-3 | — |
| 18 | compatible input methodology policy match | `check_input_methodology_policy()` | `compatible_input_methodology_policy` | `ComparisonRuleError` | policy redefinition attempt (P9) | METH | — |
| 19 | deterministic change recomputation | `check_change_recomputation()` | canonical inputs, canonical numeric type | `ChangeEngineError` | supplied `change_kind`/deltas disagree with recomputation | CHG, DIR, ZB, UNIT | **GAP-1, GAP-2** |

```text
CHECKS_TOTAL                    = 19
CHECKS_INDEPENDENTLY_FALSIFIABLE = 19
CHECKS_IMPLEMENTABLE            = 16
CHECKS_BLOCKED_BY_GAPS          = 2  (check 12 -> GAP-3; check 19 -> GAP-1,
                                       GAP-2)
CHECKS_FULLY_IMPLEMENTABLE      = 17  (19 minus check 19's numeric dependency;
                                       check 12 fails closed under GAP-3
                                       OPTION-3A)
AGGREGATE validate_all() ONLY   = REJECTED BY DESIGN
```

**Note on check 19 and GAP-4.** Check 19 recomputes `change_kind` from the
sign of `absolute_delta`. It can therefore produce `INCREASE`, `DECREASE`,
`NO_CHANGE` and (subject to GAP-1's equality decision) `CHANGE_UNDEFINED`.
It **cannot** produce `NOT_COMPARABLE`, and it is not required to — but no
*other* ratified check produces it either. See GAP-4.

---

## 18. Phase 18 — ChangeObservation creation path

### 18.1 Division of labour

```text
CALLER SUPPLIES (raw intent + input refs ONLY)
  change_observation_id
  subject_ref
  metric_definition_ref
  comparison_rule_ref
  baseline_selection_methodology_ref   (a citation; it is resolved, not trusted)
  baseline_measurement_refs
  comparison_measurement_refs
  coverage_observation_ref            (iff the caller holds an observation)
  valid_time / observed_at
  display_metadata                    (PRESENTATION ONLY, CO-11)

ENGINE COMPUTES (never caller-supplied)
  resolved baseline                    (from the benchmark rule)
  comparison set
  comparability                        (BLOCKED - GAP-4)
  absolute_delta
  relative_delta
  change_kind                          (from the sign of canonical absolute_delta)
  coverage_requirement_status          (derived; GAP-3)
  coverage_observation_state           (derived discriminator)
  coverage_verdict                     (replayed)
  derivation_binding_ref               (registry-derived)
  current_authority                    (replayed; never asserted)
```

```text
CALLER MUST NOT AUTHORITATIVELY SUPPLY
  computed delta            -> REJECTED (extra="forbid")
  change_kind               -> REJECTED
  current_authority         -> REJECTED
  coverage verdict          -> REJECTED
  ratified status           -> REJECTED
```

### 18.2 The testing escape hatch (explicitly bounded)

If the API accepts `expected_*` values for test ergonomics, they are
**recomputed and compared**, never trusted:

```text
construct_change_observation(..., expected_change_kind=..., expected_absolute_delta=...)
  -> the engine computes its own values,
  -> compares them to the expected values,
  -> a MISMATCH raises (never silently adopts the caller's value),
  -> the stored record carries the ENGINE's values.
TEST OBLIGATION: one test must prove that supplying a wrong expected value
  raises rather than being persisted.
```

```text
CHANGE_OBSERVATION_CREATION_PATH_READY = TRUE
BLOCKED                               = comparability_status (GAP-4)
```

---

## 19. Phase 19 — Current authority replay

```text
ENTRY POINT   = authorize_change_observation(change_observation_id, registries)
BEHAVIOUR     = re-runs ALL NINETEEN checks at the moment of use
NO CACHED
TRUE AUTHORITY= FORBIDDEN. There is no memoised "it was authorized once"
                shortcut. `current_authority` is a property of THIS call.
HISTORY       = preserved and queryable. `record_state` moves to
                SUPERSEDED / WITHDRAWN / INVALIDATED; the object is never
                deleted and never rewritten (CO-6 IMMUTABLE_HISTORY).
DECAY         = if ANY dependency decays (benchmark rule superseded,
                comparison rule superseded, metric definition content
                changed, coverage rule withdrawn, Book 2 authority lost):
                    current_authority = FALSE
                the historical ChangeObservation remains intact and
                continues to report what it reported when derived (CO-10
                NO_LATE_BOUND_DERIVATION - it does not silently re-derive)
RETURN         = a per-check result structure:
                { check_number, passed, failure_type, detail } x 19
                plus the derived current_authority
RATIFIED
SEPARATION     = RULE RATIFIED != CHANGE EXISTS
                CHANGE RECORD EXISTS != CURRENTLY AUTHORITATIVE
                CHANGE RECORD SELF-STATUS != AUTHORITY
```

```text
CURRENT_AUTHORITY_REPLAY_READY = TRUE
CACHE-BYPASS POSSIBLE          = NO
HISTORY MUTATION POSSIBLE      = NO
```

---

## 20. Phase 20 — Book 7 seam implementability

**No Book 7 code is written, imported, or referenced. Book 6 must not import
Book 7. No reverse dependency.**

### 20.1 Reference surface Book 6 must expose (read-only)

| Book 7 needs | Book 6 field / derivation | Available? |
|---|---|---|
| `change_observation_id` | `ChangeObservation.change_observation_id` | YES |
| comparison rule ref | `.comparison_rule_ref` (id) | YES |
| comparison rule version | via the rule registry | YES |
| comparison rule fingerprint | via `canonical_comparison_rule_spec()` (§7 pattern) | YES |
| coverage requirement | `.coverage_requirement_status` | YES (value blocked by GAP-3) |
| coverage verdict | `.coverage_verdict` (replayed) | YES |
| valid time | `.valid_time` (bitemporal) | YES |
| authority resolution | `authorize_change_observation()` (§19) | YES |

### 20.2 Seam contract discipline

```text
DIRECTION OF DEPENDENCY = Book 6 -> (exposes) ; Book 7 -> (consumes)
BOOK 6 IMPORTS BOOK 7   = FORBIDDEN and mechanically testable
BOOK 7 CODE WRITTEN     = NONE in this session
SEAM                    = CSIA_BOOK_6_TO_BOOK_7_CHANGE_RESPONSE_SEAM_v0.4
                          ResponseLink, RL-1..RL-13,
                          SOURCE_VALUE_PRESENT -> SEAM_QUOTE_PRESENT
READ-ONLY               = Book 7 may read Book 6 reference data; it may
                          not mutate a Book 6 record, and no Book 6 field
                          becomes writable from outside Book 6
```

```text
BOOK7_SEAM_IMPLEMENTABLE = TRUE
REVERSE DEPENDENCY       = NONE
BOOK7_CODE WRITTEN       = 0
```

---

## 21. Phases 21–24 — Test specification, negative surface, fingerprints, traceability

Translated in full in
`CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.1.md`
(Phase 21). Summary of the plan-level conclusions:

```text
PHASE 21  Test families COV-1..12, CHG-1..8, METH-1..5, NULL-1..9, POL-1..11,
          19 independently falsifiable replay checks, closed-operator,
          fixed-direction, zero-baseline, unit-arithmetic and
          display-independence families, no-Book2-promotion, no-state-
          emission, no-score/materiality, Book 7 read-only seam.
          EACH CASE NAMES: fixture, action, expected result, test module.
PHASE 22  Negative-surface field-EXISTENCE tests for 9 names:
          direction_derivation, zero_baseline_policy,
          unit_divisibility_policy, rounding_precision_policy, epsilon,
          tolerance, materiality, significance, custom_formula.
          Substrate: Book6FrozenModel extra="forbid", frozen=True.
          Attacks: constructor, model_copy, deserialization.
PHASE 23  Fingerprint tests for 4 digests: ComparisonRule semantic,
          MetricDefinition semantic content, baseline methodology,
          derivation binding. Each asserts mutation-changes, ordering-
          invariant, stable-serialization, same-semantics-same-digest.
PHASE 24  CSIA_BOOK_6_VALIDATION_TRACEABILITY_MATRIX.json extended with 9
          families; EVERY new invariant resolves to a REAL TEST FUNCTION.
          NO manual PASS rows. generator script regenerated.
```

---

## 22. Phase 25 — Regression baselines (pre-amendment)

```text
B1          = 107     (must remain EXACT)
B2          = 108     (must remain EXACT)
B3          = 83      (must remain EXACT)
B4          = 230     (must remain EXACT)
B5          = 293     (must remain EXACT)
B6          = 1341    (will INCREASE - the amendment adds Book 6 tests)
TOTAL_CSIA  = 2162    (will INCREASE)
R1          = 93      (must remain EXACT)
R2          = 46      (must remain EXACT)
R3          = 45      (must remain EXACT)
SENSOR      = 2325 PASS / 14 FAIL / 4 SKIPPED
              (the 14 are the KNOWN CANONICAL set and must remain exactly
              that set; the count may not improve, degrade, or change
              membership)
```

---

## 23. Phase 26 — Freeze plan

```text
BOOK1_MUTATIONS = 0
BOOK2_MUTATIONS = 0
BOOK3_MUTATIONS = 0
BOOK4_MUTATIONS = 0
BOOK5_MUTATIONS = 0
SENSOR_MUTATIONS = 0

ALLOWED
  Book 6 source            (4 NEW + 5 MODIFIED modules)
  Book 6 tests             (5 NEW test modules)
  Book 6 executable traceability / evidence
  append-only implementation ledger

NOT REQUIRED / NOT ALLOWED
  no planning-artifact mutation is required on the implementation branch
  no Book 7, no Book 8, no D8
  no live acquisition, RPC, network, database, graph database
  no sentinel.pyc, no .freebuff, no data/*.db, no __pycache__
  NO accepted-Book-6 contract may be changed without an explicit operator
  decision -- and GAP-1's OPTION-1B/1C would require exactly that, which is
  why it is a blocker rather than a task.
```

---

## 24. Phase 27 — Implementation branch strategy

```text
RECOMMENDED = CONTINUE ON agent/crypto-systems-intelligence-atlas-book6-build
              from its current HEAD 5f94c3f40
PRESERVES   = accepted anchor ancestry (3919fb805 is an ancestor)
              the acceptance record
              append-only implementation history
FORBIDDEN   = branching from planning
              merging planning history into implementation
              rebasing / force-pushing the accepted branch
INPUTS      = the ratified planning artifacts are read as GOVERNANCE INPUTS
              (docs), not as code to merge
```

**Trade-off if a separate amendment branch were preferred.** A dedicated
branch such as `agent/crypto-systems-intelligence-atlas-book6-amendment`
would give the amendment its own reviewable diff and would isolate
amendment risk from the accepted line. The cost is that the accepted
ancestry is then joined rather than continuous, and Book 6 re-acceptance
(G-10) must produce a new anchor on whichever branch is chosen. **No such
branch was created in this session**, as instructed.

```text
BRANCH_RECOMMENDATION = CONTINUE ON THE EXISTING BOOK6 BUILD BRANCH
BRANCHES_CREATED      = 0
```

---

## 25. Phase 28 — Implementation commit ladder

Proposed narrow, append-only sequence (each independently reviewable and
revertible; no giant all-in-one commit):

```text
 1  models + enums + fingerprint contract functions
 2  comparison rule registry + operator ratification binding
 3  benchmark rule registry + baseline resolver
 4  coverage applicability + sufficiency resolution
 5  arithmetic / change engine
 6  19-check replay
 7  ChangeObservation authority + creation path
 8  seam-facing Book 6 reference surface
 9  adversarial test families
10  traceability / evidence regeneration
11  implementation checkpoint (append-only ledger)
```

Each rung is gated on the previous rung's tests passing and on the
regression baselines in §22 still holding.

---

## 26. Phase 29 — Implementation authorization decision

### 26.1 Criteria

| # | Criterion | Result | Driver |
|---|---|---|---|
| 1 | `NO_UNRATIFIED_POLICY_NEEDED` | **FALSE** | GAP-1, GAP-2, GAP-3, GAP-4 |
| 2 | `NO_RUNTIME_AUTHORITY_GAP` | **TRUE** | every authority path has an accepted pattern to imitate; no gap in the *authority* machinery itself |
| 3 | `NUMERIC_REPRESENTATION_SUFFICIENT` | **FALSE** | GAP-1 |
| 4 | `UNIT_CONTRACT_SUFFICIENT` | **FALSE** | GAP-2 |
| 5 | `BENCHMARK_RUNTIME_PATH_SUFFICIENT` | **TRUE** | §6 — bounded in-amendment path exists |
| 6 | `COVERAGE_RUNTIME_PATH_SUFFICIENT` | **FALSE** | GAP-3 (rule side TRUE, applicability side FALSE) |
| 7 | `ALL_19_REPLAY_CHECKS_IMPLEMENTABLE` | **FALSE** | check 12 (GAP-3), check 19 (GAP-1, GAP-2) |
| 8 | `NEGATIVE_SURFACE_TESTS_SPECIFIED` | **TRUE** | §21 / test spec |
| 9 | `TRACEABILITY_PLAN_COMPLETE` | **TRUE** | §21 / test spec |
| 10 | `UPSTREAM_FREEZE_PRESERVABLE` | **TRUE** | §23, provided GAP-1 resolves to OPTION-1A |

```text
CRITERIA_TOTAL    = 10
CRITERIA_TRUE     = 5
CRITERIA_FALSE    = 5
```

### 26.2 Verdict

```text
BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_REVIEW = HOLD
```

**HOLD** is required because criteria 1, 3, 4, 6 and 7 are FALSE, and each
false criterion requires the operator to supply a governance decision that
ratified doctrine does not contain. Per the Phase 29 rule — *"If any require
operator invention: HOLD"* — this is not a judgement call.

### 26.3 What is explicitly NOT the reason for HOLD

```text
NOT a reason: the doctrine is vague. It is unusually precise -- 17 ratified
  domains, 4 deleted policy fields, a closed 2-member operator set, a named
  tri-state, a named discriminator, 19 enumerated checks, and an accepted
  pattern for every fingerprint and registry requirement.
NOT a reason: the accepted Book 6 code is inadequate. Three accepted
  mechanisms (methodology fingerprinting, the comparability corpus, the
  ratification ledger) map almost 1:1 onto this amendment's needs.
NOT a reason: the test plan is missing. It is complete and is delivered
  alongside this review.
NOT a reason: the freeze is unpreservable. It is preservable.
```

The reason is narrower and more uncomfortable: **three of the four gaps are
citations of "accepted" or "derived" artifacts that were never built, and the
fourth is a numeric-representation choice that changes an accepted public
model.** The ratification was internally rigorous; it referenced a substrate
that does not exist.

### 26.4 The exact operator decisions required

Recorded as concrete, answerable questions. **No option is recommended for
GAP-1's B/C variants, and none of these may be decided in code.**

```text
GAP-1  Which numeric representation is canonical for Book 6 measurements?
       1A keep binary float and define "exact canonical equality" as
          equality of the stored double (requires a doctrine wording
          amendment so the claim is not overstated)
       1B adopt decimal.Decimal (requires an accepted-Book-6 change to
          MeasurementObservation.value plus a ratified precision contract)
       1C adopt fractions.Fraction (same, plus a source-to-rational
          canonicalisation contract)
       EFFECT: determines NO_CHANGE semantics, check 19, and whether the
       upstream freeze can hold.

GAP-2  Is a unit dimensional-class contract in scope for this amendment?
       2A yes -> a THIRD authority-bearing contract class; the ratified
          "hidden third = NONE" must be amended
       2B no -> arithmetic validity is unavailable by absence; every
          comparison is NOT_COMPUTABLE / UNDEFINED
       2C deferred -> unit_requirements ships as an unenforced citation
       EFFECT: determines whether absolute_delta is ever computable and
       whether POL-11 is testable.

GAP-3  Is a coverage-applicability derivation in scope for this amendment?
       3A no -> applicability is always UNRESOLVED; all comparisons
          UNAVAILABLE
       3B yes -> author and ratify a derivation BEFORE implementation
       EFFECT: determines check 12 and whether the amendment has any
       positive path.

GAP-4  What is the value domain and derivation of comparability_status, and
       which check produces change_kind = NOT_COMPARABLE?
       4A defer the field and the member to a follow-on amendment
       4B ratify a value domain (CorpusVerdict reuse with a self-pair
          convention) plus the producing check
       EFFECT: determines a REQUIRED field of ChangeObservation and a
       REQUIRED G-5 test family.
```

### 26.5 Phase 30 disposition

```text
VERDICT = HOLD
=> CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.1.md
   is NOT CREATED. Phase 30 is conditional on PASS.
=> An authorization packet would necessarily embed the four decisions above,
   which is precisely the self-authorizing artifact this program forbids.
```

---

## 27. What this review did not do

```text
NO IMPLEMENTATION
NO SOURCE CHANGE
NO TEST CODE
NO BOOK 6 RE-ACCEPTANCE
NO BOOK 7 RATIFICATION
NO BOOK 7 IMPLEMENTATION
NO NEW POLICY
NO NEW DELTA OPERATOR
NO EPSILON
NO TOLERANCE
NO MATERIALITY
NO RULE RATIFICATION
NO LIVE ACQUISITION
NO DATABASE
NO BOOK 8
NO BRANCH CREATION
NO FORCE-PUSH / REBASE / HISTORY REWRITE
```

## 28. Ledger handoff

```text
BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_REVIEW = HOLD
NEXT = operator decisions on GAP-1, GAP-2, GAP-3, GAP-4 (§26.4),
       then re-run this review's Phases 3, 8, 10, 14 and 17 before any
       implementation authorization is considered.
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```
