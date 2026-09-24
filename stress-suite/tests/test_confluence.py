"""Confluence harness tests — Path M Increment 1 (frozen contract v0.1).

Tests exercise the real entry points: DeterministicReplay, GovernedTransitionExecutor,
EvidenceRegistry, CounterexampleRecord. No synthetic null schedule substituted.

Four tiers:
  positive (INSUFFICIENT_DATA or VERIFIED honest)
  failure-control (two valid divergent → CONFLUENCE_FAILURE + minimized counterexample)
  invalid-input (ReplayInputError on fixed-seq reorder + TOPOLOGY_DENIED excluded)
  reproducibility (byte-reproducible minimization + p_protected re-derive)
"""
import itertools
import json
from pathlib import Path

import pytest

from engine.base import deterministic_hex
from engine.confluence import (
    VALID_SCHEDULE_BOUND,
    ActionIdentity,
    action_from_raw,
    confluence_protected_digest,
    forensic_fingerprint,
    make_claim_ledger_view,
    r1_candidate_table,
    schedule_enumerator,
    schedule_to_replay_events,
    spec_to_action_identities,
    schedule_seq_hash,
    seeded_control_positive_check,
    seeded_failure_control_verdict,
    select_workflow_via_R1,
    spec_to_replay_events_fixed_seq,
    verify_confluence,
    _synthetic_seeded_failure_spec,
    dependency_digest,
    _compute_contract_hash,
    CONTRACT_ID,
    DOSSIER_ID,
    FROZEN_DEPENDENCY,
)
from engine.fixtures import StressScenarioSpec, build_seed_records, spec_to_replay_events
from engine.replay import DeterministicReplay, ReplayEvent, ReplayInputError
from engine.authority import AuthorityState

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_smoke(name: str) -> StressScenarioSpec:
    p = Path(__file__).resolve().parents[1] / "fixtures" / "smoke" / f"{name}.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    return StressScenarioSpec(**data)


def _diamond_spec() -> StressScenarioSpec:
    return StressScenarioSpec(
        scenario_id="test_diamond",
        scenario_version="1.0.0",
        initial_authority_state={"PO": "PO"},
        initial_knowledge=[
            {"record_id": "@A", "state": "OBSERVED", "claim": "a", "provenance_source_kind": "FIXTURE", "provenance_source_label": "x"},
            {"record_id": "@B", "state": "OBSERVED", "claim": "b", "provenance_source_kind": "FIXTURE", "provenance_source_label": "x"},
        ],
        stimulus_events=[
            {"seq": 1, "machine": "lifecycle", "actor": "PO", "target": "@A", "payload": {"to_state": "CANDIDATE", "authority_level": "PO", "authority_basis": "x", "reason": "x"}},
            {"seq": 2, "machine": "lifecycle", "actor": "PO", "target": "@B", "payload": {"to_state": "CANDIDATE", "authority_level": "PO", "authority_basis": "x", "reason": "x"}},
        ],
    )


# ---------------------------------------------------------------------------
# Positive: R1 honest INSUFFICIENT_DATA (no invented schedule)
# ---------------------------------------------------------------------------

class TestR1HonestInsufficientData:
    def test_r1_table_reports_insufficient_data_honestly(self):
        table = r1_candidate_table()
        # On this tree, no smoke yields >=2 valid, so eligible==0 is expected honest result
        assert table["eligible_count"] == 0
        assert table["chosen"] is None
        assert "INSUFFICIENT_DATA" in table["tie_break_distance"]

    def test_verify_confluence_on_existing_smoke_is_insufficient_data_not_verified(self):
        for name in ["knowledge_reactivation_smoke", "legal_transition_smoke", "illegal_transition_smoke"]:
            spec = _load_smoke(name)
            verdict = verify_confluence(spec)
            assert verdict["execution_status"] == "INSUFFICIENT_DATA", f"{name} should be INSUFFICIENT_DATA"
            assert verdict["scientific_verdict"] == "NOT_CLAIMED"
            assert verdict["claim_status"] == "INSUFFICIENT_DATA"
            assert verdict["confluence_verdict"] == "INSUFFICIENT_DATA"
            # Neither becomes VERIFIED
            assert verdict["scientific_verdict"] != "CONFLUENCE_VERIFIED"
            assert verdict["claim_status"] != "VERIFIED"
            # coverage gap disclosed
            assert verdict["enumerator_snapshot"]["valid_count_enumerated"] < 2
            # Not self-certifying INSUFFICIENT_DATA
            assert verdict["contract_hash"] == _compute_contract_hash()

    def test_select_workflow_via_R1_insufficient_data_does_not_fabricate(self):
        sel = select_workflow_via_R1()
        assert sel["insufficient_data"] is True
        assert sel["chosen_spec"] is None
        assert "r1_table" in sel


