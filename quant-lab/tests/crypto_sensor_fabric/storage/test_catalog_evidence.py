"""SENSOR-B4-I04E — machine evidence for the acquisition + manifest catalog.

Generates the deterministic evidence artifacts:

- ``BLOC_04_I04_CATALOG_SCHEMAS.json`` (I04 §81): every catalog family's
  stable Arrow schema (fields, logical types, nullability, model source);
- ``BLOC_04_I04_MANIFEST_CONCURRENCY.json`` (I04 §81): the deterministic
  manifest/concurrency/crash cases (first_manifest, sequential_v2,
  eight_writer_same_base, stale_writer, duplicate_exact_manifest,
  identity_conflict, pointer P1-P5).

No wall-clock nondeterminism: all clocks are injected and fixed.  Historical
I03/I03R1 evidence is never touched.
"""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity
from crypto_sensor_fabric.storage import (
    BlobMetadataRepository,
    IntegrityState,
    LocalBlobStore,
    ManifestCASConflict,
    ManifestDisposition,
    ManifestIdentityConflict,
    ManifestLockHeld,
    PartitionManifest,
    PartitionManifestRepository,
    PointerFaultPoint,
    RaisePointerFaultHook,
)
from crypto_sensor_fabric.storage.catalog import ACQUISITION_SCHEMA, BLOB_SCHEMA
from crypto_sensor_fabric.storage.manifests import MANIFEST_SCHEMA

FIXED = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"
PK = "KRAKEN_FUTURES/MECHANICAL_FUNDING/PI_XBTUSD/2026-08"

EVIDENCE_DIR = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)


def _make_store(root: Path) -> LocalBlobStore:
    return LocalBlobStore(root, clock=lambda: FIXED)


def _make_repo(
    root: Path,
) -> tuple[LocalBlobStore, BlobMetadataRepository, PartitionManifestRepository]:
    store = _make_store(root)
    blob_repo = BlobMetadataRepository(root, blob_store=store, clock=lambda: FIXED)
    repo = PartitionManifestRepository(
        root,
        blob_store=store,
        blob_metadata_repository=blob_repo,
        clock=lambda: FIXED,
    )
    return store, blob_repo, repo


def _manifest(**overrides: Any) -> PartitionManifest:
    kwargs: dict[str, Any] = {
        "partition_manifest_id": "pm-1",
        "partition_key": PK,
        "manifest_version": 1,
        "provider": "KRAKEN_FUTURES",
        "venue": "KRAKEN_FUTURES",
        "sensor_family": SensorFamily.MECHANICAL_FUNDING,
        "native_instrument": "PI_XBTUSD",
        "source_granularity": Granularity.G1H,
        "date_basis": "EVENT_TIME",
        "logical_date_start": datetime(2026, 8, 1, 0, 0, 0, tzinfo=UTC),
        "logical_date_end": datetime(2026, 8, 31, 23, 59, 59, tzinfo=UTC),
        "blob_refs": [],
        "projection_refs": [],
        "coverage_state": "PARTIAL",
        "integrity_state": IntegrityState.UNVERIFIED,
        "row_count": 0,
        "min_time": None,
        "max_time": None,
        "gap_count": 0,
        "revision_count": 0,
        "created_at": FIXED,
        "supersedes_manifest_id": None,
    }
    kwargs.update(overrides)
    return PartitionManifest(**kwargs)


def _schema_meta(
    family: str, schema: Any, model_source: str, schema_version: str
) -> dict[str, Any]:
    def logical_type(field: Any) -> str:
        t = field.type
        if isinstance(t, pa.TimestampType):
            return "timestamp(us, tz=UTC)"
        if isinstance(t, pa.ListType):
            return "list<string>"
        return str(t)

    fields = [
        {
            "name": f.name,
            "logical_type": logical_type(f),
            "nullable": f.nullable,
        }
        for f in schema
    ]
    return {
        "catalog_family": family,
        "schema_version": schema_version,
        "model_source": model_source,
        "fields": fields,
    }


