"""Scenario pack loader (G2 §8). Generic directory -> runnable artifacts.

A pack is a directory `stress-suite/scenarios/S0X/` containing:

  scenario.json              StressScenarioSpec (NO expected-trace fields)
  stimulus_events.jsonl      ordered evidence observations (one JSON per line)
  observable_evidence.json   evidence record list (informational provenance)
  evaluation_contract.json   PhaseEvaluationContract (frozen per run)
  adjudicator_policy.json    PROVISIONAL_SCENARIO_TEST_POLICY rule list
  expected_phase_trace.json  expectations applied ONLY post-hoc
  forbidden_transitions.json documented forbidden edges (asserted un-tried)
  initial_epoch.json         epoch context (informational)
  knowledge_before.json      seeded knowledge snapshot (informational)
  knowledge_after.json       expected terminal knowledge (post-hoc)

The loader assembles these into a ScenarioPack; run_scenario() strips every
expectation from the decision-grade projection, so nothing here can inform the
execution. No S01-S24 logic lives in the engine — these are data files.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .adjudicate import AdjudicatorPolicy
from .evalcontract import PhaseEvaluationContract
from .fixtures import StressScenarioSpec


@dataclass(frozen=True)
class ScenarioPack:
    scenario_id: str
    spec: StressScenarioSpec
    contract: PhaseEvaluationContract
    policy: AdjudicatorPolicy
    observable_evidence: List[Dict[str, Any]]
    forbidden_transitions: List[Dict[str, Any]]
    expected: Dict[str, Any]
    initial_epoch: Dict[str, Any]
    knowledge_before: Dict[str, Any]
    knowledge_after: Dict[str, Any]
    path: Path


def _read_json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def _load_events(p: Path) -> List[Dict[str, Any]]:
    events = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        events.append(json.loads(line))
    return events


def _build_contract(data: Dict[str, Any]) -> PhaseEvaluationContract:
    admissible = []
    for pair in data.get("admissible_phase_transitions", []):
        admissible.append(tuple(pair))
    return PhaseEvaluationContract(
        contract_id=str(data["contract_id"]),
        schema_version=str(data.get("schema_version", "1.0.0")),
        version_tag=str(data.get("version_tag", "V1")),
        channel_rules=dict(data.get("channel_rules", {})),
        hysteresis_rules=dict(data.get("hysteresis_rules", {})),
        admissible_phase_transitions=admissible,
        created_at_seq=int(data.get("created_at_seq", 0)),
        authority_basis=str(data.get("authority_basis", "PROVISIONAL_SCENARIO_TEST_POLICY")),
        freeze_status=data.get("freeze_status", "UNFROZEN"),
        supersedes=data.get("supersedes"),
    )


def load_scenario_pack(sdir: Union[str, Path]) -> ScenarioPack:
    d = Path(sdir)
    scenario_raw = _read_json(d / "scenario.json")
    scenario_raw["stimulus_events"] = _load_events(d / "stimulus_events.jsonl")

    spec = StressScenarioSpec(**scenario_raw)
    # expectations live in their own file; loaded onto the spec only so the
    # POST-HOC comparator can use them (run_scenario strips them regardless).
    expected = _read_json(d / "expected_phase_trace.json")
    spec.expected_phase_path = list(expected.get("expected_phase_path", []))
    spec.expected_terminal_knowledge = dict(expected.get("expected_terminal_knowledge", {}))
    spec.terminal_states = list(expected.get("terminal_states", []))

    contract = _build_contract(_read_json(d / "evaluation_contract.json"))
    policy = AdjudicatorPolicy.from_data(_read_json(d / "adjudicator_policy.json"))
    observable = _read_json(d / "observable_evidence.json").get("records", [])
    forbidden = _read_json(d / "forbidden_transitions.json").get("forbidden", [])
    initial_epoch = _read_json(d / "initial_epoch.json")
    knowledge_before = _read_json(d / "knowledge_before.json")
    knowledge_after = _read_json(d / "knowledge_after.json")

    return ScenarioPack(
        scenario_id=spec.scenario_id,
        spec=spec,
        contract=contract,
        policy=policy,
        observable_evidence=observable,
        forbidden_transitions=forbidden,
        expected=expected,
        initial_epoch=initial_epoch,
        knowledge_before=knowledge_before,
        knowledge_after=knowledge_after,
        path=d.resolve(),
    )


SCENARIO_DIRS = {
    "S01": "s01_old_theory_dies_slowly",
    "S02": "s02_false_revolution",
    "S03": "s03_patch_maze",
    "S04": "s04_leaf_failure",
    "S05": "s05_two_non_dominated_models",
    "S01_WEAK": "s01_variant_weak_contradiction",
}


def load_all_packs(scenarios_root: Optional[Union[str, Path]] = None) -> Dict[str, ScenarioPack]:
    root = Path(scenarios_root) if scenarios_root else Path(__file__).resolve().parent.parent / "scenarios"
    return {sid: load_scenario_pack(root / sub) for sid, sub in SCENARIO_DIRS.items()}