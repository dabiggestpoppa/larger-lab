"""SENSOR-B3-I02 — free-only access gate + request fingerprint/hash tests.

The access gate must run BEFORE any transport call, hard-block paid/trading/
wallet/stake/transaction classes, and FAIL CLOSED on uncertainty.  Fingerprint
tests prove determinism and semantic sensitivity; payload hash tests prove
integrity determinism.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from crypto_sensor_fabric.contracts.access import FreeOnlyPolicy
from crypto_sensor_fabric.contracts.enums import AccessClass, SensorFamily
from crypto_sensor_fabric.providers.base.access import (
    assert_free_only_access,
    evaluate_access,
)
from crypto_sensor_fabric.providers.base.enums import (
    AdapterAuthMode,
    FetchPurpose,
)
from crypto_sensor_fabric.providers.base.errors import AccessClassViolation
from crypto_sensor_fabric.providers.base.fingerprint import (
    fingerprint_request,
    payload_hash,
)
from crypto_sensor_fabric.providers.base.models import FetchRequest

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def free_policy() -> FreeOnlyPolicy:
    return FreeOnlyPolicy(
        access_class=AccessClass.FREE_AUTOMATED,
        cost_usd_required=0,
        payment_method_required=False,
        staking_required=False,
        transaction_required=False,
    )


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


class TestAccessGateFreeOnly:
    def test_free_policy_passes(self) -> None:
        decision = evaluate_access(
            "KRAKEN_FUTURES", free_policy(), AdapterAuthMode.NO_AUTH
        )
        assert decision.allowed
        assert not decision.violations

    def test_free_api_key_allowed(self) -> None:
        decision = evaluate_access(
            "COINALYZE", free_policy(), AdapterAuthMode.FREE_API_KEY
        )
        assert decision.allowed

    def test_optional_public_key_allowed(self) -> None:
        decision = evaluate_access(
            "GATE_FUTURES", free_policy(), AdapterAuthMode.OPTIONAL_PUBLIC_KEY
        )
        assert decision.allowed

    def test_assert_passes_without_raising(self) -> None:
        assert_free_only_access(
            "KRAKEN_FUTURES", free_policy(), AdapterAuthMode.NO_AUTH
        )


class TestAccessGateHardBlocks:
    def test_paid_key_blocked(self) -> None:
        decision = evaluate_access(
            "X", free_policy(), AdapterAuthMode.PAID_KEY
        )
        assert not decision.allowed
        assert any("auth:" in v for v in decision.violations)

    def test_trading_key_blocked(self) -> None:
        decision = evaluate_access(
            "X", free_policy(), AdapterAuthMode.TRADING_KEY
        )
        assert not decision.allowed

    @pytest.mark.parametrize(
        "mode",
        [
            AdapterAuthMode.WITHDRAWAL_PERMISSION,
            AdapterAuthMode.SIGNING_SECRET,
            AdapterAuthMode.WALLET_SIGNATURE,
            AdapterAuthMode.STAKING_UNLOCK,
            AdapterAuthMode.TRANSACTION_REQUIRED,
        ],
    )
    def test_credential_classes_blocked(self, mode: AdapterAuthMode) -> None:
        decision = evaluate_access("X", free_policy(), mode)
        assert not decision.allowed

    def test_unverified_fails_closed(self) -> None:
        decision = evaluate_access(
            "X", free_policy(), AdapterAuthMode.UNVERIFIED
        )
        assert not decision.allowed

    def test_assert_raises_typed_error(self) -> None:
        with pytest.raises(AccessClassViolation):
            assert_free_only_access(
                "X", free_policy(), AdapterAuthMode.TRADING_KEY
            )


class TestAccessGatePolicy:
    def test_payment_method_required_blocked(self) -> None:
        policy = free_policy().model_copy(update={"payment_method_required": True})
        decision = evaluate_access("X", policy, AdapterAuthMode.NO_AUTH)
        assert not decision.allowed
        assert any("payment_method_required" in v for v in decision.violations)

    def test_staking_required_blocked(self) -> None:
        policy = free_policy().model_copy(update={"staking_required": True})
        decision = evaluate_access("X", policy, AdapterAuthMode.NO_AUTH)
        assert not decision.allowed

    def test_transaction_required_blocked(self) -> None:
        policy = free_policy().model_copy(update={"transaction_required": True})
        decision = evaluate_access("X", policy, AdapterAuthMode.NO_AUTH)
        assert not decision.allowed

    def test_cost_required_blocked(self) -> None:
        policy = free_policy().model_copy(update={"cost_usd_required": 9})
        decision = evaluate_access("X", policy, AdapterAuthMode.NO_AUTH)
        assert not decision.allowed

    def test_unknown_access_class_fails_closed(self) -> None:
        policy = free_policy().model_copy(update={"access_class": AccessClass.UNVERIFIED})
        decision = evaluate_access("X", policy, AdapterAuthMode.NO_AUTH)
        assert not decision.allowed


class TestFingerprintDeterminism:
    def test_identical_requests_identical_fingerprint(self) -> None:
        a = fingerprint_request(make_request(), "/analytics")
        b = fingerprint_request(make_request(), "/analytics")
        assert a == b

    def test_material_semantic_change_differs(self) -> None:
        base = fingerprint_request(make_request(), "/analytics")
        changed_sensor = fingerprint_request(
            make_request(sensor_family=SensorFamily.MECHANICAL_LIQUIDATION),
            "/analytics",
        )
        changed_window = fingerprint_request(
            make_request(
                start_time=NOW.replace(hour=3), end_time=NOW.replace(hour=4)
            ),
            "/analytics",
        )
        changed_instrument = fingerprint_request(
            make_request(native_instrument_id="PI_ETHUSD"),
            "/analytics",
        )
        changed_family = fingerprint_request(make_request(), "/derivatives/api/v3")
        changed_version = fingerprint_request(
            make_request(adapter_semantic_version="0.2.0"), "/analytics"
        )
        assert changed_sensor != base
        assert changed_window != base
        assert changed_instrument != base
        assert changed_family != base
        assert changed_version != base

    def test_serialization_noise_is_inert(self) -> None:
        a = fingerprint_request(
            make_request(),
            "/analytics",
            page_or_cursor_inputs={"since": "1000", "limit": 100},
        )
        b = fingerprint_request(
            make_request(),
            "/analytics",
            page_or_cursor_inputs={"limit": 100, "since": "1000"},
        )
        assert a == b

    def test_cursor_change_alters_fingerprint(self) -> None:
        a = fingerprint_request(
            make_request(), "/analytics", page_or_cursor_inputs={"cursor": "x"}
        )
        b = fingerprint_request(
            make_request(), "/analytics", page_or_cursor_inputs={"cursor": "y"}
        )
        assert a != b


class TestPayloadHash:
    def test_same_bytes_same_hash(self) -> None:
        assert payload_hash(b'{"a":1}') == payload_hash(b'{"a":1}')

    def test_different_bytes_different_hash(self) -> None:
        assert payload_hash(b'{"a":1}') != payload_hash(b'{"a":2}')

    def test_str_and_bytes_consistent(self) -> None:
        assert payload_hash('{"a":1}') == payload_hash(b'{"a":1}')
