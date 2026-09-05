"""Generic fixture format (G1 §16) capable of expressing later StressScenarioSpec
fields. G1 creates NO S01-S24 specs and encodes no scenario outcome logic.

`hidden_ground_truth` (Book §3) is sealed from decision roles: the loader can
return a decision-grade projection that simply omits it. Nothing here ever mutates
production/cloud/capital.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from .replay import DeterministicReplay, ReplayEvent


@dataclass
class StressScenarioSpec:
    scenario_id: str
    scenario_version: str = "1.0.0"
    policy_ref: str = ""
    threat_class: str = "DETERMINISTIC_CONSTITUTIONAL"
    institutional_scope: str = ""
    initial_epoch: str = ""
    initial_authority_state: Dict[str, str] = field(default_factory=dict)
    initial_knowledge: List[dict] = field(default_factory=list)     # KnowledgeRecord seeds
    initial_phase: str = "STABLE"
    stimulus_events: List[dict] = field(default_factory=list)
    observable_evidence: List[str] = field(default_factory=list)
    correlation_structure: Dict[str, Any] = field(default_factory=dict)
    expected_phase_path: List[str] = field(default_factory=list)
    expected_terminal_knowledge: Dict[str, str] = field(default_factory=dict)
    allowed_actions: List[str] = field(default_factory=list)
    forbidden_actions: List[str] = field(default_factory=list)
    required_roles: List[str] = field(default_factory=list)
    operator_required_at: List[str] = field(default_factory=list)
    terminal_states: List[str] = field(default_factory=list)
    evaluation_contract: Optional[Dict[str, Any]] = None
    hidden_ground_truth: Optional[dict] = None          # sealed from decision roles
    seq: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    def decision_grade(self) -> "StressScenarioSpec":
        """Projection WITHOUT hidden_ground_truth — what decision roles may see."""
        out = self.to_dict()
        out.pop("hidden_ground_truth", None)
        return StressScenarioSpec(**out)


def spec_to_replay_events(spec: StressScenarioSpec) -> List[ReplayEvent]:
    """Translate generic stimulus_events into replay events. Each event carries
    its own seq; machine defaults to 'phase' unless overridden."""
    evs: List[ReplayEvent] = []
    for raw in spec.stimulus_events:
        evs.append(
            ReplayEvent(
                seq=int(raw.get("seq", len(evs) + 1)),
                event_type=raw.get("event_type", "phase_step"),
                machine=raw.get("machine", "phase"),
                actor=raw.get("actor", "TEST_DRIVER"),
                target=raw.get("target", "@INST"),
                payload=dict(raw.get("payload", {})),
                contract_version=raw.get("contract_version", ""),
            )
        )
    return evs


def build_seed_records(spec: StressScenarioSpec) -> List[Any]:
    """Build KnowledgeRecord seeds from the spec's initial_knowledge list."""
    from .base import Provenance
    from .lifecycle import KnowledgeRecord

    out: List[Any] = []
    for item in spec.initial_knowledge or []:
        prov = Provenance(
            source_kind=item.get("provenance_source_kind", "FIXTURE"),
            source_label=item.get("provenance_source_label", "fixture"),
            producing_actor=item.get("producing_actor", ""),
        )
        out.append(
            KnowledgeRecord(
                record_id=item["record_id"],
                claim=item.get("claim", ""),
                provenance=prov,
                creation_source="fixture",
                initial_state=item.get("state", "OBSERVED"),
            )
        )
    return out


def run_smoke(spec: StressScenarioSpec, seed_records=None) -> Any:
    """Small helper used by smoke fixtures: build a replay from a spec and run it.

    G2-P0: seeds AuthorityState from the spec's `initial_authority_state` and
    freezes initialization BEFORE the first event, so governed actions are bound
    to registered actors. Unknown authoritative roles in the fixture fail closed
    at seeding (ontology-bounded setup).
    """
    from .authority import AuthorityState
    seeds = seed_records if seed_records is not None else build_seed_records(spec)
    auth = AuthorityState()
    for actor, level in (spec.initial_authority_state or {}).items():
        auth.seed_level(actor, level)
    auth.freeze_initialization()
    replay = DeterministicReplay(seed_records=seeds, authority=auth)
    return replay.run(spec_to_replay_events(spec))


def add_seed_record(spec: StressScenarioSpec, record_id: str, state: str, claim: str = "") -> StressScenarioSpec:
    """Return a spec copy with a seeded knowledge record (for smoke fixtures)."""
    out = spec.to_dict()
    out["initial_knowledge"] = list(out.get("initial_knowledge", [])) + [
        {"record_id": record_id, "state": state, "claim": claim}
    ]
    return StressScenarioSpec(**out)


def load_spec(path) -> StressScenarioSpec:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    return StressScenarioSpec(**data)