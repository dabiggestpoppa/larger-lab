"""SENSOR-B4-I10 — rebuildable DuckDB discovery tests."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pytest

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.probes.enums import Granularity
from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
from crypto_sensor_fabric.storage.catalog import AcquisitionRepository, BlobMetadataRepository
from crypto_sensor_fabric.storage.duckdb_catalog import (
    VIEW_NAMES,
    DuckDBCatalogCorrupt,
    ReadOnlyDuckDBCatalog,
    rebuild_duckdb_catalog,
)
from crypto_sensor_fabric.storage.enums import CoverageState, StorageEncoding
from crypto_sensor_fabric.storage.manifests import PartitionManifest, PartitionManifestRepository
from crypto_sensor_fabric.storage.models import AcquisitionRecord
from crypto_sensor_fabric.storage.projection_lineage import ProjectionLineageRepository
from crypto_sensor_fabric.storage.projection_schema import (
    ProjectionSchemaDefinition,
    ProjectionSchemaRegistry,
)
from crypto_sensor_fabric.storage.projections import (
    ProjectionArtifactRepository,
    ProjectionContextRepository,
    T0BProjectionService,
)
from crypto_sensor_fabric.storage.recovery import RecoveryJournal
from crypto_sensor_fabric.storage.revisions import SourceRevisionRegistry

FIXED = datetime(2026, 1, 15, 12, tzinfo=UTC)
NATIVE_SCHEMA = pa.schema(
    [
        pa.field("price", pa.float64(), nullable=False),
        pa.field("qty", pa.int64(), nullable=True),
        pa.field("symbol", pa.string(), nullable=False),
    ]
)


def _snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class Fixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir()
        self.store = LocalBlobStore(str(root))
        self.blobs = BlobMetadataRepository(root, blob_store=self.store, clock=lambda: FIXED)
        self.acquisitions = AcquisitionRepository(
            root, blob_store=self.store, blob_metadata_repository=self.blobs, clock=lambda: FIXED
        )
        put = self.store.put_bytes(b'{"trade":1}', storage_encoding=StorageEncoding.NONE, source_media_type="application/json")
        self.blob = put.blob
        self.blobs.append_metadata(self.blob)
        self.acquisition = AcquisitionRecord(
            acquisition_id="acq-1",
            provider_id="kraken",
            venue="futures",
            sensor_family=SensorFamily.MECHANICAL_TRADE,
            request_fingerprint="request-1",
            adapter_version="1.0",
            requested_start=FIXED,
            requested_end=FIXED,
            native_instrument="BTC-USD",
            request_started_at=FIXED,
            response_observed_at=FIXED,
            ingested_at=FIXED,
            http_status_or_source_status="200",
            source_locator="fixture://trade-1",
            blob_sha256=self.blob.blob_sha256,
        )
        self.acquisitions.append_acquisition(self.acquisition)
        self.schemas = ProjectionSchemaRegistry(root / "catalogs" / "projection_schemas")
        self.schemas.register(
            ProjectionSchemaDefinition(
                projection_schema_id="i10.fixture",
                projection_schema_version="1.0.0",
                provider_native_schema=NATIVE_SCHEMA,
            )
        )
        self.artifacts = ProjectionArtifactRepository(
            root / "catalogs" / "manifests" / "projections",
            projection_root=root,
            schema_registry=self.schemas,
        )
        self.contexts = ProjectionContextRepository(root / "catalogs" / "manifests" / "projection_context")
        self.lineage = ProjectionLineageRepository(
            root / "catalogs" / "manifests" / "projection_lineage",
            blob_store=self.store,
            blob_metadata_repository=self.blobs,
            acquisition_repository=self.acquisitions,
            artifact_repository=self.artifacts,
            context_repository=self.contexts,
        )
        self.service = T0BProjectionService(
            root=root,
            blob_store=self.store,
            blob_metadata_repository=self.blobs,
            acquisition_repository=self.acquisitions,
            schema_registry=self.schemas,
            artifact_repository=self.artifacts,
            context_repository=self.contexts,
            lineage_repository=self.lineage,
            clock=lambda: FIXED,
        )
        self.projection, _ = self.service.commit_projection(
            rows=[{"price": 1.0, "qty": 1, "symbol": "BTC-USD"}],
            schema_definition=self.schemas.resolve_by_id("i10.fixture", "1.0.0"),
            projection_id="projection-1",
            source_blob_sha256=[self.blob.blob_sha256],
            acquisition_ids=[self.acquisition.acquisition_id],
            provider="kraken",
            venue="futures",
            sensor_family=SensorFamily.MECHANICAL_TRADE,
            native_instrument="BTC-USD",
            native_granularity="1m",
            parser_version="1.0.0",
            partition_key="kraken/futures/BTC-USD/2026-01-15",
            logical_year=2026,
            logical_month=1,
            logical_day=15,
            lineage_manifest_id="lineage-1",
        )
        from crypto_sensor_fabric.storage.projection_resolver import ProjectionLineageResolver

        self.resolver = ProjectionLineageResolver(
            root=root,
            artifacts=self.artifacts,
            contexts=self.contexts,
            lineage=self.lineage,
            schemas=self.schemas,
        )
        self.manifests = PartitionManifestRepository(
            root,
            blob_store=self.store,
            blob_metadata_repository=self.blobs,
            acquisition_repository=self.acquisitions,
            projection_lineage_resolver=self.resolver,
            clock=lambda: FIXED,
        )
        self.manifests.append_partition_manifest(
            PartitionManifest(
                partition_manifest_id="manifest-1",
                partition_key="kraken/futures/BTC-USD/2026-01-15",
                provider="kraken",
                venue="futures",
                sensor_family=SensorFamily.MECHANICAL_TRADE,
                native_instrument="BTC-USD",
                source_granularity=Granularity.G1M,
                logical_date_start=FIXED,
                logical_date_end=FIXED,
                blob_refs=[self.blob.blob_sha256],
                projection_refs=[self.projection.projection_id],
                coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
                created_at=FIXED,
            ),
            expected_current=None,
        )
        self.revisions = SourceRevisionRegistry(
            root / "catalogs" / "source_revisions",
            acquisition_repository=self.acquisitions,
            blob_metadata_repository=self.blobs,
            blob_store=self.store,
            clock=lambda: FIXED,
        )
        self.revisions.register_acquisition(self.acquisition.acquisition_id)
        RecoveryJournal(root).record(
            recovery_run_id="run-1",
            object_type="EVIDENCE_BLOB",
            object_id=self.blob.blob_sha256,
            problem="CORRUPT_BLOB",
            resolution="quarantined",
        )


@pytest.fixture
def evidence_root(tmp_path: Path) -> Path:
    fixture = Fixture(tmp_path / "evidence")
    return fixture.root


def _all_rows(catalog: Path) -> dict[str, list[list[object]]]:
    with ReadOnlyDuckDBCatalog(catalog) as reader:
        return {view: reader.canonical_view_rows(view) for view in VIEW_NAMES}


def test_build_empty_catalog_has_all_typed_views(tmp_path: Path) -> None:
    root = tmp_path / "empty"
    root.mkdir()
    output = tmp_path / "discovery.duckdb"
    receipt = rebuild_duckdb_catalog(root, output)
    assert set(receipt.view_row_counts) == set(VIEW_NAMES)
    assert all(count == 0 for count in receipt.view_row_counts.values())


def test_destroy_rebuild_and_rebuild_twire_are_equivalent(evidence_root: Path, tmp_path: Path) -> None:
    output = tmp_path / "catalog.duckdb"
    rebuild_duckdb_catalog(evidence_root, output)
    first = _all_rows(output)
    output.unlink()
    rebuild_duckdb_catalog(evidence_root, output)
    second = _all_rows(output)
    second_output = tmp_path / "catalog-2.duckdb"
    rebuild_duckdb_catalog(evidence_root, second_output)
    assert second == first == _all_rows(second_output)
    assert len(first["v_t0_blobs"]) == 1


def test_rebuild_does_not_mutate_evidence(evidence_root: Path, tmp_path: Path) -> None:
    before = _snapshot(evidence_root)
    rebuild_duckdb_catalog(evidence_root, tmp_path / "catalog.duckdb")
    assert _snapshot(evidence_root) == before


def test_views_preserve_lineage_missingness_revisions_and_quarantine(evidence_root: Path, tmp_path: Path) -> None:
    output = tmp_path / "catalog.duckdb"
    rebuild_duckdb_catalog(evidence_root, output)
    rows = _all_rows(output)
    assert len(rows["v_t0_projections"]) == 1
    assert rows["v_t0_projections"][0][-1] == 1
    assert len(rows["v_t0_revisions"]) == 1
    assert rows["v_t0_revisions"][0][1] == 1
    assert len(rows["v_t0_quarantine"]) == 1
    assert [row[3] for row in rows["v_t0_gaps"]] == ["QUARANTINED"]


def test_explicit_failed_missingness_is_not_zero_filled(evidence_root: Path, tmp_path: Path) -> None:
    fixture = Fixture.__new__(Fixture)
    fixture.root = evidence_root
    fixture.store = LocalBlobStore(str(evidence_root))
    fixture.blobs = BlobMetadataRepository(evidence_root, blob_store=fixture.store, clock=lambda: FIXED)
    fixture.acquisitions = AcquisitionRepository(evidence_root, blob_store=fixture.store, blob_metadata_repository=fixture.blobs, clock=lambda: FIXED)
    failed = AcquisitionRecord(
        acquisition_id="acq-failed",
        provider_id="kraken",
        venue="futures",
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        request_fingerprint="request-failed",
        adapter_version="1.0",
        requested_start=FIXED,
        requested_end=FIXED,
        native_instrument="BTC-USD",
        request_started_at=FIXED,
        response_observed_at=FIXED,
        ingested_at=FIXED,
        source_locator="fixture://failed",
        failure_ref="provider_timeout",
    )
    fixture.acquisitions.append_acquisition(failed)
    output = tmp_path / "catalog.duckdb"
    rebuild_duckdb_catalog(evidence_root, output)
    gaps = _all_rows(output)["v_t0_gaps"]
    assert any(
        row[2] == "acq-failed" and row[3] == "FAILED" for row in gaps
    )


def test_corrupt_manifest_fails_loudly_and_preserves_existing_catalog(evidence_root: Path, tmp_path: Path) -> None:
    output = tmp_path / "catalog.duckdb"
    rebuild_duckdb_catalog(evidence_root, output)
    before_output = output.read_bytes()
    manifest_path = next((evidence_root / "catalogs" / "manifests" / "partitions").glob("*/*.parquet"))
    manifest_path.write_bytes(b"not parquet")
    with pytest.raises(DuckDBCatalogCorrupt, match="partition manifest"):
        rebuild_duckdb_catalog(evidence_root, output)
    assert output.read_bytes() == before_output


def test_corrupt_projection_catalog_fails_loudly(evidence_root: Path, tmp_path: Path) -> None:
    target = next((evidence_root / "catalogs" / "manifests" / "projections").glob("*.json"))
    target.write_text("{broken", encoding="utf-8")
    with pytest.raises(DuckDBCatalogCorrupt, match="JSON catalog"):
        rebuild_duckdb_catalog(evidence_root, tmp_path / "catalog.duckdb")


def test_missing_projection_artifact_is_not_silently_ignored(evidence_root: Path, tmp_path: Path) -> None:
    next(evidence_root.rglob("*.parquet"))
    artifact_path = next(path for path in evidence_root.rglob("*.parquet") if "projections/provider=" in path.as_posix())
    artifact_path.unlink()
    with pytest.raises(DuckDBCatalogCorrupt, match="missing physical object"):
        rebuild_duckdb_catalog(evidence_root, tmp_path / "catalog.duckdb")


def test_root_relocation_preserves_canonical_ids(evidence_root: Path, tmp_path: Path) -> None:
    first = tmp_path / "first.duckdb"
    rebuild_duckdb_catalog(evidence_root, first)
    relocated = tmp_path / "relocated"
    shutil.copytree(evidence_root, relocated)
    second = tmp_path / "second.duckdb"
    rebuild_duckdb_catalog(relocated, second)
    first_rows = _all_rows(first)
    second_rows = _all_rows(second)
    for view in VIEW_NAMES:
        if view == "v_t0_storage_usage":
            continue
        first_ids = [row[:3] for row in first_rows[view]]
        second_ids = [row[:3] for row in second_rows[view]]
        assert second_ids == first_ids
    assert all("/" not in str(row[0]) for row in first_rows["v_t0_blobs"])


def test_read_only_query_rejects_mutation(evidence_root: Path, tmp_path: Path) -> None:
    output = tmp_path / "catalog.duckdb"
    rebuild_duckdb_catalog(evidence_root, output)
    with ReadOnlyDuckDBCatalog(output) as reader:
        with pytest.raises(Exception):
            reader.query_view("v_t0_blobs", "DELETE FROM v_t0_blobs")
        with pytest.raises(Exception):
            reader.query_view("v_t0_blobs", "SELECT 1; SELECT 2")


def test_multiple_revisions_are_preserved_without_latest_selection(
    evidence_root: Path, tmp_path: Path
) -> None:
    fixture = Fixture.__new__(Fixture)
    fixture.root = evidence_root
    fixture.store = LocalBlobStore(str(evidence_root))
    fixture.blobs = BlobMetadataRepository(
        evidence_root, blob_store=fixture.store, clock=lambda: FIXED
    )
    fixture.acquisitions = AcquisitionRepository(
        evidence_root,
        blob_store=fixture.store,
        blob_metadata_repository=fixture.blobs,
        clock=lambda: FIXED,
    )
    later = FIXED.replace(minute=1)
    second_blob = fixture.store.put_bytes(
        b'{"trade":2}',
        storage_encoding=StorageEncoding.NONE,
        source_media_type="application/json",
    ).blob
    fixture.blobs.append_metadata(second_blob)
    second = AcquisitionRecord(
        acquisition_id="acq-2",
        provider_id="kraken",
        venue="futures",                sensor_family=SensorFamily.MECHANICAL_TRADE,

        request_fingerprint="request-1",
        adapter_version="1.0",
        requested_start=FIXED,
        requested_end=FIXED,
        native_instrument="BTC-USD",
        request_started_at=later,
        response_observed_at=later,
        ingested_at=later,
        http_status_or_source_status="200",
        source_locator="fixture://trade-2",
        blob_sha256=second_blob.blob_sha256,
    )
    fixture.acquisitions.append_acquisition(second)
    registry = SourceRevisionRegistry(
        evidence_root / "catalogs" / "source_revisions",
        acquisition_repository=fixture.acquisitions,
        blob_metadata_repository=fixture.blobs,
        blob_store=fixture.store,
        clock=lambda: FIXED,
    )
    registry.register_acquisition(second.acquisition_id)

    output = tmp_path / "catalog.duckdb"
    rebuild_duckdb_catalog(evidence_root, output)
    rows = _all_rows(output)["v_t0_revisions"]
    revision_numbers = [int(str(row[1])) for row in rows]
    assert sorted(revision_numbers) == [1, 2]
    assert len({str(row[0]) for row in rows}) == 1


def test_dangling_current_pointer_fails_loudly(
    evidence_root: Path, tmp_path: Path
) -> None:
    pointer_path = next(
        (evidence_root / "catalogs" / "current" / "partitions").glob("*.json")
    )
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    pointer["partition_manifest_id"] = "0" * 64
    pointer_path.write_text(json.dumps(pointer), encoding="utf-8")
    with pytest.raises(DuckDBCatalogCorrupt, match="dangling or divergent"):
        rebuild_duckdb_catalog(evidence_root, tmp_path / "dangling-pointer.duckdb")


def test_missing_blob_fails_loudly(tmp_path: Path) -> None:
    root = tmp_path / "missing-blob-evidence"
    Fixture(root)
    physical = next(path for path in (root / "blobs").rglob("*") if path.is_file())
    physical.unlink()
    with pytest.raises(DuckDBCatalogCorrupt, match="missing physical object"):
        rebuild_duckdb_catalog(root, tmp_path / "missing-blob.duckdb")


def test_malformed_revision_evidence_fails_loudly(
    evidence_root: Path, tmp_path: Path
) -> None:
    target = next((evidence_root / "catalogs" / "source_revisions" / "segments").glob("*.json"))
    target.write_text("{broken", encoding="utf-8")
    with pytest.raises(DuckDBCatalogCorrupt, match="JSON catalog"):
        rebuild_duckdb_catalog(evidence_root, tmp_path / "catalog.duckdb")


def test_10k_manifest_scan_is_usable(evidence_root: Path, tmp_path: Path) -> None:
    from crypto_sensor_fabric.storage.manifests import (
        MANIFEST_SCHEMA,
        _manifest_row,
        publish_immutable_fragment,
    )

    rows = []
    for index in range(10_000):
        rows.append(
            _manifest_row(
                PartitionManifest(
                    partition_manifest_id=f"synthetic-{index:05d}",
                    partition_key=f"synthetic/{index:05d}",
                    provider="synthetic",
                    venue="test",
                    sensor_family=SensorFamily.MECHANICAL_TRADE,
                    native_instrument="BTC-USD",
                    logical_date_start=FIXED,
                    logical_date_end=FIXED,
                    created_at=FIXED,
                )
            )
        )
    publish_immutable_fragment(
        evidence_root,
        ["catalogs", "manifests", "partitions", "synthetic"],
        "synthetic-batch.parquet",
        MANIFEST_SCHEMA,
        rows,
        clock=lambda: FIXED,
    )
    output = tmp_path / "catalog.duckdb"
    receipt = rebuild_duckdb_catalog(evidence_root, output)
    assert receipt.view_row_counts["v_t0_partitions"] == 10_001
