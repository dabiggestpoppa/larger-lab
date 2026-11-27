"""SENSOR-B5-WAVE1 - shared semantic-admission and derived-amount surface.

Wave 1 (I12-I15) adds four sensor families that all face the same two
record-construction problems, so this module solves each of them ONCE:

1. **Semantic admission.**  Whether a provider field really means what a row
   claims it means is an I09 ``ProviderSemanticMapping`` question, decided by the
   evidence ladder and the trusted approval root -- never by the caller.  I10
   established that pattern for one trading side
   (``sensors/side_maps.py``); I11 generalized it to four liquidation fields but
   kept the helper private to its own module.  I12-I15 need the same ladder, so
   it lives here rather than being copied four times.

2. **Derived-amount carriers.**  ``DerivedAmount`` (value + unit + methodology +
   version + consumed-input lineage, or a typed absence) was introduced at I10.
   It is unchanged and is RE-USED, not re-declared; the two constructors here
   simply make "blocked because unresolved" and "lift an accepted I04B result"
   one line at every call site.

What this module deliberately is NOT: a registry, a methodology authority, a
conversion engine, a calibration table, or a second copy of any frozen
vocabulary.  Every semantic fact is read from the registry row it is handed; the
confidence rung is read, never supplied.

Ownership (mission section 3): this is the explicitly authorized shared surface
for the Wave 1 normalizers.  It is producer-owned here; the independent audit
lane resolves the same I09 rows with its own reader and does not import this
module, so a defect here cannot be hidden by a shared helper on both sides.

The refusal vocabulary is family-neutral and duplicated from
``liquidation.py``'s ``LiquidationAdmissionRefusal`` on purpose: that checkpoint
is ratified and audited, and re-pointing its enum at a Wave 1 module would edit
sealed history for no behavioural gain.  The two enumerations answer the same
question, and a Wave 1 scope audit pins the correspondence member by member.

No network, no wall clock, no filesystem, no id generation: evidence in, answer
out.
"""

from __future__ import annotations

from enum import Enum

from pydantic import model_validator

from ...contracts.enums import SemanticEquivalence, SensorFamily
from ..authority import SemanticAuthority
from ..common.semantic_registry import (
    PENDING_EVIDENCE_REFERENCE,
    ProviderSemanticMapping,
    ProviderSemanticRegistry,
    SemanticConfidence,
    admits_critical_t1_use,
)
from ..enums import _FLAG_ORDER, MissingnessReason, NormalizationQualityFlag
from ..models import NormalizationModelBase, OpaqueIdentifier
from ..terms.conversion import ConversionResult
from .trade import I04B_METHODOLOGY_ID, I08_UNITS_METHODOLOGY_ID, DerivedAmount

__all__ = [
    "I04B_METHODOLOGY_ID",
    "I08_UNITS_METHODOLOGY_ID",
    "SensorAdmissionRefusal",
    "SensorFieldAdmission",
    "admit_sensor_field",
    "amount_from_conversion",
    "blocked_amount",
    "canonical_flags",
]


