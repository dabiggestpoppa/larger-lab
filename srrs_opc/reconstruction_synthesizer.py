"""
Reconstruction Synthesizer
===========================
Reconstructs coherent continuity from sparse recovery anchors.

This is the core of Phase 2: even if 90% of context is deleted,
the synthesizer can rebuild a coherent picture from the remaining anchors.

Process:
1. Load top-weighted anchors (the "core")
2. Organize by tags (clusters)
3. Generate continuity narrative
4. Identify gaps (what's missing)
"""

import json
from typing import List, Dict, Any, Optional
from collections import defaultdict
try:
    from .recovery_anchors import get_top_anchors, get_anchors_by_tag, get_stats
except ImportError:
    from recovery_anchors import get_top_anchors, get_anchors_by_tag, get_stats


class ReconstructionSynthesizer:
    """Synthesizes coherent continuity from sparse anchors."""

    def __init__(self, min_weight: float = 0.5, max_anchors: int = 20):
        self.min_weight = min_weight
        self.max_anchors = max_anchors

    def reconstruct(self) -> Dict[str, Any]:
        """
        Reconstruct continuity from current anchors.
        Returns a structured continuity report.
        """
        anchors = get_top_anchors(limit=self.max_anchors, min_weight=self.min_weight)
        stats = get_stats()

        if not anchors:
            return {
                "status": "no_data",
                "message": "No anchors available for reconstruction",
                "continuity": None,
            }

        # Organize anchors by tag clusters
        clusters = self._cluster_by_tags(anchors)

        # Generate narrative
        narrative = self._generate_narrative(anchors, clusters)

        # Identify gaps
        gaps = self._identify_gaps(anchors, clusters)

        return {
            "status": "reconstructed",
            "anchor_count": len(anchors),
            "total_available": stats["total_anchors"],
            "compression_ratio": round(len(anchors) / max(stats["total_anchors"], 1), 2),
            "clusters": {k: len(v) for k, v in clusters.items()},
            "narrative": narrative,
            "gaps": gaps,
            "confidence": self._calculate_confidence(anchors, stats),
        }

    def _cluster_by_tags(self, anchors: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """Cluster anchors by their tags."""
        clusters = defaultdict(list)
        for anchor in anchors:
            for tag in anchor.get("tags", []):
                clusters[tag].append(anchor)
        return dict(clusters)

    def _generate_narrative(self, anchors: List[Dict[str, Any]],
                            clusters: Dict[str, List[Dict]]) -> str:
        """Generate a human-readable continuity narrative."""
        lines = ["# Reconstructed Continuity", ""]

        # System identity
        identity_anchors = clusters.get("system", []) + clusters.get("architecture", [])
        if identity_anchors:
            lines.append("## System Identity")
            for a in identity_anchors[:5]:
                lines.append(f"- {a['content']}")
            lines.append("")

        # Active phases
        phase_anchors = clusters.get("srra-oph", [])
        if phase_anchors:
            lines.append("## SRRA-OPH Build Status")
            for a in phase_anchors:
                lines.append(f"- {a['content']}")
            lines.append("")

        # Constraints
        constraint_anchors = clusters.get("constraint", [])
        if constraint_anchors:
            lines.append("## Active Constraints")
            for a in constraint_anchors[:5]:
                lines.append(f"- {a['content']}")
            lines.append("")

        # Agent setup
        agent_anchors = clusters.get("agents", [])
        if agent_anchors:
            lines.append("## Agent Configuration")
            for a in agent_anchors[:3]:
                lines.append(f"- {a['content']}")
            lines.append("")

        return "\n".join(lines)

    def _identify_gaps(self, anchors: List[Dict[str, Any]],
                       clusters: Dict[str, List[Dict]]) -> List[str]:
        """Identify what's missing from the reconstruction."""
        gaps = []
        expected_categories = ["system", "architecture", "agents", "srra-oph", "constraint", "memory"]

        for cat in expected_categories:
            if cat not in clusters:
                gaps.append(f"No anchors for category: {cat}")

        if not clusters.get("trading", []):
            gaps.append("No trading strategy anchors")

        if not clusters.get("phase2", []):
            gaps.append("No Phase 2 specific anchors")

        return gaps

    def _calculate_confidence(self, anchors: List[Dict[str, Any]],
                               stats: Dict[str, Any]) -> float:
        """Calculate confidence in the reconstruction (0.0 to 1.0)."""
        if not anchors:
            return 0.0

        # Factors: anchor count, average weight, coverage
        count_factor = min(1.0, len(anchors) / 10)  # 10+ anchors = full count score
        weight_factor = stats.get("avg_weight", 0.5)
        coverage_factor = min(1.0, len(anchors) / max(stats.get("total_anchors", 1), 1))

        confidence = (count_factor * 0.3 + weight_factor * 0.5 + coverage_factor * 0.2)
        return round(min(1.0, confidence), 2)


if __name__ == "__main__":
    synthesizer = ReconstructionSynthesizer(min_weight=0.3)
    result = synthesizer.reconstruct()
    print(json.dumps(result, indent=2))
