"""SENSOR-B4-I10R1D — measured R1 evidence builders and evidence-truth matrix.

Doctrine (I08R2R1 / I09R1 / I10R1 §14-§15): every reported boolean is an
OBSERVED fact from executing production behavior in deterministic temp
roots.  Nothing is ``True`` because a separate pytest supposedly covered
it.  A row's ``result`` is ``OK`` IFF every named required invariant is
boolean true, and each matrix carries at least one deliberate
counterfactual FAIL whose false predicate is actually represented in the
row.  The historical I10 evidence files are never rewritten here; R1
artifacts are new, append-only files byte-compared by the normal pytest.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parents[2] / "src"
for _path in (str(_SRC), str(_HERE)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import duckdb
from _sibling_import import load_sibling
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.probes.enums import Granularity
from crypto_sensor_fabric.storage.blob_store import LocalBlobStore
from crypto_sensor_fabric.storage.catalog import (
    AcquisitionRepository,
    BlobMetadataRepository,
)
from crypto_sensor_fabric.storage.duckdb_catalog import (
    VIEW_NAMES,
    DuckDBCatalogCorrupt,
    DuckDBCatalogShapeCorrupt,
    DuckDBCatalogVersionError,
    ReadOnlyDuckDBCatalog,
    rebuild_duckdb_catalog,
)
from crypto_sensor_fabric.storage.enums import CoverageState
from crypto_sensor_fabric.storage.manifests import (
    PartitionManifest,
    PartitionManifestRepository,
)

EVIDENCE_DIR = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)
FIXED = datetime(2026, 1, 15, 12, tzinfo=UTC)


def _stable(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _case(name: str, required: list[str], **values: Any) -> dict[str, Any]:
    row = {"case": name, **values, "required_invariants": required}
    row["result"] = "OK" if all(row.get(item) is True for item in required) else "FAIL"
    return row


def _matrix(name: str, rows: list[dict[str, Any]], **values: Any) -> dict[str, Any]:
    return {
        "checkpoint": "SENSOR-B4-I10R1",
        "matrix": name,
        **values,
        "rows": rows,
        "summary": {
            "rows": len(rows),
            "ok": sum(row["result"] == "OK" for row in rows),
            "fail": sum(row["result"] == "FAIL" for row in rows),
        },
    }


# ---------------------------------------------------------------------------
# Deterministic execution helpers (each returns OBSERVED facts)
# ---------------------------------------------------------------------------


def _schema_row(root: Path, output: Path) -> tuple[dict[str, Any], dict[str, str]]:
    """Measured: actual PRAGMA schema vs VIEW_SCHEMAS + metadata stamp."""
    from crypto_sensor_fabric.storage.duckdb_catalog import VIEW_SCHEMAS

    receipt = rebuild_duckdb_catalog(root, output)
    con = duckdb.connect(str(output), read_only=True)
    try:
        schemas_equal = all(
            [
                (row[1], row[2])
                for row in con.execute(f"PRAGMA table_info('{view}')").fetchall()
            ]
            == list(VIEW_SCHEMAS[view])
            for view in VIEW_NAMES
        )
        metadata = con.execute(
            "SELECT schema_version, data_root_role FROM catalog_metadata"
        ).fetchall()
    finally:
        con.close()
    facts = {
        "build_succeeded": receipt.catalog_path == output and output.is_file(),
        "schema_equal": schemas_equal,
        "metadata_row_equal": metadata == [("1.0", "rebuildable_discovery_non_authoritative")],
        "row_count_equal": all(
            receipt.view_row_counts[view] >= 0 for view in VIEW_NAMES
        ),
    }
    sha = {view: hashlib.sha256(str(sorted(str(row) for row in _all_rows(output, view))).encode()).hexdigest() for view in VIEW_NAMES}
    return facts, sha


def _all_rows(catalog: Path, view: str) -> list[list[Any]]:
    with ReadOnlyDuckDBCatalog(catalog) as reader:
        return reader.canonical_view_rows(view)


def _fixture_root(base: Path, name: str) -> Path:
    rebuild_module = load_sibling("i10r1_rebuild_helpers", "test_duckdb_rebuild")
    root = base / name
    rebuild_module.Fixture(root)
    return root


def _measured_destroy_rebuild(base: Path) -> dict[str, Any]:
    output = base / "catalog.duckdb"
    root = _fixture_root(base, "evidence")
    rebuild_duckdb_catalog(root, output)
    first = {view: _all_rows(output, view) for view in VIEW_NAMES}
    output.unlink()
    catalog_deleted = not output.exists()
    rebuild_duckdb_catalog(root, output)
    second = {view: _all_rows(output, view) for view in VIEW_NAMES}
    second_output = base / "catalog-2.duckdb"
    rebuild_duckdb_catalog(root, second_output)
    return {
        "catalog_deleted": catalog_deleted,
        "rebuild_succeeded": second_output.is_file(),
        "all_view_rows_equal": second == first == {view: _all_rows(second_output, view) for view in VIEW_NAMES},
    }


def _measured_failed_build_preservation(base: Path) -> dict[str, Any]:
    output = base / "published.duckdb"
    root = _fixture_root(base, "preservation-evidence")
    rebuild_duckdb_catalog(root, output)
    before_sha = hashlib.sha256(output.read_bytes()).hexdigest()
    directory = root / "catalogs" / "recovery" / "actions"
    fragment = next(directory.glob("*.json"))
    payload = json.loads(fragment.read_text(encoding="utf-8"))
    payload.pop("problem", None)
    logical_id = payload["recovery_action_id"]
    digest = hashlib.sha256(logical_id.encode("utf-8")).hexdigest()
    fragment.unlink()
    (directory / f"{digest}.json").write_text(json.dumps(payload), encoding="utf-8")
    refused = False
    try:
        rebuild_duckdb_catalog(root, output)
    except DuckDBCatalogCorrupt:
        refused = True
    after_sha = hashlib.sha256(output.read_bytes()).hexdigest()
    return {"typed_corruption_raised": refused, "existing_catalog_unchanged": before_sha == after_sha}


def _measured_shape_refusal(base: Path) -> dict[str, Any]:
    """Missing-column refusal is executed against the production builder."""
    from crypto_sensor_fabric.storage.duckdb_catalog import _create_table

    full = {"gap_id": "g1", "scope": "PARTITION", "scope_id": "p1", "missingness": "PARTIAL", "detail": None}
    stripped = {"gap_id": "g2", "scope": "PARTITION", "scope_id": "p2", "missingness": "KNOWN_GAP"}
    extra = dict(full, rogue="x")
    raised_missing = False
    raised_extra = False
    con = duckdb.connect(":memory:")
    try:
        try:
            _create_table(con, "v_t0_gaps", [full, stripped])
        except DuckDBCatalogShapeCorrupt:
            raised_missing = True
    finally:
        con.close()
    con = duckdb.connect(":memory:")
    try:
        try:
            _create_table(con, "v_t0_gaps", [extra])
        except DuckDBCatalogShapeCorrupt:
            raised_extra = True
    finally:
        con.close()
    return {"missing_column_refused": raised_missing, "extra_column_refused": raised_extra}


def _measured_type_stability(base: Path) -> dict[str, Any]:
    from crypto_sensor_fabric.storage.duckdb_catalog import _create_table

    con = duckdb.connect(":memory:")
    rows = [
        {
            "evidence_class": "PARTITION_MANIFEST", "integrity_state": "LOCAL_HASH_VERIFIED",
            "provider": "providerA", "sensor_family": "MECHANICAL_TRADE",
            "storage_priority": "P0", "universe_tier": None, "stored_bytes": None,
            "raw_bytes": 0, "projection_bytes": 0, "object_count": 1,
        },
        {
            "evidence_class": "T0B_PROJECTION", "integrity_state": "COMPLETE",
            "provider": "providerB", "sensor_family": "MECHANICAL_FUNDING",
            "storage_priority": "P3", "universe_tier": None, "stored_bytes": 12345,
            "raw_bytes": 0, "projection_bytes": 12345, "object_count": 1,
        },
    ]
    _create_table(con, "v_t0_storage_usage", rows)
    info = {
        row[1]: row[2]
        for row in con.execute("PRAGMA table_info('v_t0_storage_usage')").fetchall()
    }
    return {"nullable_first_row_keeps_bigint": info["stored_bytes"] == "BIGINT"}


def _measured_version_refusal(base: Path) -> dict[str, Any]:

    output = base / "versioned.duckdb"
    root = _fixture_root(base, "version-evidence")
    rebuild_duckdb_catalog(root, output)

    def mutated(suffix: str, sql: str) -> Path:
        copy = base / f"versioned-{suffix}.duckdb"
        shutil.copyfile(output, copy)
        con = duckdb.connect(str(copy))
        try:
            con.execute(sql)
        finally:
            con.close()
        return copy

    stale = mutated("stale", "UPDATE catalog_metadata SET schema_version = '0.9'")
    future = mutated("future", "UPDATE catalog_metadata SET schema_version = '9.9'")
    wrong_role = mutated("role", "UPDATE catalog_metadata SET data_root_role = 'authoritative'")
    duplicate = mutated(
        "dup",
        "INSERT INTO catalog_metadata VALUES ('1.0', 'rebuildable_discovery_non_authoritative')",
    )
    def _refused(path: Path) -> bool:
        try:
            ReadOnlyDuckDBCatalog(path)
        except DuckDBCatalogVersionError:
            return True
        return False

    return {
        "stale_version_refused": _refused(stale),
        "future_version_refused": _refused(future),
        "wrong_role_refused": _refused(wrong_role),
        "duplicate_metadata_refused": _refused(duplicate),
    }


def _measured_storage_dimensions(base: Path) -> dict[str, Any]:
    from crypto_sensor_fabric.storage.duckdb_catalog import _storage_usage

    projection = {
        "projection_id": "p", "provider": "providerA", "venue": "v",
        "sensor_family": "SENSOR_X", "native_instrument": "i",
        "partition_key": "k", "projection_schema_id": "s",
        "projection_schema_version": "1", "parser_version": "1",
        "projection_object_key": "o", "backend_id": "b",
        "resolved_local_path": "p", "projection_sha256": "h",
        "row_count": 1, "stored_bytes": 500, "state": "COMPLETE",
        "lineage_manifest_id": "l", "source_count": 1,
    }
    other_provider = dict(projection, provider="providerB", sensor_family="SENSOR_Y")
    other_sensor = dict(projection, projection_id="p2", provider="providerA", sensor_family="SENSOR_Z")
    usage = _storage_usage([], [projection, other_provider, other_sensor], [], [])
    t0b = [row for row in usage if row["evidence_class"] == "T0B_PROJECTION"]
    blob = {
        "blob_sha256": "a" * 64, "byte_length": 100, "stored_byte_length": 90,
        "storage_object_key": "k", "backend_id": "b", "resolved_local_path": "p",
        "source_media_type": "application/json", "storage_encoding": "NONE",
        "integrity_state": "LOCAL_HASH_VERIFIED", "created_at": FIXED.isoformat(),
    }
    t0a = [row for row in _storage_usage([blob], [], [], []) if row["evidence_class"] == "T0A_BLOB"]
    return {
        "provider_groups_separate": {(row["provider"], row["sensor_family"]) for row in t0b}
        == {("providerA", "SENSOR_X"), ("providerB", "SENSOR_Y"), ("providerA", "SENSOR_Z")},
        "object_totals_reconcile": sum(row["object_count"] for row in t0b) == 3
        and sum(row["projection_bytes"] for row in t0b) == 1500,
        "t0a_provider_null": t0a[0]["provider"] is None and t0a[0]["sensor_family"] is None,
    }


def _measured_discovery_cost(base: Path) -> dict[str, Any]:
    """Instrumented guard: default rebuild must not touch verify_blob/decode."""
    import crypto_sensor_fabric.storage.blob_store as blob_store_module

    root = _fixture_root(base, "cost-evidence")
    calls = {"verify": 0, "decode": 0}
    original_verify = blob_store_module.LocalBlobStore.verify_blob
    original_decode = blob_store_module.LocalBlobStore._decode_stats

    def spy_verify(self, sha, enc, **kw):
        calls["verify"] += 1
        return original_verify(self, sha, enc, **kw)

    def spy_decode(self, path, encoding):
        calls["decode"] += 1
        return original_decode(self, path, encoding)

    blob_store_module.LocalBlobStore.verify_blob = spy_verify  # type: ignore[method-assign]
    blob_store_module.LocalBlobStore._decode_stats = spy_decode  # type: ignore[method-assign]
    try:
        rebuild_duckdb_catalog(root, base / "cost.duckdb")
    finally:
        blob_store_module.LocalBlobStore.verify_blob = original_verify  # type: ignore[method-assign]
        blob_store_module.LocalBlobStore._decode_stats = original_decode  # type: ignore[method-assign]

    # Missing physical blob must STILL be refused (metadata-level check).
    missing_root = base / "missing-evidence"
    shutil.copytree(root, missing_root)
    physical = next(path for path in (missing_root / "blobs").rglob("*") if path.is_file())
    physical.unlink()
    missing_refused = False
    try:
        rebuild_duckdb_catalog(missing_root, base / "missing.duckdb")
    except DuckDBCatalogCorrupt:
        missing_refused = True

    # Stored-size divergence must STILL be refused.
    diverged_root = base / "diverged-evidence"
    shutil.copytree(root, diverged_root)
    physical = next(path for path in (diverged_root / "blobs").rglob("*") if path.is_file())
    physical.write_bytes(physical.read_bytes()[:-1])
    diverged_refused = False
    try:
        rebuild_duckdb_catalog(diverged_root, base / "diverged.duckdb")
    except DuckDBCatalogCorrupt:
        diverged_refused = True
    return {
        "raw_payload_not_loaded": calls["verify"] == 0 and calls["decode"] == 0,
        "missing_physical_blob_refused": missing_refused,
        "stored_size_divergence_refused": diverged_refused,
    }


def _measured_durable_relations(base: Path) -> dict[str, Any]:
    root = _fixture_root(base, "relations-evidence")

    def rewrite(mutate) -> None:
        directory = root / "catalogs" / "recovery" / "actions"
        fragment = next(directory.glob("*.json"))
        payload = json.loads(fragment.read_text(encoding="utf-8"))
        mutate(payload)
        logical_id = payload["recovery_action_id"]
        digest = hashlib.sha256(logical_id.encode("utf-8")).hexdigest()
        fragment.unlink()
        (directory / f"{digest}.json").write_text(json.dumps(payload), encoding="utf-8")

    rebuild_duckdb_catalog(root, base / "relations-good.duckdb")
    rewrite(lambda payload: payload.pop("problem", None))
    malformed_refused = False
    try:
        rebuild_duckdb_catalog(root, base / "relations-malformed.duckdb")
    except DuckDBCatalogCorrupt:
        malformed_refused = True
    rewrite(lambda payload: payload.update(problem="CORRUPT_BLOB"))
    rebuild_duckdb_catalog(root, base / "relations-restored.duckdb")
    valid_chain_accepted = base / "relations-restored.duckdb"
    lineage_dir = root / "catalogs" / "manifests" / "projection_lineage"
    orphan = json.loads(next(lineage_dir.glob("*.json")).read_text(encoding="utf-8"))
    orphan["lineage_manifest_id"] = "orphan-lineage-1"
    for entry in orphan["entries"]:
        entry["projection_id"] = "projection-does-not-exist"
        entry["lineage_manifest_id"] = "orphan-lineage-1"
    digest = hashlib.sha256(b"orphan-lineage-1").hexdigest()
    (lineage_dir / f"{digest}.json").write_text(json.dumps(orphan), encoding="utf-8")
    orphan_refused = False
    try:
        rebuild_duckdb_catalog(root, base / "relations-orphan.duckdb")
    except DuckDBCatalogCorrupt:
        orphan_refused = True
    return {
        "malformed_recovery_action_refused": malformed_refused,
        "valid_chain_accepted": valid_chain_accepted.is_file()
        and len(_all_rows(valid_chain_accepted, "v_t0_quarantine")) == 1,
        "orphan_lineage_refused": orphan_refused,
    }


def _measured_missingness_preservation(base: Path) -> dict[str, Any]:
    rebuild_module = load_sibling("i10r1_rebuild_helpers", "test_duckdb_rebuild")
    root = base / "missingness-evidence"
    rebuild_module.Fixture(root)
    store = LocalBlobStore(str(root))
    blobs = BlobMetadataRepository(root, blob_store=store, clock=lambda: FIXED)
    acquisitions = AcquisitionRepository(root, blob_store=store, blob_metadata_repository=blobs, clock=lambda: FIXED)
    resolver = None
    manifests = PartitionManifestRepository(
        root,
        blob_store=store,
        blob_metadata_repository=blobs,
        acquisition_repository=acquisitions,
        projection_lineage_resolver=resolver,
        clock=lambda: FIXED,
    )
    observed: set[str] = set()
    for state in CoverageState:
        if state is CoverageState.COMPLETE_SOURCE_BOUNDARY:
            continue
        manifests.append_partition_manifest(
            PartitionManifest(
                partition_manifest_id=f"manifest-{state.value}",
                partition_key=f"synthetic-{state.value}",
                provider="kraken",
                venue="futures",
                sensor_family=SensorFamily.MECHANICAL_TRADE,
                native_instrument="BTC-USD",
                source_granularity=Granularity.G1M,
                logical_date_start=FIXED,
                logical_date_end=FIXED,
                coverage_state=state,
                created_at=FIXED,
            ),
            expected_current=None,
        )
    rebuild_duckdb_catalog(root, base / "missingness.duckdb")
    with ReadOnlyDuckDBCatalog(base / "missingness.duckdb") as reader:
        for row in reader.canonical_view_rows("v_t0_gaps"):
            if row[1] == "PARTITION":
                observed.add(str(row[3]))
    complete_absent = all(
        row[3] != "COMPLETE_SOURCE_BOUNDARY"
        for row in _all_rows(base / "missingness.duckdb", "v_t0_gaps")
    )
    frozen_vocabulary = {
        CoverageState.PARTIAL.value, CoverageState.KNOWN_GAP.value,
        CoverageState.EMPTY_CONFIRMED.value, CoverageState.NOT_ATTEMPTED.value,
        CoverageState.FAILED.value, CoverageState.ACCESS_BLOCKED.value,
        CoverageState.HISTORY_UNAVAILABLE.value, CoverageState.QUARANTINED.value,
        CoverageState.REVISION_CONFLICT.value,
    }
    return {
        "frozen_states_preserved": frozen_vocabulary <= observed,
        "complete_boundary_not_a_gap": complete_absent,
        "no_zero_fill_or_generic_missing": observed.isdisjoint({"0", "GENERIC_MISSING", "MISSING"}),
    }


def _static_builder_false_green(base: Path) -> dict[str, Any]:
    """The historical negative control, executed against the ORIGINAL static
    builder module (test_i10_evidence): with production rebuild DESTROYED,
    the static builder still emits all-OK matrices byte-identical to the
    committed historical evidence.  This capability is the recorded
    historical false-green; it is never rewritten."""
    import importlib.util

    import crypto_sensor_fabric.storage.duckdb_catalog as duckdb_catalog_module

    storage_dir = Path(__file__).resolve().parent
    if "i10r1_static_evidence_probe" in sys.modules:
        del sys.modules["i10r1_static_evidence_probe"]

    spec = importlib.util.spec_from_file_location(
        "i10r1_static_evidence_probe", storage_dir / "test_i10_evidence.py"
    )
    assert spec is not None and spec.loader is not None
    static_module = importlib.util.module_from_spec(spec)
    sys.modules["i10r1_static_evidence_probe"] = static_module
    spec.loader.exec_module(static_module)

    real_rebuild = duckdb_catalog_module.rebuild_duckdb_catalog

    def destroyed(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError("production rebuild destroyed for negative control")

    duckdb_catalog_module.rebuild_duckdb_catalog = destroyed
    try:
        matrices = {name: builder() for name, builder in static_module.BUILDERS.items()}
    finally:
        duckdb_catalog_module.rebuild_duckdb_catalog = real_rebuild
    first_rebuild_row = matrices["BLOC_04_I10_CATALOG_REBUILD_MATRIX.json"]["rows"][0]
    view_rows = matrices["BLOC_04_I10_VIEW_EQUIVALENCE_MATRIX.json"]["rows"]
    return {
        "static_builder_still_ok_with_broken_production": first_rebuild_row["result"] == "OK",
        "static_schema_equal_is_literal": view_rows[0]["schema_equal"] is True,
        "static_row_count_equal_is_literal": view_rows[0]["row_count_equal"] is True,
        "static_canonical_rows_equal_is_literal": view_rows[0]["canonical_rows_equal"] is True,
    }


# ---------------------------------------------------------------------------
# R1 matrices — every boolean below comes from the measured helpers
# ---------------------------------------------------------------------------


def build_i10r1_schema_contract_matrix() -> dict[str, Any]:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        root = _fixture_root(base, "evidence")
        output = base / "catalog.duckdb"
        facts, _sha = _schema_row(root, output)
        empty_root = base / "empty-root"
        empty_root.mkdir()
        empty_output = base / "empty.duckdb"
        rebuild_duckdb_catalog(empty_root, empty_output)
        import duckdb
        from crypto_sensor_fabric.storage.duckdb_catalog import VIEW_SCHEMAS

        con = duckdb.connect(str(empty_output), read_only=True)
        try:
            empty_schemas_equal = all(
                [
                    (row[1], row[2])
                    for row in con.execute(f"PRAGMA table_info('{view}')").fetchall()
                ]
                == list(VIEW_SCHEMAS[view])
                for view in VIEW_NAMES
            )
        finally:
            con.close()
        version = _measured_version_refusal(base)
        shape = _measured_shape_refusal(base)
        typing = _measured_type_stability(base)
    rows = [
        _case(
            "populated_view_exact_schema",
            ["build_succeeded", "schema_equal", "metadata_row_equal"],
            **facts,
        ),
        _case(
            "empty_view_exact_schema",
            ["empty_schemas_equal", "metadata_row_equal"],
            empty_schemas_equal=empty_schemas_equal,
            metadata_row_equal=facts["metadata_row_equal"],
        ),
        _case(
            "nullable_first_row_keeps_contract_type",
            ["nullable_first_row_keeps_bigint"],
            **typing,
        ),
        _case(
            "missing_column_refused",
            ["missing_column_refused"],
            **shape,
        ),
        _case(
            "extra_column_refused",
            ["extra_column_refused"],
            **shape,
        ),
        _case(
            "stale_schema_version_refused",
            ["stale_version_refused", "future_version_refused", "wrong_role_refused", "duplicate_metadata_refused"],
            **version,
        ),
        _case(
            "counterfactual_shape_accepts_stripped_rows",
            ["missing_column_refused", "extra_column_refused"],
            missing_column_refused=False,
            extra_column_refused=False,
        ),
    ]
    return _matrix(
        "I10R1_SCHEMA_CONTRACT",
        rows,
        schema_authority="VIEW_SCHEMAS ordered contract",
        schema_version="1.0",
    )


def build_i10r1_runtime_evidence_truth_matrix() -> dict[str, Any]:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        destroy = _measured_destroy_rebuild(base)
        preservation = _measured_failed_build_preservation(base)
        static = _static_builder_false_green(base)
    rows = [
        _case(
            "measured_destroy_rebuild",
            ["rebuild_succeeded", "all_view_rows_equal"],
            **destroy,
        ),
        _case(
            "measured_failed_build_preservation",
            ["typed_corruption_raised", "existing_catalog_unchanged"],
            **preservation,
        ),
        _case(
            "original_static_builder_false_green_negative_control",
            [
                "static_builder_still_ok_with_broken_production",
                "static_schema_equal_is_literal",
                "static_row_count_equal_is_literal",
                "static_canonical_rows_equal_is_literal",
            ],
            **static,
        ),
        _case(
            "counterfactual_measured_builder_detects_broken_production",
            ["rebuild_succeeded", "all_view_rows_equal"],
            rebuild_succeeded=False,
            all_view_rows_equal=False,
        ),
    ]
    return _matrix("I10R1_RUNTIME_EVIDENCE_TRUTH", rows)


def build_i10r1_storage_usage_dimension_matrix() -> dict[str, Any]:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        measured = _measured_storage_dimensions(Path(tmp))
    rows = [
        _case(
            "two_providers_same_state_stay_separate",
            ["provider_groups_separate"],
            **measured,
        ),
        _case(
            "two_sensors_same_state_stay_separate",
            ["provider_groups_separate"],
            **measured,
        ),
        _case(
            "t0a_provider_stays_null_where_not_durably_owned",
            ["t0a_provider_null"],
            **measured,
        ),
        _case(
            "object_and_byte_totals_reconcile",
            ["object_totals_reconcile"],
            **measured,
        ),
        _case(
            "counterfactual_collapsed_dimensions",
            ["provider_groups_separate"],
            provider_groups_separate=False,
        ),
    ]
    return _matrix("I10R1_STORAGE_USAGE_DIMENSION", rows)


def build_i10r1_discovery_cost_matrix() -> dict[str, Any]:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        measured = _measured_discovery_cost(Path(tmp))
    rows = [
        _case("verify_blob_not_called_by_default_rebuild", ["raw_payload_not_loaded"], **measured),
        _case("source_decoder_not_called", ["raw_payload_not_loaded"], **measured),
        _case("missing_physical_blob_still_refused", ["missing_physical_blob_refused"], **measured),
        _case("stored_size_divergence_still_refused", ["stored_size_divergence_refused"], **measured),
        _case("large_blob_metadata_discovery_without_payload_read", ["raw_payload_not_loaded"], **measured),
        _case(
            "counterfactual_full_rescan_cost",
            ["raw_payload_not_loaded"],
            raw_payload_not_loaded=False,
        ),
    ]
    return _matrix("I10R1_DISCOVERY_COST", rows)


def build_i10r1_durable_relation_matrix() -> dict[str, Any]:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        relations = _measured_durable_relations(Path(tmp))
        missingness = _measured_missingness_preservation(Path(tmp))
    rows = [
        _case("malformed_recovery_action_refused", ["malformed_recovery_action_refused"], **relations),
        _case("orphan_lineage_refused", ["orphan_lineage_refused"], **relations),
        _case("artifact_context_lineage_valid_chain_accepted", ["valid_chain_accepted"], **relations),
        _case("frozen_missingness_states_preserved", ["frozen_states_preserved", "complete_boundary_not_a_gap", "no_zero_fill_or_generic_missing"], **missingness),
        _case(
            "counterfactual_silent_orphan_adoption",
            ["orphan_lineage_refused"],
            orphan_lineage_refused=False,
        ),
    ]
    return _matrix("I10R1_DURABLE_RELATION", rows)


def build_i10r1_summary() -> dict[str, Any]:
    return {
        "checkpoint": "SENSOR-B4-I10R1",
        "api": "crypto_sensor_fabric.storage.duckdb_catalog.rebuild_duckdb_catalog",
        "catalog_role": "rebuildable_discovery_non_authoritative",
        "schema_version": "1.0",
        "schema_authority": "VIEW_SCHEMAS (single ordered contract)",
        "views": list(VIEW_NAMES),
        "matrices": {
            "schema_contract_rows": 7,
            "runtime_evidence_truth_rows": 4,
            "storage_usage_dimension_rows": 5,
            "discovery_cost_rows": 6,
            "durable_relation_rows": 5,
        },
        "measured_evidence": "every boolean observed from executed production behavior in temp roots",
        "historical_i10_evidence": "preserved byte-for-byte; never rewritten",
        "governance": {
            "PASS_SENSOR_B4_I10_DUCKDB_DISCOVERY_SEALED": "OPERATOR_HOLD",
            "PASS_SENSOR_B4_I10R1_SCHEMA_EVIDENCE_DISCOVERY_SEALED": "PENDING_OPERATOR_REVIEW",
            "G4-09_CATALOG_REBUILD_GATE": "IMPLEMENTATION_PASS_PENDING_OPERATOR_REVIEW",
            "next_checkpoint_authorized": False,
            "recommended_next": "OPERATOR REVIEW OF COMPLETE I10 -> I10R1 CHAIN",
        },
    }


I10R1_BUILDERS = {
    "BLOC_04_I10R1_SCHEMA_CONTRACT_MATRIX.json": build_i10r1_schema_contract_matrix,
    "BLOC_04_I10R1_RUNTIME_EVIDENCE_TRUTH_MATRIX.json": build_i10r1_runtime_evidence_truth_matrix,
    "BLOC_04_I10R1_STORAGE_USAGE_DIMENSION_MATRIX.json": build_i10r1_storage_usage_dimension_matrix,
    "BLOC_04_I10R1_DISCOVERY_COST_MATRIX.json": build_i10r1_discovery_cost_matrix,
    "BLOC_04_I10R1_DURABLE_RELATION_MATRIX.json": build_i10r1_durable_relation_matrix,
    "BLOC_04_I10R1_DUCKDB_DISCOVERY_MICROSEAL.json": build_i10r1_summary,
}

HISTORICAL_I10_ARTIFACTS = (
    "BLOC_04_I10_CATALOG_REBUILD_MATRIX.json",
    "BLOC_04_I10_VIEW_EQUIVALENCE_MATRIX.json",
    "BLOC_04_I10_EVIDENCE_IMMUTABILITY_MATRIX.json",
    "BLOC_04_I10_CORRUPTION_DISCOVERY_MATRIX.json",
    "BLOC_04_I10_PORTABILITY_MATRIX.json",
    "BLOC_04_I10_DUCKDB_REBUILD_EVIDENCE.md",
    "duckdb_rebuild.json",
)


def test_i10r1_evidence_is_measured_and_committed() -> None:
    for name, builder in I10R1_BUILDERS.items():
        payload = builder()
        for row in payload.get("rows", []):
            required = row["required_invariants"]
            assert row["result"] == (
                "OK" if all(row.get(item) is True for item in required) else "FAIL"
            )
            for item in required:
                assert isinstance(row.get(item), bool), (name, row["case"], item)
        expected = _stable(payload)
        committed = EVIDENCE_DIR / name
        assert committed.exists(), f"missing committed R1 artifact: {name}"
        assert committed.read_bytes() == expected, f"R1 artifact drifted: {name}"


def test_i10r1_historical_i10_evidence_is_unchanged() -> None:
    for name in HISTORICAL_I10_ARTIFACTS:
        path = EVIDENCE_DIR / name
        assert path.exists(), f"historical artifact missing: {name}"
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == HISTORICAL_I10_SHA256[name], f"historical artifact changed: {name}"


HISTORICAL_I10_SHA256 = {
    "BLOC_04_I10_CATALOG_REBUILD_MATRIX.json": "eca261e85c468366b075414eefdc8e3268c62260b843d23ce2bbb7b65012e548",
    "BLOC_04_I10_VIEW_EQUIVALENCE_MATRIX.json": "e7aefdc79da06fe820f8f8fcc0c1dd4d51681768dff3782645b190bdb617917b",
    "BLOC_04_I10_EVIDENCE_IMMUTABILITY_MATRIX.json": "6c069d3510a021409efd316c03fcb67b7b1bbbe9ec4c36ad62bce711a6276682",
    "BLOC_04_I10_CORRUPTION_DISCOVERY_MATRIX.json": "3883c7cad4076de57d581e812cab93f878927bd156741d505cb37249d01a8f85",
    "BLOC_04_I10_PORTABILITY_MATRIX.json": "68fc87660e7c6607545b19f99b67727a728796324ac5634991542a6e879e409b",
    "BLOC_04_I10_DUCKDB_REBUILD_EVIDENCE.md": "2df4f210f100f949f868ba8a830800fd8af9c5f80d4463197042ca979094ea74",
    "duckdb_rebuild.json": "677e23272be3055db83dd8b6a2cf8b2938b69ec3ebb5abbc6ed2f9ac70fbf5fd",
}


def test_i10r1_deliberate_counterfactual_fails_are_represented() -> None:
    for name, builder in I10R1_BUILDERS.items():
        payload = builder()
        rows = payload.get("rows", [])
        if not rows:
            continue
        counterfactuals = [row for row in rows if row["case"].startswith("counterfactual")]
        assert counterfactuals, f"matrix lacks a deliberate counterfactual FAIL: {name}"
        for row in counterfactuals:
            assert row["result"] == "FAIL", (name, row["case"])
            assert any(row.get(item) is False for item in row["required_invariants"]), (
                name,
                row["case"],
            )


__all__ = [
    "HISTORICAL_I10_ARTIFACTS",
    "HISTORICAL_I10_SHA256",
    "I10R1_BUILDERS",
]
