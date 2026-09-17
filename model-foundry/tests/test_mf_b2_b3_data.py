"""MF-B2 (rights, roles, contamination) and MF-B3 (refinery) tests."""

from __future__ import annotations

import dataclasses

import pytest

from foundry.core import Contradiction, PolicyBlocked
from foundry.data import (
    ContaminationRelation,
    RightsDisposition,
    SourceRecord,
    SourceRegistry,
    assert_role_transition_allowed,
)
from foundry.enums import (
    ContaminationClass,
    ContaminationType,
    RightsBasis,
    RightsState,
    RefineryFailure,
    SourceRole,
    TrustClass,
)
from foundry.fixtures import build_registry, load_bundle, load_contamination
from foundry.refinery import (
    DEFAULT_RECIPE,
    DatasetRefinery,
    RawItem,
    RefineryRecipe,
    assert_manifest_covers_sources,
    audit_point_in_time,
    dedup,
    scan_secrets,
)

PIT_INSTANT = "2026-01-02T00:00:00Z"


def _rights(basis: RightsBasis, *, resolved: bool = True, scope: str = "") -> RightsDisposition:
    return RightsDisposition(
        subject="SRC",
        basis=basis,
        basis_ref="ref://x",
        basis_resolved=resolved,
        basis_scope=scope,
        decided_utc="2026-01-01T00:00:00Z",
    )


@pytest.mark.parametrize(
    ("basis", "resolved", "scope", "expected"),
    [
        (RightsBasis.EXPLICIT_OPEN_LICENSE, True, "train", RightsState.RIGHTS_VERIFIED_BY_POLICY),
        (RightsBasis.PUBLIC_DOMAIN, True, "", RightsState.RIGHTS_VERIFIED_BY_POLICY),
        (RightsBasis.OPERATOR_OWNED, True, "", RightsState.RIGHTS_VERIFIED_BY_POLICY),
        (RightsBasis.DIRECT_PERMISSION, True, "", RightsState.RIGHTS_VERIFIED_BY_POLICY),
        (RightsBasis.PROVIDER_TERMS_ALLOW, True, "scope recorded", RightsState.RIGHTS_VERIFIED_BY_POLICY),
        (RightsBasis.PROVIDER_TERMS_ALLOW, True, "", RightsState.RIGHTS_RESTRICTED),
        (RightsBasis.UNKNOWN, True, "", RightsState.RIGHTS_UNKNOWN),
        (RightsBasis.RIGHTS_REVIEW_REQUIRED, True, "", RightsState.REVIEW_REQUIRED),
        (RightsBasis.PROHIBITED, True, "", RightsState.EXCLUDED_BY_POLICY),
        (RightsBasis.EXPLICIT_OPEN_LICENSE, False, "", RightsState.REVIEW_REQUIRED),
    ],
)
def test_rights_state_is_derived_from_evidence(
    basis: RightsBasis, resolved: bool, scope: str, expected: RightsState
) -> None:
    disposition = _rights(basis, resolved=resolved, scope=scope)
    assert disposition.state is expected
    assert disposition.permits_training() is (expected is RightsState.RIGHTS_VERIFIED_BY_POLICY)


def test_claiming_rights_without_resolving_the_basis_does_not_grant_them() -> None:
    unresolved = _rights(RightsBasis.EXPLICIT_OPEN_LICENSE, resolved=False)
    assert unresolved.state is RightsState.REVIEW_REQUIRED
    assert unresolved.to_dict()["permits_training"] is False


def test_unknown_rights_cannot_transition_into_a_training_role() -> None:
    with pytest.raises(PolicyBlocked) as exc:
        assert_role_transition_allowed(
            SourceRole.RETRIEVAL_ONLY,
            SourceRole.TRAIN_CPT,
            rights=_rights(RightsBasis.UNKNOWN),
            actor="builder",
        )
    assert exc.value.code == "RIGHTS_BLOCKED"


