# SENSOR-B5-P3-R6-F4-F5-INDEPENDENT-CLOSURE-R1

**SECOND-AGENT TECHNICAL AUDIT — NOT ORGANIZATIONALLY INDEPENDENT**

Targeted reattack carrier for F4 and F5, additive to
`p3_r6_reattack_r2` (audit head `6a1a7a5d6`) and to
`p3_consolidated_independent_audit_r1` (audit head `6c4874b43`).
Both are preserved unchanged. No earlier bundle was edited, regenerated or
replaced, and no production source was modified.

---

## 1. Disposition

```
P3_F4_F5_CLOSURE_BLOCKED_AWAITING_REPAIR_PUBLICATION
```

The mission's `P3_F4_F5_TARGETED_REPAIR_ACCEPTED` is **not issuable**, and
`P3_FINAL_INDEPENDENT_TECHNICAL_ACCEPTANCE` is **not issuable**, because the
repair this mission is built to accept does not exist yet in any published ref.

This is not a planning-only return. Because the counterexample must be shown to
be *live* before a pass at a later SHA can be attributed to a repair, the whole
targeted matrix was executed and pinned at the current head:

| Measurement | Result |
| --- | --- |
| Candidate pinned | `21fd7e473a534c38b237729f9474c46bb94267ee` |
| Targeted probe | **32 cases — 23 passed, 9 failed, 0 errored** |
| Shipped consumer suite at the same head | **161 passed, 0 failed** |
| Detector calibration (both controls injected) | **32 passed, 0 failed** |
| Mutation controls | 2 DETECTED, 0 NOT_DETECTED, 1 NOT_APPLICABLE |
| F4 | **still open — 5 accepting forms measured** |
| F5 | **still open — both format strings relay detail** |
| Replay-binding boundary | unchanged; still not enforced |

### Why no repair could be reattacked

`git ls-remote --heads origin` and `git log --all` place the newest commit at
`21fd7e473` (the R7 decision package, documentation only). The newest commit
touching `consumer/policy.py` is `d81cceb28` — the R6 repair, not a new one.
The R7 package at `05_REPAIR_PROTOCOL.md` records *"This mission made no repair,
because no independently confirmed defect was received"*, which predates the
publication of the F4/F5 findings at `6a1a7a5d6`. There is no branch, tag or
stash carrying an F4/F5 repair.

---

## 2. Exact candidate pin

| Fact | Value |
| --- | --- |
| Candidate SHA | `21fd7e473a534c38b237729f9474c46bb94267ee` |
| Branch | `agent/crypto-sensor-fabric-p3-production-master-r1` |
| `consumer/policy.py` sha256 | `fe3853da5ceec16edd31be7f372ade8ad530d22fe4d963259d0c0a26c6fbe843` |
| `consumer/models.py` sha256 | `c3cc51b14831bc2a6b2a27e05a44ba70fc4fa328b6888ba6129bb881c733c7da` |
| `time/replay_gate.py` sha256 | `79aa9bd9a98fc76d4666689f71ea4d47a69d75f3a05036b7ccc278a269a3a936` |
| Approval manifest `artifacts` | `{}` |
| Tracked Python under `quant-lab` | 696 |
| Tracked-file working tree | clean (only the three untracked canonical bundles, unchanged) |

The candidate is byte-identical to `868dd3fc9` in every file this mission
touches; `868dd3fc9 → eb3644f03 → 21fd7e473` are evidence/documentation
commits. The Rung 6 canonical reconciliation therefore still describes these
bytes — but it is *not* re-cited here as new evidence.

---

## 3. F4 — independent reattack (still open)

**The counterexample.** A selection whose *chosen* revision is admissible but
which also carries a revision that became known after the cutoff certifies the
consumption:

```python
RevisionSelection(mode=AS_KNOWN_THEN, selected=(
    rev("rev-audit", known_from=2026-02-01),          # the record's own revision
    rev("rev-LATER", known_from=2026-09-01),          # known AFTER the 2026-06-01 cutoff
), excluded=(), pit_safe=True)
```

→ `ACCEPT_FIELD_BINDING`, `replay_status=ELIGIBLE`, `pit_status=ADMISSIBLE`.

