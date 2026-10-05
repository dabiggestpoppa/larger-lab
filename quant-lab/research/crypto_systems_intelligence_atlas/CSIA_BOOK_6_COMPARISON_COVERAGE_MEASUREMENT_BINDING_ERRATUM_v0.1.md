# CSIA — Book 6 Comparison Coverage Measurement Binding Erratum v0.1

**Status:** `RATIFIED` (§1–§6, binding correction) with §7 `OPEN`
**Record type:** narrow governance erratum
**Date:** 2026-10-05
**Decision id:** none required for §1–§6. Those sections correct how an
already-ratified binding participates in replay; no operator selection is made
or implied. §7 is an **open question** reserved for
`BOOK6-COVERAGE-MEASUREMENT-BINDING-v0.1`, which is **not yet issued**.
**Grants implementation authority:** `FALSE`
**Changes implementation:** `FALSE`
**Reopens GAP-3 / GAP-4:** `FALSE`

```text
DOCTRINE_CHANGED                   = FALSE
NEW_FIELD                          = FALSE
NEW_AUTHORITY_CLASS                = FALSE
NEW_COVERAGE_POLICY                = FALSE
IMPLEMENTATION_BINDING_DEFECT      = TRUE
COVERAGE_OBSERVATION_IS_MEASUREMENT_BOUND = TRUE
CROSS_MEASUREMENT_COVERAGE_SUBSTITUTION   = PROHIBITED
RULE_MATCH_ALONE_IS_NOT_ENOUGH            = TRUE
WHICH_MEASUREMENT_THE_COVERAGE_REF_COVERS = OPEN (§7)
```

---

## 0. What this record is

`CSIA_BOOK_6_COMPARISON_COVERAGE_REPLAY_BINDING_CLARIFICATION_v0.1.md` §4
(`BOOK6-COVERAGE-REPLAY-BINDING-v0.1`, `RATIFIED`) defines check 16's required
validations, in order:

```text
 1. a CoverageObservation exists for this comparison
 2. observation.sufficiency_rule_ref == the named coverage_sufficiency_rule_ref
 3. the named rule passed checks 14 and 15
 4. the observation applies to the comparison input under accepted coverage
    semantics
```

Validation **4** is load-bearing and was not implemented. This record establishes
that it is already binding as a consequence of the accepted substrate, records
the defect its absence produced, and declares one residual question open rather
than answering it.

It adds no field, no class, no registry and no authority. The accepted
`CoverageObservation` type is not re-declared, extended or relaxed.

---

## 1. Fact 1 — `CoverageObservation.measurement_id` is required and is the binding identity

`book6_definitions.py:192–208`, verified at `5f94c3f4` (frozen accepted Book 6):

```text
CoverageObservation(Book6FrozenModel)
  model_config      = ConfigDict(extra="forbid", frozen=True)
  measurement_id    : str = Field(min_length=1)      <-- REQUIRED, no default
  observed_fraction : float = Field(ge=0.0, le=1.0)
  basis             : str = Field(min_length=8)
  sufficiency_rule_ref : str | None = None
  valid_time        : datetime
```

`measurement_id` is not optional, not nullable and not defaulted. A
`CoverageObservation` **cannot be constructed** without naming the measurement
its coverage belongs to, and `extra="forbid"` means no second measurement
identity can be smuggled in alongside it.

```text
COVERAGE_WITHOUT_A_MEASUREMENT_ID = UNCONSTRUCTIBLE
```

## 2. Fact 2 — the registry stores and returns coverage by exact measurement identity

`book6_registry.py`, verified at `5f94c3f4`:

```text
:87    self._coverage: dict[str, CoverageObservation] = {}

:152   def register_coverage(self, coverage: CoverageObservation) -> ...:
:153       if coverage.measurement_id in self._coverage:
:155           raise Book6RegistryError(
:156               f"coverage for {coverage.measurement_id} already registered")
:157       self._coverage[coverage.measurement_id] = coverage

:398   def coverage_of(self, measurement_id: str) -> CoverageObservation | None:
:399       return self._coverage.get(measurement_id)
```

