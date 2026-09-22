# SENSOR-B4-I07R1I — Failed-Gate Atomicity + Validated Public Reads + Ledger Structure

**Checkpoint:** SENSOR-B4-I07R1I — failed outer-entry rollback, validated
public read, ledger structure seal
**Branch:** agent/crypto-sensor-fabric-build
**Starting SHA:** 940c25097774a11c3e3b5282c41f1428fb5f10cf
**Ending SHA:** ee7777d8 (SENSOR-B4-I07R1I-A) + this evidence/ledger commit
(SENSOR-B4-I07R1I-B)
**Operator review state at freeze:** every I07 approval remains
`OPERATOR_HOLD`; I07R1I is `PENDING_OPERATOR_REVIEW`; nothing here is
self-ratified.  I08 NOT started.

## 1. Commit chain

| Commit | Content |
|---|---|
| 765ed1a2 | SENSOR-B4-I07R1H-A (pre-existing lineage) |
| 940c2509 | SENSOR-B4-I07R1H-B (start lock HEAD) |
| ee7777d8 | SENSOR-B4-I07R1I-A — failed-gate rollback + gated public reads + `test_job_state_r1i.py` (§25 A–P) |
| (this commit) | SENSOR-B4-I07R1I-B — 2 machine matrices, this evidence MD, ledger structure repair (§22) |

Process note (recorded, not repaired): the worktree opened at the exact
start SHA with a preserved partial attempt at this checkpoint — a crashed
session had left the implementation and both test modules on disk, but no
verification runs, no evidence MD and no commits.  That state was
re-derived against the spec, verified by execution, and completed; no
history was rewritten.

## 2. Operator finding — why a failed gate became a live reentrant context

`_NestedFileLock.__enter__` (pre-fix order):

1. `self._process_lock.acquire()` — in-process RLock;
2. nested check on `_lock_owners[job_id]`; for an outer entry:
   `_acquire_file_lock(job_id)` and
   `_lock_owners[job_id] = {"thread": ident, "depth": 1}`;
3. `_refresh_durable_truth(job_id)` — both catalog refreshes + the shared
   per-job chain authority `_validate_job_chain`.

If step 3 raised, the bare `except BaseException` released ONLY the
in-process RLock.  `__exit__` never runs after a failed `__enter__`, so
the owner record and the physical lock file survived.  The next
same-thread operation on that job then read `_lock_owners[job_id]`, saw
its own thread id, classified itself as NESTED and skipped
acquire/refresh/validate entirely — the gate that had just rejected the
durable truth was bypassed on the very next call.  Because
`DurableJsonCatalog.refresh()` adopts a newly discovered fragment into its
cache BEFORE `_validate_job_chain` runs, the forged head was already in
the cache, and the public reads (`get_job` / `list_transitions`) read the
catalogs directly — so the corrupt cached state was also readable as
validated runtime truth with no write operation at all.

## 3. Rollback mechanics (§5–§7)

`__enter__` now wraps `_refresh_durable_truth` in its own `try/except
BaseException: self._rollback_outer_entry(); raise`.  The outer
`except BaseException` continues to release the in-process RLock and
re-raise the ORIGINAL exception, so cleanup can never mask the diagnosis:

- `_rollback_outer_entry()` pops `_lock_owners[job_id]` FIRST, then
  releases and removes THIS attempt's physical lock (`_release_file_lock`
  wrapped in `except OSError: pass`).  Both were installed under the
  process lock this thread still holds, so the removal is exact.
- §6: when `_acquire_file_lock` itself fails (a foreign/stale lock file
  already exists), no handle and no owner entry were installed — the
  rollback touches nothing and the foreign lock survives untouched as
  recovery evidence belonging to I08.  Proven by
  `test_foreign_lock_is_never_auto_deleted` (`JobLockHeld`, foreign file
  still present, owner map clean).
- §7: cleanup faults cannot replace the original error —
  `test_cleanup_error_does_not_mask_validation_error` monkeypatches
  `_release_file_lock` to raise `OSError` and asserts the caller still
  sees `JobCatalogCorrupt` while the unreleased lock remains as I08
  evidence and the owner map is clean.

## 4. Measured attack outcomes (§25 A–P)

