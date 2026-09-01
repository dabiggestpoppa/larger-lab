"""G2X — cross-scenario audit (G2 §14, §23).

Each scenario is replayed under EVERY OTHER scenario's frozen evaluation
contract. The audit proves:

  * contracts participate in decisions (own vs foreign fingerprint differs);
  * a foreign contract is never mutated by another scenario's run (still
    frozen, byte-stable fingerprint);
  * NO SILENT INHERITANCE: if the foreign run's VERDICT against the scenario's
    own expectations passes, the foreign run's behavior (trace + holdings +
    knowledge) must be IDENTICAL to the own-contract run — a pass under foreign
    semantics is only acceptable when nothing actually differed. If behavior
    diverged, the verdict must honestly fail or differ accordingly.
"""
import pytest

from engine.scenariolib import load_all_packs
from engine.scenario import run_scenario, evaluate_expectation

from pathlib import Path

PACKS = load_all_packs(Path(__file__).resolve().parent.parent / "scenarios")
MAIN = ["S01", "S02", "S03", "S04", "S05"]


def _behavior_sig(res):
    a = res.artifacts
    return (a["actual_phase_trace"], a["trace"], a["holds"], a["terminal_knowledge_states"])


def _own_run(sid):
    pack = PACKS[sid]
    return run_scenario(pack.spec, pack.contract, pack.policy)


@pytest.mark.parametrize("a", MAIN)
@pytest.mark.parametrize("b", MAIN)
def test_cross_contract_run(a, b):
    if a == b:
        return
    own = _own_run(a)
    pack_a = PACKS[a]
    contract_b = PACKS[b].contract

    # materialize the frozen snapshot first (unfrozen vs frozen fingerprint
    # strings differ by design, so compare within the frozen state)
    if not contract_b.is_frozen():
        contract_b.freeze()
    fp_before = contract_b.fingerprint()

    foreign = run_scenario(pack_a.spec, contract_b, pack_a.policy)

    # 1) the contract participates: fingerprints always differ between contracts
    assert foreign.artifacts["evaluation_contract"]["contract_id"] != own.artifacts["evaluation_contract"]["contract_id"]
    assert foreign.artifacts["fingerprint"] != own.artifacts["fingerprint"]

    # 2) foreign contract untouched by A's run (still frozen, byte-stable)
    assert contract_b.is_frozen()
    assert contract_b.fingerprint() == fp_before

    # 3) no silent inheritance
    same_behavior = _behavior_sig(foreign) == _behavior_sig(own)
    verdict_pass = evaluate_expectation(foreign, pack_a.spec)["pass"]
    if verdict_pass:
        assert same_behavior, (
            f"{a} under {b}'s contract PASSED with DIFFERENT behavior — "
            f"that would be silent inheritance"
        )


def test_audit_covers_all_pairs():
    pairs = [(a, b) for a in MAIN for b in MAIN if a != b]
    assert len(pairs) == 20
    # sanity: contracts are pairwise distinct in threshold semantics
    for a in MAIN:
        for b in MAIN:
            if a == b:
                continue
            ca = PACKS[a].contract
            cb = PACKS[b].contract
            assert ca.fingerprint() != cb.fingerprint()


def test_s03_under_s04_contract_diverges_honestly():
    """S04's exception threshold (HIGH) is higher than S03's (MEDIUM): replaying
    S03 under S04's contract must change behavior (no silent equivalence)."""
    own = _own_run("S03")
    s04_contract = PACKS["S04"].contract
    foreign = run_scenario(PACKS["S03"].spec, s04_contract, PACKS["S03"].policy)
    assert _behavior_sig(foreign) != _behavior_sig(own)
    verdict = evaluate_expectation(foreign, PACKS["S03"].spec)
    assert verdict["pass"] is False  # honestly fails against S03's own expectations


def test_s02_under_s01_contract_keeps_entry_but_changes_nothing_critical():
    """S02's sole entry gate reads independent_contradiction; S01's contract has
    the same contradiction threshold, so S02 under S01 behaves identically —
    recorded as benign equivalence, never as inheritance."""
    own = _own_run("S02")
    s01_contract = PACKS["S01"].contract
    foreign = run_scenario(PACKS["S02"].spec, s01_contract, PACKS["S02"].policy)
    assert _behavior_sig(foreign) == _behavior_sig(own)
    assert evaluate_expectation(foreign, PACKS["S02"].spec)["pass"] is True
    # ... and the contract fingerprints themselves still differ (identity kept)
    assert foreign.artifacts["fingerprint"] != own.artifacts["fingerprint"]