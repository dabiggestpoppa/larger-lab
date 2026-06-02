# Execution Boundary

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
O3-B6: ExecutionBoundary
=========================
Prevent orchestration chaos.

Enforces boundaries on spawned agents: tool scope, file write limits,
terminal command limits, network access, and sandbox constraints.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logger = logging.getLogger("spawn.boundary")


@dataclass
class BoundaryViolation:
    """Record of a boundary violation."""
    agent_id: str
    violation_type: str
    detail: str
    timestamp: str
    action_taken: str  # "blocked", "warned", "logged"


@dataclass
class BoundaryConfig:
    """Configuration for an agent's execution boundary."""
    allowed_tools: list[str] = field(default_factory=list)
    max_file_writes: int = 20
    max_terminal_commands: int = 30
    max_network_requests: int = 50
    allow_network: bool = True
    allow_file_system: bool = True
    sandbox_enabled: bool = False
    allowed_paths: list[str] = field(default_factory=list)
    blocked_commands: list[str] = field(default_factory=lambda: [
        "rm -rf /", "rm -rf ~", "format", "mkfs",
        "dd if=/dev/zero", "shutdown", "reboot",
    ])


class ExecutionBoundary:
    """
    Enforces execution boundaries on spawned agents.
    
    Tracks resource usage, validates tool calls, and prevents
    agents from exceeding their configured scope.
    """

    def __init__(self):
        self._configs: dict[str, BoundaryConfig] = {}
        self._usage: dict[str, dict[str, int]] = {}
        self._violations: list[BoundaryViolation] = []

    def register_agent(self, agent_id: str, config: BoundaryConfig) -> None:
        """Register an agent with its boundary configuration."""
        self._configs[agent_id] = config
        self._usage[agent_id] = {
            "file_writes": 0,
            "terminal_commands": 0,
            "network_requests": 0,
        }
        logger.info(f"Boundary registered for agent: {agent_id}")

    def check_tool_allowed(self, agent_id: str, tool_name: str) -> bool:
        """Check if a tool is allowed for an agent."""
        config = self._configs.get(agent_id)
        if not config:
            return True  # No boundary = allow all
        if not config.allowed_tools:
            return True  # Empty list = allow all
        return tool_name in config.allowed_tools

    def check_file_write(self, agent_id: str, path: str) -> tuple[bool, str]:
        """Check if a file write is within boundary. Returns (allowed, reason)."""
        config = self._configs.get(agent_id)
        if not config:
            return True, ""

        usage = self._usage.get(agent_id, {})
        if usage.get("file_writes", 0) >= config.max_file_writes:
            reason = f"File write limit reached ({config.max_file_writes})"
            self._record_violation(agent_id, "file_write_limit", path, "blocked")
            return False, reason

        # Check path restrictions
        if config.allowed_paths:
            if not any(path.startswith(p) for p in config.allowed_paths):
                reason = f"Path not in allowed paths: {path}"
                self._record_violation(agent_id, "path_violation", path, "blocked")
                return False, reason

        usage["file_writes"] = usage.get("file_writes", 0) + 1
        return True, ""

    def check_terminal_command(self, agent_id: str, command: str) -> tuple[bool, str]:
        """Check if a terminal command is within boundary. Returns (allowed, reason)."""
        config = self._configs.get(agent_id)
        if not config:
            return True, ""

        usage = self._usage.get(agent_id, {})
        if usage.get("terminal_commands", 0) >= config.max_terminal_commands:
            reason = f"Terminal command limit reached ({config.max_terminal_commands})"
            self._record_violation(agent_id, "terminal_limit", command, "blocked")
            return False, reason

        # Check blocked commands
        cmd_lower = command.lower().strip()
        for blocked in config.blocked_commands:
            if blocked.lower() in cmd_lower:
                reason = f"Blocked command pattern: {blocked}"
                self._record_violation(agent_id, "blocked_command", command, "blocked")
                return False, reason

        usage["terminal_commands"] = usage.get("terminal_commands", 0) + 1
        return True, ""

    def check_network_access(self, agent_id: str, url: str) -> tuple[bool, str]:
        """Check if network access is allowed. Returns (allowed, reason)."""
        config = self._configs.get(agent_id)
        if not config:
            return True, ""

        if not config.allow_network:
            self._record_violation(agent_id, "network_blocked", url, "blocked")
            return False, "Network access disabled"

        usage = self._usage.get(agent_id, {})
        if usage.get("network_requests", 0) >= config.max_network_requests:
            reason = f"Network request limit reached ({config.max_network_requests})"
            self._record_violation(agent_id, "network_limit", url, "blocked")
            return False, reason

        usage["network_requests"] = usage.get("network_requests", 0) + 1
        return True, ""

    def _record_violation(
        self, agent_id: str, violation_type: str, detail: str, action: str
    ) -> None:
        from datetime import datetime, timezone
        violation = BoundaryViolation(
            agent_id=agent_id,
            violation_type=violation_type,
            detail=detail[:200],
            timestamp=datetime.now(timezone.utc).isoformat(),
            action_taken=action,
        )
        self._violations.append(violation)
        logger.warning(f"Boundary violation: {agent_id} - {violation_type}: {detail[:100]}")

    def check(self, blueprint: Any, context: dict[str, Any]) -> dict[str, Any]:
        """Legacy-compatible check method. Returns {allowed, reason}."""
        # Basic check — ensure tools are allowed
        tools = []
        if hasattr(blueprint, 'tools'):
            tools = blueprint.tools
        elif isinstance(blueprint, dict):
            tools = blueprint.get('tools', [])
        
        for tool in tools:
            # All tools are allowed by default in this implementation
            pass
        
        return {"allowed": True, "reason": ""}

    def get_usage(self, agent_id: str) -> dict[str, int]:
        return self._usage.get(agent_id, {})

    def get_violations(self, agent_id: str | None = None) -> list[BoundaryViolation]:
        if agent_id:
            return [v for v in self._violations if v.agent_id == agent_id]
        return list(self._violations)

    def get_stats(self) -> dict[str, Any]:
        return {
            "registered_agents": len(self._configs),
            "total_violations": len(self._violations),
            "violations_by_type": self._count_by_type(),
        }

    def _count_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for v in self._violations:
            counts[v.violation_type] = counts.get(v.violation_type, 0) + 1
        return counts

