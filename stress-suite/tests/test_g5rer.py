"""G5RER — G5R external-review TRUTH-CLOSURE regression suite (TC-01..TC-06).

Supersedes, with evidence, several claims from the earlier G5R external-review
closure where vocabulary was stronger than what was verified:

  TC-01  PROTOCOL_FROZEN=true + free-text evidence != PROVEN FREEZE CHRONOLOGY
  TC-02  an atom labeled 'exact' MUST come from the bound source; a normalized
         JSON fallback is never promoted to an exact atom (fail closed)
  TC-03  'CLEAN' is scoped to a CHECKED surface; fidelity carries the whole-
         protocol verdict and CLEAN never implies FULL_PROTOCOL_VERIFIED
  TC-04  two floats are not comparable merely because both are floats
  TC-05  source diversity alone is never globally CONFIRMED independence
         (explicit vocabulary: SOURCE_DIVERSE / SOURCE_AND_METHOD_DIVERSE /
         FULL_INDEPENDENCE_NOT_ASSESSED / CORRELATED / UNRESOLVED)
  TC-06  contract-declared provider semantics are never implied empirically
         verified (CONTRACT_SEMANTICS_ACCEPTED vs TRANSFORMATION_EMPIRICALLY_VERIFIED)

Every test is deterministic, local, model-free and wall-clock-free. Zero model
calls, zero production/cloud/capital mutation surfaces, zero CEREBUS mutation.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.domain import (
    DoctrineClaimRecord,
    DomainTransferHypothesis,
    FrozenExperimentProtocol,
    ProviderObservation,
    ProviderSemanticsRecord,
    UnresolvedPatternRecord,
    diagnose_provider_disagreement,
)
from engine.evidence import EvidenceRecord
from engine.g5_runner import load_g5_pack, run_s15
from engine.g5r import (
    DIM_MISMATCH,
    DIM_NOT_APPLICABLE,
    DIM_NOT_DOCTRINE_COMPARABLE,
    DIM_UNVERIFIED,
    DIM_VERIFIED,
    FIDELITY_FLAWED,
    FIDELITY_FULL,
    FIDELITY_PARTIAL,
    FRAGMENT_STATUS_UNRESOLVED,
    FRAGMENT_STATUS_VERIFIED,
    SEMANTIC_CORRELATED,
    SEMANTIC_FULL_NOT_ASSESSED,
    SEMANTIC_SOURCE_AND_METHOD_DIVERSE,
    SEMANTIC_UNRESOLVED,
    COMPARISON_READY,
    FreezeChronologyProof,
    IndependenceAssessment,
    MeasuredComparisonContract,
    NormalizedDoctrineClaim,
    ObservedResult,
    ReproductionProtocol,
    SourceFragmentAtom,
    classify_protocol_dimensions,
    cluster_verified_observation_paths,
    compare_measured_result,
    compare_measured_result_guarded,
    derive_fidelity,
    derive_independence,
    derive_reproduction_quality,
    derive_semantic_label,
    resolve_frozen_target_protocol,
    sha256_hex,
    validate_measured_comparison_contract,
    verify_atom_occurs_in_source,
    verify_freeze_chronology,
)
from engine.registry import EvidenceRegistry

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "scenarios"
S15_DIR = SCENARIOS / "s15_new_alpha_family"
S16_DIR = SCENARIOS / "s16_cerebus_contradiction"

_POLICY = None


def _policy():
    global _POLICY
    if _POLICY is None:
        from engine.domain_policy import G5DomainPolicy
        _POLICY = G5DomainPolicy.from_data(json.loads(
            (SCENARIOS / "policies/G5_DOMAIN_EPISTEMIC_POLICY.json")
            .read_text(encoding="utf-8")))
    return _POLICY


# --------------------------------------------------------------------------- #
# shared small builders
# --------------------------------------------------------------------------- #
def _frozen_protocol(**over):
    base = {
        "protocol_id": "PROTO_A", "mechanism_ref": "M_A", "dataset_ref": "DS",
        "time_range": "2020-01-01..2024-01-01", "features": ["f1"],
        "metrics": ["m1"], "falsification_criteria": ["fc1"], "holdout_ref": "H",
        "cost_execution_assumptions": ["c"], "promotion_criteria": ["p"],
        "target_domain": "FX", "freeze_seq": 1, "freeze_epoch": "EPOCH_0",
        "frozen_by": "GOVERNOR_TEST", "authority_basis": "registered freeze",
        "freeze_evidence_refs": ["FREEZE_EV_1"],
        "frozen_before_result_evidence": "registered at load (structured record below)",
    }
    base.update(over)
    return FrozenExperimentProtocol.from_fixture(base)


def _hypothesis(hid="H_A", mechanism="M_A", target="FX", protocol_ref="PROTO_A",
                refs=()):
    return DomainTransferHypothesis.from_fixture({
        "hypothesis_id": hid, "source_concept": "c", "source_domain": "CRYPTO",
        "target_domain": target, "source_evidence_refs": list(refs),
        "transfer_map": {"source_domain": "CRYPTO", "target_domain": target},
        "frozen_target_protocol_ref": protocol_ref, "mechanism_ref": mechanism})


def _registry_with_freeze_evidence():
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="FREEZE_EV_1", kind="OBSERVATION",
                                claim="freeze registration", source_lineage="L_FREEZE",
                                seq=0))
    return reg


def _claim(**over):
    base = {
        "claim_id": "CLAIM_A", "doctrine": "CEREBUS", "manual_version": "v4",
        "source_path": "quant-lab/reports/CEREBUS_v4_Manual_EXTRACTED.txt",
        "section": "PART_1_CORE_MANUAL / Target Metric table", "page": "4-5",
        "source_fingerprint": "1" * 64, "exact_claim_representation": "row",
        "numeric_parameters": {"session_window": "2:00-11:00 AM EST",
                               "tier_constraints": ["T1", "T2"],
                               "win_rate_band": [0.85, 0.90]},
        "structural_conditions": [], "authority_class": "CEREBUS_MANUAL",
        "current_status": "AUTHORITATIVE",
    }
    base.update(over)
    return DoctrineClaimRecord.from_fixture(base)


def _proto(**over):
    base = {
        "protocol_id": "PROTO_REPRO", "claim_ref": "CLAIM_A",
        "dataset_lineage": "DS_LINE", "implementation_version": "v1",
        "session_window": "2:00-11:00 AM EST session", "tier_constraints": ["T1", "T2"],
        "feature_definitions": ["fdef"], "pit_rules": ["PIT rule"],
        "sample_definition": "3y", "metric_definition": "Win Rate (Filtered)",
        "execution_assumptions": ["e"], "evaluation_criterion": "band membership",
        "independence_lineage": "IND_L", "falsification_criterion": "outside band",
    }
    base.update(over)
    return ReproductionProtocol.from_fixture(base)


def _obs_result(**over):
    base = {"metric": "filtered_win_rate", "estimate": 0.87,
            "uncertainty_interval": (0.86, 0.88), "sample_size": 500,
            "units": "pct_win_rate", "result_seq": 10}
    base.update(over)
    return ObservedResult.from_fixture(base)


def _pattern(refs):
    return UnresolvedPatternRecord.from_fixture({
        "pattern_id": "UP", "domain": "FX", "observations": ["OBS_A"],
        "conditions": ["c"], "data_quality_passed": True,
        "known_family_fit_attempts": [], "residual_behavior": "r",
        "independence_evidence_refs": refs, "falsifiers": [],
        "what_remains_unexplained": "x", "evidence_lineages": len(refs)})


def _registry(*refs):
    reg = EvidenceRegistry()
    for rid, lineage in refs:
        reg.register(EvidenceRecord(record_id=rid, kind="INDEPENDENT_CONFIRMATION",
                                    claim=f"ev {rid}", source_lineage=lineage, seq=0))
    return reg


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


# =========================================================================== #
# TC-01 — REAL FREEZE PROOF (chronology, not "trust me" text)
# =========================================================================== #
def test_valid_frozen_protocol_proves_freeze_before_result():
    proto = _frozen_protocol()
    proof = verify_freeze_chronology(proto, result_seq=10, registry=_registry_with_freeze_evidence())
    assert proof.status == "FROZEN_BEFORE_RESULT_VERIFIED"
    assert proof.fingerprint_valid is True
    assert proof.chronology_ok is True
    assert proof.structured_freeze is True
    assert proof.evidence_refs_resolve is True
    assert proof.freeze_seq < proof.result_seq


def test_forged_stored_fingerprint_fails_closed():
    proto = _frozen_protocol()
    # simulate a fixture that SUPPLIED a stored fingerprint that does not match
    # the recomputed canonical fingerprint (a forged stored value)
    object.__setattr__(proto, "fingerprint", "0" * 64)
    proof = verify_freeze_chronology(proto, result_seq=10, registry=_registry_with_freeze_evidence())
    assert proof.status == "FINGERPRINT_MISMATCH"
    assert proof.fingerprint_valid is False
    assert proof.chronology_ok is False


def test_stale_fingerprint_after_field_mutation_fails_closed():
    """A fixture that changes protocol fields after freeze while retaining the
    OLD stored fingerprint must fail — the stored value is stale."""
    proto = _frozen_protocol()
    good_fp = proto.fingerprint
    object.__setattr__(proto, "features", ("mutated_after_freeze",))
    assert proto.fingerprint == good_fp          # stored value unchanged (stale)
    proof = verify_freeze_chronology(proto, result_seq=10, registry=_registry_with_freeze_evidence())
    assert proof.status == "FINGERPRINT_MISMATCH"
    assert proof.fingerprint_valid is False
    assert "stale" in proof.reason.lower() or "forged" in proof.reason.lower()


def test_missing_freeze_record_text_alone_never_proves():
    proto = _frozen_protocol(freeze_seq=0, freeze_epoch="", frozen_by="",
                             authority_basis="", freeze_evidence_refs=[],
                             frozen_before_result_evidence="trust me")
    assert proto.structured_freeze_present() is False
    proof = verify_freeze_chronology(proto, result_seq=10)
    assert proof.status == "FREEZE_RECORD_INCOMPLETE"
    # resolver side: free text alone must not authorize
    hyp = _hypothesis(protocol_ref=proto.protocol_id)
    res = resolve_frozen_target_protocol(hyp, [proto])
    assert res.frozen_before_result is False


def test_result_preceding_freeze_fails_chronology():
    proto = _frozen_protocol(freeze_seq=5)
    proof = verify_freeze_chronology(proto, result_seq=5, registry=_registry_with_freeze_evidence())
    assert proof.status == "RESULT_PRECEDES_FREEZE"
    assert proof.chronology_ok is False
    proof2 = verify_freeze_chronology(proto, result_seq=3, registry=_registry_with_freeze_evidence())
    assert proof2.chronology_ok is False


def test_freeze_evidence_refs_unresolved_or_unverified_fail_closed():
    proto = _frozen_protocol(freeze_evidence_refs=["PHANTOM_REF"])
    reg = EvidenceRegistry()
    proof = verify_freeze_chronology(proto, result_seq=10, registry=reg)
    assert proof.status == "FREEZE_EVIDENCE_REFS_UNRESOLVED"
    assert proof.evidence_refs_resolve is False
    # declared refs but no registry -> UNVERIFIED, never claimed resolved
    proto2 = _frozen_protocol(freeze_evidence_refs=["ANY_REF"])
    proof2 = verify_freeze_chronology(proto2, result_seq=10, registry=None)
    assert proof2.status == "FREEZE_EVIDENCE_REFS_UNVERIFIED"


def test_wrong_mechanism_binding_never_sets_claim_hypothesis_ok():
    proto = _frozen_protocol(mechanism_ref="M_A")
    hyp = _hypothesis(mechanism="M_WRONG")
    res = resolve_frozen_target_protocol(hyp, [proto])
    assert res.resolved is True
    assert res.claim_hypothesis_ok is False
    assert "does not bind" in res.reason


def test_correct_mechanism_binding_sets_claim_hypothesis_ok():
    proto = _frozen_protocol(mechanism_ref="M_A")
    hyp = _hypothesis(mechanism="M_A")
    res = resolve_frozen_target_protocol(hyp, [proto])
    assert res.claim_hypothesis_ok is True
    assert res.fingerprint_valid is True
    assert res.frozen_before_result is True


def test_wrong_target_domain_protocol_rejected():
    proto = _frozen_protocol(target_domain="CRYPTO")
    hyp = _hypothesis(target="FX", mechanism="M_A")
    res = resolve_frozen_target_protocol(hyp, [proto])
    assert res.target_domain_ok is False
    assert res.claim_hypothesis_ok is False


# =========================================================================== #
# TC-02 — source atoms FAIL CLOSED (no normalized-JSON exact laundering)
# =========================================================================== #
def test_source_fragment_atom_verified_occurrence_and_digests():
    source_text = "SECTION\nWin Rate (Filtered) 85% – 90%\nEND"
    fragment = "Win Rate (Filtered) 85% – 90%"
    atom = SourceFragmentAtom.make(
        atom_id="A1", claim_id="C1", source_path="manual.txt", locator="L",
        claim_kind="TARGET_METRIC_ROW", exact_fragment=fragment,
        source_text=source_text, source_file_digest="d" * 64)
    assert atom.fragment_status == FRAGMENT_STATUS_VERIFIED
    assert atom.fragment_digest == sha256_hex(fragment.encode("utf-8"))
    assert verify_atom_occurs_in_source(atom, source_text) is True
    d = atom.to_dict()
    assert d["fragment_status"] == FRAGMENT_STATUS_VERIFIED
    assert d["source_file_digest"] == "d" * 64


def test_source_fragment_atom_fail_closed_when_absent_from_source():
    """A fragment that does NOT occur in the bound source is
    SOURCE_FRAGMENT_UNRESOLVED — it can never be used as an exact atom."""
    source_text = "completely different content"
    atom = SourceFragmentAtom.make(
        atom_id="A1", claim_id="C1", source_path="manual.txt", locator="L",
        claim_kind="TARGET_METRIC_ROW", exact_fragment="Win Rate (Filtered) 85%",
        source_text=source_text)
    assert atom.fragment_status == FRAGMENT_STATUS_UNRESOLVED
    assert verify_atom_occurs_in_source(atom, source_text) is False


def test_normalized_doctrine_claim_is_never_exact():
    n = NormalizedDoctrineClaim.make("C1", {"win_rate_band": [0.85, 0.9]},
                                     derived_from_atom_refs=["C1:TARGET_METRIC"])
    d = n.to_dict()
    assert d["representation_kind"] == "NORMALIZED_REPRESENTATION"
    assert "exact_fragment" not in d          # structurally cannot carry exact text
    assert n.representation_digest  # deterministic digest present
    # deterministic: two makes with same content -> same digest
    n2 = NormalizedDoctrineClaim.make("C1", {"win_rate_band": [0.85, 0.9]},
                                      derived_from_atom_refs=["C1:TARGET_METRIC"])
    assert n2.representation_digest == n.representation_digest


def test_run_s16_target_atom_is_verbatim_and_normalized_claim_is_separate():
    """Green-path check on the real bound CEREBUS extract: the TARGET_METRIC
    atom is a VERIFIED verbatim fragment and the normalized representation is a
    separate object — never the atom's exact_fragment."""
    from engine.g5_runner import run_s16
    res = run_s16(load_g5_pack(S16_DIR).decision_grade(), _policy()).artifacts
    claim = res["doctrine_claims"][0]
    atoms = {a["atom_id"]: a for a in claim["claim_atoms"]}
    target = atoms[f"{claim['claim_id']}:TARGET_METRIC"]
    assert target["fragment_status"] == FRAGMENT_STATUS_VERIFIED
    assert target["fragment_digest"]
    assert "Win Rate (Filtered)" in target["exact_fragment"]
    # the normalized claim never equals the exact fragment (not a JSON dump)
    norm = claim["normalized_claim"]
    assert norm["representation_kind"] == "NORMALIZED_REPRESENTATION"
    assert norm["claim_id"] == claim["claim_id"]
    assert target["atom_id"] in norm["derived_from_atom_refs"]
    assert json.dumps(claim["numeric_parameters"], sort_keys=True) != target["exact_fragment"]


