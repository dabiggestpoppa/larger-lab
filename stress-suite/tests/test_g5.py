"""G5 — CLASS C domain resilience regression suite (S14–S19).

Enforces, not merely asserts:
  OBSERVE BEFORE PREDICT, STATE BEFORE ACTION, PROFIT != VALIDATION,
  MISSING DATA != NEGATIVE EVIDENCE, ANALOGY != TRANSFER,
  AUTHORITATIVE MANUAL != IMMUNE FROM CONTRADICTION,
  CONTRADICTION != SILENT REWRITE.

Covers: B7 gate discipline, priority-vs-promotion separation, PnL metamorphics,
forbidden shortcuts, doctrine preservation, source-layer diagnosis order,
DATA_BLOCKED + SearchDemand, sensor reactivation without retroactive
validation, and the transfer firewall. Static guards check the shared policy
for scenario-id / literal / expected-outcome scripting.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "scenarios"
G5_DIRS = {
    "S14": SCENARIOS / "s14_huge_fake_alpha",
    "S15": SCENARIOS / "s15_new_alpha_family",
    "S16": SCENARIOS / "s16_cerebus_contradiction",
    "S17": SCENARIOS / "s17_crypto_provider_disagreement",
    "S18": SCENARIOS / "s18_sensor_gap",
    "S19": SCENARIOS / "s19_crypto_to_fx_transfer",
}
POLICY_DATA = json.loads((SCENARIOS / "policies/G5_DOMAIN_EPISTEMIC_POLICY.json")
                         .read_text(encoding="utf-8"))

from engine.domain import SOURCE_DIAGNOSTIC_LAYERS  # noqa: E402
from engine.domain_policy import G5DomainPolicy, KNOWN_G5_FIELDS  # noqa: E402
from engine.g5_runner import (  # noqa: E402
    load_g5_pack, run_g5_scenario, evaluate_g5_expectation,
    G5ScenarioPack,
)

POLICY = G5DomainPolicy.from_data(POLICY_DATA)


# --------------------------------------------------------------------------- #
# static policy guards (sealing / no scenario scripting)
# --------------------------------------------------------------------------- #
def test_shared_policy_has_no_scenario_ids_or_literals():
    """Decision logic only: rule conditions + outcomes must be generic. The
    authority_basis prose may name the scenario FAMILY it serves (like G4's
    policy names S10-S13), but no rule may branch on a scenario id, a literal
    strategy/provider/concept name or an expected outcome."""
    blob = json.dumps([{"when": r["when"], "then": r["then"]}
                       for r in POLICY_DATA["rules"]])
    for token in ("S14", "S15", "S16", "S17", "S18", "S19",
                  "CAND_FAKE_ALPHA", "BYBIT_LINEAR", "BINANCE_USDM",
                  "MECH_LIQUIDATION_FLOW_1", "ARBITRAGE_CAPITAL_BANDWIDTH",
                  "CEREBUS_V4_P90_TARGET_METRICS"):
        assert token not in blob, f"policy rule bodies must not reference {token!r}"
    for rule in POLICY_DATA["rules"]:
        assert set(rule["when"]) <= set(KNOWN_G5_FIELDS)


def test_shared_policy_known_dispositions_only():
    from engine.domain_policy import KNOWN_DISPOSITIONS
    for rule in POLICY.rules:
        disp = rule.then.get("disposition", rule.then.get("outcome", ""))
        assert disp in KNOWN_DISPOSITIONS


def test_policy_change_changes_behavior():
    """The shared policy actually governs the S14 disposition: flipping the
    REJECTED rule to VALIDATION_REQUIRED changes the runner's decision."""
    pack = load_g5_pack(G5_DIRS["S14"]).decision_grade()
    a = run_g5_scenario(pack, POLICY)
    data = copy.deepcopy(POLICY_DATA)
    for rule in data["rules"]:
        if rule["rule_id"] == "g5.claim.rejected_on_material_gates":
            rule["then"]["disposition"] = "VALIDATION_REQUIRED"
    variant = G5DomainPolicy.from_data(data)
    b = run_g5_scenario(pack, variant)
    assert a.artifacts["items"][0]["disposition"] == "REJECTED_NEGATIVE_KNOWLEDGE"
    assert b.artifacts["items"][0]["disposition"] == "VALIDATION_REQUIRED"
    assert a.artifacts["behavior_fingerprint"] != b.artifacts["behavior_fingerprint"]


def test_primary_packs_load_and_all_pass():
    for sid, d in G5_DIRS.items():
        pack = load_g5_pack(d)
        res = run_g5_scenario(pack.decision_grade(), POLICY)
        verdict = evaluate_g5_expectation(res, pack)
        assert verdict["pass"], f"{sid}: {verdict['failures']}"
        assert res.artifacts["expected_outcome_accessed"] is False
        assert res.artifacts["hidden_ground_truth_accessed"] is False


