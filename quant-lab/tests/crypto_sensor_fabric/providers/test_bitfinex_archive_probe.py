"""Bitfinex community liquidation archive probe tests (bloc_02/02 §12, 04 §7).

All offline: fixtures only.  Focus: archive-as-source characterization —
license/checksum classification, liquidation row semantics inspection, archive
hole detection (404 -> F_ARCHIVE_NOT_FOUND, never a zero), and the
COMMUNITY_ARCHIVE evidence class that must never masquerade as first-party
venue truth.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.probes.enums import (
    AccessMode,
    EvidenceSourceClass,
    Granularity,
    ProbeFailureClass,
    QueryMode,
    ResponseStatusClass,
)
from crypto_sensor_fabric.probes.models import CapabilityProbeRequest
from crypto_sensor_fabric.providers.bitfinex_archive import (
    PROVIDER_ID,
    BitfinexArchiveCapabilityProbe,
)

FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "probe_payloads"
    / "bitfinex_archive"
)

PROBE = BitfinexArchiveCapabilityProbe()


def _sample(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _request(*, era: str = "2022", instrument: str = "BTCUSD", asset: str = "BTC") -> CapabilityProbeRequest:
    return CapabilityProbeRequest.model_validate(
        {
            "provider_id": PROVIDER_ID,
            "sensor_family": SensorFamily.MECHANICAL_LIQUIDATION,
            "venue_market": "BITFINEX",
            "instrument_native": instrument,
            "canonical_asset_hint": asset,
            "requested_start": datetime(2022, 6, 15, tzinfo=UTC),
            "requested_end": datetime(2022, 6, 16, tzinfo=UTC),
            "requested_granularity": Granularity.G1D,
            "access_mode": AccessMode.COMMUNITY_ARCHIVE,
            "query_mode": QueryMode.DOWNLOAD_FILE,
            "probe_run_id": "run_bitfinex_001",
            "provider_hints": {"era": era},
        }
    )


# ---------------------------------------------------------------------------
# identity + evidence class
# ---------------------------------------------------------------------------


def test_identity_and_evidence_class():
    assert PROBE.provider_id == "BITFINEX_COMMUNITY_ARCHIVE"
    assert PROBE.evidence_class is EvidenceSourceClass.COMMUNITY_ARCHIVE
    assert PROBE.access_mode is AccessMode.COMMUNITY_ARCHIVE
    assert PROBE.probe_version == "bitfinex-archive-v1"


def test_archive_base_unverified_by_default():
    # the module must NOT claim a reachable archive before a live probe
    assert "example.invalid" in PROBE.archive_base_url


# ---------------------------------------------------------------------------
# deterministic URLs
# ---------------------------------------------------------------------------


def test_deterministic_archive_urls():
    assert PROBE.daily_file_url("2022-06-15") == (
        f"{PROBE.archive_base_url}/liquidations/2022-06-15.csv"
    )
    assert PROBE.checksums_url().endswith("/checksums.txt")
    assert PROBE.license_url().endswith("/LICENSE")
    assert PROBE.methodology_url().endswith("/README.md")


# ---------------------------------------------------------------------------
# schema / semantics inspection
# ---------------------------------------------------------------------------


def test_inspect_liquidation_schema_preserves_semantics():
    summary = PROBE.inspect_liquidation_schema(_sample("liquidations_sample_success.json"))
    assert "side" in summary["observed_columns"]
    assert "timestamp" in summary["observed_columns"]
    assert "amount" in summary["observed_columns"]
    assert "spot/margin/perpetual" in summary["semantics"]


def test_inspect_liquidation_schema_empty():
    summary = PROBE.inspect_liquidation_schema([])
    assert summary["semantics"] == "EMPTY_SAMPLE"


def test_inspect_liquidation_schema_flag_missing_side():
    summary = PROBE.inspect_liquidation_schema(_sample("liquidations_sample_schema_changed.json"))
    assert "no side column" in summary["semantics"]


# ---------------------------------------------------------------------------
# file characterization
# ---------------------------------------------------------------------------


def test_characterize_success_sample():
    attempt = PROBE.characterize_daily_file(
        _request(),
        date="2022-06-15",
        file_status=200,
        checksum_status="verified",
        license_status="verified",
        methodology_status="verified",
        checksum_line=None,
        sample_rows=_sample("liquidations_sample_success.json"),
    )
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.rows_returned == 3
    assert attempt.first_timestamp_returned is not None
    assert attempt.last_timestamp_returned is not None
    assert attempt.sensor_family is SensorFamily.MECHANICAL_LIQUIDATION
    assert attempt.venue_market == "BITFINEX"
    assert attempt.error_class is None


def test_characterize_success_sample_has_schema_fingerprint():
    attempt = PROBE.characterize_daily_file(
        _request(),
        date="2022-06-15",
        file_status=200,
        sample_rows=_sample("liquidations_sample_success.json"),
    )
    assert attempt.payload_schema_fingerprint
    assert "timestamp" in attempt.native_timestamp_fields
    assert PROBE.evidence_class.value in attempt.rate_limit_metadata["evidence_class"]
    assert attempt.rate_limit_metadata["archive_base_url_status"] == "UNVERIFIED"


def test_characterize_empty_sample():
    attempt = PROBE.characterize_daily_file(
        _request(),
        date="2022-06-15",
        file_status=200,
        sample_rows=_sample("liquidations_sample_empty.json"),
    )
    assert attempt.rows_returned == 0
    assert attempt.first_timestamp_returned is None


def test_characterize_archive_hole_is_not_zero():
    attempt = PROBE.characterize_daily_file(_request(), date="2022-06-17", file_status=404)
    assert attempt.response_status_class is ResponseStatusClass.FAILED
    assert attempt.error_class is ProbeFailureClass.F_ARCHIVE_NOT_FOUND
    assert attempt.error_detail_redacted


def test_characterize_server_error():
    attempt = PROBE.characterize_daily_file(_request(), date="2022-06-15", file_status=503)
    assert attempt.error_class is ProbeFailureClass.F_SERVER_5XX


def test_characterize_rate_limit():
    attempt = PROBE.characterize_daily_file(_request(), date="2022-06-15", file_status=429)
    assert attempt.error_class is ProbeFailureClass.F_ACCESS_RATE_LIMIT


@pytest.mark.parametrize("status", [401, 403])
def test_characterize_auth(status):
    attempt = PROBE.characterize_daily_file(_request(), date="2022-06-15", file_status=status)
    assert attempt.error_class is ProbeFailureClass.F_ACCESS_AUTH


def test_characterize_unknown_status():
    attempt = PROBE.characterize_daily_file(_request(), date="2022-06-15", file_status=418)
    assert attempt.error_class is ProbeFailureClass.F_UNKNOWN


def test_failed_attempt_carries_error_class():
    attempt = PROBE.characterize_daily_file(_request(), date="2022-06-15", file_status=404)
    # model invariant enforces this at construction (T2-MODEL-05)
    assert attempt.error_class is not None


# ---------------------------------------------------------------------------
# license + checksum classification
# ---------------------------------------------------------------------------


def test_classify_license_mit():
    text = (FIXTURES / "license_mit.txt").read_text(encoding="utf-8")
    assert PROBE.classify_license(text) == "MIT"


def test_classify_license_unrecognized():
    text = (FIXTURES / "license_unrecognized.txt").read_text(encoding="utf-8")
    assert PROBE.classify_license(text) == "UNRECOGNIZED"


def test_classify_license_apache_and_cc():
    assert PROBE.classify_license("Apache License") == "Apache-2.0"
    assert PROBE.classify_license("Creative Commons") == "CC-BY-* (check)"


def test_parse_checksums_manifest():
    text = (FIXTURES / "checksums_manifest.txt").read_text(encoding="utf-8")
    entries = PROBE.parse_checksums(text)
    assert len(entries) == 2
    assert entries[0]["hash"].startswith("9f86d081")
    assert entries[0]["file"].endswith("2022-06-15.csv")