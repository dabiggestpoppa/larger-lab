"""SENSOR-B3-I07B — OKX v5 error-envelope -> typed failure mapping tests."""

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
from crypto_sensor_fabric.providers.okx import (
    is_okx_error_body,
    is_okx_success,
    map_okx_error,
)

SENSOR = SensorFamily.MECHANICAL_TRADE
PROVIDER = "OKX_SWAP"


def _map(body, status=400):
    return map_okx_error(PROVIDER, SENSOR, body, status)


class TestEnvelopeClassification:
    def test_success_envelope(self) -> None:
        assert is_okx_success({"code": "0", "msg": "", "data": []}) is True
        assert is_okx_error_body({"code": "0", "msg": "", "data": []}) is False

    def test_error_envelope_nonzero_code(self) -> None:
        assert is_okx_error_body({"code": "51001", "msg": "x", "data": []}) is True

    def test_http_2xx_with_nonzero_code_is_still_error(self) -> None:
        # a nonzero code on HTTP 200 must be an error, never EMPTY_VALID
        err = _map({"code": "51001", "msg": "Instrument ID does not exist", "data": []}, status=200)
        assert isinstance(err, InvalidInstrument)


class TestCodeFamilyMapping:
    def test_rate_limit_codes(self) -> None:
        for code in ("50011", "50012", "50110", "50111"):
            assert isinstance(_map({"code": code, "msg": "x", "data": []}, 200), RateLimited)

    def test_invalid_instrument_code(self) -> None:
        assert isinstance(
            _map({"code": "51001", "msg": "Instrument ID does not exist", "data": []}, 200),
            InvalidInstrument,
        )

    def test_auth_code(self) -> None:
        assert isinstance(
            _map({"code": "50113", "msg": "Please login", "data": []}, 200),
            AuthenticationRequired,
        )

    def test_unknown_code_is_semantic_error(self) -> None:
        assert isinstance(
            _map({"code": "99999", "msg": "some error", "data": []}, 200),
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
        err = _map({"code": "51001", "msg": "Instrument ID does not exist", "data": []}, 400)
        assert err.provider_id == PROVIDER
        assert err.sensor_family is SENSOR
        ctx = err.provider_native_context_redacted
        assert ctx["http_status"] == 400
        assert ctx["code"] == "51001"

    def test_nonzero_code_never_becomes_empty_valid(self) -> None:
        # provider error is a typed AcquisitionError, not an EMPTY_VALID batch
        err = _map({"code": "51001", "msg": "x", "data": []}, 400)
        assert not isinstance(err, (list, tuple, dict))
        assert hasattr(err, "failure_type")