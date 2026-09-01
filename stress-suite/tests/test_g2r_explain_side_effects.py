"""G2R-11 (§15) + G2R-09 (§13).

* explain_transition(): every material applied phase transition carries the full
  linkage invariant — refs exist and are permitted inputs, contract + policy
  fingerprints recorded, authority actor valid, role authorized, transition
  contract-admissible, M5 topology legal, evidence vector + derived recurrence
  preserved.
* Scripted M4 side effects are labeled FIXTURE_SIDE_EFFECT: G2 proves those
  lifecycle actions are LEGAL and evidence-bound, NOT that the Governor
  autonomously chose the knowledge disposition.
"""
from pathlib import Path

from engine.scenariolib import load_all_packs
from engine.scenario import run_scenario, explain_transition

SCENARIOS_ROOT = Path(__file__).resolve().parent.parent / "scenarios"
PACKS = load_all_packs(SCENARIOS_ROOT)


def _run(sid):
    pack = PACKS[sid]
    return run_scenario(pack.spec, pack.contract, pack.policy,
                        evidence_records=pack.observable_evidence), pack


def test_explain_transition_full_linkage_record():
    res, pack = _run("S01")
    audit = res.artifacts["transitions_audit"]
    assert audit, "S01 must have material transitions"
    # obs1 -> WATCH is the first material transition
    rec = explain_transition(res, 1)
    assert rec["explained"] is True
    assert rec["from"] == "STABLE" and rec["to"] == "WATCH"
    assert rec["allowed"] is True and rec["applied"] is True
    assert rec["evidence_refs_resolved"] is True
    assert rec["permitted_input_objects"] is True
    assert rec["contract_fingerprint"] == pack.contract.fingerprint()
    assert rec["policy_fingerprint"] == pack.policy.fingerprint()
    assert rec["policy_id"] == "G2_CORE_PHASE_POLICY"
    assert rec["authority_actor"] == "GOVERNOR"
    assert rec["authority_level"] == "GOVERNOR"
    assert rec["role_authorized"] is True
    assert rec["contract_admissible"] is True
    assert rec["m5_topology_legal"] is True
    assert rec["evidence_vector"]["reliability_degradation"] == "MEDIUM"


def test_explain_transition_unknown_seq_sentinel():
    res, _ = _run("S01")
    sentinel = explain_transition(res, 99999)
    assert sentinel["explained"] is False
    assert "no transition proposal" in sentinel["reason"]


def test_every_applied_transition_satisfies_linkage_invariants():
    for sid in ("S01", "S02", "S03", "S04", "S05"):
        res, pack = _run(sid)
        audit = res.artifacts["transitions_audit"]
        applied = [a for a in audit.values() if a["applied"]]
        assert applied, sid
        for a in applied:
            assert a["evidence_refs_resolved"] is True, (sid, a["seq"])
            assert a["permitted_input_objects"] is True
            assert a["role_authorized"] is True
            assert a["contract_admissible"] is True
            assert a["m5_topology_legal"] is True
            assert a["contract_fingerprint"] == pack.contract.fingerprint()
            assert a["policy_fingerprint"] == pack.policy.fingerprint()


def test_scripted_lifecycle_actions_labeled_fixture_side_effect():
    """G2R-09 honesty: the M4 actions S01/S02/S05 execute are SCRIPTED stimulus
    side effects, labeled FIXTURE_SIDE_EFFECT. G2 therefore proves LEGALITY and
    EVIDENCE-BINDING of those actions — it does NOT claim the Governor
    autonomously selected the knowledge disposition."""
    for sid in ("S01", "S02", "S05"):
        res, _ = _run(sid)
        inst = [t for t in res.artifacts["trace"] if t.get("institutional")]
        assert inst, sid
        for t in inst:
            assert t.get("fixture_side_effect", False) is True, \
                f"{sid}: institutional step must be labeled FIXTURE_SIDE_EFFECT"
            assert t["applied"] is True and t["allowed"] is True   # legal + bound


def test_side_effect_label_survives_deterministic_rerun():
    a, _ = _run("S01")
    b, _ = _run("S01")
    assert a.artifacts["trace"] == b.artifacts["trace"]
    labels_a = [t.get("fixture_side_effect") for t in a.artifacts["trace"] if t.get("institutional")]
    labels_b = [t.get("fixture_side_effect") for t in b.artifacts["trace"] if t.get("institutional")]
    assert labels_a == labels_b == [True] * len(labels_a)