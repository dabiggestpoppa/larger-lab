"""
V3 Phase 9 — Continuity Identity Engine
Maintains operational continuity.
Preserves identity and continuity across field transformations.
"""

from __future__ import annotations
import time
import hashlib
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ContinuityState:
    """A continuity checkpoint for an element."""
    state_id: str
    element_id: str
    identity_hash: str  # hash of the element's identity
    continuity_score: float  # 0-1, how continuous the element's identity is
    checkpoint_data: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    @property
    def is_continuous(self) -> bool:
        return self.continuity_score > 0.6


class ContinuityIdentityEngine:
    """
    Maintains operational continuity across field transformations.
    
    Preserves identity by tracking continuity checkpoints and detecting
    identity drift. When field elements transform (merge, split, reconfigure),
    this engine ensures their identity remains traceable.
    """

    def __init__(self):
        self._checkpoints: list[ContinuityState] = []
        self._identity_map: dict[str, str] = {}  # element_id → identity_hash

    def _compute_hash(self, state: dict) -> str:
        """Compute an identity hash from state data."""
        state_str = str(sorted(state.items()))
        return hashlib.sha256(state_str.encode()).hexdigest()[:16]

    def create_checkpoint(self, element_id: str, state: dict) -> ContinuityState:
        """Create a continuity checkpoint for an element."""
        identity_hash = self._compute_hash(state)

        # Check continuity with previous checkpoint
        prev = self._get_latest_checkpoint(element_id)
        continuity_score = 1.0
        if prev:
            if prev.identity_hash == identity_hash:
                continuity_score = 1.0
            else:
                # Compute similarity based on shared keys
                shared = sum(1 for k in state if k in prev.checkpoint_data)
                total = max(len(state), len(prev.checkpoint_data), 1)
                continuity_score = shared / total

        checkpoint = ContinuityState(
            state_id=f"chk_{int(time.time() * 1000)}",
            element_id=element_id,
            identity_hash=identity_hash,
            continuity_score=round(continuity_score, 4),
            checkpoint_data=dict(state),
        )
        self._checkpoints.append(checkpoint)
        self._identity_map[element_id] = identity_hash
        return checkpoint

    def _get_latest_checkpoint(self, element_id: str) -> Optional[ContinuityState]:
        for cp in reversed(self._checkpoints):
            if cp.element_id == element_id:
                return cp
        return None

    def verify_continuity(self, element_id: str, current_state: dict) -> ContinuityState:
        """Verify continuity of an element against its last checkpoint."""
        return self.create_checkpoint(element_id, current_state)

    def get_continuity_score(self, element_id: str) -> float:
        """Get the latest continuity score for an element."""
        cp = self._get_latest_checkpoint(element_id)
        return cp.continuity_score if cp else 0.0

    def get_discontinuous_elements(self, threshold: float = 0.5) -> list[str]:
        """Get elements with low continuity scores."""
        latest: dict[str, ContinuityState] = {}
        for cp in self._checkpoints:
            latest[cp.element_id] = cp
        return [eid for eid, cp in latest.items() if cp.continuity_score < threshold]

    def merge_identities(self, element_a: str, element_b: str,
                          merged_state: dict) -> ContinuityState:
        """Merge two element identities into one."""
        merged_hash = self._compute_hash(merged_state)
        checkpoint = ContinuityState(
            state_id=f"chk_{int(time.time() * 1000)}",
            element_id=f"{element_a}+{element_b}",
            identity_hash=merged_hash,
            continuity_score=0.5,  # merged identity starts at medium continuity
            checkpoint_data=merged_state,
        )
        self._checkpoints.append(checkpoint)
        return checkpoint

    @property
    def stats(self) -> dict:
        elements = set(cp.element_id for cp in self._checkpoints)
        discontinuous = len(self.get_discontinuous_elements())
        avg_continuity = (
            sum(cp.continuity_score for cp in self._checkpoints) / len(self._checkpoints)
            if self._checkpoints else 0.0
        )
        return {
            "total_checkpoints": len(self._checkpoints),
            "tracked_elements": len(elements),
            "discontinuous_elements": discontinuous,
            "avg_continuity": round(avg_continuity, 4),
        }
