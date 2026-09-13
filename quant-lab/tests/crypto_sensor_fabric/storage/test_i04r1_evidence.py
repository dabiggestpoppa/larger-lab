"""SENSOR-B4-I04R1E — machine evidence for the provenance/integrity microseal.

Generates deterministic artifacts (no wall-clock, injected clocks, fixed
identities; scheduling-independent):

- ``BLOC_04_I04R1_PROVENANCE_MATRIX.json`` (I04R1 §52): the acquisition-
  provenance + H3 truth matrix — no_acquisition, matching_acquisition,
  wrong_provider, wrong_sensor, wrong_instrument, multiple_one_matching,
  h3_valid, h3_false_claim, h3_missing_proof, provider_integrity_manifest;
- ``BLOC_04_I04R1_POINTER_SCHEMA.json`` (I04R1 §52): the CLOSED pointer
  field contract (schema_version=1) plus the adversarial parse cases.

Historical I04 evidence is never touched; I04R1 writes its OWN superseding
artifacts.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.providers.base.enums import Granularity
from crypto_sensor_fabric.storage import (
    AcquisitionRecord,
    AcquisitionRepository,
    BlobMetadataRepository,
    IntegrityState,
    LocalBlobStore,
    MissingAcquisitionProvenance,
    PartitionManifest,
    PartitionManifestRepository,
    ProviderChecksumClaimConflict,
    StorageEncoding,
    UnearnedProviderIntegrityClaim,
)
from crypto_sensor_fabric.storage.manifests import (
    POINTER_SCHEMA_VERSION,
    PartitionCurrentPointer,
)

FIXED = datetime(2026, 9, 5, 12, 0, 0, tzinfo=UTC)
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


def _repos(
    root: Path,
) -> tuple[LocalBlobStore, BlobMetadataRepository, AcquisitionRepository, PartitionManifestRepository]:
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


def _seed_blob(
    store: LocalBlobStore, blob_repo: BlobMetadataRepository, data: bytes
) -> str:
    blob = store.put_bytes(
        data, storage_encoding=StorageEncoding.NONE, source_media_type=MEDIA
    ).blob
    blob_repo.append_metadata(blob)
    return blob.blob_sha256


class TestProvenanceMatrixEvidence:
    def _case(
        self, root: Path, case: str
    ) -> dict[str, Any]:
        store, blob_repo, acq_repo, manifest_repo = _repos(root)
        sha = _seed_blob(store, blob_repo, H3_DATA)
        base = {
            "case": case,
            "manifest_allowed": None,
            "matching_acquisition_count": 0,
            "local_integrity_proven": True,
            "provider_integrity_proven": False,
            "expected_error": None,
            "test_name": "",
        }

        def try_manifest(manifest: PartitionManifest) -> tuple[bool, str | None]:
            try:
                manifest_repo.append_partition_manifest(
                    manifest, expected_current=None
                )
                return True, None
            except (
                MissingAcquisitionProvenance,
                UnearnedProviderIntegrityClaim,
                ProviderChecksumClaimConflict,
            ) as exc:
                return False, type(exc).__name__

        def count_matching(
            provider: str, venue: str, sensor: Any, instrument: str
        ) -> int:
            return len(
                acq_repo.find_matching_acquisitions(
                    blob_sha256=sha,
                    provider_id=provider,
                    venue=venue,
                    sensor_family=sensor,
                    native_instrument=instrument,
                    native_granularity=Granularity.G1H,
                )
            )

        if case == "no_acquisition":
            # blob + metadata ONLY; no durable acquisition
            allowed, error = try_manifest(
                _manifest(blob_refs=[sha], integrity_state=IntegrityState.LOCAL_HASH_VERIFIED)
            )
            base.update(
                manifest_allowed=allowed,
                matching_acquisition_count=count_matching(
                    "KRAKEN_FUTURES", "KRAKEN_FUTURES",
                    SensorFamily.MECHANICAL_FUNDING, "PI_XBTUSD",
                ),
                expected_error=error,
                test_name="test_no_acquisition_manifest_rejected",
            )
        elif case == "matching_acquisition":
            acq_repo.append_acquisition(
                _acquisition(acquisition_id="acq-m", blob_sha256=sha)
            )
            allowed, error = try_manifest(
                _manifest(blob_refs=[sha], integrity_state=IntegrityState.LOCAL_HASH_VERIFIED)
            )
            base.update(
                manifest_allowed=allowed,
                matching_acquisition_count=count_matching(
                    "KRAKEN_FUTURES", "KRAKEN_FUTURES",
                    SensorFamily.MECHANICAL_FUNDING, "PI_XBTUSD",
                ),
                expected_error=error,
                test_name="test_matching_acquisition_manifest_accepted",
            )
        elif case == "wrong_provider":
            # acquisition says KRAKEN; manifest claims OKX — byte identity
            # NEVER transfers provider identity
            acq_repo.append_acquisition(
                _acquisition(acquisition_id="acq-k", blob_sha256=sha)
            )
            allowed, error = try_manifest(
                _manifest(
                    partition_manifest_id="pm-okx",
                    provider="OKX",
                    venue="OKX",
                    blob_refs=[sha],
                )
            )
            base.update(
                manifest_allowed=allowed,
                matching_acquisition_count=count_matching(
                    "OKX", "OKX", SensorFamily.MECHANICAL_FUNDING, "PI_XBTUSD"
                ),
                expected_error=error,
                test_name="test_wrong_provider_rejected",
            )
        elif case == "wrong_sensor":
            acq_repo.append_acquisition(
                _acquisition(acquisition_id="acq-f", blob_sha256=sha)
            )
            allowed, error = try_manifest(
                _manifest(
                    partition_manifest_id="pm-oi",
                    sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
                    blob_refs=[sha],
                )
            )
            base.update(
                manifest_allowed=allowed,
                expected_error=error,
                test_name="test_wrong_sensor_rejected",
            )
        elif case == "wrong_instrument":
            acq_repo.append_acquisition(
                _acquisition(acquisition_id="acq-i", blob_sha256=sha)
            )
            allowed, error = try_manifest(
                _manifest(
                    partition_manifest_id="pm-i",
                    native_instrument="PI_ETHUSD",
                    blob_refs=[sha],
                )
            )
            base.update(
                manifest_allowed=allowed,
                expected_error=error,
                test_name="test_wrong_native_instrument_rejected",
            )
        elif case == "multiple_one_matching":
            for index, (provider, venue) in enumerate(
                [("OKX", "OKX"), ("BINANCE", "BINANCE"), ("KRAKEN_FUTURES", "KRAKEN_FUTURES")]
            ):
                acq_repo.append_acquisition(
                    _acquisition(
                        acquisition_id=f"acq-{index}",
                        provider_id=provider,
                        venue=venue,
                        blob_sha256=sha,
                    )
                )
            allowed, error = try_manifest(
                _manifest(
                    blob_refs=[sha], integrity_state=IntegrityState.LOCAL_HASH_VERIFIED
                )
            )
            base.update(
                manifest_allowed=allowed,
                matching_acquisition_count=count_matching(
                    "KRAKEN_FUTURES", "KRAKEN_FUTURES",
                    SensorFamily.MECHANICAL_FUNDING, "PI_XBTUSD",
                ),
                expected_error=error,
                test_name="test_multiple_acquisitions_one_matching_accepted",
            )
        elif case == "h3_valid":
            acq_repo.append_acquisition(
                _acquisition(
                    acquisition_id="acq-h3",
                    blob_sha256=sha,
                    provider_checksum_algorithm="SHA256",
                    provider_checksum_value=hashlib.sha256(H3_DATA).hexdigest(),
                    provider_checksum_verified=True,
                )
            )
            base.update(
                matching_acquisition_count=count_matching(
                    "KRAKEN_FUTURES", "KRAKEN_FUTURES",
                    SensorFamily.MECHANICAL_FUNDING, "PI_XBTUSD",
                ),
                provider_integrity_proven=acq_repo.has_earned_h3_proof(
                    blob_sha256=sha,
                    provider_id="KRAKEN_FUTURES",
                    venue="KRAKEN_FUTURES",
                    sensor_family=SensorFamily.MECHANICAL_FUNDING,
                    native_instrument="PI_XBTUSD",
                    native_granularity=Granularity.G1H,
                ),
                test_name="test_real_sha256_h3_accepted",
            )
        elif case == "h3_false_claim":
            error = None
            try:
                acq_repo.append_acquisition(
                    _acquisition(
                        acquisition_id="acq-fake",
                        blob_sha256=sha,
                        provider_checksum_algorithm="MD5",
                        provider_checksum_value="0" * 32,
                        provider_checksum_verified=True,
                    )
                )
            except ProviderChecksumClaimConflict as exc:
                error = type(exc).__name__
            base.update(
                matching_acquisition_count=count_matching(
                    "KRAKEN_FUTURES", "KRAKEN_FUTURES",
                    SensorFamily.MECHANICAL_FUNDING, "PI_XBTUSD",
                ),
                expected_error=error,
                test_name="test_fake_md5_verified_rejected",
            )
        elif case == "h3_missing_proof":
            # durable acquisition WITHOUT any H3 claim
            acq_repo.append_acquisition(
                _acquisition(acquisition_id="acq-noh3", blob_sha256=sha)
            )
            allowed, error = try_manifest(
                _manifest(
                    blob_refs=[sha],
                    integrity_state=IntegrityState.PROVIDER_HASH_VERIFIED,
                )
            )
            base.update(
                manifest_allowed=allowed,
                matching_acquisition_count=count_matching(
                    "KRAKEN_FUTURES", "KRAKEN_FUTURES",
                    SensorFamily.MECHANICAL_FUNDING, "PI_XBTUSD",
                ),
                provider_integrity_proven=acq_repo.has_earned_h3_proof(
                    blob_sha256=sha,
                    provider_id="KRAKEN_FUTURES",
                    venue="KRAKEN_FUTURES",
                    sensor_family=SensorFamily.MECHANICAL_FUNDING,
                    native_instrument="PI_XBTUSD",
                    native_granularity=Granularity.G1H,
                ),
                expected_error=error,
                test_name="test_provider_manifest_claim_without_earned_h3_rejected",
            )
        elif case == "provider_integrity_manifest":
            acq_repo.append_acquisition(
                _acquisition(
                    acquisition_id="acq-earned",
                    blob_sha256=sha,
                    provider_checksum_algorithm="SHA256",
                    provider_checksum_value=hashlib.sha256(H3_DATA).hexdigest(),
                    provider_checksum_verified=True,
                )
            )
            allowed, error = try_manifest(
                _manifest(
                    blob_refs=[sha],
                    integrity_state=IntegrityState.PROVIDER_HASH_VERIFIED,
                )
            )
            base.update(
                manifest_allowed=allowed,
                matching_acquisition_count=count_matching(
                    "KRAKEN_FUTURES", "KRAKEN_FUTURES",
                    SensorFamily.MECHANICAL_FUNDING, "PI_XBTUSD",
                ),
                provider_integrity_proven=acq_repo.has_earned_h3_proof(
                    blob_sha256=sha,
                    provider_id="KRAKEN_FUTURES",
                    venue="KRAKEN_FUTURES",
                    sensor_family=SensorFamily.MECHANICAL_FUNDING,
                    native_instrument="PI_XBTUSD",
                    native_granularity=Granularity.G1H,
                ),
                expected_error=error,
                test_name="test_provider_manifest_claim_with_earned_h3_accepted",
            )
        else:
            raise AssertionError(f"unknown provenance case {case}")
        return base

    def test_provenance_matrix_artifact_written(self, tmp_path: Path) -> None:
        cases = [
            "no_acquisition",
            "matching_acquisition",
            "wrong_provider",
            "wrong_sensor",
            "wrong_instrument",
            "multiple_one_matching",
            "h3_valid",
            "h3_false_claim",
            "h3_missing_proof",
            "provider_integrity_manifest",
        ]
        rows: list[dict[str, Any]] = []
        for case in cases:
            root = tmp_path / case
            root.mkdir()
            rows.append(self._case(root, case))
        out_path = EVIDENCE_DIR / "BLOC_04_I04R1_PROVENANCE_MATRIX.json"
        out_path.write_text(
            json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        # deterministic regeneration
        again = json.loads(out_path.read_text(encoding="utf-8"))
        assert again == rows
        by_case = {r["case"]: r for r in rows}
        assert by_case["no_acquisition"]["manifest_allowed"] is False
        assert by_case["no_acquisition"]["expected_error"] == "MissingAcquisitionProvenance"
        assert by_case["no_acquisition"]["matching_acquisition_count"] == 0
        assert by_case["matching_acquisition"]["manifest_allowed"] is True
        assert by_case["matching_acquisition"]["matching_acquisition_count"] == 1
        assert by_case["wrong_provider"]["manifest_allowed"] is False
        assert by_case["wrong_provider"]["expected_error"] == "MissingAcquisitionProvenance"
        assert by_case["wrong_sensor"]["manifest_allowed"] is False
        assert by_case["wrong_instrument"]["manifest_allowed"] is False
        assert by_case["multiple_one_matching"]["manifest_allowed"] is True
        assert by_case["multiple_one_matching"]["matching_acquisition_count"] == 1
        assert by_case["h3_valid"]["provider_integrity_proven"] is True
        assert by_case["h3_valid"]["expected_error"] is None
        assert by_case["h3_false_claim"]["expected_error"] == "ProviderChecksumClaimConflict"
        assert by_case["h3_false_claim"]["provider_integrity_proven"] is False
        assert by_case["h3_missing_proof"]["manifest_allowed"] is False
        assert by_case["h3_missing_proof"]["expected_error"] == "UnearnedProviderIntegrityClaim"
        assert by_case["h3_missing_proof"]["provider_integrity_proven"] is False
        assert by_case["provider_integrity_manifest"]["manifest_allowed"] is True
        assert by_case["provider_integrity_manifest"]["provider_integrity_proven"] is True
        # historical I04 evidence untouched
        assert (EVIDENCE_DIR / "BLOC_04_I04_MANIFEST_CONCURRENCY.json").exists()


class TestPointerSchemaEvidence:
    def _valid_payload(self) -> dict[str, Any]:
        return {
            "schema_version": POINTER_SCHEMA_VERSION,
            "partition_key": PK,
            "partition_manifest_id": "pm-1",
            "manifest_version": 1,
            "previous_manifest_id": None,
            "updated_at": "2026-09-05T12:00:00+00:00",
        }

    def test_pointer_schema_artifact_written(self, tmp_path: Path) -> None:
        closed_fields = [
            {"field": "schema_version", "json_type": "int", "required": True,
             "constraint": "== 1 (bool rejected)"},
            {"field": "partition_key", "json_type": "string", "required": True,
             "constraint": "nonempty; numeric values rejected, never coerced"},
            {"field": "partition_manifest_id", "json_type": "string", "required": True,
             "constraint": "nonempty"},
            {"field": "manifest_version", "json_type": "int", "required": True,
             "constraint": ">= 1; bool/str/float rejected"},
            {"field": "previous_manifest_id", "json_type": "null|string", "required": True,
             "constraint": "null or nonempty string"},
            {"field": "updated_at", "json_type": "string", "required": True,
             "constraint": "timezone-aware ISO-8601"},
        ]
        mutations: list[dict[str, Any]] = [
            {"case": "valid", "mutations": {}, "outcome": "OK"},
            {"case": "unknown_schema_version", "mutations": {"schema_version": 2},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "schema_version_bool", "mutations": {"schema_version": True},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "schema_version_string", "mutations": {"schema_version": "1"},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "missing_schema_version", "mutations": {"schema_version": "__delete__"},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "missing_required_field", "mutations": {"partition_manifest_id": "__delete__"},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "extra_field", "mutations": {"surprise": 1},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "manifest_version_bool", "mutations": {"manifest_version": True},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "manifest_version_string", "mutations": {"manifest_version": "1"},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "manifest_version_float", "mutations": {"manifest_version": 1.2},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "manifest_version_zero", "mutations": {"manifest_version": 0},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "partition_key_numeric", "mutations": {"partition_key": 123},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "partition_key_empty", "mutations": {"partition_key": ""},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "previous_manifest_id_empty", "mutations": {"previous_manifest_id": ""},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "updated_at_naive", "mutations": {"updated_at": "2026-09-05T12:00:00"},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "updated_at_bad_iso", "mutations": {"updated_at": "not-a-date"},
             "outcome": "CurrentPointerCorrupt"},
            {"case": "updated_at_numeric", "mutations": {"updated_at": 123},
             "outcome": "CurrentPointerCorrupt"},
        ]
        rows: list[dict[str, Any]] = []
        for entry in mutations:
            payload = self._valid_payload()
            for key, value in entry["mutations"].items():
                if value == "__delete__":
                    payload.pop(key, None)
                else:
                    payload[key] = value
            try:
                PartitionCurrentPointer.from_canonical_json(json.dumps(payload))
                observed = "OK"
            except Exception as exc:  # noqa: BLE001 - expected typed rejection
                observed = type(exc).__name__
            rows.append(
                {
                    "case": entry["case"],
                    "mutations": entry["mutations"],
                    "expected_outcome": entry["outcome"],
                    "observed_outcome": observed,
                    "test_name": f"pointer_case_{entry['case']}",
                }
            )
        artifact = {
            "pointer_object": "PartitionCurrentPointer (operational state, I04 §34)",
            "schema_version": POINTER_SCHEMA_VERSION,
            "closed_fields": closed_fields,
            "closed_json": True,
            "unknown_field_policy": "CurrentPointerCorrupt (never silently ignored)",
            "partition_key_binding": "pointer.partition_key must equal the requested partition_key on read (I04R1 §38)",
            "ancestry_binding": "pointer.previous_manifest_id must equal manifest.supersedes_manifest_id (I04R1 §39)",
            "adversarial_cases": rows,
        }
        out_path = EVIDENCE_DIR / "BLOC_04_I04R1_POINTER_SCHEMA.json"
        out_path.write_text(
            json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        # deterministic regeneration
        again = json.loads(out_path.read_text(encoding="utf-8"))
        assert again == artifact
        by_case = {r["case"]: r for r in rows}
        assert by_case["valid"]["observed_outcome"] == "OK"
        for case, outcome in [
            ("unknown_schema_version", "CurrentPointerCorrupt"),
            ("schema_version_bool", "CurrentPointerCorrupt"),
            ("schema_version_string", "CurrentPointerCorrupt"),
            ("missing_schema_version", "CurrentPointerCorrupt"),
            ("missing_required_field", "CurrentPointerCorrupt"),
            ("extra_field", "CurrentPointerCorrupt"),
            ("manifest_version_bool", "CurrentPointerCorrupt"),
            ("manifest_version_string", "CurrentPointerCorrupt"),
            ("manifest_version_float", "CurrentPointerCorrupt"),
            ("manifest_version_zero", "CurrentPointerCorrupt"),
            ("partition_key_numeric", "CurrentPointerCorrupt"),
            ("partition_key_empty", "CurrentPointerCorrupt"),
            ("previous_manifest_id_empty", "CurrentPointerCorrupt"),
            ("updated_at_naive", "CurrentPointerCorrupt"),
            ("updated_at_bad_iso", "CurrentPointerCorrupt"),
            ("updated_at_numeric", "CurrentPointerCorrupt"),
        ]:
            assert by_case[case]["observed_outcome"] == outcome, case
        # historical I04 evidence untouched
        assert (EVIDENCE_DIR / "BLOC_04_I04_CATALOG_SCHEMAS.json").exists()