# SENSOR-B4-I07R1H — Runtime Refreshed-Chain + Restart Validation Parity

**Checkpoint:** SENSOR-B4-I07R1H — runtime refreshed-event chain + restart
validation parity
**Branch:** agent/crypto-sensor-fabric-build
**Starting SHA:** `7a7d576c056693a49cf261753af886a5b4df4e0c`
**Ending SHA:** commit chain below (`765ed1a2` implementation + adversarial
surface; the freeze commit carrying this MD + matrix + ledger is the end).
**Operator review state at freeze:** every I07 approval remains
`OPERATOR_HOLD`; I07R1H is `PENDING_OPERATOR_REVIEW`; nothing here is
self-ratified.  I08 NOT started.

---

## §1 Start lock

- Branch `agent/crypto-sensor-fabric-build` HEAD exactly
  `7a7d576c056693a49cf261753af886a5b4df4e0c`, clean tree.
- Lineage verified: `3c838e4d` I07R1G-A → `b24ef884` I07R1G-B → `7a7d576c`
  I07R1G post-audit repair.  No reset, no rebase, no force push.
- Historical I07 / I07R1 / I07R1F / I07R1G evidence and the historical
  ledger sections untouched (§2).

## §2 Operator finding

The OUTERMOST per-job file lock calls `_births.refresh()` +
`_events.refresh()` and `get_job()` then materializes the newest
`resulting_state` directly.  Catalog refresh proves fragment parse,
physical-key/logical-id binding, cached-vs-disk divergence and vanished
records — but NOT job-chain semantics.  A long-lived repository could
therefore consume, as authoritative runtime state, an event that a fresh
restart would reject with `JobCatalogCorrupt`.

## §3 Why catalog validity ≠ job-chain validity

`DurableJsonCatalog.refresh()` validates the record against the CATALOG
contract (parse + `catalog_physical_key(logical_id)` filename binding).
The JOB contract is a different, larger object: canonical event identity
(`_event_id(job_id, sequence)`), transition/result binding, immutable
birth identity, result/transition time binding, the frozen transition
graph, chain contiguity + linkage + chronology, ordinary pointer
immutability, and the proof↔event relation.  A physically well-formed
fragment at the right hashed key passes refresh while violating every one
of those rules — which is exactly what the forged heads in §7 do (each is
published at its CORRECT hashed physical key; refresh adopts it; only job
validation can refuse it).

## §4 Shared per-job validation architecture (I07R1H §4/§20)

ONE authority: `DurableJobStateRepository._validate_job_chain(job_id)`.

- **Restart** (`__init__` → `_validate_cross_constraints`): the global
  unknown-job check (§15) sweeps every event id against the birth
  catalog, then the per-job authority runs for EVERY known job — restart
  coverage is unchanged (§14).
- **Runtime** (`_NestedFileLock.__enter__` → `_refresh_durable_truth`):
  after BOTH catalog refreshes complete, the per-job authority runs for
  the LOCKED job only — targeted, never a global all-job rescan (§5/§28).

No rule is duplicated: the per-event and per-job rules moved verbatim
from the old monolithic `_validate_cross_constraints` into the shared
method, which now owns

- birth contract (§6): `record_kind == job_birth`, exact `job_id`, valid
  `StorageJobState`, status `PLANNED`; the legitimate new-job path (a
  `create_job` caller under the lock with no birth and no events) passes;
- every event (§7): frozen `StorageJobTransition`/`StorageJobState`
  validation, integer sequence ≥ 1, canonical
  `_event_id(job_id, sequence)` identity, `transition.transition_id ==
  event_id`, `transition.job_id == job_id`, `resulting.job_id == job_id`,
  `resulting.status == transition.to_status`, birth identity immutability
  (provider/sensor/request_fingerprint), `resulting.updated_at ==
  transition.transitioned_at`;
- chain (§10/§11): contiguity from 1, `transition.from_status ==
  previous.status`, forward chronology
  (`transitioned_at >= previous.updated_at`), and exact preservation of
  `resume_token` / `last_committed_acquisition_id` /
  `last_committed_blob_sha256` / `last_manifest_id` on every
  non-checkpoint event.

Reused ONE-owner primitives, unchanged (§8/§9): `validate_transition(...)`
(the writer's graph), `is_checkpoint_event(...)` (the I07R1G post-audit
predicate), `_validate_checkpoint_proof(...)` (the I07R1G proof authority
runtime + restart already share), `_job_events`, `_event_id`.

## §5 Runtime refresh ordering (§12/§13)

Outer-lock sequence is now exactly:

1. acquire file lock (outermost; nested entries reuse the fresh view);
2. `self._births.refresh()`;
3. `self._events.refresh()`;
4. `self._validate_job_chain(job_id)`;
5. ONLY THEN: `get_job()`, `_next_sequence()`, `expected_from` CAS,
   retry classification, new transition construction.

