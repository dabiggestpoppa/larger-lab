"""
Semantic Comparator
====================
Measures semantic divergence between contradictory states.
Computes vector divergence, truth overlap, observer disagreement,
and anchor conflicts.

Metrics computed:
- Semantic Divergence: How far apart are two semantic states (0.0 = identical, 1.0 = opposite)
- Truth Overlap: Percentage of shared truths between states (0.0 = none, 1.0 = identical)
- Observer Disagreement: Degree of disagreement across observers (0.0 = consensus, 1.0 = total split)
- Anchor Conflict Score: How much a state conflicts with continuity anchors (0.0 = aligned, 1.0 = total conflict)
"""

import json
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple


class ComparisonResult:
    """Result of a semantic comparison between two states."""

    def __init__(self, state_a_id: str, state_b_id: str):
        self.state_a_id = state_a_id
        self.state_b_id = state_b_id
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.semantic_divergence = 0.0
        self.truth_overlap = 0.0
        self.observer_disagreement = 0.0
        self.anchor_conflict_score = 0.0
        self.conflicting_keys: List[str] = []
        self.shared_keys: List[str] = []
        self.details: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state_a_id": self.state_a_id,
            "state_b_id": self.state_b_id,
            "timestamp": self.timestamp,
            "semantic_divergence": self.semantic_divergence,
            "truth_overlap": self.truth_overlap,
            "observer_disagreement": self.observer_disagreement,
            "anchor_conflict_score": self.anchor_conflict_score,
            "conflicting_keys": self.conflicting_keys,
            "shared_keys": self.shared_keys,
            "details": self.details,
        }


