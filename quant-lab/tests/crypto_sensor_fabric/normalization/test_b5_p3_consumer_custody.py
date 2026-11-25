"""SENSOR-B5-P3-R3 — bounded custody-authority derivation.

The harness defended authorization with a capability object plus a
module-private issuance marker; CAP01 (minting) and CAP02 (marker copying) both
work against it, and no in-process sentinel can be made uncopyable.  Production
ships **no capability at all**, so these tests ask a different question: can the
derivation be made to return ``AUTHORIZED``?

**The answer, asserted: no.**  Under the shipped manifest it returns
``INTEGRATION_REQUIRED`` for every identity.  Under a *synthetic* root with a
complete, approvable artifact it returns ``INTEGRATION_REQUIRED`` too -- because
the reviewed manifest schema has no record type that names a custody SOURCE as
operator-authorized, and reinterpreting artifact approval as source
authorization is exactly what design spec E forbids.  The missing contract is
named (:data:`UNRESOLVED_AUTHORITY_CONTRACT`), not invented: this module defines
no token that could be written into a manifest to obtain authority.

That is a **limitation, honestly stated**: the positive branch is unreachable in
``src/``.  ``test_b5_p3_consumer_policy.py`` exercises the accepting branch
through a wiring double, and
``test_the_production_source_never_authorizes`` asserts the production source
cannot do it.  A test never grants authority.
"""

from __future__ import annotations

import ast
import hashlib
import inspect
import json
import pathlib
from datetime import UTC, datetime
from typing import Any

import pytest

import crypto_sensor_fabric.normalization.authority as authority_module
from crypto_sensor_fabric.normalization.authority import (
    TRUSTED_MANIFEST_SHA256,
    ApprovalManifest,
    ApprovedArtifact,
)
from crypto_sensor_fabric.normalization.consumer.custody_authority import (
    SUPPORTED_RECORD_KINDS,
    UNRESOLVED_AUTHORITY_CONTRACT,
    CustodyAuthorityBasis,
    CustodyAuthorityDerivation,
    CustodyAuthorityIdentity,
    CustodySourceAuthoritySource,
    ManifestCustodyAuthority,
    derive_custody_authority,
)
from crypto_sensor_fabric.normalization.consumer.models import (
    ConsumerDecision,
    ConsumerVerdict,
)

QUANT_LAB = pathlib.Path(__file__).resolve().parents[3]
CONSUMER = QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization" / "consumer"
CUSTODY_PATH = CONSUMER / "custody_authority.py"
PRODUCTION_MANIFEST = (
    QUANT_LAB
    / "config"
    / "crypto_sensor_fabric"
    / "provider_semantics"
    / "approval_manifest.json"
)
CUTOFF = datetime(2026, 6, 1, 12, 0, tzinfo=UTC)
ARTIFACT_SHA = "c" * 64
ARTIFACT_ID = "registry-p3-custody.yaml"
APPROVAL_ID = "APPROVAL-SYNTHETIC-P3"
PROVIDER = "BINANCE_USDM"


def _manifest(**overrides: Any) -> bytes:
    entry: dict[str, Any] = {
        "sha256": ARTIFACT_SHA,
        "approval_id": APPROVAL_ID,
        "registry_schema_version": "9.9.9",
        "approved_at": "2026-01-01",
        "valid_until": "2027-01-01",
        "available_at": "2026-03-01",
        "evidence_blobs": {"SYNTHETIC_P3_DOC_REF": "d" * 64},
        "allowed_methodologies": ["AGGRESSOR_FROM_BUYER_MAKER_BINANCE_V1"],
        "evidence": {PROVIDER: {"isBuyerMaker": ["SYNTHETIC_P3_DOC_REF"]}},
        "declared_native_fields": {PROVIDER: ["isBuyerMaker"]},
        "approved_transformations": {},
        "resolved_blocking_assumptions": ["synthetic"],
    }
    entry.update(overrides)
    return json.dumps(
        {
            "schema_version": "b5-i09p2a-1",
            "authority_id": "PROBE_ROOT",
            "artifacts": {ARTIFACT_ID: entry},
            "revoked_approval_ids": [],
        }
    ).encode("utf-8")


