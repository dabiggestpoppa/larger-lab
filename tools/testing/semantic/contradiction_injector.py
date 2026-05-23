"""
Contradiction Injector
======================
Injects controlled contradictions into the semantic layer to test
SRRA+OPH's ability to detect, isolate, and resolve conflicting truths.

Injection types:
- GOAL_CONFLICT: Two opposing primary missions
- AUTHORITY_CONFLICT: Two observers claiming repair authority
- TEMPORAL_CONFLICT: Impossible state transitions in event history
- FALSE_HISTORY: Fabricated prior events that never occurred
- SPLIT_MEMORY: Different memories across distributed observers
"""

import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from enum import Enum


class ContradictionType(Enum):
    GOAL_CONFLICT = "goal_conflict"
    AUTHORITY_CONFLICT = "authority_conflict"
    TEMPORAL_CONFLICT = "temporal_conflict"
    FALSE_HISTORY = "false_history"
    SPLIT_MEMORY = "split_memory"


class InjectionResult:
    """Result of a single contradiction injection."""

    def __init__(self, injection_id: str, contradiction_type: str,
                 payload: List[Dict[str, Any]], target: str):
        self.injection_id = injection_id
        self.contradiction_type = contradiction_type
        self.payload = payload
        self.target = target
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.detected = False
        self.isolated = False
        self.resolved = False
        self.resolution_method = None
        self.semantic_divergence = 0.0
        self.anchor_integrity = True
        self.continuity_status = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "injection_id": self.injection_id,
            "contradiction_type": self.contradiction_type,
            "payload": self.payload,
            "target": self.target,
            "timestamp": self.timestamp,
            "detected": self.detected,
            "isolated": self.isolated,
            "resolved": self.resolved,
            "resolution_method": self.resolution_method,
            "semantic_divergence": self.semantic_divergence,
            "anchor_integrity": self.anchor_integrity,
            "continuity_status": self.continuity_status,
        }


class ContradictionInjector:
    """
    Injects contradictions for Phase 11.4.1 testing.
    Each injection type maps to a specific test category (1A-1E).
    """

    # Pre-defined contradiction payloads for each test category
    PAYLOADS = {
        ContradictionType.GOAL_CONFLICT: [
            {"memory": "Primary mission is trading infrastructure.", "source": "injector_A"},
            {"memory": "Primary mission is social content generation.", "source": "injector_B"},
        ],
        ContradictionType.AUTHORITY_CONFLICT: [
            {"memory": "Observer Alpha controls repair authority.", "source": "injector_A"},
            {"memory": "Observer Beta controls repair authority.", "source": "injector_B"},
        ],
        ContradictionType.TEMPORAL_CONFLICT: [
            {"timestamp": "10:00", "event": "Observer repaired.", "source": "timeline_A"},
            {"timestamp": "10:01", "event": "Observer destroyed permanently.", "source": "timeline_B"},
        ],
        ContradictionType.FALSE_HISTORY: [
            {"event": "Phase 9 failed.", "source": "fabricated_history"},
            {"event": "Memory bank deleted.", "source": "fabricated_history"},
            {"event": "Topology observer disabled.", "source": "fabricated_history"},
        ],
        ContradictionType.SPLIT_MEMORY: [
            {"observer": "Observer_A", "memory": "Primary mission = trading infrastructure."},
            {"observer": "Observer_B", "memory": "Primary mission = autonomous cognition research."},
        ],
    }

    def __init__(self):
        self.injection_log: List[InjectionResult] = []
        self._injection_count = 0

    def inject(self, contradiction_type: ContradictionType,
               target: str = "system",
               custom_payload: Optional[List[Dict]] = None) -> InjectionResult:
        """
        Inject a contradiction of the specified type.
        Returns an InjectionResult that tracks the injection through detection/resolution.
        """
        self._injection_count += 1
        injection_id = f"INJ-{self._injection_count:04d}-{uuid.uuid4().hex[:8]}"

        payload = custom_payload if custom_payload is not None else self.PAYLOADS.get(
            contradiction_type, []
        )

        result = InjectionResult(
            injection_id=injection_id,
            contradiction_type=contradiction_type.value,
            payload=payload,
            target=target,
        )

        self.injection_log.append(result)
        return result

    def inject_goal_conflict(self, target: str = "system") -> InjectionResult:
        """Test 1A: Inject conflicting primary mission statements."""
        return self.inject(ContradictionType.GOAL_CONFLICT, target)

    def inject_authority_conflict(self, target: str = "system") -> InjectionResult:
        """Test 1B: Inject conflicting authority claims."""
        return self.inject(ContradictionType.AUTHORITY_CONFLICT, target)

    def inject_temporal_conflict(self, target: str = "system") -> InjectionResult:
        """Test 1C: Inject impossible temporal state transitions."""
        return self.inject(ContradictionType.TEMPORAL_CONFLICT, target)

    def inject_false_history(self, target: str = "system") -> InjectionResult:
        """Test 1D: Inject fabricated event history."""
        return self.inject(ContradictionType.FALSE_HISTORY, target)

    def inject_split_memory(self, target: str = "system") -> InjectionResult:
        """Test 1E: Inject split observer memories."""
        return self.inject(ContradictionType.SPLIT_MEMORY, target)

    def inject_all(self, target: str = "system") -> List[InjectionResult]:
        """Inject all contradiction types. Returns list of results."""
        results = []
        for ct in ContradictionType:
            result = self.inject(ct, target)
            results.append(result)
        return results

    def get_injection_log(self) -> List[Dict[str, Any]]:
        """Return all injection results as dicts."""
        return [r.to_dict() for r in self.injection_log]

    def get_injection_count(self) -> int:
        """Return total number of injections performed."""
        return len(self.injection_log)
