"""M4 / M5 / M1 separation — the core structural guarantee (AMB-01, AMB-07)."""
from engine.phase import PhaseStateMachine
from engine.lifecycle import KnowledgeRecord
from engine.truth import CapabilityStatus, TruthRegistry
from engine.base import Provenance


def test_phase_does_not_touch_lifecycle():
    m = PhaseStateMachine()
    r = KnowledgeRecord(record_id="k", claim="c",
                        provenance=Provenance(source_kind="FIXTURE", source_label="t"),
                        creation_source="t", initial_state="DEMOTED")
    m.attempt(seq=1, actor="GOVERNOR", to_state="WATCH", evidence_vector={},
              authority_level="GOVERNOR", mutation_class="READ_ONLY")
    # phase moved to WATCH; knowledge state and its transitions are untouched
    assert m.state == "WATCH"
    assert r.state == "DEMOTED"
    assert r.transitions == []


def test_lifecycle_does_not_touch_phase():
    m = PhaseStateMachine()
    r = KnowledgeRecord(record_id="k", claim="c",
                        provenance=Provenance(source_kind="FIXTURE", source_label="t"),
                        creation_source="t", initial_state="OBSERVED")
    r.transition(seq=1, to_state="CANDIDATE", actor="PO", authority_basis="b",
                 authority_level="PO", reason="r")
    # lifecycle advanced while phase stays STABLE and got no decisions
    assert r.state == "CANDIDATE"
    assert m.state == "STABLE"
    assert m.decisions == []


def test_m1_label_does_not_change_m4_or_authority():
    reg = TruthRegistry()
    reg.register(CapabilityStatus(capability_id="cap1", label="IDEA"))
    reg.promote("cap1", "OPERATIONALLY_PROVEN", ["ev1"], "EVALUATOR")
    r = KnowledgeRecord(record_id="k", claim="c",
                        provenance=Provenance(source_kind="FIXTURE", source_label="t"),
                        creation_source="t", initial_state="OBSERVED")
    # capability label rose to max; knowledge object (M4) and phase remain baseline
    assert reg.label("cap1") == "OPERATIONALLY_PROVEN"
    assert r.state == "OBSERVED"


def test_promotion_requires_evidence_m1():
    reg = TruthRegistry()
    reg.register(CapabilityStatus(capability_id="cap2", label="IDEA"))
    try:
        reg.promote("cap2", "VERIFIED_E2E", [], "EVALUATOR")
        raise AssertionError("promotion without evidence must fail")
    except ValueError:
        pass