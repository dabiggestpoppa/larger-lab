"""Versioning / serialization tests (B1-T60 .. B1-T63)."""

from __future__ import annotations

import pytest
from crypto_sensor_fabric.contracts.base import (
    canonical_bytes,
    canonical_dump,
    canonical_hash,
)
from crypto_sensor_fabric.schemas import MechanicalFunding, MechanicalOpenInterest
from crypto_sensor_fabric.schemas.export import (
    SNAPSHOT_MODELS,
    export_all_schemas,
    export_schema,
    load_snapshot,
)
from crypto_sensor_fabric.testing import load_fixture_json

# ---------------------------------------------------------------------------
# B1-T60 — schema version present
# ---------------------------------------------------------------------------


def test_t60_serialized_observation_has_schema_version(load_model):
    from crypto_sensor_fabric.schemas import MechanicalTrade

    trade = load_model(MechanicalTrade, "trade_valid.json")
    dumped = canonical_dump(trade)
    assert dumped["schema_version"] == trade.schema_version == "1.0.0"


@pytest.mark.parametrize("fixture", ["trade_valid.json", "oi_contracts_native.json"])
def test_t60_all_serialized_records_carry_schema_version(load_model, fixture):
    from crypto_sensor_fabric.schemas import MechanicalOpenInterest, MechanicalTrade

    model_cls = (
        MechanicalOpenInterest if fixture.startswith("oi") else MechanicalTrade
    )
    record = load_model(model_cls, fixture)
    assert record.model_dump(mode="json")["schema_version"] == "1.0.0"


# ---------------------------------------------------------------------------
# B1-T61 — methodology version present when normalized
# ---------------------------------------------------------------------------


def test_t61_normalized_oi_carries_versions(load_model):
    oi = load_model(MechanicalOpenInterest, "oi_contracts_native.json")
    assert oi.normalization_version == "1.0"
    assert oi.methodology_version == "1"
    assert oi.normalization_method == "OI_CONTRACTS_TO_USD_V1"


def test_t61_normalized_funding_carries_versions(load_model):
    funding = load_model(MechanicalFunding, "funding_8h_native.json")
    assert funding.normalization_version == "1.0"
    assert funding.methodology_version == "1"


def test_t61_native_only_record_may_omit_normalization_versions(load_model):
    funding = load_model(MechanicalFunding, "funding_non8h_native.json")
    assert funding.funding_rate_8h_equivalent is None
    assert funding.normalization_version is None
    assert funding.methodology_version is None


# ---------------------------------------------------------------------------
# B1-T62 — deterministic serialization
# ---------------------------------------------------------------------------


def test_t62_same_object_stable_bytes(load_model):
    from crypto_sensor_fabric.schemas import MechanicalTrade

    trade = load_model(MechanicalTrade, "trade_valid.json")
    assert canonical_bytes(trade) == canonical_bytes(trade)
    assert canonical_hash(trade) == canonical_hash(trade)


def test_t62_equivalent_instances_identical_hash():
    payload = load_fixture_json("trade_valid.json")
    from crypto_sensor_fabric.schemas import MechanicalTrade

    first = MechanicalTrade.model_validate(payload)
    second = MechanicalTrade.model_validate(payload)
    assert canonical_bytes(first) == canonical_bytes(second)
    assert canonical_hash(first) == canonical_hash(second)


def test_t62_mutation_changes_hash(load_model):
    from crypto_sensor_fabric.schemas import MechanicalTrade

    trade = load_model(MechanicalTrade, "trade_valid.json")
    baseline = canonical_hash(trade)
    payload = trade.model_dump(mode="json")
    payload["price_native"] = 99999
    mutated = MechanicalTrade.model_validate(payload)
    assert canonical_hash(mutated) != baseline


def test_t62_different_models_differ():
    payload = load_fixture_json("trade_valid.json")
    from crypto_sensor_fabric.schemas import MechanicalTrade

    trade = MechanicalTrade.model_validate(payload)
    liq_payload = load_fixture_json("liquidation_trade_level.json")
    from crypto_sensor_fabric.schemas import MechanicalLiquidation

    liq = MechanicalLiquidation.model_validate(liq_payload)
    assert canonical_bytes(trade) != canonical_bytes(liq)


# ---------------------------------------------------------------------------
# B1-T63 — JSON Schema snapshots
# ---------------------------------------------------------------------------


def test_t63_snapshots_are_committed_and_current():
    """Regenerate in-memory and compare with committed snapshots.

    Any mismatch means the committed schema snapshot is stale: run
    `python tools/export_sensor_fabric_schemas.py` and commit the update.
    """
    current = export_all_schemas()
    assert set(current) == set(SNAPSHOT_MODELS)
    for name, content in current.items():
        committed = load_snapshot(name)
        assert content == committed, (
            f"schema snapshot {name}.schema.json is stale; "
            "regenerate with python tools/export_sensor_fabric_schemas.py"
        )


def test_t63_every_schema_model_is_snapshotted():
    from crypto_sensor_fabric.contracts.access import FreeOnlyPolicy
    from crypto_sensor_fabric.contracts.base import (
        CanonicalObservationBase,
        MissingObservation,
    )
    from crypto_sensor_fabric.contracts.identity import InstrumentIdentity
    from crypto_sensor_fabric.schemas import (
        MechanicalBasis,
        MechanicalBookMetric,
        MechanicalBookSnapshot,
        MechanicalFunding,
        MechanicalLiquidation,
        MechanicalOpenInterest,
        MechanicalPositioning,
        MechanicalTrade,
        PriceLevel,
        ProviderEnvelope,
    )

    all_models = {
        model.__name__: model
        for model in (
            CanonicalObservationBase,
            ProviderEnvelope,
            PriceLevel,
            MechanicalTrade,
            MechanicalLiquidation,
            MechanicalOpenInterest,
            MechanicalFunding,
            MechanicalBookSnapshot,
            MechanicalBookMetric,
            MechanicalPositioning,
            MechanicalBasis,
            MissingObservation,
            FreeOnlyPolicy,
            InstrumentIdentity,
        )
    }
    assert set(SNAPSHOT_MODELS) == set(all_models)


def test_t63_schema_export_is_deterministic():
    from crypto_sensor_fabric.schemas import MechanicalTrade

    assert export_schema(MechanicalTrade) == export_schema(MechanicalTrade)


def test_t63_snapshot_has_required_provenance_fields():
    snapshot = load_snapshot("MechanicalTrade")
    assert '"raw_object_uri"' in snapshot
    assert '"raw_checksum"' in snapshot
    assert '"provider"' in snapshot
    assert '"schema_version"' in snapshot
