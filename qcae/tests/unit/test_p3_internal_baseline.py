"""P3-C03 — internal-first baseline: canon 2.6 laws.

Covers internal-first ordering (2.6.1/2.6.6), the internal trust firewall
(2.6.3/2.6.10), prior-decision lookup (2.6.5), partial-reuse narrowing (2.6.8),
the duplicate seed (2.6.9), confidentiality fail-closed behaviour (2.6.11) and
the explicit baseline requirement (2.6.7). The service is exercised against a
fake ``RegistryQuery`` so the suite proves the *mapping and its laws*, not a
particular SQLite build.
"""

from __future__ import annotations

import pytest

from qcae.core.discovery import (
    CostTier,
    DiscoveryBudget,
    DiversityRequirement,
    QueryFamilyKind,
    QueryFamilyRecord,
    SearchHypothesis,
    SearchHypothesisKind,
    SourceAllocation,
    SourceClass,
    StopCondition,
    StopRule,
    make_discovery_plan,
)
from qcae.core.errors import QcaeValidationError
from qcae.core.ports.knowledge_registry import RegistryQuery
from qcae.core.vocabulary import VerificationLevel
from qcae.discovery.internal.baseline import (
    NON_DERIVABLE_CLASSIFICATIONS,
    InternalBaselineClassification as C,
    InternalBaselineRecord,
    InternalDiscoveryBaselineService,
    InternalDiscoveryPolicy,
)

CAP = "CAP-REPLAY-001"
ATOM_A = "atom-causal-ordering"
ATOM_B = "atom-duplicate-suppression"


# -- fakes ------------------------------------------------------------------


class FakeRegistryQuery(RegistryQuery):
    """Records what the baseline service asks; returns scripted durable state."""

    def __init__(
        self,
        categories=(),
        detail=None,
        atom_ids=(),
        candidate_refs=(),
        reuse=None,
    ) -> None:
        self._findings = {"capability_id": CAP, "categories": list(categories),
                          "detail": dict(detail or {})}
        self._state = {
            "contract_versions": [1],
            "latest_contract_version": 1,
            "atom_ids": list(atom_ids),
            "composite_member_count": None,
            "candidate_refs": list(candidate_refs),
        }
        self._reuse = reuse or {
            "active_receipts": [],
            "positive_knowledge": [],
            "negative_blocks": [],
            "stale_evidence": [],
            "sufficient_without_discovery": False,
        }
        self.calls = []

    def internal_first_findings(self, capability_id, contract_id, contract_version):
        self.calls.append(("internal_first_findings", capability_id, contract_id, contract_version))
        return self._findings

    def known_capability_state(self, capability_id):
        self.calls.append(("known_capability_state", capability_id))
        return self._state

    def decision_reuse_findings(self, capability_id, contract_id, contract_version):
        self.calls.append(("decision_reuse_findings", capability_id, contract_id, contract_version))
        return self._reuse


