"""SENSOR-B5-I09 - the frozen ``ProviderSemanticMapping`` registry (03 §11-§13).

The I09 realization of bloc_05/03 §11 (the four equivalence classes made
operational), §12 (the per-provider semantic record) and §13 (the semantic
confidence ladder), as an EXTENSION of the live Bloc 1 registry (BOOK 00 Q1):
``registry/semantic_equivalence.py`` keeps its six planning mappings, its YAML
and its ratified consumers; this module adds the frozen 07 §4 object, the
per-provider record surface, the confidence ladder and fail-closed typed
lookup.

Text-in/text-out, like the I05 time-semantics registry: no path is read here.

Deliberate properties:

1. **Frozen names verbatim.**  03 §11's eight field names
   (``provider_field``, ``canonical_field``, ``semantic_equivalence_class``,
   ``native_definition``, ``transformation``, ``methodology_id``,
   ``blocking_assumptions``, ``known_limitations``) are this model's field
   names; 03 §12's record attributes complete the 07 §4 object.
2. **Blocking assumptions and known limitations are mandatory** (readiness §10
   stop 1): a mapping that cannot state them is refused at construction.
3. **Provisional stays provisional (BOOK 00 Q7).**  While ``evidence_reference``
   is the pending token, the confidence MUST be ``AMBIGUOUS``; a ``VERIFIED_*``
   claim must point at evidence that is not the pending token.  A mapping's
   class is never upgraded here -- the four classes are the upstream enum,
   imported, never forked.
4. **The eight-provider schema is the live provider set (BOOK 00 Q6).**  Every
   ``provider`` token is validated against the consumed ``PROVIDER_IDS``
   tuple, so an invented exchange fails closed at construction while the
   frozen eight-provider structural contract is reused rather than restated.
5. **No default synthesis.**  A missing ``(provider, provider_field,
   sensor_family)`` row resolves to ``None``; the same field NAME on another
   family never cross-fills it (bloc_01 §13: same field name never establishes
   comparability).
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated

import yaml
from pydantic import (
    AfterValidator,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from ...contracts.enums import SemanticEquivalence, SensorFamily
from ...registry.provider_registry import PROVIDER_IDS
from ...registry.semantic_equivalence import EquivalenceMapping
from ..models import (
    NormalizationModelBase,
    RegistryVersion,
    _reject_blank,
    _require_unpadded,
)

__all__ = [
    "PENDING_EVIDENCE_REFERENCE",
    "IntervalDataScope",
    "ProviderSemanticMapping",
    "ProviderSemanticRegistry",
    "SemanticConfidence",
    "UnknownProviderSemanticMapping",
    "admits_critical_t1_use",
    "is_first_party_grade",
    "parse_provider_semantic_registry_yaml",
    "project_planning_mapping",
    "serialize_provider_semantic_registry_yaml",
]

#: The evidence-reference token that means "no probe has proven this mapping".
#: Every live Bloc 1 planning mapping carries it (measured: six of six).
PENDING_EVIDENCE_REFERENCE = "BLOC2_PROBE_PENDING"

_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class UnknownProviderSemanticMapping(LookupError):
    """Raised instead of returning a guess (06 §1 G9 fail-closed)."""


class _StrEnum(str, Enum):
    """Deterministic string-valued enum base (values equal member names)."""


class SemanticConfidence(_StrEnum):
    """The frozen bloc_05/03 §13 confidence ladder, in document order.

    ``AMBIGUOUS`` blocks use in critical T1 normalized fields.  Community
    evidence can support corroboration but can never masquerade as first-party
    semantics -- :func:`is_first_party_grade` is the operational form of that
    second law.
    """

    VERIFIED_FIRST_PARTY = "VERIFIED_FIRST_PARTY"
    VERIFIED_SECONDARY = "VERIFIED_SECONDARY"
    RECONSTRUCTED_FROM_FIRST_PARTY_FIELDS = "RECONSTRUCTED_FROM_FIRST_PARTY_FIELDS"
    COMMUNITY_DOCUMENTED = "COMMUNITY_DOCUMENTED"
    AMBIGUOUS = "AMBIGUOUS"


#: Confidences that may back a critical T1 normalized field (03 §13).
_BLOCKING_CONFIDENCE: frozenset[SemanticConfidence] = frozenset(
    {SemanticConfidence.AMBIGUOUS}
)

#: Confidences that may be presented as first-party semantics (03 §13).
_FIRST_PARTY_GRADE: frozenset[SemanticConfidence] = frozenset(
    {SemanticConfidence.VERIFIED_FIRST_PARTY}
)

#: Confidences that require non-pending evidence to be claimed at all.
_EVIDENCE_BACKED_CONFIDENCE: frozenset[SemanticConfidence] = frozenset(
    {
        SemanticConfidence.VERIFIED_FIRST_PARTY,
        SemanticConfidence.VERIFIED_SECONDARY,
        SemanticConfidence.RECONSTRUCTED_FROM_FIRST_PARTY_FIELDS,
        SemanticConfidence.COMMUNITY_DOCUMENTED,
    }
)


def admits_critical_t1_use(confidence: SemanticConfidence) -> bool:
    """03 §13: ``AMBIGUOUS`` blocks use in critical T1 normalized fields."""
    return confidence not in _BLOCKING_CONFIDENCE


def is_first_party_grade(confidence: SemanticConfidence) -> bool:
    """03 §13: only first-party verification may masquerade as first-party."""
    return confidence in _FIRST_PARTY_GRADE


class IntervalDataScope(_StrEnum):
    """Cumulative-vs-interval-local semantics of a provider field (03 §12).

    A vocabulary, not a registry: it exists so a mapping can STATE what §12
    requires it to state.  ``PROVIDER_NATIVE_UNKNOWN`` is the honest
    unclassified member -- it means "not verified", never "compatible" (the
    I05 ``PROVIDER_NATIVE_UNKNOWN`` precedent).  ``POINT_SNAPSHOT`` carries
    the 07 F19 stock/snapshot law so an open-interest row need not lie about
    being an interval aggregate.
    """

    CUMULATIVE = "CUMULATIVE"
    INTERVAL_LOCAL = "INTERVAL_LOCAL"
    POINT_SNAPSHOT = "POINT_SNAPSHOT"
    PROVIDER_NATIVE_UNKNOWN = "PROVIDER_NATIVE_UNKNOWN"


OpaqueToken = Annotated[
    str,
    StringConstraints(min_length=1, pattern=r"^\S(.*\S)?$"),
    AfterValidator(_reject_blank),
    AfterValidator(_require_unpadded),
]

def _require_known_provider(value: str) -> str:
    """BOOK 00 Q6: a provider token must be in the live, consumed eight-provider
    schema; an invented exchange is refused at construction, not at lookup."""
    if value not in PROVIDER_IDS:
        raise ValueError(
            f"provider {value!r} is not in the frozen eight-provider schema "
            "(registry.provider_registry.PROVIDER_IDS); an unknown provider "
            "mapping fails closed (BOOK 00 Q6)"
        )
    return value


#: A provider token must be one of the live, consumed eight-provider set.
ProviderToken = Annotated[
    str,
    StringConstraints(min_length=1, pattern=r"^\S(.*\S)?$"),
    AfterValidator(_reject_blank),
    AfterValidator(_require_unpadded),
    AfterValidator(_require_known_provider),
]


class ProviderSemanticMapping(NormalizationModelBase):
    """One provider→canonical semantic mapping (03 §11 + §12 + §13; 07 §4).

    The §11 names are preserved verbatim; the §12 attributes complete the
    per-provider record.  Validators re-enforce the Bloc 1 laws (B1-T41,
    B1-T43) so an upgraded surface cannot weaken a ratified one, plus the
    confidence/evidence coherence law of 03 §13.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    # --- bloc_05/03 §11 frozen names ---
    provider: ProviderToken
    provider_field: OpaqueToken
    canonical_sensor: SensorFamily
    canonical_field: OpaqueToken
    semantic_equivalence_class: SemanticEquivalence
    native_definition: OpaqueToken
    transformation: OpaqueToken
    methodology_id: OpaqueToken | None = None
    blocking_assumptions: tuple[OpaqueToken, ...] = Field(min_length=1)
    known_limitations: tuple[OpaqueToken, ...] = Field(min_length=1)

    # --- bloc_05/03 §12 per-provider record attributes ---
    source_endpoint_or_archive: OpaqueToken
    data_type: OpaqueToken
    native_unit: OpaqueToken
    timestamp_meaning: OpaqueToken
    interval_data_scope: IntervalDataScope
    direction_side_convention: OpaqueToken
    evidence_reference: OpaqueToken | None = None
    semantic_confidence: SemanticConfidence
    last_verified_date: str | None = None
    version: OpaqueToken = "1"

    @field_validator("last_verified_date")
    @classmethod
    def _validated_date_or_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if not _ISO_DATE_RE.match(value):
            raise ValueError(
                "last_verified_date must be an ISO date (YYYY-MM-DD) or null "
                "(never verified); a mapping cannot invent a verification date"
            )
        return value

    @model_validator(mode="after")
    def _class_and_evidence_laws(self) -> ProviderSemanticMapping:
        if (
            self.semantic_equivalence_class is SemanticEquivalence.NORMALIZABLE_COMPARABLE
            and self.methodology_id is None
        ):
            raise ValueError(
                "NORMALIZABLE_COMPARABLE mapping requires methodology_id (B1-T41)"
            )
        if (
            self.semantic_equivalence_class is SemanticEquivalence.EXACT_EQUIVALENT
            and self.evidence_reference is None
        ):
            raise ValueError(
                "EXACT_EQUIVALENT mapping requires evidence_reference (B1-T43)"
            )
        pending = self.evidence_reference == PENDING_EVIDENCE_REFERENCE
        if pending and self.semantic_confidence is not SemanticConfidence.AMBIGUOUS:
            raise ValueError(
                "a mapping whose evidence_reference is still "
                f"{PENDING_EVIDENCE_REFERENCE} must stay AMBIGUOUS: a provisional "
                "mapping is not a verified mapping and no registry edit promotes "
                "semantic confidence without documentary proof (BOOK 00 Q7)"
            )
        if (
            self.semantic_confidence in _EVIDENCE_BACKED_CONFIDENCE
            and (self.evidence_reference is None or pending)
        ):
            raise ValueError(
                f"semantic_confidence={self.semantic_confidence.value} requires "
                "evidence_reference other than the pending token: community or "
                "verified claims cannot rest on absent evidence (03 §13)"
            )
        return self


