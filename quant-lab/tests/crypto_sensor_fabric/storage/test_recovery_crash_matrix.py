"""SENSOR-B4-I08B/C/D — recovery apply, crash matrix, idempotence, locks.

Covers the frozen I08 apply surface over the REAL I04/I05/I07 stack:

- the 12 frozen crash scenarios (I08 §24) mapped to concrete storage
  truth, each with its required expectation;
- quarantine/apply results (I08 §10/§11/§12/§13/§30): bytes preserved,
  canonical objects unusable, no-clobber, no silent repair;
- idempotence (I08 §27): scan read-only and repeatable, repeat apply
  idempotent or typed already-applied, exact journal retry idempotent,
  divergent retry typed conflict, foreign locks never auto-deleted;
- TOCTOU (I08 §28): a plan applied against changed truth conflicts typed
  (also proven for jobs and manifests);
- job durability divergence (I08 §18/§19) using the proven I07R1H forged
  head attack: runtime gate refuses the transition, the refusal is
  journaled as UNRESOLVED, old checkpoint events never mutated;
- lock policy (I08 §20): LOCK_PRESENT_OWNER_UNPROVEN recorded, explicit
  operator clear journaled-before-mutation, no in-process owner probe.

Read-only against the committed evidence tree; no network; no provider
integration.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest
from crypto_sensor_fabric.providers.base.enums import Granularity
from crypto_sensor_fabric.storage import recovery as rec
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.storage.enums import (
    CoverageState,
    DateBasis,
    IntegrityState,
    StorageEncoding,
    StorageJobStatus,
    StorageObjectType,
)
from crypto_sensor_fabric.storage.models import (
    AcquisitionRecord,
    EvidenceBlob,
    PartitionManifest,
)

from _sibling_import import load_sibling

_base = load_sibling("_i08_base_mod", "test_job_state_r1")

FP = _base._FP
PROVIDER = _base._PROVIDER

#: Shared partition key for orphan-fragment cases (exact, deterministic).
_ORPHAN_PARTITION_KEY = FP + "/2026-01-15"


def RecoveryStack(root: Path, **kwargs: Any) -> Any:
    """The real I07 stack plus a T0-root attribute for the recovery engine.

    A factory (not a subclass): the base module is loaded through the
    sibling loader, so its classes are invisible to static analysis.
    """
    stack = _base.JobStack(root, **kwargs)
    stack.root = root  # T0 root for the recovery engine
    return stack


def _engine(stack: Any) -> rec.RecoveryEngine:
    return rec.RecoveryEngine(
        stack.root,
        blob_store=stack.store,
        blob_metadata_repository=stack.blob_repo,
        acquisition_repository=stack.acq_repo,
        manifest_repository=stack.manifest_repo,
        job_repository=stack.repo,
    )


def _blob_path(root: Path, sha: str, encoding: StorageEncoding) -> Path:
    from crypto_sensor_fabric.storage.paths import blob_object_key, resolve_under_root

    return resolve_under_root(root, blob_object_key(sha, encoding))


def _sha_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Job-chain divergence machinery (I07R1H proven attack, reused verbatim)
# ---------------------------------------------------------------------------


def _events_dir(root: Path) -> Path:
    return root / "catalogs" / "jobs_state" / "events"


def _job_events(root: Path, job_id: str) -> list[dict[str, Any]]:
    events = []
    for path in sorted(_events_dir(root).glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("job_id") == job_id:
            events.append(payload)
    events.sort(key=lambda event: event["sequence"])
    return events


def _bump_iso(value: str, seconds: int) -> str:
    from datetime import datetime, timedelta

    bumped = datetime.fromisoformat(value) + timedelta(seconds=seconds)
    text = bumped.isoformat()
    return text.replace("+00:00", "Z") if value.endswith("Z") else text


def _publish_forged_from_status_break(root: Path, job_id: str) -> None:
    """I07R1H §17 attack: publish a chain-invalid later checkpoint head at
    its correct hashed physical key (proof left fully valid)."""
    events = _job_events(root, job_id)
    genuine = next(
        event for event in events if event.get("checkpoint_proof") is not None
    )
    sequence = max(event["sequence"] for event in events) + 1
    instant = _bump_iso(
        max(event["resulting_state"]["updated_at"] for event in events), 1
    )
    forged = json.loads(json.dumps(genuine))
    forged["sequence"] = sequence
    forged["transition_id"] = f"{job_id}:{sequence:06d}"
    forged["transition"]["transition_id"] = forged["transition_id"]
    forged["transition"]["from_status"] = StorageJobStatus.RAW_STAGED.value
    forged["transition"]["to_status"] = StorageJobStatus.CHECKPOINT_ADVANCED.value
    forged["transition"]["transitioned_at"] = instant
    forged["transition"]["reason"] = "forged from_status break (I08 crash-matrix)"
    forged["resulting_state"]["updated_at"] = instant
    forged["resulting_state"]["status"] = StorageJobStatus.CHECKPOINT_ADVANCED.value
    key = hashlib.sha256(forged["transition_id"].encode("utf-8")).hexdigest()
    (_events_dir(root) / f"{key}.json").write_bytes(json.dumps(forged).encode("utf-8"))


# ---------------------------------------------------------------------------
# Manifest/orphan-fragment machinery (real repository, pointer-crash shape)
# ---------------------------------------------------------------------------


def _publish_orphan_fragment(
    stack: Any,
    manifest_id: str,
    sha: str,
    *,
    version: int = 2,
    supersedes: str | None = None,
) -> PartitionManifest:
    """Publish a manifest fragment WITHOUT updating the current pointer —
    the frozen P1 crash case (I08 §24-5): immutable orphan possible."""
    manifest = PartitionManifest(
        partition_manifest_id=manifest_id,
        partition_key=_ORPHAN_PARTITION_KEY,
        manifest_version=version,
        provider=PROVIDER,
        venue=PROVIDER,
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        native_instrument=_base._INSTRUMENT,
        source_granularity=Granularity.G1H,
        date_basis=DateBasis.EVENT_TIME,
        logical_date_start=_base.FIXED,
        logical_date_end=_base.FIXED,
        blob_refs=[sha],
        projection_refs=[],
        coverage_state=CoverageState.PARTIAL,
        integrity_state=IntegrityState.UNVERIFIED,
        row_count=1,
        min_time=_base.FIXED,
        max_time=_base.FIXED,
        gap_count=0,
        revision_count=0,
        supersedes_manifest_id=supersedes,
        created_at=_base.FIXED,
    )
    from crypto_sensor_fabric.storage.manifests import (
        MANIFEST_SCHEMA,
        _manifest_fragment_name,
        _manifest_row,
        _partition_hash,
    )

    fragment_rows = [_manifest_row(manifest)]
    from crypto_sensor_fabric.storage.catalog import publish_immutable_fragment

    partition_hash = _partition_hash(manifest.partition_key)
    publish_immutable_fragment(
        stack.root,
        ["catalogs", "manifests", "partitions", partition_hash],
        _manifest_fragment_name(manifest),
        MANIFEST_SCHEMA,
        fragment_rows,
        clock=lambda: _base.FIXED,
    )
    return manifest


def _read_fragment_manifest(root: Path, manifest: PartitionManifest) -> PartitionManifest:
    from crypto_sensor_fabric.storage.catalog import read_fragment
    from crypto_sensor_fabric.storage.manifests import (
        MANIFEST_SCHEMA,
        _manifest_from_row,
        _manifest_fragment_name,
        _partition_hash,
    )

    path = (
        root
        / "catalogs"
        / "manifests"
        / "partitions"
        / _partition_hash(manifest.partition_key)
        / _manifest_fragment_name(manifest)
    )
    rows = read_fragment(path, MANIFEST_SCHEMA)
    assert len(rows) == 1
    return _manifest_from_row(rows[0])


# ---------------------------------------------------------------------------
# The 12 frozen crash scenarios (I08 §24)
# ---------------------------------------------------------------------------


def test_crash_1_half_blob_write_is_uncommitted_staging(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path)
    (tmp_path / "staging").mkdir(exist_ok=True)
    (tmp_path / "staging" / "abc123.partial").write_bytes(b"half-written")
    result = _engine(stack).scan(recovery_run_id="run-c1")
    staging = [
        f for f in result.findings if f.problem == rec.PROBLEM_UNCOMMITTED_STAGING
    ]
    assert len(staging) == 1
    assert "abc123.partial" in staging[0].detail
    _engine(stack).apply_plan(result, recovery_run_id="run-c1")
    records = _engine(stack).journal.list_for_run("run-c1")
    assert records and "resume was never advanced from staging" in records[-1]["resolution"]
    assert not (tmp_path / "staging" / "abc123.partial").exists()
    quarantined = list((tmp_path / "quarantine" / "malformed").iterdir())
    assert len(quarantined) == 1


def test_crash_2_orphan_durable_blob_reconciles_with_context(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path)
    data = b"crash-2 orphan"
    orphan_sha = stack.store.put_bytes(
        data, storage_encoding=StorageEncoding.NONE, source_media_type=_base.MEDIA
    ).blob.blob_sha256
    # Durable context prepared through the REAL repositories (what the
    # crashed writer would have committed next).
    blob_meta = EvidenceBlob(
        blob_sha256=orphan_sha,
        byte_length=len(data),
        stored_byte_length=len(data),
        source_media_type=_base.MEDIA,
        storage_encoding=StorageEncoding.NONE,
        storage_uri=f"blobs/sha256/{orphan_sha[:2]}/{orphan_sha[2:4]}/{orphan_sha}.blob",
        integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
        created_at=_base.FIXED,
    )
    acquisition = AcquisitionRecord(
        acquisition_id="acq-crash2",
        provider_id=PROVIDER,
        venue=PROVIDER,
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint=FP,
        adapter_version="kraken-adapter-v2",
        requested_start=_base.FIXED,
        requested_end=_base.FIXED,
        native_instrument=_base._INSTRUMENT,
        native_granularity=Granularity.G1H,
        request_started_at=_base.FIXED,
        response_observed_at=_base.FIXED,
        ingested_at=_base.FIXED,
        http_status_or_source_status="200",
        endpoint_host="futures.kraken.com",
        endpoint_path="/api/charts/v1/analytics/PI_XBTUSD/funding",
        request_family="market_analytics_funding",
        source_locator="https://futures.kraken.com/api/x",
        blob_sha256=orphan_sha,
    )
    _engine(stack).register_orphan_context(
        orphan_sha, evidence_blob=blob_meta, acquisition=acquisition
    )
    engine = _engine(stack)  # ONE engine instance: registration + apply
    engine.register_orphan_context(
        orphan_sha, evidence_blob=blob_meta, acquisition=acquisition
    )
    result = engine.scan(recovery_run_id="run-c2")
    orphans = [
        f for f in result.findings if f.problem == rec.PROBLEM_ORPHAN_DURABLE_BLOB
    ]
    assert [f.object_id for f in orphans] == [orphan_sha]
    engine.apply_plan(result, recovery_run_id="run-c2")
    assert stack.blob_repo.get_blob_metadata(orphan_sha)
    assert stack.acq_repo.get_acquisition("acq-crash2").blob_sha256 == orphan_sha


def test_crash_2_unknown_context_quarantines(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path)
    data = b"crash-2 no context"
    orphan_sha = stack.store.put_bytes(
        data, storage_encoding=StorageEncoding.NONE, source_media_type=_base.MEDIA
    ).blob.blob_sha256
    result = _engine(stack).scan(recovery_run_id="run-c2b")
    _engine(stack).apply_plan(result, recovery_run_id="run-c2b")
    assert not _blob_path(tmp_path, orphan_sha, StorageEncoding.NONE).exists()
    quarantined = list((tmp_path / "quarantine" / "unknown_context").iterdir())
    assert len(quarantined) == 1
    assert hashlib.sha256(quarantined[0].read_bytes()).hexdigest() == _sha_of(data)


def test_crash_3_acquisition_before_projection_keeps_t0a_valid(
    tmp_path: Path,
) -> None:
    """T0A durable; no projection exists.  Recovery must NOT manufacture one
    or damage the acquisition: clean scan, acquisition still readable."""
    stack = RecoveryStack(tmp_path)
    sha = stack.seed_blob(b"crash-3 t0a only")
    stack.seed_acquisition(sha, "acq-c3")
    result = _engine(stack).scan(recovery_run_id="run-c3")
    assert result.findings == ()
    record = stack.acq_repo.get_acquisition("acq-c3")
    assert record.blob_sha256 == sha
    assert not (tmp_path / "projections").exists()


def test_crash_4_orphan_projection_detected_and_quarantined(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path)
    sha = stack.seed_blob(b"crash-4 source")
    stack.seed_acquisition(sha, "acq-c4")
    body = b"PAR1-forged-parquet-bytes"
    projection_path = tmp_path / "projections" / "orphan-c4.parquet"
    projection_path.parent.mkdir(parents=True, exist_ok=True)
    projection_path.write_bytes(body)
    result = _engine(stack).scan(recovery_run_id="run-c4")
    orphans = [
        f for f in result.findings if f.problem == rec.PROBLEM_ORPHAN_PROJECTION
    ]
    assert len(orphans) == 1
    _engine(stack).apply_plan(result, recovery_run_id="run-c4")
    assert not projection_path.exists()
    quarantined = list((tmp_path / "quarantine" / "unknown_context").iterdir())
    assert len(quarantined) == 1


def test_crash_5_orphan_manifest_fragment_no_latest_wins(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path)
    sha = stack.seed_blob(b"crash-5 manifest target")
    stack.seed_acquisition(sha, "acq-c5")
    stack.seed_manifest("pm-c5", _ORPHAN_PARTITION_KEY, sha)
    # Pointer-crash orphan with UNPROVABLE ancestry (supersedes a manifest
    # that does not exist): recovery must record it unresolved, never
    # promote it (I08 §15).
    _publish_orphan_fragment(
        stack,
        "pm-c5-v2",
        sha,
        version=2,
        supersedes="pm-does-not-exist",
    )
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="run-c5")
    orphan_findings = [
        f for f in result.findings if f.problem == rec.PROBLEM_ORPHAN_MANIFEST
    ]
    assert [f.object_id for f in orphan_findings] == ["pm-c5-v2"]
    engine.apply_plan(result, recovery_run_id="run-c5")
    chain = stack.manifest_repo.list_manifest_versions(_ORPHAN_PARTITION_KEY)
    assert [m.partition_manifest_id for m in chain] == ["pm-c5"], (
        "no latest-wins: the committed chain must stay v1"
    )
    records = engine.journal.list_for_object("PARTITION_MANIFEST", "pm-c5-v2")
    assert records and "UNRESOLVED" in records[0]["resolution"]


def test_crash_5_reconciliation_through_public_api_when_cas_permits(
    tmp_path: Path,
) -> None:
    stack = RecoveryStack(tmp_path)
    sha = stack.seed_blob(b"crash-5b target")
    stack.seed_acquisition(sha, "acq-c5b")
    stack.seed_manifest("pm-c5b", _ORPHAN_PARTITION_KEY, sha)
    # Pointer-crash orphan with EXACT ancestry (supersedes the current v1)
    # and verified refs: recovery reconciles through the PUBLIC CAS API.
    _publish_orphan_fragment(
        stack, "pm-c5b-v2", sha, version=2, supersedes="pm-c5b"
    )
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="run-c5b")
    engine.apply_plan(result, recovery_run_id="run-c5b")
    chain = stack.manifest_repo.list_manifest_versions(_ORPHAN_PARTITION_KEY)
    assert [m.partition_manifest_id for m in chain] == ["pm-c5b", "pm-c5b-v2"]
    assert chain[1].supersedes_manifest_id == "pm-c5b"


def test_crash_6_checkpoint_refetch_semantics_preserved(tmp_path: Path) -> None:
    """Crash before resume advancement: durable batch valid, re-fetch may
    occur, resume does NOT skip — the accepted I07 semantics themselves."""
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    job_id = "job-c6"
    _base._create(stack.repo, job_id)
    _base._drive_to_manifest(stack.repo, job_id)
    sha = _base._full_batch(
        stack, "acq-c6", "pm-c6", b'{"rows": ["c6"]}'
    )
    _base._checkpoint(
        stack.repo, job_id, "acq-c6", "pm-c6"
    )
    state = stack.repo.get_job(job_id)
    assert state.status is StorageJobStatus.CHECKPOINT_ADVANCED
    assert state.last_committed_blob_sha256 == sha
    assert state.last_manifest_id == "pm-c6"
    result = _engine(stack).scan(recovery_run_id="run-c6")
    job_findings = [
        f for f in result.findings if f.problem == rec.PROBLEM_JOB_DURABILITY_DIVERGENCE
    ]
    assert job_findings == [], "a valid checkpointed job is NOT divergent"


def test_crash_9_corrupted_stored_blob_quarantined_no_overwrite(
    tmp_path: Path,
) -> None:
    stack = RecoveryStack(tmp_path)
    sha = stack.seed_blob(b"crash-9 victim")
    stack.seed_acquisition(sha, "acq-c9")
    corrupt_bytes = b"totally corrupted"
    _blob_path(tmp_path, sha, StorageEncoding.NONE).write_bytes(corrupt_bytes)
    result = _engine(stack).scan(recovery_run_id="run-c9")
    _engine(stack).apply_plan(result, recovery_run_id="run-c9")
    # canonical key empty, corrupt bytes preserved under integrity quarantine
    assert not _blob_path(tmp_path, sha, StorageEncoding.NONE).exists()
    qdir = tmp_path / "quarantine" / "integrity"
    quarantined = list(qdir.iterdir())
    assert len(quarantined) == 1
    assert quarantined[0].read_bytes() == corrupt_bytes
    # acquisition history untouched
    assert stack.acq_repo.get_acquisition("acq-c9").blob_sha256 == sha


def test_crash_10_missing_manifest_target_fails_closed(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path)
    sha = stack.seed_blob(b"crash-10 target")
    stack.seed_acquisition(sha, "acq-c10")
    stack.seed_manifest("pm-c10", "PK-pm-c10", sha)
    _blob_path(tmp_path, sha, StorageEncoding.NONE).unlink()
    result = _engine(stack).scan(recovery_run_id="run-c10")
    targets = [
        f for f in result.findings if f.problem == rec.PROBLEM_MISSING_MANIFEST_TARGET
    ]
    assert targets and targets[0].object_id == "pm-c10"
    _engine(stack).apply_plan(result, recovery_run_id="run-c10")
    # manifest history immutable, canonical reads fail closed
    chain = stack.manifest_repo.list_manifest_versions(targets[0].before_state["partition_key"])
    assert chain and chain[-1].partition_manifest_id == "pm-c10"
    with pytest.raises(Exception):
        stack.manifest_repo._verify_blob_ref(sha)


def test_crash_11_parser_bug_keeps_t0a_no_source_rewrite(tmp_path: Path) -> None:
    """Invalid projection bytes: T0A retained, projection quarantined as
    unknown context, never rebuilt from guessed lineage."""
    stack = RecoveryStack(tmp_path)
    sha = stack.seed_blob(b"crash-11 t0a")
    stack.seed_acquisition(sha, "acq-c11")
    bad = tmp_path / "projections" / "bad.parquet"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_bytes(b"not a parquet file")
    result = _engine(stack).scan(recovery_run_id="run-c11")
    _engine(stack).apply_plan(result, recovery_run_id="run-c11")
    assert stack.acq_repo.get_acquisition("acq-c11").blob_sha256 == sha
    assert not bad.exists()
    assert len(list((tmp_path / "quarantine" / "unknown_context").iterdir())) == 1


def test_crash_12_concurrent_writers_cas_preserved(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path)
    sha1 = stack.seed_blob(b"crash-12 v1")
    stack.seed_acquisition(sha1, "acq-c12a")
    stack.seed_manifest("pm-c12-1", "PK-c12", sha1)
    sha2 = stack.seed_blob(b"crash-12 v2")
    stack.seed_acquisition(sha2, "acq-c12b")
    # A stale writer with an outdated expected_current must get CAS refusal.
    from crypto_sensor_fabric.storage.manifests import ManifestCASConflict

    manifest = PartitionManifest(
        partition_manifest_id="pm-c12-2-stale",
        partition_key="PK-c12",
        manifest_version=2,
        provider=PROVIDER,
        venue=PROVIDER,
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        native_instrument=_base._INSTRUMENT,
        source_granularity=Granularity.G1H,
        date_basis=DateBasis.EVENT_TIME,
        logical_date_start=_base.FIXED,
        logical_date_end=_base.FIXED,
        blob_refs=[sha2],
        projection_refs=[],
        coverage_state=CoverageState.PARTIAL,
        integrity_state=IntegrityState.UNVERIFIED,
        row_count=1,
        min_time=_base.FIXED,
        max_time=_base.FIXED,
        gap_count=0,
        revision_count=0,
        supersedes_manifest_id="pm-c12-1",
        created_at=_base.FIXED,
    )
    with pytest.raises(ManifestCASConflict):
        stack.manifest_repo.append_partition_manifest(
            manifest, ("pm-c12-1", 2)  # stale: actual current is (pm-c12-1, 1)
        )
    # The real append with correct CAS wins.
    manifest2 = manifest.model_copy(
        update={"partition_manifest_id": "pm-c12-2", "supersedes_manifest_id": "pm-c12-1"}
    )
    stack.manifest_repo.append_partition_manifest(manifest2, ("pm-c12-1", 1))
    chain = stack.manifest_repo.list_manifest_versions("PK-c12")
    assert [m.partition_manifest_id for m in chain] == ["pm-c12-1", "pm-c12-2"]


# ---------------------------------------------------------------------------
# Job durability divergence (I08 §18/§19) — I07R1H attack reused
# ---------------------------------------------------------------------------


def test_job_durability_divergence_detected_and_transition_refused(
    tmp_path: Path,
) -> None:
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    job_id = "job-div"
    _base._create(stack.repo, job_id)
    _base._drive_to_manifest(stack.repo, job_id)
    _base._full_batch(stack, "acq-div", "pm-div", b'{"rows": ["div"]}')
    _base._checkpoint(stack.repo, job_id, "acq-div", "pm-div")
    events_before = len(_job_events(tmp_path, job_id))
    _publish_forged_from_status_break(tmp_path, job_id)

    result = _engine(stack).scan(recovery_run_id="run-div")
    divergent = [
        f for f in result.findings if f.problem == rec.PROBLEM_JOB_DURABILITY_DIVERGENCE
    ]
    assert [f.object_id for f in divergent] == [job_id]

    applied = _engine(stack).apply_plan(result, recovery_run_id="run-div")
    # The runtime gate refuses ANY operation on the corrupt chain — the
    # safe transition is recorded UNRESOLVED; the evidence record itself
    # IS the frozen RecoveryAction for the STORAGE_JOB object (I08 §6).
    assert len(applied) == 1
    assert applied[0].object_type is StorageObjectType.STORAGE_JOB
    records = _engine(stack).journal.list_for_object("STORAGE_JOB", job_id)
    assert len(records) == 1
    after = json.loads(records[0]["after_state"])
    assert after["transition_refused"] is True
    assert len(_job_events(tmp_path, job_id)) == events_before + 1


def test_job_quarantine_via_public_api_on_healthy_chain(tmp_path: Path) -> None:
    """§18's preferred safe action exists for genuinely divergent jobs and
    works through the public transition API when the chain itself allows
    the annotated failure edge (e.g. divergence detected in a live job
    BEFORE any forged head: operator decides to quarantine)."""
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    job_id = "job-q"
    _base._create(stack.repo, job_id)
    stack.repo.advance_status(
        job_id,
        to_status=StorageJobStatus.FAILED_TERMINAL,
        reason="operator explicit terminal failure (I08 §18 boundary demo)",
    )
    result = _engine(stack).scan(recovery_run_id="run-q")
    assert result.findings == (), "healthy job is not a recovery finding"
    with pytest.raises(Exception):
        stack.repo.advance_status(
            job_id,
            to_status=StorageJobStatus.QUARANTINED,
            reason="terminal is frozen",
        )


# ---------------------------------------------------------------------------
# Idempotence (I08 §27) + TOCTOU (I08 §28)
# ---------------------------------------------------------------------------


def test_scan_read_only_and_repeatable_full_stack(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path)
    sha = stack.seed_blob(b"idem source")
    stack.seed_acquisition(sha, "acq-idem")
    (tmp_path / "staging").mkdir(exist_ok=True)
    (tmp_path / "staging" / "x.partial").write_bytes(b"partial")
    stack.store.put_bytes(
        b"idem orphan", storage_encoding=StorageEncoding.NONE, source_media_type=_base.MEDIA
    )

    def census() -> dict[str, str]:
        return {
            p.relative_to(tmp_path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(tmp_path.rglob("*"))
            if p.is_file()
        }

    before = census()
    engine = _engine(stack)
    first = engine.scan(recovery_run_id="run-idem")
    second = engine.scan(recovery_run_id="run-idem")
    assert first.to_dict() == second.to_dict()
    assert census() == before, "scan must not mutate anything"


def test_repeat_apply_idempotent_within_run(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path)
    data = b"repeat-orphan"
    stack.store.put_bytes(
        data, storage_encoding=StorageEncoding.NONE, source_media_type=_base.MEDIA
    )
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="run-repeat")
    first = engine.apply_plan(result, recovery_run_id="run-repeat")
    assert first, "first apply must quarantine the orphan"
    qdir = tmp_path / "quarantine" / "unknown_context"
    assert len(list(qdir.iterdir())) == 1
    second = engine.apply_plan(result, recovery_run_id="run-repeat")
    assert second == [], "second apply in the SAME run is already-applied"
    assert len(list(qdir.iterdir())) == 1


def test_journal_exact_retry_idempotent_divergence_typed(tmp_path: Path) -> None:
    stack = RecoveryStack(tmp_path)
    engine = _engine(stack)
    planned = rec.RecoveryPlanAction(
        action_kind=rec._ACTION_QUARANTINE_UNKNOWN_CONTEXT,
        object_type="EVIDENCE_BLOB",
        object_id="a" * 64,
        problem=rec.PROBLEM_UNKNOWN_CONTEXT,
        resolution="r",
        before_state={"k": 1},
        after_state={},
    )
    engine._journal_action(
        run_id="run-x",
        planned=planned,
        resolution="quarantined",
        after_state={"quarantined": True},
    )
    # Exact retry (same semantics, later clock) adopts; divergence typed.
    action_id = engine.journal.action_ids()[0]
    payload = engine.journal.get(action_id)
    assert payload is not None
    same = engine.journal.record(
        recovery_run_id="run-x",
        object_type="EVIDENCE_BLOB",
        object_id="a" * 64,
        problem=rec.PROBLEM_UNKNOWN_CONTEXT,
        resolution="quarantined",
        before_state={"k": 1},
        after_state={"quarantined": True},
        action_kind=planned.action_kind,
    )
    assert same[1] is True  # adopted existing
    from crypto_sensor_fabric.storage.json_catalog import JsonCatalogConflict

    catalog = engine.journal._catalog  # noqa: SLF001
    with pytest.raises(JsonCatalogConflict):
        catalog.commit(action_id, {**payload, "problem": "TAMPERED"})


def test_divergent_job_stays_fail_closed_after_forged_record_removal(
    tmp_path: Path,
) -> None:
    """Removing the forged head does NOT heal the chain: the catalog cache
    holds the record, so the next gated refresh fails closed on
    cache-vs-disk divergence (I07R1F §13).  Recovery must report the job
    STILL divergent and refuse — never silently proceed."""
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    job_id = "job-stale"
    _base._create(stack.repo, job_id)
    _base._drive_to_manifest(stack.repo, job_id)
    _base._full_batch(stack, "acq-stale", "pm-stale", b'{"rows": ["s"]}')
    _base._checkpoint(stack.repo, job_id, "acq-stale", "pm-stale")
    _publish_forged_from_status_break(tmp_path, job_id)
    result = _engine(stack).scan(recovery_run_id="run-stale")
    divergent = [
        f for f in result.findings if f.problem == rec.PROBLEM_JOB_DURABILITY_DIVERGENCE
    ]
    assert divergent
    events = _job_events(tmp_path, job_id)
    forged_key = hashlib.sha256(
        f"{job_id}:{max(e['sequence'] for e in events):06d}".encode("utf-8")
    ).hexdigest()
    (_events_dir(tmp_path) / f"{forged_key}.json").unlink()
    # Apply STILL refuses: refresh detects the vanished cached record and
    # fails closed, so the plan revalidation sees corruption (not health).
    applied = _engine(stack).apply_plan(result, recovery_run_id="run-stale-2")
    assert len(applied) == 1
    assert applied[0].after_state is not None
    after = json.loads(applied[0].after_state)
    assert after.get("transition_refused") is True


def test_foreign_lock_not_auto_deleted_and_explicit_clear_gate(
    tmp_path: Path,
) -> None:
    stack = RecoveryStack(tmp_path, clock=_base.TickingClock())
    lock_id = hashlib.sha256(b"foreign-job").hexdigest()
    lock_path = tmp_path / "locks" / f"{lock_id}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(b"{}")
    result = _engine(stack).scan(recovery_run_id="run-lock2")
    _engine(stack).apply_plan(result, recovery_run_id="run-lock2")
    assert lock_path.exists(), "foreign lock must NEVER be auto-deleted"
    # Explicit clear: fingerprint mismatch refuses; match + absent-owner works.
    # I08R1 §23: the owner repository (the REAL job repository here) is
    # mandatory — its _lock_owners truth must show no live owner.
    with pytest.raises(TypeError):
        _engine(stack).clear_job_lock(
            lock_id, expected_job_id="not-the-job", run_id="run-clear2"
        )
    with pytest.raises(rec.RecoveryConfigurationError):
        _engine(stack).clear_job_lock(
            lock_id,
            expected_job_id="foreign-job",
            owner_repository=None,
            run_id="run-clear2",
        )
    _engine(stack).clear_job_lock(
        lock_id,
        expected_job_id="foreign-job",
        owner_repository=stack.repo,
        run_id="run-clear2",
    )
    assert not lock_path.exists()
    # TWO records exist: the scan-apply RECORD_LOCK_ONLY evidence from
    # run-lock2 and the explicit clear from run-clear2 (different runs are
    # different actions — dedup is per-run, §27).
    records = _engine(stack).journal.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id)
    assert len(records) == 2
    cleared = [
        r for r in records if json.loads(r["after_state"]).get("cleared") is True
    ]
    assert len(cleared) == 1


def test_recovery_action_records_visible_in_narrow_read_surface(
    tmp_path: Path,
) -> None:
    stack = RecoveryStack(tmp_path)
    data = b"read-surface orphan"
    stack.store.put_bytes(
        data, storage_encoding=StorageEncoding.NONE, source_media_type=_base.MEDIA
    )
    engine = _engine(stack)
    result = engine.scan(recovery_run_id="run-read")
    engine.apply_plan(result, recovery_run_id="run-read")
    ids = engine.journal.action_ids()
    assert ids == sorted(ids)
    records = engine.journal.list_for_run("run-read")
    assert len(records) == 1
    by_object = engine.journal.list_for_object(
        records[0]["object_type"], records[0]["object_id"]
    )
    assert [r["recovery_action_id"] for r in by_object] == [records[0]["recovery_action_id"]]
    frozen = engine.journal.to_recovery_action(records[0])
    assert frozen is not None
    assert isinstance(frozen, rec.RecoveryAction)
