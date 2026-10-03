# CSIA — Book 6 GAP-7 Measurement Currentness Test Spec v0.2

**Status:** `DRAFT_PENDING_OPERATOR_RATIFICATION` — specification only.
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Cases:** 27 (`CURR-1..15` less `CURR-7`, `CURR-S1..S3`, `CURR-16..23` less `CURR-24`, `NV-1..NV-5`); 0 implemented.

**Supersedes:** `CSIA_BOOK_6_GAP7_MEASUREMENT_CURRENTNESS_TEST_SPEC_v0.1.md`
(24 cases). Superseded, not withdrawn — see §1 for the exact defect.

---

## 0. Why v0.2 exists

An external review of v0.1 found two defects and refused ratification.

```text
DEFECT_A = CURR-7 and CURR-24 contradict each other.
DEFECT_B = NV-A is not proven as accepted current-authority doctrine.
```

v0.2 corrects both. Every correction below is backed by an executed probe
against accepted implementation `5f94c3f40c` (baseline **2162 passed**), not by
restatement.

---

## 1. Defect A — the status contradiction, resolved

### 1.1 What v0.1 said

| Case | v0.1 text | Decision it makes |
|---|---|---|
| CURR-7 | a `SUPERSEDED`-status record that is terminal → *refused (never current)* | status decides |
| CURR-24 | a terminal record carrying legacy status `SUPERSEDED` → *current iff the other conjuncts hold* | status does not decide |

Both cannot hold. One of them makes `ObservationStatus` an authority input.

### 1.2 The one rule

Under the ratified status direction,

```text
OBSERVATION_STATUS_IS_CURRENTNESS_AUTHORITY = FALSE
STATUS_ONLY_CHANGES_CURRENTNESS            = FALSE
```

**Changing only `ObservationStatus`, while every authority-bearing structural
fact stays identical, MUST NOT change the current-authority outcome.** One rule,
no exceptions, no second path.

### 1.3 Measured — status is already not an authority input

Executed against accepted `5f94c3f40c`. Two records, identical in every field
except `ObservationStatus`, both terminal successors, same live claim, same
methodology:

```text
status=OBSERVED    -> registered   resolve_current: CURRENT
status=SUPERSEDED  -> registered   resolve_current: CURRENT
ObservationStatus members: ['OBSERVED', 'SUPERSEDED']
```

So the accepted kernel **already** behaves as B-STRICT requires. Consequence:
**CURR-7 as written in v0.1 would FAIL if implemented**, because it demands a
status-driven refusal the kernel does not produce. CURR-24 agrees with measured
behaviour.

**Disposition:** `CURR-7` is **superseded** by `CURR-S1`. `CURR-24` is
**subsumed** by `CURR-S1`/`CURR-S2` and is withdrawn as a separate case to
remove the duplicated, contradictory statement. Both dispositions are recorded
so the lineage is auditable.

### 1.4 A construction constraint the cases must respect

`ObservationStatus` has exactly two members (`book6_grammar.py:264-272`), and
`book6_records.py:203` refuses any record whose `status is SUPERSEDED` unless
it names `supersedes_measurement_id`. Measured: marking a *predecessor*
`SUPERSEDED` — which the `ObservationStatus` docstring says is the intended
meaning — is **refused for value-bearing and non-value-bearing records alike**.

Therefore a legal status flip must hold `supersedes_measurement_id` constant.
`CURR-S1` is specified as a **twin pair** (§4) for exactly this reason. This
entanglement is a further, independent argument against making status
authority-bearing.

---

## 2. Resolver order the cases assume

Every case is stated against the proposed 7A-KERNEL resolver. The order is
normative for the test contract:

```text
resolve_current(measurement_id):
  1. registered lookup                      -> REFUSE if absent
  2. lineage validity (unique successor)    -> REFUSE if branched
  3. terminality                            -> REFUSE if a successor exists
  4. definition lookup                      -> REFUSE if absent
  5. structural validation                  -> REFUSE on drift
  6. methodology authority                  -> REFUSE if not current
  7. missingness/evidence authority path    -> per operator NV decision, see §6
  8. Book 2 authority, where refs are cited -> REFUSE if any ref decayed
  9. return record
```

**No authority-bearing early return may occur before step 9.** The accepted
kernel violates this at its step-0 position; that is the defect GAP-7 repairs.

```text
COMPARISON_LOCAL_CURRENTNESS = PROHIBITED
```

---

## 3. Carried supersession cases (`CURR-1` .. `CURR-15`)

Carried unchanged from the audit §10 and v0.1 §2. `CURR-7` is the sole
exception and is superseded per §1.3.

