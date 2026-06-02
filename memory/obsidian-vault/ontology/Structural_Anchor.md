# Structural Anchor

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #core

```python
"""
CG-3: OpenClaw Structural Anchor
==================================
Topology overlay for OpenClaw's planning loop.

Provides:
- Topology Thinking Template (structured planning)
- Dependency Check Habit (pre-execution validation)
- Execution Topology Memory (lesson storage)
- Tool Sequencing Governance (ordered, validated execution)
- Structural Validation Layer (pre-action checks)

This is AUGMENTATION of OpenClaw, NOT replacement.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("cg3.structural_anchor")


# ── Topology Thinking Template ───────────────────────────────────────────────

@dataclass
class TopologyPlan:
    """Structured plan following CG-3 topology thinking template."""
    objective: str = ""
    nodes: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    risks: List[str] = field(default_factory=list)
    validations: List[str] = field(default_factory=list)
    execution_order: List[str] = field(default_factory=list)
    rollback_points: Dict[str, str] = field(default_factory=dict)

    def validate(self) -> tuple[bool, List[str]]:
        """Validate the plan. Returns (is_valid, list_of_issues)."""
        issues = []

        if not self.objective:
            issues.append("No objective defined")

        if not self.nodes:
            issues.append("No nodes identified")

        # Check for circular dependencies
        visited = set()
        stack = set()

        def has_cycle(node: str) -> bool:
            if node in stack:
                return True
            if node in visited:
                return False
            visited.add(node)
            stack.add(node)
            for dep in self.dependencies.get(node, []):
                if has_cycle(dep):
                    return True
            stack.discard(node)
            return False

        for node in self.nodes:
            if has_cycle(node):
                issues.append(f"Circular dependency detected involving: {node}")

        # Check for missing dependencies
        for node, deps in self.dependencies.items():
            for dep in deps:
                if dep not in self.nodes:
                    issues.append(f"Dependency '{dep}' of '{node}' not in nodes list")

        # Check for rollback points
        for node in self.nodes:
            if node not in self.rollback_points:
                issues.append(f"No rollback point for: {node}")

        return (len(issues) == 0, issues)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective": self.objective,
            "nodes": self.nodes,
            "dependencies": self.dependencies,
            "risks": self.risks,
            "validations": self.validations,
            "execution_order": self.execution_order,
            "rollback_points": self.rollback_points,
        }

    def to_markdown(self) -> str:
        lines = [
            f"# Topology Plan: {self.objective}",
            "",
            "## Nodes",
        ]
        for node in self.nodes:
            lines.append(f"- {node}")

        lines.extend(["", "## Dependencies"])
        for node, deps in self.dependencies.items():
            for dep in deps:
                lines.append(f"- {node} → depends on → {dep}")

        lines.extend(["", "## Risks"])
        for risk in self.risks:
            lines.append(f"- ⚠ {risk}")

        lines.extend(["", "## Validations"])
        for val in self.validations:
            lines.append(f"- [ ] {val}")

        lines.extend(["", "## Execution Order"])
        for i, step in enumerate(self.execution_order, 1):
            rollback = self.rollback_points.get(step, "none")
            lines.append(f"{i}. {step} (rollback: {rollback})")

        return "\n".join(lines)


# ── Dependency Check ─────────────────────────────────────────────────────────

class DependencyChecker:
    """Pre-execution dependency validation."""

    @staticmethod
    def check_dependencies(
        task: str,
        prerequisites: Dict[str, bool],
    ) -> tuple[bool, List[str]]:
        """
        Check if all prerequisites are met.
        Returns (all_met, list_of_missing).
        """
        missing = [
            name for name, met in prerequisites.items() if not met
        ]
        return (len(missing) == 0, missing)

    @staticmethod
    def map_propagation(
        target: str,
        dependency_graph: Dict[str, List[str]],
    ) -> List[str]:
        """
        Map what would be affected if `target` fails.
        Returns list of affected nodes (BFS from target through reverse deps).
        """
        # Build reverse graph
        reverse: Dict[str, List[str]] = {}
        for node, deps in dependency_graph.items():
            for dep in deps:
                if dep not in reverse:
                    reverse[dep] = []
                reverse[dep].append(node)

        # BFS from target
        affected = []
        visited = {target}
        queue = [target]

        while queue:
            current = queue.pop(0)
            for dependent in reverse.get(current, []):
                if dependent not in visited:
                    visited.add(dependent)
                    affected.append(dependent)
                    queue.append(dependent)

        return affected

    @staticmethod
    def suggest_rollback(target: str, state_snapshots: Dict[str, Any]) -> Optional[str]:
        """Suggest rollback action based on available state snapshots."""
        if target in state_snapshots:
            snapshot = state_snapshots[target]
            if isinstance(snapshot, dict) and "path" in snapshot:
                return f"Restore {target} from {snapshot['path']}"
            return f"Restore {target} from snapshot ({type(snapshot).__name__})"
        return None


# ── Execution Topology Memory ─────────────────────────────────────────────────

class TopologyMemory:
    """Store and retrieve topology lessons in O2C-VAULT."""

    def __init__(self, vault_path: Optional[Path] = None):
        from core.obsidian.vault_writer import VaultWriter
        self._writer = Writer = VaultWriter()
        self._vault = vault_path or Path("O2C-VAULT")

    def store_lesson(
        self,
        category: str,  # "failures", "dependencies", "rollback", "stability"
        title: str,
        cause: str,
        fix: str,
        result: str,
        links: Optional[List[str]] = None,
    ) -> str:
        """Store a topology lesson in the vault."""
        content = f"""# {title}

CAUSE:
{cause}

FIX:
{fix}

RESULT:
{result}

LINKS:
[[Telegram Gateway]]
[[Semantic State]]
[[Interpreter]]
[[Vault Writer]]
[[Test Vault Writer]]
[[Test Taxonomy]]
[[Test Pattern Crystallizer]]
[[Test Note Standard]]
[[Test Memory Distiller]]
[[Test Linker]]
[[Test Error Intelligence]]
[[Test Context Injector]]
[[Test Compressor]]
[[Taxonomy]]
[[Pattern Crystallizer]]
[[Note Standard]]
[[Memory Distiller]]
[[Live Sync]]
[[Linker]]
[[Knowledge Importer]]
[[Error Intelligence]]
[[Compressor]]
[[Vault]]
[[Task Intent Analyzer]]
[[Task Executor]]
[[Semantic Retrieval]]
[[Runtime Awareness]]
[[Report Return]]
[[Primary Observer]]
[[Pattern Distillation]]
[[Observer State]]
[[Observer Session]]
[[Observer Lifecycle]]
[[Observer Conversation Runtime]]
[[Graph Traversal]]
[[Event Awareness]]
[[Continuity Memory]]
[[Context Distiller]]
[[Command Router]]
[[Chat Log]]
[[Autonomous Orchestrator]]
[[Workflow Memory]]
[[Workflow Distiller]]
[[Trace Feedback]]
[[Trace Collector]]
[[Topology Learning]]
[[Test Loader]]
[[Test Journal]]
[[Temporal Graph]]
[[Task Classifier]]
[[Synthesizer]]
[[Spawn Replay]]
[[Spawn Registry]]
[[Spawn Planner]]
[[Spawn Blueprint]]
[[Runtime Heartbeat]]
[[Routing Learning]]
[[Routing Consensus]]
[[Recovery Persistence]]
[[Persistent Scheduler]]
[[Persistent Runtime]]
[[Pattern Memory]]
[[Passive Awareness]]
[[Operational Scoring]]
[[Operational Replay]]
[[Operational Drift Detect]]
[[Openrouter Gateway]]
[[Observer Specialization]]
[[Observer Registry]]
[[Observer Persistence]]
[[Observer Evolution]]
[[Observer Consensus]]
[[Observability Stress]]
[[Multi Agent Coordinator]]
[[Model Selector]]
[[Metrics]]
[[Long Horizon Memory]]
[[Loader]]
[[Journal]]
[[Indicators]]
[[Failure Analyzer]]
[[Execution Boundary]]
[[Event Schema]]
[[Environmental Monitor]]
[[Dormant State Manager]]
[[Data Fetcher]]
[[Continuity Preserver]]
[[Context Injector]]
[[Consensus Replay]]
[[Consensus Memory]]
[[Complexity Scorer]]
[[Capability Matcher]]
[[Autonomous Repair]]
[[Attractor Analysis]]
[[Agent Spawner]]
[[Agent Lifecycle]]
[[Adaptation Engine]]
[[Two Plays Engine]]
[[Symmetry Trap V7 Sl Calibrated]]
[[Symmetry Trap V7B Sl Calibrated]]
[[Symmetry Trap V6 Exact]]
[[Symmetry Trap V5]]
[[Symmetry Trap V4]]
[[Symmetry Trap Strategy]]
[[Symmetry Trap Option B]]
[[Symmetry Trap Exact]]
[[Symmetry Trap Engine]]
[[Stall Harvest Cfd Engine]]
[[Shared]]
[[P90 Strategy]]
[[P90 Cfd Expansion Engine V5]]
[[P90 Cfd Expansion Engine V4]]
[[P90 Cfd Expansion Engine V3]]
[[P90 Cfd Expansion Engine V2]]
[[P90 Cfd Expansion Engine]]
[[Naut Asset Config]]
[[Dual Engine]]
[[Dmr Strategy]]
[[Diag V5]]
[[Diag Option B]]
[[Debug Trace]]
[[Debug St]]
[[Debug One Day]]
[[Debug Days]]
[[Constraint Anchor Engine]]
[[Cerebus Resolution Engine]]
[[Blind Chain V3]]
[[Blind Chain V2 Sl Calibrated]]
[[Blind Chain V2 Debug]]
[[Blind Chain Exact]]
[[Blind Chain Engine]]
[[Blind Chain Diag]]
[[Blind Chain Debug]]
[[Atomic Sym Trap]]
[[Memory]]
[[Symmetry Trap Monte Carlo]]
[[Symmetry Trap Backtest]]
[[Symmetry Trap]]
[[St Batch Runner]]
[[St Batch2 Runner]]
[[Run Top5 Backtest Mc]]
[[Run St Multi Asset]]
[[Run Majors Backtest]]
[[P90 Usdchf Backtest]]
[[P90 Trace Trades]]
[[P90 Gap Check]]
[[P90 Engine Dmr]]
[[P90 Engine]]
[[P90 Dmr Overlay Backtest]]
[[P90 Dmr Combo Backtest]]
[[P90 Dmr Backtest]]
[[P90 Count Ews]]
[[P90 Backtest]]
[[Dmr Standalone Backtest]]
[[Convergence Indicator]]
[[Asset Configs]]
[[System]]
[[Structural Breakdown]]
[[Failures]]
[[Expo]]
[[Citation Workflow]]
[[Cal]]
[[Action]]
[[Ontology Core Summary]]
[[Tools]]
[[Cg 3 Openclaw Anchor]]
{chr(10).join(f'[[{l}]]' for l in (links or []))}
"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{category}/{timestamp}_{title.replace(' ', '_')}.md"

        from core.obsidian.live_sync import write_and_sync
        write_and_sync(filename, content)

        logger.info(f"Stored topology lesson: {filename}")
        return filename

    def get_lessons(self, category: str) -> List[Dict[str, Any]]:
        """Retrieve topology lessons by category."""
        from core.obsidian.vault_writer import VaultWriter
        writer = VaultWriter()
        return writer.list_notes(category=category)


# ── Structural Validation Layer ───────────────────────────────────────────────

class StructuralValidator:
    """Pre-action structural validation."""

    @staticmethod
    def validate_before_action(
        action: str,
        context: Dict[str, Any],
    ) -> tuple[bool, List[str]]:
        """
        Run structural validation before any action.
        Returns (is_valid, list_of_issues).
        """
        issues = []

        # Check 1: Dependency completeness
        deps = context.get("dependencies", {})
        for dep, met in deps.items():
            if not met:
                issues.append(f"Dependency not met: {dep}")

        # Check 2: Rollback presence
        if not context.get("rollback_plan"):
            issues.append("No rollback plan defined")

        # Check 3: Propagation exposure
        affected = context.get("affected_nodes", [])
        if affected:
            logger.warning(f"Action '{action}' affects {len(affected)} nodes: {affected}")

        # Check 4: Continuity stability
        if not context.get("state_preserved", True):
            issues.append("System state may not be preserved on failure")

        return (len(issues) == 0, issues)

    @staticmethod
    def create_state_snapshot(target: str, state: Any) -> Dict[str, Any]:
        """Create a state snapshot for rollback."""
        return {
            "target": target,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": state,
            "type": type(state).__name__,
        }


# ── Tool Sequencing Governance ────────────────────────────────────────────────

class ToolSequencer:
    """Governs tool selection, ordering, and validation."""

    @staticmethod
    def sequence_tools(
        tools: List[str],
        dependencies: Optional[Dict[str, List[str]]] = None,
    ) -> List[str]:
        """
        Order tools based on dependencies (topological sort).
        """
        if not dependencies:
            return tools

        # Simple topological sort
        ordered = []
        visited = set()
        temp_mark = set()

        def visit(tool: str):
            if tool in temp_mark:
                logger.warning(f"Circular tool dependency detected: {tool}")
                return
            if tool in visited:
                return
            temp_mark.add(tool)
            for dep in dependencies.get(tool, []):
                visit(dep)
            temp_mark.discard(tool)
            visited.add(tool)
            ordered.append(tool)

        for tool in tools:
            visit(tool)

        return ordered

    @staticmethod
    def validate_tool_chain(tools: List[str]) -> tuple[bool, List[str]]:
        """Validate a chain of tools for dependency completeness."""
        issues = []
        available = set()

        for i, tool in enumerate(tools):
            # Each tool should be usable given what came before
            if i > 0 and tool not in available:
                # Check if previous tools produce what this one needs
                pass  # Tool-specific validation would go here
            available.add(tool)

        return (len(issues) == 0, issues)

```