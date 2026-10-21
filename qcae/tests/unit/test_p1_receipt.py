"""P1-C05 — Capability Receipt evidence (P1 spec §7, tests 14–20)."""

from __future__ import annotations

import dataclasses

import pytest

from qcae.core.errors import QcaeValidationError
from qcae.core.receipts import (
    CapabilityReceipt,
    ReceiptEvidenceRef,
    ReceiptState,
    make_receipt,
)
from qcae.core.serialization import QcaeSchemaVersionError


def _ref(eid="ev-exec-1", cls="E5_INDEPENDENT_CONTRACT", owner="") -> ReceiptEvidenceRef:
    return ReceiptEvidenceRef(
        evidence_id=eid,
        evidence_class=cls,
        artifact_digest="a" * 64,
        external_owner_domain=owner,
    )


def _receipt(**over) -> CapabilityReceipt:
    defaults = dict(
        receipt_id="rcpt-001",
        capability_id="CAP-REPLAY-001",
        atom_ids=("atom-replay-engine",),
        contract_id="CAP-REPLAY-001",
        contract_version="1.0.0",
        implementation_id="repo:owner/impl@abc123",
        acquisition_form="VENDOR",
        source_revision="abc123",
        integration_scope="quant-lab.research",
        owner="quant-lab-platform",
        created_at="2026-09-12T00:00:00Z",
        state=ReceiptState.ACTIVE,
        proof_refs=(_ref(),),
        rollback_ref="plan-exit-replay-001",
        authority_ref="auth-decision-001",
        revalidation_triggers=("upstream_revision",),
    )
    defaults.update(over)
    return make_receipt(**defaults)


class TestReceiptBasics:
    def test_round_trip(self) -> None:
        r = _receipt()
        restored = CapabilityReceipt.from_dict(r.to_dict())
        assert restored == r
        assert restored.proof_refs == (_ref(),)

    def test_all_states_exist(self) -> None:
        assert {s.value for s in ReceiptState} == {
            "ACTIVE", "STALE", "REVALIDATION_REQUIRED", "SUPERSEDED", "REVOKED", "REJECTED",
        }

    def test_scope_fields_preserved_round_trip(self) -> None:
        r = _receipt(integration_scope="quant-lab.live-cerebus")
        restored = CapabilityReceipt.from_dict(r.to_dict())
        assert restored.integration_scope == "quant-lab.live-cerebus"

    def test_schema_version_rejected(self) -> None:
        payload = _receipt().to_dict()
        payload["schema_version"] = 2
        with pytest.raises(QcaeSchemaVersionError):
            CapabilityReceipt.from_dict(payload)


class TestProofFirewall:
    def test_receipt_cannot_claim_proof_absent_evidence(self) -> None:
        with pytest.raises(QcaeValidationError, match="without proof evidence"):
            _receipt(proof_refs=())

    def test_authority_ref_required(self) -> None:
        with pytest.raises(QcaeValidationError, match="authority_ref"):
            _receipt(authority_ref="")

    def test_rollback_required(self) -> None:
        with pytest.raises(QcaeValidationError, match="rollback"):
            _receipt(rollback_ref="")

    def test_research_mesh_citation_alone_cannot_satisfy_executable_proof(self) -> None:
        """Even a full set of Research Mesh refs, however strong-looking,
        cannot create a receipt: executable proof must be QCAE-owned."""
        mesh_refs = tuple(
            _ref(eid=f"ev-mesh-{i}", cls="E5_INDEPENDENT_CONTRACT",
                 owner="research-mesh.internal")
            for i in range(3)
        )
        with pytest.raises(QcaeValidationError, match="Research Mesh/external evidence alone"):
            _receipt(proof_refs=mesh_refs)

    def test_mesh_evidence_can_support_but_not_substitute(self) -> None:
        """Mixed refs are valid: external supports, QCAE-owned proves."""
        r = _receipt(
            proof_refs=(
                _ref(eid="ev-mesh-1", cls="E2_SOURCE", owner="research-mesh.internal"),
                _ref(eid="ev-exec-1", cls="E5_INDEPENDENT_CONTRACT"),
            )
        )
        r.validate()

    def test_external_evidence_cannot_be_rewritten_as_qcae_owned(self) -> None:
        """The owner domain is part of the record identity; erasing it changes
        the digest, so any 'conversion' of external evidence to internal is a
        different, detectable object."""
        external = _ref(eid="ev-mesh-1", cls="E2_SOURCE", owner="research-mesh.internal")
        laundered = dataclasses.replace(external, external_owner_domain="")
        assert external.digest() != laundered.digest()

    def test_non_executable_internal_refs_insufficient(self) -> None:
        with pytest.raises(QcaeValidationError, match="no QCAE-owned executable"):
            _receipt(proof_refs=(_ref(eid="ev-doc", cls="E1_DOCUMENTATION"),))


class TestLineage:
    def test_superseded_receipt_lineage_preserved(self) -> None:
        old = _receipt(receipt_id="rcpt-000", state=ReceiptState.SUPERSEDED)
        new = _receipt(supersedes_receipt="rcpt-000")
        new.validate()
        # the old receipt object is untouched and still says SUPERSEDED
        assert old.state is ReceiptState.SUPERSEDED
        assert new.supersedes_receipt == "rcpt-000"

    def test_self_supersession_rejected(self) -> None:
        with pytest.raises(QcaeValidationError, match="supersede itself"):
            _receipt(supersedes_receipt="rcpt-001")

    def test_stale_receipt_not_current(self) -> None:
        stale = _receipt(state=ReceiptState.STALE)
        assert stale.state is not ReceiptState.ACTIVE

    def test_atom_required(self) -> None:
        with pytest.raises(QcaeValidationError, match="at least one atom"):
            _receipt(atom_ids=())
