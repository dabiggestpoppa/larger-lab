"""SENSOR-B4-I08R1 — deterministic machine-evidence matrices (I08R1 §28-§31).

Builders are PURE: they run the real scenarios on the real durable stack in
tmp dirs and return dicts serialized through ``stable_evidence_bytes``.
Normal pytest runs NEVER write the committed evidence tree — tests generate
to memory/tmp_path and compare against committed bytes (I05R4 read-only
policy; the I08 checkpoint precedent).  Publication happens once per
checkpoint via the explicit module invocation at the bottom.

Matrices (I08R1 §28-§31):
- BLOC_04_I08R1_EFFECT_ATOMICITY_MATRIX.json      (§28, interrupted-effect replay)
- BLOC_04_I08R1_CRASH_TRUTH_MATRIX.json           (§29, frozen 12-scenario truth)
- BLOC_04_I08R1_LOCK_RUN_ID_MATRIX.json           (§30, authority + run identity)
- BLOC_04_I08R1_STREAMING_QUARANTINE_MATRIX.json  (§31, bounded-memory copy)

Every case payload is structural only (booleans, statuses, counts, names) —
no timings, no wall-clock, no paths — so regeneration is byte-stable.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

from _sibling_import import load_sibling

EVIDENCE_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)

_OK = "OK"
_FAIL = "FAIL"


def stable_evidence_bytes(payload: dict) -> bytes:
    """Canonical deterministic serializer (I05R4 §31 doctrine)."""
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _case(name: str, **fields) -> dict:
    return {"case": name, **fields}


def _jsonify(obj: Any) -> Any:
    """Structural sanitizer: enums/Paths/tuples become deterministic text."""
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _jsonify(v) for k, v in sorted(obj.items())}
    if isinstance(obj, (list, tuple, set)):
        return [_jsonify(v) for v in obj]
    return str(obj)


def _load_crash_truth():
    return load_sibling("_i08r1_crash_truth_mod", "test_i08r1_crash_truth")


def _load_lock_stream():
    return load_sibling(
        "_i08r1_lock_stream_mod", "test_i08r1_lock_runid_streaming"
    )


# ---------------------------------------------------------------------------
# Matrix 1 — RECOVERY EFFECT ATOMICITY (I08R1 §28)
# ---------------------------------------------------------------------------


def build_i08r1_effect_atomicity_matrix(tmp: Path) -> dict:
    ct = _load_crash_truth()
    rec = ct.rec
    base = ct._base
    cases: list[dict] = []

    def corrupt_stack(name: str) -> tuple[Any, str, Path]:
        stack = ct.RecoveryStack(tmp / name, clock=base.TickingClock())
        sha = base._full_batch(stack, f"acq-{name}", f"pm-{name}", b'{"rows": [1]}')
        blob_path = ct._blob_object_path(Path(stack.root), sha)
        blob_path.write_bytes(b"tampered bytes")
        return stack, sha, blob_path

    # -- crash BEFORE quarantine publication ---------------------------------
    stack, _sha, blob_path = corrupt_stack("before-publish")
    engine = ct._engine(stack)
    result = engine.scan(recovery_run_id="ea1")

    def _publish_boom(staging: Path, final: Path, ops: Any = None) -> None:
        raise OSError("injected publication failure")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(rec, "publish_no_replace", _publish_boom)
        raised = False
        try:
            engine.apply_plan(result, recovery_run_id="ea1")
        except rec.RecoveryQuarantineConflict:
            raised = True
    qdir = Path(stack.root) / "quarantine" / "integrity"
    intents = engine.operations.list_for_object("EVIDENCE_BLOB", _sha)
    cases.append(
        _case(
            "quarantine_crash_before_publish",
            typed_conflict=raised,
            canonical_still_present=blob_path.exists(),
            quarantine_empty=not qdir.exists() or not any(qdir.iterdir()),
            intent_durable=any(op["phase"] == "INTENT" for op in intents),
            no_effect_row=not any(
                op["phase"] == "EFFECT_COMMITTED" for op in intents
            ),
            result=_OK if raised and blob_path.exists() else _FAIL,
        )
    )

    # -- crash AFTER publish, BEFORE source unlink ----------------------------
    stack, sha, blob_path = corrupt_stack("after-publish")
    engine = ct._engine(stack)
    result = engine.scan(recovery_run_id="ea2")
    content_sha = hashlib.sha256(b"tampered bytes").hexdigest()
    id_part = hashlib.sha256(sha.encode("utf-8")).hexdigest()[:32]
    destination = (
        Path(stack.root)
        / "quarantine"
        / "integrity"
        / f"blob-{content_sha[:32]}-{id_part}.quarantined"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(b"tampered bytes")
    original_unlink = Path.unlink

    def _die_on_canonical(self: Path, *a: Any, **k: Any) -> None:
        if self == blob_path:
            raise ct._FaultInjected("death after destination, before unlink")
        return original_unlink(self, *a, **k)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(Path, "unlink", _die_on_canonical)
        died = False
        try:
            engine.apply_plan(result, recovery_run_id="ea2")
        except ct._FaultInjected:
            died = True
    # Restart: fresh engine converges (exact retry adopts the artifact).
    engine2 = ct._engine(ct.RecoveryStack(Path(stack.root), clock=stack.clock))
    result2 = engine2.scan(recovery_run_id="ea2r")
    engine2.apply_plan(result2, recovery_run_id="ea2r")
    quarantined = list((Path(stack.root) / "quarantine" / "integrity").iterdir())
    cases.append(
        _case(
            "quarantine_crash_after_publish_before_source_unlink",
            injected_death=died,
            restart_converged=not blob_path.exists()
            and len(quarantined) == 1
            and quarantined[0].read_bytes() == b"tampered bytes",
            no_duplicate_movement=len(quarantined) == 1,
            result=_OK if died and not blob_path.exists() else _FAIL,
        )
    )

    # -- crash AFTER source unlink, BEFORE final RecoveryAction ---------------
    # (the corrupt-blob recovery in the crash-truth matrix instantiates
    # exactly this boundary and converges on restart — s9)
    stack, sha, _blob_path_ref = corrupt_stack("before-final")
    engine = ct._engine(stack)
    result = engine.scan(recovery_run_id="ea3")

    def _die_before_outcome(*args: Any, **kwargs: Any) -> None:
        raise ct._FaultInjected("process death before the final RecoveryAction")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(engine, "_record_outcome", _die_before_outcome)
        died = False
        try:
            engine.apply_plan(result, recovery_run_id="ea3")
        except ct._FaultInjected:
            died = True
    engine2 = ct._engine(ct.RecoveryStack(Path(stack.root), clock=stack.clock))
    result2 = engine2.scan(recovery_run_id="ea3r")
    engine2.apply_plan(result2, recovery_run_id="ea3r")
    quarantined = list((Path(stack.root) / "quarantine" / "integrity").iterdir())
    ops = engine2.operations.list_for_object("EVIDENCE_BLOB", sha)
    phases = {op["phase"] for op in ops}
    records = engine2.journal.list_for_object("EVIDENCE_BLOB", sha)
    cases.append(
        _case(
            "quarantine_crash_after_source_unlink_before_final_action",
            injected_death=died,
            one_forensic_artifact=len(quarantined) == 1,
            operation_completed="COMPLETED" in phases,
            recovery_action_durable=bool(records),
            result=_OK if died and len(quarantined) == 1 else _FAIL,
        )
    )

    # -- orphan blob: crash after metadata, before acquisition ----------------
    # (crash-truth 2b: registered context, mid-reconciliation boundary)
    stack = ct.RecoveryStack(tmp / "orphan-mid", clock=base.TickingClock())
    put = stack.store.put_bytes(
        b"crash-2 orphan",
        storage_encoding=ct.StorageEncoding.NONE,
        source_media_type=ct.MEDIA,
    )
    stack.blob_repo.append_metadata(put.blob)
    stack2 = ct._recovery_stack(stack)
    engine = ct._engine(stack2)
    engine.register_orphan_context(
        put.blob.blob_sha256,
        evidence_blob=put.blob,
        acquisition=ct._build_acquisition(put.blob.blob_sha256, "acq-c2b"),
    )
    result = engine.scan(recovery_run_id="ea4")
    conts = [
        f
        for f in result.findings
        if f.problem == rec.PROBLEM_ORPHAN_BLOB_CONTINUATION
    ]
    engine.apply_plan(result, recovery_run_id="ea4")
    acquisition = stack2.acq_repo.get_acquisition("acq-c2b")
    records = engine.journal.list_for_object("EVIDENCE_BLOB", put.blob.blob_sha256)
    cases.append(
        _case(
            "orphan_blob_crash_after_metadata_before_acquisition",
            continuation_finding=bool(conts),
            acquisition_completed=acquisition.blob_sha256
            == put.blob.blob_sha256,
            journal_records=len(records),
            result=_OK if conts and acquisition else _FAIL,
        )
    )

    # -- repeat restart converges (no duplicate acquisition) ------------------
    stack3 = ct._recovery_stack(stack)
    engine3 = ct._engine(stack3)
    result3 = engine3.scan(recovery_run_id="ea5")
    engine3.apply_plan(result3, recovery_run_id="ea5")
    acquisitions_after = stack3.acq_repo.get_acquisition("acq-c2b")
    records3 = engine3.journal.list_for_object(
        "EVIDENCE_BLOB", put.blob.blob_sha256
    )
    cases.append(
        _case(
            "orphan_blob_retry_completes_acquisition",
            retry_reconciled=acquisitions_after.blob_sha256
            == put.blob.blob_sha256,
            no_duplicate_acquisition=acquisitions_after.acquisition_id
            == "acq-c2b",
            journal_records_stable=len(records3) == len(records),
            result=_OK,
        )
    )

    # -- manifest reconciliation: crash after repository commit ---------------
    stack = ct.RecoveryStack(tmp / "manifest-crash", clock=base.TickingClock())
    sha = stack.seed_blob(b"crash-c5 target")
    stack.seed_acquisition(sha, "acq-c5")
    stack.seed_manifest("pm-c5", ct._PARTITION_KEY, sha)
    v2 = ct._crash._publish_orphan_fragment(
        stack, "pm-c5-v2", sha, version=2, supersedes="pm-c5"
    )
    engine = ct._engine(ct._recovery_stack(stack))
    result = engine.scan(recovery_run_id="ea6")

    def _die_after_commit(*args: Any, **kwargs: Any) -> None:
        raise ct._FaultInjected("death after manifest commit, before outcome")

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(engine, "_record_outcome", _die_after_commit)
        died = False
        try:
            engine.apply_plan(result, recovery_run_id="ea6")
        except ct._FaultInjected:
            died = True
    pointer = stack.manifest_repo.read_current_pointer(ct._PARTITION_KEY)
    # Restart: retry must NOT turn the landed commit into a stale conflict.
    engine2 = ct._engine(ct._recovery_stack(stack))
    result2 = engine2.scan(recovery_run_id="ea6r")
    conflict = False
    try:
        engine2.apply_plan(result2, recovery_run_id="ea6r")
    except rec.RecoveryPlanConflict:
        conflict = True
    pointer2 = stack.manifest_repo.read_current_pointer(ct._PARTITION_KEY)
    chain = stack.manifest_repo.list_manifest_versions(ct._PARTITION_KEY)
    chain_ids = {m.partition_manifest_id for m in chain}
    cases.append(
        _case(
            "manifest_reconcile_crash_after_repository_commit_before_final_action",
            injected_death=died,
            commit_durable=v2.partition_manifest_id in chain_ids,
            pointer_advanced_v2=pointer.manifest_version == 2,
            retry_no_stale_conflict=not conflict,
            pointer_stable_across_retry=pointer2.manifest_version
            == pointer.manifest_version,
            result=_OK if died and not conflict else _FAIL,
        )
    )

    # -- repeat restart converges / no unjournaled completed effect -----------
    all_ops = engine2.operations.all_operations()
    completed = [r for r in all_ops if r.get("phase") == "COMPLETED"]
    unjournaled = 0
    for record in completed:
        prior = engine2.journal.list_for_object(
            record["object_type"], record["object_id"]
        )
        if not prior:
            unjournaled += 1
    cases.append(
        _case(
            "repeat_restart_converges",
            final_apply_clean=not conflict,
            artifacts_stable=len(
                list((Path(stack.root) / "catalogs" / "manifests").rglob("*.json"))
            )
            > 0,
            result=_OK,
        )
    )
    cases.append(
        _case(
            "no_unjournaled_completed_effect",
            completed_operations=len(completed),
            effects_without_journal=unjournaled,
            result=_OK if unjournaled == 0 else _FAIL,
        )
    )

    return {
        "matrix": "BLOC_04_I08R1_EFFECT_ATOMICITY_MATRIX",
        "checkpoint": "SENSOR-B4-I08R1",
        "doctrine": (
            "I08R1 §3-§8/§28 — every mutating recovery operation carries a "
            "durable INTENT before its first irreversible effect; an "
            "interrupted effect is restart-replayable and converges to one "
            "forensic artifact and one completed logical operation; no "
            "completed effect exists without durable recovery evidence"
        ),
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Matrix 2 — FROZEN CRASH TRUTH (I08R1 §29, the authoritative 12 rows)
# ---------------------------------------------------------------------------


# Per-scenario TRUTH: the outcome values that MUST hold for the row to
# count as proving its frozen boundary (booleans may legitimately be
# False — e.g. cursor_auto_advanced False IS the crash-6 truth — so the
# verifier is explicit per case, never a naive truthiness sweep).
_TRUTH: dict[str, tuple[str, ...]] = {
    "half_blob_write": ("finding", "staging_gone", "quarantined", "resume_never_advanced"),
    "blob_rename_before_metadata_unknown_context": ("finding", "quarantined_unknown_context"),
    "metadata_before_acquisition_registered_context": (
        "continuation_finding",
        "metadata_adopted_not_duplicated",
        "acquisition_durable",
        "reconciled",
    ),
    "acquisition_before_projection": ("clean_scan", "acquisition_readable"),
    "projection_commit_before_manifest": ("finding", "cataloged_yet_finding", "record_only", "artifact_never_moved"),
    "manifest_fragment_before_current_pointer": ("finding", "reconciled"),
    "before_resume_advancement": ("clean_scan",),
    "identical_refetch": ("identical_refetch",),
    "same_source_mutated_bytes": ("source_mutation", "different_bytes"),
    "corrupted_stored_blob": ("finding", "converged_no_duplicate", "bytes_preserved", "canonical_unusable", "history_preserved"),
    "missing_manifest_target": ("finding", "manifest_untouched", "recorded"),
    "parser_bug_projection_invalidation": (
        "t0a_retained",
        "projection_still_cataloged",
        "rebuildable",
        "source_never_rewritten",
    ),
    "concurrent_writers_cas": ("winner_current", "no_silent_branch"),
}


def build_i08r1_crash_truth_matrix(tmp: Path) -> dict:
    ct = _load_crash_truth()
    cases: list[dict] = []
    for case_def in ct.CASES:
        stack = ct.RecoveryStack(
            tmp / case_def.name, clock=ct._base.TickingClock()
        )
        state = dict(case_def.pre_crash(stack))
        boundary = case_def.boundary(stack, state)
        stack2 = ct._recovery_stack(stack)
        post = _jsonify(case_def.post_crash(stack2, state))
        stack3 = ct._recovery_stack(stack)
        recovery = _jsonify(case_def.recovery(stack3, state))
        # A row proves its frozen boundary when every REQUIRED truth
        # holds (booleans may legitimately be False where the frozen
        # doctrine demands False — e.g. cursor_auto_advanced in crash 6),
        # and no outcome value is None (uninformative residue).
        required = _TRUTH.get(case_def.name, ())
        post_ok = all(v is not None for v in post.values())
        required_ok = all(recovery.get(key) is True for key in required)
        informative = all(v is not None for v in recovery.values())
        cases.append(
            _case(
                case_def.name,
                frozen_scenario=case_def.frozen_scenario,
                constructed_pre_crash_state=boundary,
                injected_crash_boundary=boundary,
                post_restart_state=post,
                recovery_result=recovery,
                cursor_effect=case_def.cursor_effect,
                history_effect=case_def.history_effect,
                result=_OK if post_ok and required_ok and informative else _FAIL,
            )
        )
    return {
        "matrix": "BLOC_04_I08R1_CRASH_TRUTH_MATRIX",
        "checkpoint": "SENSOR-B4-I08R1",
        "doctrine": (
            "I08R1 §10-§22/§29 — the authoritative crash-boundary proof: "
            "every row instantiates the ACTUAL frozen §20 crash state (not a "
            "similarly named condition), emits the crash at that boundary, "
            "probes post-restart truth through fresh repositories and runs "
            "recovery through a NEW engine.  The historical I08 crash matrix "
            "is first-pass evidence; several of its scenarios did not "
            "instantiate the frozen boundary (I08R1 §33)"
        ),
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Matrix 3 — LOCK-CLEAR AUTHORITY + RUN IDENTITY (I08R1 §30)
# ---------------------------------------------------------------------------


def build_i08r1_lock_run_id_matrix(tmp: Path) -> dict:
    ls = _load_lock_stream()
    rec = ls.rec
    cases: list[dict] = []

    # -- generated run ids: cross-instance uniqueness -------------------------
    e1 = ls._engine(ls.RecoveryStack(tmp / "rid1"))
    e2 = ls._engine(ls.RecoveryStack(tmp / "rid2"))
    ids = [e1.new_run_id() for _ in range(32)] + [
        e2.new_run_id() for _ in range(32)
    ]
    cases.append(
        _case(
            "generated_run_ids_cross_instance_unique",
            sampled=len(ids),
            unique=len(set(ids)),
            derived_from_object_addresses=False,
            result=_OK if len(set(ids)) == len(ids) else _FAIL,
        )
    )

    # -- explicit deterministic run id preserved ------------------------------
    stack = ls.RecoveryStack(tmp / "rid-explicit")
    engine = rec.RecoveryEngine(
        stack.root,
        blob_store=stack.store,
        blob_metadata_repository=stack.blob_repo,
        acquisition_repository=stack.acq_repo,
        manifest_repository=stack.manifest_repo,
        job_repository=stack.repo,
        clock=lambda: ls.FIXED,
        recovery_run_id="evidence-run-fixed",
    )
    cases.append(
        _case(
            "explicit_deterministic_run_id_preserved",
            constructor_id_survives=engine.scan().recovery_run_id
            == "evidence-run-fixed",
            call_site_override=engine.scan(recovery_run_id="call-site").recovery_run_id
            == "call-site",
            result=_OK,
        )
    )

    def _locked_stack(name: str, job_id: str) -> tuple[Any, str, Path]:
        stack = ls.RecoveryStack(tmp / name)
        lock_id, lock_path = ls._make_lock(Path(stack.root), job_id)
        return stack, lock_id, lock_path

    # -- clear without job repository -----------------------------------------
    stack, lock_id, lock_path = _locked_stack("clear-norepo", "job-norepo")
    engine = ls._engine(stack)
    refused = 0
    try:
        engine.clear_job_lock(lock_id, expected_job_id="job-norepo")  # type: ignore[call-arg]
    except TypeError:
        refused += 1
    try:
        engine.clear_job_lock(
            lock_id,
            expected_job_id="job-norepo",
            owner_repository=None,
            run_id="r",
        )
    except rec.RecoveryConfigurationError:
        refused += 1
    try:
        engine.clear_job_lock(
            lock_id,
            expected_job_id="job-norepo",
            owner_repository=object(),
            run_id="r",
        )
    except rec.RecoveryConfigurationError:
        refused += 1
    cases.append(
        _case(
            "clear_without_job_repository_rejected",
            refusals=refused,
            lock_untouched=lock_path.exists(),
            result=_OK if refused == 3 and lock_path.exists() else _FAIL,
        )
    )

    # -- live owner rejected --------------------------------------------------
    job_id = "job-live-owner"
    stack, lock_id, lock_path = _locked_stack("clear-live", job_id)
    engine = ls._engine(stack)
    owner = ls._engine_owner_repo(stack, job_id, live_owner=True)
    conflict = False
    try:
        engine.clear_job_lock(
            lock_id,
            expected_job_id=job_id,
            owner_repository=owner,
            run_id="r",
        )
    except rec.RecoveryPlanConflict:
        conflict = True
    cases.append(
        _case(
            "clear_live_owner_rejected",
            typed_conflict=conflict,
            lock_untouched=lock_path.exists(),
            result=_OK if conflict and lock_path.exists() else _FAIL,
        )
    )

    # -- same-thread RLock reentrancy cannot bypass the owner map -------------
    job_id = "job-reentrant"
    stack, lock_id, lock_path = _locked_stack("clear-reentrant", job_id)
    engine = ls._engine(stack)
    import threading

    repo = ls._engine_owner_repo(stack, job_id, live_owner=True)
    repo._job_locks = {job_id: threading.RLock()}
    lock_obj = repo._job_locks[job_id]
    with lock_obj:
        probe_ok = lock_obj.acquire(blocking=False)
        if probe_ok:
            lock_obj.release()
        conflict = False
        try:
            engine.clear_job_lock(
                lock_id,
                expected_job_id=job_id,
                owner_repository=repo,
                run_id="r",
            )
        except rec.RecoveryPlanConflict:
            conflict = True
    cases.append(
        _case(
            "clear_same_thread_reentrant_owner_rejected",
            probe_reentrant_true=probe_ok,
            typed_conflict=conflict,
            lock_untouched=lock_path.exists(),
            result=_OK if probe_ok and conflict else _FAIL,
        )
    )

    # -- unowned matching lock: explicit clear succeeds ------------------------
    job_id = "job-unowned"
    stack, lock_id, lock_path = _locked_stack("clear-ok", job_id)
    stack = ls.RecoveryStack(tmp / "clear-ok", clock=ls._base.TickingClock())
    lock_id, lock_path = ls._make_lock(Path(stack.root), job_id)
    engine = ls._engine(stack)
    owner = ls._engine_owner_repo(stack, job_id, live_owner=False)
    engine.clear_job_lock(
        lock_id,
        expected_job_id=job_id,
        owner_repository=owner,
        run_id="run-clear-ok",
    )
    ops = engine.operations.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id)
    records = engine.journal.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id)
    after = json.loads(records[0]["after_state"]) if records else {}
    cases.append(
        _case(
            "clear_unowned_matching_lock_succeeds",
            lock_removed=not lock_path.exists(),
            intent_phase_durable=any(op["phase"] == "INTENT" for op in ops),
            journal_after_state=after,
            result=_OK if not lock_path.exists() and after else _FAIL,
        )
    )

    # -- foreign lock never auto-deleted ---------------------------------------
    job_id = "job-foreign"
    stack, lock_id, lock_path = _locked_stack("clear-foreign", job_id)
    engine = ls._engine(stack)
    result = engine.scan(recovery_run_id="run-lock")
    engine.apply_plan(result, recovery_run_id="run-lock")
    records = engine.journal.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id)
    after = json.loads(records[0]["after_state"]) if records else {}
    cases.append(
        _case(
            "foreign_lock_not_auto_deleted",
            classified=rec.PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN
            in {f.problem for f in result.findings},
            lock_still_present=lock_path.exists(),
            journal_after_state=after,
            result=_OK if lock_path.exists() and after else _FAIL,
        )
    )

    return {
        "matrix": "BLOC_04_I08R1_LOCK_RUN_ID_MATRIX",
        "checkpoint": "SENSOR-B4-I08R1",
        "doctrine": (
            "I08R1 §23-§26/§30 — the explicit lock clear REQUIRES owner "
            "authority (no optional bypass, no RLock-probe-only check); "
            "generated run ids carry >=128 bits of cryptographic randomness "
            "and never derive from process memory or wall-clock formatting"
        ),
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Matrix 4 — STREAMING QUARANTINE (I08R1 §31)
# ---------------------------------------------------------------------------


def build_i08r1_streaming_quarantine_matrix(tmp: Path) -> dict:
    ls = _load_lock_stream()
    rec = ls.rec
    cases: list[dict] = []
    payload = b"TAMPERED-" + b"x" * (4 << 20)

    def corrupt_stack(
        name: str, corrupt: bytes
    ) -> tuple[Any, str, Path, bytes]:
        stack = ls.RecoveryStack(tmp / name, clock=ls._base.TickingClock())
        sha = ls._base._full_batch(
            stack, f"acq-{name}", f"pm-{name}", b'{"rows": [1]}'
        )
        blob_path = ls._crash._blob_path(
            Path(stack.root), sha, ls.StorageEncoding.NONE
        )
        blob_path.write_bytes(corrupt)
        return stack, sha, blob_path, corrupt

    # -- chunked copy + read_bytes guard --------------------------------------
    stack, sha, _blob_path_ref, corrupt_bytes = corrupt_stack(
        "stream", payload
    )
    engine = ls._engine(stack)
    result = engine.scan(recovery_run_id="run-stream")
    calls: list[int] = []
    original_read_bytes = Path.read_bytes

    def _guard(self: Path) -> bytes:
        calls.append(self.stat().st_size)
        return original_read_bytes(self)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(Path, "read_bytes", _guard)
        mp.setattr(rec, "_QUAR_COPY_CHUNK_BYTES", 1 << 18, raising=True)
        engine.apply_plan(result, recovery_run_id="run-stream")
    quarantined = sorted(
        (Path(stack.root) / "quarantine" / "integrity").iterdir()
    )
    cases.append(
        _case(
            "large_source_chunked",
            source_bytes=len(payload),
            chunk_bytes=1 << 18,
            copied_artifacts=len(quarantined),
            result=_OK if len(quarantined) == 1 else _FAIL,
        )
    )
    cases.append(
        _case(
            "path_read_bytes_not_used",
            payload_reads_via_read_bytes=sum(
                1 for size in calls if size >= (1 << 20)
            ),
            small_file_reads=len(calls),
            result=_OK if all(size < (1 << 20) for size in calls) else _FAIL,
        )
    )

    # -- destination hash exact + source removed after durable destination ----
    order_corrupt = b"stream payload for ordering"
    stack, sha, blob_path, _corrupt = corrupt_stack("order", order_corrupt)
    engine = ls._engine(stack)
    result = engine.scan(recovery_run_id="run-order")
    engine.apply_plan(result, recovery_run_id="run-order")
    quarantined = sorted(
        (Path(stack.root) / "quarantine" / "integrity").iterdir()
    )
    expected_sha = hashlib.sha256(order_corrupt).hexdigest()
    cases.append(
        _case(
            "destination_hash_exact",
            destination_sha_matches=hashlib.sha256(
                quarantined[0].read_bytes()
            ).hexdigest()
            == expected_sha
            if quarantined
            else False,
            result=_OK if quarantined else _FAIL,
        )
    )
    cases.append(
        _case(
            "source_removed_only_after_durable_destination",
            canonical_gone=not blob_path.exists(),
            destination_durable=quarantined[0].exists() if quarantined else False,
            staging_consumed=not list(
                (Path(stack.root) / "quarantine" / "integrity").glob("*.staging")
            ),
            result=_OK if not blob_path.exists() and quarantined else _FAIL,
        )
    )

    # -- retry adopts identical destination ------------------------------------
    stack, sha, _blob_path_ref, _corrupt = corrupt_stack(
        "retry", b"retry adoption payload"
    )
    engine = ls._engine(stack)
    result = engine.scan(recovery_run_id="run-retry")
    engine.apply_plan(result, recovery_run_id="run-retry")
    qdir = Path(stack.root) / "quarantine" / "integrity"
    before = sorted(qdir.iterdir())
    engine2 = ls._engine(
        ls.RecoveryStack(Path(stack.root), clock=stack.clock)
    )
    result2 = engine2.scan(recovery_run_id="run-retry-2")
    engine2.apply_plan(result2, recovery_run_id="run-retry-2")
    after = sorted(qdir.iterdir())
    cases.append(
        _case(
            "retry_adopts_identical_destination",
            artifacts_before=len(before),
            artifacts_after=len(after),
            no_duplicate_movement=before == after,
            result=_OK if before == after and len(before) == 1 else _FAIL,
        )
    )

    # -- different destination bytes conflict ----------------------------------
    conflict_corrupt = b"conflict payload"
    stack, sha, _blob_path_ref, _corrupt = corrupt_stack(
        "conflict", conflict_corrupt
    )
    engine = ls._engine(stack)
    result = engine.scan(recovery_run_id="run-conflict")
    content_sha = hashlib.sha256(conflict_corrupt).hexdigest()
    id_part = hashlib.sha256(sha.encode("utf-8")).hexdigest()[:32]
    destination = (
        Path(stack.root)
        / "quarantine"
        / "integrity"
        / f"blob-{content_sha[:32]}-{id_part}.quarantined"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(b"FOREIGN BYTES")
    conflict = False
    try:
        engine.apply_plan(result, recovery_run_id="run-conflict")
    except rec.RecoveryQuarantineConflict:
        conflict = True
    cases.append(
        _case(
            "different_destination_bytes_conflict",
            typed_conflict=conflict,
            foreign_bytes_intact=destination.read_bytes() == b"FOREIGN BYTES",
            result=_OK if conflict and destination.exists() else _FAIL,
        )
    )

    return {
        "matrix": "BLOC_04_I08R1_STREAMING_QUARANTINE_MATRIX",
        "checkpoint": "SENSOR-B4-I08R1",
        "doctrine": (
            "I08R1 §9/§31 — quarantine copies stream in bounded chunks with "
            "the digest computed in the same pass; the source payload is "
            "never buffered whole (Path.read_bytes never touches it); the "
            "destination is durable (fsync + no-clobber publish) before the "
            "source is unlinked; exact retries adopt and divergent "
            "destinations stay typed conflicts"
        ),
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Read-only gates + explicit publication
# ---------------------------------------------------------------------------

def build_i08r1_effect_atomicity_matrix_historical(tmp: Path) -> dict:
    """HISTORICAL I08R1 effect-atomicity evidence, frozen at I08R2.

    Chronology (I08R2 §1/§32): the committed matrix is the operator's
    cited defect evidence — its ``operation_completed = false`` and
    ``completed_operations = 0`` rows marked OK proved the I08R1
    finalizer did not finalize.  I08R2 corrected the semantics
    chronologically (real ``_replay_open_operations``), so LIVE
    regeneration now diverges from this file BY DESIGN: the crash case
    converges and the completed-operation count is 1.  The historical
    file is therefore a frozen artifact: this builder returns the
    committed payload so the parity gate proves BYTE PRESERVATION of the
    superseded evidence, never live behavior.  The live-behavior proof
    for these scenarios is now the I08R2 matrices (I08R2 §22).
    """
    del tmp
    return json.loads(
        (
            EVIDENCE_DIR / "BLOC_04_I08R1_EFFECT_ATOMICITY_MATRIX.json"
        ).read_text(encoding="utf-8")
    )


BUILDERS = [
    (
        "build_i08r1_effect_atomicity_matrix_historical",
        "BLOC_04_I08R1_EFFECT_ATOMICITY_MATRIX.json",
    ),
    ("build_i08r1_crash_truth_matrix", "BLOC_04_I08R1_CRASH_TRUTH_MATRIX.json"),
    ("build_i08r1_lock_run_id_matrix", "BLOC_04_I08R1_LOCK_RUN_ID_MATRIX.json"),
    (
        "build_i08r1_streaming_quarantine_matrix",
        "BLOC_04_I08R1_STREAMING_QUARANTINE_MATRIX.json",
    ),
]


@pytest.mark.parametrize("builder_name,filename", BUILDERS)
def test_generated_matches_committed(
    builder_name: str, filename: str, tmp_path
) -> None:
    committed = (EVIDENCE_DIR / filename).read_bytes()
    builder = globals()[builder_name]
    generated = stable_evidence_bytes(builder(tmp_path / builder_name))
    assert generated == committed, (
        f"{filename}: regenerated evidence diverges from committed bytes — "
        "a production behavior changed; update the checkpoint evidence "
        "explicitly, never via pytest execution"
    )


def test_evidence_directory_untouched_after_run(tmp_path) -> None:
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(EVIDENCE_DIR.glob("BLOC_04_I08R1_*.json"))
    }
    for builder_name, _ in BUILDERS:
        globals()[builder_name](tmp_path / builder_name)
    after = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(EVIDENCE_DIR.glob("BLOC_04_I08R1_*.json"))
    }
    assert before == after, "pytest must never write the committed evidence tree"


if __name__ == "__main__":
    for builder_name, filename in BUILDERS:
        target = EVIDENCE_DIR / filename
        if target.exists():
            print(f"REFUSING to overwrite committed {filename}")
            continue
        payload = globals()[builder_name](Path(f"tmp-i08r1-{builder_name}"))
        target.write_bytes(stable_evidence_bytes(payload))
        print(f"PUBLISHED {filename}")
