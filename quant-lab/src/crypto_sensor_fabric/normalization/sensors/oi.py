"""SENSOR-B5-I12 - provider-neutral open-interest (OI) normalizer.

The I12 realization of ``bloc_05/04`` section 4 (canonical fields, unit honesty,
USD conversion, aggregator OI), ``bloc_05/02`` section 4 (OI classification and
the ``market_available_at >= interval_end_at`` rule) and
``BLOC_05_I12_READINESS_ASSESSMENT.md`` sections 2-9.

OI is a STOCK, not a flow (04 section 4).  Nothing here sums across intervals,
derives a delta, or lets an OI row carry funding/liquidation/volume semantics: a
change in OI is a different sensor, and a delta is not an I12 field.

The eight frozen canonical fields are realized exactly:

    oi_native_value / oi_native_unit      carried verbatim from the provider
    oi_contracts                          optional derived
    oi_base                               optional derived
    oi_quote                              optional derived
    oi_usd                                optional derived -- BLOCKED (below)
    snapshot_or_interval                  the frozen five-member scope
    reference_price_ref                   optional citation, never a substitution

Two economic distinctions this module enforces structurally rather than
documenting:

**A carried value is not a derived value.**  A native unit that is already base
is not copied into ``oi_base`` as if computed, and a native contract count is not
copied into ``oi_contracts``: ``oi_native_value`` already holds it.  Only a value
the accepted I04B primitive actually produced appears in a derived slot, with the
primitive's own consumed-input lineage.

**A measured zero is not a defaulted zero.**  A venue genuinely can have no open
interest, so zero is admissible -- but only as a MEASURED zero with verified
coverage (04 section 4, mirroring the opposite rule at 04 section 3.5).  A zero
whose coverage is not verified keeps its native value and refuses every derived
amount with its own cause, so a gap can never be filled with an economic zero.

``oi_usd`` ships BLOCKED.  ``B5_I08_UNITS_V1`` governs USD methodology and is not
admitted, so no USD value is minted here and no "1 USDT = 1 USD" shortcut exists.
When the provider itself reports a USD-native reading, that reading survives in
``native_values`` and the record marks
``usd_native_passthrough_pending``: the passthrough is representable as a pending
claim without a single dollar being emitted.

Aggregator OI (04 section 4.4): ``provider`` and ``venue`` stay separate fields,
and a multi-venue aggregate is marked ``venue_assignment_refused`` -- it is never
attributed to one venue.

No network, no wall clock, no id generation, no filesystem: a payload in, a
record out, byte-identical for byte-identical input.
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
from ..terms.conversion import (
    ReferencePriceEvidence,
    contracts_to_quote_notional,
    inverse_base_from_quote,
    inverse_quote_face,
    linear_base_exposure,
)
from ..terms.snapshot import ContractTermsSnapshot
from .admission import (
    I04B_METHODOLOGY_ID,
    I08_UNITS_METHODOLOGY_ID,
    SensorFieldAdmission,
    admit_sensor_field,
    amount_from_conversion,
    blocked_amount,
    canonical_flags,
)
from .trade import DerivedAmount

__all__ = [
    "OI_CONTRACTS_METHODOLOGY_ID",
    "OI_USD_PASSTHROUGH_METHODOLOGY_ID",
    "OpenInterestAggregationScope",
    "OpenInterestNativeUnit",
    "OpenInterestObservationInput",
    "OpenInterestSnapshotScope",
    "T1OpenInterestRecord",
    "normalize_open_interest",
]

#: The accepted methodology that governs contract-count OI conversion.  CIted
#: verbatim from ``config/crypto_sensor_fabric/methodology_registry.yaml``, where
#: the row is still ``PROVISIONAL``: citing is not admitting.
OI_CONTRACTS_METHODOLOGY_ID = "OI_CONTRACTS_TO_USD_V1"

#: The representation-equivalent USD passthrough methodology.  Also cited, also
#: not exercised: the value it would produce is withheld while I08 is unresolved.
OI_USD_PASSTHROUGH_METHODOLOGY_ID = "OI_USD_NATIVE_PASSTHROUGH_V1"

#: The frozen ``snapshot_or_interval`` vocabulary (04 section 4.1, five members).
#: Deliberately NOT merged with ``bloc_05/02`` section 4's observation
#: classification (POINT_SNAPSHOT / WINDOW_STATISTIC / UNKNOWN): those are two
#: layers, and I11 refused the same merge for the liquidation event shape.
class OpenInterestSnapshotScope(str, Enum):
    """How the provider reduced the stock it is reporting."""

    POINT_SNAPSHOT = "POINT_SNAPSHOT"
    INTERVAL_LAST = "INTERVAL_LAST"
    INTERVAL_AVERAGE = "INTERVAL_AVERAGE"
    PROVIDER_AGGREGATE = "PROVIDER_AGGREGATE"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class OpenInterestNativeUnit(str, Enum):
    """The five frozen native-unit readings (04 section 4.2) plus ``UNKNOWN``.

    ``PROVIDER_SPECIFIC`` and ``UNKNOWN`` are the fail-closed members: a unit the
    registry has not certified converts to nothing, and the native value survives
    untouched.
    """

    CONTRACTS = "CONTRACTS"
    BASE_ASSET = "BASE_ASSET"
    QUOTE_ASSET = "QUOTE_ASSET"
    USD = "USD"
    PROVIDER_SPECIFIC = "PROVIDER_SPECIFIC"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class OpenInterestAggregationScope(str, Enum):
    """Whether the observation covers one venue or several (04 section 4.4)."""

    SINGLE_VENUE = "SINGLE_VENUE"
    MULTI_VENUE_AGGREGATE = "MULTI_VENUE_AGGREGATE"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class OpenInterestObservationInput(NormalizationModelBase):
    """Transport-neutral OI observation, before any canonical claim.

    Provider-neutral: the only provider-specific things a caller supplies are the
    raw field name and token it observed (preserved verbatim) and its own reading
    of them.  There is deliberately NO field by which a caller can declare its
    reading certified: the reading is resolved against the I09 registry inside
    :func:`normalize_open_interest`.

    ``oi_native_value`` is required, including when it is zero.  Missing OI is
    not a value: a provider that reported nothing produced no OI observation to
    normalize, and accepting ``None`` here would create exactly the
    missing-as-zero hole 04 section 4.1 forbids.
    """

    provider: OpaqueIdentifier
    venue: OpaqueIdentifier
    native_instrument: OpaqueIdentifier
    provider_instrument_id: OpaqueIdentifier | None = None
    contract_instance_id: OpaqueIdentifier | None = None

    native_snapshot_id: OpaqueIdentifier | None = None
    native_sequence_id: OpaqueIdentifier | None = None

    oi_native_value: Decimal
    native_unit_token: OpaqueIdentifier
    native_unit_field: OpaqueIdentifier | None = None
    unit_reading: OpenInterestNativeUnit
    native_unit_evidence: SourceUnitEvidence | None = None
    source_unit_contract: SourceUnitContract | None = None

    snapshot_scope: OpenInterestSnapshotScope
    aggregation_scope: OpenInterestAggregationScope = (
        OpenInterestAggregationScope.SINGLE_VENUE
    )
    aggregate_venue_count: int | None = Field(default=None, ge=2)

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
    def _interval_scope_law(self) -> OpenInterestObservationInput:
        if self.snapshot_scope in (
            OpenInterestSnapshotScope.INTERVAL_LAST,
            OpenInterestSnapshotScope.INTERVAL_AVERAGE,
        ) and self.interval_end_at is None:
            raise ValueError(
                f"snapshot_scope={self.snapshot_scope.value} requires "
                "interval_end_at: an interval statistic without a window end "
                "cannot satisfy market_available_at >= interval_end_at "
                "(bloc_05/02 section 4)"
            )
        return self

    @model_validator(mode="after")
    def _aggregate_law(self) -> OpenInterestObservationInput:
        multi = self.aggregation_scope is OpenInterestAggregationScope.MULTI_VENUE_AGGREGATE
        if multi and self.aggregate_venue_count is None:
            raise ValueError(
                "aggregation_scope=MULTI_VENUE_AGGREGATE requires "
                "aggregate_venue_count: an aggregate that cannot say how many "
                "venues it covers cannot be compared with a single venue"
            )
        if not multi and self.aggregate_venue_count is not None:
            raise ValueError(
                "aggregate_venue_count is a multi-venue claim and must be absent "
                "on a SINGLE_VENUE observation"
            )
        return self

    @model_validator(mode="after")
    def _unique_refs(self) -> OpenInterestObservationInput:
        for name in ("raw_projection_refs", "acquisition_refs", "evidence_blob_hashes"):
            values = getattr(self, name)
            if len(set(values)) != len(values):
                raise ValueError(f"{name} contains duplicate references")
        return self


class T1OpenInterestRecord(T1BaseEnvelope):
    """OI-specific T1 record (04 section 4.1; readiness sections 2-8).

    Extends the accepted base envelope and adds only OI-owned fields.  The
    inherited laws still apply unchanged, so this subclass cannot relax the
    ratified base contract -- it can only add.

    OI-specific laws enforced here:

    * ``oi_usd`` is BLOCKED.  ``B5_I08_UNITS_V1`` is unresolved, so an emitted
      USD value is not a decision this checkpoint may take; the law makes that a
      construction error rather than a code-review question.
    * a measured zero without verified coverage admits no derived amount.
    * a multi-venue aggregate refuses venue attribution AND must be scoped
      ``PROVIDER_AGGREGATE``, so an aggregate can never look like a snapshot of
      one market.
    * an interval scope requires a window end.
    """

    oi_native_value: Decimal
    oi_native_unit: OpaqueIdentifier

    oi_contracts: DerivedAmount | None = None
    oi_base: DerivedAmount | None = None
    oi_quote: DerivedAmount | None = None
    oi_usd: DerivedAmount | None = None

    snapshot_or_interval: OpenInterestSnapshotScope
    reference_price_ref: OpaqueIdentifier | None = None

    aggregation_scope: OpenInterestAggregationScope = (
        OpenInterestAggregationScope.SINGLE_VENUE
    )
    venue_assignment_refused: bool = False
    unit_admission: SensorFieldAdmission | None = None

    measured_zero: bool
    zero_coverage_verified: bool
    usd_native_passthrough_pending: bool = False

    @model_validator(mode="after")
    def _sensor_family_law(self) -> T1OpenInterestRecord:
        if self.sensor_family is not SensorFamily.MECHANICAL_OPEN_INTEREST:
            raise ValueError(
                "T1OpenInterestRecord requires "
                "sensor_family=MECHANICAL_OPEN_INTEREST, got "
                f"{self.sensor_family.value}"
            )
        return self

    @model_validator(mode="after")
    def _usd_stays_blocked(self) -> T1OpenInterestRecord:
        """``B5_I08_UNITS_V1`` is unresolved: no OI row may carry a USD value."""
        if self.oi_usd is not None and not self.oi_usd.blocked:
            raise ValueError(
                "oi_usd must remain blocked while B5_I08_UNITS_V1 is unresolved "
                "(readiness section 5): a USD value here would require a "
                "methodology no operator has admitted"
            )
        return self

    @model_validator(mode="after")
    def _unit_admission_law(self) -> T1OpenInterestRecord:
        if self.unit_admission is None:
            return self
        if self.unit_admission.sensor_family is not SensorFamily.MECHANICAL_OPEN_INTEREST:
            raise ValueError("unit_admission belongs to another sensor family")
        if self.unit_admission.canonical_field != "oi_native_unit":
            raise ValueError(
                "unit_admission must decide oi_native_unit, got "
                f"{self.unit_admission.canonical_field!r}"
            )
        return self

    @model_validator(mode="after")
    def _measured_zero_law(self) -> T1OpenInterestRecord:
        if self.measured_zero != (self.oi_native_value == 0):
            raise ValueError(
                "measured_zero must be exactly 'the native value is zero': a zero "
                "is a measurement, never an inference (04 section 4)"
            )
        if self.measured_zero and not self.zero_coverage_verified:
            for name in ("oi_contracts", "oi_base", "oi_quote"):
                amount = getattr(self, name)
                if amount is not None and not amount.blocked:
                    raise ValueError(
                        f"{name} is admitted on an unverified-coverage zero: a zero "
                        "without coverage provenance must not be converted into a "
                        "derived quantity (readiness section 7)"
                    )
        return self

    @model_validator(mode="after")
    def _aggregation_law(self) -> T1OpenInterestRecord:
        multi = self.aggregation_scope is OpenInterestAggregationScope.MULTI_VENUE_AGGREGATE
        if self.venue_assignment_refused != multi:
            raise ValueError(
                "venue_assignment_refused must be exactly 'the observation is a "
                "multi-venue aggregate': a single-venue row has a venue, and an "
                "aggregate must not be attributed to one (04 section 4.4)"
            )
        if multi and self.snapshot_or_interval is not OpenInterestSnapshotScope.PROVIDER_AGGREGATE:
            raise ValueError(
                "a multi-venue aggregate must be scoped PROVIDER_AGGREGATE "
                "(04 section 4.1/4.4)"
            )
        return self

    @model_validator(mode="after")
    def _interval_scope_law(self) -> T1OpenInterestRecord:
        if self.snapshot_or_interval in (
            OpenInterestSnapshotScope.INTERVAL_LAST,
            OpenInterestSnapshotScope.INTERVAL_AVERAGE,
        ) and self.time.interval_end_at is None:
            raise ValueError(
                f"snapshot_or_interval={self.snapshot_or_interval.value} requires "
                "an interval_end_at (bloc_05/02 section 4)"
            )
        return self


#: Coverage states that let a zero be read as a measurement rather than a gap.
_VERIFIED_COVERAGE = frozenset(
    {CoverageState.COMPLETE_SOURCE_BOUNDARY, CoverageState.EMPTY_CONFIRMED}
)

#: Quote assets whose USD equivalent needs the unresolved ``B5_I08_UNITS_V1``.
_STABLECOIN_QUOTES = frozenset({"USDT", "USDC"})

#: The canonical unit token meaning "this quantity counts contracts".
_CONTRACTS_UNIT = "CONTRACTS"


def _quality(
    *, identity_resolved: bool, coverage_ok: bool
) -> T1Quality:
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


def _derived_amounts(
    payload: OpenInterestObservationInput,
    *,
    admitted_unit: OpenInterestNativeUnit | None,
    terms: ContractTermsSnapshot | None,
    reference_price: ReferencePriceEvidence | None,
    knowledge_cutoff: datetime | None,
    flags: set[NormalizationQualityFlag],
) -> tuple[DerivedAmount | None, DerivedAmount | None, DerivedAmount | None]:
    """The three optional conversions, or typed refusals.  Never a guess.

    ``admitted_unit`` is ``None`` when the unit claim was not admitted -- in that
    case nothing is convertible and every derived slot says why.
    """
    contracts: DerivedAmount | None = None
    base: DerivedAmount | None = None
    quote: DerivedAmount | None = None

    definition = MissingnessReason.CONVERSION_BLOCKED

    if admitted_unit is None:
        reason = MissingnessReason.SEMANTICS_BLOCKED
        return (
            blocked_amount(
                OI_CONTRACTS_METHODOLOGY_ID,
                "1",
                reason,
                unresolved_citation=OI_CONTRACTS_METHODOLOGY_ID,
            ),
            blocked_amount(
                OI_CONTRACTS_METHODOLOGY_ID,
                "1",
                reason,
                unresolved_citation=OI_CONTRACTS_METHODOLOGY_ID,
            ),
            blocked_amount(
                OI_CONTRACTS_METHODOLOGY_ID,
                "1",
                reason,
                unresolved_citation=OI_CONTRACTS_METHODOLOGY_ID,
            ),
        )

    if admitted_unit is OpenInterestNativeUnit.CONTRACTS:
        if terms is None:
            # Contract denomination without PIT terms converts to nothing.
            return (
                None,
                blocked_amount(OI_CONTRACTS_METHODOLOGY_ID, "1", definition),
                blocked_amount(OI_CONTRACTS_METHODOLOGY_ID, "1", definition),
            )
        if terms.payoff_type.value == "INVERSE" and terms.inverse_flag:
            face = inverse_quote_face(
                payload.oi_native_value, _CONTRACTS_UNIT, terms
            )
            quote = amount_from_conversion(face, methodology_id=OI_CONTRACTS_METHODOLOGY_ID)
            if face.normalized_value is None:
                base = blocked_amount(OI_CONTRACTS_METHODOLOGY_ID, "1", definition)
            elif reference_price is None or knowledge_cutoff is None:
                base = blocked_amount(OI_CONTRACTS_METHODOLOGY_ID, "1", definition)
                flags.add(NormalizationQualityFlag.REFERENCE_PRICE_UNAVAILABLE)
            else:
                base = amount_from_conversion(
                    inverse_base_from_quote(
                        face.normalized_value,
                        terms.price_unit,
                        terms,
                        reference_price,
                        knowledge_cutoff,
                    ),
                    methodology_id=OI_CONTRACTS_METHODOLOGY_ID,
                )
            return None, base, quote
        base = amount_from_conversion(
            linear_base_exposure(payload.oi_native_value, _CONTRACTS_UNIT, terms),
            methodology_id=OI_CONTRACTS_METHODOLOGY_ID,
        )
        if reference_price is None or knowledge_cutoff is None:
            quote = blocked_amount(OI_CONTRACTS_METHODOLOGY_ID, "1", definition)
            flags.add(NormalizationQualityFlag.REFERENCE_PRICE_UNAVAILABLE)
        else:
            quote = amount_from_conversion(
                contracts_to_quote_notional(
                    payload.oi_native_value,
                    _CONTRACTS_UNIT,
                    terms,
                    reference_price,
                    knowledge_cutoff,
                ),
                methodology_id=OI_CONTRACTS_METHODOLOGY_ID,
            )
        return None, base, quote

    if admitted_unit in (
        OpenInterestNativeUnit.BASE_ASSET,
        OpenInterestNativeUnit.QUOTE_ASSET,
    ):
        # The native reading already IS the base/quote quantity.  Re-labelling it
        # into a derived slot would be a claim that a conversion happened.
        return None, None, None

    if admitted_unit is OpenInterestNativeUnit.USD:
        # Withheld with the passthrough pending (see ``usd_native_passthrough``).
        return None, None, None

    reason = MissingnessReason.SEMANTICS_BLOCKED
    return (
        None,
        blocked_amount(
            OI_CONTRACTS_METHODOLOGY_ID,
            "1",
            reason,
            unresolved_citation=OI_CONTRACTS_METHODOLOGY_ID,
        ),
        blocked_amount(
            OI_CONTRACTS_METHODOLOGY_ID,
            "1",
            reason,
            unresolved_citation=OI_CONTRACTS_METHODOLOGY_ID,
        ),
    )


def normalize_open_interest(
    payload: OpenInterestObservationInput,
    *,
    registry: ProviderSemanticRegistry | object | None = None,
    terms: ContractTermsSnapshot | None = None,
    reference_price: ReferencePriceEvidence | None = None,
    knowledge_cutoff: datetime | None = None,
) -> T1OpenInterestRecord:
    """Normalize one OI observation.  Pure, deterministic, fail-closed.

    ``registry`` carries EITHER a loader-issued ``SemanticAuthority`` (the only
    thing that may promote a native unit reading) OR a bare I09
    ``ProviderSemanticRegistry``, which stays a DIAGNOSTIC value: its rows are
    resolved, but no derived field is admitted from it.

    Raises ``ValueError`` for the one contradiction the record cannot represent: a
    payload whose ``contract_instance_id`` disagrees with the supplied PIT terms.
    Every other unease is a typed flag, a typed absence or a marked scope, never
    an exception and never a guess.
    """
    if (
        terms is not None
        and payload.contract_instance_id is not None
        and terms.contract_instance_id != payload.contract_instance_id
    ):
        raise ValueError(
            f"payload contract_instance_id {payload.contract_instance_id!r} "
            f"contradicts the PIT terms' {terms.contract_instance_id!r}; an "
            "observation is normalized against its own contract instance or not "
            "at all (bloc_05/07 F3)"
        )

    authority, resolved_registry = resolve_authority_inputs(registry, None)

    admission = admit_sensor_field(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        canonical_field="oi_native_unit",
        provisional_value=payload.unit_reading.value,
        provider=payload.provider,
        provider_field=payload.native_unit_field,
        registry=resolved_registry,
        authority=authority,
    )
    admitted_unit = (
        payload.unit_reading if admission.admitted else None
    )

    coverage_ok = payload.source_coverage_state in _VERIFIED_COVERAGE
    measured_zero = payload.oi_native_value == 0
    zero_coverage_verified = coverage_ok

    flags: set[NormalizationQualityFlag] = {
        NormalizationQualityFlag.SEMANTICS_UNVERIFIED,
        NormalizationQualityFlag.LINEAGE_COMPLETE,
    }

    if zero_coverage_verified is False and measured_zero:
        # A zero that cannot show coverage is not convertible into a derived
        # quantity: every derived slot gets this cause instead of an economic zero.
        oi_contracts: DerivedAmount | None = None
        oi_base: DerivedAmount | None = blocked_amount(
            OI_CONTRACTS_METHODOLOGY_ID,
            "1",
            MissingnessReason.SOURCE_GAP,
        )
        oi_quote: DerivedAmount | None = blocked_amount(
            OI_CONTRACTS_METHODOLOGY_ID,
            "1",
            MissingnessReason.SOURCE_GAP,
        )
    else:
        oi_contracts, oi_base, oi_quote = _derived_amounts(
            payload,
            admitted_unit=admitted_unit,
            terms=terms,
            reference_price=reference_price,
            knowledge_cutoff=knowledge_cutoff,
            flags=flags,
        )

    # The unresolved cross-family step stays blocked (readiness section 5).
    oi_usd = blocked_amount(
        I08_UNITS_METHODOLOGY_ID,
        I08_UNITS_METHODOLOGY_ID,
        MissingnessReason.CONVERSION_BLOCKED,
        unresolved_citation=I08_UNITS_METHODOLOGY_ID,
    )
    flags.add(NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED)

    passthrough_pending = admitted_unit is OpenInterestNativeUnit.USD
    if passthrough_pending or (
        payload.native_unit_token in _STABLECOIN_QUOTES
        or (terms is not None and terms.quote_asset_id in _STABLECOIN_QUOTES)
    ):
        flags.add(NormalizationQualityFlag.STABLECOIN_CONVERSION_UNAVAILABLE)

    if any(
        amount is not None and amount.blocked
        for amount in (oi_contracts, oi_base, oi_quote)
    ):
        flags.add(NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED)
    if admitted_unit is None:
        flags.add(NormalizationQualityFlag.SEMANTICS_UNVERIFIED)
    if payload.native_snapshot_id is None:
        flags.add(NormalizationQualityFlag.IDENTITY_PROVIDER_ID_MISSING)
        flags.add(NormalizationQualityFlag.NO_SAFE_DEDUPE_KEY)

    conversion_refs: list[str] = []
    for amount in (oi_contracts, oi_base, oi_quote):
        if amount is None:
            continue
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

    native_values = (
        NativeQuantity(
            native_field_name="oi",
            native_value=payload.oi_native_value,
            native_unit_evidence=payload.native_unit_evidence,
            source_unit_contract=payload.source_unit_contract,
        ),
    )

    return T1OpenInterestRecord(
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
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
            market_available_at=payload.market_available_at,
            availability_basis=payload.availability_basis,
            source_precision=payload.source_precision,
            interval_start_at=payload.interval_start_at,
            interval_end_at=payload.interval_end_at,
            interval_closed=payload.interval_closed,
            interval_time_convention=payload.interval_time_convention,
        ),
        native_values=native_values,
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
        oi_native_value=payload.oi_native_value,
        oi_native_unit=payload.native_unit_token,
        oi_contracts=oi_contracts,
        oi_base=oi_base,
        oi_quote=oi_quote,
        oi_usd=oi_usd,
        snapshot_or_interval=payload.snapshot_scope,
        reference_price_ref=(
            reference_price.reference_price_source if reference_price is not None else None
        ),
        aggregation_scope=payload.aggregation_scope,
        venue_assignment_refused=(
            payload.aggregation_scope is OpenInterestAggregationScope.MULTI_VENUE_AGGREGATE
        ),
        unit_admission=admission,
        measured_zero=measured_zero,
        zero_coverage_verified=zero_coverage_verified,
        usd_native_passthrough_pending=passthrough_pending,
    )
