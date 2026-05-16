"""
Drift Detector
==============
Detects when stored recovery anchors diverge from current system state.

Drift types:
- CONTENT_DRIFT: Anchor content no longer matches reality
- WEIGHT_DRIFT: Anchor weight is inconsistent with usage frequency
- SOURCE_DRIFT: Source system no longer exists or has changed
"""

import json
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
try:
    from .recovery_anchors import get_anchor, get_top_anchors, get_anchor_count
except ImportError:
    from recovery_anchors import get_anchor, get_top_anchors, get_anchor_count


class DriftType:
    CONTENT_DRIFT = "content_drift"
    WEIGHT_DRIFT = "weight_drift"
    SOURCE_DRIFT = "source_drift"
    STALE_DRIFT = "stale_drift"


class DriftReport:
    """A single drift detection report."""

    def __init__(self, anchor_id: str, drift_type: str, severity: float,
                 description: str, recommendation: str):
        self.anchor_id = anchor_id
        self.drift_type = drift_type
        self.severity = severity  # 0.0 to 1.0
        self.description = description
        self.recommendation = recommendation
        self.detected_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anchor_id": self.anchor_id,
            "drift_type": self.drift_type,
            "severity": self.severity,
            "description": self.description,
            "recommendation": self.recommendation,
            "detected_at": self.detected_at,
        }


class DriftDetector:
    """Detects drift between stored anchors and current state."""

    def __init__(self, staleness_days: int = 30, min_weight_threshold: float = 0.3):
        self.staleness_days = staleness_days
        self.min_weight_threshold = min_weight_threshold

    def check_staleness(self, anchor: Dict[str, Any]) -> Optional[DriftReport]:
        """Check if an anchor is stale (not updated recently)."""
        try:
            updated = datetime.fromisoformat(anchor["updated_at"])
            age = datetime.now(timezone.utc) - updated
            if age > timedelta(days=self.staleness_days):
                divisor = max(self.staleness_days * 3, 1)
                severity = min(1.0, age.days / divisor)
                return DriftReport(
                    anchor_id=anchor["id"],
                    drift_type=DriftType.STALE_DRIFT,
                    severity=severity,
                    description=f"Anchor not updated in {age.days} days",
                    recommendation="Review and update, or lower weight if no longer relevant"
                )
        except (ValueError, KeyError):
            pass
        return None

    def check_weight_consistency(self, anchor: Dict[str, Any],
                                  usage_count: int = 0) -> Optional[DriftReport]:
        """Check if anchor weight is consistent with usage."""
        weight = anchor.get("weight", 0.5)
        # High weight but never used = potential drift
        if weight > 0.7 and usage_count == 0:
            return DriftReport(
                anchor_id=anchor["id"],
                drift_type=DriftType.WEIGHT_DRIFT,
                severity=0.5,
                description=f"High weight ({weight}) but never accessed",
                recommendation="Lower weight or verify anchor is still relevant"
            )
        return None

    def scan_all(self, usage_data: Dict[str, int] = None) -> List[DriftReport]:
        """Scan all anchors for drift. Returns list of drift reports."""
        usage_data = usage_data or {}
        reports = []
        anchors = get_top_anchors(limit=100)

        for anchor in anchors:
            # Check staleness
            staleness = self.check_staleness(anchor)
            if staleness:
                reports.append(staleness)

            # Check weight consistency
            usage = usage_data.get(anchor["id"], 0)
            weight_drift = self.check_weight_consistency(anchor, usage)
            if weight_drift:
                reports.append(weight_drift)

        # Sort by severity (highest first)
        reports.sort(key=lambda r: r.severity, reverse=True)
        return reports

    def get_drift_summary(self, reports: List[DriftReport]) -> Dict[str, Any]:
        """Summarize drift reports."""
        if not reports:
            return {"status": "healthy", "total_drifts": 0, "max_severity": 0.0}

        by_type = {}
        for r in reports:
            by_type.setdefault(r.drift_type, []).append(r.severity)

        return {
            "status": "drift_detected" if reports else "healthy",
            "total_drifts": len(reports),
            "max_severity": max(r.severity for r in reports),
            "by_type": {t: len(s) for t, s in by_type.items()},
            "critical": [r.to_dict() for r in reports if r.severity > 0.7],
        }


if __name__ == "__main__":
    detector = DriftDetector(staleness_days=7)
    reports = detector.scan_all()
    summary = detector.get_drift_summary(reports)
    print(json.dumps(summary, indent=2))
