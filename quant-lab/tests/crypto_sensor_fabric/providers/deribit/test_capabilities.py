"""SENSOR-B3-I08A — Deribit capability + native acquisition-mode freeze.

Proves the I14-bounded Deribit production set (EXACTLY four paths), exact I14
equality, roles (BOOK_SNAPSHOT CURRENT_ONLY, FUNDING SECONDARY, LIQUIDATION +
TRADE MECHANISM_MICROSCOPE), the evidence-derived production symbol scope
(BTC-PERPETUAL only; probe ETH/SOL excluded), native acquisition-mode evidence
(REST_RANGE + TIME_RANGE for the three HISTORICAL surfaces; no historical
grant for the CURRENT_ONLY book), and that all grants resolve to I14 without
broadening.
"""

from __future__ import annotations

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.probes.enums import ProviderRole
from crypto_sensor_fabric.providers.base import (
    ProviderNativeCapabilityEvidence,
    capabilities_from_promotion,
    load_promotion_candidates,
    native_evidence_violations,
)
from crypto_sensor_fabric.providers.base.enums import (
    HistoricalMode,
    PaginationMode,
)
from crypto_sensor_fabric.providers.deribit import (
    DERIBIT_PRODUCTION_INSTRUMENT_SCOPE,
    DERIBIT_PROBE_INSTRUMENT_SCOPE,
    DERIBIT_PROMOTED_SENSORS,
    DERIBIT_SYMBOL_SCOPES,
    PROVIDER_ID,
    build_deribit_capabilities,
    deribit_endpoint_family,
    deribit_native_evidence,
)
from crypto_sensor_fabric.providers.deribit.capabilities import _PROMOTED_ORDER

ALL_PROMOTED = _PROMOTED_ORDER
BOOK = SensorFamily.MECHANICAL_BOOK_SNAPSHOT
FUNDING = SensorFamily.MECHANICAL_FUNDING
LIQUIDATION = SensorFamily.MECHANICAL_LIQUIDATION
TRADE = SensorFamily.MECHANICAL_TRADE


class TestProviderIdentity:
    def test_provider_id_frozen(self) -> None:
        assert PROVIDER_ID == "DERIBIT"
        caps = build_deribit_capabilities()
        assert caps.provider_id == "DERIBIT"


class TestExactPromotedSet:
    def test_exactly_four_promoted_sensors(self) -> None:
        caps = build_deribit_capabilities()
        supported = set(caps.supported_sensors())
        assert len(supported) == 4
        assert supported == set(ALL_PROMOTED)
        assert supported == set(DERIBIT_PROMOTED_SENSORS)

    def test_exact_i14_equality(self) -> None:
        """Declared Deribit production set == I14 Deribit promotion set (no 5th path)."""
        promoted = capabilities_from_promotion(PROVIDER_ID, load_promotion_candidates())
        i14_deribit = {s for s, c in promoted.sensors.items() if c.supported}
        assert i14_deribit == set(ALL_PROMOTED)
        declared = set(build_deribit_capabilities().supported_sensors())
        assert declared == i14_deribit
        assert BOOK in declared
        assert FUNDING in declared
        assert LIQUIDATION in declared
        assert TRADE in declared

    def test_unsupported_deribit_sensors_not_promoted(self) -> None:
        caps = build_deribit_capabilities()
        for sensor in (
            SensorFamily.MECHANICAL_BASIS,
            SensorFamily.MECHANICAL_BOOK_METRIC,
            SensorFamily.MECHANICAL_OPEN_INTEREST,
            SensorFamily.MECHANICAL_POSITIONING,
        ):
            assert caps.capability_for(sensor).supported is False, sensor


class TestRoles:
    def test_book_snapshot_is_current_only(self) -> None:
        cap = build_deribit_capabilities().capability_for(BOOK)
        assert cap.allowed_role is ProviderRole.CURRENT_ONLY
        assert cap.supported is True
        # CURRENT_ONLY must NEVER claim a historical/rest acquisition mode.
        assert cap.historical_mode is None

    def test_funding_is_secondary_historical(self) -> None:
        cap = build_deribit_capabilities().capability_for(FUNDING)
        assert cap.allowed_role is ProviderRole.SECONDARY
        assert cap.history_scope.value == "HISTORICAL"
        assert cap.probe_evidence_ref is not None

    def test_liquidation_and_trade_are_mechanism_microscope(self) -> None:
        caps = build_deribit_capabilities()
        for sensor in (LIQUIDATION, TRADE):
            cap = caps.capability_for(sensor)
            assert cap.allowed_role is ProviderRole.MECHANISM_MICROSCOPE, sensor
            assert cap.history_scope.value == "HISTORICAL", sensor
            assert cap.probe_evidence_ref is not None, sensor


