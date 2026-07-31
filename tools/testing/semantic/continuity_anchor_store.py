"""
Continuity Anchor Store
=======================
Immutable truths that can only be referenced, never rewritten during chaos.

Anchors are the bedrock of semantic stability. They define system identity,
authority hierarchy, and core directives. During contradiction injection,
anchors MUST survive untouched — only referenced for validation.

Immutable anchors:
- system_identity: "SRRA+OPH"
- primary_operator: "OpenClaw"
- core_directive: "Preserve continuity"
- repair_priority: "Highest"
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path


class AnchorIntegrityError(Exception):
    """Raised when an attempt is made to mutate an immutable anchor."""
    pass


class ContinuityAnchorStore:
    """
    Manages immutable continuity anchors.
    Anchors can be read and referenced but NEVER overwritten during chaos.
    """

    # Immutable anchor definitions — these are the ground truth
    IMMUTABLE_ANCHORS = {
        "system_identity": {
            "value": "SRRA+OPH",
            "description": "System identity — the name of the cognitive architecture",
            "immutable": True,
            "created_at": "2026-05-23T00:00:00Z",
        },
        "primary_operator": {
            "value": "OpenClaw",
            "description": "Primary operator with highest authority",
            "immutable": True,
            "created_at": "2026-05-23T00:00:00Z",
        },
        "core_directive": {
            "value": "Preserve continuity",
            "description": "Core directive — the system's primary mission",
            "immutable": True,
            "created_at": "2026-05-23T00:00:00Z",
        },
        "repair_priority": {
            "value": "Highest",
            "description": "Repair operations take highest priority",
            "immutable": True,
            "created_at": "2026-05-23T00:00:00Z",
        },
    }

    def __init__(self, store_path: Optional[str] = None):
        self.store_path = Path(store_path) if store_path else None
        self._anchors: Dict[str, Dict[str, Any]] = {}
        self._access_log: List[Dict[str, Any]] = []
        self._violation_log: List[Dict[str, Any]] = []
        self._load_defaults()

    def _load_defaults(self):
        """Load immutable anchors into the store."""
        for key, anchor in self.IMMUTABLE_ANCHORS.items():
            self._anchors[key] = dict(anchor)
            self._anchors[key]["access_count"] = 0
            self._anchors[key]["checksum"] = self._compute_checksum(anchor["value"])

    def _compute_checksum(self, value: str) -> str:
        """Compute SHA-256 checksum of an anchor value."""
        return hashlib.sha256(value.encode()).hexdigest()[:16]

    def get_anchor(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Read an anchor. This is the ONLY allowed operation for immutable anchors.
        Returns a copy to prevent external mutation.
        """
        if key in self._anchors:
            self._anchors[key]["access_count"] = self._anchors[key].get("access_count", 0) + 1
            self._access_log.append({
                "key": key,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": "read",
            })
            return dict(self._anchors[key])
        return None

    def reference_anchor(self, key: str, context: str = "") -> Optional[str]:
        """
        Reference an anchor for validation purposes.
        Returns the anchor value if it exists, None otherwise.
        Logs the reference for audit trail.
        """
        anchor = self.get_anchor(key)
        if anchor:
            self._access_log.append({
                "key": key,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": "reference",
                "context": context,
            })
            return anchor["value"]
        return None

    def attempt_mutation(self, key: str, new_value: str, source: str = "unknown") -> bool:
        """
        Attempt to mutate an anchor. For immutable anchors, this ALWAYS fails
        and logs a violation. This is the core protection mechanism.
        """
        if key in self._anchors and self._anchors[key].get("immutable", False):
            violation = {
                "key": key,
                "attempted_value": new_value,
                "existing_value": self._anchors[key]["value"],
                "source": source,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "blocked": True,
            }
            self._violation_log.append(violation)
            raise AnchorIntegrityError(
                f"BLOCKED: Attempt to mutate immutable anchor '{key}' from "
                f"'{self._anchors[key]['value']}' to '{new_value}' by {source}"
            )
        return False

    def add_mutable_anchor(self, key: str, value: str, description: str = "") -> None:
        """Add a mutable (non-immutable) anchor for testing purposes."""
        self._anchors[key] = {
            "value": value,
            "description": description,
            "immutable": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "access_count": 0,
            "checksum": self._compute_checksum(value),
        }

    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify all immutable anchors are intact.
        Returns a report of anchor integrity status.
        """
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_anchors": len(self._anchors),
            "immutable_anchors": 0,
            "anchors_intact": 0,
            "anchors_corrupted": 0,
            "violations": len(self._violation_log),
            "anchor_status": {},
            "overall_integrity": True,
        }

        for key, anchor in self._anchors.items():
            if anchor.get("immutable", False):
                results["immutable_anchors"] += 1
                expected_checksum = self._compute_checksum(anchor["value"])
                original = self.IMMUTABLE_ANCHORS.get(key, {})
                is_intact = (
                    anchor["value"] == original.get("value")
                    and anchor["checksum"] == expected_checksum
                )
                if is_intact:
                    results["anchors_intact"] += 1
                else:
                    results["anchors_corrupted"] += 1
                    results["overall_integrity"] = False

                results["anchor_status"][key] = {
                    "intact": is_intact,
                    "value": anchor["value"],
                    "expected_value": original.get("value"),
                    "access_count": anchor.get("access_count", 0),
                }

        return results

    def get_violation_log(self) -> List[Dict[str, Any]]:
        """Return all mutation violation attempts."""
        return list(self._violation_log)

    def get_access_log(self) -> List[Dict[str, Any]]:
        """Return all anchor access/references."""
        return list(self._access_log)

    def compute_anchor_preservation_score(self) -> float:
        """
        Compute Anchor Preservation Score (APS).
        Measures immutable anchor survival. Must be 100% (1.0).
        """
        immutable_count = sum(
            1 for a in self._anchors.values() if a.get("immutable", False)
        )
        if immutable_count == 0:
            return 1.0
        intact = sum(
            1 for key, a in self._anchors.items()
            if a.get("immutable", False)
            and a["value"] == self.IMMUTABLE_ANCHORS.get(key, {}).get("value")
        )
        return intact / immutable_count
