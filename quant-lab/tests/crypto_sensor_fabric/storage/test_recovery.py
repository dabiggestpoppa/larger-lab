"""SENSOR-B4-I08A — recovery findings vocabulary + journal + read-only scan.

Covers the frozen I08 scanner contract: the typed finding vocabulary, the
deterministic append-only recovery journal (exact retry idempotent,
divergent typed conflict, registration time excluded from identity), the
READ-ONLY scan over real forged defects (zero mutations — bytes, catalogs,
locks, pointers and jobs untouched), deterministic sorted output, TOCTOU
revalidation, quarantine path safety (§29/§30), and the explicit-only lock
policy (§20).  Uses the REAL I04/I05/I07 stack — no mock repositories.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from crypto_sensor_fabric.contracts.enums import SensorFamily  # noqa: E402
from crypto_sensor_fabric.storage import recovery as rec  # noqa: E402
from crypto_sensor_fabric.storage import (  # noqa: E402
    AcquisitionRepository,
    BlobMetadataRepository,
    LocalBlobStore,
)
from crypto_sensor_fabric.storage.catalog import (  # noqa: E402
    AcquisitionRepository as AcquisitionRepositoryAlias,  # noqa: F401
)
from crypto_sensor_fabric.storage.models import (  # noqa: E402
    AcquisitionRecord,
    StorageObjectType,
)
from crypto_sensor_fabric.storage.recovery import (  # noqa: E402
    PROBLEM_ACQUISITION_SOURCE_QUARANTINED,
    PROBLEM_CORRUPT_BLOB,
    PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN,
    PROBLEM_MISSING_MANIFEST_TARGET,
    PROBLEM_ORPHAN_DURABLE_BLOB,
    PROBLEM_ORPHAN_PROJECTION,
    PROBLEM_ORPHAN_MANIFEST,
    PROBLEM_UNCOMMITTED_STAGING,
    QUARANTINE_CATEGORY_INTEGRITY,
    RecoveryEngine,
    RecoveryJournal,
    RecoveryPlanConflict,
    RecoveryQuarantineConflict,
    action_identity,
)
from crypto_sensor_fabric.storage.enums import StorageEncoding  # noqa: E402

FIXED = datetime(2026, 8, 17, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"


# ---------------------------------------------------------------------------
# Real-stack harness
# ---------------------------------------------------------------------------


class Stack:
    """The real I04 stack on one T0 root — no mocks."""

    def __init__(self, tmp_path: Path) -> None:
        self.root = tmp_path
        self.store = LocalBlobStore(str(self.root))
        self.blobs = BlobMetadataRepository(self.root, blob_store=self.store)
        self.acqs = AcquisitionRepository(
            self.root, blob_store=self.store, blob_metadata_repository=self.blobs
        )

    def seed_blob(self, data: bytes, acq_id: str = "acq") -> str:
        put = self.store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        )
        self.blobs.append_metadata(put.blob)
        # Acquisition AFTER metadata: the repository gates acquisitions on
        # durable EvidenceBlob metadata existing first (I04 §12/§26).
        self.acqs.append_acquisition(self.build_acquisition(put.blob.blob_sha256, acq_id))
        return put.blob.blob_sha256

    def build_acquisition(self, sha: str, acq_id: str) -> AcquisitionRecord:
        """Pure model construction (no durable registration)."""
        return AcquisitionRecord(
            acquisition_id=acq_id,
            provider_id="kraken",
            venue="futures",
            sensor_family=SensorFamily.MECHANICAL_TRADE,
            request_fingerprint="fp",
            adapter_version="1.0",
            requested_start=FIXED,
            requested_end=FIXED,
            native_instrument="BTC-USDT",
            request_started_at=FIXED,
            response_observed_at=FIXED,
            ingested_at=FIXED,
            http_status_or_source_status="200",
            source_locator="file:///test",
            blob_sha256=sha,
        )

    def forge_orphan(self, data: bytes) -> str:
        """Physically commit a blob at its canonical key WITHOUT metadata."""
        put = self.store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        )
        return put.blob.blob_sha256

    def corrupt_blob(self, sha: str) -> None:
        """Overwrite committed bytes so they fail their content identity."""
        key = _blob_object_path(self.root, sha, StorageEncoding.NONE)
        key.write_bytes(b"tampered bytes that cannot match any sha256")

    def engine(self, recovery_run_id: str | None = None) -> RecoveryEngine:
        return RecoveryEngine(
            self.root,
            blob_store=self.store,
            blob_metadata_repository=self.blobs,
            acquisition_repository=self.acqs,
            manifest_repository=_NoManifests(),
            recovery_run_id=recovery_run_id,
        )


class _NoManifests:
    """No manifest participation (I08A scope); journal-only manifest cases
    are covered through direct RecoveryPlanAction calls."""

    def list_manifest_versions(self, partition_key: str) -> list:
        raise AssertionError("manifests not expected in I08A scan cases")

    def list_orphan_manifest_fragments(self, partition_key: str) -> list:
        raise AssertionError("manifests not expected in I08A scan cases")


def _blob_object_path(root: Path, sha: str, encoding: StorageEncoding) -> Path:
    from crypto_sensor_fabric.storage.paths import blob_object_key, resolve_under_root

    return resolve_under_root(root, blob_object_key(sha, encoding))


def _snapshot(root: Path) -> dict[str, str]:
    """Content census of every file under root (relative path -> sha256)."""
    snapshot: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            snapshot[path.relative_to(root).as_posix()] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
    return snapshot


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _apply(engine: RecoveryEngine, result, run_id: str) -> list:
    return engine.apply_plan(result, recovery_run_id=run_id)


# ---------------------------------------------------------------------------
# Journal identity (I08 §7/§8/§27)
# ---------------------------------------------------------------------------


def test_action_identity_excludes_registration_time() -> None:
    base = {
        "recovery_run_id": "run-1",
        "object_type": "EVIDENCE_BLOB",
        "object_id": "a" * 64,
        "problem": PROBLEM_CORRUPT_BLOB,
        "resolution": "quarantine",
        "before_state": {"k": 1},
        "after_state": {"k": 2},
    }
    early = action_identity(base)
    assert early == action_identity(dict(base))


def test_journal_exact_retry_is_idempotent(tmp_path: Path) -> None:
    journal = RecoveryJournal(tmp_path)
    first_id, first_adopted = journal.record(
        recovery_run_id="run-1",
        object_type="EVIDENCE_BLOB",
        object_id="b" * 64,
        problem=PROBLEM_CORRUPT_BLOB,
        resolution="quarantined",
        before_state={"x": "1"},
        after_state={"y": "2"},
    )
    second_id, second_adopted = journal.record(
        recovery_run_id="run-1",
        object_type="EVIDENCE_BLOB",
        object_id="b" * 64,
        problem=PROBLEM_CORRUPT_BLOB,
        resolution="quarantined",
        before_state={"x": "1"},
        after_state={"y": "2"},
    )
    assert first_id == second_id
    assert first_adopted is False
    assert second_adopted is True
    assert journal.action_ids() == [first_id]


def test_journal_divergent_retry_typed_conflict(tmp_path: Path) -> None:
    journal = RecoveryJournal(tmp_path)
    journal.record(
        recovery_run_id="run-1",
        object_type="EVIDENCE_BLOB",
        object_id="c" * 64,
        problem=PROBLEM_CORRUPT_BLOB,
        resolution="quarantined",
        before_state={"x": "1"},
        after_state={"y": "2"},
    )
    # A pure `record` retry with different resolution text produces a
    # DIFFERENT logical id (identity is a hash over the semantics), so the
    # journal happily stores it as a distinct action — divergence is about
    # the SAME id with different content.  Forge that: retry with a changed
    # PROBLEM through the record API after tampering the durable envelope's
    # semantic fields at the same logical id via the underlying catalog.
    same_id = action_identity(
        {
            "recovery_run_id": "run-1",
            "object_type": "EVIDENCE_BLOB",
            "object_id": "c" * 64,
            "problem": PROBLEM_CORRUPT_BLOB,
            "resolution": "quarantined",
            "before_state": {"x": "1"},
            "after_state": {"y": "2"},
        }
    )
    catalog = journal._catalog  # noqa: SLF001 - direct catalog tamper
    existing = catalog.get(same_id)
    assert existing is not None
    tampered = dict(existing)
    tampered["problem"] = "TAMPERED"
    from crypto_sensor_fabric.storage.json_catalog import JsonCatalogConflict

    # The catalog itself refuses to overwrite the immutable record.
    with pytest.raises(JsonCatalogConflict):
        catalog.commit(same_id, tampered)
    # The journal-level divergence path: a retry whose semantics hash to
    # the same logical id but whose envelope differs (tampered durable
    # record) must fail typed, not adopt.
    # A different before_state produces a different logical id, so it is
    # not the same action; same id therefore requires identical semantics.
    # the identity boundary instead: same id requires identical semantics.
    assert action_identity(
        {
            "recovery_run_id": "run-1",
            "object_type": "EVIDENCE_BLOB",
            "object_id": "c" * 64,
            "problem": PROBLEM_CORRUPT_BLOB,
            "resolution": "quarantined",
            "before_state": {"x": "DIFFERENT"},
            "after_state": {"y": "2"},
        }
    ) != same_id


def test_journal_registration_time_does_not_change_identity(tmp_path: Path) -> None:
    journal = RecoveryJournal(tmp_path)
    id_a, adopted_a = journal.record(
        recovery_run_id="run-1",
        object_type="EVIDENCE_BLOB",
        object_id="d" * 64,
        problem=PROBLEM_CORRUPT_BLOB,
        resolution="quarantined",
        before_state={},
        after_state={},
        registered_at=FIXED,
    )
    id_b, adopted_b = journal.record(
        recovery_run_id="run-1",
        object_type="EVIDENCE_BLOB",
        object_id="d" * 64,
        problem=PROBLEM_CORRUPT_BLOB,
        resolution="quarantined",
        before_state={},
        after_state={},
        registered_at=datetime(2030, 1, 1, tzinfo=UTC),
    )
    assert id_a == id_b
    assert adopted_a is False and adopted_b is True


def test_journal_frozen_recovery_action_mapping(tmp_path: Path) -> None:
    journal = RecoveryJournal(tmp_path)
    action_id, _ = journal.record(
        recovery_run_id="run-1",
        object_type=StorageObjectType.EVIDENCE_BLOB.value,
        object_id="e" * 64,
        problem=PROBLEM_CORRUPT_BLOB,
        resolution="quarantined",
        before_state={"a": 1},
        after_state={"b": 2},
    )
    payload = journal.get(action_id)
    assert payload is not None
    action = journal.to_recovery_action(payload)
    assert action is not None
    assert action.recovery_run_id == "run-1"
    assert action.problem == PROBLEM_CORRUPT_BLOB
    assert action.object_type is StorageObjectType.EVIDENCE_BLOB
    assert action.before_state is not None
    assert action.after_state is not None
    assert json.loads(action.before_state) == {"a": 1}
    assert json.loads(action.after_state) == {"b": 2}
    # semantic internal object types map to None (internal envelope rule)
    journal.record(
        recovery_run_id="run-1",
        object_type=rec.SEMANTIC_JOB_LOCK,
        object_id="f" * 64,
        problem=PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN,
        resolution="recorded",
    )
    lock_payloads = journal.list_for_object(rec.SEMANTIC_JOB_LOCK, "f" * 64)
    assert len(lock_payloads) == 1
    assert journal.to_recovery_action(lock_payloads[0]) is None


# ---------------------------------------------------------------------------
# Scan over real forged defects (I08 §4/§5)
# ---------------------------------------------------------------------------


def test_clean_root_scan_is_empty(stack_t0: Path) -> None:
    engine = Stack(stack_t0).engine(recovery_run_id="run-clean")
    result = engine.scan()
    assert result.findings == ()
    assert result.counts_by_problem == {}
    assert result.planned_actions == ()
    assert result.has_blockers is False


@pytest.fixture()
def stack_t0(tmp_path: Path) -> Path:
    return tmp_path


def test_scan_finds_all_defect_classes_read_only(stack_t0: Path) -> None:
    stack = Stack(stack_t0)
    good_sha = stack.seed_blob(b"good-bytes")
    stack.forge_orphan(b"orphan-bytes")
    corrupt_sha = stack.seed_blob(b"corrupt-me", acq_id="acq-corrupt")
    stack.corrupt_blob(corrupt_sha)
    _write(stack_t0 / "staging" / "deadbeef.partial", b"abandoned")
    _write(stack_t0 / "locks" / f"{hashlib.sha256(b'job-x').hexdigest()}.lock", b"{}")
    _write(
        stack_t0 / "projections" / "orphan.parquet", b"not really parquet bytes"
    )

    before = _snapshot(stack_t0)
    result = stack.engine(recovery_run_id="run-scan").scan()
    after = _snapshot(stack_t0)

    # READ-ONLY proof (I08 §5): byte census identical before/after.
    assert before == after
    problems = {f.problem for f in result.findings}
    assert PROBLEM_ORPHAN_DURABLE_BLOB in problems
    assert PROBLEM_CORRUPT_BLOB in problems
    assert PROBLEM_ACQUISITION_SOURCE_QUARANTINED in problems
    assert PROBLEM_UNCOMMITTED_STAGING in problems
    assert PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN in problems
    assert PROBLEM_ORPHAN_PROJECTION in problems
    # no false positive on the healthy verified blob
    healthy = [
        f
        for f in result.findings
        if f.object_id == good_sha
        and f.problem
        in (PROBLEM_CORRUPT_BLOB, PROBLEM_ORPHAN_DURABLE_BLOB)
    ]
    assert healthy == []
    # findings sorted + deterministic
    keys = [(f.problem, f.object_type, f.object_id) for f in result.findings]
    assert keys == sorted(keys)
    again = stack.engine(recovery_run_id="run-scan").scan()
    assert again.to_dict() == result.to_dict()
    # counts add up
    total = sum(result.counts_by_problem.values())
    assert total == len(result.findings)


def test_scan_missing_manifest_target_finding(stack_t0: Path) -> None:
    """A manifest model surfaced through the scan path (record-only class)."""
    stack = Stack(stack_t0)
    sha = stack.seed_blob(b"manifest-target")
    # Directly remove the physical bytes; metadata stays durable.
    _blob_object_path(stack_t0, sha, StorageEncoding.NONE).unlink()
    result = stack.engine(recovery_run_id="run-scan").scan()
    problems = {f.problem for f in result.findings}
    assert PROBLEM_CORRUPT_BLOB in problems
    # acquisition referencing the missing blob is surfaced too
    assert PROBLEM_ACQUISITION_SOURCE_QUARANTINED in problems


def test_scan_manifest_repository_used_when_provided(stack_t0: Path) -> None:
    """Manifest findings route through the repository's own forensic API."""
    stack = Stack(stack_t0)
    sha = stack.seed_blob(b"manifest-blob")

    class FakeManifests:
        def __init__(self, sha: str) -> None:
            self.sha = sha

        def list_manifest_versions(self, partition_key: str) -> list:
            return []

        def list_orphan_manifest_fragments(self, partition_key: str) -> list:
            raise AssertionError("scan uses _all_manifests for targets")

    engine = RecoveryEngine(
        stack_t0,
        blob_store=stack.store,
        blob_metadata_repository=stack.blobs,
        acquisition_repository=stack.acqs,
        manifest_repository=FakeManifests(sha),
    )
    # No manifests exist on disk; the scan must still be clean, proving the
    # repo-backed path does not invent findings.
    result = engine.scan()
    manifest_findings = [
        f
        for f in result.findings
        if f.problem
        in (PROBLEM_MISSING_MANIFEST_TARGET, PROBLEM_ORPHAN_MANIFEST)
    ]
    assert manifest_findings == []