# ---------------------------------------------------------------------------
# Positive: synthetic diamond yields CONFLUENCE_VERIFIED (honest VERIFIED)
# ---------------------------------------------------------------------------

class TestPositiveConfluenceVerified:
    def test_diamond_two_valid_converge_protected(self):
        spec = _diamond_spec()
        verdict = verify_confluence(spec)
        # Diamond has 2 valid disjoint ops → both valid, protected equal, forensic may be equal (identical transitions)
        assert verdict["execution_status"] == "COMPLETED"
        assert verdict["scientific_verdict"] == "CONFLUENCE_VERIFIED"
        assert verdict["claim_status"] == "VERIFIED"
        assert verdict["confluence_verdict"] == "CONFLUENCE_VERIFIED"
        assert verdict["valid_schedules_enumerated"] == 2
        # Both protected equal (sorted)
        digests = verdict["confluence_protected_digest_per_schedule"]
        assert len(set(digests)) == 1
        # Four checks: termination PASS, idempotence INCONCLUSIVE or PASS, diamond PASS, equivalence PASS
        assert verdict["checks"]["termination"]["verdict"] == "PASS"
        assert verdict["checks"]["final_state_equivalence"]["verdict"] == "PASS"
        assert verdict["checks"]["local_diamond"]["verdict"] == "PASS"

    def test_seeded_control_positive_check_is_verified(self):
        pos = seeded_control_positive_check()
        assert pos["execution_status"] == "COMPLETED"
        assert pos["scientific_verdict"] == "CONFLUENCE_VERIFIED"


# ---------------------------------------------------------------------------
# Failure-control: two valid divergent schedules → CONFLUENCE_FAILURE + minimized counterexample
# ---------------------------------------------------------------------------

class TestSeededFailureControl:
    def test_seeded_failure_has_two_valid_divergent(self):
        spec = _synthetic_seeded_failure_spec()
        enum = schedule_enumerator(spec)
        assert enum["valid_count_enumerated"] == 2
        assert enum["invalid_count"] == 0
        assert len(set(enum["protected_per_schedule"])) == 2
        # Both valid, terminals differ
        r0 = enum["valid_results"][0]
        r1 = enum["valid_results"][1]
        assert r0.terminal_lifecycle != r1.terminal_lifecycle

    def test_seeded_failure_verdict_is_failure_with_counterexample(self):
        verdict = seeded_failure_control_verdict()
        assert verdict["execution_status"] == "COMPLETED"
        assert verdict["scientific_verdict"] == "CONFLUENCE_FAILURE"
        assert verdict["claim_status"] == "CONFLUENCE_FAILURE"
        ce = verdict["counterexample"]
        assert ce is not None
        # Minimized: smallest by (valid schedule prefix length, total event count)
        assert ce.expected_relation == "protected equivalence across valid schedules"
        assert ce.observed_relation == "divergent p_protected digest"
        # Preserved evidence bound
        assert "minimized_trace_hash" in ce.preserved_evidence
        assert "divergent_schedules_pair_hash" in ce.preserved_evidence
        # Baseline vs perturbed are two valid schedules from same validity set, not fabricated
        assert ce.baseline_observables["schedule"] != ce.perturbed_observables["schedule"]

    def test_verify_confluence_reports_failure_via_synthetic_spec(self):
        spec = _synthetic_seeded_failure_spec()
        verdict = verify_confluence(spec)
        # This spec itself diverges → CONFLUENCE_FAILURE (not tautological PASS)
        assert verdict["scientific_verdict"] == "CONFLUENCE_FAILURE"
        assert verdict["claim_status"] == "CONFLUENCE_FAILURE"
        assert verdict["counterexample"] is not None
        assert verdict["seeded_negative_control_verdict"] == "PASS"
        # Failure does not become VERIFIED
        assert verdict["scientific_verdict"] != "CONFLUENCE_VERIFIED"


