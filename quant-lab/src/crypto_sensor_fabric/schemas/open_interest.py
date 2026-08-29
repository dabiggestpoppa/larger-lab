"""MECHANICAL_OPEN_INTEREST canonical observation (02 §6).

Native value preservation rule (B1-T12): the provider-native `oi_native` and
`native_unit` are always retained; normalized values (`oi_base` / `oi_quote` /
`oi_usd`) are additive fields.

If a conversion is not defensible, normalized fields stay null and
`UNIT_NORMALIZATION_UNAVAILABLE` is flagged (B1-T13).  Any non-native
normalization must carry `normalization_method` plus base
`normalization_version` and `methodology_version` (B1-T61).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import model_validator

from ..contracts.base import CanonicalObservationBase
from ..contracts.enums import NativeOIUnit, SensorFamily


class MechanicalOpenInterest(CanonicalObservationBase):
    """A venue/instrument open-interest observation."""

    oi_native: Decimal
    native_unit: NativeOIUnit
    oi_base: Decimal | None = None
    oi_quote: Decimal | None = None
    oi_usd: Decimal | None = None
    mark_price_used: Decimal | None = None
    index_price_used: Decimal | None = None
    conversion_timestamp: datetime | None = None
    normalization_method: str | None = None

    @model_validator(mode="after")
    def _pin_sensor_family(self) -> MechanicalOpenInterest:
        self.sensor_family = SensorFamily.MECHANICAL_OPEN_INTEREST
        return self

    @model_validator(mode="after")
    def _require_normalization_versions(self) -> MechanicalOpenInterest:
        normalized = [v for v in (self.oi_base, self.oi_quote, self.oi_usd) if v is not None]
        if normalized:
            if not self.normalization_method:
                raise ValueError(
                    "normalization_method required when normalized OI fields are present"
                )
            if not self.normalization_version:
                raise ValueError(
                    "normalization_version required when normalized OI fields are present (B1-T61)"
                )
            if not self.methodology_version:
                raise ValueError(
                    "methodology_version required when normalized OI fields are present (B1-T61)"
                )
        return self
