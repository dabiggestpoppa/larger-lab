"""Bitfinex community GitHub/LFS DuckDB source probe tests (bloc_02/02 §12, 04 §7).

All offline: fixtures only.  The real source is the public GitHub replication
repository tradingstrategy-ai/bitfinex-liquidations distributed as a single
Git-LFS DuckDB dump — NOT a daily CSV tree, NOT a Bitfinex first-party archive,
and there is NO upstream `checksums.txt` to assume.

Tests enforce (I11R1 requirements A-J):

A. evidence class stays COMMUNITY_ARCHIVE
B. never silently promoted to a first-party exchange class
C. never defaults to EXACT_EQUIVALENT
D. mixed spot/margin + perpetual semantics stay explicit (never whole-db PERPETUAL_LIQUIDATIONS)
E. LFS pointer parser extracts oid algorithm / digest / size
F. malformed LFS pointer fails closed
G. changed LFS OID is detectable as a source revision
H. no daily-CSV path assumption remains
I. no fictional checksums.txt assumption remains
J. no large network download exists in unit tests (dump fixture is the LFS pointer text)
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

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
    DUMP_RELATIVE_PATH,
    DUMP_STORAGE,
    PROVIDER_ID,
    REPOSITORY_NAME,
    REPOSITORY_OWNER,
    BitfinexArchiveCapabilityProbe,
    parse_lfs_pointer,
)

FIXTURES = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "probe_payloads"
    / "bitfinex_archive"
)
PROBE_SOURCE = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "crypto_sensor_fabric"
    / "providers"
    / "bitfinex_archive"
    / "probe.py"
).read_text(encoding="utf-8")

PROBE = BitfinexArchiveCapabilityProbe()

FIRST_PARTY_CLASSES = {
    EvidenceSourceClass.FIRST_PARTY_RUNTIME,
    EvidenceSourceClass.FIRST_PARTY_ARCHIVE,
    EvidenceSourceClass.FIRST_PARTY_DOCUMENTATION,
}


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _request(*, era: str = "RECENT_CONTROL", instrument: str = "tBTCF0:USTF0", asset: str = "BTC") -> CapabilityProbeRequest:
    return CapabilityProbeRequest.model_validate(
        {
            "provider_id": PROVIDER_ID,
            "sensor_family": SensorFamily.MECHANICAL_LIQUIDATION,
            "venue_market": "BITFINEX",
            "instrument_native": instrument,
            "canonical_asset_hint": asset,
            "requested_start": datetime(2024, 6, 1, tzinfo=UTC),
            "requested_end": datetime(2024, 6, 2, tzinfo=UTC),
            "requested_granularity": Granularity.G1D,
            "access_mode": AccessMode.COMMUNITY_ARCHIVE,
            "query_mode": QueryMode.DOWNLOAD_FILE,
            "probe_run_id": "run_bitfinex_001",
            "provider_hints": {"era": era},
        }
    )


def _success_attempt():
    return PROBE.characterize_repository(
        _request(),
        repo_status=200,
        license_text=_read("license_mit.txt"),
        readme_text=_read("README_sample.md"),
        gitattributes_text=_read("gitattributes_sample.txt"),
        lfs_pointer_text=_read("lfs_pointer_valid.txt"),
        upstream_commit="abc1234",
    )


# ---------------------------------------------------------------------------
# A/B/C — evidence class and promotion discipline
# ---------------------------------------------------------------------------


def test_source_identity_points_at_real_repo():
    assert PROVIDER_ID == "BITFINEX_COMMUNITY_ARCHIVE"
    assert PROBE.repository_url().endswith("tradingstrategy-ai/bitfinex-liquidations")
    assert REPOSITORY_OWNER == "tradingstrategy-ai"
    assert REPOSITORY_NAME == "bitfinex-liquidations"


def test_evidence_class_stays_community_archive():  # A
    assert PROBE.evidence_class is EvidenceSourceClass.COMMUNITY_ARCHIVE
    assert PROBE.access_mode is AccessMode.COMMUNITY_ARCHIVE


def test_never_first_party_exchange():  # B
    assert PROBE.evidence_class not in FIRST_PARTY_CLASSES
    # the module source never reassigns to a first-party class
    assert "FIRST_PARTY_RUNTIME" not in PROBE_SOURCE
    assert "FIRST_PARTY_ARCHIVE" not in PROBE_SOURCE


def test_never_exact_equivalent_default():  # C
    # the module declares on its face that it is never EXACT_EQUIVALENT and
    # never assigns any equivalence verdict during characterization
    assert "never EXACT_EQUIVALENT" in PROBE_SOURCE
    assert "semantic_equivalence" not in PROBE_SOURCE
    # attempt-level evidence maintains corroboration semantics: success is a
    # VERIFIED_SAMPLE of the source, never an equivalence verdict
    attempt = _success_attempt()
    assert attempt.rate_limit_metadata["evidence_class"] == "COMMUNITY_ARCHIVE"


# ---------------------------------------------------------------------------
# D — mixed market-type semantics stay explicit
# ---------------------------------------------------------------------------


def test_mixed_market_types_explicit():  # D
    attempt = _success_attempt()
    summary = attempt.native_units_summary
    assert "spot/margin" in summary["market_types"]
    assert "perpetual" in summary["market_types"]
    # the market-type description is an explicit mixed (spot/margin + perpetual)
    # characterization, never a whole-database perpetual-only label
    assert summary["market_types"] != "PERPETUAL_LIQUIDATIONS"


# ---------------------------------------------------------------------------
# E/F/G — LFS pointer and source revision
# ---------------------------------------------------------------------------


def test_parse_lfs_pointer_extracts_fields():  # E
    parsed = parse_lfs_pointer(_read("lfs_pointer_valid.txt"))
    assert parsed is not None
    assert parsed["oid_algorithm"] == "sha256"
    assert parsed["oid_digest"].startswith("90b5d550")
    assert parsed["oid_digest"] == "90b5d550df057fde1b5a66b5ae9b3de256814ce347bdc5ccc05c7bb9f74e2989"
    assert parsed["size"] == 355217408
    assert parsed["version"].startswith("https://git-lfs.github.com")


def test_malformed_lfs_pointer_fails_closed():  # F
    assert parse_lfs_pointer(_read("lfs_pointer_malformed.txt")) is None
    assert parse_lfs_pointer(None) is None
    assert parse_lfs_pointer("") is None
    assert parse_lfs_pointer("not an lfs file") is None


def test_changed_oid_detected_as_source_revision():  # G
    assert PROBE.lfs_oid_changed(_read("lfs_pointer_valid.txt")) is False
    assert PROBE.lfs_oid_changed(_read("lfs_pointer_changed.txt")) is True
    # a new revision identity tuple exposes the change explicitly
    rev = PROBE.source_revision(
        upstream_commit="def5678",
        lfs_pointer_text=_read("lfs_pointer_changed.txt"),
    )
    assert rev["lfs_oid"] != "90b5d550df057fde1b5a66b5ae9b3de256814ce347bdc5ccc05c7bb9f74e2989"
    assert rev["lfs_declared_size"] == 360000000
    assert rev["source_revision_id"] == rev["lfs_oid"]


# ---------------------------------------------------------------------------
# H/I — no daily-CSV or checksum-manifest assumptions
# ---------------------------------------------------------------------------


def test_dump_is_single_artifact_not_daily_tree():  # H
    assert DUMP_RELATIVE_PATH == "bitfinex_liquidations.duckdb"
    assert DUMP_STORAGE == "GIT_LFS"
    assert PROBE.dump_pointer_url().endswith("/bitfinex_liquidations.duckdb")


def test_no_daily_csv_assumption_remains():  # H
    assert "example.invalid" not in PROBE_SOURCE
    assert "liquidations/{YYYY-MM-DD}.csv" not in PROBE_SOURCE
    assert "daily_file_url" not in PROBE_SOURCE


def test_no_fictional_checksum_manifest():  # I
    # no checksum-manifest machinery exists (the docstring only notes its absence)
    assert "checksums_url" not in PROBE_SOURCE
    assert "parse_checksums" not in PROBE_SOURCE
    assert "def checksum" not in PROBE_SOURCE


# ---------------------------------------------------------------------------
# J — offline / no large download
# ---------------------------------------------------------------------------


def test_no_large_download_in_unit_tests():  # J
    attempt = _success_attempt()
    assert attempt.rate_limit_metadata["dump_acquired"] is False
    assert attempt.rate_limit_metadata["dump_downloaded"] is False
    # fixtures never reference the multi-hundred-MB binary
    assert "355217408" in _read("lfs_pointer_valid.txt")  # declared size, not bytes
    # every fixture is a small text file (no .duckdb binary checked in)
    bin_fixtures = [p.name for p in FIXTURES.iterdir() if p.suffix == ".duckdb"]
    assert bin_fixtures == []


# ---------------------------------------------------------------------------
# repository / dump characterization
# ---------------------------------------------------------------------------


def test_repository_characterization_success():
    attempt = _success_attempt()
    assert attempt.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    assert attempt.error_class is None
    assert attempt.sensor_family is SensorFamily.MECHANICAL_LIQUIDATION
    md = attempt.rate_limit_metadata
    assert md["repo_present"] is True
    assert md["license_status"] == "MIT"
    assert md["readme_methodology_status"] == "present"
    assert md["gitattributes_present"] is True
    assert md["lfs_status"] == "present"
    assert md["lfs_oid"].startswith("90b5d550")
    assert md["lfs_declared_size"] == 355217408
    assert md["upstream_commit"] == "abc1234"


def test_repository_not_found():
    attempt = PROBE.characterize_repository(_request(), repo_status=404)
    assert attempt.response_status_class is ResponseStatusClass.FAILED
    assert attempt.error_class is ProbeFailureClass.F_ARCHIVE_NOT_FOUND


def test_dump_pointer_absent():
    attempt = PROBE.characterize_repository(
        _request(),
        repo_status=200,
        license_text=_read("license_mit.txt"),
        readme_text=_read("README_sample.md"),
        lfs_pointer_text=None,
    )
    assert attempt.error_class is ProbeFailureClass.F_ARCHIVE_NOT_FOUND


def test_malformed_pointer_characterized_corrupt():
    attempt = PROBE.characterize_repository(
        _request(),
        repo_status=200,
        license_text=_read("license_mit.txt"),
        readme_text=_read("README_sample.md"),
        lfs_pointer_text=_read("lfs_pointer_malformed.txt"),
    )
    assert attempt.error_class is ProbeFailureClass.F_PAYLOAD_CORRUPT


def test_license_missing_blocks():
    attempt = PROBE.characterize_repository(
        _request(),
        repo_status=200,
        readme_text=_read("README_sample.md"),
        lfs_pointer_text=_read("lfs_pointer_valid.txt"),
        license_status_override="missing",
    )
    assert attempt.error_class is ProbeFailureClass.F_REQUIRED_ARTIFACT_MISSING


def test_license_unrecognized_blocks():
    attempt = PROBE.characterize_repository(
        _request(),
        repo_status=200,
        license_text=_read("license_unrecognized.txt"),
        readme_text=_read("README_sample.md"),
        lfs_pointer_text=_read("lfs_pointer_valid.txt"),
    )
    assert attempt.error_class is ProbeFailureClass.F_REQUIRED_ARTIFACT_MISSING


def test_methodology_missing_blocks():
    attempt = PROBE.characterize_repository(
        _request(),
        repo_status=200,
        license_text=_read("license_mit.txt"),
        readme_text="",
        lfs_pointer_text=_read("lfs_pointer_valid.txt"),
    )
    assert attempt.error_class is ProbeFailureClass.F_REQUIRED_ARTIFACT_MISSING


# ---------------------------------------------------------------------------
# license classification
# ---------------------------------------------------------------------------


def test_classify_license_mit():
    assert PROBE.classify_license(_read("license_mit.txt")) == "MIT"


def test_classify_license_unrecognized_and_missing():
    assert PROBE.classify_license(_read("license_unrecognized.txt")) == "UNRECOGNIZED"
    assert PROBE.classify_license(None) == "MISSING"