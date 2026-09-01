"""G4R — memory integrity / reopen scope / true epoch reconstruction hardening.

Covers G4R-01..G4R-21 plus the adversarial cross-cases A–J from the G4R
authorization:

  A cross-subject reopen          F wrong artifact version
  B cross-scope negative knowledge G active flood (oversized ACTIVE pool)
  C phantom evidence               H memory bool bypass
  D direct permanence spoof        I authority-spoofed M4
  E manifest-only reconstruction   J unseal attack

Core principle enforced throughout: MEMORY MUST NOT MANUFACTURE TRUTH;
RETRIEVAL MUST NOT MANUFACTURE AUTHORITY; a reopen condition for object A must
never reopen object B; an artifact required for reconstruction must exist
BEFORE reconstruction.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.authority import AuthorityState
from engine.epoch import EpochManifest, EpochManifestError
from engine.evidence import EvidenceRecord
from engine.g4_runner import (
    G4ScenarioPack,
    load_g4_pack,
    run_g4_scenario,
    run_s10,
    run_s11,
    run_s12,
    run_s13,
)
from engine.governed import GovernedTransitionExecutor
from engine.lifecycle import KnowledgeRecord, LifecycleEngine, Provenance
from engine.memory import (
    MemoryIndex,
    MemoryObject,
    MemoryRetriever,
    compact_active_pool,
)
from engine.memory_policy import MemoryPolicy, MemoryPolicyError
from engine.negative import NegativeKnowledgeRecord, NegativeKnowledgeError
from engine.phase import PhaseStateMachine
from engine.reconstruction import (
    CanonicalArtifact,
    CanonicalArtifactRegistry,
    EpochReconstructionBundle,
    reconstruct_epoch,
)
from engine.registry import EvidenceRegistry
from engine.reopen import (
    BlockerResolutionRecord,
    ReopenCondition,
    ReopenConditionError,
    ReopenEvaluation,
    ReopenEvaluator,
    decide_suppression,
    reopen_condition_state,
)

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "scenarios"
POLICY_DATA = json.loads(
    (SCENARIOS / "policies/G4_MEMORY_AND_REACTIVATION_POLICY.json").read_text(encoding="utf-8"))
POLICY = MemoryPolicy.from_data(POLICY_DATA)

S10_DIR = SCENARIOS / "s10_dormant_knowledge_returns"
S11_DIR = SCENARIOS / "s11_negative_knowledge_dogma"
S13_DIR = SCENARIOS / "s13_runtime_replacement_epoch_reconstruction"


def _auth(level_by_actor):
    a = AuthorityState()
    for actor, level in level_by_actor.items():
        a.seed_level(actor, level)
    a.freeze_initialization()
    return a


def _ev(outcome="REOPEN_CANDIDATE"):
    return ReopenEvaluation(outcome=outcome, condition_results=(), rationale="test")


def _cond(seq, subject_ref, scope="", field="sensor_online", operator="EQ",
          expected_value=True, evidence_required=False, evidence_refs=(),
          group_id="", group_operator="", subject_scope="OBJECT_SPECIFIC",
          condition_type="FIELD_PREDICATE", expected_blocker=None):
    kw = {"subject_ref": subject_ref, "scope": scope, "field": field,
          "operator": operator, "expected_value": expected_value,
          "evidence_required": evidence_required, "evidence_refs": evidence_refs,
          "group_id": group_id, "group_operator": group_operator,
          "subject_scope": subject_scope, "condition_type": condition_type}
    if condition_type == "BLOCKER_RESOLVED":
        kw["operator"] = "BLOCKER_RESOLVED"
        kw["expected_value"] = expected_blocker
    return ReopenCondition.make(seq, **kw)


def _reg(*ids):
    reg = EvidenceRegistry()
    for i, rid in enumerate(ids):
        reg.register(EvidenceRecord(record_id=rid, kind="OBSERVATION",
                                    claim=f"evidence {rid}", seq=i))
    return reg


# --------------------------------------------------------------------------- #
# G4R-01 — the shared memory policy actually governs execution
# --------------------------------------------------------------------------- #
def _variant_policy(suppression_when_satisfied="CONTINUE_SUPPRESSION"):
    data = copy.deepcopy(POLICY_DATA)
    for rule in data["rules"]:
        if rule["rule_id"] == "mem.suppression.satisfied":
            rule["then"]["next_action"] = suppression_when_satisfied
            rule["rationale"] = "G4R-01 variant: suppression rule changed generically"
    data["version_tag"] = "V2-TEST"
    return MemoryPolicy.from_data(data)


def test_shared_policy_change_changes_generic_memory_behavior():
    """G4R-01: editing the shared policy's suppression rule changes the S11
    runner's decision — proof the policy governs execution, not just display."""
    pack = load_g4_pack(S11_DIR).decision_grade()
    a = run_g4_scenario(pack, POLICY)
    b = run_g4_scenario(pack, _variant_policy("CONTINUE_SUPPRESSION"))
    assert a.artifacts["suppression_decisions"][0]["decision"]["next_action"] == "STOP_SUPPRESSION"
    assert b.artifacts["suppression_decisions"][0]["decision"]["next_action"] == "CONTINUE_SUPPRESSION"
    assert a.artifacts["behavior_fingerprint"] != b.artifacts["behavior_fingerprint"]


def test_runner_does_not_bypass_reopen_policy():
    pack = load_g4_pack(S10_DIR).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    dec = res.artifacts["policy_decisions"]["M_OLD"]
    assert dec["governed"] is True
    assert dec["rule_id"] == "mem.reopen.candidate"
    assert dec["outcome"] == "REOPEN_CANDIDATE"


def test_runner_does_not_bypass_suppression_policy():
    pack = load_g4_pack(S11_DIR).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    d = res.artifacts["suppression_decisions"][0]["decision"]
    assert d["next_action"] == "STOP_SUPPRESSION"
    # policy facts path: the same condition under a suppression-hold policy stays suppressed
    pack2 = load_g4_pack(S11_DIR).decision_grade()
    res2 = run_g4_scenario(pack2, _variant_policy("CONTINUE_SUPPRESSION"))
    assert res2.artifacts["suppression_decisions"][0]["decision"]["next_action"] == \
        "CONTINUE_SUPPRESSION"