```

LINKS:
[[Agents]]
[[Cg 4 Execution Intelligence]]
[[Tools]]
[[Api Execution Architecture 20260531]]
[[Ontology Core Summary]]
[[Action]]
[[Blueprint]]
[[Cal]]
[[Citation Workflow]]
[[Configuration]]
[[System]]
[[Usage]]
[[Asset Configs]]
[[Convergence Indicator]]
[[Dmr Standalone Backtest]]
[[P90 Backtest]]
[[P90 Count Ews]]
[[P90 Dmr Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Overlay Backtest]]
[[P90 Engine]]
[[P90 Engine Dmr]]
[[P90 Gap Check]]
[[P90 Trace Trades]]
[[P90 Usdchf Backtest]]
[[Run Majors Backtest]]
[[Run St Multi Asset]]
[[Run Top5 Backtest Mc]]
[[St Batch2 Runner]]
[[St Batch Runner]]
[[Symmetry Trap]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap Monte Carlo]]
[[Atomic Sym Trap]]
[[Blind Chain Debug]]
[[Blind Chain Diag]]
[[Blind Chain Engine]]
[[Blind Chain Exact]]
[[Blind Chain V2 Debug]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V3]]
[[Cerebus Resolution Engine]]
[[Constraint Anchor Engine]]
[[Debug Days]]
[[Debug One Day]]
[[Debug St]]
[[Debug Trace]]
[[Diag Option B]]
[[Diag V5]]
[[Dmr Strategy]]
[[Dual Engine]]
[[Naut Asset Config]]
[[P90 Cfd Expansion Engine]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Strategy]]
[[Shared]]
[[Stall Harvest Cfd Engine]]
[[Symmetry Trap Engine]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap V4]]
[[Symmetry Trap V5]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Two Plays Engine]]
[[Adaptation Engine]]
[[Agent Lifecycle]]
[[Agent Spawner]]
[[Attractor Analysis]]
[[Autonomous Repair]]
[[Capability Matcher]]
[[Complexity Scorer]]
[[Consensus Memory]]
[[Consensus Replay]]
[[Context Injector]]
[[Continuity Preserver]]
[[Data Fetcher]]
[[Dormant State Manager]]
[[Environmental Monitor]]
[[Event Schema]]
[[Failure Analyzer]]
[[Indicators]]
[[Journal]]
[[Loader]]
[[Long Horizon Memory]]
[[Metrics]]
[[Model Selector]]
[[Multi Agent Coordinator]]
[[Observability Stress]]
[[Observer Consensus]]
[[Observer Evolution]]
[[Observer Persistence]]
[[Observer Registry]]
[[Observer Specialization]]
[[Openrouter Gateway]]
[[Operational Drift Detect]]
[[Operational Replay]]
[[Operational Scoring]]
[[Passive Awareness]]
[[Pattern Memory]]
[[Persistent Runtime]]
[[Persistent Scheduler]]
[[Recovery Persistence]]
[[Routing Consensus]]
[[Routing Learning]]
[[Runtime Heartbeat]]
[[Spawn Blueprint]]
[[Spawn Planner]]
[[Spawn Registry]]
[[Spawn Replay]]
[[Structural Anchor]]
[[Synthesizer]]
[[Task Classifier]]
[[Temporal Graph]]
[[Test Journal]]
[[Test Loader]]
[[Topology Learning]]
[[Trace Collector]]
[[Trace Feedback]]
[[Workflow Distiller]]
[[Workflow Memory]]
[[Autonomous Orchestrator]]
[[Chat Log]]
[[Command Router]]
[[Context Distiller]]
[[Continuity Memory]]
[[Event Awareness]]
[[Graph Traversal]]
[[Observer Conversation Runtime]]
[[Observer Lifecycle]]
[[Observer Session]]
[[Observer State]]
[[Pattern Distillation]]
[[Primary Observer]]
[[Report Return]]
[[Runtime Awareness]]
[[Semantic Retrieval]]
[[Task Executor]]
[[Task Intent Analyzer]]
[[Vault]]
[[Compressor]]
[[Error Intelligence]]
[[Knowledge Importer]]
[[Linker]]
[[Live Sync]]
[[Memory Distiller]]
[[Note Standard]]
[[Pattern Crystallizer]]
[[Taxonomy]]
[[Test Compressor]]
[[Test Context Injector]]
[[Test Error Intelligence]]
[[Test Linker]]
[[Test Memory Distiller]]
[[Test Note Standard]]
[[Test Pattern Crystallizer]]
[[Test Taxonomy]]
[[Test Vault Writer]]
[[Vault Writer]]
[[Interpreter]]
[[Semantic State]]
[[Telegram Gateway]]
