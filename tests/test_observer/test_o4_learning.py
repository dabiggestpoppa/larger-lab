"""
O-4 Tests: Operational Trace + Field Learning
==============================================
Tests for WorkflowDistiller (O4-B3) and PatternMemory (O4-B8).
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timezone

from core.learning.workflow_distiller import WorkflowDistiller, TraceEntry
from core.learning.pattern_memory import PatternMemory, StoredPattern


# ─── WorkflowDistiller Tests ───────────────────────────────────────────────

class TestWorkflowDistiller:
    """Tests for O4-B3: WorkflowDistiller."""

    def test_ingest_single_trace(self):
        """Single trace should be stored without error."""
        distiller = WorkflowDistiller()
        trace = TraceEntry(
            trace_id="t1",
            timestamp=datetime.now(timezone.utc).isoformat(),
            task_domain="coding",
            complexity="medium",
            routing_decision="spawn_agent",
            outcome="success",
            duration_ms=1500,
            context_keys=["repo_path", "task_description"],
        )
        distiller.ingest_trace(trace)
        assert len(distiller._traces) == 1

    def test_extract_patterns_from_repeated_traces(self):
        """Repeated task sequences should produce patterns."""
        distiller = WorkflowDistiller()
        for i in range(5):
            distiller.ingest_trace(TraceEntry(
                trace_id=f"t{i}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                task_domain="coding",
                complexity="medium",
                routing_decision="spawn_agent",
                outcome="success",
                duration_ms=1000 + i * 100,
                context_keys=["repo_path"],
            ))
        patterns = distiller.get_patterns(min_frequency=2)
        assert len(patterns) >= 1
        assert "coding" in patterns[0].name

    def test_get_recommended_routing(self):
        """Should recommend the most successful routing for a domain."""
        distiller = WorkflowDistiller()
        # Add successful traces for "coding" -> "spawn_agent"
        for i in range(5):
            distiller.ingest_trace(TraceEntry(
                trace_id=f"t{i}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                task_domain="coding",
                complexity="low",
                routing_decision="spawn_agent",
                outcome="success",
                duration_ms=1000,
                context_keys=[],
            ))
        # Add failed traces for "coding" -> "direct"
        for i in range(3):
            distiller.ingest_trace(TraceEntry(
                trace_id=f"f{i}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                task_domain="coding",
                complexity="low",
                routing_decision="direct",
                outcome="failure",
                duration_ms=5000,
                context_keys=[],
            ))
        recommendation = distiller.get_recommended_routing("coding")
        assert recommendation is not None

    def test_ingest_from_events(self):
        """Should ingest from raw event format."""
        distiller = WorkflowDistiller()
        events = [
            {
                "event_id": "e1",
                "event_type": "orchestration_complete",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_domain": "research",
                "complexity": "high",
                "routing_decision": "spawn_agent",
                "duration_ms": 2000,
                "context": {"query": "deep analysis"},
            },
            {
                "event_id": "e2",
                "event_type": "orchestration_failure",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_domain": "research",
                "complexity": "high",
                "routing_decision": "direct",
                "duration_ms": 5000,
                "context": {"query": "quick lookup"},
                "error_type": "timeout",
            },
        ]
        count = distiller.ingest_from_events(events)
        assert count == 2
        assert len(distiller._traces) == 2

    def test_save_and_load(self):
        """Patterns should persist to disk and load back."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            distiller = WorkflowDistiller(storage_path=path)
            for i in range(5):
                distiller.ingest_trace(TraceEntry(
                    trace_id=f"t{i}",
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    task_domain="coding",
                    complexity="low",
                    routing_decision="spawn_agent",
                    outcome="success",
                    duration_ms=1000,
                    context_keys=[],
                ))
            distiller.save()

            # Load into new instance
            distiller2 = WorkflowDistiller(storage_path=path)
            assert distiller2.load() is True
            assert len(distiller2._patterns) == len(distiller._patterns)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_get_stats(self):
        """Should return accurate statistics."""
        distiller = WorkflowDistiller()
        for i in range(3):
            distiller.ingest_trace(TraceEntry(
                trace_id=f"t{i}",
                timestamp=datetime.now(timezone.utc).isoformat(),
                task_domain="coding",
                complexity="low",
                routing_decision="spawn_agent",
                outcome="success" if i < 2 else "failure",
                duration_ms=1000,
                context_keys=[],
            ))
        stats = distiller.get_stats()
        assert stats["total_traces"] == 3
        assert "coding" in stats["domains"]


# ─── PatternMemory Tests ───────────────────────────────────────────────────

