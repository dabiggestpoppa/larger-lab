"""G2 scenario execution — S01..S05 (+ S01 weak variant).

Every scenario must produce its expected phase trace FROM OBSERVABLE EVIDENCE
(nothing in stimulus_events.jsonl is a phase event), keep expectations and
hidden ground truth out of the decision path, and preserve knowledge lineage.
No scenario-name logic exists in the generic engine; these assertions validate
the scenario DATA.
"""
import json
from pathlib import Path

import pytest

from engine.scenariolib import load_all_packs, load_scenario_pack
from engine.scenario import run_scenario, evaluate_expectation, decision_view
from engine.base import KnowledgeLifecycleState

SCENARIOS_ROOT = Path(__file__).resolve().parent.parent / "scenarios"
PACKS = load_all_packs(SCENARIOS_ROOT)
MAIN = ["S01", "S02", "S03", "S04", "S05"]


def _run(sid):
    pack = PACKS[sid]
    return run_scenario(pack.spec, pack.contract, pack.policy), pack


# --------------------------------------------------------------------------- #
# execution honesty: traces derived from evidence, expectations sealed
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("sid", MAIN + ["S01_WEAK"])
def test_scenario_follows_expected_trace_from_evidence(sid):
    res, pack = _run(sid)
    verdict = evaluate_expectation(res, pack.spec)
    assert verdict["pass"], f"{sid} failures: {verdict['failures']}"
    assert len(res.artifacts["actual_phase_trace"]) >= 2
    # expectations did not participate
    assert res.artifacts["expected_trace_accessed"] is False
    assert res.artifacts["hidden_ground_truth_accessed"] is False


@pytest.mark.parametrize("sid", MAIN + ["S01_WEAK"])
def test_no_forbidden_attempts_in_clean_scenarios(sid):
    res, _ = _run(sid)
    assert res.artifacts["forbidden_attempts"] == []


@pytest.mark.parametrize("sid", MAIN + ["S01_WEAK"])
def test_scenario_json_contains_no_expected_fields(sid):
    raw = json.loads((SCENARIOS_ROOT / PACKS[sid].path.name / "scenario.json").read_text(encoding="utf-8"))
    for key in ("expected_phase_path", "expected_terminal_knowledge", "terminal_states", "hidden_ground_truth"):
        assert key not in raw, f"{sid}/scenario.json must not contain {key}"


@pytest.mark.parametrize("sid", MAIN + ["S01_WEAK"])
def test_stimulus_stream_has_no_scripted_phase_events(sid):
    """G2 §2: stimulus events must never directly encode the phase path."""
    path = SCENARIOS_ROOT / PACKS[sid].path.name / "stimulus_events.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        assert ev.get("machine", "evidence") != "phase"
        payload = ev.get("payload") or {}
        assert "to_state" not in payload
        assert "evidence_vector" in ev  # observations carry evidence, not phases


@pytest.mark.parametrize("sid", MAIN)
def test_expected_trace_sealed_metamorphic(sid):
    pack = PACKS[sid]
    base = run_scenario(pack.spec, pack.contract, pack.policy)
    spec2 = pack.spec.to_dict()
    spec2["expected_phase_path"] = ["STABLE", "NEW_STABLE", "ROLLBACK", "NOPE"]  # intentional garbage
    spec2.pop("expected_terminal_knowledge", None)
    spec2.pop("terminal_states", None)
    from engine.fixtures import StressScenarioSpec
    tampered = StressScenarioSpec(**spec2)
    res2 = run_scenario(tampered, pack.contract, pack.policy)
    # execution is byte-identical; only the post-hoc verdict differs
    assert base.artifacts["fingerprint"] == res2.artifacts["fingerprint"]
    assert base.artifacts["actual_phase_trace"] == res2.artifacts["actual_phase_trace"]
    assert evaluate_expectation(res2, tampered)["pass"] is False
    assert evaluate_expectation(base, tampered)["pass"] is False


