"""SENSOR-B5-I14 - provider-neutral book snapshot and book-metric normalizers.

The I14 realization of ``bloc_05/04`` sections 6 and 7: exact side/level
semantics for snapshots, provider-native analytics for metrics, and the
sequence guardrails both need.

Snapshot truth this checkpoint preserves:

    snapshot identity       a provider snapshot id is required for certification
    provider sequence       carried, never renumbered
    bids[] / asks[]         price + native quantity + native unit, per level
    best_bid / best_ask     declared values are CHECKED against the levels
    depth levels            the provider's own level count, when it states one
    depth semantics         the provider's depth definition, verbatim
    event/availability      the frozen nine-clock envelope, undivided
    source lineage          projection / acquisition / blob, unchanged

**A delta is not a book.**  ``DELTA_UPDATE`` rows exist and are preserved, but
they are never certified as a complete book, and no derived metric is certified
from them.  Reconstruction across a sequence gap is not attempted here: the gap
is DETECTED and the book state is left uncertified, because interpolating across
an unresolved gap would invent levels the provider never sent (04 section 6.2).

**No metric across an invalid reconstruction.**  A reconstructed metric names the
book state it came from and is refused unless that book state was certified.

Book metrics are provider evidence with their own equivalence class.  A
provider-native liquidity or slippage score is NOT a Fabric-defined liquidity
metric, so the record carries the provider's methodology reference and the
frozen ``SemanticEquivalence`` class rather than a canonical metric value.  T1
stores normalized levels and provider-native metrics; the common ±5/10/25/50 bps
derivations belong to Bloc 9 (04 section 6.3), which is why none are computed
here.

No network, no wall clock, no id generation, no filesystem.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import Field, model_validator

from ...contracts.enums import SemanticEquivalence, SensorFamily
from ...storage import CoverageState, RevisionState
from ..authority import resolve_authority_inputs
from ..common.semantic_registry import ProviderSemanticRegistry
from ..enums import (
    AvailabilityBasis,
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
    linear_base_exposure,
    quote_notional,
)
from ..terms.snapshot import ContractTermsSnapshot
from .admission import (
    I04B_METHODOLOGY_ID,
    SensorFieldAdmission,
    admit_sensor_field,
    amount_from_conversion,
    blocked_amount,
    canonical_flags,
)
from .trade import DerivedAmount

__all__ = [
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
]

#: The canonical contract-count token, matching the I04B multiplier vocabulary.
_CONTRACTS_UNIT = "CONTRACTS"


class BookSide(str, Enum):
    """The two book sides.  Distinct from trade aggressor vocabulary."""

    BID = "BID"
    ASK = "ASK"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class BookQuantityUnit(str, Enum):
    """The canonical readings of a level quantity's native unit."""

    BASE_ASSET = "BASE_ASSET"
    CONTRACTS = "CONTRACTS"
    QUOTE_ASSET = "QUOTE_ASSET"
    PROVIDER_SPECIFIC = "PROVIDER_SPECIFIC"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class BookUpdateSemantics(str, Enum):
    """The frozen five-member update vocabulary (04 section 6.2)."""

    FULL_SNAPSHOT = "FULL_SNAPSHOT"
    DELTA_UPDATE = "DELTA_UPDATE"
    PARTIAL_SNAPSHOT = "PARTIAL_SNAPSHOT"
    TOP_OF_BOOK = "TOP_OF_BOOK"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class BookSequenceStatus(str, Enum):
    """Whether the provider sequence proves this update followed its predecessor.

    ``UNKNOWN_SEQUENCE`` is the fail-closed member and is NOT a synonym for
    contiguous: an unprovable sequence cannot certify a book state.
    """

    CONTIGUOUS = "CONTIGUOUS"
    GAP_DETECTED = "GAP_DETECTED"
    UNKNOWN_SEQUENCE = "UNKNOWN_SEQUENCE"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class BookMetricSource(str, Enum):
    """Who computed the metric: the provider, or this fabric from levels."""

    PROVIDER_NATIVE = "PROVIDER_NATIVE"
    RECONSTRUCTED_INTERNAL = "RECONSTRUCTED_INTERNAL"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


