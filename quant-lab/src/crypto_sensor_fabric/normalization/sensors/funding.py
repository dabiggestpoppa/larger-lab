"""SENSOR-B5-I13 - provider-neutral funding normalizer.

The I13 realization of ``bloc_05/04`` section 5: funding needs BOTH rate
semantics and interval semantics, so neither is allowed to stand alone.

Four readings stay distinguishable by construction.  There is no single
``funding_rate`` canonical field, only ``funding_rate_kind`` plus the native rate,
so predicted funding cannot overwrite realized funding by assignment: a predicted
row and a realized row are different rows, and the kind is required.

What is emitted:

    funding_rate_native                  carried verbatim (``native_values`` too)
    funding_rate_unit                    the provider's token, verbatim
    funding_rate_kind                    REALIZED / PREDICTED / INDICATIVE / UNKNOWN
    funding_interval_seconds             the provider's own interval
    funding_rate_per_8h_simple_equiv     optional comparable (SIMPLE_LINEAR)
    funding_rate_per_day_simple_equiv    optional comparable (SIMPLE_LINEAR)

The two equivalents are the ONLY transforms this checkpoint performs, they are
labeled ``simple_equiv`` in their own field names, and the methodology they cite
(``FUNDING_NATIVE_TO_8H_EQUIV_V1``) is the frozen registry row whose description
is exactly a scale-to-8h transform.  No compounding is applied and none is
claimed: 04 section 5.3 forbids silently annualizing with arbitrary compounding.

Annualized funding is deliberately ABSENT.  04 section 5.2 puts it in later
analytical layers, so this record has no field for it -- not a null field, no
field.  A consumer that wants annualization must derive it downstream with its
own stated method.

Rejections (fail-closed, never a clever reinterpretation):

* a flow amount or a PnL amount is not a funding rate: that is a contradiction,
  refused at construction rather than silently rescaled;
* an incompatible native unit (provider-specific, unknown) preserves the native
  rate and refuses every equivalent with a typed cause;
* an equivalent requires the interval, so an unknown interval yields a typed
  absence rather than a default 8h assumption;
* the USD funding amount is not derivable here at all: the approved conversion
  methodology does not exist, so the record has no USD funding field.

No network, no wall clock, no id generation, no filesystem.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import Field, model_validator

from ...contracts.enums import SensorFamily
from ...storage import (
    CoverageState,
    RevisionState,
    SourceUnitContract,
    SourceUnitEvidence,
)
from ..authority import resolve_authority_inputs
from ..common.semantic_registry import ProviderSemanticRegistry
from ..enums import (
    AvailabilityBasis,
    IntervalTimeConvention,
    LineageState,
    MissingnessReason,
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
from .admission import (
    SensorFieldAdmission,
    admit_sensor_field,
    blocked_amount,
    canonical_flags,
)
from .trade import DerivedAmount

__all__ = [
    "FUNDING_EQUIV_METHODOLOGY_ID",
    "FundingRateKind",
    "FundingRateUnit",
    "FundingObservationInput",
    "T1FundingRecord",
    "normalize_funding",
]

#: The frozen methodology that scales a native rate to an 8-hour equivalent.
#: Registry status is still ``PROVISIONAL``: citing is not admitting.
FUNDING_EQUIV_METHODOLOGY_ID = "FUNDING_NATIVE_TO_8H_EQUIV_V1"

#: The canonical interval the frozen methodology targets, in seconds.
_EIGHT_HOURS = Decimal(28800)
#: One day, in seconds, for the second comparable.
_ONE_DAY = Decimal(86400)


class FundingRateKind(str, Enum):
    """The frozen ``predicted_or_realized`` vocabulary (04 section 5.1)."""

    REALIZED = "REALIZED"
    PREDICTED = "PREDICTED"
    INDICATIVE = "INDICATIVE"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class FundingRateUnit(str, Enum):
    """What the provider's rate dimension actually is.

    The first two are rate dimensions and are rescalable across intervals.  The
    last three are NOT: a flow or a PnL amount has a different dimension, and
    ``UNKNOWN`` is the fail-closed reading.

    Members are readings, not registry rows: whether a provider field really means
    ``RATE_FRACTION`` is decided by the I09 admission ladder, never by this enum.
    """

    RATE_FRACTION = "RATE_FRACTION"
    RATE_PERCENT = "RATE_PERCENT"
    FLOW_AMOUNT = "FLOW_AMOUNT"
    PNL_AMOUNT = "PNL_AMOUNT"
    PROVIDER_SPECIFIC = "PROVIDER_SPECIFIC"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


#: Readings that are rate dimensions at all.  A flow or PnL reading is refused
#: outright: it is a different economic quantity with a different unit, and
#: rescaling it into a rate would invent a conversion nobody authorized.
_RATE_UNITS = frozenset(
    {FundingRateUnit.RATE_FRACTION, FundingRateUnit.RATE_PERCENT}
)


class FundingObservationInput(NormalizationModelBase):
    """Transport-neutral funding observation, before any canonical claim.

    ``funding_rate_native`` is required, including when it is zero: a zero
    funding rate is a real, published number, and a missing rate is not a
    different spelling of zero.

    ``funding_interval_seconds`` is Optional because a provider may publish a rate
    without its interval.  The absence then refuses the comparable equivalents
    instead of defaulting to 8 hours.
    """

    provider: OpaqueIdentifier
    venue: OpaqueIdentifier
    native_instrument: OpaqueIdentifier
    provider_instrument_id: OpaqueIdentifier | None = None
    contract_instance_id: OpaqueIdentifier | None = None

    native_funding_id: OpaqueIdentifier | None = None
    native_sequence_id: OpaqueIdentifier | None = None

    funding_rate_native: Decimal
    native_rate_unit_token: OpaqueIdentifier
    native_rate_unit_field: OpaqueIdentifier | None = None
    rate_reading: FundingRateUnit
    funding_rate_kind: FundingRateKind
    native_unit_evidence: SourceUnitEvidence | None = None
    source_unit_contract: SourceUnitContract | None = None

    funding_interval_seconds: int | None = Field(default=None, ge=1)

    event_at: datetime | None = None
    observed_at: datetime | None = None
    ingested_at: datetime | None = None
    published_at: datetime | None = None
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
    def _rate_unit_law(self) -> FundingObservationInput:
        if self.rate_reading in (
            FundingRateUnit.FLOW_AMOUNT,
            FundingRateUnit.PNL_AMOUNT,
        ):
            raise ValueError(
                f"rate_reading={self.rate_reading.value} is not a funding-rate "
                "dimension: a flow or PnL amount cannot be normalized as a rate "
                "and no conversion into one is authorized (04 section 5)"
            )
        return self

    @model_validator(mode="after")
    def _interval_agreement_law(self) -> FundingObservationInput:
        """A declared interval must agree with the period bounds it describes."""
        if (
            self.funding_interval_seconds is not None
            and self.interval_start_at is not None
            and self.interval_end_at is not None
        ):
            actual = int(
                (self.interval_end_at - self.interval_start_at).total_seconds()
            )
            if actual != self.funding_interval_seconds:
                raise ValueError(
                    f"funding_interval_seconds={self.funding_interval_seconds} "
                    f"contradicts the period bounds, which span {actual}s: an "
                    "interval substitution is not a rounding difference "
                    "(04 section 5.1)"
                )
        return self

    @model_validator(mode="after")
    def _unique_refs(self) -> FundingObservationInput:
        for name in ("raw_projection_refs", "acquisition_refs", "evidence_blob_hashes"):
            values = getattr(self, name)
            if len(set(values)) != len(values):
                raise ValueError(f"{name} contains duplicate references")
        return self


class T1FundingRecord(T1BaseEnvelope):
    """Funding-specific T1 record (04 sections 5.1-5.3).

    The four funding readings are kept distinct by ``funding_rate_kind`` plus the
    native rate, and the two interval comparables are separate optional fields so
    a predicted rate never occupies a realized slot.

    There is no annualized field and no USD amount field: 04 section 5.2 defers
    annualization, and no approved methodology produces a USD funding amount, so
    neither can be claimed.  The absence is structural, not an oversight.
    """

    funding_rate_native: Decimal
    funding_rate_unit: OpaqueIdentifier
    funding_rate_kind: FundingRateKind
    funding_interval_seconds: int | None = Field(default=None, ge=1)
    funding_period_start_at: datetime | None = None
    funding_period_end_at: datetime | None = None

    funding_rate_per_8h_simple_equiv: DerivedAmount | None = None
    funding_rate_per_day_simple_equiv: DerivedAmount | None = None

    rate_unit_admission: SensorFieldAdmission | None = None

    @model_validator(mode="after")
    def _sensor_family_law(self) -> T1FundingRecord:
        if self.sensor_family is not SensorFamily.MECHANICAL_FUNDING:
            raise ValueError(
                "T1FundingRecord requires sensor_family=MECHANICAL_FUNDING, got "
                f"{self.sensor_family.value}"
            )
        return self

    @model_validator(mode="after")
    def _admission_law(self) -> T1FundingRecord:
        admission = self.rate_unit_admission
        if admission is None:
            return self
        if admission.sensor_family is not SensorFamily.MECHANICAL_FUNDING:
            raise ValueError("rate_unit_admission belongs to another sensor family")
        if admission.canonical_field != "funding_rate_unit":
            raise ValueError(
                "rate_unit_admission must decide funding_rate_unit, got "
                f"{admission.canonical_field!r}"
            )
        return self

    @model_validator(mode="after")
    def _interval_law(self) -> T1FundingRecord:
        """A comparable interval rate must state the interval it was scaled from."""
        for name in (
            "funding_rate_per_8h_simple_equiv",
            "funding_rate_per_day_simple_equiv",
        ):
            amount = getattr(self, name)
            if amount is None or amount.blocked:
                continue
            if self.funding_interval_seconds is None:
                raise ValueError(
                    f"{name} is present but no funding interval is recorded: an "
                    "interval-scaled rate without its interval is unattributable "
                    "(04 section 5.1)"
                )
        return self

    @model_validator(mode="after")
    def _period_law(self) -> T1FundingRecord:
        start, end = self.funding_period_start_at, self.funding_period_end_at
        if start is not None and end is not None and end < start:
            raise ValueError("funding_period_end_at must be >= funding_period_start_at")
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


def _scaled_equivalent(
    *,
    rate: Decimal,
    interval_seconds: int,
    target_seconds: Decimal,
    output_unit: str,
    field: str,
    flags: set[NormalizationQualityFlag],
) -> DerivedAmount:
    """One SIMPLE_LINEAR interval scaling, citing the frozen methodology.

    The transform is exactly ``rate * target / interval``.  It performs no
    compounding, no annualization and no rounding: Decimal division keeps the
    scale deterministic, and the consumed inputs are named so the value's lineage
    is auditable (bloc_05/03 section 22 inv.7).
    """
    value = rate * target_seconds / Decimal(interval_seconds)
    if not value.is_finite():
        flags.add(NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED)
        return blocked_amount(
            FUNDING_EQUIV_METHODOLOGY_ID,
            "1",
            MissingnessReason.CONVERSION_BLOCKED,
        )
    return DerivedAmount(
        value=value,
        blocked=False,
        missingness_reason=None,
        methodology_id=FUNDING_EQUIV_METHODOLOGY_ID,
        methodology_version="1",
        output_unit=output_unit,
        conversion_lineage_refs=(
            f"B5_I13_FUNDING_INTERVAL_SECONDS:{interval_seconds}",
            f"B5_I13_SIMPLE_LINEAR_TARGET_SECONDS:{int(target_seconds)}",
        ),
        unresolved_citation=None,
    )


def normalize_funding(
    payload: FundingObservationInput,
    *,
    registry: ProviderSemanticRegistry | object | None = None,
) -> T1FundingRecord:
    """Normalize one funding observation.  Pure, deterministic, fail-closed.

    ``registry`` behaves exactly as at I12: a loader-issued ``SemanticAuthority``
    may promote the rate-unit claim; a bare registry is diagnostic only.
    """
    authority, resolved_registry = resolve_authority_inputs(registry, None)

    admission = admit_sensor_field(
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        canonical_field="funding_rate_unit",
        provisional_value=payload.rate_reading.value,
        provider=payload.provider,
        provider_field=payload.native_rate_unit_field,
        registry=resolved_registry,
        authority=authority,
    )
    admitted_unit = payload.rate_reading if admission.admitted else None

    coverage_ok = payload.source_coverage_state in (
        CoverageState.COMPLETE_SOURCE_BOUNDARY,
        CoverageState.EMPTY_CONFIRMED,
    )

    flags: set[NormalizationQualityFlag] = {
        NormalizationQualityFlag.SEMANTICS_UNVERIFIED,
        NormalizationQualityFlag.LINEAGE_COMPLETE,
    }

    output_unit = (
        "RATE_FRACTION"
        if payload.rate_reading is FundingRateUnit.RATE_FRACTION
        else "RATE_PERCENT"
        if payload.rate_reading is FundingRateUnit.RATE_PERCENT
        else None
    )

    def refused(reason: MissingnessReason) -> DerivedAmount:
        return blocked_amount(
            FUNDING_EQUIV_METHODOLOGY_ID,
            "1",
            reason,
            unresolved_citation=FUNDING_EQUIV_METHODOLOGY_ID,
        )

    eight_hour: DerivedAmount
    one_day: DerivedAmount

    if admitted_unit is None:
        eight_hour = refused(MissingnessReason.SEMANTICS_BLOCKED)
        one_day = refused(MissingnessReason.SEMANTICS_BLOCKED)
        flags.add(NormalizationQualityFlag.SEMANTICS_UNVERIFIED)
    elif admitted_unit not in _RATE_UNITS:
        # PROVIDER_SPECIFIC / UNKNOWN: a real rate in a dimension nobody certified.
        eight_hour = refused(MissingnessReason.SEMANTICS_BLOCKED)
        one_day = refused(MissingnessReason.SEMANTICS_BLOCKED)
        flags.add(NormalizationQualityFlag.UNIT_NATIVE_ONLY)
    elif payload.funding_interval_seconds is None:
        eight_hour = refused(MissingnessReason.TIME_BLOCKED)
        one_day = refused(MissingnessReason.TIME_BLOCKED)
        flags.add(NormalizationQualityFlag.TIME_INTERVAL_BOUNDARY_UNVERIFIED)
    else:
        eight_hour = _scaled_equivalent(
            rate=payload.funding_rate_native,
            interval_seconds=payload.funding_interval_seconds,
            target_seconds=_EIGHT_HOURS,
            output_unit=output_unit or "RATE_UNKNOWN",
            field="funding_rate_per_8h_simple_equiv",
            flags=flags,
        )
        one_day = _scaled_equivalent(
            rate=payload.funding_rate_native,
            interval_seconds=payload.funding_interval_seconds,
            target_seconds=_ONE_DAY,
            output_unit=output_unit or "RATE_UNKNOWN",
            field="funding_rate_per_day_simple_equiv",
            flags=flags,
        )

    if any(amount.blocked for amount in (eight_hour, one_day)):
        flags.add(NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED)
    if payload.native_funding_id is None:
        flags.add(NormalizationQualityFlag.IDENTITY_PROVIDER_ID_MISSING)
        flags.add(NormalizationQualityFlag.NO_SAFE_DEDUPE_KEY)

    conversion_refs: list[str] = []
    for amount in (eight_hour, one_day):
        for ref in amount.conversion_lineage_refs:
            if ref not in conversion_refs:
                conversion_refs.append(ref)

    lineage = T1LineageRef(
        raw_projection_refs=payload.raw_projection_refs,
        acquisition_refs=payload.acquisition_refs,
        evidence_blob_hashes=payload.evidence_blob_hashes,
        identity_evidence_refs=(),
        semantic_evidence_refs=(
            (admission.evidence_reference,)
            if admission.admitted and admission.evidence_reference is not None
            else ()
        ),
        conversion_lineage_refs=tuple(conversion_refs),
        code_version=payload.code_version,
        config_version=payload.config_version,
    )

    return T1FundingRecord(
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        provider=payload.provider,
        venue=payload.venue,
        native_instrument=payload.native_instrument,
        provider_instrument_id=payload.provider_instrument_id,
        native_event_id=None,
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
            published_at=payload.published_at,
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
                native_field_name="funding_rate",
                native_value=payload.funding_rate_native,
                native_unit_evidence=payload.native_unit_evidence,
                source_unit_contract=payload.source_unit_contract,
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
        funding_rate_native=payload.funding_rate_native,
        funding_rate_unit=payload.native_rate_unit_token,
        funding_rate_kind=payload.funding_rate_kind,
        funding_interval_seconds=payload.funding_interval_seconds,
        funding_period_start_at=payload.interval_start_at,
        funding_period_end_at=payload.interval_end_at,
        funding_rate_per_8h_simple_equiv=eight_hour,
        funding_rate_per_day_simple_equiv=one_day,
        rate_unit_admission=admission,
    )
