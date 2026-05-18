"""
V3 Phase 9 — Sovereign Field Emergence
Tests for ReconstructionCore module.
"""

import pytest
from oce.backend.field_core.reconstruction_core import (
    ReconstructionCore,
    ReconstructionResult,
)


class TestReconstructionResult:
    """Tests for ReconstructionResult dataclass."""

    def test_result_creation(self):
        """Test creating a reconstruction result."""
        result = ReconstructionResult(
            result_id="recon_1",
            target_element="elem_1",
            success=True,
            confidence=0.8,
        )
        assert result.result_id == "recon_1"
        assert result.target_element == "elem_1"
        assert result.success is True
        assert result.confidence == 0.8

    def test_is_usable_true(self):
        """Test is_usable when success and confidence are good."""
        result = ReconstructionResult(
            result_id="recon_1",
            target_element="elem_1",
            success=True,
            confidence=0.6,
        )
        assert result.is_usable is True

    def test_is_usable_false_low_confidence(self):
        """Test is_usable when confidence is too low."""
        result = ReconstructionResult(
            result_id="recon_1",
            target_element="elem_1",
            success=True,
            confidence=0.4,
        )
        assert result.is_usable is False

    def test_is_usable_false_failure(self):
        """Test is_usable when not successful."""
        result = ReconstructionResult(
            result_id="recon_1",
            target_element="elem_1",
            success=False,
            confidence=0.8,
        )
        assert result.is_usable is False


class TestReconstructionCore:
    """Tests for ReconstructionCore."""

    def test_core_empty(self):
        """Test empty core."""
        core = ReconstructionCore()
        assert core.stats["total_attempts"] == 0
        assert core.get_success_rate() == 0.0

    def test_set_topology(self):
        """Test setting topology."""
        core = ReconstructionCore()
        core.set_topology("elem_1", ["neighbor_1", "neighbor_2"])
        assert core._topology["elem_1"] == ["neighbor_1", "neighbor_2"]

    def test_reconstruct_full_state(self):
        """Test reconstruction with full state."""
        core = ReconstructionCore()
        result = core.reconstruct(
            "elem_1",
            {"key": "value"},
            {"key": "value"},
        )
        assert result.success is True
        assert result.confidence == 1.0
        assert result.missing_keys == []

    def test_reconstruct_partial_state(self):
        """Test reconstruction with partial state."""
        core = ReconstructionCore()
        core.set_topology("elem_1", ["neighbor_1"])
        result = core.reconstruct(
            "elem_1",
            {"key1": "value1"},
            {"key1": "value1", "key2": "default"},
        )
        assert "key2" in result.reconstructed_state

    def test_reconstruct_from_neighbors(self):
        """Test reconstruction from neighbor states."""
        core = ReconstructionCore()
        neighbors = [
            {"key1": "value1", "key2": "value2"},
            {"key3": "value3"},
        ]
        result = core.reconstruct_from_neighbors(
            "elem_1",
            neighbors,
            {"key1": "v1", "key2": "v2", "key3": "v3", "key4": "v4"},
        )
        assert result.success is True
        assert result.confidence > 0.5

    def test_reconstruct_no_schema(self):
        """Test reconstruction with no schema."""
        core = ReconstructionCore()
        result = core.reconstruct("elem_1", {}, {})
        assert result.success is True
        # No schema means no missing keys, so confidence is 1.0
        assert result.confidence == 1.0

    def test_get_success_rate(self):
        """Test getting success rate."""
        core = ReconstructionCore()
        core.reconstruct("elem_1", {"key": "value"}, {"key": "value"})
        core.reconstruct("elem_2", {}, {"key": "value"})  # Will fail

        rate = core.get_success_rate()
        assert rate == 0.5

    def test_stats(self):
        """Test core stats."""
        core = ReconstructionCore()
        core.reconstruct("elem_1", {"key": "value"}, {"key": "value"})
        core.reconstruct("elem_2", {"key": "value"}, {"key": "value"})

        stats = core.stats
        assert stats["total_attempts"] == 2
        assert stats["successful"] == 2
        assert stats["success_rate"] == 1.0