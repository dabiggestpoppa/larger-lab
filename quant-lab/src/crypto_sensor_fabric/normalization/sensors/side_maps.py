"""SENSOR-B5-I10E1 - Binance side adapter + provider-neutral side evidence.

The I10 realization of ``BLOC_05_I10D1_DECISION_PACKAGE.md`` section 1.4 and
section 9.2: ONE pure mapping algorithm, ONE registry authority (the I09
``ProviderSemanticRegistry``), and a provisional-versus-admitted split that the
type system enforces rather than documents.

Three boundaries are structural, not conventional:

1. **No second registry.**  This module mints no methodology id, writes no
   configuration and holds no confidence authority.  Every semantic fact is
   read from the I09-owned registry row it is handed
   (:class:`~crypto_sensor_fabric.normalization.common.semantic_registry.ProviderSemanticRegistry`),
   and the confidence is *read* from that row, never assigned here.
2. **Provisional is a different type.**  :class:`ProvisionalSideMapping` is what
   this module returns.  It is deliberately not an ``AggressorSide``: while the
   registry row's evidence reference is still ``BLOC2_PROBE_PENDING`` the I09
   confidence is ``AMBIGUOUS``, ``admits_critical_t1_use`` is ``False``, and
   ``canonical_admitted`` is ``False``.  A caller therefore cannot reach the
   canonical field by holding the mapped value alone.
3. **Refusal is silent-free.**  :func:`apply_side_map` returns ``None`` rather
   than a guess, and :func:`require_side_mapping` raises the typed
   :class:`UnsupportedSideMappingError`.  No path here consults direction,
   momentum or any other market observation: schema rule B1-T10 and bloc_05/07
   F17 forbid inferring an aggressor from how the tape moved, so the workbook
   of inputs is deliberately limited to the provider's own declared boolean.

Frozen direction (operator repair SENSOR-B1-R01, bloc_05/04 section 2.2)::

    isBuyerMaker = true  -> buyer is maker  -> seller is taker -> SELL
    isBuyerMaker = false -> buyer is taker                      -> BUY

The same direction is pinned by ``providers/binance/probe.py``; production code
must not import that package (the forbidden-import firewall of every Bloc 5
scope audit), so the one-line rule lives here and a pin-consistency test asserts
the two never diverge.

Provider scope (ruling R4): Binance USD-M is the only venue with a declared rule.
Every other member of the frozen eight-provider schema resolves to ``None`` --
a provider's field name never transfers its polarity to another venue, and no
other venue is characterized by this checkpoint.

No network, no wall clock, no filesystem: evidence in, answer out.
"""

from __future__ import annotations

from enum import Enum
from typing import Callable

from pydantic import model_validator

from ...contracts.enums import AggressorSide, SemanticEquivalence, SensorFamily
from ..common.methodologies import MethodologyRef
from ..common.semantic_registry import (
    ProviderSemanticMapping,
    ProviderSemanticRegistry,
    SemanticConfidence,
    admits_critical_t1_use,
)
from ..models import NormalizationModelBase, OpaqueIdentifier

__all__ = [
    "BINANCE_IS_BUYER_MAKER_METHODOLOGY_ID",
    "BINANCE_PROVIDER_ID",
    "ProvisionalSideMapping",
    "SideEvidence",
    "SideEvidenceKind",
    "SideMappingStatus",
    "UnsupportedSideMappingError",
    "admit_aggressor_side",
    "apply_declared_side_transformation",
    "apply_side_map",
    "binance_side_from_is_buyer_maker",
    "require_side_mapping",
    "resolve_side_mapping",
]