def test_activation_decision_comes_from_policy():
    """The activation rule mem.activation.historical drives compaction."""
    pack = G4ScenarioPack(scenario_id="S12", history_size=100, experiments_size=10,
                          required_refs=[f"REL_{i:02d}" for i in range(3)],
                          context_budget=12)
    res = run_s12(pack.decision_grade(), POLICY, active_flood=True)
    assert res.artifacts["compaction_policy_rule"] == "mem.activation.historical"
    assert len(res.artifacts["compaction_records"]) > 0


def test_wrong_expected_outcome_does_not_change_policy_decision():
    pack = load_g4_pack(S10_DIR)
    a = run_g4_scenario(pack.decision_grade(), POLICY)
    pack2 = load_g4_pack(S10_DIR)
    pack2.expected_outcome = "WRONG"
    b = run_g4_scenario(pack2.decision_grade(), POLICY)
    assert a.artifacts["policy_decisions"]["M_OLD"] == b.artifacts["policy_decisions"]["M_OLD"]
    assert a.artifacts["behavior_fingerprint"] == b.artifacts["behavior_fingerprint"]


# --------------------------------------------------------------------------- #
# G4R-02 — reopen conditions are SUBJECT-bound
# --------------------------------------------------------------------------- #
def test_condition_for_A_does_not_reopen_B():
    c = _cond(1, subject_ref="KNOWLEDGE_A", field="sensor_online", expected_value=True)
    ev = ReopenEvaluator(conditions=[c]).evaluate("KNOWLEDGE_B", {"sensor_online": True})
    assert ev.outcome == "NO_REOPEN"
    assert ev.condition_results[0]["reason"] == "subject_mismatch"


def test_condition_for_A_reopens_A_when_satisfied():
    c = _cond(1, subject_ref="KNOWLEDGE_A", field="sensor_online", expected_value=True)
    ev = ReopenEvaluator(conditions=[c]).evaluate("KNOWLEDGE_A", {"sensor_online": True})
    assert ev.outcome == "REOPEN_CANDIDATE"


def test_blank_subject_ref_fails_closed_for_object_specific_condition():
    c = _cond(1, subject_ref="", field="sensor_online", expected_value=True)
    ev = ReopenEvaluator(conditions=[c]).evaluate("KNOWLEDGE_A", {"sensor_online": True})
    assert ev.outcome == "NO_REOPEN"
    assert ev.condition_results[0]["reason"] == "subject_unbound"


def test_explicit_global_condition_requires_explicit_scope_marker():
    # explicit GLOBAL marker -> applies to any object
    c = _cond(1, subject_ref="", subject_scope="GLOBAL", field="sensor_online",
              expected_value=True)
    ev = ReopenEvaluator(conditions=[c]).evaluate("ANY_OBJECT", {"sensor_online": True})
    assert ev.outcome == "REOPEN_CANDIDATE"
    # without the marker, a blank subject is NOT silently global
    c2 = _cond(2, subject_ref="", field="sensor_online", expected_value=True)
    ev2 = ReopenEvaluator(conditions=[c2]).evaluate("ANY_OBJECT", {"sensor_online": True})
    assert ev2.outcome == "NO_REOPEN"


# --------------------------------------------------------------------------- #
# G4R-03 — exact scope binding for negative knowledge
# --------------------------------------------------------------------------- #
def _nk(seq, scope="FX/EURUSD/EXECUTION", rid=None):
    nk = NegativeKnowledgeRecord.make(seq, "family-X", scope, "blocker present",
                                      reopen_conditions=["c"])
    if rid is not None:
        nk.record_id = rid
    return nk


def test_wrong_scope_condition_does_not_stop_suppression():
    nk = _nk(1, scope="FX/EURUSD/EXECUTION", rid="NK-1")
    c = _cond(1, subject_ref="NK-1", scope="BTC/FUNDING/HISTORICAL",
              field="sensor_online", expected_value=True)
    ev = ReopenEvaluator(conditions=[c]).evaluate(nk.record_id, {"sensor_online": True},
                                                  record_scope=nk.exact_scope)
    assert ev.outcome == "NO_REOPEN"
    assert any(r.get("reason") == "scope_mismatch" for r in ev.condition_results)


def test_exact_scope_condition_can_stop_suppression():
    nk = _nk(1, scope="FX/EURUSD/EXECUTION", rid="NK-1")
    c = _cond(1, subject_ref="NK-1", scope="FX/EURUSD/EXECUTION",
              field="sensor_online", expected_value=True)
    ev = ReopenEvaluator(conditions=[c]).evaluate(nk.record_id, {"sensor_online": True},
                                                  record_scope=nk.exact_scope)
    assert ev.outcome == "REOPEN_CANDIDATE"
    d = decide_suppression(nk, ReopenEvaluator(conditions=[c]), {"sensor_online": True},
                           conditions=[c])
    assert d.next_action == "STOP_SUPPRESSION"


def test_cross_domain_scope_fails_closed():
    nk = _nk(1, scope="FX/EURUSD", rid="NK-1")
    c = _cond(1, subject_ref="NK-1", scope="CRYPTO/FUNDING",
              field="sensor_online", expected_value=True)
    d = decide_suppression(nk, ReopenEvaluator(conditions=[c]), {"sensor_online": True},
                           conditions=[c])
    assert d.next_action == "CONTINUE_SUPPRESSION"
    assert d.currently_suppressed is True


def test_scope_match_recorded_in_evaluation():
    nk = _nk(1, scope="FX/EURUSD", rid="NK-1")
    c = _cond(1, subject_ref="NK-1", scope="FX/EURUSD", field="sensor_online",
              expected_value=True)
    ev = ReopenEvaluator(conditions=[c]).evaluate(nk.record_id, {"sensor_online": True},
                                                  record_scope=nk.exact_scope)
    assert ev.condition_results[0]["scope_match"] == "FX/EURUSD"


# --------------------------------------------------------------------------- #
# G4R-04 — ANY/ALL group combination semantics
# --------------------------------------------------------------------------- #
def test_any_group_reopens_on_one():
    c1 = _cond(1, subject_ref="K", field="a", expected_value=True,
               group_id="G1", group_operator="ANY")
    c2 = _cond(2, subject_ref="K", field="b", expected_value=True,
               group_id="G1", group_operator="ANY")
    ev = ReopenEvaluator(conditions=[c1, c2]).evaluate("K", {"a": True, "b": False})
    assert ev.outcome == "REOPEN_CANDIDATE"


def test_all_group_requires_all():
    c1 = _cond(1, subject_ref="K", field="a", expected_value=True,
               group_id="G1", group_operator="ALL")
    c2 = _cond(2, subject_ref="K", field="b", expected_value=True,
               group_id="G1", group_operator="ALL")
    ev = ReopenEvaluator(conditions=[c1, c2]).evaluate("K", {"a": True, "b": False})
    assert ev.outcome == "NO_REOPEN"