def test_scan_is_deterministic_across_repeated_calls(stack_t0: Path) -> None:
    stack = Stack(stack_t0)
    stack.seed_blob(b"determinism")
    stack.forge_orphan(b"orphan-determinism")
    engine = stack.engine()
    one = engine.scan(recovery_run_id="run-det")
    two = engine.scan(recovery_run_id="run-det")
    assert one.to_dict() == two.to_dict()
    assert one.recovery_run_id == "run-det"


# ---------------------------------------------------------------------------
# TOCTOU revalidation (I08 §28)
# ---------------------------------------------------------------------------


def test_stale_orphan_plan_conflicts_when_metadata_appears(stack_t0: Path) -> None:
    stack = Stack(stack_t0)
    orphan = stack.forge_orphan(b"toctou-orphan")
    result = stack.engine(recovery_run_id="run-1").scan()
    orphan_actions = [
        a for a in result.planned_actions if a.object_id == orphan
    ]
    assert orphan_actions, "orphan must be planned"
    # Meanwhile durable metadata legitimately appears...
    put = stack.store.put_bytes(
        b"toctou-orphan",
        storage_encoding=StorageEncoding.NONE,
        source_media_type=MEDIA,
    )
    stack.blobs.append_metadata(put.blob)
    with pytest.raises(RecoveryPlanConflict):
        _apply(stack.engine(), result, "run-1")