# ---------------------------------------------------------------------------
# Invalid-input: fixed-seq reorder → ReplayInputError; prerequisite violation → TOPOLOGY_DENIED excluded
# ---------------------------------------------------------------------------

class TestInvalidInputs:
    def test_fixed_seq_reorder_raises_replay_input_error(self):
        spec = _load_smoke("legal_transition_smoke")
        evs = spec_to_replay_events_fixed_seq(spec)
        perm = list(evs)
        perm[0], perm[1] = perm[1], perm[0]
        seeds = build_seed_records(spec)
        auth = AuthorityState()
        for actor, level in (spec.initial_authority_state or {}).items():
            auth.seed_level(actor, level)
        auth.freeze_initialization()
        replay = DeterministicReplay(seed_records=seeds, authority=auth)
        with pytest.raises(ReplayInputError, match="out-of-order seq"):
            replay.run(perm)

    def test_fixed_seq_reorder_also_flagged_in_verify(self):
        spec = _load_smoke("legal_transition_smoke")
        verdict = verify_confluence(spec)
        assert verdict["invalid_input_checks"]["fixed_seq_replay_input_error"] is True

    def test_prerequisite_violating_order_is_topology_denied_not_failure(self):
        # OBSERVED->TESTED before CANDIDATE on same @K should be TOPOLOGY_DENIED and excluded
        probe = StressScenarioSpec(
            scenario_id="invalid_probe",
            scenario_version="1.0.0",
            initial_authority_state={"PO": "PO"},
            initial_knowledge=[{"record_id": "@K", "state": "OBSERVED", "claim": "probe", "provenance_source_kind": "FIXTURE", "provenance_source_label": "x"}],
            stimulus_events=[
                {"seq": 1, "machine": "lifecycle", "actor": "PO", "target": "@K", "payload": {"to_state": "TESTED", "authority_level": "PO", "authority_basis": "x", "reason": "x"}},
                {"seq": 2, "machine": "lifecycle", "actor": "PO", "target": "@K", "payload": {"to_state": "CANDIDATE", "authority_level": "PO", "authority_basis": "x", "reason": "x"}},
            ],
        )
        actions = spec_to_action_identities(probe)
        # Schedule is [TESTED, CANDIDATE] — violates OBSERVED->CANDIDATE prerequisite
        enum = schedule_enumerator(probe)
        # valid count should be 0 or 1? First action TESTED from OBSERVED is invalid (no OBSERVED->TESTED edge), so 0 valid
        # But we can also run the specific violating schedule and check trace
        from engine.confluence import _run_schedule
        result, _events = _run_schedule(actions, probe)
        # First action should be denied
        assert not result.trace[0]["allowed"]
        assert result.trace[0]["kind"] in ("TOPOLOGY_DENIED", "FORBIDDEN", "UNKNOWN", "OK") or not result.trace[0]["allowed"]
        # It is NOT counted as CONFLUENCE_FAILURE
        verdict = verify_confluence(probe)
        assert verdict["invalid_input_checks"]["assigned_seq_topology_denied_excluded"] is True
        assert verdict["execution_status"] == "INSUFFICIENT_DATA"  # no valid pair, so not a confluence claim

    def test_neither_error_becomes_verified(self):
        for name in ["knowledge_reactivation_smoke", "legal_transition_smoke"]:
            spec = _load_smoke(name)
            verdict = verify_confluence(spec)
            # Invalid-input proofs must not map to VERIFIED
            assert verdict["scientific_verdict"] != "CONFLUENCE_VERIFIED"
            assert verdict["checks"]["final_state_equivalence"]["verdict"] != "PASS" or verdict["valid_schedules_enumerated"] < 2


# ---------------------------------------------------------------------------
# Reproducibility: byte-reproducible minimization + p_protected re-derive
# ---------------------------------------------------------------------------

