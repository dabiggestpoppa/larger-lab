"""Tests for Boundary Engine."""

import pytest
from oce.backend.cognition.boundary_engine import BoundaryEngine, Boundary


class TestBoundary:
    def test_creation(self):
        b = Boundary(boundary_id="b1", boundary_type="entropy", threshold=0.8)
        assert b.boundary_id == "b1"
        assert b.threshold == 0.8

    def test_not_exceeded(self):
        b = Boundary(boundary_id="b1", boundary_type="entropy", threshold=0.8)
        assert b.update(0.5) is False
        assert b.is_exceeded is False

    def test_exceeded(self):
        b = Boundary(boundary_id="b1", boundary_type="entropy", threshold=0.8)
        assert b.update(0.9) is True
        assert b.is_exceeded is True

    def test_utilization(self):
        b = Boundary(boundary_id="b1", boundary_type="entropy", threshold=1.0)
        b.update(0.5)
        assert b.utilization == 0.5


class TestBoundaryEngine:
    def test_creation(self):
        engine = BoundaryEngine()
        assert len(engine.boundaries) >= 5  # Default boundaries

    def test_add_boundary(self):
        engine = BoundaryEngine()
        b = engine.add_boundary("custom", "test", 0.5)
        assert "custom" in engine.boundaries

    def test_check(self):
        engine = BoundaryEngine()
        assert engine.check("entropy_max", 0.9) is True  # Exceeds 0.8
        assert engine.check("entropy_max", 0.5) is False

    def test_check_all(self):
        engine = BoundaryEngine()
        exceeded = engine.check_all({"entropy_max": 0.9, "recursion_max": 5.0})
        assert "entropy_max" in exceeded

    def test_get_critical(self):
        engine = BoundaryEngine()
        engine.check("entropy_max", 0.75)  # Near threshold
        critical = engine.get_critical_boundaries()
        assert isinstance(critical, list)

    def test_stats(self):
        engine = BoundaryEngine()
        stats = engine.stats
        assert stats["total_boundaries"] >= 5
