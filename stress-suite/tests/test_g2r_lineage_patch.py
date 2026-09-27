"""G2R §5 / G2R-03 — non-scalar independence lineage + DERIVED patch recurrence.

§5  independent_contradiction = HIGH must be supported by MULTIPLE DISTINCT
    lineages; collapsing two lineages into one must change the high-independence
    gate behavior even with identical channel grades. No effective-sample-size
    score is produced (AMB-03 remains open).

    NOTE on S01: the committed S01 pack drives its TRANSFORMATION_CANDIDATE
    through the DERIVED patch-pressure gate (core.structural.patch) — a
    signature-recurrence topology that intentionally does NOT claim independent
    confirmation. The §5 metamorphic test therefore isolates the high-independence
    gate on a fixture (real G2_CORE_PHASE_POLICY + real S01 evaluation contract)
    whose ONLY transform path is the lineage-gated contradiction rule; a separate
    assertion proves S01's patch gate stays lineage-independent.

G2R-03  patch recurrence is DERIVED from the ordered exact-signature event
    history. A stimulus that lies about recurrence is overridden; unrelated
    signatures never aggregate. Miniature scenarios here carry an enter.watch +
    escalation ladder because STABLE -> TRANSFORMATION_CANDIDATE is not an M5
    edge — the escalation path is topology, not scenario logic.
"""
import pytest

from pathlib import Path

from engine.registry import EvidenceRegistry
from engine.scenariolib import load_all_packs
from engine.scenario import run_scenario
from engine.adjudicate import AdjudicatorPolicy
from engine.evalcontract import PhaseEvaluationContract
from engine.fixtures import StressScenarioSpec

SCENARIOS_ROOT = Path(__file__).resolve().parent.parent / "scenarios"
PACKS = load_all_packs(SCENARIOS_ROOT)


# --------------------------------------------------------------------------- #
# §5 lineage metamorphic (real core policy + real S01 contract)
# --------------------------------------------------------------------------- #
def _lineage_events():
    return [
        {"seq": 1, "evidence_vector": {"independent_contradiction": "HIGH",
                                       "reliability_degradation": "MEDIUM",
                                       "dependency_centrality": "HIGH"},
         "evidence_refs": ["C1"]},
        {"seq": 2, "evidence_vector": {"independent_contradiction": "HIGH",
                                       "reliability_degradation": "MEDIUM",
                                       "dependency_centrality": "HIGH"},
         "evidence_refs": ["C2"]},
        {"seq": 3, "evidence_vector": {"independent_contradiction": "HIGH",
                                       "reliability_degradation": "MEDIUM",
                                       "dependency_centrality": "HIGH"},
         "evidence_refs": ["C1", "C2"]},
    ]


LINEAGE_RECORDS = [
    {"record_id": "C1", "kind": "INDEPENDENT_CONFIRMATION", "claim": "c1",
     "lineage": "LINEAGE_A"},
    {"record_id": "C2", "kind": "INDEPENDENT_CONFIRMATION", "claim": "c2",
     "lineage": "LINEAGE_B"},
]


def test_collapse_lineages_kills_independent_confirmation():
    """Identical channel grades everywhere; ONLY the evidence lineages collapse.
    The lineage-gated contradiction rule must stop believing independent
    confirmation: two distinct lineages reach TRANSFORMATION_CANDIDATE, a single
    lineage stalls the review at ESCALATION_REVIEW."""
    pack = PACKS["S01"]
    spec = StressScenarioSpec(scenario_id="lineage-meta", stimulus_events=_lineage_events(),
                              initial_authority_state={"GOVERNOR": "GOVERNOR"})
    base = run_scenario(spec, pack.contract, pack.policy, evidence_records=LINEAGE_RECORDS)
    assert base.artifacts["actual_phase_trace"] == \
        ["STABLE", "WATCH", "ESCALATION_REVIEW", "TRANSFORMATION_CANDIDATE"]

    collapsed = [dict(r, lineage="LINEAGE_A") for r in LINEAGE_RECORDS]
    res = run_scenario(spec, pack.contract, pack.policy, evidence_records=collapsed)
    assert "TRANSFORMATION_CANDIDATE" not in res.artifacts["actual_phase_trace"]
    assert "TRANSFORMATION_WINDOW" not in res.artifacts["actual_phase_trace"]
    assert res.artifacts["terminal_phase"] == "ESCALATION_REVIEW"


