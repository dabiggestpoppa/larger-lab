# CSIA — Book 6 Consolidated Implementation Authorization Review v0.4

**Status:** `AUDIT_FINDING` — assesses authorization readiness; ratifies nothing.
**Date:** 2026-10-04
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE` (see `CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.4.md`)
**Reviewed against planning HEAD:** `5bb6eba8`
**Implementation base:** `5f94c3f40cea4441470c57671f51454da7377361`
**Accepted anchor:** `3919fb8052e216e94034a753fb258d338c5fa0dc`

```text
REVIEW_TYPE = CONSOLIDATED_PRE_IMPLEMENTATION_AUTHORIZATION
VERDICT     = PASS (12 / 12)

GREEN_RUNGS          = 11 / 11
KNOWN_EVIDENCE_GAPS  =  0
```

## Supersession

```text
SUPERSEDES_PROSPECTIVELY =
    CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.3.md
SUPERSESSION_REASON = D2 ENFORCEMENT-LOCATION OVERREACH
v0.3_EDITED = FALSE
```

```text
AUTH_REVIEW_v0.3 = SUPERSEDED / D2 ENFORCEMENT-LOCATION OVERREACH
```

**The D2 doctrine is correct.** Fail-closed branching is ratified. What v0.3 got
wrong was *where* it is enforced. v0.3 stated the delta as *"lineage /
terminality enforced at the registry … so branching fails closed on WRITE."*
That location was never ratified, and it changes three things the operator never
agreed to: registration legality, historical representability, and ingestion
behaviour.

```text
D2_DOCTRINE_CORRECT            = TRUE
D2_ENFORCEMENT_LOCATION_CORRECT = FALSE
D2_REVISED                     = TRUE
```

---

## 1. The ratified evidence

Three ratified artifacts settle this. None mentions registration rejection.

### 1.1 `TERM-4` — test spec v0.3 lines 122 and 135–139

```text
| `TERM-4` | `A <- B` and `A <- C` | lineage invalid; fail closed; `A` not current |
```

> `TERM-4` must fail closed at the resolver, not merely at the
> `measurement_history` accessor. The accepted kernel currently refuses branching
> only in `measurement_history` (`book6_registry.py:172-191`) and **accepts**
> multiple successors at registration. Ratified doctrine requires the resolver to
> refuse.

The sentence names the resolver as the required enforcement point and names
registration acceptance as the *current* state, not as a defect to repair there.

### 1.2 Resolver order — clarification v0.3 §8, "ratified target"

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

Lineage validity is **step 2 inside the authority resolver**. It is a read gate.

### 1.3 `REGISTRATION_IS_NOT_AUTHORITY` — clarification v0.3 §4

```text
REGISTRATION_IS_NOT_AUTHORITY = True   (book6_registry.py)
```

An explicit ratified statement, in the accepted-sources table, that registration
is not an authority surface. A write-time refusal is an authority surface.

### 1.4 Conclusions

```text
LINEAGE_VALIDITY_IS_A_READ_AUTHORITY_GATE    = TRUE
WRITE_TIME_BRANCH_REJECTION_RATIFIED        = FALSE
SECOND_SUCCESSOR_REGISTRATION_MUST_BE_REJECTED = FALSE
BRANCHED_LINEAGE_CANNOT_RESOLVE_CURRENT     = TRUE
BRANCHING_REGISTRATION_POLICY               = NOT GOVERNED BY GAP-7
```

### 1.5 The accepted kernel, measured read-only

```text
register_measurement            book6_registry.py:123-144
  checks    duplicate id; definition registered; methodology;
            validate_against_definition
  does NOT check supersession linearity
  docstring: "Registration-time checking is necessary but NOT sufficient:
              authority is re-resolved live by resolve_current"

measurement_history             book6_registry.py:172-191
  raises on >1 successor  <- ALREADY REFUSES BRANCHING
  CALLERS IN src/ = 0