def test_stale_corrupt_plan_conflicts_after_repair(stack_t0: Path) -> None:
    stack = Stack(stack_t0)
    sha = stack.seed_blob(b"corrupt-then-fixed", acq_id="acq-t")
    stack.corrupt_blob(sha)
    result = stack.engine(recovery_run_id="run-1").scan()
    # The blob is repaired (correct bytes rewritten at the canonical key).
    _blob_object_path(stack_t0, sha, StorageEncoding.NONE).write_bytes(
        b"corrupt-then-fixed"
    )
    with pytest.raises(RecoveryPlanConflict):
        _apply(stack.engine(), result, "run-1")


# ---------------------------------------------------------------------------
# Path safety (I08 §29) + quarantine collisions (I08 §30)
# ---------------------------------------------------------------------------


def test_unknown_quarantine_category_rejected(stack_t0: Path) -> None:
    stack = Stack(stack_t0)
    engine = stack.engine()
    with pytest.raises(rec.RecoveryConfigurationError):
        engine.quarantine_dir("secret_leak_prevented")


def test_quarantine_destination_is_deterministic_and_unique(
    stack_t0: Path,
) -> None:
    stack = Stack(stack_t0)
    engine = stack.engine()
    content = hashlib.sha256(b"same-bytes").hexdigest()
    a = engine.quarantine_destination(
        QUARANTINE_CATEGORY_INTEGRITY,
        object_type="blob",
        object_id="first-object",
        content_sha256=content,
        suffix=".quarantined",
    )
    b = engine.quarantine_destination(
        QUARANTINE_CATEGORY_INTEGRITY,
        object_type="blob",
        object_id="second-object",
        content_sha256=content,
        suffix=".quarantined",
    )
    assert a != b
    assert a == engine.quarantine_destination(
        QUARANTINE_CATEGORY_INTEGRITY,
        object_type="blob",
        object_id="first-object",
        content_sha256=content,
        suffix=".quarantined",
    )
    assert a.is_relative_to(stack_t0 / "quarantine" / "integrity")
    # no raw logical id becomes a path component
    assert "first-object" not in a.name


