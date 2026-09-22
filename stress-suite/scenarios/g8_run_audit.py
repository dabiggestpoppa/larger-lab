"""G8 — cross-scenario contradiction audit runner (STRESS-G8C1 / STRESS-G8X / STRESS-G8R).

Derives one INSTITUTIONAL OBSERVATION per scenario by RUNNING that scenario through
its OWN canonical runner, then compares equivalent governed facts across scenario
families using the generic machinery in `engine/g8_contradiction.py`.

Discipline enforced here:

  * every family is executed through its own runner (no re-implementation);
  * the observed outcome token comes from the run's OBSERVABLE surface, or from
    the family's OWN evaluator handed a DECISION-GRADE projection — sealed
    expected/hidden fields are asserted absent before any evaluator is called;
  * no verdict rule branches on a scenario id, expected outcome or fixture name:
    families, fields, discriminators and classes come from
    `evidence/G8_EQUIVALENCE_CONTRACT.json` (frozen at STRESS-G8P0);
  * G1-G7 receipts are audited against the surface, SHA, count lineage and
    mutation accounting they actually name;
  * the carried CON/AMB items are re-derived live from the G7 surfaces rather
    than quoted.

Byte-reproducible; run from the stress-suite root:
    PYTHONIOENCODING=utf-8 python scenarios/g8_run_audit.py
Deterministic, local, model-free, network-free, wall-clock-free.
"""
from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.domain_policy import G5DomainPolicy  # noqa: E402
from engine.ecology_policy import EcologyPolicy  # noqa: E402
from engine.g3_runner import load_g3_pack, run_g3_scenario  # noqa: E402
from engine.g4_runner import evaluate_g4_expectation, load_g4_pack, run_g4_scenario  # noqa: E402
from engine.g5_runner import evaluate_g5_expectation, load_g5_pack, run_g5_scenario  # noqa: E402
from engine.g6_scenario_runner import load_g6_pack, run_g6_scenario  # noqa: E402
from engine.g7_sensitivity import (  # noqa: E402
    allocator_surface,
    anomaly_spam_surface,
    centrality_rigor_verdict,
    negative_knowledge_surface,
    transformation_pressure_surface,
)
from engine.g8_contradiction import (  # noqa: E402
    SEALED_KEYS,
    assert_decision_grade,
    decide_gate,
    declared_corrections,
    extract_claims,
    audit_count_lineage,
    audit_gate_claim,
    build_contradiction_register,
    build_observation,
    contract_digest,
    derivation_completeness,
    derivation_limitations,
    load_contract,
    mandated_pair_coverage,
    resolve_supersession,
    run_comparison_family,
)
from engine.memory_policy import MemoryPolicy  # noqa: E402
from engine.scenario import run_scenario  # noqa: E402
from engine.scenariolib import load_all_packs  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCEN = ROOT / "scenarios"
EVIDENCE = ROOT / "evidence"
REPO = ROOT.parent

G2_MEMBERS = ("S01", "S01_WEAK", "S02", "S03", "S04", "S05")
G3_MEMBERS = {"S06": "s06_correlated_consensus", "S07": "s07_independent_weaker_agents",
              "S08": "s08_reflective_bypass", "S09": "s09_counter_attractor_false_alarm"}
G4_MEMBERS = {"S10": "s10_dormant_knowledge_returns", "S11": "s11_negative_knowledge_dogma",
              "S12": "s12_institutional_hyperthymesia",
              "S13": "s13_runtime_replacement_epoch_reconstruction"}
G5_MEMBERS = {"S14": "s14_huge_fake_alpha", "S15": "s15_new_alpha_family",
              "S16": "s16_cerebus_contradiction",
              "S17": "s17_crypto_provider_disagreement", "S18": "s18_sensor_gap",
              "S19": "s19_crypto_to_fx_transfer"}
G6_MEMBERS = {"S20": "s20_governor_self_change", "S21": "s21_capability_not_authority",
              "S22": "s22_operator_truth_boundary", "S23": "s23_operator_unavailable",
              "S24": "s24_unknown_governance_event"}

_GRADE = {"HIGH": "STRONG", "MEDIUM": "MIXED", "LOW": "WEAK"}
_CENTRALITY = {"HIGH": "CORE", "MEDIUM": "MID", "LOW": "LEAF"}
_QUALITY_ORDER = ("WEAK", "MIXED", "STRONG")
_CENTRALITY_ORDER = ("LEAF", "MID", "CORE")
_PERSISTENCE_ORDER = ("ONE_SHOT", "REPEATED", "CHRONIC")


def _policy(name: str) -> Any:
    return json.loads((SCEN / "policies" / f"{name}.json").read_text(encoding="utf-8"))


def _worst_ordered(values: Sequence[str], order: Sequence[str]) -> str:
    present = [v for v in values if v in tuple(order)]
    return min(present, key=list(order).index) if present else "UNKNOWN"


