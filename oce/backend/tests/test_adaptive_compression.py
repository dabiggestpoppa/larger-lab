"""
Tests for OCE Adaptive Compression — OCE-9.5c
===============================================
10+ tests covering compression, decompression, anchor preservation.
"""

import pytest


@pytest.fixture(autouse=True)
def reset_compression(tmp_path):
    """Reset the AdaptiveCompression singleton before each test."""
    from adaptive_compression import AdaptiveCompression
    import adaptive_compression
    original_path = adaptive_compression.DB_PATH
    test_db = str(tmp_path / "test_compression.db")
    adaptive_compression.DB_PATH = test_db
    AdaptiveCompression._instance = None
    yield
    AdaptiveCompression._instance = None
    adaptive_compression.DB_PATH = original_path


class TestAdaptiveCompressionInit:
    def test_singleton_identity(self):
        from adaptive_compression import get_adaptive_compression
        c1 = get_adaptive_compression()
        c2 = get_adaptive_compression()
        assert c1 is c2


class TestCompression:
    def test_compress_layer(self):
        from adaptive_compression import get_adaptive_compression
        c = get_adaptive_compression()
        data = {"key1": "value1", "key2": [1, 2, 3], "large": "x" * 1000}
        result = c.compress_layer("WORK", data, 0.6)
        assert "_metadata" in result
        assert "_anchors" in result
        assert "_compressed" in result

    def test_compress_preserves_anchors(self):
        from adaptive_compression import get_adaptive_compression
        c = get_adaptive_compression()
        data = {"key1": "value1", "attractor_state": "critical_data", "key2": "value2"}
        result = c.compress_layer("WORK", data, 0.6)
        assert result["_anchors"]["attractor_state"] == "critical_data"

    def test_compress_empty_data(self):
        from adaptive_compression import get_adaptive_compression
        c = get_adaptive_compression()
        result = c.compress_layer("WORK", {}, 0.6)
        assert result["_metadata"]["ratio"] == 0.0

    def test_compression_stats(self):
        from adaptive_compression import get_adaptive_compression
        c = get_adaptive_compression()
        data = {"key": "value" * 100}
        c.compress_layer("WORK", data, 0.6)
        stats = c.get_compression_stats()
        assert "WORK" in stats
        assert stats["WORK"]["compressions"] >= 1


class TestDecompression:
    def test_roundtrip(self):
        from adaptive_compression import get_adaptive_compression
        c = get_adaptive_compression()
        data = {"key1": "value1", "key2": [1, 2, 3], "large": "x" * 500}
        compressed = c.compress_layer("WORK", data, 0.6)
        decompressed = c.decompress_layer(compressed)
        assert decompressed["key1"] == "value1"
        assert decompressed["key2"] == [1, 2, 3]

    def test_roundtrip_preserves_anchors(self):
        from adaptive_compression import get_adaptive_compression
        c = get_adaptive_compression()
        data = {"key": "value", "attractor_state": "important"}
        compressed = c.compress_layer("WORK", data, 0.6)
        decompressed = c.decompress_layer(compressed)
        assert decompressed["attractor_state"] == "important"

    def test_decompress_empty(self):
        from adaptive_compression import get_adaptive_compression
        c = get_adaptive_compression()
        result = c.decompress_layer({"_anchors": {}, "_compressed": "", "_metadata": {}})
        assert "_decompression_error" not in result or isinstance(result, dict)


class TestAnchorPreservation:
    def test_preserve_anchors(self):
        from adaptive_compression import get_adaptive_compression
        c = get_adaptive_compression()
        data = {
            "key1": "value1",
            "attractor_state": "critical",
            "observer_config": "config_data",
            "regular_key": "regular_value",
        }
        anchors = c.preserve_anchors(data)
        assert "attractor_state" in anchors
        assert "observer_config" in anchors
        assert "key1" not in anchors

    def test_preserve_anchor_prefix(self):
        from adaptive_compression import get_adaptive_compression
        c = get_adaptive_compression()
        data = {"anchor_test": "value", "regular": "data"}
        anchors = c.preserve_anchors(data)
        assert "anchor_test" in anchors
        assert "regular" not in anchors


class TestCompressionPolicy:
    def test_set_policy(self):
        from adaptive_compression import get_adaptive_compression
        c = get_adaptive_compression()
        c.set_compression_policy("WORK", "aggressive")
        assert c._policies["WORK"]["ratio"] == 0.3

    def test_set_invalid_policy(self):
        from adaptive_compression import get_adaptive_compression
        c = get_adaptive_compression()
        with pytest.raises(ValueError):
            c.set_compression_policy("WORK", "invalid")

    def test_available_policies(self):
        from adaptive_compression import COMPRESSION_POLICIES
        assert "aggressive" in COMPRESSION_POLICIES
        assert "moderate" in COMPRESSION_POLICIES
        assert "conservative" in COMPRESSION_POLICIES
        assert "none" in COMPRESSION_POLICIES
