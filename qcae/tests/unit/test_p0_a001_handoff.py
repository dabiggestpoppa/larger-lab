"""P0-A001-02 — ResearchCapabilityHandoff contract evidence (A-001 §4–§5)."""

from __future__ import annotations

import pytest

from qcae.core.amendments.a001.gaps import GapType
from qcae.core.amendments.a001.handoff import (
    FallbackClass,
    HandoffConstraints,
    HandoffDirection,
    HandoffMode,
    HandoffProvenance,
    HandoffResult,
    HandoffStatus,
    RequiredOutput,
    ResearchCapabilityHandoff,
    make_handoff,
)
from qcae.core.amendments.a001.shared import DataRights
from qcae.core.errors import QcaeValidationError


def provenance(**overrides) -> HandoffProvenance:
    fields = {
        "created_at": "2026-09-12T12:00:00Z",
        "producer": "qcae:orchestrator",
        "source_refs": ("github-search:orderbook-replay",),
        "parent_event_ids": ("evt-0001",),
    }
    fields.update(overrides)
    return HandoffProvenance(**fields)


def request_handoff(**overrides) -> ResearchCapabilityHandoff:
    fields = {
        "request_id": "rh-0001",
        "direction": HandoffDirection.QCAE_TO_RESEARCH_MESH,
        "mode": HandoffMode.QCAE_CAPABILITY_RESEARCH,
        "gap_type": GapType.KNOWLEDGE_GAP,
        "status": HandoffStatus.REQUESTED,
        "origin_objective_id": "obj-0001",
        "capability_gap_id": "gap-k-0001",
        "research_question": (
            "Which published L2 replay algorithms guarantee deterministic "
            "checkpoint state under out-of-order event arrival?"
        ),
        "capability_context": {
            "capability_id": "CAP-REPLAY-001",
            "contract_version": 1,
        },
        "constraints": HandoffConstraints(
            deadline="2026-09-19T00:00:00Z",
            max_compute_cost_usd=5.0,
            max_tool_cost_usd=10.0,
            max_human_minutes=60,
            source_allowlist=("arxiv", "acm-dl"),
            source_denylist=("unverified-blogs",),
            data_rights=DataRights.PUBLIC,
        ),
        "required_outputs": (
            RequiredOutput.EVIDENCE_PACKAGE,
            RequiredOutput.SPECIFICATION_INPUT,
            RequiredOutput.UNCERTAINTY,
        ),
        "provenance": provenance(),
    }
    fields.update(overrides)
    return ResearchCapabilityHandoff(**fields)


def response_handoff(**overrides) -> ResearchCapabilityHandoff:
    fields = {
        "request_id": "rh-0001",
        "direction": HandoffDirection.RESEARCH_MESH_TO_QCAE,
        "mode": HandoffMode.QCAE_CAPABILITY_RESEARCH,
        "gap_type": GapType.KNOWLEDGE_GAP,
        "status": HandoffStatus.COMPLETED,
        "capability_gap_id": "gap-k-0001",
        "required_outputs": (
            RequiredOutput.EVIDENCE_PACKAGE,
            RequiredOutput.SPECIFICATION_INPUT,
            RequiredOutput.UNCERTAINTY,
        ),
        "result": HandoffResult(
            finding="Two candidate algorithms exist; neither documents ordering guarantees.",
            confidence=0.72,
            uncertainty="Neither paper evaluates adversarial event reordering.",
            assumptions=("Papers describe current released versions",),
            contradictions=(),
            testable_claims=(
                "Algorithm A reproduces reference fixture snapshots",
                "Algorithm B's checkpoint output is order-insensitive",
            ),
            specification_inputs=(
                {"source": "arxiv:2401.00001", "contract_input": "deterministic-checkpoint-spec"},
            ),
            recommended_next_action="Route both candidates to QCAE proving lab",
        ),
        "provenance": provenance(producer="research-mesh:synthesis"),
    }
    fields.update(overrides)
    return ResearchCapabilityHandoff(**fields)


