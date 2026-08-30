"""SENSOR-B3-I04 / I04R1 / I04R2 — common provider conformance suite.

Hardening lineage:

- I04R1 Repair 2: PRODUCTION_CANDIDATE requires I14 promotion bounds; missing
  evidence FAILS CLOSED (no None bypass).
- I04R1 Repair 3/4: live/historical separation; strict promotion-file parsing.
- I04R1 Repair 5/6/7: empty-valid vs unsupported, schema drift, I03 retry.
- I04R1 Repair 8: adversarial fixtures are VALID typed models.
- I04R2 Issue 1/2: empty-valid vs unsupported and dispatch are BEHAVIORAL —
  the suite invokes the real adapter's fetch methods via `dispatch_fetch`.
- I04R2 Issue 3: every adversarial fixture uses enum members / model_validate
  (never unvalidated model_copy injecting raw strings into enum fields).
- I04R2 Issue 4/9: promotion bounds bind live/archive/access/auth/history-scope.
- I04R2 Issue 5: the probe evidence ref must RESOLVE, not just exist.
- I04R2 Issue 6: strict promotion-file structure (root/schema/candidates shape).
- I04R2 Issue 7: auth/access override removed — the I14 access_path is authoritative.
- I04R2 Issue 8: coarse I14 history scope is never turned into a manufactured
  native historical_mode.

All offline.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_sensor_fabric.contracts.access import FreeOnlyPolicy
from crypto_sensor_fabric.contracts.enums import AccessClass, SensorFamily
from crypto_sensor_fabric.probes.enums import (
    PITReadiness,
    ProviderRole,
    RedundancyClass,
)
from crypto_sensor_fabric.providers.base import (
    AdapterConformanceMode,
    AdapterUnderTest,
    ProviderCapabilities,
    assert_no_zero_coercion,
    assess_schema,
    capabilities_from_promotion,
    dispatch_fetch,
    load_promotion_candidates,
    promotion_bound_violations,
    promotion_provider_ids,
    run_conformance_suite,
    summarize_conformance,
)
from crypto_sensor_fabric.providers.base.enums import (
    AdapterAuthMode,
    FetchPurpose,
    FreeOnlyStatus,
    HistoryScope,
    HistoricalMode,
    LiveMode,
    QualityFlagAcquisition,
    SchemaState,
)
from crypto_sensor_fabric.providers.base.errors import CapabilityUnavailable
from crypto_sensor_fabric.providers.base.models import (
    AdapterEvidenceRef,
    FetchBatch,
    FetchRequest,
    InstrumentListRequest,
    InstrumentListResult,
    ProviderCapabilities as _PC,
    SensorCapability,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)
END = NOW.replace(hour=1)


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


CURRENT_ONLY_CANDIDATE = {
    "provider": "OKX_SWAP",
    "sensor": "MECHANICAL_BOOK_SNAPSHOT",
    "allowed_role": "CURRENT_ONLY",
    "access_path": "PUBLIC_REST",
    "history_mode": "CURRENT_ONLY",
    "verified_history": "2026-08-30T13:55:11.250844Z..2026-08-30T13:55:11.250844Z",
    "redundancy_class": "R2_TWO_INDEPENDENT",
    "PIT_requirement": "PIT_READY_WITH_METHOD_VERSION",
    "methodology_pin": "okx_swap-book_snapshot",
    "known_hazards": ["current-only surface (no historical window by nature)"],
    "evidence_basis": ["okx_swap_book_snapshot_btc-usdt-swap_RECENT_CONTROL_book_snapshot"],
}

ARCHIVE_CANDIDATE = {
    "provider": "ARCHIVE_VENUE",
    "sensor": "MECHANICAL_TRADE",
    "allowed_role": "ARCHIVE_ONLY",
    "access_path": "PUBLIC_ARCHIVE",
    "history_mode": "ARCHIVE_ONLY",
    "verified_history": "2021-06-15Z..2024-06-15Z",
    "redundancy_class": "R1_SINGLE_INDEPENDENT",
    "PIT_requirement": "PIT_READY_WITH_METHOD_VERSION",
    "methodology_pin": "archive-trade",
    "known_hazards": [],
    "evidence_basis": ["archive_trade_RECENT_CONTROL_archive"],
}


# ---------------------------------------------------------------------------
#  helpers
# ---------------------------------------------------------------------------
def _req(sensor: SensorFamily, request_id: str = "r1") -> FetchRequest:
    return FetchRequest(
        provider_id="KRAKEN_FUTURES",
        sensor_family=sensor,
        native_instrument_id="PI_XBTUSD",
        start_time=NOW,
        end_time=END,
        request_id=request_id,
        purpose=FetchPurpose.PROBE,
        adapter_semantic_version="0.0.0-fake",
    )


def _nonempty_batch(sensor: SensorFamily) -> FetchBatch:
    return FetchBatch(
        provider_id="KRAKEN_FUTURES",
        sensor_family=sensor,
        native_instrument_id="PI_XBTUSD",
        request_fingerprint=f"fp-{sensor.value}",
        requested_start=NOW,
        requested_end=END,
        row_count=1,
        is_complete=True,
        retrieved_at=NOW,
        adapter_version="0.0.0-fake",
    )


def promoted_caps() -> ProviderCapabilities:
    return capabilities_from_promotion("KRAKEN_FUTURES", PROMOTED)


def mutate(
    caps: ProviderCapabilities,
    sensor: SensorFamily,
    **updates: object,
) -> ProviderCapabilities:
    """Apply a fully-validated override to one sensor capability.

    Uses model_dump -> update -> model_validate, so every override is VALID TYPED
    data (enum members, real datetimes), never raw strings smuggled through an
    unvalidated model_copy (I04R2 Issue 3).
    """
    base = caps.sensors[sensor]
    data = base.model_dump()
    data.update(updates)
    caps.sensors[sensor] = SensorCapability.model_validate(data)
    return caps


def _sensor(caps: ProviderCapabilities, sensor: str) -> SensorCapability:
    return caps.sensors[SensorFamily(sensor)]


def free_policy() -> FreeOnlyPolicy:
    return FreeOnlyPolicy(
        access_class=AccessClass.FREE_AUTOMATED,
        cost_usd_required=0,
        payment_method_required=False,
        staking_required=False,
        transaction_required=False,
    )


class FakeKrakenAdapter:
    """Full protocol adapter with a fake transport (never touches network)."""

    provider_id = "KRAKEN_FUTURES"

    def __init__(
        self,
        caps: ProviderCapabilities | None = None,
        fixtures: dict[SensorFamily, object] | None = None,
    ) -> None:
        self._caps = caps if caps is not None else promoted_caps()
        #: default: BOOK_METRIC returns a non-empty batch; any other supported
        #: sensor returns EMPTY_VALID (0 rows).
        self._fixtures = fixtures if fixtures is not None else {}
        if SensorFamily.MECHANICAL_BOOK_METRIC not in self._fixtures:
            self._fixtures[SensorFamily.MECHANICAL_BOOK_METRIC] = _nonempty_batch(
                SensorFamily.MECHANICAL_BOOK_METRIC
            )

    def capabilities(self) -> ProviderCapabilities:
        return self._caps

    def list_instruments(self, request: InstrumentListRequest) -> InstrumentListResult:
        return InstrumentListResult(
            provider_id=self.provider_id,
            native_instrument_ids=["PI_XBTUSD"],
            retrieved_at=NOW,
        )

    def _fetch(self, request: FetchRequest) -> FetchBatch:
        capability = self._caps.capability_for(request.sensor_family)
        if not capability.supported:
            raise CapabilityUnavailable(
                provider_id=self.provider_id,
                sensor_family=request.sensor_family,
            )
        response = self._fixtures.get(request.sensor_family)
        if isinstance(response, Exception):
            raise response
        if response is not None:
            return response  # type: ignore[return-value]
        return FetchBatch(
            provider_id=self.provider_id,
            sensor_family=request.sensor_family,
            native_instrument_id=request.native_instrument_id,
            request_fingerprint=f"fp-{request.sensor_family.value}",
            requested_start=request.start_time,
            requested_end=request.end_time,
            row_count=0,
            quality_flags=[QualityFlagAcquisition.EMPTY_VALID],
            retrieved_at=NOW,
            adapter_version="0.0.0-fake",
        )

    def fetch_trades(self, r: FetchRequest) -> FetchBatch:
        return self._fetch(r)

    def fetch_liquidations(self, r: FetchRequest) -> FetchBatch:
        return self._fetch(r)

    def fetch_open_interest(self, r: FetchRequest) -> FetchBatch:
        return self._fetch(r)

    def fetch_funding(self, r: FetchRequest) -> FetchBatch:
        return self._fetch(r)

    def fetch_book(self, r: FetchRequest) -> FetchBatch:
        return self._fetch(r)

    def fetch_book_metrics(self, r: FetchRequest) -> FetchBatch:
        return self._fetch(r)

    def fetch_positioning(self, r: FetchRequest) -> FetchBatch:
        return self._fetch(r)

    def fetch_basis(self, r: FetchRequest) -> FetchBatch:
        return self._fetch(r)


def under_test(
    adapter: object | None = None,
    **overrides: object,
) -> AdapterUnderTest:
    base: dict[str, object] = {
        "adapter": FakeKrakenAdapter(),
        "registry_policy": free_policy(),
        "auth_mode": AdapterAuthMode.NO_AUTH,
        "promoted_capabilities": promoted_caps(),
        "fetch_request": _req(SensorFamily.MECHANICAL_BOOK_METRIC),
        "empty_valid_request": _req(SensorFamily.MECHANICAL_FUNDING),
        "unsupported_request": _req(SensorFamily.MECHANICAL_BASIS),
    }
    if adapter is not None:
        base["adapter"] = adapter
    base.update(overrides)
    return AdapterUnderTest(**base)  # type: ignore[arg-type]


def _check(results, check_id):
    return next(r for r in results if r.check_id == check_id)


def _assert_this_check_fails(results, check_id, detail_fragment: str) -> None:
    check = _check(results, check_id)
    assert not check.passed, check.detail
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
#  REPAIR 2 / Issue 2 — availability mode gating + dispatch
# ---------------------------------------------------------------------------
class TestProductionModeGating:
    def test_production_candidate_without_promotion_fails_closed(self) -> None:
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
        assert _check(results, "q0_production_promotion_required").passed
        assert _check(results, "q0_promotion_bounds").passed

    def test_behavioral_dispatch_returns_fetch_batch(self) -> None:
        # q0_behavioral_dispatch proves the adapter returns a valid FetchBatch
        # via its real fetch method, keyed to the request sensor.
        results = run_conformance_suite(under_test())
        assert _check(results, "q0_behavioral_dispatch").passed, _check(
            results, "q0_behavioral_dispatch"
        ).detail


# ---------------------------------------------------------------------------
#  REPAIR 1 + 8 + Issues 4/9/11 — strict promotion bounds, valid-typed fixtures
# ---------------------------------------------------------------------------
class TestPromotionBoundEnforcement:
    def _fund_bound(self) -> SensorCapability:
        return _sensor(promoted_caps(), "MECHANICAL_FUNDING")

    def test_supported_sensor_not_promoted(self) -> None:
        declared = _sensor(promoted_caps(), "MECHANICAL_FUNDING")
        bound = _PC(provider_id="KRAKEN_FUTURES").capability_for(
            SensorFamily.MECHANICAL_FUNDING
        )
        violations = promotion_bound_violations(declared, bound)
        assert any("not in promotion file" in v for v in violations)

    def test_role_change_fails(self) -> None:
        caps = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                      allowed_role=ProviderRole.PRIMARY)
        declared = _sensor(caps, "MECHANICAL_FUNDING")
        assert isinstance(declared.allowed_role, ProviderRole)
        violations = promotion_bound_violations(declared, self._fund_bound())
        assert any("allowed_role" in v for v in violations)

    def test_history_widened_earlier_fails(self) -> None:
        caps = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                      verified_history_start=datetime(2021, 1, 1, tzinfo=UTC))
        violations = promotion_bound_violations(
            _sensor(caps, "MECHANICAL_FUNDING"), self._fund_bound()
        )
        assert any("earlier than bound" in v for v in violations)

    def test_history_end_beyond_bound_fails(self) -> None:
        caps = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                      verified_history_end=datetime(2030, 1, 1, tzinfo=UTC))
        violations = promotion_bound_violations(
            _sensor(caps, "MECHANICAL_FUNDING"), self._fund_bound()
        )
        assert any("beyond bound" in v for v in violations)

    def test_history_scope_change_fails(self) -> None:
        caps = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                      history_scope=HistoryScope.CURRENT_ONLY)
        violations = promotion_bound_violations(
            _sensor(caps, "MECHANICAL_FUNDING"), self._fund_bound()
        )
        assert any("history_scope" in v for v in violations)

    def test_manufactured_native_mode_fails(self) -> None:
        # Issue 8: the coarse HISTORICAL label is NOT turned into a native mode.
        caps = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                      historical_mode=HistoricalMode.REST_RANGE)
        violations = promotion_bound_violations(
            _sensor(caps, "MECHANICAL_FUNDING"), self._fund_bound()
        )
        assert any("manufactured native historical_mode" in v for v in violations)

    def test_live_mode_widened_historical_fails(self) -> None:
        # Issue 9: historical evidence does NOT auto-grant a live contract.
        caps = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                      live_mode=LiveMode.LIVE_REST)
        violations = promotion_bound_violations(
            _sensor(caps, "MECHANICAL_FUNDING"), self._fund_bound()
        )
        assert any("live_mode" in v for v in violations)

    def test_methodology_pin_removed_fails(self) -> None:
        caps = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                      methodology_pin=None)
        violations = promotion_bound_violations(
            _sensor(caps, "MECHANICAL_FUNDING"), self._fund_bound()
        )
        assert any("methodology_pin" in v for v in violations)

    def test_hazard_removed_fails(self) -> None:
        bound = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                       known_hazards=["hazard-1"])
        declared = _sensor(promoted_caps(), "MECHANICAL_FUNDING")  # has no hazards
        violations = promotion_bound_violations(declared, _sensor(bound, "MECHANICAL_FUNDING"))
        assert any("hazard" in v and "hazard-1" in v for v in violations)

    def test_evidence_lineage_removed_fails(self) -> None:
        caps = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                      evidence_basis=[])
        violations = promotion_bound_violations(
            _sensor(caps, "MECHANICAL_FUNDING"), self._fund_bound()
        )
        assert any("evidence basis" in v for v in violations)

    def test_pit_upgraded_fails(self) -> None:
        caps = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                      pit_requirement=PITReadiness.PIT_READY)
        declared = _sensor(caps, "MECHANICAL_FUNDING")
        assert isinstance(declared.pit_requirement, PITReadiness)
        violations = promotion_bound_violations(declared, self._fund_bound())
        assert any("PIT requirement" in v for v in violations)

    def test_redundancy_class_changed_fails(self) -> None:
        caps = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                      redundancy_class=RedundancyClass.R1_SINGLE_INDEPENDENT)
        declared = _sensor(caps, "MECHANICAL_FUNDING")
        assert isinstance(declared.redundancy_class, RedundancyClass)
        violations = promotion_bound_violations(declared, self._fund_bound())
        assert any("redundancy_class" in v for v in violations)

    def test_access_path_changed_fails(self) -> None:
        caps = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                      access_mode="PUBLIC_ARCHIVE")
        violations = promotion_bound_violations(
            _sensor(caps, "MECHANICAL_FUNDING"), self._fund_bound()
        )
        assert any("access_path" in v for v in violations)

    def test_auth_contract_changed_fails(self) -> None:
        caps = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                      auth_requirement=AdapterAuthMode.FREE_API_KEY)
        violations = promotion_bound_violations(
            _sensor(caps, "MECHANICAL_FUNDING"), self._fund_bound()
        )
        assert any("auth_requirement" in v for v in violations)

    def test_free_only_status_downgraded_no_bypass(self) -> None:
        caps = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                      free_access_status=FreeOnlyStatus.UNVERIFIED)
        violations = promotion_bound_violations(
            _sensor(caps, "MECHANICAL_FUNDING"), self._fund_bound()
        )
        assert any("free_access_status" in v for v in violations)

    def test_non_archive_becoming_archive_fails(self) -> None:
        caps = mutate(promoted_caps(), SensorFamily.MECHANICAL_FUNDING,
                      archive_mode=True)
        violations = promotion_bound_violations(
            _sensor(caps, "MECHANICAL_FUNDING"), self._fund_bound()
        )
        assert any("archive_mode" in v for v in violations)

    def test_current_only_cannot_become_historical(self) -> None:
        bound_caps = capabilities_from_promotion("OKX_SWAP", [CURRENT_ONLY_CANDIDATE])
        bound = _sensor(bound_caps, "MECHANICAL_BOOK_SNAPSHOT")
        # declared identical to bound passes (current-only stays current-only)
        assert not promotion_bound_violations(bound, bound)
        # widen CURRENT_ONLY -> HISTORICAL
        declared_caps = capabilities_from_promotion(
            "OKX_SWAP",
            [
                {
                    **CURRENT_ONLY_CANDIDATE,
                    "history_mode": "HISTORICAL",
                    "verified_history": "2021-06-15Z..2026-08-30T13:55:11.250844Z",
                    "allowed_role": "PRIMARY",
                }
            ],
        )
        declared = _sensor(declared_caps, "MECHANICAL_BOOK_SNAPSHOT")
        violations = promotion_bound_violations(declared, bound)
        assert any(
            "CURRENT_ONLY" in v or "history_scope" in v for v in violations
        )

    def test_live_mode_removed_from_current_only_fails(self) -> None:
        bound_caps = capabilities_from_promotion("OKX_SWAP", [CURRENT_ONLY_CANDIDATE])
        bound = _sensor(bound_caps, "MECHANICAL_BOOK_SNAPSHOT")
        declared_caps = mutate(
            capabilities_from_promotion("OKX_SWAP", [CURRENT_ONLY_CANDIDATE]),
            SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
            live_mode=LiveMode.NONE,
        )
        declared = _sensor(declared_caps, "MECHANICAL_BOOK_SNAPSHOT")
        violations = promotion_bound_violations(declared, bound)
        assert any("live_mode" in v for v in violations)

    def test_archive_only_cannot_become_rest(self) -> None:
        bound_caps = capabilities_from_promotion("ARCHIVE_VENUE", [ARCHIVE_CANDIDATE])
        bound = _sensor(bound_caps, "MECHANICAL_TRADE")
        assert bound.archive_mode is True
        declared_caps = capabilities_from_promotion(
            "ARCHIVE_VENUE",
            [
                {
                    **ARCHIVE_CANDIDATE,
                    "history_mode": "HISTORICAL",
                    "access_path": "PUBLIC_REST",
                }
            ],
        )
        # the coarse label must not be silently editable
        declared = _sensor(declared_caps, "MECHANICAL_TRADE")
        violations = promotion_bound_violations(declared, bound)
        assert any(
            "history_scope" in v or "archive_mode" in v or "access_path" in v
            for v in violations
        )


# ---------------------------------------------------------------------------
#  REPAIR 9 — no dead `declared_capabilities` field
# ---------------------------------------------------------------------------
class TestNoDeadState:
    def test_adapter_under_test_has_no_declared_capabilities_field(self) -> None:
        import dataclasses

        fields = {f.name for f in dataclasses.fields(AdapterUnderTest)}
        assert "declared_capabilities" not in fields


# ---------------------------------------------------------------------------
#  REPAIR 3 + Issues 8/9 — live vs historical separation, no manufactured mode
# ---------------------------------------------------------------------------
class TestLiveHistoricalSeparation:
    def test_historical_does_not_grant_live_and_has_no_manufactured_native_mode(
        self,
    ) -> None:
        caps = capabilities_from_promotion("KRAKEN_FUTURES", load_promotion_candidates())
        funding = caps.capability_for(SensorFamily.MECHANICAL_FUNDING)
        assert funding.history_scope is HistoryScope.HISTORICAL
        # Issue 8: exact native historical_mode is NOT inferred from the coarse
        # HISTORICAL label
        assert funding.historical_mode is None
        # Issue 9: historical evidence does NOT auto-grant a live contract
        assert funding.live_mode is LiveMode.NONE
        assert funding.archive_mode is False

    def test_current_only_is_live_snapshot_not_history(self) -> None:
        caps = capabilities_from_promotion("OKX_SWAP", load_promotion_candidates())
        book = caps.capability_for(SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
        assert book.history_scope is HistoryScope.CURRENT_ONLY
        assert book.historical_mode is None  # no invented historical depth
        assert book.live_mode is LiveMode.LIVE_REST
        assert book.archive_mode is False

    def test_archive_only_does_not_imply_rest_or_live(self) -> None:
        caps = capabilities_from_promotion("ARCHIVE_VENUE", [ARCHIVE_CANDIDATE])
        trade = caps.capability_for(SensorFamily.MECHANICAL_TRADE)
        assert trade.history_scope is HistoryScope.ARCHIVE_ONLY
        assert trade.historical_mode is None
        assert trade.archive_mode is True
        assert trade.live_mode is LiveMode.NONE
        assert trade.live_mode is not LiveMode.LIVE_REST


# ---------------------------------------------------------------------------
#  REPAIR 4 — strict promotion-file field parsing
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

    def test_verified_history_out_of_order_fails(self) -> None:
        c = self._base_candidate()
        c["verified_history"] = "2026-06-15Z..2024-06-15Z"
        with pytest.raises(ValueError):
            capabilities_from_promotion("KRAKEN_FUTURES", [c])

    def test_missing_evidence_basis_fails(self) -> None:
        c = self._base_candidate()
        c["evidence_basis"] = []
        with pytest.raises(ValueError):
            capabilities_from_promotion("KRAKEN_FUTURES", [c])

    def test_missing_methodology_pin_fails(self) -> None:
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
#  REPAIR 6 / Issue 6 — strict promotion-file STRUCTURE
# ---------------------------------------------------------------------------
class TestPromotionFileStructure:
    def _write(self, tmp_path, payload: object):
        import yaml

        p = tmp_path / "promo.yaml"
        p.write_text(yaml.safe_dump(payload), encoding="utf-8")
        return p

    def _with_candidates(self, candidates) -> dict:
        return {"schema_version": "2.0", "candidates": candidates}

    def test_root_not_mapping_fails(self, tmp_path) -> None:
        p = self._write(tmp_path, ["not-a-mapping"])
        with pytest.raises(ValueError):
            load_promotion_candidates(p)

    def test_missing_schema_version_fails(self, tmp_path) -> None:
        p = self._write(tmp_path, {"candidates": [dict(PROMOTED[0])]})
        with pytest.raises(ValueError):
            load_promotion_candidates(p)

    def test_unsupported_schema_version_fails(self, tmp_path) -> None:
        p = self._write(
            tmp_path, {"schema_version": "99.0", "candidates": [dict(PROMOTED[0])]}
        )
        with pytest.raises(ValueError):
            load_promotion_candidates(p)

    def test_candidates_not_list_fails(self, tmp_path) -> None:
        p = self._write(tmp_path, self._with_candidates({"a": 1}))
        with pytest.raises(ValueError):
            load_promotion_candidates(p)

    def test_empty_candidates_fails(self, tmp_path) -> None:
        p = self._write(tmp_path, self._with_candidates([]))
        with pytest.raises(ValueError):
            load_promotion_candidates(p)

    def test_candidate_not_mapping_fails(self, tmp_path) -> None:
        p = self._write(tmp_path, self._with_candidates(["nope"]))
        with pytest.raises(ValueError):
            load_promotion_candidates(p)

    def test_missing_provider_fails(self, tmp_path) -> None:
        c = dict(PROMOTED[0])
        del c["provider"]
        p = self._write(tmp_path, self._with_candidates([c]))
        with pytest.raises(ValueError):
            load_promotion_candidates(p)

    def test_missing_sensor_fails(self, tmp_path) -> None:
        c = dict(PROMOTED[0])
        del c["sensor"]
        p = self._write(tmp_path, self._with_candidates([c]))
        with pytest.raises(ValueError):
            load_promotion_candidates(p)

    def test_duplicate_provider_sensor_fails_and_never_overwrites(self) -> None:
        first = dict(PROMOTED[0])
        second = {**PROMOTED[0], "allowed_role": "PRIMARY"}
        with pytest.raises(ValueError):
            capabilities_from_promotion("KRAKEN_FUTURES", [first, second])

    def test_real_promotion_file_loads(self) -> None:
        candidates = load_promotion_candidates()
        assert candidates
        assert set(promotion_provider_ids(candidates)) == {
            "KRAKEN_FUTURES", "GATE_FUTURES", "OKX_SWAP", "DERIBIT",
        }
        assert "BINANCE_USDM" not in promotion_provider_ids(candidates)


# ---------------------------------------------------------------------------
#  REPAIR 5 + Issue 1 — empty-valid vs unsupported (behavioral)
# ---------------------------------------------------------------------------
class TestEmptyValidVsUnsupportedBehavioral:
    def test_unsupported_sensor_is_typed_not_empty(self) -> None:
        unbound = declared_caps()
        basis = unbound.capability_for(SensorFamily.MECHANICAL_BASIS)
        assert basis.supported is False
        with pytest.raises(CapabilityUnavailable):
            dispatch_fetch(FakeKrakenAdapter(), _req(SensorFamily.MECHANICAL_BASIS))

    def test_supported_empty_is_explicit_emvalid_batch(self) -> None:
        adapter = FakeKrakenAdapter()
        batch = dispatch_fetch(adapter, _req(SensorFamily.MECHANICAL_FUNDING))
        assert isinstance(batch, FetchBatch)
        assert batch.row_count == 0
        assert QualityFlagAcquisition.EMPTY_VALID in batch.quality_flags

    def test_supported_nonempty_returns_batch(self) -> None:
        adapter = FakeKrakenAdapter()
        batch = dispatch_fetch(adapter, _req(SensorFamily.MECHANICAL_BOOK_METRIC))
        assert isinstance(batch, FetchBatch)
        assert batch.row_count == 1
        assert batch.is_complete

    def test_without_explicit_emvalid_flag_model_fails_closed(self) -> None:
        with pytest.raises(Exception):
            FetchBatch(
                provider_id="P",
                sensor_family=SensorFamily.MECHANICAL_FUNDING,
                native_instrument_id="PI_XBTUSD",
                request_fingerprint="fp",
                requested_start=NOW,
                requested_end=END,
                row_count=0,
                retrieved_at=NOW,
                adapter_version="0.0.0",
            )


# ---------------------------------------------------------------------------
#  REPAIR 6 — schema drift fail-closed
# ---------------------------------------------------------------------------
class TestSchemaDriftFailClosed:
    def test_parse_fail_closed_blocking_states(self) -> None:
        from crypto_sensor_fabric.providers.base.schema import parse_fail_closed

        expected = {"timestamp", "rate"}
        known = assess_schema(expected, {"timestamp", "rate"}, semantics_known=True)
        parsed = parse_fail_closed(
            known, {"timestamp": 1, "rate": 2.0}, required=expected, parsed_factory=lambda row: row
        )
        assert parsed["rate"] == 2.0

        breaking = assess_schema(expected, {"timestamp"}, semantics_known=True)
        with pytest.raises(ValueError):
            parse_fail_closed(
                breaking, {"timestamp": 1}, required=expected, parsed_factory=lambda row: row
            )

        unknown = assess_schema(expected, {"timestamp"}, semantics_known=False)
        with pytest.raises(ValueError):
            parse_fail_closed(
                unknown, {"timestamp": 1}, required=expected, parsed_factory=lambda row: row
            )

    def test_no_zero_coercion(self) -> None:
        expected = {"timestamp", "rate"}
        breaking = assess_schema(expected, {"timestamp"}, semantics_known=True)
        with pytest.raises(KeyError):
            assert_no_zero_coercion(breaking, {"timestamp": 1}, "rate")
        known = assess_schema(expected, {"timestamp", "rate"}, semantics_known=True)
        assert_no_zero_coercion(known, {"timestamp": 1, "rate": 2}, "rate")


# ---------------------------------------------------------------------------
#  REPAIR 7 + Issue 7 — retry classifier (real I03) ; geo/access never retried
# ---------------------------------------------------------------------------
class TestRetryClassifierConformance:
    def test_transient_retryable(self) -> None:
        results = run_conformance_suite(under_test())
        assert _check(results, "q2_retry_classification").passed

    def test_geo_restriction_never_retried(self) -> None:
        from crypto_sensor_fabric.providers.base.errors import GeoRestricted
        from crypto_sensor_fabric.providers.base.retry import RetryPolicy, is_retryable

        policy = RetryPolicy(max_attempts=5)
        geo = GeoRestricted("P", SensorFamily.MECHANICAL_TRADE)
        assert is_retryable(geo, policy) is False


# ---------------------------------------------------------------------------
#  I14 evidence integration
# ---------------------------------------------------------------------------
class TestPromotionIntegration:
    def test_capabilities_bound_to_i14_fields(self) -> None:
        cands = load_promotion_candidates()
        caps = capabilities_from_promotion("KRAKEN_FUTURES", cands)
        funding = caps.capability_for(SensorFamily.MECHANICAL_FUNDING)
        assert funding.supported
        assert funding.allowed_role is ProviderRole.SECONDARY
        assert funding.methodology_pin == "kraken_futures-funding"
        assert funding.pit_requirement is PITReadiness.PIT_READY_WITH_METHOD_VERSION
        assert funding.redundancy_class is RedundancyClass.R3_THREE_PLUS_INDEPENDENT
        assert funding.evidence_basis
        assert funding.probe_evidence_ref is not None
        assert funding.verified_history_start is not None

    def test_unpromoted_provider_has_no_capabilities(self) -> None:
        cands = load_promotion_candidates()
        caps = capabilities_from_promotion("BINANCE_USDM", cands)
        assert not caps.supported_sensors()


# ---------------------------------------------------------------------------
#  Issue 5 — evidence-ref resolution
# ---------------------------------------------------------------------------
class TestEvidenceRefResolution:
    def _caps_with_ref(self, ref: AdapterEvidenceRef) -> ProviderCapabilities:
        return mutate(
            promoted_caps(),
            SensorFamily.MECHANICAL_FUNDING,
            probe_evidence_ref=ref,
        )

    def test_id_not_in_i14_basis_fails(self) -> None:
        ref = AdapterEvidenceRef(
            evidence_id="unrelated-evidence-id",
            provider_id="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
        )
        adapter = FakeKrakenAdapter(caps=self._caps_with_ref(ref))
        results = run_conformance_suite(under_test(adapter=adapter))
        _assert_this_check_fails(results, "q0_evidence_ref_resolves", "not in the I14")

    def test_provider_mismatch_fails(self) -> None:
        ref = AdapterEvidenceRef(
            evidence_id=promoted_caps().sensors[SensorFamily.MECHANICAL_FUNDING].evidence_basis[0],
            provider_id="GATE_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
        )
        adapter = FakeKrakenAdapter(caps=self._caps_with_ref(ref))
        results = run_conformance_suite(under_test(adapter=adapter))
        _assert_this_check_fails(results, "q0_evidence_ref_resolves", "provider")

    def test_sensor_mismatch_fails(self) -> None:
        ref = AdapterEvidenceRef(
            evidence_id=promoted_caps().sensors[SensorFamily.MECHANICAL_FUNDING].evidence_basis[0],
            provider_id="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_TRADE,
        )
        adapter = FakeKrakenAdapter(caps=self._caps_with_ref(ref))
        results = run_conformance_suite(under_test(adapter=adapter))
        _assert_this_check_fails(results, "q0_evidence_ref_resolves", "sensor")

    def test_valid_lineage_passes(self) -> None:
        results = run_conformance_suite(under_test())
        assert _check(results, "q0_evidence_ref_resolves").passed


# ---------------------------------------------------------------------------
#  Issue 7 — no access/auth override can change the I14 contract
# ---------------------------------------------------------------------------
class TestAuthOverrideRemoved:
    def test_capabilities_from_promotion_has_no_auth_override_param(self) -> None:
        import inspect

        sig = inspect.signature(capabilities_from_promotion)
        assert "auth_mode_override" not in sig.parameters

    def test_paid_trading_auth_fails_free_only_gate(self) -> None:
        results = run_conformance_suite(
            under_test(auth_mode=AdapterAuthMode.TRADING_KEY)
        )
        _assert_this_check_fails(results, "q0_free_only", "auth")


# ---------------------------------------------------------------------------
#  PASS / FAIL closed — required adversarial + pass proofs
# ---------------------------------------------------------------------------
class TestRequiredAdversarialProofs:
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

    def test_unknown_schema_preserves_raw_and_blocks(self) -> None:
        unknown = assess_schema(set(), {"timestamp"}, semantics_known=False)
        assert unknown.state is SchemaState.UNKNOWN_SCHEMA
        assert unknown.raw_preserved is True
        assert unknown.semantic_output_allowed is False


def declared_caps(**sensor_overrides: object) -> ProviderCapabilities:
    """A type-valid declared capability set, with validated per-sensor overrides.

    Every override is routed through real validation (model_dump +
    model_validate) — never unvalidated model_copy.
    """
    caps = promoted_caps()
    for sensor_name, override in sensor_overrides.items():
        if not isinstance(override, dict):
            raise TypeError("overrides must be dicts")
        mutate(caps, SensorFamily(sensor_name), **override)  # type: ignore[arg-type]
    return caps