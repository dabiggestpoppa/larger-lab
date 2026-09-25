"""MF-B0 — constitution, boundary, and the 20-attack adversarial gate."""

from __future__ import annotations

import pytest

from foundry.boundary import (
    CheckpointPlan,
    RemoteCredential,
    assert_capability_gain_does_not_expand_authority,
    assert_capability_promotion_requires_review,
    assert_claim_class,
    assert_conclusion_allowed,
    assert_failure_lineage,
    assert_no_claim_degrading_contamination,
    assert_no_pnl_validity_bypass,
    assert_not_canonical_authority,
    assert_operator_preference_does_not_alter_evaluator,
    assert_subject_credit,
    assert_tier_change_allowed,
    assert_trainable,
    assert_within_authority_ceiling,
    derived_role,
    doctrine_shape_leak,
    effective_independence,
    grade_contamination,
    mf_b0_gate_report,
    run_mf_b0_adversarial_suite,
)
from foundry.constitution import (
    CONSTITUTION,
    EVALUATION_TIER_CONTRACT,
    FOUNDRY_DOCTRINE,
    LifecycleSnapshot,
    ReproducibilityClaim,
    ResourceBudget,
    ownership_conflicts,
    self_promotion_blocked,
    undeclared_generic_services,
)
from foundry.core import PolicyBlocked, Unauthorized
from foundry.enums import (
    ClaimClass,
    ContaminationClass,
    EvaluationTier,
    ReproducibilityClass,
    RightsState,
    SourceRole,
    SubjectKind,
    TerminalConclusion,
    TrustClass,
)


def test_constitution_fingerprint_is_stable_and_complete() -> None:
    first = CONSTITUTION.fingerprint
    second = CONSTITUTION.fingerprint
    assert first == second
    assert first.startswith("sha256:")
    assert CONSTITUTION.mission_contract.mission
    assert len(CONSTITUTION.ownership_matrix) >= 10


def test_doctrine_states_the_governing_inequalities() -> None:
    required = {
        "MODEL OUTPUT != INSTITUTIONAL TRUTH",
        "CAPABILITY != AUTHORITY",
        "ACCESS != RIGHTS",
        "AVAILABLE DATA != TRAINABLE DATA",
        "BENCHMARK SCORE != CAPABILITY",
        "PROVIDER OFFER != GUARANTEE",
        "HOURLY PRICE != COST-TO-CLOSE",
        "REGISTERED SOURCE != CLEAN SOURCE",
        "HIDDEN EVAL != DEVELOPMENT DATA",
        "NEGATIVE RESULT != FAILED PROJECT",
        "UNKNOWN != FAVORABLE",
    }
    assert required.issubset(set(FOUNDRY_DOCTRINE))


def test_no_ownership_conflicts_and_every_generic_service_has_a_retirement_path() -> None:
    assert ownership_conflicts() == ()
    assert undeclared_generic_services() == ()


def test_lifecycle_machines_stay_separate() -> None:
    snapshot = LifecycleSnapshot(
        source_role="QUARANTINED",
        experiment_run="COMPLETED",
        cognitive_artifact="DOMAIN_VALIDATED",
        benchmark="DEGRADED",
        capability_evidence="REPRODUCED",
    )
    snapshot.validate()
    assert snapshot.to_dict()["source_role"] == "QUARANTINED"
    with pytest.raises(PolicyBlocked) as exc:
        snapshot.collapse_to_single_status()
    assert exc.value.code == "LIFECYCLE_COLLAPSE_REFUSED"


def test_lifecycle_rejects_states_from_another_machine() -> None:
    with pytest.raises(PolicyBlocked) as exc:
        LifecycleSnapshot(
            source_role="COMPLETED",
            experiment_run="COMPLETED",
            cognitive_artifact="REGISTERED",
            benchmark="DRAFT",
            capability_evidence="MEASURED",
        ).validate()
    assert exc.value.code == "LIFECYCLE_STATE_INVALID"


