"""Tests for Temporal Compression Engine."""

import pytest
from oce.backend.temporal.temporal_compression import TemporalCompressionEngine, CompressionResult


class TestCompressionResult:
    def test_effective(self):
        r = CompressionResult(original_count=100, compressed_count=10, compression_ratio=0.9, attractors_formed=5)
        assert r.is_effective is True

    def test_not_effective(self):
        r = CompressionResult(original_count=100, compressed_count=80, compression_ratio=0.2, attractors_formed=2)
        assert r.is_effective is False


class TestTemporalCompressionEngine:
    def test_compress_trajectory(self):
        engine = TemporalCompressionEngine()
        states = [f"s{i}" for i in range(20)]
        coherence = [0.8 + (i % 3) * 0.05 for i in range(20)]
        result = engine.compress_trajectory(states, coherence)
        assert result.original_count == 20
        assert result.compression_ratio >= 0.0

    def test_extract_attractor(self):
        engine = TemporalCompressionEngine()
        states = [f"s{i}" for i in range(10)]
        coherence = [0.9 - i * 0.05 for i in range(10)]
        attractor = engine.extract_attractor(states, coherence)
        assert attractor is not None

    def test_stats(self):
        engine = TemporalCompressionEngine()
        engine.compress_trajectory(["s1", "s2"], [0.8, 0.9])
        stats = engine.stats
        assert stats["total_compressions"] == 1