class _StrEnum(str, Enum):
    """Deterministic string-valued enum base (values equal member names)."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


#: The venue this checkpoint characterizes.  A string constant, not an enum
#: member: provider tokens are registry-controlled in this repository and
#: ``contracts.enums`` deliberately keeps them out of enums.
BINANCE_PROVIDER_ID = "BINANCE_USDM"

#: The Bloc 1 methodology identity the adapter must cite verbatim.  Read from
#: ``config/crypto_sensor_fabric/methodology_registry.yaml`` (status
#: ``PROVISIONAL``); citing is not minting, and the registry row is the authority.
BINANCE_IS_BUYER_MAKER_METHODOLOGY_ID = "AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1"


class UnsupportedSideMappingError(LookupError):
    """Raised instead of guessing when a certified side is required.

    ``LookupError`` rather than a bare exception so a caller that swallows it
    still has a typed, specific failure: the request asked for a declared
    mapping that does not exist (bloc_05/06 section 1 G9 fail-closed).
    """


class SideEvidenceKind(_StrEnum):
    """The three exclusive states of provider-side evidence (section 4.2(a)).

    Frozen by the decision package, not by a Bloc 5 planning document, so the
    members are named exactly as the package names them::

        PROVIDER_BOOLEAN_FIELD    structurally present, a declared field
        SIDE_FIELD_ABSENT         the provider exposes no side-bearing field
        SIDE_SEMANTICS_UNDECLARED a field exists but no row declares it

    The third state exists so an undeclared field is reported as undeclared
    rather than downgraded to "absent" -- the two are different facts and
    merging them would hide a registry gap.
    """

    PROVIDER_BOOLEAN_FIELD = "PROVIDER_BOOLEAN_FIELD"
    SIDE_FIELD_ABSENT = "SIDE_FIELD_ABSENT"
    SIDE_SEMANTICS_UNDECLARED = "SIDE_SEMANTICS_UNDECLARED"


class SideMappingStatus(_StrEnum):
    """The two acceptance layers, kept apart (decision package section 2.2).

    ``BEHAVIORALLY_IMPLEMENTED`` means the pure transformation exists, is
    deterministic and is fixture-tested: arithmetic, not semantics.
    ``PROVIDER_SEMANTICALLY_VERIFIED`` means provider-grade evidence moved the
    I09 confidence off ``AMBIGUOUS``.  Only the second may reach a critical T1
    field, and it is unreachable while the evidence reference is pending.
    """

    BEHAVIORALLY_IMPLEMENTED = "BEHAVIORALLY_IMPLEMENTED"
    PROVIDER_SEMANTICALLY_VERIFIED = "PROVIDER_SEMANTICALLY_VERIFIED"


class SideEvidence(NormalizationModelBase):
    """Provider-neutral source-side evidence (decision package section 4.2(a)).

    An algebraic-data-type-shaped record: exactly one of the three states, and
    the fields each state is allowed to carry.  The validators make a
    contradictory combination unrepresentable, which is why the normalizer never
    has to ask whether a missing boolean "really" means absent.

    ``provider`` is optional and, when present, is compared against the mapping
    row's provider before the rule is applied -- that comparison is what stops
    one venue's declared polarity from being applied to another venue's payload.
    """

    kind: SideEvidenceKind
    provider: OpaqueIdentifier | None = None
    provider_field: OpaqueIdentifier | None = None
    boolean_value: bool | None = None

    # -- constructors -----------------------------------------------------

    @classmethod
    def provider_boolean(
        cls, provider_field: str, boolean_value: bool, *, provider: str | None = None
    ) -> SideEvidence:
        return cls(
            kind=SideEvidenceKind.PROVIDER_BOOLEAN_FIELD,
            provider_field=provider_field,
            boolean_value=boolean_value,
            provider=provider,
        )

    @classmethod
    def field_absent(cls, *, provider: str | None = None) -> SideEvidence:
        return cls(kind=SideEvidenceKind.SIDE_FIELD_ABSENT, provider=provider)

    @classmethod
    def semantics_undeclared(
        cls, provider_field: str, *, provider: str | None = None
    ) -> SideEvidence:
        return cls(
            kind=SideEvidenceKind.SIDE_SEMANTICS_UNDECLARED,
            provider_field=provider_field,
            provider=provider,
        )

    # -- laws -------------------------------------------------------------

    @model_validator(mode="after")
    def _state_laws(self) -> SideEvidence:
        if self.kind is SideEvidenceKind.PROVIDER_BOOLEAN_FIELD:
            if self.provider_field is None:
                raise ValueError(
                    "PROVIDER_BOOLEAN_FIELD requires the provider field name; a "
                    "boolean without its field cannot be mapped"
                )
            if self.boolean_value is None:
                raise ValueError(
                    "PROVIDER_BOOLEAN_FIELD requires the observed boolean; absence "
                    "is SIDE_FIELD_ABSENT, never a missing value on a present field"
                )
            return self
        if self.boolean_value is not None:
            raise ValueError(
                f"{self.kind.value} must not carry a boolean value; the field is "
                "not structurally present, so no value can have been observed"
            )
        if self.kind is SideEvidenceKind.SIDE_FIELD_ABSENT and self.provider_field is not None:
            raise ValueError(
                "SIDE_FIELD_ABSENT must not name a field; use "
                "SIDE_SEMANTICS_UNDECLARED when a field exists but is undeclared"
            )
        if self.kind is SideEvidenceKind.SIDE_SEMANTICS_UNDECLARED and self.provider_field is None:
            raise ValueError(
                "SIDE_SEMANTICS_UNDECLARED requires the undeclared field name"
            )
        return self


class ProvisionalSideMapping(NormalizationModelBase):
    """Behaviourally computed side, held OUTSIDE the canonical field.

    This type is the operator ruling R2 made structural.  It exists so that
    "the adapter computed SELL" and "the canonical aggressor was SELL" are two
    different statements in the type system, not two readings of one field:

    * ``mapped_side`` is the frozen behavioural result.
    * ``semantic_confidence`` is READ from the I09 registry row.
    * ``status`` names which acceptance layer applies.
    * ``canonical_admitted`` is the single boolean the normalizer consults, and
      it is ``False`` for every provisional row.

    ``evidence_reference`` is carried so a reader can see *why* layer 2 is
    unearned without consulting the registry again -- for the live Binance row
    it is the pending token, not a citation.
    """

    provider: OpaqueIdentifier
    provider_field: OpaqueIdentifier
    mapped_side: AggressorSide
    semantic_confidence: SemanticConfidence
    methodology_ref: MethodologyRef
    evidence_reference: OpaqueIdentifier | None = None
    status: SideMappingStatus
    canonical_admitted: bool
    rule_id: OpaqueIdentifier

    @model_validator(mode="after")
    def _admission_law(self) -> ProvisionalSideMapping:
        if self.mapped_side is AggressorSide.UNKNOWN:
            raise ValueError(
                "a provisional mapping must carry a computed side; UNKNOWN is the "
                "absence of a mapping, not a mapping result"
            )
        expected = admits_critical_t1_use(self.semantic_confidence)
        if self.canonical_admitted != expected:
            raise ValueError(
                "canonical_admitted must equal admits_critical_t1_use("
                f"{self.semantic_confidence.value}) = {expected}; admission is a "
                "property of the provider-evidence ladder, never a caller choice"
            )
        verified = self.status is SideMappingStatus.PROVIDER_SEMANTICALLY_VERIFIED
        if verified != self.canonical_admitted:
            raise ValueError(
                f"status={self.status.value} contradicts "
                f"canonical_admitted={self.canonical_admitted}: only a "
                "provider-semantically-verified mapping may be admitted"
            )
        return self


def _binance_is_buyer_maker(value: bool) -> AggressorSide:
    """Frozen direction, operator repair SENSOR-B1-R01 (bloc_05/04 section 2.2)."""
    return AggressorSide.SELL if value else AggressorSide.BUY


def binance_side_from_is_buyer_maker(value: bool) -> AggressorSide:
    """Public form of the frozen Binance direction, for pin-consistency checks.

    Exposing it lets a test assert the adapter and
    ``providers/binance/probe.py::aggressor_side_from_is_buyer_maker`` agree on
    both booleans without production code importing the provider package.
    """
    return _binance_is_buyer_maker(value)


#: The declared behavioural rule table, keyed by ``(provider, provider_field)``.
#: One entry: Binance USD-M ``isBuyerMaker``.  Adding a venue is one row here
#: plus an I09-b semantic record -- never a change to the normalizer
#: (decision package section 4.2(d)).
_SIDE_RULES: dict[tuple[str, str], tuple[str, Callable[[bool], AggressorSide]]] = {
    (BINANCE_PROVIDER_ID, "isBuyerMaker"): (
        "BINANCE_IS_BUYER_MAKER_R01",
        _binance_is_buyer_maker,
    ),
}


def resolve_side_mapping(
    registry: ProviderSemanticRegistry,
    provider: str,
    provider_field: str,
    family: SensorFamily,
) -> ProviderSemanticMapping | None:
    """The declared I09 row for one field, or ``None`` -- never a default.

    A thin, explicit wrapper over the I09 registry lookup so this module has no
    resolution logic of its own: the key is
    ``(provider, provider_field, sensor_family)`` and an absent row stays
    absent (bloc_05/03 section 12; readiness stop 7).
    """
    return registry.resolve(provider, provider_field, family)


def require_side_mapping(
    registry: ProviderSemanticRegistry,
    provider: str,
    provider_field: str,
    family: SensorFamily,
) -> ProviderSemanticMapping:
    """Strict form: refuse loudly instead of returning ``None``.

    A caller that requires a certified mapping gets a typed refusal here rather
    than an ``AttributeError`` later (decision package section 4.2(c): refusal
    is explicit, not silent).
    """
    row = resolve_side_mapping(registry, provider, provider_field, family)
    if row is None:
        raise UnsupportedSideMappingError(
            f"no declared side mapping for provider={provider!r} "
            f"provider_field={provider_field!r} sensor_family={family.value!r}; "
            "an undeclared mapping is never inferred from another venue's rule "
            "or from market direction (bloc_05/06 section 1 G9, bloc_05/07 F17)"
        )
    return row


def apply_side_map(
    evidence: SideEvidence, mapping: ProviderSemanticMapping | None
) -> ProvisionalSideMapping | None:
    """Apply the declared rule, or return ``None``.

    Fail-closed in order, and every exit is a *stated* refusal:

    1. no declared row -> ``None`` (the field is not characterized);
    2. a ``NOT_COMPARABLE`` row -> ``None`` (the registry says the two fields are
       not comparable, so applying a rule would contradict it);
    3. no ``methodology_id`` -> ``None`` (a computed side that cannot be cited
       cannot enter lineage, so it is not computed);
    4. the evidence is not a structurally present boolean -> ``None``;
    5. the evidence's field or provider disagrees with the row -> ``None`` (no
       cross-field and no cross-venue fill);
    6. the venue has no declared rule -> ``None`` (ruling R4: no extrapolation);
    7. otherwise the frozen rule, the row's confidence READ verbatim, and a
       :class:`ProvisionalSideMapping` whose ``canonical_admitted`` follows the
       I09 ladder.

    Returns ``None`` for every refusal.  The canonical aggressor side is never
    an output of this function.
    """
    if mapping is None:
        return None
    if mapping.semantic_equivalence_class is SemanticEquivalence.NOT_COMPARABLE:
        return None
    if mapping.methodology_id is None:
        return None
    if evidence.kind is not SideEvidenceKind.PROVIDER_BOOLEAN_FIELD:
        return None
    if evidence.provider_field != mapping.provider_field:
        return None
    if evidence.provider is not None and evidence.provider != mapping.provider:
        return None
    if evidence.boolean_value is None:  # pragma: no cover - model forbids it
        return None
    rule = _SIDE_RULES.get((mapping.provider, mapping.provider_field))
    if rule is None:
        return None
    rule_id, transform = rule
    mapped = transform(evidence.boolean_value)
    confidence = mapping.semantic_confidence
    admitted = admits_critical_t1_use(confidence)
    return ProvisionalSideMapping(
        provider=mapping.provider,
        provider_field=mapping.provider_field,
        mapped_side=mapped,
        semantic_confidence=confidence,
        methodology_ref=MethodologyRef(
            methodology_id=mapping.methodology_id, version=mapping.version
        ),
        evidence_reference=mapping.evidence_reference,
        status=(
            SideMappingStatus.PROVIDER_SEMANTICALLY_VERIFIED
            if admitted
            else SideMappingStatus.BEHAVIORALLY_IMPLEMENTED
        ),
        canonical_admitted=admitted,
        rule_id=rule_id,
    )


def apply_declared_side_transformation(
    mapping: ProviderSemanticMapping | None, native_value: object
) -> AggressorSide | None:
    """Re-execute the DECLARED rule for this row, or refuse by returning ``None``.

    SENSOR-B5-I09P2c needs an EXECUTABLE transformation: the row's
    ``transformation`` prose describes a mapping, it does not prove a record
    follows one.  This is the only sanctioned way to recompute a canonical side
    from a preserved native value, and it refuses unless a mechanical rule is
    declared for the exact ``(provider, provider_field)`` with the frozen
    methodology identity:

    * another sensor family, or a canonical field other than ``aggressor_side``
      -> ``None`` (a liquidation side domain is provider semantics this
      checkpoint has no executable rule for);
    * a ``NOT_COMPARABLE`` row -> ``None``;
    * a methodology other than the frozen Binance adapter -> ``None``;
    * a native value that is not the declared boolean -> ``None``.

    Nothing is inferred from tape direction, momentum or another venue's rule
    (bloc_05/06 section 1 G9, bloc_05/07 F17): an absent rule stays absent.
    """
    if mapping is None:
        return None
    if mapping.canonical_sensor is not SensorFamily.MECHANICAL_TRADE:
        return None
    if mapping.canonical_field != "aggressor_side":
        return None
    if mapping.semantic_equivalence_class is SemanticEquivalence.NOT_COMPARABLE:
        return None
    if mapping.methodology_id != BINANCE_IS_BUYER_MAKER_METHODOLOGY_ID:
        return None
    rule = _SIDE_RULES.get((mapping.provider, mapping.provider_field))
    if rule is None:
        return None
    if not isinstance(native_value, bool):
        return None
    _, transform = rule
    return transform(native_value)


def admit_aggressor_side(side: AggressorSide, confidence: SemanticConfidence) -> bool:
    """May this side occupy a critical T1 field?  (bloc_05/03 section 13)

    Two conjuncts, both required: the side must be an actual direction (an
    ``UNKNOWN`` is never "admitted"), and the confidence must clear the I09
    critical-use ladder.  Thin by design -- the ladder itself is I09's.
    """
    if side is AggressorSide.UNKNOWN:
        return False
    return admits_critical_t1_use(confidence)
