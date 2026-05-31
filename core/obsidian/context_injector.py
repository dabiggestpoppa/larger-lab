"""
Context Injection at Spawn — Phase 01 Component 4
Loads relevant vault knowledge before agent execution.

Core principle: Agents should start with accumulated knowledge, not from scratch.
Before spawning, search vault for relevant patterns/errors/skills and inject into context.

Usage:
    from core.obsidian.context_injector import ContextInjector
    ci = ContextInjector(vault_path="/path/to/O2C-VAULT")
    context = ci.prepare_context(task="Fix the vault writer test failure")
    # Returns context string to inject into agent prompt
"""

import re
from pathlib import Path
from typing import Optional

from core.obsidian.vault_writer import VaultWriter, DEFAULT_VAULT_PATH
from core.skills.loader import SkillLoader


class ContextInjector:
    """Prepare context injection for agent spawn."""

    def __init__(self, vault_path: Optional[str | Path] = None):
        self.vault_path = Path(vault_path) if vault_path else DEFAULT_VAULT_PATH
        self.writer = VaultWriter(vault_path=self.vault_path)
        self.skill_loader = SkillLoader(skills_dir=self.vault_path.parent / "skills")

    def prepare_context(
        self,
        task: str,
        max_skills: int = 3,
        max_patterns: int = 5,
        max_errors: int = 5,
    ) -> str:
        """
        Prepare full context injection for an agent task.

        Args:
            task: The task description
            max_skills: Max number of relevant skills to include
            max_patterns: Max number of relevant patterns to include
            max_errors: Max number of relevant past errors to include

        Returns: Context string to inject into agent prompt
        """
        parts = []

        # 1. Load relevant skills
        skill_context = self.skill_loader.load_for_task(task)
        if skill_context:
            parts.append(skill_context)

        # 2. Find relevant patterns from vault
        patterns = self._find_relevant_notes("doctrine", task, max_patterns)
        if patterns:
            parts.append("# Relevant Patterns\n")
            for p in patterns:
                title = p.get("title", "")
                parts.append(f"## {title}")
                parts.append(f"See: {p.get('path', '')}")
                parts.append("")

        # 3. Find relevant past errors
        errors = self._find_relevant_notes("failures", task, max_errors)
        if errors:
            parts.append("# Relevant Past Errors\n")
            for e in errors:
                title = e.get("title", "")
                tags = e.get("tags", [])
                parts.append(f"- **{title}** (tags: {', '.join(tags)})")
                parts.append(f"  Path: {e.get('path', '')}")
                parts.append("")

        # 4. Find relevant execution history
        executions = self._find_relevant_notes("execution", task, 3)
        if executions:
            parts.append("# Recent Related Executions\n")
            for ex in executions:
                parts.append(f"- {ex.get('title', '')}: {ex.get('path', '')}")
            parts.append("")

        if not parts:
            return ""

        header = f"# Injected Context for Task\n\n> Task: {task}\n"
        return header + "\n".join(parts)

    def _find_relevant_notes(
        self,
        category: str,
        query: str,
        limit: int = 5,
    ) -> list[dict]:
        """Find notes in a category relevant to the query."""
        notes = self.writer.list_notes(category=category)
        if not notes:
            return []

        # Score notes by relevance to query
        query_words = set(query.lower().split())
        scored = []

        for note in notes:
            score = 0
            title = note.get("title", "").lower()
            tags = [t.lower() for t in note.get("tags", [])]
            links = [l.lower() for l in note.get("links", [])]

            for word in query_words:
                if word in title:
                    score += 3
                if word in tags:
                    score += 2
                if word in links:
                    score += 1

            if score > 0:
                scored.append((score, note))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        return [note for _, note in scored[:limit]]

    def get_vault_summary(self) -> str:
        """Get a summary of vault contents for context."""
        categories = self.writer.list_categories()
        lines = ["# Vault Summary", ""]

        for cat in categories[:10]:
            notes = self.writer.list_notes(category=cat)
            if notes:
                lines.append(f"## {cat} ({len(notes)} notes)")
                for note in notes[:3]:
                    lines.append(f"- {note.get('title', '')}")
                if len(notes) > 3:
                    lines.append(f"  ... and {len(notes) - 3} more")
                lines.append("")

        return "\n".join(lines)
