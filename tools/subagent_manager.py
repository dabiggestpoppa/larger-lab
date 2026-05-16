"""
Subagent Manager — Sidechain File Pattern
Inspired by VILA-Lab/Dive-into-Claude-Code analysis.

Subagents return only summary text to the parent. Full transcripts live in
sidechain files. This prevents parent context pollution.

Usage:
    from tools.subagent_manager import SubagentManager
    
    mgr = SubagentManager(sidechain_dir="progress/sidechains")
    result = mgr.run_subagent(task="Run Phase 2 tests", agent="HR")
    # result.summary — short text for parent context
    # result.sidechain_path — full transcript file
"""

import json
import os
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


@dataclass
class SubagentResult:
    """Result from a subagent execution."""
    task: str
    agent: str
    summary: str
    sidechain_path: str
    success: bool
    duration_seconds: float
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SubagentManager:
    """
    Manages subagent execution with sidechain file pattern.
    
    Key principle: Subagents return ONLY summary text to the parent.
    Full transcripts (every tool call, every response) go to sidechain files.
    This prevents parent context from being polluted by subagent internals.
    """
    
    def __init__(self, sidechain_dir: str = "progress/sidechains"):
        self.sidechain_dir = Path(sidechain_dir)
        self.sidechain_dir.mkdir(parents=True, exist_ok=True)
    
    def create_sidechain(self, task: str, agent: str) -> Path:
        """Create a new sidechain file for a subagent run."""
        run_id = str(uuid.uuid4())[:8]
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{agent}_{timestamp}_{run_id}.jsonl"
        path = self.sidechain_dir / filename
        
        # Write header
        with open(path, "w", encoding="utf-8") as f:
            header = {
                "type": "header",
                "run_id": run_id,
                "agent": agent,
                "task": task,
                "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            f.write(json.dumps(header) + "\n")
        
        return path
    
    def log_turn(self, sidechain_path: Path, role: str, content: str, 
                 tool_calls: Optional[List[Dict]] = None,
                 metadata: Optional[Dict] = None):
        """Log a single turn to the sidechain file."""
        entry = {
            "type": "turn",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "role": role,
            "content": content[:500],  # Truncate for sidechain
            "tool_calls": tool_calls or [],
            "metadata": metadata or {},
        }
        with open(sidechain_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    
    def finalize_sidechain(self, sidechain_path: Path, success: bool, 
                           summary: str, tokens_used: int = 0):
        """Finalize the sidechain with result summary."""
        entry = {
            "type": "result",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "success": success,
            "summary": summary,
            "tokens_used": tokens_used,
        }
        with open(sidechain_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_summary(self, sidechain_path: Path) -> Optional[str]:
        """Extract the summary from a sidechain file."""
        if not sidechain_path.exists():
            return None
        
        with open(sidechain_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "result":
                        return entry.get("summary", "")
                except json.JSONDecodeError:
                    continue
        return None
    
    def list_sidechains(self, agent: Optional[str] = None) -> List[Path]:
        """List all sidechain files, optionally filtered by agent."""
        if agent:
            return sorted(self.sidechain_dir.glob(f"{agent}_*.jsonl"))
        return sorted(self.sidechain_dir.glob("*.jsonl"))
    
    def cleanup_stale(self, max_age_hours: int = 24):
        """Remove sidechain files older than max_age_hours."""
        cutoff = time.time() - (max_age_hours * 3600)
        for path in self.sidechain_dir.glob("*.jsonl"):
            if path.stat().st_mtime < cutoff:
                path.unlink()
    
    def run_subagent(self, task: str, agent: str, 
                     max_turns: int = 20) -> SubagentResult:
        """
        Execute a subagent task. This is the main entry point.
        
        In production, this would dispatch to the actual agent.
        For now, it creates the sidechain and returns a placeholder.
        """
        start_time = time.time()
        sidechain_path = self.create_sidechain(task, agent)
        
        # Log the task assignment
        self.log_turn(sidechain_path, "system", f"Task assigned: {task}")
        
        # In production: dispatch to agent, collect results
        # For now, return placeholder
        duration = time.time() - start_time
        
        return SubagentResult(
            task=task,
            agent=agent,
            summary=f"[Subagent {agent} would execute: {task}]",
            sidechain_path=str(sidechain_path),
            success=True,
            duration_seconds=duration,
        )


# Convenience function
def run_subagent(task: str, agent: str, sidechain_dir: str = "progress/sidechains") -> SubagentResult:
    """Quick subagent execution."""
    mgr = SubagentManager(sidechain_dir=sidechain_dir)
    return mgr.run_subagent(task=task, agent=agent)


if __name__ == "__main__":
    mgr = SubagentManager()
    
    # Demo
    result = mgr.run_subagent("Run Phase 2 tests", "HR")
    print(f"Task: {result.task}")
    print(f"Agent: {result.agent}")
    print(f"Sidechain: {result.sidechain_path}")
    print(f"Summary: {result.summary}")
    
    # List sidechains
    print(f"\nAll sidechains: {len(mgr.list_sidechains())}")
