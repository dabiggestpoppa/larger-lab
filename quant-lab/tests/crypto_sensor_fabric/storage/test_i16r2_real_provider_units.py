"""SENSOR-B4-I16R2 §21/§22 — real supported provider-native unit-shape proofs.

Every row payload comes from the committed supported-family fixtures under
``tests/crypto_sensor_fabric/fixtures/`` (offline; no network).  Every
projection is registered, committed, handoffed and consumed through the real
public storage path — these tests never prove a hand-built
``ProjectionSchemaDefinition`` in isolation:

    static scalar      trade / book metric / open interest
    optional           liquidation (real fixture carries null units)
    row/nested         book snapshot (per-level quantity_unit)
    no unit fields     funding / basis / positioning

The §22 public-only consumer probe (``i16r2_bloc5_consumer_probe``) must
distinguish STATIC VERIFIED / UNIT_UNVERIFIED / ROW-NATIVE LOCATION / NO
UNIT-BEARING FIELDS / HISTORICAL CONTRACT ABSENT using public contracts only.
"""

from __future__ import annotations

import ast
import json
import sys
from datetime import UTC, datetime
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

from crypto_sensor_fabric.contracts.enums import SensorFamily  # noqa: E402
from crypto_sensor_fabric.providers.base.enums import Granularity  # noqa: E402
from crypto_sensor_fabric.storage import (  # noqa: E402
    CoverageState,
    IntegrityState,
    PartitionManifest,
    ProjectionSchemaDefinition,
    ProjectionUnitEvidenceConflict,
    SourceUnitContract,
    SourceUnitEvidence,
    SourceUnitState,
    SourceUnitVariability,
)

CURRENT_HEAD = "e8d1384d98771c39cb119e2cae0ff93296be02ec"

_support = load_sibling("i16r1_contract_support", "test_i16r1_unit_contract")
Lake = _support.Lake
consumer = load_sibling("_i16r2_consumer_probe", "i16r2_bloc5_consumer_probe")

FIXTURES = HERE.parent / "fixtures"
FIXED = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)

TRADE_SCHEMA = pa.schema(
    [
        pa.field("price_native", pa.float64(), nullable=False),
        pa.field("quantity_native", pa.float64(), nullable=False),
        pa.field("quantity_unit", pa.string(), nullable=False),
    ]
)
BOOK_METRIC_SCHEMA = pa.schema(
    [
        pa.field("metric_value", pa.float64(), nullable=False),
        pa.field("metric_unit", pa.string(), nullable=False),
    ]
)
OI_SCHEMA = pa.schema(
    [
        pa.field("oi_native", pa.float64(), nullable=False),
        pa.field("native_unit", pa.string(), nullable=False),
    ]
)
LIQUIDATION_SCHEMA = pa.schema(
    [
        pa.field("quantity_native", pa.float64(), nullable=True),
        pa.field("quantity_unit", pa.string(), nullable=True),
    ]
)
_LEVEL = pa.struct(
    [
        pa.field("price", pa.float64(), nullable=False),
        pa.field("quantity", pa.float64(), nullable=False),
        pa.field("quantity_unit", pa.string(), nullable=True),
    ]
)
BOOK_SCHEMA = pa.schema(
    [
        pa.field("sequence_id", pa.string(), nullable=True),
        pa.field("bids", pa.list_(pa.field("item", _LEVEL, nullable=True)), nullable=False),
        pa.field("asks", pa.list_(pa.field("item", _LEVEL, nullable=True)), nullable=False),
    ]
)
FUNDING_SCHEMA = pa.schema(
    [
        pa.field("funding_rate_native", pa.float64(), nullable=False),
        pa.field("funding_interval_seconds", pa.int64(), nullable=False),
        pa.field("predicted_or_realized", pa.string(), nullable=False),
    ]
)
BASIS_SCHEMA = pa.schema(
    [
        pa.field("basis_native", pa.float64(), nullable=False),
        pa.field("reference_price", pa.float64(), nullable=False),
        pa.field("reference_type", pa.string(), nullable=False),
    ]
)
POSITIONING_SCHEMA = pa.schema(
    [
        pa.field("positioning_metric", pa.string(), nullable=False),
        pa.field("long_value", pa.float64(), nullable=False),
        pa.field("short_value", pa.float64(), nullable=False),
        pa.field("ratio_value", pa.float64(), nullable=False),
        pa.field("population_definition", pa.string(), nullable=False),
    ]
)

