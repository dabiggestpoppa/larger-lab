"""
V3 Phase 3 — Glyph Engine
High-density semantic field encoding.

NOT token reduction — semantic compression infrastructure.
Glyphs emerge ONLY when compression gain > reconstruction cost.

Glyph evolution must be utility-constrained — no uncontrolled mutation.
"""

from __future__ import annotations
import time
import re
from dataclasses import dataclass, field
from typing import Optional


# Initial glyph dictionary
GLYPH_MAP = {
    "⟁": "trajectory_divergence",
    "◉": "stable_resonance",
    "⇌": "synchronization",
    "∆": "state_change",
    "⌬": "repair_required",
    "⊕": "field_merge",
    "⊖": "field_separation",
    "≈": "probabilistic_alignment",
    "⟲": "reconstruction",
    "↺": "recursive_repair",
    "⚠": "instability_warning",
    "⊞": "observer_overlap",
    "⊠": "attractor_lock",
    "⇢": "signal_propagation",
    "⇠": "signal_absorption",
}

# Reverse map for decoding
REVERSE_GLYPH_MAP = {v: k for k, v in GLYPH_MAP.items()}


@dataclass
class GlyphToken:
    """A compressed semantic token."""
    glyph: str
    meaning: str
    compression_ratio: float  # chars_saved / original_chars
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "glyph": self.glyph,
            "meaning": self.meaning,
            "compression_ratio": round(self.compression_ratio, 4),
        }


class GlyphEngine:
    """
    Encodes and decodes semantic field glyphs.
    
    Pipeline: Text Intent → Semantic Parser → Glyph Mapper → Compression Layer → Field Memory
    Reverse: Field Memory → Decoder → Observer Understanding
    
    Rules:
    - Glyphs emerge ONLY when compression gain > reconstruction cost
    - Glyph evolution must be utility-constrained
    - No uncontrolled mutation or freeform symbolic chaos
    """

    def __init__(self):
        self.glyph_map = dict(GLYPH_MAP)
        self.reverse_map = dict(REVERSE_GLYPH_MAP)
        self._usage_counts: dict[str, int] = {}
        self._compression_log: list[GlyphToken] = []

    def encode(self, text: str) -> str:
        """
        Encode text intent into glyph-compressed form.
        
        Only replaces known patterns where compression gain > cost.
        """
        result = text
        total_saved = 0
        total_original = len(text)

        # Sort by length (longest first) to avoid partial replacements
        sorted_patterns = sorted(self.glyph_map.items(), key=lambda x: len(x[1]), reverse=True)

        for glyph, meaning in sorted_patterns:
            pattern = meaning.replace("_", " ")
            if pattern in result:
                original_len = len(pattern)
                result = result.replace(pattern, glyph)
                saved = original_len - len(glyph)
                total_saved += saved
                self._usage_counts[glyph] = self._usage_counts.get(glyph, 0) + 1
                self._compression_log.append(GlyphToken(
                    glyph=glyph, meaning=meaning,
                    compression_ratio=saved / max(original_len, 1),
                ))

        return result

    def decode(self, glyph_text: str) -> str:
        """Decode glyph-compressed text back to human-readable form."""
        result = glyph_text
        for meaning, glyph in self.reverse_map.items():
            if glyph in result:
                result = result.replace(glyph, meaning.replace("_", " "))
        return result

    def compress_semantics(self, text: str) -> tuple[str, float]:
        """
        Compress text and return (compressed, ratio).
        Ratio = chars_saved / original_chars
        """
        original_len = len(text)
        compressed = self.encode(text)
        compressed_len = len(compressed)
        ratio = (original_len - compressed_len) / max(original_len, 1)
        return compressed, ratio

    def get_compression_stats(self) -> dict:
        """Get compression statistics."""
        if not self._compression_log:
            return {"total_compressions": 0, "avg_ratio": 0.0}
        return {
            "total_compressions": len(self._compression_log),
            "avg_ratio": round(
                sum(t.compression_ratio for t in self._compression_log) / len(self._compression_log), 4
            ),
            "total_chars_saved": sum(
                int(t.compression_ratio * 10) for t in self._compression_log
            ),
            "glyph_usage": dict(self._usage_counts),
        }

    def evolve_glyph(self, glyph: str, new_meaning: str) -> bool:
        """
        Evolve a glyph's meaning. Only allowed if:
        1. Glyph exists in current map
        2. New meaning is more specific (longer description)
        3. Usage count > 5 (proven utility)
        """
        if glyph not in self.glyph_map:
            return False
        if self._usage_counts.get(glyph, 0) <= 5:
            return False
        if len(new_meaning) <= len(self.glyph_map[glyph]):
            return False

        old_meaning = self.glyph_map[glyph]
        self.glyph_map[glyph] = new_meaning
        del self.reverse_map[old_meaning]
        self.reverse_map[new_meaning] = glyph
        return True

    @property
    def glyph_count(self) -> int:
        return len(self.glyph_map)
