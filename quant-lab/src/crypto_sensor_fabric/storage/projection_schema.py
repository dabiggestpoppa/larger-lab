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
from typing import Any

import pyarrow as pa

from .json_catalog import (
    JsonCatalogConflict,
    JsonCatalogCorrupt,
    DurableJsonCatalog,
)


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


def compute_schema_fingerprint(schema: pa.Schema) -> str:
    """Deterministic structural fingerprint of an Arrow schema.

    Covers, in order: every provider-native field (name, Arrow logical type,
    nullable flag) PLUS the FULL ordered required ``_t0_*`` metadata schema
    (name + Arrow type + nullable per column — I05R1 §34/§35, so a
    ``_t0_row_ordinal`` int64→string change alters the fingerprint).

    Returns full 64-char lowercase SHA-256 hex.  The fingerprint answers:
    WHAT EXACT FIELD STRUCTURE WAS REGISTERED?  It is separate from
    schema_key (WHICH REGISTERED SCHEMA ID/VERSION?).
    """
    fields_desc = [_field_descriptor(field) for field in schema]
    descriptor = {
        "fields": fields_desc,
        "t0_metadata_schema": t0_metadata_descriptor(),
    }
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

        self.projection_schema_id = projection_schema_id
        self.projection_schema_version = projection_schema_version
        self.provider_native_schema = provider_native_schema
        self.schema_key = compute_schema_key(
            projection_schema_id, projection_schema_version
        )
        self.schema_fingerprint = compute_schema_fingerprint(provider_native_schema)

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
        """Language-neutral JSON-serializable descriptor for persistence."""
        fields = [_field_descriptor(field) for field in self.provider_native_schema]
        return {
            "schema_identity": self.schema_identity,
            "projection_schema_id": self.projection_schema_id,
            "projection_schema_version": self.projection_schema_version,
            "schema_key": self.schema_key,
            "schema_fingerprint": self.schema_fingerprint,
            "provider_native_fields": fields,
            "t0_metadata_schema": t0_metadata_descriptor(),
        }

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
        definition = cls(schema_id, schema_version, schema)
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
    "t0_metadata_descriptor",
    "validate_semver",
]
