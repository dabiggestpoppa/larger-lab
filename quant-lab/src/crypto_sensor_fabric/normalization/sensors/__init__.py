"""Checkpoint-local public API of the Bloc 5 sensor normalizers.

The ``normalization/sensors/`` namespace (bloc_05/03 section 2 and section 18;
``BLOC_05_I10D1_DECISION_PACKAGE.md`` section 9.1) grows checkpoint by
checkpoint, and Wave 1 brings it to the full sensor set:

* ``side_maps``   -- I10 provider-neutral source-side evidence and the one
  declared Binance USD-M ``isBuyerMaker`` rule;
* ``admission``   -- Wave 1 shared semantic-admission ladder and derived-amount
  constructors, shared by I12-I15 and owned here;
* ``trade``       -- I10 trade record and ``normalize_trade``;
* ``liquidation`` -- I11 liquidation record and ``normalize_liquidation``;
* ``oi``          -- I12 open-interest record and ``normalize_open_interest``;
* ``funding``     -- I13 funding record and ``normalize_funding``;
* ``book``        -- I14 book snapshot + book metric and their normalizers;
* ``positioning`` -- I15 positioning record and ``normalize_positioning``;
* ``basis``       -- I15 basis record and ``normalize_basis``.

Three boundaries this package deliberately keeps:

**The ratified root API is untouched.**  ``crypto_sensor_fabric.normalization``
keeps its 24 I01 symbols and does NOT re-export anything from here, so the sensor
surface is reachable only by its explicit path.  That is what keeps the I01
scope audit's absolute module and symbol measurements honest.

**The composite envelope stays unexported.**  ``T1ObservationEnvelope`` is not a
name this package offers: the frozen full envelope also carries
identity/methodology/replay fields owned by other checkpoints, so exposing the
name here would let a consumer mistake a partial record for the finished contract.
Each family offers its own record that EXTENDS the accepted base.

**No family is forced into another family's union.**  Trade and liquidation are
not merged with OI, funding, books, positioning or basis: each new family has its
own input, its own record and its own normalizer, and none of them widens
``TradeObservationInput``.  Cross-family union is a separate contract review.

Only the symbols below are public contract for this package.  No network, no wall
clock, no filesystem, no provider package import: evidence in, answer out.
"""

from __future__ import annotations

from .side_maps import (
    BINANCE_IS_BUYER_MAKER_METHODOLOGY_ID,
    BINANCE_PROVIDER_ID,
    ProvisionalSideMapping,
    SideEvidence,
    SideEvidenceKind,
    SideMappingStatus,
    UnsupportedSideMappingError,
    admit_aggressor_side,
    apply_side_map,
    binance_side_from_is_buyer_maker,
    require_side_mapping,
    resolve_side_mapping,
)
from .admission import (
    SensorAdmissionRefusal,
    SensorFieldAdmission,
    admit_sensor_field,
    amount_from_conversion,
    blocked_amount,
    canonical_flags,
)
from .liquidation import (
    LiquidationAdmissionRefusal,
    LiquidationAggregationScope,
    LiquidationCanonicalField,
    LiquidationObservationInput,
    LiquidationPositionSide,
    LiquidationSideAdmission,
    LiquidationZeroIntervalState,
    T1LiquidationRecord,
    normalize_liquidation,
)
from .trade import (
    I04B_METHODOLOGY_ID,
    I08_UNITS_METHODOLOGY_ID,
    DerivedAmount,
    T1TradeRecord,
    TradeObservationInput,
    normalize_trade,
)
from .oi import (
    OI_CONTRACTS_METHODOLOGY_ID,
    OI_USD_PASSTHROUGH_METHODOLOGY_ID,
    OpenInterestAggregationScope,
    OpenInterestNativeUnit,
    OpenInterestObservationInput,
    OpenInterestSnapshotScope,
    T1OpenInterestRecord,
    normalize_open_interest,
)
from .funding import (
    FUNDING_EQUIV_METHODOLOGY_ID,
    FundingObservationInput,
    FundingRateKind,
    FundingRateUnit,
    T1FundingRecord,
    normalize_funding,
)
from .book import (
    BookLevel,
    BookLevelInput,
    BookMetricObservationInput,
    BookMetricSource,
    BookQuantityUnit,
    BookSequenceStatus,
    BookSide,
    BookSnapshotObservationInput,
    BookUpdateSemantics,
    T1BookMetricRecord,
    T1BookSnapshotRecord,
    classify_sequence,
    normalize_book_metric,
    normalize_book_snapshot,
)
from .positioning import (
    PositioningMetricType,
    PositioningObservationInput,
    T1PositioningRecord,
    normalize_positioning,
)
from .basis import (
    BasisObservationInput,
    BasisReferenceRefusal,
    BasisUnit,
    T1BasisRecord,
    normalize_basis,
)

__all__ = [
    # side evidence + the one declared rule
    "BINANCE_IS_BUYER_MAKER_METHODOLOGY_ID",
    "BINANCE_PROVIDER_ID",
    "ProvisionalSideMapping",
    "SideEvidence",
    "SideEvidenceKind",
    "SideMappingStatus",
    "UnsupportedSideMappingError",
    "admit_aggressor_side",
    "apply_side_map",
    "binance_side_from_is_buyer_maker",
    "require_side_mapping",
    "resolve_side_mapping",
    # shared Wave 1 admission surface
    "SensorAdmissionRefusal",
    "SensorFieldAdmission",
    "admit_sensor_field",
    "amount_from_conversion",
    "blocked_amount",
    "canonical_flags",
    # liquidation normalization (B5-I11 + the B5-I11F1 admission repair)
    "LiquidationAdmissionRefusal",
    "LiquidationAggregationScope",
    "LiquidationCanonicalField",
    "LiquidationObservationInput",
    "LiquidationPositionSide",
    "LiquidationSideAdmission",
    "LiquidationZeroIntervalState",
    "T1LiquidationRecord",
    "normalize_liquidation",
    # trade normalization
    "I04B_METHODOLOGY_ID",
    "I08_UNITS_METHODOLOGY_ID",
    "DerivedAmount",
    "T1TradeRecord",
    "TradeObservationInput",
    "normalize_trade",
    # open interest (B5-I12)
    "OI_CONTRACTS_METHODOLOGY_ID",
    "OI_USD_PASSTHROUGH_METHODOLOGY_ID",
    "OpenInterestAggregationScope",
    "OpenInterestNativeUnit",
    "OpenInterestObservationInput",
    "OpenInterestSnapshotScope",
    "T1OpenInterestRecord",
    "normalize_open_interest",
    # funding (B5-I13)
    "FUNDING_EQUIV_METHODOLOGY_ID",
    "FundingObservationInput",
    "FundingRateKind",
    "FundingRateUnit",
    "T1FundingRecord",
    "normalize_funding",
    # books and book metrics (B5-I14)
    "BookLevel",
    "BookLevelInput",
    "BookMetricObservationInput",
    "BookMetricSource",
    "BookQuantityUnit",
    "BookSequenceStatus",
    "BookSide",
    "BookSnapshotObservationInput",
    "BookUpdateSemantics",
    "T1BookMetricRecord",
    "T1BookSnapshotRecord",
    "classify_sequence",
    "normalize_book_metric",
    "normalize_book_snapshot",
    # positioning and basis (B5-I15)
    "PositioningMetricType",
    "PositioningObservationInput",
    "T1PositioningRecord",
    "normalize_positioning",
    "BasisObservationInput",
    "BasisReferenceRefusal",
    "BasisUnit",
    "T1BasisRecord",
    "normalize_basis",
]
