"""SENSOR-B4-I01 — frozen enum vocabulary tests.

Proves the exact frozen member sets from the Bloc 4 freeze manifest §5–§6 and
companion docs.  A missing/added/renamed member fails closed.
"""

from __future__ import annotations

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


class TestIntegrityState:
    def test_exact_frozen_values(self) -> None:
        assert {e.value for e in IntegrityState} == {
            "UNVERIFIED",
            "LOCAL_HASH_VERIFIED",
            "PROVIDER_HASH_VERIFIED",
            "QUARANTINED_INTEGRITY_FAILURE",
            "MISSING_BLOB",
            "PROJECTION_INVALID",
        }

    def test_no_generic_good_bad_ok(self) -> None:
        values = {e.value for e in IntegrityState}
        assert "GOOD" not in values and "BAD" not in values and "OK" not in values


class TestCoverageState:
    def test_exact_frozen_values(self) -> None:
        assert {e.value for e in CoverageState} == {
            "COMPLETE_SOURCE_BOUNDARY",
            "PARTIAL",
            "KNOWN_GAP",
            "EMPTY_CONFIRMED",
            "NOT_ATTEMPTED",
            "FAILED",
            "ACCESS_BLOCKED",
            "HISTORY_UNAVAILABLE",
            "QUARANTINED",
            "REVISION_CONFLICT",
        }


class TestRevisionPolicy:
    def test_exact_frozen_values(self) -> None:
        assert {e.value for e in RevisionPolicy} == {
            "ERROR_ON_AMBIGUITY",
            "ALL",
            "FIRST_SEEN",
            "LATEST_SEEN",
            "EXACT_REVISION",
            "PROVIDER_DECLARED_CANONICAL",
        }

    def test_obsolete_acquired_vocabulary_absent(self) -> None:
        values = {e.value for e in RevisionPolicy}
        assert "FIRST_ACQUIRED" not in values
        assert "LATEST_ACQUIRED" not in values

    def test_error_on_ambiguity_available(self) -> None:
        assert RevisionPolicy.ERROR_ON_AMBIGUITY is not None


class TestProjectionState:
    def test_exact_frozen_values(self) -> None:
        assert {e.value for e in ProjectionState} == {
            "VALID",
            "SUPERSEDED",
            "INVALID_PARSER",
            "INVALID_SOURCE",
            "INVALID_LINEAGE",
        }


class TestRevisionState:
    def test_exact_frozen_values(self) -> None:
        assert {e.value for e in RevisionState} == {
            "STABLE",
            "IDENTICAL_REFETCH",
            "SOURCE_MUTATION",
            "PROVIDER_DECLARED_REVISION",
            "UNKNOWN_REVISION",
        }


class TestStorageEncoding:
    def test_exact_frozen_values(self) -> None:
        assert {e.value for e in StorageEncoding} == {"NONE", "ZSTD"}


class TestDateBasis:
    def test_exact_frozen_values(self) -> None:
        assert {e.value for e in DateBasis} == {
            "EVENT_TIME",
            "PROVIDER_FILE_DATE",
            "SNAPSHOT_TIME",
            "UNKNOWN",
        }


class TestStoragePriority:
    def test_exact_frozen_values(self) -> None:
        assert {e.value for e in StoragePriority} == {"P0", "P1", "P2", "P3"}

    def test_no_market_score_implication(self) -> None:
        # Storage policy classes must not look like market-importance scores.
        for e in StoragePriority:
            assert e.value.startswith("P")


class TestDiskPressure:
    def test_exact_frozen_values(self) -> None:
        assert {e.value for e in DiskPressure} == {
            "NORMAL",
            "WATCH",
            "CONSTRAINED",
            "CRITICAL",
        }

    def test_thresholds_not_baked_in(self) -> None:
        # The enum has no numeric threshold fields.
        assert not hasattr(DiskPressure, "NORMAL_THRESHOLD")


class TestBackupClass:
    def test_exact_frozen_values(self) -> None:
        assert {e.value for e in BackupClass} == {
            "UNBACKED",
            "MANIFEST_BACKED",
            "SECOND_COPY_VERIFIED",
            "OFFSITE_VERIFIED",
        }


class TestStorageJobStatus:
    def test_exact_frozen_values(self) -> None:
        assert {e.value for e in StorageJobStatus} == {
            "PLANNED",
            "ACQUIRING",
            "RAW_STAGED",
            "RAW_COMMITTED",
            "PROJECTION_PENDING",
            "PROJECTION_COMMITTED",
            "MANIFEST_COMMITTED",
            "CHECKPOINT_ADVANCED",
            "COMPLETE",
            "FAILED_RETRYABLE",
            "FAILED_TERMINAL",
            "QUARANTINED",
        }


class TestIntegrityAndCoverageAreDistinct:
    def test_separate_classes(self) -> None:
        assert IntegrityState is not CoverageState
        values = {e.value for e in IntegrityState}
        cov_values = {e.value for e in CoverageState}
        # No overlapping member names: integrity and coverage are separate.
        assert values.isdisjoint(cov_values)


class TestStorageObjectType:
    def test_typed_object_identity(self) -> None:
        assert {e.value for e in StorageObjectType} == {
            "EVIDENCE_BLOB",
            "ACQUISITION_RECORD",
            "RAW_PROJECTION",
            "PARTITION_MANIFEST",
            "SOURCE_REVISION",
            "STORAGE_JOB",
            "EXPORT_MANIFEST",
        }
