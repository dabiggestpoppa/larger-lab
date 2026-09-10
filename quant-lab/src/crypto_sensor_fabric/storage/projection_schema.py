"""SENSOR-B4-I05A — projection schema definition, fingerprint, key and registry.

The projection schema registry freezes the structural contract between a
provider-native parser and the T0B Parquet physical layer.

Key doctrines:

- ``projection_schema_id`` is a nonempty stable logical name (e.g.
  ``kraken_futures.market_analytics.liquidation_volume``).
- ``projection_schema_version`` is strict semver ``MAJOR.MINOR.PATCH``.
- ``schema_key`` = SHA-256(UTF-8(``schema_id + "@" + schema_version``)) —
  answers WHICH registered schema (full 64-char hex, never truncated).
- ``schema_fingerprint`` = deterministic structural fingerprint of the Arrow
  schema covering field name, Arrow logical type, nullable flag, and required
  ``_t0_*`` metadata columns — answers WHAT exact field structure was
  registered.
- Provider-native input MUST NOT contain field names beginning ``_t0_``
  (reserved namespace).  Injection by the T0B layer is permitted.
- Same ``schema_id + schema_version`` MUST NOT resolve to two different
  structural schemas (``ProjectionSchemaConflict``).
- No lossy coercion.  No silent Arrow inference.
- Registry is immutable and language-neutral: persisted as deterministic JSON
  under ``<t0_root>/catalogs/projection_schemas/``.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pyarrow as pa


_SEMVER_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")

# Required T0B metadata columns injected by the projection layer.
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


# ---------------------------------------------------------------------------
# Schema fingerprint
# ---------------------------------------------------------------------------


def _arrow_type_descriptor(arrow_type: pa.DataType) -> dict[str, Any]:
    """Deterministic structural descriptor for an Arrow logical type.

    Covers the essential structural dimensions without relying on Python
    repr of arbitrary objects.  Language-neutral: a future non-Python
    implementation could reproduce this descriptor.
    """
    # Timestamp: unit + timezone
    if pa.types.is_timestamp(arrow_type):
        return {
            "type": "timestamp",
            "unit": str(arrow_type.unit),
            "tz": str(arrow_type.tz) if arrow_type.tz else None,
        }
    # Large types
    if pa.types.is_large_string(arrow_type):
        return {"type": "large_string"}
    if pa.types.is_large_binary(arrow_type):
        return {"type": "large_binary"}
    # Fixed-size binary
    if pa.types.is_fixed_size_binary(arrow_type):
        return {"type": "fixed_size_binary", "byte_width": arrow_type.byte_width}
    # Decimal
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
    # List types
    if pa.types.is_list(arrow_type):
        return {
            "type": "list",
            "value_type": _arrow_type_descriptor(arrow_type.value_type),
        }
    if pa.types.is_large_list(arrow_type):
        return {
            "type": "large_list",
            "value_type": _arrow_type_descriptor(arrow_type.value_type),
        }
    if pa.types.is_map(arrow_type):
        return {
            "type": "map",
            "key_type": _arrow_type_descriptor(arrow_type.key_type),
            "value_type": _arrow_type_descriptor(arrow_type.item_type),
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
    # Primitive types — just use the type name
    return {"type": str(arrow_type)}


def compute_schema_fingerprint(schema: pa.Schema) -> str:
    """Deterministic structural fingerprint of an Arrow schema.

    Covers, in order: field name, Arrow logical type, nullable flag, and
    required ``_t0_*`` metadata columns.  Returns full 64-char lowercase
    SHA-256 hex.

    The fingerprint answers: WHAT EXACT FIELD STRUCTURE WAS REGISTERED?
    It is separate from schema_key (WHICH REGISTERED SCHEMA ID/VERSION?).
    """
    fields_desc: list[dict[str, Any]] = []
    for field in schema:
        fields_desc.append(
            {
                "name": field.name,
                "type": _arrow_type_descriptor(field.type),
                "nullable": field.nullable,
            }
        )
    descriptor = {
        "fields": fields_desc,
        "t0_metadata_columns": sorted(_T0_REQUIRED_COLUMNS),
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
            provider_native_schema plus required T0 metadata columns.
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

        self.projection_schema_id = projection_schema_id
        self.projection_schema_version = projection_schema_version
        self.provider_native_schema = provider_native_schema
        self.schema_key = compute_schema_key(
            projection_schema_id, projection_schema_version
        )
        self.schema_fingerprint = compute_schema_fingerprint(provider_native_schema)

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
        fields: list[dict[str, Any]] = []
        for field in self.provider_native_schema:
            fields.append(
                {
                    "name": field.name,
                    "type": _arrow_type_descriptor(field.type),
                    "nullable": field.nullable,
                }
            )
        return {
            "projection_schema_id": self.projection_schema_id,
            "projection_schema_version": self.projection_schema_version,
            "schema_key": self.schema_key,
            "schema_fingerprint": self.schema_fingerprint,
            "provider_native_fields": fields,
            "t0_required_columns": sorted(_T0_REQUIRED_COLUMNS),
        }

    @classmethod
    def from_descriptor(
        cls, descriptor: dict[str, Any]
    ) -> ProjectionSchemaDefinition:
        """Reconstruct from a persisted descriptor (round-trip)."""
        schema_id = descriptor["projection_schema_id"]
        schema_version = descriptor["projection_schema_version"]
        fields_desc = descriptor["provider_native_fields"]
        pa_fields = []
        for fd in fields_desc:
            pa_fields.append(pa.field(fd["name"], _rebuild_arrow_type(fd["type"]), fd["nullable"]))
        schema = pa.schema(pa_fields)
        definition = cls(schema_id, schema_version, schema)
        # Verify fingerprint integrity
        if definition.schema_fingerprint != descriptor["schema_fingerprint"]:
            raise ValueError(
                "descriptor fingerprint mismatch — schema may have been modified"
            )
        return definition


def _rebuild_arrow_type(desc: dict[str, Any]) -> pa.DataType:
    """Rebuild an Arrow DataType from a descriptor produced by
    ``_arrow_type_descriptor``."""
    type_name = desc["type"]
    if type_name == "timestamp":
        return pa.timestamp(desc["unit"], tz=desc.get("tz"))
    if type_name == "large_string":
        return pa.large_string()
    if type_name == "large_binary":
        return pa.large_binary()
    if type_name == "fixed_size_binary":
        return pa.binary(desc["byte_width"])
    if type_name == "decimal128":
        return pa.decimal128(desc["precision"], desc["scale"])
    if type_name == "decimal256":
        return pa.decimal256(desc["precision"], desc["scale"])
    if type_name == "list":
        return pa.list_(_rebuild_arrow_type(desc["value_type"]))
    if type_name == "large_list":
        return pa.large_list(_rebuild_arrow_type(desc["value_type"]))
    if type_name == "map":
        return pa.map_(
            _rebuild_arrow_type(desc["key_type"]),
            _rebuild_arrow_type(desc["value_type"]),
        )
    if type_name == "struct":
        struct_fields = [
            pa.field(f["name"], _rebuild_arrow_type(f["type"]), f["nullable"])
            for f in desc["fields"]
        ]
        return pa.struct(struct_fields)
    # Primitive types — map canonical descriptor names to pa constructors
    _TYPE_MAP: dict[str, Any] = {
        "bool": pa.bool_,
        "int8": pa.int8,
        "int16": pa.int16,
        "int32": pa.int32,
        "int64": pa.int64,
        "uint8": pa.uint8,
        "uint16": pa.uint16,
        "uint32": pa.uint32,
        "uint64": pa.uint64,
        "float": pa.float16,
        "float16": pa.float16,
        "float32": pa.float32,
        "double": pa.float64,
        "float64": pa.float64,
        "string": pa.string,
        "utf8": pa.utf8,
        "binary": pa.binary,
        "date32": pa.date32,
        "date64": pa.date64,
        "time32": lambda: pa.time32("ms"),
        "time64": lambda: pa.time64("us"),
        "null": pa.null,
    }
    ctor = _TYPE_MAP.get(type_name)
    if ctor is not None:
        return ctor() if callable(ctor) else ctor
    return getattr(pa, type_name)()


# ---------------------------------------------------------------------------
# ProjectionSchemaRegistry — immutable local catalog
# ---------------------------------------------------------------------------


class ProjectionSchemaRegistry:
    """Immutable local projection schema registry.

    Persists schema definitions under ``<t0_root>/catalogs/projection_schemas/``.
    One JSON file per ``schema_key`` (the 64-char SHA-256).  Same
    ``schema_id + schema_version`` with a different structural schema is
    ``ProjectionSchemaConflict``.

    Language-neutral persistence (no pickled pa.Schema, no Python repr).
    """

    def __init__(self, catalog_root: str | Path) -> None:
        self._root = Path(catalog_root)
        self._root.mkdir(parents=True, exist_ok=True)
        # In-memory cache keyed by schema_key
        self._cache: dict[str, ProjectionSchemaDefinition] = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all persisted schema definitions into memory."""
        for path in self._root.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                definition = ProjectionSchemaDefinition.from_descriptor(data)
                self._cache[definition.schema_key] = definition
            except (json.JSONDecodeError, KeyError, ValueError):
                continue  # skip corrupt entries — they will be re-registered

    def register(self, definition: ProjectionSchemaDefinition) -> ProjectionSchemaDefinition:
        """Register a schema definition.  Idempotent for exact duplicates.

        Raises ``ProjectionSchemaConflict`` if same schema_key but different
        fingerprint is already registered.

        Returns the registered definition.
        """
        key = definition.schema_key
        if key in self._cache:
            existing = self._cache[key]
            if existing.schema_fingerprint != definition.schema_fingerprint:
                raise ProjectionSchemaConflict(
                    definition.projection_schema_id,
                    definition.projection_schema_version,
                )
            return existing

        # Persist
        path = self._root / f"{key}.json"
        path.write_text(
            json.dumps(
                definition.to_descriptor(),
                sort_keys=True,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        self._cache[key] = definition
        return definition

    def resolve(self, schema_key: str) -> ProjectionSchemaDefinition:
        """Resolve a schema_key to its definition.

        Raises ``ProjectionSchemaNotFound`` if not registered.
        """
        if schema_key not in self._cache:
            raise ProjectionSchemaNotFound(
                f"schema_key {schema_key!r} not found in registry"
            )
        return self._cache[schema_key]

    def resolve_by_id(
        self, schema_id: str, schema_version: str
    ) -> ProjectionSchemaDefinition:
        """Resolve by schema_id + schema_version."""
        key = compute_schema_key(schema_id, schema_version)
        return self.resolve(key)

    def has(self, schema_key: str) -> bool:
        """Check if a schema_key is registered."""
        return schema_key in self._cache

    def list_keys(self) -> list[str]:
        """Return all registered schema_keys (sorted)."""
        return sorted(self._cache.keys())


__all__ = [
    "ProjectionSchemaDefinition",
    "ProjectionSchemaRegistry",
    "ProjectionSchemaConflict",
    "ProjectionSchemaNotFound",
    "ReservedProjectionColumn",
    "compute_schema_fingerprint",
    "compute_schema_key",
    "validate_semver",
]
