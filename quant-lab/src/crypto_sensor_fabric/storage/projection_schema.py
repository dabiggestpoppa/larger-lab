"""SENSOR-B4-I05A/I05R1B — projection schema definition, fingerprint, key and registry.

The projection schema registry freezes the structural contract between a
provider-native parser and the T0B Parquet physical layer.

Key doctrines:

- ``projection_schema_id`` is a nonempty stable logical name (e.g.
  ``kraken_futures.market_analytics.liquidation_volume``).
- ``projection_schema_version`` is strict semver ``MAJOR.MINOR.PATCH``.
- ``schema_key`` = SHA-256(UTF-8(``schema_id + "@" + schema_version``)) —
  answers WHICH registered schema (full 64-char hex, never truncated).
- ``schema_fingerprint`` = deterministic structural fingerprint of the Arrow
  schema covering field name, Arrow logical type, nullable flag, and the FULL
  ordered required ``_t0_*`` metadata schema (name + Arrow type + nullable
  per column, I05R1 §34/§35) — answers WHAT exact field structure was
  registered.
- Provider-native input MUST NOT contain field names beginning ``_t0_``
  (reserved namespace).  Injection by the T0B layer is permitted.
- Same ``schema_id + schema_version`` MUST NOT resolve to two different
  structural schemas (``ProjectionSchemaConflict``).
- No lossy coercion.  No silent Arrow inference.
- Arrow type descriptors are LOSSLESS for every supported type and FAIL
  CLOSED (``UnsupportedProjectionSchemaType``) for anything that cannot be
  reconstructed exactly — never ``getattr(pa, name)()`` (I05R1 §37).
- Registry is immutable, durable and language-neutral: persisted as
  deterministic JSON through the shared ``DurableJsonCatalog`` primitive
  (I05R1 §4-§6) with hashed physical keys, physical-key binding, and
  corruption fail-closed reload self-validation (I05R1 §38).
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

import pyarrow as pa

from .json_catalog import (
    JsonCatalogConflict,
    JsonCatalogCorrupt,
    DurableJsonCatalog,
)
from .enums import SourceUnitContract
from .models import SourceUnitEvidence


_SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

# Required T0B metadata column names injected by the projection layer.
_T0_REQUIRED_COLUMNS: frozenset[str] = frozenset(
    {
        "_t0_projection_id",
        "_t0_source_blob_sha256",
        "_t0_acquisition_id",
        "_t0_provider",
        "_t0_venue",
        "_t0_sensor_family",
        "_t0_native_instrument",
        "_t0_parser_version",
        "_t0_schema_version",
        "_t0_row_ordinal",
    }
)

# ---------------------------------------------------------------------------
# THE canonical required T0 metadata schema (I05R1 §35 — defined ONCE).
#
# The same ordered schema is used by fingerprint generation, the projection
# writer, staged validation and readers.  No competing T0 field declarations
# are permitted anywhere else.
# ---------------------------------------------------------------------------

T0_METADATA_SCHEMA: pa.Schema = pa.schema(
    [
        pa.field("_t0_projection_id", pa.string(), nullable=False),
        # Multi-source rows with no defensible attribution may be NULL.
        pa.field("_t0_source_blob_sha256", pa.string(), nullable=True),
        pa.field("_t0_acquisition_id", pa.string(), nullable=True),
        pa.field("_t0_provider", pa.string(), nullable=False),
        pa.field("_t0_venue", pa.string(), nullable=False),
        pa.field("_t0_sensor_family", pa.string(), nullable=False),
        pa.field("_t0_native_instrument", pa.string(), nullable=False),
        pa.field("_t0_parser_version", pa.string(), nullable=False),
        pa.field("_t0_schema_version", pa.string(), nullable=False),
        pa.field("_t0_row_ordinal", pa.int64(), nullable=False),
    ]
)


def t0_metadata_descriptor() -> list[dict[str, Any]]:
    """Ordered canonical descriptor of the required T0 metadata schema."""
    return [
        {
            "name": field.name,
            "type": _arrow_type_descriptor(field.type),
            "nullable": field.nullable,
        }
        for field in T0_METADATA_SCHEMA
    ]


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def validate_semver(value: str, field_name: str = "projection_schema_version") -> None:
    """Validate strict semver MAJOR.MINOR.PATCH (no prerelease, no leading zeros)."""
    if not _SEMVER_RE.fullmatch(value):
        raise ValueError(
            f"{field_name} must be MAJOR.MINOR.PATCH (e.g. 1.0.0), got {value!r}"
        )


def _validate_nonempty_string(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a nonempty string, got {value!r}")


def _validate_reserved_columns(schema: pa.Schema) -> None:
    """Reject provider-native fields beginning with ``_t0_``.

    The T0B layer injects these; the provider must not collide.
    """
    for field in schema:
        if field.name.startswith("_t0_"):
            raise ReservedProjectionColumn(
                f"provider-native schema contains reserved column {field.name!r} "
                "beginning with _t0_ (injected by T0B layer)"
            )


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ReservedProjectionColumn(ValueError):
    """Provider-native schema contains a field beginning with ``_t0_``."""


class ProjectionSchemaConflict(ValueError):
    """Same schema_id + schema_version registered with different structure."""

    def __init__(self, schema_id: str, schema_version: str) -> None:
        self.schema_id = schema_id
        self.schema_version = schema_version
        super().__init__(
            f"projection_schema_id={schema_id!r} version={schema_version!r} "
            "already registered with a different structural schema"
        )


class ProjectionSchemaNotFound(KeyError):
    """Requested schema_id + schema_version not in the registry."""


class ProjectionSchemaCatalogCorrupt(RuntimeError):
    """A committed schema registry fragment is corrupt; fail closed.

    Raised for: invalid JSON, schema_key drift, fingerprint mismatch on
    reload, T0-metadata-contract drift, or a physical-key binding violation.
    A corrupt committed object may never silently become "not registered"
    (I05R1 §7/§38).  I08 later owns quarantine/recovery.
    """


class UnsupportedProjectionSchemaType(RuntimeError):
    """An Arrow type cannot be losslessly described/reconstructed.

    Fail closed: one unsupported schema is rejected rather than silently
    rebuilt differently (I05R1 §37).
    """


# ---------------------------------------------------------------------------
# Lossless Arrow type descriptors (I05R1 §36/§37)
# ---------------------------------------------------------------------------


def _arrow_type_descriptor(arrow_type: pa.DataType) -> dict[str, Any]:
    """Deterministic LOSSLESS structural descriptor for an Arrow logical type.

    Preserves the complete semantics of every supported type: widths/sign,
    decimal precision/scale, timestamp unit/timezone, date/time units,
    duration unit, fixed-size-binary width, list/large-list child name +
    nullability, struct child order/name/type/nullability, map key/value
    structure and ``keys_sorted``.

    Raises :class:`UnsupportedProjectionSchemaType` for any type that cannot
    be reconstructed exactly (dictionary, union, ...).  Never falls back to
    ``getattr(pa, name)()`` on reload.
    """
    # Nested / parameterized types first.
    if pa.types.is_timestamp(arrow_type):
        return {
            "type": "timestamp",
            "unit": str(arrow_type.unit),
            "tz": str(arrow_type.tz) if arrow_type.tz else None,
        }
    if pa.types.is_time32(arrow_type):
        return {"type": "time32", "unit": str(arrow_type.unit)}
    if pa.types.is_time64(arrow_type):
        return {"type": "time64", "unit": str(arrow_type.unit)}
    if pa.types.is_duration(arrow_type):
        return {"type": "duration", "unit": str(arrow_type.unit)}
    if pa.types.is_date32(arrow_type):
        return {"type": "date32", "unit": "day"}
    if pa.types.is_date64(arrow_type):
        return {"type": "date64", "unit": "ms"}
    if pa.types.is_fixed_size_binary(arrow_type):
        return {"type": "fixed_size_binary", "byte_width": arrow_type.byte_width}
    if pa.types.is_decimal128(arrow_type):
        return {
            "type": "decimal128",
            "precision": arrow_type.precision,
            "scale": arrow_type.scale,
        }
    if pa.types.is_decimal256(arrow_type):
        return {
            "type": "decimal256",
            "precision": arrow_type.precision,
            "scale": arrow_type.scale,
        }
    if pa.types.is_large_list(arrow_type):
        return {
            "type": "large_list",
            "value_name": arrow_type.value_field.name,
            "value_type": _arrow_type_descriptor(arrow_type.value_type),
            "value_nullable": arrow_type.value_field.nullable,
        }
    if pa.types.is_list(arrow_type):
        return {
            "type": "list",
            "value_name": arrow_type.value_field.name,
            "value_type": _arrow_type_descriptor(arrow_type.value_type),
            "value_nullable": arrow_type.value_field.nullable,
        }
    if pa.types.is_map(arrow_type):
        return {
            "type": "map",
            "key_type": _arrow_type_descriptor(arrow_type.key_type),
            "item_type": _arrow_type_descriptor(arrow_type.item_type),
            "keys_sorted": bool(arrow_type.keys_sorted),
        }
    if pa.types.is_struct(arrow_type):
        return {
            "type": "struct",
            "fields": [
                {
                    "name": f.name,
                    "type": _arrow_type_descriptor(f.type),
                    "nullable": f.nullable,
                }
                for f in arrow_type
            ],
        }
    # Fail closed on types this contract does not support losslessly.
    if (
        pa.types.is_dictionary(arrow_type)
        or pa.types.is_union(arrow_type)
        or pa.types.is_nested(arrow_type)
    ):
        raise UnsupportedProjectionSchemaType(
            f"Arrow type {arrow_type!s} is not supported by the lossless "
            "projection schema descriptor; fail closed"
        )
    # Primitive leaf types: str(t) is the canonical, stable Arrow name
    # (null, bool, int8..uint64, halffloat, float, double, string,
    # large_string, binary, large_binary).
    return {"type": str(arrow_type)}


# Canonical primitive-name whitelist — the ONLY names accepted on reload.
_PRIMITIVE_CTORS: dict[str, Any] = {
    "null": pa.null,
    "bool": pa.bool_,
    "int8": pa.int8,
    "int16": pa.int16,
    "int32": pa.int32,
    "int64": pa.int64,
    "uint8": pa.uint8,
    "uint16": pa.uint16,
    "uint32": pa.uint32,
    "uint64": pa.uint64,
    "halffloat": pa.float16,
    "float": pa.float32,
    "double": pa.float64,
    "string": pa.string,
    "large_string": pa.large_string,
    "binary": pa.binary,
    "large_binary": pa.large_binary,
}


def _rebuild_arrow_type(desc: dict[str, Any]) -> pa.DataType:
    """Exact inverse of :func:`_arrow_type_descriptor`.

    Unknown/unconstructable/malformed descriptors FAIL CLOSED with
    :class:`UnsupportedProjectionSchemaType` — there is no
    ``getattr(pa, name)()`` escape hatch (I05R1 §37).
    """
    try:
        return _rebuild_arrow_type_checked(desc)
    except UnsupportedProjectionSchemaType:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise UnsupportedProjectionSchemaType(
            f"cannot losslessly rebuild Arrow type descriptor {desc!r}: {exc!r}; "
            "fail closed (no getattr fallback)"
        ) from exc


def _rebuild_arrow_type_checked(desc: dict[str, Any]) -> pa.DataType:
    type_name = desc["type"]
    if type_name == "timestamp":
        return pa.timestamp(desc["unit"], tz=desc.get("tz"))
    if type_name == "time32":
        return pa.time32(desc["unit"])
    if type_name == "time64":
        return pa.time64(desc["unit"])
    if type_name == "duration":
        return pa.duration(desc["unit"])
    if type_name == "date32":
        return pa.date32()
    if type_name == "date64":
        return pa.date64()
    if type_name == "fixed_size_binary":
        return pa.binary(desc["byte_width"])
    if type_name == "decimal128":
        return pa.decimal128(desc["precision"], desc["scale"])
    if type_name == "decimal256":
        return pa.decimal256(desc["precision"], desc["scale"])
    if type_name == "list":
        return pa.list_(
            pa.field(
                desc.get("value_name", "item"),
                _rebuild_arrow_type(desc["value_type"]),
                nullable=desc.get("value_nullable", True),
            )
        )
    if type_name == "large_list":
        return pa.large_list(
            pa.field(
                desc.get("value_name", "item"),
                _rebuild_arrow_type(desc["value_type"]),
                nullable=desc.get("value_nullable", True),
            )
        )
    if type_name == "map":
        return pa.map_(
            _rebuild_arrow_type(desc["key_type"]),
            _rebuild_arrow_type(desc["item_type"]),
            keys_sorted=desc.get("keys_sorted", False),
        )
    if type_name == "struct":
        return pa.struct(
            [
                pa.field(f["name"], _rebuild_arrow_type(f["type"]), f["nullable"])
                for f in desc["fields"]
            ]
        )
    ctor = _PRIMITIVE_CTORS.get(type_name)
    if ctor is None:
        raise UnsupportedProjectionSchemaType(
            f"cannot losslessly rebuild Arrow type descriptor {desc!r}; "
            "fail closed (no getattr fallback)"
        )
    return ctor()


# ---------------------------------------------------------------------------
# Schema fingerprint
# ---------------------------------------------------------------------------


def _field_descriptor(field: pa.Field) -> dict[str, Any]:
    return {
        "name": field.name,
        "type": _arrow_type_descriptor(field.type),
        "nullable": field.nullable,
    }


def resolve_unit_field_path(
    schema: pa.Schema, field_path: Iterable[str]
) -> tuple[tuple[str, str], ...]:
    """Resolve one structural source-unit path against an Arrow schema.

    I16R2 §12: a source-unit location is a deterministic structural path
    (never a dotted string).  Traversal is type-driven and fails closed:

    * component 0 must be a top-level provider-native field;
    * a component under a ``list``/``large_list`` type must equal the Arrow
      list value-field name (Arrow's default element name is ``item``);
    * a component under a ``struct`` type must name a struct child field;
    * any other intermediate type is not traversable;
    * the terminal field must be a string (the native unit lexeme).

    Returns the ordered traversal steps for value walking:
    ``("struct_field", name)`` / ``("list_element", name)``.
    """
    components = tuple(field_path)
    if not components:
        raise ValueError(
            "unit evidence field_path must be a nonempty structural path"
        )
    root = components[0]
    try:
        field = schema.field(root)
    except KeyError as exc:
        raise ValueError(
            f"unit evidence path root {root!r} is not a provider-native "
            "field of this schema; fail closed"
        ) from exc
    current: pa.DataType = field.type
    steps: list[tuple[str, str]] = []
    for component in components[1:]:
        if pa.types.is_list(current) or pa.types.is_large_list(current):
            if component != current.value_field.name:
                raise ValueError(
                    f"unit evidence path step {component!r} must equal the "
                    f"Arrow list value-field name "
                    f"{current.value_field.name!r} at {current!s}; fail closed"
                )
            steps.append(("list_element", component))
            current = current.value_field.type
        elif pa.types.is_struct(current):
            try:
                child = current.field(component)
            except KeyError as exc:
                raise ValueError(
                    f"unit evidence path step {component!r} is not a child "
                    f"field of {current!s}; fail closed"
                ) from exc
            steps.append(("struct_field", component))
            current = child.type
        else:
            raise ValueError(
                f"unit evidence path step {component!r} cannot address "
                f"Arrow type {current!s}; only list/struct nesting is "
                "traversable; fail closed"
            )
    if not (pa.types.is_string(current) or pa.types.is_large_string(current)):
        raise ValueError(
            "unit evidence path must terminate at a string field (the "
            f"native unit lexeme); got {current!s}; fail closed"
        )
    return tuple(steps)


def compute_schema_fingerprint(
    schema: pa.Schema,
    source_unit_evidence: Iterable[SourceUnitEvidence] | None = None,
    source_unit_contract: SourceUnitContract | None = None,
) -> str:
    """Deterministic structural fingerprint of an Arrow schema.

    Covers, in order: every provider-native field (name, Arrow logical type,
    nullable flag) PLUS the FULL ordered required ``_t0_*`` metadata schema
    (name + Arrow type + nullable per column — I05R1 §34/§35, so a
    ``_t0_row_ordinal`` int64→string change alters the fingerprint).

    I16R1 ADDITIVE extension: when the definition declares durable
    source-unit evidence, the canonical declaration list (sorted by field
    name / structural path) is part of the fingerprinted contract too, so a
    changed unit declaration is a changed schema contract.  I16R2 extends
    the same law to the explicit unit-contract marker.  When NO declaration
    exists the fingerprint is byte-identical to the pre-I16R1 formula —
    historical descriptors keep verifying under their historical contract.

    Returns full 64-char lowercase SHA-256 hex.  The fingerprint answers:
    WHAT EXACT FIELD STRUCTURE WAS REGISTERED?  It is separate from
    schema_key (WHICH REGISTERED SCHEMA ID/VERSION?).
    """
    fields_desc = [_field_descriptor(field) for field in schema]
    descriptor: dict[str, Any] = {
        "fields": fields_desc,
        "t0_metadata_schema": t0_metadata_descriptor(),
    }
    evidence = tuple(source_unit_evidence or ())
    if evidence:
        descriptor["source_unit_evidence"] = [
            e.to_descriptor()
            for e in sorted(evidence, key=lambda e: e.resolved_field_path)
        ]
    if source_unit_contract is not None:
        descriptor["source_unit_contract"] = source_unit_contract.value
    canonical = json.dumps(
        descriptor, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


# ---------------------------------------------------------------------------
# Schema key
# ---------------------------------------------------------------------------


def compute_schema_key(schema_id: str, schema_version: str) -> str:
    """Deterministic schema registry key.

    ``schema_key`` = SHA-256(UTF-8(``schema_id + "@" + schema_version``)).

    Full 64-char hex, never truncated.  Answers WHICH registered schema
    id/version (structural integrity is a separate fingerprint check).
    """
    identity = f"{schema_id}@{schema_version}".encode("utf-8")
    return hashlib.sha256(identity).hexdigest()


# ---------------------------------------------------------------------------
# ProjectionSchemaDefinition
# ---------------------------------------------------------------------------


class ProjectionSchemaDefinition:
    """Frozen projection schema definition (I05 §24).

    Attributes:
        projection_schema_id: Nonempty stable logical name.
        projection_schema_version: Strict semver MAJOR.MINOR.PATCH.
        provider_native_schema: The Arrow schema for provider-native columns
            (does NOT include the ``_t0_*`` metadata columns — those are
            injected by the projection writer).
        schema_key: Deterministic registry key (SHA-256 of id@version).
        schema_fingerprint: Deterministic structural fingerprint of the
            provider_native_schema plus the full required T0 metadata schema.
    """

    def __init__(
        self,
        projection_schema_id: str,
        projection_schema_version: str,
        provider_native_schema: pa.Schema,
        source_unit_evidence: Iterable[SourceUnitEvidence] | None = None,
        source_unit_contract: SourceUnitContract | str | None = None,
    ) -> None:
        _validate_nonempty_string(projection_schema_id, "projection_schema_id")
        validate_semver(projection_schema_version)
        if not isinstance(provider_native_schema, pa.Schema):
            raise TypeError(
                f"provider_native_schema must be pa.Schema, "
                f"got {type(provider_native_schema).__name__}"
            )
        _validate_reserved_columns(provider_native_schema)
        # Lossless descriptor round-trip is verified EAGERLY: a schema that
        # cannot be described and reconstructed exactly never registers.
        for field in provider_native_schema:
            rebuilt = _rebuild_arrow_type(_arrow_type_descriptor(field.type))
            if not field.type.equals(rebuilt):
                raise UnsupportedProjectionSchemaType(
                    f"Arrow type {field.type!s} of field {field.name!r} does "
                    "not survive a lossless descriptor round trip; fail closed"
                )

        # I16R1: durable source-unit declarations.  Each declaration must
        # name a REAL provider-native field of THIS schema (fail closed on
        # contradictions) and appear at most once (no silent dedupe).
        # I16R2 §12: a nested declaration must RESOLVE against this Arrow
        # schema (list/struct traversal, string terminal) at registration
        # time — an unresolvable structural path never registers.
        native_names = {field.name for field in provider_native_schema}
        evidence_list: list[SourceUnitEvidence] = []
        seen_fields: set[tuple[str, ...]] = set()
        for entry in source_unit_evidence or ():
            evidence = (
                entry
                if isinstance(entry, SourceUnitEvidence)
                else SourceUnitEvidence.from_descriptor(entry)
            )
            if evidence.field_name not in native_names:
                raise ValueError(
                    f"source-unit evidence names field "
                    f"{evidence.field_name!r}, which is not a provider-native "
                    "field of this schema; fail closed"
                )
            if evidence.field_path is not None:
                resolve_unit_field_path(provider_native_schema, evidence.field_path)
            path = evidence.resolved_field_path
            if path in seen_fields:
                raise ValueError(
                    "duplicate source-unit evidence for field path "
                    f"{list(path)!r}; conflicting declarations fail closed "
                    "(no silent dedupe)"
                )
            seen_fields.add(path)
            evidence_list.append(evidence)

        if isinstance(source_unit_contract, str):
            source_unit_contract = SourceUnitContract(source_unit_contract)
        if (
            source_unit_contract is SourceUnitContract.NO_UNIT_FIELDS
            and evidence_list
        ):
            raise ValueError(
                "source_unit_contract=NO_UNIT_FIELDS forbids source-unit "
                "evidence entries; fail closed"
            )
        if (
            source_unit_contract is SourceUnitContract.UNIT_EVIDENCE_DECLARED
            and not evidence_list
        ):
            raise ValueError(
                "source_unit_contract=UNIT_EVIDENCE_DECLARED requires at "
                "least one evidence entry; fail closed"
            )

        self.projection_schema_id = projection_schema_id
        self.projection_schema_version = projection_schema_version
        self.provider_native_schema = provider_native_schema
        self.source_unit_evidence: tuple[SourceUnitEvidence, ...] = tuple(
            sorted(evidence_list, key=lambda e: e.resolved_field_path)
        )
        self.source_unit_contract: SourceUnitContract | None = source_unit_contract
        self.schema_key = compute_schema_key(
            projection_schema_id, projection_schema_version
        )
        self.schema_fingerprint = compute_schema_fingerprint(
            provider_native_schema,
            self.source_unit_evidence,
            self.source_unit_contract,
        )

    @property
    def schema_identity(self) -> str:
        """Logical registry identity ``id@version`` (the catalog logical ID)."""
        return f"{self.projection_schema_id}@{self.projection_schema_version}"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProjectionSchemaDefinition):
            return NotImplemented
        return (
            self.projection_schema_id == other.projection_schema_id
            and self.projection_schema_version == other.projection_schema_version
            and self.schema_fingerprint == other.schema_fingerprint
        )

    def __repr__(self) -> str:
        return (
            f"ProjectionSchemaDefinition("
            f"schema_id={self.projection_schema_id!r}, "
            f"version={self.projection_schema_version!r}, "
            f"key={self.schema_key!r})"
        )

    def to_descriptor(self) -> dict[str, Any]:
        """Language-neutral JSON-serializable descriptor for persistence.

        I16R1: ``source_unit_evidence`` appears only when the definition
        declares at least one source-unit field; a definition with no
        declaration serializes exactly as it did before I16R1.  I16R2:
        ``source_unit_contract`` appears only when an explicit marker was
        declared — an absent marker plus an empty list is
        HISTORICAL_UNIT_CONTRACT_ABSENT and serializes exactly as before.
        """
        fields = [_field_descriptor(field) for field in self.provider_native_schema]
        descriptor = {
            "schema_identity": self.schema_identity,
            "projection_schema_id": self.projection_schema_id,
            "projection_schema_version": self.projection_schema_version,
            "schema_key": self.schema_key,
            "schema_fingerprint": self.schema_fingerprint,
            "provider_native_fields": fields,
            "t0_metadata_schema": t0_metadata_descriptor(),
        }
        if self.source_unit_evidence:
            descriptor["source_unit_evidence"] = [
                e.to_descriptor() for e in self.source_unit_evidence
            ]
        if self.source_unit_contract is not None:
            descriptor["source_unit_contract"] = self.source_unit_contract.value
        return descriptor

    @classmethod
    def from_descriptor(
        cls, descriptor: dict[str, Any]
    ) -> ProjectionSchemaDefinition:
        """Reconstruct from a persisted descriptor with self-validation.

        Raises ``ValueError`` on fingerprint mismatch and
        ``UnsupportedProjectionSchemaType``/``ValueError`` on T0-metadata
        contract drift — callers (the registry) fail closed.
        """
        schema_id = descriptor["projection_schema_id"]
        schema_version = descriptor["projection_schema_version"]
        fields_desc = descriptor["provider_native_fields"]
        pa_fields = [
            pa.field(fd["name"], _rebuild_arrow_type(fd["type"]), fd["nullable"])
            for fd in fields_desc
        ]
        schema = pa.schema(pa_fields)
        # I16R1 additive source-unit declarations.  A historical descriptor
        # without the key loads under its historical contract: absence means
        # UNKNOWN HISTORICAL CONTRACT, never VERIFIED_NATIVE.  I16R2 adds
        # the optional explicit contract marker on the same law.
        raw_units = descriptor.get("source_unit_evidence")
        unit_evidence = (
            [SourceUnitEvidence.from_descriptor(entry) for entry in raw_units]
            if raw_units is not None
            else None
        )
        raw_contract = descriptor.get("source_unit_contract")
        unit_contract = (
            SourceUnitContract(raw_contract) if raw_contract is not None else None
        )
        definition = cls(
            schema_id,
            schema_version,
            schema,
            source_unit_evidence=unit_evidence,
            source_unit_contract=unit_contract,
        )
        # Fingerprint integrity (I05R1 §38).
        if definition.schema_fingerprint != descriptor["schema_fingerprint"]:
            raise ValueError(
                "descriptor fingerprint mismatch — schema may have been modified"
            )
        # Registry self-consistency: stored key must hash from stored id/version.
        stored_key = descriptor.get("schema_key")
        if stored_key != definition.schema_key:
            raise ValueError(
                f"descriptor schema_key drift: stored {stored_key!r} but "
                f"computed {definition.schema_key!r}"
            )
        # The required T0 metadata schema is part of the frozen contract —
        # a stored fragment describing different T0 columns is corrupt.
        stored_t0 = descriptor.get("t0_metadata_schema")
        if stored_t0 != t0_metadata_descriptor():
            raise ValueError(
                "descriptor required-T0-metadata schema does not match the "
                "current registered T0 contract; catalog corrupt"
            )
        return definition


# ---------------------------------------------------------------------------
# ProjectionSchemaRegistry — immutable, durable local catalog (I05R1 §4-§6)
# ---------------------------------------------------------------------------


class ProjectionSchemaRegistry:
    """Immutable durable projection schema registry.

    Persists schema definitions under
    ``<t0_root>/catalogs/projection_schemas/`` via the shared
    ``DurableJsonCatalog`` primitive: staged write -> fsync -> verify ->
    no-clobber publish -> parent-dir fsync.  One JSON file per schema_key
    (the 64-char SHA-256 of ``id@version``).

    Same ``schema_id + schema_version`` with a different structural schema is
    ``ProjectionSchemaConflict``.  A corrupt committed fragment raises
    ``ProjectionSchemaCatalogCorrupt`` — it never silently disappears.

    Language-neutral persistence (no pickled pa.Schema, no Python repr).
    """

    def __init__(self, catalog_root: str | Path) -> None:
        self._root = Path(catalog_root)
        try:
            self._catalog = DurableJsonCatalog(
                self._root, logical_id_field="schema_identity"
            )
        except JsonCatalogCorrupt as exc:
            raise ProjectionSchemaCatalogCorrupt(str(exc)) from exc
        # schema_key -> rebuilt definition cache
        self._cache: dict[str, ProjectionSchemaDefinition] = {}
        # Validate every committed fragment on load (I05R1 §38): parse,
        # rebuild, verify fingerprint + key + T0 contract.
        for logical_id, payload in list(self._catalog_items()):
            definition = self._definition_from_payload(payload)
            self._cache[definition.schema_key] = definition

    @property
    def root(self) -> Path:
        """Public read-only schema catalog root (I13R3 §13)."""
        return self._root

    # -- internals -----------------------------------------------------------

    def _catalog_items(self) -> list[tuple[str, dict[str, Any]]]:
        return [(lid, self._catalog.get(lid) or {}) for lid in self._catalog.list_ids()]

    def _definition_from_payload(
        self, payload: dict[str, Any]
    ) -> ProjectionSchemaDefinition:
        try:
            return ProjectionSchemaDefinition.from_descriptor(payload)
        except (ValueError, KeyError, TypeError, UnsupportedProjectionSchemaType) as exc:
            raise ProjectionSchemaCatalogCorrupt(
                f"schema registry fragment {payload.get('schema_identity')!r} "
                f"is corrupt: {exc}"
            ) from exc

    # -- registration --------------------------------------------------------

    def register(self, definition: ProjectionSchemaDefinition) -> ProjectionSchemaDefinition:
        """Register a schema definition.  Idempotent for exact duplicates.

        Raises ``ProjectionSchemaConflict`` if same schema_key but different
        fingerprint is already registered, and
        ``ProjectionSchemaCatalogCorrupt`` if a committed fragment is corrupt.

        Returns the registered definition.
        """
        try:
            self._catalog.commit(definition.schema_identity, definition.to_descriptor())
        except JsonCatalogConflict as exc:
            raise ProjectionSchemaConflict(
                definition.projection_schema_id,
                definition.projection_schema_version,
            ) from exc
        except JsonCatalogCorrupt as exc:
            raise ProjectionSchemaCatalogCorrupt(str(exc)) from exc
        self._cache[definition.schema_key] = definition
        return definition

    # -- resolution ----------------------------------------------------------

    def resolve(self, schema_key: str) -> ProjectionSchemaDefinition:
        """Resolve a schema_key to its definition.

        Raises ``ProjectionSchemaNotFound`` if not registered.
        """
        if schema_key in self._cache:
            return self._cache[schema_key]
        # Find the catalog payload whose stored schema_key matches.  (The
        # physical filename is the hash of the logical id@version, which IS
        # the schema_key — see binding validation in DurableJsonCatalog.)
        for logical_id, payload in self._catalog_items():
            if payload.get("schema_key") == schema_key:
                definition = self._definition_from_payload(payload)
                self._cache[schema_key] = definition
                return definition
        raise ProjectionSchemaNotFound(
            f"schema_key {schema_key!r} not found in registry"
        )

    def resolve_by_id(
        self, schema_id: str, schema_version: str
    ) -> ProjectionSchemaDefinition:
        """Resolve by schema_id + schema_version."""
        key = compute_schema_key(schema_id, schema_version)
        return self.resolve(key)

    def has(self, schema_key: str) -> bool:
        """Check if a schema_key is registered."""
        try:
            self.resolve(schema_key)
        except ProjectionSchemaNotFound:
            return False
        return True

    def list_keys(self) -> list[str]:
        """Return all registered schema_keys (sorted)."""
        return sorted(self._cache.keys())


__all__ = [
    "ProjectionSchemaDefinition",
    "ProjectionSchemaRegistry",
    "ProjectionSchemaConflict",
    "ProjectionSchemaCatalogCorrupt",
    "ProjectionSchemaNotFound",
    "ReservedProjectionColumn",
    "UnsupportedProjectionSchemaType",
    "T0_METADATA_SCHEMA",
    "compute_schema_fingerprint",
    "compute_schema_key",
    "resolve_unit_field_path",
    "t0_metadata_descriptor",
    "validate_semver",
]