class ProviderSemanticRegistry(NormalizationModelBase):
    """The complete declared set, canonically ordered and duplicate-free.

    The lookup key is ``(provider, provider_field, canonical_sensor)``: one
    provider field may legitimately map into two sensor families, but never
    twice into the same one.
    """

    schema_version: OpaqueToken
    mappings: tuple[ProviderSemanticMapping, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def _canonicalize(cls, payload: object) -> object:
        if not isinstance(payload, dict):
            return payload
        rows = payload.get("mappings")
        if isinstance(rows, list):
            ordered = sorted(
                rows,
                key=lambda row: (
                    str(row.get("provider", "")) if isinstance(row, dict) else "",
                    str(row.get("canonical_sensor", "")) if isinstance(row, dict) else "",
                    str(row.get("provider_field", "")) if isinstance(row, dict) else "",
                ),
            )
            payload = {**payload, "mappings": ordered}
        return payload

    @model_validator(mode="after")
    def _reject_duplicates(self) -> ProviderSemanticRegistry:
        keys = [
            (row.provider, row.canonical_sensor, row.provider_field)
            for row in self.mappings
        ]
        if len(set(keys)) != len(keys):
            raise ValueError(
                "duplicate (provider, canonical_sensor, provider_field) semantic row"
            )
        return self

    def resolve(
        self, provider: str, provider_field: str, sensor_family: SensorFamily
    ) -> ProviderSemanticMapping | None:
        """The declared row, or ``None`` -- never a synthesized default."""
        for row in self.mappings:
            if (
                row.provider == provider
                and row.provider_field == provider_field
                and row.canonical_sensor is sensor_family
            ):
                return row
        return None

    def require(
        self, provider: str, provider_field: str, sensor_family: SensorFamily
    ) -> ProviderSemanticMapping:
        row = self.resolve(provider, provider_field, sensor_family)
        if row is None:
            raise UnknownProviderSemanticMapping(
                f"no declared semantic mapping for provider={provider!r} "
                f"provider_field={provider_field!r} sensor_family="
                f"{sensor_family.value!r}; an unprobed mapping is never filled "
                "from a similar-looking row (bloc_05/03 §12, readiness §10 stop 7)"
            )
        return row

    def version_token(self) -> RegistryVersion:
        """The registry-generation token a T1 envelope carries (03 §2)."""
        return self.schema_version


def project_planning_mapping(
    mapping: EquivalenceMapping,
    *,
    source_endpoint_or_archive: str,
    data_type: str,
    native_unit: str,
    timestamp_meaning: str,
    interval_data_scope: IntervalDataScope | str,
    direction_side_convention: str,
    blocking_assumptions: tuple[str, ...],
    known_limitations: tuple[str, ...],
    semantic_confidence: SemanticConfidence = SemanticConfidence.AMBIGUOUS,
) -> ProviderSemanticMapping:
    """Project a live Bloc 1 planning mapping into the frozen §11/§12 shape.

    Identity-bearing fields are copied verbatim -- provider, source metric,
    canonical sensor/field, equivalence class, methodology id, evidence
    reference and version -- so no existing ID or mapping changes meaning
    (BOOK 00 Q1).  ``native_definition``/``transformation`` come from the
    Bloc 1 row's own ``source_definition``/``transformation_method``; the §12
    record attributes and the mandatory blocking/known statements are supplied
    by the caller from accepted evidence, with no defaults.  The confidence
    default is ``AMBIGUOUS`` and the model itself refuses an upgrade while the
    evidence reference is pending (BOOK 00 Q7), so this adapter cannot be used
    to promote a planning mapping.
    """
    if mapping.source_definition is None or mapping.transformation_method is None:
        raise ValueError(
            "Bloc 1 mapping lacks source_definition/transformation_method; the "
            "frozen §11 shape requires native_definition and transformation, "
            "and neither may be invented (readiness §10 stop 9)"
        )
    return ProviderSemanticMapping.model_validate(
        {
            "provider": mapping.provider,
            "provider_field": mapping.source_metric,
            "canonical_sensor": mapping.canonical_sensor,
            "canonical_field": mapping.canonical_field,
            "semantic_equivalence_class": mapping.equivalence,
            "native_definition": mapping.source_definition,
            "transformation": mapping.transformation_method,
            "methodology_id": mapping.methodology_id,
            "blocking_assumptions": tuple(blocking_assumptions),
            "known_limitations": tuple(known_limitations),
            "source_endpoint_or_archive": source_endpoint_or_archive,
            "data_type": data_type,
            "native_unit": native_unit,
            "timestamp_meaning": timestamp_meaning,
            "interval_data_scope": interval_data_scope,
            "direction_side_convention": direction_side_convention,
            "evidence_reference": mapping.evidence_reference,
            "semantic_confidence": semantic_confidence,
            "last_verified_date": None,
            "version": mapping.version,
        }
    )


def parse_provider_semantic_registry_yaml(text: str) -> ProviderSemanticRegistry:
    """Parse configuration TEXT.  No path is read here, ever."""
    try:
        payload = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid provider semantic registry YAML: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(
            "provider semantic registry document must be a mapping with "
            "schema_version and mappings"
        )
    return ProviderSemanticRegistry.model_validate(payload)


def serialize_provider_semantic_registry_yaml(
    registry: ProviderSemanticRegistry,
) -> str:
    """Deterministic YAML: frozen field order, sorted rows, stable width."""
    payload = {
        "schema_version": registry.schema_version,
        "mappings": [
            {
                "provider": row.provider,
                "provider_field": row.provider_field,
                "canonical_sensor": row.canonical_sensor.value,
                "canonical_field": row.canonical_field,
                "semantic_equivalence_class": row.semantic_equivalence_class.value,
                "native_definition": row.native_definition,
                "transformation": row.transformation,
                "methodology_id": row.methodology_id,
                "blocking_assumptions": list(row.blocking_assumptions),
                "known_limitations": list(row.known_limitations),
                "source_endpoint_or_archive": row.source_endpoint_or_archive,
                "data_type": row.data_type,
                "native_unit": row.native_unit,
                "timestamp_meaning": row.timestamp_meaning,
                "interval_data_scope": row.interval_data_scope.value,
                "direction_side_convention": row.direction_side_convention,
                "evidence_reference": row.evidence_reference,
                "semantic_confidence": row.semantic_confidence.value,
                "last_verified_date": row.last_verified_date,
                "version": row.version,
            }
            for row in sorted(
                registry.mappings,
                key=lambda row: (row.provider, row.canonical_sensor.value, row.provider_field),
            )
        ],
    }
    return yaml.safe_dump(
        payload,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=100,
    )