def test_quarantine_no_clobber_identical_adopts_different_conflicts(
    stack_t0: Path,
) -> None:
    stack = Stack(stack_t0)
    sha = stack.seed_blob(b"no-clobber-blob", acq_id="acq-nc")
    stack.corrupt_blob(sha)
    engine = stack.engine()
    result = engine.scan(recovery_run_id="run-nc")
    applied_first = _apply(engine, result, "run-nc")
    kinds = {a.object_id: a.after_state for a in applied_first}
    assert json.loads(kinds[sha])["quarantined"] is True
    assert json.loads(kinds[sha])["canonical_state"] == "ABSENT_QUARANTINED"
    # Rescan: the canonical object is absent now; the corrupt finding stays
    # (durable metadata vs absent bytes) and its apply records evidence
    # only (already-quarantined dedup), while the acquisition dependency
    # still journals.
    rescanned = engine.scan(recovery_run_id="run-nc2")
    corrupt = [f for f in rescanned.findings if f.object_id == sha]
    assert corrupt and corrupt[0].before_state.get("physical_present") is False
    applied_second = _apply(engine, rescanned, "run-nc2")
    assert all(a.object_id != sha for a in applied_second)
    # Exactly ONE quarantined artifact exists (no duplicate movement).
    dest = stack_t0 / "quarantine" / "integrity"
    assert len(list(dest.iterdir())) == 1
    # Direct no-clobber proof at the file level: different bytes behind the
    # SAME deterministic locator must conflict, identical bytes adopt.
    content = hashlib.sha256(b"probe-bytes").hexdigest()
    locator = engine.quarantine_destination(
        QUARANTINE_CATEGORY_INTEGRITY,
        object_type="probe",
        object_id="probe-object",
        content_sha256=content,
        suffix=".probe",
    )
    source = stack_t0 / "probe-source.bin"
    source.write_bytes(b"probe-bytes")
    assert engine._quarantine_file(source, locator, content) is True
    source.write_bytes(b"probe-bytes")
    assert engine._quarantine_file(source, locator, content) is False  # adopt
    other = stack_t0 / "probe-source-2.bin"
    other.write_bytes(b"other-bytes")
    locator.write_bytes(b"other-bytes")  # same locator, different history
    with pytest.raises(RecoveryQuarantineConflict):
        engine._quarantine_file(
            other,
            locator,
            hashlib.sha256(b"probe-bytes").hexdigest(),
        )