def test_retrieval_only_to_train_requires_review_evidence_even_with_permissive_rights() -> None:
    rights = _rights(RightsBasis.OPERATOR_OWNED)
    with pytest.raises(PolicyBlocked) as exc:
        assert_role_transition_allowed(
            SourceRole.RETRIEVAL_ONLY, SourceRole.TRAIN_CPT, rights=rights, actor="builder"
        )
    assert exc.value.code == "ROLE_LAUNDERING_REFUSED"
    assert_role_transition_allowed(
        SourceRole.RETRIEVAL_ONLY,
        SourceRole.TRAIN_CPT,
        rights=rights,
        actor="operator",
        human_review_ref="review://operator/44",
    ) is None


def test_role_noop_and_sealed_retirement_are_refused() -> None:
    rights = _rights(RightsBasis.OPERATOR_OWNED)
    with pytest.raises(PolicyBlocked) as exc:
        assert_role_transition_allowed(
            SourceRole.TRAIN_CPT, SourceRole.TRAIN_CPT, rights=rights, actor="builder"
        )
    assert exc.value.code == "ROLE_TRANSITION_NOOP"
    with pytest.raises(PolicyBlocked) as exc2:
        assert_role_transition_allowed(
            SourceRole.SEALED_CONFIRMATION, SourceRole.EXCLUDED, rights=rights, actor="builder"
        )
    assert exc2.value.code == "SEALED_ROLE_RETIREMENT_REQUIRES_OPERATOR"


def test_registry_versions_role_changes_and_keeps_history() -> None:
    registry = build_registry()
    before = registry.get("SRC_NEWS_ALPHA")
    updated = registry.transition_role(
        "SRC_NEWS_ALPHA",
        SourceRole.DEV,
        actor="operator",
        reason="hold out for development evaluation",
    )
    assert updated.role is SourceRole.DEV
    assert registry.version("SRC_NEWS_ALPHA") == 2
    history = registry.role_history("SRC_NEWS_ALPHA")
    assert [entry[0] for entry in history] == [SourceRole.TRAIN_CPT, SourceRole.DEV]
    assert before.role is SourceRole.TRAIN_CPT  # the old version is still intact
    entries = registry.history("SRC_NEWS_ALPHA")
    assert entries[1].predecessor_fingerprint is not None


def test_registry_requires_integrity_digest_and_actor_reason() -> None:
    registry = SourceRegistry()
    record = dataclasses.replace(
        build_registry().get("SRC_NEWS_ALPHA"), source_id="SRC_NO_DIGEST", integrity_digest=""
    )
    with pytest.raises(PolicyBlocked) as exc:
        registry.register(record, actor="builder", reason="no digest")
    assert exc.value.code == "SOURCE_INTEGRITY_DIGEST_REQUIRED"
    with pytest.raises(PolicyBlocked):
        registry.register(
            build_registry().get("SRC_NEWS_ALPHA"), actor="", reason="no actor"
        )


def test_mirror_aliases_do_not_manufacture_diversity() -> None:
    registry = build_registry()
    diversity = registry.effective_diversity(["SRC_NEWS_ALPHA", "SRC_NEWS_ALPHA_MIRROR"])
    assert diversity["requested_sources"] == 2
    assert diversity["effective_lineages"] == 1
    assert diversity["diversity_is_claimed_not_effective"] is True
    assert registry.lineage_of("SRC_NEWS_ALPHA_MIRROR") == registry.lineage_of("SRC_NEWS_ALPHA")


def test_rights_permission_is_not_the_same_as_role_permission() -> None:
    registry = build_registry()
    assert registry.get("SRC_BENCH_CORE").trainable() is True
    assert registry.get("SRC_BENCH_CORE").role_permits_training() is False
    assert registry.get("SRC_BENCH_CORE").eligible_for_training() is False
    assert "SRC_BENCH_CORE" in registry.rights_permissive_but_role_forbidden()
    assert set(registry.trainable_sources()) == {
        "SRC_AGENT_TRACE",
        "SRC_NEWS_ALPHA",
        "SRC_NEWS_ALPHA_MIRROR",
    }