Three consequences, all structural rather than advisory:

```text
COVERAGE_STORE_KEYED_BY        = coverage.measurement_id
ONE_COVERAGE_OBSERVATION_PER_MEASUREMENT = TRUE
CROSS_MEASUREMENT_COVERAGE_LOOKUP_PATH    = NONE
```

There is **no** accepted code path that returns measurement B's coverage when
asked for measurement A's. `coverage_of(A)` is `None` when only B is registered.
A `CoverageObservation` is therefore **not** generic evidence that may be
reused for any observation sharing the same metric or the same rule.

The measurement side closes the same loop: `MeasurementObservation.coverage_observation_id`
(`book6_records.py:125`) is the measurement's own pointer to its coverage.

## 3. Conclusion — the substrate is already measurement-bound

```text
COVERAGE_OBSERVATION_IS_MEASUREMENT_BOUND = TRUE
```

This is a **fact about accepted artifacts**, not a policy selection. Nothing in
this record creates the binding; it already exists in the schema, the store key
and the lookup. What is ratified here is that the comparison replay may not
weaken it.

---

## 4. Finding C — check 16 never validated the measurement identity

Reproduced at the Rung 7 repair `53ac5ea28e4b82eedf924f631ada13c56b1cffe6`,
implementation HEAD at the time of this record.

Fixture: measurement `A` (the comparison input), measurement `B` (an unrelated
subject), one registered + ratified `cov:1` scoped to the exact compared metric,
and

```text
CoverageObservation(measurement_id = B,
                    sufficiency_rule_ref = "cov:1",
                    observed_fraction = 0.97,
                    required_fraction  = 0.90)
```

Result of replaying coverage for comparison measurement **A** with **B's**
observation:

```text
check 12 PASS  coverage is REQUIRED for metric.tx
check 13 PASS  ComparisonRule binds coverage_sufficiency_rule_ref cov:1
check 14 PASS  cov:1 carries a live ratification by operator:probe
check 15 PASS  cov:1 is scoped to metric.tx
check 16 PASS  cov:1 requires 0.9 and observation meas:unrelated-other-subject
               observed 0.97 -> SUFFICIENT

coverage verdict          : SUFFICIENT
temporal comparability    : COMPARABLE
CoverageAuthorization.observation_ref : meas:unrelated-other-subject
```

```text
CROSS_MEASUREMENT_COVERAGE_SUBSTITUTION = TRUE
SAME_METRIC_WRONG_MEASUREMENT           = ACCEPTED   (defect)
```

Note the last line: the substituted measurement id was not merely tolerated, it
was written into the authorization record as `observation_ref`.

The replay API surface at `53ac5ea2`:

```text
replay_coverage_checks(registry, metric_id, named_rule_ref,
                       coverage_observation)
carries_an_expected_measurement_identity = False
```

The identity was not merely unchecked — it was **inexpressible**. There was no
parameter in which the comparison input could be named, so no caller could have
complied with validation 4 even if they wished to.

### 4.1 Classification

```text
DOCTRINE_CHANGED              = FALSE
NEW_FIELD                     = FALSE
NEW_AUTHORITY_CLASS           = FALSE
NEW_COVERAGE_POLICY           = FALSE
IMPLEMENTATION_BINDING_DEFECT = TRUE
```

The already-ratified clarification required the binding. The already-accepted
schema and registry carry it. The implementation simply did not perform it.

---

## 5. The binding, restated as law

Before any `observed_fraction` is read, and before any comparison of it against
`required_fraction`:

```text
COVERAGE_EVIDENCE_BINDING             = EXACT_MEASUREMENT_IDENTITY
CROSS_MEASUREMENT_COVERAGE_SUBSTITUTION = PROHIBITED
RULE_MATCH_ALONE_IS_NOT_ENOUGH          = TRUE
```

A `CoverageObservation` whose `measurement_id` is not the measurement for which
coverage is being replayed is **not evidence for that comparison at all**. It is
not degraded evidence, not partial evidence and not evidence for a nearby
measurement. It is evidence about something else.

