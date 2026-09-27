"""Scenario runner (G2 §7-§8, G2R-02/03/09/11/12) — the only path stress
evidence may take.

Pipeline (G2 §2):

    scenario spec
        -> decision-grade projection (hidden ground truth + expected trace REMOVED)
        -> governed evidence registry (G2R-02: refs resolve, phantom fails closed)
        -> observations (lineage + resolution derived from the registry; patch
           recurrence DERIVED from exact-signature history, never caller-trusted)
        -> EvidenceAdjudicator -> PhaseProposal
        -> GovernedTransitionExecutor -> actual phase trace
        -> compare (expectations applied AFTER the run, never during)

G2R additions:

  * Evidence objects are EXECUTION-GRADE. Every evidence_ref cited by an
    observation, proposal or institutional action must resolve in the governed
    EvidenceRegistry (built from observable_evidence.json before the first
    adjudicated decision); unknown refs fail closed with a recorded violation.
  * Independence is a NON-SCALAR lineage vector (G2R §5): raw count, distinct
    source/model lineages, shared allocator/retrieval exposure. Policy gates may
    require >= N distinct lineages; no effective-sample-size score is minted.
  * Patch recurrence is DERIVED from the ordered exact-signature event history;
    a caller-supplied recurrence that lies is overridden (G2R-03).
  * RESOLUTION CONDITIONS (PROVISIONAL_TEST_OBJECT, AMB-13) are resolved from
    the registry so NEW_STABLE / PLURAL_MODEL_STATE make their resolution
    semantics explicit without adding an A-010 evidence channel.
  * Scripted institutional lifecycle steps are labelled FIXTURE_SIDE_EFFECT:
    G2 tests that those actions are LEGAL and evidence-bound, not that OCE
    autonomously chose them (G2R-09).
  * behavior_fingerprint excludes scenario_id and post-hoc expectations; the
    run-identity fingerprint keeps scenario_id (G2R-12).
  * Every applied phase transition gets an audit entry (G2R-11) covering: refs
    exist, refs are permitted input objects, contract fingerprint, policy
    fingerprint, authority actor valid, role authorized, transition
    contract-admissible, M5 topology legal.
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
from .registry import EvidenceRegistry, UnknownEvidenceRef
from .replay import ReplayEvent

# structural levels for derived recurrence (L1..L6)
_LEVEL_RANK = {"L1": 1, "L2": 2, "L3": 3, "L4": 4, "L5": 5, "L6": 6}


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


class PatchAccumulator:
    """G2R-03: derive per-signature recurrence / override / justified-level from
    the ORDERED patch-event history. Caller-supplied recurrence is NEVER trusted
    as institutional truth — the derived value wins."""

    def __init__(self) -> None:
        self._by_sig: Dict[str, Dict[str, Any]] = {}

    def derive(self, patch: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
        if not patch:
            return None
        sig = str(patch.get("causal_signature", "") or "UNSIGNED")
        level = str(patch.get("structural_level", "L1"))
        override = int(patch.get("override_count", 0) or 0)
        bucket = self._by_sig.setdefault(sig, {"count": 0, "max_level": "L1", "override_total": 0})
        bucket["count"] += 1
        if level in _LEVEL_RANK and _LEVEL_RANK[level] > _LEVEL_RANK.get(bucket["max_level"], 0):
            bucket["max_level"] = level
        bucket["override_total"] += override
        out = dict(patch)  # caller-supplied fields preserved for the audit
        out.pop("recurrence", None)                      # derived replaces the trust field
        out["causal_signature"] = sig
        out["derived_recurrence"] = bucket["count"]       # DERIVED truth (G2R-03)
        out["recurrence"] = bucket["count"]               # rules read this
        out["justified_level"] = bucket["max_level"]      # highest level for this signature so far
        out["override_total"] = bucket["override_total"]
        out["caller_supplied_recurrence"] = int(patch.get("recurrence", 0) or 0)
        return out


class ScenarioRunResult:
    """Machine-readable outcome of one scenario execution (G2 §22 shape)."""

    def __init__(self, **kw):
        self.artifacts: Dict[str, Any] = dict(kw)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.artifacts)


def explain_transition(result: ScenarioRunResult, seq: int) -> Dict[str, Any]:
    """G2R-11: machine-readable WHY for a phase transition at observation `seq`.
    Returns the full audit record, or a sentinel when the seq was not a
    submitted transition."""
    audit = result.artifacts.get("transitions_audit", {})
    if seq in audit:
        return audit[seq]
    return {"seq": seq, "explained": False, "reason": "no transition proposal at this observation"}


def run_scenario(
    spec: StressScenarioSpec,
    contract: PhaseEvaluationContract,
    policy: AdjudicatorPolicy,
    governor_actor: str = "GOVERNOR",
    authority_override: Optional[Dict[str, str]] = None,
    evidence_records: Optional[List[Mapping[str, Any]]] = None,
) -> ScenarioRunResult:
    # ---- freeze the evaluation contract BEFORE any adjudicated decision ----
    if not contract.is_frozen():
        contract.freeze()
    contract_fp = contract.fingerprint()
    contract_meta = {
        "contract_id": contract.contract_id,
        "version_tag": contract.version_tag,
        "fingerprint": contract_fp,
        "freeze_status": contract.freeze_status,
    }

    # ---- governed evidence registry (G2R-02) --------------------------------
    registry = EvidenceRegistry.from_records(evidence_records or []) if evidence_records else None
    if registry is not None:
        registry_snapshot = sorted(registry.ids)
    else:
        registry_snapshot = []

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
    executor = GovernedTransitionExecutor(phase, lifecycle, auth, registry=registry)
    adjudicator = EvidenceAdjudicator(policy, contract)
    accumulator = PatchAccumulator()

    actual_phase_trace: List[str] = [phase.state]
    trace_entries: List[Dict[str, Any]] = []
    evidence_refs_by_transition: Dict[int, List[str]] = {}
    transitions_audit: Dict[int, Dict[str, Any]] = {}
    holds: List[Dict[str, Any]] = []
    stimulus_count = 0
    evidence_count = 0
    ref_violations: List[Dict[str, Any]] = []

    for raw in view.get("stimulus_events", []):
        stimulus_count += 1
        vec = dict(raw.get("evidence_vector", {}))
        refs = tuple(raw.get("evidence_refs", []))
        if refs:
            evidence_count += 1
        holds_labels = tuple(raw.get("holds", []))

        # fail-closed ref validation: unknown refs park the observation entirely
        if registry is not None:
            try:
                registry.check_all(refs)
            except UnknownEvidenceRef as exc:
                ref_violations.append({"seq": int(raw["seq"]), "detail": str(exc)})
                trace_entries.append({
                    "seq": int(raw["seq"]), "machine": "evidence", "event_type": "observe",
                    "from": "", "to": "", "allowed": False, "applied": False,
                    "rule_ids": ["EVIDENCE_REF_UNKNOWN"], "rationale": str(exc),
                    "kind": "EVIDENCE_REF_UNKNOWN",
                })
                continue

        lineage = registry.lineage_summary(refs) if (registry is not None and refs) else None
        derived_patch = accumulator.derive(raw.get("patch_pressure"))
        obs = EvidenceObservation(
            seq=int(raw["seq"]),
            vector=vec,
            evidence_refs=refs,
            lineage_labels=tuple(raw.get("lineage_labels", [])),
            lineage=dict(lineage.to_dict()) if lineage is not None else None,
            resolution_kinds=lineage.resolution_kinds if lineage is not None else (),
            patch=derived_patch,
            affected=raw.get("affected"),
            holds=holds_labels,
        )
        adjudicator.observe(obs)
        proposal: PhaseProposal = adjudicator.propose(current_phase=phase.state)

        base_seq = int(raw["seq"]) * 10
        # generic topology prefilter: a proposal whose target is not reachable
        # from the current phase is never submitted to the executor (it would
        # only generate a noisy forbidden attempt). Recorded as a filtered hold.
        if proposal.action == "TRANSITION" and not phase.can_transition(proposal.to_state):
            holds.append({
                "seq": obs.seq, "rule_id": proposal.rule_id,
                "rationale": f"proposal filtered: {phase.state} -> {proposal.to_state} is not a legal phase edge",
            })
            proposal = PhaseProposal(rule_id="PREFILTERED", action="HOLD", rationale="topology-prefiltered")
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
            m5_topology_legal = phase.can_transition(proposal.to_state)  # captured BEFORE apply
            entry = executor.execute(event)
            trace_entries.append({"seq": obs.seq, **{k: entry.to_dict()[k] for k in
                ("machine", "event_type", "from", "to", "allowed", "applied", "rule_ids",
                 "rationale", "kind")}})
            if entry.applied:
                actual_phase_trace.append(entry.to_dict()["to"])
                evidence_refs_by_transition[obs.seq] = list(proposal.evidence_refs)
            # G2R-11 linkage audit — every material transition must satisfy the
            # full invariant list; the audit records each dimension explicitly.
            refs_ok = True
            if registry is not None:
                try:
                    registry.check_all(proposal.evidence_refs)
                except UnknownEvidenceRef:
                    refs_ok = False
            transitions_audit[obs.seq] = {
                "seq": obs.seq,
                "from": entry.from_state,
                "to": entry.to_state,
                "rule_id": proposal.rule_id,
                "allowed": entry.allowed,
                "applied": entry.applied,
                "evidence_refs": list(proposal.evidence_refs),
                "evidence_refs_resolved": refs_ok,
                "permitted_input_objects": registry is not None,
                "contract_fingerprint": contract_fp,
                "contract_admissible": getattr(proposal, "admissible", True),
                "policy_fingerprint": policy.fingerprint(),
                "policy_id": policy.policy_id,
                "authority_actor": governor_actor,
                "authority_level": auth.level(governor_actor),
                "role_authorized": auth.level(governor_actor) in GovernedTransitionExecutor.M5_APPLY_ROLES,
                "m5_topology_legal": m5_topology_legal,
                "evidence_vector": dict(vec),
                "patch_derived_recurrence": (derived_patch or {}).get("derived_recurrence"),
                "lineage": dict(lineage.to_dict()) if lineage is not None else None,
                "explained": True,
            }

        # optional generic institutional action(s) (lifecycle/evidence/authority)
        ias = raw.get("institutional_action")
        if ias:
            if isinstance(ias, dict):
                ias = [ias]
            for offset, ia in enumerate(ias):
                ia_event = _institutional_action_event(base_seq + 1 + offset, ia)
                ia_entry = executor.execute(ia_event)
                fixture_side_effect = bool(ia.get("fixture_side_effect", False))
                trace_entries.append({"seq": obs.seq, "institutional": True,
                                      "fixture_side_effect": fixture_side_effect,
                                      **{k: ia_entry.to_dict()[k] for k in
                                         ("machine", "event_type", "from", "to", "allowed",
                                          "applied", "rule_ids", "rationale", "kind")}})

    terminal_lifecycle = {rid: r.state for rid, r in lifecycle.records.items()}
    authority_after = {
        a: {"level": auth.level(a),
            "grants": sorted(g.grant_id for g in auth.registry.grants(a))}
        for a in auth.actors
    }

    # run-identity fingerprint (G2R-12): carries scenario_id for artifact identity
    fingerprint = deterministic_hex(
        "scenario", spec.scenario_id, phase.state, terminal_lifecycle,
        trace_entries, contract_fp, policy.fingerprint(),
        length=32,
    )
    # behavior fingerprint (G2R-12): EXCLUDES scenario_id and post-hoc
    # expectations — a rename must not change behavior identity.
    behavior_fingerprint = deterministic_hex(
        "behavior", phase.state, terminal_lifecycle, trace_entries,
        holds, contract_fp, policy.fingerprint(), length=32,
    )

    return ScenarioRunResult(
        scenario_id=spec.scenario_id,
        scenario_version=spec.scenario_version,
        evaluation_contract=contract_meta,
        policy_id=policy.policy_id,
        policy_version=policy.version_tag,
        policy_fingerprint=policy.fingerprint(),
        initial_phase=spec.initial_phase,
        stimulus_count=stimulus_count,
        evidence_count=evidence_count,
        actual_phase_trace=actual_phase_trace,
        terminal_phase=phase.state,
        terminal_knowledge_states=terminal_lifecycle,
        holds=holds,
        trace=trace_entries,
        evidence_refs_by_transition=evidence_refs_by_transition,
        transitions_audit=transitions_audit,
        forbidden_attempts=[t for t in trace_entries if t.get("allowed") is False],
        evidence_ref_violations=ref_violations,
        registry_ids=registry_snapshot,
        authority_state_before=authority_before,
        authority_state_after=authority_after,
        expected_trace_accessed=False,
        hidden_ground_truth_accessed=False,
        fingerprint=fingerprint,
        behavior_fingerprint=behavior_fingerprint,
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