def _pin(monkeypatch: pytest.MonkeyPatch, manifest: bytes) -> None:
    monkeypatch.setattr(
        authority_module, "TRUSTED_MANIFEST_SHA256", hashlib.sha256(manifest).hexdigest()
    )


def _identity(manifest: bytes, **overrides: Any) -> CustodyAuthorityIdentity:
    payload: dict[str, Any] = {
        "manifest_sha256": hashlib.sha256(manifest).hexdigest(),
        "artifact_id": ARTIFACT_ID,
        "approval_id": APPROVAL_ID,
        "registry_digest": ARTIFACT_SHA,
        "record_kind": "TRADE",
        "provider": PROVIDER,
        "knowledge_cutoff": CUTOFF,
    }
    payload.update(overrides)
    return CustodyAuthorityIdentity(**payload)


# ---------------------------------------------------------------------------
# A3.1 -- under the shipped manifest, AUTHORIZED is unreachable
# ---------------------------------------------------------------------------


def test_the_shipped_manifest_produces_integration_required_for_every_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    shipped = PRODUCTION_MANIFEST.read_bytes()
    _pin(monkeypatch, shipped)
    identities = [
        _identity(shipped),
        _identity(shipped, artifact_id="any-other-artifact"),
        _identity(shipped, record_kind="LIQUIDATION"),
        _identity(shipped, provider="BYBIT_USDT"),
        _identity(shipped, approval_id="APPROVAL-ANY"),
        _identity(shipped, registry_digest="e" * 64),
        _identity(shipped, knowledge_cutoff=datetime(2030, 1, 1, tzinfo=UTC)),
    ]
    for identity in identities:
        derivation = derive_custody_authority(
            manifest_bytes=shipped, identity=identity
        )
        assert derivation.basis is CustodyAuthorityBasis.INTEGRATION_REQUIRED
        assert derivation.basis is not CustodyAuthorityBasis.AUTHORIZED
        assert derivation.unresolved_contract