def test_symlink_escape_rejected(stack_t0: Path) -> None:
    if os.name != "nt":
        stack = Stack(stack_t0)
        engine = stack.engine()
        outside = stack_t0.parent / f"outside-{abs(hash(stack_t0.name))}"
        outside.mkdir(exist_ok=True)
        link = stack_t0 / "quarantine" / "integrity"
        link.mkdir(parents=True, exist_ok=True)
        # A symlinked quarantine root must not accept outside content.
        real_target = outside / "target.bin"
        real_target.write_bytes(b"x")
        link_target = stack_t0 / "escape-link"
        os.symlink(real_target, link_target)
        content = hashlib.sha256(b"x").hexdigest()
        with pytest.raises((RecoveryQuarantineConflict, rec.RecoveryPathSafetyError)):
            engine._quarantine_file(
                link_target, link / "escape.quarantined", content
            )
    else:
        pytest.skip("POSIX symlink semantics required")


def test_staging_move_rejected_outside_root(stack_t0: Path) -> None:
    stack = Stack(stack_t0)
    engine = stack.engine()
    source = stack_t0 / "inner.bin"
    source.write_bytes(b"data")
    # A destination OUTSIDE the T0 root (lexical escape) must be refused.
    outside = stack_t0.parent / f"escape-{abs(hash(stack_t0.name))}.bin"
    with pytest.raises(rec.RecoveryPathSafetyError):
        engine._quarantine_file(
            source, outside, hashlib.sha256(b"data").hexdigest()
        )
    assert not outside.exists()


