"""SENSOR-B5-I09 - the frozen ``NormalizationMethodology`` registry (03 §16).

The I09 realization of bloc_05/03 §16 and the 07 §4 frozen object name, built
AS AN EXTENSION of the live Bloc 1 registry, never as a replacement (BOOK 00
Q1): ``registry/methodology_registry.py`` keeps its nine planning ids, its
YAML and its ratified consumers; this module adds the frozen eleven-field
object, versioned identity (07 F14) and fail-closed typed lookup, and offers
:func:`project_planning_methodology` -- a text-adjacent adapter that projects a
Bloc 1 ``MethodologyEntry`` into the frozen shape when, and only when, the
caller can state every attribute Bloc 1 does not carry.  Attributes that
cannot be established from accepted evidence are NOT defaulted: the caller
omits the projection and the entry stays unregistered (Q2's fail-closed
branch).

Text-in/text-out like the I05 time-semantics registry: serialization and
parsing carry no filesystem knowledge, so this package never reads or writes a
path.  Committed configuration is read by the caller (tests, evidence
producer) as text.

Three deliberate properties:

1. **Versioned identity is mechanical (07 F14).**  The registry refuses two
   rows with the same ``(methodology_id, version)``; a legitimate change is a
   new version row, and the historical row stays resolvable.  A silent
   overwrite is structurally impossible: records are frozen and duplicates are
   refused.
2. **No default, ever.**  ``resolve`` returns ``None`` and ``require`` raises
   the typed :class:`UnknownNormalizationMethodology`; an unversioned lookup
   with more than one live version fails closed rather than picking one.
3. **Frozen names, verbatim.**  ``PIT_requirements`` keeps its frozen casing;
   the eleven 03 §16 field names are the model's field names, so a serialized
   registry matches the frozen contract line for line.
"""

from __future__ import annotations

from typing import Annotated, Sequence

import yaml
from pydantic import AfterValidator, ConfigDict, Field, StringConstraints, model_validator

from ...contracts.enums import SensorFamily
from ...registry.methodology_registry import MethodologyEntry
from ..models import (
    NormalizationModelBase,
    RegistryVersion,
    _reject_blank,
    _require_unpadded,
)

__all__ = [
    "MethodologyRef",
    "NormalizationMethodology",
    "NormalizationMethodologyRegistry",
    "UnknownNormalizationMethodology",
    "parse_normalization_methodology_registry_yaml",
    "project_planning_methodology",
    "serialize_normalization_methodology_registry_yaml",
]


class UnknownNormalizationMethodology(LookupError):
    """Raised instead of returning a guess (06 §1 G9 fail-closed).

    ``LookupError`` rather than a bare exception so a caller that swallows it
    still has a typed, specific failure to reason about.
    """


#: A non-blank, unpadded opaque token.  Well-formedness only: the I01 opaque
#: identifier law applies, so nothing here is a registry lookup or a guess.
OpaqueToken = Annotated[
    str,
    StringConstraints(min_length=1, pattern=r"^\S(.*\S)?$"),
    AfterValidator(_reject_blank),
    AfterValidator(_require_unpadded),
]


class NormalizationMethodology(NormalizationModelBase):
    """One versioned methodology contract (bloc_05/03 §16; 07 §4, F14).

    Frozen field set, names and casing preserved verbatim from the plan:

    * ``methodology_id`` / ``version`` -- the versioned identity; a change of
      substance must create a new version (F14), never overwrite this row;
    * ``sensor_family`` -- the frozen eight-member Bloc 1 vocabulary; a
      cross-family methodology cannot state it and therefore stays
      unregistered until an operator ruling supplies a lawful representation
      (BOOK 00 Q2 fail-closed branch, recorded in the I09 evidence);
    * ``formula_or_algorithm`` / ``required_inputs`` / ``output_units`` --
      the operational transform description 03 §22 inv.7 requires every
      derived canonical value to reference;
    * ``PIT_requirements`` -- the point-in-time law the conversion and
      reference-price stages must satisfy;
    * ``known_limitations`` -- mandatory and non-empty: a versioned
      methodology that cannot state a limitation has not been examined
      (07 F14 lists it as a required attribute);
    * ``introduced_at`` -- an opaque provenance token (the introducing commit
      SHA, or the operator-ruled date); ``deprecated_at`` marks retirement
      without deletion, so historical references stay resolvable.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    methodology_id: OpaqueToken
    version: OpaqueToken
    sensor_family: SensorFamily
    description: OpaqueToken
    formula_or_algorithm: OpaqueToken
    required_inputs: tuple[OpaqueToken, ...] = Field(min_length=1)
    output_units: tuple[OpaqueToken, ...] = Field(min_length=1)
    PIT_requirements: OpaqueToken
    known_limitations: tuple[OpaqueToken, ...] = Field(min_length=1)
    introduced_at: OpaqueToken
    deprecated_at: OpaqueToken | None = None


class MethodologyRef(NormalizationModelBase):
    """The ``(methodology_id, version)`` pair a T1 record cites (03 §22 inv.7).

    TYPE ONLY for the two ``T1ObservationEnvelope`` fields I09 owns
    (``normalization_methodology_id`` / ``normalization_methodology_version``):
    this reference is what those fields carry, and it is the only envelope
    surface I09 ships (BOOK 00 Q4 -- the frozen composite name stays
    unexported and incomplete by design).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    methodology_id: OpaqueToken
    version: OpaqueToken

    @classmethod
    def from_methodology(cls, row: NormalizationMethodology) -> MethodologyRef:
        return cls(methodology_id=row.methodology_id, version=row.version)


