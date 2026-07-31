"""
OCE Governance Engine — Phase 8.1
===================================
Self-governance layer for Sovereign Coevolution.

Provides:
- Policy self-modification with approval workflow
- MAD override capability
- Sovereignty boundary enforcement
- Proposal lifecycle management
"""

import sqlite3
import uuid
import logging
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("oce.governance")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "governance.db"


class ProposalStatus(str, Enum):
    PROPOSED = "proposed"
    VOTING = "voting"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"
    EXPIRED = "expired"
    OVERRIDDEN = "overridden"


class ProposalType(str, Enum):
    POLICY_CHANGE = "policy_change"
    DRIFT_CONFIG = "drift_config"
    HEALING_STRATEGY = "healing_strategy"
    TOPOLOGY_MUTATION = "topology_mutation"
    RESOURCE_ALLOCATION = "resourceallocation"
    ATTRACTOR_UPDATE = "attractor_update"
    SOVEREIGNTY_BOUNDARY = "sovereignty_boundary"


# — Sovereignty Boundaries —
# These can NEVER be self-modified. Only MAD can change them.
SOVEREIGN_BOUNDARIES = {
    "max_workers": {"min": 1, "max": 32, "description": "Worker pool size limits"},
    "max_entropy_budget": {"min": 100, "max": 100000, "description": "Total entropy budget"},
    "max_retry_count": {"min": 0, "max": 10, "description": "Maximum retry attempts"},
    "sandbox_required": {"type": "bool", "description": "Whether sandboxing is required"},
    "mad_override_enabled": {"type": "bool", "immutable": True, "description": "MAD override can never be disabled"},
    "max_policy_self_modifications_per_hour": {"min": 1, "max": 60, "description": "Rate limit for self-modification"},
}


