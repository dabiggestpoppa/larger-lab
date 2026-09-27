"""OutcomePacket (A-004 §6) and ResumeCapsule (A-004 §7 / A-005 §2.4).

ResumeCapsule must permit cold-start reconstruction WITHOUT the raw transcript.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from .base import deterministic_hex


@dataclass
class OutcomePacket:
    packet_id: str
    schema_version: str = "1.0.0"
    disposition: str = "PARTIAL"      # PASS / FAIL / BLOCKED / PARTIAL / CANCELLED
    produced_artifacts: List[str] = field(default_factory=list)
    claims_made: List[str] = field(default_factory=list)
    evidence_refs: List[str] = field(default_factory=list)
    observed_side_effects: List[str] = field(default_factory=list)
    unresolved_uncertainty: List[str] = field(default_factory=list)
    contradictions_discovered: List[str] = field(default_factory=list)
    cost_consumed: str = "0"
    recommended_next_action: str = ""
    reusable_lesson_candidates: List[str] = field(default_factory=list)
    seq: int = 0

    @classmethod
    def make(cls, seq, disposition="PARTIAL", **kw):
        return cls(
            packet_id=deterministic_hex("outcome", seq, disposition),
            disposition=disposition,
            seq=seq,
            **kw,
        )


@dataclass
class ResumeCapsule:
    capsule_id: str
    schema_version: str = "1.0.0"
    goal_id: str = ""
    task_id: str = ""
    plan_version: str = ""
    last_verified_state: str = ""
    completed_nodes: List[str] = field(default_factory=list)
    remaining_nodes: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    pending_operator_decision: str = ""
    active_leases_grants: List[str] = field(default_factory=list)
    cleanup_obligations: List[str] = field(default_factory=list)
    next_safe_action: str = ""
    evidence_refs: List[str] = field(default_factory=list)
    epoch_ref: str = ""
    seq: int = 0

    @classmethod
    def make(cls, seq, goal_id="", task_id="", **kw):
        return cls(
            capsule_id=deterministic_hex("resume", seq, goal_id, task_id),
            goal_id=goal_id,
            task_id=task_id,
            seq=seq,
            **kw,
        )