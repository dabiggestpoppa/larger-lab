"""
Recovery Anchor Storage
=======================
Sparse persistence layer for SRRA-OPH Phase 2.

Instead of saving full conversations/transcripts, we save invariant structures:
- User preferences and priorities
- Execution logic patterns
- Repair loop behaviors
- Constraint definitions

Each anchor has a weight (importance) and tags for retrieval.
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).parent / "data" / "recovery_anchors.db"


def get_db() -> sqlite3.Connection:
    """Get database connection, creating tables if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS anchors (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            weight REAL DEFAULT 1.0,
            source TEXT DEFAULT 'system',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            tags TEXT DEFAULT '[]',
            checksum TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_anchors_weight ON anchors(weight DESC)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_anchors_source ON anchors(source)
    """)
    conn.commit()
    return conn


def _checksum(content: str) -> str:
    """Generate checksum for content integrity."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def create_anchor(content: str, weight: float = 1.0, source: str = "system",
                  tags: List[str] = None) -> Dict[str, Any]:
    """Create a new recovery anchor."""
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    anchor_id = f"anchor_{hashlib.md5(content.encode()).hexdigest()[:12]}"
    tags_json = json.dumps(tags or [])
    checksum = _checksum(content)

    conn.execute(
        """INSERT OR REPLACE INTO anchors (id, content, weight, source, created_at, updated_at, tags, checksum)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (anchor_id, content, weight, source, now, now, tags_json, checksum)
    )
    conn.commit()
    conn.close()

    return {
        "id": anchor_id,
        "content": content,
        "weight": weight,
        "source": source,
        "created_at": now,
        "tags": tags or [],
    }


def get_anchor(anchor_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single anchor by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM anchors WHERE id = ?", (anchor_id,)).fetchone()
    conn.close()
    if row:
        return _row_to_dict(row)
    return None


def get_anchors_by_tag(tag: str, min_weight: float = 0.0, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve anchors matching a tag, sorted by weight descending."""
    conn = get_db()
    rows = conn.execute(
        """SELECT * FROM anchors WHERE tags LIKE ? AND weight >= ?
           ORDER BY weight DESC LIMIT ?""",
        (f'%"{tag}"%', min_weight, limit)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_top_anchors(limit: int = 20, min_weight: float = 0.5) -> List[Dict[str, Any]]:
    """Get the highest-weight anchors (the 'core' memory)."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM anchors WHERE weight >= ? ORDER BY weight DESC LIMIT ?",
        (min_weight, limit)
    ).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def update_weight(anchor_id: str, new_weight: float) -> bool:
    """Update an anchor's weight."""
    conn = get_db()
    now = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "UPDATE anchors SET weight = ?, updated_at = ? WHERE id = ?",
        (new_weight, now, anchor_id)
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def delete_anchor(anchor_id: str) -> bool:
    """Delete an anchor."""
    conn = get_db()
    cursor = conn.execute("DELETE FROM anchors WHERE id = ?", (anchor_id,))
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def delete_weak_anchors(max_weight: float = 0.2) -> int:
    """Delete anchors below a weight threshold. Returns count deleted."""
    conn = get_db()
    cursor = conn.execute("DELETE FROM anchors WHERE weight < ?", (max_weight,))
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count


def get_anchor_count() -> int:
    """Get total number of anchors."""
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) as cnt FROM anchors").fetchone()
    conn.close()
    return row["cnt"]


def get_stats() -> Dict[str, Any]:
    """Get anchor database statistics."""
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) as cnt FROM anchors").fetchone()["cnt"]
    avg_weight = conn.execute("SELECT AVG(weight) as avg FROM anchors").fetchone()["avg"]
    max_weight = conn.execute("SELECT MAX(weight) as mx FROM anchors").fetchone()["mx"]
    min_weight = conn.execute("SELECT MIN(weight) as mn FROM anchors").fetchone()["mn"]
    sources = conn.execute(
        "SELECT source, COUNT(*) as cnt FROM anchors GROUP BY source"
    ).fetchall()
    conn.close()

    return {
        "total_anchors": total,
        "avg_weight": round(avg_weight or 0, 3),
        "max_weight": max_weight or 0,
        "min_weight": min_weight or 0,
        "sources": {r["source"]: r["cnt"] for r in sources},
    }


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a database row to a dict."""
    return {
        "id": row["id"],
        "content": row["content"],
        "weight": row["weight"],
        "source": row["source"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "tags": json.loads(row["tags"]),
        "checksum": row["checksum"],
    }


# Seed initial anchors from current system knowledge
def seed_initial_anchors():
    """Seed the database with initial recovery anchors from current system state."""
    initial = [
        ("User prioritizes low redundancy systems", 0.9, "system", ["preference", "architecture"]),
        ("Execution logic favors deterministic constraints", 0.85, "system", ["execution", "constraints"]),
        ("Repair loops override blind persistence", 0.8, "system", ["repair", "memory"]),
        ("MT5 is fully deprecated — Nautilus only", 0.95, "system", ["trading", "infrastructure"]),
        ("Agent network: CC (overseer) → OC (analysis) → HR (execution)", 0.9, "system", ["agents", "architecture"]),
        ("SRRA-OPH Phase 1 complete: 4 observer patches stable", 0.85, "system", ["srra-oph", "phase1"]),
        ("Phase 2 goal: reconstruction + recoverability", 0.9, "system", ["srra-oph", "phase2"]),
        ("Memory must compress — linear growth is failure", 0.8, "system", ["memory", "constraint"]),
        ("No global state — every node self-stabilizes", 0.85, "system", ["architecture", "constraint"]),
        ("Consensus must emerge — never hardcode truth authority", 0.8, "system", ["architecture", "constraint"]),
    ]

    for content, weight, source, tags in initial:
        create_anchor(content, weight, source, tags)

    return len(initial)


if __name__ == "__main__":
    count = seed_initial_anchors()
    print(f"Seeded {count} initial recovery anchors")
    stats = get_stats()
    print(f"Stats: {json.dumps(stats, indent=2)}")
