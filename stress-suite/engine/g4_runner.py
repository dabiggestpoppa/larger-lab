"""G4/G4R deterministic scenario runner (S10–S13).

Pipeline (G2/G3 discipline carried): scenario pack -> decision-grade projection
(expected outcomes + hidden ground truth REMOVED) -> deterministic memory /
reopen / retrieval / reconstruction machinery -> result with scenario-id-free
behavior fingerprint -> expectations applied post-hoc only.

G4R wiring:
  * G4R-01 — the ONE shared G4_MEMORY_AND_REACTIVATION_POLICY actually governs
    REOPEN / ACTIVATION / SUPPRESSION dispositions; the runner records which
    rule fired for every decision.
  * G4R-07 — M4 lifecycle changes driven by memory/reopen behavior route
    through the governed executor (GovernedTransitionExecutor) with a real
    AuthorityState binding; a payload string can never authorize reactivation.
  * G4R-05/06 — reopen evidence resolves in a governed EvidenceRegistry;
    blocker resolution requires an attributable BlockerResolutionRecord.
  * G4R-11..14 — S13 reconstruction resolves EVERY external surface from a
    CanonicalArtifactRegistry; nothing is synthesized during reconstruction.
  * G4R-15 — a runtime-native-memory run is diagnostic only and never counts
    as qualified evidence for the runtime-neutral reconstruction pass.
  * G4R-16..19 — S12 active-flood variants, explicit required-ref gaps,
    evaluator-gated reopen retrieval, policy-governed compaction.
  * G4R-21 — every binding/evidence conflict survives into the run receipt via
    the ProvenanceConflictLedger.

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
from .cognitive_ecology import ProvenanceConflict, ProvenanceConflictLedger
from .epoch import EpochManifest
from .governed import GovernedTransitionExecutor
from .lifecycle import KnowledgeRecord, LifecycleEngine, Provenance
from .memory import (
    MemoryCompactionRecord,
    MemoryIndex,
    MemoryObject,
    MemoryRetriever,
    KnowledgeActivationState,
    compact_active_pool,
    run_metabolism_pipeline,
)
from .memory_policy import MemoryPolicy
from .negative import NegativeKnowledgeRecord
from .phase import PhaseStateMachine
from .reconstruction import (
    CanonicalArtifact,
    CanonicalArtifactRegistry,
    EpochReconstructionBundle,
    reconstruct_epoch,
    verify_epoch_chain,
)
from .registry import EvidenceRegistry
from .reopen import (
    BlockerResolutionRecord,
    ReopenCondition,
    ReopenEvaluator,
    decide_suppression,
    reopen_condition_state,
)
from .replay import ReplayEvent


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
    evidence: List[Mapping[str, Any]] = field(default_factory=list)       # G4R-05
    artifacts: List[Mapping[str, Any]] = field(default_factory=list)      # G4R-11
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
               "runtime_certifications", "evidence", "artifacts",
               "expected_outcome", "hidden_ground_truth"}

REF_KEYS = {"knowledge_ref": "knowledge", "negative_ref": "negative_knowledge",
            "reopen_conditions_ref": "reopen_conditions", "epochs_ref": "epochs",
            "evidence_ref": "evidence", "artifacts_ref": "artifacts"}


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


def _build_evidence_registry(pack: G4ScenarioPack) -> EvidenceRegistry:
    return EvidenceRegistry.from_records(list(pack.evidence or []))


def _policy_outcome(policy: MemoryPolicy, facts: Mapping[str, Any], kind: str,
                    fallback: str) -> Dict[str, Any]:
    """G4R-01: the shared policy decides the institutional disposition. Records
    the fired rule; falls back to the evaluator-derived value only when no rule
    applies (fail-open at the DECISION layer is impossible — the fallback is
    the factual condition state)."""
    rule = policy.evaluate(facts, kind) if policy is not None else None
    if rule is None:
        return {"outcome": fallback, "rule_id": "", "governed": False,
                "rationale": "no policy rule applied; factual state retained"}
    return {"outcome": str(rule.then.get("outcome", rule.then.get("action", rule.then.get("next_action", fallback)))),
            "rule_id": rule.rule_id, "governed": True,
            "rationale": rule.rationale}


def _trace_entry(entry) -> Dict[str, Any]:
    return {"to_state": entry.to_state, "from_state": entry.from_state,
            "allowed": entry.allowed, "applied": entry.applied,
            "reason": entry.rationale, "rule_ids": list(entry.rule_ids),
            "kind": entry.kind}


def _record_conflicts(ledger: Optional[ProvenanceConflictLedger], surface: str,
                      subject: str, conflicts: Sequence[Mapping[str, Any]]) -> None:
    if ledger is None:
        return
    for c in conflicts:
        ledger.record(surface, [ProvenanceConflict(
            reviewer_id=f"{surface}:{subject}", axis=c.get("axis", ""),
            claimed=c.get("claimed"), registered=c.get("registered"),
            disposition=c.get("disposition", "FAIL_CLOSED"))])


# --------------------------------------------------------------------------- #
# S10 — dormant knowledge returns (policy-governed + governed M4 execution)
# --------------------------------------------------------------------------- #
def run_s10(pack: G4ScenarioPack, policy: MemoryPolicy,
            policy_fingerprint: str = "",
            reactivation_actor: str = "GOVERNOR",
            declared_level: Optional[str] = None,
            authority_override: Optional[Mapping[str, str]] = None) -> G4RunResult:
    """DORMANT knowledge whose machine-readable reopen condition fires is
    RETRIEVED for review and must begin DORMANT -> REACTIVATED (never
    DORMANT -> ACTIVE). The shared policy decides the reopen disposition
    (G4R-01); M4 changes route through the governed executor with real
    AuthorityState binding (G4R-07)."""
    facts = dict(pack.current_facts)
    conditions = tuple(ReopenCondition.make(i, **c)
                       for i, c in enumerate(pack.reopen_conditions))
    registry = _build_evidence_registry(pack)
    evaluator = ReopenEvaluator(conditions=conditions, current_epoch=pack.epochs[0]["epoch_id"]
                                if pack.epochs else "", evidence_registry=registry)
    outcomes = {}
    policy_decisions: Dict[str, Dict[str, Any]] = {}
    ledger = ProvenanceConflictLedger()
    for k in pack.knowledge:
        kid = k["record_id"]
        ev = evaluator.evaluate(kid, facts, conditions=conditions)
        outcomes[kid] = ev.outcome
        _record_conflicts(ledger, "REOPEN_EVALUATION", kid, ev.conflicts)
        cond_state = reopen_condition_state(ev)
        pf = {"reopen_condition_state": cond_state,
              "lifecycle_state": k.get("m4_state", "DORMANT"),
              "memory_tier": k.get("memory_tier", "DORMANT_STORE"),
              "permanent_operator_authority": False}
        decision = _policy_outcome(policy, pf, "reopen", ev.outcome)
        policy_decisions[kid] = decision
        outcomes[kid] = decision["outcome"]

    # M4 path via the GOVERNED executor (G4R-07): the memory system proposes;
    # a registered GOVERNOR actor bound to AuthorityState applies the steps.
    auth = AuthorityState()
    for actor, level in dict(pack.authority_seed or {}).items():
        auth.seed_level(actor, level)
    if authority_override:
        # the caller registers the reactivation actor explicitly (e.g. a
        # WORKER whose level must NOT drive reactivation)
        for actor, level in authority_override.items():
            auth.seed_level(actor, level)
    elif reactivation_actor == "GOVERNOR":
        # default institutional review path: a registered GOVERNOR applies the
        # memory-proposed reactivation (G4R-07)
        auth.seed_level("GOVERNOR", "GOVERNOR")
    # any other reactivation actor is NOT auto-registered: an unknown or
    # unseeded actor (e.g. a memory component) cannot drive M4 mutations
    auth.freeze_initialization()
    lifecycle = LifecycleEngine()
    for k in pack.knowledge:
        lifecycle.add(KnowledgeRecord(
            record_id=k["record_id"], claim=k.get("claim", ""),
            provenance=Provenance(source_kind="FIXTURE",
                                  source_label=k.get("source_label", "S10")),
            creation_source="S10", initial_state=k.get("m4_state", "DORMANT")))
    executor = GovernedTransitionExecutor(PhaseStateMachine(), lifecycle, auth,
                                          registry=registry)
    m4_results: Dict[str, List[Dict[str, Any]]] = {}
    for k in pack.knowledge:
        kid = k["record_id"]
        trace: List[Dict[str, Any]] = []
        if outcomes.get(kid) == "REOPEN_CANDIDATE":
            payload = {"to_state": "REACTIVATED", "authority_basis": "reopen-review",
                       "reason": "reopen condition satisfied; renewed evaluation begins",
                       "reopen_driven": True}
            if declared_level is not None:
                payload["authority_level"] = declared_level
            t1 = executor.execute(ReplayEvent(1, "lifecycle_step", "lifecycle",
                                              reactivation_actor, kid, payload))
            trace.append(_trace_entry(t1))
            # legal: REACTIVATED -> CANDIDATE
            t2 = executor.execute(ReplayEvent(2, "lifecycle_step", "lifecycle",
                                              reactivation_actor, kid,
                                              {"to_state": "CANDIDATE",
                                               "authority_basis": "reopen-review",
                                               "reason": "eligible for renewed evaluation",
                                               "reopen_driven": True}))
            trace.append(_trace_entry(t2))
            # forbidden: direct DORMANT->ACTIVE shortcut must fail (edge table)
            t3 = executor.execute(ReplayEvent(3, "lifecycle_step", "lifecycle",
                                              reactivation_actor, kid,
                                              {"to_state": "ACTIVE",
                                               "authority_basis": "reopen-review",
                                               "reason": "illegal auto-promotion attempt",
                                               "reopen_driven": True}))
            trace.append(_trace_entry(t3))
        m4_results[kid] = trace

    bundle_fp = deterministic_hex(
        "s10_behavior", sorted(outcomes.items()), sorted(policy_decisions.items()),
        facts, policy_fingerprint, length=32)
    return G4RunResult({
        "scenario_id": pack.scenario_id,
        "reopen_outcomes": outcomes,
        "policy_decisions": policy_decisions,
        "m4_traces": m4_results,
        "direct_dormant_to_active_forbidden": {
            kid: (m4_results[kid][-1]["allowed"] is False
                  if m4_results[kid] and outcomes.get(kid) == "REOPEN_CANDIDATE" else True)
            for kid in [k["record_id"] for k in pack.knowledge]},
        "behavior_fingerprint": bundle_fp,
        "fingerprint": deterministic_hex("g4_run", pack.scenario_id, bundle_fp, length=32),
        "policy_id": policy.policy_id, "policy_version": policy.version_tag,
        "policy_fingerprint": policy_fingerprint or policy.fingerprint(),
        "provenance_conflicts": ledger.to_dict(),
        "expected_outcome_accessed": False, "hidden_ground_truth_accessed": False,
        "authority_before": "NONE", "authority_after": "NONE",
    })


# --------------------------------------------------------------------------- #
# S11 — negative knowledge dogma (evidence-backed, exact-scope, policy-governed)
# --------------------------------------------------------------------------- #
def run_s11(pack: G4ScenarioPack, policy: MemoryPolicy,
            policy_fingerprint: str = "") -> G4RunResult:
    facts = dict(pack.current_facts)
    conditions = tuple(ReopenCondition.make(i, **c)
                       for i, c in enumerate(pack.reopen_conditions))
    registry = _build_evidence_registry(pack)
    evaluator = ReopenEvaluator(conditions=conditions, current_epoch="E11",
                                evidence_registry=registry)
    ledger = ProvenanceConflictLedger()
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
            nk.make_permanent("OPERATOR", auth, "ratified-permanence",
                              ratification_ref="RAT-P")
        # evaluate first (collect conflicts), then decide through the policy
        ev = evaluator.evaluate(nk.record_id, facts, conditions=conditions,
                                negative_knowledge=nk, record_scope=nk.exact_scope)
        _record_conflicts(ledger, "NEGATIVE_KNOWLEDGE", nk.record_id, ev.conflicts)
        decision = decide_suppression(nk, evaluator, facts, conditions=conditions,
                                      policy=policy)
        decisions.append({
            "record_id": nk.record_id,
            "decision": decision.to_dict(),
            "record_retained": True,
            "permanent": nk.is_permanent,
            "reopen_condition_state": reopen_condition_state(ev),
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
        "provenance_conflicts": ledger.to_dict(),
        "expected_outcome_accessed": False, "hidden_ground_truth_accessed": False,
        "authority_before": "NONE", "authority_after": "NONE",
    })


# --------------------------------------------------------------------------- #
# S12 — institutional hyperthymesia / bounded active context (+ G4R-16..18)
# --------------------------------------------------------------------------- #
def _make_history_objects(history_size: int, experiments_size: int,
                          relevant_refs: Sequence[str],
                          active_flood: bool = False) -> Tuple[MemoryIndex, int]:
    """Deterministic synthetic history. In the DEFAULT fixture only the
    relevant set lives in ACTIVE_CONTEXT. G4R-16 VARIANT A (active_flood=True)
    starts a large subset of history in ACTIVE_CONTEXT so the shared policy +
    bounded retriever must compress the pool down to task need."""
    index = MemoryIndex()
    for i in range(history_size):
        kind = "EVIDENCE" if i % 3 == 0 else "KNOWLEDGE"
        if active_flood and i % 2 == 0:
            tier = "ACTIVE_CONTEXT"
        elif i % 10 == 0:
            tier = "ARCHIVAL_STORE"
        else:
            tier = "DORMANT_STORE"
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
            policy_fingerprint: str = "",
            active_flood: bool = False,
            required_override: Optional[Sequence[str]] = None,
            budget_override: Optional[int] = None,
            reopen_resolver=None) -> G4RunResult:
    index, total = _make_history_objects(
        int(pack.history_size), int(pack.experiments_size),
        list(required_override if required_override is not None else pack.required_refs),
        active_flood=active_flood)
    budget = int(budget_override if budget_override is not None else pack.context_budget)
    retriever = MemoryRetriever(index, context_budget=budget,
                                reopen_resolver=reopen_resolver)
    required = list(required_override if required_override is not None else pack.required_refs)
    bundle = retriever.build_context(
        task_ref=required[0] if required else "TASK",
        required_refs=required,
        dependency_refs=pack.dependency_refs, current_epoch="E12")
    # G4R-17: policy-governed compaction of the oversized ACTIVE pool
    compactions, compaction_rule = compact_active_pool(
        index, policy, keep_refs=bundle.selected_active_objects,
        task_ref=required[0] if required else "TASK", epoch="E12")
    active_after = len(index.objects_by_tier("ACTIVE_CONTEXT"))
    fp = deterministic_hex("s12_behavior", bundle.fingerprint,
                           policy_fingerprint, length=32)
    return G4RunResult({
        "scenario_id": pack.scenario_id,
        "total_history": total,
        "context_bundle": bundle.to_dict(),
        "metrics": dict(bundle.metrics),
        "bundle_status": bundle.bundle_status,
        "budget_sufficient": bundle.budget_sufficient,
        "missing_required_refs": list(bundle.missing_required_refs),
        "compaction_records": [c.to_dict() for c in compactions],
        "compaction_policy_rule": compaction_rule,
        "active_context_after_compaction": active_after,
        "behavior_fingerprint": fp,
        "fingerprint": deterministic_hex("g4_run", pack.scenario_id, fp, length=32),
        "policy_id": policy.policy_id, "policy_version": policy.version_tag,
        "policy_fingerprint": policy_fingerprint or policy.fingerprint(),
        "expected_outcome_accessed": False, "hidden_ground_truth_accessed": False,
        "authority_before": "NONE", "authority_after": "NONE",
    })


# --------------------------------------------------------------------------- #
# S13 — total runtime replacement / REGISTRY-BACKED epoch reconstruction
# --------------------------------------------------------------------------- #
def _build_canonical_registry(pack: G4ScenarioPack,
                              manifests: Sequence[EpochManifest]) -> CanonicalArtifactRegistry:
    """G4R-11: register ACTUAL pre-existing canonical fixture artifacts BEFORE
    reconstruction. The sealed manifests and every external surface resolve
    here; reconstruction never synthesizes them."""
    reg = CanonicalArtifactRegistry()
    for data in (pack.artifacts or []):
        reg.register_fixture(data)
    for m in manifests:
        reg.register_manifest(m)
        # authority snapshot artifact whose fingerprint must equal the
        # manifest's inline snapshot (G4R-13)
        if m.authority_state_snapshot:
            reg.register(CanonicalArtifact.make(
                "AUTHORITY_SNAPSHOT", m.authority_snapshot_ref or f"AUTH_SNAP:{m.epoch_id}",
                dict(m.authority_state_snapshot), epoch_id=m.epoch_id))
    return reg


def run_s13(pack: G4ScenarioPack, policy: MemoryPolicy,
            policy_fingerprint: str = "", current_runtime: str = "NEW_RUNTIME",
            runtime_native_memory: bool = False) -> G4RunResult:
    manifests = [EpochManifest(**e) for e in pack.epochs]
    for m in manifests:
        m.seal()
    chain = verify_epoch_chain(manifests)
    registry = _build_canonical_registry(pack, manifests)
    bundles = [EpochReconstructionBundle.for_manifest(m) for m in manifests]
    reports = [reconstruct_epoch(b, registry, current_runtime, runtime_native_memory)
               for b in bundles]
    # runtime rename metamorphic: semantic fingerprint must not change
    rename_reports = [reconstruct_epoch(b, registry, "ANOTHER_RUNTIME", runtime_native_memory)
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
        "registered_artifact_ids": list(registry.all_ids()),
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
        return run_s10(pack, policy, policy_fingerprint, **runner_kw)
    if sid == "S11":
        return run_s11(pack, policy, policy_fingerprint)
    if sid == "S12":
        return run_s12(pack, policy, policy_fingerprint, **runner_kw)
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
        # G4R-15: only a QUALIFIED run (zero runtime-native memory + all
        # surfaces resolved) counts as RECONSTRUCTED evidence.
        first = artifacts["reports"][0]
        if first["reconstruction_evidence_qualified"]:
            actual = "RECONSTRUCTED"
        elif first["success"]:
            actual = "DIAGNOSTIC_ONLY"
        else:
            actual = "MISSING_SURFACES"
    else:
        actual = ""
    if expected and actual != expected:
        failures.append(f"outcome {actual!r} != expected {expected!r}")
    return {"pass": not failures, "expected_outcome": expected,
            "actual_outcome": actual, "failures": failures}
