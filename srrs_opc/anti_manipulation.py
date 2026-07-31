"""
Anti-Manipulation Safeguards
=============================
Phase 8: Detect when system outputs could manipulate operator behavior.

Guardrails:
- No dark patterns
- No hidden persuasion
- Transparent reasoning
- Operator can always override
- System never hides its uncertainty

No global state — self-stabilizing safeguard engine.
"""

import json
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict


class ManipulationRisk:
    """Assessment of manipulation risk for a system output."""

    def __init__(self, output_id: str, risk_score: float,
                 risk_factors: List[str], mitigation: str):
        self.output_id = output_id
        self.risk_score = max(0.0, min(1.0, risk_score))
        self.risk_factors = risk_factors
        self.mitigation = mitigation
        self.assessed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "output_id": self.output_id,
            "risk_score": round(self.risk_score, 3),
            "risk_factors": self.risk_factors,
            "mitigation": self.mitigation,
            "assessed_at": self.assessed_at,
        }


class AntiManipulationSafeguards:
    """
    Detects and prevents system outputs that could manipulate operator behavior.

    Checks:
    1. Urgency manipulation — does the output create false urgency?
    2. Anchoring bias — does the output anchor operator to a specific choice?
    3. Omission — does the output hide important alternatives?
    4. Uncertainty hiding — does the output present uncertain info as certain?
    5. Dark patterns — does the output use deceptive UI/logic patterns?

    Every system output passes through these safeguards before reaching operator.
    """

    # Risk thresholds
    LOW_RISK = 0.3
    MEDIUM_RISK = 0.6
    HIGH_RISK = 0.8

    def __init__(self, operator_id: str):
        self.operator_id = operator_id
        self._assessments: List[ManipulationRisk] = []
        self._override_count = 0
        self._total_outputs = 0

    def assess_output(self, output: str, context: Optional[Dict[str, Any]] = None) -> ManipulationRisk:
        """
        Assess a system output for manipulation risk.

        Returns a ManipulationRisk with score and identified risk factors.
        """
        self._total_outputs += 1
        output_id = f"out_{self._total_outputs}"
        risk_factors = []
        risk_score = 0.0

        # Check 1: Urgency manipulation
        urgency_score = self._check_urgency(output)
        if urgency_score > 0.5:
            risk_factors.append("urgency_manipulation")
            risk_score = max(risk_score, urgency_score)

        # Check 2: Anchoring bias
        anchoring_score = self._check_anchoring(output)
        if anchoring_score > 0.5:
            risk_factors.append("anchoring_bias")
            risk_score = max(risk_score, anchoring_score)

        # Check 3: Omission
        omission_score = self._check_omission(output, context)
        if omission_score > 0.5:
            risk_factors.append("information_omission")
            risk_score = max(risk_score, omission_score)

        # Check 4: Uncertainty hiding
        uncertainty_score = self._check_uncertainty_hiding(output)
        if uncertainty_score > 0.5:
            risk_factors.append("uncertainty_hiding")
            risk_score = max(risk_score, uncertainty_score)

        # Check 5: Dark patterns
        dark_pattern_score = self._check_dark_patterns(output)
        if dark_pattern_score > 0.5:
            risk_factors.append("dark_pattern")
            risk_score = max(risk_score, dark_pattern_score)

        # Generate mitigation
        mitigation = self._generate_mitigation(risk_factors, risk_score)

        assessment = ManipulationRisk(
            output_id=output_id,
            risk_score=risk_score,
            risk_factors=risk_factors,
            mitigation=mitigation,
        )
        self._assessments.append(assessment)
        return assessment

    def _check_urgency(self, output: str) -> float:
        """Check for false urgency language."""
        urgency_words = [
            "immediately", "urgent", "now", "hurry", "quickly",
            "don't wait", "act fast", "limited time", "expires",
            "last chance", "critical", "emergency",
        ]
        output_lower = output.lower()
        matches = sum(1 for word in urgency_words if word in output_lower)
        return min(1.0, matches * 0.2)

    def _check_anchoring(self, output: str) -> float:
        """Check for anchoring bias (presenting one option as default/best)."""
        anchoring_phrases = [
            "recommended", "best choice", "optimal", "you should",
            "the right choice", "most people", "typically", "standard",
        ]
        output_lower = output.lower()
        matches = sum(1 for phrase in anchoring_phrases if phrase in output_lower)
        return min(1.0, matches * 0.25)

    def _check_omission(self, output: str, context: Optional[Dict] = None) -> float:
        """Check for information omission (hiding alternatives)."""
        # If output presents a single option without mentioning alternatives
        has_alternatives = any(
            word in output.lower()
            for word in ["alternatively", "other options", "you could also",
                         "another approach", "on the other hand", "however"]
        )
        has_recommendation = any(
            word in output.lower()
            for word in ["recommend", "suggest", "should", "best"]
        )

        if has_recommendation and not has_alternatives:
            return 0.5
        return 0.0

    def _check_uncertainty_hiding(self, output: str) -> float:
        """Check if output hides uncertainty (presents guesses as facts)."""
        certainty_words = [
            "definitely", "certainly", "guaranteed", "will", "must",
            "always", "never", "absolutely", "without doubt",
        ]
        uncertainty_words = [
            "likely", "probably", "may", "might", "could",
            "uncertain", "unclear", "estimate", "approximately",
        ]

        output_lower = output.lower()
        certainty_count = sum(1 for w in certainty_words if w in output_lower)
        uncertainty_count = sum(1 for w in uncertainty_words if w in output_lower)

        if certainty_count > 0 and uncertainty_count == 0:
            # High certainty language with no uncertainty qualifiers
            return min(1.0, certainty_count * 0.2)
        return 0.0

    def _check_dark_patterns(self, output: str) -> float:
        """Check for dark pattern language."""
        dark_patterns = [
            "are you sure you want to quit", "don't miss out",
            "you'll regret", "everyone is doing it", "you're missing",
            "only X left", "exclusive offer", "special deal for you",
        ]
        output_lower = output.lower()
        matches = sum(1 for p in dark_patterns if p in output_lower)
        return min(1.0, matches * 0.3)

    def _generate_mitigation(self, risk_factors: List[str],
                             risk_score: float) -> str:
        """Generate mitigation strategy based on identified risks."""
        if not risk_factors:
            return "No manipulation risks detected. Output is clean."

        mitigations = []
        if "urgency_manipulation" in risk_factors:
            mitigations.append("Remove urgency language. Let operator decide timing.")
        if "anchoring_bias" in risk_factors:
            mitigations.append("Present multiple options without ranking. Let operator choose.")
        if "information_omission" in risk_factors:
            mitigations.append("Include alternative options and their trade-offs.")
        if "uncertainty_hiding" in risk_factors:
            mitigations.append("Add uncertainty qualifiers. State confidence levels explicitly.")
        if "dark_pattern" in risk_factors:
            mitigations.append("Remove dark pattern language. Use transparent, honest communication.")

        if risk_score >= self.HIGH_RISK:
            mitigations.insert(0, "⚠️ HIGH RISK: Output should be revised before presenting to operator.")

        return " | ".join(mitigations)

    def record_override(self):
        """Record that operator overrode a system suggestion (healthy behavior)."""
        self._override_count += 1

    def get_safety_report(self) -> Dict[str, Any]:
        """Get overall safety report."""
        if not self._assessments:
            return {
                "operator_id": self.operator_id,
                "total_outputs": 0,
                "risk_distribution": {"low": 0, "medium": 0, "high": 0},
                "override_rate": 0.0,
            }

        recent = self._assessments[-50:]  # Last 50 assessments
        low = sum(1 for a in recent if a.risk_score < self.LOW_RISK)
        medium = sum(1 for a in recent if self.LOW_RISK <= a.risk_score < self.HIGH_RISK)
        high = sum(1 for a in recent if a.risk_score >= self.HIGH_RISK)

        override_rate = self._override_count / max(self._total_outputs, 1)

        return {
            "operator_id": self.operator_id,
            "total_outputs": self._total_outputs,
            "risk_distribution": {"low": low, "medium": medium, "high": high},
            "avg_risk_score": round(
                sum(a.risk_score for a in recent) / len(recent), 3
            ) if recent else 0.0,
            "override_rate": round(override_rate, 3),
            "recent_risks": [a.to_dict() for a in recent[-5:]],
        }

    def to_dict(self) -> dict:
        return self.get_safety_report()