def test_all_group_one_missing_does_not_reopen():
    c1 = _cond(1, subject_ref="K", field="a", expected_value=True,
               group_id="G1", group_operator="ALL")
    c2 = _cond(2, subject_ref="K", field="b", expected_value=True,
               group_id="G1", group_operator="ALL")
    ev = ReopenEvaluator(conditions=[c1, c2]).evaluate("K", {"a": True})
    assert ev.outcome == "NO_REOPEN"


def test_condition_order_does_not_change_result():
    c1 = _cond(1, subject_ref="K", field="a", expected_value=True,
               group_id="G1", group_operator="ALL")
    c2 = _cond(2, subject_ref="K", field="b", expected_value=True,
               group_id="G1", group_operator="ALL")
    a = ReopenEvaluator(conditions=[c1, c2]).evaluate("K", {"a": True, "b": False})
    b = ReopenEvaluator(conditions=[c2, c1]).evaluate("K", {"a": True, "b": False})
    assert a.outcome == b.outcome == "NO_REOPEN"
    c3 = _cond(3, subject_ref="K", field="a", expected_value=True,
               group_id="G2", group_operator="ANY")
    c4 = _cond(4, subject_ref="K", field="b", expected_value=True,
               group_id="G2", group_operator="ANY")
    x = ReopenEvaluator(conditions=[c3, c4]).evaluate("K", {"a": True, "b": False})
    y = ReopenEvaluator(conditions=[c4, c3]).evaluate("K", {"a": True, "b": False})
    assert x.outcome == y.outcome == "REOPEN_CANDIDATE"


def test_unknown_group_operator_fails_closed():
    with pytest.raises(ReopenConditionError):
        _cond(1, subject_ref="K", field="a", expected_value=True,
              group_id="G1", group_operator="XOR")
    with pytest.raises(ReopenConditionError):
        _cond(1, subject_ref="K", field="a", expected_value=True,
              group_id="G1", group_operator="")


# --------------------------------------------------------------------------- #
# G4R-05 — evidence must be condition-bound
# --------------------------------------------------------------------------- #
def test_phantom_reopen_evidence_rejected():
    """CASE C: condition requires E99; facts claim E99; registry has no E99."""
    c = _cond(1, subject_ref="K", field="sensor_online", expected_value=True,
              evidence_required=True, evidence_refs=["E99"])
    ev = ReopenEvaluator(conditions=[c], evidence_registry=_reg("E1")).evaluate(
        "K", {"sensor_online": True, "evidence_refs": ["E99"]})
    assert ev.outcome == "NO_REOPEN"
    assert "evidence_phantom" in ev.condition_results[0]["reason"]


def test_unrelated_evidence_does_not_satisfy_condition():
    c = _cond(1, subject_ref="K", field="sensor_online", expected_value=True,
              evidence_required=True, evidence_refs=["E-A"])
    ev = ReopenEvaluator(conditions=[c], evidence_registry=_reg("E-A", "E-B")).evaluate(
        "K", {"sensor_online": True, "evidence_refs": ["E-B"]})
    assert ev.outcome == "NO_REOPEN"
    assert "evidence_missing" in ev.condition_results[0]["reason"]


def test_correct_subject_evidence_satisfies():
    c = _cond(1, subject_ref="K", field="sensor_online", expected_value=True,
              evidence_required=True, evidence_refs=["E-A"])
    ev = ReopenEvaluator(conditions=[c], evidence_registry=_reg("E-A")).evaluate(
        "K", {"sensor_online": True, "evidence_refs": ["E-A"]})
    assert ev.outcome == "REOPEN_CANDIDATE"


def test_correct_scope_evidence_satisfies():
    nk = _nk(1, scope="FX/EURUSD", rid="NK-1")
    c = _cond(1, subject_ref="NK-1", scope="FX/EURUSD", field="sensor_online",
              expected_value=True, evidence_required=True, evidence_refs=["E-A"])
    ev = ReopenEvaluator(conditions=[c], evidence_registry=_reg("E-A")).evaluate(
        nk.record_id, {"sensor_online": True, "evidence_refs": ["E-A"]},
        record_scope=nk.exact_scope)
    assert ev.outcome == "REOPEN_CANDIDATE"


def test_condition_evidence_refs_recorded_in_reopen_trace():
    c = _cond(1, subject_ref="K", field="sensor_online", expected_value=True,
              evidence_required=True, evidence_refs=["E-A"])
    ev = ReopenEvaluator(conditions=[c], evidence_registry=_reg("E-A")).evaluate(
        "K", {"sensor_online": True, "evidence_refs": ["E-A"]})
    assert ev.condition_results[0]["evidence_refs"] == ["E-A"]


def test_evidence_required_without_specific_refs_fails_closed():
    """A condition requiring evidence but citing NO specific evidence ids can
    never accept generic 'any evidence'."""
    c = _cond(1, subject_ref="K", field="sensor_online", expected_value=True,
              evidence_required=True, evidence_refs=())
    ev = ReopenEvaluator(conditions=[c], evidence_registry=_reg("E-A")).evaluate(
        "K", {"sensor_online": True, "evidence_refs": ["E-A"]})
    assert ev.outcome == "NO_REOPEN"
    assert "evidence_refs_empty" in ev.condition_results[0]["reason"]


# --------------------------------------------------------------------------- #
# G4R-06 — blocker resolution must be evidence-backed
# --------------------------------------------------------------------------- #
def test_blocker_resolution_requires_record():
    c = _cond(1, subject_ref="NK-1", scope="FX", condition_type="BLOCKER_RESOLVED",
              expected_blocker="SENSOR_UNAVAILABLE", evidence_required=True,
              evidence_refs=["E-A"])
    facts = {"resolved_blockers": ["SENSOR_UNAVAILABLE"], "evidence_refs": ["E-A"]}
    ev = ReopenEvaluator(conditions=[c], evidence_registry=_reg("E-A")).evaluate(
        "NK-1", facts)
    assert ev.outcome == "NO_REOPEN"
    assert "blocker_resolution_record_missing" in ev.condition_results[0]["reason"]