def test_contamination_graph_grades_and_blocks_claims() -> None:
    graph = load_contamination()
    assert graph.grade_between("SRC_NEWS_ALPHA", "SRC_BENCH_CORE") is ContaminationClass.C3_PARAPHRASE_OR_SOLUTION_OVERLAP
    assert graph.worst_grade("SRC_NEWS_ALPHA") is ContaminationClass.C4_DIRECT_ITEM_OR_ANSWER_OVERLAP
    assert graph.claim_blocking_edges("SRC_NEWS_ALPHA")
    # No observed edge is not a cleanliness certificate.
    assert graph.worst_grade("SRC_SECRET_INCIDENT") is ContaminationClass.C0_NO_OBSERVED_OVERLAP
    assert graph.to_dict()["unobserved_overlap_is_not_cleanliness"] is True


def test_contamination_severity_ordering_keeps_unknown_above_clean() -> None:
    from foundry.enums import CONTAMINATION_SEVERITY

    assert (
        CONTAMINATION_SEVERITY[ContaminationClass.C5_UPSTREAM_PROVENANCE_UNKNOWN]
        > CONTAMINATION_SEVERITY[ContaminationClass.C0_NO_OBSERVED_OVERLAP]
    )
    assert (
        CONTAMINATION_SEVERITY[ContaminationClass.C4_DIRECT_ITEM_OR_ANSWER_OVERLAP]
        > CONTAMINATION_SEVERITY[ContaminationClass.C2_SEMANTIC_TASK_PROXIMITY]
    )


def test_cerebus_family_withholding_is_operational() -> None:
    registry = build_registry()
    assert registry.doctrine_bearing_sources() == ("SRC_CEREBUS_RULES",)
    with pytest.raises(PolicyBlocked) as exc:
        registry.assert_doctrine_withheld("SRC_CEREBUS_RULES")
    assert exc.value.code == "CEREBUS_FAMILY_WITHHELD"
    with pytest.raises(PolicyBlocked):
        registry.assert_no_doctrine_leak(["SRC_NEWS_ALPHA", "SRC_CEREBUS_RULES"])
    registry.assert_doctrine_withheld("SRC_NEWS_ALPHA")


def test_provenance_summary_penalises_unknown_ancestry() -> None:
    registry = build_registry()
    summary = registry.provenance_summary(["SRC_NEWS_ALPHA", "SRC_AGENT_TRACE"])
    assert summary["unknown_ancestry_sources"] == ["SRC_AGENT_TRACE"]
    assert summary["claim_strength_penalty"] is True


# -- MF-B3 ------------------------------------------------------------------


def _refinery() -> tuple[DatasetRefinery, object]:
    registry = build_registry()
    bundle = load_bundle()
    return DatasetRefinery(registry=registry, contamination=bundle.contamination), bundle


def test_manifest_is_deterministic_and_lineage_bound() -> None:
    refinery, bundle = _refinery()
    sources = ["SRC_NEWS_ALPHA", "SRC_NEWS_ALPHA_MIRROR", "SRC_AGENT_TRACE"]
    first = refinery.refine(
        dataset_id="ds.a", purpose="p", role=SourceRole.TRAIN_CPT, items=bundle.items, source_ids=sources
    )
    second = refinery.refine(
        dataset_id="ds.a", purpose="p", role=SourceRole.TRAIN_CPT, items=bundle.items, source_ids=sources
    )
    assert first.manifest is not None and second.manifest is not None
    assert first.manifest.lineage_fingerprint == second.manifest.lineage_fingerprint
    # ALPHA-0001-DUP is an exact duplicate; the mirror copy and the variant item
    # are caught across sources by near-duplicate detection.
    assert first.manifest.dedup["exact_duplicates_collapsed"] == 1
    assert first.manifest.dedup["near_duplicate_count"] >= 2
    assert first.manifest.dedup["cross_source_duplicate_count"] >= 1
    assert first.manifest.splits["strategy"] == "BY_SOURCE"
    assert first.manifest.splits["item_level_random_split_used"] is False
    assert first.manifest.dedup["duplicates_do_not_add_diversity"] is True


