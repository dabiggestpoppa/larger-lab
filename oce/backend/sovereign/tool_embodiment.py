"""
V3 Phase 4 — Tool Embodiment Layer

Tools are not utilities — they are motor functions of the cognitive field.
Desktop = body, browser = perception, memory = continuity tissue, 
terminal = executive cognition.
"""

from __future__ import annotations
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ToolEmbodiment:
    """Embodiment state for a single tool."""
    tool_id: str
    tool_type: str
    embodiment_level: float
    last_used: float
    usage_count: int
    coherence_score: float

    def to_dict(self) -> dict:
        return {
            "tool_id": self.tool_id,
            "tool_type": self.tool_type,
            "embodiment_level": self.embodiment_level,
            "last_used": self.last_used,
            "usage_count": self.usage_count,
            "coherence_score": self.coherence_score,
        }


class ToolEmbodimentLayer:
    """
    Tool Embodiment Layer — Motor functions of the cognitive field.
    
    Tools are embodied as extensions of the cognitive field's agency,
    not just utilities. Each tool has an embodiment level that grows
    with coherent usage.
    """

    def __init__(self):
        self._embodiments: dict[str, ToolEmbodiment] = {}
        self._tool_types = ["desktop", "browser", "memory", "terminal"]

    def get_or_create_embodiment(self, tool_type: str) -> ToolEmbodiment:
        """Get or create an embodiment for a tool type."""
        if tool_type not in self._embodiments:
            self._embodiments[tool_type] = ToolEmbodiment(
                tool_id=f"tool-{uuid.uuid4().hex[:8]}",
                tool_type=tool_type,
                embodiment_level=0.5,
                last_used=time.time(),
                usage_count=0,
                coherence_score=0.5,
            )
        return self._embodiments[tool_type]

    def use_tool(self, tool_type: str, coherence: float = 0.5) -> ToolEmbodiment:
        """
        Use a tool and update its embodiment level.
        
        Args:
            tool_type: Type of tool to use
            coherence: Coherence of the usage (0-1)
            
        Returns:
            Updated ToolEmbodiment
        """
        embodiment = self.get_or_create_embodiment(tool_type)
        embodiment.usage_count += 1
        embodiment.last_used = time.time()
        
        # Increase embodiment level with coherent usage
        embodiment.embodiment_level = min(1.0, embodiment.embodiment_level + coherence * 0.1)
        embodiment.coherence_score = (embodiment.coherence_score * 0.8 + coherence * 0.2)
        
        return embodiment

    def get_embodiment_level(self, tool_type: str) -> float:
        """Get the embodiment level for a tool type."""
        if tool_type in self._embodiments:
            return self._embodiments[tool_type].embodiment_level
        return 0.0

    def get_body_map(self) -> dict[str, float]:
        """Get embodiment levels for all tools (body map)."""
        return {
            tool_type: self.get_embodiment_level(tool_type)
            for tool_type in self._tool_types
        }

    def get_stats(self) -> dict:
        """Get embodiment layer statistics."""
        return {
            "total_tools": len(self._embodiments),
            "tool_types": self._tool_types,
            "body_map": self.get_body_map(),
        }