def test_run_s16_applicability_conditions_labeled_when_not_verbatim():
    """The S16 structural_conditions are paraphrased applicability statements
    (verified absent from the manual text), so they must be labeled
    NORMALIZED_APPLICABILITY with source_bound=False — never 'exact'."""
    from engine.g5_runner import run_s16
    res = run_s16(load_g5_pack(S16_DIR).decision_grade(), _policy()).artifacts
    claim = res["doctrine_claims"][0]
    for a in claim["claim_atoms"]:
        if a["claim_kind"] == "APPLICABILITY_CONDITION":
            if a["fragment_status"] != FRAGMENT_STATUS_VERIFIED:
                assert a.get("representation_mode") == "NORMALIZED_APPLICABILITY"
                assert a.get("source_bound") is False


def test_no_json_fallback_creates_exact_atom():
    """Unit proof of the fail-closed contract: an extraction that yields NO
    verbatim text must produce an UNRESOLVED atom, and the caller-side guard
    (fragment_status != VERIFIED) prevents it ever being used as exact."""
    empty = SourceFragmentAtom.make(
        atom_id="C1:TARGET_METRIC", claim_id="C1", source_path="manual.txt",
        locator="L", claim_kind="TARGET_METRIC_ROW", exact_fragment="",
        source_text="")
    assert empty.fragment_status == FRAGMENT_STATUS_UNRESOLVED
    assert empty.exact_fragment == ""
    assert empty.fragment_digest  # digest over the actual (empty) bytes
    # a json.dumps fallback would have produced non-empty exact text here;
    # the fail-closed contract forbids substituting it
    assert "json" not in empty.representation_mode.lower() or empty.fragment_digest


