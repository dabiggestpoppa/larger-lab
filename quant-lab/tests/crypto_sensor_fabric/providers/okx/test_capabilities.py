"""SENSOR-B3-I07A — OKX Swap capability + native acquisition-mode freeze.

Proves the I14-bounded OKX production set (EXACTLY three paths), exact I14
equality, roles (BOOK_SNAPSHOT CURRENT_ONLY, FUNDING + TRADE PRIMARY), the
evidence-derived production symbol scope (BTC-USDT-SWAP only; probe
ETH/SOL/DOGE excluded), native acquisition-mode evidence (REST_CURSOR for the
two HISTORICAL surfaces; no historical grant for the CURRENT_ONLY book), and
that all grants resolve to I14 without broadening.
"""

from __future__ import annotations

from crypto_sensor_fabric.contracts.enums import SensorFamily
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
from crypto_sensor_fabric.providers.okx import (
    OKX_PRODUCTION_INSTRUMENT_SCOPE,
    OKX_PROBE_INSTRUMENT_SCOPE,
    OKX_PROMOTED_SENSORS,
    OKX_SYMBOL_SCOPES,
    PROVIDER_ID,
    build_okx_capabilities,
    okx_endpoint_family,
    okx_native_evidence,
)
from crypto_sensor_fabric.providers.okx.capabilities import _PROMOTED_ORDER

ALL_PROMOTED = _PROMOTED_ORDER
BOOK = SensorFamily.MECHANICAL_BOOK_SNAPSHOT
FUNDING = SensorFamily.MECHANICAL_FUNDING
TRADE = SensorFamily.MECHANICAL_TRADE


class TestProviderIdentity:
    def test_provider_id_frozen(self) -> None:
        assert PROVIDER_ID == "OKX_SWAP"
        caps = build_okx_capabilities()
        assert caps.provider_id == "OKX_SWAP"


class TestExactPromotedSet:
    def test_exactly_three_promoted_sensors(self) -> None:
        caps = build_okx_capabilities()
        supported = set(caps.supported_sensors())
        assert len(supported) == 3
        assert supported == set(ALL_PROMOTED)
        assert supported == set(OKX_PROMOTED_SENSORS)

    def test_exact_i14_equality(self) -> None:
        """Declared OKX production set == I14 OKX promotion set (no 4th path)."""
        promoted = capabilities_from_promotion(PROVIDER_ID, load_promotion_candidates())
        i14_okx = {s for s, c in promoted.sensors.items() if c.supported}
        assert i14_okx == set(ALL_PROMOTED)
        declared = set(build_okx_capabilities().supported_sensors())
        assert declared == i14_okx
        assert BOOK in declared
        assert FUNDING in declared
        assert TRADE in declared

    def test_unsupported_okx_sensors_not_promoted(self) -> None:
        caps = build_okx_capabilities()
        for sensor in (
            SensorFamily.MECHANICAL_BASIS,
            SensorFamily.MECHANICAL_BOOK_METRIC,
            SensorFamily.MECHANICAL_LIQUIDATION,
            SensorFamily.MECHANICAL_OPEN_INTEREST,
            SensorFamily.MECHANICAL_POSITIONING,
        ):
            assert caps.capability_for(sensor).supported is False, sensor


class TestRoles:
    def test_book_snapshot_is_current_only(self) -> None:
        from crypto_sensor_fabric.probes.enums import ProviderRole

        cap = build_okx_capabilities().capability_for(BOOK)
        assert cap.allowed_role is ProviderRole.CURRENT_ONLY
        assert cap.supported is True
        # CURRENT_ONLY must NEVER claim a historical/rest acquisition mode.
        assert cap.historical_mode is None

    def test_funding_and_trade_are_primary_historical(self) -> None:
        from crypto_sensor_fabric.probes.enums import ProviderRole

        caps = build_okx_capabilities()
        for sensor in (FUNDING, TRADE):
            cap = caps.capability_for(sensor)
            assert cap.allowed_role is ProviderRole.PRIMARY, sensor
            assert cap.probe_evidence_ref is not None, sensor


