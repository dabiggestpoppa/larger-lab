# CSIA — Book 6 Measurement Supersession / Currentness Audit v0.1

**Status:** `AUDIT_FINDING` — reproduces and characterises a defect; resolves none.
**Date:** 2026-10-03
**Decision id:** none. This artifact records **no** operator decision.
**Grants implementation authority:** `FALSE`
**Ratifies:** nothing. Amends: nothing. Reverses: nothing.
**Authorized scope:** `BOOK 6 MEASUREMENT SUPERSESSION / CURRENTNESS AUDIT` ONLY.

---

## 0. Headline

```text
GAP_7_REPRODUCED          = TRUE
KERNEL_WIDE_DEFECT        = TRUE
NO_RESURRECTION_BROKEN    = TRUE
STATUS_SEMANTICS_INCOHERENT = TRUE
SECOND_DEFECT_FOUND       = TRUE   (non-value-bearing authority bypass)
ACCEPTED_TEST_BASELINE    = 2162 passed, 0 failed
```

The accepted kernel resolves `A` and `B` as *both* current after `B` has validly
superseded `A`, while `measurement_history("A")` correctly returns `('A', 'B')`.
The registry therefore **knows** the lineage and `resolve_current` does not
consult it. The defect reaches six non-comparison call sites, including the
kernel's own sanctioned value read.

Nothing here was inferred from comments. Every claim below was executed against
the accepted worktree at `5f94c3f40c` and is reproducible from the scripts named
in §12.

---

## 1. Scope and anchors

```text
accepted worktree : C:/Users/wifik/Desktop/larger-lab-csia-book6-build
accepted HEAD     : 5f94c3f40cea4441470c57671f51454da7377361
accepted anchor   : 3919fb8052e216e94034a753fb258d338c5fa0dc (ancestor: YES)
commits past anchor: 1  (the acceptance commit)
impl dirty files  : 0
planning HEAD     : 06cf85090c564ac1ffaf4c9b831964e6c05b8094
```

No accepted source was modified. No test file was created in the repository. All
reproducers were written to a scratch directory outside the checkout and import
only accepted public contracts.

---

## 2. Runtime reproducer

Built from `book6_support.build_engine`, `.definition`, `.windowed_observation`,
`.register_definition`, `.register_measurement` — accepted factories only.

```python
A = windowed_observation("A", "metric:g", value=10.0,
      missingness=MissingnessState.OBSERVED, claim_refs=(CLAIM_A,),
      window_class=WindowClass.DAILY, status=ObservationStatus.OBSERVED)

B = windowed_observation("B", "metric:g", value=12.0,
      missingness=MissingnessState.OBSERVED, claim_refs=(CLAIM_B,),
      window_class=WindowClass.DAILY, supersedes="A",
      restatement_reason=RestatementReason.LATE_BLOCKS,
      status=ObservationStatus.OBSERVED)
```

Both methodologies current; both cited Book 2 claims current.

### 2.1 Actual outputs

```text
registered_refs:                          ('A', 'B')
measurement_history("A"):                 ('A', 'B')
registered_measurement("A").status:        ObservationStatus.OBSERVED
registered_measurement("B").status:        ObservationStatus.OBSERVED
resolve_current("A"):                     'A'          <-- predecessor resolves
resolve_current("B"):                     'B'
is_authoritative_now("A"):                True         <-- DEFECT
is_authoritative_now("B"):                True
GAP_7_REPRODUCED:                          TRUE
```

`measurement_history` sees the supersession. `resolve_current` does not.

---

## 3. Phase 2 — accepted supersession semantics, by executable behaviour

`resolve_current` is `book6_registry.py:195-211`. In order, it:

1. fetches the record (`:202`);
2. **returns it immediately if `not is_value_bearing`** (`:203`);
3. resolves methodology identity (`:204`);
4. resolves cited Book 2 claims with `require_current=True` (`:206-209`).

It never reads `observation.status`, and never consults the successor set.

