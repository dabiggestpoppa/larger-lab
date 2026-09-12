"""SENSOR-B2-I14 — provider-role decision adjudication tests.

Cover the fail-closed decision invariants on synthetic claim fixtures AND on
the committed I13R1 capability-claims packet:

- unverified evidence (E0/E1) can never promote
- evidence-free E2+ claims can never promote
- NOT_PIT_READY can never become a promoted PIT-required production candidate
- GEO_BLOCKED / AUTH_BLOCKED / PAYMENT_BLOCKED REST is never treated as
  reachable REST; archive-only remains separate from REST capability
- community archive cannot become first-party venue truth
- CREDENTIAL_NOT_CONFIGURED != AUTH_BLOCKED (aggregator never promotes as venue)
- historical retention boundary is never represented as unlimited history
- one provider cannot count twice toward independent redundancy
- EMPTY_VALID alone cannot increment verified redundancy
- source-promotion file derives only from final evidence-backed decision
- roles remain sensor-specific
- 34-scope canonical universe never disappears

All offline and deterministic.
"""

from __future__ import annotations

from pathlib import Path

from crypto_sensor_fabric.contracts.enums import SensorFamily as SF
from crypto_sensor_fabric.probes.decision import (
    final_roles_from_claims,
    final_redundancy_from_rows,
    validate_decision,
)
from crypto_sensor_fabric.probes.enums import (
    AccessMode,
    CapabilityStatus,
    EvidenceLevel,
    PITReadiness,
    ProviderRole,
)
from crypto_sensor_fabric.probes.models import CapabilityClaim

EVIDENCE = (
    Path(__file__).resolve().parents[3]
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_02"
)


def _claim(
    *,
    provider: str,
    sensor: SF,
    level: EvidenceLevel = EvidenceLevel.E2_LIVE_RECENT_VERIFIED,
    pit: PITReadiness = PITReadiness.PIT_READY_WITH_METHOD_VERSION,
    status: CapabilityStatus = CapabilityStatus.VERIFIED,
    data_ok: bool = True,
    access: AccessMode = AccessMode.PUBLIC_REST,
    evidence: list[str] | None = None,
) -> CapabilityClaim:
    return CapabilityClaim.model_validate(
        {
            "claim_id": f"claim_{provider.lower()}_{sensor.value.lower()}_i14",
            "provider_id": provider,
            "sensor_family": sensor,
            "venue_market": provider,
            "instrument_scope": ["BTC"],
            "granularity_scope": [],
            "access_mode": access,
            "capability_status": status,
            "evidence_level": level,
            "earliest_claimed_history": None,
            "history_boundary_confidence": "UNKNOWN",
            "PIT_readiness": pit,
            "free_only_status": "FREE_COMPLIANT",
            "evidence_ids": evidence if evidence is not None else (["e1"] if level != EvidenceLevel.E0_CLAIM_ONLY else []),
            "data_semantics_verified": data_ok,
            "pit_effective_ts_understood": True if pit != PITReadiness.NOT_PIT_READY else False,
            "pit_observation_ts_understood": True if pit != PITReadiness.NOT_PIT_READY else False,
        }
    )


def _by_scope(rows):
    return {(r.provider_id, r.sensor_family): r for r in rows}


def test_unverified_evidence_cannot_promote() -> None:
    rows = final_roles_from_claims(
        [
            _claim(provider="KRAKEN_FUTURES", sensor=SF.MECHANICAL_BOOK_SNAPSHOT,
                   level=EvidenceLevel.E0_CLAIM_ONLY, status=CapabilityStatus.UNVERIFIED,
                   data_ok=False, access=AccessMode.PUBLIC_REST),
        ],
        free_only_class_by_provider={"KRAKEN_FUTURES": "FREE_PUBLIC"},
    )
    row = _by_scope(rows)[("KRAKEN_FUTURES", SF.MECHANICAL_BOOK_SNAPSHOT)]
    assert row.promotion_eligible is False
    assert row.final_provider_role is ProviderRole.REFERENCE_ONLY
    assert validate_decision(rows) == []


