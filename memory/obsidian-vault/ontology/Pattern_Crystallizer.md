# Pattern Crystallizer

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #obsidian

```python
"""
Pattern Crystallization Engine — Phase 01 Component 2
Extracts recurring operational structures from vault notes.

Core principle: When recurring structures appear, they become reusable ontology patterns.
These are cognitive primitives — the building blocks of operational intelligence.

Usage:
    from core.obsidian.pattern_crystallizer import PatternCrystallizer
    pc = PatternCrystallizer(vault_path="/path/to/O2C-VAULT")
    patterns = pc.extract_patterns()
    pc.crystallize_pattern("Stable Multi-Agent Research Pattern", conditions, result)
"""

import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from collections import Counter

from core.obsidian.vault_writer import VaultWriter, DEFAULT_VAULT_PATH


class PatternCrystallizer:
    """Extract and crystallize recurring operational patterns."""

    def __init__(self, vault_path: Optional[str | Path] = None):
        self.vault_path = Path(vault_path) if vault_path else DEFAULT_VAULT_PATH
        self.writer = VaultWriter(vault_path=self.vault_path)

    def extract_patterns(self, min_occurrences: int = 2) -> list[dict]:
        """
        Scan vault for recurring patterns.

        Looks for:
        - Repeated tags across notes
        - Shared links between notes
        - Common error categories
        - Frequently co-occurring concepts

        Returns: List of pattern dicts
        """
        all_notes = self.writer.list_notes()
        patterns = []

        # Analyze tag co-occurrence
        tag_counter = Counter()
        link_counter = Counter()
        category_counter = Counter()

        for note in all_notes:
            for tag in note.get("tags", []):
                tag_counter[tag] += 1
            for link in note.get("links", []):
                link_counter[link] += 1
            cat = note.get("category", "")
            if cat:
                category_counter[cat] += 1

        # Tags that appear multiple times = potential patterns
        for tag, count in tag_counter.most_common():
            if count >= min_occurrences:
                patterns.append({
                    "type": "recurring_tag",
                    "name": tag,
                    "occurrences": count,
                    "description": f"Tag '{tag}' appears {count} times across vault",
                })

        # Links that appear multiple times = strong patterns
        for link, count in link_counter.most_common():
            if count >= min_occurrences:
                patterns.append({
                    "type": "recurring_link",
                    "name": link,
                    "occurrences": count,
                    "description": f"Concept '{link}' is referenced {count} times — potential cognitive primitive",
                })

        # Categories with many notes = active areas
        for cat, count in category_counter.most_common():
            if count >= min_occurrences:
                patterns.append({
                    "type": "active_category",
                    "name": cat,
                    "occurrences": count,
                    "description": f"Category '{cat}' has {count} notes — active knowledge area",
                })

        return patterns

    def crystallize_pattern(
        self,
        name: str,
        conditions: list[str],
        result: str,
        links: list[str] | None = None,
    ) -> dict:
        """
        Save a recognized pattern as a crystallized cognitive primitive.

        Args:
            name: Pattern name
            conditions: List of conditions for this pattern
            result: What this pattern achieves
            links: Related concepts

        Returns: Written note metadata
        """
        content = {
            "cause": "Recurring operational pattern detected across executions",
            "fix": "Crystallized as reusable cognitive primitive",
            "result": result,
            "links": links or [],
        }

        # Add conditions as structured data
        conditions_text = "\n".join(f"- {c}" for c in conditions)
        content["cause"] += f"\n\nConditions:\n{conditions_text}"

        note_path = self.writer.write_note(
            category="doctrine",
            title=name,
            content=content,
            tags=["pattern", "cognitive_primitive"],
        )

        return {
            "name": name,
            "path": note_path["path"] if isinstance(note_path, dict) else str(note_path),
            "conditions": conditions,
            "result": result,
        }

    def get_cognitive_primitives(self) -> list[dict]:
        """Get all crystallized cognitive primitives from the vault."""
        notes = self.writer.list_notes(category="doctrine")
        primitives = []

        for note in notes:
            tags = note.get("tags", [])
            if "pattern" in tags or "cognitive_primitive" in tags:
                primitives.append({
                    "name": note.get("title", ""),
                    "category": note.get("category", ""),
                    "tags": tags,
                    "links": note.get("links", []),
                })

        return primitives

    def analyze_co_occurrence(self) -> dict:
        """
        Analyze which concepts co-occur frequently.

        Returns: Dict of concept pairs and their co-occurrence count
        """
        all_notes = self.writer.list_notes()
        co_occurrence = Counter()

        for note in all_notes:
            links = note.get("links", [])
            # Count all pairs of links in the same note
            for i in range(len(links)):
                for j in range(i + 1, len(links)):
                    pair = tuple(sorted([links[i], links[j]]))
                    co_occurrence[pair] += 1

        return {
            f"{a} ↔ {b}": count
            for (a, b), count in co_occurrence.most_common(20)
        }

```

LINKS:
[[Hermes Obsidian Test   Vault Working]]
[[Obsidian Vault Connection Info]]
[[Ontology Core Summary]]
[[Sage Audit Environment Utilization]]
[[Test Pattern]]
[[Citation Workflow]]
[[Description]]
[[Patterns]]
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
