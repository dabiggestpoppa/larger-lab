"""SENSOR-B5-I15b - provider-neutral basis normalizer.

The I15 realization of ``bloc_05/04`` section 9.  A basis number is meaningless
without the identity of the two instruments it relates and the reference price it
was measured against, so this checkpoint emits identity and refusals rather than
a converted number.

The frozen canonical fields are:

    basis_value_native / basis_unit
    spot_reference            the reference instrument's identity
    futures_reference         the derivative's identity
    annualization_method      present iff the reading is annualized
    expiry                    optional temporal context
    provider_methodology_ref  the provider's own method, when it states one

Four reference-price conditions are checked BEFORE a reading counts as comparable,
and each has its own stated refusal (mission section 7):

* ``NOT_SUPPLIED``            no reference price was offered
* ``TYPE_NOT_APPROVED``       the reference type is not admissible for basis
* ``NO_REFERENCE_AVAILABILITY`` the reference has no market-availability clock
* ``LATE_REFERENCE``          the reference became available after the knowledge
                              cutoff, so using it would be future information
* ``UNIT_MISMATCH``           an absolute-price basis whose reference is priced in
                              a different unit

A late or type-substituted reference is REFUSED, never substituted: no fallback
ladder between the five frozen reference types exists (bloc_05/03 section 8).

Cross-venue synthesis is refused outright: a basis whose spot reference sits on a
different venue from the futures leg is not a T1 basis at all (04 section 9,
"no cross-venue synthesis at T1"), so it is a contradiction rather than a subtly
degraded record.

No derived bps value is minted.  The frozen methodology registry contains no
basis-methodology row, and inventing one would be an unauthorized methodology
admission, so the record carries ``basis_comparable`` (a comparability flag, not a
computed number) and leaves every transformation to a later analytical layer.

No network, no wall clock, no id generation, no filesystem.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import Field, model_validator

from ...contracts.enums import SensorFamily
from ...storage import CoverageState, RevisionState
from ..enums import (
    AvailabilityBasis,
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
from ..terms.conversion import ReferencePriceType
from .admission import canonical_flags

__all__ = [
    "BasisReferenceRefusal",
    "BasisUnit",
    "BasisObservationInput",
    "T1BasisRecord",
    "normalize_basis",
]

#: Reference-price types admissible as a basis reference.  ``TRADE_PRICE`` is a
#: transaction, not a reference for a stock comparison; ``MID_PRICE`` is a
#: derived quantity whose own construction would need certifying first.
_APPROVED_REFERENCE_TYPES = frozenset(
    {ReferencePriceType.PROVIDER_INDEX, ReferencePriceType.PROVIDER_MARK}
)


class BasisUnit(str, Enum):
    """The four frozen basis units (04 section 9)."""

    ABSOLUTE_PRICE = "ABSOLUTE_PRICE"
    PERCENT = "PERCENT"
    BPS = "BPS"
    ANNUALIZED_PERCENT = "ANNUALIZED_PERCENT"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class BasisReferenceRefusal(str, Enum):
    """Why a basis reading is not comparable.  Fail-closed, one cause each."""

    NOT_SUPPLIED = "NOT_SUPPLIED"
    TYPE_NOT_APPROVED = "TYPE_NOT_APPROVED"
    NO_REFERENCE_AVAILABILITY = "NO_REFERENCE_AVAILABILITY"
    LATE_REFERENCE = "LATE_REFERENCE"
    UNIT_MISMATCH = "UNIT_MISMATCH"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class BasisObservationInput(NormalizationModelBase):
    """Transport-neutral basis observation, before any canonical claim.

    ``spot_reference_venue`` is required so the cross-venue rule is checkable: a
    basis between two venues is not a T1 basis, and accepting the payload without
    knowing where the reference trades would make that unenforceable.
    """

    provider: OpaqueIdentifier
    venue: OpaqueIdentifier
    native_instrument: OpaqueIdentifier
    provider_instrument_id: OpaqueIdentifier | None = None
    contract_instance_id: OpaqueIdentifier | None = None

    native_basis_id: OpaqueIdentifier | None = None
    native_sequence_id: OpaqueIdentifier | None = None

    futures_reference: OpaqueIdentifier
    spot_reference: OpaqueIdentifier
    spot_reference_venue: OpaqueIdentifier

    basis_value_native: Decimal
    basis_unit: BasisUnit

    reference_price: Decimal | None = None
    reference_price_type: ReferencePriceType | None = None
    reference_price_unit: OpaqueIdentifier | None = None
    reference_price_at: datetime | None = None
    reference_available_at: datetime | None = None

    annualization_method: OpaqueIdentifier | None = None
    expiry: datetime | None = None
    provider_methodology_ref: OpaqueIdentifier | None = None

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
    def _cross_venue_law(self) -> BasisObservationInput:
        if self.spot_reference_venue != self.venue:
            raise ValueError(
                f"spot reference venue {self.spot_reference_venue!r} differs from the "
                f"futures venue {self.venue!r}: cross-venue synthesis is not a T1 "
                "basis (04 section 9)"
            )
        if self.spot_reference == self.futures_reference:
            raise ValueError(
                "spot_reference and futures_reference must identify different "
                "instruments: a basis against itself is not a basis"
            )
        return self

    @model_validator(mode="after")
    def _annualization_law(self) -> BasisObservationInput:
        if self.basis_unit is BasisUnit.ANNUALIZED_PERCENT:
            if self.annualization_method is None:
                raise ValueError(
                    "basis_unit=ANNUALIZED_PERCENT requires annualization_method: an "
                    "annualized reading without its method cannot be compared with "
                    "any other basis (04 section 9)"
                )
        elif self.annualization_method is not None:
            raise ValueError(
                "annualization_method requires basis_unit=ANNUALIZED_PERCENT: an "
                "annualization method on a raw reading is a unit substitution"
            )
        return self

    @model_validator(mode="after")
    def _reference_shape_law(self) -> BasisObservationInput:
        if self.reference_price is not None and self.reference_price <= 0:
            raise ValueError("reference_price must be positive when supplied")
        if self.reference_price is not None and self.reference_price_type is None:
            raise ValueError(
                "a supplied reference price requires its frozen reference type: an "
                "untyped reference is a substitution waiting to happen "
                "(bloc_05/03 section 8)"
            )
        return self

    @model_validator(mode="after")
    def _unique_refs(self) -> BasisObservationInput:
        for name in ("raw_projection_refs", "acquisition_refs", "evidence_blob_hashes"):
            values = getattr(self, name)
            if len(set(values)) != len(values):
                raise ValueError(f"{name} contains duplicate references")
        return self


class T1BasisRecord(T1BaseEnvelope):
    """Basis T1 record (04 section 9).

    Carries the reference identity and the comparability verdict.  ``basis_comparable``
    is a boolean about EVIDENCE sufficiency, not a computed value: no bps, no
    annualized number and no cross-venue number is minted here.
    """

    basis_value_native: Decimal
    basis_unit: BasisUnit

    futures_reference: OpaqueIdentifier
    spot_reference: OpaqueIdentifier
    spot_reference_venue: OpaqueIdentifier

    reference_price_type: ReferencePriceType | None = None
    reference_price_unit: OpaqueIdentifier | None = None
    reference_price_at: datetime | None = None
    reference_available_at: datetime | None = None
    reference_price_ref: OpaqueIdentifier | None = None

    annualization_method: OpaqueIdentifier | None = None
    expiry: datetime | None = None
    provider_methodology_ref: OpaqueIdentifier | None = None

    basis_comparable: bool
    reference_refusal: BasisReferenceRefusal | None = None

    @model_validator(mode="after")
    def _sensor_family_law(self) -> T1BasisRecord:
        if self.sensor_family is not SensorFamily.MECHANICAL_BASIS:
            raise ValueError(
                "T1BasisRecord requires sensor_family=MECHANICAL_BASIS, got "
                f"{self.sensor_family.value}"
            )
        return self

    @model_validator(mode="after")
    def _comparability_law(self) -> T1BasisRecord:
        if self.basis_comparable == (self.reference_refusal is not None):
            raise ValueError(
                "basis_comparable must be exactly 'no refusal': a comparable basis "
                "was not refused and a refused basis is not comparable"
            )
        if not self.basis_comparable:
            return self
        if self.basis_unit is BasisUnit.ABSOLUTE_PRICE and self.reference_price_type is None:
            raise ValueError(
                "an ABSOLUTE_PRICE basis is comparable only against a typed "
                "reference price (04 section 9)"
            )
        if self.basis_unit is BasisUnit.ANNUALIZED_PERCENT and self.annualization_method is None:
            raise ValueError(
                "an ANNUALIZED_PERCENT basis is comparable only with its "
                "annualization method"
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


def _reference_verdict(
    payload: BasisObservationInput,
    *,
    knowledge_cutoff: datetime | None,
) -> BasisReferenceRefusal | None:
    """The reference-price ladder.  Returns the FIRST clause that fails."""
    if payload.reference_price is None:
        return BasisReferenceRefusal.NOT_SUPPLIED
    if payload.reference_price_type not in _APPROVED_REFERENCE_TYPES:
        return BasisReferenceRefusal.TYPE_NOT_APPROVED
    if payload.reference_available_at is None:
        return BasisReferenceRefusal.NO_REFERENCE_AVAILABILITY
    if knowledge_cutoff is not None and payload.reference_available_at > knowledge_cutoff:
        return BasisReferenceRefusal.LATE_REFERENCE
    if payload.basis_unit is BasisUnit.ABSOLUTE_PRICE:
        if payload.reference_price_unit is None:
            return BasisReferenceRefusal.UNIT_MISMATCH
    return None


def normalize_basis(
    payload: BasisObservationInput,
    *,
    knowledge_cutoff: datetime | None = None,
) -> T1BasisRecord:
    """Normalize one basis observation.  Pure, deterministic, fail-closed."""
    coverage_ok = payload.source_coverage_state in (
        CoverageState.COMPLETE_SOURCE_BOUNDARY,
        CoverageState.EMPTY_CONFIRMED,
    )
    refusal = _reference_verdict(payload, knowledge_cutoff=knowledge_cutoff)

    flags: set[NormalizationQualityFlag] = {
        NormalizationQualityFlag.SEMANTICS_UNVERIFIED,
        NormalizationQualityFlag.LINEAGE_COMPLETE,
    }
    if refusal is BasisReferenceRefusal.LATE_REFERENCE:
        flags.add(NormalizationQualityFlag.PIT_LATE_CORRECTION)
        flags.add(NormalizationQualityFlag.REFERENCE_PRICE_UNAVAILABLE)
    elif refusal is not None:
        flags.add(NormalizationQualityFlag.REFERENCE_PRICE_UNAVAILABLE)
    if payload.provider_methodology_ref is None:
        flags.add(NormalizationQualityFlag.SEMANTICS_UNVERIFIED)
    if payload.native_basis_id is None:
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

    return T1BasisRecord(
        sensor_family=SensorFamily.MECHANICAL_BASIS,
        provider=payload.provider,
        venue=payload.venue,
        native_instrument=payload.native_instrument,
        provider_instrument_id=payload.provider_instrument_id,
        native_event_id=payload.native_basis_id,
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
        ),
        native_values=(
            NativeQuantity(
                native_field_name="basis_value",
                native_value=payload.basis_value_native,
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
        basis_value_native=payload.basis_value_native,
        basis_unit=payload.basis_unit,
        futures_reference=payload.futures_reference,
        spot_reference=payload.spot_reference,
        spot_reference_venue=payload.spot_reference_venue,
        reference_price_type=payload.reference_price_type,
        reference_price_unit=payload.reference_price_unit,
        reference_price_at=payload.reference_price_at,
        reference_available_at=payload.reference_available_at,
        reference_price_ref=None,
        annualization_method=payload.annualization_method,
        expiry=payload.expiry,
        provider_methodology_ref=payload.provider_methodology_ref,
        basis_comparable=refusal is None,
        reference_refusal=refusal,
    )
