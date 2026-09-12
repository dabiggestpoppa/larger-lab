"""Capability scoring and promotion eligibility (03 §9, §19 / T2-COV-02).

The composite score is a TRIAGE convenience only — it never decides science
(03 §21, do-not-average rule).  Hard blockers dominate: a paid source, an
unusable-timestamp source or a non-comparable source can never be promoted,
regardless of composite score (T2-COV-02).  Promotion eligibility is the
fail-closed gate that Bloc 3 handoff consumes (03 §19, 04 §27).
"""

from __future__ import annotations

from .coverage import CoverageVector
from .enums import EvidenceLevel, FreeOnlyStatus, PITReadiness

#: Initial planning-default weighting (03 §9).  Not scientific truth.
CAPABILITY_WEIGHTS: dict[str, float] = {
    "H": 0.20,
    "G": 0.10,
    "U": 0.10,
    "P": 0.10,
    "T": 0.10,
    "N": 0.10,
    "A": 0.10,
    "R": 0.10,
    "S": 0.05,
    "Q": 0.05,
}

HARD_BLOCKER_RULES: tuple[tuple[str, float, str], ...] = (
    ("A", 0.0, "A == 0: paid/payment/stake/transaction access cannot be a required runtime source"),
    ("T", 0.0, "T == 0: timestamps unusable for PIT — cannot be PIT-ready"),
    ("S", 0.0, "S == 0: not comparable to the canonical sensor contract"),
)


def capability_score(vector: CoverageVector) -> float:
    """Composite triage score (03 §9).  Rounding to 4 decimals for stability.

    Hard blockers still apply at promotion time — this number never overrides
    a zeroed A/T/S dimension.
    """
    total = sum(
        weight * float(getattr(vector, dim)) for dim, weight in CAPABILITY_WEIGHTS.items()
    )
    return round(total, 4)


def hard_blockers(vector: CoverageVector) -> list[str]:
    """List of blocking dimensions (empty list means no hard blocker)."""
    return [
        reason
        for dim, threshold, reason in HARD_BLOCKER_RULES
        if float(getattr(vector, dim)) == threshold
    ]


def is_blocked(vector: CoverageVector) -> bool:
    """True when any hard blocker applies (fail closed)."""
    return bool(hard_blockers(vector))


def evaluate_promotion(
    *,
    free_only_status: FreeOnlyStatus,
    recent_control_verified: bool,
    evidence_level: EvidenceLevel,
    pit_readiness: PITReadiness,
    unit_clarity: float | None,
    reproducible_request: bool,
    blocking_contradictions: int = 0,
) -> tuple[bool, list[str]]:
    """Fail-closed promotion gate (03 §19).

    Every mandatory gate must pass; the returned reasons name each unmet gate
    so the decision is auditable.  Returns (eligible, unmet_reasons).
    """
    unmet: list[str] = []

    if free_only_status is FreeOnlyStatus.PAID_BLOCKED:
        unmet.append("free_only = PAID_BLOCKED (hard)")
    elif free_only_status is FreeOnlyStatus.UNVERIFIED:
        unmet.append("free_only = UNVERIFIED (cannot promote)")
    if not recent_control_verified:
        unmet.append("recent_control = FAIL (no runtime verification)")
    if EvidenceLevel.E0_CLAIM_ONLY in (evidence_level,):
        unmet.append("runtime_evidence < E2 (claim only)")
    elif EvidenceLevel.E1_DOC_CONTRACT_VERIFIED in (evidence_level,):
        unmet.append("runtime_evidence = E1 (docs only)")
    if pit_readiness is PITReadiness.NOT_PIT_READY:
        unmet.append("PIT_readiness = NOT_PIT_READY")
    if unit_clarity is None or unit_clarity == 0.0:
        unmet.append("native_units = UNKNOWN/UNCLEAR (T2-SEM-03)")
    if not reproducible_request:
        unmet.append("reproducible_request = NO")
    if blocking_contradictions > 0:
        unmet.append(f"{blocking_contradictions} blocking contradiction(s) (T2-CONTRA-02)")

    eligible = len(unmet) == 0
    return eligible, unmet
