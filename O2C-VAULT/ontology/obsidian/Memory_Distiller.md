# Memory Distiller

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #obsidian

```python
"""
Memory Distillation Layer — Phase 01 Component 3
Compresses session execution data into distilled operational memory.

Core principle: Raw execution traces are noise. Distilled memory is intelligence.
This runs automatically after each agent session.

Usage:
    from core.obsidian.memory_distiller import MemoryDistiller
    md = MemoryDistiller(vault_path="/path/to/O2C-VAULT")
    md.distill_session(journal_entries=[...])
    md.distill_from_vault(days=7)  # Distill last 7 days of vault activity
"""

import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional

from core.obsidian.vault_writer import VaultWriter, DEFAULT_VAULT_PATH
from core.obsidian.compressor import compress_trace, extract_signal
from core.obsidian.pattern_crystallizer import PatternCrystallizer


class MemoryDistiller:
    """Compress session data into distilled operational memory."""

    def __init__(self, vault_path: Optional[str | Path] = None):
        self.vault_path = Path(vault_path) if vault_path else DEFAULT_VAULT_PATH
        self.writer = VaultWriter(vault_path=self.vault_path)
        self.crystallizer = PatternCrystallizer(vault_path=self.vault_path)

    def distill_session(
        self,
        agent_name: str,
        task: str,
        journal_entries: list[dict],
    ) -> dict:
        """
        Distill a full agent session into compressed memory.

        Args:
            agent_name: Name of the agent
            task: Task description
            journal_entries: List of journal step dicts

        Returns: Distillation result metadata
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

        # Categorize entries
        successes = [e for e in journal_entries if e.get("result") == "success"]
        failures = [e for e in journal_entries if e.get("result") == "failed"]
        corrections = [e for e in journal_entries if e.get("result") == "correction"]

        # Build distilled content
        lines = [
            f"# Session Distillation — {agent_name}",
            "",
            f"> Task: {task} | Date: {timestamp} | Steps: {len(journal_entries)}",
            "",
            "## What Worked",
            "",
        ]

        for entry in successes[:10]:
            detail = entry.get("details", entry.get("step", ""))
            lines.append(f"- ✅ {detail}")

        lines.extend(["", "## What Failed", ""])
        for entry in failures[:10]:
            detail = entry.get("details", entry.get("step", ""))
            lines.append(f"- ❌ {detail}")

        if corrections:
            lines.extend(["", "## Corrections Applied", ""])
            for entry in corrections[:10]:
                detail = entry.get("details", entry.get("step", ""))
                lines.append(f"- 🔧 {detail}")

        # Extract patterns
        lines.extend(["", "## Observed Patterns", ""])
        step_names = [e.get("step", "") for e in journal_entries]
        if len(step_names) >= 3:
            lines.append(f"- Execution flow: {' → '.join(step_names[:5])}")
        if failures and successes:
            success_rate = len(successes) / len(journal_entries)
            lines.append(f"- Success rate: {success_rate*100:.0f}%")

        lines.extend(["", "LINKS:
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
[[Usage]]
[[Description]]
[[Citation Workflow]]
[[Cal]]
[[Sage Audit Environment Utilization]]
[[Ontology Core Summary]]
[[Obsidian Vault Connection Info]]
[[Hermes Obsidian Test   Vault Working]]", f"[[{agent_name}]]", "[[Session Distillation]]"])
        if failures:
            lines.append("[[Failures]]")

        markdown = "\n".join(lines)

        # Write to vault
        title = f"Session {agent_name} {datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}"
        note_path = self.writer.write_note(
            category="memory",
            title=title,
            content={
                "cause": f"Agent {agent_name} executed: {task}",
                "fix": f"{len(corrections)} corrections applied" if corrections else "No corrections needed",
                "result": f"{len(successes)}/{len(journal_entries)} steps succeeded",
                "links": [agent_name, "Session Distillation"],
            },
            tags=["session", "distillation", agent_name.lower()],
        )

        # Write full markdown
        if isinstance(note_path, dict):
            full_path = self.vault_path / note_path["path"]
            full_path = full_path.with_name(full_path.stem + "_full.md")
        else:
            full_path = note_path.with_name(note_path.stem + "_full.md")
        full_path.write_text(markdown, encoding="utf-8")

        return {
            "agent": agent_name,
            "task": task,
            "total_steps": len(journal_entries),
            "successes": len(successes),
            "failures": len(failures),
            "corrections": len(corrections),
            "path": note_path["path"] if isinstance(note_path, dict) else str(note_path),
        }

    def distill_from_vault(self, days: int = 7) -> dict:
        """
        Distill patterns from recent vault activity.

        Scans execution and failure notes from the last N days
        and produces a summary distillation note.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        # Get recent execution notes
        exec_notes = self.writer.list_notes(category="execution")
        failure_notes = self.writer.list_notes(category="failures")

        # Build summary
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        lines = [
            f"# Vault Distillation — Last {days} Days",
            "",
            f"> Generated: {timestamp}",
            "",
            f"## Activity Summary",
            "",
            f"- Execution reports: {len(exec_notes)}",
            f"- Failure reports: {len(failure_notes)}",
            "",
        ]

        # Extract common failure categories
        failure_categories = set()
        for note in failure_notes:
            for tag in note.get("tags", []):
                failure_categories.add(tag)

        if failure_categories:
            lines.append("## Active Failure Categories")
            lines.append("")
            for cat in sorted(failure_categories):
                lines.append(f"- {cat}")
            lines.append("")

        # Extract patterns
        patterns = self.crystallizer.extract_patterns(min_occurrences=1)
        if patterns:
            lines.append("## Detected Patterns")
            lines.append("")
            for p in patterns[:10]:
                lines.append(f"- **{p['name']}**: {p['description']}")
            lines.append("")

        lines.extend(["LINKS:
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
[[Usage]]
[[Description]]
[[Citation Workflow]]
[[Cal]]
[[Sage Audit Environment Utilization]]
[[Ontology Core Summary]]
[[Obsidian Vault Connection Info]]
[[Hermes Obsidian Test   Vault Working]]", "[[Vault Distillation]]", "[[Patterns]]"])
        markdown = "\n".join(lines)

        title = f"Vault Distillation {datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}"
        note_path = self.writer.write_note(
            category="memory",
            title=title,
            content={
                "cause": f"Automated distillation of last {days} days of vault activity",
                "fix": "Compressed into operational memory",
                "result": f"{len(exec_notes)} executions, {len(failure_notes)} failures analyzed",
                "links": ["Vault Distillation"],
            },
            tags=["distillation", "automated", "summary"],
        )

        return {
            "days": days,
            "executions_analyzed": len(exec_notes),
            "failures_analyzed": len(failure_notes),
            "patterns_detected": len(patterns),
            "path": note_path["path"] if isinstance(note_path, dict) else str(note_path),
        }

```