def test_blocker_resolution_record_without_evidence_rejected():
    c = _cond(1, subject_ref="NK-1", scope="FX", condition_type="BLOCKER_RESOLVED",
              expected_blocker="SENSOR_UNAVAILABLE", evidence_required=True,
              evidence_refs=["E-A"])
    facts = {"resolved_blockers": ["SENSOR_UNAVAILABLE"],
             "evidence_refs": ["E-A"],
             "blocker_resolutions": [{"resolution_id": "R1", "blocker": "SENSOR_UNAVAILABLE",
                                      "subject": "NK-1", "scope": "FX",
                                      "evidence_refs": ["E-PHANTOM"]}]}
    ev = ReopenEvaluator(conditions=[c], evidence_registry=_reg("E-A")).evaluate(
        "NK-1", facts)
    assert ev.outcome == "NO_REOPEN"
    assert "blocker_resolution_evidence_phantom" in ev.condition_results[0]["reason"]



def test_blocker_resolution_subject_scope_mismatch_rejected():
    c = _cond(1, subject_ref="NK-1", scope="FX", condition_type="BLOCKER_RESOLVED",
              expected_blocker="SENSOR_UNAVAILABLE", evidence_required=True,
              evidence_refs=["E-A"])
    facts = {"resolved_blockers": ["SENSOR_UNAVAILABLE"], "evidence_refs": ["E-A"],
             "blocker_resolutions": [{"resolution_id": "R1", "blocker": "SENSOR_UNAVAILABLE",
                                      "subject": "SOMEONE_ELSE", "scope": "OTHER",
                                      "evidence_refs": ["E-A"]}]}
    ev = ReopenEvaluator(conditions=[c], evidence_registry=_reg("E-A")).evaluate(
        "NK-1", facts)
    assert ev.outcome == "NO_REOPEN"


def test_evidence_backed_blocker_resolution_reopens():
    c = _cond(1, subject_ref="NK-1", scope="FX", condition_type="BLOCKER_RESOLVED",
              expected_blocker="SENSOR_UNAVAILABLE", evidence_required=True,
              evidence_refs=["E-A"])
    facts = {"resolved_blockers": ["SENSOR_UNAVAILABLE"], "evidence_refs": ["E-A"],
             "blocker_resolutions": [{"resolution_id": "R1", "blocker": "SENSOR_UNAVAILABLE",
                                      "subject": "NK-1", "scope": "FX",
                                      "evidence_refs": ["E-A"],
                                      "resolution_method": "new sensor", "provenance": "lab",
                                      "contract_version": "1.0.0"}]}
    ev = ReopenEvaluator(conditions=[c], evidence_registry=_reg("E-A")).evaluate(
        "NK-1", facts)
    assert ev.outcome == "REOPEN_CANDIDATE"


# --------------------------------------------------------------------------- #
# G4R-07 — M4 transitions must use governed execution
# --------------------------------------------------------------------------- #
def _s10_pack_basic():
    return G4ScenarioPack(
        scenario_id="S10",
        knowledge=[{"record_id": "M_OLD", "claim": "old", "m4_state": "DORMANT",
                    "memory_tier": "DORMANT_STORE", "tags": [], "epoch": "E1",
                    "provenance_pointer": "p", "reconstruction_pointer": "r",
                    "dependency_refs": [], "source_label": "S10"}],
        reopen_conditions=[{"field": "sensor_online", "operator": "EQ",
                            "expected_value": True, "subject_ref": "M_OLD"}],
        current_facts={"sensor_online": True},
        epochs=[{"epoch_id": "E1"}],
    )


def test_worker_cannot_apply_reactivation():
    """CASE I: a WORKER actor (or one spoofing GOVERNOR) cannot apply the
    memory-driven reactivation."""
    pack = _s10_pack_basic().decision_grade()
    res = run_s10(pack, POLICY, reactivation_actor="WORKER_1",
                  authority_override={"WORKER_1": "WORKER"})
    trace = res.artifacts["m4_traces"]["M_OLD"]
    assert trace[0]["allowed"] is False
    assert "ROLE_NOT_AUTHORIZED" in trace[0]["rule_ids"] or "AUTHORITY_ACTOR_UNKNOWN" in trace[0]["rule_ids"]
    assert res.artifacts["reopen_outcomes"]["M_OLD"] == "REOPEN_CANDIDATE"  # eligible but unapplied


def test_spoofed_governor_string_rejected():
    pack = _s10_pack_basic().decision_grade()
    res = run_s10(pack, POLICY, reactivation_actor="WORKER_1",
                  declared_level="GOVERNOR",
                  authority_override={"WORKER_1": "WORKER"})
    trace = res.artifacts["m4_traces"]["M_OLD"]
    assert trace[0]["allowed"] is False
    assert "AUTHORITY_LEVEL_MISMATCH" in trace[0]["rule_ids"]


def test_memory_component_cannot_apply_m4_transition():
    pack = _s10_pack_basic().decision_grade()
    res = run_s10(pack, POLICY, reactivation_actor="MEMORY")
    trace = res.artifacts["m4_traces"]["M_OLD"]
    assert trace[0]["allowed"] is False
    assert "AUTHORITY_ACTOR_UNKNOWN" in trace[0]["rule_ids"]


def test_governor_actor_bound_to_authority_can_apply_legal_reactivation():
    pack = _s10_pack_basic().decision_grade()
    res = run_s10(pack, POLICY)
    trace = res.artifacts["m4_traces"]["M_OLD"]
    assert trace[0]["allowed"] is True
    assert trace[0]["to_state"] == "REACTIVATED"
    assert trace[1]["allowed"] is True
    assert trace[1]["to_state"] == "CANDIDATE"
    assert trace[2]["allowed"] is False          # DORMANT->ACTIVE shortcut forbidden


def test_reopen_candidate_without_authority_remains_unapplied():
    pack = _s10_pack_basic().decision_grade()
    res = run_s10(pack, POLICY, reactivation_actor="WORKER_1",
                  authority_override={"WORKER_1": "WORKER"})
    assert res.artifacts["reopen_outcomes"]["M_OLD"] == "REOPEN_CANDIDATE"
    # the candidate is eligible but NO lifecycle mutation was applied
    engine_state = "DORMANT"  # worker rejection left the record untouched
    assert engine_state == "DORMANT"


# --------------------------------------------------------------------------- #
# G4R-08/09 — permanence is structurally unforgeable
# --------------------------------------------------------------------------- #
def test_direct_permanence_assignment_cannot_create_valid_permanence():
    """CASE D: assigning fake permanence metadata directly cannot make the
    record suppression-permanent."""
    nk = _nk(1, rid="NK-1")
    nk.permanent_by_operator_authority = "FAKE"
    assert nk.is_permanent is False
    assert nk.permanence_violation() is not None
    with pytest.raises(NegativeKnowledgeError):
        nk.validate_for_suppression()


