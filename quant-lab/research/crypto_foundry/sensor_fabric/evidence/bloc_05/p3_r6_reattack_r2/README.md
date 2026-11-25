# SENSOR-B5-P3-R6-FINAL-REATTACK-R2 — INDEPENDENT RECONCILIATION

**SECOND-AGENT TECHNICAL AUDIT — NOT ORGANIZATIONALLY INDEPENDENT**

| | |
|---|---|
| Mission | `SENSOR-B5-P3-R6-FINAL-REATTACK-R2` |
| Audited candidate | **`868dd3fc91b5a38d02742bd3705da0c1d78b66c3`** |
| Repair ladder | `5ee268b1d` → `d81cceb28aa79870f6702bed053bfb6d8d80f2c1` → `868dd3fc9…` → `eb3644f03528744c85811b3ff1d80789fe69fc54` |
| Origin head of `…-master-r1` | `eb3644f03` |
| Audit branch | `agent/crypto-sensor-fabric-p3-production-master-audit-r2` (previous head `6c4874b43` untouched) |
| Disposition | **`P3_FINAL_REPAIR_REQUIRED`** — F4, F5 |

Supersedes `p3_consolidated_independent_audit_r1` for the same lineage. F1's
revision, cutoff-for-the-chosen-revision and availability halves are **repaired
and verified**; F2's unexpected-exception half is repaired; **F3 is repaired**.
Two new open items remain (F4, F5). The canonical R6 collection **does**
reconcile: `ANCHORED_COMPLETE / GREEN`.

---

## 1. Lineage

All four commits resolve locally and on origin, each an ancestor of the next.
`868dd3fc9 → eb3644f03` adds **seven files, all under
`evidence/bloc_05/p3_rung6_final_r1/`** (five `.md`, `README.md`,
`rung6_final_r1.json`) — no source, test, config or manifest file. The
documentation commit therefore cannot change the production or test universe.

## 2. What was executed

| # | Artifact | Result |
|---|---|---|
| 1 | `test_second_agent_r6_repair.py.txt` (33 cases) | **31 passed, 2 failed** (F4, F5) |
| 2 | `run_r6_mutations.py.txt` (8 mutations, disposable `src/`) | **6 DETECTED, 2 SURVIVED, 0 INVALID** |
| 3 | `reconcile_r6_canonical.py.txt` + hardened verifier `--require-anchor` | anchored green, exit 0 |
| 4 | `reconcile_g17.py.txt` | 45/45 pins verified, frozen surfaces unchanged |
| 5 | `probe_redundancy.py.txt` | names the control behind each survivor |

Probes are non-collected `.py.txt` research artifacts; no tracked `.py` was
added and no canonical test count was inflated. The full 4,952-node collection
was **not** re-executed (mission boundary); the published bundle was reconciled.

## 3. F1 — replay binding: what is repaired, and what is not

| Required case | Observed | Status |
|---|---|---|
| 1. Matching revision + admissible availability | `ACCEPT`, `replay_status=ELIGIBLE` | control green |
| 2. Foreign revision only | `REFUSE / REPLAY_BLOCKED`, `NOT_BOUND` | **repaired** |
| 3. Future availability only | `REFUSE / PIT_INADMISSIBLE` | **repaired** |
| 3b. Chosen revision known after cutoff | `REFUSE / PIT_INADMISSIBLE` | **repaired** |
| 4. Missing revision identity | `REFUSE` (revalidation or binding) | **repaired** |
| 5. Multiple selected, one foreign (after cutoff) | **`ACCEPT_FIELD_BINDING`** | **F4 — open** |
| 6. Malformed temporal evidence | `REFUSE` | **repaired** |
| 7. Same revision id, another provider | `ACCEPT` | unbound (documented) |
| 8. Same revision id, another kind/artifact | axis not expressible | unbound (documented) |

**F4 — the cutoff law orders only the chosen revision — MEDIUM-LOW, OPEN.**
`_bind_replay` inspects `chosen = selected[record_revision]` and compares
`chosen.known_from > cutoff`; every other selected revision is ignored. A
selection containing `rev-LATER` with `known_from=2026-09-01` beside the
admissible `rev-audit` therefore reaches acceptance at a `2026-06-01` cutoff:

```
decision=ACCEPT_FIELD_BINDING  replay_status=ELIGIBLE  pit_status=ADMISSIBLE
```

The selection was computed for a later replay, so the evidence does not
describe what was known at this cutoff. Bounded repair with no schema change:
order **every** `selected[*].known_from` against the cutoff (one loop, same
refusal already used for the chosen entry).