# =========================================================================== #
# TC-03 — CLEAN is scoped to a checked surface; fidelity is explicit
# =========================================================================== #
def test_clean_quality_never_implies_full_protocol_verified():
    qa = derive_reproduction_quality(_proto(), _claim())
    assert qa.quality == "CLEAN"
    assert qa.fidelity == FIDELITY_PARTIAL
    assert qa.clean_surface == "CHECKED_SURFACE_ONLY"
    # the whole protocol was NOT validated: several dimensions are
    # NOT_DOCTRINE_COMPARABLE (no doctrine contract) — CLEAN != FULL
    labels = dict(qa.dimension_classifications)
    assert labels["claim_ref"] == DIM_VERIFIED
    assert labels["session"] == DIM_VERIFIED
    assert labels["tiers"] == DIM_VERIFIED
    assert DIM_NOT_DOCTRINE_COMPARABLE in labels.values()


def test_dimension_classification_never_silent_pass():
    proto = _proto(claim_ref="WRONG_CLAIM")
    dims = dict(classify_protocol_dimensions(proto, _claim()))
    assert dims["claim_ref"] == DIM_MISMATCH
    # observed metric identity + units are assessed by the measured-comparison
    # contract, not silently passed here
    assert dims["observed_metric_identity"] == DIM_NOT_APPLICABLE
    assert dims["units"] == DIM_NOT_APPLICABLE
    qa = derive_reproduction_quality(proto, _claim())
    assert qa.quality == "FLAWED"
    assert qa.fidelity == FIDELITY_FLAWED


