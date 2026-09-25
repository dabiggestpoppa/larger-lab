"""Book 4 substitutability, protocol roles, infrastructure context, and boundary tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book4_test_support import context, kernel, role, substitutability
from crypto_systems_intelligence_atlas.book4 import assert_book4_technical_scope
from crypto_systems_intelligence_atlas.infrastructure_context import InfrastructureContextBook
from crypto_systems_intelligence_atlas.protocol_roles import (
    ProtocolRole,
    ProtocolRoleBook,
    RoleState,
)
from crypto_systems_intelligence_atlas.substitutability import (
    SubstitutabilityBook,
    SubstitutabilityDirection,
)


@pytest.mark.parametrize(
    ("assessment_id", "incumbent", "candidate"),
    [
        ("oracle-feed", "oracle-a", "oracle-b"),
        ("rpc-provider", "rpc-a", "rpc-b"),
        ("indexer", "indexer-a", "indexer-b"),
        ("da", "da-a", "da-b"),
        ("bridge", "bridge-a", "bridge-b"),
        ("messaging", "messenger-a", "messenger-b"),
        ("sequencer", "sequencer-a", "sequencer-b"),
        ("sdk", "sdk-a", "sdk-b"),
        ("validator", "validator-a", "validator-b"),
        ("canonical-bridge", "canonical-a", "canonical-b"),
        ("relayer", "relayer-a", "relayer-b"),
    ],
)
def test_substitutability_is_directional_and_scoped(
    assessment_id: str, incumbent: str, candidate: str
) -> None:
    _, _, provenance = kernel()
    book = SubstitutabilityBook(provenance)
    item = book.add(substitutability(assessment_id, incumbent, candidate))
    assert item.direction is SubstitutabilityDirection.INCUMBENT_TO_CANDIDATE
    assert book.applies(assessment_id) == (incumbent, candidate)
    assert not hasattr(book, "reverse_relation")
    assert item.context == "production read path"


def test_reverse_assessment_does_not_imply_forward_assessment() -> None:
    _, _, provenance = kernel()
    book = SubstitutabilityBook(provenance)
    forward = book.add(substitutability("forward", "a", "b"))
    reverse = book.add(
        substitutability(
            "reverse",
            "a",
            "b",
            direction=SubstitutabilityDirection.CANDIDATE_TO_INCUMBENT,
        )
    )
    assert forward is not reverse
    assert forward.direction is not reverse.direction


def test_role_book_is_multivalued_and_scoped() -> None:
    _, _, provenance = kernel()
    book = ProtocolRoleBook(provenance)
    book.add(role("role-sequencer", ProtocolRole.SEQUENCER))
    book.add(role("role-da", ProtocolRole.DA_PROVIDER))
    assert len(book.for_system("fixture:system")) == 2


def test_role_state_is_domain_only_not_book2_claim_state() -> None:
    assert {item.value for item in RoleState} == {
        "CURRENT",
        "HISTORICAL",
        "DECLARED_ONLY",
        "UNKNOWN",
    }
    assert "VERIFIED" not in {item.value for item in RoleState}


def test_all_ratified_role_families_are_supported() -> None:
    required = {
        "ORACLE_NETWORK", "DATA_PUBLISHER", "DATA_SOURCE", "FEED", "PRICE_FEED",
        "ATTESTATION_SERVICE", "DELIVERY_LAYER", "AUTOMATION_SERVICE",
        "MESSAGING_SERVICE", "FALLBACK_SOURCE", "MESSAGE_TRANSPORT", "ASSET_BRIDGE",
        "CANONICAL_BRIDGE", "LIGHT_CLIENT_VERIFIER", "VALIDATOR_VERIFIER",
        "GUARDIAN_VERIFIER", "ORACLE_ASSISTED_VERIFIER", "LOCK_MINT", "BURN_MINT",
        "LIQUIDITY_BRIDGE", "INTENT_BASED_TRANSFER", "CHAIN_NATIVE_INTEROPERABILITY",
        "RELAYER_LAYER", "ENDPOINT", "CHANNEL", "ROUTE", "DA_NETWORK", "DA_PROVIDER",
        "BLOB_DATA_PUBLICATION", "SAMPLING_AVAILABILITY_MECHANISM", "RETRIEVAL_SERVICE",
        "SEQUENCER", "SETTLEMENT_LAYER", "SECURITY_PROVIDER", "FALLBACK_DA",
        "RPC_PROVIDER", "NODE_INFRASTRUCTURE", "INDEXER", "DATA_API", "SDK",
        "FRAMEWORK", "DEVELOPER_TOOL", "WALLET_INFRASTRUCTURE", "EXPLORER",
        "OPERATIONAL_PROVIDER", "HOSTED_SERVICE",
    }
    assert {item.value for item in ProtocolRole} == required


def test_infrastructure_context_rejects_book5_fields() -> None:
    with pytest.raises(ValidationError, match="Book 5"):
        context().model_copy(update={"function": "total value locked calculation"}).model_validate(
            {**context().model_dump(), "function": "total value locked calculation"}
        )


def test_infrastructure_context_book_validates_provenance() -> None:
    _, _, provenance = kernel()
    assert InfrastructureContextBook(provenance).add(context()) is not None


@pytest.mark.parametrize(
    "claim",
    [
        "capital routing through the bridge",
        "liquidity depth for the pool",
        "collateral value at liquidation",
        "stablecoin supply expansion",
        "staking economics determine yield",
    ],
)
def test_book4_scope_guard_rejects_capital_claims(claim: str) -> None:
    with pytest.raises(ValueError, match="Book 5"):
        assert_book4_technical_scope(claim)
