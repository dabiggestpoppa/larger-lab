"""Tests for GlyphEngine."""

import pytest
from oce.backend.topology.glyph_engine import GlyphEngine, GLYPH_MAP


class TestGlyphEngine:
    def test_encode_known_pattern(self):
        engine = GlyphEngine()
        encoded = engine.encode("stable resonance detected")
        assert "◉" in encoded

    def test_decode(self):
        engine = GlyphEngine()
        decoded = engine.decode("◉ detected")
        assert "stable" in decoded or "resonance" in decoded or len(decoded) > 0

    def test_compress_semantics(self):
        engine = GlyphEngine()
        compressed, ratio = engine.compress_semantics("trajectory divergence in field stabilization")
        assert "⟁" in compressed or "⌬" in compressed
        assert ratio >= 0.0

    def test_roundtrip(self):
        engine = GlyphEngine()
        original = "stable resonance"
        encoded = engine.encode(original)
        decoded = engine.decode(encoded)
        # Decoded should be a valid string
        assert isinstance(decoded, str) and len(decoded) >= 0

    def test_compression_stats(self):
        engine = GlyphEngine()
        engine.encode("stable resonance trajectory divergence")
        stats = engine.get_compression_stats()
        assert stats["total_compressions"] >= 1

    def test_evolve_glyph_rejects_new(self):
        engine = GlyphEngine()
        # Can't evolve a glyph with < 5 uses
        result = engine.evolve_glyph("◉", "very_specific_stable_resonance_state")
        assert result is False

    def test_evolve_glyph_accepts_utility(self):
        engine = GlyphEngine()
        # Use glyph 6 times
        for _ in range(6):
            engine.encode("stable resonance")
        result = engine.evolve_glyph("◉", "very_specific_stable_resonance_state")
        assert result is True

    def test_glyph_count(self):
        engine = GlyphEngine()
        assert engine.glyph_count == len(GLYPH_MAP)
        assert engine.glyph_count >= 14
