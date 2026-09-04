"""G5R — domain evidence / doctrine / sensor / transfer integrity regression suite.

Closes fixture-declared truth paths (G5R-01..25) and exercises adversarial
cases A–J. Core law, enforced not asserted:

  CLAIMED INDEPENDENCE != VERIFIED INDEPENDENCE
  CLAIMED REPRODUCTION QUALITY != REPRODUCTION QUALITY
  CLAIMED CONTRADICTION != MEASURED CONTRADICTION
  AVAILABLE != ADEQUATE
  PROTOCOL_FROZEN=true != RESOLVED FROZEN PROTOCOL
  RATIFIED=true != GOVERNED RATIFICATION
  ANALOGY != TRANSFER

Every test is deterministic, local, model-free and wall-clock-free. Zero model
calls, zero production/cloud/capital mutation surfaces.
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
POLICY = None


def _policy():
    global POLICY
    if POLICY is None:
        from engine.domain_policy import G5DomainPolicy
        POLICY = G5DomainPolicy.from_data(json.loads(
            (SCENARIOS / "policies/G5_DOMAIN_EPISTEMIC_POLICY.json")
            .read_text(encoding="utf-8")))
    return POLICY


from engine.domain import (  # noqa: E402
    B7ValidationGate, B7ValidationResult, DataAvailabilityRecord,
    DisagreementToleranceContract, FrozenExperimentProtocol,
    ProviderObservation, ProviderSemanticsRecord, SensorRequirement,
    StrategyCandidate, FeatureUse, FillRecord, PerformanceReport,
    TransferInvariantMap,
)
from engine.g5_runner import (  # noqa: E402
    load_g5_pack, run_g5_scenario, G5ScenarioPack, run_s15, run_s16, run_s18,
    run_s19,
)
from engine.g5r import (  # noqa: E402
    DoctrineAmendmentProposal, DoctrineClaimAtom, DoctrineComparison,
    ObservedResult, ReproductionProtocol, SensorCapabilityChangeRecord,
    assess_sensor_adequacy, compare_measured_result, decide_mechanism_admission,
    derive_independence, derive_reproduction_quality,
    govern_amendment_ratification, recompute_source_binding,
    validate_sha256_digest, validate_transfer_map,
)
from engine.registry import EvidenceRegistry
from engine.evidence import EvidenceRecord


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _registry(*refs):
    reg = EvidenceRegistry()
    for rid, lineage in refs:
        reg.register(EvidenceRecord(record_id=rid, kind="INDEPENDENT_CONFIRMATION",
                                    claim=f"ev {rid}", source_lineage=lineage, seq=0))
    return reg


def _req(**over):
    base = {"requirement_id": "R", "claim_ref": "C", "required_observable": "X",
            "resolution": "1m", "history_depth": "12m", "instrument_coverage": ["I"],
            "time_semantics": "EVENT", "quality_minimum": "VERIFIED",
            "why_required": "w", "alternative_insufficient": "a"}
    base.update(over)
    return SensorRequirement.from_fixture(base)


def _avail(**over):
    base = {"observable": "X", "status": "AVAILABLE", "history_depth": "12m",
            "instrument_coverage": ["I"], "claimed": True, "verified": True,
            "source": "CRYPTO_SENSOR_FABRIC", "resolution": "1m",
            "time_semantics": "EVENT", "quality_state": "VERIFIED",
            "certification": "AUTHORITATIVE_SYNTHETIC_SENSOR_FIXTURE"}
    base.update(over)
    return DataAvailabilityRecord.from_fixture(base)


def _obs(oid, **over):
    base = {"observation_id": oid, "provider": "P", "instrument_native_id": "BTC",
            "instrument_canonical_id": "BTC_USDT_PERP", "metric": "M",
            "contract_type": "PERP_LINEAR", "units": "CONTRACTS",
            "timestamp_value": 1, "time_window": "5m", "event_time": 1,
            "receive_time": 2, "mode": "HISTORICAL", "native_value": 1.0,
            "normalized_value": 1.0, "quality_state": "OK", "adapter_version": "v1"}
    base.update(over)
    return ProviderObservation.from_fixture(base)


def _sem(provider="P", metric="M", **over):
    base = {"provider": provider, "metric": metric, "native_units": "CONTRACTS",
            "canonical_units": "CONTRACTS", "instrument_mapping_ok": True,
            "adapter_version": "v1", "time_window": "5m",
            "timestamp_semantics": "EVENT", "quality_state": "OK",
            "canonical_instrument": "BTC_USDT_PERP", "contract_type": "PERP_LINEAR"}
    base.update(over)
    return ProviderSemanticsRecord.from_fixture(base)


def _s19_adequate_pack():
    pack = load_g5_pack(G5_DIRS["S19"]).decision_grade()
    adequate = []
    for req in pack.sensor_requirements:
        adequate.append({"observable": req["required_observable"], "status": "AVAILABLE",
                         "history_depth": req["history_depth"],
                         "instrument_coverage": list(req["instrument_coverage"]),
                         "claimed": True, "verified": True,
                         "source": "CRYPTO_SENSOR_FABRIC",
                         "resolution": req["resolution"],
                         "time_semantics": req["time_semantics"],
                         "quality_state": req["quality_minimum"],
                         "certification": "AUTHORITATIVE_SYNTHETIC_SENSOR_FIXTURE"})
    return G5ScenarioPack(**{**pack.__dict__, "data_availability": adequate})


# =========================================================================== #
# G5R-01 — S15 independence must be proven from paths
# =========================================================================== #
def test_raw_integer_cannot_mint_independence():
    """CASE A: evidence_lineages=99 with no registered refs => NOT independent."""
    from engine.domain import UnresolvedPatternRecord
    p = UnresolvedPatternRecord.from_fixture({
        "pattern_id": "UP", "domain": "FX", "observations": ["OBS_A"],
        "conditions": ["c"], "data_quality_passed": True,
        "known_family_fit_attempts": [], "residual_behavior": "r",
        "independence_evidence_refs": [], "falsifiers": [], "what_remains_unexplained": "x",
        "evidence_lineages": 99})
    a = derive_independence(p, _registry(), {})
    assert a.independence_status != "CONFIRMED"
    assert a.verified_distinct_lineage_count == 0
    assert "99" not in a.rationale or a.independence_status == "UNRESOLVED"
    # end-to-end: the RUNNER must not mint exploration from the integer
    pack = G5ScenarioPack(scenario_id="S15", unresolved_patterns=[p.to_dict()],
                          evidence=[]).decision_grade()
    res = run_g5_scenario(pack, _policy())
    assert res.artifacts["patterns"][0]["disposition"] == "UNRESOLVED_PATTERN"


def test_zero_lineage_does_not_become_one():
    p = _pattern(refs=[])
    a = derive_independence(p, _registry(), {})
    assert a.independence_status == "UNRESOLVED"
    assert a.unknown_lineage_count == 0
    assert a.verified_distinct_lineage_count == 0


def test_duplicate_lineage_not_independent():
    """Two registered refs on the SAME lineage => one lineage, not two."""
    p = _pattern(refs=["E1", "E2"])
    a = derive_independence(p, _registry(("E1", "L1"), ("E2", "L1")), {})
    assert a.distinct_source_lineages == 1
    assert a.independence_status != "CONFIRMED"


def test_two_verified_distinct_lineages_support_exploration():
    p = _pattern(refs=["E1", "E2", "E3"])
    a = derive_independence(p, _registry(("E1", "L1"), ("E2", "L2"), ("E3", "L3")), {})
    assert a.verified_distinct_lineage_count == 3
    assert a.independence_status == "CONFIRMED"
    assert a.unknown_lineage_count == 0


def test_unknown_lineage_does_not_count_favorably():
    p = _pattern(refs=["E1", "E2"])
    reg = _registry(("E1", "L1"))
    reg.register(EvidenceRecord(record_id="E2", kind="AGENT_CLAIM",
                                claim="no lineage", source_lineage="", seq=1))
    a = derive_independence(p, reg, {})
    assert a.unknown_lineage_count >= 1
    assert a.independence_status != "CONFIRMED"


def _pattern(refs):
    from engine.domain import UnresolvedPatternRecord
    return UnresolvedPatternRecord.from_fixture({
        "pattern_id": "UP", "domain": "FX", "observations": ["OBS_A"],
        "conditions": ["c"], "data_quality_passed": True,
        "known_family_fit_attempts": [], "residual_behavior": "r",
        "independence_evidence_refs": refs, "falsifiers": [], "what_remains_unexplained": "x",
        "evidence_lineages": len(refs)})


# =========================================================================== #
# G5R-02 — cluster membership must be evidence-bound
# =========================================================================== #
def test_duplicate_pattern_same_evidence_dedupes():
    """Two pattern records referencing the SAME underlying observation cannot
    inflate the cluster."""
    from engine.g5r import cluster_verified_observation_paths
    p1 = _pattern(refs=["E1", "E2"])
    p2 = _pattern(refs=["E1", "E2"])
    paths = cluster_verified_observation_paths([p1, p2], _registry(("E1", "L1"), ("E2", "L2")))
    assert len(paths) == 2


def test_same_signature_distinct_evidence_counts_separately():
    from engine.g5r import cluster_verified_observation_paths
    p1 = _pattern(refs=["E1"])
    p2 = _pattern(refs=["E2"])
    paths = cluster_verified_observation_paths([p1, p2], _registry(("E1", "L1"), ("E2", "L2")))
    assert len(paths) == 2


def test_similarity_does_not_imply_independence():
    """Cluster grouping by similarity never upgrades per-pattern independence."""
    from engine.g5r import cluster_verified_observation_paths
    p1 = _pattern(refs=["E1"])
    p2 = _pattern(refs=["E1"])      # same evidence
    paths = cluster_verified_observation_paths([p1, p2], _registry(("E1", "L1")))
    assert len(paths) == 1
    # the runner must not report more independent observations than verified paths
    raw = json.loads((G5_DIRS["S15"] / "unresolved_patterns.json").read_text(encoding="utf-8"))
    dup = [dict(raw[0]), dict(raw[0])]
    pack = G5ScenarioPack(scenario_id="S15", unresolved_patterns=dup, evidence=raw_evidence()).decision_grade()
    res = run_s15(pack, _policy())
    assert res.artifacts["cluster"]["independent_observations"] == 3  # IND_1..3 deduped


def raw_evidence():
    return json.loads((G5_DIRS["S15"] / "evidence.json").read_text(encoding="utf-8"))


# =========================================================================== #
# G5R-03 — mechanism admission follows the governed disposition
# =========================================================================== #
def _card():
    from engine.domain import MechanismCard
    return MechanismCard.from_fixture({
        "mechanism_id": "MECH_X", "proposed_mechanism": "m", "observable_inputs": ["o"],
        "constraints": ["c"], "state_transition_hypothesis": "h",
        "realization_conditions": ["r"], "failure_conditions": ["f"], "domain": "FX",
        "evidence_refs": ["IND_1", "IND_2", "IND_3"],
        "alternative_explanations": ["a"], "falsifiers": ["x"]})


def test_qualified_pattern_can_admit_mechanism():
    dec = decide_mechanism_admission(_card(), {"MECH_X": "ONTOLOGY_EXPLORATION_CANDIDATE"})
    assert dec.admission == "ADMITTED_MECHANISM_FOR_EXPERIMENT"


def test_data_quality_failed_pattern_not_admitted_to_mechanism():
    dec = decide_mechanism_admission(_card(), {"MECH_X": "UNRESOLVED_PATTERN"})
    assert dec.admission == "PROPOSED_MECHANISM"
    # runner-level: quality failed -> card present in fixture stays PROPOSED
    raw = json.loads((G5_DIRS["S15"] / "unresolved_patterns.json").read_text(encoding="utf-8"))
    bad = dict(raw[0]); bad["data_quality_passed"] = False
    pack = G5ScenarioPack(scenario_id="S15", unresolved_patterns=[bad],
                          mechanism_cards=json.loads((G5_DIRS["S15"] / "mechanism_cards.json").read_text(encoding="utf-8")),
                          experiment_protocols=json.loads((G5_DIRS["S15"] / "protocols.json").read_text(encoding="utf-8")),
                          evidence=raw_evidence()).decision_grade()
    res = run_s15(pack, _policy())
    assert res.artifacts["mechanism"]["mechanism_admission"] == "PROPOSED_MECHANISM"
    assert res.artifacts["mechanism"]["frozen_protocol"] is None


def test_single_lineage_pattern_not_admitted():
    raw = json.loads((G5_DIRS["S15"] / "unresolved_patterns.json").read_text(encoding="utf-8"))
    one = dict(raw[0]); one["independence_evidence_refs"] = ["IND_1"]
    pack = G5ScenarioPack(scenario_id="S15", unresolved_patterns=[one],
                          mechanism_cards=json.loads((G5_DIRS["S15"] / "mechanism_cards.json").read_text(encoding="utf-8")),
                          experiment_protocols=json.loads((G5_DIRS["S15"] / "protocols.json").read_text(encoding="utf-8")),
                          evidence=raw_evidence()).decision_grade()
    res = run_s15(pack, _policy())
    assert res.artifacts["patterns"][0]["disposition"] == "UNRESOLVED_PATTERN"
    assert res.artifacts["mechanism"]["mechanism_admission"] == "PROPOSED_MECHANISM"


def test_data_blocked_pattern_not_admitted():
    raw = json.loads((G5_DIRS["S15"] / "unresolved_patterns.json").read_text(encoding="utf-8"))
    dep = dict(raw[0]); dep["required_sensor"] = "AGGRESSOR_FLOW_STATE"
    pack = G5ScenarioPack(scenario_id="S15", unresolved_patterns=[dep],
                          mechanism_cards=json.loads((G5_DIRS["S15"] / "mechanism_cards.json").read_text(encoding="utf-8")),
                          experiment_protocols=json.loads((G5_DIRS["S15"] / "protocols.json").read_text(encoding="utf-8")),
                          evidence=raw_evidence()).decision_grade()
    res = run_s15(pack, _policy())
    assert res.artifacts["patterns"][0]["disposition"] == "DATA_BLOCKED"
    assert res.artifacts["mechanism"]["mechanism_admission"] == "PROPOSED_MECHANISM"


# =========================================================================== #
# G5R-04/05 — CEREBUS source binding + exact claim atoms
# =========================================================================== #
MANUAL = ROOT.parent / "quant-lab/reports/CEREBUS_v4_Manual_EXTRACTED.txt"


def test_correct_source_binding_passes():
    binding = recompute_source_binding(str(MANUAL), "v4", "Target Metric table (PAGE 4-5)")
    validate_sha256_digest(binding.content_digest)          # exactly 64 hex
    assert len(binding.content_digest) == 64
    assert binding.hash_algorithm == "SHA-256"
    assert binding.content_length == MANUAL.stat().st_size
    assert binding.source_blob_sha == binding.content_digest


def test_wrong_manual_digest_rejected():
    with pytest.raises(ValueError):
        validate_sha256_digest("72ba79d7064404b463dfcf7d937a3a4c")   # 32 chars: not SHA-256


def test_stale_manual_digest_rejected():
    """A stored digest that does not match the recomputed file digest fails
    closed at the runner level (STALE_DIGEST) — the claim is not source-bound."""
    pack = load_g5_pack(G5_DIRS["S16"]).decision_grade()
    claims = copy.deepcopy(pack.doctrine_claims)
    claims[0]["source_fingerprint"] = "1" * 64          # valid length, wrong content
    pack = G5ScenarioPack(**{**pack.__dict__, "doctrine_claims": claims})
    res = run_s16(pack, _policy())
    assert res.artifacts["doctrine_claims"][0]["source_binding_status"] == "STALE_DIGEST"


def test_source_file_unchanged():
    """The manual source file is read-only during G5R — bytes identical."""
    before = MANUAL.read_bytes()
    binding = recompute_source_binding(str(MANUAL), "v4", "tbl")
    after = MANUAL.read_bytes()
    assert before == after
    # and matches the digest the fixture claims (the true file digest)
    assert binding.content_digest == "72ba79d7064404b463dfcf7d937a3a4c03565f6bad12f0ffa4fb8f6d5f011233"


def test_exact_claim_atoms_preserve_section_boundaries():
    """G5R-05: the 'exact' claim is the bounded Target Metric table; pre-session
    conditions / tier sizing / P90 thresholds are SEPARATELY bound fragments,
    never paraphrased into one composite quote."""
    res = run_s16(load_g5_pack(G5_DIRS["S16"]).decision_grade(), _policy()).artifacts
    claim = res["doctrine_claims"][0]
    atoms = {a["atom_id"]: a for a in claim["claim_atoms"]}
    target = atoms[f"{claim['claim_id']}:TARGET_METRIC"]
    assert target["claim_kind"] == "TARGET_METRIC_ROW"
    assert "win_rate_band" in json.loads(target["exact_fragment"])
    # the composite paraphrase is GONE: no token for external sections inside
    # the exact representation
    assert "Conditions:" not in claim["exact_claim_representation"]
    assert any(a["claim_kind"] == "APPLICABILITY_CONDITION" for a in claim["claim_atoms"])
    assert all(a["fragment_digest"] for a in claim["claim_atoms"])


# =========================================================================== #
# G5R-06 — reproduction quality must be DERIVED
# =========================================================================== #
def _claim():
    from engine.domain import DoctrineClaimRecord
    return DoctrineClaimRecord.from_fixture(json.loads(
        (G5_DIRS["S16"] / "doctrine_claims.json").read_text(encoding="utf-8"))[0])


def _proto(**over):
    base = {"protocol_id": "RP", "claim_ref": "CEREBUS_V4_P90_TARGET_METRICS",
            "dataset_lineage": "fx", "implementation_version": "v",
            "session_window": "00:00-08:00 UTC (Asia)",
            "tier_constraints": ["TIER_1_100%", "TIER_2_75%", "TIER_3_50%", "NO_GO_>45p"],
            "feature_definitions": ["f"], "pit_rules": ["availability_before_decision"],
            "sample_definition": "s", "metric_definition": "filtered_win_rate",
            "execution_assumptions": ["2bp"], "evaluation_criterion": "c",
            "independence_lineage": "L", "falsification_criterion": "fc",
            "frozen_before_result": True}
    base.update(over)
    return ReproductionProtocol.from_fixture(base)


def test_clean_exact_protocol_passes():
    qa = derive_reproduction_quality(_proto(), _claim(), [])
    assert qa.quality == "CLEAN"


def test_wrong_session_detected_without_declared_deviation():
    """CASE B: known_deviations=[] cannot launder a structured session
    mismatch => REPRODUCTION_REJECTED."""
    qa = derive_reproduction_quality(_proto(session_window="13:00-17:00 UTC (EU)"),
                                     _claim(), [])
    assert qa.quality == "FLAWED"
    assert "wrong_session_window" in qa.deviations
    # runner-level
    repros = json.loads((G5_DIRS["S16"] / "reproductions.json").read_text(encoding="utf-8"))
    clean = copy.deepcopy([r for r in repros if r["reproduction_id"] == "REPRO_CLEAN_1"][0])
    clean["protocol"]["session_window"] = "09:00-12:00 UTC (EU)"
    clean["known_deviations"] = []
    pack = G5ScenarioPack(scenario_id="S16",
                          doctrine_claims=json.loads((G5_DIRS["S16"] / "doctrine_claims.json").read_text(encoding="utf-8")),
                          reproductions=[clean]).decision_grade()
    res = run_s16(pack, _policy())
    assert res.artifacts["reproduction_results"][0]["status"] == "REPRODUCTION_REJECTED"


def test_wrong_tier_detected():
    qa = derive_reproduction_quality(_proto(tier_constraints=["TIER_1_100%"]), _claim(), [])
    assert qa.quality == "FLAWED"
    assert qa.tier_match is False


def test_PIT_failure_detected():
    qa = derive_reproduction_quality(_proto(pit_rules=[]), _claim(), [])
    assert qa.quality == "FLAWED"
    assert qa.pit_clean is False


def test_missing_protocol_fingerprint_rejected():
    p = _proto()
    object.__setattr__(p, "protocol_fingerprint", "")
    qa = derive_reproduction_quality(p, _claim(), [])
    assert qa.quality == "FLAWED"
    assert qa.protocol_fingerprint_present is False


def test_post_result_protocol_change_changes_fingerprint_and_invalidates_comparison():
    p1 = _proto()
    p2 = _proto(session_window="13:00-17:00 UTC (EU)")
    assert p1.protocol_fingerprint != p2.protocol_fingerprint
    qa = derive_reproduction_quality(p2, _claim(), [], claim_fingerprint=p1.protocol_fingerprint)
    assert qa.quality == "FLAWED"
    assert qa.protocol_fingerprint_valid is False


# =========================================================================== #
# G5R-07 — contradiction from measured result
# =========================================================================== #
def test_fixture_string_contradicts_cannot_override_measured_result():
    """CASE C: result='CONTRADICTS_CLAIM' with measured result INSIDE the band
    => no contradiction."""
    obs = ObservedResult(metric="filtered_win_rate", estimate=0.87,
                         uncertainty_interval=(0.86, 0.88), sample_size=2400)
    c = compare_measured_result(obs, [0.85, 0.90])
    assert c.verdict == "SUPPORTS_CLAIM"


def test_numeric_result_inside_claim_band_not_contradiction():
    obs = ObservedResult(metric="filtered_win_rate", estimate=0.88,
                         uncertainty_interval=(0.87, 0.89), sample_size=2400)
    assert compare_measured_result(obs, [0.85, 0.90]).verdict == "SUPPORTS_CLAIM"


def test_numeric_result_materially_outside_claim_band_can_contradict():
    obs = ObservedResult(metric="filtered_win_rate", estimate=0.72,
                         uncertainty_interval=(0.68, 0.76), sample_size=2400)
    c = compare_measured_result(obs, [0.85, 0.90])
    assert c.verdict == "CONTRADICTS_CLAIM"


def test_uncertainty_overlap_can_return_inconclusive():
    obs = ObservedResult(metric="filtered_win_rate", estimate=0.83,
                         uncertainty_interval=(0.78, 0.88), sample_size=2400)
    assert compare_measured_result(obs, [0.85, 0.90]).verdict == "INCONCLUSIVE"


# =========================================================================== #
# G5R-08 — manual authority and reproduction quality remain separate
# =========================================================================== #
def test_claim_never_rewritten_by_reproduction_or_comparison():
    res = run_s16(load_g5_pack(G5_DIRS["S16"]).decision_grade(), _policy()).artifacts
    claim = res["doctrine_claims"][0]
    assert claim["current_status"] == "AUTHORITATIVE"
    assert res["manual_modified"] is False
    assert res["manual_claim_rewritten"] is False
    assert res["contradictions"]        # measured contradiction opened
    assert claim["numeric_parameters"]["win_rate_band"] == [0.85, 0.90]  # untouched


# =========================================================================== #
# G5R-09 — amendment ratification via AuthorityState
# =========================================================================== #
def _proposal():
    return DoctrineAmendmentProposal.from_fixture(json.loads(
        (G5_DIRS["S16"] / "amendment.json").read_text(encoding="utf-8")))


def _authority(*levels):
    from engine.authority import AuthorityState
    a = AuthorityState()
    for actor, level in levels:
        a.seed_level(actor, level)
    return a


def test_fixture_ratified_true_without_authority_rejected():
    """CASE D: amendment ratified=true with no governed ratification record =>
    the manual remains unamended (the runner only honors governed ratification)."""
    raw = json.loads((G5_DIRS["S16"] / "amendment.json").read_text(encoding="utf-8"))
    raw["ratified"] = True
    pack = load_g5_pack(G5_DIRS["S16"]).decision_grade()
    pack = G5ScenarioPack(**{**pack.__dict__, "amendment_proposal": raw,
                             "amendment_ratifications": []})
    res = run_s16(pack, _policy())
    assert res.artifacts["amendment_ratified"] is False
    assert res.artifacts["amendment_operator_required"] is True
    assert res.artifacts["manual_modified"] is False


def test_worker_cannot_ratify_doctrine_amendment():
    authority = _authority(("WORKER_1", "WORKER"))
    with pytest.raises(Exception):
        govern_amendment_ratification(authority, _proposal(), "WORKER_1",
                                      "basis", "scope", "CLAIM")


def test_operator_can_ratify_existing_proposal():
    authority = _authority(("OPERATOR_ACTOR", "OPERATOR"))
    rec = govern_amendment_ratification(authority, _proposal(), "OPERATOR_ACTOR",
                                        "provisional test contract", _proposal().scope,
                                        _proposal().claim_id, seq=0)
    assert rec.authority_level == "OPERATOR"
    assert rec.proposal_id == _proposal().proposal_id
    assert rec.manual_claim_id == _proposal().claim_id


def test_ratification_without_proposal_rejected():
    authority = _authority(("OPERATOR_ACTOR", "OPERATOR"))
    stale = DoctrineAmendmentProposal(proposal_id="NOPE", claim_id="C", scope="s",
                                      requested_amendment="x", status="RATIFIED")
    with pytest.raises(Exception):
        govern_amendment_ratification(authority, stale, "OPERATOR_ACTOR",
                                      "basis", "scope", "C")


def test_ratification_does_not_rewrite_source_file():
    before = MANUAL.read_bytes()
    authority = _authority(("OPERATOR_ACTOR", "OPERATOR"))
    govern_amendment_ratification(authority, _proposal(), "OPERATOR_ACTOR",
                                  "basis", _proposal().scope, _proposal().claim_id)
    assert MANUAL.read_bytes() == before


# =========================================================================== #
# G5R-10 — S17 semantics key = provider + metric
# =========================================================================== #
def test_same_provider_multiple_metrics_resolve_correct_contract():
    """A provider may publish multiple metrics with different semantics; the
    diagnosis must resolve the (provider, metric) contract, never provider
    alone."""
    from engine.domain import diagnose_provider_disagreement
    obs_a = _obs("O1", provider="P", metric="M", adapter_version="v1")
    obs_b = _obs("O2", provider="P2", metric="M", units="USD_NOTIONAL",
                 canonical_units="USD_NOTIONAL", normalized_value=None)
    sem_a = _sem("P", "M", adapter_version="v1")
    sem_a2 = _sem("P", "OTHER_METRIC", adapter_version="v9")
    sem_b = _sem("P2", "M", native_units="USD_NOTIONAL", canonical_units="USD_NOTIONAL",
                 adapter_version="v1", contract_type="PERP_LINEAR")
    # contract for metric M found even though provider P also has OTHER_METRIC
    # (and that other contract must NOT be used)
    diag = diagnose_provider_disagreement(obs_a, obs_b, sem_a, sem_b)
    assert diag.cause in ("NORMALIZATION_MISSING", "NORMALIZATION_MISMATCH")
    assert "OTHER_METRIC" not in [s.detail for s in diag.steps]


def test_missing_metric_semantics_fails_closed():
    """A provider+metric with NO registered semantic contract fails closed
    (SOURCE_DIAGNOSTIC_REQUIRED / DATA_INSUFFICIENT), never silently compared.

    G5R-10 runner contract: a missing contract produces a fail-closed
    DIAGNOSTIC per pair — cause SEMANTIC_CONTRACT_MISSING, terminal
    DATA_INSUFFICIENT, disposition SOURCE_DIAGNOSTIC_REQUIRED — and no pair
    ever reaches the disagreement surface or is averaged. (The original draft
    asserted `diagnoses == []`, which would silently SKIP uncontracted pairs;
    a silent skip is exactly the G5R-10 defect, so the runner-level assertion
    now asserts the fail-closed diagnostics instead.)"""
    from engine.domain import diagnose_provider_disagreement
    obs_a = _obs("O1", provider="P", metric="M", adapter_version="v1")
    obs_b = _obs("O2", provider="P2", metric="M", adapter_version="v1")
    diag = diagnose_provider_disagreement(obs_a, obs_b, _sem("P", "M"), None)
    assert diag.cause == "SEMANTIC_CONTRACT_MISSING"
    assert diag.terminal == "DATA_INSUFFICIENT"
    # runner-level: no contract -> EVERY pair fails closed at the semantics
    # layer; none reaches a disagreement verdict, none is averaged away
    pack = load_g5_pack(G5_DIRS["S17"]).decision_grade()
    pack = G5ScenarioPack(**{**pack.__dict__, "provider_semantics": []})
    res = run_g5_scenario(pack, _policy())
    diagnoses = res.artifacts["diagnoses"]
    assert diagnoses                                  # fail-closed diagnostics emitted
    assert all(d["cause"] == "SEMANTIC_CONTRACT_MISSING" for d in diagnoses)
    assert all(d["terminal"] == "DATA_INSUFFICIENT" for d in diagnoses)
    assert all(d["disposition"] == "SOURCE_DIAGNOSTIC_REQUIRED" for d in diagnoses)
    assert all(d["averaged_to_consensus"] is False for d in diagnoses)


# =========================================================================== #
# G5R-11 — observation adapter version must match semantic contract
# =========================================================================== #
def test_wrong_observation_adapter_version_detected():
    """CASE E: observation adapter=v2, semantic contract adapter=v1 =>
    ADAPTER_MISMATCH before normalization."""
    from engine.domain import diagnose_provider_disagreement
    obs_a = _obs("O1", provider="P", metric="M", adapter_version="v2")
    obs_b = _obs("O2", provider="P2", metric="M", adapter_version="v1")
    diag = diagnose_provider_disagreement(obs_a, obs_b, _sem("P", "M", adapter_version="v1"),
                                          _sem("P2", "M", adapter_version="v1"))
    assert diag.cause == "ADAPTER_MISMATCH"
    assert diag.terminal == "REPAIRABLE_SOURCE_MISMATCH"


def test_blank_observation_adapter_version_detected():
    from engine.domain import diagnose_provider_disagreement
    obs_a = _obs("O1", provider="P", metric="M", adapter_version="")
    obs_b = _obs("O2", provider="P2", metric="M", adapter_version="v1")
    diag = diagnose_provider_disagreement(obs_a, obs_b, _sem("P", "M", adapter_version="v1"),
                                          _sem("P2", "M", adapter_version="v1"))
    assert diag.cause == "ADAPTER_MISMATCH"


def test_matching_adapter_passes():
    from engine.domain import diagnose_provider_disagreement
    obs_a = _obs("O1", provider="P", metric="M", adapter_version="v1")
    obs_b = _obs("O2", provider="P2", metric="M", adapter_version="v1")
    diag = diagnose_provider_disagreement(obs_a, obs_b, _sem("P", "M", adapter_version="v1"),
                                          _sem("P2", "M", adapter_version="v1"))
    assert diag.cause not in ("ADAPTER_MISMATCH", "SEMANTIC_CONTRACT_MISSING")


# =========================================================================== #
# G5R-12 — missing normalized value stays UNKNOWN
# =========================================================================== #
def test_missing_normalized_value_not_zero():
    """CASE F: normalized_value omitted => DATA_INSUFFICIENT / normalization
    missing, never zero."""
    from engine.domain import diagnose_provider_disagreement
    obs_a = _obs("O1", provider="P", metric="M", normalized_value=None)
    obs_b = _obs("O2", provider="P2", metric="M", normalized_value=None)
    diag = diagnose_provider_disagreement(obs_a, obs_b, _sem("P", "M"), _sem("P2", "M"))
    assert diag.cause == "NORMALIZATION_MISSING"
    assert diag.terminal == "DATA_INSUFFICIENT"
    assert obs_a.normalized_value is None   # never coerced to 0.0
    assert obs_a.has_normalized_value is False


def test_missing_normalized_value_blocks_disagreement_comparison():
    """A missing normalized value must block the valuation, not become a real
    zero that could manufacture a genuine disagreement."""
    from engine.domain import diagnose_provider_disagreement
    obs_a = _obs("O1", provider="P", metric="M", normalized_value=None)
    obs_b = _obs("O2", provider="P2", metric="M", normalized_value=0.0)
    diag = diagnose_provider_disagreement(obs_a, obs_b, _sem("P", "M"), _sem("P2", "M"))
    assert diag.terminal == "DATA_INSUFFICIENT"


# =========================================================================== #
# G5R-13 — S17 time / quality / contract semantics
# =========================================================================== #
def test_provider_expected_window_mismatch_detected():
    from engine.domain import diagnose_provider_disagreement
    obs_a = _obs("O1", provider="P", metric="M", time_window="5m")
    obs_b = _obs("O2", provider="P2", metric="M", time_window="15m")
    diag = diagnose_provider_disagreement(obs_a, obs_b, _sem("P", "M", time_window="5m"),
                                          _sem("P2", "M", time_window="5m"))
    assert diag.terminal == "REPAIRABLE_SOURCE_MISMATCH"
    assert diag.cause in ("TIME_WINDOW_MISMATCH", "INSTRUMENT_MISMATCH")


def test_provider_quality_contract_failure_detected():
    from engine.domain import diagnose_provider_disagreement
    obs_a = _obs("O1", provider="P", metric="M", quality_state="OK")
    obs_b = _obs("O2", provider="P2", metric="M", quality_state="STALE")
    diag = diagnose_provider_disagreement(obs_a, obs_b, _sem("P", "M", quality_state="OK"),
                                          _sem("P2", "M", quality_state="OK"))
    assert diag.terminal == "REPAIRABLE_SOURCE_MISMATCH"
    assert diag.cause == "QUALITY_FAILURE"


def test_spot_vs_perp_contract_type_mismatch_detected():
    from engine.domain import diagnose_provider_disagreement
    obs_a = _obs("O1", provider="P", metric="M", contract_type="PERP_LINEAR")
    obs_b = _obs("O2", provider="P2", metric="M", contract_type="SPOT")
    diag = diagnose_provider_disagreement(obs_a, obs_b, _sem("P", "M", contract_type="PERP_LINEAR"),
                                          _sem("P2", "M", contract_type="SPOT"))
    assert diag.cause == "CONTRACT_TYPE_MISMATCH"
    assert diag.terminal == "REPAIRABLE_SOURCE_MISMATCH"


# =========================================================================== #
# G5R-14 — NO_DISAGREEMENT must not terminate as genuine
# =========================================================================== #
def test_equal_clean_normalized_values_no_disagreement():
    from engine.domain import diagnose_provider_disagreement
    obs_a = _obs("O1", provider="P", metric="M", normalized_value=340.0)
    obs_b = _obs("O2", provider="P2", metric="M", normalized_value=340.0)
    diag = diagnose_provider_disagreement(obs_a, obs_b, _sem("P", "M"), _sem("P2", "M"))
    assert diag.cause == "NO_DISAGREEMENT"
    assert diag.terminal == "NO_DISAGREEMENT"
    assert diag.terminal != "GENUINE_SOURCE_DISAGREEMENT"


# =========================================================================== #
# G5R-15 — explicit tolerance contract
# =========================================================================== #
def test_tiny_rounding_difference_not_material():
    from engine.g5r import disagreement_is_material
    tol = DisagreementToleranceContract(contract_id="T", absolute_tolerance=0.001)
    assert disagreement_is_material(340.0, 340.0001, tol) is False


def test_material_difference_preserved():
    from engine.g5r import disagreement_is_material
    tol = DisagreementToleranceContract(contract_id="T", absolute_tolerance=0.001)
    assert disagreement_is_material(340.0, 212.0, tol) is True


def test_relative_tolerance_contract():
    from engine.g5r import disagreement_is_material
    tol = DisagreementToleranceContract(contract_id="T", relative_tolerance=0.01)
    assert disagreement_is_material(100.0, 100.5, tol) is False
    assert disagreement_is_material(100.0, 105.0, tol) is True


def test_tolerance_wired_into_diagnosis():
    from engine.domain import diagnose_provider_disagreement
    obs_a = _obs("O1", provider="P", metric="M", normalized_value=340.0)
    obs_b = _obs("O2", provider="P2", metric="M", normalized_value=340.5)
    tol = DisagreementToleranceContract(contract_id="T", metric="M", units="CONTRACTS",
                                        absolute_tolerance=1.0)
    diag = diagnose_provider_disagreement(obs_a, obs_b, _sem("P", "M"), _sem("P2", "M"),
                                          tolerance=tol)
    assert diag.cause == "NO_DISAGREEMENT"
    assert diag.terminal == "NO_DISAGREEMENT"


# =========================================================================== #
# G5R-16/17 — full-vector sensor adequacy with provenance
# =========================================================================== #
def test_available_but_unverified_not_adequate():
    """CASE G: status=AVAILABLE + correct history + verified=false => NOT
    adequate (AVAILABLE != ADEQUATE)."""
    rec = _avail(verified=False)
    assert rec.adequate_history(_req()) is False


def test_available_wrong_resolution_not_adequate():
    """CASE H: AVAILABLE + VERIFIED but 5m while requirement is 1m =>
    DATA_BLOCKED."""
    rec = _avail(resolution="5m")
    assert rec.adequate_history(_req()) is False
    res = run_g5_scenario(load_g5_pack(G5_DIRS["S18"]).decision_grade(), _policy())
    # requirement-level check via the runner on a single adequate-ish record
    pack = G5ScenarioPack(
        scenario_id="S18",
        sensor_requirements=[_req().to_dict()],
        data_availability=[_avail(resolution="5m").to_dict()]).decision_grade()
    r2 = run_g5_scenario(pack, _policy())
    assert r2.artifacts["blocked_claims"][0]["disposition"] == "DATA_BLOCKED"


def test_available_wrong_instrument_not_adequate():
    rec = _avail(instrument_coverage=["OTHER"])
    assert rec.adequate_history(_req()) is False


def test_available_wrong_time_semantics_not_adequate():
    rec = _avail(time_semantics="RECEIVE")
    assert rec.adequate_history(_req()) is False


def test_available_insufficient_history_not_adequate():
    rec = _avail(history_depth="1m")
    assert rec.adequate_history(_req()) is False


def test_full_requirement_match_adequate():
    assert _avail().adequate_history(_req()) is True


def test_unknown_provenance_not_adequate():
    """G5R-17: status=AVAILABLE from an unverified arbitrary caller with no
    certification => UNKNOWN provenance => not adequate."""
    rec = _avail(certification="")
    assert rec.adequate_history(_req()) is False
    rec2 = _avail(certification="UNKNOWN")
    assert rec2.adequate_history(_req()) is False


def test_structured_history_not_naive_string_equality():
    from engine.domain import HistorySpan
    assert HistorySpan.from_string("12m").satisfies(HistorySpan.from_string("12m"))
    assert not HistorySpan.from_string("1m").satisfies(HistorySpan.from_string("12m"))
    # '2021-06-01..' covers far more than 12m against the fixed anchor
    assert HistorySpan.from_string("2021-06-01..").satisfies(HistorySpan.from_string("12m"))


# =========================================================================== #
# G5R-18 — sensor arrival is an EVIDENCED capability-state change
# =========================================================================== #
def test_boolean_alone_cannot_make_sensor_verified():
    """sensor_available_later=True flips the status but NOT verification or
    certification; adequacy stays off and the override is reported as
    NON_AUTHORITATIVE."""
    pack = load_g5_pack(G5_DIRS["S18"]).decision_grade()
    res = run_s18(pack, _policy(), sensor_available_later=True)
    changes = res.artifacts["sensor_capability_changes"]
    assert changes
    assert all(not c["certification"] for c in changes)
    assert res.artifacts["boolean_override_non_authoritative"] is True
    assert all(b["adequate_history"] is False for b in res.artifacts["blocked_claims"])


def test_registered_sensor_change_can_reopen():
    """A registered, evidence-backed capability change (with certification)
    can make the requirement adequate and reopen the claim."""
    pack = load_g5_pack(G5_DIRS["S18"]).decision_grade()
    change = {"change_id": "CHG_LF_1", "observable": "AGGRESSOR_FLOW_STATE",
              "old_state": "UNAVAILABLE", "new_state": "AVAILABLE",
              "source": "CRYPTO_SENSOR_FABRIC", "evidence_refs": ["EV_S18_SENSOR"],
              "certification": "CRYPTO_SENSOR_FABRIC_CERTIFICATION",
              "effective_epoch": "E18_LATER", "history_coverage": "12m"}
    pack = G5ScenarioPack(**{**pack.__dict__, "sensor_capability_changes": [change]})
    res = run_s18(pack, _policy(), sensor_available_later=True)
    blocked = {b["required_observable"]: b for b in res.artifacts["blocked_claims"]}
    assert blocked["AGGRESSOR_FLOW_STATE"]["adequate_history"] is True
    assert all(a["reopen_outcome"] == "REOPEN_CANDIDATE" for a in res.artifacts["activation"])


def test_sensor_arrival_does_not_retroactively_validate_history():
    """A sensor that arrives later cannot retroactively satisfy a longer
    history requirement."""
    req = _req(history_depth="36m")
    rec = _avail(history_depth="2026-06-01..")
    assert rec.adequate_history(req) is False


# =========================================================================== #
# G5R-19 — SearchDemand acceptable source semantics
# =========================================================================== #
def test_search_demand_separates_instruments_from_source_classes():
    res = run_g5_scenario(load_g5_pack(G5_DIRS["S18"]).decision_grade(), _policy()).artifacts
    d = res["search_demands"][0]
    assert d["required_instruments"] == ["BTC_USDT_PERP", "ETH_USDT_PERP"]
    assert d["acceptable_source_classes"] == ["CRYPTO_SENSOR_FABRIC"]
    for inst in d["required_instruments"]:
        assert inst not in d["acceptable_source_classes"]   # instrument != provider


# =========================================================================== #
# G5R-20 — S19 structural map validates ALL required axes
# =========================================================================== #
def _s19_map():
    return TransferInvariantMap.from_fixture(json.loads(
        (G5_DIRS["S19"] / "transfer_hypotheses.json").read_text(encoding="utf-8"))[0]["transfer_map"])


def test_complete_map_sound():
    assert validate_transfer_map(_s19_map()).map_sound is True


def test_missing_units_scale_not_sound():
    m = _s19_map()
    m = TransferInvariantMap(**{**m.__dict__, "units_scales": ()})
    v = validate_transfer_map(m)
    assert v.map_sound is False and "units_scales" in v.missing_axes


def test_missing_state_semantics_not_sound():
    m = TransferInvariantMap(**{**_s19_map().__dict__, "state_semantics": ()})
    assert validate_transfer_map(m).map_sound is False


def test_missing_market_structure_assumption_not_sound():
    m = TransferInvariantMap(**{**_s19_map().__dict__, "market_structure_assumptions": ()})
    assert validate_transfer_map(m).map_sound is False


def test_missing_falsifiers_not_sound():
    m = TransferInvariantMap(**{**_s19_map().__dict__, "falsifiers": ()})
    assert validate_transfer_map(m).map_sound is False


def test_missing_required_sensor_definition_not_sound():
    m = TransferInvariantMap(**{**_s19_map().__dict__, "required_sensors": ()})
    assert validate_transfer_map(m).map_sound is False


def test_incomplete_transfer_map_runner_analogy():
    """CASE J: source/target observables + invariants present but units / state
    semantics / falsifiers absent => map not structurally sound (ANALOGY)."""
    raw = json.loads((G5_DIRS["S19"] / "transfer_hypotheses.json").read_text(encoding="utf-8"))[0]
    raw = copy.deepcopy(raw)
    raw["transfer_map"]["units_scales"] = []
    raw["transfer_map"]["state_semantics"] = []
    raw["transfer_map"]["falsifiers"] = []
    pack = G5ScenarioPack(scenario_id="S19", transfer_hypotheses=[raw]).decision_grade()
    res = run_s19(pack, _policy())
    assert res.artifacts["transfers"][0]["transfer_map_validation"]["map_sound"] is False
    assert res.artifacts["transfers"][0]["disposition"] == "ANALOGY_ONLY"


# =========================================================================== #
# G5R-21 — target protocol must be a real frozen registered object
# =========================================================================== #
def test_protocol_frozen_boolean_without_protocol_ref_rejected():
    """CASE I: protocol_frozen=true with no registered target protocol ref =>
    cannot authorize DOMAIN_VALIDATION_REQUIRED."""
    pack = _s19_adequate_pack()
    raw = json.loads((G5_DIRS["S19"] / "transfer_hypotheses.json").read_text(encoding="utf-8"))
    raw[0]["frozen_target_protocol_ref"] = ""
    pack = G5ScenarioPack(**{**pack.__dict__, "transfer_hypotheses": raw})
    res = run_s19(pack, _policy(), protocol_frozen=True)
    item = res.artifacts["transfers"][0]
    assert item["disposition"] != "DOMAIN_VALIDATION_REQUIRED"
    assert item["protocol_resolution"]["resolved"] is False
    assert item["disposition"] == "TRANSFER_HYPOTHESIS_ONLY"


def test_missing_protocol_ref_holds_hypothesis():
    pack = _s19_adequate_pack()
    raw = json.loads((G5_DIRS["S19"] / "transfer_hypotheses.json").read_text(encoding="utf-8"))
    raw[0]["frozen_target_protocol_ref"] = ""
    pack = G5ScenarioPack(**{**pack.__dict__, "transfer_hypotheses": raw})
    res = run_s19(pack, _policy())
    assert res.artifacts["transfers"][0]["disposition"] == "TRANSFER_HYPOTHESIS_ONLY"


def test_wrong_target_domain_protocol_rejected():
    pack = _s19_adequate_pack()
    protos = json.loads((G5_DIRS["S19"] / "experiment_protocols.json").read_text(encoding="utf-8"))
    protos[0]["target_domain"] = "CRYPTO"       # hypothesis targets FX
    pack = G5ScenarioPack(**{**pack.__dict__, "experiment_protocols": protos})
    res = run_s19(pack, _policy(), protocol_frozen=True)
    item = res.artifacts["transfers"][0]
    assert item["protocol_resolution"]["target_domain_ok"] is False
    assert item["disposition"] != "DOMAIN_VALIDATION_REQUIRED"


def test_valid_registered_frozen_protocol_allows_domain_validation_required():
    pack = _s19_adequate_pack()
    res = run_s19(pack, _policy(), protocol_frozen=True)
    item = res.artifacts["transfers"][0]
    assert item["protocol_resolution"]["resolved"] is True
    assert item["protocol_resolution"]["fingerprint_valid"] is True
    assert item["disposition"] == "DOMAIN_VALIDATION_REQUIRED"


# =========================================================================== #
# G5R-22 — target data passes sensor adequacy, not a boolean
# =========================================================================== #
def test_boolean_override_cannot_bypass_target_sensor_adequacy():
    pack = load_g5_pack(G5_DIRS["S19"]).decision_grade()
    res = run_s19(pack, _policy(), target_data_available=True, protocol_frozen=True)
    item = res.artifacts["transfers"][0]
    assert item["disposition"] == "DATA_BLOCKED"
    assert item["target_data_override"] == "NON_AUTHORITATIVE_TEST_CONVENIENCE"
    assert item["target_data_available"] is False


# =========================================================================== #
# G5R-23 — source evidence refs must resolve
# =========================================================================== #
def test_phantom_source_evidence_ref_rejected():
    pack = _s19_adequate_pack()
    raw = json.loads((G5_DIRS["S19"] / "transfer_hypotheses.json").read_text(encoding="utf-8"))
    raw[0]["source_evidence_refs"] = ["FAM_A_EXTREME_NEGATIVE_BASIS_DISLOCATION", "PHANTOM_99"]
    pack = G5ScenarioPack(**{**pack.__dict__, "transfer_hypotheses": raw})
    res = run_s19(pack, _policy(), protocol_frozen=True)
    item = res.artifacts["transfers"][0]
    assert item["source_evidence_refs_resolved"] is False
    assert item["source_evidence_refs_unknown"] == ["PHANTOM_99"]
    assert item["disposition"] != "DOMAIN_VALIDATION_REQUIRED"


def test_registered_crypto_evidence_preserved():
    pack = load_g5_pack(G5_DIRS["S19"]).decision_grade()
    res = run_s19(pack, _policy())
    item = res.artifacts["transfers"][0]
    assert item["source_evidence_refs_resolved"] is True
    assert item["source_domain"] == "CRYPTO"


def test_crypto_evidence_cannot_satisfy_target_validation():
    """Strong crypto evidence stays crypto; it never becomes FX validation."""
    pack = _s19_adequate_pack()
    res = run_s19(pack, _policy(), protocol_frozen=True)
    item = res.artifacts["transfers"][0]
    assert item["source_evidence_refs_resolved"] is True
    assert item["disposition"] == "DOMAIN_VALIDATION_REQUIRED"   # needs target-domain program
    assert item["source_validation_as_target_validation"] is False
    assert item["disposition"] != "DOMAIN_VALIDATED"             # crypto refs never validate FX


# =========================================================================== #
# G5R-24 — S14 promotion vocabulary internal consistency
# =========================================================================== #
def test_validation_pass_not_execution_authority():
    gate = B7ValidationGate()
    cand = _clean_candidate()
    result: B7ValidationResult = gate.run(cand)
    assert result.terminal == "VALIDATION_PASS"
    assert "EXECUTION" not in result.terminal


def test_promotion_candidate_not_final_execution():
    pack = load_g5_pack(G5_DIRS["S14"]).decision_grade()
    res = run_g5_scenario(pack, POLICY) if False else None
    # clean control: gates pass -> PROMOTION_CANDIDATE, never execution
    data = json.loads((G5_DIRS["S14"] / "strategies.json").read_text(encoding="utf-8"))[0]
    clean = {"candidate_id": "CAND_CLEAN", "family": "F", "specification_ref": "S",
             "performance": {"sharpe": 1.4, "cumulative_return": 0.8,
                             "max_drawdown": 0.06, "win_rate": 0.58, "sample_years": 3.0},
             "features": [{"feature_id": "FEAT_OK", "observation_time": 100,
                           "availability_time": 100, "decision_time": 200, "pct": 100}],
             "fills": [{"fill_id": "FILL_OK", "signal_time": 500, "fill_time": 505,
                        "spread_state": "NORMAL", "depth_available": 1000, "size": 100,
                        "slippage_bps": 2.0}],
             "data_lineage": "synth", "dataset_ref": "DS", "parameter_count": 2,
             "sample_count": 4000, "holdout_ref": "H", "walk_forward_ref": "W",
             "cost_model_ref": "C"}
    pack2 = G5ScenarioPack(scenario_id="S14", strategies=[clean]).decision_grade()
    item = run_g5_scenario(pack2, _policy()).artifacts["items"][0]
    assert item["promotion_decision"]["decision"] == "PROMOTION_CANDIDATE"
    assert item["promotion_decision"]["validation_terminal"] == "VALIDATION_PASS"
    assert item["promotion_decision"]["execution_authority"] == "NONE"


def test_receipt_has_no_contradictory_status_labels():
    data = json.loads((G5_DIRS["S14"] / "strategies.json").read_text(encoding="utf-8"))[0]
    clean = {"candidate_id": "CAND_CLEAN", "family": "F", "specification_ref": "S",
             "performance": {"sharpe": 1.4, "cumulative_return": 0.8,
                             "max_drawdown": 0.06, "win_rate": 0.58, "sample_years": 3.0},
             "features": [{"feature_id": "FEAT_OK", "observation_time": 100,
                           "availability_time": 100, "decision_time": 200, "pct": 100}],
             "fills": [{"fill_id": "FILL_OK", "signal_time": 500, "fill_time": 505,
                        "spread_state": "NORMAL", "depth_available": 1000, "size": 100,
                        "slippage_bps": 2.0}],
             "data_lineage": "synth", "dataset_ref": "DS", "parameter_count": 2,
             "sample_count": 4000, "holdout_ref": "H", "walk_forward_ref": "W",
             "cost_model_ref": "C"}
    pack = G5ScenarioPack(scenario_id="S14", strategies=[clean]).decision_grade()
    item = run_g5_scenario(pack, _policy()).artifacts["items"][0]
    blob = json.dumps(item)
    assert "\"PROMOTED\"" not in blob          # no final-promotion label on a validation candidate
    assert item["disposition"] == "VALIDATION_REQUIRED"
    assert item["promotion_decision"]["decision"] == "PROMOTION_CANDIDATE"


def _clean_candidate():
    return StrategyCandidate(
        candidate_id="C", family="F", specification_ref="S",
        performance=PerformanceReport(sharpe=1.4, cumulative_return=0.8,
                                      max_drawdown=0.06, win_rate=0.58),
        features=(FeatureUse("FEAT_OK", 100, 100, 200, 100),),
        fills=(FillRecord("FILL_OK", 500, 505, "NORMAL", 1000, 100, 2.0),),
        parameter_count=2, sample_count=4000, holdout_ref="H", walk_forward_ref="W",
        cost_model_ref="C")


# =========================================================================== #
# G5R-25 — B7 gate materiality contract
# =========================================================================== #
def test_gate_materiality_comes_from_contract():
    from engine.domain import B7GateContract, B7_GATE_CONTRACT_DATA
    data = copy.deepcopy(B7_GATE_CONTRACT_DATA)
    for g in data["gates"]:
        if g["gate_id"] == "COST_SENSITIVITY":
            g["materiality"] = "BLOCKING"
    strict = B7GateContract.from_data(data)
    cand = _clean_candidate()
    a = B7ValidationGate().run(cand, cost_sensitivity_bad=True)              # default: ADVISORY
    b = B7ValidationGate().run(cand, contract=strict, cost_sensitivity_bad=True)
    assert "COST_SENSITIVITY" not in a.material_failures
    assert "COST_SENSITIVITY" in b.material_failures
    assert b.terminal == "REJECTED"


def test_missing_required_gate_cannot_silently_pass():
    """A candidate with NO holdout/walk-forward surfaces fails the BLOCKING
    OOS_WALK_FORWARD gate and cannot pass."""
    from engine.domain import DEFAULT_B7_GATE_CONTRACT
    assert DEFAULT_B7_GATE_CONTRACT.materiality("OOS_WALK_FORWARD") == "BLOCKING"
    cand = StrategyCandidate(
        candidate_id="C", family="F", specification_ref="S",
        performance=PerformanceReport(sharpe=2.0, cumulative_return=1.0,
                                      max_drawdown=0.02, win_rate=0.7),
        features=(FeatureUse("FEAT_OK", 100, 100, 200, 100),),
        fills=(FillRecord("FILL_OK", 500, 505, "NORMAL", 1000, 100, 2.0),),
        parameter_count=2, sample_count=4000)
    res = B7ValidationGate().run(cand)
    assert "OOS_WALK_FORWARD" in res.material_failures
    assert res.terminal == "REJECTED"


def test_advisory_failure_preserved_without_false_rejection():
    cand = _clean_candidate()
    cand = StrategyCandidate(
        candidate_id=cand.candidate_id, family=cand.family,
        specification_ref=cand.specification_ref, performance=cand.performance,
        features=cand.features, fills=cand.fills, parameter_count=50, sample_count=100,
        holdout_ref="H", walk_forward_ref="W", cost_model_ref="C")
    res = B7ValidationGate().run(cand, family_multiple_peak=True)
    fam = [g for g in res.gates if g.gate_id == "FAMILY_MULTIPLICITY"][0]
    assert fam.passed is False            # advisory failure PRESERVED
    assert "FAMILY_MULTIPLICITY" not in res.material_failures   # not a false rejection
    assert res.terminal == "VALIDATION_PASS"
    # but the failure is visible, not hidden
    assert any(a.failure_id == "FAMILY_MULTIPLICITY" for a in res.failure_atoms)


def test_not_executed_doctrine_gates_are_surfaced_not_silently_passed():
    from engine.domain import DEFAULT_B7_GATE_CONTRACT
    assert "REPRODUCIBILITY" in DEFAULT_B7_GATE_CONTRACT.not_executed_gates()
    res = B7ValidationGate().run(_clean_candidate())
    assert "REPRODUCIBILITY" in res.not_executed_gates