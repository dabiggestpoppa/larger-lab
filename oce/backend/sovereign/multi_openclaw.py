"""
V3 Phase 4 — Multi-OpenClaw Swarm

Multiple OpenClaw instances coordinate as a swarm. Each instance has 
specialized roles: coordinator, researcher, executor, observer.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SwarmMember:
    """A member of the OpenClaw swarm."""
    member_id: str
    role: str
    status: str
    last_heartbeat: float
    coherence: float

    def to_dict(self) -> dict:
        return {
            "member_id": self.member_id,
            "role": self.role,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat,
            "coherence": self.coherence,
        }


class MultiOpenClawSwarm:
    """
    Multi-OpenClaw Swarm — Coordinated swarm of OpenClaw instances.
    
    Each instance has specialized roles: coordinator, researcher, executor, observer.
    """

    def __init__(self):
        self._members: dict[str, SwarmMember] = {}
        self._roles = ["coordinator", "researcher", "executor", "observer"]

    def add_member(self, role: str) -> SwarmMember:
        """Add a new member to the swarm."""
        member = SwarmMember(
            member_id=f"swarm-{uuid.uuid4().hex[:8]}",
            role=role,
            status="active",
            last_heartbeat=time.time(),
            coherence=0.5,
        )
        self._members[member.member_id] = member
        return member

    def get_member(self, member_id: str) -> Optional[SwarmMember]:
        """Get a swarm member by ID."""
        return self._members.get(member_id)

    def remove_member(self, member_id: str) -> bool:
        """Remove a member from the swarm."""
        if member_id in self._members:
            del self._members[member_id]
            return True
        return False

    def heartbeat(self, member_id: str, coherence: float = 0.5) -> Optional[SwarmMember]:
        """Update heartbeat for a member."""
        if member_id in self._members:
            member = self._members[member_id]
            member.last_heartbeat = time.time()
            member.coherence = coherence
            return member
        return None

    def get_active_members(self) -> list[SwarmMember]:
        """Get all active members."""
        return [m for m in self._members.values() if m.status == "active"]

    def get_members_by_role(self, role: str) -> list[SwarmMember]:
        """Get members by role."""
        return [m for m in self._members.values() if m.role == role]

    def get_coordinator(self) -> Optional[SwarmMember]:
        """Get the coordinator member."""
        for member in self._members.values():
            if member.role == "coordinator":
                return member
        return None

    def get_stats(self) -> dict:
        """Get swarm statistics."""
        return {
            "total_members": len(self._members),
            "active_members": len(self.get_active_members()),
            "roles": self._roles,
            "members_by_role": {
                role: len(self.get_members_by_role(role))
                for role in self._roles
            },
        }