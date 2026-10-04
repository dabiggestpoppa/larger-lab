# CSIA — Book 6 Consolidated Implementation Authorization Review v0.2

**Status:** `AUDIT_FINDING` — assesses authorization readiness; ratifies nothing.
**Date:** 2026-10-04
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Reviewed against planning HEAD:** `d5f2de94cabe9e42195fa11bda429b3fc9ddd80b`
**Accepted implementation base:** `5f94c3f40cea4441470c57671f51454da7377361`
**Accepted anchor:** `3919fb8052e216e94034a753fb258d338c5fa0dc`

```text
REVIEW_TYPE = CONSOLIDATED_PRE_IMPLEMENTATION_AUTHORIZATION
SCOPE       = A GAP-7 KERNEL HARDENING
              B COMPARISON / CHANGE GAP-1..5
              C RATIFIED GAP-6 6E ORDERING
              D CANONICAL 20-CHECK REPLAY
VERDICT     = PASS (12 / 12)
```

## Supersession

```text
SUPERSEDES_PROSPECTIVELY =
    CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1.md
SUPERSESSION_REASON = INTERNAL GAP-7 STATUS CONTRADICTION
v0.1_EDITED = FALSE      (left exactly as committed at a3503fee)
v0.1_OTHER_EVIDENCE_STILL_USABLE = TRUE
```

The defect is **narrow**. v0.1 §1.1 and row A8 correctly stated the ratified
B-STRICT doctrine, while v0.1 §1.3 delta **D3** instructed an implementer to
change the `SUPERSEDED` validator "so SUPERSEDED cannot read as CURRENT". Those
cannot both govern implementation. D3 is withdrawn; everything else in v0.1
stands.

---

## 0. The defect, exactly

```text
STATEMENT A  (v0.1 section 1.1, line 71-72; row A8, line 86)
    ObservationStatus IS NOT A CONJUNCT
    STATUS_ONLY_CHANGES_CURRENTNESS = FALSE
    ObservationStatus ignored for authority

STATEMENT B  (v0.1 section 1.3, line 115-117)
    D3  book6_records.py:203-206  SUPERSEDED validator
        Required: correct the polarity so SUPERSEDED cannot read as CURRENT.

AUTH_REVIEW_v0.1_INTERNAL_CONTRADICTION = TRUE
```

Statement A is the ratified doctrine, quoted correctly. Statement B would make
`ObservationStatus` authority-bearing. They are not compatible readings; one of
them is wrong.

```text
D3_AS_IMPLEMENTATION_REQUIREMENT = INVALID
RATIFIED_PRECEDENCE = BOOK6-GAP7-v0.3 GOVERNS
```

## 1. The ratified status doctrine, verified

From `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md`
§2 (ratified verbatim at line 45-56) and §3 (line 76-83):

```text
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE
STATUS_ONLY_CHANGES_CURRENTNESS             = FALSE
SUPERSESSION_CURRENTNESS_SOURCE             = REGISTERED_LINEAGE_TERMINALITY

CURRENT = TERMINAL
     AND STRUCTURALLY_VALID
     AND METHODOLOGY_CURRENT
     AND HAS_SOURCE_CLAIMS
     AND ALL_SOURCE_CLAIMS_CURRENT

ObservationStatus is NOT a conjunct.
```

```text
AUTHORITY_FOLLOWS_LINEAGE_NOT_STATUS = TRUE
STATUS_APPEARS_ANYWHERE_IN_THE_CURRENTNESS_FORMULA = FALSE
```

The five conjuncts name terminality, structure, methodology, source-claim
presence, and source-claim currentness. None of them is a status term. There is
no reading of the ratified formula under which `status` participates.

---

## 2. What the status validator actually does

The claim in v0.1 D3 was not merely in tension with the ratified doctrine — it
misdescribed the code. Read at `book6_records.py:202-215`:

```python
@model_validator(mode="after")
def _check_supersession_discipline(self) -> "MeasurementObservation":
    if self.status is ObservationStatus.SUPERSEDED and not self.supersedes_measurement_id:
        raise MeasurementRecordError(
            "a SUPERSEDED observation must name the observation it superseded")
    if self.supersedes_measurement_id and not self.restatement_reason:
        raise MeasurementRecordError(
            "a superseding observation must declare its restatement reason; "
            "history is never rewritten without one")
    if self.supersedes_measurement_id == self.measurement_id:
        raise MeasurementRecordError("an observation may not supersede itself")
    return self
```

It performs three **construction-time bookkeeping** checks. It does not read
terminality. It does not read methodology. It does not read source claims. It
never returns a currency verdict. There is no polarity to invert, because it
contains no status-to-currency mapping at all.

```text
THE_VALIDATOR_DECIDES_CURRENTNESS = FALSE
D3_PREMISE "INVERTED RELATIVE TO TERMINALITY LAW" = FALSE
```

### 2.1 The real incoherence, which is narrower and non-authority-bearing

`supersedes_measurement_id` is an **outgoing** edge: record B names the record
A it supersedes. `measurement_history` (`book6_registry.py:172-191`) walks
**forward**, selecting `obs.supersedes_measurement_id == chain[-1]
.measurement_id`. So terminality is exactly "no registered successor".

The validator requires that a record whose status is `SUPERSEDED` must name
**what it superseded** — its *predecessor*. But "superseded" ordinarily describes
the *incoming* edge: this record has been superseded, i.e. some successor names
it. So the status is paired with the outgoing edge while its meaning describes
the incoming one.

```text
STATUS_VALIDATOR_SEMANTIC_INCOHERENCE = KNOWN
STATUS_PAIRED_WITH = OUTGOING_EDGE
STATUS_MEANING_DESCRIBES = INCOMING_EDGE
```

This is a **lifecycle representation** incoherence. It is a real defect and it
should eventually be cleaned up. It changes no authority, because no authority
path reads `status`.

### 2.2 Classification

```text
STATUS_VALIDATOR_SEMANTIC_INCOHERENCE  = KNOWN
HISTORICAL                             = TRUE
AUTHORITY_BEARING                      = FALSE
REQUIRED_FOR_GAP7_CURRENTNESS_FIX      = FALSE
REQUIRED_FOR_COMPARISON_IMPLEMENTATION = FALSE
OUT_OF_SCOPE_LIFECYCLE_CLEANUP         = TRUE
```

```text
STATUS_VALIDATOR_EDIT_REQUIRED     = FALSE
CURRENTNESS_RESOLVER_USES_STATUS   = FALSE
RENAME_OBSERVATION_STATUS          = FORBIDDEN
DELETE_OBSERVATION_STATUS          = FORBIDDEN
SUPERSEDED_STATUS_REFUSES_AUTHORITY = FORBIDDEN
HISTORICAL_RECORDS_REINTERPRETED   = FALSE
```

The incoherence is **recorded, not dropped**, in
`CSIA_BOOK_6_STATUS_VALIDATOR_LIFECYCLE_AMENDMENT_DEFERRED_v0.1.md`, which
poses five candidate remedies for a future lifecycle amendment and selects
none. That record also notes why the prohibition needs writing down: every
other status enum in this codebase *is* authority-bearing, so B-STRICT is an
exception to the local convention and will read as a bug to anyone applying
the house idiom.

The prohibition is load-bearing, not tidiness. The tempting repair — make a
`SUPERSEDED` record refuse authority so the validator agrees with terminality —
would introduce exactly the status-to-currency mapping the ratified record
forbids. It would fix a bookkeeping inconsistency by **corrupting the
currentness law**, and it would break `CURR-S1`, which requires two otherwise
identical terminal records differing only in status to receive the **same**
authority verdict.

---

## 3. Corrected GAP-7 implementation deltas

The runtime deltas are exactly the **authority-relevant** ones. Renumbered from
v0.1; D3 is now the explicit non-action.

### D1 — remove the non-value-bearing early authority bypass

```text
LOCATION = book6_registry.py:195-216  resolve_current
CURRENT  = if not observation.is_value_bearing: return observation
           (line 203, precedes require_methodology and resolve_source_claim_refs)

REQUIRED = reorder so that the NV-B gates are evaluated for every record,
           before any value-bearing shortcut can return early.
EFFECT   = a source-less non-value-bearing record stops reading as CURRENT.
FALSIFIED_BY = NV-1, NV-3, NV-4, NV-8, NV-9, NV-10
```