def classify_sequence(
    sequence: str | None, previous_sequence: str | None
) -> BookSequenceStatus:
    """Classify one update against its predecessor.  Never interpolates.

    * both integers and consecutive -> ``CONTIGUOUS``
    * both integers and the successor is not exactly previous + 1 -> ``GAP_DETECTED``
    * either token missing or non-numeric -> ``UNKNOWN_SEQUENCE``
    * a non-increasing pair is a contradiction, refused rather than classified
    """
    if sequence is None or previous_sequence is None:
        return BookSequenceStatus.UNKNOWN_SEQUENCE
    try:
        current = int(sequence)
        previous = int(previous_sequence)
    except (TypeError, ValueError):
        return BookSequenceStatus.UNKNOWN_SEQUENCE
    if current <= previous:
        raise ValueError(
            f"provider sequence did not advance ({previous} -> {current}): a "
            "non-increasing sequence contradicts the update itself"
        )
    if current == previous + 1:
        return BookSequenceStatus.CONTIGUOUS
    return BookSequenceStatus.GAP_DETECTED


class BookLevelInput(NormalizationModelBase):
    """One provider-reported level, before any canonical claim."""

    side: BookSide
    price_native: Decimal
    quantity_native: Decimal
    native_unit_token: OpaqueIdentifier
    unit_reading: BookQuantityUnit

    @model_validator(mode="after")
    def _price_law(self) -> BookLevelInput:
        if self.price_native <= 0 or not self.price_native.is_finite():
            raise ValueError("a book level price must be positive and finite")
        if self.quantity_native < 0 or not self.quantity_native.is_finite():
            raise ValueError("a book level quantity must be non-negative and finite")
        return self


class BookLevel(NormalizationModelBase):
    """One canonical level: native truth, plus only what I04B actually derived."""

    side: BookSide
    price_native: Decimal
    quantity_native: Decimal
    quantity_native_unit: OpaqueIdentifier
    quantity_base: DerivedAmount | None = None
    quote_notional: DerivedAmount | None = None


class BookSnapshotObservationInput(NormalizationModelBase):
    """Transport-neutral book snapshot, before any canonical claim.

    All levels of one snapshot must share one unit convention.  A book whose
    levels disagree about what "quantity" means is not one book, so that
    disagreement is refused rather than normalized row by row.
    """

    provider: OpaqueIdentifier
    venue: OpaqueIdentifier
    native_instrument: OpaqueIdentifier
    provider_instrument_id: OpaqueIdentifier | None = None
    contract_instance_id: OpaqueIdentifier | None = None

    snapshot_id: OpaqueIdentifier | None = None
    sequence: OpaqueIdentifier | None = None
    previous_sequence: OpaqueIdentifier | None = None

    update_semantics: BookUpdateSemantics
    bids: tuple[BookLevelInput, ...] = Field(min_length=1)
    asks: tuple[BookLevelInput, ...] = Field(min_length=1)
    provider_level_count: int | None = Field(default=None, ge=1)
    source_depth_definition: OpaqueIdentifier | None = None
    is_full_depth: bool = False

    native_unit_field: OpaqueIdentifier | None = None

    event_at: datetime | None = None
    observed_at: datetime | None = None
    ingested_at: datetime | None = None
    market_available_at: datetime | None = None
    availability_basis: AvailabilityBasis | None = None
    source_precision: TimestampPrecision | None = None

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
    def _side_law(self) -> BookSnapshotObservationInput:
        if any(level.side is not BookSide.BID for level in self.bids):
            raise ValueError("bids[] may contain only BID levels")
        if any(level.side is not BookSide.ASK for level in self.asks):
            raise ValueError("asks[] may contain only ASK levels")
        return self

    @model_validator(mode="after")
    def _unit_uniformity_law(self) -> BookSnapshotObservationInput:
        readings = {level.unit_reading for level in self.bids} | {
            level.unit_reading for level in self.asks
        }
        tokens = {level.native_unit_token for level in self.bids} | {
            level.native_unit_token for level in self.asks
        }
        if len(readings) != 1 or len(tokens) != 1:
            raise ValueError(
                "all levels of one snapshot must share one quantity unit reading "
                f"and token; got readings={sorted(r.value for r in readings)} "
                f"tokens={sorted(tokens)}"
            )
        return self

    @model_validator(mode="after")
    def _ordering_law(self) -> BookSnapshotObservationInput:
        """A book is ordered by construction; a disordered one is a schema failure."""
        bid_prices = [level.price_native for level in self.bids]
        ask_prices = [level.price_native for level in self.asks]
        if any(a <= b for a, b in zip(bid_prices, bid_prices[1:])):
            raise ValueError("bids must be strictly descending by price")
        if any(a >= b for a, b in zip(ask_prices, ask_prices[1:])):
            raise ValueError("asks must be strictly ascending by price")
        if bid_prices[0] >= ask_prices[0]:
            raise ValueError(
                "best bid >= best ask: a crossed book is a schema failure, not a "
                "normalization choice (04 section 6.1)"
            )
        return self

    @model_validator(mode="after")
    def _unique_refs(self) -> BookSnapshotObservationInput:
        for name in ("raw_projection_refs", "acquisition_refs", "evidence_blob_hashes"):
            values = getattr(self, name)
            if len(set(values)) != len(values):
                raise ValueError(f"{name} contains duplicate references")
        return self


