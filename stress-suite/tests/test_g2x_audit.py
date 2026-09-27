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
    return run_scenario(pack.spec, pack.contract, pack.policy,
                        evidence_records=pack.observable_evidence)


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

    foreign = run_scenario(pack_a.spec, contract_b, pack_a.policy,
                           evidence_records=pack_a.observable_evidence)

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
    """S04's evaluation contract does NOT admit ESCALATION_REVIEW ->
    TRANSFORMATION_CANDIDATE (G2R-06 admissible enforcement): replaying S03
    under S04's contract must change behavior — the structural proposal is
    blocked by the contract, never silently inherited."""
    own = _own_run("S03")
    s04_contract = PACKS["S04"].contract
    foreign = run_scenario(PACKS["S03"].spec, s04_contract, PACKS["S03"].policy,
                           evidence_records=PACKS["S03"].observable_evidence)
    assert _behavior_sig(foreign) != _behavior_sig(own)
    assert foreign.artifacts["terminal_phase"] != "TRANSFORMATION_CANDIDATE"
    # the block is recorded as a CONTRACT_INADMISSIBLE hold, not silence
    assert any(
        h.get("rule_id") == "CONTRACT_INADMISSIBLE" for h in foreign.artifacts["holds"]
    ), "the inadmissible proposal must be recorded, not silently dropped"
    verdict = evaluate_expectation(foreign, PACKS["S03"].spec)
    assert verdict["pass"] is False  # honestly fails against S03's own expectations


def test_s02_under_s01_contract_diverges_on_admissibility():
    """G2R-06 correction: S01's admissible list does NOT admit ESCALATION_REVIEW
    -> NO_CHANGE (S01 resolves via transformation, not NO_CHANGE). S02 replay
    under S01's contract therefore LEGITIMATELY diverges at the NO_CHANGE step —
    contract admissibility is now semantically enforced, so the old 'benign
    equivalence' assertion encoded the exact G2R-06 defect and is replaced by
    an honest contract-driven divergence check.

    Old assertion: S02 under S01 contract behaves identically (admissible list
    ignored).
    Why invalid: admissible_phase_transitions was fingerprint material but not
    semantically wired; a contract could not gate execution.
    Replacement: divergence + recorded CONTRACT_INADMISSIBLE hold."""
    own = _own_run("S02")
    s01_contract = PACKS["S01"].contract
    foreign = run_scenario(PACKS["S02"].spec, s01_contract, PACKS["S02"].policy,
                           evidence_records=PACKS["S02"].observable_evidence)
    assert _behavior_sig(foreign) != _behavior_sig(own)
    assert any(
        h.get("rule_id") == "CONTRACT_INADMISSIBLE" for h in foreign.artifacts["holds"]
    ), "NO_CHANGE blocked by S01 contract's admissible list must be recorded"
    assert evaluate_expectation(foreign, PACKS["S02"].spec)["pass"] is False
    # the contracts themselves still differ (identity kept)
    assert foreign.artifacts["fingerprint"] != own.artifacts["fingerprint"]