class _StrEnum(str, Enum):
    """Deterministic string-valued enum base (values equal member names)."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class SensorAdmissionRefusal(_StrEnum):
    """Why one canonical field stayed out of its canonical slot (fail-closed).

    Every member is a *stated* cause, so a provisional reading is never merely
    absent: the record says which link of the evidence chain was missing.  The
    membership matches ``LiquidationAdmissionRefusal`` member for member, plus
    the one case liquidation never needed (``CORROBORATION_ONLY_MAPPING``), which
    Wave 1 does need because book metrics and basis references are routinely
    declared corroboration-only.
    """

    #: The reading was supplied with no native provider field naming its source.
    NO_NATIVE_FIELD = "NO_NATIVE_FIELD"
    #: No registry was supplied, so there is no semantic authority at all.
    NO_REGISTRY = "NO_REGISTRY"
    #: The registry declares no row for (provider, field, sensor family).
    NO_REGISTRY_MAPPING = "NO_REGISTRY_MAPPING"
    #: The row's provider is not the payload's provider (defence in depth).
    PROVIDER_MISMATCH = "PROVIDER_MISMATCH"
    #: The row declares the fields not comparable at all.
    NOT_COMPARABLE_MAPPING = "NOT_COMPARABLE_MAPPING"
    #: The row is corroboration-only: usable as evidence, not as an equivalence.
    CORROBORATION_ONLY_MAPPING = "CORROBORATION_ONLY_MAPPING"
    #: The row maps this provider field to a DIFFERENT canonical field.
    FIELD_MISMATCH = "FIELD_MISMATCH"
    #: The row cites no methodology, so a promoted value could not enter lineage.
    UNCITABLE_METHODOLOGY = "UNCITABLE_METHODOLOGY"
    #: The evidence reference is absent or still the pending probe token.
    PENDING_EVIDENCE = "PENDING_EVIDENCE"
    #: 03 section 13: ``AMBIGUOUS`` blocks use in critical T1 fields.
    AMBIGUOUS_MAPPING = "AMBIGUOUS_MAPPING"
    #: The provider's own readings contradict each other.
    CONTRADICTION = "CONTRADICTION"
    #: No trusted approval context was supplied: a registry SHAPE is not authority
    #: (SENSOR-B5-I09P2A).  A caller-minted registry admits nothing.
    UNTRUSTED_AUTHORITY = "UNTRUSTED_AUTHORITY"
    #: A trusted authority exists but does not cover this row.
    NOT_APPROVED_BY_AUTHORITY = "NOT_APPROVED_BY_AUTHORITY"


class SensorFieldAdmission(NormalizationModelBase):
    """One canonical field's admission decision, with its full evidence chain.

    The record-level replacement for a caller boolean: it carries the registry
    row's identity (provider field, methodology, version, equivalence class),
    the row's semantic confidence READ verbatim, and the non-pending evidence
    reference -- so "admitted" and "refused, for this reason" are both auditable
    facts.

    The model's own law is what makes a caller assertion useless: an admitted
    row MUST name a confidence, an evidence reference, a citable methodology, a
    mapping version and the approving authority, and may not be ``AMBIGUOUS``,
    ``CORROBORATION_ONLY`` or cite the pending token.
    """

    sensor_family: SensorFamily
    canonical_field: OpaqueIdentifier
    provider_field: OpaqueIdentifier | None = None
    provisional_value: OpaqueIdentifier
    semantic_equivalence_class: SemanticEquivalence | None = None
    semantic_confidence: SemanticConfidence | None = None
    evidence_reference: OpaqueIdentifier | None = None
    methodology_id: OpaqueIdentifier | None = None
    mapping_version: OpaqueIdentifier | None = None
    admitted: bool
    refusal: SensorAdmissionRefusal | None = None
    #: The approving authority, when one issued this decision (SENSOR-B5-I09P2A).
    #: Provenance EVIDENCE, not an authenticated signature.
    admission_approval_id: OpaqueIdentifier | None = None
    admission_registry_digest: OpaqueIdentifier | None = None

    @model_validator(mode="after")
    def _admission_laws(self) -> SensorFieldAdmission:
        if self.admitted == (self.refusal is not None):
            raise ValueError(
                "admitted must be exactly 'no refusal': an admitted field was not "
                "refused and a refused field was not admitted"
            )
        if not self.admitted:
            return self
        missing = [
            name
            for name in (
                "provider_field",
                "semantic_equivalence_class",
                "semantic_confidence",
                "evidence_reference",
                "methodology_id",
                "mapping_version",
            )
            if getattr(self, name) is None
        ]
        if missing:
            raise ValueError(
                "an admitted canonical field requires "
                f"{', '.join(missing)}: admission is a property of the provider "
                "evidence ladder, never a caller choice (bloc_05/03 section 13)"
            )
        if self.semantic_confidence is SemanticConfidence.AMBIGUOUS:
            raise ValueError(
                "an AMBIGUOUS mapping cannot admit a critical T1 field "
                "(bloc_05/03 section 13)"
            )
        if self.semantic_equivalence_class is SemanticEquivalence.CORROBORATION_ONLY:
            raise ValueError(
                "a CORROBORATION_ONLY mapping is evidence, not an equivalence, so "
                "it cannot admit a canonical field (bloc_05/04 sections 7 and 9)"
            )
        if self.semantic_equivalence_class is SemanticEquivalence.NOT_COMPARABLE:
            raise ValueError(
                "a NOT_COMPARABLE mapping cannot admit a canonical field"
            )
        if self.evidence_reference == PENDING_EVIDENCE_REFERENCE:
            raise ValueError(
                f"an admitted field cannot cite {PENDING_EVIDENCE_REFERENCE}: a "
                "provisional mapping is not a verified mapping (BOOK 00 Q7)"
            )
        if self.admission_approval_id is None or self.admission_registry_digest is None:
            raise ValueError(
                "an admitted canonical field must name the approving authority "
                "(approval id and registry digest): model validity is not upstream "
                "authorization (SENSOR-B5-I09P2A)"
            )
        return self


def admit_sensor_field(
    *,
    sensor_family: SensorFamily,
    canonical_field: str,
    provisional_value: str,
    provider: str,
    provider_field: str | None,
    registry: ProviderSemanticRegistry | None,
    authority: SemanticAuthority | None,
    contradiction: bool = False,
) -> SensorFieldAdmission:
    """Resolve ONE canonical field's authority.  Never guesses, never widens.

    The order is the evidence chain, so the recorded refusal names the FIRST
    missing link: contradiction, source field, registry, row, provider,
    equivalence class, declared canonical field, citable methodology,
    non-pending evidence, the frozen confidence ladder, then the approval root
    that decides whether a row that MAY admit actually DID.

    Nothing here reads a clock, a network or a default, and the confidence rung
    is read from the row rather than accepted as an argument.
    """

    def refused(reason: SensorAdmissionRefusal) -> SensorFieldAdmission:
        return SensorFieldAdmission(
            sensor_family=sensor_family,
            canonical_field=canonical_field,
            provider_field=provider_field,
            provisional_value=provisional_value,
            admitted=False,
            refusal=reason,
        )

    if contradiction:
        return refused(SensorAdmissionRefusal.CONTRADICTION)
    if provider_field is None:
        return refused(SensorAdmissionRefusal.NO_NATIVE_FIELD)
    if registry is None:
        return refused(SensorAdmissionRefusal.NO_REGISTRY)
    row: ProviderSemanticMapping | None = registry.resolve(
        provider, provider_field, sensor_family
    )
    if row is None:
        return refused(SensorAdmissionRefusal.NO_REGISTRY_MAPPING)
    if row.provider != provider:  # pragma: no cover - resolve() already filters
        return refused(SensorAdmissionRefusal.PROVIDER_MISMATCH)
    if row.semantic_equivalence_class is SemanticEquivalence.NOT_COMPARABLE:
        return refused(SensorAdmissionRefusal.NOT_COMPARABLE_MAPPING)
    if row.semantic_equivalence_class is SemanticEquivalence.CORROBORATION_ONLY:
        return refused(SensorAdmissionRefusal.CORROBORATION_ONLY_MAPPING)
    if row.canonical_field != canonical_field:
        return refused(SensorAdmissionRefusal.FIELD_MISMATCH)
    if row.methodology_id is None:
        return refused(SensorAdmissionRefusal.UNCITABLE_METHODOLOGY)
    if (
        row.evidence_reference is None
        or row.evidence_reference == PENDING_EVIDENCE_REFERENCE
    ):
        return refused(SensorAdmissionRefusal.PENDING_EVIDENCE)
    if not admits_critical_t1_use(row.semantic_confidence):
        return refused(SensorAdmissionRefusal.AMBIGUOUS_MAPPING)
    # The chain above decides whether this row MAY admit; the approval decides
    # whether it DID.  A registry the caller minted reaches this point and stops.
    if authority is None:
        return refused(SensorAdmissionRefusal.UNTRUSTED_AUTHORITY)
    if authority.attests(row) is not None:
        return refused(SensorAdmissionRefusal.NOT_APPROVED_BY_AUTHORITY)
    return SensorFieldAdmission(
        sensor_family=sensor_family,
        canonical_field=canonical_field,
        provider_field=provider_field,
        provisional_value=provisional_value,
        semantic_equivalence_class=row.semantic_equivalence_class,
        semantic_confidence=row.semantic_confidence,
        evidence_reference=row.evidence_reference,
        methodology_id=row.methodology_id,
        mapping_version=row.version,
        admitted=True,
        admission_approval_id=authority.approval_id,
        admission_registry_digest=authority.registry_digest,
    )


def blocked_amount(
    methodology_id: str,
    methodology_version: str,
    reason: MissingnessReason,
    *,
    unresolved_citation: str | None = None,
    output_unit: str | None = None,
) -> DerivedAmount:
    """A typed absence: no value, its cause, and the methodology that owes it."""
    return DerivedAmount(
        value=None,
        blocked=True,
        missingness_reason=reason,
        methodology_id=methodology_id,
        methodology_version=methodology_version,
        output_unit=output_unit,
        conversion_lineage_refs=(),
        unresolved_citation=unresolved_citation,
    )


def amount_from_conversion(
    result: ConversionResult,
    *,
    methodology_id: str = I04B_METHODOLOGY_ID,
) -> DerivedAmount:
    """Lift an accepted I04B result into a :class:`DerivedAmount`.

    Both branches are carried VERBATIM: a successful primitive contributes its
    value, output unit and consumed-input lineage; a refused one contributes its
    typed absence and NO consumed inputs, exactly as I04B itself decided.  This
    function adds no arithmetic of its own, which is why it takes the result
    object rather than the numbers.
    """
    if result.normalized_value is None:
        return blocked_amount(
            methodology_id=methodology_id,
            methodology_version=result.methodology_version,
            reason=MissingnessReason.CONVERSION_BLOCKED,
        )
    return DerivedAmount(
        value=result.normalized_value,
        blocked=False,
        missingness_reason=None,
        methodology_id=methodology_id,
        methodology_version=result.methodology_version,
        output_unit=result.output_unit,
        conversion_lineage_refs=tuple(result.conversion_inputs),
        unresolved_citation=None,
    )


def canonical_flags(
    flags: set[NormalizationQualityFlag],
) -> tuple[NormalizationQualityFlag, ...]:
    """Canonical, duplicate-free flag ordering the base envelope requires."""
    return tuple(sorted(flags, key=_FLAG_ORDER.__getitem__))