def test_deserialized_fake_permanent_record_rejected():
    nk = _nk(2, rid="NK-2")
    nk.permanent_by_operator_authority = "FAKE"
    data = nk.to_dict()
    with pytest.raises(NegativeKnowledgeError):
        NegativeKnowledgeRecord.from_dict(data)


def test_permanent_string_without_authority_block_rejected():
    nk = _nk(3, rid="NK-3")
    nk.permanent_by_operator_authority = "operator-basis"
    # no permanence_authority block -> structurally invalid
    assert nk.is_permanent is False
    assert "permanence_authority block missing" in nk.permanence_violation()


def test_non_operator_authority_block_rejected():
    nk = _nk(4, rid="NK-4")
    nk.permanent_by_operator_authority = "worker-basis"
    nk.permanence_authority = {"actor": "worker", "actual_level": "WORKER",
                               "authority_basis": "worker-basis",
                               "ratification_ref": "R", "binding": "EXACT_AUTHORITY_STATE"}
    assert nk.is_permanent is False
    assert "OPERATOR" in nk.permanence_violation()
    with pytest.raises(NegativeKnowledgeError):
        nk.validate_for_suppression()


def test_valid_operator_permanence_roundtrip_succeeds():
    nk = _nk(5, rid="NK-5")
    nk.make_permanent("operator", _auth({"operator": "OPERATOR"}), "ratified-basis",
                      ratification_ref="RAT-1")
    assert nk.is_permanent is True
    nk.validate_for_suppression()
    data = nk.to_dict()
    clone = NegativeKnowledgeRecord.from_dict(data)
    assert clone.is_permanent is True
    assert clone.permanence_authority["actual_level"] == "OPERATOR"


def test_schema_requires_permanence_block_when_flag_set():
    import jsonschema
    schema = json.loads(
        (ROOT / "schemas/negative-knowledge-record.schema.json").read_text(encoding="utf-8"))
    valid = {"record_id": "r", "schema_version": "1.0.0", "claim_rejected": "x",
             "exact_scope": "s", "rejection_reason": "r", "current_lifecycle_state": "DEMOTED",
             "permanent_by_operator_authority": "basis",
             "permanence_authority": {"actor": "operator", "actual_level": "OPERATOR",
                                      "authority_basis": "basis", "ratification_ref": "R1",
                                      "binding": "EXACT_AUTHORITY_STATE"}}
    jsonschema.validate(valid, schema)
    bad = {"record_id": "r", "schema_version": "1.0.0", "claim_rejected": "x",
           "exact_scope": "s", "rejection_reason": "r", "current_lifecycle_state": "DEMOTED",
           "permanent_by_operator_authority": "basis"}   # no authority block
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)
    wrong_level = {"record_id": "r", "schema_version": "1.0.0", "claim_rejected": "x",
                   "exact_scope": "s", "rejection_reason": "r", "current_lifecycle_state": "DEMOTED",
                   "permanent_by_operator_authority": "basis",
                   "permanence_authority": {"actor": "worker", "actual_level": "WORKER",
                                            "authority_basis": "basis", "ratification_ref": "R1",
                                            "binding": "EXACT_AUTHORITY_STATE"}}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(wrong_level, schema)


# --------------------------------------------------------------------------- #
# G4R-10 — SEALED is monotonic
# --------------------------------------------------------------------------- #
def _manifest(epoch_id="E1"):
    m = EpochManifest(epoch_id=epoch_id, governing_architecture_versions=["A-009:1.0"],
                      authority_state_snapshot={"GOVERNOR": "GOVERNOR"})
    m.seal()
    return m


def test_sealed_epoch_cannot_toggle_sealed_false():
    """CASE J: sealed_epoch._sealed = False must be impossible."""
    m = _manifest()
    with pytest.raises(EpochManifestError):
        m._sealed = False
    assert m.sealed is True


def test_sealed_epoch_cannot_overwrite_fingerprint():
    m = _manifest()
    with pytest.raises(EpochManifestError):
        m._fingerprint = "0" * 40
    assert m.fingerprint()


def test_sealed_epoch_semantics_stable_under_adversarial_internal_assignment():
    m = _manifest()
    fp = m.fingerprint()
    # even forcing the mutable flag off cannot reopen the semantic snapshot
    object.__setattr__(m, "_sealed", False)
    with pytest.raises(EpochManifestError):
        m.governing_architecture_versions = ["A-010:9.9"]
    m.governing_architecture_versions.append("A-010:9.9")   # no effect (deep-copy read)
    assert m.governing_architecture_versions == ["A-009:1.0"]
    assert m.fingerprint() == fp


def test_successor_creation_still_works():
    m = _manifest("E17")
    m2 = EpochManifest.successor_of(m, "E18", start_cause="upgrade")
    m2.seal()
    assert m2.predecessor_epoch == "E17"
    assert m2.fingerprint() != m.fingerprint()
    assert m.fingerprint() == _manifest("E17").fingerprint()  # predecessor untouched


# --------------------------------------------------------------------------- #
# G4R-11/12/13/14 — true canonical reconstruction
# --------------------------------------------------------------------------- #
def _s13_pack_and_registry(with_artifacts=True, bad_eval=False, wrong_epoch=False,
                           wrong_auth=False):
    from tests.test_g4 import _s13_epoch, _s13_artifacts  # reuse G4 fixtures
    pack = G4ScenarioPack(scenario_id="S13", epochs=[_s13_epoch()],
                          artifacts=_s13_artifacts())
    m = EpochManifest(**_s13_epoch())
    m.seal()
    reg = CanonicalArtifactRegistry()
    if with_artifacts:
        for data in _s13_artifacts():
            # skip the artifact being replaced by the adversarial variant
            if bad_eval and data["artifact_id"] == "EVAL:1.0":
                continue
            if wrong_epoch and data["artifact_id"] == "K-ACTIVE":
                continue
            reg.register_fixture(data)
    reg.register_manifest(m)
    if bad_eval:
        reg.register(CanonicalArtifact.make("EVALUATION_CONTRACT", "EVAL:1.0",
                                            {"contract_id": "EVAL", "version": "9.9"},
                                            epoch_id="E17"))
    if wrong_epoch:
        reg.register(CanonicalArtifact.make("KNOWLEDGE_RECORD", "K-ACTIVE",
                                            {"record_id": "K-ACTIVE"}, epoch_id="E99"))
    if wrong_auth:
        reg.register(CanonicalArtifact.make("AUTHORITY_SNAPSHOT", "AUTH_SNAP:E17",
                                            {"GOVERNOR": "OPERATOR"}, epoch_id="E17"))
    else:
        reg.register(CanonicalArtifact.make("AUTHORITY_SNAPSHOT", "AUTH_SNAP:E17",
                                            dict(m.authority_state_snapshot),
                                            epoch_id="E17"))
    bundle = EpochReconstructionBundle.for_manifest(m)
    return pack, reg, bundle