### D2 — enforce lineage validity and terminality at the registry

```text
LOCATION = book6_registry.py:172-191  measurement_history
CURRENT  = branching is refused HERE, but registration does not refuse it
REQUIRED = branching must fail closed at registration, not only in the reader,
           so a branched lineage is never admitted in the first place.
EFFECT   = MULTIPLE_SUCCESSOR_LINEAGE = FAIL_CLOSED holds on write, not only read
FALSIFIED_BY = TERM-4
```

### D3 — NO STATUS VALIDATOR AUTHORITY CHANGE

```text
LOCATION = book6_records.py:202-215  _check_supersession_discipline
ACTION   = NONE
EDIT     = NOT REQUIRED
RATIONALE = construction-time bookkeeping; not on any authority path; the
            incoherence is lifecycle, not currentness (section 2.2)
FALSIFIED_BY = nothing — there is no case here, because there is no change
```

### D4 — every consumer inherits the central fix

```text
LOCATION = book6_core.py:139,148,165,243,337,485
           book6_sensitivity.py:132,193      (8 call sites)
REQUIRED = no consumer-side workaround. The resolver is fixed once, centrally,
           and every call site inherits the corrected law.
```

```text
RUNTIME_DELTAS_TOTAL              = 4
AUTHORITY_RELEVANT_DELTAS         = 3   (D1, D2, D4)
EXPLICIT_NON_ACTIONS              = 1   (D3)
STATUS_VALIDATOR_EDIT_REQUIRED    = FALSE
CURRENTNESS_RESOLVER_USES_STATUS  = FALSE
EACH_DELTA_HAS_ONE_RATIFIED_REMEDY = TRUE
EACH_REMEDY_REQUIRES_NEW_POLICY   = FALSE
```

---

## 4. The implementation law for B-STRICT

This is the rule D3's removal restores, and the single most important
constraint on any future GAP-7 implementation.

Take two records that are **otherwise identical**, both terminal, both
structurally valid, both with current methodology, both carrying source claims,
all of those claims current:

```text
record A:  status = OBSERVED
record B:  status = SUPERSEDED
```

Then:

```text
resolve_current(A)  and  resolve_current(B)
    MUST HAVE THE SAME AUTHORITY VERDICT
```

Status alone may do **none** of the following:

```text
STATUS_CAN_GRANT_AUTHORITY      = FALSE
STATUS_CAN_REMOVE_AUTHORITY     = FALSE
STATUS_CAN_RESTORE_AUTHORITY    = FALSE
STATUS_CAN_DESTROY_AUTHORITY    = FALSE
```

```text
STATUS_ONLY_CHANGES_CURRENTNESS = FALSE
VERDICT_EQUIVALENCE_REQUIRED    = TRUE
FALSIFIED_BY                    = CURR-S1, CURR-S2, CURR-S3
```

`CURR-S1` is the case that exists to keep the other two honest, and it is the
one the withdrawn D3 would have broken.

---

## 5. Non-terminal `SUPERSEDED` record — refusal comes from lineage

A record can be `SUPERSEDED` **and** historical, because a registered successor
exists. It is refused at **terminality**, never at status.

```text
SETUP    record R, status = SUPERSEDED, a registered successor names R
GATES    TERMINAL = FALSE   (a successor exists)

REFUSAL_REASON  = LINEAGE / TERMINALITY
STATUS_REFUSAL  = FALSE
STATUS_IS_THE_REASON = FALSE
```

```text
FALSIFIED_BY = TERM-2, CURR-S2
```

The distinction is the whole point. Two different facts happen to co-occur here:
R has a status, and R has a successor. Only the second one bears on authority.
An implementation that refuses R "because it is SUPERSEDED" gets the right
answer for the wrong reason, and gets the wrong answer the moment a record
carries a successor while its status reads `OBSERVED` — which
`SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS` forbids from resurrecting.