@pytest.mark.parametrize(
    "action",
    [
        "deploy_production_oce_runtime",
        "change_oce_constitution",
        "place_trade",
        "connect_live_broker_or_exchange",
        "approve_own_evaluator_change",
        "certify_own_consequence_bearing_runtime",
        "launch_paid_compute_without_operator_authorization",
        "write_global_capability_status",
        "amend_doctrine",
    ],
)
def test_authority_ceiling_is_enforced(action: str) -> None:
    with pytest.raises(Unauthorized) as exc:
        assert_within_authority_ceiling(action)
    assert exc.value.code == "AUTHORITY_CEILING_EXCEEDED"


def test_authority_ceiling_allows_ordinary_work() -> None:
    assert_within_authority_ceiling("register_source")
    assert_within_authority_ceiling("build_dataset")


def test_child_program_cannot_promote_itself() -> None:
    assert self_promotion_blocked("scratch-model laboratory", "OCE review") is True
    assert self_promotion_blocked("scratch-model laboratory", "Foundry -> OCE evidence review") is False


def test_evaluation_tier_contract_separates_builder_visibility() -> None:
    contract = {rule.tier: rule for rule in EVALUATION_TIER_CONTRACT}
    assert contract[EvaluationTier.DEVELOPMENT].visible_to_builder.startswith("tasks and answers")
    assert contract[EvaluationTier.PROMOTION].may_influence_training is False
    assert contract[EvaluationTier.SEALED_CONFIRMATION].answer_key_access == "isolated"


def test_tier_upgrade_requires_new_protected_set_and_cannot_be_self_served() -> None:
    with pytest.raises(Unauthorized) as exc:
        assert_tier_change_allowed(
            EvaluationTier.DEVELOPMENT,
            EvaluationTier.PROMOTION,
            new_protected_task_set=True,
            actor_is_builder=True,
        )
    assert exc.value.code == "TIER_SELF_UPGRADE_REFUSED"
    with pytest.raises(PolicyBlocked):
        assert_tier_change_allowed(
            EvaluationTier.DEVELOPMENT,
            EvaluationTier.PROMOTION,
            new_protected_task_set=False,
            actor_is_builder=False,
        )
    assert_tier_change_allowed(
        EvaluationTier.DEVELOPMENT,
        EvaluationTier.PROMOTION,
        new_protected_task_set=True,
        actor_is_builder=False,
    ) is None


def test_claim_class_laundering_is_refused() -> None:
    with pytest.raises(PolicyBlocked) as exc:
        assert_claim_class(
            ClaimClass.CONTROLLED_INDEPENDENT_REDISCOVERY,
            upstream_provenance_known=False,
            doctrine_leak=False,
            doctrine_revealed=False,
        )
    assert exc.value.code == "CLAIM_CLASS_LAUNDERING_REFUSED"
    assert_claim_class(
        ClaimClass.POST_REVEAL_REPRODUCTION,
        upstream_provenance_known=False,
        doctrine_leak=False,
        doctrine_revealed=True,
    ) is None


def test_doctrine_shape_leak_detects_numbers_plus_geometry_not_vocabulary() -> None:
    from foundry.boundary import DoctrineSignature

    signature = DoctrineSignature(
        rule_ids=("CEREBUS-R12",),
        exact_numbers=("0.7425",),
        structural_tokens=("displacement_band",),
    )
    assert doctrine_shape_leak(signature, ("plain_words", "0.7425", "displacement_band")) is True
    assert doctrine_shape_leak(signature, ("cerebus_stuff", "displacement_band")) is False
    assert doctrine_shape_leak(signature, ("plain_words", "1.0", "other")) is False


