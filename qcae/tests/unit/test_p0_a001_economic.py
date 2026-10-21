"""P0-A001-03 — Economic Experience + cross-registry reference evidence (A-001 §6, §10, §11)."""

from __future__ import annotations

import pytest

from qcae.core.amendments.a001.economic_experience import (
    CustomerAcceptance,
    EconomicExperienceRecord,
    EconomicOutcome,
    EconomicsBlock,
    PromotionState,
    QaResult,
    make_economic_experience,
)
from qcae.core.amendments.a001.external_registry import (
    ExternalLifecycleRole,
    ExternalRegistry,
    ExternalRegistryRef,
    make_external_registry_ref,
)
from qcae.core.amendments.a001.shared import DataRights
from qcae.core.errors import QcaeValidationError


def economics(**overrides) -> EconomicsBlock:
    fields = {
        "gross_payout": 250.0,
        "direct_cost": 40.0,
        "compute_cost": 12.5,
        "tool_cost": 3.0,
        "currency": "USD",
        "estimated_human_cost": 30.0,
        "net_contribution": 164.5,
    }
    fields.update(overrides)
    return EconomicsBlock(**fields)


def experience(**overrides) -> EconomicExperienceRecord:
    fields = {
        "experience_id": "eer-0001",
        "source": "external-marketplace:job-8841",
        "opportunity_id": "opp-0007",
        "objective_type": "data-pipeline-delivery",
        "economics": economics(),
        "human_intervention_minutes": 25.0,
        "execution_time_seconds": 5400.0,
        "capabilities_used": ("CAP-ATOM-INGEST",),
        "research_used": ("rh-0001",),
        "knowledge_gaps_found": ("unclear vendor API rate limits",),
        "capability_gaps_found": (),
        "errors_encountered": ("transient timeout on retry 2",),
        "client_revisions": 1,
        "qa_result": QaResult.PASS_WITH_CAVEATS,
        "customer_acceptance": CustomerAcceptance.ACCEPTED,
        "outcome": EconomicOutcome.DELIVERED_PAID,
        "reusability_score": 0.6,
        "transferability_score": 0.5,
        "lesson_candidates": ("retry policy for vendor APIs",),
        "data_rights": DataRights.INTERNAL,
        "contains_client_specific_material": False,
        "promotion_state": PromotionState.RAW,
        "recorded_at": "2026-09-12T18:00:00Z",
    }
    fields.update(overrides)
    return EconomicExperienceRecord(**fields)


class TestEconomicExperienceRecord:
    def test_valid_record(self) -> None:
        experience().validate()

    def test_round_trip(self) -> None:
        record = experience()
        rebuilt = EconomicExperienceRecord.from_dict(record.to_dict())
        assert rebuilt == record
        assert rebuilt.economics == economics()
        assert rebuilt.promotion_state is PromotionState.RAW
        assert rebuilt.data_rights is DataRights.INTERNAL

    def test_missing_economics_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="economics"):
            experience(economics=None).validate()

    def test_negative_costs_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="compute_cost"):
            experience(economics=economics(compute_cost=-1.0)).validate()

    def test_score_bounds_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="reusability_score"):
            experience(reusability_score=1.2).validate()

    def test_bad_promotion_state_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="PromotionState"):
            experience(promotion_state="INSTANT_DOCTRINE").validate()

    def test_bad_data_rights_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="DataRights"):
            experience(data_rights="SECRET").validate()

    def test_malformed_provenance_style_fields_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="experience_id"):
            experience(experience_id="not a valid id!").validate()

    def test_recorded_at_required(self) -> None:
        with pytest.raises(QcaeValidationError, match="recorded_at"):
            experience(recorded_at="").validate()


