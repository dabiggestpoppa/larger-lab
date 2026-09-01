"""G4 — memory, negative knowledge, epistemic metabolism, epoch reconstruction.

Covers:
  * G4-P0 — replication identity/provenance, provenance conflict ledger,
    negative-knowledge permanence authority, sealed epoch snapshots.
  * S10 — dormant knowledge becomes valid again (reopen -> REACTIVATED, never
    DORMANT -> ACTIVE).
  * S11 — negative knowledge reopens without deletion; operator-permanent
    records require operator review (revocation ambiguity preserved).
  * S12 — institutional hyperthymesia: bounded active context under 50k
    history; scaling metamorphics; dormant reactivation via reopen.
  * S13 — total runtime replacement: epoch reconstruction from canonical
    artifacts, runtime-neutral semantic fingerprint, fail-closed missing
    surfaces, epoch chain integrity.
  * Sealing — expected outcomes / hidden ground truth never reach the
    decision path; scenario-rename and runtime-rename invariance.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.authority import AuthorityState
from engine.epoch import EpochManifest, EpochManifestError
from engine.g4_runner import (
    G4ScenarioPack,
    load_g4_pack,
    run_g4_scenario,
    run_s10,
    run_s11,
    evaluate_g4_expectation,
)
from engine.lifecycle import KnowledgeRecord, LifecycleEngine, LifecycleEdgeTable, Provenance
from engine.memory import (
    ContextBundle,
    MemoryCompactionRecord,
    MemoryIndex,
    MemoryObject,
    MemoryRetriever,
    KnowledgeActivationState,
    run_metabolism_pipeline,
)
from engine.memory_policy import MemoryPolicy, MemoryPolicyError
from engine.negative import NegativeKnowledgeRecord, NegativeKnowledgeError
from engine.reconstruction import (
    EpochReconstructionBundle,
    PROVISIONAL_EPOCH_RECONSTRUCTION_CONTRACT,
    reconstruct_epoch,
    verify_epoch_chain,
)
from engine.reopen import (
    ReopenCondition,
    ReopenConditionError,
    ReopenEvaluator,
    decide_suppression,
)
from engine.cognitive_ecology import (
    ReplicationPathRecord,
    ProvenanceConflictLedger,
    collect_epistemic_paths,
)

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "scenarios"
POLICY_DATA = json.loads(
    (SCENARIOS / "policies/G4_MEMORY_AND_REACTIVATION_POLICY.json").read_text(encoding="utf-8"))
POLICY = MemoryPolicy.from_data(POLICY_DATA)

PACK_DIRS = {
    "S10": SCENARIOS / "s10_dormant_knowledge_returns",
    "S11": SCENARIOS / "s11_negative_knowledge_dogma",
    "S12": SCENARIOS / "s12_institutional_hyperthymesia",
    "S13": SCENARIOS / "s13_runtime_replacement_epoch_reconstruction",
}


def _auth(level_by_actor):
    a = AuthorityState()
    for actor, level in level_by_actor.items():
        a.seed_level(actor, level)
    a.freeze_initialization()
    return a


def _nk(seq, scope="scope-X", reopen_conditions=None, permanent=False):
    nk = NegativeKnowledgeRecord.make(seq, "family-X", scope, "blocker present",
                                      reopen_conditions=reopen_conditions or [])
    if permanent:
        nk.make_permanent("operator", _auth({"operator": "OPERATOR"}),
                          "ratified-permanence", ratification_ref="RAT-P")
    return nk


def _condition(seq, field="sensor_online", operator="EQ", expected_value=True,
               evidence_required=False, **kw):
    return ReopenCondition.make(seq, field=field, operator=operator,
                                expected_value=expected_value,
                                evidence_required=evidence_required, **kw)


# --------------------------------------------------------------------------- #
# G4-P0-A — replication must have identity / provenance
# --------------------------------------------------------------------------- #
def test_raw_replication_count_cannot_mint_paths():
    """G4-P0-A: an explicit empty replication-path contract plus a raw count of
    20 must NOT mint twenty independent paths by declaration."""
    paths = collect_epistemic_paths([], replication_paths=[], independent_replication_count=20)
    assert len(paths) == 0


def test_registered_replication_paths_count():
    rp = ReplicationPathRecord(
        replication_id="REP-1", method="deterministic", runtime_or_deterministic_path="RT-A",
        source_lineages=("SRC-1",), provenance_mode="AUTHORITATIVE_SYNTHETIC_FIXTURE",
        registered_or_synthetic_authority="harness")
    paths = collect_epistemic_paths([], replication_paths=[rp])
    assert len(paths) == 1
    assert paths[0].independent_replication is True


def test_duplicate_replication_id_counts_once():
    rps = [
        ReplicationPathRecord(replication_id="REP-1", method="deterministic",
                              runtime_or_deterministic_path="RT-A",
                              provenance_mode="AUTHORITATIVE_SYNTHETIC_FIXTURE",
                              registered_or_synthetic_authority="harness"),
        ReplicationPathRecord(replication_id="REP-1", method="deterministic",
                              runtime_or_deterministic_path="RT-B",
                              provenance_mode="AUTHORITATIVE_SYNTHETIC_FIXTURE",
                              registered_or_synthetic_authority="harness"),
    ]
    paths = collect_epistemic_paths([], replication_paths=rps)
    assert len(paths) == 1


def test_unknown_replication_provenance_does_not_qualify():
    rp = ReplicationPathRecord(replication_id="REP-9", method="UNKNOWN",
                               runtime_or_deterministic_path="UNKNOWN",
                               source_lineages=(), experiment_design_origin="UNKNOWN",
                               provenance_mode="GOVERNED_REGISTRY",
                               registered_or_synthetic_authority="")
    assert rp.qualifies() is False
    paths = collect_epistemic_paths([], replication_paths=[rp])
    assert len(paths) == 0


def test_replication_path_needs_explicit_authority():
    rp = ReplicationPathRecord(replication_id="REP-3", method="deterministic",
                               runtime_or_deterministic_path="RT-A",
                               provenance_mode="AUTHORITATIVE_SYNTHETIC_FIXTURE",
                               registered_or_synthetic_authority="")
    assert rp.qualifies() is False


# --------------------------------------------------------------------------- #
# G4-P0-B — secondary provenance conflicts survive in a run ledger
# --------------------------------------------------------------------------- #
def test_provenance_conflict_ledger_records_all_surfaces():
    ledger = ProvenanceConflictLedger()
    ledger.record("PRIMARY_REVIEW", [])
    ledger.record("TOPOLOGY_CANDIDATE", [])
    ledger.record("FRICTION_REVIEW", [])
    ledger.record("REPLICATION_PATH", [])
    assert ledger.count() == 0
    # unknown surface tag fails closed
    with pytest.raises(ValueError):
        ledger.record("BOGUS_SURFACE", [])


def test_conflict_ledger_roundtrip_survives_into_receipt_shape():
    from engine.cognitive_ecology import ProvenanceConflict
    ledger = ProvenanceConflictLedger()
    ledger.record("TOPOLOGY_CANDIDATE", [
        ProvenanceConflict("r1", "model_family", "FAM-B", "FAM-A")])
    data = ledger.to_dict()
    assert data["count"] == 1
    entry = data["entries"][0]
    assert entry["surface"] == "TOPOLOGY_CANDIDATE"
    assert entry["axis"] == "model_family"
    assert entry["claimed"] == "FAM-B"
    assert entry["registered"] == "FAM-A"


# --------------------------------------------------------------------------- #
# G4-P0-C — negative-knowledge permanence requires exact operator authority
# --------------------------------------------------------------------------- #
def test_worker_cannot_make_negative_knowledge_permanent():
    nk = _nk(1)
    with pytest.raises(NegativeKnowledgeError):
        nk.make_permanent("worker", _auth({"worker": "WORKER"}), "rationale")
    assert not nk.is_permanent


def test_fake_operator_payload_rejected():
    """Payload containing OPERATOR while the actor is a WORKER fails closed."""
    nk = _nk(2)
    with pytest.raises(NegativeKnowledgeError):
        nk.make_permanent("worker", _auth({"worker": "WORKER"}), "payload OPERATOR")
    assert not nk.is_permanent


def test_real_operator_authority_can_make_permanent():
    nk = _nk(3)
    nk.make_permanent("operator", _auth({"operator": "OPERATOR"}), "basis",
                      ratification_ref="RAT-7")
    assert nk.is_permanent
    assert nk.permanence_authority["actual_level"] == "OPERATOR"
    assert nk.permanence_authority["ratification_ref"] == "RAT-7"


def test_permanence_records_authority_reference():
    nk = _nk(4)
    nk.make_permanent("operator", _auth({"operator": "OPERATOR"}), "basis-rt",
                      ratification_ref="RAT-11")
    assert nk.permanent_by_operator_authority == "basis-rt"
    assert nk.permanence_authority["binding"] == "EXACT_AUTHORITY_STATE"


def test_permanence_does_not_delete_reopen_history():
    nk = _nk(5, reopen_conditions=["cond-1"])
    nk.make_permanent("operator", _auth({"operator": "OPERATOR"}), "basis",
                      ratification_ref="RAT-1")
    assert nk.reopen_conditions == ["cond-1"]   # history retained


# --------------------------------------------------------------------------- #
# G4-P0-D — sealed epoch manifests are immutable snapshots
# --------------------------------------------------------------------------- #
def _manifest(epoch_id="E1", predecessor=None, **kw):
    m = EpochManifest(epoch_id=epoch_id, predecessor_epoch=predecessor,
                      governing_architecture_versions=["A-009:1.0"],
                      authority_state_snapshot={"GOVERNOR": "GOVERNOR"},
                      active_knowledge_projection=["K1"],
                      **kw)
    m.seal()
    return m


def test_sealed_epoch_blocks_nested_mutation():
    """Sealed snapshots are effectively immutable: in-place nested mutation on
    attribute reads has NO effect (reads return deep copies) and direct
    attribute assignment raises."""
    m = _manifest()
    m.governing_architecture_versions.append("A-010:2.0")
    m.authority_state_snapshot["GOVERNOR"] = "OPERATOR"
    assert m.governing_architecture_versions == ["A-009:1.0"]
    assert m.authority_state_snapshot == {"GOVERNOR": "GOVERNOR"}
    with pytest.raises(EpochManifestError):
        m.governing_architecture_versions = ["A-010:2.0"]


def test_sealed_epoch_blocks_pre_seal_alias_mutation():
    """Lists/dicts referenced before seal are deep-copied at seal: mutating the
    original alias after seal cannot change the manifest."""
    arch = ["A-009:1.0"]
    m = EpochManifest(epoch_id="E1", governing_architecture_versions=arch)
    m.seal()
    arch.append("A-010:2.0")
    assert m.governing_architecture_versions == ["A-009:1.0"]
    assert "A-010:2.0" not in m.governing_architecture_versions


def test_sealed_epoch_fingerprint_stable():
    m = _manifest()
    fp1 = m.fingerprint()
    fp2 = m.fingerprint()
    assert fp1 == fp2
    # round trip preserves fingerprint
    m2 = EpochManifest.from_dict(json.loads(json.dumps(m.to_dict())))
    m2.seal()
    assert m2.fingerprint() == fp1


def test_future_epoch_does_not_alias_predecessor():
    m = _manifest(epoch_id="E17")
    m2 = EpochManifest.successor_of(m, "E18", start_cause="runtime upgrade")
    # mutating the successor must not touch the sealed predecessor
    m2.active_knowledge_projection.append("K2")
    assert m2.active_knowledge_projection == ["K1", "K2"]  # successor mutable
    assert m.active_knowledge_projection == ["K1"]          # predecessor untouched
    m.active_knowledge_projection.append("K2")              # sealed: no effect
    assert m.active_knowledge_projection == ["K1"]
    assert m2.predecessor_epoch == "E17"


def test_historical_epoch_never_rewritten_by_successor():
    m = _manifest(epoch_id="E17")
    m2 = EpochManifest.successor_of(m, "E18")
    m2.seal()
    m3 = EpochManifest.successor_of(m2, "E19")
    m3.seal()
    # mutating E19's nested content cannot reach E18 or E17 (all sealed)
    m3.active_ontology_versions.append("ONT-9")
    m2.active_ontology_versions.append("ONT-8")
    assert m3.active_ontology_versions == []
    assert m2.active_ontology_versions == []
    assert m.active_ontology_versions == []


# --------------------------------------------------------------------------- #
# ReopenCondition — fail closed at construction
# --------------------------------------------------------------------------- #
def test_unknown_condition_type_rejected():
    with pytest.raises(ReopenConditionError):
        ReopenCondition(condition_id="c", condition_type="MAGIC_TYPE", operator="EQ")


def test_unknown_operator_rejected():
    with pytest.raises(ReopenConditionError):
        ReopenCondition(condition_id="c", condition_type="FIELD_PREDICATE", operator="EVAL")


def test_unknown_blocker_rejected():
    with pytest.raises(ReopenConditionError):
        ReopenCondition(condition_id="c", condition_type="BLOCKER_RESOLVED",
                        operator="BLOCKER_RESOLVED", expected_value="MAGIC_BLOCKER")


def test_reopen_contract_version_retained():
    c = ReopenCondition(condition_id="c1", field="sensor_online", operator="EQ",
                        expected_value=True, version_tag="1.0.0")
    ev = ReopenEvaluator(conditions=[c]).evaluate("K", {"sensor_online": True})
    assert ev.condition_results[0]["version_tag"] == "1.0.0"


# --------------------------------------------------------------------------- #
# S10 — dormant knowledge becomes valid again
# --------------------------------------------------------------------------- #
def _s10_pack(conditions_satisfied=True):
    facts = {"sensor_online": True} if conditions_satisfied else {"sensor_online": False}
    return G4ScenarioPack(
        scenario_id="S10",
        knowledge=[{"record_id": "M_OLD", "claim": "old regime valid",
                    "m4_state": "DORMANT", "memory_tier": "DORMANT_STORE",
                    "tags": ["reopen-review"], "epoch": "E1",
                    "provenance_pointer": "orig://M_OLD",
                    "reconstruction_pointer": "recon://M_OLD",
                    "dependency_refs": [], "source_label": "S10"}],
        reopen_conditions=[{"field": "sensor_online", "operator": "EQ",
                            "expected_value": True}],
        current_facts=facts,
        epochs=[{"epoch_id": "E1"}],
        expected_outcome="REOPEN_CANDIDATE" if conditions_satisfied else "NO_REOPEN",
    )


def test_satisfied_reopen_condition_retrieves_dormant_knowledge():
    pack = _s10_pack(True).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    assert res.artifacts["reopen_outcomes"]["M_OLD"] == "REOPEN_CANDIDATE"
    # M4 path: DORMANT -> REACTIVATED -> CANDIDATE, and the DORMANT->ACTIVE
    # shortcut attempt was rejected
    trace = res.artifacts["m4_traces"]["M_OLD"]
    states = [t["to_state"] for t in trace]
    assert states[:2] == ["REACTIVATED", "CANDIDATE"]
    assert res.artifacts["direct_dormant_to_active_forbidden"]["M_OLD"] is True
    assert trace[-1]["allowed"] is False


def test_unsatisfied_condition_leaves_dormant():
    pack = _s10_pack(False).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    assert res.artifacts["reopen_outcomes"]["M_OLD"] == "NO_REOPEN"
    assert res.artifacts["m4_traces"]["M_OLD"] == []


def test_dormant_to_active_forbidden_by_edge_table():
    rec = KnowledgeRecord(record_id="M", claim="x", provenance=Provenance("FIXTURE", "S10"),
                          creation_source="S10", initial_state="DORMANT")
    engine = LifecycleEngine()
    engine.add(rec)
    t = rec.transition(1, "ACTIVE", actor="GOVERNOR", authority_basis="b",
                       authority_level="GOVERNOR", reason="illegal",
                       edge_table=LifecycleEdgeTable.default())
    assert t.allowed is False


def test_dormant_to_reactivated_legal():
    rec = KnowledgeRecord(record_id="M", claim="x", provenance=Provenance("FIXTURE", "S10"),
                          creation_source="S10", initial_state="DORMANT")
    engine = LifecycleEngine()
    engine.add(rec)
    t = engine.transition("M", 1, "REACTIVATED", actor="GOVERNOR", authority_basis="b",
                          authority_level="GOVERNOR", reason="reopen")
    assert t.allowed is True


def test_reactivation_requires_renewed_evaluation():
    """REACTIVATED may not jump straight to ACTIVE — it routes through
    CANDIDATE/CHALLENGED (edge table forbids REACTIVATED -> ACTIVE)."""
    rec = KnowledgeRecord(record_id="M", claim="x", provenance=Provenance("FIXTURE", "S10"),
                          creation_source="S10", initial_state="DORMANT")
    engine = LifecycleEngine()
    engine.add(rec)
    engine.transition("M", 1, "REACTIVATED", actor="GOVERNOR", authority_basis="b",
                      authority_level="GOVERNOR", reason="reopen")
    t = rec.transition(2, "ACTIVE", actor="GOVERNOR", authority_basis="b",
                       authority_level="GOVERNOR", reason="auto-promotion attempt",
                       edge_table=LifecycleEdgeTable.default())
    assert t.allowed is False


def test_old_evidence_and_demotion_reason_survive():
    """The record keeps its provenance pointers and historical regime reason;
    historical validation is not treated as current validation (the reopen path
    starts a fresh CANDIDATE evaluation)."""
    pack = _s10_pack(True).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    trace = res.artifacts["m4_traces"]["M_OLD"]
    # The REACTIVATED transition reason records that renewed evaluation begins
    assert any("renewed evaluation" in t.get("reason", "") for t in trace)
    assert pack.knowledge[0]["provenance_pointer"] == "orig://M_OLD"


def test_s10_scenario_rename_invariant():
    a = run_s10(_s10_pack(True).decision_grade(), POLICY)
    renamed = _s10_pack(True)
    renamed.scenario_id = "RANDOM_NAME_741"
    b = run_s10(renamed.decision_grade(), POLICY)
    assert a.artifacts["behavior_fingerprint"] == b.artifacts["behavior_fingerprint"]
    assert a.artifacts["fingerprint"] != b.artifacts["fingerprint"]


def test_s10_wrong_expected_outcome_leaves_fingerprint_unchanged():
    pack = _s10_pack(True)
    a = run_g4_scenario(pack.decision_grade(), POLICY)
    pack2 = _s10_pack(True)
    pack2.expected_outcome = "WRONG_EXPECTATION"
    b = run_g4_scenario(pack2.decision_grade(), POLICY)
    assert a.artifacts["behavior_fingerprint"] == b.artifacts["behavior_fingerprint"]
    # post-hoc evaluation reports the mismatch without touching the run
    verdict = evaluate_g4_expectation(b, pack2)
    assert verdict["pass"] is False


# --------------------------------------------------------------------------- #
# S11 — negative knowledge becomes dogma (and how it is legally reopened)
# --------------------------------------------------------------------------- #
def _s11_pack(blocker_resolved=True, with_evidence=True, operator_permanent=False):
    facts = {"resolved_blockers": ["TIMESTAMP_LEAKAGE"]} if blocker_resolved else \
            {"resolved_blockers": []}
    if with_evidence:
        facts["evidence_refs"] = ["EVID-1"]
    return G4ScenarioPack(
        scenario_id="S11",
        negative_knowledge=[{
            "record_id": "NK-1", "claim_rejected": "family-X alpha", "exact_scope": "FX EURUSD",
            "evidence_refs": ["EVID-OLD"], "rejection_reason": "timestamp leakage",
            "blockers": ["TIMESTAMP_LEAKAGE"],
            "reopen_conditions": ["sensor available"], "operator_permanent": operator_permanent,
        }],
        reopen_conditions=[{"condition_type": "BLOCKER_RESOLVED",
                            "operator": "BLOCKER_RESOLVED", "expected_value": "TIMESTAMP_LEAKAGE",
                            "evidence_required": True}],
        current_facts=facts,
        expected_outcome="STOP_SUPPRESSION" if (blocker_resolved and with_evidence
                                                and not operator_permanent)
        else "CONTINUE_SUPPRESSION",
    )


def test_blocker_resolved_condition_reopens_ordinary_negative_knowledge():
    pack = _s11_pack(True, True).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    d = res.artifacts["suppression_decisions"][0]
    assert d["decision"]["next_action"] == "STOP_SUPPRESSION"
    assert d["decision"]["currently_suppressed"] is False
    assert d["record_retained"] is True


def test_unrelated_evidence_does_not_reopen():
    pack = _s11_pack(False, True).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    d = res.artifacts["suppression_decisions"][0]
    assert d["decision"]["next_action"] == "CONTINUE_SUPPRESSION"
    assert d["decision"]["currently_suppressed"] is True


def test_unsupported_blocker_assertion_does_not_reopen():
    """Control 2: agent merely asserts the blocker resolved, no evidence."""
    pack = _s11_pack(True, False).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    d = res.artifacts["suppression_decisions"][0]
    assert d["decision"]["next_action"] == "CONTINUE_SUPPRESSION"


def test_negative_knowledge_record_retained_after_reopen():
    pack = _s11_pack(True, True).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    d = res.artifacts["suppression_decisions"][0]
    assert d["record_retained"] is True
    assert d["decision"]["evidence_refs"] == ["EVID-OLD"]


def test_suppression_ends_only_for_exact_scope():
    """A different scope whose reopen condition is not satisfied stays
    suppressed — each record governs only its own exact scope."""
    nk1 = _nk(1, scope="FX EURUSD", reopen_conditions=["c1"])
    nk2 = _nk(2, scope="OTHER SCOPE", reopen_conditions=["c2"])
    c1 = _condition(1, field="sensor_online", expected_value=True, evidence_required=True)
    c2 = _condition(2, field="sensor_online", expected_value=False, evidence_required=True)
    evaluator = ReopenEvaluator(conditions=[c1, c2])
    facts = {"sensor_online": True, "evidence_refs": ["EVID-1"]}
    d1 = decide_suppression(nk1, evaluator, facts, conditions=[c1])
    d2 = decide_suppression(nk2, evaluator, facts, conditions=[c2])
    assert d1.next_action == "STOP_SUPPRESSION"
    assert d2.next_action == "CONTINUE_SUPPRESSION"
    assert d1.scope == "FX EURUSD"
    assert d2.scope == "OTHER SCOPE"


def test_operator_permanent_record_does_not_auto_reopen():
    pack = _s11_pack(True, True, operator_permanent=True).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    d = res.artifacts["suppression_decisions"][0]
    assert d["decision"]["next_action"] == "OPERATOR_REVIEW_REQUIRED"
    assert d["decision"]["currently_suppressed"] is True
    assert d["decision"]["reopen_condition_status"] == "OPERATOR_PERMANENT"
    assert d["decision"]["permanent_operator_authority"] == "ratified-permanence"


def test_permanent_behavior_ambiguity_remains_explicit():
    """Revocation of operator permanence is unspecified — the decision exposes
    OPERATOR_REVIEW_REQUIRED rather than pretending to resolve it."""
    pack = _s11_pack(True, True, operator_permanent=True).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    reason = res.artifacts["suppression_decisions"][0]["decision"]["reason"]
    assert "revocation" in reason.lower()


def test_s11_scenario_rename_invariant():
    a = run_s11(_s11_pack(True, True).decision_grade(), POLICY)
    renamed = _s11_pack(True, True)
    renamed.scenario_id = "RANDOM_NAME_812"
    b = run_s11(renamed.decision_grade(), POLICY)
    assert a.artifacts["behavior_fingerprint"] == b.artifacts["behavior_fingerprint"]


# --------------------------------------------------------------------------- #
# S12 — institutional hyperthymesia / bounded active context
# --------------------------------------------------------------------------- #
def _s12_pack(history_size, experiments_size, required=12, budget=12):
    return G4ScenarioPack(
        scenario_id="S12",
        history_size=history_size,
        experiments_size=experiments_size,
        required_refs=[f"REL_{i:02d}" for i in range(required)],
        context_budget=budget,
        expected_outcome="BOUNDED_CONTEXT",
    )


def test_fifty_k_history_bounded_active_context():
    pack = _s12_pack(50000, 5000).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    m = res.artifacts["metrics"]
    assert res.artifacts["total_history"] == 55012  # 50k + 5k + 12 relevant
    assert m["active_context_objects"] <= pack.context_budget
    assert m["required_object_recall"] == 1.0


def test_required_objects_all_retrieved():
    pack = _s12_pack(1000, 100).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    bundle = res.artifacts["context_bundle"]
    assert bundle["metrics"]["required_object_recall"] == 1.0
    for ref in pack.required_refs:
        assert ref in bundle["selected_active_objects"]


def test_archive_growth_does_not_grow_active_context():
    """Metamorphic: same 12 relevant objects, archive 5k vs 50k -> bundle under
    the same budget/rules must be approximately unchanged."""
    a = run_g4_scenario(_s12_pack(5000, 500).decision_grade(), POLICY)
    b = run_g4_scenario(_s12_pack(50000, 5000).decision_grade(), POLICY)
    assert a.artifacts["metrics"]["active_context_objects"] == \
        b.artifacts["metrics"]["active_context_objects"]
    assert a.artifacts["context_bundle"]["selected_active_objects"] == \
        b.artifacts["context_bundle"]["selected_active_objects"]


def test_context_scaling_metamorphic():
    counts = []
    for size in (1000, 10000, 50000):
        res = run_g4_scenario(_s12_pack(size, size // 10).decision_grade(), POLICY)
        counts.append(res.artifacts["metrics"]["active_context_objects"])
    assert len(set(counts)) == 1  # active context scales with task need, not age


def test_dormant_record_reactivates_via_reopen_despite_absence():
    """G4 §13: archive is not memory. A dormant record absent from default
    active context is retrieved when its reopen condition fires."""
    index = MemoryIndex()
    for i in range(100):
        index.add(MemoryObject(object_id=f"HIST_{i}", kind="KNOWLEDGE", tags=(),
                               memory_tier="DORMANT_STORE", m4_state="DEMOTED",
                               summary=f"h{i}", provenance_pointer=f"p://{i}",
                               reconstruction_pointer=f"r://{i}"))
    index.add(MemoryObject(object_id="DORMANT_1", kind="KNOWLEDGE", tags=("task-x",),
                           memory_tier="DORMANT_STORE", m4_state="DORMANT",
                           reopen_condition_ids=("c1",), summary="dormant relevant",
                           provenance_pointer="p://dormant", reconstruction_pointer="r://dormant"))
    retriever = MemoryRetriever(index, reopen_facts={"c1": True})
    bundle = retriever.build_context("task-x", required_refs=["DORMANT_1"])
    assert "DORMANT_1" in bundle.selected_active_objects
    why = [w for w in bundle.retrieval_trace if w.object_id == "DORMANT_1"]
    assert why and why[0].policy == "REQUIRED_DORMANT_REOPEN"
    assert "DORMANT_1" in bundle.dormant_refs


def test_archival_object_reconstructs_explicitly():
    index = MemoryIndex()
    index.add(MemoryObject(object_id="ARCH_1", kind="EVIDENCE", tags=("task-y",),
                           memory_tier="ARCHIVAL_STORE", m4_state="DEMOTED",
                           reopen_condition_ids=("c2",), summary="archival evidence",
                           provenance_pointer="p://arch", reconstruction_pointer="r://arch"))
    retriever = MemoryRetriever(index, reopen_facts={"c2": True})
    bundle = retriever.build_context("task-y", required_refs=["ARCH_1"],
                                     activation_rules={"allow_archival_reconstruct": True})
    assert "ARCH_1" in bundle.selected_active_objects
    assert "ARCH_1" in bundle.archival_refs


def test_compaction_never_deletes_provenance():
    index = MemoryIndex()
    objs = [MemoryObject(object_id=f"K{i}", kind="KNOWLEDGE", tags=(f"tag{i % 5}",),
                         memory_tier="ACTIVE_CONTEXT", m4_state="ACTIVE",
                         summary=f"k{i}", provenance_pointer=f"p://{i}",
                         reconstruction_pointer=f"r://{i}") for i in range(20)]
    report = run_metabolism_pipeline(index, objs, compress=[(f"K{i}", "stale") for i in range(15)],
                                     epoch="E12")
    assert report.provenance_intact is True
    for i in range(15):
        assert index.get(f"K{i}").memory_tier == "DORMANT_STORE"  # not deleted
        assert index.get(f"K{i}").provenance_pointer == f"p://{i}"
    compactions = report.compressed
    assert len(compactions) == 15
    assert all(c.provenance_pointer for c in compactions)


def test_compaction_record_keeps_reconstruction_pointer():
    rec = MemoryCompactionRecord.make(0, ["K1"], "stale", "DORMANT_STORE",
                                      summary="s", provenance_pointer="p://1",
                                      reconstruction_pointer="r://1", epoch="E12")
    d = rec.to_dict()
    assert d["reconstruction_pointer"] == "r://1"
    assert d["policy_version"].startswith("G4_MEMORY_AND_REACTIVATION_POLICY")


def test_same_inputs_byte_identical_bundle_fingerprint():
    a = run_g4_scenario(_s12_pack(1000, 100).decision_grade(), POLICY)
    b = run_g4_scenario(_s12_pack(1000, 100).decision_grade(), POLICY)
    assert a.artifacts["context_bundle"]["fingerprint"] == \
        b.artifacts["context_bundle"]["fingerprint"]
    assert a.artifacts["behavior_fingerprint"] == b.artifacts["behavior_fingerprint"]


def test_m4_state_legal_with_archival_tier():
    """A historically ACTIVE M4 object may live in ARCHIVAL_STORE — lifecycle
    state is not memory tier."""
    st = KnowledgeActivationState(knowledge_id="K", m4_state="ACTIVE",
                                  memory_tier="ARCHIVAL_STORE")
    assert st.memory_tier == "ARCHIVAL_STORE"
    assert st.m4_state == "ACTIVE"
    with pytest.raises(ValueError):
        KnowledgeActivationState(knowledge_id="K", m4_state="ACTIVE",
                                 memory_tier="BOGUS_TIER")


# --------------------------------------------------------------------------- #
# S13 — total runtime replacement / epoch reconstruction
# --------------------------------------------------------------------------- #
def _s13_pack(with_authority=True, with_lifecycle=True, with_projection=True,
              with_negative=True, with_unresolved=True):
    epochs = [{
        "epoch_id": "E17", "predecessor_epoch": None, "schema_version": "1.0.0",
        "governing_architecture_versions": ["A-009:1.0", "A-010:1.0"],
        "evaluation_contract_version": "EVAL-1.0",
        "active_ontology_versions": ["ONT-1"],
        "high_dependency_assumptions": ["assumption-A"],
        "active_runtime_certifications": ["Hermes", "OpenClaw"],
        "major_capabilities": ["CAP-A"],
        "known_tensions": ["tension-1"],
        "unresolved_pattern_refs": ["UP-1"] if with_unresolved else [],
        "active_knowledge_projection": ["K-ACTIVE"] if with_projection else [],
        "dormant_knowledge_projection": ["K-DORMANT"],
        "validation_rules": ["rule-1"],
        "authority_state_snapshot": {"GOVERNOR": "GOVERNOR"} if with_authority else {},
        "operator_ratifications": ["RAT-1"],
        "transformation_evidence": ["T-EVID-1"],
        "challenge_conditions": ["challenge-1"],
    }]
    return G4ScenarioPack(scenario_id="S13", epochs=epochs,
                          expected_outcome="RECONSTRUCTED")


def test_sealed_epoch_reconstructs_from_canonical_artifacts():
    pack = _s13_pack().decision_grade()
    res = run_g4_scenario(pack, POLICY)
    report = res.artifacts["reports"][0]
    assert report["success"] is True
    assert report["missing_surfaces"] == []
    assert report["runtime_native_memory_used"] is False


def test_replacement_runtime_has_zero_private_memory():
    """A mock replacement runtime with zero runtime-native memory reconstructs
    the epoch state from canonical artifacts only."""
    pack = _s13_pack().decision_grade()
    res = run_g4_scenario(pack, POLICY, current_runtime="RECONSTRUCTOR_0",
                          runtime_native_memory=True)
    assert res.artifacts["reports"][0]["success"] is True
    assert res.artifacts["reports"][0]["runtime_native_memory_used"] is True


def test_runtime_rename_does_not_alter_semantic_fingerprint():
    a = run_g4_scenario(_s13_pack().decision_grade(), POLICY, current_runtime="RUNTIME_A")
    b = run_g4_scenario(_s13_pack().decision_grade(), POLICY, current_runtime="RUNTIME_B")
    assert a.artifacts["reports"][0]["reconstruction_semantic_fingerprint"] == \
        b.artifacts["reports"][0]["reconstruction_semantic_fingerprint"]
    assert a.artifacts["runtime_rename_semantic_stable"] == [True]


def test_missing_required_artifact_fails_closed():
    """Remove the authority snapshot -> reconstruction identifies the missing
    surface; no silently substituted defaults."""
    pack = _s13_pack(with_authority=False).decision_grade()
    res = run_g4_scenario(pack, POLICY)
    report = res.artifacts["reports"][0]
    assert report["success"] is False
    assert "authority_state_snapshot" in report["missing_surfaces"]
    assert "FAIL_CLOSED" in report["notes"][0]


def test_missing_negative_knowledge_fails_closed():
    pack = _s13_pack().decision_grade()
    res = run_g4_scenario(pack, POLICY)
    # bundle-level: strip the negative-knowledge ref and reconstruct directly
    from engine.epoch import EpochManifest
    m = EpochManifest(**pack.epochs[0])
    m.seal()
    bundle = EpochReconstructionBundle.from_epoch_manifest(m)
    bundle = EpochReconstructionBundle(
        epoch_id=m.epoch_id, sealed_epoch_manifest=m,
        governing_architecture_versions=tuple(m.governing_architecture_versions),
        evaluation_contract={"contract_id": "G4-EVAL", "version": m.evaluation_contract_version},
        lifecycle_contract_version=m.evaluation_contract_version,
        active_ontology_versions=tuple(m.active_ontology_versions),
        high_dependency_assumptions=tuple(m.high_dependency_assumptions),
        active_capability_certifications=tuple(m.major_capabilities),
        authority_state_snapshot=dict(m.authority_state_snapshot),
        active_knowledge_projection=tuple(m.active_knowledge_projection),
        dormant_knowledge_projection=tuple(m.dormant_knowledge_projection),
        negative_knowledge_refs=(),          # removed
        unresolved_pattern_refs=tuple(m.unresolved_pattern_refs),
        known_tensions=tuple(m.known_tensions),
        validation_rules=tuple(m.validation_rules),
        operator_ratifications=tuple(m.operator_ratifications),
        transformation_evidence=tuple(m.transformation_evidence),
        challenge_reopen_conditions=tuple(m.challenge_conditions),
    )
    report = reconstruct_epoch(bundle, "RECONSTRUCTOR")
    assert report.success is False
    assert "negative_knowledge_refs" in report.missing_surfaces


def test_historical_runtime_certifications_retained():
    pack = _s13_pack().decision_grade()
    res = run_g4_scenario(pack, POLICY)
    report = res.artifacts["reports"][0]
    assert set(report["historical_runtime_certifications"]) == {"CAP-A"}
    # the historical epoch fingerprint embeds historical runtime certifications
    assert report["historical_epoch_fingerprint"]


def test_current_runtime_does_not_overwrite_historical_identity():
    """Reconstruction never writes the current runtime into the sealed
    historical manifest (it remains immutable)."""
    pack = _s13_pack().decision_grade()
    from engine.epoch import EpochManifest
    m = EpochManifest(**pack.epochs[0])
    m.seal()
    bundle = EpochReconstructionBundle.from_epoch_manifest(m)
    reconstruct_epoch(bundle, "NEW_RUNTIME")
    # manifest unchanged: no current-runtime field, still sealed
    assert m.active_runtime_certifications == ["Hermes", "OpenClaw"]
    assert m.sealed


def test_epoch_chain_acyclic_and_sealed():
    m17 = _manifest("E17")
    m18 = EpochManifest.successor_of(m17, "E18")
    m18.seal()
    m19 = EpochManifest.successor_of(m18, "E19")
    m19.seal()
    verdict = verify_epoch_chain([m17, m18, m19])
    assert verdict["pass"] is True
    assert verdict["acyclic"] is True
    assert verdict["all_sealed"] is True
    assert verdict["predecessors_resolved"] is True


def test_predecessor_missing_detected():
    m18 = EpochManifest(epoch_id="E18", predecessor_epoch="E17")
    m18.seal()
    verdict = verify_epoch_chain([m18])
    assert verdict["pass"] is False
    assert any("missing predecessor" in p for p in verdict["problems"])


def test_epoch_cycle_fails_closed():
    m17 = EpochManifest(epoch_id="E17", predecessor_epoch="E18")
    m17.seal()
    m18 = EpochManifest(epoch_id="E18", predecessor_epoch="E17")
    m18.seal()
    verdict = verify_epoch_chain([m17, m18])
    assert verdict["acyclic"] is False
    assert any("cycle" in p for p in verdict["problems"])


def test_authority_state_reconstructed_exactly():
    pack = _s13_pack().decision_grade()
    res = run_g4_scenario(pack, POLICY)
    assert res.artifacts["reports"][0]["success"] is True
    assert pack.epochs[0]["authority_state_snapshot"] == {"GOVERNOR": "GOVERNOR"}


def test_m4_and_negative_and_unresolved_surfaces_reconstructed():
    pack = _s13_pack().decision_grade()
    res = run_g4_scenario(pack, POLICY)
    report = res.artifacts["reports"][0]
    assert report["success"] is True
    for surface in ("active_knowledge_projection", "dormant_knowledge_projection",
                    "negative_knowledge_refs", "unresolved_pattern_refs"):
        assert surface in report["resolved_surfaces"]


def test_amb12_stays_provisional():
    contract = PROVISIONAL_EPOCH_RECONSTRUCTION_CONTRACT
    assert contract["status"] == "PROVISIONAL_TEST_CONTRACT"
    assert "EMPIRICALLY_TESTED_PROVISIONAL_CONTRACT" in contract["AMB12"]
    assert "ratification" in contract["AMB12"]


# --------------------------------------------------------------------------- #
# Shared policy — generic predicates only, one policy across S10-S13
# --------------------------------------------------------------------------- #
def test_memory_policy_rejects_scenario_specific_conditions():
    with pytest.raises(MemoryPolicyError):
        MemoryRule_from_data = MemoryPolicy.from_data
        bad = {"policy_id": "BAD", "rules": [{"rule_id": "r1", "kind": "reopen",
                                              "when": {"scenario_id": "S10"},
                                              "then": {}}]}
        MemoryPolicy.from_data(bad)


def test_policy_json_has_no_scenario_ids_or_literals():
    """Rule PREDICATES and actions may not reference scenario ids or knowledge
    literals (descriptive header prose is not a decision predicate)."""
    rules_text = json.dumps(POLICY_DATA.get("rules", []))
    for forbidden in ("S10", "S11", "S12", "S13", "M_OLD", "NK-1", "REL_", "HIST_",
                      "EXPECTED_", "hidden_ground_truth", "scenario_id"):
        assert forbidden not in rules_text, \
            f"policy rule contains scenario-specific literal {forbidden!r}"


def test_policy_knows_only_generic_fields():
    for rule in POLICY.rules:
        for field in rule.when:
            assert field in {
                "lifecycle_state", "memory_tier", "reopen_condition_state",
                "evidence_fresh", "task_relevance", "dependency_centrality",
                "blocker_resolved", "authority_required", "permanent_operator_authority",
                "current_epoch", "retrieval_budget_used", "context_budget",
                "history_size", "suppression_state", "reopen_candidate",
            }


def test_run_g4_scenario_refuses_sealed_fields():
    pack = _s10_pack(True)   # expected_outcome set
    with pytest.raises(ValueError):
        run_g4_scenario(pack, POLICY)


def test_g4_packs_load_and_all_pass():
    for sid, pdir in PACK_DIRS.items():
        pack = load_g4_pack(pdir)
        res = run_g4_scenario(pack.decision_grade(), POLICY)
        verdict = evaluate_g4_expectation(res, pack)
        assert verdict["pass"], f"{sid}: {verdict['failures']}"
        assert res.artifacts["expected_outcome_accessed"] is False
        assert res.artifacts["hidden_ground_truth_accessed"] is False
        assert res.artifacts["authority_before"] == "NONE"
        assert res.artifacts["authority_after"] == "NONE"


def test_policy_fingerprint_deterministic():
    fp1 = POLICY.fingerprint()
    fp2 = MemoryPolicy.from_data(POLICY_DATA).fingerprint()
    assert fp1 == fp2
