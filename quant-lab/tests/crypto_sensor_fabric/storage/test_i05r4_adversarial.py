"""SENSOR-B4-I05R4D — partial-chain crash/retry + verifier adversarial proofs.

Covers (I05R4 §7/§8/§26-§28/§36):

- the exact context-before-lineage crash state (physical + artifact +
  context durable, NO lineage) is NOT resolver-valid — partial science
  never masquerades as a complete chain;
- a real-service retry at T2 completes the missing lineage, reusing the
  T1 context, without deleting any durable intermediate truth;
- a verifier substitute without verify_physical fails at lineage-repository
  CONSTRUCTION (§7), not at commit;
- verify_physical failure propagates through an idempotent lineage
  re-commit — no cached success (§8);
- the full recovered chain survives a complete restart (§28/§36.18);
- lineage commit always invokes verify_physical (spy, §36.2).
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
from crypto_sensor_fabric.storage.projection_lineage import (
    LineageConfigurationError,
    ProjectionLineageRepository,
)
from crypto_sensor_fabric.storage.projection_resolver import (
    ProjectionLineageResolver,
)
from crypto_sensor_fabric.storage.projection_schema import (
    ProjectionSchemaDefinition,
    ProjectionSchemaRegistry,
)
from crypto_sensor_fabric.storage.projections import (
    ProjectionArtifactRepository,
    ProjectionCatalogRecord,
    ProjectionContextRepository,
    ProjectionCorruption,
    ProjectionIdentityConflict,
    T0BProjectionService,
    write_projection,
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


def _lineage(lmid: str, pid: str, sha: str, acq_id: str):
    from crypto_sensor_fabric.storage.models import ProjectionLineage

    return ProjectionLineage(
        lineage_manifest_id=lmid,
        projection_id=pid,
        source_blob_sha256=sha,
        source_acquisition_id=acq_id,
        source_order=0,
    )


class CrashChain:
    """Sealed stack able to stop exactly after the context commit."""

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
        self.lineage = ProjectionLineageRepository(
            self.root / "catalogs" / "manifests" / "projection_lineage",
            blob_store=self.store,
            blob_metadata_repository=self.blob_repo,
            acquisition_repository=self.acq_repo,
            artifact_repository=self.artifacts,
            context_repository=self.contexts,
        )
        self.resolver = ProjectionLineageResolver(
            root=self.root,
            artifacts=self.artifacts,
            contexts=self.contexts,
            lineage=self.lineage,
            schemas=self.schemas,
        )

    def definition(self) -> ProjectionSchemaDefinition:
        import pyarrow as pa

        return ProjectionSchemaDefinition(
            projection_schema_id="r4d.market.projection",
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

    def commit_through_context(self, projection_id: str, sha: str, acq_id: str):
        """Steps 1-8 of the frozen service order, then STOP (crash point)."""

        d = self.definition()
        try:
            self.schemas.resolve(d.schema_key)
        except Exception:
            self.schemas.register(d)
        artifact, final_path = write_projection(
            root=self.root,
            rows=[{"price": 1.0, "qty": 1, "symbol": "BTC-USDT"}],
            schema_definition=d,
            schema_registry=self.schemas,
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
        )
        self.artifacts.commit(artifact)
        context = ProjectionCatalogRecord(
            projection_id=projection_id,
            provider="kraken",
            venue="futures",
            sensor_family="MECHANICAL_TRADE",
            native_instrument="BTC-USDT",
            source_granularity="1m",
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            logical_date_start=datetime(2026, 1, 15, tzinfo=UTC),
            logical_date_end=datetime(2026, 1, 15, 23, 59, 59, tzinfo=UTC),
            projection_schema_id=d.projection_schema_id,
            projection_schema_version=d.projection_schema_version,
            schema_key=d.schema_key,
            schema_fingerprint=d.schema_fingerprint,
            parser_version="1.0.0",
            projection_uri=artifact.projection_uri,
            projection_sha256=artifact.projection_sha256,
            row_count=artifact.row_count,
            min_provider_time=None,
            max_provider_time=None,
            lineage_manifest_id=f"lm-{projection_id}",
            quality_flags=[],
            created_at=self.now,
        )
        self.contexts.commit(context)
        return artifact, final_path

    def new_service(self) -> T0BProjectionService:
        return T0BProjectionService(
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


class TestPartialChainCrashState:
    def test_context_without_lineage_not_resolver_visible(
        self, tmp_path
    ) -> None:
        """§26: the crash state must fail production projection-ref checks."""
        chain = CrashChain(tmp_path)
        sha = chain.seed(b'{"rows": [1]}', "acq-1")
        artifact, _ = chain.commit_through_context("proj-partial", sha, "acq-1")

        assert chain.contexts.has("proj-partial")
        assert not chain.lineage.has("lm-proj-partial")
        # The resolver (used for manifest projection-ref validation) must
        # fail closed — the partial chain is not complete science.
        from crypto_sensor_fabric.storage.models import PartitionManifest

        manifest = PartitionManifest(
            partition_manifest_id="pm-partial",
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            provider="kraken",
            venue="futures",
            sensor_family="MECHANICAL_TRADE",
            native_instrument="BTC-USDT",
            source_granularity="1m",
            logical_date_start=datetime(2026, 1, 15, tzinfo=UTC),
            logical_date_end=datetime(2026, 1, 15, 23, 59, 59, tzinfo=UTC),
            blob_refs=[sha],
            projection_refs=["proj-partial"],
            created_at=T1,
        )
        with pytest.raises(Exception) as excinfo:
            chain.resolver.validate_projection_ref("proj-partial", manifest)
        # Typed lineage-absence, never a silent pass.
        assert "lineage" in str(excinfo.value).lower()

    def test_partial_retry_completes_chain_and_preserves_t1(
        self, tmp_path
    ) -> None:
        """§27/§15: retry at T2 finishes the chain; context stays T1;
        no intermediate truth is deleted (§28)."""
        chain = CrashChain(tmp_path)
        sha = chain.seed(b'{"rows": [2]}', "acq-2")
        artifact_before, path_before = chain.commit_through_context(
            "proj-recover", sha, "acq-2"
        )
        # Intermediate truth that MUST survive the retry.
        ctx_before = chain.contexts.get("proj-recover")
        assert ctx_before is not None and ctx_before.created_at == T1

        # CRASH recovered: wall clock moves, fresh service instance.
        chain.now = T2
        service = chain.new_service()
        artifact_after, path_after = service.commit_projection(
            rows=[{"price": 1.0, "qty": 1, "symbol": "BTC-USDT"}],
            schema_definition=chain.definition(),
            projection_id="proj-recover",
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
            lineage_manifest_id="lm-proj-recover",
        )
        # Same physical bytes; nothing deleted or overwritten (§28).
        assert artifact_after.projection_sha256 == artifact_before.projection_sha256
        assert path_after == path_before and path_after.exists()
        assert chain.contexts.get("proj-recover").created_at == T1  # type: ignore[union-attr]
        # The chain is now lineage-complete.
        assert chain.lineage.has("lm-proj-recover")

    def test_recovered_chain_survives_full_restart(self, tmp_path) -> None:
        """§36.18: discard all objects, rebuild from disk, resolver passes."""
        chain = CrashChain(tmp_path)
        sha = chain.seed(b'{"rows": [3]}', "acq-3")
        chain.commit_through_context("proj-restart", sha, "acq-3")
        chain.now = T2
        chain.new_service().commit_projection(
            rows=[{"price": 1.0, "qty": 1, "symbol": "BTC-USDT"}],
            schema_definition=chain.definition(),
            projection_id="proj-restart",
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
            lineage_manifest_id="lm-proj-restart",
        )

        # Full restart: fresh resolver over fresh repositories.
        chain.artifacts = ProjectionArtifactRepository(
            chain.root / "catalogs" / "manifests" / "projections",
            projection_root=chain.root,
            schema_registry=chain.schemas,
        )
        chain.contexts = ProjectionContextRepository(
            chain.root / "catalogs" / "manifests" / "projection_context"
        )
        chain.lineage = ProjectionLineageRepository(
            chain.root / "catalogs" / "manifests" / "projection_lineage",
            blob_store=chain.store,
            blob_metadata_repository=chain.blob_repo,
            acquisition_repository=chain.acq_repo,
            artifact_repository=chain.artifacts,
            context_repository=chain.contexts,
        )
        resolver = ProjectionLineageResolver(
            root=chain.root,
            artifacts=chain.artifacts,
            contexts=chain.contexts,
            lineage=chain.lineage,
            schemas=chain.schemas,
        )
        from crypto_sensor_fabric.storage.models import PartitionManifest

        manifest = PartitionManifest(
            partition_manifest_id="pm-restart",
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            provider="kraken",
            venue="futures",
            sensor_family="MECHANICAL_TRADE",
            native_instrument="BTC-USDT",
            source_granularity="1m",
            logical_date_start=datetime(2026, 1, 15, tzinfo=UTC),
            logical_date_end=datetime(2026, 1, 15, 23, 59, 59, tzinfo=UTC),
            blob_refs=[sha],
            projection_refs=["proj-restart"],
            created_at=T2,
        )
        resolver.validate_projection_ref("proj-restart", manifest)


class TestVerifierAdversarial:
    def test_verifier_without_verify_physical_fails_at_construction(
        self, tmp_path
    ) -> None:
        """§7: get()-only substitute is rejected BEFORE commit, typed."""

        class GetOnlyArtifactRepo:
            def get(self, projection_id: str) -> object:
                return None

        # Sanity: the stub genuinely fails the runtime protocol check.
        from crypto_sensor_fabric.storage.projection_lineage import (
            ProjectionArtifactVerifier,
        )

        assert not isinstance(GetOnlyArtifactRepo(), ProjectionArtifactVerifier)

        with pytest.raises(LineageConfigurationError, match="verify_physical"):
            ProjectionLineageRepository(
                tmp_path / "lin",
                blob_store=object(),
                blob_metadata_repository=object(),
                acquisition_repository=object(),
                artifact_repository=GetOnlyArtifactRepo(),
                context_repository=object(),
            )

    def test_verifier_failure_propagates_no_cached_success(
        self, tmp_path
    ) -> None:
        """§8: sealed repo + corrupt T0B -> idempotent re-commit fails."""
        chain = CrashChain(tmp_path)
        sha = chain.seed(b'{"rows": [4]}', "acq-4")
        chain.commit_through_context("proj-verif", sha, "acq-4")
        entries = chain.lineage.commit(
            "lm-proj-verif", [_lineage("lm-proj-verif", "proj-verif", sha, "acq-4")]
        )
        assert len(entries) == 1
        # Corrupt the physical T0B behind the committed artifact.
        artifact = chain.artifacts.get("proj-verif")
        assert artifact is not None
        physical = chain.root / artifact.projection_uri
        physical.write_bytes(b"CORRUPTED")
        # Idempotent re-commit: verifier runs unconditionally, failure
        # propagates — the cached manifest is NOT returned as success.
        with pytest.raises(ProjectionCorruption):
            chain.lineage.commit(
                "lm-proj-verif",
                [_lineage("lm-proj-verif", "proj-verif", sha, "acq-4")],
            )

    def test_lineage_commit_always_invokes_verifier(self, tmp_path) -> None:
        """§36.2: a spy proves verify_physical runs on EVERY commit path."""
        chain = CrashChain(tmp_path)
        sha = chain.seed(b'{"rows": [5]}', "acq-5")
        chain.commit_through_context("proj-spy", sha, "acq-5")

        calls: list[str] = []
        original = chain.artifacts.verify_physical
        chain.artifacts.verify_physical = lambda pid: (calls.append(pid), original(pid))[  # type: ignore[method-assign]
            1
        ]

        entries = [
            _lineage("lm-proj-spy", "proj-spy", sha, "acq-5"),
        ]
        chain.lineage.commit("lm-proj-spy", entries)  # first commit
        chain.lineage.commit("lm-proj-spy", entries)  # idempotent commit
        assert calls == ["proj-spy", "proj-spy"]


class TestServiceConflictRegressions:
    def test_changed_rows_under_same_projection_id_conflicts(
        self, tmp_path
    ) -> None:
        chain = CrashChain(tmp_path)
        sha = chain.seed(b'{"rows": [6]}', "acq-6")
        d = chain.definition()
        try:
            chain.schemas.resolve(d.schema_key)
        except Exception:
            chain.schemas.register(d)
        service = chain.new_service()
        service.commit_projection(
            rows=[{"price": 1.0, "qty": 1, "symbol": "BTC-USDT"}],
            schema_definition=chain.definition(),
            projection_id="proj-conflict",
            source_blob_sha256=[sha],
            acquisition_ids=["acq-6"],
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
            lineage_manifest_id="lm-proj-conflict",
        )
        with pytest.raises(ProjectionIdentityConflict):
            service.commit_projection(
                rows=[{"price": 9.0, "qty": 1, "symbol": "BTC-USDT"}],
                schema_definition=chain.definition(),
                projection_id="proj-conflict",
                source_blob_sha256=[sha],
                acquisition_ids=["acq-6"],
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
                lineage_manifest_id="lm-proj-conflict",
            )