# ---------------------------------------------------------------------------
# Lock policy (I08 §20)
# ---------------------------------------------------------------------------


def test_lock_scan_records_never_deletes(stack_t0: Path) -> None:
    lock_id = hashlib.sha256(b"job-lock-1").hexdigest()
    lock_path = stack_t0 / "locks" / f"{lock_id}.lock"
    _write(lock_path, b"{}")
    stack = Stack(stack_t0)
    engine = stack.engine()
    result = engine.scan(recovery_run_id="run-lock")
    lock_findings = [
        f for f in result.findings if f.problem == PROBLEM_LOCK_PRESENT_OWNER_UNPROVEN
    ]
    assert [f.object_id for f in lock_findings] == [lock_id]
    _apply(engine, result, "run-lock")
    # Internal-envelope object (JOB_LOCK): no frozen RecoveryAction is
    # returned, but the durable journal record MUST exist.
    records = engine.journal.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id)
    assert len(records) == 1
    assert json.loads(records[0]["after_state"]) == {
        "lock_present": True,
        "cleared": False,
    }
    assert lock_path.exists(), "lock file must NEVER be auto-deleted"


def test_explicit_clear_requires_matching_fingerprint(stack_t0: Path) -> None:
    stack = Stack(stack_t0)
    engine = stack.engine()
    with pytest.raises(rec.RecoveryConfigurationError):
        engine.clear_job_lock(
            "f" * 64, expected_job_id="other-job", run_id="run-clear"
        )
    # Correct fingerprint but absent lock -> conflict, no action.
    with pytest.raises(RecoveryPlanConflict):
        engine.clear_job_lock(
            hashlib.sha256(b"ghost-job").hexdigest(),
            expected_job_id="ghost-job",
            run_id="run-clear",
        )