| Question | Answer | Evidence |
|---|---|---|
| 1. Who marks a predecessor `SUPERSEDED`? | **Nobody.** No code path mutates an observation. | `grep -c "def supersede" book6_registry.py` → `0`; records are frozen (`book6_records.py:106`) |
| 2. Can immutable registration mutate the predecessor? | **No.** | `ConfigDict(extra="forbid", frozen=True)` at `book6_records.py:106` |
| 3. Does status describe this record's own currentness, or that it supersedes another? | **Neither, coherently.** See §4. | validator at `book6_records.py:203` |
| 4. Can B be `OBSERVED` while superseding A? | **Yes**, and that is the defect. | §2.1 |
| 5. Can A remain `OBSERVED` forever after B exists? | **Yes.** Nothing can ever change it. | §2.1, §5 |
| 6. Does any runtime helper compute terminality? | **No.** Only `measurement_history` walks the lineage, and only `resolve_current` does not use it. | `book6_registry.py:170-190` vs `:195-211` |

### 3.1 The asymmetry that makes this a defect, not a design choice

The **methodology** registry implements exactly this doctrine:

```text
book6_methodology.py:225   def supersede_methodology(...)
book6_methodology.py:242   def invalidate_methodology(...)
book6_methodology.py:285   def superseded_versions(...)
book6_methodology.py:327   "a superseded methodology version authorizes nothing"
```

The **observation** registry has **none** of these. `book6_registry.py` contains
zero `supersede_observation` / `def supersede` definitions. The kernel adopted
"supersession stops authorizing while the record stays queryable" for
methodologies and did not adopt it for observations.

---

## 4. Phase 11 — status semantics are incoherent with the module doctrine

Three artifacts disagree about what `status = SUPERSEDED` means.

| Source | Says |
|---|---|
| `book6_records.py:101-102` (class docstring) | "the prior value is retained with `status = SUPERSEDED`" |
| `book6_grammar.py:265-268` (`ObservationStatus`) | "the prior observation is retained with `SUPERSEDED`" |
| `book6_records.py:203-206` (**the validator**) | "a SUPERSEDED observation must name the observation **it superseded**" |
| `test_book6_core.py:236` (test name) | `test_superseded_observation_must_name_its_**successor**` |
| `test_book6_adversarial.py:477` (test name) | `test_a_superseded_observation_must_name_what_it_**superseded**` |

The field `supersedes_measurement_id` points **backwards**: a record names its
**predecessor**. So the validator's rule reads as "a record marked SUPERSEDED
must name the record it replaced" — i.e. `SUPERSEDED` is being used to mean
*this record supersedes another*, which is the opposite of the doctrine that
says the *prior* observation is retained as SUPERSEDED.

Executed confirmation:

```text
SUPERSEDED, no supersedes_measurement_id   -> ValidationError (REJECTED)
SUPERSEDED, supersedes_measurement_id="X"  -> ACCEPTED  (status=SUPERSEDED,
                                               supersedes_measurement_id="X")
```

The consequence is decisive: **no valid record can express "A was superseded by
B".** A has no successor link of its own to declare; its own
`supersedes_measurement_id` would have to point at A's predecessor, which is
either absent (rejected) or wrong. `ObservationStatus.SUPERSEDED` is therefore
effectively unusable as a statement about having been superseded.

Two accepted tests assert the *same* validator under *contradictory names*, and
both pass, because the validator message matches either regex. The disagreement
is invisible to the suite.

This is recorded as part of GAP-7, not silently reinterpreted.

---

## 5. Phase 5 / 8 / 9 — no-resurrection is broken in every decay direction

### 5.1 Successor loses Book 2 authority (`A <- B`, decay B's claim)

```text
before decay: A_now = True   B_now = True
after  decay: A_now = True   B_now = False      <-- A must be historical
NO_RESURRECTION_BROKEN = True
```

### 5.2 Successor loses methodology authority

Methodology loss was produced by pointing B at an unregistered methodology
version (`book6-methodology@2`), which `require_methodology` refuses.

```text
before: A_now = True   B_now = True
after:  A_now = True   B_now = False
A still current after B lost methodology = True
```

The same asymmetry applies to *any* future methodology invalidation route: `A`'s
authority is computed from `A`'s own cited claim and methodology, both of which
are untouched by `B`'s decay. There is no mechanism by which `A` could learn
that `B` exists.

### 5.3 Longer lineage `A <- B <- C`

```text
history(A) = ('A', 'B', 'C')
A_now = True   B_now = True   C_now = True     <-- all three current
after C decays:
A_now = True   B_now = True   C_now = False
STRUCTURAL_TERMINAL_CORRECT = True    (history correctly ends at C)
NO_RESURRECTION_BROKEN     = True
```

