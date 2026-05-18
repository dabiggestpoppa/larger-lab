"""
V3 Phase 5 — Temporal Compression Engine
Converts massive event history into stable structural attractors.

Old memory: store every event → linear growth → bloat.
New memory: compress into attractors → structural persistence.
"""

from __future__ import annotations
import time
import math
from dataclasses import dataclass, field
from typing import Optional

from reconstruction.attractor_memory import AttractorMemory, Attractor


@dataclass
class CompressionResult:
    """Result of a temporal compression operation."""
    original_count: int
    compressed_count: int
    compression_ratio: float
    attractors_formed: int
    timestamp: float = field(default_factory=time.time)

    @property
    def is_effective(self) -> bool:
        return self.compression_ratio > 0.5


class TemporalCompressionEngine:
    """
    Compresses event history into stable structural attractors.
    
    Instead of storing every state transition, this engine:
    1. Clusters similar states
    2. Extracts stable patterns (attractors)
    3. Discards transient noise
    4. Preserves structural relationships
    
    Result: O(log n) storage instead of O(n) for event history.
    """

    def __init__(self, attractor_memory: AttractorMemory = None):
        self.attractor_memory = attractor_memory or AttractorMemory()
        self._compression_history: list[CompressionResult] = []

    def compress_trajectory(
        self, states: list[str], coherence_values: list[float],
        observer_clusters: list[list[str]] = None,
    ) -> CompressionResult:
        """
        Compress a sequence of states into attractors.
        
        Args:
            states: Sequence of state IDs
            coherence_values: Coherence score for each state
            observer_clusters: Observer groups active during each state
            
        Returns:
            CompressionResult with stats
        """
        original_count = len(states)
        if original_count == 0:
            return CompressionResult(0, 0, 0.0, 0)

        # Cluster states by coherence similarity
        clusters = self._cluster_states(states, coherence_values)

        # Form attractors from clusters
        attractors_formed = 0
        for i, cluster in enumerate(clusters):
            if len(cluster) >= 2:  # Minimum cluster size
                avg_coherence = sum(
                    coherence_values[states.index(s)] for s in cluster if s in states
                ) / len(cluster)

                observer = (observer_clusters[states.index(cluster[0])]
                           if observer_clusters and cluster[0] in states else [])

                self.attractor_memory.create_attractor(
                    state_id=f"compressed_{int(time.time())}_{i}",
                    observer_cluster=observer,
                    coherence=min(1.0, avg_coherence),
                    resonance_signature=[f"cluster_size_{len(cluster)}"],
                )
                attractors_formed += 1

        compressed_count = attractors_formed
        ratio = 1.0 - (compressed_count / max(original_count, 1))

        result = CompressionResult(
            original_count=original_count,
            compressed_count=compressed_count,
            compression_ratio=round(ratio, 4),
            attractors_formed=attractors_formed,
        )
        self._compression_history.append(result)
        return result

    def _cluster_states(self, states: list[str], coherence: list[float]) -> list[list[str]]:
        """Cluster states by coherence similarity."""
        if not states:
            return []

        clusters = []
        current_cluster = [states[0]]

        for i in range(1, len(states)):
            if i < len(coherence) and abs(coherence[i] - coherence[i-1]) < 0.2:
                current_cluster.append(states[i])
            else:
                clusters.append(current_cluster)
                current_cluster = [states[i]]

        clusters.append(current_cluster)
        return clusters

    def extract_attractor(self, states: list[str], coherence_values: list[float]) -> Optional[Attractor]:
        """Extract the most stable attractor from a state sequence."""
        if not states or not coherence_values:
            return None

        # Find the most coherent contiguous subsequence
        best_start = 0
        best_coherence = 0.0

        for i in range(len(states)):
            for j in range(i + 1, min(i + 10, len(states) + 1)):
                avg_c = sum(coherence_values[i:j]) / (j - i)
                if avg_c > best_coherence:
                    best_coherence = avg_c
                    best_start = i

        cluster = states[best_start:best_start + 5]
        return self.attractor_memory.create_attractor(
            state_id=f"extracted_{int(time.time())}",
            observer_cluster=[],
            coherence=best_coherence,
            resonance_signature=[f"extracted_from_{len(states)}_states"],
        )

    @property
    def stats(self) -> dict:
        if not self._compression_history:
            return {"total_compressions": 0, "avg_ratio": 0.0}
        return {
            "total_compressions": len(self._compression_history),
            "avg_ratio": round(
                sum(r.compression_ratio for r in self._compression_history) / len(self._compression_history), 4
            ),
            "total_attractors": sum(r.attractors_formed for r in self._compression_history),
        }
