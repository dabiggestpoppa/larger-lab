"""
Adaptive Compression Engine
==============================
Phase 9 Component 4: Continuously compress redundant state while preserving recoverability.

Compresses:
- Repetitive repair patterns
- Stable synchronization routes
- Low-variance continuity structures

Preserves:
- Reconstruction-critical geometry
- Attractor memory
- Topology memory

Integration: StructuralMemoryFields, ReinforcementEngine
"""

import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class CompressionRecord:
    """Records a single compression operation."""

    def __init__(self, target: str, original_size: float,
                 compressed_size: float, recoverability_preserved: float):
        self.target = target
        self.original_size = original_size
        self.compressed_size = compressed_size
        self.recoverability_preserved = max(0.0, min(1.0, recoverability_preserved))
        self.ratio = compressed_size / original_size if original_size > 0 else 1.0
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "original_size": round(self.original_size, 2),
            "compressed_size": round(self.compressed_size, 2),
            "compression_ratio": round(self.ratio, 3),
            "recoverability_preserved": round(self.recoverability_preserved, 3),
            "timestamp": self.timestamp,
        }


class AdaptiveCompressionEngine:
    """
    Adaptive compression that preserves recoverability.

    Compression aggressiveness is controlled by a target recoverability
    threshold (default 0.90 = 90% viability preserved).
    """

    # Memory layers that should NOT be aggressively compressed
    CRITICAL_LAYERS = {"attractor", "topology", "repair"}
    # Memory layers that CAN be aggressively compressed
    COMPRESSIBLE_LAYERS = {"trajectory", "event", "context"}

    def __init__(self, target_recoverability: float = 0.90,
                 max_compression_ratio: float = 0.5):
        self.target_recoverability = target_recoverability
        self.max_compression_ratio = max_compression_ratio
        self._records: List[CompressionRecord] = []
        self._layer_ratios: Dict[str, List[float]] = defaultdict(list)

    def compress(self, target: str, original_size: float,
                 layer: str = "context") -> CompressionRecord:
        """
        Compress a state target, respecting layer criticality.

        Critical layers (attractor, topology, repair) get light compression.
        Compressible layers (trajectory, event, context) get aggressive compression.
        """
        if layer in self.CRITICAL_LAYERS:
            # Light compression: max 20% reduction
            ratio = 0.8 + (1.0 - self.target_recoverability) * 0.2
        elif layer in self.COMPRESSIBLE_LAYERS:
            # Aggressive compression: up to max_compression_ratio
            ratio = 1.0 - (1.0 - self.max_compression_ratio) * self.target_recoverability
        else:
            # Default: moderate compression
            ratio = 0.7

        compressed_size = original_size * ratio
        recoverability = self._estimate_recoverability(layer, ratio)

        record = CompressionRecord(target, original_size, compressed_size, recoverability)
        self._records.append(record)
        self._layer_ratios[layer].append(ratio)
        return record

    def _estimate_recoverability(self, layer: str, ratio: float) -> float:
        """Estimate recoverability after compression."""
        if layer in self.CRITICAL_LAYERS:
            # Critical layers: high recoverability even with compression
            return min(1.0, 1.0 - (1.0 - ratio) * 0.3)
        elif layer in self.COMPRESSIBLE_LAYERS:
            # Compressible layers: recoverability proportional to ratio
            return min(1.0, ratio + 0.2)
        else:
            return min(1.0, ratio + 0.1)

    def should_compress(self, redundancy_score: float,
                        layer: str = "context") -> bool:
        """Determine if compression should be applied based on redundancy."""
        threshold = 0.6 if layer in self.COMPRESSIBLE_LAYERS else 0.8
        return redundancy_score > threshold

    def compression_ratio(self) -> float:
        """Current overall compression ratio."""
        if not self._records:
            return 1.0
        total_original = sum(r.original_size for r in self._records)
        total_compressed = sum(r.compressed_size for r in self._records)
        if total_original == 0:
            return 1.0
        return round(total_compressed / total_original, 3)

    def avg_recoverability(self) -> float:
        """Average recoverability across all compressions."""
        if not self._records:
            return 1.0
        return round(sum(r.recoverability_preserved for r in self._records) / len(self._records), 3)

    def layer_stats(self, layer: str) -> Optional[dict]:
        """Get compression statistics for a memory layer."""
        ratios = self._layer_ratios.get(layer, [])
        if not ratios:
            return None
        return {
            "layer": layer,
            "avg_ratio": round(sum(ratios) / len(ratios), 3),
            "compressions": len(ratios),
            "is_critical": layer in self.CRITICAL_LAYERS,
        }

    def get_stats(self) -> dict:
        return {
            "total_compressions": len(self._records),
            "overall_ratio": self.compression_ratio(),
            "avg_recoverability": self.avg_recoverability(),
            "target_recoverability": self.target_recoverability,
            "layer_stats": {
                layer: self.layer_stats(layer)
                for layer in set(list(self._layer_ratios.keys()))
                if self.layer_stats(layer)
            },
        }
