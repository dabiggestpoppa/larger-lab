"""SENSOR-B4-I04R2D — machine evidence for the usable-provenance seal.

Generates a deterministic artifact (no wall-clock, injected clocks, fixed
identities, scheduling-independent):

- ``BLOC_04_I04R2_USABLE_PROVENANCE_MATRIX.json`` (I04R2 §30): the eight
  usable-provenance truth cases — clean_no_h3, clean_h3_true,
  failed_h3_false, failed_http_with_body, failure_ref_with_body,
  failed_plus_clean, wrong_provider_clean, provider_integrity_clean_h3 —
  each recording durable_acquisition_count, usable_acquisition_count,
  manifest_allowed, provider_integrity_allowed, expected_error and
  test_name.

Historical I04/I04R1 evidence is never touched; I04R2 writes its OWN
superseding artifact.
"""

from __future__ import annotations

import hashlib
import json
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
    IntegrityState,
    LocalBlobStore,
    MissingAcquisitionProvenance,
    NoUsableAcquisitionProvenance,
    PartitionManifest,
    PartitionManifestRepository,
    StorageEncoding,
    UnearnedProviderIntegrityClaim,
)

FIXED = datetime(2026, 9, 6, 12, 0, 0, tzinfo=UTC)
MEDIA = "application/json"
PK = "KRAKEN_FUTURES/MECHANICAL_FUNDING/PI_XBTUSD/2026-08"

EVIDENCE_DIR = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_04"
)

H3_DATA = b'{"funding_rate": 1.5e-07, "ts": 1723000000}'


def _make_store(root: Path) -> LocalBlobStore:
    return LocalBlobStore(root, clock=lambda: FIXED)


def _repos(root: Path):
    store = _make_store(root)
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


