"""
6_resonance.collective_reasoning
==================================
Multi-agent collective reasoning engine.

Manages structured group reasoning sessions where multiple agents
contribute arguments, evidence, and counterarguments to reach
collective conclusions. Supports dialectical reasoning modes:
- deliberation (weigh pros/cons)
- debate (adversarial argumentation)
- consensus (converge on agreement)
- brainstorm (divergent idea generation)

Each session has a topic, participating agents, reasoning mode,
and tracks the evolving state of arguments toward a conclusion.
"""

import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger("field.resonance.collective_reasoning")


class ReasoningMode(str, Enum):
    DELIBERATION = "deliberation"
    DEBATE = "debate"
    CONSENSUS = "consensus"
    BRAINSTORM = "brainstorm"


class ArgumentType(str, Enum):
    CLAIM = "claim"
    EVIDENCE = "evidence"
    COUNTER = "counter"
    REBUTTAL = "rebuttal"
    SYNTHESIS = "synthesis"


class Argument(BaseModel):
    argument_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    agent_id: str
    arg_type: ArgumentType
    content: str
    strength: float = 0.5  # 0.0 to 1.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    targets: List[str] = Field(default_factory=list)  # argument_ids this responds to
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ReasoningSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    topic: str
    mode: ReasoningMode = ReasoningMode.DELIBERATION
    participants: List[str] = Field(default_factory=list)
    arguments: List[Argument] = Field(default_factory=list)
    conclusion: Optional[str] = None
    confidence: float = 0.0
    status: str = "active"  # active, concluded, deadlocked
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CollectiveReasoningConfig(BaseModel):
    """Configuration for collective_reasoning."""
    enabled: bool = True
    max_sessions: int = 100
    max_arguments_per_session: int = 500
    consensus_threshold: float = 0.7
    deadlock_threshold: int = 50  # max rounds without progress


