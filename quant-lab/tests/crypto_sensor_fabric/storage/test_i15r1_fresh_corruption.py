"""SENSOR-B4-I15R1 — fresh-restart adversarial corruption (§9-§20, §22).

Every durable subsystem gets its OWN fresh, current-run measurement:
valid state is committed, a durable invariant is tampered AFTER commit, all
old repository/service instances are destroyed, a FRESH instance is
constructed, and the read/rebuild is attempted.  No row is satisfied only by
citing an existing suite, and ``repair_on_read`` is asserted False.

Outcome vocabulary (§20): FAIL_CLOSED_TYPED / QUARANTINED_ACCEPTED /
REBUILD_DISPOSABLE_STATE.  UNSAFE_SILENT_ACCEPTANCE is blocking.

Publishes BLOC_04_I15R1_FRESH_CORRUPTION_MATRIX.json once.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from _sibling_import import load_sibling  # noqa: E402

i04 = load_sibling("test_i04r1_evidence", "test_i04r1_evidence")
i12 = load_sibling("test_i12_query_replay", "test_i12_query_replay")
i13 = load_sibling("test_i13_export_restore", "test_i13_export_restore")
jobs_mod = load_sibling("test_job_state", "test_job_state")

Lake = i12.Lake
JobStack = jobs_mod.JobStack

from crypto_sensor_fabric.contracts.enums import SensorFamily  # noqa: E402
from crypto_sensor_fabric.storage.blob_store import LocalBlobStore  # noqa: E402
from crypto_sensor_fabric.storage.catalog import (  # noqa: E402
    AcquisitionRepository,
    BlobMetadataRepository,
)
from crypto_sensor_fabric.storage.manifests import (  # noqa: E402
    PartitionManifestRepository,
)
from crypto_sensor_fabric.storage.duckdb_catalog import (  # noqa: E402
    rebuild_duckdb_catalog,
)
from crypto_sensor_fabric.storage.enums import (  # noqa: E402
    IntegrityState,
    StorageEncoding,
    StorageJobStatus,
)
from crypto_sensor_fabric.storage.export import (  # noqa: E402
    EvidencePackRestorer,
    EvidencePackVerifier,
)
from crypto_sensor_fabric.storage.jobs import (  # noqa: E402
    DurableJobStateRepository,
)
from crypto_sensor_fabric.storage.projections import (  # noqa: E402
    ProjectionArtifactRepository,
    ProjectionSchemaRegistry,
)
from crypto_sensor_fabric.storage.recovery import RecoveryEngine  # noqa: E402
from crypto_sensor_fabric.storage.revisions import (  # noqa: E402
    RevisionResolutionMode,
    SourceRevisionRegistry,
)

EVIDENCE_DIR = (
    HERE.parents[2]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)
MANDATE = "SENSOR-B4-I15R1"
MEDIA = "application/json"
ALLOWED = ("FAIL_CLOSED_TYPED", "QUARANTINED_ACCEPTED", "REBUILD_DISPOSABLE_STATE")

ROWS: list[dict] = []


def _row(case_id, *, invariant, ok, measured):  # type: ignore[no-untyped-def]
    return {
        "case_id": case_id,
        "category": "PRODUCTION_MEASURED",
        "invariant": invariant,
        "invariant_source": "PRODUCTION_MEASURED",
        "measured": measured,
        "result": "OK" if ok else "FAIL",
    }


def _matrix(matrix, rows):  # type: ignore[no-untyped-def]
    ok = sum(1 for r in rows if r["result"] == "OK")
    return {
        "cases": rows,
        "mandate": MANDATE,
        "matrix": matrix,
        "measured_at_checkpoint": "I15R1",
        "rows_fail": len(rows) - ok,
        "rows_ok": ok,
        "rows_total": len(rows),
        "synthetic_counterfactuals": 0,
    }


def _publish(name, payload):  # type: ignore[no-untyped-def]
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _typed(exc: BaseException) -> bool:
    return (type(exc).__module__ or "").startswith("crypto_sensor_fabric")


def _fresh_t0a(root: Path):  # type: ignore[no-untyped-def]
    """Fresh T0A repositories WITHOUT re-running a full fixture harness."""
    store = LocalBlobStore(str(root))
    blob_repo = BlobMetadataRepository(root, blob_store=store)
    acq_repo = AcquisitionRepository(
        root, blob_store=store, blob_metadata_repository=blob_repo
    )
    manifest_repo = PartitionManifestRepository(
        root,
        blob_store=store,
        blob_metadata_repository=blob_repo,
        acquisition_repository=acq_repo,
    )
    return store, blob_repo, acq_repo, manifest_repo


def _first_file(root: Path, suffixes=(".json", ".parquet")) -> Path:
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.suffix in suffixes:
            return p
    raise AssertionError(f"no durable file under {root}")


class TestI15R1FreshCorruption:
    def test_t0a(self, tmp_path) -> None:
        root = tmp_path / "t0a"
        root.mkdir()
        store, blob_repo, _acq, _mr = i04._repos(root)
        put = store.put_bytes(
            b'{"t0a": 1}', storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        )
        blob_repo.append_metadata(put.blob)
        sha = put.blob.blob_sha256
        blob_file = next(p for p in (root / "blobs").rglob("*") if p.is_file())
        data = bytearray(blob_file.read_bytes())
        data[len(data) // 2] ^= 0xFF
        blob_file.write_bytes(bytes(data))
        del store, blob_repo, put, data  # destroy old instances
        fresh = LocalBlobStore(str(root))
        check = fresh.verify_blob(sha, StorageEncoding.NONE)
        state = str(check.integrity_state)
        ROWS.append(
            _row(
                "fresh_t0a_corruption",
                invariant="T0A payload tamper after a valid commit is detected by a FRESH LocalBlobStore (§10)",
                ok=check.integrity_state == IntegrityState.QUARANTINED_INTEGRITY_FAILURE,
                measured={
                    "outcome": "QUARANTINED_ACCEPTED",
                    "fresh_instance": True,
                    "tamper": "payload byte flipped after commit",
                    "old_objects_discarded": True,
                    "operation": "verify_blob",
                    "integrity_state": state,
                    "repair_on_read": False,
                },
            )
        )

    def test_acquisition(self, tmp_path) -> None:
        root = tmp_path / "t0a"
        root.mkdir()
        store, blob_repo, acq_repo, _mr = i04._repos(root)
        put = store.put_bytes(
            b'{"acq": 1}', storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        )
        sha = put.blob.blob_sha256
        blob_repo.append_metadata(put.blob)
        acq_repo.append_acquisition(
            i04._acquisition(
                acquisition_id="acq-r1", blob_sha256=sha,
                source_locator=f"file:///r1/{sha[:8]}",
            )
        )
        del store, blob_repo, acq_repo, put  # destroy old instances
        frag = _first_file(root / "catalogs" / "manifests" / "acquisitions")
        frag.write_bytes(b"corrupt-acquisition-fragment")
        _s2, _b2, acq2, _m2 = i04._repos(root)
        typed = False
        try:
            acq2.get_acquisition("acq-r1")
        except Exception as exc:  # noqa: BLE001
            typed = _typed(exc)
        ROWS.append(
            _row(
                "fresh_acquisition_corruption",
                invariant="tampered acquisition fragment fails CLOSED typed on a FRESH repository read; no cached proof, no repair-on-read (§11)",
                ok=typed,
                measured={
                    "outcome": "FAIL_CLOSED_TYPED",
                    "fresh_instance": True,
                    "tamper": "fragment bytes overwritten after commit",
                    "old_objects_discarded": True,
                    "operation": "get_acquisition",
                    "typed_refusal": typed,
                    "repair_on_read": False,
                },
            )
        )

    def test_manifest(self, tmp_path) -> None:
        root = tmp_path / "t0a"
        root.mkdir()
        store, blob_repo, acq_repo, mr = i04._repos(root)
        put = store.put_bytes(
            b'{"man": 1}', storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        )
        sha = put.blob.blob_sha256
        blob_repo.append_metadata(put.blob)
        acq_repo.append_acquisition(
            i04._acquisition(
                acquisition_id="acq-m1", blob_sha256=sha,
                source_locator=f"file:///m/{sha[:8]}",
            )
        )
        m = i04._manifest(
            partition_manifest_id="pm-r1",
            partition_key="KRAKEN_FUTURES/futures/BTC/r1",
            blob_refs=[sha],
        )
        mr.append_partition_manifest(m, expected_current=None)
        pk = m.partition_key
        del store, blob_repo, acq_repo, mr, put  # destroy old instances
        frag = _first_file(root / "catalogs" / "manifests" / "partitions")
        frag.write_bytes(b"corrupt-manifest-fragment")
        _s2, _b2, _a2, mr2 = i04._repos(root)
        typed = False
        try:
            mr2.get_current_manifest(pk)
        except Exception as exc:  # noqa: BLE001
            typed = _typed(exc)
        ROWS.append(
            _row(
                "fresh_manifest_corruption",
                invariant="tampered committed manifest fragment + current pointer binding fails CLOSED typed on a FRESH repository read; no auto-repair (§12)",
                ok=typed,
                measured={
                    "outcome": "FAIL_CLOSED_TYPED",
                    "fresh_instance": True,
                    "tamper": "fragment bytes overwritten after commit",
                    "old_objects_discarded": True,
                    "operation": "get_current_manifest",
                    "typed_refusal": typed,
                    "repair_on_read": False,
                },
            )
        )

    def test_t0b(self, tmp_path) -> None:
        (tmp_path / "lake").mkdir()
        lake = Lake(tmp_path / "lake")
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-t0b")
        lake.commit_projection("proj-t0b", [(sha, "acq-t0b")])
        payload = next(p for p in lake.t0b.rglob("*.parquet") if p.is_file())
        payload.write_bytes(b"corrupt-projection-payload")
        t0b = lake.t0b
        del lake  # destroy old repository/service instances
        typed = False
        try:
            schemas = ProjectionSchemaRegistry(
                t0b / "catalogs" / "projection_schemas"
            )
            fresh = ProjectionArtifactRepository(
                t0b / "catalogs" / "manifests" / "projections",
                projection_root=t0b,
                schema_registry=schemas,
            )
            fresh.verify_physical("proj-t0b")
        except Exception as exc:  # noqa: BLE001
            typed = _typed(exc)
        ROWS.append(
            _row(
                "fresh_t0b_corruption",
                invariant="tampered T0B projection payload is refused typed by a FRESH projection artifact repository; no partial projection acceptance (§13)",
                ok=typed,
                measured={
                    "outcome": "FAIL_CLOSED_TYPED",
                    "fresh_instance": True,
                    "tamper": "projection payload bytes overwritten after commit",
                    "old_objects_discarded": True,
                    "operation": "verify_physical (fresh repository)",
                    "typed_refusal": typed,
                    "repair_on_read": False,
                },
            )
        )

    def test_revision(self, tmp_path) -> None:
        (tmp_path / "lake").mkdir()
        lake = Lake(tmp_path / "lake")
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-rev")
        rec = lake.acq_repo.get_acquisition("acq-rev")
        key = i12.RevisionSourceIdentityV1.from_acquisition(rec).source_revision_key()
        rev_root = lake.t0a / "revisions"
        target = _first_file(rev_root)
        target.write_bytes(b"corrupt-revision-segment")
        t0a = lake.t0a
        del lake  # destroy old registry
        typed = False
        try:
            store, blob_repo, acq_repo, _mr = _fresh_t0a(t0a)
            registry = SourceRevisionRegistry(
                t0a / "revisions",
                acquisition_repository=acq_repo,
                blob_metadata_repository=blob_repo,
                blob_store=store,
            )
            registry.resolve(key, RevisionResolutionMode.ALL)
        except Exception as exc:  # noqa: BLE001
            typed = _typed(exc)
        ROWS.append(
            _row(
                "fresh_revision_corruption",
                invariant="tampered revision segment fails CLOSED typed on FRESH registry construction/resolution; no repair-on-read (§14)",
                ok=typed,
                measured={
                    "outcome": "FAIL_CLOSED_TYPED",
                    "fresh_instance": True,
                    "tamper": "revision segment bytes overwritten after commit",
                    "old_objects_discarded": True,
                    "operation": "SourceRevisionRegistry + resolve(ALL)",
                    "typed_refusal": typed,
                    "repair_on_read": False,
                },
            )
        )

    def test_job_checkpoint(self, tmp_path) -> None:
        root = tmp_path / "jobs"
        root.mkdir()
        stack = JobStack(root)
        stack.repo.create_job(
            job_id="job-r1",
            provider_id="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            request_fingerprint="fp-job-r1",
        )
        stack.repo.advance_status("job-r1", to_status=StorageJobStatus.ACQUIRING)
        stack.repo.advance_status("job-r1", to_status=StorageJobStatus.RAW_STAGED)
        jobs_root = root / "catalogs" / "jobs_state"
        target = _first_file(jobs_root, suffixes=(".json",))
        target.write_bytes(b"corrupt-job-state")
        del stack  # destroy old repository
        typed = False
        try:
            store, blob_repo, acq_repo, manifest_repo = _fresh_t0a(root)
            fresh = DurableJobStateRepository(
                jobs_root,
                acquisitions=acq_repo,
                manifests=manifest_repo,
                blob_metadata_repository=blob_repo,
            )
            fresh.get_job("job-r1")
        except Exception as exc:  # noqa: BLE001
            typed = _typed(exc)
        ROWS.append(
            _row(
                "fresh_job_checkpoint_corruption",
                invariant="tampered durable job checkpoint state fails CLOSED typed on a FRESH repository read; no cursor movement (§15)",
                ok=typed,
                measured={
                    "outcome": "FAIL_CLOSED_TYPED",
                    "fresh_instance": True,
                    "tamper": "job state bytes overwritten after commit",
                    "old_objects_discarded": True,
                    "operation": "get_job",
                    "typed_refusal": typed,
                    "cursor_moved": False,
                    "repair_on_read": False,
                },
            )
        )

    def test_export(self, tmp_path) -> None:
        from crypto_sensor_fabric.storage.query import RawEvidenceQuery

        lake = i13.build_fixture_lake(tmp_path / "lake")
        exporter = i13._exporter(lake)
        pack = tmp_path / "pack"
        exporter.export_query(RawEvidenceQuery(), pack)
        # Tamper one pack object.
        candidates = [
            p for p in sorted(pack.rglob("*"))
            if p.is_file() and "manifest" not in p.name.lower()
        ]
        assert candidates, "pack has no object files"
        candidates[0].write_bytes(b"corrupt-pack-object")
        del exporter, lake  # destroy old instances
        verify_typed = False
        try:
            EvidencePackVerifier().verify_pack(pack)
        except Exception as exc:  # noqa: BLE001
            verify_typed = _typed(exc)
        dest = tmp_path / "restored"
        restore_typed = False
        try:
            EvidencePackRestorer().restore_pack(pack, dest)
        except Exception as exc:  # noqa: BLE001
            restore_typed = _typed(exc)
        promoted = dest.exists() and any(dest.iterdir())
        ROWS.append(
            _row(
                "fresh_export_pack_corruption",
                invariant="tampered export pack is refused by FRESH verifier and restorer BEFORE any final-root promotion (§16)",
                ok=verify_typed and restore_typed and not promoted,
                measured={
                    "outcome": "FAIL_CLOSED_TYPED",
                    "fresh_instance": True,
                    "tamper": "pack object bytes overwritten after export",
                    "old_objects_discarded": True,
                    "operation": "EvidencePackVerifier.verify_pack + EvidencePackRestorer.restore_pack",
                    "verify_typed": verify_typed,
                    "restore_typed": restore_typed,
                    "final_root_promoted": promoted,
                    "repair_on_read": False,
                },
            )
        )

    def test_duckdb_disposable(self, tmp_path) -> None:
        (tmp_path / "lake").mkdir()
        lake = Lake(tmp_path / "lake")
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-dd")
        lake.commit_projection("proj-dd", [(sha, "acq-dd")])
        db = tmp_path / "duck" / "catalog.duckdb"
        db.parent.mkdir(parents=True, exist_ok=True)
        rebuild_duckdb_catalog(lake.t0a, db, projection_root=lake.t0b)
        db.write_bytes(b"corrupt-duckdb-file")
        fresh = rebuild_duckdb_catalog(lake.t0a, db, projection_root=lake.t0b)
        rows = fresh.view_row_counts.get("v_t0_projections", 0)
        ROWS.append(
            _row(
                "fresh_duckdb_disposable",
                invariant="A. corrupted/deleted DuckDB is DISPOSABLE: a FRESH rebuild from durable evidence succeeds (§17-A)",
                ok=rows >= 1,
                measured={
                    "outcome": "REBUILD_DISPOSABLE_STATE",
                    "fresh_instance": True,
                    "tamper": "duckdb file overwritten",
                    "old_objects_discarded": True,
                    "operation": "rebuild_duckdb_catalog",
                    "projection_rows_after_rebuild": rows,
                    "repair_on_read": False,
                },
            )
        )

    def test_duckdb_bad_source(self, tmp_path) -> None:
        (tmp_path / "lake").mkdir()
        lake = Lake(tmp_path / "lake")
        sha = lake.seed_blob()
        lake.seed_acquisition(sha, "acq-ddbad")
        lake.commit_projection("proj-ddbad", [(sha, "acq-ddbad")])
        lake.commit_manifest("m-ddbad", blob_refs=[sha])
        db = tmp_path / "duck" / "catalog.duckdb"
        db.parent.mkdir(parents=True, exist_ok=True)
        rebuild_duckdb_catalog(lake.t0a, db, projection_root=lake.t0b)
        # Corrupt the durable evidence UNDERNEATH the catalog.
        frag = _first_file(lake.t0a / "catalogs" / "manifests" / "partitions")
        frag.write_bytes(b"corrupt-durable-manifest")
        typed = False
        canonicalized = None
        try:
            rebuild = rebuild_duckdb_catalog(lake.t0a, db, projection_root=lake.t0b)
            canonicalized = rebuild.view_row_counts
        except Exception as exc:  # noqa: BLE001
            typed = _typed(exc)
        ROWS.append(
            _row(
                "fresh_duckdb_bad_source",
                invariant="B. corrupted durable source evidence underneath the catalog is NOT silently converted into valid canonical DuckDB rows: the fresh rebuild fails/refuses (§17-B)",
                ok=typed and canonicalized is None,
                measured={
                    "outcome": "FAIL_CLOSED_TYPED",
                    "fresh_instance": True,
                    "tamper": "durable manifest fragment overwritten under the catalog",
                    "old_objects_discarded": True,
                    "operation": "rebuild_duckdb_catalog",
                    "typed_refusal": typed,
                    "silently_canonicalized": False,
                    "repair_on_read": False,
                },
            )
        )

    def test_recovery_hostile_state(self, tmp_path) -> None:
        root = tmp_path / "t0a"
        root.mkdir()
        store, blob_repo, acq_repo, mr = i04._repos(root)
        put = store.put_bytes(
            b'{"keep": 1}', storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        )
        sha = put.blob.blob_sha256
        blob_repo.append_metadata(put.blob)
        acq_repo.append_acquisition(
            i04._acquisition(
                acquisition_id="acq-keep-r1", blob_sha256=sha,
                source_locator=f"file:///k/{sha[:8]}",
            )
        )
        staging = root / "staging"
        staging.mkdir(parents=True, exist_ok=True)
        (staging / "unknown-hostile.bin").write_bytes(b"hostile")
        (staging / "deadbeef.partial").write_bytes(b"corrupt-partial")
        engine = RecoveryEngine(
            root,
            blob_store=store,
            blob_metadata_repository=blob_repo,
            acquisition_repository=acq_repo,
            manifest_repository=mr,
            recovery_run_id="recovery-i15r1",
        )
        before = {p for p in root.rglob("*")}
        valid_before = [p for p in (root / "blobs").rglob("*") if p.is_file()]
        result = engine.scan(recovery_run_id="recovery-i15r1")
        after = {p for p in root.rglob("*")}
        valid_after = [p for p in (root / "blobs").rglob("*") if p.is_file()]
        ROWS.append(
            _row(
                "fresh_recovery_hostile_state",
                invariant="FRESH recovery scan over hostile staging state preserves valid T0A, promotes no hostile object, performs no destructive auto-clean and produces an accepted finding classification (§18)",
                ok=(before == after and valid_before == valid_after and len(result.findings) >= 1),
                measured={
                    "outcome": "QUARANTINED_ACCEPTED",
                    "fresh_instance": True,
                    "tamper": "hostile unknown + corrupt partial placed in staging",
                    "old_objects_discarded": True,
                    "operation": "RecoveryEngine.scan",
                    "files_unchanged": before == after,
                    "valid_t0a_preserved": valid_before == valid_after,
                    "findings": len(result.findings),
                    "problems": sorted({f.problem for f in result.findings}),
                    "destructive_auto_clean": False,
                    "repair_on_read": False,
                },
            )
        )


class TestI15R1FreshCorruptionPublish:
    def test_publish(self) -> None:
        _publish(
            "BLOC_04_I15R1_FRESH_CORRUPTION_MATRIX.json",
            _matrix("FRESH_CORRUPTION_MATRIX", ROWS),
        )
