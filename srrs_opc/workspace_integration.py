"""
Workspace Integration Layer
=============================
Phase 4: Map workspace tools to SRRA substrate roles.

Each tool becomes an adapter surface — NOT a cognition authority.
Tools are interchangeable limbs, not identity containers.

Mapping:
- OpenClaw → strategic synthesis patch
- Hermes → execution patch
- Nautilus → environment verification
- Claude → symbolic reasoning interface
- Terminal → execution surface
- VPS/Cloud → distributed persistence topology
"""

import json
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum

if sys.platform == "win32":
    import codecs
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class ToolRole(Enum):
    """SRRA roles for workspace tools."""
    STRATEGIC_SYNTHESIS = "strategic_synthesis"
    EXECUTION = "execution"
    ENVIRONMENT_VERIFICATION = "environment_verification"
    SYMBOLIC_REASONING = "symbolic_reasoning"
    EXECUTION_SURFACE = "execution_surface"
    PERSISTENCE_TOPOLOGY = "persistence_topology"


class ToolAdapter:
    """
    Adapter interface for workspace tools.
    Each tool connects through a bounded adapter — never directly integrated.
    """

    def __init__(self, tool_name: str, role: ToolRole, capabilities: List[str]):
        self.tool_name = tool_name
        self.role = role
        self.capabilities = capabilities
        self.is_available = False
        self.last_health_check = None
        self.error_count = 0

    def health_check(self) -> bool:
        """Check if the tool is available and responsive."""
        self.last_health_check = datetime.now(timezone.utc).isoformat()
        return self.is_available

    def execute(self, command: str, params: dict = None) -> dict:
        """Execute a command through this tool adapter."""
        raise NotImplementedError("Subclasses must implement execute()")

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "role": self.role.value,
            "capabilities": self.capabilities,
            "is_available": self.is_available,
            "last_health_check": self.last_health_check,
            "error_count": self.error_count,
        }


class OpenClawAdapter(ToolAdapter):
    """OpenClaw → strategic synthesis patch."""

    def __init__(self):
        super().__init__(
            tool_name="OpenClaw",
            role=ToolRole.STRATEGIC_SYNTHESIS,
            capabilities=["planning", "coordination", "analysis", "gateway"]
        )

    def health_check(self) -> bool:
        """Check if OpenClaw gateway is running."""
        import subprocess
        try:
            result = subprocess.run(
                ["openclaw", "gateway", "status"],
                capture_output=True, text=True, timeout=10,
                encoding="utf-8", errors="replace"
            )
            self.is_available = result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.is_available = False
        return self.is_available

    def execute(self, command: str, params: dict = None) -> dict:
        """Execute via OpenClaw gateway."""
        if not self.is_available:
            return {"status": "error", "message": "OpenClaw not available"}
        # In production, this would route through OpenClaw's gateway protocol
        return {"status": "delegated", "tool": "openclaw", "command": command}


class HermesAdapter(ToolAdapter):
    """Hermes → execution patch."""

    def __init__(self):
        super().__init__(
            tool_name="Hermes",
            role=ToolRole.EXECUTION,
            capabilities=["backtesting", "data_prep", "reporting", "telegram"]
        )

    def health_check(self) -> bool:
        """Check if Hermes bot is responsive."""
        # Check if Hermes process or Telegram bot is reachable
        self.is_available = True  # Placeholder
        return self.is_available

    def execute(self, command: str, params: dict = None) -> dict:
        """Execute via Hermes."""
        return {"status": "delegated", "tool": "hermes", "command": command}


class NautilusAdapter(ToolAdapter):
    """Nautilus → environment verification."""

    def __init__(self):
        super().__init__(
            tool_name="Nautilus",
            role=ToolRole.ENVIRONMENT_VERIFICATION,
            capabilities=["backtesting", "verification", "data_validation"]
        )

    def health_check(self) -> bool:
        """Check if Nautilus backtest engine is available."""
        import os
        nautilus_path = os.path.join(os.path.dirname(__file__), "..", "nautilus")
        self.is_available = os.path.exists(nautilus_path)
        return self.is_available

    def execute(self, command: str, params: dict = None) -> dict:
        """Execute via Nautilus."""
        return {"status": "delegated", "tool": "nautilus", "command": command}


