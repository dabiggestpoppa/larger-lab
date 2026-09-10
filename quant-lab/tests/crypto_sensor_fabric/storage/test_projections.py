"""SENSOR-B4-I05B — T0B Parquet writer and projection artifact catalog tests.

Covers:
  - single-blob projection exact source refs
  - row ordinal deterministic contiguous
  - physical projection SHA verified
  - same projection id / identical artifact idempotent
  - same projection id / different bytes rejected
  - same projection id / different schema rejected
  - schema mismatch rejected
  - null preservation
  - type preservation (provider-native round trip)
  - reserved column rejected
  - provider-native fields preserved
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from crypto_sensor_fabric.storage.projection_schema import (
    ProjectionSchemaDefinition,
    ProjectionSchemaRegistry,
    ReservedProjectionColumn,
)
from crypto_sensor_fabric.storage.projections import (
    ProjectionArtifactRepository,
    ProjectionIdentityConflict,
    ProjectionSchemaMismatch,
    ProjectionWriteError,
    write_projection,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def provider_native_schema() -> pa.Schema:
    """Minimal valid provider-native Arrow schema."""
    return pa.schema(
        [
            pa.field("price", pa.float64(), nullable=False),
            pa.field("qty", pa.int64(), nullable=True),
            pa.field("symbol", pa.string(), nullable=False),
        ]
    )


@pytest.fixture()
def schema_definition(provider_native_schema: pa.Schema) -> ProjectionSchemaDefinition:
    """Registered schema definition."""
    return ProjectionSchemaDefinition(
        projection_schema_id="test.market.liquidation",
        projection_schema_version="1.0.0",
        provider_native_schema=provider_native_schema,
    )


@pytest.fixture()
def schema_registry(
    tmp_path: Path, schema_definition: ProjectionSchemaDefinition
) -> ProjectionSchemaRegistry:
    """Registry with the schema registered."""
    catalog_root = tmp_path / "catalogs" / "projection_schemas"
    registry = ProjectionSchemaRegistry(catalog_root)
    registry.register(schema_definition)
    return registry


@pytest.fixture()
def projection_root(tmp_path: Path) -> Path:
    """Fresh projection root directory (short path for Windows MAX_PATH)."""
    # Use C:/tmp_proj to stay within Windows 260-char path limit
    # (the full projection path with 64-char schema key exceeds 260 chars
    # under the default deep pytest tmp_path)
    root = Path("C:/tmp_proj")
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    yield root
    if root.exists():
        shutil.rmtree(root)


@pytest.fixture()
def sample_rows() -> list[dict]:
    """Sample provider-native rows."""
    return [
        {"price": 100.5, "qty": 10, "symbol": "BTC-USDT"},
        {"price": 200.0, "qty": None, "symbol": "ETH-USDT"},
        {"price": 50.25, "qty": 5, "symbol": "SOL-USDT"},
    ]


@pytest.fixture()
def projection_artifact_repo(tmp_path: Path) -> ProjectionArtifactRepository:
    """Fresh projection artifact repository."""
    catalog_root = tmp_path / "catalogs" / "manifests" / "projections"
    return ProjectionArtifactRepository(catalog_root)


# ---------------------------------------------------------------------------
# Core write tests
# ---------------------------------------------------------------------------


class TestWriteProjection:
    def test_single_blob_projection(
        self,
        projection_root: Path,
        sample_rows: list[dict],
        schema_definition: ProjectionSchemaDefinition,
    ) -> None:
        artifact, path = write_projection(
            root=projection_root,
            rows=sample_rows,
            schema_definition=schema_definition,
            projection_id="proj-001",
            source_blob_sha256=["a" * 64],
            acquisition_ids=["acq-001"],
            provider="kraken",
            venue="futures",
            sensor_family="market_data",
            native_instrument="BTC-USDT",
            native_granularity="1m",
            parser_version="1.0.0",
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            logical_year=2026,
            logical_month=1,
            logical_day=15,
        )
        assert path.exists()
        assert artifact.row_count == 3
        assert artifact.projection_id == "proj-001"
        assert artifact.source_blob_sha256 == ["a" * 64]
        assert artifact.projection_schema_id == "test.market.liquidation"
        assert artifact.projection_schema_version == "1.0.0"

    def test_row_ordinals_contiguous(
        self,
        projection_root: Path,
        sample_rows: list[dict],
        schema_definition: ProjectionSchemaDefinition,
    ) -> None:
        artifact, path = write_projection(
            root=projection_root,
            rows=sample_rows,
            schema_definition=schema_definition,
            projection_id="proj-ordinals",
            source_blob_sha256=["b" * 64],
            acquisition_ids=["acq-002"],
            provider="kraken",
            venue="futures",
            sensor_family="market_data",
            native_instrument="BTC-USDT",
            native_granularity="1m",
            parser_version="1.0.0",
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            logical_year=2026,
            logical_month=1,
            logical_day=15,
        )
        table = pq.read_table(str(path))
        ordinals = table.column("_t0_row_ordinal").to_pylist()
        assert ordinals == [0, 1, 2]

    def test_single_source_row_metadata_exact(
        self,
        projection_root: Path,
        sample_rows: list[dict],
        schema_definition: ProjectionSchemaDefinition,
    ) -> None:
        source_sha = "c" * 64
        artifact, path = write_projection(
            root=projection_root,
            rows=sample_rows,
            schema_definition=schema_definition,
            projection_id="proj-meta",
            source_blob_sha256=[source_sha],
            acquisition_ids=["acq-003"],
            provider="kraken",
            venue="futures",
            sensor_family="market_data",
            native_instrument="BTC-USDT",
            native_granularity="1m",
            parser_version="1.0.0",
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            logical_year=2026,
            logical_month=1,
            logical_day=15,
        )
        table = pq.read_table(str(path))
        for i in range(3):
            assert table.column("_t0_source_blob_sha256")[i].as_py() == source_sha
            assert table.column("_t0_acquisition_id")[i].as_py() == "acq-003"
            assert table.column("_t0_provider")[i].as_py() == "kraken"
            assert table.column("_t0_schema_version")[i].as_py() == "1.0.0"

    def test_projection_sha_matches_physical(
        self,
        projection_root: Path,
        sample_rows: list[dict],
        schema_definition: ProjectionSchemaDefinition,
    ) -> None:
        artifact, path = write_projection(
            root=projection_root,
            rows=sample_rows,
            schema_definition=schema_definition,
            projection_id="proj-sha",
            source_blob_sha256=["d" * 64],
            acquisition_ids=["acq-004"],
            provider="kraken",
            venue="futures",
            sensor_family="market_data",
            native_instrument="BTC-USDT",
            native_granularity="1m",
            parser_version="1.0.0",
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            logical_year=2026,
            logical_month=1,
            logical_day=15,
        )
        from crypto_sensor_fabric.storage.checksums import sha256_file

        actual_sha = sha256_file(str(path)).hex_digest
        assert artifact.projection_sha256 == actual_sha

    def test_empty_rows_rejected(
        self,
        projection_root: Path,
        schema_definition: ProjectionSchemaDefinition,
    ) -> None:
        with pytest.raises(ProjectionWriteError, match="at least one row"):
            write_projection(
                root=projection_root,
                rows=[],
                schema_definition=schema_definition,
                projection_id="proj-empty",
                source_blob_sha256=["e" * 64],
                acquisition_ids=["acq-005"],
                provider="kraken",
                venue="futures",
                sensor_family="market_data",
                native_instrument="BTC-USDT",
                native_granularity="1m",
                parser_version="1.0.0",
                partition_key="kraken/futures/BTC-USDT/2026-01-15",
                logical_year=2026,
                logical_month=1,
                logical_day=15,
            )


# ---------------------------------------------------------------------------
# Idempotent / conflict tests
# ---------------------------------------------------------------------------


class TestProjectionIdempotent:
    def test_idempotent_same_bytes(
        self,
        projection_root: Path,
        sample_rows: list[dict],
        schema_definition: ProjectionSchemaDefinition,
    ) -> None:
        kwargs = dict(
            root=projection_root,
            rows=sample_rows,
            schema_definition=schema_definition,
            projection_id="proj-idem",
            source_blob_sha256=["f" * 64],
            acquisition_ids=["acq-006"],
            provider="kraken",
            venue="futures",
            sensor_family="market_data",
            native_instrument="BTC-USDT",
            native_granularity="1m",
            parser_version="1.0.0",
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            logical_year=2026,
            logical_month=1,
            logical_day=15,
        )
        a1, p1 = write_projection(**kwargs)
        a2, p2 = write_projection(**kwargs)
        assert a1.projection_sha256 == a2.projection_sha256
        assert p1 == p2

    def test_conflict_different_bytes(
        self,
        projection_root: Path,
        sample_rows: list[dict],
        schema_definition: ProjectionSchemaDefinition,
        projection_artifact_repo: ProjectionArtifactRepository,
    ) -> None:
        """Different bytes for same projection_id conflict at catalog level."""
        a1, _ = write_projection(
            root=projection_root,
            rows=sample_rows,
            schema_definition=schema_definition,
            projection_id="proj-conflict",
            source_blob_sha256=["a" * 64],
            acquisition_ids=["acq-a"],
            provider="kraken",
            venue="futures",
            sensor_family="market_data",
            native_instrument="BTC-USDT",
            native_granularity="1m",
            parser_version="1.0.0",
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            logical_year=2026,
            logical_month=1,
            logical_day=15,
        )
        projection_artifact_repo.commit(a1)

        different_rows = [{"price": 999.0, "qty": 999, "symbol": "DIFFERENT"}]
        a2, _ = write_projection(
            root=projection_root,
            rows=different_rows,
            schema_definition=schema_definition,
            projection_id="proj-conflict",
            source_blob_sha256=["b" * 64],
            acquisition_ids=["acq-b"],
            provider="kraken",
            venue="futures",
            sensor_family="market_data",
            native_instrument="BTC-USDT",
            native_granularity="1m",
            parser_version="1.0.0",
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            logical_year=2026,
            logical_month=1,
            logical_day=15,
        )
        # Catalog-level conflict: same projection_id, different SHA
        assert a2.projection_sha256 != a1.projection_sha256
        with pytest.raises(ProjectionIdentityConflict):
            projection_artifact_repo.commit(a2)


# ---------------------------------------------------------------------------
# Schema mismatch
# ---------------------------------------------------------------------------


class TestSchemaMismatch:
    def test_type_mismatch_rejected(
        self,
        projection_root: Path,
        schema_definition: ProjectionSchemaDefinition,
    ) -> None:
        """int value where float expected."""
        rows = [{"price": "not_a_number", "qty": 1, "symbol": "BTC"}]
        with pytest.raises((ProjectionSchemaMismatch, pa.ArrowInvalid)):
            write_projection(
                root=projection_root,
                rows=rows,
                schema_definition=schema_definition,
                projection_id="proj-mismatch",
                source_blob_sha256=["a" * 64],
                acquisition_ids=["acq-m"],
                provider="kraken",
                venue="futures",
                sensor_family="market_data",
                native_instrument="BTC-USDT",
                native_granularity="1m",
                parser_version="1.0.0",
                partition_key="kraken/futures/BTC-USDT/2026-01-15",
                logical_year=2026,
                logical_month=1,
                logical_day=15,
            )


# ---------------------------------------------------------------------------
# Null / type preservation
# ---------------------------------------------------------------------------


class TestTypePreservation:
    def test_null_preserved(
        self,
        projection_root: Path,
        schema_definition: ProjectionSchemaDefinition,
    ) -> None:
        rows = [{"price": 1.0, "qty": None, "symbol": "BTC"}]
        artifact, path = write_projection(
            root=projection_root,
            rows=rows,
            schema_definition=schema_definition,
            projection_id="proj-null",
            source_blob_sha256=["a" * 64],
            acquisition_ids=["acq-null"],
            provider="kraken",
            venue="futures",
            sensor_family="market_data",
            native_instrument="BTC-USDT",
            native_granularity="1m",
            parser_version="1.0.0",
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            logical_year=2026,
            logical_month=1,
            logical_day=15,
        )
        table = pq.read_table(str(path))
        assert table.column("qty")[0].as_py() is None

    def test_provider_native_round_trip(
        self,
        projection_root: Path,
        schema_definition: ProjectionSchemaDefinition,
    ) -> None:
        """Provider-native values preserved exactly."""
        rows = [
            {"price": 100.5, "qty": 10, "symbol": "BTC-USDT"},
            {"price": 200.0, "qty": -5, "symbol": "ETH-USDT"},
            {"price": 0.001, "qty": 999999, "symbol": "SOL-USDT"},
        ]
        artifact, path = write_projection(
            root=projection_root,
            rows=rows,
            schema_definition=schema_definition,
            projection_id="proj-roundtrip",
            source_blob_sha256=["a" * 64],
            acquisition_ids=["acq-rt"],
            provider="kraken",
            venue="futures",
            sensor_family="market_data",
            native_instrument="BTC-USDT",
            native_granularity="1m",
            parser_version="1.0.0",
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            logical_year=2026,
            logical_month=1,
            logical_day=15,
        )
        table = pq.read_table(str(path))
        assert table.column("price")[0].as_py() == 100.5
        assert table.column("qty")[1].as_py() == -5
        assert table.column("symbol")[2].as_py() == "SOL-USDT"


# ---------------------------------------------------------------------------
# Reserved column
# ---------------------------------------------------------------------------


class TestReservedColumn:
    def test_reserved_column_rejected(self, projection_root: Path) -> None:
        """Provider-native schema with _t0_ field is rejected at definition time."""
        bad_schema = pa.schema(
            [
                pa.field("_t0_provider", pa.string(), nullable=False),
                pa.field("price", pa.float64(), nullable=False),
            ]
        )
        with pytest.raises(ReservedProjectionColumn, match="reserved"):
            ProjectionSchemaDefinition(
                projection_schema_id="test.reserved",
                projection_schema_version="1.0.0",
                provider_native_schema=bad_schema,
            )


# ---------------------------------------------------------------------------
# Multi-blob projection
# ---------------------------------------------------------------------------


class TestMultiBlob:
    def test_multi_blob_projection(
        self,
        projection_root: Path,
        schema_definition: ProjectionSchemaDefinition,
    ) -> None:
        """Multi-source: row-level source attribution left NULL."""
        rows = [
            {"price": 1.0, "qty": 1, "symbol": "BTC"},
            {"price": 2.0, "qty": 2, "symbol": "ETH"},
        ]
        artifact, path = write_projection(
            root=projection_root,
            rows=rows,
            schema_definition=schema_definition,
            projection_id="proj-multi",
            source_blob_sha256=["a" * 64, "b" * 64],
            acquisition_ids=["acq-a", "acq-b"],
            provider="kraken",
            venue="futures",
            sensor_family="market_data",
            native_instrument="BTC-USDT",
            native_granularity="1m",
            parser_version="1.0.0",
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            logical_year=2026,
            logical_month=1,
            logical_day=15,
        )
        assert artifact.row_count == 2
        table = pq.read_table(str(path))
        # Multi-source: per-row source attribution is NULL
        assert table.column("_t0_source_blob_sha256")[0].as_py() is None
        assert table.column("_t0_acquisition_id")[0].as_py() is None


# ---------------------------------------------------------------------------
# ProjectionArtifactRepository
# ---------------------------------------------------------------------------


class TestProjectionArtifactRepository:
    def test_commit_and_get(
        self, projection_artifact_repo: ProjectionArtifactRepository
    ) -> None:
        from crypto_sensor_fabric.storage.models import RawProjectionArtifact

        artifact = RawProjectionArtifact(
            projection_id="proj-001",
            source_blob_sha256=["a" * 64],
            projection_schema_id="test.schema",
            projection_schema_version="1.0.0",
            parser_version="1.0.0",
            row_count=10,
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            projection_uri="projections/provider=kraken/venue=futures/part-00000-abc.parquet",
            projection_sha256="d" * 64,
        )
        committed = projection_artifact_repo.commit(artifact)
        assert committed.projection_id == "proj-001"

        retrieved = projection_artifact_repo.get("proj-001")
        assert retrieved is not None
        assert retrieved.projection_sha256 == "d" * 64

    def test_idempotent_commit(
        self, projection_artifact_repo: ProjectionArtifactRepository
    ) -> None:
        from crypto_sensor_fabric.storage.models import RawProjectionArtifact

        artifact = RawProjectionArtifact(
            projection_id="proj-idem",
            source_blob_sha256=["a" * 64],
            projection_schema_id="test.schema",
            projection_schema_version="1.0.0",
            parser_version="1.0.0",
            row_count=10,
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            projection_uri="projections/part-00000-abc.parquet",
            projection_sha256="d" * 64,
        )
        r1 = projection_artifact_repo.commit(artifact)
        r2 = projection_artifact_repo.commit(artifact)
        assert r1.projection_sha256 == r2.projection_sha256

    def test_conflict_different_bytes(
        self, projection_artifact_repo: ProjectionArtifactRepository
    ) -> None:
        from crypto_sensor_fabric.storage.models import RawProjectionArtifact

        a1 = RawProjectionArtifact(
            projection_id="proj-conflict",
            source_blob_sha256=["a" * 64],
            projection_schema_id="test.schema",
            projection_schema_version="1.0.0",
            parser_version="1.0.0",
            row_count=10,
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            projection_uri="projections/part-00000-abc.parquet",
            projection_sha256="d" * 64,
        )
        projection_artifact_repo.commit(a1)

        a2 = RawProjectionArtifact(
            projection_id="proj-conflict",
            source_blob_sha256=["b" * 64],  # different
            projection_schema_id="test.schema",
            projection_schema_version="1.0.0",
            parser_version="1.0.0",
            row_count=10,
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            projection_uri="projections/part-00000-def.parquet",
            projection_sha256="e" * 64,  # different
        )
        with pytest.raises(ProjectionIdentityConflict):
            projection_artifact_repo.commit(a2)

    def test_list_ids(
        self, projection_artifact_repo: ProjectionArtifactRepository
    ) -> None:
        from crypto_sensor_fabric.storage.models import RawProjectionArtifact

        for pid in ["proj-c", "proj-a", "proj-b"]:
            projection_artifact_repo.commit(
                RawProjectionArtifact(
                    projection_id=pid,
                    source_blob_sha256=["a" * 64],
                    projection_schema_id="test.schema",
                    projection_schema_version="1.0.0",
                    parser_version="1.0.0",
                    row_count=1,
                    partition_key="key",
                    projection_uri="uri",
                    projection_sha256="d" * 64,
                )
            )
        ids = projection_artifact_repo.list_ids()
        assert ids == ["proj-a", "proj-b", "proj-c"]

    def test_persist_and_reload(self, tmp_path: Path) -> None:
        from crypto_sensor_fabric.storage.models import RawProjectionArtifact

        catalog_root = tmp_path / "catalogs" / "manifests" / "projections"
        repo1 = ProjectionArtifactRepository(catalog_root)
        artifact = RawProjectionArtifact(
            projection_id="proj-reload",
            source_blob_sha256=["a" * 64],
            projection_schema_id="test.schema",
            projection_schema_version="1.0.0",
            parser_version="1.0.0",
            row_count=5,
            partition_key="key",
            projection_uri="uri",
            projection_sha256="d" * 64,
        )
        repo1.commit(artifact)

        # Reload from disk
        repo2 = ProjectionArtifactRepository(catalog_root)
        retrieved = repo2.get("proj-reload")
        assert retrieved is not None
        assert retrieved.row_count == 5
