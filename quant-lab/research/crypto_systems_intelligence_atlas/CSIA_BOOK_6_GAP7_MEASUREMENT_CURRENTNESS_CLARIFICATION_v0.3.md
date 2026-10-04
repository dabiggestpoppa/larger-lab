# CSIA — Book 6 GAP-7 Measurement Currentness Clarification v0.3

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION`
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`

**Supersedes:** `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_CLARIFICATION_v0.2.md`
— which superseded v0.1. This version resolves the one entry v0.2 left open,
by carrying a policy the operator selected. It **records that selection; it is
not the instrument of ratification.** The ratification record is
`CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md`.

**Carried unchanged from v0.2:** §§1–6 in full, including the 8-call-site table,
the status quarantine boundary, the withdrawn-claim evidence chain, the per-state
measured matrix, the five distinctions, and the policy-invariant cited-ref and
methodology requirements. Nothing in §§1–6 is reopened, softened or re-derived
here. Only §7 moves, and it moves from `OPEN_OPERATOR_DECISION` to a selected
policy.

---

## 1. Resolution summary

```text
GAP_7_RESOLUTION                        = 7A-KERNEL
GAP_7_KERNEL_WIDE_DEFECT                = TRUE
SINGLE_MEANING_OF_CURRENT               = TRUE
COMPARISON_LOCAL_CURRENTNESS            = PROHIBITED

STATUS_OPTION                           = B-STRICT
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE
STATUS_ONLY_CHANGES_CURRENTNESS         = FALSE

SUPERSESSION_CURRENTNESS_SOURCE         = REGISTERED LINEAGE TERMINALITY
SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS = TRUE
MULTIPLE_SUCCESSOR_LINEAGE              = FAIL_CLOSED

NON_VALUE_BEARING_SOURCELESS_CURRENT_AUTHORITY = FALSE
NV_POLICY                               = NV-B / EVIDENCE_REQUIRED_MISSINGNESS
```

Nine of the ten entries are unchanged from v0.2 and were **not** reopened: the
kernel shape, kernel-wide defect, single meaning of current, the prohibition on
comparison-local currentness, the status direction, the status-is-not-authority
rule, the status-only rule, lineage as the supersession source, no resurrection,
and fail-closed branching. The tenth — non-value-bearing source-less current
authority — moved from `OPEN_OPERATOR_DECISION` to `FALSE`, because the
operator chose NV-B.

## 2. Status doctrine — the single rule

```text
Changing ONLY ObservationStatus, with every authority-bearing structural fact
held identical, MUST NOT change the current-authority outcome.
```

Carried unchanged from v0.2 §2, including the measured finding that the accepted
kernel already complies, and including the status quarantine boundary: B-STRICT
asserts only that `ObservationStatus` is ignored when computing current
authority. It asserts nothing about whether the name `SUPERSEDED` is correctly
placed. The measured validator/docstring incoherence at
`book6_records.py:203` versus `book6_grammar.py:264-268` remains a **separate
future lifecycle-cleanup item**, out of GAP-7 scope, and does not affect
authority, because authority is computed from registered lineage and never from
that field.

## 3. Why 7A-KERNEL

Carried unchanged from v0.2 §3. `resolve_current` has 8 call sites across 3
modules; six are not comparison code, and comparison code cannot hold its own
currentness without violating `COMPARISON_LOCAL_CURRENTNESS = PROHIBITED`. A
repair at any subset of sites leaves the others wrong. The repair goes inside
`resolve_current` and fixes all eight at once.

## 4. What the accepted sources do settle

Carried unchanged from v0.2 §4:

```text
REGISTRATION_IS_NOT_AUTHORITY                        = True   (book6_registry.py)
STRUCTURAL_VALIDATION_ENFORCED_AT_REGISTRATION        = True   (measured)
DUPLICATE_METRIC_DEFINITION_REFUSED                  = True   (measured)
METRIC_DEFINITION_HAS_NO_SUPERSEDE_REPLACE_INVALIDATE = True   (measured)
METHODOLOGY_AUTHORITY_APPLIES_TO_NON_VALUE_BEARING    = True   (measured)
NON_VALUE_BEARING_CAN_BE_HISTORICAL                  = True   (measured)
SOURCE_LESS_MISSINGNESS_CONSTRUCTIBILITY              = ACCEPTED (measured)
SOURCE_LESS_MISSINGNESS_CONSTRUCTION_WITH_EMPTY_REFS = ACCEPTED (measured)
ABSENCE_IS_NOT_ZERO                                  = True   (test_book6_missingness.py:111)
```

