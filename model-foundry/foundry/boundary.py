"""MF-B0 enforcement: constitutional guards + the 20-attack adversarial suite.

Every shortcut the Foundry is forbidden to take is implemented here as a guard
that *fails closed*, plus an attack that actually attempts the shortcut. The
MF-B0 gate passes only when every attack is refused.

Nothing in this module makes the Foundry more powerful; it only makes improper
shortcuts impossible to perform quietly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .constitution import (
    CONSTITUTION,
    LIFECYCLE_MACHINES,
    LifecycleSnapshot,
    assert_within_authority_ceiling,
    permit_credit,
    undeclared_generic_services,
)
from .core import (
    Contradiction,
    OceTestDouble,
    PolicyBlocked,
    Unauthorized,
    fingerprint,
)
from .enums import (
    CLAIM_CLASS_RANK,
    CLAIM_DEGRADING_CONTAMINATION,
    CONTAMINATION_SEVERITY,
    EvaluationTier,
    ClaimClass,
    ContaminationClass,
    RightsState,
    SourceRole,
    SubjectKind,
    TIER_RANK,
    TerminalConclusion,
)

# --------------------------------------------------------------------------
# Guards
# --------------------------------------------------------------------------


def assert_not_canonical_authority(declaration: OceTestDouble | None, *, subject: str) -> None:
    """A local fixture can never claim canonical institutional authority."""

    if declaration is None:
        raise PolicyBlocked(
            "NONCANONICAL_DECLARATION_REQUIRED",
            f"{subject!r} is a generic-looking local service without an OCE replacement declaration",
        )
    # A malformed/hand-rolled declaration object is treated as a canonical claim,
    # not as a missing one: absence of the flag must never read as permission.
    if getattr(declaration, "noncanonical", None) is not True:
        raise Unauthorized(
            "FIXTURE_CLAIMS_CANONICAL_AUTHORITY",
            f"{subject!r} declared itself canonical; the Foundry owns no institutional authority",
        )


def assert_capability_promotion_requires_review(*, self_review: bool, oce_review_ref: str | None) -> None:
    """score -> capability truth is a forbidden shortcut."""

    if self_review or not oce_review_ref:
        raise Unauthorized(
            "CAPABILITY_SELF_PROMOTION_REFUSED",
            "Foundry capability evidence cannot become institutional capability truth without OCE review",
        )


def assert_subject_credit(
    observed: SubjectKind, claimed: SubjectKind, *, attribution_study: str | None = None
) -> None:
    if not permit_credit(observed, claimed, attribution_study=attribution_study):
        raise PolicyBlocked(
            "SUBJECT_CREDIT_COLLAPSE_REFUSED",
            f"{observed.value} result cannot be credited as {claimed.value}",
            observed=observed.value,
            claimed=claimed.value,
        )


def derived_role(parent_roles: tuple[SourceRole, ...]) -> SourceRole:
    """Derived artifacts inherit ancestor restrictions by default.

    A derived record is eligible for training only if every ancestor was. Nothing
    in the transform path launders a retrieval-only or eval ancestor.
    """

    blocked = [
        role
        for role in parent_roles
        if role in {SourceRole.RETRIEVAL_ONLY, SourceRole.QUARANTINED, SourceRole.EXCLUDED, SourceRole.UNASSIGNED}
        or role.value.endswith("_EVAL")
        or role == SourceRole.SEALED_CONFIRMATION
        or role == SourceRole.HIDDEN_EVAL
        or role == SourceRole.BLIND_DISCOVERY
    ]
    if blocked:
        return SourceRole.QUARANTINED
    return SourceRole.TRAIN_CPT


def rights_permit_training(state: RightsState) -> bool:
    """UNKNOWN / REVIEW_REQUIRED / RESTRICTED / EXCLUDED never authorize training."""

    return state == RightsState.RIGHTS_VERIFIED_BY_POLICY


def assert_trainable(state: RightsState) -> None:
    if not rights_permit_training(state):
        raise PolicyBlocked(
            "RIGHTS_BLOCKED",
            f"rights state {state.value} does not authorize model training",
            rights_state=state.value,
        )


def grade_contamination(pairs: tuple[tuple[str, ContaminationClass], ...]) -> ContaminationClass:
    """Graded contamination. C0 alone does not mean 'proven clean' unless specified."""

    if not pairs:
        return ContaminationClass.C0_NO_OBSERVED_OVERLAP
    worst = max(pairs, key=lambda p: CONTAMINATION_SEVERITY[p[1]])[1]
    return worst


def assert_no_claim_degrading_contamination(grade: ContaminationClass, *, claim_label: str) -> None:
    if grade in CLAIM_DEGRADING_CONTAMINATION:
        raise PolicyBlocked(
            "CONTAMINATION_BLOCKED",
            f"{claim_label} cannot be asserted at contamination grade {grade.value}",
            grade=grade.value,
        )


def assert_tier_change_allowed(
    current: EvaluationTier,
    requested: EvaluationTier,
    *,
    new_protected_task_set: bool,
    actor_is_builder: bool,
) -> None:
    """No result (and no builder) can upgrade its own evaluation tier."""

    if TIER_RANK[requested] > TIER_RANK[current]:
        if actor_is_builder:
            raise Unauthorized(
                "TIER_SELF_UPGRADE_REFUSED",
                "a builder cannot upgrade its own evaluation tier",
                current=current.value,
                requested=requested.value,
            )
        if not new_protected_task_set:
            raise PolicyBlocked(
                "TIER_UPGRADE_REQUIRES_NEW_PROTECTED_SET",
                "a widely exposed benchmark cannot be relabeled without a new protected task set/version",
                current=current.value,
                requested=requested.value,
            )


def max_claim_class(*, upstream_provenance_known: bool, doctrine_leak: bool, doctrine_revealed: bool) -> ClaimClass:
    """A pretrained base with unknown ancestry cannot receive the strongest label."""

    if doctrine_revealed:
        return ClaimClass.POST_REVEAL_REPRODUCTION
    if not upstream_provenance_known or doctrine_leak:
        return ClaimClass.BLIND_TASK_PERFORMANCE
    return ClaimClass.CONTROLLED_INDEPENDENT_REDISCOVERY


def assert_claim_class(requested: ClaimClass, *, upstream_provenance_known: bool, doctrine_leak: bool, doctrine_revealed: bool) -> None:
    allowed = max_claim_class(
        upstream_provenance_known=upstream_provenance_known,
        doctrine_leak=doctrine_leak,
        doctrine_revealed=doctrine_revealed,
    )
    if CLAIM_CLASS_RANK[requested] > CLAIM_CLASS_RANK[allowed]:
        raise PolicyBlocked(
            "CLAIM_CLASS_LAUNDERING_REFUSED",
            f"requested {requested.value} exceeds the supported {allowed.value}",
            requested=requested.value,
            allowed=allowed.value,
        )


@dataclass(frozen=True)
class DoctrineSignature:
    """Deterministic shape signature of withheld doctrine.

    Detection is structural (exact thresholds, numeric tuples, rule-table
    geometry) rather than vocabulary-based, so stripping CEREBUS terminology
    does not defeat it.
    """

    rule_ids: tuple[str, ...]
    exact_numbers: tuple[str, ...]
    structural_tokens: tuple[str, ...]

    def matches(self, candidate_tokens: tuple[str, ...]) -> bool:
        token_set = {t.strip().lower() for t in candidate_tokens if t.strip()}
        numbers = {n for n in self.exact_numbers if n in token_set}
        tokens = {t for t in self.structural_tokens if t.lower() in token_set}
        return len(numbers) >= 1 and len(tokens) >= 1


def doctrine_shape_leak(signature: DoctrineSignature, candidate_tokens: tuple[str, ...]) -> bool:
    """A doctrine-shape leak without CEREBUS vocabulary still blocks strongest claim."""

    return signature.matches(candidate_tokens)


def assert_no_pnl_validity_bypass(*, pnl: float, validity_ratio: float | None) -> None:
    """paper/PnL claim -> scientific validity is a forbidden shortcut."""

    if validity_ratio is None:
        raise PolicyBlocked(
            "PNL_VALIDITY_BYPASS_REFUSED",
            "realized PnL is not scientific validity and cannot substitute for a validity ratio",
            pnl=pnl,
        )


def assert_capability_gain_does_not_expand_authority(*, capability_delta: float, grant_set_before: tuple[str, ...], grant_set_after: tuple[str, ...]) -> None:
    if tuple(sorted(grant_set_before)) != tuple(sorted(grant_set_after)):
        raise Unauthorized(
            "CAPABILITY_AUTHORITY_CONFUSION",
            "a capability change must not change the grant set",
            capability_delta=capability_delta,
        )


@dataclass(frozen=True)
class CheckpointPlan:
    locations: tuple[str, ...]
    integrity_hash: str | None
    resume_semantics: str | None
    max_recomputation_hours: float | None

    def validate(self) -> None:
        if len(self.locations) < 2:
            raise PolicyBlocked(
                "PROVIDER_LOSS_CAN_STRAND_ARTIFACTS",
                "a material run needs at least two checkpoint locations",
                locations=list(self.locations),
            )
        if not (self.integrity_hash and self.resume_semantics and self.max_recomputation_hours is not None):
            raise PolicyBlocked(
                "CHECKPOINT_PLAN_INCOMPLETE",
                "checkpoint integrity/resume/recomputation semantics are required",
            )


@dataclass(frozen=True)
class RemoteCredential:
    credential_id: str
    scope: tuple[str, ...]
    durable: bool
    can_grant_authority: bool

    def assert_rental_boundary(self) -> None:
        if self.durable or self.can_grant_authority:
            raise Unauthorized(
                "RENTAL_DURABLE_AUTHORITY_REFUSED",
                "rental compute credentials must be ephemeral and carry no durable authority",
                credential=self.credential_id,
            )


def assert_failure_lineage(total_runs: int, successes: int, failures_recorded: int) -> None:
    if successes + failures_recorded != total_runs:
        raise PolicyBlocked(
            "FAILURE_LINEAGE_INCOMPLETE",
            "reliability cannot be reported from survivors only",
            total=total_runs,
            successes=successes,
            failures_recorded=failures_recorded,
        )


def assert_operator_preference_does_not_alter_evaluator(
    *, preference: str, protocol_fingerprint_before: str, protocol_fingerprint_after: str
) -> None:
    if protocol_fingerprint_before != protocol_fingerprint_after:
        raise Unauthorized(
            "OPERATOR_PREFERENCE_ALTERED_EVALUATOR",
            "operator preference may set priorities and budgets, not evidence grade",
            preference=preference,
        )


def effective_independence(
    *, shared_teacher: bool, shared_evaluator: bool, shared_training_data: bool, architecture_distinct: bool
) -> str:
    """Architecture difference cannot manufacture independence."""

    if shared_teacher or shared_evaluator or shared_training_data:
        return "SHARED_LINEAGE"
    if architecture_distinct:
        return "INDEPENDENT_MULTI_AXIS"
    return "INDEPENDENT_UNVERIFIED"


def assert_conclusion_allowed(requested: TerminalConclusion, *, power_adequate: bool, sample_adequate: bool) -> None:
    """Insufficient compute/sample/evidence can never become a silent PASS/FAIL."""

    if requested in {TerminalConclusion.PASS, TerminalConclusion.FAIL} and not (power_adequate and sample_adequate):
        raise PolicyBlocked(
            "UNDERPOWERED_PASS_REFUSED",
            "underpowered evidence may only terminate as UNDERPOWERED/INCONCLUSIVE",
            requested=requested.value,
        )


def classify_novel_behavior(*, fits_taxonomy: bool, evidence_strength: str) -> str:
    """Novel behavior is preserved rather than force-classified into the nearest category."""

    if evidence_strength == "UNKNOWN":
        return "UNRESOLVED_CAPABILITY_PATTERN"
    if not fits_taxonomy:
        return "UNRESOLVED_CAPABILITY_PATTERN"
    return "CLASSIFIED"


# --------------------------------------------------------------------------
# MF-B0 adversarial suite (20 attacks)
# --------------------------------------------------------------------------


#: Defense outcomes that are not exceptions but still mean the attack failed.
#: A guard may refuse by raising (REFUSED) or by returning a contained state
#: (CONTAINED). Anything else is the attack getting through.
SAFE_CONTAINMENT_MARKERS: frozenset[str] = frozenset(
    {
        "QUARANTINED",
        "LEAK_DETECTED",
        "SHARED_LINEAGE",
        "INDEPENDENT_UNVERIFIED",
        "UNRESOLVED_CAPABILITY_PATTERN",
        "ALL_FIXTURES_DECLARED_AND_REPLACEABLE",
    }
)


@dataclass(frozen=True)
class AttackResult:
    attack_id: str
    attack: str
    expected: str
    observed: str
    verdict: str
    detail: str

    @property
    def held(self) -> bool:
        return self.verdict in {"REFUSED", "CONTAINED"}

    def to_dict(self) -> dict[str, Any]:
        return {
            "attack_id": self.attack_id,
            "attack": self.attack,
            "expected": self.expected,
            "observed": self.observed,
            "verdict": self.verdict,
            "held": self.held,
            "detail": self.detail,
        }


def _run(attack_id: str, attack: str, expected: str, fn: Callable[[], Any]) -> AttackResult:
    """Execute one adversarial attempt and classify how the defense responded.

    * ``PolicyBlocked`` / ``Unauthorized`` -> REFUSED (the guard raised).
    * a return value inside :data:`SAFE_CONTAINMENT_MARKERS` -> CONTAINED.
    * ``Contradiction`` -> FAILED_OPEN, because in this suite contradictions are
      raised by the *checks* that assert a defense is present: a contradiction
      means the claimed defense did not hold.
    * any other return value -> ALLOWED (the attack got through).
    """

    try:
        outcome = fn()
    except (PolicyBlocked, Unauthorized) as exc:
        return AttackResult(attack_id, attack, expected, type(exc).__name__, "REFUSED", str(exc))
    except Contradiction as exc:
        return AttackResult(
            attack_id,
            attack,
            expected,
            "NO_DEFENSE_PRESENT",
            "FAILED_OPEN",
            str(exc),
        )
    observed = str(getattr(outcome, "value", outcome))
    if observed in SAFE_CONTAINMENT_MARKERS:
        return AttackResult(attack_id, attack, expected, observed, "CONTAINED", f"{attack}: contained")
    return AttackResult(
        attack_id,
        attack,
        expected,
        f"ALLOWED:{outcome!r}",
        "ALLOWED",
        f"{attack} was not refused",
    )


def run_mf_b0_adversarial_suite() -> tuple[AttackResult, ...]:
    from .core import OceTestDouble  # local import keeps the module import graph shallow

    results: list[AttackResult] = []

    # 1. fixture attempts to become canonical authority
    results.append(
        _run(
            "MF-B0-A01",
            "Foundry fixture attempts to become canonical authority",
            "REFUSED",
            lambda: assert_not_canonical_authority(
                OceTestDouble(
                    fixture="LocalEvidenceRegistry",
                    canonical_oce_target="OCE EvidenceGraph",
                    replacement_condition="when convergence branch exposes canonical service",
                    retirement_evidence="evidence refs carry OCE envelope ids",
                    noncanonical=False,
                ),
                subject="LocalEvidenceRegistry",
            ),
        )
    )

    # 2. model score attempts direct capability promotion
    results.append(
        _run(
            "MF-B0-A02",
            "Model score attempts direct capability promotion",
            "REFUSED",
            lambda: assert_capability_promotion_requires_review(self_review=True, oce_review_ref=None),
        )
    )

    # 3. system-level result attempts artifact-level promotion
    results.append(
        _run(
            "MF-B0-A03",
            "System-level result attempts artifact-only capability promotion",
            "REFUSED",
            lambda: assert_subject_credit(SubjectKind.COGNITIVE_SYSTEM, SubjectKind.COGNITIVE_ARTIFACT),
        )
    )

    # 4. retrieval-only source transformed into synthetic training data
    results.append(
        _run(
            "MF-B0-A04",
            "Retrieval-only source transformed into synthetic training data",
            "CONTAINED",
            lambda: _assert_retrieval_only_derivation_quarantined(),
        )
    )

    # 5. unknown rights treated as permission
    results.append(
        _run(
            "MF-B0-A05",
            "Unknown rights treated as training permission",
            "REFUSED",
            lambda: assert_trainable(RightsState.RIGHTS_UNKNOWN),
        )
    )

    # 6. benchmark item leaks directly / paraphrased
    results.append(
        _run(
            "MF-B0-A06",
            "Benchmark item leakage (paraphrase) attempts a clean claim",
            "REFUSED",
            lambda: assert_no_claim_degrading_contamination(
                grade_contamination(
                    (
                        ("benchmark_item", ContaminationClass.C3_PARAPHRASE_OR_SOLUTION_OVERLAP),
                        ("unrelated", ContaminationClass.C0_NO_OBSERVED_OVERLAP),
                    )
                ),
                claim_label="sealed confirmation result",
            ),
        )
    )

    # 7. public dev benchmark relabeled sealed
    results.append(
        _run(
            "MF-B0-A07",
            "Widely exposed dev benchmark relabeled SEALED",
            "REFUSED",
            lambda: assert_tier_change_allowed(
                EvaluationTier.DEVELOPMENT,
                EvaluationTier.SEALED_CONFIRMATION,
                new_protected_task_set=False,
                actor_is_builder=True,
            ),
        )
    )

    # 8. pretrained model with unknown corpus claims independent CEREBUS discovery
    results.append(
        _run(
            "MF-B0-A08",
            "Pretrained model with unknown corpus claims CONTROLLED_INDEPENDENT_REDISCOVERY",
            "REFUSED",
            lambda: assert_claim_class(
                ClaimClass.CONTROLLED_INDEPENDENT_REDISCOVERY,
                upstream_provenance_known=False,
                doctrine_leak=False,
                doctrine_revealed=False,
            ),
        )
    )

    # 9. CEREBUS terminology removed but exact threshold leaked
    results.append(
        _run(
            "MF-B0-A09",
            "Doctrine-shaped leak without CEREBUS vocabulary",
            "CONTAINED",
            lambda: _assert_leak_detected(),
        )
    )

    # 10. high PnL attempts validation bypass
    results.append(
        _run(
            "MF-B0-A10",
            "High PnL attempts scientific validity bypass",
            "REFUSED",
            lambda: assert_no_pnl_validity_bypass(pnl=5_000.0, validity_ratio=None),
        )
    )

    # 11. capability gain attempts authority expansion
    results.append(
        _run(
            "MF-B0-A11",
            "Capability gain attempts authority expansion",
            "REFUSED",
            lambda: assert_capability_gain_does_not_expand_authority(
                capability_delta=0.4,
                grant_set_before=("READ_SOURCES",),
                grant_set_after=("READ_SOURCES", "LAUNCH_PAID_COMPUTE"),
            ),
        )
    )

    # 12. provider outage attempts to strand artifacts
    results.append(
        _run(
            "MF-B0-A12",
            "Provider outage strands artifacts (single-location checkpoint)",
            "REFUSED",
            lambda: CheckpointPlan(
                locations=("provider_volume",),
                integrity_hash="sha256:abc",
                resume_semantics="resume_from_checkpoint",
                max_recomputation_hours=2.0,
            ).validate(),
        )
    )

    # 13. rental host attempts durable credential use
    results.append(
        _run(
            "MF-B0-A13",
            "Rental host attempts durable credential use",
            "REFUSED",
            lambda: RemoteCredential(
                credential_id="rental-token",
                scope=("WORKER",),
                durable=True,
                can_grant_authority=True,
            ).assert_rental_boundary(),
        )
    )

    # 14. failed training runs omitted from recipe evidence
    results.append(
        _run(
            "MF-B0-A14",
            "Recipe reliability reported from six survivors of ten runs",
            "REFUSED",
            lambda: assert_failure_lineage(total_runs=10, successes=6, failures_recorded=0),
        )
    )

    # 15. operator preference attempts to change evaluator
    results.append(
        _run(
            "MF-B0-A15",
            "Operator preference attempts to change the frozen evaluator",
            "REFUSED",
            lambda: assert_operator_preference_does_not_alter_evaluator(
                preference="favourite architecture must score higher",
                protocol_fingerprint_before="sha256:aaa",
                protocol_fingerprint_after="sha256:bbb",
            ),
        )
    )

    # 16. teacher/student/judge shared lineage appears independent
    results.append(
        _run(
            "MF-B0-A16",
            "Shared teacher/evaluator lineage presented as independence",
            "CONTAINED",
            lambda: _assert_shared_lineage_not_independent(),
        )
    )

    # 17. underpowered experiment attempts PASS
    results.append(
        _run(
            "MF-B0-A17",
            "Underpowered experiment attempts PASS",
            "REFUSED",
            lambda: assert_conclusion_allowed(TerminalConclusion.PASS, power_adequate=False, sample_adequate=False),
        )
    )

    # 18. novel capability forced into nearest taxonomy class
    results.append(
        _run(
            "MF-B0-A18",
            "Novel capability forced into the nearest taxonomy class",
            "CONTAINED",
            lambda: _assert_novel_preserved(),
        )
    )

    # 19. one lifecycle state attempts to overwrite another
    results.append(
        _run(
            "MF-B0-A19",
            "Divergent lifecycle states coerced into one overall status",
            "REFUSED",
            lambda: LifecycleSnapshot(
                source_role="QUARANTINED",
                experiment_run="COMPLETED",
                cognitive_artifact="DOMAIN_VALIDATED",
                benchmark="DEGRADED",
                capability_evidence="REPRODUCED",
            ).collapse_to_single_status(),
        )
    )

    # 20. temporary OCE test double has no retirement path
    results.append(
        _run(
            "MF-B0-A20",
            "Temporary OCE test double without a retirement path",
            "CONTAINED",
            lambda: _assert_retirement_path_present(),
        )
    )

    return tuple(results)


def _assert_retrieval_only_derivation_quarantined() -> str:
    role = derived_role((SourceRole.RETRIEVAL_ONLY,))
    if role is not SourceRole.QUARANTINED:
        raise Contradiction(f"retrieval-only derivation produced {role.value}")
    return role.value


def _assert_leak_detected() -> str:
    """Doctrine-shape detection is structural: numbers + geometry, not vocabulary."""

    signature = DoctrineSignature(
        rule_ids=("CEREBUS-R12",),
        exact_numbers=("0.7425", "13.5"),
        structural_tokens=("session_open", "displacement_band"),
    )
    # CEREBUS vocabulary stripped, exact threshold plus structural geometry kept:
    # this must still be flagged as a doctrine-shape leak.
    if not doctrine_shape_leak(
        signature, ("market_research", "0.7425", "displacement_band")
    ):
        raise Contradiction("doctrine-shape leak was not detected")
    # Control: vocabulary and geometry without a leaked exact number is not decisive.
    if doctrine_shape_leak(signature, ("cerebus_rules", "session_open", "displacement_band")):
        raise Contradiction("vocabulary-only content was treated as a numeric leak")
    # Control: unrelated content must not be flagged.
    if doctrine_shape_leak(signature, ("unrelated", "1.0", "table")):
        raise Contradiction("false-positive leak detection")
    return "LEAK_DETECTED"


def _assert_shared_lineage_not_independent() -> str:
    verdict = effective_independence(
        shared_teacher=True,
        shared_evaluator=True,
        shared_training_data=True,
        architecture_distinct=True,
    )
    if verdict != "SHARED_LINEAGE":
        raise Contradiction(f"shared lineage was scored as {verdict}")
    if effective_independence(
        shared_teacher=False,
        shared_evaluator=False,
        shared_training_data=False,
        architecture_distinct=False,
    ) != "INDEPENDENT_UNVERIFIED":
        raise Contradiction("unverifiable independence was scored as verified")
    return verdict


def _assert_novel_preserved() -> str:
    verdict = classify_novel_behavior(fits_taxonomy=False, evidence_strength="UNKNOWN")
    if verdict != "UNRESOLVED_CAPABILITY_PATTERN":
        raise Contradiction("novel behavior was force-classified")
    return verdict


def _assert_retirement_path_present() -> str:
    missing = undeclared_generic_services()
    if missing:
        raise PolicyBlocked(
            "OCE_DOUBLE_WITHOUT_RETIREMENT_PATH",
            f"generic services without retirement evidence: {', '.join(missing)}",
        )
    return "ALL_FIXTURES_DECLARED_AND_REPLACEABLE"


def mf_b0_gate_report() -> dict[str, Any]:
    """Full MF-B0 report: constitutional artifacts + adversarial suite result."""

    attacks = run_mf_b0_adversarial_suite()
    failed = tuple(a for a in attacks if not a.held)
    report = {
        "block": "MF-B0",
        "constitution_fingerprint": CONSTITUTION.fingerprint,
        "lifecycle_machines": {k: list(v) for k, v in LIFECYCLE_MACHINES.items()},
        "attacks_total": len(attacks),
        "attacks_refused": sum(1 for a in attacks if a.verdict == "REFUSED"),
        "attacks_contained": sum(1 for a in attacks if a.verdict == "CONTAINED"),
        "attacks_held": len(attacks) - len(failed),
        "attacks_failed_open": len(failed),
        "attacks": [a.to_dict() for a in attacks],
        "verdict": "PASS" if not failed else "FAIL",
    }
    report["report_fingerprint"] = fingerprint(report)
    return report


__all__ = [
    "AttackResult",
    "CheckpointPlan",
    "DoctrineSignature",
    "RemoteCredential",
    "assert_capability_gain_does_not_expand_authority",
    "assert_capability_promotion_requires_review",
    "assert_claim_class",
    "assert_conclusion_allowed",
    "assert_failure_lineage",
    "assert_no_claim_degrading_contamination",
    "assert_no_pnl_validity_bypass",
    "assert_not_canonical_authority",
    "assert_operator_preference_does_not_alter_evaluator",
    "assert_subject_credit",
    "assert_tier_change_allowed",
    "assert_trainable",
    "assert_within_authority_ceiling",
    "classify_novel_behavior",
    "derived_role",
    "doctrine_shape_leak",
    "effective_independence",
    "grade_contamination",
    "max_claim_class",
    "mf_b0_gate_report",
    "rights_permit_training",
    "run_mf_b0_adversarial_suite",
]
