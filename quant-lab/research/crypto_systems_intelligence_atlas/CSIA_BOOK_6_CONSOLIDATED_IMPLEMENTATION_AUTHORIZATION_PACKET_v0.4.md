# CSIA — Book 6 Consolidated Implementation Authorization Packet v0.4

**Status:** `DECIDED` — operator selected **Option A**, `AUTHORIZE_OFFLINE_IMPLEMENTATION` (see §11).
**Date:** 2026-10-04
**Proposed decision id:** `BOOK6-IMPL-CONSOLIDATED-v0.4`
**Grants implementation authority:** `TRUE` — recorded 2026-10-04 via `BOOK6-IMPL-CONSOLIDATED-v0.4`
**Precondition satisfied:** consolidated review **v0.4** = `PASS` (12 / 12)

## Supersession

```text
SUPERSEDES_PROSPECTIVELY =
    CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.3.md
SUPERSESSION_REASON = D2 ENFORCEMENT-LOCATION OVERREACH
v0.3_EDITED = FALSE      (left exactly as committed)
```

Packet v0.3 asked the right question but bound the wrong implementation. Its
§4.2 read:

> `D2 book6_registry.py:172-191  enforce lineage validity / terminality at the
> registry, so branching fails closed on WRITE`

That sentence was never ratified, and implementing it would have changed
registration legality, historical representability and ingestion behaviour. The
question is re-put against a corrected contract.

```text
D2_DOCTRINE_CORRECT            = TRUE
D2_ENFORCEMENT_LOCATION_CORRECT = FALSE
QUESTIONS                      = 1   (unchanged from v0.3)
```

---

## 0. State at the moment of writing — read this first

```text
IMPLEMENTATION HAS NOT BEGUN.
FRESH BRANCH HAS NOT BEEN CREATED.
FRESH WORKTREE HAS NOT BEEN CREATED.
FROZEN BRANCH UNTOUCHED.        (agent/...-book6-build at 5f94c3f40c)
FROZEN WORKTREE UNTOUCHED.      (0 drift, re-measured this round)
ACCEPTED ANCHOR PRESERVED.      (3919fb8052 verified ancestor)
STATUS VALIDATOR UNTOUCHED.
REGISTRATION CODE UNTOUCHED.
```

---

## 1. What is being asked

```text
Authorize offline implementation of the ENTIRE Book 6 amendment?
```

```text
A. AUTHORIZE_OFFLINE_IMPLEMENTATION
B. HOLD
```

## 2. Required scope

```text
1  GAP-7 kernel currentness hardening
2  comparison / change GAP-1..GAP-6
3  the canonical 20-check authority replay
```

---

## 3. The implementation law

These bind any authorized implementation. They are the corrections this packet
exists to carry.

```text
BRANCHING_FAILS_CLOSED_AT_CURRENT_AUTHORITY = TRUE
WRITE_TIME_BRANCH_REJECTION                = NOT AUTHORIZED
STATUS_VALIDATOR_EDIT                      = FORBIDDEN
OBSERVATION_STATUS_AUTHORITY               = FORBIDDEN
```

Concretely:

```text
REGISTRATION_REJECTION_ADDED               = PROHIBITED
INGESTION_BEHAVIOUR_CHANGED                = PROHIBITED
HISTORICAL_RECORDS_UNREGISTERED            = PROHIBITED
RECORDS_MUTATED_OR_REMOVED                 = PROHIBITED
SUPERSEDED_STATUS_REFUSES_AUTHORITY        = FORBIDDEN
OBSERVED_STATUS_PREFERRED                  = FORBIDDEN
RENAME_OBSERVATION_STATUS                  = FORBIDDEN
DELETE_OBSERVATION_STATUS                  = FORBIDDEN
STATUS_ONLY_CHANGES_CURRENTNESS            = MUST REMAIN FALSE
CURRENTNESS_RESOLVER_USES_STATUS           = MUST REMAIN FALSE
```

### 3.1 The four corrected deltas