def test_s01_patch_pressure_is_not_an_independent_confirmation_claim():
    """S01's TRANSFORMATION_CANDIDATE fires through the DERIVED patch-pressure
    gate (core.structural.patch), which intentionally does NOT claim independent
    confirmation. Collapsing lineages must therefore NOT silence that gate; the
    audit documents the one-lineage support alongside the patch rule."""
    pack = PACKS["S01"]
    collapsed = [dict(r, lineage="LINEAGE_A") for r in pack.observable_evidence]
    res = run_scenario(pack.spec, pack.contract, pack.policy, evidence_records=collapsed)
    audit = res.artifacts["transitions_audit"]
    fired = [s for s, a in audit.items() if a["applied"] and a["to"] == "TRANSFORMATION_CANDIDATE"]
    assert fired, "S01 must still reach TRANSFORMATION_CANDIDATE via patch pressure"
    assert audit[fired[0]]["rule_id"] == "core.structural.patch"
    assert audit[fired[0]]["lineage"]["distinct_source_lineages"] == 1


def test_registry_lineage_summary_distinguishes_one_vs_many():
    reg = EvidenceRegistry.from_records([
        {"record_id": "A1", "kind": "INDEPENDENT_CONFIRMATION", "claim": "a", "lineage": "LINEAGE_A"},
        {"record_id": "A2", "kind": "INDEPENDENT_CONFIRMATION", "claim": "a2", "lineage": "LINEAGE_A"},
        {"record_id": "B1", "kind": "INDEPENDENT_CONFIRMATION", "claim": "b", "lineage": "LINEAGE_B"},
    ])
    one = reg.lineage_summary(["A1", "A2"])
    assert one.raw_evidence_count == 2
    assert one.distinct_source_lineages == 1       # ONE LINEAGE
    assert one.distinct_model_lineages == 1
    two = reg.lineage_summary(["A1", "B1"])
    assert two.raw_evidence_count == 2
    assert two.distinct_source_lineages == 2       # MULTIPLE DISTINCT
    # no authoritative effective-sample-size score exists (AMB-03 open)
    assert not hasattr(two, "effective_sample_size")


def test_registry_lineage_ignores_claim_when_evidence_disagrees():
    """An IndependenceRecord may CLAIM 2 distinct source lineages, but the
    registry derives support from the actual evidence objects' lineages: 1."""
    reg = EvidenceRegistry.from_records([
        {"record_id": "IND", "kind": "INDEPENDENCE", "distinct_source_lineages": 2,
         "raw_reviewers": 10},
        {"record_id": "R1", "kind": "INDEPENDENT_CONFIRMATION", "claim": "r1", "lineage": "SAME"},
        {"record_id": "R2", "kind": "INDEPENDENT_CONFIRMATION", "claim": "r2", "lineage": "SAME"},
    ])
    summary = reg.lineage_summary(["R1", "R2"])
    assert summary.raw_evidence_count == 2
    assert summary.distinct_source_lineages == 1   # derived truth, not the claim


# --------------------------------------------------------------------------- #
# G2R-03 derived patch recurrence (caller lies must lose)
# --------------------------------------------------------------------------- #
def _patch_policy():
    """Miniature generic policy: watch -> escalation -> structural. The
    escalation ladder exists because STABLE -> TRANSFORMATION_CANDIDATE is not
    an M5 edge; all predicate material remains generic evidence properties."""
    return AdjudicatorPolicy.from_data({
        "policy_id": "g2r-patch",
        "version_tag": "V1",
        "rules": [
            {"rule_id": "enter.watch", "to_state": "WATCH",
             "any_of": [{"exception_burden": "MEDIUM"}]},
            {"rule_id": "escalate", "to_state": "ESCALATION_REVIEW",
             "all_of": [{"exception_burden": "MEDIUM"}],
             "persistence": {"channel": "exception_burden", "grade": "MEDIUM",
                             "minimum_observations": 3}},
            {"rule_id": "structural.sig", "to_state": "TRANSFORMATION_CANDIDATE",
             "all_of": [{"exception_burden": "HIGH"}],
             "patch": {"structural_level": "L3", "max_structural_level": "L6", "min_recurrence": 3}},
        ],
    })


