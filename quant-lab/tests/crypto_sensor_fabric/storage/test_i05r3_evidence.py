"""SENSOR-B4-I05R3D — deterministic machine evidence for the lineage-identity
and time-truth seal.

Generates TWO evidence matrices (no wall-clock content; injected clocks,
fixed identities, generation-twice byte-stability asserted):

- ``BLOC_04_I05R3_LINEAGE_IDENTITY_MATRIX.json``: the seven lineage-identity
  cases (context binding exact, alternate lmid rejected, duplicate
  projection ownership on restart, idempotent healthy re-commit and the
  three idempotent-after-corruption failures);
- ``BLOC_04_I05R3_TIME_CONTRACT_MATRIX.json``: the eight time-contract
  cases (five naive rejections, offset-aware UTC normalization, persisted
  naive reload failure, inverted provider range).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pyarrow as pa

from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
from crypto_sensor_fabric.storage.catalog import (
    AcquisitionRepository,
    BlobMetadataRepository,
)
from crypto_sensor_fabric.storage.enums import StorageEncoding
from crypto_sensor_fabric.storage.json_catalog import (
    DurableJsonCatalog,
    catalog_physical_key,
)
from crypto_sensor_fabric.storage.models import (
    AcquisitionRecord,
    ProjectionLineage,
)
from crypto_sensor_fabric.storage.projection_lineage import (
    ProjectionLineageRepository,
)
from crypto_sensor_fabric.storage.projection_schema import (
    ProjectionSchemaDefinition,
    ProjectionSchemaRegistry,
)
from crypto_sensor_fabric.storage.projections import (
    ProjectionArtifactRepository,
    ProjectionCatalogRecord,
    ProjectionContextRepository,
    write_projection,
)

FIXED = datetime(2026, 9, 12, 12, 0, 0, tzinfo=UTC)
UTC_M5 = timezone(timedelta(hours=-5))
MEDIA = "application/json"
EVIDENCE_DIR = (
    Path(__file__).parent.parent.parent.parent
    / "research" / "crypto_foundry" / "sensor_fabric" / "evidence" / "bloc_04"
)


def stable_evidence_bytes(payload: dict) -> bytes:
    """Canonical serializer for deterministic evidence payloads (I05R4 §31)."""
    return json.dumps(
        payload, sort_keys=True, ensure_ascii=False, indent=2
    ).encode("utf-8")


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
    """Minimal real chain with INJECTED clocks (byte-stable evidence).

    I05R4 §16: the T0B catalog root is derived from the pytest tmp_path —
    no global workstation path.
    """

    def __init__(self, tmp_path: Path) -> None:
        self.root = tmp_path / "t0b"
        self.root.mkdir(parents=True, exist_ok=True)
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
        return self

    def close(self) -> None:  # pragma: no cover - tmp_path cleanup is automatic
        pass

    def definition(self) -> ProjectionSchemaDefinition:
        return ProjectionSchemaDefinition(
            projection_schema_id="r3e.market.projection",
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

    def commit_projection(
        self,
        projection_id: str,
        pairs: list[tuple[str, str]],
        *,
        lineage_manifest_id: str | None = None,
    ):

        d = self.definition()
        try:
            self.schemas.resolve(d.schema_key)
        except Exception:
            self.schemas.register(d)
        if lineage_manifest_id is None:
            lineage_manifest_id = f"lm-{projection_id}"
        artifact, _p = write_projection(
            root=self.root,
            rows=[{"price": 1.0, "qty": 1, "symbol": "BTC-USDT"}],
            schema_definition=d,
            schema_registry=self.schemas,
            projection_id=projection_id,
            source_blob_sha256=[s for s, _a in pairs],
            acquisition_ids=[a for _s, a in pairs],
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
                lineage_manifest_id=lineage_manifest_id,
                quality_flags=[],
                created_at=FIXED,
            )
        )
        return artifact


def _lineage(lmid: str, pid: str, sha: str, acq_id: str, order: int = 0):
    return ProjectionLineage(
        lineage_manifest_id=lmid,
        projection_id=pid,
        source_blob_sha256=sha,
        source_acquisition_id=acq_id,
        source_order=order,
    )


def _build_lineage_identity_matrix(tmp_path: Path) -> dict:
    """I05R3 §25 — BLOC_04_I05R3_LINEAGE_IDENTITY_MATRIX.json cases."""
    cases: list[dict] = []

    # 1. context_lmid_exact: commit with the context's lmid succeeds.
    s = Stack(tmp_path / "a")
    try:
        sha = s.seed(b'{"rows": [1]}', "acq-li1")
        s.commit_projection(
            "proj-li1", [(sha, "acq-li1")], lineage_manifest_id="lm-li1"
        )
        raised = None
        try:
            s.lineage.commit("lm-li1", [_lineage("lm-li1", "proj-li1", sha, "acq-li1")])
        except Exception as exc:  # noqa: BLE001
            raised = exc
        cases.append({
            "case": "context_lmid_exact",
            "expected": "commit_succeeds",
            "observed_error": _err_name(raised),
            "durable": s.lineage.has("lm-li1"),
        })
    finally:
        s.close()

    # 2. alternate_lmid_same_projection: L2 for a context-bound P rejected.
    s = Stack(tmp_path / "b")
    try:
        sha = s.seed(b'{"rows": [2]}', "acq-li2")
        s.commit_projection(
            "proj-li2", [(sha, "acq-li2")], lineage_manifest_id="lm-auth2"
        )
        raised = None
        try:
            s.lineage.commit(
                "lm-alt2", [_lineage("lm-alt2", "proj-li2", sha, "acq-li2")]
            )
        except Exception as exc:  # noqa: BLE001
            raised = exc
        frag = (
            s.root / "catalogs" / "manifests" / "projection_lineage"
            / catalog_physical_key("lm-alt2")
        )
        cases.append({
            "case": "alternate_lmid_same_projection",
            "expected_error": "LineageContextBindingConflict",
            "observed_error": _err_name(raised),
            "fragment_written": frag.exists(),
        })
    finally:
        s.close()

    # 3. duplicate_lineage_projection_restart: two committed manifests
    #    claiming one projection fail closed on repository reload.
    s = Stack(tmp_path / "c")
    try:
        sha = s.seed(b'{"rows": [3]}', "acq-li3")
        s.commit_projection(
            "proj-li3", [(sha, "acq-li3")], lineage_manifest_id="lm-li3a"
        )
        s.lineage.commit(
            "lm-li3a", [_lineage("lm-li3a", "proj-li3", sha, "acq-li3")]
        )
        # Tamper via the raw catalog (legacy/tampered disk simulation).
        raw = DurableJsonCatalog(
            s.root / "catalogs" / "manifests" / "projection_lineage",
            logical_id_field="lineage_manifest_id",
        )
        raw.commit(
            "lm-li3b",
            {
                "record_type": "projection_lineage_manifest",
                "lineage_manifest_id": "lm-li3b",
                "projection_id": "proj-li3",
                "entries": [
                    json.loads(
                        _lineage("lm-li3b", "proj-li3", sha, "acq-li3").model_dump_json()
                    )
                ],
            },
        )
        raised = None
        try:
            s.reopen()
        except Exception as exc:  # noqa: BLE001
            raised = exc
        cases.append({
            "case": "duplicate_lineage_projection_restart",
            "expected_error": "LineageProjectionIdentityConflict",
            "observed_error": _err_name(raised),
        })
    finally:
        s.close()

    # 4. idempotent_healthy: identical re-commit over an intact chain.
    s = Stack(tmp_path / "d")
    try:
        sha = s.seed(b'{"rows": [4]}', "acq-li4")
        s.commit_projection(
            "proj-li4", [(sha, "acq-li4")], lineage_manifest_id="lm-li4"
        )
        entries = [_lineage("lm-li4", "proj-li4", sha, "acq-li4")]
        s.lineage.commit("lm-li4", entries)
        raised = None
        try:
            s.lineage.commit("lm-li4", entries)
        except Exception as exc:  # noqa: BLE001
            raised = exc
        cases.append({
            "case": "idempotent_healthy",
            "expected": "recommit_succeeds_after_full_revalidation",
            "observed_error": _err_name(raised),
        })
    finally:
        s.close()

    # 5. idempotent_source_corrupt: corrupt the T0A source blob, re-commit.
    s = Stack(tmp_path / "e")
    try:
        sha = s.seed(b'{"rows": [5]}', "acq-li5")
        s.commit_projection(
            "proj-li5", [(sha, "acq-li5")], lineage_manifest_id="lm-li5"
        )
        entries = [_lineage("lm-li5", "proj-li5", sha, "acq-li5")]
        s.lineage.commit("lm-li5", entries)
        from crypto_sensor_fabric.storage.paths import blob_object_key

        metas = s.blob_repo.get_blob_metadata(sha)
        blob_path = s.t0a / blob_object_key(
            metas[0].blob_sha256, metas[0].storage_encoding
        )
        blob_path.write_bytes(b"CORRUPTED")
        raised = None
        try:
            s.lineage.commit("lm-li5", entries)
        except Exception as exc:  # noqa: BLE001
            raised = exc
        cases.append({
            "case": "idempotent_source_corrupt",
            "expected": "recommit_fails_no_stale_cache_success",
            "observed_error": _err_name(raised),
            "historical_lineage_durable": s.lineage.get("lm-li5") is not None,
        })
    finally:
        s.close()

    # 6. idempotent_context_missing: remove the context fragment, restart,
    #    re-commit -> fail closed.
    s = Stack(tmp_path / "f")
    try:
        sha = s.seed(b'{"rows": [6]}', "acq-li6")
        s.commit_projection(
            "proj-li6", [(sha, "acq-li6")], lineage_manifest_id="lm-li6"
        )
        entries = [_lineage("lm-li6", "proj-li6", sha, "acq-li6")]
        s.lineage.commit("lm-li6", entries)
        for frag in (s.root / "catalogs" / "manifests" / "projection_context").glob(
            "*.json"
        ):
            frag.unlink()
        s.reopen()
        raised = None
        try:
            s.lineage.commit("lm-li6", entries)
        except Exception as exc:  # noqa: BLE001
            raised = exc
        cases.append({
            "case": "idempotent_context_missing",
            "expected_error": "ProjectionContextMissing",
            "observed_error": _err_name(raised),
        })
    finally:
        s.close()

    # 7. idempotent_artifact_corrupt: corrupt the physical T0B, re-commit.
    s = Stack(tmp_path / "g")
    try:
        sha = s.seed(b'{"rows": [7]}', "acq-li7")
        artifact = s.commit_projection(
            "proj-li7", [(sha, "acq-li7")], lineage_manifest_id="lm-li7"
        )
        entries = [_lineage("lm-li7", "proj-li7", sha, "acq-li7")]
        s.lineage.commit("lm-li7", entries)
        physical = s.root / artifact.projection_uri
        physical.write_bytes(b"CORRUPTED-T0B")
        raised = None
        try:
            s.lineage.commit("lm-li7", entries)
        except Exception as exc:  # noqa: BLE001
            raised = exc
        cases.append({
            "case": "idempotent_artifact_corrupt",
            "expected": "recommit_fails_via_artifact_verification",
            "observed_error": _err_name(raised),
        })
    finally:
        s.close()

    return {
        "matrix": "BLOC_04_I05R3_LINEAGE_IDENTITY_MATRIX",
        "checkpoint": "SENSOR-B4-I05R3",
        "generated_from_fixture": "deterministic (injected clock, fixed ids)",
        "cases": cases,
    }


def _time_record(**overrides: object) -> ProjectionCatalogRecord:
    base: dict[str, object] = {
        "projection_id": "proj-time",
        "provider": "kraken",
        "venue": "futures",
        "sensor_family": "MECHANICAL_TRADE",
        "native_instrument": "BTC-USDT",
        "source_granularity": "1m",
        "partition_key": "kraken/futures/BTC-USDT/2026-01-15",
        "logical_date_start": datetime(2026, 1, 15, tzinfo=UTC),
        "logical_date_end": datetime(2026, 1, 15, 23, 59, 59, tzinfo=UTC),
        "projection_schema_id": "schema.x",
        "projection_schema_version": "1.0.0",
        "schema_key": "k" * 64,
        "schema_fingerprint": "f" * 64,
        "parser_version": "1.0.0",
        "projection_uri": "projections/part-0.parquet",
        "projection_sha256": "a" * 64,
        "row_count": 1,
        "min_provider_time": None,
        "max_provider_time": None,
        "lineage_manifest_id": "lm-time",
        "quality_flags": [],
        "created_at": datetime(2026, 1, 16, tzinfo=UTC),
    }
    base.update(overrides)
    return ProjectionCatalogRecord(**base)  # type: ignore[arg-type]


def _build_time_contract_matrix() -> dict:
    """I05R3 §25 — BLOC_04_I05R3_TIME_CONTRACT_MATRIX.json cases."""
    cases: list[dict] = []

    def naive_case(name: str, field: str) -> None:
        raised = None
        try:
            if field == "logical_date_start":
                _time_record(logical_date_start=datetime(2026, 1, 15))
            elif field == "logical_date_end":
                _time_record(logical_date_end=datetime(2026, 1, 15, 23, 59, 59))
            elif field == "min_provider_time":
                _time_record(
                    min_provider_time=datetime(2026, 1, 15),
                    max_provider_time=datetime(2026, 1, 15, 23, tzinfo=UTC),
                )
            elif field == "max_provider_time":
                _time_record(
                    min_provider_time=datetime(2026, 1, 15, tzinfo=UTC),
                    max_provider_time=datetime(2026, 1, 15, 23),
                )
            else:
                _time_record(created_at=datetime(2026, 1, 16))
        except Exception as exc:  # noqa: BLE001
            raised = exc
        cases.append({
            "case": name,
            "expected_error": "ProjectionPreconditionError",
            "observed_error": _err_name(raised),
        })

    naive_case("naive_logical_start", "logical_date_start")
    naive_case("naive_logical_end", "logical_date_end")
    naive_case("naive_min_provider_time", "min_provider_time")
    naive_case("naive_max_provider_time", "max_provider_time")
    naive_case("naive_created_at", "created_at")

    # offset_aware_normalized: -05:00 input serializes as UTC.
    raised = None
    serialized = None
    try:
        serialized = _time_record(
            logical_date_start=datetime(2026, 1, 1, 12, tzinfo=UTC_M5)
        ).to_dict()["logical_date_start"]
    except Exception as exc:  # noqa: BLE001
        raised = exc
    cases.append({
        "case": "offset_aware_normalized",
        "expected": "2026-01-01T17:00:00+00:00",
        "observed": serialized,
        "observed_error": _err_name(raised),
    })

    # persisted_naive_reload: naive fragment string fails from_dict.
    raised = None
    payload = _time_record().to_dict()
    payload["logical_date_start"] = "2026-01-15T00:00:00"
    try:
        ProjectionCatalogRecord.from_dict(payload)
    except Exception as exc:  # noqa: BLE001
        raised = exc
    cases.append({
        "case": "persisted_naive_reload",
        "expected_error": "ProjectionArtifactCatalogCorrupt",
        "observed_error": _err_name(raised),
    })

    # inverted_provider_range: max < min fails when both present.
    raised = None
    try:
        _time_record(
            min_provider_time=datetime(2026, 1, 15, 12, tzinfo=UTC),
            max_provider_time=datetime(2026, 1, 15, 11, tzinfo=UTC),
        )
    except Exception as exc:  # noqa: BLE001
        raised = exc
    cases.append({
        "case": "inverted_provider_range",
        "expected_error": "ProjectionPreconditionError",
        "observed_error": _err_name(raised),
    })

    return {
        "matrix": "BLOC_04_I05R3_TIME_CONTRACT_MATRIX",
        "checkpoint": "SENSOR-B4-I05R3",
        "generated_from_fixture": "deterministic (fixed ids, no wall clock)",
        "cases": cases,
    }


class TestI05R3Evidence:
    """I05R4 §10-§13: evidence tests are READ-ONLY.

    Generation happens in memory; canonical bytes are compared against the
    COMMITTED evidence file.  No write to EVIDENCE_DIR ever occurs from a
    test — a future behavior change that alters matrix output FAILS here
    instead of silently rewriting governance history.
    """

    def test_lineage_identity_matrix_matches_committed(
        self, tmp_path: Path
    ) -> None:
        matrix = _build_lineage_identity_matrix(tmp_path)
        raw1 = stable_evidence_bytes(matrix)
        # Generation #2 (independent fixture tree) must be byte-identical.
        matrix2 = _build_lineage_identity_matrix(tmp_path / "second")
        assert raw1 == stable_evidence_bytes(matrix2)
        assert len(matrix["cases"]) == 7
        assert cases_ok(matrix["cases"])
        # §13: the regenerated bytes must equal the COMMITTED artifact.
        committed = (
            EVIDENCE_DIR / "BLOC_04_I05R3_LINEAGE_IDENTITY_MATRIX.json"
        ).read_bytes()
        assert raw1 == committed

    def test_time_contract_matrix_matches_committed(self, tmp_path: Path) -> None:
        matrix = _build_time_contract_matrix()
        raw1 = stable_evidence_bytes(matrix)
        matrix2 = _build_time_contract_matrix()
        assert raw1 == stable_evidence_bytes(matrix2)
        assert len(matrix["cases"]) == 8
        assert cases_ok(matrix["cases"])
        committed = (
            EVIDENCE_DIR / "BLOC_04_I05R3_TIME_CONTRACT_MATRIX.json"
        ).read_bytes()
        assert raw1 == committed

    def test_evidence_tree_not_written_by_generation(
        self, tmp_path: Path
    ) -> None:
        """§36.4/§36.7: running the generators leaves committed evidence
        bytes byte-identical — the read-only policy is itself proven."""
        before = {
            p.name: p.read_bytes()
            for p in EVIDENCE_DIR.glob("BLOC_04_I05R3_*.json")
        }
        _build_lineage_identity_matrix(tmp_path)
        _build_time_contract_matrix()
        after = {
            p.name: p.read_bytes()
            for p in EVIDENCE_DIR.glob("BLOC_04_I05R3_*.json")
        }
        assert before == after
        assert set(before) >= {
            "BLOC_04_I05R3_LINEAGE_IDENTITY_MATRIX.json",
            "BLOC_04_I05R3_TIME_CONTRACT_MATRIX.json",
        }


def cases_ok(cases: list[dict]) -> bool:
    """Every case must record the expected typed outcome (or success)."""
    for case in cases:
        expected_error = case.get("expected_error")
        observed = case.get("observed_error")
        if expected_error is not None and observed != expected_error:
            return False
        if "expected" in case and "observed" in case and case["observed"] != case["expected"]:
            return False
        # Positive requirements: truth must be durable where claimed.
        if "durable" in case and case["durable"] is not True:
            return False
        if "historical_lineage_durable" in case and case[
            "historical_lineage_durable"
        ] is not True:
            return False
        # Negative requirements: rejected lineage must never reach disk.
        if "fragment_written" in case and case["fragment_written"] is True:
            return False
    return True
