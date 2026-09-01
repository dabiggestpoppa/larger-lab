"""SENSOR-B4-I01 — storage model validation tests.

Fail-closed behavior: bad SHA format, negative counts, inverted windows,
naive datetimes, unknown extra fields, revision ambiguity defaults, and the
T0A/T0B + acquisition/blob identity separation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest
from pydantic import ValidationError

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity
from crypto_sensor_fabric.storage.enums import (
    BackupClass,
    CoverageState,
    DateBasis,
    DiskPressure,
    IntegrityState,
    ProjectionState,
    RevisionPolicy,
    RevisionState,
    StorageEncoding,
    StorageJobStatus,
    StorageObjectType,
    StoragePriority,
)
from crypto_sensor_fabric.storage.models import (
    AcquisitionRecord,
    BackupState,
    EvidenceBlob,
    ExportManifest,
    IntegrityCheck,
    PartitionManifest,
    ProjectionLineage,
    RawEvidenceQuery,
    RawEvidenceResult,
    RawNormalizationBatch,
    RawProjectionArtifact,
    RecoveryAction,
    SourceRevision,
    StorageJobState,
    StorageJobTransition,
    StorageQuotaState,
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


class TestEvidenceBlob:
    def test_valid(self) -> None:
        blob = _blob()
        assert blob.byte_length == 100
        assert blob.integrity_state is IntegrityState.UNVERIFIED

    def test_bad_sha_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _blob(blob_sha256="zz" + "a" * 62)

    def test_uppercase_sha_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _blob(blob_sha256="A" * 64)

    def test_negative_byte_length_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _blob(byte_length=-1)
        with pytest.raises(ValidationError):
            _blob(stored_byte_length=-5)

    def test_naive_datetime_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _blob(created_at=datetime(2026, 9, 1, 12, 0, 0))  # noqa: DTZ001 — naive input is the test subject

    def test_unknown_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _blob(mystery_field=123)

    def test_utc_normalized(self) -> None:
        # 14:00 +02:00 == 12:00Z — proves timezone conversion to UTC.
        blob = _blob(created_at=datetime(2026, 9, 1, 14, 0, 0, tzinfo=timezone(timedelta(hours=2))))
        assert blob.created_at == UTC_NOW


class TestAcquisitionRecord:
    def _record(self, **overrides: Any) -> AcquisitionRecord:
        kwargs: dict[str, Any] = {
            "acquisition_id": "acq-1",
            "provider_id": "KRAKEN_FUTURES",
            "venue": "KRAKEN_FUTURES",
            "sensor_family": SensorFamily.MECHANICAL_FUNDING,
            "request_fingerprint": "fp-abc",
            "adapter_version": "kraken-adapter-v2",
            "requested_start": UTC_NOW,
            "requested_end": UTC_NOW,
            "native_instrument": "PI_XBTUSD",
            "native_granularity": Granularity.G1H,
            "request_started_at": UTC_NOW,
            "response_observed_at": UTC_NOW,
            "ingested_at": UTC_NOW,
            "http_status_or_source_status": "200",
            "source_locator": "https://futures.kraken.com/api/charts/v1/analytics/PI_XBTUSD/funding",
            "blob_sha256": SHA,
            "provider_checksum": None,
            "resume_token_before": None,
            "resume_token_after": None,
            "quality_flags": [],
            "failure_ref": None,
        }
        kwargs.update(overrides)
        return AcquisitionRecord(**kwargs)

    def test_valid(self) -> None:
        rec = self._record()
        assert rec.native_instrument == "PI_XBTUSD"

    def test_requested_end_before_start_rejected(self) -> None:
        later = datetime(2026, 9, 2, 12, 0, 0, tzinfo=UTC)
        with pytest.raises(ValidationError):
            self._record(requested_start=later)

    def test_naive_datetime_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._record(requested_start=datetime(2026, 9, 1, 12, 0, 0))  # noqa: DTZ001 — naive input is the test subject

    def test_utc_normalization(self) -> None:
        # 14:00 +02:00 == 12:00Z — proves timezone conversion to UTC.
        rec = self._record(
            requested_start=datetime(2026, 9, 1, 14, 0, 0, tzinfo=timezone(timedelta(hours=2)))
        )
        assert rec.requested_start == UTC_NOW

    def test_bad_blob_sha_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._record(blob_sha256="not-a-hash")


class TestRawProjectionArtifact:
    def _projection(self, **overrides: Any) -> RawProjectionArtifact:
        kwargs: dict[str, Any] = {
            "projection_id": "proj-1",
            "source_blob_sha256": [SHA],
            "projection_schema_id": "deribit-trade-v1",
            "projection_schema_version": "1.0.0",
            "parser_version": "deribit-adapter-v1",
            "row_count": 10,
            "min_provider_time": UTC_NOW,
            "max_provider_time": UTC_NOW,
            "partition_key": "DERIBIT/MECHANICAL_TRADE/BTC-PERPETUAL/2026-08",
            "projection_uri": "t0://projections/proj-1.parquet",
            "projection_sha256": SHA,
            "quality_flags": [],
            "state": ProjectionState.VALID,
        }
        kwargs.update(overrides)
        return RawProjectionArtifact(**kwargs)

    def test_valid(self) -> None:
        p = self._projection()
        assert p.row_count == 10

    def test_negative_rows_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._projection(row_count=-1)

    def test_bad_projection_sha_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._projection(projection_sha256="x" * 63)


class TestPartitionManifest:
    def _manifest(self, **overrides: Any) -> PartitionManifest:
        kwargs: dict[str, Any] = {
            "partition_manifest_id": "pm-1",
            "partition_key": "GATE_FUTURES/MECHANICAL_OPEN_INTEREST/BTC_USDT/2026-08",
            "manifest_version": 1,
            "provider": "GATE_FUTURES",
            "venue": "GATE_FUTURES",
            "sensor_family": SensorFamily.MECHANICAL_OPEN_INTEREST,
            "native_instrument": "BTC_USDT",
            "source_granularity": Granularity.G1H,
            "logical_date_start": UTC_NOW,
            "logical_date_end": UTC_NOW,
            "blob_refs": [SHA],
            "projection_refs": [],
            "coverage_state": CoverageState.PARTIAL,
            "integrity_state": IntegrityState.LOCAL_HASH_VERIFIED,
            "row_count": 24,
            "min_time": UTC_NOW,
            "max_time": UTC_NOW,
            "gap_count": 0,
            "revision_count": 1,
            "created_at": UTC_NOW,
            "supersedes_manifest_id": None,
        }
        kwargs.update(overrides)
        return PartitionManifest(**kwargs)

    def test_valid(self) -> None:
        m = self._manifest()
        assert m.manifest_version == 1

    def test_invalid_date_order_rejected(self) -> None:
        later = datetime(2026, 9, 2, 12, 0, 0, tzinfo=UTC)
        with pytest.raises(ValidationError):
            self._manifest(logical_date_start=later)

    def test_manifest_version_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._manifest(manifest_version=0)

    def test_negative_row_count_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._manifest(row_count=-1)

    def test_negative_gap_count_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._manifest(gap_count=-3)


class TestStorageJobModels:
    def test_job_state_valid(self) -> None:
        job = StorageJobState(
            job_id="job-1",
            provider_id="OKX_SWAP",
            sensor_family=SensorFamily.MECHANICAL_TRADE,
            request_fingerprint="fp-1",
            status=StorageJobStatus.PLANNED,
            updated_at=UTC_NOW,
        )
        assert job.status is StorageJobStatus.PLANNED

    def test_job_transition_noop_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StorageJobTransition(
                transition_id="t-1",
                job_id="job-1",
                from_status=StorageJobStatus.PLANNED,
                to_status=StorageJobStatus.PLANNED,
                transitioned_at=UTC_NOW,
            )

    def test_job_transition_valid(self) -> None:
        tr = StorageJobTransition(
            transition_id="t-1",
            job_id="job-1",
            from_status=StorageJobStatus.PLANNED,
            to_status=StorageJobStatus.ACQUIRING,
            transitioned_at=UTC_NOW,
        )
        assert tr.to_status is StorageJobStatus.ACQUIRING


class TestSourceRevision:
    def test_valid(self) -> None:
        rev = SourceRevision(
            source_revision_key="KRAKEN_FUTURES/MECHANICAL_FUNDING/PI_XBTUSD",
            revision_number=1,
            blob_sha256=SHA,
            first_seen_at=UTC_NOW,
            last_seen_at=UTC_NOW,
            revision_reason="first acquisition",
            revision_state=RevisionState.STABLE,
        )
        assert rev.revision_number == 1

    def test_revision_number_zero_rejected(self) -> None:
        with pytest.raises(ValidationError):
            SourceRevision(
                source_revision_key="k",
                revision_number=0,
                blob_sha256=SHA,
                first_seen_at=UTC_NOW,
                last_seen_at=UTC_NOW,
                revision_state=RevisionState.STABLE,
            )

    def test_last_seen_before_first_rejected(self) -> None:
        later = datetime(2026, 9, 2, 12, 0, 0, tzinfo=UTC)
        with pytest.raises(ValidationError):
            SourceRevision(
                source_revision_key="k",
                revision_number=1,
                blob_sha256=SHA,
                first_seen_at=later,
                last_seen_at=UTC_NOW,
                revision_state=RevisionState.STABLE,
            )

    def test_distinct_bytes_distinct_revisions_representable(self) -> None:
        rev1 = SourceRevision(
            source_revision_key="k",
            revision_number=1,
            blob_sha256=SHA,
            first_seen_at=UTC_NOW,
            last_seen_at=UTC_NOW,
            revision_state=RevisionState.STABLE,
        )
        rev2 = SourceRevision(
            source_revision_key="k",
            revision_number=2,
            blob_sha256="b" * 64,
            first_seen_at=UTC_NOW,
            last_seen_at=UTC_NOW,
            revision_state=RevisionState.SOURCE_MUTATION,
        )
        assert rev1.blob_sha256 != rev2.blob_sha256
        assert rev1.revision_number != rev2.revision_number


class TestRawEvidenceQuery:
    def _query(self, **overrides: Any) -> RawEvidenceQuery:
        kwargs: dict[str, Any] = {
            "providers": ["KRAKEN_FUTURES"],
            "sensor_families": [SensorFamily.MECHANICAL_FUNDING],
            "limit": 100,
        }
        kwargs.update(overrides)
        return RawEvidenceQuery(**kwargs)

    def test_default_revision_policy_is_error_on_ambiguity(self) -> None:
        q = self._query()
        assert q.revision_policy is RevisionPolicy.ERROR_ON_AMBIGUITY

    def test_negative_limit_rejected(self) -> None:
        with pytest.raises(ValidationError):
            self._query(limit=-1)

    def test_inverted_logical_window_rejected(self) -> None:
        later = datetime(2026, 9, 2, 12, 0, 0, tzinfo=UTC)
        with pytest.raises(ValidationError):
            self._query(logical_start=later, logical_end=UTC_NOW)

    def test_utc_normalized(self) -> None:
        # 14:00 +02:00 == 12:00Z — proves timezone conversion to UTC.
        q = self._query(logical_start=datetime(2026, 9, 1, 14, 0, 0, tzinfo=timezone(timedelta(hours=2))))
        assert q.logical_start == UTC_NOW


class TestRawEvidenceResult:
    def test_valid(self) -> None:
        r = RawEvidenceResult(
            provider="GATE_FUTURES",
            venue="GATE_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
            native_instrument="BTC_USDT",
            source_granularity=Granularity.G1H,
            logical_time_start=UTC_NOW,
            logical_time_end=UTC_NOW,
            coverage_state=CoverageState.PARTIAL,
            integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
            acquisition_ids=["acq-1"],
            blob_refs=[SHA],
            projection_refs=[],
            revision_state=RevisionState.UNKNOWN_REVISION,
            quality_flags=[],
            lineage_refs=[],
        )
        assert r.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED


class TestRawNormalizationBatch:
    def test_valid(self) -> None:
        b = RawNormalizationBatch(
            batch_id="batch-1",
            provider="DERIBIT",
            venue="DERIBIT",
            sensor_family=SensorFamily.MECHANICAL_TRADE,
            native_instrument="BTC-PERPETUAL",
            projection_schema_id="deribit-trade-v1",
            projection_schema_version="1.0.0",
            parser_version="deribit-adapter-v1",
            raw_rows_or_reader="reader://projections/proj-1.parquet",
            source_blob_refs=[SHA],
            acquisition_refs=["acq-1"],
            logical_time_range_start=UTC_NOW,
            logical_time_range_end=UTC_NOW,
            integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
            coverage_state=CoverageState.PARTIAL,
            revision_state=RevisionState.UNKNOWN_REVISION,
            quality_flags=[],
            known_gap_intervals=[],
            source_granularity=Granularity.G5M,
            history_boundary="LIMITED",
        )
        assert b.parser_version == "deribit-adapter-v1"

    def test_no_canonical_fields(self) -> None:
        for field in (
            "canonical_asset_id",
            "canonical_notional",
            "effective_at",
            "normalized_funding",
            "normalized_OI",
        ):
            assert field not in RawNormalizationBatch.model_fields


class TestStorageQuotaState:
    def test_valid(self) -> None:
        q = StorageQuotaState(
            pressure_state=DiskPressure.NORMAL,
            priority_class=StoragePriority.P0,
            used_bytes=50,
            capacity_bytes=100,
            free_bytes=50,
            utilization_ratio=0.5,
            absolute_free_floor_bytes=10,
            observed_at=UTC_NOW,
        )
        assert q.utilization_ratio == 0.5

    def test_negative_bytes_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StorageQuotaState(
                pressure_state=DiskPressure.NORMAL,
                used_bytes=-1,
                capacity_bytes=100,
                free_bytes=50,
                utilization_ratio=0.5,
                observed_at=UTC_NOW,
            )

    def test_ratio_out_of_bounds_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StorageQuotaState(
                pressure_state=DiskPressure.NORMAL,
                used_bytes=50,
                capacity_bytes=100,
                free_bytes=50,
                utilization_ratio=1.5,
                observed_at=UTC_NOW,
            )


class TestBackupState:
    def test_valid(self) -> None:
        b = BackupState(
            state=BackupClass.MANIFEST_BACKED,
            observed_at=UTC_NOW,
            verified_object_count=10,
            verified_bytes=1000,
            manifest_ref="manifest-1",
        )
        assert b.state is BackupClass.MANIFEST_BACKED

    def test_negative_counts_rejected(self) -> None:
        with pytest.raises(ValidationError):
            BackupState(
                state=BackupClass.UNBACKED,
                observed_at=UTC_NOW,
                verified_object_count=-1,
                verified_bytes=0,
            )

    def test_default_is_unbacked(self) -> None:
        b = BackupState(state=BackupClass.UNBACKED, observed_at=UTC_NOW)
        assert b.state is BackupClass.UNBACKED


class TestIntegrityCheck:
    def test_valid(self) -> None:
        c = IntegrityCheck(
            check_id="chk-1",
            object_type=StorageObjectType.EVIDENCE_BLOB,
            object_id="blob-1",
            integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
            checked_at=UTC_NOW,
            expected_hash=SHA,
            observed_hash=SHA,
        )
        assert c.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED

    def test_bad_expected_hash_rejected(self) -> None:
        with pytest.raises(ValidationError):
            IntegrityCheck(
                check_id="chk-1",
                object_type=StorageObjectType.EVIDENCE_BLOB,
                object_id="blob-1",
                integrity_state=IntegrityState.UNVERIFIED,
                checked_at=UTC_NOW,
                expected_hash="bad",
            )


class TestRecoveryAction:
    def test_valid(self) -> None:
        from crypto_sensor_fabric.storage.enums import StorageObjectType

        r = RecoveryAction(
            recovery_run_id="run-1",
            object_type=StorageObjectType.PARTITION_MANIFEST,
            object_id="pm-1",
            problem="manifest references missing blob",
            resolution="recorded for operator review",
            before_state="PARTIAL",
            after_state="QUARANTINED",
        )
        assert r.object_type is StorageObjectType.PARTITION_MANIFEST


class TestExportManifest:
    def test_valid(self) -> None:
        e = ExportManifest(
            export_id="exp-1",
            created_at=UTC_NOW,
            source_data_root="t0://",
            selection_query=RawEvidenceQuery(providers=["KRAKEN_FUTURES"]),
            blob_count=2,
            projection_count=1,
            total_bytes=500,
            manifest_sha256=SHA,
            objects=["blob-1", "proj-1"],
            verification_state=IntegrityState.UNVERIFIED,
        )
        assert e.blob_count == 2

    def test_negative_counts_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ExportManifest(
                export_id="exp-1",
                created_at=UTC_NOW,
                source_data_root="t0://",
                selection_query=RawEvidenceQuery(),
                blob_count=-1,
                projection_count=0,
                total_bytes=0,
                manifest_sha256=SHA,
                objects=[],
                verification_state=IntegrityState.UNVERIFIED,
            )


class TestProjectionLineage:
    def test_valid(self) -> None:
        lr = ProjectionLineage(
            lineage_manifest_id="lm-1",
            projection_id="proj-1",
            source_blob_sha256=SHA,
            source_acquisition_id="acq-1",
            source_row_start=0,
            source_row_end=99,
            source_order=1,
        )
        assert lr.source_row_end == 99

    def test_inverted_row_bounds_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProjectionLineage(
                lineage_manifest_id="lm-1",
                projection_id="proj-1",
                source_blob_sha256=SHA,
                source_acquisition_id="acq-1",
                source_row_start=50,
                source_row_end=10,
                source_order=1,
            )

    def test_multiple_lineage_records_supported(self) -> None:
        records = [
            ProjectionLineage(
                lineage_manifest_id="lm-1",
                projection_id="proj-1",
                source_blob_sha256=SHA,
                source_acquisition_id=f"acq-{i}",
                source_order=i,
            )
            for i in range(3)
        ]
        assert len(records) == 3


class TestI01R1SemverContract:
    """I01R1 defect A — projection_schema_version is a semantic version."""

    def test_semver_100_accepted(self) -> None:
        p = RawProjectionArtifact(
            projection_id="proj-1",
            source_blob_sha256=[SHA],
            projection_schema_id="deribit-trade-v1",
            projection_schema_version="1.0.0",
            parser_version="deribit-adapter-v1",
            row_count=1,
            partition_key="k",
            projection_uri="t0://projections/p.parquet",
            projection_sha256=SHA,
        )
        assert p.projection_schema_version == "1.0.0"

    def test_semver_234_accepted(self) -> None:
        p = RawProjectionArtifact(
            projection_id="proj-1",
            source_blob_sha256=[SHA],
            projection_schema_id="s",
            projection_schema_version="2.3.4",
            parser_version="p",
            partition_key="k",
            projection_uri="u",
            projection_sha256=SHA,
        )
        assert p.projection_schema_version == "2.3.4"

    @pytest.mark.parametrize(
        "bad", [1, "1", "v1", "1.0", "1.0.0-beta", "01.0.0", "1.0.-1", " 1.0.0", "1.0.0 "]
    )
    def test_invalid_semver_rejected(self, bad: object) -> None:
        with pytest.raises(ValidationError):
            RawProjectionArtifact(
                projection_id="proj-1",
                source_blob_sha256=[SHA],
                projection_schema_id="s",
                projection_schema_version=bad,  # type: ignore[arg-type]
                parser_version="p",
                partition_key="k",
                projection_uri="u",
                projection_sha256=SHA,
            )

    def test_batch_semver_contract(self) -> None:
        b = RawNormalizationBatch(
            batch_id="b",
            provider="DERIBIT",
            venue="DERIBIT",
            sensor_family=SensorFamily.MECHANICAL_TRADE,
            native_instrument="BTC-PERPETUAL",
            projection_schema_id="s",
            projection_schema_version="2.0.0",
            parser_version="p",
            raw_rows_or_reader="r",
            source_blob_refs=[SHA],
            acquisition_refs=["acq-1"],
            logical_time_range_start=UTC_NOW,
            logical_time_range_end=UTC_NOW,
        )
        assert b.projection_schema_version == "2.0.0"

    def test_schema_version_distinct_from_parser_version(self) -> None:
        p = RawProjectionArtifact(
            projection_id="proj-1",
            source_blob_sha256=[SHA],
            projection_schema_id="s",
            projection_schema_version="1.2.0",
            parser_version="deribit-adapter-v1",
            partition_key="k",
            projection_uri="u",
            projection_sha256=SHA,
        )
        assert p.projection_schema_version != p.parser_version


class TestI01R1SourceLineage:
    """I01R1 defect B — T0B must carry T0A lineage."""

    def test_projection_zero_source_blobs_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RawProjectionArtifact(
                projection_id="proj-1",
                source_blob_sha256=[],
                projection_schema_id="s",
                projection_schema_version="1.0.0",
                parser_version="p",
                partition_key="k",
                projection_uri="u",
                projection_sha256=SHA,
            )

    def test_projection_malformed_source_hash_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RawProjectionArtifact(
                projection_id="proj-1",
                source_blob_sha256=["zz" + "a" * 62],
                projection_schema_id="s",
                projection_schema_version="1.0.0",
                parser_version="p",
                partition_key="k",
                projection_uri="u",
                projection_sha256=SHA,
            )

    def test_projection_duplicate_source_hash_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RawProjectionArtifact(
                projection_id="proj-1",
                source_blob_sha256=[SHA, SHA],
                projection_schema_id="s",
                projection_schema_version="1.0.0",
                parser_version="p",
                partition_key="k",
                projection_uri="u",
                projection_sha256=SHA,
            )

    def test_batch_zero_source_blobs_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RawNormalizationBatch(
                batch_id="b",
                provider="DERIBIT",
                venue="DERIBIT",
                sensor_family=SensorFamily.MECHANICAL_TRADE,
                native_instrument="BTC-PERPETUAL",
                projection_schema_id="s",
                projection_schema_version="1.0.0",
                parser_version="p",
                raw_rows_or_reader="r",
                source_blob_refs=[],
                acquisition_refs=["acq-1"],
                logical_time_range_start=UTC_NOW,
                logical_time_range_end=UTC_NOW,
            )

    def test_batch_zero_acquisition_refs_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RawNormalizationBatch(
                batch_id="b",
                provider="DERIBIT",
                venue="DERIBIT",
                sensor_family=SensorFamily.MECHANICAL_TRADE,
                native_instrument="BTC-PERPETUAL",
                projection_schema_id="s",
                projection_schema_version="1.0.0",
                parser_version="p",
                raw_rows_or_reader="r",
                source_blob_refs=[SHA],
                acquisition_refs=[],
                logical_time_range_start=UTC_NOW,
                logical_time_range_end=UTC_NOW,
            )

    def test_batch_malformed_source_hash_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RawNormalizationBatch(
                batch_id="b",
                provider="DERIBIT",
                venue="DERIBIT",
                sensor_family=SensorFamily.MECHANICAL_TRADE,
                native_instrument="BTC-PERPETUAL",
                projection_schema_id="s",
                projection_schema_version="1.0.0",
                parser_version="p",
                raw_rows_or_reader="r",
                source_blob_refs=["nope"],
                acquisition_refs=["acq-1"],
                logical_time_range_start=UTC_NOW,
                logical_time_range_end=UTC_NOW,
            )


class TestI01R1HashRefSurfaces:
    """I01R1 defect D — every T0A hash ref fails closed on syntax + duplicates."""

    def test_manifest_malformed_blob_ref_rejected(self) -> None:
        m = _make_manifest()
        with pytest.raises(ValidationError):
            PartitionManifest(**{**m.model_dump(), "blob_refs": ["bad"]})

    def test_manifest_duplicate_blob_ref_rejected(self) -> None:
        m = _make_manifest()
        with pytest.raises(ValidationError):
            PartitionManifest(**{**m.model_dump(), "blob_refs": [SHA, SHA]})

    def test_result_malformed_blob_ref_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RawEvidenceResult(
                provider="GATE_FUTURES",
                venue="GATE_FUTURES",
                sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
                native_instrument="BTC_USDT",
                source_granularity=Granularity.G1H,
                logical_time_start=UTC_NOW,
                logical_time_end=UTC_NOW,
                coverage_state=CoverageState.PARTIAL,
                integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
                acquisition_ids=["acq-1"],
                blob_refs=["bad"],
            )

    def test_result_duplicate_blob_ref_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RawEvidenceResult(
                provider="GATE_FUTURES",
                venue="GATE_FUTURES",
                sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
                native_instrument="BTC_USDT",
                source_granularity=Granularity.G1H,
                logical_time_start=UTC_NOW,
                logical_time_end=UTC_NOW,
                coverage_state=CoverageState.PARTIAL,
                integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
                acquisition_ids=["acq-1"],
                blob_refs=[SHA, SHA],
            )

    def test_lineage_malformed_source_hash_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ProjectionLineage(
                lineage_manifest_id="lm-1",
                projection_id="proj-1",
                source_blob_sha256="bad",
                source_acquisition_id="acq-1",
                source_order=1,
            )

    def test_job_state_malformed_blob_hash_rejected(self) -> None:
        with pytest.raises(ValidationError):
            StorageJobState(
                job_id="job-1",
                provider_id="OKX_SWAP",
                sensor_family=SensorFamily.MECHANICAL_TRADE,
                request_fingerprint="fp-1",
                last_committed_blob_sha256="bad",
                status=StorageJobStatus.PLANNED,
                updated_at=UTC_NOW,
            )


class TestI01R1DateBasis:
    """I01R1 defect C — date_basis defaults to UNKNOWN, never inferred."""

    def test_default_is_unknown(self) -> None:
        m = _make_manifest()
        assert m.date_basis is DateBasis.UNKNOWN

    def test_explicit_event_time_preserved(self) -> None:
        m = _make_manifest(date_basis=DateBasis.EVENT_TIME)
        assert m.date_basis is DateBasis.EVENT_TIME

    def test_explicit_provider_file_date_preserved(self) -> None:
        m = _make_manifest(date_basis=DateBasis.PROVIDER_FILE_DATE)
        assert m.date_basis is DateBasis.PROVIDER_FILE_DATE

    def test_explicit_snapshot_time_preserved(self) -> None:
        m = _make_manifest(date_basis=DateBasis.SNAPSHOT_TIME)
        assert m.date_basis is DateBasis.SNAPSHOT_TIME


class TestI01R1TimestampOrder:
    """I01R1 defect E — paired min/max timestamps fail on inverted order."""

    def test_projection_min_gt_max_rejected(self) -> None:
        later = datetime(2026, 9, 2, 12, 0, 0, tzinfo=UTC)
        with pytest.raises(ValidationError):
            RawProjectionArtifact(
                projection_id="proj-1",
                source_blob_sha256=[SHA],
                projection_schema_id="s",
                projection_schema_version="1.0.0",
                parser_version="p",
                partition_key="k",
                projection_uri="u",
                projection_sha256=SHA,
                min_provider_time=later,
                max_provider_time=UTC_NOW,
            )

    def test_projection_one_sided_bounds_allowed(self) -> None:
        p = RawProjectionArtifact(
            projection_id="proj-1",
            source_blob_sha256=[SHA],
            projection_schema_id="s",
            projection_schema_version="1.0.0",
            parser_version="p",
            partition_key="k",
            projection_uri="u",
            projection_sha256=SHA,
            min_provider_time=UTC_NOW,
        )
        assert p.min_provider_time == UTC_NOW
        assert p.max_provider_time is None

    def test_manifest_min_gt_max_rejected(self) -> None:
        later = datetime(2026, 9, 2, 12, 0, 0, tzinfo=UTC)
        with pytest.raises(ValidationError):
            _make_manifest(min_time=later, max_time=UTC_NOW)

    def test_manifest_one_sided_bounds_allowed(self) -> None:
        m = _make_manifest(min_time=UTC_NOW, max_time=None)
        assert m.min_time == UTC_NOW
        assert m.max_time is None


def _make_manifest(**overrides: Any) -> PartitionManifest:
    kwargs: dict[str, Any] = {
        "partition_manifest_id": "pm-1",
        "partition_key": "GATE_FUTURES/MECHANICAL_OPEN_INTEREST/BTC_USDT/2026-08",
        "manifest_version": 1,
        "provider": "GATE_FUTURES",
        "venue": "GATE_FUTURES",
        "sensor_family": SensorFamily.MECHANICAL_OPEN_INTEREST,
        "native_instrument": "BTC_USDT",
        "source_granularity": Granularity.G1H,
        "logical_date_start": UTC_NOW,
        "logical_date_end": UTC_NOW,
        "blob_refs": [SHA],
        "projection_refs": [],
        "coverage_state": CoverageState.PARTIAL,
        "integrity_state": IntegrityState.LOCAL_HASH_VERIFIED,
        "row_count": 24,
        "min_time": UTC_NOW,
        "max_time": UTC_NOW,
        "gap_count": 0,
        "revision_count": 1,
        "created_at": UTC_NOW,
        "supersedes_manifest_id": None,
    }
    kwargs.update(overrides)
    return PartitionManifest(**kwargs)
