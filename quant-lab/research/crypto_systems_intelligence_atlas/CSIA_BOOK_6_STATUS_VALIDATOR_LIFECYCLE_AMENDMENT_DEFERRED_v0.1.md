# CSIA — Book 6 Status Validator Lifecycle Amendment (DEFERRED) v0.1

**Status:** `DEFERRED — RECORDED, NOT ADOPTED`
**Date:** 2026-10-04
**Decision id:** none. This artifact **records** a deferred incoherence and
**ratifies nothing**. It proposes no repair and selects no remedy.
**Grants implementation authority:** `FALSE`
**Amends:** `book6_records.py:202-215` `_check_supersession_discipline`
**Amendment class:** `LIFECYCLE REPRESENTATION` — explicitly **not**
`CURRENTNESS`

```text
STATUS_VALIDATOR_SEMANTIC_INCOHERENCE  = KNOWN
HISTORICAL                             = TRUE
AUTHORITY_BEARING                      = FALSE
REQUIRED_FOR_GAP7_CURRENTNESS_FIX      = FALSE
REQUIRED_FOR_COMPARISON_IMPLEMENTATION = FALSE
OUT_OF_SCOPE_LIFECYCLE_CLEANUP         = TRUE

DEFERRED = TRUE
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

---

## 0. Why this record exists

An external review found that authorization review v0.1 told an implementer to
"correct the polarity" of the `SUPERSEDED` validator, contradicting ratified
B-STRICT. Review v0.2 withdrew that instruction. This record exists so the
underlying incoherence is not silently dropped along with the bad instruction.

Withdrawing the instruction is right. **Deleting the observation would be
wrong.** The incoherence is real. It is simply not a currentness defect, so it
does not belong in the currentness amendment — and saying that is only durable
if it is written down somewhere an implementer will actually hit.

```text
THE_INSTRUCTION_WAS_WRONG = TRUE
THE_DEFECT_IS_STILL_REAL   = TRUE
BOTH_ARE_TRUE_SIMULTANEOUSLY
```

---

## 1. The incoherence, stated precisely

`MeasurementObservation` carries two relations over a lineage:

```text
OUTGOING  supersedes_measurement_id = X   "I superseded X"      (I am the successor)
INCOMING  (no field exists)             "X superseded me"      (I am the predecessor)
```

`ObservationStatus.SUPERSEDED` means *"I have been superseded"* — the
**incoming** relation, the one with no field. The validator binds it to the
**outgoing** one:

```python
if self.status is ObservationStatus.SUPERSEDED and not self.supersedes_measurement_id:
    raise MeasurementRecordError(
        "a SUPERSEDED observation must name the observation it superseded")
```

So a record is required to declare that it superseded something, using a status
that says it was superseded. The two relations are opposite, and the accepted
test suite pins the opposite pairing as intended behaviour.

```text
STATUS_MEANS_INCOMING_EDGE
STATUS_IS_BOUND_TO_OUTGOING_EDGE
THE_TWO_ARE_OPOSITE_RELATIONS
```

### 1.1 Consequence, stated without spin

A predecessor record has **no way to record that it was superseded**. Its
successor names it, and the predecessor's own status field would have to name
its predecessor instead. Lineage membership is therefore only discoverable by
scanning forward, never by reading the record.

That is a real representational cost, and it is why this is recorded rather than
dismissed.

---

## 2. Why it is out of currentness scope — proven, not asserted

Three independent pieces of evidence, all read-only at `5f94c3f40c`.

### 2.1 The validator decides nothing about currency

`_check_supersession_discipline` performs three construction-time checks. It
reads no lineage, no methodology, no source claims, and **never returns a
currency verdict**. It returns `self`.

```text
THE_VALIDATOR_DECIDES_CURRENTNESS = FALSE
```

### 2.2 `ObservationStatus` is branched on exactly once in all of accepted `src/`

```text
ObservationStatus read sites in src/crypto_systems_intelligence_atlas/ = 1
    book6_records.py:203   (the bookkeeping validator itself)
```

Every other occurrence of `ObservationStatus` in accepted source is a **default
value** on construction (`book6_records.py:129`, `book6_support.py:398`,
`book6_valuation.py:175`) — never a branch.

```text
CURRENTNESS_RESOLVER_USES_STATUS = FALSE
STATUS_ON_ANY_AUTHORITY_PATH     = NONE
```

### 2.3 Terminality is computed by forward scan, not by status

`measurement_history` (`book6_registry.py:172-191`) finds successors via
`obs.supersedes_measurement_id == chain[-1].measurement_id` and refuses
branching. Currentness follows from "no registered successor".

```text
SUPERSESSION_CURRENTNESS_SOURCE = REGISTERED_LINEAGE_TERMINALITY
```

## 3. The tripwire: the local convention points the wrong way

This is the part worth reading twice.

Every **other** status enum in this codebase *is* authority-bearing:

```text
RuleRatificationStatus        book6_states.py:235
    return self.status is RuleRatificationStatus.RATIFIED      <- an authority predicate
RegistryStatus                architecture.py:260,267
    status gates whether a registry value is live vs historical
