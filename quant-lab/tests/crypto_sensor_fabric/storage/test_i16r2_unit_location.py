"""SENSOR-B4-I16R2 §11/§12/§13/§19/§20 — unit-location contract tests.

The eight-family audit proved the unit-bearing shapes are not all scalar:
book snapshots carry a unit PER PRICE LEVEL (``PriceLevel.quantity_unit``)
and a batch may legitimately vary the native lexeme by row.  These tests
exercise the additive location contract:

  * §12 — structural ``field_path`` tuples resolve against the registered
    Arrow schema (list element name / struct child names / string terminal);
    unresolvable or reserved paths never register;
  * §13 — nested strict proof: a static claim at a nested path is proven
    across every level of every row; a mixed level is refused;
  * §11 — ``ROW_NATIVE`` declares the durable per-row/per-level location
    with no batch lexeme, so row variation is never silently collapsed;
  * §19 — explicit ``NO_UNIT_FIELDS`` vs historical absence;
  * §20 — historical descriptors/batches load unchanged.
"""

from __future__ import annotations

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
    ProjectionUnitEvidenceConflict,
    RawNormalizationBatch,
    SourceUnitContract,
    SourceUnitEvidence,
    SourceUnitState,
    SourceUnitVariability,
    compute_schema_fingerprint,
)

CURRENT_HEAD = "e8d1384d98771c39cb119e2cae0ff93296be02ec"

_support = load_sibling("i16r1_contract_support", "test_i16r1_unit_contract")
Lake = _support.Lake

BID_LEVEL = pa.struct(
    [
        pa.field("price", pa.float64(), nullable=False),
        pa.field("quantity", pa.float64(), nullable=False),
        pa.field("quantity_unit", pa.string(), nullable=True),
    ]
)

BOOK_SCHEMA = pa.schema(
    [
        pa.field("sequence_id", pa.string(), nullable=True),
        pa.field(
            "bids",
            pa.list_(pa.field("item", BID_LEVEL, nullable=True)),
            nullable=False,
        ),
        pa.field(
            "asks",
            pa.list_(pa.field("item", BID_LEVEL, nullable=True)),
            nullable=False,
        ),
    ]
)

BIDS_PATH = ("bids", "item", "quantity_unit")
ASKS_PATH = ("asks", "item", "quantity_unit")

BIDS_ROW_NATIVE = SourceUnitEvidence(
    field_name="bids",
    field_path=BIDS_PATH,
    native_unit_lexeme=None,
    state=SourceUnitState.UNIT_UNVERIFIED,
    variability=SourceUnitVariability.ROW_NATIVE,
)
ASKS_ROW_NATIVE = SourceUnitEvidence(
    field_name="asks",
    field_path=ASKS_PATH,
    native_unit_lexeme=None,
    state=SourceUnitState.UNIT_UNVERIFIED,
    variability=SourceUnitVariability.ROW_NATIVE,
)
BIDS_STATIC_BTC = SourceUnitEvidence(
    field_name="bids",
    field_path=BIDS_PATH,
    native_unit_lexeme="BTC",
    state=SourceUnitState.VERIFIED_NATIVE,
)
BIDS_STATIC_BTC_EXPLICIT = SourceUnitEvidence(
    field_name="bids",
    field_path=BIDS_PATH,
    native_unit_lexeme="BTC",
    state=SourceUnitState.VERIFIED_NATIVE,
    variability=SourceUnitVariability.STATIC_VERIFIED,
)


def _book_row(bid_units=None, ask_units=None) -> dict:
    return {
        "sequence_id": "1",
        "bids": [
            {"price": 100.0, "quantity": 1.0, "quantity_unit": unit}
            for unit in (bid_units or ["BTC"])
        ],
        "asks": [
            {"price": 101.0, "quantity": 1.0, "quantity_unit": unit}
            for unit in (ask_units or ["BTC"])
        ],
    }


def _stack(tmp_path: Path, *, schema_id: str, declarations, contract=None):
    lake = Lake(tmp_path / "lake")
    definition = ProjectionSchemaDefinition(
        schema_id,
        "1.0.0",
        BOOK_SCHEMA,
        source_unit_evidence=declarations,
        source_unit_contract=contract,
    )
    lake.schemas.register(definition)
    lake.schema_definition = definition
    return lake