class GovernanceEngine:
    """Singleton governance engine for OCE."""

    _instance: Optional["GovernanceEngine"] = None
    _lock = Lock()

    def __new__(cls) -> "GovernanceEngine":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True
        self._proposal_handlers: Dict[str, Callable] = {}
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info("GovernanceEngine initialized")

    def _init_db(self):
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS proposals (
                    proposal_id TEXT PRIMARY KEY,
                    proposal_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    changes_json TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    proposer TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'proposed',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    applied_at TEXT,
                    overridden_at TEXT,
                    override_reason TEXT,
                    required_approvals INTEGER DEFAULT 1,
                    current_approvals INTEGER DEFAULT 0
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_log (
                    log_id TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

    def _log(self, action: str, details: Dict, actor: str):
        log_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                "INSERT INTO governance_log (log_id, action, details_json, actor, timestamp) VALUES (?, ?, ?, ?, ?)",
                (log_id, action, str(details), actor, now),
            )
            conn.commit()

    def _check_sovereignty(self, proposal_type: str, changes: Dict) -> None:
        """Check if changes violate sovereignty boundaries. Raises ValueError if violated."""
        if proposal_type == ProposalType.SOVEREIGNTY_BOUNDARY.value:
            raise ValueError("Sovereignty boundaries are immutable — only MAD can change these directly")

        for key, value in changes.items():
            if key in SOVEREIGN_BOUNDARIES:
                boundary = SOVEREIGN_BOUNDARIES[key]
                if boundary.get("immutable", False):
                    raise ValueError(f"'{key}' is an immutable sovereignty boundary — cannot be self-modified")
                if "min" in boundary and value < boundary["min"]:
                    raise ValueError(f"'{key}' value {value} below minimum {boundary['min']}")
                if "max" in boundary and value > boundary["max"]:
                    raise ValueError(f"'{key}' value {value} exceeds maximum {boundary['max']}")

    def propose_policy_change(
        self,
        proposal_type: str,
        title: str,
        description: str,
        changes: Dict[str, Any],
        reason: str,
        proposer: str = "oce-autonomous",
        required_approvals: int = 1,
    ) -> str:
        """Submit a governance proposal. Returns proposal_id."""
        self._check_sovereignty(proposal_type, changes)

        proposal_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute(
                """INSERT INTO proposals
                (proposal_id, proposal_type, title, description, changes_json, reason, proposer, status, created_at, updated_at, required_approvals)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (proposal_id, proposal_type, title, description, str(changes), reason, proposer, ProposalStatus.PROPOSED.value, now, now, required_approvals),
            )
            conn.commit()

        self._log("proposal_submitted", {"proposal_id": proposal_id, "type": proposal_type, "title": title}, proposer)
        logger.info(f"Governance proposal submitted: {proposal_id} ({proposal_type})")
        return proposal_id

    def approve_proposal(self, proposal_id: str, approver: str) -> bool:
        """Approve a governance proposal. Returns True if fully approved."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(DB_PATH)) as conn:
            row = conn.execute("SELECT status, required_approvals, current_approvals FROM proposals WHERE proposal_id = ?", (proposal_id,)).fetchone()
            if not row:
                raise ValueError(f"Proposal {proposal_id} not found")
            status, required, current = row
            if status != ProposalStatus.PROPOSED.value and status != ProposalStatus.VOTING.value:
                raise ValueError(f"Proposal {proposal_id} is {status}, cannot approve")

            new_approvals = current + 1
            if new_approvals >= required:
                new_status = ProposalStatus.APPROVED.value
            else:
                new_status = ProposalStatus.VOTING.value

            conn.execute("UPDATE proposals SET status = ?, current_approvals = ?, updated_at = ? WHERE proposal_id = ?",
                         (new_status, new_approvals, now, proposal_id))
            conn.commit()

        self._log("proposal_approved", {"proposal_id": proposal_id, "approver": approver, "fully_approved": new_approvals >= required}, approver)
        return new_approvals >= required

    def reject_proposal(self, proposal_id: str, rejecter: str, reason: str = "") -> None:
        """Reject a governance proposal."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("UPDATE proposals SET status = ?, updated_at = ? WHERE proposal_id = ?",
                         (ProposalStatus.REJECTED.value, now, proposal_id))
            conn.commit()
        self._log("proposal_rejected", {"proposal_id": proposal_id, "rejecter": rejecter, "reason": reason}, rejecter)

    def apply_approved_proposals(self) -> List[str]:
        """Apply all approved proposals. Returns list of applied proposal IDs."""
        applied = []
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(DB_PATH)) as conn:
            rows = conn.execute("SELECT proposal_id, proposal_type, changes_json FROM proposals WHERE status = ?", (ProposalStatus.APPROVED.value,)).fetchall()
            for proposal_id, proposal_type, changes_json in rows:
                try:
                    conn.execute("UPDATE proposals SET status = ?, applied_at = ?, updated_at = ? WHERE proposal_id = ?",
                                 (ProposalStatus.APPLIED.value, now, now, proposal_id))
                    applied.append(proposal_id)
                    self._log("proposal_applied", {"proposal_id": proposal_id, "type": proposal_type}, "governance-engine")
                except Exception as e:
                    logger.error(f"Failed to apply proposal {proposal_id}: {e}")
            conn.commit()
        return applied

    def override_autonomous_decision(self, decision_id: str, reason: str, mad_id: str = "mad") -> None:
        """MAD override an autonomous decision."""
        now = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.execute("UPDATE proposals SET status = ?, overridden_at = ?, override_reason = ?, updated_at = ? WHERE proposal_id = ?",
                         (ProposalStatus.OVERRIDDEN.value, now, reason, now, decision_id))
            conn.commit()
        self._log("decision_overridden", {"decision_id": decision_id, "reason": reason}, mad_id)
        logger.warning(f"MAD override: {decision_id} — {reason}")

    def get_proposal_status(self, proposal_id: str) -> Optional[Dict]:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM proposals WHERE proposal_id = ?", (proposal_id,)).fetchone()
            if row:
                return dict(row)
        return None

    def get_proposal(self, proposal_id: str) -> Optional[Dict]:
        """Alias for get_proposal_status."""
        return self.get_proposal_status(proposal_id)

    def list_proposals(self, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            if status:
                rows = conn.execute("SELECT * FROM proposals WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM proposals ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    def get_sovereignty_report(self) -> Dict:
        return {
            "boundaries": SOVEREIGN_BOUNDARIES,
            "total_boundaries": len(SOVEREIGN_BOUNDARIES),
            "immutable_boundaries": [k for k, v in SOVEREIGN_BOUNDARIES.items() if v.get("immutable", False)],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_governance_log(self, limit: int = 100) -> List[Dict]:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM governance_log ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]


def get_governance_engine() -> GovernanceEngine:
    return GovernanceEngine()