resolve_current                 book6_registry.py:195-216
  no lineage check of any kind
  early return for non-value-bearing at :204-205
```

`measurement_history` has **zero callers in `src/`**. Its branching refusal is
real code and a complete no-op for authority. This is why v0.3's D2 was wrong
twice over: it named a line range that already refuses branching, and described
a write path that neither that range nor any ratified clause governs.

---

## 2. The corrected deltas

```text
D1  book6_registry.py:204-205  remove the non-value-bearing early bypass
                               (function span :195-216, resolve_current)

D2  book6_registry.py:195-216  RESOLVER-LEVEL lineage validity + terminality,
                               at ratified resolver steps 2 and 3.
                               NO NEW REGISTRATION REJECTION.

D3  book6_records.py:202-215   NO STATUS VALIDATOR AUTHORITY CHANGE

D4  8 call sites + is_authoritative_now   inherit the central fix
```

### 2.1 What D2 now says, exactly

Accepted registration behaviour remains unchanged. During
`resolve_current(measurement_id)`:

```text
- inspect the resolved record's registered successor relationships
- more than one direct successor  -> lineage invalid
                                  -> FAIL CLOSED for CURRENT AUTHORITY
- exactly one direct successor    -> non-terminal, NOT CURRENT
- zero direct successors          -> terminality passes; continue steps 4..9
```

```text
MULTIPLE_SUCCESSOR_LINEAGE  = FAIL_CLOSED_AT_CURRENT_AUTHORITY
REGISTRATION_MUTATION       = NONE
REGISTRATION_REJECTION_ADDED = FALSE
HISTORICAL_RECORDS_PRESERVED = TRUE
```

A refused record is **not** removed, **not** mutated, and **not** unregistered.
It remains queryable history. That is what "fail closed" means here: the
authority question is answered NO, and nothing else changes.

### 2.2 What D2 must not become

```text
WRITE_TIME_BRANCH_REJECTION              = NOT AUTHORIZED
SECOND_SUCCESSOR_REGISTRATION_REJECTED   = PROHIBITED
HISTORICAL_BRANCHED_LINEAGE_UNREGISTERED = PROHIBITED
INGESTION_BEHAVIOUR_CHANGED              = PROHIBITED
REGISTRATION_LEGALITY_CHANGED            = PROHIBITED
```

Three things follow from refusing to touch registration, and all three are
ratified rather than assumed. Historical representability is protected by `NV-5`
(*"the record itself is never mutated or removed"*, itself restated in
`resolve_current`'s own docstring). Ingestion behaviour is unchanged because
`register_measurement` is unchanged. Registration legality is unchanged because
no clause was ratified that changes it.

### 2.3 D1 and D2 now share a function

In v0.3 they pointed at different line ranges, which was itself a symptom of the
confusion. Ratified resolver steps 2 and 3 and the early bypass all live inside
`resolve_current`. One function, two edits, one authority surface.

```text
D1_TARGET = resolve_current
D2_TARGET = resolve_current
D3_TARGET = book6_records._check_supersession_discipline  (NO CHANGE)
```

### 2.4 `is_authoritative_now` inherits for free

```text
book6_registry.py:218-226
  def is_authoritative_now(...):
      try:    self.resolve_current(measurement_id)
      except (Book6RegistryError, Book6ProvenanceError): return False
      return True
