"""SENSOR-B4-I05R2E — deterministic machine evidence for the fail-closed
public-API seal.

Generates THREE evidence matrices (no wall-clock content; injected clocks,
fixed identities, generation-twice byte-stability asserted):

- ``BLOC_04_I05R2_PUBLIC_API_MATRIX.json``: the seven public-API cases
  (construction gates, valid physical commit, lineage dependency gates,
  orphan lineage, full-dependency success);
- ``BLOC_04_I05R2_PHYSICAL_SCHEMA_MATRIX.json``: the eleven physical
  truth cases (exact schema control, native type/nullability/order/
  nested-child attacks, T0 value attacks, row-ordinal and row-lineage
  attacks);
- ``BLOC_04_I05R2_CRASH_BOUNDARY_MATRIX.json``: every catalog fault
  boundary with actual fsync-spy evidence (file fsyncs before fault,
  staging/final existence, success claimed, fragment visible after
  restart).
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

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
    ProjectionLineage,
    RawProjectionArtifact,
)
from crypto_sensor_fabric.storage.projection_lineage import (
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
    write_projection,
)

FIXED = datetime(2026, 9, 12, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"
ROOT = Path("C:/tmp_r2e_proj")
EVIDENCE_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "research" / "crypto_foundry" / "sensor_fabric" / "evidence" / "bloc_04"
)

NATIVE = pa.schema(
    [
        pa.field("price", pa.float64(), nullable=False),
        pa.field("qty", pa.int64(), nullable=True),
        pa.field("symbol", pa.string(), nullable=False),
    ]
)
FULL_SCHEMA = pa.schema(list(NATIVE) + list(T0_METADATA_SCHEMA))


def stable_evidence_bytes(payload: dict) -> bytes:
    """Canonical serializer (I05R4 §31) — no publication side effects."""
    return json.dumps(
        payload, sort_keys=True, ensure_ascii=False, indent=2
    ).encode("utf-8")


def _dump_stable(path: Path, payload: dict) -> bytes:
    raw = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, indent=2
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


def _err_name(exc: BaseException | None) -> str | None:
    if exc is None:
        return None
    return type(exc).__name__


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


class Stack:
    """Minimal real chain with INJECTED clocks (byte-stable evidence)."""

    def __init__(self, tmp_path: Path) -> None:
        if ROOT.exists():
            shutil.rmtree(ROOT)
        ROOT.mkdir(parents=True)
        self.root = ROOT
        self.t0a = tmp_path / "t0a"
        self.t0a.mkdir(parents=True, exist_ok=True)
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

    def reopen(self) -> "Stack":
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

    def definition(self) -> ProjectionSchemaDefinition:
        return ProjectionSchemaDefinition(
            projection_schema_id="r2e.market.projection",
            projection_schema_version="1.0.0",
            provider_native_schema=NATIVE,
        )

    def seed(self, data: bytes, acq_id: str) -> str:
        put = self.store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
        )
        self.blob_repo.append_metadata(put.blob)
        self.acq_repo.append_acquisition(_acq(acq_id, put.blob.blob_sha256))
        return put.blob.blob_sha256

    def commit_chain(
        self,
        projection_id: str,
        pairs: list[tuple[str, str]],
        *,
        rows: list[dict] | None = None,
        d: ProjectionSchemaDefinition | None = None,
    ) -> RawProjectionArtifact:
        d = d or self.definition()
        if not self.schemas.has(d.schema_key) if hasattr(
            self.schemas, "has"
        ) else True:
            try:
                self.schemas.resolve(d.schema_key)
            except Exception:
                self.schemas.register(d)
        sources = [s for s, _a in pairs]
        acq_ids = [a for _s, a in pairs]
        if rows is None:
            rows = [{"price": 1.0, "qty": 1, "symbol": "BTC-USDT"}]
        artifact, _p = write_projection(
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
                lineage_manifest_id=f"lm-{projection_id}",
                quality_flags=[],
                created_at=FIXED,
            )
        )
        self.lineage.commit(
            f"lm-{projection_id}",
            [
                ProjectionLineage(
                    lineage_manifest_id=f"lm-{projection_id}",
                    projection_id=projection_id,
                    source_blob_sha256=sha,
                    source_acquisition_id=acq_id,
                    source_order=order,
                )
                for order, (sha, acq_id) in enumerate(pairs)
            ],
        )
        return artifact


def _write_parquet(root: Path, uri: str, schema: pa.Schema, columns: dict) -> str:
    target = root / uri
    target.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table(columns, schema=schema), str(target))
    return sha256_file(str(target)).hex_digest


def _t0_row(projection_id: str, blob_sha: str, acq_id: str, n: int = 1, **ov):
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
    cols.update(ov)
    return cols


def _rewrite_committed_sha(root: Path, projection_id: str, new_sha: str) -> None:
    for base in (
        root / "catalogs" / "manifests" / "projections",
        root / "catalogs" / "manifests" / "projection_context",
    ):
        for fragment in base.glob("*.json"):
            payload = json.loads(fragment.read_text(encoding="utf-8"))
            if payload.get("projection_id") == projection_id:
                payload["projection_sha256"] = new_sha
                fragment.write_bytes(
                    json.dumps(
                        payload, sort_keys=True, ensure_ascii=False,
                        separators=(",", ":"),
                    ).encode("utf-8")
                )


class _FsyncSpy:
    """Counts real fsync operations during a catalog commit."""

    def __init__(self) -> None:
        self.file_fsyncs = 0
        self.dir_fsyncs = 0

    def __enter__(self) -> "_FsyncSpy":
        import crypto_sensor_fabric.storage.atomic as atomic
        import crypto_sensor_fabric.storage.json_catalog as jc

        self._real_file = atomic.fsync_file
        self._real_dir = atomic.fsync_directory

        def spy_file(path):
            self.file_fsyncs += 1
            return self._real_file(path)

        def spy_dir(path):
            self.dir_fsyncs += 1
            return self._real_dir(path)

        self._atomic = atomic
        self._jc = jc
        atomic.fsync_file = spy_file  # type: ignore[assignment]
        jc.fsync_file = spy_file  # type: ignore[assignment]
        atomic.fsync_directory = spy_dir  # type: ignore[assignment]
        jc.fsync_directory = spy_dir  # type: ignore[assignment]
        return self

    def __exit__(self, *exc) -> None:
        self._atomic.fsync_file = self._real_file  # type: ignore[assignment]
        self._jc.fsync_file = self._real_file  # type: ignore[assignment]
        self._atomic.fsync_directory = self._real_dir  # type: ignore[assignment]
        self._jc.fsync_directory = self._real_dir  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Matrix 1 — public API
# ---------------------------------------------------------------------------


def _public_api_matrix(work: Path) -> dict:
    cases: list[dict] = []

    def record(case, ok, error, detail=None):
        cases.append(
            {
                "case": case,
                "allowed": ok,
                "expected_error": error,
                "detail": detail,
            }
        )

    # artifact_no_root
    try:
        ProjectionArtifactRepository(work / "no_root")  # type: ignore[call-arg]
        record("artifact_no_root", True, None)
    except Exception as exc:  # noqa: BLE001
        record("artifact_no_root", False, _err_name(exc), "construction refused")

    # artifact_no_schema_registry
    try:
        ProjectionArtifactRepository(  # type: ignore[call-arg]
            work / "no_reg", projection_root=work / "t0"
        )
        record("artifact_no_schema_registry", True, None)
    except Exception as exc:  # noqa: BLE001
        record(
            "artifact_no_schema_registry", False, _err_name(exc),
            "construction refused",
        )

    # artifact_valid_physical
    s = Stack(work / "a")
    try:
        d = s.definition()
        s.schemas.register(d)
        sha = s.seed(b'{"api": 1}', "acq-api")
        artifact, _p = write_projection(
            root=s.root,
            rows=[{"price": 1.0, "qty": 1, "symbol": "BTC-USDT"}],
            schema_definition=d,
            schema_registry=s.schemas,
            projection_id="proj-api",
            source_blob_sha256=[sha],
            acquisition_ids=["acq-api"],
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
        s.artifacts.commit(artifact)
        record("artifact_valid_physical", True, None, "VALID earned by proof")
    except Exception as exc:  # noqa: BLE001
        record("artifact_valid_physical", False, _err_name(exc))
    finally:
        s.close()

    # lineage_no_artifact_repo
    try:
        ProjectionLineageRepository(  # type: ignore[call-arg]
            work / "lin_a",
            blob_store=object(),
            blob_metadata_repository=object(),
            acquisition_repository=object(),
            context_repository=object(),
        )
        record("lineage_no_artifact_repo", True, None)
    except Exception as exc:  # noqa: BLE001
        record("lineage_no_artifact_repo", False, _err_name(exc))

    # lineage_no_context_repo
    try:
        ProjectionLineageRepository(  # type: ignore[call-arg]
            work / "lin_b",
            blob_store=object(),
            blob_metadata_repository=object(),
            acquisition_repository=object(),
            artifact_repository=object(),
        )
        record("lineage_no_context_repo", True, None)
    except Exception as exc:  # noqa: BLE001
        record("lineage_no_context_repo", False, _err_name(exc))

    # lineage_nonexistent_projection
    s = Stack(work / "c")
    try:
        sha = s.seed(b'{"api": 2}', "acq-api2")
        try:
            s.lineage.commit(
                "lm-ghost",
                [
                    ProjectionLineage(
                        lineage_manifest_id="lm-ghost",
                        projection_id="proj-ghost",
                        source_blob_sha256=sha,
                        source_acquisition_id="acq-api2",
                        source_order=0,
                    )
                ],
            )
            record("lineage_nonexistent_projection", True, None)
        except Exception as exc:  # noqa: BLE001
            record("lineage_nonexistent_projection", False, _err_name(exc))
    finally:
        s.close()

    # lineage_valid_full_dependencies
    s = Stack(work / "d")
    try:
        sha = s.seed(b'{"api": 3}', "acq-api3")
        s.commit_chain("proj-api3", [(sha, "acq-api3")])
        record("lineage_valid_full_dependencies", True, None)
    except Exception as exc:  # noqa: BLE001
        record("lineage_valid_full_dependencies", False, _err_name(exc))
    finally:
        s.close()

    return {
        "matrix": "BLOC_04_I05R2_PUBLIC_API_MATRIX",
        "checkpoint": "SENSOR-B4-I05R2",
        "clock": "injected-fixed",
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Matrix 2 — physical schema / T0 value truth
# ---------------------------------------------------------------------------


def _physical_schema_matrix(work: Path) -> dict:
    cases: list[dict] = []

    def record(case, rejected, error, gate):
        cases.append(
            {
                "case": case,
                "rejected": rejected,
                "expected_error": error,
                "gate": gate,
            }
        )

    def isolated_repo(tmp: Path):
        t0 = tmp / "t0"
        t0.mkdir(parents=True)
        schemas = ProjectionSchemaRegistry(tmp / "schemas")
        schemas.register(
            ProjectionSchemaDefinition(
                projection_schema_id="r2e.market.projection",
                projection_schema_version="1.0.0",
                provider_native_schema=NATIVE,
            )
        )
        repo = ProjectionArtifactRepository(
            tmp / "artifacts", projection_root=t0, schema_registry=schemas
        )
        return repo, t0, schemas

    def artifact_for(sha: str, uri: str, row_count: int = 1):
        return RawProjectionArtifact(
            projection_id="proj-atk",
            source_blob_sha256=["a" * 64],
            projection_schema_id="r2e.market.projection",
            projection_schema_version="1.0.0",
            parser_version="1.0.0",
            row_count=row_count,
            partition_key="kraken/futures/BTC-USDT/2026-01-15",
            projection_uri=uri,
            projection_sha256=sha,
        )

    def artifact_commit_case(case, schema, columns, row_count=1, gate="exact_schema"):
        tmp = work / case
        repo, t0, _s = isolated_repo(tmp)
        try:
            uri = "projections/atk/part-00000.parquet"
            sha = _write_parquet(t0, uri, schema, columns)
            try:
                repo.commit(artifact_for(sha, uri, row_count))
                record(case, False, None, gate)
            except Exception as exc:  # noqa: BLE001
                record(case, True, _err_name(exc), gate)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # exact_schema — the control
    cols = {"price": [1.0], "qty": [1], "symbol": ["BTC-USDT"]}
    cols.update(_t0_row("proj-atk", "a" * 64, "acq-atk"))
    artifact_commit_case("exact_schema", FULL_SCHEMA, cols)

    # wrong_native_type
    wrong = pa.schema(
        [
            pa.field("price", pa.string(), nullable=False),
            pa.field("qty", pa.int64(), nullable=True),
            pa.field("symbol", pa.string(), nullable=False),
        ]
        + list(T0_METADATA_SCHEMA)
    )
    cols = {"price": ["1.0"], "qty": [1], "symbol": ["BTC-USDT"]}
    cols.update(_t0_row("proj-atk", "a" * 64, "acq-atk"))
    artifact_commit_case("wrong_native_type", wrong, cols, gate="native_type")

    # wrong_native_nullability
    wrong = pa.schema(
        [
            pa.field("price", pa.float64(), nullable=True),
            pa.field("qty", pa.int64(), nullable=True),
            pa.field("symbol", pa.string(), nullable=False),
        ]
        + list(T0_METADATA_SCHEMA)
    )
    cols = {"price": [1.0], "qty": [1], "symbol": ["BTC-USDT"]}
    cols.update(_t0_row("proj-atk", "a" * 64, "acq-atk"))
    artifact_commit_case("wrong_native_nullability", wrong, cols, gate="nullability")

    # wrong_native_order
    wrong = pa.schema(
        [
            pa.field("qty", pa.int64(), nullable=True),
            pa.field("price", pa.float64(), nullable=False),
            pa.field("symbol", pa.string(), nullable=False),
        ]
        + list(T0_METADATA_SCHEMA)
    )
    cols = {"qty": [1], "price": [1.0], "symbol": ["BTC-USDT"]}
    cols.update(_t0_row("proj-atk", "a" * 64, "acq-atk"))
    artifact_commit_case("wrong_native_order", wrong, cols, gate="field_order")

    # wrong_nested_type (struct child nullability drift)
    tmp = work / "wrong_nested_type"
    repo, t0, schemas = isolated_repo(tmp)
    try:
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
        schemas.register(
            ProjectionSchemaDefinition(
                projection_schema_id="r2e.nested.projection",
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
        uri = "projections/atk/part-00000.parquet"
        cols = {"level": [{"price": 1.0, "qty": 1}], "symbol": ["BTC-USDT"]}
        cols.update(_t0_row("proj-atk", "a" * 64, "acq-atk"))
        sha = _write_parquet(t0, uri, wrong, cols)
        artifact = artifact_for(sha, uri).model_copy(
            update={"projection_schema_id": "r2e.nested.projection"}
        )
        try:
            repo.commit(artifact)
            record("wrong_nested_type", False, None, "nested_child")
        except Exception as exc:  # noqa: BLE001
            record("wrong_nested_type", True, _err_name(exc), "nested_child")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    # Resolver-side value/lineage attacks: honest chain, mutated file,
    # SHA forged into catalogs, repositories reopened.
    def resolver_case(case, columns, n, match=None):
        s = Stack(work / case)
        try:
            d = s.definition()
            sha = s.seed(b'{"r2e": 1}', "acq-r2e")
            artifact = s.commit_chain("proj-r2e", [(sha, "acq-r2e")], d=d)
            if n == 1:
                base = {"price": [1.0], "qty": [1], "symbol": ["BTC-USDT"]}
            else:
                base = {
                    "price": [1.0, 2.0],
                    "qty": [1, 2],
                    "symbol": ["BTC-USDT"] * 2,
                }
            base.update(columns)
            target = s.root / artifact.projection_uri
            pq.write_table(pa.table(base, schema=FULL_SCHEMA), str(target))
            new_sha = sha256_file(str(target)).hex_digest
            _rewrite_committed_sha(s.root, "proj-r2e", new_sha)
            s.reopen()
            from crypto_sensor_fabric.storage.models import PartitionManifest

            manifest = PartitionManifest(
                partition_manifest_id="pm-r2e",
                partition_key="kraken/futures/BTC-USDT/2026-01-15",
                provider="kraken",
                venue="futures",
                sensor_family="MECHANICAL_TRADE",
                native_instrument="BTC-USDT",
                source_granularity="1m",
                logical_date_start=datetime(2026, 1, 15, tzinfo=UTC),
                logical_date_end=datetime(2026, 1, 15, 23, 59, 59, tzinfo=UTC),
                blob_refs=[sha],
                projection_refs=["proj-r2e"],
                created_at=FIXED,
            )
            try:
                s.resolver.validate_projection_ref("proj-r2e", manifest)
                record(case, False, None, "resolver")
            except Exception as exc:  # noqa: BLE001
                record(case, True, _err_name(exc), "resolver")
        finally:
            s.close()

    resolver_case(
        "wrong_t0_provider",
        _t0_row("proj-r2e", "REPLACED", "acq-r2e", _t0_provider=["gate"]),
        1,
    )
    resolver_case(
        "wrong_t0_parser",
        _t0_row("proj-r2e", "REPLACED", "acq-r2e", _t0_parser_version=["9.9.9"]),
        1,
    )
    resolver_case(
        "wrong_projection_id",
        _t0_row("proj-evil", "REPLACED", "acq-r2e"),
        1,
    )
    bad_ord = _t0_row("proj-r2e", "REPLACED", "acq-r2e", n=2)
    bad_ord["_t0_row_ordinal"] = [0, 2]
    resolver_case("bad_row_ordinal", bad_ord, 2)
    resolver_case(
        "bad_single_source_lineage",
        _t0_row("proj-r2e", "REPLACED", "acq-decoy"),
        1,
    )
    multi = _t0_row("proj-r2e", "REPLACED", "acq-r2e", n=2)
    multi["_t0_source_blob_sha256"] = ["c" * 64, None]
    multi["_t0_acquisition_id"] = ["acq-undeclared", None]
    resolver_case("bad_multi_source_pair", multi, 2)

    return {
        "matrix": "BLOC_04_I05R2_PHYSICAL_SCHEMA_MATRIX",
        "checkpoint": "SENSOR-B4-I05R2",
        "clock": "injected-fixed",
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Matrix 3 — crash boundary truth (fsync-spy evidence)
# ---------------------------------------------------------------------------


def _crash_boundary_matrix(work: Path) -> dict:
    cases: list[dict] = []
    boundaries = list(CatalogFaultPoint)

    for boundary in boundaries:
        root = work / boundary.value / "cat"
        hook = CatalogFaultHook(boundary)
        with _FsyncSpy() as spy:
            cat = DurableJsonCatalog(
                root, logical_id_field="id", fault_hooks=hook
            )
            success = True
            error = None
            try:
                cat.commit("obj", {"id": "obj", "v": 1})
            except FaultError as exc:
                success = False
                error = type(exc).__name__
            except Exception as exc:  # noqa: BLE001
                success = False
                error = type(exc).__name__
            final_exists = cat._physical_path("obj").exists()
            staging_dir_exists = (root / "_staging").exists()
            success_claimed = success and cat.has("obj")
            # Restart: a fresh instance sees committed fragments only.
            reloaded = DurableJsonCatalog(root, logical_id_field="id")
            visible_after_restart = reloaded.has("obj")
        cases.append(
            {
                "boundary": boundary.value,
                "file_fsyncs_before_fault": spy.file_fsyncs,
                "dir_fsyncs_before_fault": spy.dir_fsyncs,
                "staging_dir_exists_after": staging_dir_exists,
                "final_exists_after": final_exists,
                "success_returned": success_claimed,
                "error": error,
                "fragment_visible_after_restart": visible_after_restart,
            }
        )

    # Unfaulted control: exactly ONE file fsync, full durability.
    root = work / "unfaulted" / "cat"
    with _FsyncSpy() as spy:
        cat = DurableJsonCatalog(root, logical_id_field="id")
        cat.commit("obj", {"id": "obj", "v": 1})
        visible = cat.has("obj")
    cases.append(
        {
            "boundary": "NONE_UNFAULTED_CONTROL",
            "file_fsyncs_before_fault": spy.file_fsyncs,
            "dir_fsyncs_before_fault": spy.dir_fsyncs,
            "staging_dir_exists_after": (root / "_staging").exists(),
            "final_exists_after": cat._physical_path("obj").exists(),
            "success_returned": visible,
            "error": None,
            "fragment_visible_after_restart": DurableJsonCatalog(
                root, logical_id_field="id"
            ).has("obj"),
        }
    )

    return {
        "matrix": "BLOC_04_I05R2_CRASH_BOUNDARY_MATRIX",
        "checkpoint": "SENSOR-B4-I05R2",
        "clock": "injected-fixed",
        "fsync_proof": "spy-counted real os-level fsync operations",
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Tests: generate twice, assert byte stability
# ---------------------------------------------------------------------------


class TestPublicApiMatrix:
    def test_deterministic_generation(self, tmp_path: Path) -> None:
        first = _public_api_matrix(tmp_path / "a")
        second = _public_api_matrix(tmp_path / "b")
        raw = stable_evidence_bytes(first)
        assert raw == stable_evidence_bytes(second)
        # I05R4 §10: READ-ONLY — compare to the committed artifact bytes.
        assert raw == (
            EVIDENCE_DIR / "BLOC_04_I05R2_PUBLIC_API_MATRIX.json"
        ).read_bytes()

    def test_required_cases_present(self, tmp_path: Path) -> None:
        matrix = _public_api_matrix(tmp_path)
        names = {c["case"] for c in matrix["cases"]}
        assert {
            "artifact_no_root",
            "artifact_no_schema_registry",
            "artifact_valid_physical",
            "lineage_no_artifact_repo",
            "lineage_no_context_repo",
            "lineage_nonexistent_projection",
            "lineage_valid_full_dependencies",
        } <= names


class TestPhysicalSchemaMatrix:
    def test_deterministic_generation(self, tmp_path: Path) -> None:
        first = _physical_schema_matrix(tmp_path / "a")
        second = _physical_schema_matrix(tmp_path / "b")
        raw = stable_evidence_bytes(first)
        assert raw == stable_evidence_bytes(second)
        assert raw == (
            EVIDENCE_DIR / "BLOC_04_I05R2_PHYSICAL_SCHEMA_MATRIX.json"
        ).read_bytes()

    def test_required_cases_present(self, tmp_path: Path) -> None:
        matrix = _physical_schema_matrix(tmp_path)
        names = {c["case"] for c in matrix["cases"]}
        assert {
            "exact_schema",
            "wrong_native_type",
            "wrong_native_nullability",
            "wrong_native_order",
            "wrong_nested_type",
            "wrong_t0_provider",
            "wrong_t0_parser",
            "wrong_projection_id",
            "bad_row_ordinal",
            "bad_single_source_lineage",
            "bad_multi_source_pair",
        } <= names


class TestCrashBoundaryMatrix:
    def test_deterministic_generation(self, tmp_path: Path) -> None:
        first = _crash_boundary_matrix(tmp_path / "a")
        second = _crash_boundary_matrix(tmp_path / "b")
        raw = stable_evidence_bytes(first)
        assert raw == stable_evidence_bytes(second)
        assert raw == (
            EVIDENCE_DIR / "BLOC_04_I05R2_CRASH_BOUNDARY_MATRIX.json"
        ).read_bytes()

    def test_after_write_boundary_proves_zero_file_fsyncs(
        self, tmp_path: Path
    ) -> None:
        matrix = _crash_boundary_matrix(tmp_path)
        by_name = {c["boundary"]: c for c in matrix["cases"]}
        after_write = by_name["AFTER_WRITE_BEFORE_FSYNC"]
        assert after_write["file_fsyncs_before_fault"] == 0
        assert after_write["success_returned"] is False
        assert after_write["final_exists_after"] is False
        control = by_name["NONE_UNFAULTED_CONTROL"]
        assert control["file_fsyncs_before_fault"] == 1
        assert control["success_returned"] is True


def teardown_function() -> None:
    if ROOT.exists():
        shutil.rmtree(ROOT, ignore_errors=True)
