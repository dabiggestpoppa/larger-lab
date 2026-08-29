"""MECHANICAL_BOOK_SNAPSHOT and MECHANICAL_BOOK_METRIC observations (02 §8-9).

Depth semantics are source-specific: raw level counts are never compared across
venues as if equivalent.  A snapshot must always carry a non-empty
`source_depth_definition` (B1-T15).  If a provider exposes only aggregate book
analytics, use `MechanicalBookMetric`, never a fake snapshot (B1-T16:
`methodology_id` mandatory).
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..contracts.base import CanonicalObservationBase
from ..contracts.enums import BookMetricName, BookSide, SensorFamily


class PriceLevel(BaseModel):
    """One price/quantity level of a book snapshot (02 §8)."""

    model_config = ConfigDict(extra="forbid")

    price: Decimal
    quantity: Decimal
    quantity_unit: str = Field(min_length=1)


class MechanicalBookSnapshot(CanonicalObservationBase):
    """Raw or provider-aggregated order-book state."""

    best_bid: Decimal | None = None
    best_ask: Decimal | None = None
    bids: list[PriceLevel] | None = None
    asks: list[PriceLevel] | None = None
    provider_level_count: int | None = None
    source_depth_definition: str = Field(min_length=1)
    is_full_depth: bool
    sequence_id: str | None = None

    @model_validator(mode="after")
    def _pin_sensor_family(self) -> MechanicalBookSnapshot:
        if self.sensor_family is not SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            raise ValueError(
                f"sensor_family={self.sensor_family.value!r} does not match "
                "MechanicalBookSnapshot; expected MECHANICAL_BOOK_SNAPSHOT"
            )
        return self

    @model_validator(mode="after")
    def _depth_definition_nonempty(self) -> MechanicalBookSnapshot:
        if not self.source_depth_definition.strip():
            raise ValueError("source_depth_definition must be non-empty (B1-T15)")
        return self


class MechanicalBookMetric(CanonicalObservationBase):
    """Economically normalized book measurement (02 §9).

    Provider-native analytics and locally reconstructed metrics must carry
    different `methodology_id` values.
    """

    metric_name: BookMetricName
    metric_value: Decimal
    metric_unit: str = Field(min_length=1)
    side: BookSide = BookSide.NONE
    distance_bps: Decimal | None = None
    trade_notional_usd: Decimal | None = None
    methodology_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def _pin_sensor_family(self) -> MechanicalBookMetric:
        if self.sensor_family is not SensorFamily.MECHANICAL_BOOK_METRIC:
            raise ValueError(
                f"sensor_family={self.sensor_family.value!r} does not match "
                "MechanicalBookMetric; expected MECHANICAL_BOOK_METRIC"
            )
        return self

    @model_validator(mode="after")
    def _methodology_required(self) -> MechanicalBookMetric:
        if not self.methodology_id.strip():
            raise ValueError("methodology_id required for book metrics (B1-T16)")
        if not self.methodology_version:
            raise ValueError(
                "methodology_version required for book metrics (B1-T61)"
            )
        return self
