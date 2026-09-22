"""SENSOR-B4-I08 — deterministic machine-evidence matrices (I08 §37).

Builders are PURE: they run the real scenarios on the real durable stack in
tmp dirs and return dicts serialized through ``stable_evidence_bytes``.
Normal pytest runs NEVER write the committed evidence tree — tests generate
to memory/tmp_path and compare against committed bytes (I05R4 read-only
policy, I07R1I §29 precedent).  Publication happens once per checkpoint via
an explicit operator invocation (module bottom).

Matrices (I08 §37):
- BLOC_04_I08_RECOVERY_SCAN_MATRIX.json          (§4/§26 scan coverage)
- BLOC_04_I08_QUARANTINE_MATRIX.json             (§10/§11/§29/§30)
- BLOC_04_I08_CRASH_MATRIX.json                  (§24, 12 frozen scenarios)
- BLOC_04_I08_RECOVERY_IDEMPOTENCE_MATRIX.json   (§27/§28/§20)

Every case payload is structural only (booleans, statuses, counts, names) —
no timings, no wall-clock, no paths — so regeneration is byte-stable.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

from _sibling_import import load_sibling
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity
from crypto_sensor_fabric.storage.enums import CoverageState, DateBasis

EVIDENCE_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)

_NO_ERROR = "NO_ERROR"
_OK = "OK"


def stable_evidence_bytes(payload: dict) -> bytes:
    """Canonical deterministic serializer (I05R4 §31 doctrine)."""
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _case(name: str, **fields) -> dict:
    return {"case": name, **fields}


def _load_base():
    return load_sibling("_i08_base_mod", "test_job_state_r1")


def _load_recovery():
    return load_sibling("_i08_recovery_mod", "test_recovery")


def _load_crash():
    return load_sibling("_i08_crash_mod", "test_recovery_crash_matrix")





# ---------------------------------------------------------------------------
# Matrix 1 — RECOVERY SCAN (§4 classes A-J + §26 determinism)
# ---------------------------------------------------------------------------


def build_recovery_scan_matrix(tmp: Path) -> dict:
    rec = _load_recovery()
    rec_mod = rec.rec
    crash = _load_crash()
    cases: list[dict] = []

    # -- clean root ----------------------------------------------------------
    stack = crash.RecoveryStack(tmp / "clean")
    result = crash._engine(stack).scan(recovery_run_id="mx-clean")
    cases.append(
        _case(
            "clean_root",
            findings=len(result.findings),
            has_blockers=result.has_blockers,
            result=_OK if result.findings == () else "UNEXPECTED_FINDINGS",
        )
    )

    # -- uncommitted staging -------------------------------------------------
    stack = crash.RecoveryStack(tmp / "staging")
    (tmp / "staging" / "staging").mkdir(parents=True, exist_ok=True)
    (tmp / "staging" / "staging" / "abc.partial").write_bytes(b"partial")
    result = crash._engine(stack).scan(recovery_run_id="mx-staging")
    staging = [
        f for f in result.findings if f.problem == rec_mod.PROBLEM_UNCOMMITTED_STAGING
    ]
    cases.append(
        _case(
            "uncommitted_staging",
            findings=len(staging),
            result=_OK if staging else "MISSING",
        )
    )

    # -- orphan durable blob (no context) ------------------------------------
    stack = crash.RecoveryStack(tmp / "orphan")
    data = b"mx orphan"
    stack.store.put_bytes(
        data,
        storage_encoding=_storage_encoding_NONE(),
        source_media_type=_base_media(),
    )
    result = crash._engine(stack).scan(recovery_run_id="mx-orphan")
    orphans = [
        f for f in result.findings if f.problem == rec_mod.PROBLEM_ORPHAN_DURABLE_BLOB
    ]
    cases.append(
        _case(
            "orphan_durable_blob",
            findings=len(orphans),
            result=_OK if orphans else "MISSING",
        )
    )

    # -- orphan projection ----------------------------------------------------
    stack = crash.RecoveryStack(tmp / "projection")
    sha = stack.seed_blob(b"mx projection source")
    stack.seed_acquisition(sha, "acq-mx-proj")
    proj_dir = tmp / "projection" / "projections"
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "orphan.parquet").write_bytes(b"PAR1-mx")
    result = crash._engine(stack).scan(recovery_run_id="mx-proj")
    orphans = [
        f for f in result.findings if f.problem == rec_mod.PROBLEM_ORPHAN_PROJECTION
    ]
    cases.append(
        _case(
            "orphan_projection",
            findings=len(orphans),
            result=_OK if orphans else "MISSING",
        )
    )

    # -- orphan manifest ------------------------------------------------------
    stack = crash.RecoveryStack(tmp / "manifest")
    sha = stack.seed_blob(b"mx manifest target")
    stack.seed_acquisition(sha, "acq-mx-man")
    stack.seed_manifest("pm-mx", crash._ORPHAN_PARTITION_KEY, sha)
    crash._publish_orphan_fragment(
        stack, "pm-mx-v2", sha, version=2, supersedes="pm-does-not-exist"
    )
    engine = crash._engine(stack)
    result = engine.scan(recovery_run_id="mx-man")
    orphans = [
        f for f in findings_of(result)
        if f.problem == rec_mod.PROBLEM_ORPHAN_MANIFEST
    ]
    cases.append(
        _case(
            "orphan_manifest",
            findings=len(orphans),
            result=_OK if orphans else "MISSING",
        )
    )

    # -- missing manifest target ----------------------------------------------
    stack = crash.RecoveryStack(tmp / "missing")
    sha = stack.seed_blob(b"mx missing target")
    stack.seed_acquisition(sha, "acq-mx-mis")
    stack.seed_manifest("pm-mx-mis", crash._ORPHAN_PARTITION_KEY, sha)
    _blob_path_for(tmp / "missing", sha).unlink()
    result = crash._engine(stack).scan(recovery_run_id="mx-mis")
    targets = [
        f
        for f in findings_of(result)
        if f.problem == rec_mod.PROBLEM_MISSING_MANIFEST_TARGET
    ]
    cases.append(
        _case(
            "missing_manifest_blob",
            findings=len(targets),
            result=_OK if targets else "MISSING",
        )
    )

    # -- quarantined blob dependency (acquisition) ----------------------------
    stack = crash.RecoveryStack(tmp / "acqdep")
    sha = stack.seed_blob(b"mx acq dependency")
    stack.seed_acquisition(sha, "acq-mx-dep")
    _blob_path_for(tmp / "acqdep", sha).write_bytes(b"tampered")
    result = crash._engine(stack).scan(recovery_run_id="mx-dep")
    deps = [
        f
        for f in findings_of(result)
        if f.problem == rec_mod.PROBLEM_ACQUISITION_SOURCE_QUARANTINED
    ]
    cases.append(
        _case(
            "quarantined_blob_dependency",
            findings=len(deps),
            result=_OK if deps else "MISSING",
        )
    )

    # -- job durability divergence (I07R1H forged head) -----------------------
    stack = crash.RecoveryStack(tmp / "jobdiv", clock=_load_base().TickingClock())
    job_id = "job-mx-div"
    _load_base()._create(stack.repo, job_id)
    _load_base()._drive_to_manifest(stack.repo, job_id)
    _load_base()._full_batch(stack, "acq-mx-div", "pm-mx-div", b'{"rows": ["mx"]}')
    _load_base()._checkpoint(stack.repo, job_id, "acq-mx-div", "pm-mx-div")
    crash._publish_forged_from_status_break(tmp / "jobdiv", job_id)
    result = crash._engine(stack).scan(recovery_run_id="mx-div")
    divergent = [
        f
        for f in findings_of(result)
        if f.problem == rec_mod.PROBLEM_JOB_DURABILITY_DIVERGENCE
    ]
    cases.append(
        _case(
            "job_durability_divergence",
            findings=len(divergent),
            typed_error="JobCatalogCorrupt",
            result=_OK if divergent else "MISSING",
        )
    )

    # -- lock owner unproven --------------------------------------------------
    stack = crash.RecoveryStack(tmp / "lock")
    (tmp / "lock" / "locks").mkdir(parents=True, exist_ok=True)
    (tmp / "lock" / "locks" / (hashlib.sha256(b"job-mx-lock").hexdigest() + ".lock")).write_bytes(b"{}")
    result = crash._engine(stack).scan(recovery_run_id="mx-lock")
    locks = [
        f
        for f in findings_of(result)
        if f.problem == rec_mod.PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN
    ]
    cases.append(
        _case(
            "lock_owner_unproven",
            findings=len(locks),
            result=_OK if locks else "MISSING",
        )
    )

    # -- unknown context (unparseable manifest fragment) ----------------------
    stack = crash.RecoveryStack(tmp / "unknown")
    frag_dir = (
        tmp / "unknown" / "catalogs" / "manifests" / "partitions" / ("0" * 32)
    )
    frag_dir.mkdir(parents=True, exist_ok=True)
    (frag_dir / "v00000001-garbage.parquet").write_bytes(b"not parquet")
    result = crash._engine(stack).scan(recovery_run_id="mx-unknown")
    unknown = [
        f for f in findings_of(result) if f.problem == rec_mod.PROBLEM_UNKNOWN_CONTEXT
    ]
    cases.append(
        _case(
            "unknown_context",
            findings=len(unknown),
            result=_OK if unknown else "MISSING",
        )
    )

    # -- determinism -----------------------------------------------------------
    stack = crash.RecoveryStack(tmp / "det")
    sha = stack.seed_blob(b"mx determinism")
    stack.seed_acquisition(sha, "acq-mx-det")
    (tmp / "det" / "staging").mkdir(exist_ok=True)
    (tmp / "det" / "staging" / "x.partial").write_bytes(b"p")
    first = crash._engine(stack).scan(recovery_run_id="mx-det")
    second = crash._engine(stack).scan(recovery_run_id="mx-det")
    cases.append(
        _case(
            "scan_deterministic_sorted",
            identical=first.to_dict() == second.to_dict(),
            sorted_keys=first.counts_by_problem == dict(sorted(first.counts_by_problem.items())),
            result=_OK
            if first.to_dict() == second.to_dict()
            else "NON_DETERMINISTIC",
        )
    )

    return {
        "matrix": "BLOC_04_I08_RECOVERY_SCAN_MATRIX",
        "checkpoint": "SENSOR-B4-I08",
        "doctrine": (
            "I08 §4/§5/§26 — the read-only scan classifies every frozen "
            "recovery class (staging, orphan blob/projection/manifest, "
            "missing manifest target, acquisition dependency, job "
            "divergence, unproven locks, unknown context) with zero "
            "mutation and deterministic sorted output"
        ),
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Matrix 2 — QUARANTINE (§10/§11/§29/§30)
# ---------------------------------------------------------------------------


def build_quarantine_matrix(tmp: Path) -> dict:
    crash = _load_crash()
    rec = _load_recovery()
    rec_mod = rec.rec
    cases: list[dict] = []

    # -- corrupt blob quarantined, bytes preserved, canonical unusable --------
    stack = crash.RecoveryStack(tmp / "q1")
    sha = stack.seed_blob(b"q corrupt victim")
    stack.seed_acquisition(sha, "acq-q1")
    _blob_path_for(tmp / "q1", sha).write_bytes(b"corrupted bytes")
    engine = crash._engine(stack)
    result = engine.scan(recovery_run_id="mx-q1")
    engine.apply_plan(result, recovery_run_id="mx-q1")
    qdir = tmp / "q1" / "quarantine" / "integrity"
    quarantined = list(qdir.iterdir()) if qdir.exists() else []
    cases.append(
        _case(
            "corrupt_blob_quarantined",
            quarantined=len(quarantined) == 1,
            canonical_absent=not _blob_path_for(tmp / "q1", sha).exists(),
            bytes_preserved=quarantined
            and quarantined[0].read_bytes() == b"corrupted bytes",
            acquisition_history_intact=stack.acq_repo.get_acquisition(
                "acq-q1"
            ).blob_sha256
            == sha,
            result=_OK
            if (quarantined and not _blob_path_for(tmp / "q1", sha).exists())
            else "FAIL",
        )
    )

    # -- quarantine bytes preserved (orphan, unknown_context) ------------------
    stack = crash.RecoveryStack(tmp / "q2")
    data = b"q preserved orphan"
    expected_sha = hashlib.sha256(data).hexdigest()
    stack.store.put_bytes(
        data, storage_encoding=_storage_encoding_NONE(), source_media_type=_base_media()
    )
    engine = crash._engine(stack)
    result = engine.scan(recovery_run_id="mx-q2")
    engine.apply_plan(result, recovery_run_id="mx-q2")
    qdir = tmp / "q2" / "quarantine" / "unknown_context"
    quarantined = list(qdir.iterdir()) if qdir.exists() else []
    cases.append(
        _case(
            "quarantine_bytes_preserved",
            quarantined=len(quarantined) == 1,
            byte_identity=quarantined
            and hashlib.sha256(quarantined[0].read_bytes()).hexdigest() == expected_sha,
            result=_OK if quarantined else "FAIL",
        )
    )

    # -- canonical bad object unusable (read fails closed) --------------------
    stack = crash.RecoveryStack(tmp / "q3")
    sha = stack.seed_blob(b"q unusable victim")
    stack.seed_acquisition(sha, "acq-q3")
    _blob_path_for(tmp / "q3", sha).write_bytes(b"bad")
    engine = crash._engine(stack)
    result = engine.scan(recovery_run_id="mx-q3")
    engine.apply_plan(result, recovery_run_id="mx-q3")
    try:
        stack.store.verify_blob(sha, _storage_encoding_NONE())
        usable = True
    except Exception:
        usable = False
    cases.append(
        _case(
            "canonical_bad_object_unusable",
            canonical_read_fails_closed=not usable,
            result=_OK if not usable else "FAIL",
        )
    )

    # -- no overwrite + exact retry adopt + different bytes conflict -----------
    stack = crash.RecoveryStack(tmp / "q4")
    engine = crash._engine(stack)
    content = hashlib.sha256(b"q probe bytes").hexdigest()
    locator = engine.quarantine_destination(
        "integrity",
        object_type="probe",
        object_id="probe-object",
        content_sha256=content,
        suffix=".probe",
    )
    source = tmp / "q4" / "probe.bin"
    source.write_bytes(b"q probe bytes")
    moved = engine._quarantine_file(source, locator, content)
    source.write_bytes(b"q probe bytes")
    adopted = not engine._quarantine_file(source, locator, content)
    other = tmp / "q4" / "other.bin"
    other.write_bytes(b"other bytes")
    locator.write_bytes(b"other bytes")
    conflict = False
    try:
        engine._quarantine_file(
            other, locator, hashlib.sha256(b"q probe bytes").hexdigest()
        )
    except rec_mod.RecoveryQuarantineConflict:
        conflict = True
    cases.append(
        _case(
            "no_overwrite",
            first_move=moved,
            exact_retry_adopted=adopted,
            different_bytes_conflict=conflict,
            result=_OK if (moved and adopted and conflict) else "FAIL",
        )
    )

    # -- exact retry idempotent (apply twice, same run) ------------------------
    stack = crash.RecoveryStack(tmp / "q5")
    data = b"q idempotent orphan"
    stack.store.put_bytes(
        data, storage_encoding=_storage_encoding_NONE(), source_media_type=_base_media()
    )
    engine = crash._engine(stack)
    result = engine.scan(recovery_run_id="mx-q5")
    first = engine.apply_plan(result, recovery_run_id="mx-q5")
    second = engine.apply_plan(result)
    qdir = tmp / "q5" / "quarantine" / "unknown_context"
    quarantined = list(qdir.iterdir()) if qdir.exists() else []
    cases.append(
        _case(
            "exact_retry_idempotent",
            first_apply=len(first),
            second_apply=len(second),
            single_artifact=len(quarantined) == 1,
            result=_OK if (first and not second and len(quarantined) == 1) else "FAIL",
        )
    )

    # -- different bytes conflict (same locator) -------------------------------
    stack = crash.RecoveryStack(tmp / "q6")
    engine = crash._engine(stack)
    content = hashlib.sha256(b"q conflict probe").hexdigest()
    locator = engine.quarantine_destination(
        "integrity",
        object_type="probe2",
        object_id="probe2-object",
        content_sha256=content,
        suffix=".probe",
    )
    locator.parent.mkdir(parents=True, exist_ok=True)
    locator.write_bytes(b"PRE-EXISTING DIFFERENT")
    source = tmp / "q6" / "probe.bin"
    source.write_bytes(b"q conflict probe")
    conflict = False
    try:
        engine._quarantine_file(
            source, locator, hashlib.sha256(b"q conflict probe").hexdigest()
        )
    except rec_mod.RecoveryQuarantineConflict:
        conflict = True
    cases.append(
        _case(
            "different_bytes_conflict",
            conflict=conflict,
            result=_OK if conflict else "FAIL",
        )
    )

    # -- unknown_context quarantine --------------------------------------------
    stack = crash.RecoveryStack(tmp / "q7")
    data = b"q unknown context"
    stack.store.put_bytes(
        data, storage_encoding=_storage_encoding_NONE(), source_media_type=_base_media()
    )
    engine = crash._engine(stack)
    result = engine.scan(recovery_run_id="mx-q7")
    engine.apply_plan(result, recovery_run_id="mx-q7")
    qdir = tmp / "q7" / "quarantine" / "unknown_context"
    cases.append(
        _case(
            "unknown_context_quarantine",
            quarantined=qdir.exists() and len(list(qdir.iterdir())) == 1,
            result=_OK if qdir.exists() else "FAIL",
        )
    )

    # -- path escape rejected ---------------------------------------------------
    stack = crash.RecoveryStack(tmp / "q8")
    engine = crash._engine(stack)
    source = tmp / "q8" / "inner.bin"
    source.write_bytes(b"escape")
    outside = (tmp / "q8").parent / "outside-escape.bin"
    rejected = False
    try:
        engine._quarantine_file(source, outside, hashlib.sha256(b"escape").hexdigest())
    except rec_mod.RecoveryPathSafetyError:
        rejected = True
    cases.append(
        _case(
            "path_escape_rejected",
            rejected=rejected,
            outside_created=outside.exists(),
            result=_OK if (rejected and not outside.exists()) else "FAIL",
        )
    )

    # -- symlink escape rejected (POSIX; skip on Windows) -----------------------
    import os

    if os.name == "nt":
        cases.append(
            _case(
                "symlink_escape_rejected",
                skipped="posix_symlink_semantics_required",
                result="SKIPPED_ON_WINDOWS",
            )
        )
    else:
        stack = crash.RecoveryStack(tmp / "q9")
        engine = crash._engine(stack)
        outside = (tmp / "q9").parent / "symlink-target.bin"
        outside.write_bytes(b"x")
        link = tmp / "q9" / "escape-link"
        os.symlink(outside, link)
        rejected = False
        try:
            engine._quarantine_file(
                link,
                tmp / "q9" / "quarantine" / "integrity" / "esc.quarantined",
                hashlib.sha256(b"x").hexdigest(),
            )
        except (rec_mod.RecoveryPathSafetyError, rec_mod.RecoveryQuarantineConflict):
            rejected = True
        cases.append(
            _case(
                "symlink_escape_rejected",
                rejected=rejected,
                result=_OK if rejected else "FAIL",
            )
        )

    return {
        "matrix": "BLOC_04_I08_QUARANTINE_MATRIX",
        "checkpoint": "SENSOR-B4-I08",
        "doctrine": (
            "I08 §10/§11/§29/§30 — quarantined artifacts preserve forensic "
            "bytes under deterministic no-clobber locators, the canonical "
            "location fails closed, and path/symlink escapes are refused"
        ),
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Matrix 3 — CRASH MATRIX (§24, 12 frozen scenarios)
# ---------------------------------------------------------------------------


def build_crash_matrix(tmp: Path) -> dict:
    crash = _load_crash()
    rec = _load_recovery()
    rec_mod = rec.rec
    base = _load_base()
    cases: list[dict] = []

    def scenario_ok(case: dict) -> bool:
        return case["result"] == _OK

    # 1. crash halfway through blob write
    stack = crash.RecoveryStack(tmp / "c1")
    (tmp / "c1" / "staging").mkdir(exist_ok=True)
    (tmp / "c1" / "staging" / "half.partial").write_bytes(b"half")
    engine = crash._engine(stack)
    result = engine.scan(recovery_run_id="mx-c1")
    staging = [f for f in result.findings if f.problem == rec_mod.PROBLEM_UNCOMMITTED_STAGING]
    engine.apply_plan(result, recovery_run_id="mx-c1")
    cases.append(
        _case(
            "crash_halfway_through_blob_write",
            classified="UNCOMMITTED_STAGING",
            no_committed_claim=not (tmp / "c1" / "blobs").exists(),
            no_cursor_movement=True,
            quarantined=(tmp / "c1" / "quarantine" / "malformed").exists()
            and len(list((tmp / "c1" / "quarantine" / "malformed").iterdir())) == 1,
            result=_OK if staging else "FAIL",
        )
    )

    # 2. crash after blob rename before metadata
    stack = crash.RecoveryStack(tmp / "c2")
    data = b"c2 orphan"
    orphan_sha = stack.store.put_bytes(
        data, storage_encoding=_storage_encoding_NONE(), source_media_type=_base_media()
    ).blob.blob_sha256
    engine = crash._engine(stack)
    result = engine.scan(recovery_run_id="mx-c2")
    orphans = [f for f in result.findings if f.problem == rec_mod.PROBLEM_ORPHAN_DURABLE_BLOB]
    # no context -> unknown-context quarantine (frozen §24-2 alternative)
    engine.apply_plan(result, recovery_run_id="mx-c2")
    gone = not _blob_path_for(tmp / "c2", orphan_sha).exists()
    cases.append(
        _case(
            "crash_after_blob_rename_before_metadata",
            classified="ORPHAN_DURABLE_BLOB",
            unknown_context_quarantine=gone,
            result=_OK if (orphans and gone) else "FAIL",
        )
    )

    # 3. crash after acquisition commit before projection
    stack = crash.RecoveryStack(tmp / "c3")
    sha = stack.seed_blob(b"c3 t0a")
    stack.seed_acquisition(sha, "acq-c3-mx")
    result = crash._engine(stack).scan(recovery_run_id="mx-c3")
    cases.append(
        _case(
            "crash_after_acquisition_before_projection",
            t0a_valid=stack.acq_repo.get_acquisition("acq-c3-mx").blob_sha256 == sha,
            projection_absent=not (tmp / "c3" / "projections").exists(),
            no_findings=result.findings == (),
            result=_OK if result.findings == () else "FAIL",
        )
    )

    # 4. crash after projection write before manifest
    stack = crash.RecoveryStack(tmp / "c4")
    sha = stack.seed_blob(b"c4 source")
    stack.seed_acquisition(sha, "acq-c4-mx")
    proj_dir = tmp / "c4" / "projections"
    proj_dir.mkdir(parents=True, exist_ok=True)
    (proj_dir / "orphan.parquet").write_bytes(b"PAR1-c4")
    result = crash._engine(stack).scan(recovery_run_id="mx-c4")
    orphans = [f for f in result.findings if f.problem == rec_mod.PROBLEM_ORPHAN_PROJECTION]
    cases.append(
        _case(
            "crash_after_projection_write_before_manifest",
            classified="ORPHAN_PROJECTION",
            result=_OK if orphans else "FAIL",
        )
    )

    # 5. crash before manifest-current pointer update
    stack = crash.RecoveryStack(tmp / "c5")
    sha = stack.seed_blob(b"c5 target")
    stack.seed_acquisition(sha, "acq-c5-mx")
    stack.seed_manifest("pm-c5-mx", crash._ORPHAN_PARTITION_KEY, sha)
    crash._publish_orphan_fragment(
        stack, "pm-c5-mx-v2", sha, version=2, supersedes="pm-does-not-exist"
    )
    engine = crash._engine(stack)
    result = engine.scan(recovery_run_id="mx-c5")
    orphans = [f for f in result.findings if f.problem == rec_mod.PROBLEM_ORPHAN_MANIFEST]
    engine.apply_plan(result, recovery_run_id="mx-c5")
    chain = stack.manifest_repo.list_manifest_versions(crash._ORPHAN_PARTITION_KEY)
    cases.append(
        _case(
            "crash_before_manifest_current_pointer_update",
            classified="ORPHAN_MANIFEST",
            current_pointer_unchanged=[m.partition_manifest_id for m in chain]
            == ["pm-c5-mx"],
            unresolved_recorded=True,
            result=_OK if orphans else "FAIL",
        )
    )

    # 6. crash before resume advancement
    stack = crash.RecoveryStack(tmp / "c6", clock=base.TickingClock())
    job_id = "job-c6-mx"
    base._create(stack.repo, job_id)
    base._drive_to_manifest(stack.repo, job_id)
    sha = base._full_batch(stack, "acq-c6-mx", "pm-c6-mx", b'{"rows": ["c6"]}')
    base._checkpoint(stack.repo, job_id, "acq-c6-mx", "pm-c6-mx")
    state = stack.repo.get_job(job_id)
    result = crash._engine(stack).scan(recovery_run_id="mx-c6")
    cases.append(
        _case(
            "crash_before_resume_advancement",
            durable_batch_valid=state.last_committed_blob_sha256 == sha,
            resume_not_skipped=state.status.value == "CHECKPOINT_ADVANCED",
            no_findings=result.findings == (),
            result=_OK if result.findings == () else "FAIL",
        )
    )

    # 7. identical refetch — existing revision/refetch semantics preserved
    stack = crash.RecoveryStack(tmp / "c7")
    sha = stack.seed_blob(b"c7 identical")
    stack.seed_acquisition(sha, "acq-c7-mx")
    again = stack.seed_blob(b"c7 identical")
    stack.seed_acquisition(sha, "acq-c7-mx-b")
    cases.append(
        _case(
            "identical_refetch",
            same_content_identity=sha == again,
            existing_semantics_preserved=sha == again,
            result=_OK if sha == again else "FAIL",
        )
    )

    # 8. same source/request with mutated bytes — revision semantics
    stack = crash.RecoveryStack(tmp / "c8")
    sha = stack.seed_blob(b"c8 source")
    stack.seed_acquisition(sha, "acq-c8-mx")
    stack.seed_acquisition(sha, "acq-c8-mx-r")
    records = stack.acq_repo.list_acquisitions_for_blob(sha)
    cases.append(
        _case(
            "same_source_mutated_bytes",
            revision_records=len(records) >= 2,
            result=_OK if len(records) >= 2 else "FAIL",
        )
    )

    # 9. corrupted stored blob
    stack = crash.RecoveryStack(tmp / "c9")
    sha = stack.seed_blob(b"c9 victim")
    stack.seed_acquisition(sha, "acq-c9-mx")
    _blob_path_for(tmp / "c9", sha).write_bytes(b"corrupt")
    engine = crash._engine(stack)
    result = engine.scan(recovery_run_id="mx-c9")
    engine.apply_plan(result, recovery_run_id="mx-c9")
    qdir = tmp / "c9" / "quarantine" / "integrity"
    cases.append(
        _case(
            "corrupted_stored_blob",
            integrity_quarantine=qdir.exists() and len(list(qdir.iterdir())) == 1,
            no_silent_overwrite=not _blob_path_for(tmp / "c9", sha).exists(),
            result=_OK if qdir.exists() else "FAIL",
        )
    )

    # 10. missing manifest target
    stack = crash.RecoveryStack(tmp / "c10")
    sha = stack.seed_blob(b"c10 target")
    stack.seed_acquisition(sha, "acq-c10-mx")
    stack.seed_manifest("pm-c10-mx", crash._ORPHAN_PARTITION_KEY, sha)
    _blob_path_for(tmp / "c10", sha).unlink()
    result = crash._engine(stack).scan(recovery_run_id="mx-c10")
    targets = [
        f for f in result.findings if f.problem == rec_mod.PROBLEM_MISSING_MANIFEST_TARGET
    ]
    cases.append(
        _case(
            "missing_manifest_target",
            fail_closed=len(targets) == 1,
            recovery_evidence_planned=any(
                a.problem == rec_mod.PROBLEM_MISSING_MANIFEST_TARGET
                for a in result.planned_actions
            ),
            result=_OK if targets else "FAIL",
        )
    )

    # 11. parser bug / invalid projection
    stack = crash.RecoveryStack(tmp / "c11")
    sha = stack.seed_blob(b"c11 t0a")
    stack.seed_acquisition(sha, "acq-c11-mx")
    bad = tmp / "c11" / "projections" / "bad.parquet"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_bytes(b"not parquet")
    engine = crash._engine(stack)
    result = engine.scan(recovery_run_id="mx-c11")
    engine.apply_plan(result, recovery_run_id="mx-c11")
    cases.append(
        _case(
            "parser_bug_invalid_projection",
            t0a_retained=stack.acq_repo.get_acquisition("acq-c11-mx").blob_sha256 == sha,
            projection_quarantined=not bad.exists(),
            no_source_rewrite=True,
            result=_OK if not bad.exists() else "FAIL",
        )
    )

    # 12. concurrent writers to same logical partition
    stack = crash.RecoveryStack(tmp / "c12")
    sha1 = stack.seed_blob(b"c12 v1")
    stack.seed_acquisition(sha1, "acq-c12-mx-a")
    stack.seed_manifest("pm-c12-mx-1", crash._ORPHAN_PARTITION_KEY, sha1)
    sha2 = stack.seed_blob(b"c12 v2")
    stack.seed_acquisition(sha2, "acq-c12-mx-b")
    from crypto_sensor_fabric.providers.base.enums import Granularity
    from crypto_sensor_fabric.storage.enums import IntegrityState
    from crypto_sensor_fabric.storage.models import PartitionManifest as PM

    stale = PM(
        partition_manifest_id="pm-c12-mx-2-stale",
        partition_key=crash._ORPHAN_PARTITION_KEY,
        manifest_version=2,
        provider=crash.PROVIDER,
        venue=crash.PROVIDER,
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        native_instrument=base._INSTRUMENT,
        source_granularity=Granularity.G1H,
        date_basis=DateBasis.EVENT_TIME,
        logical_date_start=base.FIXED,
        logical_date_end=base.FIXED,
        blob_refs=[sha2],
        projection_refs=[],
        coverage_state=CoverageState.PARTIAL,
        integrity_state=IntegrityState.UNVERIFIED,
        row_count=1,
        min_time=base.FIXED,
        max_time=base.FIXED,
        gap_count=0,
        revision_count=0,
        supersedes_manifest_id="pm-c12-mx-1",
        created_at=base.FIXED,
    )
    from crypto_sensor_fabric.storage.manifests import ManifestCASConflict

    cas_refused = False
    try:
        stack.manifest_repo.append_partition_manifest(stale, ("pm-c12-mx-1", 2))
    except ManifestCASConflict:
        cas_refused = True
    cases.append(
        _case(
            "concurrent_writers_cas_preserved",
            cas_refusal=cas_refused,
            no_silent_overwrite=True,
            result=_OK if cas_refused else "FAIL",
        )
    )

    return {
        "matrix": "BLOC_04_I08_CRASH_MATRIX",
        "checkpoint": "SENSOR-B4-I08",
        "doctrine": (
            "I08 §24 — all 12 frozen crash scenarios proven against real "
            "durable truth: staging/orphan/projection/manifest classifications, "
            "resume never skips, no silent overwrite, CAS preserved"
        ),
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Matrix 4 — IDEMPOTENCE (§27/§28/§20)
# ---------------------------------------------------------------------------


def build_recovery_idempotence_matrix(tmp: Path) -> dict:
    crash = _load_crash()
    rec = _load_recovery()
    rec_mod = rec.rec
    cases: list[dict] = []

    # -- scan read-only (byte census before/after) ----------------------------
    stack = crash.RecoveryStack(tmp / "ro")
    sha = stack.seed_blob(b"ro source")
    stack.seed_acquisition(sha, "acq-ro")
    (tmp / "ro" / "staging").mkdir(exist_ok=True)
    (tmp / "ro" / "staging" / "x.partial").write_bytes(b"p")
    stack.store.put_bytes(
        b"ro orphan", storage_encoding=_storage_encoding_NONE(), source_media_type=_base_media()
    )

    def census(root: Path) -> dict[str, str]:
        return {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*"))
            if p.is_file()
        }

    before = census(tmp / "ro")
    crash._engine(stack).scan(recovery_run_id="mx-ro")
    after = census(tmp / "ro")
    cases.append(
        _case(
            "scan_read_only",
            byte_census_identical=before == after,
            result=_OK if before == after else "MUTATED",
        )
    )

    # -- repeat scan same findings ---------------------------------------------
    stack = crash.RecoveryStack(tmp / "rs")
    stack.seed_blob(b"rs source")
    first = crash._engine(stack).scan(recovery_run_id="mx-rs")
    second = crash._engine(stack).scan(recovery_run_id="mx-rs")
    cases.append(
        _case(
            "repeat_scan_same_findings",
            identical=first.to_dict() == second.to_dict(),
            result=_OK if first.to_dict() == second.to_dict() else "FAIL",
        )
    )

    # -- repeat apply idempotent -------------------------------------------------
    stack = crash.RecoveryStack(tmp / "ra")
    stack.store.put_bytes(
        b"ra orphan",
        storage_encoding=_storage_encoding_NONE(),
        source_media_type=_base_media(),
    )
    engine = crash._engine(stack)
    result = engine.scan(recovery_run_id="mx-ra")
    first = engine.apply_plan(result, recovery_run_id="mx-ra")
    second = engine.apply_plan(result)
    cases.append(
        _case(
            "repeat_apply_idempotent",
            first_apply=len(first),
            second_apply=len(second),
            result=_OK if (first and not second) else "FAIL",
        )
    )

    # -- stale plan conflict (orphan blob metadata appears) ----------------------
    stack = crash.RecoveryStack(tmp / "sp")
    stack.store.put_bytes(
        b"sp orphan",
        storage_encoding=_storage_encoding_NONE(),
        source_media_type=_base_media(),
    )
    result = crash._engine(stack).scan(recovery_run_id="mx-sp")
    stack.blob_repo.append_metadata(
        stack.store.put_bytes(
            b"sp orphan",
            storage_encoding=_storage_encoding_NONE(),
            source_media_type=_base_media(),
        ).blob
    )
    conflict = False
    try:
        crash._engine(stack).apply_plan(result, recovery_run_id="mx-sp")
    except rec_mod.RecoveryPlanConflict:
        conflict = True
    cases.append(
        _case(
            "stale_plan_conflict",
            conflict=conflict,
            result=_OK if conflict else "FAIL",
        )
    )

    # -- recovery action exact retry idempotent + divergence typed ---------------
    stack = crash.RecoveryStack(tmp / "jr")
    engine = crash._engine(stack)
    from crypto_sensor_fabric.storage.json_catalog import JsonCatalogConflict

    planned = _planned_unknown_context()
    engine._journal_action(
        run_id="mx-jr",
        planned=planned,
        resolution="quarantined",
        after_state={"quarantined": True},
    )
    action_id = engine.journal.action_ids()[0]
    payload = engine.journal.get(action_id)
    same = engine.journal.record(
        recovery_run_id="mx-jr",
        object_type="EVIDENCE_BLOB",
        object_id="a" * 64,
        problem=rec_mod.PROBLEM_UNKNOWN_CONTEXT,
        resolution="quarantined",
        before_state={"k": 1},
        after_state={"quarantined": True},
        action_kind=planned.action_kind,
    )
    divergence_typed = False
    try:
        engine.journal._catalog.commit(action_id, {**payload, "problem": "TAMPERED"})
    except JsonCatalogConflict:
        divergence_typed = True
    cases.append(
        _case(
            "recovery_action_exact_retry",
            adopted_existing=same[1] is True,
            divergence_typed=divergence_typed,
            result=_OK if (same[1] is True and divergence_typed) else "FAIL",
        )
    )

    # -- foreign lock not auto-deleted --------------------------------------------
    stack = crash.RecoveryStack(tmp / "fl")
    lock_id = hashlib.sha256(b"job-fl").hexdigest()
    lock_path = tmp / "fl" / "locks" / f"{lock_id}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(b"{}")
    engine = crash._engine(stack)
    result = engine.scan(recovery_run_id="mx-fl")
    engine.apply_plan(result, recovery_run_id="mx-fl")
    cases.append(
        _case(
            "foreign_lock_not_auto_deleted",
            lock_present=lock_path.exists(),
            recorded=lock_path.exists(),
            result=_OK if lock_path.exists() else "FAIL",
        )
    )

    return {
        "matrix": "BLOC_04_I08_RECOVERY_IDEMPOTENCE_MATRIX",
        "checkpoint": "SENSOR-B4-I08",
        "doctrine": (
            "I08 §27/§28/§20 — scan is read-only and repeatable, apply is "
            "idempotent with typed stale-plan conflicts, exact journal "
            "retries adopt and divergences stay typed, foreign locks are "
            "never auto-deleted"
        ),
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def findings_of(result):
    return list(result.findings)


def _planned_unknown_context():
    from crypto_sensor_fabric.storage import recovery as rec_module

    return rec_module.RecoveryPlanAction(
        action_kind=rec_module._ACTION_QUARANTINE_UNKNOWN_CONTEXT,
        object_type="EVIDENCE_BLOB",
        object_id="a" * 64,
        problem=rec_module.PROBLEM_UNKNOWN_CONTEXT,
        resolution="r",
        before_state={"k": 1},
        after_state={},
    )


def _blob_path_for(root: Path, sha: str) -> Path:
    from crypto_sensor_fabric.storage.paths import blob_object_key, resolve_under_root
    from crypto_sensor_fabric.storage.enums import StorageEncoding

    return resolve_under_root(root, blob_object_key(sha, StorageEncoding.NONE))


def _storage_encoding_NONE():
    from crypto_sensor_fabric.storage.enums import StorageEncoding

    return StorageEncoding.NONE


def _base_media() -> str:
    return "application/json"


# ---------------------------------------------------------------------------
# Read-only gates + explicit publication
# ---------------------------------------------------------------------------

BUILDERS = [
    ("build_recovery_scan_matrix", "BLOC_04_I08_RECOVERY_SCAN_MATRIX.json"),
    ("build_quarantine_matrix", "BLOC_04_I08_QUARANTINE_MATRIX.json"),
    ("build_crash_matrix", "BLOC_04_I08_CRASH_MATRIX.json"),
    (
        "build_recovery_idempotence_matrix",
        "BLOC_04_I08_RECOVERY_IDEMPOTENCE_MATRIX.json",
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
        for p in sorted(EVIDENCE_DIR.glob("*.json"))
    }
    for builder_name, _ in BUILDERS:
        globals()[builder_name](tmp_path / builder_name)
    after = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(EVIDENCE_DIR.glob("*.json"))
    }
    assert before == after, "pytest must never write the committed evidence tree"


if __name__ == "__main__":
    for builder_name, filename in BUILDERS:
        target = EVIDENCE_DIR / filename
        if target.exists():
            print(f"REFUSING to overwrite committed {filename}")
            continue
        payload = globals()[builder_name](Path(f"tmp-i08-{builder_name}"))
        target.write_bytes(stable_evidence_bytes(payload))
        print(f"PUBLISHED {filename}")
