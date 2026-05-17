"""
OCE Consensus Engine — Phase 8.2
=================================
Multi-agent consensus for distributed governance decisions.

Provides:
- Voting on governance topics
- Quorum detection
- Conflict resolution strategies
- Voting history
"""

import sqlite3
import uuid
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.consensus")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "consensus.db"


class ConsensusStrategy(str, Enum):
    MAJORITY = "majority"       # >50%
    WEIGHTED = "weighted"       # Weighted by trust level
    UNANIMOUS = "unanimous"     # 100%


class ConsensusStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


class VoteValue(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


class ConsensusEngine:
    """Singleton consensus engine for OCE."""

    _instance: Optional["ConsensusEngine"] = None
    _lock = Lock()

    def __new__(cls) -> "ConsensusEngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info("ConsensusEngine initialized")

    def _init_db(self):
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS votes (
                    vote_id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    voter_id TEXT NOT NULL,
                    vote TEXT NOT NULL,
                    weight REAL DEFAULT 1.0,
                    reason TEXT DEFAULT '',
                    timestamp TEXT NOT NULL,
                    UNIQUE(topic, voter_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS consensus_topics (
                    topic TEXT PRIMARY KEY,
                    description TEXT,
                    strategy TEXT NOT NULL DEFAULT 'majority',
                    quorum_threshold REAL DEFAULT 0.66,
                    status TEXT NOT NULL DEFAULT 'open',
                    created_at TEXT NOT NULL,
                    resolved_at TEXT,
                    result TEXT
                )
            """)
            conn.commit()

    def create_topic(self, topic: str, description: str = "",
                     strategy: str = "majority", quorum_threshold: float = 0.66) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO consensus_topics (topic, description, strategy, quorum_threshold, status, created_at) VALUES (?, ?, ?, ?, 'open', ?)",
                (topic, description, strategy, quorum_threshold, now),
            )
            conn.commit()

    def submit_vote(self, topic: str, voter_id: str, vote: str,
                    weight: float = 1.0, reason: str = "") -> Dict:
        """Submit a vote on a topic. Returns consensus status."""
        vote_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO votes (vote_id, topic, voter_id, vote, weight, reason, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (vote_id, topic, voter_id, vote, weight, reason, now),
            )
            conn.commit()

        result = self.get_consensus(topic)
        logger.info(f"Vote submitted on '{topic}' by {voter_id}: {vote} (consensus: {result['status']})")
        return result

    def get_consensus(self, topic: str) -> Dict:
        """Check consensus status for a topic."""
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            topic_row = conn.execute("SELECT * FROM consensus_topics WHERE topic = ?", (topic,)).fetchone()
            if not topic_row:
                return {"topic": topic, "status": "not_found", "message": "Topic does not exist"}

            strategy = topic_row["strategy"]
            quorum = topic_row["quorum_threshold"]

            votes = conn.execute("SELECT * FROM votes WHERE topic = ?", (topic,)).fetchall()
            total_voters = conn.execute("SELECT COUNT(DISTINCT voter_id) FROM votes WHERE topic = ?", (topic,)).fetchone()[0]

            if total_voters == 0:
                return {"topic": topic, "status": "no_votes", "strategy": strategy, "quorum": quorum}

            approve_weight = sum(v["weight"] for v in votes if v["vote"] == VoteValue.APPROVE.value)
            reject_weight = sum(v["weight"] for v in votes if v["vote"] == VoteValue.REJECT.value)
            abstain_weight = sum(v["weight"] for v in votes if v["vote"] == VoteValue.ABSTAIN.value)
            total_weight = approve_weight + reject_weight + abstain_weight

            if total_weight == 0:
                return {"topic": topic, "status": "no_valid_votes", "strategy": strategy}

            approve_ratio = approve_weight / total_weight
            reject_ratio = reject_weight / total_weight

            # Determine consensus based on strategy
            if strategy == ConsensusStrategy.UNANIMOUS.value:
                consensus_reached = approve_ratio >= quorum and reject_weight == 0
                rejected = reject_weight > 0
            elif strategy == ConsensusStrategy.WEIGHTED.value:
                consensus_reached = approve_ratio >= quorum
                rejected = reject_ratio > (1 - quorum)
            else:  # MAJORITY
                consensus_reached = approve_ratio > 0.5
                rejected = reject_ratio > 0.5

            status = "pending"
            result = None
            if consensus_reached:
                status = "approved"
                result = "approve"
            elif rejected:
                status = "rejected"
                result = "reject"

            return {
                "topic": topic,
                "status": status,
                "result": result,
                "strategy": strategy,
                "quorum": quorum,
                "total_voters": total_voters,
                "approve_weight": round(approve_weight, 2),
                "reject_weight": round(reject_weight, 2),
                "abstain_weight": round(abstain_weight, 2),
                "approve_ratio": round(approve_ratio, 3),
                "reject_ratio": round(reject_ratio, 3),
                "consensus_reached": consensus_reached,
            }

    def resolve_conflict(self, topic: str, strategy: str = "majority") -> Dict:
        """Resolve a conflicted topic using the specified strategy."""
        result = self.get_consensus(topic)
        now = datetime.now(timezone.utc).isoformat()

        if result["status"] == "approved":
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute("UPDATE consensus_topics SET status = 'resolved', resolved_at = ?, result = 'approved' WHERE topic = ?",
                             (now, topic))
                conn.commit()
            result["status"] = "resolved"
            result["resolution"] = "approved"
        elif result["status"] == "rejected":
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute("UPDATE consensus_topics SET status = 'resolved', resolved_at = ?, result = 'rejected' WHERE topic = ?",
                             (now, topic))
                conn.commit()
            result["status"] = "resolved"
            result["resolution"] = "rejected"
        else:
            result["resolution"] = "inconclusive"

        logger.info(f"Conflict resolved on '{topic}': {result.get('resolution', 'inconclusive')}")
        return result

    def get_voting_history(self, limit: int = 50) -> List[Dict]:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM votes ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_open_topics(self) -> List[Dict]:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM consensus_topics WHERE status = 'open' ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]


def get_consensus_engine() -> ConsensusEngine:
    return ConsensusEngine()