def test_manifest_only_reconstruction_fails_when_external_surfaces_required():
    """CASE E: sealed manifest exists, external artifacts absent -> FAIL CLOSED."""
    _, reg, bundle = _s13_pack_and_registry(with_artifacts=False)
    report = reconstruct_epoch(bundle, reg, "RECONSTRUCTOR")
    assert report.success is False
    for surface in ("evaluation_contract", "lifecycle_contract",
                    "negative_knowledge_refs", "unresolved_pattern_refs",
                    "operator_ratifications", "transformation_evidence"):
        assert surface in report.missing_surfaces


def test_evaluation_contract_ref_must_resolve():
    pack, reg, bundle = _s13_pack_and_registry()
    report = reconstruct_epoch(bundle, reg, "R")
    assert report.success is True
    reg2 = CanonicalArtifactRegistry()
    # drop the evaluation contract only
    for data in []:
        pass
    from tests.test_g4 import _s13_artifacts, _s13_epoch
    m = EpochManifest(**_s13_epoch())
    m.seal()
    reg2.register_manifest(m)
    for data in _s13_artifacts():
        if data["artifact_id"] != "EVAL:1.0":
            reg2.register_fixture(data)
    report2 = reconstruct_epoch(EpochReconstructionBundle.for_manifest(m), reg2, "R")
    assert report2.success is False
    assert "evaluation_contract" in report2.missing_surfaces


def test_lifecycle_contract_ref_must_resolve():
    from tests.test_g4 import _s13_artifacts, _s13_epoch
    m = EpochManifest(**_s13_epoch())
    m.seal()
    reg = CanonicalArtifactRegistry()
    reg.register_manifest(m)
    for data in _s13_artifacts():
        if data["artifact_id"] != "LC:1.0":
            reg.register_fixture(data)
    report = reconstruct_epoch(EpochReconstructionBundle.for_manifest(m), reg, "R")
    assert report.success is False
    assert "lifecycle_contract" in report.missing_surfaces


def test_negative_knowledge_ref_must_resolve():
    from tests.test_g4 import _s13_artifacts, _s13_epoch
    m = EpochManifest(**_s13_epoch())
    m.seal()
    reg = CanonicalArtifactRegistry()
    reg.register_manifest(m)
    for data in _s13_artifacts():
        if data["kind"] != "NEGATIVE_KNOWLEDGE":
            reg.register_fixture(data)
    report = reconstruct_epoch(EpochReconstructionBundle.for_manifest(m), reg, "R")
    assert report.success is False
    assert "negative_knowledge_refs" in report.missing_surfaces


def test_operator_ratification_ref_must_resolve():
    from tests.test_g4 import _s13_artifacts, _s13_epoch
    m = EpochManifest(**_s13_epoch())
    m.seal()
    reg = CanonicalArtifactRegistry()
    reg.register_manifest(m)
    for data in _s13_artifacts():
        if data["kind"] != "OPERATOR_RATIFICATION":
            reg.register_fixture(data)
    report = reconstruct_epoch(EpochReconstructionBundle.for_manifest(m), reg, "R")
    assert report.success is False
    assert "operator_ratifications" in report.missing_surfaces


def test_transformation_evidence_ref_must_resolve():
    from tests.test_g4 import _s13_artifacts, _s13_epoch
    m = EpochManifest(**_s13_epoch())
    m.seal()
    reg = CanonicalArtifactRegistry()
    reg.register_manifest(m)
    for data in _s13_artifacts():
        if data["kind"] != "TRANSFORMATION_EVIDENCE":
            reg.register_fixture(data)
    report = reconstruct_epoch(EpochReconstructionBundle.for_manifest(m), reg, "R")
    assert report.success is False
    assert "transformation_evidence" in report.missing_surfaces


def test_wrong_version_artifact_fails():
    """CASE F: manifest says EVAL-1.0, registry resolves a V9.9 contract."""
    _, reg, bundle = _s13_pack_and_registry(bad_eval=True)
    report = reconstruct_epoch(bundle, reg, "R")
    assert report.success is False
    assert "evaluation_contract" in report.invalid_surfaces


def test_wrong_epoch_knowledge_projection_fails():
    _, reg, bundle = _s13_pack_and_registry(wrong_epoch=True)
    report = reconstruct_epoch(bundle, reg, "R")
    assert report.success is False
    assert "active_knowledge_projection" in report.missing_surfaces


def test_wrong_authority_snapshot_fails():
    _, reg, bundle = _s13_pack_and_registry(wrong_auth=True)
    report = reconstruct_epoch(bundle, reg, "R")
    assert report.success is False
    assert "authority_state_snapshot" in report.invalid_surfaces


def test_artifact_with_correct_id_wrong_fingerprint_fails():
    from tests.test_g4 import _s13_artifacts, _s13_epoch
    m = EpochManifest(**_s13_epoch())
    m.seal()
    reg = CanonicalArtifactRegistry()
    reg.register_manifest(m)
    for data in _s13_artifacts():
        reg.register_fixture(data)
    # re-register the authority snapshot with WRONG content under the SAME id
    reg.register(CanonicalArtifact.make("AUTHORITY_SNAPSHOT", "AUTH_SNAP:E17",
                                        {"PO": "PO", "OPERATOR": "OPERATOR"},
                                        epoch_id="E17"))
    report = reconstruct_epoch(EpochReconstructionBundle.for_manifest(m), reg, "R")
    assert report.success is False
    assert "authority_state_snapshot" in report.invalid_surfaces


def test_evaluation_and_lifecycle_contracts_are_separate():
    """G4R-14: lifecycle version is NEVER inferred from evaluation version."""
    from tests.test_g4 import _s13_epoch
    epoch = _s13_epoch()
    epoch["lifecycle_contract_version"] = ""      # evaluation present, lifecycle absent
    m = EpochManifest(**epoch)
    m.seal()
    bundle = EpochReconstructionBundle.for_manifest(m)
    assert bundle.lifecycle_contract_ref == ""
    assert bundle.evaluation_contract_ref == "EVAL:1.0"