class NormalizationMethodologyRegistry(NormalizationModelBase):
    """The complete declared set, canonically ordered and duplicate-free.

    The ``(methodology_id, version)`` key IS the versioned identity: two rows
    may share an id only when their versions differ, which is exactly 07
    F14's "bump the version instead of changing the formula in place".
    """

    schema_version: OpaqueToken
    methodologies: tuple[NormalizationMethodology, ...] = ()

    @model_validator(mode="before")
    @classmethod
    def _canonicalize(cls, payload: object) -> object:
        if not isinstance(payload, dict):
            return payload
        rows = payload.get("methodologies")
        if isinstance(rows, list):
            ordered = sorted(
                rows,
                key=lambda row: (
                    str(row.get("methodology_id", "")) if isinstance(row, dict) else "",
                    str(row.get("version", "")) if isinstance(row, dict) else "",
                ),
            )
            payload = {**payload, "methodologies": ordered}
        return payload

    @model_validator(mode="after")
    def _reject_duplicate_identities(self) -> NormalizationMethodologyRegistry:
        keys = [(row.methodology_id, row.version) for row in self.methodologies]
        if len(set(keys)) != len(keys):
            raise ValueError(
                "duplicate (methodology_id, version) methodology row: changing a "
                "formula under the same identity is a forbidden silent change "
                "(bloc_05/07 F14) -- register a new version instead"
            )
        return self

    def resolve(
        self, methodology_id: str, version: str | None = None
    ) -> NormalizationMethodology | None:
        """The declared row, or ``None`` -- never a synthesized default.

        With no ``version``, exactly one live row must exist; two live
        versions are ambiguous and resolve to ``None`` (fail closed).
        """
        rows = [row for row in self.methodologies if row.methodology_id == methodology_id]
        if version is not None:
            for row in rows:
                if row.version == version:
                    return row
            return None
        if len(rows) == 1:
            return rows[0]
        return None

    def require(
        self, methodology_id: str, version: str | None = None
    ) -> NormalizationMethodology:
        row = self.resolve(methodology_id, version)
        if row is not None:
            return row
        rows = [row for row in self.methodologies if row.methodology_id == methodology_id]
        if rows and version is None:
            raise UnknownNormalizationMethodology(
                f"methodology_id {methodology_id!r} has {len(rows)} live versions "
                f"({', '.join(sorted(row.version for row in rows))}); an unversioned "
                "lookup must fail closed rather than pick one (bloc_05/07 F14)"
            )
        raise UnknownNormalizationMethodology(
            f"methodology_id {methodology_id!r} version {version!r} is not "
            "registered; the methodology is unknown, so it is refused "
            "(bloc_05/06 s1 G9)"
        )

    def versions(self, methodology_id: str) -> tuple[str, ...]:
        return tuple(
            sorted(
                row.version
                for row in self.methodologies
                if row.methodology_id == methodology_id
            )
        )

    def version_token(self) -> RegistryVersion:
        """The registry-generation token a T1 envelope carries.

        Names the declared schema generation; per-methodology identity is
        carried by :class:`MethodologyRef`, not by this token.  Minting a
        content digest belongs to the evidence producer (hashing stays out of
        the pure layer by design).
        """
        return self.schema_version


def project_planning_methodology(
    entry: MethodologyEntry,
    *,
    methodology_id: str,
    sensor_family: SensorFamily,
    formula_or_algorithm: str,
    required_inputs: Sequence[str],
    output_units: Sequence[str],
    PIT_requirements: str,
    known_limitations: Sequence[str],
    introduced_at: str,
) -> NormalizationMethodology:
    """Project a live Bloc 1 planning entry into the frozen §16 shape.

    The adapter copies ``entry.description`` and ``entry.version`` verbatim
    (no meaning change, BOOK 00 Q1), carries the upstream ``status`` into the
    limitations list so no upstream information is dropped, and requires the
    CALLER to state every attribute Bloc 1 does not carry.  There are no
    defaults: an entry whose attributes cannot be established from accepted
    evidence simply is not projected, which is Q2's fail-closed branch.
    """
    limitations = tuple(known_limitations) + (
        f"upstream bloc_01/02 methodology_registry.yaml status: {entry.status}",
    )
    return NormalizationMethodology.model_validate(
        {
            "methodology_id": methodology_id,
            "version": entry.version,
            "sensor_family": sensor_family,
            "description": entry.description,
            "formula_or_algorithm": formula_or_algorithm,
            "required_inputs": tuple(required_inputs),
            "output_units": tuple(output_units),
            "PIT_requirements": PIT_requirements,
            "known_limitations": limitations,
            "introduced_at": introduced_at,
            "deprecated_at": None,
        }
    )


def parse_normalization_methodology_registry_yaml(text: str) -> NormalizationMethodologyRegistry:
    """Parse configuration TEXT.  No path is read here, ever."""
    try:
        payload = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid normalization methodology registry YAML: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(
            "normalization methodology registry document must be a mapping with "
            "schema_version and methodologies"
        )
    return NormalizationMethodologyRegistry.model_validate(payload)


def serialize_normalization_methodology_registry_yaml(
    registry: NormalizationMethodologyRegistry,
) -> str:
    """Deterministic YAML: frozen field order, sorted rows, stable width."""
    payload = {
        "schema_version": registry.schema_version,
        "methodologies": [
            {
                "methodology_id": row.methodology_id,
                "version": row.version,
                "sensor_family": row.sensor_family.value,
                "description": row.description,
                "formula_or_algorithm": row.formula_or_algorithm,
                "required_inputs": list(row.required_inputs),
                "output_units": list(row.output_units),
                "PIT_requirements": row.PIT_requirements,
                "known_limitations": list(row.known_limitations),
                "introduced_at": row.introduced_at,
                "deprecated_at": row.deprecated_at,
            }
            for row in sorted(
                registry.methodologies,
                key=lambda row: (row.methodology_id, row.version),
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
