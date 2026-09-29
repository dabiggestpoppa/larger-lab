"""MF-B4 — protocol freeze, sealed access, capability vectors, negative results."""

from __future__ import annotations

import dataclasses

import pytest

from foundry.constitution import ReproducibilityClaim
from foundry.core import FrozenMap, PolicyBlocked, Unauthorized
from foundry.enums import (
    BenchmarkStatus,
    CapabilityEvidenceState,
    ContaminationClass,
    EvaluationTier,
    ExposureType,
    ReproducibilityClass,
    SubjectKind,
    TerminalConclusion,
)
from foundry.evaluation import (
    EvaluationObservation,
    EvaluationRun,
    NegativeKnowledgeStore,
    NegativeResult,
    ReproductionEvidence,
    SealedEvaluationStore,
    SealedPayload,
    assert_conclusion_supported,
    assert_no_master_score,
    assert_protocol_unchanged,
    assess_capability,
    credit_assessment,
    elevate_tier,
    freeze_protocol,
    submit_for_oce_review,
)
from foundry.fixtures import load_benchmark, load_protocol


def _frozen(tier: EvaluationTier = EvaluationTier.PROMOTION):
    protocol = dataclasses.replace(load_protocol(), tier=tier)
    return freeze_protocol(
        protocol,
        registrar="test",
        freeze_reason="criteria frozen before outcomes",
        candidate_outcomes_observed=False,
        actor_is_builder=False,
    )


def _run(
    *,
    frozen=None,
    subject_kind: SubjectKind = SubjectKind.COGNITIVE_RUNTIME,
    framework: str = "fixture-framework",
    contamination: ContaminationClass = ContaminationClass.C0_NO_OBSERVED_OVERLAP,
    item_count: int = 6,
    seeds: int = 2,
    failures: tuple[str, ...] = (),
) -> EvaluationRun:
    return EvaluationRun(
        run_id="RUN-1",
        frozen_protocol=frozen or _frozen(),
        subject_kind=subject_kind,
        subject_id="SUBJ-1",
        observations=(
            EvaluationObservation("accuracy", 0.71, item_count=item_count, seed=1),
            EvaluationObservation("calibration_error", 0.08, item_count=item_count, seed=2),
        ),
        framework=framework,
        framework_version="0.1",
        runtime_identity="sha256:runtime",
        contamination_grade=contamination,
        started_utc="2026-01-03T00:00:00Z",
        completed_utc="2026-01-03T01:00:00Z",
        seeds_used=seeds,
        failures=failures,
    )


def _reproducibility() -> ReproducibilityClaim:
    return ReproducibilityClaim(
        claimed=ReproducibilityClass.R1_FRESH_ENVIRONMENT_REPLAY,
        environment_recorded=True,
        independent_implementation=False,
        external_replication=False,
        framework="fixture-framework",
        dependency_lock_digest="sha256:lock",
        container_digest="sha256:container",
        accelerator_identity="fixture-gpu",
        driver_stack="fixture-driver",
    )


def test_freeze_records_when_and_why_criteria_were_frozen() -> None:
    frozen = _frozen()
    assert frozen.protocol.frozen_at_utc
    assert frozen.freeze_reason
    payload = frozen.to_dict()
    assert payload["criteria_frozen_before_outcomes"] is True
    assert payload["protocol_fingerprint"].startswith("sha256:")


def test_freeze_after_peeking_at_outcomes_is_refused() -> None:
    with pytest.raises(PolicyBlocked) as exc:
        freeze_protocol(
            load_protocol(),
            registrar="builder",
            freeze_reason="after seeing results",
            candidate_outcomes_observed=True,
            actor_is_builder=False,
        )
    assert exc.value.code == "FREEZE_AFTER_OUTCOMES_REFUSED"


def test_builder_cannot_author_the_sealed_freeze_that_judges_it() -> None:
    with pytest.raises(Unauthorized) as exc:
        freeze_protocol(
            dataclasses.replace(load_protocol(), tier=EvaluationTier.SEALED_CONFIRMATION),
            registrar="builder",
            freeze_reason="self-serving",
            candidate_outcomes_observed=False,
            actor_is_builder=True,
        )
    assert exc.value.code == "SEALED_FREEZE_BUILDER_REFUSED"


