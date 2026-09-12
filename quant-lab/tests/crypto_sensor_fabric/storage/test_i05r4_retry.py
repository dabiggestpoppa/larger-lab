"""SENSOR-B4-I05R4C — context idempotence + real-service retry tests.

Covers (I05R4 §19-§30):

- ``created_at`` is first-seen operational metadata: the same scientific
  ProjectionCatalogRecord committed at T1 and T2 returns the T1 record
  with its original ``created_at`` preserved (no rewrite, no conflict);
- any scientific/structural field difference still conflicts;
- the REAL T0BProjectionService retried across clock movement (T1 → T2)
  completes idempotently — physical re-verification, T1 context reuse,
  lineage idempotent revalidation, no duplicate scientific identity;
- alternate lineage_manifest_id retry still fails (I05R3 binding stays
  authoritative);
- scientifically different projection bytes under the same projection_id
  still conflict.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
from crypto_sensor_fabric.storage.catalog import (
    AcquisitionRepository,
    BlobMetadataRepository,
)
from crypto_sensor_fabric.storage.enums import StorageEncoding
from crypto_sensor_fabric.storage.models import AcquisitionRecord
from crypto_sensor_fabric.storage.projection_schema import (
    ProjectionSchemaDefinition,
    ProjectionSchemaRegistry,
)
from crypto_sensor_fabric.storage.projections import (
    ProjectionArtifactRepository,
    ProjectionCatalogRecord,
    ProjectionContextRepository,
    ProjectionIdentityConflict,
    T0BProjectionService,
)

T1 = datetime(2026, 9, 12, 12, 0, 0, tzinfo=UTC)
T2 = datetime(2026, 9, 12, 18, 30, 0, tzinfo=UTC)
MEDIA = "application/json"


def _acq(acq_id: str, sha: str) -> AcquisitionRecord:
    return AcquisitionRecord(
        acquisition_id=acq_id,
        provider_id="kraken",
        venue="futures",
        sensor_family="MECHANICAL_TRADE",
        request_fingerprint="fp",
        adapter_version="1.0",
        requested_start=datetime(2026, 1, 1, tzinfo=UTC),
        requested_end=datetime(2026, 1, 2, tzinfo=UTC),
        native_instrument="BTC-USDT",
        request_started_at=datetime(2026, 1, 1, tzinfo=UTC),
        response_observed_at=datetime(2026, 1, 1, tzinfo=UTC),
        ingested_at=datetime(2026, 1, 1, tzinfo=UTC),
        source_locator="file:///test",
        blob_sha256=sha,
        provider_checksum_algorithm=None,
        provider_checksum_value=None,
        provider_checksum_verified=None,
        failure_ref=None,
        http_status_or_source_status=None,
    )


class RetryChain:
    """Real sealed stack whose clock is swappable between attempts."""

    def __init__(self, tmp_path: Path) -> None:
        self.root = tmp_path / "t0b"
        self.root.mkdir(parents=True)
        self.t0a = tmp_path / "t0a"
        self.t0a.mkdir(parents=True)
        self.now = T1
        self.store = LocalBlobStore(str(self.t0a), clock=lambda: self.now)
        self.blob_repo = BlobMetadataRepository(
            self.t0a, blob_store=self.store, clock=lambda: self.now
        )
        self.acq_repo = AcquisitionRepository(
            self.t0a,
            blob_store=self.store,
            blob_metadata_repository=self.blob_repo,
            clock=lambda: self.now,
        )
        self.reopen()

    def reopen(self) -> "RetryChain":
        """Reinstantiate every T0B repository from durable disk state."""
        self.schemas = ProjectionSchemaRegistry(
            self.root / "catalogs" / "projection_schemas"
        )
        self.artifacts = ProjectionArtifactRepository(
            self.root / "catalogs" / "manifests" / "projections",
            projection_root=self.root,
            schema_registry=self.schemas,
        )
        self.contexts = ProjectionContextRepository(
            self.root / "catalogs" / "manifests" / "projection_context"
        )
        from crypto_sensor_fabric.storage.projection_lineage import (
            ProjectionLineageRepository,
        )

        self.lineage = ProjectionLineageRepository(
            self.root / "catalogs" / "manifests" / "projection_lineage",
            blob_store=self.store,
            blob_metadata_repository=self.blob_repo,
            acquisition_repository=self.acq_repo,
            artifact_repository=self.artifacts,
            context_repository=self.contexts,
        )
        self.service = T0BProjectionService(
            root=self.root,
            blob_store=self.store,
            blob_metadata_repository=self.blob_repo,
            acquisition_repository=self.acq_repo,
            schema_registry=self.schemas,
            artifact_repository=self.artifacts,
            context_repository=self.contexts,
            lineage_repository=self.lineage,
            clock=lambda: self.now,
        )
        return self

    def definition(self) -> ProjectionSchemaDefinition:
        import pyarrow as pa

        return ProjectionSchemaDefinition(
            projection_schema_id="r4c.market.projection",
            projection_schema_version="1.0.0",
            provider_native_schema=pa.schema(
                [
                    pa.field("price", pa.float64(), nullable=False),
                    pa.field("qty", pa.int64(), nullable=True),
                    pa.field("symbol", pa.string(), nullable=False),
                ]
            ),
        )

    def seed(self, data: bytes, acq_id: str) -> str:
        put = self.store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        )
        self.blob_repo.append_metadata(put.blob)
        self.acq_repo.append_acquisition(_acq(acq_id, put.blob.blob_sha256))
        return put.blob.blob_sha256


def _commit_via_service(chain: RetryChain, projection_id: str, sha: str, acq_id: str):
    d = chain.definition()
    try:
        chain.schemas.resolve(d.schema_key)
    except Exception:
        chain.schemas.register(d)
    return chain.service.commit_projection(
        rows=[{"price": 1.0, "qty": 1, "symbol": "BTC-USDT"}],
        schema_definition=d,
        projection_id=projection_id,
        source_blob_sha256=[sha],
        acquisition_ids=[acq_id],
        provider="kraken",
        venue="futures",
        sensor_family="MECHANICAL_TRADE",
        native_instrument="BTC-USDT",
        native_granularity="1m",
        parser_version="1.0.0",
        partition_key="kraken/futures/BTC-USDT/2026-01-15",
        logical_year=2026,
        logical_month=1,
        logical_day=15,
        lineage_manifest_id=f"lm-{projection_id}",
    )


def _context(
    projection_id: str, created_at: datetime, **overrides: object
) -> ProjectionCatalogRecord:
    base: dict[str, object] = dict(
        projection_id=projection_id,
        provider="kraken",
        venue="futures",
        sensor_family="MECHANICAL_TRADE",
        native_instrument="BTC-USDT",
        source_granularity="1m",
        partition_key="kraken/futures/BTC-USDT/2026-01-15",
        logical_date_start=datetime(2026, 1, 15, tzinfo=UTC),
        logical_date_end=datetime(2026, 1, 15, 23, 59, 59, tzinfo=UTC),
        projection_schema_id="schema.x",
        projection_schema_version="1.0.0",
        schema_key="k" * 64,
        schema_fingerprint="f" * 64,
        parser_version="1.0.0",
        projection_uri="projections/part-0.parquet",
        projection_sha256="a" * 64,
        row_count=1,
        min_provider_time=None,
        max_provider_time=None,
        lineage_manifest_id="lm-time",
        quality_flags=[],
        created_at=created_at,
    )
    base.update(overrides)
    return ProjectionCatalogRecord(**base)  # type: ignore[arg-type]


class TestContextCreatedAtIdempotence:
    def test_same_scientific_context_t1_t2_preserves_first(self, tmp_path) -> None:
        """§23: C1@T1 commit, C2@T2 identical-scientific → returns C1."""
        repo = ProjectionContextRepository(tmp_path / "ctx")
        first = repo.commit(_context("proj-x", T1))
        second = repo.commit(_context("proj-x", T2))
        assert second.created_at == T1
        assert second.to_dict() == first.to_dict()
        # The committed fragment retains the FIRST created_at.
        reloaded = ProjectionContextRepository(tmp_path / "ctx")
        assert reloaded.get("proj-x").created_at == T1  # type: ignore[union-attr]

    def test_scientific_difference_still_conflicts(self, tmp_path) -> None:
        """§24: created_at is the ONLY excluded field."""
        repo = ProjectionContextRepository(tmp_path / "ctx")
        repo.commit(_context("proj-x", T1))
        for changed in (
            {"provider": "okx"},
            {"partition_key": "kraken/futures/BTC-USDT/2026-01-16"},
            {"projection_schema_version": "1.1.0"},
            {"parser_version": "1.0.1"},
            {"projection_sha256": "b" * 64},
            {"lineage_manifest_id": "lm-other"},
            {"row_count": 2},
            {"quality_flags": ["flag"]},
        ):
            with pytest.raises(ProjectionIdentityConflict):
                repo.commit(_context("proj-x", T2, **changed))  # type: ignore[arg-type]


class TestServiceRetryAcrossClock:
    def test_real_service_same_projection_t1_then_t2_succeeds(
        self, tmp_path
    ) -> None:
        """§25: real sealed service, same scientific inputs at T1 and T2."""
        chain = RetryChain(tmp_path)
        sha = chain.seed(b'{"rows": [1]}', "acq-1")
        a1, _p1 = _commit_via_service(chain, "proj-retry", sha, "acq-1")

        # Move the wall clock and RESTART every repository from disk.
        chain.now = T2
        chain.reopen()
        a2, _p2 = _commit_via_service(chain, "proj-retry", sha, "acq-1")

        assert a2.projection_sha256 == a1.projection_sha256
        # Context reuses the FIRST committed T1 record.
        assert chain.contexts.get("proj-retry").created_at == T1  # type: ignore[union-attr]
        # No duplicate scientific identity in either catalog.
        assert chain.artifacts.list_ids() == ["proj-retry"]
        assert chain.contexts.list_ids() == ["proj-retry"]

    def test_alternate_lmid_retry_rejected(self, tmp_path) -> None:
        """§29: same projection_id, different lineage_manifest_id → FAIL."""
        chain = RetryChain(tmp_path)
        sha = chain.seed(b'{"rows": [2]}', "acq-2")
        _commit_via_service(chain, "proj-alt", sha, "acq-2")

        chain.now = T2
        chain.reopen()
        d = chain.definition()
        with pytest.raises(Exception) as excinfo:
            chain.service.commit_projection(
                rows=[{"price": 1.0, "qty": 1, "symbol": "BTC-USDT"}],
                schema_definition=d,
                projection_id="proj-alt",
                source_blob_sha256=[sha],
                acquisition_ids=["acq-2"],
                provider="kraken",
                venue="futures",
                sensor_family="MECHANICAL_TRADE",
                native_instrument="BTC-USDT",
                native_granularity="1m",
                parser_version="1.0.0",
                partition_key="kraken/futures/BTC-USDT/2026-01-15",
                logical_year=2026,
                logical_month=1,
                logical_day=15,
                lineage_manifest_id="lm-something-else",
            )
        assert type(excinfo.value).__name__ in {
            "LineageContextBindingConflict",
            "ProjectionIdentityConflict",
            "ProjectionWriteError",
        }

    def test_changed_projection_bytes_rejected(self, tmp_path) -> None:
        """§30: same projection_id, scientifically different rows → conflict."""
        chain = RetryChain(tmp_path)
        sha = chain.seed(b'{"rows": [3]}', "acq-3")
        a1, _ = _commit_via_service(chain, "proj-chg", sha, "acq-3")

        chain.now = T2
        chain.reopen()
        d = chain.definition()
        with pytest.raises(ProjectionIdentityConflict):
            chain.service.commit_projection(
                rows=[{"price": 2.0, "qty": 1, "symbol": "BTC-USDT"}],
                schema_definition=d,
                projection_id="proj-chg",
                source_blob_sha256=[sha],
                acquisition_ids=["acq-3"],
                provider="kraken",
                venue="futures",
                sensor_family="MECHANICAL_TRADE",
                native_instrument="BTC-USDT",
                native_granularity="1m",
                parser_version="1.0.0",
                partition_key="kraken/futures/BTC-USDT/2026-01-15",
                logical_year=2026,
                logical_month=1,
                logical_day=15,
                lineage_manifest_id="lm-proj-chg",
            )
        # The original artifact truth survives untouched.
        assert chain.artifacts.get("proj-chg").projection_sha256 == (  # type: ignore[union-attr]
            a1.projection_sha256
        )