### 5.1 Rule match, ratification, scope and measurement identity are four distinct things

```text
14. the named rule is ratified and current
15. the named rule's scope_metric_id == the compared metric
16. the observation's sufficiency_rule_ref == the named rule
    AND the observation's measurement_id == the replayed measurement
    AND THEN observed_fraction vs required_fraction
```

Each is independently falsifiable. Passing three of them says nothing about the
fourth. The defect was precisely that the fourth was absent while the first
three were enforced, which is what made substitution invisible.

### 5.2 Metric identity and measurement identity are different questions

```text
metric_id       answers: what metric DEFINITION is this?
measurement_id  answers: which concrete OBSERVATION is this evidence attached to?
BOTH_ARE_REQUIRED = TRUE
```

`CoverageSufficiencyRule.scope_metric_id` is a metric. `CoverageObservation.measurement_id`
is an observation. A rule scoped to `metric.tx` says nothing about whether
`meas:B`'s coverage says anything about `meas:A` — even though both may measure
`metric.tx`.

```text
SAME_METRIC_WRONG_MEASUREMENT = REFUSED
```

### 5.3 A cross-measurement observation yields no verdict at all

When the measurement identity does not match, there is no coverage determination
to report — not a negative one:

```text
CHECK_16                      = FAIL
COVERAGE_VERDICT              = UNKNOWN
TEMPORAL_COMPARABILITY_STATUS = UNRESOLVED
```

This is the clarification §6 distinction, applied. A check 16 that **fails** is
an absence of basis and routes to `UNRESOLVED`. It must **never** be reported as
a check 16 that succeeded in recomputing `INSUFFICIENT`, which would route to
`NOT_COMPARABLE` and assert a structural finding that was never made.

```text
WRONG_MEASUREMENT_PRODUCES_SUFFICIENT   = PROHIBITED
WRONG_MEASUREMENT_PRODUCES_INSUFFICIENT = PROHIBITED
WRONG_MEASUREMENT_IS_NOT_A_FINDING      = TRUE
```

---

## 6. What the caller must supply, and what it may never be inferred from

The replay must receive the expected measurement identity as an **explicit,
exact input**.

```text
INFER_FROM_RULE_ID              = PROHIBITED
INFER_FROM_METRIC_ID            = PROHIBITED
INFER_FROM_CALLER_CONVENTION    = PROHIBITED
INFER_FROM_THE_OBSERVATION      = PROHIBITED
INFER_FROM_REGISTRY_ORDERING    = PROHIBITED
OMISSION_WHEN_COVERAGE_REQUIRED = PROHIBITED
```

The last line matters as much as the first. Inferring the expected identity from
`coverage_observation.measurement_id` would make the check vacuously true for
every observation, including a substituted one — the binding would be satisfied
by the very thing it exists to test. There is no safe default and no optional
path: when coverage applicability is `REQUIRED`, the expected measurement is a
required input of the replay.

---

## 7. OPEN — which measurement the singular `coverage_observation_ref` covers

The binding in §5 is unambiguous. **Which measurement identity the replay must be
told to expect is not.** That question is not settled by the corpus, and this
record does not answer it.

### 7.1 The singular field

`ChangeObservation` carries:

```text
baseline_measurement_refs              tuple[str, ...]   min_length=1
comparison_measurement_refs            tuple[str, ...]   min_length=1
selected_baseline_measurement_ref      str | None
coverage_observation_ref               str | None       (singleton)
```

`book6_comparison_contracts.py:406–422`, ratified under grammar v0.3/§3.1 R-3:
the ref is required iff `coverage_observation_state is PRESENT` and absent
otherwise. It names **one** observation, while both measurement sides are
**lists**.

### 7.2 Audit of every governing artifact that bears on the question