def test_rights_and_contamination_guards() -> None:
    with pytest.raises(PolicyBlocked) as exc:
        assert_trainable(RightsState.RIGHTS_UNKNOWN)
    assert exc.value.code == "RIGHTS_BLOCKED"
    assert_trainable(RightsState.RIGHTS_VERIFIED_BY_POLICY) is None

    grade = grade_contamination(
        (("benchmark", ContaminationClass.C3_PARAPHRASE_OR_SOLUTION_OVERLAP),)
    )
    with pytest.raises(PolicyBlocked) as exc2:
        assert_no_claim_degrading_contamination(grade, claim_label="sealed claim")
    assert exc2.value.code == "CONTAMINATION_BLOCKED"


def test_derived_role_inherits_ancestor_restrictions() -> None:
    assert derived_role((SourceRole.RETRIEVAL_ONLY,)) is SourceRole.QUARANTINED
    assert derived_role((SourceRole.HIDDEN_EVAL,)) is SourceRole.QUARANTINED
    assert derived_role((SourceRole.TRAIN_CPT,)) is SourceRole.TRAIN_CPT


def test_subject_credit_requires_attribution_study() -> None:
    with pytest.raises(PolicyBlocked) as exc:
        assert_subject_credit(SubjectKind.COGNITIVE_SYSTEM, SubjectKind.COGNITIVE_ARTIFACT)
    assert exc.value.code == "SUBJECT_CREDIT_COLLAPSE_REFUSED"
    assert_subject_credit(
        SubjectKind.COGNITIVE_SYSTEM,
        SubjectKind.COGNITIVE_ARTIFACT,
        attribution_study="study://attribution/002",
    ) is None


def test_capability_promotion_and_authority_confusion_guards() -> None:
    with pytest.raises(Unauthorized):
        assert_capability_promotion_requires_review(self_review=True, oce_review_ref=None)
    with pytest.raises(Unauthorized):
        assert_capability_gain_does_not_expand_authority(
            capability_delta=0.5, grant_set_before=("A",), grant_set_after=("A", "B")
        )
    assert_capability_gain_does_not_expand_authority(
        capability_delta=0.5, grant_set_before=("A",), grant_set_after=("A",)
    ) is None


def test_fixture_cannot_declare_itself_canonical() -> None:
    from foundry.core import OceTestDouble

    # The declaration object itself refuses to be born canonical ...
    with pytest.raises(PolicyBlocked) as exc:
        OceTestDouble(
            fixture="LocalAuthority",
            canonical_oce_target="OCE AuthorityState",
            replacement_condition="always",
            retirement_evidence="never",
            noncanonical=False,
        )
    assert exc.value.code == "NONCANONICAL_FLAG_REQUIRED"

    # ... and a generic-looking local service with no declaration at all is refused too.
    with pytest.raises(PolicyBlocked) as exc2:
        assert_not_canonical_authority(None, subject="LocalAuthority")
    assert exc2.value.code == "NONCANONICAL_DECLARATION_REQUIRED"

    declared = OceTestDouble(
        fixture="LocalEvidenceRegistry",
        canonical_oce_target="OCE EvidenceGraph",
        replacement_condition="when the convergence branch exposes the canonical service",
        retirement_evidence="evidence refs carry OCE envelope ids",
    )
    assert_not_canonical_authority(declared, subject="LocalEvidenceRegistry") is None

    # An incomplete declaration (no retirement path) cannot be constructed at all.
    with pytest.raises(PolicyBlocked) as exc3:
        OceTestDouble(
            fixture="LocalAuthority",
            canonical_oce_target="OCE AuthorityState",
            replacement_condition="",
            retirement_evidence="",
        )
    assert exc3.value.code == "NONCANONICAL_DECLARATION_INCOMPLETE"


def test_checkpoint_plan_and_rental_credential_boundaries() -> None:
    with pytest.raises(PolicyBlocked):
        CheckpointPlan(
            locations=("only-one",),
            integrity_hash="sha256:x",
            resume_semantics="resume",
            max_recomputation_hours=1.0,
        ).validate()
    with pytest.raises(Unauthorized):
        RemoteCredential(
            credential_id="rental",
            scope=("WORKER",),
            durable=True,
            can_grant_authority=False,
        ).assert_rental_boundary()


