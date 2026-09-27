"""AffectedSurface (A-005 §2.5) — machine-readable blast-radius of a change.

Review depth and test radius follow AffectedSurface, never line/file count.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List

from .base import deterministic_hex


@dataclass
class AffectedSurface:
    affected_surface_id: str
    schema_version: str = "1.0.0"
    changed_contracts: List[str] = field(default_factory=list)
    direct_consumers: List[str] = field(default_factory=list)
    transitive_consumers: List[str] = field(default_factory=list)
    authority_security_impact: str = "NONE"
    data_state_impact: str = "NONE"
    required_test_depth: str = "LEAF"      # LEAF / MID / CORE
    required_review_depth: str = "LOCAL"   # LOCAL / FRESH_CONTEXT / INDEPENDENT
    seq: int = 0

    @classmethod
    def make(cls, seq, consumers, required_test_depth="LEAF", required_review_depth="LOCAL"):
        return cls(
            affected_surface_id=deterministic_hex("affected_surface", seq, required_test_depth),
            direct_consumers=list(consumers),
            required_test_depth=required_test_depth,
            required_review_depth=required_review_depth,
            seq=seq,
        )

    def centrality_tier(self) -> str:
        if self.required_test_depth == "CORE":
            return "CORE"
        if self.required_test_depth == "MID":
            return "MID"
        return "LEAF"

    def __post_init__(self):
        # ensure no silent downgrade of review requirement
        if self.required_review_depth == "INDEPENDENT" and self.required_test_depth == "LEAF":
            # allowed: a leaf may still demand independent review if blast radius is authority/security
            pass


# NOTE: AffectedSurface.make uses a slightly awkward keyword dance to keep the
# signature stable; downstream code prefers centrality_tier() over raw depth.