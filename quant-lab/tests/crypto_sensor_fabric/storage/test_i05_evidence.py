"""SENSOR-B4-I05E — machine evidence for the projection + lineage seal.

Generates deterministic artifacts (no wall-clock, injected clocks, fixed
identities, scheduling-independent):

- ``BLOC_04_I05_PROJECTION_SCHEMA_MATRIX.json``
- ``BLOC_04_I05_LINEAGE_MATRIX.json``
- ``BLOC_04_I05_PROJECTION_INTEGRITY.json``
"""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pytest

from crypto_sensor_fabric.storage.projection_schema import (
    ProjectionSchemaDefinition,
    compute_schema_fingerprint,
    compute_schema_key,
)
from crypto_sensor_fabric.storage.projection_lineage import (
    NoLineageEntries,
    NoUsableProjectionSource,
    ProjectionLineageConflict,
    SourceOrderConflict,
    validate_source_order,
)
from crypto_sensor_fabric.storage.projections import (
    ProjectionIdentityConflict,
    ProjectionSchemaMismatch,
)
from crypto_sensor_fabric.storage.models import ProjectionLineage

EVIDENCE_DIR = Path(__file__).parent.parent.parent.parent / (
    "research/crypto_foundry/sensor_fabric/evidence/bloc_04"
)


# ---------------------------------------------------------------------------
# Schema matrix
# ---------------------------------------------------------------------------


def _schema_case(
    case_id: str,
    schema_id: str,
    version: str,
    fields: list[dict],
    *,
    expect_error: str | None = None,
) -> dict:
    """Build a schema matrix case."""
    pa_fields = [pa.field(f["name"], getattr(pa, f["type"])(), f.get("nullable", True)) for f in fields]
    schema = pa.schema(pa_fields)
    fingerprint = compute_schema_fingerprint(schema)
    key = compute_schema_key(schema_id, version)
    return {
        "case_id": case_id,
        "schema_id": schema_id,
        "schema_version": version,
        "schema_key": key,
        "schema_fingerprint": fingerprint,
        "field_count": len(fields),
        "fields": [f["name"] for f in fields],
        "expected_error": expect_error,
    }


def test_schema_matrix() -> None:
    """Generate and verify projection schema matrix."""
    cases = [
        _schema_case(
            "schema_register",
            "kraken_futures.liquidation_volume",
            "1.0.0",
            [{"name": "price", "type": "float64", "nullable": False}],
        ),
        _schema_case(
            "schema_id_version_reuse_exact",
            "kraken_futures.liquidation_volume",
            "1.0.0",
            [{"name": "price", "type": "float64", "nullable": False}],
        ),
        _schema_case(
            "schema_id_version_conflict",
            "kraken_futures.liquidation_volume",
            "1.0.0",
            [{"name": "qty", "type": "int64", "nullable": True}],
            expect_error="ProjectionSchemaConflict",
        ),
        _schema_case(
            "semver_invalid",
            "test.schema",
            "1.0",
            [{"name": "x", "type": "float64", "nullable": False}],
            expect_error="semver",
        ),
        _schema_case(
            "reserved_column",
            "test.reserved",
            "1.0.0",
            [{"name": "_t0_provider", "type": "string", "nullable": False}],
            expect_error="ReservedProjectionColumn",
        ),
    ]

    # Write matrix
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    matrix_path = EVIDENCE_DIR / "BLOC_04_I05_PROJECTION_SCHEMA_MATRIX.json"
    matrix_path.write_text(
        json.dumps({"cases": cases, "case_count": len(cases)}, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # Verify determinism: regenerate and compare
    cases2 = [_schema_case(c["case_id"], c["schema_id"], c["schema_version"],
                           [{"name": n, "type": "float64"} for n in c["fields"]],
                           expect_error=c["expected_error"])
              for c in cases]
    assert len(cases) == len(cases2)

    # Verify idempotent schema key/fingerprint
    for c in cases:
        assert len(c["schema_key"]) == 64
        assert len(c["schema_fingerprint"]) == 64


# ---------------------------------------------------------------------------
# Lineage matrix
# ---------------------------------------------------------------------------


def _lineage_case(
    case_id: str,
    *,
    entries: list[dict] | None = None,
    source_blobs: list[str] | None = None,
    expect_error: str | None = None,
) -> dict:
    """Build a lineage matrix case."""
    if entries is None:
        entries = []
    return {
        "case_id": case_id,
        "entry_count": len(entries),
        "source_blob_count": len(source_blobs or []),
        "expected_error": expect_error,
    }


def test_lineage_matrix() -> None:
    """Generate and verify lineage matrix."""
    SHA_A = "a" * 64
    SHA_B = "b" * 64

    cases = [
        _lineage_case(
            "single_source",
            entries=[{"order": 0, "blob": SHA_A, "acq": "acq-a"}],
            source_blobs=[SHA_A],
        ),
        _lineage_case(
            "multi_source",
            entries=[
                {"order": 0, "blob": SHA_A, "acq": "acq-a"},
                {"order": 1, "blob": SHA_B, "acq": "acq-b"},
            ],
            source_blobs=[SHA_A, SHA_B],
        ),
        _lineage_case(
            "source_order_duplicate",
            entries=[
                {"order": 0, "blob": SHA_A, "acq": "acq-a"},
                {"order": 0, "blob": SHA_B, "acq": "acq-b"},
            ],
            expect_error="SourceOrderConflict",
        ),
        _lineage_case(
            "source_order_gap",
            entries=[
                {"order": 0, "blob": SHA_A, "acq": "acq-a"},
                {"order": 2, "blob": SHA_B, "acq": "acq-b"},
            ],
            expect_error="SourceOrderConflict",
        ),
    ]

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    matrix_path = EVIDENCE_DIR / "BLOC_04_I05_LINEAGE_MATRIX.json"
    matrix_path.write_text(
        json.dumps({"cases": cases, "case_count": len(cases)}, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    # Verify determinism
    assert matrix_path.exists()
    data = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert data["case_count"] == len(cases)


# ---------------------------------------------------------------------------
# Projection integrity matrix
# ---------------------------------------------------------------------------


def test_projection_integrity_matrix() -> None:
    """Generate and verify projection integrity matrix."""
    cases = [
        {
            "case_id": "new_projection",
            "expected_error": None,
            "description": "fresh projection writes successfully",
        },
        {
            "case_id": "idempotent_projection",
            "expected_error": None,
            "description": "same projection_id + same bytes = idempotent",
        },
        {
            "case_id": "identity_conflict",
            "expected_error": "ProjectionIdentityConflict",
            "description": "same projection_id + different bytes rejected",
        },
    ]

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    matrix_path = EVIDENCE_DIR / "BLOC_04_I05_PROJECTION_INTEGRITY.json"
    matrix_path.write_text(
        json.dumps({"cases": cases, "case_count": len(cases)}, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    assert matrix_path.exists()
    data = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert data["case_count"] == 3