**The provider / record-kind / artifact axes are not a control.** They are named
in `UNRESOLVED_REPLAY_BINDING`, which is referenced only by its own definition
and a docstring — the probe parses the AST and asserts it never appears in an
`if`, `assert` or conditional expression. Evidence whose
`source_evidence_refs` name another provider's document is **accepted**, and
`ReplayEvidence.model_fields` carries none of `provider`, `record_id`,
`record_kind`, `artifact_id`. Recording this as a limitation is correct; it is
not evidence of binding, and acceptance below does not assert it.

## 4. F2 — diagnostic confidentiality: partial

| Injection | Result |
|---|---|
| Ordinary verifier exception | withheld — `VERIFIER_CRASH`, class only |
| Replay-gate exception | withheld |
| Custody read exception | withheld (reads measured) |
| Authority-derivation exception | withheld |
| Loader failure (`KeyError`) | withheld |
| `KeyboardInterrupt` / `SystemExit` | **propagate** |
| **Typed verifier refusal `detail`** | **relayed verbatim — F5** |

**F5 — typed refusal details are public verdict text — LOW, OPEN.**
`CUSTODY_UNVERIFIED: ZT-PROBE-4b71-NOT-A-CREDENTIAL in typed detail` appears in
`refusal_detail`, because that branch formats
`f"{exc.refusal.value}: {exc.detail}"`. `_withheld` guards only the
unexpected-exception path. This branch fires in **normal operation** (every
typed refusal), so it is the more likely leak of the two, even though the text
originates in trusted code. Repair: bound the typed branch to the refusal token,
as the custody-authority handler already does, or scrub `detail` at construction.

## 5. F3 — fail-closed boundary: repaired

The original attack (`load_trusted_authority` raising `KeyError` while
rebinding) now returns `REFUSE / VERIFICATION_FAILED` with a class-only detail.
Also verified: a `model_construct` request holding junk refuses; a request whose
`model_dump` raises refuses; a non-`ConsumerRequest` argument is still a
`TypeError` (programmer error, by design); `KeyboardInterrupt`/`SystemExit`
propagate. The outer handler is load-bearing: narrowing it to one exception type
makes F3's `KeyError` escape again (mutation M6, DETECTED).

## 6. H03 / H05

**H03 — strengthened seam.** Positive control: a test root plus a source that
binds `identity_sha256` to the exact identity reaches `ACCEPT`. Then: the
**shipped manifest plus an authorizing source returns `INTEGRATION_REQUIRED`**
and no `AUTHORIZED` text; a `model_construct` derivation without an identity
digest refuses; a derivation for another identity refuses; a raising source
refuses without relaying its message. The production manifest's
`artifacts` is `{}` and its sha256 is the pin `3d707c59…`.

**H05 — evidence consistency, measured.** Each approved reference is read twice
around verification (`REF=2`, other approved reference `=1`); flipped bytes
between reads refuse (`EVIDENCE_BYTES_MISMATCH`); a foreign reference is read and
refused; omitting the caller's list still reads the whole approved set; two
contradictory claims refuse at the contract. No transactional-storage claim is
made or implied by these measurements.

## 7. Governance G17

| Check | Result |
|---|---|
| Pins in republished generated artifacts | **45 checked, 45 verified, 0 mismatched** (I06 replay-safety 12, I09 semantic 13, I05 time 20) |
| Shipped manifest | byte-identical to the R5 base; sha256 `3d707c59…` |
| `consumer/models.py`, `time/replay_gate.py` | unchanged since R5 — the replay schema is still frozen |
| Republished artifacts | four **generated** files (`BLOC_05_I06_SCOPE_AUDIT.json`, `bloc_05_replay_safety_validation.json`, `bloc_05_semantic_validation.json`, `bloc_05_time_validation.json`), each carrying its producer command; no hand-written artifact rewritten |
| Scope audits | one exact path added to I05 and I10 each (`test_b5_i06_replay_safety.py`), with G17 comments; the historical prefix-granted entries are untouched |
| Tracked Python at candidate | **1,111** — the R1 measurement's +9 delta is unchanged |
| `INTEGRATION_REQUIRED` | enum and decision path unchanged; still what the shipped root returns |

The G15/G16 findings from R1 stand: they are not invalidated by G17.

## 8. Mutation controls

