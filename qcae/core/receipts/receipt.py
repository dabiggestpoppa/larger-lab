"""Capability Receipt — Book IV 9.2.

The canonical bounded statement: what capability Quant Lab believes it has,
through what implementation, under what proof, for what scope, under what
authority, and until what changes invalidate that belief.

A receipt is NOT a universal certificate (9.2 Invariant 2): it is a
scope-bounded, evidence-backed claim. Validation enforces the P1 firewall
rules:

- a receipt cannot exist without proof evidence refs (test 18);
- an authority ref is required (canon 0.3.x acquisition authority; test 19);
- Research Mesh evidence alone never satisfies executable proof (test 20) —
  executable classes (runtime/contract/benchmark evidence) must include at
  least one QCAE-owned or internal ref; external-owner evidence can support
  but never substitute;
- external evidence remains a reference: ``external_owner_domain`` travels
  with every ref that has one and is never rewritten to QCAE (§12).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import (
    require_identifier,
    require_non_empty_str,
    require_str_list,
)

__all__ = ["ReceiptState", "ReceiptEvidenceRef", "CapabilityReceipt", "EXECUTABLE_PROOF_CLASSES"]


class ReceiptState(str, Enum):
    """Receipt lifecycle states (Book IV 9.2)."""

    ACTIVE = "ACTIVE"
    STALE = "STALE"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"
    REJECTED = "REJECTED"


#: Evidence classes that constitute executable proof standing when they come
#: from QCAE-owned/internal execution (Book I 0.4.2 E-classes).
EXECUTABLE_PROOF_CLASSES = frozenset(
    {
        "E4_INDEPENDENT_RUNTIME",
        "E5_INDEPENDENT_CONTRACT",
        "E6_BENCHMARK",
        "E8_INTEGRATION",
    }
)

#: E-class names accepted inside a receipt's evidence refs.
_KNOWN_E_CLASSES = EXECUTABLE_PROOF_CLASSES | {
    "E0_CLAIM",
    "E1_DOCUMENTATION",
    "E2_SOURCE",
    "E3_UPSTREAM_TEST",
    "E7_DOMAIN_VALIDATION",
    "E9_PRODUCTION_OBSERVATION",
}


@dataclass(frozen=True)
class ReceiptEvidenceRef(SerializableRecord):
    """One evidence citation inside a receipt.

    Carries the evidence's standing (E-class) and, when the evidence lives
    under an external owner (A-001 Research Mesh / Economic Experience), the
    immutable external owner domain. Ownership is preserved, never claimed.
    """

    SCHEMA_VERSION = 1

    evidence_id: str
    evidence_class: str
    artifact_digest: str
    external_owner_domain: str = ""

    def validate(self) -> None:
        require_identifier(self.evidence_id, "evidence_id")
        require_non_empty_str(self.artifact_digest, "artifact_digest")
        if self.evidence_class not in _KNOWN_E_CLASSES:
            raise QcaeValidationError(
                f"evidence_class {self.evidence_class!r} is not a known E-class"
            )


@dataclass(frozen=True)
class CapabilityReceipt(SerializableRecord):
    """Scope-bounded capability belief record (Book IV 9.2)."""

    SCHEMA_VERSION = 1

    receipt_id: str
    capability_id: str
    atom_ids: Tuple[str, ...]
    contract_id: str
    contract_version: str
    implementation_id: str
    acquisition_form: str
    source_revision: str
    integration_scope: str
    owner: str
    created_at: str
    state: ReceiptState
    proof_refs: Tuple[ReceiptEvidenceRef, ...]
    security_refs: Tuple[str, ...] = ()
    legal_refs: Tuple[str, ...] = ()
    quant_refs: Tuple[str, ...] = ()
    limitations: Tuple[str, ...] = ()
    assumptions: Tuple[str, ...] = ()
    rollback_ref: str = ""
    authority_ref: str = ""
    revalidation_triggers: Tuple[str, ...] = ()
    valid_until: str = ""
    supersedes_receipt: str = ""
    source_artifact_digests: Tuple[str, ...] = ()

    _COERCIONS = {
        "state": lambda v: coerce_enum(v, ReceiptState),
        "proof_refs": tuple,
        "atom_ids": tuple,
    }

    _NESTED_RECORDS = {"proof_refs": "ReceiptEvidenceRef"}

    def validate(self) -> None:
        require_identifier(self.receipt_id, "receipt_id")
        require_identifier(self.capability_id, "capability_id")
        require_identifier(self.contract_id, "contract_id")
        require_identifier(self.implementation_id, "implementation_id")
        require_identifier(self.authority_ref, "authority_ref")
        require_non_empty_str(self.contract_version, "contract_version")
        require_non_empty_str(self.acquisition_form, "acquisition_form")
        require_non_empty_str(self.source_revision, "source_revision")
        require_non_empty_str(self.integration_scope, "integration_scope")
        require_non_empty_str(self.owner, "owner")
        require_non_empty_str(self.created_at, "created_at")
        require_str_list(self.atom_ids, "atom_ids")
        if not self.atom_ids:
            raise QcaeValidationError("receipt must reference at least one atom")
        if not isinstance(self.state, ReceiptState):
            raise QcaeValidationError(f"state must be a ReceiptState, got {self.state!r}")

        # -- proof firewall -------------------------------------------------
        if not self.proof_refs:
            raise QcaeValidationError(
                "receipt cannot exist without proof evidence refs (Book IV 9.2)"
            )
        for ref in self.proof_refs:
            if not isinstance(ref, ReceiptEvidenceRef):
                raise QcaeValidationError(f"proof_refs entries must be ReceiptEvidenceRef, got {type(ref).__name__}")
        external_only = all(ref.external_owner_domain for ref in self.proof_refs)
        has_executable = any(
            ref.evidence_class in EXECUTABLE_PROOF_CLASSES and not ref.external_owner_domain
            for ref in self.proof_refs
        )
        if external_only:
            raise QcaeValidationError(
                "Research Mesh/external evidence alone cannot satisfy executable proof; "
                "at least one QCAE-owned executable ref is required (A-001 §5)"
            )
        if not has_executable:
            raise QcaeValidationError(
                "receipt proof refs contain no QCAE-owned executable evidence "
                f"(one of {sorted(EXECUTABLE_PROOF_CLASSES)})"
            )

        if not self.rollback_ref:
            raise QcaeValidationError(
                "rollback/exit ref is required (canon 0.2.10 credible exit path)"
            )
        require_identifier(self.rollback_ref, "rollback_ref")
        require_str_list(self.revalidation_triggers, "revalidation_triggers")
        if self.supersedes_receipt:
            require_identifier(self.supersedes_receipt, "supersedes_receipt")
            if self.supersedes_receipt == self.receipt_id:
                raise QcaeValidationError("receipt cannot supersede itself")


def make_receipt(**kwargs) -> CapabilityReceipt:
    receipt = CapabilityReceipt(**kwargs)
    receipt.validate()
    return receipt
