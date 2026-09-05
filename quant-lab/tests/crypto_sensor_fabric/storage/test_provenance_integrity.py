"""SENSOR-B4-I04R1 — provenance + integrity + pointer-truth microseal tests.

Covers the four operator TRUTH-SEAM classes (I04R1 §0):

A. every non-empty manifest blob_ref requires durable matching acquisition
   provenance (I04R1 §4-§11 — the frozen ordering is never skipped);
B. provider checksums (H3) are recomputed over the EXACT decoded source
   bytes — a caller boolean is never verification evidence (I04R1 §14-§24);
C. blobless outcomes require closed explicit failure evidence and secret-
   bearing acquisition metadata is refused before persistence
   (I04R1 §25-§33);
D. the current pointer is a closed, strictly-typed JSON contract bound to
   the requested partition_key and to the manifest's ancestry
   (I04R1 §34-§40).

Regression coverage: P1-P5 crash matrix and old-or-new pointer visibility
remain green under the sealed pointer schema.
"""

from __future__ import annotations

import hashlib
import json
import zlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity
from crypto_sensor_fabric.storage import (
    AcquisitionRecord,
    AcquisitionRepository,
    BlobMetadataRepository,
    CatalogIntegrityError,
    EvidenceBlob,
    IntegrityState,
    LocalBlobStore,
    MissingAcquisitionProvenance,
    PartitionManifest,
    PartitionManifestRepository,
    ProviderChecksumClaimConflict,
    SecretBearingAcquisitionMetadata,
    StorageEncoding,
    UnearnedProviderIntegrityClaim,
)
FIXED = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"
PK = "KRAKEN_FUTURES/MECHANICAL_FUNDING/PI_XBTUSD/2026-08"
PK_OTHER = "OKX_SPOT/MECHANICAL_OPEN_INTEREST/PI_ETHUSD/2026-08"


def make_store(root: Path) -> LocalBlobStore:
    return LocalBlobStore(root, clock=lambda: FIXED)


def _put(store: LocalBlobStore, data: bytes) -> EvidenceBlob:
    return store.put_bytes(
        data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
    ).blob