class T1BookSnapshotRecord(T1BaseEnvelope):
    """Book-snapshot T1 record (04 sections 6.1-6.3).

    ``book_state_certified`` is the single derived boolean a consumer may trust
    when it needs a complete, ordered, gap-free book.  It is true only for a full
    snapshot whose sequence was proven contiguous, so a delta or a gap cannot be
    mistaken for a book by anything downstream.
    """

    snapshot_id: OpaqueIdentifier | None = None
    provider_sequence: OpaqueIdentifier | None = None
    previous_sequence: OpaqueIdentifier | None = None
    sequence_status: BookSequenceStatus

    update_semantics: BookUpdateSemantics
    is_full_snapshot: bool
    book_state_certified: bool

    bids: tuple[BookLevel, ...]
    asks: tuple[BookLevel, ...]
    best_bid: Decimal | None = None
    best_ask: Decimal | None = None
    snapshot_depth_levels: int | None = Field(default=None, ge=1)
    source_depth_definition: OpaqueIdentifier | None = None
    is_full_depth: bool = False

    level_unit_admission: SensorFieldAdmission | None = None

    @model_validator(mode="after")
    def _sensor_family_law(self) -> T1BookSnapshotRecord:
        if self.sensor_family is not SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            raise ValueError(
                "T1BookSnapshotRecord requires "
                "sensor_family=MECHANICAL_BOOK_SNAPSHOT, got "
                f"{self.sensor_family.value}"
            )
        return self

    @model_validator(mode="after")
    def _full_snapshot_law(self) -> T1BookSnapshotRecord:
        if self.is_full_snapshot != (
            self.update_semantics is BookUpdateSemantics.FULL_SNAPSHOT
        ):
            raise ValueError(
                "is_full_snapshot must be exactly 'update_semantics is "
                "FULL_SNAPSHOT': a delta is never a full snapshot (04 section 6.2)"
            )
        return self

    @model_validator(mode="after")
    def _certification_law(self) -> T1BookSnapshotRecord:
        if self.book_state_certified and not self.is_full_snapshot:
            raise ValueError(
                "a book state may be certified only from a full snapshot: a delta "
                "update is not a standalone book (04 section 6.2)"
            )
        if (
            self.book_state_certified
            and self.sequence_status is not BookSequenceStatus.CONTIGUOUS
        ):
            raise ValueError(
                "a book state may be certified only across a proven contiguous "
                f"sequence, got {self.sequence_status.value}"
            )
        return self

    @model_validator(mode="after")
    def _level_law(self) -> T1BookSnapshotRecord:
        if not self.bids or not self.asks:
            raise ValueError("a book snapshot record requires both sides")
        if any(level.side is not BookSide.BID for level in self.bids):
            raise ValueError("bids may contain only BID levels")
        if any(level.side is not BookSide.ASK for level in self.asks):
            raise ValueError("asks may contain only ASK levels")
        if self.best_bid is not None and self.best_bid != self.bids[0].price_native:
            raise ValueError(
                "best_bid contradicts the first bid level (04 section 6.1)"
            )
        if self.best_ask is not None and self.best_ask != self.asks[0].price_native:
            raise ValueError(
                "best_ask contradicts the first ask level (04 section 6.1)"
            )
        return self

    @model_validator(mode="after")
    def _admission_law(self) -> T1BookSnapshotRecord:
        admission = self.level_unit_admission
        if admission is None:
            return self
        if admission.sensor_family is not SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            raise ValueError("level_unit_admission belongs to another sensor family")
        if admission.canonical_field != "quantity_native_unit":
            raise ValueError(
                "level_unit_admission must decide quantity_native_unit, got "
                f"{admission.canonical_field!r}"
            )
        return self