Both refreshes finish before validation begins — one post-refresh
snapshot, never a half-refreshed view — and a corrupt refreshed tail
fails BEFORE it can influence any runtime decision.

## §6 Restart reuse (§14)

The old `_validate_cross_constraints` carried the per-event rules in one
loop and the per-job rules in a second loop.  Both loops now delegate to
`_validate_job_chain`; the entry point keeps only what the per-job view
cannot see: the unknown-job event rejection (§15) and the complete
per-job sweep.  No restart check was removed or weakened — the same
assertions run, from the same code, in the same order (cheap pure checks
before the expensive durable re-proof, preserving the I07R1G post-audit
ordering).

## §7 Attack outcomes (§16-§25)

Every attack uses the proven I07R1G shape: repository constructed FIRST,
legitimate chain (birth → manifest-committed batch → checkpoint →
annotated continuation), forged later head published at the CORRECT
hashed physical key so outer-lock refresh ADOPTS it, then the runtime
operation executes.  Where a proof is present it stays FULLY VALID — only
event/chain semantics are corrupted (proof corruption is I07R1G §16).

Measured results (each also recorded in
`BLOC_04_I07R1H_REFRESHED_CHAIN_PARITY_MATRIX.json`; every corruption
case: `runtime_rejected = true`, `restart_rejected = true`,
`typed_error = JobCatalogCorrupt`, `chain_unchanged = true`):

| case | attack |
|---|---|
| `from_status_chain_break` (§17) | prior real head ACQUIRING; forged checkpoint claims `from_status = RAW_STAGED`; proof valid |
| `transition_job_id_mismatch` (§18) | top-level event job_id = real job; `transition.job_id` = another REAL existing job |
| `result_status_mismatch` (§19) | `resulting.status != transition.to_status` with anchors untouched |
| `provider_identity_mismatch` (§20) | resulting `provider_id` mutated under a valid proof |
| `sensor_identity_mismatch` (§20) | resulting `sensor_family` mutated |
| `request_identity_mismatch` (§20) | resulting `request_fingerprint` mutated |
| `updated_at_transition_mismatch` (§21) | `resulting.updated_at != transition.transitioned_at` |
| `backward_chronology` (§21) | transition instant predates the previous head (time binding kept consistent) |
| `sequence_gap` (§22) | forged sequence +7, physical key recomputed for the forged logical id (catalog integrity passes; job validation catches it) |
| `event_identity_mismatch` (§23) | logical id / sequence relationship violates `_event_id(job_id, sequence)`; physical key valid for the logical id so corruption reaches JOB validation |
| `ordinary_resume_pointer_mutation` (§24) | chain-valid ORDINARY event, mutated `resume_token` |
| `ordinary_anchor_mutation` (§24) | chain-valid ORDINARY event, mutated committed anchor |
| `proof_on_ordinary_event` (§25) | ORDINARY event carrying a fully valid-looking `checkpoint_proof` |

All 13: runtime `JobCatalogCorrupt` BEFORE the forged head influences any
decision; fresh restart over the identical chain `JobCatalogCorrupt`;
event count unchanged (corruption never writes).

## §8 Intact control (§26)

`intact_refreshed_control`: the same publication mechanics with a fully
chain-valid event (valid proof, canonical identity, correct linkage).  It
is ADOPTED at runtime through the refresh path and accepted at restart —
and the probe's own `+1` event (the annotated continuation appended after
the forged head) proves the forged head really entered the chain; a
sequence collision would have raised instead.  The new validation rejects
chain corruption, never records merely because they arrived via refresh.

## §9 I07R1G proof-parity regression (§16/§27)

The committed `BLOC_04_I07R1G_RUNTIME_PROOF_PARITY_MATRIX.json` still
regenerates byte-identically and its 18-case module passes: the 17 forged
proof cases fail closed on BOTH paths, the intact-proof control is still
adopted.  `test_checkpoint_head_without_proof_fails_closed` (d10f2a5e)
remains green.  The r1h runtime gate calls the SAME proof authority, so
runtime and restart still cannot disagree about a persisted proof.

## §10 Cross-repository + persisted-floor regressions (§27)

- RAW-persisted / MANIFEST-constructor exact retry: adopted, `manifest
  anchor None` preserved (matrix `valid_raw_cross_constructor_retry`).
- MANIFEST-persisted / RAW-constructor exact retry: adopted under the
  persisted MANIFEST floor (matrix
  `valid_manifest_cross_constructor_retry`).
- Two-repository refresh, two-repository sequence serialization, external
  exact checkpoint retry: all I07R1/I07R1F tests green.
- Catalog RLock unchanged; constructor-floor authority for NEW
  checkpoints unchanged.

