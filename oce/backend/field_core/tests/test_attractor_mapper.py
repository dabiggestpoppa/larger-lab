"""
V3 Phase 9 — Sovereign Field Emergence
Tests for AttractorMapper module.
"""

import pytest
import time
from oce.backend.field_core.attractor_mapper import (
    AttractorMapper,
    AttractorState,
)


class TestAttractorState:
    """Tests for AttractorState dataclass."""

    def test_attractor_creation(self):
        """Test creating an attractor state."""
        attractor = AttractorState(
            attractor_id="attr_1",
            name="test_attractor",
        )
        assert attractor.attractor_id == "attr_1"
        assert attractor.name == "test_attractor"
        assert attractor.basin_size == 0
        assert attractor.stability == 0.5
        assert attractor.visit_count == 0

    def test_is_stable_false(self):
        """Test is_stable when not enough visits."""
        attractor = AttractorState(
            attractor_id="attr_1",
            name="test",
            stability=0.7,
            visit_count=2,
        )
        assert attractor.is_stable is False

    def test_is_stable_true(self):
        """Test is_stable when stable."""
        attractor = AttractorState(
            attractor_id="attr_1",
            name="test",
            stability=0.7,
            visit_count=3,
        )
        assert attractor.is_stable is True

    def test_record_visit(self):
        """Test recording a visit increases stability."""
        attractor = AttractorState(
            attractor_id="attr_1",
            name="test",
            stability=0.5,
            visit_count=0,
        )
        attractor.record_visit()
        assert attractor.visit_count == 1
        assert attractor.stability == 0.55
        # last_seen is updated (may be same as first_seen in fast tests)

    def test_stability_cap(self):
        """Test stability caps at 1.0."""
        attractor = AttractorState(
            attractor_id="attr_1",
            name="test",
            stability=0.98,
            visit_count=0,
        )
        attractor.record_visit()
        assert attractor.stability == 1.0


class TestAttractorMapper:
    """Tests for AttractorMapper."""

    def test_mapper_empty(self):
        """Test empty mapper."""
        mapper = AttractorMapper()
        assert mapper.get_stable_attractors() == []
        assert mapper.stats["total_attractors"] == 0

    def test_register_attractor(self):
        """Test registering an attractor."""
        mapper = AttractorMapper()
        attractor = mapper.register_attractor("test_attr")
        assert attractor.attractor_id == "attr_0"
        assert attractor.name == "test_attr"

    def test_register_attractor_with_id(self):
        """Test registering with custom ID."""
        mapper = AttractorMapper()
        attractor = mapper.register_attractor("test", attractor_id="custom_id")
        assert attractor.attractor_id == "custom_id"

    def test_record_state(self):
        """Test recording a state."""
        mapper = AttractorMapper()
        mapper.register_attractor("attr_1")
        # Need > 10 visits for similarity > 0.5 (visit_count / 10.0)
        for _ in range(12):
            mapper._attractors["attr_0"].record_visit()
        result = mapper.record_state({"key": "value"})
        assert result is not None

    def test_get_stable_attractors(self):
        """Test getting stable attractors."""
        mapper = AttractorMapper()
        attr1 = mapper.register_attractor("attr_1")
        attr2 = mapper.register_attractor("attr_2")

        # Make attr1 stable
        for _ in range(5):
            attr1.record_visit()

        stable = mapper.get_stable_attractors()
        assert len(stable) == 1
        assert stable[0].attractor_id == "attr_0"

    def test_get_attractor(self):
        """Test getting a specific attractor."""
        mapper = AttractorMapper()
        mapper.register_attractor("test", attractor_id="test_id")
        attractor = mapper.get_attractor("test_id")
        assert attractor is not None
        assert attractor.name == "test"

    def test_get_attractor_not_found(self):
        """Test getting nonexistent attractor."""
        mapper = AttractorMapper()
        assert mapper.get_attractor("nonexistent") is None

    def test_get_drifting_attractors(self):
        """Test getting drifting attractors."""
        mapper = AttractorMapper()
        stable = mapper.register_attractor("stable")
        drifting = mapper.register_attractor("drifting")

        stable.stability = 0.8
        drifting.stability = 0.2

        drifting_list = mapper.get_drifting_attractors()
        assert len(drifting_list) == 1
        assert drifting_list[0].name == "drifting"

    def test_stats(self):
        """Test mapper stats."""
        mapper = AttractorMapper()
        mapper.register_attractor("attr_1")
        mapper.register_attractor("attr_2")
        for _ in range(5):
            mapper._attractors["attr_0"].record_visit()

        stats = mapper.stats
        assert stats["total_attractors"] == 2
        assert stats["stable_attractors"] == 1
        assert stats["total_states_recorded"] == 0