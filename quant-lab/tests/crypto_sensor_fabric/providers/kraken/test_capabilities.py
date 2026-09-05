"""SENSOR-B3-I05 — Kraken capability + native acquisition-mode freeze.

Proves the I14-bound exact promoted set (six paths), the typed unsupported
surfaces (TRADE / BOOK_SNAPSHOT), native REST_RANGE/TIME_RANGE refinement, and
role / PIT / methodology / verified-history bounds retained.
"""

from __future__ import annotations

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.probes.enums import (
    PITReadiness,
    ProviderRole,
    RedundancyClass,
)
from crypto_sensor_fabric.providers.base.enums import (
    HistoryScope,
    HistoricalMode,
    PaginationMode,
)
from crypto_sensor_fabric.providers.kraken import (
    KRAKEN_PRODUCTION_INSTRUMENT_SCOPE,
    KRAKEN_PROMOTED_SENSORS,
    KRAKEN_PROBE_INSTRUMENT_SCOPE,
    KRAKEN_SYMBOL_SCOPES,
    PROVIDER_ID,
    build_kraken_capabilities,
    kraken_native_evidence,
)

PROMOTED = {
    SensorFamily.MECHANICAL_BASIS,
    SensorFamily.MECHANICAL_BOOK_METRIC,
    SensorFamily.MECHANICAL_FUNDING,
    SensorFamily.MECHANICAL_LIQUIDATION,
    SensorFamily.MECHANICAL_OPEN_INTEREST,
    SensorFamily.MECHANICAL_POSITIONING,
}


def _caps():
    return build_kraken_capabilities()


