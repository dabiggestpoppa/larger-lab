# SENSOR-B4-I07R1G — RUNTIME CHECKPOINT-PROOF SCHEMA + REPLAY-PARITY MICROSEAL — EVIDENCE

**Checkpoint:** SENSOR-B4-I07R1G (Runtime Checkpoint-Proof Schema + Replay-Parity Seal)
**Proposed verdict:** `PASS_SENSOR_B4_I07R1G_RUNTIME_PROOF_SCHEMA_REPLAY_PARITY_SEALED`
**Branch:** `agent/crypto-sensor-fabric-build`
**Repo:** dabiggestpoppa/larger-lab
**Operator review state at start:** `HOLD_PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED_PENDING_I07R1G_RUNTIME_PROOF_SCHEMA_SEAL`, with `PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED = OPERATOR_HOLD` and `PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED = OPERATOR_HOLD`

---

## 1. SHAs

| Item | Value |
|---|---|
| Mandatory starting SHA | `d10f2a5ee9e249b0e70b2f745a0b44aa64777e40` (I07R1F missing-proof runtime proof) |
| Verified at session start | exact — branch `agent/crypto-sensor-fabric-build`, clean tree, `d10f2a5e` is an ancestor of `HEAD` |
| Required lineage | `619cbaf0` I07R1F-A → `7fa51ada` I07R1F-B → `91294f10` ledger LF repair → `d10f2a5e` missing-proof adversarial proof ✔ |
| I07R1G commit chain | `3c838e4d` I07R1G-A → `<this commit>` I07R1G-B |
| Ending SHA | see the I07R1G-B commit at the ledger tail |

No reset, no rebase, no force push, no history rewrite at any point.

## 2. Historical evidence — untouched

`BLOC_04_I07_JOB_STATE_MATRIX.json`, `BLOC_04_I07_RESUME_COUPLING_MATRIX.json`,
`BLOC_04_I07_JOB_RESUME_EVIDENCE.md`, the four `BLOC_04_I07R1_*_MATRIX.json` files,
`BLOC_04_I07R1_GATE_IDENTITY_REPLAY_EVIDENCE.md`, the two `BLOC_04_I07R1F_*_MATRIX.json`
files and `BLOC_04_I07R1F_PERSISTED_FLOOR_CONCURRENCY_LEDGER_EVIDENCE.md` were **not**
rewritten. `git diff d10f2a5e..HEAD -- .../evidence/` contains only the **single added**
`BLOC_04_I07R1G_RUNTIME_PROOF_PARITY_MATRIX.json` (status `A`, zero `M`). The
I06/I06R1/I07/I07R1/I07R1F read-only byte-comparison tests all still pass.

## 3. Operator finding → seam closed (§0/§3)

**Finding:** the runtime exact-retry path validated that a committed checkpoint's
`checkpoint_proof` **existed**, but not that it was **valid**; restart validated the full
contract. Runtime truth and restart truth therefore had two owners, and they disagreed.

**Closure:** one authority now serves both paths.

```
validate_checkpoint_proof(event_id, proof)            # module-level, PURE
    -> (floor, acquisition_id, blob_sha256, manifest_id)
       closed V1 field set · version · floor ∈ MIN_DURABLE_STATES
       floor↔manifest rule · nonempty anchors

DurableJobStateRepository._validate_checkpoint_proof(
    *, event_id, job_id, proof, resulting)            # one call per path
    proof↔resulting-state anchor binding (I07R1 §17)
    durable batch re-proof under the floor PERSISTED in the proof (I07R1 §19/§25)

callers:
    _retry_committed_checkpoint(...)   # runtime exact retry (before any adoption)
    _validate_cross_constraints(...)   # restart replay (replaces _reprove_checkpoint)
```

`_reprove_checkpoint` — the old restart-only re-prover — is **deleted**, not paralleled:
its rules live in the single authority. Both call sites invoke the same method, so the
reader and the writer can no longer drift (§4/§10/§15).

## 4. Runtime exact-retry flow (§9)

```
with self._job_lock(job_id):                     # outermost lock → validated refresh
    current = self.get_job(job_id)               # may be a REFRESHED forged head
    if current.status is CHECKPOINT_ADVANCED:
        return self._retry_committed_checkpoint(...)
```

