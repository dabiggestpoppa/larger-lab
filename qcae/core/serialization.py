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
from typing import Any, ClassVar, Dict, Tuple, Type, TypeVar

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
        for field_name, nested_cls in cls._NESTED_RECORDS.items():
            value = kwargs.get(field_name)
            if isinstance(value, dict):
                kwargs[field_name] = nested_cls.from_dict(value)
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