```text
D1  book6_registry.py:204-205  remove the non-value-bearing early bypass
D2  book6_registry.py:195-216  RESOLVER-LEVEL lineage validity + terminality
                               (ratified resolver steps 2 and 3)
                               NO NEW REGISTRATION REJECTION
D3  book6_records.py:202-215   NO STATUS VALIDATOR AUTHORITY CHANGE
D4  8 call sites + is_authoritative_now   inherit the central fix
```

`D2` targets `resolve_current`. It did not, in v0.3, target that function at
all — it named `book6_registry.py:172-191`, which is `measurement_history`, a
read accessor that already refuses branching and has **zero callers in `src/`**.

### 3.2 Resolver-level branching rule

```text
>1 direct successor  -> lineage invalid -> FAIL CLOSED for CURRENT AUTHORITY
=1 direct successor  -> non-terminal    -> NOT CURRENT
 0 direct successors -> terminality passes -> continue resolver steps 4..9
```

A refused record stays registered, queryable and unmutated.

### 3.3 Successor currentness — stated so it can be overridden

In `A <- B` and `A <- C`: `A` is not current. `B` and `C`, if each is terminal
and passes the other four conjuncts, **are** current. Fail-closed scope is
**per record**.

```text
SUCCESSOR_CURRENTNESS_SCOPE = PER_RECORD
FAMILY_FAIL_CLOSED           = NOT AUTHORIZED
```

The ratified `CURRENT = …` conjunction has exactly five conjuncts. Refusing `B`
would need a sixth, and no ratification supplies one. A component-wide reading
exists and is recorded in review v0.4 §6.4; it is rejected as requiring unratified
policy. This is the single interpretive call in the contract, and it is written
here so the operator can strike it before authorizing.

---

## 4. Option A — `AUTHORIZE_OFFLINE_IMPLEMENTATION`

### 4.1 What it permits

```text
Creating branch  agent/crypto-systems-intelligence-atlas-book6-comparison-change-build
                 from 5f94c3f40cea4441470c57671f51454da7377361
Creating a fresh worktree for that branch
Writing comparison/change source under the 11-rung order
Writing the ratified GAP-7 39-case and comparison 252-case test contracts
Running and committing regression-verified implementation commits
Re-accepting Book 6 under a NEW acceptance commit
```

### 4.2 What it does NOT permit

```text
Mutating the frozen accepted Book 6 worktree or branch
Implementing on, or deriving from, the planning branch
Changing ObservationStatus authority semantics
Editing the SUPERSEDED validator
Adding any registration-time refusal
Changing what registration accepts
Using the historical 19-check replay list
Implementing any reserved selector as a placeholder
Silently aggregating when aggregation == NONE
Inventing a WindowClass conversion or coercion
Broadening fail-closed branching to the whole successor family
Opening GAP-1..GAP-7 for any reason
Status lifecycle cleanup
Class C state benchmark implementation
Any Book 7 or Choir work
Any live acquisition
Force-push, rebase, or history rewrite
```

---

### 4.3 Worktree discipline Option A binds

```text
FRESH_BRANCH_BASE = 5f94c3f40cea4441470c57671f51454da7377361
PRESERVES_ANCHOR  = 3919fb8052e216e94034a753fb258d338c5fa0dc
PLANNING_BRANCH   = UNTOUCHED BY IMPLEMENTATION
FROZEN_WORKTREE   = UNTOUCHED BY IMPLEMENTATION
```

The branch name was re-verified collision-free this round against all 42 remote
heads. It must be re-verified immediately before creation.

## 5. Option B — `HOLD`

