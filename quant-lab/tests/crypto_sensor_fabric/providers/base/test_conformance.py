"""SENSOR-B3-I04 — common provider conformance suite + I14 evidence integration.

A full fake adapter (implementing the entire MechanicalProviderAdapter
protocol with a fake transport) must pass the conformance suite; a degraded
adapter must fail the exact invariant it violates.  I14 promotion-file
integration proves capabilities are bound by source_promotion_candidates.yaml
and never upgraded beyond it.  All offline.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_sensor_fabric.contracts.access import FreeOnlyPolicy
from crypto_sensor_fabric.contracts.enums import AccessClass, SensorFamily
from crypto_sensor_fabric.providers.base import (
    AdapterEvidenceRef,
    AdapterUnderTest,
    FetchBatch,
    FetchRequest,
    InstrumentListRequest,
    InstrumentListResult,
    ProviderCapabilities,
    RawPayloadEnvelope,
    ResumeToken,
    fingerprint_request,
    payload_hash,
    run_conformance_suite,
    summarize_conformance,
)
from crypto_sensor_fabric.providers.base.capabilities import (
    capabilities_from_promotion,
    load_promotion_candidates,
    promotion_provider_ids,
)
from crypto_sensor_fabric.providers.base.enums import (
    AdapterAuthMode,
    FetchPurpose,
    LiveMode,
    PaginationMode,
    SchemaState,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)

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


class FakeKrakenAdapter:
    """Full protocol adapter with a fake transport (never touches network)."""

    provider_id = "KRAKEN_FUTURES"

    def capabilities(self) -> ProviderCapabilities:
        return capabilities_from_promotion("KRAKEN_FUTURES", PROMOTED)

    def list_instruments(self, request: InstrumentListRequest) -> InstrumentListResult:
        return InstrumentListResult(
            provider_id=self.provider_id,
            native_instrument_ids=["PI_XBTUSD", "PI_ETHUSD"],
            retrieved_at=NOW,
        )

    def _batch(self, sensor: SensorFamily, rows: list[dict]) -> FetchBatch:
        body = b'{"rows": []}' if not rows else b'{"rows": [1,2,3]}'
        return FetchBatch(
            provider_id=self.provider_id,
            sensor_family=sensor,
            native_instrument_id="PI_XBTUSD",
            request_fingerprint=f"fp-{sensor.value}",
            requested_start=NOW,
            requested_end=NOW.replace(hour=1),
            row_count=len(rows),
            raw_payloads=[
                RawPayloadEnvelope(
                    provider_id=self.provider_id,
                    sensor_family=sensor,
                    request_fingerprint=f"fp-{sensor.value}",
                    raw_body=body,
                    content_hash=payload_hash(body),
                    schema_state=SchemaState.KNOWN_SCHEMA,
                    evidence_ref=AdapterEvidenceRef(
                        evidence_id=f"evidence-{sensor.value}",
                        provider_id=self.provider_id,
                        sensor_family=sensor,
                    ),
                    adapter_version="0.1.0",
                )
            ],
            is_complete=True,
            retrieved_at=NOW,
            adapter_version="0.1.0",
        )

    def fetch_trades(self, request: FetchRequest) -> FetchBatch:
        return self._batch(SensorFamily.MECHANICAL_TRADE, [{"id": 1}])

    def fetch_liquidations(self, request: FetchRequest) -> FetchBatch:
        return self._batch(SensorFamily.MECHANICAL_LIQUIDATION, [{"id": 1}])

    def fetch_open_interest(self, request: FetchRequest) -> FetchBatch:
        return self._batch(SensorFamily.MECHANICAL_OPEN_INTEREST, [{"id": 1}])

    def fetch_funding(self, request: FetchRequest) -> FetchBatch:
        return self._batch(SensorFamily.MECHANICAL_FUNDING, [{"id": 1}])

    def fetch_book(self, request: FetchRequest) -> FetchBatch:
        return self._batch(SensorFamily.MECHANICAL_BOOK_SNAPSHOT, [{"id": 1}])

    def fetch_book_metrics(self, request: FetchRequest) -> FetchBatch:
        return self._batch(SensorFamily.MECHANICAL_BOOK_METRIC, [{"id": 1}])

    def fetch_positioning(self, request: FetchRequest) -> FetchBatch:
        return self._batch(SensorFamily.MECHANICAL_POSITIONING, [{"id": 1}])

    def fetch_basis(self, request: FetchRequest) -> FetchBatch:
        return self._batch(SensorFamily.MECHANICAL_BASIS, [{"id": 1}])


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
        "promoted_capabilities": capabilities_from_promotion(
            "KRAKEN_FUTURES", PROMOTED
        ),
    }
    if adapter is not None:
        base["adapter"] = adapter
    base.update(overrides)
    return AdapterUnderTest(**base)  # type: ignore[arg-type]


class TestConformancePass:
    def test_full_adapter_passes_all_checks(self) -> None:
        results = run_conformance_suite(under_test())
        failed = [r for r in results if not r.passed]
        assert not failed, [f"{r.check_id}: {r.detail}" for r in failed]
        summary = summarize_conformance(results)
        assert summary["passed"] == summary["checks"]
        assert summary["failed"] == 0

    def test_summary_counts(self) -> None:
        results = run_conformance_suite(under_test())
        summary = summarize_conformance(results)
        assert summary["checks"] == len(results)
        assert summary["passed"] + summary["failed"] == summary["checks"]


class TestConformanceFailClosed:
    def test_missing_registry_entry_fails(self) -> None:
        policy = FreeOnlyPolicy()  # access_class UNVERIFIED
        results = run_conformance_suite(under_test(registry_policy=policy))
        check = next(r for r in results if r.check_id == "q0_registry_entry")
        assert not check.passed

    def test_paid_auth_fails_free_only_gate(self) -> None:
        results = run_conformance_suite(
            under_test(auth_mode=AdapterAuthMode.PAID_KEY)
        )
        check = next(r for r in results if r.check_id == "q0_free_only")
        assert not check.passed

    def test_undeclared_sensor_fails_evidence_check(self) -> None:
        class NoEvidenceAdapter(FakeKrakenAdapter):
            def capabilities(self) -> ProviderCapabilities:
                caps = capabilities_from_promotion("KRAKEN_FUTURES", PROMOTED)
                # strip the evidence ref -> supported sensor without evidence
                stripped = caps.model_copy(
                    update={
                        "sensors": {
                            s: c.model_copy(update={"probe_evidence_ref": None})
                            for s, c in caps.sensors.items()
                        }
                    }
                )
                return stripped

        results = run_conformance_suite(under_test(adapter=NoEvidenceAdapter()))
        check = next(
            r for r in results if r.check_id == "q0_capability_evidence_ref"
        )
        assert not check.passed

    def test_upgraded_capability_fails_promotion_bounds(self) -> None:
        class OverclaimingAdapter(FakeKrakenAdapter):
            def capabilities(self) -> ProviderCapabilities:
                caps = capabilities_from_promotion("KRAKEN_FUTURES", PROMOTED)
                funding = caps.sensors[SensorFamily.MECHANICAL_FUNDING]
                upgraded = funding.model_copy(
                    update={
                        "pit_requirement": "PIT_READY",
                        "verified_history_start": datetime(2021, 1, 1, tzinfo=UTC),
                    }
                )
                caps.sensors[SensorFamily.MECHANICAL_FUNDING] = upgraded
                return caps

        results = run_conformance_suite(under_test(adapter=OverclaimingAdapter()))
        check = next(r for r in results if r.check_id == "q0_promotion_bounds")
        assert not check.passed


class TestPromotionIntegration:
    def test_promotion_file_loads_real_candidates(self) -> None:
        candidates = load_promotion_candidates()
        providers = promotion_provider_ids(candidates)
        assert set(providers) == {
            "KRAKEN_FUTURES",
            "GATE_FUTURES",
            "OKX_SWAP",
            "DERIBIT",
        }
        # exactly the I14 promoted set — Binance/Bybit/Coinalyze/Bitfinex absent
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

    def test_current_only_stays_current_only(self) -> None:
        candidates = load_promotion_candidates()
        caps = capabilities_from_promotion("DERIBIT", candidates)
        book = caps.capability_for(SensorFamily.MECHANICAL_BOOK_SNAPSHOT)
        assert book.supported
        assert book.historical_mode.value == "LIVE_REST_ONLY"
        assert book.live_mode is LiveMode.NONE

    def test_unpromoted_provider_has_no_capabilities(self) -> None:
        candidates = load_promotion_candidates()
        caps = capabilities_from_promotion("BINANCE_USDM", candidates)
        assert not caps.supported_sensors()

    def test_pit_ready_requires_verified_history(self) -> None:
        with pytest.raises(Exception):
            capabilities_from_promotion(
                "KRAKEN_FUTURES",
                [
                    {
                        "provider": "KRAKEN_FUTURES",
                        "sensor": "MECHANICAL_FUNDING",
                        "allowed_role": "SECONDARY",
                        "access_path": "PUBLIC_REST",
                        "history_mode": "HISTORICAL",
                        "verified_history": "",
                        "redundancy_class": "R3_THREE_PLUS_INDEPENDENT",
                        "PIT_requirement": "PIT_READY_WITH_METHOD_VERSION",
                        "methodology_pin": "x",
                        "evidence_basis": ["e1"],
                    }
                ],
            )


class TestFetchFlow:
    def test_adapter_batch_preserves_raw_and_completion(self) -> None:
        adapter = FakeKrakenAdapter()
        request = FetchRequest(
            provider_id="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            native_instrument_id="PI_XBTUSD",
            start_time=NOW,
            end_time=NOW.replace(hour=1),
            granularity="1h",
            request_id="req-1",
            purpose=FetchPurpose.PROBE,
            adapter_semantic_version="0.1.0",
        )
        batch = adapter.fetch_funding(request)
        assert batch.provider_id == "KRAKEN_FUTURES"
        assert batch.row_count == 1
        assert batch.is_complete
        assert batch.raw_payloads
        assert batch.raw_payloads[0].content_hash == payload_hash(
            batch.raw_payloads[0].raw_body
        )

    def test_fingerprint_stable_across_fetch(self) -> None:
        request = FetchRequest(
            provider_id="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            native_instrument_id="PI_XBTUSD",
            start_time=NOW,
            end_time=NOW.replace(hour=1),
            granularity="1h",
            request_id="req-1",
            purpose=FetchPurpose.BACKFILL,
            adapter_semantic_version="0.1.0",
        )
        fp1 = fingerprint_request(request, "/api/charts/v1/analytics")
        fp2 = fingerprint_request(request, "/api/charts/v1/analytics")
        assert fp1 == fp2

    def test_resume_token_round_trip(self) -> None:
        token = ResumeToken(
            mode=PaginationMode.CURSOR,
            provider_cursor="abc",
            page_number=2,
            last_timestamp=NOW,
            provider_native_state={"next": "z"},
        )
        rebuilt = ResumeToken.model_validate_json(token.model_dump_json())
        assert rebuilt == token