def test_derive_fidelity_vocabulary_boundaries():
    all_verified = [(d, DIM_VERIFIED) for d in
                    ("claim_ref", "session", "tiers", "PIT", "metric_definition",
                     "sample_definition")]
    full, surface = derive_fidelity("CLEAN", all_verified)
    assert full == FIDELITY_FULL and surface == "FULL_ASSESSED_SURFACE"
    partial = all_verified + [("units", DIM_NOT_DOCTRINE_COMPARABLE)]
    full2, _ = derive_fidelity("CLEAN", partial)
    assert full2 == FIDELITY_PARTIAL
    unverified = all_verified + [("PIT", DIM_UNVERIFIED)]
    full3, _ = derive_fidelity("CLEAN", unverified)
    assert full3 == FIDELITY_PARTIAL            # material UNVERIFIED blocks FULL
    flawed = all_verified + [("claim_ref", DIM_MISMATCH)]
    full4, _ = derive_fidelity("CLEAN", flawed)
    assert full4 == FIDELITY_FLAWED


def test_material_unverified_dimension_never_full():
    """A material UNVERIFIED dimension (empty PIT rules) prevents
    FULL_PROTOCOL_VERIFIED and gates quality to FLAWED."""
    qa = derive_reproduction_quality(_proto(pit_rules=[]), _claim())
    assert qa.quality == "FLAWED"
    assert qa.fidelity == FIDELITY_FLAWED
    labels = dict(qa.dimension_classifications)
    assert labels["PIT"] == DIM_UNVERIFIED


