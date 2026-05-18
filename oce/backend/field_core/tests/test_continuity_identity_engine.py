"""
V3 Phase 9 — Sovereign Field Emergence
Tests for ContinuityIdentityEngine module.
"""

import pytest
from oce.backend.field_core.continuity_identity_engine import (
    ContinuityIdentityEngine,
    ContinuityState,
)


class TestContinuityState:
    """Tests for ContinuityState dataclass."""

    def test_state_creation(self):
        """Test creating a continuity state."""
        state = ContinuityState(
            state_id="chk_1",
            element_id="elem_1",
            identity_hash="abc123",
            continuity_score=0.8,
        )
        assert state.state_id == "chk_1"
        assert state.element_id == "elem_1"
        assert state.identity_hash == "abc123"
        assert state.continuity_score == 0.8

    def test_is_continuous_true(self):
        """Test is_continuous when score is high."""
        state = ContinuityState(
            state_id="chk_1",
            element_id="elem_1",
            identity_hash="hash",
            continuity_score=0.7,
        )
        assert state.is_continuous is True

    def test_is_continuous_false(self):
        """Test is_continuous when score is low."""
        state = ContinuityState(
            state_id="chk_1",
            element_id="elem_1",
            identity_hash="hash",
            continuity_score=0.5,
        )
        assert state.is_continuous is False


class TestContinuityIdentityEngine:
    """Tests for ContinuityIdentityEngine."""

    def test_engine_empty(self):
        """Test empty engine."""
        engine = ContinuityIdentityEngine()
        assert engine.stats["total_checkpoints"] == 0
        assert engine.get_continuity_score("nonexistent") == 0.0

    def test_create_checkpoint(self):
        """Test creating a checkpoint."""
        engine = ContinuityIdentityEngine()
        state = engine.create_checkpoint("elem_1", {"key": "value"})
        assert state.element_id == "elem_1"
        assert state.continuity_score == 1.0  # First checkpoint is always 1.0
        assert state.identity_hash != ""

    def test_verify_continuity(self):
        """Test verifying continuity."""
        engine = ContinuityIdentityEngine()
        engine.create_checkpoint("elem_1", {"key": "value"})
        state = engine.verify_continuity("elem_1", {"key": "value"})
        assert state.continuity_score == 1.0

    def test_continuity_drift(self):
        """Test continuity score changes with state drift."""
        engine = ContinuityIdentityEngine()
        engine.create_checkpoint("elem_1", {"key": "value"})
        # Different state - lower continuity
        state = engine.verify_continuity("elem_1", {"different": "state"})
        assert state.continuity_score < 1.0

    def test_get_continuity_score(self):
        """Test getting continuity score."""
        engine = ContinuityIdentityEngine()
        engine.create_checkpoint("elem_1", {"key": "value"})
        score = engine.get_continuity_score("elem_1")
        assert score == 1.0

    def test_get_discontinuous_elements(self):
        """Test getting discontinuous elements."""
        engine = ContinuityIdentityEngine()
        engine.create_checkpoint("elem_1", {"key": "value"})
        engine.create_checkpoint("elem_2", {"different": "state"})
        # elem_2 has different state, so lower continuity
        engine.create_checkpoint("elem_2", {"another": "change"})

        # elem_2 has lower continuity due to state drift
        discontinuous = engine.get_discontinuous_elements(threshold=0.9)
        assert "elem_2" in discontinuous

    def test_merge_identities(self):
        """Test merging identities."""
        engine = ContinuityIdentityEngine()
        engine.create_checkpoint("elem_a", {"key": "value"})
        engine.create_checkpoint("elem_b", {"key": "value"})

        merged = engine.merge_identities("elem_a", "elem_b", {"merged": "state"})
        assert "elem_a" in merged.element_id
        assert "elem_b" in merged.element_id
        assert merged.continuity_score == 0.5

    def test_stats(self):
        """Test engine stats."""
        engine = ContinuityIdentityEngine()
        engine.create_checkpoint("elem_1", {"key": "value"})
        engine.create_checkpoint("elem_2", {"key": "value"})

        stats = engine.stats
        assert stats["total_checkpoints"] == 2
        assert stats["tracked_elements"] == 2
        assert stats["avg_continuity"] == 1.0