def test_wrong_expected_outcome_does_not_change_execution():
    """G5 §20: wrong expected result leaves the execution fingerprint unchanged."""
    pack = load_g5_pack(G5_DIRS["S14"])
    a = run_g5_scenario(pack.decision_grade(), POLICY)
    pack2 = copy.deepcopy(pack)
    pack2.expected_outcome = "DATA_BLOCKED"
    b = run_g5_scenario(pack2.decision_grade(), POLICY)
    assert a.artifacts["behavior_fingerprint"] == b.artifacts["behavior_fingerprint"]


def test_scenario_rename_leaves_behavior_unchanged():
    from engine.g5_runner import run_s15

    pack = load_g5_pack(G5_DIRS["S15"]).decision_grade()
    a = run_s15(pack, POLICY)
    renamed = G5ScenarioPack(**{**pack.__dict__, "scenario_id": "SXX"})
    b = run_s15(renamed, POLICY)
    assert a.artifacts["behavior_fingerprint"] == b.artifacts["behavior_fingerprint"]


# --------------------------------------------------------------------------- #
# S14 — huge fake alpha
# --------------------------------------------------------------------------- #
def test_primary_fixture_rejects_despite_extreme_pnl():
    pack = load_g5_pack(G5_DIRS["S14"]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    item = res.artifacts["items"][0]
    assert item["performance"]["economic_value_class"] == "EXTREME"
    assert item["research_priority"]["priority"] == "PRIORITY_HIGH"
    assert item["promotion_decision"]["decision"] == "REJECTED"
    assert item["disposition"] == "REJECTED_NEGATIVE_KNOWLEDGE"
    assert "LOOKAHEAD_LEAKAGE" in [a["failure_id"] for a in item["failure_atoms"]]
    assert "UNREALISTIC_FILL_MODEL" in [a["failure_id"] for a in item["failure_atoms"]]
    assert item["negative_knowledge"] is not None
    assert item["reopen_conditions"]  # machine-readable


def test_pit_leak_detected_from_timestamps():
    """The gate discovers lookahead from observable availability/decision times,
    never from the hidden ground truth."""
    from engine.domain import B7ValidationGate, FeatureUse, FillRecord, StrategyCandidate, PerformanceReport
    cand = StrategyCandidate(
        candidate_id="C", family="F", specification_ref="S",
        performance=PerformanceReport(sharpe=3.0, cumulative_return=10.0,
                                      max_drawdown=0.01, win_rate=0.8),
        features=(FeatureUse("FUT", 100, 150, 90, 40),),  # availability 150 > decision 90: leaks
        fills=(FillRecord("FIL", 500, 501, "NORMAL", 100, 50, 1.0),))
    res = B7ValidationGate().run(cand)
    assert res.terminal == "REJECTED"
    assert "PIT_INTEGRITY" in res.material_failures
    assert any(a.failure_id == "LOOKAHEAD_LEAKAGE" for a in res.failure_atoms)


def test_impossible_fill_detected():
    from engine.domain import B7ValidationGate, FeatureUse, FillRecord, StrategyCandidate, PerformanceReport
    cand = StrategyCandidate(
        candidate_id="C", family="F", specification_ref="S",
        performance=PerformanceReport(sharpe=2.0, cumulative_return=5.0,
                                      max_drawdown=0.02, win_rate=0.7),
        features=(FeatureUse("FEAT", 100, 100, 200),),
        fills=(FillRecord("FIL", 500, 490, "NORMAL", 100, 50, 0.0),   # fill before signal
               FillRecord("FIL2", 600, 601, "NORMAL", 5, 200, 0.0)))  # size > depth
    res = B7ValidationGate().run(cand)
    assert res.terminal == "REJECTED"
    assert "EXECUTION_REALISM" in res.material_failures


def test_priority_and_promotion_are_separate():
    """PRIORITY_HIGH may coexist with PROMOTION_REJECTED (mandatory S14)."""
    pack = load_g5_pack(G5_DIRS["S14"]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    item = res.artifacts["items"][0]
    assert item["research_priority"]["priority"] == "PRIORITY_HIGH"
    assert item["promotion_decision"]["decision"] == "REJECTED"


def test_control_a_fixing_lookahead_only_still_rejects():
    pack = load_g5_pack(G5_DIRS["S14"]).decision_grade()
    res = run_g5_scenario(pack, POLICY, fix_lookahead=True)
    item = res.artifacts["items"][0]
    assert "LOOKAHEAD_LEAKAGE" not in [a["failure_id"] for a in item["failure_atoms"]]
    assert "UNREALISTIC_FILL_MODEL" in [a["failure_id"] for a in item["failure_atoms"]]
    assert item["disposition"] == "REJECTED_NEGATIVE_KNOWLEDGE"


def test_control_b_fixing_fills_only_still_rejects():
    pack = load_g5_pack(G5_DIRS["S14"]).decision_grade()
    res = run_g5_scenario(pack, POLICY, fix_fills=True)
    item = res.artifacts["items"][0]
    assert "LOOKAHEAD_LEAKAGE" in [a["failure_id"] for a in item["failure_atoms"]]
    assert item["disposition"] == "REJECTED_NEGATIVE_KNOWLEDGE"


def test_control_c_moderate_clean_progresses_farther():
    """A moderate clean candidate passes the B7 vector and becomes
    VALIDATION_REQUIRED (never promoted) while the fake alpha is REJECTED."""
    data = json.loads((G5_DIRS["S14"] / "strategies.json").read_text(encoding="utf-8"))
    clean = {
        "candidate_id": "CAND_CLEAN",
        "family": "MEAN_REVERSION_CASH",
        "specification_ref": "SPEC:CLEAN",
        "performance": {"sharpe": 1.4, "cumulative_return": 0.8,
                        "max_drawdown": 0.06, "win_rate": 0.58, "sample_years": 3.0},
        "features": [{"feature_id": "FEAT_OK", "observation_time": 100,
                      "availability_time": 100, "decision_time": 200, "pct": 100}],
        "fills": [{"fill_id": "FILL_OK", "signal_time": 500, "fill_time": 505,
                   "spread_state": "NORMAL", "depth_available": 1000, "size": 100,
                   "slippage_bps": 2.0, "low_liquidity": False}],
        "data_lineage": "synthetic fixture", "dataset_ref": "DS",
        "parameter_count": 2, "sample_count": 4000,
        "holdout_ref": "H", "walk_forward_ref": "W", "cost_model_ref": "C",
    }
    pack = G5ScenarioPack(scenario_id="S14", strategies=[clean]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    item = res.artifacts["items"][0]
    assert item["material_failures"] == []
    assert item["promotion_decision"]["decision"] == "PROMOTED"  # validated gates
    assert item["disposition"] == "VALIDATION_REQUIRED"          # but not promoted into execution
    assert item["research_priority"]["priority"] == "PRIORITY_NORMAL"


def test_pnl_metamorphic_x10_unchanged_verdict():
    """A. Multiply reported PnL by 10 => validation outcome unchanged."""
    pack = load_g5_pack(G5_DIRS["S14"]).decision_grade()
    a = run_g5_scenario(pack, POLICY, pnl_multiplier=1.0)
    b = run_g5_scenario(pack, POLICY, pnl_multiplier=10.0)
    assert a.artifacts["items"][0]["disposition"] == b.artifacts["items"][0]["disposition"]
    assert a.artifacts["items"][0]["promotion_decision"]["decision"] == \
        b.artifacts["items"][0]["promotion_decision"]["decision"]
    # priority may rise; verdict must not
    assert b.artifacts["items"][0]["research_priority"]["priority"] == "PRIORITY_HIGH"


def test_fake_alpha_negative_knowledge_has_reopen_conditions():
    from engine.reopen import ReopenCondition
    pack = load_g5_pack(G5_DIRS["S14"]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    nk = res.artifacts["items"][0]["negative_knowledge"]
    assert nk is not None
    # reopen conditions are machine-readable (constructable -> fail-closed vocab)
    conditions = [ReopenCondition.make(i, **c)
                  for i, c in enumerate(res.artifacts["items"][0]["reopen_conditions"])]
    assert conditions[0].subject_ref == "CAND_FAKE_ALPHA"


def test_profit_cannot_purchase_promotion():
    """Both the fake alpha at 58x and a 10x variant are rejected — profit does
    not purchase epistemic promotion."""
    pack = load_g5_pack(G5_DIRS["S14"]).decision_grade()
    for mult in (1.0, 10.0, 100.0):
        res = run_g5_scenario(pack, POLICY, pnl_multiplier=mult)
        assert res.artifacts["items"][0]["promotion_decision"]["decision"] == "REJECTED"


# --------------------------------------------------------------------------- #
# S15 — new alpha family
# --------------------------------------------------------------------------- #
def test_unknown_family_allowed():
    pack = load_g5_pack(G5_DIRS["S15"]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    assert res.artifacts["patterns"][0]["family_label"] == "UNKNOWN_FAMILY"
    assert res.artifacts["patterns"][0]["disposition"] == "ONTOLOGY_EXPLORATION_CANDIDATE"


def test_nearest_family_forcing_prohibited():
    """No nearest-family label is injected: the pattern's family stays
    UNKNOWN_FAMILY throughout the run."""
    pack = load_g5_pack(G5_DIRS["S15"]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    assert res.artifacts["patterns"][0]["family_label"] == "UNKNOWN_FAMILY"
    assert all(p["family_label"] == "UNKNOWN_FAMILY" for p in res.artifacts["patterns"])


def test_mechanism_card_precedes_strategy_and_no_execution_artifact():
    pack = load_g5_pack(G5_DIRS["S15"]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    mech = res.artifacts["mechanism"]
    assert mech["strategy_created"] is False
    assert mech["execution_artifact_created"] is False
    assert mech["forbidden_transition_blocked"] is True
    assert mech["mechanism_card"]["mechanism_id"] == "MECH_ORPHAN_1"
    assert mech["frozen_protocol"]["protocol_id"] == "PROTO_ORPHAN_1"


def test_frozen_protocol_immutable_fingerprint():
    from engine.domain import FrozenExperimentProtocol
    raw = json.loads((G5_DIRS["S15"] / "protocols.json").read_text(encoding="utf-8"))[0]
    p1 = FrozenExperimentProtocol.from_fixture(raw)
    p2 = FrozenExperimentProtocol.from_fixture(raw)
    assert p1.fingerprint == p2.fingerprint
    # criteria cannot change after result: fingerprint is bound to content
    raw2 = dict(raw)
    raw2["promotion_criteria"] = ["something looser"]   # post-hoc threshold change
    assert FrozenExperimentProtocol.from_fixture(raw2).fingerprint != p1.fingerprint


def test_control_a_quality_failure_kills_false_pattern():
    raw = json.loads((G5_DIRS["S15"] / "unresolved_patterns.json").read_text(encoding="utf-8"))[0]
    bad = dict(raw)
    bad["data_quality_passed"] = False
    pack = G5ScenarioPack(scenario_id="S15", unresolved_patterns=[bad]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    assert res.artifacts["patterns"][0]["disposition"] == "UNRESOLVED_PATTERN"


def test_control_b_single_lineage_remains_unresolved():
    raw = json.loads((G5_DIRS["S15"] / "unresolved_patterns.json").read_text(encoding="utf-8"))[0]
    one = dict(raw)
    one["evidence_lineages"] = 1
    pack = G5ScenarioPack(scenario_id="S15", unresolved_patterns=[one]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    assert res.artifacts["patterns"][0]["disposition"] == "UNRESOLVED_PATTERN"


def test_control_c_sensor_dependent_pattern_routes_data_blocked():
    raw = json.loads((G5_DIRS["S15"] / "unresolved_patterns.json").read_text(encoding="utf-8"))[0]
    dep = dict(raw)
    dep["required_sensor"] = "AGGRESSOR_FLOW_STATE"
    pack = G5ScenarioPack(scenario_id="S15", unresolved_patterns=[dep]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    assert res.artifacts["patterns"][0]["disposition"] == "DATA_BLOCKED"


def test_unresolved_pattern_cannot_become_strategy():
    """FORBIDDEN SHORTCUT: UNRESOLVED_PATTERN -> StrategySpec is impossible."""
    pack = load_g5_pack(G5_DIRS["S15"]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    assert "strategy_created" in res.artifacts["mechanism"]
    assert res.artifacts["mechanism"]["strategy_created"] is False
    assert res.artifacts["mechanism"]["execution_artifact_created"] is False


def test_rename_pattern_leaves_decision_unchanged():
    """B. Rename S15's unknown pattern => ontology decision unchanged."""
    pack = load_g5_pack(G5_DIRS["S15"]).decision_grade()
    a = run_g5_scenario(pack, POLICY)
    renamed = G5ScenarioPack(**{**pack.__dict__, "unresolved_patterns": [
        {**p, "pattern_id": "UP_RENAMED"} for p in pack.unresolved_patterns]})
    b = run_g5_scenario(renamed, POLICY)
    assert b.artifacts["patterns"][0]["disposition"] == a.artifacts["patterns"][0]["disposition"]
    assert b.artifacts["cluster"]["pattern_refs"] != a.artifacts["cluster"]["pattern_refs"] \
        or b.artifacts["patterns"][0]["disposition"] == a.artifacts["patterns"][0]["disposition"]


# --------------------------------------------------------------------------- #
# S16 — CEREBUS manual contradiction
# --------------------------------------------------------------------------- #
def test_exact_manual_claim_preserved():
    pack = load_g5_pack(G5_DIRS["S16"]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    claim = res.artifacts["doctrine_claims"][0]
    assert claim["authority_class"] == "CEREBUS_MANUAL"
    assert claim["current_status"] == "AUTHORITATIVE"
    assert claim["source_fingerprint"]  # recorded
    assert claim["numeric_parameters"]["win_rate_band"] == [0.85, 0.90]
    assert claim["source_path"].endswith("CEREBUS_v4_Manual_EXTRACTED.txt")


def test_clean_contradiction_opens_contradiction_and_preserves_manual():
    pack = load_g5_pack(G5_DIRS["S16"]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    statuses = {r["reproduction_id"]: r["status"] for r in res.artifacts["reproduction_results"]}
    assert statuses["REPRO_CLEAN_1"] == "CONTRADICTION_OPEN"
    assert res.artifacts["manual_modified"] is False
    assert res.artifacts["manual_claim_rewritten"] is False
    assert len(res.artifacts["contradictions"]) == 1
    assert res.artifacts["amendment_operator_required"] is True
    assert res.artifacts["amendment_ratified"] is False


def test_flawed_reproduction_rejected_manual_preserved():
    pack = load_g5_pack(G5_DIRS["S16"]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    statuses = {r["reproduction_id"]: r["status"] for r in res.artifacts["reproduction_results"]}
    assert statuses["REPRO_FLAWED_1"] == "REPRODUCTION_REJECTED"
    assert res.artifacts["manual_modified"] is False


def test_doctrine_claim_never_overwritten_by_reproduction():
    """MANUAL CLAIM and REPRODUCTION RESULT stay separate objects; the
    contradiction is a relation, not a rewrite."""
    res = run_g5_scenario(load_g5_pack(G5_DIRS["S16"]).decision_grade(), POLICY).artifacts
    claim = res["doctrine_claims"][0]
    assert claim["current_status"] == "AUTHORITATIVE"
    assert res["reproduction_results"][0]["status"] != "AUTHORITATIVE"


def test_generic_quant_convention_cannot_override_manual():
    """MANUAL AUTHORITY decides what doctrine IS; evidence only challenges it."""
    pack = load_g5_pack(G5_DIRS["S16"]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    assert res.artifacts["manual_modified"] is False
    assert all(r["manual_preserved"] for r in res.artifacts["reproduction_results"])


def test_amendment_requires_operator():
    res = run_g5_scenario(load_g5_pack(G5_DIRS["S16"]).decision_grade(), POLICY).artifacts
    assert res["amendment_operator_required"] is True
    assert res["amendment_ratified"] is False


def test_claim_id_rename_leaves_doctrine_authority_unchanged():
    """C. Rename the CEREBUS claim id => doctrine authority unchanged."""
    pack = load_g5_pack(G5_DIRS["S16"]).decision_grade()
    renamed = G5ScenarioPack(**{**pack.__dict__, "doctrine_claims": [
        {**c, "claim_id": "CEREBUS_RENAMED"} for c in pack.doctrine_claims]})
    a = run_g5_scenario(pack, POLICY)
    b = run_g5_scenario(renamed, POLICY)
    assert a.artifacts["manual_modified"] == b.artifacts["manual_modified"] is False
    assert b.artifacts["doctrine_claims"][0]["current_status"] == "AUTHORITATIVE"
    assert b.artifacts["amendment_operator_required"] is True


def test_operator_preference_cannot_fabricate_contradiction():
    """A bare 'operator prefers different' input cannot create a contradiction
    record without a CLEAN reproduction result."""
    raw = json.loads((G5_DIRS["S16"] / "reproductions.json").read_text(encoding="utf-8"))
    for r in raw:
        r["result"] = "SUPPORTS_CLAIM" if r["reproduction_id"] == "REPRO_CLEAN_1" else r["result"]
    pack = G5ScenarioPack(scenario_id="S16", doctrine_claims=[
        json.loads((G5_DIRS["S16"] / "doctrine_claims.json").read_text(encoding="utf-8"))[0]],
        reproductions=raw).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    assert len(res.artifacts["contradictions"]) == 0


# --------------------------------------------------------------------------- #
# S17 — provider disagreement
# --------------------------------------------------------------------------- #
def _s17_pack():
    return load_g5_pack(G5_DIRS["S17"]).decision_grade()


def test_source_layer_diagnosis_first_cause_unit_mismatch():
    """Primary fixture: GATE reports USD notional with un-wired normalization
    => NORMALIZATION_MISMATCH discovered at the normalization layer."""
    res = run_g5_scenario(_s17_pack(), POLICY).artifacts
    first = res["diagnoses"][0]
    assert first["cause"] == "NORMALIZATION_MISMATCH"
    layers = [s["layer"] for s in first["steps"]]
    assert layers == ["provider_semantics", "instrument_identity", "adapter", "normalization"]
    assert first["terminal"] == "REPAIRABLE_SOURCE_MISMATCH"


def test_instrument_mapping_mismatch_localized():
    res = run_g5_scenario(_s17_pack(), POLICY).artifacts
    causes = {d["cause"] for d in res["diagnoses"]}
    assert "INSTRUMENT_MISMATCH" in causes


def test_genuine_disagreement_preserved_not_averaged():
    res = run_g5_scenario(_s17_pack(), POLICY).artifacts
    genuine = [d for d in res["diagnoses"] if d["cause"] == "GENUINE_SOURCE_DISAGREEMENT"]
    assert genuine
    g = genuine[0]
    assert g["terminal"] == "GENUINE_SOURCE_DISAGREEMENT"
    assert g["source_disagreement_record"]["preserved"] is True
    assert g["averaged_to_consensus"] is False
    assert g["field_ontology_rewritten"] is False
    # native values are preserved individually (340 vs 212), never averaged
    record = g["source_disagreement_record"]
    assert record["value_a"] == 340.0 and record["value_b"] == 212.0


def test_diagnosis_order_invariant():
    """CANONICAL ORDER: source semantics before field interpretation."""
    res = run_g5_scenario(_s17_pack(), POLICY).artifacts
    for d in res["diagnoses"]:
        layers = [s["layer"] for s in d["steps"]]
        idx = {name: i for i, name in enumerate(SOURCE_DIAGNOSTIC_LAYERS)}
        assert layers == sorted(layers, key=lambda l: idx[l])


def test_provider_rename_metamorphic_semantics_preserved():
    """D. Swap provider names while preserving semantics => diagnosis unchanged."""
    pack = _s17_pack()
    obs = copy.deepcopy(pack.provider_observations)
    rename = {"BYBIT_LINEAR": "EXCHANGE_X", "GATE_FUTURES": "EXCHANGE_Y"}
    for o in obs:
        o["provider"] = rename.get(o["provider"], o["provider"])
        o["observation_id"] = f"RENAMED_{o['observation_id']}"
    renamed = G5ScenarioPack(**{**pack.__dict__, "provider_observations": obs,
                                "provider_semantics": [
                                    {**s, "provider": rename.get(s["provider"], s["provider"])}
                                    for s in pack.provider_semantics]})
    a = run_g5_scenario(pack, POLICY)
    b = run_g5_scenario(renamed, POLICY)
    assert [d["cause"] for d in a.artifacts["diagnoses"]] == \
        [d["cause"] for d in b.artifacts["diagnoses"]]


def test_control_a_normalization_repair_removes_disagreement():
    """Once normalization is valid, the notional-vs-contracts pair agrees."""
    from engine.domain import (ProviderObservation, ProviderSemanticsRecord,
                               diagnose_provider_disagreement)
    obs_a = ProviderObservation.from_fixture({
        "observation_id": "O1", "provider": "BYBIT_LINEAR",
        "instrument_native_id": "BTCUSDT", "instrument_canonical_id": "BTC_USDT_PERP",
        "metric": "OPEN_INTEREST_STATE", "contract_type": "PERP_LINEAR",
        "units": "CONTRACTS", "timestamp_value": 1, "time_window": "5m",
        "event_time": 1, "receive_time": 2, "mode": "HISTORICAL",
        "native_value": 220000.0, "normalized_value": 220000.0,
        "quality_state": "OK", "adapter_version": "v"})
    obs_b = ProviderObservation.from_fixture({
        "observation_id": "O2", "provider": "GATE_FUTURES",
        "instrument_native_id": "BTC_USDT", "instrument_canonical_id": "BTC_USDT_PERP",
        "metric": "OPEN_INTEREST_STATE", "contract_type": "PERP_LINEAR",
        "units": "USD_NOTIONAL", "timestamp_value": 1, "time_window": "5m",
        "event_time": 1, "receive_time": 2, "mode": "HISTORICAL",
        "native_value": 14000000000.0, "normalized_value": 220000.0,
        "quality_state": "OK", "adapter_version": "v"})
    sem_a = ProviderSemanticsRecord(provider="BYBIT_LINEAR", metric="OPEN_INTEREST_STATE",
                                    native_units="CONTRACTS", canonical_units="CONTRACTS",
                                    instrument_mapping_ok=True, adapter_version="v",
                                    time_window="5m", timestamp_semantics="EVENT",
                                    quality_state="OK", normalization_valid=True)
    sem_b_broken = ProviderSemanticsRecord(provider="GATE_FUTURES", metric="OPEN_INTEREST_STATE",
                                           native_units="USD_NOTIONAL",
                                           canonical_units="CONTRACTS",
                                           instrument_mapping_ok=True, adapter_version="v",
                                           time_window="5m", timestamp_semantics="EVENT",
                                           quality_state="OK", normalization_valid=False)
    sem_b_repaired = ProviderSemanticsRecord(provider="GATE_FUTURES",
                                             metric="OPEN_INTEREST_STATE",
                                             native_units="USD_NOTIONAL",
                                             canonical_units="CONTRACTS",
                                             instrument_mapping_ok=True, adapter_version="v",
                                             time_window="5m", timestamp_semantics="EVENT",
                                             quality_state="OK", normalization_valid=True)
    broken = diagnose_provider_disagreement(obs_a, obs_b, sem_a, sem_b_broken)
    assert broken.cause == "NORMALIZATION_MISMATCH"
    repaired = diagnose_provider_disagreement(obs_a, obs_b, sem_a, sem_b_repaired)
    assert repaired.cause == "NO_DISAGREEMENT"


# --------------------------------------------------------------------------- #
# S18 — sensor gap
# --------------------------------------------------------------------------- #
def test_unavailable_required_sensor_data_blocked():
    pack = load_g5_pack(G5_DIRS["S18"]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    blocked = res.artifacts["blocked_claims"]
    assert all(b["disposition"] == "DATA_BLOCKED" for b in blocked)
    assert res.artifacts["synthetic_backfill_used"] is False
    assert res.artifacts["blocked_claim_demoted_as_false"] is False


def test_partial_history_not_adequate():
    """PARTIAL is not adequate historical coverage for the mechanism."""
    pack = load_g5_pack(G5_DIRS["S18"]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    hist = [b for b in res.artifacts["blocked_claims"]
            if b["required_observable"] == "HISTORICAL_LIQUIDATION_DETAIL"][0]
    assert hist["data_availability"] != "AVAILABLE"
    assert hist["adequate_history"] is False
    assert hist["disposition"] == "DATA_BLOCKED"


def test_search_demand_emitted_with_reopen_condition():
    res = run_g5_scenario(load_g5_pack(G5_DIRS["S18"]).decision_grade(), POLICY).artifacts
    demands = res["search_demands"]
    assert len(demands) == 2
    for d in demands:
        assert d["status"] == "OPEN"
        assert "AVAILABLE" in d["reopen_condition"]


def test_blocked_claim_not_demoted_as_false():
    """MISSING DATA != NEGATIVE EVIDENCE."""
    res = run_g5_scenario(load_g5_pack(G5_DIRS["S18"]).decision_grade(), POLICY).artifacts
    assert res["blocked_claim_demoted_as_false"] is False


def test_sensor_arrival_reactivates_via_governed_reopen_not_validation():
    res = run_g5_scenario(load_g5_pack(G5_DIRS["S18"]).decision_grade(), POLICY,
                          sensor_available_later=True).artifacts
    assert res["activation"]
    for act in res["activation"]:
        assert act["reopen_outcome"] == "REOPEN_CANDIDATE"
        assert act["retroactively_validated"] is False


def test_search_demand_is_not_claim_validation():
    """FORBIDDEN SHORTCUT: SearchDemand -> claim validation is impossible."""
    res = run_g5_scenario(load_g5_pack(G5_DIRS["S18"]).decision_grade(), POLICY).artifacts
    assert all(b["disposition"] == "DATA_BLOCKED" for b in res["blocked_claims"])
    assert res["search_demands"]


def test_unknown_is_not_available():
    """UNKNOWN data availability is never treated as AVAILABLE."""
    from engine.domain import DataAvailabilityRecord, SensorRequirement
    req = SensorRequirement.from_fixture({
        "requirement_id": "R", "claim_ref": "C", "required_observable": "X",
        "resolution": "1m", "history_depth": "12m", "instrument_coverage": ["I"],
        "time_semantics": "EVENT", "quality_minimum": "VERIFIED",
        "why_required": "w", "alternative_insufficient": "a"})
    rec = DataAvailabilityRecord.from_fixture({
        "observable": "X", "status": "UNKNOWN"})
    assert rec.adequate_history(req) is False


def test_rename_missing_sensor_preserves_data_blocked():
    """E. Rename the missing sensor while preserving capability =>
    DATA_BLOCKED behavior unchanged."""
    pack = load_g5_pack(G5_DIRS["S18"]).decision_grade()
    renamed = G5ScenarioPack(**{**pack.__dict__, "sensor_requirements": [
        {**r, "required_observable": "FLOW_DETAIL_RENAMED",
         "requirement_id": "REQ_RENAMED"} for r in pack.sensor_requirements]})
    a = run_g5_scenario(pack, POLICY)
    b = run_g5_scenario(renamed, POLICY)
    assert all(b["disposition"] == "DATA_BLOCKED" for b in b.artifacts["blocked_claims"])
    assert len(b.artifacts["search_demands"]) == len(a.artifacts["search_demands"])


# --------------------------------------------------------------------------- #
# S19 — transfer firewall
# --------------------------------------------------------------------------- #
def test_source_domain_claim_stays_crypto():
    res = run_g5_scenario(load_g5_pack(G5_DIRS["S19"]).decision_grade(), POLICY).artifacts
    t = res["transfers"][0]
    assert t["source_domain"] == "CRYPTO"
    assert t["target_domain"] == "FX"
    assert t["source_concept"] == "ARBITRAGE_CAPITAL_BANDWIDTH"


def test_missing_target_observables_data_blocked():
    """CONTROL B: mapping + target sensor unavailable => DATA_BLOCKED."""
    res = run_g5_scenario(load_g5_pack(G5_DIRS["S19"]).decision_grade(), POLICY).artifacts
    assert res["transfers"][0]["disposition"] == "DATA_BLOCKED"
    assert res["transfers"][0]["fx_strategy_generated"] is False


def test_invariant_map_required_and_name_alone_insufficient():
    res = run_g5_scenario(load_g5_pack(G5_DIRS["S19"]).decision_grade(), POLICY).artifacts
    tmap = res["transfers"][0]["transfer_map"]
    assert tmap["mechanism_invariants"]
    assert tmap["source_observables"] and tmap["target_observables"]


def test_broken_structural_assumption_transfer_rejected():
    pack = load_g5_pack(G5_DIRS["S19"]).decision_grade()
    res = run_g5_scenario(pack, POLICY, broken_mapping=True)
    assert res.artifacts["transfers"][0]["disposition"] == "TRANSFER_REJECTED"


def test_target_data_frozen_protocol_routes_domain_validation_required():
    """CONTROL C: mapping + target data + frozen protocol =>
    DOMAIN_VALIDATION_REQUIRED (never DOMAIN_VALIDATED on source evidence)."""
    pack = load_g5_pack(G5_DIRS["S19"]).decision_grade()
    res = run_g5_scenario(pack, POLICY, target_data_available=True, protocol_frozen=True)
    assert res.artifacts["transfers"][0]["disposition"] == "DOMAIN_VALIDATION_REQUIRED"
    assert res.artifacts["transfers"][0]["source_validation_as_target_validation"] is False


def test_without_frozen_protocol_transfer_stays_hypothesis():
    pack = load_g5_pack(G5_DIRS["S19"]).decision_grade()
    res = run_g5_scenario(pack, POLICY, target_data_available=True, protocol_frozen=False)
    assert res.artifacts["transfers"][0]["disposition"] == "TRANSFER_HYPOTHESIS_ONLY"


def test_analogy_control_same_name_different_mechanics():
    """CONTROL A: same concept name with different observable mechanics =>
    ANALOGY_ONLY."""
    raw = json.loads((G5_DIRS["S19"] / "transfer_hypotheses.json").read_text(encoding="utf-8"))[0]
    analogy = copy.deepcopy(raw)
    analogy["transfer_map"]["source_observables"] = ["spot_perp_basis"]
    analogy["transfer_map"]["target_observables"] = ["order_book_snapshots"]
    analogy["transfer_map"]["mechanism_invariants"] = []     # name match only
    pack = G5ScenarioPack(scenario_id="S19",
                          transfer_hypotheses=[analogy]).decision_grade()
    res = run_g5_scenario(pack, POLICY)
    assert res.artifacts["transfers"][0]["disposition"] == "ANALOGY_ONLY"


def test_cerebus_doctrine_not_overridden_by_analogy():
    res = run_g5_scenario(load_g5_pack(G5_DIRS["S19"]).decision_grade(), POLICY).artifacts
    assert res["transfers"][0]["cerebus_doctrine_overridden"] is False


def test_source_validation_cannot_be_target_validation():
    """Source-domain evidence alone can never reach DOMAIN_VALIDATED."""
    pack = load_g5_pack(G5_DIRS["S19"]).decision_grade()
    for kwargs in ({"target_data_available": True, "protocol_frozen": True},
                   {"target_data_available": True, "protocol_frozen": False},
                   {"target_data_available": False}):
        res = run_g5_scenario(pack, POLICY, **kwargs)
        assert res.artifacts["transfers"][0]["disposition"] != "DOMAIN_VALIDATED"


def test_rename_crypto_concept_preserves_transfer_disposition():
    """F. Rename the crypto concept => transfer disposition unchanged."""
    pack = load_g5_pack(G5_DIRS["S19"]).decision_grade()
    renamed = G5ScenarioPack(**{**pack.__dict__, "transfer_hypotheses": [
        {**t, "source_concept": "CAPACITY_RENAMED"} for t in pack.transfer_hypotheses]})
    a = run_g5_scenario(pack, POLICY)
    b = run_g5_scenario(renamed, POLICY)
    assert a.artifacts["transfers"][0]["disposition"] == b.artifacts["transfers"][0]["disposition"]


# --------------------------------------------------------------------------- #
# cross-scenario comparisons
# --------------------------------------------------------------------------- #
def test_s14_vs_s15_good_evidence_beats_good_pnl():
    """S14 (huge PnL + invalid evidence) => REJECTED; S15 (unknown family +
    clean evidence) => ONTOLOGY_EXPLORATION_CANDIDATE. Good evidence wins over
    good PnL."""
    r14 = run_g5_scenario(load_g5_pack(G5_DIRS["S14"]).decision_grade(), POLICY).artifacts
    r15 = run_g5_scenario(load_g5_pack(G5_DIRS["S15"]).decision_grade(), POLICY).artifacts
    assert r14["items"][0]["disposition"] == "REJECTED_NEGATIVE_KNOWLEDGE"
    assert r15["patterns"][0]["disposition"] == "ONTOLOGY_EXPLORATION_CANDIDATE"


def test_s17_vs_s18_disagreement_is_not_absence():
    res17 = run_g5_scenario(_s17_pack(), POLICY).artifacts
    res18 = run_g5_scenario(load_g5_pack(G5_DIRS["S18"]).decision_grade(), POLICY).artifacts
    assert any(d["cause"] == "GENUINE_SOURCE_DISAGREEMENT" for d in res17["diagnoses"])
    assert all(b["data_availability"] != "AVAILABLE" for b in res18["blocked_claims"])


def test_s16_vs_s17_doctrine_contradiction_distinct_from_source_disagreement():
    r16 = run_g5_scenario(load_g5_pack(G5_DIRS["S16"]).decision_grade(), POLICY).artifacts
    r17 = run_g5_scenario(_s17_pack(), POLICY).artifacts
    assert len(r16["contradictions"]) == 1
    assert r16["amendment_operator_required"] is True
    assert all(d["terminal"] in ("REPAIRABLE_SOURCE_MISMATCH", "GENUINE_SOURCE_DISAGREEMENT")
               for d in r17["diagnoses"])
    assert all(d["field_ontology_rewritten"] is False for d in r17["diagnoses"])


def test_zero_mutations_in_every_run():
    for sid, d in G5_DIRS.items():
        res = run_g5_scenario(load_g5_pack(d).decision_grade(), POLICY)
        a = res.artifacts
        assert a["authority_before"] == a["authority_after"] == "NONE"
        assert a["expected_outcome_accessed"] is False
        assert a["hidden_ground_truth_accessed"] is False