def test_hidden_ground_truth_sealed_metamorphic():
    pack = PACKS["S03"]
    spec = pack.spec.to_dict()
    from engine.fixtures import StressScenarioSpec
    base = run_scenario(pack.spec, pack.contract, pack.policy)
    spec["hidden_ground_truth"] = {"shared_assumption": "SIG_C", "revision_matrix": "NOT LEAKED"}
    with_truth = StressScenarioSpec(**spec)
    res = run_scenario(with_truth, pack.contract, pack.policy)
    assert base.artifacts["fingerprint"] == res.artifacts["fingerprint"]
    assert "hidden_ground_truth" not in decision_view(with_truth)


def test_evaluation_contract_frozen_and_recorded_before_first_decision():
    res, pack = _run("S01")
    meta = res.artifacts["evaluation_contract"]
    assert meta["freeze_status"] == "FROZEN"
    assert pack.contract.is_frozen()
    assert meta["fingerprint"] == pack.contract.fingerprint()
    assert meta["contract_id"] == "S01-EVAL-V1"


def test_evidence_refs_recorded_for_every_material_transition():
    res, _ = _run("S01")
    refs = res.artifacts["evidence_refs_by_transition"]
    assert refs  # non-empty
    for seq, ids in refs.items():
        assert ids, f"transition at seq {seq} lacks evidence refs"


def test_committed_run_receipts_match_a_fresh_run():
    """The evidence receipts on disk must reproduce exactly: same fingerprint,
    same verdict. Guards against drift between committed evidence and code."""
    for sid, pack in PACKS.items():
        receipt_path = pack.path / "run_receipt.json"
        assert receipt_path.exists(), f"missing receipt for {sid}"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        res = run_scenario(pack.spec, pack.contract, pack.policy)
        assert res.artifacts["fingerprint"] == receipt["fingerprint"], sid
        assert receipt["pass"] == (evaluate_expectation(res, pack.spec)["pass"]), sid
        assert res.artifacts["actual_phase_trace"] == receipt["actual_phase_trace"], sid


def test_runs_are_deterministic():
    for sid in MAIN:
        a, _ = _run(sid)
        b, _ = _run(sid)
        assert a.artifacts["fingerprint"] == b.artifacts["fingerprint"]


# --------------------------------------------------------------------------- #
# knowledge-lifecycle preservation
# --------------------------------------------------------------------------- #
def test_s01_old_mechanism_retained_not_deleted():
    res, _ = _run("S01")
    kn = res.artifacts["terminal_knowledge_states"]
    assert kn["@M_A"] == KnowledgeLifecycleState.SUPERSEDED.value
    assert kn["@M_B"] == KnowledgeLifecycleState.ACTIVE.value
    # provenance survives SUPERSEDED (lineage retained, reopen path exists)
    pack = PACKS["S01"]
    rec = next(r for r in pack.spec.initial_knowledge if r["record_id"] == "@M_A")
    assert rec["provenance_source_kind"] == "FIXTURE"


def test_s02_failed_claim_is_demoted_with_reopen_conditions():
    res, _ = _run("S02")
    assert res.artifacts["terminal_knowledge_states"]["@K_REV"] == "DEMOTED"
    # the demotion reason carries the reopen condition and defect evidence
    inst_entries = [t for t in res.artifacts["trace"] if t.get("institutional")]
    demote = [t for t in inst_entries if t.get("to") == "DEMOTED"]
    assert demote, "expected a governed demotion action"
    assert "reopen" in demote[0]["rationale"]
    # the revolutionary claim never reached PROMOTED/ACTIVE
    assert "PROMOTED" not in str(res.artifacts["trace"])
    assert all(t.get("to") != "ACTIVE" for t in inst_entries)


def test_s02_bad_dataset_and_anomaly_not_erased():
    pack = PACKS["S02"]
    ids = {r["record_id"] for r in pack.observable_evidence}
    assert {"E_LEAK", "E_SURV", "E_NOVEL"} <= ids  # defects + original novelty retained on disk
    res, _ = _run("S02")
    all_refs = [ref for refs in res.artifacts["evidence_refs_by_transition"].values() for ref in refs]
    assert "E_NOVEL" in all_refs  # the original anomaly lineage proves it stayed in the chain


