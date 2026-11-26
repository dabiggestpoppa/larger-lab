# SENSOR-B5-P3-R6-FINAL-INDEPENDENT-CLOSEOUT-R3

**SECOND-AGENT TECHNICAL AUDIT — NOT ORGANIZATIONALLY INDEPENDENT**

Additive audit-r4 carrier. It is appended to
`p3_f4_f5_closure_r1` (audit head `d6b3f9f83`), `p3_r6_reattack_r2`
(`6a1a7a5d6`) and `p3_consolidated_independent_audit_r1` (`6c4874b43`). None of
those was edited, regenerated or replaced. **No production source was modified
by this audit.** Every file in this package is written by this auditor.

---

## 1. Disposition

```
P3_F4_F5_TARGETED_REPAIR_ACCEPTED
```

```
P3_FINAL_INDEPENDENT_TECHNICAL_ACCEPTANCE
  scopes accepted here:  F4 closure, F5 closure, executable replay-binding
                         guard, targeted mutation accounting
  NOT issued here:       P3_FINAL_CANONICAL_RECONCILIATION for 66200f3cb
                         — see §9. The claim is not made because the evidence
                         does not yet exist, not because the run is doubted.
```

| Measured scope | Pre-repair `21fd7e473` | Repair `66200f3cb` |
| --- | --- | --- |
| Independent targeted matrix | **32 cases — 23 passed, 9 failed** | **41 cases — 41 passed, 0 failed, 0 errored** |
| F4 counterexamples accepted | 5 accepting forms | **0** — every form refuses at the temporal or contradiction stage |
| F5 typed-detail leakage | both format strings relay `detail`, plus `str(exc)` | **0 leaks** across five exceptions, four branches |
| Executable replay-binding guard | absent (documentation only) | **present, runtime-effective, ships off** |
| Targeted mutations | 2 DETECTED / 1 NOT_APPLICABLE | **3 DETECTED / 0 survived / 0 NOT_APPLICABLE** |
| Producer's own consumer suite | 161 passed | 177 passed (+16 tracked regressions) |

The pre-repair column is the point of this mission's ordering. A pass at a
later SHA is attributable to a repair only if the counterexample was first
shown to be **live** at a pinned earlier SHA. It was, at `21fd7e473`
(`baseline_pre_repair_reference.json`), by this auditor, with this matrix.

---

## 2. Exact candidate pin

| Fact | Value |
| --- | --- |
| Candidate SHA | `66200f3cb18ee5cea1483d986e64502f388eeb77` |
| Tree | `e7f058bb2e315365b19c3933c16745c895e7bb5b` |
| Branch | `agent/crypto-sensor-fabric-p3-production-master-r1` |
| Parent (single commit) | `21fd7e473a534c38b237729f9474c46bb94267ee` |
| Subject | `B5-P3-R6: close selected-revision cutoff and typed-refusal leakage` |
| Committer date | `2026-11-25T19:14:04-05:00` |
| `consumer/policy.py` sha256 | `cc5d1bb9dc6cd8c901106153cfb81aa638a60bceb3527758b7bf340445f4e24a` |
| …at the pre-repair pin | `ee1b07ee22899f0b050b275e6cdbedd15c21296370791f0f4f7760c3e1c62102` |
| `consumer/models.py` sha256 | `c3cc51b14831bc2a6b2a27e05a44ba70fc4fa328b6888ba6129bb881c733c7da` (**unchanged**) |
| `time/replay_gate.py` sha256 | `79aa9bd9a98fc76d4666689f71ea4d47a69d75f3a05036b7ccc278a269a3a936` (**unchanged**) |
| Approval manifest sha256 | `3d707c59fbf1fe96f28b2080811a0da189d2ad5c2859c97faa01a367c7042654` |
| Approval manifest `artifacts` | `{}` (**unchanged — no manifest activation**) |

The repair is one commit touching **one** production file and three test files:

```
quant-lab/src/crypto_sensor_fabric/normalization/consumer/policy.py        M
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_policy.py    M
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_rebinding.py M
quant-lab/tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_security.py  M
```

`models.py` and `replay_gate.py` are byte-identical to the pre-repair pin, so
the repair is confined to the consumer's adjudication logic. No schema was
invented, no manifest was written, no trust was promoted.

### Untested-change check (§7)