class ClaudeAdapter(ToolAdapter):
    """Claude → symbolic reasoning interface."""

    def __init__(self):
        super().__init__(
            tool_name="Claude",
            role=ToolRole.SYMBOLIC_REASONING,
            capabilities=["reasoning", "coding", "analysis", "architecture"]
        )
        self.is_available = True  # Always available (this IS Claude)

    def health_check(self) -> bool:
        self.is_available = True
        return True

    def execute(self, command: str, params: dict = None) -> dict:
        """Execute via Claude (this is the current agent)."""
        return {"status": "self", "tool": "claude", "command": command}


class WorkspaceIntegrationLayer:
    """
    Manages all workspace tool adapters.
    Ensures tools are interchangeable and never become identity authorities.
    """

    def __init__(self):
        self.adapters: Dict[str, ToolAdapter] = {}
        self._register_defaults()

    def _register_defaults(self):
        """Register default workspace tool adapters."""
        self.register(OpenClawAdapter())
        self.register(HermesAdapter())
        self.register(NautilusAdapter())
        self.register(ClaudeAdapter())

    def register(self, adapter: ToolAdapter):
        """Register a tool adapter."""
        self.adapters[adapter.tool_name] = adapter

    def get_adapter(self, tool_name: str) -> Optional[ToolAdapter]:
        """Get a tool adapter by name."""
        return self.adapters.get(tool_name)

    def get_by_role(self, role: ToolRole) -> List[ToolAdapter]:
        """Get all adapters for a given SRRA role."""
        return [a for a in self.adapters.values() if a.role == role]

    def health_check_all(self) -> Dict[str, bool]:
        """Run health checks on all registered tools."""
        results = {}
        for name, adapter in self.adapters.items():
            try:
                results[name] = adapter.health_check()
            except Exception as e:
                results[name] = False
                adapter.error_count += 1
        return results

    def route_task(self, task_type: str, command: str, params: dict = None) -> dict:
        """
        Route a task to the appropriate tool based on task type.
        This is the key Phase 4 mechanism — tasks route through SRRA roles,
        not directly to tools.
        """
        role_map = {
            "planning": ToolRole.STRATEGIC_SYNTHESIS,
            "analysis": ToolRole.STRATEGIC_SYNTHESIS,
            "execution": ToolRole.EXECUTION,
            "backtest": ToolRole.EXECUTION,
            "verification": ToolRole.ENVIRONMENT_VERIFICATION,
            "reasoning": ToolRole.SYMBOLIC_REASONING,
            "coding": ToolRole.SYMBOLIC_REASONING,
        }

        role = role_map.get(task_type)
        if not role:
            return {"status": "error", "message": f"Unknown task type: {task_type}"}

        adapters = self.get_by_role(role)
        if not adapters:
            return {"status": "error", "message": f"No adapter for role: {role.value}"}

        # Use first available adapter
        for adapter in adapters:
            if adapter.health_check():
                return adapter.execute(command, params)

        return {"status": "error", "message": f"No available adapter for role: {role.value}"}

    def get_status(self) -> dict:
        """Get full workspace integration status."""
        health = self.health_check_all()
        return {
            "tools": {name: adapter.to_dict() for name, adapter in self.adapters.items()},
            "health": health,
            "available_count": sum(1 for v in health.values() if v),
            "total_count": len(health),
        }


# Global integration layer
_integration_layer = None


def get_integration_layer() -> WorkspaceIntegrationLayer:
    """Get the global workspace integration layer."""
    global _integration_layer
    if _integration_layer is None:
        _integration_layer = WorkspaceIntegrationLayer()
    return _integration_layer


if __name__ == "__main__":
    layer = get_integration_layer()
    status = layer.get_status()
    print(json.dumps(status, indent=2))
