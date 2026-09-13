"""Evidence + claim synthesis tests (T2-MODEL-03/05/06, T2-HIST-03/04/05,
T2-SEM-02/03, T2-CONTRA-03)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.probes.enums import (
    AccessMode,
    CapabilityStatus,
    EvidenceLevel,
    EvidenceSourceClass,
    Granularity,
    PITReadiness,
    ProbeFailureClass,
    QueryMode,
    ResponseStatusClass,
)
from crypto_sensor_fabric.probes.evidence import (
    CapabilityProbeEvidence,
    assess_pit_readiness,
    derive_evidence_level,
    derive_pit_readiness,
    deterministic_json,
    evidence_from_attempts,
    synthesize_claim,
    validate_claims_lineage,
)
from crypto_sensor_fabric.probes.models import CapabilityProbeAttempt

RECENT = "RECENT_CONTROL"

RUN_ID = "run_evidence_001"


_ERA_YEARS = {"2021": 2021, "2022": 2022, "2024": 2024, "2026": 2026}


def make_attempt(
    *,
    era: str,
    status: ResponseStatusClass = ResponseStatusClass.VERIFIED_SAMPLE,
    error_class: ProbeFailureClass | None = None,
    timestamp_fields: list[str] | None = None,
    unit_summary: dict[str, str] | None = None,
    fingerprint: str | None = None,
    start: datetime | None = None,
    index: int = 0,
) -> CapabilityProbeAttempt:
    start = start or datetime(_ERA_YEARS.get(era, 2026), 6, 15, tzinfo=UTC)
    return CapabilityProbeAttempt.model_validate(
        {
            "probe_id": f"p-{index}",
            "probe_run_id": RUN_ID,
            "provider_id": "KRAKEN_FUTURES",
            "sensor_family": SensorFamily.MECHANICAL_OPEN_INTEREST,
            "venue_market": "KRAKEN_FUTURES",
            "instrument_native": "PI_XBTUSD",
            "canonical_asset_hint": "BTC",
            "requested_start": start,
            "requested_end": start,
            "requested_granularity": Granularity.G1D,
            "access_mode": AccessMode.PUBLIC_REST,
            "query_mode": QueryMode.TIME_RANGE,
            "response_status_class": status,
            "error_class": error_class,
            "native_timestamp_fields": timestamp_fields or [],
            "native_units_summary": unit_summary or {},
            "request_fingerprint": fingerprint,
            "era_hint": era,
            "probe_version": "sensor-probe-v1",
        }
    )


def _verified_era(era: str, index: int = 0) -> CapabilityProbeAttempt:
    return make_attempt(era=era, index=index)


def _failed_era(era: str, cls: ProbeFailureClass, index: int = 0) -> CapabilityProbeAttempt:
    return make_attempt(
        era=era,
        status=ResponseStatusClass.FAILED,
        error_class=cls,
        index=index,
    )


# ---------------------------------------------------------------------------
# Evidence record invariants
# ---------------------------------------------------------------------------


def test_evidence_model_rejects_extra_fields():
    with pytest.raises(ValueError):
        CapabilityProbeEvidence.model_validate(
            {
                "evidence_id": "e1",
                "probe_run_id": RUN_ID,
                "provider_id": "K",
                "sensor_family": SensorFamily.MECHANICAL_TRADE,
                "venue_market": "K",
                "instrument_native": "I",
                "requested_granularity": Granularity.G1D,
                "observed_at": datetime(2026, 8, 29, tzinfo=UTC),
                "stray": 1,
            }
        )


def test_failed_evidence_requires_failure_class():
    with pytest.raises(ValueError):
        evidence_from_attempts(
            [
                make_attempt(
                    era=RECENT,
                    status=ResponseStatusClass.FAILED,
                    error_class=None,  # type: ignore[arg-type]
                )
            ],
            evidence_id="e1",
            probe_run_id=RUN_ID,
            evidence_class=EvidenceSourceClass.FIRST_PARTY_RUNTIME,
        )


def test_evidence_requires_at_least_one_attempt():
    with pytest.raises(ValueError):
        evidence_from_attempts(
            [],
            evidence_id="e1",
            probe_run_id=RUN_ID,
            evidence_class=EvidenceSourceClass.FIRST_PARTY_RUNTIME,
        )


def test_evidence_groups_attempts_and_preserves_ids():
    attempts = [
        make_attempt(era=RECENT, index=0),
        make_attempt(era=RECENT, index=1),
    ]
    evidence = evidence_from_attempts(
        attempts,
        evidence_id="e-rc",
        probe_run_id=RUN_ID,
        evidence_class=EvidenceSourceClass.FIRST_PARTY_RUNTIME,
    )
    assert evidence.attempt_ids == ["p-0", "p-1"]
    assert evidence.era == RECENT
    assert evidence.provider_id == "KRAKEN_FUTURES"
    assert evidence.evidence_level is EvidenceLevel.E0_CLAIM_ONLY  # raised by synthesis


def test_deterministic_json_sorts_keys_and_serializes_enums():
    a = {"z": 1, "a": {"y": 2, "x": 3}, "era": RECENT}
    b = {"a": {"x": 3, "y": 2}, "era": RECENT, "z": 1}
    assert deterministic_json(a) == deterministic_json(b)
    assert '"era":"RECENT_CONTROL"' in deterministic_json(a)


def test_deterministic_json_serializes_datetimes_deterministically():
    dt = datetime(2026, 8, 29, 12, 0, 0, tzinfo=UTC)
    assert deterministic_json({"t": dt}) == deterministic_json(
        {"t": datetime.fromisoformat("2026-08-29T12:00:00+00:00")}
    )


# ---------------------------------------------------------------------------
# T2-HIST-04/05 — evidence ladder + claimed vs verified separation
# ---------------------------------------------------------------------------


def test_evidence_level_e0_when_nothing_verified():
    attempts = [
        _failed_era("2021", ProbeFailureClass.F_HISTORY_TRUNCATED),
        _failed_era(RECENT, ProbeFailureClass.F_ACCESS_RATE_LIMIT),
    ]
    assert derive_evidence_level(attempts) is EvidenceLevel.E0_CLAIM_ONLY


def test_evidence_level_e2_recent_only():
    attempts = [_verified_era(RECENT)]
    assert derive_evidence_level(attempts) is EvidenceLevel.E2_LIVE_RECENT_VERIFIED


def test_evidence_level_e3_single_historical_era():
    attempts = [_verified_era(RECENT), _verified_era("2024", index=1)]
    assert derive_evidence_level(attempts) is EvidenceLevel.E3_HISTORICAL_CHECKPOINT_VERIFIED


def test_evidence_level_e4_multi_era():
    attempts = [_verified_era(RECENT), _verified_era("2022", index=1), _verified_era("2024", index=2)]
    assert derive_evidence_level(attempts) is EvidenceLevel.E4_MULTI_ERA_VERIFIED


def test_evidence_level_e5_requires_full_reproducibility():
    attempts = [
        make_attempt(
            era="2022",
            index=0,
            timestamp_fields=["t"],
            unit_summary={"amount": "contracts"},
            fingerprint="f",
        ),
        make_attempt(
            era="2024",
            index=1,
            timestamp_fields=["t"],
            unit_summary={"amount": "contracts"},
            fingerprint="f",
        ),
        make_attempt(era=RECENT, index=2, timestamp_fields=["t"]),
    ]
    assert (
        derive_evidence_level(
            attempts,
            pagination_characterized=True,
            timestamp_semantics_clear=True,
            unit_semantics_clear=True,
        )
        is EvidenceLevel.E5_REPRODUCIBLE_COVERAGE_VERIFIED
    )
    # missing reproducibility inputs must not reach E5
    assert (
        derive_evidence_level(attempts, timestamp_semantics_clear=True)
        is EvidenceLevel.E4_MULTI_ERA_VERIFIED
    )


def test_derive_pit_readiness_not_ready_on_timestamp_ambiguity():
    attempts = [
        make_attempt(
            era=RECENT,
            timestamp_fields=["t"],
            error_class=ProbeFailureClass.F_TIMESTAMP_UNCLEAR,
            status=ResponseStatusClass.FAILED,
        )
    ]
    assert derive_pit_readiness(attempts) is PITReadiness.NOT_PIT_READY


def test_derive_pit_readiness_method_version_when_timestamps_observed():
    attempts = [
        make_attempt(era=RECENT, timestamp_fields=["ts"], unit_summary={"qty": "contracts"})
    ]
    assert (
        derive_pit_readiness(attempts) is PITReadiness.PIT_READY_WITH_METHOD_VERSION
    )


def test_derive_pit_readiness_not_ready_without_timestamp_fields():
    attempts = [make_attempt(era=RECENT, timestamp_fields=None)]
    assert derive_pit_readiness(attempts) is PITReadiness.NOT_PIT_READY


# ---------------------------------------------------------------------------
# Claim synthesis — T2-HIST-03/04/05, T2-MODEL-06, T2-CONTRA-03
# ---------------------------------------------------------------------------


def test_claim_current_only_resolves_history_blocked_not_unsupported():
    attempts = [
        _verified_era(RECENT),
        _failed_era("2021", ProbeFailureClass.F_HISTORY_TRUNCATED),
        _failed_era("2022", ProbeFailureClass.F_HISTORY_TRUNCATED),
    ]
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="KRAKEN_FUTURES",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        venue_market="KRAKEN_FUTURES",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=attempts,
    )
    assert claim.capability_status is CapabilityStatus.HISTORY_BLOCKED
    assert claim.capability_status is not CapabilityStatus.UNSUPPORTED


def test_claim_current_only_when_history_not_probed():
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=[_verified_era(RECENT)],
    )
    assert claim.capability_status is CapabilityStatus.VERIFIED_CURRENT_ONLY


def test_claim_claimed_and_verified_history_remain_separate():
    attempts = [_verified_era("2022", index=1)]
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=attempts,
        earliest_claimed_history=datetime(2019, 1, 1, tzinfo=UTC),
    )
    assert claim.earliest_claimed_history == datetime(2019, 1, 1, tzinfo=UTC)
    assert claim.earliest_verified_history == datetime(2022, 6, 15, tzinfo=UTC)
    assert claim.earliest_claimed_history < claim.earliest_verified_history


def test_claim_verified_history_never_exceeds_evidence():
    attempts = [
        _verified_era("2022", index=1),
        _verified_era("2024", index=2),
    ]
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=attempts,
    )
    assert claim.earliest_verified_history == datetime(2022, 6, 15, tzinfo=UTC)
    assert claim.latest_verified_history == datetime(2024, 6, 15, tzinfo=UTC)
    assert claim.evidence_level is EvidenceLevel.E4_MULTI_ERA_VERIFIED


def test_claim_unattempted_is_unverified_never_unsupported():
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=[],
    )
    assert claim.capability_status is CapabilityStatus.UNVERIFIED
    assert claim.evidence_level is EvidenceLevel.E0_CLAIM_ONLY


def test_claim_payment_block_dominates():
    attempts = [
        _verified_era(RECENT),
        _failed_era("2021", ProbeFailureClass.F_ACCESS_PAYMENT),
    ]
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=attempts,
    )
    assert claim.capability_status is CapabilityStatus.PAYMENT_BLOCKED


def test_claim_pre_listing_is_not_provider_failure():
    attempts = [
        _failed_era("2021", ProbeFailureClass.F_PRE_LISTING),
        _failed_era("2022", ProbeFailureClass.F_PRE_LISTING),
    ]
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=attempts,
        known_gaps=["PRE_LISTING at 2021/2022 checkpoints"],
    )
    assert claim.capability_status is CapabilityStatus.UNVERIFIED
    assert claim.known_gaps == ["PRE_LISTING at 2021/2022 checkpoints"]


def test_claim_unsupported_sensor():
    attempts = [_failed_era(RECENT, ProbeFailureClass.F_UNSUPPORTED_SENSOR)]
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_FUNDING,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=attempts,
    )
    assert claim.capability_status is CapabilityStatus.UNSUPPORTED


def test_claim_semantically_unusable_on_timestamp_ambiguity():
    attempts = [
        make_attempt(
            era=RECENT,
            status=ResponseStatusClass.FAILED,
            error_class=ProbeFailureClass.F_TIMESTAMP_UNCLEAR,
        )
    ]
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=attempts,
    )
    assert claim.capability_status is CapabilityStatus.SEMANTICALLY_UNUSABLE
    assert claim.PIT_readiness is PITReadiness.NOT_PIT_READY


def test_claim_transient_failure_remains_unresolved():
    attempts = [_failed_era(RECENT, ProbeFailureClass.F_NETWORK_TIMEOUT)]
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=attempts,
    )
    assert claim.capability_status is CapabilityStatus.TRANSIENT_FAILURE


def test_claim_verified_limited_with_limitations():
    attempts = [_verified_era(RECENT), _verified_era("2022", index=1)]
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=attempts,
        limitations=["strict free quota: 100 requests/min"],
    )
    assert claim.capability_status is CapabilityStatus.VERIFIED_LIMITED


def test_claim_verified_full_scope():
    attempts = [_verified_era(RECENT), _verified_era("2022", index=1), _verified_era("2024", index=2)]
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=attempts,
    )
    assert claim.capability_status is CapabilityStatus.VERIFIED


# ---------------------------------------------------------------------------
# I13R1 — evidence lineage (claims must reference real attempt evidence)
# ---------------------------------------------------------------------------


def test_claim_evidence_ids_populated_from_attempts():
    attempts = [_verified_era(RECENT, index=1), _verified_era("2022", index=2)]
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=attempts,
    )
    # I13R1 §7: an E3 claim must reference its actual attempt evidence
    assert claim.evidence_level is EvidenceLevel.E3_HISTORICAL_CHECKPOINT_VERIFIED
    assert claim.evidence_ids == ["p-1", "p-2"]


def test_lineage_validation_flags_evidence_free_e2_claim():
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=[_verified_era(RECENT)],
    )
    # strip the ids -> lineage violation (E2+ without evidence)
    stripped = claim.model_copy(update={"evidence_ids": []})
    violations = validate_claims_lineage([stripped], [_verified_era(RECENT)])
    assert any("evidence_ids is empty" in v for v in violations)


def test_lineage_validation_flags_dangling_evidence_id():
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=[_verified_era(RECENT)],
    )
    bad = claim.model_copy(update={"evidence_ids": ["does-not-exist"]})
    violations = validate_claims_lineage([bad], [_verified_era(RECENT)])
    assert any("dangling" in v for v in violations)


def test_lineage_validation_clean_when_ids_resolve():
    attempts = [_verified_era(RECENT), _verified_era("2022", index=1)]
    claim = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_OPEN_INTEREST,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=attempts,
    )
    assert validate_claims_lineage([claim], attempts) == []


# ---------------------------------------------------------------------------
# I13R1 — PIT readiness FAIL-CLOSED invariants
# ---------------------------------------------------------------------------


def _pit(*, effective=None, observation=None, publication=None, forward=False,
         forward_resolved=None, affects=None):
    return assess_pit_readiness(
        effective_ts_understood=effective,
        observation_ts_understood=observation,
        publication_delay_understood=publication,
        forward_info_required=forward,
        forward_availability_resolved=forward_resolved,
        publication_affects_reconstruction=affects,
    )


def test_pit_ready_forbidden_when_effective_timestamp_unresolved():
    readiness, reason = _pit(effective=False, observation=True, affects=False)
    assert readiness is PITReadiness.NOT_PIT_READY
    assert reason


def test_pit_ready_forbidden_when_observation_timestamp_unresolved():
    readiness, _ = _pit(effective=True, observation=False, affects=False)
    assert readiness is PITReadiness.NOT_PIT_READY


def test_pit_ready_forbidden_when_forward_info_availability_unresolved():
    readiness, _ = _pit(
        effective=True, observation=True, forward=True, forward_resolved=None, affects=False
    )
    assert readiness is PITReadiness.NOT_PIT_READY


def test_pit_ready_forbidden_when_publication_unknown_and_affects_reconstruction():
    readiness, _ = _pit(
        effective=True, observation=True, publication=None, affects=True
    )
    assert readiness is PITReadiness.NOT_PIT_READY


def test_pit_ready_with_method_version_when_timestamps_understood():
    readiness, reason = _pit(effective=True, observation=True, publication=True, affects=False)
    assert readiness is PITReadiness.PIT_READY
    assert reason is None


def test_pit_limited_path_when_publication_unknown_but_does_not_affect():
    readiness, _ = _pit(effective=True, observation=True, publication=None, affects=False)
    assert readiness in (PITReadiness.PIT_READY, PITReadiness.PIT_READY_WITH_METHOD_VERSION)


def test_claim_supersede_never_erases_prior_evidence():
    first = synthesize_claim(
        claim_id="c1",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=[_verified_era(RECENT)],
        claim_version=1,
    )
    second = synthesize_claim(
        claim_id="c2",
        provider_id="K",
        sensor_family=SensorFamily.MECHANICAL_TRADE,
        venue_market="K",
        access_mode=AccessMode.PUBLIC_REST,
        attempts=[_verified_era(RECENT), _verified_era("2022", index=1)],
        claim_version=2,
        supersedes_claim_id="c1",
    )
    # the superseding claim references its predecessor; evidence is never deleted
    assert second.supersedes_claim_id == "c1"
    assert second.claim_version == 2
    assert first.evidence_level is EvidenceLevel.E2_LIVE_RECENT_VERIFIED
    assert second.evidence_level is EvidenceLevel.E3_HISTORICAL_CHECKPOINT_VERIFIED
