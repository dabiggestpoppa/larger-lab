"""Foundry CLI — local, offline, deterministic.

    python -m foundry.cli doctrine
    python -m foundry.cli boundary
    python -m foundry.cli b0-gate
    python -m foundry.cli b1-cost-close
    python -m foundry.cli b2-registry
    python -m foundry.cli b3-refine
    python -m foundry.cli b4-run
    python -m foundry.cli report

Every command writes receipts under ``model-foundry/receipts``. No command
contacts a provider, an exchange, or any remote service, and no command can
launch paid compute.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .constitution import CONSTITUTION, FOUNDRY_DOCTRINE, ReproducibilityClaim
from .core import FrozenMap, fingerprint, write_json
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
    SealedEvaluationStore,
    ReproductionEvidence,
    SealedPayload,
    assess_capability,
    freeze_protocol,
)
from .fixtures import build_registry, load_bundle
from .oce_boundary import assert_boundary_complete, declaration_payload
from .providers import normalize_offer
from .refinery import DEFAULT_RECIPE, DatasetRefinery
from .resources import ComputeRequest, simulate_placement

RECEIPTS_DIR = Path(__file__).resolve().parent.parent / "receipts"
FIXTURE_DECLARATIONS = Path(__file__).resolve().parent.parent / "fixtures" / "noncanonical_declarations.json"
EVIDENCE_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "model-foundry" / "evidence"

NOW_EPOCH = 1767225600  # 2026-01-01T00:00:00Z fixture clock


def _emit(title: str, payload: Any) -> None:
    out = write_json(RECEIPTS_DIR / f"{title}.json", payload)
    print(f"wrote {out}")


def cmd_doctrine(_: argparse.Namespace) -> int:
    print(f"foundry constitution fingerprint: {CONSTITUTION.fingerprint}")
    for line in FOUNDRY_DOCTRINE:
        print(f"  {line}")
    return 0


def cmd_boundary(_: argparse.Namespace) -> int:
    assert_boundary_complete()
    payload = declaration_payload()
    write_json(FIXTURE_DECLARATIONS, payload)
    for entry in payload["fixtures"]:
        print(f"  {entry['fixture']:34s} -> {entry['canonical_oce_target']}")
    print(f"boundary fingerprint: {payload['boundary_fingerprint']}")
    return 0


def cmd_b0_gate(_: argparse.Namespace) -> int:
    from .boundary import mf_b0_gate_report

    report = mf_b0_gate_report()
    _emit("mf-b0-gate", report)
    print(
        f"MF-B0 verdict={report['verdict']} attacks={report['attacks_total']} "
        f"refused={report['attacks_refused']} contained={report['attacks_contained']} "
        f"failed_open={report['attacks_failed_open']}"
    )
    return 0 if report["verdict"] == "PASS" else 1


def cmd_b1_cost_close(_: argparse.Namespace) -> int:
    bundle = load_bundle()
    offers = [normalize_offer(o) for o in bundle.observations]
    request = ComputeRequest(
        request_id="REQ-FIXTURE-SMOKE",
        experiment_fingerprint=fingerprint({"experiment": "fixture-smoke"}),
        workload_class="RESEARCH_SMOKE",
        accelerator_class_required="ANY",
        accelerator_count=1,
        vram_gb_required=40.0,
        scratch_gb_required=40.0,
        expected_wall_hours=12.0,
        max_cost_to_close_usd=10.0,
        checkpoint_required=False,
        failure_tolerance="RETRYABLE",
    )
    decision = simulate_placement(request, offers, now_epoch_s=NOW_EPOCH)
    _emit(
        "mf-b1-placement",
        {
            "request": request.to_dict(),
            "decision": decision.to_dict(),
            "offers": [o.to_dict() for o in offers],
        },
    )
    print(f"cheapest hourly : {decision.cheapest_hourly_offer_id} (${decision.cheapest_hourly_usd}/h)")
    print(f"chosen to close : {decision.selected_offer_id} (${decision.selected_cost_to_close_usd:.2f})")
    print(f"hourly trap     : {decision.hourly_trap_detected}")
    return 0


def cmd_b2_registry(_: argparse.Namespace) -> int:
    registry = build_registry()
    payload = {
        "source_count": len(registry.source_ids()),
        "role_distribution": registry.role_distribution(),
        "rights_blocked": registry.rights_blocked_sources(),
        "trainable": list(registry.trainable_sources()),
        "diversity": registry.effective_diversity(),
        "doctrine_bearing": list(registry.doctrine_bearing_sources()),
        "registry_digest": registry.digest(),
    }
    _emit("mf-b2-registry", payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_b3_refine(_: argparse.Namespace) -> int:
    registry = build_registry()
    bundle = load_bundle()
    refinery = DatasetRefinery(registry=registry, contamination=bundle.contamination)

    train_sources = [
        "SRC_NEWS_ALPHA",
        "SRC_NEWS_ALPHA_MIRROR",
        "SRC_AGENT_TRACE",
        "SRC_RIGHTS_UNKNOWN",
        "SRC_CEREBUS_RULES",
    ]
    train_run = refinery.refine(
        dataset_id="ds.tier0.cpt.v0",
        purpose="continued pretraining corpus for scratch-model research",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=train_sources,
        recipe=DEFAULT_RECIPE,
    )
    contamination_run = refinery.refine(
        dataset_id="ds.withheld.v0",
        purpose="attempt to build a dataset from withheld doctrine material",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_CEREBUS_RULES"],
    )
    verdict_run = refinery.refine(
        dataset_id="ds.secret.v0",
        purpose="attempt to build a dataset from a secret-bearing note",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_SECRET_INCIDENT"],
    )
    pit_run = refinery.refine(
        dataset_id="ds.market.pit.v0",
        purpose="point-in-time audit on fixture market data",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_MARKET_TICKS_PIT"],
        decision_reference_utc="2026-01-02T00:00:00Z",
    )

    payload = {
        "train_dataset": train_run.to_dict(),
        "withheld_attempt": contamination_run.to_dict(),
        "secret_attempt": verdict_run.to_dict(),
        "pit_attempt": pit_run.to_dict(),
    }
    _emit("mf-b3-refinery", payload)
    for name, run in (
        ("train", train_run),
        ("withheld", contamination_run),
        ("secret", verdict_run),
        ("pit", pit_run),
    ):
        state = (
            f"manifest {run.manifest.dataset_id} items={run.manifest.item_count}"
            if run.manifest
            else f"refused: {run.negative_result.failure.value}"
        )
        print(f"  {name:9s} {state}")
    return 0


def cmd_b4_run(_: argparse.Namespace) -> int:
    bundle = load_bundle()
    frozen = freeze_protocol(
        bundle.protocol,
        registrar="foundry.evaluation.fixture",
        freeze_reason="criteria frozen before any candidate outcome existed",
        candidate_outcomes_observed=False,
        actor_is_builder=False,
        now_iso="2026-01-03T00:00:00Z",  # fixture clock: receipts must be replayable
    )
    observations = (
        EvaluationObservation("accuracy", 0.71, item_count=6, seed=1),
        EvaluationObservation("accuracy", 0.69, item_count=6, seed=2),
        EvaluationObservation("calibration_error", 0.08, item_count=6, seed=1),
        EvaluationObservation("instruction_adherence", 0.97, item_count=6, seed=1),
        EvaluationObservation("refusal_precision", 0.88, item_count=6, seed=2),
    )
    run = EvaluationRun(
        run_id="RUN-FIXTURE-0001",
        frozen_protocol=frozen,
        subject_kind=SubjectKind.COGNITIVE_RUNTIME,
        subject_id="RT-FIXTURE-A",
        observations=observations,
        framework="fixture-framework",
        framework_version="0.1",
        runtime_identity=fingerprint({"runtime": "RT-FIXTURE-A"}),
        contamination_grade=ContaminationClass.C0_NO_OBSERVED_OVERLAP,
        started_utc="2026-01-03T00:00:00Z",
        completed_utc="2026-01-03T00:42:00Z",
        seeds_used=2,
    )
    simulation = EvaluationRun(
        run_id="RUN-FIXTURE-0001-SIM",
        frozen_protocol=frozen,
        subject_kind=SubjectKind.COGNITIVE_RUNTIME,
        subject_id="RT-FIXTURE-A",
        observations=observations,
        framework="independent-fixture-framework",
        framework_version="0.1",
        runtime_identity=fingerprint({"runtime": "RT-FIXTURE-A"}),
        contamination_grade=ContaminationClass.C0_NO_OBSERVED_OVERLAP,
        started_utc="2026-01-03T01:00:00Z",
        completed_utc="2026-01-03T01:40:00Z",
        seeds_used=2,
    )
    assessment = assess_capability(
        run,
        baseline={"accuracy": 0.60, "calibration_error": 0.12},
        replication=ReproductionEvidence(
            frameworks=("fixture-framework", "independent-fixture-framework"),
            metric_agreement=FrozenMap(
                {"accuracy": True, "calibration_error": True, "instruction_adherence": True}
            ),
            max_delta=0.0,
            tolerance=bundle.protocol.tolerance,
            evidence_ref="receipts/mf-b4-evaluation.json#simulation_run",
            simulated=True,
        ),
        limitations=(
            "fixture benchmark with six items",
            "cross-runtime agreement is simulated on fixtures, not an independent implementation",
        ),
        oce_review_ref=None,
        # Honest claim: the second runtime is a fixture simulation, not an
        # independent implementation, so R1 is the strongest supported class.
        reproducibility=ReproducibilityClaim(
            claimed=ReproducibilityClass.R1_FRESH_ENVIRONMENT_REPLAY,
            environment_recorded=True,
            independent_implementation=False,
            external_replication=False,
            framework="fixture-framework",
            dependency_lock_digest="sha256:lock-fixture",
            container_digest="sha256:container-fixture",
            accelerator_identity="fixture-accelerator",
            driver_stack="fixture-driver-0.1",
            provider_details="fixture-provider-abstracted",
        ),
    )

    store = SealedEvaluationStore()
    store.register(
        SealedPayload(
            payload_id="SEALED-RB-V0",
            benchmark_id=bundle.benchmark.benchmark_id,
            tier=EvaluationTier.SEALED_CONFIRMATION,
            answer_key_digest="sha256:sealed-answer-key-fixture",
            items=("C-01", "C-02"),
            doctrine_bearing=False,
        ),
        registrar_role="SEALED_EVALUATOR",
    )
    builder_refusal = None
    try:
        store.read("SEALED-RB-V0", actor="builder-agent", role="BUILDER_AGENT", purpose="curiosity")
    except Exception as exc:  # noqa: BLE001 - refusal is the expected path
        builder_refusal = {"type": type(exc).__name__, "detail": str(exc)}

    negatives = NegativeKnowledgeStore()
    negatives.record(
        NegativeResult(
            negative_id="NEG-FIXTURE-0001",
            subject_kind=SubjectKind.COGNITIVE_RUNTIME,
            subject_id="RT-FIXTURE-B",
            hypothesis="longer continued pretraining improves calibration on the fixture benchmark",
            outcome="calibration_error did not move beyond the declared tolerance",
            conclusion=TerminalConclusion.UNDERPOWERED,
            evidence={"seeds_used": 2, "item_count": 6, "delta": -0.004},
            reopen_conditions=(
                "a powered run with >= 40 items and >= 3 seeds shows a calibration delta beyond tolerance",
            ),
            scope="fixture benchmark RESEARCH_BENCH_V0 only",
            recorded_utc="2026-01-03T02:00:00Z",
        )
    )

    payload = {
        "frozen_protocol": frozen.to_dict(),
        "run": run.to_dict(),
        "simulation_run": simulation.to_dict(),
        "assessment": assessment.to_dict(),
        "sealed_store": store.receipt().to_dict(),
        "builder_refusal": builder_refusal,
        "negative_knowledge": negatives.receipt().to_dict(),
    }
    _emit("mf-b4-evaluation", payload)
    print(f"frozen protocol   : {frozen.protocol.fingerprint}")
    print(f"terminal result   : {assessment.terminal_conclusion.value}")
    print(f"framework dep.    : {assessment.framework_dependence}")
    print(f"builder refusal   : {builder_refusal['type'] if builder_refusal else 'NONE'}")
    print(f"dogma risks       : {negatives.dogma_risks()}")
    return 0


def cmd_cross_block(_: argparse.Namespace) -> int:
    from .cross_block import cross_block_report

    report = cross_block_report()
    _emit("cross-block-scenarios", report)
    for scenario in report["scenarios"]:
        print(f"  {scenario['scenario_id']:4s} {scenario['status']:6s} {scenario['title']}")
    print(f"cross-block verdict={report['verdict']} held={report['scenarios_held']}/{report['scenarios_total']}")
    return 0 if report["verdict"] == "PASS" else 1


def _strip_run_timestamps(value: Any) -> Any:
    """Remove wall-clock stamps so a replay produces an identical digest.

    Event time is recorded in the receipts themselves; it must not change the
    fingerprint of the evidence that describes the substrate.
    """

    if isinstance(value, dict):
        return {
            key: _strip_run_timestamps(item)
            for key, item in value.items()
            if key != "recorded_utc"
        }
    if isinstance(value, list):
        return [_strip_run_timestamps(item) for item in value]
    return value


def evidence_payload() -> dict[str, Any]:
    """Aggregate the whole build into one reviewable, replay-stable artifact."""

    from .boundary import mf_b0_gate_report
    from .cross_block import cross_block_report

    bundle = load_bundle()
    registry = build_registry()
    offers = [normalize_offer(o) for o in bundle.observations]
    request = ComputeRequest(
        request_id="REQ-EVIDENCE",
        experiment_fingerprint=fingerprint({"experiment": "evidence"}),
        workload_class="RESEARCH_SMOKE",
        accelerator_class_required="ANY",
        accelerator_count=1,
        vram_gb_required=40.0,
        scratch_gb_required=40.0,
        expected_wall_hours=12.0,
        max_cost_to_close_usd=10.0,
        checkpoint_required=False,
        failure_tolerance="RETRYABLE",
    )
    decision = simulate_placement(request, offers, now_epoch_s=NOW_EPOCH)
    refinery = DatasetRefinery(registry=registry, contamination=bundle.contamination)
    train_run = refinery.refine(
        dataset_id="ds.evidence.train.v0",
        purpose="evidence corpus",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_NEWS_ALPHA", "SRC_NEWS_ALPHA_MIRROR", "SRC_AGENT_TRACE", "SRC_RIGHTS_UNKNOWN"],
    )
    gate = mf_b0_gate_report()
    cross = cross_block_report()
    payload: dict[str, Any] = {
        "generated_by": "python -m foundry.cli evidence",
        "note": "replay-stable: wall-clock receipt timestamps are excluded from the fingerprint",
        "blocks": ["MF-B0", "MF-B1", "MF-B2", "MF-B3", "MF-B4"],
        "constitution_fingerprint": CONSTITUTION.fingerprint,
        "doctrine": list(FOUNDRY_DOCTRINE),
        "b0_gate": {
            "verdict": gate["verdict"],
            "attacks_total": gate["attacks_total"],
            "attacks_refused": gate["attacks_refused"],
            "attacks_contained": gate["attacks_contained"],
            "attacks_failed_open": gate["attacks_failed_open"],
            "report_fingerprint": gate["report_fingerprint"],
        },
        "b1_placement": {
            "selected_offer_id": decision.selected_offer_id,
            "cost_to_close_usd": round(decision.selected_cost_to_close_usd, 6),
            "cheapest_hourly_eligible": decision.cheapest_hourly_offer_id,
            "hourly_trap_detected": decision.hourly_trap_detected,
            "offers_observed": len(offers),
            "providers": sorted({o.provider for o in offers}),
        },
        "b2_registry": {
            "registry_digest": registry.digest(),
            "role_distribution": registry.role_distribution(),
            "rights_blocked": registry.rights_blocked_sources(),
            "eligible_for_training": list(registry.trainable_sources()),
            "diversity": registry.effective_diversity(),
            "doctrine_bearing": list(registry.doctrine_bearing_sources()),
        },
        "b3_manifest": train_run.manifest.to_dict() if train_run.manifest else None,
        "b3_receipt": train_run.receipt.to_dict(),
        "b4": {
            "protocol_fingerprint": bundle.protocol.fingerprint,
            "benchmark": bundle.benchmark.to_dict(),
            "note": "freeze/refusal behaviour is exercised in the block receipt and cross-block F7/F8",
        },
        "cross_block": cross,
        "external_operations": {
            "public_read_only_calls": 0,
            "paid_compute": 0,
            "provider_launches": 0,
            "cloud_mutations": 0,
            "production_mutations": 0,
            "capital_operations": 0,
            "model_api_calls": 0,
        },
        "scientific_integrity": {
            "rights_blocks": registry.rights_blocked_sources(),
            "contamination_edges": bundle.contamination.to_dict()["edge_count"],
            "cerebus_exposures": 0,
            "sealed_eval_exposures": 0,
            "negative_results": 1,
        },
        "temporary_oce_fixtures": declaration_payload()["fixtures"],
        "limits": [
            "compute, evaluation, sealed confirmation and recovery are simulated on fixtures",
            "no provider adapter performs live reads in this build",
            "no model was trained; nothing here is a capability claim",
        ],
    }
    payload["receipt_timestamps_excluded"] = True
    payload = _strip_run_timestamps(payload)
    payload["evidence_fingerprint"] = fingerprint(payload)
    payload["verdict"] = "PASS" if (gate["verdict"] == "PASS" and cross["verdict"] == "PASS") else "FAIL"
    return payload


def cmd_evidence(_: argparse.Namespace) -> int:
    """Write the evidence package to receipts and to the docs tree."""

    payload = evidence_payload()
    _emit("mf-b0-b4-evidence", payload)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    write_json(EVIDENCE_DIR / "MF_B0_B4_EVIDENCE.json", payload)
    print(f"wrote {EVIDENCE_DIR / 'MF_B0_B4_EVIDENCE.json'}")
    print(f"evidence fingerprint: {payload['evidence_fingerprint']}")
    return 0 if payload["verdict"] == "PASS" else 1


def cmd_report(_: argparse.Namespace) -> int:
    from .boundary import mf_b0_gate_report

    outputs: dict[str, Any] = {"doctrine": list(FOUNDRY_DOCTRINE)}
    for name, fn in (
        ("b0_gate", cmd_b0_gate),
        ("b1_cost_close", cmd_b1_cost_close),
        ("b2_registry", cmd_b2_registry),
        ("b3_refine", cmd_b3_refine),
        ("b4_run", cmd_b4_run),
        ("cross_block", cmd_cross_block),
        ("evidence", cmd_evidence),
    ):
        code = fn(argparse.Namespace())
        outputs[name] = "ok" if code == 0 else f"exit={code}"
    gate = mf_b0_gate_report()
    summary = {
        "blocks": outputs,
        "b0_verdict": gate["verdict"],
        "b0_attacks_held": gate["attacks_held"],
        "b0_attacks_refused": gate["attacks_refused"],
        "b0_attacks_contained": gate["attacks_contained"],
        "constitution_fingerprint": CONSTITUTION.fingerprint,
        "receipt_fingerprint": fingerprint(outputs),
        "paid_compute_launched": False,
        "cloud_mutations": 0,
        "production_mutations": 0,
        "capital_operations": 0,
    }
    _emit("mf-b0-b4-summary", summary)
    return 0 if gate["verdict"] == "PASS" else 1


COMMANDS = {
    "doctrine": cmd_doctrine,
    "boundary": cmd_boundary,
    "b0-gate": cmd_b0_gate,
    "b1-cost-close": cmd_b1_cost_close,
    "b2-registry": cmd_b2_registry,
    "b3-refine": cmd_b3_refine,
    "b4-run": cmd_b4_run,
    "cross-block": cmd_cross_block,
    "evidence": cmd_evidence,
    "report": cmd_report,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="foundry", description="Larger Lab Model Foundry (offline)")
    parser.add_argument("command", choices=sorted(COMMANDS))
    args = parser.parse_args(argv)
    return COMMANDS[args.command](args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
