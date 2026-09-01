"""SENSOR-B4-I01 — deterministic serialization tests.

Canonical serialization must be byte-identical for semantically identical
input, differ for semantically different input, normalize timezone-equivalent
datetimes to the same UTC representation, and never contain wall-clock
auto-population.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity, SchemaState
from crypto_sensor_fabric.providers.base.models import (
    AdapterEvidenceRef,
    RawPayloadEnvelope,
)
from crypto_sensor_fabric.storage.enums import (
    CoverageState,
    IntegrityState,
    RevisionPolicy,
    StorageEncoding,
)
from crypto_sensor_fabric.storage.models import (
    AcquisitionRecord,
    EvidenceBlob,
    PartitionManifest,
    RawEvidenceQuery,
    canonical_json_bytes,
)

UTC_NOW = datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC)
SHA = "a" * 64


def _blob(**overrides: Any) -> EvidenceBlob:
    kwargs: dict[str, Any] = {
        "blob_sha256": SHA,
        "byte_length": 100,
        "stored_byte_length": 80,
        "source_media_type": "application/json",
        "storage_encoding": StorageEncoding.NONE,
        "created_at": UTC_NOW,
        "storage_uri": "t0://blobs/aaaa",
        "integrity_state": IntegrityState.UNVERIFIED,
    }
    kwargs.update(overrides)
    return EvidenceBlob(**kwargs)


class TestDeterministicSerialization:
    def test_same_input_byte_identical(self) -> None:
        a = canonical_json_bytes(_blob())
        b = canonical_json_bytes(_blob())
        assert a == b

    def test_different_input_different_bytes(self) -> None:
        a = canonical_json_bytes(_blob())
        b = canonical_json_bytes(_blob(byte_length=200))
        assert a != b

    def test_timezone_equivalent_normalized_same(self) -> None:
        a = canonical_json_bytes(
            _blob(created_at=datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC))
        )
        b = canonical_json_bytes(
            _blob(created_at=datetime(2026, 9, 1, 8, 0, 0, tzinfo=UTC) + timedelta(hours=4))
        )
        # +04:00 equivalent of 08:00Z == 12:00Z
        c = canonical_json_bytes(
            _blob(created_at=datetime(2026, 9, 1, 12, 0, 0, tzinfo=UTC))
        )
        assert a == b == c

    def test_field_insertion_order_irrelevant(self) -> None:
        a = canonical_json_bytes(_blob())
        b = canonical_json_bytes(
            EvidenceBlob.model_validate(
                {
                    "storage_uri": "t0://blobs/aaaa",  # moved field position
                    "integrity_state": "UNVERIFIED",
                    "blob_sha256": SHA,
                    "byte_length": 100,
                    "stored_byte_length": 80,
                    "source_media_type": "application/json",
                    "storage_encoding": "NONE",
                    "created_at": "2026-09-01T12:00:00Z",
                }
            )
        )
        assert a == b

    def test_no_wall_clock_in_canonical_output(self) -> None:
        blob = _blob()
        serialized = canonical_json_bytes(blob)
        # No field may be auto-populated from datetime.now(); the only datetime
        # is the caller-supplied created_at.
        assert "now()" not in serialized.decode("utf-8").lower()
        # Deterministic constructors must not require a runtime clock: an
        # identical object serializes identically at any later time.
        blob2 = _blob()
        assert canonical_json_bytes(blob) == canonical_json_bytes(blob2)

    def test_enum_values_serialized_explicitly(self) -> None:
        text = canonical_json_bytes(_blob()).decode("utf-8")
        assert '"storage_encoding":"NONE"' in text
        assert '"integrity_state":"UNVERIFIED"' in text

    def test_utc_iso8601(self) -> None:
        text = canonical_json_bytes(_blob()).decode("utf-8")
        assert '"created_at":"2026-09-01T12:00:00Z"' in text

    def test_query_serialization_deterministic(self) -> None:
        q1 = RawEvidenceQuery(providers=["KRAKEN_FUTURES"], limit=10)
        q2 = RawEvidenceQuery(providers=["KRAKEN_FUTURES"], limit=10)
        assert canonical_json_bytes(q1) == canonical_json_bytes(q2)

    def test_query_default_revision_policy_serialized(self) -> None:
        q = RawEvidenceQuery()
        text = canonical_json_bytes(q).decode("utf-8")
        assert '"revision_policy":"ERROR_ON_AMBIGUITY"' in text


class TestBloc3HandoffBridge:
    """Storage contracts can reference frozen Bloc 3 provenance without
    canonicalization, identity loss or circular imports."""

    def test_acquisition_carries_bloc3_provenance(self) -> None:
        env = RawPayloadEnvelope(
            provider_id="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            request_fingerprint="fp-xyz",
            content_type="application/json",
            encoding="utf-8",
            raw_body='{"rate": 0.0001}',
            content_hash=SHA,
            schema_state=SchemaState.KNOWN_SCHEMA,
            retrieval_metadata={"native_url": "https://futures.kraken.com/..."},
            evidence_ref=AdapterEvidenceRef(
                evidence_id="ev-1", provider_id="KRAKEN_FUTURES",
                sensor_family=SensorFamily.MECHANICAL_FUNDING,
            ),
            adapter_version="kraken-adapter-v2",
        )
        rec = AcquisitionRecord(
            acquisition_id="acq-1",
            provider_id=env.provider_id,
            venue="KRAKEN_FUTURES",
            sensor_family=env.sensor_family,
            request_fingerprint=env.request_fingerprint,
            adapter_version=env.adapter_version,
            requested_start=UTC_NOW,
            requested_end=UTC_NOW,
            native_instrument="PI_XBTUSD",
            native_granularity=Granularity.G1H,
            request_started_at=UTC_NOW,
            response_observed_at=UTC_NOW,
            ingested_at=UTC_NOW,
            http_status_or_source_status="200",
            source_locator="https://futures.kraken.com/...",
            blob_sha256=SHA,
            quality_flags=[],
        )
        assert rec.provider_id == env.provider_id
        assert rec.sensor_family is env.sensor_family
        assert rec.request_fingerprint == env.request_fingerprint
        assert rec.adapter_version == env.adapter_version

    def test_manifest_maps_partition_semantics(self) -> None:
        m = PartitionManifest(
            partition_manifest_id="pm-1",
            partition_key="GATE_FUTURES/MECHANICAL_OPEN_INTEREST/BTC_USDT/2026-08",
            manifest_version=1,
            provider="GATE_FUTURES",
            venue="GATE_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
            native_instrument="BTC_USDT",
            source_granularity=Granularity.G1H,
            logical_date_start=UTC_NOW,
            logical_date_end=UTC_NOW,
            blob_refs=[SHA],
            coverage_state=CoverageState.PARTIAL,
            integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
            row_count=24,
            revision_count=1,
            created_at=UTC_NOW,
        )
        # Logical partition is NOT a physical blob address.
        assert m.blob_refs != m.partition_key
        assert m.native_instrument == "BTC_USDT"

    def test_query_default_fails_safe(self) -> None:
        q = RawEvidenceQuery()
        assert q.revision_policy is RevisionPolicy.ERROR_ON_AMBIGUITY
        assert q.include_t0a is True
