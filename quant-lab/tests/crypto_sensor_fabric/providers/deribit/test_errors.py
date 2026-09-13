"""SENSOR-B3-I08B — Deribit JSON-RPC error-envelope -> typed failure tests."""

from __future__ import annotations

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.errors import (
    AccessClassViolation,
    AuthenticationRequired,
    InvalidInstrument,
    ProviderSemanticError,
    ProviderUnavailable,
    RateLimited,
)
from crypto_sensor_fabric.providers.deribit import (
    deribit_error_code,
    is_deribit_error_body,
    map_deribit_error,
)

SENSOR = SensorFamily.MECHANICAL_TRADE
PROVIDER = "DERIBIT"


def _map(body, status=400):
    return map_deribit_error(PROVIDER, SENSOR, body, status)


class TestEnvelopeClassification:
    def test_success_envelope_not_error(self) -> None:
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"has_more": False, "trades": []},
        }
        assert is_deribit_error_body(body) is False
        assert deribit_error_code(body) is None

    def test_error_envelope_on_http_200_detected(self) -> None:
        body = {"jsonrpc": "2.0", "error": {"code": 40400, "message": "invalid instrument name"}}
        assert is_deribit_error_body(body) is True
        assert deribit_error_code(body) == 40400

    def test_http_200_with_error_is_still_error(self) -> None:
        # a JSON-RPC error on HTTP 200 must be an error, never EMPTY_VALID
        err = _map({"jsonrpc": "2.0", "error": {"code": 40400, "message": "x"}}, status=200)
        assert isinstance(err, InvalidInstrument)


class TestCodeFamilyMapping:
    def test_rate_limit_code(self) -> None:
        assert isinstance(_map({"jsonrpc": "2.0", "error": {"code": 10001, "message": "x"}}, 200), RateLimited)

    def test_invalid_instrument_code(self) -> None:
        assert isinstance(
            _map({"jsonrpc": "2.0", "error": {"code": 40400, "message": "invalid instrument name"}}, 200),
            InvalidInstrument,
        )

    def test_auth_codes(self) -> None:
        for code in (10000, 10002):
            assert isinstance(
                _map({"jsonrpc": "2.0", "error": {"code": code, "message": "x"}}, 200),
                AuthenticationRequired,
            ), code

    def test_endpoint_removed_is_semantic(self) -> None:
        assert isinstance(
            _map({"jsonrpc": "2.0", "error": {"code": -32601, "message": "method not found"}}, 200),
            ProviderSemanticError,
        )

    def test_invalid_request_code_is_semantic(self) -> None:
        assert isinstance(
            _map({"jsonrpc": "2.0", "error": {"code": -32602, "message": "invalid params"}}, 200),
            ProviderSemanticError,
        )

    def test_unknown_code_is_semantic_error(self) -> None:
        assert isinstance(
            _map({"jsonrpc": "2.0", "error": {"code": -32000, "message": "x"}}, 200),
            ProviderSemanticError,
        )


class TestHttpBandMapping:
    def test_429_rate_limited(self) -> None:
        assert isinstance(_map({}, 429), RateLimited)

    def test_403_access_class_violation(self) -> None:
        assert isinstance(_map({}, 403), AccessClassViolation)

    def test_500_provider_unavailable(self) -> None:
        assert isinstance(_map({}, 500), ProviderUnavailable)

    def test_400_semantic_error(self) -> None:
        assert isinstance(_map({}, 400), ProviderSemanticError)


class TestPreservesContext:
    def test_redacted_context_holds_code_and_status(self) -> None:
        err = _map({"jsonrpc": "2.0", "error": {"code": 40400, "message": "invalid instrument name"}}, 400)
        assert err.provider_id == PROVIDER
        assert err.sensor_family is SENSOR
        ctx = err.provider_native_context_redacted
        assert ctx["http_status"] == 400
        assert ctx["code"] == 40400

    def test_error_never_becomes_empty_valid(self) -> None:
        err = _map({"jsonrpc": "2.0", "error": {"code": 40400, "message": "x"}}, 400)
        assert not isinstance(err, (list, tuple, dict))
        assert hasattr(err, "failure_type")