`quant-lab/src/**` and `quant-lab/tests/**` are **clean**. Seven BLOC_04
research evidence JSONs are byte-dirty, and each is **EOL-only**:
`git diff --ignore-cr-at-eol --numstat` reports zero hunks for all seven, so
their JSON content is unchanged. They are exactly the paths the canonical
runner lists in its own `restoration` set. Four other restoration paths
(I15 TOCTOU, manifest-scan, resource-bounds, secret-safety) are byte-clean.
Recorded in `carrier_pin.json → workspace`.

---

## 3. What the repair actually changed (read at the blob)

**F4.** `_bind_replay` previously built
`selected = {item.source_revision_id: item for item in revision.selected}` and
ordered only `chosen = selected[record_revision]` against the cutoff. The dict
kept the **last** entry per id, so tuple order decided the answer and a
duplicate could hide a late entry. The repair sweeps the **original selected
sequence** before any id-keyed mapping:

- every selected identity must be a non-empty string;
- a repeated identity refuses as a contradiction (`REPLAY_BLOCKED`);
- a revision both selected and excluded refuses as a contradiction;
- every selected `known_from` must be a real, offset-aware instant, else
  `REPLAY_BLOCKED` (never a fabricated PIT answer);
- every selected instant must be `<= cutoff`; equality stays admissible;
- the **excluded** half is deliberately not ordered, because an exclusion is
  retained precisely as evidence that the revision was not knowable here.

**F5.** Both typed branches formatted `f"{exc.refusal.value}: {exc.detail}"`
into the public verdict, and the semantic branch formatted `str(exc)` — which is
the same string. The repair introduces `_approved_refusal` / `_refusal_token`:
a verdict now carries an **approved refusal token** from the closed vocabulary
or the fixed `UNSPECIFIED_REFUSAL`, never authored text. The replay gate's
`UnassessableReplayEvidence` message is withheld for the same reason, and the
approved-evidence re-derivation branch reports a token or the exception class.

**F1 residual — the executable guard.** `REPLAY_RECORD_BINDING_ESTABLISHED` is
`False`. A fully satisfied evaluation terminates in `INTEGRATION_REQUIRED`
naming `REPLAY_EVIDENCE_RECORD_BINDING_V1`, because the frozen I05
`ReplayEvidence` schema cannot carry record id, provider, record kind or
artifact identity. This is the operator-reconciled decision recorded in §1 of
the mission, and it is now **executable rather than documentary**.

### The historical finding is preserved, not retired

At audit-r3 this auditor proved `UNRESOLVED_REPLAY_BINDING` was a string that
no branch read (`b_06`, plus an AST walk). That finding **still holds** and the
AST assertion is retained as `b_10`. The enforced control is a *different*
symbol. Crediting the repair required measuring the new boolean, not quietly
dropping the old observation. See `intentional_control_changes.json`.

---

## 4. F4 — targeted reattack (closed)

41-case matrix, repaired head, `41 passed / 0 failed / 0 errored / 0 skipped`
(`r4_matrix.xml`, `repaired_probe_results.json`, `observed_outcomes.json`).

The controls are anchored to the **intermediate** control, not to a terminal
verdict. `INTEGRATION_REQUIRED` alone is ambiguous — a broken harness produces
it too — so each positive control asserts `replay_status == "ELIGIBLE"`, the
absence of any temporal refusal detail, and the presence of the binding-contract
name; then the **labelled test-only override** reaches
`ACCEPT_FIELD_BINDING`. Both prongs are required.