CoverageRuleRatificationStatus book6_coverage_rules.py:142 ; book6_definitions.py:259
RealizationStatus             identity.py:311,314,318,714,717
```

So `MeasurementObservation` is the **only** record type in the codebase whose
status carries no authority. B-STRICT is an **exception to the house style**,
not an instance of it.

```text
AUTHORITY_BEARING_STATUS_ENUMS_ELSEWHERE = MANY
AUTHORITY_BEARING_STATUS_ENUMS_ON_OBSERVATIONS = NONE
B_STRICT_IS_A_DEVIATION_FROM_LOCAL_CONVENTION = TRUE
```

That is why it needs writing down. An implementer applying this repository's
own idiom — *status drives authority; that is how records work here* — to
`MeasurementObservation` would reintroduce exactly the defect the withdrawn D3
described, and would look entirely reasonable while doing it.

The ratified position is the counterintuitive one, and counterintuitive
positions are the ones that get "helpfully" corrected by someone who assumes
they found a bug.

```text
THIS_IS_NOT_A_TYPO_IN_THE_DOCTRINE = TRUE
```

## 4. The accepted test suite pins the current shape

Four accepted tests assert the present behaviour by message:

```text
test_book6_adversarial.py:452  test_an_observation_may_not_supersede_itself
test_book6_adversarial.py:465  test_a_superseding_observation_must_declare_why
test_book6_adversarial.py:477  test_a_superseded_observation_must_name_what_it_superseded
test_book6_core.py:224         test_supersession_requires_restatement_reason
```

The third is the one that pins the incoherence:

```text
test_a_superseded_observation_must_name_what_it_superseded
    asserts that a SUPERSEDED record without supersedes_measurement_id
    raises "must name the observation it superseded"
```

So any future repair is a **breaking change to accepted tests**. That is the
concrete reason it cannot be folded into the currentness amendment as a
drive-by: the currentness work has a regression contract (`B1..B5`, `R1..R3`
exact) that such a change would break, and it would break them *legitimately*,
which is worse than breaking them illegitimately because it invites a
last-minute exemption.

---

## 5. Open questions for a future lifecycle amendment — posed, not answered

Every item below requires **new ratification**. None is selected here, and this
record must not be read as a preference.

```text
Q1  Give predecessors an explicit incoming edge (a superseded_by field)?
      -> makes lineage readable from the record
      -> adds a field to an accepted contract class; needs its own ratification
      -> interacts with MeasurementObservation contract stability

Q2  Retarget the SUPERSEDED status to the outgoing relation and rename it
    (e.g. SUPERSEDES)?
      -> makes the binding honest
      -> renames a ratified enum member; breaks the four accepted tests above

Q3  Drop the status requirement from the validator and derive supersession
    from lineage alone?
      -> smallest change; removes a false constraint
      -> leaves the enum carrying a status nothing validates

Q4  Leave it alone permanently and document the scan-only lineage model?
      -> zero cost, zero risk
      -> preserves the representational cost in section 1.1 forever

Q5  Deprecate ObservationStatus entirely?
      -> most honest long-term
      -> largest blast radius; touches every fixture constructing a status
```

```text
QUESTIONS_POSED      = 5
QUESTIONS_ANSWERED  = 0
REMEDY_SELECTED     = NONE
```

Q3 and Q4 are cheap; Q1, Q2 and Q5 are not. That trade is real, and it is the
operator's to weigh, not this record's.

### 5.1 What any future amendment must preserve

```text
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE   (BOOK6-GAP7-v0.3)
STATUS_ONLY_CHANGES_CURRENTNESS             = FALSE
```

No lifecycle remedy may be implemented by making status authority-bearing. The
two questions are independent, and Q1–Q5 all keep them independent.

---

## 6. Standing prohibitions, in force now

```text
STATUS_VALIDATOR_EDIT_REQUIRED   = FALSE
CURRENTNESS_RESOLVER_USES_STATUS = FALSE
RENAME_OBSERVATION_STATUS        = FORBIDDEN
DELETE_OBSERVATION_STATUS        = FORBIDDEN
SUPERSEDED_STATUS_REFUSES_AUTHORITY = FORBIDDEN
REINTERPRET_HISTORICAL_RECORDS   = FORBIDDEN
```

An implementer who encounters this incoherence during the GAP-7 or comparison
work should **leave it alone and note it**, exactly as this record does. The
defect is pre-existing, out of scope, and already recorded.

```text
DISCOVERED_DURING_CURRENTNESS_WORK = LEAVE_AND_RECORD
```

## 7. What this record did not do

```text
RATIFIED_ANYTHING               = FALSE
SELECTED_A_REMEDY               = FALSE
EDITED_SOURCE                   = FALSE
EDITED_THE_STATUS_VALIDATOR     = FALSE
EDITED_ANY_ACCEPTED_TEST        = FALSE
REVISED_B_STRICT                = FALSE
REOPENED_ANY_GAP                = FALSE
IMPLEMENTATION_AUTHORIZED       = FALSE
BRANCH_OR_WORKTREE_CREATED      = FALSE
FROZEN_WORKTREE_MUTATED         = FALSE
```

## 8. Cross-references

```text
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.2.md  section 2
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md  RATIFIED
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md           CURR-S1..S3
CSIA_BOOK_6_IMPLEMENTATION_RUNG_TRACEABILITY_MATRIX_v0.1.md           RUNG 2
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```
