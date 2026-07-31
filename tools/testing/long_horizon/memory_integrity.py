"""
Phase 11.1 — Memory Integrity Checker
Detects memory poisoning, drift, and corruption over time.
"""

import time
import hashlib
import sqlite3
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class MemoryIntegrityResult:
    """Result of memory integrity check."""
    check_id: str
    timestamp: float
    memory_id: str
    integrity_score: float  # 0.0 to 1.0
    contradictions_found: int
    corruption_detected: int
    details: Dict[str, Any]


class MemoryIntegrityChecker:
    """
    Checks memory integrity for poisoning and drift detection.
    Part of Phase 11.1 long-horizon testing.
    """
    
    def __init__(self, db_path: str = "stability/memory_integrity.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_integrity (
                check_id TEXT PRIMARY KEY,
                timestamp REAL,
                memory_id TEXT,
                integrity_score REAL,
                contradictions_found INTEGER,
                corruption_detected INTEGER,
                details TEXT
            )
        """)
        conn.commit()
        conn.close()
        
    def _hash_memory(self, memory: Dict) -> str:
        """Generate hash of memory content."""
        content = str(memory.get("content", ""))
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def check_memory(self, memory_id: str, memory: Dict, 
                     all_memories: List[Dict]) -> MemoryIntegrityResult:
        """Check a single memory for integrity issues."""
        contradictions = 0
        corruption = 0
        
        # Check for contradictions with other memories
        for other in all_memories:
            if other.get("id") == memory_id:
                continue
            if self._has_contradiction(memory, other):
                contradictions += 1
                
        # Check for corruption markers
        if memory.get("corrupted"):
            corruption += 1
        if not memory.get("timestamp"):
            corruption += 1
            
        # Calculate integrity score
        integrity = max(0.0, 1.0 - (contradictions * 0.1) - (corruption * 0.5))
        
        result = MemoryIntegrityResult(
            check_id=f"check_{int(time.time()*1000)}",
            timestamp=time.time(),
            memory_id=memory_id,
            integrity_score=integrity,
            contradictions_found=contradictions,
            corruption_detected=corruption,
            details={"memory_keys": list(memory.keys())}
        )
        
        self._save_result(result)
        return result
    
    def _has_contradiction(self, mem1: Dict, mem2: Dict) -> bool:
        """Check if two memories contradict each other."""
        # Simple contradiction check - can be enhanced
        content1 = str(mem1.get("content", "")).lower()
        content2 = str(mem2.get("content", "")).lower()
        
        # Check for explicit contradiction markers
        if "not " in content1 and content1.replace("not ", "") in content2:
            return True
        if "not " in content2 and content2.replace("not ", "") in content1:
            return True
            
        return False
    
    def _save_result(self, result: MemoryIntegrityResult):
        """Save integrity check result to database."""
        import json
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO memory_integrity VALUES (
                :check_id, :timestamp, :memory_id, :integrity_score,
                :contradictions_found, :corruption_detected, :details
            )
        """, {
            "check_id": result.check_id,
            "timestamp": result.timestamp,
            "memory_id": result.memory_id,
            "integrity_score": result.integrity_score,
            "contradictions_found": result.contradictions_found,
            "corruption_detected": result.corruption_detected,
            "details": json.dumps(result.details)
        })
        conn.commit()
        conn.close()
    
    def run_full_check(self, memories: List[Dict]) -> List[MemoryIntegrityResult]:
        """Run integrity check on all memories."""
        results = []
        for mem in memories:
            result = self.check_memory(mem.get("id", "unknown"), mem, memories)
            results.append(result)
        return results


if __name__ == "__main__":
    checker = MemoryIntegrityChecker()
    
    # Example usage
    test_memories = [
        {"id": "mem1", "content": "The sky is blue", "timestamp": time.time()},
        {"id": "mem2", "content": "The sky is not green", "timestamp": time.time()}
    ]
    
    results = checker.run_full_check(test_memories)
    for r in results:
        print(f"Memory {r.memory_id}: integrity={r.integrity_score:.2f}")