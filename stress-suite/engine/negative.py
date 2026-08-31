"""NegativeKnowledgeRecord (A-005 §2.3, A-009 §10, Book S11).

A negative-knowledge record intended for automated suppression/retrieval
filtering MUST carry at least one explicit reopen condition, or an explicit
`PERMANENT_BY_OPERATOR_AUTHORITY` designation with an authority reference.

Ordinary agents CANNOT create irreversible permanent negative knowledge. Only an
operator-authorized authority basis may mark a record permanent.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional

from .base import Provenance, deterministic_hex


class NegativeKnowledgeError(ValueError):
    pass


@dataclass
class NegativeKnowledgeRecord:
    record_id: str
    schema_version: str = "1.0.0"
    claim_rejected: str = ""
    exact_scope: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    rejection_reason: str = ""
    assumptions: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    reopen_conditions: List[str] = field(default_factory=list)
    provenance: Optional[Provenance] = None
    author_actor: str = ""
    authority_basis: str = ""
    current_lifecycle_state: str = "DEMOTED"
    seq: int = 0
    permanent_by_operator_authority: Optional[str] = None   # authority reference if operator-permanent

    @classmethod
    def make(
        cls,
        seq,
        claim_rejected,
        exact_scope,
        rejection_reason,
        reopen_conditions=None,
        permissions=None,
    ):
        """Creates ordinary agent-created negative knowledge (reopenable)."""
        return cls(
            record_id=deterministic_hex("negative_knowledge", seq, claim_rejected),
            claim_rejected=claim_rejected,
            exact_scope=exact_scope,
            rejection_reason=rejection_reason,
            reopen_conditions=list(reopen_conditions or []),
            seq=seq,
        )

    def validate_for_suppression(self) -> None:
        """Schema-level rule: an auto-suppressed record must be reopenable or
        operator-permanent. An agent-branded permanent record is a violation."""
        if self.permanent_by_operator_authority:
            return
        if not self.reopen_conditions:
            raise NegativeKnowledgeError(
                "NegativeKnowledge with no reopen_conditions may not be auto-suppressed; "
                "add a reopen condition or PERMANENT_BY_OPERATOR_AUTHORITY"
            )

    def make_permanent(self, authority_basis: str, authority_level: str) -> None:
        """Only an operator-authorized call may set permanence."""
        if authority_level != "OPERATOR" and "OPERATOR" not in str(authority_level):
            raise NegativeKnowledgeError("only operator authority may mark negative knowledge permanent")
        self.permanent_by_operator_authority = authority_basis
        self.authority_basis = authority_basis

    @property
    def is_permanent(self) -> bool:
        return self.permanent_by_operator_authority is not None