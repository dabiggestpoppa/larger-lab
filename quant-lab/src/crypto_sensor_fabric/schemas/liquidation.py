"""MECHANICAL_LIQUIDATION canonical observation (02 §5).

Deliberately supports three distinct shapes:

    TRADE_LEVEL        individual liquidation event
    INTERVAL_AGGREGATE long/short interval aggregate
    TOTAL_AGGREGATE    provider-level total liquidation volume

Non-equivalence rule (B1-T11): trade-level records are never numerically merged
with interval aggregates at T1; pooling happens only at T2 under explicit
eligibility rules.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import model_validator

from ..contracts.base import CanonicalObservationBase
from ..contracts.enums import (
    LiquidationEventShape,
    LiquidationRole,
    LiquidationSide,
    SensorFamily,
)


class MechanicalLiquidation(CanonicalObservationBase):
    """A provider-observed forced-liquidation event or aggregate."""

    event_shape: LiquidationEventShape
    liquidation_side: LiquidationSide = LiquidationSide.UNKNOWN
    liquidation_role: LiquidationRole = LiquidationRole.UNKNOWN
    price_native: Decimal | None = None
    quantity_native: Decimal | None = None
    quantity_unit: str | None = None
    liquidation_quote_native: Decimal | None = None
    liquidation_usd: Decimal | None = None
    liquidation_count: int | None = None
    source_long_liq_native: Decimal | None = None
    source_short_liq_native: Decimal | None = None
    source_long_liq_usd: Decimal | None = None
    source_short_liq_usd: Decimal | None = None

    @model_validator(mode="after")
    def _pin_sensor_family(self) -> MechanicalLiquidation:
        self.sensor_family = SensorFamily.MECHANICAL_LIQUIDATION
        return self