class CollectiveReasoningModule:
    """Multi-agent collective reasoning engine."""

    def __init__(self):
        self.config = CollectiveReasoningConfig()
        self.running = False
        self._lock = Lock()
        self._sessions: Dict[str, ReasoningSession] = {}
        self._agent_sessions: Dict[str, List[str]] = defaultdict(list)  # agent_id -> [session_ids]
        self._stats: Dict[str, int] = defaultdict(int)

    def start(self) -> None:
        """Start the module."""
        self.running = True
        logger.info("CollectiveReasoningModule started")

    def stop(self) -> None:
        """Stop the module."""
        self.running = False
        logger.info("CollectiveReasoningModule stopped")

    def create_session(self, topic: str, mode: ReasoningMode = ReasoningMode.DELIBERATION,
                       participants: Optional[List[str]] = None) -> str:
        """
        Create a new collective reasoning session.

        Args:
            topic: The topic or question to reason about.
            mode: Reasoning mode (deliberation, debate, consensus, brainstorm).
            participants: List of agent IDs participating.

        Returns:
            The session_id.
        """
        with self._lock:
            if len(self._sessions) >= self.config.max_sessions:
                # Evict oldest concluded session
                oldest = sorted(
                    (s for s in self._sessions.values() if s.status != "active"),
                    key=lambda s: s.updated_at
                )
                if oldest:
                    del self._sessions[oldest[0].session_id]
                    logger.debug("Evicted old session %s", oldest[0].session_id)

            session = ReasoningSession(
                topic=topic,
                mode=mode,
                participants=participants or [],
            )
            self._sessions[session.session_id] = session
            for agent_id in (participants or []):
                self._agent_sessions[agent_id].append(session.session_id)
            self._stats["sessions_created"] += 1
            logger.info("Session %s created: '%s' [%s]", session.session_id, topic, mode)
            return session.session_id

    def submit_argument(self, session_id: str, agent_id: str, arg_type: ArgumentType,
                        content: str, strength: float = 0.5,
                        targets: Optional[List[str]] = None, **metadata) -> Optional[str]:
        """
        Submit an argument to a reasoning session.

        Args:
            session_id: The session to contribute to.
            agent_id: The contributing agent.
            arg_type: Type of argument (claim, evidence, counter, rebuttal, synthesis).
            content: The argument text.
            strength: Argument strength 0.0-1.0.
            targets: Argument IDs this responds to.

        Returns:
            The argument_id, or None if session is not active.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                logger.warning("Session %s not found", session_id)
                return None
            if session.status != "active":
                logger.warning("Session %s is %s, not accepting arguments", session_id, session.status)
                return None
            if len(session.arguments) >= self.config.max_arguments_per_session:
                logger.warning("Session %s argument limit reached", session_id)
                return None

            arg = Argument(
                agent_id=agent_id,
                arg_type=arg_type,
                content=content,
                strength=max(0.0, min(1.0, strength)),
                targets=targets or [],
                metadata=metadata,
            )
            session.arguments.append(arg)
            session.updated_at = datetime.now(timezone.utc).isoformat()
            self._stats["arguments_submitted"] += 1

            # Auto-evaluate consensus in consensus mode
            if session.mode == ReasoningMode.CONSENSUS:
                self._check_consensus(session_id)

            logger.debug("Argument %s in session %s: %s [%s]", arg.argument_id, session_id, agent_id, arg_type)
            return arg.argument_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session details."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            return session.model_dump()

    def get_session_arguments(self, session_id: str, arg_type: Optional[ArgumentType] = None) -> List[Dict]:
        """Get arguments for a session, optionally filtered by type."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return []
            args = session.arguments
            if arg_type:
                args = [a for a in args if a.arg_type == arg_type]
            return [a.model_dump() for a in args]

    def conclude_session(self, session_id: str, conclusion: str,
                         confidence: float = 0.5) -> bool:
        """
        Conclude a reasoning session with a final conclusion.

        Args:
            session_id: The session to conclude.
            conclusion: The final conclusion text.
            confidence: Confidence in the conclusion 0.0-1.0.

        Returns:
            True if concluded successfully.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            session.conclusion = conclusion
            session.confidence = max(0.0, min(1.0, confidence))
            session.status = "concluded"
            session.updated_at = datetime.now(timezone.utc).isoformat()
            self._stats["sessions_concluded"] += 1
            logger.info("Session %s concluded (confidence=%.3f)", session_id, confidence)
            return True

    def get_argument_map(self, session_id: str) -> Dict[str, List[str]]:
        """
        Get the argument response map for a session.

        Returns:
            Dict mapping argument_ids to list of response argument_ids.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return {}
            arg_map: Dict[str, List[str]] = defaultdict(list)
            for arg in session.arguments:
                for target in arg.targets:
                    arg_map[target].append(arg.argument_id)
            return dict(arg_map)

    def get_agent_contributions(self, agent_id: str) -> Dict[str, Any]:
        """Get all contributions by an agent across sessions."""
        with self._lock:
            session_ids = self._agent_sessions.get(agent_id, [])
            contributions = {}
            for sid in session_ids:
                session = self._sessions.get(sid)
                if session:
                    agent_args = [a.model_dump() for a in session.arguments if a.agent_id == agent_id]
                    contributions[sid] = {
                        "topic": session.topic,
                        "mode": session.mode,
                        "argument_count": len(agent_args),
                        "arguments": agent_args,
                    }
            return contributions

    def get_stats(self) -> Dict[str, Any]:
        """Get module statistics."""
        with self._lock:
            active = sum(1 for s in self._sessions.values() if s.status == "active")
            concluded = sum(1 for s in self._sessions.values() if s.status == "concluded")
            deadlocked = sum(1 for s in self._sessions.values() if s.status == "deadlocked")
            total_args = sum(len(s.arguments) for s in self._sessions.values())
            # Merge counters into top-level dict for test compatibility
            return {
                "total_sessions": len(self._sessions),
                "active_sessions": active,
                "concluded_sessions": concluded,
                "deadlocked_sessions": deadlocked,
                "total_arguments": total_args,
                "total_participants": len(self._agent_sessions),
                **self._stats,
            }

    # ── Proposal / Voting / Debate API (test-compatible) ──────────

    def submit_proposal(self, agent_id: str, content: str,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Submit a proposal — creates a consensus session behind the scenes.

        Returns:
            proposal_id (same as session_id).
        """
        pid = self.create_session(topic=content, mode=ReasoningMode.CONSENSUS,
                                  participants=[agent_id])
        # Store metadata on the session
        with self._lock:
            session = self._sessions.get(pid)
            if session and metadata:
                session.arguments.append(Argument(
                    agent_id=agent_id,
                    arg_type=ArgumentType.CLAIM,
                    content=content,
                    strength=1.0,
                    metadata=metadata,
                ))
        self._stats["total_proposals"] = self._stats.get("total_proposals", 0) + 1
        return pid

    def get_proposals(self) -> List[Dict[str, Any]]:
        """Get all proposals (consensus sessions) as dicts."""
        with self._lock:
            return [
                {
                    "proposal_id": sid,
                    "topic": s.topic,
                    "status": s.status,
                    "created_at": s.created_at,
                }
                for sid, s in self._sessions.items()
            ]

    def cast_vote(self, agent_id: str, proposal_id: str, vote: str,
                  weight: float = 1.0) -> bool:
        """Cast a vote on a proposal.

        Args:
            agent_id: Voting agent.
            proposal_id: The proposal/session ID.
            vote: 'agree', 'disagree', or 'abstain'.
            weight: Vote weight 0.0-1.0.

        Returns:
            True if vote recorded.
        """
        with self._lock:
            session = self._sessions.get(proposal_id)
            if not session or session.status != "active":
                return False

        arg_type = ArgumentType.EVIDENCE if vote == "agree" else ArgumentType.COUNTER
        self.submit_argument(
            session_id=proposal_id,
            agent_id=agent_id,
            arg_type=arg_type,
            content=f"Vote: {vote}",
            strength=weight,
        )
        self._stats["total_votes"] = self._stats.get("total_votes", 0) + 1
        return True

    def get_consensus(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Get consensus result for a proposal.

        Returns:
            Dict with status, agree_count, disagree_count, etc.
        """
        with self._lock:
            session = self._sessions.get(proposal_id)
            if not session:
                return None

            agree_count = sum(1 for a in session.arguments
                              if a.arg_type == ArgumentType.EVIDENCE)
            disagree_count = sum(1 for a in session.arguments
                                 if a.arg_type == ArgumentType.COUNTER)
            total = agree_count + disagree_count

            if total == 0:
                return {"status": "pending", "agree_count": 0, "disagree_count": 0}

            agree_ratio = agree_count / total
            if agree_ratio >= self.config.consensus_threshold:
                status = "consensus"
            elif disagree_count > agree_count:
                status = "rejected"
            else:
                status = "pending"

            return {
                "status": status,
                "agree_count": agree_count,
                "disagree_count": disagree_count,
                "total_votes": total,
                "confidence": round(agree_ratio, 3),
            }

    def get_dissent_flags(self) -> List[Dict[str, Any]]:
        """Get all dissent flags — agents who voted disagree.

        Returns:
            List of dicts with agent_id, proposal_id, reason.
        """
        flags = []
        with self._lock:
            for sid, session in self._sessions.items():
                for arg in session.arguments:
                    if arg.arg_type == ArgumentType.COUNTER:
                        flags.append({
                            "agent_id": arg.agent_id,
                            "proposal_id": sid,
                            "reason": arg.content,
                        })
        return flags

    def open_debate(self, proposal_id: str, agent_id: str, argument: str) -> str:
        """Open a debate thread on a proposal.

        Returns:
            debate_thread_id (same as the opening argument's ID).
        """
        arg_id = self.submit_argument(
            session_id=proposal_id,
            agent_id=agent_id,
            arg_type=ArgumentType.COUNTER,
            content=argument,
        )
        self._stats["total_debates"] = self._stats.get("total_debates", 0) + 1
        return arg_id or str(uuid.uuid4())[:8]

    def reply_to_debate(self, debate_id: str, agent_id: str, argument: str) -> bool:
        """Reply to a debate thread.

        Returns:
            True if reply recorded.
        """
        # Find the session containing this debate
        with self._lock:
            for sid, session in self._sessions.items():
                if any(a.argument_id == debate_id for a in session.arguments):
                    self.submit_argument(
                        session_id=sid,
                        agent_id=agent_id,
                        arg_type=ArgumentType.REBUTTAL,
                        content=argument,
                        targets=[debate_id],
                    )
                    return True
        return False

    def get_debate_thread(self, debate_id: str) -> Optional[Dict[str, Any]]:
        """Get a debate thread by ID.

        Returns:
            Dict with thread info and replies.
        """
        with self._lock:
            for sid, session in self._sessions.items():
                for arg in session.arguments:
                    if arg.argument_id == debate_id:
                        replies = [
                            a.model_dump() for a in session.arguments
                            if debate_id in a.targets
                        ]
                        return {
                            "debate_id": debate_id,
                            "proposal_id": sid,
                            "opening_argument": arg.content,
                            "replies": replies,
                        }
        return None

    def _check_consensus(self, session_id: str) -> None:
        """Internal: check if consensus has been reached in a session."""
        session = self._sessions.get(session_id)
        if not session or session.mode != ReasoningMode.CONSENSUS:
            return

        # Compute average argument strength as proxy for consensus
        if len(session.arguments) >= 3:
            avg_strength = sum(a.strength for a in session.arguments) / len(session.arguments)
            if avg_strength >= self.config.consensus_threshold:
                session.status = "concluded"
                session.confidence = avg_strength
                session.conclusion = f"Consensus reached with avg strength {avg_strength:.3f}"
                session.updated_at = datetime.now(timezone.utc).isoformat()
                self._stats["sessions_concluded"] += 1
                logger.info("Session %s auto-concluded by consensus (%.3f)", session_id, avg_strength)
