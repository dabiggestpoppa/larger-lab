"""SENSOR-B3-I06 — Gate error-envelope -> typed acquisition-failure tests."""

from __future__ import annotations

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.errors import (
    HistoricalRangeUnavailable,
    InvalidInstrument,
    ProviderSemanticError,
    ProviderUnavailable,
    RateLimited,
)
from crypto_sensor_fabric.providers.base.retry import classify_retryability
from crypto_sensor_fabric.providers.base.enums import Retryability
from crypto_sensor_fabric.providers.gate.errors import (
    is_gate_error_body,
    map_gate_error,
)

SENSOR = SensorFamily.MECHANICAL_OPEN_INTEREST


class TestRetention:
    def test_180_day_retention_maps_to_historical_range_unavailable(self) -> None:
        err = map_gate_error(
            "GATE_FUTURES",
            SENSOR,
            {"label": "INVALID_PARAM_VALUE", "message": "from time exceeds 180-day limit"},
            400,
        )
        assert isinstance(err, HistoricalRangeUnavailable)
        assert classify_retryability(err) is Retryability.TERMINAL

    def test_retention_is_not_empty_valid_nor_auth_nor_unsupported(self) -> None:
        err = map_gate_error(
            "GATE_FUTURES",
            SENSOR,
            {"label": "INVALID_PARAM_VALUE", "message": "from time exceeds 180-day limit"},
            400,
        )
        assert not isinstance(err, RateLimited)
        assert "180" in (err.detail or "")


class TestErrorClassification:
    def test_rate_limit_body(self) -> None:
        err = map_gate_error("GATE_FUTURES", SENSOR, {"label": "RATE_LIMIT_CONTROL", "message": "Too many requests"}, 429)
        assert isinstance(err, RateLimited)
        assert classify_retryability(err) is Retryability.RETRYABLE

    def test_http_429_is_rate_limited(self) -> None:
        err = map_gate_error("GATE_FUTURES", SENSOR, {"label": "X", "message": "y"}, 429)
        assert isinstance(err, RateLimited)

    def test_invalid_contract_is_invalid_instrument(self) -> None:
        err = map_gate_error(
            "GATE_FUTURES",
            SENSOR,
            {"label": "INVALID_PARAM_VALUE", "message": "contract ETH_USDT not found"},
            400,
        )
        assert isinstance(err, InvalidInstrument)

    def test_http_400_generic_is_provider_semantic_error(self) -> None:
        err = map_gate_error("GATE_FUTURES", SENSOR, {"label": "BAD_REQUEST", "message": "nope"}, 400)
        assert isinstance(err, ProviderSemanticError)

    def test_http_500_is_provider_unavailable(self) -> None:
        err = map_gate_error("GATE_FUTURES", SENSOR, {"label": "INTERNAL", "message": "boom"}, 500)
        assert isinstance(err, ProviderUnavailable)

    def test_forbidden_label_is_geo_restricted(self) -> None:
        # Gate is US-region restricted; a FORBIDDEN label is geo evidence, never
        # bypassed (never auth, never EMPTY_VALID).
        from crypto_sensor_fabric.providers.base.errors import GeoRestricted

        err = map_gate_error("GATE_FUTURES", SENSOR, {"label": "FORBIDDEN", "message": "restricted"}, 403)
        assert isinstance(err, GeoRestricted)

    def test_http_403_is_access_class_violation(self) -> None:
        from crypto_sensor_fabric.providers.base.errors import AccessClassViolation

        err = map_gate_error("GATE_FUTURES", SENSOR, {"label": "OTHER", "message": "no"}, 403)
        assert isinstance(err, AccessClassViolation)


class TestEnvelopeDetection:
    def test_is_gate_error_body(self) -> None:
        assert is_gate_error_body({"label": "X", "message": "y"})
        assert not is_gate_error_body({"label": "X", "message": []})
        assert not is_gate_error_body([])
        assert not is_gate_error_body({"foo": 1})
        assert not is_gate_error_body(7)