UNITLESS_CASES = (
    (
        "funding_8h_native.json",
        FUNDING_SCHEMA,
        ("funding_rate_native", "funding_interval_seconds", "predicted_or_realized"),
    ),
    ("basis_valid.json", BASIS_SCHEMA, ("basis_native", "reference_price", "reference_type")),
    (
        "positioning_top_trader.json",
        POSITIONING_SCHEMA,
        (
            "positioning_metric",
            "long_value",
            "short_value",
            "ratio_value",
            "population_definition",
        ),
    ),
)


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _rows(fixture: dict, fields: tuple[str, ...]) -> list[dict]:
    return [{field: fixture[field] for field in fields}]


def _manifest(
    fixture: dict,
    *,
    blob_refs: list[str],
    projection_refs: list[str],
    manifest_id: str,
) -> PartitionManifest:
    partition_key = (
        f"{fixture['provider']}/{fixture['venue']}/"
        f"{fixture['instrument_native']}/2026-01-15"
    )
    return PartitionManifest(
        partition_manifest_id=manifest_id,
        partition_key=partition_key,
        manifest_version=1,
        provider=fixture["provider"],
        venue=fixture["venue"],
        sensor_family=SensorFamily(fixture["sensor_family"]),
        native_instrument=fixture["instrument_native"],
        source_granularity=Granularity.G1M,
        logical_date_start=datetime(2026, 1, 15, tzinfo=UTC),
        logical_date_end=datetime(2026, 1, 15, 23, 59, tzinfo=UTC),
        blob_refs=sorted(blob_refs),
        projection_refs=sorted(projection_refs),
        coverage_state=CoverageState.COMPLETE_SOURCE_BOUNDARY,
        integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
        row_count=None,
        min_time=None,
        max_time=None,
        gap_count=None,
        created_at=FIXED,
        supersedes_manifest_id=None,
    )


def _stack(tmp_path: Path, name: str, *, schema, declarations, contract=None):
    lake = Lake(tmp_path / name)
    definition = ProjectionSchemaDefinition(
        f"i16r2.real.{name}",
        "1.0.0",
        schema,
        source_unit_evidence=declarations,
        source_unit_contract=contract,
    )
    lake.schemas.register(definition)
    lake.schema_definition = definition
    return lake, definition


def _commit(
    lake,
    definition,
    fixture: dict,
    rows: list[dict],
    *,
    projection_id: str = "proj-r1",
):
    raw = json.dumps(fixture, sort_keys=True, ensure_ascii=False).encode("utf-8")
    sha = lake.seed_blob(raw)
    lake.seed_acquisition(
        sha,
        "acq-real",
        provider=fixture["provider"],
        venue=fixture["venue"],
        sensor=fixture["sensor_family"],
        instrument=fixture["instrument_native"],
    )
    partition_key = (
        f"{fixture['provider']}/{fixture['venue']}/"
        f"{fixture['instrument_native']}/2026-01-15"
    )
    lake.projection_service.commit_projection(
        rows=rows,
        schema_definition=definition,
        projection_id=projection_id,
        source_blob_sha256=[sha],
        acquisition_ids=["acq-real"],
        provider=fixture["provider"],
        venue=fixture["venue"],
        sensor_family=fixture["sensor_family"],
        native_instrument=fixture["instrument_native"],
        native_granularity="1m",
        parser_version="1.0.0",
        partition_key=partition_key,
        logical_year=2026,
        logical_month=1,
        logical_day=15,
        lineage_manifest_id=f"lm-{projection_id}",
    )
    lake.resolver_backed_manifests().append_partition_manifest(
        _manifest(
            fixture,
            blob_refs=[sha],
            projection_refs=[projection_id],
            manifest_id=f"pm-{projection_id}",
        ),
        None,
    )
    return sha


def _view(lake, sha):
    batch = _support._handoff_batch(lake, sha, registry=lake.schemas)
    return consumer.unit_evidence_view(batch, schemas=lake.schemas), batch