Inside `_retry_committed_checkpoint`, in order:

1. latest event resolved; a `CHECKPOINT_ADVANCED` head with no event is corruption;
2. the committed `resulting_state` is parsed — an unparseable one is corruption
   (no raw `KeyError`/`ValidationError` escape);
3. `self._validate_checkpoint_proof(...)` — **structure, closed version, floor,
   proof↔result anchors, durable re-proof under the persisted floor** (steps 2–5 of §9);
4. the caller's retry semantics (resume token, acquisition anchor, manifest anchor) are
   compared against the committed state;
5. the exact retry is adopted and returned.

Success is unreachable before steps 2–5 complete.

## 5. Runtime / restart parity (§10/§11) — measured, before → after

Both paths were attacked with the **same** durable chain: the repository is constructed
**before** the fabrication, the forged **later** checkpoint head is published at its
correct hashed physical key (a fresh logical id, so the post-lock refresh **adopts** it
and restart validation never sees the chain), and the head is **chain-valid** —
`ACQUIRING -> CHECKPOINT_ADVANCED`, canonical `job_id:sequence` identity,
`resulting_state.updated_at == transition.transitioned_at`, nonempty reason. The only
difference from an adoptable checkpoint is the proof.

Measured against the pre-I07R1G runtime path (only that runtime branch neutralised, in a
backed-up hash-verified copy — restart was untouched and refused every case):

| Forged proof | runtime (before) | restart (before) | runtime (after) | restart (after) |
|---|---|---|---|---|
| proof missing | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| proof_version = 2 | **NO_ERROR (adopted)** | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| proof_version missing | **NO_ERROR (adopted)** | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| minimum_durable_status missing | **`KeyError`** | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| minimum_durable_status unknown | **`ValueError`** | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| acquisition anchor mismatch | **NO_ERROR (adopted)** | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| blob anchor mismatch | **NO_ERROR (adopted)** | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| manifest anchor mismatch | **NO_ERROR (adopted)** | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| RAW floor + manifest anchor | **`JobTransitionConflict`** | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| MANIFEST floor + no manifest | **`JobTransitionConflict`** | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| proof = `[]` | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| proof = `{}` | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| proof = `"proof"` | **`TypeError`** | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| proof = `1` | **`TypeError`** | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| proof = `True` | **`TypeError`** | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| proof + unexpected extra field | **NO_ERROR (adopted)** | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| same blob, wrong acquisition | **`JobTransitionConflict`** | `JobCatalogCorrupt` | `JobCatalogCorrupt` | `JobCatalogCorrupt` |
| **intact-control (not an attack)** | accepted | accepted | **accepted** | **accepted** |

Before: **6 forged heads silently ADOPTED at runtime**, **5 raw Python exceptions**
(`KeyError`/`ValueError`/`TypeError`) escaped the public corruption classification, and
3 persisted-corrupt records surfaced as the wrong typed error (`JobTransitionConflict`,
because the old path re-proved the *caller's* anchors instead of the persisted ones).
After: **17/17 forged cases `JobCatalogCorrupt` on both paths**, chain unchanged in every
case; only absence, a non-mapping and the empty mapping were already caught before —
existence, never validity.

**Non-vacuity control (§10/§11).** The same forgery mechanics with an **intact** proof are
**accepted on both paths** (runtime adopts the forged head — same status, same anchors,
no new event written; restart loads cleanly). The rejections above are therefore specific
to proof *validity*, not to the forged event's shape (chain position, event id, anchors,
chronology).

## 6. Typed corruption, never an implementation exception (§7/§8)

| Surface | Before | After |
|---|---|---|
| absent proof | `JobCatalogCorrupt` (presence check) | `JobCatalogCorrupt` |
| proof not a mapping (`[]`, `"p"`, `1`, `True`) | truthy → `TypeError` on subscript | `JobCatalogCorrupt` |
| proof not the closed V1 field set (missing / extra) | missing floor → `KeyError`; extra field → ignored | `JobCatalogCorrupt` |
| unknown / non-durability floor | `ValueError` (or silently used) | `JobCatalogCorrupt` |
| anchors divergent from the resulting state | **not checked at runtime** | `JobCatalogCorrupt` |

