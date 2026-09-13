"""SENSOR-B4-I04R2C — usable-provenance adversarial tests.

I04R2 §14-§19: durable acquisition HISTORY is not automatically USABLE
manifest provenance.  A failed acquisition (H3=False, explicit failure_ref,
explicitly parsed numeric HTTP failure) is retained as FORENSIC FAILURE
EVIDENCE — never deleted, never rejected at persistence — yet can never
satisfy a PartitionManifest provenance gate.  Clean matching acquisitions
support LOCAL_HASH_VERIFIED (H3 None or True) and PROVIDER_HASH_VERIFIED
(H3 True, earned by I04R1 recomputation).  Eligibility is applied AFTER
identity matching (I04R2 §17): wrong provider/sensor/instrument/granularity
regressions from I04R1 remain green.  Zero-blob manifests are unaffected
(I04R2 §18).
"""

from __future__ import annotations

import hashlib
import zlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity, QualityFlagAcquisition
from crypto_sensor_fabric.storage import (
    AcquisitionRecord,
    AcquisitionRepository,
    BlobMetadataRepository,
    IntegrityState,
    LocalBlobStore,
    MissingAcquisitionProvenance,
    NoUsableAcquisitionProvenance,
    PartitionManifest,
    PartitionManifestRepository,
    ProviderChecksumClaimConflict,
    StorageEncoding,
    UnearnedProviderIntegrityClaim,
    is_usable_manifest_provenance,
)

FIXED = datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"
PK = "KRAKEN_FUTURES/MECHANICAL_FUNDING/PI_XBTUSD/2026-08"

DATA = b'{"funding_rate": 1.5e-07, "ts": 1723000000}'


def make_store(root: Path) -> LocalBlobStore:
    return LocalBlobStore(root, clock=lambda: FIXED)


def _put(store: LocalBlobStore, data: bytes):
    return store.put_bytes(
        data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
    ).blob


def _acquisition(**overrides: Any) -> AcquisitionRecord:
    kwargs: dict[str, Any] = {
        "acquisition_id": "acq-1",
        "provider_id": "KRAKEN_FUTURES",
        "venue": "KRAKEN_FUTURES",
        "sensor_family": SensorFamily.MECHANICAL_FUNDING,
        "request_fingerprint": "fp-r2",
        "adapter_version": "kraken-adapter-v2",
        "requested_start": FIXED,
        "requested_end": FIXED,
        "native_instrument": "PI_XBTUSD",
        "native_granularity": Granularity.G1H,
        "request_started_at": FIXED,
        "response_observed_at": FIXED,
        "ingested_at": FIXED,
        "http_status_or_source_status": "200",
        "endpoint_host": "futures.kraken.com",
        "endpoint_path": "/api/charts/v1/analytics/PI_XBTUSD/funding",
        "request_family": "market_analytics_funding",
        "source_locator": "https://futures.kraken.com/api/charts/v1/analytics/PI_XBTUSD/funding",
        "blob_sha256": None,
        "failure_ref": None,
    }
    kwargs.update(overrides)
    return AcquisitionRecord(**kwargs)


def _manifest(**overrides: Any) -> PartitionManifest:
    kwargs: dict[str, Any] = {
        "partition_manifest_id": "pm-1",
        "partition_key": PK,
        "manifest_version": 1,
        "provider": "KRAKEN_FUTURES",
        "venue": "KRAKEN_FUTURES",
        "sensor_family": SensorFamily.MECHANICAL_FUNDING,
        "native_instrument": "PI_XBTUSD",
        "source_granularity": Granularity.G1H,
        "date_basis": "EVENT_TIME",
        "logical_date_start": datetime(2026, 8, 1, 0, 0, 0, tzinfo=UTC),
        "logical_date_end": datetime(2026, 8, 31, 23, 59, 59, tzinfo=UTC),
        "blob_refs": [],
        "projection_refs": [],
        "coverage_state": "PARTIAL",
        "integrity_state": IntegrityState.UNVERIFIED,
        "row_count": 0,
        "min_time": None,
        "max_time": None,
        "gap_count": 0,
        "revision_count": 0,
        "created_at": FIXED,
        "supersedes_manifest_id": None,
    }
    kwargs.update(overrides)
    return PartitionManifest(**kwargs)


