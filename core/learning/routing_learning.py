"""
O-4-B4: RoutingLearning
========================
Improves future orchestration routing through operational outcomes. Learns which models
succeed, which routes fail, which observers perform best, and which workflows
destabilize topology. Adapts slowly and conservatively.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("core.learning.routing_learning")

@dataclass
class RoutingPattern:
    """A learned routing pattern from operational traces."""
    pattern_id: str
    task_domain: str
    routing_decision: str  # e.g., "model_A->observer_X->observer_Y"
    model: str
    observer_sequence: List[str]
    success_count: int
    failure_count: int
    success_rate: float
    avg_duration_ms: float
    frequency: int
    first_seen: str
    last_seen: str

class RoutingLearning:
    """Analyzes operational traces to learn optimal routing decisions."""
    
    def __init__(self, trace_collector: "TraceCollector", storage_path: Optional[str] = None):
        self.trace_collector = trace_collector
        self._patterns: Dict[str, RoutingPattern] = {}
        self._storage_path = Path(storage_path) if storage_path else None
        self._initialized = False
    
    def _init_if_needed(self) -> None:
        """Initialize if not already initialized."""
        if not self._initialized:
            # Ensure trace collector is available
            if not hasattr(self, 'trace_collector'):
                raise ValueError("TraceCollector not provided")
            self._initialized = True
    
    def analyze_traces(self) -> Dict[str, Any]:
        """Analyze all traces to extract routing patterns and performance metrics."""
        self._init_if_needed()
        
        # Collect all traces
        traces = self.trace_collector.get_traces()
        if not traces:
            logger.warning("No traces available for routing learning")
            return {}
        
        # Group by task domain
        domain_patterns: Dict[str, List[RoutingPattern]] = defaultdict(list)
        
        for trace in traces:
            # Extract relevant information from trace metadata if available
            # In real implementation, this would come from actual trace data
            # For now, we'll simulate based on available data
            domain = trace.metadata.get("task_domain", "unknown")
            # Simulate routing decision from trace metadata
            routing_decision = trace.metadata.get("routing_decision", "default")
            model = trace.metadata.get("model", "default_model")
            observer_sequence = trace.metadata.get("observer_sequence", [])
            
            # Count successes/failures
            success = trace.status == "complete"  # Assume completion means success
            key = f"{domain}:{routing_decision}:{model}"
            pattern_key = f"{domain}:{routing_decision}"
            
            # Update pattern statistics
            if key not in self._patterns:
                self._patterns[key] = RoutingPattern(
                    pattern_id=key,
                    task_domain=domain,
                    routing_decision=routing_decision,
                    model=model,
                    observer_sequence=observer_sequence,
                    success_count=1 if success else 0,
                    failure_count=0 if success else 1,
                    success_rate=1.0 if success else 0.0,
                    avg_duration_ms=trace.duration_seconds * 1000 if trace.duration_seconds > 0 else 0,
                    frequency=1,
                    first_seen=trace.timestamp,
                    last_seen=trace.timestamp,
                )
            else:
                pattern = self._patterns[key]
                pattern.success_count += 1 if success else 0
                pattern.failure_count += 0 if success else 1
                pattern.success_rate = pattern.success_count / (pattern.success_count + pattern.failure_count) if (pattern.success_count + pattern.failure_count) > 0 else 0.0
                pattern.avg_duration_ms = (
                    (pattern.avg_duration_ms * (pattern.frequency - 1) + trace.duration_seconds * 1000)
                    / pattern.frequency
                    if pattern.frequency > 0
                    else trace.duration_seconds * 1000
                )
                pattern.frequency += 1
                pattern.last_seen = trace.timestamp
        
        # Convert to dict for return
        result = {
            "total_patterns": len(self._patterns),
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "task_domain": p.task_domain,
                    "routing_decision": p.routing_decision,
                    "model": p.model,
                    "observer_sequence": p.observer_sequence,
                    "success_count": p.success_count,
                    "failure_count": p.failure_count,
                    "success_rate": p.success_rate,
                    "avg_duration_ms": p.avg_duration_ms,
                    "frequency": p.frequency,
                    "first_seen": p.first_seen,
                    "last_seen": p.last_seen,
                }
                for p in self._patterns.values()
            ],
            "domains": list(set(t.task_domain for t in traces)),
        }
        
        # Save patterns to persistent storage if configured
        if self._storage_path:
            self.save()
            
        return result
    
    def get_recommended_routing(self, task_domain: str) -> Optional[str]:
        """Get the best routing decision for a task domain based on learned patterns."""
        self._init_if_needed()
        
        # Find patterns for the given domain
        domain_patterns = [
            p for p in self._patterns.values() 
            if p.task_domain == task_domain and p.frequency > 0
        ]
        
        if not domain_patterns:
            logger.info(f"No routing patterns found for domain: {task_domain}")
            return None
        
        # Select pattern with highest success_rate * frequency (weighted by reliability)
        best_pattern = max(domain_patterns, key=lambda p: p.success_rate * p.frequency)
        return best_pattern.routing_decision
    
    def get_model_performance(self) -> Dict[str, float]:
        """Get performance metrics for each model."""
        self._init_if_needed()
        model_perf: Dict[str, float] = {}
        
        for pattern in self._patterns.values():
            model = pattern.model
            key = f"{model}_success_rate"
            if key not in model_perf:
                model_perf[key] = 0.0
            model_perf[key] = max(model_perf[key], pattern.success_rate)
        
        # Convert to simple model-perf dict
        return {model: perf for (model, perf) in model_perf.items()}
    
    def get_observer_performance(self) -> Dict[str, float]:
        """Get performance metrics for each observer."""
        self._init_if_needed()
        observer_perf: Dict[str, float] = {}
        
        for pattern in self._patterns.values():
            for observer in pattern.observer_sequence:
                key = f"{observer}_success_rate"
                if key not in observer_perf:
                    observer_perf[key] = 0.0
                observer_perf[key] = max(observer_perf[key], pattern.success_rate)
        
        return observer_perf
    
    def save(self) -> None:
        """Persist learned routing patterns to disk."""
        if not self._storage_path:
            return
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "task_domain": p.task_domain,
                    "routing_decision": p.routing_decision,
                    "model": p.model,
                    "observer_sequence": p.observer_sequence,
                    "success_count": p.success_count,
                    "failure_count": p.failure_count,
                    "success_rate": p.success_rate,
                    "avg_duration_ms": p.avg_duration_ms,
                    "frequency": p.frequency,
                    "first_seen": p.first_seen,
                    "last_seen": p.last_seen,
                }
                for p in self._patterns.values()
            ],
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        self._storage_path.write_text(json.dumps(data, indent=2))
        logger.info(f"Saved {len(self._patterns)} routing patterns to {self._storage_path}")
    
    def load(self) -> bool:
        """Load learned routing patterns from disk."""
        if not self._storage_path or not self._storage_path.exists():
            return False
            
        try:
            data = json.loads(self._storage_path.read_text())
            self._patterns = {}
            for pattern_data in data.get("patterns", []):
                self._patterns[pattern_data["pattern_id"]] = RoutingPattern(
                    pattern_id=pattern_data["pattern_id"],
                    task_domain=pattern_data["task_domain"],
                    routing_decision=pattern_data["routing_decision"],
                    model=pattern_data["model"],
                    observer_sequence=pattern_data["observer_sequence"],
                    success_count=pattern_data["success_count"],
                    failure_count=pattern_data["failure_count"],
                    success_rate=pattern_data["success_rate"],
                    avg_duration_ms=pattern_data["avg_duration_ms"],
                    frequency=pattern_data["frequency"],
                    first_seen=pattern_data["first_seen"],
                    last_seen=pattern_data["last_seen"],
                )
            logger.info(f"Loaded {len(self._patterns)} routing patterns from {self._storage_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load routing patterns: {e}")
            return False