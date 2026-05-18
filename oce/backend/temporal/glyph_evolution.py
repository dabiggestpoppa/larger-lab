"""
V3 Phase 5 — Glyph Evolution Engine
Glyphs evolve across time, developing compressed historical symbolic language.

Recurring trajectories get compressed into glyphs.
Recurring failure states get compressed into warning glyphs.
Strategic archetypes get compressed into operational glyphs.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional

from topology.glyph_engine import GlyphEngine, GLYPH_MAP


@dataclass
class EvolvedGlyph:
    """A glyph that has evolved from usage patterns."""
    glyph: str
    original_meaning: str
    evolved_meaning: str
    usage_count: int = 0
    compression_history: list[float] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)

    @property
    def avg_compression(self) -> float:
        if not self.compression_history:
            return 0.0
        return sum(self.compression_history) / len(self.compression_history)

    def use(self, compression_ratio: float) -> None:
        self.usage_count += 1
        self.last_used = time.time()
        self.compression_history.append(compression_ratio)


class GlyphEvolutionEngine:
    """
    Manages the evolution of glyphs across time.
    
    Glyphs emerge and evolve when:
    1. A pattern recurs frequently enough to warrant compression
    2. The compression gain exceeds reconstruction cost
    3. The glyph proves useful across multiple contexts
    
    Glyph evolution is utility-constrained — no uncontrolled mutation.
    """

    def __init__(self, base_engine: GlyphEngine = None):
        self.base_engine = base_engine or GlyphEngine()
        self.evolved_glyphs: dict[str, EvolvedGlyph] = {}
        self._pattern_counts: dict[str, int] = {}

    def record_pattern(self, pattern: str, compression_ratio: float = 0.0) -> None:
        """Record a recurring pattern for potential glyph evolution."""
        self._pattern_counts[pattern] = self._pattern_counts.get(pattern, 0) + 1

        # Check if pattern should evolve into a glyph
        if self._pattern_counts[pattern] >= 5:
            self._evolve_pattern(pattern, compression_ratio)

    def _evolve_pattern(self, pattern: str, compression_ratio: float) -> Optional[EvolvedGlyph]:
        """Evolve a recurring pattern into a glyph."""
        # Check if pattern already has a glyph
        if pattern in self.base_engine.glyph_map.values():
            glyph = self.base_engine.reverse_map.get(pattern)
            if glyph and glyph not in self.evolved_glyphs:
                evolved = EvolvedGlyph(
                    glyph=glyph,
                    original_meaning=pattern,
                    evolved_meaning=pattern,
                    usage_count=self._pattern_counts[pattern],
                )
                evolved.use(compression_ratio)
                self.evolved_glyphs[glyph] = evolved
                return evolved

        # Check for compound patterns (multi-word)
        words = pattern.split("_")
        if len(words) >= 2:
            # Try to compose from existing glyphs
            composed = self._compose_glyph(pattern)
            if composed:
                return composed

        return None

    def _compose_glyph(self, pattern: str) -> Optional[EvolvedGlyph]:
        """Try to compose a glyph from existing glyphs."""
        words = pattern.split("_")
        glyphs = []
        for word in words:
            if word in self.base_engine.reverse_map:
                glyphs.append(self.base_engine.reverse_map[word])

        if len(glyphs) >= 2:
            # Create compound glyph (use first + last)
            compound = glyphs[0] + glyphs[-1]
            if compound not in self.evolved_glyphs:
                evolved = EvolvedGlyph(
                    glyph=compound,
                    original_meaning=pattern,
                    evolved_meaning=f"compound:{pattern}",
                    usage_count=self._pattern_counts.get(pattern, 0),
                )
                self.evolved_glyphs[compound] = evolved
                return evolved
        return None

    def get_semantic_clusters(self) -> dict[str, list[str]]:
        """Group evolved glyphs by semantic similarity."""
        clusters = {}
        for glyph, evolved in self.evolved_glyphs.items():
            category = evolved.evolved_meaning.split("_")[0] if "_" in evolved.evolved_meaning else "general"
            if category not in clusters:
                clusters[category] = []
            clusters[category].append(glyph)
        return clusters

    @property
    def stats(self) -> dict:
        return {
            "evolved_glyphs": len(self.evolved_glyphs),
            "patterns_tracked": len(self._pattern_counts),
            "total_evolution_events": sum(g.usage_count for g in self.evolved_glyphs.values()),
            "avg_compression": round(
                sum(g.avg_compression for g in self.evolved_glyphs.values()) / max(len(self.evolved_glyphs), 1), 4
            ),
        }
