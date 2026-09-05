"""SENSOR-B4-I04R1 — provenance + integrity + pointer-truth microseal tests.

SENSOR-B4-I04R1A stage: the acquisition-provenance gate (Defect A) — every
non-empty manifest blob_ref requires a durable matching AcquisitionRecord
(I04R1 §4-§11; the frozen ordering is never skipped).  Later R1 stages add
the H3 (B), blobless/secret (C) and pointer (D) classes to this file.

Regression coverage: P1-P5 crash matrix and old-or-new pointer visibility
remain green under the sealed pointer schema.
"""

from __future__ import annotations

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
    EvidenceBlob,
    IntegrityState,
    LocalBlobStore,
    MissingAcquisitionProvenance,
    PartitionManifest,
    PartitionManifestRepository,
    StorageEncoding,
)

FIXED = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"
PK = "KRAKEN_FUTURES/MECHANICAL_FUNDING/PI_XBTUSD/2026-08"


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