def test_a_frozen_protocol_cannot_be_edited() -> None:
    frozen = _frozen()
    assert_protocol_unchanged(frozen, frozen.protocol) is None
    with pytest.raises(Unauthorized) as exc:
        assert_protocol_unchanged(frozen, dataclasses.replace(frozen.protocol, tolerance=0.9))
    assert exc.value.code == "PROTOCOL_MUTATION_REFUSED"


def test_protocol_requires_declared_decision_rules() -> None:
    with pytest.raises(PolicyBlocked) as exc:
        freeze_protocol(
            dataclasses.replace(load_protocol(), decision_rules=()),
            registrar="test",
            freeze_reason="no rules",
            candidate_outcomes_observed=False,
            actor_is_builder=False,
        )
    assert exc.value.code == "DECISION_RULES_REQUIRED"


def test_sealed_store_builder_surface_exposes_no_contents() -> None:
    store = SealedEvaluationStore()
    store.register(
        SealedPayload(
            payload_id="SEALED-1",
            benchmark_id="B",
            tier=EvaluationTier.SEALED_CONFIRMATION,
            answer_key_digest="sha256:key",
            items=("C-01",),
        ),
        registrar_role="SEALED_EVALUATOR",
    )
    view = store.builder_view()
    assert view[0]["contents_available_to_builder"] is False
    assert "items" not in view[0]
    assert view[0]["item_count"] == 1


@pytest.mark.parametrize("role", ["BUILDER_AGENT", "RESEARCHER", "TRAINING_OPERATOR", "REVIEWER_AGENT"])
def test_builder_roles_can_never_read_sealed_items(role: str) -> None:
    store = SealedEvaluationStore()
    store.register(
        SealedPayload(
            payload_id="SEALED-1",
            benchmark_id="B",
            tier=EvaluationTier.SEALED_CONFIRMATION,
            answer_key_digest="sha256:key",
            items=("C-01",),
        ),
        registrar_role="SEALED_EVALUATOR",
    )
    with pytest.raises(Unauthorized) as exc:
        store.read("SEALED-1", actor="someone", role=role, purpose="curiosity")
    assert exc.value.code == "SEALED_ACCESS_BUILDER_REFUSED"
    assert store.refusals()[-1]["reason"] == "BUILDER_SURFACE"
    assert store.exposures() == ()


def test_sealed_read_requires_role_token_and_operator_issue() -> None:
    store = SealedEvaluationStore()
    store.register(
        SealedPayload(
            payload_id="SEALED-1",
            benchmark_id="B",
            tier=EvaluationTier.SEALED_CONFIRMATION,
            answer_key_digest="sha256:key",
            items=("C-01", "C-02"),
        ),
        registrar_role="SEALED_EVALUATOR",
    )
    with pytest.raises(Unauthorized) as exc:
        store.read("SEALED-1", actor="e", role="SEALED_EVALUATOR", purpose="score")
    assert exc.value.code == "SEALED_ACCESS_TOKEN_REQUIRED"

    with pytest.raises(Unauthorized) as exc2:
        store.issue_access_token("SEALED-1", operator_actor="BUILDER_AGENT", purpose="peek")
    assert exc2.value.code == "SEALED_ACCESS_OPERATOR_REQUIRED"

    token = store.issue_access_token("SEALED-1", operator_actor="OPERATOR", purpose="sealed scoring")
    items = store.read(
        "SEALED-1", actor="e", role="SEALED_EVALUATOR", purpose="sealed scoring", access_token=token
    )
    assert items == ("C-01", "C-02")
    exposures = store.exposures()
    assert len(exposures) == 1
    assert exposures[0].exposure_type is ExposureType.ACCESSED_SEALED_PAYLOAD
    assert exposures[0].compromising is True
    assert store.receipt().to_dict()["builder_surface_contains_contents"] is False


def test_sealed_registration_requires_the_sealed_role_and_immutable_payloads() -> None:
    store = SealedEvaluationStore()
    payload = SealedPayload(
        payload_id="SEALED-1",
        benchmark_id="B",
        tier=EvaluationTier.SEALED_CONFIRMATION,
        answer_key_digest="sha256:key",
        items=("C-01",),
    )
    with pytest.raises(Unauthorized):
        store.register(payload, registrar_role="BUILDER_AGENT")
    store.register(payload, registrar_role="SEALED_EVALUATOR")
    with pytest.raises(PolicyBlocked) as exc:
        store.register(payload, registrar_role="SEALED_EVALUATOR")
    assert exc.value.code == "SEALED_PAYLOAD_IMMUTABLE"


