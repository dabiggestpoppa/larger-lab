"""
Phase 11.1 — Continuity Checksum Engine
Tracks identity, trajectory, goal, and memory hashes for reconstruction validation.
"""

import hashlib
import json
import time
from dataclasses import dataclass, asdict
from typing import Dict, Optional, Any
from pathlib import Path


@dataclass
class ContinuityState:
    """Complete continuity state for an observer."""
    observer_id: str
    timestamp: float
    identity_hash: str
    trajectory_hash: str
    goal_hash: str
    memory_hash: str
    state_hash: str  # Combined hash of all components
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ContinuityChecksumEngine:
    """
    Generates and validates continuity checksums.
    Used for drift detection and reconstruction validation.
    """
    
    def __init__(self, db_path: str = "stability/continuity_states.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite database."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS continuity_states (
                state_id TEXT PRIMARY KEY,
                observer_id TEXT,
                identity_hash TEXT,
                trajectory_hash TEXT,
                goal_hash TEXT,
                memory_hash TEXT,
                state_hash TEXT,
                timestamp REAL,
                valid INTEGER DEFAULT 1
            )
        """)
        conn.commit()
        conn.close()
        
    def _hash_data(self, data: Any) -> str:
        """Generate SHA256 hash of data."""
        if isinstance(data, dict):
            data = json.dumps(data, sort_keys=True)
        return hashlib.sha256(str(data).encode()).hexdigest()[:16]
    
    def generate_identity_hash(self, observer_id: str, config: Dict) -> str:
        """Generate hash of observer identity."""
        identity_data = {
            "observer_id": observer_id,
            "role": config.get("role", ""),
            "capabilities": sorted(config.get("capabilities", [])),
            "created_at": config.get("created_at", 0)
        }
        return self._hash_data(identity_data)
    
    def generate_trajectory_hash(self, tasks: list, events: list) -> str:
        """Generate hash of observer trajectory."""
        trajectory_data = {
            "task_count": len(tasks),
            "last_tasks": tasks[-10:] if tasks else [],
            "event_count": len(events),
            "last_events": events[-10:] if events else []
        }
        return self._hash_data(trajectory_data)
    
    def generate_goal_hash(self, goals: list) -> str:
        """Generate hash of current goals."""
        return self._hash_data(sorted(goals))
    
    def generate_memory_hash(self, memories: list) -> str:
        """Generate hash of memory state."""
        memory_data = {
            "count": len(memories),
            "ids": sorted([m.get("id", "") for m in memories[-100:]])
        }
        return self._hash_data(memory_data)
    
    def generate_continuity_state(self, observer_id: str, 
                                   config: Dict, tasks: list, 
                                   events: list, goals: list, 
                                   memories: list) -> ContinuityState:
        """Generate complete continuity state."""
        identity_hash = self.generate_identity_hash(observer_id, config)
        trajectory_hash = self.generate_trajectory_hash(tasks, events)
        goal_hash = self.generate_goal_hash(goals)
        memory_hash = self.generate_memory_hash(memories)
        
        # Combined state hash
        state_hash = self._hash_data({
            "identity": identity_hash,
            "trajectory": trajectory_hash,
            "goal": goal_hash,
            "memory": memory_hash
        })
        
        return ContinuityState(
            observer_id=observer_id,
            timestamp=time.time(),
            identity_hash=identity_hash,
            trajectory_hash=trajectory_hash,
            goal_hash=goal_hash,
            memory_hash=memory_hash,
            state_hash=state_hash
        )
    
    def save_state(self, state: ContinuityState):
        """Persist continuity state to database."""
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO continuity_states VALUES (
                :state_id, :observer_id, :identity_hash, :trajectory_hash,
                :goal_hash, :memory_hash, :state_hash, :timestamp, :valid
            )
        """, {
            "state_id": f"state_{int(state.timestamp * 1000)}",
            **asdict(state),
            "valid": 1
        })
        conn.commit()
        conn.close()
    
    def validate_continuity(self, current_state: ContinuityState, 
                            previous_state: ContinuityState) -> Dict:
        """Compare current and previous states for drift detection."""
        drift = {}
        
        if current_state.identity_hash != previous_state.identity_hash:
            drift["identity"] = "changed"
        if current_state.trajectory_hash != previous_state.trajectory_hash:
            drift["trajectory"] = "changed"
        if current_state.goal_hash != previous_state.goal_hash:
            drift["goal"] = "changed"
        if current_state.memory_hash != previous_state.memory_hash:
            drift["memory"] = "changed"
            
        return {
            "valid": len(drift) == 0,
            "drift": drift,
            "drift_score": len(drift) / 4.0
        }


if __name__ == "__main__":
    engine = ContinuityChecksumEngine()
    
    # Example usage
    state = engine.generate_continuity_state(
        observer_id="test_observer",
        config={"role": "test", "capabilities": ["read", "write"]},
        tasks=["task1", "task2"],
        events=["event1"],
        goals=["goal1"],
        memories=[{"id": "mem1"}]
    )
    
    print(f"Generated state: {state}")
    engine.save_state(state)