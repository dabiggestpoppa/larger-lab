"""G5 — ONE shared domain epistemic policy (S14–S19).

G5_DOMAIN_EPISTEMIC_POLICY drives the primary dispositions of the six CLASS C
scenarios from GENERIC domain dimensions only:

  domain, claim_type, authority_class, data_availability, data_quality,
  pit_integrity, execution_realism, cost_sensitivity, oos_status,
  mechanism_status, independence_status, source_disagreement, sensor_resolution,
  domain_transfer_status, manual_authority, reproduction_quality,
  validation_gate_state, economic_value_class, AffectedSurface,
  validation_gate_state.

Hard rules:
  * NO scenario ids, NO literal strategy/provider/concept names, NO expected
    outcomes (static guards test this).
  * Deterministic first-match per rule kind in declared order.
  * PROVISIONAL_SCENARIO_TEST_POLICY — never constitutional truth; dispositions
    are TEST-ONLY labels mapped onto existing M4/M5 semantics.
  * PnL may change RESEARCH PRIORITY only; it can never weaken B7 gates,
    PIT/execution realism, OOS/WF requirements, evidence independence,
    authority, manual doctrine or source semantics.
  * When a policy is required and NO rule matches, the disposition is
    POLICY_HOLD — a factual classification never authorizes institutional
    action by itself (G5-P0-A discipline carried forward).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex

G5_RULE_KINDS = ("claim_disposition", "transfer", "doctrine", "source_disagreement",
                 "availability", "research_priority")

KNOWN_G5_FIELDS = {
    "domain", "claim_type", "authority_class", "data_availability", "data_quality",
    "pit_integrity", "execution_realism", "cost_sensitivity", "oos_status",
    "mechanism_status", "independence_status", "source_disagreement",
    "sensor_resolution", "domain_transfer_status", "manual_authority",
    "reproduction_quality", "validation_gate_state", "economic_value_class",
    "affected_surface", "validation_gate_terminal", "protocol_frozen",
    "hypothesis_status", "suppression_state",
    "contradiction_present", "target_data_availability", "diagnosis_complete",
    "sensor_verified", "pit_integrity", "execution_realism",
}

# TEST-ONLY dispositions the policy may yield (no new constitutional states)
KNOWN_DISPOSITIONS = {
    "VALIDATION_REQUIRED", "REJECTED_NEGATIVE_KNOWLEDGE", "UNRESOLVED_PATTERN",
    "ONTOLOGY_EXPLORATION_CANDIDATE", "CONTRADICTION_OPEN", "MANUAL_PRESERVED",
    "SOURCE_DIAGNOSTIC_REQUIRED", "SOURCE_DISAGREEMENT_PRESERVED", "DATA_BLOCKED",
    "TRANSFER_HYPOTHESIS_ONLY", "DOMAIN_VALIDATION_REQUIRED", "DOMAIN_VALIDATED",
    "ANALOGY_ONLY", "TRANSFER_REJECTED", "REPRODUCTION_REJECTED",
    "PRIORITY_HIGH", "PRIORITY_NORMAL", "PRIORITY_LOW", "POLICY_HOLD",
    "REOPEN_CANDIDATE", "CONTINUE_SUPPRESSION", "STOP_SUPPRESSION",
}


class G5PolicyError(ValueError):
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
            elif op == "neq":
                if value == target:
                    return False
            else:
                raise G5PolicyError(f"unknown condition op {op!r}")
        return True
    return bool(value == cond)


@dataclass(frozen=True)
class G5Rule:
    rule_id: str
    kind: str
    when: Mapping[str, Any]
    then: Mapping[str, Any]
    rationale: str = ""

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> "G5Rule":
        kind = str(data.get("kind", ""))
        if kind not in G5_RULE_KINDS:
            raise G5PolicyError(f"rule {data.get('rule_id', '?')}: unknown kind {kind!r}")
        when = dict(data.get("when", {}))
        unknown = set(when) - KNOWN_G5_FIELDS
        if unknown:
            raise G5PolicyError(
                f"rule {data.get('rule_id', '?')}: conditions on non-generic "
                f"fields {sorted(unknown)}")
        then = dict(data.get("then", {}))
        disp = str(then.get("disposition", then.get("outcome", then.get("next_action", ""))))
        if disp and disp not in KNOWN_DISPOSITIONS:
            raise G5PolicyError(
                f"rule {data.get('rule_id', '?')}: unknown disposition {disp!r}")
        return cls(rule_id=str(data["rule_id"]), kind=kind, when=when, then=then,
                   rationale=str(data.get("rationale", "")))


@dataclass(frozen=True)
class G5DomainPolicy:
    policy_id: str
    version_tag: str = "V1"
    status: str = "PROVISIONAL_SCENARIO_TEST_POLICY"
    authority_basis: str = ""
    rules: Tuple[G5Rule, ...] = ()

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> "G5DomainPolicy":
        return cls(policy_id=str(data["policy_id"]),
                   version_tag=str(data.get("version_tag", "V1")),
                   status=str(data.get("status", "PROVISIONAL_SCENARIO_TEST_POLICY")),
                   authority_basis=str(data.get("authority_basis", "")),
                   rules=tuple(G5Rule.from_data(r) for r in data.get("rules", [])))

    def to_dict(self) -> Dict[str, Any]:
        return {"policy_id": self.policy_id, "version_tag": self.version_tag,
                "status": self.status, "authority_basis": self.authority_basis,
                "rules": [{"rule_id": r.rule_id, "kind": r.kind, "when": dict(r.when),
                           "then": dict(r.then), "rationale": r.rationale}
                          for r in self.rules]}

    def fingerprint(self) -> str:
        return deterministic_hex("g5_policy", self.policy_id, self.version_tag,
                                 self.to_dict(), length=24)

    def evaluate(self, facts: Mapping[str, Any], kind: str) -> Optional[G5Rule]:
        for rule in self.rules:
            if rule.kind != kind:
                continue
            if all(_cond_ok(cond, facts.get(field)) for field, cond in rule.when.items()):
                return rule
        return None


def g5_policy_outcome(policy: G5DomainPolicy, facts: Mapping[str, Any], kind: str,
                      fallback: str = "POLICY_HOLD") -> Dict[str, Any]:
    """Resolve the shared G5 policy's disposition for a governed decision.
    G5-P0-A: when no rule matches the decision is POLICY_HOLD — the factual
    classification (fallback) never authorizes action by itself."""
    rule = policy.evaluate(facts, kind)
    if rule is None:
        return {"disposition": "POLICY_HOLD", "rule_id": "", "governed": False,
                "rationale": "no shared G5 policy rule matched; governed disposition HELD",
                "factual": fallback}
    disp = str(rule.then.get("disposition", rule.then.get("outcome",
                                                          rule.then.get("next_action", fallback))))
    return {"disposition": disp, "rule_id": rule.rule_id, "governed": True,
            "rationale": rule.rationale, "factual": fallback}