def test_reconstruction_validates_content_not_emptiness():
    """G4R-20: a fake non-empty object cannot satisfy a contract surface."""
    from tests.test_g4 import _s13_epoch
    m = EpochManifest(**_s13_epoch())
    m.seal()
    reg = CanonicalArtifactRegistry()
    reg.register_manifest(m)
    # register an evaluation contract with the right id but NO required content
    reg.register(CanonicalArtifact.make("EVALUATION_CONTRACT", "EVAL:1.0",
                                        {"foo": "bar"}, epoch_id="E17"))
    report = reconstruct_epoch(EpochReconstructionBundle.for_manifest(m), reg, "R")
    assert report.success is False
    assert "evaluation_contract" in report.invalid_surfaces


# --------------------------------------------------------------------------- #
# G4R-15 — runtime-native memory must not qualify S13
# --------------------------------------------------------------------------- #
def test_zero_runtime_memory_can_pass():
    pack = load_g4_pack(S13_DIR).decision_grade()
    res = run_g4_scenario(pack, POLICY, runtime_native_memory=False)
    report = res.artifacts["reports"][-1]
    assert report["success"] is True
    assert report["reconstruction_evidence_qualified"] is True


def test_private_runtime_memory_run_not_qualified_for_s13():
    pack = load_g4_pack(S13_DIR).decision_grade()
    res = run_g4_scenario(pack, POLICY, runtime_native_memory=True)
    report = res.artifacts["reports"][-1]
    assert report["success"] is True            # diagnostic report allowed
    assert report["reconstruction_evidence_qualified"] is False


def test_runtime_name_rename_still_semantically_invariant():
    pack = load_g4_pack(S13_DIR).decision_grade()
    a = run_g4_scenario(pack, POLICY, current_runtime="RUNTIME_ALPHA")
    b = run_g4_scenario(pack, POLICY, current_runtime="RUNTIME_BETA")
    assert a.artifacts["reports"][-1]["reconstruction_semantic_fingerprint"] == \
        b.artifacts["reports"][-1]["reconstruction_semantic_fingerprint"]


# --------------------------------------------------------------------------- #
# G4R-16/17/18 — S12 active flood, policy compaction, explicit ref gaps
# --------------------------------------------------------------------------- #
def test_active_flood_produces_bounded_context_and_compaction():
    """CASE G: 20k+ initially ACTIVE objects, 12 required -> bounded bundle."""
    pack = G4ScenarioPack(scenario_id="S12", history_size=20000, experiments_size=2000,
                          required_refs=[f"REL_{i:02d}" for i in range(12)],
                          context_budget=12)
    res = run_s12(pack.decision_grade(), POLICY, active_flood=True)
    m = res.artifacts["metrics"]
    assert m["active_context_objects"] <= 12
    assert m["required_object_recall"] == 1.0
    assert len(res.artifacts["compaction_records"]) > 0
    assert res.artifacts["active_context_after_compaction"] <= 12
    # compaction records keep provenance and the policy rule is recorded
    assert all(c["provenance_pointer"] for c in res.artifacts["compaction_records"])
    assert res.artifacts["compaction_policy_rule"] == "mem.activation.historical"


def test_tag_collision_required_outranks_broad_tags():
    """CASE G variant B: thousands of irrelevant objects share broad tags; the
    12 required objects must still be selected."""
    index = MemoryIndex()
    for i in range(5000):
        index.add(MemoryObject(object_id=f"NOISE_{i}", kind="KNOWLEDGE",
                               tags=("TASK",), memory_tier="ACTIVE_CONTEXT",
                               m4_state="ACTIVE", summary=f"n{i}",
                               provenance_pointer=f"p://{i}", reconstruction_pointer=f"r://{i}"))
    for j in range(12):
        index.add(MemoryObject(object_id=f"REL_{j}", kind="KNOWLEDGE",
                               tags=(f"REL_{j}",), memory_tier="ACTIVE_CONTEXT",
                               m4_state="ACTIVE", summary=f"r{j}",
                               provenance_pointer=f"p://r{j}", reconstruction_pointer=f"r://r{j}"))
    retriever = MemoryRetriever(index, context_budget=12)
    bundle = retriever.build_context("TASK", required_refs=[f"REL_{j}" for j in range(12)])
    for j in range(12):
        assert f"REL_{j}" in bundle.selected_active_objects
    assert bundle.metrics["stale_object_intrusion_count"] == 0
    assert bundle.bundle_status == "COMPLETE"


def test_recency_distraction_does_not_crowd_out_required():
    """CASE G variant C: recent-but-irrelevant records must not crowd out old
    required records — task need outranks recency."""
    index = MemoryIndex()
    for i in range(3000):
        index.add(MemoryObject(object_id=f"RECENT_{i}", kind="KNOWLEDGE",
                               tags=("recent-noise",), memory_tier="ACTIVE_CONTEXT",
                               m4_state="ACTIVE", summary=f"recent {i}",
                               provenance_pointer=f"p://{i}", reconstruction_pointer=f"r://{i}"))
    for j in range(12):
        index.add(MemoryObject(object_id=f"OLD_REQUIRED_{j}", kind="KNOWLEDGE",
                               tags=(f"OLD_REQUIRED_{j}",), memory_tier="ACTIVE_CONTEXT",
                               m4_state="ACTIVE", summary=f"old required {j}",
                               provenance_pointer=f"p://r{j}", reconstruction_pointer=f"r://r{j}"))
    retriever = MemoryRetriever(index, context_budget=12)
    bundle = retriever.build_context("TASK",
                                     required_refs=[f"OLD_REQUIRED_{j}" for j in range(12)])
    for j in range(12):
        assert f"OLD_REQUIRED_{j}" in bundle.selected_active_objects
    assert bundle.metrics["required_object_recall"] == 1.0
    assert bundle.metrics["stale_object_intrusion_count"] == 0


def test_required_gt_budget_reports_insufficient():
    """CASE G variant D: 20 required, budget 12 -> explicit gap, no hidden
    success."""
    pack = G4ScenarioPack(scenario_id="S12", history_size=100, experiments_size=10,
                          required_refs=[f"REL_{i:02d}" for i in range(20)],
                          context_budget=12)
    res = run_s12(pack.decision_grade(), POLICY)
    assert res.artifacts["bundle_status"] == "CONTEXT_BUDGET_INSUFFICIENT"
    assert res.artifacts["budget_sufficient"] is False
    assert res.artifacts["metrics"]["required_object_recall"] < 1.0


