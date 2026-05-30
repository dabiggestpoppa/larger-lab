"""
Vault Writer — Phase 0A
Write structured markdown into the O2C Obsidian vault.

Core principle: Every agent execution leaves behind operational intelligence
in markdown format. The filesystem becomes smarter, not the model.

Usage:
    from core.obsidian.vault_writer import VaultWriter
    writer = VaultWriter(vault_path="/path/to/O2C-VAULT")
    writer.write_note(category="failures", title="State Reset Bug", content={
        "cause": "entry_price cleared before archival",
        "fix": "snapshot before reset",
        "result": "trade continuity restored",
        "links": ["Trading Systems", "State Machines"]
    })
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


# Default vault path — can be overridden
DEFAULT_VAULT_PATH = Path(__file__).resolve().parent.parent.parent / "O2C-VAULT"

# Required vault directories (Phase 0H taxonomy)
VAULT_DIRECTORIES = [
    "agents/quant",
    "agents/research",
    "agents/coding",
    "agents/observer",
    "memory/successful_patterns",
    "memory/error_corrections",
    "memory/spawn_history",
    "memory/consensus_failures",
    "ontology/cerebus",
    "ontology/observer_core",
    "ontology/state_machines",
    "ontology/routing_logic",
    "graphs/agent_relationships",
    "graphs/execution_flow",
    "graphs/knowledge_clusters",
    "journals/daily_runtime",
    "journals/backtest_logs",
    "journals/forward_test_logs",
    "doctrine",
    "failures",
    "execution",
    "skills",
    "heuristics",
    "routing",
    "architecture",
]

# Valid categories for write_note
VALID_CATEGORIES = [d.split("/")[0] for d in VAULT_DIRECTORIES]
VALID_CATEGORIES = list(set(VALID_CATEGORIES))


class VaultWriter:
    """Write structured markdown notes into the O2C Obsidian vault."""

    def __init__(self, vault_path: Optional[str | Path] = None):
        self.vault_path = Path(vault_path) if vault_path else DEFAULT_VAULT_PATH
        self._ensure_vault_structure()

    def _ensure_vault_structure(self):
        """Create vault directory structure if it doesn't exist."""
        for dir_path in VAULT_DIRECTORIES:
            full_path = self.vault_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sanitize_filename(title: str) -> str:
        """Convert title to safe filename."""
        # Replace spaces with underscores, remove special chars
        safe = re.sub(r'[^\w\s\-]', '', title)
        safe = re.sub(r'\s+', '_', safe.strip())
        return safe[:100]  # Cap length

    @staticmethod
    def _format_note(title: str, content: dict, category: str, tags: list[str] | None = None) -> str:
        """
        Format a note following the CAUSE/FIX/RESULT/LINKS standard.

        content dict keys: cause, fix, result, links (all optional)
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        lines = [
            f"# {title}",
            "",
            f"> Category: {category} | Created: {timestamp}",
            "",
        ]

        # Tags
        if tags:
            tag_str = " ".join(f"#{t}" for t in tags)
            lines.append(f"Tags: {tag_str}")
            lines.append("")

        # CAUSE
        if content.get("cause"):
            lines.append("CAUSE:")
            lines.append(str(content["cause"]))
            lines.append("")

        # FIX
        if content.get("fix"):
            lines.append("FIX:")
            lines.append(str(content["fix"]))
            lines.append("")

        # RESULT
        if content.get("result"):
            lines.append("RESULT:")
            lines.append(str(content["result"]))
            lines.append("")

        # LINKS (Obsidian wiki-links)
        if content.get("links"):
            lines.append("LINKS:")
            for link in content["links"]:
                lines.append(f"[[{link}]]")
            lines.append("")

        return "\n".join(lines)

    def write_note(
        self,
        category: str,
        title: str,
        content: dict,
        tags: list[str] | None = None,
        subcategory: str | None = None,
    ) -> Path:
        """
        Write a markdown note to the vault.

        Args:
            category: Top-level category (e.g., "failures", "doctrine", "skills")
            title: Note title
            content: Dict with keys: cause, fix, result, links
            tags: Optional list of tags (without #)
            subcategory: Optional subcategory (e.g., "quant" under "agents")

        Returns:
            Path to the written file
        """
        # Validate category
        if category not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{category}'. Valid: {VALID_CATEGORIES}"
            )

        # Build path
        if subcategory:
            dir_path = self.vault_path / category / subcategory
        else:
            dir_path = self.vault_path / category
        dir_path.mkdir(parents=True, exist_ok=True)

        # Write file
        filename = self._sanitize_filename(title) + ".md"
        file_path = dir_path / filename

        markdown = self._format_note(title, content, category, tags)
        file_path.write_text(markdown, encoding="utf-8")

        return file_path

    def get_note(self, category: str, title: str, subcategory: str | None = None) -> str | None:
        """Read a note from the vault."""
        filename = self._sanitize_filename(title) + ".md"
        if subcategory:
            file_path = self.vault_path / category / subcategory / filename
        else:
            file_path = self.vault_path / category / filename

        if file_path.exists():
            return file_path.read_text(encoding="utf-8")
        return None

    def list_notes(self, category: str | None = None, subcategory: str | None = None) -> list[str]:
        """List all notes in a category, or all notes in the vault."""
        if category:
            if subcategory:
                dir_path = self.vault_path / category / subcategory
            else:
                dir_path = self.vault_path / category
        else:
            dir_path = self.vault_path

        notes = []
        for path in dir_path.rglob("*.md"):
            notes.append(str(path.relative_to(self.vault_path)))
        return sorted(notes)

    def note_exists(self, category: str, title: str, subcategory: str | None = None) -> bool:
        """Check if a note exists."""
        filename = self._sanitize_filename(title) + ".md"
        if subcategory:
            file_path = self.vault_path / category / subcategory / filename
        else:
            file_path = self.vault_path / category / filename
        return file_path.exists()

    def update_note(
        self,
        category: str,
        title: str,
        content: dict,
        tags: list[str] | None = None,
        subcategory: str | None = None,
    ) -> Path:
        """Overwrite an existing note (or create if not exists)."""
        return self.write_note(category, title, content, tags, subcategory)

    def delete_note(self, category: str, title: str, subcategory: str | None = None) -> bool:
        """Delete a note. Returns True if deleted, False if not found."""
        filename = self._sanitize_filename(title) + ".md"
        if subcategory:
            file_path = self.vault_path / category / subcategory / filename
        else:
            file_path = self.vault_path / category / filename

        if file_path.exists():
            file_path.unlink()
            return True
        return False


# Module-level convenience functions
_default_writer: VaultWriter | None = None


def get_writer(vault_path: Optional[str | Path] = None) -> VaultWriter:
    """Get or create the default VaultWriter singleton."""
    global _default_writer
    if _default_writer is None:
        _default_writer = VaultWriter(vault_path)
    return _default_writer


def write_note(category: str, title: str, content: dict, tags: list[str] | None = None) -> Path:
    """Convenience: write a note using the default writer."""
    return get_writer().write_note(category, title, content, tags)


def get_note(category: str, title: str) -> str | None:
    """Convenience: read a note using the default writer."""
    return get_writer().get_note(category, title)


def list_notes(category: str | None = None) -> list[str]:
    """Convenience: list notes using the default writer."""
    return get_writer().list_notes(category)
