"""SENSOR-B3-I01 — base models + provider protocol tests.

All offline.  Covers the frozen base contract: provider identity immutability,
sensor-specific capability declarations, typed unsupported, UTC fetch
requests, raw payload preservation, empty-valid vs unsupported distinction,
schema/version identity, and the common protocol surface.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import (
    FetchPurpose,
    HistoricalMode,
    LiveMode,
    PaginationMode,
    SchemaState,
)
from crypto_sensor_fabric.providers.base.errors import CapabilityUnavailable
from crypto_sensor_fabric.providers.base.models import (
    FetchBatch,
    FetchRequest,
    ProviderCapabilities,
    RawPayloadEnvelope,
    ResumeToken,
    SensorCapability,
)
from crypto_sensor_fabric.providers.base.protocol import (
    MechanicalProviderAdapter,
    ensure_supported,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def make_request(**overrides: object) -> FetchRequest:
    base: dict[str, object] = {
        "provider_id": "KRAKEN_FUTURES",
        "sensor_family": SensorFamily.MECHANICAL_FUNDING,
        "native_instrument_id": "PI_XBTUSD",
        "start_time": NOW,
        "end_time": NOW.replace(hour=1),
        "granularity": "1h",
        "request_id": "req-1",
        "purpose": FetchPurpose.BACKFILL,
        "adapter_semantic_version": "0.1.0",
    }
    base.update(overrides)
    return FetchRequest.model_validate(base)


class TestProviderIdentity:
    def test_provider_id_required(self) -> None:
        with pytest.raises(ValidationError):
            make_request(provider_id="")

    def test_provider_identity_survives_serialization(self) -> None:
        request = make_request()
        rebuilt = FetchRequest.model_validate_json(request.model_dump_json())
        assert rebuilt.provider_id == "KRAKEN_FUTURES"
        assert rebuilt.native_instrument_id == "PI_XBTUSD"
        assert rebuilt.request_id == "req-1"


class TestUTCFetchRequest:
    def test_naive_datetime_rejected(self) -> None:
        naive = datetime(2026, 1, 1)
        with pytest.raises(ValidationError):
            make_request(start_time=naive)

    def test_window_order_enforced(self) -> None:
        with pytest.raises(ValidationError):
            make_request(
                start_time=NOW.replace(hour=2),
                end_time=NOW.replace(hour=1),
            )

    def test_utc_boundaries_normalized(self) -> None:
        request = make_request(
            start_time=datetime(2026, 1, 1, tzinfo=UTC),
            end_time=datetime(2026, 1, 1, hour=1, tzinfo=UTC),
        )
        assert request.start_time.tzinfo == UTC
        assert request.end_time.tzinfo == UTC

    def test_schema_version_required(self) -> None:
        with pytest.raises(ValidationError):
            make_request(adapter_semantic_version="")


class TestCapabilityDeclaration:
    def test_capabilities_are_sensor_specific(self) -> None:
        capabilities = ProviderCapabilities(
            provider_id="KRAKEN_FUTURES",
            sensors={
                SensorFamily.MECHANICAL_FUNDING: SensorCapability(
                    sensor_family=SensorFamily.MECHANICAL_FUNDING,
                    supported=True,
                    historical_mode=HistoricalMode.REST_RANGE,
                    live_mode=LiveMode.LIVE_REST,
                    pagination_mode=PaginationMode.TIME_RANGE,
                ),
                SensorFamily.MECHANICAL_LIQUIDATION: SensorCapability(
                    sensor_family=SensorFamily.MECHANICAL_LIQUIDATION,
                    supported=True,
                    historical_mode=HistoricalMode.REST_RANGE,
                ),
            },
        )
        funding = capabilities.capability_for(SensorFamily.MECHANICAL_FUNDING)
        liquidation = capabilities.capability_for(SensorFamily.MECHANICAL_LIQUIDATION)
        assert funding.supported
        assert liquidation.supported
        # no global capability flag — each sensor has its own object
        assert funding is not liquidation

    def test_unsupported_sensor_fails_closed_by_default(self) -> None:
        capabilities = ProviderCapabilities(provider_id="KRAKEN_FUTURES")
        basis = capabilities.capability_for(SensorFamily.MECHANICAL_BASIS)
        assert not basis.supported
        assert basis.historical_mode is None
        assert basis.live_mode is LiveMode.NONE

    def test_unsupported_cannot_declare_surface(self) -> None:
        with pytest.raises(ValidationError):
            SensorCapability(
                sensor_family=SensorFamily.MECHANICAL_BASIS,
                supported=False,
                historical_mode=HistoricalMode.REST_RANGE,
            )

    def test_capability_rejects_unknown_sensor(self) -> None:
        with pytest.raises(ValidationError):
            ProviderCapabilities(
                provider_id="X",
                sensors={"NOT_A_SENSOR": {"sensor_family": "NOT_A_SENSOR"}},
            )


class TestTypedUnsupported:
    def test_ensure_supported_raises_typed_error(self) -> None:
        class FakeAdapter:
            provider_id = "FAKE"

            def capabilities(self) -> ProviderCapabilities:
                return ProviderCapabilities(
                    provider_id="FAKE",
                    sensors={
                        SensorFamily.MECHANICAL_FUNDING: SensorCapability(
                            sensor_family=SensorFamily.MECHANICAL_FUNDING,
                            supported=True,
                        )
                    },
                )

        adapter = FakeAdapter()
        # supported path passes
        ensure_supported(adapter, SensorFamily.MECHANICAL_FUNDING)
        # unsupported path is a typed CapabilityUnavailable, not []/None
        with pytest.raises(CapabilityUnavailable):
            ensure_supported(adapter, SensorFamily.MECHANICAL_BASIS)

    def test_protocol_is_runtime_checkable(self) -> None:
        class FullAdapter:
            provider_id = "FULL"

            def capabilities(self):  # pragma: no cover - protocol probe
                raise NotImplementedError

            def list_instruments(self, request):  # pragma: no cover
                raise NotImplementedError

            def fetch_trades(self, request):  # pragma: no cover
                raise NotImplementedError

            def fetch_liquidations(self, request):  # pragma: no cover
                raise NotImplementedError

            def fetch_open_interest(self, request):  # pragma: no cover
                raise NotImplementedError

            def fetch_funding(self, request):  # pragma: no cover
                raise NotImplementedError

            def fetch_book(self, request):  # pragma: no cover
                raise NotImplementedError

            def fetch_book_metrics(self, request):  # pragma: no cover
                raise NotImplementedError

            def fetch_positioning(self, request):  # pragma: no cover
                raise NotImplementedError

            def fetch_basis(self, request):  # pragma: no cover
                raise NotImplementedError

        assert isinstance(FullAdapter(), MechanicalProviderAdapter)


class TestRawPayloadPreservation:
    def test_raw_payload_envelope_preserves_body_and_hash(self) -> None:
        envelope = RawPayloadEnvelope(
            provider_id="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            request_fingerprint="fp-1",
            raw_body=b'{"rate": "0.0001"}',
            content_hash="abc123",
            schema_state=SchemaState.UNKNOWN_SCHEMA,
            adapter_version="0.1.0",
        )
        assert envelope.raw_body == b'{"rate": "0.0001"}'
        assert envelope.content_hash == "abc123"

    def test_known_schema_requires_evidence_ref(self) -> None:
        with pytest.raises(ValidationError):
            RawPayloadEnvelope(
                provider_id="KRAKEN_FUTURES",
                sensor_family=SensorFamily.MECHANICAL_FUNDING,
                request_fingerprint="fp-1",
                raw_body="{}",
                content_hash="h",
                schema_state=SchemaState.KNOWN_SCHEMA,
                adapter_version="0.1.0",
            )

    def test_fetch_batch_requires_raw_payload(self) -> None:
        # empty batch without EMPTY_VALID flag is ambiguous -> fail closed
        with pytest.raises(ValidationError):
            FetchBatch(
                provider_id="KRAKEN_FUTURES",
                sensor_family=SensorFamily.MECHANICAL_FUNDING,
                native_instrument_id="PI_XBTUSD",
                request_fingerprint="fp-1",
                requested_start=NOW,
                requested_end=NOW.replace(hour=1),
                row_count=0,
                retrieved_at=NOW,
                adapter_version="0.1.0",
            )

    def test_empty_valid_must_be_explicit(self) -> None:
        batch = FetchBatch(
            provider_id="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            native_instrument_id="PI_XBTUSD",
            request_fingerprint="fp-1",
            requested_start=NOW,
            requested_end=NOW.replace(hour=1),
            row_count=0,
            quality_flags=["EMPTY_VALID"],
            retrieved_at=NOW,
            adapter_version="0.1.0",
        )
        assert batch.row_count == 0
        assert "EMPTY_VALID" in [f.value for f in batch.quality_flags]

    def test_complete_batch_cannot_carry_next_token(self) -> None:
        with pytest.raises(ValidationError):
            FetchBatch(
                provider_id="KRAKEN_FUTURES",
                sensor_family=SensorFamily.MECHANICAL_FUNDING,
                native_instrument_id="PI_XBTUSD",
                request_fingerprint="fp-1",
                requested_start=NOW,
                requested_end=NOW.replace(hour=1),
                row_count=1,
                is_complete=True,
                next_resume_token=ResumeToken(mode=PaginationMode.CURSOR),
                retrieved_at=NOW,
                adapter_version="0.1.0",
            )


class TestResumeTokenRoundtrip:
    def test_roundtrip_is_deterministic(self) -> None:
        token = ResumeToken(
            mode=PaginationMode.CURSOR,
            provider_cursor="12345",
            page_number=3,
            last_timestamp=NOW,
            last_native_id="tid-9",
            provider_native_state={"since": "1000"},
        )
        rebuilt = ResumeToken.model_validate_json(token.model_dump_json())
        assert rebuilt == token

    def test_serialized_form_is_stable(self) -> None:
        token = ResumeToken(
            mode=PaginationMode.TIME_RANGE, last_timestamp=NOW
        )
        assert token.model_dump_json() == ResumeToken.model_validate_json(
            token.model_dump_json()
        ).model_dump_json()