class BookMetricObservationInput(NormalizationModelBase):
    """Transport-neutral provider-native or reconstructed book metric.

    ``source_book_state_certified`` is required for a reconstructed metric: a
    metric computed from a book this fabric could not certify is not a metric.
    """

    provider: OpaqueIdentifier
    venue: OpaqueIdentifier
    native_instrument: OpaqueIdentifier
    provider_instrument_id: OpaqueIdentifier | None = None
    contract_instance_id: OpaqueIdentifier | None = None

    native_metric_id: OpaqueIdentifier | None = None

    metric_name: OpaqueIdentifier
    metric_value_native: Decimal
    metric_unit: OpaqueIdentifier
    side: BookSide | None = None
    distance_bps: Decimal | None = None
    canonical_metric_family: OpaqueIdentifier | None = None
    semantic_equivalence: SemanticEquivalence
    provider_methodology_ref: OpaqueIdentifier | None = None

    metric_source: BookMetricSource
    source_book_state_certified: bool | None = None
    source_snapshot_id: OpaqueIdentifier | None = None

    event_at: datetime | None = None
    observed_at: datetime | None = None
    ingested_at: datetime | None = None
    market_available_at: datetime | None = None
    availability_basis: AvailabilityBasis | None = None
    source_precision: TimestampPrecision | None = None

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
    def _source_law(self) -> BookMetricObservationInput:
        if self.metric_source is BookMetricSource.RECONSTRUCTED_INTERNAL:
            if self.source_book_state_certified is None:
                raise ValueError(
                    "a reconstructed metric requires source_book_state_certified: "
                    "no derived spread/depth/imbalance may be certified across an "
                    "invalid reconstruction (04 section 6.2)"
                )
            if self.provider_methodology_ref is None:
                raise ValueError(
                    "a reconstructed metric requires provider_methodology_ref "
                    "(e.g. DEPTH_BPS_RECONSTRUCTION_V1): a computed metric must "
                    "name the method that computed it"
                )
        elif self.source_book_state_certified is not None:
            raise ValueError(
                "source_book_state_certified is a reconstruction claim and must be "
                "absent on provider-native evidence"
            )
        return self

    @model_validator(mode="after")
    def _depth_law(self) -> BookMetricObservationInput:
        if self.distance_bps is not None and self.side is None:
            raise ValueError(
                "a depth distance is measured from one side of the book, so "
                "distance_bps requires side"
            )
        if self.distance_bps is not None and self.distance_bps < 0:
            raise ValueError("distance_bps must be non-negative")
        return self

    @model_validator(mode="after")
    def _equivalence_law(self) -> BookMetricObservationInput:
        if (
            self.semantic_equivalence
            in (
                SemanticEquivalence.EXACT_EQUIVALENT,
                SemanticEquivalence.NORMALIZABLE_COMPARABLE,
            )
            and self.provider_methodology_ref is None
        ):
            raise ValueError(
                f"semantic_equivalence={self.semantic_equivalence.value} requires a "
                "documented provider_methodology_ref: an undocumented provider "
                "score is CORROBORATION_ONLY or NOT_COMPARABLE (04 section 7)"
            )
        return self

    @model_validator(mode="after")
    def _unique_refs(self) -> BookMetricObservationInput:
        for name in ("raw_projection_refs", "acquisition_refs", "evidence_blob_hashes"):
            values = getattr(self, name)
            if len(set(values)) != len(values):
                raise ValueError(f"{name} contains duplicate references")
        return self


