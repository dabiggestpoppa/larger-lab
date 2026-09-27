"""Book 4 fail-closed audit — every admission/classification path must refuse
untyped or drifted payloads with ``Book4ProvenanceError`` instead of crashing.

Attack surface (pydantic ``model_copy(update=...)`` bypasses every model
validator, so decision points must type-check record- and binding-supplied
payloads themselves):

- raw dict records injected into each Book admission method
- raw dict / drifted bindings injected into classify paths
- non-string and unhashable claim/snapshot refs reaching provenance
  validation (set/dict operations and ``ClaimStore.require`` must never see
  them)
- fact bindings whose ``fact`` drifted outside the canonical enum
- records whose structural invariants (affected systems) were stripped
"""

from __future__ import annotations

import pytest

from crypto_systems_intelligence_atlas.book4_test_support import (
    hard_evidence,
    kernel,
    path,
    record,
    redundancy,
    role,
    substitutability,
)
from crypto_systems_intelligence_atlas.dependency import (
    DependencyBook,
    HardRuntimeGate,
    RuntimeScope,
)
from crypto_systems_intelligence_atlas.dependency_paths import DependencyPathBook
from crypto_systems_intelligence_atlas.dependency_provenance import Book4ProvenanceError
from crypto_systems_intelligence_atlas.failure_domains import (
    FailureDomainBook,
    IndependenceClaimBinding,
)
from crypto_systems_intelligence_atlas.protocol_roles import ProtocolRole, ProtocolRoleBook
from crypto_systems_intelligence_atlas.redundancy import RedundancyBook
from crypto_systems_intelligence_atlas.substitutability import SubstitutabilityBook


@pytest.fixture()
def env():
    claims, evidence, provenance = kernel()
    return claims, evidence, provenance


# ---------------------------------------------------------------- raw records


def test_dependency_book_refuses_raw_dict_record(env) -> None:
    _, _, provenance = env
    with pytest.raises(Book4ProvenanceError, match="typed DependencyRecord"):
        DependencyBook(provenance).add({"dependency_id": "hostile"})


def test_path_book_refuses_raw_dict_record(env) -> None:
    _, _, provenance = env
    with pytest.raises(Book4ProvenanceError, match="typed DependencyPath"):
        DependencyPathBook(provenance).add({"path_id": "hostile"})


def test_role_book_refuses_raw_dict_record(env) -> None:
    _, _, provenance = env
    with pytest.raises(Book4ProvenanceError, match="typed RoleAssignment"):
        ProtocolRoleBook(provenance).add({"role_assignment_id": "hostile"})


def test_substitutability_book_refuses_raw_dict_record(env) -> None:
    _, _, provenance = env
    with pytest.raises(Book4ProvenanceError, match="typed SubstitutabilityAssessment"):
        SubstitutabilityBook(provenance).add({"assessment_id": "hostile"})


def test_redundancy_book_refuses_raw_dict_record(env) -> None:
    _, _, provenance = env
    with pytest.raises(Book4ProvenanceError, match="typed RedundancyAssessment"):
        RedundancyBook(provenance, FailureDomainBook(provenance)).add(
            {"redundancy_id": "hostile"}
        )


def test_failure_domain_book_refuses_raw_dict_record(env) -> None:
    _, _, provenance = env
    with pytest.raises(Book4ProvenanceError, match="typed FailureDomain"):
        FailureDomainBook(provenance).add({"domain_id": "hostile"})


def test_hard_runtime_gate_refuses_raw_evidence_record(env) -> None:
    _, _, provenance = env
    with pytest.raises(Book4ProvenanceError, match="typed HardRuntimeEvidence"):
        HardRuntimeGate(provenance).classify({"consumer_ref": "hostile"})


# ------------------------------------------------- provenance chokepoint types


