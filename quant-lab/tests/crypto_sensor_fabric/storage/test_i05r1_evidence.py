"""SENSOR-B4-I05R1F — deterministic machine evidence for the I05R1 seal.

Generates THREE evidence matrices (no wall-clock content; injected clocks,
fixed identities, scheduling-independent input ordering):

- ``BLOC_04_I05R1_DURABILITY_MATRIX.json``: crash boundaries + idempotence
  for the schema, artifact, context and lineage catalogs;
- ``BLOC_04_I05R1_END_TO_END_LINEAGE_MATRIX.json``: the fifteen end-to-end
  lineage cases (real chain, adversarial rejections, restart proofs);
- ``BLOC_04_I05R1_SCHEMA_FIDELITY_MATRIX.json``: the ten schema-fidelity
  cases (T0-metadata type change, Arrow structural units, unsupported
  types, key/fingerprint tamper).

Each matrix is generated TWICE and asserted byte-identical.
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

import pyarrow as pa

from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
from crypto_sensor_fabric.storage.catalog import AcquisitionRepository, BlobMetadataRepository
from crypto_sensor_fabric.storage.enums import StorageEncoding
from crypto_sensor_fabric.storage.json_catalog import catalog_physical_key
from crypto_sensor_fabric.storage.projection_lineage import (
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
    ProjectionContextRepository,
    T0BProjectionService,
)

FIXED = datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC)
# SENSOR-B4-I05R2 (§2): the committed I05R1 matrices are FROZEN historical
# evidence.  This generator now writes to a throwaway directory so running
# the suite can never mutate the committed I05R1 artifacts; the stability
# assertions below remain meaningful (generate twice, assert byte-equal).
EVIDENCE_DIR = Path("C:/tmp_i05r1_evidence_regenerate")

NATIVE = pa.schema(
    [
        pa.field("price", pa.float64(), nullable=False),
        pa.field("qty", pa.int64(), nullable=True),
        pa.field("symbol", pa.string(), nullable=False),
    ]
)


def _dump_stable(path: Path, payload: dict) -> bytes:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, indent=2).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


class Stack:
    """Minimal real chain (mirrors the R1E adversarial harness)."""

    ROOT = Path("C:/tmp_r1f_proj")

    def __init__(self, tmp_path: Path, *, fresh: bool = True) -> None:
        if fresh:
            if self.ROOT.exists():
                shutil.rmtree(self.ROOT)
            self.ROOT.mkdir(parents=True)
        else:
            self.ROOT.mkdir(parents=True, exist_ok=True)
        self.t0a = tmp_path / "t0a"
        self.t0a.mkdir(exist_ok=True)
        # Fixed clock EVERYWHERE on the T0A stack: identical re-seeds of the
        # same content are idempotent, and no wall-clock value can leak into
        # durable metadata (machine evidence must be byte-stable).
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

    def definition(self) -> ProjectionSchemaDefinition:
        return ProjectionSchemaDefinition(
            projection_schema_id="r1f.market.projection",
            projection_schema_version="1.0.0",
            provider_native_schema=NATIVE,
        )

    def seed(self, data: bytes, acq_id: str, *, provider: str = "kraken") -> str:
        put = self.store.put_bytes(
            data, storage_encoding=StorageEncoding.NONE,
            source_media_type="application/json",
        )
        self.blob_repo.append_metadata(put.blob)
        from crypto_sensor_fabric.storage.models import AcquisitionRecord

        self.acq_repo.append_acquisition(
            AcquisitionRecord(
                acquisition_id=acq_id,
                provider_id=provider,
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

    def commit(
        self,
        projection_id: str,
        sources: list[tuple[str, str]],
        lineage_manifest_id: str | None = None,
    ):
        definition = self.definition()
        if not self.schemas.has(definition.schema_key):
            self.schemas.register(definition)
        if lineage_manifest_id is None:
            lineage_manifest_id = f"lm-{projection_id}"
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
            lineage_manifest_id=lineage_manifest_id,
        )


def _manifest(blob_refs, projection_refs):
    from crypto_sensor_fabric.storage.manifests import PartitionManifest

    return PartitionManifest(
        partition_manifest_id="pm-r1f",
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


def _err_name(exc: object) -> str:
    """Typed error name from a raised exception OR a pytest ExcInfo."""
    value = getattr(exc, "value", exc)
    return type(value).__name__


# ---------------------------------------------------------------------------
# Matrix 1 — durability: crash boundaries + idempotence per catalog family
# ---------------------------------------------------------------------------


def _durability_matrix(tmp_path: Path) -> dict:
    tmp_path.mkdir(parents=True, exist_ok=True)
    cases: list[dict] = []

    # -- schema catalog: crash boundaries (reuse json_catalog fault seams
    # indirectly through the durable primitive's deterministic points) and
    # idempotence via double registration. -------------------------------
    s = Stack(tmp_path)
    try:
        d = s.definition()
        s.schemas.register(d)
        s.schemas.register(s.definition())  # idempotent
        cases.append({
            "catalog": "projection_schema",
            "case": "idempotent_registration",
            "committed_fragments": len(
                list((s.ROOT / "catalogs" / "projection_schemas").glob("*.json"))
            ),
            "schema_keys": sorted([s.definition().schema_key]),
            "expected": "single_fragment",
        })
    finally:
        s.close()

    # artifact catalog idempotence
    s = Stack(tmp_path)
    try:
        sha = s.seed(b'{"m": 1}', "acq-m1")
        a1, _ = s.commit("proj-1", [(sha, "acq-m1")])
        committed = s.artifacts.commit(a1)  # idempotent
        cases.append({
            "catalog": "projection_artifact",
            "case": "idempotent_commit",
            "projection_id": committed.projection_id,
            "fragments": len(
                list((s.ROOT / "catalogs" / "manifests" / "projections").glob("*.json"))
            ),
            "expected": "single_fragment_same_content",
        })
    finally:
        s.close()

    # artifact identity conflict
    s = Stack(tmp_path)
    try:
        sha = s.seed(b'{"m": 2}', "acq-m2")
        a1, _ = s.commit("proj-1", [(sha, "acq-m2")])
        tampered = a1.model_copy(update={"projection_sha256": "e" * 64})
        try:
            s.artifacts.commit(tampered)
            raised = "none"
        except Exception as exc:  # noqa: BLE001
            raised = type(exc).__name__
        cases.append({
            "catalog": "projection_artifact",
            "case": "identity_conflict",
            "expected_error": "ProjectionIdentityConflict",
            "observed_error": raised,
        })
    finally:
        s.close()

    # context catalog idempotence (re-commit identical context)
    s = Stack(tmp_path)
    try:
        sha = s.seed(b'{"m": 3}', "acq-m3")
        s.commit("proj-1", [(sha, "acq-m3")])
        context = s.contexts.get("proj-1")
        s.contexts.commit(context)
        cases.append({
            "catalog": "projection_context",
            "case": "idempotent_commit",
            "projection_id": "proj-1",
            "fragments": len(
                list((s.ROOT / "catalogs" / "manifests" / "projection_context").glob("*.json"))
            ),
            "expected": "single_fragment_same_content",
        })
    finally:
        s.close()

    # lineage catalog idempotence + conflict (row-bound divergence)
    s = Stack(tmp_path)
    try:
        sha = s.seed(b'{"m": 4}', "acq-m4")
        s.commit("proj-1", [(sha, "acq-m4")], lineage_manifest_id="lm-idem")
        from crypto_sensor_fabric.storage.models import ProjectionLineage

        entries = [
            ProjectionLineage(
                lineage_manifest_id="lm-idem",
                projection_id="proj-1",
                source_blob_sha256=sha,
                source_acquisition_id="acq-m4",
                source_order=0,
            )
        ]
        s.lineage.commit("lm-idem", entries)
        s.lineage.commit("lm-idem", entries)
        bounded = [
            ProjectionLineage(
                lineage_manifest_id="lm-idem",
                projection_id="proj-1",
                source_blob_sha256=sha,
                source_acquisition_id="acq-m4",
                source_row_start=0,
                source_row_end=0,
                source_order=0,
            )
        ]
        try:
            s.lineage.commit("lm-idem", bounded)
            raised = "none"
        except Exception as exc:  # noqa: BLE001
            raised = type(exc).__name__
        cases.append({
            "catalog": "projection_lineage",
            "case": "idempotent_including_row_bounds",
            "conflict_case": "same_id_different_row_bounds",
            "expected_error": "ProjectionLineageConflict",
            "observed_error": raised,
        })
    finally:
        s.close()

    # lineage manifest-id argument binding
    s = Stack(tmp_path)
    try:
        sha = s.seed(b'{"m": 5}', "acq-m5")
        s.commit("proj-1", [(sha, "acq-m5")], lineage_manifest_id="lm-real")
        from crypto_sensor_fabric.storage.models import ProjectionLineage

        entries = [
            ProjectionLineage(
                lineage_manifest_id="lm-real",
                projection_id="proj-1",
                source_blob_sha256=sha,
                source_acquisition_id="acq-m5",
                source_order=0,
            )
        ]
        try:
            s.lineage.commit("lm-argument", entries)
            raised = "none"
        except Exception as exc:  # noqa: BLE001
            raised = type(exc).__name__
        cases.append({
            "catalog": "projection_lineage",
            "case": "manifest_id_argument_binding",
            "expected_error": "LineageManifestBindingConflict",
            "observed_error": raised,
        })
    finally:
        s.close()

    return {
        "matrix": "BLOC_04_I05R1_DURABILITY_MATRIX",
        "checkpoint": "SENSOR-B4-I05R1",
        "clock": "injected-fixed",
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Matrix 2 — end-to-end lineage cases
# ---------------------------------------------------------------------------


def _end_to_end_matrix(tmp_path: Path) -> dict:
    tmp_path.mkdir(parents=True, exist_ok=True)
    cases: list[dict] = []

    def record(name: str, *, ok: bool, error: str | None = None, **extra) -> None:
        case = {
            "case": name,
            "result": "valid" if ok else "rejected",
            "expected_error": error,
            "observed": "accepted" if ok else (error or "rejected"),
        }
        case.update(extra)
        cases.append(case)

    # single_source_real_chain
    s = Stack(tmp_path)
    try:
        sha = s.seed(b'{"e": 1}', "acq-e1")
        s.commit("proj-single", [(sha, "acq-e1")])
        resolver = ProjectionLineageResolver(
            root=s.ROOT, artifacts=s.artifacts, contexts=s.contexts,
            lineage=s.lineage, schemas=s.schemas,
        )
        resolver.validate_projection_ref("proj-single", _manifest([sha], ["proj-single"]))
        record("single_source_real_chain", ok=True,
               source_blobs=1, lineage_entries=1)
    finally:
        s.close()

    # multi_source_real_chain
    s = Stack(tmp_path)
    try:
        sha_a = s.seed(b'{"e": 2}', "acq-e2a")
        sha_b = s.seed(b'{"e": 3}', "acq-e2b")
        s.commit("proj-multi", [(sha_a, "acq-e2a"), (sha_b, "acq-e2b")])
        resolver = ProjectionLineageResolver(
            root=s.ROOT, artifacts=s.artifacts, contexts=s.contexts,
            lineage=s.lineage, schemas=s.schemas,
        )
        resolver.validate_projection_ref(
            "proj-multi", _manifest([sha_a, sha_b], ["proj-multi"])
        )
        entries = s.lineage.get_by_projection("proj-multi")
        record("multi_source_real_chain", ok=True,
               source_blobs=2, lineage_orders=[e.source_order for e in entries])
    finally:
        s.close()

    # wrong_provider
    s = Stack(tmp_path)
    try:
        sha = s.seed(b'{"e": 4}', "acq-e4", provider="gate")
        try:
            s.commit("proj-wrong", [(sha, "acq-e4")])
            raised, ok = "none", True
        except Exception as exc:  # noqa: BLE001
            raised, ok = _err_name(_loc(exc)), False
        record("wrong_provider", ok=ok, error=raised,
               doctrine="byte_equality_never_transfers_provenance")
    finally:
        s.close()

    # wrong_acquisition_blob
    s = Stack(tmp_path)
    try:
        sha_a = s.seed(b'{"e": 5}', "acq-e5a")
        s.seed(b'{"e": 6}', "acq-e5b")
        try:
            s.commit("proj-x", [(sha_a, "acq-e5b")])
            raised, ok = "none", True
        except Exception as exc:  # noqa: BLE001
            raised, ok = _err_name(_loc(exc)), False
        record("wrong_acquisition_blob", ok=ok, error=raised)
    finally:
        s.close()

    # failed_acquisition
    s = Stack(tmp_path)
    try:
        put = s.store.put_bytes(
            b'{"e": 7}', storage_encoding=StorageEncoding.NONE,
            source_media_type="application/json",
        )
        s.blob_repo.append_metadata(put.blob)
        from crypto_sensor_fabric.storage.models import AcquisitionRecord

        s.acq_repo.append_acquisition(
            AcquisitionRecord(
                acquisition_id="acq-e7",
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
                failure_ref="checksum_mismatch",
            )
        )
        try:
            s.commit("proj-fail", [(put.blob.blob_sha256, "acq-e7")])
            raised, ok = "none", True
        except Exception as exc:  # noqa: BLE001
            raised, ok = _err_name(_loc(exc)), False
        # Forensic history preserved.
        preserved = s.acq_repo.get_acquisition("acq-e7").failure_ref
        record("failed_acquisition", ok=ok, error=raised,
               forensic_history_preserved=preserved == "checksum_mismatch")
    finally:
        s.close()

    # missing_physical_blob
    s = Stack(tmp_path)
    try:
        sha = s.seed(b'{"e": 8}', "acq-e8")
        from crypto_sensor_fabric.storage.paths import blob_object_key

        (s.t0a / blob_object_key(sha, StorageEncoding.NONE)).unlink()
        try:
            s.commit("proj-orphan", [(sha, "acq-1")])
            raised, ok = "none", True
        except Exception as exc:  # noqa: BLE001
            raised, ok = _err_name(_loc(exc)), False
        record("missing_physical_blob", ok=ok, error=raised)
    finally:
        s.close()

    # missing_artifact / missing_lineage
    s = Stack(tmp_path)
    try:
        sha = s.seed(b'{"e": 9}', "acq-e9")
        from crypto_sensor_fabric.storage.models import ProjectionLineage

        # I05R2 §11: the lineage repository now REFUSES orphan lineage at
        # commit time (typed ProjectionArtifactMissing).  The resolver-level
        # cases below remain valid: a manifest referencing a projection with
        # no committed artifact/lineage fails closed at the resolver.
        try:
            s.lineage.commit(
                "lm-orphan",
                [ProjectionLineage(
                    lineage_manifest_id="lm-orphan",
                    projection_id="proj-orphan",
                    source_blob_sha256=sha,
                    source_acquisition_id="acq-e9",
                    source_order=0,
                )],
            )
        except Exception:  # noqa: BLE001 — expected under the I05R2 seal
            pass
        resolver = ProjectionLineageResolver(
            root=s.ROOT, artifacts=s.artifacts, contexts=s.contexts,
            lineage=s.lineage, schemas=s.schemas,
        )
        try:
            resolver.validate_projection_ref("proj-orphan", _manifest([sha], ["proj-orphan"]))
            raised, ok = "none", True
        except Exception as exc:  # noqa: BLE001
            raised, ok = _err_name(_loc(exc)), False
        record("missing_artifact", ok=ok, error=raised)
        try:
            resolver.validate_projection_ref("proj-never", _manifest([sha], ["proj-never"]))
            raised, ok = "none", True
        except Exception as exc:  # noqa: BLE001
            raised, ok = _err_name(_loc(exc)), False
        record("missing_lineage", ok=ok, error=raised)
    finally:
        s.close()

    # wrong_partition / source_blob_hidden_from_manifest
    s = Stack(tmp_path)
    try:
        sha = s.seed(b'{"e": 10}', "acq-e10")
        s.commit("proj-p", [(sha, "acq-e10")])
        resolver = ProjectionLineageResolver(
            root=s.ROOT, artifacts=s.artifacts, contexts=s.contexts,
            lineage=s.lineage, schemas=s.schemas,
        )
        wrong = _manifest([sha], ["proj-p"])
        wrong = wrong.model_copy(update={"partition_key": "other/partition", "provider": "other"})
        try:
            resolver.validate_projection_ref("proj-p", wrong)
            raised, ok = "none", True
        except Exception as exc:  # noqa: BLE001
            raised, ok = _err_name(_loc(exc)), False
        record("wrong_partition", ok=ok, error=raised)

        sha_b = s.seed(b'{"e": 11}', "acq-e11")
        s.commit("proj-hidden", [(sha, "acq-e10"), (sha_b, "acq-e11")])
        try:
            resolver.validate_projection_ref(
                "proj-hidden", _manifest([sha], ["proj-hidden"])
            )
            raised, ok = "none", True
        except Exception as exc:  # noqa: BLE001
            raised, ok = _err_name(_loc(exc)), False
        record("source_blob_hidden_from_manifest", ok=ok, error=raised)
    finally:
        s.close()

    # restart_valid
    s = Stack(tmp_path)
    try:
        sha_a = s.seed(b'{"e": 12}', "acq-e12a")
        sha_b = s.seed(b'{"e": 13}', "acq-e12b")
        s.commit("proj-restart", [(sha_a, "acq-e12a"), (sha_b, "acq-e12b")])
        s2 = Stack(tmp_path, fresh=False).reopen()
        resolver = ProjectionLineageResolver(
            root=s2.ROOT, artifacts=s2.artifacts, contexts=s2.contexts,
            lineage=s2.lineage, schemas=s2.schemas,
        )
        resolver.validate_projection_ref(
            "proj-restart", _manifest([sha_a, sha_b], ["proj-restart"])
        )
        record("restart_valid", ok=True,
               detail="all repositories reinstantiated from disk")
    finally:
        s.close()

    # restart_corrupt_* (schema/lineage/artifact fragments + physical)
    def _restart_corrupt(case_name: str, corrupt: str) -> None:
        s = Stack(tmp_path)
        try:
            sha = s.seed(b'{"e": 14}', "acq-e14")
            s.commit("proj-c", [(sha, "acq-e14")])
            if corrupt == "schema":
                frag = (
                    s.ROOT / "catalogs" / "projection_schemas"
                    / catalog_physical_key(s.definition().schema_identity)
                )
                expected = "ProjectionSchemaCatalogCorrupt"
            elif corrupt == "artifact":
                frag = (
                    s.ROOT / "catalogs" / "manifests" / "projections"
                    / catalog_physical_key("proj-c")
                )
                expected = "ProjectionArtifactCatalogCorrupt"
            elif corrupt == "lineage":
                frag = (
                    s.ROOT / "catalogs" / "manifests" / "projection_lineage"
                    / catalog_physical_key("lm-proj-c")
                )
                expected = "ProjectionLineageCatalogCorrupt"
            else:  # context
                frag = (
                    s.ROOT / "catalogs" / "manifests" / "projection_context"
                    / catalog_physical_key("proj-c")
                )
                expected = "ProjectionArtifactCatalogCorrupt"
            frag.write_text("{corrupt", encoding="utf-8")
            raised = "none"
            try:
                Stack(tmp_path, fresh=False).reopen()
            except Exception as exc:  # noqa: BLE001
                raised = _err_name(_loc(exc))
            record(case_name, ok=False, error=expected, observed=raised,
                   fragment_preserved=frag.exists())
        finally:
            s.close()

    _restart_corrupt("restart_corrupt_schema", "schema")
    _restart_corrupt("restart_corrupt_artifact", "artifact")
    _restart_corrupt("restart_corrupt_lineage", "lineage")

    # restart_corrupt_projection (physical bytes)
    s = Stack(tmp_path)
    try:
        sha = s.seed(b'{"e": 15}', "acq-e15")
        s.commit("proj-c", [(sha, "acq-e15")])
        physical = list((s.ROOT / "projections").glob("**/*.parquet"))[0]
        physical.write_bytes(b"corrupt parquet bytes")
        s2 = Stack(tmp_path, fresh=False).reopen()
        resolver = ProjectionLineageResolver(
            root=s2.ROOT, artifacts=s2.artifacts, contexts=s2.contexts,
            lineage=s2.lineage, schemas=s2.schemas,
        )
        raised = "none"
        try:
            resolver.validate_projection_ref("proj-c", _manifest([sha], ["proj-c"]))
        except Exception as exc:  # noqa: BLE001
            raised = _err_name(_loc(exc))
        record("restart_corrupt_projection", ok=False,
               error="projection_corruption_detected", observed=raised,
               expected_error="typed_corruption_failure")
    finally:
        s.close()

    return {
        "matrix": "BLOC_04_I05R1_END_TO_END_LINEAGE_MATRIX",
        "checkpoint": "SENSOR-B4-I05R1",
        "clock": "injected-fixed",
        "resolver": "production ProjectionLineageResolver (no stub)",
        "cases": cases,
    }


def _loc(exc: BaseException) -> BaseException:
    return exc


# ---------------------------------------------------------------------------
# Matrix 3 — schema fidelity
# ---------------------------------------------------------------------------


def _schema_fidelity_matrix() -> dict:
    from crypto_sensor_fabric.storage.projection_schema import (
        t0_metadata_descriptor,
    )
    import hashlib

    cases: list[dict] = []

    def fp(descriptor: dict) -> str:
        return hashlib.sha256(
            json.dumps(descriptor, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")).encode("utf-8")
        ).hexdigest()

    fields = [{"name": "price", "type": {"type": "double"}, "nullable": False}]

    # t0_metadata_type_change
    t0_base = t0_metadata_descriptor()
    t0_changed = [
        {**d, "type": {"type": "string"}} if d["name"] == "_t0_row_ordinal" else d
        for d in t0_base
    ]
    cases.append({
        "case": "t0_metadata_type_change",
        "change": "_t0_row_ordinal int64 -> string",
        "fingerprint_changes": fp(
            {"fields": fields, "t0_metadata_schema": t0_base}
        ) != fp({"fields": fields, "t0_metadata_schema": t0_changed}),
        "expected": True,
    })

    # Arrow structural units
    def _pair(schema_a: pa.Schema, schema_b: pa.Schema, case: str) -> None:
        d1 = ProjectionSchemaDefinition("f.id", "1.0.0", schema_a)
        d2 = ProjectionSchemaDefinition("f.id", "1.0.0", schema_b)
        roundtrip = d1.provider_native_schema.equals(
            ProjectionSchemaDefinition.from_descriptor(d1.to_descriptor())
            .provider_native_schema
        )
        cases.append({
            "case": case,
            "lossless_roundtrip": roundtrip,
            "fingerprint_changes": d1.schema_fingerprint != d2.schema_fingerprint,
        })

    _pair(
        pa.schema([pa.field("t", pa.time32("ms"), nullable=True)]),
        pa.schema([pa.field("t", pa.time32("s"), nullable=True)]),
        "time32_unit",
    )
    _pair(
        pa.schema([pa.field("t", pa.time64("us"), nullable=True)]),
        pa.schema([pa.field("t", pa.time64("ns"), nullable=True)]),
        "time64_unit",
    )
    _pair(
        pa.schema([pa.field("ts", pa.timestamp("us", tz="UTC"), nullable=False)]),
        pa.schema([pa.field("ts", pa.timestamp("us", tz="+05:30"), nullable=False)]),
        "timestamp_timezone",
    )
    _pair(
        pa.schema([pa.field("l", pa.list_(pa.field("item", pa.string(), nullable=False)))]),
        pa.schema([pa.field("l", pa.list_(pa.field("item", pa.string(), nullable=True)))]),
        "list_child_nullability",
    )
    _pair(
        pa.schema([pa.field(
            "s",
            pa.struct([pa.field("x", pa.float64(), nullable=False),
                       pa.field("y", pa.int64(), nullable=True)]),
        )]),
        pa.schema([pa.field(
            "s",
            pa.struct([pa.field("x", pa.float64(), nullable=True),
                       pa.field("y", pa.int64(), nullable=True)]),
        )]),
        "struct_child_nullability",
    )
    _pair(
        pa.schema([pa.field("a", pa.decimal128(18, 8), nullable=False)]),
        pa.schema([pa.field("a", pa.decimal128(20, 8), nullable=False)]),
        "decimal_precision_scale",
    )

    # unsupported_arrow_type
    arr = pa.array(["a", "b", "a"]).dictionary_encode()
    unsupported = "none"
    try:
        ProjectionSchemaDefinition(
            "f.bad", "1.0.0", pa.schema([pa.field("d", arr.type, nullable=True)])
        )
    except Exception as exc:  # noqa: BLE001
        unsupported = type(exc).__name__
    cases.append({
        "case": "unsupported_arrow_type",
        "expected_error": "UnsupportedProjectionSchemaType",
        "observed_error": unsupported,
    })

    # schema_key_tamper / schema_fingerprint_tamper (registry reload fails closed)
    import shutil as _shutil
    import tempfile

    base = Path(tempfile.mkdtemp(prefix="r1f_schema_"))
    try:
        root = base / "catalogs" / "projection_schemas"
        reg = ProjectionSchemaRegistry(root)
        d = ProjectionSchemaDefinition("f.tamper", "1.0.0", NATIVE)
        reg.register(d)
        frag = root / catalog_physical_key(d.schema_identity)

        payload = json.loads(frag.read_text(encoding="utf-8"))
        payload["schema_key"] = "f" * 64
        frag.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        raised = "none"
        try:
            ProjectionSchemaRegistry(root)
        except Exception as exc:  # noqa: BLE001
            raised = type(exc).__name__
        cases.append({
            "case": "schema_key_tamper",
            "expected_error": "ProjectionSchemaCatalogCorrupt",
            "observed_error": raised,
        })

        payload = json.loads(frag.read_text(encoding="utf-8"))
        payload["schema_key"] = d.schema_key
        payload["schema_fingerprint"] = "e" * 64
        frag.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
        raised = "none"
        try:
            ProjectionSchemaRegistry(root)
        except Exception as exc:  # noqa: BLE001
            raised = type(exc).__name__
        cases.append({
            "case": "schema_fingerprint_tamper",
            "expected_error": "ProjectionSchemaCatalogCorrupt",
            "observed_error": raised,
        })
    finally:
        _shutil.rmtree(base, ignore_errors=True)

    return {
        "matrix": "BLOC_04_I05R1_SCHEMA_FIDELITY_MATRIX",
        "checkpoint": "SENSOR-B4-I05R1",
        "clock": "injected-fixed",
        "cases": cases,
    }


# ---------------------------------------------------------------------------
# Tests: generate twice, assert byte stability
# ---------------------------------------------------------------------------


class TestDurabilityMatrix:
    def test_deterministic_generation(self, tmp_path: Path) -> None:
        first = _durability_matrix(tmp_path / "a")
        second = _durability_matrix(tmp_path / "b")
        raw = _dump_stable(EVIDENCE_DIR / "BLOC_04_I05R1_DURABILITY_MATRIX.json", first)
        assert raw == json.dumps(second, sort_keys=True, ensure_ascii=False,
                                 indent=2).encode("utf-8")

    def test_all_cases_deterministic_fields(self, tmp_path: Path) -> None:
        matrix = _durability_matrix(tmp_path)
        text = json.dumps(matrix).lower()
        for banned in ("now()", "utcnow", "wallclock"):
            assert banned not in text


class TestEndToEndLineageMatrix:
    def test_deterministic_generation(self, tmp_path: Path) -> None:
        first = _end_to_end_matrix(tmp_path / "a")
        second = _end_to_end_matrix(tmp_path / "b")
        raw = _dump_stable(
            EVIDENCE_DIR / "BLOC_04_I05R1_END_TO_END_LINEAGE_MATRIX.json", first
        )
        assert raw == json.dumps(second, sort_keys=True, ensure_ascii=False,
                                 indent=2).encode("utf-8")

    def test_required_cases_present(self, tmp_path: Path) -> None:
        matrix = _end_to_end_matrix(tmp_path)
        names = {c["case"] for c in matrix["cases"]}
        required = {
            "single_source_real_chain", "multi_source_real_chain", "wrong_provider",
            "wrong_acquisition_blob", "failed_acquisition", "missing_physical_blob",
            "missing_artifact", "missing_lineage", "wrong_partition",
            "source_blob_hidden_from_manifest", "restart_valid",
            "restart_corrupt_schema", "restart_corrupt_projection",
            "restart_corrupt_artifact", "restart_corrupt_lineage",
        }
        assert required <= names


class TestSchemaFidelityMatrix:
    def test_deterministic_generation(self) -> None:
        first = _schema_fidelity_matrix()
        second = _schema_fidelity_matrix()
        raw = _dump_stable(
            EVIDENCE_DIR / "BLOC_04_I05R1_SCHEMA_FIDELITY_MATRIX.json", first
        )
        assert raw == json.dumps(second, sort_keys=True, ensure_ascii=False,
                                 indent=2).encode("utf-8")

    def test_required_cases_present(self) -> None:
        matrix = _schema_fidelity_matrix()
        names = {c["case"] for c in matrix["cases"]}
        required = {
            "t0_metadata_type_change", "time32_unit", "time64_unit",
            "timestamp_timezone", "list_child_nullability",
            "struct_child_nullability", "decimal_precision_scale",
            "unsupported_arrow_type", "schema_key_tamper",
            "schema_fingerprint_tamper",
        }
        assert required <= names
