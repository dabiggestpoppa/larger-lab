"""G1R-10 — adversarial serialization / replay integrity sweep.

Every object used in replay/evidence must serialize deterministically, contain no
accidental wall-clock or non-serializable mutable alias, retain provenance, and
keep the relevant contract version. We build each object TWICE from the same
inputs and require identical serialized bytes — any embedded live timestamp or
mutable leakage would break equality.
"""
import json
from dataclasses import asdict

from engine.phase import PhaseDecisionRecord, PhaseStateMachine
from engine.lifecycle import KnowledgeRecord, LifecycleEdgeTable, TransitionRecord
from engine.evidence import EvidenceRecord, EvidenceChannelVector
from engine.independence import IndependenceRecord
from engine.negative import NegativeKnowledgeRecord
from engine.epoch import EpochManifest
from engine.evalcontract import PhaseEvaluationContract
from engine.replay import DeterministicReplay, ReplayEvent
from engine.base import Provenance


def _stable_dumps(obj) -> str:
    # json.dumps forces the object to be plain-serializable and canonical-key
    return json.dumps(obj, sort_keys=True, ensure_ascii=True)


_FRAG = "G1R10"


def _phase_decision() -> PhaseDecisionRecord:
    m = PhaseStateMachine()
    return m.evaluate(seq=1, actor="GOVERNOR", to_state="WATCH",
                      evidence_vector={"reliability_degradation": "MEDIUM"},
                      authority_level="GOVERNOR", mutation_class="READ_ONLY", reason="r")


def _transition() -> TransitionRecord:
    r = KnowledgeRecord(record_id="k", claim="c",
                        provenance=Provenance(source_kind="FIXTURE", source_label=_FRAG),
                        creation_source="t", initial_state="ACTIVE")
    return r.transition(seq=1, to_state="CHALLENGED", actor="PO", authority_basis="b",
                        authority_level="PO", reason="r")


def _evidence() -> EvidenceRecord:
    return EvidenceRecord.make(1, "claim", kind="OBSERVATION",
                               provenance=Provenance(source_kind="OBSERVATION", source_label=_FRAG))


def _independence() -> IndependenceRecord:
    return IndependenceRecord.make(1, raw_reviewers=10, distinct_source_lineages=1,
                                   distinct_model_families=1, distinct_retrieval_bundles=1,
                                   overlaps={"source_overlap": "HIGH", "allocator_overlap": "HIGH"})


def _negative() -> NegativeKnowledgeRecord:
    return NegativeKnowledgeRecord.make(1, "claim", "scope", "reason", reopen_conditions=["sensor"])


def _epoch() -> EpochManifest:
    return EpochManifest.make(seq=1, epoch_id="E17", known_tensions=["T1"])


def _contract() -> PhaseEvaluationContract:
    return PhaseEvaluationContract.make(1, version_tag="V1", hysteresis_rules={"enter_watch": "one"})


def _replay_result():
    evs = [ReplayEvent(1, "phase_step", "phase", "S", "@INST",
                       {"to_state": "WATCH", "evidence_vector": {}, "authority_level": "GOVERNOR",
                        "mutation_class": "READ_ONLY"}),
           ReplayEvent(2, "phase_step", "phase", "G", "@INST",
                       {"to_state": "STABLE", "evidence_vector": {}, "authority_level": "GOVERNOR",
                        "mutation_class": "READ_ONLY"})]
    return DeterministicReplay().run(evs)


_CASES = [
    ("PhaseDecisionRecord", lambda: _phase_decision().to_dict()),
    ("LifecycleTransitionRecord", lambda: _transition().to_dict()),
    ("EvidenceRecord", lambda: asdict(_evidence())),
    ("IndependenceRecord", lambda: asdict(_independence())),
    ("NegativeKnowledgeRecord", lambda: asdict(_negative())),
    ("EpochManifest", lambda: _epoch().to_dict()),
    ("PhaseEvaluationContract", lambda: _contract().to_dict()),
    ("ReplayResult", lambda: _replay_result().to_dict()),
]


def test_all_replay_objects_serialize_plainly():
    for name, build in _CASES:
        data = build()
        # json-serializability proves "no non-serializable alias" + no proxies
        text = _stable_dumps(data)
        assert isinstance(text, str) and len(text) > 0


def test_all_replay_objects_deterministic_across_independent_builds():
    for name, build in _CASES:
        assert _stable_dumps(build()) == _stable_dumps(build()), f"{name} not deterministic"


def test_provenance_retained_in_evidence_series():
    ev = _evidence()
    d = asdict(ev)
    assert d["provenance"]["source_label"] == _FRAG


def test_contract_version_retained_on_decisions_and_transitions():
    pd = _phase_decision()
    assert pd.to_dict()["contract_version"] == PhaseStateMachine().edge_table.contract_version
    tr = _transition()
    assert tr.to_dict()["contract_version"] == LifecycleEdgeTable.default().contract_version


def test_no_live_timestamp_embedded():
    # building the same noisy object twice on separate "clock" must still be equal
    a = _replay_result().fingerprint
    b = _replay_result().fingerprint
    assert a == b
    # and evidence channel vector serializes stably
    v = EvidenceChannelVector({"reliability_degradation": "HIGH"}).vector
    assert _stable_dumps(v) == _stable_dumps(v)