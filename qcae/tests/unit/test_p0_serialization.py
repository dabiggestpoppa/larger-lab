"""P0-C02 — serialization base + error taxonomy evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import pytest

from qcae.core.errors import (
    QcaeError,
    QcaeSerializationError,
    QcaeSchemaVersionError,
    QcaeStateTransitionError,
    QcaeTransitionWaiverError,
    QcaeUnknownTypeError,
    QcaeValidationError,
)
from qcae.core.serialization import (
    SerializableRecord,
    canonical_json_bytes,
    sha256_of,
)


@dataclass(frozen=True)
class _SampleRecord(SerializableRecord):
    SCHEMA_VERSION = 1

    record_id: str
    tags: List[str]
    attrs: dict


class TestCanonicalEncoding:
    def test_deterministic_across_key_order(self) -> None:
        a = canonical_json_bytes({"b": 1, "a": [1, 2]})
        b = canonical_json_bytes({"a": [1, 2], "b": 1})
        assert a == b

    def test_stable_digest_of_equal_content(self) -> None:
        assert sha256_of({"x": 1, "y": ["p", "q"]}) == sha256_of({"y": ["p", "q"], "x": 1})

    def test_digest_changes_with_content(self) -> None:
        assert sha256_of({"x": 1}) != sha256_of({"x": 2})

    def test_non_json_native_value_rejected(self) -> None:
        with pytest.raises(QcaeSerializationError):
            canonical_json_bytes({"s": {1, 2}})

    def test_nan_rejected(self) -> None:
        with pytest.raises(QcaeSerializationError):
            canonical_json_bytes({"f": float("nan")})

    def test_encoding_is_utf8_json(self) -> None:
        raw = canonical_json_bytes({"k": "väl"})
        assert raw.decode("utf-8") == '{"k":"väl"}'


class TestRecordRoundTrip:
    def test_round_trip_preserves_equality(self) -> None:
        rec = _SampleRecord(record_id="r-1", tags=["a", "b"], attrs={"k": 1})
        rebuilt = _SampleRecord.from_dict(rec.to_dict())
        assert rebuilt == rec

    def test_digest_stable_across_instances(self) -> None:
        r1 = _SampleRecord(record_id="r-2", tags=["x"], attrs={"n": 2})
        r2 = _SampleRecord(record_id="r-2", tags=["x"], attrs={"n": 2})
        assert r1.digest() == r2.digest()
        assert r1.digest() != _SampleRecord(record_id="r-3", tags=["x"], attrs={"n": 2}).digest()

    def test_envelope_fields_present(self) -> None:
        rec = _SampleRecord(record_id="r-4", tags=[], attrs={})
        payload = rec.to_dict()
        assert payload["schema_version"] == 1
        assert payload["object_type"] == "_SampleRecord"
        assert payload["record_id"] == "r-4"

    def test_nested_record_serializes(self) -> None:
        @dataclass(frozen=True)
        class _Inner(SerializableRecord):
            SCHEMA_VERSION = 1

            value: int

        @dataclass(frozen=True)
        class _Outer(SerializableRecord):
            SCHEMA_VERSION = 1

            _NESTED_RECORDS = {"inner": _Inner}

            inner: _Inner

        outer = _Outer(inner=_Inner(value=7))
        rebuilt = _Outer.from_dict(outer.to_dict())
        assert isinstance(rebuilt.inner, _Inner)
        assert rebuilt.inner.value == 7


class TestFailClosedDeserialization:
    def make_payload(self, **overrides) -> dict:
        rec = _SampleRecord(record_id="r-5", tags=["t"], attrs={"a": 1})
        payload = rec.to_dict()
        payload.update(overrides)
        return payload

    def test_missing_schema_version_rejected(self) -> None:
        payload = self.make_payload()
        del payload["schema_version"]
        with pytest.raises(QcaeSchemaVersionError):
            _SampleRecord.from_dict(payload)

    def test_missing_object_type_rejected(self) -> None:
        payload = self.make_payload()
        del payload["object_type"]
        with pytest.raises(QcaeSchemaVersionError):
            _SampleRecord.from_dict(payload)

    def test_wrong_object_type_rejected(self) -> None:
        with pytest.raises(QcaeUnknownTypeError):
            _SampleRecord.from_dict(self.make_payload(object_type="SomethingElse"))

    def test_future_schema_version_rejected(self) -> None:
        with pytest.raises(QcaeSchemaVersionError):
            _SampleRecord.from_dict(self.make_payload(schema_version=2))

    def test_non_int_schema_version_rejected(self) -> None:
        with pytest.raises(QcaeSchemaVersionError):
            _SampleRecord.from_dict(self.make_payload(schema_version="1"))

    def test_bool_schema_version_rejected(self) -> None:
        with pytest.raises(QcaeSchemaVersionError):
            _SampleRecord.from_dict(self.make_payload(schema_version=True))

    def test_missing_field_rejected(self) -> None:
        payload = self.make_payload()
        del payload["tags"]
        with pytest.raises(QcaeSerializationError):
            _SampleRecord.from_dict(payload)

    def test_unknown_field_rejected(self) -> None:
        with pytest.raises(QcaeSerializationError):
            _SampleRecord.from_dict(self.make_payload(extra_field="surprise"))

    def test_non_dict_payload_rejected(self) -> None:
        with pytest.raises(QcaeSerializationError):
            _SampleRecord.from_dict(["not", "a", "dict"])

    def test_null_payload_rejected(self) -> None:
        with pytest.raises(QcaeSerializationError):
            _SampleRecord.from_dict(None)


class TestErrorTaxonomy:
    def test_all_errors_share_base(self) -> None:
        for exc in (
            QcaeValidationError,
            QcaeSchemaVersionError,
            QcaeSerializationError,
            QcaeStateTransitionError,
            QcaeTransitionWaiverError,
            QcaeUnknownTypeError,
        ):
            assert issubclass(exc, QcaeError)

    def test_validation_specializations(self) -> None:
        assert issubclass(QcaeStateTransitionError, QcaeValidationError)
        assert issubclass(QcaeTransitionWaiverError, QcaeStateTransitionError)
        assert issubclass(QcaeUnknownTypeError, QcaeSchemaVersionError)

    def test_errors_are_catchable_and_message_preserved(self) -> None:
        with pytest.raises(QcaeError, match="boom"):
            raise QcaeValidationError("boom")