def plan():
    """Two requested atoms; a two-family portfolio so the plan itself is valid."""
    return make_discovery_plan(
        discovery_plan_id="plan-001",
        contract_id=CAP,
        contract_version=1,
        atom_ids=(ATOM_A, ATOM_B),
        internal_baseline_queries=("internal:capability-registry:CAP-REPLAY-001",),
        search_hypotheses=(
            SearchHypothesis(
                hypothesis_id="hyp-a",
                atom_ids=(ATOM_A,),
                kind=SearchHypothesisKind.FOCUSED_LIBRARY,
                statement="A may exist as a focused library",
            ),
            SearchHypothesis(
                hypothesis_id="hyp-b",
                atom_ids=(ATOM_B,),
                kind=SearchHypothesisKind.EXTRACTABLE_SUBSYSTEM,
                statement="B may exist inside a larger framework",
            ),
        ),
        query_families=(
            QueryFamilyRecord(
                family_id="fam-behavioral",
                kind=QueryFamilyKind.BEHAVIORAL,
                hypothesis_ids=("hyp-a",),
                terms=("causal ordering",),
                source_classes=(SourceClass.INTERNAL_REGISTRY_CODE,
                                SourceClass.GITHUB_REPOSITORY_CODE),
            ),
            QueryFamilyRecord(
                family_id="fam-synonym",
                kind=QueryFamilyKind.SYNONYM,
                hypothesis_ids=("hyp-b",),
                terms=("event deduplication",),
                source_classes=(SourceClass.PACKAGE_ECOSYSTEM,),
            ),
            QueryFamilyRecord(
                family_id="fam-spec",
                kind=QueryFamilyKind.SPECIFICATION_PAPER,
                hypothesis_ids=("hyp-a", "hyp-b"),
                terms=("ordering specification",),
                source_classes=(SourceClass.RESEARCH_LITERATURE,),
            ),
        ),
        source_allocations=(
            SourceAllocation(source_class=SourceClass.INTERNAL_REGISTRY_CODE, budget_share=0.2,
                             max_tier=CostTier.TIER_0_MEMORY_LOOKUP),
            SourceAllocation(source_class=SourceClass.GITHUB_REPOSITORY_CODE, budget_share=0.3,
                             max_tier=CostTier.TIER_3_SOURCE_TREE),
            SourceAllocation(source_class=SourceClass.PACKAGE_ECOSYSTEM, budget_share=0.3),
            SourceAllocation(source_class=SourceClass.RESEARCH_LITERATURE, budget_share=0.2),
        ),
        budget=DiscoveryBudget(max_queries=10, max_results_inspected=50,
                               max_source_calls=10, max_wall_clock_seconds=600),
        cost_tier_ceiling=CostTier.TIER_3_SOURCE_TREE,
        diversity_requirements=DiversityRequirement(),
        stop_rules=(
            StopRule(condition=StopCondition.BUDGET_CEILING_REACHED),
            StopRule(condition=StopCondition.NON_DOMINATED_SET_SUFFICIENT),
        ),
        created_by="qcae-discovery-planner",
        policy_version="discovery-ranking-policy-1.0",
        single_route_justification="narrow routes recorded for this fixture",
    )


def baseline(registry: RegistryQuery, **overrides) -> InternalBaselineRecord:
    service = InternalDiscoveryBaselineService(registry, InternalDiscoveryPolicy())
    kwargs = dict(
        baseline_id="baseline-001",
        plan=plan(),
        created_at="2026-09-21T12:00:00Z",
        created_by="qcae-internal-discovery",
    )
    kwargs.update(overrides)
    return service.build(**kwargs)


# -- classification mapping -------------------------------------------------