def test_power_gate_and_contamination_gate_prevent_pass() -> None:
    underpowered = _run(item_count=2, seeds=1)
    assert underpowered.power_adequate() is False
    with pytest.raises(PolicyBlocked) as exc:
        assert_conclusion_supported(
            TerminalConclusion.PASS,
            run=underpowered,
            contamination=ContaminationClass.C0_NO_OBSERVED_OVERLAP,
        )
    assert exc.value.code == "UNDERPOWERED_PASS_REFUSED"

    with pytest.raises(PolicyBlocked) as exc2:
        assert_conclusion_supported(
            TerminalConclusion.PASS,
            run=_run(),
            contamination=ContaminationClass.C4_DIRECT_ITEM_OR_ANSWER_OVERLAP,
        )
    assert exc2.value.code == "CONTAMINATED_PASS_REFUSED"


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({"item_count": 2, "seeds": 1}, TerminalConclusion.UNDERPOWERED),
        ({"contamination": ContaminationClass.C3_PARAPHRASE_OR_SOLUTION_OVERLAP}, TerminalConclusion.CONTAMINATED),
        ({"failures": ("PREEMPTED",)}, TerminalConclusion.INCONCLUSIVE),
    ],
)
def test_terminal_conclusions_are_truthful(kwargs: dict, expected: TerminalConclusion) -> None:
    assessment = assess_capability(
        _run(**kwargs),
        baseline={"accuracy": 0.6},
        replication=ReproductionEvidence(
            frameworks=("fixture-framework", "other-framework"),
            metric_agreement=FrozenMap({"accuracy": True}),
            max_delta=0.0,
            tolerance=0.02,
            evidence_ref="evidence://replication",
        ),
        limitations=(),
        oce_review_ref=None,
        reproducibility=_reproducibility(),
    )
    assert assessment.terminal_conclusion is expected


def test_cross_framework_agreement_is_required_for_pass() -> None:
    no_replication = assess_capability(
        _run(),
        baseline={"accuracy": 0.6},
        replication=None,
        limitations=(),
        oce_review_ref=None,
        reproducibility=_reproducibility(),
    )
    assert no_replication.terminal_conclusion is TerminalConclusion.INCONCLUSIVE
    assert no_replication.framework_dependence == "FRAMEWORK_UNVERIFIED"

    simulated = assess_capability(
        _run(),
        baseline={"accuracy": 0.6},
        replication=ReproductionEvidence(
            frameworks=("fixture-framework", "other-framework"),
            metric_agreement=FrozenMap({"accuracy": True}),
            max_delta=0.0,
            tolerance=0.02,
            evidence_ref="evidence://simulated",
            simulated=True,
        ),
        limitations=(),
        oce_review_ref=None,
        reproducibility=_reproducibility(),
    )
    assert simulated.terminal_conclusion is TerminalConclusion.INCONCLUSIVE
    assert simulated.framework_dependence == "CROSS_FRAMEWORK_AGREED_SIMULATED"

    disagreeing = assess_capability(
        _run(),
        baseline={"accuracy": 0.6},
        replication=ReproductionEvidence(
            frameworks=("fixture-framework", "other-framework"),
            metric_agreement=FrozenMap({"accuracy": False}),
            max_delta=0.4,
            tolerance=0.02,
            evidence_ref="evidence://disagreement",
        ),
        limitations=(),
        oce_review_ref=None,
        reproducibility=_reproducibility(),
    )
    assert disagreeing.framework_dependence == "CROSS_FRAMEWORK_DISAGREEMENT"
    assert disagreeing.terminal_conclusion is TerminalConclusion.INCONCLUSIVE

    agreed = assess_capability(
        _run(),
        baseline={"accuracy": 0.6},
        replication=ReproductionEvidence(
            frameworks=("fixture-framework", "other-framework"),
            metric_agreement=FrozenMap({"accuracy": True}),
            max_delta=0.001,
            tolerance=0.02,
            evidence_ref="evidence://agreement",
        ),
        limitations=(),
        oce_review_ref=None,
        reproducibility=_reproducibility(),
    )
    assert agreed.terminal_conclusion is TerminalConclusion.PASS
    assert agreed.framework_dependence == "CROSS_FRAMEWORK_AGREED"
    assert agreed.evidence_state is CapabilityEvidenceState.REPRODUCED