def _acquisition(**overrides: Any) -> AcquisitionRecord:
    kwargs: dict[str, Any] = {
        "acquisition_id": "acq-1",
        "provider_id": "KRAKEN_FUTURES",
        "venue": "KRAKEN_FUTURES",
        "sensor_family": SensorFamily.MECHANICAL_FUNDING,
        "request_fingerprint": "fp-prov",
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


def _repos(
    root: Path,
) -> tuple[LocalBlobStore, BlobMetadataRepository, AcquisitionRepository, PartitionManifestRepository]:
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


def _seed_blob(
    store: LocalBlobStore, blob_repo: BlobMetadataRepository, data: bytes
) -> str:
    blob = _put(store, data)
    blob_repo.append_metadata(blob)
    return blob.blob_sha256


class TestAcquisitionProvenanceGate:
    """I04R1 §43 — Defect A: acquisition-before-manifest."""

    def test_no_acquisition_manifest_rejected(self, tmp_path: Path) -> None:
        """1: physical blob + metadata only -> manifest FAILS."""
        store, blob_repo, _, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, b"bytes-1")
        with pytest.raises(MissingAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(blob_refs=[sha]), expected_current=None
            )

    def test_matching_acquisition_manifest_accepted(self, tmp_path: Path) -> None:
        """2: durable matching acquisition -> manifest accepted."""
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, b"bytes-2")
        acq_repo.append_acquisition(
            _acquisition(acquisition_id="acq-m", blob_sha256=sha)
        )
        result = manifest_repo.append_partition_manifest(
            _manifest(
                blob_refs=[sha],
                integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
            ),
            expected_current=None,
        )
        assert result.disposition.value == "COMMITTED_NEW"

    def test_wrong_provider_rejected(self, tmp_path: Path) -> None:
        """3: same bytes do NOT transfer provider identity (I04R1 §7)."""
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, b"bytes-3")
        acq_repo.append_acquisition(
            _acquisition(acquisition_id="acq-kraken", blob_sha256=sha)
        )
        with pytest.raises(MissingAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-okx",
                    provider="OKX",
                    venue="OKX",
                    blob_refs=[sha],
                ),
                expected_current=None,
            )

    def test_wrong_venue_rejected(self, tmp_path: Path) -> None:
        """4: same provider, different venue -> rejected."""
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, b"bytes-4")
        acq_repo.append_acquisition(
            _acquisition(acquisition_id="acq-v", blob_sha256=sha)
        )
        with pytest.raises(MissingAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-v",
                    venue="KRAKEN_SPOT",
                    blob_refs=[sha],
                ),
                expected_current=None,
            )

    def test_wrong_sensor_rejected(self, tmp_path: Path) -> None:
        """5: same bytes do NOT manufacture sensor-family attribution (§8)."""
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, b"bytes-5")
        acq_repo.append_acquisition(
            _acquisition(acquisition_id="acq-f", blob_sha256=sha)
        )
        with pytest.raises(MissingAcquisitionProvenance):
            manifest_repo.append_partition_manifest(
                _manifest(
                    partition_manifest_id="pm-oi",
                    sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
                    blob_refs=[sha],
                ),
                expected_current=None,
            )

    def test_wrong_native_instrument_rejected(self, tmp_path: Path) -> None:
        """6: same bytes / wrong native instrument -> rejected."""
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, b"bytes-6")
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

    def test_granularity_conflict_when_both_known_rejected(
        self, tmp_path: Path
    ) -> None:
        """7: granularity mismatch when both sides are known -> rejected."""
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, b"bytes-7")
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

    def test_multiple_acquisitions_one_matching_accepted(
        self, tmp_path: Path
    ) -> None:
        """8: >=1 durable matching acquisition suffices; history not deduped."""
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, b"bytes-8")
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-okx", provider_id="OKX", venue="OKX", blob_sha256=sha
            )
        )
        acq_repo.append_acquisition(
            _acquisition(acquisition_id="acq-matching", blob_sha256=sha)
        )
        result = manifest_repo.append_partition_manifest(
            _manifest(
                blob_refs=[sha],
                integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
            ),
            expected_current=None,
        )
        assert result.disposition.value == "COMMITTED_NEW"

    def test_zero_blob_manifest_remains_valid(self, tmp_path: Path) -> None:
        """9: no blob claim -> no provenance required; UNVERIFIED only."""
        _, _, _, manifest_repo = _repos(tmp_path)
        result = manifest_repo.append_partition_manifest(
            _manifest(coverage_state="NOT_ATTEMPTED"), expected_current=None
        )
        assert result.disposition.value == "COMMITTED_NEW"
        current = manifest_repo.get_current_manifest(PK)
        assert current.integrity_state is IntegrityState.UNVERIFIED
        assert current.coverage_state.value == "NOT_ATTEMPTED"


