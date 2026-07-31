# Taxonomy

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #obsidian

```python
"""
Doctrine Taxonomy — Phase 0H
Enforce vault structure. Prevent entropy landfill.

Core principle: Without taxonomy, the vault becomes a garbage dump.
Every note MUST be in the correct category. Every category has a purpose.

Usage:
    from core.obsidian.taxonomy import Taxonomy
    tax = Taxonomy(vault_path="/path/to/O2C-VAULT")
    issues = tax.validate()  # Returns list of structural issues
    tax.enforce()             # Auto-fix issues where possible
"""

import re
from pathlib import Path
from typing import Optional

from core.obsidian.vault_writer import VAULT_DIRECTORIES, VALID_CATEGORIES, DEFAULT_VAULT_PATH


# Category descriptions — what belongs where
CATEGORY_RULES = {
    "agents": "Agent execution reports, spawn logs, agent journals",
    "memory": "Successful patterns, error corrections, spawn history, consensus failures",
    "ontology": "Domain models, system architecture, routing logic, state machines",
    "graphs": "Agent relationships, execution flows, knowledge clusters",
    "journals": "Daily runtime logs, backtest logs, forward test logs",
    "doctrine": "Core operational principles, architectural decisions, design patterns",
    "failures": "Failure patterns, root causes, fixes, prevention strategies",
    "execution": "Execution traces, runtime observations, performance data",
    "skills": "Portable operational capabilities, executable procedures",
    "heuristics": "Rules of thumb, decision shortcuts, operational patterns",
    "routing": "Task routing patterns, consensus routing, model selection",
    "architecture": "System architecture notes, design decisions, component maps",
}

# Required top-level directories
REQUIRED_DIRS = [d.split("/")[0] for d in VAULT_DIRECTORIES]
REQUIRED_DIRS = list(set(REQUIRED_DIRS))


class Taxonomy:
    """Enforce vault structure and prevent entropy landfill."""

    def __init__(self, vault_path: Optional[str] = None):
        self.vault_path = Path(vault_path) if vault_path else DEFAULT_VAULT_PATH

    def validate(self) -> list[dict]:
        """
        Validate vault structure. Returns list of issues.

        Each issue is a dict: {type, path, message, fixable}
        """
        issues = []

        # Check required directories exist
        for dir_name in REQUIRED_DIRS:
            dir_path = self.vault_path / dir_name
            if not dir_path.exists():
                issues.append({
                    "type": "missing_directory",
                    "path": str(dir_path),
                    "message": f"Required directory '{dir_name}' is missing",
                    "fixable": True,
                })

        # Check for files in wrong locations (files directly in vault root)
        for item in self.vault_path.iterdir():
            if item.is_file() and item.suffix == ".md":
                issues.append({
                    "type": "orphan_file",
                    "path": str(item),
                    "message": f"Markdown file '{item.name}' is in vault root — should be in a category",
                    "fixable": False,  # Can't auto-determine category
                })

        # Check for unknown top-level directories
        for item in self.vault_path.iterdir():
            if item.is_dir() and item.name not in REQUIRED_DIRS:
                issues.append({
                    "type": "unknown_directory",
                    "path": str(item),
                    "message": f"Unknown directory '{item.name}' — not in taxonomy",
                    "fixable": False,
                })

        # Validate note format in all notes
        for note_path in self.vault_path.rglob("*.md"):
            content = note_path.read_text(encoding="utf-8")
            note_issues = self._validate_note_format(note_path, content)
            issues.extend(note_issues)

        return issues

    def _validate_note_format(self, path: Path, content: str) -> list[dict]:
        """Validate a single note follows the standard."""
        issues = []
        rel_path = str(path.relative_to(self.vault_path))

        # Check for title
        if not re.search(r"^#\s+.+$", content, re.MULTILINE):
            issues.append({
                "type": "missing_title",
                "path": rel_path,
                "message": "Note missing a # Title header",
                "fixable": False,
            })

        # Check for at least CAUSE or content
        if "CAUSE:" not in content and "FIX:" not in content:
            # Some notes (like doctrine) may not follow full format — just warn
            if len(content.strip()) < 50:
                issues.append({
                    "type": "empty_note",
                    "path": rel_path,
                    "message": "Note appears empty or too short",
                    "fixable": False,
                })

        return issues

    def enforce(self) -> list[str]:
        """
        Auto-fix structural issues where possible.

        Returns list of actions taken.
        """
        actions = []

        # Create missing directories
        for dir_path_str in VAULT_DIRECTORIES:
            dir_path = self.vault_path / dir_path_str
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                actions.append(f"Created directory: {dir_path_str}")

        return actions

    def get_category_for_note(self, title: str, content: str) -> str:
        """
        Suggest a category for a note based on its content.

        Returns the suggested category name.
        """
        content_lower = content.lower()
        title_lower = title.lower()

        # Keyword-based classification
        if any(w in content_lower for w in ["error", "failed", "bug", "fix", "traceback", "exception"]):
            return "failures"
        if any(w in content_lower for w in ["pattern", "heuristic", "rule of thumb", "shortcut"]):
            return "heuristics"
        if any(w in content_lower for w in ["skill", "procedure", "workflow", "how to"]):
            return "skills"
        if any(w in content_lower for w in ["architecture", "design", "component", "system"]):
            return "architecture"
        if any(w in content_lower for w in ["route", "routing", "consensus", "spawn"]):
            return "routing"
        if any(w in content_lower for w in ["ontology", "domain model", "state machine", "schema"]):
            return "ontology"
        if any(w in content_lower for w in ["agent", "spawn", "execution report"]):
            return "agents"
        if any(w in content_lower for w in ["journal", "log", "daily", "runtime"]):
            return "journals"

        return "doctrine"  # Default

    def get_stats(self) -> dict:
        """Get vault taxonomy statistics."""
        stats = {cat: 0 for cat in REQUIRED_DIRS}
        stats["unknown"] = 0
        stats["total"] = 0

        for note_path in self.vault_path.rglob("*.md"):
            stats["total"] += 1
            # Get top-level category from relative path
            parts = note_path.relative_to(self.vault_path).parts
            if parts[0] in stats:
                stats[parts[0]] += 1
            else:
                stats["unknown"] += 1

        return stats

```

LINKS:
[[Architecture]]
[[System Architecture]]
[[Agents]]
[[Principles]]
[[Hermes Obsidian Test   Vault Working]]
[[Obsidian Vault Connection Info]]
[[Ontology Core Summary]]
[[Sage Audit Environment Utilization]]
[[Action]]
[[Citation Workflow]]
[[Description]]
[[Failures]]
[[Heuristics]]
[[Patterns]]
[[Skill]]
[[Standard]]
[[System]]
[[Usage]]
[[Workflow]]
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
[[Memory]]
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
[[Execution Boundary]]
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