class TestPromotionFirewall:
    def test_client_material_cannot_directly_promote(self) -> None:
        with pytest.raises(QcaeValidationError, match="client-specific"):
            experience(
                contains_client_specific_material=True,
                data_rights=DataRights.CLIENT_CONFIDENTIAL,
                promotion_state=PromotionState.PROMOTED,
                promotion_refs=("institutional-review-0001",),
            ).validate()

    def test_client_material_needs_rights_filtering_first(self) -> None:
        with pytest.raises(QcaeValidationError, match="RIGHTS_FILTERED"):
            experience(
                contains_client_specific_material=True,
                data_rights=DataRights.RESTRICTED,
                promotion_state=PromotionState.ABSTRACTED,
            ).validate()

    def test_client_material_rights_filtered_is_legal(self) -> None:
        experience(
            contains_client_specific_material=True,
            data_rights=DataRights.CLIENT_CONFIDENTIAL,
            promotion_state=PromotionState.RIGHTS_FILTERED,
        ).validate()

    def test_promoted_requires_governed_citation(self) -> None:
        with pytest.raises(QcaeValidationError, match="promotion_refs"):
            experience(promotion_state=PromotionState.PROMOTED).validate()

    def test_promoted_with_citation_is_legal(self) -> None:
        experience(
            promotion_state=PromotionState.PROMOTED,
            promotion_refs=("institutional-review-0042",),
        ).validate()

    def test_customer_acceptance_does_not_imply_promotion(self) -> None:
        """A-001 invariant 6: paid acceptance is not proof of institutional truth."""
        record = experience(
            customer_acceptance=CustomerAcceptance.ACCEPTED,
            outcome=EconomicOutcome.DELIVERED_PAID,
            qa_result=QaResult.PASS,
            promotion_state=PromotionState.RAW,
        )
        record.validate()
        assert record.promotion_state is PromotionState.RAW
        assert record.customer_acceptance is CustomerAcceptance.ACCEPTED
        assert record.outcome is EconomicOutcome.DELIVERED_PAID

    def test_data_rights_state_remains_explicit(self) -> None:
        record = experience()
        payload = record.to_dict()
        assert payload["data_rights"] == "INTERNAL"
        assert payload["contains_client_specific_material"] is False

    def test_record_is_not_self_modification_instruction(self) -> None:
        """A-001 §10: the record type carries lesson candidates as evidence;
        it has no instruction/authority field to mutate the institution."""
        payload = experience().to_dict()
        forbidden = {"instruction", "self_modification", "doctrine", "authority_grant"}
        assert not (set(payload) & forbidden)
        assert isinstance(payload["lesson_candidates"], list)


class TestExternalRegistryRef:
    def test_research_mesh_reference(self) -> None:
        make_external_registry_ref(
            registry=ExternalRegistry.RESEARCH_MESH,
            external_id="rmev-0009",
            owner_domain="research-mesh:synthesis",
            external_digest="a" * 64,
            referenced_at="2026-09-12T19:00:00Z",
        )

    def test_economic_experience_reference(self) -> None:
        make_external_registry_ref(
            registry=ExternalRegistry.ECONOMIC_EXPERIENCE,
            external_id="eer-0001",
            owner_domain="oce:opportunity-exchange",
        )

    def test_institutional_learning_reference(self) -> None:
        make_external_registry_ref(
            registry=ExternalRegistry.INSTITUTIONAL_LEARNING,
            external_id="ilc-0031",
            owner_domain="institution:transformation-governor",
        )

    def test_owner_and_registry_identity_preserved_on_round_trip(self) -> None:
        ref = make_external_registry_ref(
            registry=ExternalRegistry.RESEARCH_MESH,
            external_id="rmev-777",
            owner_domain="research-mesh:contradiction-registry",
            lifecycle_role=ExternalLifecycleRole.SUBMIT,
        )
        rebuilt = ExternalRegistryRef.from_dict(ref.to_dict())
        assert rebuilt == ref
        assert rebuilt.registry is ExternalRegistry.RESEARCH_MESH
        assert rebuilt.owner_domain == "research-mesh:contradiction-registry"
        assert rebuilt.lifecycle_role is ExternalLifecycleRole.SUBMIT

    def test_no_govern_role_exists(self) -> None:
        """Ownership and lifecycle authority never merge (A-001 §6)."""
        assert not hasattr(ExternalLifecycleRole, "GOVERN")
        assert {r.value for r in ExternalLifecycleRole} == {"OBSERVE", "SUBMIT"}

    def test_bad_registry_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="ExternalRegistry"):
            ExternalRegistryRef(
                registry="SOMEONE_ELSES_REGISTRY",
                external_id="x-1",
                owner_domain="elsewhere",
            ).validate()

    def test_missing_owner_domain_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="owner_domain"):
            ExternalRegistryRef(
                registry=ExternalRegistry.RESEARCH_MESH,
                external_id="rmev-1",
                owner_domain="",
            ).validate()

    def test_bad_digest_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="external_digest"):
            ExternalRegistryRef(
                registry=ExternalRegistry.RESEARCH_MESH,
                external_id="rmev-1",
                owner_domain="research-mesh",
                external_digest="short",
            ).validate()
