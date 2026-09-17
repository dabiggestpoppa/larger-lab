# SENSOR-B4-I07R1F — PERSISTED-FLOOR + CATALOG-CONCURRENCY + LEDGER-TRUTH MICROSEAL — EVIDENCE

**Checkpoint:** SENSOR-B4-I07R1F (Persisted-Floor Retry + Catalog Concurrency + Operator-Ledger Truth Seal)
**Proposed verdict:** `PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED`
**Branch:** `agent/crypto-sensor-fabric-build`
**Repo:** dabiggestpoppa/larger-lab
**Operator review state at start:** `HOLD_PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED_PENDING_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEAL`, with `PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED = OPERATOR_HOLD`

---

## 1. SHAs

| Item | Value |
|---|---|
| Mandatory starting SHA | `dd4db19715f8d4fa39af421b882b21c976cd42cf` (SENSOR-B4-I07R1E) |
| Verified at session start | exact — branch `agent/crypto-sensor-fabric-build`, clean tree |
| Required lineage | `cbb93b15` I07R1A/B/C/D → `dd4db197` I07R1E ✔ |
| I07R1F commit chain | `619cbaf0` I07R1F-A → `<this commit>` I07R1F-B |
| Ending SHA | see the I07R1F-B commit at the ledger tail |

No reset, no rebase, no force push at any point.

## 2. Historical evidence — untouched

`BLOC_04_I07_JOB_STATE_MATRIX.json`, `BLOC_04_I07_RESUME_COUPLING_MATRIX.json`,
`BLOC_04_I07_JOB_RESUME_EVIDENCE.md`, `BLOC_04_I07R1_PUBLIC_API_MATRIX.json`,
`BLOC_04_I07R1_CHECKPOINT_IDENTITY_MATRIX.json`,
`BLOC_04_I07R1_RESTART_REPLAY_MATRIX.json`,
`BLOC_04_I07R1_COORDINATION_MATRIX.json` and `BLOC_04_I07R1_GATE_IDENTITY_REPLAY_EVIDENCE.md`
were **not** rewritten. The I07R1F evidence (2 matrices + this file) is new and
chronological, and `git diff dd4db197..HEAD` shows zero modifications under
`research/crypto_foundry/sensor_fabric/evidence/` other than the two added files.
The I06/I06R1/I07/I07R1 read-only byte-comparison tests all still pass.

## 3. Operator findings → seams closed (A, B, C)

| Seam | Closure |
|---|---|
| **A — exact historical checkpoint retry can be rejected by the CURRENT constructor floor before the PERSISTED floor is read** | `advance_checkpoint` now detects an existing `CHECKPOINT_ADVANCED` head **first** and delegates to the new private `_retry_committed_checkpoint`, which validates the batch against — and re-proves the durable evidence under — the floor **persisted in that checkpoint's own proof**. The new-checkpoint caller-shape rules (formerly executed before the lock, unconditionally) moved into `_require_checkpoint_shape`, applied to NEW checkpoints only (§3-§7). |
| **B — `DurableJsonCatalog` cache operations are not internally synchronized while per-job locks allow different jobs to run concurrently** | One `threading.RLock` per catalog now guards the complete `_cache` critical sections of `refresh`, `commit`, `get`, `has`, `list_ids` and `__len__` (plus `_load_all`). RLock — not Lock — so the validated reload/commit helpers reuse it without self-deadlock. `refresh`/`commit` keep their public signatures; their bodies moved to `_refresh_locked` / `_commit_locked` under the lock (§9-§10). |
| **C — the operator-facing top-level ledger still reports `SENSOR-B4-I06R1-RATIFY` as current truth** | The `Current state` table rows (`Current checkpoint`, `Operator review state`, `next_checkpoint_authorized`) now carry the I07R1F truth: `PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED = OPERATOR_HOLD`, `PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED = PENDING_OPERATOR_REVIEW`, `SENSOR-B4-I07R1F = PENDING_OPERATOR_REVIEW`, `DURABLE_RESUME_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`, `RECOVERY_SCANNER_IMPLEMENTED = FALSE`, `next_checkpoint_authorized = FALSE`. The old top-level text is retained **inside the same row, explicitly labeled a historical ratified governance record**; the four remaining `SENSOR-B4-I06R1-RATIFY` occurrences are historical checkpoint/commit-log entries and are untouched (§15-§16). |

