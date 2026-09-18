"""MF-B1 — Compute + Experiment Resource Layer.

Answers, before any model work happens:

    What resources exist, what does it actually cost to finish, and who is
    allowed to start spending?

Doctrine enforced here:

    PROVIDER OFFER != GUARANTEE
    HOURLY PRICE != COST-TO-CLOSE
    CAPABILITY != AUTHORITY

The layer is provider-neutral: a :class:`ComputeRequest` carries scientific
requirements and never a provider name, and provider identity is never an input
to scientific semantics. Selection optimizes **cost-to-close** rather than hourly
price, because the cheapest advertised hour routinely loses to a slightly more
expensive but more reliable, higher-throughput, or lower-preemption offer.

No code path in this module rents anything. ``launch`` only accepts offers
observed in a read-only or simulated mode and requires an explicit operator
grant; a provider accepted as *available* is still not an authorization.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .core import (
    Contradiction,
    FrozenMap,
    OceTestDouble,
    PolicyBlocked,
    Unauthorized,
    fingerprint,
)

RESOURCE_DOUBLE = OceTestDouble(
    fixture="FoundryLocalOfferNormalizer",
    canonical_oce_target="OCE B10 Resource Intelligence (COMPUTE.GPU.RENT)",
    replacement_condition="replace when B10 exposes provider-neutral offer/routing",
    retirement_evidence="Foundry submits ComputeRequest to B10 and consumes routing receipts",
)

RECOVERY_DOUBLE = OceTestDouble(
    fixture="FoundryLocalCheckpointRecovery",
    canonical_oce_target="OCE recovery/resume service",
    replacement_condition="replace when generic recovery exists",
    retirement_evidence="provider-loss recovery runs through canonical recovery service",
)

BUDGET_DOUBLE = OceTestDouble(
    fixture="FoundryLocalBudgetLedger",
    canonical_oce_target="OCE resource budget service",
    replacement_condition="replace when OCE budget authority is consumable",
    retirement_evidence="budget holds are issued by canonical budget service",
)

# Relative compute throughput per accelerator class for a fixed workload class.
# These are *fixture* performance coefficients, declared as such, and are the
# only place where hardware identity is allowed to influence planning.
THROUGHPUT_COEFFICIENTS: dict[str, float] = {
    "cpu-only": 0.02,
    "A4000": 1.0,
    "A5000": 1.3,
    "RTX_4090": 2.6,
    "A6000": 2.2,
    "L40S": 3.0,
    "A100_40G": 4.0,
    "A100_80G": 4.4,
    "H100_80G": 7.0,
}

LAUNCH_CLASSES_REQUIRING_AUTHORIZATION = (
    "TRAINING_FULL",
    "TRAINING_PARTIAL",
    "EVAL_SEALED",
    "DISTILLATION",
)


# --------------------------------------------------------------------------
# Requests and offers
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ComputeRequest:
    """A provider-neutral statement of scientific compute need.

    There is deliberately no ``provider`` field. Adding one would let resource
    vendor choice enter scientific semantics, which doctrine forbids.
    """

    request_id: str
    experiment_fingerprint: str
    workload_class: str
    accelerator_class_required: str
    accelerator_count: int
    vram_gb_required: float
    scratch_gb_required: float
    expected_wall_hours: float
    max_cost_to_close_usd: float
    checkpoint_required: bool
    failure_tolerance: str  # NONE / RETRYABLE
    data_transfer_gb: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "experiment_fingerprint": self.experiment_fingerprint,
            "workload_class": self.workload_class,
            "accelerator_class_required": self.accelerator_class_required,
            "accelerator_count": self.accelerator_count,
            "vram_gb_required": self.vram_gb_required,
            "scratch_gb_required": self.scratch_gb_required,
            "expected_wall_hours": self.expected_wall_hours,
            "max_cost_to_close_usd": self.max_cost_to_close_usd,
            "checkpoint_required": self.checkpoint_required,
            "failure_tolerance": self.failure_tolerance,
            "data_transfer_gb": self.data_transfer_gb,
            "notes": self.notes,
            "provider_field_present": False,
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())

    def requires_authorization(self) -> bool:
        return self.workload_class in LAUNCH_CLASSES_REQUIRING_AUTHORIZATION


@dataclass(frozen=True)
class ComputeOffer:
    """Normalized provider offer. ``PROVIDER OFFER != GUARANTEE``.

    ``adapter`` records *how* the offer was observed, never *what* it means
    scientifically. ``raw_observation`` is retained so normalization losses stay
    inspectable.
    """

    provider: str
    offer_id: str
    accelerator: str
    accelerator_count: int
    vram_gb: float
    system_ram_gb: float
    scratch_gb: float
    price_usd_per_hour: float
    storage_usd_per_gb_month: float
    egress_usd_per_gb: float
    region: str
    preemptible: bool
    preempt_probability_per_hour: float
    setup_overhead_minutes: float
    container_support: str
    trust_class: str
    observed_at_epoch_s: int
    freshness_window_s: int
    normalization_losses: tuple[str, ...] = ()
    adapter: str = ""
    raw_observation: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "offer_id": self.offer_id,
            "accelerator": self.accelerator,
            "accelerator_count": self.accelerator_count,
            "vram_gb": self.vram_gb,
            "system_ram_gb": self.system_ram_gb,
            "scratch_gb": self.scratch_gb,
            "price_usd_per_hour": self.price_usd_per_hour,
            "storage_usd_per_gb_month": self.storage_usd_per_gb_month,
            "egress_usd_per_gb": self.egress_usd_per_gb,
            "region": self.region,
            "preemptible": self.preemptible,
            "preempt_probability_per_hour": self.preempt_probability_per_hour,
            "setup_overhead_minutes": self.setup_overhead_minutes,
            "container_support": self.container_support,
            "trust_class": self.trust_class,
            "observed_at_epoch_s": self.observed_at_epoch_s,
            "freshness_window_s": self.freshness_window_s,
            "normalization_losses": list(self.normalization_losses),
            "adapter": self.adapter,
            "guarantee": "OBSERVED_ONLY_NOT_GUARANTEED",
        }

    def is_stale(self, *, now_epoch_s: int) -> bool:
        return (now_epoch_s - self.observed_at_epoch_s) > self.freshness_window_s

    def throughput_coefficient(self) -> float:
        coefficient = THROUGHPUT_COEFFICIENTS.get(self.accelerator)
        if coefficient is None:
            # Unknown hardware is not assumed fast.
            return min(THROUGHPUT_COEFFICIENTS.values())
        return coefficient


# --------------------------------------------------------------------------
# Cost-to-close
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CostToCloseEstimate:
    """Cost of *finishing*, not cost of *being rented*."""

    offer_id: str
    provider: str
    hourly_usd: float
    effective_wall_hours: float
    expected_preemption_retries: float
    compute_usd: float
    storage_usd: float
    egress_usd: float
    setup_usd: float
    cost_to_close_usd: float
    assumptions: FrozenMap

    def to_dict(self) -> dict[str, Any]:
        return {
            "offer_id": self.offer_id,
            "provider": self.provider,
            "hourly_usd": round(self.hourly_usd, 6),
            "effective_wall_hours": round(self.effective_wall_hours, 6),
            "expected_preemption_retries": round(self.expected_preemption_retries, 6),
            "compute_usd": round(self.compute_usd, 6),
            "storage_usd": round(self.storage_usd, 6),
            "egress_usd": round(self.egress_usd, 6),
            "setup_usd": round(self.setup_usd, 6),
            "cost_to_close_usd": round(self.cost_to_close_usd, 6),
            "assumptions": dict(self.assumptions),
        }


def estimate_cost_to_close(
    request: ComputeRequest,
    offer: ComputeOffer,
    *,
    retention_days: float = 30.0,
) -> CostToCloseEstimate:
    """Deterministic cost-to-close for one request/offer pair.

    Components:

    * throughput adjustment — slow hardware needs more billable hours;
    * preemption overhead — retries and lost progress, using a geometric-loss
      approximation with checkpoint credit when the request checkpoints;
    * setup overhead — provisioning and image pull, billed;
    * storage and egress — the costs that hourly price tags hide.
    """

    coefficient = offer.throughput_coefficient()
    if coefficient <= 0:
        raise PolicyBlocked(
            "THROUGHPUT_COEFFICIENT_INVALID",
            f"{offer.offer_id}: non-positive throughput coefficient",
        )

    base_wall_hours = request.expected_wall_hours / coefficient
    # Probability that at least one preemption lands inside the run.
    q = 1.0 - math.exp(-max(0.0, offer.preempt_probability_per_hour) * base_wall_hours)
    if offer.preemptible:
        # Checkpointing converts lost work into overhead rather than total restart.
        loss_fraction = 0.35 if request.checkpoint_required else 1.0
        # q is capped below 1 by construction (max(1e-9, 1 - q)), so the
        # geometric-loss ratio stays finite; NaN cannot reach here because
        # max(0.0, rate * hours) floors the exponent input at 0.
        expected_retries = min(2.0, q / max(1e-9, 1.0 - q))
        effective_wall_hours = base_wall_hours + (base_wall_hours * loss_fraction * expected_retries)
    else:
        expected_retries = 0.0
        effective_wall_hours = base_wall_hours

    setup_hours = offer.setup_overhead_minutes / 60.0
    compute_usd = (effective_wall_hours + setup_hours) * offer.price_usd_per_hour
    storage_gb = max(request.scratch_gb_required, offer.scratch_gb * 0.0 + request.scratch_gb_required)
    storage_usd = (
        storage_gb * offer.storage_usd_per_gb_month * (retention_days / 30.0)
    )
    egress_usd = request.data_transfer_gb * offer.egress_usd_per_gb
    setup_usd = setup_hours * offer.price_usd_per_hour

    return CostToCloseEstimate(
        offer_id=offer.offer_id,
        provider=offer.provider,
        hourly_usd=offer.price_usd_per_hour,
        effective_wall_hours=effective_wall_hours + setup_hours,
        expected_preemption_retries=expected_retries,
        compute_usd=compute_usd,
        storage_usd=storage_usd,
        egress_usd=egress_usd,
        setup_usd=setup_usd,
        cost_to_close_usd=compute_usd + storage_usd + egress_usd,
        assumptions=FrozenMap(
            {
                "throughput_coefficient": coefficient,
                "checkpoint_credit_applied": bool(offer.preemptible and request.checkpoint_required),
                "retention_days": retention_days,
                "price_is_usd_per_hour_observed": True,
                "cost_model": "setup+throughput+preemption+storage+egress",
            }
        ),
    )


# --------------------------------------------------------------------------
# Placement (provider-neutral)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PlacementDecision:
    request_fingerprint: str
    selected_offer_id: str
    selected_cost_to_close_usd: float
    considered: tuple[dict[str, Any], ...]
    rejected: tuple[dict[str, Any], ...]
    cheapest_hourly_offer_id: str | None
    cheapest_hourly_usd: float | None
    cheapest_observed_hourly_offer_id: str | None
    hourly_trap_detected: bool
    within_budget: bool
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_fingerprint": self.request_fingerprint,
            "selected_offer_id": self.selected_offer_id,
            "selected_cost_to_close_usd": round(self.selected_cost_to_close_usd, 6),
            "considered": list(self.considered),
            "rejected": list(self.rejected),
            "cheapest_hourly_offer_id": self.cheapest_hourly_offer_id,
            "cheapest_hourly_usd": self.cheapest_hourly_usd,
            "cheapest_observed_hourly_offer_id": self.cheapest_observed_hourly_offer_id,
            "hourly_trap_detected": self.hourly_trap_detected,
            "hourly_trap_scope": "cheapest hourly price among eligible offers did not win on cost-to-close",
            "within_budget": self.within_budget,
            "rationale": self.rationale,
        }


def simulate_placement(
    request: ComputeRequest,
    offers: list[ComputeOffer],
    *,
    now_epoch_s: int,
    stale_policy: str = "EXCLUDE",
) -> PlacementDecision:
    """Choose an offer by cost-to-close. Providers are interchangeable inputs.

    Eligibility is a scientific/hardware question (VRAM, accelerator class,
    scratch, count), never a vendor question.
    """

    if not offers:
        raise PolicyBlocked("NO_OFFERS", "placement requires at least one observed offer")

    rejected: list[dict[str, Any]] = []
    eligible: list[tuple[CostToCloseEstimate, ComputeOffer]] = []
    for offer in sorted(offers, key=lambda o: o.offer_id):
        reason = None
        if offer.accelerator != request.accelerator_class_required and request.accelerator_class_required != "ANY":
            reason = "ACCELERATOR_CLASS_MISMATCH"
        elif offer.accelerator_count < request.accelerator_count:
            reason = "INSUFFICIENT_ACCELERATORS"
        elif offer.vram_gb * offer.accelerator_count < request.vram_gb_required:
            reason = "INSUFFICIENT_VRAM"
        elif offer.scratch_gb < request.scratch_gb_required:
            reason = "INSUFFICIENT_SCRATCH"
        elif offer.is_stale(now_epoch_s=now_epoch_s) and stale_policy == "EXCLUDE":
            reason = "OFFER_OBSERVATION_STALE"
        elif offer.preemptible and request.failure_tolerance == "NONE":
            reason = "PREEMPTIBLE_REFUSED_FOR_INTOLERANT_WORKLOAD"
        if reason:
            rejected.append({"offer_id": offer.offer_id, "provider": offer.provider, "reason": reason})
            continue
        eligible.append((estimate_cost_to_close(request, offer), offer))

    if not eligible:
        raise PolicyBlocked(
            "NO_ELIGIBLE_OFFER",
            "no observed offer satisfies the scientific requirements",
            rejected=rejected,
            request=request.to_dict(),
        )

    eligible.sort(key=lambda pair: (pair[0].cost_to_close_usd, pair[0].offer_id))
    best_estimate, _best_offer = eligible[0]

    # The hourly trap is measured among *eligible* offers, so an inadmissible
    # free offer can never be mistaken for a price argument.
    cheapest_hourly_eligible = min(
        eligible, key=lambda pair: (pair[1].price_usd_per_hour, pair[1].offer_id)
    )[1]
    cheapest_hourly_observed = min(offers, key=lambda o: (o.price_usd_per_hour, o.offer_id))
    hourly_trap = cheapest_hourly_eligible.offer_id != best_estimate.offer_id

    within_budget = best_estimate.cost_to_close_usd <= request.max_cost_to_close_usd
    rationale = (
        "selected by minimum cost-to-close"
        if not hourly_trap
        else "hourly-cheapest eligible offer loses on cost-to-close; provider hours are not the cost of finishing"
    )

    return PlacementDecision(
        request_fingerprint=request.fingerprint,
        selected_offer_id=best_estimate.offer_id,
        selected_cost_to_close_usd=best_estimate.cost_to_close_usd,
        considered=tuple(estimate.to_dict() for estimate, _ in eligible),
        rejected=tuple(rejected),
        cheapest_hourly_offer_id=cheapest_hourly_eligible.offer_id,
        cheapest_hourly_usd=cheapest_hourly_eligible.price_usd_per_hour,
        cheapest_observed_hourly_offer_id=cheapest_hourly_observed.offer_id,
        hourly_trap_detected=hourly_trap,
        within_budget=within_budget,
        rationale=rationale,
    )


# --------------------------------------------------------------------------
# Budget + authorization
# --------------------------------------------------------------------------


@dataclass
class BudgetLedger:
    """Simulated, explicit budget authority. Not a spend system."""

    authorized_usd: float
    spent_usd: float = 0.0
    holds: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "authorized_usd": self.authorized_usd,
            "spent_usd": self.spent_usd,
            "remaining_usd": self.authorized_usd - self.spent_usd,
            "holds": list(self.holds),
        }


def assert_within_budget(budget: BudgetLedger, amount_usd: float) -> None:
    if budget.spent_usd + amount_usd > budget.authorized_usd:
        raise Unauthorized(
            "BUDGET_EXCEEDED",
            (
                f"cost-to-close {amount_usd:.2f} USD would exceed authorized "
                f"{budget.authorized_usd:.2f} USD (spent {budget.spent_usd:.2f})"
            ),
            operator_hold=True,
        )


@dataclass(frozen=True)
class OperatorGrant:
    """Explicit, single-purpose operator authorization to spend real money.

    ``granted_by`` must be an operator actor. A grant is required *in addition*
    to an available provider: availability is not permission.
    """

    grant_id: str
    granted_by: str
    granted_to_request: str
    max_usd: float
    expires_at_epoch_s: int
    purpose: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "grant_id": self.grant_id,
            "granted_by": self.granted_by,
            "granted_to_request": self.granted_to_request,
            "max_usd": self.max_usd,
            "expires_at_epoch_s": self.expires_at_epoch_s,
            "purpose": self.purpose,
            "self_declared_authority_accepted": False,
        }


def verify_operator_grant(
    request: ComputeRequest,
    grant: OperatorGrant | None,
    *,
    operator_actor: str,
    now_epoch_s: int,
) -> None:
    """Fail closed. Missing/expired/mismatched grants never become permission."""

    if grant is None:
        raise Unauthorized(
            "OPERATOR_HOLD",
            f"no operator grant for paid compute on {request.request_id}; Foundry may not authorize its own spending",
            operator_hold=True,
        )
    if grant.granted_by != operator_actor:
        raise Unauthorized(
            "GRANT_ISSUER_NOT_OPERATOR",
            f"grant {grant.grant_id} was issued by {grant.granted_by!r}, not the operator actor",
            operator_hold=True,
        )
    if grant.granted_to_request != request.request_id:
        raise Unauthorized(
            "GRANT_SUBJECT_MISMATCH",
            f"grant {grant.grant_id} does not authorize request {request.request_id!r}",
            operator_hold=True,
        )
    if grant.expires_at_epoch_s < now_epoch_s:
        raise Unauthorized(
            "GRANT_EXPIRED",
            f"grant {grant.grant_id} expired at {grant.expires_at_epoch_s}",
            operator_hold=True,
        )


# --------------------------------------------------------------------------
# Simulated launch + receipts
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ComputeReceipt:
    """What actually ran. Claims nothing about real paid hardware."""

    request_id: str
    request_fingerprint: str
    offer_id: str
    provider: str
    mode: str
    estimate: dict[str, Any]
    grant_id: str | None
    checkpoint_ref: str | None
    outcome: str
    failure_class: str | None
    provider_identity_in_scientific_result: bool
    notes: str
    paid_compute_consumed: bool = False
    cloud_mutations: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "request_fingerprint": self.request_fingerprint,
            "offer_id": self.offer_id,
            "provider": self.provider,
            "mode": self.mode,
            "estimate": self.estimate,
            "grant_id": self.grant_id,
            "checkpoint_ref": self.checkpoint_ref,
            "outcome": self.outcome,
            "failure_class": self.failure_class,
            "provider_identity_in_scientific_result": self.provider_identity_in_scientific_result,
            "notes": self.notes,
            "paid_compute_consumed": self.paid_compute_consumed,
            "cloud_mutations": self.cloud_mutations,
        }


FAILURE_TAXONOMY = {
    "PROVIDER_UNAVAILABLE": "resource",
    "PREEMPTED": "resource",
    "IMAGE_INCOMPATIBLE": "environment",
    "CUDA_MISMATCH": "environment",
    "DATASET_INTEGRITY": "data",
    "NUMERICAL_DIVERGENCE": "scientific",
    "OPERATOR_HOLD": "authority",
    "UNKNOWN": "unknown",
}


def classify_failure(signal: str) -> str:
    """Deterministic failure classification. UNKNOWN stays unknown."""

    return FAILURE_TAXONOMY.get(signal, "unknown")


def simulate_launch(
    request: ComputeRequest,
    decision: PlacementDecision,
    offer: ComputeOffer,
    *,
    now_epoch_s: int,
    mode: str,
    budget: BudgetLedger | None = None,
    grant: OperatorGrant | None = None,
    operator_actor: str,
) -> ComputeReceipt:
    """Run a *simulated* placement. Real rental is not implemented by design.

    ``mode`` must be ``SIMULATE`` (fixtures) — this function refuses ``LIVE``
    so that no accidental paid path exists in this build.
    """

    if mode != "SIMULATE":
        raise PolicyBlocked(
            "LIVE_LAUNCH_NOT_AUTHORIZED",
            (
                "real provider launch is outside MF-B0..B4 scope; a live path "
                "requires explicit operator authorization and a costed MF-B5 gate"
            ),
            operator_hold=True,
        )

    if request.requires_authorization():
        verify_operator_grant(
            request, grant, operator_actor=operator_actor, now_epoch_s=now_epoch_s
        )

    if budget is not None:
        assert_within_budget(budget, decision.selected_cost_to_close_usd)
        budget.spent_usd += decision.selected_cost_to_close_usd

    estimate = estimate_cost_to_close(request, offer)
    checkpoint_ref = (
        f"ckpt:{fingerprint({'request': request.fingerprint, 'offer': offer.offer_id})[:23]}"
        if request.checkpoint_required
        else None
    )
    return ComputeReceipt(
        request_id=request.request_id,
        request_fingerprint=request.fingerprint,
        offer_id=offer.offer_id,
        provider=offer.provider,
        mode=mode,
        estimate=estimate.to_dict(),
        grant_id=grant.grant_id if grant else None,
        checkpoint_ref=checkpoint_ref,
        outcome="SIMULATED_COMPLETE",
        failure_class=None,
        provider_identity_in_scientific_result=False,
        notes="simulated placement; no paid resource contacted",
    )


# --------------------------------------------------------------------------
# Checkpoint portability (provider loss is not scientific loss)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class PortableCheckpoint:
    """Framework-agnostic checkpoint identity so training is resumable elsewhere."""

    checkpoint_ref: str
    request_fingerprint: str
    framework: str
    framework_version: str
    optimizer_state_digest: str
    model_state_digest: str
    rng_state_digest: str
    data_position_digest: str
    export_format: str
    portability_notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "checkpoint_ref": self.checkpoint_ref,
            "request_fingerprint": self.request_fingerprint,
            "framework": self.framework,
            "framework_version": self.framework_version,
            "optimizer_state_digest": self.optimizer_state_digest,
            "model_state_digest": self.model_state_digest,
            "rng_state_digest": self.rng_state_digest,
            "data_position_digest": self.data_position_digest,
            "export_format": self.export_format,
            "portability_notes": self.portability_notes,
        }

    @property
    def fingerprint(self) -> str:
        return fingerprint(self.to_dict())


def assert_checkpoint_portable(checkpoint: PortableCheckpoint) -> None:
    """A checkpoint is portable only if it is *not* framework-locked."""

    if checkpoint.export_format not in {"safetensors+json", "numpy+json"}:
        raise PolicyBlocked(
            "CHECKPOINT_FORMAT_NOT_PORTABLE",
            f"{checkpoint.export_format!r} is framework-locked; provider/framework loss would lose the run",
        )
    for name in ("optimizer_state_digest", "model_state_digest", "rng_state_digest", "data_position_digest"):
        if not str(getattr(checkpoint, name)).strip():
            raise Contradiction(
                f"{checkpoint.checkpoint_ref}: resume requires {name}; cannot claim resumability without it"
            )


__all__ = [
    "BUDGET_DOUBLE",
    "FAILURE_TAXONOMY",
    "LAUNCH_CLASSES_REQUIRING_AUTHORIZATION",
    "RECOVERY_DOUBLE",
    "RESOURCE_DOUBLE",
    "THROUGHPUT_COEFFICIENTS",
    "BudgetLedger",
    "ComputeOffer",
    "ComputeReceipt",
    "ComputeRequest",
    "CostToCloseEstimate",
    "OperatorGrant",
    "PlacementDecision",
    "PortableCheckpoint",
    "assert_checkpoint_portable",
    "assert_within_budget",
    "classify_failure",
    "estimate_cost_to_close",
    "simulate_launch",
    "simulate_placement",
    "verify_operator_grant",
]