```

It delegates. `TERM-4`'s second assertion — `is_authoritative_now("A")` is
`FALSE` — therefore follows from the D2 fix without a separate edit. Recorded so
the implementer does not "harden" it independently.

---

## 3. Registration policy — result

```text
REGISTRATION_POLICY_CHANGED      = FALSE
REGISTRATION_REJECTION_ADDED     = FALSE
WRITE_TIME_BRANCH_REJECTION      = NOT AUTHORIZED
INGESTION_BEHAVIOUR_CHANGED      = FALSE
HISTORICAL_REPRESENTABILITY      = PRESERVED
```

The accepted kernel will continue to accept two successors of one predecessor.
That is not a defect left in place; it is a behaviour GAP-7 does not govern.

```text
ACCEPTED_KERNEL_BRANCHING_REGISTRATION = ACCEPTED
GAP_7_MUTATES_IT                        = NO
```

## 4. `measurement_history` — relationship

```text
measurement_history branching refusal = PRESERVED UNCHANGED
resolve_current    branching refusal = REQUIRED (this is D2)
registration       branching refusal = NOT REQUIRED
```

`measurement_history` keeps its existing refusal, and it must keep it: it is the
structural accessor's honest answer to an ill-formed chain, and deleting it would
change accepted behaviour for no ratified reason.

It must **not** be treated as the authority gate. It has no callers in `src/`,
`resolve_current` never invokes it, and `TERM-4` explicitly rejects
`measurement_history`-only enforcement.

```text
measurement_history_IS_THE_AUTHORITY_GATE = FALSE
measurement_history_MAY_BE_THE_ONLY_GATE  = PROHIBITED BY TERM-4
```

## 5. `TERM-4` implementation contract

Ratified `TERM-4` is now testable exactly as written. Register:

```text
A
B  supersedes A
C  supersedes A
```

Registration **succeeds exactly as accepted**, unless some other pre-existing
accepted rule independently refuses it — duplicate id, unregistered definition,
missing methodology, or `validate_against_definition`. No linearity check is
added and none is removed.

Then:

```text
resolve_current("A")           -> REFUSE / NOT CURRENT, reason LINEAGE INVALID
is_authoritative_now("A")      -> FALSE
registered_measurement("A")    -> STILL RETURNS A   (history preserved)
measurement_history("A")       -> STILL REFUSES     (unchanged behaviour)
```

### 5.1 What the refusal must NOT do

```text
NO ARBITRARY B/C SELECTION
NO LEXICAL CHOICE BETWEEN B AND C
NO observed_at CHOICE
NO REGISTRATION-ORDER CHOICE
NO STATUS-BASED REFUSAL
NO UNREGISTRATION OF A, B OR C
```

There is no tie-break to invent here. `A` is refused because its own successor
set is branched, not because another candidate outranks it. Ranking, lexical
ordering and `observed_at` are `TIME-1..TIME-15` machinery and play no part.

```text
REFUSAL_REASON_A  = LINEAGE_INVALID
SELECTION_RAN     = FALSE
TIE_BREAK_RAN     = FALSE
STATUS_READ       = FALSE
```

---

## 6. Successor currentness — scope

The question: in `A <- B` and `A <- C`, may `B` and `C` independently resolve
current, if each is terminal and otherwise valid?

This review **did not assume** an answer, and did not broaden fail-closed scope.

### 6.1 What the ratified text actually says

```text
clarification v0.3 §1   MULTIPLE_SUCCESSOR_LINEAGE = FAIL_CLOSED
test spec v0.3 §5       TERM-4 | A <- B and A <- C | lineage invalid;
                        fail closed; A not current
```

Neither names `B` or `C`. No ratified artifact invalidates the family.

### 6.2 The deciding argument — the conjunction is exhaustive

Ratification record v0.1 §3 defines current authority for **all**
`MeasurementObservation` records, conjunctively:

```text
CURRENT = TERMINAL
     AND STRUCTURALLY_VALID
     AND METHODOLOGY_CURRENT
     AND HAS_SOURCE_CLAIMS
     AND ALL_SOURCE_CLAIMS_CURRENT