class TestExactPromotedSet:
    def test_provider_id_frozen(self) -> None:
        assert PROVIDER_ID == "KRAKEN_FUTURES"
        assert _caps().provider_id == "KRAKEN_FUTURES"

    def test_exactly_six_promoted_sensors(self) -> None:
        assert KRAKEN_PROMOTED_SENSORS == PROMOTED
        assert set(_caps().supported_sensors()) == PROMOTED
        assert len(_caps().supported_sensors()) == 6

    def test_trade_unsupported(self) -> None:
        cap = _caps().capability_for(SensorFamily.MECHANICAL_TRADE)
        assert cap.supported is False
        assert cap.historical_mode is None
        assert cap.live_mode.value == "NONE"

    def test_book_snapshot_unsupported(self) -> None:
        cap = _caps().capability_for(SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
        assert cap.supported is False
        assert cap.historical_mode is None

    def test_seventh_path_not_silently_promoted(self) -> None:
        assert len(_caps().supported_sensors()) == len(PROMOTED) == 6

    def test_native_evidence_covers_only_promoted(self) -> None:
        evidence = kraken_native_evidence()
        assert set(evidence) == PROMOTED

    def test_declared_set_equals_i14_promotion_set_exactly(self) -> None:
        # PROMOTED-SET COMPLETENESS: the declared production set must equal the
        # I14 promotion set derived from source_promotion_candidates.yaml — no
        # silent omission, no seventh path.
        from crypto_sensor_fabric.providers.base import load_promotion_candidates

        cands = load_promotion_candidates()
        i14_kraken = {
            SensorFamily(str(c["sensor"]))
            for c in cands
            if c.get("provider") == "KRAKEN_FUTURES"
        }
        assert i14_kraken == PROMOTED
        assert set(_caps().supported_sensors()) == i14_kraken
        assert len(i14_kraken) == 6
        # no Kraken promotion path may silently disappear (all six are
        # implemented; none is evidence-blocked at I05)
        for sensor in i14_kraken:
            assert _caps().capability_for(sensor).supported
            assert _caps().capability_for(sensor).probe_evidence_ref is not None


class TestNativeModeRefinement:
    def test_each_promoted_has_exact_native_mode(self) -> None:
        caps = _caps()
        for sensor in PROMOTED:
            cap = caps.capability_for(sensor)
            assert cap.historical_mode is HistoricalMode.REST_RANGE
            assert cap.pagination_mode is PaginationMode.TIME_RANGE
            assert cap.history_scope is HistoryScope.HISTORICAL
            assert cap.access_mode == "PUBLIC_REST"
            assert cap.live_mode.value == "NONE"
            assert cap.archive_mode is False

    def test_funding_secondary_kept(self) -> None:
        funding = _caps().capability_for(SensorFamily.MECHANICAL_FUNDING)
        assert funding.allowed_role is ProviderRole.SECONDARY
        assert funding.redundancy_class is RedundancyClass.R3_THREE_PLUS_INDEPENDENT
        assert funding.pit_requirement is PITReadiness.PIT_READY_WITH_METHOD_VERSION

    def test_liquidation_primary_with_microscope_distinction(self) -> None:
        liq = _caps().capability_for(SensorFamily.MECHANICAL_LIQUIDATION)
        assert liq.allowed_role is ProviderRole.PRIMARY
        assert liq.methodology_pin == "kraken-market-analytics-liquidation-volume"

    def test_methodology_pins_frozen(self) -> None:
        caps = _caps()
        assert caps.capability_for(SensorFamily.MECHANICAL_OPEN_INTEREST).methodology_pin == "kraken_futures-open_interest"
        assert caps.capability_for(SensorFamily.MECHANICAL_FUNDING).methodology_pin == "kraken_futures-funding"
        assert caps.capability_for(SensorFamily.MECHANICAL_BASIS).methodology_pin == "kraken_futures-basis"
        assert caps.capability_for(SensorFamily.MECHANICAL_POSITIONING).methodology_pin == "kraken_futures-positioning"
        assert caps.capability_for(SensorFamily.MECHANICAL_BOOK_METRIC).methodology_pin == "kraken_futures-book_metric"

    def test_verified_history_bounds_retained(self) -> None:
        caps = _caps()
        assert caps.capability_for(SensorFamily.MECHANICAL_BASIS).verified_history_start is not None
        assert caps.capability_for(SensorFamily.MECHANICAL_LIQUIDATION).verified_history_start is not None

    def test_evidence_refs_resolve_to_i14(self) -> None:
        caps = _caps()
        cands = caps.supported_sensors()
        for sensor in cands:
            ref = caps.capability_for(sensor).probe_evidence_ref
            assert ref is not None
            assert ref.provider_id == "KRAKEN_FUTURES"
            assert ref.sensor_family is sensor
            assert ref.evidence_id in caps.capability_for(sensor).evidence_basis

    def test_production_scope_separated_from_probe_scope(self) -> None:
        # SENSOR-B3-I05R1: PI_SOLUSD / PI_DOGEUSD are probe/control targets
        # only — never production support.
        assert KRAKEN_PRODUCTION_INSTRUMENT_SCOPE == ["PI_XBTUSD", "PI_ETHUSD"]
        assert set(KRAKEN_PROBE_INSTRUMENT_SCOPE) >= {
            "PI_XBTUSD",
            "PI_ETHUSD",
            "PI_SOLUSD",
            "PI_DOGEUSD",
        }
        assert "PI_SOLUSD" not in KRAKEN_PRODUCTION_INSTRUMENT_SCOPE
        assert "PI_DOGEUSD" not in KRAKEN_PRODUCTION_INSTRUMENT_SCOPE

    def test_sensor_specific_symbol_scope_on_capabilities(self) -> None:
        # OI is evidence-backed for PI_XBTUSD + PI_ETHUSD; the other five are
        # evidence-backed on PI_XBTUSD only (08_HISTORY_BOUNDARIES.csv).
        caps = _caps()
        for sensor in PROMOTED:
            scope = caps.capability_for(sensor).symbol_scope
            if sensor is SensorFamily.MECHANICAL_OPEN_INTEREST:
                assert set(scope) == {"PI_XBTUSD", "PI_ETHUSD"}
            else:
                assert scope == ["PI_XBTUSD"]
        assert set(KRAKEN_SYMBOL_SCOPES) == PROMOTED

    def test_native_evidence_grant_proves_instruments(self) -> None:
        evidence = kraken_native_evidence()
        for sensor in PROMOTED:
            grant = evidence[sensor]
            assert grant.instruments
            assert set(grant.instruments) == set(
                _caps().capability_for(sensor).symbol_scope
            )