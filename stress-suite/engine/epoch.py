"""EpochManifest (A-010 §14). Institutional time may be queried by epoch.

G1 validates only serialization / reconstruction-round-trip semantics; the
operational reconstruction *checklist* for which graphs must rehydrate is G4 work
(AMB-12 stays open).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set

from .base import deterministic_hex


@dataclass
class EpochManifest:
    epoch_id: str
    schema_version: str = "1.0.0"
    start_cause: str = ""
    predecessor_epoch: Optional[str] = None
    governing_architecture_versions: List[str] = field(default_factory=list)
    evaluation_contract_version: str = ""
    active_ontology_versions: List[str] = field(default_factory=list)
    high_dependency_assumptions: List[str] = field(default_factory=list)
    active_runtime_certifications: List[str] = field(default_factory=list)
    major_capabilities: List[str] = field(default_factory=list)
    known_tensions: List[str] = field(default_factory=list)
    unresolved_pattern_refs: List[str] = field(default_factory=list)
    active_knowledge_projection: List[str] = field(default_factory=list)
    dormant_knowledge_projection: List[str] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)
    authority_state_snapshot: Dict[str, str] = field(default_factory=dict)
    operator_ratifications: List[str] = field(default_factory=list)
    transformation_evidence: List[str] = field(default_factory=list)
    challenge_conditions: List[str] = field(default_factory=list)   # T16: epoch != dogma

    @classmethod
    def make(cls, seq, epoch_id=None, **kw):
        return cls(
            epoch_id=epoch_id or deterministic_hex("epoch", seq),
            **kw,
        )

    def fingerprint(self) -> str:
        return deterministic_hex("epoch_fp", asdict(self))

    # Round-trip: to_dict/from_dict must be lossless (G1 test).
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EpochManifest":
        return cls(**data)