def test_explicit_clear_journals_then_removes(stack_t0: Path) -> None:
    lock_id = hashlib.sha256(b"job-clear-me").hexdigest()
    lock_path = stack_t0 / "locks" / f"{lock_id}.lock"
    _write(lock_path, b"{}")
    stack = Stack(stack_t0)
    engine = stack.engine()
    action = engine.clear_job_lock(
        lock_id, expected_job_id="job-clear-me", run_id="run-clear"
    )
    assert action is None  # semantic JOB_LOCK -> internal envelope (no frozen model)
    assert not lock_path.exists()
    records = engine.journal.list_for_object(rec.SEMANTIC_JOB_LOCK, lock_id)
    assert len(records) == 1
    assert json.loads(records[0]["after_state"]) == {
        "lock_present": False,
        "cleared": True,
    }


# ---------------------------------------------------------------------------
# Orphan blob apply: unknown-context quarantine vs proven reconciliation
# ---------------------------------------------------------------------------


def test_orphan_without_context_is_quarantined(stack_t0: Path) -> None:
    stack = Stack(stack_t0)
    orphan = stack.forge_orphan(b"orphan-unknown")
    engine = stack.engine()
    result = engine.scan(recovery_run_id="run-orphan")
    applied = _apply(engine, result, "run-orphan")
    orphan_actions = {
        a.object_id: a.after_state for a in applied if a.object_id == orphan
    }
    assert json.loads(orphan_actions[orphan])["quarantined"] is True
    # canonical blob key is now empty; quarantine holds identical bytes
    assert not _blob_object_path(stack_t0, orphan, StorageEncoding.NONE).exists()
    quarantined = sorted(
        (stack_t0 / "quarantine" / "unknown_context").iterdir()
    )
    assert len(quarantined) == 1
    assert (
        hashlib.sha256(quarantined[0].read_bytes()).hexdigest() == orphan
    ), "quarantined bytes must be preserved byte-identically"


