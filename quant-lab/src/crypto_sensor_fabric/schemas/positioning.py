"""MECHANICAL_POSITIONING canonical observation (02 §10).

Positioning observations are contextual and never substitutes for OI.
Different populations (global, top-trader, taker, user) are never equated:
`population_definition` is mandatory (B1-T17).
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import Field, model_validator

from ..contracts.base import CanonicalObservationBase
from ..contracts.enums import PositioningMetric, SensorFamily


class MechanicalPositioning(CanonicalObservationBase):
    """A public long/short ratio or positioning observation."""

    positioning_metric: PositioningMetric
    long_value: Decimal | None = None
    short_value: Decimal | None = None
    ratio_value: Decimal | None = None
    population_definition: str = Field(min_length=1)

    @model_validator(mode="after")
    def _pin_sensor_family(self) -> MechanicalPositioning:
        self.sensor_family = SensorFamily.MECHANICAL_POSITIONING
        return self

    @model_validator(mode="after")
    def _population_required(self) -> MechanicalPositioning:
        if not self.population_definition.strip():
            raise ValueError("population_definition required (B1-T17)")
        return self
