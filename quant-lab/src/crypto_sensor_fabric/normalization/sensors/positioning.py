"""SENSOR-B5-I15a - provider-neutral positioning-ratio normalizer.

The I15 realization of ``bloc_05/04`` section 8.  Positioning ratios are
HETEROGENEOUS: an account long/short ratio, a top-trader account ratio, a
top-trader position ratio, a taker buy/sell ratio and a provider aggregate are
five different economic measurements of five different populations.

Therefore there is no generic ``long_short_ratio`` field here.  Every record must
state:

    positioning_metric_type        which of the frozen five it is
    numerator_definition           what the top of the ratio counts
    denominator_definition         what the bottom counts
    population_scope               WHICH population (accounts? top N? notional?)
    value_native / value_unit      the number and its dimension
    interval_semantics             carried by the time envelope

``population_scope`` is required and non-blank, which is what makes "unrelated
long/short populations" structurally non-interchangeable: two records can only be
compared when their type, definitions and scope all agree, and a provider that
does not declare its population cannot produce a comparable record at all.

A provider-defined ratio keeps its own name and can claim no canonical family:
``PROVIDER_DEFINED_RATIO`` requires a methodology reference and forbids a
``canonical_metric_family``, because mapping an undocumented aggregate onto a
fabric family would be an unauthorized semantic equivalence.

No conversion is performed.  A ratio is dimensionless evidence; nothing here
invents a USD value, an account count or a notional.

No network, no wall clock, no id generation, no filesystem.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import Field, model_validator

from ...contracts.enums import SemanticEquivalence, SensorFamily
from ...storage import CoverageState, RevisionState
from ..enums import (
    AvailabilityBasis,
    IntervalTimeConvention,
    LineageState,
    NormalizationQualityFlag,
    NormalizationStatus,
    QualityDimensionState,
    TimestampPrecision,
)
from ..models import (
    NativeQuantity,
    NormalizationModelBase,
    ObservationTimeEnvelope,
    OpaqueIdentifier,
    T1BaseEnvelope,
    T1LineageRef,
    T1Quality,
    T1VersionContext,
)
from .admission import canonical_flags

__all__ = [
    "PositioningMetricType",
    "PositioningObservationInput",
    "T1PositioningRecord",
    "normalize_positioning",
]


class PositioningMetricType(str, Enum):
    """The frozen five initial metric types (04 section 8)."""

    ACCOUNT_LONG_SHORT_RATIO = "ACCOUNT_LONG_SHORT_RATIO"
    TOP_TRADER_ACCOUNT_RATIO = "TOP_TRADER_ACCOUNT_RATIO"
    TOP_TRADER_POSITION_RATIO = "TOP_TRADER_POSITION_RATIO"
    TAKER_BUY_SELL_RATIO = "TAKER_BUY_SELL_RATIO"
    PROVIDER_DEFINED_RATIO = "PROVIDER_DEFINED_RATIO"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


#: The two dimensionless unit readings a ratio may carry.
_RATIO_UNITS = frozenset({"RATIO", "PERCENT"})


class PositioningObservationInput(NormalizationModelBase):
    """Transport-neutral positioning observation, before any canonical claim.

    ``numerator_definition`` / ``denominator_definition`` / ``population_scope``
    are all required and all non-blank.  A ratio whose population is undeclared is
    not comparable to anything, so the input refuses it rather than letting the
    record guess.
    """

    provider: OpaqueIdentifier
    venue: OpaqueIdentifier
    native_instrument: OpaqueIdentifier
    provider_instrument_id: OpaqueIdentifier | None = None
    contract_instance_id: OpaqueIdentifier | None = None

    native_positioning_id: OpaqueIdentifier | None = None
    native_sequence_id: OpaqueIdentifier | None = None

    metric_type: PositioningMetricType
    numerator_definition: OpaqueIdentifier
    denominator_definition: OpaqueIdentifier
    population_scope: OpaqueIdentifier
    population_size: int | None = Field(default=None, ge=1)

    value_native: Decimal
    value_unit: OpaqueIdentifier
    provider_metric_name: OpaqueIdentifier | None = None
    provider_methodology_ref: OpaqueIdentifier | None = None
    semantic_equivalence: SemanticEquivalence = SemanticEquivalence.NORMALIZABLE_COMPARABLE

    event_at: datetime | None = None
    observed_at: datetime | None = None
    ingested_at: datetime | None = None
    market_available_at: datetime | None = None
    availability_basis: AvailabilityBasis | None = None
    source_precision: TimestampPrecision | None = None
    interval_start_at: datetime | None = None
    interval_end_at: datetime | None = None
    interval_closed: bool | None = None
    interval_time_convention: IntervalTimeConvention | None = None

    source_revision_id: OpaqueIdentifier
    source_revision_state: RevisionState
    source_coverage_state: CoverageState
    normalization_generation: OpaqueIdentifier

    raw_projection_refs: tuple[OpaqueIdentifier, ...] = Field(min_length=1)
    acquisition_refs: tuple[OpaqueIdentifier, ...] = Field(min_length=1)
    evidence_blob_hashes: tuple[str, ...] = Field(min_length=1)
    code_version: OpaqueIdentifier
    config_version: OpaqueIdentifier

    @model_validator(mode="after")
    def _unit_law(self) -> PositioningObservationInput:
        if self.value_unit not in _RATIO_UNITS:
            raise ValueError(
                f"value_unit={self.value_unit!r} is not a ratio dimension: a "
                "positioning ratio is dimensionless evidence, and a quantity or "
                "USD reading here would be a different measurement entirely "
                "(04 section 8)"
            )
        return self

    @model_validator(mode="after")
    def _provider_defined_law(self) -> PositioningObservationInput:
        if self.metric_type is PositioningMetricType.PROVIDER_DEFINED_RATIO:
            if self.provider_methodology_ref is None:
                raise ValueError(
                    "PROVIDER_DEFINED_RATIO requires provider_methodology_ref: an "
                    "undocumented aggregate cannot be normalized, only quoted"
                )
        if not self.value_native.is_finite():
            raise ValueError("value_native must be finite")
        return self

    @model_validator(mode="after")
    def _unique_refs(self) -> PositioningObservationInput:
        for name in ("raw_projection_refs", "acquisition_refs", "evidence_blob_hashes"):
            values = getattr(self, name)
            if len(set(values)) != len(values):
                raise ValueError(f"{name} contains duplicate references")
        return self


class T1PositioningRecord(T1BaseEnvelope):
    """Positioning T1 record (04 section 8).

    The population triple (type, numerator, denominator) plus ``population_scope``
    is what a consumer must match before comparing two records.  ``T1PositioningRecord``
    offers no combined or "overall" ratio field, because a combined ratio would be
    exactly the cross-population equivalence the frozen rule forbids.
    """

    positioning_metric_type: PositioningMetricType
    numerator_definition: OpaqueIdentifier
    denominator_definition: OpaqueIdentifier
    population_scope: OpaqueIdentifier
    population_size: int | None = Field(default=None, ge=1)

    value_native: Decimal
    value_unit: OpaqueIdentifier
    provider_metric_name: OpaqueIdentifier | None = None
    provider_methodology_ref: OpaqueIdentifier | None = None
    canonical_metric_family: OpaqueIdentifier | None = None
    semantic_equivalence: SemanticEquivalence

    @model_validator(mode="after")
    def _sensor_family_law(self) -> T1PositioningRecord:
        if self.sensor_family is not SensorFamily.MECHANICAL_POSITIONING:
            raise ValueError(
                "T1PositioningRecord requires "
                f"sensor_family=MECHANICAL_POSITIONING, got {self.sensor_family.value}"
            )
        return self

    @model_validator(mode="after")
    def _provider_defined_law(self) -> T1PositioningRecord:
        if self.positioning_metric_type is PositioningMetricType.PROVIDER_DEFINED_RATIO:
            if self.provider_methodology_ref is None:
                raise ValueError(
                    "PROVIDER_DEFINED_RATIO requires provider_methodology_ref"
                )
            if self.canonical_metric_family is not None:
                raise ValueError(
                    "a provider-defined ratio cannot claim a canonical metric family: "
                    "that would be an unauthorized semantic equivalence "
                    "(04 section 8)"
                )
        else:
            if self.semantic_equivalence is SemanticEquivalence.NOT_COMPARABLE:
                raise ValueError(
                    f"{self.positioning_metric_type.value} is a normalized metric and "
                    "cannot be declared NOT_COMPARABLE"
                )
        return self

    @model_validator(mode="after")
    def _population_law(self) -> T1PositioningRecord:
        if self.numerator_definition == self.denominator_definition:
            raise ValueError(
                "numerator_definition and denominator_definition must differ: a "
                "ratio whose two sides are the same population is not a ratio"
            )
        return self


def _quality(*, identity_resolved: bool, coverage_ok: bool) -> T1Quality:
    return T1Quality(
        identity_quality=(
            QualityDimensionState.ACCEPTABLE_WITH_FLAGS
            if identity_resolved
            else QualityDimensionState.PARTIAL
        ),
        time_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
        semantic_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
        unit_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
        lineage_quality=QualityDimensionState.VERIFIED,
        source_integrity_quality=QualityDimensionState.VERIFIED,
        coverage_quality=(
            QualityDimensionState.VERIFIED if coverage_ok else QualityDimensionState.PARTIAL
        ),
        replay_quality=QualityDimensionState.UNKNOWN,
    )


def normalize_positioning(
    payload: PositioningObservationInput,
) -> T1PositioningRecord:
    """Normalize one positioning ratio.  Pure, deterministic, fail-closed."""
    coverage_ok = payload.source_coverage_state in (
        CoverageState.COMPLETE_SOURCE_BOUNDARY,
        CoverageState.EMPTY_CONFIRMED,
    )
    flags: set[NormalizationQualityFlag] = {
        NormalizationQualityFlag.SEMANTICS_UNVERIFIED,
        NormalizationQualityFlag.LINEAGE_COMPLETE,
    }
    if payload.metric_type is PositioningMetricType.PROVIDER_DEFINED_RATIO:
        flags.add(NormalizationQualityFlag.NO_SAFE_DEDUPE_KEY)
    if payload.native_positioning_id is None:
        flags.add(NormalizationQualityFlag.IDENTITY_PROVIDER_ID_MISSING)
        flags.add(NormalizationQualityFlag.NO_SAFE_DEDUPE_KEY)

    lineage = T1LineageRef(
        raw_projection_refs=payload.raw_projection_refs,
        acquisition_refs=payload.acquisition_refs,
        evidence_blob_hashes=payload.evidence_blob_hashes,
        identity_evidence_refs=(),
        semantic_evidence_refs=(),
        conversion_lineage_refs=(),
        code_version=payload.code_version,
        config_version=payload.config_version,
    )

    return T1PositioningRecord(
        sensor_family=SensorFamily.MECHANICAL_POSITIONING,
        provider=payload.provider,
        venue=payload.venue,
        native_instrument=payload.native_instrument,
        provider_instrument_id=payload.provider_instrument_id,
        native_event_id=payload.native_positioning_id,
        native_sequence_id=payload.native_sequence_id,
        contract_instance_id=payload.contract_instance_id,
        normalization_generation=payload.normalization_generation,
        source_revision_id=payload.source_revision_id,
        source_revision_state=payload.source_revision_state,
        source_coverage_state=payload.source_coverage_state,
        time=ObservationTimeEnvelope(
            source_event_at=payload.event_at,
            observed_at=payload.observed_at,
            ingested_at=payload.ingested_at,
            market_available_at=payload.market_available_at,
            availability_basis=payload.availability_basis,
            source_precision=payload.source_precision,
            interval_start_at=payload.interval_start_at,
            interval_end_at=payload.interval_end_at,
            interval_closed=payload.interval_closed,
            interval_time_convention=payload.interval_time_convention,
        ),
        native_values=(
            NativeQuantity(
                native_field_name="positioning_ratio",
                native_value=payload.value_native,
            ),
        ),
        normalization_status=NormalizationStatus.NATIVE_ONLY,
        missingness_reason=None,
        lineage_state=LineageState.LINEAGE_COMPLETE,
        lineage=lineage,
        quality=_quality(
            identity_resolved=payload.contract_instance_id is not None,
            coverage_ok=coverage_ok,
        ),
        quality_flags=canonical_flags(flags),
        versions=T1VersionContext(),
        positioning_metric_type=payload.metric_type,
        numerator_definition=payload.numerator_definition,
        denominator_definition=payload.denominator_definition,
        population_scope=payload.population_scope,
        population_size=payload.population_size,
        value_native=payload.value_native,
        value_unit=payload.value_unit,
        provider_metric_name=payload.provider_metric_name,
        provider_methodology_ref=payload.provider_methodology_ref,
        canonical_metric_family=None,
        semantic_equivalence=payload.semantic_equivalence,
    )