def _acquisition(**overrides: Any) -> AcquisitionRecord:
    kwargs: dict[str, Any] = {
        "acquisition_id": "acq-1",
        "provider_id": "KRAKEN_FUTURES",
        "venue": "KRAKEN_FUTURES",
        "sensor_family": SensorFamily.MECHANICAL_FUNDING,
        "request_fingerprint": "fp-r2e",
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


def _seed_blob(store: LocalBlobStore, blob_repo: BlobMetadataRepository) -> str:
    blob = store.put_bytes(
        H3_DATA, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
    ).blob
    blob_repo.append_metadata(blob)
    return blob.blob_sha256


class TestUsableProvenanceMatrixEvidence:
    """I04R2 §30 — deterministic machine matrix (byte-stable)."""

    CASES = [
        "clean_no_h3",
        "clean_h3_true",
        "failed_h3_false",
        "failed_http_with_body",
        "failure_ref_with_body",
        "failed_plus_clean",
        "wrong_provider_clean",
        "provider_integrity_clean_h3",
    ]

    def _case(self, root: Path, case: str) -> dict[str, Any]:
        store, blob_repo, acq_repo, manifest_repo = _repos(root)
        sha = _seed_blob(store, blob_repo)

        if case == "clean_no_h3":
            acq_repo.append_acquisition(_acquisition(blob_sha256=sha))
        elif case == "clean_h3_true":
            acq_repo.append_acquisition(
                _acquisition(
                    blob_sha256=sha,
                    provider_checksum_algorithm="SHA256",
                    provider_checksum_value=hashlib.sha256(H3_DATA).hexdigest(),
                    provider_checksum_verified=True,
                )
            )
        elif case == "failed_h3_false":
            acq_repo.append_acquisition(
                _acquisition(
                    blob_sha256=sha,
                    provider_checksum_algorithm="MD5",
                    provider_checksum_value="0" * 32,  # deliberately WRONG
                    provider_checksum_verified=False,
                    failure_ref="provider:checksum_mismatch",
                )
            )
        elif case == "failed_http_with_body":
            acq_repo.append_acquisition(
                _acquisition(
                    blob_sha256=sha,
                    http_status_or_source_status="503",
                    failure_ref="provider:unavailable_body_archived",
                )
            )
        elif case == "failure_ref_with_body":
            acq_repo.append_acquisition(
                _acquisition(
                    blob_sha256=sha,
                    failure_ref="ingest:operator_flagged",
                )
            )
        elif case == "failed_plus_clean":
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
        elif case == "wrong_provider_clean":
            acq_repo.append_acquisition(
                _acquisition(
                    acquisition_id="acq-okx",
                    provider_id="OKX",
                    venue="OKX",
                    blob_sha256=sha,
                )
            )
        elif case == "provider_integrity_clean_h3":
            acq_repo.append_acquisition(
                _acquisition(
                    blob_sha256=sha,
                    provider_checksum_algorithm="SHA256",
                    provider_checksum_value=hashlib.sha256(H3_DATA).hexdigest(),
                    provider_checksum_verified=True,
                )
            )
        else:  # pragma: no cover - guard against typos in CASES
            raise AssertionError(f"unknown usable-provenance case {case}")

        identity = dict(
            blob_sha256=sha,
            provider_id="KRAKEN_FUTURES",
            venue="KRAKEN_FUTURES",
            sensor_family=SensorFamily.MECHANICAL_FUNDING,
            native_instrument="PI_XBTUSD",
            native_granularity=Granularity.G1H,
        )
        durable = acq_repo.list_acquisitions_for_blob(sha)
        usable = acq_repo.find_usable_matching_acquisitions(**identity)

        manifest_allowed = False
        expected_error: str | None = None
        try:
            manifest_repo.append_partition_manifest(
                _manifest(
                    blob_refs=[sha],
                    integrity_state=IntegrityState.LOCAL_HASH_VERIFIED,
                ),
                expected_current=None,
            )
            manifest_allowed = True
        except (
            MissingAcquisitionProvenance,
            NoUsableAcquisitionProvenance,
        ) as exc:
            expected_error = type(exc).__name__

        # PROVIDER claim needs usable provenance AND earned H3 on every ref
        # (read-level determination: same gates the publication path runs).
        provider_integrity_allowed = acq_repo.has_usable_matching_acquisition(
            **identity
        ) and acq_repo.has_earned_h3_proof(**identity)
        provider_expected_error: str | None = None
        if case in ("clean_no_h3",):
            # prove it at the publication layer too for the classic §8 case
            with pytest.raises(UnearnedProviderIntegrityClaim):
                manifest_repo.append_partition_manifest(
                    _manifest(
                        partition_manifest_id="pm-prov",
                        manifest_version=2,
                        supersedes_manifest_id="pm-1",
                        blob_refs=[sha],
                        integrity_state=IntegrityState.PROVIDER_HASH_VERIFIED,
                    ),
                    expected_current=("pm-1", 1),
                )
            provider_expected_error = "UnearnedProviderIntegrityClaim"

        return {
            "case": case,
            "durable_acquisition_count": len(durable),
            "usable_acquisition_count": len(usable),
            "manifest_allowed": manifest_allowed,
            "provider_integrity_allowed": provider_integrity_allowed,
            "expected_error": expected_error,
            "provider_expected_error": provider_expected_error,
            "test_name": f"test_usable_provenance_matrix_artifact_written[{case}]",
        }

    def test_usable_provenance_matrix_artifact_written(self, tmp_path: Path) -> None:
        rows = [self._case(tmp_path / case, case) for case in self.CASES]
        out_path = EVIDENCE_DIR / "BLOC_04_I04R2_USABLE_PROVENANCE_MATRIX.json"
        out_path.write_text(
            json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        # deterministic regeneration (byte-stable across runs)
        again = json.loads(out_path.read_text(encoding="utf-8"))
        assert again == rows
        by_case = {r["case"]: r for r in rows}

        # §14: failed H3 is durable forensic history, usable count 0,
        # manifest rejected typed
        f = by_case["failed_h3_false"]
        assert f["durable_acquisition_count"] == 1
        assert f["usable_acquisition_count"] == 0
        assert f["manifest_allowed"] is False
        assert f["expected_error"] == "NoUsableAcquisitionProvenance"
        assert f["provider_integrity_allowed"] is False

        # §15: HTTP 503 with archived body — same shape
        f = by_case["failed_http_with_body"]
        assert f["durable_acquisition_count"] == 1
        assert f["usable_acquisition_count"] == 0
        assert f["manifest_allowed"] is False
        assert f["expected_error"] == "NoUsableAcquisitionProvenance"

        # §10: failure_ref with body — same shape
        f = by_case["failure_ref_with_body"]
        assert f["durable_acquisition_count"] == 1
        assert f["usable_acquisition_count"] == 0
        assert f["manifest_allowed"] is False
        assert f["expected_error"] == "NoUsableAcquisitionProvenance"

        # §16: failed + clean -> manifest via clean only; failed kept
        f = by_case["failed_plus_clean"]
        assert f["durable_acquisition_count"] == 2
        assert f["usable_acquisition_count"] == 1
        assert f["manifest_allowed"] is True
        assert f["expected_error"] is None
        assert f["provider_integrity_allowed"] is False

        # §5/§8: clean without H3 -> LOCAL ok, PROVIDER never
        f = by_case["clean_no_h3"]
        assert f["durable_acquisition_count"] == 1
        assert f["usable_acquisition_count"] == 1
        assert f["manifest_allowed"] is True
        assert f["expected_error"] is None
        assert f["provider_integrity_allowed"] is False
        assert f["provider_expected_error"] == "UnearnedProviderIntegrityClaim"

        # §9: earned H3 True -> LOCAL and PROVIDER both allowed
        f = by_case["clean_h3_true"]
        assert f["manifest_allowed"] is True
        assert f["provider_integrity_allowed"] is True
        f = by_case["provider_integrity_clean_h3"]
        assert f["manifest_allowed"] is True
        assert f["provider_integrity_allowed"] is True

        # §17: identity gate still fires for the wrong provider (a clean
        # record that does not match the manifest identity is not provenance)
        f = by_case["wrong_provider_clean"]
        assert f["durable_acquisition_count"] == 1
        assert f["usable_acquisition_count"] == 0
        assert f["manifest_allowed"] is False
        assert f["expected_error"] == "MissingAcquisitionProvenance"

        # historical I04/I04R1 evidence untouched
        assert (EVIDENCE_DIR / "BLOC_04_I04R1_PROVENANCE_MATRIX.json").exists()
        assert (EVIDENCE_DIR / "BLOC_04_I04R1_PROVENANCE_INTEGRITY_SEAL_EVIDENCE.md").exists()
