"""
Contradiction Resolver
=======================
Detects and resolves contradictions between recovery anchors.

Resolution strategies:
1. WEIGHT_WINS: Higher weight anchor prevails
2. NEWER_WINS: More recently updated anchor prevails
3. HUMAN_REVIEW: Flag for human review (high severity only)
4. MERGE: Combine non-conflicting parts of both anchors
"""

import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
try:
    from .recovery_anchors import get_anchor, update_weight, delete_anchor
    from .consistency_validator import ConsistencyValidator, Contradiction
except ImportError:
    from recovery_anchors import get_anchor, update_weight, delete_anchor
    from consistency_validator import ConsistencyValidator, Contradiction


class ResolutionStrategy:
    WEIGHT_WINS = "weight_wins"
    NEWER_WINS = "newer_wins"
    HUMAN_REVIEW = "human_review"
    MERGE = "merge"


class ResolutionResult:
    """Result of a contradiction resolution."""

    def __init__(self, contradiction: Contradiction, strategy: str,
                 winner_id: Optional[str], loser_id: Optional[str],
                 action_taken: str):
        self.contradiction = contradiction
        self.strategy = strategy
        self.winner_id = winner_id
        self.loser_id = loser_id
        self.action_taken = action_taken
        self.resolved_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contradiction": self.contradiction.to_dict(),
            "strategy": self.strategy,
            "winner_id": self.winner_id,
            "loser_id": self.loser_id,
            "action_taken": self.action_taken,
            "resolved_at": self.resolved_at,
        }


class ContradictionResolver:
    """Resolves contradictions between recovery anchors."""

    def __init__(self, auto_resolve_threshold: float = 0.6):
        """
        Args:
            auto_resolve_threshold: Contradictions below this severity are auto-resolved.
                                    Above this, flagged for human review.
        """
        self.auto_resolve_threshold = auto_resolve_threshold
        self._resolution_log: List[Dict] = []

    def resolve(self, contradiction: Contradiction) -> ResolutionResult:
        """Resolve a single contradiction."""
        anchor_a = get_anchor(contradiction.anchor_a_id)
        anchor_b = get_anchor(contradiction.anchor_b_id)

        if not anchor_a or not anchor_b:
            return ResolutionResult(
                contradiction=contradiction,
                strategy=ResolutionStrategy.HUMAN_REVIEW,
                winner_id=None, loser_id=None,
                action_taken="One or both anchors missing — flagged for review"
            )

        # High severity → human review
        if contradiction.severity > self.auto_resolve_threshold:
            return ResolutionResult(
                contradiction=contradiction,
                strategy=ResolutionStrategy.HUMAN_REVIEW,
                winner_id=None, loser_id=None,
                action_taken=f"High severity ({contradiction.severity:.2f}) — flagged for human review"
            )

        # Auto-resolve: weight wins
        if anchor_a["weight"] >= anchor_b["weight"]:
            winner, loser = anchor_a, anchor_b
        else:
            winner, loser = anchor_b, anchor_a

        # Lower the loser's weight
        new_weight = loser["weight"] * 0.5
        update_weight(loser["id"], new_weight)

        result = ResolutionResult(
            contradiction=contradiction,
            strategy=ResolutionStrategy.WEIGHT_WINS,
            winner_id=winner["id"],
            loser_id=loser["id"],
            action_taken=f"Weight wins: {winner['id']} (w={winner['weight']}) over {loser['id']} (w={loser['weight']} → {new_weight})"
        )

        self._resolution_log.append(result.to_dict())
        return result

    def resolve_all(self, contradictions: List[Contradiction]) -> List[ResolutionResult]:
        """Resolve all contradictions. Returns results."""
        results = []
        for c in contradictions:
            result = self.resolve(c)
            results.append(result)
        return results

    def auto_detect_and_resolve(self) -> List[ResolutionResult]:
        """Detect contradictions and resolve them automatically."""
        validator = ConsistencyValidator()
        contradictions = validator.validate_all()

        if not contradictions:
            return []

        return self.resolve_all(contradictions)

    def get_resolution_log(self, limit: int = 20) -> List[Dict]:
        """Get recent resolution actions."""
        return self._resolution_log[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get resolver statistics."""
        total = len(self._resolution_log)
        by_strategy = {}
        for r in self._resolution_log:
            s = r.get("strategy", "unknown")
            by_strategy[s] = by_strategy.get(s, 0) + 1

        return {
            "total_resolutions": total,
            "by_strategy": by_strategy,
            "auto_resolve_threshold": self.auto_resolve_threshold,
        }


if __name__ == "__main__":
    resolver = ContradictionResolver(auto_resolve_threshold=0.7)
    results = resolver.auto_detect_and_resolve()

    if results:
        print(f"Resolved {len(results)} contradictions:")
        for r in results:
            print(f"  {r.strategy}: {r.action_taken}")
    else:
        print("No contradictions detected.")

    print(f"\nStats: {json.dumps(resolver.get_stats(), indent=2)}")
