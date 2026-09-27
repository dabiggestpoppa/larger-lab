"""NegativeKnowledgeRecord (A-005 §2.3, A-009 §10, Book S11).

A negative-knowledge record intended for automated suppression/retrieval
filtering MUST carry at least one explicit reopen condition, or an explicit
`PERMANENT_BY_OPERATOR_AUTHORITY` designation with an attributable authority
reference.

Ordinary agents CANNOT create irreversible permanent negative knowledge. Only an
operator-authorized authority basis may mark a record permanent.

G4R-08 — permanence is STRUCTURALLY unforgeable:
  * `is_permanent` is a VALIDATED property: it is True only when the full
    governed permanence block exists AND validates (actual level == OPERATOR,
    binding == EXACT_AUTHORITY_STATE, non-empty authority basis and
    ratification ref).
  * Direct assignment of `permanent_by_operator_authority = "FAKE"` alone can
    never produce a valid permanent record — validate_for_suppression() and
    is_permanent both reject it.
  * Deserialization (from_dict) validates the full authority block and rejects
    fabricated permanence.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List, Optional

from .base import Provenance, deterministic_hex


class NegativeKnowledgeError(ValueError):
    pass


PERMANENCE_BINDING = "EXACT_AUTHORITY_STATE"
PERMANENCE_LEVEL = "OPERATOR"


def _validate_permanence_block(permanent_flag: Optional[str],
                               block: Optional[dict]) -> Optional[str]:
    """Returns None when the permanence block is valid, else a violation
    reason. A valid permanent record requires the flag AND a full governed
    authority block with actual OPERATOR level and exact state binding."""
    if permanent_flag is None:
        return None if block is None else "permanence block without permanent flag"
    if not permanent_flag:
        return "empty permanence flag"
    if not isinstance(block, dict) or not block:
        return "permanence_authority block missing"
    required = ("actor", "actual_level", "authority_basis", "ratification_ref", "binding")
    missing = [k for k in required if not block.get(k)]
    if missing:
        return f"permanence_authority missing mandatory field(s): {missing}"
    if block["actual_level"] != PERMANENCE_LEVEL:
        return f"permanence requires actual_level == {PERMANENCE_LEVEL}, got {block['actual_level']!r}"
    if block["binding"] != PERMANENCE_BINDING:
        return f"permanence requires binding == {PERMANENCE_BINDING}, got {block['binding']!r}"
    if block["authority_basis"] != permanent_flag:
        return "permanence_authority.authority_basis does not match the permanent flag"
    return None


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
    permanence_authority: Optional[dict] = None              # G4-P0-C attributable authority block

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

    # ------------------------------------------------------------------ #
    # G4R-08 — validated permanence property
    # ------------------------------------------------------------------ #
    @property
    def is_permanent(self) -> bool:
        """True ONLY when the full governed authority block validates. A bare
        `permanent_by_operator_authority` string (e.g. "FAKE") cannot make a
        record permanent — direct spoofing fails closed."""
        violation = _validate_permanence_block(self.permanent_by_operator_authority,
                                               self.permanence_authority)
        return violation is None and self.permanent_by_operator_authority is not None

    def permanence_violation(self) -> Optional[str]:
        return _validate_permanence_block(self.permanent_by_operator_authority,
                                          self.permanence_authority)

    def validate_for_suppression(self) -> None:
        """Schema-level rule: an auto-suppressed record must be reopenable or
        carry a STRUCTURALLY VALID operator-permanent block. A spoofed or
        partial permanence designation is a violation."""
        if self.permanent_by_operator_authority:
            violation = _validate_permanence_block(self.permanent_by_operator_authority,
                                                   self.permanence_authority)
            if violation is not None:
                raise NegativeKnowledgeError(
                    f"NegativeKnowledge permanence is structurally invalid: {violation}")
            return
        if not self.reopen_conditions:
            raise NegativeKnowledgeError(
                "NegativeKnowledge with no reopen_conditions may not be auto-suppressed; "
                "add a reopen condition or PERMANENT_BY_OPERATOR_AUTHORITY"
            )

    def make_permanent(self, actor: str, authority_state: "AuthorityState",
                       authority_basis: str, ratification_ref: str = "") -> None:
        """G4-P0-C/G4R-08: permanence requires EXACT actor -> AuthorityState
        binding.

        The caller must supply the ACTOR and the governed AuthorityState; the
        ACTUAL level of that actor is read from AuthorityState.level(actor). A
        payload string saying "OPERATOR" while the actor is a WORKER is
        rejected — substring checks ("OPERATOR" in authority_level) are never
        an authority basis.

        Only actual OPERATOR authority may create PERMANENT_BY_OPERATOR_AUTHORITY.
        The actor, actual level, authority basis and ratification reference are
        recorded so permanence is attributable and reconstructable.
        """
        from .authority import AuthorityLevel  # local import avoids cycle
        actual_level = authority_state.level(actor)
        if actual_level != AuthorityLevel.OPERATOR.value:
            raise NegativeKnowledgeError(
                f"only actual OPERATOR authority may mark negative knowledge "
                f"permanent; actor {actor!r} has level {actual_level!r}"
            )
        if not authority_basis:
            raise NegativeKnowledgeError("permanence requires a non-empty authority basis")
        self.permanent_by_operator_authority = authority_basis
        self.authority_basis = authority_basis
        self.permanence_authority = {
            "actor": actor,
            "actual_level": actual_level,
            "authority_basis": authority_basis,
            "ratification_ref": ratification_ref,
            "binding": PERMANENCE_BINDING,
        }

    # ------------------------------------------------------------------ #
    # serialization — deserialization validates the permanence block (G4R-08)
    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "schema_version": self.schema_version,
            "claim_rejected": self.claim_rejected,
            "exact_scope": self.exact_scope,
            "evidence_refs": list(self.evidence_refs),
            "rejection_reason": self.rejection_reason,
            "assumptions": list(self.assumptions),
            "blockers": list(self.blockers),
            "reopen_conditions": list(self.reopen_conditions),
            "provenance": asdict(self.provenance) if self.provenance else None,
            "author_actor": self.author_actor,
            "authority_basis": self.authority_basis,
            "current_lifecycle_state": self.current_lifecycle_state,
            "seq": self.seq,
            "permanent_by_operator_authority": self.permanent_by_operator_authority,
            "permanence_authority": dict(self.permanence_authority)
            if self.permanence_authority else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NegativeKnowledgeRecord":
        rec = cls(**{k: v for k, v in data.items()
                     if k in cls.__dataclass_fields__})
        violation = _validate_permanence_block(rec.permanent_by_operator_authority,
                                               rec.permanence_authority)
        if rec.permanent_by_operator_authority and violation is not None:
            raise NegativeKnowledgeError(
                f"deserialized NegativeKnowledge permanence rejected: {violation}")
        return rec