## §11 Job-local validation (§5/§28)

`test_runtime_validation_is_job_local`: job A's chain carries a corrupt
forged head; a different healthy job B is operated by the SAME long-lived
repository without obstruction, while A's own next operation fails
closed.  Runtime cost is bounded to the locked job's chain; no global
rescan per lock.  The runtime path replays the complete LOCKED job chain
each outer lock (simple, mechanically proven); no incremental-tail cache
was invented — recovery belongs to I08.

## §12 Baseline and final counts

- Fresh exact-head baseline at `7a7d576c` (measured, this session):
  storage **1098 passed / 0 failed / 3 skipped** (1101 collected); full
  **2477 passed / 0 failed / 4 skipped** (2481 collected) — matches the
  I07R1G recorded counts.
- Final tree: storage **1115 passed / 0 failed / 3 skipped** (1118
  collected); full **2494 passed / 0 failed / 4 skipped** (2498
  collected).  Delta +17 passed on both suites, zero failures.
- Transparency: one earlier full-suite run observed a single failure in
  the pre-existing `test_blob_store_adversarial.py::
  TestConcurrency::test_concurrent_identical_writers_one_final` (a
  threading test in the blob store, code untouched by this checkpoint);
  it passes in isolation and in the recorded final run.  No
  jobs/resume/refresh test failed at any point in this chain.
- Network calls: 0.  Provider source: unchanged.

## §13 Ruff / mypy — precise statement (§31)

- Ruff: clean on all changed scope (`jobs.py`, `test_job_state_r1h.py`,
  `test_i07r1h_evidence.py`).
- Production changed source: `mypy quant-lab/src/crypto_sensor_fabric/
  storage/jobs.py` reports exactly **1 error** — the pre-existing,
  previously documented `probes/planner.py:79` baseline (`call-overload`
  pulled in via the probe import chain).  No new error, no new error
  class.
- New test modules: the repository defines **no `[tool.mypy]` policy**
  (`pyproject.toml` has none), so "mypy changed scope clean" was
  previously satisfied only loosely.  For this checkpoint the modules
  were type-checked with the repository source root CONFIGURED
  (`MYPYPATH="quant-lab/src;quant-lab/tests/crypto_sensor_fabric/
  storage"`): `test_job_state_r1h.py` and `test_i07r1h_evidence.py` are
  **fully clean** — zero errors, no `import-not-found`, no arg-type
  notes.  The only remaining error under any configuration is the
  documented `probes/planner.py:79` baseline.

## §14 Evidence governance

- Historical I07 / I07R1 / I07R1F / I07R1G evidence and matrices:
  untouched (`git diff d10f2a5e..HEAD` under `evidence/` shows only
  I07R1G and I07R1H additions).
- This checkpoint's matrix (`BLOC_04_I07R1H_REFRESHED_CHAIN_PARITY_
  MATRIX.json`, 16 cases) was published ONCE via the explicit builder
  entry point; normal pytest runs generate in tmp dirs and compare
  against committed bytes (`test_generated_matches_committed` +
  `test_evidence_directory_untouched_after_run`).  Evidence tree LF (CR
  = 0) and git-clean after test execution.
- The seven pre-existing I03R1/I04-era evidence modules still re-emit
  CRLF during full-suite runs (out-of-scope, previously recorded); they
  were restored after the final run and are not part of this commit.

## §15 Ledger

Top-level Current state advanced to `SENSOR-B4-I07R1H` truth:
`PASS_SENSOR_B4_I07R1G_RUNTIME_PROOF_SCHEMA_REPLAY_PARITY_SEALED`,
`PASS_SENSOR_B4_I07R1F_PERSISTED_FLOOR_CATALOG_CONCURRENCY_LEDGER_SEALED`,
`PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED`,
`PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED` all `OPERATOR_HOLD`;
I07R1H `PENDING_OPERATOR_REVIEW`;
`DURABLE_RESUME_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`;
`RECOVERY_SCANNER_IMPLEMENTED = FALSE`;
`next_checkpoint_authorized = FALSE`; recommended next = SENSOR-B4-I08
RECOVERY / QUARANTINE ONLY AFTER operator acceptance.  No self-ratification;
historical ledger sections untouched.

## §16 Scope boundaries

No I08 implementation, no recovery scanner, no stale-lock recovery, no
quarantine movement, no quota, no DuckDB, no Postgres, no provider
integration, no proof redesign, no module split, no event-model redesign,
no fixture cleanup, research NOT resumed.

---

## Core doctrine

Catalog integrity is not job-chain validity.  A record adopted by refresh
must satisfy the same durable job contract a restart would enforce before
it can influence runtime state.  Valid proof does not excuse an invalid
event.  Runtime truth and restart truth must have one chain authority.
