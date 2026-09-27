"""G5-P0 — residual integrity closure (policy / evidence / canonical artifacts).

G5-P0-A  FACTUAL CLASSIFICATION != AUTHORIZED INSTITUTIONAL ACTION.
G5-P0-B  evidence_required => governed EvidenceRegistry required (fail closed).
G5-P0-C  EvidenceApplicability: registered evidence + applicability link must
         both resolve; wrong subject/scope/domain rejected; explicit transfer
         contract required for cross-domain use.
G5-P0-D  CanonicalArtifact content is deep-frozen at construction (copy-on-read)
         and the registry recomputes + verifies the fingerprint over
         (kind+id+content+epoch); stale/wrong fingerprints are rejected.
G5-P0-E  the exact sealed manifest resolves from the CanonicalArtifactRegistry
         with matching content/fingerprint; bundle epoch id == manifest epoch id.
G5-P0-F  no synthetic authority snapshot ref; blank ref == missing surface.
G5-P0-G  SealedEpochSnapshot is the reconstruction truth; threat boundary is
         documented honestly (supported institutional APIs, not arbitrary
         interpreter-memory tamper-proofness).

All effects are deterministic, local, model-free, wall-clock-free.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
POLICY_FILE = ROOT / "scenarios/policies/G4_MEMORY_AND_REACTIVATION_POLICY.json"


# --------------------------------------------------------------------------- #
# P0-A helpers
# --------------------------------------------------------------------------- #
def _reopen_only_policy():
    """A shared policy with a reopen rule but NO suppression/activation rules."""
    data = json.loads(POLICY_FILE.read_text(encoding="utf-8"))
    data = dict(data)
    data["rules"] = [r for r in data["rules"] if r.get("kind") == "reopen"]
    data["version_tag"] = "V2-P0A-HOLD"
    from engine.memory_policy import MemoryPolicy
    return MemoryPolicy.from_data(data)


def test_factual_reopen_candidate_can_exist_while_governed_action_holds():
    """P0-A: the evaluator may classify REOPEN_CANDIDATE at the factual layer
    while the governed action is HELD because no policy rule matched."""
    from engine.memory_policy import MemoryPolicy
    from engine.g4_runner import _policy_outcome

    data = json.loads(POLICY_FILE.read_text(encoding="utf-8"))
    policy = MemoryPolicy.from_data(data)
    # strip every reopen rule
    data2 = dict(data)
    data2["rules"] = [r for r in data2["rules"] if r.get("kind") != "reopen"]
    hold_policy = MemoryPolicy.from_data(data2)
    facts = {"reopen_condition_state": "SATISFIED", "lifecycle_state": "DORMANT",
             "memory_tier": "DORMANT_STORE", "permanent_operator_authority": False}
    decided = _policy_outcome(policy, facts, "reopen", "REOPEN_CANDIDATE")
    held = _policy_outcome(hold_policy, facts, "reopen", "REOPEN_CANDIDATE")
    assert decided["outcome"] == "REOPEN_CANDIDATE"
    assert decided["governed"] is True
    assert held["outcome"] == "POLICY_HOLD"
    assert held["governed"] is False
    assert held["factual"] == "REOPEN_CANDIDATE"   # factual layer intact, no action


def test_missing_reopen_policy_rule_does_not_reactivate():
    """P0-A: running S10 under a policy that has NO matching reopen rule must not
    reactivate the dormant record — the factual REOPEN_CANDIDATE is held."""
    from engine.g4_runner import load_g4_pack, run_s10
    from engine.memory_policy import MemoryPolicy

    pack = load_g4_pack(ROOT / "scenarios/s10_dormant_knowledge_returns").decision_grade()
    data = json.loads(POLICY_FILE.read_text(encoding="utf-8"))
    data = dict(data)
    data["rules"] = [r for r in data["rules"] if r.get("kind") != "reopen"]
    hold_policy = MemoryPolicy.from_data(data)
    res = run_s10(pack, hold_policy)
    assert res.artifacts["reopen_outcomes"]["M_OLD"] == "POLICY_HOLD"
    assert res.artifacts["m4_traces"]["M_OLD"] == []           # no mutation applied


def test_missing_suppression_policy_rule_does_not_stop_suppression():
    """P0-A: S11 under a policy without a suppression rule keeps suppressing even
    when the factual reopen condition is satisfied."""
    from engine.g4_runner import load_g4_pack, run_s11
    from engine.memory_policy import MemoryPolicy

    pack = load_g4_pack(ROOT / "scenarios/s11_negative_knowledge_dogma").decision_grade()
    data = json.loads(POLICY_FILE.read_text(encoding="utf-8"))
    data = dict(data)
    data["rules"] = [r for r in data["rules"] if r.get("kind") != "suppression"]
    hold_policy = MemoryPolicy.from_data(data)
    res = run_s11(pack, hold_policy)
    d = res.artifacts["suppression_decisions"][0]["decision"]
    # factual SATISFIED is visible, but the governed action stays CONTINUE
    assert d["reopen_condition_status"] == "SATISFIED"
    assert d["next_action"] == "CONTINUE_SUPPRESSION"
    assert d["currently_suppressed"] is True


def test_missing_activation_policy_rule_does_not_change_memory_tier():
    """P0-A: compact_active_pool under a policy with no activation rule performs
    ZERO compactions and reports POLICY_HOLD — no tier change from facts alone."""
    from engine.memory import MemoryIndex, MemoryObject, compact_active_pool
    from engine.memory_policy import MemoryPolicy

    index = MemoryIndex()
    for i in range(3):
        index.add(MemoryObject(object_id=f"OBJ_{i}", kind="KNOWLEDGE",
                               tags=("tag",), dependency_refs=(), epoch="E",
                               memory_tier="ACTIVE_CONTEXT", m4_state="ACTIVE",
                               summary="x", history_size=1))
    data = json.loads(POLICY_FILE.read_text(encoding="utf-8"))
    data = dict(data)
    data["rules"] = [r for r in data["rules"] if r.get("kind") != "activation"]
    hold_policy = MemoryPolicy.from_data(data)
    records, rule = compact_active_pool(index, hold_policy, keep_refs=(),
                                        task_ref="TASK")
    assert rule == "POLICY_HOLD"
    assert records == ()
    assert len(index.objects_by_tier("ACTIVE_CONTEXT")) == 3   # unchanged


# --------------------------------------------------------------------------- #
# P0-B — evidence_required => registry required
# --------------------------------------------------------------------------- #
def test_evidence_required_without_registry_rejected():
    from engine.reopen import ReopenCondition, ReopenConditionError, ReopenEvaluator

    c = ReopenCondition.make(1, subject_ref="K", field="sensor_online",
                             expected_value=True, evidence_required=True,
                             evidence_refs=["E-A"])
    with pytest.raises(ReopenConditionError):
        ReopenEvaluator(conditions=[c], evidence_registry=None).evaluate(
            "K", {"sensor_online": True, "evidence_refs": ["E-A"]})


def test_non_evidence_required_condition_can_run_without_registry():
    from engine.reopen import ReopenCondition, ReopenEvaluator

    c = ReopenCondition.make(1, subject_ref="K", field="sensor_online",
                             expected_value=True, evidence_required=False)
    ev = ReopenEvaluator(conditions=[c], evidence_registry=None).evaluate(
        "K", {"sensor_online": True})
    assert ev.outcome == "REOPEN_CANDIDATE"


# --------------------------------------------------------------------------- #
# P0-C — EvidenceApplicability
# --------------------------------------------------------------------------- #
def _applicability(**links):
    from engine.reopen import EvidenceApplicability

    return {eid: EvidenceApplicability(**kw) for eid, kw in links.items()}


def _eval_evidence(condition, facts, registry, applicability):
    from engine.reopen import ReopenEvaluator
    return ReopenEvaluator(conditions=[condition], evidence_registry=registry,
                           applicability=applicability).evaluate(
        condition.subject_ref, facts)


def _evidence_registry(*ids):
    from engine.evidence import EvidenceRecord
    from engine.registry import EvidenceRegistry

    reg = EvidenceRegistry()
    for i, rid in enumerate(ids):
        reg.register(EvidenceRecord(record_id=rid, kind="OBSERVATION",
                                    claim=f"ev {rid}", seq=i))
    return reg


def _cond(subject, field="sensor_online", expected_value=True, evidence_refs=(),
          scope="", domain=""):
    from engine.reopen import ReopenCondition
    return ReopenCondition.make(1, subject_ref=subject, field=field,
                                expected_value=expected_value,
                                evidence_required=True, evidence_refs=evidence_refs,
                                scope=scope, domain=domain)


def test_evidence_exists_but_wrong_subject_rejected():
    c = _cond("K", evidence_refs=["E-A"])
    app = _applicability(**{"E-A": {"evidence_id": "E-A", "subject_ref": "OTHER"}})
    ev = _eval_evidence(c, {"sensor_online": True, "evidence_refs": ["E-A"]},
                        _evidence_registry("E-A"), app)
    assert ev.outcome == "NO_REOPEN"
    assert "evidence_not_admissible" in ev.condition_results[0]["reason"]


def test_evidence_exists_but_wrong_scope_rejected():
    c = _cond("K", evidence_refs=["E-A"], scope="FX/EURUSD")
    app = _applicability(**{"E-A": {"evidence_id": "E-A", "subject_ref": "K",
                                    "scope": "CRYPTO/OI"}})
    ev = _eval_evidence(c, {"sensor_online": True, "evidence_refs": ["E-A"]},
                        _evidence_registry("E-A"), app)
    assert ev.outcome == "NO_REOPEN"
    assert "scope-mismatch" in ev.condition_results[0]["reason"]


def test_evidence_exists_but_wrong_domain_rejected():
    """CRYPTO/OI evidence cannot satisfy an FX/EURUSD condition unless an
    explicit transfer contract permits it."""
    c = _cond("K", evidence_refs=["E-A"], domain="FX/EURUSD")
    app = _applicability(**{"E-A": {"evidence_id": "E-A", "subject_ref": "K",
                                    "domain": "CRYPTO/OI", "admissible_use": ["FIELD_PREDICATE"]}})
    ev = _eval_evidence(c, {"sensor_online": True, "evidence_refs": ["E-A"]},
                        _evidence_registry("E-A"), app)
    assert ev.outcome == "NO_REOPEN"
    assert "domain-mismatch" in ev.condition_results[0]["reason"]

    # explicit governed transfer contract permits cross-domain applicability
    app2 = _applicability(**{"E-A": {"evidence_id": "E-A", "subject_ref": "K",
                                     "domain": "CRYPTO/OI",
                                     "admissible_use": ["TRANSFER:FX/EURUSD"]}})
    ev2 = _eval_evidence(c, {"sensor_online": True, "evidence_refs": ["E-A"]},
                         _evidence_registry("E-A"), app2)
    assert ev2.outcome == "REOPEN_CANDIDATE"


def test_correct_applicability_passes():
    c = _cond("K", evidence_refs=["E-A"], scope="FX/EURUSD", domain="FX/EURUSD")
    app = _applicability(**{"E-A": {"evidence_id": "E-A", "subject_ref": "K",
                                    "scope": "FX/EURUSD", "domain": "FX/EURUSD",
                                    "admissible_use": ["FIELD_PREDICATE"]}})
    ev = _eval_evidence(c, {"sensor_online": True, "evidence_refs": ["E-A"]},
                        _evidence_registry("E-A"), app)
    assert ev.outcome == "REOPEN_CANDIDATE"


def test_phantom_reopen_evidence_rejected():
    """CASE C: condition requires E99; facts claim E99; registry has no E99."""
    c = _cond("K", evidence_refs=["E99"])
    app = _applicability(**{"E99": {"evidence_id": "E99", "subject_ref": "K"}})
    ev = _eval_evidence(c, {"sensor_online": True, "evidence_refs": ["E99"]},
                        _evidence_registry("E-A"), app)
    assert ev.outcome == "NO_REOPEN"
    assert "evidence_phantom" in ev.condition_results[0]["reason"]


def test_historical_evidence_link_retains_epoch():
    app = _applicability(**{"E-HIST": {"evidence_id": "E-HIST", "subject_ref": "K",
                                       "scope": "FX/EURUSD", "epoch": "E17"}})
    link = app["E-HIST"]
    assert link.epoch == "E17"
    assert link.version_tag == "1.0.0"


# --------------------------------------------------------------------------- #
# P0-D — canonical artifact deep immutability + fingerprint verification
# --------------------------------------------------------------------------- #
def test_nested_artifact_content_cannot_mutate_after_registration():
    from engine.reconstruction import CanonicalArtifact

    original = {"nested": {"deep": [1, 2]}}
    artifact = CanonicalArtifact.make("EVALUATION_CONTRACT", "EVAL:1.0", original)
    original["nested"]["deep"].append(3)          # caller mutates ITS dict
    original["nested"]["deep"][0] = 999           # and again
    assert artifact.content == {"nested": {"deep": [1, 2]}}
    view = artifact.content_view()
    view["nested"]["deep"].append(4)              # mutate the returned copy
    assert artifact.content == {"nested": {"deep": [1, 2]}}


def test_valid_artifact_roundtrip_succeeds():
    from engine.reconstruction import CanonicalArtifact, CanonicalArtifactRegistry

    reg = CanonicalArtifactRegistry()
    art = CanonicalArtifact.make("EVALUATION_CONTRACT", "EVAL:1.0",
                                 {"contract_id": "EVAL", "version": "1.0"})
    reg.register(art)                             # fingerprint verified on entry
    assert reg.resolve("EVALUATION_CONTRACT", "EVAL:1.0").artifact_id == "EVAL:1.0"


def test_stale_artifact_fingerprint_rejected():
    from engine.reconstruction import (CanonicalArtifact, CanonicalArtifactRegistry,
                                       ReconstructionError)

    reg = CanonicalArtifactRegistry()
    stale = CanonicalArtifact("EVALUATION_CONTRACT", "EVAL:1.0", "deadbeef")
    with pytest.raises(ReconstructionError):
        reg.register(stale)


def test_manually_constructed_wrong_fingerprint_rejected():
    """content=A with fingerprint=hash(B) can never be registered (P0-D)."""
    from engine.reconstruction import (CanonicalArtifact, CanonicalArtifactRegistry,
                                       ReconstructionError)

    reg = CanonicalArtifactRegistry()
    wrong = CanonicalArtifact.make("EVALUATION_CONTRACT", "EVAL:1.0",
                                   {"contract_id": "EVAL", "version": "1.0"},
                                   )
    spoofed = CanonicalArtifact(kind=wrong.kind, artifact_id=wrong.artifact_id,
                                content={"contract_id": "SPOOF"},
                                fingerprint=wrong.fingerprint)
    with pytest.raises(ReconstructionError):
        reg.register(spoofed)


# --------------------------------------------------------------------------- #
# P0-E — registered manifest identity
# --------------------------------------------------------------------------- #
def _manifest(epoch_id="E17"):
    from engine.epoch import EpochManifest

    m = EpochManifest(epoch_id=epoch_id, governing_architecture_versions=["A-009:1.0"],
                      evaluation_contract_version="EVAL:1.0",
                      lifecycle_contract_version="LC:1.0",
                      authority_snapshot_ref="AUTH_SNAP:E17",
                      authority_state_snapshot={"GOVERNOR": "GOVERNOR"})
    m.seal()
    return m


def _full_registry(m):
    from engine.reconstruction import (CanonicalArtifact, CanonicalArtifactRegistry,
                                       EpochReconstructionBundle)

    reg = CanonicalArtifactRegistry()
    reg.register_manifest(m)
    reg.register(CanonicalArtifact.make("EVALUATION_CONTRACT", "EVAL:1.0",
                                        {"contract_id": "EVAL", "version": "1.0"},
                                        epoch_id="E17"))
    reg.register(CanonicalArtifact.make("LIFECYCLE_CONTRACT", "LC:1.0",
                                        {"contract_id": "LC", "version": "1.0"},
                                        epoch_id="E17"))
    reg.register(CanonicalArtifact.make("AUTHORITY_SNAPSHOT", "AUTH_SNAP:E17",
                                        dict(m.authority_state_snapshot), epoch_id="E17"))
    bundle = EpochReconstructionBundle.for_manifest(m)
    return reg, bundle


def test_unregistered_sealed_manifest_fails():
    from engine.reconstruction import (CanonicalArtifact, CanonicalArtifactRegistry,
                                       ReconstructionError)

    m = _manifest()
    reg = CanonicalArtifactRegistry()
    # register everything EXCEPT the manifest itself
    reg.register(CanonicalArtifact.make("EVALUATION_CONTRACT", "EVAL:1.0",
                                        {"contract_id": "EVAL", "version": "1.0"}))
    with pytest.raises(ReconstructionError):
        reg.resolve_manifest_artifact(m)


def test_registered_manifest_content_mismatch_fails():
    """A registered artifact at the same id whose content differs from the
    bundle manifest fails closed (fingerprint verify in resolve)."""
    from engine.reconstruction import (CanonicalArtifact, CanonicalArtifactRegistry,
                                       EpochReconstructionBundle, ReconstructionError,
                                       reconstruct_epoch)

    m = _manifest()
    reg = CanonicalArtifactRegistry()
    # register a SEMANTICALLY-DIFFERENT manifest under the same epoch id
    from engine.epoch import EpochManifest
    other = EpochManifest(epoch_id="E17", governing_architecture_versions=["A-999:9.9"],
                          evaluation_contract_version="EVAL:1.0",
                          lifecycle_contract_version="LC:1.0",
                          authority_snapshot_ref="AUTH_SNAP:E17",
                          authority_state_snapshot={"GOVERNOR": "GOVERNOR"})
    other.seal()
    reg.register(CanonicalArtifact.make("SEALED_EPOCH_MANIFEST", "E17", other.to_dict(),
                                        epoch_id="E17"))
    reg.register(CanonicalArtifact.make("EVALUATION_CONTRACT", "EVAL:1.0",
                                        {"contract_id": "EVAL", "version": "1.0"}))
    reg.register(CanonicalArtifact.make("LIFECYCLE_CONTRACT", "LC:1.0",
                                        {"contract_id": "LC", "version": "1.0"}))
    reg.register(CanonicalArtifact.make("AUTHORITY_SNAPSHOT", "AUTH_SNAP:E17",
                                        dict(m.authority_state_snapshot), epoch_id="E17"))
    report = reconstruct_epoch(EpochReconstructionBundle.for_manifest(m), reg, "R")
    assert report.success is False
    assert "sealed_epoch_manifest" in report.missing_surfaces


def test_registered_manifest_fingerprint_mismatch_fails():
    from engine.reconstruction import (CanonicalArtifact, CanonicalArtifactRegistry,
                                       ReconstructionError)

    m = _manifest()
    reg = CanonicalArtifactRegistry()
    wrong = CanonicalArtifact("SEALED_EPOCH_MANIFEST", "E17", "deadbeef",
                              content=m.to_dict(), epoch_id="E17")
    with pytest.raises(ReconstructionError):
        reg.register(wrong)


def test_bundle_epoch_id_must_equal_manifest_epoch_id():
    """P0-E: a bundle whose epoch id disagrees with the sealed manifest's epoch
    id fails closed at reconstruction."""
    from engine.reconstruction import (CanonicalArtifactRegistry,
                                       EpochReconstructionBundle,
                                       reconstruct_epoch)

    m = _manifest(epoch_id="E17")
    b = EpochReconstructionBundle(epoch_id="E99", sealed_epoch_manifest=m)
    reg = CanonicalArtifactRegistry()
    reg.register_manifest(m)
    contract = {"required_surfaces": ["sealed_epoch_manifest",
                                      "evaluation_contract",
                                      "lifecycle_contract",
                                      "authority_state_snapshot"]}
    report = reconstruct_epoch(b, reg, "R", contract=contract)
    assert report.success is False
    assert "sealed_epoch_manifest" in report.invalid_surfaces


# --------------------------------------------------------------------------- #
# P0-F — no synthetic authority snapshot ref
# --------------------------------------------------------------------------- #
def test_blank_authority_snapshot_ref_does_not_infer_name():
    from engine.epoch import EpochManifest
    from engine.reconstruction import (CanonicalArtifact, CanonicalArtifactRegistry,
                                       EpochReconstructionBundle, reconstruct_epoch)

    m = EpochManifest(epoch_id="E17", authority_state_snapshot={"GOVERNOR": "GOVERNOR"},
                      authority_snapshot_ref="")     # blank — no synthetic ref
    m.seal()
    reg = CanonicalArtifactRegistry()
    bundle = EpochReconstructionBundle.for_manifest(m)
    assert bundle.authority_snapshot_ref == ""
    reg.register_manifest(m)
    report = reconstruct_epoch(bundle, reg, "R")
    assert report.success is False
    assert "authority_state_snapshot" in report.missing_surfaces


def test_explicit_authority_snapshot_ref_resolves():
    from engine.reconstruction import (CanonicalArtifact, CanonicalArtifactRegistry,
                                       EpochReconstructionBundle, reconstruct_epoch)

    m = _manifest()      # ref = AUTH_SNAP:E17
    reg, bundle = _full_registry(m)
    contract = {"required_surfaces": ["sealed_epoch_manifest",
                                      "evaluation_contract",
                                      "lifecycle_contract",
                                      "authority_state_snapshot"]}
    report = reconstruct_epoch(bundle, reg, "R", contract=contract)
    assert report.success is True
    assert "authority_state_snapshot" in report.resolved_surfaces


# --------------------------------------------------------------------------- #
# P0-G — sealed epoch snapshot is reconstruction truth
# --------------------------------------------------------------------------- #
def test_sealed_epoch_snapshot_is_frozen_reconstruction_truth():
    from engine.epoch import EpochManifest, SealedEpochSnapshot

    m = _manifest()
    snap = SealedEpochSnapshot.from_manifest(m)
    assert snap.epoch_id == "E17"
    assert snap.fingerprint == m.fingerprint()
    nested = snap.semantic_content
    nested["active_ontology_versions"] = ["HACKED"]    # mutate the returned copy
    assert snap.semantic_content["active_ontology_versions"] == []
    assert snap.semantic_fingerprint() == SealedEpochSnapshot.from_manifest(m).semantic_fingerprint()


def test_seal_threat_model_documented_honestly():
    """P0-G: the module docs state the honest boundary. The institution relies
    on supported-API immutability + fingerprint verification, not a claim of
    cryptographic tamper-proofness against arbitrary memory manipulation."""
    from engine import reconstruction
    import inspect

    doc = inspect.getdoc(reconstruction).lower()
    assert "supported" in doc and "api" in doc
    assert "tamper-proofness" in doc
    assert "arbitrary interpreter-memory manipulation" in doc
    from engine.reconstruction import PROVISIONAL_EPOCH_RECONSTRUCTION_CONTRACT
    assert PROVISIONAL_EPOCH_RECONSTRUCTION_CONTRACT["status"] == "PROVISIONAL_TEST_CONTRACT"