Structural terminality is computed correctly by `measurement_history`. Nothing
consumes it.

### 5.4 Branching lineage `A <- B`, `A <- C`

```text
measurement_history("A") -> Book6RegistryError:
    measurement A has multiple successors; supersession must be linear
MULTIPLE_SUCCESSOR_FAIL_CLOSED = TRUE          <-- PRESERVE THIS
is_authoritative_now(A) = True
is_authoritative_now(B) = True
is_authoritative_now(C) = True
```

`measurement_history` fails closed and correctly refuses any lexical,
registration-order, or `observed_at` resolution. That behaviour is **correct and
must be preserved**. But the fail-closed signal does not propagate: the three
authority-bearing queries return `True` for every branch, so a caller that never
calls `measurement_history` learns nothing.

### 5.5 Proposed invariant, stated but NOT ratified

```text
SUPERSEDED_PREDECESSOR_NEVER_RESURRECTS = TRUE   (proposed)

CURRENT_AUTHORITATIVE_MEASUREMENT = NONE
```

once a successor exists but is itself no longer authoritative.

---

## 6. Phase 3 — the six currentness axes, measured

| Axis | Implemented in `resolve_current`? | Evidence |
|---|---|---|
| `BOOK2_AUTHORITY_CURRENT` | **YES** (value-bearing only) | `book6_registry.py:206-209` |
| `METHODOLOGY_CURRENT` | **YES** (value-bearing only) | `book6_registry.py:204` |
| `RECORD_STATUS_ELIGIBLE` | **NO** | `observation.status` is never read |
| `TERMINAL_IN_SUPERSESSION_LINEAGE` | **NO** | no successor lookup exists |
| `STRUCTURALLY_VALID` | **NOT AT USE** | `validate_against_definition` runs only at registration (`book6_registry.py:139`) |
| `MEASUREMENT_CURRENT_AUTHORITY` | **NO** — it is a conjunction and only two conjuncts exist | §3 |

Two of the six axes are missing entirely, one is present only at registration
time, and the conjunction the docstring claims to perform is not performed.

### 6.1 A second, independent defect in the same function

`book6_registry.py:203` returns the record immediately when it is not
value-bearing, **before** any authority check:

```text
resolve_current('NV') with a FULLY DECAYED cited claim -> RETURNED 'NV'
is_value_bearing = False
is_authoritative_now('NV')                            = True
```

Control, same decayed claim, value-bearing record:

```text
is_authoritative_now('VB')                            = False
```

So a `NOT_AVAILABLE` observation whose Book 2 authority has decayed is reported
authoritative, while an `OBSERVED` one with identical decay is not. The two
record kinds have different authority semantics, and the docstring — "Resolve a
measurement's CURRENT authority against live Book 2 state" — is false for every
non-value-bearing record. This is recorded separately inside GAP-7 because it
has a different repair surface (§10, option A/B).

---

## 7. Phase 4 — global call-site audit

Every accepted call to `resolve_current` / `is_authoritative_now`, found by AST
walk over all 62 modules:

| # | Site | Enclosing function | Class | Can consume a predecessor? |
|---|---|---|---|---|
| 1 | `book6_core.py:139` | `current_value` | value read | **YES — executed, returns 10.0** |
| 2 | `book6_core.py:148` | `current_unit` | identity/unit read | **YES** |
| 3 | `book6_core.py:165` | `compute_ratio` | ratio arithmetic | **YES** |
| 4 | `book6_core.py:243` | `normalize` | **normalization** | **YES** |
| 5 | `book6_core.py:337` | `_required_input_value` | **base/divisor lookup** | **YES** |
| 6 | `book6_core.py:485` | `emit_rule_gated_state` | **state emission** | **YES** |
| 7 | `book6_sensitivity.py:132` | `compare_methodology_variants` | comparison | **YES — executed** |
| 8 | `book6_sensitivity.py:193` | `compare_sources` | comparison | **YES** |

(`book6_registry.py:222` is the internal call inside `is_authoritative_now`
itself and is excluded.)

**Six of eight are not comparison.** `current_value` is described in its own
docstring as "the only sanctioned way to read a value out of the kernel"
(`book6_core.py:135`), so the defect sits on the kernel's primary read path.

### 7.1 Executed kernel impact

