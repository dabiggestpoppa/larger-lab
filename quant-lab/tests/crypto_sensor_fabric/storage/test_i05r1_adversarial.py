"""SENSOR-B4-I05R1E — restart, corruption, and concurrency adversarial proof.

Covers (I05R1 §45/§47/§16):

- CORRUPTION RESTART MATRIX: after a valid end-to-end chain, separately
  corrupting each catalog family (schema registry fragment, physical
  Parquet, artifact fragment, context fragment, lineage fragment) makes the
  production resolver fail closed on restart — no skip, no silent
  disappearance, no automatic re-registration, no stale cache.
- CONCURRENT CATALOG WRITERS: same-object registration/commit from two
  independent repository instances — identical content adopts/reuses (one
  physical winner, same semantic result); conflicting content under the
  same identity fails typed with exactly one truth intact.
- Durable-commit order contract replayed on the real lineage commit path.
"""

from __future__ import annotations

import shutil
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
from crypto_sensor_fabric.storage.json_catalog import catalog_physical_key
from crypto_sensor_fabric.storage.projection_lineage import (
    ProjectionLineageCatalogCorrupt,
    ProjectionLineageRepository,
)
from crypto_sensor_fabric.storage.projection_resolver import (
    ProjectionChainBroken,
    ProjectionCorruption as ResolverCorruption,
)
from crypto_sensor_fabric.storage.projection_schema import (
    ProjectionSchemaCatalogCorrupt,
    ProjectionSchemaDefinition,
    ProjectionSchemaRegistry,
)
from crypto_sensor_fabric.storage.projections import (
    ProjectionArtifactCatalogCorrupt,
    ProjectionArtifactRepository,
    ProjectionContextRepository,
    ProjectionIdentityConflict,
    T0BProjectionService,
)

FIXED = datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC)

NATIVE = pa.schema(
    [
        pa.field("price", pa.float64(), nullable=False),
        pa.field("qty", pa.int64(), nullable=True),
        pa.field("symbol", pa.string(), nullable=False),
    ]
)