**Cause, read at the pinned blob.** `_bind_replay` builds
`selected = {item.source_revision_id: item for item in revision.selected}` and
then orders **only** `chosen = selected[record_revision]`
(`policy.py:595-604`). Every other entry in the selection — and every duplicate
that the dict collapsed — is never compared with the cutoff.

**The module's own stated law is broader than its enforcement.** The
`_bind_replay` docstring at `policy.py:524-525` states:

> *"2. no selected revision may have become known after the cutoff — that is a
> selection computed for a later replay"*

The code checks `chosen` only. The documented invariant and the executed
invariant disagree, which is why the defect survived the R6 repair: the repair
implemented the law for the one entry it was looking at.

### Measured matrix

| Case | Selection | Expected | Measured at `21fd7e473` |
| --- | --- | --- | --- |
| `f4_00` control | chosen only, early | ACCEPT | ACCEPT ✓ |
| `f4_01` control | all selected known by cutoff | ACCEPT | ACCEPT ✓ |
| `f4_02` control | `known_from == cutoff` | ACCEPT | ACCEPT ✓ |
| `f4_03` control | same instant via `+02:00` | ACCEPT | ACCEPT ✓ |
| `f4_04` control | future revision correctly *excluded* | ACCEPT | ACCEPT ✓ |
| `f4_05` | **future revision last** (the R6 counterexample) | REFUSE `PIT_INADMISSIBLE` | **ACCEPT** ✗ |
| `f4_06` | future revision first | REFUSE `PIT_INADMISSIBLE` | **ACCEPT** ✗ |
| `f4_07` | duplicate id, future entry masked by a later early entry | REFUSE | **ACCEPT** ✗ |
| `f4_08[future_last]` | contradictory duplicate | REFUSE | REFUSE ✓ (by tuple order) |
| `f4_08[future_first]` | contradictory duplicate, other order | REFUSE | **ACCEPT** ✗ |
| `f4_09` | evaluated revision both selected and excluded | REFUSE | **ACCEPT** ✗ |
| `f4_10` | malformed instant on another entry | REFUSE | REFUSE ✓ **by the schema guard, not the temporal control** |
| `f4_11` | same content, two orders | same decision | **differs** ✗ |
| `f4_12` | chosen revision after cutoff | REFUSE by name | REFUSE ✓ — the temporal branch *does* execute |
| `f4_13` | wrong revision | REFUSE `REPLAY_BLOCKED` | REFUSE ✓ — why/when stay distinct |

Positive controls hold, so the accept path is reachable and the matrix is not
refusing everything. `f4_12` proves the temporal branch executes for the chosen
entry, which is what makes the *narrowing* — not a missing control — the defect.
No downstream missing-integration refusal is credited as a temporal refusal
anywhere in this matrix; `_refused_temporally` asserts
`PIT_INADMISSIBLE` + `NOT_BOUND` + the law's own detail text.

`f4_10` is recorded as refused and **not credited**: the refusal is
`VERIFICATION_FAILED` with `"does not satisfy its own schema"`, i.e. the H04
serialization guard, which runs before rebinding and therefore covers the
malformed-instant axis without the temporal control ever seeing it.

**Order decides the answer** (`f4_11`): the identical pair of records certifies
in one tuple order and refuses in the other. Adjudication does not depend on
order; a dict collapse does.

---

## 4. F5 — independent reattack (still open, and wider than reported at R6)

The audit's own sentinel (`ZT-PROBE-4b71-NOT-A-CREDENTIAL`, non-credential
shaped, asserted by `f5_07`) reaches `refusal_detail` on **both** format
strings, not one:

| Site | Line | Form | Measured |
| --- | --- | --- | --- |
| PIT branch | `policy.py:426` | `f"{exc.refusal.value}: {exc.detail}"` | **leaks** (`f5_03`) |
| verification branch | `policy.py:438` | `f"{exc.refusal.value}: {exc.detail}"` | **leaks** (`f5_01`, `f5_02`) |
| ordinary exception | `_withheld` | class name only | withheld ✓ (`f5_04`) |

- `f5_01` — sentinel present in `refusal_detail` after a typed
  `RecordVerificationError(CUSTODY_UNVERIFIED, …)`.
- `f5_02` — sentinel reachable through `refusal_detail`, `model_dump_json()` and
  `repr()`; no other public field carries it.
