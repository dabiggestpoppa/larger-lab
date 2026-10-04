"""SENSOR-B4-I16R2 §16 — restart + tamper laws around a committed unit claim.

These laws already hold in the accepted stack (I05R2 physical verification,
I16R1 registry self-validation).  I16R2 restates them narrowly for the
source-unit chain so the R2 evidence can bind them:

  * a fresh restart reproduces the durable unit declaration and re-proves
    the physical projection (no repair-on-read, no stale cache);
  * tampering the committed unit column or the projection payload fails
    closed through the existing physical-verification laws;
  * tampering the registered schema declaration fails closed through the
    registry fingerprint law.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pyarrow as pa
import pytest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))  # noqa: E402
SRC = str(HERE.parents[2] / "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # noqa: E402

from _sibling_import import load_sibling  # noqa: E402

from crypto_sensor_fabric.storage import (  # noqa: E402
    ProjectionSchemaDefinition,
    ProjectionSchemaRegistry,
    SourceUnitEvidence,
    SourceUnitState,
)
from crypto_sensor_fabric.storage.json_catalog import (  # noqa: E402
    catalog_physical_key,
)
from crypto_sensor_fabric.storage.projections import (  # noqa: E402
    ProjectionCorruption,
)
from crypto_sensor_fabric.storage.projection_schema import (  # noqa: E402
    ProjectionSchemaCatalogCorrupt,
)

CURRENT_HEAD = "e8d1384d98771c39cb119e2cae0ff93296be02ec"

_support = load_sibling("i16r1_contract_support", "test_i16r1_unit_contract")
Lake = _support.Lake
KNOWN = _support.KNOWN  # quantity_unit VERIFIED_NATIVE "SOL"

SOL_ROW = {"price": 1.0, "qty": 1.0, "quantity_unit": "SOL"}


def _committed_lake(tmp_path: Path, *, schema_id: str = "i16r2.integrity"):
    lake = Lake(tmp_path / "lake")
    _support._register_definition(lake, schema_id=schema_id, declarations=[KNOWN])
    sha = lake.seed_blob(
        b'{"rows":[{"price":1.0,"qty":1.0,"quantity_unit":"SOL"}],'
        b'"ts":1700000000}'
    )
    lake.seed_acquisition(sha, "acq-r2")
    lake.projection_service.commit_projection(
        rows=[SOL_ROW, SOL_ROW],
        schema_definition=lake.schema_definition,
        projection_id="proj-r1",
        source_blob_sha256=[sha],
        acquisition_ids=["acq-r2"],
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
        lineage_manifest_id="lm-proj-r1",
    )
    lake.commit_manifest("pm-r1", blob_refs=[sha], projection_refs=["proj-r1"])
    return lake, sha


def _projection_path(lake) -> Path:
    artifact = lake.artifacts.get_strict("proj-r1")
    return lake.t0b / artifact.projection_uri


class TestRestartReproducesUnitDeclaration:
    def test_fresh_restart_reproduces_declaration_and_physical_proof(
        self, tmp_path: Path
    ) -> None:
        lake, sha = _committed_lake(tmp_path)
        fresh = lake.fresh()
        fresh.artifacts.verify_physical("proj-r1")
        batch = _support._handoff_batch(fresh, sha, registry=fresh.schemas)
        assert [
            (e.field_name, e.state.value, e.native_unit_lexeme)
            for e in batch.source_unit_evidence
        ] == [("quantity_unit", "VERIFIED_NATIVE", "SOL")]


class TestTamperFailsClosed:
    def test_tampered_unit_column_fails_closed(self, tmp_path: Path) -> None:
        lake, _ = _committed_lake(tmp_path)
        path = _projection_path(lake)
        import pyarrow.parquet as pq

        table = pq.read_table(str(path))
        values = table.column("quantity_unit").to_pylist()
        rewritten = pa.array(
            ["XXX" if value == "SOL" else value for value in values],
            type=pa.string(),
        )
        table = table.set_column(
            table.schema.get_field_index("quantity_unit"),
            "quantity_unit",
            rewritten,
        )
        pq.write_table(table, str(path))
        fresh = lake.fresh()
        with pytest.raises(ProjectionCorruption):
            fresh.artifacts.verify_physical("proj-r1")

    def test_tampered_payload_bytes_fail_closed(self, tmp_path: Path) -> None:
        lake, _ = _committed_lake(tmp_path)
        path = _projection_path(lake)
        payload = bytearray(path.read_bytes())
        middle = len(payload) // 2
        payload[middle] ^= 0xFF
        path.write_bytes(bytes(payload))
        fresh = lake.fresh()
        with pytest.raises(ProjectionCorruption):
            fresh.artifacts.verify_physical("proj-r1")

    def test_tampered_schema_declaration_fails_closed(self, tmp_path: Path) -> None:
        root = tmp_path / "catalogs" / "projection_schemas"
        registry = ProjectionSchemaRegistry(root)
        registry.register(
            ProjectionSchemaDefinition(
                "i16r2.integrity.tamper",
                "1.0.0",
                pa.schema(
                    [
                        pa.field("price", pa.float64(), nullable=False),
                        pa.field("qty", pa.float64(), nullable=False),
                        pa.field("quantity_unit", pa.string(), nullable=False),
                    ]
                ),
                source_unit_evidence=[
                    SourceUnitEvidence(
                        field_name="quantity_unit",
                        native_unit_lexeme="SOL",
                        state=SourceUnitState.VERIFIED_NATIVE,
                    )
                ],
            )
        )
        fragment = root / catalog_physical_key("i16r2.integrity.tamper@1.0.0")
        payload = json.loads(fragment.read_text(encoding="utf-8"))
        payload["source_unit_evidence"][0]["native_unit_lexeme"] = "BTC"
        fragment.write_text(
            json.dumps(payload, sort_keys=True), encoding="utf-8", newline="\n"
        )
        with pytest.raises(ProjectionSchemaCatalogCorrupt):
            ProjectionSchemaRegistry(root)