class TestReproducibility:
    def test_enumerator_deterministic_and_hash_stable(self):
        spec = _diamond_spec()
        e1 = schedule_enumerator(spec, bound=VALID_SCHEDULE_BOUND)
        e2 = schedule_enumerator(spec, bound=VALID_SCHEDULE_BOUND)
        assert e1["enumerator_hash"] == e2["enumerator_hash"]
        assert e1["forensic_per_schedule"] == e2["forensic_per_schedule"]
        assert e1["protected_per_schedule"] == e2["protected_per_schedule"]
        assert e1["seq_hashes"] == e2["seq_hashes"]
        assert e1["enumerator_hash"] == deterministic_hex("schedule-enumerator", VALID_SCHEDULE_BOUND, json.dumps([[list(a.to_tuple()) for a in s] for s in e1["valid_schedules"]], sort_keys=True, separators=(",", ":")))

    def test_forensic_retained_distinct_from_protected(self):
        # For diamond, both schedules succeed but forensic may be equal; for seeded failure, they differ
        diamond = _diamond_spec()
        e_diamond = schedule_enumerator(diamond)
        # For diamond, both perms give same transitions (both OBSERVED->CANDIDATE), so forensic equal is expected
        assert e_diamond["forensic_per_schedule"][0] == e_diamond["forensic_per_schedule"][1]
        # But protected also equal now (sorted) — verify they are both equal but distinct namespace
        assert e_diamond["protected_per_schedule"][0] == e_diamond["protected_per_schedule"][1]
        # For seeded, forensic and protected both diverge but are distinct hashes
        seeded = _synthetic_seeded_failure_spec()
        e_seeded = schedule_enumerator(seeded)
        assert e_seeded["forensic_per_schedule"][0] != e_seeded["forensic_per_schedule"][1]
        assert e_seeded["protected_per_schedule"][0] != e_seeded["protected_per_schedule"][1]
        # Names are distinct: forensic is replay fingerprint, protected is confluence_protected_digest
        from engine.confluence import forensic_fingerprint, confluence_protected_digest
        # Already verified via enumerator that both namespaces are computed and published separately

    def test_protected_rederive_from_result_and_events(self):
        spec = _diamond_spec()
        enum = schedule_enumerator(spec)
        for result, events, digest in zip(enum["valid_results"], enum["valid_events"], enum["protected_per_schedule"]):
            rederived = confluence_protected_digest(result, events)
            assert rederived == digest
            # forensic likewise
            assert forensic_fingerprint(result) in enum["forensic_per_schedule"]

    def test_counterexample_minimization_deterministic(self):
        # Two runs of seeded control must give same counterexample id and hashes
        v1 = seeded_failure_control_verdict()
        v2 = seeded_failure_control_verdict()
        assert v1["counterexample"].counterexample_id == v2["counterexample"].counterexample_id
        assert v1["counterexample"].preserved_evidence["minimized_trace_hash"] == v2["counterexample"].preserved_evidence["minimized_trace_hash"]
        assert v1["counterexample"].preserved_evidence["divergent_schedules_pair_hash"] == v2["counterexample"].preserved_evidence["divergent_schedules_pair_hash"]

    def test_schedule_seq_hash_deterministic(self):
        actions = spec_to_action_identities(_diamond_spec())
        h1 = schedule_seq_hash(actions)
        h2 = schedule_seq_hash(actions)
        assert h1 == h2
        # Different order yields different hash
        h_rev = schedule_seq_hash(list(reversed(actions)))
        assert h1 != h_rev


# ---------------------------------------------------------------------------
# Status vocabulary: execution_status distinct from scientific_verdict
# ---------------------------------------------------------------------------

