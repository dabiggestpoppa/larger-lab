"""G3 receipt integrity.

* Committed per-scenario run_receipt.json files must byte-match a fresh run
  (receipts are reproducible evidence).
* The committed G3_EVIDENCE_RECEIPT.json must use the non-self-referential
  SHA lineage semantics (G3-P0-C): artifacts_head_sha distinct from
  externally_verified_branch_head, no self-pin claim.
"""
import json
import sys
from pathlib import Path

import pytest

from engine.g3_runner import load_g3_pack, run_g3_scenario, evaluate_g3_expectation
from engine.ecology_policy import EcologyPolicy

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "scenarios"
POLICY = EcologyPolicy.from_data(json.loads(
    (SCENARIOS / "policies/G3_COGNITIVE_ECOLOGY_POLICY.json").read_text(encoding="utf-8")))

PACK_DIRS = {
    "S06": SCENARIOS / "s06_correlated_consensus",
    "S07": SCENARIOS / "s07_independent_weaker_agents",
    "S08": SCENARIOS / "s08_reflective_bypass",
    "S09": SCENARIOS / "s09_counter_attractor_false_alarm",
}


def _fresh_receipt(sid: str) -> dict:
    pack = load_g3_pack(PACK_DIRS[sid])
    res = run_g3_scenario(pack.decision_grade(), POLICY)
    verdict = evaluate_g3_expectation(res, pack)
    a = res.artifacts
    # JSON round-trip so tuple/list serialization matches the committed file
    def j(x):
        return json.loads(json.dumps(x))
    return {
        "scenario_id": sid,
        "behavior_fingerprint": a["behavior_fingerprint"],
        "raw_reviewer_count": a["raw_reviewer_count"],
        "raw_vote_distribution": a["raw_vote_distribution"],
        "disposition": a["disposition"],
        "independent_confirmation_satisfied": a["independent_confirmation_satisfied"],
        "topology_decision": j(a["topology_decision"]),
        "friction_result": j(a["friction_result"]),
        "counter_attractor_result": j(a["counter_attractor_result"]),
        "facts": a["facts"],
        "cost_units": a["cost_units"],
        "pass": verdict["pass"],
        "failures": verdict["failures"],
    }


@pytest.mark.parametrize("sid", ["S06", "S07", "S08", "S09"])
def test_committed_g3_receipt_matches_fresh_run(sid):
    committed = json.loads((PACK_DIRS[sid] / "run_receipt.json").read_text(encoding="utf-8"))
    fresh = _fresh_receipt(sid)
    for key, value in fresh.items():
        assert committed.get(key) == value, \
            f"{sid} receipt field {key!r} diverged from a fresh run: {committed.get(key)!r} vs {value!r}"
    assert committed["pass"] is True
    assert committed["hidden_ground_truth_accessed"] is False
    assert committed["expected_accessed_during_run"] is False


def test_all_g3_receipts_pass_and_are_deterministic():
    for sid in ("S06", "S07", "S08", "S09"):
        r1 = _fresh_receipt(sid)
        r2 = _fresh_receipt(sid)
        assert r1 == r2
        assert r1["pass"] is True


def test_g3_receipt_uses_non_self_referential_sha_semantics():
    receipt = json.loads((ROOT / "evidence/G3_EVIDENCE_RECEIPT.json").read_text(encoding="utf-8"))
    lineage = receipt.get("receipt_lineage", {})
    assert "artifacts_head_sha" in lineage
    assert "receipt_content_parent_sha" in lineage
    assert "externally_verified_branch_head" in lineage
    # the receipt must NOT claim to pin its own containing commit
    assert lineage.get("self_pin_attempted") is False
    assert "receipt_terminal_commit" not in lineage
    assert lineage["externally_verified_branch_head"] is None or \
        isinstance(lineage["externally_verified_branch_head"], str)