class TestProductionSymbolScope:
    def test_production_scope_derives_from_evidence(self) -> None:
        # 08_HISTORY_BOUNDARIES.csv evidences BTC-USDT-SWAP for all three
        # promoted OKX paths; the production union is exactly BTC-USDT-SWAP.
        assert OKX_PRODUCTION_INSTRUMENT_SCOPE == ["BTC-USDT-SWAP"]

    def test_probe_scope_keeps_probe_universe(self) -> None:
        assert OKX_PROBE_INSTRUMENT_SCOPE == [
            "BTC-USDT-SWAP",
            "ETH-USDT-SWAP",
            "SOL-USDT-SWAP",
            "DOGE-USDT-SWAP",
        ]

    def test_sensor_specific_symbol_scopes(self) -> None:
        for sensor in ALL_PROMOTED:
            assert OKX_SYMBOL_SCOPES[sensor] == ("BTC-USDT-SWAP",), sensor

    def test_capability_symbol_scope_per_sensor(self) -> None:
        caps = build_okx_capabilities()
        for sensor in ALL_PROMOTED:
            cap = caps.capability_for(sensor)
            assert cap.symbol_scope == ["BTC-USDT-SWAP"], sensor

    def test_probe_only_symbols_never_in_production_capability(self) -> None:
        caps = build_okx_capabilities()
        for sensor in ALL_PROMOTED:
            assert "ETH-USDT-SWAP" not in caps.capability_for(sensor).symbol_scope
            assert "SOL-USDT-SWAP" not in caps.capability_for(sensor).symbol_scope
            assert "DOGE-USDT-SWAP" not in caps.capability_for(sensor).symbol_scope


class TestNativeEvidence:
    def test_funding_and_trade_have_grants_only(self) -> None:
        evidence = okx_native_evidence()
        assert set(evidence.keys()) == {FUNDING, TRADE}
        assert BOOK not in evidence  # CURRENT_ONLY: no historical grant
        for sensor in (FUNDING, TRADE):
            assert isinstance(evidence[sensor], ProviderNativeCapabilityEvidence)

    def test_funding_grant_mechanics(self) -> None:
        ev = okx_native_evidence()[FUNDING]
        assert ev.historical_mode is HistoricalMode.REST_CURSOR
        assert ev.pagination_mode is PaginationMode.CURSOR
        assert ev.endpoint_family == "okx-swap-funding-rate-history"
        assert ev.start_param == "after"
        assert ev.start_unit == "epoch_milliseconds (fundingTime keyed)"
        assert ev.end_param == "before"
        assert ev.end_unit == "epoch_milliseconds (fundingTime keyed)"
        assert ev.interval_param is None
        assert ev.instruments == ("BTC-USDT-SWAP",)

    def test_trade_grant_mechanics(self) -> None:
        ev = okx_native_evidence()[TRADE]
        assert ev.historical_mode is HistoricalMode.REST_CURSOR
        assert ev.pagination_mode is PaginationMode.CURSOR
        assert ev.endpoint_family == "okx-swap-history-trades"
        assert ev.start_param == "after"
        assert ev.start_unit == "trade-id based cursor (provider tradeId)"
        assert ev.end_param == "before"
        assert ev.end_unit == "trade-id based cursor (provider tradeId)"
        assert ev.interval_param is None
        assert ev.instruments == ("BTC-USDT-SWAP",)

    def test_grants_resolve_to_i14_and_never_broaden(self) -> None:
        promoted = capabilities_from_promotion(PROVIDER_ID, load_promotion_candidates())
        evidence = okx_native_evidence()
        for sensor in (FUNDING, TRADE):
            vio = native_evidence_violations(
                PROVIDER_ID, evidence[sensor], promoted.capability_for(sensor)
            )
            assert vio == [], f"{sensor}: {vio}"
            for eid in evidence[sensor].evidence_ids:
                assert eid in promoted.capability_for(sensor).evidence_basis

    def test_endpoint_family_mapping(self) -> None:
        assert okx_endpoint_family(BOOK) == "okx-swap-market-books"
        assert okx_endpoint_family(FUNDING) == "okx-swap-funding-rate-history"
        assert okx_endpoint_family(TRADE) == "okx-swap-history-trades"

    def test_book_capability_stays_current_only(self) -> None:
        # A CURRENT_ONLY surface can never be given a historical acquisition
        # mode (native_evidence_violations would reject a grant).
        caps = build_okx_capabilities()
        cap = caps.capability_for(BOOK)
        assert cap.supported is True
        assert cap.history_scope.value == "CURRENT_ONLY"
        assert cap.historical_mode is None