"""SENSOR-B4-I10R1 — schema-contract, measured-evidence, discovery-cost tests.

Every test here executes the production rebuild/read path in deterministic
temp roots.  None of the booleans feeding R1 evidence builders are hard-coded:
the R1 builders import and call these execution helpers directly.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pyarrow as pa
import pytest
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.probes.enums import Granularity
from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
from crypto_sensor_fabric.storage.catalog import (
    AcquisitionRepository,
    BlobMetadataRepository,
)
from crypto_sensor_fabric.storage.duckdb_catalog import (
    VIEW_NAMES,
    DuckDBCatalogCorrupt,
    DuckDBCatalogError,
    DuckDBCatalogShapeCorrupt,
    DuckDBCatalogVersionError,
    ReadOnlyDuckDBCatalog,
    rebuild_duckdb_catalog,
)
from crypto_sensor_fabric.storage.enums import CoverageState, StorageEncoding
from crypto_sensor_fabric.storage.manifests import (
    PartitionManifest,
    PartitionManifestRepository,
)
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
        from crypto_sensor_fabric.storage.projection_resolver import (
            ProjectionLineageResolver,
        )

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


def _pragma_schema(catalog: Path, view: str) -> list[tuple[object, ...]]:
    with ReadOnlyDuckDBCatalog(catalog) as reader:
        return [
            (row[1], row[2])
            for row in reader._connection.execute(f"PRAGMA table_info('{view}')").fetchall()
        ]


def _rewrite_recovery_action(root: Path, mutate) -> None:
    """Rewrite the single durable recovery action fragment in a fixture root."""
    directory = root / "catalogs" / "recovery" / "actions"
    fragment = next(directory.glob("*.json"))
    payload = json.loads(fragment.read_text(encoding="utf-8"))
    mutate(payload)
    logical_id = payload["recovery_action_id"]
    digest = hashlib.sha256(logical_id.encode("utf-8")).hexdigest()
    target = directory / f"{digest}.json"
    if target != fragment:
        fragment.unlink()
    target.write_text(json.dumps(payload), encoding="utf-8")


def _rebuild_partitions_view(evidence_root: Path, tmp_path: Path) -> Path:
    output = tmp_path / "catalog.duckdb"
    rebuild_duckdb_catalog(evidence_root, output)
    return output


# ---------------------------------------------------------------------------
# §18 test battery — schema contract
# ---------------------------------------------------------------------------


def test_i10r1_all_eight_views_have_exact_contract_schema_populated(
    evidence_root: Path, tmp_path: Path
) -> None:
    from crypto_sensor_fabric.storage.duckdb_catalog import VIEW_SCHEMAS

    output = _rebuild_partitions_view(evidence_root, tmp_path)
    for view in VIEW_NAMES:
        assert _pragma_schema(output, view) == list(VIEW_SCHEMAS[view]), view


def test_i10r1_all_eight_views_have_exact_contract_schema_empty(
    tmp_path: Path,
) -> None:
    from crypto_sensor_fabric.storage.duckdb_catalog import VIEW_SCHEMAS

    root = tmp_path / "empty"
    root.mkdir()
    output = tmp_path / "catalog.duckdb"
    rebuild_duckdb_catalog(root, output)
    for view in VIEW_NAMES:
        assert _pragma_schema(output, view) == list(VIEW_SCHEMAS[view]), view


def test_i10r1_nullable_first_row_cannot_change_a_numeric_type() -> None:
    import duckdb
    from crypto_sensor_fabric.storage.duckdb_catalog import _create_table

    con = duckdb.connect(":memory:")
    rows = [
        {
            "evidence_class": "PARTITION_MANIFEST",
            "integrity_state": "LOCAL_HASH_VERIFIED",
            "provider": "providerA",
            "sensor_family": "MECHANICAL_TRADE",
            "storage_priority": "P0",
            "universe_tier": None,
            "stored_bytes": None,
            "raw_bytes": 0,
            "projection_bytes": 0,
            "object_count": 1,
        },
        {
            "evidence_class": "T0B_PROJECTION",
            "integrity_state": "COMPLETE",
            "provider": "providerB",
            "sensor_family": "MECHANICAL_FUNDING",
            "storage_priority": "P3",
            "universe_tier": None,
            "stored_bytes": 12345,
            "raw_bytes": 0,
            "projection_bytes": 12345,
            "object_count": 1,
        },
    ]
    _create_table(con, "v_t0_storage_usage", rows)
    info = {
        row[1]: row[2]
        for row in con.execute("PRAGMA table_info('v_t0_storage_usage')").fetchall()
    }
    assert info["stored_bytes"] == "BIGINT"
    assert con.execute("SELECT max(stored_bytes) FROM v_t0_storage_usage").fetchone() == (12345,)


def test_i10r1_missing_row_key_is_refused_not_null_backfilled() -> None:
    import duckdb
    from crypto_sensor_fabric.storage.duckdb_catalog import _create_table

    con = duckdb.connect(":memory:")
    full = {"gap_id": "g1", "scope": "PARTITION", "scope_id": "p1", "missingness": "PARTIAL", "detail": None}
    stripped = {"gap_id": "g2", "scope": "PARTITION", "scope_id": "p2", "missingness": "KNOWN_GAP"}
    with pytest.raises(DuckDBCatalogShapeCorrupt, match="missing"):
        _create_table(con, "v_t0_gaps", [full, stripped])


def test_i10r1_extra_row_key_is_refused() -> None:
    import duckdb
    from crypto_sensor_fabric.storage.duckdb_catalog import _create_table

    con = duckdb.connect(":memory:")
    row = {"gap_id": "g1", "scope": "PARTITION", "scope_id": "p1", "missingness": "PARTIAL", "detail": None, "rogue": "x"}
    with pytest.raises(DuckDBCatalogShapeCorrupt, match="unexpected"):
        _create_table(con, "v_t0_gaps", [row])


def test_i10r1_wrong_scalar_type_is_refused() -> None:
    import duckdb
    from crypto_sensor_fabric.storage.duckdb_catalog import _create_table

    con = duckdb.connect(":memory:")
    row = {
        "projection_id": "p1", "provider": "kraken", "venue": "futures",
        "sensor_family": "MECHANICAL_TRADE", "native_instrument": "BTC-USD",
        "partition_key": "k", "projection_schema_id": "s",
        "projection_schema_version": "1", "parser_version": "1",
        "projection_object_key": "o", "backend_id": "b",
        "resolved_local_path": "p", "projection_sha256": "h",
        "row_count": "7",  # string where BIGINT is contracted
        "stored_bytes": 5, "state": "COMPLETE",
        "lineage_manifest_id": "l", "source_count": 1,
    }
    with pytest.raises(DuckDBCatalogShapeCorrupt, match="row_count"):
        _create_table(con, "v_t0_projections", [row])


def test_i10r1_wrong_list_type_is_refused() -> None:
    import duckdb
    from crypto_sensor_fabric.storage.duckdb_catalog import _create_table

    con = duckdb.connect(":memory:")
    row = {
        "partition_manifest_id": "m1", "partition_key": "k",
        "manifest_version": 1, "is_current": True, "provider": "kraken",
        "venue": "futures", "sensor_family": "MECHANICAL_TRADE",
        "native_instrument": "BTC-USD",
        "blob_refs": "not-a-list",
        "projection_refs": ["p1"], "coverage_state": "PARTIAL",
        "integrity_state": "LOCAL_HASH_VERIFIED", "gap_count": None,
        "revision_count": 0, "supersedes_manifest_id": None,
    }
    with pytest.raises(DuckDBCatalogShapeCorrupt, match="blob_refs"):
        _create_table(con, "v_t0_partitions", [row])


# ---------------------------------------------------------------------------
# §18 — storage-usage dimensions
# ---------------------------------------------------------------------------


def test_i10r1_multi_provider_storage_usage_stays_separate() -> None:
    from crypto_sensor_fabric.storage.duckdb_catalog import _storage_usage

    projection = {
        "projection_id": "p", "provider": "providerA", "venue": "v",
        "sensor_family": "SENSOR_X", "native_instrument": "i",
        "partition_key": "k", "projection_schema_id": "s",
        "projection_schema_version": "1", "parser_version": "1",
        "projection_object_key": "o", "backend_id": "b",
        "resolved_local_path": "p", "projection_sha256": "h",
        "row_count": 1, "stored_bytes": 500, "state": "COMPLETE",
        "lineage_manifest_id": "l", "source_count": 1,
    }
    other = dict(projection, provider="providerB", sensor_family="SENSOR_Y")
    usage = _storage_usage([], [projection, other], [], [])
    t0b = [row for row in usage if row["evidence_class"] == "T0B_PROJECTION"]
    assert len(t0b) == 2
    assert {(row["provider"], row["sensor_family"]) for row in t0b} == {
        ("providerA", "SENSOR_X"),
        ("providerB", "SENSOR_Y"),
    }
    assert sum(row["object_count"] for row in t0b) == 2
    assert sum(row["projection_bytes"] for row in t0b) == 1000


def test_i10r1_multi_sensor_storage_usage_stays_separate() -> None:
    from crypto_sensor_fabric.storage.duckdb_catalog import _storage_usage

    partition = {
        "partition_manifest_id": "m", "partition_key": "k",
        "manifest_version": 1, "is_current": True, "provider": "providerA",
        "venue": "v", "sensor_family": "SENSOR_X", "native_instrument": "i",
        "blob_refs": ["a"], "projection_refs": ["p"],
        "coverage_state": "PARTIAL", "integrity_state": "LOCAL_HASH_VERIFIED",
        "gap_count": None, "revision_count": 0, "supersedes_manifest_id": None,
    }
    other = dict(partition, partition_manifest_id="m2", partition_key="k2", sensor_family="SENSOR_Y")
    usage = _storage_usage([], [], [partition, other], [])
    part_rows = [row for row in usage if row["evidence_class"] == "PARTITION_MANIFEST"]
    assert len(part_rows) == 2
    assert {row["sensor_family"] for row in part_rows} == {"SENSOR_X", "SENSOR_Y"}


def test_i10r1_t0a_provider_stays_null_and_totals_reconcile() -> None:
    from crypto_sensor_fabric.storage.duckdb_catalog import _storage_usage

    blob = {
        "blob_sha256": "a" * 64, "byte_length": 100, "stored_byte_length": 90,
        "storage_object_key": "k", "backend_id": "b", "resolved_local_path": "p",
        "source_media_type": "application/json", "storage_encoding": "NONE",
        "integrity_state": "LOCAL_HASH_VERIFIED", "created_at": FIXED.isoformat(),
    }
    other = dict(blob, blob_sha256="b" * 64, byte_length=40, stored_byte_length=40)
    usage = _storage_usage([blob, other], [], [], [])
    assert len(usage) == 1
    row = usage[0]
    assert row["evidence_class"] == "T0A_BLOB"
    assert row["provider"] is None and row["sensor_family"] is None
    assert row["storage_priority"] is None and row["universe_tier"] is None
    assert row["object_count"] == 2
    assert row["stored_bytes"] == 130 and row["raw_bytes"] == 140


# ---------------------------------------------------------------------------
# §18 — catalog version gate at read-only open
# ---------------------------------------------------------------------------


def _mutated_catalog_copy(catalog: Path, tmp_path: Path, mutate) -> Path:
    import duckdb

    copy = tmp_path / f"{catalog.stem}-{mutate.__name__}.duckdb"
    shutil.copyfile(catalog, copy)
    con = duckdb.connect(str(copy))
    try:
        mutate(con)
    finally:
        con.close()
    return copy


def test_i10r1_stale_catalog_version_is_refused_at_open(
    evidence_root: Path, tmp_path: Path
) -> None:
    output = _rebuild_partitions_view(evidence_root, tmp_path)

    def downgrade(con) -> None:
        con.execute("UPDATE catalog_metadata SET schema_version = '0.9'")

    stale = _mutated_catalog_copy(output, tmp_path, downgrade)
    with pytest.raises(DuckDBCatalogVersionError, match="schema_version"):
        ReadOnlyDuckDBCatalog(stale)


def test_i10r1_future_catalog_version_is_refused_at_open(
    evidence_root: Path, tmp_path: Path
) -> None:
    output = _rebuild_partitions_view(evidence_root, tmp_path)

    def upgrade(con) -> None:
        con.execute("UPDATE catalog_metadata SET schema_version = '9.9'")

    future = _mutated_catalog_copy(output, tmp_path, upgrade)
    with pytest.raises(DuckDBCatalogVersionError, match="schema_version"):
        ReadOnlyDuckDBCatalog(future)


def test_i10r1_missing_catalog_metadata_is_refused_at_open(
    evidence_root: Path, tmp_path: Path
) -> None:
    output = _rebuild_partitions_view(evidence_root, tmp_path)

    def drop_metadata(con) -> None:
        con.execute("DROP TABLE catalog_metadata")

    stripped = _mutated_catalog_copy(output, tmp_path, drop_metadata)
    with pytest.raises(DuckDBCatalogVersionError, match="catalog_metadata"):
        ReadOnlyDuckDBCatalog(stripped)


def test_i10r1_duplicate_metadata_rows_are_refused_at_open(
    evidence_root: Path, tmp_path: Path
) -> None:
    output = _rebuild_partitions_view(evidence_root, tmp_path)

    def duplicate(con) -> None:
        con.execute(
            "INSERT INTO catalog_metadata VALUES ('1.0', 'rebuildable_discovery_non_authoritative')"
        )

    doubled = _mutated_catalog_copy(output, tmp_path, duplicate)
    with pytest.raises(DuckDBCatalogVersionError, match="exactly one metadata row"):
        ReadOnlyDuckDBCatalog(doubled)


def test_i10r1_wrong_role_metadata_is_refused_at_open(
    evidence_root: Path, tmp_path: Path
) -> None:
    output = _rebuild_partitions_view(evidence_root, tmp_path)

    def reassign(con) -> None:
        con.execute("UPDATE catalog_metadata SET data_root_role = 'authoritative'")

    hostile = _mutated_catalog_copy(output, tmp_path, reassign)
    with pytest.raises(DuckDBCatalogVersionError, match="data_root_role"):
        ReadOnlyDuckDBCatalog(hostile)


# ---------------------------------------------------------------------------
# §18 — measured discovery cost (Defect C)
# ---------------------------------------------------------------------------


def test_i10r1_default_rebuild_never_calls_verify_blob(
    evidence_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import crypto_sensor_fabric.storage.blob_store as blob_store_module

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("default discovery rebuild must not verify blob payloads")

    monkeypatch.setattr(blob_store_module.LocalBlobStore, "verify_blob", forbidden)
    receipt = rebuild_duckdb_catalog(evidence_root, tmp_path / "catalog.duckdb")
    assert receipt.view_row_counts["v_t0_blobs"] == 1


def test_i10r1_default_rebuild_never_decodes_t0a_payloads(
    evidence_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import crypto_sensor_fabric.storage.blob_store as blob_store_module

    def forbidden_decode(self, _path: object, _encoding: object) -> object:
        raise AssertionError("default discovery rebuild must not decode T0A payloads")

    def forbidden_verify(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("default discovery rebuild must not verify blob payloads")

    monkeypatch.setattr(blob_store_module.LocalBlobStore, "_decode_stats", forbidden_decode)
    monkeypatch.setattr(blob_store_module.LocalBlobStore, "verify_blob", forbidden_verify)
    rebuild_duckdb_catalog(evidence_root, tmp_path / "catalog.duckdb")


def test_i10r1_large_blob_discovery_is_metadata_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An 8 MiB payload is discovered without reading a single payload byte."""
    import crypto_sensor_fabric.storage.blob_store as blob_store_module

    root = tmp_path / "big-evidence"
    root.mkdir()
    store = LocalBlobStore(str(root))
    put = store.put_bytes(
        b"\0" * (8 * 1024 * 1024),
        storage_encoding=StorageEncoding.NONE,
        source_media_type="application/json",
    )
    blobs = BlobMetadataRepository(root, blob_store=store, clock=lambda: FIXED)
    blobs.append_metadata(put.blob)

    def forbidden(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("metadata discovery must not read payload content")

    monkeypatch.setattr(blob_store_module.LocalBlobStore, "verify_blob", forbidden)
    receipt = rebuild_duckdb_catalog(root, tmp_path / "big.duckdb")
    assert receipt.view_row_counts["v_t0_blobs"] == 1


def test_i10r1_missing_physical_blob_is_still_refused(tmp_path: Path) -> None:
    root = tmp_path / "missing-blob-evidence"
    Fixture(root)
    physical = next(path for path in (root / "blobs").rglob("*") if path.is_file())
    physical.unlink()
    with pytest.raises(DuckDBCatalogCorrupt, match="missing physical object"):
        rebuild_duckdb_catalog(root, tmp_path / "missing-blob.duckdb")


def test_i10r1_stored_size_divergence_is_still_refused(
    evidence_root: Path, tmp_path: Path
) -> None:
    physical = next(path for path in (evidence_root / "blobs").rglob("*") if path.is_file())
    truncated = physical.read_bytes()[:-1]
    physical.write_bytes(truncated)
    with pytest.raises(DuckDBCatalogCorrupt, match="stored byte length diverges"):
        rebuild_duckdb_catalog(evidence_root, tmp_path / "catalog.duckdb")


# ---------------------------------------------------------------------------
# §18 — durable relation validation (Defects D/E)
# ---------------------------------------------------------------------------


def test_i10r1_malformed_recovery_action_is_refused_not_null_backfilled(
    evidence_root: Path, tmp_path: Path
) -> None:
    def strip(payload: dict) -> None:
        for field in ("recovery_run_id", "object_type", "object_id", "problem", "resolution"):
            payload.pop(field, None)

    _rewrite_recovery_action(evidence_root, strip)
    with pytest.raises(DuckDBCatalogCorrupt, match="recovery action"):
        rebuild_duckdb_catalog(evidence_root, tmp_path / "catalog.duckdb")


def test_i10r1_recovery_action_identity_divergence_is_refused(
    evidence_root: Path, tmp_path: Path
) -> None:
    def tamper(payload: dict) -> None:
        payload["problem"] = "TAMPROBLEM"

    _rewrite_recovery_action(evidence_root, tamper)
    with pytest.raises(DuckDBCatalogCorrupt, match="identity diverges"):
        rebuild_duckdb_catalog(evidence_root, tmp_path / "catalog.duckdb")


def test_i10r1_orphan_lineage_manifest_is_refused(
    evidence_root: Path, tmp_path: Path
) -> None:
    lineage_dir = evidence_root / "catalogs" / "manifests" / "projection_lineage"
    orphan = json.loads(next(lineage_dir.glob("*.json")).read_text(encoding="utf-8"))
    orphan["lineage_manifest_id"] = "orphan-lineage-1"
    for entry in orphan["entries"]:
        entry["projection_id"] = "projection-does-not-exist"
        entry["lineage_manifest_id"] = "orphan-lineage-1"
    digest = hashlib.sha256(b"orphan-lineage-1").hexdigest()
    (lineage_dir / f"{digest}.json").write_text(json.dumps(orphan), encoding="utf-8")
    with pytest.raises(DuckDBCatalogCorrupt, match="without projection artifacts"):
        rebuild_duckdb_catalog(evidence_root, tmp_path / "catalog.duckdb")


def test_i10r1_valid_artifact_context_lineage_chain_is_accepted(
    evidence_root: Path, tmp_path: Path
) -> None:
    output = _rebuild_partitions_view(evidence_root, tmp_path)
    rows = _all_rows(output)["v_t0_projections"]
    assert len(rows) == 1
    assert rows[0][16] == "lineage-1"
    assert rows[0][17] == 1


# ---------------------------------------------------------------------------
# §18 — missingness preservation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("state", list(CoverageState))
def test_i10r1_frozen_missingness_states_are_preserved_verbatim(
    evidence_root: Path, tmp_path: Path, state: CoverageState
) -> None:
    fixture = Fixture.__new__(Fixture)
    fixture.root = evidence_root
    fixture.store = LocalBlobStore(str(evidence_root))
    fixture.blobs = BlobMetadataRepository(evidence_root, blob_store=fixture.store, clock=lambda: FIXED)
    fixture.acquisitions = AcquisitionRepository(
        evidence_root, blob_store=fixture.store, blob_metadata_repository=fixture.blobs, clock=lambda: FIXED
    )
    fixture.artifacts = ProjectionArtifactRepository(
        evidence_root / "catalogs" / "manifests" / "projections",
        projection_root=evidence_root,
        schema_registry=ProjectionSchemaRegistry(evidence_root / "catalogs" / "projection_schemas"),
    )
    fixture.contexts = ProjectionContextRepository(evidence_root / "catalogs" / "manifests" / "projection_context")
    fixture.lineage = ProjectionLineageRepository(
        evidence_root / "catalogs" / "manifests" / "projection_lineage",
        blob_store=fixture.store,
        blob_metadata_repository=fixture.blobs,
        acquisition_repository=fixture.acquisitions,
        artifact_repository=fixture.artifacts,
        context_repository=fixture.contexts,
    )
    from crypto_sensor_fabric.storage.projection_resolver import (
        ProjectionLineageResolver,
    )

    fixture.resolver = ProjectionLineageResolver(
        root=evidence_root,
        artifacts=fixture.artifacts,
        contexts=fixture.contexts,
        lineage=fixture.lineage,
        schemas=ProjectionSchemaRegistry(evidence_root / "catalogs" / "projection_schemas"),
    )
    fixture.manifests = PartitionManifestRepository(
        evidence_root,
        blob_store=fixture.store,
        blob_metadata_repository=fixture.blobs,
        acquisition_repository=fixture.acquisitions,
        projection_lineage_resolver=fixture.resolver,
        clock=lambda: FIXED,
    )
    fixture.manifests.append_partition_manifest(
        PartitionManifest(
            partition_manifest_id=f"manifest-{state.value}",
            partition_key=f"synthetic-{state.value}",
            provider="kraken",
            venue="futures",
            sensor_family=SensorFamily.MECHANICAL_TRADE,
            native_instrument="BTC-USD",
            source_granularity=Granularity.G1M,
            logical_date_start=FIXED,
            logical_date_end=FIXED,
            coverage_state=state,
            created_at=FIXED,
        ),
        expected_current=None,
    )
    output = _rebuild_partitions_view(evidence_root, tmp_path)
    gaps = _all_rows(output)["v_t0_gaps"]
    partition_gaps = [row for row in gaps if row[1] == "PARTITION"]
    if state is CoverageState.COMPLETE_SOURCE_BOUNDARY:
        assert all(row[3] != "COMPLETE_SOURCE_BOUNDARY" for row in partition_gaps)
    else:
        assert any(row[3] == state.value for row in partition_gaps), (state.value, partition_gaps)


def _fixture_blob_sha256(root: Path) -> str:
    physical = next(path for path in (root / "blobs").rglob("*") if path.is_file())
    return hashlib.sha256(physical.read_bytes()).hexdigest()


def _fixture_projection_id(root: Path) -> str:
    manifest_dir = root / "catalogs" / "manifests" / "projections"
    payload = json.loads(next(manifest_dir.glob("*.json")).read_text(encoding="utf-8"))
    return payload["projection_id"]


def test_i10r1_acquisition_missingness_stays_separate_from_partition_coverage(
    evidence_root: Path, tmp_path: Path
) -> None:
    """Acquisition-derived fallbacks (FAILED/NOT_ATTEMPTED) never overwrite
    partition coverage truth, and stay visibly separate rows."""
    fixture = Fixture.__new__(Fixture)
    fixture.root = evidence_root
    fixture.store = LocalBlobStore(str(evidence_root))
    fixture.blobs = BlobMetadataRepository(evidence_root, blob_store=fixture.store, clock=lambda: FIXED)
    fixture.acquisitions = AcquisitionRepository(
        evidence_root, blob_store=fixture.store, blob_metadata_repository=fixture.blobs, clock=lambda: FIXED
    )
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
    output = _rebuild_partitions_view(evidence_root, tmp_path)
    gaps = _all_rows(output)["v_t0_gaps"]
    assert any(row[1] == "ACQUISITION" and row[3] == "FAILED" for row in gaps)
    assert all(row[1] != "PARTITION" or row[3] != "FAILED" for row in gaps)


# ---------------------------------------------------------------------------
# §18 — publication preservation + consumer read-only
# ---------------------------------------------------------------------------


def test_i10r1_failed_shape_rebuild_preserves_published_catalog(
    evidence_root: Path, tmp_path: Path
) -> None:
    output = tmp_path / "catalog.duckdb"
    rebuild_duckdb_catalog(evidence_root, output)
    before_output = output.read_bytes()
    _rewrite_recovery_action(evidence_root, lambda payload: payload.pop("problem", None))
    with pytest.raises(DuckDBCatalogCorrupt):
        rebuild_duckdb_catalog(evidence_root, output)
    assert output.read_bytes() == before_output


def test_i10r1_consumer_remains_read_only(
    evidence_root: Path, tmp_path: Path
) -> None:
    output = _rebuild_partitions_view(evidence_root, tmp_path)
    with ReadOnlyDuckDBCatalog(output) as reader:
        with pytest.raises(DuckDBCatalogError):
            reader.query_view("v_t0_blobs", "DELETE FROM v_t0_blobs")
        with pytest.raises(DuckDBCatalogError):
            reader.query_view("v_t0_blobs", "SELECT 1; SELECT 2")
        with pytest.raises(DuckDBCatalogError):
            reader.query_view("v_t0_blobs", "UPDATE v_t0_blobs SET blob_sha256 = 'x'")
        # The connection itself is opened read-only: even a valid SELECT-
        # shaped statement cannot mutate (defense in depth at the DB layer).
        with pytest.raises(duckdb.Error):
            reader._connection.execute("CREATE OR REPLACE TABLE v_t0_blobs AS SELECT 1")


# ---------------------------------------------------------------------------
# Measured-fact execution helpers for the R1 evidence builders (§14/§15).
# Each helper returns observed booleans; builders must NOT hard-code them.
# ---------------------------------------------------------------------------


def measure_contract_schema(evidence_root: Path, catalog: Path) -> dict[str, bool]:
    from crypto_sensor_fabric.storage.duckdb_catalog import VIEW_SCHEMAS

    return {
        "all_view_schemas_exact": all(
            _pragma_schema(catalog, view) == list(VIEW_SCHEMAS[view]) for view in VIEW_NAMES
        ),
        "metadata_row_exact": _catalog_metadata_rows(catalog)
        == [("1.0", "rebuildable_discovery_non_authoritative")],
    }


def _catalog_metadata_rows(catalog: Path) -> list[tuple[object, ...]]:
    import duckdb

    con = duckdb.connect(str(catalog), read_only=True)
    try:
        return con.execute("SELECT schema_version, data_root_role FROM catalog_metadata").fetchall()
    finally:
        con.close()
