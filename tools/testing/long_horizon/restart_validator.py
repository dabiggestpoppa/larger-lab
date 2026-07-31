"""
Phase 11.1 — Restart Validator
Validates system state after restart/recovery.
"""

import time
import hashlib
import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class RestartValidationResult:
    """Result of restart validation."""
    validation_id: str
    timestamp: float
    pre_restart_hash: str
    post_restart_hash: str
    recovery_success: bool
    time_to_recovery: float
    details: Dict[str, Any]


class RestartValidator:
    """
    Validates system state after restart/recovery.
    Part of Phase 11.1 long-horizon testing.
    """
    
    def __init__(self, db_path: str = "stability/restart_validation.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._pre_restart_state: Optional[Dict] = None
        
    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS restart_validation (
                validation_id TEXT PRIMARY KEY,
                timestamp REAL,
                pre_restart_hash TEXT,
                post_restart_hash TEXT,
                recovery_success INTEGER,
                time_to_recovery REAL,
                details TEXT
            )
        """)
        conn.commit()
        conn.close()
        
    def capture_pre_restart_state(self, state: Dict) -> str:
        """Capture state before restart."""
        self._pre_restart_state = state
        state_hash = hashlib.sha256(str(state).encode()).hexdigest()[:16]
        return state_hash
    
    def validate_restart(self, post_restart_state: Dict, 
                         recovery_time: float = 0.0) -> RestartValidationResult:
        """Validate state after restart."""
        post_hash = hashlib.sha256(str(post_restart_state).encode()).hexdigest()[:16]
        
        recovery_success = True
        if self._pre_restart_state:
            # Compare critical fields
            for key in ["identity", "goal", "phase"]:
                if self._pre_restart_state.get(key) != post_restart_state.get(key):
                    recovery_success = False
                    break
        
        result = RestartValidationResult(
            validation_id=f"restart_{int(time.time()*1000)}",
            timestamp=time.time(),
            pre_restart_hash=self._pre_restart_state.get("hash", "") if self._pre_restart_state else "",
            post_restart_hash=post_hash,
            recovery_success=recovery_success,
            time_to_recovery=recovery_time,
            details={"state_keys": list(post_restart_state.keys())}
        )
        
        self._save_result(result)
        return result
    
    def _save_result(self, result: RestartValidationResult):
        """Save validation result to database."""
        import json
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO restart_validation VALUES (
                :validation_id, :timestamp, :pre_restart_hash, :post_restart_hash,
                :recovery_success, :time_to_recovery, :details
            )
        """, {
            "validation_id": result.validation_id,
            "timestamp": result.timestamp,
            "pre_restart_hash": result.pre_restart_hash,
            "post_restart_hash": result.post_restart_hash,
            "recovery_success": 1 if result.recovery_success else 0,
            "time_to_recovery": result.time_to_recovery,
            "details": json.dumps(result.details)
        })
        conn.commit()
        conn.close()
    
    def get_success_rate(self, limit: int = 100) -> float:
        """Get restart success rate."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT recovery_success FROM restart_validation
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return 1.0
        return sum(r[0] for r in results) / len(results)


if __name__ == "__main__":
    validator = RestartValidator()
    
    # Example usage
    pre_hash = validator.capture_pre_restart_state({
        "identity": "CC",
        "goal": "stability",
        "phase": 11
    })
    
    result = validator.validate_restart({
        "identity": "CC",
        "goal": "stability",
        "phase": 11
    }, recovery_time=2.5)
    
    print(f"Restart validation: success={result.recovery_success}, time={result.time_to_recovery}s")