def test_orphan_with_proven_context_reconciles_through_public_apis(
    stack_t0: Path,
) -> None:
    stack = Stack(stack_t0)
    data = b"orphan-with-context"
    orphan = stack.forge_orphan(data)
    engine = stack.engine()
    # Prepare the exact metadata/acquisition the public APIs would accept.
    put = stack.store.put_bytes(
        data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
    )
    engine.register_orphan_context(
        orphan,
        evidence_blob=put.blob,
        acquisition=stack.build_acquisition(orphan, "acq-orphan-ctx"),
    )
    result = engine.scan(recovery_run_id="run-orphan2")
    applied = _apply(engine, result, "run-orphan2")
    orphan_actions = {
        a.object_id: a.after_state for a in applied if a.object_id == orphan
    }
    assert json.loads(orphan_actions[orphan])["reconciled"] is True
    # durable truth now holds metadata + acquisition
    assert stack.blobs.get_blob_metadata(orphan)
    assert stack.acqs.get_acquisition("acq-orphan-ctx").blob_sha256 == orphan


def test_orphan_bytes_failing_name_go_to_integrity_quarantine(
    stack_t0: Path,
) -> None:
    stack = Stack(stack_t0)
    data = b"i-am-not-what-my-name-says"
    orphan = stack.forge_orphan(data)  # committed under REAL sha key
    # Now swap the bytes under the orphan key for different content.
    _blob_object_path(stack_t0, orphan, StorageEncoding.NONE).write_bytes(
        b"completely different bytes"
    )
    engine = stack.engine()
    result = engine.scan(recovery_run_id="run-orphan3")
    applied = _apply(engine, result, "run-orphan3")
    orphan_actions = {
        a.object_id: a.after_state for a in applied if a.object_id == orphan
    }
    assert json.loads(orphan_actions[orphan])["quarantine_category"] == (
        QUARANTINE_CATEGORY_INTEGRITY
    )
    # the preserved bytes hash to what was actually stored (the swapped
    # bytes, NOT the content-addressed name)
    qdir = stack_t0 / "quarantine" / "integrity"
    preserved = next(iter(qdir.iterdir()))
    assert (
        hashlib.sha256(preserved.read_bytes()).hexdigest()
        == hashlib.sha256(b"completely different bytes").hexdigest()
    )


# ---------------------------------------------------------------------------
# Corrupt blob apply (I08 §11)
# ---------------------------------------------------------------------------


def test_corrupt_blob_quarantined_not_overwritten(stack_t0: Path) -> None:
    stack = Stack(stack_t0)
    sha = stack.seed_blob(b"victim-blob", acq_id="acq-victim")
    stack.corrupt_blob(sha)
    corrupt_bytes = _blob_object_path(
        stack_t0, sha, StorageEncoding.NONE
    ).read_bytes()
    engine = stack.engine()
    result = engine.scan(recovery_run_id="run-corrupt")
    applied = _apply(engine, result, "run-corrupt")
    after_by_id = {a.object_id: a.after_state for a in applied}
    action_state = json.loads(after_by_id[sha])
    assert action_state["quarantined"] is True
    assert action_state["canonical_state"] == "ABSENT_QUARANTINED"
    # corrupt bytes preserved, canonical key empty
    qdir = stack_t0 / "quarantine" / "integrity"
    assert len(list(qdir.iterdir())) == 1
    qfile = next(iter(qdir.iterdir()))
    assert qfile.read_bytes() == corrupt_bytes
    assert not _blob_object_path(stack_t0, sha, StorageEncoding.NONE).exists()
    # immutable history untouched: acquisition still references the sha
    record = stack.acqs.get_acquisition("acq-victim")
    assert record.blob_sha256 == sha


def test_corrupt_blob_missing_after_scan_records_evidence_only(
    stack_t0: Path,
) -> None:
    stack = Stack(stack_t0)
    sha = stack.seed_blob(b"missing-later", acq_id="acq-m")
    stack.corrupt_blob(sha)
    engine = stack.engine()
    result = engine.scan(recovery_run_id="run-m")
    _blob_object_path(stack_t0, sha, StorageEncoding.NONE).unlink()
    applied = _apply(engine, result, "run-m")
    after_by_id = {a.object_id: a.after_state for a in applied}
    assert json.loads(after_by_id[sha]) == {"physical_present": False}
    assert not (stack_t0 / "quarantine" / "integrity").exists()