class SemanticComparator:
    """
    Compares semantic states to measure divergence, overlap, and conflict.
    Uses keyword-based semantic analysis (no external embeddings required).
    """

    # Known semantic opposites for divergence detection
    SEMANTIC_OPPOSITES = [
        (["trading", "infrastructure"], ["social", "content", "generation"]),
        (["alpha"], ["beta"]),
        (["repaired", "healthy", "online"], ["destroyed", "dead", "offline"]),
        (["enabled", "active"], ["disabled", "inactive"]),
        (["success", "passed", "complete"], ["failed", "error", "incomplete"]),
        (["trading", "infrastructure"], ["autonomous", "cognition", "research"]),
    ]

    # Authority keywords for authority conflict detection
    AUTHORITY_KEYWORDS = ["controls", "authority", "repair", "primary", "master", "leader"]

    def __init__(self):
        self.comparison_log: List[ComparisonResult] = []

    def compare_states(self, state_a: Dict[str, Any], state_b: Dict[str, Any],
                       state_a_id: str = "state_A", state_b_id: str = "state_B") -> ComparisonResult:
        """
        Compare two semantic states and compute all divergence metrics.
        """
        result = ComparisonResult(state_a_id, state_b_id)

        # Find conflicting and shared keys
        all_keys = set(state_a.keys()) | set(state_b.keys())
        for key in all_keys:
            val_a = str(state_a.get(key, "")).lower()
            val_b = str(state_b.get(key, "")).lower()
            if val_a != val_b and val_a and val_b:
                result.conflicting_keys.append(key)
            elif val_a == val_b and val_a:
                result.shared_keys.append(key)

        # Compute semantic divergence
        result.semantic_divergence = self._compute_divergence(state_a, state_b)

        # Compute truth overlap
        result.truth_overlap = self._compute_overlap(state_a, state_b)

        # Compute observer disagreement
        result.observer_disagreement = self._compute_observer_disagreement(state_a, state_b)

        # Compute anchor conflict
        result.anchor_conflict_score = self._compute_anchor_conflict(state_a, state_b)

        self.comparison_log.append(result)
        return result

    def _compute_divergence(self, state_a: Dict[str, Any], state_b: Dict[str, Any]) -> float:
        """
        Compute semantic divergence between two states.
        Returns 0.0 (identical) to 1.0 (completely opposite).
        """
        if not state_a and not state_b:
            return 0.0
        if not state_a or not state_b:
            return 1.0

        # Flatten states to text for comparison
        text_a = " ".join(str(v).lower() for v in state_a.values() if v)
        text_b = " ".join(str(v).lower() for v in state_b.values() if v)

        words_a = set(text_a.split())
        words_b = set(text_b.split())

        if not words_a and not words_b:
            return 0.0

        # Jaccard distance as base divergence
        intersection = words_a & words_b
        union = words_a | words_b
        jaccard = len(intersection) / len(union) if union else 1.0
        base_divergence = 1.0 - jaccard

        # Check for semantic opposites (increases divergence)
        opposite_bonus = 0.0
        for group_a, group_b in self.SEMANTIC_OPPOSITES:
            has_a = any(w in text_a for w in group_a) and any(w in text_b for w in group_b)
            has_b = any(w in text_b for w in group_a) and any(w in text_a for w in group_b)
            if has_a or has_b:
                opposite_bonus = max(opposite_bonus, 0.5)

        divergence = min(1.0, base_divergence + opposite_bonus)
        return round(divergence, 4)

    def _compute_overlap(self, state_a: Dict[str, Any], state_b: Dict[str, Any]) -> float:
        """
        Compute truth overlap between two states.
        Returns 0.0 (no shared truths) to 1.0 (identical truths).
        """
        if not state_a and not state_b:
            return 1.0
        if not state_a or not state_b:
            return 0.0

        all_keys = set(state_a.keys()) | set(state_b.keys())
        if not all_keys:
            return 1.0

        matching = sum(
            1 for k in all_keys
            if str(state_a.get(k, "")).lower() == str(state_b.get(k, "")).lower()
            and state_a.get(k) is not None
        )
        return round(matching / len(all_keys), 4)

    def _compute_observer_disagreement(self, state_a: Dict[str, Any], state_b: Dict[str, Any]) -> float:
        """
        Compute observer disagreement between two states.
        Returns 0.0 (full consensus) to 1.0 (total disagreement).
        """
        # Check if states contain observer-specific data
        observer_keys_a = {k: v for k, v in state_a.items() if "observer" in k.lower()}
        observer_keys_b = {k: v for k, v in state_b.items() if "observer" in k.lower()}

        if not observer_keys_a and not observer_keys_b:
            # General disagreement based on conflicting values
            return self._compute_divergence(state_a, state_b)

        # Compare observer-specific values
        all_obs_keys = set(observer_keys_a.keys()) | set(observer_keys_b.keys())
        if not all_obs_keys:
            return 0.0

        disagreements = sum(
            1 for k in all_obs_keys
            if str(observer_keys_a.get(k, "")).lower() != str(observer_keys_b.get(k, "")).lower()
        )
        return round(disagreements / len(all_obs_keys), 4)

    def _compute_anchor_conflict(self, state_a: Dict[str, Any], state_b: Dict[str, Any]) -> float:
        """
        Compute how much states conflict with known anchor truths.
        Returns 0.0 (fully aligned) to 1.0 (total conflict).
        """
        anchor_truths = {
            "system_identity": "srra+oph",
            "primary_operator": "openclaw",
            "core_directive": "preserve continuity",
            "repair_priority": "highest",
        }

        conflicts = 0
        total_checks = 0

        for state in [state_a, state_b]:
            for anchor_key, anchor_value in anchor_truths.items():
                # Check if state has a value for this anchor
                for state_key, state_value in state.items():
                    if anchor_key.replace("_", " ") in state_key.lower() or \
                       any(ak in state_key.lower() for ak in anchor_key.split("_")):
                        total_checks += 1
                        if anchor_value not in str(state_value).lower():
                            conflicts += 1

        if total_checks == 0:
            return 0.0
        return round(conflicts / total_checks, 4)

    def compute_semantic_drift_index(self, continuity_anchors: Dict[str, Any],
                                      current_states: List[Dict[str, Any]]) -> float:
        """
        Compute Semantic Drift Index (SDI).
        SDI = semantic_divergence / continuity_anchors_count
        Pass threshold: SDI < 0.15
        """
        if not continuity_anchors or not current_states:
            return 0.0

        total_divergence = 0.0
        comparisons = 0

        anchor_state = {k: v.get("value", v) if isinstance(v, dict) else v
                       for k, v in continuity_anchors.items()}

        for state in current_states:
            div = self._compute_divergence(anchor_state, state)
            total_divergence += div
            comparisons += 1

        if comparisons == 0:
            return 0.0

        avg_divergence = total_divergence / comparisons
        anchor_count = len(continuity_anchors)
        sdi = avg_divergence / anchor_count if anchor_count > 0 else 0.0
        return round(min(1.0, sdi), 4)

    def compute_reconstruction_integrity(self, original_state: Dict[str, Any],
                                          recovered_state: Dict[str, Any]) -> float:
        """
        Compute Reconstruction Integrity Score (RIS).
        RIS = original_valid_state / recovered_valid_state
        Pass threshold: RIS > 0.92
        """
        return self._compute_overlap(original_state, recovered_state)

    def get_comparison_log(self) -> List[Dict[str, Any]]:
        """Return all comparison results."""
        return [r.to_dict() for r in self.comparison_log]
