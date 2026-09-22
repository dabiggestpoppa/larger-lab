"""P0-C02 — serialization base + error taxonomy evidence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Mapping

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
from qcae.orchestration.orchestrator.budgets import Budget
from qcae.orchestration.workers.contracts import WorkerResult, WorkerStatus


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


# -- P3-R4-R2: deep freeze by declaration, not annotation specificity --------


class TestDeepFreezeCoversEveryDeclaredCollection:
    """P3-R4-R2 — the audit's annotation-gating hole, closed.

    ``get_origin(dict)`` is ``None``, so C5's origin-gated freeze silently
    skipped bare ``dict`` fields: a frozen record held the caller's own
    mapping, and a post-construction caller mutation reached into the record
    — empirically demonstrated on ``AuthorityRequest.context``, and it even
    moved the record's digest. Freezing now keys on the declaration (any
    ``dict``/``Mapping``/set spelling) and the value's nature, so every
    declared mutable collection is frozen whatever the annotation says.
    """

    def test_bare_dict_field_survives_caller_mutation(self) -> None:
        caller = {"tenant": "t1"}
        rec = _SampleRecord(record_id="r-6", tags=[], attrs=caller)
        digest = rec.digest()
        caller["tenant"] = "TAMPERED"
        assert rec.attrs == {"tenant": "t1"}
        assert rec.digest() == digest

    def test_typed_dict_field_stays_frozen(self) -> None:
        caller = {"attempts": 1}
        budget = Budget(
            budget_id="b-1", owner_kind="job", owner_id="job-1",
            allocation=caller,
        )
        caller["attempts"] = 99
        assert budget.allocation == {"attempts": 1}

    def test_freeze_is_deep(self) -> None:
        caller = {"scope": {"nested": [1, 2]}}
        rec = _SampleRecord(record_id="r-7", tags=[], attrs=caller)
        caller["scope"]["nested"].append(3)
        assert rec.attrs["scope"]["nested"] == (1, 2)

    def test_mapping_annotated_field_is_frozen(self) -> None:
        @dataclass(frozen=True)
        class _Scoped(SerializableRecord):
            SCHEMA_VERSION = 1

            record_id: str
            scopes: Mapping[str, int]

        caller = {"read": 1}
        rec = _Scoped(record_id="r-8", scopes=caller)
        caller["read"] = 99
        assert rec.scopes == {"read": 1}

    def test_mapping_declared_field_rejects_a_non_mapping(self) -> None:
        @dataclass(frozen=True)
        class _Scoped(SerializableRecord):
            SCHEMA_VERSION = 1

            record_id: str
            scopes: Mapping[str, int]

        with pytest.raises(QcaeSerializationError, match="declared as a mapping"):
            _Scoped(record_id="r-9", scopes=("read",))

    def test_set_declared_field_freezes_and_round_trips(self) -> None:
        @dataclass(frozen=True)
        class _Tagged(SerializableRecord):
            SCHEMA_VERSION = 1

            record_id: str
            labels: set

        caller = {"alpha", "beta"}
        rec = _Tagged(record_id="r-10", labels=caller)
        caller.add("GAMMA")
        assert rec.labels == frozenset({"alpha", "beta"})
        # JSON has no set form: the sorted array is the deterministic
        # encoding, and from_dict rebuilds the frozenset it declares.
        assert rec.to_dict()["labels"] == ["alpha", "beta"]
        rebuilt = _Tagged.from_dict(rec.to_dict())
        assert rebuilt.labels == frozenset({"alpha", "beta"})
        assert rebuilt == rec

    def test_worker_result_budget_used_holds_under_freezing(self) -> None:
        """The audit's flagged path, as a real record.

        ``WorkerResult.validate`` checks ``budget_used`` with a subclass
        ``getattr`` check outside the base-class loop; the probe showed a
        caller mutation previously reached the field and moved the digest.
        Freezing must hold while that validator keeps accepting the frozen
        shape and the round trip stays exact.
        """
        caller = {"attempts": 3}
        result = WorkerResult(
            step_id="step-1", job_id="job-1", status=WorkerStatus.SUCCESS,
            budget_used=caller,
        )
        digest = result.digest()
        caller["attempts"] = 99
        result.validate()
        assert dict(result.budget_used) == {"attempts": 3}
        assert result.digest() == digest
        rebuilt = WorkerResult.from_dict(result.to_dict())
        assert rebuilt == result
        assert dict(rebuilt.budget_used) == {"attempts": 3}