## 4. Defect A — floor authority (before → after)

Before: `advance_checkpoint` read `floor = self._min_durable_status` and rejected
contradictory caller shapes **before** any examination of the committed chain, so a
RAW-persisted checkpoint retried by a process configured `MANIFEST_COMMITTED` raised
`JobResumeGateError` instead of returning the committed state — and vice versa.

After — one authority split, applied in this order:

```
with self._job_lock(job_id):
    current = self.get_job(job_id)
    if current.status is CHECKPOINT_ADVANCED:
        return self._retry_committed_checkpoint(...)   # PERSISTED floor governs
    if current.status is COMPLETE:
        raise JobTransitionConflict(...)
    floor = self._min_durable_status                   # CURRENT config governs NEW work
    self._require_checkpoint_shape(floor, manifest_id)
    self._require_checkpoint_eligible(current.status, floor)
    blob_sha = self._prove_batch_durable(..., floor=floor)
    return self._append_checkpoint_event(..., floor=floor)
```

| Checkpoint age | Governing floor | Source of truth |
|---|---|---|
| NEW checkpoint | `self._min_durable_status` (constructor) | `_require_checkpoint_shape` + `_prove_batch_durable` |
| HISTORICAL retry | `proof["minimum_durable_status"]` (persisted) | `_retry_committed_checkpoint` → `_prove_batch_durable(floor=persisted_floor)` |

An exact retry is adopted only when the resume token, the acquisition anchor **and** the
manifest anchor all match the committed state; anything divergent remains
`JobTransitionConflict` — persisted-floor support is not overwrite permission (§8).

## 5. Defect B — catalog cache synchronization

| Surface | Guard |
|---|---|
| `_cache_lock` | `threading.RLock()`, created in `__init__` before `_load_all()` |
| `refresh()` | whole scan → compare → adopt sequence under the lock (`_refresh_locked`) |
| `commit()` | whole cache-read → adopt → publish → cache-write sequence under the lock (`_commit_locked`) |
| `get`, `has`, `list_ids`, `__len__`, `_load_all` | under the lock |

The failure this closes: per-job locks let job A's `refresh` list the events directory
**before** job B's commit, then compare `self._cache` (shared) **after** it — so B's
legitimately committed record looked like a vanished committed record and raised a
false `JsonCatalogCorrupt`. Real vanish/divergence detection is unchanged (§13).

## 6. Load-bearing proof (negative verification)

Every new adversarial test was executed against the **pre-fix** sources (`jobs.py` and
`json_catalog.py` restored from `dd4db197`, with the fixed files backed up and
hash-verified before and after). Result — 6 of 12 fail on the old code, each with the
exact predicted failure mode:

| New test | Old-code outcome |
|---|---|
| `test_raw_persisted_checkpoint_retried_under_manifest_constructor` | FAIL — `JobResumeGateError` (current MANIFEST floor rejected a RAW-persisted retry) |
| `test_manifest_persisted_checkpoint_retried_under_raw_constructor` | FAIL — `JobResumeGateError` (current RAW floor rejected a MANIFEST-persisted retry) |
| `test_persisted_proof_floor_never_rewritten_by_constructor` | FAIL — same current-floor rejection |
| `test_divergent_historical_retry_rejected` | FAIL — the retry never reached the divergence check |
| `test_catalog_cache_lock_is_reentrant` | FAIL — `_cache_lock` did not exist |
| `test_refresh_commit_race_does_not_false_corrupt` | FAIL — `JsonCatalogCorrupt("cached committed record logical_id='id-race-new' has vanished from disk; committed catalog truth may never silently disappear")` |
| `test_two_jobs_same_repository_concurrent_checkpoints` | FAIL — `JsonCatalogCorrupt("cached committed record logical_id='job-cc-a:000007' has vanished from disk…")` raised by the slow thread against the fast thread's freshly committed event |

The remaining 6 are deliberate *preserve* proofs (new-checkpoint floor shape, vanished/
divergent fail-closed, cross-repository truth) and correctly pass both before and after.

The two concurrency proofs are made deterministic rather than probabilistic: the
refreshing thread pauses **after** its file listing (and, for the two-job case, the fast
thread does not start until that listing exists), so the committing thread provably
lands inside the scan/compare window. The higher-level two-job proof was initially
jitter-dependent — it passed on the old code because the fast thread could finish before
the slow thread listed — and was re-engineered with the listing handshake until it
reproduced the false corruption reliably.

