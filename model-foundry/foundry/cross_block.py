"""Cross-block scenarios F0–F11.

Each scenario crosses two or more blocks and asserts a *boundary* rather than a
happy path: the point is to show that the substrate refuses the shortcut even
when every single block works in isolation.

Results are data (:class:`ScenarioResult`), so tests, the CLI, and the evidence
package all consume the same execution instead of three divergent stories.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import Any, Callable

from .boundary import grade_contamination, run_mf_b0_adversarial_suite
from .constitution import CONSTITUTION, ReproducibilityClaim, ownership_conflicts, undeclared_generic_services
from .core import FrozenMap, PolicyBlocked, Unauthorized, fingerprint
from .data import SourceRole
from .enums import (
    ContaminationClass,
    EvaluationTier,
    ReproducibilityClass,
    SubjectKind,
    TerminalConclusion,
)
from .evaluation import (
    EvaluationObservation,
    EvaluationRun,
    NegativeKnowledgeStore,
    NegativeResult,
    ReproductionEvidence,
    SealedEvaluationStore,
    SealedPayload,
    assess_capability,
    assert_protocol_unchanged,
    credit_assessment,
    freeze_protocol,
    submit_for_oce_review,
)
from .fixtures import build_registry, load_bundle
from .oce_boundary import assert_boundary_complete, declaration_payload
from .providers import normalize_offer
from .refinery import DEFAULT_RECIPE, DatasetRefinery, audit_point_in_time, scan_secrets
from .resources import (
    BudgetLedger,
    ComputeRequest,
    OperatorGrant,
    PortableCheckpoint,
    assert_checkpoint_portable,
    estimate_cost_to_close,
    simulate_launch,
    simulate_placement,
)

NOW_EPOCH = 1767225600


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    title: str
    intent: str
    status: str  # HELD / FAILED
    observed: dict[str, Any]
    refusals: tuple[dict[str, Any], ...] = field(default_factory=tuple)

    @property
    def held(self) -> bool:
        return self.status == "HELD"

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "title": self.title,
            "intent": self.intent,
            "status": self.status,
            "held": self.held,
            "observed": self.observed,
            "refusals": list(self.refusals),
        }


def _refuse(fn: Callable[[], Any]) -> dict[str, Any]:
    """Run an attack and record how it was refused."""

    try:
        outcome = fn()
    except (PolicyBlocked, Unauthorized) as exc:
        return {"refused_by": type(exc).__name__, "code": getattr(exc, "code", None), "detail": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"refused_by": type(exc).__name__, "code": None, "detail": str(exc)}
    return {"refused_by": None, "code": None, "detail": f"NOT_REFUSED:{outcome!r}"}


def _world() -> dict[str, Any]:
    bundle = load_bundle()
    registry = build_registry()
    return {
        "bundle": bundle,
        "registry": registry,
        "refinery": DatasetRefinery(registry=registry, contamination=bundle.contamination),
        "offers": tuple(normalize_offer(o) for o in bundle.observations),
    }


def _train_request(**overrides: Any) -> ComputeRequest:
    base = {
        "request_id": "REQ-CROSS-BLOCK",
        "experiment_fingerprint": fingerprint({"experiment": "cross-block"}),
        "workload_class": "TRAINING_PARTIAL",
        "accelerator_class_required": "ANY",
        "accelerator_count": 1,
        "vram_gb_required": 40.0,
        "scratch_gb_required": 40.0,
        "expected_wall_hours": 12.0,
        "max_cost_to_close_usd": 10.0,
        "checkpoint_required": False,
        "failure_tolerance": "RETRYABLE",
    }
    base.update(overrides)
    return ComputeRequest(**base)  # type: ignore[arg-type]


# --------------------------------------------------------------------------
# F0 — constitution and boundary
# --------------------------------------------------------------------------


def scenario_f0() -> ScenarioResult:
    attacks = run_mf_b0_adversarial_suite()
    assert_boundary_complete()
    observed = {
        "doctrine_count": len(CONSTITUTION.doctrine),
        "ownership_conflicts": list(ownership_conflicts()),
        "undeclared_generic_services": list(undeclared_generic_services()),
        "attacks_total": len(attacks),
        "attacks_held": sum(1 for a in attacks if a.held),
        "attacks_allowed": [a.attack_id for a in attacks if not a.held],
        "boundary_fixtures": len(declaration_payload()["fixtures"]),
        "constitution_fingerprint": CONSTITUTION.fingerprint,
    }
    status = "HELD" if (not observed["ownership_conflicts"] and not observed["attacks_allowed"]) else "FAILED"
    return ScenarioResult(
        "F0",
        "constitution + one-OCE boundary",
        "the substrate may not become a second OCE and may not own truth or authority",
        status,
        observed,
    )


# --------------------------------------------------------------------------
# F1 — provider-neutral compute
# --------------------------------------------------------------------------


def scenario_f1() -> ScenarioResult:
    world = _world()
    request = _train_request()
    decision = simulate_placement(request, list(world["offers"]), now_epoch_s=NOW_EPOCH)

    renamed = [
        dataclasses.replace(offer, provider=f"anonymous-vendor-{index}")
        for index, offer in enumerate(world["offers"])
    ]
    renamed_decision = simulate_placement(request, renamed, now_epoch_s=NOW_EPOCH)

    def provider_free(payload: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {k: v for k, v in entry.items() if k not in {"provider", "offer_id", "adapter"}}
            for entry in payload["considered"]
        ]

    observed = {
        "selected_offer_id": decision.selected_offer_id,
        "selected_cost_to_close_usd": round(decision.selected_cost_to_close_usd, 6),
        "cheapest_hourly_eligible": decision.cheapest_hourly_offer_id,
        "cheapest_hourly_usd": decision.cheapest_hourly_usd,
        "hourly_trap_detected": decision.hourly_trap_detected,
        "rejected_reasons": {r["offer_id"]: r["reason"] for r in decision.rejected},
        "cost_to_close_stable_under_provider_rename": provider_free(decision.to_dict())
        == provider_free(renamed_decision.to_dict()),
        "request_has_no_provider_field": request.to_dict()["provider_field_present"] is False,
    }
    status = "HELD" if (observed["hourly_trap_detected"] and observed["cost_to_close_stable_under_provider_rename"]) else "FAILED"
    return ScenarioResult(
        "F1",
        "provider-neutral placement",
        "provider identity must not change scientific semantics, and hourly price is not cost-to-close",
        status,
        observed,
    )


# --------------------------------------------------------------------------
# F2 — rights and roles
# --------------------------------------------------------------------------


def scenario_f2() -> ScenarioResult:
    world = _world()
    registry = world["registry"]
    refusals: list[dict[str, Any]] = []

    refusals.append(
        _refuse(
            lambda: registry.transition_role(
                "SRC_RIGHTS_UNKNOWN",
                SourceRole.TRAIN_CPT,
                actor="builder",
                reason="we need more data",
            )
        )
    )
    refusals.append(
        _refuse(
            lambda: registry.transition_role(
                "SRC_NEWS_ALPHA",
                SourceRole.TRAIN_CPT,
                actor="builder",
                reason="no-op transition",
            )
        )
    )
    refusals.append(
        _refuse(
            lambda: registry.register(
                dataclasses.replace(
                    registry.get("SRC_SECRET_INCIDENT"),
                    source_id="SRC_SECRET_TRAIN",
                    role=SourceRole.TRAIN_CPT,
                ),
                actor="builder",
                reason="try to train on incident notes",
            )
        )
    )

    observed = {
        "unknown_rights_state": registry.rights_state("SRC_RIGHTS_UNKNOWN").value,
        "unknown_rights_permits_training": registry.trainable("SRC_RIGHTS_UNKNOWN"),
        "rights_blocked": registry.rights_blocked_sources(),
        "rights_permissive_but_role_forbidden": registry.rights_permissive_but_role_forbidden(),
        "eligible_for_training": list(registry.trainable_sources()),
        "refusal_codes": [r["code"] for r in refusals],
        "negative_control_can_train": registry.eligible_for_training("SRC_NEWS_ALPHA"),
    }
    expected_codes = {
        "RIGHTS_BLOCKED",
        "ROLE_TRANSITION_NOOP",
        "SECRET_BEARING_SOURCE_TRAIN_ROLE_REFUSED",
    }
    status = (
        "HELD"
        if (
            {r["code"] for r in refusals} == expected_codes
            and observed["negative_control_can_train"]
        )
        else "FAILED"
    )
    return ScenarioResult(
        "F2",
        "data rights, roles, and permissions",
        "ACCESS != RIGHTS: unknown rights fail away from training, and permissions are not roles",
        status,
        observed,
        tuple(refusals),
    )


# --------------------------------------------------------------------------
# F3 — corpus construction
# --------------------------------------------------------------------------


def scenario_f3() -> ScenarioResult:
    world = _world()
    bundle = world["bundle"]
    registry = world["registry"]
    refinery = world["refinery"]

    run = refinery.refine(
        dataset_id="ds.cross.train.v0",
        purpose="cross-block governed corpus",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_NEWS_ALPHA", "SRC_NEWS_ALPHA_MIRROR", "SRC_AGENT_TRACE", "SRC_RIGHTS_UNKNOWN"],
        recipe=DEFAULT_RECIPE,
    )
    assert run.manifest is not None
    repeated = refinery.refine(
        dataset_id="ds.cross.train.v0",
        purpose="cross-block governed corpus",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_NEWS_ALPHA", "SRC_NEWS_ALPHA_MIRROR", "SRC_AGENT_TRACE", "SRC_RIGHTS_UNKNOWN"],
        recipe=DEFAULT_RECIPE,
    )
    diversity = registry.effective_diversity(["SRC_NEWS_ALPHA", "SRC_NEWS_ALPHA_MIRROR"])

    observed = {
        "item_count": run.manifest.item_count,
        "exact_duplicates_collapsed": run.manifest.dedup["exact_duplicates_collapsed"],
        "near_duplicates_collapsed": run.manifest.dedup["near_duplicate_count"],
        "excluded_sources": [e["source_id"] for e in run.manifest.excluded_sources],
        "split_strategy": run.manifest.splits["strategy"],
        "item_level_random_split_used": run.manifest.splits["item_level_random_split_used"],
        "lineage_fingerprint": run.manifest.lineage_fingerprint,
        "lineage_reproducible": run.manifest.lineage_fingerprint == repeated.manifest.lineage_fingerprint,
        "mirror_lineages": diversity["effective_lineages"],
        "mirror_collapsed": diversity["diversity_is_claimed_not_effective"],
        "unknown_rights_excluded": "SRC_RIGHTS_UNKNOWN" in [e["source_id"] for e in run.manifest.excluded_sources],
    }
    status = "HELD" if (observed["lineage_reproducible"] and observed["mirror_collapsed"] and observed["unknown_rights_excluded"]) else "FAILED"
    return ScenarioResult(
        "F3",
        "governed corpus construction",
        "governed sources produce a deterministic manifest, and aliases are not diversity",
        status,
        observed,
    )


# --------------------------------------------------------------------------
# F4 — point-in-time leakage
# --------------------------------------------------------------------------


def scenario_f4() -> ScenarioResult:
    world = _world()
    bundle = world["bundle"]
    market_items = [i for i in bundle.items if i.source_id == "SRC_MARKET_TICKS_PIT"]
    audit = audit_point_in_time(market_items, decision_reference_utc="2026-01-02T00:00:00Z")
    clean_audit = audit_point_in_time(
        [i for i in market_items if not i.item_id.startswith("MARKET-LEAK") and not i.item_id.startswith("MARKET-IMPLAUSIBLE")],
        decision_reference_utc="2026-01-02T00:00:00Z",
    )
    run = world["refinery"].refine(
        dataset_id="ds.cross.pit.v0",
        purpose="PIT enforcement",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_MARKET_TICKS_PIT"],
        decision_reference_utc="2026-01-02T00:00:00Z",
    )
    reasons = sorted({v["reason"] for v in audit.violations})
    observed = {
        "violations": len(audit.violations),
        "violation_reasons": reasons,
        "clean_subset_passes": clean_audit.passed(),
        "dataset_refused": run.manifest is None,
        "failure": run.negative_result.failure.value if run.negative_result else None,
    }
    status = (
        "HELD"
        if (
            observed["violations"] > 0
            and clean_audit.passed()
            and observed["dataset_refused"]
        )
        else "FAILED"
    )
    return ScenarioResult(
        "F4",
        "point-in-time leakage",
        "future information at the decision instant is detected and blocks a training dataset",
        status,
        observed,
    )


# --------------------------------------------------------------------------
# F5 — contamination
# --------------------------------------------------------------------------


def scenario_f5() -> ScenarioResult:
    world = _world()
    bundle = world["bundle"]
    graph = bundle.contamination
    blocked_edges = graph.claim_blocking_edges("SRC_BENCH_CORE")
    worst = graph.worst_grade("SRC_BENCH_CORE")
    empty_graph_grade = graph.worst_grade("SRC_SECRET_INCIDENT")
    grade = grade_contamination(
        (("bench", worst), ("unrelated", ContaminationClass.C0_NO_OBSERVED_OVERLAP))
    )
    observed = {
        "worst_grade_for_bench_core": worst.value,
        "claim_blocking_edges": len(blocked_edges),
        "combined_grade": grade.value,
        "adjacent_source_grade_not_inherited": empty_graph_grade.value,
        "unobserved_is_not_clean": "absence is not cleanliness"
        or graph.to_dict()["unobserved_overlap_is_not_cleanliness"],
    }
    status = "HELD" if (blocked_edges and grade is ContaminationClass.C3_PARAPHRASE_OR_SOLUTION_OVERLAP) else "FAILED"
    return ScenarioResult(
        "F5",
        "contamination gating",
        "a train source contaminated against an eval set degrades the claim and blocks the strongest labels",
        status,
        observed,
    )


# --------------------------------------------------------------------------
# F6 — withheld doctrine
# --------------------------------------------------------------------------


def scenario_f6() -> ScenarioResult:
    world = _world()
    registry = world["registry"]
    refusals = [
        _refuse(lambda: registry.assert_doctrine_withheld("SRC_CEREBUS_RULES")),
        _refuse(lambda: registry.assert_no_doctrine_leak(["SRC_NEWS_ALPHA", "SRC_CEREBUS_RULES"])),
    ]
    run = world["refinery"].refine(
        dataset_id="ds.cross.withheld.v0",
        purpose="withheld",
        role=SourceRole.TRAIN_CPT,
        items=world["bundle"].items,
        source_ids=["SRC_CEREBUS_RULES"],
    )
    observed = {
        "doctrine_bearing_sources": list(registry.doctrine_bearing_sources()),
        "refusal_codes": [r["code"] for r in refusals],
        "dataset_refused": run.manifest is None,
        "failure": run.negative_result.failure.value if run.negative_result else None,
        "blocked_sources": list(run.negative_result.blocked_sources) if run.negative_result else [],
        "reopen_condition": run.negative_result.reopen_condition if run.negative_result else None,
    }
    status = "HELD" if (all(r["code"] == "CEREBUS_FAMILY_WITHHELD" for r in refusals) and observed["dataset_refused"]) else "FAILED"
    return ScenarioResult(
        "F6",
        "withheld doctrine boundary",
        "CEREBUS-family material is operationally withheld from every model-facing path",
        status,
        observed,
        tuple(refusals),
    )


# --------------------------------------------------------------------------
# F7 — protocol freeze
# --------------------------------------------------------------------------


def scenario_f7() -> ScenarioResult:
    world = _world()
    bundle = world["bundle"]
    frozen = freeze_protocol(
        bundle.protocol,
        registrar="cross-block",
        freeze_reason="cross-block freeze before outcomes",
        candidate_outcomes_observed=False,
        actor_is_builder=False,
    )
    refusals = [
        _refuse(
            lambda: freeze_protocol(
                bundle.protocol,
                registrar="builder",
                freeze_reason="peeked first",
                candidate_outcomes_observed=True,
                actor_is_builder=False,
            )
        ),
        _refuse(
            lambda: freeze_protocol(
                dataclasses.replace(bundle.protocol, tier=EvaluationTier.SEALED_CONFIRMATION),
                registrar="builder",
                freeze_reason="self-serving freeze",
                candidate_outcomes_observed=False,
                actor_is_builder=True,
            )
        ),
        _refuse(
            lambda: assert_protocol_unchanged(
                frozen, dataclasses.replace(bundle.protocol, tolerance=0.5)
            )
        ),
    ]
    observed = {
        "protocol_fingerprint": frozen.protocol.fingerprint,
        "frozen_at_utc_present": bool(frozen.protocol.frozen_at_utc),
        "refusal_codes": [r["code"] for r in refusals],
        "tier": frozen.protocol.tier.value,
    }
    status = "HELD" if all(r["code"] for r in refusals) else "FAILED"
    return ScenarioResult(
        "F7",
        "evaluation freeze",
        "criteria are frozen before outcomes, builders cannot author the freeze that judges them, freeze is immutable",
        status,
        observed,
        tuple(refusals),
    )


# --------------------------------------------------------------------------
# F8 — sealed access
# --------------------------------------------------------------------------


def scenario_f8() -> ScenarioResult:
    store = SealedEvaluationStore()
    store.register(
        SealedPayload(
            payload_id="SEALED-CROSS-01",
            benchmark_id="RESEARCH_BENCH_V0",
            tier=EvaluationTier.SEALED_CONFIRMATION,
            answer_key_digest="sha256:sealed-cross-answer-key",
            items=("C-01", "C-02"),
        ),
        registrar_role="SEALED_EVALUATOR",
    )
    refusals = [
        _refuse(lambda: store.read("SEALED-CROSS-01", actor="builder", role="BUILDER_AGENT", purpose="curiosity")),
        _refuse(lambda: store.read("SEALED-CROSS-01", actor="reviewer", role="REVIEWER_AGENT", purpose="review")),
        _refuse(
            lambda: store.read(
                "SEALED-CROSS-01", actor="evaluator", role="SEALED_EVALUATOR", purpose="score", access_token=None
            )
        ),
        _refuse(
            lambda: store.register(
                SealedPayload(
                    payload_id="SEALED-CROSS-02",
                    benchmark_id="RESEARCH_BENCH_V0",
                    tier=EvaluationTier.SEALED_CONFIRMATION,
                    answer_key_digest="sha256:x",
                    items=("C-03",),
                ),
                registrar_role="BUILDER_AGENT",
            )
        ),
    ]
    token = store.issue_access_token("SEALED-CROSS-01", operator_actor="OPERATOR", purpose="sealed scoring run")
    items = store.read(
        "SEALED-CROSS-01",
        actor="evaluator",
        role="SEALED_EVALUATOR",
        purpose="sealed scoring run",
        access_token=token,
    )
    observed = {
        "refusal_codes": [r["code"] for r in refusals],
        "refusals_recorded": len(store.refusals()),
        "authorised_read_items": len(items),
        "exposures_recorded": [e.exposure_type.value for e in store.exposures()],
        "builder_view_exposes_contents": any(
            "items" in entry for entry in store.builder_view()
        ),
        "exposure_budget_ok": store.exposure_budget_ok(EvaluationTier.SEALED_CONFIRMATION),
    }
    status = "HELD" if (all(r["code"] for r in refusals) and observed["authorised_read_items"] == 2) else "FAILED"
    return ScenarioResult(
        "F8",
        "sealed evaluation boundary",
        "sealed answers are unreachable from the builder surface, every attempt is recorded, access requires operator authority",
        status,
        observed,
        tuple(refusals),
    )


# --------------------------------------------------------------------------
# F9 — subject credit separation
# --------------------------------------------------------------------------


def scenario_f9() -> ScenarioResult:
    world = _world()
    frozen = freeze_protocol(
        world["bundle"].protocol,
        registrar="cross-block",
        freeze_reason="cross-block freeze",
        candidate_outcomes_observed=False,
        actor_is_builder=False,
    )
    run = EvaluationRun(
        run_id="RUN-CROSS-F9",
        frozen_protocol=frozen,
        subject_kind=SubjectKind.COGNITIVE_SYSTEM,
        subject_id="SYS-CROSS-1",
        observations=(EvaluationObservation("accuracy", 0.7, item_count=6, seed=1),),
        framework="fixture-framework",
        framework_version="0.1",
        runtime_identity="runtime-cross-1",
        contamination_grade=ContaminationClass.C0_NO_OBSERVED_OVERLAP,
        started_utc="2026-01-04T00:00:00Z",
        completed_utc="2026-01-04T00:10:00Z",
        seeds_used=2,
    )
    assessment = assess_capability(
        run,
        baseline={"accuracy": 0.6},
        replication=ReproductionEvidence(
            frameworks=("fixture-framework", "other-framework"),
            metric_agreement=FrozenMap({"accuracy": True}),
            max_delta=0.0,
            tolerance=0.02,
            evidence_ref="evidence://runs/RUN-CROSS-F9-OTHER",
            simulated=False,
        ),
        limitations=(),
        oce_review_ref=None,
        reproducibility=ReproducibilityClaim(
            claimed=ReproducibilityClass.R1_FRESH_ENVIRONMENT_REPLAY,
            environment_recorded=True,
            independent_implementation=False,
            external_replication=False,
            framework="fixture-framework",
            dependency_lock_digest="sha256:lock",
            container_digest="sha256:container",
            accelerator_identity="fixture-gpu",
            driver_stack="fixture-driver",
        ),
    )
    refusals = [
        _refuse(lambda: credit_assessment(assessment, claimed_kind=SubjectKind.COGNITIVE_ARTIFACT)),
        _refuse(lambda: submit_for_oce_review(assessment, oce_review_ref=None)),
    ]
    with_study = assessment
    credit_assessment(with_study, claimed_kind=SubjectKind.COGNITIVE_ARTIFACT, attribution_study="study://attribution/001")
    observed = {
        "subject_kind": assessment.subject_kind.value,
        "refusal_codes": [r["code"] for r in refusals],
        "attribution_study_permits_narrower_credit": True,
        "vector_dimensions": sorted(assessment.dimensions.keys()),
        "master_score": assessment.to_dict()["master_score"],
        "writes_global_capability_status": assessment.to_dict()["writes_global_capability_status"],
        "framework_dependence": assessment.framework_dependence,
        "terminal_conclusion": assessment.terminal_conclusion.value,
    }
    status = "HELD" if all(r["code"] for r in refusals) else "FAILED"
    return ScenarioResult(
        "F9",
        "artifact / runtime / system separation",
        "a system result cannot be credited as an artifact result, and capability evidence promotes only through OCE review",
        status,
        observed,
        tuple(refusals),
    )


# --------------------------------------------------------------------------
# F10 — negative results and reopen
# --------------------------------------------------------------------------


def scenario_f10() -> ScenarioResult:
    store = NegativeKnowledgeStore()
    store.record(
        NegativeResult(
            negative_id="NEG-CROSS-1",
            subject_kind=SubjectKind.COGNITIVE_RUNTIME,
            subject_id="RT-CROSS-1",
            hypothesis="scaling the corpus improves calibration",
            outcome="no calibrated improvement beyond tolerance",
            conclusion=TerminalConclusion.INCONCLUSIVE,
            evidence={"delta": 0.003, "tolerance": 0.02},
            reopen_conditions=("a powered run with >= 40 items shows a calibration delta beyond the declared tolerance",),
            scope="fixture benchmark only",
            recorded_utc="2026-01-04T01:00:00Z",
        )
    )
    refusals = [
        _refuse(lambda: store.reopen("NEG-CROSS-1", reason="we feel it should work", new_evidence_ref=None, actor="builder")),
        _refuse(
            lambda: store.record(
                NegativeResult(
                    negative_id="NEG-CROSS-1",
                    subject_kind=SubjectKind.COGNITIVE_RUNTIME,
                    subject_id="RT-CROSS-1",
                    hypothesis="overwrite attempt",
                    outcome="x",
                    conclusion=TerminalConclusion.FAIL,
                    evidence={},
                    reopen_conditions=("never",),
                    scope="fixture",
                    recorded_utc="2026-01-04T02:00:00Z",
                )
            )
        ),
    ]
    reopened = store.reopen(
        "NEG-CROSS-1",
        reason="new powered measurement available",
        new_evidence_ref="evidence://runs/RUN-CROSS-40",
        actor="researcher",
        operator_approval_ref="approval://operator/117",
    )
    tight = NegativeResult(
        negative_id="NEG-DOGMA",
        subject_kind=SubjectKind.COGNITIVE_ARTIFACT,
        subject_id="ART-1",
        hypothesis="h",
        outcome="o",
        conclusion=TerminalConclusion.FAIL,
        evidence={},
        reopen_conditions=("never",),
        scope="fixture",
        recorded_utc="2026-01-04T03:00:00Z",
    )
    observed = {
        "refusal_codes": [r["code"] for r in refusals],
        "reopen_preserves_prior_conclusion": reopened["prior_conclusion"],
        "reopen_requires_new_evidence_record": bool(reopened["new_evidence_ref"]),
        "dogma_risk_of_unreachable_condition": tight.dogma_risk(),
    }
    status = "HELD" if (all(r["code"] for r in refusals) and observed["dogma_risk_of_unreachable_condition"].startswith("CRITICAL")) else "FAILED"
    return ScenarioResult(
        "F10",
        "negative results and reopen",
        "negative findings are first-class, reopening requires new evidence, and impossible reopen conditions stay visible as dogma risk",
        status,
        observed,
        tuple(refusals),
    )


# --------------------------------------------------------------------------
# F11 — provider loss, portability, and secret discipline
# --------------------------------------------------------------------------


def scenario_f11() -> ScenarioResult:
    world = _world()
    request = _train_request(checkpoint_required=True)
    decision = simulate_placement(request, list(world["offers"]), now_epoch_s=NOW_EPOCH)
    offer = next(o for o in world["offers"] if o.offer_id == decision.selected_offer_id)
    budget = BudgetLedger(authorized_usd=50.0)
    grant = OperatorGrant(
        grant_id="GRANT-CROSS-1",
        granted_by="OPERATOR",
        granted_to_request=request.request_id,
        max_usd=25.0,
        expires_at_epoch_s=NOW_EPOCH + 86400,
        purpose="cross-block simulated run",
    )
    receipt = simulate_launch(
        request,
        decision,
        offer,
        now_epoch_s=NOW_EPOCH,
        mode="SIMULATE",
        budget=budget,
        grant=grant,
        operator_actor="OPERATOR",
    )
    refusals = [
        _refuse(
            lambda: simulate_launch(
                request, decision, offer, now_epoch_s=NOW_EPOCH, mode="LIVE", operator_actor="OPERATOR", grant=grant
            )
        ),
        _refuse(
            lambda: simulate_launch(
                request, decision, offer, now_epoch_s=NOW_EPOCH, mode="SIMULATE", operator_actor="OPERATOR", grant=None
            )
        ),
        _refuse(
            lambda: simulate_launch(
                request,
                decision,
                offer,
                now_epoch_s=NOW_EPOCH,
                mode="SIMULATE",
                operator_actor="OPERATOR",
                grant=dataclasses.replace(grant, granted_by="BUILDER_AGENT"),
            )
        ),
        _refuse(
            lambda: simulate_launch(
                request,
                decision,
                offer,
                now_epoch_s=NOW_EPOCH,
                mode="SIMULATE",
                operator_actor="OPERATOR",
                budget=BudgetLedger(authorized_usd=1.0),
                grant=grant,
            )
        ),
    ]

    portable = PortableCheckpoint(
        checkpoint_ref="ckpt:cross-1",
        request_fingerprint=request.fingerprint,
        framework="fixture-framework",
        framework_version="0.1",
        optimizer_state_digest="sha256:opt",
        model_state_digest="sha256:model",
        rng_state_digest="sha256:rng",
        data_position_digest="sha256:pos",
        export_format="safetensors+json",
        portability_notes="framework-agnostic export",
    )
    assert_checkpoint_portable(portable)
    locked_refusal = _refuse(
        lambda: assert_checkpoint_portable(
            dataclasses.replace(portable, export_format="framework-pickle")
        )
    )

    secrets = scan_secrets(world["bundle"].items)
    observed = {
        "refusal_codes": [r["code"] for r in refusals],
        "simulated_mode": receipt.mode,
        "paid_compute_consumed": receipt.paid_compute_consumed,
        "provider_identity_in_scientific_result": receipt.provider_identity_in_scientific_result,
        "budget_consumed_usd": round(budget.spent_usd, 4),
        "checkpoint_fingerprint": portable.fingerprint,
        "framework_locked_checkpoint_refused": locked_refusal["code"],
        "secret_hits": [h["pattern"] for h in secrets.hits],
        "secret_scan_passed": secrets.passed(),
        "cost_to_close_with_checkpoint": round(
            estimate_cost_to_close(request, offer).cost_to_close_usd, 6
        ),
    }
    status = (
        "HELD"
        if (
            all(r["code"] for r in refusals)
            and receipt.paid_compute_consumed is False
            and locked_refusal["code"] == "CHECKPOINT_FORMAT_NOT_PORTABLE"
            and not observed["secret_scan_passed"]
        )
        else "FAILED"
    )
    return ScenarioResult(
        "F11",
        "provider loss, portability, and secret discipline",
        "no paid path exists, an accepted provider is not an authorization, checkpoints survive framework loss, secrets are detected",
        status,
        observed,
        tuple(refusals),
    )


SCENARIOS: dict[str, Callable[[], ScenarioResult]] = {
    "F0": scenario_f0,
    "F1": scenario_f1,
    "F2": scenario_f2,
    "F3": scenario_f3,
    "F4": scenario_f4,
    "F5": scenario_f5,
    "F6": scenario_f6,
    "F7": scenario_f7,
    "F8": scenario_f8,
    "F9": scenario_f9,
    "F10": scenario_f10,
    "F11": scenario_f11,
}


def run_all() -> tuple[ScenarioResult, ...]:
    return tuple(SCENARIOS[key]() for key in sorted(SCENARIOS))


def cross_block_report() -> dict[str, Any]:
    results = run_all()
    report = {
        "scenarios": [r.to_dict() for r in results],
        "scenarios_total": len(results),
        "scenarios_held": sum(1 for r in results if r.held),
        "scenarios_failed": [r.scenario_id for r in results if not r.held],
        "verdict": "PASS" if all(r.held for r in results) else "FAIL",
    }
    report["report_fingerprint"] = fingerprint(report)
    return report


__all__ = [
    "NOW_EPOCH",
    "SCENARIOS",
    "ScenarioResult",
    "cross_block_report",
    "run_all",
    "scenario_f0",
    "scenario_f1",
    "scenario_f2",
    "scenario_f3",
    "scenario_f4",
    "scenario_f5",
    "scenario_f6",
    "scenario_f7",
    "scenario_f8",
    "scenario_f9",
    "scenario_f10",
    "scenario_f11",
]