def test_exact_and_near_duplicates_collapse_deterministically() -> None:
    refinery, bundle = _refinery()
    run = refinery.refine(
        dataset_id="ds.dedup",
        purpose="p",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_NEWS_ALPHA"],
        recipe=RefineryRecipe(
            recipe_id="recipe.dedup.test",
            steps=("normalize_whitespace", "exact_dedup", "near_dedup"),
            dedup_shingle_size=3,
            dedup_jaccard_threshold=0.6,
        ),
    )
    assert run.manifest is not None
    assert run.manifest.dedup["exact_duplicates_collapsed"] == 1  # ALPHA-0001-DUP
    assert run.manifest.dedup["near_duplicate_count"] >= 1  # ALPHA-0002-NEAR


def test_unknown_rights_sources_never_enter_a_training_dataset() -> None:
    refinery, bundle = _refinery()
    run = refinery.refine(
        dataset_id="ds.rights",
        purpose="p",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_NEWS_ALPHA", "SRC_RIGHTS_UNKNOWN", "SRC_VENDOR_TERMS"],
    )
    assert run.manifest is not None
    excluded = {entry["source_id"]: entry["reason"] for entry in run.manifest.excluded_sources}
    assert excluded["SRC_RIGHTS_UNKNOWN"] == RefineryFailure.RIGHTS_BLOCKED.value
    assert excluded["SRC_VENDOR_TERMS"] == RefineryFailure.RIGHTS_BLOCKED.value
    assert "SRC_RIGHTS_UNKNOWN" not in [s["source_id"] for s in run.manifest.sources]


def test_withheld_doctrine_cannot_be_refined_into_a_dataset() -> None:
    refinery, bundle = _refinery()
    run = refinery.refine(
        dataset_id="ds.withheld",
        purpose="p",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_CEREBUS_RULES"],
    )
    assert run.manifest is None
    assert run.negative_result is not None
    assert run.negative_result.failure is RefineryFailure.CONTAMINATION_BLOCKED
    assert run.negative_result.blocked_sources == ("SRC_CEREBUS_RULES",)
    assert run.negative_result.to_dict()["negative_result_is_project_failure"] is False
    assert run.negative_result.reopen_condition


def test_secret_scan_refuses_a_dataset_and_reports_patterns() -> None:
    _, bundle = _refinery()
    scan = scan_secrets(bundle.items)
    assert scan.passed() is False
    patterns = {hit["pattern"] for hit in scan.hits}
    assert patterns >= {"aws_access_key", "api_key_assignment"}
    assert all(hit["source_id"] == "SRC_SECRET_INCIDENT" for hit in scan.hits)
    refinery = DatasetRefinery(registry=build_registry(), contamination=bundle.contamination)
    run = refinery.refine(
        dataset_id="ds.secret",
        purpose="p",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_SECRET_INCIDENT"],
    )
    assert run.manifest is None
    assert run.negative_result is not None
    assert run.negative_result.failure is RefineryFailure.SCHEMA_INVALID


def test_negative_result_names_the_dominant_reason() -> None:
    refinery, bundle = _refinery()
    run = refinery.refine(
        dataset_id="ds.reason",
        purpose="p",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_CEREBUS_RULES", "SRC_RIGHTS_UNKNOWN"],
    )
    assert run.negative_result is not None
    assert run.negative_result.failure is RefineryFailure.CONTAMINATION_BLOCKED


def test_point_in_time_audit_detects_future_and_implausible_knowledge() -> None:
    _, bundle = _refinery()
    market = [item for item in bundle.items if item.source_id == "SRC_MARKET_TICKS_PIT"]
    audit = audit_point_in_time(market, decision_reference_utc=PIT_INSTANT)
    reasons = {violation["reason"] for violation in audit.violations}
    assert "FUTURE_INFORMATION_AT_DECISION_INSTANT" in reasons
    assert "KNOWLEDGE_PRECEDES_EVENT" in reasons
    assert audit.passed() is False

    unknown = audit_point_in_time(
        [RawItem(item_id="X", source_id="S", text="t", event_time_utc="2026-01-01T00:00:00Z", known_at_utc="")]
    )
    assert {v["reason"] for v in unknown.violations} == {"KNOWN_AT_UNKNOWN"}


def test_pit_leakage_blocks_a_training_dataset() -> None:
    refinery, bundle = _refinery()
    run = refinery.refine(
        dataset_id="ds.pit",
        purpose="p",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_MARKET_TICKS_PIT"],
        decision_reference_utc=PIT_INSTANT,
    )
    assert run.manifest is None
    assert run.negative_result is not None
    assert run.negative_result.failure is RefineryFailure.PIT_INVALID
    assert run.negative_result.evidence["checked"] >= 1