def test_s03_s04_no_knowledge_mutation():
    for sid in ("S03", "S04"):
        res, _ = _run(sid)
        assert res.artifacts["terminal_knowledge_states"] == {}


def test_s05_plural_knowledge_preserved_while_phase_stable():
    res, _ = _run("S05")
    assert res.artifacts["terminal_phase"] == "STABLE"
    kn = res.artifacts["terminal_knowledge_states"]
    assert kn == {"@M_A": "ACTIVE", "@M_B": "ACTIVE"}
    # no synthetic compromise model was created
    assert "@M_AVG" not in kn
    # M4/M5 separation: plural ACTIVE knowledge coexists with STABLE phase
    assert res.artifacts["actual_phase_trace"][-2] == "PLURAL_MODEL_STATE"


# --------------------------------------------------------------------------- #
# cross-scenario contrast (evidence shape, not scenario IDs)
# --------------------------------------------------------------------------- #
def test_s01_vs_s02_persistent_structural_vs_false_novelty():
    s01, _ = _run("S01")
    s02, _ = _run("S02")
    s01_tokens = {"TRANSFORMATION_CANDIDATE", "TRANSFORMATION_WINDOW", "RECONSOLIDATION", "NEW_STABLE"}
    assert s01_tokens <= set(s01.artifacts["actual_phase_trace"])
    assert not (s01_tokens & set(s02.artifacts["actual_phase_trace"]))  # S02 never transformed
    # both opened WATCH and escalated for review (that part is shared)
    assert "ESCALATION_REVIEW" in s02.artifacts["actual_phase_trace"]


def test_s03_vs_s04_repeated_shared_signature_escalates_leaf_stays_local():
    s03, _ = _run("S03")
    s04, _ = _run("S04")
    assert s03.artifacts["terminal_phase"] == "TRANSFORMATION_CANDIDATE"
    assert s04.artifacts["terminal_phase"] == "STABLE"
    assert "TRANSFORMATION_CANDIDATE" not in s04.artifacts["actual_phase_trace"]
    assert s04.artifacts["forbidden_attempts"] == []
    # S03 escalation only after the SAME causal signature reached >= L3 with recurrence >= 3
    assert len(s03.artifacts["actual_phase_trace"]) > len(s04.artifacts["actual_phase_trace"])


def test_s01_weak_variant_no_transformation_despite_core_centrality():
    res, _ = _run("S01_WEAK")
    trace = res.artifacts["actual_phase_trace"]
    assert trace == ["STABLE", "WATCH", "STABLE", "WATCH", "STABLE"]
    blocked = {"ESCALATION_REVIEW", "TRANSFORMATION_CANDIDATE", "TRANSFORMATION_WINDOW",
               "RECONSOLIDATION", "NEW_STABLE", "PLURAL_MODEL_STATE"}
    assert not (blocked & set(trace))  # centrality alone is not the cause
    # every observation carried CORE (HIGH) centrality — the sensitivity is real
    path = SCENARIOS_ROOT / PACKS["S01_WEAK"].path.name / "stimulus_events.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        ev = json.loads(line)
        assert ev["evidence_vector"]["dependency_centrality"] == "HIGH"


def test_s01_vs_s05_both_transform_but_outcomes_differ():
    s01, p01 = _run("S01")
    s05, p05 = _run("S05")
    # S01: contradiction resolved -> NEW_STABLE; S05: multiplicity unresolved -> PLURAL_MODEL_STATE
    assert s01.artifacts["actual_phase_trace"][-1] in ("NEW_STABLE",)
    assert s05.artifacts["actual_phase_trace"][-2] == "PLURAL_MODEL_STATE"
    # knowledge mirrors the distinction
    assert s05.artifacts["terminal_knowledge_states"]["@M_A"] == "ACTIVE"
    assert s01.artifacts["terminal_knowledge_states"]["@M_A"] == "SUPERSEDED"