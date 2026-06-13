"""
Phase 1.7.1 — Self Evaluation Engine

System continuously evaluates itself: strengths, weaknesses,
failure rates, domain confidence.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger("oce.evolution")


@dataclass
class DomainConfidence:
    """Confidence score for a knowledge domain."""
    domain: str
    confidence: float = 0.5  # 0-1
    source_count: int = 0
    last_updated: str = ""
    failure_count: int = 0
    success_count: int = 0

    @property
    def accuracy(self) -> float:
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.5
        return self.success_count / total


@dataclass
class SelfEvaluationReport:
    """Complete self-evaluation report."""
    timestamp: str = ""
    overall_confidence: float = 0.5
    domain_scores: Dict[str, DomainConfidence] = field(default_factory=dict)
    weak_domains: List[str] = field(default_factory=list)
    strong_domains: List[str] = field(default_factory=list)
    failure_patterns: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class SelfEvaluationEngine:
    """
    System continuously evaluates itself.
    
    Questions OCE asks itself:
    - What am I weak at?
    - Where do I hallucinate most?
    - What domains have shallow knowledge?
    - What workflows fail often?
    - Which agents perform poorly?
    """

    def __init__(self):
        self._domain_scores: Dict[str, DomainConfidence] = {}
        self._failure_log: List[Dict[str, Any]] = []
        self._success_log: List[Dict[str, Any]] = []

    def record_success(self, domain: str, task_type: str = ""):
        """Record a successful task completion."""
        if domain not in self._domain_scores:
            self._domain_scores[domain] = DomainConfidence(domain=domain)
        self._domain_scores[domain].success_count += 1
        self._domain_scores[domain].confidence = min(1.0, self._domain_scores[domain].confidence + 0.05)
        self._success_log.append({"domain": domain, "task_type": task_type})

    def record_failure(self, domain: str, task_type: str = "", error: str = ""):
        """Record a task failure."""
        if domain not in self._domain_scores:
            self._domain_scores[domain] = DomainConfidence(domain=domain)
        self._domain_scores[domain].failure_count += 1
        self._domain_scores[domain].confidence = max(0.0, self._domain_scores[domain].confidence - 0.1)
        self._failure_log.append({"domain": domain, "task_type": task_type, "error": error})

    def evaluate(self) -> SelfEvaluationReport:
        """Generate a complete self-evaluation report."""
        from datetime import datetime, timezone

        report = SelfEvaluationReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Domain scores
        report.domain_scores = dict(self._domain_scores)

        # Identify weak and strong domains
        for domain, score in self._domain_scores.items():
            if score.confidence < 0.4:
                report.weak_domains.append(domain)
            elif score.confidence > 0.7:
                report.strong_domains.append(domain)

        # Overall confidence
        if self._domain_scores:
            report.overall_confidence = sum(
                s.confidence for s in self._domain_scores.values()
            ) / len(self._domain_scores)

        # Failure patterns
        failure_domains: Dict[str, int] = {}
        for f in self._failure_log[-50:]:  # Last 50 failures
            d = f.get("domain", "unknown")
            failure_domains[d] = failure_domains.get(d, 0) + 1
        for domain, count in sorted(failure_domains.items(), key=lambda x: -x[1])[:5]:
            report.failure_patterns.append(f"{domain}: {count} recent failures")

        # Recommendations
        for domain in report.weak_domains:
            report.recommendations.append(f"Strengthen {domain} knowledge through targeted research")
        if len(report.weak_domains) > len(report.strong_domains):
            report.recommendations.append("Overall knowledge base needs expansion — increase ingestion frequency")

        logger.info(
            f"Self-evaluation: {len(report.strong_domains)} strong, "
            f"{len(report.weak_domains)} weak domains, "
            f"overall confidence={report.overall_confidence:.2f}"
        )

        return report

    def get_weak_domains(self, threshold: float = 0.4) -> List[str]:
        """Get domains below confidence threshold."""
        return [
            domain for domain, score in self._domain_scores.items()
            if score.confidence < threshold
        ]

    def get_strong_domains(self, threshold: float = 0.7) -> List[str]:
        """Get domains above confidence threshold."""
        return [
            domain for domain, score in self._domain_scores.items()
            if score.confidence >= threshold
        ]
