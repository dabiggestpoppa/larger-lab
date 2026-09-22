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
from types import MappingProxyType
from typing import (
    Any,
    ClassVar,
    Dict,
    Mapping,
    Tuple,
    Type,
    TypeVar,
    get_origin,
    get_type_hints,
)

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


def _deep_freeze(value: Any) -> Any:
    """Deeply freeze a JSON-native structure (P3-R4C5 deep immutability).

    Dicts become ``MappingProxyType`` copies whose values are themselves
    frozen, lists become tuples, and scalars pass through. Mutating a caller's
    original mapping after construction can no longer mutate the record.
    """
    if isinstance(value, dict):
        return MappingProxyType(
            {key: _deep_freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_deep_freeze(item) for item in value)
    return value


def _freeze_set(value: Any) -> Any:
    """Freeze a set-shaped value deterministically.

    A ``frozenset`` is already immutable, so it passes through; a mutable set
    is copied to one. Ordering is value-determined (hash order), so a digest
    over the frozenset content is independent of the caller's construction
    order.
    """
    if isinstance(value, frozenset):
        return value
    return frozenset(value)


def _declares_mapping(hint: Any) -> bool:
    """Whether a field annotation declares a mapping in any form.

    Every ``dict``/``Mapping`` spelling counts — typed, bare, or protocol —
    because ``get_origin(dict)`` is ``None``: an origin-only test is exactly
    the hole that left bare-``dict`` fields holding the caller's mapping.
    """
    origin = get_origin(hint)
    return (
        origin is dict
        or (isinstance(origin, type) and issubclass(origin, Mapping))
        or (isinstance(hint, type) and issubclass(hint, Mapping))
    )


def _declares_set(hint: Any) -> bool:
    """Whether a field annotation declares a set in any form."""
    origin = get_origin(hint)
    return origin is set or (
        isinstance(hint, type) and issubclass(hint, (set, frozenset))
    )


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
        """Canonicalize declared sequence types and deeply freeze collections.

        JSON flattens tuples to arrays and callers may pass either form; a
        tuple-declared field therefore always holds a tuple in memory, and a
        list-declared field always a list. Every declared field holding a
        mutable collection is defensively frozen by the value's nature, not
        the annotation's specificity (P3-R4-R2): ``get_origin(dict)`` is
        ``None``, so an annotation-gated rule silently skipped bare ``dict``
        fields and left the caller's own mapping inside a frozen record — a
        post-construction caller mutation reached the record and even moved
        its digest. Mappings are copied into a frozen proxy whose values are
        themselves deeply frozen; sets become ``frozenset``. Digests and
        equality stay deterministic regardless of how the record was built.
        """
        cls = type(self)
        hints = cls._hints()
        if not hints:
            return
        for fld in fields(cls):
            hint = hints.get(fld.name)
            origin = get_origin(hint)
            value = getattr(self, fld.name)
            if origin is tuple and isinstance(value, list):
                object.__setattr__(self, fld.name, tuple(value))
            elif origin is list and isinstance(value, tuple):
                object.__setattr__(self, fld.name, list(value))
            else:
                # P3-R4-R2: mapping- and set-declared fields are frozen by
                # their declaration (any ``dict``/``Mapping``/set form, typed
                # or bare) and by the value's nature, so a mapping a caller
                # mutated into the constructor is copied, whatever the
                # annotation said.
                if _declares_mapping(hint):
                    if isinstance(value, dict):
                        object.__setattr__(self, fld.name, _deep_freeze(value))
                    elif not isinstance(value, Mapping):
                        raise QcaeSerializationError(
                            f"field {fld.name!r} is declared as a mapping but holds "
                            f"{type(value).__name__}; domain records carry real mappings"
                        )
                elif _declares_set(hint):
                    if isinstance(value, (set, frozenset)):
                        object.__setattr__(self, fld.name, _freeze_set(value))
                    else:
                        raise QcaeSerializationError(
                            f"field {fld.name!r} is declared as a set but holds "
                            f"{type(value).__name__}; domain records carry real sets"
                        )

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
        # P3-R4-R2: a serialized set returns as a sorted array (JSON has no
        # set form); rebuild the frozenset the declared field carries so the
        # round trip preserves exact meaning. Mappings arrive as JSON objects
        # and are frozen again by __post_init__.
        for field_ in fields(cls):
            if _declares_set(cls._hints().get(field_.name)):
                value = kwargs.get(field_.name)
                if isinstance(value, list):
                    kwargs[field_.name] = frozenset(value)
        for field_name, nested_cls in cls._NESTED_RECORDS.items():
            if isinstance(nested_cls, str):
                # Forward reference by class name; resolve in the declaring
                # module's namespace (mirrors dataclass forward refs).
                import sys

                module = sys.modules[cls.__module__]
                nested_cls = getattr(module, nested_cls)
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
    if isinstance(value, frozenset):
        # JSON has no set form; the sorted array is the deterministic lossless
        # encoding for the homogeneous scalar sets domain records carry.
        return sorted(_to_jsonable(item) for item in value)
    if isinstance(value, (dict, MappingProxyType)):
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


def coerce_int_enum(value: Any, enum_cls: Type[Enum]) -> Any:
    """Coerce a serialized value back to an ``IntEnum`` member.

    The single owner of this rule: an ``IntEnum`` serializes to its *integer*
    value, so the string-only :func:`coerce_enum` cannot restore it. The name
    form is accepted as well. Unknown values pass through untouched so the
    record's own ``validate()`` raises the domain-level error with context.
    """
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        try:
            return enum_cls(value)
        except ValueError:
            return value
    if isinstance(value, str):
        try:
            return enum_cls[value]
        except KeyError:
            return value
    return value
