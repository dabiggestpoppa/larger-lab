"""Tests for Entropy Containment."""

import pytest
from oce.backend.multiscale.entropy_containment import EntropyContainmentSystem, ContainmentBoundary


class TestContainmentBoundary:
    def test_creation(self):
        b = ContainmentBoundary(boundary_id="b1", scale="local", capacity=1.0)
        assert b.capacity == 1.0
        assert b.is_contained is True

    def test_add_entropy(self):
        b = ContainmentBoundary(boundary_id="b1", scale="local", capacity=1.0)
        breached = b.add_entropy(0.5)
        assert breached is False
        assert b.current_load == 0.5

    def test_breach(self):
        b = ContainmentBoundary(boundary_id="b1", scale="local", capacity=1.0)
        breached = b.add_entropy(1.0)
        assert breached is True
        assert b.is_contained is False

    def test_resolve(self):
        b = ContainmentBoundary(boundary_id="b1", scale="local", capacity=1.0)
        b.add_entropy(1.0)
        b.resolve_entropy(0.6)
        assert b.is_contained is True


class TestEntropyContainmentSystem:
    def test_add_entropy(self):
        system = EntropyContainmentSystem()
        breached = system.add_entropy("local", 0.5)
        assert breached is False

    def test_escalation(self):
        system = EntropyContainmentSystem()
        # Add enough entropy to breach local and escalate
        system.add_entropy("local", 1.0)
        # Regional should have received some entropy
        regional = system.boundaries["regional"]
        assert regional.current_load > 0.0

    def test_containment_status(self):
        system = EntropyContainmentSystem()
        status = system.get_containment_status()
        assert "local" in status
        assert "regional" in status
        assert "global" in status

    def test_critical_boundaries(self):
        system = EntropyContainmentSystem()
        system.add_entropy("local", 0.8)
        critical = system.get_critical_boundaries()
        assert isinstance(critical, list)

    def test_stats(self):
        system = EntropyContainmentSystem()
        system.add_entropy("local", 0.5)
        stats = system.stats
        assert stats["total_boundaries"] == 3