class TestProductionSymbolScope:
    def test_production_scope_derives_from_evidence(self) -> None:
        # 08_HISTORY_BOUNDARIES.csv evidences BTC-PERPETUAL for all four
        # promoted Deribit paths; the production union is exactly BTC-PERPETUAL.
        assert DERIBIT_PRODUCTION_INSTRUMENT_SCOPE == ["BTC-PERPETUAL"]

    def test_probe_scope_keeps_probe_universe(self) -> None:
        assert DERIBIT_PROBE_INSTRUMENT_SCOPE == [
            "BTC-PERPETUAL",
            "ETH-PERPETUAL",
            "SOL-PERPETUAL",
        ]

    def test_sensor_specific_symbol_scopes(self) -> None:
        for sensor in ALL_PROMOTED:
            assert DERIBIT_SYMBOL_SCOPES[sensor] == ("BTC-PERPETUAL",), sensor

    def test_capability_symbol_scope_per_sensor(self) -> None:
        caps = build_deribit_capabilities()
        for sensor in ALL_PROMOTED:
            cap = caps.capability_for(sensor)
            assert cap.symbol_scope == ["BTC-PERPETUAL"], sensor

    def test_probe_only_symbols_never_in_production_capability(self) -> None:
        caps = build_deribit_capabilities()
        for sensor in ALL_PROMOTED:
            assert "ETH-PERPETUAL" not in caps.capability_for(sensor).symbol_scope
            assert "SOL-PERPETUAL" not in caps.capability_for(sensor).symbol_scope


class TestNativeEvidence:
    def test_historical_sensors_have_grants_only(self) -> None:
        evidence = deribit_native_evidence()
        assert set(evidence.keys()) == {FUNDING, LIQUIDATION, TRADE}
        assert BOOK not in evidence  # CURRENT_ONLY: no historical grant
        for sensor in (FUNDING, LIQUIDATION, TRADE):
            assert isinstance(evidence[sensor], ProviderNativeCapabilityEvidence)

    def test_funding_grant_mechanics(self) -> None:
        ev = deribit_native_evidence()[FUNDING]
        assert ev.historical_mode is HistoricalMode.REST_RANGE
        assert ev.pagination_mode is PaginationMode.TIME_RANGE
        assert ev.endpoint_family == "deribit-get-funding-rate-history"
        assert ev.start_param == "start_timestamp"
        assert ev.start_unit == "epoch_milliseconds (request unit)"
        assert ev.end_param == "end_timestamp"
        assert ev.end_unit == "epoch_milliseconds (request unit)"
        assert ev.interval_param is None
        assert ev.instruments == ("BTC-PERPETUAL",)

    def test_trade_grant_mechanics(self) -> None:
        ev = deribit_native_evidence()[TRADE]
        assert ev.historical_mode is HistoricalMode.REST_RANGE
        assert ev.pagination_mode is PaginationMode.TIME_RANGE
        assert ev.endpoint_family == "deribit-get-last-trades-by-instrument"
        assert ev.start_param == "start_timestamp"
        assert ev.end_param == "end_timestamp"
        assert ev.interval_param is None
        assert ev.instruments == ("BTC-PERPETUAL",)

    def test_liquidation_grant_mechanics_same_physical_surface(self) -> None:
        # LIQUIDATION shares the physical get_last_trades_by_instrument surface
        # with TRADE but is a distinct logical sensor (mechanism microscope).
        ev = deribit_native_evidence()[LIQUIDATION]
        assert ev.historical_mode is HistoricalMode.REST_RANGE
        assert ev.pagination_mode is PaginationMode.TIME_RANGE
        assert ev.endpoint_family == "deribit-get-last-trades-by-instrument"
        assert ev.instruments == ("BTC-PERPETUAL",)
        assert ev.methodology_pin == "deribit-trade-level-liquidation-anatomy"

    def test_grants_resolve_to_i14_and_never_broaden(self) -> None:
        promoted = capabilities_from_promotion(PROVIDER_ID, load_promotion_candidates())
        evidence = deribit_native_evidence()
        for sensor in (FUNDING, LIQUIDATION, TRADE):
            vio = native_evidence_violations(
                PROVIDER_ID, evidence[sensor], promoted.capability_for(sensor)
            )
            assert vio == [], f"{sensor}: {vio}"
            for eid in evidence[sensor].evidence_ids:
                assert eid in promoted.capability_for(sensor).evidence_basis

    def test_endpoint_family_mapping(self) -> None:
        assert deribit_endpoint_family(BOOK) == "deribit-get-order-book"
        assert deribit_endpoint_family(FUNDING) == "deribit-get-funding-rate-history"
        assert deribit_endpoint_family(LIQUIDATION) == "deribit-get-last-trades-by-instrument"
        assert deribit_endpoint_family(TRADE) == "deribit-get-last-trades-by-instrument"

    def test_book_capability_stays_current_only(self) -> None:
        caps = build_deribit_capabilities()
        cap = caps.capability_for(BOOK)
        assert cap.supported is True
        assert cap.history_scope.value == "CURRENT_ONLY"
        assert cap.historical_mode is None

    def test_liquidation_scope_is_not_interval_total(self) -> None:
        # MECHANISM_MICROSCOPE must never become general aggregate truth
        # (promotion_bound_violations check #19 covers role equality).
        cap = build_deribit_capabilities().capability_for(LIQUIDATION)
        assert cap.allowed_role is ProviderRole.MECHANISM_MICROSCOPE