class T1BookMetricRecord(T1BaseEnvelope):
    """Book-metric T1 record (04 section 7).

    Provider-native analytics are EVIDENCE with an equivalence class, never a
    Fabric-defined liquidity metric, so no canonical metric value is minted.
    """

    metric_name: OpaqueIdentifier
    metric_value_native: Decimal
    metric_unit: OpaqueIdentifier
    side: BookSide | None = None
    distance_bps: Decimal | None = None
    canonical_metric_family: OpaqueIdentifier | None = None
    semantic_equivalence: SemanticEquivalence
    provider_methodology_ref: OpaqueIdentifier | None = None

    metric_source: BookMetricSource
    source_book_state_certified: bool | None = None
    source_snapshot_id: OpaqueIdentifier | None = None

    @model_validator(mode="after")
    def _sensor_family_law(self) -> T1BookMetricRecord:
        if self.sensor_family is not SensorFamily.MECHANICAL_BOOK_METRIC:
            raise ValueError(
                "T1BookMetricRecord requires "
                f"sensor_family=MECHANICAL_BOOK_METRIC, got {self.sensor_family.value}"
            )
        return self

    @model_validator(mode="after")
    def _reconstruction_law(self) -> T1BookMetricRecord:
        if self.metric_source is BookMetricSource.RECONSTRUCTED_INTERNAL:
            if self.source_book_state_certified is not True:
                raise ValueError(
                    "a reconstructed metric may not be certified from an "
                    "uncertified book state (04 section 6.2)"
                )
            if self.provider_methodology_ref is None:
                raise ValueError(
                    "a reconstructed metric requires provider_methodology_ref"
                )
        return self


def _quality(
    *, identity_resolved: bool, coverage_ok: bool, quarantined: bool = False
) -> T1Quality:
    if quarantined:
        return T1Quality(
            identity_quality=QualityDimensionState.PARTIAL,
            time_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
            semantic_quality=QualityDimensionState.QUARANTINED,
            unit_quality=QualityDimensionState.ACCEPTABLE_WITH_FLAGS,
            lineage_quality=QualityDimensionState.VERIFIED,
            source_integrity_quality=QualityDimensionState.VERIFIED,
            coverage_quality=QualityDimensionState.QUARANTINED,
            replay_quality=QualityDimensionState.UNKNOWN,
        )
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


def _level_amounts(
    level: BookLevelInput,
    *,
    admitted_unit: BookQuantityUnit | None,
    terms: ContractTermsSnapshot | None,
    reference_price: ReferencePriceEvidence | None,
    knowledge_cutoff: datetime | None,
    flags: set[NormalizationQualityFlag],
) -> tuple[DerivedAmount | None, DerivedAmount | None]:
    """The two optional per-level derivations, or typed refusals."""
    base: DerivedAmount | None = None
    quote: DerivedAmount | None = None

    if admitted_unit is None:
        reason = MissingnessReason.SEMANTICS_BLOCKED
        return (
            blocked_amount(
                I04B_METHODOLOGY_ID,
                I04B_METHODOLOGY_ID,
                reason,
                unresolved_citation=I04B_METHODOLOGY_ID,
            ),
            blocked_amount(
                I04B_METHODOLOGY_ID,
                I04B_METHODOLOGY_ID,
                reason,
                unresolved_citation=I04B_METHODOLOGY_ID,
            ),
        )

    if admitted_unit is BookQuantityUnit.CONTRACTS:
        if terms is None:
            return (
                blocked_amount(
                    I04B_METHODOLOGY_ID,
                    I04B_METHODOLOGY_ID,
                    MissingnessReason.CONVERSION_BLOCKED,
                ),
                blocked_amount(
                    I04B_METHODOLOGY_ID,
                    I04B_METHODOLOGY_ID,
                    MissingnessReason.CONVERSION_BLOCKED,
                ),
            )
        base = amount_from_conversion(
            linear_base_exposure(level.quantity_native, _CONTRACTS_UNIT, terms)
        )
        if reference_price is None or knowledge_cutoff is None:
            quote = blocked_amount(
                I04B_METHODOLOGY_ID,
                I04B_METHODOLOGY_ID,
                MissingnessReason.CONVERSION_BLOCKED,
            )
            flags.add(NormalizationQualityFlag.REFERENCE_PRICE_UNAVAILABLE)
        else:
            quote = amount_from_conversion(
                contracts_to_quote_notional(
                    level.quantity_native,
                    _CONTRACTS_UNIT,
                    terms,
                    reference_price,
                    knowledge_cutoff,
                )
            )
        return base, quote

    if admitted_unit is BookQuantityUnit.BASE_ASSET:
        # Already base-denominated: the native value IS the base quantity.
        if reference_price is None or knowledge_cutoff is None or terms is None:
            return None, None
        if level.native_unit_token != terms.quantity_unit:
            return None, None
        quote = amount_from_conversion(
            quote_notional(
                base_exposure=level.quantity_native,
                base_unit=level.native_unit_token,
                terms=terms,
                price=reference_price,
                knowledge_cutoff=knowledge_cutoff,
            )
        )
        return None, quote

    if admitted_unit is BookQuantityUnit.QUOTE_ASSET:
        return None, None

    reason = MissingnessReason.SEMANTICS_BLOCKED
    return (
        blocked_amount(
            I04B_METHODOLOGY_ID,
            I04B_METHODOLOGY_ID,
            reason,
            unresolved_citation=I04B_METHODOLOGY_ID,
        ),
        blocked_amount(
            I04B_METHODOLOGY_ID,
            I04B_METHODOLOGY_ID,
            reason,
            unresolved_citation=I04B_METHODOLOGY_ID,
        ),
    )


