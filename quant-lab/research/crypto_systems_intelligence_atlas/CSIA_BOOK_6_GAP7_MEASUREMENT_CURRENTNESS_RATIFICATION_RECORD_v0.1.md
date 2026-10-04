# CSIA — Book 6 GAP-7 Measurement Currentness Ratification Record v0.1

**Status:** `RATIFIED`
**Record type:** formal governance ratification record
**Date:** 2026-10-03
**Decision id:** `BOOK6-GAP7-v0.3`
**Operator selection:** `RATIFY_7A_KERNEL_WITH_STATUS_B_STRICT_AND_NV_B`
**Scope:** `BOOK 6 CURRENTNESS GOVERNANCE ONLY`
**Grants implementation authority:** `FALSE`

**Precondition satisfied:** `CSIA_BOOK_6_GAP7_PRE_RATIFICATION_REVIEW_v0.3.md`
= `15 / 15 PASS`, `BLOCKING = 0`.

---

## 0. What this record is, and what it is not

This record **ratifies doctrine**. It does not implement anything, and it does
not ratify GAP-6.

```text
RATIFIES     = GAP-7 kernel currentness doctrine
IMPLEMENTS   = NOTHING
CHANGES ANY ACCEPTED SOURCE = FALSE
RATIFIES GAP-6 = FALSE
```

## 1. The ratified decision

```text
GAP_7 = RATIFIED / CLOSED

REPAIR_SURFACE      = 7A-KERNEL
STATUS_DIRECTION    = B-STRICT
NV_POLICY           = NV-B / EVIDENCE_REQUIRED_MISSINGNESS
```

Three components, ratified together as one doctrine:

```text
GAP_7_KERNEL_SHAPE = 7A-KERNEL
STATUS_DIRECTION   = B-STRICT
NV_POLICY          = NV-B
```

## 2. Ratified doctrine, verbatim

```text
GAP_7                                = CLOSED / RATIFIED
SINGLE_MEANING_OF_CURRENT            = TRUE
COMPARISON_LOCAL_CURRENTNESS         = PROHIBITED

OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE
STATUS_ONLY_CHANGES_CURRENTNESS      = FALSE

SUPERSESSION_CURRENTNESS_SOURCE      = REGISTERED_LINEAGE_TERMINALITY
SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS = TRUE
MULTIPLE_SUCCESSOR_LINEAGE           = FAIL_CLOSED

NV_POLICY                            = NV-B
NON_VALUE_BEARING_SOURCELESS_CURRENT_AUTHORITY = FALSE
```

## 3. NV-B — the ratified rule

```text
SOURCELESS_MISSINGNESS_CONSTRUCTIBILITY = ACCEPTED
SOURCELESS_MISSINGNESS_REGISTRATION     = ACCEPTED
SOURCELESS_MISSINGNESS_QUERYABILITY     = ACCEPTED
SOURCELESS_MISSINGNESS_CURRENT_AUTHORITY = FALSE
```

Current authority, for **all** `MeasurementObservation` records:

```text
CURRENT = TERMINAL
     AND STRUCTURALLY_VALID
     AND METHODOLOGY_CURRENT
     AND HAS_SOURCE_CLAIMS
     AND ALL_SOURCE_CLAIMS_CURRENT
```

`ObservationStatus` is **not** a conjunct.

## 4. NV-B is new policy, not recovered doctrine

This is the load-bearing provenance statement of this record.

```text
NV_B_IS_A_NEW_POLICY_CHOICE = TRUE
NV_B_IS_PRE_EXISTING_ACCEPTED_DOCTRINE = FALSE
```

The withdrawn v0.1 §6.2 claim — *"No new policy is invented. NV-A is the
already-ratified behaviour"* — remains **withdrawn and false**. No accepted
source settles the non-value-bearing authority question: `resolve_current`
names zero `MissingnessState` members, the accepted missingness test never calls
the authority resolver, and the ratified grammar §6 is descriptive with a
single downstream-resolution sentence.

The operator selected NV-B as a **policy judgment**. It is recorded here as new
policy. It is never to be cited as pre-existing accepted rule.

