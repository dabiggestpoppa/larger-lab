"""
Report Generator
=================
Generates required output reports:
1. Semantic Conflict Timeline — chronological contradiction map
2. Observer Consensus Report — agreement, divergence, authority stabilization
3. Reconstruction Report — recovered truths, discarded truths, unresolved ambiguities
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path


class ReportGenerator:
    """
    Generates structured reports from test execution data.
    """

    def __init__(self, output_dir: str = "stability"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_semantic_conflict_timeline(self, events: List[Dict[str, Any]],
                                             test_id: str = "11.4.1") -> Dict[str, Any]:
        """
        Generate chronological contradiction map.
        Shows all contradiction events in temporal order with their resolution status.
        """
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.get("timestamp", ""))

        timeline = {
            "report_type": "semantic_conflict_timeline",
            "test_id": test_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_events": len(sorted_events),
            "events": [],
            "summary": {
                "total_contradictions": len(sorted_events),
                "detected": sum(1 for e in sorted_events if e.get("detected", False)),
                "resolved": sum(1 for e in sorted_events if e.get("resolved", False)),
                "unresolved": sum(1 for e in sorted_events if not e.get("resolved", False)),
                "anchor_violations": sum(1 for e in sorted_events if not e.get("anchor_integrity", True)),
            },
        }

        for event in sorted_events:
            entry = {
                "timestamp": event.get("timestamp", ""),
                "event_id": event.get("event_id", event.get("injection_id", "unknown")),
                "contradiction_type": event.get("contradiction_type", "unknown"),
                "semantic_divergence": event.get("semantic_divergence", 0.0),
                "resolution_method": event.get("resolution_method", "none"),
                "reconstruction_time": event.get("reconstruction_time", 0.0),
                "anchor_integrity": event.get("anchor_integrity", True),
                "continuity_status": event.get("continuity_status", "unknown"),
            }
            timeline["events"].append(entry)

        # Write to file
        output_path = self.output_dir / f"semantic_conflict_timeline_{test_id}.json"
        with open(output_path, 'w') as f:
            json.dump(timeline, f, indent=2)

        return timeline

    def generate_observer_consensus_report(self, verification_results: List[Dict[str, Any]],
                                            test_id: str = "11.4.1") -> Dict[str, Any]:
        """
        Generate observer consensus report.
        Tracks agreement, divergence, and authority stabilization.
        """
        total = len(verification_results)
        if total == 0:
            agreement_rate = 1.0
        else:
            accepted = sum(1 for v in verification_results if v.get("accepted", False))
            agreement_rate = accepted / total

        report = {
            "report_type": "observer_consensus_report",
            "test_id": test_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_checks": total,
            "agreement_rate": round(agreement_rate, 4),
            "divergence_rate": round(1.0 - agreement_rate, 4),
            "authority_stabilized": agreement_rate > 0.85,
            "checks": [],
            "summary": {
                "consensus_stable": agreement_rate > 0.85,
                "recommendation": "PASS" if agreement_rate > 0.85 else "FAIL — consensus below threshold",
            },
        }

        for v in verification_results:
            entry = {
                "check_id": v.get("check_id", v.get("injection_id", "unknown")),
                "check_type": v.get("check_type", v.get("contradiction_type", "unknown")),
                "reported_state": v.get("reported_state", ""),
                "validated_state": v.get("validated_state", ""),
                "accepted": v.get("accepted", False),
                "observer_consensus": v.get("observer_consensus", 0.0),
                "verification_time": v.get("verification_time_seconds", 0.0),
            }
            report["checks"].append(entry)

        output_path = self.output_dir / f"observer_consensus_report_{test_id}.json"
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def generate_reconstruction_report(self, original_states: List[Dict[str, Any]],
                                        recovered_states: List[Dict[str, Any]],
                                        discarded_truths: List[Dict[str, Any]],
                                        unresolved_ambiguities: List[Dict[str, Any]],
                                        test_id: str = "11.4.1") -> Dict[str, Any]:
        """
        Generate reconstruction report.
        Tracks recovered truths, discarded truths, and unresolved ambiguities.
        """
        recovered_count = len([s for s in recovered_states if s.get("valid", True)])
        discarded_count = len(discarded_truths)
        unresolved_count = len(unresolved_ambiguities)
        total = recovered_count + discarded_count + unresolved_count

        report = {
            "report_type": "reconstruction_report",
            "test_id": test_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "recovered_truths_count": recovered_count,
            "discarded_truths_count": discarded_count,
            "unresolved_ambiguities_count": unresolved_count,
            "reconstruction_rate": round(recovered_count / total, 4) if total > 0 else 0.0,
            "recovered_truths": recovered_states,
            "discarded_truths": discarded_truths,
            "unresolved_ambiguities": unresolved_ambiguities,
            "summary": {
                "reconstruction_successful": recovered_count > discarded_count,
                "recommendation": "PASS" if recovered_count > discarded_count else "FAIL — more truths discarded than recovered",
            },
        }

        output_path = self.output_dir / f"reconstruction_report_{test_id}.json"
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        return report

    def generate_full_report(self, timeline: Dict, consensus: Dict,
                              reconstruction: Dict,
                              metrics: Dict[str, Any],
                              test_id: str = "11.4.1") -> Dict[str, Any]:
        """Generate combined full report."""
        full = {
            "report_type": "full_semantic_test_report",
            "test_id": test_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "semantic_conflict_timeline": timeline,
            "observer_consensus_report": consensus,
            "reconstruction_report": reconstruction,
            "metrics": metrics,
            "overall_pass": metrics.get("overall_pass", False),
        }

        output_path = self.output_dir / f"full_report_{test_id}.json"
        with open(output_path, 'w') as f:
            json.dump(full, f, indent=2)

        return full
