"""Generate the Bloc 2 pre-live evidence packet (SENSOR-B2-I12 helpers).

Offline and deterministic.  It renders the corrected provider contracts into
the frozen human/machine reports under
`research/crypto_foundry/sensor_fabric/evidence/bloc_02/`.

This is the CLAIMED / FIXTURE / UNATTEMPTED pass — nothing is marked live- or
historically-verified because SENSOR-B2-I13 live probing and SENSOR-B2-I14 role
freezing have not run yet.  An unprobed claim is never promoted.

Run from the `quant-lab` directory:

    python scripts/generate_bloc_02_packet.py

Writes only inside the evidence/bloc_02 directory.  No network calls.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from crypto_sensor_fabric.contracts.enums import SensorFamily  # noqa: E402
from crypto_sensor_fabric.probes.enums import (  # noqa: E402
    AccessMode,
    CapabilityStatus,
    ContradictionResolutionStatus,
    ContradictionSeverity,
    EvidenceLevel,
    FreeOnlyStatus,
    Granularity,
    HistoricalBoundaryConfidence,
    PITReadiness,
    ProviderRole,
)
from crypto_sensor_fabric.probes.models import (  # noqa: E402
    CapabilityClaim,
    DocumentationRuntimeContradiction,
    ProbeRunResult,
    ProbeRunStatus,
    ProviderSensorCoverage,
    SensorRedundancySummary,
)
from crypto_sensor_fabric.probes.reports import write_reports  # noqa: E402

OUTPUT_DIR = (
    REPO_ROOT
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_02"
)
CONFIG = REPO_ROOT / "config" / "crypto_sensor_fabric" / "provider_probe_endpoints.yaml"

#: access-mode vocabulary mapping from the endpoint registry to the probe enum.
_ACCESS_MAP = {
    "FREE_PUBLIC": AccessMode.PUBLIC_REST,
    "FREE_API_KEY": AccessMode.FREE_API_KEY,
    "COMMUNITY_ARCHIVE": AccessMode.COMMUNITY_ARCHIVE,
}


def _load_providers() -> dict:
    with CONFIG.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)["providers"]


def _claims_and_coverages(providers: dict) -> tuple[list[CapabilityClaim], list[ProviderSensorCoverage]]:
    claims: list[CapabilityClaim] = []
    coverages: list[ProviderSensorCoverage] = []
    claim_idx = 0
    for pid in sorted(providers):
        entry = providers[pid]
        access = _ACCESS_MAP.get(entry.get("access", ""))
        if access is None:
            continue
        # Every sensor family the registry maps for this provider is a CLAIMED
        # probe cell until a live/fixture observation exists (fail-closed).
        for sensor in sorted({SensorFamily(s) for s in entry.get("endpoints", {})}):
            claim_idx += 1
            claims.append(
                CapabilityClaim.model_validate(
                    {
                        "claim_id": f"claim_bloc2_{pid.lower()}_{sensor.value.lower()}_{claim_idx:03d}",
                        "provider_id": pid,
                        "sensor_family": sensor,
                        "venue_market": pid,
                        "instrument_scope": ["TBD"],
                        "granularity_scope": [Granularity.G1D],
                        "access_mode": access,
                        "capability_status": CapabilityStatus.UNVERIFIED,
                        "evidence_level": EvidenceLevel.E0_CLAIM_ONLY,
                        "history_boundary_confidence": HistoricalBoundaryConfidence.UNKNOWN,
                        "PIT_readiness": PITReadiness.NOT_PIT_READY,
                        "free_only_status": FreeOnlyStatus.UNVERIFIED,
                        "known_gaps": ["no live probe yet (SENSOR-B2-I13 pending)"],
                        "evidence_ids": [],
                    }
                )
            )
            coverages.append(
                ProviderSensorCoverage.model_validate(
                    {
                        "provider_id": pid,
                        "sensor_family": sensor,
                        "venue_market": pid,
                        "instrument_scope": ["TBD"],
                        "access_mode": access,
                        "era_status": {},
                        "PIT_readiness": PITReadiness.NOT_PIT_READY,
                        "evidence_level": EvidenceLevel.E0_CLAIM_ONLY,
                        "provider_role": ProviderRole.REFERENCE_ONLY,
                        "promotion_eligible": False,
                        "blocking_reason": "no live evidence yet",
                    }
                )
            )
    return claims, coverages


def _condensed_sensors(providers: dict) -> tuple[list[SensorFamily], list[str]]:
    sensors = sorted({SensorFamily(s) for e in providers.values() for s in e.get("endpoints", {})})
    provider_ids = sorted(providers)
    return sensors, provider_ids


def _informational_contradictions() -> list[DocumentationRuntimeContradiction]:
    """INFO-class observations from the planning books (documentation only)."""
    return [
        DocumentationRuntimeContradiction.model_validate(
            {
                "contradiction_id": "contr_bloc2_plan_orderflow",
                "provider_id": "PLANNING",
                "sensor_family": SensorFamily.MECHANICAL_TRADE,
                "documentation_claim": "order_flow listed as a provider capability",
                "documentation_source_ref": "bloc_02/02 provider playbook",
                "runtime_observation": (
                    "no MECHANICAL_ORDER_FLOW member in frozen Bloc 1 SensorFamily; "
                    "order flow is a T2-derived family riding on MECHANICAL_TRADE"
                ),
                "severity": ContradictionSeverity.INFO,
                "resolution_status": ContradictionResolutionStatus.RESOLVED,
                "notes": "BLOC5_SCHEMA_REFINEMENT_PENDING (informational, not a blocker)",
            }
        ),
        DocumentationRuntimeContradiction.model_validate(
            {
                "contradiction_id": "contr_bloc2_plan_bitfinex_source",
                "provider_id": "BITFINEX_COMMUNITY_ARCHIVE",
                "sensor_family": SensorFamily.MECHANICAL_LIQUIDATION,
                "documentation_claim": "daily CSV liquidation tree with checksums.txt",
                "documentation_source_ref": "I11 original characterization (superseded)",
                "runtime_observation": (
                    "actual source is tradingstrategy-ai/bitfinex-liquidations "
                    "Git-LFS DuckDB dump (I11R1); no daily tree, no checksums.txt"
                ),
                "severity": ContradictionSeverity.INFO,
                "resolution_status": ContradictionResolutionStatus.RESOLVED,
                "notes": "corrected in SENSOR-B2-I11R1",
            }
        ),
    ]


def _free_only_audit(providers: dict) -> list[dict]:
    rows: list[dict] = []
    for pid in sorted(providers):
        entry = providers[pid]
        access = entry.get("access", "")
        key = access in ("FREE_API_KEY", "COMMUNITY_ARCHIVE")
        rows.append(
            {
                "provider_id": pid,
                "sensor_family": "|".join(sorted(entry.get("endpoints", {}))) or "",
                "access_mode": access,
                "api_key_required": bool(key),
                "account_required": False,
                "payment_method_required": False,
                "paid_subscription_required": False,
                "staking_required": False,
                "transaction_required": False,
                "free_quota": "UNVERIFIED",
                "access_class": access,
                "eligible_required_runtime": "(pending B2-D/B2-C verification)",
                "evidence_refs": "",
            }
        )
    return rows


def main() -> int:
    if not CONFIG.exists():
        print(f"config not found: {CONFIG}", file=sys.stderr)
        return 1
    providers = _load_providers()
    claims, coverages = _claims_and_coverages(providers)
    expected_sensors, provider_ids = _condensed_sensors(providers)

    now = datetime.now(UTC)
    run = ProbeRunResult.model_validate(
        {
            "probe_run_id": "bloc02_prelive_claims",
            "run_status": ProbeRunStatus.PARTIAL.value,
            "attempts": [],
            "planned_but_skipped": [],
            "started_at": now,
            "finished_at": now,
            "probe_version": "sensor-probe-v1",
            "notes": [
                "pre-live packet: all cells CLAIMED / UNATTEMPTED; nothing verified",
                "SENSOR-B2-I13 live probing not run; SENSOR-B2-I14 roles not frozen",
            ],
        }
    )

    redundancies = []
    for sensor in sorted(set(expected_sensors), key=lambda s: s.value):
        redundancies.append(
            SensorRedundancySummary.model_validate(
                {
                    "sensor_family": sensor,
                    "verified_provider_count": 0,
                    "verified_venues": [],
                    "redundancy_class": "R0_NONE",
                    "first_party_count": 0,
                    "aggregator_count": 0,
                    "community_count": 0,
                    "PIT_ready_provider_count": 0,
                    "gap_status": "UNVERIFIED",
                    "notes": "no live verification yet",
                }
            )
        )

    written = write_reports(
        output_dir=str(OUTPUT_DIR),
        run=run,
        attempts=[],
        claims=claims,
        coverages=coverages,
        redundancies=redundancies,
        contradictions=_informational_contradictions(),
        free_only_audit=_free_only_audit(providers),
        failures=[],  # no runtime failures before live probing
        provider_ids=provider_ids,
        expected_sensors=expected_sensors,
    )
    for path in written:
        print(path)
    print(f"wrote {len(written)} reports -> {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())