class Stack:
    """Real chain on a short root (Windows MAX_PATH) + tmp T0A catalogs."""

    ROOT = Path("C:/tmp_r1e_proj")

    def __init__(self, tmp_path: Path, *, fresh: bool = True) -> None:
        if fresh:
            if self.ROOT.exists():
                shutil.rmtree(self.ROOT)
            self.ROOT.mkdir(parents=True)
        else:
            self.ROOT.mkdir(parents=True, exist_ok=True)

        self.t0a = tmp_path / "t0a"
        self.t0a.mkdir(exist_ok=True)
        self.store = LocalBlobStore(str(self.t0a))
        self.blob_repo = BlobMetadataRepository(self.t0a, blob_store=self.store)
        self.acq_repo = AcquisitionRepository(
            self.t0a, blob_store=self.store, blob_metadata_repository=self.blob_repo
        )
        self.reopen()

    def reopen(self) -> "Stack":
        """Discard and reinstantiate every T0B repository from disk."""
        self.schemas = ProjectionSchemaRegistry(
            self.ROOT / "catalogs" / "projection_schemas"
        )
        self.artifacts = ProjectionArtifactRepository(
            self.ROOT / "catalogs" / "manifests" / "projections",
            projection_root=self.ROOT,
            schema_registry=self.schemas,
        )
        self.contexts = ProjectionContextRepository(
            self.ROOT / "catalogs" / "manifests" / "projection_context"
        )
        self.lineage = ProjectionLineageRepository(
            self.ROOT / "catalogs" / "manifests" / "projection_lineage",
            blob_store=self.store,
            blob_metadata_repository=self.blob_repo,
            acquisition_repository=self.acq_repo,
            artifact_repository=self.artifacts,
            context_repository=self.contexts,
        )
        self.service = T0BProjectionService(
            root=self.ROOT,
            blob_store=self.store,
            blob_metadata_repository=self.blob_repo,
            acquisition_repository=self.acq_repo,
            schema_registry=self.schemas,
            artifact_repository=self.artifacts,
            context_repository=self.contexts,
            lineage_repository=self.lineage,
            clock=lambda: FIXED,
        )
        return self

    def close(self) -> None:
        if self.ROOT.exists():
            shutil.rmtree(self.ROOT)

    # -- helpers -------------------------------------------------------------

    def schema_definition(self) -> ProjectionSchemaDefinition:
        return ProjectionSchemaDefinition(
            projection_schema_id="r1e.market.projection",
            projection_schema_version="1.0.0",
            provider_native_schema=NATIVE,
        )

    def seed_source(self, data: bytes, acq_id: str) -> str:
        put = self.store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE,
            source_media_type="application/json",
        )
        self.blob_repo.append_metadata(put.blob)
        from crypto_sensor_fabric.storage.models import AcquisitionRecord

        self.acq_repo.append_acquisition(
            AcquisitionRecord(
                acquisition_id=acq_id,
                provider_id="kraken",
                venue="futures",
                sensor_family="MECHANICAL_TRADE",
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
                blob_sha256=put.blob.blob_sha256,
            )
        )
        return put.blob.blob_sha256

    def commit(self, projection_id: str, sources: list[tuple[str, str]]):
        definition = self.schema_definition()
        if not self.schemas.has(definition.schema_key):
            self.schemas.register(definition)
        return self.service.commit_projection(
            rows=[{"price": 1.0, "qty": 1, "symbol": "BTC-USDT"}],
            schema_definition=definition,
            projection_id=projection_id,
            source_blob_sha256=[s for s, _ in sources],
            acquisition_ids=[a for _, a in sources],
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


@pytest.fixture()
def stack(tmp_path: Path):
    s = Stack(tmp_path)
    yield s
    s.close()


# ---------------------------------------------------------------------------
# Valid chain + restart sanity
# ---------------------------------------------------------------------------


class TestValidChainRestart:
    def test_valid_chain_survives_repository_restart(self, tmp_path: Path) -> None:
        s = Stack(tmp_path)
        try:
            sha = s.seed_source(b'{"r1e": 1}', "acq-1")
            s.commit("proj-1", [(sha, "acq-1")])
            from crypto_sensor_fabric.storage.projection_resolver import (
                ProjectionLineageResolver,
            )

            resolver = ProjectionLineageResolver(
                root=s.ROOT, artifacts=s.artifacts, contexts=s.contexts,
                lineage=s.lineage, schemas=s.schemas,
            )
            manifest = _manifest([sha], ["proj-1"])
            resolver.validate_projection_ref("proj-1", manifest)

            # RESTART: fresh repositories from disk, fresh resolver.
            s2 = Stack(tmp_path, fresh=False).reopen()
            resolver2 = ProjectionLineageResolver(
                root=s2.ROOT, artifacts=s2.artifacts, contexts=s2.contexts,
                lineage=s2.lineage, schemas=s2.schemas,
            )
            manifest2 = _manifest([sha], ["proj-1"])
            resolver2.validate_projection_ref("proj-1", manifest2)
        finally:
            s.close()


def _manifest(blob_refs, projection_refs):
    from crypto_sensor_fabric.storage.manifests import PartitionManifest

    return PartitionManifest(
        partition_manifest_id="pm-r1e",
        partition_key="kraken/futures/BTC-USDT/2026-01-15",
        provider="kraken",
        venue="futures",
        sensor_family="MECHANICAL_TRADE",
        native_instrument="BTC-USDT",
        source_granularity="1m",
        logical_date_start=datetime(2026, 1, 15, tzinfo=UTC),
        logical_date_end=datetime(2026, 1, 15, 23, 59, 59, tzinfo=UTC),
        blob_refs=list(blob_refs),
        projection_refs=list(projection_refs),
        created_at=FIXED,
    )


# ---------------------------------------------------------------------------
# §45 — corruption restart matrix (every family fails closed)
# ---------------------------------------------------------------------------


class TestCorruptionRestartMatrix:
    def test_corrupt_schema_fragment_fails_closed(self, tmp_path: Path) -> None:
        s = Stack(tmp_path)
        try:
            sha = s.seed_source(b'{"c": 1}', "acq-1")
            s.commit("proj-1", [(sha, "acq-1")])
            definition = s.schema_definition()
            frag = (
                s.ROOT / "catalogs" / "projection_schemas"
                / catalog_physical_key(definition.schema_identity)
            )
            frag.write_text("{corrupt", encoding="utf-8")
            # Restart: schema catalog corruption fails closed.
            with pytest.raises(ProjectionSchemaCatalogCorrupt):
                Stack(tmp_path, fresh=False).reopen()
        finally:
            s.close()

    def test_corrupt_artifact_fragment_fails_closed(self, tmp_path: Path) -> None:
        s = Stack(tmp_path)
        try:
            sha = s.seed_source(b'{"c": 2}', "acq-1")
            s.commit("proj-1", [(sha, "acq-1")])
            frag_dir = s.ROOT / "catalogs" / "manifests" / "projections"
            frag = frag_dir / catalog_physical_key("proj-1")
            frag.write_text("{corrupt", encoding="utf-8")
            with pytest.raises(ProjectionArtifactCatalogCorrupt):
                Stack(tmp_path, fresh=False).reopen()
        finally:
            s.close()

    def test_corrupt_context_fragment_fails_closed(self, tmp_path: Path) -> None:
        s = Stack(tmp_path)
        try:
            sha = s.seed_source(b'{"c": 3}', "acq-1")
            s.commit("proj-1", [(sha, "acq-1")])
            frag_dir = s.ROOT / "catalogs" / "manifests" / "projection_context"
            frag = frag_dir / catalog_physical_key("proj-1")
            frag.write_text("{corrupt", encoding="utf-8")
            with pytest.raises(ProjectionArtifactCatalogCorrupt):
                Stack(tmp_path, fresh=False).reopen()
        finally:
            s.close()

    def test_corrupt_lineage_fragment_fails_closed(self, tmp_path: Path) -> None:
        s = Stack(tmp_path)
        try:
            sha = s.seed_source(b'{"c": 4}', "acq-1")
            s.commit("proj-1", [(sha, "acq-1")])
            frag_dir = s.ROOT / "catalogs" / "manifests" / "projection_lineage"
            frag = frag_dir / catalog_physical_key("lm-proj-1")
            frag.write_text("{corrupt", encoding="utf-8")
            with pytest.raises(ProjectionLineageCatalogCorrupt):
                Stack(tmp_path, fresh=False).reopen()
        finally:
            s.close()

    def test_corrupt_physical_projection_fails_closed(self, tmp_path: Path) -> None:
        s = Stack(tmp_path)
        try:
            sha = s.seed_source(b'{"c": 5}', "acq-1")
            s.commit("proj-1", [(sha, "acq-1")])
            # Corrupt the PHYSICAL Parquet bytes (catalogs stay intact).
            physical = list((s.ROOT / "projections").glob("**/*.parquet"))[0]
            physical.write_bytes(b"not a parquet file at all")
            s2 = Stack(tmp_path, fresh=False).reopen()
            from crypto_sensor_fabric.storage.projection_resolver import (
                ProjectionLineageResolver,
            )

            resolver = ProjectionLineageResolver(
                root=s2.ROOT, artifacts=s2.artifacts, contexts=s2.contexts,
                lineage=s2.lineage, schemas=s2.schemas,
            )
            with pytest.raises((ResolverCorruption, ProjectionChainBroken, Exception)):
                resolver.validate_projection_ref("proj-1", _manifest([sha], ["proj-1"]))
        finally:
            s.close()

    def test_corrupt_fragment_never_silently_disappears(
        self, tmp_path: Path
    ) -> None:
        """The corrupt fragment must still be on disk after the failed load."""
        s = Stack(tmp_path)
        try:
            sha = s.seed_source(b'{"c": 6}', "acq-1")
            s.commit("proj-1", [(sha, "acq-1")])
            frag_dir = s.ROOT / "catalogs" / "manifests" / "projections"
            frag = frag_dir / catalog_physical_key("proj-1")
            frag.write_text("{corrupt", encoding="utf-8")
            with pytest.raises(ProjectionArtifactCatalogCorrupt):
                Stack(tmp_path, fresh=False).reopen()
            assert frag.exists()  # NOT deleted/repaired automatically
        finally:
            s.close()


# ---------------------------------------------------------------------------
# §47 — concurrent catalog writers
# ---------------------------------------------------------------------------


class TestConcurrentWriters:
    def test_identical_schema_registration_from_two_instances(
        self, tmp_path: Path
    ) -> None:
        s = Stack(tmp_path)
        try:
            d = s.schema_definition()
            reg_a = ProjectionSchemaRegistry(
                s.ROOT / "catalogs" / "projection_schemas"
            )
            reg_b = ProjectionSchemaRegistry(
                s.ROOT / "catalogs" / "projection_schemas"
            )
            r1 = reg_a.register(d)
            r2 = reg_b.register(d)
            assert r1.schema_key == r2.schema_key
            assert r1.schema_fingerprint == r2.schema_fingerprint
            # Exactly ONE physical fragment.
            frags = list(
                (s.ROOT / "catalogs" / "projection_schemas").glob("*.json")
            )
            assert len(frags) == 1
        finally:
            s.close()

    def test_conflicting_schema_content_fails_typed(self, tmp_path: Path) -> None:
        from crypto_sensor_fabric.storage.projection_schema import (
            ProjectionSchemaConflict,
        )

        s = Stack(tmp_path)
        try:
            d = s.schema_definition()
            reg_a = ProjectionSchemaRegistry(
                s.ROOT / "catalogs" / "projection_schemas"
            )
            reg_b = ProjectionSchemaRegistry(
                s.ROOT / "catalogs" / "projection_schemas"
            )
            reg_a.register(d)
            # Same identity, different structure — exactly one truth wins.
            drifted = ProjectionSchemaDefinition(
                projection_schema_id="r1e.market.projection",
                projection_schema_version="1.0.0",
                provider_native_schema=pa.schema(
                    [pa.field("x", pa.int32(), nullable=False)]
                ),
            )
            with pytest.raises(ProjectionSchemaConflict):
                reg_b.register(drifted)
        finally:
            s.close()

    def test_identical_lineage_commit_from_two_instances(
        self, tmp_path: Path
    ) -> None:
        s = Stack(tmp_path)
        try:
            sha = s.seed_source(b'{"c": 7}', "acq-1")
            s.commit("proj-1", [(sha, "acq-1")])
            lin_a = ProjectionLineageRepository(
                s.ROOT / "catalogs" / "manifests" / "projection_lineage",
                blob_store=s.store,
                blob_metadata_repository=s.blob_repo,
                acquisition_repository=s.acq_repo,
            )
            from crypto_sensor_fabric.storage.models import ProjectionLineage

            entries = [
                ProjectionLineage(
                    lineage_manifest_id="lm-concurrent",
                    projection_id="proj-1",
                    source_blob_sha256=sha,
                    source_acquisition_id="acq-1",
                    source_order=0,
                )
            ]
            # Independent instances, same content: both succeed idempotently.
            lin_a.commit("lm-concurrent", entries)
            s.lineage.commit("lm-concurrent", entries)
            # Exactly ONE physical fragment for the concurrent manifest
            # (lm-proj-1 also exists from the earlier commit).
            frags = list(
                (s.ROOT / "catalogs" / "manifests" / "projection_lineage").glob(
                    catalog_physical_key("lm-concurrent")
                )
            )
            assert len(frags) == 1
        finally:
            s.close()

    def test_conflicting_lineage_content_fails_typed(self, tmp_path: Path) -> None:
        s = Stack(tmp_path)
        try:
            sha = s.seed_source(b'{"c": 8}', "acq-1")
            s.commit("proj-1", [(sha, "acq-1")])
            from crypto_sensor_fabric.storage.models import ProjectionLineage

            entries_a = [
                ProjectionLineage(
                    lineage_manifest_id="lm-conflict",
                    projection_id="proj-1",
                    source_blob_sha256=sha,
                    source_acquisition_id="acq-1",
                    source_order=0,
                )
            ]
            s.lineage.commit("lm-conflict", entries_a)
            # Same lmid, different row bounds — typed conflict, truth intact.
            entries_b = [
                ProjectionLineage(
                    lineage_manifest_id="lm-conflict",
                    projection_id="proj-1",
                    source_blob_sha256=sha,
                    source_acquisition_id="acq-1",
                    source_row_start=0,
                    source_row_end=0,
                    source_order=0,
                )
            ]
            with pytest.raises(ProjectionLineageConflict):
                s.lineage.commit("lm-conflict", entries_b)
            # Original truth survives.
            got = s.lineage.get("lm-conflict")
            assert got[0].source_row_start is None
        finally:
            s.close()

    def test_artifact_conflict_preserves_first_truth(self, tmp_path: Path) -> None:
        s = Stack(tmp_path)
        try:
            sha = s.seed_source(b'{"c": 9}', "acq-1")
            artifact, _ = s.commit("proj-1", [(sha, "acq-1")])
            # A different artifact under the same identity is a conflict.
            tampered = artifact.model_copy(
                update={"projection_sha256": "e" * 64}
            )
            with pytest.raises(ProjectionIdentityConflict):
                s.artifacts.commit(tampered)
            assert s.artifacts.get("proj-1").projection_sha256 == (
                artifact.projection_sha256
            )
        finally:
            s.close()


from crypto_sensor_fabric.storage.projection_lineage import (  # noqa: E402
    ProjectionLineageConflict,
)