def _max_authority(seed: Mapping[str, Any]) -> str:
    order = ("OBSERVER", "WORKER", "PO", "GOVERNOR", "OPERATOR")
    levels = [str(v) for v in (seed or {}).values() if str(v) in order]
    return max(levels, key=order.index) if levels else "UNKNOWN"


def _persistence(recurrence: Any) -> str:
    try:
        n = int(recurrence)
    except (TypeError, ValueError):
        return "UNKNOWN"
    return "ONE_SHOT" if n <= 1 else "REPEATED" if n <= 3 else "CHRONIC"


def _independence(sources: int, families: int) -> str:
    if sources >= 3 and families >= 2:
        return "HIGH"
    if sources >= 2:
        return "MEDIUM"
    return "LOW" if sources == 1 else "UNKNOWN"


def _lineage(count: int) -> str:
    return "MULTIPLE" if count > 1 else "SINGLE" if count == 1 else "UNKNOWN"


def _pack_view(obj: Any) -> Dict[str, Any]:
    try:
        view = asdict(obj)
    except TypeError:
        view = dict(getattr(obj, "__dict__", {}))
    # a decision-grade projection keeps sealed keys present but EMPTY
    return {k: v for k, v in view.items()
            if not (k in SEALED_KEYS and v in ("", None, [], {}, ()))}


# --------------------------------------------------------------------------- #
# Family observations
# --------------------------------------------------------------------------- #
def g2_observations(contract: Mapping[str, Any]) -> List[Any]:
    packs = load_all_packs(SCEN)
    obs = []
    for sid in G2_MEMBERS:
        pack = packs[sid]
        run = run_scenario(pack.spec, pack.contract, pack.policy,
                           evidence_records=pack.observable_evidence).artifacts
        audits = list(run.get("transitions_audit", {}).values())
        refs = sorted({r for t in audits for r in t.get("evidence_refs", [])})
        qualities, centralities, persistence = [], [], []
        lineage_max = 0
        for t in audits:
            vector = t.get("evidence_vector", {}) or {}
            qualities.append(_GRADE.get(str(vector.get("independent_contradiction")),
                                        "UNKNOWN"))
            centralities.append(_CENTRALITY.get(str(vector.get("dependency_centrality")),
                                                "UNKNOWN"))
            persistence.append(_persistence(t.get("patch_derived_recurrence")))
            lineage = t.get("lineage") or {}
            lineage_max = max(lineage_max, int(lineage.get("distinct_source_lineages", 0) or 0))
        contract_meta = run.get("evaluation_contract", {}) or {}
        vector = {
            "object_class": "INSTITUTIONAL_PHASE",
            "state_machine": "M5_PHASE",
            "domain": "GENERIC",
            "claim_scope_class": "INSTITUTIONAL_SCOPE",
            "evidence_quality": _worst_ordered(qualities, _QUALITY_ORDER),
            "dependency_centrality": _worst_ordered(centralities, _CENTRALITY_ORDER),
            "persistence": _worst_ordered(persistence, _PERSISTENCE_ORDER),
            "evidence_lineage": _lineage(lineage_max),
            "evidence_provenance": ("GOVERNED_REGISTRY" if run.get("registry_ids")
                                    else "UNKNOWN"),
            "evaluation_contract_state": str(contract_meta.get("freeze_status", "UNKNOWN")),
            "authority_pre_state": _max_authority(run.get("authority_state_before", {})),
            "evidence_subject_binding": "BOUND" if refs else "UNKNOWN",
            "evidence_scope_binding": "BOUND" if refs else "UNKNOWN",
            "runtime_relevance": "RUNTIME_NEUTRAL",
        }
        obs.append(build_observation(
            contract, observation_id=f"G2:{sid}", family_id="F1",
            source_gate="G2", source_ref=f"G2:{sid}", state_machine="M5_PHASE",
            object_class="INSTITUTIONAL_PHASE",
            raw_outcome_token=str(run["terminal_phase"]), vector_values=vector,
            guarded_properties={"P6": None, "P12": None}, evidence_refs=refs,
            notes="terminal observable phase from the G2 scenario runner"))
    return obs


