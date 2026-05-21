"""
Phase 11.1 — Entropy Monitor
Monitors system entropy for stability indicators.
"""

import time
import hashlib
import sqlite3
import math
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class EntropyReading:
    """Entropy reading at a point in time."""
    timestamp: float
    entropy_value: float
    component: str
    details: Dict[str, Any]


class EntropyMonitor:
    """
    Monitors system entropy for stability indicators.
    Part of Phase 11.1 long-horizon testing.
    """
    
    def __init__(self, db_path: str = "stability/entropy_history.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entropy_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                entropy_value REAL,
                component TEXT,
                details TEXT
            )
        """)
        conn.commit()
        conn.close()
        
    def _calculate_entropy(self, data: List) -> float:
        """Calculate Shannon entropy of data."""
        if not data:
            return 0.0
        
        # Count frequencies
        freq: Dict[str, int] = {}
        for item in data:
            key = str(item)
            freq[key] = freq.get(key, 0) + 1
        
        # Calculate Shannon entropy
        total = len(data)
        entropy = 0.0
        for count in freq.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        return entropy
    
    def record_entropy(self, data: List, component: str, 
                       details: Dict = None) -> EntropyReading:
        """Record entropy reading."""
        entropy = self._calculate_entropy(data)
        
        reading = EntropyReading(
            timestamp=time.time(),
            entropy_value=entropy,
            component=component,
            details=details or {}
        )
        
        self._save_reading(reading)
        return reading
    
    def _save_reading(self, reading: EntropyReading):
        """Save entropy reading to database."""
        import json
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO entropy_history (timestamp, entropy_value, component, details)
            VALUES (?, ?, ?, ?)
        """, (reading.timestamp, reading.entropy_value, reading.component, json.dumps(reading.details)))
        conn.commit()
        conn.close()
    
    def get_entropy_trend(self, hours: int = 24) -> List[EntropyReading]:
        """Get entropy trend over specified hours."""
        cutoff = time.time() - (hours * 3600)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, entropy_value, component, details FROM entropy_history
            WHERE timestamp > ? ORDER BY timestamp
        """, (cutoff,))
        
        import json
        results = []
        for row in cursor.fetchall():
            results.append(EntropyReading(
                timestamp=row[0],
                entropy_value=row[1],
                component=row[2],
                details=json.loads(row[3])
            ))
        conn.close()
        return results
    
    def get_average_entropy(self, hours: int = 24) -> float:
        """Get average entropy over period."""
        trend = self.get_entropy_trend(hours)
        if not trend:
            return 0.0
        return sum(r.entropy_value for r in trend) / len(trend)
    
    def is_stable(self, threshold: float = 2.0) -> bool:
        """Check if entropy is within stable range."""
        return self.get_average_entropy() < threshold


if __name__ == "__main__":
    monitor = EntropyMonitor()
    
    # Example usage
    monitor.record_entropy(["a", "b", "a", "c", "a"], "test_data")
    monitor.record_entropy(["x", "x", "x", "x"], "uniform_data")
    
    print(f"Average entropy: {monitor.get_average_entropy():.3f}")
    print(f"Is stable: {monitor.is_stable()}")