| §2 requirement | Scenario | Production default | Test-only override |
| --- | --- | --- | --- |
| chosen revision alone accepts | single early revision | `INTEGRATION_REQUIRED`, `ELIGIBLE` | **`ACCEPT_FIELD_BINDING`** |
| valid multi-revision passes intermediate | two revisions, both early | `INTEGRATION_REQUIRED`, `ELIGIBLE` | **`ACCEPT_FIELD_BINDING`** |
| equality at cutoff admissible | `known_from == cutoff` | `INTEGRATION_REQUIRED`, `ELIGIBLE` | **`ACCEPT_FIELD_BINDING`** |
| equivalent offsets identical | `+02:00` form of the same instant | `INTEGRATION_REQUIRED`, `ELIGIBLE` | **`ACCEPT_FIELD_BINDING`** |
| excluded future does not invalidate | withheld revision at `2026-09-01` | `INTEGRATION_REQUIRED`, `ELIGIBLE` | **`ACCEPT_FIELD_BINDING`** |
| **future-last refuses** | own revision early, `rev-LATER` last | **`REFUSE` / `PIT_INADMISSIBLE`** | `REFUSE` (override cannot cross it) |
| **future-first refuses** | `rev-LATER` first | **`REFUSE` / `PIT_INADMISSIBLE`** | `REFUSE` |
| **duplicate cannot conceal future** | same id, future then early | **`REFUSE` / `REPLAY_BLOCKED`** "more than once" | `REFUSE` |
| **contradictory duplicate refuses** | same id, both orders | **`REFUSE` / `REPLAY_BLOCKED`** | `REFUSE` |
| **selected/excluded contradiction refuses** | id in both halves | **`REFUSE` / `REPLAY_BLOCKED`** "BOTH selected and excluded" | `REFUSE` |
| malformed knowledge instant refuses | `known_from="not-an-instant"` | **`REFUSE` / `VERIFICATION_FAILED`** (schema guard) | `REFUSE` |
| reordering cannot manufacture admissibility | valid selection, both orders | identical decision and status | — |
| order alone cannot decide | identical content, two orders | identical decision **and** identical refusal reason | — |

**Intermediate control results, stated explicitly.** For the two temporal
counterexamples the refusal is `PIT_INADMISSIBLE` with `replay_status=NOT_BOUND`
and the detail *"the replay selection was computed for a LATER cutoff: selected
revision(s) [...] became known after this request's knowledge cutoff"* — the
temporal law's own text, not a downstream integration refusal. `f4_12` proves
the branch executes for the chosen revision; `f4_13` proves a wrong-row refusal
stays `REPLAY_BLOCKED` and is not confused with the temporal law.

