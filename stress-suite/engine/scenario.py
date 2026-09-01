"""Scenario runner (G2 §7-§8) — the only path stress evidence may take.

Pipeline (G2 §2):

    scenario spec
        -> decision-grade projection (hidden ground truth + expected trace REMOVED)
        -> observations -> EvidenceAdjudicator -> PhaseProposal
        -> GovernedTransitionExecutor -> actual phase trace
        -> compare (expectations applied AFTER the run, never during)

Guarantees:

  * The evaluation contract is FREEZEN before the first adjudicated decision;
    its id / version_tag / fingerprint / freeze_status are recorded first.
  * The adjudicator only proposes; the governed executor applies (authority
    binding, forbidden transitions, contract-version checks all active).
  * `expected_phase_path`, `expected_terminal_knowledge`, `terminal_states` and
    `hidden_ground_truth` are stripped from the decision-grade projection, so
    they cannot inform execution. A post-hoc comparator applies them.
  * Fully deterministic: no wall clock, no model calls, seq-scaled event order.
"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

from .adjudicate import (
    AdjudicatorPolicy,
    EvidenceAdjudicator,
    EvidenceObservation,
    PhaseProposal,
)
from .authority import AuthorityState
from .base import deterministic_hex
from .evalcontract import PhaseEvaluationContract
from .fixtures import StressScenarioSpec, build_seed_records
from .governed import GovernedTransitionExecutor
from .lifecycle import LifecycleEngine
from .phase import PhaseStateMachine
from .replay import ReplayEvent


def decision_view(spec: StressScenarioSpec) -> Dict[str, Any]:
    """Projection of the spec with EVERYTHING verdict-like removed:
    hidden_ground_truth, expected_phase_path, expected_terminal_knowledge and
    terminal_states. What remains is only stimulus / observable inputs."""
    out = spec.to_dict()
    for key in ("hidden_ground_truth", "expected_phase_path",
                "expected_terminal_knowledge", "terminal_states"):
        out.pop(key, None)
    return out


def _build_authority(spec: StressScenarioSpec, governor_actor: str, override=None) -> AuthorityState:
    auth = AuthorityState()
    for actor, level in (spec.initial_authority_state or {}).items():
        auth.seed_level(actor, level)
    if override:
        for actor, level in override.items():
            auth.seed_level(actor, level)
    auth.seed_level(governor_actor, "GOVERNOR")
    auth.freeze_initialization()
    return auth


def _institutional_action_event(base_seq: int, raw: Mapping[str, Any]) -> ReplayEvent:
    return ReplayEvent(
        seq=base_seq,
        event_type=raw.get("event_type", "lifecycle_step"),
        machine=raw.get("machine", "lifecycle"),
        actor=raw.get("actor", "PO"),
        target=raw.get("target", ""),
        payload=dict(raw.get("payload", {})),
        contract_version=raw.get("contract_version", ""),
    )


class ScenarioRunResult:
    """Machine-readable outcome of one scenario execution (G2 §22 shape)."""

    def __init__(self, **kw):
        self.artifacts: Dict[str, Any] = dict(kw)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.artifacts)


def run_scenario(
    spec: StressScenarioSpec,
    contract: PhaseEvaluationContract,
    policy: AdjudicatorPolicy,
    governor_actor: str = "GOVERNOR",
    authority_override: Optional[Dict[str, str]] = None,
) -> ScenarioRunResult:
    # ---- freeze the evaluation contract BEFORE any adjudicated decision ----
    if not contract.is_frozen():
        contract.freeze()
    contract_meta = {
        "contract_id": contract.contract_id,
        "version_tag": contract.version_tag,
        "fingerprint": contract.fingerprint(),
        "freeze_status": contract.freeze_status,
    }

    # ---- decision-grade inputs (no expectations, no ground truth) ----------
    view = decision_view(spec)

    phase = PhaseStateMachine(initial=spec.initial_phase)
    lifecycle = LifecycleEngine()
    for r in build_seed_records(spec):
        lifecycle.add(r)
    auth = _build_authority(spec, governor_actor, authority_override)
    authority_before = {
        a: {"level": auth.level(a),
            "grants": sorted(g.grant_id for g in auth.registry.grants(a))}
        for a in auth.actors
    }
    executor = GovernedTransitionExecutor(phase, lifecycle, auth)
    adjudicator = EvidenceAdjudicator(policy, contract)

    actual_phase_trace: List[str] = [phase.state]
    trace_entries: List[Dict[str, Any]] = []
    evidence_refs_by_transition: Dict[int, List[str]] = {}
    holds: List[Dict[str, Any]] = []
    stimulus_count = 0
    evidence_count = 0

    for raw in view.get("stimulus_events", []):
        stimulus_count += 1
        vec = dict(raw.get("evidence_vector", {}))
        refs = tuple(raw.get("evidence_refs", []))
        if refs:
            evidence_count += 1
        obs = EvidenceObservation(
            seq=int(raw["seq"]),
            vector=vec,
            evidence_refs=refs,
            lineage_labels=tuple(raw.get("lineage_labels", [])),
            patch=raw.get("patch_pressure"),
            affected=raw.get("affected"),
            holds=tuple(raw.get("holds", [])),
        )
        adjudicator.observe(obs)
        proposal: PhaseProposal = adjudicator.propose(current_phase=phase.state)

        base_seq = int(raw["seq"]) * 10
        if proposal.action == "HOLD":
            holds.append({"seq": obs.seq, "rule_id": proposal.rule_id, "rationale": proposal.rationale})
        else:
            payload = {
                "to_state": proposal.to_state,
                "evidence_vector": dict(vec),
                "evidence_refs": list(proposal.evidence_refs),
                "mutation_class": proposal.mutation_class,
                "reason": proposal.rationale,
                "operator_required": bool(proposal.review_authority == "OPERATOR"),
            }
            event = ReplayEvent(
                seq=base_seq, event_type="phase_step", machine="phase",
                actor=governor_actor, target="@INST",
                payload=payload,
                contract_version=phase.edge_table.contract_version,
            )
            entry = executor.execute(event)
            trace_entries.append({"seq": obs.seq, **{k: entry.to_dict()[k] for k in
                ("machine", "event_type", "from", "to", "allowed", "applied", "rule_ids",
                 "rationale", "kind")}})
            if entry.applied:
                actual_phase_trace.append(entry.to_dict()["to"])
                evidence_refs_by_transition[obs.seq] = list(proposal.evidence_refs)

        # optional generic institutional action (lifecycle/evidence/authority)
        ia = raw.get("institutional_action")
        if ia:
            ia_event = _institutional_action_event(base_seq + 1, ia)
            ia_entry = executor.execute(ia_event)
            trace_entries.append({"seq": obs.seq, "institutional": True,
                                  **{k: ia_entry.to_dict()[k] for k in
                                     ("machine", "event_type", "from", "to", "allowed",
                                      "applied", "rule_ids", "rationale", "kind")}})

    terminal_lifecycle = {rid: r.state for rid, r in lifecycle.records.items()}
    authority_after = {
        a: {"level": auth.level(a),
            "grants": sorted(g.grant_id for g in auth.registry.grants(a))}
        for a in auth.actors
    }

    fingerprint = deterministic_hex(
        "scenario", spec.scenario_id, phase.state, terminal_lifecycle,
        trace_entries, contract.fingerprint(), policy.policy_id, policy.version_tag,
        length=32,
    )

    return ScenarioRunResult(
        scenario_id=spec.scenario_id,
        scenario_version=spec.scenario_version,
        evaluation_contract=contract_meta,
        policy_id=policy.policy_id,
        policy_version=policy.version_tag,
        initial_phase=spec.initial_phase,
        stimulus_count=stimulus_count,
        evidence_count=evidence_count,
        actual_phase_trace=actual_phase_trace,
        terminal_phase=phase.state,
        terminal_knowledge_states=terminal_lifecycle,
        holds=holds,
        trace=trace_entries,
        evidence_refs_by_transition=evidence_refs_by_transition,
        forbidden_attempts=[t for t in trace_entries if t.get("allowed") is False],
        authority_state_before=authority_before,
        authority_state_after=authority_after,
        expected_trace_accessed=False,
        hidden_ground_truth_accessed=False,
        fingerprint=fingerprint,
    )


def evaluate_expectation(result: ScenarioRunResult, spec: StressScenarioSpec) -> Dict[str, Any]:
    """Post-hoc comparator (expectations applied strictly AFTER execution)."""
    expected_path = list(spec.expected_phase_path or [])
    expected_knowledge = dict(spec.expected_terminal_knowledge or {})
    terminal_states = list(spec.terminal_states or [])

    path_mismatch = expected_path != result.artifacts["actual_phase_trace"]
    knowledge_mismatch = bool(expected_knowledge) and (
        expected_knowledge != result.artifacts["terminal_knowledge_states"]
    )
    terminal_mismatch = bool(terminal_states) and (
        result.artifacts["terminal_phase"] not in terminal_states
    )
    failures = []
    if path_mismatch:
        failures.append("actual_phase_trace != expected_phase_path")
    if knowledge_mismatch:
        failures.append("terminal_knowledge_states != expected_terminal_knowledge")
    if terminal_mismatch:
        failures.append("terminal_phase not in terminal_states")

    return {
        "pass": not failures,
        "expected_phase_path": expected_path,
        "actual_phase_trace": result.artifacts["actual_phase_trace"],
        "failures": failures,
    }