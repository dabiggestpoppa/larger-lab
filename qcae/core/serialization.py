"""Schema-versioned serialization base for QCAE core domain records.

Every durable QCAE domain object serializes through a versioned envelope:

    {"schema_version": <int>, "object_type": "<stable name>", ...fields}

Contract rules (canon Book V 15.2 invariant 5):

- Readers fail closed on unknown schema versions or unknown object types
  (QcaeSchemaVersionError / QcaeUnknownTypeError) instead of guessing.
- Serialization is canonical: deterministic field order, stable key sets, and
  no environment-dependent values. Equal domain records always produce equal
  serialized dicts, so content addressing (P1) can hash the payload directly.
- Each concrete record class owns exactly one SCHEMA_VERSION and its declared
  field set. Evolving a schema means bumping SCHEMA_VERSION and teaching
  readers about the new version explicitly.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, ClassVar, Dict, Tuple, Type, TypeVar, get_origin, get_type_hints

from qcae.core.errors import (
    QcaeSerializationError,
    QcaeSchemaVersionError,
    QcaeUnknownTypeError,
)

T = TypeVar("T", bound="SerializableRecord")


def canonical_json_bytes(data: Any) -> bytes:
    """Deterministic JSON encoding used for digests and round-trip evidence."""
    try:
        return json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise QcaeSerializationError(f"value is not canonically serializable: {exc}") from exc


def sha256_of(data: Any) -> str:
    """sha256 hex digest over the canonical encoding of ``data``."""
    return hashlib.sha256(canonical_json_bytes(data)).hexdigest()


class SerializableRecord:
    """Base for versioned, canonically serializable QCAE domain records.

    Subclasses must be frozen dataclasses declaring:

    - ``SCHEMA_VERSION: ClassVar[int]`` — this class's payload version;
    - an exact field set matching ``_serialized_fields()``.
    """

    SCHEMA_VERSION: ClassVar[int]

    # Fields holding nested SerializableRecord values, mapped to their record
    # class so from_dict can rebuild them. Concrete classes declare this only
    # when they actually embed nested records.
    _NESTED_RECORDS: ClassVar[Dict[str, Type["SerializableRecord"]]] = {}

    # Field-name -> coercion callable applied to raw deserialized values before
    # construction (used to rebuild enums from their serialized strings).
    # Unknown values pass through so validate() reports the domain error.
    _COERCIONS: ClassVar[Dict[str, Any]] = {}

    _TYPE_HINTS_CACHE: ClassVar[Dict[type, Any]] = {}

    def __post_init__(self) -> None:
        """Canonicalize declared sequence types so equal records compare equal.

        JSON flattens tuples to arrays and callers may pass either form; a
        tuple-declared field therefore always holds a tuple in memory, and a
        list-declared field always a list. This keeps digests and equality
        deterministic regardless of how the record was constructed.
        """
        cls = type(self)
        hints = cls._hints()
        if not hints:
            return
        for fld in fields(cls):
            origin = get_origin(hints.get(fld.name))
            if origin is None:
                continue
            value = getattr(self, fld.name)
            if origin is tuple and isinstance(value, list):
                object.__setattr__(self, fld.name, tuple(value))
            elif origin is list and isinstance(value, tuple):
                object.__setattr__(self, fld.name, list(value))

    @classmethod
    def _hints(cls) -> Dict[str, Any]:
        cached = SerializableRecord._TYPE_HINTS_CACHE.get(cls)
        if cached is None:
            try:
                cached = get_type_hints(cls)
            except Exception:
                cached = {}
            SerializableRecord._TYPE_HINTS_CACHE[cls] = cached
        return cached

    # -- envelope ---------------------------------------------------------

    @classmethod
    def object_type(cls) -> str:
        """Stable wire name for this record class."""
        return cls.__name__

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to the canonical versioned dict form."""
        if not is_dataclass(self):  # pragma: no cover - misuse guard
            raise QcaeSerializationError(
                f"{type(self).__name__} must be a dataclass to serialize"
            )
        payload: Dict[str, Any] = {
            "schema_version": self.SCHEMA_VERSION,
            "object_type": self.object_type(),
        }
        for field in fields(self):  # dataclass field order is deterministic
            payload[field.name] = _to_jsonable(getattr(self, field.name))
        return payload

    @classmethod
    def from_dict(cls: Type[T], data: Any) -> T:
        """Rebuild a record from its canonical dict form, failing closed."""
        if not isinstance(data, dict):
            raise QcaeSerializationError(
                f"{cls.object_type()} payload must be a JSON object"
            )
        for key in ("schema_version", "object_type"):
            if key not in data:
                raise QcaeSchemaVersionError(
                    f"{cls.object_type()} payload missing '{key}'"
                )
        if data["object_type"] != cls.object_type():
            raise QcaeUnknownTypeError(
                f"payload declares object_type={data['object_type']!r}, "
                f"reader expects {cls.object_type()!r}"
            )
        version = data["schema_version"]
        if not isinstance(version, int) or isinstance(version, bool):
            raise QcaeSchemaVersionError(
                f"{cls.object_type()} schema_version must be an integer"
            )
        if version != cls.SCHEMA_VERSION:
            raise QcaeSchemaVersionError(
                f"{cls.object_type()} schema_version {version} not supported by "
                f"reader (expects {cls.SCHEMA_VERSION})"
            )
        try:
            kwargs = {
                field.name: _from_jsonable(data[field.name])
                for field in fields(cls)
            }
        except KeyError as exc:
            raise QcaeSerializationError(
                f"{cls.object_type()} payload missing field {exc.args[0]!r}"
            ) from exc
        envelope_keys = {"schema_version", "object_type"}
        declared_keys = envelope_keys | {field.name for field in fields(cls)}
        unknown_keys = sorted(set(data) - declared_keys)
        if unknown_keys:
            raise QcaeSerializationError(
                f"{cls.object_type()} payload has fields unknown to schema "
                f"version {cls.SCHEMA_VERSION}: {unknown_keys}"
            )
        for field_name, coerce in cls._COERCIONS.items():
            if field_name in kwargs:
                kwargs[field_name] = coerce(kwargs[field_name])
        for field_name, nested_cls in cls._NESTED_RECORDS.items():
            value = kwargs.get(field_name)
            if isinstance(value, dict):
                kwargs[field_name] = nested_cls.from_dict(value)
            elif isinstance(value, (list, tuple)):
                kwargs[field_name] = tuple(
                    nested_cls.from_dict(item) if isinstance(item, dict) else item
                    for item in value
                )
        try:
            return cls(**kwargs)
        except TypeError as exc:
            raise QcaeSerializationError(
                f"{cls.object_type()} payload fields do not match reader: {exc}"
            ) from exc

    def digest(self) -> str:
        """Content digest over the canonical serialized payload."""
        return sha256_of(self.to_dict())

    # -- helpers ----------------------------------------------------------

    @classmethod
    def _serialized_fields(cls) -> Tuple[str, ...]:
        return tuple(field.name for field in fields(cls))


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, SerializableRecord):
        return value.to_dict()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _to_jsonable(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _to_jsonable(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise QcaeSerializationError(
        f"field value of type {type(value).__name__} is not serializable; "
        "domain records must contain only JSON-native data, nested records, "
        "lists, or string-keyed dicts"
    )


def _from_jsonable(value: Any) -> Any:
    # Nested records are rebuilt by concrete from_dict implementations that
    # know their nested classes; at this level nested dicts pass through and
    # concrete validators reject malformed shapes.
    return value


def coerce_enum(value: Any, enum_cls: Type[Enum]) -> Any:
    """Coerce a serialized string back to an enum member.

    Unknown strings pass through untouched so the record's own ``validate()``
    raises the domain-level error with full context.
    """
    if isinstance(value, enum_cls) or not isinstance(value, str):
        return value
    try:
        return enum_cls(value)
    except ValueError:
        return value


def coerce_enum_tuple(value: Any, enum_cls: Type[Enum]) -> Any:
    """Coerce a list/tuple of serialized strings back to a tuple of enum members."""
    if isinstance(value, (list, tuple)):
        return tuple(coerce_enum(item, enum_cls) for item in value)
    return value