# ---------------------------------------------------------------------------
# static scalar shapes
# ---------------------------------------------------------------------------


class TestRealStaticScalarShapes:
    def test_trade_quantity_unit_is_statically_verified(
        self, tmp_path: Path
    ) -> None:
        fixture = _fixture("trade_valid.json")
        lake, definition = _stack(
            tmp_path,
            "trade",
            schema=TRADE_SCHEMA,
            declarations=[
                SourceUnitEvidence(
                    field_name="quantity_unit",
                    native_unit_lexeme="BTC",
                    state=SourceUnitState.VERIFIED_NATIVE,
                )
            ],
        )
        sha = _commit(
            lake,
            definition,
            fixture,
            _rows(fixture, ("price_native", "quantity_native", "quantity_unit")),
        )
        view, _batch = _view(lake, sha)
        assert view["contract_state"] == consumer.UNIT_EVIDENCE_DECLARED
        assert view["static_verified"] == [
            {
                "field_path": ["quantity_unit"],
                "state": "VERIFIED_NATIVE",
                "variability": None,
                "native_unit_lexeme": "BTC",
                "classification": "STATIC_VERIFIED",
            }
        ]
        assert view["resolved_schema_declaration_matches_batch"] is True
        assert view["resolved_contract_matches_batch"] is True
        assert view["guessed_values"] == []

    def test_trade_static_mismatch_is_refused(self, tmp_path: Path) -> None:
        fixture = _fixture("trade_valid.json")
        lake, definition = _stack(
            tmp_path,
            "trade-mismatch",
            schema=TRADE_SCHEMA,
            declarations=[
                SourceUnitEvidence(
                    field_name="quantity_unit",
                    native_unit_lexeme="ETH",
                    state=SourceUnitState.VERIFIED_NATIVE,
                )
            ],
        )
        with pytest.raises(ProjectionUnitEvidenceConflict) as excinfo:
            _commit(
                lake,
                definition,
                fixture,
                _rows(fixture, ("price_native", "quantity_native", "quantity_unit")),
            )
        assert excinfo.value.declared_lexeme == "ETH"
        assert excinfo.value.conflict_class == "MISMATCH"
        assert lake.artifacts.list_ids() == []

    def test_book_metric_unit_is_statically_verified(
        self, tmp_path: Path
    ) -> None:
        fixture = _fixture("book_metric_provider.json")
        lake, definition = _stack(
            tmp_path,
            "book-metric",
            schema=BOOK_METRIC_SCHEMA,
            declarations=[
                SourceUnitEvidence(
                    field_name="metric_unit",
                    native_unit_lexeme="BPS",
                    state=SourceUnitState.VERIFIED_NATIVE,
                )
            ],
        )
        sha = _commit(
            lake, definition, fixture, _rows(fixture, ("metric_value", "metric_unit"))
        )
        view, _batch = _view(lake, sha)
        assert view["static_verified"][0]["native_unit_lexeme"] == "BPS"

    def test_open_interest_unit_is_statically_verified(
        self, tmp_path: Path
    ) -> None:
        fixture = _fixture("oi_contracts_native.json")
        lake, definition = _stack(
            tmp_path,
            "open-interest",
            schema=OI_SCHEMA,
            declarations=[
                SourceUnitEvidence(
                    field_name="native_unit",
                    native_unit_lexeme="CONTRACTS",
                    state=SourceUnitState.VERIFIED_NATIVE,
                )
            ],
        )
        sha = _commit(
            lake, definition, fixture, _rows(fixture, ("oi_native", "native_unit"))
        )
        view, _batch = _view(lake, sha)
        assert view["static_verified"][0]["native_unit_lexeme"] == "CONTRACTS"


# ---------------------------------------------------------------------------
# optional / unverified shape
# ---------------------------------------------------------------------------


