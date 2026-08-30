"""Coverage vectors, per-scope coverage synthesis and sensor redundancy
(03 §7-8, §16-17 / T2-COV-01..06).

Coverage is multidimensional and is never collapsed into a single score for
science decisions — the composite score is a triage convenience only (03 §9,
§21).  Redundancy counts independent venues, never aliases of one feed or
aggregator re-reporting a venue (T2-COV-03, T2-COV-05, §14 redundancy rule).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field

from ..contracts.enums import SemanticEquivalence, SensorFamily
from .enums import (
    AccessMode,
    CapabilityStatus,
    EvidenceSourceClass,
    FreeOnlyStatus,
    Granularity,
    ProbeFailureClass,
    ProviderRole,
    RedundancyClass,
    ResponseStatusClass,
)
from .evidence import derive_evidence_level, derive_pit_readiness
from .models import (
    CapabilityProbeAttempt,
    ProviderSensorCoverage,
    SensorRedundancySummary,
)
from .planner import RECENT_CONTROL_ERA

#: Canonical era names for the historical-coverage dimension (H).
HISTORICAL_ERAS: tuple[str, ...] = ("2021", "2022", "2024", "2026")

#: All evidence-source classes that count toward an independent venue.
INDEPENDENT_CLASSES: frozenset[EvidenceSourceClass] = frozenset(
    {
        EvidenceSourceClass.FIRST_PARTY_RUNTIME,
        EvidenceSourceClass.FIRST_PARTY_ARCHIVE,
    }
)

VERIFIED_LIKE: frozenset[CapabilityStatus] = frozenset(
    {
        CapabilityStatus.VERIFIED,
        CapabilityStatus.VERIFIED_LIMITED,
        CapabilityStatus.VERIFIED_CURRENT_ONLY,
        CapabilityStatus.VERIFIED_ARCHIVE_ONLY,
    }
)


class CoverageVector(BaseModel):
    """Normalized 0..1 coordinate vector (03 §7-8).

    Dimensions: H historical, G granularity, U universe, P pagination/archive
    reliability, T timestamp clarity, N native-unit clarity, A free-only
    accessibility, R reproducibility, S semantic fit, Q continuity/quality.
    """

    model_config = ConfigDict(extra="forbid")

    H: float = Field(ge=0.0, le=1.0)
    G: float = Field(ge=0.0, le=1.0)
    U: float = Field(ge=0.0, le=1.0)
    P: float = Field(ge=0.0, le=1.0)
    T: float = Field(ge=0.0, le=1.0)
    N: float = Field(ge=0.0, le=1.0)
    A: float = Field(ge=0.0, le=1.0)
    R: float = Field(ge=0.0, le=1.0)
    S: float = Field(ge=0.0, le=1.0)
    Q: float = Field(ge=0.0, le=1.0)

    def as_dict(self) -> dict[str, float]:
        return {dim: float(getattr(self, dim)) for dim in "HGPUTNARSQ"}


def _verified_eras(attempts: Sequence[CapabilityProbeAttempt]) -> set[str]:
    return {
        a.era_hint
        for a in attempts
        if a.era_hint is not None
        and a.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    }


def _has_failure(attempts: Sequence[CapabilityProbeAttempt], cls: ProbeFailureClass) -> bool:
    return any(a.error_class is cls for a in attempts)


def _verified_attempts(attempts: Sequence[CapabilityProbeAttempt]) -> list[CapabilityProbeAttempt]:
    return [
        a for a in attempts if a.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    ]


def _historical_coverage(attempts: Sequence[CapabilityProbeAttempt]) -> float:
    """H dimension (03 §8): recent = 0.25 base, each verified era +0.1875."""
    verified = _verified_eras(attempts)
    recent_ok = RECENT_CONTROL_ERA in verified
    era_score = 0.1875 * sum(1 for era in HISTORICAL_ERAS if era in verified)
    return min(1.0, 0.25 * recent_ok + era_score)


def _granularity_coverage(
    attempts: Sequence[CapabilityProbeAttempt],
    planned_granularities: Sequence[Granularity],
) -> float:
    if not planned_granularities:
        return 0.0
    planned = set(planned_granularities)
    verified = {a.requested_granularity for a in _verified_attempts(attempts)}
    return round(len(planned & verified) / len(planned), 4)


def _universe_coverage(
    attempts: Sequence[CapabilityProbeAttempt],
    planned_instruments: Sequence[str],
) -> float:
    if not planned_instruments:
        return 0.0
    planned = set(planned_instruments)
    verified = {a.instrument_native for a in _verified_attempts(attempts)}
    return round(len(planned & verified) / len(planned), 4)


def _pagination_coverage(attempts: Sequence[CapabilityProbeAttempt]) -> float:
    if any(
        _has_failure(attempts, cls)
        for cls in (
            ProbeFailureClass.F_PAGINATION_LOOP,
            ProbeFailureClass.F_PAGINATION_TRUNCATED,
            ProbeFailureClass.F_ARCHIVE_NOT_FOUND,
        )
    ):
        return 0.0
    verified = _verified_attempts(attempts)
    if not verified:
        return 0.0
    if any(a.pagination_detected and a.pagination_complete is True for a in verified):
        return 1.0
    if any(a.pagination_detected for a in verified):
        return 0.75
    return 0.5  # no pagination observed (latest-only surface): n/a-ish, not proven


def _timestamp_clarity(attempts: Sequence[CapabilityProbeAttempt]) -> float:
    if _has_failure(attempts, ProbeFailureClass.F_TIMESTAMP_UNCLEAR):
        return 0.0
    verified = _verified_attempts(attempts)
    if not verified:
        return 0.0
    if any(a.native_timestamp_fields for a in verified):
        return 0.75
    if _has_failure(attempts, ProbeFailureClass.F_METHOD_UNCLEAR):
        return 0.25
    return 0.25


def _unit_clarity(attempts: Sequence[CapabilityProbeAttempt]) -> float:
    if _has_failure(attempts, ProbeFailureClass.F_UNIT_UNCLEAR):
        return 0.0
    verified = _verified_attempts(attempts)
    if not verified:
        return 0.0
    if any(a.native_units_summary for a in verified):
        return 0.75
    return 0.25


def _accessibility(free_only_status: FreeOnlyStatus) -> float:
    """A dimension (03 §8).  PAID_BLOCKED is a hard zero — never overridable."""
    return {
        FreeOnlyStatus.FREE_COMPLIANT: 1.0,
        FreeOnlyStatus.FREE_LIMITED: 0.75,
        FreeOnlyStatus.UNVERIFIED: 0.5,
        FreeOnlyStatus.PAID_BLOCKED: 0.0,
    }[free_only_status]


def _reproducibility(attempts: Sequence[CapabilityProbeAttempt]) -> float:
    verified = _verified_attempts(attempts)
    if not verified:
        return 0.0
    if any(a.request_fingerprint for a in verified):
        return 1.0
    return 0.5


def _semantic_fit(semantic_equivalence_class: SemanticEquivalence | None) -> float:
    return {
        SemanticEquivalence.EXACT_EQUIVALENT: 1.0,
        SemanticEquivalence.NORMALIZABLE_COMPARABLE: 0.75,
        SemanticEquivalence.CORROBORATION_ONLY: 0.5,
        SemanticEquivalence.NOT_COMPARABLE: 0.0,
        None: 0.5,  # unassessed is not assumed equivalent
    }[semantic_equivalence_class]


def _continuity(attempts: Sequence[CapabilityProbeAttempt]) -> float:
    if any(
        _has_failure(attempts, cls)
        for cls in (
            ProbeFailureClass.F_GAP_EXCESS,
            ProbeFailureClass.F_DUPLICATE_EXCESS,
            ProbeFailureClass.F_PAYLOAD_CORRUPT,
            ProbeFailureClass.F_CHECKSUM_FAILURE,
        )
    ):
        return 0.0
    return 0.75 if _verified_attempts(attempts) else 0.0


def compute_coverage_vector(
    attempts: Sequence[CapabilityProbeAttempt],
    *,
    free_only_status: FreeOnlyStatus,
    semantic_equivalence_class: SemanticEquivalence | None = None,
    planned_granularities: Sequence[Granularity] = (),
    planned_instruments: Sequence[str] = (),
) -> CoverageVector:
    """Compute the normalized coverage vector for one provider/sensor scope.

    A == 0 (paid), T == 0 (PIT unusable) and S == 0 (not comparable) are hard
    blockers at the scoring layer — a high composite never overrides them
    (T2-COV-02 / 03 §9).
    """
    return CoverageVector(
        H=_historical_coverage(attempts),
        G=_granularity_coverage(attempts, planned_granularities),
        U=_universe_coverage(attempts, planned_instruments),
        P=_pagination_coverage(attempts),
        T=_timestamp_clarity(attempts),
        N=_unit_clarity(attempts),
        A=_accessibility(free_only_status),
        R=_reproducibility(attempts),
        S=_semantic_fit(semantic_equivalence_class),
        Q=_continuity(attempts),
    )


def _era_status_map(attempts: Sequence[CapabilityProbeAttempt]) -> dict[str, CapabilityStatus]:
    """Per-era outcome: a scope verifies for an era iff it has a verified sample."""
    statuses: dict[str, CapabilityStatus] = {}
    for era in list(HISTORICAL_ERAS) + [RECENT_CONTROL_ERA]:
        era_attempts = [a for a in attempts if a.era_hint == era]
        if not era_attempts:
            continue
        if any(a.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE for a in era_attempts):
            statuses[era] = CapabilityStatus.VERIFIED
        else:
            # fail-closed: dominant failure class for that era
            failures = sorted({a.error_class for a in era_attempts if a.error_class})
            if ProbeFailureClass.F_PRE_LISTING in failures:
                statuses[era] = CapabilityStatus.UNVERIFIED  # PRE_LISTING is distinct
            elif any(f in {ProbeFailureClass.F_ACCESS_PAYMENT} for f in failures):
                statuses[era] = CapabilityStatus.PAYMENT_BLOCKED
            elif any(f in {ProbeFailureClass.F_ACCESS_GEO} for f in failures):
                statuses[era] = CapabilityStatus.GEO_BLOCKED
            elif any(f in {ProbeFailureClass.F_ACCESS_AUTH} for f in failures):
                statuses[era] = CapabilityStatus.AUTH_BLOCKED
            elif any(
                f
                in {
                    ProbeFailureClass.F_HISTORY_TRUNCATED,
                    ProbeFailureClass.F_EMPTY_VALID_WINDOW,
                }
                for f in failures
            ):
                statuses[era] = CapabilityStatus.HISTORY_BLOCKED
            elif any(
                f
                in {
                    ProbeFailureClass.F_TIMESTAMP_UNCLEAR,
                    ProbeFailureClass.F_UNIT_UNCLEAR,
                    ProbeFailureClass.F_METHOD_UNCLEAR,
                }
                for f in failures
            ):
                statuses[era] = CapabilityStatus.SEMANTICALLY_UNUSABLE
            elif ProbeFailureClass.F_UNSUPPORTED_SENSOR in failures:
                statuses[era] = CapabilityStatus.UNSUPPORTED
            elif any(
                f
                in {
                    ProbeFailureClass.F_NETWORK_TIMEOUT,
                    ProbeFailureClass.F_SERVER_5XX,
                    ProbeFailureClass.F_ACCESS_RATE_LIMIT,
                }
                for f in failures
            ):
                statuses[era] = CapabilityStatus.TRANSIENT_FAILURE
            else:
                statuses[era] = CapabilityStatus.UNVERIFIED
    return statuses


def synthesize_coverage(
    *,
    provider_id: str,
    sensor_family: SensorFamily,
    venue_market: str,
    access_mode: AccessMode,
    attempts: Sequence[CapabilityProbeAttempt],
    free_only_status: FreeOnlyStatus,
    semantic_equivalence_class: SemanticEquivalence | None = None,
    planned_granularities: Sequence[Granularity] = (),
    planned_instruments: Sequence[str] = (),
    provider_role: ProviderRole = ProviderRole.REFERENCE_ONLY,
) -> ProviderSensorCoverage:
    """Build the per-scope coverage row (05 §3).  Triage score attached only
    as metadata; it never overrides hard blockers (checked at scoring layer)."""
    verified_dates = [
        a.requested_start
        for a in attempts
        if a.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    ]
    vector = compute_coverage_vector(
        attempts,
        free_only_status=free_only_status,
        semantic_equivalence_class=semantic_equivalence_class,
        planned_granularities=planned_granularities,
        planned_instruments=planned_instruments,
    )
    return ProviderSensorCoverage.model_validate(
        {
            "provider_id": provider_id,
            "sensor_family": sensor_family,
            "venue_market": venue_market,
            "instrument_scope": list(planned_instruments),
            "access_mode": access_mode,
            "era_status": _era_status_map(attempts),
            "earliest_verified_history": min(verified_dates) if verified_dates else None,
            "latest_verified_history": max(verified_dates) if verified_dates else None,
            "granularity_scope": sorted(
                {a.requested_granularity for a in attempts},
                key=lambda g: g.value,
            ),
            "PIT_readiness": derive_pit_readiness(attempts),
            "unit_clarity": vector.N,
            "pagination_quality": vector.P,
            "schema_stability": None,
            "semantic_equivalence_class": semantic_equivalence_class,
            "evidence_level": derive_evidence_level(attempts),
            "provider_role": provider_role,
            "capability_score": None,  # scoring layer computes with hard-block overrides
            "promotion_eligible": False,  # scoring layer decides (fail closed)
            "blocking_reason": None,
        }
    )


@dataclass(frozen=True)
class VerifiedSource:
    """One verified provider/sensor source for redundancy computation (03 §17)."""

    provider_id: str
    venue_market: str
    evidence_class: EvidenceSourceClass
    pit_ready: bool = False


def compute_sensor_redundancy(
    sensor_family: SensorFamily,
    sources: Sequence[VerifiedSource],
) -> SensorRedundancySummary:
    """Independence-aware redundancy for one sensor family (T2-COV-03..05).

    Only first-party runtime/archive sources at distinct venues count as
    independent.  Aggregators and community sources contribute diversity
    counts but never increment the independent-venue count — three sources
    derived from one upstream exchange are not three independent venues.
    """
    first_party = [
        s for s in sources if s.evidence_class in INDEPENDENT_CLASSES
    ]
    independent_venues = {s.venue_market for s in first_party}
    independent_count = len(independent_venues)
    if independent_count == 0:
        redundancy = RedundancyClass.R0_NONE
    elif independent_count == 1:
        redundancy = RedundancyClass.R1_SINGLE_INDEPENDENT
    elif independent_count == 2:
        redundancy = RedundancyClass.R2_TWO_INDEPENDENT
    else:
        redundancy = RedundancyClass.R3_THREE_PLUS_INDEPENDENT

    if not sources:
        gap_status = "UNVERIFIED"
    elif independent_count >= 2:
        gap_status = "ADEQUATE"
    elif independent_count == 1:
        gap_status = "SINGLE_SOURCE"
    else:
        gap_status = "INSUFFICIENT"

    return SensorRedundancySummary.model_validate(
        {
            "sensor_family": sensor_family,
            "verified_provider_count": len(sources),
            "verified_venues": sorted({s.venue_market for s in sources}),
            "redundancy_class": redundancy,
            "first_party_count": len(first_party),
            "aggregator_count": sum(
                1
                for s in sources
                if s.evidence_class is EvidenceSourceClass.THIRD_PARTY_AGGREGATOR
            ),
            "community_count": sum(
                1
                for s in sources
                if s.evidence_class
                in {
                    EvidenceSourceClass.COMMUNITY_ARCHIVE,
                    EvidenceSourceClass.COMMUNITY_RECONSTRUCTION,
                }
            ),
            "PIT_ready_provider_count": sum(1 for s in sources if s.pit_ready),
            "gap_status": gap_status,
            "notes": (
                f"{len(independent_venues)} independent first-party venue(s); "
                "aggregators/community sources counted for diversity only"
            ),
        }
    )
