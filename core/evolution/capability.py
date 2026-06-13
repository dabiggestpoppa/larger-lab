"""Phase 1.7.6 — Capability Generation Engine. System creates new internal tools."""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.evolution.capability")


class CapabilityGenerationEngine:
    """System creates new internal tools when a capability is repeatedly needed."""

    def __init__(self):
        self._needed_capabilities: Dict[str, int] = {}
        self._generated_tools: Dict[str, str] = {}

    def record_need(self, capability: str):
        """Record that a capability was needed."""
        self._needed_capabilities[capability] = self._needed_capabilities.get(capability, 0) + 1

    def should_generate(self, capability: str, threshold: int = 3) -> bool:
        """Check if a capability should be generated."""
        return (
            self._needed_capabilities.get(capability, 0) >= threshold
            and capability not in self._generated_tools
        )

    def generate_tool(self, capability: str) -> Optional[str]:
        """Generate a tool for a capability. Returns tool name."""
        if not self.should_generate(capability):
            return None

        tool_name = f"{capability}_tool"
        self._generated_tools[tool_name] = capability
        logger.info(f"Capability generated: {tool_name} for {capability}")
        return tool_name

    def get_stats(self) -> Dict[str, Any]:
        return {
            "needed_capabilities": dict(self._needed_capabilities),
            "generated_tools": dict(self._generated_tools),
        }