## 5. What the accepted sources do not settle — now closed

### 5.1 The withdrawn claim

v0.1 §6.2 stated, verbatim in effect:

> *"**No new policy is invented.** NV-A is the already-ratified behaviour, written
> down. The value-bearing rule is not imposed on missingness records."*

That sentence remains **withdrawn**. The operator's selection of NV-B does not
resurrect it; it makes the sentence unnecessary rather than true. NV-B is a
**new policy choice**, recorded as such in the ratification record.

```text
ACCEPTED_CONSTRUCTION_BEHAVIOR != ACCEPTED_CURRENT_AUTHORITY_DOCTRINE
DEFECTIVE_BEHAVIOR_IS_NORMATIVE_EVIDENCE = FALSE
```

The rule that was measured, and that governs how this program reasons, is not
retired by any operator selection: uniform observed behaviour produced by a
defective branch is still not doctrine.

### 5.2 The evidence chain that was examined

Carried unchanged from v0.2 §5.2. In summary: `resolve_current`
(`book6_registry.py:195-216`) names zero `MissingnessState` members; the
accepted missingness test never calls `resolve_current` or
`is_authoritative_now`; the ratified grammar §6 is descriptive with one
downstream-resolution sentence; and every `NOT_APPLICABLE` hit in the governance
corpus belongs to the coverage enum, not `MissingnessState`. The v0.1 inference
from constructibility and registration to authority does not hold, and no
accepted source settles the question — which is exactly why the question was put
to the operator.

### 5.3 Per-state matrix — measured

Carried unchanged from v0.2 §5.3, with its eight independently executed rows and
its warning that uniformity across the eight states is an artifact of a single
`in` test against a **value-forbiddance** partition, not a considered per-state
authority policy.

That warning is now load-bearing in the ratified direction. NV-B ratifies a
**uniform** rule across all eight states. It reaches that uniformity by explicit
operator policy, **not** by citing the defective branch's uniform behaviour. The
two are independent, and the v0.3 evidence for NV-B is the operator's policy
judgment plus the fail-closed argument in §6, not the measured uniformity.

### 5.4 The five distinctions — unchanged and operative

```text
1 CONSTRUCTION LEGALITY   may the record be built at all?          NV-B: YES
2 REGISTRATION LEGALITY   may the registry accept it?             NV-B: YES
3 QUERYABILITY            can it be read back after authority?    NV-B: YES
4 CURRENT AUTHORITY       does resolve_current return it?         NV-B: NO
5 VALUE READABILITY       may current_value return a number?      NV-B: NO
```

NV-B changes **only** row 4. Rows 1, 2, 3 and 5 keep their measured accepted
behaviour. No historical record is deleted or invalidated by this selection.

---

## 6. The ratified NV-B policy

### 6.1 Construction and authority remain separate

NV-B changes exactly one axis. It does not make source-less missingness
unconstructible, unregisterable, unreadable, or unreadable as a value.

```text
SOURCELESS_MISSINGNESS_CONSTRUCTIBILITY = ACCEPTED
SOURCELESS_MISSINGNESS_REGISTRATION     = ACCEPTED
SOURCELESS_MISSINGNESS_QUERYABILITY     = ACCEPTED
SOURCELESS_MISSINGNESS_CURRENT_AUTHORITY = FALSE
```

A source-less missingness record may still be constructed, registered, and read
back as history, and may still carry no numeric value. What it may not do is
answer an authority-bearing question. No historical record is deleted or
invalidated.

### 6.2 Why fail-closed, in one paragraph

A record that cites nothing has made no falsifiable claim, so nothing can refute
it. Granting it current authority means an unfalsifiable assertion inherits the
authority that Book 2 evidence otherwise has to earn — and the accepted kernel
demonstrates the cost, because it currently grants exactly that on all eight
states and consequently defeats cited Book 2 decay and methodology invalidation
as well. NV-B closes the whole early-return branch, restores live
revalidation for cited and methodology-bearing facts, and pays for it with
uniform refusal of the source-less case. The refusal is the safe direction: a
caller that loses authority can still see the record, but a caller that gains
authority without evidence cannot be audited. This is a **policy choice**, made
by the operator, not a recovery of accepted doctrine.