class TestCatalogSchemasEvidence:
    def test_catalog_schemas_artifact_written(self) -> None:
        schemas = [
            _schema_meta("blobs", BLOB_SCHEMA, "EvidenceBlob (I01 model)", "1.0.0"),
            _schema_meta(
                "acquisitions", ACQUISITION_SCHEMA, "AcquisitionRecord (I01 + I04A)", "1.0.0"
            ),
            _schema_meta(
                "partitions", MANIFEST_SCHEMA, "PartitionManifest (I01 model)", "1.0.0"
            ),
        ]
        for entry in schemas:
            names = [f["name"] for f in entry["fields"]]
            assert len(names) == len(set(names))
            assert all(f["logical_type"] for f in entry["fields"])
        out_path = EVIDENCE_DIR / "BLOC_04_I04_CATALOG_SCHEMAS.json"
        out_path.write_text(
            json.dumps(schemas, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        # deterministic regeneration
        again = json.loads(out_path.read_text(encoding="utf-8"))
        assert again == schemas
        # historical evidence untouched
        assert (EVIDENCE_DIR / "BLOC_04_I03R1_NAMESPACE_DURABILITY.json").exists()
        assert (EVIDENCE_DIR / "BLOC_04_I03_CRASH_MATRIX.json").exists()


class TestManifestConcurrencyEvidence:
    def _run_case(self, root: Path, case: str) -> dict[str, Any]:
        store, blob_repo, repo = _make_repo(root)
        if case == "first_manifest":
            repo.append_partition_manifest(_manifest(), expected_current=None)
            current = repo.get_current_manifest(PK)
            return {
                "case": case,
                "expected_current": None,
                "winner_count": 1,
                "final_version": current.manifest_version,
                "current_manifest_id": current.partition_manifest_id,
                "orphan_count": len(repo.list_orphan_manifest_fragments(PK)),
                "test_name": "test_first_manifest_v1",
            }
        if case == "sequential_v2":
            repo.append_partition_manifest(_manifest(), expected_current=None)
            repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-2",
                    manifest_version=2,
                    supersedes_manifest_id="pm-1",
                ),
                expected_current=("pm-1", 1),
            )
            current = repo.get_current_manifest(PK)
            return {
                "case": case,
                "expected_current": ["pm-1", 1],
                "winner_count": 1,
                "final_version": current.manifest_version,
                "current_manifest_id": current.partition_manifest_id,
                "orphan_count": len(repo.list_orphan_manifest_fragments(PK)),
                "test_name": "test_sequential_v2",
            }
        if case == "stale_writer":
            repo.append_partition_manifest(_manifest(), expected_current=None)
            repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-2",
                    manifest_version=2,
                    supersedes_manifest_id="pm-1",
                ),
                expected_current=("pm-1", 1),
            )
            stale_rejected = False
            try:
                repo.append_partition_manifest(
                    _manifest(
                        partition_manifest_id="pm-stale",
                        manifest_version=2,
                        supersedes_manifest_id="pm-1",
                    ),
                    expected_current=("pm-1", 1),
                )
            except ManifestCASConflict:
                stale_rejected = True
            current = repo.get_current_manifest(PK)
            return {
                "case": case,
                "expected_current": ["pm-1", 1],
                "winner_count": 1,
                "final_version": current.manifest_version,
                "current_manifest_id": current.partition_manifest_id,
                "stale_writer_rejected": stale_rejected,
                "orphan_count": len(repo.list_orphan_manifest_fragments(PK)),
                "test_name": "test_stale_writer_cas_conflict_no_auto_rebase",
            }
        if case == "duplicate_exact_manifest":
            repo.append_partition_manifest(_manifest(), expected_current=None)
            v2 = _manifest(
                partition_manifest_id="pm-2",
                manifest_version=2,
                supersedes_manifest_id="pm-1",
            )
            repo.append_partition_manifest(v2, expected_current=("pm-1", 1))
            second = repo.append_partition_manifest(v2, expected_current=("pm-1", 1))
            current = repo.get_current_manifest(PK)
            return {
                "case": case,
                "expected_current": ["pm-1", 1],
                "winner_count": 1,
                "final_version": current.manifest_version,
                "current_manifest_id": current.partition_manifest_id,
                "second_disposition": second.disposition.value,
                "second_idempotent": (
                    second.disposition is ManifestDisposition.IDEMPOTENT_COMPLETION
                ),
                "orphan_count": len(repo.list_orphan_manifest_fragments(PK)),
                "test_name": "test_idempotent_completion_after_pointer_move",
            }
        if case == "identity_conflict":
            repo.append_partition_manifest(_manifest(), expected_current=None)
            with pytest.raises(RuntimeError):
                repo.append_partition_manifest(
                    _manifest(
                        partition_manifest_id="pm-2",
                        manifest_version=2,
                        supersedes_manifest_id="pm-1",
                    ),
                    expected_current=("pm-1", 1),
                    fault_hooks=RaisePointerFaultHook(PointerFaultPoint.P2),
                )
            conflict = False
            try:
                repo.append_partition_manifest(
                    _manifest(
                        partition_manifest_id="pm-2",
                        manifest_version=2,
                        supersedes_manifest_id="pm-1",
                        row_count=99,
                    ),
                    expected_current=("pm-1", 1),
                )
            except ManifestIdentityConflict:
                conflict = True
            return {
                "case": case,
                "expected_current": ["pm-1", 1],
                "winner_count": 0,
                "final_version": repo.get_current_manifest(PK).manifest_version,
                "identity_conflict_raised": conflict,
                "orphan_count": len(repo.list_orphan_manifest_fragments(PK)),
                "test_name": "test_same_manifest_id_different_content_conflict",
            }
        if case == "eight_writer_same_base":
            repo.append_partition_manifest(_manifest(), expected_current=None)
            outcomes: list[str] = []
            outcomes_lock = threading.Lock()
            candidates: list[str] = []

            def writer(index: int) -> None:
                manifest_id = f"pm-2-w{index}"
                with outcomes_lock:
                    candidates.append(manifest_id)
                try:
                    result = repo.append_partition_manifest(
                        _manifest(
                            partition_manifest_id=manifest_id,
                            manifest_version=2,
                            supersedes_manifest_id="pm-1",
                            row_count=index + 1,
                        ),
                        expected_current=("pm-1", 1),
                    )
                    outcome = f"{result.disposition.value}:{manifest_id}"
                except ManifestCASConflict:
                    outcome = f"ManifestCASConflict:{manifest_id}"
                except ManifestLockHeld:
                    outcome = f"ManifestLockHeld:{manifest_id}"
                with outcomes_lock:
                    outcomes.append(outcome)

            threads = [
                threading.Thread(target=writer, args=(i,)) for i in range(8)
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
            committed = [o for o in outcomes if o.startswith("COMMITTED_NEW")]
            # Winner identity is scheduling-dependent by design; the evidence
            # records only provable, deterministic properties (winner count,
            # winner-membership in the candidate set, candidate-set fingerprint).
            current = repo.get_current_manifest(PK)
            return {
                "case": case,
                "expected_current": ["pm-1", 1],
                "winner_count": len(committed),
                "winner_in_candidate_set": bool(committed) and any(
                    o.endswith(w) for o in committed for w in candidates
                ),
                "candidate_count": len(candidates),
                "candidate_set_fingerprint": hashlib.sha256(
                    json.dumps(sorted(candidates), separators=(",", ":")).encode("utf-8")
                ).hexdigest(),
                "loser_count": len(outcomes) - len(committed),
                "final_version": current.manifest_version,
                "current_manifest_id": None,
                "winner_identity_nondeterministic": True,
                "orphan_count": len(repo.list_orphan_manifest_fragments(PK)),
                "test_name": "test_exactly_one_current_v2",
            }
        if case.startswith("pointer_"):
            point = PointerFaultPoint(case.removeprefix("pointer_"))
            repo.append_partition_manifest(_manifest(), expected_current=None)
            v2 = _manifest(
                partition_manifest_id="pm-2",
                manifest_version=2,
                supersedes_manifest_id="pm-1",
            )
            faulted = False
            try:
                repo.append_partition_manifest(
                    v2,
                    expected_current=("pm-1", 1),
                    fault_hooks=RaisePointerFaultHook(point),
                )
            except RuntimeError:
                faulted = True
            fragment_dir = root / "catalogs" / "manifests" / "partitions"
            manifest_published = False
            for partition_dir in fragment_dir.glob("*"):
                if (partition_dir / f"v00000002-{hashlib.sha256(b'pm-2').hexdigest()[:32]}.parquet").exists():
                    manifest_published = True
            pointer_after = repo.read_current_pointer(PK)
            retry = repo.append_partition_manifest(v2, expected_current=("pm-1", 1))
            return {
                "case": case,
                "fault_point": point.value,
                "expected_current": ["pm-1", 1],
                "fault_raised": faulted,
                "manifest_published": manifest_published,
                "pointer_version_after_fault": pointer_after.manifest_version,
                "retry_disposition": retry.disposition.value,
                "retry_resolves": (
                    repo.get_current_manifest(PK).partition_manifest_id == "pm-2"
                ),
                "final_version": repo.get_current_manifest(PK).manifest_version,
                "orphan_count_after_retry": len(
                    repo.list_orphan_manifest_fragments(PK)
                ),
                "test_name": "test_pointer_crash_matrix",
            }
        raise AssertionError(f"unknown evidence case {case}")

    def test_manifest_concurrency_artifact_written(self, tmp_path: Path) -> None:
        cases = [
            "first_manifest",
            "sequential_v2",
            "eight_writer_same_base",
            "stale_writer",
            "duplicate_exact_manifest",
            "identity_conflict",
            "pointer_P1",
            "pointer_P2",
            "pointer_P3",
            "pointer_P4",
            "pointer_P5",
        ]
        rows: list[dict[str, Any]] = []
        for case in cases:
            root = tmp_path / case
            root.mkdir()
            rows.append(self._run_case(root, case))
        out_path = EVIDENCE_DIR / "BLOC_04_I04_MANIFEST_CONCURRENCY.json"
        out_path.write_text(
            json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        # deterministic: re-reading yields identical content
        again = json.loads(out_path.read_text(encoding="utf-8"))
        assert again == rows
        # invariants
        by_case = {r["case"]: r for r in rows}
        assert by_case["first_manifest"]["final_version"] == 1
        assert by_case["sequential_v2"]["final_version"] == 2
        assert by_case["stale_writer"]["stale_writer_rejected"] is True
        assert by_case["duplicate_exact_manifest"]["second_idempotent"] is True
        assert by_case["identity_conflict"]["identity_conflict_raised"] is True
        eight = by_case["eight_writer_same_base"]
        assert eight["winner_count"] == 1
        assert eight["winner_in_candidate_set"] is True
        assert eight["candidate_count"] == 8
        assert eight["loser_count"] == 7
        assert eight["final_version"] == 2
        assert eight["orphan_count"] == 0
        for point in ("P1", "P2", "P3", "P4", "P5"):
            row = by_case[f"pointer_{point}"]
            assert row["fault_raised"] is True
            assert row["retry_resolves"] is True
            assert row["final_version"] == 2
            assert row["orphan_count_after_retry"] == 0
            assert row["pointer_version_after_fault"] == (
                2 if point in ("P4", "P5") else 1
            )
            assert row["manifest_published"] is (point != "P1")
        # historical evidence untouched
        assert (EVIDENCE_DIR / "BLOC_04_I03R1_NAMESPACE_DURABILITY.json").exists()