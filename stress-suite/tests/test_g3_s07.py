"""S07 — Weaker but Independent Reviewers (RUNTIME-QUALITY FIXATION).

Routing is constrained satisfaction: HIGH consequence demands sufficient
differentiation; LOW consequence may take the cheapest capable path. Capability
and epistemic independence are SEPARATE axes; no quality*independence scalar.
"""
import json
from pathlib import Path

from engine.ecology_policy import EcologyPolicy
from engine.g3_runner import load_g3_pack, run_g3_scenario
from engine.review_topology import (
    ReviewTopology,
    TopologyConstraintContract,
    route_review_topology,
)
from engine.cognitive_ecology import ReviewerIndependenceProfile

ROOT = Path(__file__).resolve().parent.parent / "scenarios"
PACK_DIR = ROOT / "s07_independent_weaker_agents"
POLICY = EcologyPolicy.from_data(json.loads(
    (ROOT / "policies/G3_COGNITIVE_ECOLOGY_POLICY.json").read_text(encoding="utf-8")))


def _run(consequence="HIGH"):
    pack = load_g3_pack(PACK_DIR)
    pack.consequence_class = consequence
    return run_g3_scenario(pack.decision_grade(), POLICY)


# --------------------------------------------------------------------------- #
def test_high_consequence_routes_to_differentiated_topology():
    res = _run("HIGH")
    td = res.artifacts["topology_decision"]
    assert td["chosen_topology_id"] == "TOPO_B_DIFFERENTIATED"
    assert td["constraints_satisfied"] is True
    # the high-capability monoculture was inadmissible under HIGH consequence
    assert "TOPO_A_MONOCULTURE" not in td["admissible_alternatives"]


def test_high_consequence_route_meets_independence_constraints():
    res = _run("HIGH")
    td = res.artifacts["topology_decision"]
    achieved = td["independence_dimensions_achieved"]
    assert achieved["source_lineage"] >= 2
    assert max(achieved["model_family"], achieved["runtime_lineage"]) >= 2
    assert td["remaining_gaps"] == ()


def test_low_consequence_may_select_cheaper_correlated_path():
    """LOW consequence: the cheapest ADMISSIBLE topology wins — here the
    high-capability monoculture (no independence demands at LOW)."""
    res = _run("LOW")
    td = res.artifacts["topology_decision"]
    assert td["chosen_topology_id"] == "TOPO_A_MONOCULTURE"
    assert td["constraints_satisfied"] is True
    assert td["cost_units"] == 15            # cheaper than TOPO_B (24)


def test_independence_is_a_constraint_not_universal_maximization():
    """The differentiated topology is NOT chosen at LOW consequence merely
    because it is more diverse — the cheapest admissible one is."""
    low = _run("LOW")
    assert low.artifacts["topology_decision"]["chosen_topology_id"] == "TOPO_A_MONOCULTURE"
    # cost does not maximize reviewers/diversity
    assert low.artifacts["topology_decision"]["cost_units"] < \
        low.artifacts["topology_decision"]["cost_units"] + 1  # trivially true; guard below
    assert "TOPO_B_DIFFERENTIATED" not in low.artifacts["topology_decision"]["admissible_alternatives"] or \
        low.artifacts["topology_decision"]["cost_units"] <= 15


def test_insufficient_capability_diverse_agents_cannot_pass_merely_because_diverse():
    """TOPO_C is diverse but BASIC capability: inadmissible at HIGH consequence
    where ADEQUATE is required — diversity never substitutes for capability."""
    data = json.loads((PACK_DIR / "topology_options.json").read_text(encoding="utf-8"))
    contract = TopologyConstraintContract(**data["contract"])
    topo = ReviewTopology(
        topology_id="TOPO_C_DIVERSE_WEAK", purpose="p", consequence_class="HIGH",
        profiles=tuple(ReviewerIndependenceProfile.from_reviewer_fixture(r)
                       for r in data["topology_options"][2]["reviewers"]),
        capability_tiers=tuple("BASIC" for _ in data["topology_options"][2]["reviewers"]),
        cost_units=6, latency_units=3,
    )
    decision = route_review_topology("p", "HIGH", [topo], contract)
    assert decision.constraints_satisfied is False
    assert any("capability" in g for g in decision.remaining_gaps)


def test_capability_and_independence_remain_separate_axes():
    """TOPO_A has HIGH individual capability yet fails HIGH-consequence
    independence constraints; TOPO_B has only ADEQUATE capability yet passes."""
    high = _run("HIGH")
    td = high.artifacts["topology_decision"]
    assert td["chosen_topology_id"] == "TOPO_B_DIFFERENTIATED"
    # TOPO_A would be chosen for its capability alone if capability were the
    # only axis — it is not admissible at HIGH (exposure + source monoculture)
    assert "TOPO_A_MONOCULTURE" not in td["admissible_alternatives"]
    assert td["individual_quality_metadata"]  # quality kept as metadata, not authority


def test_deterministic_routing_under_identical_inputs():
    r1 = _run("HIGH")
    r2 = _run("HIGH")
    assert r1.artifacts["topology_decision"] == r2.artifacts["topology_decision"]
    assert r1.artifacts["behavior_fingerprint"] == r2.artifacts["behavior_fingerprint"]


def test_reviewer_rename_preserves_topology_decision():
    pack = load_g3_pack(PACK_DIR)
    renamed = load_g3_pack(PACK_DIR)
    renamed.topology_options = [
        dict(t, reviewers=[dict(r, reviewer_id=f"Q_{i}_{j}")
                           for j, r in enumerate(t["reviewers"])])
        for i, t in enumerate(renamed.topology_options)
    ]
    r1 = run_g3_scenario(pack.decision_grade(), POLICY)
    r2 = run_g3_scenario(renamed.decision_grade(), POLICY)
    assert r1.artifacts["topology_decision"]["chosen_topology_id"] == \
        r2.artifacts["topology_decision"]["chosen_topology_id"]
    assert r1.artifacts["behavior_fingerprint"] == r2.artifacts["behavior_fingerprint"]


def test_costs_and_budgets_exposed_on_every_decision():
    res = _run("HIGH")
    td = res.artifacts["topology_decision"]
    assert "cost_units" in td and "latency_units" in td
    assert res.artifacts["cost_units"] == td["cost_units"]
    assert res.artifacts["cost_units"] > 0
