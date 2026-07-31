"""
OCE Coevolution Protocol — Phase 8.3
======================================
Multi-agent coevolution for distributed cognition.

Provides:
- Peer agent registration and discovery
- Topology synchronization
- Goal alignment negotiation
- Graceful peer failure handling
"""

import sqlite3
import uuid
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.coevolution")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "coevolution.db"


class TrustLevel(str, Enum):
    OBSERVER = "observer"       # Read-only access to shared state
    PARTICIPANT = "participant" # Can submit votes and proposals
    COOPERATOR = "cooperator"   # Can execute shared tasks
    SOVEREIGN = "sovereign"     # Full coevolution rights


class PeerStatus(str, Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    UNREACHABLE = "unreachable"
    FAILED = "failed"


class CoevolutionProtocol:
    """Singleton coevolution protocol for OCE."""

    _instance: Optional["CoevolutionProtocol"] = None
    _lock = Lock()

    def __new__(cls) -> "CoevolutionProtocol":
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
        logger.info("CoevolutionProtocol initialized")

    def _init_db(self):
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS peer_agents (
                    agent_id TEXT PRIMARY KEY,
                    label TEXT,
                    capabilities_json TEXT DEFAULT '[]',
                    trust_level TEXT NOT NULL DEFAULT 'observer',
                    status TEXT NOT NULL DEFAULT 'active',
                    last_heartbeat TEXT,
                    registered_at TEXT NOT NULL,
                    metadata_json TEXT DEFAULT '{}'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS topology_sync (
                    sync_id TEXT PRIMARY KEY,
                    source_agent TEXT NOT NULL,
                    target_agent TEXT NOT NULL,
                    topology_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    synced_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS goal_alignment (
                    alignment_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    goals_json TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'proposed',
                    created_at TEXT NOT NULL,
                    resolved_at TEXT
                )
            """)
            conn.commit()

    def register_peer_agent(
        self,
        agent_id: str,
        label: str = "",
        capabilities: List[str] = None,
        trust_level: str = "observer",
        metadata: Dict = None,
    ) -> str:
        """Register a peer agent for coevolution."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO peer_agents
                (agent_id, label, capabilities_json, trust_level, status, last_heartbeat, registered_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (agent_id, label, str(capabilities or []), trust_level, PeerStatus.ACTIVE.value, now, now, str(metadata or {})),
            )
            conn.commit()
        logger.info(f"Peer agent registered: {agent_id} (trust: {trust_level})")
        return agent_id

    def update_peer_heartbeat(self, agent_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("UPDATE peer_agents SET last_heartbeat = ?, status = ? WHERE agent_id = ?",
                         (now, PeerStatus.ACTIVE.value, agent_id))
            conn.commit()

    def update_peer_status(self, agent_id: str, status: str) -> None:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("UPDATE peer_agents SET status = ? WHERE agent_id = ?", (status, agent_id))
            conn.commit()
        logger.info(f"Peer agent {agent_id} status → {status}")

    def negotiate_topology_change(self, proposal: Dict) -> Dict:
        """Negotiate a topology change with peer agents."""
        sync_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Get all active peers
        peers = self.get_active_peers()
        results = {"sync_id": sync_id, "proposal": proposal, "peers_contacted": len(peers), "responses": []}

        for peer in peers:
            # In a real implementation, this would send the proposal to the peer
            # and wait for a response. For now, we record the sync attempt.
            with sqlite3.connect(str(DB_PATH)) as conn:
                conn.execute(
                    """INSERT INTO topology_sync
                    (sync_id, source_agent, target_agent, topology_json, status, created_at)
                    VALUES (?, ?, ?, ?, 'pending', ?)""",
                    (sync_id, "self", peer["agent_id"], str(proposal), now),
                )
                conn.commit()
            results["responses"].append({"agent_id": peer["agent_id"], "status": "pending"})

        logger.info(f"Topology change negotiation initiated: {sync_id} ({len(peers)} peers)")
        return results

    def align_goals(self, peer_agent_id: str, goals: List[str]) -> str:
        """Align operational goals with a peer agent."""
        alignment_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                "INSERT INTO goal_alignment (alignment_id, agent_id, goals_json, status, created_at) VALUES (?, ?, ?, 'proposed', ?)",
                (alignment_id, peer_agent_id, str(goals), now),
            )
            conn.commit()
        logger.info(f"Goal alignment proposed with {peer_agent_id}: {len(goals)} goals")
        return alignment_id

    def handle_peer_failure(self, agent_id: str) -> Dict:
        """Handle a peer agent failure gracefully."""
        now = datetime.now(timezone.utc).isoformat()
        self.update_peer_status(agent_id, PeerStatus.FAILED.value)

        # Get the peer's capabilities to redistribute
        peer = self.get_peer(agent_id)
        capabilities = peer.get("capabilities", []) if peer else []

        # Find tasks that were assigned to this peer
        with sqlite3.connect(str(DB_PATH)) as conn:
            pending_syncs = conn.execute(
                "SELECT * FROM topology_sync WHERE target_agent = ? AND status = 'pending'",
                (agent_id,)
            ).fetchall()

        result = {
            "agent_id": agent_id,
            "status": "failed",
            "capabilities_lost": capabilities,
            "pending_syncs_cancelled": len(pending_syncs),
            "timestamp": now,
        }

        # Cancel pending syncs
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("UPDATE topology_sync SET status = 'cancelled' WHERE target_agent = ? AND status = 'pending'", (agent_id,))
            conn.commit()

        logger.warning(f"Peer failure handled: {agent_id} — {len(capabilities)} capabilities lost, {len(pending_syncs)} syncs cancelled")
        return result

    def get_peer(self, agent_id: str) -> Optional[Dict]:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM peer_agents WHERE agent_id = ?", (agent_id,)).fetchone()
            if row:
                d = dict(row)
                d["capabilities"] = eval(d.get("capabilities_json", "[]"))
                d["metadata"] = eval(d.get("metadata_json", "{}"))
                return d
        return None

    def get_active_peers(self) -> List[Dict]:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM peer_agents WHERE status = ?", (PeerStatus.ACTIVE.value,)).fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["capabilities"] = eval(d.get("capabilities_json", "[]"))
                d["metadata"] = eval(d.get("metadata_json", "{}"))
                result.append(d)
            return result

    def get_all_peers(self) -> List[Dict]:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM peer_agents ORDER BY registered_at DESC").fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["capabilities"] = eval(d.get("capabilities_json", "[]"))
                d["metadata"] = eval(d.get("metadata_json", "{}"))
                result.append(d)
            return result

    def get_coevolution_status(self) -> Dict:
        peers = self.get_all_peers()
        active = [p for p in peers if p["status"] == PeerStatus.ACTIVE.value]
        failed = [p for p in peers if p["status"] == PeerStatus.FAILED.value]

        with sqlite3.connect(str(DB_PATH)) as conn:
            pending_syncs = conn.execute("SELECT COUNT(*) FROM topology_sync WHERE status = 'pending'").fetchone()[0]
            pending_alignments = conn.execute("SELECT COUNT(*) FROM goal_alignment WHERE status = 'proposed'").fetchone()[0]

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_peers": len(peers),
            "active_peers": len(active),
            "failed_peers": len(failed),
            "pending_syncs": pending_syncs,
            "pending_alignments": pending_alignments,
            "trust_distribution": {
                level: len([p for p in peers if p["trust_level"] == level])
                for level in ["observer", "participant", "cooperator", "sovereign"]
            },
        }


def get_coevolution_protocol() -> CoevolutionProtocol:
    return CoevolutionProtocol()