def test_reliability_cannot_be_reported_from_survivors_only() -> None:
    with pytest.raises(PolicyBlocked) as exc:
        assert_failure_lineage(total_runs=10, successes=6, failures_recorded=0)
    assert exc.value.code == "FAILURE_LINEAGE_INCOMPLETE"
    assert_failure_lineage(total_runs=10, successes=6, failures_recorded=4) is None


def test_frozen_map_survives_copying_and_serialization() -> None:
    """Immutability must not make a record unusable.

    The mappingproxy backing store cannot be deep-copied or pickled, which broke
    ``copy.deepcopy``, ``pickle``, and ``dataclasses.asdict`` on every record that
    contained a FrozenMap (dataset manifests, receipts, capability vectors).
    """

    import copy
    import dataclasses
    import json
    import pickle

    from foundry.core import FrozenMap

    frozen = FrozenMap({"dimensions": {"accuracy": 0.71}, "sources": ["SRC_A", "SRC_B"]})
    assert copy.deepcopy(frozen).to_dict() == frozen.to_dict()
    assert pickle.loads(pickle.dumps(frozen)).to_dict() == frozen.to_dict()
    assert copy.copy(frozen) is frozen

    @dataclasses.dataclass(frozen=True)
    class Record:
        payload: FrozenMap

    record = Record(payload=frozen)
    # this used to raise TypeError: cannot pickle 'mappingproxy' object
    payload = dataclasses.asdict(record)["payload"]
    assert payload.to_dict() == frozen.to_dict()
    assert json.loads(json.dumps(frozen.to_dict()))["dimensions"]["accuracy"] == 0.71


def test_operator_preference_cannot_alter_the_frozen_evaluator() -> None:
    with pytest.raises(Unauthorized) as exc:
        assert_operator_preference_does_not_alter_evaluator(
            preference="prefer this architecture",
            protocol_fingerprint_before="sha256:a",
            protocol_fingerprint_after="sha256:b",
        )
    assert exc.value.code == "OPERATOR_PREFERENCE_ALTERED_EVALUATOR"


def test_shared_lineage_is_not_independence() -> None:
    assert (
        effective_independence(
            shared_teacher=True,
            shared_evaluator=False,
            shared_training_data=False,
            architecture_distinct=True,
        )
        == "SHARED_LINEAGE"
    )
    assert (
        effective_independence(
            shared_teacher=False,
            shared_evaluator=False,
            shared_training_data=False,
            architecture_distinct=False,
        )
        == "INDEPENDENT_UNVERIFIED"
    )


def test_underpowered_evidence_cannot_conclude_pass_or_fail() -> None:
    with pytest.raises(PolicyBlocked) as exc:
        assert_conclusion_allowed(
            TerminalConclusion.PASS, power_adequate=False, sample_adequate=False
        )
    assert exc.value.code == "UNDERPOWERED_PASS_REFUSED"
    assert_conclusion_allowed(
        TerminalConclusion.UNDERPOWERED, power_adequate=False, sample_adequate=False
    ) is None


def test_pnl_cannot_substitute_for_validity() -> None:
    with pytest.raises(PolicyBlocked) as exc:
        assert_no_pnl_validity_bypass(pnl=1000.0, validity_ratio=None)
    assert exc.value.code == "PNL_VALIDITY_BYPASS_REFUSED"


def test_reproducibility_overclaim_is_refused() -> None:
    claim = ReproducibilityClaim(
        claimed=ReproducibilityClass.R3_EXTERNAL_DOMAIN_REPLICATION,
        environment_recorded=True,
        independent_implementation=False,
        external_replication=False,
        framework="fixture",
        dependency_lock_digest="sha256:lock",
        accelerator_identity="fixture-gpu",
        driver_stack="fixture-driver",
    )
    with pytest.raises(PolicyBlocked) as exc:
        claim.validate()
    assert exc.value.code == "REPRODUCIBILITY_OVERCLAIM"