class TestRealOptionalShape:
    def test_liquidation_optional_unit_stays_explicitly_unverified(
        self, tmp_path: Path
    ) -> None:
        fixture = _fixture("liquidation_interval_aggregate.json")
        lake, definition = _stack(
            tmp_path,
            "liquidation",
            schema=LIQUIDATION_SCHEMA,
            declarations=[
                SourceUnitEvidence(
                    field_name="quantity_unit",
                    native_unit_lexeme=None,
                    state=SourceUnitState.UNIT_UNVERIFIED,
                )
            ],
            contract=SourceUnitContract.UNIT_EVIDENCE_DECLARED,
        )
        sha = _commit(
            lake,
            definition,
            fixture,
            _rows(fixture, ("quantity_native", "quantity_unit")),
        )
        view, _batch = _view(lake, sha)
        assert view["unverified"] == [
            {
                "field_path": ["quantity_unit"],
                "state": "UNIT_UNVERIFIED",
                "variability": None,
                "native_unit_lexeme": None,
                "classification": "UNIT_UNVERIFIED",
            }
        ]
        assert view["static_verified"] == []
        assert view["guessed_values"] == []
        assert view["resolved_contract_matches_batch"] is True

    def test_liquidation_static_claim_is_refused_by_real_nulls(
        self, tmp_path: Path
    ) -> None:
        fixture = _fixture("liquidation_interval_aggregate.json")
        lake, definition = _stack(
            tmp_path,
            "liquidation-null",
            schema=LIQUIDATION_SCHEMA,
            declarations=[
                SourceUnitEvidence(
                    field_name="quantity_unit",
                    native_unit_lexeme="USDT",
                    state=SourceUnitState.VERIFIED_NATIVE,
                )
            ],
        )
        with pytest.raises(ProjectionUnitEvidenceConflict) as excinfo:
            _commit(
                lake,
                definition,
                fixture,
                _rows(fixture, ("quantity_native", "quantity_unit")),
            )
        assert excinfo.value.conflict_class == "ALL_NULL"
        assert excinfo.value.null_count == 1


# ---------------------------------------------------------------------------
# row/nested shape
# ---------------------------------------------------------------------------


class TestRealNestedShape:
    def _book_rows(self, fixture: dict, *, flip_bid_unit: str | None = None):
        bids = [dict(level) for level in fixture["bids"]]
        asks = [dict(level) for level in fixture["asks"]]
        if flip_bid_unit is not None:
            # flip the SECOND level so the scan observes [declared, other] and
            # reports the row-varying MIXED class (the spec's §3 case)
            bids[1]["quantity_unit"] = flip_bid_unit
        return [
            {
                "sequence_id": fixture["source_record_id"],
                "bids": bids,
                "asks": asks,
            }
        ]

    def test_book_snapshot_row_native_location_for_every_level_column(
        self, tmp_path: Path
    ) -> None:
        fixture = _fixture("book_snapshot_l2.json")
        lake, definition = _stack(
            tmp_path,
            "book-snapshot",
            schema=BOOK_SCHEMA,
            declarations=[
                SourceUnitEvidence(
                    field_name="bids",
                    field_path=("bids", "item", "quantity_unit"),
                    native_unit_lexeme=None,
                    state=SourceUnitState.UNIT_UNVERIFIED,
                    variability=SourceUnitVariability.ROW_NATIVE,
                ),
                SourceUnitEvidence(
                    field_name="asks",
                    field_path=("asks", "item", "quantity_unit"),
                    native_unit_lexeme=None,
                    state=SourceUnitState.UNIT_UNVERIFIED,
                    variability=SourceUnitVariability.ROW_NATIVE,
                ),
            ],
        )
        sha = _commit(lake, definition, fixture, self._book_rows(fixture))
        view, _batch = _view(lake, sha)
        assert [
            entry["field_path"] for entry in view["row_native_locations"]
        ] == [["asks", "item", "quantity_unit"], ["bids", "item", "quantity_unit"]]
        assert view["static_verified"] == []
        assert view["guessed_values"] == []
        assert view["resolved_schema_declaration_matches_batch"] is True

    def test_book_snapshot_nested_static_claim_is_proven_by_fixture_levels(
        self, tmp_path: Path
    ) -> None:
        fixture = _fixture("book_snapshot_l2.json")
        lake, definition = _stack(
            tmp_path,
            "book-snapshot-static",
            schema=BOOK_SCHEMA,
            declarations=[
                SourceUnitEvidence(
                    field_name="bids",
                    field_path=("bids", "item", "quantity_unit"),
                    native_unit_lexeme="BTC",
                    state=SourceUnitState.VERIFIED_NATIVE,
                )
            ],
        )
        sha = _commit(lake, definition, fixture, self._book_rows(fixture))
        view, _batch = _view(lake, sha)
        assert view["static_verified"][0]["field_path"] == [
            "bids",
            "item",
            "quantity_unit",
        ]
        assert view["static_verified"][0]["native_unit_lexeme"] == "BTC"

    def test_book_snapshot_mixed_levels_are_refused(self, tmp_path: Path) -> None:
        fixture = _fixture("book_snapshot_l2.json")
        lake, definition = _stack(
            tmp_path,
            "book-snapshot-mixed",
            schema=BOOK_SCHEMA,
            declarations=[
                SourceUnitEvidence(
                    field_name="bids",
                    field_path=("bids", "item", "quantity_unit"),
                    native_unit_lexeme="BTC",
                    state=SourceUnitState.VERIFIED_NATIVE,
                )
            ],
        )
        with pytest.raises(ProjectionUnitEvidenceConflict) as excinfo:
            _commit(
                lake,
                definition,
                fixture,
                self._book_rows(fixture, flip_bid_unit="ETH"),
            )
        assert excinfo.value.conflict_class == "MIXED"
        assert excinfo.value.field_path == ("bids", "item", "quantity_unit")