| ID | Setup | Required result |
|---|---|---|
| CURR-1 | A only, OBSERVED, terminal, live | `resolve_current("A")` returns A |
| CURR-2 | A <- B, both OBSERVED, both live | A **refused**; B current |
| CURR-3 | A <- B, then B's cited claim decays | both refused; `CURRENT = NONE` |
| CURR-4 | A <- B, then B's methodology stops authorizing | both refused; `CURRENT = NONE` |
| CURR-5 | A <- B <- C, all live | A and B refused; C current |
| CURR-6 | A has B and C as direct successors | step 2 refuses; lineage invalid |
| ~~CURR-7~~ | ~~SUPERSEDED-status record that is terminal~~ | **SUPERSEDED — withdrawn.** Status may not decide. Replaced by `CURR-S1`. |
| CURR-8 | `status == OBSERVED` alone, with a successor present | **insufficient** — refused, and refused *by lineage*, never by status |
| CURR-9 | `resolve_current(A predecessor)` | raises / refuses |
| CURR-10 | `is_authoritative_now(A predecessor)` | `False` |
| CURR-11 | a normalization rule citing predecessor A | refused; no normalized value |
| CURR-12 | comparison over `{A, B}` | predecessor filtered before ordering; A absent |
| CURR-13 | lexical tie-break over a set containing A | A never enters the candidate set |
| CURR-14 | `registered_measurement("A")` after supersession | still returns A |
| CURR-15 | successor loses authority, then re-check | A **does not** resurrect |

Note on CURR-8: v0.1 stated the correct *outcome* but attributed it to status.
The refusal must come from **registered lineage terminality** at step 3. The
outcome is unchanged; the reason is now pinned.

---

## 4. Status cases (`CURR-S1` .. `CURR-S3`) — replace `CURR-7` / `CURR-24`

### CURR-S1 — status-only variation cannot change authority

**Setup.** Twin pair, identical in every authority-bearing field — subject,
metric, window, missingness, value, unit, methodology identity, cited refs,
lineage role — differing **only** in `ObservationStatus`.

Because `book6_records.py:203` requires a `SUPERSEDED` record to name what it
supersedes (§1.4), the twins are built on two structurally identical
predecessors `P` and `P'` so that each twin holds a legal, constant
`supersedes_measurement_id` and no branching is introduced.

```text
P  <- A   A.status = OBSERVED
P' <- B   B.status = SUPERSEDED     P and P' are structurally identical
```

**Required.** `resolve_current("A")` and `resolve_current("B")` return the
**same verdict**, and `is_authoritative_now` agrees for both.

**Status.** Satisfied by accepted `5f94c3f40c` today (measured, §1.3).

### CURR-S2 — a status change alone neither resurrects nor invalidates

**Setup.** Take the terminal current record from CURR-S1. Vary **only** its
`ObservationStatus`; keep lineage, methodology, cited refs and structure fixed.

**Required.** The record is not resurrected and is not invalidated by the status
write alone.

```text
terminal + structurally valid + methodology current + evidence current
    status OBSERVED   -> CURRENT
    status SUPERSEDED -> CURRENT      (same verdict; see CURR-S1)
```

A record whose lineage has advanced is refused whatever its status, and a
record whose methodology has been invalidated is refused whatever its status.

**Status.** Satisfied by accepted `5f94c3f40c` today.

### CURR-S3 — terminality DOES change authority, and only terminality does

**Setup.** Twin pair identical to CURR-S1, but now vary **lineage** instead of
status: register a successor for one twin only.

**Required.**

```text
no successor  -> CURRENT
successor     -> REFUSED   (predecessor is historical, never resurrected)
```

This is the positive half of the status rule: something *does* move authority,
and it is terminality derived from registered lineage
(`SUPERSESSION_CURRENTNESS_SOURCE = REGISTERED LINEAGE TERMINALITY`), never
`ObservationStatus`.

**Status.** **FAILS** against accepted `5f94c3f40c`. Measured: a superseded
non-value-bearing predecessor still resolves `CURRENT`, because `resolve_current`
never consults lineage. This is the kernel-wide defect GAP-7 repairs.

---

## 5. Carried non-value-bearing and evidence cases (`CURR-16` .. `CURR-23`)