# =========================================================================== #
# TC-04 — measured comparison CONTRACT (validate before comparing floats)
# =========================================================================== #
def test_compare_contract_blocks_metric_mismatch():
    obs = _obs_result(metric="other_metric")
    c = validate_measured_comparison_contract(obs, (0.85, 0.90), expected_metric="filtered_win_rate")
    assert c.metric_ok is False
    assert c.readiness == "METRIC_MISMATCH"
    contract, comp = compare_measured_result_guarded(obs, (0.85, 0.90),
                                                     expected_metric="filtered_win_rate")
    assert contract.readiness == "METRIC_MISMATCH"
    assert comp is None


def test_compare_contract_blocks_units_incompatible():
    obs = _obs_result(units="notional_usd")
    c = validate_measured_comparison_contract(obs, (0.85, 0.90), claim_units="pct_win_rate")
    assert c.units_ok is False
    assert c.readiness == "UNITS_INCOMPATIBLE"


def test_compare_contract_blocks_invalid_intervals():
    obs = _obs_result(uncertainty_interval=(0.90, 0.85))   # inverted
    c = validate_measured_comparison_contract(obs, (0.85, 0.90),
                                              claim_units="pct_win_rate")
    assert c.interval_valid is False
    assert c.readiness == "INVALID_INTERVAL"
    obs2 = _obs_result()
    c2 = validate_measured_comparison_contract(obs2, (0.95, 0.85),   # inverted claim band
                                               claim_units="pct_win_rate")
    assert c2.claim_interval_valid is False
    assert c2.readiness == "INVALID_CLAIM_INTERVAL"