class TestBaselineClassification:
    def test_no_internal_knowledge_is_reported_as_absence(self) -> None:
        record = baseline(FakeRegistryQuery(categories=["NO_INTERNAL_KNOWLEDGE"]))
        assert record.sufficiency_verdict is C.NO_INTERNAL_CAPABILITY_FOUND
        assert record.covered_atoms == ()
        assert record.external_target_atoms == (ATOM_A, ATOM_B)
        assert record.external_search_required is True
        assert record.partial_reuse is False

    def test_active_receipt_with_full_coverage_is_fully_satisfied(self) -> None:
        record = baseline(
            FakeRegistryQuery(
                categories=["CAPABILITY_ACTIVE"],
                detail={"CAPABILITY_ACTIVE": ["rcpt-001"]},
                atom_ids=[ATOM_A, ATOM_B],
                candidate_refs=["cand-1"],
            )
        )
        assert record.sufficiency_verdict is C.FULLY_SATISFIED_INTERNAL
        assert record.missing_atoms == ()
        assert record.external_target_atoms == ()
        assert record.external_search_required is False

    def test_partial_internal_coverage_narrows_the_external_request(self) -> None:
        record = baseline(
            FakeRegistryQuery(
                categories=[],
                atom_ids=[ATOM_A],
                candidate_refs=["cand-1"],
            )
        )
        assert record.sufficiency_verdict is C.PARTIALLY_SATISFIED_INTERNAL
        assert record.covered_atoms == (ATOM_A,)
        assert record.missing_atoms == (ATOM_B,)
        assert record.external_target_atoms == (ATOM_B,)
        assert record.partial_reuse is True
        assert record.coverage_basis == "CAPABILITY_GRANULARITY_FROM_REGISTRY_STATE"

    def test_stale_evidence_marks_component_reusable_and_revalidation(self) -> None:
        record = baseline(
            FakeRegistryQuery(
                categories=["EVIDENCE_STALE"],
                detail={"EVIDENCE_STALE": ["ev-001"]},
                atom_ids=[ATOM_A, ATOM_B],
                candidate_refs=["cand-1"],
            )
        )
        assert C.INTERNAL_COMPONENT_REUSABLE in record.classifications
        assert record.requires_revalidation is True
        assert record.stale_evidence_refs == ("ev-001",)

    def test_prior_failure_carries_rejection_references(self) -> None:
        record = baseline(
            FakeRegistryQuery(
                categories=["CANDIDATE_PREVIOUSLY_FAILED"],
                detail={"CANDIDATE_PREVIOUSLY_FAILED": ["nk-001"]},
                reuse={
                    "active_receipts": [],
                    "positive_knowledge": [],
                    "negative_blocks": ["cand-bad"],
                    "stale_evidence": [],
                    "sufficient_without_discovery": False,
                },
            )
        )
        assert C.PRIOR_EXTERNAL_REJECTION_EXISTS in record.classifications
        assert record.prior_rejection_refs == ("cand-bad", "nk-001")

    def test_revision_change_forces_revalidation(self) -> None:
        record = baseline(
            FakeRegistryQuery(
                categories=["REVISION_CHANGED"],
                detail={"REVISION_CHANGED": ["cand-9"]},
                atom_ids=[ATOM_A],
                candidate_refs=["cand-9"],
            )
        )
        assert record.requires_revalidation is True
        assert record.revision_change_refs == ("cand-9",)

    def test_definition_without_implementation_is_partial(self) -> None:
        record = baseline(
            FakeRegistryQuery(
                categories=["DEFINITION_WITHOUT_IMPLEMENTATION"],
                detail={"DEFINITION_WITHOUT_IMPLEMENTATION": [ATOM_A, ATOM_B]},
            )
        )
        assert C.PARTIALLY_SATISFIED_INTERNAL in record.classifications
        assert record.sufficiency_verdict is C.NO_INTERNAL_CAPABILITY_FOUND
        assert record.external_target_atoms == (ATOM_A, ATOM_B)

    @pytest.mark.parametrize(
        "categories",
        [
            ["CAPABILITY_ACTIVE"],
            ["EVIDENCE_STALE"],
            ["CANDIDATE_PREVIOUSLY_FAILED"],
            ["REVISION_CHANGED"],
            ["DEFINITION_WITHOUT_IMPLEMENTATION"],
            ["NO_INTERNAL_KNOWLEDGE"],
            [],
        ],
    )
    def test_evaluation_only_classifications_are_never_invented(self, categories) -> None:
        record = baseline(FakeRegistryQuery(categories=categories, atom_ids=[ATOM_A, ATOM_B],
                                            candidate_refs=["cand-1", "cand-2"]))
        assert not (set(record.classifications) & NON_DERIVABLE_CLASSIFICATIONS)

    def test_capability_granularity_candidate_count_is_not_duplication(self) -> None:
        record = baseline(
            FakeRegistryQuery(atom_ids=[ATOM_A, ATOM_B],
                              candidate_refs=["cand-1", "cand-2"])
        )
        assert C.DUPLICATE_IMPLEMENTATIONS not in record.classifications

    def test_attributed_duplicate_implementations_are_seeded(self) -> None:
        record = baseline(
            FakeRegistryQuery(atom_ids=[ATOM_A, ATOM_B], candidate_refs=["cand-1", "cand-2"]),
            atom_coverage={ATOM_A: ["cand-1", "cand-2"], ATOM_B: ["cand-3"]},
        )
        assert C.DUPLICATE_IMPLEMENTATIONS in record.classifications
        assert record.coverage_basis == "ATOM_ATTRIBUTED_BY_CALLER"
        assert record.internal_candidate_refs == ("cand-1", "cand-2", "cand-3")


# -- trust firewall / policy ------------------------------------------------


