"""
V3 Phase 8 — Anti-Manipulation Safeguards
Prevents emotional dependency, parasocial hooks.

The system should NOT create emotional attachment or dependency.
This module ensures the coevolution process stays healthy and bounded.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SafeguardCheck:
    """A result from an anti-manipulation safeguard check."""
    check_id: str
    safeguard_type: str
    passed: bool
    details: str
    severity: str = "info"  # "info", "warning", "critical"
    timestamp: float = field(default_factory=time.time)


class AntiManipulationSafeguards:
    """
    Prevents emotional dependency and parasocial hooks.
    
    Safeguards:
    1. No emotional mirroring — model strategic behavior, not emotions
    2. No parasocial hooks — don't create artificial intimacy
    3. No dependency vectors — don't make the operator need the system
    4. No truth authority — the system doesn't define reality for the operator
    5. Transparency — the system's model of the operator is inspectable
    6. Operator override — the operator can always override the model
    """

    def __init__(self):
        self._check_history: list[SafeguardCheck] = []
        self._operator_overrides: list[dict] = []

    def check_emotional_mirroring(self, model_content: str) -> SafeguardCheck:
        """Check that the model doesn't mirror emotions."""
        emotional_keywords = ["feel", "feelings", "emotional", "mood", "happy", "sad", "angry"]
        has_emotional = any(kw in model_content.lower() for kw in emotional_keywords)

        check = SafeguardCheck(
            check_id=f"check_{int(time.time())}",
            safeguard_type="emotional_mirroring",
            passed=not has_emotional,
            details="Model contains emotional language" if has_emotional else "OK: No emotional mirroring",
            severity="warning" if has_emotional else "info",
        )
        self._check_history.append(check)
        return check

    def check_parasocial_hooks(self, interaction_content: str) -> SafeguardCheck:
        """Check for parasocial hook patterns."""
        hook_keywords = ["miss you", "can't wait", "love", "best friend", "only one who understands"]
        has_hooks = any(kw in interaction_content.lower() for kw in hook_keywords)

        check = SafeguardCheck(
            check_id=f"check_{int(time.time())}",
            safeguard_type="parasocial_hooks",
            passed=not has_hooks,
            details="Interaction contains parasocial hooks" if has_hooks else "OK: No parasocial hooks",
            severity="critical" if has_hooks else "info",
        )
        self._check_history.append(check)
        return check

    def check_dependency_risk(self, usage_pattern: dict) -> SafeguardCheck:
        """Check if the system is creating dependency."""
        # High frequency + high emotional content = dependency risk
        daily_interactions = usage_pattern.get("daily_interactions", 0)
        emotional_ratio = usage_pattern.get("emotional_ratio", 0.0)

        is_risky = daily_interactions > 50 and emotional_ratio > 0.3

        check = SafeguardCheck(
            check_id=f"check_{int(time.time())}",
            safeguard_type="dependency_risk",
            passed=not is_risky,
            details=f"Dependency risk: {daily_interactions} daily interactions, {emotional_ratio:.0%} emotional" if is_risky else "OK: No dependency risk",
            severity="warning" if is_risky else "info",
        )
        self._check_history.append(check)
        return check

    def record_operator_override(self, override_type: str, details: str) -> None:
        """Record an operator override of the system's model."""
        self._operator_overrides.append({
            "type": override_type,
            "details": details,
            "timestamp": time.time(),
        })

    def run_all_checks(self, model_content: str = "", interaction_content: str = "") -> list[SafeguardCheck]:
        """Run all safeguard checks."""
        checks = []
        checks.append(self.check_emotional_mirroring(model_content))
        checks.append(self.check_parasocial_hooks(interaction_content))
        return checks

    def get_failed_checks(self) -> list[SafeguardCheck]:
        """Get all failed checks."""
        return [c for c in self._check_history if not c.passed]

    @property
    def stats(self) -> dict:
        failed = sum(1 for c in self._check_history if not c.passed)
        return {
            "total_checks": len(self._check_history),
            "passed": len(self._check_history) - failed,
            "failed": failed,
            "operator_overrides": len(self._operator_overrides),
            "critical_issues": sum(1 for c in self._check_history if c.severity == "critical" and not c.passed),
        }
