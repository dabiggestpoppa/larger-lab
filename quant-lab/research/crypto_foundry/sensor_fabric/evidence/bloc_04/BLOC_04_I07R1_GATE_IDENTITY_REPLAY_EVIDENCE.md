# SENSOR-B4-I07R1 — GATE IDENTITY REPLAY SEAL — EVIDENCE

**Checkpoint:** SENSOR-B4-I07R1 (Sealed Checkpoint API + Job/Evidence Identity + Restart Replay + Safe Coordination)
**Proposed verdict:** `PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED`
**Branch:** `agent/crypto-sensor-fabric-build`
**Repo:** dabiggestpoppa/larger-lab
**Operator review state at start:** `HOLD_PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED_PENDING_I07R1_GATE_IDENTITY_REPLAY_SEAL`

---

## 1. SHAs

| Item | Value |
|---|---|
| Mandatory starting SHA | `42cdfe09018c1edff5ed89ffab294b4f1e5940e9` (SENSOR-B4-I07C) |
| Verified at session start | exact — branch `agent/crypto-sensor-fabric-build`, clean tree |
| Required lineage | `b5c8edfe` I06R1-RATIFY → `37a54678` I07A → `00a47ccd` I07B → `42cdfe09` I07C ✔ |
| I07R1 commit chain | `cbb93b15` I07R1A/B/C/D → `<this commit>` I07R1E |
| Ending SHA | see the I07R1E commit at the ledger tail |

No reset, no rebase, no force push at any point.

## 2. Historical evidence — untouched

`BLOC_04_I07_JOB_STATE_MATRIX.json`, `BLOC_04_I07_RESUME_COUPLING_MATRIX.json`,
`BLOC_04_I07_JOB_RESUME_EVIDENCE.md` were NOT rewritten.  `git diff 42cdfe09..HEAD`
on those three files is empty; the I07R1 evidence (4 matrices + this file) is new
and chronological.  The I07 evidence comparison tests still pass byte-exact at
HEAD (read-only governance, §42).

## 3. Operator findings → seams closed (A-H)

| Seam | Closure |
|---|---|
| A — `advance_status` exposes resume/anchor fields + `_via_checkpoint_gate` | Public signature is now exactly `(job_id, *, to_status, reason, evidence_ref, expected_from)`; the gate flag parameter no longer exists; `_append_checkpoint_event` is the only checkpoint entry and receives already-proven, fully validated state (§3/§4). |
| B — checkpoint proof not bound to the exact job | `advance_checkpoint` resolves the durable acquisition and requires `provider_id`, `sensor_family`, `request_fingerprint` to equal the job's birth identity; mismatch → `JobResumeGateError` (§7). |
| C — manifest proof not bound to the acquisition/source | At the MANIFEST_COMMITTED floor the manifest must exist durably, carry the batch blob in `blob_refs`, and bind exactly on provider/venue/sensor_family/native_instrument/source_granularity to the proven acquisition (§10). |
| D — RAW floor can store an unproven manifest anchor | `min_durable_status == RAW_COMMITTED` + `manifest_id is not None` → typed rejection; the valid RAW form persists `last_manifest_id=None` and the exact acquisition/blob anchors; no `pm-not-required` dummy strings (§12). |
| E — `last_committed_blob_sha256` not sealed to the proven batch | The anchor is the blob SHA returned by the proof routine itself — the exact acquisition's blob, physically verified before advancement (§13). |
| F — restart validation weaker than the write path | ONE pure `validate_transition(current, target, reason, *, checkpoint)` graph drives BOTH the write path and restart replay; forward skips, ungated checkpoints, bad retry edges and reason-less failure events are corruption on replay (§20-§22). |
| G — raw `job_id` becomes a lock pathname | Physical lock key is `sha256(utf8(job_id)).hexdigest() + ".lock"` (full 64 lowercase hex); traversal/drive/Unicode/long IDs cannot escape the locks root (§28/§29). |
| H — stale `DurableJsonCatalog` caches under long-lived repositories | `DurableJsonCatalog.refresh()` (validated read-only reload: re-parse + physical-key binding, adopt new, divergent/vanished → `JsonCatalogCorrupt`) runs on OUTERMOST per-job file-lock acquisition, BEFORE any state read (§30-§32). |

## 4. Public API before/after

