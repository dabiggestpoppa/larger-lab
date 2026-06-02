# Linker

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #obsidian

```python
"""
Linker — Phase 0C
Auto-link doctrine. Build knowledge graph from vault notes.

Core principle: Notes are not intelligence. The GRAPH between notes is intelligence.
Every note should link to related notes. Obsidian [[WikiLinks]] create the cognitive topology.

Usage:
    from core.obsidian.linker import Linker
    linker = Linker(vault_path="/path/to/O2C-VAULT")
    linker.auto_link()  # Scan all notes and add missing links
    related = linker.get_related("State Reset Bug")
"""

import re
from pathlib import Path
from typing import Optional
from collections import defaultdict

from core.obsidian.vault_writer import VaultWriter, DEFAULT_VAULT_PATH


class Linker:
    """Auto-link vault notes to build knowledge graph."""

    def __init__(self, vault_path: Optional[str | Path] = None):
        self.vault_path = Path(vault_path) if vault_path else DEFAULT_VAULT_PATH
        self.writer = VaultWriter(vault_path=self.vault_path)
        self._graph: dict[str, set[str]] = defaultdict(set)

    def _extract_title(self, content: str) -> str:
        """Extract the title from a markdown note."""
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        return match.group(1).strip() if match else ""

    def _extract_existing_links(self, content: str) -> list[str]:
        """Extract all [[WikiLinks]] from content."""
        return re.findall(r"\[\[(.+?)\]\]", content)

    def _extract_tags(self, content: str) -> list[str]:
        """Extract #tags from content."""
        return re.findall(r"#(\w+)", content)

    def _find_related(self, title: str, content: str, all_notes: dict[str, str]) -> list[str]:
        """
        Find related notes based on:
        1. Shared tags
        2. Keyword overlap in titles
        3. Category proximity
        """
        related = []
        my_tags = set(self._extract_tags(content))
        my_words = set(title.lower().split())

        for other_title, other_content in all_notes.items():
            if other_title == title:
                continue

            # Check tag overlap
            other_tags = set(self._extract_tags(other_content))
            if my_tags & other_tags:  # Shared tags
                related.append(other_title)
                continue

            # Check word overlap in titles
            other_words = set(other_title.lower().split())
            shared = my_words & other_words
            if len(shared) >= 1 and len(my_words) > 1:
                related.append(other_title)
                continue

            # Check if content mentions the other title
            if other_title.lower() in content.lower():
                related.append(other_title)

        return related

    def scan_vault(self) -> dict[str, str]:
        """Scan all notes in the vault. Returns {title: content} dict."""
        notes = {}
        for note_path in self.vault_path.rglob("*.md"):
            content = note_path.read_text(encoding="utf-8")
            title = self._extract_title(content)
            if title:
                rel_path = str(note_path.relative_to(self.vault_path))
                notes[title] = content
                notes[rel_path] = content  # Also index by path
        return notes

    def auto_link(self, dry_run: bool = False) -> dict[str, list[str]]:
        """
        Scan all notes and add missing [[WikiLinks]] to related notes.

        Args:
            dry_run: If True, only report what links would be added (don't write)

        Returns:
            Dict of {note_title: [new_links_added]}
        """
        all_notes = self.scan_vault()
        # Filter to only title-indexed notes
        title_notes = {k: v for k, v in all_notes.items() if not k.endswith(".md")}

        additions: dict[str, list[str]] = {}

        for title, content in title_notes.items():
            existing_links = set(self._extract_existing_links(content))
            related = self._find_related(title, content, title_notes)

            new_links = [r for r in related if r not in existing_links]

            if new_links:
                additions[title] = new_links

                if not dry_run:
                    # Find the actual file and update it
                    for note_path in self.vault_path.rglob("*.md"):
                        note_content = note_path.read_text(encoding="utf-8")
                        note_title = self._extract_title(note_content)
                        if note_title == title:
                            # Append new links
                            link_lines = [f"[[{link}]]" for link in new_links]
                            # Add LINKS section if not present
                            if "LINKS:
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
[[Structural Anchor]]
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
[[Usage]]
[[Citation Workflow]]
[[Sage Audit Environment Utilization]]
[[Ontology Core Summary]]
[[Obsidian Vault Connection Info]]
[[Hermes Obsidian Test   Vault Working]]" not in note_content:
                                note_content = note_content.rstrip() + "\n\nLINKS:
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
[[Structural Anchor]]
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
[[Usage]]
[[Citation Workflow]]
[[Sage Audit Environment Utilization]]
[[Ontology Core Summary]]
[[Obsidian Vault Connection Info]]
[[Hermes Obsidian Test   Vault Working]]\n"
                                for link in new_links:
                                    note_content += f"[[{link}]]\n"
                            else:
                                # Append to existing LINKS section
                                for link in new_links:
                                    if f"[[{link}]]" not in note_content:
                                        note_content = note_content.replace(
                                            "LINKS:
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
[[Structural Anchor]]
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
[[Usage]]
[[Citation Workflow]]
[[Sage Audit Environment Utilization]]
[[Ontology Core Summary]]
[[Obsidian Vault Connection Info]]
[[Hermes Obsidian Test   Vault Working]]", f"LINKS:
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
[[Structural Anchor]]
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
[[Usage]]
[[Citation Workflow]]
[[Sage Audit Environment Utilization]]
[[Ontology Core Summary]]
[[Obsidian Vault Connection Info]]
[[Hermes Obsidian Test   Vault Working]]\n[[{link}]]"
                                        )
                            note_path.write_text(note_content, encoding="utf-8")
                            break

        return additions

    def get_related(self, title: str) -> list[str]:
        """Get all notes related to the given title."""
        all_notes = self.scan_vault()
        title_notes = {k: v for k, v in all_notes.items() if not k.endswith(".md")}

        content = title_notes.get(title, "")
        if not content:
            return []

        return self._find_related(title, content, title_notes)

    def build_graph(self) -> dict[str, set[str]]:
        """
        Build the full knowledge graph from all notes.

        Returns:
            Dict of {note_title: {linked_note_titles}}
        """
        all_notes = self.scan_vault()
        title_notes = {k: v for k, v in all_notes.items() if not k.endswith(".md")}

        graph: dict[str, set[str]] = defaultdict(set)

        for title, content in title_notes.items():
            links = self._extract_existing_links(content)
            for link in links:
                graph[title].add(link)
                graph[link].add(title)  # Bidirectional

        self._graph = graph
        return dict(graph)

    def get_graph_mermaid(self) -> str:
        """Generate a Mermaid graph representation of the knowledge graph."""
        if not self._graph:
            self.build_graph()

        lines = ["graph LR"]
        seen_edges = set()

        for source, targets in self._graph.items():
            for target in targets:
                edge = tuple(sorted([source, target]))
                if edge not in seen_edges:
                    seen_edges.add(edge)
                    lines.append(f"    {edge[0].replace(' ', '_')} --> {edge[1].replace(' ', '_')}")

        return "\n".join(lines)

    def get_stats(self) -> dict:
        """Get vault statistics."""
        all_notes = self.scan_vault()
        title_notes = {k: v for k, v in all_notes.items() if not k.endswith(".md")}
        graph = self.build_graph()

        total_links = sum(len(v) for v in graph.values()) // 2  # Bidirectional
        isolated = [t for t in title_notes if t not in graph or not graph[t]]

        return {
            "total_notes": len(title_notes),
            "total_links": total_links,
            "isolated_notes": isolated,
            "avg_links_per_note": round(total_links / max(len(title_notes), 1), 2),
        }

```