Nothing changes. All seven gaps stay CLOSED / RATIFIED, the test contracts stay
ratified, and implementation stays unauthorized.

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
```

`HOLD` remains defensible on grounds unchanged by this round, minus the RUNG 6
condition, which is satisfied:

```text
WANT_A_SECOND_OPINION_ON_THE_REPLAY       (the precedence erratum is recent)
WANT_BOOK_7_SEAM_REVIEWED_FIRST           (the seam was outside review scope)
WANT_TO_BATCH_WITH_OTHER_PROGRAMS        (multi-program sequencing)
WANT_RUNG_6_FALSIFICATION_RATIFIED_FIRST  (SATISFIED 2026-10-04)
WANT_THE_SUCCESSOR_SCOPE_CLARIFIED       (new: review v0.4 §6.3 — see §3.3)
```

The last is new and worth weighing. The successor-currentness reading is an
interpretation, not a quotation. It is derivable and this review states it, but
an operator who wants family-wide fail-closed would need to ratify a sixth
conjunct first. `HOLD` on that ground is defensible.

```text
OPEN_STRENGTHENINGS = 2   (TIME-16 suggested; successor-scope ratification)
```

## 6. Regression gates binding any authorized implementation

```text
B1 = 107   B2 = 108   B3 =  83   B4 = 230   B5 = 293   B6 = 1341   TOTAL = 2162
R1 =  93   R2 =  46   R3 =  45

MAY INCREASE  = B6, and therefore TOTAL
MUST NOT MOVE = B1, B2, B3, B4, B5, R1, R2, R3
```

Sensor, pinned and not reopened:

```text
PINNED_TO = 5f94c3f40cea4441470c57671f51454da7377361
2325 passed / 14 failed / 4 skipped / 0 xfailed   (2343 collected)
The 14 are the canonical evidence-matrix set, pinned by identity.
```

```text
BOOK6_TREE_FINGERPRINT_REQUIRED_FOR_AUTHORIZATION = FALSE
```

## 7. Explicit state required by this packet

```text
TIME-1..TIME-15  = RATIFIED
RUNG 6           = GREEN
ALL RUNGS        = GREEN  (11 / 11)
B-STRICT         = PRESERVED
STATUS VALIDATOR = OUT OF SCOPE
WRITE-TIME BRANCH REJECTION = NOT AUTHORIZED
```

## 8. Supporting artifacts

```text
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.4.md   PASS 12/12
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.4.md   this file
CSIA_BOOK_6_IMPLEMENTATION_RUNG_TRACEABILITY_MATRIX_v0.2.md            11 GREEN
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.3.md            TERM-4
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_CLARIFICATION_v0.3.md        resolver order
CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_RATIFICATION_RECORD_v0.1.md RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_TIME_TEST_RATIFICATION_RECORD_v0.1.md    RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_IMPLEMENTATION_TEST_SPEC_v0.5.md        252 cases
CSIA_BOOK_6_COMPARISON_CHANGE_GAP6_RATIFICATION_RECORD_v0.1.md         RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_SUBSTRATE_RATIFICATION_RECORD_v0.1.md    RATIFIED
CSIA_BOOK_6_COMPARISON_CHANGE_REPLAY_PRECEDENCE_ERRATUM_v0.1.md       RATIFIED
CSIA_BOOK_6_SENSOR_REGRESSION_BASELINE_PIN_v0.1.md                     PINNED
CSIA_BOOK_6_STATUS_VALIDATOR_LIFECYCLE_AMENDMENT_DEFERRED_v0.1.md     OUT OF SCOPE
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.3.md   SUPERSEDED
CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.3.md   SUPERSEDED
CSIA_OPERATOR_DECISION_LOG.md
CSIA_PLANNING_PROGRESS.md
```

## 9. Exact next operator action

```text
1. Read   CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_REVIEW_v0.4.md
2. Note   packet v0.4 §3.3 — the successor-currentness reading
3. Select exactly one:
     BOOK6-IMPL-CONSOLIDATED-v0.4 = AUTHORIZE_OFFLINE_IMPLEMENTATION
                                  | HOLD