| ID | Setup | Required result |
|---|---|---|
| CURR-16 | non-value-bearing, `source_claim_refs=(c)`, `c` **current** | follows the operator NV policy (§6); cited refs re-resolved at step 8 |
| CURR-17 | non-value-bearing, `source_claim_refs=(c)`, `c` **decayed** | **not current** — step 8 refuses, no early-return bypass |
| CURR-18 | non-value-bearing, `source_claim_refs=()` | outcome fixed by the operator NV decision (§6). **Currently UNRESOLVED.** |
| CURR-19 | predecessor A after supersession | `registered_measurement("A")` returns A; history intact |
| CURR-20 | any `resolve_current` call | **no mutation** of any record, store or order list |
| CURR-21 | branching lineage `A <- B`, `A <- C` | `resolve_current(A/B/C)` all refuse; `is_authoritative_now` `False` for all |
| CURR-22 | observation structurally drifted from its registered definition | current authority **fails** at step 5 |
| CURR-23 | any route flipping `ObservationStatus` | current authority **unchanged** — status quarantined |

`CURR-24` is withdrawn as a separate case; it restated CURR-S1 in contradictory
wording (§1.3).

---

## 6. Non-value-bearing authority cases (`NV-1` .. `NV-5`)

### 6.1 The open decision these cases are written against

v0.1 asserted `NV_OUTCOME = NV-A` and called it *accepted doctrine*. **That
assertion is withdrawn.** See §6.2. The cases below are therefore written
**policy-relative**: each states what must hold for the policy the operator
ratifies, and names the three candidate policies explicitly.

```text
NV_POLICY = <UNRATIFIED: NV-A | NV-B | NV-C | HOLD>
```

- **NV-A — structural missingness.** A source-less record MAY be
  current-authoritative when it is terminal, structurally valid and
  methodology-current. Any cited refs must additionally be current.
- **NV-B — evidence-required missingness.** No missingness record is
  current-authoritative without current Book 2 evidence. This changes
  *authority at resolve time only*; construction and registration stay exactly
  as accepted.
- **NV-C — state-specific authority.** Different states carry different
  requirements (e.g. structural states `NOT_APPLICABLE` / `NOT_SUPPORTED` versus
  operational/empirical `NOT_AVAILABLE` / `NOT_COLLECTED` /
  `SOURCE_UNAVAILABLE` / `STALE` / `PARTIAL_COVERAGE` / `UNKNOWN`). **NV-C may
  only be ratified against a fully specified per-state policy** — see decision
  packet v0.3.

### 6.2 Defect B — why v0.1's NV-A claim was withdrawn

The v0.1 argument was: *`test_book6_missingness.py:111` constructs and registers
a source-less `NOT_COLLECTED` record and shows `current_value` refuses, therefore
source-less missingness is accepted current-authority doctrine.*

That inference is invalid, for three measured reasons.

```text
1. The cited test NEVER calls resolve_current or is_authoritative_now.
   It asserts construction, registration and value-non-readability ONLY.

2. The only accepted tests that call is_authoritative_now are in
   test_book6_temporal.py, and every one of them uses a VALUE-BEARING
   record (value=7.0). No accepted test asserts current authority over
   ANY non-value-bearing record.

3. resolve_current names ZERO MissingnessStates; the token "missingness"
   does not appear in its body. The early return is gated solely on
   is_value_bearing, which is `missingness_state in VALUE_BEARING_MISSINGNESS`
   -- a VALUE-FORBIDDANCE partition being reused as an AUTHORITY partition.
   That is precisely the defect class under repair, so its output cannot
   be cited as evidence for the policy being chosen.
```

Required invariant, now binding on all GAP-7 artifacts:

```text
DEFECTIVE_BEHAVIOR_IS_NORMATIVE_EVIDENCE     = FALSE
ACCEPTED_CONSTRUCTION_BEHAVIOR
    != ACCEPTED_CURRENT_AUTHORITY_DOCTRINE
```

Corrected classification:

```text
SOURCELESS_MISSINGNESS_CONSTRUCTIBILITY   = ACCEPTED
SOURCELESS_MISSINGNESS_CURRENT_AUTHORITY  = UNRESOLVED
```

### 6.3 The cases

| ID | Setup | Required result |
|---|---|---|
| NV-1 | source-less non-value-bearing record (`source_claim_refs=()`), terminal, structurally valid, methodology current | follows `NV_POLICY`: **NV-A** current; **NV-B** not current; **NV-C** per-state rule |
| NV-2 | cited refs, all **current** | allowed under NV-A (terminal + valid + methodology current + refs current). NV-C per-state rule. NV-B current. |
| NV-3 | cited refs, any **decayed** | **not current under every policy.** No early-return bypass. |
| NV-4 | source-less construction and registration | **remains legal regardless of the authority outcome** — `NV_POLICY` never reaches construction |
| NV-5 | a record that **is** current-authoritative | `current_value` still refuses to fabricate a value — "absence is not zero" |

`NV-3` and `NV-4` are policy-invariant and are the two cases that can be
ratified now. `NV-1`, `NV-2` and `NV-5` are the ones blocked on the operator
decision.

`NV-5` records the separation the review demanded:

