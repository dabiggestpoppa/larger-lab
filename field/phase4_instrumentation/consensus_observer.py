"""
4_instrumentation.consensus_observer
=====================================
Multi-agent consensus tracking — observes and records consensus decisions
across field agents. Proposals, votes, timeouts, and history.

Status: IMPLEMENTED
"""
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.consensus_observer")


class Proposal(BaseModel):
    proposal_id: str
    proposal_type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    votes: Dict[str, bool] = Field(default_factory=dict)
    status: str = "pending"  # pending, reached, rejected, expired
    created_at: str = ""
    resolved_at: str = ""
    total_agents: int = 0


class ConsensusObserverConfig(BaseModel):
    """Configuration for consensus_observer."""
    enabled: bool = True
    consensus_threshold: float = 0.66
    vote_timeout_sec: int = 300
    max_proposals: int = 1000


class ConsensusObserverModule:
    """Multi-agent consensus tracking engine."""

    def __init__(self):
        self.config = ConsensusObserverConfig()
        self.running = False
        self._proposals: Dict[str, Proposal] = {}
        self._lock = Lock()
        self._history: List[str] = []

    def start(self) -> None:
        self.running = True
        logger.info("ConsensusObserver started (threshold=%.0f%%)",
                     self.config.consensus_threshold * 100)

    def stop(self) -> None:
        self.running = False
        logger.info("ConsensusObserver stopped (%d proposals total)",
                     len(self._proposals))

    def propose(self, proposal_id: str, proposal_type: str,
                data: Optional[Dict] = None, total_agents: int = 0) -> Proposal:
        with self._lock:
            if len(self._proposals) >= self.config.max_proposals:
                # Evict oldest resolved/expired
                evictable = [k for k, v in self._proposals.items()
                             if v.status in ("reached", "rejected", "expired")]
                if evictable:
                    del self._proposals[evictable[0]]

            now = datetime.now(timezone.utc).isoformat()
            p = Proposal(
                proposal_id=proposal_id,
                proposal_type=proposal_type,
                data=data or {},
                total_agents=total_agents,
                created_at=now,
            )
            self._proposals[proposal_id] = p
            logger.debug("Proposal created: %s (%s)", proposal_id, proposal_type)
            return p

    def vote(self, proposal_id: str, agent_id: str,
             approve: bool) -> Optional[str]:
        with self._lock:
            p = self._proposals.get(proposal_id)
            if not p or p.status != "pending":
                return None
            p.votes[agent_id] = approve
            return self._check_consensus(p)

    def _check_consensus(self, p: Proposal) -> str:
        if not p.votes:
            return p.status
        yes = sum(1 for v in p.votes.values() if v)
        total = max(p.total_agents, len(p.votes))
        ratio = yes / total if total else 0.0
        now = datetime.now(timezone.utc).isoformat()

        if ratio >= self.config.consensus_threshold:
            p.status = "reached"
            p.resolved_at = now
            self._history.append(p.proposal_id)
            logger.info("Consensus REACHED on %s (%.0f%%)", p.proposal_id, ratio * 100)
        elif (len(p.votes) - yes) / total > (1 - self.config.consensus_threshold):
            p.status = "rejected"
            p.resolved_at = now
            self._history.append(p.proposal_id)
            logger.info("Consensus REJECTED on %s", p.proposal_id)
        return p.status

    def get_consensus(self, proposal_id: str) -> Optional[Dict]:
        with self._lock:
            p = self._proposals.get(proposal_id)
            if not p:
                return None
            return {
                "proposal_id": p.proposal_id,
                "type": p.proposal_type,
                "status": p.status,
                "yes_votes": sum(1 for v in p.votes.values() if v),
                "no_votes": sum(1 for v in p.votes.values() if not v),
                "total_votes": len(p.votes),
                "created_at": p.created_at,
                "resolved_at": p.resolved_at,
            }

    def get_pending(self) -> List[Dict]:
        self._expire_old()
        with self._lock:
            return [self.get_consensus(pid)
                    for pid, p in self._proposals.items()
                    if p.status == "pending"]

    def get_history(self, n: int = 20) -> List[Dict]:
        with self._lock:
            ids = self._history[-n:]
            return [self.get_consensus(pid)
                    for pid in reversed(ids)
                    if pid in self._proposals]

    def _expire_old(self):
        cutoff = datetime.now(timezone.utc) - timedelta(
            seconds=self.config.vote_timeout_sec)
        with self._lock:
            for p in self._proposals.values():
                if p.status == "pending" and p.created_at:
                    try:
                        created = datetime.fromisoformat(p.created_at)
                        if created.replace(tzinfo=timezone.utc) < cutoff:
                            p.status = "expired"
                            p.resolved_at = datetime.now(timezone.utc).isoformat()
                            self._history.append(p.proposal_id)
                            logger.debug("Proposal expired: %s", p.proposal_id)
                    except (ValueError, TypeError):
                        pass

    def get_stats(self) -> Dict:
        with self._lock:
            statuses = defaultdict(int)
            for p in self._proposals.values():
                statuses[p.status] += 1
            return {
                "total_proposals": len(self._proposals),
                "pending": statuses.get("pending", 0),
                "reached": statuses.get("reached", 0),
                "rejected": statuses.get("rejected", 0),
                "expired": statuses.get("expired", 0),
            }
