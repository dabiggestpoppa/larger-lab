"""SENSOR-B5-I16 (preliminary) - deterministic T1 identity and lineage laws.

The I16 realization of ``bloc_05/05`` sections 2, 3 and 4: a complete lineage
chain, a deterministic content-addressed record identity, and immutable
normalization generations.

**Deterministic identity.**  ``t1_record_id`` is derived from an identity KEY, not
from the record's values:

    sensor_family, provider, venue, contract_instance_id,
    native identity (event or snapshot id + sequence),
    source_revision_id, normalization_generation

Consequences the composition gives for free:

* no normalized number appears in the key, so a corrected value cannot collide
  with the original row (05 section 4) and a revision yields a different id;
* no wall clock, no random source, no process-local counter and no machine
  identity appears in the key, so the same evidence derives the same id on any
  host, in any order, at any time;
* a new generation re-derives ids, which is exactly what makes a regeneration
  additive rather than destructive.

**Completeness assertions.**  ``assert_lineage_complete`` refuses a record whose
T0 chain is broken: T1 -> projection -> acquisition -> blob, plus the code and
config versions.  There is no "partial" construction here; a record either names
its whole chain or fails.

**Generation immutability.**  ``assert_generation_immutable`` compares a published
generation descriptor with an observed one and refuses any drift in the fields
that define it.  ``created_at`` is carried but explicitly EXCLUDED from the
fingerprint: 05 permits nondeterministic build timestamps only when they are
documented, and documenting it in one constant is how that stays true.

**What is deliberately NOT here.**  No duplicate/revision engine (I17), no
generation writer or atomic publish (I18), no query or replay filter (I19).  This
module also does not close the LINEAGE gate: ``LINEAGE_GATE_STATE`` stays
``NOT_CLOSED`` because the complete required sensor-family set is not yet covered
(see ``missing_sensor_families``).  Preliminary means preliminary.

Hashing lives here, in ``normalization/lineage/``, and not in
``normalization/sensors/``: the sensor tree is contractually hash-free (no
fingerprinting, no id generation), and the I11 scope audit enforces that.  The
identity law is a different layer with a different job.
"""

from __future__ import annotations

import hashlib
import json
from typing import Iterable

from pydantic import ConfigDict, Field, model_validator

from ...contracts.enums import SensorFamily
from ..enums import LineageState
from ..models import (
    NormalizationModelBase,
    OpaqueIdentifier,
    RegistryVersion,
    T1BaseEnvelope,
    T1RecordId,
)

__all__ = [
    "IDENTITY_SCHEMA_VERSION",
    "LINEAGE_GATE_STATE",
    "LINEAGE_GATE_CLOSED",
    "REQUIRED_SENSOR_FAMILIES",
    "GenerationDescriptor",
    "GenerationImmutableViolation",
    "IncompleteLineageError",
    "T1IdentityKey",
    "assert_generation_immutable",
    "assert_lineage_complete",
    "canonical_identity_bytes",
    "compute_t1_record_id",
    "generation_fingerprint",
    "lineage_completeness",
    "missing_sensor_families",
]

#: Version of the identity key schema.  Changing the key is a new schema, never a
#: silent reinterpretation of an existing one.
IDENTITY_SCHEMA_VERSION = "b5-i16-t1-identity-1"

#: Fields a generation descriptor may carry that are NOT part of its identity.
#: Documented here once so no caller has to guess (05 section 20 law 10 permits
#: nondeterministic build metadata only when it is explicitly documented).
GENERATION_NONDETERMINISTIC_FIELDS = ("created_at",)

#: The frozen eight member sensor-family set the lineage gate must eventually see.
REQUIRED_SENSOR_FAMILIES = tuple(family.value for family in SensorFamily)

#: Preliminary state.  The gate needs the complete required sensor-family set,
#: which Wave 1 does not deliver: I17-I19 still own the rest of the chain.
LINEAGE_GATE_STATE = "NOT_CLOSED"
LINEAGE_GATE_CLOSED = False


class IncompleteLineageError(ValueError):
    """Raised when a record cannot name its whole T0 chain (05 section 2)."""


class GenerationImmutableViolation(ValueError):
    """Raised when a published generation no longer matches its descriptor."""