def normalize_book_snapshot(
    payload: BookSnapshotObservationInput,
    *,
    registry: ProviderSemanticRegistry | object | None = None,
    terms: ContractTermsSnapshot | None = None,
    reference_price: ReferencePriceEvidence | None = None,
    knowledge_cutoff: datetime | None = None,
) -> T1BookSnapshotRecord:
    """Normalize one book snapshot.  Pure, deterministic, fail-closed."""
    if (
        terms is not None
        and payload.contract_instance_id is not None
        and terms.contract_instance_id != payload.contract_instance_id
    ):
        raise ValueError(
            f"payload contract_instance_id {payload.contract_instance_id!r} "
            f"contradicts the PIT terms' {terms.contract_instance_id!r} "
            "(bloc_05/07 F3)"
        )

    authority, resolved_registry = resolve_authority_inputs(registry, None)

    first_level = payload.bids[0]
    admission = admit_sensor_field(
        sensor_family=SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
        canonical_field="quantity_native_unit",
        provisional_value=first_level.unit_reading.value,
        provider=payload.provider,
        provider_field=payload.native_unit_field,
        registry=resolved_registry,
        authority=authority,
    )
    admitted_unit = first_level.unit_reading if admission.admitted else None

    sequence_status = classify_sequence(payload.sequence, payload.previous_sequence)
    coverage_ok = payload.source_coverage_state in (
        CoverageState.COMPLETE_SOURCE_BOUNDARY,
        CoverageState.EMPTY_CONFIRMED,
    )

    flags: set[NormalizationQualityFlag] = {
        NormalizationQualityFlag.SEMANTICS_UNVERIFIED,
        NormalizationQualityFlag.LINEAGE_COMPLETE,
    }
    if sequence_status is BookSequenceStatus.GAP_DETECTED:
        flags.add(NormalizationQualityFlag.BOOK_SEQUENCE_GAP)
    elif sequence_status is BookSequenceStatus.UNKNOWN_SEQUENCE:
        flags.add(NormalizationQualityFlag.TIME_SEQUENCE_MISSING)
    if payload.update_semantics in (
        BookUpdateSemantics.PARTIAL_SNAPSHOT,
        BookUpdateSemantics.TOP_OF_BOOK,
    ):
        flags.add(NormalizationQualityFlag.BOOK_PARTIAL_ONLY)
    if not payload.is_full_depth:
        flags.add(NormalizationQualityFlag.BOOK_DEPTH_UNKNOWN)
    if admitted_unit is None:
        flags.add(NormalizationQualityFlag.SEMANTICS_UNVERIFIED)

    def convert(levels: tuple[BookLevelInput, ...]) -> tuple[BookLevel, ...]:
        out: list[BookLevel] = []
        for level in levels:
            base, quote = _level_amounts(
                level,
                admitted_unit=admitted_unit,
                terms=terms,
                reference_price=reference_price,
                knowledge_cutoff=knowledge_cutoff,
                flags=flags,
            )
            out.append(
                BookLevel(
                    side=level.side,
                    price_native=level.price_native,
                    quantity_native=level.quantity_native,
                    quantity_native_unit=level.native_unit_token,
                    quantity_base=base,
                    quote_notional=quote,
                )
            )
        return tuple(out)

    bids = convert(payload.bids)
    asks = convert(payload.asks)

    if any(
        amount is not None and amount.blocked
        for level in (bids + asks)
        for amount in (level.quantity_base, level.quote_notional)
    ):
        flags.add(NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED)
    if payload.snapshot_id is None:
        flags.add(NormalizationQualityFlag.IDENTITY_PROVIDER_ID_MISSING)
        flags.add(NormalizationQualityFlag.NO_SAFE_DEDUPE_KEY)

    conversion_refs: list[str] = []
    for level in bids + asks:
        for amount in (level.quantity_base, level.quote_notional):
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

    native_values = tuple(
        NativeQuantity(
            native_field_name=f"{level.side.value.lower()}_quantity",
            native_value=level.quantity_native,
        )
        for level in payload.bids[:1] + payload.asks[:1]
    ) + tuple(
        NativeQuantity(
            native_field_name=f"{level.side.value.lower()}_price",
            native_value=level.price_native,
        )
        for level in payload.bids[:1] + payload.asks[:1]
    )

    is_full = payload.update_semantics is BookUpdateSemantics.FULL_SNAPSHOT
    certified = is_full and sequence_status is BookSequenceStatus.CONTIGUOUS

    return T1BookSnapshotRecord(
        sensor_family=SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
        provider=payload.provider,
        venue=payload.venue,
        native_instrument=payload.native_instrument,
        provider_instrument_id=payload.provider_instrument_id,
        native_event_id=payload.snapshot_id,
        native_sequence_id=payload.sequence,
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
        snapshot_id=payload.snapshot_id,
        provider_sequence=payload.sequence,
        previous_sequence=payload.previous_sequence,
        sequence_status=sequence_status,
        update_semantics=payload.update_semantics,
        is_full_snapshot=is_full,
        book_state_certified=certified,
        bids=bids,
        asks=asks,
        best_bid=bids[0].price_native,
        best_ask=asks[0].price_native,
        snapshot_depth_levels=payload.provider_level_count,
        source_depth_definition=payload.source_depth_definition,
        is_full_depth=payload.is_full_depth,
        level_unit_admission=admission,
    )