class TestRequestContract:
    def test_valid_request(self) -> None:
        make_handoff(**request_handoff().__dict__)

    def test_request_round_trip(self) -> None:
        handoff = request_handoff()
        rebuilt = ResearchCapabilityHandoff.from_dict(handoff.to_dict())
        assert rebuilt == handoff
        assert rebuilt.constraints.data_rights is DataRights.PUBLIC
        assert isinstance(rebuilt.provenance, HandoffProvenance)

    def test_missing_research_question_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="research_question"):
            request_handoff(research_question="").validate()

    def test_request_cannot_carry_result(self) -> None:
        with pytest.raises(QcaeValidationError, match="cannot carry a result"):
            request_handoff(result=HandoffResult(finding="premature")).validate()

    def test_request_may_declare_local_fallback_in_progress(self) -> None:
        """A-001 §5: QCAE marks its own bounded fallback research on the
        request-direction handoff; the result attaches when complete."""
        handoff = request_handoff(fallback_class=FallbackClass.LOCAL_FALLBACK_RESEARCH)
        handoff.validate()
        assert handoff.fallback_class is FallbackClass.LOCAL_FALLBACK_RESEARCH

    def test_request_result_still_requires_fallback_marking(self) -> None:
        with pytest.raises(QcaeValidationError, match="cannot carry a result"):
            request_handoff(
                status=HandoffStatus.COMPLETED,
                result=HandoffResult(finding="x"),
            ).validate()

    def test_provenance_required(self) -> None:
        with pytest.raises(QcaeValidationError, match="provenance"):
            request_handoff(provenance=None).validate()

    def test_bad_request_id_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="request_id"):
            request_handoff(request_id="has spaces!").validate()

    def test_conflicting_source_policy_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="allowed and denied"):
            request_handoff(
                constraints=HandoffConstraints(
                    source_allowlist=("arxiv",),
                    source_denylist=("arxiv",),
                )
            ).validate()

    def test_negative_budget_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="max_compute_cost_usd"):
            request_handoff(
                constraints=HandoffConstraints(max_compute_cost_usd=-1.0)
            ).validate()

    def test_duplicate_required_outputs_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="duplicate"):
            request_handoff(
                required_outputs=(RequiredOutput.SYNTHESIS, RequiredOutput.SYNTHESIS)
            ).validate()

    def test_bad_required_output_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="RequiredOutput"):
            request_handoff(required_outputs=("DOCTRINE_PROMOTION",)).validate()

    def test_bad_data_rights_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="DataRights"):
            request_handoff(constraints=HandoffConstraints(data_rights="PUBLIC")).validate()


class TestResponseContract:
    def test_valid_response(self) -> None:
        response_handoff().validate()

    def test_response_round_trip(self) -> None:
        handoff = response_handoff()
        rebuilt = ResearchCapabilityHandoff.from_dict(handoff.to_dict())
        assert rebuilt == handoff
        assert rebuilt.result.confidence == 0.72
        assert rebuilt.result.specification_inputs[0]["source"] == "arxiv:2401.00001"

    def test_unresolved_contradiction_remains_explicit(self) -> None:
        """A-001 §4: contradictions are preserved, never silently resolved."""
        handoff = response_handoff(
            status=HandoffStatus.PARTIAL,
            result=HandoffResult(
                finding="Sources disagree on ordering semantics.",
                confidence=0.4,
                uncertainty="Contradiction unresolved between two primary sources.",
                contradictions=(
                    "Paper A claims deterministic reordering; Paper B demonstrates a counterexample.",
                ),
            ),
        )
        handoff.validate()
        assert handoff.result.contradictions
        assert handoff.result.uncertainty

    def test_completed_without_result_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="requires a result"):
            response_handoff(result=None).validate()

    def test_result_requires_response_direction(self) -> None:
        with pytest.raises(QcaeValidationError, match="cannot carry a result"):
            request_handoff(
                status=HandoffStatus.COMPLETED,
                result=HandoffResult(finding="x"),
            ).validate()

    def test_confidence_bounds_enforced(self) -> None:
        with pytest.raises(QcaeValidationError, match="confidence"):
            response_handoff(
                result=HandoffResult(finding="x", confidence=1.5)
            ).validate()