class TestTrustFirewall:
    def test_internal_ownership_confers_no_verification(self) -> None:
        record = baseline(
            FakeRegistryQuery(categories=["CAPABILITY_ACTIVE"], atom_ids=[ATOM_A, ATOM_B],
                              candidate_refs=["cand-1"])
        )
        assert record.internal_trust_level is VerificationLevel.DISCOVERED

    def test_access_classification_travels_with_the_baseline(self) -> None:
        service = InternalDiscoveryBaselineService(
            FakeRegistryQuery(), InternalDiscoveryPolicy(access_classification="INTERNAL-CONFIDENTIAL")
        )
        record = service.build(
            baseline_id="baseline-002",
            plan=plan(),
            created_at="2026-09-21T12:00:00Z",
            created_by="qcae-internal-discovery",
        )
        assert record.access_classification == "INTERNAL-CONFIDENTIAL"

    def test_sufficiency_from_prior_decision_cannot_bypass_missing_atoms(self) -> None:
        record = baseline(
            FakeRegistryQuery(
                atom_ids=[ATOM_A],
                candidate_refs=["cand-1"],
                reuse={
                    "active_receipts": ["rcpt-1"],
                    "positive_knowledge": ["pk-1"],
                    "negative_blocks": [],
                    "stale_evidence": [],
                    "sufficient_without_discovery": True,
                },
            )
        )
        assert record.sufficient_without_discovery is False
        assert record.external_target_atoms == (ATOM_B,)


# -- fail-closed laws -------------------------------------------------------


class TestFailClosed:
    def test_unknown_category_is_refused(self) -> None:
        with pytest.raises(QcaeValidationError, match="unknown internal-first category"):
            baseline(FakeRegistryQuery(categories=["SOMETHING_NEW"]))

    def test_unrecognizable_findings_shape_is_refused(self) -> None:
        registry = FakeRegistryQuery()
        registry._findings = {"capability_id": CAP}
        with pytest.raises(QcaeValidationError, match="unrecognizable"):
            baseline(registry)

    def test_non_object_detail_is_refused(self) -> None:
        registry = FakeRegistryQuery()
        registry._findings = {"capability_id": CAP, "categories": [], "detail": ["nope"]}
        with pytest.raises(QcaeValidationError, match="non-object detail"):
            baseline(registry)

    def test_atom_coverage_outside_plan_scope_is_refused(self) -> None:
        with pytest.raises(QcaeValidationError, match="outside the plan scope"):
            baseline(FakeRegistryQuery(), atom_coverage={"atom-not-requested": ["cand-1"]})

    def test_service_queries_use_capability_identity_and_string_version(self) -> None:
        registry = FakeRegistryQuery()
        baseline(registry)
        assert ("internal_first_findings", CAP, CAP, "1") in registry.calls
        assert ("decision_reuse_findings", CAP, CAP, "1") in registry.calls
        assert ("known_capability_state", CAP) in registry.calls


# -- real registry wiring ---------------------------------------------------


class TestRealRegistryWiring:
    """The baseline service over the real P1 registry query (not a fake).

    P1 documents partial wiring as a valid shape ("shape is stable regardless of
    wiring") and constructs the query with absent repositories in its own tests.
    A discovery attempt on that wiring must produce a baseline, not crash.
    """

    def _real_query(self):
        from qcae.infrastructure.persistence.sqlite_capability_registry import (
            CAPABILITY_REGISTRY_DDL,
            SqliteCapabilityRegistry,
        )
        from qcae.infrastructure.persistence.sqlite_knowledge_store import (
            KNOWLEDGE_DDL,
            SqliteNegativeKnowledgeRepository,
            SqliteRegistryQuery,
        )
        from qcae.infrastructure.persistence.sqlite_repository_registry import (
            REPOSITORY_REGISTRY_DDL,
            SqliteRepositoryRegistry,
        )
        from qcae.infrastructure.persistence.store_factory import open_metadata_db

        conn = open_metadata_db(":memory:")
        for ddl in (CAPABILITY_REGISTRY_DDL, REPOSITORY_REGISTRY_DDL, KNOWLEDGE_DDL):
            conn.executescript(ddl)
        return conn, SqliteRegistryQuery(
            None, None, SqliteNegativeKnowledgeRepository(conn), None,
            capability_registry=SqliteCapabilityRegistry(conn),
            repository_registry=SqliteRepositoryRegistry(conn),
        )

    def test_partially_wired_registry_produces_a_baseline(self) -> None:
        conn, query = self._real_query()
        try:
            record = baseline(query)
        finally:
            conn.close()
        assert record.sufficiency_verdict is C.NO_INTERNAL_CAPABILITY_FOUND
        assert record.external_target_atoms == (ATOM_A, ATOM_B)