```

Five conjuncts. `TERMINAL` is a property of the record's **own** registered
successor set — it is how a record knows it has been superseded, and it is what
makes `A` non-current under `TERM-2`, `TERM-3` and `TERM-4` alike.

For `B` in a branched family: `B` has no registered successor, so `TERMINAL`
holds. If the other four conjuncts hold, `B` is current. **Refusing `B` would
require a sixth conjunct** — something like `NOT_IN_BRANCHED_COMPONENT` — and no
ratification supplies one.

```text
CURRENT_IS_AN_EXHAUSTIVE_CONJUNCTION = TRUE
CONJUNCTS                            = 5
A_SIXTH_CONJUNCT_WAS_RATIFIED        = FALSE
FAIL_CLOSED_FAMILY_SCOPE_WOULD_NEED_A_SIXTH_CONJUNCT = TRUE
```

That is the whole reason the scope is determined rather than arbitrary.

### 6.3 Result

```text
SUCCESSOR_CURRENTNESS_SCOPE     = PER_RECORD
A_BRANCHED                      -> NOT CURRENT  (TERM-4)
B_OR_C_TERMINAL_AND_VALID       -> CURRENT      (conjunction applied)
REGISTRATION_OF_B_AND_C         -> UNCHANGED ACCEPTED

FAMILY_FAIL_CLOSED              = NOT RATIFIED
FAMILY_FAIL_CLOSED_IMPLEMENTED  = NO
```

### 6.4 The alternative, recorded rather than hidden

"Lineage validity" at resolver step 2 could be read *component-wise* — every
record in a branched connected component fails. That reading is not absurd on
its face. It is rejected for one reason only: it cannot be derived from the
ratified conjunction without adding a conjunct, and this program does not add
policy by interpretation.

```text
REJECTED_ALTERNATIVE = COMPONENT_WIDE_FAIL_CLOSED
REJECTION_GROUND     = REQUIRES AN UNRATIFIED SIXTH CONJUNCT
IS_THIS_A_HOLD_TRIGGER = NO — the text is determinate, and this review
                         states which reading it implements so the operator
                         can override it before implementation begins
```

The implementation law in packet v0.4 states this explicitly for exactly that
reason.

---

## 7. The B-STRICT implementation law — carried unchanged

Two otherwise identical terminal records differing only in `status` receive the
**same** authority verdict. Status can grant, remove, restore or destroy
authority: all `FALSE`.

```text
REFUSAL_REASONS_THAT_READ_STATUS = NONE
```

The refusal vocabulary after this correction:

```text
REGISTRATION  LINEAGE  TERMINALITY  STRUCTURE
METHODOLOGY_CURRENT  SOURCE_CLAIMS_ABSENT  SOURCE_CLAIMS_STALE
```

`LINEAGE` is in that list because of `TERM-4`, and it is the *only* new entry.
It is a lineage refusal, not a status refusal.

```text
RATIFIED_CASES = 39  (CARR-1..19, CURR-S1..3, TERM-1..5, NV-1..10, STRUCT-1..2)
STATUS_VALIDATOR_EDIT_REQUIRED    = FALSE
CURRENTNESS_RESOLVER_USES_STATUS  = FALSE
B_STRICT_PRESERVED                = TRUE
```

## 8. The twelve criteria, re-run

Criterion 3 was the one at risk. It is `TRUE` **only because** no write-time
branching policy remains anywhere in the contract.

| # | Criterion | v0.3 | v0.4 | Evidence |
|---|---|---|---|---|
| 1 | `NO_UNRATIFIED_POLICY_NEEDED` | TRUE | **TRUE** | 0 coder policy choices; §6.4 alternative rejected, not adopted |
| 2 | `NO_AUTHORITY_DESIGN_GAP` | TRUE | **TRUE** | resolver steps 2–3 now have a named enforcement point |
| 3 | `GAP7_IMPLEMENTATION_CONTRACT_COMPLETE` | TRUE | **TRUE** | D1+D2 both in `resolve_current`; **no write-time branching policy remains** |
| 4 | `COMPARISON_CONTRACT_COMPLETE` | TRUE | **TRUE** | 5 closed gaps, closed objects, closed selector set, 11 conditions |
| 5 | `GAP6_ORDERING_CONTRACT_COMPLETE` | TRUE | **TRUE** | ratified `BOOK6-GAP6-v0.2`; 15 TIME cases ratified |
| 6 | `CANONICAL_20_CHECK_REPLAY_UNAMBIGUOUS` | TRUE | **TRUE** | one canonical source, 20 enumerated |
| 7 | `TEST_CONTRACT_COMPLETE` | TRUE | **TRUE** | 237 + 15 = 252; `BLOCKED = 0` |
| 8 | `IMPLEMENTATION_ORDER_COMPLETE` | TRUE | **TRUE** | 11 rungs, all GREEN |
| 9 | `FRESH_BRANCH_STRATEGY_VALID` | TRUE | **TRUE** | derives from `5f94c3f40c`; name re-verified collision-free |
| 10 | `UPSTREAM_FREEZE_PRESERVABLE` | TRUE | **TRUE** | frozen worktree untouched, re-measured this round |
| 11 | `BOOK1_5_FREEZE_PRESERVABLE` | TRUE | **TRUE** | B1–B5 re-measured exact |
| 12 | `SENSOR_FREEZE_PRESERVABLE` | TRUE | **TRUE** | pinned to `5f94c3f40c`, not re-run |

```text
CRITERIA          = 12
TRUE              = 12
FALSE             =  0
CRITERION_CHANGED_VALUE = 0
CRITERION_CHANGED_EVIDENCE = 3   (criteria 2, 3, and the D2 anchor itself)