def test_lax_failure_tolerance_records_pit_violations_without_hiding_them() -> None:
    refinery, bundle = _refinery()
    run = refinery.refine(
        dataset_id="ds.pit.lax",
        purpose="p",
        role=SourceRole.DEV,
        items=bundle.items,
        source_ids=["SRC_MARKET_TICKS_PIT"],
        decision_reference_utc=PIT_INSTANT,
        failure_tolerance="RECORD",
    )
    assert run.manifest is not None
    assert run.manifest.pit_audit["passed"] is False
    assert run.manifest.pit_audit["violations"]


def test_manifest_guard_refuses_unresolved_or_illegal_sources() -> None:
    refinery, bundle = _refinery()
    run = refinery.refine(
        dataset_id="ds.guard",
        purpose="p",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_NEWS_ALPHA"],
    )
    assert run.manifest is not None
    assert_manifest_covers_sources(run.manifest, refinery.registry) is None

    from foundry.enums import RightsState

    forged_registry = build_registry()
    forged = dataclasses.replace(
        run.manifest,
        sources=(
            {
                "source_id": "SRC_RIGHTS_UNKNOWN",
                "role": "RETRIEVAL_ONLY",
                "rights_state": RightsState.RIGHTS_UNKNOWN.value,
                "lineage": "crawl://unknown",
            },
        ),
    )
    with pytest.raises(Contradiction):
        assert_manifest_covers_sources(forged, forged_registry)


def test_derived_items_inherit_ancestor_restrictions_in_manifest_notes() -> None:
    refinery, bundle = _refinery()
    run = refinery.refine(
        dataset_id="ds.notes",
        purpose="p",
        role=SourceRole.TRAIN_CPT,
        items=bundle.items,
        source_ids=["SRC_AGENT_TRACE"],
    )
    assert run.manifest is not None
    assert run.manifest.notes == "derived artifacts inherit ancestor restrictions"
    assert run.manifest.provenance_summary["claim_strength_penalty"] is True
    assert run.manifest.trainable is True
    assert run.manifest.to_dict()["manifest_is_capability_claim"] is False
    dev_run = refinery.refine(
        dataset_id="ds.notes.dev",
        purpose="p",
        role=SourceRole.DEV,
        items=bundle.items,
        source_ids=["SRC_NEWS_ALPHA"],
    )
    assert dev_run.manifest is not None
    assert dev_run.manifest.trainable is False


def test_dedup_helper_is_stable_regardless_of_input_order() -> None:
    _, bundle = _refinery()
    items = [item for item in bundle.items if item.source_id == "SRC_NEWS_ALPHA"]
    forward, _ = dedup(items, shingle_size=3, jaccard_threshold=0.6)
    backward, _ = dedup(list(reversed(items)), shingle_size=3, jaccard_threshold=0.6)
    assert [item.item_id for item in forward] == [item.item_id for item in backward]


def test_recipe_declares_no_model_inference() -> None:
    assert DEFAULT_RECIPE.to_dict()["model_inference_used"] is False
    assert DEFAULT_RECIPE.fingerprint == DEFAULT_RECIPE.fingerprint


def test_contamination_relation_requires_incidence() -> None:
    relation = ContaminationRelation(
        left="A",
        right="B",
        contamination_type=ContaminationType.EXACT_DUPLICATE,
        evidence_ref="evidence://1",
        detected_by="test",
    )
    assert relation.other("A") == "B"
    assert relation.grade is ContaminationClass.C4_DIRECT_ITEM_OR_ANSWER_OVERLAP
    with pytest.raises(PolicyBlocked):
        relation.other("C")


def test_source_record_registration_is_not_a_cleanliness_claim() -> None:
    record = build_registry().get("SRC_NEWS_ALPHA")
    assert record.to_dict()["registration_is_cleanliness_claim"] is False
    assert record.trust_class is TrustClass.PUBLIC_RESEARCH
    assert record.eligible_for_training() is True