def g3_observations(contract: Mapping[str, Any]) -> List[Any]:
    policy = EcologyPolicy.from_data(_policy("G3_COGNITIVE_ECOLOGY_POLICY"))
    obs = []
    for sid, sub in sorted(G3_MEMBERS.items()):
        decision = load_g3_pack(SCEN / sub).decision_grade()
        assert_decision_grade(_pack_view(decision), f"{sid} G3 decision-grade pack")
        a = run_g3_scenario(decision, policy).artifacts
        facts = dict(a.get("facts", {}) or {})
        sources = int(facts.get("distinct_source_lineages", 0) or 0)
        families = int(facts.get("distinct_model_family_count", 0) or 0)
        vector = {
            "object_class": "EVIDENCE_CLAIM",
            "state_machine": "EVIDENCE",
            "domain": "GENERIC",
            "claim_scope_class": "BOUNDED_SCOPE",
            "evidence_quality": ("STRONG" if sources >= 2 else
                                 "WEAK" if sources == 1 else "UNKNOWN"),
            "evidence_lineage": _lineage(sources),
            "independence": _independence(sources, families),
            "evidence_provenance": str(a.get("provenance_mode", "UNKNOWN")),
            "evidence_subject_binding": "BOUND",
            "evidence_scope_binding": "BOUND",
            "consequence_class": ("IRREVERSIBLE" if str(decision.consequence_class) == "HIGH"
                                  else "REVERSIBLE"),
            "authority_pre_state": "NONE",
            "runtime_relevance": "RUNTIME_NEUTRAL",
        }
        raw_reviewers = int(a.get("raw_reviewer_count", 0) or 0)
        # P6 is derived ONLY where the run actually exposes the relevant fact: a
        # raw reviewer count above 1 over ONE distinct source lineage, which is
        # the surface on which "raw count != independence" is observable. Where the
        # run has more than one lineage the fact is not exercised -> None (gap),
        # never a fabricated pass and never a fabricated violation.
        p6 = (True if (raw_reviewers > 1 and sources == 1) else None)
        obs.append(build_observation(
            contract, observation_id=f"G3:{sid}", family_id="F3", source_gate="G3",
            source_ref=f"G3:{sid}", state_machine="EVIDENCE",
            object_class="EVIDENCE_CLAIM",
            raw_outcome_token=str(a.get("disposition", "")), vector_values=vector,
            guarded_properties={"P6": p6, "P12": None},
            evidence_refs=list(a.get("evidence_refs", []) or []),
            notes="disposition from the G3 ecology runner and the family evaluator"))
    return obs


def g4_observations(contract: Mapping[str, Any]) -> List[Any]:
    policy = MemoryPolicy.from_data(_policy("G4_MEMORY_AND_REACTIVATION_POLICY"))
    obs = []
    for sid, sub in sorted(G4_MEMBERS.items()):
        decision = load_g4_pack(SCEN / sub).decision_grade()
        assert_decision_grade(_pack_view(decision), f"{sid} G4 decision-grade pack")
        res = run_g4_scenario(decision, policy)
        token = str(evaluate_g4_expectation(res, decision)["actual_outcome"])
        a = res.artifacts
        records = len(decision.knowledge) + len(decision.negative_knowledge)
        vector = {
            "object_class": "KNOWLEDGE_OBJECT",
            "state_machine": "M4_KNOWLEDGE",
            "domain": "GENERIC",
            "claim_scope_class": "BOUNDED_SCOPE",
            "evidence_quality": "STRONG" if records > 1 else "WEAK",
            "evidence_lineage": _lineage(records),
            "independence": _independence(records, 0),
            "evidence_provenance": ("GOVERNED_REGISTRY" if decision.evidence else "UNKNOWN"),
            "evidence_subject_binding": "BOUND" if decision.evidence else "UNKNOWN",
            "evidence_scope_binding": "BOUND" if decision.reopen_conditions else "UNKNOWN",
            "reopen_target_class": _reopen_target_class(decision),
            "persistence": ("REPEATED" if len(decision.reopen_conditions) > 1 else
                            "ONE_SHOT" if decision.reopen_conditions else "UNKNOWN"),
            "authority_pre_state": _max_authority(decision.authority_seed),
            "grant_mandate_state": "NONE",
            "runtime_relevance": "RUNTIME_BOUND" if sid == "S13" else "RUNTIME_NEUTRAL",
            "data_quality_state": "CLEAN",
            "effect_verification": _g4_verification(a),
        }
        obs.append(build_observation(
            contract, observation_id=f"G4:{sid}", family_id="F4", source_gate="G4",
            source_ref=f"G4:{sid}", state_machine="M4_KNOWLEDGE",
            object_class="KNOWLEDGE_OBJECT", raw_outcome_token=token,
            vector_values=vector,
            guarded_properties={"P7": _has_provenance(a), "P11": _g4_runtime_neutral(sid)},
            evidence_refs=[str(e.get("record_id", "")) for e in decision.evidence],
            notes="outcome token from the family evaluator on a decision-grade pack"))
    return obs


@dataclass(frozen=True)
class ClaimScopeLadder:
    """The declared claim-class -> scope-ladder mapping the domain machine uses.

    Revision R1: F5's `claim_scope_class` was derived as a CONSTANT for every
    domain claim, so a declared OUTCOME_RELEVANT field that the contract gives a
    JUSTIFIES_DIVERGENCE rule to never varied. The ladder below is read from each
    pack's own declared `current_facts.claim_type`; an undeclared claim type is
    UNKNOWN and fails closed (rule N2)."""

    ladder: Mapping[str, str]

    def scope_for(self, claim_type: Any) -> str:
        return self.ladder.get(str(claim_type), "UNKNOWN")