```text
CURRENT AUTHORITY  !=  VALUE READABILITY
```

A missingness record may legitimately be the current authoritative statement
about a metric precisely because the metric has no value. That is the intended
semantics of Axiom 6 (`missing != false`) — and it is orthogonal to whether it
*is* authoritative.

---

## 7. Measured baseline for the future implementation round

Baseline accepted suite: **2162 passed** (re-measured 2026-10-03, twice).

| Case | Accepted behaviour today | Required |
|---|---|---|
| CURR-1, CURR-14, CURR-19, CURR-20 | already correct | unchanged |
| CURR-S1, CURR-S2, CURR-23 | already correct | unchanged (now pinned) |
| CURR-S3 | lineage never consulted | terminality enforced |
| CURR-2, CURR-9, CURR-10 | predecessor resolves as current | refused |
| CURR-3, CURR-4, CURR-15 | predecessor current after successor decay | neither current |
| CURR-5 | A, B and C all current | C only |
| CURR-6 | `measurement_history` refuses, `is_authoritative_now` does not | both refuse |
| CURR-11, CURR-12, CURR-13 | predecessor enters normalization / comparison | filtered out |
| CURR-16 | cited authority never checked for non-value-bearing | checked |
| CURR-17 | **cited-but-decayed non-value-bearing reports `True`** | `False` |
| CURR-21 | branching refused only at history-walk | refused at step 2 too |
| CURR-22 | structure enforced at registration | unchanged |
| NV-1, NV-2 | source-less and cited-current resolve `CURRENT` | per `NV_POLICY` — **blocked** |
| NV-3 | **cited-but-decayed still resolves `CURRENT`** | `False` |
| NV-4 | construction and registration legal | unchanged |
| NV-5 | `current_value` refuses "absence is not zero" | unchanged |

### 7.1 Two additional measured defects, recorded so no future round misses them

Both were found this round while verifying Phase 10 and Phase 12, and both are
**independent** of the NV policy choice.

**(a) Methodology is not re-resolved for non-value-bearing records.**
With `book6-methodology@1` invalidated after registration:

```text
methodology_is_current                        -> False
resolve_current(value-bearing record)         -> REFUSED  (methodology re-resolved)
resolve_current(NON-value-bearing record)    -> CURRENT  <-- NOT re-resolved
```

This contradicts accepted doctrine at `book6_methodology.py:19-26`, which states
that every authority-bearing surface must resolve methodology identity *"before
it may authorize anything"* and **explicitly lists**
`MeasurementObservation.methodology_ref + methodology_version` among those
surfaces. `methodology_ref` is `Field(min_length=1)`, required, on every record,
value-bearing or not.

```text
METHODOLOGY_AUTHORITY_APPLIES_TO_NON_VALUE_BEARING = TRUE   (re-verified)
```

**(b) Branching lineage is refused only at history-walk.**
Measured: registering two successors of one predecessor is **accepted**;
`measurement_history` then raises *"multiple successors; supersession must be
linear"*, but `resolve_current` and `is_authoritative_now` do not consult
lineage at all.

```text
MULTIPLE_SUCCESSOR_LINEAGE = FAIL_CLOSED   (required at resolve step 2)
```

### 7.2 Terminality

Measured: a non-value-bearing record can be superseded, and
`measurement_history` returns the full 2-record chain for it.

```text
NON_VALUE_BEARING_CAN_BE_HISTORICAL = TRUE
PREDECESSOR_NEVER_RESURRECTS        = TRUE   (required; not yet enforced)
```

Record supersession is independent of whether a record carries a numeric value.
Terminality is therefore universal across value-bearing and non-value-bearing
records.

---

## 8. Case accounting

```text
CARRIED_UNCHANGED        = 19   (CURR-1..15 less CURR-7, plus CURR-16..23 less CURR-24)
STATUS_CASES_ADDED       =  3   (CURR-S1, CURR-S2, CURR-S3)
NV_CASES_ADDED           =  5   (NV-1..NV-5)
TOTAL                    = 27
IMPLEMENTED              =  0
BLOCKED_ON_OPERATOR_NV   =  3   (NV-1, NV-2, NV-5; NV-3/NV-4 are policy-invariant)
WITHDRAWN                =  2   (CURR-7 superseded by CURR-S1; CURR-24 subsumed)
```

```text
GRANTS_IMPLEMENTATION_AUTHORITY = FALSE
GRANTS_TEST_AUTHORITY          = FALSE
RATIFIED                       = FALSE
```

**Next operator action:** choose `NV_POLICY` (decision packet v0.3 options A/B/C/D).
Until then GAP-7 cannot be ratified, and GAP-6 stays `HOLD_PENDING_GAP7`.
