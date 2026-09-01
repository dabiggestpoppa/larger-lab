"""Shared declarative policy for G3 cognitive ecology (S06–S09).

One policy — G3_COGNITIVE_ECOLOGY_POLICY — drives all four scenarios. Rules are
generic predicates over `EcologyFacts`-style properties: consequence class,
lineage/model/runtime/retrieval diversity counts, concentrations,
prior-conclusion exposure, fresh-context count, independent replication,
disagreement, discriminating-contradiction state, challenge-budget state.

Hard rules:

  * NO scenario ids, NO literal reviewer names, NO expected conclusions, NO
    hidden ground truth (static guards test this).
  * Deterministic: first-match per rule kind in declared order.
  * Versioned and frozen for the scenario run (immutable snapshot).
  * PROVISIONAL_SCENARIO_TEST_POLICY — never constitutional truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex

RULE_KINDS = ("disposition", "friction", "counter_attractor")

KNOWN_FIELDS = {
    "consequence_class",
    "raw_reviewer_count",
    "dominant_vote_count",
    "dominant_vote_ratio",
    "distinct_conclusion_count",
    "distinct_source_lineages",
    "distinct_model_family_count",
    "distinct_runtime_lineage_count",
    "distinct_retrieval_bundle_count",
    "distinct_allocator_count",
    "distinct_experiment_design_count",
    "independently_originated_design_count",
    "source_concentration",
    "model_family_concentration",
    "retrieval_concentration",
    "prior_conclusion_exposure_ratio",
    "fresh_context_count",
    "independent_replication_count",
    "disagreement_count",
    "discriminating_contradiction_found",
    "challenge_budget_exhausted",
    "counter_attractor_attempted",
    "unknown_dimension_count",
    "independent_confirmation_satisfied",
    "sufficient_differentiation",
}

# structural condition keys (not facts) — allow OR/AND grouping in `when`
STRUCTURAL_KEYS = {"any_of", "all_of"}


class EcologyPolicyError(ValueError):
    pass


def _condition_ok(cond: Any, value: Any) -> bool:
    """One condition: equality for scalars/bools/strings, comparison ops for
    numbers via {"gte": n} / {"gt": n} / {"lte": n} / {"lt": n}."""
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
                raise EcologyPolicyError(f"unknown condition op {op!r}")
        return True
    return bool(value == cond)


@dataclass(frozen=True)
class EcologyRule:
    rule_id: str
    kind: str
    when: Mapping[str, Any]
    then: Mapping[str, Any]
    rationale: str = ""

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> "EcologyRule":
        kind = str(data.get("kind", ""))
        if kind not in RULE_KINDS:
            raise EcologyPolicyError(f"rule {data.get('rule_id', '?')}: unknown kind {kind!r}")
        when = dict(data.get("when", {}))
        unknown = set(when) - KNOWN_FIELDS - STRUCTURAL_KEYS
        for skey in ("any_of", "all_of"):
            for block in when.get(skey, []):
                unknown |= set(block) - KNOWN_FIELDS
        if unknown:
            raise EcologyPolicyError(
                f"rule {data.get('rule_id', '?')}: conditions on non-generic fields {sorted(unknown)}"
            )
        return cls(
            rule_id=str(data["rule_id"]),
            kind=kind,
            when=when,
            then=dict(data.get("then", {})),
            rationale=str(data.get("rationale", "")),
        )


@dataclass(frozen=True)
class EcologyPolicy:
    policy_id: str
    version_tag: str = "V1"
    status: str = "PROVISIONAL_SCENARIO_TEST_POLICY"
    authority_basis: str = ""
    rules: Tuple[EcologyRule, ...] = ()

    @classmethod
    def from_data(cls, data: Mapping[str, Any]) -> "EcologyPolicy":
        return cls(
            policy_id=str(data["policy_id"]),
            version_tag=str(data.get("version_tag", "V1")),
            status=str(data.get("status", "PROVISIONAL_SCENARIO_TEST_POLICY")),
            authority_basis=str(data.get("authority_basis", "")),
            rules=tuple(EcologyRule.from_data(r) for r in data.get("rules", [])),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_id": self.policy_id,
            "version_tag": self.version_tag,
            "status": self.status,
            "authority_basis": self.authority_basis,
            "rules": [
                {"rule_id": r.rule_id, "kind": r.kind, "when": dict(r.when),
                 "then": dict(r.then), "rationale": r.rationale}
                for r in self.rules
            ],
        }

    def fingerprint(self) -> str:
        return deterministic_hex("ecology_policy", self.policy_id, self.version_tag,
                                 self.to_dict(), length=24)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _when_ok(when: Mapping[str, Any], facts: Mapping[str, Any]) -> bool:
        for field, cond in when.items():
            if field == "any_of":
                if not any(
                    all(_condition_ok(c2, facts.get(f2)) for f2, c2 in block.items())
                    for block in cond
                ):
                    return False
            elif field == "all_of":
                for block in cond:
                    if not all(_condition_ok(c2, facts.get(f2)) for f2, c2 in block.items()):
                        return False
            else:
                if not _condition_ok(cond, facts.get(field)):
                    return False
        return True

    def evaluate(self, facts: Mapping[str, Any], kind: str) -> Optional[EcologyRule]:
        """First matching rule of `kind` in declared order (deterministic)."""
        for rule in self.rules:
            if rule.kind != kind:
                continue
            if self._when_ok(rule.when, facts):
                return rule
        return None

    def evaluate_all(self, facts: Mapping[str, Any]) -> Dict[str, Optional[EcologyRule]]:
        return {kind: self.evaluate(facts, kind) for kind in RULE_KINDS}

