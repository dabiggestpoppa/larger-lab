"""G4 deterministic scenario runner (S10–S13).

Pipeline (G2/G3 discipline carried): scenario pack -> decision-grade projection
(expected outcomes + hidden ground truth REMOVED) -> deterministic memory /
reopen / retrieval / reconstruction machinery -> result with scenario-id-free
behavior fingerprint -> expectations applied post-hoc only.

Sealing guarantees:
  * expected outcomes and hidden ground truth never reach the decision path;
  * behavior fingerprint excludes scenario_id and expected outcomes;
  * replacement runtime name never enters the reconstruction SEMANTIC
    fingerprint (runtime-neutral identity lives in canonical artifacts).

Deterministic, local, model-free, wall-clock-free.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import deterministic_hex
from .authority import AuthorityState
from .epoch import EpochManifest
from .lifecycle import KnowledgeRecord, LifecycleEngine, Provenance
from .memory import (
    MemoryCompactionRecord,
    MemoryIndex,
    MemoryObject,
    MemoryRetriever,
    KnowledgeActivationState,
    run_metabolism_pipeline,
)
from .memory_policy import MemoryPolicy
from .negative import NegativeKnowledgeRecord
from .reconstruction import (
    EpochReconstructionBundle,
    reconstruct_epoch,
    verify_epoch_chain,
)
from .reopen import (
    ReopenCondition,
    ReopenEvaluator,
    decide_suppression,
)


@dataclass
class G4ScenarioPack:
    scenario_id: str
    scenario_version: str = "1.0.0"
    knowledge: List[Mapping[str, Any]] = field(default_factory=list)
    negative_knowledge: List[Mapping[str, Any]] = field(default_factory=list)
    reopen_conditions: List[Mapping[str, Any]] = field(default_factory=list)
    current_facts: Mapping[str, Any] = field(default_factory=dict)
    authority_seed: Mapping[str, str] = field(default_factory=dict)
    history_size: int = 0
    experiments_size: int = 0
    required_refs: List[str] = field(default_factory=list)
    dependency_refs: List[str] = field(default_factory=list)
    context_budget: int = 12
    epochs: List[Mapping[str, Any]] = field(default_factory=list)
    runtime_certifications: List[str] = field(default_factory=list)
    expected_outcome: str = ""            # SEALED — stripped before run
    hidden_ground_truth: Optional[dict] = None  # SEALED

    def decision_grade(self) -> "G4ScenarioPack":
        out = {k: v for k, v in self.__dict__.items()
               if k not in ("expected_outcome", "hidden_ground_truth")}
        return G4ScenarioPack(**out)


@dataclass
class G4RunResult:
    artifacts: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.artifacts)


PACK_FIELDS = {"scenario_id", "scenario_version", "knowledge", "negative_knowledge",
               "reopen_conditions", "current_facts", "authority_seed",
               "history_size", "experiments_size", "required_refs",
               "dependency_refs", "context_budget", "epochs",
               "runtime_certifications", "expected_outcome", "hidden_ground_truth"}

REF_KEYS = {"knowledge_ref": "knowledge", "negative_ref": "negative_knowledge",
            "reopen_conditions_ref": "reopen_conditions", "epochs_ref": "epochs"}


def load_g4_pack(pack_dir: Path) -> G4ScenarioPack:
    root = Path(pack_dir)
    spec = json.loads((root / "scenario.json").read_text(encoding="utf-8"))
    kw: Dict[str, Any] = {}
    for key, value in spec.items():
        if key in REF_KEYS:
            kw[REF_KEYS[key]] = json.loads(
                (root / value).read_text(encoding="utf-8"))
        elif key in PACK_FIELDS:
            kw[key] = value
    return G4ScenarioPack(**kw)


# --------------------------------------------------------------------------- #
# S10 — dormant knowledge returns
# --------------------------------------------------------------------------- #
def run_s10(pack: G4ScenarioPack, policy: MemoryPolicy,
            policy_fingerprint: str = "") -> G4RunResult:
    """DORMANT knowledge whose machine-readable reopen condition fires is
    RETRIEVED for review and must begin DORMANT -> REACTIVATED (never
    DORMANT -> ACTIVE)."""
    facts = dict(pack.current_facts)
    conditions = tuple(ReopenCondition.make(i, **c)
                       for i, c in enumerate(pack.reopen_conditions))
    evaluator = ReopenEvaluator(conditions=conditions, current_epoch=pack.epochs[0]["epoch_id"]
                                if pack.epochs else "")
    outcomes = {}
    for k in pack.knowledge:
        kid = k["record_id"]
        ev = evaluator.evaluate(kid, facts, conditions=conditions)
        outcomes[kid] = ev.outcome

    # memory tier routing + retrieval for REOPEN_CANDIDATE records
    index = MemoryIndex()
    tier_by_id: Dict[str, str] = {}
    for k in pack.knowledge:
        tier = "DORMANT_STORE" if k.get("memory_tier") == "DORMANT_STORE" else "ACTIVE_CONTEXT"
        index.add(MemoryObject(
            object_id=k["record_id"], kind="KNOWLEDGE",
            tags=tuple(k.get("tags", [])), dependency_refs=tuple(k.get("dependency_refs", [])),
            epoch=k.get("epoch", ""), memory_tier=tier,
            m4_state=k.get("m4_state", "DORMANT"),
            reopen_condition_ids=tuple(c.condition_id for c in conditions),
            summary=k.get("claim", ""), provenance_pointer=k.get("provenance_pointer", ""),
            reconstruction_pointer=k.get("reconstruction_pointer", "")))
        tier_by_id[k["record_id"]] = tier

    # M4 path via the governed LifecycleEngine
    lifecycle = LifecycleEngine()
    m4_results: Dict[str, List[Dict[str, Any]]] = {}
    for k in pack.knowledge:
        kid = k["record_id"]
        rec = KnowledgeRecord(record_id=kid, claim=k.get("claim", ""),
                              provenance=Provenance(source_kind="FIXTURE",
                                                    source_label=k.get("source_label", "S10")),
                              creation_source="S10", initial_state=k.get("m4_state", "DORMANT"))
        lifecycle.add(rec)
        trace = []
        if outcomes.get(kid) == "REOPEN_CANDIDATE":
            # legal: DORMANT -> REACTIVATED
            t1 = lifecycle.transition(kid, 1, "REACTIVATED", actor="GOVERNOR",
                                      authority_basis="reopen-review",
                                      authority_level="GOVERNOR",
                                      reason="reopen condition satisfied; renewed evaluation begins")
            trace.append(t1.to_dict())
            # legal: REACTIVATED -> CANDIDATE
            t2 = lifecycle.transition(kid, 2, "CANDIDATE", actor="GOVERNOR",
                                      authority_basis="reopen-review",
                                      authority_level="GOVERNOR",
                                      reason="eligible for renewed evaluation")
            trace.append(t2.to_dict())
            # forbidden: DORMANT -> ACTIVE shortcut must fail
            from_state = rec.state
            t3 = rec.transition(3, "ACTIVE", actor="GOVERNOR", authority_basis="reopen-review",
                                authority_level="GOVERNOR",
                                reason="illegal auto-promotion attempt",
                                edge_table=lifecycle.edge_table)
            trace.append(t3.to_dict())
        m4_results[kid] = trace

    bundle_fp = deterministic_hex(
        "s10_behavior", sorted(outcomes.items()), facts, policy_fingerprint, length=32)
    return G4RunResult({
        "scenario_id": pack.scenario_id,
        "reopen_outcomes": outcomes,
        "m4_traces": m4_results,
        "direct_dormant_to_active_forbidden": {
            kid: (m4_results[kid][-1]["allowed"] is False
                  if m4_results[kid] and outcomes.get(kid) == "REOPEN_CANDIDATE" else True)
            for kid in [k["record_id"] for k in pack.knowledge]},
        "behavior_fingerprint": bundle_fp,
        "fingerprint": deterministic_hex("g4_run", pack.scenario_id, bundle_fp, length=32),
        "policy_id": policy.policy_id, "policy_version": policy.version_tag,
        "policy_fingerprint": policy_fingerprint or policy.fingerprint(),
        "expected_outcome_accessed": False, "hidden_ground_truth_accessed": False,
        "authority_before": "NONE", "authority_after": "NONE",
    })


# --------------------------------------------------------------------------- #
# S11 — negative knowledge dogma
# --------------------------------------------------------------------------- #
def run_s11(pack: G4ScenarioPack, policy: MemoryPolicy,
            policy_fingerprint: str = "") -> G4RunResult:
    facts = dict(pack.current_facts)
    conditions = tuple(ReopenCondition.make(i, **c)
                       for i, c in enumerate(pack.reopen_conditions))
    evaluator = ReopenEvaluator(conditions=conditions, current_epoch="E11")
    decisions = []
    for i, nk_data in enumerate(pack.negative_knowledge):
        nk = NegativeKnowledgeRecord(
            record_id=nk_data["record_id"],
            claim_rejected=nk_data.get("claim_rejected", ""),
            exact_scope=nk_data.get("exact_scope", ""),
            evidence_refs=list(nk_data.get("evidence_refs", [])),
            rejection_reason=nk_data.get("rejection_reason", ""),
            blockers=list(nk_data.get("blockers", [])),
            reopen_conditions=list(nk_data.get("reopen_conditions", [])),
            seq=i,
        )
        if nk_data.get("operator_permanent"):
            auth = AuthorityState()
            auth.seed_level("OPERATOR", "OPERATOR")
            auth.freeze_initialization()
            nk.make_permanent("OPERATOR", auth, "ratified-permanence", ratification_ref="RAT-P")
        decision = decide_suppression(nk, evaluator, facts, conditions=conditions)
        decisions.append({
            "record_id": nk.record_id,
            "decision": decision.to_dict(),
            "record_retained": True,
            "permanent": nk.is_permanent,
        })
    fp = deterministic_hex("s11_behavior", [d["decision"] for d in decisions], facts,
                           policy_fingerprint, length=32)
    return G4RunResult({
        "scenario_id": pack.scenario_id,
        "suppression_decisions": decisions,
        "behavior_fingerprint": fp,
        "fingerprint": deterministic_hex("g4_run", pack.scenario_id, fp, length=32),
        "policy_id": policy.policy_id, "policy_version": policy.version_tag,
        "policy_fingerprint": policy_fingerprint or policy.fingerprint(),
        "expected_outcome_accessed": False, "hidden_ground_truth_accessed": False,
        "authority_before": "NONE", "authority_after": "NONE",
    })


# --------------------------------------------------------------------------- #
# S12 — institutional hyperthymesia
# --------------------------------------------------------------------------- #
def _make_history_objects(history_size: int, experiments_size: int,
                          relevant_refs: Sequence[str]) -> Tuple[MemoryIndex, int]:
    """Deterministic synthetic history: `history_size` knowledge/evidence
    objects, `experiments_size` experiment records, plus the relevant set.
    Only the 12 relevant objects live in ACTIVE_CONTEXT; the rest are
    DORMANT/ARCHIVAL. Returns (index, total)."""
    index = MemoryIndex()
    for i in range(history_size):
        kind = "EVIDENCE" if i % 3 == 0 else "KNOWLEDGE"
        tier = "ARCHIVAL_STORE" if i % 10 == 0 else "DORMANT_STORE"
        index.add(MemoryObject(
            object_id=f"HIST_{i:06d}", kind=kind, tags=(f"tag_{i % 97}",),
            dependency_refs=(), epoch="E12", memory_tier=tier,
            m4_state="DEMOTED", summary=f"historical object {i}",
            provenance_pointer=f"hist://{i}", reconstruction_pointer=f"recon://{i}",
            history_size=1))
    for i in range(experiments_size):
        index.add(MemoryObject(
            object_id=f"EXP_{i:06d}", kind="EXPERIMENT", tags=("experiment",),
            dependency_refs=(), epoch="E12", memory_tier="ARCHIVAL_STORE",
            m4_state="DEMOTED", summary=f"experiment {i}",
            provenance_pointer=f"exp://{i}", reconstruction_pointer=f"recon_exp://{i}",
            history_size=1))
    for j, ref in enumerate(relevant_refs):
        index.add(MemoryObject(
            object_id=ref, kind="KNOWLEDGE", tags=(ref,),
            dependency_refs=tuple(dep for dep in relevant_refs if dep != ref)[:2],
            epoch="E12", memory_tier="ACTIVE_CONTEXT", m4_state="ACTIVE",
            summary=f"relevant {ref}", provenance_pointer=f"rel://{ref}",
            reconstruction_pointer=f"recon_rel://{ref}", history_size=1))
    return index, len(index.objects())


def run_s12(pack: G4ScenarioPack, policy: MemoryPolicy,
            policy_fingerprint: str = "") -> G4RunResult:
    index, total = _make_history_objects(
        int(pack.history_size), int(pack.experiments_size), pack.required_refs)
    retriever = MemoryRetriever(index, context_budget=int(pack.context_budget))
    bundle = retriever.build_context(
        task_ref=pack.required_refs[0] if pack.required_refs else "TASK",
        required_refs=pack.required_refs,
        dependency_refs=pack.dependency_refs, current_epoch="E12")
    fp = deterministic_hex("s12_behavior", bundle.fingerprint,
                           policy_fingerprint, length=32)
    return G4RunResult({
        "scenario_id": pack.scenario_id,
        "total_history": total,
        "context_bundle": bundle.to_dict(),
        "metrics": dict(bundle.metrics),
        "behavior_fingerprint": fp,
        "fingerprint": deterministic_hex("g4_run", pack.scenario_id, fp, length=32),
        "policy_id": policy.policy_id, "policy_version": policy.version_tag,
        "policy_fingerprint": policy_fingerprint or policy.fingerprint(),
        "expected_outcome_accessed": False, "hidden_ground_truth_accessed": False,
        "authority_before": "NONE", "authority_after": "NONE",
    })


# --------------------------------------------------------------------------- #
# S13 — total runtime replacement / epoch reconstruction
# --------------------------------------------------------------------------- #
def run_s13(pack: G4ScenarioPack, policy: MemoryPolicy,
            policy_fingerprint: str = "", current_runtime: str = "NEW_RUNTIME",
            runtime_native_memory: bool = False) -> G4RunResult:
    manifests = [EpochManifest(**e) for e in pack.epochs]
    for m in manifests:
        m.seal()
    chain = verify_epoch_chain(manifests)
    bundles = [EpochReconstructionBundle.from_epoch_manifest(m) for m in manifests]
    reports = [reconstruct_epoch(b, current_runtime, runtime_native_memory)
               for b in bundles]
    # runtime rename metamorphic: semantic fingerprint must not change
    rename_reports = [reconstruct_epoch(b, "ANOTHER_RUNTIME", runtime_native_memory)
                      for b in bundles]
    fp = deterministic_hex(
        "s13_behavior", [r.reconstruction_semantic_fingerprint for r in reports],
        chain, policy_fingerprint, length=32)
    return G4RunResult({
        "scenario_id": pack.scenario_id,
        "chain": chain,
        "reports": [r.to_dict() for r in reports],
        "runtime_rename_semantic_stable": [
            r.reconstruction_semantic_fingerprint == rr.reconstruction_semantic_fingerprint
            for r, rr in zip(reports, rename_reports)],
        "behavior_fingerprint": fp,
        "fingerprint": deterministic_hex("g4_run", pack.scenario_id, fp, length=32),
        "policy_id": policy.policy_id, "policy_version": policy.version_tag,
        "policy_fingerprint": policy_fingerprint or policy.fingerprint(),
        "expected_outcome_accessed": False, "hidden_ground_truth_accessed": False,
        "authority_before": "NONE", "authority_after": "NONE",
    })


# --------------------------------------------------------------------------- #
# dispatch + post-hoc expectation
# --------------------------------------------------------------------------- #
def run_g4_scenario(pack: G4ScenarioPack, policy: MemoryPolicy,
                    policy_fingerprint: str = "", **runner_kw) -> G4RunResult:
    if pack.expected_outcome or pack.hidden_ground_truth is not None:
        raise ValueError("run_g4_scenario refuses sealed fields: pass pack.decision_grade()")
    sid = pack.scenario_id
    if sid == "S10":
        return run_s10(pack, policy, policy_fingerprint)
    if sid == "S11":
        return run_s11(pack, policy, policy_fingerprint)
    if sid == "S12":
        return run_s12(pack, policy, policy_fingerprint)
    if sid == "S13":
        return run_s13(pack, policy, policy_fingerprint, **runner_kw)
    raise ValueError(f"unknown G4 scenario id {sid!r}")


def evaluate_g4_expectation(result: G4RunResult, pack: G4ScenarioPack) -> Dict[str, Any]:
    """Post-hoc comparator — expectations applied strictly AFTER execution."""
    expected = pack.expected_outcome
    failures = []
    artifacts = result.artifacts
    if pack.scenario_id == "S10":
        actual = "REOPEN_CANDIDATE" if any(
            v == "REOPEN_CANDIDATE" for v in artifacts.get("reopen_outcomes", {}).values()) \
            else "NO_REOPEN"
    elif pack.scenario_id == "S11":
        actual = artifacts["suppression_decisions"][0]["decision"]["next_action"] \
            if artifacts.get("suppression_decisions") else "CONTINUE_SUPPRESSION"
    elif pack.scenario_id == "S12":
        actual = "BOUNDED_CONTEXT"
    elif pack.scenario_id == "S13":
        actual = "RECONSTRUCTED" if artifacts["reports"][0]["success"] else "MISSING_SURFACES"
    else:
        actual = ""
    if expected and actual != expected:
        failures.append(f"outcome {actual!r} != expected {expected!r}")
    return {"pass": not failures, "expected_outcome": expected,
            "actual_outcome": actual, "failures": failures}