def test_compare_contract_blocks_estimate_outside_uncertainty():
    obs = _obs_result(estimate=0.99, uncertainty_interval=(0.86, 0.88))
    c = validate_measured_comparison_contract(obs, (0.85, 0.90),
                                              claim_units="pct_win_rate")
    assert c.estimate_in_interval is False
    assert c.readiness == "ESTIMATE_OUTSIDE_UNCERTAINTY"
    # explicitly allowed -> no longer a blocker
    c2 = validate_measured_comparison_contract(
        obs, (0.85, 0.90), claim_units="pct_win_rate",
        allow_estimate_outside_interval=True)
    assert c2.readiness == COMPARISON_READY


def test_compare_contract_blocks_missing_sample():
    obs = _obs_result(sample_size=0)
    c = validate_measured_comparison_contract(obs, (0.85, 0.90),
                                              claim_units="pct_win_rate")
    assert c.sample_ok is False
    assert c.readiness == "SAMPLE_REQUIRED"
    c2 = validate_measured_comparison_contract(obs, (0.85, 0.90),
                                               claim_units="pct_win_rate",
                                               require_sample=False)
    assert c2.readiness == COMPARISON_READY


def test_compare_contract_ready_then_guarded_compare_runs():
    obs = _obs_result()
    contract, comp = compare_measured_result_guarded(
        obs, (0.85, 0.90), expected_metric="filtered_win_rate",
        claim_metric="filtered_win_rate", claim_units="pct_win_rate")
    assert contract.readiness == COMPARISON_READY
    assert comp is not None
    assert comp.verdict == "SUPPORTS_CLAIM"


def test_exact_band_equality_is_explicitly_inconclusive():
    """Exact equality of the observed interval to the full doctrine band counts
    INCONCLUSIVE (boundary equality is indeterminate under ER-04 semantics),
    never SUPPORTS and never CONTRADICTS."""
    obs = _obs_result(estimate=0.875, uncertainty_interval=(0.85, 0.90))
    contract, comp = compare_measured_result_guarded(
        obs, (0.85, 0.90), expected_metric="filtered_win_rate",
        claim_metric="filtered_win_rate", claim_units="pct_win_rate")
    assert contract.readiness == COMPARISON_READY
    assert comp is not None
    assert comp.verdict == "INCONCLUSIVE"
    assert comp.observed_interval == (0.85, 0.90)
    assert comp.claim_interval == (0.85, 0.90)


