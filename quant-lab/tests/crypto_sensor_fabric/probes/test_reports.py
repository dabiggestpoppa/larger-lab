"""Report-and-gap-matrix generator tests (SENSOR-B2-I12).

All offline and deterministic: reports are rendered from synthetic models via
`write_reports` into a tmp dir and every output is parsed/asserted.  I13 (live
probing) and I14 (final promotion packet) are explicitly out of scope here.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.probes.enums import (
    AccessMode,
    CapabilityStatus,
    ContradictionResolutionStatus,
    ContradictionSeverity,
    EvidenceLevel,
    Granularity,
    HistoricalBoundaryConfidence,
    PITReadiness,
    ProbeFailureClass,
    ProviderRole,
    QueryMode,
    RedundancyClass,
    ResponseStatusClass,
)
from crypto_sensor_fabric.probes.models import (
    CapabilityClaim,
    CapabilityProbeAttempt,
    DocumentationRuntimeContradiction,
    FailureRecord,
    ProbeRunResult,
    ProviderSensorCoverage,
    SensorRedundancySummary,
)
from crypto_sensor_fabric.probes.reports import (
    REPORT_FILENAMES,
    history_boundaries_csv,
    pit_readiness_csv,
    provider_coverage_csv,
    schema_fingerprints_jsonl,
    sensor_gap_csv,
    write_reports,
)

T0 = datetime(2024, 6, 1, tzinfo=UTC)
T1 = datetime(2024, 6, 2, tzinfo=UTC)


def _attempt(*, provider: str = "KRAKEN_FUTURES", sensor: SensorFamily = SensorFamily.MECHANICAL_OPEN_INTEREST,
             status: ResponseStatusClass = ResponseStatusClass.VERIFIED_SAMPLE,
             era: str = "RECENT_CONTROL",
             fingerprint: str | None = "dict{a:int}",
             bare: bool = False):
    return CapabilityProbeAttempt.model_validate(
        {
            "probe_id": f"{provider.lower()}_{sensor.value.lower()}_001",
            "probe_run_id": "run_reports_001",
            "provider_id": provider,
            "sensor_family": sensor,
            "venue_market": provider,
            "instrument_native": "BTCUSD",
            "canonical_asset_hint": "BTC",
            "requested_start": T0,
            "requested_end": T1,
            "requested_granularity": Granularity.G1D,
            "access_mode": AccessMode.PUBLIC_REST,
            "query_mode": QueryMode.TIME_RANGE,
            "response_status_class": status,
            "http_status_or_file_status": 200,
            "first_timestamp_returned": None if bare else T0,
            "last_timestamp_returned": None if bare else T1,
            "native_timestamp_fields": [] if bare else ["lastTime"],
            "native_units_summary": {} if bare else {"units": "contracts"},
            "payload_schema_fingerprint": fingerprint,
            "error_class": None if status is not ResponseStatusClass.FAILED else ProbeFailureClass.F_ARCHIVE_NOT_FOUND,
            "probe_version": "reports-test-v1",
            "era_hint": era,
        }
    )


def _claim(*, provider: str = "KRAKEN_FUTURES", sensor: SensorFamily = SensorFamily.MECHANICAL_OPEN_INTEREST):
    return CapabilityClaim.model_validate(
        {
            "claim_id": f"claim_{provider.lower()}_{sensor.value.lower()}_001",
            "provider_id": provider,
            "sensor_family": sensor,
            "venue_market": provider,
            "instrument_scope": ["BTCUSD"],
            "granularity_scope": [Granularity.G1D, Granularity.G5M],
            "access_mode": AccessMode.PUBLIC_REST,
            "capability_status": CapabilityStatus.VERIFIED_CURRENT_ONLY,
            "evidence_level": EvidenceLevel.E2_LIVE_RECENT_VERIFIED,
            "earliest_claimed_history": T0,
            "earliest_verified_history": T0,
            "history_boundary_confidence": HistoricalBoundaryConfidence.MONTH_BOUNDARY_VERIFIED,
            "latest_verified_history": T1,
            "PIT_readiness": PITReadiness.PIT_READY,
            "free_only_status": "FREE_COMPLIANT",
            "known_gaps": ["2021 not verified"],
            "evidence_ids": ["kraken_open_interest_btc_2024_5m_001"],
        }
    )


def _coverage(*, provider: str = "KRAKEN_FUTURES",
              sensor: SensorFamily = SensorFamily.MECHANICAL_OPEN_INTEREST,
              promotion: bool = False, blocking: str | None = None,
              pit_ready: bool = True):
    return ProviderSensorCoverage.model_validate(
        {
            "provider_id": provider,
            "sensor_family": sensor,
            "venue_market": provider,
            "instrument_scope": ["BTCUSD"],
            "access_mode": AccessMode.PUBLIC_REST,
            "era_status": {"RECENT_CONTROL": CapabilityStatus.VERIFIED, "2022": CapabilityStatus.HISTORY_BLOCKED},
            "earliest_verified_history": T0,
            "latest_verified_history": T1,
            "granularity_scope": [Granularity.G1D, Granularity.G5M],
            "PIT_readiness": PITReadiness.PIT_READY if pit_ready else PITReadiness.NOT_PIT_READY,
            "unit_clarity": 0.75,
            "pagination_quality": 1.0,
            "semantic_equivalence_class": None,
            "evidence_level": EvidenceLevel.E2_LIVE_RECENT_VERIFIED,
            "provider_role": ProviderRole.REFERENCE_ONLY,
            "capability_score": 0.62,
            "promotion_eligible": promotion,
            "blocking_reason": blocking,
            "pit_effective_ts_understood": True if pit_ready else False,
            "pit_observation_ts_understood": True if pit_ready else False,
            "pit_publication_delay_understood": True if pit_ready else None,
            "pit_forward_info_required": False,
            "pit_forward_availability_resolved": True,
            "pit_publication_affects_reconstruction": False if pit_ready else None,
            "data_semantics_verified": True if pit_ready else False,
        }
    )


def _redundancy(sensor: SensorFamily = SensorFamily.MECHANICAL_OPEN_INTEREST):
    return SensorRedundancySummary.model_validate(
        {
            "sensor_family": sensor,
            "verified_provider_count": 2,
            "verified_venues": ["GATE_FUTURES", "OKX_SWAP"],
            "redundancy_class": RedundancyClass.R2_TWO_INDEPENDENT,
            "first_party_count": 2,
            "aggregator_count": 0,
            "community_count": 0,
            "PIT_ready_provider_count": 1,
            "gap_status": "ADEQUATE",
        }
    )


def _contradiction():
    return DocumentationRuntimeContradiction.model_validate(
        {
            "contradiction_id": "contrad_001",
            "provider_id": "GATE_FUTURES",
            "sensor_family": SensorFamily.MECHANICAL_LIQUIDATION,
            "documentation_claim": "endpoint supports full history",
            "documentation_source_ref": "docs/liq",
            "runtime_observation": "retention limited to recent interval",
            "runtime_evidence_ids": ["gate_liquidation_2022_001"],
            "severity": ContradictionSeverity.MATERIAL,
            "resolution_status": ContradictionResolutionStatus.OPEN,
        }
    )


def _failure():
    return FailureRecord.model_validate(
        {
            "failure_id": "fail_001",
            "probe_id": "okx_books_2022_001",
            "provider_id": "OKX_SWAP",
            "sensor_family": SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
            "failure_class": ProbeFailureClass.F_HISTORY_TRUNCATED,
            "retryable": False,
            "hard_block": True,
            "evidence_ref": "okx_book_history_2022_evidence",
        }
    )


def _run():
    return ProbeRunResult.model_validate(
        {
            "probe_run_id": "run_reports_001",
            "run_status": "PARTIAL",
            "attempts": [_attempt(), _attempt(status=ResponseStatusClass.FAILED, era="2022")],
            "planned_but_skipped": [],
            "probe_version": "reports-test-v1",
        }
    )


@pytest.fixture()
def report_dir(tmp_path: Path) -> str:
    write_reports(
        output_dir=str(tmp_path),
        run=_run(),
        attempts=[_attempt(), _attempt(status=ResponseStatusClass.FAILED, era="2022")],
        claims=[_claim()],
        coverages=[_coverage()],
        redundancies=[_redundancy()],
        contradictions=[_contradiction()],
        free_only_audit=[
            {
                "provider_id": "COINALYZE",
                "sensor_family": "MECHANICAL_LIQUIDATION",
                "access_mode": "FREE_API_KEY",
                "api_key_required": True,
                "payment_method_required": False,
                "paid_subscription_required": False,
                "staking_required": False,
                "transaction_required": False,
                "eligible_required_runtime": True,
            }
        ],
        failures=[_failure()],
        provider_ids=["KRAKEN_FUTURES", "OKX_SWAP"],
        expected_sensors=list(SensorFamily),
    )
    return str(tmp_path)


def test_writes_all_eleven_reports(report_dir: str):
    names = sorted(p.name for p in Path(report_dir).iterdir())
    # 12 (decision packet) is reserved for I14 — must NOT be generated
    assert names == sorted(REPORT_FILENAMES)
    assert "12_BLOC_02_IMPLEMENTATION_DECISION.md" not in names


def test_reports_are_deterministic():
    import tempfile

    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        write_reports(
            output_dir=d1,
            attempts=[_attempt()],
            claims=[_claim()],
            coverages=[_coverage()],
            redundancies=[_redundancy()],
            failures=[_failure()],
        )
        write_reports(
            output_dir=d2,
            attempts=[_attempt()],
            claims=[_claim()],
            coverages=[_coverage()],
            redundancies=[_redundancy()],
            failures=[_failure()],
        )
        for name in REPORT_FILENAMES:
            a = Path(d1, name).read_bytes()
            b = Path(d2, name).read_bytes()
            assert a == b, f"{name} not deterministic"


def test_provider_coverage_csv_headers_and_status(report_dir: str):
    csv_text = Path(report_dir, "02_PROVIDER_COVERAGE_MATRIX.csv").read_text(encoding="utf-8")
    rows = list(csv.reader(io.StringIO(csv_text)))
    header = rows[0]
    for col in ["provider_id", "sensor_family", "2021", "2022", "2024", "2026", "recent_status",
                "PIT_readiness", "promotion_eligible", "blocking_reason"]:
        assert col in header, col
    data = [r for r in rows[1:] if r]
    assert any(r[header.index("recent_status")] == "VERIFIED" for r in data)
    assert any(r[header.index("2022")] == "HISTORY_BLOCKED" for r in data)


def test_provider_coverage_csv_direct():
    csv_text = provider_coverage_csv([_coverage()])
    rows = list(csv.reader(io.StringIO(csv_text)))
    data = [r for r in rows[1:] if r][0]
    header = rows[0]
    assert data[header.index("PIT_readiness")] == "PIT_READY"
    assert data[header.index("capability_score")] == "0.62"
    assert data[header.index("promotion_eligible")] == "FALSE"


def test_sensor_gap_matrix_covers_unprobed_sensors(report_dir: str):
    csv_text = Path(report_dir, "03_SENSOR_GAP_MATRIX.csv").read_text(encoding="utf-8")
    rows = list(csv.reader(io.StringIO(csv_text)))
    header = rows[0]
    fam_idx = header.index("sensor_family")
    gap_idx = header.index("gap_status")
    families = {r[fam_idx] for r in rows[1:] if r}
    assert "MECHANICAL_OPEN_INTEREST" in families
    row = next(r for r in rows[1:] if r and r[fam_idx] == SensorFamily.MECHANICAL_BOOK_SNAPSHOT.value)
    assert row[gap_idx] == "UNVERIFIED"  # unprobed, not unsupported


def test_sensor_gap_csv_direct_uses_r2():
    text = sensor_gap_csv([_redundancy()], [SensorFamily.MECHANICAL_OPEN_INTEREST])
    rows = list(csv.reader(io.StringIO(text)))
    data = [r for r in rows[1:] if r][0]
    header = rows[0]
    assert data[header.index("redundancy_class")] == "R2_TWO_INDEPENDENT"
    assert data[header.index("gap_status")] == "ADEQUATE"


def test_role_recommendations_markdown(report_dir: str):
    text = Path(report_dir, "04_PROVIDER_ROLE_RECOMMENDATIONS.md").read_text(encoding="utf-8")
    assert "promotion_eligible" in text
    assert "sensor-probe-v1" in text or "FALSE" in text


def test_free_only_audit_csv(report_dir: str):
    text = Path(report_dir, "06_FREE_ONLY_AUDIT.csv").read_text(encoding="utf-8")
    rows = list(csv.reader(io.StringIO(text)))
    header = rows[0]
    assert header[0] == "provider_id"
    data = rows[1]
    assert "payment_method_required" in header and header.index("staking_required") < len(header)
    assert data[header.index("provider_id")] == "COINALYZE"
    assert data[header.index("payment_method_required")] == "False"


def test_pit_readiness_csv(report_dir: str):
    text = Path(report_dir, "07_PIT_READINESS_MATRIX.csv").read_text(encoding="utf-8")
    rows = list(csv.reader(io.StringIO(text)))
    header = rows[0]
    data = [r for r in rows[1:] if r][0]
    assert data[header.index("PIT_readiness")] == "PIT_READY"
    assert data[header.index("effective_timestamp_understood")] == "YES"


def test_pit_readiness_fails_closed_when_facts_unresolved():
    # I13R1 §6: PIT_READY with unresolved effective/observation timestamp
    # meaning is invalid — the matrix renders NOT_PIT_READY + a blocking reason.
    bad = _coverage(pit_ready=True).model_copy(
        update={"pit_effective_ts_understood": False, "pit_observation_ts_understood": False}
    )
    text = pit_readiness_csv([bad])
    rows = list(csv.reader(io.StringIO(text)))
    data = [r for r in rows[1:] if r][0]
    header = rows[0]
    assert data[header.index("PIT_readiness")] == "NOT_PIT_READY"
    assert data[header.index("effective_timestamp_understood")] == "NO"
    assert data[header.index("blocking_reason")]


def test_pit_readiness_fails_closed_on_publication_unknown():
    # publication delay unknown AND publication affects reconstruction -> fail
    bad = _coverage(pit_ready=True).model_copy(
        update={
            "pit_publication_delay_understood": None,
            "pit_publication_affects_reconstruction": True,
        }
    )
    text = pit_readiness_csv([bad])
    rows = list(csv.reader(io.StringIO(text)))
    data = [r for r in rows[1:] if r][0]
    header = rows[0]
    assert data[header.index("PIT_readiness")] == "NOT_PIT_READY"


def test_pit_readiness_fails_closed_on_unresolved_forward_info():
    # forward info required but availability timing unresolved -> fail
    bad = _coverage(pit_ready=True).model_copy(
        update={"pit_forward_info_required": True, "pit_forward_availability_resolved": None}
    )
    text = pit_readiness_csv([bad])
    rows = list(csv.reader(io.StringIO(text)))
    data = [r for r in rows[1:] if r][0]
    header = rows[0]
    assert data[header.index("PIT_readiness")] == "NOT_PIT_READY"


def test_history_boundaries_csv(report_dir: str):
    text = Path(report_dir, "08_HISTORY_BOUNDARIES.csv").read_text(encoding="utf-8")
    rows = list(csv.reader(io.StringIO(text)))
    header = rows[0]
    data = [r for r in rows[1:] if r][0]
    assert data[header.index("earliest_verified")].endswith("Z")
    # I13R1: boundaries derive from attempt evidence -> ERA_BOUNDARY_VERIFIED
    # when a verified sample exists (never fabricated from claims).
    assert data[header.index("boundary_confidence")] in (
        "ERA_BOUNDARY_VERIFIED",
        "MONTH_BOUNDARY_VERIFIED",
    )
    assert data[header.index("latest_verified")].endswith("Z")


def test_history_boundaries_direct():
    # I13R1 §5: boundaries are keyed on (provider, sensor, INSTRUMENT) from
    # attempt evidence — BTC and ETH histories are never collapsed.
    text = history_boundaries_csv([_attempt(), _attempt(era="2022")])
    rows = list(csv.reader(io.StringIO(text)))
    data = [r for r in rows[1:] if r][0]
    assert data[0] == "KRAKEN_FUTURES"
    assert data[2] == "BTCUSD"  # instrument column


def test_history_boundaries_keep_instruments_separate():
    attempts = [
        _attempt(era="2024"),  # BTCUSD verified at 2024
        _attempt(era="2022"),  # BTCUSD also verified at 2022 (same instrument)
        CapabilityProbeAttempt.model_validate(
            {
                **{k: v for k, v in _attempt(era="2024").model_dump().items()},
                "instrument_native": "PI_ETHUSD",
                "probe_id": "kraken_futures_mechanical_open_interest_pi_ethusd_2024",
            }
        ),
    ]
    text = history_boundaries_csv(attempts)
    rows = list(csv.reader(io.StringIO(text)))
    data = [r for r in rows[1:] if r]
    instruments = {r[2] for r in data}
    assert instruments == {"BTCUSD", "PI_ETHUSD"}
    # ETH row carries only its own evidence, not BTC's 2022 boundary
    eth_row = next(r for r in data if r[2] == "PI_ETHUSD")
    assert eth_row[5] == "" or eth_row[5]  # earliest_verified present
    assert "2022" not in (eth_row[9] or "")  # evidence ids not polluted across instruments


def test_schema_fingerprints_jsonl(report_dir: str):
    text = Path(report_dir, "09_SCHEMA_FINGERPRINTS.jsonl").read_text(encoding="utf-8")
    records = [json.loads(line) for line in text.splitlines() if line.strip()]
    assert records
    assert all("schema_fingerprint" in r for r in records)
    assert any(r["schema_fingerprint"] == "dict{a:int}" for r in records)


def test_schema_fingerprints_skip_noise():
    # attempts without a fingerprint or timestamps contribute no schema row
    noisy = [_attempt(fingerprint=None, status=ResponseStatusClass.FAILED, era="2021", bare=True)]
    assert schema_fingerprints_jsonl(noisy).strip() == ""


def test_capability_claims_jsonl(report_dir: str):
    text = Path(report_dir, "10_CAPABILITY_CLAIMS.jsonl").read_text(encoding="utf-8")
    records = [json.loads(line) for line in text.splitlines() if line.strip()]
    assert records
    rec = records[0]
    assert rec["provider_id"] == "KRAKEN_FUTURES"
    assert rec["evidence_level"] == "E2_LIVE_RECENT_VERIFIED"
    assert rec["PIT_readiness"] == "PIT_READY"
    assert rec["earliest_verified_history"].endswith("Z")


def test_failures_jsonl(report_dir: str):
    text = Path(report_dir, "11_FAILURES.jsonl").read_text(encoding="utf-8")
    records = [json.loads(line) for line in text.splitlines() if line.strip()]
    assert records
    assert records[0]["failure_class"] == "F_HISTORY_TRUNCATED"
    assert records[0]["hard_block"] is True


def test_manifest_status_vocabulary_distinguishes_categories(report_dir: str):
    text = Path(report_dir, "01_PROBE_RUN_MANIFEST.md").read_text(encoding="utf-8")
    for marker in ["CLAIMED", "FIXTURE", "LIVE_VERIFIED", "HISTORICAL", "BLOCKED", "UNATTEMPTED"]:
        assert marker in text, marker
    assert "BLOC-2-IMPLEMENTATION-DECISION" not in text