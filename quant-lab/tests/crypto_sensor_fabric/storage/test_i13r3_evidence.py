"""SENSOR-B4-I13R3 — nonvacuous DuckDB/T0B parity + fail-safe source boundary.

Operator-review correction for three I13R2 findings:

A. published DUCKDB_IDENTITY_PARITY rows were all EMPTY (0/0) — the
   builder rebuilt from the wrong root level.  Root law (I13R3 §3): the
   discovery root is the T0A storage root, and the accepted lake layout
   stores T0B projection catalogs in the SIBLING ``t0b`` tree, so the
   rebuild takes an explicit ``projection_root``.  A single-root
   rebuild of a T0B-bearing fixture fail-closes
   (DuckDBCatalogCorrupt) — the empty 0/0 "parity" rows are impossible
   by construction now.
B. published T0B exact-metadata parity was EMPTY — the fixture query
   used the ``include_t0b=False`` default.  I13R3 builds a real T0B
   roundtrip (artifact + context + lineage + schema + payload) with a
   versioned manifest (v2 supersedes v1) and proves literal parity,
   three-way payload SHA, and restored T0B query usability.
C. ``protected_source_roots`` defaulted to optional — a caller could
   omit T0B/revision protection by accident.  The exporter now DERIVES
   every wired dependency's source boundary through public read-only
   root accessors (I05/I06 repositories grew ``root`` properties) and
   FAILS CLOSED (ExportSourceBoundaryUnproven) when a wired dependency
   cannot prove its root.

Three matrices, append-only, byte-stable, at most one synthetic
counterfactual each:

- BLOC_04_I13R3_DUCKDB_NONVACUOUS_IDENTITY_MATRIX.json
- BLOC_04_I13R3_T0B_PARITY_MATRIX.json
- BLOC_04_I13R3_SOURCE_BOUNDARY_MATRIX.json
- BLOC_04_I13R3_EVIDENCE_CORRECTION.md

Historical I13/I13R1/I13R2 matrices are NOT modified (§18): the empty
I13R2 DuckDB/T0B rows remain the historical proof of what R2 measured.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
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
    RawEvidenceQuery,
)
from crypto_sensor_fabric.storage.catalog import (  # noqa: E402
    AcquisitionRepository,
    BlobMetadataRepository,
)
from crypto_sensor_fabric.storage.duckdb_catalog import (  # noqa: E402
    DuckDBCatalogCorrupt,
    rebuild_duckdb_catalog,
)
from crypto_sensor_fabric.storage.enums import (  # noqa: E402
    CoverageState,
    IntegrityState,
)
from crypto_sensor_fabric.storage.export import (  # noqa: E402
    ExportSourceBoundaryUnproven,
    read_pack_manifest,
)
from crypto_sensor_fabric.storage.manifests import (  # noqa: E402
    PartitionManifest,
    PartitionManifestRepository,
)
from crypto_sensor_fabric.storage.models import (  # noqa: E402
    AcquisitionRecord,
)
from crypto_sensor_fabric.storage.projection_lineage import (  # noqa: E402
    ProjectionLineageRepository,
)
from crypto_sensor_fabric.storage.projection_schema import (  # noqa: E402
    ProjectionSchemaRegistry,
    compute_schema_key,
)
from crypto_sensor_fabric.storage.projections import (  # noqa: E402
    ProjectionArtifactRepository,
    ProjectionContextRepository,
)
from crypto_sensor_fabric.storage.revisions import (  # noqa: E402
    RevisionSegmentRecord,
    SourceRevisionRegistry,
)

from crypto_sensor_fabric.storage.blob_store import LocalBlobStore  # noqa: E402

i13 = load_sibling("test_i13_export_restore", "test_i13_export_restore")
i13r2 = load_sibling("test_i13r2_evidence", "test_i13r2_evidence")

_exporter = i13._exporter
_restore_service = i13._restore_service
FIXED = i13.FIXED
ts = i13.ts

build_deterministic_lake = i13r2.build_deterministic_lake
_canonical = i13r2._canonical
_results_digest = i13r2._results_digest
_scrub = i13r2._scrub
def _row(  # type: ignore[no-untyped-def]
    case_id, *, invariant, result, measured,
    category="PRODUCTION_BEHAVIOR",
    invariant_source="PRODUCTION_MEASURED",
):
    return i13r2._row(
        case_id,
        category=category,
        invariant=invariant,
        result=result,
        measured=measured,
        invariant_source=invariant_source,
    )

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


# ---------------------------------------------------------------------------
# T0B fixture lake (I13R3 §8): real projection graph + versioned manifest.
# The T0B-aware manifest supersedes m1 as version 2 on the SAME partition
# key (CAS + no-gap version law); the projection resolver requires the
# manifest partition key to equal the projection partition key, which is
# what makes v2 the T0B manifest.
# ---------------------------------------------------------------------------


def build_t0b_lake(root: Path):  # type: ignore[no-untyped-def]
    lake = build_deterministic_lake(root)
    sha_a1 = lake.acq_repo.get_acquisition("acq-1").blob_sha256
    lake.commit_projection("proj-1", [(sha_a1, "acq-1")])
    manifest = PartitionManifest(
        partition_manifest_id="m-t0b",
        partition_key="kraken/futures/BTC-USDT/2026-01-15",
        provider="kraken",
        venue="futures",
        sensor_family="MECHANICAL_TRADE",
        native_instrument="BTC-USDT",
        source_granularity="1m",
        logical_date_start=ts(0),
        logical_date_end=ts(23, 59),
        blob_refs=[sha_a1],
        projection_refs=["proj-1"],
        coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
        integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
        created_at=FIXED,
        manifest_version=2,
        supersedes_manifest_id="m1",
    )
    repo = PartitionManifestRepository(
        root / "t0a",
        blob_store=lake.store,
        blob_metadata_repository=lake.blob_repo,
        acquisition_repository=lake.acq_repo,
        projection_lineage_resolver=lake.resolver,
        clock=lambda: FIXED,
    )
    repo.append_partition_manifest(manifest, expected_current=("m1", 1))
    return lake


def _t0b_query() -> RawEvidenceQuery:
    """The T0B query (§8): include_t0b=True — NOT the vacuous default."""
    return RawEvidenceQuery(include_t0b=True)


class T0BRoundtrip:
    """One T0B export + restore round-trip with repo/manifest facts."""

    def __init__(self, tmp: Path) -> None:
        root = _mkdir(tmp / "t0b_roundtrip")
        self.lake_root = root / "src"
        self.lake = build_t0b_lake(self.lake_root)
        self.query = _t0b_query()
        self.source_results = self.lake.service().execute(self.query).results
        self.receipt = _exporter(self.lake).export_query(
            self.query, root / "pack"
        )
        self.pack_root = root / "pack"
        self.manifest = read_pack_manifest(self.pack_root)
        self.restored_root = root / "restored"
        EvidencePackRestorer().restore_pack(
            self.pack_root, self.restored_root
        )
        self.restored_service = _restore_service(self.restored_root)
        self.restored_results = self.restored_service.execute(
            self.query
        ).results

    # -- pack inventory helpers --------------------------------------------

    def inventory(self) -> dict[PackObjectRole, list]:
        by_role: dict[PackObjectRole, list] = {}
        for rec in self.manifest.object_inventory:
            by_role.setdefault(rec.role, []).append(rec)
        return by_role

    def pack_bytes(self, rec) -> bytes:  # type: ignore[no-untyped-def]
        from crypto_sensor_fabric.storage.export import (
            _read_pack_metadata_bytes,
        )

        return _read_pack_metadata_bytes(self.pack_root / rec.pack_path)

    # -- restored repositories ----------------------------------------------

    def restored_repos(self):  # type: ignore[no-untyped-def]
        root = self.restored_root
        store = LocalBlobStore(str(root / "t0a"))
        blob = BlobMetadataRepository(root / "t0a", blob_store=store)
        acq = AcquisitionRepository(
            root / "t0a", blob_store=store, blob_metadata_repository=blob
        )
        schemas = ProjectionSchemaRegistry(
            root / "t0b" / "catalogs" / "projection_schemas"
        )
        artifacts = ProjectionArtifactRepository(
            root / "t0b" / "catalogs" / "manifests" / "projections",
            projection_root=root / "t0b",
            schema_registry=schemas,
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
        registry = SourceRevisionRegistry(
            root / "t0a" / "revisions",
            acquisition_repository=acq,
            blob_metadata_repository=blob,
            blob_store=store,
        )
        return (
            store,
            blob,
            acq,
            schemas,
            artifacts,
            contexts,
            lineage,
            registry,
        )


def _mkdir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _duck_rows(db_path: Path, view: str, cols: str) -> list[str]:
    """Sorted canonical identity tuples for ``view`` from a rebuilt catalog."""
    import duckdb

    con = duckdb.connect(str(db_path), read_only=True)
    try:
        return sorted(
            _canonical(list(t))
            for t in con.execute(f"SELECT {cols} FROM {view}").fetchall()
        )
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Matrix 1 — DUCKDB_NONVACUOUS_IDENTITY (§4/§5/§6/§20)
# ---------------------------------------------------------------------------

_DUCK_VIEWS: dict[str, str] = {
    "v_t0_blobs": "blob_sha256",
    "v_t0_acquisitions": "acquisition_id, blob_sha256",
    "v_t0_partitions": (
        "partition_manifest_id, partition_key, manifest_version"
    ),
    "v_t0_revisions": (
        "source_revision_key, revision_number, segment_id, "
        "first_acquisition_id"
    ),
    "v_t0_projections": "projection_id, projection_sha256",
}


def _expected_pack_identities(roundtrip: T0BRoundtrip) -> dict[str, list[str]]:
    """Per-view EXPECTED pack identity sets derived from pack inventory."""
    by_role = roundtrip.inventory()
    expected: dict[str, list[str]] = {}

    expected["v_t0_blobs"] = sorted(
        _canonical([rec.object_id])
        for rec in by_role.get(PackObjectRole.BLOB, [])
    )

    acq_pairs = sorted(
        (
            record.acquisition_id,
            record.blob_sha256,
        )
        for record in (
            AcquisitionRecord.model_validate_json(roundtrip.pack_bytes(rec))
            for rec in by_role.get(PackObjectRole.ACQUISITION, [])
        )
    )
    expected["v_t0_acquisitions"] = sorted(
        _canonical([acq_id, blob]) for acq_id, blob in acq_pairs
    )

    expected["v_t0_partitions"] = sorted(
        _canonical(
            [
                pm.partition_manifest_id,
                pm.partition_key,
                pm.manifest_version,
            ]
        )
        for pm in (
            PartitionManifest.model_validate_json(
                roundtrip.pack_bytes(rec)
            )
            for rec in by_role.get(PackObjectRole.MANIFEST, [])
        )
    )

    expected["v_t0_revisions"] = sorted(
        _canonical(
            [
                seg.source_revision_key,
                seg.revision_number,
                seg.segment_id,
                seg.first_acquisition_id,
            ]
        )
        for seg in (
            RevisionSegmentRecord.model_validate_json(
                roundtrip.pack_bytes(rec)
            )
            for rec in by_role.get(PackObjectRole.REVISION_SEGMENTS, [])
        )
    )

    expected["v_t0_projections"] = sorted(
        _canonical([rec.object_id, rec.provenance_ref])
        for rec in by_role.get(PackObjectRole.PROJECTION, [])
    )
    return expected


def _measure_duckdb_nonvacuous(tmp: Path) -> list[dict]:
    roundtrip = T0BRoundtrip(_mkdir(tmp / "duck"))

    src_db = _mkdir(tmp / "duck") / "src_catalog.duckdb"
    rst_db = _mkdir(tmp / "duck") / "restored_catalog.duckdb"
    # §3 root law: T0A discovery root + explicit T0B sibling projection
    # root (the accepted lake layout splits the trees).
    rebuild_duckdb_catalog(
        roundtrip.lake_root / "t0a",
        src_db,
        projection_root=roundtrip.lake_root / "t0b",
    )
    rebuild_duckdb_catalog(
        roundtrip.restored_root / "t0a",
        rst_db,
        projection_root=roundtrip.restored_root / "t0b",
    )

    expected = _expected_pack_identities(roundtrip)
    cases: list[dict] = []

    for view, cols in _DUCK_VIEWS.items():
        source_all = _duck_rows(src_db, view, cols)
        restored_rows = _duck_rows(rst_db, view, cols)
        expected_set = expected[view]
        # §6: source discovery filtered to the EXPECTED pack closure.
        if view == "v_t0_blobs":
            wanted = {json.loads(e)[0] for e in set(expected_set)}
            source_rows = [r for r in source_all if json.loads(r)[0] in wanted]
        elif view == "v_t0_acquisitions":
            wanted = set(expected_set)
            source_rows = [r for r in source_all if r in wanted]
        elif view == "v_t0_partitions":
            wanted = set(expected_set)
            source_rows = [r for r in source_all if r in wanted]
        elif view == "v_t0_revisions":
            wanted_segment_ids = {
                json.loads(e)[2] for e in set(expected_set)
            }
            source_rows = [
                r
                for r in source_all
                if json.loads(r)[2] in wanted_segment_ids
            ]
        else:  # v_t0_projections
            wanted = {json.loads(e)[0] for e in set(expected_set)}
            source_rows = [r for r in source_all if json.loads(r)[0] in wanted]

        ok = (
            len(source_rows) > 0
            and len(restored_rows) > 0
            and source_rows == restored_rows
            and restored_rows == expected_set
        )
        cases.append(
            _row(
                f"duckdb_nonvacuous_identity_{view}",
                invariant=(
                    f"{view}: sorted identity tuples [{cols}] with "
                    "source_count > 0 AND restored_count > 0, "
                    "SOURCE(filtered to pack closure) == "
                    "PACK_EXPECTED == RESTORED (§6 literal-set law; "
                    "empty==empty is not parity, §4)"
                ),
                result="OK" if ok else "FAIL",
                measured={
                    "view": view,
                    "identity_columns": cols,
                    "source_rows": source_rows,
                    "restored_rows": restored_rows,
                    "expected_pack_identity_set": expected_set,
                    "source_count": len(source_rows),
                    "restored_count": len(restored_rows),
                },
            )
        )

    # Single-root rebuild of a T0B-bearing fixture must FAIL CLOSED —
    # the I13R2 0/0 rows are impossible by construction now.
    single_root_db = _mkdir(tmp / "duck") / "single.duckdb"
    refused_type: str | None = None
    try:
        rebuild_duckdb_catalog(
            roundtrip.lake_root / "t0a", single_root_db
        )
    except DuckDBCatalogCorrupt as exc:  # noqa: PERF203
        refused_type = type(exc).__name__
        _ = str(exc)
    cases.append(
        _row(
            "duckdb_single_root_t0b_fixture_fail_closed",
            invariant=(
                "rebuilding from the T0A root WITHOUT the T0B projection "
                "root on a T0B-bearing fixture refuses typed "
                "(DuckDBCatalogCorrupt) — never a silent 0-projection "
                "catalog (I13R3 §3)"
            ),
            result="OK" if refused_type == "DuckDBCatalogCorrupt" else "FAIL",
            measured={
                "exception_type": refused_type or "NO_REFUSAL",
            },
        )
    )

    cases.append(
        _row(
            "synthetic_counterfactual_empty_equal_empty_parity",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant=(
                "empty==empty 'parity' (0 source rows, 0 restored rows) "
                "ratifies nothing: it cannot distinguish a correct slice "
                "from a total rebuild failure"
            ),
            result="FAIL",
            measured={"asserted": "nonvacuous counts required (§4)"},
            invariant_source="SYNTHETIC",
        )
    )
    return cases


# ---------------------------------------------------------------------------
# Matrix 2 — T0B_PARITY (§9/§10/§11/§21)
# ---------------------------------------------------------------------------


def _measure_t0b_parity(tmp: Path) -> list[dict]:
    roundtrip = T0BRoundtrip(_mkdir(tmp / "t0b"))
    projection_id = "proj-1"
    cases: list[dict] = []

    # Pre-export requirement (§8): the source query returns nonempty
    # projection_refs AND lineage_refs BEFORE export.
    src_r0 = roundtrip.source_results[0]
    cases.append(
        _row(
            "t0b_query_selects_nonempty_t0b_graph",
            invariant=(
                "include_t0b=True query returns results with nonempty "
                "projection_refs and lineage_refs BEFORE export (§8)"
            ),
            result="OK"
            if bool(src_r0.projection_refs) and bool(src_r0.lineage_refs)
            else "FAIL",
            measured={
                "results": len(roundtrip.source_results),
                "projection_refs": src_r0.projection_refs,
                "lineage_refs": src_r0.lineage_refs,
            },
        )
    )

    _store, _blob, _acq, r_schemas, r_art, r_ctx, r_lin, _reg = (
        roundtrip.restored_repos()
    )

    # 1. Artifact metadata parity (nonempty).
    s_artifact = roundtrip.lake.artifacts.get_strict(projection_id)
    r_artifact = r_art.get_strict(projection_id)
    s_art = _canonical(s_artifact.model_dump(mode="json"))
    r_art_row = _canonical(r_artifact.model_dump(mode="json"))
    cases.append(
        _row(
            "t0b_projection_artifact_nonempty_parity",
            invariant=(
                "RawProjectionArtifact canonical serialization literally "
                "equal with source rows > 0 AND restored rows > 0 (§9)"
            ),
            result="OK" if s_art == r_art_row and s_art else "FAIL",
            measured={
                "source_count": 1,
                "restored_count": 1,
                "source_digest": hashlib.sha256(s_art.encode()).hexdigest(),
                "restored_digest": hashlib.sha256(
                    r_art_row.encode()
                ).hexdigest(),
            },
        )
    )

    # 2. Context parity (nonempty).
    s_ctx = _canonical(roundtrip.lake.contexts.get_strict(projection_id).to_dict())
    r_ctx_row = _canonical(r_ctx.get_strict(projection_id).to_dict())
    cases.append(
        _row(
            "t0b_projection_context_nonempty_parity",
            invariant=(
                "ProjectionCatalogRecord context canonical serialization "
                "equal with nonempty rows on both sides (§9)"
            ),
            result="OK" if s_ctx == r_ctx_row and s_ctx else "FAIL",
            measured={
                "source_count": 1,
                "restored_count": 1,
                "source_digest": hashlib.sha256(s_ctx.encode()).hexdigest(),
                "restored_digest": hashlib.sha256(
                    r_ctx_row.encode()
                ).hexdigest(),
            },
        )
    )

    # 3. Lineage parity (nonempty).
    s_lin_rows = [
        e.model_dump(mode="json")
        for e in roundtrip.lake.lineage.get_by_projection(projection_id)
    ]
    r_lin_rows = [
        e.model_dump(mode="json") for e in r_lin.get_by_projection(projection_id)
    ]
    s_lin = _canonical(s_lin_rows)
    r_lin_row = _canonical(r_lin_rows)
    cases.append(
        _row(
            "t0b_projection_lineage_nonempty_parity",
            invariant=(
                "ProjectionLineage entries literally equal with "
                "source lineage rows > 0 AND restored rows > 0 (§9)"
            ),
            result="OK"
            if s_lin == r_lin_row and len(s_lin_rows) > 0
            else "FAIL",
            measured={
                "source_count": len(s_lin_rows),
                "restored_count": len(r_lin_rows),
                "source_digest": hashlib.sha256(s_lin.encode()).hexdigest(),
                "restored_digest": hashlib.sha256(
                    r_lin_row.encode()
                ).hexdigest(),
            },
        )
    )

    # 4. Schema parity (nonempty).
    schema_key = compute_schema_key(
        r_artifact.projection_schema_id,
        r_artifact.projection_schema_version,
    )
    s_def = roundtrip.lake.schemas.resolve(schema_key)
    r_def = r_schemas.resolve(schema_key)
    s_sch = _canonical(s_def.to_descriptor())
    r_sch = _canonical(r_def.to_descriptor())
    cases.append(
        _row(
            "t0b_projection_schema_nonempty_parity",
            invariant=(
                "ProjectionSchemaDefinition descriptors literally equal "
                "(fingerprint identity) with nonempty registries (§9)"
            ),
            result="OK" if s_sch == r_sch and s_sch else "FAIL",
            measured={
                "source_count": len(roundtrip.lake.schemas.list_keys()),
                "restored_count": len(r_schemas.list_keys()),
                "schema_fingerprint": r_def.schema_fingerprint,
            },
        )
    )

    # 5. Three-way payload SHA parity through PUBLIC physical readers.
    pack_payload_rec = next(
        rec
        for rec in roundtrip.inventory().get(
            PackObjectRole.PROJECTION_PAYLOAD, []
        )
        if rec.object_id == f"payload:{projection_id}"
    )
    with r_art.open_payload(projection_id) as handle:
        restored_payload_sha = hashlib.sha256(handle.read()).hexdigest()
    r_art.verify_physical(projection_id)
    three_way = (
        s_artifact.projection_sha256
        == pack_payload_rec.sha256
        == restored_payload_sha
    )
    cases.append(
        _row(
            "t0b_projection_payload_three_way_sha",
            invariant=(
                "source projection_sha256 == pack payload object sha256 == "
                "restored PHYSICAL payload sha256, physical verification "
                "through the public open_payload()/verify_physical() "
                "surface only — no path-based shortcut (§10)"
            ),
            result="OK" if three_way else "FAIL",
            measured={
                "source_sha256": s_artifact.projection_sha256,
                "pack_sha256": pack_payload_rec.sha256,
                "restored_physical_sha256": restored_payload_sha,
                "verify_physical": "OK",
            },
        )
    )

    # 6. Restored T0B query usability (§11).
    src_digest = _results_digest(roundtrip.source_results)
    rst_digest = _results_digest(roundtrip.restored_results)
    rst_r0 = roundtrip.restored_results[0]
    usable = (
        src_digest == rst_digest
        and bool(rst_r0.projection_refs)
        and bool(rst_r0.lineage_refs)
    )
    cases.append(
        _row(
            "t0b_query_result_digest_parity",
            invariant=(
                "canonical T0B query result digests equal source vs "
                "restored WITH nonempty projection_refs and "
                "lineage_refs on the restored side — the restored T0B "
                "graph is USABLE, not merely present (§11)"
            ),
            result="OK" if usable else "FAIL",
            measured={
                "source_result_digest": src_digest,
                "restored_result_digest": rst_digest,
                "restored_projection_refs": rst_r0.projection_refs,
                "restored_lineage_refs": rst_r0.lineage_refs,
            },
        )
    )

    cases.append(
        _row(
            "synthetic_counterfactual_vacuous_t0b_parity",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant=(
                "0 artifact rows == 0 artifact rows 'passes' an "
                "empty-set parity check while proving the T0B graph was "
                "never exported (the I13R2 finding)"
            ),
            result="FAIL",
            measured={"asserted": "nonempty rows required (§9)"},
            invariant_source="SYNTHETIC",
        )
    )
    return cases


# ---------------------------------------------------------------------------
# Matrix 3 — SOURCE_BOUNDARY (§12/§13/§15/§16/§22)
# ---------------------------------------------------------------------------


def _attempt_export(exporter, destination: Path) -> str:
    """Return 'EXPORTED' or the exception type name."""
    try:
        exporter.export_query(RawEvidenceQuery(), destination)
        return "EXPORTED"
    except Exception as exc:  # noqa: BLE001
        return type(exc).__name__


def _measure_source_boundary(tmp: Path) -> list[dict]:
    root = _mkdir(tmp / "boundary")
    lake = build_deterministic_lake(root / "src")
    # Canonical composition (i13._exporter) passes NO protected_source_roots
    # — protection must be derived (§16 fail-safe default).
    exporter = _exporter(lake)
    cases: list[dict] = []

    t0a = root / "src" / "t0a"
    t0b = root / "src" / "t0b"

    refusal_families: list[tuple[str, Path]] = [
        ("T0A blob root (equal)", t0a),
        ("T0A blob root (child)", t0a / "objects"),
        ("T0A catalog root (child)", t0a / "catalogs" / "manifests"),
        ("revision registry root (equal)", t0a / "revisions"),
        ("T0B projection payload root (equal)", t0b),
        ("T0B projection payload root (child)", t0b / "projections"),
        ("T0B projection catalog (child)", t0b / "catalogs" / "manifests" / "projections"),
        ("T0B schema catalog (child)", t0b / "catalogs" / "projection_schemas"),
        ("T0B context catalog (child)", t0b / "catalogs" / "manifests" / "projection_context"),
        ("T0B lineage catalog (child)", t0b / "catalogs" / "manifests" / "projection_lineage"),
    ]
    for label, destination in refusal_families:
        outcome = _attempt_export(exporter, destination)
        refused = outcome in (
            "ExportDestinationUnsafe",
            "ExportPackExists",
        )
        cases.append(
            _row(
                f"destination_overlap_refused_{label.split(' (')[0].lower().replace(' ', '_')}",
                invariant=(
                    f"destination {label} is refused without any caller "
                    "override — protection derived from wired source "
                    "boundaries (I13R3 §16)"
                ),
                result="OK" if refused else "FAIL",
                measured={
                    "source_boundary": label,
                    "attempted_destination": str(destination),
                    "exception_type": outcome,
                },
            )
        )

    # Symlink resolving into a protected root (§16).  On platforms
    # without symlink privilege the always-running structural equivalent
    # (the destination parent-chain symlink guard in _validate_destination)
    # is measured instead (§24).
    link = root / "link-into-source"
    outcome: str | None = None
    structural_equivalent = False
    try:
        os.symlink(t0a, link, target_is_directory=True)
        outcome = _attempt_export(exporter, link / "pack")
    except OSError:
        structural_equivalent = True
        outcome = None
    if structural_equivalent:
        guard_count = EXPORT_SOURCE.count("is_symlink")
        cases.append(
            _row(
                "destination_symlink_into_source_structural_equivalent",
                category="STRUCTURAL_INTROSPECTION",
                invariant=(
                    "symlink privilege unavailable on this platform; the "
                    "always-running structural equivalent (destination "
                    "parent-chain symlink guard) is present in the "
                    "production export boundary"
                ),
                result="OK" if guard_count >= 1 else "FAIL",
                measured={
                    "structural_equivalent": "is_symlink parent-chain guard",
                    "guard_occurrences": guard_count,
                },
            )
        )
    else:
        cases.append(
            _row(
                "destination_symlink_into_source_refused",
                invariant=(
                    "destination resolving THROUGH a symlink into a "
                    "protected source root is refused (§16)"
                ),
                result="OK"
                if outcome == "ExportDestinationUnsafe"
                else "FAIL",
                measured={
                    "source_boundary": "symlink -> T0A blob root",
                    "attempted_destination": str(link / "pack"),
                    "exception_type": outcome,
                },
            )
        )

    # Valid external destination success control (§22).
    control = _mkdir(root / "outside") / "pack"
    receipt = exporter.export_query(RawEvidenceQuery(), control)
    cases.append(
        _row(
            "external_destination_success_control",
            invariant=(
                "a destination outside every protected source boundary "
                "still exports (protection must not degenerate into "
                "refusing everything)"
            ),
            result="OK" if receipt.object_count > 0 else "FAIL",
            measured={
                "destination": str(control),
                "object_count": receipt.object_count,
            },
        )
    )

    # §15 fail-closed constructor: a wired dependency that cannot prove
    # its root refuses composition with the typed configuration error.
    class _UnprovenRootRepo:
        """Duck-typed repository WITHOUT a public root accessor."""

        def __init__(self) -> None:
            self._hidden_root = "/internal/never/visible"

    from crypto_sensor_fabric.storage import EvidencePackExporter
    from crypto_sensor_fabric.storage.export import ExportLimits

    try:
        EvidencePackExporter(
            service=lake.service(),
            blob_store=lake.store,
            blob_metadata_repository=lake.blob_repo,
            acquisition_repository=lake.acq_repo,
            manifest_repository=lake.manifest_repo,
            artifact_repository=_UnprovenRootRepo(),  # type: ignore[arg-type]
            clock=lambda: FIXED,
            limits=ExportLimits(),
        )
        construction = "CONSTRUCTED"
    except ExportSourceBoundaryUnproven:
        construction = "ExportSourceBoundaryUnproven"
    cases.append(
        _row(
            "constructor_fail_closed_unproven_boundary",
            invariant=(
                "wiring a source dependency that cannot prove its "
                "filesystem root refuses CONSTRUCTION with "
                "ExportSourceBoundaryUnproven — silent omission of a "
                "root from protection is impossible (§15)"
            ),
            result="OK"
            if construction == "ExportSourceBoundaryUnproven"
            else "FAIL",
            measured={"construction_outcome": construction},
        )
    )

    # Private-access seal proof (§17/§25).
    seals = {
        "_segments_by_key": EXPORT_SOURCE.count("_segments_by_key"),
        "_declarations_by_key": EXPORT_SOURCE.count("_declarations_by_key"),
        "_projection_root": EXPORT_SOURCE.count("_projection_root"),
    }
    cases.append(
        _row(
            "private_access_seal_unchanged",
            invariant=(
                "export.py performs zero private-attribute access on "
                "I05/I06 internals (_segments_by_key/_declarations_by_key/"
                "_projection_root each occur 0 times) — the I13R1 public "
                "authority repair is not regressed (§17)"
            ),
            result="OK" if all(v == 0 for v in seals.values()) else "FAIL",
            measured=seals,
        )
    )

    cases.append(
        _row(
            "synthetic_counterfactual_opt_in_protection",
            category="SYNTHETIC_COUNTERFACTUAL",
            invariant=(
                "opt-in protection (protected_source_roots defaulting to "
                "[]) lets an accidental composition omit T0B/revision "
                "roots and write packs INTO the source tree"
            ),
            result="FAIL",
            measured={"asserted": "derived fail-closed boundaries (§15)"},
            invariant_source="SYNTHETIC",
        )
    )
    return cases


# ---------------------------------------------------------------------------
# Matrix registry + publisher
# ---------------------------------------------------------------------------

_MATRICES = [
    ("DUCKDB_NONVACUOUS_IDENTITY", _measure_duckdb_nonvacuous),
    ("T0B_PARITY", _measure_t0b_parity),
    ("SOURCE_BOUNDARY", _measure_source_boundary),
]


def _matrix(name: str, cases: list[dict], scrub_root: Path) -> dict:  # type: ignore[type-arg]
    scrubbed = [_scrub(c, scrub_root) for c in cases]
    return {
        "mandate": "SENSOR-B4-I13R3",
        "matrix": name,
        "measured_at_checkpoint": "I13R3",
        "corrects": (
            "SENSOR-B4-I13R2 operator-review findings A-C (vacuous "
            "DuckDB identity rows, vacuous T0B parity rows, optional "
            "source-root protection)"
        ),
        "rows_total": len(scrubbed),
        "rows_ok": sum(1 for c in scrubbed if c["result"] == "OK"),
        "rows_fail": sum(1 for c in scrubbed if c["result"] == "FAIL"),
        "synthetic_counterfactuals": sum(
            1
            for c in scrubbed
            if c["category"] == "SYNTHETIC_COUNTERFACTUAL"
        ),
        "cases": scrubbed,
    }


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
            path = EVIDENCE_DIR / f"BLOC_04_I13R3_{name}_MATRIX.json"
            path.write_bytes(_canonical_matrix_bytes(matrix))
            results[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    return results


class TestI13R3NonvacuousParity:
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
            path = EVIDENCE_DIR / f"BLOC_04_I13R3_{name}_MATRIX.json"
            assert path.is_file(), f"missing published matrix {name}"
            matrix = json.loads(path.read_text(encoding="utf-8"))
            assert matrix["mandate"] == "SENSOR-B4-I13R3"
            assert matrix["rows_ok"] >= 1
            assert matrix["synthetic_counterfactuals"] <= 1
            # Nonvacuity is a PUBLISHED property (§4): every identity row
            # must carry positive counts on both sides.
            for case in matrix["cases"]:
                counts = {
                    k: v
                    for k, v in case.get("measured", {}).items()
                    if k in ("source_count", "restored_count")
                }
                if len(counts) == 2:
                    assert counts["source_count"] > 0, (name, case["case_id"])
                    assert counts["restored_count"] > 0, (
                        name,
                        case["case_id"],
                    )


if __name__ == "__main__":
    if os.environ.get("UPDATE_I13R3_EVIDENCE") == "1":
        published = publish_all()
        for name, digest in published.items():
            print(f"published {name}: {digest}")
    else:
        raise SystemExit(
            "read-only module: run pytest, or set UPDATE_I13R3_EVIDENCE=1"
        )