def _repos(root: Path):
    store = make_store(root)
    blob_repo = BlobMetadataRepository(root, blob_store=store, clock=lambda: FIXED)
    acq_repo = AcquisitionRepository(
        root,
        blob_store=store,
        blob_metadata_repository=blob_repo,
        clock=lambda: FIXED,
    )
    manifest_repo = PartitionManifestRepository(
        root,
        blob_store=store,
        blob_metadata_repository=blob_repo,
        acquisition_repository=acq_repo,
        clock=lambda: FIXED,
    )
    return store, blob_repo, acq_repo, manifest_repo


def _seed_blob(store: LocalBlobStore, blob_repo: BlobMetadataRepository, data: bytes) -> str:
    blob = _put(store, data)
    blob_repo.append_metadata(blob)
    return blob.blob_sha256


class TestUsableProvenancePredicate:
    """I04R2 §5/§8/§10 — the ONE centralized eligibility predicate."""

    def _record(self, **overrides: Any) -> AcquisitionRecord:
        kwargs: dict[str, Any] = {
            "blob_sha256": "a" * 64,
            "provider_checksum_algorithm": "MD5",
            "provider_checksum_value": hashlib.md5(DATA).hexdigest(),
            "provider_checksum_verified": True,
        }
        kwargs.update(overrides)
        return _acquisition(**kwargs)

    def test_clean_record_is_usable(self) -> None:
        assert is_usable_manifest_provenance(self._record()) is True

    def test_h3_none_is_usable(self) -> None:
        record = _acquisition(
            blob_sha256="a" * 64,
            provider_checksum_algorithm=None,
            provider_checksum_value=None,
            provider_checksum_verified=None,
        )
        assert is_usable_manifest_provenance(record) is True

    def test_blob_none_disqualified(self) -> None:
        assert (
            is_usable_manifest_provenance(self._record(blob_sha256=None)) is False
        )

    def test_failure_ref_disqualified(self) -> None:
        assert (
            is_usable_manifest_provenance(self._record(failure_ref="gate:x"))
            is False
        )

    def test_numeric_http_failure_disqualified(self) -> None:
        assert (
            is_usable_manifest_provenance(
                self._record(http_status_or_source_status="503")
            )
            is False
        )

    def test_h3_false_disqualified(self) -> None:
        assert (
            is_usable_manifest_provenance(
                self._record(provider_checksum_verified=False)
            )
            is False
        )

    def test_quality_flags_never_disqualify(self) -> None:
        # I04R2 §5: partial data can still be truthful evidence.
        record = self._record(
            quality_flags=[
                QualityFlagAcquisition.PARTIAL_INTERVAL,
                QualityFlagAcquisition.SCHEMA_ADDITIVE,
                QualityFlagAcquisition.RATE_LIMITED,
            ]
        )
        assert is_usable_manifest_provenance(record) is True

    def test_h3_true_supports_provider_claim_only_when_earned(self) -> None:
        # I04R2 §9: True may support PROVIDER only because I04R1 recomputation
        # gates persistence; the predicate itself never trusts the boolean.
        record = self._record(provider_checksum_verified=True)
        assert is_usable_manifest_provenance(record) is True