## 7. Governance reconciliation (§16) and commit-chain deviation (§17)

**I07R1E ledger miss.** I07R1E appended the correct HOLD state at the ledger tail but did
not advance the top-level operator-facing `Current state` table, leaving the head of the
ledger two checkpoints stale. I07R1F corrects the top-level rows and records this
explicitly in the ledger; no historical entry, evidence file or checkpoint section was
rewritten.

**Commit-chain deviation (recorded, NOT repaired).** The I07R1 prompt requested staged
commits `I07R1A` → `I07R1B` → `I07R1C` → `I07R1D` → `I07R1E`. The implementation
delivered A/B/C/D as one combined content commit `cbb93b15` (`SENSOR-B4-I07R1A/B/C/D`),
with `I07R1E` as `dd4db197`. This is a process/staging deviation only — the content is
accepted work. No rebase, no squash, no history rewrite, no force push were performed to
repair it. The I07R1F plan's two commits (`I07R1F-A`, `I07R1F-B`) are followed exactly.

## 8. Machine evidence (§18)

| Matrix | Cases | Result |
|---|---|---|
| `BLOC_04_I07R1F_PERSISTED_FLOOR_MATRIX.json` | `raw_persisted_manifest_constructor_retry`, `manifest_persisted_raw_constructor_retry`, `new_raw_uses_current_floor`, `new_manifest_uses_current_floor`, `divergent_historical_retry_rejected` | 5 / 5 PASS |
| `BLOC_04_I07R1F_CATALOG_CONCURRENCY_MATRIX.json` | `refresh_commit_same_catalog`, `different_jobs_same_repository`, `refresh_vanished_fail_closed`, `refresh_divergence_fail_closed`, `cross_repo_refresh_regression` | 5 / 5 PASS |

10 cases total, all deterministic (regeneration verified byte-identical across runs;
payloads carry only structural fields — statuses, counts, booleans — no timings or
paths). Both matrices were published **once** by explicit operator invocation
(`PYTHONPATH=src python tests/crypto_sensor_fabric/storage/test_i07r1f_evidence.py`);
normal pytest runs compare generated-in-`tmp_path` bytes against the committed artifacts
and never write the evidence tree, which is git-clean after the suites (I05R4 read-only
governance).

## 9. Baseline and final counts

Fresh exact-head baseline was measured at `dd4db197` in a clean `git worktree` (not
copied from the I07R1 evidence), and independently reproduced in the primary checkout:

| Scope | Collected | Passed | Failed | Skipped |
|---|---|---|---|---|
| Baseline storage @ `dd4db197` | 1064 | 1061 | 0 | 3 |
| Baseline full @ `dd4db197` | 2444 | 2440 | 0 | 4 |
| Final storage @ I07R1F | 1079 | 1076 | 0 | 3 |
| Final full @ I07R1F | 2459 | 2455 | 0 | 4 |

Delta = **+15 tests** (12 adversarial in `test_job_state_r1f.py` + 3 in
`test_i07r1f_evidence.py`); zero failures, pass count above baseline.

**Environment note 1 — worktree baselines (affects future baselining).** The
worktree checkout first reported 20 failures, all in the read-only evidence-comparison
tests across seven I0x evidence modules. Cause: the checkout converted the committed
LF evidence JSON to CRLF, so generated LF bytes no longer matched. Re-materialising the
tree with `core.autocrlf=false` reproduced the clean baseline exactly (1061 / 0 / 3
storage, 2440 / 0 / 4 full). The evidence byte-comparison tests are therefore sensitive
to `core.autocrlf`; baselines must be measured with LF line endings in the evidence tree.