- `f5_03` — **new at this mission**: the `_PIT_REFUSALS` branch leaks too, so a
  fix scoped to the `VERIFICATION_FAILED` branch would leave a second channel.
- Classification remains correct throughout (`f5_00`, `f5_03`): the typed
  refusal still lands on `VERIFICATION_FAILED` / `PIT_INADMISSIBLE`, so
  withholding the detail is a diagnostic change only.
- `KeyboardInterrupt` and `SystemExit` still propagate (`f5_05`, `f5_06`).
- `RecordVerificationRefusal` carries no `PIT_INADMISSIBLE` member (`f5_08`), so
  the PIT classification is the consumer's own and the leak is the consumer's.

---

## 5. Unresolved replay-binding boundary — unchanged

**Question:** is the unsupported complete replay-identity binding now
*explicitly enforced* at the consumption boundary?

**Answer: no.** The boundary binds what the frozen schema carries and nothing
more.

| Axis | Status | Evidence |
| --- | --- | --- |
| revision identity | BOUND | `b_00` → `REPLAY_BLOCKED` |
| temporal adjudication | BOUND **for the chosen entry only** | `f4_12` vs `f4_05`–`f4_09` |
| market-availability instant | BOUND | `b_01` |
| evidence-reference digest | BOUND at the contract | `b_02`, `b_03` |
| provider identity of the evidence | NOT expressible, NOT enforced | `b_04` → ACCEPT |
| record id / kind / artifact identity | NOT expressible | `b_05` |
| the named limitation as a boundary | **documentation only** | `b_06` |
| authoritative acceptance | needs the test-only composition control | `b_07` |

`b_06` is operational, not textual: no `If` tests `UNRESOLVED_REPLAY_BINDING`
(AST), and rebinding the constant to `()` at runtime changes no outcome. A
documentation constant is not a security control.

`b_07` closes the "the manifest is empty so it is enforced" reasoning: the
shipped root plus an authorizing source answers `INTEGRATION_REQUIRED`; the
probe root plus the same source answers `ACCEPT`. The empty manifest proves the
absence of a custody-authority record. It proves nothing about the replay
binding, and this package does not use it as proof.

Correct intermediate revision binding, correct temporal adjudication of the
chosen entry, unsupported full replay provenance and authoritative acceptance
are four different facts and are kept separate above. No replay/custody schema
was invented.

---

## 6. Targeted mutation verification

An unrepaired candidate cannot be mutated to *remove* a control it does not
have, so each mutation is measured in both directions: the removal state is the
published tree (the detector must fail) and the injected state is a throwaway
copy (the detector must pass). A mutation counts as DETECTED only when both
halves are observed **and** the mutated module was imported from the copy —
`imported_from_copy: true` in every calibration run.

| Mutation | Detector | Published tree | Control injected | Status |
| --- | --- | --- | --- | --- |
| `M1_CHOSEN_ONLY_CUTOFF` | `f4_05` | FAIL | PASS (`CAL_A`) | **DETECTED** |
| `M2_RAW_TYPED_REFUSAL_DETAIL` | `f5_01` | FAIL | PASS (`CAL_B`) | **DETECTED** |
| `M3_UNRESOLVED_BINDING_GUARD_REMOVAL` | — | no guard exists | nothing to remove | **NOT_APPLICABLE** |

Calibration, all four runs importing from the copy:

| Run | Injected | Result |
| --- | --- | --- |
| `BASELINE` | none | 9 failed, 23 passed |
| `CAL_A_F4_SELECTION_ORDERING` | whole-selection ordering | 3 failed, 29 passed (only F5 remains) |
| `CAL_B_F5_TYPED_DETAIL_WITHHELD` | detail withheld on both strings | 6 failed, 26 passed (only F4 remains) |
| `CAL_AB_BOTH_CONTROLS` | both | **32 passed, 0 failed** |

`CAL_AB` is the completeness proof: the probe is satisfiable, so a green run at
a future SHA is reachable and a red one is not an artefact of the harness.
`CAL_A` and `CAL_B` are disjoint (6 vs 3), so each detector set is attributable
to its own control. No syntax or dependency error is counted as a detection;
`M3` is recorded as NOT_APPLICABLE rather than as a pass.