class TestPatternMemory:
    """Tests for O4-B8: PatternMemory."""

    def test_store_and_recall(self):
        """Should store and recall patterns."""
        memory = PatternMemory()
        pattern = StoredPattern(
            pattern_id="p1",
            name="coding:spawn_agent",
            category="routing",
            content={"task_domain": "coding", "routing": "spawn_agent"},
            confidence=0.85,
            usage_count=5,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            source_traces=10,
        )
        memory.store(pattern)
        recalled = memory.recall("p1")
        assert recalled is not None
        assert recalled.name == "coding:spawn_agent"

    def test_search_by_category(self):
        """Should filter patterns by category."""
        memory = PatternMemory()
        for i, cat in enumerate(["routing", "routing", "context", "failure"]):
            memory.store(StoredPattern(
                pattern_id=f"p{i}",
                name=f"test_{cat}",
                category=cat,
                content={"key": f"value_{i}"},
                confidence=0.5 + i * 0.1,
                usage_count=i + 1,
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
            ))
        routing = memory.search(category="routing")
        assert len(routing) == 2
        context = memory.search(category="context")
        assert len(context) == 1

    def test_search_by_confidence(self):
        """Should filter patterns by minimum confidence."""
        memory = PatternMemory()
        for i in range(5):
            memory.store(StoredPattern(
                pattern_id=f"p{i}",
                name=f"pattern_{i}",
                category="routing",
                content={},
                confidence=0.2 * i,
                usage_count=1,
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
            ))
        high_conf = memory.search(min_confidence=0.5)
        assert len(high_conf) == 2  # 0.6, 0.8 (0.0, 0.2, 0.4 are below 0.5)

    def test_get_routing_knowledge(self):
        """Should return routing knowledge for a task domain."""
        memory = PatternMemory()
        memory.store(StoredPattern(
            pattern_id="r1",
            name="coding:spawn_agent",
            category="routing",
            content={"routing": "spawn_agent", "model": "claude-sonnet"},
            confidence=0.9,
            usage_count=10,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
            source_traces=20,
        ))
        knowledge = memory.get_routing_knowledge("coding")
        assert knowledge.get("routing") == "spawn_agent"

    def test_get_failure_patterns(self):
        """Should return failure patterns to avoid."""
        memory = PatternMemory()
        memory.store(StoredPattern(
            pattern_id="f1",
            name="coding:direct_failure",
            category="failure",
            content={"error": "timeout", "avoid_routing": "direct"},
            confidence=0.8,
            usage_count=3,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        ))
        failures = memory.get_failure_patterns("coding")
        assert len(failures) == 1
        assert failures[0].content["avoid_routing"] == "direct"

    def test_consolidate_prunes_weak_patterns(self):
        """Should prune patterns with low confidence and low usage."""
        memory = PatternMemory()
        # Strong pattern
        memory.store(StoredPattern(
            pattern_id="strong",
            name="strong_pattern",
            category="routing",
            content={},
            confidence=0.9,
            usage_count=10,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        ))
        # Weak pattern
        memory.store(StoredPattern(
            pattern_id="weak",
            name="weak_pattern",
            category="routing",
            content={},
            confidence=0.1,
            usage_count=1,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=datetime.now(timezone.utc).isoformat(),
        ))
        pruned = memory.consolidate()
        assert pruned == 1
        assert memory.recall("weak") is None
        assert memory.recall("strong") is not None

    def test_save_and_load(self):
        """Memory should persist to disk and load back."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        try:
            memory = PatternMemory(storage_path=path)
            memory.store(StoredPattern(
                pattern_id="p1",
                name="test_pattern",
                category="routing",
                content={"key": "value"},
                confidence=0.8,
                usage_count=5,
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
                source_traces=10,
            ))
            memory.save()

            memory2 = PatternMemory(storage_path=path)
            assert memory2.load() is True
            assert len(memory2.patterns) == 1
            assert memory2.recall("p1").name == "test_pattern"
        finally:
            Path(path).unlink(missing_ok=True)

    def test_get_stats(self):
        """Should return accurate memory statistics."""
        memory = PatternMemory()
        for i in range(3):
            memory.store(StoredPattern(
                pattern_id=f"p{i}",
                name=f"pattern_{i}",
                category=["routing", "context", "failure"][i],
                content={},
                confidence=0.5 + i * 0.2,
                usage_count=i + 1,
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
            ))
        stats = memory.get_stats()
        assert stats["total_patterns"] == 3
        assert stats["categories"]["routing"] == 1
        assert stats["categories"]["context"] == 1
        assert stats["categories"]["failure"] == 1
        assert stats["total_usage"] == 6  # 1 + 2 + 3
