"""MECHANICAL_BASIS canonical observation (02 §11).

Perpetual/futures basis or premium where provider semantics are clear.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import model_validator

from ..contracts.base import CanonicalObservationBase
from ..contracts.enums import ReferenceType, SensorFamily


class MechanicalBasis(CanonicalObservationBase):
    """A basis or premium observation."""

    basis_native: Decimal
    basis_bps: Decimal | None = None
    reference_price: Decimal | None = None
    reference_type: ReferenceType = ReferenceType.OTHER
    tenor_seconds: int | None = None

    @model_validator(mode="after")
    def _pin_sensor_family(self) -> MechanicalBasis:
        if self.sensor_family is not SensorFamily.MECHANICAL_BASIS:
            raise ValueError(
                f"sensor_family={self.sensor_family.value!r} does not match "
                "MechanicalBasis; expected MECHANICAL_BASIS"
            )
        return self
