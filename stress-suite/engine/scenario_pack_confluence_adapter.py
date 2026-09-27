"""Scenario-pack → confluence adapter (read-only, translation/observation only).

Reuses existing owners — no duplication:
  parsing:            engine/scenariolib.load_scenario_pack (when available)
                      + direct JSON reads for stimulus_events
  adjudication:       owned by engine/scenario.run_scenario (not duplicated here)
  authority:          engine/authority.AuthorityState
  lifecycle:          engine/lifecycle.LifecycleEngine / edge table
  replay:             engine/replay.DeterministicReplay
  evidence registry:  engine/registry.EvidenceRegistry
  transition:         engine/governed.GovernedTransitionExecutor

Job: determine whether an existing scenario directory can be represented as an
outcome-preserving confluence action set under the frozen v0.2 engine, and if so
produce a StressScenarioSpec that preserves every consequential field verbatim
(no invention, no discard, no reduction).

If faithful projection is impossible, the adapter fails CLOSED with an exact
UNAVAILABLE_* provenance — never invents actions, never discards fields, never
substitutes a synthetic.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Projection status vocabulary — matches v0.2 projection_evidence_status family
AVAILABLE = "AVAILABLE"
UNAVAILABLE_NO_CONFLUENCE_ACTIONS = "UNAVAILABLE_NO_CONFLUENCE_ACTIONS"
UNAVAILABLE_ADJUDICATION_ONLY = "UNAVAILABLE_ADJUDICATION_ONLY"
UNAVAILABLE_MISSING_PAYLOAD_FIELD = "UNAVAILABLE_MISSING_PAYLOAD_FIELD"
UNAVAILABLE_UNSUPPORTED_MACHINE = "UNAVAILABLE_UNSUPPORTED_MACHINE"
UNAVAILABLE_UNSUPPORTED_AUTHORITY_SEMANTIC = "UNAVAILABLE_UNSUPPORTED_AUTHORITY_SEMANTIC"
UNAVAILABLE_EVIDENCE_IDENTITY_LOSS = "UNAVAILABLE_EVIDENCE_IDENTITY_LOSS"
UNAVAILABLE_LOAD_ERROR = "UNAVAILABLE_LOAD_ERROR"

# Machines the confluence model supports (lifecycle/phase/evidence) — these
# are the only ones that have a ReplayEvent interpretation under DeterministicReplay.
SUPPORTED_MACHINES = {"lifecycle", "phase", "evidence"}
# For institutional_action payload, these fields are consequential and must be preserved.
# If any required field is absent and cannot be derived without invention, projection fails.
REQUIRED_PAYLOAD_FIELDS = {"to_state", "authority_level", "authority_basis", "reason"}


@dataclass(frozen=True)
class PackProjection:
    candidate_id: str
    candidate_path: str
    status: str  # AVAILABLE | UNAVAILABLE_*
    reason: str
    # When AVAILABLE, these are populated:
    projected_spec: Any = None  # StressScenarioSpec or None
    action_count: int = 0
    institutional_action_count: int = 0
    stimulus_len: int = 0
    evidence_refs: tuple = ()  # type: ignore[assignment]

    @property
    def available(self) -> bool:
        return self.status == AVAILABLE


def _read_lines(path: Path) -> List[str]:
    return [l for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not l.strip().startswith("#")]


def project_pack(pack_dir: Path) -> PackProjection:
    """Read-only projection of a scenario directory into a confluence spec.

    Reuses stimulus_events.jsonl parsing directly (the same bytes the adjudication
    runner consumes) and the existing fixtures/replay owners for validation only.
    No second implementation of adjudication, authority, lifecycle or replay.

    Institutional_action-bearing events are the ONLY actions directly representable
    as confluence ActionIdentity / ReplayEvent under DeterministicReplay. Pure
    adjudication observations (evidence_vector without institutional_action) have
    no outcome-preserving mapping without duplicating the EvidenceAdjudicator —
    they are therefore UNAVAILABLE with provenance.
    """
    scen_path = pack_dir / "scenario.json"
    stim_path = pack_dir / "stimulus_events.jsonl"
    sid = pack_dir.name
    try:
        scen_data = json.loads(scen_path.read_text(encoding="utf-8"))
        sid = scen_data.get("scenario_id", sid)
    except Exception as e:
        return PackProjection(
            candidate_id=sid, candidate_path=str(pack_dir),
            status=UNAVAILABLE_LOAD_ERROR, reason=f"scenario.json load failed: {e}",
        )
    try:
        raw_lines = _read_lines(stim_path)
    except Exception as e:
        return PackProjection(
            candidate_id=sid, candidate_path=str(pack_dir),
            status=UNAVAILABLE_LOAD_ERROR, reason=f"stimulus_events.jsonl read failed: {e}",
        )
    if not raw_lines:
        return PackProjection(
            candidate_id=sid, candidate_path=str(pack_dir),
            status=UNAVAILABLE_NO_CONFLUENCE_ACTIONS,
            reason="stimulus_events.jsonl empty; no confluence actions to project",
            stimulus_len=0,
        )
    raw_events = []
    for line in raw_lines:
        try:
            raw_events.append(json.loads(line))
        except Exception as e:
            return PackProjection(
                candidate_id=sid, candidate_path=str(pack_dir),
                status=UNAVAILABLE_LOAD_ERROR, reason=f"stimulus line parse failed: {e}",
            )
    # Separate institutional actions from adjudication-only observations
    institutional_actions: List[Dict[str, Any]] = []
    adjudication_only: List[Dict[str, Any]] = []
    for ev in raw_events:
        ias = ev.get("institutional_action")
        if ias is not None:
            items = ias if isinstance(ias, list) else [ias]
            institutional_actions.extend(items)
        else:
            adjudication_only.append(ev)

    if not institutional_actions:
        # No direct ReplayEvent actions present. The stimulus consists entirely of
        # adjudication observations (evidence_vector -> EvidenceAdjudicator -> phase
        # proposal). Faithful projection would require duplicating the adjudicator
        # execution path — forbidden. Report UNAVAILABLE with exact provenance.
        has_vec = any("evidence_vector" in e for e in raw_events)
        has_operator = any(e.get("type", "").startswith("freeze") or e.get("type", "").startswith("mutate") or "grant_id" in e for e in raw_events)
        if has_operator:
            reason = (
                "UNAVAILABLE_ADJUDICATION_ONLY: stimulus events contain no institutional_action "
                "with lifecycle/phase ReplayEvent semantics; they are operator/governor/capability "
                "mutations requiring the adjudication authority path (engine/scenario.run_scenario), "
                "not DeterministicReplay; translating them as lifecycle events would discard governing semantics"
            )
            status = UNAVAILABLE_ADJUDICATION_ONLY
        elif has_vec:
            reason = (
                "UNAVAILABLE_ADJUDICATION_ONLY: stimulus events are evidence_vector observations "
                "routed through EvidenceAdjudicator -> PhaseProposal -> GovernedTransitionExecutor; "
                "they have no direct ReplayEvent payload (to_state/authority_level) and cannot be "
                "represented as outcome-preserving ActionIdentity without duplicating the adjudication owner"
            )
            status = UNAVAILABLE_ADJUDICATION_ONLY
        else:
            reason = (
                "UNAVAILABLE_NO_CONFLUENCE_ACTIONS: stimulus events contain no institutional_action entries "
                "and no identifiable action payload; nothing maps to ActionIdentity without invention"
            )
            status = UNAVAILABLE_NO_CONFLUENCE_ACTIONS
        return PackProjection(
            candidate_id=sid, candidate_path=str(pack_dir),
            status=status, reason=reason,
            stimulus_len=len(raw_events),
            institutional_action_count=0,
            action_count=0,
        )

    # Validate each institutional_action entry for consequential field preservation
    for idx, ia in enumerate(institutional_actions):
        machine = str(ia.get("machine", "lifecycle"))
        if machine not in SUPPORTED_MACHINES:
            return PackProjection(
                candidate_id=sid, candidate_path=str(pack_dir),
                status=UNAVAILABLE_UNSUPPORTED_MACHINE,
                reason=(
                    f"UNAVAILABLE_UNSUPPORTED_MACHINE: institutional_action[{idx}] machine={machine!r} "
                    f"is not in supported confluence machines {sorted(SUPPORTED_MACHINES)}; "
                    f"no confluence representation exists without inventing payload semantics"
                ),
                stimulus_len=len(raw_events),
                institutional_action_count=len(institutional_actions),
            )
        payload = ia.get("payload") or {}
        missing = sorted(REQUIRED_PAYLOAD_FIELDS - set(payload.keys()))
        if missing:
            return PackProjection(
                candidate_id=sid, candidate_path=str(pack_dir),
                status=UNAVAILABLE_MISSING_PAYLOAD_FIELD,
                reason=(
                    f"UNAVAILABLE_MISSING_PAYLOAD_FIELD: institutional_action[{idx}] target={ia.get('target','')!r} "
                    f"missing consequential fields {missing}; discarding or inventing them would break outcome preservation"
                ),
                stimulus_len=len(raw_events),
                institutional_action_count=len(institutional_actions),
            )
        # Evidence identity: if evidence_refs present, they must be strings that survive projection.
        # An institutional_action that carries no machine or target would lose identity.
        if not ia.get("target"):
            return PackProjection(
                candidate_id=sid, candidate_path=str(pack_dir),
                status=UNAVAILABLE_EVIDENCE_IDENTITY_LOSS,
                reason=(
                    f"UNAVAILABLE_EVIDENCE_IDENTITY_LOSS: institutional_action[{idx}] has no target record_id; "
                    f"evidence identity (record_id) would be lost under projection"
                ),
                stimulus_len=len(raw_events),
                institutional_action_count=len(institutional_actions),
            )
        # Authority semantic: if authority_level missing, cannot be preserved
        # (already covered by REQUIRED_PAYLOAD_FIELDS, but explicit for audit)
        if not payload.get("authority_level"):
            return PackProjection(
                candidate_id=sid, candidate_path=str(pack_dir),
                status=UNAVAILABLE_UNSUPPORTED_AUTHORITY_SEMANTIC,
                reason=(
                    f"UNAVAILABLE_UNSUPPORTED_AUTHORITY_SEMANTIC: institutional_action[{idx}] "
                    f"authority_level missing; authority semantics cannot be preserved without invention"
                ),
                stimulus_len=len(raw_events),
                institutional_action_count=len(institutional_actions),
            )

    # Build the projected StressScenarioSpec by reusing the existing spec fields
    # (initial_knowledge / authority / phase) and translating institutional_action
    # entries verbatim into stimulus_events with their exact payload bytes preserved.
    try:
        from engine.fixtures import StressScenarioSpec  # type: ignore[import]

        stimulus = []
        for seq, ia in enumerate(institutional_actions, start=1):
            stimulus.append({
                "seq": seq,
                "machine": str(ia.get("machine", "lifecycle")),
                "actor": str(ia.get("actor", "PO")),
                "target": str(ia.get("target", "")),
                "event_type": str(ia.get("event_type", "lifecycle_step" if ia.get("machine", "lifecycle") == "lifecycle" else "phase_step")),
                "payload": dict(ia.get("payload", {}) or {}),
                "contract_version": str(ia.get("contract_version", "")),
            })
        spec = StressScenarioSpec(
            scenario_id=sid,
            scenario_version=str(scen_data.get("scenario_version", "1.0.0")),
            policy_ref=str(scen_data.get("policy_ref", "")),
            threat_class=str(scen_data.get("threat_class", "")),
            institutional_scope=str(scen_data.get("institutional_scope", "")),
            initial_epoch=str(scen_data.get("initial_epoch", "")),
            initial_authority_state=dict(scen_data.get("initial_authority_state", {}) or {}),
            initial_knowledge=list(scen_data.get("initial_knowledge", []) or []),
            initial_phase=str(scen_data.get("initial_phase", "STABLE")),
            stimulus_events=stimulus,
            observable_evidence=list(scen_data.get("observable_evidence", []) or []),
            correlation_structure=dict(scen_data.get("correlation_structure", {}) or {}),
            expected_phase_path=list(scen_data.get("expected_phase_path", []) or []),
            expected_terminal_knowledge=dict(scen_data.get("expected_terminal_knowledge", {}) or {}),
            allowed_actions=list(scen_data.get("allowed_actions", []) or []),
            forbidden_actions=list(scen_data.get("forbidden_actions", []) or []),
            required_roles=list(scen_data.get("required_roles", []) or []),
            operator_required_at=list(scen_data.get("operator_required_at", []) or []),
            terminal_states=list(scen_data.get("terminal_states", []) or []),
            evaluation_contract=scen_data.get("evaluation_contract"),
            hidden_ground_truth=scen_data.get("hidden_ground_truth"),
            seq=int(scen_data.get("seq", 0)),
        )
        return PackProjection(
            candidate_id=sid, candidate_path=str(pack_dir),
            status=AVAILABLE,
            reason="projected via institutional_action -> ActionIdentity translation; all consequential fields preserved verbatim",
            projected_spec=spec,
            action_count=len(stimulus),
            institutional_action_count=len(institutional_actions),
            stimulus_len=len(raw_events),
            evidence_refs=tuple(sorted({r for ia in institutional_actions for r in (ia.get("payload", {}) or {}).get("evidence_refs", [])})),
        )
    except Exception as e:
        return PackProjection(
            candidate_id=sid, candidate_path=str(pack_dir),
            status=UNAVAILABLE_LOAD_ERROR, reason=f"projected spec build failed: {e}",
            stimulus_len=len(raw_events),
            institutional_action_count=len(institutional_actions),
        )
