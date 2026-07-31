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
