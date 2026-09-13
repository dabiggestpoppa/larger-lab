"""SENSOR-B4-I05R1C — real end-to-end projection chain tests.

The acceptance path uses ONLY real objects (I05R1 §17 — no stub may certify
it): LocalBlobStore, BlobMetadataRepository, AcquisitionRepository,
ProjectionSchemaRegistry, write_projection (via T0BProjectionService),
ProjectionArtifactRepository, ProjectionContextRepository,
ProjectionLineageRepository, the production ProjectionLineageResolver, and
PartitionManifestRepository.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pytest

from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
from crypto_sensor_fabric.storage.catalog import (
    AcquisitionRepository,
    BlobMetadataRepository,
)
from crypto_sensor_fabric.storage.enums import StorageEncoding
from crypto_sensor_fabric.storage.manifests import (
    PartitionManifest,
    PartitionManifestRepository,
)
from crypto_sensor_fabric.storage.projection_lineage import (
    ProjectionArtifactMissing,
    ProjectionLineageRepository,
)
from crypto_sensor_fabric.storage.projection_resolver import (
    ProjectionLineageResolver,
    ProjectionPartitionMismatch,
    ProjectionSourceHidden,
)
from crypto_sensor_fabric.storage.projection_schema import (
    ProjectionSchemaDefinition,
    ProjectionSchemaRegistry,
)
from crypto_sensor_fabric.storage.projections import (
    ProjectionArtifactRepository,
    ProjectionContextRepository,
    ProjectionSourceNotUsable,
    T0BProjectionService,
)

FIXED = datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"

NATIVE_SCHEMA = pa.schema(
    [
        pa.field("price", pa.float64(), nullable=False),
        pa.field("qty", pa.int64(), nullable=True),
        pa.field("symbol", pa.string(), nullable=False),
    ]
)


class Chain:
    """Full real stack on one root."""

    # Track seeded blob bytes so a failing H3 value can be synthesized as a
    # guaranteed-wrong digest of DIFFERENT data (I04R1 canonical form holds).
    _blob_bytes: dict[str, bytes] = {}

    def __init__(self, tmp_path: Path, *, fresh_t0b: bool = True) -> None:
        import shutil

        # I05R4 §16: portable per-test T0B root derived from pytest tmp_path
        # — no global workstation path.
        self.root = tmp_path / "t0b"
        if fresh_t0b:
            if self.root.exists():
                shutil.rmtree(self.root)
            self.root.mkdir(parents=True)
        else:
            # Reopen mode: reuse the existing T0B catalogs from disk.
            self.root.mkdir(parents=True, exist_ok=True)

        # T0A root (blob store + catalog repositories share it).  Tests that
        # construct a SECOND chain on the same tmp_path reuse the T0A stack.
        self.t0a = tmp_path / "t0a"
        self.t0a.mkdir(exist_ok=True)
        self.store = LocalBlobStore(str(self.t0a))
        self.blob_repo = BlobMetadataRepository(self.t0a, blob_store=self.store)
        self.acq_repo = AcquisitionRepository(
            self.t0a, blob_store=self.store, blob_metadata_repository=self.blob_repo
        )

        # T0B catalogs under the T0 root.
        self.schemas = ProjectionSchemaRegistry(
            self.root / "catalogs" / "projection_schemas"
        )
        self.schema_definition = ProjectionSchemaDefinition(
            projection_schema_id="e2e.market.projection",
            projection_schema_version="1.0.0",
            provider_native_schema=NATIVE_SCHEMA,
        )
        self.schemas.register(self.schema_definition)

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
        self.service = T0BProjectionService(
            root=self.root,
            blob_store=self.store,
            blob_metadata_repository=self.blob_repo,
            acquisition_repository=self.acq_repo,
            schema_registry=self.schemas,
            artifact_repository=self.artifacts,
            context_repository=self.contexts,
            lineage_repository=self.lineage,
            clock=lambda: FIXED,
        )
        self.resolver = ProjectionLineageResolver(
            root=self.root,
            artifacts=self.artifacts,
            contexts=self.contexts,
            lineage=self.lineage,
            schemas=self.schemas,
        )

    # -- T0A seeding ---------------------------------------------------------

    def seed_blob(self, data: bytes) -> str:
        put = self.store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        )
        Chain._blob_bytes[put.blob.blob_sha256] = data
        self.blob_repo.append_metadata(put.blob)
        return put.blob.blob_sha256

    def seed_acquisition(
        self,
        sha: str,
        acq_id: str,
        *,
        provider: str = "kraken",
        venue: str = "futures",
        sensor: str = "MECHANICAL_TRADE",
        instrument: str = "BTC-USDT",
        granularity: str = "1m",
        failure_ref: str | None = None,
        h3: bool | None = None,
        http_status: str = "200",
    ):
        import hashlib as _hashlib

        from crypto_sensor_fabric.storage.models import AcquisitionRecord

        def data_for(sha: str) -> bytes:
            # H3=True seeds the digest of the REAL bytes (earned would be
            # recomputed by the repository); H3=False seeds a deliberately
            # WRONG digest of different bytes — canonical form, wrong value.
            payload = Chain._blob_bytes.get(sha, b"unused")
            return b"WRONG-" + payload if h3 is False else payload

        record = AcquisitionRecord(
            acquisition_id=acq_id,
            provider_id=provider,
            venue=venue,
            sensor_family=sensor,
            request_fingerprint="fp",
            adapter_version="1.0",
            requested_start=FIXED,
            requested_end=FIXED,
            native_instrument=instrument,
            request_started_at=FIXED,
            response_observed_at=FIXED,
            ingested_at=FIXED,
            http_status_or_source_status=http_status,
            source_locator="file:///test",
            blob_sha256=sha,
            provider_checksum_algorithm=(
                "SHA256" if h3 is not None else None
            ),
            provider_checksum_value=(
                _hashlib.sha256(data_for(sha)).hexdigest()
                if h3 is not None
                else None
            ),
            provider_checksum_verified=h3,
            failure_ref=failure_ref,
        )
        self.acq_repo.append_acquisition(record)
        return record

    # -- projection ----------------------------------------------------------

    def commit_projection(
        self,
        projection_id: str,
        sources: list[tuple[str, str]],
        *,
        rows: list[dict] | None = None,
        provider: str = "kraken",
        venue: str = "futures",
        sensor: str = "MECHANICAL_TRADE",
        instrument: str = "BTC-USDT",
        granularity: str = "1m",
        lmid: str | None = None,
    ):
        if rows is None:
            rows = [{"price": 1.0, "qty": 1, "symbol": "BTC-USDT"}]
        return self.service.commit_projection(
            rows=rows,
            schema_definition=self.schema_definition,
            projection_id=projection_id,
            source_blob_sha256=[s for s, _ in sources],
            acquisition_ids=[a for _, a in sources],
            provider=provider,
            venue=venue,
            sensor_family=sensor,
            native_instrument=instrument,
            native_granularity=granularity,
            parser_version="1.0.0",
            partition_key=f"{provider}/{venue}/{instrument}/2026-01-15",
            logical_year=2026,
            logical_month=1,
            logical_day=15,
            lineage_manifest_id=lmid or f"lm-{projection_id}",
        )

    # -- manifests -----------------------------------------------------------

    def manifest_repo(self) -> PartitionManifestRepository:
        return PartitionManifestRepository(
            self.t0a,
            blob_store=self.store,
            blob_metadata_repository=self.blob_repo,
            acquisition_repository=self.acq_repo,
            projection_lineage_resolver=self.resolver,
            clock=lambda: FIXED,
        )

    def manifest(
        self,
        manifest_id: str,
        *,
        blob_refs: list[str],
        projection_refs: list[str],
        provider: str = "kraken",
        venue: str = "futures",
        instrument: str = "BTC-USDT",
        granularity: str = "1m",
    ) -> PartitionManifest:
        return PartitionManifest(
            partition_manifest_id=manifest_id,
            partition_key=f"{provider}/{venue}/{instrument}/2026-01-15",
            provider=provider,
            venue=venue,
            sensor_family="MECHANICAL_TRADE",
            native_instrument=instrument,
            source_granularity=granularity,
            logical_date_start=datetime(2026, 1, 15, tzinfo=UTC),
            logical_date_end=datetime(2026, 1, 15, 23, 59, 59, tzinfo=UTC),
            blob_refs=blob_refs,
            projection_refs=projection_refs,
            created_at=FIXED,
        )


# I05R4 §10/§16: tests own no global T0B state; every Chain is rooted in
# its own pytest tmp_path, so no teardown of a workstation path is needed.
# ---------------------------------------------------------------------------
# Real end-to-end chains
# ---------------------------------------------------------------------------


class TestEndToEnd:
    def test_single_source_real_chain(self, tmp_path: Path) -> None:
        chain = Chain(tmp_path)
        sha = chain.seed_blob(b'{"k": "v1"}')
        chain.seed_acquisition(sha, "acq-1")
        artifact, path = chain.commit_projection("proj-1", [(sha, "acq-1")])
        assert path.exists()
        assert artifact.row_count == 1

        # Production resolver validates against a real manifest.
        repo = chain.manifest_repo()
        manifest = chain.manifest(
            "pm-1", blob_refs=[sha], projection_refs=["proj-1"]
        )
        repo._validate_referential_integrity(manifest)

    def test_multi_source_real_chain(self, tmp_path: Path) -> None:
        chain = Chain(tmp_path)
        sha_a = chain.seed_blob(b'{"k": "a"}')
        sha_b = chain.seed_blob(b'{"k": "b"}')
        chain.seed_acquisition(sha_a, "acq-a")
        chain.seed_acquisition(sha_b, "acq-b")
        artifact, path = chain.commit_projection(
            "proj-multi", [(sha_a, "acq-a"), (sha_b, "acq-b")]
        )
        assert artifact.source_blob_sha256 == [sha_a, sha_b]

        repo = chain.manifest_repo()
        manifest = chain.manifest(
            "pm-multi",
            blob_refs=[sha_a, sha_b],
            projection_refs=["proj-multi"],
        )
        repo._validate_referential_integrity(manifest)

        # Lineage is complete and ordered at the file level.
        entries = chain.lineage.get_by_projection("proj-multi")
        assert [e.source_order for e in entries] == [0, 1]
        assert [e.source_blob_sha256 for e in entries] == [sha_a, sha_b]

    def test_wrong_provider_rejected(self, tmp_path: Path) -> None:
        chain = Chain(tmp_path)
        sha = chain.seed_blob(b'{"k": "v"}')
        # Gate acquisition over the same bytes — byte identity never
        # transfers provider provenance (I05R1 §13).
        chain.seed_acquisition(sha, "acq-gate", provider="gate", venue="gate")
        with pytest.raises(ProjectionSourceNotUsable):
            chain.commit_projection("proj-wrong", [(sha, "acq-gate")])

    def test_wrong_acquisition_blob_pair_rejected(self, tmp_path: Path) -> None:
        chain = Chain(tmp_path)
        sha_a = chain.seed_blob(b'{"k": "a"}')
        sha_b = chain.seed_blob(b'{"k": "b"}')
        chain.seed_acquisition(sha_a, "acq-a")
        chain.seed_acquisition(sha_b, "acq-b")
        # Lineage pairs blob A with acquisition B (whose blob is B).
        with pytest.raises(Exception) as excinfo:
            chain.commit_projection("proj-x", [(sha_a, "acq-b")])
        assert "references blob" in str(excinfo.value)

    def test_failed_acquisition_rejected(self, tmp_path: Path) -> None:
        chain = Chain(tmp_path)
        sha = chain.seed_blob(b'{"k": "v"}')
        chain.seed_acquisition(
            sha,
            "acq-fail",
            failure_ref="checksum_mismatch",
            h3=False,
        )
        with pytest.raises(ProjectionSourceNotUsable):
            chain.commit_projection("proj-fail", [(sha, "acq-fail")])
        # Forensic history is preserved, queryable — not deleted.
        record = chain.acq_repo.get_acquisition("acq-fail")
        assert record.failure_ref == "checksum_mismatch"

    def test_missing_physical_source_rejected(self, tmp_path: Path) -> None:
        chain = Chain(tmp_path)
        sha = chain.seed_blob(b'{"k": "v"}')
        chain.seed_acquisition(sha, "acq-1")
        # Simulate source loss AFTER durable metadata + acquisition exist:
        # a fresh chain cannot re-verify the bytes.
        # reuse the same T0A stack but drop the physical file
        from crypto_sensor_fabric.storage.paths import blob_object_key

        obj = chain.t0a / blob_object_key(sha, StorageEncoding.NONE)
        obj.unlink()
        with pytest.raises(Exception):
            chain.commit_projection("proj-orphan", [(sha, "acq-1")])  # BlobMissing

    def test_hidden_source_blob_rejected(self, tmp_path: Path) -> None:
        chain = Chain(tmp_path)
        sha_a = chain.seed_blob(b'{"k": "a"}')
        sha_b = chain.seed_blob(b'{"k": "b"}')
        chain.seed_acquisition(sha_a, "acq-a")
        chain.seed_acquisition(sha_b, "acq-b")
        chain.commit_projection(
            "proj-hidden", [(sha_a, "acq-a"), (sha_b, "acq-b")]
        )
        repo = chain.manifest_repo()
        # Manifest exposes only ONE of the two source blobs.
        manifest = chain.manifest(
            "pm-hidden",
            blob_refs=[sha_a],
            projection_refs=["proj-hidden"],
        )
        with pytest.raises(ProjectionSourceHidden):
            repo._validate_referential_integrity(manifest)

    def test_wrong_partition_rejected(self, tmp_path: Path) -> None:
        chain = Chain(tmp_path)
        sha = chain.seed_blob(b'{"k": "v"}')
        chain.seed_acquisition(sha, "acq-1")
        chain.commit_projection("proj-1", [(sha, "acq-1")])
        repo = chain.manifest_repo()
        # A manifest from another provider/partition may not attach the
        # projection just because its bytes exist.
        manifest = PartitionManifest(
            partition_manifest_id="pm-other",
            partition_key="other/provider/BTC-USDT/2026-01-15",
            provider="other",
            venue="futures",
            sensor_family="MECHANICAL_TRADE",
            native_instrument="BTC-USDT",
            logical_date_start=datetime(2026, 1, 15, tzinfo=UTC),
            logical_date_end=datetime(2026, 1, 15, 23, 59, 59, tzinfo=UTC),
            blob_refs=[sha],
            projection_refs=["proj-1"],
            created_at=FIXED,
        )
        with pytest.raises(ProjectionPartitionMismatch):
            repo._validate_referential_integrity(manifest)

    def test_dangling_projection_rejected(self, tmp_path: Path) -> None:
        chain = Chain(tmp_path)
        repo = chain.manifest_repo()
        manifest = chain.manifest(
            "pm-dangling", blob_refs=[], projection_refs=["missing-proj"]
        )
        from crypto_sensor_fabric.storage.projection_resolver import (
            ProjectionChainBroken,
        )

        with pytest.raises(ProjectionChainBroken):
            repo._validate_referential_integrity(manifest)

    def test_missing_artifact_but_lineage_rejected(self, tmp_path: Path) -> None:
        """I05R2 §11: lineage for a projection with no committed artifact
        fails AT LINEAGE COMMIT (typed), and a manifest referencing it
        still fails closed at the resolver."""
        chain = Chain(tmp_path)
        sha = chain.seed_blob(b'{"k": "v"}')
        chain.seed_acquisition(sha, "acq-1")
        from crypto_sensor_fabric.storage.models import ProjectionLineage

        # I05R2 §11: the lineage repository itself refuses orphan lineage.
        with pytest.raises(ProjectionArtifactMissing):
            chain.lineage.commit(
                "lm-orphan",
                [ProjectionLineage(
                    lineage_manifest_id="lm-orphan",
                    projection_id="proj-orphan",
                    source_blob_sha256=sha,
                    source_acquisition_id="acq-1",
                    source_order=0,
                )],
            )
        repo = chain.manifest_repo()
        manifest = chain.manifest(
            "pm-orphan", blob_refs=[sha], projection_refs=["proj-orphan"]
        )
        from crypto_sensor_fabric.storage.projection_resolver import (
            ProjectionChainBroken,
        )

        with pytest.raises(ProjectionChainBroken):
            repo._validate_referential_integrity(manifest)


# ---------------------------------------------------------------------------
# Restart proof (I05R1 §44) — real restart of the full chain
# ---------------------------------------------------------------------------


class TestRestart:
    def test_full_chain_survives_restart(self, tmp_path: Path) -> None:
        chain = Chain(tmp_path)
        sha_a = chain.seed_blob(b'{"k": "a"}')
        sha_b = chain.seed_blob(b'{"k": "b"}')
        chain.seed_acquisition(sha_a, "acq-a")
        chain.seed_acquisition(sha_b, "acq-b")
        chain.commit_projection(
            "proj-restart", [(sha_a, "acq-a"), (sha_b, "acq-b")]
        )
        repo = chain.manifest_repo()
        manifest = chain.manifest(
            "pm-restart",
            blob_refs=[sha_a, sha_b],
            projection_refs=["proj-restart"],
        )
        repo._validate_referential_integrity(manifest)

        # DISCARD all Python objects; reinstantiate every repository from
        # disk (reopen mode — T0B catalogs must NOT be wiped); validate
        # again with the REAL production resolver.
        chain2 = Chain(tmp_path, fresh_t0b=False)
        artifacts2 = chain2.artifacts
        contexts2 = chain2.contexts
        lineage2 = chain2.lineage
        schemas2 = chain2.schemas

        # The T0A metadata repos are also rebuilt from disk.
        store2 = chain2.store
        blob_repo2 = chain2.blob_repo
        acq_repo2 = chain2.acq_repo

        assert artifacts2.get("proj-restart") is not None
        assert contexts2.get("proj-restart") is not None
        assert len(lineage2.get_by_projection("proj-restart")) == 2
        assert schemas2.has(chain.schema_definition.schema_key)

        fresh_resolver = ProjectionLineageResolver(
            root=chain2.root,
            artifacts=artifacts2,
            contexts=contexts2,
            lineage=lineage2,
            schemas=schemas2,
        )
        # Note: chain2 re-seeds nothing; the blob metadata/acquisition
        # repositories above were reloaded from the same t0a root, so the
        # lineage sources still resolve durably.
        manifest2 = chain2.manifest(
            "pm-restart-2",
            blob_refs=[sha_a, sha_b],
            projection_refs=["proj-restart"],
        )
        repo2 = PartitionManifestRepository(
            chain2.t0a,
            blob_store=store2,
            blob_metadata_repository=blob_repo2,
            acquisition_repository=acq_repo2,
            projection_lineage_resolver=fresh_resolver,
            clock=lambda: FIXED,
        )
        repo2._validate_referential_integrity(manifest2)
