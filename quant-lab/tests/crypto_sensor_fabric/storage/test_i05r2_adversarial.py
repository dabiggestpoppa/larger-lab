"""SENSOR-B4-I05R2D — fail-closed public-API, schema-attack and restart proofs.

Covers (I05R2 §30-§36):

- adversarial bypass tests (§31): no commit-capable artifact repository
  without projection_root / schema_registry; no verify_physical bypass;
  lineage commit without artifact/context repository fails at
  CONSTRUCTION; lineage for nonexistent projection / context-less
  projection fails before durable publication;
- native schema attack tests (§32): physically valid Parquet files with
  correct SHAs but wrong native type / nullability / field order /
  nested child type are rejected by BOTH the artifact repository and the
  production resolver (proving schema identity, not hash corruption);
- T0 value attack tests (§33): wrong provider/venue/sensor/instrument/
  parser/schema version/projection id and noncontiguous ordinals are
  rejected by the resolver;
- row-lineage attack tests (§34): one-sided and undeclared pairs are
  rejected by the resolver;
- duplicate projection refs (§35) rejected at model construction;
- catalog fault boundary truth (§36): an fsync spy proves
  AFTER_WRITE_BEFORE_FSYNC fires before ANY file fsync;
- restart regression (I05R1 §44): the valid chain still passes after
  full restart.
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
from crypto_sensor_fabric.storage.catalog import (
    AcquisitionRepository,
    BlobMetadataRepository,
)
from crypto_sensor_fabric.storage.checksums import sha256_file
from crypto_sensor_fabric.storage.enums import StorageEncoding
from crypto_sensor_fabric.storage.json_catalog import (
    CatalogFaultHook,
    CatalogFaultPoint,
    DurableJsonCatalog,
    FaultError,
)
from crypto_sensor_fabric.storage.models import (
    AcquisitionRecord,
    PartitionManifest,
    ProjectionLineage,
    RawProjectionArtifact,
)
from crypto_sensor_fabric.storage.projection_lineage import (
    LineageConfigurationError,
    ProjectionArtifactMissing,
    ProjectionContextMissing,
    ProjectionLineageRepository,
)
from crypto_sensor_fabric.storage.projection_resolver import (
    ProjectionLineageResolver,
)
from crypto_sensor_fabric.storage.projection_schema import (
    ProjectionSchemaDefinition,
    ProjectionSchemaRegistry,
    T0_METADATA_SCHEMA,
)
from crypto_sensor_fabric.storage.projections import (
    ProjectionArtifactRepository,
    ProjectionCatalogRecord,
    ProjectionContextRepository,
    ProjectionCorruption,
    write_projection,
)

FIXED = datetime(2026, 9, 12, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"
ROOT = Path("C:/tmp_r2d_proj")

NATIVE = pa.schema(
    [
        pa.field("price", pa.float64(), nullable=False),
        pa.field("qty", pa.int64(), nullable=True),
        pa.field("symbol", pa.string(), nullable=False),
    ]
)

FULL_SCHEMA = pa.schema(list(NATIVE) + list(T0_METADATA_SCHEMA))


# ---------------------------------------------------------------------------
# Sealed real stack (I05R2 §30): every repository is the production form
# ---------------------------------------------------------------------------


class SealedChain:
    """Real production stack; short roots (Windows MAX_PATH)."""

    def __init__(self, tmp_path: Path, *, fresh: bool = True) -> None:
        if fresh:
            if ROOT.exists():
                shutil.rmtree(ROOT)
            ROOT.mkdir(parents=True)
        else:
            ROOT.mkdir(parents=True, exist_ok=True)
        self.root = ROOT

        self.t0a = tmp_path / "t0a"
        self.t0a.mkdir(exist_ok=True)
        self.store = LocalBlobStore(str(self.t0a), clock=lambda: FIXED)
        self.blob_repo = BlobMetadataRepository(
            self.t0a, blob_store=self.store, clock=lambda: FIXED
        )
        self.acq_repo = AcquisitionRepository(
            self.t0a,
            blob_store=self.store,
            blob_metadata_repository=self.blob_repo,
            clock=lambda: FIXED,
        )
        self.reopen()

    def reopen(self) -> "SealedChain":
        """Discard and reinstantiate every T0B repository from disk."""
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
        return self

    def close(self) -> None:
        if ROOT.exists():
            shutil.rmtree(ROOT, ignore_errors=True)

    # -- helpers -------------------------------------------------------------

    def definition(self) -> ProjectionSchemaDefinition:
        return ProjectionSchemaDefinition(
            projection_schema_id="r2d.market.projection",
            projection_schema_version="1.0.0",
            provider_native_schema=NATIVE,
        )

    def register(self) -> ProjectionSchemaDefinition:
        d = self.definition()
        self.schemas.register(d)
        return d

    def seed(self, data: bytes, acq_id: str) -> str:
        put = self.store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        )
        self.blob_repo.append_metadata(put.blob)
        sha = put.blob.blob_sha256
        self.acq_repo.append_acquisition(_acq(acq_id, sha))
        return sha

    def commit_chain(
        self,
        projection_id: str,
        pairs: list[tuple[str, str]],
        *,
        rows: list[dict] | None = None,
        lineage_manifest_id: str | None = None,
        definition: ProjectionSchemaDefinition | None = None,
    ) -> RawProjectionArtifact:
        """Full sealed chain: physical -> artifact -> context -> lineage."""
        d = definition or self.definition()
        sources = [s for s, _a in pairs]
        acq_ids = [a for _s, a in pairs]
        if rows is None:
            rows = [{"price": 1.0, "qty": 1, "symbol": "BTC-USDT"}]
        artifact, _path = write_projection(
            root=self.root,
            rows=rows,
            schema_definition=d,
            schema_registry=self.schemas,
            projection_id=projection_id,
            source_blob_sha256=sources,
            acquisition_ids=acq_ids,
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
        self.contexts.commit(
            ProjectionCatalogRecord(
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
                lineage_manifest_id=lineage_manifest_id or f"lm-{projection_id}",
                quality_flags=[],
                created_at=FIXED,
            )
        )
        lmid = lineage_manifest_id or f"lm-{projection_id}"
        self.lineage.commit(
            lmid,
            [
                ProjectionLineage(
                    lineage_manifest_id=lmid,
                    projection_id=projection_id,
                    source_blob_sha256=sha,
                    source_acquisition_id=acq_id,
                    source_order=order,
                )
                for order, (sha, acq_id) in enumerate(pairs)
            ],
        )
        return artifact

    def manifest(
        self,
        manifest_id: str,
        *,
        blob_refs: list[str],
        projection_refs: list[str],
    ) -> PartitionManifest:
        return PartitionManifest(
            partition_manifest_id=manifest_id,
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            provider="kraken",
            venue="futures",
            sensor_family="MECHANICAL_TRADE",
            native_instrument="BTC-USDT",
            source_granularity="1m",
            logical_date_start=datetime(2026, 1, 15, tzinfo=UTC),
            logical_date_end=datetime(2026, 1, 15, 23, 59, 59, tzinfo=UTC),
            blob_refs=blob_refs,
            projection_refs=projection_refs,
            created_at=FIXED,
        )


def _acq(
    acq_id: str,
    sha: str,
    provider: str = "kraken",
    venue: str = "futures",
    sensor: str = "MECHANICAL_TRADE",
    instrument: str = "BTC-USDT",
) -> AcquisitionRecord:
    return AcquisitionRecord(
        acquisition_id=acq_id,
        provider_id=provider,
        venue=venue,
        sensor_family=sensor,
        request_fingerprint="fp",
        adapter_version="1.0",
        requested_start=datetime(2026, 1, 1, tzinfo=UTC),
        requested_end=datetime(2026, 1, 2, tzinfo=UTC),
        native_instrument=instrument,
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


# ---------------------------------------------------------------------------
# Shared attack-file helpers
# ---------------------------------------------------------------------------


def _write_parquet(root: Path, uri: str, schema: pa.Schema, columns: dict) -> str:
    """Write a physically valid Parquet file; return its exact SHA."""
    target = root / uri
    target.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table(columns, schema=schema), str(target))
    return sha256_file(str(target)).hex_digest


def _t0_row(
    projection_id: str,
    blob_sha: str,
    acq_id: str,
    n: int = 1,
    **overrides,
) -> dict[str, list]:
    """Full T0 column set with correct constant values for n rows."""
    cols: dict[str, list] = {
        "_t0_projection_id": [projection_id] * n,
        "_t0_source_blob_sha256": [blob_sha] * n,
        "_t0_acquisition_id": [acq_id] * n,
        "_t0_provider": ["kraken"] * n,
        "_t0_venue": ["futures"] * n,
        "_t0_sensor_family": ["MECHANICAL_TRADE"] * n,
        "_t0_native_instrument": ["BTC-USDT"] * n,
        "_t0_parser_version": ["1.0.0"] * n,
        "_t0_schema_version": ["1.0.0"] * n,
        "_t0_row_ordinal": list(range(n)),
    }
    cols.update(overrides)
    return cols


def _rewrite_committed_sha(root: Path, projection_id: str, new_sha: str) -> None:
    """Filesystem-level forgery: point artifact+context fragments at a new
    SHA so an attack isolates VALUE/SCHEMA mutation (catalogs are immutable
    by design; only a test may do this directly)."""
    for base in (
        root / "catalogs" / "manifests" / "projections",
        root / "catalogs" / "manifests" / "projection_context",
    ):
        for fragment in base.glob("*.json"):
            payload = json.loads(fragment.read_text(encoding="utf-8"))
            if payload.get("projection_id") == projection_id:
                payload["projection_sha256"] = new_sha
                raw = json.dumps(
                    payload, sort_keys=True, ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
                fragment.write_bytes(raw)


# ---------------------------------------------------------------------------
# §31 — adversarial bypass tests
# ---------------------------------------------------------------------------


class TestPublicApiBypass:
    def test_artifact_repo_without_root_fails(self, tmp_path: Path) -> None:
        """§31A: construction without projection_root fails."""
        with pytest.raises(TypeError):
            ProjectionArtifactRepository(tmp_path / "a")  # type: ignore[call-arg]

    def test_artifact_repo_without_registry_fails(self, tmp_path: Path) -> None:
        """§31B: construction without schema_registry fails."""
        with pytest.raises(TypeError):
            ProjectionArtifactRepository(  # type: ignore[call-arg]
                tmp_path / "a", projection_root=tmp_path / "t0"
            )

    def test_no_verify_physical_bypass_exists(self, tmp_path: Path) -> None:
        """§31C: verify_physical is not a constructor parameter at all."""
        with pytest.raises(TypeError):
            ProjectionArtifactRepository(  # type: ignore[call-arg]
                tmp_path / "a",
                projection_root=tmp_path / "t0",
                schema_registry=ProjectionSchemaRegistry(tmp_path / "s"),
                verify_physical=False,
            )

    def test_lineage_without_artifact_repo_fails_at_construction(
        self, tmp_path: Path
    ) -> None:
        """§31D: typed failure BEFORE any durable publication is possible."""
        with pytest.raises(LineageConfigurationError, match="artifact_repository"):
            ProjectionLineageRepository(  # type: ignore[call-arg]
                tmp_path / "lin",
                blob_store=object(),
                blob_metadata_repository=object(),
                acquisition_repository=object(),
                context_repository=object(),
            )

    def test_lineage_without_context_repo_fails_at_construction(
        self, tmp_path: Path
    ) -> None:
        """§31E: typed failure BEFORE any durable publication is possible."""
        with pytest.raises(LineageConfigurationError, match="context_repository"):
            ProjectionLineageRepository(  # type: ignore[call-arg]
                tmp_path / "lin",
                blob_store=object(),
                blob_metadata_repository=object(),
                acquisition_repository=object(),
                artifact_repository=object(),
            )

    def test_lineage_bare_construction_fails_typed(
        self, tmp_path: Path
    ) -> None:
        """Any missing dependency is a typed construction failure."""
        with pytest.raises(LineageConfigurationError):
            ProjectionLineageRepository(tmp_path / "lin")  # type: ignore[call-arg]

    def test_lineage_for_nonexistent_projection_fails(
        self, tmp_path: Path
    ) -> None:
        """§31F: typed failure before persistence."""
        c = SealedChain(tmp_path)
        try:
            sha = c.seed(b'{"f": 1}', "acq-f1")
            with pytest.raises(ProjectionArtifactMissing):
                c.lineage.commit(
                    "lm-ghost",
                    [
                        ProjectionLineage(
                            lineage_manifest_id="lm-ghost",
                            projection_id="proj-ghost",
                            source_blob_sha256=sha,
                            source_acquisition_id="acq-f1",
                            source_order=0,
                        )
                    ],
                )
        finally:
            c.close()

    def test_lineage_for_contextless_projection_fails(
        self, tmp_path: Path
    ) -> None:
        """§31G: artifact present, context missing -> typed failure."""
        c = SealedChain(tmp_path)
        try:
            d = c.register()
            sha = c.seed(b'{"f": 2}', "acq-f2")
            artifact, _p = write_projection(
                root=c.root,
                rows=[{"price": 1.0, "qty": 1, "symbol": "BTC-USDT"}],
                schema_definition=d,
                schema_registry=c.schemas,
                projection_id="proj-noctx",
                source_blob_sha256=[sha],
                acquisition_ids=["acq-f2"],
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
            c.artifacts.commit(artifact)
            with pytest.raises(ProjectionContextMissing):
                c.lineage.commit(
                    "lm-noctx",
                    [
                        ProjectionLineage(
                            lineage_manifest_id="lm-noctx",
                            projection_id="proj-noctx",
                            source_blob_sha256=sha,
                            source_acquisition_id="acq-f2",
                            source_order=0,
                        )
                    ],
                )
        finally:
            c.close()


# ---------------------------------------------------------------------------
# §32 — native schema attack tests (schema identity, not hash corruption)
# ---------------------------------------------------------------------------


def _attack_artifact(sha: str, uri: str, row_count: int = 1) -> RawProjectionArtifact:
    return RawProjectionArtifact(
        projection_id="proj-atk",
        source_blob_sha256=["a" * 64],
        projection_schema_id="r2d.market.projection",
        projection_schema_version="1.0.0",
        parser_version="1.0.0",
        row_count=row_count,
        partition_key="kraken/futures/BTC-USDT/2026-01-15",
        projection_uri=uri,
        projection_sha256=sha,
    )


class TestNativeSchemaAttacks:
    """Correct SHAs over malicious bytes: only schema identity saves us."""

    def _repo(self, tmp_path: Path) -> tuple[ProjectionArtifactRepository, Path]:
        t0 = tmp_path / "t0"
        t0.mkdir()
        schemas = ProjectionSchemaRegistry(tmp_path / "schemas")
        schemas.register(
            ProjectionSchemaDefinition(
                projection_schema_id="r2d.market.projection",
                projection_schema_version="1.0.0",
                provider_native_schema=NATIVE,
            )
        )
        repo = ProjectionArtifactRepository(
            tmp_path / "artifacts",
            projection_root=t0,
            schema_registry=schemas,
        )
        return repo, t0

    def test_exact_schema_accepted(self, tmp_path: Path) -> None:
        """Control: correct schema + correct SHA is accepted."""
        repo, t0 = self._repo(tmp_path)
        uri = "projections/exact/part-00000.parquet"
        cols = {"price": [1.0], "qty": [1], "symbol": ["BTC-USDT"]}
        cols.update(_t0_row("proj-atk", "a" * 64, "acq-atk"))
        sha = _write_parquet(t0, uri, FULL_SCHEMA, cols)
        committed = repo.commit(_attack_artifact(sha, uri))
        assert committed.projection_id == "proj-atk"

    def test_wrong_native_type_rejected(self, tmp_path: Path) -> None:
        """price: string in the file vs double registered — SHA is correct."""
        repo, t0 = self._repo(tmp_path)
        wrong = pa.schema(
            [
                pa.field("price", pa.string(), nullable=False),
                pa.field("qty", pa.int64(), nullable=True),
                pa.field("symbol", pa.string(), nullable=False),
            ]
            + list(T0_METADATA_SCHEMA)
        )
        uri = "projections/wrongtype/part-00000.parquet"
        cols = {"price": ["1.0"], "qty": [1], "symbol": ["BTC-USDT"]}
        cols.update(_t0_row("proj-atk", "a" * 64, "acq-atk"))
        sha = _write_parquet(t0, uri, wrong, cols)
        with pytest.raises(ProjectionCorruption, match="EXACTLY"):
            repo.commit(_attack_artifact(sha, uri))

    def test_wrong_native_nullability_rejected(self, tmp_path: Path) -> None:
        """price nullable in the file but NOT NULL registered."""
        repo, t0 = self._repo(tmp_path)
        wrong = pa.schema(
            [
                pa.field("price", pa.float64(), nullable=True),
                pa.field("qty", pa.int64(), nullable=True),
                pa.field("symbol", pa.string(), nullable=False),
            ]
            + list(T0_METADATA_SCHEMA)
        )
        uri = "projections/wrongnull/part-00000.parquet"
        cols = {"price": [1.0], "qty": [1], "symbol": ["BTC-USDT"]}
        cols.update(_t0_row("proj-atk", "a" * 64, "acq-atk"))
        sha = _write_parquet(t0, uri, wrong, cols)
        with pytest.raises(ProjectionCorruption, match="EXACTLY"):
            repo.commit(_attack_artifact(sha, uri))

    def test_wrong_native_order_rejected(self, tmp_path: Path) -> None:
        """Registered field order is part of schema identity (§16)."""
        repo, t0 = self._repo(tmp_path)
        wrong = pa.schema(
            [
                pa.field("qty", pa.int64(), nullable=True),
                pa.field("price", pa.float64(), nullable=False),
                pa.field("symbol", pa.string(), nullable=False),
            ]
            + list(T0_METADATA_SCHEMA)
        )
        uri = "projections/wrongorder/part-00000.parquet"
        cols = {"qty": [1], "price": [1.0], "symbol": ["BTC-USDT"]}
        cols.update(_t0_row("proj-atk", "a" * 64, "acq-atk"))
        sha = _write_parquet(t0, uri, wrong, cols)
        with pytest.raises(ProjectionCorruption, match="EXACTLY"):
            repo.commit(_attack_artifact(sha, uri))

    def test_wrong_nested_child_type_rejected(self, tmp_path: Path) -> None:
        """Nested struct child nullability drift caught by exact equality."""
        repo, t0 = self._repo(tmp_path)
        nested_native = pa.schema(
            [
                pa.field(
                    "level",
                    pa.struct(
                        [
                            pa.field("price", pa.float64(), nullable=False),
                            pa.field("qty", pa.int64(), nullable=True),
                        ]
                    ),
                    nullable=False,
                ),
                pa.field("symbol", pa.string(), nullable=False),
            ]
        )
        repo._schema_registry.register(
            ProjectionSchemaDefinition(
                projection_schema_id="r2d.nested.projection",
                projection_schema_version="1.0.0",
                provider_native_schema=nested_native,
            )
        )
        wrong = pa.schema(
            [
                pa.field(
                    "level",
                    pa.struct(
                        [
                            # child nullable where registered says not-null
                            pa.field("price", pa.float64(), nullable=True),
                            pa.field("qty", pa.int64(), nullable=True),
                        ]
                    ),
                    nullable=False,
                ),
                pa.field("symbol", pa.string(), nullable=False),
            ]
            + list(T0_METADATA_SCHEMA)
        )
        uri = "projections/wrongnested/part-00000.parquet"
        cols = {"level": [{"price": 1.0, "qty": 1}], "symbol": ["BTC-USDT"]}
        cols.update(_t0_row("proj-atk", "a" * 64, "acq-atk"))
        sha = _write_parquet(t0, uri, wrong, cols)
        artifact = _attack_artifact(sha, uri).model_copy(
            update={"projection_schema_id": "r2d.nested.projection"}
        )
        with pytest.raises(ProjectionCorruption, match="EXACTLY"):
            repo.commit(artifact)

    def test_resolver_rejects_forged_bytes_on_read(self, tmp_path: Path) -> None:
        """§22/§32: the resolver re-proves the bytes NOW.  A same-schema
        file with mutated values (duplicated ordinal) and a stale committed
        SHA fails at the SHA gate; a file whose SHA was forged into the
        catalog fails at the T0-value gate.  Writer trust is void."""
        c = SealedChain(tmp_path)
        try:
            c.register()
            sha = c.seed(b'{"forge": 1}', "acq-fg")
            artifact = c.commit_chain("proj-forged", [(sha, "acq-fg")])
            # The honest chain passes.
            c.resolver.validate_projection_ref(
                "proj-forged",
                c.manifest(
                    "pm-honest", blob_refs=[sha], projection_refs=["proj-forged"]
                ),
            )
            # Forge 1: replace the physical bytes (schema exact, values wrong,
            # duplicated ordinal) WITHOUT updating the committed SHA.
            target = c.root / artifact.projection_uri
            cols = {"price": [5.0, 6.0], "qty": [1, 1], "symbol": ["BTC-USDT"] * 2}
            cols.update(_t0_row("proj-forged", sha, "acq-fg", n=2))
            cols["_t0_row_ordinal"] = [0, 0]
            pq.write_table(pa.table(cols, schema=FULL_SCHEMA), str(target))
            assert sha256_file(str(target)).hex_digest != artifact.projection_sha256
            with pytest.raises(ProjectionCorruption):
                c.resolver.validate_projection_ref(
                    "proj-forged",
                    c.manifest(
                        "pm-f1", blob_refs=[sha], projection_refs=["proj-forged"]
                    ),
                )
            # Forge 2: point the committed metadata at the forged bytes'
            # actual SHA — the schema now agrees, so the T0-VALUE gate fires.
            forged_sha = sha256_file(str(target)).hex_digest
            _rewrite_committed_sha(c.root, "proj-forged", forged_sha)
            c.reopen()
            with pytest.raises(ProjectionCorruption):
                c.resolver.validate_projection_ref(
                    "proj-forged",
                    c.manifest(
                        "pm-f2", blob_refs=[sha], projection_refs=["proj-forged"]
                    ),
                )
        finally:
            c.close()

    def test_resolver_rejects_wrong_native_schema_on_read(
        self, tmp_path: Path
    ) -> None:
        """§32 resolver side: a file whose SHA was forged into the catalog
        but whose native schema is wrong (price as string) fails the
        exact-schema gate at read time."""
        c = SealedChain(tmp_path)
        try:
            c.register()
            sha = c.seed(b'{"wt": 1}', "acq-wt")
            artifact = c.commit_chain("proj-wt", [(sha, "acq-wt")])
            target = c.root / artifact.projection_uri
            wrong = pa.schema(
                [
                    pa.field("price", pa.string(), nullable=False),
                    pa.field("qty", pa.int64(), nullable=True),
                    pa.field("symbol", pa.string(), nullable=False),
                ]
                + list(T0_METADATA_SCHEMA)
            )
            cols = {"price": ["1.0"], "qty": [1], "symbol": ["BTC-USDT"]}
            cols.update(_t0_row("proj-wt", sha, "acq-wt"))
            pq.write_table(pa.table(cols, schema=wrong), str(target))
            forged_sha = sha256_file(str(target)).hex_digest
            _rewrite_committed_sha(c.root, "proj-wt", forged_sha)
            c.reopen()
            with pytest.raises(ProjectionCorruption, match="EXACTLY"):
                c.resolver.validate_projection_ref(
                    "proj-wt",
                    c.manifest(
                        "pm-wt", blob_refs=[sha], projection_refs=["proj-wt"]
                    ),
                )
        finally:
            c.close()


# ---------------------------------------------------------------------------
# §33 — T0 value attack tests (valid schema + correct SHA, mutated values)
# ---------------------------------------------------------------------------


class TestT0ValueAttacks:
    def _chain_with_mutated_value(
        self, tmp_path: Path, mutate: dict[str, list]
    ) -> tuple[SealedChain, RawProjectionArtifact, str]:
        """Honest chain, then rewrite its file with one mutated T0 value and
        point the committed metadata at the new SHA: ONLY the value is wrong."""
        c = SealedChain(tmp_path)
        c.register()
        sha = c.seed(b'{"t0": 1}', "acq-t0")
        artifact = c.commit_chain("proj-t0atk", [(sha, "acq-t0")])
        target = c.root / artifact.projection_uri
        cols = {"price": [1.0], "qty": [1], "symbol": ["BTC-USDT"]}
        cols.update(_t0_row("proj-t0atk", sha, "acq-t0", **mutate))
        pq.write_table(pa.table(cols, schema=FULL_SCHEMA), str(target))
        new_sha = sha256_file(str(target)).hex_digest
        _rewrite_committed_sha(c.root, "proj-t0atk", new_sha)
        c.reopen()
        return c, artifact, sha

    @pytest.mark.parametrize(
        "label,mutate",
        [
            ("wrong_provider", {"_t0_provider": ["gate"]}),
            ("wrong_venue", {"_t0_venue": ["spot"]}),
            ("wrong_sensor", {"_t0_sensor_family": ["MARKET_DATA"]}),
            ("wrong_instrument", {"_t0_native_instrument": ["ETH-USDT"]}),
            ("wrong_parser", {"_t0_parser_version": ["9.9.9"]}),
            ("wrong_schema_version", {"_t0_schema_version": ["9.9.9"]}),
            ("wrong_projection_id", {"_t0_projection_id": ["proj-evil"]}),
        ],
    )
    def test_mutated_t0_constant_rejected(
        self, tmp_path: Path, label: str, mutate: dict[str, list]
    ) -> None:
        """§33: every mutated T0 constant is rejected by the resolver."""
        c, _artifact, sha = self._chain_with_mutated_value(tmp_path, mutate)
        try:
            manifest = c.manifest(
                "pm-t0atk", blob_refs=[sha], projection_refs=["proj-t0atk"]
            )
            with pytest.raises(ProjectionCorruption):
                c.resolver.validate_projection_ref("proj-t0atk", manifest)
        finally:
            c.close()

    def test_noncontiguous_row_ordinal_rejected(self, tmp_path: Path) -> None:
        """§20/§33: ordinals [0, 2] (gap) fail even with matching SHA."""
        c = SealedChain(tmp_path)
        try:
            c.register()
            sha = c.seed(b'{"ord": 1}', "acq-ord")
            artifact = c.commit_chain(
                "proj-ordatk",
                [(sha, "acq-ord")],
                rows=[
                    {"price": 1.0, "qty": 1, "symbol": "BTC-USDT"},
                    {"price": 2.0, "qty": 2, "symbol": "BTC-USDT"},
                ],
            )
            target = c.root / artifact.projection_uri
            cols = {
                "price": [1.0, 2.0],
                "qty": [1, 2],
                "symbol": ["BTC-USDT"] * 2,
            }
            cols.update(
                _t0_row("proj-ordatk", sha, "acq-ord", n=2)
            )
            cols["_t0_row_ordinal"] = [0, 2]
            pq.write_table(pa.table(cols, schema=FULL_SCHEMA), str(target))
            new_sha = sha256_file(str(target)).hex_digest
            _rewrite_committed_sha(c.root, "proj-ordatk", new_sha)
            c.reopen()
            manifest = c.manifest(
                "pm-ordatk", blob_refs=[sha], projection_refs=["proj-ordatk"]
            )
            with pytest.raises(ProjectionCorruption, match="contiguous"):
                c.resolver.validate_projection_ref("proj-ordatk", manifest)
        finally:
            c.close()


# ---------------------------------------------------------------------------
# §34 — row-lineage attack tests
# ---------------------------------------------------------------------------


class TestRowLineageAttacks:
    def _rewrite_file(self, c: SealedChain, artifact, columns: dict) -> None:
        target = c.root / artifact.projection_uri
        pq.write_table(pa.table(columns, schema=FULL_SCHEMA), str(target))
        new_sha = sha256_file(str(target)).hex_digest
        _rewrite_committed_sha(c.root, artifact.projection_id, new_sha)
        c.reopen()

    def _honest_row(self, projection_id: str, sha: str, acq_id: str) -> dict:
        cols = {"price": [1.0], "qty": [1], "symbol": ["BTC-USDT"]}
        cols.update(_t0_row(projection_id, sha, acq_id))
        return cols

    def test_single_source_wrong_acquisition_rejected(
        self, tmp_path: Path
    ) -> None:
        c = SealedChain(tmp_path)
        try:
            c.register()
            sha = c.seed(b'{"rl": 1}', "acq-rl1")
            c.seed(b'{"rl": 2}', "acq-rl2")  # real durable decoy acquisition
            artifact = c.commit_chain("proj-rl", [(sha, "acq-rl1")])
            self._rewrite_file(
                c,
                artifact,
                self._honest_row("proj-rl", sha, "acq-rl2"),
            )
            manifest = c.manifest(
                "pm-rl", blob_refs=[sha], projection_refs=["proj-rl"]
            )
            with pytest.raises(ProjectionCorruption, match="single-source"):
                c.resolver.validate_projection_ref("proj-rl", manifest)
        finally:
            c.close()

    def test_single_source_wrong_blob_rejected(self, tmp_path: Path) -> None:
        c = SealedChain(tmp_path)
        try:
            c.register()
            sha = c.seed(b'{"rl": 3}', "acq-rl3")
            artifact = c.commit_chain("proj-rl", [(sha, "acq-rl3")])
            self._rewrite_file(
                c,
                artifact,
                self._honest_row("proj-rl", "b" * 64, "acq-rl3"),
            )
            manifest = c.manifest(
                "pm-rl", blob_refs=[sha], projection_refs=["proj-rl"]
            )
            with pytest.raises(ProjectionCorruption, match="single-source"):
                c.resolver.validate_projection_ref("proj-rl", manifest)
        finally:
            c.close()

    def test_multi_source_undeclared_pair_rejected(self, tmp_path: Path) -> None:
        c = SealedChain(tmp_path)
        try:
            c.register()
            sha_a = c.seed(b'{"m": 1}', "acq-m1")
            sha_b = c.seed(b'{"m": 2}', "acq-m2")
            sha_c = c.seed(b'{"m": 3}', "acq-m3")  # NOT in lineage
            artifact = c.commit_chain(
                "proj-ms",
                [(sha_a, "acq-m1"), (sha_b, "acq-m2")],
                rows=[
                    {"price": 1.0, "qty": 1, "symbol": "BTC-USDT"},
                    {"price": 2.0, "qty": 2, "symbol": "BTC-USDT"},
                ],
            )
            cols = {
                "price": [1.0, 2.0],
                "qty": [1, 2],
                "symbol": ["BTC-USDT"] * 2,
                # Row 0 claims (sha_c, acq-m3): an UNDECLARED pair.
                "_t0_projection_id": ["proj-ms"] * 2,
                "_t0_source_blob_sha256": [sha_c, None],
                "_t0_acquisition_id": ["acq-m3", None],
                "_t0_provider": ["kraken"] * 2,
                "_t0_venue": ["futures"] * 2,
                "_t0_sensor_family": ["MECHANICAL_TRADE"] * 2,
                "_t0_native_instrument": ["BTC-USDT"] * 2,
                "_t0_parser_version": ["1.0.0"] * 2,
                "_t0_schema_version": ["1.0.0"] * 2,
                "_t0_row_ordinal": [0, 1],
            }
            self._rewrite_file(c, artifact, cols)
            manifest = c.manifest(
                "pm-ms", blob_refs=[sha_a, sha_b], projection_refs=["proj-ms"]
            )
            with pytest.raises(ProjectionCorruption, match="committed lineage pair"):
                c.resolver.validate_projection_ref("proj-ms", manifest)
        finally:
            c.close()

    @pytest.mark.parametrize(
        "label,blob_col,acq_col",
        [
            ("blob_with_null_acq", ["a" * 64], [None]),
            ("null_blob_with_acq", [None], ["acq-os"]),
        ],
    )
    def test_one_sided_pairs_rejected(
        self, tmp_path: Path, label: str, blob_col: list, acq_col: list
    ) -> None:
        """(blob, NULL) and (NULL, acquisition) both rejected (§21)."""
        c = SealedChain(tmp_path)
        try:
            c.register()
            sha = c.seed(b'{"os": 1}', "acq-os")
            artifact = c.commit_chain("proj-rl", [(sha, "acq-os")])
            cols = self._honest_row("proj-rl", sha, "acq-os")
            cols["_t0_source_blob_sha256"] = blob_col
            cols["_t0_acquisition_id"] = acq_col
            self._rewrite_file(c, artifact, cols)
            manifest = c.manifest(
                "pm-rl", blob_refs=[sha], projection_refs=["proj-rl"]
            )
            with pytest.raises(ProjectionCorruption):
                c.resolver.validate_projection_ref("proj-rl", manifest)
        finally:
            c.close()


# ---------------------------------------------------------------------------
# §35 — duplicate projection refs
# ---------------------------------------------------------------------------


class TestDuplicateProjectionRefs:
    def test_duplicate_projection_refs_rejected(self) -> None:
        """["p1", "p1"] fails at MODEL construction, before persistence."""
        with pytest.raises(ValueError, match="duplicate projection"):
            PartitionManifest(
                partition_manifest_id="pm-dup",
                partition_key="k",
                provider="kraken",
                venue="futures",
                sensor_family="MECHANICAL_TRADE",
                native_instrument="BTC-USDT",
                logical_date_start=datetime(2026, 1, 15, tzinfo=UTC),
                logical_date_end=datetime(2026, 1, 15, 23, 59, 59, tzinfo=UTC),
                blob_refs=["a" * 64],
                projection_refs=["p1", "p1"],
                created_at=FIXED,
            )

    def test_unique_projection_refs_accepted(self) -> None:
        m = PartitionManifest(
            partition_manifest_id="pm-uniq",
            partition_key="k",
            provider="kraken",
            venue="futures",
            sensor_family="MECHANICAL_TRADE",
            native_instrument="BTC-USDT",
            logical_date_start=datetime(2026, 1, 15, tzinfo=UTC),
            logical_date_end=datetime(2026, 1, 15, 23, 59, 59, tzinfo=UTC),
            blob_refs=["a" * 64],
            projection_refs=["p1", "p2"],
            created_at=FIXED,
        )
        assert m.projection_refs == ["p1", "p2"]

    def test_unique_refs_still_pass_resolver(self, tmp_path: Path) -> None:
        c = SealedChain(tmp_path)
        try:
            c.register()
            sha = c.seed(b'{"dup": 1}', "acq-dup")
            c.commit_chain("proj-dup", [(sha, "acq-dup")])
            manifest = c.manifest(
                "pm-dupok", blob_refs=[sha], projection_refs=["proj-dup"]
            )
            c.resolver.validate_projection_ref("proj-dup", manifest)
        finally:
            c.close()


# ---------------------------------------------------------------------------
# §36 — catalog fault boundary truth with an fsync spy
# ---------------------------------------------------------------------------


class _FsyncSpy:
    """Intercepts atomic/json_catalog fsync helpers to record real calls."""

    def __init__(self) -> None:
        self.file_fsyncs = 0
        self.dir_fsyncs = 0

    def install(self, monkeypatch) -> None:
        import crypto_sensor_fabric.storage.atomic as atomic
        import crypto_sensor_fabric.storage.json_catalog as jc

        real_file = atomic.fsync_file
        real_dir = atomic.fsync_directory

        def spy_file(path):
            self.file_fsyncs += 1
            return real_file(path)

        def spy_dir(path):
            self.dir_fsyncs += 1
            return real_dir(path)

        monkeypatch.setattr(atomic, "fsync_file", spy_file)
        monkeypatch.setattr(jc, "fsync_file", spy_file)
        monkeypatch.setattr(atomic, "fsync_directory", spy_dir)
        monkeypatch.setattr(jc, "fsync_directory", spy_dir)


class TestCrashBoundaryTruth:
    def test_after_write_fault_fires_before_any_file_fsync(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """§36: the named fault point precedes ALL file durability fsyncs.

        Proven with an fsync SPY (not operation labels): when
        AFTER_WRITE_BEFORE_FSYNC is armed, the FaultError is raised while
        the file-fsync count is still ZERO.
        """
        spy = _FsyncSpy()
        spy.install(monkeypatch)

        cat = DurableJsonCatalog(
            tmp_path / "cat",
            logical_id_field="id",
            fault_hooks=CatalogFaultHook(
                CatalogFaultPoint.AFTER_WRITE_BEFORE_FSYNC
            ),
        )
        with pytest.raises(FaultError):
            cat.commit("obj-1", {"id": "obj-1", "v": 1})

        assert spy.file_fsyncs == 0, (
            "AFTER_WRITE_BEFORE_FSYNC must fire before ANY file fsync; "
            f"saw {spy.file_fsyncs}"
        )
        # No final object, no committed truth.
        assert not cat.has("obj-1")
        assert not cat._physical_path("obj-1").exists()

    def test_unfaulted_commit_fsyncs_file_exactly_once(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        """§27: exactly ONE file fsync of the staged artifact (no fake
        double-boundary evidence), then the parent-dir fsync."""
        spy = _FsyncSpy()
        spy.install(monkeypatch)

        cat = DurableJsonCatalog(tmp_path / "cat", logical_id_field="id")
        cat.commit("obj-2", {"id": "obj-2", "v": 2})

        assert spy.file_fsyncs == 1
        assert spy.dir_fsyncs >= 1
        assert cat.has("obj-2")

    def test_post_publish_fault_preserves_final_object(
        self, tmp_path: Path
    ) -> None:
        """Crash after publish: final may exist as crash evidence, but the
        crashing invocation never claims success."""
        cat = DurableJsonCatalog(
            tmp_path / "cat",
            logical_id_field="id",
            fault_hooks=CatalogFaultHook(
                CatalogFaultPoint.AFTER_PUBLISH_BEFORE_DIR_FSYNC
            ),
        )
        with pytest.raises(FaultError):
            cat.commit("obj-3", {"id": "obj-3", "v": 3})
        assert cat._physical_path("obj-3").exists()  # crash evidence
        assert not cat.has("obj-3")  # no success claimed


# ---------------------------------------------------------------------------
# I05R1 §44 restart regression: the valid chain still passes
# ---------------------------------------------------------------------------


class TestRestartRegression:
    def test_valid_chain_survives_restart(self, tmp_path: Path) -> None:
        c = SealedChain(tmp_path)
        try:
            c.register()
            sha_a = c.seed(b'{"r": "a"}', "acq-ra")
            sha_b = c.seed(b'{"r": "b"}', "acq-rb")
            c.commit_chain(
                "proj-restart",
                [(sha_a, "acq-ra"), (sha_b, "acq-rb")],
                rows=[
                    {"price": 1.0, "qty": 1, "symbol": "BTC-USDT"},
                    {"price": 2.0, "qty": 2, "symbol": "BTC-USDT"},
                ],
            )
            # Discard all Python objects; reinstantiate from disk.
            c.reopen()
            manifest = c.manifest(
                "pm-restart",
                blob_refs=[sha_a, sha_b],
                projection_refs=["proj-restart"],
            )
            c.resolver.validate_projection_ref("proj-restart", manifest)
        finally:
            c.close()


def teardown_function() -> None:
    if ROOT.exists():
        shutil.rmtree(ROOT, ignore_errors=True)
