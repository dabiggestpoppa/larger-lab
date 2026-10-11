"""SENSOR-B5-I05 - the provider time-semantics registry (bloc_05/02 section 17).

Text-in/text-out, exactly like the I02 identity registry: serialization and
parsing carry no filesystem knowledge, so this package can never read or write
a path.  The committed configuration lives at
``config/crypto_sensor_fabric/provider_time_semantics.yaml`` and is loaded by
the caller (tests, evidence producer) as text.

Frozen authority: section 2/3 (role vocabulary), section 7 (the provider
mapping config must STATE the interval convention -- never guess it), section
8 (declared precision), section 18 rule 7 (unknown provider timestamp
semantics fail closed for strict replay) and bloc_05/06 s1 G2.

Three deliberate properties:

1. **No defaults, ever.**  A missing (provider, sensor family) row yields
   ``None`` from :meth:`resolve` and an exception from :meth:`require`; there
   is no synthesized "probably realtime" record and no fallback convention.
2. **No invented real-exchange rows.**  ``provider_time_semantics.yaml`` ships
   with zero real-provider entries because no verified documentation or probe
   evidence for any of them exists in this repository; inventing one would be
   guessing a provider's timestamp semantics, which the I05 directive lists as
   a STOP condition.  Synthetic fixtures live in tests only.
3. **An unclassified source is still an honest record.**  A row may declare
   ``PROVIDER_NATIVE_UNKNOWN``/``UNKNOWN`` and an empty role map: that states
   "we know this provider, and we have NOT verified its semantics", which is
   strictly more informative than absence and still fails closed at use.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Annotated, Mapping

import yaml
from pydantic import AfterValidator, Field, StringConstraints, model_validator

from ...contracts.enums import SensorFamily
from ..enums import IntervalTimeConvention, TimestampPrecision
from .enums import TimestampRole
from .models import (
    EvidenceRef,
    TimeEvidenceBase,
    _reject_blank,
    _require_unpadded,
)

__all__ = [
    "ProviderTimeSemantics",
    "ProviderTimeSemanticsRegistry",
    "UnknownProviderTimeSemantics",
    "parse_provider_time_semantics_yaml",
    "serialize_provider_time_semantics_yaml",
]


class UnknownProviderTimeSemantics(LookupError):
    """Raised instead of returning a guess (section 18 rule 7).

    ``LookupError`` rather than a bare exception so a caller that swallows it
    still has a typed, specific failure to reason about.
    """


ProviderId = Annotated[
    str,
    StringConstraints(min_length=1, pattern=r"\S"),
    AfterValidator(_reject_blank),
    AfterValidator(_require_unpadded),
]


def _freeze_roles(roles: Mapping[TimestampRole, str]) -> Mapping[TimestampRole, str]:
    cleaned: dict[TimestampRole, str] = {}
    for role, field_name in roles.items():
        _reject_blank(field_name)
        _require_unpadded(field_name)
        cleaned[role] = field_name
    return MappingProxyType(cleaned)


#: A role map that is read-only once constructed: frozen plan data cannot be
#: edited through a live dict reference.
RoleMap = Annotated[Mapping[TimestampRole, str], AfterValidator(_freeze_roles)]


class ProviderTimeSemantics(TimeEvidenceBase):
    """One declared (provider, sensor family) time-semantics record.

    Fields and their frozen authority:

    * ``provider`` / ``sensor_family`` -- the lookup key (section 17 config);
    * ``timestamp_field_roles`` -- which provider-native field carries each
      canonical role; empty means "not verified", never "same as" (section 2);
    * ``interval_time_convention`` -- STATED, never inferred (section 7);
    * ``precision`` -- declared source precision (section 8);
    * ``contemporaneous_public`` -- the section 6 explicit classification that
      is the ONLY license for using ``source_event_at`` as a market-availability
      anchor ("only when the source is explicitly classified
      contemporaneous-public"), and therefore it must be evidenced;
    * ``source_evidence_refs`` -- the durable evidence behind that claim.
    """

    provider: ProviderId
    sensor_family: SensorFamily
    timestamp_field_roles: RoleMap = Field(
        default_factory=lambda: MappingProxyType({})
    )
    interval_time_convention: IntervalTimeConvention
    precision: TimestampPrecision
    contemporaneous_public: bool
    source_evidence_refs: tuple[EvidenceRef, ...] = Field(default_factory=tuple)

    @model_validator(mode="after")
    def _freeze_and_check(self) -> ProviderTimeSemantics:
        if self.contemporaneous_public and not self.source_evidence_refs:
            raise ValueError(
                "contemporaneous_public requires source_evidence_refs "
                "(bloc_05/02 section 6: a contemporaneous-public classification "
                "is only usable when documentation or evidence establishes it)"
            )
        if len(set(self.source_evidence_refs)) != len(self.source_evidence_refs):
            raise ValueError("source_evidence_refs contains duplicates")
        return self


class ProviderTimeSemanticsRegistry(TimeEvidenceBase):
    """The complete declared set, canonically ordered and duplicate-free."""

    schema_version: str
    semantics: tuple[ProviderTimeSemantics, ...] = Field(default_factory=tuple)

    @model_validator(mode="before")
    @classmethod
    def _canonicalize(cls, payload: object) -> object:
        if not isinstance(payload, dict):
            return payload
        rows = payload.get("semantics")
        if isinstance(rows, list):
            ordered = sorted(
                rows,
                key=lambda row: (
                    str(row.get("provider", "")) if isinstance(row, dict) else "",
                    str(row.get("sensor_family", "")) if isinstance(row, dict) else "",
                ),
            )
            payload = {**payload, "semantics": ordered}
        return payload

    @model_validator(mode="after")
    def _reject_duplicates(self) -> ProviderTimeSemanticsRegistry:
        keys = [(row.provider, row.sensor_family) for row in self.semantics]
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate (provider, sensor_family) time-semantics row")
        return self

    def resolve(
        self, provider: str, sensor_family: SensorFamily
    ) -> ProviderTimeSemantics | None:
        """The declared row, or ``None`` -- never a synthesized default."""
        for row in self.semantics:
            if row.provider == provider and row.sensor_family is sensor_family:
                return row
        return None

    def require(
        self, provider: str, sensor_family: SensorFamily
    ) -> ProviderTimeSemantics:
        row = self.resolve(provider, sensor_family)
        if row is None:
            raise UnknownProviderTimeSemantics(
                f"no declared time semantics for provider={provider!r} "
                f"sensor_family={sensor_family.value!r}; strict replay fails "
                "closed rather than guessing (bloc_05/02 section 18 rule 7)"
            )
        return row

    def resolve_role(
        self, provider: str, sensor_family: SensorFamily, role: TimestampRole
    ) -> str | None:
        row = self.resolve(provider, sensor_family)
        if row is None:
            return None
        return row.timestamp_field_roles.get(role)

    def require_role(
        self, provider: str, sensor_family: SensorFamily, role: TimestampRole
    ) -> str:
        field_name = self.resolve_role(provider, sensor_family, role)
        if field_name is None:
            raise UnknownProviderTimeSemantics(
                f"provider={provider!r} sensor_family={sensor_family.value!r} does "
                f"not declare a source field for role={role.value!r}; the mapping "
                "is unknown, so it is refused (bloc_05/02 section 7)"
            )
        return field_name


def parse_provider_time_semantics_yaml(text: str) -> ProviderTimeSemanticsRegistry:
    """Parse configuration TEXT.  No path is read here, ever."""
    try:
        payload = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid provider time semantics YAML: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(
            "provider time semantics document must be a mapping with "
            "schema_version and semantics"
        )
    return ProviderTimeSemanticsRegistry.model_validate(payload)


def serialize_provider_time_semantics_yaml(
    registry: ProviderTimeSemanticsRegistry,
) -> str:
    """Deterministic YAML: fixed key order, sorted rows, stable width."""
    payload = {
        "schema_version": registry.schema_version,
        "semantics": [
            {
                "provider": row.provider,
                "sensor_family": row.sensor_family.value,
                "timestamp_field_roles": {
                    role.value: field_name
                    for role, field_name in sorted(
                        row.timestamp_field_roles.items(), key=lambda item: item[0].value
                    )
                },
                "interval_time_convention": row.interval_time_convention.value,
                "precision": row.precision.value,
                "contemporaneous_public": row.contemporaneous_public,
                "source_evidence_refs": list(row.source_evidence_refs),
            }
            for row in sorted(
                registry.semantics, key=lambda row: (row.provider, row.sensor_family.value)
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
