"""M1 — capability truth labels (Constitution Article II).

Kept SEPARATE from the M4 knowledge lifecycle and from authority. A capability
status of OPERATIONALLY_PROVEN must never be mistaken for "evidence strength" or
for any authority. Only enough interoperability is provided to prevent conflation
(AMB-07), not a parallel truth system.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from .base import CapabilityTruthLabel as T, deterministic_hex


@dataclass
class CapabilityStatus:
    capability_id: str
    label: str = T.SCAFFOLDED.value
    evidence_refs: List[str] = field(default_factory=list)
    owner: str = ""
    env: str = "local-test"
    schema_version: str = "1.0.0"

    def to_dict(self) -> dict:
        return asdict(self)


class TruthRegistry:
    """capability -> CapabilityStatus. Promotion requires linked evidence; a high
    label never grants authority (Constitution Article II, A-009 §21.3)."""

    def __init__(self) -> None:
        self._capabilities: Dict[str, CapabilityStatus] = {}
        self._promotions: List[dict] = []

    def register(self, cap: CapabilityStatus) -> None:
        self._capabilities[cap.capability_id] = cap

    def promote(self, capability_id: str, to_label: str, evidence_refs: List[str], actor: str) -> None:
        if not evidence_refs:
            raise ValueError("no status promotion may lack linked evidence (Constitution Article II)")
        cap = self._capabilities[capability_id]
        new = CapabilityStatus(
            capability_id=cap.capability_id,
            label=to_label,
            evidence_refs=list(evidence_refs),
            owner=cap.owner,
            env=cap.env,
        )
        self._capabilities[capability_id] = new
        self._promotions.append({"capability_id": capability_id, "to": to_label, "actor": actor})

    def label(self, capability_id: str) -> str:
        return self._capabilities[capability_id].label

    # hard separations
    @staticmethod
    def truth_label_is_not_evidence(entry: CapabilityStatus) -> bool:
        # a label is a claim; it must point to evidence_refs if proven
        if entry.label in (T.VERIFIED_ISOLATED.value, T.VERIFIED_INTEGRATED.value,
                           T.VERIFIED_E2E.value, T.OPERATIONALLY_PROVEN.value):
            return bool(entry.evidence_refs)
        return True

    @staticmethod
    def truth_label_is_not_authority(label: str) -> bool:
        return True   # no label, however high, is by itself an authority grant