"""MF-B1 — provider-neutral compute, cost-to-close, budget and authorization."""

from __future__ import annotations

import dataclasses

import pytest

from foundry.core import PolicyBlocked, Unauthorized
from foundry.fixtures import load_observations
from foundry.providers import ADAPTERS, PROVIDER_OFFER_DOUBLE, normalize_offer
from foundry.resources import (
    BudgetLedger,
    ComputeOffer,
    ComputeRequest,
    OperatorGrant,
    PortableCheckpoint,
    assert_checkpoint_portable,
    assert_within_budget,
    classify_failure,
    estimate_cost_to_close,
    simulate_launch,
    simulate_placement,
    verify_operator_grant,
)

NOW = 1767225600


def _offers() -> list[ComputeOffer]:
    return [normalize_offer(observation) for observation in load_observations()]


def _request(**overrides: object) -> ComputeRequest:
    base: dict[str, object] = {
        "request_id": "REQ-1",
        "experiment_fingerprint": "sha256:exp",
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


def _grant(**overrides: object) -> OperatorGrant:
    base: dict[str, object] = {
        "grant_id": "GRANT-1",
        "granted_by": "OPERATOR",
        "granted_to_request": "REQ-1",
        "max_usd": 25.0,
        "expires_at_epoch_s": NOW + 3600,
        "purpose": "fixture run",
    }
    base.update(overrides)
    return OperatorGrant(**base)  # type: ignore[arg-type]


def test_request_has_no_provider_field_and_stays_provider_neutral() -> None:
    request = _request()
    assert "provider" not in request.to_dict()
    assert request.to_dict()["provider_field_present"] is False
    assert request.fingerprint == _request().fingerprint


def test_two_provider_dialects_normalize_to_the_same_contract() -> None:
    offers = {offer.offer_id: offer for offer in _offers()}
    octa = offers["octa_fixture:octa-gpu-4471"]
    runpod = offers["runpod_fixture:runpod-secure-8891"]
    assert set(octa.to_dict()) == set(runpod.to_dict())
    # Dialect conversion actually happened: cents/hour -> USD/hour, MB -> GB.
    assert runpod.price_usd_per_hour == pytest.approx(1.10)
    assert runpod.vram_gb == pytest.approx(80.0)
    assert runpod.container_support == "docker"


def test_raw_observation_is_retained_so_normalization_losses_stay_visible() -> None:
    offers = {offer.offer_id: offer for offer in _offers()}
    octa = offers["octa_fixture:octa-gpu-4471"]
    assert octa.raw_observation["raw"]["price_usd_per_hour"] == 0.25
    assert octa.normalization_losses == ("provider_advertised_reliability_not_mapped",)


def test_adapters_are_observation_only() -> None:
    for adapter in ADAPTERS.values():
        payload = adapter.to_dict()
        assert payload["can_launch_instances"] is False
        assert payload["mode"] in {"OBSERVE", "SIMULATE"}
        assert payload["noncanonical_declaration"]["noncanonical"] is True
    assert PROVIDER_OFFER_DOUBLE.canonical_oce_target.startswith("OCE B10")


def test_unknown_provider_and_incomplete_observation_are_refused() -> None:
    from foundry.providers import RawProviderObservation

    with pytest.raises(PolicyBlocked) as exc:
        normalize_offer(
            RawProviderObservation(
                provider="mystery_cloud",
                raw={"offer_id": "x", "accelerator": "A100_80G", "vram_gb": 80, "price_usd_per_hour": 1, "region": "r", "preemptible": False},
                observed_at_epoch_s=NOW,
                freshness_window_s=60,
            )
        )
    assert exc.value.code == "PROVIDER_ADAPTER_UNKNOWN"

    with pytest.raises(PolicyBlocked) as exc2:
        normalize_offer(
            RawProviderObservation(
                provider="runpod_fixture",
                raw={"offer_id": "x", "accelerator": "A100_80G", "region": "r", "preemptible": False},
                observed_at_epoch_s=NOW,
                freshness_window_s=60,
            )
        )
    assert exc2.value.code == "OFFER_OBSERVATION_INCOMPLETE"


def test_cost_to_close_beats_hourly_price() -> None:
    decision = simulate_placement(_request(), _offers(), now_epoch_s=NOW)
    assert decision.cheapest_hourly_offer_id == "octa_fixture:octa-gpu-4471"
    assert decision.cheapest_hourly_usd == pytest.approx(0.25)
    assert decision.selected_offer_id == "runpod_fixture:runpod-secure-8891"
    assert decision.hourly_trap_detected is True
    assert decision.selected_cost_to_close_usd < estimate_cost_to_close(
        _request(), next(o for o in _offers() if o.offer_id == "octa_fixture:octa-gpu-4471")
    ).cost_to_close_usd


def test_ineligible_offers_are_rejected_with_reasons() -> None:
    decision = simulate_placement(_request(), _offers(), now_epoch_s=NOW)
    rejected = {r["offer_id"]: r["reason"] for r in decision.rejected}
    assert rejected["local_cpu:local-workstation-0"] == "INSUFFICIENT_VRAM"
    assert rejected["runpod_fixture:runpod-secure-2200-stale"] == "OFFER_OBSERVATION_STALE"


def test_stale_offers_can_be_kept_when_the_caller_accepts_stale_observations() -> None:
    decision = simulate_placement(
        _request(), _offers(), now_epoch_s=NOW, stale_policy="ALLOW"
    )
    assert any("runpod-secure-2200-stale" in entry["offer_id"] for entry in decision.considered)


def test_checkpointing_reduces_preemption_cost() -> None:
    offers = _offers()
    octa = next(o for o in offers if o.offer_id == "octa_fixture:octa-gpu-4471")
    without = estimate_cost_to_close(_request(checkpoint_required=False), octa)
    with_ckpt = estimate_cost_to_close(_request(checkpoint_required=True), octa)
    assert with_ckpt.cost_to_close_usd < without.cost_to_close_usd
    assert with_ckpt.assumptions["checkpoint_credit_applied"] is True
    assertive = simulate_placement(
        _request(checkpoint_required=True), offers, now_epoch_s=NOW
    )
    assert assertive.selected_offer_id == "octa_fixture:octa-gpu-4471"


def test_preemptible_offer_refused_for_intolerant_workload() -> None:
    with pytest.raises(PolicyBlocked) as exc:
        simulate_placement(
            _request(
                failure_tolerance="NONE",
                accelerator_class_required="A6000",
            ),
            _offers(),
            now_epoch_s=NOW,
        )
    assert exc.value.code == "NO_ELIGIBLE_OFFER"


def test_provider_rename_does_not_change_scientific_placement() -> None:
    request = _request()
    original = simulate_placement(request, _offers(), now_epoch_s=NOW)
    renamed = simulate_placement(
        request,
        [dataclasses.replace(o, provider=f"vendor-{i}") for i, o in enumerate(_offers())],
        now_epoch_s=NOW,
    )
    assert original.selected_cost_to_close_usd == renamed.selected_cost_to_close_usd
    assert original.hourly_trap_detected == renamed.hourly_trap_detected


def test_budget_and_grant_are_both_required_for_a_paid_class_request() -> None:
    decision = simulate_placement(_request(), _offers(), now_epoch_s=NOW)
    offer = next(o for o in _offers() if o.offer_id == decision.selected_offer_id)

    with pytest.raises(Unauthorized) as exc:
        simulate_launch(
            _request(), decision, offer, now_epoch_s=NOW, mode="SIMULATE", operator_actor="OPERATOR"
        )
    assert exc.value.code == "OPERATOR_HOLD"

    with pytest.raises(Unauthorized) as exc2:
        simulate_launch(
            _request(),
            decision,
            offer,
            now_epoch_s=NOW,
            mode="SIMULATE",
            operator_actor="OPERATOR",
            grant=_grant(granted_by="BUILDER_AGENT"),
        )
    assert exc2.value.code == "GRANT_ISSUER_NOT_OPERATOR"

    with pytest.raises(Unauthorized) as exc3:
        simulate_launch(
            _request(),
            decision,
            offer,
            now_epoch_s=NOW,
            mode="SIMULATE",
            operator_actor="OPERATOR",
            grant=_grant(granted_to_request="OTHER-REQ"),
        )
    assert exc3.value.code == "GRANT_SUBJECT_MISMATCH"

    with pytest.raises(Unauthorized) as exc4:
        simulate_launch(
            _request(),
            decision,
            offer,
            now_epoch_s=NOW,
            mode="SIMULATE",
            operator_actor="OPERATOR",
            grant=_grant(expires_at_epoch_s=NOW - 1),
        )
    assert exc4.value.code == "GRANT_EXPIRED"


def test_budget_exhaustion_produces_operator_hold_not_spending() -> None:
    decision = simulate_placement(_request(), _offers(), now_epoch_s=NOW)
    offer = next(o for o in _offers() if o.offer_id == decision.selected_offer_id)
    budget = BudgetLedger(authorized_usd=0.5)
    with pytest.raises(Unauthorized) as exc:
        simulate_launch(
            _request(),
            decision,
            offer,
            now_epoch_s=NOW,
            mode="SIMULATE",
            budget=budget,
            grant=_grant(),
            operator_actor="OPERATOR",
        )
    assert exc.value.code == "BUDGET_EXCEEDED"
    assert exc.value.context["operator_hold"] is True
    assert budget.spent_usd == 0.0
    assert_within_budget(BudgetLedger(authorized_usd=10.0), 5.0) is None


def test_live_launch_path_does_not_exist() -> None:
    decision = simulate_placement(_request(), _offers(), now_epoch_s=NOW)
    offer = next(o for o in _offers() if o.offer_id == decision.selected_offer_id)
    with pytest.raises(PolicyBlocked) as exc:
        simulate_launch(
            _request(),
            decision,
            offer,
            now_epoch_s=NOW,
            mode="LIVE",
            grant=_grant(),
            operator_actor="OPERATOR",
        )
    assert exc.value.code == "LIVE_LAUNCH_NOT_AUTHORIZED"


def test_simulated_launch_receipt_claims_nothing_about_paid_hardware() -> None:
    decision = simulate_placement(_request(), _offers(), now_epoch_s=NOW)
    offer = next(o for o in _offers() if o.offer_id == decision.selected_offer_id)
    budget = BudgetLedger(authorized_usd=50.0)
    receipt = simulate_launch(
        _request(checkpoint_required=True),
        decision,
        offer,
        now_epoch_s=NOW,
        mode="SIMULATE",
        budget=budget,
        grant=_grant(),
        operator_actor="OPERATOR",
    )
    payload = receipt.to_dict()
    assert payload["paid_compute_consumed"] is False
    assert payload["cloud_mutations"] == 0
    assert payload["provider_identity_in_scientific_result"] is False
    assert payload["mode"] == "SIMULATE"
    assert payload["checkpoint_ref"].startswith("ckpt:")
    assert budget.spent_usd > 0


def test_checkpoint_portability_requires_an_open_export_format() -> None:
    portable = PortableCheckpoint(
        checkpoint_ref="ckpt:1",
        request_fingerprint="sha256:exp",
        framework="fixture",
        framework_version="0.1",
        optimizer_state_digest="sha256:opt",
        model_state_digest="sha256:model",
        rng_state_digest="sha256:rng",
        data_position_digest="sha256:pos",
        export_format="safetensors+json",
        portability_notes="open export",
    )
    assert_checkpoint_portable(portable)
    with pytest.raises(PolicyBlocked) as exc:
        assert_checkpoint_portable(dataclasses.replace(portable, export_format="framework-pickle"))
    assert exc.value.code == "CHECKPOINT_FORMAT_NOT_PORTABLE"


def test_resume_without_full_state_is_a_contradiction() -> None:
    from foundry.core import Contradiction

    portable = PortableCheckpoint(
        checkpoint_ref="ckpt:2",
        request_fingerprint="sha256:exp",
        framework="fixture",
        framework_version="0.1",
        optimizer_state_digest="sha256:opt",
        model_state_digest="sha256:model",
        rng_state_digest="",
        data_position_digest="sha256:pos",
        export_format="safetensors+json",
        portability_notes="missing rng",
    )
    with pytest.raises(Contradiction):
        assert_checkpoint_portable(portable)


def test_failure_taxonomy_keeps_unknown_unknown() -> None:
    assert classify_failure("PREEMPTED") == "resource"
    assert classify_failure("CUDA_MISMATCH") == "environment"
    assert classify_failure("OPERATOR_HOLD") == "authority"
    assert classify_failure("something-nobody-classified") == "unknown"


def test_verify_operator_grant_accepts_a_correct_grant() -> None:
    request = _request(workload_class="RESEARCH_SMOKE")
    verify_operator_grant(request, _grant(granted_to_request="REQ-1"), operator_actor="OPERATOR", now_epoch_s=NOW)
    assert request.requires_authorization() is False
    assert _request().requires_authorization() is True