Every case uses the proven I07R1G/I07R1H attack shape: repository
constructed FIRST, legitimate chain, then a chain-invalid (but
catalog-valid, and where present checkpoint-proof-valid) later event
published externally at its CORRECT hashed physical catalog key.

| Case | Result |
|---|---|
| A — first corrupt operation (`advance_status`) | `JobCatalogCorrupt` |
| B — immediate SAME-THREAD retry, same repo | `JobCatalogCorrupt`; forged head NOT adopted |
| C — validation executes again | instrumented counters: refresh 1→2, validate 1→2; the nested shortcut is never taken |
| D — owner state rolled back | `job_id not in repo._lock_owners` |
| E — owned physical lock rolled back | `_lock_path(job_id).exists() is False` |
| F — second thread after failure | acquires the lock normally, raises `JobCatalogCorrupt` (never `JobLockHeld`) |
| G/H — `_births.refresh` / `_events.refresh` failure | typed `JsonCatalogCorrupt` (the ORIGINAL catalog error), owner + owned lock rolled back, and after the corruption is removed the next call performs a genuine fresh outer entry (refresh counter 2, forward transition succeeds) |
| I — direct `get_job` after corrupt publication | `JobCatalogCorrupt`, no prior write |
| J — direct `list_transitions` after corrupt publication | `JobCatalogCorrupt`, invalid transition never exposed |
| K/L — valid `get_job` / `list_transitions` | green (ACQUIRING head / 8 transitions) |
| M/N — cross-repo valid publication through public reads | refreshed head visible via `get_job`; `list_transitions` grows by exactly 1 |
| O — `create_job` empty path | birth + idempotent re-create + gated public reads green; no lock left behind |
| P — I07R1H intact refreshed control | still adopted on both runtime and restart (adoption proven by the probe's own +1 event) |

Additional guards proven: a missing job through the gated reads is still
`JobUnknown` (not corruption); a read-only probe shows the forged head
PRESENT in the catalog cache when the public read refuses it — cache
state is forensic, never runtime truth (§13); every rejected gate leaves
the durable chain byte-count unchanged (corruption never writes).

## 5. Public read design (§14–§17)

- `get_job(job_id)` = `with self._job_lock(job_id): return
  self._get_job_unlocked(job_id)`; `list_transitions(job_id)` mirrors it
  with `_list_transitions_unlocked`.  The job-lock entry point performs
  the outer refresh + `_validate_job_chain` gate, so public reads cross
  the SAME boundary as writes.
- Internal callers already inside a successfully entered outer lock
  (`advance_status`, `advance_checkpoint`, `create_job`) call the
  unlocked helpers — no recursion, no re-refresh.
- §17 preserved: a successful nested entry (or an internal read inside a
  live outer context) does not re-refresh —
  `test_successful_nested_entry_does_not_refresh_again` and
  `test_one_write_entry_refreshes_once` pin refresh/validate at exactly
  1 per operation.  Failed entries leave no state capable of triggering
  the nested path (§4/§5).

## 6. Load-bearing counterfactual (§21)

Two measurements, both recorded:

1. **§23 ledger structure test counterfactually RED at 940c2509** — the
   test module was executed against the committed 940c2509 ledger blob
   and `test_current_state_table_is_two_columns` failed on the real
   assertion (`assert not malformed` over the parsed Current state rows),
   then passed against the repaired tree.
2. **Rollback disabled** — the atomicity matrix's
   `counterfactual_rollback_disabled` case neutralizes ONLY
   `_NestedFileLock._rollback_outer_entry` (monkeypatched in the evidence
   builder, no production edit) and re-measures the same scenario: the
   first call still raises `JobCatalogCorrupt`, but the owner record and
   physical lock LEAK, the second same-thread call skips validation
   entirely (`validations_after_second == validations_after_first`) and
   ADOPTS the forged head (`second_attempt_adopted_forged_head = true`).
   With the fix restored, both calls raise `JobCatalogCorrupt` with two
   real validation passes.

## 7. Regressions (§26)

- I07R1H: 13 chain-corruption cases + intact control — green; its
  committed matrix regenerates byte-identically through the read-only
  comparator.
- I07R1G: 17 forged-proof cases + intact-proof control — green; committed
  matrix regenerates byte-identically.
- I07R1F: RAW↔MANIFEST persisted-floor cross-config retries — green.
- Two-repository refresh, two-repository sequence serialization, external
  exact checkpoint retry, catalog cache RLock, safe hashed job lock
  paths — all green (107 upstream job/resume/evidence tests re-run in one
  command).

## 8. Ledger structure repair (§22–§24)

The top-level Current checkpoint row at 940c2509 carried the intended
I07R1H cell followed by a duplicated trailing segment beginning
`| — closed V1 schema` (three logical cells).  The row now carries
EXACTLY two cells; the historical text inside the row is unchanged.
`test_current_state_table_is_two_columns` (§23) proves every ordinary row
between the `## Current state` header and the table end is exactly
`Field | Value`, and is counterfactually red on the pre-repair blob (§6
above).  §24 truth at freeze: `Current checkpoint = SENSOR-B4-I07R1I`;
`PASS_SENSOR_B4_I07R1H/G/F/R1/I07…SEALED = OPERATOR_HOLD`;
`DURABLE_RESUME_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`;
`RECOVERY_SCANNER_IMPLEMENTED = FALSE`; `next_checkpoint_authorized =
FALSE`; recommended next SENSOR-B4-I08 RECOVERY / QUARANTINE ONLY AFTER
operator acceptance.  No self-ratification.

## 9. Machine evidence (§27)

- `BLOC_04_I07R1I_FAILED_GATE_ATOMICITY_MATRIX.json` — 17 cases (all 15
  required + the §21 counterfactual + the I07R1H intact control;
  the corruption-never-writes invariant is pinned by the
  `test_corruption_never_writes` pytest case), all PASS, generated in
  tmp dirs by pure builders and compared byte-for-byte against the
  committed file; normal pytest NEVER writes the evidence tree.
- `BLOC_04_I07R1I_LEDGER_STRUCTURE_MATRIX.json` — 6 cases
  (`current_state_table_two_columns`, `current_checkpoint_exactly_one_row`,
  `no_duplicate_trailing_current_checkpoint_cell`,
  `i07_hold_chain_truthful`, `durable_resume_pending_acceptance`,
  `next_checkpoint_not_authorized`), all PASS.

## 10. Baseline, suites, tooling (§30–§32)

- Fresh exact-head baseline at 940c2509 (clean worktree): **storage 1115
  passed / 0 failed / 3 skipped** (1118 collected); **full 2494 passed /
  0 failed / 4 skipped** (2498 collected).
- Final tree: **storage 1142 passed / 0 failed / 3 skipped** (1145
  collected); **full 2521 passed / 0 failed / 4 skipped** (2525
  collected).  Delta +27, zero failures, no flake.
- Ruff: clean on all changed scope (`jobs.py`,
  `test_job_state_r1i.py`, `test_i07r1i_evidence.py`).
- Mypy, stated precisely (§32): `jobs.py` introduces no new error beyond
  the documented pre-existing `probes/planner.py:79` baseline (1 error,
  that file).  The repository defines no `[tool.mypy]` policy, so the two
  new test modules were checked with the source root configured
  (`MYPYPATH="src;tests/crypto_sensor_fabric/storage"`): both resolve
  fully — zero `import-not-found`, zero arg-type notes — leaving only
  that same single pre-existing baseline.  The evidence module's two
  deliberate rollback-neutralization assignments carry explicit
  `method-assign` suppressions.
- External CI truth (§31): at operator review of 940c2509 the combined
  commit statuses and workflow runs were NONE.  All evidence here is
  local/repository evidence; no CI success is claimed.

## 11. Governance (§29, §33)

Historical I07/I07R1/I07R1F/I07R1G/I07R1H evidence and matrices are NOT
rewritten.  The seven pre-I05-era evidence JSONs showed their documented
CRLF-only churn during pytest (zero content delta via
`--ignore-cr-at-eol`) and were restored before commit, per §29.  Network
= 0; provider source unchanged; no I08 code, no recovery scanner, no
quota, no DuckDB/Postgres, no harness extraction, no module split, no
typed event-model refactor; research NOT resumed.

**STOP GATE honored:** after I07R1I the chain STOPS — I08 (recovery /
quarantine) NOT started; evidence returned to the operator.