def test_an_unrecognised_benchmark_status_cannot_read_as_healthy() -> None:
    """The audited fail-open: ``status="COMPROMISEDD"`` used to reach PASS.

    The status vocabulary has one owner. A misspelling is neither a valid status
    nor a healthy one: it fails closed at construction instead of falling
    through the degraded check.
    """

    benchmark = load_benchmark()
    assert benchmark.status is BenchmarkStatus.FROZEN
    assert benchmark.degraded() is False

    with pytest.raises(PolicyBlocked) as exc:
        dataclasses.replace(benchmark, status="COMPROMISEDD")
    assert exc.value.code == "BENCHMARK_STATUS_UNKNOWN"

    compromised = dataclasses.replace(benchmark, status=BenchmarkStatus.COMPROMISED)
    assert compromised.degraded() is True

    frozen = freeze_protocol(
        dataclasses.replace(load_protocol(), benchmark=compromised),
        registrar="test",
        freeze_reason="criteria frozen before outcomes",
        candidate_outcomes_observed=False,
        actor_is_builder=False,
    )
    degraded_run = dataclasses.replace(_run(), frozen_protocol=frozen)
    assessment = assess_capability(
        degraded_run,
        baseline={"accuracy": 0.6},
        replication=ReproductionEvidence(
            frameworks=("fixture-framework", "other-framework"),
            metric_agreement=FrozenMap({"accuracy": True}),
            max_delta=0.001,
            tolerance=0.02,
            evidence_ref="evidence://agreement",
        ),
        limitations=(),
        oce_review_ref=None,
        reproducibility=_reproducibility(),
    )
    # the same replication evidence that reaches PASS for a healthy benchmark
    # cannot carry a degraded one
    assert assessment.terminal_conclusion is TerminalConclusion.INCONCLUSIVE
    assert assessment.evidence_state is CapabilityEvidenceState.MEASURED
    healthy = assess_capability(
        _run(),
        baseline={"accuracy": 0.6},
        replication=ReproductionEvidence(
            frameworks=("fixture-framework", "other-framework"),
            metric_agreement=FrozenMap({"accuracy": True}),
            max_delta=0.001,
            tolerance=0.02,
            evidence_ref="evidence://agreement",
        ),
        limitations=(),
        oce_review_ref=None,
        reproducibility=_reproducibility(),
    )
    assert healthy.terminal_conclusion is TerminalConclusion.PASS


def test_capability_is_vector_valued_with_no_master_score() -> None:
    assessment = assess_capability(
        _run(),
        baseline={"accuracy": 0.6, "calibration_error": 0.12},
        replication=None,
        limitations=(),
        oce_review_ref=None,
        reproducibility=_reproducibility(),
    )
    payload = assessment.to_dict()
    assert set(payload["dimensions"]) == {"accuracy", "calibration_error"}
    assert payload["dimensions"]["accuracy"]["delta"] == pytest.approx(0.11)
    assert payload["master_score"] is None
    assert payload["master_score_is_forbidden"] is True
    assert payload["writes_global_capability_status"] is False
    assert_no_master_score(payload)
    with pytest.raises(PolicyBlocked) as exc:
        assert_no_master_score({"master_score": 0.87})
    assert exc.value.code == "MASTER_CAPABILITY_SCORE_FORBIDDEN"


def test_capability_evidence_promotes_only_through_oce_review() -> None:
    assessment = assess_capability(
        _run(),
        baseline={"accuracy": 0.6},
        replication=None,
        limitations=(),
        oce_review_ref=None,
        reproducibility=_reproducibility(),
    )
    with pytest.raises(Unauthorized) as exc:
        submit_for_oce_review(assessment, oce_review_ref=None)
    assert exc.value.code == "CAPABILITY_SELF_PROMOTION_REFUSED"
    submitted = submit_for_oce_review(assessment, oce_review_ref="oce://review/9")
    assert submitted.evidence_state is CapabilityEvidenceState.READY_FOR_OCE_CAPABILITY_REVIEW