| # | Artifact | What it says about which measurement the coverage covers | Settles it? |
|---|---|---|---|
| 1 | `book6_definitions.py:192` `CoverageObservation` | `measurement_id` is the identity coverage belongs to | **substrate only** — says coverage is measurement-bound, not *which* measurement of a comparison |
| 2 | `book6_registry.py:152,398` | keyed and looked up by exact `measurement_id` | **substrate only** — same |
| 3 | `book6_records.py:125` `MeasurementObservation.coverage_observation_id` | a measurement carries its own coverage ref | **substrate only** — per-measurement, still no comparison-side choice |
| 4 | `AMENDMENT_RECONCILIATION_v0.1:200` | *"CoverageObservation — a measurement, with its basis"* | "a measurement", indefinite. Does not say which |
| 5 | `GRAMMAR_v0.1:143` `coverage: coverage state of the inputs` | plural "the inputs" | **REMOVED** — recorded as `AMBIGUOUS` at reconciliation `:26` |
| 6 | `GRAMMAR_v0.3:218`, `GRAMMAR_v0.4 §3.1`, `GRAMMAR_v0.5 §3` | `coverage_observation` / `coverage_observation_ref`, singular | **no measurement qualifier at any version** |
| 7 | `GRAMMAR_v0.6 §5` checks 8–9 | baseline measurement refs / comparison measurement refs | both sides **plural** |
| 8 | `IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1 §17` check 16 row | inputs listed as *"`CoverageObservation`, rule fraction"* | **silent** — no measurement binding in the canonical check table |
| 9 | `IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1 §18.1` | caller supplies `coverage_observation_ref` beside both ref lists | **silent** — no binding stated |
| 10 | `GRAMMAR_v0.5 §3.2` items 8–9 | one verdict for the comparison; no per-side attribution | **silent** |
| 11 | `COVERAGE_REPLAY_BINDING_CLARIFICATION_v0.1 §4` validations 1 and 4 | *"exists for this comparison"*; *"applies to **the comparison input**"* | **the only affirmative statement** — see §7.3 |
| 12 | Corpus search: lines containing both `coverage` and `baseline` | **18 hits**, every one about `COVERAGE_INFLUENCES_BASELINE_SELECTION = FALSE`, absence/tolerance prose, or change-response narratives | **no binding** |
| 13 | Corpus search: lines containing both `coverage` and `measurement` | **35 hits**; filtering for `comparison measurement`, `baseline measurement`, `its measurement`, `attached to` returns **0 hits** | **no binding** |
| 14 | Corpus search for the phrase `comparison input` | **1 hit** outside this record — clarification `:197`, artifact 11 | see §7.3 |

### 7.3 Why artifact 11 is not decisive

"the comparison input" is the sole affirmative phrasing in the corpus, and it
does not survive scrutiny as a settled term of art:

1. Outside this record the phrase occurs **exactly once** in the corpus, at
   `CSIA_BOOK_6_COMPARISON_COVERAGE_REPLAY_BINDING_CLARIFICATION_v0.1.md:197`.
   It is not a defined term anywhere.
2. `comparison_measurement_refs` is **plural** — grammar v0.1 `:134` "one or
   more; non-empty", and the ratified contract enforces `min_length=1` on a
   tuple. A single `coverage_observation_ref` cannot cover a set unless a rule
   says which member it covers, and no such rule exists.
3. The canonical check table's own generic term for the measurement side is
   *"input measurement"* (checks 10, 11) — which in this corpus means **all**
   inputs, baseline included. So "comparison input" is not how this corpus
   already refers to that side.
4. Nothing anywhere binds it to the baseline side either, and nothing says
   both.

```text
DOCTRINE_BINDS_COVERAGE_TO_COMPARISON_MEASUREMENT = NOT ESTABLISHED
DOCTRINE_BINDS_COVERAGE_TO_BASELINE_MEASUREMENT   = NOT ESTABLISHED
DOCTRINE_REQUIRES_BOTH                            = NOT ESTABLISHED
DOCTRINE_IS_SILENT_ON_THE_QUESTION                = TRUE
```

### 7.4 Reserved decision

```text
DECISION_ID_RESERVED = BOOK6-COVERAGE-MEASUREMENT-BINDING-v0.1
STATUS               = OPEN / NOT ISSUED
```