**One deliberate non-credit.** The malformed-instant case refuses through the
**H04 schema boundary** (`VERIFICATION_FAILED`, *"does not satisfy its own
schema"*), not through the temporal sweep. The assertion records which path ran
and does **not** credit the temporal control for it. The new `REPLAY_BLOCKED`
"not a timestamp" arm exists for entries the schema lets through; it is
reachable but is not exercised by this fixture, and that is stated rather than
implied.

---

## 5. F5 — targeted reattack (closed)

Sentinel `ZT-PROBE-4b71-NOT-A-CREDENTIAL` — deliberately **not**
credential-shaped, and asserted so (`f5_07`: no `key|token|secret|passw|bearer|sk-`).
It appears in: public verdict fields, `model_dump_json()`, `repr()`, and the
whole serialized verdict text (`_text`). Absence is required in all of them.

| Channel | Case | Result |
| --- | --- | --- |
| PIT typed refusal (format string 1) | `f5_03` | `PIT_INADMISSIBLE`, token present, **sentinel absent** |
| General typed refusal (format string 2) | `f5_01`, `f5_02` | `VERIFICATION_FAILED`, **sentinel absent from every public field** |
| Semantic authority `str(exc)` | `f5_09` | `INTEGRATION_REQUIRED`, `NO_APPROVAL` relayed, **detail withheld** |
| Semantic authority violation | `f5_10` | `VERIFICATION_FAILED`, `DIGEST_MISMATCH` relayed, **detail withheld** |
| Unapproved claimed code | `f5_11` | fixed `UNSPECIFIED_REFUSAL`, **claimed text withheld** |
| Approved-evidence re-derivation | `f5_12` | `VERIFICATION_FAILED`, token relayed, **detail withheld** |
| Ordinary exception | `f5_04` | `VERIFIER_CRASH`, class only, **sentinel absent** |
| `KeyboardInterrupt` | `f5_05` | **propagates** |
| `SystemExit` | `f5_06` | **propagates** |

**Classification preserved:** `f5_00` keeps `VERIFICATION_FAILED` and the
approved code; `f5_08` keeps the consumer's `PIT_INADMISSIBLE` distinct from the
verification vocabulary, which has no such member.

`f5_12` is a **channel this auditor found while targeting the third**: the
approved-evidence re-derivation wraps its own authority load and reports
`<CODE>` there. It is withheld at the repair. It is listed because a measured
fourth branch is evidence, not because the repair was credited with it.

---

## 6. Executable replay-binding guard (§4)

Production default — `REPLAY_RECORD_BINDING_ESTABLISHED is False`, asserted at
the top of every production-default evaluation so a flipped module cannot
silently invalidate the table.

| §4 requirement | Measured |
| --- | --- |
| Fully satisfied composition terminates in `INTEGRATION_REQUIRED` | **yes** — `custody_status=VERIFIED`, `replay_status=ELIGIBLE`, `pit_status=ADMISSIBLE`, decision `INTEGRATION_REQUIRED`, naming `REPLAY_EVIDENCE_RECORD_BINDING_V1` |
| Provider substitution cannot authorize | **`INTEGRATION_REQUIRED`** (was `ACCEPT` before the repair) |
| Record-kind substitution cannot authorize | **`INTEGRATION_REQUIRED`** (liquidation record against trade evidence) |
| Artifact substitution cannot authorize | **`REFUSE` / `VERIFICATION_FAILED`** |
| Nonempty test manifest cannot bypass | **`INTEGRATION_REQUIRED`** — all other claims satisfied, guard still holds |
| Shipped empty manifest remains non-authorizing | **`INTEGRATION_REQUIRED`** — `artifacts == {}` re-read, not assumed |
| Schema cannot express the missing axes | `provider`, `record_id`, `record_kind`, `artifact_id` all absent from `ReplayEvidence` |
| Guard is executable, not documentary | AST finds a branch reading it; flipping it to `True` turns a satisfied evaluation into `ACCEPT_FIELD_BINDING` |

**The labelled test-only override.** Reaching the downstream accepting
machinery requires
`monkeypatch.setattr(policy_module, "REPLAY_RECORD_BINDING_ESTABLISHED", True)`.
Every use is labelled `test_only_override` in `observed_outcomes.json`. It is
**not production authority**: the binding it implies does not exist, the schema
still cannot carry it, and the override was proved unable to cross a temporal
refusal, a duplicate contradiction, or a diagnostic refusal. Neither missing
integration schema was invented.

---

## 7. Targeted mutation accounting (§5)

Each mutation is applied to a **disposable copy** of the repaired package; the
probe runs with `PYTHONPATH` at that copy, and a provenance case
(`test_zz_the_imported_policy_module_is_the_expected_tree`) asserts the imported
`policy.py` came from it. An uncompacted copy is run first as a control, so a
red result cannot be attributed to the copying mechanism.

| Mutation | Restored defect | Intended detectors | Status |
| --- | --- | --- | --- |
| `M1_CHOSEN_ONLY_CUTOFF` | orders only the record's own revision | `f4_05`, `f4_06` | **DETECTED** — 2/2 failed, 0 additional, 0 errors |
| `M2_RAW_TYPED_REFUSAL_DETAIL` | formats `exc.detail` into the verdict on both typed branches | `f5_01`, `f5_02`, `f5_03` | **DETECTED** — 3/3 failed, 0 additional, 0 errors |
| `M3_BYPASS_UNRESOLVED_REPLAY_BINDING_GUARD` | `if False:` in place of the guard | 8 named cases | **DETECTED** — 8/8 failed, 0 errors |

| Control | Result |
| --- | --- |
| `CAL_COPY_BASELINE_UNMUTATED` | **41 passed**, provenance confirmed |

`M3` produced two **additional** failures, both correct consequences and not
spurious: `b_05` (record-kind substitution) and `f4_14` (reordering) assert
non-acceptance and therefore fail once the guard is bypassed. All 41 cases were
collected in every run and the collection count never varied.

`M1` and `M2` are now **true removals** of a control that exists. At audit-r3
the same mutations had to be run in reverse (control injection into a throwaway
copy) because an unrepaired tree cannot be mutated to remove a control it does
not have, and `M3_UNRESOLVED_BINDING_GUARD_REMOVAL` was recorded
`NOT_APPLICABLE` because no guard existed. That limitation is now discharged.

---

## 8. Blindness measurement

The producer's own consumer suite is **green at the defective and at the
repaired SHA**: 161 passed before, 177 passed after. A green producer suite
therefore carries no verdict about F4 or F5 — which is why the independently
constructed probe does. The +16 is the repair's own tracked regressions; it is
**not** counted as independent evidence of correctness.

At audit-r3 the same 161-case suite was green while the probe measured 9
failures. That gap is the measured blindness.

---

## 9. Final canonical reconciliation (§7) — **NOT ISSUED**

**The claim is not made, because the evidence does not exist yet.**

At the time this package was written, the only *complete* canonical bundle
present is `canonical_runs/p3-r6-final`, and it was executed at
`868dd3fc91b5a38d02742bd3705da0c1d78b66c3` — an **ancestor** of the repair:

| Check | Value |
| --- | --- |
| Bundle recorded commit | `868dd3fc91b5a38d02742bd3705da0c1d78b66c3` |
| Repair candidate | `66200f3cb18ee5cea1483d986e64502f388eeb77` |
| Bundle ran | `2026-11-25T20:14:52Z → 20:40:01Z` |
| Repair committed | `2026-11-25T19:14:04-05:00` = `2026-11-26T00:14:04Z` (≈3h34m **after** the run finished) |
| Repair controls present in the executed tree | `F4 sweep: no · F5 token helper: no · F1 guard: no · F1 terminal branch: no` |
| `policy.py` sha256 in executed tree | `ee1b07ee22899f0b050b275e6cdbedd15c21296370791f0f4f7760c3e1c62102` |

That bundle nevertheless reconciles **cleanly to its own anchor**, and this is
recorded so the reader can see it was checked rather than dismissed:

| §7 item | Result |
| --- | --- |
| Collection count / recomputed digest | 4,952 / recomputed `f2fc9090…` — **digest matches**, 0 duplicates, 0 malformed |
| Partition membership | intended set equals collection set |
| Raw executed node IDs | node set **equals** the collection set; 0 duplicate executions; 0 unimplemented partitions |
| JUnit accounting | 4,952 tests / 0 failures / 0 errors / 11 skipped |
| Recomputed counts | 4,941 passed / 11 skipped — equals the recorded counts |
| Explained skips | 11, each with a stated environment reason (live-network smoke gated by `SENSOR_NETWORK_SMOKE`; POSIX mode bits on Windows; no `os.pathconf`; real PostgreSQL opt-in via `SENSOR_POSTGRES_TEST_DSN`; …) |
| Hardened verifier with external anchor | `canonical_runner.py verify <evidence.json> --require-anchor --expect-count 4952 --expect-digest f2fc9090…` → **exit 0, `ANCHORED_COMPLETE`, `GREEN`** |
| Restoration | attempted, **verified**, zero failed |
| Tree clean after | true · interrupted: false |

**Therefore:** this is the *pre-repair* R6 run already reconciled at audit-r2,
with an identical anchor. It says nothing about `66200f3cb`, and the previous
**4,952-node count is not inherited** as evidence for the repair.

A successor run is **in flight** against the repair at the time of writing, and
the count is **not** expected to stay 4,952:

| In-flight observation | Value |
| --- | --- |
| Bundle | `canonical_runs/p3-r6-final-r3` |
| External collection anchor | **4,968** = 4,952 + **16** (the repair's new tracked tests) |
| Collection duplicates / malformed | 0 / 0 · collection exit 0 |
| Partition intended count | 4,968 (set equality not yet asserted — `evidence.json` absent) |
| Progress at publication | 3,859 of 4,968 unique nodes, **0 failed**, 6 skipped |
| `evidence.json` | **absent** — the runner writes it last |

Because `evidence.json` does not exist, the recomputed digest, JUnit accounting,
node-set equality, skip explanations, restoration and exit codes for this run
**cannot be verified yet**, and none of them is asserted here. Per §8 the
targeted acceptance is published without falsely claiming canonical
reconciliation. This is not a blocker on Agent 1's execution and does not repeat
it: no duplicate canonical run was launched by this audit.

**To close this section**, the values needed are exactly the §7 list above,
recomputed from `p3-r6-final-r3` with
`reconcile_r4.py` (included) and the hardened verifier's `--require-anchor`,
`--expect-count 4968`, `--expect-digest <recomputed>`.

---

## 10. Remaining integration limitations

Stated as unresolved dependencies, not as security controls.

1. **`REPLAY_EVIDENCE_RECORD_BINDING_V1` is unminted.** The frozen I05
   `ReplayEvidence` carries no record id, provider, record kind or artifact
   identity (`b_09`). Complete record-level binding is therefore
   **unestablishable**, not merely unestablished. The guard names the contract
   and refuses; it does not substitute for it.
2. **The shipped approval manifest approves no artifact** (`artifacts == {}`,
   sha `3d707c59…`, unchanged). The production path is `INTEGRATION_REQUIRED`
   for that reason independently of item 1, so the two absences are separate
   and neither can stand in for the other.
3. **No custody-source authority record exists.** An authorizing source is
   reachable only as a labelled composition double, never through
   `ConsumerRequest`.
4. **`ACCEPT_FIELD_BINDING` is unreachable in production by design.** The
   downstream accepting machinery exists and is exercised only under the
   labelled test-only guard override.
5. **Canonical reconciliation for `66200f3cb` is outstanding** (§9).
6. **The temporal sweep's malformed-instant arm is reachable but not exercised
   by this fixture**; the tested path for that case is the H04 schema boundary.

---

## 11. Recommendation — D1 bounded production implementation acceptance

Accept the D1 bounded production implementation scope, bounded to exactly what
was measured here:

- **F4 — whole-selection temporal adjudication.** Every selected revision, not
  only the record's own, is ordered against the cutoff; duplicates and
  selected/excluded contradictions refuse as contradictions; excluded revisions
  are not ordered. Accepted.
- **F5 — diagnostic withholding.** No authored exception text reaches a public
  verdict through any of the four measured branches, while classification and
  `KeyboardInterrupt`/`SystemExit` propagation are preserved. Accepted.
- **The unresolved replay-binding guard.** Accepted **as a refusal**, i.e. as
  the correct fail-closed terminal behaviour for an unexpressible claim. It is
  not accepted as, and must not be recorded as, replay-binding enforcement.
- **Blanket acceptance is explicitly withheld** on authoritative
  `ACCEPT_FIELD_BINDING`, on any claim of complete replay/record binding, and on
  canonical regression coverage of `66200f3cb` until §9 closes.

No trust promotion, no gate advancement, no provider approval, no custody-source
activation, no manifest modification, no merge. This is a technical
recommendation for the operator, not a ratification by the auditor.

---

## 12. What this package does not do

- It does not modify production source, tests, schema or manifest.
- It does not repeat the broad historical audit or restart production design; it
  executes the targeted matrix only.
- It does not launch a duplicate canonical execution.
- It does not ratify itself, and it is not organizationally independent — it is
  a second-agent technical audit.
- It does not merge, promote trust, advance a gate, approve a provider, activate
  a custody source, or invent either missing integration schema.

---

## 13. Reproduction

```bash
# Targeted matrix at the repair candidate (41 cases expected)
AUDIT_QUANT_LAB=<candidate>/quant-lab \
AUDIT_PRIOR_FIXTURES=<audit-r1>/test_second_agent_p01_p06.py.txt \
PYTHONPATH=<candidate>/quant-lab/src \
python -m pytest test_f4f5_closure_r4.py -q

# Producer's own consumer suite (177 expected; carries no F4/F5 verdict)
PYTHONPATH=src python -m pytest \
  tests/crypto_sensor_fabric/normalization/test_b5_p3_consumer_{policy,rebinding,security,contracts,custody}.py -q

# Mutations: disposable copies, provenance-asserted, control first
AUDIT_QUANT_LAB=<candidate>/quant-lab \
AUDIT_PRIOR_FIXTURES=<audit-r1>/test_second_agent_p01_p06.py.txt \
python run_mutations_r4.py

# Observed-outcome table (production default vs labelled override)
python measure_r4.py

# Canonical reconciliation once evidence.json exists
AUDIT_QUANT_LAB=<candidate>/quant-lab \
AUDIT_CANONICAL_RUNS=<candidate>/quant-lab/research/.../canonical_runs \
python reconcile_r4.py
```

---

## 14. Package manifest

| File | Contents |
| --- | --- |
| `carrier_pin.json` | candidate SHA/tree/branch/parent, file hashes before and after, manifest state, workspace classification |
| `baseline_pre_repair_reference.json` | the 32-case pre-repair counterexample-of-record (carried, not re-executed) |
| `repaired_probe_results.json` | 41-case matrix at `66200f3cb`, per-case status |
| `observed_outcomes.json` | measured decision / refusal reason / replay status, production default vs labelled override |
| `intentional_control_changes.json` | the eight §1-driven expectation changes, each with why it is not a regression |
| `mutation_results.json` | M1/M2/M3 with intended-detector accounting and provenance |
| `canonical_evidence.json` | §9 — the pre-repair bundle reconciliation and why it is not evidence for the repair |
| `shipped_suite_results.json` | producer's suite at the repaired head |
| `test_f4f5_closure_r4.py.txt` | the independent matrix (non-collected research artifact) |
| `run_mutations_r4.py.txt` | mutation runner |
| `measure_r4.py.txt` | observed-outcome harness |
| `reconcile_r4.py.txt` | canonical reconciler, hardened verifier with external anchor |
| `r4_matrix.xml`, `mut_*.xml`, `shipped_consumer_suite.xml` | raw JUnit |