The injected text is a calibration fixture used only to prove detector
sensitivity and specificity. It is not a proposed patch, it was never applied
to the audited tree, and it is labelled as such in `run_closure_calibration.py.txt`.

---

## 7. Shipped-suite blindness

At the same pinned head, with every F4 and F5 defect present:

```
quant-lab/tests/.../test_b5_p3_consumer_{policy,rebinding,security,contracts,custody}.py
161 passed, 0 failed
```

The producer's own detector set does not distinguish a consumer that orders the
whole selection from one that orders only the chosen entry, and does not
distinguish a withheld typed detail from a relayed one. That is the mechanism
by which both defects survived the R6 repair and the R7 decision package.

---

## 8. What is required to close

Smallest reproducible counterexample, for reproduction-then-repair under the
producer's own protocol (`Rung 7 — Repair readiness`):

1. `f4_05` — selection `[rev-audit@2026-02-01, rev-LATER@2026-09-01]` at cutoff
   `2026-06-01T12:00Z` must refuse `PIT_INADMISSIBLE`; it currently accepts.
   Ordering **every** `selected[*].known_from` (and deciding explicitly what a
   duplicate id in one selection means) closes `f4_05`–`f4_09` and `f4_11`.
2. `f5_01`/`f5_03` — a typed `RecordVerificationError` detail must not reach
   `refusal_detail` on either branch; both `policy.py:426` and `policy.py:438`
   format it today.

Acceptance at the repaired SHA re-runs this package's probe unchanged:

```
AUDIT_QUANT_LAB=<wt>/quant-lab \
AUDIT_PRIOR_FIXTURES=<...>/p3_consolidated_independent_audit_r1/test_second_agent_p01_p06.py.txt \
PYTHONPATH=<wt>/quant-lab/src python -m pytest test_f4f5_closure.py -q
```

A green re-entry is `32 passed` **and** the five positive controls still
ACCEPT. `CAL_AB` in this package is the proof that this is achievable.

---

## 9. Not done, and why

| Mission item | State | Reason |
| --- | --- | --- |
| §1 F4 reattack at the repaired candidate | **blocked** | no repair SHA published; matrix executed and pinned at `21fd7e473` instead |
| §2 F5 reattack at the repaired candidate | **blocked** | same |
| §5 `P3_F4_F5_TARGETED_REPAIR_ACCEPTED` | **not issued** | condition unmet |
| §6 final canonical reconciliation | **not attempted** | Agent 1 owns the execution; no new bundle exists. The R6 reconciliation stands as history and is not restated as a new result |
| §7 `P3_FINAL_INDEPENDENT_TECHNICAL_ACCEPTANCE` | **not issued** | F4/F5 unclosed and no final bundle |

The previous independent reconciliation (4,952 collected, 4,941 passed, 0
failed, 0 errored, 11 explained skips, digest `f2fc9090…`, anchor verified) is
preserved and is **not** re-asserted as evidence for any repaired candidate.
Per the producer's own protocol, a change to production or canonical-test
source invalidates the freeze: any repaired SHA needs its own bundle, and its
count is not expected to remain 4,952.

## 10. Hard stops observed

No production source modification. No merge. No provider approval. No
replay/custody schema invention. No manifest activation. No trust promotion. No
gate or Bloc 6 advancement. No self-ratification. No canonical bundle deleted,
regenerated or overwritten. No failure classified away as blanket
"infrastructure". No earlier audit head rewritten: `6c4874b43` (r1) and
`6a1a7a5d6` (r2) are untouched, and this carrier is a new branch.

---

## 11. Files

| File | Content |
| --- | --- |
| `test_f4f5_closure.py.txt` | the 32-case targeted probe (executed as `test_f4f5_closure.py`) |
| `run_closure_calibration.py.txt` | the four-run detector calibration |
| `closure_probe_results.json` | per-case outcomes and failure messages at `21fd7e473` |
| `calibration_results.json` | raw calibration runs, including imported module paths |
| `mutation_results.json` | M1/M2/M3 with both-direction evidence |
| `boundary_measurements.json` | §5 axis table and disposition |
| `shipped_suite_results.json` | the 161-pass blindness measurement |
| `carrier_pin.json` | SHA, per-file hashes, blob ids, tree cleanliness, environment |

All JSON in this package parses. The `.py.txt` copies are byte-identical to the
files that were executed (asserted during composition).