def _seed(
    lake,
    *,
    sensor: str = "MECHANICAL_TRADE",
    instrument: str = "BTC-USDT",
) -> str:
    sha = lake.seed_blob(b'{"fixture":"i16r2-location"}')
    lake.seed_acquisition(
        sha, "acq-r2", sensor=sensor, instrument=instrument
    )
    return sha


def _commit(lake, sha: str, rows):
    result = lake.projection_service.commit_projection(
        rows=rows,
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
    return result


# ---------------------------------------------------------------------------
# §12 — structural path resolution at registration time
# ---------------------------------------------------------------------------


class TestStructuralPathResolution:
    def test_nested_path_registers_and_enters_the_fingerprint(self) -> None:
        legacy = ProjectionSchemaDefinition("r2.path.a", "1.0.0", BOOK_SCHEMA)
        declared = ProjectionSchemaDefinition(
            "r2.path.a",
            "1.0.0",
            BOOK_SCHEMA,
            source_unit_evidence=[BIDS_ROW_NATIVE, ASKS_ROW_NATIVE],
        )
        assert declared.schema_fingerprint != legacy.schema_fingerprint
        assert declared.schema_fingerprint == compute_schema_fingerprint(
            BOOK_SCHEMA, [BIDS_ROW_NATIVE, ASKS_ROW_NATIVE]
        )

    def test_unresolvable_root_fails_closed(self) -> None:
        with pytest.raises(ValueError):
            ProjectionSchemaDefinition(
                "r2.path.root",
                "1.0.0",
                BOOK_SCHEMA,
                source_unit_evidence=[
                    SourceUnitEvidence(
                        field_name="levels",
                        field_path=("levels", "item", "quantity_unit"),
                        native_unit_lexeme=None,
                        state=SourceUnitState.UNIT_UNVERIFIED,
                        variability=SourceUnitVariability.ROW_NATIVE,
                    )
                ],
            )

    def test_wrong_list_element_name_fails_closed(self) -> None:
        with pytest.raises(ValueError):
            ProjectionSchemaDefinition(
                "r2.path.list",
                "1.0.0",
                BOOK_SCHEMA,
                source_unit_evidence=[
                    SourceUnitEvidence(
                        field_name="bids",
                        field_path=("bids", "element", "quantity_unit"),
                        native_unit_lexeme=None,
                        state=SourceUnitState.UNIT_UNVERIFIED,
                        variability=SourceUnitVariability.ROW_NATIVE,
                    )
                ],
            )

    def test_wrong_struct_child_fails_closed(self) -> None:
        with pytest.raises(ValueError):
            ProjectionSchemaDefinition(
                "r2.path.struct",
                "1.0.0",
                BOOK_SCHEMA,
                source_unit_evidence=[
                    SourceUnitEvidence(
                        field_name="bids",
                        field_path=("bids", "item", "missing_unit"),
                        native_unit_lexeme=None,
                        state=SourceUnitState.UNIT_UNVERIFIED,
                        variability=SourceUnitVariability.ROW_NATIVE,
                    )
                ],
            )

    def test_non_string_terminal_fails_closed(self) -> None:
        with pytest.raises(ValueError):
            ProjectionSchemaDefinition(
                "r2.path.terminal",
                "1.0.0",
                BOOK_SCHEMA,
                source_unit_evidence=[
                    SourceUnitEvidence(
                        field_name="bids",
                        field_path=("bids", "item", "quantity"),
                        native_unit_lexeme=None,
                        state=SourceUnitState.UNIT_UNVERIFIED,
                        variability=SourceUnitVariability.ROW_NATIVE,
                    )
                ],
            )

    def test_path_root_must_equal_field_name(self) -> None:
        with pytest.raises(ValueError):
            SourceUnitEvidence(
                field_name="asks",
                field_path=BIDS_PATH,
                native_unit_lexeme=None,
                state=SourceUnitState.UNIT_UNVERIFIED,
                variability=SourceUnitVariability.ROW_NATIVE,
            )

    def test_reserved_or_empty_component_fails_closed(self) -> None:
        with pytest.raises(ValueError):
            SourceUnitEvidence(
                field_name="bids",
                field_path=("bids", "item", "_t0_unit"),
                native_unit_lexeme=None,
                state=SourceUnitState.UNIT_UNVERIFIED,
                variability=SourceUnitVariability.ROW_NATIVE,
            )
        with pytest.raises(ValueError):
            SourceUnitEvidence(
                field_name="bids",
                field_path=("bids", "", "quantity_unit"),
                native_unit_lexeme=None,
                state=SourceUnitState.UNIT_UNVERIFIED,
                variability=SourceUnitVariability.ROW_NATIVE,
            )
        with pytest.raises(ValueError):
            SourceUnitEvidence(
                field_name="bids",
                field_path=(),
                native_unit_lexeme=None,
                state=SourceUnitState.UNIT_UNVERIFIED,
                variability=SourceUnitVariability.ROW_NATIVE,
            )

    def test_same_path_declared_twice_fails_closed(self) -> None:
        with pytest.raises(ValueError):
            ProjectionSchemaDefinition(
                "r2.path.dup",
                "1.0.0",
                BOOK_SCHEMA,
                source_unit_evidence=[BIDS_ROW_NATIVE, BIDS_STATIC_BTC],
            )

    def test_nested_descriptor_round_trips_with_fingerprint(self) -> None:
        declared = ProjectionSchemaDefinition(
            "r2.path.roundtrip",
            "1.0.0",
            BOOK_SCHEMA,
            source_unit_evidence=[BIDS_ROW_NATIVE, ASKS_ROW_NATIVE],
        )
        payload = declared.to_descriptor()
        # canonical order = sorted by resolved structural path (asks < bids)
        assert [
            entry["field_path"] for entry in payload["source_unit_evidence"]
        ] == [list(ASKS_PATH), list(BIDS_PATH)]
        assert payload["source_unit_evidence"][0]["variability"] == "ROW_NATIVE"
        rebuilt = ProjectionSchemaDefinition.from_descriptor(payload)
        assert rebuilt.schema_fingerprint == declared.schema_fingerprint
        assert list(rebuilt.source_unit_evidence) == list(
            declared.source_unit_evidence
        )


# ---------------------------------------------------------------------------
# §13 — nested static proof
# ---------------------------------------------------------------------------


class TestNestedStaticProof:
    def test_nested_static_claim_is_proven_across_every_level(
        self, tmp_path: Path
    ) -> None:
        lake = _stack(
            tmp_path,
            schema_id="r2.nested.static",
            declarations=[BIDS_STATIC_BTC_EXPLICIT],
        )
        sha = _seed(lake)
        _commit(lake, sha, [_book_row(bid_units=["BTC", "BTC"])])
        batch = _support._handoff_batch(lake, sha, registry=lake.schemas)
        entry = batch.source_unit_evidence[0]
        assert entry.resolved_field_path == BIDS_PATH
        assert entry.state == SourceUnitState.VERIFIED_NATIVE
        assert entry.native_unit_lexeme == "BTC"
        assert entry.variability == SourceUnitVariability.STATIC_VERIFIED

    def test_nested_mixed_levels_are_refused(self, tmp_path: Path) -> None:
        lake = _stack(
            tmp_path,
            schema_id="r2.nested.mixed",
            declarations=[BIDS_STATIC_BTC],
        )
        sha = _seed(lake)
        with pytest.raises(ProjectionUnitEvidenceConflict) as excinfo:
            _commit(lake, sha, [_book_row(bid_units=["BTC", "ETH"])])
        conflict = excinfo.value
        assert conflict.field_path == BIDS_PATH
        assert conflict.conflict_class == "MIXED"
        assert lake.artifacts.list_ids() == []

    def test_nested_wrong_lexeme_is_refused(self, tmp_path: Path) -> None:
        lake = _stack(
            tmp_path,
            schema_id="r2.nested.wrong",
            declarations=[BIDS_STATIC_BTC],
        )
        sha = _seed(lake)
        with pytest.raises(ProjectionUnitEvidenceConflict) as excinfo:
            _commit(lake, sha, [_book_row(bid_units=["ETH"])])
        assert excinfo.value.conflict_class == "MISMATCH"
        assert excinfo.value.field_path == BIDS_PATH


# ---------------------------------------------------------------------------
# §11 — ROW_NATIVE location (no forced static lexeme)
# ---------------------------------------------------------------------------


class TestRowNativeLocation:
    def test_row_native_accepts_per_level_variation(self, tmp_path: Path) -> None:
        lake = _stack(
            tmp_path,
            schema_id="r2.rownative.nested",
            declarations=[BIDS_ROW_NATIVE, ASKS_ROW_NATIVE],
        )
        sha = _seed(lake)
        _commit(
            lake,
            sha,
            [
                _book_row(bid_units=["BTC", "ETH"], ask_units=["USDT"]),
                _book_row(bid_units=["BTC"], ask_units=["BTC", "USDT"]),
            ],
        )
        batch = _support._handoff_batch(lake, sha, registry=lake.schemas)
        assert [
            (e.resolved_field_path, e.state.value, e.variability.value, e.native_unit_lexeme)
            for e in batch.source_unit_evidence
        ] == [
            (ASKS_PATH, "UNIT_UNVERIFIED", "ROW_NATIVE", None),
            (BIDS_PATH, "UNIT_UNVERIFIED", "ROW_NATIVE", None),
        ]

    def test_row_native_scalar_varying_units_commits(self, tmp_path: Path) -> None:
        lake = _scalar_stack(
            tmp_path,
            schema_id="r2.rownative.scalar",
            declarations=[
                SourceUnitEvidence(
                    field_name="quantity_unit",
                    native_unit_lexeme=None,
                    state=SourceUnitState.UNIT_UNVERIFIED,
                    variability=SourceUnitVariability.ROW_NATIVE,
                )
            ],
            contract=SourceUnitContract.UNIT_EVIDENCE_DECLARED,
        )
        sha = _seed(lake)
        rows = [
            {"quantity_unit": "SOL"},
            {"quantity_unit": "BTC"},
        ]
        _commit_scalar(lake, sha, rows)
        batch = _support._handoff_batch(
            lake, sha, registry=lake.schemas
        )
        entry = batch.source_unit_evidence[0]
        assert entry.resolved_field_path == ("quantity_unit",)
        assert entry.variability == SourceUnitVariability.ROW_NATIVE
        assert entry.native_unit_lexeme is None
        assert batch.source_unit_contract == SourceUnitContract.UNIT_EVIDENCE_DECLARED

    def test_row_native_must_not_carry_a_lexeme(self) -> None:
        with pytest.raises(ValueError):
            SourceUnitEvidence(
                field_name="bids",
                field_path=BIDS_PATH,
                native_unit_lexeme="BTC",
                state=SourceUnitState.UNIT_UNVERIFIED,
                variability=SourceUnitVariability.ROW_NATIVE,
            )

    def test_static_variability_requires_verified_state(self) -> None:
        with pytest.raises(ValueError):
            SourceUnitEvidence(
                field_name="bids",
                field_path=BIDS_PATH,
                native_unit_lexeme=None,
                state=SourceUnitState.UNIT_UNVERIFIED,
                variability=SourceUnitVariability.STATIC_VERIFIED,
            )


# ---------------------------------------------------------------------------
# §19/§20 — explicit contract marker vs historical absence
# ---------------------------------------------------------------------------


class TestUnitContractMarker:
    def test_no_unit_fields_marker_round_trips(self) -> None:
        definition = ProjectionSchemaDefinition(
            "r2.contract.none",
            "1.0.0",
            BOOK_SCHEMA,
            source_unit_contract=SourceUnitContract.NO_UNIT_FIELDS,
        )
        payload = definition.to_descriptor()
        assert payload["source_unit_contract"] == "NO_UNIT_FIELDS"
        assert "source_unit_evidence" not in payload
        rebuilt = ProjectionSchemaDefinition.from_descriptor(payload)
        assert rebuilt.source_unit_contract == SourceUnitContract.NO_UNIT_FIELDS
        assert (
            rebuilt.schema_fingerprint
            != ProjectionSchemaDefinition(
                "r2.contract.legacy", "1.0.0", BOOK_SCHEMA
            ).schema_fingerprint
        )

    def test_no_unit_fields_marker_rejects_entries(self) -> None:
        with pytest.raises(ValueError):
            ProjectionSchemaDefinition(
                "r2.contract.bad",
                "1.0.0",
                BOOK_SCHEMA,
                source_unit_evidence=[BIDS_ROW_NATIVE],
                source_unit_contract=SourceUnitContract.NO_UNIT_FIELDS,
            )

    def test_declared_marker_requires_entries(self) -> None:
        with pytest.raises(ValueError):
            ProjectionSchemaDefinition(
                "r2.contract.empty",
                "1.0.0",
                BOOK_SCHEMA,
                source_unit_contract=SourceUnitContract.UNIT_EVIDENCE_DECLARED,
            )

    def test_historical_absence_is_preserved(self) -> None:
        legacy = ProjectionSchemaDefinition("r2.contract.hist", "1.0.0", BOOK_SCHEMA)
        payload = legacy.to_descriptor()
        assert "source_unit_contract" not in payload
        assert legacy.source_unit_contract is None
        assert legacy.schema_fingerprint == compute_schema_fingerprint(BOOK_SCHEMA)
        rebuilt = ProjectionSchemaDefinition.from_descriptor(payload)
        assert rebuilt.source_unit_contract is None

    def test_handoff_copies_the_contract_marker_verbatim(
        self, tmp_path: Path
    ) -> None:
        lake = _stack(
            tmp_path,
            schema_id="r2.contract.copy",
            declarations=None,
            contract=SourceUnitContract.NO_UNIT_FIELDS,
        )
        sha = _seed(lake)
        _commit(lake, sha, [_book_row()])
        batch = _support._handoff_batch(lake, sha, registry=lake.schemas)
        assert batch.source_unit_contract == SourceUnitContract.NO_UNIT_FIELDS
        assert list(batch.source_unit_evidence) == []

    def test_batch_contract_law_fails_closed(self) -> None:
        from datetime import UTC, datetime

        base = dict(
            batch_id="b",
            provider="kraken",
            venue="futures",
            sensor_family=__import__(
                "crypto_sensor_fabric.contracts.enums", fromlist=["SensorFamily"]
            ).SensorFamily.MECHANICAL_TRADE,
            native_instrument="BTC-USDT",
            projection_schema_id="r2.batch",
            projection_schema_version="1.0.0",
            parser_version="1.0.0",
            raw_rows_or_reader="descriptor://proj-r1",
            source_blob_refs=["a" * 64],
            acquisition_refs=["acq-r2"],
            logical_time_range_start=datetime(2026, 1, 15, tzinfo=UTC),
            logical_time_range_end=datetime(2026, 1, 15, 1, tzinfo=UTC),
        )
        with pytest.raises(ValueError):
            RawNormalizationBatch(
                **base,
                source_unit_evidence=[BIDS_ROW_NATIVE],
                source_unit_contract=SourceUnitContract.NO_UNIT_FIELDS,
            )
        with pytest.raises(ValueError):
            RawNormalizationBatch(
                **base,
                source_unit_contract=SourceUnitContract.UNIT_EVIDENCE_DECLARED,
            )


# ---------------------------------------------------------------------------
# scalar-schema helper used by the ROW_NATIVE scalar case
# ---------------------------------------------------------------------------


SCALAR_SCHEMA = pa.schema(
    [
        pa.field("quantity_unit", pa.string(), nullable=False),
    ]
)


def _scalar_stack(tmp_path: Path, *, schema_id: str, declarations, contract=None):
    lake = Lake(tmp_path / "lake")
    definition = ProjectionSchemaDefinition(
        schema_id,
        "1.0.0",
        SCALAR_SCHEMA,
        source_unit_evidence=declarations,
        source_unit_contract=contract,
    )
    lake.schemas.register(definition)
    lake.schema_definition = definition
    return lake


def _commit_scalar(lake, sha: str, rows):
    result = lake.projection_service.commit_projection(
        rows=rows,
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
    return result