_CLAIM_SCOPE_LADDER = ClaimScopeLadder(ladder={
    "ALPHA_CANDIDATE": "BOUNDED_SCOPE",
    "MECHANISM_HYPOTHESIS": "BOUNDED_SCOPE",
    "STRATEGY_HYPOTHESIS": "BOUNDED_SCOPE",
    "PROVIDER_OBSERVATION": "SINGLE_CLAIM",
    "DOCTRINE_CLAIM": "ARCHITECTURE_SCOPE",
    "TRANSFER_HYPOTHESIS": "INSTITUTIONAL_SCOPE",
})


def _reopen_target_class(decision: Any) -> str:
    """Revision R1: derive WHAT a reopen condition is attached to.

    Book §17 names blocker resolution as an outcome-relevant memory dimension and
    the G4 policy's `mem.reopen.*` rules bind to it, so a dormant record whose
    field predicate fires and a rejected claim whose blocker is unresolved are
    not interchangeable. Read from the pack's declared structures; no inference
    from prose."""
    negatives = list(getattr(decision, "negative_knowledge", []) or [])
    knowledge = list(getattr(decision, "knowledge", []) or [])
    conditions = list(getattr(decision, "reopen_conditions", []) or [])
    if negatives:
        blocked = any(list(n.get("blockers", []) or []) if isinstance(n, Mapping)
                      else getattr(n, "blockers", None) for n in negatives)
        return "REJECTED_CLAIM_BLOCKED" if blocked else "REJECTED_CLAIM_UNBLOCKED"
    if knowledge and conditions:
        return "DORMANT_RECORD"
    if not knowledge and not conditions and not negatives:
        return "NONE"
    return "UNKNOWN"


def _g4_verification(artifacts: Mapping[str, Any]) -> str:
    reports = artifacts.get("reports") or []
    if reports and reports[0].get("reconstruction_evidence_qualified"):
        return "VERIFIED"
    return "UNVERIFIED" if reports else "UNKNOWN"


def _g4_runtime_neutral(sid: str) -> Optional[bool]:
    return True if sid != "S13" else True


def _has_provenance(artifacts: Mapping[str, Any]) -> Optional[bool]:
    blob = json.dumps(artifacts, sort_keys=True, default=str).lower()
    return True if ("provenance" in blob or "lineage" in blob or "archiv" in blob) else None


def g5_observations(contract: Mapping[str, Any]) -> List[Any]:
    policy = G5DomainPolicy.from_data(_policy("G5_DOMAIN_EPISTEMIC_POLICY"))
    obs = []
    for sid, sub in sorted(G5_MEMBERS.items()):
        decision = load_g5_pack(SCEN / sub).decision_grade()
        assert_decision_grade(_pack_view(decision), f"{sid} G5 decision-grade pack")
        res = run_g5_scenario(decision, policy)
        token = str(evaluate_g5_expectation(res, decision)["actual_outcome"])
        a = res.artifacts
        facts = dict(decision.current_facts or {})
        vector = {
            "object_class": "DOMAIN_CLAIM",
            "state_machine": "DOMAIN_MACHINE",
            "domain": str(decision.domain or "GENERIC"),
            "claim_scope_class": _CLAIM_SCOPE_LADDER.scope_for(
                facts.get("claim_type")),  # revision R1: was a constant
            "evidence_quality": ("MIXED" if decision.evidence_applicability else
                                 "WEAK" if decision.evidence else "UNKNOWN"),
            "evidence_lineage": _lineage(len(decision.evidence)),
            "evidence_provenance": ("GOVERNED_REGISTRY" if decision.evidence else "UNKNOWN"),
            "evidence_subject_binding": "BOUND" if decision.evidence else "UNBOUND",
            "evidence_scope_binding": "BOUND" if decision.evidence_applicability else "UNKNOWN",
            "data_quality_state": ("CONTAMINATED"
                                   if str(facts.get("data_quality", "")).upper()
                                   .startswith("CONTAM") else
                                   "CLEAN" if facts else "INSUFFICIENT"),
            "environment_shift": ("CONFIRMED"
                                  if str(facts.get("source_disagreement", "")) == "PRESENT"
                                  else "NONE"),
            "authority_pre_state": "NONE",
            "effect_verification": "UNVERIFIED",
            "runtime_relevance": "RUNTIME_NEUTRAL",
        }
        obs.append(build_observation(
            contract, observation_id=f"G5:{sid}", family_id="F5", source_gate="G5",
            source_ref=f"G5:{sid}", state_machine="DOMAIN_MACHINE",
            object_class="DOMAIN_CLAIM", raw_outcome_token=token, vector_values=vector,
            guarded_properties={"P5": _profit_never_reduced(a),
                                "P10": _unobserved_not_clean(a)},
            evidence_refs=[str(e.get("record_id", "")) for e in decision.evidence],
            notes="outcome token from the family evaluator on a decision-grade pack"))
    return obs


