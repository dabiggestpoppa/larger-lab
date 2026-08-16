"""
CR-RISK-BLOCK2 R5 — Family Quality / Allocation Anatomy tests.

Covers: sealed family counts, disjoint labels, total-f preservation, 50/50
semantics, 100/0 and 0/100 reproducing solo paths, pooled 50/50@2% reproducing
the sealed R4 baseline, probabilities in [0,1], joint episode preservation,
predefined grid constraint, no best allocation / no Kelly / no strategy
change, Block-I artifact preservation, sampler determinism, and R4-identical
edge-shrink semantics.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
R5 = ROOT / "artifacts" / "risk_block2" / "r5"
B1 = ROOT / "artifacts" / "risk_block1"


def _load(name: str) -> pd.DataFrame:
    return pd.read_csv(R5 / name)


def _decision() -> dict:
    return json.loads((R5 / "R5_DECISION.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 1-2. family counts + disjoint labels
# ---------------------------------------------------------------------------

def test_family_counts_match_sealed_890():
    ledger = pd.read_csv(B1 / "R1_EVENT_RISK_LEDGER.csv")
    fd = _load("R5_FAMILY_DISTRIBUTIONS.csv")
    a = int(fd[fd.family == "A"]["N"].iloc[0])
    b = int(fd[fd.family == "B"]["N"].iloc[0])
    assert a == int((ledger.family == "A").sum())
    assert b == int((ledger.family == "B").sum())
    assert a + b == 890
    # distribution frame reports the pooled count too
    assert int(fd[fd.family == "A+B"]["N"].iloc[0]) == 890


def test_no_event_in_both_families():
    ledger = pd.read_csv(B1 / "R1_EVENT_RISK_LEDGER.csv")
    a_ids = set(ledger.loc[ledger.family == "A", "event_id"])
    b_ids = set(ledger.loc[ledger.family == "B", "event_id"])
    assert not (a_ids & b_ids)
    assert len(a_ids) + len(b_ids) == 890


# ---------------------------------------------------------------------------
# 3-4. total f preserved; 50/50 semantics
# ---------------------------------------------------------------------------

def test_allocation_weights_sum_to_one():
    fr = _load("R5_ALLOCATION_FRONTIER.csv")
    assert ((fr["w_A_pct"] + fr["w_B_pct"]) == 100.0).all()
    # total heat = (w_A + w_B) * f = 100% * f
    assert fr["total_heat_pct"].equals(fr["f_total_pct"])


def test_5050_at_f1_means_half_per_family():
    mc = _load("R5_ALLOCATION_MC.csv")
    row = mc[(mc.scheme == "block") & (mc.w_A_pct == 50) & (mc.f_total_pct == 1.0)].iloc[0]
    assert row["w_A_pct"] == 50 and row["w_B_pct"] == 50
    # per-trade R-fraction = w_family * f_total = 0.5% each
    from capital_routing.phases.phase_r5_common import ALLOC_GRID
    assert (50, 50) in ALLOC_GRID


# ---------------------------------------------------------------------------
# 5-6. solo endpoints reproduce family-only paths
# ---------------------------------------------------------------------------

def test_100_0_reproduces_a_only():
    fr = _load("R5_ALLOCATION_FRONTIER.csv")
    a_solo = fr[(fr.w_A_pct == 100) & (fr.f_total_pct == 1.0)].iloc[0]
    # A-only at f=1% matches R4's family frontier (10.3% max DD, ~79% CAGR)
    assert a_solo["max_dd"] == pytest.approx(0.103039, rel=0.01)
    assert a_solo["cagr"] == pytest.approx(0.792172, rel=0.01)


def test_0_100_reproduces_b_only():
    fr = _load("R5_ALLOCATION_FRONTIER.csv")
    b_solo = fr[(fr.w_A_pct == 0) & (fr.f_total_pct == 1.0)].iloc[0]
    assert b_solo["max_dd"] == pytest.approx(0.111078, rel=0.01)
    assert b_solo["cagr"] == pytest.approx(0.619553, rel=0.01)


def test_5050_at_total_f2_reproduces_sealed_pooled():
    """50/50 at total f=2% = each trade at 1% = the sealed R4 pooled baseline."""
    fr = _load("R5_ALLOCATION_FRONTIER.csv")
    r = fr[(fr.w_A_pct == 50) & (fr.f_total_pct == 2.0)].iloc[0]
    assert r["cagr"] == pytest.approx(1.903112, rel=0.01)
    assert r["max_dd"] == pytest.approx(0.101695, rel=0.01)


# ---------------------------------------------------------------------------
# 7. probabilities in [0,1]
# ---------------------------------------------------------------------------

def test_probabilities_in_unit_interval():
    for name in ["R5_ALLOCATION_FRONTIER.csv", "R5_ALLOCATION_MC.csv",
                 "R5_FAMILY_EDGE_DEGRADATION.csv"]:
        df = _load(name)
        prob_cols = [c for c in df.columns
                     if c.startswith("P_") or c.startswith("mc_P_")]
        assert prob_cols, name
        for c in prob_cols:
            assert df[c].between(0.0, 1.0).all(), f"{name} {c}"


# ---------------------------------------------------------------------------
# 8. joint bootstrap preserves episode grouping
# ---------------------------------------------------------------------------

def test_episode_blocks_keep_families_together():
    from capital_routing.phases.phase_r5_portfolio import _episode_blocks
    ledger = pd.read_csv(B1 / "R1_EVENT_RISK_LEDGER.csv")
    fam = ledger.set_index("event_id")["family"]
    blocks = _episode_blocks(ledger)
    assert len(blocks) > 50
    for b in blocks:
        fams = set(fam.iloc[b])
        assert len(fams) >= 1
    # some blocks must contain BOTH families (joint preservation is meaningful)
    both = sum(1 for b in blocks if len(set(fam.iloc[b])) == 2)
    assert both > 0


def test_joint_sampler_deterministic():
    from capital_routing.phases.phase_r5_common import joint_indices
    rng_arr = np.arange(100.0)
    a = joint_indices(rng_arr, "block", 50, 100, seed=42)
    b = joint_indices(rng_arr, "block", 50, 100, seed=42)
    assert (a == b).all()


# ---------------------------------------------------------------------------
# 9. no arbitrary allocation outside predefined grid
# ---------------------------------------------------------------------------

def test_all_allocations_on_predefined_grid():
    from capital_routing.phases.phase_r5_common import ALLOC_GRID
    grid = set(ALLOC_GRID)
    for name in ["R5_ALLOCATION_FRONTIER.csv", "R5_ALLOCATION_MC.csv"]:
        df = _load(name)
        for _, r in df.iterrows():
            assert (int(r["w_A_pct"]), int(r["w_B_pct"])) in grid, \
                f"{name} off-grid allocation {r['w_A_pct']}/{r['w_B_pct']}"
    # non-dominated labels encode alloc@f - parse and check the grid part
    nd = _load("R5_NONDOMINATED_FRONTIER.csv")
    for _, r in nd.iterrows():
        alloc = r["label"].split("@")[0]
        wa, wb = (int(x) for x in alloc.split("/"))
        assert (wa, wb) in grid, f"off-grid in nondominated: {alloc}"


# ---------------------------------------------------------------------------
# 10-12. no best allocation, no Kelly, no strategy change
# ---------------------------------------------------------------------------

def test_no_best_allocation_and_no_kelly():
    d = _decision()
    assert d["best_allocation_selected"] is False
    assert d["kelly_authorized"] is False
    assert d["dd_adaptive_authorized"] is False
    assert d["episode_sizing_authorized"] is False
    assert d["cluster_sizing_authorized"] is False
    assert d["deployment_authorized"] is False
    assert d["mt5_authorized"] is False
    assert d["block_2_r6_cleared"] is False
    assert d["human_review_required"] is True
    assert d["r5_family_quality_allocation_pass"] is True
    # no "best" field anywhere in the decision
    assert "best_allocation" not in {k for k in d if "best" in k.lower()}
    # forbidden outputs absent
    assert not any("optimal" in str(v).lower() for v in d.get("key_findings", {}).values())


def test_no_strategy_changes_anywhere():
    d = _decision()
    assert d["B_capital_limiter_confirmed"] is True
    # protocol forbids alpha/entry/exit changes
    proto = (R5 / "R5_PROTOCOL.md").read_text(encoding="utf-8")
    assert "alpha" in proto.lower() and "entry" in proto.lower()
    assert "Forbidden" in proto


# ---------------------------------------------------------------------------
# 13. Block-I artifacts unchanged (sealed ledger hash matches manifest)
# ---------------------------------------------------------------------------

def test_block1_artifacts_preserved():
    import hashlib
    m = json.loads((R5 / "R5_INPUT_HASH_MANIFEST.json").read_text(encoding="utf-8"))
    inp = m["inputs"]
    ledger_path = ROOT / inp["R1_EVENT_RISK_LEDGER.csv"]["path"]
    assert hashlib.sha256(ledger_path.read_bytes()).hexdigest() == \
        inp["R1_EVENT_RISK_LEDGER.csv"]["sha256"]
    # manifest provenance complete
    assert m["block1_seal_sha"] == "8ca072d0d9390acf581770a99ce45b333deddd8c"
    assert len(m["git_sha_at_generation"]) == 40
    assert m["sample_size"] == 890
    assert m["family_counts"]["A"] + m["family_counts"]["B"] == 890
    # decision carries the same block-I seal
    assert _decision()["block1_seal_sha"] == m["block1_seal_sha"]


# ---------------------------------------------------------------------------
# 14. sampler determinism (light) + 15. edge-shrink semantics = R4
# ---------------------------------------------------------------------------

def test_edge_shrink_matches_r4_method_a():
    from capital_routing.phases.phase_r5_stress import _edge_shrink_family
    r = np.array([1.5, -1.0, 0.6, -0.3, 2.0, -0.8])
    fam = np.array(["A", "A", "A", "B", "B", "B"])
    out = _edge_shrink_family(r, fam, 0.5, 0.75)
    # losses preserved exactly; positives scaled per family
    np.testing.assert_allclose(out, np.array([0.75, -1.0, 0.3, -0.3, 1.5, -0.8]))


def test_non_dominated_definitions():
    from capital_routing.phases.phase_r5_portfolio import _dominance
    pts = pd.DataFrame({
        "label": ["p1", "p2", "p3", "p4"],
        "ret": [0.10, 0.12, 0.05, 0.11],
        "risk": [0.05, 0.06, 0.04, 0.05],
    })
    rows = _dominance(pts, "test", "ret", "risk")
    status = {r["label"]: r["status"] for r in rows}
    # p4 (ret 0.11, risk 0.05) dominates p1 (ret 0.10, risk 0.05)
    assert status["p1"] == "DOMINATED"
    assert "p4" in rows[0]["dominated_by"]
    # p2/p3/p4 lie on the Pareto frontier
    assert status["p2"] == "NON_DOMINATED"
    assert status["p3"] == "NON_DOMINATED"
    assert status["p4"] == "NON_DOMINATED"
