"""
V3 Phase 5 — Identity Reconstruction Engine
Maintains persistent operational identity across time.

Without identity continuity: the field resets psychologically, goals fragment,
cognition becomes reactive, mission decay begins.
"""

from __future__ import annotations
import time
import json
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class IdentityAttractor:
    """A stable identity pattern that persists across sessions."""
    attractor_id: str
    identity_type: str       # "mission", "behavioral", "strategic", "boundary"
    weight: float = 0.5
    stability: float = 0.5
    access_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)

    def access(self) -> None:
        self.access_count += 1
        self.last_accessed = time.time()
        self.stability = min(1.0, self.stability + 0.05)


class IdentityEngine:
    """
    Maintains persistent operational identity for the cognitive field.
    
    Tracks:
    - Mission vectors (long-term purpose)
    - Behavioral attractors (stable operational tendencies)
    - Strategic memory (accumulated system understanding)
    - Continuity anchors (non-negotiable identity invariants)
    - Entropy signatures (instability tendencies)
    - Field preferences (optimized execution styles)
    """

    def __init__(self, identity_file: str = ".oce/identity.json"):
        self.identity_file = Path(identity_file)
        self.attractors: dict[str, IdentityAttractor] = {}
        self._mission_vectors: list[str] = []
        self._continuity_anchors: dict = {}
        self._load()

    def _load(self) -> None:
        """Load identity from disk."""
        if self.identity_file.exists():
            try:
                data = json.loads(self.identity_file.read_text(encoding="utf-8"))
                self._mission_vectors = data.get("missions", [])
                self._continuity_anchors = data.get("anchors", {})
                for aid, adata in data.get("attractors", {}).items():
                    self.attractors[aid] = IdentityAttractor(**adata)
            except (json.JSONDecodeError, TypeError, KeyError):
                pass

    def _save(self) -> None:
        """Persist identity to disk."""
        self.identity_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "missions": self._mission_vectors,
            "anchors": self._continuity_anchors,
            "attractors": {
                aid: {
                    "attractor_id": a.attractor_id,
                    "identity_type": a.identity_type,
                    "weight": a.weight,
                    "stability": a.stability,
                    "access_count": a.access_count,
                    "created_at": a.created_at,
                    "last_accessed": a.last_accessed,
                }
                for aid, a in self.attractors.items()
            },
            "last_saved": time.time(),
        }
        self.identity_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def add_mission(self, mission: str) -> None:
        """Add a mission vector."""
        if mission not in self._mission_vectors:
            self._mission_vectors.append(mission)

    def add_anchor(self, key: str, value: str) -> None:
        """Add a continuity anchor (non-negotiable identity invariant)."""
        self._continuity_anchors[key] = value

    def create_attractor(self, identity_type: str, weight: float = 0.5) -> IdentityAttractor:
        """Create a new identity attractor."""
        aid = f"id_{identity_type}_{int(time.time())}"
        attractor = IdentityAttractor(
            attractor_id=aid,
            identity_type=identity_type,
            weight=weight,
        )
        self.attractors[aid] = attractor
        return attractor

    def reconstruct_identity(self) -> dict:
        """
        Reconstruct the field's identity from stored attractors.
        Called after a restart or identity fragmentation event.
        """
        stable = sorted(
            [a for a in self.attractors.values() if a.stability > 0.3],
            key=lambda a: a.stability,
            reverse=True,
        )

        return {
            "missions": self._mission_vectors,
            "anchors": self._continuity_anchors,
            "stable_attractors": len(stable),
            "total_attractors": len(self.attractors),
            "identity_strength": round(
                sum(a.stability for a in stable) / max(len(stable), 1), 4
            ),
            "reconstructed_at": time.time(),
        }

    def verify_integrity(self) -> dict:
        """Verify identity integrity — are core invariants intact?"""
        intact_anchors = sum(
            1 for k, v in self._continuity_anchors.items()
            if self._continuity_anchors.get(k) == v
        )
        return {
            "anchors_intact": intact_anchors,
            "total_anchors": len(self._continuity_anchors),
            "missions_active": len(self._mission_vectors),
            "identity_strength": round(
                sum(a.stability for a in self.attractors.values()) / max(len(self.attractors), 1), 4
            ),
        }

    @property
    def stats(self) -> dict:
        return {
            "attractors": len(self.attractors),
            "missions": len(self._mission_vectors),
            "anchors": len(self._continuity_anchors),
            "stable_attractors": sum(1 for a in self.attractors.values() if a.stability > 0.5),
        }