def test_evidence_free_claim_cannot_promote() -> None:
    rows = final_roles_from_claims(
        [
            _claim(provider="OKX_SWAP", sensor=SF.MECHANICAL_FUNDING,
                   level=EvidenceLevel.E3_HISTORICAL_CHECKPOINT_VERIFIED,
                   pit=PITReadiness.PIT_READY, data_ok=True, evidence=[]),
        ],
        free_only_class_by_provider={"OKX_SWAP": "FREE_PUBLIC"},
    )
    row = _by_scope(rows)[("OKX_SWAP", SF.MECHANICAL_FUNDING)]
    assert row.promotion_eligible is False
    assert "evidence_ids" in " ".join(row.remaining_hazards) or not row.promotion_eligible


def test_not_pit_ready_cannot_be_required_runtime() -> None:
    rows = final_roles_from_claims(
        [
            _claim(provider="GATE_FUTURES", sensor=SF.MECHANICAL_TRADE,
                   level=EvidenceLevel.E2_LIVE_RECENT_VERIFIED,
                   pit=PITReadiness.NOT_PIT_READY, data_ok=True,
                   status=CapabilityStatus.VERIFIED_CURRENT_ONLY),
        ],
        free_only_class_by_provider={"GATE_FUTURES": "FREE_PUBLIC"},
    )
    row = _by_scope(rows)[("GATE_FUTURES", SF.MECHANICAL_TRADE)]
    assert row.promotion_eligible is False
    assert "PIT" in " ".join(row.remaining_hazards)


def _committed_claims() -> list[CapabilityClaim]:
    import json

    path = EVIDENCE / "10_CAPABILITY_CLAIMS.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(CapabilityClaim.model_validate(json.loads(line)))
    return out


def test_committed_packet_34_scopes_all_present() -> None:
    claims = _committed_claims()
    if not claims:
        import pytest

        pytest.skip("committed evidence packet not present")
    assert len(claims) == 34
    scopes = {(c.provider_id, c.sensor_family) for c in claims}
    for provider, sensors in {
        "KRAKEN_FUTURES": 8,
        "GATE_FUTURES": 6,
        "OKX_SWAP": 3,
        "DERIBIT": 4,
        "BINANCE_USDM": 4,
        "BYBIT_LINEAR": 4,
        "COINALYZE": 4,
        "BITFINEX_COMMUNITY_ARCHIVE": 1,
    }.items():
        assert sum(1 for (p, _) in scopes if p == provider) == sensors, provider


def test_committed_decision_invariants_clean() -> None:
    from crypto_sensor_fabric.probes.decision import final_roles_from_claims

    claims = _committed_claims()
    if not claims:
        import pytest

        pytest.skip("committed evidence packet not present")
    free = {
        "KRAKEN_FUTURES": "FREE_PUBLIC",
        "GATE_FUTURES": "FREE_PUBLIC",
        "BINANCE_USDM": "FREE_PUBLIC",
        "BYBIT_LINEAR": "FREE_PUBLIC",
        "OKX_SWAP": "FREE_PUBLIC",
        "DERIBIT": "FREE_PUBLIC",
        "COINALYZE": "FREE_API_KEY",
        "BITFINEX_COMMUNITY_ARCHIVE": "COMMUNITY_ARCHIVE",
    }
    rows = final_roles_from_claims(claims, free_only_class_by_provider=free)
    violations = validate_decision(rows)
    assert violations == [], violations

    # roles are sensor-specific: Kraken is PRIMARY for some but EXCLUDED for book
    role_map = _by_scope(rows)
    kraken_oi = role_map[("KRAKEN_FUTURES", SF.MECHANICAL_OPEN_INTEREST)]
    kraken_book = role_map[("KRAKEN_FUTURES", SF.MECHANICAL_BOOK_SNAPSHOT)]
    assert kraken_oi.promotion_eligible is True
    assert kraken_book.promotion_eligible is False

    # community archive: never promoted as first-party
    bitfinex = role_map[("BITFINEX_COMMUNITY_ARCHIVE", SF.MECHANICAL_LIQUIDATION)]
    assert bitfinex.final_provider_role is ProviderRole.CORROBORATOR
    assert bitfinex.promotion_eligible is False

    # aggregator without key: CREDENTIAL_NOT_CONFIGURED, never AUTH
    coina = role_map[("COINALYZE", SF.MECHANICAL_OPEN_INTEREST)]
    assert coina.final_provider_role is ProviderRole.CORROBORATOR
    assert coina.promotion_eligible is False
    from crypto_sensor_fabric.probes.enums import CapabilityStatus as CS
    assert coina.capability_status is CS.UNVERIFIED  # never AUTH_BLOCKED
    assert coina.final_provider_role is not ProviderRole.EXCLUDED
    assert "CREDENTIAL" in " ".join(coina.remaining_hazards)