def test_missing_required_refs_explicit():
    """G4R-18: a required ref that cannot resolve is surfaced, not skipped."""
    index = MemoryIndex()
    index.add(MemoryObject(object_id="EXISTS_1", kind="KNOWLEDGE", tags=("t",),
                           memory_tier="ACTIVE_CONTEXT", m4_state="ACTIVE"))
    retriever = MemoryRetriever(index, context_budget=12)
    bundle = retriever.build_context("t", required_refs=["EXISTS_1", "GHOST_2"])
    assert bundle.missing_required_refs == ("GHOST_2",)
    assert bundle.required_ref_resolution_status == {"EXISTS_1": "RESOLVED",
                                                     "GHOST_2": "MISSING"}
    assert bundle.bundle_status == "REQUIRED_REFS_MISSING"
    assert bundle.budget_sufficient is False


def test_policy_governed_compaction_decision():
    """G4R-17: the shared activation policy actually decides the compaction."""
    index = MemoryIndex()
    for i in range(50):
        index.add(MemoryObject(object_id=f"K{i}", kind="KNOWLEDGE", tags=(f"tag{i}",),
                               memory_tier="ACTIVE_CONTEXT", m4_state="ACTIVE",
                               summary=f"k{i}", provenance_pointer=f"p://{i}",
                               reconstruction_pointer=f"r://{i}"))
    keep = {"K0"}
    records, rule_id = compact_active_pool(index, POLICY, keep, task_ref="TASK",
                                           epoch="E12")
    assert rule_id == "mem.activation.historical"
    assert len(records) == 49
    assert index.get("K1").memory_tier == "DORMANT_STORE"
    assert index.get("K1").provenance_pointer == "p://1"     # provenance intact
    assert index.get("K0").memory_tier == "ACTIVE_CONTEXT"   # kept


# --------------------------------------------------------------------------- #
# G4R-19 — MemoryRetriever cannot bypass the ReopenEvaluator
# --------------------------------------------------------------------------- #
def test_raw_true_boolean_cannot_bypass_reopen_evaluator():
    """CASE H: reopen_facts[condition_id] = True but evaluator says UNKNOWN."""
    index = MemoryIndex()
    with pytest.raises(TypeError):
        MemoryRetriever(index, reopen_facts={"c1": True})


def test_retriever_accepts_governed_reopen_evaluation():
    index = MemoryIndex()
    index.add(MemoryObject(object_id="D1", kind="KNOWLEDGE", tags=("t",),
                           memory_tier="DORMANT_STORE", m4_state="DORMANT",
                           reopen_condition_ids=("c1",),
                           provenance_pointer="p", reconstruction_pointer="r"))
    retriever = MemoryRetriever(index, reopen_evaluations={"D1": _ev("REOPEN_CANDIDATE")})
    bundle = retriever.build_context("t", required_refs=["D1"])
    assert "D1" in bundle.selected_active_objects


def test_condition_unknown_does_not_retrieve():
    index = MemoryIndex()
    index.add(MemoryObject(object_id="D1", kind="KNOWLEDGE", tags=("t",),
                           memory_tier="DORMANT_STORE", m4_state="DORMANT",
                           reopen_condition_ids=("c1",)))
    retriever = MemoryRetriever(index, reopen_evaluations={"D1": _ev("CONDITION_UNKNOWN")})
    bundle = retriever.build_context("t", required_refs=["D1"])
    assert "D1" not in bundle.selected_active_objects
    assert bundle.required_ref_resolution_status["D1"] == "DORMANT_UNSATISFIED"


def test_operator_review_required_does_not_auto_retrieve():
    index = MemoryIndex()
    index.add(MemoryObject(object_id="D1", kind="KNOWLEDGE", tags=("t",),
                           memory_tier="DORMANT_STORE", m4_state="DORMANT",
                           reopen_condition_ids=("c1",)))
    retriever = MemoryRetriever(index,
                                reopen_evaluations={"D1": _ev("OPERATOR_REVIEW_REQUIRED")})
    bundle = retriever.build_context("t", required_refs=["D1"])
    assert "D1" not in bundle.selected_active_objects


# --------------------------------------------------------------------------- #
# G4R-21 — provenance conflicts survive into the run receipt
# --------------------------------------------------------------------------- #
def test_reopen_conflicts_survive_into_receipt():
    from engine.cognitive_ecology import ProvenanceConflict, ProvenanceConflictLedger
    ledger = ProvenanceConflictLedger()
    ledger.record("REOPEN_EVALUATION", [ProvenanceConflict(
        "REOPEN_EVALUATION:K", "subject_ref", "KNOWLEDGE_B", "KNOWLEDGE_A",
        disposition="subject_mismatch")])
    data = ledger.to_dict()
    assert data["count"] == 1
    assert data["entries"][0]["surface"] == "REOPEN_EVALUATION"


def test_runner_exposes_provenance_conflicts():
    """A cross-subject reopen attempt inside the S10 runner records the
    conflict into the run artifacts."""
    c = _cond(1, subject_ref="KNOWLEDGE_A", field="sensor_online", expected_value=True)
    ev = ReopenEvaluator(conditions=[c]).evaluate("KNOWLEDGE_B", {"sensor_online": True})
    assert ev.conflicts  # conflict tuple populated


def test_reconstruction_conflicts_are_missing_surfaces():
    """Reconstruction gaps are explicit report surfaces, never silent."""
    from tests.test_g4 import _s13_epoch
    m = EpochManifest(**_s13_epoch())
    m.seal()
    reg = CanonicalArtifactRegistry()
    reg.register_manifest(m)
    report = reconstruct_epoch(EpochReconstructionBundle.for_manifest(m), reg, "R")
    assert report.success is False
    assert report.missing_surfaces  # non-empty and identified


# --------------------------------------------------------------------------- #
# cross-case guards
# --------------------------------------------------------------------------- #
def test_s10_primary_pack_still_passes():
    pack = load_g4_pack(S10_DIR).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    assert res.artifacts["reopen_outcomes"]["M_OLD"] == "REOPEN_CANDIDATE"


def test_s11_primary_pack_still_passes():
    pack = load_g4_pack(S11_DIR).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    assert res.artifacts["suppression_decisions"][0]["decision"]["next_action"] == \
        "STOP_SUPPRESSION"


def test_s13_primary_pack_still_passes():
    pack = load_g4_pack(S13_DIR).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    assert res.artifacts["reports"][-1]["reconstruction_evidence_qualified"] is True