### 6.3 The authority formula under NV-B

For **all** `MeasurementObservation` records, regardless of missingness state:

```text
CURRENT = TERMINAL
     AND STRUCTURALLY_VALID
     AND METHODOLOGY_CURRENT
     AND HAS_SOURCE_CLAIMS
     AND ALL_SOURCE_CLAIMS_CURRENT
```

`ObservationStatus` is **not** a conjunct. Value-readability is not a conjunct
either — it is enforced separately, by refusing a numeric read.

### 6.4 Applies uniformly to all eight non-value-bearing states

`NOT_APPLICABLE`, `NOT_SUPPORTED`, `NOT_AVAILABLE`, `NOT_COLLECTED`,
`SOURCE_UNAVAILABLE`, `STALE`, `PARTIAL_COVERAGE`, `UNKNOWN`:

```text
source_claim_refs == ()                                  -> NOT CURRENT
source_claim_refs != () AND every cited claim current
                   AND every other authority gate passes -> MAY BE CURRENT
```

No state-specific authority split is ratified. NV-C's per-state table is **not**
adopted; it was never ratifiable as written.

### 6.5 Structural states still require evidence

Under NV-B, even structurally flavoured states require evidence to become
current-authoritative observations:

```text
UNCITED_STRUCTURAL_ASSERTION_IS_CURRENT_AUTHORITY = FALSE
```

This does **not** mean a structural truth must originate in Book 6. It means a
Book 2 claim may **cite** the architecture or protocol evidence supporting it.
The evidence requirement is on the *observation's* assertion of currency, not on
where the underlying fact comes from. This is an **intentional new policy**
chosen by the operator, and it is recorded as new policy, never as pre-existing
accepted doctrine.

### 6.6 Value permission is not authority — do not conflate

```text
VALUE_FORBIDDEN_MISSINGNESS / VALUE_BEARING_MISSINGNESS
    govern whether a NUMERIC VALUE MAY EXIST

NV-B governs whether the record is CURRENT-AUTHORITATIVE

VALUE_PERMISSION_PARTITION != AUTHORITY_PARTITION
```

These partitions are **not** changed by this ratification. The defect that made
them collide was the early return at `book6_registry.py:203`, gated on
`is_value_bearing` — a value-forbiddance test standing in for an authority test.
Removing that early return separates them permanently. The partition
memberships stay exactly as accepted; only their use as an authority predicate
ends.

## 7. What an authority-bearing caller receives

```text
NO CURRENT AUTHORITATIVE MEASUREMENT
```

A source-less missingness record remains historical and queryable. An
authority-bearing caller receives no current authoritative measurement, and may
then resolve that absence according to its own existing ratified rules —
including `INSUFFICIENT_DATA` where those rules already require it.

```text
resolve_current is an AUTHORITY RESOLVER, not a STATE-EMISSION ENGINE
SOURCE_LESS_MISSINGNESS == INSUFFICIENT_DATA  -> NOT ENCODED IN resolve_current
```

`resolve_current` must not encode that mapping. The only place accepted code may
currently produce `INSUFFICIENT_DATA` is downstream resolution under an existing
ratified rule; this ratification does not create a new emission rule and does not
widen an existing one.

## 8. Resolver order — ratified target

```text
1  registered lookup
2  lineage validity
3  terminality
4  definition lookup
5  structural validation
6  methodology authority
7  require source_claim_refs != ()
8  resolve every cited Book 2 claim as current
9  return record
```

```text
NO AUTHORITY-BEARING EARLY RETURN
NO SPECIAL BYPASS FOR NON-VALUE-BEARING OBSERVATIONS
```

Step 7 is the NV-B addition. Steps 1–6 and 8 are the policy-invariant
requirements already established in v0.2 §6 and §6.1, and they were equally
violated by the early return. NV-B does not add them; it stops them from being
bypassed.

## 9. Status

```text
GAP_7_RATIFIED_BY_THIS_ARTIFACT = FALSE   (this artifact records no decision)
BOOK_6_IMPLEMENTATION_AUTHORITY  = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY  = FALSE
LIVE_ACQUISITION_AUTHORITY       = FALSE
```

The ratified doctrine lives in
`CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md`.