```text
current_value("A")   [superseded predecessor] -> 10.0     <-- stale value returned
current_unit("A")                            -> 'native-unit'
is_authoritative_now("A")                    -> True
compare_methodology_variants over A and B    -> ('A', 'B')
```

The comparison path places the superseded predecessor **side by side with its own
successor** as two methodology variants. A sensitivity finding computed over
that pair compares a live value against a historical one and reports a
methodology difference that is really a restatement.

### 7.2 Classification

```text
KERNEL_WIDE_DEFECT = TRUE
```

Sites 1–6 are outside comparison, so a comparison-local filter (7B) would leave
them reading stale predecessors. Normalization, base/divisor lookup, state
emission, ratio arithmetic and the sanctioned value read all inherit the defect.

Evidence strength is stated honestly: sites 1, 2, 7 and 8 were **executed**; sites
3, 4, 5 and 6 are proven by **call-site identity** — the same unguarded
`resolve_current` call followed by a `.value` / `.unit` read, with no successor
check between them — not separately executed, because building a valid
`NormalizedMeasurement` product or a ratified `StateRule` was out of the
authorized scope. The two arguments are the same two-line argument; only the
fixture differs.

---

## 8. Phase 6 / 7 — proposed GAP-7 and the status/terminality matrix

**Proposed, NOT ratified:**

```text
GAP_7 = MEASUREMENT SUPERSESSION CURRENTNESS
7A-KERNEL = TERMINAL_SUPERSESSION_CURRENTNESS

CURRENT_AUTHORITATIVE_MEASUREMENT(record) requires ALL of:
  1. record.status == OBSERVED
  2. record is TERMINAL: no registered observation names it in
     supersedes_measurement_id
  3. methodology is current
  4. Book 2 authority is current
  5. record still validates against its MetricDefinition

CURRENT = OBSERVED
      AND TERMINAL
      AND METHODOLOGY_CURRENT
      AND BOOK2_AUTHORITY_CURRENT
      AND STRUCTURALLY_VALID
```

### 8.1 Status / terminality matrix

| `status` | terminal? | Accepted `is_authoritative_now` | Proposed 7A | Agreement |
|---|---|---|---|---|
| `OBSERVED` | yes | True | current | agrees |
| `OBSERVED` | **no** (successor exists) | **True** | not current | **DEFECT** |
| `SUPERSEDED` | yes | *unreachable* — no valid record can express this (§4) | not current | gap |
| `SUPERSEDED` | no | *unreachable* | not current | gap |

Neither signal is sufficient alone, and the accepted kernel has neither:

```text
STATUS_ALONE_ESTABLISHES_CURRENTNESS    = FALSE
TERMINALITY_ALONE_ESTABLISHES_CURRENTNESS = FALSE
```

Both are required, and both are required *together with* methodology, Book 2
authority, and structural validity.

---

## 9. Phase 12 — kernel-wide vs comparison-local

| | 7A-KERNEL | 7B-COMPARISON-LOCAL |
|---|---|---|
| Repair surface | `Book6MeasurementRegistry.resolve_current` | comparison selector only |
| Sites fixed | 8 of 8 | 2 of 8 |
| Sites left reading stale predecessors | none | **6**, incl. `current_value` |
| `single-meaning-of-current` doctrine | one `resolve_current` means one thing | two notions of current coexist |
| Matches the methodology precedent | yes (`book6_methodology.py:327`) | no |

`resolve_current`'s own docstring — "Resolve a measurement's **CURRENT
authority**" — is the kernel-wide contract, and it is already shared by
normalization, base/divisor lookup and state emission. A comparison-local filter
would leave the same method returning `True` for `A` in one path and `False` in
another, which is the ambiguity the single-meaning-of-current doctrine exists to
prevent.

```text
KERNEL_WIDE_DEFECT = TRUE
=> 7A-KERNEL is the preferred shape.
```

This is a **recommendation**, not a decision. See the decision packet.

### 9.1 Phase 11 repair-surface options

| Option | What it changes | Consequence |
|---|---|---|
| **A — status semantic correction** | reconcile the validator with the doctrine so a record can express "I was superseded" | makes `ObservationStatus.SUPERSEDED` usable; larger surface; touches two accepted tests whose names disagree |
| **B — terminality-only currentness, status preserved** | currentness derives from the successor set alone; `status` stays descriptive | smaller, self-contained; leaves the incoherent validator in place |
| **C — both** | A then B | largest surface, no incoherence left |

