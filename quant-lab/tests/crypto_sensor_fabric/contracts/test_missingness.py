"""Missingness / fail-closed tests (B1-T50 partly, B1-T51, B1-T52).

B1-T50 (no default zero) lives with the schema suite once schemas exist;
this module covers the structured missingness object and the
missingness-is-not-zero rules.
"""

from __future__ import annotations

import pytest
from crypto_sensor_fabric.contracts.base import (
    MissingObservation,
    is_numeric_zero_semantics,
    missing_reason_as_zero,
)
from crypto_sensor_fabric.contracts.enums import (
    MissingReason,
    SensorFamily,
)
from pydantic import ValidationError


def test_t51_missing_observation_requires_reason():
    with pytest.raises(ValidationError):
        MissingObservation.model_validate(
            {
                "sensor_family": SensorFamily.MECHANICAL_LIQUIDATION,
                "provider": "KRAKEN_FUTURES",
            }
        )


def test_t51_missing_observation_with_reason_validates():
    obs = MissingObservation.model_validate(
        {
            "sensor_family": SensorFamily.MECHANICAL_LIQUIDATION,
            "provider": "KRAKEN_FUTURES",
            "venue": "KRAKEN_FUTURES",
            "instrument_native": "PF_XBTUSD",
            "reason": MissingReason.OUTSIDE_PROVIDER_HISTORY,
        }
    )
    assert obs.reason is MissingReason.OUTSIDE_PROVIDER_HISTORY


def test_t52_not_supported_cannot_be_zero():
    with pytest.raises(ValueError, match="must not be interpreted as a numeric zero"):
        missing_reason_as_zero(MissingReason.NOT_SUPPORTED)


def test_t52_no_missing_reason_is_zero_semantics():
    for reason in MissingReason:
        assert is_numeric_zero_semantics(reason) is False


def test_t52_zero_conversion_raises_for_every_reason():
    for reason in MissingReason:
        with pytest.raises(ValueError):
            missing_reason_as_zero(reason)