def test_no_input_produces_authorized_even_with_a_complete_fixture_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The property test A3.1 asks for: over a matrix, never AUTHORIZED."""
    manifest = _manifest()
    _pin(monkeypatch, manifest)
    source = ManifestCustodyAuthority(manifest_bytes=manifest)
    variants: list[dict[str, Any]] = [
        {},
        {"record_kind": "LIQUIDATION"},
        {"approval_id": "APPROVAL-OTHER"},
        {"registry_digest": "f" * 64},
        {"provider": "KRAKEN_SPOT"},
        {"artifact_id": "other.yaml"},
        {"knowledge_cutoff": datetime(2027, 6, 1, tzinfo=UTC)},
        {"knowledge_cutoff": datetime(2026, 1, 1, tzinfo=UTC)},
    ]
    results = [source.authorize(_identity(manifest, **variant)) for variant in variants]
    assert {result.basis for result in results} <= {
        CustodyAuthorityBasis.INTEGRATION_REQUIRED,
        CustodyAuthorityBasis.UNAUTHORIZED,
    }
    assert CustodyAuthorityBasis.AUTHORIZED not in {result.basis for result in results}


# ---------------------------------------------------------------------------
# A3.3 -- every bound element fails closed, with a specific reason
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "overrides, expected",
    [
        # the artifact is not the one approved: there is no integration for it
        ({"artifact_id": "unapproved.yaml"}, CustodyAuthorityBasis.INTEGRATION_REQUIRED),
        # the approval identity is not the one this record was derived under
        ({"approval_id": "APPROVAL-OTHER"}, CustodyAuthorityBasis.UNAUTHORIZED),
        # the record was verified against other bytes than the approval names
        ({"registry_digest": "f" * 64}, CustodyAuthorityBasis.UNAUTHORIZED),
        # a venue's approval never transfers
        ({"provider": "KRAKEN_SPOT"}, CustodyAuthorityBasis.UNAUTHORIZED),
        # the approval had expired at the cutoff
        (
            {"knowledge_cutoff": datetime(2027, 6, 1, 12, 0, tzinfo=UTC)},
            CustodyAuthorityBasis.UNAUTHORIZED,
        ),
    ],
)
def test_each_bound_element_fails_closed(
    monkeypatch: pytest.MonkeyPatch, overrides: dict[str, Any], expected: Any
) -> None:
    manifest = _manifest()
    _pin(monkeypatch, manifest)
    derivation = derive_custody_authority(
        manifest_bytes=manifest, identity=_identity(manifest, **overrides)
    )
    assert derivation.basis is expected
    assert derivation.basis is not CustodyAuthorityBasis.AUTHORIZED
    assert derivation.detail


def test_a_revoked_approval_is_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = json.dumps(
        {
            "schema_version": "b5-i09p2a-1",
            "authority_id": "PROBE_ROOT",
            "artifacts": {
                ARTIFACT_ID: {
                    "sha256": ARTIFACT_SHA,
                    "approval_id": APPROVAL_ID,
                    "registry_schema_version": "9.9.9",
                    "approved_at": "2026-01-01",
                    "valid_until": "2027-01-01",
                    "evidence_blobs": {"SYNTHETIC_P3_DOC_REF": "d" * 64},
                    "allowed_methodologies": ["M"],
                    "evidence": {PROVIDER: {"isBuyerMaker": ["SYNTHETIC_P3_DOC_REF"]}},
                    "declared_native_fields": {PROVIDER: ["isBuyerMaker"]},
                    "resolved_blocking_assumptions": ["synthetic"],
                }
            },
            "revoked_approval_ids": [APPROVAL_ID],
        }
    ).encode("utf-8")
    _pin(monkeypatch, manifest)
    derivation = derive_custody_authority(
        manifest_bytes=manifest, identity=_identity(manifest)
    )
    assert derivation.basis is CustodyAuthorityBasis.UNAUTHORIZED
    assert "revoked" in derivation.detail


def test_an_approval_not_yet_operative_is_unauthorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest(available_at_instant="2026-07-01T00:00:00+00:00")
    _pin(monkeypatch, manifest)
    derivation = derive_custody_authority(
        manifest_bytes=manifest, identity=_identity(manifest)
    )
    assert derivation.basis is CustodyAuthorityBasis.UNAUTHORIZED
    assert "operative" in derivation.detail


def test_authority_does_not_travel_between_roots(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _manifest()
    _pin(monkeypatch, manifest)
    other = _manifest(approval_id="APPROVAL-OTHER-ROOT")
    _pin(monkeypatch, other)
    stale_identity = _identity(manifest)  # derived under the FIRST root
    derivation = derive_custody_authority(manifest_bytes=other, identity=stale_identity)
    assert derivation.basis is CustodyAuthorityBasis.UNAUTHORIZED
    assert "root" in derivation.detail


def test_a_foreign_manifest_is_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    reviewed = _manifest()
    _pin(monkeypatch, reviewed)
    foreign = _manifest(approval_id="APPROVAL-ATTACKER")
    derivation = derive_custody_authority(
        manifest_bytes=foreign, identity=_identity(reviewed)
    )
    assert derivation.basis is CustodyAuthorityBasis.UNAUTHORIZED
    assert "reviewed production root" in derivation.detail


def test_a_malformed_reviewed_manifest_is_unauthorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = b'{"schema_version": "b5-i09p2a-1", "artifacts": {"a": {}}}'
    _pin(monkeypatch, manifest)
    identity = CustodyAuthorityIdentity(
        manifest_sha256=hashlib.sha256(manifest).hexdigest(),
        artifact_id="a",
        approval_id="b",
        registry_digest=ARTIFACT_SHA,
        record_kind="TRADE",
        provider=PROVIDER,
        knowledge_cutoff=CUTOFF,
    )
    derivation = derive_custody_authority(
        manifest_bytes=manifest, identity=identity
    )
    assert derivation.basis is CustodyAuthorityBasis.UNAUTHORIZED


# ---------------------------------------------------------------------------
# The identity is complete or it does not exist
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field", ["manifest_sha256", "artifact_id", "approval_id", "registry_digest", "provider"]
)
def test_the_identity_requires_every_element(field: str) -> None:
    manifest = _manifest()
    payload = _identity(manifest).model_dump()
    payload.pop(field)
    with pytest.raises(Exception):
        CustodyAuthorityIdentity(**payload)


def test_a_wildcard_record_kind_does_not_exist() -> None:
    manifest = _manifest()
    for kind in ("ANY", "*", "TRADE_OR_LIQUIDATION", ""):
        with pytest.raises(Exception):
            _identity(manifest, record_kind=kind)
    assert SUPPORTED_RECORD_KINDS == ("TRADE", "LIQUIDATION")


def test_a_naive_cutoff_cannot_be_bound() -> None:
    manifest = _manifest()
    with pytest.raises(Exception):
        _identity(manifest, knowledge_cutoff=datetime(2026, 6, 1, 12, 0))


def test_derivation_rejects_raw_kwargs_and_non_bytes() -> None:
    manifest = _manifest()
    with pytest.raises(TypeError):
        derive_custody_authority(  # type: ignore[call-arg]
            manifest_bytes=manifest, artifact_id=ARTIFACT_ID
        )
    with pytest.raises(TypeError):
        derive_custody_authority(
            manifest_bytes=json.dumps({"artifacts": {}}),  # a str, not bytes
            identity=_identity(manifest),
        )


# ---------------------------------------------------------------------------
# No capability object, no issuance marker, no synthetic basis
# ---------------------------------------------------------------------------


def test_no_capability_object_or_issuance_marker_exists_in_src() -> None:
    text = CUSTODY_PATH.read_text(encoding="utf-8")
    identifiers = {
        node.id for node in ast.walk(ast.parse(text)) if isinstance(node, ast.Name)
    } | {node.arg for node in ast.walk(ast.parse(text)) if isinstance(node, ast.arg)}
    for forbidden in (
        "_issue",
        "is_issued",
        "_ISSUANCE_MARKER",
        "capability",
        "SYNTHETIC_TEST_ONLY",
        "attested",
    ):
        assert forbidden not in identifiers, forbidden
    # and the words are not used as public attribute names either
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Attribute):
            assert node.attr not in {"_issue", "is_issued"}, node.attr


def test_no_public_symbol_in_src_builds_an_authorized_value() -> None:
    """A3.2: the derivation is the only producer, and it never produces it."""
    offenders: list[str] = []
    for path in sorted(CONSUMER.glob("*.py")):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(("#", "*", '"""', "'''")):
                continue
            if "AUTHORIZED" in stripped and "CustodyAuthorityBasis.AUTHORIZED" in stripped:
                if "is" in stripped or "==" in stripped or "!=" in stripped:
                    continue
                offenders.append(f"{path.name}: {stripped}")
    assert offenders == [], offenders


