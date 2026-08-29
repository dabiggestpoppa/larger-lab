"""MECHANICAL_TRADE canonical observation (02 §4).

A public venue trade or aggregated trade observation.  Derived concepts such
as CVD, large-trade classification or imbalance are T2 features and never
appear in this schema.

Side rule (B1-T10): a provider's maker/taker boolean is not trusted until a
provider fixture test proves the mapping; untrusted records preserve
`aggressor_side=UNKNOWN` rather than guess.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import Field, model_validator

from ..contracts.base import CanonicalObservationBase
from ..contracts.enums import AggregationType, AggressorSide, SensorFamily


class MechanicalTrade(CanonicalObservationBase):
    """A single or provider-aggregated public trade observation."""

    trade_id: str | None = None
    price_native: Decimal
    quantity_native: Decimal
    quantity_unit: str = Field(min_length=1)
    quote_notional_native: Decimal | None = None
    quote_notional_usd: Decimal | None = None
    aggressor_side: AggressorSide = AggressorSide.UNKNOWN
    maker_side: AggressorSide = AggressorSide.UNKNOWN
    aggregation_type: AggregationType = AggregationType.INDIVIDUAL
    source_trade_count: int | None = None

    @model_validator(mode="after")
    def _pin_sensor_family(self) -> MechanicalTrade:
        self.sensor_family = SensorFamily.MECHANICAL_TRADE
        return self
