# Error Intelligence

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #obsidian

```python
"""
Error Intelligence System — Phase 01 Component 1
Categorizes errors into indexed knowledge (not logs).

Core principle: Errors become searchable, linkable knowledge.
Every error has a category, root cause, fix strategy, and prevention rule.

Usage:
    from core.obsidian.error_intelligence import ErrorIntelligence
    ei = ErrorIntelligence(vault_path="/path/to/O2C-VAULT")
    ei.index_error(traceback_str, category="execution", context="...")
    related = ei.find_similar_errors("KeyError: 'price'")
    patterns = ei.get_error_patterns()
"""

import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from collections import defaultdict

from core.obsidian.vault_writer import VaultWriter, DEFAULT_VAULT_PATH
from core.obsidian.compressor import compress_trace


# Error category taxonomy
ERROR_CATEGORIES = [
    "routing",
    "memory",
    "spawn",
    "execution",
    "backtest",
    "pine",
    "mt5",
    "classification",
    "state_mutation",
    "data_validation",
    "api_error",
    "import_error",
    "configuration",
    "unknown",
]

# Error type patterns for auto-classification
ERROR_PATTERNS = {
    "KeyError": ("data_validation", "Missing key in dictionary/data structure"),
    "IndexError": ("data_validation", "Index out of range on sequence"),
    "AttributeError": ("state_mutation", "Object attribute not found — possible state desync"),
    "TypeError": ("data_validation", "Incorrect type passed to operation"),
    "ValueError": ("data_validation", "Invalid value passed to operation"),
    "ImportError": ("import_error", "Module or symbol not found during import"),
    "ModuleNotFoundError": ("import_error", "Module not found"),
    "ConnectionError": ("api_error", "Network/API connection failed"),
    "TimeoutError": ("api_error", "Operation timed out"),
    "AssertionError": ("execution", "Assertion failed — logic invariant violated"),
    "RuntimeError": ("execution", "General runtime error"),
    "StateError": ("state_mutation", "Invalid state transition or state corruption"),
    "ConsensusError": ("routing", "Consensus routing failure"),
    "SpawnError": ("spawn", "Agent spawn failure"),
}


class ErrorIntelligence:
    """Index, categorize, and query errors as operational knowledge."""

    def __init__(self, vault_path: Optional[str | Path] = None):
        self.vault_path = Path(vault_path) if vault_path else DEFAULT_VAULT_PATH
        self.writer = VaultWriter(vault_path=self.vault_path)
        self._error_index: dict[str, list[dict]] = defaultdict(list)

    def classify_error(self, traceback: str) -> tuple[str, str]:
        """
        Auto-classify an error from its traceback.

        Returns: (category, root_cause_description)
        """
        for error_type, (category, description) in ERROR_PATTERNS.items():
            if error_type in traceback:
                return category, description

        # Fallback: try to infer from context
        tb_lower = traceback.lower()
        if "route" in tb_lower or "consensus" in tb_lower:
            return "routing", "Routing or consensus failure"
        if "spawn" in tb_lower or "agent" in tb_lower:
            return "spawn", "Agent spawn or management failure"
        if "state" in tb_lower or "reset" in tb_lower:
            return "state_mutation", "State mutation or corruption"
        if "import" in tb_lower or "module" in tb_lower:
            return "import_error", "Import or module resolution failure"

        return "unknown", "Unclassified error — needs manual review"

    def index_error(
        self,
        traceback: str,
        category: str = "",
        context: str = "",
        fix_applied: str = "",
        result: str = "",
    ) -> dict:
        """
        Index an error into the vault as structured knowledge.

        Args:
            traceback: Raw traceback string
            category: Error category (auto-detected if empty)
            context: What was happening when the error occurred
            fix_applied: What fixed the error
            result: Outcome after fix

        Returns: Dict with error metadata
        """
        # Auto-classify if no category provided
        if not category:
            category, auto_cause = self.classify_error(traceback)
        else:
            auto_cause = ""

        # Extract error type from traceback
        error_type = "Unknown"
        for et in ERROR_PATTERNS:
            if et in traceback:
                error_type = et
                break

        # Build title
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')
        title = f"{error_type} — {category} — {timestamp}"

        # Build content
        content = {
            "cause": context or auto_cause or f"{error_type} occurred during execution",
            "fix": fix_applied or "Pending investigation",
            "result": result or "Pending verification",
            "links": [error_type, category.replace("_", " ").title()],
        }

        # Add traceback reference
        if traceback:
            content["cause"] += f"\n\n```\n{traceback[:500]}\n```"

        # Write to vault
        note_path = self.writer.write_note(
            category="failures",
            title=title,
            content=content,
            tags=[category, error_type.lower()],
            subcategory=category if category in ERROR_CATEGORIES else None,
        )

        # Update in-memory index
        error_entry = {
            "title": title,
            "category": category,
            "error_type": error_type,
            "path": note_path["path"] if isinstance(note_path, dict) else str(note_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fix_applied": fix_applied,
        }
        self._error_index[category].append(error_entry)

        return error_entry

    def find_similar_errors(self, query: str, limit: int = 10) -> list[dict]:
        """Find errors similar to the query from the vault."""
        all_notes = self.writer.list_notes(category="failures")
        results = []
        query_lower = query.lower()

        for note in all_notes:
            title = note.get("title", "")
            tags = note.get("tags", [])
            if query_lower in title.lower() or any(query_lower in t.lower() for t in tags):
                results.append(note)
            if len(results) >= limit:
                break

        return results

    def get_error_patterns(self) -> dict:
        """
        Analyze indexed errors to find recurring patterns.

        Returns: Dict of {category: count, ...} and top error types
        """
        all_notes = self.writer.list_notes(category="failures")
        category_counts = defaultdict(int)
        error_type_counts = defaultdict(int)

        for note in all_notes:
            cat = note.get("category", "unknown")
            category_counts[cat] += 1
            # Extract error type from title
            title = note.get("title", "")
            for et in ERROR_PATTERNS:
                if et in title:
                    error_type_counts[et] += 1
                    break

        return {
            "total_errors": len(all_notes),
            "by_category": dict(category_counts),
            "by_type": dict(error_type_counts),
            "top_category": max(category_counts, key=category_counts.get) if category_counts else None,
            "top_error_type": max(error_type_counts, key=error_type_counts.get) if error_type_counts else None,
        }

    def get_prevention_rules(self) -> list[dict]:
        """Extract prevention rules from indexed errors."""
        all_notes = self.writer.list_notes(category="failures")
        rules = []

        for note in all_notes:
            title = note.get("title", "")
            tags = note.get("tags", [])
            # Each error note becomes a prevention rule
            rules.append({
                "error": title,
                "category": tags[0] if tags else "unknown",
                "prevention": f"Check for {title.split('—')[0].strip()} before execution",
            })

        return rules

```

LINKS:
[[Cg 4 Execution Intelligence]]
[[Cg 5 Continuity Intelligence]]
[[User]]
[[Hermes Obsidian Test   Vault Working]]
[[Obsidian Vault Connection Info]]
[[Ontology Core Summary]]
[[Sage Audit Environment Utilization]]
[[Citation Workflow]]
[[Configuration]]
[[Description]]
[[Failures]]
[[Patterns]]
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
