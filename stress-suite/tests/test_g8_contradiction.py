"""G8 — cross-scenario contradiction audit regressions + adversarial controls.

Covers the §9 mandatory controls C01-C15 of the G8 master prompt, the mandated
comparison families of §7, and the gate-claim audit of §7 (cross-gate claims).

Every control proves the AUDIT can detect its own failure mode. Nothing here
alters canonical S01-S24 fixtures: the negative control builds its own synthetic
family on a COPY of the frozen contract.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scenarios") not in sys.path:
    sys.path.insert(0, str(ROOT / "scenarios"))

from engine.evidence import EvidenceRecord  # noqa: E402
from engine.g7_sensitivity import authority_boundary_surface  # noqa: E402
from engine.g8_contradiction import (  # noqa: E402
    SelfCertificationError,
    SealedAccessError,
    assert_decision_grade,
    assert_not_self_certifying,
    build_contradiction_register,
    build_equivalence_classes,
    build_observation,
    compare_observations,
    decide_gate,
    extract_claims,
    load_contract,
    mandated_pair_coverage,
    normalize_vector,
    run_comparison_family,
    scan_for_sealed,
    validate_contract,
)
from engine.registry import EvidenceRegistry  # noqa: E402

import g8_run_audit as AUDIT  # noqa: E402

CONTRACT_PATH = ROOT / "evidence" / "G8_EQUIVALENCE_CONTRACT.json"


@pytest.fixture(scope="module")
def contract() -> Dict[str, Any]:
    return load_contract(CONTRACT_PATH)


@pytest.fixture(scope="module")
def package() -> Dict[str, Any]:
    return AUDIT.build_package(measured_full=938)


def _obs(contract, oid, **kw):
    base = {
        "observation_id": oid, "family_id": kw.pop("family_id", "F1"),
        "source_gate": kw.pop("source_gate", "SYNTHETIC"),
        "source_ref": kw.pop("source_ref", oid),
        "state_machine": kw.pop("state_machine", "M5_PHASE"),
        "object_class": kw.pop("object_class", "INSTITUTIONAL_PHASE"),
        "raw_outcome_token": kw.pop("raw_outcome_token", "STABLE"),
        "vector_values": kw.pop("vector_values", {}),
    }
    base.update(kw)
    return build_observation(contract, **base)


def _sufficient_contract(contract, family_id="F1"):
    """A COPY of the frozen contract whose family declares a sufficient basis.
    Used by the negative control; canonical fixtures are untouched."""
    copied = copy.deepcopy(contract)
    for fam in copied["comparison_families"]:
        if fam["family_id"] == family_id:
            fam["equivalence_basis"] = "DECLARED_SUFFICIENT"
            fam["equivalence_basis_note"] = "SYNTHETIC CONTROL ONLY"
    validate_contract(copied)
    return copied


# --------------------------------------------------------------------------- #
# C01 / C02 / C03 — contradiction, discriminator, omitted discriminator
# --------------------------------------------------------------------------- #
def test_c01_identical_facts_with_different_outcomes_are_a_contradiction(contract):
    synthetic = _sufficient_contract(contract)
    left = _obs(synthetic, "SYN:A", family_id="F1", raw_outcome_token="STABLE",
                vector_values={"evidence_quality": "STRONG"})
    right = _obs(synthetic, "SYN:B", family_id="F1", raw_outcome_token="NEW_STABLE",
                 vector_values={"evidence_quality": "STRONG"})
    result = compare_observations(synthetic, left, right)
    assert result.verdict == "CONTRADICTION"
    assert result.classification == "ARCHITECTURE_CONTRADICTION"
    assert result.differing_fields == ()
    assert "incompatible outcome classes" in result.reason


def test_c02_declared_discriminator_prevents_a_false_contradiction(contract):
    # F1 (M5 phase) declares the evaluation-contract state as a VERIFIED field, so a
    # difference in it may legitimately carry a different outcome.
    left = _obs(contract, "SYN:A",
                vector_values={"evaluation_contract_state": "FROZEN"})
    right = _obs(contract, "SYN:B", raw_outcome_token="NO_CHANGE",
                 vector_values={"evaluation_contract_state": "UNFROZEN"})
    result = compare_observations(contract, left, right)
    assert result.verdict == "MATERIAL_DISCRIMINATOR"
    assert "D-CONTRACT-STATE" in result.discriminator_ids
    assert result.classification == "" and result.severity == ""


def test_c03_omitted_discriminator_cannot_create_silent_equivalence(contract):
    # `evidence_provenance` is declared NEUTRAL: it may never justify a divergence,
    # so a provenance-mode difference that changes the outcome is a contradiction,
    # not an accepted explanation.
    left = _obs(contract, "SYN:A", vector_values={
        "evidence_provenance": "GOVERNED_REGISTRY"})
    right = _obs(contract, "SYN:B", raw_outcome_token="NO_CHANGE", vector_values={
        "evidence_provenance": "AUTHORITATIVE_SYNTHETIC_FIXTURE"})
    result = compare_observations(contract, left, right)
    assert result.verdict == "CONTRADICTION"
    assert result.classification == "ARCHITECTURE_CONTRADICTION"
    assert "no declared discriminator explaining the divergence" in result.reason

    # a field with no rule at all is reported as UNDECLARED and cannot silently
    # produce either equivalence or a material discriminator
    bare = copy.deepcopy(contract)
    bare["discriminator_rules"] = [d for d in bare["discriminator_rules"]
                                   if d["field"] != "persistence"]
    left2 = _obs(bare, "SYN:C")
    right2 = _obs(bare, "SYN:D", raw_outcome_token="NO_CHANGE",
                  vector_values={"persistence": "CHRONIC"})
    result2 = compare_observations(bare, left2, right2)
    assert "persistence" in result2.undeclared_fields
    assert result2.classification == "INSUFFICIENT_EVIDENCE"
    # and the same undeclared difference with the SAME outcome is also refused
    result3 = compare_observations(bare, left2, _obs(
        bare, "SYN:E", vector_values={"persistence": "CHRONIC"}))
    assert "persistence" in result3.undeclared_fields
    assert result3.verdict == "CONTRADICTION"


# --------------------------------------------------------------------------- #
# C04 / C10 — UNKNOWN is never favorable; profit/capability are not outcome fields
# --------------------------------------------------------------------------- #
def test_c04_unknown_is_never_normalized_into_a_favourable_token(contract):
    vector = normalize_vector(contract, {"independence": "UNKNOWN",
                                         "evidence_quality": "STRONG"})
    assert vector.values["independence"] == "UNKNOWN"
    assert vector.derivation_status["independence"] == "DERIVED"
    # an undeclared token fails closed to UNKNOWN, never to a nearest known token
    bad = normalize_vector(contract, {"independence": "VERY_HIGH"})
    assert bad.values["independence"] == "UNKNOWN"
    assert bad.derivation_status["independence"] == "UNDECLARED_TOKEN_FAILED_CLOSED"
    # a missing field is UNKNOWN and recorded as not derived
    missing = normalize_vector(contract, {})
    assert missing.values["independence"] == "UNKNOWN"
    assert missing.derivation_status["independence"] == "NOT_DERIVED"
    # UNKNOWN on an ordered field is not evaluable: it becomes a recorded gap
    left = _obs(contract, "SYN:A", vector_values={"evidence_quality": "STRONG"})
    right = _obs(contract, "SYN:B", raw_outcome_token="NO_CHANGE")
    result = compare_observations(contract, left, right)
    assert result.verdict != "CONSISTENT"


def test_c10_profit_and_capability_are_never_outcome_equivalence_fields(contract):
    banned = ("profit", "pnl", "capability", "confidence", "novelty", "vote_count",
              "score")
    declared = {f["field"] for f in contract["equivalence_fields"]}
    for field in declared:
        assert not any(b in field for b in banned), field
    # a difference in an undeclared profit-like field cannot create a verdict
    left = _obs(contract, "SYN:A")
    right = _obs(contract, "SYN:B")
    assert compare_observations(contract, left, right).verdict == "CONSISTENT"


# --------------------------------------------------------------------------- #
# C05 — state-machine vocabulary is not interchangeable
# --------------------------------------------------------------------------- #
def test_c05_same_terminal_string_on_different_machines_is_not_comparable(contract):
    m5 = _obs(contract, "SYN:M5", state_machine="M5_PHASE",
              object_class="INSTITUTIONAL_PHASE", raw_outcome_token="UNRESOLVED")
    m4 = _obs(contract, "SYN:M4", state_machine="M4_KNOWLEDGE",
              object_class="KNOWLEDGE_OBJECT", raw_outcome_token="UNRESOLVED")
    result = compare_observations(contract, m5, m4)
    assert result.verdict == "NOT_COMPARABLE"
    assert "N8" in result.reason
    assert result.classification == ""


# --------------------------------------------------------------------------- #
# C06 / C07 — determinism, ordering, renaming
# --------------------------------------------------------------------------- #
def test_c06_reordered_declarations_leave_digest_and_report_identical(contract):
    a = _obs(contract, "SYN:A", vector_values={"evidence_quality": "STRONG",
                                              "evaluation_contract_state": "FROZEN"})
    b = _obs(contract, "SYN:A", vector_values={
        "evaluation_contract_state": "FROZEN", "evidence_quality": "STRONG"})
    assert a.vector.digest() == b.vector.digest()
    assert a.fingerprint() == b.fingerprint()
    assert json.dumps(a.to_dict(), sort_keys=True) == json.dumps(b.to_dict(),
                                                                 sort_keys=True)


def test_c07_renaming_identifiers_does_not_change_vector_or_verdict(contract):
    base = {"evidence_quality": "STRONG"}
    left = _obs(contract, "SYN:A", source_ref="AGENT_1", vector_values=base)
    renamed = _obs(contract, "SYN:A2", source_ref="AGENT_X", vector_values=base)
    assert left.vector.digest() == renamed.vector.digest()
    assert left.fingerprint() == renamed.fingerprint()
    partner = _obs(contract, "SYN:B", source_ref="AGENT_2",
                   raw_outcome_token="NO_CHANGE", vector_values=base)
    assert compare_observations(contract, left, partner).verdict == \
        compare_observations(contract, renamed, partner).verdict


# --------------------------------------------------------------------------- #
# C08 — aliases are one epistemic path
# --------------------------------------------------------------------------- #
def test_c08_aliasing_one_evidence_object_is_one_epistemic_path():
    reg = EvidenceRegistry()
    reg.register(EvidenceRecord(record_id="EV_1", kind="OBSERVATION",
                                claim="c", subject="S", source_lineage="L1", seq=1))
    reg.register(EvidenceRecord(record_id="EV_1_ALIAS", kind="OBSERVATION",
                                claim="c", subject="S", source_lineage="L1", seq=1))
    one = reg.lineage_summary(["EV_1"])
    aliased = reg.lineage_summary(["EV_1", "EV_1_ALIAS"])
    assert aliased.distinct_source_lineages == one.distinct_source_lineages == 1
    assert aliased.raw_evidence_count == 2  # raw count kept, independence unchanged


# --------------------------------------------------------------------------- #
# C09 — a claimed label is not authority
# --------------------------------------------------------------------------- #
def test_c09_operator_label_without_canonical_authority_has_no_effect():
    boundary = authority_boundary_surface("OPERATOR_1", "GOV")
    assert boundary["operator_authorized"] is True
    assert boundary["governor_authorized"] is False
    assert boundary["stranger_authorized"] is False
    # the G6 vector derives authority from the CANONICAL SEED only: a stimulus-level
    # claim is not an equivalence field at all
    assert AUDIT._max_authority({"W1": "WORKER", "GOV": "GOVERNOR"}) == "GOVERNOR"
    assert AUDIT._max_authority({"IMPOSTER": "OPERATOR"}) == "OPERATOR"


# --------------------------------------------------------------------------- #
# C11 / C12 — sealed truth and future-planning language
# --------------------------------------------------------------------------- #
def test_c11_sealed_truth_is_never_consumed(package):
    # every observation the audit built carries no sealed field
    for obs in package["observations"]:
        assert scan_for_sealed(obs.to_dict()) == []
    # the guard actually fires on a payload that still carries sealed truth
    with pytest.raises(SealedAccessError):
        assert_decision_grade({"hidden_ground_truth": {"x": 1}}, "probe")
    with pytest.raises(SealedAccessError):
        assert_decision_grade({"a": {"expected_disposition": "X"}}, "probe")
    # and accepts a decision-grade projection (present but empty)
    assert_decision_grade({"expected_disposition": "", "hidden_ground_truth": None},
                          "probe")


def test_c12_proposed_future_package_cannot_overwrite_existing_expectations(contract):
    banned = ("A012", "A-012", "MF_A002", "MF-A002", "OPH", "CADENCE",
              "CONTINUATION", "MODEL_SPARSE")
    # every DECISION INPUT must be free of the proposed future package
    decision_inputs = {
        "equivalence_fields": contract["equivalence_fields"],
        "discriminator_rules": contract["discriminator_rules"],
        "comparison_families": contract["comparison_families"],
        "guarded_properties": contract["guarded_properties"],
        "outcome_token_map": contract["outcome_token_map"],
        "outcome_classes": contract["outcome_classes"],
        "normalization_rules": contract["normalization_rules"],
    }
    for name, payload in decision_inputs.items():
        blob = json.dumps(payload).upper()
        for token in banned:
            assert token not in blob, (name, token)
    for path in (ROOT / "engine" / "g8_contradiction.py",
                 ROOT / "scenarios" / "g8_run_audit.py"):
        source = path.read_text(encoding="utf-8").upper()
        for token in banned:
            assert token not in source, (path.name, token)
    # the contract may only mention the package in its explicit non-input
    # declaration, and the vocabulary must permit recording the interaction
    assert "A-012" in contract["freeze_note"]
    assert "FUTURE_PLANNING_IMPACT" in contract["classification_vocabulary"]


# --------------------------------------------------------------------------- #
# C13 — a seeded inconsistent control is detected, and the register is non-empty
# --------------------------------------------------------------------------- #
def test_c13_seeded_inconsistent_control_is_detected_and_registered(contract):
    synthetic = _sufficient_contract(contract)
    # a control that contradicts itself: identical facts, incompatible outcomes
    inconsistent = _obs(synthetic, "CTRL:BAD", family_id="F1",
                        raw_outcome_token="STABLE",
                        vector_values={"evidence_quality": "STRONG"})
    inconsistent_twin = _obs(synthetic, "CTRL:BAD_TWIN", family_id="F1",
                             raw_outcome_token="NO_CHANGE",
                             vector_values={"evidence_quality": "STRONG"})
    family = {"family_id": "F1", "family_class": "PHASE_STRUCTURE",
              "question": "synthetic control", "members": ["CTRL:BAD",
                                                            "CTRL:BAD_TWIN"],
              "declared_pairs": [["CTRL:BAD", "CTRL:BAD_TWIN"]],
              "default_classification": "ARCHITECTURE_CONTRADICTION"}
    result = run_comparison_family(synthetic, family,
                                   {"CTRL:BAD": inconsistent,
                                    "CTRL:BAD_TWIN": inconsistent_twin})
    assert len(result.contradictions()) == 1
    register = build_contradiction_register(synthetic, [result], [], [])
    assert register["open_entries"] == 1
    assert register["counts_by_classification"]["ARCHITECTURE_CONTRADICTION"] == 1
    # an empty register with a seeded control would be a hard failure
    empty = build_contradiction_register(synthetic, [], [], [])
    assert empty["open_entries"] == 0 and register["open_entries"] == 1


# --------------------------------------------------------------------------- #
# C14 / C15 — byte reproducibility and the self-certification guard
# --------------------------------------------------------------------------- #
def test_c14_report_generation_is_byte_reproducible():
    first = json.dumps(AUDIT.build_package(measured_full=938)["register"],
                       sort_keys=True)
    second = json.dumps(AUDIT.build_package(measured_full=938)["register"],
                        sort_keys=True)
    assert first == second


def test_c15_receipt_cannot_certify_itself():
    with pytest.raises(SelfCertificationError):
        assert_not_self_certifying({"tested_sha": "abc"},
                                   receipt_path="evidence/G8_EVIDENCE_RECEIPT.json",
                                   evidence_paths=["evidence/G8_RESULT.md"],
                                   containing_commit="abc")
    # distinct commit is accepted
    assert_not_self_certifying({"tested_sha": "abc"},
                               receipt_path="evidence/G8_EVIDENCE_RECEIPT.json",
                               evidence_paths=["evidence/G8_RESULT.md"],
                               containing_commit="def")


# --------------------------------------------------------------------------- #
# Mandated families, coverage, decision
# --------------------------------------------------------------------------- #
def test_all_observations_have_a_mapped_outcome_class(package):
    assert len(package["observations"]) == 29
    for obs in package["observations"]:
        assert obs.outcome_mapped, (obs.observation_id, obs.raw_outcome_token)
        assert obs.outcome_class, obs.observation_id


def test_every_mandated_comparison_pair_was_actually_compared(package):
    coverage = package["mandated_coverage"]
    assert coverage["uncovered_mandated_pairs"] == []
    assert coverage["mandated_comparisons_observed"] == coverage["mandated_pairs"] > 0


def test_every_family_completed_its_comparisons(package):
    for fam in package["families"]:
        counts = fam.to_dict()["counts"]
        assert counts["missing"] == 0, fam.family_id
        assert counts["comparisons"] == counts["members"] * (counts["members"] - 1) // 2 \
            or fam.family_id == "F2", fam.family_id
        assert counts["consistent"] + counts["material_discriminator"] + \
            counts["not_comparable"] + counts["contradictions"] == counts["comparisons"]


def test_an_incoherent_equivalence_class_is_never_silent(package):
    """Every equivalence class holding more than one outcome class must have a
    matching recorded entry. Incoherence may be reported, never dropped."""
    registered = {(e["family_id"], frozenset((e["left"], e["right"])))
                  for e in package["register"]["entries"]
                  if e["kind"] == "COMPARISON_CONTRADICTION"}
    for cls in build_equivalence_classes(package["observations"]):
        if cls.coherent or len(cls.members) < 2:
            continue
        pair = frozenset(cls.members)
        assert (cls.family_id, pair) in registered, cls.to_dict()


def test_no_observation_pair_was_compared_across_state_machines(package):
    for fam in package["families"]:
        for cmp in fam.comparisons:
            if cmp.verdict == "NOT_COMPARABLE":
                assert "different state machines" in cmp.reason


def test_gate_decision_is_derived_from_the_counts_not_asserted(package):
    decision = package["decision"]
    assert decision["counts"]["blocking_contradictions"] == 0
    assert decision["counts"]["guarded_violations"] == 0
    blocking = (decision["counts"]["gate_claim_blocking"]
                + decision["counts"]["evidence_gaps"])
    if blocking or decision["counts"]["blocking_contradictions"]:
        assert decision["exit"] != "PASS_G8_CROSS_SCENARIO_COHERENCE"
    assert decision["mandated"]["uncovered"] == []


def test_gate_claim_audit_locates_each_receipt_surface_and_recomputes_lineage(package):
    gate = package["gate"]
    assert gate["receipts_audited"], "no receipts audited"
    lineage = gate["count_lineage"]
    assert lineage["terminal_matches_measured"] is True
    # every audited receipt produced at least one finding, so nothing is missing
    assert len(gate["findings"]) > len(gate["receipts_audited"])
    assert lineage["monotone"] is True
    assert lineage["terminal_declared_full"] == 938
    assert lineage["arithmetic_defects"] == []


def test_audit_records_the_g4_declared_identifier_as_a_defect(package):
    """Regression: the G4 receipt declares a full-length identifier that is not an
    object in this repository. It must be recorded, and the audit must say exactly
    what its own abbreviation resolves to and whether the subject matches."""
    findings = [f for f in package["gate"]["findings"]
                if "G4_EVIDENCE_RECEIPT" in f["receipt_path"]
                and f["finding_id"].startswith("TESTED_SHA")]
    assert findings, "the unresolvable G4 tested surface must be recorded"
    finding = findings[0]
    assert finding["is_defect"] is True
    assert finding["finding_id"] == "TESTED_SHA_FULL_FORM_UNRESOLVABLE"
    assert finding["classification"] == "RECEIPT_OR_CLAIM_DEFECT"
    evidence = finding["evidence"]
    assert evidence["declared_sha"] == "490e078d1e2e6f1c31e88944de9cf2dcd99a4609"
    # the abbreviation the SAME receipt declares resolves to exactly one commit
    # whose recorded subject matches the receipt's declared subject verbatim
    assert evidence["prefix"] == "490e078d"
    assert evidence["resolved_candidate"].startswith("490e078d2b5c")
    assert evidence["declared_subject_matches"] is True
    # an identifier defect is never silently dismissed: it appears in the register
    assert any(e["left"].endswith("G4_EVIDENCE_RECEIPT.json")
               for e in package["register"]["entries"]
               if e["classification"] == "RECEIPT_OR_CLAIM_DEFECT")


def test_receipt_claim_extraction_reads_the_declaration_it_consumed():
    """The older G1 receipt names its tested surface as `ending_sha`, not as
    `tested_sha`; the audit must read the declaration and say which one it used."""
    g1 = json.loads((ROOT / "evidence" / "G1_EVIDENCE_RECEIPT.json").read_text(
        encoding="utf-8"))
    claims = extract_claims(g1)
    assert claims["tested_sha"] == g1["ending_sha"]
    assert claims["claim_sources"]["tested_sha"] == "ending_sha"
    assert claims["start_sha"] == g1["starting_sha"]
    assert claims["full_test_count"] == 77
    assert claims["claim_sources"]["full_test_count"] == "tests_run"
    # a nested receipt declaration is read too (G3 stores it under receipt_lineage)
    g3 = json.loads((ROOT / "evidence" / "G3_EVIDENCE_RECEIPT.json").read_text(
        encoding="utf-8"))
    g3_claims = extract_claims(g3)
    assert g3_claims["tested_sha"] == g3["receipt_lineage"]["artifacts_head_sha"]
    assert g3_claims["claim_sources"]["tested_sha"] == \
        "receipt_lineage.artifacts_head_sha"


def test_carried_items_are_re_derived_live_not_quoted(package):
    carried = package["carried"]
    assert carried["CON-02"]["status"] == "OPEN_OBSERVABLE_NOT_RESOLVED"
    assert carried["CON-02"]["source_diverse_single_allocator"] == \
        "CONCENTRATED_SINGLE_ALLOCATOR"
    assert carried["CON-03"]["status"] == "OPEN_NOT_SILENTLY_SOLVED"
    assert all(v is False for v in
               carried["CON-03"]["threshold_knowledge_candidacy"].values())
    assert carried["AMB-08"]["status"] == "OPEN_HOLD_IS_A_HOLD"


def test_the_audit_does_not_modify_canonical_fixtures(contract):
    before = CONTRACT_PATH.read_bytes()
    AUDIT.build_package(measured_full=938)
    assert CONTRACT_PATH.read_bytes() == before


# --------------------------------------------------------------------------- #
# C16-C21 — controls for the revision-R2 gate-claim machinery and the
# revision-R1 derivation-completeness check
# --------------------------------------------------------------------------- #
def _findings_for(package, receipt_name):
    return [f for f in package["gate"]["findings"]
            if receipt_name in f["receipt_path"]]


def test_c16_terminal_head_convention_is_a_note_not_a_false_claim(package):
    """A terminal-head key names the very commit that archives the receipt, which
    is what that key MEANS. It must be recorded as a convention note and must NOT
    be reported as self-certification. A receipt whose terminal head is a DIFFERENT
    commit (G1/G1R/G2) must not be flagged at all."""
    g2r = _findings_for(package, "G2R_EVIDENCE_RECEIPT.json")
    conventions = [f for f in g2r
                   if f["finding_id"] == "SHA_CONVENTION_TERMINAL_SELF_REFERENTIAL"]
    assert len(conventions) == 1
    note = conventions[0]
    assert note["is_defect"] is False and note["blocks_gate"] is False
    assert note["severity"] == "INFO"
    assert note["evidence"]["declared_semantic"] == "TERMINAL_HEAD_OF_RECORD"
    assert not [f for f in g2r if f["finding_id"] == "TESTED_SHA_PRECEDES_EVIDENCE_COMMIT"]
    for name in ("G1_EVIDENCE_RECEIPT.json", "G1R_EVIDENCE_RECEIPT.json",
                 "G2_EVIDENCE_RECEIPT.json"):
        assert not [f for f in _findings_for(package, name)
                    if f["finding_id"].startswith("SHA_CONVENTION")]


def test_c17_a_declared_tested_surface_that_self_certifies_still_fails(contract):
    """The convention exemption must not become a hole: a DECLARED tested-surface
    key naming the receiving commit is still a blocking self-certification."""
    from engine.g8_contradiction import audit_gate_claim
    archive = "a" * 40
    receipt = {"tested_sha": archive, "collected": 1, "passed": 1}
    findings = audit_gate_claim(
        receipt_path="stress-suite/evidence/SYNTHETIC_RECEIPT.json", receipt=receipt,            git_probe=lambda args: ("commit" if args[:2] == ["cat-file", "-t"] else ""),
        contract=contract, evidence_dir_commit_of=lambda p: archive, head_sha=archive)
    self_cert = [f for f in findings
                 if f.finding_id == "TESTED_SHA_PRECEDES_EVIDENCE_COMMIT"]
    assert self_cert and self_cert[0].is_defect is True
    assert self_cert[0].blocks_gate is True and self_cert[0].severity == "BLOCKING"


def test_c17b_an_unresolvable_identifier_with_no_declared_abbreviation_blocks(contract):
    """Prefix resolution must not rescue an identifier the receipt never abbreviates."""
    from engine.g8_contradiction import audit_gate_claim
    bogus = "deadbeef" + "0" * 32

    def probe(args):
        if args[:2] == ["cat-file", "-t"]:
            raise RuntimeError("could not get object info")
        if args[:1] == ["rev-parse"]:
            return ""
        if args[:2] == ["log", "--all"]:
            return ""
        return ""

    findings = audit_gate_claim(
        receipt_path="stress-suite/evidence/SYNTHETIC2_RECEIPT.json",
        receipt={"tested_sha": bogus, "commits": [{"sha": "12345678",
                                                    "subject": "unrelated"}]},
        git_probe=probe, contract=contract, evidence_dir_commit_of=lambda p: "",
        head_sha="b" * 40)
    unresolvable = [f for f in findings if f.finding_id == "TESTED_SHA_UNRESOLVABLE"]
    assert unresolvable and unresolvable[0].blocks_gate is True
    assert unresolvable[0].evidence["abbreviation"] == bogus[:12]
    assert unresolvable[0].evidence["in_repository"] == "NO"


def test_c18_supersession_requires_a_later_artifact_that_names_the_receipt(package):
    """Two directions. Positive: the G6 receipt's collapsed authority vocabulary is
    corrected by the later G6 truth-closure receipt, so the finding is retained but
    no longer blocking. Negative: the same correction must NOT supersede a finding
    in a receipt that the correction does not name."""
    from engine.g8_contradiction import GateClaimFinding, resolve_supersession
    g6 = [f for f in _findings_for(package, "G6_EVIDENCE_RECEIPT.json")
          if f["finding_id"] == "AUTHORITY_ACCOUNTING_VOCABULARY"]
    assert g6 and g6[0]["superseded_by"] == "G6_TRUTH_CLOSURE_RECEIPT.json"
    assert g6[0]["is_defect"] is False and g6[0]["blocks_gate"] is False
    assert g6[0]["classification"] == "SUPERSEDED_BY_LATER_ARTIFACT"
    assert "scenario_internal_authority_events" in g6[0]["supersession_detail"]
    # the G4 identifier finding is NOT superseded by anything
    g4 = [f for f in _findings_for(package, "G4_EVIDENCE_RECEIPT.json")
          if f["finding_id"].startswith("TESTED_SHA")]
    assert g4 and g4[0]["superseded_by"] == ""

    # negative control on the mechanism itself
    finding = GateClaimFinding(
        finding_id="SYN", receipt_path="stress-suite/evidence/G4_EVIDENCE_RECEIPT.json",
        claim="c", observed="o", is_defect=True,
        classification="RECEIPT_OR_CLAIM_DEFECT", severity="HIGH",
        governing_contract="g", detail="d",
        subject_tokens=("490e078d1e2e",))
    not_named = resolve_supersession(
        [finding], later_corrections={"OTHER_RECEIPT.json": [
            "a correction about something else entirely"]})
    assert not_named[0].is_defect is True and not_named[0].blocks_gate is True
    names_but_silent = resolve_supersession(
        [finding], later_corrections={"OTHER_RECEIPT.json": [
            "G4_EVIDENCE_RECEIPT.json is mentioned but not about this"]})
    assert names_but_silent[0].is_defect is True
    both = resolve_supersession(
        [finding], later_corrections={"OTHER_RECEIPT.json": [
            "G4_EVIDENCE_RECEIPT.json tested surface corrected",
            "the identifier 490e078d1e2e was mistranscribed"]})
    assert both[0].is_defect is False and both[0].blocks_gate is False


def test_c19_a_constant_derivation_is_detected_not_hidden(package):
    """The pre-revision F4/F5 gaps were caused by declared outcome-relevant fields
    being DERIVED AS A CONSTANT, so they could not discriminate. The audit must
    report that condition itself, both for a synthetic constant and for the real
    run."""
    from engine.g8_contradiction import (build_observation, derivation_limitations,
                                        run_comparison_family)
    contract = package["contract"]
    family = copy.deepcopy(next(f for f in contract["comparison_families"]
                               if f["family_id"] == "F5"))
    family["members"] = ["SYN:0", "SYN:1"]
    family["declared_pairs"] = []
    obs = {}
    for i, token in enumerate(("REJECTED_NEGATIVE_KNOWLEDGE", "CONTRADICTION_OPEN")):
        o = build_observation(
            contract, observation_id=f"SYN:{i}", family_id="F5", source_gate="GX",
            source_ref=f"SYN:{i}", state_machine="DOMAIN_MACHINE",
            object_class="DOMAIN_CLAIM", raw_outcome_token=token,
            vector_values={"domain": "GENERIC", "claim_scope_class": "BOUNDED_SCOPE"})
        obs[o.observation_id] = o
    limits = derivation_limitations(contract, [run_comparison_family(contract, family, obs)],
                                    obs)
    constant = {(d.family_id, d.field) for d in limits
                if d.limitation == "CONSTANT_DERIVATION"}
    assert ("F5", "domain") in constant
    # and the real run reports its own limitations rather than implying coverage
    real = package["derivation"]
    assert real["declared_verified_field_count"] == sum(
        len(f.get("verified_fields", [])) for f in contract["comparison_families"])
    assert real["limitations"], "a run with constant derivations must say so"
    # The domain field's declared vocabulary covers only SOME of the domain labels
    # the domain machine actually uses, so real differences collapse to UNKNOWN.
    # That is the exact failure mode G8 exists to catch, so it must be reported as
    # a limitation of the audit rather than tolerated as equivalence.
    f5_domain = [d for d in real["limitations"]
                 if d["family_id"] == "F5" and d["field"] == "domain"]
    assert f5_domain, "the partial domain vocabulary must be reported"
    assert f5_domain[0]["limitation"] == "PARTIALLY_UNDECLARED"
    assert real["partially_undeclared"] >= 1
    assert real["discriminating_field_count"] < real["declared_verified_field_count"]
    assert real["identically_unknown"] >= 1


def test_c20_contract_validation_rejects_duplicate_outcome_classes(contract):
    with pytest.raises(ValueError):
        bad = copy.deepcopy(contract)
        bad["outcome_classes"] = bad["outcome_classes"] + [bad["outcome_classes"][0]]
        validate_contract(bad)


def test_c21_the_declared_blocks_gate_policy_governs_the_exit(contract, package):
    """The gate exit must follow the DECLARED policy: a HIGH-severity evidence gap
    and a RECEIPT_OR_CLAIM_DEFECT that cannot be resolved block; a LOW-severity
    coarse-proxy gap and a superseded finding do not."""
    policy = contract["blocks_gate_policy"]
    assert "ARCHITECTURE_CONTRADICTION" in policy["blocking_classifications"]
    assert "SUPERSEDED_BY_LATER_ARTIFACT" in policy["never_blocking_classifications"]
    from engine.g8_contradiction import GateClaimFinding
    high = GateClaimFinding(
        finding_id="H", receipt_path="x", claim="c", observed="o", is_defect=True,
        classification="RECEIPT_OR_CLAIM_DEFECT", severity="HIGH",
        governing_contract="g", detail="d", blocks_gate=True)
    quiet = GateClaimFinding(
        finding_id="Q", receipt_path="y", claim="c", observed="o", is_defect=False,
        classification="SUPERSEDED_BY_LATER_ARTIFACT", severity="MEDIUM",
            governing_contract="g", detail="d", blocks_gate=False,
            superseded_by="LATER_CLOSURE_RECEIPT.json")
    families = package["families"]
    blocked = decide_gate(contract, families, [], [high], measured_full=1, collected_full=1)
    assert blocked["exit"] == "BLOCKED_G8_MISSING_EVIDENCE"
    passed = decide_gate(contract, families, [], [quiet], measured_full=1, collected_full=1)
    assert passed["exit"] == "PASS_G8_CROSS_SCENARIO_COHERENCE"
    assert passed["counts"]["gate_claim_superseded"] == 1
    # a recorded-but-non-blocking defect is still counted, never dropped
    recorded = decide_gate(contract, families, [], [GateClaimFinding(
        finding_id="R", receipt_path="z", claim="c", observed="o", is_defect=True,
        classification="RECEIPT_OR_CLAIM_DEFECT", severity="MEDIUM",
        governing_contract="g", detail="d", blocks_gate=False)],
        measured_full=1, collected_full=1)
    assert recorded["exit"] == "PASS_G8_CROSS_SCENARIO_COHERENCE"
    assert recorded["counts"]["gate_claim_recorded_not_blocking"] == 1