class TestH3Recomputation:
    """I04R1 §44 — Defect B: provider integrity earned from exact bytes."""

    DATA = b'{"funding_rate": 1.5e-07, "ts": 1723000000}'

    @staticmethod
    def _seed(root: Path, data: bytes = DATA) -> tuple[str, LocalBlobStore, BlobMetadataRepository, AcquisitionRepository]:
        store = make_store(root)
        blob_repo = BlobMetadataRepository(root, blob_store=store, clock=lambda: FIXED)
        acq_repo = AcquisitionRepository(
            root,
            blob_store=store,
            blob_metadata_repository=blob_repo,
            clock=lambda: FIXED,
        )
        blob = _put(store, data)
        blob_repo.append_metadata(blob)
        return blob.blob_sha256, store, blob_repo, acq_repo

    def test_real_md5_verified_accepted(self, tmp_path: Path) -> None:
        """10: real MD5 + verified=True -> accepted."""
        sha, _, _, acq_repo = self._seed(tmp_path)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-md5",
                blob_sha256=sha,
                provider_checksum_algorithm="MD5",
                provider_checksum_value=hashlib.md5(self.DATA).hexdigest(),
                provider_checksum_verified=True,
            )
        )
        loaded = acq_repo.get_acquisition("acq-md5")
        assert loaded.provider_checksum_verified is True

    def test_fake_md5_verified_rejected(self, tmp_path: Path) -> None:
        """11: all-zero MD5 + verified=True -> ProviderChecksumClaimConflict."""
        sha, _, _, acq_repo = self._seed(tmp_path)
        with pytest.raises(ProviderChecksumClaimConflict):
            acq_repo.append_acquisition(
                _acquisition(
                    acquisition_id="acq-fake",
                    blob_sha256=sha,
                    provider_checksum_algorithm="MD5",
                    provider_checksum_value="0" * 32,
                    provider_checksum_verified=True,
                )
            )

    def test_real_sha256_h3_accepted(self, tmp_path: Path) -> None:
        """12: real SHA256 H3 -> accepted."""
        sha, _, _, acq_repo = self._seed(tmp_path)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-sha",
                blob_sha256=sha,
                provider_checksum_algorithm="SHA256",
                provider_checksum_value=hashlib.sha256(self.DATA).hexdigest(),
                provider_checksum_verified=True,
            )
        )
        assert acq_repo.get_acquisition("acq-sha").provider_checksum_verified is True

    def test_real_crc32_h3_accepted(self, tmp_path: Path) -> None:
        """13: real CRC32 H3 (8 lowercase hex) -> accepted."""
        sha, _, _, acq_repo = self._seed(tmp_path)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-crc",
                blob_sha256=sha,
                provider_checksum_algorithm="CRC32",
                provider_checksum_value=format(zlib.crc32(self.DATA), "08x"),
                provider_checksum_verified=True,
            )
        )
        assert acq_repo.get_acquisition("acq-crc").provider_checksum_verified is True

    def test_verified_false_when_bytes_match_rejected(self, tmp_path: Path) -> None:
        """14: verified=False against matching bytes -> claim conflict."""
        sha, _, _, acq_repo = self._seed(tmp_path)
        with pytest.raises(ProviderChecksumClaimConflict):
            acq_repo.append_acquisition(
                _acquisition(
                    acquisition_id="acq-mis",
                    blob_sha256=sha,
                    provider_checksum_algorithm="MD5",
                    provider_checksum_value=hashlib.md5(self.DATA).hexdigest(),
                    provider_checksum_verified=False,
                )
            )

    def test_verified_true_with_blob_none_rejected(self, tmp_path: Path) -> None:
        """15: verified=True with no durable source bytes -> rejected."""
        _, _, _, acq_repo = self._seed(tmp_path)
        with pytest.raises(ProviderChecksumClaimConflict):
            acq_repo.append_acquisition(
                _acquisition(
                    acquisition_id="acq-nb",
                    blob_sha256=None,
                    http_status_or_source_status="503",
                    failure_ref="gate:rate_limited",
                    provider_checksum_algorithm="MD5",
                    provider_checksum_value=hashlib.md5(self.DATA).hexdigest(),
                    provider_checksum_verified=True,
                )
            )

    def test_algorithm_never_inferred(self, tmp_path: Path) -> None:
        """16: unknown explicit algorithm -> typed conflict, no length guess."""
        sha, _, _, acq_repo = self._seed(tmp_path)
        with pytest.raises(ProviderChecksumClaimConflict):
            acq_repo.append_acquisition(
                _acquisition(
                    acquisition_id="acq-unknown",
                    blob_sha256=sha,
                    provider_checksum_algorithm="XXH64",
                    provider_checksum_value="deadbeef",
                    provider_checksum_verified=True,
                )
            )

    def test_unearned_provider_blob_metadata_rejected(self, tmp_path: Path) -> None:
        """17: caller-set PROVIDER_HASH_VERIFIED metadata -> rejected."""
        store = make_store(tmp_path)
        blob_repo = BlobMetadataRepository(tmp_path, blob_store=store, clock=lambda: FIXED)
        blob = _put(store, self.DATA)
        with pytest.raises(UnearnedProviderIntegrityClaim):
            blob_repo.append_metadata(
                blob.model_copy(
                    update={"integrity_state": IntegrityState.PROVIDER_HASH_VERIFIED}
                )
            )

    def test_local_verified_metadata_remains_accepted(self, tmp_path: Path) -> None:
        """18: LOCAL_HASH_VERIFIED metadata remains appendable."""
        store = make_store(tmp_path)
        blob_repo = BlobMetadataRepository(tmp_path, blob_store=store, clock=lambda: FIXED)
        blob = _put(store, self.DATA)
        returned, _ = blob_repo.append_metadata(blob)
        assert returned.integrity_state is IntegrityState.LOCAL_HASH_VERIFIED

    def test_provider_manifest_claim_without_earned_h3_rejected(
        self, tmp_path: Path
    ) -> None:
        """19: PROVIDER manifest claim needs earned H3 on EVERY blob."""
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, self.DATA)
        acq_repo.append_acquisition(
            _acquisition(acquisition_id="acq-prov", blob_sha256=sha)  # NO H3
        )
        with pytest.raises(UnearnedProviderIntegrityClaim):
            manifest_repo.append_partition_manifest(
                _manifest(
                    blob_refs=[sha],
                    integrity_state=IntegrityState.PROVIDER_HASH_VERIFIED,
                ),
                expected_current=None,
            )

    def test_provider_manifest_claim_with_earned_h3_accepted(
        self, tmp_path: Path
    ) -> None:
        """20: earned matching H3 on every blob -> PROVIDER claim accepted."""
        store, blob_repo, acq_repo, manifest_repo = _repos(tmp_path)
        sha = _seed_blob(store, blob_repo, self.DATA)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-h3",
                blob_sha256=sha,
                provider_checksum_algorithm="SHA256",
                provider_checksum_value=hashlib.sha256(self.DATA).hexdigest(),
                provider_checksum_verified=True,
            )
        )
        result = manifest_repo.append_partition_manifest(
            _manifest(
                blob_refs=[sha],
                integrity_state=IntegrityState.PROVIDER_HASH_VERIFIED,
            ),
            expected_current=None,
        )
        assert result.disposition.value == "COMMITTED_NEW"
        assert (
            manifest_repo.get_current_manifest(PK).integrity_state
            is IntegrityState.PROVIDER_HASH_VERIFIED
        )