def test_boundary_touch_inconclusive_strict_separation_contradicts():
    touch = _obs_result(estimate=0.89, uncertainty_interval=(0.88, 0.90))  # hi == claim hi
    _, comp = compare_measured_result_guarded(touch, (0.85, 0.90),
                                              claim_units="pct_win_rate")
    assert comp.verdict == "INCONCLUSIVE"
    far = _obs_result(estimate=0.94, uncertainty_interval=(0.93, 0.95))
    _, comp2 = compare_measured_result_guarded(far, (0.85, 0.90),
                                               claim_units="pct_win_rate")
    assert comp2.verdict == "CONTRADICTS_CLAIM"


# =========================================================================== #
# TC-05 — independence semantics must not fork from G3; explicit vocabulary
# =========================================================================== #
def test_semantic_label_unresolved_when_zero_refs_or_unknown():
    assert derive_semantic_label(0, 0, 0, False, []) == SEMANTIC_UNRESOLVED
    assert derive_semantic_label(2, 2, 1, True, ["E1", "E2"]) == SEMANTIC_UNRESOLVED


def test_source_only_is_never_globally_confirmed_independence():
    """Two distinct source lineages with NO method/runtime assessment must not
    be labeled globally CONFIRMED independence — it is
    FULL_INDEPENDENCE_NOT_ASSESSED."""
    p = _pattern(refs=["E1", "E2"])
    a = derive_independence(p, _registry(("E1", "L1"), ("E2", "L2")), None)
    assert a.independence_status == "CONFIRMED"      # policy-channel vocabulary
    assert a.semantic_label == SEMANTIC_FULL_NOT_ASSESSED
    assert "FULL_INDEPENDENCE_NOT_ASSESSED" in a.rationale


def test_source_and_method_diverse_label():
    p = _pattern(refs=["E1", "E2"])
    a = derive_independence(p, _registry(("E1", "L1"), ("E2", "L2")),
                            {"E1": "M1", "E2": "M2"})
    assert a.independence_status == "CONFIRMED"
    assert a.semantic_label == SEMANTIC_SOURCE_AND_METHOD_DIVERSE


def test_correlated_when_methods_share_lineage_or_single_source():
    p = _pattern(refs=["E1", "E2"])
    a = derive_independence(p, _registry(("E1", "L1"), ("E2", "L2")),
                            {"E1": "M1", "E2": "M1"})
    assert a.independence_status == "SOURCE_ONLY"
    assert a.semantic_label == SEMANTIC_CORRELATED
    single = _pattern(refs=["E1", "E2"])
    b = derive_independence(single, _registry(("E1", "L1"), ("E2", "L1")), None)
    assert b.semantic_label == SEMANTIC_CORRELATED


def test_unknown_lineage_never_favorable():
    reg = _registry(("E1", "L1"))
    reg.register(EvidenceRecord(record_id="E2", kind="AGENT_CLAIM",
                                claim="no lineage", source_lineage="", seq=1))
    a = derive_independence(_pattern(refs=["E1", "E2"]), reg, None)
    assert a.unknown_lineage_count >= 1
    assert a.semantic_label == SEMANTIC_UNRESOLVED


class _AliasRegistry:
    """Fake registry where two ref strings alias ONE underlying evidence object."""

    def __init__(self, record):
        self._record = record

    def resolve(self, ref):
        return self._record


def test_cluster_dedupes_canonical_underlying_identity_not_ref_string():
    """E1 and E2 alias ONE evidence object -> ONE canonical path, even though
    the reference strings differ."""
    underlying = EvidenceRecord(record_id="EV_UNDERLYING", kind="OBSERVATION",
                                claim="the one evidence object", source_lineage="L1", seq=0)
    p = _pattern(refs=["E1", "E2"])
    paths = cluster_verified_observation_paths([p], _AliasRegistry(underlying))
    assert len(paths) == 1
    assert paths == ("EV_UNDERLYING",)


def test_cluster_distinct_records_still_count_separately():
    p = _pattern(refs=["E1", "E2"])
    paths = cluster_verified_observation_paths([p], _registry(("E1", "L1"), ("E2", "L2")))
    assert len(paths) == 2


