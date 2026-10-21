"""Context Packet (P2-C06; Book V 12.4, directive §18).

Workers receive minimum sufficient context. The packet references, and does
not blindly copy: job objective, step objective, required CapabilityContract,
relevant evidence/registry refs, the authority decision, budget, allowed
tools/providers, and the output contract.

Law (Book V 12.4):

- context is assembled per task; full-chat continuity is never required;
- unrelated registry/project memory is absent by construction;
- earlier claims retain verification labels;
- the packet itself is versioned/hashable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from qcae.core.errors import QcaeValidationError
from qcae.core.serialization import SerializableRecord
from qcae.core.validation import (
    require_identifier,
    require_non_empty_str,
    require_no_duplicates,
)

__all__ = ["ContextPacket", "make_context_packet"]


@dataclass(frozen=True)
class ContextPacket(SerializableRecord):
    """Reproducible, least-context invocation envelope."""

    SCHEMA_VERSION = 1

    packet_id: str
    job_id: str
    step_id: str
    worker_type: str

    # Objectives (short, reference-backed — not chat history).
    job_objective: str = ""
    step_objective: str = ""

    # References, not copies (Book V 12.4 "references and summaries with
    # provenance").
    contract_ref: str = ""
    contract_version: Optional[int] = None
    evidence_refs: Tuple[str, ...] = ()
    registry_refs: Tuple[str, ...] = ()
    prior_findings_refs: Tuple[str, ...] = ()
    authority_decision_ref: str = ""
    budget_ref: str = ""

    # Explicit tool/permission boundary (directive §12: least authority).
    allowed_tools: Tuple[str, ...] = ()

    # What the worker must produce.
    output_contract: str = ""

    # Verification labels for prior claims (Book V 12.4 hypothesis separation).
    prior_claim_labels: Tuple[str, ...] = ()

    def validate(self) -> None:
        require_identifier(self.packet_id, "packet_id")
        require_identifier(self.job_id, "job_id")
        require_identifier(self.step_id, "step_id")
        require_non_empty_str(self.worker_type, "worker_type")
        require_no_duplicates(self.evidence_refs, "evidence_refs")
        require_no_duplicates(self.registry_refs, "registry_refs")
        require_no_duplicates(self.allowed_tools, "allowed_tools")
        if self.contract_version is not None and not self.contract_ref:
            raise QcaeValidationError(
                "contract_version requires contract_ref"
            )


def make_context_packet(**kwargs) -> ContextPacket:
    packet = ContextPacket(**kwargs)
    packet.validate()
    return packet
