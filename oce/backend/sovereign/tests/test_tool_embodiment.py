"""Tests for Tool Embodiment Layer."""

import pytest
from oce.backend.sovereign.tool_embodiment import ToolEmbodimentLayer, ToolEmbodiment


class TestToolEmbodiment:
    """Tests for ToolEmbodiment dataclass."""

    def test_embodiment_creation(self):
        """Test ToolEmbodiment can be created."""
        embodiment = ToolEmbodiment(
            tool_id="tool-1",
            tool_type="terminal",
            embodiment_level=0.5,
            last_used=12345.0,
            usage_count=10,
            coherence_score=0.8,
        )
        assert embodiment.tool_id == "tool-1"
        assert embodiment.tool_type == "terminal"
        assert embodiment.embodiment_level == 0.5

    def test_embodiment_to_dict(self):
        """Test ToolEmbodiment serialization."""
        embodiment = ToolEmbodiment(
            tool_id="tool-1",
            tool_type="terminal",
            embodiment_level=0.5,
            last_used=12345.0,
            usage_count=10,
            coherence_score=0.8,
        )
        d = embodiment.to_dict()
        assert d["tool_id"] == "tool-1"
        assert d["embodiment_level"] == 0.5


class TestToolEmbodimentLayer:
    """Tests for ToolEmbodimentLayer class."""

    def test_layer_creation(self):
        """Test ToolEmbodimentLayer can be created."""
        layer = ToolEmbodimentLayer()
        assert layer is not None

    def test_get_or_create_embodiment(self):
        """Test getting or creating embodiment."""
        layer = ToolEmbodimentLayer()
        embodiment = layer.get_or_create_embodiment("terminal")
        assert embodiment.tool_type == "terminal"
        assert embodiment.embodiment_level == 0.5

    def test_get_existing_embodiment(self):
        """Test getting existing embodiment."""
        layer = ToolEmbodimentLayer()
        e1 = layer.get_or_create_embodiment("terminal")
        e2 = layer.get_or_create_embodiment("terminal")
        assert e1.tool_id == e2.tool_id

    def test_use_tool(self):
        """Test using a tool."""
        layer = ToolEmbodimentLayer()
        embodiment = layer.use_tool("terminal", coherence=0.8)
        assert embodiment.usage_count == 1
        assert embodiment.embodiment_level > 0.5

    def test_use_tool_multiple_times(self):
        """Test using a tool multiple times."""
        layer = ToolEmbodimentLayer()
        layer.use_tool("terminal", coherence=0.8)
        layer.use_tool("terminal", coherence=0.9)
        embodiment = layer.get_or_create_embodiment("terminal")
        assert embodiment.usage_count == 2
        assert embodiment.embodiment_level > 0.5

    def test_get_embodiment_level(self):
        """Test getting embodiment level."""
        layer = ToolEmbodimentLayer()
        assert layer.get_embodiment_level("terminal") == 0.0
        layer.use_tool("terminal")
        assert layer.get_embodiment_level("terminal") > 0.0

    def test_get_body_map(self):
        """Test getting body map."""
        layer = ToolEmbodimentLayer()
        body_map = layer.get_body_map()
        assert "desktop" in body_map
        assert "browser" in body_map
        assert "memory" in body_map
        assert "terminal" in body_map

    def test_get_stats(self):
        """Test getting layer statistics."""
        layer = ToolEmbodimentLayer()
        stats = layer.get_stats()
        assert "total_tools" in stats
        assert "tool_types" in stats
        assert "body_map" in stats