def _patch_contract():
    return PhaseEvaluationContract.make(2, version_tag="PATCH-V1")


def _patch_spec(events):
    return StressScenarioSpec(scenario_id="patchder", stimulus_events=events,
                              initial_authority_state={"GOVERNOR": "GOVERNOR"})


def test_caller_lied_about_recurrence_derived_recurrence_wins():
    """One L3 patch claiming recurrence=99 with HIGH exceptions: derived
    recurrence is 1 -> no structural escalation; the audit exposes the derived
    value, not the lie."""
    events = [
        {"seq": 1, "evidence_vector": {"exception_burden": "HIGH"},
         "patch_pressure": {"structural_level": "L3", "causal_signature": "SIG_X",
                            "recurrence": 99, "override_count": 50}},
    ]
    res = run_scenario(_patch_spec(events), _patch_contract(), _patch_policy())
    assert "TRANSFORMATION_CANDIDATE" not in res.artifacts["actual_phase_trace"]
    assert res.artifacts["actual_phase_trace"] == ["STABLE", "WATCH"]
    audit = res.artifacts["transitions_audit"]
    assert audit[1]["patch_derived_recurrence"] == 1    # derived truth beats the lie


def test_derived_recurrence_drives_structural_threshold():
    """FOUR same-signature L3 patches -> derived recurrence reaches 4 at the
    fourth period -> structural escalation fires exactly then, despite each
    event claiming only 1 (caller recurrence never accumulates)."""
    events = [
        {"seq": i, "evidence_vector": {"exception_burden": "HIGH"},
         "patch_pressure": {"structural_level": "L3", "causal_signature": "SIG_K",
                            "recurrence": 1, "override_count": 1}}
        for i in range(1, 5)
    ]
    res = run_scenario(_patch_spec(events), _patch_contract(), _patch_policy())
    assert res.artifacts["actual_phase_trace"] == \
        ["STABLE", "WATCH", "ESCALATION_REVIEW", "TRANSFORMATION_CANDIDATE"]
    audit = res.artifacts["transitions_audit"]
    fired = [s for s, a in audit.items() if a["applied"] and a["to"] == "TRANSFORMATION_CANDIDATE"]
    assert fired == [4]                          # fires ONLY when derived count reaches 4
    assert audit[4]["patch_derived_recurrence"] == 4


def test_unrelated_signatures_do_not_aggregate():
    """Three DIFFERENT signatures, each L3 HIGH: no single signature reaches
    recurrence 3 -> no structural escalation (raw patch count is insufficient)."""
    events = [
        {"seq": i, "evidence_vector": {"exception_burden": "HIGH"},
         "patch_pressure": {"structural_level": "L3", "causal_signature": f"SIG_{i}",
                            "recurrence": 99, "override_count": 50}}
        for i in range(1, 4)
    ]
    res = run_scenario(_patch_spec(events), _patch_contract(), _patch_policy())
    assert res.artifacts["actual_phase_trace"] == ["STABLE", "WATCH", "ESCALATION_REVIEW"]
    assert "TRANSFORMATION_CANDIDATE" not in res.artifacts["actual_phase_trace"]


def test_s03_unrelated_signature_never_aggregates_in_pack():
    """The committed S03 fixture already contains the anti-overfit case: one L3
    SIG_X event lying recurrence=99 must NOT trigger escalation; only the L3
    SIG_C cluster (derived recurrence) does. Runs under the CORE policy."""
    pack = PACKS["S03"]
    res = run_scenario(pack.spec, pack.contract, pack.policy,
                       evidence_records=pack.observable_evidence)
    assert res.artifacts["actual_phase_trace"][-1] == "TRANSFORMATION_CANDIDATE"
    # the very last applied transition (obs11, SIG_C derived 8) is structural
    audit = res.artifacts["transitions_audit"]
    fired = [s for s, a in audit.items() if a["applied"] and a["to"] == "TRANSFORMATION_CANDIDATE"]
    assert fired == [11]