Before (I07): `advance_status(job_id, *, to_status, reason, evidence_ref, expected_from, resume_token=None, last_committed_acquisition_id=None, last_committed_blob_sha256=None, last_manifest_id=None, _via_checkpoint_gate=False)`.

After (I07R1): `advance_status(job_id, *, to_status, reason=None, evidence_ref=None, expected_from=None)` — callers can no longer write `resume_token` or any anchor through the ordinary path, and no caller-settable flag can authorize `CHECKPOINT_ADVANCED` (the planted-attribute attack is a typed conflict).  Every ordinary transition PRESERVES `resume_token`, `last_committed_acquisition_id`, `last_committed_blob_sha256`, `last_manifest_id` exactly (§5); resulting states are round-tripped through full pydantic validation before durability — never a bare `model_copy` (§6).

## 5. Identity and floor contracts

- **Job ↔ acquisition (§7):** provider + sensor_family + request_fingerprint must match the job's birth record; cross-job same-blob and wrong-source evidence are rejected (`BLOC_04_I07R1_CHECKPOINT_IDENTITY_MATRIX.json` cases `provider_mismatch`, `sensor_mismatch`, `request_fingerprint_mismatch`, `cross_job_same_blob`).
- **Usable provenance (§8):** the authoritative frozen predicate `is_usable_manifest_provenance` (I04R2 §5/§13, `storage/catalog.py`) gates advancement — NO duplicated eligibility logic; a forensic failed acquisition stays durable T0A history and can never move the cursor (`forensic_acquisition_rejected`).
- **Manifest ↔ acquisition (§10):** exact provider/venue/sensor_family/native_instrument/source_granularity binding plus blob membership (`manifest_exact`, `manifest_{provider,venue,sensor,instrument,granularity}_mismatch`).
- **RAW_COMMITTED floor (§12):** `manifest_id=None` is the only valid form; contradictory anchors are rejected pre-commit; anchors = exact acquisition_id + exact blob SHA; `last_manifest_id=None` survives restart (`raw_floor_no_manifest`, §14 test `test_raw_floor_survives_restart`).
- **MANIFEST_COMMITTED floor (§13):** `manifest_id` mandatory; the exact proven manifest is persisted; all anchors describe the same batch (`manifest_floor_required`, `manifest_exact`).

## 6. Checkpoint proof schema (V1, closed)

Every `CHECKPOINT_ADVANCED` event record (repository-internal JSON envelope — the frozen `StorageJobTransition` model is untouched, §15) carries:

```json
"checkpoint_proof": {
  "proof_version": 1,
  "minimum_durable_status": "MANIFEST_COMMITTED" | "RAW_COMMITTED",
  "acquisition_id": "<durable acquisition id>",
  "blob_sha256": "<64-hex exact proven blob>",
  "manifest_id": "<manifest id>" | null
}
```

Replay rules (§16-§18, §25): proof_version is closed at 1 (unknown → `JobCatalogCorrupt`); checkpoint events without proof and ordinary events with proof are corruption; proof anchors must equal the resulting state's anchors exactly; historical checkpoints are re-proved against durable truth under the floor PERSISTED IN THE PROOF — the constructor's current `min_durable_status` governs only NEW checkpoints (§19).  A RAW-floor checkpoint persisting a manifest anchor is corruption; a MANIFEST-floor checkpoint without a manifest anchor is corruption.

## 7. Restart replay design (§20-§27)

One pure validator (`validate_transition`) is used by both the writer and `_validate_cross_constraints`, so a persisted event must pass the exact graph that would have authorized it.  Replay additionally enforces: birth identity (job_id/provider/sensor/fingerprint) immutable through every event (§23); ordinary events preserve all four pointers exactly (§24); canonical event identity `{job_id}:{sequence:06d}` bound across filename (via catalog physical-key binding), top-level logical id and `transition.transition_id` — coordinated mutation is rejected (§26); `resulting_state.updated_at == transition.transitioned_at` (§27); per-job sequence contiguity, chain linkage and chronology.  13/13 replay-matrix tamper cases fail closed (`BLOC_04_I07R1_RESTART_REPLAY_MATRIX.json`).

## 8. Coordination (§28-§36)