## 6. Decayed `SUPERSEDED` record — refusal comes from the decayed gate

A terminal record with status `SUPERSEDED`, where methodology or cited Book 2
evidence has decayed, is refused at the decayed gate.

```text
CASE 6a  terminal, status = SUPERSEDED, methodology invalidated
        REFUSAL_REASON       = METHODOLOGY_CURRENT = FALSE
        STATUS_REFUSAL       = FALSE

CASE 6b  terminal, status = SUPERSEDED, a cited Book 2 claim decayed
        REFUSAL_REASON       = ALL_SOURCE_CLAIMS_CURRENT = FALSE
        STATUS_REFUSAL       = FALSE

CASE 6c  terminal, status = OBSERVED, same decayed methodology
        REFUSAL_REASON       = METHODOLOGY_CURRENT = FALSE
        VERDICT               = IDENTICAL to case 6a
```

```text
FALSIFIED_BY = CURR-S3, NV-3, NV-9
```

Case 6c is the control: swap only the status and the verdict must not move. If
an implementation refuses 6a but accepts 6c, it has smuggled status onto the
authority path, and no amount of passing `CURR-S1` would catch it.

### 6.1 The complete refusal-reason vocabulary

Every refusal a GAP-7-correct resolver may emit, and no others:

```text
REGISTRATION          record not registered
LINEAGE               branching -> fail closed (TERM-4)
TERMINALITY           a registered successor exists (TERM-2, CURR-S2)
STRUCTURE             validate_against_definition failed
METHODOLOGY_CURRENT   methodology no longer resolves current (NV-9)
SOURCE_CLAIMS_ABSENT  source_claim_refs == () (NV-1, NV-4, STRUCT-1)
SOURCE_CLAIMS_STALE   a cited claim is not current (NV-3, CURR-S3)
```

```text
STATUS_IS_A_VALID_REFUSAL_REASON = FALSE
REFUSAL_REASONS_THAT_READ_STATUS  = NONE
```

## 7. Implementation-scope consequence

```text
DO_NOT_CHANGE_OBSERVATION_STATUS_AUTHORITY_SEMANTICS
STATUS_VALIDATOR_LIFECYCLE_CLEANUP = OUT_OF_SCOPE
```

An implementer who finds the status validator confusing should leave it alone
and record the observation. The incoherence is real, it is pre-existing, and it
is not theirs to fix inside a currentness amendment. Fixing it here would make
`ObservationStatus` authority-bearing and break the ratified B-STRICT contract.

---

## 8. Scopes B, C, D — carried from v0.1 unchanged

Only the GAP-7 status delta changed. Scopes B, C and D are restated by reference,
not re-derived, and their v0.1 evidence stands.

### Scope B — comparison / change GAP-1..5

```text
GAP-1  1A-STRICT   FINITE_STORED_BINARY64; NaN/Inf rejected; EPSILON_TOLERANCE = NONE
GAP-2  2D          SAME_METRIC_EXACT_UNIT_IDENTITY; no conversion or normalisation
GAP-3  3C          coverage presence derivation; absent -> UNRESOLVED
GAP-4  4D          COMPARABLE | NOT_COMPARABLE | UNRESOLVED
GAP-5  5E          BASELINE_SELECTOR_AUTHORITY = BOUND_INSIDE_COMPARISON_RULE

2 authority-bearing classes; HIDDEN_THIRD_CONTRACT = NONE
1 executable selector (PRIOR_COMPARABLE_WINDOW); 4 RESERVED_NOT_EXECUTABLE
11 eligibility conditions; coverage firewall; no silent fallback
```

### Scope C — ratified GAP-6 6E ordering

```text
Ratified at BOOK6-GAP6-v0.2; implementation authority remains FALSE
Derived effective keys, total over the closed WindowClass enum, no default arm
Strict candidate.effective_end < comparison.effective_start
3-step ordering, lexical tie-break FINAL only
WindowClass conversion / coercion = FALSE
Eligibility precedes ordering
SELECTOR_AGGREGATES = FALSE; hold and surface rather than aggregate
```

### Scope D — canonical 20-check replay