B alone is sufficient to stop stale consumption, because terminality is
structurally decidable and status is not currently decidable. A is required only
if `ObservationStatus.SUPERSEDED` is ever to carry meaning. C is the only choice
that leaves no contradiction behind. The operator chooses; this audit does not.

---

## 10. Phase 14 — currentness test family (PLANNED ONLY, NOT IMPLEMENTED)

No test code was written to the repository. These are specifications for a
future authorized round.

| ID | Scenario | Required result |
|---|---|---|
| CURR-1 | A only, OBSERVED, terminal, live | current |
| CURR-2 | A <- B, both OBSERVED and live | A not current, B current |
| CURR-3 | A <- B, B Book 2 authority decays | neither current |
| CURR-4 | A <- B, B methodology decays | neither current |
| CURR-5 | A <- B <- C | C only current |
| CURR-6 | A has B and C as direct successors | structural failure (fail closed) |
| CURR-7 | terminal `SUPERSEDED` record | not current |
| CURR-8 | `OBSERVED` status alone | insufficient for currentness |
| CURR-9 | `resolve_current(A predecessor)` | reject |
| CURR-10 | `is_authoritative_now(A predecessor)` | `False` |
| CURR-11 | normalization cannot consume a superseded predecessor | refuse |
| CURR-12 | comparison filters predecessor before ordering | predecessor absent from ordering input |
| CURR-13 | lexical tie-break never sees a historical predecessor | absent from candidate set |
| CURR-14 | historical predecessor remains queryable | `registered_measurement("A")` still returns A |
| CURR-15 | successor authority loss never resurrects predecessor | A stays non-current |

CURR-6 and CURR-15 are the two that currently fail hardest: CURR-6 because
`measurement_history` fails closed but `is_authoritative_now` does not, and
CURR-15 in all three decay directions (§5).

---

## 11. Accepted Book 6 hardening impact

```text
accepted suite : 2162 passed, 0 failed  (measured at 5f94c3f40c)
```

**No accepted test catches GAP-7.** The suite is fully green while the defect is
reproducible. This is stated as a fact about coverage, not as a criticism of the
suite: the existing tests were written to pin Book 2 decay, methodology
invalidation, claim refusal and self-supersession, and none of them asserts
predecessor non-currentness. `test_book6_hardening_r1.py:206` and
`test_book6_hardening_r2.py:436` prove the *methodology* supersession analogue is
covered; the observation analogue has no equivalent.

Hardening implication, stated without authorization: any future repair of
`resolve_current` will change behaviour at all 8 call sites simultaneously,
because they share the one method. That is an argument for 7A, and also a reason
to expect the repair round to be broad.

---

## 12. Reproduction

All scripts were written outside the repository and import accepted public
contracts only:

```text
/tmp/gap7/repro_phase1.py    -> §2.1, §5.1, §5.3
/tmp/gap7/phases_5_11.py     -> §4, §5.1-5.4
/tmp/gap7/phase4_impact.py   -> §7.1
/tmp/gap7/extra.py           -> §6.1
```

Run shape:

```python
import sys
sys.path.insert(0, "C:/Users/wifik/Desktop/larger-lab-csia-book6-build/quant-lab/src")
from crypto_systems_intelligence_atlas.book6_support import (
    build_engine, definition, register_definition,
    register_measurement, windowed_observation)
```

Baseline command used for §11:

```bash
python -m pytest quant-lab/tests/crypto_systems_intelligence_atlas -q
```

---

## 13. Choir plan preservation

```text
CSIA_BOOK_6_CHOIR_FORMAL_PROOF_PILOT_PLAN_v0.1.md   present, unedited
commit 2b02fcf4325449c9344cbfc4b386af9772c500e3    ancestor of planning HEAD: YES
CHOIR_PLAN_PRESERVED = TRUE
```

Zero semantic overlap: the plan contains **no** occurrence of `supersedes`,
`supersedes_measurement_id`, `resolve_current`, `is_authoritative_now`,
`currentness`, `ObservationStatus`, or `terminal`. It concerns a bounded formal
proof pilot and does not depend on measurement supersession semantics. No proof
work was performed and none is proposed here. GAP-7 may later become one of its
explicit premises; that is a future decision, not this audit's.
