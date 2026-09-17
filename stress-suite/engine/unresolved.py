"""Unresolved states — MUST NOT force an observation into the nearest known
ontology/mechanism/governance category (A-009 §12, A-010 §13, Book S24).

Two distinct objects:
* UnresolvedPatternRecord   -> an observation that existing ontology cannot
                               classify (may eventually seed a new mechanism
                               family: S15).
* UnresolvedGovernanceEvent -> a governance failure that maps to no known
                               Governor channel/scope rule (S24) — preserved
                               exactly, then routed to a safe hold + amendment
                               candidate.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from .base import Provenance, deterministic_hex


@dataclass
class UnresolvedPatternRecord:
    record_id: str
    schema_version: str = "1.0.0"
    classification: str = "UNRESOLVED_PATTERN"   # forced assignment is FORBIDDEN
    observation: str = ""
    provenance: Optional[Provenance] = None
    confirmed_by: List[str] = field(default_factory=list)   # evidence refs that survived data-quality checks
    candidate_explanations: List[str] = field(default_factory=list)
    revisit_trigger: str = ""
    status: str = "ACTIVE"
    seq: int = 0

    @classmethod
    def make(cls, seq, observation, provenance=None, confirmed_by=None, revisit_trigger=""):
        return cls(
            record_id=deterministic_hex("unresolved_pattern", seq, observation),
            observation=observation,
            provenance=provenance,
            confirmed_by=list(confirmed_by or []),
            revisit_trigger=revisit_trigger,
            seq=seq,
        )

    # structural guarantee: there is no required 'closest_category' field.


@dataclass
class UnresolvedGovernanceEvent:
    record_id: str
    schema_version: str = "1.0.0"
    classification: str = "UNRESOLVED_GOVERNANCE_EVENT"
    description: str = ""
    provenance: Optional[Provenance] = None
    suggested_consequences: List[str] = field(default_factory=list)  # e.g. "SAFE_HOLD"
    amendment_candidate: str = ""
    status: str = "OPEN"
    seq: int = 0

    @classmethod
    def make(cls, seq, description, provenance=None, suggested_consequences=None):
        return cls(
            record_id=deterministic_hex("unresolved_governance", seq, description),
            description=description,
            provenance=provenance,
            suggested_consequences=list(suggested_consequences or []),
            seq=seq,
        )

    # 'unknown_governance_failure' remains representable WITHOUT requiring the
    # caller to assign an existing channel or scope level (Book S24).