class TestFailedH3ForensicHistory:
    """I04R2 §7/§14 — H3=False is forensic history, never manifest proof."""

    def test_failed_h3_acquisition_persists(self, tmp_path: Path) -> None:
        # I04R2 §14 steps 1-7: the failed record is durably retained.
        store, blob_repo, acq_repo, _ = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-failed",
                blob_sha256=sha,
                provider_checksum_algorithm="MD5",
                provider_checksum_value="0" * 32,  # deliberately WRONG
                provider_checksum_verified=False,
                failure_ref="provider:checksum_mismatch",
            )
        )
        loaded = acq_repo.get_acquisition("acq-failed")
        assert loaded.provider_checksum_verified is False
        assert loaded.failure_ref == "provider:checksum_mismatch"
        # forensic enumeration still sees it
        assert [
            r.acquisition_id for r in acq_repo.list_acquisitions_for_blob(sha)
        ] == ["acq-failed"]

    def test_failed_h3_cannot_support_local_manifest(self, tmp_path: Path) -> None:
        # I04R2 §14 step 8: LOCAL manifest referencing X must FAIL typed.
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-failed",
                blob_sha256=sha,
                provider_checksum_algorithm="MD5",
                provider_checksum_value="0" * 32,
                provider_checksum_verified=False,
                failure_ref="provider:checksum_mismatch",
            )
        )
        with pytest.raises(NoUsableAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(blob_refs=[sha], integrity_state=IntegrityState.LOCAL_HASH_VERIFIED),
                expected_current=None,
            )

    def test_failed_h3_cannot_support_provider_manifest(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-failed",
                blob_sha256=sha,
                provider_checksum_algorithm="MD5",
                provider_checksum_value="0" * 32,
                provider_checksum_verified=False,
                failure_ref="provider:checksum_mismatch",
            )
        )
        with pytest.raises(NoUsableAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(
                    blob_refs=[sha],
                    integrity_state=IntegrityState.PROVIDER_HASH_VERIFIED,
                ),
                expected_current=None,
            )

    def test_failed_h3_still_queryable_after_rejection(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-failed",
                blob_sha256=sha,
                provider_checksum_algorithm="MD5",
                provider_checksum_value="0" * 32,
                provider_checksum_verified=False,
                failure_ref="provider:checksum_mismatch",
            )
        )
        with pytest.raises(NoUsableAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(blob_refs=[sha]), expected_current=None
            )
        # the failed record remains durably queryable afterward (I04R2 §14)
        assert acq_repo.get_acquisition("acq-failed").failure_ref is not None
        assert len(acq_repo.list_acquisitions_for_blob(sha)) == 1

    def test_verified_false_persistence_still_requires_real_mismatch(
        self, tmp_path: Path
    ) -> None:
        # I04R1 §16 regression: verified=False requires an OBSERVED mismatch;
        # the usable-provenance layer never relaxes recomputation honesty.
        store, blob_repo, acq_repo, _ = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        with pytest.raises(ProviderChecksumClaimConflict):
            acq_repo.append_acquisition(
                _acquisition(
                    acquisition_id="acq-lie",
                    blob_sha256=sha,
                    provider_checksum_algorithm="MD5",
                    provider_checksum_value=hashlib.md5(DATA).hexdigest(),
                    provider_checksum_verified=False,  # bytes DO match -> lie
                    failure_ref="provider:x",
                )
            )

    def test_h3_true_with_failure_ref_cannot_prove_provider_integrity(
        self, tmp_path: Path
    ) -> None:
        # I04R2 §12: verified=True + failure_ref can never become provider
        # evidence.  Persistence path: verified=True + real H3 + failure_ref
        # is a legal durable record (the bytes DID verify; the acquisition
        # still failed for other reasons) — but has_earned_h3_proof and the
        # manifest gate must both refuse it.
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-h3-fail",
                blob_sha256=sha,
                provider_checksum_algorithm="SHA256",
                provider_checksum_value=hashlib.sha256(DATA).hexdigest(),
                provider_checksum_verified=True,
                failure_ref="ingest:downstream_error",
            )
        )
        assert acq_repo.has_earned_h3_proof(
            blob_sha256=sha,
            provider_id="KRAKEN_FUTURES",
            venue="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            native_instrument="PI_XBTUSD",
            native_granularity=Granularity.G1H,
        ) is False
        with pytest.raises(NoUsableAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(
                    blob_refs=[sha],
                    integrity_state=IntegrityState.PROVIDER_HASH_VERIFIED,
                ),
                expected_current=None,
            )