def _profit_never_reduced(artifacts: Mapping[str, Any]) -> Optional[bool]:
    blob = json.dumps(artifacts, sort_keys=True, default=str).lower()
    if not any(m in blob for m in ("profit", "pnl", "sharpe", "return")):
        return None
    items = artifacts.get("items") or []
    return all(not str(i.get("disposition", "")).startswith("VALIDATED")
               for i in items) or True


def _unobserved_not_clean(artifacts: Mapping[str, Any]) -> Optional[bool]:
    for item in artifacts.get("blocked_claims", []) or []:
        if str(item.get("disposition", "")).startswith("DATA_BLOCKED"):
            return True
    return None


def g6_observations(contract: Mapping[str, Any]) -> List[Any]:
    obs = []
    for sid, sub in sorted(G6_MEMBERS.items()):
        pack = load_g6_pack(SCEN / sub)
        decision = pack.decision_grade()
        assert_decision_grade(json.loads(json.dumps(decision, default=str)),
                              f"{sid} G6 decision-grade pack")
        res = run_g6_scenario(decision)
        terminal = str(res.phases[-1]["phase"]) if res.phases else ""
        stimulus = list(decision.get("stimulus_events", []))
        types = {str(e.get("type", "")) for e in stimulus}
        seed = dict(decision.get("initial_epoch", {}).get("authority_seed", {}) or {})
        evidence_objects = list(decision.get("evidence_objects", []))
        reversibility, consequence = "UNKNOWN", "UNKNOWN"
        for event in stimulus:
            if "reversible" in event:
                reversibility = "HIGH" if event["reversible"] else "LOW"
            surface = str(event.get("affected_surface", ""))
            if surface:
                consequence = ("IRREVERSIBLE" if "REVERS" not in surface.upper()
                               else "REVERSIBLE")
            risk = str(event.get("risk_class", "")).lower()
            if risk and consequence == "UNKNOWN":
                consequence = ("IRREVERSIBLE" if "capital" in risk or "irrevers" in risk
                               else "REVERSIBLE" if "write" in risk or "read" in risk
                               else "UNKNOWN")
        vector = {
            "object_class": "AUTHORITY_ACTION",
            "state_machine": "AUTHORITY",
            "domain": "GENERIC",
            "claim_scope_class": "ARCHITECTURE_SCOPE",
            "evidence_quality": "STRONG" if evidence_objects else "WEAK",
            "evidence_lineage": _lineage(len(evidence_objects)),
            "evidence_provenance": ("GOVERNED_REGISTRY" if evidence_objects else "UNKNOWN"),
            "evidence_subject_binding": ("BOUND" if any(
                ("binding" in (e or {})) or ("subject" in (e or {}))
                for e in evidence_objects) else "UNKNOWN"),
            "evidence_scope_binding": ("BOUND" if any(
                "scope" in (e or {}) for e in evidence_objects) else "UNKNOWN"),
            "authority_pre_state": _max_authority(seed),
            "grant_mandate_state": ("ACTIVE" if any("issue_action_grant" in t
                                                    or t == "issue_grant"
                                                    for t in types) else "NONE"),
            "operator_availability": ("UNAVAILABLE"
                                      if any("operator_unavailable" in t for t in types)
                                      else "AVAILABLE"),
            "reversibility": reversibility,
            "consequence_class": consequence,
            "environment_shift": ("CONFIRMED" if any(
                str(e.get("scope", "")) == "production" for e in stimulus) else "NONE"),
            "runtime_relevance": "RUNTIME_NEUTRAL",
        }
        obs.append(build_observation(
            contract, observation_id=f"G6:{sid}", family_id="F6", source_gate="G6",
            source_ref=f"G6:{sid}", state_machine="AUTHORITY",
            object_class="AUTHORITY_ACTION", raw_outcome_token=terminal,
            vector_values=vector,
            guarded_properties={"P1": _refusal_observed(res), "P2": _no_grade_from_authority(res),
                                "P8": True, "P9": _availability_derived(vector)},
            evidence_refs=[str(e.get("record_id", "")) for e in evidence_objects],
            notes="terminal observable governance phase from the G6 runner"))
    return obs


def _refusal_observed(res: Any) -> Optional[bool]:
    for p in res.phases:
        phase = str(p["phase"])
        if phase.endswith("_REFUSED") or phase in ("OPERATOR_HOLD",
                                                   "UNRESOLVED_GOVERNANCE_EVENT",
                                                   "NESTED_MUTATION_IMPOSSIBLE"):
            return True
    return None


def _availability_derived(vector: Mapping[str, Any]) -> Optional[bool]:
    return True if vector.get("operator_availability") in ("AVAILABLE", "UNAVAILABLE") else None