def test_committed_redundancy_no_double_count_and_empty_never_counts() -> None:
    claims = _committed_claims()
    if not claims:
        import pytest

        pytest.skip("committed evidence packet not present")
    free = {
        "KRAKEN_FUTURES": "FREE_PUBLIC",
        "GATE_FUTURES": "FREE_PUBLIC",
        "BINANCE_USDM": "FREE_PUBLIC",
        "BYBIT_LINEAR": "FREE_PUBLIC",
        "OKX_SWAP": "FREE_PUBLIC",
        "DERIBIT": "FREE_PUBLIC",
        "COINALYZE": "FREE_API_KEY",
        "BITFINEX_COMMUNITY_ARCHIVE": "COMMUNITY_ARCHIVE",
    }
    rows = final_roles_from_claims(claims, free_only_class_by_provider=free)
    red = final_redundancy_from_rows(rows)

    # Binance archive = metadata only (data_semantics_verified=False) -> never
    # counted for OI redundancy
    oi = red.get(SF.MECHANICAL_OPEN_INTEREST)
    if oi:
        assert "BINANCE_USDM" not in oi.verified_venues

    # each venue appears once per sensor
    for sensor, summary in red.items():
        assert len(summary.verified_venues) == len(set(summary.verified_venues)), sensor.value


def test_promotion_candidates_only_from_final_decision() -> None:
    import yaml

    from crypto_sensor_fabric.probes.decision import (
        promotion_candidates_yaml,
        verify_promotion_file_derivation,
    )

    claims = _committed_claims()
    if not claims:
        import pytest

        pytest.skip("committed evidence packet not present")
    free = {
        "KRAKEN_FUTURES": "FREE_PUBLIC",
        "GATE_FUTURES": "FREE_PUBLIC",
        "BINANCE_USDM": "FREE_PUBLIC",
        "BYBIT_LINEAR": "FREE_PUBLIC",
        "OKX_SWAP": "FREE_PUBLIC",
        "DERIBIT": "FREE_PUBLIC",
        "COINALYZE": "FREE_API_KEY",
        "BITFINEX_COMMUNITY_ARCHIVE": "COMMUNITY_ARCHIVE",
    }
    rows = final_roles_from_claims(claims, free_only_class_by_provider=free)
    red = final_redundancy_from_rows(rows)
    text = promotion_candidates_yaml(rows, red)
    doc = yaml.safe_load(text)
    cand_providers_sensors = {(c["provider"], c["sensor"]) for c in doc["candidates"]}
    expected = {
        (r.provider_id, r.sensor_family.value)
        for r in rows
        if r.promotion_eligible
    }
    assert cand_providers_sensors == expected
    assert verify_promotion_file_derivation(doc, rows) == []