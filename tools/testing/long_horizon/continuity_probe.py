"""
Phase 11.1 — Continuity Probe
Probes continuity state at regular intervals for drift detection.
"""

import time
import hashlib
import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class ContinuityProbeResult:
    """Result of continuity probe."""
    probe_id: str
    timestamp: float
    identity_hash: str
    trajectory_hash: str
    goal_hash: str
    memory_hash: str
    drift_score: float
    status: str


class ContinuityProbe:
    """
    Probes continuity state at regular intervals.
    Part of Phase 11.1 long-horizon testing.
    """
    
    def __init__(self, db_path: str = "stability/continuity_probes.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._baseline: Optional[Dict[str, str]] = None
        
    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS continuity_probes (
                probe_id TEXT PRIMARY KEY,
                timestamp REAL,
                identity_hash TEXT,
                trajectory_hash TEXT,
                goal_hash TEXT,
                memory_hash TEXT,
                drift_score REAL,
                status TEXT
            )
        """)
        conn.commit()
        conn.close()
        
    def _hash_state(self, state: Dict) -> str:
        """Generate hash of state."""
        content = str(state)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def probe(self, identity: Dict, trajectory: Dict, 
              goal: Dict, memory: Dict) -> ContinuityProbeResult:
        """Run a continuity probe."""
        identity_hash = self._hash_state(identity)
        trajectory_hash = self._hash_state(trajectory)
        goal_hash = self._hash_state(goal)
        memory_hash = self._hash_state(memory)
        
        # Calculate drift from baseline
        drift_score = 0.0
        if self._baseline:
            drift_score = self._calculate_drift(
                identity_hash, trajectory_hash, goal_hash, memory_hash
            )
        else:
            self._baseline = {
                "identity": identity_hash,
                "trajectory": trajectory_hash,
                "goal": goal_hash,
                "memory": memory_hash
            }
        
        result = ContinuityProbeResult(
            probe_id=f"probe_{int(time.time()*1000)}",
            timestamp=time.time(),
            identity_hash=identity_hash,
            trajectory_hash=trajectory_hash,
            goal_hash=goal_hash,
            memory_hash=memory_hash,
            drift_score=drift_score,
            status="ok" if drift_score < 0.1 else "drift_detected"
        )
        
        self._save_result(result)
        return result
    
    def _calculate_drift(self, identity_hash: str, trajectory_hash: str,
                         goal_hash: str, memory_hash: str) -> float:
        """Calculate drift score from baseline."""
        drift = 0.0
        if self._baseline:
            if identity_hash != self._baseline["identity"]:
                drift += 0.25
            if trajectory_hash != self._baseline["trajectory"]:
                drift += 0.25
            if goal_hash != self._baseline["goal"]:
                drift += 0.25
            if memory_hash != self._baseline["memory"]:
                drift += 0.25
        return drift
    
    def _save_result(self, result: ContinuityProbeResult):
        """Save probe result to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO continuity_probes VALUES (
                :probe_id, :timestamp, :identity_hash, :trajectory_hash,
                :goal_hash, :memory_hash, :drift_score, :status
            )
        """, {
            "probe_id": result.probe_id,
            "timestamp": result.timestamp,
            "identity_hash": result.identity_hash,
            "trajectory_hash": result.trajectory_hash,
            "goal_hash": result.goal_hash,
            "memory_hash": result.memory_hash,
            "drift_score": result.drift_score,
            "status": result.status
        })
        conn.commit()
        conn.close()
    
    def get_recent_probes(self, limit: int = 100) -> List[ContinuityProbeResult]:
        """Get recent probe results."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM continuity_probes 
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append(ContinuityProbeResult(
                probe_id=row[0],
                timestamp=row[1],
                identity_hash=row[2],
                trajectory_hash=row[3],
                goal_hash=row[4],
                memory_hash=row[5],
                drift_score=row[6],
                status=row[7]
            ))
        conn.close()
        return results


if __name__ == "__main__":
    probe = ContinuityProbe()
    
    # Example usage
    result = probe.probe(
        identity={"name": "CC", "role": "Overseer"},
        trajectory={"phase": 11, "task": "continuity"},
        goal={"target": "stability"},
        memory={"recent": "probe"}
    )
    print(f"Probe {result.probe_id}: drift={result.drift_score:.2f}, status={result.status}")