def test_run_s15_pattern_carries_semantic_label_observability():
    """S15 exploration may rest on source diversity per its explicit
    PROVISIONAL_SCENARIO_TEST_POLICY, but the evidence item must carry the
    honest semantic label (FULL_INDEPENDENCE_NOT_ASSESSED), not a global
    confirmation claim."""
    res = run_s15(load_g5_pack(S15_DIR).decision_grade(), _policy())
    item = res.artifacts["patterns"][0]
    indep = item["independence"]
    assert indep["semantic_label"] in (
        SEMANTIC_FULL_NOT_ASSESSED, SEMANTIC_SOURCE_AND_METHOD_DIVERSE,
        SEMANTIC_UNRESOLVED)
    if indep["independence_status"] == "CONFIRMED":
        assert indep["semantic_label"] == SEMANTIC_FULL_NOT_ASSESSED or \
            indep["semantic_label"] == SEMANTIC_SOURCE_AND_METHOD_DIVERSE


# =========================================================================== #
# TC-06 — provider semantics: CONTRACT_ACCEPTED vs EMPIRICALLY_VERIFIED
# =========================================================================== #
def test_diagnosis_contract_semantics_not_empirical_by_default():
    obs_a = _obs("O1", provider="P", metric="M", adapter_version="v1")
    obs_b = _obs("O2", provider="P2", metric="M", adapter_version="v1",
                 instrument_canonical_id="BTC_USDT_PERP")
    sem_a = _sem("P", "M", adapter_version="v1")
    sem_b = _sem("P2", "M", adapter_version="v1")
    diag = diagnose_provider_disagreement(obs_a, obs_b, sem_a, sem_b)
    assert diag.semantics_grade == "CONTRACT_SEMANTICS_ACCEPTED"
    assert diag.timestamp_grade == "CONTRACT_DECLARED"
    grades = diag.transformation_grades
    assert set(grades) == {"normalization", "instrument_identity", "adapter",
                           "time_semantics"}
    assert all(g == "CONTRACT_SEMANTICS_ACCEPTED" for g in grades.values())
    # the terminal never implies empirical verification
    blob = json.dumps(diag.to_dict())
    assert "TRANSFORMATION_EMPIRICALLY_VERIFIED" not in blob


def test_empirically_verified_steps_upgrade_only_those_steps():
    obs_a = _obs("O1", provider="P", metric="M", adapter_version="v1")
    obs_b = _obs("O2", provider="P2", metric="M", adapter_version="v1",
                 instrument_canonical_id="BTC_USDT_PERP")
    sem_a = _sem("P", "M", adapter_version="v1")
    sem_b = _sem("P2", "M", adapter_version="v1")
    diag = diagnose_provider_disagreement(
        obs_a, obs_b, sem_a, sem_b, empirically_verified_steps=["normalization"])
    assert diag.transformation_grades["normalization"] == "TRANSFORMATION_EMPIRICALLY_VERIFIED"
    assert diag.transformation_grades["adapter"] == "CONTRACT_SEMANTICS_ACCEPTED"
    # overall grade stays CONTRACT until every transformation step is verified
    assert diag.semantics_grade == "CONTRACT_SEMANTICS_ACCEPTED"
    assert diag.timestamp_grade == "CONTRACT_DECLARED"


def test_all_steps_verified_upgrades_semantics_grade():
    obs_a = _obs("O1", provider="P", metric="M", adapter_version="v1")
    obs_b = _obs("O2", provider="P2", metric="M", adapter_version="v1",
                 instrument_canonical_id="BTC_USDT_PERP")
    sem_a = _sem("P", "M", adapter_version="v1")
    sem_b = _sem("P2", "M", adapter_version="v1")
    diag = diagnose_provider_disagreement(
        obs_a, obs_b, sem_a, sem_b,
        empirically_verified_steps=["normalization", "instrument_identity",
                                    "adapter", "time_semantics"])
    assert diag.semantics_grade == "TRANSFORMATION_EMPIRICALLY_VERIFIED"
    assert diag.timestamp_grade == "DETERMINISTICALLY_VERIFIED"


def test_terminal_values_unchanged_while_grades_added():
    obs_a = _obs("O1", provider="P", metric="M", adapter_version="v1")
    obs_b = _obs("O2", provider="P2", metric="M", adapter_version="v1",
                 instrument_canonical_id="BTC_USDT_PERP")
    diag = diagnose_provider_disagreement(obs_a, obs_b, _sem("P", "M"), _sem("P2", "M"))
    assert diag.terminal == "NO_DISAGREEMENT"
    assert diag.cause == "NO_DISAGREEMENT"