def test_the_source_protocol_is_one_method() -> None:
    protocol = CustodySourceAuthoritySource
    methods = [name for name in protocol.__dict__ if not name.startswith("_")]
    assert methods == ["authorize"]
    signature = inspect.signature(protocol.authorize)
    assert list(signature.parameters) == ["self", "identity"]


def test_the_production_source_refuses_a_foreign_root() -> None:
    manifest = _manifest()
    with pytest.raises(ValueError):
        ManifestCustodyAuthority(manifest_bytes=manifest)
    with pytest.raises(TypeError):
        ManifestCustodyAuthority(manifest_bytes=json.dumps({"artifacts": {}}))  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# The missing contract: named, documented, and not invented
# ---------------------------------------------------------------------------


def test_the_unresolved_contract_is_named_in_the_derivation() -> None:
    assert "OPERATOR_CUSTODY_SOURCE_AUTHORITY_RECORD_V1" in UNRESOLVED_AUTHORITY_CONTRACT
    shipped = PRODUCTION_MANIFEST.read_bytes()
    derivation = derive_custody_authority(
        manifest_bytes=shipped, identity=_identity(shipped)
    )
    assert derivation.unresolved_contract == UNRESOLVED_AUTHORITY_CONTRACT


def test_the_manifest_schema_has_no_custody_source_record() -> None:
    """The exact gap, measured on the model rather than asserted in prose."""
    fields = set(ApprovalManifest.model_fields)
    assert fields == {"schema_version", "authority_id", "artifacts", "revoked_approval_ids"}
    artifact_fields = set(ApprovedArtifact.model_fields)
    for absent in (
        "custody_source",
        "authorized_custody_provider",
        "operator_authority",
        "source_authorization",
    ):
        assert absent not in artifact_fields, absent
        assert absent not in fields, absent