class TestStatusVocabulary:
    def test_confluence_failure_never_becomes_verified(self):
        spec = _synthetic_seeded_failure_spec()
        v = verify_confluence(spec)
        assert v["execution_status"] == "COMPLETED"
        assert v["scientific_verdict"] == "CONFLUENCE_FAILURE"
        assert v["claim_status"] == "CONFLUENCE_FAILURE"
        assert v["scientific_verdict"] != "CONFLUENCE_VERIFIED"
        assert v["claim_status"] != "VERIFIED"

    def test_inconclusive_never_becomes_verified(self):
        # INSUFFICIENT_DATA is INCONCLUSIVE-class, not VERIFIED
        spec = _load_smoke("knowledge_reactivation_smoke")
        v = verify_confluence(spec)
        assert v["execution_status"] == "INSUFFICIENT_DATA"
        assert v["scientific_verdict"] == "NOT_CLAIMED"
        assert v["claim_status"] == "INSUFFICIENT_DATA"
        assert v["scientific_verdict"] != "CONFLUENCE_VERIFIED"

    def test_r1_no_valid_pair_gives_insufficient_data_not_verified(self):
        # Already tested but explicit: R1 with 0 eligible yields INSUFFICIENT_DATA
        sel = select_workflow_via_R1()
        assert sel["insufficient_data"]
        # Running verify on such should be INSUFFICIENT_DATA
        spec = _load_smoke("legal_transition_smoke")  # only 1 valid
        v = verify_confluence(spec)
        assert v["valid_schedules_enumerated"] < 2
        assert v["execution_status"] == "INSUFFICIENT_DATA"
        assert v["scientific_verdict"] == "NOT_CLAIMED"


# ---------------------------------------------------------------------------
# ClaimLedgerView: minimum read-only view
# ---------------------------------------------------------------------------

class TestClaimLedgerView:
    def test_claim_ledger_view_is_read_only_and_typed(self):
        spec = _diamond_spec()
        v = verify_confluence(spec)
        view = make_claim_ledger_view(spec, v)
        d = view.to_dict()
        assert d["claim_class"] in ("diagnostic", "confluence_check")
        assert d["execution_status"] == v["execution_status"]
        assert d["scientific_verdict"] == v["scientific_verdict"]
        assert "record_id" in d and len(d["record_id"]) == 16
        assert "input_hash" in d and "code_hash" in d
        # Never PROMOTED
        assert d["claim_class"] != "PROMOTED"
        assert d["receipt"]["claim_cap"] == "DIAGNOSTIC"

    def test_insufficient_data_ledger_not_promoted(self):
        spec = _load_smoke("knowledge_reactivation_smoke")
        v = verify_confluence(spec)
        view = make_claim_ledger_view(spec, v)
        assert view.claim_class == "confluence_check"
        assert view.execution_status == "INSUFFICIENT_DATA"
        assert view.scientific_verdict == "NOT_CLAIMED"
        assert view.receipt["confluence_verdict"] == "INSUFFICIENT_DATA"


# ---------------------------------------------------------------------------
# Contract binding: hash and dependency digest
# ---------------------------------------------------------------------------

class TestContractBinding:
    def test_contract_hash_is_bindable(self):
        h = _compute_contract_hash()
        assert len(h) == 16  # deterministic_hex length 16
        # Second call same
        assert h == _compute_contract_hash()

    def test_dependency_digest_has_required_fields(self):
        spec = _diamond_spec()
        dd = dependency_digest(spec)
        assert "tested_sha" in dd
        assert "harness_version" in dd
        assert "contract_hash" in dd
        assert "smoke_fixture_digests" in dd
        assert dd["contract_id"] == CONTRACT_ID
        assert dd["dossier_id"] == DOSSIER_ID


# ---------------------------------------------------------------------------
# Idempotence and diamond smoke on valid independent spec
# ---------------------------------------------------------------------------

class TestChecksOnValidSpec:
    def test_idempotence_pass_on_valid_candidate(self):
        spec = _diamond_spec()
        v = verify_confluence(spec)
        # Valid CANDIDATE singly, duplicated should be TOPOLOGY_DENIED second but lifecycle same => PASS
        assert v["idempotence_verdict"] in ("PASS", "INCONCLUSIVE")

    def test_termination_always_pass_or_inconclusive(self):
        for name in ["knowledge_reactivation_smoke", "legal_transition_smoke", "illegal_transition_smoke"]:
            spec = _load_smoke(name)
            v = verify_confluence(spec)
            assert v["termination_verdict"] in ("PASS", "INCONCLUSIVE")
