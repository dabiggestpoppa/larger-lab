"""Tests for Identity Engine."""

import pytest
from oce.backend.temporal.identity_engine import IdentityEngine, IdentityAttractor


class TestIdentityEngine:
    def test_creation(self):
        engine = IdentityEngine(identity_file=".oce/test_identity.json")
        assert engine is not None

    def test_add_mission(self):
        engine = IdentityEngine(identity_file=".oce/test_identity.json")
        engine.add_mission("Build V3 cognitive field")
        assert "Build V3 cognitive field" in engine._mission_vectors

    def test_add_anchor(self):
        engine = IdentityEngine(identity_file=".oce/test_identity.json")
        engine.add_anchor("core_value", "bounded_autonomy")
        assert engine._continuity_anchors["core_value"] == "bounded_autonomy"

    def test_create_attractor(self):
        engine = IdentityEngine(identity_file=".oce/test_identity.json")
        a = engine.create_attractor("mission", weight=0.8)
        assert a.identity_type == "mission"
        assert a.weight == 0.8

    def test_reconstruct_identity(self):
        engine = IdentityEngine(identity_file=".oce/test_identity.json")
        engine.add_mission("test_mission")
        engine.create_attractor("mission")
        result = engine.reconstruct_identity()
        assert "missions" in result
        assert result["missions"] == ["test_mission"]

    def test_verify_integrity(self):
        engine = IdentityEngine(identity_file=".oce/test_identity.json")
        engine.add_anchor("test", "value")
        result = engine.verify_integrity()
        assert result["anchors_intact"] >= 1

    def test_stats(self):
        engine = IdentityEngine(identity_file=".oce/test_identity.json")
        engine.create_attractor("mission")
        stats = engine.stats
        assert stats["attractors"] == 1