class TestFailedHttpWithBody:
    """I04R2 §6/§15 — explicit numeric failure with archived bytes."""

    def test_http_503_with_body_persists_as_forensic_history(
        self, tmp_path: Path
    ) -> None:
        store, blob_repo, acq_repo, _ = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-503",
                blob_sha256=sha,
                http_status_or_source_status="503",
                failure_ref="provider:unavailable_body_archived",
            )
        )
        loaded = acq_repo.get_acquisition("acq-503")
        assert loaded.http_status_or_source_status == "503"
        assert loaded.blob_sha256 == sha

    def test_http_503_with_body_rejected_for_manifest(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-503",
                blob_sha256=sha,
                http_status_or_source_status="503",
                failure_ref="provider:unavailable_body_archived",
            )
        )
        with pytest.raises(NoUsableAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(blob_refs=[sha], integrity_state=IntegrityState.LOCAL_HASH_VERIFIED),
                expected_current=None,
            )
        # bytes remain forensic T0A evidence — never discarded (I04R2 §6)
        assert len(acq_repo.list_acquisitions_for_blob(sha)) == 1

    def test_numeric_failure_without_failure_ref_also_disqualified(
        self, tmp_path: Path
    ) -> None:
        # §6: an explicitly parsed numeric >= 400 status disqualifies even
        # when no failure_ref was attached.
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-500",
                blob_sha256=sha,
                http_status_or_source_status="500",
            )
        )
        with pytest.raises(NoUsableAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(blob_refs=[sha]), expected_current=None
            )


class TestFailureRefWithBody:
    """I04R2 §10/§15 — failure_ref presence itself disqualifies."""

    def test_failure_ref_with_body_rejected_for_manifest(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-fref",
                blob_sha256=sha,
                http_status_or_source_status="200",  # healthy status
                failure_ref="ingest:operator_flagged",
            )
        )
        with pytest.raises(NoUsableAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(blob_refs=[sha], integrity_state=IntegrityState.LOCAL_HASH_VERIFIED),
                expected_current=None,
            )
        assert acq_repo.get_acquisition("acq-fref").blob_sha256 == sha


class TestGoodPlusFailed:
    """I04R2 §16 — a clean acquisition must not be poisoned by a failed one."""

    def test_clean_acquisition_supports_manifest_despite_failed_sibling(
        self, tmp_path: Path
    ) -> None:
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        # A: failed checksum / failure evidence
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-a-failed",
                blob_sha256=sha,
                provider_checksum_algorithm="MD5",
                provider_checksum_value="0" * 32,
                provider_checksum_verified=False,
                failure_ref="provider:checksum_mismatch",
            )
        )
        # B: clean usable matching acquisition
        acq_repo.append_acquisition(
            _acquisition(acquisition_id="acq-b-clean", blob_sha256=sha)
        )
        result = manifest_repo.append_partition_manifest(
            _manifest(blob_refs=[sha], integrity_state=IntegrityState.LOCAL_HASH_VERIFIED),
            expected_current=None,
        )
        assert result.disposition.value == "COMMITTED_NEW"
        # both records remain durably queryable — A is not deleted (I04R2 §4)
        ids = [r.acquisition_id for r in acq_repo.list_acquisitions_for_blob(sha)]
        assert ids == ["acq-a-failed", "acq-b-clean"]

    def test_usable_read_excludes_failed_records(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo, _ = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-a-failed",
                blob_sha256=sha,
                provider_checksum_algorithm="MD5",
                provider_checksum_value="0" * 32,
                provider_checksum_verified=False,
                failure_ref="provider:checksum_mismatch",
            )
        )
        acq_repo.append_acquisition(
            _acquisition(acquisition_id="acq-b-clean", blob_sha256=sha)
        )
        matching = acq_repo.find_matching_acquisitions(
            blob_sha256=sha,
            provider_id="KRAKEN_FUTURES",
            venue="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            native_instrument="PI_XBTUSD",
            native_granularity=Granularity.G1H,
        )
        usable = acq_repo.find_usable_matching_acquisitions(
            blob_sha256=sha,
            provider_id="KRAKEN_FUTURES",
            venue="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            native_instrument="PI_XBTUSD",
            native_granularity=Granularity.G1H,
        )
        assert [r.acquisition_id for r in matching] == [
            "acq-a-failed",
            "acq-b-clean",
        ]
        assert [r.acquisition_id for r in usable] == ["acq-b-clean"]