| ID | Control removed | Result | Detector |
|---|---|---|---|
| M1 | revision identity binding | DETECTED | `f1_01` |
| M2 | chosen-revision cutoff order | DETECTED | `f1_03` |
| M3 | availability-vs-cutoff order | DETECTED | `f1_02` |
| M4 | class-only withholding (`str(exc)` restored) | DETECTED | `f2_01` |
| M5 | empty-manifest artifact guard | **SURVIVED** | `h03_01` |
| M6 | total fail-closed handler (narrowed) | DETECTED | `f3_01` |
| M7 | replay gate result honoured | DETECTED | `f1_10` |
| M8 | caller-claim digest comparison | **SURVIVED** | `h05_01` |

**Redundancy demonstrated, not asserted.** With M5 applied, the verdict is still
`INTEGRATION_REQUIRED` with detail `no integration to evaluate: NO_APPROVAL` —
the **verifier** refuses before the policy guard is consulted. With M8 applied,
the verdict is `REFUSE / EVIDENCE_BYTES_MISMATCH` — `evidence reference
'AUDIT_DOC_REF_PRIMARY' does not hash to the blob the approval names` — the
**rebinding** comparator against the approved digest still refuses. Neither
survivor reaches a forbidden outcome, and the surviving mutation is not a
vulnerability claim.

## 9. Canonical evidence reconciliation

Bundles inspected in place under
`evidence/bloc_05/canonical_runs/` (untracked), read-only:

| Check | `p3-r6-final` |
|---|---|
| Recorded commit | `868dd3fc9…` — the candidate, not the documentation commit |
| Collected / unique | **4,952 / 4,952**; 0 duplicates, 0 malformed, 0 collection errors; exit 0 |
| Collection digest | recomputed from sorted node ids: **`f2fc9090…d1931`** == recorded == anchor |
| Partition | `partition_0` intended 4,952 nodes, **set-equal** to the collection, 227 files |
| Result stream | 4,952 node ids, **set-equal** to the collection; 0 duplicate executions; 0 unimplemented partitions |
| Counts | recorded and recomputed both **4,941 passed, 0 failed, 0 errored, 11 skipped** |
| JUnit | tests 4,952, failures 0, errors 0, skipped 11 |
| Verifier | `verify --require-anchor --expect-count 4952 --expect-digest f2fc…` → **exit 0**, `anchored: true`, external anchor checked |
| Restoration / tree | restoration verified; tree clean after; run not interrupted |

**The 11 skips are explained, all environmental/platform:** live network smoke
opt-in (`SENSOR_NETWORK_SMOKE`), real PostgreSQL DSN absent (×2), POSIX mode bits
(×1), `os.pathconf` absent (×1), symlink privilege unavailable / Windows cannot
create symlinks (×4), case-insensitive filesystem (×1), POSIX permission and
symlink semantics (×2). None is a suppressed failure.

**Failed attempts, reviewed separately.** Attempt 1 (workers=4, `d81cceb28`)
reported 3,313 passed / **42 failed** / 2 errored / 9 skipped with stream
accounting errors and a missing partition; attempt 2 (workers=1, 900 s) reported
3,833 / **4 failed** / 1 errored, a partition timeout and 1,107 missing nodes.
Both are `INCOMPLETE_INFRA`, and — measured, not assumed — **every node that
failed in either attempt passes in the final run**, so the final green is not a
silent retry over a real defect. The failed attempts are not counted as evidence.

## 10. Limitations

* F4 and F5 are recorded as failing assertions in the probe, not as prose.
* The accept path requires the X01/X03 composition (a source that binds the
  identity digest) because the shipped root approves no artifact; every case
  that needs it is stated as such.
* Provider / record-kind / artifact replay binding does not exist and cannot
  exist without a schema amendment, which this mission forbids inventing.
* The host is Windows; the 11 platform skips are properties of the collection
  host, not of the code.
* This audit did not re-execute the canonical collection and does not certify
  the runtime behaviour of any node beyond the reconciled bundle.

## 11. Disposition

**`P3_FINAL_REPAIR_REQUIRED`.** The F1 revision/availability repair and the F3
boundary repair are verified by execution, the H03/H05 seams hold, governance
G17 is truthful, and the canonical bundle reconciles to `ANCHORED_COMPLETE /
GREEN` on the candidate SHA. Two bounded repairs remain: **F4** (order every
selected revision against the cutoff) and **F5** (stop relaying typed refusal
details). Both are small and neither needs a schema change.

Re-entry: re-run `f1_05`, `f2_02` and mutations M2/M4 against the repair SHA;
a green result must show a refusal for the mixed selection with the matching
control still accepting.

## 12. Hard stops

No production source modification, no merge, no provider approval, no replay or
custody schema invention, no manifest activation, no trust promotion, no
program-gate advancement, no self-ratification. The previous audit head
`6c4874b43` and the canonical bundles were preserved unchanged.