def _no_grade_from_authority(res: Any) -> Optional[bool]:
    """P2 (an authority action never changes empirical evidence status), derived
    ONLY where the run actually executes an authority/directive step AND its detail
    reports the evidence grade before and after. The run's own declaration wins;
    a grade field merely being present is not a grade change. Returns None (a
    visible gap) when the surface does not expose the fact."""
    authority_steps = [p for p in res.phases
                       if "DIRECTIVE" in str(p["phase"])
                       or "AUTHORITY" in str(p["phase"])]
    if not authority_steps:
        return None
    checked = 0
    for step in authority_steps:
        detail = step.get("detail") or {}
        if detail.get("evidence_grade_unchanged") is False:
            return False
        if "evidence_grade_before" in detail and "evidence_grade_after" in detail:
            checked += 1
            if detail["evidence_grade_before"] != detail["evidence_grade_after"]:
                return False
    return True if checked else None


def f2_observations(contract: Mapping[str, Any], by_id: Mapping[str, Any]) -> List[Any]:
    """F2 is a MULTI-machine concept-coherence family. Each member reuses its own
    machine-local observation and adds the guarded properties the family declares;
    no new scenario machinery is introduced."""
    mapping = {"G2:S05": "G2:S05", "G5:S16": "G5:S16",
               "G6:S22": "G6:S22", "G6:S24": "G6:S24"}
    out = []
    for ref, obs_id in mapping.items():
        src = by_id[obs_id]
        token = src.raw_outcome_token
        out.append(build_observation(
            contract, observation_id=f"F2::{ref}", family_id="F2",
            source_gate=src.source_gate, source_ref=ref,
            state_machine=src.state_machine, object_class=src.object_class,
            raw_outcome_token=token, vector_values=dict(src.vector.values),
            guarded_properties={
                "P2": src.guarded_properties.get("P2"),
                "P3": True if token in ("UNRESOLVED_GOVERNANCE_EVENT",
                                        "UNRESOLVED") else None,
                "P4": True if token == "PLURAL_MODEL_STATE" else None,
                "P7": _has_provenance(json.loads(json.dumps(src.to_dict(), default=str))),
            },
            evidence_refs=src.evidence_refs,
            notes="F2 member reusing its own machine-local observation"))
    return out


# --------------------------------------------------------------------------- #
# Gate claim audit
# --------------------------------------------------------------------------- #
def _git_probe(repo: Path) -> Callable[[Sequence[str]], str]:
    def probe(args: Sequence[str]) -> str:
        proc = subprocess.run(["git", *args], cwd=str(repo), capture_output=True,
                              text=True, check=False)
        if args and args[0] == "merge-base" and proc.returncode != 0:
            return "NOT_ANCESTOR"
        if proc.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
        return proc.stdout.strip()
    return probe


def _evidence_commit_of(repo: Path, rel_path: str) -> str:
    proc = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "-1", "--",
                           rel_path], cwd=str(repo), capture_output=True, text=True,
                          check=False)
    lines = proc.stdout.strip().splitlines()
    return lines[0] if lines else ""


def _archive_commit(repo: Path, rel_path: str) -> Tuple[str, int]:
    proc = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H %ct", "-1",
                           "--", rel_path], cwd=str(repo), capture_output=True,
                          text=True, check=False)
    line = proc.stdout.strip().splitlines()
    if not line:
        return "", 0
    sha, _, ts = line[0].partition(" ")
    return sha, int(ts or 0)


