"""
Metrics Engine
===============
Computes all required Phase 11.4.1 and 11.4.2 metrics:

Phase 11.4.1:
- Semantic Drift Index (SDI): divergence / anchor_count — Pass: < 0.15
- Reconstruction Integrity Score (RIS): original/recovered overlap — Pass: > 0.92
- Observer Consensus Stability (OCS): agreement percentage — Pass: > 85%
- Anchor Preservation Score (APS): immutable anchor survival — Pass: 100%

Phase 11.4.2:
- False Acceptance Rate (FAR): accepted_false / total_false — Pass: < 0.05
- Recovery Validation Accuracy (RVA): correct / total — Pass: > 95%
- Semantic Integrity Score (SIS): semantic coherence — Pass: > 0.90
- Topology Verification Time (TVT): avg verification time — Pass: < 45s
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class MetricsReport:
    """Complete metrics report for Phase 11.4.1 and/or 11.4.2."""

    def __init__(self, test_id: str, test_name: str):
        self.test_id = test_id
        self.test_name = test_name
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.metrics: Dict[str, float] = {}
        self.pass_fail: Dict[str, bool] = {}
        self.overall_pass = False
        self.details: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "timestamp": self.timestamp,
            "metrics": self.metrics,
            "pass_fail": self.pass_fail,
            "overall_pass": self.overall_pass,
            "details": self.details,
        }


class MetricsEngine:
    """
    Computes all required metrics for Phase 11.4.1 and 11.4.2.
    Each metric has a pass threshold defined in the amendment spec.
    """

    # Pass thresholds from the amendment
    THRESHOLDS = {
        "SDI": {"max": 0.15, "direction": "lt"},   # Semantic Drift Index < 0.15
        "RIS": {"min": 0.92, "direction": "gt"},   # Reconstruction Integrity > 0.92
        "OCS": {"min": 0.85, "direction": "gt"},   # Observer Consensus > 85%
        "APS": {"min": 1.0, "direction": "gt"},    # Anchor Preservation = 100%
        "FAR": {"max": 0.05, "direction": "lt"},   # False Acceptance Rate < 0.05
        "RVA": {"min": 0.95, "direction": "gt"},   # Recovery Validation > 95%
        "SIS": {"min": 0.90, "direction": "gt"},   # Semantic Integrity > 0.90
        "TVT": {"max": 45.0, "direction": "lt"},   # Topology Verification < 45s
    }

    def __init__(self):
        self.reports: List[MetricsReport] = []

    def evaluate(self, metric_name: str, value: float) -> bool:
        """Evaluate a single metric against its threshold."""
        threshold = self.THRESHOLDS.get(metric_name)
        if not threshold:
            return True  # No threshold = pass

        if threshold["direction"] == "lt":
            return value < threshold.get("max", float("inf"))
        elif threshold["direction"] == "gt":
            return value > threshold.get("min", float("-inf"))
        elif threshold["direction"] == "gte":
            return value >= threshold.get("min", float("-inf"))
        elif threshold["direction"] == "lte":
            return value <= threshold.get("max", float("inf"))
        return True

    def compute_sdi(self, semantic_divergence: float, anchor_count: int) -> float:
        """Semantic Drift Index = divergence / anchor_count. Pass: < 0.15"""
        if anchor_count == 0:
            return 0.0
        return min(1.0, semantic_divergence / anchor_count)

    def compute_ris(self, original_valid: int, recovered_valid: int) -> float:
        """Reconstruction Integrity Score = original / recovered. Pass: > 0.92"""
        if recovered_valid == 0:
            return 0.0
        return min(1.0, original_valid / recovered_valid)

    def compute_ocs(self, agreeing_observers: int, total_observers: int) -> float:
        """Observer Consensus Stability = agreeing / total. Pass: > 85%"""
        if total_observers == 0:
            return 1.0
        return agreeing_observers / total_observers

    def compute_aps(self, intact_anchors: int, total_immutable_anchors: int) -> float:
        """Anchor Preservation Score = intact / total_immutable. Pass: 100%"""
        if total_immutable_anchors == 0:
            return 1.0
        return intact_anchors / total_immutable_anchors

    def compute_far(self, accepted_false: int, total_false: int) -> float:
        """False Acceptance Rate = accepted_false / total_false. Pass: < 0.05"""
        if total_false == 0:
            return 0.0
        return accepted_false / total_false

    def compute_rva(self, correct_validations: int, total_validations: int) -> float:
        """Recovery Validation Accuracy = correct / total. Pass: > 95%"""
        if total_validations == 0:
            return 1.0
        return correct_validations / total_validations

    def compute_sis(self, coherent_states: int, total_states: int) -> float:
        """Semantic Integrity Score = coherent / total. Pass: > 0.90"""
        if total_states == 0:
            return 1.0
        return coherent_states / total_states

    def compute_tvt(self, verification_times: List[float]) -> float:
        """Topology Verification Time = avg verification time. Pass: < 45s"""
        if not verification_times:
            return 0.0
        return sum(verification_times) / len(verification_times)

    def generate_report(self, test_id: str, test_name: str,
                        metrics: Dict[str, float],
                        details: Optional[Dict[str, Any]] = None) -> MetricsReport:
        """
        Generate a complete metrics report with pass/fail for each metric.
        """
        report = MetricsReport(test_id, test_name)
        report.metrics = metrics
        report.details = details or {}

        all_pass = True
        for metric_name, value in metrics.items():
            passed = self.evaluate(metric_name, value)
            report.pass_fail[metric_name] = passed
            if not passed:
                all_pass = False

        report.overall_pass = all_pass
        self.reports.append(report)
        return report

    def get_all_reports(self) -> List[Dict[str, Any]]:
        """Return all generated reports."""
        return [r.to_dict() for r in self.reports]

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all reports."""
        total = len(self.reports)
        passed = sum(1 for r in self.reports if r.overall_pass)
        return {
            "total_reports": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total, 4) if total > 0 else 0.0,
        }