def test_subject_credit_separation_and_attribution_study() -> None:
    assessment = assess_capability(
        _run(subject_kind=SubjectKind.COGNITIVE_SYSTEM),
        baseline={"accuracy": 0.6},
        replication=None,
        limitations=(),
        oce_review_ref=None,
        reproducibility=_reproducibility(),
    )
    with pytest.raises(PolicyBlocked):
        credit_assessment(assessment, claimed_kind=SubjectKind.COGNITIVE_ARTIFACT)
    credit_assessment(
        assessment,
        claimed_kind=SubjectKind.COGNITIVE_ARTIFACT,
        attribution_study="study://attribution/1",
    )


def test_negative_results_are_first_class_and_reopen_requires_evidence() -> None:
    store = NegativeKnowledgeStore()
    result = NegativeResult(
        negative_id="NEG-1",
        subject_kind=SubjectKind.COGNITIVE_RUNTIME,
        subject_id="RT-1",
        hypothesis="bigger corpus improves calibration",
        outcome="no movement beyond tolerance",
        conclusion=TerminalConclusion.INCONCLUSIVE,
        evidence={"delta": 0.002},
        reopen_conditions=("a powered run with >= 40 items exceeds tolerance",),
        scope="fixture benchmark",
        recorded_utc="2026-01-04T00:00:00Z",
    )
    store.record(result)
    assert store.get("NEG-1").dogma_risk() == "ACCEPTABLE"

    with pytest.raises(PolicyBlocked) as exc:
        store.reopen("NEG-1", reason="feels right", new_evidence_ref=None, actor="builder")
    assert exc.value.code == "REOPEN_REQUIRES_NEW_EVIDENCE"

    with pytest.raises(PolicyBlocked) as exc2:
        store.record(result)
    assert exc2.value.code == "NEGATIVE_RESULT_IMMUTABLE"

    record = store.reopen(
        "NEG-1", reason="new powered measurement", new_evidence_ref="evidence://runs/RUN-40", actor="researcher"
    )
    assert record["provenance_preserved"] is True
    assert record["prior_conclusion"] == TerminalConclusion.INCONCLUSIVE.value
    assert store.get("NEG-1").reopen_state == "REOPENED"
    assert store.receipt().to_dict()["results"][0]["negative_result_is_project_failure"] is False


@pytest.mark.parametrize(
    ("conditions", "expected"),
    [
        ((), "CRITICAL_NO_REOPEN_PATH"),
        (("this can never be re-reviewed",), "CRITICAL_UNREACHABLE"),
        (("short", "also short"), "ELEVATED_VAGUE"),
        (("a powered run with new independent evidence exceeds tolerance",), "ACCEPTABLE"),
    ],
)
def test_dogma_risk_is_visible_in_reopen_conditions(conditions: tuple[str, ...], expected: str) -> None:
    result = NegativeResult(
        negative_id="NEG-X",
        subject_kind=SubjectKind.COGNITIVE_ARTIFACT,
        subject_id="A",
        hypothesis="h",
        outcome="o",
        conclusion=TerminalConclusion.FAIL,
        evidence={},
        reopen_conditions=conditions,
        scope="scope",
        recorded_utc="2026-01-04T00:00:00Z",
    )
    assert result.dogma_risk() == expected
    assert result.to_dict_with_dogma()["dogma_risk"] == expected


def test_tier_elevation_requires_a_new_protected_set_and_an_external_reference() -> None:
    benchmark = load_benchmark()
    with pytest.raises(Unauthorized) as exc:
        elevate_tier(
            benchmark,
            EvaluationTier.SEALED_CONFIRMATION,
            new_protected_task_set=True,
            actor_is_builder=True,
            authorizing_ref="oce://review/1",
        )
    assert exc.value.code == "TIER_SELF_UPGRADE_REFUSED"

    with pytest.raises(Unauthorized) as exc2:
        elevate_tier(
            benchmark,
            EvaluationTier.SEALED_CONFIRMATION,
            new_protected_task_set=True,
            actor_is_builder=False,
            authorizing_ref=None,
        )
    assert exc2.value.code == "TIER_ELEVATION_REQUIRES_AUTHORIZING_REF"

    elevated = elevate_tier(
        benchmark,
        EvaluationTier.SEALED_CONFIRMATION,
        new_protected_task_set=True,
        actor_is_builder=False,
        authorizing_ref="oce://review/1",
    )
    assert elevated.tier is EvaluationTier.SEALED_CONFIRMATION
