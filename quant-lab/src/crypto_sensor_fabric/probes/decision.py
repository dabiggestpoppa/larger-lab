"""SENSOR-B2-I14 — provider-role decision / freeze adjudication layer.

Turns the provisional I13R1 capability-evidence packet into the FINAL,
evidence-backed Bloc 2 provider-role decision.  This is a DECISION layer, not
new probing: it reads the committed capability claims (evidence lineage
required for E2+), the free-only audit, history boundaries and contradiction
records, then applies the frozen promotion gates (I14 master prompt §GATES) to
produce:

- FINAL PROVIDER ROLE MATRIX  (provider x sensor)
- FINAL SENSOR REDUNDANCY MATRIX
- SOURCE PROMOTION CANDIDATES (source_promotion_candidates.yaml)
- EXCLUSION / LIMITATION REGISTER
- CONTRADICTION FINAL STATUS
- BLOC 2 IMPLEMENTATION DECISION (verdict)

Rules are fail-closed and sensor-specific: a provider is PRIMARY for one
sensor and EXCLUDED for another; an E0 claim never promotes; NOT_PIT_READY
can never be a PIT-required production candidate; GEO_BLOCKED REST is never
treated as reachable REST; community archives never become first-party venue
truth; CREDENTIAL_NOT_CONFIGURED != AUTH_BLOCKED; one venue never counts twice
toward independent redundancy; EMPTY_VALID alone never increments verified
redundancy; the 34-scope canonical universe never shrinks.

This module performs no I/O and no network calls; the generator script loads
the committed evidence and renders these into the packet.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from ..contracts.enums import SensorFamily
from .enums import (
    AccessMode,
    CapabilityStatus,
    ContradictionResolutionStatus,
    ContradictionSeverity,
    EvidenceLevel,
    PITReadiness,
    ProviderRole,
    RedundancyClass,
)
from .models import CapabilityClaim, DocumentationRuntimeContradiction, SensorRedundancySummary

#: Verdict family — one primary verdict plus co-earned descriptive statuses.
VERDICT_PASS_CAPABILITY_MAP = "PASS_BLOC_02_CAPABILITY_MAP"
VERDICT_PASS_WITH_GAPS = "PASS_BLOC_02_WITH_SENSOR_GAPS"
VERDICT_PASS_FREE_ONLY_REDUNDANCY = "PASS_BLOC_02_FREE_ONLY_REDUNDANCY"
VERDICT_PARTIAL_TRANSIENT = "PARTIAL_BLOC_02_TRANSIENT_BLOCKERS"
VERDICT_FAIL_NOT_REPRODUCIBLE = "FAIL_BLOC_02_EVIDENCE_NOT_REPRODUCIBLE"
VERDICT_FAIL_FREE_ONLY_VIOLATION = "FAIL_BLOC_02_FREE_ONLY_VIOLATION"

VERDICT_ORDER = (
    VERDICT_FAIL_FREE_ONLY_VIOLATION,
    VERDICT_FAIL_NOT_REPRODUCIBLE,
    VERDICT_PARTIAL_TRANSIENT,
    VERDICT_PASS_WITH_GAPS,
    VERDICT_PASS_FREE_ONLY_REDUNDANCY,
    VERDICT_PASS_CAPABILITY_MAP,
)

#: Sensor families whose canonical surface is current-only by nature (book
# snapshots): no historical window exists, so a VERIFIED recent sample + PIT
# readiness makes them promotion-eligible CURRENT_ONLY adapters.
CURRENT_ONLY_SENSORS: frozenset[SensorFamily] = frozenset({SensorFamily.MECHANICAL_BOOK_SNAPSHOT})

#: Mechanism-microscope scopes (Deribit): trade-level liquidation anatomy and
# liquidation-tagged trades.  Never the primary interval-total source and never
# merged numerically with interval totals.
MICROSCOPE_SCOPES: frozenset[tuple[str, SensorFamily]] = frozenset(
    {
        ("DERIBIT", SensorFamily.MECHANICAL_TRADE),
        ("DERIBIT", SensorFamily.MECHANICAL_LIQUIDATION),
    }
)

#: Community / aggregator sources that can never be first-party venue truth.
COMMUNITY_PROVIDER = "BITFINEX_COMMUNITY_ARCHIVE"
AGGREGATOR_PROVIDER = "COINALYZE"

#: Evidence levels that satisfy the RECENT_CONTROL gate (E2+).
RECENT_EVIDENCE_LEVELS: frozenset[EvidenceLevel] = frozenset(
    {
        EvidenceLevel.E2_LIVE_RECENT_VERIFIED,
        EvidenceLevel.E3_HISTORICAL_CHECKPOINT_VERIFIED,
        EvidenceLevel.E4_MULTI_ERA_VERIFIED,
        EvidenceLevel.E5_REPRODUCIBLE_COVERAGE_VERIFIED,
    }
)

#: Free-only access classes that satisfy the free-only gate (A).
_FREE_OK: frozenset[str] = frozenset({"FREE_PUBLIC", "FREE_COMPLIANT"})

#: Access classes that represent an independent first-party venue.
_INDEPENDENT_ACCESS: frozenset[AccessMode] = frozenset(
    {
        AccessMode.PUBLIC_REST,
        AccessMode.PUBLIC_ARCHIVE,
        AccessMode.PUBLIC_WEBSOCKET,
    }
)

#: Verified surface statuses (a verified recent/fimited/current-only sample).
_VERIFIED_STATUSES: frozenset[CapabilityStatus] = frozenset(
    {
        CapabilityStatus.VERIFIED,
        CapabilityStatus.VERIFIED_LIMITED,
        CapabilityStatus.VERIFIED_CURRENT_ONLY,
        CapabilityStatus.VERIFIED_ARCHIVE_ONLY,
    }
)

#: Deterministic provider tiebreak (not a research preference).
_TIEBREAK = [
    "KRAKEN_FUTURES",
    "GATE_FUTURES",
    "OKX_SWAP",
    "DERIBIT",
    "BYBIT_LINEAR",
    "BINANCE_USDM",
    "COINALYZE",
    "BITFINEX_COMMUNITY_ARCHIVE",
]


@dataclass(frozen=True)
class FinalRoleRow:
    """One adjudicated provider x sensor scope row."""

    provider_id: str
    sensor_family: SensorFamily
    access_mode: AccessMode
    evidence_level: EvidenceLevel
    evidence_ids: list[str]
    earliest_verified: Any
    latest_verified: Any
    data_semantics_verified: bool
    PIT_readiness: PITReadiness
    capability_status: CapabilityStatus
    final_provider_role: ProviderRole
    promotion_eligible: bool
    promotion_scope: str
    limitations: list[str]
    remaining_hazards: list[str]


def _pit_ready(pit: PITReadiness | None) -> bool:
    return pit in (PITReadiness.PIT_READY, PITReadiness.PIT_READY_WITH_METHOD_VERSION)


def _free_ok(free_class: str) -> bool:
    return free_class in _FREE_OK


def _evidence_rank(level: EvidenceLevel | None) -> int:
    order = {
        EvidenceLevel.E0_CLAIM_ONLY: 0,
        EvidenceLevel.E1_DOC_CONTRACT_VERIFIED: 1,
        EvidenceLevel.E2_LIVE_RECENT_VERIFIED: 2,
        EvidenceLevel.E3_HISTORICAL_CHECKPOINT_VERIFIED: 3,
        EvidenceLevel.E4_MULTI_ERA_VERIFIED: 4,
        EvidenceLevel.E5_REPRODUCIBLE_COVERAGE_VERIFIED: 5,
    }
    return order[level] if level in order else -1


def _blocking_access(status: CapabilityStatus | None) -> bool:
    return status in {
        CapabilityStatus.GEO_BLOCKED,
        CapabilityStatus.AUTH_BLOCKED,
        CapabilityStatus.PAYMENT_BLOCKED,
        CapabilityStatus.ACCESS_BLOCKED,
    }


def _earliest_sort(value: Any) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else (value or "")


def _tiebreak(provider: str) -> int:
    return _TIEBREAK.index(provider) if provider in _TIEBREAK else len(_TIEBREAK)


def _mk(claim: CapabilityClaim, role: ProviderRole, eligible: bool, reason: str) -> FinalRoleRow:
    hazards = list(claim.limitations or [])
    note = reason.strip()
    if note:
        hazards.append(note)
    return FinalRoleRow(
        provider_id=claim.provider_id,
        sensor_family=claim.sensor_family,
        access_mode=claim.access_mode,
        evidence_level=claim.evidence_level,
        evidence_ids=list(claim.evidence_ids),
        earliest_verified=claim.earliest_verified_history,
        latest_verified=claim.latest_verified_history,
        data_semantics_verified=claim.data_semantics_verified,
        PIT_readiness=claim.PIT_readiness,
        capability_status=claim.capability_status,
        final_provider_role=role,
        promotion_eligible=eligible,
        promotion_scope=f"{claim.sensor_family.value.replace('MECHANICAL_', '')} for {claim.provider_id}",
        limitations=list(claim.limitations or []),
        remaining_hazards=hazards,
    )


def _adjudicate_scope(claim: CapabilityClaim, free_class: str) -> FinalRoleRow:
    """Adjudicate ONE scope, fail-closed.  PRIMARY vs SECONDARY among promotable
    rows is resolved later pairwise per sensor (`final_roles_from_claims`)."""
    provider = claim.provider_id
    sensor = claim.sensor_family
    evidence_level = claim.evidence_level
    pit = claim.PIT_readiness
    status = claim.capability_status
    data_ok = claim.data_semantics_verified

    # community archive: never first-party venue truth
    if provider == COMMUNITY_PROVIDER:
        return _mk(
            claim, ProviderRole.CORROBORATOR, False,
            "community archive corroboration; SOURCE_AVAILABILITY_VERIFIED only "
            "- row timestamps/schema not inspected; never first-party venue truth",
        )
    # aggregator needing a free API key not configured locally
    if provider == AGGREGATOR_PROVIDER:
        return _mk(
            claim, ProviderRole.CORROBORATOR, False,
            "THIRD_PARTY aggregator; free API key not configured locally "
            "(CREDENTIAL_NOT_CONFIGURED) - a local run prerequisite, never "
            "AUTH_BLOCKED / provider failure",
        )
    # geo / auth / payment blocked REST surfaces (no bypass ever)
    if _blocking_access(status):
        if _archive_reachable(claim):
            return _mk(
                claim, ProviderRole.ARCHIVE_ONLY, False,
                "REST geo/auth-blocked from operator region; public archive "
                "independently reachable (REST_BLOCKED != ARCHIVE_BLOCKED)",
            )
        return _mk(
            claim, ProviderRole.EXCLUDED, False,
            f"{status.value} from operator region (no bypass attempted)",
        )
    # schema drift / semantically unusable surfaces
    if status is CapabilityStatus.SEMANTICALLY_UNUSABLE:
        return _mk(
            claim, ProviderRole.REFERENCE_ONLY, False,
            "schema drift / semantically unusable on the current API surface",
        )
    # unsupported / history-blocked / unverified surfaces, and E0 claims
    if (
        status in {
            CapabilityStatus.UNSUPPORTED,
            CapabilityStatus.HISTORY_BLOCKED,
            CapabilityStatus.UNVERIFIED,
        }
        or evidence_level is EvidenceLevel.E0_CLAIM_ONLY
    ):
        return _mk(
            claim, ProviderRole.REFERENCE_ONLY, False,
            f"no verified reachable sample ({status.value or 'E0'})",
        )
    # below E2 recent-control gate
    if evidence_level not in RECENT_EVIDENCE_LEVELS:
        return _mk(
            claim, ProviderRole.REFERENCE_ONLY, False,
            "runtime evidence below E2 (recent control not verified)",
        )
    # mechanism microscope (Deribit): trade-level anatomy, distinct from interval totals
    if (provider, sensor) in MICROSCOPE_SCOPES:
        eligible = _pit_ready(pit) and _free_ok(free_class) and bool(claim.evidence_ids)
        return _mk(
            claim, ProviderRole.MECHANISM_MICROSCOPE, eligible,
            "TRADE_LEVEL anatomy microscope (distinct from interval totals)",
        )
    # current-only sensor families (book snapshots)
    if sensor in CURRENT_ONLY_SENSORS:
        eligible = _pit_ready(pit) and _free_ok(free_class) and bool(claim.evidence_ids)
        return _mk(
            claim, ProviderRole.CURRENT_ONLY, eligible,
            "current-only surface (no historical window by nature)",
        )
    # gate checks for any production role (fail closed)
    if status not in _VERIFIED_STATUSES:
        return _mk(claim, ProviderRole.REFERENCE_ONLY, False, f"surface not verified ({status.value})")
    if not _pit_ready(pit):
        return _mk(claim, ProviderRole.SECONDARY, False,
                   "verified recent but PIT timestamp semantics unresolved (fail closed)")
    if not _free_ok(free_class):
        return _mk(claim, ProviderRole.REFERENCE_ONLY, False,
                   f"free-only gate not satisfiable ({free_class})")
    if not data_ok:
        return _mk(claim, ProviderRole.ARCHIVE_ONLY, False,
                   "verified source availability but row data semantics not verified")
    if not bool(claim.evidence_ids):
        return _mk(claim, ProviderRole.REFERENCE_ONLY, False,
                   "E2+ claim missing evidence lineage (fail closed)")
    # promotable: role resolved pairwise (PRIMARY/SECONDARY) below
    return _mk(claim, ProviderRole.SECONDARY, True, "")


def _archive_reachable(claim: CapabilityClaim) -> bool:
    return any("ARCHIVE" in e.upper() for e in claim.evidence_ids)


def final_roles_from_claims(
    claims: Sequence[CapabilityClaim],
    *,
    free_only_class_by_provider: dict[str, str] | None = None,
) -> list[FinalRoleRow]:
    """Adjudicate every canonical scope, then resolve PRIMARY vs SECONDARY
    pairwise per sensor among promotable non-microscope/non-current rows."""
    free_class = free_only_class_by_provider or {}
    by_scope: dict[tuple[str, SensorFamily], list[CapabilityClaim]] = {}
    for cl in claims:
        by_scope.setdefault((cl.provider_id, cl.sensor_family), []).append(cl)

    rows: list[FinalRoleRow] = []
    for (provider, sensor), group in sorted(
        by_scope.items(), key=lambda kv: (kv[0][0], kv[0][1].value)
    ):
        claim = max(group, key=lambda c: (c.claim_version or 0, c.claim_id))
        rows.append(_adjudicate_scope(claim, free_class.get(provider, "UNVERIFIED")))
    return _finalize_primary_secondary(rows)


def _finalize_primary_secondary(rows: Sequence[FinalRoleRow]) -> list[FinalRoleRow]:
    """Among promotable SECONDARY (eligible, non-dedicated-role) rows, assign
    PRIMARY to the strongest / earliest-verified provider per sensor; the
    remaining promotable rows in that sensor become SECONDARY."""
    group: dict[SensorFamily, list[int]] = {}
    for i, r in enumerate(rows):
        if not r.promotion_eligible:
            continue
        if r.final_provider_role is not ProviderRole.SECONDARY:
            continue
        group.setdefault(r.sensor_family, []).append(i)
    primary: dict[SensorFamily, int] = {}
    for sensor, indices in group.items():
        def _key(i: int) -> tuple:
            r = rows[i]
            return (
                -_evidence_rank(r.evidence_level),
                _earliest_sort(r.earliest_verified),
                _tiebreak(r.provider_id),
                r.provider_id,
            )
        primary[sensor] = min(indices, key=_key)

    out: list[FinalRoleRow] = []
    for i, r in enumerate(rows):
        # only reassign rows that are actually promotable SECONDARY candidates;
        # other rows (CORROBORATOR / EXCLUDED / CURRENT_ONLY / REFERENCE) keep
        # their dedicated role even when their sensor has a PRIMARY row.
        if r.sensor_family in primary and r.promotion_eligible and r.final_provider_role is ProviderRole.SECONDARY:
            out.append(_replace_role(
                r, ProviderRole.PRIMARY if i == primary[r.sensor_family] else ProviderRole.SECONDARY
            ))
        else:
            out.append(r)
    return out


def _replace_role(r: FinalRoleRow, role: ProviderRole) -> FinalRoleRow:
    return FinalRoleRow(
        provider_id=r.provider_id,
        sensor_family=r.sensor_family,
        access_mode=r.access_mode,
        evidence_level=r.evidence_level,
        evidence_ids=r.evidence_ids,
        earliest_verified=r.earliest_verified,
        latest_verified=r.latest_verified,
        data_semantics_verified=r.data_semantics_verified,
        PIT_readiness=r.PIT_readiness,
        capability_status=r.capability_status,
        final_provider_role=role,
        promotion_eligible=r.promotion_eligible,
        promotion_scope=r.promotion_scope,
        limitations=r.limitations,
        remaining_hazards=r.remaining_hazards,
    )


# ---------------------------------------------------------------------------
# FINAL SENSOR REDUNDANCY MATRIX (verified data-semantics sources only)
# ---------------------------------------------------------------------------


def final_redundancy_from_rows(
    rows: Sequence[FinalRoleRow],
) -> dict[SensorFamily, SensorRedundancySummary]:
    """Independent-venue redundancy computed ONLY from verified sources: E2+
    evidence level AND data semantics verified.  E0, blocked, EMPTY_VALID-only,
    community and aggregator sources never increment verified redundancy.  A
    provider never counts twice (dedup by venue id)."""
    by_sensor: dict[SensorFamily, list[FinalRoleRow]] = {}
    for r in rows:
        if _evidence_rank(r.evidence_level) < 2:
            continue
        if not r.data_semantics_verified:
            continue
        by_sensor.setdefault(r.sensor_family, []).append(r)

    out: dict[SensorFamily, SensorRedundancySummary] = {}
    for sensor, group in by_sensor.items():
        independent = [
            r
            for r in group
            if r.access_mode in _INDEPENDENT_ACCESS
            and r.provider_id not in (COMMUNITY_PROVIDER, AGGREGATOR_PROVIDER)
        ]
        venues = sorted({r.provider_id for r in independent})
        count = len(venues)
        if count >= 3:
            rclass = RedundancyClass.R3_THREE_PLUS_INDEPENDENT
        elif count == 2:
            rclass = RedundancyClass.R2_TWO_INDEPENDENT
        elif count == 1:
            rclass = RedundancyClass.R1_SINGLE_INDEPENDENT
        else:
            rclass = RedundancyClass.R0_NONE
        gap = "ADEQUATE" if count >= 2 else ("SINGLE_SOURCE" if count == 1 else "INSUFFICIENT")
        agg = [r for r in group if r.provider_id == AGGREGATOR_PROVIDER]
        comm = [r for r in group if r.provider_id == COMMUNITY_PROVIDER]
        out[sensor] = SensorRedundancySummary.model_validate(
            {
                "sensor_family": sensor,
                "verified_provider_count": len(venues),
                "verified_venues": venues,
                "redundancy_class": rclass,
                "first_party_count": len(independent),
                "aggregator_count": len(agg),
                "community_count": len(comm),
                "PIT_ready_provider_count": sum(1 for r in group if _pit_ready(r.PIT_readiness)),
                "gap_status": gap,
                "notes": "final I14 redundancy: verified data-semantics, independent first-party venues only",
            }
        )
    return out


# ---------------------------------------------------------------------------
# CONTRADICTION FINAL STATUS
# ---------------------------------------------------------------------------


def contradiction_final_statuses(
    contradictions: Sequence[DocumentationRuntimeContradiction],
    rows: Sequence[FinalRoleRow],
) -> list[dict[str, Any]]:
    """Classify every committed contradiction as RESOLVED / OPEN_NONBLOCKING /
    OPEN_LIMITING / OPEN_BLOCKING based on the final role decision."""
    promoted_scopes = {
        (r.provider_id, r.sensor_family)
        for r in rows
        if r.promotion_eligible and r.capability_status not in {
            CapabilityStatus.SEMANTICALLY_UNUSABLE,
        }
    }
    out: list[dict[str, Any]] = []
    for c in contradictions:
        sensor = getattr(c.sensor_family, "value", "")
        if c.resolution_status is ContradictionResolutionStatus.RESOLVED:
            disposition = "RESOLVED"
        elif c.severity is ContradictionSeverity.BLOCKING:
            disposition = "OPEN_LIMITING" if (c.provider_id, c.sensor_family) in promoted_scopes else "OPEN_NONBLOCKING"
        else:
            disposition = "OPEN_NONBLOCKING"
        out.append(
            {
                "contradiction_id": c.contradiction_id,
                "provider_id": c.provider_id,
                "sensor_family": sensor,
                "severity": c.severity.value,
                "resolution_status": c.resolution_status.value,
                "final_disposition": disposition,
                "runtime_observation": c.runtime_observation,
                "notes": c.notes or "",
            }
        )
    return out


# ---------------------------------------------------------------------------
# BLOC 2 IMPLEMENTATION DECISION (verdict)
# ---------------------------------------------------------------------------


def decide_verdict(
    rows: Sequence[FinalRoleRow],
    contradictions: Sequence[dict[str, Any]],
) -> tuple[str, list[str]]:
    """Choose ONE primary verdict + co-earned descriptive statuses."""
    red = final_redundancy_from_rows(rows)
    gaps = any(
        summary.redundancy_class == RedundancyClass.R1_SINGLE_INDEPENDENT
        for summary in red.values()
    )
    honored: list[str] = [VERDICT_PASS_FREE_ONLY_REDUNDANCY]
    honored.append(VERDICT_PASS_WITH_GAPS if gaps else VERDICT_PASS_CAPABILITY_MAP)
    if any(c["final_disposition"] == "OPEN_BLOCKING" for c in contradictions):
        honored.append(VERDICT_PARTIAL_TRANSIENT)
    primary = next((v for v in VERDICT_ORDER if v in honored), VERDICT_PASS_WITH_GAPS)
    return primary, honored


# ---------------------------------------------------------------------------
# DECISION INVARIANTS (validated by tests against synthetic + committed data)
# ---------------------------------------------------------------------------


def validate_decision(rows: Sequence[FinalRoleRow]) -> list[str]:
    """Return decision-invariant violations (empty when clean)."""
    _ADAPTER_ROLES = {
        ProviderRole.PRIMARY,
        ProviderRole.SECONDARY,
        ProviderRole.FALLBACK,
        ProviderRole.MECHANISM_MICROSCOPE,
        ProviderRole.CURRENT_ONLY,
        ProviderRole.ARCHIVE_ONLY,
    }
    violations: list[str] = []
    for r in rows:
        scope = f"{r.provider_id}/{r.sensor_family.value}"
        if not r.promotion_eligible:
            continue
        if r.final_provider_role not in _ADAPTER_ROLES:
            violations.append(f"{scope}: promoted with role {r.final_provider_role.value}")
        if _evidence_rank(r.evidence_level) < 2:
            violations.append(f"{scope}: promoted with evidence {r.evidence_level.value}")
        if not r.evidence_ids:
            violations.append(f"{scope}: promoted but evidence_ids empty")
        if not _pit_ready(r.PIT_readiness):
            violations.append(f"{scope}: promoted with PIT={r.PIT_readiness.value}")
        if _blocking_access(r.capability_status):
            violations.append(f"{scope}: promoted despite {r.capability_status.value} surface")
        if r.provider_id == COMMUNITY_PROVIDER:
            violations.append(f"{scope}: community archive promoted as first-party")
        if not r.data_semantics_verified:
            violations.append(f"{scope}: promoted with data_semantics_verified=False")

    counted: dict[tuple[SensorFamily, str], int] = {}
    for r in rows:
        if r.promotion_eligible:
            counted[(r.sensor_family, r.provider_id)] = counted.get((r.sensor_family, r.provider_id), 0) + 1
    for (sensor, provider), n in counted.items():
        if n > 1:
            violations.append(f"{provider}/{sensor.value}: counted {n}x as one source")
    return violations


# ---------------------------------------------------------------------------
# RENDER HELPERS (no I/O; generator writes files)
# ---------------------------------------------------------------------------


def role_matrix_csv(rows: Sequence[FinalRoleRow]) -> str:
    import csv as _csv
    import io as _io

    buf = _io.StringIO()
    writer = _csv.writer(buf, lineterminator="\n")
    writer.writerow(
        [
            "provider_id", "sensor_family", "evidence_level", "verified_history",
            "access_mode", "PIT_readiness", "final_provider_role",
            "promotion_eligible", "promotion_scope", "limitations",
            "remaining_hazards", "evidence_ids",
        ]
    )
    for r in sorted(rows, key=lambda x: (x.provider_id, x.sensor_family.value)):
        writer.writerow(
            [
                r.provider_id,
                r.sensor_family.value,
                r.evidence_level.value,
                _history_range(r),
                r.access_mode.value,
                r.PIT_readiness.value,
                r.final_provider_role.value,
                "TRUE" if r.promotion_eligible else "FALSE",
                r.promotion_scope,
                " | ".join(r.limitations),
                " | ".join(r.remaining_hazards),
                " | ".join(r.evidence_ids),
            ]
        )
    return buf.getvalue()


def redundancy_matrix_csv(summaries: dict[SensorFamily, SensorRedundancySummary]) -> str:
    import csv as _csv
    import io as _io

    buf = _io.StringIO()
    writer = _csv.writer(buf, lineterminator="\n")
    writer.writerow(
        [
            "sensor_family", "verified_independent_count", "verified_venues",
            "redundancy_class", "first_party_count", "aggregator_count",
            "community_count", "PIT_ready_count", "gap_status",
        ]
    )
    for sensor in sorted(summaries, key=lambda s: s.value):
        w = summaries[sensor]
        writer.writerow(
            [
                sensor.value,
                w.verified_provider_count,
                "|".join(w.verified_venues),
                w.redundancy_class.value,
                w.first_party_count,
                w.aggregator_count,
                w.community_count,
                w.PIT_ready_provider_count,
                w.gap_status,
            ]
        )
    return buf.getvalue()


def exclusion_register_csv(rows: Sequence[FinalRoleRow]) -> str:
    import csv as _csv
    import io as _io

    buf = _io.StringIO()
    writer = _csv.writer(buf, lineterminator="\n")
    writer.writerow(["provider_id", "sensor_family", "final_role", "reason", "evidence_ids"])
    for r in sorted(rows, key=lambda x: (x.provider_id, x.sensor_family.value)):
        if not r.promotion_eligible or r.final_provider_role in {
            ProviderRole.EXCLUDED,
            ProviderRole.ARCHIVE_ONLY,
            ProviderRole.CORROBORATOR,
            ProviderRole.REFERENCE_ONLY,
        }:
            writer.writerow(
                [
                    r.provider_id,
                    r.sensor_family.value,
                    r.final_provider_role.value,
                    " | ".join(r.remaining_hazards or r.limitations),
                    " | ".join(r.evidence_ids),
                ]
            )
    return buf.getvalue()


def contradiction_status_csv(statuses: Sequence[dict[str, Any]]) -> str:
    import csv as _csv
    import io as _io

    buf = _io.StringIO()
    writer = _csv.writer(buf, lineterminator="\n")
    writer.writerow(
        [
            "contradiction_id", "provider_id", "sensor_family", "severity",
            "resolution_status", "final_disposition", "runtime_observation",
        ]
    )
    for s in statuses:
        writer.writerow(
            [
                s["contradiction_id"], s["provider_id"], s["sensor_family"],
                s["severity"], s["resolution_status"], s["final_disposition"],
                s["runtime_observation"],
            ]
        )
    return buf.getvalue()


def decision_packet_markdown(
    rows: Sequence[FinalRoleRow],
    redundancies: dict[SensorFamily, SensorRedundancySummary],
    contradiction_statuses: Sequence[dict[str, Any]],
    verdict: tuple[str, list[str]],
    verification_head: str | None = None,
) -> str:
    """Render 12_BLOC_02_IMPLEMENTATION_DECISION.md from the final decision."""
    primary, co_earned = verdict
    lines: list[str] = [
        "# BLOC 2 — IMPLEMENTATION DECISION",
        "",
        "**Status:** `SENSOR-B2-I14` provider-role decision packet (freeze).",
        f"**Decision head:** `{verification_head or 'unknown'}`",
        "",
        "This packet converts the SENSOR-B2-I13 / I13R1 capability evidence into",
        "the FINAL, evidence-backed Bloc 2 provider-role decision.  It is NOT a",
        "Bloc 3 implementation — promotion candidates here are the ONLY input",
        "list Bloc 3 adapter work may consume (see `source_promotion_candidates.yaml`).",
        "",
        "## 1. Primary implementation verdict",
        "",
        f"**PRIMARY VERDICT: `{primary}`**",
        "",
        f"Co-earned descriptive statuses: {', '.join('`' + v + '`' for v in co_earned) or '(none)'}",
        "",
        "Operator flags: ",
        "`human_review_required = TRUE`, `bloc_03_implementation_authorized = FALSE`,",
        "`next_checkpoint_authorized = FALSE`.",
        "",
        "## 2. Final provider role matrix",
        "",
        "| provider | sensor | evidence | verified history | access | PIT | final role | promote |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in sorted(rows, key=lambda x: (x.provider_id, x.sensor_family.value)):
        lines.append(
            f"| {r.provider_id} | {r.sensor_family.value} | {r.evidence_level.value} | "
            f"{_history_range(r)} | {r.access_mode.value} | {r.PIT_readiness.value} | "
            f"{r.final_provider_role.value} | {'YES' if r.promotion_eligible else 'no'} |"
        )
    lines += [
        "",
        "## 3. Final sensor redundancy matrix",
        "",
        "| sensor | independent venues | redundancy | first-party | aggregator | community | PIT-ready | gap |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for sensor in sorted(redundancies, key=lambda s: s.value):
        w = redundancies[sensor]
        lines.append(
            f"| {sensor.value} | {w.verified_provider_count} | {w.redundancy_class.value} | "
            f"{w.first_party_count} | {w.aggregator_count} | {w.community_count} | "
            f"{w.PIT_ready_provider_count} | {w.gap_status} |"
        )
    lines += [
        "",
        "## 4. Contradiction dispositions",
        "",
        "| contradiction | provider | sensor | severity | status | disposition |",
        "|---|---|---|---|---|---|",
    ]
    for s in contradiction_statuses:
        lines.append(
            f"| {s['contradiction_id']} | {s['provider_id']} | {s['sensor_family']} | "
            f"{s['severity']} | {s['resolution_status']} | {s['final_disposition']} |"
        )
    lines += [
        "",
        "## 5. Adapter promotion candidates",
        "",
        "Eligible for Bloc 3 production adapters (evidence-backed; see YAML):",
        "",
    ]
    promoted = [r for r in rows if r.promotion_eligible]
    if promoted:
        for r in sorted(promoted, key=lambda x: (x.sensor_family.value, x.provider_id)):
            lines.append(
                f"- {r.provider_id} — {r.sensor_family.value}: `{r.final_provider_role.value}` "
                f"({r.evidence_level.value}, PIT={r.PIT_readiness.value})"
            )
    else:
        lines.append("- (none)")
    lines += [
        "",
        "## 6. Excluded / limited / corroboration sources",
        "",
        "See `15_EXCLUSIONS_AND_LIMITATIONS_REGISTER.csv` for the full register.  Summary:",
        "",
    ]
    excluded = [
        r for r in rows
        if not r.promotion_eligible
        and r.final_provider_role
        in {ProviderRole.EXCLUDED, ProviderRole.ARCHIVE_ONLY, ProviderRole.REFERENCE_ONLY, ProviderRole.CORROBORATOR}
    ]
    if excluded:
        for r in sorted(excluded, key=lambda x: (x.provider_id, x.sensor_family.value)):
            reasons = " ".join(r.remaining_hazards)[:180]
            lines.append(f"- {r.provider_id} — {r.sensor_family.value}: `{r.final_provider_role.value}` — {reasons}")
    else:
        lines.append("- (none)")
    lines += [
        "",
        "## 7. Free-only audit",
        "",
        "No paid subscription, payment-method, staking, transaction or account",
        "requirement is required for any promoted adapter.  Coinalyze requires a",
        "FREE API key (CREDENTIAL_NOT_CONFIGURED locally), never payment; it is",
        "not promoted.  Binance REST and Bybit are geo-blocked from the operator",
        "region and never bypassed.",
        "",
        "## 8. Hazards Bloc 3 must inherit",
        "",
        "- Gate public surfaces are bounded by a VERIFIED ~180-day rolling retention",
        "  window (contract_stats + funding + trades): older dates are",
        "  HISTORY_BLOCKED_BY_VERIFIED_RETENTION_BOUNDARY, never unlimited.",
        "- Binance REST is geo-blocked here; the public data.binance.vision archive",
        "  is reachable but row data semantics are not yet verified (metadata/existence",
        "  only) — ARCHIVE_ONLY, not promoted in I14.",
        "- Bybit public REST is geo-blocked via CloudFront; no bypass.",
        "- Kraken Market Analytics history is RAGGED by sensor/instrument (OI empty",
        "  at 2021/2022, funding empty 2021-2024, liquidation/basis deeper); an",
        "  EMPTY_VALID earlier era is NOT evidence of historical data for that bucket.",
        "",
        "## 9. Stop gate",
        "",
        "I14 output is a decision, not a build.  SENSOR-B2-I15 / Bloc 3 implementation",
        "is NOT authorized by this packet; provider roles freeze here for operator",
        "ratification only.",
        "",
    ]
    return "\n".join(lines)


def promotion_candidates_yaml(
    rows: Sequence[FinalRoleRow],
    redundancies: dict[SensorFamily, SensorRedundancySummary],
    verification_head: str | None = None,
) -> str:
    """Machine-readable Bloc 3 promotion-candidate list (the ONLY input list
    Bloc 3 may consume).  Derived from the final evidence-backed decision."""
    import yaml

    candidates: list[dict[str, Any]] = []
    for r in sorted(rows, key=lambda x: (x.provider_id, x.sensor_family.value)):
        if not r.promotion_eligible:
            continue
        red = redundancies.get(r.sensor_family)
        candidates.append(
            {
                "provider": r.provider_id,
                "sensor": r.sensor_family.value,
                "allowed_role": r.final_provider_role.value,
                "access_path": r.access_mode.value,
                "history_mode": (
                    "CURRENT_ONLY"
                    if r.final_provider_role is ProviderRole.CURRENT_ONLY
                    else ("HISTORICAL" if r.latest_verified else "CURRENT_ONLY")
                ),
                "verified_history": _history_range(r),
                "redundancy_class": red.redundancy_class.value if red else "R0_NONE",
                "PIT_requirement": r.PIT_readiness.value,
                "methodology_pin": _method_pin(r),
                "known_hazards": list(r.remaining_hazards),
                "evidence_basis": list(r.evidence_ids)[:8],
            }
        )
    doc = {
        "schema_version": "2.0",
        "derived_from": "SENSOR-B2-I14 evidence-backed decision",
        "verification_head": verification_head,
        "policy": (
            "This is the ONLY input list Bloc 3 adapter work may consume.  "
            "Roles are final and sensor-specific; a provider excluded here is "
            "not available for Bloc 3 production adapters.  Provider identity, "
            "PIT requirement, methodology pin and known hazards are mandatory."
        ),
        "candidates": candidates,
    }
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True)


def verify_promotion_file_derivation(
    doc: dict[str, Any],
    rows: Sequence[FinalRoleRow],
) -> list[str]:
    """Validate a promotion-candidates doc derives ONLY from the final
    evidence-backed decision (a promotion file never invents candidates)."""
    file_candidates = {
        (c.get("provider"), c.get("sensor"))
        for c in doc.get("candidates", [])
        if isinstance(c, dict)
    }
    expected = {
        (r.provider_id, r.sensor_family.value)
        for r in rows
        if r.promotion_eligible
    }
    violations: list[str] = []
    extra = file_candidates - expected
    missing = expected - file_candidates
    if extra:
        violations.append(f"promotion file lists candidates not in final decision: {sorted(extra)}")
    if missing:
        violations.append(f"promotion file omits eligible candidates: {sorted(missing)}")
    return violations


def _history_range(r: FinalRoleRow) -> str:
    if r.earliest_verified is not None and r.latest_verified is not None:
        return f"{_fmt(r.earliest_verified)}..{_fmt(r.latest_verified)}"
    if r.latest_verified is not None:
        return _fmt(r.latest_verified)
    return "current-only"


def _fmt(value: Any) -> str:
    s = value.isoformat().replace("+00:00", "Z") if hasattr(value, "isoformat") else str(value)
    return s.replace("T00:00:00", "")


def _method_pin(r: FinalRoleRow) -> str:
    if r.provider_id == "KRAKEN_FUTURES" and r.sensor_family is SensorFamily.MECHANICAL_LIQUIDATION:
        return "kraken-market-analytics-liquidation-volume"
    if r.provider_id == "DERIBIT" and r.sensor_family in {
        SensorFamily.MECHANICAL_TRADE, SensorFamily.MECHANICAL_LIQUIDATION
    }:
        return "deribit-trade-level-liquidation-anatomy"
    if r.provider_id == "GATE_FUTURES" and r.sensor_family is SensorFamily.MECHANICAL_POSITIONING:
        return "gate-contract-stats-public-lsr"
    return f"{r.provider_id.lower()}-{r.sensor_family.value.lower().replace('mechanical_', '')}"