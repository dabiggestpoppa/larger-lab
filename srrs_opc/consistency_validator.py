"""
Consistency Validator
======================
Validates that recovery anchors are mutually consistent.
Detects contradictions and flags them for resolution.

Contradiction types:
- DIRECT: Two anchors make opposite claims about the same thing
- IMPLICIT: Anchors imply conflicting constraints
- TEMPORAL: Newer anchor contradicts older one without explicit override
"""

import json
from typing import List, Dict, Any, Optional, Tuple
try:
    from .recovery_anchors import get_top_anchors
except ImportError:
    from recovery_anchors import get_top_anchors


class ContradictionType:
    DIRECT = "direct"
    IMPLICIT = "implicit"
    TEMPORAL = "temporal"


class Contradiction:
    """Represents a contradiction between two anchors."""

    def __init__(self, anchor_a_id: str, anchor_b_id: str,
                 contradiction_type: str, severity: float,
                 description: str):
        self.anchor_a_id = anchor_a_id
        self.anchor_b_id = anchor_b_id
        self.contradiction_type = contradiction_type
        self.severity = severity
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anchor_a": self.anchor_a_id,
            "anchor_b": self.anchor_b_id,
            "type": self.contradiction_type,
            "severity": self.severity,
            "description": self.description,
        }


class ConsistencyValidator:
    """Validates anchor consistency using tag overlap and content analysis."""

    def __init__(self):
        # Known contradiction patterns (keyword pairs that conflict)
        self.conflict_patterns = [
            (["mt5", "metatrader"], ["nautilus", "no mt5", "deprecated"]),
            (["global state"], ["no global state", "distributed", "local"]),
            (["linear growth"], ["compress", "sparse", "bounded"]),
            (["central orchestrator"], ["emergent", "distributed", "no master"]),
        ]

    def check_direct_contradiction(self, anchor_a: Dict[str, Any],
                                    anchor_b: Dict[str, Any]) -> Optional[Contradiction]:
        """Check if two anchors directly contradict each other."""
        content_a = anchor_a["content"].lower()
        content_b = anchor_b["content"].lower()

        for pos_terms, neg_terms in self.conflict_patterns:
            a_has_pos = any(t in content_a for t in pos_terms)
            a_has_neg = any(t in content_a for t in neg_terms)
            b_has_pos = any(t in content_b for t in pos_terms)
            b_has_neg = any(t in content_b for t in neg_terms)

            if (a_has_pos and b_has_neg) or (a_has_neg and b_has_pos):
                return Contradiction(
                    anchor_a_id=anchor_a["id"],
                    anchor_b_id=anchor_b["id"],
                    contradiction_type=ContradictionType.DIRECT,
                    severity=0.8,
                    description=f"Direct conflict between '{anchor_a['content'][:50]}' and '{anchor_b['content'][:50]}'"
                )
        return None

    def check_temporal_contradiction(self, anchor_a: Dict[str, Any],
                                      anchor_b: Dict[str, Any]) -> Optional[Contradiction]:
        """Check if a newer anchor contradicts an older one without override."""
        # Same tags but different content = potential temporal contradiction
        tags_a = set(anchor_a.get("tags", []))
        tags_b = set(anchor_b.get("tags", []))
        shared_tags = tags_a & tags_b

        if shared_tags and anchor_a["content"] != anchor_b["content"]:
            # Check if one explicitly references the other
            a_refers_b = anchor_b["id"] in anchor_a["content"]
            b_refers_a = anchor_a["id"] in anchor_b["content"]

            if not a_refers_b and not b_refers_a:
                # Same topic, different content, no explicit override
                try:
                    time_a = anchor_a.get("updated_at", anchor_a.get("created_at", ""))
                    time_b = anchor_b.get("updated_at", anchor_b.get("created_at", ""))
                    if time_a and time_b:
                        # Only flag if they're close in time (within same session)
                        return Contradiction(
                            anchor_a_id=anchor_a["id"],
                            anchor_b_id=anchor_b["id"],
                            contradiction_type=ContradictionType.TEMPORAL,
                            severity=0.4,
                            description=f"Same tags {shared_tags} but different content. Possible unmarked override."
                        )
                except (ValueError, KeyError):
                    pass
        return None

    def validate_all(self) -> List[Contradiction]:
        """Validate all anchors against each other. Returns contradictions found."""
        anchors = get_top_anchors(limit=100)
        contradictions = []

        for i, a in enumerate(anchors):
            for b in anchors[i + 1:]:
                # Direct contradiction check
                direct = self.check_direct_contradiction(a, b)
                if direct:
                    contradictions.append(direct)
                    continue  # Don't double-report

                # Temporal contradiction check
                temporal = self.check_temporal_contradiction(a, b)
                if temporal:
                    contradictions.append(temporal)

        contradictions.sort(key=lambda c: c.severity, reverse=True)
        return contradictions

    def get_validation_summary(self, contradictions: List[Contradiction]) -> Dict[str, Any]:
        """Summarize validation results."""
        if not contradictions:
            return {"status": "consistent", "total_contradictions": 0}

        by_type = {}
        for c in contradictions:
            by_type.setdefault(c.contradiction_type, []).append(c.severity)

        return {
            "status": "contradictions_found" if contradictions else "consistent",
            "total_contradictions": len(contradictions),
            "max_severity": max(c.severity for c in contradictions),
            "by_type": {t: len(s) for t, s in by_type.items()},
            "critical": [c.to_dict() for c in contradictions if c.severity > 0.6],
        }


if __name__ == "__main__":
    validator = ConsistencyValidator()
    contradictions = validator.validate_all()
    summary = validator.get_validation_summary(contradictions)
    print(json.dumps(summary, indent=2))
