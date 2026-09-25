"""The 17 ratified Book 4 adversarial tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book4_test_support import kernel, path, record, role
from crypto_systems_intelligence_atlas.architecture_relations import ArchitectureRelationType
from crypto_systems_intelligence_atlas.book4 import assert_book4_technical_scope
from crypto_systems_intelligence_atlas.dependency import (
    DependencyBook,
    DependencyClass,
    DependencyStrengthState,
    RuntimeScope,
)
from crypto_systems_intelligence_atlas.dependency_paths import DependencyPathBook
from crypto_systems_intelligence_atlas.dependency_relations import Book4RelationProjector
from crypto_systems_intelligence_atlas.protocol_roles import ProtocolRole
from crypto_systems_intelligence_atlas.relationships import EdgeType


def test_01_integrates_with_does_not_imply_depends_on() -> None:
    item = record("integrated", relation=EdgeType.INTEGRATES_WITH, strength=DependencyStrengthState.OPTIONAL)
    assert item.relation_basis is EdgeType.INTEGRATES_WITH
    assert item.relation_basis is not EdgeType.DEPENDS_ON


def test_02_depends_on_does_not_imply_hard_runtime() -> None:
    with pytest.raises(ValidationError, match="cannot establish HARD_RUNTIME"):
        record("hard-depends", relation=EdgeType.DEPENDS_ON, runtime_scope=RuntimeScope.HARD_RUNTIME)


def test_03_built_with_does_not_imply_runtime_dependency() -> None:
    item = record(
        "sdk-build",
        relation=EdgeType.BUILT_WITH,
        runtime_scope=RuntimeScope.BUILD_TIME,
        strength=DependencyStrengthState.REQUIRED,
    )
    assert item.runtime_scope is RuntimeScope.BUILD_TIME
    assert item.dependency_class is DependencyClass.DIRECT_RUNTIME


def test_04_oracle_for_does_not_imply_single_source_dependency() -> None:
    _, _, provenance = kernel()
    book = DependencyBook(provenance)
    first = record("oracle-a", relation=EdgeType.ORACLE_FOR)
    second = record("oracle-b", relation=EdgeType.ORACLE_FOR)
    first = first.model_copy(update={"subject_ref": "fixture:consumer", "object_ref": "fixture:oracle-a"})
    second = second.model_copy(update={"subject_ref": "fixture:consumer", "object_ref": "fixture:oracle-b"})
    book.add(first)
    book.add(second)
    assert len(book.all_records()) == 2


def test_05_messages_to_does_not_imply_asset_bridge() -> None:
    _, _, provenance = kernel()
    projection = Book4RelationProjector().project(record("message", relation=EdgeType.MESSAGES_TO))
    assert projection.relation_type is EdgeType.MESSAGES_TO
    assert role("role-messenger", ProtocolRole.MESSAGING_SERVICE).role_type is ProtocolRole.MESSAGING_SERVICE


def test_06_bridges_to_does_not_imply_settlement() -> None:
    projection = Book4RelationProjector().project(record("bridge", relation=EdgeType.BRIDGES_TO))
    assert projection.relation_type is EdgeType.BRIDGES_TO
    assert projection.relation_type is not EdgeType.SETTLES_TO


def test_07_uses_da_does_not_imply_secured_by() -> None:
    _, _, provenance = kernel()
    item = record("da", relation=ArchitectureRelationType.USES_DA)
    projection = Book4RelationProjector().project(item)
    assert projection.target_book == "BOOK_3"
    assert projection.relation_type is ArchitectureRelationType.USES_DA
    assert projection.relation_type is not EdgeType.SECURED_BY


def test_08_multiple_providers_do_not_imply_independent_redundancy() -> None:
    from crypto_systems_intelligence_atlas.book4_test_support import redundancy

    item = redundancy("multi-provider")
    assert len(item.provider_refs) == 2
    assert item.state.value == "UNKNOWN"
    assert not item.positive_independence_evidence_refs


def test_09_same_provider_does_not_automatically_imply_one_failure_domain() -> None:
    from crypto_systems_intelligence_atlas.book4_test_support import failure_domain
    from crypto_systems_intelligence_atlas.failure_domains import FailureDomainBook, FailureDomainClassification

    _, _, provenance = kernel()
    book = FailureDomainBook(provenance)
    left = book.add(failure_domain("left", provider="same-brand", evidence_ref="backend-a"))
    right = book.add(failure_domain("right", provider="same-brand", evidence_ref="backend-b"))
    assert book.classify(left, right).classification is FailureDomainClassification.PARTIAL_SHARED_DOMAIN


def test_10_transitive_dependency_preserves_full_path_provenance() -> None:
    _, _, provenance = kernel()
    book = DependencyPathBook(provenance)
    item = book.add(path())
    derived = book.derive_transitive(item.path_id)
    assert derived.ordered_path == item.ordered_nodes
    assert derived.source_path_id == item.path_id
    assert derived.authoritative is False


def test_11_substitutability_is_directional() -> None:
    from crypto_systems_intelligence_atlas.book4_test_support import substitutability
    from crypto_systems_intelligence_atlas.substitutability import SubstitutabilityBook

    _, _, provenance = kernel()
    book = SubstitutabilityBook(provenance)
    item = book.add(substitutability("directional", "a", "b"))
    assert book.applies(item.assessment_id) == ("a", "b")
    assert ("b", "a") not in [book.applies(item.assessment_id)]


def test_12_canonical_bridge_is_not_third_party_bridge() -> None:
    canonical = role("canonical", ProtocolRole.CANONICAL_BRIDGE, system_ref="fixture:canonical-bridge")
    third_party = role("third-party", ProtocolRole.ASSET_BRIDGE, system_ref="fixture:third-party-bridge")
    assert canonical.role_type is not third_party.role_type
    assert canonical.system_ref != third_party.system_ref


def test_13_ibc_messaging_is_not_generic_bridge_semantics() -> None:
    ibc = role("ibc", ProtocolRole.CHAIN_NATIVE_INTEROPERABILITY)
    generic = role("generic", ProtocolRole.MESSAGE_TRANSPORT)
    assert ibc.role_type is not generic.role_type
    assert ibc.function == "serve scoped protocol function"


def test_14_rpc_dependency_is_not_protocol_consensus_dependency() -> None:
    rpc = record("rpc", relation=EdgeType.DEPENDS_ON)
    rpc = rpc.model_copy(update={"function": "read chain state", "object_ref": "fixture:rpc-provider"})
    assert rpc.subject_ref != "fixture:protocol-consensus"
    assert rpc.relation_basis is not EdgeType.SECURED_BY


def test_15_shared_sdk_is_not_shared_runtime_failure_domain() -> None:
    sdk = record(
        "shared-sdk",
        relation=EdgeType.BUILT_WITH,
        runtime_scope=RuntimeScope.BUILD_TIME,
        strength=DependencyStrengthState.REQUIRED,
    )
    assert sdk.runtime_scope is RuntimeScope.BUILD_TIME
    assert not hasattr(sdk, "failure_domain_id")


def test_16_token_identity_is_not_infrastructure_role_identity() -> None:
    assignment = role("rpc-role", ProtocolRole.RPC_PROVIDER, system_ref="fixture:rpc-provider")
    assert assignment.system_ref == "fixture:rpc-provider"
    with pytest.raises(ValidationError):
        role("invalid", ProtocolRole.RPC_PROVIDER).model_copy(
            update={"token_identity": "fixture:token"}
        ).model_validate({**role("invalid", ProtocolRole.RPC_PROVIDER).model_dump(), "token_identity": "fixture:token"})


def test_17_book5_capital_claims_cannot_enter_book4() -> None:
    with pytest.raises(ValueError, match="Book 5"):
        assert_book4_technical_scope("capital routing and liquidity depth")


@pytest.mark.parametrize(
    "name",
    ["VERIFIED_BY", "RELAYED_BY", "USES_ENDPOINT", "USES_RELAYER", "TRANSPORTS_FOR", "ROUTE_DEPENDS_ON"],
)
def test_unratified_relation_additions_fail_closed(name: str) -> None:
    with pytest.raises(ValueError, match="operator stop"):
        Book4RelationProjector().ensure_no_forbidden_addition(name)
