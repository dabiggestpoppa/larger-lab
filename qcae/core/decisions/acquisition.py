"""AcquisitionDecision — a terminal, evidence-backed recommendation/authority result.

Canon Book I 0.5.12–0.5.15, 1.3.3 (Acquisition Decision entity), 1.3.10
(decision graph preserves alternatives), master prompt §17.

Scope rule: decisions are capability/atom-scoped, not repository-scoped — one
repository may produce several different decisions across its atoms.

Rejection reasons form the controlled negative-knowledge vocabulary (canon
0.2.8, master prompt §19) so rejected candidates stay queryable and are not
silently re-investigated.

Authority rule: intelligence is separate from authority (canon 0.2.12). An
APPROVED outcome must cite the authority decision that granted it; QCAE
workers cannot self-approve.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord, coerce_enum
from qcae.core.validation import (
    require_identifier,
    require_no_duplicates,
    require_non_empty_str,
)
from qcae.core.vocabulary import AcquisitionForm


class DecisionOutcome(StrEnum):
    """Terminal decision status (canon 0.5.13–0.5.15)."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"


class RejectionReason(StrEnum):
    """Durable negative-knowledge vocabulary (canon 0.2.8; master prompt §19)."""

    LICENSE_CONFLICT = "license-conflict"
    DEPENDENCY_BURDEN = "dependency-burden"
    FAILED_BUILD = "failed-build"
    HIDDEN_SAAS_REQUIREMENT = "hidden-saas-requirement"
    SECURITY_ISSUE = "security-issue"
    FAILED_CONTRACT_TEST = "failed-contract-test"
    QUANT_LEAKAGE = "quant-leakage"
    UNREPRODUCIBLE_BENCHMARK = "unreproducible-benchmark"
    INFERIOR_TO_INTERNAL = "inferior-to-internal"
    EXCESSIVE_LOCK_IN = "excessive-lock-in"
    OTHER = "other"


@dataclass(frozen=True)
class AcquisitionDecision(SerializableRecord):
    SCHEMA_VERSION = 1

    decision_id: str

    # Capability/atom scope (NOT repository scope; master prompt §17).
    capability_scope: str

    # Candidate under evaluation; may be empty for internal-retention decisions.
    candidate_ref: str

    form: AcquisitionForm
    outcome: DecisionOutcome

    rationale: str

    # Required when outcome == REJECTED (negative knowledge, canon 0.2.8).
    rejection_reason: Optional[RejectionReason] = None

    # Content digests of the evidence artifacts backing this decision
    # (canon 0.2.2: evidence over claims; 1.3.10: decision graph).
    evidence_digests: Tuple[str, ...] = ()

    # Authority linkage (canon 0.2.12, 0.3.6): the AuthorityDecision that
    # granted an APPROVED outcome. QCAE cannot approve itself.
    authority_decision_ref: str = ""

    # Canon 0.5.15: deferral names the unresolved material dependency.
    deferred_pending: str = ""

    decided_by: str = ""
    decided_at: str = ""

    supersedes_decision: str = ""

    _COERCIONS = {
        "form": lambda v: coerce_enum(v, AcquisitionForm),
        "outcome": lambda v: coerce_enum(v, DecisionOutcome),
        "rejection_reason": lambda v: coerce_enum(v, RejectionReason) if v else None,
    }

    def validate(self) -> None:
        require_identifier(self.decision_id, "decision_id")
        require_identifier(self.capability_scope, "capability_scope")
        if self.candidate_ref:
            require_identifier(self.candidate_ref, "candidate_ref")
        if not isinstance(self.form, AcquisitionForm):
            raise QcaeValidationError(
                f"form must be an AcquisitionForm member (canon 0.5.12 spectrum), "
                f"got {self.form!r}"
            )
        if not isinstance(self.outcome, DecisionOutcome):
            raise QcaeValidationError(
                f"outcome must be a DecisionOutcome member, got {self.outcome!r}"
            )
        require_non_empty_str(self.rationale, "rationale")

        # Form/outcome coherence (canon 0.5.12: DEFER/REJECT are spectrum forms).
        if self.outcome == DecisionOutcome.REJECTED:
            if self.rejection_reason is None:
                raise QcaeValidationError(
                    "REJECTED decisions require a rejection_reason: rejection is "
                    "an output stored as durable knowledge (canon 0.2.8)"
                )
        else:
            if self.rejection_reason is not None:
                raise QcaeValidationError(
                    "rejection_reason is only valid on REJECTED outcomes"
                )

        if self.outcome == DecisionOutcome.DEFERRED:
            require_non_empty_str(
                self.deferred_pending,
                "deferred_pending (canon 0.5.15: deferral names the unresolved "
                "material dependency)",
            )
        else:
            if self.deferred_pending:
                raise QcaeValidationError(
                    "deferred_pending is only valid on DEFERRED outcomes"
                )

        # Evidence-backed decisions (canon 0.2.2, 0.5.14).
        if self.outcome != DecisionOutcome.DEFERRED and not self.evidence_digests:
            raise QcaeValidationError(
                f"{self.outcome} decisions must cite evidence artifacts"
            )
        for digest in self.evidence_digests:
            if not isinstance(digest, str) or len(digest) < 8:
                raise QcaeValidationError(
                    f"evidence_digests entries must be content digests, got {digest!r}"
                )
        require_no_duplicates(self.evidence_digests, "evidence_digests")

        # Authority separation (canon 0.2.12): approval requires granted authority.
        if self.outcome == DecisionOutcome.APPROVED:
            require_identifier(
                self.authority_decision_ref,
                "authority_decision_ref (canon 0.2.12: intelligence is not authority; "
                "approval must cite the authority decision)",
            )

        if self.decided_by:
            require_non_empty_str(self.decided_by, "decided_by")
        if self.supersedes_decision:
            require_identifier(self.supersedes_decision, "supersedes_decision")


def make_acquisition_decision(**kwargs) -> AcquisitionDecision:
    """Build and validate an acquisition decision in one call."""
    decision = AcquisitionDecision(**kwargs)
    decision.validate()
    return decision