`proof_version` is compared with a `bool` guard, so `True` cannot pass as `1`.

## 7. Same-bytes wrong-anchor attack (§12)

Two durable acquisitions share the **exact** physical blob SHA; the second carries a
different `request_fingerprint`. The forged proof and the forged resulting state **agree
with each other** and both point at the second acquisition — internally consistent, byte-
identical content — yet the re-proof rejects it because the durable request identity does
not match the job's birth (I07R1 §7). Matrix fields `identical_blob_sha256 = true`,
`different_request_identity = true`,
`forged_anchors_internally_consistent = true`, `runtime_rejected = restart_rejected = true`.

The matrix also covers the wrong-typed (`isinstance`-guarded) sibling variant: an
acquisition that is *not* even durable cannot be reached either, since the re-proof
resolves it from the repository first.

## 8. Valid history is not reinterpreted (§13/§14)

| Regression | Result |
|---|---|
| RAW-persisted checkpoint retried under a MANIFEST_COMMITTED constructor | PASS — adopted, `last_manifest_id = None`, blob anchor exact, 1 gate event |
| MANIFEST-persisted checkpoint retried under a RAW_COMMITTED constructor | PASS — adopted, manifest preserved, persisted proof floor still `MANIFEST_COMMITTED`, 1 gate event |
| All I07R1F persisted-floor + catalog-concurrency tests (12) | PASS, unchanged |
| Divergent caller batch on a valid checkpoint | still `JobTransitionConflict` — a valid record with a divergent request is **not** corruption (the validator re-proves the **persisted** anchors, never the caller's) |
| Crash-after-publication adoption (`_commit_adopting`) | unchanged |

## 9. Load-bearing negative proof

`jobs.py` was backed up (md5 `41531a946a4c76277316707e2612a730`), then **only** the runtime
call to the new authority was neutralised back to the pre-I07R1G shape
(`if not last.get("checkpoint_proof"): raise …` + a raw
`StorageJobStatus(last["checkpoint_proof"]["minimum_durable_status"])`), and the new suite
was re-run: **15 of 19 tests failed**, each with the exact predicted mode from the table in
§5 (six `NO_ERROR` silent adoptions, `KeyError`, `ValueError`, three `TypeError`s, three
`JobTransitionConflict`s). The file was then restored from the backup and re-verified:
md5 `41531a94…` — byte-identical, both new call sites present (runtime and replay) plus the
authority definition, `git diff` clean against the commit. Re-run: 19/19 green.

## 10. Test counts

Fresh exact-head baseline measured in a **clean `git worktree` at `d10f2a5e`**
(`core.autocrlf=false`, so the read-only evidence byte comparisons are meaningful):

| Scope | Collected | Passed | Failed | Skipped |
|---|---|---|---|---|
| Baseline storage @ `d10f2a5e` | 1080 | 1077 | 0 | 3 |
| Baseline full @ `d10f2a5e` | 2460 | 2456 | 0 | 4 |
| Final storage @ I07R1G | 1101 | 1098 | 0 | 3 |
| Final full @ I07R1G | 2481 | 2477 | 0 | 4 |

Delta = **+21 tests** (19 adversarial in `test_job_state_r1g.py` — 17 forged cases + the
intact-proof control + the same-bytes premise test — plus 2 read-only evidence tests in
`test_i07r1g_evidence.py`). Zero failures; pass count above the fresh baseline.

## 11. Static analysis, prohibitions, network

| Item | Result |
|---|---|
| `ruff check` (changed scope: `jobs.py`, `test_job_state_r1g.py`, `test_i07r1g_evidence.py`) | clean — `All checks passed!` |
| `mypy src/.../storage/jobs.py` | **1 error**: the documented pre-existing `probes/planner.py:79` `call-overload` baseline (out of scope, unchanged). The production change itself is clean. |
| `mypy` on the new test modules (PRECISE, not optimistic) | Exactly **7** errors in `test_job_state_r1g.py` + `test_i07r1g_evidence.py`, and every one is `import-not-found` (`_sibling_import` ×2, `crypto_sensor_fabric.providers.base.models` ×2, `…storage.enums` ×2, `…storage.jobs` ×1). The pre-existing sibling pair (`test_job_state_r1f.py` + `test_i07r1f_evidence.py`) reports **11** errors of that same class. When the source root is resolved in the same mypy invocation the pre-existing `ResumeToken(mode="PAGE")` `arg-type` note appears in BOTH the r1g and the r1f module (measured: `mypy src/.../jobs.py tests/.../test_job_state_r1f.py` and the r1g equivalent each report it). So the new test files add **instances of an existing noise class, not a new class of typing error** — but the hard-gate line "mypy changed scope clean" is literally unmet for them, and this file says so rather than claiming otherwise. |
| Network calls | 0 — every proof runs against the local durable stack |
| Provider source | unchanged — no file under `providers/` touched |
| Catalog RLock / new-checkpoint floor authority | unchanged (I07R1F behaviour preserved) |
| I08 / recovery scanner / quarantine / stale-lock deletion / orphan reconciliation | NOT started |
| DuckDB / Postgres / RawEvidenceQuery / Bloc-3 integration / backfill / quota / live recorder / Bloc 5 | not touched |
| Module split / fixture cleanup / typed-event refactor | NOT done (explicitly forbidden) |
| Evidence tree after test execution | git-clean (read-only governance holds; the new matrix is regenerated byte-identically) |
| Research | NOT resumed |

**Recorded honestly, pre-existing, out of scope:** after the suites ran, the same seven
I03R1/I04-era evidence files were dirty again with **identical insert/delete counts**
(`BLOC_04_I03R1_ATOMIC_ORDER.json` 40/40, `BLOC_04_I03R1_NAMESPACE_DURABILITY.json` 52/52,
`BLOC_04_I04R1_POINTER_SCHEMA.json` 199/199, `BLOC_04_I04R1_PROVENANCE_MATRIX.json` 92/92,
`BLOC_04_I04R2_USABLE_PROVENANCE_MATRIX.json` 82/82, `BLOC_04_I04_CATALOG_SCHEMAS.json`
328/328, `BLOC_04_I04_MANIFEST_CONCURRENCY.json` 159/159) — those legacy modules rewrite
their committed matrices with `Path.write_text` during pytest and Windows translates `\n`
to `\r\n`. Content is byte-identical and all seven were restored with
`git checkout HEAD --` before committing, so this commit carries **zero** historical-
evidence changes. Per §19 this is not counted as an I07R1G behavioural failure.

## 12. Post-audit repair pass (this commit)

A read-only four-dimension audit of this checkpoint named two small defects **inside the lines this
pass touched**, plus two record-keeping facts. Both defects are closed here; nothing else changed, and
the spec's prohibitions (no module split, no fixture cleanup, no event-model redesign, no I08) remain
in force.

| Item | Before | After |
|---|---|---|
| Replay validation order | unifying the proof contract moved the durable re-proof (repository + physical-blob I/O) AHEAD of the pure `validate_transition` check — an inverted, gratuitous order | the CHEAP pure graph check runs FIRST; the durable re-proof follows it (replay loop, `jobs.py:1255`–`jobs.py:1286`) |
| Checkpoint predicate | the per-event loop recomputed `is_checkpoint = transition.to_status is CHECKPOINT_ADVANCED` inline while the module already defined `is_checkpoint_event` and used it in the neighbouring per-job loop | the per-event loop calls `is_checkpoint_event(payload)`; both loops share the one predicate, and no inline duplicate remains anywhere in the file (verified by grep) |

Both edits are ordering/ownership refactors only — every rejection still classifies as
`JobCatalogCorrupt`. Verified by re-running the full job/resume surface (135 passed) including the 17
forged cases (all still fail closed on BOTH paths), the intact-proof control (still accepted on both
paths) and the read-only matrix byte comparison: the committed
`BLOC_04_I07R1G_RUNTIME_PROOF_PARITY_MATRIX.json` regenerates **byte-identically**, so these two source
edits required **no evidence change**. Re-measured at the final repaired tree: **storage 1101 collected /
1098 passed / 0 failed / 3 skipped**, **full 2481 collected / 2477 passed / 0 failed / 4 skipped** —
identical to the pre-repair counts in §10, because the two edits change no test outcome. `ruff check` on
`jobs.py` is clean and `mypy src/.../storage/jobs.py` still reports only the documented
`probes/planner.py:79` baseline.

### Facts the operator may want to veto

**1. The closed field-set check is stricter than the enumerated attack list.** §5 states the proof
schema is "exactly" the five fields, so rejecting a proof carrying an unexpected field follows from
it — but §11's letters A–L asked only for non-mapping proofs (`[]`, `{}`). A proof with an extra field
was ACCEPTED before this checkpoint (measured: `NO_ERROR (adopted)` at runtime, table in §5) and is
now `JobCatalogCorrupt` on both paths.

*Is any legitimate writer at risk? No — measured, not assumed.* `checkpoint_proof` has exactly ONE
write site in the entire `src/` tree: `jobs.py:770` inside `_append_checkpoint_event`, which emits the
five closed fields and nothing else; no other module reads or writes the proof, and the adoption path
(`_commit_adopting`) only compares event semantics. A genuine checkpoint produced by the real stack was
inspected: its proof key set is exactly
`{acquisition_id, blob_sha256, manifest_id, minimum_durable_status, proof_version}` — equal to
`CHECKPOINT_PROOF_FIELDS`, zero extras. Only TWO paths can reach the extra-field rejection, and both
read the proof from the DURABLE catalog rather than accept one from a caller:

| Path | Entry | Reaches the rule through |
|---|---|---|
| Runtime exact retry | `advance_checkpoint` on a `CHECKPOINT_ADVANCED` head | `_retry_committed_checkpoint` → `_validate_checkpoint_proof` |
| Restart replay | `DurableJobStateRepository.__init__` | `_validate_cross_constraints` → `_validate_checkpoint_proof` |

**Therefore only forged or hand-edited durable records are at risk**: no code path that writes a proof
through the normal API can be rejected by the closed field-set rule.

**2. Two test/matrix variants were not requested.** §11 K/L asked for `[]` and `{}`; the committed case
table and the matrix additionally carry a `bool` proof (`True`) and an extra-field proof. Both are
additions to the requested surface: they change no production behaviour beyond the closed field-set
rule above (measured: `JobCatalogCorrupt` on both paths, aggregated under the `proof_wrong_type`
matrix case as six schema variants), and they are recorded here so the operator can veto them without
diffing the test files.

## 13. Proposed ledger state

```
Current checkpoint = SENSOR-B4-I07R1G
PASS_SENSOR_B4_I07R1G_RUNTIME_PROOF_SCHEMA_REPLAY_PARITY_SEALED     = PENDING_OPERATOR_REVIEW
PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED = OPERATOR_HOLD
PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED                   = OPERATOR_HOLD
PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED                 = OPERATOR_HOLD
DURABLE_RESUME_IMPLEMENTED   = PENDING_OPERATOR_ACCEPTANCE
RECOVERY_SCANNER_IMPLEMENTED = FALSE
next_checkpoint_authorized   = FALSE
recommended_next             = SENSOR-B4-I08 RECOVERY / QUARANTINE — ONLY AFTER operator acceptance
```

On operator acceptance of this microseal, `PASS_SENSOR_B4_I07R1F…` may be accepted, then
`PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED` and
`PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED`.

**STOP GATE honored:** I08 (recovery / quarantine) NOT started. Research NOT resumed.

---

## Core doctrine applied

- **Proof existence is not proof validity.**
- **Runtime truth and restart truth must have one owner.**
- A long-lived repository that refreshes new durable records must reject the same corrupt checkpoint proof that a fresh restart would reject.
- Malformed durable history produces typed corruption, never `KeyError`, `ValueError` or silent adoption.
- A proof that is internally consistent can still be a lie; the durable evidence re-decides.
- A valid record with a divergent retry request is a conflict, not corruption.
- Constructor configuration governs new checkpoints; persisted proof governs historical checkpoints.
- The reader must enforce the same state machine as the writer.