class TestFallbackAndFirewall:
    def test_local_fallback_round_trip(self) -> None:
        handoff = make_handoff(
            request_id="rh-0002",
            direction=HandoffDirection.QCAE_TO_RESEARCH_MESH,
            status=HandoffStatus.PARTIAL,
            research_question="q",
            result=HandoffResult(
                finding="local prior-art scan only",
                uncertainty="No Research Mesh synthesis; unreviewed sources",
            ),
            fallback_class=FallbackClass.LOCAL_FALLBACK_RESEARCH,
            provenance=provenance(producer="qcae:research-fallback-adapter"),
        )
        rebuilt = ResearchCapabilityHandoff.from_dict(handoff.to_dict())
        assert rebuilt.fallback_class is FallbackClass.LOCAL_FALLBACK_RESEARCH
        assert rebuilt == handoff

    def test_local_fallback_marked(self) -> None:
        handoff = make_handoff(
            request_id="rh-0003",
            direction=HandoffDirection.RESEARCH_MESH_TO_QCAE,
            status=HandoffStatus.PARTIAL,
            result=HandoffResult(finding="x", uncertainty="u"),
            fallback_class=FallbackClass.LOCAL_FALLBACK_RESEARCH,
            provenance=provenance(),
        )
        assert handoff.fallback_class is FallbackClass.LOCAL_FALLBACK_RESEARCH

    def test_fallback_requires_uncertainty(self) -> None:
        """A-001 §5: fallback results carry explicit uncertainty."""
        with pytest.raises(QcaeValidationError, match="uncertainty"):
            make_handoff(
                request_id="rh-0004",
                direction=HandoffDirection.RESEARCH_MESH_TO_QCAE,
                status=HandoffStatus.PARTIAL,
                result=HandoffResult(finding="confident-sounding claim", uncertainty=None),
                fallback_class=FallbackClass.LOCAL_FALLBACK_RESEARCH,
                provenance=provenance(),
            )

    def test_fallback_cannot_represent_doctrine_promotion(self) -> None:
        """The contract has no doctrine-promotion representation at all: no
        status, output, or field can express promoting a fallback result into
        institutional doctrine."""
        all_values = {
            *(s.value for s in HandoffStatus),
            *(o.value for o in RequiredOutput),
        }
        assert "DOCTRINE_PROMOTED" not in all_values
        assert "PROMOTE" not in {o.value for o in RequiredOutput}
        # And the drift guard pins the enum sets to the A-001 schema values.

    def test_research_evidence_cannot_directly_set_capability_proven(self) -> None:
        """A-001 invariant 4: a completed handoff is evidence input only.

        The handoff contract exposes no lifecycle state, no waiver, and no
        promotion authority — proving obligations remain with QCAE's evidence
        gates (core.lifecycle). This test pins the firewall structurally.
        """
        completed = response_handoff()
        completed.validate()
        payload = completed.to_dict()
        # No lifecycle-control fields exist on the contract.
        forbidden_fields = {
            "lifecycle_state", "lifecycle", "promotion", "waiver",
            "approved", "authority", "evidence_gate",
        }
        assert not (set(payload) & forbidden_fields)
        # The contract does not import or wrap lifecycle machinery.
        import qcae.core.amendments.a001.handoff as handoff_module

        source = handoff_module.__doc__ or ""
        assert "EVIDENCE INPUT" in source

    def test_interface_version_mismatch_rejected(self) -> None:
        handoff = response_handoff(interface_version="2.0")
        with pytest.raises(QcaeValidationError, match="interface_version"):
            handoff.validate()

    def test_required_output_enums_match_schema(self) -> None:
        """Pinned to A-001 research-capability-handoff.schema.json required_outputs."""
        assert {o.value for o in RequiredOutput} == {
            "EVIDENCE_PACKAGE", "SYNTHESIS", "SPECIFICATION_INPUT", "ASSUMPTIONS",
            "CONTRADICTIONS", "TESTABLE_CLAIMS", "UNCERTAINTY", "PROVENANCE",
            "RECOMMENDED_NEXT_ACTION",
        }

    def test_handoff_mode_enums_match_schema(self) -> None:
        assert {m.value for m in HandoffMode} == {
            "INTERNAL_ACQUISITION", "QCAE_CAPABILITY_RESEARCH", "CLIENT_RESEARCH_SERVICE",
        }

    def test_status_enums_match_schema(self) -> None:
        assert {s.value for s in HandoffStatus} == {
            "REQUESTED", "IN_PROGRESS", "COMPLETED", "PARTIAL", "BLOCKED", "REFUSED",
        }
