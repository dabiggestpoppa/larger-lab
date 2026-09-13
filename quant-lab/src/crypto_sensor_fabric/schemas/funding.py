"""MECHANICAL_FUNDING canonical observation (02 §7).

Native preservation rule (B1-T14): `funding_rate_8h_equivalent` and
`annualized_context` are derived fields and can never exist without
`funding_rate_native`; the native rate is never overwritten.  Derived funding
fields require `normalization_version` + `methodology_version` (B1-T61).
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import model_validator

from ..contracts.base import CanonicalObservationBase
from ..contracts.enums import FundingType, SensorFamily


class MechanicalFunding(CanonicalObservationBase):
    """A venue/instrument funding observation."""

    funding_rate_native: Decimal
    funding_interval_seconds: int | None = None
    funding_rate_8h_equivalent: Decimal | None = None
    annualized_context: Decimal | None = None
    predicted_or_realized: FundingType = FundingType.UNKNOWN

    @model_validator(mode="after")
    def _pin_sensor_family(self) -> MechanicalFunding:
        if self.sensor_family is not SensorFamily.MECHANICAL_FUNDING:
            raise ValueError(
                f"sensor_family={self.sensor_family.value!r} does not match "
                "MechanicalFunding; expected MECHANICAL_FUNDING"
            )
        return self

    @model_validator(mode="after")
    def _native_required_for_derived(self) -> MechanicalFunding:
        if self.funding_rate_8h_equivalent is not None and self.funding_rate_native is None:
            raise ValueError(
                "funding_rate_8h_equivalent cannot exist without funding_rate_native (B1-T14)"
            )
        derived_present = (
            self.funding_rate_8h_equivalent is not None or self.annualized_context is not None
        )
        if derived_present:
            if not self.normalization_version:
                raise ValueError(
                    "normalization_version required when derived funding fields present (B1-T61)"
                )
            if not self.methodology_version:
                raise ValueError(
                    "methodology_version required when derived funding fields present (B1-T61)"
                )
        return self
