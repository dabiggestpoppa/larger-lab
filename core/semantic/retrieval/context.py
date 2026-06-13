"""
Phase 1.4.3 — Context Assembler

Merges retrieval results into reasoning-ready context windows.
Handles deduplication, token budget management, and source attribution.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SourceAttribution:
    """Tracks the origin of a piece of context."""
    source_id: str
    source_type: str  # "rtrvr", "shiji", "graph", "procedural"
    chunk_id: str
    text_snippet: str  # first 100 chars for reference
    confidence: float
    metadata: dict = field(default_factory=dict)


@dataclass
class AssembledContext:
    """
    A reasoning-ready context window assembled from multiple retrieval results.

    Attributes:
        context_text: The merged, deduplicated context string.
        sources: List of SourceAttribution objects for traceability.
        total_tokens: Approximate token count of context_text.
        truncated: Whether the context was cut to fit the token budget.
        sections: Named sections within the context (e.g., "primary", "supporting").
    """
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    context_text: str = ""
    sources: list[SourceAttribution] = field(default_factory=list)
    total_tokens: int = 0
    truncated: bool = False
    sections: dict[str, str] = field(default_factory=dict)

    def add_section(self, name: str, text: str) -> None:
        """Add a named section to the context."""
        self.sections[name] = text
        self._rebuild_text()

    def _rebuild_text) -> None:
        """Rebuild context_text from sections."""
        parts = []
        for name, text in self.sections.items():
            if text.strip():
                parts.append(f"[{name}]\n{text}")
        self.context_text = "\n\n".join(parts)
        self.total_tokens = len(self.context_text) // 4

    def format_with_attribution(self) -> str:
        """Format context with inline source attribution."""
        lines = [self.context_text, "", "--- Sources ---"]
        for src in self.sources:
            snippet = src.text_snippet[:80].replace("\n", " ")
            lines.append(f"  [{src.source_type}] {src.source_id} ({src.confidence:.2f}): {snippet}...")
        return "\n".join(lines)


class ContextAssembler:
    """
    Merges retrieval results into reasoning-ready context windows.

    Responsibilities:
    - Deduplicate overlapping content
    - Manage token budget (fit within LLM context limits)
    - Track source attribution
    - Organize results into named sections
    """

    def __init__(
        self,
        default_budget: int = 4096,
        overlap_threshold: float = 0.8,
    ):
        self.default_budget = default_budget
        self.overlap_threshold = overlap_threshold

    def assemble(
        self,
        results: list[Any],
        token_budget: int | None = None,
        section_mode: str = "grouped",
    ) -> AssembledContext:
        """
        Assemble retrieval results into a context window.

        Args:
            results: List of RetrievalResult or RecallResult objects.
            token_budget: Max tokens (default: self.default_budget).
            section_mode: "flat" | "grouped" | "prioritized"
                - flat: all results in one block
                - grouped: grouped by source type
                - prioritized: primary results first, then supporting

        Returns:
            AssembledContext with merged, deduplicated, budget-aware text.
        """
        token_budget = token_budget or self.default_budget

        if not results:
            return AssembledContext(context_text="", total_tokens=0)

        # Step 1: Deduplicate
        deduped = self._deduplicate(results)

        # Step 2: Sort by relevance/confidence
        sorted_results = self._sort_by_relevance(deduped)

        # Step 3: Build sections based on mode
        if section_mode == "flat":
            sections = self._build_flat_sections(sorted_results)
        elif section_mode == "grouped":
            sections = self._build_grouped_sections(sorted_results)
        elif section_mode == "prioritized":
            sections = self._build_prioritized_sections(sorted_results)
        else:
            sections = self._build_flat_sections(sorted_results)

        # Step 4: Apply token budget
        truncated = False
        total_tokens = sum(len(t) // 4 for t in sections.values())
        if total_tokens > token_budget:
            sections, truncated = self._apply_budget(sections, token_budget)
            total_tokens = sum(len(t) // 4 for t in sections.values())

        # Step 5: Build attributions
        sources = self._build_attributions(sorted_results, sections)

        # Assemble final context
        context = AssembledContext(
            sources=sources,
            total_tokens=total_tokens,
            truncated=truncated,
            sections=sections,
        )
        context._rebuild_text()
        return context

    def _deduplicate(self, results: list[Any]) -> list[Any]:
        """
        Remove duplicate/overlapping results.

        Uses text similarity to detect near-duplicates.
        Keeps the higher-scored version.
        """
        if len(results) <= 1:
            return list(results)

        unique: list[Any] = []
        seen_texts: list[str] = []

        for result in results:
            text = self._get_text(result)
            is_dup = False
            for seen in seen_texts:
                similarity = self._text_overlap(text, seen)
                if similarity >= self.overlap_threshold:
                    is_dup = True
                    break

            if not is_dup:
                unique.append(result)
                seen_texts.append(text)

        return unique

    def _sort_by_relevance(self, results: list[Any]) -> list[Any]:
        """Sort results by score/confidence descending."""
        def _key(r: Any) -> float:
            if hasattr(r, "score"):
                return float(r.score)
            if hasattr(r, "confidence"):
                return float(r.confidence)
            return 0.0

        return sorted(results, key=_key, reverse=True)

    def _build_flat_sections(self, results: list[Any]) -> dict[str, str]:
        """All results in a single 'context' section."""
        parts: list[str] = []
        for r in results:
            text = self._get_text(r)
            if text.strip():
                parts.append(text)
        return {"context": "\n\n".join(parts)}

    def _build_grouped_sections(self, results: list[Any]) -> dict[str, str]:
        """Group results by source type into named sections."""
        groups: dict[str, list[str]] = {}
        for r in results:
            source_type = self._get_source_type(r)
            text = self._get_text(r)
            if text.strip():
                groups.setdefault(source_type, []).append(text)

        sections: dict[str, str] = {}
        for group_name, texts in groups.items():
            sections[group_name] = "\n\n".join(texts)
        return sections

    def _build_prioritized_sections(self, results: list[Any]) -> dict[str, str]:
        """Split into primary (top 30%) and supporting (rest) sections."""
        if not results:
            return {}

        split_idx = max(1, len(results) // 3)
        primary = results[:split_idx]
        supporting = results[split_idx:]

        sections: dict[str, str] = {}
        if primary:
            sections["primary"] = "\n\n".join(self._get_text(r) for r in primary if self._get_text(r).strip())
        if supporting:
            sections["supporting"] = "\n\n".join(self._get_text(r) for r in supporting if self._get_text(r).strip())
        return sections

    def _apply_budget(
        self,
        sections: dict[str, str],
        budget: int,
    ) -> tuple[dict[str, str], bool]:
        """Trim sections to fit within token budget. Primary sections are preserved first."""
        # Priority order: primary, then other sections alphabetically
        priority_keys = []
        if "primary" in sections:
            priority_keys.append("primary")
        priority_keys.extend(k for k in sorted(sections.keys()) if k != "primary")

        result: dict[str, str] = {}
        remaining = budget

        for key in priority_keys:
            text = sections[key]
            tokens = len(text) // 4
            if tokens <= remaining:
                result[key] = text
                remaining -= tokens
            else:
                # Truncate this section
                if remaining > 0:
                    # Approximate chars we can keep
                    keep_chars = remaining * 4
                    result[key] = text[:keep_chars]
                remaining = 0

        return result, True

    def _build_attributions(
        self,
        results: list[Any],
        sections: dict[str, str],
    ) -> list[SourceAttribution]:
        """Build source attribution for all results that appear in the final context."""
        attributions: list[SourceAttribution] = []
        all_section_text = "\n\n".join(sections.values())

        for r in results:
            text = self._get_text(r)
            # Only attribute if the text actually made it into the context
            if text[:50] in all_section_text:
                score = float(getattr(r, "score", None) or getattr(r, "confidence", 0.0))
                attributions.append(SourceAttribution(
                    source_id=getattr(r, "source", "unknown"),
                    source_type=self._get_source_type(r),
                    chunk_id=getattr(r, "chunk_id", ""),
                    text_snippet=text[:100],
                    confidence=score,
                    metadata=getattr(r, "metadata", {}),
                ))

        return attributions

    @staticmethod
    def _get_text(result: Any) -> str:
        """Extract text from a result object."""
        if hasattr(result, "text"):
            return str(result.text)
        if hasattr(result, "context_window"):
            return str(result.context_window)
        if isinstance(result, dict):
            return str(result.get("text") or result.get("content") or "")
        return str(result)

    @staticmethod
    def _get_source_type(result: Any) -> str:
        """Determine the source type of a result."""
        if hasattr(result, "result_id"):
            return "rtrvr"
        if hasattr(result, "hop_distance"):
            return "shiji"
        if isinstance(result, dict):
            return result.get("_source_type", "unknown")
        return "unknown"

    @staticmethod
    def _text_overlap(a: str, b: str) -> float:
        """
        Compute overlap ratio between two texts using character-level Jaccard.
        Returns 0.0 (no overlap) to 1.0 (identical).
        """
        if not a or not b:
            return 0.0

        # Use character trigrams for robust overlap detection
        def _trigrams(text: str) -> set[str]:
            text = text.lower().strip()
            if len(text) < 3:
                return {text}
            return {text[i:i + 3] for i in range(len(text) - 2)}

        tri_a = _trigrams(a)
        tri_b = _trigrams(b)
        if not tri_a or not tri_b:
            return 0.0

        intersection = tri_a & tri_b
        union = tri_a | tri_b
        return len(intersection) / len(union)