def test_provenance_refuses_non_string_claim_refs(env) -> None:
    _, _, provenance = env
    book = DependencyBook(provenance)
    drifted = record("probe-refs-tuple").model_copy(
        update={"book2_claim_refs": (("claim-ok",),)}
    )
    with pytest.raises(Book4ProvenanceError, match="canonical string references"):
        book.add(drifted)


def test_provenance_refuses_unhashable_claim_refs(env) -> None:
    _, _, provenance = env
    book = DependencyBook(provenance)
    drifted = record("probe-refs-dict").model_copy(
        update={"book2_claim_refs": ("claim-ok", {"forged": "claim"})}
    )
    with pytest.raises(Book4ProvenanceError, match="canonical string references"):
        book.add(drifted)


def test_provenance_refuses_non_string_snapshot_refs(env) -> None:
    _, _, provenance = env
    book = DependencyBook(provenance)
    drifted = record("probe-snapshots").model_copy(
        update={"source_snapshot_refs": ("snapshot://book4/evidence", {"snap": 1})}
    )
    with pytest.raises(Book4ProvenanceError, match="canonical string references"):
        book.add(drifted)


def test_provenance_refuses_non_string_claim_id_in_resolve(env) -> None:
    _, _, provenance = env
    with pytest.raises(Book4ProvenanceError, match="canonical string references"):
        provenance.resolve_claim(42)  # type: ignore[arg-type]


def test_provenance_snapshot_lineage_refuses_bad_claim_ref_types(env) -> None:
    _, _, provenance = env
    with pytest.raises(Book4ProvenanceError, match="canonical string references"):
        provenance.validate_snapshot_lineage(({"claim": 1},), ("snapshot://book4/evidence",))


# ----------------------------------------------- model_copy drifted payloads


def test_drifted_book2_claim_refs_refused_by_role_book(env) -> None:
    _, _, provenance = env
    book = ProtocolRoleBook(provenance)
    drifted = role("probe-role", ProtocolRole.SEQUENCER).model_copy(
        update={"book2_claim_refs": ("claim-ok", {"forged": "claim"})}
    )
    with pytest.raises(Book4ProvenanceError, match="canonical string references"):
        book.add(drifted)


def test_drifted_book2_claim_refs_refused_by_substitutability_book(env) -> None:
    _, _, provenance = env
    book = SubstitutabilityBook(provenance)
    drifted = substitutability("probe-sub", "fixture:incumbent", "fixture:candidate").model_copy(
        update={"book2_claim_refs": ("claim-ok", ("nested",))}
    )
    with pytest.raises(Book4ProvenanceError, match="canonical string references"):
        book.add(drifted)


def test_drifted_book2_claim_refs_refused_by_redundancy_book(env) -> None:
    _, _, provenance = env
    book = RedundancyBook(provenance, FailureDomainBook(provenance))
    drifted = redundancy("probe-red").model_copy(
        update={"book2_claim_refs": ({"forged": "claim"},)}
    )
    with pytest.raises(Book4ProvenanceError, match="canonical string references"):
        book.add(drifted)


# ------------------------------------------------------- HardRuntimeGate facts


def test_hard_runtime_gate_fact_drift_outside_enum_fails_closed(env) -> None:
    """A binding whose fact drifted outside HardRuntimeFact must produce a
    refusal reason, never crash on set insertion or .value reads."""
    _, _, provenance = env
    base = hard_evidence()
    drifted_binding = base.fact_bindings[0].model_copy(update={"fact": "NOT_A_FACT"})
    drifted = base.model_copy(update={"fact_bindings": (drifted_binding,)})
    result = HardRuntimeGate(provenance).classify(drifted)
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME
    assert any("canonical HardRuntimeFact" in reason for reason in result.reasons)


def test_hard_runtime_gate_unhashable_fact_payload_fails_closed(env) -> None:
    _, _, provenance = env
    base = hard_evidence()
    drifted_binding = base.fact_bindings[0].model_copy(update={"fact": {"forged": True}})
    drifted = base.model_copy(update={"fact_bindings": (drifted_binding,)})
    result = HardRuntimeGate(provenance).classify(drifted)
    assert result.runtime_scope is not RuntimeScope.HARD_RUNTIME