```text
CANONICAL_SOURCE = BOOK6-COMPARE-SUBSTRATE-v0.2 section 14
CHECKS_THAT_CANNOT_FAIL = 0
HISTORICAL_19_CHECK_LIST_USABLE_FOR_IMPLEMENTATION = FALSE
```

### 8.1 Open item carried forward from the traceability matrix

Unchanged by this review, and still open:

```text
RUNG 6 falsification cases = 15 draft (TIME-1..TIME-15), 0 ratified
RUNG_6_GATE = AMBER
```

This is a **known evidence gap**, not a criterion failure, and it was not
created or closed by this review. It is recorded in
`CSIA_BOOK_6_IMPLEMENTATION_RUNG_TRACEABILITY_MATRIX_v0.1.md` §4 FINDING-1 and
remains an operator choice.

---

## 9. Regression baselines

### 9.1 Book 6 / CSIA counts — carried unchanged, independently re-measured

```text
B1 = 107   B2 = 108   B3 =  83   B4 = 230   B5 = 293   B6 = 1341
TOTAL = 2162   (2162 passed in 6.44s)
R1 =  93   R2 =  46   R3 =  45

DIVERGENCES = 0
BOOK6_COUNT_BASELINES_VERIFIED = TRUE
```

```text
BOOK6_TREE_FINGERPRINT_REQUIRED_FOR_AUTHORIZATION = FALSE
```

These counts were re-measured per-file at `5f94c3f40c`, not asserted. A
tree-fingerprint manifest is a reasonable *hardening* for RUNG 11 and is
explicitly **not** an authorization prerequisite. If a future implementation
adds one, it must change no governance semantics.

### 9.2 Sensor baseline — pinned, carried unchanged, not reopened

```text
PINNED_TO  = 5f94c3f40cea4441470c57671f51454da7377361
COLLECTED  = 2343
PASSED     = 2325
FAILED     =   14
SKIPPED    =    4
XFAILED    =    0

TESTS_TREE_SHA256 = a3a99657117c0238a0f635c19dde8a7f8e5ab3575c8bac6b334fa3e7254b0fd5
SRC_TREE_SHA256   = b16a148e5ac05ca148bf6bd60af4be6ff72b1fbc95e118dafdbcf7f24c6b2081
```

The 14 failures are the canonical evidence-matrix regeneration set, pinned by
identity. They are **failures, not xfails**; an xfail reading would have
produced a freeze gate that cannot fail. Not re-run for this review.

---

## 10. The twelve criteria, re-run

| # | Criterion | v0.1 | v0.2 | Basis for the v0.2 result |
|---|---|---|---|---|
| 1 | `NO_UNRATIFIED_POLICY_NEEDED` | TRUE | **TRUE** | 0 coder policy choices in A, B, C, D |
| 2 | `NO_AUTHORITY_DESIGN_GAP` | TRUE | **TRUE** | 2 authority-bearing classes; no hidden third |
| 3 | `GAP7_IMPLEMENTATION_CONTRACT_COMPLETE` | TRUE* | **TRUE** | **was not sound in v0.1**; now complete — the contradiction is removed and D1/D2/D4 each carry one ratified remedy |
| 4 | `COMPARISON_CONTRACT_COMPLETE` | TRUE | **TRUE** | carried from v0.1 §2; unchanged |
| 5 | `GAP6_ORDERING_CONTRACT_COMPLETE` | TRUE | **TRUE** | ratified `BOOK6-GAP6-v0.2`; unchanged |
| 6 | `CANONICAL_20_CHECK_REPLAY_UNAMBIGUOUS` | TRUE | **TRUE** | carried from v0.1 §4; unchanged |
| 7 | `TEST_CONTRACT_COMPLETE` | TRUE | **TRUE** | ratified 237 + ratified GAP-7 39; unchanged |
| 8 | `IMPLEMENTATION_ORDER_COMPLETE` | TRUE | **TRUE** | 11 rungs, rungs 1-3 precede consumption; unchanged |
| 9 | `FRESH_BRANCH_STRATEGY_VALID` | TRUE | **TRUE** | derives from `5f94c3f40c`; unchanged |
| 10 | `UPSTREAM_FREEZE_PRESERVABLE` | TRUE | **TRUE** | frozen worktree untouched; unchanged |
| 11 | `BOOK1_5_FREEZE_PRESERVABLE` | TRUE | **TRUE** | B1-B5 re-measured exact; unchanged |
| 12 | `SENSOR_FREEZE_PRESERVABLE` | TRUE | **TRUE** | pinned and reproduced; unchanged |

