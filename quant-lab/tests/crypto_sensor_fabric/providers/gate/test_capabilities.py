"""SENSOR-B3-I06 — Gate Futures capability + native acquisition-mode freeze.

Proves the I14-bounded Gate production set, SECONDARY roles, evidence-derived
production symbol scope (BTC_USDT only; probe ETH/SOL/DOGE excluded), native
acquisition-mode evidence, and exact-set equality against
`source_promotion_candidates.yaml`.
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
from crypto_sensor_fabric.providers.gate import (
    GATE_PRODUCTION_INSTRUMENT_SCOPE,
    GATE_PROBE_INSTRUMENT_SCOPE,
    GATE_PROMOTED_SENSORS,
    GATE_SYMBOL_SCOPES,
    PROVIDER_ID,
    build_gate_capabilities,
    gate_endpoint_family,
    gate_native_evidence,
)
from crypto_sensor_fabric.providers.gate.capabilities import _PROMOTED_ORDER

ALL_PROMOTED = _PROMOTED_ORDER


class TestProviderIdentity:
    def test_provider_id_frozen(self) -> None:
        assert PROVIDER_ID == "GATE_FUTURES"
        caps = build_gate_capabilities()
        assert caps.provider_id == "GATE_FUTURES"


class TestExactPromotedSet:
    def test_exactly_four_promoted_sensors(self) -> None:
        caps = build_gate_capabilities()
        supported = set(caps.supported_sensors())
        assert len(supported) == 4
        assert supported == set(ALL_PROMOTED)
        assert supported == set(GATE_PROMOTED_SENSORS)

    def test_exact_i14_equality(self) -> None:
        """Declared Gate production set == I14 Gate promotion set (no 5th path)."""
        promoted = capabilities_from_promotion(PROVIDER_ID, load_promotion_candidates())
        i14_gate = {s for s, c in promoted.sensors.items() if c.supported}
        assert i14_gate == set(ALL_PROMOTED)
        declared = set(build_gate_capabilities().supported_sensors())
        assert declared == i14_gate
        # at least the four expected members are present
        assert SensorFamily.MECHANICAL_FUNDING in declared
        assert SensorFamily.MECHANICAL_LIQUIDATION in declared
        assert SensorFamily.MECHANICAL_OPEN_INTEREST in declared
        assert SensorFamily.MECHANICAL_POSITIONING in declared

    def test_trade_and_book_snapshot_not_promoted(self) -> None:
        caps = build_gate_capabilities()
        assert caps.capability_for(SensorFamily.MECHANICAL_TRADE).supported is False
        assert (
            caps.capability_for(SensorFamily.MECHANICAL_BOOK_SNAPSHOT).supported is False
        )


class TestRolesStaySecondary:
    def test_all_four_paths_are_secondary(self) -> None:
        from crypto_sensor_fabric.probes.enums import ProviderRole

        caps = build_gate_capabilities()
        assert caps.supported_sensors()
        for sensor in caps.supported_sensors():
            cap = caps.capability_for(sensor)
            assert cap.allowed_role is ProviderRole.SECONDARY, sensor
            assert cap.probe_evidence_ref is not None, sensor


class TestProductionSymbolScope:
    def test_production_scope_derives_from_evidence(self) -> None:
        # 08_HISTORY_BOUNDARIES.csv evidences BTC_USDT for all four promoted
        # Gate paths; the production union is exactly BTC_USDT.
        assert GATE_PRODUCTION_INSTRUMENT_SCOPE == ["BTC_USDT"]

    def test_probe_scope_keeps_probe_universe(self) -> None:
        assert GATE_PROBE_INSTRUMENT_SCOPE == [
            "BTC_USDT",
            "ETH_USDT",
            "SOL_USDT",
            "DOGE_USDT",
        ]

    def test_sensor_specific_symbol_scopes(self) -> None:
        for sensor in ALL_PROMOTED:
            assert GATE_SYMBOL_SCOPES[sensor] == ("BTC_USDT",), sensor

    def test_capability_symbol_scope_per_sensor(self) -> None:
        caps = build_gate_capabilities()
        for sensor in ALL_PROMOTED:
            cap = caps.capability_for(sensor)
            assert cap.symbol_scope == ["BTC_USDT"], sensor

    def test_probe_only_symbols_never_in_production_capability(self) -> None:
        caps = build_gate_capabilities()
        for sensor in ALL_PROMOTED:
            assert "ETH_USDT" not in caps.capability_for(sensor).symbol_scope
            assert "SOL_USDT" not in caps.capability_for(sensor).symbol_scope
            assert "DOGE_USDT" not in caps.capability_for(sensor).symbol_scope


class TestNativeEvidence:
    def test_every_promoted_sensor_has_a_grant(self) -> None:
        evidence = gate_native_evidence()
        assert set(evidence.keys()) == set(ALL_PROMOTED)
        for sensor in ALL_PROMOTED:
            assert isinstance(evidence[sensor], ProviderNativeCapabilityEvidence)

    def test_funding_grant_mechanics(self) -> None:
        sensor = ALL_PROMOTED[0]  # FUNDING
        ev = gate_native_evidence()[sensor]
        assert ev.historical_mode is HistoricalMode.REST_RANGE
        assert ev.pagination_mode is PaginationMode.TIME_RANGE
        assert ev.endpoint_family == "gate-futures-funding_rate"
        assert ev.start_param == "from"
        assert ev.start_unit == "epoch_seconds"
        assert ev.end_param == "to"
        assert ev.end_unit == "epoch_seconds"
        assert ev.interval_param is None
        assert ev.instruments == ("BTC_USDT",)

    def test_contract_stats_grants_mechanics(self) -> None:
        for sensor in ALL_PROMOTED[1:]:  # Liquidations / OI / Positioning
            ev = gate_native_evidence()[sensor]
            assert ev.historical_mode is HistoricalMode.REST_RANGE
            assert ev.pagination_mode is PaginationMode.TIME_RANGE
            assert ev.endpoint_family == "gate-futures-contract_stats"
            assert ev.start_param == "from"
            assert ev.start_unit == "epoch_seconds"
            assert ev.end_param == "none"  # NO invented `to`
            assert ev.end_unit == "n/a (no `to`; from/interval/limit bounded window)"
            assert ev.interval_param == "interval"
            assert ev.resume_mechanic == (
                "unresolved; single-request window (no invented from+interval "
                "advancement)"
            )
            assert ev.instruments == ("BTC_USDT",)

    def test_grants_resolve_to_i14_and_never_broaden(self) -> None:
        promoted = capabilities_from_promotion(PROVIDER_ID, load_promotion_candidates())
        evidence = gate_native_evidence()
        for sensor in ALL_PROMOTED:
            vio = native_evidence_violations(
                PROVIDER_ID, evidence[sensor], promoted.capability_for(sensor)
            )
            assert vio == [], f"{sensor}: {vio}"
            for eid in evidence[sensor].evidence_ids:
                assert eid in promoted.capability_for(sensor).evidence_basis

    def test_endpoint_family_mapping(self) -> None:
        assert gate_endpoint_family(SensorFamily.MECHANICAL_FUNDING) == "gate-futures-funding_rate"
        for sensor in ALL_PROMOTED[1:]:
            assert gate_endpoint_family(sensor) == "gate-futures-contract_stats"