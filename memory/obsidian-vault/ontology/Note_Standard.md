# Note Standard

> Category: ontology | Imported: 2026-06-02 01:13 UTC

Tags: #ontology #python #obsidian

```python
"""
Note Standard — Phase 0I
Validate that all notes follow the CAUSE/FIX/RESULT/LINKS format.

Core principle: Consistent format = machine-parseable = graph-ready.
No essays. No rambling. No AI sludge. Operational signal only.

Usage:
    from core.obsidian.note_standard import NoteValidator
    validator = NoteValidator()
    result = validator.validate(note_content)
    # result = {"valid": True/False, "issues": [...], "score": 0.0-1.0}
"""

import re
from pathlib import Path
from typing import Optional


# Required sections for a "full" note
REQUIRED_SECTIONS = ["CAUSE", "FIX", "RESULT"]

# Optional but recommended
OPTIONAL_SECTIONS = ["LINKS"]

# Maximum note length (chars) — notes should be concise
MAX_NOTE_LENGTH = 5000

# Minimum note length — notes should have substance
MIN_NOTE_LENGTH = 50


class NoteValidator:
    """Validate notes against the CAUSE/FIX/RESULT/LINKS standard."""

    def __init__(self, strict: bool = False):
        """
        Args:
            strict: If True, all REQUIRED_SECTIONS must be present.
                    If False, only CAUSE is required.
        """
        self.strict = strict

    def validate(self, content: str) -> dict:
        """
        Validate a note's format.

        Returns:
            {
                "valid": bool,
                "issues": list[str],
                "score": float (0.0-1.0),
                "has_cause": bool,
                "has_fix": bool,
                "has_result": bool,
                "has_links": bool,
                "has_title": bool,
            }
        """
        issues = []
        score = 0.0
        max_score = 0.0

        # Check title
        has_title = bool(re.search(r"^#\s+.+$", content, re.MULTILINE))
        max_score += 1.0
        if has_title:
            score += 1.0
        else:
            issues.append("Missing # Title header")

        # Check length
        if len(content) > MAX_NOTE_LENGTH:
            issues.append(f"Note too long ({len(content)} chars, max {MAX_NOTE_LENGTH})")
            score -= 0.5
        elif len(content) < MIN_NOTE_LENGTH:
            issues.append(f"Note too short ({len(content)} chars, min {MIN_NOTE_LENGTH})")
            score -= 0.5

        # Check required sections
        has_cause = "CAUSE:" in content
        has_fix = "FIX:" in content
        has_result = "RESULT:" in content
        has_links = "LINKS:
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
[[Standard]]
[[Patterns]]
[[Citation Workflow]]
[[Test Note]]
[[Sage Audit Environment Utilization]]
[[Pm2 Test Note]]
[[Ontology Core Summary]]
[[Obsidian Vault Connection Info]]
[[Hermes Obsidian Test   Vault Working]]
[[Hermes Agent Test Note]]
[[Hermes Agent Activation Note]]
[[Api Test Note]]" in content

        # CAUSE is always required
        max_score += 1.0
        if has_cause:
            score += 1.0
            # Check CAUSE has content after it
            cause_content = self._get_section_content(content, "CAUSE")
            if not cause_content.strip():
                issues.append("CAUSE section is empty")
                score -= 0.3
        else:
            issues.append("Missing CAUSE section")

        # FIX and RESULT required in strict mode
        for section in ["FIX", "RESULT"]:
            max_score += 1.0
            has_section = section + ":" in content
            if has_section:
                score += 1.0
                section_content = self._get_section_content(content, section)
                if not section_content.strip():
                    issues.append(f"{section} section is empty")
                    score -= 0.3
            elif self.strict:
                issues.append(f"Missing {section} section (strict mode)")

        # LINKS is optional but recommended
        max_score += 0.5
        if has_links:
            score += 0.5
            links = re.findall(r"\[\[(.+?)\]\]", content)
            if not links:
                issues.append("LINKS section present but no [[WikiLinks]] found")
                score -= 0.2

        # Check for AI sludge (common patterns)
        sludge_patterns = [
            (r"I apologize for", "Contains AI apology"),
            (r"Great question!", "Contains filler phrase"),
            (r"As an AI", "Contains AI self-reference"),
            (r"In conclusion", "Contains essay-style conclusion"),
            (r"Let me explain", "Contains rambling intro"),
        ]
        for pattern, message in sludge_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                issues.append(f"AI sludge detected: {message}")
                score -= 0.3

        # Normalize score
        final_score = max(0.0, min(1.0, score / max_score)) if max_score > 0 else 0.0

        # Valid if score >= 0.6 and has title and cause
        is_valid = final_score >= 0.6 and has_title and has_cause

        return {
            "valid": is_valid,
            "issues": issues,
            "score": round(final_score, 2),
            "has_cause": has_cause,
            "has_fix": has_fix,
            "has_result": has_result,
            "has_links": has_links,
            "has_title": has_title,
        }

    @staticmethod
    def _get_section_content(content: str, section: str) -> str:
        """Extract content after a section header until the next section or end."""
        pattern = rf"{section}:\s*\n(.*?)(?=\n[A-Z]+:|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def validate_file(self, file_path: str | Path) -> dict:
        """Validate a note file on disk."""
        path = Path(file_path)
        if not path.exists():
            return {"valid": False, "issues": [f"File not found: {path}"], "score": 0.0}

        content = path.read_text(encoding="utf-8")
        result = self.validate(content)
        result["file"] = str(path)
        return result

    def validate_vault(self, vault_path: str | Path) -> dict:
        """Validate all notes in a vault. Returns summary."""
        vault_path = Path(vault_path)
        results = []
        valid_count = 0
        invalid_count = 0

        for note_path in vault_path.rglob("*.md"):
            result = self.validate_file(note_path)
            results.append(result)
            if result["valid"]:
                valid_count += 1
            else:
                invalid_count += 1

        total = valid_count + invalid_count
        return {
            "total_notes": total,
            "valid": valid_count,
            "invalid": invalid_count,
            "compliance_rate": round(valid_count / max(total, 1), 2),
            "results": results,
        }


def format_note(title: str, cause: str, fix: str, result: str, links: list[str] | None = None) -> str:
    """
    Create a properly formatted note from components.

    This is the "constructor" for valid notes — use this to ensure
    all notes follow the standard.
    """
    lines = [
        f"# {title}",
        "",
        "CAUSE:",
        cause,
        "",
        "FIX:",
        fix,
        "",
        "RESULT:",
        result,
        "",
    ]

    if links:
        lines.append("LINKS:
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
[[Standard]]
[[Patterns]]
[[Citation Workflow]]
[[Test Note]]
[[Sage Audit Environment Utilization]]
[[Pm2 Test Note]]
[[Ontology Core Summary]]
[[Obsidian Vault Connection Info]]
[[Hermes Obsidian Test   Vault Working]]
[[Hermes Agent Test Note]]
[[Hermes Agent Activation Note]]
[[Api Test Note]]")
        for link in links:
            lines.append(f"[[{link}]]")
        lines.append("")

    return "\n".join(lines)

```