# ------------------------------------------------- failure-domain classify


def test_failure_domain_classify_refuses_raw_dict_binding(env) -> None:
    _, _, provenance = env
    book = FailureDomainBook(provenance)
    from crypto_systems_intelligence_atlas.book4_test_support import failure_domain

    left = book.add(failure_domain("probe-left", provider="a", evidence_ref="mechanism-a"))
    right = book.add(failure_domain("probe-right", provider="b", evidence_ref="mechanism-b"))
    with pytest.raises(Book4ProvenanceError, match="typed IndependenceClaimBinding"):
        book.classify(
            left,
            right,
            positive_independence_claim_refs=("some-claim",),
            independence_bindings=({"claim_ref": "some-claim"},),
        )


def test_failure_domain_classify_drifted_extra_system_unknown_not_crash(env) -> None:
    """An extra unbound affected system yields UNKNOWN, never an IndexError or
    a silent ride on single-pair evidence."""
    _, _, provenance = env
    book = FailureDomainBook(provenance)
    from crypto_systems_intelligence_atlas.book4_test_support import (
        CLAIM_REF,
        add_pair_independence_claim,
        failure_domain,
    )
    from crypto_systems_intelligence_atlas.redundancy import RedundancyState  # noqa: F401

    claims, evidence_store, _ = kernel()
    left = book.add(failure_domain("probe-drift-left", provider="a", evidence_ref="mechanism-a"))
    right = book.add(failure_domain("probe-drift-right", provider="b", evidence_ref="mechanism-b"))
    claim_ref = add_pair_independence_claim(
        claims,
        evidence_store,
        left_system=left.affected_system_refs[0],
        right_system=right.affected_system_refs[0],
    )
    binding = IndependenceClaimBinding(
        claim_ref=claim_ref,
        left_domain_ref=left.domain_id,
        right_domain_ref=right.domain_id,
        left_system_ref=left.affected_system_refs[0],
        right_system_ref=right.affected_system_refs[0],
        correlation_scope=left.correlation_scope,
    )
    drifted_left = left.model_copy(
        update={
            "affected_system_refs": (
                left.affected_system_refs[0],
                "fixture:unbound-system",
            ),
            "book2_claim_refs": (CLAIM_REF, claim_ref),
        }
    )
    result = book.classify(
        drifted_left,
        right,
        positive_independence_claim_refs=(claim_ref,),
        independence_bindings=(binding,),
    )
    from crypto_systems_intelligence_atlas.failure_domains import (
        FailureDomainClassification,
    )

    assert result.classification is FailureDomainClassification.UNKNOWN


def test_failure_domain_classify_empty_affected_systems_fails_closed(env) -> None:
    """A record whose affected-system tuple was stripped via model_copy must
    be refused closed, never crash with IndexError."""
    _, _, provenance = env
    book = FailureDomainBook(provenance)
    from crypto_systems_intelligence_atlas.book4_test_support import failure_domain

    left = book.add(failure_domain("probe-empty-left", provider="a", evidence_ref="mechanism-a"))
    right = book.add(failure_domain("probe-empty-right", provider="b", evidence_ref="mechanism-b"))
    stripped = left.model_copy(update={"affected_system_refs": ()})
    with pytest.raises(Book4ProvenanceError, match="affected system"):
        book.classify(stripped, right)


def test_path_book_and_dependency_book_still_accept_valid_records(env) -> None:
    _, _, provenance = env
    dependency_book = DependencyBook(provenance)
    dependency_book.add(record("probe-valid-record"))
    from crypto_systems_intelligence_atlas.dependency_paths import DependencyPathBook

    DependencyPathBook(provenance).add(path("probe-valid-path"))
