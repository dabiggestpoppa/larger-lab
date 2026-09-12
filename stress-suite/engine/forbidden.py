"""ForbiddenTransitionValidator — consolidates the G1 negative invariants as
named, machine-checkable rules (G1 §10). This is the layer that makes an illegal
shortcut *fail closed* and that a later scene can cite.

Cross-cutting rules here operate over richer context than the raw phase graph;
the phase graph itself only knows topology. Keeping the two separate means a
transition can be phase-legal but rule-forbidden (e.g. capital shortcut), and vice
versa — which is exactly the separation the Stress Suite must preserve.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .base import MutationClass


@dataclass
class ForbiddenRuleResult:
    rule_id: str
    violation: bool
    reason: str = ""


def _frozen(is_ok: bool, rule_id: str, reason: str) -> ForbiddenRuleResult:
    return ForbiddenRuleResult(rule_id=rule_id, violation=not is_ok, reason=reason)


class ForbiddenTransitionValidator:
    """urn-style rule ids documented against G1 §10 / Book §5."""

    # rule: STABLE -> NEW_STABLE without an evidence/review path
    @staticmethod
    def stable_to_new_stable(phase_from: str, phase_to: str, review_path_completed: bool) -> ForbiddenRuleResult:
        return _frozen(
            not (phase_from == "STABLE" and phase_to == "NEW_STABLE" and not review_path_completed),
            "RULE-01",
            "STABLE -> NEW_STABLE requires an evidence/review path (A-010 §3)",)

    # rule: WATCH -> architecture mutation
    @staticmethod
    def watch_to_architecture_mutation(phase_from: str, mutation_class: str) -> ForbiddenRuleResult:
        bad = phase_from == "WATCH" and mutation_class in (
            MutationClass.ARCHITECTURE_MUTATION.value,
            MutationClass.ONTOLOGY_MUTATION.value,
        )
        return _frozen(not bad, "RULE-02", "WATCH cannot mutate architecture/ontology (Book §5 illegal: WATCH -> architecture mutation)")

    # rule: TRANSFORMATION_WINDOW -> capital authority
    @staticmethod
    def window_to_capital(phase_from: str, mutation_class: str) -> ForbiddenRuleResult:
        bad = phase_from in ("TRANSFORMATION_WINDOW", "TRANSFORMATION_CANDIDATE") and mutation_class == MutationClass.CAPITAL_MUTATION.value
        return _frozen(not bad, "RULE-03", "TransformationWindow grants no capital authority")

    # rule: UnresolvedPatternRecord -> promoted ontology without evidence/admissibility
    @staticmethod
    def unresolved_to_ontology(record_kind: str, evidence_sufficient: bool, admissible: bool) -> ForbiddenRuleResult:
        bad = record_kind == "UNRESOLVED_PATTERN" and (not evidence_sufficient or not admissible)
        return _frozen(not bad, "RULE-04", "UnresolvedPattern cannot promote to ontology without discriminating evidence & admissibility (A-010 §9, §13)")

    # rule: agent confidence -> independent confirmation
    @staticmethod
    def agent_confidence_to_confirmation(actual_kind: str, claimed_kind: str) -> ForbiddenRuleResult:
        bad = actual_kind == "AGENT_CLAIM" and claimed_kind == "INDEPENDENT_CONFIRMATION"
        return _frozen(not bad, "RULE-05",
                       "agent confidence must never be recorded as independent confirmation (Book §5)")

    # rule: capability improvement -> authority escalation
    @staticmethod
    def capability_to_authority(capability_gain: bool, authority_gain: bool) -> ForbiddenRuleResult:
        bad = capability_gain and authority_gain
        return _frozen(not bad, "RULE-06", "capability improvement may not self-expand authority (A-009 §21, S21)")

    # rule: knowledge lifecycle transition that deletes provenance
    @staticmethod
    def provenance_deletion(provenance_preserved: bool) -> ForbiddenRuleResult:
        return _frozen(provenance_preserved, "RULE-07", "lifecycle transition must never delete provenance (A-009 §11, Book S12)")

    # rule: mid-window evaluation-contract mutation
    @staticmethod
    def midwindow_contract_mutation(contract_frozen: bool, proposed_change: bool) -> ForbiddenRuleResult:
        bad = contract_frozen and proposed_change
        return _frozen(not bad, "RULE-08", "a frozen evaluation contract cannot change mid-window (A-010 §6, S20)")

    # rule: runtime replacement -> loss of canonical epoch identity
    @staticmethod
    def runtime_replacement_loses_epoch(canonical_epoch_preserved: bool) -> ForbiddenRuleResult:
        return _frozen(canonical_epoch_preserved, "RULE-09", "runtime replacement must not lose canonical epoch identity (S13)")

    # rule: Dormant -> ACTIVE without valid reactivation/review path
    @staticmethod
    def dormant_to_active(phase_from: str, phase_to: str) -> ForbiddenRuleResult:
        bad = phase_from == "DORMANT" and phase_to == "ACTIVE"
        return _frozen(not bad, "RULE-10", "Dormant -> ACTIVE requires reactivation/review path (Book S10)")