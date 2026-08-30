"""Immutable probe evidence + capability claim synthesis (03 §1-4, §12, §14).

I03 scope — evidence records, evidence-level derivation, PIT readiness
classification and normalized capability claims.  This layer is the boundary
between raw attempt records and the coverage/scoring layers:

    CapabilityProbeAttempt (immutable, one per probe)
        -> CapabilityProbeEvidence (immutable, grouped, source-classed)
        -> CapabilityClaim (normalized, versioned capability statement)

Invariants (04 §25 / T2-HIST-04, T2-CONTRA-03):

- evidence is never overwritten; later observations may supersede a claim
  (claim_version / supersedes_claim_id) but never erase prior evidence
- claimed history and verified history remain separate fields
- earliest verified history never predates actual successful evidence
- an unattempted cell is never serialized as UNSUPPORTED
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..contracts.base import normalize_utc_datetimes
from ..contracts.enums import SemanticEquivalence, SensorFamily
from .enums import (
    AccessMode,
    CapabilityStatus,
    EvidenceLevel,
    EvidenceSourceClass,
    Granularity,
    HistoricalBoundaryConfidence,
    PITReadiness,
    ProbeFailureClass,
    ResponseStatusClass,
)
from .models import CapabilityClaim, CapabilityProbeAttempt
from .planner import RECENT_CONTROL_ERA

#: Evidence-source classes that represent the venue's own words (first party).
FIRST_PARTY_CLASSES: frozenset[EvidenceSourceClass] = frozenset(
    {
        EvidenceSourceClass.FIRST_PARTY_RUNTIME,
        EvidenceSourceClass.FIRST_PARTY_ARCHIVE,
        EvidenceSourceClass.FIRST_PARTY_DOCUMENTATION,
    }
)

#: Hard access/support classes that dominate claim status (fail closed).
_ACCESS_DOMINANT: tuple[tuple[ProbeFailureClass, CapabilityStatus], ...] = (
    (ProbeFailureClass.F_ACCESS_PAYMENT, CapabilityStatus.PAYMENT_BLOCKED),
    (ProbeFailureClass.F_ACCESS_GEO, CapabilityStatus.GEO_BLOCKED),
    (ProbeFailureClass.F_ACCESS_AUTH, CapabilityStatus.AUTH_BLOCKED),
    (ProbeFailureClass.F_UNSUPPORTED_SENSOR, CapabilityStatus.UNSUPPORTED),
)

#: History-retention failures: current data may exist, deep history does not.
_HISTORY_RETENTION: frozenset[ProbeFailureClass] = frozenset(
    {
        ProbeFailureClass.F_HISTORY_TRUNCATED,
        ProbeFailureClass.F_EMPTY_VALID_WINDOW,
    }
)

#: Semantic failures: payload exists but cannot be made PIT/unit/method reliable.
_SEMANTIC_FAILURES: frozenset[ProbeFailureClass] = frozenset(
    {
        ProbeFailureClass.F_TIMESTAMP_UNCLEAR,
        ProbeFailureClass.F_UNIT_UNCLEAR,
        ProbeFailureClass.F_METHOD_UNCLEAR,
        ProbeFailureClass.F_PAYLOAD_CORRUPT,
        ProbeFailureClass.F_CHECKSUM_FAILURE,
        ProbeFailureClass.F_SCHEMA_CHANGED,
    }
)

#: Transient failures: capability remains unresolved.
_TRANSIENT: frozenset[ProbeFailureClass] = frozenset(
    {
        ProbeFailureClass.F_NETWORK_TIMEOUT,
        ProbeFailureClass.F_NETWORK_DNS,
        ProbeFailureClass.F_NETWORK_TLS,
        ProbeFailureClass.F_SERVER_5XX,
        ProbeFailureClass.F_ACCESS_RATE_LIMIT,
        ProbeFailureClass.F_QUOTA_EXHAUSTED,
    }
)


class CapabilityProbeEvidence(BaseModel):
    """Immutable evidence record for one probe scope (03 §14 / 05 §1).

    Groups one or more attempts (retries/pages) of the same probe into a
    single source-classed, checkpoint-labelled evidence object.  Every claim
    references evidence_ids; evidence is never deleted or rewritten.
    """

    model_config = ConfigDict(extra="forbid")

    evidence_id: str = Field(min_length=1)
    probe_run_id: str = Field(min_length=1)
    provider_id: str = Field(min_length=1)
    sensor_family: SensorFamily
    venue_market: str = Field(min_length=1)
    instrument_native: str = Field(min_length=1)
    requested_granularity: Granularity
    era: str | None = None
    evidence_level: EvidenceLevel = EvidenceLevel.E0_CLAIM_ONLY
    evidence_class: EvidenceSourceClass = EvidenceSourceClass.FIRST_PARTY_RUNTIME
    response_status_class: ResponseStatusClass = ResponseStatusClass.NOT_ATTEMPTED
    failure_class: ProbeFailureClass | None = None
    attempt_ids: list[str] = Field(default_factory=list)
    payload_schema_fingerprint: str | None = None
    observed_at: datetime
    summary: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _failed_evidence_carries_failure_class(self) -> CapabilityProbeEvidence:
        if (
            self.response_status_class is ResponseStatusClass.FAILED
            and self.failure_class is None
        ):
            raise ValueError("failed evidence must carry a failure_class")
        return self

    @model_validator(mode="after")
    def _normalize_timestamps(self) -> CapabilityProbeEvidence:
        return normalize_utc_datetimes(self)  # type: ignore[return-value]


def deterministic_json(value: Any) -> str:
    """Deterministic compact JSON for identical normalized content.

    Recursively sorts mapping keys so serialization does not depend on
    insertion order (T2-MODEL-03).  Enums and datetimes serialize by value.
    """

    def _sorted(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {str(k): _sorted(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
        if isinstance(value, list):
            return [_sorted(item) for item in value]
        if isinstance(value, tuple):
            return [_sorted(item) for item in value]
        if hasattr(value, "value"):  # enums
            return value.value
        if isinstance(value, datetime):
            return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
        return value

    return json.dumps(_sorted(value), separators=(",", ":"), default=str, sort_keys=True)


def evidence_from_attempts(
    attempts: Sequence[CapabilityProbeAttempt],
    *,
    evidence_id: str,
    probe_run_id: str,
    evidence_class: EvidenceSourceClass,
    observed_at: datetime | None = None,
    summary: Mapping[str, Any] | None = None,
) -> CapabilityProbeEvidence:
    """Build one immutable evidence record from one probe's attempts.

    The first attempt defines the scope (provider/sensor/instrument/granularity/
    era); every attempt id is preserved for traceability.  Requires at least
    one attempt — a probe always emits evidence, even on failure (T2-MODEL-05).
    """
    if not attempts:
        raise ValueError("evidence_from_attempts requires at least one attempt")
    first = attempts[0]
    last = attempts[-1]
    era = first.era_hint
    return CapabilityProbeEvidence.model_validate(
        {
            "evidence_id": evidence_id,
            "probe_run_id": probe_run_id,
            "provider_id": first.provider_id,
            "sensor_family": first.sensor_family,
            "venue_market": first.venue_market,
            "instrument_native": first.instrument_native,
            "requested_granularity": first.requested_granularity,
            "era": era,
            "evidence_level": EvidenceLevel.E0_CLAIM_ONLY,  # raised by synthesis
            "evidence_class": evidence_class,
            "response_status_class": last.response_status_class,
            "failure_class": last.error_class,
            "attempt_ids": [a.probe_id for a in attempts],
            "payload_schema_fingerprint": last.payload_schema_fingerprint,
            "observed_at": observed_at or datetime.now(UTC),
            "summary": dict(summary or {}),
        }
    )


def derive_evidence_level(
    attempts: Sequence[CapabilityProbeAttempt],
    *,
    pagination_characterized: bool = False,
    timestamp_semantics_clear: bool = False,
    unit_semantics_clear: bool = False,
) -> EvidenceLevel:
    """Evidence ladder from observed attempts (03 §1 / F2.5).

    Never upgrades beyond what was actually observed: E1 (doc contract) is
    only reachable by explicit declaration, never inferred from attempts.
    """
    verified = [
        a for a in attempts if a.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    ]
    if not verified:
        return EvidenceLevel.E0_CLAIM_ONLY
    recent_verified = any(a.era_hint == RECENT_CONTROL_ERA for a in verified)
    historical_eras = {
        a.era_hint
        for a in verified
        if a.era_hint is not None and a.era_hint != RECENT_CONTROL_ERA
    }
    if historical_eras:
        if (
            len(historical_eras) >= 2
            and pagination_characterized
            and timestamp_semantics_clear
            and unit_semantics_clear
        ):
            return EvidenceLevel.E5_REPRODUCIBLE_COVERAGE_VERIFIED
        if len(historical_eras) >= 2:
            return EvidenceLevel.E4_MULTI_ERA_VERIFIED
        return EvidenceLevel.E3_HISTORICAL_CHECKPOINT_VERIFIED
    if recent_verified:
        return EvidenceLevel.E2_LIVE_RECENT_VERIFIED
    return EvidenceLevel.E0_CLAIM_ONLY


def derive_pit_readiness(
    attempts: Sequence[CapabilityProbeAttempt],
) -> PITReadiness:
    """PIT readiness from observed timestamp semantics (03 §10 / T2-SEM-02).

    Raw timestamp semantics sufficient + explicit native timestamp fields
    observed -> PIT_READY_WITH_METHOD_VERSION (canonical normalization is
    Bloc 5).  Any timestamp/method ambiguity -> NOT_PIT_READY (fail closed).
    """
    semantic_failures = any(
        a.error_class
        in {
            ProbeFailureClass.F_TIMESTAMP_UNCLEAR,
            ProbeFailureClass.F_METHOD_UNCLEAR,
        }
        for a in attempts
    )
    if semantic_failures:
        return PITReadiness.NOT_PIT_READY
    verified_with_timestamps = [
        a
        for a in attempts
        if a.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
        and a.native_timestamp_fields
    ]
    if verified_with_timestamps:
        return PITReadiness.PIT_READY_WITH_METHOD_VERSION
    return PITReadiness.NOT_PIT_READY


def _has(attempts: Sequence[CapabilityProbeAttempt], cls: ProbeFailureClass) -> bool:
    return any(a.error_class is cls for a in attempts)


def _derive_status(
    attempts: Sequence[CapabilityProbeAttempt],
    *,
    known_limitations: Sequence[str],
) -> CapabilityStatus:
    """Fail-closed status derivation (03 §4).  Hard blocks dominate."""
    if not attempts:
        return CapabilityStatus.UNVERIFIED
    for failure_class, status in _ACCESS_DOMINANT:
        if _has(attempts, failure_class):
            return status
    if _has(attempts, ProbeFailureClass.F_ENDPOINT_REMOVED) or _has(
        attempts, ProbeFailureClass.F_ARCHIVE_NOT_FOUND
    ):
        return CapabilityStatus.ACCESS_BLOCKED
    if _has(attempts, ProbeFailureClass.F_SYMBOL_NOT_FOUND):
        return CapabilityStatus.UNVERIFIED  # instrument-specific, not provider failure
    if any(_has(attempts, cls) for cls in _SEMANTIC_FAILURES):
        return CapabilityStatus.SEMANTICALLY_UNUSABLE
    verified = [
        a for a in attempts if a.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    ]
    if not verified:
        history_retention = any(_has(attempts, cls) for cls in _HISTORY_RETENTION)
        if history_retention:
            return CapabilityStatus.HISTORY_BLOCKED
        if _has(attempts, ProbeFailureClass.F_PRE_LISTING):
            return CapabilityStatus.UNVERIFIED  # PRE_LISTING, not a provider verdict
        if any(_has(attempts, cls) for cls in _TRANSIENT):
            return CapabilityStatus.TRANSIENT_FAILURE
        return CapabilityStatus.UNVERIFIED
    historical_verified = any(
        a.era_hint is not None and a.era_hint != RECENT_CONTROL_ERA for a in verified
    )
    if not historical_verified:
        if any(_has(attempts, cls) for cls in _HISTORY_RETENTION):
            return CapabilityStatus.HISTORY_BLOCKED
        return CapabilityStatus.VERIFIED_CURRENT_ONLY
    if known_limitations:
        return CapabilityStatus.VERIFIED_LIMITED
    return CapabilityStatus.VERIFIED


def synthesize_claim(
    *,
    claim_id: str,
    provider_id: str,
    sensor_family: SensorFamily,
    venue_market: str,
    access_mode: AccessMode,
    attempts: Sequence[CapabilityProbeAttempt],
    evidence_class: EvidenceSourceClass = EvidenceSourceClass.FIRST_PARTY_RUNTIME,
    instrument_scope: Sequence[str] | None = None,
    granularity_scope: Sequence[Granularity] | None = None,
    earliest_claimed_history: datetime | None = None,
    history_boundary_confidence: HistoricalBoundaryConfidence = (
        HistoricalBoundaryConfidence.UNKNOWN
    ),
    semantic_equivalence_class: SemanticEquivalence | None = None,
    known_gaps: Sequence[str] | None = None,
    limitations: Sequence[str] | None = None,
    pagination_characterized: bool = False,
    timestamp_semantics_clear: bool = False,
    unit_semantics_clear: bool = False,
    claim_version: int = 1,
    supersedes_claim_id: str | None = None,
) -> CapabilityClaim:
    """Synthesize a normalized capability claim from probe attempts.

    Claimed and verified history stay separate (T2-HIST-05); verified history
    is derived only from VERIFIED_SAMPLE attempts (T2-HIST-04).  An unattempted
    scope yields UNVERIFIED, never UNSUPPORTED (T2-REPORT-04).
    """
    status = _derive_status(attempts, known_limitations=limitations or [])
    verified_dates = [
        a.requested_start
        for a in attempts
        if a.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
    ]
    earliest_verified = min(verified_dates) if verified_dates else None
    latest_verified = max(verified_dates) if verified_dates else None
    evidence_level = derive_evidence_level(
        attempts,
        pagination_characterized=pagination_characterized,
        timestamp_semantics_clear=timestamp_semantics_clear,
        unit_semantics_clear=unit_semantics_clear,
    )
    return CapabilityClaim.model_validate(
        {
            "claim_id": claim_id,
            "provider_id": provider_id,
            "sensor_family": sensor_family,
            "venue_market": venue_market,
            "instrument_scope": list(instrument_scope or []),
            "granularity_scope": list(granularity_scope or []),
            "access_mode": access_mode,
            "capability_status": status,
            "evidence_level": evidence_level,
            "earliest_claimed_history": earliest_claimed_history,
            "earliest_verified_history": earliest_verified,
            "history_boundary_confidence": history_boundary_confidence,
            "latest_verified_history": latest_verified,
            "PIT_readiness": derive_pit_readiness(attempts),
            "semantic_equivalence_class": semantic_equivalence_class,
            # free_only_status defaults to UNVERIFIED; the coverage layer
            # promotes it from access evidence (03 §8 A dimension).
            "known_gaps": list(known_gaps or []),
            "limitations": list(limitations or []),
            "evidence_ids": [],
            "claim_version": claim_version,
            "supersedes_claim_id": supersedes_claim_id,
        }
    )