class TestBloblessAndSecrets:
    """I04R1 §45 — Defect C: closed failure evidence + non-secret metadata."""

    def test_blobless_ok_rejected(self, tmp_path: Path) -> None:
        """21: blobless 'OK' without failure_ref -> rejected (no 2xx guess)."""
        _, _, acq_repo, _ = _repos(tmp_path)
        with pytest.raises(CatalogIntegrityError):
            acq_repo.append_acquisition(
                _acquisition(
                    acquisition_id="acq-ok", blob_sha256=None, http_status_or_source_status="OK"
                )
            )

    def test_blobless_success_rejected(self, tmp_path: Path) -> None:
        """22: blobless 'SUCCESS' without failure_ref -> rejected."""
        _, _, acq_repo, _ = _repos(tmp_path)
        with pytest.raises(CatalogIntegrityError):
            acq_repo.append_acquisition(
                _acquisition(
                    acquisition_id="acq-succ",
                    blob_sha256=None,
                    http_status_or_source_status="SUCCESS",
                )
            )

    def test_blobless_failure_ref_accepted(self, tmp_path: Path) -> None:
        """23: blobless with explicit failure_ref -> accepted."""
        _, _, acq_repo, _ = _repos(tmp_path)
        rec, _ = acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-fail",
                blob_sha256=None,
                http_status_or_source_status="503",
                failure_ref="gate:rate_limited",
                quality_flags=[],
            )
        )
        assert rec.failure_ref == "gate:rate_limited"

    def test_blobless_numeric_http_failure_accepted(self, tmp_path: Path) -> None:
        """§27: only an explicitly parsed HTTP failure code may contribute."""
        _, _, acq_repo, _ = _repos(tmp_path)
        acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-503",
                blob_sha256=None,
                http_status_or_source_status="503",
                failure_ref="provider:gate_geo",
            )
        )
        assert acq_repo.get_acquisition("acq-503").http_status_or_source_status == "503"

    def test_endpoint_path_with_api_key_rejected(self, tmp_path: Path) -> None:
        """24: endpoint_path carrying ?api_key= -> refused."""
        _, _, acq_repo, _ = _repos(tmp_path)
        with pytest.raises(SecretBearingAcquisitionMetadata):
            acq_repo.append_acquisition(
                _acquisition(
                    acquisition_id="acq-sec1",
                    blob_sha256=None,
                    http_status_or_source_status="503",
                    failure_ref="gate:x",
                    endpoint_path="/api/charts?api_key=fake123",
                )
            )

    def test_source_locator_token_query_rejected(self, tmp_path: Path) -> None:
        """25: source_locator with a token query -> refused."""
        _, _, acq_repo, _ = _repos(tmp_path)
        with pytest.raises(SecretBearingAcquisitionMetadata):
            acq_repo.append_acquisition(
                _acquisition(
                    acquisition_id="acq-sec2",
                    blob_sha256=None,
                    http_status_or_source_status="503",
                    failure_ref="gate:x",
                    source_locator="https://futures.kraken.com/api?token=sekrit",
                )
            )

    def test_source_locator_signature_query_rejected(self, tmp_path: Path) -> None:
        """26: source_locator with a signature query -> refused."""
        _, _, acq_repo, _ = _repos(tmp_path)
        with pytest.raises(SecretBearingAcquisitionMetadata):
            acq_repo.append_acquisition(
                _acquisition(
                    acquisition_id="acq-sec3",
                    blob_sha256=None,
                    http_status_or_source_status="503",
                    failure_ref="gate:x",
                    source_locator="https://futures.kraken.com/api?signature=abc123",
                )
            )

    def test_url_userinfo_rejected(self, tmp_path: Path) -> None:
        """27: URL userinfo credentials -> refused."""
        _, _, acq_repo, _ = _repos(tmp_path)
        with pytest.raises(SecretBearingAcquisitionMetadata):
            acq_repo.append_acquisition(
                _acquisition(
                    acquisition_id="acq-sec4",
                    blob_sha256=None,
                    http_status_or_source_status="503",
                    failure_ref="gate:x",
                    source_locator="https://user:sekrit@futures.kraken.com/api",
                )
            )

    def test_public_query_param_preserved(self, tmp_path: Path) -> None:
        """28: non-secret query parameters are preserved, not stripped."""
        _, _, acq_repo, _ = _repos(tmp_path)
        rec, _ = acq_repo.append_acquisition(
            _acquisition(
                acquisition_id="acq-pub",
                blob_sha256=None,
                http_status_or_source_status="503",
                failure_ref="gate:x",
                source_locator="https://futures.kraken.com/api?page=2&venue=test",
            )
        )
        assert rec.source_locator == "https://futures.kraken.com/api?page=2&venue=test"

    def test_error_never_echoes_secret_value(self, tmp_path: Path) -> None:
        """29: failure text names the KEY, never the secret VALUE."""
        _, _, acq_repo, _ = _repos(tmp_path)
        for locator, secret in [
            ("https://host/x?token=super-secret-value-xyz", "super-secret-value-xyz"),
            ("https://host/x?api_key=ultra-secret-abc", "ultra-secret-abc"),
        ]:
            with pytest.raises(SecretBearingAcquisitionMetadata) as excinfo:
                acq_repo.append_acquisition(
                    _acquisition(
                        acquisition_id="acq-sec9",
                        blob_sha256=None,
                        http_status_or_source_status="503",
                        failure_ref="gate:x",
                        source_locator=locator,
                    )
                )
            assert secret not in str(excinfo.value)