# -- record laws ------------------------------------------------------------


class TestBaselineRecordLaws:
    def _record_kwargs(self, **overrides):
        kwargs = dict(
            baseline_id="baseline-003",
            capability_id=CAP,
            contract_id=CAP,
            contract_version=1,
            requested_atoms=(ATOM_A,),
            covered_atoms=(),
            missing_atoms=(ATOM_A,),
            external_target_atoms=(ATOM_A,),
            classifications=(C.NO_INTERNAL_CAPABILITY_FOUND,),
            sufficiency_verdict=C.NO_INTERNAL_CAPABILITY_FOUND,
            query_provenance=("internal:capability-registry:CAP-REPLAY-001",),
            created_at="2026-09-21T12:00:00Z",
            created_by="qcae-internal-discovery",
        )
        kwargs.update(overrides)
        return kwargs

    def test_missing_atoms_must_be_requested_minus_covered(self) -> None:
        with pytest.raises(QcaeValidationError, match="minus the covered ones"):
            InternalBaselineRecord(**self._record_kwargs(missing_atoms=())).validate()

    def test_external_target_must_equal_uncovered_atoms(self) -> None:
        with pytest.raises(QcaeValidationError, match="partial reuse"):
            InternalBaselineRecord(**self._record_kwargs(external_target_atoms=())).validate()

    def test_fully_satisfied_cannot_leave_uncovered_atoms(self) -> None:
        with pytest.raises(QcaeValidationError, match="cannot leave uncovered atoms"):
            InternalBaselineRecord(
                **self._record_kwargs(
                    classifications=(C.FULLY_SATISFIED_INTERNAL,),
                    sufficiency_verdict=C.FULLY_SATISFIED_INTERNAL,
                )
            ).validate()

    def test_absence_verdict_requires_no_coverage(self) -> None:
        with pytest.raises(QcaeValidationError, match="cannot be reported"):
            InternalBaselineRecord(
                **self._record_kwargs(
                    covered_atoms=(ATOM_A,),
                    missing_atoms=(),
                    external_target_atoms=(),
                    classifications=(C.NO_INTERNAL_CAPABILITY_FOUND,),
                    sufficiency_verdict=C.NO_INTERNAL_CAPABILITY_FOUND,
                )
            ).validate()

    def test_comparative_classification_requires_basis(self) -> None:
        with pytest.raises(QcaeValidationError, match="comparative evidence"):
            InternalBaselineRecord(
                **self._record_kwargs(
                    classifications=(C.NO_INTERNAL_CAPABILITY_FOUND,
                                    C.INTERNAL_IMPLEMENTATION_SUPERIOR),
                )
            ).validate()
        ok = InternalBaselineRecord(
            **self._record_kwargs(
                classifications=(C.NO_INTERNAL_CAPABILITY_FOUND,
                                C.INTERNAL_IMPLEMENTATION_SUPERIOR),
                comparison_basis="benchmark ev-77 under the contract",
            )
        )
        ok.validate()

    def test_revalidation_flag_requires_cited_state(self) -> None:
        with pytest.raises(QcaeValidationError, match="must cite the stale evidence"):
            InternalBaselineRecord(**self._record_kwargs(requires_revalidation=True)).validate()

    def test_query_provenance_is_required(self) -> None:
        with pytest.raises(QcaeValidationError, match="query provenance"):
            InternalBaselineRecord(**self._record_kwargs(query_provenance=())).validate()

    def test_sufficiency_must_be_among_classifications(self) -> None:
        with pytest.raises(QcaeValidationError, match="must be one of the record's"):
            InternalBaselineRecord(
                **self._record_kwargs(
                    covered_atoms=(ATOM_A,),
                    missing_atoms=(),
                    external_target_atoms=(),
                    classifications=(C.INTERNAL_COMPONENT_REUSABLE,),
                    sufficiency_verdict=C.PARTIALLY_SATISFIED_INTERNAL,
                )
            ).validate()

    def test_round_trip_preserves_classifications(self) -> None:
        record = baseline(FakeRegistryQuery(categories=["NO_INTERNAL_KNOWLEDGE"]))
        restored = InternalBaselineRecord.from_dict(record.to_dict())
        assert restored == record
        assert restored.sufficiency_verdict is C.NO_INTERNAL_CAPABILITY_FOUND