# ---------------------------------------------------------------------------
# unitless families
# ---------------------------------------------------------------------------


class TestRealUnitlessFamilies:
    @pytest.mark.parametrize("fixture_name,schema,fields", UNITLESS_CASES)
    def test_explicit_no_unit_fields(
        self, tmp_path: Path, fixture_name: str, schema, fields
    ) -> None:
        fixture = _fixture(fixture_name)
        lake, definition = _stack(
            tmp_path,
            f"unitless-{fixture_name.replace('.json', '')}",
            schema=schema,
            declarations=None,
            contract=SourceUnitContract.NO_UNIT_FIELDS,
        )
        sha = _commit(lake, definition, fixture, _rows(fixture, fields))
        view, _batch = _view(lake, sha)
        assert view["contract_state"] == consumer.NO_UNIT_FIELDS
        assert view["no_unit_bearing_fields"] is True
        assert view["entries"] == []
        assert view["historical_contract_absent"] is False

    @pytest.mark.parametrize("fixture_name,schema,fields", UNITLESS_CASES)
    def test_historical_absence_is_distinguishable(
        self, tmp_path: Path, fixture_name: str, schema, fields
    ) -> None:
        fixture = _fixture(fixture_name)
        lake, definition = _stack(
            tmp_path,
            f"legacy-{fixture_name.replace('.json', '')}",
            schema=schema,
            declarations=None,
        )
        sha = _commit(lake, definition, fixture, _rows(fixture, fields))
        view, _batch = _view(lake, sha)
        assert view["contract_state"] == consumer.HISTORICAL_UNIT_CONTRACT_ABSENT
        assert view["historical_contract_absent"] is True
        assert view["no_unit_bearing_fields"] is False
        assert view["entries"] == []


# ---------------------------------------------------------------------------
# consumer contract (§22)
# ---------------------------------------------------------------------------