```

```text
DECISIONS_OUTSTANDING = 1
```

Until the selection is recorded:

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = FALSE
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

## 10. Explicit non-actions taken in producing this packet

```text
IMPLEMENTATION_STARTED       = FALSE
SOURCE_FILE_WRITTEN          = FALSE
SOURCE_FILE_EDITED           = FALSE
REGISTRATION_CODE_EDITED     = FALSE
TEST_FILE_WRITTEN            = FALSE
TEST_CASE_EXECUTED           = FALSE
BRANCH_CREATED               = FALSE
WORKTREE_CREATED             = FALSE
FROZEN_BRANCH_TOUCHED         = FALSE
FROZEN_WORKTREE_TOUCHED       = FALSE
STATUS_VALIDATOR_TOUCHED     = FALSE
RATIFIED_RECORD_EDITED       = FALSE
REVIEW_v0.3_EDITED           = FALSE
PACKET_v0.3_EDITED           = FALSE
GAP_REOPENED                 = FALSE
BOOK_7_WORKED_ON             = FALSE
CHOIR_TOUCHED                = FALSE
```

---

**Status:** `AWAITING_OPERATOR_DECISION`. Nothing has been implemented.

---

## 11. Recorded decision

```text
DECISION LOG ENTRY {
  decision_id:            BOOK6-IMPL-CONSOLIDATED-v0.4
  operator_selection:     AUTHORIZE_OFFLINE_IMPLEMENTATION   (Option A)
  source_packet:          CSIA_BOOK_6_CONSOLIDATED_IMPLEMENTATION_AUTHORIZATION_PACKET_v0.4.md
  precondition:           consolidated review v0.4 = PASS 12 / 12
                          KNOWN_EVIDENCE_GAPS = 0; GREEN_RUNGS = 11 / 11
  effective_artifact:     this packet, §3 implementation law
  scope_authorized:       A GAP-7 kernel currentness hardening
                          B comparison / change GAP-1..GAP-6
                          C canonical 20-check authority replay
                          D ratified GAP-7 39-case test contract
                          E ratified comparison 252-case test contract
                          F regression and traceability work
  scope_excluded:        status lifecycle cleanup
                          Class C state benchmark
                          Book 7
                          live acquisition
                          reserved selectors
                          new aggregation semantics
                          NEW REGISTRATION POLICY
  immediate_consequence:  BOOK_6_IMPLEMENTATION_AUTHORITY = TRUE,
                          offline amendment scope only
  reversibility:          via a later recorded decision in
                          CSIA_OPERATOR_DECISION_LOG.md, never silently
  effective_timestamp:    2026-10-04
}
```

### 11.1 The law that was authorized

```text
BRANCHING_FAILS_CLOSED_AT_CURRENT_AUTHORITY = TRUE
WRITE_TIME_BRANCH_REJECTION                = NOT AUTHORIZED
STATUS_VALIDATOR_EDIT                      = FORBIDDEN
SUCCESSOR_CURRENTNESS_SCOPE                = PER_RECORD
TIME-1..TIME-15                            = RATIFIED
ALL_RUNGS                                  = GREEN
B-STRICT                                   = PRESERVED
```

### 11.2 Authority flags after this decision

```text
BOOK_6_IMPLEMENTATION_AUTHORITY = TRUE   (OFFLINE AMENDMENT SCOPE ONLY)
BOOK_7_IMPLEMENTATION_AUTHORITY = FALSE
LIVE_ACQUISITION_AUTHORITY      = FALSE
```

### 11.3 What this decision did not start

```text
IMPLEMENTATION_STARTED   = FALSE
BRANCH_CREATED           = FALSE
WORKTREE_CREATED         = FALSE
SOURCE_FILE_WRITTEN      = FALSE
TEST_CODE_WRITTEN        = FALSE
```

Authority is granted; execution is a separate act. Nothing has been built. The
next session consumes this authorization and executes the 11-rung build against a
fresh branch at `5f94c3f40c`.

```text
NEXT_ACT = CREATE BRANCH agent/crypto-systems-intelligence-atlas-book6-comparison-change-build
           FROM 5f94c3f40cea4441470c57671f51454da7377361
           RE-VERIFY COLLISION-FREE IMMEDIATELY BEFORE CREATION
```