def normalize_book_metric(payload: BookMetricObservationInput) -> T1BookMetricRecord:
    """Normalize one book metric into evidence.  No canonical metric is minted."""
    coverage_ok = payload.source_coverage_state in (
        CoverageState.COMPLETE_SOURCE_BOUNDARY,
        CoverageState.EMPTY_CONFIRMED,
    )
    flags: set[NormalizationQualityFlag] = {
        NormalizationQualityFlag.SEMANTICS_UNVERIFIED,
        NormalizationQualityFlag.LINEAGE_COMPLETE,
    }
    if payload.native_metric_id is None:
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

    return T1BookMetricRecord(
        sensor_family=SensorFamily.MECHANICAL_BOOK_METRIC,
        provider=payload.provider,
        venue=payload.venue,
        native_instrument=payload.native_instrument,
        provider_instrument_id=payload.provider_instrument_id,
        native_event_id=payload.native_metric_id,
        native_sequence_id=None,
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
        ),
        native_values=(
            NativeQuantity(
                native_field_name="metric_value",
                native_value=payload.metric_value_native,
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
        metric_name=payload.metric_name,
        metric_value_native=payload.metric_value_native,
        metric_unit=payload.metric_unit,
        side=payload.side,
        distance_bps=payload.distance_bps,
        canonical_metric_family=payload.canonical_metric_family,
        semantic_equivalence=payload.semantic_equivalence,
        provider_methodology_ref=payload.provider_methodology_ref,
        metric_source=payload.metric_source,
        source_book_state_certified=payload.source_book_state_certified,
        source_snapshot_id=payload.source_snapshot_id,
    )