\* v0.1 asserted criterion 3 TRUE while simultaneously carrying D3, which
contradicts ratified B-STRICT. The assertion was **unsound**, not the criterion
wrong.

```text
CRITERIA = 12
TRUE     = 12
FALSE    =  0
CRITERION_CHANGED_VALUE = 0
CRITERION_CHANGED_BASIS = 1   (criterion 3, now sound)

CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.2 = PASS
```

```text
ANY_CRITERION_REQUIRED_NEW_POLICY = FALSE
HOLD_REQUIRED                     = FALSE
```

Criterion 3 is the only one this review was permitted to move, and it moved in
**basis** rather than in value. Removing the contradiction made the TRUE sound;
it did not make a FALSE true.

---

## 11. Verdict

```text
CONSOLIDATED_REVIEW_v0.2 = PASS
CRITERIA = 12 / 12 TRUE

BOOK_6_DESIGN_COMPLETE = TRUE
BOOK_6_IMPLEMENTED     = FALSE

BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

This is a PASS on implementability. It is not an authorization.

## 12. What this review did not do

```text
RATIFIED_ANYTHING              = FALSE
IMPLEMENTATION_AUTHORIZED      = FALSE
EDITED_REVIEW_v0.1             = FALSE
EDITED_ANY_RATIFIED_RECORD     = FALSE
EDITED_THE_STATUS_VALIDATOR    = FALSE
STATUS_VALIDATOR_EDIT_REQUIRED = FALSE
RENAMED_OBSERVATION_STATUS     = FALSE
DELETED_OBSERVATION_STATUS     = FALSE
REINTERPRETED_HISTORICAL_RECORDS = FALSE
GAP_REOPENED                   = FALSE
NEW_BOOK6_FINGERPRINT_BLOCKER  = FALSE   (explicitly not raised)
SOURCE_CHANGED                 = FALSE
TEST_CODE_WRITTEN              = FALSE
BRANCH_CREATED                 = FALSE
WORKTREE_CREATED               = FALSE
FROZEN_WORKTREE_MUTATED        = FALSE
SENSOR_SUITE_RERUN             = FALSE   (pin carried, not reopened)
BOOK_7_WORKED_ON               = FALSE
CHOIR_TOUCHED                  = FALSE
```

## 13. Disposition of the superseded artifacts

```text
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1.md
    STATUS = SUPERSEDED / INTERNAL GAP7 STATUS CONTRADICTION
    KEPT IN PLACE, NOT EDITED
    USABLE = its scopes B, C, D evidence; its regression baselines;
             its rung order; its sensor section as corrected at a3503fee
    NOT USABLE = section 1.3 delta D3, and the criterion-3 assertion it supported

CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.1.md
    STATUS = SUPERSEDED / INHERITED THE REVIEW_v0.1 CONTRADICTION
    SUPERSEDED BY = ..._PACKET_v0.2.md
    KEPT IN PLACE, NOT EDITED
```

## 14. Cross-references

```text
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md RATIFIED
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md          39 cases
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_RECORD_v0.1.md         RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_RECORD_v0.1.md RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_REPLAY_PRECEDENCE_ERRATUM_v0.1.md    RATIFIED
CSIA_BOOK_6_SENSOR_REGRESSION_BASELINE_PIN_v0.1.md                 PINNED
CSIA_BOOK_6_IMPLEMENTATION_RUNG_TRACEABILITY_MATRIX_v0.1.md         RUNG 6 AMBER
CSIA_BOOK_6_STATUS_VALIDATOR_LIFECYCLE_AMENDMENT_DEFERRED_v0.1.md      DEFERRED
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.1.md  SUPERSEDED
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.1.md  SUPERSEDED
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```
