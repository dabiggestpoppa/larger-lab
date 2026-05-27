"""
O2-B2: TaskClassifier
======================
Determine task type (9 categories).

Extends O-1 TaskIntentAnalyzer with consensus-aware classification.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any


class TaskType(str, Enum):
    CODING = "coding"
    RESEARCH = "research"
    ARCHITECTURE = "architecture"
    REPAIR = "repair"
    DEBUGGING = "debugging"
    ORCHESTRATION = "orchestration"
    VISUALIZATION = "visualization"
    AUTOMATION = "automation"
    SYSTEM_ANALYSIS = "system_analysis"
    GENERAL = "general"


# Extended classification patterns (builds on O-1 TaskIntentAnalyzer)
PATTERNS: dict[str, list[str]] = {
    TaskType.CODING: [
        r"\b(code|implement|write|build|create|develop|function|class|module|api|endpoint)\b",
        r"\b(fix|bug|debug|patch|refactor|optimize|rewrite)\b",
        r"\b(test|unittest|pytest|jest|vitest)\b",
        r"\b(component|hook|store|service|controller)\b",
    ],
    TaskType.RESEARCH: [
        r"\b(research|analyze|investigate|study|explore|survey|review)\b",
        r"\b(what|how|why|when|compare|difference|explain)\b",
        r"\b(documentation|docs|readme|spec)\b",
        r"\b(find|search|look up|lookup)\b",
    ],
    TaskType.ARCHITECTURE: [
        r"\b(architecture|design|structure|pattern|system|infrastructure)\b",
        r"\b(plan|blueprint|roadmap|strategy|proposal)\b",
        r"\b(microservice|monolith|layer|component|module|service)\b",
        r"\b(database|schema|model|entity|relationship)\b",
    ],
    TaskType.REPAIR: [
        r"\b(repair|fix|recover|restore|heal|stabilize|resolve)\b",
        r"\b(broken|error|crash|fail|degrad|corrupt)\b",
        r"\b(restart|reboot|reset|clean|rebuild)\b",
        r"\b(issue|problem|incident|outage)\b",
    ],
    TaskType.DEBUGGING: [
        r"\b(debug|trace|log|stack|exception|error|issue|problem)\b",
        r"\b(why.*not|doesn'?t work|not working|fails?|broken)\b",
        r"\b(investigate|diagnose|inspect|troubleshoot)\b",
        r"\b(where|which|what).*\b(happen|occur|fail|error)\b",
    ],
    TaskType.ORCHESTRATION: [
        r"\b(orchestrate|coordinate|manage|schedule|spawn|delegate|assign)\b",
        r"\b(agent|worker|pipeline|workflow|process|task)\b",
        r"\b(parallel|concurrent|async|background|batch)\b",
        r"\b(team|crew|fleet|squad)\b",
    ],
    TaskType.VISUALIZATION: [
        r"\b(visualize|chart|graph|plot|display|render|dashboard)\b",
        r"\b(ui|interface|component|page|screen|view|panel)\b",
        r"\b(show|display|present|render|draw)\b",
        r"\b(map|topology|network|tree|flow)\b",
    ],
    TaskType.AUTOMATION: [
        r"\b(automate|script|cron|schedule|batch|trigger)\b",
        r"\b(deploy|release|publish|push|merge|ship)\b",
        r"\b(ci|cd|pipeline|build|lint|format)\b",
        r"\b(github|action|workflow|hook)\b",
    ],
    TaskType.SYSTEM_ANALYSIS: [
        r"\b(analyz|monitor|metric|performance|load|capacity|health)\b",
        r"\b(status|health|check|report|summary|overview)\b",
        r"\b(topology|entropy|continuity|field|observer)\b",
        r"\b(state|status|condition|situation)\b",
    ],
}


class TaskClassifier:
    """
    Classifies user input into one of 9 task types.

    Uses weighted keyword matching with confidence scoring.
    Designed for consensus — can produce signals from multiple
    classification strategies.
    """

    def classify(self, user_input: str) -> dict[str, Any]:
        """
        Classify user input into a task type.

        Returns:
            {
                "task_type": str,
                "confidence": float,
                "scores": dict[str, float],
                "matched_patterns": dict[str, list[str]],
            }
        """
        text = user_input.lower().strip()
        scores: dict[str, float] = {}
        matched: dict[str, list[str]] = {}

        for task_type, patterns in PATTERNS.items():
            type_score = 0.0
            type_matches: list[str] = []
            for pattern in patterns:
                found = re.findall(pattern, text, re.IGNORECASE)
                if found:
                    type_score += len(found) * 1.0
                    type_matches.extend(found)
            if type_score > 0:
                scores[task_type] = type_score
                matched[task_type] = type_matches

        if not scores:
            return {
                "task_type": TaskType.GENERAL,
                "confidence": 0.3,
                "scores": {},
                "matched_patterns": {},
            }

        # Normalize scores
        total = sum(scores.values())
        normalized = {k: v / total for k, v in scores.items()}

        best_type = max(normalized, key=normalized.get)
        confidence = normalized[best_type]

        return {
            "task_type": best_type,
            "confidence": round(confidence, 3),
            "scores": {k.value: round(v, 3) for k, v in normalized.items()},
            "matched_patterns": {k.value: v for k, v in matched.items()},
        }

    def classify_with_signals(
        self, user_input: str, context: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Produce multiple classification signals for consensus.

        Returns a list of signals from different classification strategies.
        """
        signals: list[dict[str, Any]] = []

        # Signal 1: Keyword-based classification
        keyword_result = self.classify(user_input)
        signals.append({
            "source": "keyword",
            "task_type": keyword_result["task_type"],
            "confidence": keyword_result["confidence"],
            "weight": 0.6,
        })

        # Signal 2: Context-aware classification
        if context:
            context_type = self._context_classify(context)
            if context_type:
                signals.append({
                    "source": "context",
                    "task_type": context_type["task_type"],
                    "confidence": context_type["confidence"],
                    "weight": 0.4,
                })

        return signals

    def _context_classify(
        self, context: dict[str, Any]
    ) -> dict[str, str | float] | None:
        """Classify based on session context."""
        last_domain = context.get("last_domain", "")
        if last_domain:
            return {"task_type": last_domain, "confidence": 0.5}
        return None