def test_budget_envelope_blocks_instead_of_spending() -> None:
    budget = ResourceBudget(name="fixture", dollars_per_week=10.0, accelerator_hours=2.0)
    budget.check(dollars=5.0, accelerator_hours=1.0)
    with pytest.raises(PolicyBlocked) as exc:
        budget.check(dollars=25.0, accelerator_hours=1.0)
    assert exc.value.code == "BUDGET_BLOCKED"


def test_supply_chain_trust_class_blocks_runtime_entry() -> None:
    from foundry.constitution import TrustClassification

    with pytest.raises(PolicyBlocked) as exc:
        TrustClassification(
            subject="remote-code-model",
            trust_class=TrustClass.PUBLIC_RESEARCH,
            requires_remote_code=True,
            unsafe_serialization=False,
            pinned_digest=None,
            human_version=None,
        ).admit_to_trusted_runtime()
    assert exc.value.code == "SUPPLY_CHAIN_UNSAFE_RUNTIME_ENTRY"


def test_dependency_pin_detects_same_version_different_bytes() -> None:
    from foundry.constitution import DependencyPin

    with pytest.raises(PolicyBlocked) as exc:
        DependencyPin(
            name="fixture-lib",
            human_version="1.2.3",
            pinned_digest="sha256:aaa",
            observed_digest="sha256:bbb",
        ).verify()
    assert exc.value.code == "PROVENANCE_MISMATCH"


def test_adversarial_suite_has_twenty_attacks_all_held() -> None:
    attacks = run_mf_b0_adversarial_suite()
    assert len(attacks) == 20
    assert all(a.held for a in attacks), [a.to_dict() for a in attacks if not a.held]
    assert {a.verdict for a in attacks} <= {"REFUSED", "CONTAINED"}
    assert sum(1 for a in attacks if a.verdict == "REFUSED") >= 15


def test_gate_report_verdict_and_accounting() -> None:
    report = mf_b0_gate_report()
    assert report["verdict"] == "PASS"
    assert report["attacks_total"] == 20
    assert report["attacks_failed_open"] == 0
    assert report["attacks_refused"] + report["attacks_contained"] == 20
    assert report["report_fingerprint"].startswith("sha256:")
    assert report["lifecycle_machines"]["oce_authority"] == ["NONE"]


def test_secret_bearing_source_cannot_hold_a_training_role() -> None:
    from foundry.data import DATA_DOUBLE, RightsDisposition, SourceRecord, SourceRegistry
    from foundry.enums import TrustClass
    from foundry.fixtures import load_rights_evidence

    register = load_rights_evidence()
    registry = SourceRegistry(rights_evidence=register)
    record = SourceRecord(
        source_id="SRC",
        title="t",
        locator="fixture://x",
        source_family="f",
        payload_class="text",
        observed_utc="2026-01-01T00:00:00Z",
        event_time_start=None,
        event_time_end=None,
        known_at_utc=None,
        upstream_ancestry="a",
        upstream_provenance_known=True,
        integrity_digest="sha256:x",
        record_count=1,
        trust_class=TrustClass.PRIVATE_OPERATOR,
        rights=RightsDisposition(
            subject="SRC",
            basis_ref="ownership://op",
            basis_scope="op",
            decided_utc="2026-01-01T00:00:00Z",
        ),
        role=SourceRole.TRAIN_CPT,
        secret_bearing=True,
    )
    with pytest.raises(PolicyBlocked) as exc:
        registry.register(record, actor="builder", reason="secret into training")
    assert exc.value.code == "SECRET_BEARING_SOURCE_TRAIN_ROLE_REFUSED"
    assert DATA_DOUBLE.noncanonical is True