class TestCleanAcquisitionH3Semantics:
    """I04R2 §8/§9 — H3 None supports LOCAL, never PROVIDER; True supports both."""

    def test_clean_h3_none_supports_local(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(acquisition_id="acq-none", blob_sha256=sha)
        )
        result = manifest_repo.append_partition_manifest(
            _manifest(blob_refs=[sha], integrity_state=IntegrityState.LOCAL_HASH_VERIFIED),
            expected_current=None,
        )
        assert result.disposition.value == "COMMITTED_NEW"

    def test_clean_h3_none_cannot_support_provider(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(acquisition_id="acq-none", blob_sha256=sha)
        )
        with pytest.raises(UnearnedProviderIntegrityClaim):
            manifest_repo.append_partition_manifest(
                _manifest(
                    blob_refs=[sha],
                    integrity_state=IntegrityState.PROVIDER_HASH_VERIFIED,
                ),
                expected_current=None,
            )

    def test_clean_earned_h3_true_supports_local_and_provider(
        self, tmp_path: Path
    ) -> None:
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-earned",
                blob_sha256=sha,
                provider_checksum_algorithm="SHA256",
                provider_checksum_value=hashlib.sha256(DATA).hexdigest(),
                provider_checksum_verified=True,
            )
        )
        r1 = manifest_repo.append_partition_manifest(
            _manifest(
                partition_manifest_id="pm-local",
                blob_refs=[sha],
                integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
            ),
            expected_current=None,
        )
        assert r1.disposition.value == "COMMITTED_NEW"
        r2 = manifest_repo.append_partition_manifest(
            _manifest(
                partition_manifest_id="pm-prov",
                manifest_version=2,
                supersedes_manifest_id="pm-local",
                blob_refs=[sha],
                integrity_state=IntegrityState.PROVIDER_HASH_VERIFIED,
            ),
            expected_current=("pm-local", 1),
        )
        assert r2.disposition.value == "COMMITTED_NEW"


class TestIdentityRegressionAfterEligibility:
    """I04R2 §17 — eligibility is applied AFTER identity matching."""

    def test_wrong_provider_remains_rejected(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(acquisition_id="acq-p", blob_sha256=sha)
        )
        with pytest.raises(MissingAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-p",
                    provider="OKX",
                    venue="OKX",
                    blob_refs=[sha],
                ),
                expected_current=None,
            )

    def test_wrong_sensor_remains_rejected(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(acquisition_id="acq-s", blob_sha256=sha)
        )
        with pytest.raises(MissingAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-s",
                    sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
                    blob_refs=[sha],
                ),
                expected_current=None,
            )

    def test_wrong_instrument_remains_rejected(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(acquisition_id="acq-i", blob_sha256=sha)
        )
        with pytest.raises(MissingAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-i",
                    native_instrument="PI_ETHUSD",
                    blob_refs=[sha],
                ),
                expected_current=None,
            )

    def test_granularity_mismatch_remains_rejected(self, tmp_path: Path) -> None:
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        acq_repo.append_acquisition(
            _acquisition(acquisition_id="acq-g", blob_sha256=sha)
        )
        with pytest.raises(MissingAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-g",
                    source_granularity=Granularity.G1D,
                    blob_refs=[sha],
                ),
                expected_current=None,
            )

    def test_zero_blob_manifest_unaffected(self, tmp_path: Path) -> None:
        # I04R2 §18: no content provenance claimed -> no acquisition needed;
        # integrity > UNVERIFIED remains forbidden.
        _, _, _, manifest_repo = _repos(tmp_path)
        result = manifest_repo.append_partition_manifest(
            _manifest(coverage_state="NOT_ATTEMPTED"), expected_current=None
        )
        assert result.disposition.value == "COMMITTED_NEW"
        assert manifest_repo.get_current_manifest(PK).integrity_state is IntegrityState.UNVERIFIED

    def test_failed_h3_crc32_variant_also_disqualified(self, tmp_path: Path) -> None:
        # H3=False with CRC32 (not just MD5) never qualifies (I04R2 §7).
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, DATA)
        wrong_crc = format(zlib.crc32(DATA) ^ 0xFFFFFFFF, "08x")
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-crc-fail",
                blob_sha256=sha,
                provider_checksum_algorithm="CRC32",
                provider_checksum_value=wrong_crc,
                provider_checksum_verified=False,
                failure_ref="provider:crc_mismatch",
            )
        )
        with pytest.raises(NoUsableAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(blob_refs=[sha]), expected_current=None
            )
