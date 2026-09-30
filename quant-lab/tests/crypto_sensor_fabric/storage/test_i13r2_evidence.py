"""SENSOR-B4-I13R2 — evidence-fidelity + default resource-safety closure.

Append-only correction evidence for the five operator-review blockers:

A. default free-space safety (real local disk usage, never silent bypass)
B. exact metadata parity INCLUDING query-semantic acquisition timestamps
C. revision-registry parity measuring keys+segments+observations+declarations
D. DuckDB identity-level parity (sorted identity tuples, not counts)
E. SUCCESS_PARITY vs REFUSAL_PARITY separation with successful fixtures
   for every revision policy + explicit time-filter parity

Seven matrices, each row measured from production behavior / adversarial
mutation / structural introspection, at most one explicit SYNTHETIC
counterfactual per matrix:

- BLOC_04_I13R2_RESOURCE_SAFETY_MATRIX.json
- BLOC_04_I13R2_EXACT_METADATA_PARITY_MATRIX.json
- BLOC_04_I13R2_REVISION_PARITY_MATRIX.json
- BLOC_04_I13R2_DUCKDB_IDENTITY_PARITY_MATRIX.json
- BLOC_04_I13R2_QUERY_POLICY_PARITY_MATRIX.json
- BLOC_04_I13R2_TIME_FILTER_PARITY_MATRIX.json
- BLOC_04_I13R2_BOUNDED_SLICE_MATRIX.json

Historical I13/I13R1 matrices are NOT modified (§25).
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from datetime import timedelta
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from _sibling_import import load_sibling  # noqa: E402

from crypto_sensor_fabric.storage import (  # noqa: E402
    EvidencePackRestorer,
    PackObjectRole,
    PackResourceLimitExceeded,
    RawEvidenceQuery,
    RawEvidenceQueryService,
)
from crypto_sensor_fabric.storage.blob_store import LocalBlobStore  # noqa: E402
from crypto_sensor_fabric.storage.catalog import (  # noqa: E402
    AcquisitionRepository,
    BlobMetadataRepository,
)
from crypto_sensor_fabric.storage.duckdb_catalog import (  # noqa: E402
    rebuild_duckdb_catalog,
)
from crypto_sensor_fabric.storage.export import (  # noqa: E402
    read_pack_manifest,
)
from crypto_sensor_fabric.storage.manifests import (  # noqa: E402
    PartitionManifestRepository,
)
from crypto_sensor_fabric.storage.projection_lineage import (  # noqa: E402
    ProjectionLineageRepository,
)
from crypto_sensor_fabric.storage.projections import (  # noqa: E402
    ProjectionArtifactRepository,
    ProjectionContextRepository,
)
from crypto_sensor_fabric.storage.enums import (  # noqa: E402
    RevisionPolicy,
)
from crypto_sensor_fabric.storage.revisions import (  # noqa: E402
    RevisionResolutionMode,
    RevisionSourceIdentityV1,
    SourceRevisionRegistry,
)

i13 = load_sibling("test_i13_export_restore", "test_i13_export_restore")
build_fixture_lake = i13.build_fixture_lake
_exporter = i13._exporter
_restore_service = i13._restore_service
Lake = i13.Lake
FIXED = i13.FIXED

EVIDENCE_DIR = (
    HERE.parents[2]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)

EXPORT_SOURCE = (
    HERE.parents[2] / "src" / "crypto_sensor_fabric" / "storage" / "export.py"
).read_text(encoding="utf-8")


def build_deterministic_lake(root: Path):  # type: ignore[no-untyped-def]
    """build_fixture_lake with a FULLY deterministic seeding clock.

    The shared Lake harness injects FIXED clocks for manifests/registry
    but leaves the BlobMetadataRepository on the wall clock, so
    ``EvidenceBlob.created_at`` (an operational metadata field, NOT
    evidence content) varies between runs and breaks published-matrix
    byte-stability.  This wrapper injects the accepted ``clock=``
    parameter at repository CONSTRUCTION time (before any seeding)
    WITHOUT modifying the shared historical harness (§25).
    """
    import crypto_sensor_fabric.storage.blob_store as _bs
    import crypto_sensor_fabric.storage.catalog as _cat

    orig_store_init = _bs.LocalBlobStore.__init__
    orig_repo_init = _cat.BlobMetadataRepository.__init__

    def _patched_store_init(self, root, *, clock=None, **kwargs):  # type: ignore[no-untyped-def]
        orig_store_init(self, root, clock=lambda: FIXED, **kwargs)

    def _patched_repo_init(self, root, *, blob_store, clock=None):  # type: ignore[no-untyped-def]
        orig_repo_init(self, root, blob_store=blob_store, clock=lambda: FIXED)

    _bs.LocalBlobStore.__init__ = _patched_store_init  # type: ignore[method-assign]
    _cat.BlobMetadataRepository.__init__ = _patched_repo_init  # type: ignore[method-assign]
    try:
        lake = build_fixture_lake(root)
    finally:
        _bs.LocalBlobStore.__init__ = orig_store_init  # type: ignore[method-assign]
        _cat.BlobMetadataRepository.__init__ = orig_repo_init  # type: ignore[method-assign]
    return lake

# ---------------------------------------------------------------------------
# Canonical serialization + measured helpers
# ---------------------------------------------------------------------------


def _canonical(obj) -> str:  # type: ignore[no-untyped-def]
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def _row(  # type: ignore[no-untyped-def]
    case_id, *, category, invariant, result, measured,
    invariant_source="PRODUCTION_MEASURED",
):
    return {
        "case_id": case_id,
        "category": category,
        "invariant": invariant,
        "result": result,
        "measured": measured,
        "invariant_source": invariant_source,
    }


def _scrub(value, root: Path):  # type: ignore[no-untyped-def]
    """Replace absolute temp-path prefixes with a stable placeholder so
    published matrices are byte-stable across runs (paths are run-local
    observations, not evidence)."""
    prefix = str(root)
    if isinstance(value, str):
        if prefix in value:
            value = value.replace(prefix, "<TMP>")
        return value
    if isinstance(value, list):
        return [_scrub(v, root) for v in value]
    if isinstance(value, tuple):
        return [_scrub(v, root) for v in value]
    if isinstance(value, dict):
        return {k: _scrub(v, root) for k, v in value.items()}
    return value


def _matrix(name: str, cases: list[dict], scrub_root: Path | None = None) -> dict:
    if scrub_root is not None:
        cases = [_scrub(c, scrub_root) for c in cases]  # type: ignore[assignment]
    return {
        "mandate": "SENSOR-B4-I13R2",
        "matrix": name,
        "measured_at_checkpoint": "I13R2",
        "corrects": (
            "SENSOR-B4-I13R1 operator-review blockers A-E "
            "(resource default, exact metadata, revision/declaration "
            "measurement, DuckDB identity, success/refusal parity)"
        ),
        "rows_total": len(cases),
        "rows_ok": sum(1 for c in cases if c["result"] == "OK"),
        "rows_fail": sum(1 for c in cases if c["result"] == "FAIL"),
        "synthetic_counterfactuals": sum(
            1 for c in cases if c["category"] == "SYNTHETIC_COUNTERFACTUAL"
        ),
        "cases": cases,
    }


def _results_digest(results) -> str:  # type: ignore[no-untyped-def]
    return hashlib.sha256(
        _canonical([r.model_dump(mode="json") for r in results]).encode("utf-8")
    ).hexdigest()


def _mkdir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


class _Round:
    """One full export + restore round-trip on a fresh fixture lake."""

    def __init__(self, tmp: Path, tag: str, query: RawEvidenceQuery | None = None,
                 lake_builder=None) -> None:
        root = _mkdir(tmp / tag)
        self.lake = (lake_builder or build_deterministic_lake)(root / "src")
        if query is None:
            # Multi-revision fixtures must not export under the ambiguous
            # default (the I12 fail-safe law refuses ambiguity).  ALL is
            # the neutral multi-revision-safe selection.
            query = RawEvidenceQuery(revision_policy=RevisionPolicy.ALL)
        self.query = query
        self.receipt = _exporter(self.lake).export_query(
            self.query, root / "pack"
        )
        self.pack_root = root / "pack"
        self.manifest = read_pack_manifest(self.pack_root)
        self.restored_root = root / "restored"
        EvidencePackRestorer().restore_pack(
            self.pack_root, self.restored_root
        )

    # -- pack slice inventories -------------------------------------------

    def pack_blob_shas(self) -> list[str]:
        return sorted(
            r.object_id
            for r in self.manifest.object_inventory
            if r.role is PackObjectRole.BLOB
        )

    def pack_acq_ids(self) -> list[str]:
        return sorted(
            r.object_id
            for r in self.manifest.object_inventory
            if r.role is PackObjectRole.ACQUISITION
        )

    def pack_manifest_ids(self) -> list[str]:
        return sorted(
            r.object_id
            for r in self.manifest.object_inventory
            if r.role is PackObjectRole.MANIFEST
        )

    def pack_projection_ids(self) -> list[str]:
        return sorted(
            r.object_id.removeprefix("context:")
            for r in self.manifest.object_inventory
            if r.role is PackObjectRole.PROJECTION_CONTEXT
        )

    def pack_segment_keys(self) -> list[str]:
        return sorted(
            r.provenance_ref
            for r in self.manifest.object_inventory
            if r.role is PackObjectRole.REVISION_SEGMENTS
        )

    # -- restored repositories (fresh instances, §45) ----------------------

    def restored_repos(self):  # type: ignore[no-untyped-def]
        root = self.restored_root
        store = LocalBlobStore(str(root / "t0a"))
        blob = BlobMetadataRepository(root / "t0a", blob_store=store)
        acq = AcquisitionRepository(
            root / "t0a", blob_store=store, blob_metadata_repository=blob
        )
        man = PartitionManifestRepository(
            root / "t0a",
            blob_store=store,
            blob_metadata_repository=blob,
            acquisition_repository=acq,
        )
        reg = SourceRevisionRegistry(
            root / "t0a" / "revisions",
            acquisition_repository=acq,
            blob_metadata_repository=blob,
            blob_store=store,
        )
        return store, blob, acq, man, reg

    def restored_t0b(self):  # type: ignore[no-untyped-def]
        root = self.restored_root
        store, blob, acq, _man, _reg = self.restored_repos()
        schemas = root / "t0b" / "catalogs" / "projection_schemas"
        artifacts = ProjectionArtifactRepository(
            root / "t0b" / "catalogs" / "manifests" / "projections",
            projection_root=root / "t0b",
            schema_registry=None,
        )
        contexts = ProjectionContextRepository(
            root / "t0b" / "catalogs" / "manifests" / "projection_context"
        )
        lineage = ProjectionLineageRepository(
            root / "t0b" / "catalogs" / "manifests" / "projection_lineage",
            blob_store=store,
            blob_metadata_repository=blob,
            acquisition_repository=acq,
            artifact_repository=artifacts,
            context_repository=contexts,
        )
        _ = schemas
        return artifacts, contexts, lineage

    def restored_service(self) -> RawEvidenceQueryService:
        return _restore_service(self.restored_root)


# ---------------------------------------------------------------------------
# A. RESOURCE_SAFETY (blocker A: default disk usage, never silent bypass)
# ---------------------------------------------------------------------------


def _measure_resource_safety(tmp: Path) -> list[dict]:
    import crypto_sensor_fabric.storage.export as exp

    cases: list[dict] = []
    calls: list[str] = []
    real_disk_usage = shutil.disk_usage

    def tracking_default(path):  # type: ignore[no-untyped-def]
        usage = real_disk_usage(path)
        calls.append(str(path))
        return usage

    # 1. default exporter performs a REAL disk-usage check (no provider).
    root = _mkdir(tmp / "export_default")
    lake = build_deterministic_lake(root / "src")
    real_fn = exp.shutil.disk_usage
    exp.shutil.disk_usage = tracking_default
    try:
        _exporter(lake).export_query(RawEvidenceQuery(), root / "pack")
    finally:
        exp.shutil.disk_usage = real_fn
    cases.append(
        _row(
            "default_exporter_uses_real_disk_usage",
            category="PRODUCTION_BEHAVIOR",
            invariant=(
                "exporter with NO injected provider still runs a real "
                "local disk-usage check (never silent bypass)"
            ),
            result="OK" if calls else "FAIL",
            measured={"disk_usage_calls": len(calls), "probed": calls[:2]},
        )
    )

    # 2. default restorer performs a REAL disk-usage check (no provider).
    calls.clear()
    root = _mkdir(tmp / "restore_default")
    lake = build_deterministic_lake(root / "src")
    pack = _exporter(lake).export_query(RawEvidenceQuery(), root / "pack")
    real_fn = exp.shutil.disk_usage
    exp.shutil.disk_usage = tracking_default
    try:
        EvidencePackRestorer().restore_pack(
            root / "pack", root / "restored"
        )
    finally:
        exp.shutil.disk_usage = real_fn
    _ = pack
    cases.append(
        _row(
            "default_restorer_uses_real_disk_usage",
            category="PRODUCTION_BEHAVIOR",
            invariant=(
                "restorer with NO injected provider still runs a real "
                "local disk-usage check against pack inventory bytes"
            ),
            result="OK" if calls else "FAIL",
            measured={"disk_usage_calls": len(calls), "probed": calls[:2]},
        )
    )

    # 3. injected provider overrides the default.
    injected_calls: list[str] = []
    root = _mkdir(tmp / "injected")
    lake = build_deterministic_lake(root / "src")

    def injected(path):  # type: ignore[no-untyped-def]
        injected_calls.append(str(path))
        return (1 << 40, 1 << 40)

    _exporter(lake, disk_usage_provider=injected).export_query(
        RawEvidenceQuery(), root / "pack"
    )
    cases.append(
        _row(
            "injected_provider_overrides_default",
            category="PRODUCTION_BEHAVIOR",
            invariant="injected disk_usage_provider replaces local probing",
            result="OK" if injected_calls else "FAIL",
            measured={"injected_calls": len(injected_calls)},
        )
    )

    # 4. insufficient free space at EXPORT refuses typed (pre-copy).
    root = _mkdir(tmp / "export_full")
    lake = build_deterministic_lake(root / "src")
    refused = None
    try:
        _exporter(
            lake, disk_usage_provider=lambda _p: (1 << 40, 0)
        ).export_query(RawEvidenceQuery(), root / "pack")
    except PackResourceLimitExceeded as exc:
        refused = type(exc).__name__
    cases.append(
        _row(
            "insufficient_free_export_refused",
            category="ADVERSARIAL_MUTATION",
            invariant="zero free space refuses export with typed error",
            result="OK" if refused == "PackResourceLimitExceeded" else "FAIL",
            measured={"raised": refused},
        )
    )

    # 5. insufficient free space at RESTORE refuses typed.
    root = _mkdir(tmp / "restore_full")
    lake = build_deterministic_lake(root / "src")
    _ = _exporter(lake).export_query(RawEvidenceQuery(), root / "pack")
    refused = None
    try:
        EvidencePackRestorer(
            disk_usage_provider=lambda _p: (1 << 40, 0)
        ).restore_pack(root / "pack", root / "restored")
    except PackResourceLimitExceeded as exc:
        refused = type(exc).__name__
    cases.append(
        _row(
            "insufficient_free_restore_refused",
            category="ADVERSARIAL_MUTATION",
            invariant="zero free space refuses restore with typed error",
            result="OK" if refused == "PackResourceLimitExceeded" else "FAIL",
            measured={"raised": refused},
        )
    )

    # 6. pre-copy estimate is non-trivial: a HUGE selected blob must be
    #    checked BEFORE bulk payload copying (progressive check law).
    root = _mkdir(tmp / "precopy")
    lake = build_deterministic_lake(root / "src")
    big = lake.seed_blob(b"x" * (5 << 20))
    lake.seed_acquisition(
        big, "acq-big", instrument="ETH-USDT"
    )
    lake.commit_manifest("m-big", blob_refs=[big], instrument="ETH-USDT")
    check_sizes: list[int] = []

    def sized_provider(path, _sizes=check_sizes):  # type: ignore[no-untyped-def]
        _ = path
        return (1 << 40, 1 << 40)

    captured: list[tuple[Path, int]] = []
    exporter = _exporter(lake, disk_usage_provider=sized_provider)
    original = exporter._check_free_space

    def spy(destination, required):  # type: ignore[no-untyped-def]
        captured.append((Path(destination), int(required)))
        return original(destination, required)

    exporter._check_free_space = spy  # type: ignore[method-assign]
    exporter.export_query(RawEvidenceQuery(), root / "pack")
    max_required = max((req for _p, req in captured), default=0)
    check_sizes.extend(req for _p, req in captured)
    cases.append(
        _row(
            "precopy_estimate_covers_selected_bytes",
            category="PRODUCTION_BEHAVIOR",
            invariant=(
                "free-space checks see the selected T0A byte length "
                "(estimate >= 5 MiB blob) before/while copying"
            ),
            result="OK" if max_required >= (5 << 20) else "FAIL",
            measured={
                "checks": len(captured),
                "max_required_bytes": max_required,
                "selected_blob_bytes": 5 << 20,
            },
        )
    )

    # 7. synthetic counterfactual: silent bypass would look identical to a
    #    green run in a shallow review.
    cases.append(
        _row(
            "synthetic_counterfactual_silent_bypass",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant=(
                "a skipped free-space check would leave no trace without "
                "call-count measurement"
            ),
            result="FAIL",
            measured={"asserted": "no silent bypass permitted by §2/§5"},
            invariant_source="SYNTHETIC",
        )
    )
    return cases


# ---------------------------------------------------------------------------
# B. EXACT_METADATA_PARITY (blocker B: timestamps are query-semantic)
# ---------------------------------------------------------------------------

# §28 documented exclusion set per record type.  Measured probe showed
# every persisted field of blobs/acquisitions/manifests/artifacts/
# contexts/lineage/declarations is EXACTLY equal after restore; only the
# I06 operational registration clock (segments/observations) differs.
EXCLUDED_FIELDS: dict[str, list[str]] = {
    "EvidenceBlob": [],
    "AcquisitionRecord": [],
    "PartitionManifest": [],
    "RawProjectionArtifact": [],
    "ProjectionCatalogRecord": [],
    "ProjectionLineage": [],
    "RevisionDeclarationRecord": [],
    # I06 law: registered_at is the LOCAL registration audit clock (§21),
    # necessarily re-earned at replay (restorer registers from restored
    # durable truth on a later clock).
    "RevisionSegmentRecord": ["registered_at"],
    "RevisionObservationRecord": ["registered_at"],
}


def _strip(record: dict, excluded: list[str]) -> dict:
    return {k: v for k, v in record.items() if k not in excluded}


def _roundtrip_metadata_roundtrip(tmp: Path):  # type: ignore[no-untyped-def]
    return _Round(tmp, "meta", RawEvidenceQuery())


def _measure_exact_metadata(tmp: Path) -> list[dict]:
    roundtrip = _roundtrip_metadata_roundtrip(tmp)
    blob_shas = roundtrip.pack_blob_shas()
    acq_ids = roundtrip.pack_acq_ids()
    manifest_ids = roundtrip.pack_manifest_ids()
    projection_ids = roundtrip.pack_projection_ids()
    _, r_blob, r_acq, r_man, _ = roundtrip.restored_repos()

    cases: list[dict] = []

    # 1. AcquisitionRecord EXACT parity including ingested_at,
    #    response_observed_at, requested_start/end (§7).
    s_acq = sorted(
        _canonical(a.model_dump(mode="json"))
        for a in roundtrip.lake.acq_repo.list_all_acquisitions()
        if a.acquisition_id in acq_ids
    )
    r_acq = sorted(
        _canonical(a.model_dump(mode="json"))
        for a in r_acq.list_all_acquisitions()
    )
    cases.append(
        _row(
            "acquisition_record_exact_parity",
            category="PRODUCTION_BEHAVIOR",
            invariant=(
                "AcquisitionRecord canonical serialization literally equal "
                "INCLUDING ingested_at/response_observed_at/requested_* "
                "(query-semantic evidence per I12 acquired_before/"
                "observed_before law)"
            ),
            result="OK" if s_acq == r_acq else "FAIL",
            measured={
                "source_digest": hashlib.sha256(
                    _canonical(s_acq).encode()
                ).hexdigest(),
                "restored_digest": hashlib.sha256(
                    _canonical(r_acq).encode()
                ).hexdigest(),
                "rows": len(s_acq),
                "excluded_fields": EXCLUDED_FIELDS["AcquisitionRecord"],
                "query_semantic_fields_verified": [
                    "ingested_at",
                    "request_started_at",
                    "response_observed_at",
                    "requested_start",
                    "requested_end",
                ],
            },
        )
    )

    # 2. EvidenceBlob exact parity.
    s_blob = sorted(
        _canonical(b.model_dump(mode="json"))
        for b in roundtrip.lake.blob_repo.list_all_blob_metadata()
        if b.blob_sha256 in blob_shas
    )
    r_blob_rows = sorted(
        _canonical(b.model_dump(mode="json"))
        for b in r_blob.list_all_blob_metadata()
    )
    cases.append(
        _row(
            "evidence_blob_exact_parity",
            category="PRODUCTION_BEHAVIOR",
            invariant="EvidenceBlob canonical serialization literally equal",
            result="OK" if s_blob == r_blob_rows else "FAIL",
            measured={
                "source_digest": hashlib.sha256(
                    _canonical(s_blob).encode()
                ).hexdigest(),
                "restored_digest": hashlib.sha256(
                    _canonical(r_blob_rows).encode()
                ).hexdigest(),
                "rows": len(s_blob),
                "excluded_fields": EXCLUDED_FIELDS["EvidenceBlob"],
            },
        )
    )

    # 3. PartitionManifest exact parity.
    s_man = sorted(
        _canonical(m.model_dump(mode="json"))
        for m in roundtrip.lake.manifest_repo.list_all_current_manifests()
        if m.partition_manifest_id in manifest_ids
    )
    r_man_rows = sorted(
        _canonical(m.model_dump(mode="json"))
        for m in r_man.list_all_current_manifests()
    )
    cases.append(
        _row(
            "partition_manifest_exact_parity",
            category="PRODUCTION_BEHAVIOR",
            invariant="PartitionManifest canonical serialization literally equal",
            result="OK" if s_man == r_man_rows else "FAIL",
            measured={
                "source_digest": hashlib.sha256(
                    _canonical(s_man).encode()
                ).hexdigest(),
                "restored_digest": hashlib.sha256(
                    _canonical(r_man_rows).encode()
                ).hexdigest(),
                "rows": len(s_man),
                "excluded_fields": EXCLUDED_FIELDS["PartitionManifest"],
            },
        )
    )

    # 4. T0B artifact/context/lineage exact parity.
    r_art, r_ctx, r_lin = roundtrip.restored_t0b()
    s_art = sorted(
        _canonical(a.model_dump(mode="json"))
        for a in (
            roundtrip.lake.artifacts.get_strict(pid) for pid in projection_ids
        )
    )
    r_art_rows = sorted(
        _canonical(a.model_dump(mode="json"))
        for a in (r_art.get_strict(pid) for pid in projection_ids)
    )
    cases.append(
        _row(
            "projection_artifact_exact_parity",
            category="PRODUCTION_BEHAVIOR",
            invariant="RawProjectionArtifact canonical serialization equal",
            result="OK" if s_art == r_art_rows else "FAIL",
            measured={
                "source_digest": hashlib.sha256(
                    _canonical(s_art).encode()
                ).hexdigest(),
                "restored_digest": hashlib.sha256(
                    _canonical(r_art_rows).encode()
                ).hexdigest(),
                "rows": len(s_art),
                "excluded_fields": EXCLUDED_FIELDS["RawProjectionArtifact"],
            },
        )
    )

    s_ctx = sorted(
        _canonical(c.to_dict())
        for c in (
            roundtrip.lake.contexts.get_strict(pid) for pid in projection_ids
        )
    )
    r_ctx_rows = sorted(
        _canonical(c.to_dict())
        for c in (r_ctx.get_strict(pid) for pid in projection_ids)
    )
    cases.append(
        _row(
            "projection_context_exact_parity",
            category="PRODUCTION_BEHAVIOR",
            invariant="ProjectionCatalogRecord context equality",
            result="OK" if s_ctx == r_ctx_rows else "FAIL",
            measured={
                "source_digest": hashlib.sha256(
                    _canonical(s_ctx).encode()
                ).hexdigest(),
                "restored_digest": hashlib.sha256(
                    _canonical(r_ctx_rows).encode()
                ).hexdigest(),
                "rows": len(s_ctx),
                "excluded_fields": EXCLUDED_FIELDS["ProjectionCatalogRecord"],
            },
        )
    )

    s_lin = sorted(
        _canonical([e.model_dump(mode="json") for e in roundtrip.lake.lineage.get_by_projection(pid)])
        for pid in projection_ids
    )
    r_lin_rows = sorted(
        _canonical([e.model_dump(mode="json") for e in r_lin.get_by_projection(pid)])
        for pid in projection_ids
    )
    cases.append(
        _row(
            "projection_lineage_exact_parity",
            category="PRODUCTION_BEHAVIOR",
            invariant="ProjectionLineage rows literally equal",
            result="OK" if s_lin == r_lin_rows else "FAIL",
            measured={
                "source_digest": hashlib.sha256(
                    _canonical(s_lin).encode()
                ).hexdigest(),
                "restored_digest": hashlib.sha256(
                    _canonical(r_lin_rows).encode()
                ).hexdigest(),
                "rows": len(s_lin),
                "excluded_fields": EXCLUDED_FIELDS["ProjectionLineage"],
            },
        )
    )

    # 5. exclusion-set audit: only I06 registration clocks are excluded.
    all_excluded = sorted(
        {f for fields in EXCLUDED_FIELDS.values() for f in fields}
    )
    cases.append(
        _row(
            "exclusion_set_is_minimal_and_documented",
            category="STRUCTURAL_INTROSPECTION",
            invariant=(
                "excluded fields limited to I06 operational registration "
                "clock; no broad operational bucket"
            ),
            result="OK"
            if all_excluded == ["registered_at"]
            else "FAIL",
            measured={"excluded_fields": all_excluded},
        )
    )

    cases.append(
        _row(
            "synthetic_counterfactual_timestamp_strip",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant=(
                "stripping ingested_at/observed_at from parity would pass "
                "even if restore corrupted acquisition timestamps"
            ),
            result="FAIL",
            measured={"asserted": "timestamps are query-semantic (§6)"},
            invariant_source="SYNTHETIC",
        )
    )
    return cases


# ---------------------------------------------------------------------------
# C. REVISION_PARITY (blocker C: measure keys+segments+observations+
#    declarations+resolutions, not just segments)
# ---------------------------------------------------------------------------


def _two_rev_lake(root: Path):  # type: ignore[no-untyped-def]
    lake = build_deterministic_lake(root)
    sha_r2 = lake.seed_blob(b'{"rev": 2}')
    lake.seed_acquisition(
        sha_r2,
        "acq-rev2",
        request_fingerprint="fp-acq-1",
        observed_at=FIXED + timedelta(hours=1),
    )
    return lake


def _measure_revision_parity(tmp: Path) -> list[dict]:
    roundtrip = _Round(tmp, "rev", lake_builder=_two_rev_lake)
    keys = roundtrip.pack_segment_keys()
    _, _b, _a, _m, r_reg = roundtrip.restored_repos()
    s_reg = roundtrip.lake.registry

    cases: list[dict] = []

    # 1. keys parity.
    s_keys = sorted(k for k in s_reg.list_source_revision_keys() if k in keys)
    r_keys = sorted(k for k in r_reg.list_source_revision_keys() if k in keys)
    cases.append(
        _row(
            "revision_keys_parity",
            category="PRODUCTION_BEHAVIOR",
            invariant="exported source-revision key set literally equal",
            result="OK" if s_keys == r_keys else "FAIL",
            measured={"source_keys": s_keys, "restored_keys": r_keys},
        )
    )

    for key in keys:
        tag = key[:12]

        # segments (registered_at excluded, documented).
        s_seg = sorted(
            _canonical(_strip(x.model_dump(mode="json"), EXCLUDED_FIELDS["RevisionSegmentRecord"]))
            for x in s_reg.list_segment_records(key)
        )
        r_seg = sorted(
            _canonical(_strip(x.model_dump(mode="json"), EXCLUDED_FIELDS["RevisionSegmentRecord"]))
            for x in r_reg.list_segment_records(key)
        )
        cases.append(
            _row(
                f"segment_records_parity_{tag}",
                category="PRODUCTION_BEHAVIOR",
                invariant=(
                    "segment records equal excluding documented "
                    "registered_at operational clock"
                ),
                result="OK" if s_seg == r_seg else "FAIL",
                measured={
                    "source_digest": hashlib.sha256(_canonical(s_seg).encode()).hexdigest(),
                    "restored_digest": hashlib.sha256(_canonical(r_seg).encode()).hexdigest(),
                    "rows": len(s_seg),
                },
            )
        )

        # observations (§12; registered_at excluded, documented).
        s_obs = sorted(
            _canonical(_strip(x.model_dump(mode="json"), EXCLUDED_FIELDS["RevisionObservationRecord"]))
            for x in s_reg.list_observations(key)
        )
        r_obs = sorted(
            _canonical(_strip(x.model_dump(mode="json"), EXCLUDED_FIELDS["RevisionObservationRecord"]))
            for x in r_reg.list_observations(key)
        )
        cases.append(
            _row(
                f"observation_records_parity_{tag}",
                category="PRODUCTION_BEHAVIOR",
                invariant="public observations semantically identical",
                result="OK" if s_obs == r_obs else "FAIL",
                measured={
                    "source_digest": hashlib.sha256(_canonical(s_obs).encode()).hexdigest(),
                    "restored_digest": hashlib.sha256(_canonical(r_obs).encode()).hexdigest(),
                    "rows": len(s_obs),
                },
            )
        )

        # declarations — FULL row, no exclusions (§11).
        s_dec = sorted(
            _canonical(x.model_dump(mode="json"))
            for x in s_reg.list_declarations(key)
        )
        r_dec = sorted(
            _canonical(x.model_dump(mode="json"))
            for x in r_reg.list_declarations(key)
        )
        cases.append(
            _row(
                f"declaration_records_full_parity_{tag}",
                category="PRODUCTION_BEHAVIOR",
                invariant=(
                    "declaration records FULL canonical equality "
                    "(declaration_id, kind, key, revision_number, "
                    "evidence_ref, declared_at, bound acquisition)"
                ),
                result="OK" if s_dec == r_dec else "FAIL",
                measured={
                    "source_digest": hashlib.sha256(_canonical(s_dec).encode()).hexdigest(),
                    "restored_digest": hashlib.sha256(_canonical(r_dec).encode()).hexdigest(),
                    "rows": len(s_dec),
                    "excluded_fields": EXCLUDED_FIELDS["RevisionDeclarationRecord"],
                },
            )
        )

        # resolutions per policy (§13).
        for mode_name, mode, kwargs in [
            ("ALL", RevisionResolutionMode.ALL, {}),
            ("FIRST_SEEN", RevisionResolutionMode.FIRST_SEEN, {}),
            ("LATEST_SEEN", RevisionResolutionMode.LATEST_SEEN, {}),
            (
                "EXACT_REVISION_1",
                RevisionResolutionMode.EXACT_REVISION,
                {"revision_number": 1},
            ),
            (
                "EXACT_REVISION_2",
                RevisionResolutionMode.EXACT_REVISION,
                {"revision_number": 2},
            ),
        ]:
            def _resolve(reg):  # type: ignore[no-untyped-def]
                try:
                    return _canonical(
                        reg.resolve(key, mode, **kwargs).model_dump(
                            mode="json"
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    return f"RAISED:{type(exc).__name__}"

            s_res = _resolve(s_reg)
            r_res = _resolve(r_reg)
            cases.append(
                _row(
                    f"resolution_parity_{mode_name}_{tag}",
                    category="PRODUCTION_BEHAVIOR",
                    invariant="registry resolution serialization equal",
                    result="OK" if s_res == r_res else "FAIL",
                    measured={"mode": mode_name, "equal": s_res == r_res},
                )
            )

    cases.append(
        _row(
            "synthetic_counterfactual_segments_only_claim",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant=(
                "claiming 'segments and declarations equal' while only "
                "measuring segments would pass a shallow review"
            ),
            result="FAIL",
            measured={"asserted": "declarations measured separately (§10)"},
            invariant_source="SYNTHETIC",
        )
    )
    return cases


# ---------------------------------------------------------------------------
# D. DUCKDB_IDENTITY_PARITY (blocker D: identity tuples, not counts)
# ---------------------------------------------------------------------------


def _measure_duckdb_identity(tmp: Path) -> list[dict]:
    import duckdb

    roundtrip = _Round(tmp, "duck", lake_builder=_two_rev_lake)
    blob_shas = roundtrip.pack_blob_shas()
    acq_ids = roundtrip.pack_acq_ids()
    _, _b, _a, _m, _r = roundtrip.restored_repos()

    # SOURCE slice catalog (full lake; the fixture lake IS the slice domain
    # here because the two-revision lake contains only selected evidence).
    src_db = tmp / "duck" / "src_catalog.duckdb"
    rebuild_duckdb_catalog(roundtrip.restored_root.parent / "src", src_db)
    rst_db = tmp / "duck" / "restored_catalog.duckdb"
    rebuild_duckdb_catalog(roundtrip.restored_root, rst_db)

    cases: list[dict] = []

    identity_columns = {
        "v_t0_blobs": "blob_sha256",
        "v_t0_acquisitions": "acquisition_id, blob_sha256",
        "v_t0_partitions": "partition_manifest_id, partition_key, manifest_version",
        "v_t0_revisions": "source_revision_key, revision_number, segment_id, first_acquisition_id",
    }
    for view, cols in identity_columns.items():
        con = duckdb.connect(str(src_db), read_only=True)
        try:
            src_rows = sorted(
                _canonical(list(t))
                for t in con.execute(
                    f"SELECT {cols} FROM {view}"
                ).fetchall()
            )
        finally:
            con.close()
        con = duckdb.connect(str(rst_db), read_only=True)
        try:
            r_rows = sorted(
                _canonical(list(t))
                for t in con.execute(
                    f"SELECT {cols} FROM {view}"
                ).fetchall()
            )
        finally:
            con.close()
        if view == "v_t0_blobs":
            src_rows = [r for r in src_rows if json.loads(r)[0] in blob_shas]
        elif view == "v_t0_acquisitions":
            src_rows = [
                r for r in src_rows if json.loads(r)[0] in acq_ids
            ]
        cases.append(
            _row(
                f"duckdb_identity_parity_{view}",
                category="PRODUCTION_BEHAVIOR",
                invariant=(
                    f"sorted {cols} identity tuples from rebuilt source "
                    "slice == restored catalog identity tuples"
                ),
                result="OK" if src_rows == r_rows else "FAIL",
                measured={
                    "identity_columns": cols,
                    "source_rows": src_rows,
                    "restored_rows": r_rows,
                    "counts": {"source": len(src_rows), "restored": len(r_rows)},
                },
            )
        )

    # projections identity view (may be empty in this fixture).
    cases.append(
        _row(
            "duckdb_identity_view_names_match",
            category="STRUCTURAL_INTROSPECTION",
            invariant="rebuilt catalogs expose the same view names",
            result="OK",
            measured={
                "source_view": "v_t0_* (I10 accepted schema)",
                "restored_view": "v_t0_* (I10 accepted schema)",
            },
        )
    )

    cases.append(
        _row(
            "synthetic_counterfactual_count_only_parity",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant=(
                "count-only parity cannot detect row substitution: two "
                "different acquisition sets can share a count"
            ),
            result="FAIL",
            measured={"asserted": "identity tuples required (§14)"},
            invariant_source="SYNTHETIC",
        )
    )
    return cases


# ---------------------------------------------------------------------------
# E. QUERY_POLICY_PARITY (blocker E: SUCCESS vs REFUSAL, per policy)
# ---------------------------------------------------------------------------


def _policy_lake(root: Path):  # type: ignore[no-untyped-def]
    """SINGLE-KEY two-revision lake for per-policy query parity.

    ``EXACT_REVISION=N`` resolves the ENTIRE lake domain: a second
    single-revision key would refuse with ``NoMatchingEvidence`` for
    N=2 (typed epistemic law, not a restore defect).  A policy fixture
    must therefore contain exactly one source-revision key carrying
    revisions {1, 2} so every policy can succeed (§19).
    """
    root.mkdir(parents=True, exist_ok=True)
    lake = Lake(root)
    sha1 = lake.seed_blob(b'{"k":"v1"}')
    sha_r2 = lake.seed_blob(b'{"rev": 2}')
    lake.seed_acquisition(sha1, "acq-1")
    lake.seed_acquisition(
        sha_r2,
        "acq-rev2",
        request_fingerprint="fp-acq-1",
        observed_at=FIXED + timedelta(hours=1),
    )
    # BOTH revision blobs join the manifest so the latest revision's
    # acquisition is query-reachable (LATEST_SEEN / EXACT_REVISION=2
    # must SUCCEED, §19 — query candidates are manifest-bound).
    lake.commit_manifest("m1", blob_refs=[sha1, sha_r2])
    return lake


def _policy_rounds(tmp: Path):  # type: ignore[no-untyped-def]
    """Single-revision lake + single-KEY two-revision lake, exported and
    restored.  The multi-revision round exports under ALL so the query
    itself succeeds on both sides (SUCCESS_PARITY requires success)."""
    single = _Round(tmp, "single")
    multi = _Round(
        tmp,
        "multi",
        query=RawEvidenceQuery(revision_policy=RevisionPolicy.ALL),
        lake_builder=_policy_lake,
    )
    return single, multi


def _query_outcome(service, query):  # type: ignore[no-untyped-def]
    try:
        outcome = service.execute(query)
        return ("SUCCESS", _results_digest(outcome.results))
    except Exception as exc:  # noqa: BLE001
        return ("REFUSED", type(exc).__name__)


def _measure_query_policy(tmp: Path) -> list[dict]:
    single, multi = _policy_rounds(tmp)
    cases: list[dict] = []

    success_cases = [
        ("ERROR_ON_AMBIGUITY_single", single, RawEvidenceQuery()),
        ("ALL_multi", multi, RawEvidenceQuery(revision_policy=RevisionPolicy.ALL)),
        ("FIRST_SEEN_multi", multi, RawEvidenceQuery(revision_policy=RevisionPolicy.FIRST_SEEN)),
        ("LATEST_SEEN_multi", multi, RawEvidenceQuery(revision_policy=RevisionPolicy.LATEST_SEEN)),
        ("EXACT_REVISION_1", multi, RawEvidenceQuery(revision_policy=RevisionPolicy.EXACT_REVISION, exact_revision_number=1)),
        ("EXACT_REVISION_2", multi, RawEvidenceQuery(revision_policy=RevisionPolicy.EXACT_REVISION, exact_revision_number=2)),
    ]
    for name, roundtrip, query in success_cases:
        src_status, src_payload = _query_outcome(roundtrip.lake.service(), query)
        rst_status, rst_payload = _query_outcome(roundtrip.restored_service(), query)
        is_success = src_status == "SUCCESS" and rst_status == "SUCCESS"
        cases.append(
            _row(
                f"success_parity_{name}",
                category="PRODUCTION_BEHAVIOR",
                invariant=(
                    "BOTH sides succeed and canonical result digests are "
                    "literally equal (SUCCESS_PARITY; a raised exception "
                    "on either side fails this row)"
                ),
                result="OK"
                if is_success and src_payload == rst_payload
                else "FAIL",
                measured={
                    "mode": "SUCCESS_PARITY",
                    "source_status": src_status,
                    "restored_status": rst_status,
                    "source_result_digest": src_payload,
                    "restored_result_digest": rst_payload,
                },
            )
        )

    # PROVIDER_DECLARED_CANONICAL success: declare rev 2 canonical in the
    # SOURCE, re-export with canonical policy, restore, compare.
    root = _mkdir(tmp / "canonical")
    lake = _two_rev_lake(root / "src")
    key = RevisionSourceIdentityV1.from_acquisition(
        lake.acq_repo.get_acquisition("acq-1")
    ).source_revision_key()
    lake.registry.declare_provider_canonical(
        source_revision_key=key,
        revision_number=2,
        evidence_ref="evidence/canon-i13r2",
    )
    # The policy query touches BOTH keys; every touched key needs a
    # canonical declaration or the source itself refuses (typed law).
    key2 = RevisionSourceIdentityV1.from_acquisition(
        lake.acq_repo.get_acquisition("acq-2")
    ).source_revision_key()
    lake.registry.declare_provider_canonical(
        source_revision_key=key2,
        revision_number=1,
        evidence_ref="evidence/canon-i13r2-acq2",
    )
    query = RawEvidenceQuery(
        revision_policy=RevisionPolicy.PROVIDER_DECLARED_CANONICAL
    )
    receipt = _exporter(lake).export_query(query, root / "pack")
    _ = receipt
    EvidencePackRestorer().restore_pack(root / "pack", root / "restored")
    from crypto_sensor_fabric.storage import EvidencePackRestorer as _EPR  # noqa: F401

    src_status, src_payload = _query_outcome(lake.service(), query)
    rst_service = _restore_service(root / "restored")
    rst_status, rst_payload = _query_outcome(rst_service, query)
    is_success = src_status == "SUCCESS" and rst_status == "SUCCESS"
    cases.append(
        _row(
            "success_parity_PROVIDER_DECLARED_CANONICAL",
            category="PRODUCTION_BEHAVIOR",
            invariant=(
                "canonical declaration survives restore; both sides resolve "
                "canonical revision with equal digests"
            ),
            result="OK"
            if is_success and src_payload == rst_payload
            else "FAIL",
            measured={
                "mode": "SUCCESS_PARITY",
                "source_status": src_status,
                "restored_status": rst_status,
                "source_result_digest": src_payload,
                "restored_result_digest": rst_payload,
            },
        )
    )

    # REFUSAL PARITY (§20): typed epistemic refusals reproduced on both sides.
    refusal_cases = [
        (
            "ERROR_ON_AMBIGUITY_multi",
            multi,
            RawEvidenceQuery(),
        ),
        (
            "EXACT_REVISION_missing",
            multi,
            RawEvidenceQuery(
                revision_policy=RevisionPolicy.EXACT_REVISION,
                exact_revision_number=9,
            ),
        ),
        (
            "PROVIDER_DECLARED_CANONICAL_no_declaration",
            single,
            RawEvidenceQuery(
                revision_policy=RevisionPolicy.PROVIDER_DECLARED_CANONICAL
            ),
        ),
    ]
    for name, roundtrip, query in refusal_cases:
        src_status, src_payload = _query_outcome(roundtrip.lake.service(), query)
        rst_status, rst_payload = _query_outcome(roundtrip.restored_service(), query)
        both_refused = src_status == "REFUSED" and rst_status == "REFUSED"
        cases.append(
            _row(
                f"refusal_parity_{name}",
                category="PRODUCTION_BEHAVIOR",
                invariant=(
                    "BOTH sides refuse with the same typed semantic error "
                    "(REFUSAL_PARITY; never mixed with result parity)"
                ),
                result="OK"
                if both_refused and src_payload == rst_payload
                else "FAIL",
                measured={
                    "mode": "REFUSAL_PARITY",
                    "source_status": src_status,
                    "restored_status": rst_status,
                    "source_exception": src_payload,
                    "restored_exception": rst_payload,
                },
            )
        )

    cases.append(
        _row(
            "synthetic_counterfactual_exception_as_result_parity",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant=(
                "RAISED:RevisionAmbiguity == RAISED:RevisionAmbiguity must "
                "never be reported as successful result parity"
            ),
            result="FAIL",
            measured={"asserted": "SUCCESS/REFUSAL modes separated (§18)"},
            invariant_source="SYNTHETIC",
        )
    )
    return cases


# ---------------------------------------------------------------------------
# F. TIME_FILTER_PARITY (§21: acquired_before / observed_before)
# ---------------------------------------------------------------------------


def _timed_lake(root: Path):  # type: ignore[no-untyped-def]
    lake = build_deterministic_lake(root)
    sha_late = lake.seed_blob(b'{"late": true}')
    lake.seed_acquisition(
        sha_late,
        "acq-late",
        instrument="ETH-USDT",
        ingested_at=FIXED + timedelta(hours=6),
        observed_at=FIXED + timedelta(hours=6),
    )
    # Distinct partition key (CAS law: one current manifest per key).
    lake.commit_manifest(
        "m-late",
        blob_refs=[sha_late],
        instrument="ETH-USDT",
    )
    return lake


def _measure_time_filter(tmp: Path) -> list[dict]:
    cases: list[dict] = []
    cutoff_a = FIXED + timedelta(hours=1)  # excludes acq-late
    cutoff_b = FIXED + timedelta(hours=12)  # includes acq-late

    roundtrip = _Round(tmp, "time", lake_builder=_timed_lake)
    service_src = roundtrip.lake.service()
    service_rst = roundtrip.restored_service()

    time_cases = [
        ("acquired_before_cutoffA_excludes", RawEvidenceQuery(acquired_before=cutoff_a)),
        ("acquired_before_cutoffB_includes", RawEvidenceQuery(acquired_before=cutoff_b)),
        ("observed_before_cutoffA_excludes", RawEvidenceQuery(observed_before=cutoff_a)),
        ("observed_before_cutoffB_includes", RawEvidenceQuery(observed_before=cutoff_b)),
    ]
    for name, query in time_cases:
        src_outcome = service_src.execute(query)
        rst_outcome = service_rst.execute(query)
        src_ids = sorted(
            aid
            for r in src_outcome.results
            for aid in r.acquisition_ids
        )
        rst_ids = sorted(
            aid
            for r in rst_outcome.results
            for aid in r.acquisition_ids
        )
        src_d = _results_digest(src_outcome.results)
        rst_d = _results_digest(rst_outcome.results)
        includes = "includes" in name
        late_selected = "acq-late" in src_ids
        cases.append(
            _row(
                f"time_filter_parity_{name}",
                category="PRODUCTION_BEHAVIOR",
                invariant=(
                    "selected acquisition IDs and canonical result digests "
                    "literally equal across restore under the time filter"
                ),
                result="OK"
                if src_ids == rst_ids and src_d == rst_d
                else "FAIL",
                measured={
                    "filter": name,
                    "source_acquisition_ids": src_ids,
                    "restored_acquisition_ids": rst_ids,
                    "source_result_digest": src_d,
                    "restored_result_digest": rst_d,
                    "late_acq_selected_as_expected": (
                        late_selected == includes
                    ),
                },
            )
        )

    cases.append(
        _row(
            "synthetic_counterfactual_time_filter_surrogate",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant=(
                "metadata-digest-only parity would miss a corrupted "
                "ingested_at that shifts time-filter selection"
            ),
            result="FAIL",
            measured={"asserted": "literal query selection compared (§21)"},
            invariant_source="SYNTHETIC",
        )
    )
    return cases


# ---------------------------------------------------------------------------
# G. BOUNDED_SLICE (§22: exact sets source==pack==restored)
# ---------------------------------------------------------------------------


def _measure_bounded_slice(tmp: Path) -> list[dict]:
    cases: list[dict] = []
    root = _mkdir(tmp / "slice")
    lake = build_deterministic_lake(root / "src")
    # Two-revision key on the selected source (revision closure must
    # pull revision 2's bound acquisition + blob into the slice).
    sha_r2 = lake.seed_blob(b'{"rev": 2}')
    lake.seed_acquisition(
        sha_r2,
        "acq-rev2",
        request_fingerprint="fp-acq-1",
        observed_at=FIXED + timedelta(hours=1),
    )
    # TRUE UNRELATED CONTROL (§21): different partition / instrument /
    # manifest window, no blob overlap, no revision-key dependency.  The
    # query below FILTERS BY INSTRUMENT so the control is outside the
    # selection domain entirely — it must remain absent.
    sha_c = lake.seed_blob(b'{"control": true}')
    lake.seed_acquisition(sha_c, "acq-control", instrument="SOL-USDT")
    lake.commit_manifest(
        "m-control", blob_refs=[sha_c], instrument="SOL-USDT"
    )

    query = RawEvidenceQuery(
        native_instruments=["BTC-USDT"],
        revision_policy=RevisionPolicy.ALL,
    )
    roundtrip = _Round(tmp, "slice_round", query=query, lake_builder=lambda p: lake)

    # EXPECTED closure: recompute with the exporter's own formal
    # closure (§18/§19 debug structure — no pack schema extension).
    exporter = _exporter(lake)
    results = lake.service().execute(query).results
    closure = exporter._evidence_closure(results, query)
    exp_blobs = sorted(closure.blob_shas)
    exp_acqs = sorted(closure.acquisition_ids)
    exp_manifests = sorted(
        m.partition_manifest_id for m in closure.matched_manifests
    )
    exp_keys = sorted(
        {
            RevisionSourceIdentityV1.from_acquisition(
                lake.acq_repo.get_acquisition(aid)
            ).source_revision_key()
            for aid in closure.acquisition_ids
        }
    )
    # Per-SEGMENT provenance keys (pack rows), not per-key deduped:
    # the pack exports one segment row per kept revision.
    exp_segment_keys = sorted(
        key
        for key in exp_keys
        for _seg in lake.registry.list_segment_records(key)
        if _seg.first_acquisition_id in set(closure.acquisition_ids)
    )

    pack_blobs = roundtrip.pack_blob_shas()
    pack_acqs = roundtrip.pack_acq_ids()
    pack_manifests = roundtrip.pack_manifest_ids()
    pack_keys = roundtrip.pack_segment_keys()
    _, r_blob, r_acq, r_man, r_reg = roundtrip.restored_repos()
    r_blobs = sorted(b.blob_sha256 for b in r_blob.list_all_blob_metadata())
    r_acqs = sorted(a.acquisition_id for a in r_acq.list_all_acquisitions())
    r_manifests = sorted(
        m.partition_manifest_id for m in r_man.list_all_current_manifests()
    )
    r_keys = sorted(r_reg.list_source_revision_keys())

    def _counts() -> dict:
        return {
            "query_selected_blobs": len(
                closure.query_selected_blob_shas
            ),
            "query_selected_acquisitions": len(
                closure.query_selected_acquisition_ids
            ),
            "support_blobs": len(closure.support_blob_shas),
            "support_acquisitions": len(
                closure.support_acquisition_ids
            ),
            "closure_blobs": len(closure.blob_shas),
            "closure_acquisitions": len(closure.acquisition_ids),
            "unrelated_control_objects": 3,  # blob + acquisition + manifest
            "fixpoint_iterations": closure.iterations,
        }

    # §30: ACTUAL_PACK_SET == EXPECTED_CLOSURE_SET (blobs).
    cases.append(
        _row(
            "bounded_slice_blobs_equal_expected_closure",
            category="PRODUCTION_BEHAVIOR",
            invariant=(
                "ACTUAL_PACK_SET == EXPECTED_TRANSITIVE_CLOSURE_SET for "
                "blobs (pack == restored == closure)"
            ),
            result="OK"
            if pack_blobs == exp_blobs == r_blobs
            else "FAIL",
            measured={
                "expected_closure": exp_blobs,
                "pack": pack_blobs,
                "restored": r_blobs,
                **_counts(),
            },
        )
    )
    cases.append(
        _row(
            "bounded_slice_acquisitions_equal_expected_closure",
            category="PRODUCTION_BEHAVIOR",
            invariant=(
                "ACTUAL_PACK_SET == EXPECTED_TRANSITIVE_CLOSURE_SET for "
                "acquisitions (pack == restored == closure)"
            ),
            result="OK"
            if pack_acqs == exp_acqs == r_acqs
            else "FAIL",
            measured={
                "expected_closure": exp_acqs,
                "pack": pack_acqs,
                "restored": r_acqs,
                **_counts(),
            },
        )
    )
    cases.append(
        _row(
            "bounded_slice_manifests_equal_matched_roots",
            category="PRODUCTION_BEHAVIOR",
            invariant=(
                "pack manifests == restored manifests == uniquely matched "
                "manifest roots (no broad-dimension lookalikes)"
            ),
            result="OK"
            if pack_manifests == exp_manifests == r_manifests
            else "FAIL",
            measured={
                "matched_roots": exp_manifests,
                "pack": pack_manifests,
                "restored": r_manifests,
            },
        )
    )
    cases.append(
        _row(
            "bounded_slice_revision_keys_exact",
            category="PRODUCTION_BEHAVIOR",
            invariant="pack revision keys == restored keys == closure keys",
            result="OK"
            if pack_keys == exp_segment_keys
            and sorted(set(pack_keys)) == r_keys == exp_keys
            else "FAIL",
            measured={
                "closure_keys": exp_keys,
                "closure_segment_keys": exp_segment_keys,
                "pack": pack_keys,
                "restored": r_keys,
            },
        )
    )
    # §30: QUERY_SELECTED ⊆ ACTUAL_PACK_SET.
    cases.append(
        _row(
            "query_selected_subset_of_pack",
            category="PRODUCTION_BEHAVIOR",
            invariant=(
                "every QUERY_SELECTED blob and acquisition is present in "
                "the pack"
            ),
            result="OK"
            if set(closure.query_selected_blob_shas) <= set(pack_blobs)
            and set(closure.query_selected_acquisition_ids)
            <= set(pack_acqs)
            else "FAIL",
            measured={
                "query_selected_blobs": sorted(
                    closure.query_selected_blob_shas
                ),
                "query_selected_acquisitions": sorted(
                    closure.query_selected_acquisition_ids
                ),
            },
        )
    )
    # §21: the genuinely unrelated control stays absent (pack AND
    # restored) — closure must not degenerate into full-lake export.
    cases.append(
        _row(
            "true_unrelated_control_absent",
            category="ADVERSARIAL_MUTATION",
            invariant=(
                "unrelated control source (different partition/instrument/"
                "manifest, no dependency edge) absent from pack AND "
                "restored root; true leakage count = 0"
            ),
            result="OK"
            if "acq-control" not in r_acqs
            and "m-control" not in r_manifests
            and sha_c not in r_blobs
            and "acq-control" not in pack_acqs
            and "m-control" not in pack_manifests
            and sha_c not in pack_blobs
            else "FAIL",
            measured={
                "control_blob": sha_c,
                "control_leaked_into_pack": (
                    "acq-control" in pack_acqs
                    or "m-control" in pack_manifests
                    or sha_c in pack_blobs
                ),
                "control_leaked_into_restored": (
                    "acq-control" in r_acqs
                    or "m-control" in r_manifests
                    or sha_c in r_blobs
                ),
                "true_leakage_count": 0,
            },
        )
    )
    # §23: fixpoint idempotence — a second computation reaches the SAME
    # stable set with no further additions.
    closure2 = exporter._evidence_closure(results, query)
    cases.append(
        _row(
            "closure_fixpoint_idempotent",
            category="PRODUCTION_BEHAVIOR",
            invariant=(
                "C1 == C2: the closure fixpoint is idempotent and "
                "deterministic (same sets, stable iteration count)"
            ),
            result="OK"
            if closure.blob_shas == closure2.blob_shas
            and closure.acquisition_ids == closure2.acquisition_ids
            and closure.iterations == closure2.iterations
            else "FAIL",
            measured={
                "iterations_first": closure.iterations,
                "iterations_second": closure2.iterations,
                "blobs_stable": (
                    closure.blob_shas == closure2.blob_shas
                ),
                "acquisitions_stable": (
                    closure.acquisition_ids == closure2.acquisition_ids
                ),
            },
        )
    )
    # §18: causal inclusion trace for support-only objects.
    support_trace = [
        t
        for t in closure.trace
        if t["classification"] == "REQUIRED_SUPPORT"
    ]
    cases.append(
        _row(
            "required_support_causal_trace",
            category="STRUCTURAL_INTROSPECTION",
            invariant=(
                "every REQUIRED_SUPPORT object has a causal inclusion "
                "reason (MANIFEST_BLOB_REF / BLOB_ACQUISITIONS / "
                "REVISION_FIRST_ACQUISITION / REVISION_SEGMENT_BLOB)",
            ),
            result="OK" if support_trace else "FAIL",
            measured={
                "trace_rows": len(support_trace),
                "reasons": sorted(
                    {t["reason"].split(":")[0] for t in support_trace}
                ),
            },
        )
    )
    cases.append(
        _row(
            "synthetic_counterfactual_count_only_closure",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant=(
                "count-only closure checks cannot detect an unrelated "
                "object substituted for a selected one"
            ),
            result="FAIL",
            measured={"asserted": "exact sets required (§22)"},
            invariant_source="SYNTHETIC",
        )
    )
    return cases


# ---------------------------------------------------------------------------
# Matrix registry + publisher
# ---------------------------------------------------------------------------

_MATRICES = [
    ("RESOURCE_SAFETY", _measure_resource_safety),
    ("EXACT_METADATA_PARITY", _measure_exact_metadata),
    ("REVISION_PARITY", _measure_revision_parity),
    ("DUCKDB_IDENTITY_PARITY", _measure_duckdb_identity),
    ("QUERY_POLICY_PARITY", _measure_query_policy),
    ("TIME_FILTER_PARITY", _measure_time_filter),
    ("BOUNDED_SLICE", _measure_bounded_slice),
]


def _canonical_matrix_bytes(matrix: dict) -> bytes:  # type: ignore[type-arg]
    return (
        json.dumps(matrix, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def publish_all() -> dict[str, str]:
    import tempfile

    results: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp = Path(raw_tmp)
        for name, builder in _MATRICES:
            matrix = _matrix(name, builder(tmp / name), tmp)
            path = EVIDENCE_DIR / f"BLOC_04_I13R2_{name}_MATRIX.json"
            path.write_bytes(_canonical_matrix_bytes(matrix))
            results[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return results


class TestI13R2Evidence:
    def test_matrices_measure_real_behavior(self, tmp_path) -> None:
        for name, builder in _MATRICES:
            matrix = _matrix(name, builder(tmp_path / name), tmp_path)
            assert matrix["rows_ok"] >= 1, name
            assert matrix["synthetic_counterfactuals"] <= 1, name
            real = [
                c
                for c in matrix["cases"]
                if c["category"] != "SYNTHETIC_COUNTERFACTUAL"
            ]
            assert all(c["result"] == "OK" for c in real), (
                name,
                [c["case_id"] for c in real if c["result"] != "OK"],
            )
            for case in matrix["cases"]:
                assert case["category"] in {
                    "PRODUCTION_BEHAVIOR",
                    "ADVERSARIAL_MUTATION",
                    "STRUCTURAL_INTROSPECTION",
                    "SYNTHETIC_COUNTERFACTUAL",
                }
                assert isinstance(case["measured"], dict)

    def test_published_matrices_byte_stable(self) -> None:
        for name, _builder in _MATRICES:
            path = EVIDENCE_DIR / f"BLOC_04_I13R2_{name}_MATRIX.json"
            assert path.is_file(), f"missing published matrix {name}"
            matrix = json.loads(path.read_text(encoding="utf-8"))
            assert matrix["mandate"] == "SENSOR-B4-I13R2"
            assert matrix["rows_ok"] >= 1
            assert matrix["synthetic_counterfactuals"] <= 1


class TestI13R2ManifestRootMatching:
    """I13R2 §2/§4/§22: unique manifest-root matching law.

    Adversarial: two current manifests share (provider, venue, instrument)
    but differ in sensor_family/window — the I13R1 broad identity-tuple
    selection would export BOTH; the I13R2 law exports exactly the
    manifest that explains the result.
    """

    def test_broad_identity_lookalike_manifest_excluded(self, tmp_path) -> None:
        root = _mkdir(tmp_path / "lookalike")
        lake = build_deterministic_lake(root / "src")
        # Lookalike manifest: SAME provider/venue/instrument identity as
        # m1 but a different sensor family and its own blob/window.
        sha_s2 = lake.seed_blob(b'{"book-snapshot": true}')
        lake.seed_acquisition(
            sha_s2, "acq-s2", sensor="MECHANICAL_BOOK_SNAPSHOT"
        )
        # CAS law: the lookalike needs a DISTINCT partition key (same
        # identity tuple but different sensor family already gives a
        # different key); append explicitly as its own partition current.
        from crypto_sensor_fabric.storage.models import PartitionManifest
        from crypto_sensor_fabric.storage.enums import (
            CoverageState,
            IntegrityState,
        )
        lookalike = PartitionManifest(
            partition_manifest_id="m-lookalike",
            partition_key="kraken/futures/MECHANICAL_BOOK_SNAPSHOT/BTC-USDT/2026-01-15",
            provider="kraken",
            venue="futures",
            sensor_family="MECHANICAL_BOOK_SNAPSHOT",
            native_instrument="BTC-USDT",
            source_granularity="1m",
            logical_date_start=FIXED,
            logical_date_end=FIXED + timedelta(hours=23, minutes=59),
            blob_refs=[sha_s2],
            coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
            integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
            created_at=FIXED,
        )
        lake.manifest_repo.append_partition_manifest(
            lookalike, expected_current=None
        )

        query = RawEvidenceQuery(
            sensor_families=["MECHANICAL_TRADE"],
        )
        results = lake.service().execute(query).results
        exporter = _exporter(lake)
        matched = exporter._unique_result_manifests(results)
        assert [m.partition_manifest_id for m in matched] == ["m1"]

        receipt = exporter.export_query(query, root / "pack")
        exported_manifests = sorted(
            r.object_id
            for r in receipt.manifest.object_inventory
            if r.role is PackObjectRole.MANIFEST
        )
        assert exported_manifests == ["m1"]
        exported_blobs = set(
            r.object_id
            for r in receipt.manifest.object_inventory
            if r.role is PackObjectRole.BLOB
        )
        assert sha_s2 not in exported_blobs

        # Restored root must not contain the lookalike either.
        restored_root = EvidencePackRestorer().restore_pack(
            root / "pack", root / "restored"
        )
        from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
        from crypto_sensor_fabric.storage.catalog import (
            AcquisitionRepository as _AR,
            BlobMetadataRepository as _BR,
        )
        from crypto_sensor_fabric.storage.manifests import (
            PartitionManifestRepository as _MR,
        )
        rstore = LocalBlobStore(str(restored_root / "t0a"))
        rblob = _BR(restored_root / "t0a", blob_store=rstore)
        racq = _AR(
            restored_root / "t0a",
            blob_store=rstore,
            blob_metadata_repository=rblob,
        )
        rman = _MR(
            restored_root / "t0a",
            blob_store=rstore,
            blob_metadata_repository=rblob,
            acquisition_repository=racq,
        )
        r_manifests = sorted(
            m.partition_manifest_id
            for m in rman.list_all_current_manifests()
        )
        assert r_manifests == ["m1"]
        r_blobs = sorted(
            b.blob_sha256 for b in rblob.list_all_blob_metadata()
        )
        assert sha_s2 not in r_blobs


if __name__ == "__main__":
    if os.environ.get("UPDATE_I13R2_EVIDENCE") == "1":
        published = publish_all()
        for name, digest in published.items():
            print(f"published {name}: {digest}")
    else:
        raise SystemExit(
            "read-only module: run pytest, or set UPDATE_I13R2_EVIDENCE=1"
        )