GREEN_RUNGS          = 11 / 11
KNOWN_EVIDENCE_GAPS  =  0
HOLD_REQUIRED        = FALSE
```

### 8.1 What changed against v0.3

No criterion changed value. Three pieces of evidence got stronger or more
precise, and the D-delta table was corrected. That is the correct shape for a
defect that was over-specification rather than a design error.

```text
v0.3_VERDICT = PASS 12 / 12
v0.4_VERDICT = PASS 12 / 12
DIFFERENCE    = D2 CORRECTED; NO CRITERION CHANGED VALUE
```

## 9. Rung counts

```text
RUNGS_MAPPED       = 11
GREEN_RUNGS        = 11
AMBER_RUNGS        =  0
RED_RUNGS          =  0
KNOWN_EVIDENCE_GAPS = 0

ALL_IMPLEMENTATION_RUNGS_HAVE_RATIFIED_FALSIFICATION = TRUE
```

The matrix needs no correction for this round: it never carried a D-delta list
and never mentioned registration. The overreach lived only in review v0.3 §1.1
and packet v0.3 §4.2, both of which are superseded by the v0.4 pair.

```text
RUNG_TRACEABILITY_MATRIX_v0.2_REQUIRES_CORRECTION = FALSE
```

## 10. Authority flags and non-actions

```text
GAP_7_REOPENED                   = FALSE
GAP_6_REOPENED                   = FALSE
RATIFIED_RECORD_EDITED           = FALSE
REVIEW_v0.3_EDITED               = FALSE
PACKET_v0.3_EDITED               = FALSE
DOCTRINE_CHANGED                 = FALSE
REGISTRATION_POLICY_CHANGED      = FALSE
SOURCE_CHANGED                   = FALSE
TEST_CODE_WRITTEN                = FALSE
TEST_CASE_EXECUTED               = FALSE
BRANCH_CREATED                   = FALSE
WORKTREE_CREATED                 = FALSE
FROZEN_WORKTREE_MUTATED          = FALSE
SENSOR_SUITE_RERUN               = FALSE
```

`KNOWN_EVIDENCE_GAPS = 0` for the authorization contract. The one residual from
the previous round — `TERMINALITY_SPECIFICITY_PROVEN_BY_TIME_11_ALONE = FALSE`,
and its suggested `TIME-16` hardening — is unchanged, non-gating, and recorded
again here so it is not quietly forgotten.

```text
OPEN_STRENGTHENINGS = 1   (TIME-16, suggested, non-gating)
```
