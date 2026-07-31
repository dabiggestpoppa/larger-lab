"""
Phase 11.1 — Drift Tracker
Tracks drift over time and generates drift score trends.
"""

import time
import hashlib
import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class DriftScore:
    """Drift score at a point in time."""
    timestamp: float
    score: float
    component: str
    details: Dict[str, Any]


class DriftTracker:
    """
    Tracks drift over time for Phase 11.1 testing.
    """
    
    def __init__(self, db_path: str = "stability/drift_scores.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._history: List[DriftScore] = []
        
    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drift_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                score REAL,
                component TEXT,
                details TEXT
            )
        """)
        conn.commit()
        conn.close()
        
    def record_drift(self, score: float, component: str, 
                     details: Dict = None) -> DriftScore:
        """Record a drift score."""
        drift = DriftScore(
            timestamp=time.time(),
            score=score,
            component=component,
            details=details or {}
        )
        self._history.append(drift)
        self._save_drift(drift)
        return drift
    
    def _save_drift(self, drift: DriftScore):
        """Save drift to database."""
        import json
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO drift_scores (timestamp, score, component, details)
            VALUES (?, ?, ?, ?)
        """, (drift.timestamp, drift.score, drift.component, json.dumps(drift.details)))
        conn.commit()
        conn.close()
    
    def get_drift_trend(self, hours: int = 24) -> List[DriftScore]:
        """Get drift trend over specified hours."""
        cutoff = time.time() - (hours * 3600)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, score, component, details FROM drift_scores
            WHERE timestamp > ? ORDER BY timestamp
        """, (cutoff,))
        
        import json
        results = []
        for row in cursor.fetchall():
            results.append(DriftScore(
                timestamp=row[0],
                score=row[1],
                component=row[2],
                details=json.loads(row[3])
            ))
        conn.close()
        return results
    
    def get_average_drift(self, hours: int = 24) -> float:
        """Get average drift score over period."""
        trend = self.get_drift_trend(hours)
        if not trend:
            return 0.0
        return sum(d.score for d in trend) / len(trend)
    
    def get_max_drift(self, hours: int = 24) -> float:
        """Get maximum drift score over period."""
        trend = self.get_drift_trend(hours)
        if not trend:
            return 0.0
        return max(d.score for d in trend)


if __name__ == "__main__":
    tracker = DriftTracker()
    
    # Example usage
    tracker.record_drift(0.05, "identity", {"change": "minor"})
    tracker.record_drift(0.12, "memory", {"change": "moderate"})
    
    print(f"Average drift: {tracker.get_average_drift():.3f}")
    print(f"Max drift: {tracker.get_max_drift():.3f}")