class T1IdentityKey(NormalizationModelBase):
    """The deterministic inputs of a T1 record identity (05 section 4).

    Every member is durable evidence identity.  Notably ABSENT: every canonical
    numeric value, every quality flag, every timestamp of the observation, and
    anything environmental.  That absence is the guarantee, not an omission.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    sensor_family: SensorFamily
    provider: OpaqueIdentifier
    venue: OpaqueIdentifier
    contract_instance_id: OpaqueIdentifier | None = None
    native_identity_id: OpaqueIdentifier
    native_sequence_id: OpaqueIdentifier | None = None
    source_revision_id: OpaqueIdentifier
    normalization_generation: OpaqueIdentifier
    identity_schema_version: OpaqueIdentifier = IDENTITY_SCHEMA_VERSION

    @model_validator(mode="after")
    def _identity_law(self) -> T1IdentityKey:
        if self.identity_schema_version != IDENTITY_SCHEMA_VERSION:
            raise ValueError(
                "identity_schema_version must be the constant this module "
                f"implements ({IDENTITY_SCHEMA_VERSION}); a caller-chosen schema "
                "version would let two identities disagree about their own meaning"
            )
        return self


class GenerationDescriptor(NormalizationModelBase):
    """A T1 generation's defining descriptors (05 section 13).

    ``created_at`` is carried for the manifest and EXCLUDED from
    :func:`generation_fingerprint`, so two generations that differ only in build
    time are the same generation.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    generation_id: OpaqueIdentifier
    code_commit: OpaqueIdentifier
    identity_registry_version: RegistryVersion
    semantic_registry_version: RegistryVersion
    methodology_registry_version: RegistryVersion
    time_semantics_version: RegistryVersion
    source_revision_mode: OpaqueIdentifier
    input_manifest_refs: tuple[OpaqueIdentifier, ...] = Field(min_length=1)
    created_at: str | None = None

    @model_validator(mode="after")
    def _unique_refs(self) -> GenerationDescriptor:
        if len(set(self.input_manifest_refs)) != len(self.input_manifest_refs):
            raise ValueError("input_manifest_refs contains duplicate references")
        return self


def _canonical_bytes(payload: dict[str, object]) -> bytes:
    """Stable JSON bytes: sorted keys, no whitespace, ASCII-only."""
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")


def canonical_identity_bytes(key: T1IdentityKey) -> bytes:
    """The exact bytes an identity digest is taken over."""
    payload = key.model_dump(mode="json")
    return _canonical_bytes(payload)


def compute_t1_record_id(key: T1IdentityKey) -> T1RecordId:
    """Derive ``t1_record_id`` from the identity key.  Pure and reproducible.

    Content-addressed: SHA-256 over the canonical key bytes, prefixed ``t1:`` so a
    reader can tell a derived identity from an arbitrary opaque string.
    """
    digest = hashlib.sha256(canonical_identity_bytes(key)).hexdigest()
    return f"t1:{digest}"


def generation_fingerprint(descriptor: GenerationDescriptor) -> str:
    """SHA-256 over the generation's defining fields, excluding build metadata."""
    payload = descriptor.model_dump(mode="json")
    for field_name in GENERATION_NONDETERMINISTIC_FIELDS:
        payload.pop(field_name, None)
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def assert_generation_immutable(
    published: GenerationDescriptor, observed: GenerationDescriptor
) -> None:
    """Refuse any drift in a generation after publication (05 section 13).

    A new methodology must create a NEW generation, so a changed methodology
    version under the same generation id is exactly the violation this catches.
    """
    if published.generation_id != observed.generation_id:
        raise GenerationImmutableViolation(
            f"generation id changed: {published.generation_id!r} -> "
            f"{observed.generation_id!r}"
        )
    if generation_fingerprint(published) != generation_fingerprint(observed):
        raise GenerationImmutableViolation(
            f"generation {published.generation_id!r} is no longer byte-equivalent to "
            "its published descriptor: a generation is immutable after successful "
            "publication, and a new methodology requires a new generation "
            "(bloc_05/05 section 13)"
        )


def assert_lineage_complete(record: T1BaseEnvelope) -> None:
    """Refuse a record that cannot name its whole T0 chain (05 section 2).

    The three required links are checked by ``T1LineageRef`` itself, so this adds
    the record-level requirements the base model cannot know: the record must name
    its generation, its source revision and its code/config versions.
    """
    problems: list[str] = []
    if not record.lineage.raw_projection_refs:
        problems.append("no raw projection reference")
    if not record.lineage.acquisition_refs:
        problems.append("no acquisition reference")
    if not record.lineage.evidence_blob_hashes:
        problems.append("no evidence blob hash")
    if not record.normalization_generation:
        problems.append("no normalization generation")
    if not record.source_revision_id:
        problems.append("no source revision")
    if not record.lineage.code_version or not record.lineage.config_version:
        problems.append("no code/config version")
    if problems:
        raise IncompleteLineageError(
            "incomplete T1 lineage chain: " + "; ".join(problems)
        )


def lineage_completeness(record: T1BaseEnvelope) -> LineageState:
    """The record's lineage state as this module can prove it."""
    try:
        assert_lineage_complete(record)
    except IncompleteLineageError:
        return LineageState.LINEAGE_BROKEN
    return LineageState.LINEAGE_COMPLETE


def missing_sensor_families(covered: Iterable[SensorFamily | str]) -> tuple[str, ...]:
    """Required families with no accepted normalizer yet, in frozen order.

    This is the function that keeps the lineage gate honest: it can only close when
    this returns empty, and Wave 1 leaves it non-empty by construction.
    """
    present = {
        member.value if isinstance(member, SensorFamily) else str(member)
        for member in covered
    }
    return tuple(
        family for family in REQUIRED_SENSOR_FAMILIES if family not in present
    )