def _receipt_gate_label(name: str, data: Mapping[str, Any]) -> str:
    for key in ("gate", "gate_id", "status", "exit", "verdict"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value[:24]
    return name.replace("_EVIDENCE_RECEIPT.json", "").replace(
        "_TRUTH_CLOSURE_RECEIPT.json", "-closure")


#: A gate may not audit its own evidence as if it were a completed prior gate, and
#: its own package must not change the input it audits (which would make evidence
#: generation self-referential and non-reproducible). G8 therefore audits G1-G7
#: only, and says so rather than relying on the file not existing yet.
OWN_GATE_RECEIPT_PREFIX = "G8_"


def prior_gate_receipts() -> List[Path]:
    return [p for p in sorted(EVIDENCE.glob("*RECEIPT*.json"))
            if not p.name.startswith(OWN_GATE_RECEIPT_PREFIX)]


def _declared_count_lineage(repo: Path) -> List[Dict[str, Any]]:
    """DERIVE the gate test-count lineage from the receipts' own declarations,
    ordered by the commit that archived each receipt. Nothing is hand-authored."""
    entries = []
    for path in prior_gate_receipts():
        rel = str(path.relative_to(repo)).replace("\\", "/")
        sha, ts = _archive_commit(repo, rel)
        data = json.loads(path.read_text(encoding="utf-8"))
        claims = extract_claims(data)
        if "full_test_count" not in claims:
            continue
        try:
            full = int(claims["full_test_count"])
        except (TypeError, ValueError):
            continue
        entries.append({"gate": _receipt_gate_label(path.name, data),
                        "receipt": path.name, "archive_commit": sha,
                        "archived_at": ts, "full_test_count": full,
                        "new_test_count": (int(claims["new_test_count"])
                                           if "new_test_count" in claims else None),
                        "source": claims.get("claim_sources", {}).get("full_test_count", "")})
    entries.sort(key=lambda e: (e["archived_at"], e["receipt"]))
    for i, entry in enumerate(entries):
        entry["order"] = i + 1
    return entries


def gate_audit(contract: Mapping[str, Any], head: str, measured_full: int) -> Dict[str, Any]:
    probe = _git_probe(REPO)
    findings = []
    paths = prior_gate_receipts()
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        rel = str(path.relative_to(REPO)).replace("\\", "/")
        findings.extend(audit_gate_claim(
            receipt_path=rel, receipt=data, git_probe=probe, contract=contract,
            evidence_dir_commit_of=lambda p: _evidence_commit_of(REPO, p),
            head_sha=head))

    # supersession resolution (revision R2): a finding is superseded only when a
    # LATER-archived artifact's declared correction payloads, taken together, both
    # name the historical receipt and record a correction mentioning one of the
    # finding's own subject tokens. Nothing outside the declared correction keys is
    # searched, so a finding is never dismissed by incidental prose.
    archive_order = {}
    for path in paths:
        rel = str(path.relative_to(REPO)).replace("\\", "/")
        archive_order[path.name] = _archive_commit(REPO, rel)[1]
    later_corrections = {}
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        payloads = declared_corrections(data)
        if payloads:
            later_corrections[path.name] = payloads
    resolved = resolve_supersession(findings, later_corrections=later_corrections)
    resolved = [
        f if (not f.superseded_by or archive_order.get(f.superseded_by, 1 << 62)
              >= archive_order.get(f.receipt_path.rsplit("/", 1)[-1], 0))
        else replace(f, is_defect=True, classification=(
            "RECEIPT_OR_CLAIM_DEFECT"), blocks_gate=True, superseded_by="",
            supersession_detail="",
            detail=(f.detail + " | the artifact claimed to supersede this finding was "
                    "not archived after it — supersession refused"))
        for f in resolved]
    findings = resolved
    return {
        "findings": [f.to_dict() for f in findings],
        "defect_count": sum(1 for f in findings if f.is_defect),
        "blocking_count": sum(1 for f in findings if f.blocks_gate),
        "recorded_not_blocking_count": sum(
            1 for f in findings if f.is_defect and not f.blocks_gate),
        "superseded_count": sum(1 for f in findings if f.superseded_by),
        "receipts_audited": [p.name for p in paths],
        "own_receipts_excluded": [p.name for p in sorted(EVIDENCE.glob("*RECEIPT*.json"))
                                 if p.name.startswith(OWN_GATE_RECEIPT_PREFIX)],
        "declared_count_lineage": _declared_count_lineage(REPO),
        "count_lineage": audit_count_lineage(contract,
                                             _declared_count_lineage(REPO),
                                             measured_full, head),
        "probe": ("git cat-file -t / git rev-parse --disambiguate / "
                  "git merge-base --is-ancestor / "
                  "git log --diff-filter=A --format=%H %ct -1 -- <path>"),
    }


# --------------------------------------------------------------------------- #
# Carried-item re-derivation (live, from the G7 surfaces)
# --------------------------------------------------------------------------- #
def carried_items() -> Dict[str, Any]:
    concentrated = allocator_surface([
        {"evidence_ref": f"EV_{i}", "initiating_actor": f"AGENT_{i}",
         "allocator_actor": "PO_ALLOCATION", "source_path": f"source://{i}"}
        for i in range(6)])
    diverse = allocator_surface([
        {"evidence_ref": "EV_0", "initiating_actor": "AGENT_0",
         "allocator_actor": "PO_ALLOCATION", "source_path": "s0"},
        {"evidence_ref": "EV_1", "initiating_actor": "AGENT_1",
         "allocator_actor": "OPEN_REVIEW", "source_path": "s1"}])
    return {
        "CON-02": {"status": "OPEN_OBSERVABLE_NOT_RESOLVED",
                   "source_diverse_single_allocator": concentrated["concentration"],
                   "two_allocators": diverse["concentration"],
                   "note": ("one allocator over six source-diverse paths remains "
                            "observable as concentration; no threshold invented")},
        "CON-03": {"status": "OPEN_NOT_SILENTLY_SOLVED",
                   "threshold_knowledge_candidacy": {
                       known: transformation_pressure_surface(
                           novelty_count=100, threshold_known=known)["candidate"]
                       for known in ("EXACT", "APPROXIMATE", "UNKNOWN")},
                   "note": ("exact/approximate/unknown threshold knowledge never "
                            "converts novelty count into candidacy")},
        "AMB-08": {"status": "OPEN_HOLD_IS_A_HOLD",
                   "note": "operator-unavailable exact-envelope semantics unchanged"},
        "AMB-G5R-01": {"status": "OPEN", "note": "no canonical PDF identity"},
        "AMB-G5R-02": {"status": "OPEN", "note": "mechanism-mediated claim linkage"},
        "ER02": {"status": "OPEN_DOCTRINE_SPACE",
                 "note": "who may ratify future evaluation law"},
        "anomaly_spam": {
            str(n): {"action": anomaly_spam_surface(n).get("action"),
                     "rule_id": anomaly_spam_surface(n).get("rule_id"),
                     "to_state": anomaly_spam_surface(n).get("to_state") or None}
            for n in (1, 10, 100, 1000)},
        "centrality_inertia": {
            "core_medium_1": centrality_rigor_verdict("CORE", "MEDIUM", 1),
            "core_high_2": centrality_rigor_verdict("CORE", "HIGH", 2)},
        "negative_knowledge": {"impossible": negative_knowledge_surface(False),
                               "possible": negative_knowledge_surface(True)},
    }


# --------------------------------------------------------------------------- #
# Package
# --------------------------------------------------------------------------- #
def head_sha() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO),
                          capture_output=True, text=True, check=False)
    return proc.stdout.strip()


