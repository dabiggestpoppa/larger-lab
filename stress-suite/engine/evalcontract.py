"""PhaseEvaluationContract (G1 §8; addresses CON-03 / AMB-05).

A versioned contract capturing:
  - the A-010 evidence channels and their thresholds/rules;
  - hysteresis rules;
  - admissible phase transitions;
  - a freeze flag.

CRITICAL INVARIANT: once a TransformationWindow or evaluation episode opens under
contract V, its success criteria cannot silently change to V' during that same
evaluation. A proposed change becomes a separate future contract/version.

We deliberately DO NOT decide whether thresholds should be visible to adaptive
workers; each threshold carries a visibility_policy so CON-03 remains testable:
  visibility_policy: PUBLIC / ROLE_RESTRICTED / SEALED_TEST_PARAMETER
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, FrozenSet, List, Optional, Sequence

from .base import EVALUATION_CONTRACT_VERSION, EvidenceChannel, deterministic_hex

VISIBILITY_POLICIES = ("PUBLIC", "ROLE_RESTRICTED", "SEALED_TEST_PARAMETER")


class FreezeViolation(ValueError):
    pass


@dataclass
class PhaseEvaluationContract:
    contract_id: str
    schema_version: str = "1.0.0"
    version_tag: str = "V1"
    channel_rules: Dict[str, Dict[str, str]] = field(default_factory=dict)  # channel -> {threshold, visibility_policy, note}
    hysteresis_rules: Dict[str, str] = field(default_factory=dict)
    admissible_phase_transitions: List[tuple] = field(default_factory=list)
    created_at_seq: int = 0
    authority_basis: str = ""
    freeze_status: str = "UNFROZEN"     # UNFROZEN / FROZEN
    supersedes: Optional[str] = None

    @classmethod
    def make(cls, seq, version_tag="V1", visibility_policy="PUBLIC", channels=None,
             channel_rules=None, hysteresis_rules=None, admissible_phase_transitions=None,
             authority_basis="OPP", created_at_seq=None):
        if channel_rules is None:
            channel_rules = {}
            for ch in (channels or tuple(c.value for c in EvidenceChannel)):
                channel_rules[ch] = {
                    "threshold": "MEDIUM",
                    "visibility_policy": visibility_policy,
                    "note": "",
                }
        return cls(
            contract_id=deterministic_hex("eval_contract", seq, version_tag),
            version_tag=version_tag,
            channel_rules=channel_rules,
            hysteresis_rules=dict(hysteresis_rules or {}),
            admissible_phase_transitions=list(admissible_phase_transitions or []),
            created_at_seq=created_at_seq or seq,
            authority_basis=authority_basis,
        )

    def freeze(self) -> None:
        self.freeze_status = "FROZEN"

    def is_frozen(self) -> bool:
        return self.freeze_status == "FROZEN"

    def mutate(self, changes: Dict[str, object]) -> "PhaseEvaluationContract":
        """A frozen contract cannot be mutated in place. A proposed change yields
        a NEW version contract; the frozen one is untouched (S20 / T6)."""
        if self.is_frozen():
            raise FreezeViolation(
                "frozen evaluation contract may not change mid-window; "
                "open a separate future contract instead"
            )
        copy = PhaseEvaluationContract(
            contract_id=self.contract_id,
            schema_version=self.schema_version,
            version_tag=self.version_tag,
            channel_rules=dict(self.channel_rules),
            hysteresis_rules=dict(self.hysteresis_rules),
            admissible_phase_transitions=list(self.admissible_phase_transitions),
            created_at_seq=self.created_at_seq,
            authority_basis=self.authority_basis,
            freeze_status=self.freeze_status,
            supersedes=self.supersedes,
        )
        for key, val in changes.items():
            setattr(copy, key, val)
        return copy

    def next_version(self, seq: int) -> "PhaseEvaluationContract":
        """Fine-grained *future* contract with a fresh version tag; the old
        remains frozen for the evaluation it governs."""
        n = PhaseEvaluationContract(
            contract_id=deterministic_hex("eval_contract", seq, f"{self.version_tag}-next"),
            version_tag=f"{self.version_tag}-n({seq})",
            channel_rules=dict(self.channel_rules),
            hysteresis_rules=dict(self.hysteresis_rules),
            admissible_phase_transitions=list(self.admissible_phase_transitions),
            authority_basis=self.authority_basis,
            freeze_status="UNFROZEN",
            supersedes=self.contract_id,
        )
        return n