"""
Error Logger — Living Error Correction System
===============================================
Simple API for agents to log errors. Persists to memory-bank/error-db.json.
Designed for AS, PM, and RL to log errors that persist >2 attempts.

Usage:
    from error_logger import log_error, get_errors, get_patterns
    
    log_error(
        agent="PM",
        service="OC2",
        symptom="Gateway not responding",
        cause="Stuck session blocking event loop",
        solution="Kill stuck session from sessions.json",
        severity="critical",
        attempts=3
    )
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ERROR_DB = Path(__file__).parent.parent / "memory-bank" / "error-db.json"
ERROR_DB.parent.mkdir(parents=True, exist_ok=True)

# Severity levels
SEVERITY = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _load_db() -> Dict[str, Any]:
    """Load error database."""
    if ERROR_DB.exists():
        try:
            with open(ERROR_DB, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"version": 1, "entries": [], "patterns": [], "last_analyzed": None}


def _save_db(db: Dict[str, Any]):
    """Save error database."""
    with open(ERROR_DB, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def log_error(
    agent: str,
    service: str,
    symptom: str,
    cause: str = "",
    solution: str = "",
    severity: str = "medium",
    attempts: int = 1,
    tags: List[str] = None,
    related: List[str] = None,
) -> Dict[str, Any]:
    """
    Log an error to the database.
    
    Args:
        agent: Which agent encountered the error (AS/PM/RL/CC/OC/OC2)
        service: What service had the error (OC2/OCE/SRRA/workspace/etc.)
        symptom: What was observed
        cause: Root cause (if known)
        solution: How it was fixed (if known)
        severity: low/medium/high/critical
        attempts: How many attempts before resolution
        tags: Optional tags for categorization
        related: Optional list of related error IDs
    
    Returns:
        The created error entry
    """
    db = _load_db()
    
    entry_id = f"ERR-{len(db['entries']) + 1:04d}"
    now = datetime.now(timezone.utc).isoformat()
    
    entry = {
        "id": entry_id,
        "timestamp": now,
        "agent": agent,
        "service": service,
        "symptom": symptom,
        "cause": cause,
        "solution": solution,
        "severity": severity,
        "severity_level": SEVERITY.get(severity, 1),
        "attempts": attempts,
        "tags": tags or [],
        "related": related or [],
        "status": "resolved" if solution else "open",
        "pattern_id": None,
    }
    
    db["entries"].append(entry)
    _save_db(db)
    
    return entry


def get_errors(
    agent: str = None,
    service: str = None,
    severity: str = None,
    status: str = None,
    min_attempts: int = None,
    tag: str = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Query errors with optional filters."""
    db = _load_db()
    results = db["entries"]
    
    if agent:
        results = [e for e in results if e["agent"] == agent]
    if service:
        results = [e for e in results if e["service"] == service]
    if severity:
        results = [e for e in results if e["severity"] == severity]
    if status:
        results = [e for e in results if e["status"] == status]
    if min_attempts:
        results = [e for e in results if e["attempts"] >= min_attempts]
    if tag:
        results = [e for e in results if tag in e.get("tags", [])]
    
    # Sort by severity (highest first), then by timestamp (newest first)
    results.sort(key=lambda e: (-e["severity_level"], e["timestamp"]), reverse=False)
    return results[-limit:]


def get_patterns(min_occurrences: int = 2) -> List[Dict[str, Any]]:
    """
    Detect recurring error patterns.
    Groups errors by service + symptom similarity.
    """
    db = _load_db()
    
    # Group by service
    by_service: Dict[str, List[Dict]] = {}
    for entry in db["entries"]:
        svc = entry["service"]
        if svc not in by_service:
            by_service[svc] = []
        by_service[svc].append(entry)
    
    patterns = []
    for svc, entries in by_service.items():
        if len(entries) >= min_occurrences:
            # Group by similar symptoms (simple keyword matching)
            symptom_groups: Dict[str, List[Dict]] = {}
            for e in entries:
                # Use first 3 words of symptom as key
                key = " ".join(e["symptom"].lower().split()[:3])
                if key not in symptom_groups:
                    symptom_groups[key] = []
                symptom_groups[key].append(e)
            
            for key, group in symptom_groups.items():
                if len(group) >= min_occurrences:
                    patterns.append({
                        "id": f"PAT-{len(patterns) + 1:03d}",
                        "service": svc,
                        "symptom_pattern": key,
                        "occurrences": len(group),
                        "error_ids": [e["id"] for e in group],
                        "agents_involved": list(set(e["agent"] for e in group)),
                        "max_severity": max(group, key=lambda e: e["severity_level"])["severity"],
                        "total_attempts": sum(e["attempts"] for e in group),
                        "common_solution": _most_common([e["solution"] for e in group if e["solution"]]),
                        "first_seen": min(e["timestamp"] for e in group),
                        "last_seen": max(e["timestamp"] for e in group),
                    })
    
    # Sort by occurrences (highest first)
    patterns.sort(key=lambda p: -p["occurrences"])
    return patterns


def _most_common(items: List[str]) -> str:
    """Return most common non-empty string."""
    if not items:
        return ""
    counts: Dict[str, int] = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return max(counts, key=counts.get)


def get_stats() -> Dict[str, Any]:
    """Get error database statistics."""
    db = _load_db()
    entries = db["entries"]
    
    if not entries:
        return {"total": 0, "open": 0, "resolved": 0, "patterns": 0}
    
    return {
        "total": len(entries),
        "open": sum(1 for e in entries if e["status"] == "open"),
        "resolved": sum(1 for e in entries if e["status"] == "resolved"),
        "by_severity": {
            s: sum(1 for e in entries if e["severity"] == s)
            for s in SEVERITY
        },
        "by_agent": {
            a: sum(1 for e in entries if e["agent"] == a)
            for a in set(e["agent"] for e in entries)
        },
        "by_service": {
            s: sum(1 for e in entries if e["service"] == s)
            for s in set(e["service"] for e in entries)
        },
        "patterns_detected": len(get_patterns()),
        "high_attempt_errors": len([e for e in entries if e["attempts"] > 2]),
    }


def mark_resolved(error_id: str, solution: str):
    """Mark an error as resolved with the solution."""
    db = _load_db()
    for entry in db["entries"]:
        if entry["id"] == error_id:
            entry["status"] = "resolved"
            entry["solution"] = solution
            entry["resolved_at"] = datetime.now(timezone.utc).isoformat()
            _save_db(db)
            return entry
    return None


if __name__ == "__main__":
    # Demo: show current state
    stats = get_stats()
    print(json.dumps(stats, indent=2))
    print()
    patterns = get_patterns(min_occurrences=1)
    for p in patterns:
        print(f"Pattern {p['id']}: {p['service']} / {p['symptom_pattern']} — {p['occurrences']}x, severity={p['max_severity']}")
