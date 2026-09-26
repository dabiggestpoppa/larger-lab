"""G2R-02 — governed evidence registry is EXECUTION-GRADE.

Every evidence_ref used by observations, proposals and institutional actions
must resolve to an actual registered evidence object. Unknown refs fail closed;
duplicate conflicting ids fail closed; provenance survives.
"""
import pytest

from engine.registry import EvidenceRegistry, UnknownEvidenceRef, DuplicateEvidenceError
from engine.evidence import EvidenceRecord
from engine.scenario import run_scenario
from engine.adjudicate import AdjudicatorPolicy
from engine.evalcontract import PhaseEvaluationContract
from engine.fixtures import StressScenarioSpec

RECORDS = [
    {"record_id": "E1", "kind": "OBSERVATION", "claim": "first", "lineage": "LINEAGE_A"},
    {"record_id": "E2", "kind": "INDEPENDENT_CONFIRMATION", "claim": "second", "lineage": "LINEAGE_B"},
]


def _policy():
    return AdjudicatorPolicy.from_data({
        "policy_id": "g2r-reg",
        "version_tag": "V1",
        "rules": [
            {"rule_id": "enter.watch", "to_state": "WATCH",
             "any_of": [{"reliability_degradation": "MEDIUM"}]},
        ],
    })


def _contract():
    return PhaseEvaluationContract.make(1, version_tag="REG-V1")


def _spec(events):
    return StressScenarioSpec(scenario_id="minireg", stimulus_events=events,
                              initial_authority_state={"GOVERNOR": "GOVERNOR"})


def test_known_evidence_ref_resolves():
    reg = EvidenceRegistry.from_records(RECORDS)
    assert reg.has("E1")
    obj = reg.resolve("E1")
    assert isinstance(obj, EvidenceRecord)
    assert obj.source_lineage == "LINEAGE_A"


def test_unknown_evidence_ref_rejected():
    reg = EvidenceRegistry.from_records(RECORDS)
    with pytest.raises(UnknownEvidenceRef):
        reg.resolve("E_GHOST")
    with pytest.raises(UnknownEvidenceRef):
        reg.check_all(["E1", "E_GHOST"])


def test_duplicate_conflicting_evidence_id_rejected():
    with pytest.raises(DuplicateEvidenceError):
        EvidenceRegistry.from_records([
            {"record_id": "X", "kind": "OBSERVATION", "claim": "a"},
            {"record_id": "X", "kind": "OBSERVATION", "claim": "b"},
        ])


def test_duplicate_identical_evidence_id_tolerated():
    reg = EvidenceRegistry.from_records([
        {"record_id": "X", "kind": "OBSERVATION", "claim": "a"},
        {"record_id": "X", "kind": "OBSERVATION", "claim": "a"},
    ])
    assert len(reg) == 1


def test_phase_transition_cannot_cite_phantom_evidence():
    """An observation whose refs do not resolve parks the observation entirely
    (fail closed): no proposal is formed from phantom evidence."""
    events = [
        {"seq": 1, "evidence_vector": {"reliability_degradation": "MEDIUM"}, "evidence_refs": ["E1"]},
        {"seq": 2, "evidence_vector": {"reliability_degradation": "MEDIUM"}, "evidence_refs": ["E_GHOST"]},
        {"seq": 3, "evidence_vector": {"reliability_degradation": "MEDIUM"}, "evidence_refs": ["E1"]},
    ]
    res = run_scenario(_spec(events), _contract(), _policy(), evidence_records=RECORDS)
    assert res.artifacts["actual_phase_trace"] == ["STABLE", "WATCH"]  # only E1-cited obs moved
    violations = res.artifacts["evidence_ref_violations"]
    assert [v["seq"] for v in violations] == [2]
    assert any(t.get("kind") == "EVIDENCE_REF_UNKNOWN" for t in res.artifacts["trace"])


def test_institutional_action_cannot_cite_phantom_evidence():
    events = [
        {"seq": 1, "evidence_vector": {"reliability_degradation": "MEDIUM"}, "evidence_refs": ["E1"],
         "institutional_action": {
             "fixture_side_effect": True, "machine": "lifecycle", "actor": "PO",
             "target": "@K", "payload": {
                 "to_state": "DEMOTED", "authority_level": "PO", "authority_basis": "a-009",
                 "reason": "r", "evidence_refs": ["E_GHOST"]}}},
    ]
    spec = StressScenarioSpec(
        scenario_id="minireg2", stimulus_events=events,
        initial_authority_state={"GOVERNOR": "GOVERNOR", "PO": "PO"},
        initial_knowledge=[{"record_id": "@K", "state": "ACTIVE", "claim": "c"}],
    )
    res = run_scenario(spec, _contract(), _policy(), evidence_records=RECORDS)
    inst = [t for t in res.artifacts["trace"] if t.get("institutional")]
    assert inst and inst[0]["allowed"] is False
    assert inst[0]["kind"] == "EVIDENCE_REF_UNKNOWN"
    assert res.artifacts["terminal_knowledge_states"]["@K"] == "ACTIVE"  # untouched


def test_evidence_refs_survive_transitions_in_audit():
    events = [{"seq": 1, "evidence_vector": {"reliability_degradation": "MEDIUM"}, "evidence_refs": ["E1"]}]
    res = run_scenario(_spec(events), _contract(), _policy(), evidence_records=RECORDS)
    audit = res.artifacts["transitions_audit"]
    assert audit[1]["evidence_refs"] == ["E1"]
    assert audit[1]["evidence_refs_resolved"] is True
    assert audit[1]["permitted_input_objects"] is True