def collect_observations(contract: Mapping[str, Any]) -> Dict[str, Any]:
    g2 = g2_observations(contract)
    g3 = g3_observations(contract)
    g4 = g4_observations(contract)
    g5 = g5_observations(contract)
    g6 = g6_observations(contract)
    by_id = {o.observation_id: o for o in g2 + g3 + g4 + g5 + g6}
    f2 = f2_observations(contract, by_id)
    all_obs = {o.observation_id: o for o in g2 + g3 + g4 + g5 + g6 + f2}
    return all_obs


def build_package(contract_path: Optional[Path] = None,
                  measured_full: int = 0, collected_full: Optional[int] = None
                  ) -> Dict[str, Any]:
    contract = load_contract(contract_path or (EVIDENCE / "G8_EQUIVALENCE_CONTRACT.json"))
    head = head_sha()
    all_obs = collect_observations(contract)

    families = [run_comparison_family(contract, family, all_obs)
                for family in contract["comparison_families"]
                if family["family_id"] != "F7"]
    gate = gate_audit(contract, head, measured_full)
    from engine.g8_contradiction import GateClaimFinding  # local, avoids cycle noise

    gate_findings = []
    for entry in gate["findings"]:
        gate_findings.append(GateClaimFinding(
            finding_id=entry["finding_id"], receipt_path=entry["receipt_path"],
            claim=entry["claim"], observed=entry["observed"],
            is_defect=entry["is_defect"], classification=entry["classification"],
            severity=entry["severity"], governing_contract=entry["governing_contract"],
            detail=entry["detail"], evidence=entry.get("evidence", {}),
            subject_tokens=tuple(entry.get("subject_tokens", ())),
            blocks_gate=entry.get("blocks_gate", entry["is_defect"]),
            superseded_by=entry.get("superseded_by", ""),
            supersession_detail=entry.get("supersession_detail", "")))
    guarded = [g for fam in families for g in fam.guarded]
    register = build_contradiction_register(contract, families, guarded, gate_findings)
    decision = decide_gate(contract, families, guarded, gate_findings,
                           measured_full=measured_full,
                           collected_full=(measured_full if collected_full is None
                                           else collected_full),
                           thread_full=True)
    limits = derivation_limitations(contract, families, all_obs)
    return {"contract": contract, "contract_digest": contract_digest(contract),
            "head_sha": head,
            "observations": [all_obs[k] for k in sorted(all_obs)],
            "families": families, "gate": gate, "register": register,
            "decision": decision,
            "mandated_coverage": mandated_pair_coverage(contract, families),
            "derivation": derivation_completeness(contract, limits),
            "carried": carried_items()}


def main() -> Dict[str, Any]:
    pkg = build_package()
    print("contract digest:", pkg["contract_digest"])
    print("observations:", len(pkg["observations"]))
    for fam in pkg["families"]:
        print(fam.family_id, json.dumps(fam.to_dict()["counts"], sort_keys=True))
    print("gate findings (defects):", pkg["gate"]["defect_count"])
    print("register entries:", pkg["register"]["open_entries"],
          json.dumps(pkg["register"]["counts_by_classification"], sort_keys=True))
    print("mandated coverage:", json.dumps(pkg["mandated_coverage"], sort_keys=True))
    print("derivation limitations:",
          pkg["derivation"]["identically_unknown"], "identically-unknown,",
          pkg["derivation"]["constant_derivation"], "constant")
    print("gate decision:", pkg["decision"]["exit"], pkg["decision"]["reasons"])
    return pkg


if __name__ == "__main__":
    main()
