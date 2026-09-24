"""SENSOR-B4-I10R2 — durable relation binding and recovery-envelope attacks."""

from __future__ import annotations

# ruff: noqa: E402

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

import pytest

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parents[2] / "src"
for _path in (str(_SRC), str(_HERE)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

from _sibling_import import load_sibling
from crypto_sensor_fabric.storage.duckdb_catalog import (
    DuckDBCatalogCorrupt,
    ReadOnlyDuckDBCatalog,
    rebuild_duckdb_catalog,
)
from crypto_sensor_fabric.storage.enums import StorageEncoding
from crypto_sensor_fabric.storage.recovery import RecoveryJournal

Fixture = load_sibling("i10r2_rebuild_helpers", "test_duckdb_rebuild").Fixture
Mutator = Callable[[dict[str, Any], Any], None]


def _fragment(directory: Path, logical_id: str) -> tuple[Path, dict[str, Any]]:
    path = directory / f"{hashlib.sha256(logical_id.encode('utf-8')).hexdigest()}.json"
    return path, json.loads(path.read_text(encoding="utf-8"))


def _replace_fragment(
    directory: Path,
    old_logical_id: str,
    payload: dict[str, Any],
    *,
    new_logical_id: str | None = None,
) -> None:
    old_path, _ = _fragment(directory, old_logical_id)
    old_path.unlink()
    logical_id = new_logical_id or old_logical_id
    path = directory / f"{hashlib.sha256(logical_id.encode('utf-8')).hexdigest()}.json"
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _mutate_lineage(root: Path, mutator: Mutator) -> None:
    directory = root / "catalogs" / "manifests" / "projection_lineage"
    _, payload = _fragment(directory, "lineage-1")
    mutator(payload, payload["entries"][0])
    _replace_fragment(directory, "lineage-1", payload)


def _mutate_context(root: Path, mutator: Mutator) -> None:
    directory = root / "catalogs" / "manifests" / "projection_context"
    _, payload = _fragment(directory, "projection-1")
    mutator(payload, payload)
    _replace_fragment(directory, "projection-1", payload)


def _add_second_blob(fixture: Any) -> str:
    stored = fixture.store.put_bytes(
        b'{"trade":2}',
        storage_encoding=StorageEncoding.NONE,
        source_media_type="application/json",
    )
    fixture.blobs.append_metadata(stored.blob)
    return stored.blob.blob_sha256


def _add_second_acquisition(fixture: Any, blob_sha256: str) -> str:
    acquisition_id = "acq-2"
    fixture.acquisitions.append_acquisition(
        fixture.acquisition.model_copy(
            update={
                "acquisition_id": acquisition_id,
                "request_fingerprint": "request-2",
                "source_locator": "fixture://trade-2",
                "blob_sha256": blob_sha256,
            }
        )
    )
    return acquisition_id


def _mutate_action(root: Path, mutator: Mutator) -> None:
    directory = root / "catalogs" / "recovery" / "actions"
    path, payload = next(
        (path, json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(directory.glob("*.json"))
    )
    old_id = payload["recovery_action_id"]
    mutator(payload, payload)
    new_id = payload.get("recovery_action_id", old_id)
    path.unlink()
    target = directory / f"{hashlib.sha256(new_id.encode('utf-8')).hexdigest()}.json"
    target.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _assert_rebuild_refused(root: Path, output: Path) -> None:
    with pytest.raises(DuckDBCatalogCorrupt):
        rebuild_duckdb_catalog(root, output)


def test_valid_lineage_and_recovery_chain_is_accepted(tmp_path: Path) -> None:
    fixture = Fixture(tmp_path / "valid")
    output = tmp_path / "valid.duckdb"
    rebuild_duckdb_catalog(fixture.root, output)
    with ReadOnlyDuckDBCatalog(output) as reader:
        assert len(reader.canonical_view_rows("v_t0_projections")) == 1
        assert len(reader.canonical_view_rows("v_t0_quarantine")) == 1


def test_entry_manifest_id_mismatch_refused(tmp_path: Path) -> None:
    fixture = Fixture(tmp_path / "a1")
    _mutate_lineage(
        fixture.root,
        lambda payload, entry: entry.update(lineage_manifest_id="other-manifest"),
    )
    _assert_rebuild_refused(fixture.root, tmp_path / "a1.duckdb")


def test_context_manifest_id_mismatch_refused(tmp_path: Path) -> None:
    fixture = Fixture(tmp_path / "a2")
    directory = fixture.root / "catalogs" / "manifests" / "projection_lineage"
    _, lineage = _fragment(directory, "lineage-1")
    lineage["lineage_manifest_id"] = "lineage-2"
    for entry in lineage["entries"]:
        entry["lineage_manifest_id"] = "lineage-2"
    _replace_fragment(directory, "lineage-1", lineage, new_logical_id="lineage-2")
    _assert_rebuild_refused(fixture.root, tmp_path / "a2.duckdb")


def test_artifact_source_list_mismatch_refused(tmp_path: Path) -> None:
    fixture = Fixture(tmp_path / "a3")
    blob_b = _add_second_blob(fixture)
    _mutate_lineage(
        fixture.root,
        lambda _, entry: entry.update(source_blob_sha256=blob_b),
    )
    _assert_rebuild_refused(fixture.root, tmp_path / "a3.duckdb")


def test_missing_source_acquisition_refused(tmp_path: Path) -> None:
    fixture = Fixture(tmp_path / "a4")
    _mutate_lineage(
        fixture.root,
        lambda _, entry: entry.update(source_acquisition_id="acquisition-does-not-exist"),
    )
    _assert_rebuild_refused(fixture.root, tmp_path / "a4.duckdb")


def test_acquisition_blob_mismatch_refused(tmp_path: Path) -> None:
    fixture = Fixture(tmp_path / "a5")
    blob_b = _add_second_blob(fixture)
    acquisition_b = _add_second_acquisition(fixture, blob_b)
    _mutate_lineage(
        fixture.root,
        lambda _, entry: entry.update(source_acquisition_id=acquisition_b),
    )
    _assert_rebuild_refused(fixture.root, tmp_path / "a5.duckdb")


def test_duplicate_source_order_refused(tmp_path: Path) -> None:
    fixture = Fixture(tmp_path / "a6")
    _mutate_lineage(
        fixture.root,
        lambda payload, entry: payload["entries"].append(dict(entry)),
    )
    _assert_rebuild_refused(fixture.root, tmp_path / "a6.duckdb")


@pytest.mark.parametrize(
    ("start", "end"),
    [(0, None), (2, 1)],
    ids=["one-sided", "inverted"],
)
def test_invalid_row_bounds_refused(tmp_path: Path, start: int, end: int | None) -> None:
    fixture = Fixture(tmp_path / f"a7-{start}-{end}")
    _mutate_lineage(
        fixture.root,
        lambda _, entry: entry.update(source_row_start=start, source_row_end=end),
    )
    _assert_rebuild_refused(fixture.root, tmp_path / f"a7-{start}-{end}.duckdb")


def test_wrong_lineage_record_type_refused(tmp_path: Path) -> None:
    fixture = Fixture(tmp_path / "a8")
    _mutate_lineage(
        fixture.root,
        lambda payload, _: payload.update(record_type="not_projection_lineage"),
    )
    _assert_rebuild_refused(fixture.root, tmp_path / "a8.duckdb")


def test_internal_recovery_object_type_with_null_storage_mapping_accepted(
    tmp_path: Path,
) -> None:
    fixture = Fixture(tmp_path / "internal-valid")
    RecoveryJournal(fixture.root).record(
        recovery_run_id="run-internal",
        object_type="STAGING_ARTIFACT",
        object_id="staging-1",
        problem="UNCOMMITTED_STAGING",
        resolution="quarantined",
    )
    output = tmp_path / "internal-valid.duckdb"
    rebuild_duckdb_catalog(fixture.root, output)
    with ReadOnlyDuckDBCatalog(output) as reader:
        assert any(
            row[2] == "STAGING_ARTIFACT"
            for row in reader.canonical_view_rows("v_t0_quarantine")
        )


@pytest.mark.parametrize(
    ("case", "mutator"),
    [
        (
            "wrong-record-type",
            lambda payload, _: payload.update(record_type="not_recovery_action"),
        ),
        (
            "missing-record-type",
            lambda payload, _: payload.pop("record_type"),
        ),
        (
            "storage-mapping-contradiction",
            lambda payload, _: payload.update(storage_object_type="STORAGE_JOB"),
        ),
        (
            "invalid-action-kind",
            lambda payload, _: payload.update(action_kind=17),
        ),
        (
            "invalid-operation-id",
            lambda payload, _: payload.update(operation_id=17),
        ),
        (
            "malformed-before-state",
            lambda payload, _: payload.update(before_state="[]"),
        ),
        (
            "malformed-after-state",
            lambda payload, _: payload.update(after_state="[]"),
        ),
        (
            "naive-registered-at",
            lambda payload, _: payload.update(registered_at="2026-01-15T12:00:00"),
        ),
    ],
)
def test_recovery_envelope_corruption_refused(
    tmp_path: Path,
    case: str,
    mutator: Mutator,
) -> None:
    fixture = Fixture(tmp_path / case)
    _mutate_action(fixture.root, mutator)
    _assert_rebuild_refused(fixture.root, tmp_path / f"{case}.duckdb")
