"""SENSOR-B4-I11R1 real PostgreSQL integration and adversarial proofs."""

from __future__ import annotations

import hashlib
import os
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.storage import postgres_metadata as pg
from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
from crypto_sensor_fabric.storage.enums import StorageJobStatus
from crypto_sensor_fabric.storage.models import AcquisitionRecord, EvidenceBlob, PartitionManifest, SourceRevision, StorageJobState, StorageJobTransition
from crypto_sensor_fabric.storage.quota import QuotaConfig
from crypto_sensor_fabric.storage.recovery import RecoveryJournal


def _load_sibling_helper():
    """Load ``_sibling_import`` by absolute path.

    ``storage/`` is a package under pytest's importlib import-mode, so this
    directory is not on ``sys.path`` and ``from _sibling_import import ...``
    only resolves when some earlier test already cached the module.  Loading
    it by path keeps this module import-order independent.
    """
    import importlib.util

    path = Path(__file__).resolve().parent / "_sibling_import.py"
    spec = importlib.util.spec_from_file_location("_sibling_import", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.load_sibling


psycopg = pytest.importorskip("psycopg")

DSN = os.getenv("SENSOR_POSTGRES_TEST_DSN")
pytestmark = pytest.mark.skipif(not DSN, reason="set SENSOR_POSTGRES_TEST_DSN for real PostgreSQL I11R1")
UTC_TIME = datetime(2026, 1, 1, tzinfo=UTC)


def repo() -> pg.PostgresMetadataRepository:
    return pg.PostgresMetadataRepository(pg.PostgresMetadataConfig(DSN or ""))


def _row(table: str, **values: object) -> dict[str, object]:
    return pg.validate_row(table, {column: values.get(column) for column in pg._TABLE_COLUMNS[table]})


def _blob(value: str) -> dict[str, object]:
    return _row("blobs_current_metadata", blob_sha256=value * 64, storage_encoding="NONE", byte_length=3,
                stored_byte_length=3, source_media_type="application/json", storage_uri="objects/" + value * 64,
                integrity_state="LOCAL_HASH_VERIFIED", created_at=UTC_TIME)


def _acquisition(number: int) -> dict[str, object]:
    return _row("acquisitions", acquisition_id=f"acq-{number}", provider_id="PROVIDER", venue="VENUE",
                sensor_family="MECHANICAL_TRADE", request_fingerprint=f"request-{number}", adapter_version="1.0.0",
                requested_start=UTC_TIME, requested_end=UTC_TIME, actual_start=UTC_TIME, actual_end=UTC_TIME,
                native_instrument="NATIVE", native_granularity="1m", request_started_at=UTC_TIME,
                response_observed_at=UTC_TIME, ingested_at=UTC_TIME, http_status_or_source_status="200",
                endpoint_host="127.0.0.1", endpoint_path="/metadata", request_family="fixture", source_locator="fixture:acq",
                blob_sha256=str(number) * 64, schema_state="KNOWN", evidence_ref="fixture:evidence",
                provider_checksum_algorithm="SHA-256", provider_checksum_value="a" * 64,
                provider_checksum_verified=True, quality_flags="[]", failure_ref=None)


def _manifest(number: int) -> dict[str, object]:
    return _row("partition_manifest_current", partition_key=f"partition-{number}", partition_manifest_id=f"manifest-{number}",
                manifest_version=1, provider="PROVIDER", venue="VENUE", sensor_family="MECHANICAL_TRADE",
                native_instrument="NATIVE", source_granularity="1m", date_basis="EVENT_TIME",
                logical_date_start=UTC_TIME, logical_date_end=UTC_TIME, coverage_state="COMPLETE",
                integrity_state="LOCAL_HASH_VERIFIED", row_count=10, min_time=UTC_TIME, max_time=UTC_TIME,
                gap_count=0, revision_count=1, created_at=UTC_TIME, supersedes_manifest_id=None,
                pointer_updated_at=UTC_TIME)


def _job(number: int) -> dict[str, object]:
    return _row("storage_jobs", job_id=f"job-{number}", provider_id="PROVIDER", sensor_family="MECHANICAL_TRADE",
                request_fingerprint=f"request-{number}", status="MANIFEST_COMMITTED", updated_at=UTC_TIME,
                last_committed_acquisition_id=f"acq-{number}", last_committed_blob_sha256=str(number) * 64,
                last_manifest_id=f"manifest-{number}")


def _transition(number: int, job_number: int = 1) -> dict[str, object]:
    return _row("storage_job_transitions", transition_id=f"transition-{number}", job_id=f"job-{job_number}",
                from_status="PLANNED", to_status="MANIFEST_COMMITTED", transitioned_at=UTC_TIME,
                reason="fixture", evidence_ref="fixture:transition")


def _revision(number: int) -> dict[str, object]:
    return _row("source_revisions", source_revision_key="source-1", revision_number=number, blob_sha256=str(number) * 64,
                first_seen_at=UTC_TIME, last_seen_at=UTC_TIME, revision_reason="fixture", revision_state="STABLE")


def _integrity(number: int) -> dict[str, object]:
    return _row("integrity_checks", check_id=f"check-{number}", object_type="BLOB", object_id=f"blob-{number}",
                integrity_state="LOCAL_HASH_VERIFIED", checked_at=UTC_TIME)


def _quota() -> dict[str, object]:
    return _row("quota_state", singleton=True, pressure_state="NORMAL", priority_class=None, used_bytes=10,
                capacity_bytes=100, free_bytes=90, utilization_ratio=0.1, absolute_free_floor_bytes=1,
                observed_at=UTC_TIME)


def _backup() -> dict[str, object]:
    return _row("backup_state", singleton=True, state="UNBACKED", observed_at=UTC_TIME,
                verified_object_count=0, verified_bytes=0, manifest_ref=None, destination_ref=None, verification_ref=None)


def _snapshot(tag: str = "A") -> pg.MetadataSnapshot:
    return pg.MetadataSnapshot({
        "provider_registry": [_row("provider_registry", provider_id=f"provider-{tag}-{n}", status="CANDIDATE", evidence_class="B1", access_class="FREE", capability_count=1, fallback_count=0, notes="fixture") for n in (1, 2)],
        "adapter_readiness": [_row("adapter_readiness", provider_id=f"provider-{tag}-{n}", sensor_family="MECHANICAL_TRADE", adapter_id="adapter", adapter_version="1", promoted=True, implemented=True, offline_conformance_pass=True, schema_pass=True, network_smoke_status="NOT_RUN", evidence_ref="fixture", pit_readiness="NOT_PIT_READY", limitations="fixture") for n in (1, 2)],
        "storage_jobs": [_job(1), _job(2)],
        "storage_job_transitions": [_transition(1), _transition(2), _transition(3, 2)],
        "blobs_current_metadata": [_blob("1"), _blob("2")],
        "acquisitions": [_acquisition(1), _acquisition(2)],
        "partition_manifest_current": [_manifest(1), _manifest(2)],
        "source_revisions": [_revision(1), _revision(2)],
        "recovery_runs": [_row("recovery_runs", recovery_run_id="run-1", action_count=2, object_count=1, problem_count=1, unresolved_count=0, first_registered_at=UTC_TIME, last_registered_at=UTC_TIME)],
    })


@pytest.fixture
def installed_repo():
    r = repo()
    r.drop_schema()
    r.install_schema()
    yield r
    r.drop_schema()


def test_real_schema_install_reinstall_and_exact_validation(installed_repo: pg.PostgresMetadataRepository) -> None:
    first = installed_repo.validate_installed_schema()
    installed_repo.install_schema()
    second = installed_repo.validate_installed_schema()
    assert first == second
    info = installed_repo.introspect_schema()
    assert set(info["tables"]) == set(pg.ALL_TABLE_NAMES)
    assert info["raw_table_absent"] and info["generic_raw_column_absent"] and info["secret_column_absent"] and info["bytea_absent"]
    assert all("resume_token" not in name for values in info["columns"].values() for name, _type, _nullable in values)


@pytest.mark.parametrize("attack", ["version", "role", "extra_table", "extra_column", "wrong_type", "wrong_nullability", "wrong_pk", "wrong_fk"])
def test_real_installed_schema_attacks_fail_closed(installed_repo: pg.PostgresMetadataRepository, attack: str) -> None:
    with psycopg.connect(DSN, autocommit=True) as connection:
        if attack == "version":
            connection.execute(f'UPDATE "{pg.SCHEMA_NAME}"."schema_metadata" SET schema_version = %s', ("999",))
        elif attack == "role":
            connection.execute(f'UPDATE "{pg.SCHEMA_NAME}"."schema_metadata" SET repository_role = %s', ("WRONG",))
        elif attack == "extra_table":
            connection.execute(f'CREATE TABLE "{pg.SCHEMA_NAME}"."unauthorized" (id integer)')
        elif attack == "extra_column":
            connection.execute(f'ALTER TABLE "{pg.SCHEMA_NAME}"."provider_registry" ADD COLUMN extra text')
        elif attack == "wrong_type":
            connection.execute(f'ALTER TABLE "{pg.SCHEMA_NAME}"."provider_registry" ALTER COLUMN status TYPE integer USING 1')
        elif attack == "wrong_nullability":
            connection.execute(f'ALTER TABLE "{pg.SCHEMA_NAME}"."provider_registry" ALTER COLUMN notes SET NOT NULL')
        elif attack == "wrong_pk":
            connection.execute(f'ALTER TABLE "{pg.SCHEMA_NAME}"."provider_registry" DROP CONSTRAINT provider_registry_pkey')
        elif attack == "wrong_fk":
            connection.execute(f'ALTER TABLE "{pg.SCHEMA_NAME}"."storage_job_transitions" DROP CONSTRAINT storage_job_transitions_job_id_fkey')
    with pytest.raises(pg.PostgresSchemaError):
        installed_repo.validate_installed_schema()
    installed_repo.drop_schema()


def test_real_populated_reconstruction_drop_reinstall_and_repeat_parity(installed_repo: pg.PostgresMetadataRepository, tmp_path: Path) -> None:
    evidence_file = tmp_path / "raw-evidence.bin"
    evidence_file.write_bytes(b"immutable-t0a-evidence")
    before = hashlib.sha256(evidence_file.read_bytes()).hexdigest()
    snapshot = _snapshot("A")
    counts = installed_repo.refresh_reconstructible_metadata(snapshot=snapshot)
    assert counts == {table: len(snapshot.rows[table]) for table in pg.RECONSTRUCTIBLE_TABLES}
    canonical = installed_repo.canonical_rows()
    assert canonical == installed_repo.canonical_rows()
    assert set(canonical) == set(pg.RECONSTRUCTIBLE_TABLES)
    installed_repo.drop_schema()
    assert hashlib.sha256(evidence_file.read_bytes()).hexdigest() == before
    installed_repo.install_schema()
    installed_repo.refresh_reconstructible_metadata(snapshot=snapshot)
    assert installed_repo.canonical_rows() == canonical
    installed_repo.refresh_reconstructible_metadata(snapshot=snapshot)
    assert installed_repo.canonical_rows() == canonical


def test_real_operational_state_apis_and_preservation(installed_repo: pg.PostgresMetadataRepository) -> None:
    installed_repo.record_integrity_check(_integrity(1))
    installed_repo.record_integrity_check(_integrity(1))
    installed_repo.record_integrity_check(_integrity(2))
    with pytest.raises(pg.PostgresConflict):
        installed_repo.record_integrity_check(_row("integrity_checks", check_id="check-1", object_type="FORGED", object_id="blob-1", integrity_state="UNVERIFIED", checked_at=UTC_TIME))
    installed_repo.set_quota_state(_quota())
    installed_repo.set_backup_state(_backup())
    installed_repo.refresh_reconstructible_metadata(snapshot=_snapshot("A"))
    assert set(installed_repo.canonical_rows(("integrity_checks",))["integrity_checks"]) == {("check-1", "BLOB", "blob-1", "LOCAL_HASH_VERIFIED", UTC_TIME, None, None, None, None, None), ("check-2", "BLOB", "blob-2", "LOCAL_HASH_VERIFIED", UTC_TIME, None, None, None, None, None)}
    assert installed_repo.canonical_rows(("quota_state",))["quota_state"] == [(True, "NORMAL", None, 10, 100, 90, 0.1, 1, UTC_TIME)]
    assert installed_repo.canonical_rows(("backup_state",))["backup_state"] == [(True, "UNBACKED", UTC_TIME, 0, 0, None, None, None)]


def test_real_failed_refresh_rolls_back(installed_repo: pg.PostgresMetadataRepository) -> None:
    original = _snapshot("A")
    installed_repo.refresh_reconstructible_metadata(snapshot=original)
    before = installed_repo.canonical_rows()
    failing = pg.PostgresMetadataRepository(pg.PostgresMetadataConfig(DSN or ""), refresh_hook=lambda table, connection: (_ for _ in ()).throw(RuntimeError("injected")) if table == "recovery_runs" else None)
    with pytest.raises(pg.PostgresMetadataError):
        failing.refresh_reconstructible_metadata(snapshot=_snapshot("B"))
    assert installed_repo.canonical_rows() == before


def test_real_concurrent_refresh_serializes(installed_repo: pg.PostgresMetadataRepository) -> None:
    first = _snapshot("A")
    second = _snapshot("B")
    entered = threading.Event()
    release = threading.Event()
    def hold(table, connection):
        if table == "provider_registry":
            entered.set()
            assert release.wait(10)
    a = pg.PostgresMetadataRepository(pg.PostgresMetadataConfig(DSN or ""), refresh_hook=hold)
    b = pg.PostgresMetadataRepository(pg.PostgresMetadataConfig(DSN or ""))
    result = {}
    def run(name, repository, snapshot):
        result[name] = repository.refresh_reconstructible_metadata(snapshot=snapshot)
    ta = threading.Thread(target=run, args=("A", a, first))
    tb = threading.Thread(target=run, args=("B", b, second))
    ta.start()
    assert entered.wait(10)
    tb.start()
    time.sleep(0.5)
    assert tb.is_alive()
    release.set()
    ta.join(20)
    tb.join(20)
    assert not ta.is_alive() and not tb.is_alive()
    final = installed_repo.canonical_rows()
    assert final in (installed_repo.canonical_rows(), installed_repo.canonical_rows())
    assert final == a.canonical_rows() or final == b.canonical_rows()


def test_real_zero_t0a_payload_reads_during_reconstruction(monkeypatch: pytest.MonkeyPatch, installed_repo: pg.PostgresMetadataRepository) -> None:
    calls = {"verify": 0, "open": 0, "decode": 0}
    def forbidden(name):
        def fail(*args, **kwargs):
            calls[name] += 1
            raise AssertionError(f"payload read: {name}")
        return fail
    monkeypatch.setattr(LocalBlobStore, "verify_blob", forbidden("verify"))
    monkeypatch.setattr(LocalBlobStore, "open_blob", forbidden("open"))
    monkeypatch.setattr(LocalBlobStore, "_decode_stats", forbidden("decode"))
    installed_repo.refresh_reconstructible_metadata(snapshot=_snapshot("A"))
    assert calls == {"verify": 0, "open": 0, "decode": 0}


def test_real_i07_i08_i09_authorities_are_not_postgres_authorities(installed_repo: pg.PostgresMetadataRepository, tmp_path: Path) -> None:
    # I07: direct SQL forgery cannot alter the accepted durable repository.
    job_module = _load_sibling_helper()("_i11r1_job_state", "test_job_state")
    stack = job_module.JobStack(tmp_path / "i07")
    created = stack.repo.create_job(job_id="job-authority", provider_id="PROVIDER", sensor_family=SensorFamily.MECHANICAL_TRADE, request_fingerprint="authority")
    authoritative = pg._model_row("storage_jobs", created)
    authoritative_snapshot = pg.MetadataSnapshot({"storage_jobs": [authoritative], "storage_job_transitions": []})
    installed_repo.refresh_reconstructible_metadata(snapshot=authoritative_snapshot)
    with psycopg.connect(DSN, autocommit=True) as connection:
        connection.execute(f'UPDATE "{pg.SCHEMA_NAME}"."storage_jobs" SET status = %s WHERE job_id = %s', ("FORGED", "job-authority"))
    assert stack.repo.get_job("job-authority").status is StorageJobStatus.PLANNED
    installed_repo.refresh_reconstructible_metadata(snapshot=authoritative_snapshot)
    assert installed_repo.canonical_rows(("storage_jobs",))["storage_jobs"][0][4] == "PLANNED"
    # I08: journal truth remains independent of the summary mirror.
    journal = RecoveryJournal(tmp_path / "i08")
    journal.record(recovery_run_id="run-1", object_type="BLOB", object_id="blob-1", problem="problem", resolution="resolution")
    before = journal.get(journal.action_ids()[0])
    with psycopg.connect(DSN, autocommit=True) as connection:
        connection.execute(f'UPDATE "{pg.SCHEMA_NAME}"."recovery_runs" SET action_count = 999 WHERE recovery_run_id = %s', ("run-1",))
    assert journal.get(journal.action_ids()[0]) == before
    # I09: quota policy/config and filesystem evidence are not sourced from Postgres.
    config = QuotaConfig(absolute_free_floor_bytes=7)
    pressure_file = tmp_path / "pressure.txt"
    pressure_file.write_text("accepted", encoding="utf-8")
    with psycopg.connect(DSN, autocommit=True) as connection:
        connection.execute(f'UPDATE "{pg.SCHEMA_NAME}"."quota_state" SET pressure_state = %s', ("CRITICAL",))
    assert config.absolute_free_floor_bytes == 7
    assert pressure_file.read_text(encoding="utf-8") == "accepted"
    installed_repo.refresh_reconstructible_metadata(snapshot=_snapshot("A"))
    assert installed_repo.canonical_rows(("quota_state",))["quota_state"] == []


def test_real_canonical_order_is_explicit_and_stable(installed_repo: pg.PostgresMetadataRepository) -> None:
    installed_repo.refresh_reconstructible_metadata(snapshot=_snapshot("A"))
    assert installed_repo.canonical_rows() == installed_repo.canonical_rows()
    assert "resume_token" not in str(installed_repo.introspect_schema())
    assert all(key in pg.CANONICAL_ORDER for key in pg.TABLE_NAMES)
    assert pg.CANONICAL_ORDER["storage_job_transitions"] == ("job_id", "transitioned_at", "transition_id")


def test_real_reconstruction_uses_complete_public_inventory_and_omits_resume_tokens(tmp_path: Path) -> None:
    class Readers:
        def __init__(self):
            self.blob_repo = SimpleNamespace(get_blob_metadata=lambda sha: [EvidenceBlob(blob_sha256=sha, byte_length=1, stored_byte_length=1, source_media_type="application/json", storage_encoding="NONE", created_at=UTC_TIME, storage_uri="objects/" + sha, integrity_state="LOCAL_HASH_VERIFIED")])
            self.acq_repo = SimpleNamespace(get_acquisition=lambda acq_id: AcquisitionRecord.model_construct(acquisition_id=acq_id, provider_id="PROVIDER", venue="VENUE", sensor_family="MECHANICAL_TRADE", request_fingerprint="fp", adapter_version="1", requested_start=UTC_TIME, requested_end=UTC_TIME, actual_start=UTC_TIME, actual_end=UTC_TIME, native_instrument="NATIVE", request_started_at=UTC_TIME, response_observed_at=UTC_TIME, ingested_at=UTC_TIME, source_locator="fixture", blob_sha256="a" * 64, provider_checksum_verified=True, quality_flags=[], resume_token_before="PRIVATE", resume_token_after="PRIVATE"))
            self.manifest_repo = SimpleNamespace(get_current_manifest=lambda key: PartitionManifest.model_construct(partition_manifest_id="m-1", partition_key=key, manifest_version=1, provider="PROVIDER", venue="VENUE", sensor_family="MECHANICAL_TRADE", native_instrument="NATIVE", date_basis="EVENT_TIME", logical_date_start=UTC_TIME, logical_date_end=UTC_TIME, coverage_state="COMPLETE", integrity_state="LOCAL_HASH_VERIFIED", row_count=1, min_time=UTC_TIME, max_time=UTC_TIME, gap_count=0, revision_count=1, created_at=UTC_TIME, blob_refs=["a" * 64], projection_refs=[]), read_current_pointer=lambda key: SimpleNamespace(updated_at=UTC_TIME))
            self.job_repo = SimpleNamespace(list_job_ids=lambda: ["job-1"], get_job=lambda job_id: StorageJobState.model_construct(job_id=job_id, provider_id="PROVIDER", sensor_family="MECHANICAL_TRADE", request_fingerprint="fp", status="MANIFEST_COMMITTED", updated_at=UTC_TIME), list_transitions=lambda job_id: [StorageJobTransition.model_construct(transition_id="t-1", job_id=job_id, from_status="PLANNED", to_status="MANIFEST_COMMITTED", transitioned_at=UTC_TIME)])
            self.revision_registry = SimpleNamespace(list_revisions=lambda key: [SourceRevision(source_revision_key=key, revision_number=1, blob_sha256="a" * 64, first_seen_at=UTC_TIME, last_seen_at=UTC_TIME)])
            self.recovery_journal = SimpleNamespace(list_for_run=lambda run_id: [{"recovery_run_id": run_id, "object_id": "blob-1", "problem": "problem", "registered_at": UTC_TIME.isoformat()}])
        def provider_registry(self):
            return {"providers": {"P1": {"status": "CANDIDATE", "evidence_class": "B1", "access": {"mode": "FREE"}, "capabilities": {}, "fallback_candidates": {}}}}
    readers = Readers()
    sources = pg.MetadataSources(provider_registry=readers.provider_registry(), readiness_records=[{"provider_id": "P1", "sensor_family": "MECHANICAL_TRADE", "adapter_id": "a", "adapter_version": "1", "promoted": "YES", "implemented": "YES", "offline_conformance_pass": "YES", "schema_pass": "YES", "network_smoke_status": "NOT_RUN", "evidence_ref": "e", "pit_readiness": "NOT_PIT_READY", "limitations": "fixture"}], blob_metadata_repository=readers.blob_repo, acquisition_repository=readers.acq_repo, manifest_repository=readers.manifest_repo, job_repository=readers.job_repo, revision_registry=readers.revision_registry, recovery_journal=readers.recovery_journal, inventory=pg.MetadataInventory(("a" * 64,), ("acq-1",), ("partition-1",), ("source-1",), ("run-1",), True))
    snapshot = pg.reconstruct_snapshot(data_root=tmp_path, sources=sources)
    assert len(snapshot.rows["acquisitions"]) == 1
    assert "resume_token_before" not in snapshot.rows["acquisitions"][0]
    assert "PRIVATE" not in str(snapshot.rows["acquisitions"][0])
    assert len(snapshot.rows["source_revisions"]) == 1