```text
DEFECTIVE_BEHAVIOR_IS_NORMATIVE_EVIDENCE     = FALSE
ACCEPTED_CONSTRUCTION_BEHAVIOR
    != ACCEPTED_CURRENT_AUTHORITY_DOCTRINE
```

These two rules survive the ratification. Uniform observed behaviour produced by
the defective branch is still not doctrine, and NV-B's uniformity across the
eight states is reached by explicit policy, not by citing that behaviour.

## 5. Structural states

```text
UNCITED_STRUCTURAL_ASSERTION_IS_CURRENT_AUTHORITY = FALSE
```

`NOT_APPLICABLE`, `NOT_SUPPORTED` and the other structurally flavoured states
require evidence to become current-authoritative observations. This does **not**
require their underlying truth to originate in Book 6: a Book 2 claim may cite
the architecture or protocol evidence supporting the structural fact. The
evidence requirement attaches to the observation's assertion of currency.

This is an **intentional new policy chosen by the operator**, recorded as such.

## 6. Value permission is not authority

```text
VALUE_FORBIDDEN_MISSINGNESS / VALUE_BEARING_MISSINGNESS
    UNCHANGED BY THIS RATIFICATION

VALUE_PERMISSION_PARTITION != AUTHORITY_PARTITION
```

The partitions govern whether a numeric value may exist. They do not govern
authority, and they are not modified here. The defect that made them collide
was the early return at `book6_registry.py:203` gated on `is_value_bearing`; the
ratified repair removes that use.

## 7. Downstream result

An authority-bearing caller receives `NO CURRENT AUTHORITATIVE MEASUREMENT` for a
source-less missingness record. The record remains historical and queryable.
Downstream availability and state logic may resolve that absence under its own
existing ratified rules, including `INSUFFICIENT_DATA` where applicable.

```text
resolve_current is an AUTHORITY RESOLVER, not a STATE-EMISSION ENGINE
source-less missingness == INSUFFICIENT_DATA -> NOT ENCODED IN resolve_current
```

No historical record is deleted or invalidated by this ratification.

## 8. Test contract

```text
TEST_SPEC = CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md
CASES     = 39
IMPLEMENTED = 0

19 carried (CURR-1..15 less CURR-7, CURR-16..23 less CURR-24)
 3 status (CURR-S1, CURR-S2, CURR-S3)
 5 terminality (TERM-1..TERM-5)
10 NV-B concretised (NV-1..NV-10)
 2 structural (STRUCT-1, STRUCT-2)

WITHDRAWN = 2 (CURR-7 superseded by CURR-S1; CURR-24 subsumed)
```

**No relationship to comparison replay is asserted.** This record deliberately
makes no claim about the comparison/change replay count, and none should be
inferred from it. GAP-6 readiness is a separate review.

## 9. Pre-existing supersession now closed

```text
CURR_7 vs CURR_24 INTERNAL CONTRADICTION = RESOLVED (CURR-7 withdrawn)
PRE_RAT_v0.1 VERDICT                      = SUPERSEDED (not false evidence)
PRE_RAT_v0.2 VERDICT                      = SUPERSEDED (HOLD -> satisfied)
NV_OUTCOME v0.1 CLAIM                     = WITHDRAWN
```

## 10. What this record does not do

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
GAP_6_RATIFICATION              = NOT AUTHORIZED BY THIS RECORD
```

The accepted kernel remains **non-compliant** with this doctrine. It fails
`NV-1`, `NV-3`, `NV-9`, `NV-10`, `TERM-2`, `TERM-3`, `TERM-4`, `TERM-5`,
`CURR-S2` and `CURR-S3` today. Ratification fixes the contract; implementation
fixes the kernel, and implementation is a **separate, later decision**.

The eventual Book 6 implementation authorization must cover **both** the GAP-7
kernel currentness hardening **and** the comparison/change amendment, including
GAP-6 if it is ratified.

## 11. Authority flags, post-ratification

```text
GAP_1..GAP_5 = CLOSED / RATIFIED
GAP_6        = 6E DESIGN VALID / RATIFICATION STILL PENDING
GAP_7        = CLOSED / RATIFIED
BOOK_6       = FROZEN_ACCEPTED
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```
