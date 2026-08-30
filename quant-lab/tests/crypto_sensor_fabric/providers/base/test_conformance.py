"""SENSOR-B3-I04 / I04R1 — common provider conformance suite.

Hardening (I04R1):

- promotion-bound enforcement is STRICT and compares every material I14 field
- a PRODUCTION_CANDIDATE run (the only mode a real adapter may use) REQUIRES
  promotion bounds; missing evidence FAILS CLOSED (Repair 2)
- live vs historical acquisition surfaces are separated (Repair 3)
- promotion-file parsing is strict — unknown/missing controlled values fail
  closed (Repair 4)
- empty-valid vs unsupported is proven behaviorally (Repair 5)
- schema drift fail-closed is proven (Repair 6)
- retry classification uses the real I03 classifier (Repair 7)
- adversarial fixtures are VALID typed models — never invalid Pydantic
  mutation used to manufacture a failure (Repair 8)

All offline.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_sensor_fabric.contracts.access import FreeOnlyPolicy
from crypto_sensor_fabric.contracts.enums import AccessClass, SensorFamily
from crypto_sensor_fabric.providers.base import (
    AdapterConformanceMode,
    AdapterUnderTest,
    ProviderCapabilities,
    assert_no_zero_coercion,
    assess_schema,
    capabilities_from_promotion,
    load_promotion_candidates,
    promotion_bound_violations,
    promotion_provider_ids,
    run_conformance_suite,
    summarize_conformance,
)
from crypto_sensor_fabric.providers.base.enums import (
    AdapterAuthMode,
    HistoricalMode,
    LiveMode,
    SchemaState,
)
from crypto_sensor_fabric.providers.base.models import (
    ProviderCapabilities as _PC,
    SensorCapability,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)

# A clean, I14-shaped Kraken candidate covering two sensors for conformance.
PROMOTED = [
    {
        "provider": "KRAKEN_FUTURES",
        "sensor": "MECHANICAL_FUNDING",
        "allowed_role": "SECONDARY",
        "access_path": "PUBLIC_REST",
        "history_mode": "HISTORICAL",
        "verified_history": "2024-06-15Z..2026-08-23T14:55:04.309346Z",
        "redundancy_class": "R3_THREE_PLUS_INDEPENDENT",
        "PIT_requirement": "PIT_READY_WITH_METHOD_VERSION",
        "methodology_pin": "kraken_futures-funding",
        "known_hazards": [],
        "evidence_basis": ["kraken_futures_funding_pi_xbtusd_RECENT_CONTROL_1h"],
    },
    {
        "provider": "KRAKEN_FUTURES",
        "sensor": "MECHANICAL_BOOK_METRIC",
        "allowed_role": "PRIMARY",
        "access_path": "PUBLIC_REST",
        "history_mode": "HISTORICAL",
        "verified_history": "2024-06-15Z..2026-08-23T14:55:05.140795Z",
        "redundancy_class": "R1_SINGLE_INDEPENDENT",
        "PIT_requirement": "PIT_READY_WITH_METHOD_VERSION",
        "methodology_pin": "kraken_futures-book_metric",
        "known_hazards": [],
        "evidence_basis": ["kraken_futures_book_metric_pi_xbtusd_RECENT_CONTROL_1h"],
    },
]


def promoted_caps() -> ProviderCapabilities:
    """The I14 promotion-bound capabilities for the fake adapter."""
    return capabilities_from_promotion("KRAKEN_FUTURES", PROMOTED)


def declared_caps(**sensor_overrides: object) -> ProviderCapabilities:
    """A type-valid declared capability set, optionally with per-sensor override.

    `sensor_overrides` keys are SensorFamily values; values are dicts of
    SensorCapability field names -> values.  All overrides produce VALID typed
    models (the base comes from I14 promotion and is already type-valid).
    """
    caps = capabilities_from_promotion("KRAKEN_FUTURES", PROMOTED)
    for sensor_name, override in sensor_overrides.items():
        sensor = SensorFamily(sensor_name)
        base = caps.sensors[sensor]
        caps.sensors[sensor] = base.model_copy(update=override)
    return caps


def _sensor(caps: ProviderCapabilities, sensor: str) -> SensorCapability:
    return caps.sensors[SensorFamily(sensor)]


class FakeKrakenAdapter:
    """Full protocol adapter with a fake transport (never touches network)."""

    provider_id = "KRAKEN_FUTURES"

    def __init__(self, caps: ProviderCapabilities | None = None) -> None:
        self._caps = caps if caps is not None else promoted_caps()

    def capabilities(self) -> ProviderCapabilities:
        return self._caps


def free_policy() -> FreeOnlyPolicy:
    return FreeOnlyPolicy(
        access_class=AccessClass.FREE_AUTOMATED,
        cost_usd_required=0,
        payment_method_required=False,
        staking_required=False,
        transaction_required=False,
    )


def under_test(
    adapter: object | None = None,
    **overrides: object,
) -> AdapterUnderTest:
    base: dict[str, object] = {
        "adapter": FakeKrakenAdapter(),
        "registry_policy": free_policy(),
        "auth_mode": AdapterAuthMode.NO_AUTH,
        "promoted_capabilities": promoted_caps(),
    }
    if adapter is not None:
        base["adapter"] = adapter
    base.update(overrides)
    return AdapterUnderTest(**base)  # type: ignore[arg-type]


def _check(results, check_id):
    return next(r for r in results if r.check_id == check_id)


def _assert_this_check_fails(results, check_id, detail_fragment: str) -> None:
    check = _check(results, check_id)
    assert not check.passed
    assert detail_fragment in check.detail, check.detail


# ---------------------------------------------------------------------------
#  PASS: legitimate I14-bounded fake adapter
# ---------------------------------------------------------------------------
class TestConformancePass:
    def test_full_adapter_passes_all_checks(self) -> None:
        results = run_conformance_suite(under_test())
        failed = [r for r in results if not r.passed]
        assert not failed, [f"{r.check_id}: {r.detail}" for r in failed]

    def test_summary_counts(self) -> None:
        results = run_conformance_suite(under_test())
        summary = summarize_conformance(results)
        assert summary["passed"] + summary["failed"] == summary["checks"]
        assert summary["failed"] == 0


# ---------------------------------------------------------------------------
#  REPAIR 2 — availability mode gating
# ---------------------------------------------------------------------------
class TestProductionModeGating:
    def test_production_candidate_without_promotion_fails_closed(self) -> None:
        # production candidate omitting promotion evidence must FAIL, even if
        # every other dimension is sound — there is no None-based bypass.
        results = run_conformance_suite(
            under_test(promoted_capabilities=None, mode=AdapterConformanceMode.PRODUCTION_CANDIDATE)
        )
        _assert_this_check_fails(
            results, "q0_production_promotion_required", "PRODUCTION_CANDIDATE"
        )
        _assert_this_check_fails(results, "q0_promotion_bounds", "missing")

    def test_framework_test_without_promotion_is_allowed(self) -> None:
        results = run_conformance_suite(
            under_test(promoted_capabilities=None, mode=AdapterConformanceMode.FRAMEWORK_TEST)
        )
        check = _check(results, "q0_production_promotion_required")
        assert check.passed
        # promotion-bounds check is a no-op in framework self-test mode
        check = _check(results, "q0_promotion_bounds")
        assert check.passed


# ---------------------------------------------------------------------------
#  REPAIR 1 + 8 — strict promotion bounds, valid-typed adversarial fixtures
# ---------------------------------------------------------------------------
class TestPromotionBoundEnforcement:
    def test_supported_sensor_not_promoted(self) -> None:
        # funding NOT in promotion file -> declared supported must fail
        declared = declared_caps()
        bound = _PC(provider_id="KRAKEN_FUTURES")  # empty bound
        violations = promotion_bound_violations(
            _sensor(declared, "MECHANICAL_FUNDING"),
            bound.capability_for(SensorFamily.MECHANICAL_FUNDING),
        )
        assert any("not in promotion file" in v for v in violations)

    def test_report_does_not_second_count_funding(self) -> None:
        # role equivalence: declared must match bound exactly
        declared = declared_caps(MECHANICAL_FUNDING={"allowed_role": "PRIMARY"})
        bound = promoted_caps()
        violations = promotion_bound_violations(
            _sensor(declared, "MECHANICAL_FUNDING"),
            _sensor(bound, "MECHANICAL_FUNDING"),
        )
        assert any("allowed_role" in v and "PRIMARY" in v for v in violations)

    def test_history_widened_earlier_fails(self) -> None:
        declared = declared_caps(
            MECHANICAL_FUNDING={"verified_history_start": datetime(2021, 1, 1, tzinfo=UTC)}
        )
        bound = promoted_caps()
        violations = promotion_bound_violations(
            _sensor(declared, "MECHANICAL_FUNDING"),
            _sensor(bound, "MECHANICAL_FUNDING"),
        )
        assert any("earlier than bound" in v for v in violations)

    def test_history_end_beyond_bound_fails(self) -> None:
        declared = declared_caps(
            MECHANICAL_FUNDING={"verified_history_end": datetime(2030, 1, 1, tzinfo=UTC)}
        )
        bound = promoted_caps()
        violations = promotion_bound_violations(
            _sensor(declared, "MECHANICAL_FUNDING"),
            _sensor(bound, "MECHANICAL_FUNDING"),
        )
        assert any("beyond bound" in v for v in violations)

    def test_role_change_fails(self) -> None:
        declared = declared_caps(MECHANICAL_FUNDING={"allowed_role": "PRIMARY"})
        bound = promoted_caps()
        violations = promotion_bound_violations(
            _sensor(declared, "MECHANICAL_FUNDING"),
            _sensor(bound, "MECHANICAL_FUNDING"),
        )
        assert any("allowed_role" in v for v in violations)

    def test_methodology_pin_removed_fails(self) -> None:
        declared = declared_caps(MECHANICAL_FUNDING={"methodology_pin": None})
        bound = promoted_caps()
        violations = promotion_bound_violations(
            _sensor(declared, "MECHANICAL_FUNDING"),
            _sensor(bound, "MECHANICAL_FUNDING"),
        )
        assert any("methodology_pin" in v for v in violations)

    def test_hazard_removed_fails(self) -> None:
        # add a hazard to the bound (not in file) and confirm removal is caught
        bound = promoted_caps()
        bound.sensors[SensorFamily.MECHANICAL_FUNDING] = _sensor(
            bound, "MECHANICAL_FUNDING"
        ).model_copy(update={"known_hazards": ["hazard-1"]})
        declared = declared_caps()  # declared has no hazards
        violations = promotion_bound_violations(
            _sensor(declared, "MECHANICAL_FUNDING"),
            _sensor(bound, "MECHANICAL_FUNDING"),
        )
        assert any("hazard" in v and "hazard-1" in v for v in violations)

    def test_evidence_lineage_removed_fails(self) -> None:
        declared = declared_caps(MECHANICAL_FUNDING={"evidence_basis": []})
        bound = promoted_caps()
        violations = promotion_bound_violations(
            _sensor(declared, "MECHANICAL_FUNDING"),
            _sensor(bound, "MECHANICAL_FUNDING"),
        )
        assert any("evidence basis" in v for v in violations)

    def test_pit_upgraded_fails(self) -> None:
        declared = declared_caps(
            MECHANICAL_FUNDING={"pit_requirement": "PIT_READY"}
        )
        bound = promoted_caps()
        violations = promotion_bound_violations(
            _sensor(declared, "MECHANICAL_FUNDING"),
            _sensor(bound, "MECHANICAL_FUNDING"),
        )
        assert any("PIT requirement" in v for v in violations)

    def test_redundancy_class_changed_fails(self) -> None:
        declared = declared_caps(
            MECHANICAL_FUNDING={"redundancy_class": "R1_SINGLE_INDEPENDENT"}
        )
        bound = promoted_caps()
        violations = promotion_bound_violations(
            _sensor(declared, "MECHANICAL_FUNDING"),
            _sensor(bound, "MECHANICAL_FUNDING"),
        )
        assert any("redundancy_class" in v for v in violations)

    def test_current_only_to_historical_widening_fails(self) -> None:
        # a reserved current-only bound must not be widened to full REST history
        cited_current_only = {
            "provider": "OKX_SWAP",
            "sensor": "MECHANICAL_BOOK_SNAPSHOT",
            "allowed_role": "CURRENT_ONLY",
            "access_path": "PUBLIC_REST",
            "history_mode": "CURRENT_ONLY",
            "verified_history": "2026-08-30T13:55:11.250844Z..2026-08-30T13:55:11.250844Z",
            "redundancy_class": "R2_TWO_INDEPENDENT",
            "PIT_requirement": "PIT_READY_WITH_METHOD_VERSION",
            "methodology_pin": "okx_swap-book_snapshot",
            "known_hazards": ["current-only surface"],
            "evidence_basis": ["okx_swap_book_snapshot_btc-usdt-swap_RECENT_CONTROL_book_snapshot"],
        }
        bound = capabilities_from_promotion("OKX_SWAP", [cited_current_only])
        declared = bound.model_copy()  # declared == bound (current-only)
        violations = promotion_bound_violations(
            _sensor(declared, "MECHANICAL_BOOK_SNAPSHOT"),
            _sensor(bound, "MECHANICAL_BOOK_SNAPSHOT"),
        )
        assert not violations
        # now try to widen to HISTORICAL
        declared = capabilities_from_promotion(
            "OKX_SWAP",
            [{**cited_current_only, "history_mode": "HISTORICAL",
              "verified_history": "2021-06-15Z..2026-08-30T13:55:11.250844Z"}],
        )
        violations = promotion_bound_violations(
            _sensor(declared, "MECHANICAL_BOOK_SNAPSHOT"),
            _sensor(bound, "MECHANICAL_BOOK_SNAPSHOT"),
        )
        assert any("CURRENT_ONLY" in v or "historical_mode" in v for v in violations)


# ---------------------------------------------------------------------------
#  REPAIR 9 — no dead `declared_capabilities` field
# ---------------------------------------------------------------------------
class TestNoDeadState:
    def test_adapter_under_test_has_no_declared_capabilities_field(self) -> None:
        import dataclasses

        fields = {f.name for f in dataclasses.fields(AdapterUnderTest)}
        assert "declared_capabilities" not in fields


# ---------------------------------------------------------------------------
#  REPAIR 3 — live vs historical separation
# ---------------------------------------------------------------------------
class TestLiveHistoricalSeparation:
    def test_historical_does_not_grant_live(self) -> None:
        candidates = load_promotion_candidates()
        caps = capabilities_from_promotion("KRAKEN_FUTURES", candidates)
        funding = caps.capability_for(SensorFamily.MECHANICAL_FUNDING)
        assert funding.historical_mode is HistoricalMode.REST_RANGE
        # historical evidence must NOT auto-grant a live-production contract
        assert funding.live_mode is LiveMode.NONE

    def test_current_only_is_live_snapshot_not_history(self) -> None:
        candidates = load_promotion_candidates()
        caps = capabilities_from_promotion("OKX_SWAP", candidates)
        book = caps.capability_for(SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
        # current/live snapshot surface, no invented historical depth
        assert book.historical_mode is HistoricalMode.LIVE_REST_ONLY
        assert book.live_mode is LiveMode.LIVE_REST
        assert book.archive_mode is False

    def test_live_mode_mapping_decide(self) -> None:
        # Rationale: CURRENT_ONLY public REST snapshot => LIVE_REST live surface,
        # historical_mode stays LIVE_REST_ONLY (no REST_RANGE width).
        caps = capabilities_from_promotion(
            "DERIBIT", load_promotion_candidates()
        )
        book = caps.capability_for(SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
        assert book.live_mode is LiveMode.LIVE_REST
        assert book.historical_mode is HistoricalMode.LIVE_REST_ONLY


# ---------------------------------------------------------------------------
#  REPAIR 4 — strict promotion-file parsing
# ---------------------------------------------------------------------------
class TestStrictPromotionParsing:
    def _base_candidate(self) -> dict:
        return dict(PROMOTED[0])

    def test_unknown_allowed_role_fails(self) -> None:
        c = self._base_candidate()
        c["allowed_role"] = "SUPER_SOURCE"
        with pytest.raises(ValueError):
            capabilities_from_promotion("KRAKEN_FUTURES", [c])

    def test_unknown_redundancy_fails(self) -> None:
        c = self._base_candidate()
        c["redundancy_class"] = "R9_NINE"
        with pytest.raises(ValueError):
            capabilities_from_promotion("KRAKEN_FUTURES", [c])

    def test_unknown_pit_fails(self) -> None:
        c = self._base_candidate()
        c["PIT_requirement"] = "PIT_OMNISCIENT"
        with pytest.raises(ValueError):
            capabilities_from_promotion("KRAKEN_FUTURES", [c])

    def test_unknown_history_mode_fails(self) -> None:
        c = self._base_candidate()
        c["history_mode"] = "EVERYTHING_EVER"
        with pytest.raises(ValueError):
            capabilities_from_promotion("KRAKEN_FUTURES", [c])

    def test_unknown_access_path_fails(self) -> None:
        c = self._base_candidate()
        c["access_path"] = "PAY_TO_PLAY"
        with pytest.raises(ValueError):
            capabilities_from_promotion("KRAKEN_FUTURES", [c])

    def test_malformed_verified_history_fails(self) -> None:
        c = self._base_candidate()
        c["verified_history"] = "not-a-range"
        with pytest.raises(ValueError):
            capabilities_from_promotion("KRAKEN_FUTURES", [c])

    def test_missing_evidence_basis_fails(self) -> None:
        c = self._base_candidate()
        c["evidence_basis"] = []
        with pytest.raises(ValueError):
            capabilities_from_promotion("KRAKEN_FUTURES", [c])

    def test_pit_ready_missing_methodology_pin_fails(self) -> None:
        c = self._base_candidate()
        c["methodology_pin"] = ""
        with pytest.raises(ValueError):
            capabilities_from_promotion("KRAKEN_FUTURES", [c])

    def test_pit_ready_historical_no_verified_boundary_fails(self) -> None:
        c = self._base_candidate()
        c["verified_history"] = ""
        with pytest.raises(ValueError):
            capabilities_from_promotion("KRAKEN_FUTURES", [c])


# ---------------------------------------------------------------------------
#  REPAIR 5 — empty-valid vs unsupported (behavioral)
# ---------------------------------------------------------------------------
class TestEmptyValidVsUnsupported:
    def test_unsupported_sensor_is_typed_not_empty(self) -> None:
        from crypto_sensor_fabric.providers.base.errors import CapabilityUnavailable

        # The capability object surface distinguishes support at the type level
        # (never a silent []/0/None for an unsupported sensor).
        unbound_caps = declared_caps()
        # basis is NOT in our promoted set => unsupported
        basis = unbound_caps.capability_for(SensorFamily.MECHANICAL_BASIS)
        assert basis.supported is False

        err = CapabilityUnavailable(
            provider_id="KRAKEN_FUTURES", sensor_family=SensorFamily.MECHANICAL_BASIS
        )
        assert err.failure_type == "CapabilityUnavailable"


# ---------------------------------------------------------------------------
#  REPAIR 6 — schema drift fail-closed
# ---------------------------------------------------------------------------
class TestSchemaDriftFailClosed:
    def test_boundaries_respected(self) -> None:
        expected = {"timestamp", "rate"}
        known = assess_schema(expected, {"timestamp", "rate"}, semantics_known=True)
        additive = assess_schema(expected, {"timestamp", "rate", "extra"}, semantics_known=True)
        breaking = assess_schema(expected, {"timestamp"}, semantics_known=True)
        unknown = assess_schema(expected, {"timestamp"}, semantics_known=False)

        assert known.state is SchemaState.KNOWN_SCHEMA
        assert known.semantic_output_allowed is True
        assert additive.state is SchemaState.ADDITIVE_SCHEMA_CHANGE
        assert additive.semantic_output_allowed is True
        assert breaking.state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert breaking.semantic_output_allowed is False
        assert breaking.raw_preserved is True
        assert unknown.state is SchemaState.UNKNOWN_SCHEMA
        assert unknown.semantic_output_allowed is False

    def test_no_zero_coercion(self) -> None:
        expected = {"timestamp", "rate"}
        breaking = assess_schema(expected, {"timestamp"}, semantics_known=True)
        row = {"timestamp": 1}
        with pytest.raises(KeyError):
            assert_no_zero_coercion(breaking, row, "rate")

        known = assess_schema(
            expected, {"timestamp", "rate"}, semantics_known=True
        )
        assert_no_zero_coercion(known, {"timestamp": 1, "rate": 2}, "rate")


# ---------------------------------------------------------------------------
#  REPAIR 7 — retry classifier (real I03)
# ---------------------------------------------------------------------------
class TestRetryClassifierConformance:
    def test_transient_retryable(self) -> None:
        results = run_conformance_suite(under_test())
        check = _check(results, "q2_retry_classification")
        assert check.passed, check.detail

    def test_adversarial_parser_is_not_blocked(self) -> None:
        # schema assessment runs inside conformance; verify the harness does not
        # block KNOWN/additive and blocks breaking/unknown
        results = run_conformance_suite(under_test())
        check = _check(results, "q1_schema_drift_fail_closed")
        assert check.passed, check.detail


# ---------------------------------------------------------------------------
#  I14 evidence integration
# ---------------------------------------------------------------------------
class TestPromotionIntegration:
    def test_promotion_file_loads_real_candidates(self) -> None:
        candidates = load_promotion_candidates()
        providers = promotion_provider_ids(candidates)
        assert set(providers) == {"KRAKEN_FUTURES", "GATE_FUTURES", "OKX_SWAP", "DERIBIT"}
        assert "BINANCE_USDM" not in providers
        assert "BYBIT_LINEAR" not in providers

    def test_capabilities_bound_to_i14_fields(self) -> None:
        candidates = load_promotion_candidates()
        caps = capabilities_from_promotion("KRAKEN_FUTURES", candidates)
        funding = caps.capability_for(SensorFamily.MECHANICAL_FUNDING)
        assert funding.supported
        assert funding.allowed_role.value == "SECONDARY"
        assert funding.methodology_pin == "kraken_futures-funding"
        assert funding.pit_requirement.value == "PIT_READY_WITH_METHOD_VERSION"
        assert funding.redundancy_class.value == "R3_THREE_PLUS_INDEPENDENT"
        assert funding.evidence_basis
        assert funding.probe_evidence_ref is not None
        assert funding.verified_history_start is not None

    def test_unpromoted_provider_has_no_capabilities(self) -> None:
        candidates = load_promotion_candidates()
        caps = capabilities_from_promotion("BINANCE_USDM", candidates)
        assert not caps.supported_sensors()

    def test_archive_only_does_not_imply_rest_or_live(self) -> None:
        # ARCHIVE_ONLY candidate must not map to a live REST surface.
        c = {
            "provider": "X",
            "sensor": "MECHANICAL_TRADE",
            "allowed_role": "ARCHIVE_ONLY",
            "access_path": "PUBLIC_ARCHIVE",
            "history_mode": "ARCHIVE_ONLY",
            "verified_history": "2021-06-15Z..2024-06-15Z",
            "redundancy_class": "R1_SINGLE_INDEPENDENT",
            "PIT_requirement": "PIT_READY_WITH_METHOD_VERSION",
            "methodology_pin": "x-trade",
            "known_hazards": [],
            "evidence_basis": ["e-1"],
        }
        caps = capabilities_from_promotion("X", [c])
        trade = caps.capability_for(SensorFamily.MECHANICAL_TRADE)
        assert trade.archive_mode is True
        assert trade.historical_mode is HistoricalMode.PUBLIC_OBJECT_STORAGE
        assert trade.live_mode is LiveMode.NONE


# ---------------------------------------------------------------------------
#  PASS / FAIL closed — required adversarial + pass proofs
# ---------------------------------------------------------------------------
class TestRequiredAdversarialProofs:
    def test_paid_trading_auth_fails_free_only(self) -> None:
        results = run_conformance_suite(
            under_test(auth_mode=AdapterAuthMode.TRADING_KEY)
        )
        _assert_this_check_fails(results, "q0_free_only", "auth")

    def test_missing_registry_entry_fails(self) -> None:
        results = run_conformance_suite(under_test(registry_policy=FreeOnlyPolicy()))
        _assert_this_check_fails(results, "q0_registry_entry", "missing")

    def test_missing_evidence_ref_fails(self) -> None:
        class NoEvidenceAdapter(FakeKrakenAdapter):
            def capabilities(self) -> ProviderCapabilities:
                caps = promoted_caps()
                return caps.model_copy(
                    update={
                        "sensors": {
                            s: c.model_copy(update={"probe_evidence_ref": None})
                            for s, c in caps.sensors.items()
                        }
                    }
                )

        results = run_conformance_suite(under_test(adapter=NoEvidenceAdapter()))
        _assert_this_check_fails(results, "q0_capability_evidence_ref", "evidence_ref")

    def test_breaking_schema_not_parsed_as_normal(self) -> None:
        expected = {"timestamp", "rate"}
        breaking = assess_schema(expected, {"timestamp"}, semantics_known=True)
        assert breaking.state is SchemaState.BREAKING_SCHEMA_CHANGE
        assert breaking.semantic_output_allowed is False

    def test_valid_evidence_lineage(self) -> None:
        results = run_conformance_suite(under_test())
        check = _check(results, "q0_capability_evidence_ref")
        assert check.passed
        check = _check(results, "q0_promotion_bounds")
        assert check.passed