**Environment note 2 — PRE-EXISTING governance gap found in the I03R1/I04-era evidence
modules (not introduced by I07R1F, not fixed here).** After the suites ran, `git status`
showed seven historical evidence files as modified:
`BLOC_04_I03R1_ATOMIC_ORDER.json`, `BLOC_04_I03R1_NAMESPACE_DURABILITY.json`,
`BLOC_04_I04_CATALOG_SCHEMAS.json`, `BLOC_04_I04_MANIFEST_CONCURRENCY.json`,
`BLOC_04_I04R1_POINTER_SCHEMA.json`, `BLOC_04_I04R1_PROVENANCE_MATRIX.json`,
`BLOC_04_I04R2_USABLE_PROVENANCE_MATRIX.json`. Inspection showed the diffs were **pure
line-ending changes** (identical content, 328/328 or similar insert/delete counts), with
mtime inside this session. Root cause: the I03R1/I04-era evidence modules
(`test_blob_store_adversarial.py`, `test_blob_store_namespace_evidence.py`,
`test_catalog_evidence.py`, `test_i04r1_evidence.py`, `test_i04r2_evidence.py`) regenerate
their committed matrices **from inside ordinary tests** using `Path.write_text(...)` on
`EVIDENCE_DIR`. Python's default `newline=None` translates `\n` to `os.linesep`, so on
Windows every such run silently rewrites the committed artifact with CRLF. Content was
never altered (the tests assert deterministic regeneration), and all seven files were
restored with `git checkout HEAD --` so this commit carries **zero** historical-evidence
changes. This predates the I05R4 read-only doctrine that later modules honour (every
I05→I07R1F matrix is generate-in-`tmp_path` + byte-compare, and none of them changed on
disk during these runs). Recommended follow-up, deliberately OUT of I07R1F scope: convert
those five legacy modules to the read-only pattern (`tmp_path` generation + byte compare),
or at minimum pass `newline=""` to their writers.

## 10. Static analysis, prohibitions, network

| Item | Result |
|---|---|
| `ruff check` (changed scope) | clean — `All checks passed!` |
| `mypy` (changed scope: `jobs.py`, `json_catalog.py`) | clean except the documented pre-existing `probes/planner.py:79` baseline error (unchanged, out of scope) |
| Network calls | 0 — no new network path; all proofs run against the local durable stack |
| Provider source | unchanged — no file under `providers/` touched |
| I08 / recovery scanner | NOT started — no recovery, quarantine, orphan-reconciliation, stale-lock-deletion or quota code |
| DuckDB / Postgres / RawEvidenceQuery / Bloc-3 integration / backfill / live recorder / Bloc 5 | not touched |
| Module split / fixture cleanup / typed-event refactor | NOT done (explicitly forbidden this checkpoint) |
| Evidence tree after test execution | git-clean (read-only governance holds) |
| Research | NOT resumed |

**Observed once, unreproducible:** a single full-suite run emitted
`PytestUnhandledThreadExceptionWarning`. It is not attributable to I07R1F — all threaded
tests live under `tests/crypto_sensor_fabric/storage`, and the storage suite passes with
`-W error::pytest.PytestUnhandledThreadExceptionWarning` (twice) as does the full suite
(once). The likely source is the pre-existing `test_manifest_concurrency.py`, whose
thread targets (`writer`/`reader`) have no exception guard. Recorded for transparency; no
I07R1F change depends on it.

## 11. Proposed ledger state

```
Current checkpoint = SENSOR-B4-I07R1F
PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED = PENDING_OPERATOR_REVIEW
PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED                     = PENDING_OPERATOR_REVIEW
PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED                   = OPERATOR_HOLD
DURABLE_RESUME_IMPLEMENTED   = PENDING_OPERATOR_ACCEPTANCE
RECOVERY_SCANNER_IMPLEMENTED = FALSE
next_checkpoint_authorized   = FALSE
recommended_next             = SENSOR-B4-I08 RECOVERY / QUARANTINE — ONLY AFTER operator acceptance
```

On operator acceptance of this microseal, `PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED`
and `PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED` may both be accepted.

**STOP GATE honored:** I08 (recovery / quarantine) NOT started. Research NOT resumed.

---

## Core doctrine applied

- A resume gate is not a gate if another public method can mutate the cursor.
- Durable evidence must belong to the exact job/request being advanced.
- Same bytes do not imply same source.
- A manifest reference is not proof until it is bound to the acquisition it claims to index.
- A checkpoint must survive restart under the exact durability policy that authorized it.
- The reader must enforce the same state machine as the writer.
- Logical IDs never become raw filesystem paths.
- A lock without a fresh durable state view does not serialize truth.
- **Constructor configuration governs new checkpoints; persisted proof governs historical checkpoints.**
- **Per-job locking does not make a shared in-memory catalog cache thread-safe.**
- **The operator-facing Current state must tell the truth now, not two checkpoints ago.**