class TestConsumerContract:
    def test_probe_uses_only_public_contracts_and_no_filesystem(self) -> None:
        source = (HERE / "i16r2_bloc5_consumer_probe.py").read_text(
            encoding="utf-8"
        )
        tree = ast.parse(source)
        forbidden_modules = {"os", "pathlib", "glob", "shutil", "tempfile", "sys"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert root not in forbidden_modules, root
                    assert root in {"typing"}, alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                root = module.split(".")[0]
                assert root not in forbidden_modules, module
                assert module.startswith("crypto_sensor_fabric.storage") or module in {
                    "__future__",
                    "typing",
                }, module
                for alias in node.names:
                    assert not alias.name.startswith("_"), alias.name
            elif isinstance(node, ast.Attribute):
                assert not (
                    node.attr.startswith("_") and not node.attr.startswith("__")
                ), node.attr
        # No provider-adapter or normalization module may be reachable from
        # the probe: the import whitelist above proves it structurally; the
        # name scans below are belt-and-braces on call sites only.
        assert "crypto_sensor_fabric.providers" not in source
        assert "from crypto_sensor_fabric.normalization" not in source

    def test_evidence_view_is_path_independent(self, tmp_path: Path) -> None:
        fixture = _fixture("trade_valid.json")
        views = []
        for root in ("left", "right"):
            lake, definition = _stack(
                tmp_path / root,
                "path",
                schema=TRADE_SCHEMA,
                declarations=[
                    SourceUnitEvidence(
                        field_name="quantity_unit",
                        native_unit_lexeme="BTC",
                        state=SourceUnitState.VERIFIED_NATIVE,
                    )
                ],
            )
            sha = _commit(
                lake,
                definition,
                fixture,
                _rows(fixture, ("price_native", "quantity_native", "quantity_unit")),
            )
            view, _batch = _view(lake, sha)
            views.append(view)
        assert views[0] == views[1]

    def test_five_unit_states_are_distinguishable(self, tmp_path: Path) -> None:
        """One consumer sees all five UNIT states, public contracts only."""
        # static verified
        fixture = _fixture("trade_valid.json")
        lake, definition = _stack(
            tmp_path,
            "five-static",
            schema=TRADE_SCHEMA,
            declarations=[
                SourceUnitEvidence(
                    field_name="quantity_unit",
                    native_unit_lexeme="BTC",
                    state=SourceUnitState.VERIFIED_NATIVE,
                )
            ],
        )
        sha = _commit(
            lake,
            definition,
            fixture,
            _rows(fixture, ("price_native", "quantity_native", "quantity_unit")),
        )
        static_view, _ = _view(lake, sha)
        # unverified
        lake2, definition2 = _stack(
            tmp_path,
            "five-unknown",
            schema=TRADE_SCHEMA,
            declarations=[
                SourceUnitEvidence(
                    field_name="quantity_unit",
                    native_unit_lexeme=None,
                    state=SourceUnitState.UNIT_UNVERIFIED,
                )
            ],
        )
        sha2 = _commit(
            lake2,
            definition2,
            fixture,
            _rows(fixture, ("price_native", "quantity_native", "quantity_unit")),
        )
        unknown_view, _ = _view(lake2, sha2)
        # row-native
        book = _fixture("book_snapshot_l2.json")
        lake3, definition3 = _stack(
            tmp_path,
            "five-row-native",
            schema=BOOK_SCHEMA,
            declarations=[
                SourceUnitEvidence(
                    field_name="bids",
                    field_path=("bids", "item", "quantity_unit"),
                    native_unit_lexeme=None,
                    state=SourceUnitState.UNIT_UNVERIFIED,
                    variability=SourceUnitVariability.ROW_NATIVE,
                )
            ],
        )
        sha3 = _commit(
            lake3,
            definition3,
            book,
            [{"sequence_id": "1", "bids": book["bids"], "asks": book["asks"]}],
        )
        row_view, _ = _view(lake3, sha3)
        # no unit fields
        funding = _fixture("funding_8h_native.json")
        lake4, definition4 = _stack(
            tmp_path,
            "five-none",
            schema=FUNDING_SCHEMA,
            declarations=None,
            contract=SourceUnitContract.NO_UNIT_FIELDS,
        )
        sha4 = _commit(
            lake4,
            definition4,
            funding,
            _rows(
                funding,
                ("funding_rate_native", "funding_interval_seconds", "predicted_or_realized"),
            ),
        )
        none_view, _ = _view(lake4, sha4)
        # historical absent
        lake5, definition5 = _stack(
            tmp_path,
            "five-historical",
            schema=FUNDING_SCHEMA,
            declarations=None,
        )
        sha5 = _commit(
            lake5,
            definition5,
            funding,
            _rows(
                funding,
                ("funding_rate_native", "funding_interval_seconds", "predicted_or_realized"),
            ),
        )
        historical_view, _ = _view(lake5, sha5)

        states = {
            static_view["contract_state"],
            unknown_view["contract_state"],
            row_view["contract_state"],
            none_view["contract_state"],
            historical_view["contract_state"],
        }
        assert static_view["static_verified"]
        assert unknown_view["unverified"]
        assert row_view["row_native_locations"]
        assert none_view["no_unit_bearing_fields"] is True
        assert historical_view["historical_contract_absent"] is True
        assert len(states) == 3  # declared (x3), NO_UNIT_FIELDS, historical
