"""Capability scoring + promotion gate tests (03 §9, §19 / T2-COV-02,
T2-CONTRA-02, T2-SEM-03)."""

from __future__ import annotations

from crypto_sensor_fabric.probes.coverage import CoverageVector
from crypto_sensor_fabric.probes.enums import (
    EvidenceLevel,
    FreeOnlyStatus,
    PITReadiness,
)
from crypto_sensor_fabric.probes.scoring import (
    capability_score,
    evaluate_promotion,
    hard_blockers,
    is_blocked,
)


def _vector(**overrides: float) -> CoverageVector:
    values = {"H": 1.0, "G": 1.0, "U": 1.0, "P": 1.0, "T": 1.0, "N": 1.0, "A": 1.0, "R": 1.0, "S": 1.0, "Q": 1.0}
    values.update(overrides)
    return CoverageVector(**values)


def test_composite_score_full_vector_is_1():
    assert capability_score(_vector()) == 1.0


def test_composite_score_matches_weighting():
    # only H and A contribute
    vector = _vector(G=0.0, U=0.0, P=0.0, T=0.0, N=0.0, R=0.0, S=0.0, Q=0.0)
    assert capability_score(vector) == 0.30  # 0.20 H + 0.10 A


def test_composite_is_triage_only_and_never_overrides_hard_blocker():
    # A == 0 (paid) with everything else perfect: score is high but blocked
    vector = _vector(A=0.0)
    assert capability_score(vector) == 0.90
    assert is_blocked(vector)
    assert hard_blockers(vector) == [
        "A == 0: paid/payment/stake/transaction access cannot be a required runtime source"
    ]


def test_hard_blocker_t_zero_blocks_pit():
    vector = _vector(T=0.0)
    assert is_blocked(vector)
    assert any("PIT" in reason for reason in hard_blockers(vector))


def test_hard_blocker_s_zero_blocks_canonical_mapping():
    vector = _vector(S=0.0)
    assert is_blocked(vector)
    assert any("canonical sensor" in reason for reason in hard_blockers(vector))


def test_no_hard_blockers_when_all_dimensions_positive():
    assert not is_blocked(_vector())
    assert hard_blockers(_vector()) == []


# ---------------------------------------------------------------------------
# Promotion gate (03 §19) — fail closed
# ---------------------------------------------------------------------------


def test_promotion_all_gates_pass():
    eligible, unmet = evaluate_promotion(
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
        recent_control_verified=True,
        evidence_level=EvidenceLevel.E3_HISTORICAL_CHECKPOINT_VERIFIED,
        pit_readiness=PITReadiness.PIT_READY_WITH_METHOD_VERSION,
        unit_clarity=0.75,
        reproducible_request=True,
    )
    assert eligible is True
    assert unmet == []


def test_promotion_paid_blocked_fails():
    eligible, unmet = evaluate_promotion(
        free_only_status=FreeOnlyStatus.PAID_BLOCKED,
        recent_control_verified=True,
        evidence_level=EvidenceLevel.E4_MULTI_ERA_VERIFIED,
        pit_readiness=PITReadiness.PIT_READY,
        unit_clarity=1.0,
        reproducible_request=True,
    )
    assert eligible is False
    assert any("PAID_BLOCKED" in reason for reason in unmet)


def test_promotion_unverified_free_only_cannot_promote():
    eligible, _ = evaluate_promotion(
        free_only_status=FreeOnlyStatus.UNVERIFIED,
        recent_control_verified=True,
        evidence_level=EvidenceLevel.E4_MULTI_ERA_VERIFIED,
        pit_readiness=PITReadiness.PIT_READY,
        unit_clarity=1.0,
        reproducible_request=True,
    )
    assert eligible is False


def test_promotion_no_recent_control_fails():
    eligible, unmet = evaluate_promotion(
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
        recent_control_verified=False,
        evidence_level=EvidenceLevel.E3_HISTORICAL_CHECKPOINT_VERIFIED,
        pit_readiness=PITReadiness.PIT_READY,
        unit_clarity=1.0,
        reproducible_request=True,
    )
    assert eligible is False
    assert any("recent_control" in reason for reason in unmet)


def test_promotion_claim_only_evidence_fails():
    eligible, unmet = evaluate_promotion(
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
        recent_control_verified=True,
        evidence_level=EvidenceLevel.E0_CLAIM_ONLY,
        pit_readiness=PITReadiness.PIT_READY,
        unit_clarity=1.0,
        reproducible_request=True,
    )
    assert eligible is False
    assert any("E2" in reason for reason in unmet)


def test_promotion_docs_only_evidence_fails():
    eligible, _ = evaluate_promotion(
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
        recent_control_verified=True,
        evidence_level=EvidenceLevel.E1_DOC_CONTRACT_VERIFIED,
        pit_readiness=PITReadiness.PIT_READY,
        unit_clarity=1.0,
        reproducible_request=True,
    )
    assert eligible is False


def test_promotion_not_pit_ready_fails():
    eligible, unmet = evaluate_promotion(
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
        recent_control_verified=True,
        evidence_level=EvidenceLevel.E4_MULTI_ERA_VERIFIED,
        pit_readiness=PITReadiness.NOT_PIT_READY,
        unit_clarity=1.0,
        reproducible_request=True,
    )
    assert eligible is False
    assert any("NOT_PIT_READY" in reason for reason in unmet)


def test_promotion_unknown_units_fails():
    eligible, unmet = evaluate_promotion(
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
        recent_control_verified=True,
        evidence_level=EvidenceLevel.E4_MULTI_ERA_VERIFIED,
        pit_readiness=PITReadiness.PIT_READY,
        unit_clarity=None,
        reproducible_request=True,
    )
    assert eligible is False
    assert any("native_units" in reason for reason in unmet)


def test_promotion_not_reproducible_fails():
    eligible, _ = evaluate_promotion(
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
        recent_control_verified=True,
        evidence_level=EvidenceLevel.E4_MULTI_ERA_VERIFIED,
        pit_readiness=PITReadiness.PIT_READY,
        unit_clarity=1.0,
        reproducible_request=False,
    )
    assert eligible is False


def test_promotion_blocking_contradiction_fails():
    eligible, unmet = evaluate_promotion(
        free_only_status=FreeOnlyStatus.FREE_COMPLIANT,
        recent_control_verified=True,
        evidence_level=EvidenceLevel.E4_MULTI_ERA_VERIFIED,
        pit_readiness=PITReadiness.PIT_READY,
        unit_clarity=1.0,
        reproducible_request=True,
        blocking_contradictions=1,
    )
    assert eligible is False
    assert any("blocking contradiction" in reason for reason in unmet)
