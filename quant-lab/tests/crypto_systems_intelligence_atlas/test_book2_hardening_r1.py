"""Book 2 Hardening R1 — failing contract tests written before repairs."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from crypto_systems_intelligence_atlas import claims as claims_module
from crypto_systems_intelligence_atlas import freshness as freshness_module
from crypto_systems_intelligence_atlas import sources as sources_module
from crypto_systems_intelligence_atlas.authority import AuthorityPolicy
from crypto_systems_intelligence_atlas.claims import (
    Claim,
    ClaimService,
    ClaimState,
    Methodology,
    Proposition,
)
from crypto_systems_intelligence_atlas.evidence import EvidenceStore, EvidenceTier
from crypto_systems_intelligence_atlas.promotion import ClaimStateEngine
from crypto_systems_intelligence_atlas.sources import (
    AccessMethod,
    LocatorMetadata,
    Source,
    SourceRegistry,
    VerificationStatus,
)
from crypto_systems_intelligence_atlas.temporal import RecordLifecycle
from crypto_systems_intelligence_atlas.types import AuthoritySeed, AuthorityTier, ClaimFamily, SourceClass

NOW = datetime(2026, 9, 24, 12, 0, tzinfo=UTC)
LATER = NOW + timedelta(hours=1)


def make_kernel(source_class: SourceClass = SourceClass.NATIVE_TECHNICAL, owner: str = "owner:a"):
    sources = SourceRegistry()
    source = Source(
        source_id="csia:source:r1",
        source_class=source_class,
        canonical_name="R1 source",
        owner_entity_ref=owner,
        locator=LocatorMetadata(
            base_locator="fixture://r1",
            access_method=AccessMethod.DOCUMENT,
            authentication="none",
        ),
        authority_metadata=(
            AuthoritySeed(
                claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
                tier=AuthorityTier.PRIMARY,
                valid_from=NOW - timedelta(days=1),
                policy_version="v1",
            ),
        ),
        verification_status=VerificationStatus.VERIFIED,
        verification_evidence_refs=("verification-r1",),
        last_verified_at=NOW,
    )
    sources.register(source)
    authority = AuthorityPolicy()
    authority.register_source(source)
    evidence = EvidenceStore(sources)
    service = ClaimService(evidence, authority_policy=authority)
    return sources, authority, evidence, service, source


def make_claim(service, evidence, source, claim_id, *, state=ClaimState.OBSERVED, content=b"x", evidence_tier=EvidenceTier.FIRST_PARTY_DOC):
    captured = evidence.capture(
        source_id=source.source_id,
        retrieved_at=NOW,
        content=content,
        content_locator=f"fixture://{claim_id}",
        raw_snapshot_ref=f"snapshot://{claim_id}",
        extractor_version="r1",
        parser_version="p1",
        evidence_tier=evidence_tier,
    )
    return Claim(
        claim_id=claim_id,
        evidence_refs=(captured.evidence_id,),
        source_refs=(source.source_id,),
        proposition=Proposition(subject_refs=("corroborated-proposition",), predicate="state", object_ref="true"),
        claim_family=ClaimFamily.CHAIN_ARCHITECTURE,
        claim_state=state,
        valid_time_hypothesis=NOW,
        observed_time=NOW,
        methodology=Methodology(methodology_ref="direct", version="v1", description="direct"),
    )


def add_claim(service, claim):
    if hasattr(service, "add_declared") and claim.claim_state is ClaimState.DECLARED:
        return service.add_declared(claim)
    if hasattr(service, "add_observed") and claim.claim_state is ClaimState.OBSERVED:
        return service.add_observed(claim)
    return service.add(claim)


def test_a_book_1_record_lifecycle_is_frozen() -> None:
    assert set(RecordLifecycle) == {
        RecordLifecycle.DECLARED,
        RecordLifecycle.OBSERVED,
        RecordLifecycle.VERIFIED,
        RecordLifecycle.CONTESTED,
        RecordLifecycle.REJECTED,
    }


def test_b_book_2_claim_state_is_exactly_the_ratified_nine_states() -> None:
    state_enum = getattr(claims_module, "Book2ClaimState", None)
    assert state_enum is not None
    assert set(state_enum) == {
        state_enum.DECLARED,
        state_enum.OBSERVED,
        state_enum.INFERRED,
        state_enum.CORROBORATED,
        state_enum.CONTESTED,
        state_enum.UNRESOLVED,
        state_enum.STALE,
        state_enum.REJECTED,
        state_enum.SUPERSEDED,
    }
    assert not hasattr(state_enum, "VERIFIED")


def test_c_verified_is_rejected_for_book2_claim() -> None:
    _, _, _, service, source = make_kernel()
    with pytest.raises(ValueError):
        add_claim(service, make_claim(service, service.evidence_store, source, "verified", state=RecordLifecycle.VERIFIED))


def test_d_direct_corroborated_insertion_is_rejected() -> None:
    _, _, _, service, source = make_kernel()
    corroborated = getattr(ClaimState, "CORROBORATED", None)
    assert corroborated is not None
    evidence_store = service.evidence_store
    with pytest.raises(ValueError):
        add_claim(service, make_claim(service, evidence_store, source, "direct-corroborated", state=corroborated, content=b"corroborated"))


def test_e_direct_inferred_insertion_is_rejected() -> None:
    _, _, _, service, source = make_kernel()
    inferred = getattr(ClaimState, "INFERRED", None)
    assert inferred is not None
    with pytest.raises(ValueError):
        service.add(make_claim(service, service.evidence_store, source, "direct-inferred", state=inferred, content=b"inferred"))


def test_f_chain_specific_freshness_requires_context_then_evaluates() -> None:
    outcome = getattr(freshness_module, "FreshnessOutcome", None)
    context = getattr(freshness_module, "ChainFreshnessContext", None)
    assert outcome is not None and context is not None
    policy = freshness_module.FreshnessPolicy(
        policy_id="epoch-policy",
        version="v1",
        kind=freshness_module.StalenessKind.CLAIM_STALE,
        mode=freshness_module.FreshnessMode.CHAIN_SPECIFIC,
        chain_specific_window="epoch",
    )
    book = freshness_module.FreshnessPolicyBook()
    book.register(policy)
    unresolved = book.evaluate("epoch-policy", observed_at=NOW, now=LATER)
    assert unresolved.outcome is outcome.REQUIRES_CHAIN_CONTEXT
    assert unresolved.stale is None
    resolved = book.evaluate(
        "epoch-policy",
        observed_at=NOW,
        now=LATER,
        chain_context=context(window_id="epoch", observed_window="10", current_window="11"),
    )
    assert resolved.outcome is outcome.STALE
    assert resolved.stale is True


def test_g_same_source_does_not_corroborate() -> None:
    _, _, _, service, source = make_kernel()
    left = add_claim(service, make_claim(service, service.evidence_store, source, "left", content=b"left"))
    right = add_claim(service, make_claim(service, service.evidence_store, source, "right", content=b"right"))
    engine = ClaimStateEngine(service)
    with pytest.raises(ValueError):
        engine.transition(
            left.claim_id,
            ClaimState.CORROBORATED,
            triggering_evidence_refs=right.evidence_refs,
            corroborating_claim_id=right.claim_id,
            transitioned_at=LATER,
        )


def _second_source(source_id: str, *, owner: str, source_class: SourceClass = SourceClass.RPC, method: AccessMethod = AccessMethod.REST_API):
    return Source(
        source_id=source_id,
        source_class=source_class,
        canonical_name=source_id,
        owner_entity_ref=owner,
        locator=LocatorMetadata(base_locator=f"fixture://{source_id}", access_method=method, authentication="none"),
        authority_metadata=(AuthoritySeed(claim_family=ClaimFamily.CHAIN_ARCHITECTURE, tier=AuthorityTier.PRIMARY, valid_from=NOW - timedelta(days=1), policy_version="v1"),),
        verification_status=VerificationStatus.VERIFIED,
        verification_evidence_refs=(f"verification-{source_id}",),
        last_verified_at=NOW,
    )


def test_g2_same_owner_different_urls_are_not_independent() -> None:
    sources, authority, evidence, service, first = make_kernel()
    second = _second_source("csia:source:same-owner", owner="owner:a")
    sources.register(second)
    authority.register_source(second)
    left = add_claim(service, make_claim(service, evidence, first, "owner-left", content=b"left"))
    right = add_claim(service, make_claim(service, evidence, second, "owner-right", content=b"right"))
    with pytest.raises(ValueError, match="distinct owners"):
        ClaimStateEngine(service).transition(left.claim_id, ClaimState.CORROBORATED, triggering_evidence_refs=right.evidence_refs, corroborating_claim_id=right.claim_id, transitioned_at=LATER)


def test_g3_same_mechanism_or_narrative_copy_is_not_independent() -> None:
    sources, authority, evidence, service, first = make_kernel()
    second = _second_source("csia:source:same-mechanism", owner="owner:b", source_class=SourceClass.NATIVE_TECHNICAL, method=AccessMethod.DOCUMENT)
    sources.register(second)
    authority.register_source(second)
    left = add_claim(service, make_claim(service, evidence, first, "mechanism-left", content=b"left"))
    right = add_claim(service, make_claim(service, evidence, second, "mechanism-right", content=b"right"))
    with pytest.raises(ValueError, match="distinct mechanisms/providers"):
        ClaimStateEngine(service).transition(left.claim_id, ClaimState.CORROBORATED, triggering_evidence_refs=right.evidence_refs, corroborating_claim_id=right.claim_id, transitioned_at=LATER)


def test_g4_genuinely_independent_lines_may_corroborate() -> None:
    sources, authority, evidence, service, first = make_kernel()
    second = _second_source("csia:source:independent", owner="owner:b", source_class=SourceClass.RPC, method=AccessMethod.RPC)
    sources.register(second)
    authority.register_source(second)
    left = add_claim(service, make_claim(service, evidence, first, "independent-left", content=b"left"))
    right = add_claim(service, make_claim(service, evidence, second, "independent-right", content=b"right"))
    updated = ClaimStateEngine(service).transition(left.claim_id, ClaimState.CORROBORATED, triggering_evidence_refs=right.evidence_refs, corroborating_claim_id=right.claim_id, transitioned_at=LATER)
    assert updated.claim_state is ClaimState.CORROBORATED


def test_g5_narrative_copies_are_not_independent() -> None:
    sources, authority, evidence, service, first = make_kernel()
    second = _second_source("csia:source:copy", owner="owner:b", source_class=SourceClass.NEWS, method=AccessMethod.DOCUMENT)
    sources.register(second)
    authority.register_source(second)
    left = add_claim(service, make_claim(service, evidence, first, "copy-left", content=b"same-release"))
    right = add_claim(service, make_claim(service, evidence, second, "copy-right", content=b"same-release", evidence_tier=EvidenceTier.NARRATIVE))
    with pytest.raises(ValueError):
        ClaimStateEngine(service).transition(left.claim_id, ClaimState.CORROBORATED, triggering_evidence_refs=right.evidence_refs, corroborating_claim_id=right.claim_id, transitioned_at=LATER)


def test_h_authority_v10_must_not_lose_to_string_sorted_v9() -> None:
    source = Source(
        source_id="csia:source:ordering",
        source_class=SourceClass.NATIVE_TECHNICAL,
        canonical_name="ordering",
        locator=LocatorMetadata(base_locator="fixture://ordering", access_method=AccessMethod.DOCUMENT, authentication="none"),
        authority_metadata=(
            AuthoritySeed(claim_family=ClaimFamily.CHAIN_ARCHITECTURE, tier=AuthorityTier.PRIMARY, valid_from=NOW - timedelta(days=1), policy_version="v9"),
            AuthoritySeed(claim_family=ClaimFamily.CHAIN_ARCHITECTURE, tier=AuthorityTier.INSUFFICIENT, valid_from=NOW - timedelta(days=1), policy_version="v10"),
        ),
        verification_status=VerificationStatus.VERIFIED,
        verification_evidence_refs=("ordering-verification",),
        last_verified_at=NOW,
    )
    policy = AuthorityPolicy()
    policy.register_source(source)
    assert policy.resolve(source.source_id, ClaimFamily.CHAIN_ARCHITECTURE, NOW).tier is AuthorityTier.INSUFFICIENT


def test_i_overlapping_authority_assignments_are_rejected_as_ambiguous() -> None:
    source = Source(
        source_id="csia:source:overlap",
        source_class=SourceClass.NATIVE_TECHNICAL,
        canonical_name="overlap",
        locator=LocatorMetadata(base_locator="fixture://overlap", access_method=AccessMethod.DOCUMENT, authentication="none"),
        authority_metadata=(AuthoritySeed(claim_family=ClaimFamily.CHAIN_ARCHITECTURE, tier=AuthorityTier.PRIMARY, valid_from=NOW - timedelta(days=1), policy_version="v1"),),
        verification_status=VerificationStatus.VERIFIED,
        verification_evidence_refs=("overlap-verification",),
        last_verified_at=NOW,
    )
    policy = AuthorityPolicy()
    policy.register_source(source)
    policy.assign(source_id=source.source_id, claim_family=ClaimFamily.CHAIN_ARCHITECTURE, tier=AuthorityTier.INSUFFICIENT, valid_from=NOW - timedelta(days=1), valid_to=None, policy_version="v2")
    with pytest.raises(ValueError):
        policy.resolve(source.source_id, ClaimFamily.CHAIN_ARCHITECTURE, NOW)


def test_j_fake_source_update_evidence_is_rejected() -> None:
    coordinator_type = getattr(sources_module, "SourceEvidenceCoordinator", None)
    assert coordinator_type is not None
    sources, _, evidence, _, source = make_kernel()
    coordinator = coordinator_type(source_registry=sources, evidence_store=evidence)
    with pytest.raises(KeyError):
        coordinator.update_locator(source.source_id, locator=source.locator, verification_evidence_refs=("csia:evidence:fake",), at=LATER)


def test_k_book2_claim_binding_projection_keeps_book1_frozen() -> None:
    projection_type = getattr(claims_module, "Book2ClaimBinding", None)
    assert projection_type is not None
    _, _, _, service, source = make_kernel()
    claim = add_claim(service, make_claim(service, service.evidence_store, source, "projection", content=b"projection"))
    binding = projection_type.from_claim(claim)
    assert binding.book2_claim_state is claim.claim_state
    assert binding.book1.claim_id == claim.claim_id
    assert set(RecordLifecycle) == {
        RecordLifecycle.DECLARED,
        RecordLifecycle.OBSERVED,
        RecordLifecycle.VERIFIED,
        RecordLifecycle.CONTESTED,
        RecordLifecycle.REJECTED,
    }
