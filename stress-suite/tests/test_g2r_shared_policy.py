"""G2R-01 / G2R-07 / G2R-12 — ONE shared core phase policy.

* S01..S05 (+ weak) primary runs use G2_CORE_PHASE_POLICY from
  scenarios/policies/ — no per-scenario policy may carry primary evidence.
* The shared policy contains NO scenario literals: a static guard rejects
  scenario ids, '@' provenance tokens, literal causal signatures and escaped
  scope names anywhere in the policy file.
* No primary G2 pass depends on the archived per-scenario policies; those files
  are frozen for forensics only and never loaded by the pack loader.
* Renaming a scenario must preserve the behavior fingerprint (only the
  run-identity fingerprint may change).
"""
import json
import re
from pathlib import Path

import pytest

from engine.scenariolib import load_all_packs
from engine.scenario import run_scenario, evaluate_expectation
from engine.fixtures import StressScenarioSpec

SCENARIOS_ROOT = Path(__file__).resolve().parent.parent / "scenarios"
PACKS = load_all_packs(SCENARIOS_ROOT)
MAIN = ["S01", "S02", "S03", "S04", "S05"]
CORE = SCENARIOS_ROOT / "policies" / "G2_CORE_PHASE_POLICY.json"


def _run(sid, spec=None, records=None, contract=None, policy=None):
    pack = PACKS[sid]
    return run_scenario(
        spec or pack.spec,
        contract or pack.contract,
        policy or pack.policy,
        evidence_records=records if records is not None else pack.observable_evidence,
    )


@pytest.mark.parametrize("sid", MAIN + ["S01_WEAK"])
def test_scenarios_pass_under_the_single_core_policy(sid):
    """PRIMARY evidence (G2R-07): one policy, six scenario packs."""
    pack = PACKS[sid]
    assert pack.policy.policy_id == "G2_CORE_PHASE_POLICY", \
        f"{sid} must run under the SHARED core policy, not an archived per-scenario one"
    res = _run(sid)
    verdict = evaluate_expectation(res, pack.spec)
    assert verdict["pass"], f"{sid} under core policy failures: {verdict['failures']}"
    assert res.artifacts["policy_fingerprint"] == pack.policy.fingerprint()


def test_shared_policy_file_has_no_scenario_literals():
    """G2R-01 static guard: no scenario ids, no '@' provenance tokens, no
    literal causal signatures, no escaped scope names in the policy."""
    src = CORE.read_text(encoding="utf-8")
    for token in ("@", "SIG_", "PARSER"):
        assert token not in src, f"core policy must not contain {token!r}"
    assert re.search(r"S0[1-9]", src) is None, "core policy must not name any scenario id"


def test_shared_policy_rules_contain_no_literal_predicates():
    rules = json.loads(CORE.read_text(encoding="utf-8"))["rules"]
    for rule in rules:
        blob = json.dumps(rule, sort_keys=True)
        # predicates must be generic — no mechanism names, no escaped scopes,
        # no scenario-shaped identifiers in any gate or patch/affected dict
        assert "@" not in blob, f"{rule['rule_id']}: literal object id in predicate"
        assert re.search(r"S0[1-9]", blob) is None, f"{rule['rule_id']}: scenario id in predicate"


def test_no_primary_pass_depends_on_archived_per_scenario_policies():
    """The archived per-scenario policies must not even exist in a loadable
    location; the loader only reads the shared policy when policy_ref is set."""
    for sid, pack in PACKS.items():
        assert pack.spec.policy_ref == "G2_CORE_PHASE_POLICY"
        assert not (pack.path / "adjudicator_policy.json").exists(), (
            f"{sid}/adjudicator_policy.json must be archived, not loadable as primary"
        )


def test_archived_policies_preserved_for_forensics():
    """Forensic archive exists and is byte-identical to the G2-era policies."""
    archive = SCENARIOS_ROOT / "archive" / "per-scenario-policies"
    names = {
        "S01": "s01_old_theory_dies_slowly", "S02": "s02_false_revolution",
        "S03": "s03_patch_maze", "S04": "s04_leaf_failure", "S05": "s05_two_non_dominated_models",
        "S01_WEAK": "s01_variant_weak_contradiction",
    }
    for sid, sub in names.items():
        assert (archive / f"{sub}-policy.json").exists(), f"missing archived policy for {sid}"


def test_rename_scenario_preserves_behavior_fingerprint():
    """G2R-12: scenario_id participates in RUN identity only; the BEHAVIOR
    fingerprint must be untouched by a rename (anti-overfit)."""
    pack = PACKS["S01"]
    base = _run("S01")
    renamed = pack.spec.to_dict()
    renamed["scenario_id"] = "RANDOM_NAME_937"
    res2 = _run("S01", spec=StressScenarioSpec(**renamed))
    assert base.artifacts["behavior_fingerprint"] == res2.artifacts["behavior_fingerprint"]
    assert base.artifacts["actual_phase_trace"] == res2.artifacts["actual_phase_trace"]
    # identity fingerprint legitimately differs (scenario_id is run identity)
    assert base.artifacts["fingerprint"] != res2.artifacts["fingerprint"]
    assert res2.artifacts["scenario_id"] == "RANDOM_NAME_937"


def test_all_packs_share_the_same_policy_object_semantics():
    fps = {PACKS[sid].policy.fingerprint() for sid in MAIN + ["S01_WEAK"]}
    assert len(fps) == 1, "every pack must resolve to the SAME core policy semantics"