- **Lock key:** `locks/<sha256(utf8(job_id))>.lock` — traversal (`../escape`, `../../outside`, `C:\temp\x`, `/a/b`, `a\b`), Unicode (`π shifted 🚀`, `中文 job`), 500-char IDs and distinct-ID collisions all safe (`BLOC_04_I07R1_COORDINATION_MATRIX.json`).
- **Refresh:** `DurableJsonCatalog.refresh()` re-scans committed fragments through the existing corruption validator (parse + physical-key binding), adopts newly committed records, and fails closed on divergence or vanished committed truth.  It runs once, at OUTERMOST per-job file-lock acquisition, before any read; nested re-entrant entries reuse the fresh view (§32).
- **Two-repository proof:** repo B constructed before any event observes A's writes and advances with a CAS `expected_from` that only a refreshed view can satisfy (`two_repo_refresh`); racing one transition commits exactly one event with no chain fork (`two_repo_sequence`); B's exact retry of A's committed checkpoint refreshes, re-proves durable batch truth under the persisted floor, and adopts idempotently with exactly one gate event (`external_checkpoint_retry`).  Lost-race adoption now reads disk truth ONLY through the catalog's validated refresh path — the raw `json.loads` bypass of `_parse_fragment` is gone (§36).

## 9. Baseline correction (§37) and fresh baseline

The historical I07 evidence reported its baseline as "storage 939 / full 2318" —
those are the pre-I06R1 (I06) counts; I07 actually started after the accepted
I06R1 state.  The historical I07 evidence files remain untouched; this
correction is recorded chronologically here.

Fresh baseline measured at the exact starting SHA `42cdfe09` before any I07R1
change (authoritative per §37):

| Suite | Collected | Passed | Failed | Skipped |
|---|---|---|---|---|
| storage (`tests/crypto_sensor_fabric/storage`) | 1003 | 1000 | 0 | 3 |
| full (`tests/crypto_sensor_fabric`) | 2322 | 2318 | 0 | 4 |

## 10. Final counts

| Suite | Collected | Passed | Failed | Skipped |
|---|---|---|---|---|
| storage (final) | 1059 | 1056 | 0 | 3 |
| full (final) | 2444 | 2440 | 0 | 4 |

Final passing count ≥ fresh baseline (+56 storage, +122 full), zero failures.

## 11. Static analysis

- **ruff:** clean on the changed scope (`storage/jobs.py`, `storage/json_catalog.py`, `tests/.../test_job_state.py`, `test_job_state_adversarial.py`, `test_job_state_r1.py`, `test_i07_evidence.py`, `test_i07r1_evidence.py`).
- **mypy:** clean on the changed scope; the only remaining project error is the documented pre-existing `probes/planner.py:79` baseline (last touched SENSOR-B2-I02, outside Bloc 4).

## 12. Prohibitions honored

`network = 0` (no sockets in changed scope; no live provider calls).  Provider
source unchanged (diff scope = `storage/jobs.py`, `storage/json_catalog.py`,
test files, evidence files only).  No I08 implementation: no recovery scanner,
no orphan reconciliation, no stale-lock auto-deletion, no quarantine movement;
`JobLockHeld` still names I08 as the recovery owner.  No quota, no DuckDB, no
Postgres, no RawEvidenceQuery, no Bloc-3 integration, no backfill, no live
recorder, no Bloc 5.  Research NOT resumed.  I07R1 evidence tests generate to
memory/tmp_path and compare against committed bytes; normal pytest never writes
the committed evidence tree; the evidence tree is git-clean after the final
suites (§42).

## 13. Proposed ledger state

- `PASS_SENSOR_B4_I07R1_GATE_IDENTITY_REPLAY_SEALED` — PROPOSED, awaiting operator acceptance
- `PASS_SENSOR_B4_I07_DURABLE_JOB_STATE_RESUME_SEALED` — PROPOSED for operator acceptance (from OPERATOR_HOLD)
- `G4-04_REVISION_GATE` — IMPLEMENTATION_PASS candidate pending operator review
- `DURABLE_RESUME_IMPLEMENTED = PENDING_OPERATOR_ACCEPTANCE`
- `RECOVERY_SCANNER_IMPLEMENTED = FALSE`
- `next_checkpoint_authorized = FALSE`
- `recommended_next = SENSOR-B4-I08 RECOVERY / QUARANTINE` (ONLY after operator acceptance)

STOP GATE (§47) honored: I08 NOT started.