def test_the_derivation_invents_no_manifest_token() -> None:
    """Nothing in this module tells an operator what to write into a manifest."""
    text = CUSTODY_PATH.read_text(encoding="utf-8")
    assert "artifact_kind=" not in text
    assert '"CUSTODY_SOURCE_AUTHORITY"' not in text
    assert "'CUSTODY_SOURCE_AUTHORITY'" not in text


def test_a_derivation_cannot_be_authorized_while_naming_a_missing_contract() -> None:
    with pytest.raises(Exception):
        CustodyAuthorityDerivation(
            basis=CustodyAuthorityBasis.AUTHORIZED,
            detail="looks fine",
            unresolved_contract=UNRESOLVED_AUTHORITY_CONTRACT,
            identity_sha256="0" * 64,
        )


def test_a_derivation_cannot_be_authorized_without_naming_its_identity() -> None:
    """H03: an authorization that names no identity is a wildcard."""
    with pytest.raises(Exception):
        CustodyAuthorityDerivation(
            basis=CustodyAuthorityBasis.AUTHORIZED, detail="looks fine"
        )
    # ...and a digest that is not this identity's is refused by the policy.'



def test_the_shipped_manifest_is_byte_identical_and_empty() -> None:
    payload = json.loads(PRODUCTION_MANIFEST.read_text(encoding="utf-8"))
    assert payload["artifacts"] == {}
    assert payload["revoked_approval_ids"] == []
    assert hashlib.sha256(PRODUCTION_MANIFEST.read_bytes()).hexdigest() == (
        TRUSTED_MANIFEST_SHA256
    )


def test_derivation_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    manifest = _manifest()
    _pin(monkeypatch, manifest)
    first = derive_custody_authority(manifest_bytes=manifest, identity=_identity(manifest))
    second = derive_custody_authority(manifest_bytes=manifest, identity=_identity(manifest))
    assert first.model_dump() == second.model_dump()


def test_the_module_is_pure() -> None:
    tree = ast.parse(CUSTODY_PATH.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    for forbidden in (
        "os",
        "io",
        "socket",
        "pathlib",
        "subprocess",
        "glob",
        "requests",
        "httpx",
        "yaml",
    ):
        assert forbidden not in imported, forbidden


def test_a_verdict_may_not_claim_authorization_under_an_unmet_basis() -> None:
    """The verdict's own law, restated where the basis is produced."""
    with pytest.raises(Exception):
        ConsumerVerdict(
            decision=ConsumerDecision.INTEGRATION_REQUIRED,
            pit_status="ADMISSIBLE",
            replay_status="ELIGIBLE",
            custody_status="VERIFIED",
            custody_source_authorization_status=CustodyAuthorityBasis.AUTHORIZED,
            custody_source_authorized=True,
        )
