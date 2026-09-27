"""G4 — ONE shared memory/reactivation policy (S10–S13).

G4_MEMORY_AND_REACTIVATION_POLICY drives reopen eligibility, activation routing
and suppression disposition across all four scenarios from GENERIC memory
dimensions only: lifecycle state, memory tier, reopen-condition state, blocker
state, evidence freshness, task relevance, dependency refs, authority status,
current epoch, retrieval/context budget.

Hard rules:
  * NO scenario ids, NO literal knowledge names, NO expected outcomes (static
    guards test this).
  * Deterministic first-match per rule kind in declared order.
  * PROVISIONAL_SCENARIO_TEST_POLICY — never constitutional truth.
  * Memory policy never changes authority / never makes NegativeKnowledge
    permanent / never promotes CANDIDATE directly to ACTIVE.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex

MEMORY_RULE_KINDS = ("reopen", "activation", "suppression")

KNOWN_MEMORY_FIELDS = {
    "lifecycle_state", "memory_tier", "reopen_condition_state",
    "evidence_fresh", "task_relevance", "dependency_centrality",
    "blocker_resolved", "authority_required", "permanent_operator_authority",
    "current_epoch", "retrieval_budget_used", "context_budget",
    "history_size", "suppression_state", "reopen_candidate",
}


class MemoryPolicyError(ValueError):
    pass


def _cond_ok(cond: Any, value: Any) -> bool:
    if isinstance(cond, dict):
        for op, target in cond.items():
            if op == "gte":
                if not (isinstance(value, (int, float)) and value >= target):
                    return False
            elif op == "gt":
                if not (isinstance(value, (int, float)) and value > target):
                    return False
            elif op == "lte":
                if not (isinstance(value, (int, float)) and value <= target):
                    return False
            elif op == "lt":
                if not (isinstance(value, (int, float)) and value < target):
                    return False
            elif op == "eq":
                if value != target:
                    return False
            elif op == "in":
                if value not in target:
                    return False
            else:
                raise MemoryPolicyError(f"unknown condition op {op!r}")
        return True
    return bool(value == cond)


@dataclass(frozen=True)
class MemoryRule:
    rule_id: str
    kind: str
    when: Mapping[str, Any]
    then: Mapping[str, Any]
    rationale: str = ""

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> "MemoryRule":
        kind = str(data.get("kind", ""))
        if kind not in MEMORY_RULE_KINDS:
            raise MemoryPolicyError(f"rule {data.get('rule_id', '?')}: unknown kind {kind!r}")
        when = dict(data.get("when", {}))
        unknown = set(when) - KNOWN_MEMORY_FIELDS
        if unknown:
            raise MemoryPolicyError(
                f"rule {data.get('rule_id', '?')}: conditions on non-generic fields {sorted(unknown)}")
        return cls(rule_id=str(data["rule_id"]), kind=kind, when=when,
                   then=dict(data.get("then", {})), rationale=str(data.get("rationale", "")))


@dataclass(frozen=True)
class MemoryPolicy:
    policy_id: str
    version_tag: str = "V1"
    status: str = "PROVISIONAL_SCENARIO_TEST_POLICY"
    authority_basis: str = ""
    rules: Tuple[MemoryRule, ...] = ()

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> "MemoryPolicy":
        return cls(
            policy_id=str(data["policy_id"]),
            version_tag=str(data.get("version_tag", "V1")),
            status=str(data.get("status", "PROVISIONAL_SCENARIO_TEST_POLICY")),
            authority_basis=str(data.get("authority_basis", "")),
            rules=tuple(MemoryRule.from_data(r) for r in data.get("rules", [])),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {"policy_id": self.policy_id, "version_tag": self.version_tag,
                "status": self.status, "authority_basis": self.authority_basis,
                "rules": [{"rule_id": r.rule_id, "kind": r.kind, "when": dict(r.when),
                           "then": dict(r.then), "rationale": r.rationale}
                          for r in self.rules]}

    def fingerprint(self) -> str:
        return deterministic_hex("memory_policy", self.policy_id, self.version_tag,
                                 self.to_dict(), length=24)

    def evaluate(self, facts: Mapping[str, Any], kind: str) -> Optional[MemoryRule]:
        for rule in self.rules:
            if rule.kind != kind:
                continue
            if all(_cond_ok(cond, facts.get(field)) for field, cond in rule.when.items()):
                return rule
        return None