The candidate selections, none of which this record makes:

```text
BIND_COVERAGE_TO_THE_COMPARISON_MEASUREMENT
BIND_COVERAGE_TO_THE_SELECTED_BASELINE_MEASUREMENT
REQUIRE_DISTINCT_COVERAGE_EVIDENCE_FOR_BOTH_SIDES
```

The third is a **schema** question, not a binding question: `ChangeObservation`
has one `coverage_observation_ref`, and requiring both sides would need more
than one, which is a change to an authority-bearing contract and therefore an
operator decision rather than an implementation choice.

```text
IMPLEMENTATION_AUTHORIZED_WHILE_§7_IS_OPEN = FALSE
```

Rung 7's measurement-binding repair is **held** at this point. Nothing in this
record licenses implementing a guess.

---

## 8. Effect on the implementation

```text
IMPLEMENTATION_CHANGED        = FALSE
RUNG_7_MEASUREMENT_BINDING_REPAIR = HELD PENDING §7
RUNG_7_STATUS                 = REPAIR REQUIRED (third defect)
HEAD_AT_RECORD                = 53ac5ea28e4b82eedf924f631ada13c56b1cffe6
```

The repair, once §7 is answered, is **append-only**. It must:

- add an explicit expected-measurement input to the coverage replay;
- fail check 16 with verdict `UNKNOWN` and check 19 `UNRESOLVED` when the
  observation's `measurement_id` differs, **before** reading `observed_fraction`;
- keep the measurement binding independently falsifiable from checks 14 and 15;
- add traceability for `COVERAGE_OBSERVATION_MEASUREMENT_BINDING` inside the
  existing `CMP.COVERAGE_AUTHORITY` family, inventing no new family.

---

## 9. What this record does not do

```text
NEW COVERAGE OBSERVATION SCHEMA   = NONE   (accepted type reused as-is)
NEW AGGREGATION SEMANTICS         = NONE
NEW AUTHORITY-BEARING CLASS       = NONE   (contract count remains exactly 2)
NEW COVERAGE REGISTRY             = NONE
NEW COVERAGE POLICY               = NONE
COVERAGERULE_REGISTRY AUTHORITY   = UNCHANGED
CHANGEOBSERVATION FIELD ADDED     = NONE
GAP_3 / GAP_4 REOPENED            = FALSE
SOURCE_FILE_WRITTEN_OR_EDITED     = FALSE
TEST_CODE_WRITTEN_OR_EDITED       = FALSE
RATIFIED_RECORD_EDITED            = FALSE
BRANCH_REWRITTEN_OR_REBASED       = FALSE
FROZEN_BOOK_6_WORKTREE_MUTATED    = FALSE
BOOK_7_WORKED_ON                  = FALSE
LIVE_ACQUISITION                  = FALSE
WHICH_MEASUREMENT_ANSWERED       = NOT ANSWERED (§7)
```

---

## 10. Authority flags

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = TRUE   (offline amendment scope only, unchanged)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## 11. Cross-references

```text
CSIA_BOOK_6_COMPARISON_COVERAGE_REPLAY_BINDING_CLARIFICATION_v0.1.md  §4 validation 4
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.6.md                          canonical checks 12-16, 19
CSIA_BOOK_6_COMPARISON_CHANGE_GRAMMAR_v0.3.md                          coverage_observation (singleton)
CSIA_BOOK_6_COMPARISON_CHANGE_AMENDMENT_RECONCILIATION_v0.1.md        :200, :26
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1.md  §17 check 16, §18.1
book6_definitions.py                                                   CoverageObservation:192
book6_registry.py                                                      register_coverage:152, coverage_of:398
book6_records.py                                                       coverage_observation_id:125
book6_comparison_coverage.py                                           replay_coverage_checks (Rung 7)
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```

---

**Status:** `RATIFIED` for §1–§6. The measurement-identity binding is law and was
already law in the accepted substrate. §7 is `OPEN` and is reserved for
`BOOK6-COVERAGE-MEASUREMENT-BINDING-v0.1`; the repair is held until the operator
answers it.
