"""G8 — cross-scenario contradiction audit regressions + adversarial controls.

Covers the §9 mandatory controls C01-C15 of the G8 master prompt, the mandated
comparison families of §7, and the gate-claim audit of §7 (cross-gate claims).

Every control proves the AUDIT can detect its own failure mode. Nothing here
alters canonical S01-S24 fixtures: the negative control builds its own synthetic
family on a COPY of the frozen contract.
"""
from __future__ import annotations

import copy
import inspect
import json
import re
import subprocess
import sys
from dataclasses import replace
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
from engine.g8_test_evidence import (  # noqa: E402
    ARTIFACT_CANONICALIZATION_RULE,
    ARTIFACT_RELATIVE_PATH,
    CANONICALIZATION_RULE_NOTES,
    CANONICALIZATION_RULES,
    UnverifiableTestEvidence,
    canonical_junit_bytes,
    canonical_rule,
    canonical_rule_fingerprint,
    check_baseline,
    junit_document,
    read_test_evidence,
    verify_citation,
)
#: the tested tree has ONE owner (STRESS-G8ARCH3); the tests consume it, they do not
#: derive it
from scenarios.g8_tested_tree import derived_tested_tree  # noqa: E402
from engine.g8_contradiction import (  # noqa: E402
    DERIVATION_KINDS,
    ComparisonResult,
    FamilyAuditResult,
    GuardedContractError,
    GuardedPropertyValue,
    check_guarded_properties,
    validate_guarded_finding,
)
from engine.g8_chronology import (  # noqa: E402
    STAGES,
    ChronologyError,
    validate_chronology,
)
import g8_guarded as GP  # noqa: E402
from engine.registry import EvidenceRegistry  # noqa: E402

import g8_run_audit as AUDIT  # noqa: E402
import g8_concept_projection as CP  # noqa: E402
import g8_emit_evidence as EMIT  # noqa: E402
import g8_pre_repair_red_transcript as RED  # noqa: E402
import g8_arch_red_transcript as ARCH  # noqa: E402
import g8_closure_evidence as CLOSURE  # noqa: E402
from engine.g8_contradiction import GuardedPropertyFinding  # noqa: E402

CONTRACT_PATH = ROOT / "evidence" / "G8_EQUIVALENCE_CONTRACT.json"


@pytest.fixture(scope="module")
def contract() -> Dict[str, Any]:
    return load_contract(CONTRACT_PATH)


@pytest.fixture(scope="module")
def sealed_test_evidence(tmp_path_factory) -> Any:
    """A SEALED JUnit fixture document, so the regressions never re-invoke pytest
    inside pytest. The authoritative package build consumes a live artifact; a unit
    test consumes a document it fully controls.

    It is bound to the tree the emitter DECLARES (`EMIT.TESTED_SHA`), exactly as
    the authoritative artifact is, so the gate's baseline check compares a
    declared tree against a bound tree rather than against itself.
    """
    root = tmp_path_factory.mktemp("g8ev")
    path = root / ARTIFACT_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(junit_document(cases=973, tested_sha=EMIT.TESTED_SHA),
                    encoding="utf-8")
    # the fixture declares THIS temporary directory as its tree, which is what
    # makes the citation checkable, and it uses the one declared evidence path so
    # it exercises the same rule the authoritative build does. The authoritative
    # build declares the repository, so its citation is a repo-relative path a
    # reviewer can resolve (R-G8-07).
    return read_test_evidence(str(path), expected_tested_sha=EMIT.TESTED_SHA,
                              repo_root=root,
                              python_version=sys.version.split()[0])


@pytest.fixture(scope="module")
def package(sealed_test_evidence) -> Dict[str, Any]:
    return AUDIT.build_package(test_evidence=sealed_test_evidence,
                              expected_tested_sha=sealed_test_evidence.tested_sha)


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
def test_c14_report_generation_is_byte_reproducible(sealed_test_evidence):
    first = json.dumps(AUDIT.build_package(
        test_evidence=sealed_test_evidence,
        expected_tested_sha=sealed_test_evidence.tested_sha)["register"],
                       sort_keys=True)
    second = json.dumps(AUDIT.build_package(
        test_evidence=sealed_test_evidence,
        expected_tested_sha=sealed_test_evidence.tested_sha)["register"],
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
    assert len(package["observations"]) == 35
    for obs in package["observations"]:
        assert obs.outcome_mapped, (obs.observation_id, obs.raw_outcome_token)
        assert obs.outcome_class, obs.observation_id


def test_every_mandated_comparison_pair_was_substantively_adjudicated(package):
    """R-G8-01: coverage is a SUBSTANTIVE verdict, never merely invoking the
    comparator. A mandatory pair whose only comparison was NOT_COMPARABLE, or which
    was never compared, must appear in `uncovered_mandated_pairs`."""
    coverage = package["mandated_coverage"]
    assert coverage["uncovered_mandated_pairs"] == []
    assert coverage["mandated_pairs"] > 0
    assert coverage["mandated_pairs_substantively_adjudicated"] == coverage["mandated_pairs"]
    assert coverage["mandated_comparisons_observed"] == coverage["mandated_pairs"]


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
                  if e["kind"] in ("COMPARISON_CONTRADICTION",
                                   "DIAGNOSTIC_NON_COMPARABILITY")}
    for cls in build_equivalence_classes(package["observations"]):
        if cls.coherent or len(cls.members) < 2:
            continue
        pair = frozenset(cls.members)
        assert (cls.family_id, pair) in registered, cls.to_dict()


def test_no_observation_pair_was_compared_across_state_machines(package):
    for fam in package["families"]:
        for cmp in fam.comparisons:
            if cmp.verdict == "NOT_COMPARABLE":
                assert ("different state machines" in cmp.reason
                        or "diagnostic family" in cmp.reason), cmp.reason


def test_gate_decision_is_derived_from_the_counts_not_asserted(package):
    decision = package["decision"]
    assert decision["counts"]["blocking_contradictions"] == 0
    assert decision["counts"]["guarded_violations"] == 0
    blocking = (decision["counts"]["gate_claim_blocking"]
                + decision["counts"]["evidence_gaps"]
                + decision["counts"]["mandated_not_adjudicated"]
                + decision["counts"]["unexercised_required_properties"])
    if blocking or decision["counts"]["blocking_contradictions"]:
        assert decision["exit"] != "PASS_G8_CROSS_SCENARIO_COHERENCE"
    assert decision["mandated"]["uncovered"] == []
    # 'no detected violation' is not 'property proved'
    assert decision["counts"]["unexercised_required_properties"] == 0
    assert decision["counts"]["mandated_not_adjudicated"] == 0
    # and the baseline is only certified by a verified artifact
    assert decision["baseline"]["verified"] is True


def test_gate_claim_audit_locates_each_receipt_surface_and_recomputes_lineage(package):
    gate = package["gate"]
    assert gate["receipts_audited"], "no receipts audited"
    lineage = gate["count_lineage"]
    # the declared lineage is checked on its own terms: the prior gates terminate at
    # the inherited count, the chain is monotone and carries no arithmetic defect.
    # Whether the LIVE count equals the declared terminal is recorded separately
    # (a gate that adds tests legitimately differs from its predecessor's terminal).
    assert lineage["terminal_declared_full"] == 938
    assert lineage["monotone"] is True
    assert lineage["arithmetic_defects"] == []
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


def test_c22_the_audit_excludes_its_own_gate_receipt(package):
    """A gate may not audit its own package as a completed prior gate, and its own
    output must not change the input it audits — otherwise evidence generation is
    self-referential and stops being reproducible."""
    gate = package["gate"]
    assert "G8_EVIDENCE_RECEIPT.json" not in gate["receipts_audited"]
    assert all(not n.startswith("G8_") for n in gate["receipts_audited"])
    assert "G8_EVIDENCE_RECEIPT.json" in gate["own_receipts_excluded"]
    assert all(not str(e["gate"]).startswith("G8") for e in gate["count_lineage"]["chain"])
    assert gate["count_lineage"]["chain"], "the prior-gate lineage must not be empty"


def test_c14_the_emitted_evidence_package_is_byte_reproducible(
        tmp_path, monkeypatch, sealed_test_evidence):
    """Two consecutive generator runs must produce byte-identical artifacts, and
    the generator must carry no wall-clock field.

    The test redirects the generator at a TEMPORARY directory: a test must never
    rewrite the shipped evidence package with a different measured count, or the
    artifact under review stops matching the run that produced it."""
    import scenarios.g8_emit_evidence as EMIT
    shipped = {p.name: p.read_bytes() for p in (ROOT / "evidence").glob("G8_*")}
    monkeypatch.setattr(EMIT, "EVIDENCE", tmp_path)
    first = EMIT.emit(sealed_test_evidence)
    digests = {p.name: p.read_bytes() for p in tmp_path.glob("G8_*")}
    EMIT.emit(sealed_test_evidence)
    for name, before in digests.items():
        assert (tmp_path / name).read_bytes() == before, name
    source = (ROOT / "scenarios" / "g8_emit_evidence.py").read_text(encoding="utf-8")
    for forbidden in ("datetime", "time.time", "utcnow", "recorded_utc",
                      "strftime"):
        assert forbidden not in source, forbidden
    assert first["receipt"]["collected"] == sealed_test_evidence.collected
    assert first["decision"]["exit"] == "PASS_G8_CROSS_SCENARIO_COHERENCE"
    # the shipped package is untouched by the test
    for name, before in shipped.items():
        assert (ROOT / "evidence" / name).read_bytes() == before, name


def test_the_audit_does_not_modify_canonical_fixtures(contract, sealed_test_evidence):
    before = CONTRACT_PATH.read_bytes()
    AUDIT.build_package(test_evidence=sealed_test_evidence,
                       expected_tested_sha=sealed_test_evidence.tested_sha)
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


def test_c21_the_declared_blocks_gate_policy_governs_the_exit(
        contract, package, sealed_test_evidence):
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
    obs = package["observations"]
    guarded = [g for fam in families for g in fam.guarded]
    declared = sealed_test_evidence.tested_sha
    blocked = decide_gate(contract, families, guarded, [high],
                          test_evidence=sealed_test_evidence,
                          expected_tested_sha=declared, observations=obs)
    assert blocked["exit"] == "BLOCKED_G8_MISSING_EVIDENCE"
    passed = decide_gate(contract, families, guarded, [quiet],
                         test_evidence=sealed_test_evidence,
                         expected_tested_sha=declared, observations=obs)
    assert passed["exit"] == "PASS_G8_CROSS_SCENARIO_COHERENCE"
    assert passed["counts"]["gate_claim_superseded"] == 1
    # a recorded-but-non-blocking defect is still counted, never dropped
    recorded = decide_gate(contract, families, guarded, [GateClaimFinding(
        finding_id="R", receipt_path="z", claim="c", observed="o", is_defect=True,
        classification="RECEIPT_OR_CLAIM_DEFECT", severity="MEDIUM",
        governing_contract="g", detail="d", blocks_gate=False)],
        test_evidence=sealed_test_evidence, expected_tested_sha=declared,
        observations=obs)
    assert recorded["exit"] == "PASS_G8_CROSS_SCENARIO_COHERENCE"
    assert recorded["counts"]["gate_claim_recorded_not_blocking"] == 1
    # R-G8-05/R-G8RX6 F2: an EMPTY guarded-property surface proves nothing, so the
    # gate must block instead of passing by absence of a violation
    empty = decide_gate(contract, families, [], [quiet],
                        test_evidence=sealed_test_evidence,
                        expected_tested_sha=declared, observations=obs)
    assert empty["exit"] == "BLOCKED_G8_MISSING_EVIDENCE"
    assert empty["counts"]["unexercised_required_properties"] == len(
        contract["closure_required_properties"])


# =========================================================================== #
# STRESS-G8R0 — the adversarial controls the closure review requires, one group
# per finding. Every one of them was proved RED against 6c015f86 before the
# repair; that red transcript is archived in G8_CONTRADICTION_REGISTER.json.
# =========================================================================== #
def _declared_pairs(contract, family_id):
    return next(f for f in contract["comparison_families"]
                if f["family_id"] == family_id)["declared_pairs"]


def test_r01_mandatory_not_comparable_is_not_coverage(contract, package):
    """R-G8-01 RED BEFORE REPAIR: F2 reported 20/20 mandated coverage and the gate
    PASSED while five mandated pairs returned NOT_COMPARABLE. Invoking the
    comparator is not coverage."""
    fam = next(f for f in package["families"] if f.family_id == "F2")
    pair = sorted(_declared_pairs(contract, "F2")[0])
    comp = ComparisonResult(
        comparison_id="SYN:NC", family_id="F2", left_id=pair[0], right_id=pair[1],
        left_ref=pair[0], right_ref=pair[1], verdict="NOT_COMPARABLE",
        reason="SYNTHETIC CONTROL: terminal vocabularies differ",
        differing_fields=(), mandated=True)
    cov = mandated_pair_coverage(contract, [replace(fam, comparisons=(comp,))])
    assert cov["mandated_comparisons_observed"] >= 1
    assert cov["mandated_pairs_substantively_adjudicated"] == 0
    assert cov["mandated_pairs_not_comparable"]
    entry = [e for e in cov["uncovered_mandated_pairs"]
             if e["family_id"] == "F2" and pair[0] in e["pair"]]
    assert entry, "a NOT_COMPARABLE mandated pair must be reported UNCOVERED"
    assert "NOT_COMPARABLE" in entry[0]["verdicts"]


def test_r01_a_mandated_pair_never_compared_blocks_the_gate(
        contract, package, sealed_test_evidence):
    """R-G8-01: dropping every comparison leaves mandated relationships
    unadjudicated, and the gate must block instead of passing."""
    stripped = [replace(f, comparisons=()) for f in package["families"]]
    guarded = [g for f in package["families"] for g in f.guarded]
    decision = decide_gate(contract, stripped, guarded, [],
                           test_evidence=sealed_test_evidence,
                           expected_tested_sha=sealed_test_evidence.tested_sha,
                           observations=package["observations"])
    assert decision["exit"] == "BLOCKED_G8_MISSING_EVIDENCE"
    assert decision["counts"]["mandated_not_adjudicated"] > 0
    assert any("not substantively adjudicated" in r for r in decision["reasons"])


def test_r01_the_live_package_adjudicates_every_mandated_pair(contract, package):
    """The repaired audit must substantively adjudicate every mandated pair, or
    report it as an uncovered evidence gap. Neither is a silent equivalence."""
    cov = mandated_pair_coverage(contract, package["families"])
    live = package["mandated_coverage"]
    assert cov["mandated_pairs"] == live["mandated_pairs"]
    assert (cov["mandated_pairs_substantively_adjudicated"]
            + len(cov["uncovered_mandated_pairs"]) == cov["mandated_pairs"])
    assert live["uncovered_mandated_pairs"] == []
    assert live["mandated_pairs_substantively_adjudicated"] == live["mandated_pairs"]
    assert live["mandated_pairs_not_comparable"] == []


def test_r02_p5_tautology_is_gone(contract):
    """R-G8-02 RED BEFORE REPAIR: p5({'profit': 10, 'items': [{'disposition':
    'VALIDATED'}]}) returned True. The shape lives in the real contract so the
    control and the derivation stay in step."""
    red = contract["pre_repair_red_register"]["red_before_repair"]
    # the exact surface that used to return True: it cannot DEMONSTRATE the
    # relation, so the honest post-repair answer is unknown, never HOLDS
    minimal = GP.p5_profit_did_not_weaken_validation(red["R-G8-02_p5_adverse_surface"])
    assert minimal.verdict() == "UNKNOWN_NOT_FAVORABLE"
    assert minimal.verdict() != "HOLDS"
    assert red["R-G8-02_post_repair_expected"].startswith("UNKNOWN_NOT_FAVORABLE")
    # and once the profit-bearing claim is identifiable, the same construction
    # that reached VALIDATED with no gate surface is a VIOLATION
    identified = GP.p5_profit_did_not_weaken_validation(
        red["R-G8-02_p5_identified_surface"])
    assert identified.verdict() == "VIOLATED"
    assert identified.derivation_kind == "DIRECT_TRACE"


def test_r02_p5_holds_only_on_an_exercised_gate_surface():
    gp = GP.p5_profit_did_not_weaken_validation({
        "profit": 10,
        "items": [{"candidate_id": "CAND_1", "disposition": "REJECTED",
                   "gate_vector": [{"gate_id": "G1", "passed": False,
                                    "material": True}]}]})
    assert gp.verdict() == "HOLDS"
    assert gp.derivation_kind == "DIRECT_TRACE"
    quiet = GP.p5_profit_did_not_weaken_validation({"items": [{"disposition": "FLAGGED"}]})
    assert quiet.verdict() == "UNKNOWN_NOT_FAVORABLE"


def test_r03_p7_unknown_and_key_names_are_not_provenance(contract):
    """R-G8-03 RED BEFORE REPAIR: {'evidence_provenance': 'UNKNOWN',
    'evidence_lineage': 'UNKNOWN'} returned True."""
    surface = contract["pre_repair_red_register"]["red_before_repair"][
        "R-G8-03_provenance_adverse_surface"]
    gp = GP.p7_provenance_preserved(surface)
    assert gp.verdict() == "UNKNOWN_NOT_FAVORABLE"
    assert gp.derivation_kind == "NOT_DERIVABLE"
    key_names_only = GP.p7_provenance_preserved({
        "attached_references": ["UNKNOWN", ""], "retained_references": ["UNKNOWN"]})
    assert key_names_only.verdict() == "UNKNOWN_NOT_FAVORABLE"
    dropped = GP.p7_provenance_preserved({
        "attached_references": ["EV_1", "EV_2"], "retained_references": ["EV_1"]})
    assert dropped.verdict() == "VIOLATED"
    kept = GP.p7_provenance_preserved({
        "attached_references": ["EV_1"], "retained_references": ["EV_1"]})
    assert kept.verdict() == "HOLDS"


def test_r04_p11_scenario_identity_cannot_derive_runtime_neutrality(contract):
    """R-G8-04 RED BEFORE REPAIR: g4_runtime_neutral('S13') and
    g4_runtime_neutral('S99_NO_SUCH_SCENARIO') BOTH returned True."""
    for sid in ("S13", "S99_NO_SUCH_SCENARIO", ""):
        gp = GP.p11_runtime_identity_not_semantic({"scenario_id": sid})
        assert gp.verdict() == "UNKNOWN_NOT_FAVORABLE", sid
    assert contract["pre_repair_red_register"]["red_before_repair"][
        "R-G8-04_scenario_identifier"] == "S13"


def test_r04_p11_unpaired_and_mismatched_runtime_replacements():
    unpaired = GP.p11_runtime_identity_not_semantic({
        "runtime_pairs": [{"artifact_id": "ART_1", "baseline_runtime": "RUNTIME_A",
                           "replacement_runtime": "RUNTIME_A",
                           "baseline_fingerprint": "FP_1",
                           "replacement_fingerprint": "FP_1"}]})
    assert unpaired.verdict() == "UNKNOWN_NOT_FAVORABLE"
    mismatched = GP.p11_runtime_identity_not_semantic({
        "runtime_pairs": [{"artifact_id": "ART_1", "baseline_runtime": "RUNTIME_A",
                           "replacement_runtime": "RUNTIME_B",
                           "baseline_fingerprint": "FP_1",
                           "replacement_fingerprint": "FP_2",
                           "semantic_fingerprint_equal": False}]})
    assert mismatched.verdict() == "VIOLATED"
    paired = GP.p11_runtime_identity_not_semantic({
        "runtime_pairs": [{"artifact_id": "ART_1", "baseline_runtime": "RUNTIME_A",
                           "replacement_runtime": "RUNTIME_B",
                           "baseline_fingerprint": "FP_1",
                           "replacement_fingerprint": "FP_1",
                           "semantic_fingerprint_equal": True}]})
    assert paired.verdict() == "HOLDS"
    assert paired.derivation_kind == "PAIRED_COUNTERFACTUAL"


def test_r05_p1_a_refusal_elsewhere_is_not_an_authority_proof():
    """R-G8-05 RED BEFORE REPAIR: P1 returned HOLDS whenever any refusal was
    observed. An ungoverned escalation earlier in the same trace must still be a
    violation."""
    gp = GP.p1_authority_not_escalated({
        "authority_before": {"ACTOR_1": "WORKER"},
        "authority_after": {"ACTOR_1": "OPERATOR"},
        "authority_events": {"refusals": 1},
        "applied_escalations": [{"event": "EV_ESCALATE",
                                 "authorized_by_governed_basis": False}]})
    assert gp.verdict() == "VIOLATED"
    assert gp.derivation_kind == "CANONICAL_STATE_COMPARISON"
    governed = GP.p1_authority_not_escalated({
        "authority_before": {"ACTOR_1": "WORKER"},
        "authority_after": {"ACTOR_1": "OPERATOR"},
        "authority_events": {"ratifications": 1},
        "governed_basis": ["GRANT_1"],
        "applied_escalations": [{"event": "EV_ESCALATE",
                                 "authorized_by_governed_basis": True}]})
    assert governed.verdict() == "HOLDS"


def test_r05_p8_capability_caused_authority_change_is_a_violation():
    gp = GP.p8_capability_not_authority({
        "capability_changes": [{"worker_id": "WORKER_1",
                                "reliability_before": 0.4,
                                "reliability_after": 0.9}],
        "authority_before": {"WORKER_1": "WORKER"},
        "authority_after": {"WORKER_1": "OPERATOR"},
        "escalation_basis_texts": ["capability improved"]})
    assert gp.verdict() == "VIOLATED"
    assert gp.derivation_kind == "PAIRED_COUNTERFACTUAL"
    unchanged = GP.p8_capability_not_authority({
        "capability_changes": [{"worker_id": "WORKER_1",
                                "reliability_before": 0.4,
                                "reliability_after": 0.9}],
        "authority_before": {"WORKER_1": "WORKER"},
        "authority_after": {"WORKER_1": "WORKER"}})
    assert unchanged.verdict() == "HOLDS"


def test_r05_p9_availability_caused_empirical_change_is_a_violation():
    gp = GP.p9_operator_availability_not_empirical({
        "availability_pair": {
            "available": {"action_verdict": "EXECUTE",
                          "evidence_projection": {"GRADE": "STRONG"},
                          "evidence_refs": ["EV_1"]},
            "unavailable": {"action_verdict": "HOLD",
                            "evidence_projection": {"GRADE": "WEAK"},
                            "evidence_refs": ["EV_1"]}}})
    assert gp.verdict() == "VIOLATED"
    unchanged = GP.p9_operator_availability_not_empirical({
        "availability_pair": {
            "available": {"action_verdict": "EXECUTE",
                          "evidence_projection": {"GRADE": "STRONG"},
                          "evidence_refs": ["EV_1"]},
            "unavailable": {"action_verdict": "HOLD",
                            "evidence_projection": {"GRADE": "STRONG"},
                            "evidence_refs": ["EV_1"]}}})
    assert unchanged.verdict() == "HOLDS"


def test_r06_p6_raw_count_over_one_lineage_is_a_violation():
    """R-G8-06: the derivation must inspect the ACTUAL disposition, not merely
    observe that several reviewers existed."""
    gp = GP.p6_count_did_not_create_transformation({
        "raw_reviewer_count": 10, "distinct_source_lineages": 1,
        "disposition": "TRANSFORMATION_ADMITTED",
        "claim_id": "CLAIM_1", "policy_id": "POLICY_1"})
    assert gp.verdict() == "VIOLATED"
    assert gp.derivation_kind == "DIRECT_TRACE"
    held = GP.p6_count_did_not_create_transformation({
        "raw_reviewer_count": 10, "distinct_source_lineages": 1,
        "disposition": "REVIEW_OPEN",
        "claim_id": "CLAIM_1", "policy_id": "POLICY_1"})
    assert held.verdict() == "HOLDS"


def test_r05_a_holds_finding_without_derivation_evidence_is_rejected():
    for kwargs in ({"derivation_kind": "NOT_DERIVABLE", "evidence_refs": ("X",)},):
        with pytest.raises(GuardedContractError):
            validate_guarded_finding(GuardedPropertyFinding(
                property_id="P8", property_name="capability is not authority",
                governing_contract="g", observation_id="O", family_id="F1",
                value=True, verdict="HOLDS", before_state="a", after_state="b",
                decision_surface="s", reason="r", **kwargs))
    with pytest.raises(GuardedContractError):
        validate_guarded_finding(GuardedPropertyFinding(
            property_id="P1", property_name="no authority escalation",
            governing_contract="g", observation_id="O", family_id="F1",
            value=True, verdict="HOLDS",
            derivation_kind="CANONICAL_STATE_COMPARISON",
            evidence_refs=(), before_state="a", after_state="b",
            decision_surface="s", reason="r"))


def test_r05_a_bare_boolean_cannot_certify_a_guarded_property(contract):
    obs = _obs(contract, "SYN:BARE", guarded_properties={"P1": True})
    with pytest.raises(GuardedContractError):
        check_guarded_properties(contract, [obs])


# --------------------------------------------------------------------------- #
# R-G8-07 — a test count must be a provenance-bearing artifact, never a scalar
# --------------------------------------------------------------------------- #
def test_r07_the_emitter_cannot_consume_a_bare_count():
    """R-G8-07 RED BEFORE REPAIR: the emitter signature was
    `emit(measured_full: int)` and built collected=passed=that number, failed=0.
    A bare integer can no longer certify anything."""
    params = inspect.signature(EMIT.emit).parameters
    assert list(params) == ["test_evidence"]
    assert params["test_evidence"].annotation is not inspect.Parameter.empty
    for n in (1, 973, 9999):
        with pytest.raises((TypeError, AttributeError)):
            EMIT.emit(n)


def test_r07_absent_failing_stale_and_malformed_artifacts_all_refuse(tmp_path):
    sha = AUDIT.head_sha()
    with pytest.raises(UnverifiableTestEvidence):
        read_test_evidence(str(tmp_path / "absent.xml"), expected_tested_sha=sha)

    def _write(name, text):
        p = tmp_path / name
        p.write_text(text, encoding="utf-8")
        return p

    failing = _write("fail.xml", junit_document(cases=5, tested_sha=sha, failures=1))
    with pytest.raises(UnverifiableTestEvidence):
        read_test_evidence(str(failing), expected_tested_sha=sha)
    other_tree = _write("other.xml", junit_document(cases=5, tested_sha="deadbeef"))
    with pytest.raises(UnverifiableTestEvidence):
        read_test_evidence(str(other_tree), expected_tested_sha=sha)
    wrong_suite = _write("suite.xml", junit_document(cases=5, name="unrelated_suite",
                                                    tested_sha=sha))
    with pytest.raises(UnverifiableTestEvidence):
        read_test_evidence(str(wrong_suite), expected_tested_sha=sha)
    malformed = _write("bad.xml", "<not-a-testsuite/>")
    with pytest.raises(UnverifiableTestEvidence):
        read_test_evidence(str(malformed), expected_tested_sha=sha)
    empty = _write("empty.xml", "   ")
    with pytest.raises(UnverifiableTestEvidence):
        read_test_evidence(str(empty), expected_tested_sha=sha)
    counts_mismatch = _write("counts.xml", junit_document(cases=5, tested_sha=sha)
                             .replace('tests="5"', 'tests="9"'))
    with pytest.raises(UnverifiableTestEvidence):
        read_test_evidence(str(counts_mismatch), expected_tested_sha=sha)
    stale = _write("stale.xml", junit_document(cases=5, tested_sha=sha))
    with pytest.raises(UnverifiableTestEvidence):
        read_test_evidence(str(stale), expected_tested_sha=sha,
                           expected_artifact_digest="0" * 64)


def test_r07_a_clean_artifact_yields_a_verifiable_baseline(tmp_path):
    sha = AUDIT.head_sha()
    p = tmp_path / ARTIFACT_RELATIVE_PATH
    p.parent.mkdir(parents=True)
    p.write_text(junit_document(cases=7, tested_sha=sha), encoding="utf-8")
    ev = read_test_evidence(str(p), expected_tested_sha=sha, repo_root=tmp_path,
                            python_version="3.11.0")
    assert ev.honest_baseline and ev.measured_full == 7
    assert check_baseline(ev, tested_sha=sha)["verified"] is True
    assert ev.artifact_digest and ev.artifact_bytes > 0


# --------------------------------------------------------------------------- #
# R-G8-08 — a source binding must not depend on the checkout's newline policy
# --------------------------------------------------------------------------- #
def test_r08_the_s16_source_binding_is_checkout_invariant():
    """R-G8-08 RED BEFORE REPAIR: the CRLF working tree produced 366841 bytes /
    72ba79d7... and the git-stored LF blob 354913 bytes / af5941c3..., and the
    fixture, the live comparison and the receipt all used the raw working-tree
    digest, so the same source bound differently in different checkouts."""
    from engine.g5r import (CANONICAL_SOURCE_NEWLINE_RULE, canonical_source_bytes,
                            canonical_source_digest)
    manual = ROOT.parent / "quant-lab/reports/CEREBUS_v4_Manual_EXTRACTED.txt"
    lf = manual.read_bytes().replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    assert lf != crlf
    assert len(lf) == 354913 and len(crlf) == 366841
    assert canonical_source_digest(lf) == canonical_source_digest(crlf)
    assert len(canonical_source_bytes(lf)) == len(canonical_source_bytes(crlf)) == 354913
    assert CANONICAL_SOURCE_NEWLINE_RULE == "LF_NORMALIZED"
    declared = json.loads(
        (ROOT / "scenarios/s16_cerebus_contradiction/doctrine_claims.json")
        .read_text(encoding="utf-8"))[0]["source_fingerprint"]
    assert declared == canonical_source_digest(manual.read_bytes())


def test_r08_the_live_s16_run_binds_the_canonical_digest():
    """The live binding path must resolve to the canonical digest on whatever
    checkout this runs in, so the suite cannot pass on one and be STALE on
    another."""
    from engine.g5_runner import run_g5_scenario
    from engine.g5_runner import load_g5_pack
    from engine.domain_policy import G5DomainPolicy
    pack = load_g5_pack(AUDIT.SCEN / AUDIT.G5_MEMBERS["S16"]).decision_grade()
    policy = G5DomainPolicy.from_data(AUDIT._policy("G5_DOMAIN_EPISTEMIC_POLICY"))
    res = run_g5_scenario(pack, policy)
    claim = res.artifacts["doctrine_claims"][0]
    assert claim["source_binding_status"] == "BOUND"
    assert claim["source_binding"]["canonical_digest"] == \
        "af5941c35232a36f3b35c47b815d53377bd067a1fed7b1008a1ac5cace3ed4eb"
    assert claim["source_binding"]["canonical_newline_rule"] == "LF_NORMALIZED"


# --------------------------------------------------------------------------- #
# R-G8-09 — contract chronology is recorded, not asserted
# --------------------------------------------------------------------------- #
def test_r09_a_reconstruction_cannot_claim_a_pre_run_freeze():
    base = {"classification": "RETROSPECTIVE_RECONSTRUCTION",
            "gate_blocking_policy_source": "X",
            "artifacts": [{"artifact_id": "A",
                           "stage": "RETROSPECTIVE_RECONSTRUCTION",
                           "claims_pre_run_freeze": False,
                           "reconstruction_basis": "b"}]}
    assert validate_chronology(base)["weakest_stage"] == \
        "RETROSPECTIVE_RECONSTRUCTION"
    claimed = copy.deepcopy(base)
    claimed["artifacts"][0]["claims_pre_run_freeze"] = True
    with pytest.raises(ChronologyError):
        validate_chronology(claimed)


def test_r09_a_record_cannot_be_summarised_stronger_than_its_weakest_artifact():
    mixed = {"classification": "PRE_RUN_FROZEN_ARTIFACT",
             "gate_blocking_policy_source": "X",
             "artifacts": [
                 {"artifact_id": "OLD", "stage": "RETROSPECTIVE_RECONSTRUCTION",
                  "claims_pre_run_freeze": False, "reconstruction_basis": "b"},
                 {"artifact_id": "NEW", "stage": "PRE_RUN_FROZEN_ARTIFACT",
                  "claims_pre_run_freeze": True, "introducing_commit_ref": "c",
                  "pre_run_baseline_ref": "e"}]}
    with pytest.raises(ChronologyError):
        validate_chronology(mixed)
    mixed["classification"] = "RETROSPECTIVE_RECONSTRUCTION"
    assert validate_chronology(mixed)["classification"] == \
        "RETROSPECTIVE_RECONSTRUCTION"
    for bad in ({"artifact_id": "A", "stage": "NOT_A_STAGE"},
                {"artifact_id": "A", "stage": "PRE_RUN_FROZEN_ARTIFACT",
                 "claims_pre_run_freeze": True, "introducing_commit_ref": "c",
                 "pre_run_baseline_ref": ""}):
        with pytest.raises(ChronologyError):
            validate_chronology({"classification": "RETROSPECTIVE_RECONSTRUCTION",
                                 "gate_blocking_policy_source": "X",
                                 "artifacts": [bad]})


def test_r09_the_live_contract_declares_its_own_chronology(contract):
    record = contract["contract_chronology"]
    info = validate_chronology(record)
    assert info["weakest_stage"] == "RETROSPECTIVE_RECONSTRUCTION"
    assert info["classification"] == "RETROSPECTIVE_RECONSTRUCTION"
    assert "PRE_RUN_FROZEN_ARTIFACT" in info["stages"]
    assert "POST_FINDING_AMENDMENT" in info["stages"]
    assert "PRE-RUN FROZEN ARTIFACT" in record["gate_blocking_policy_source"]
    # the unsupported historical claim is retracted in the artifact itself
    assert "NOT supportable" in record["git_evidence"]


# --------------------------------------------------------------------------- #
# F2 — a seeded cross-machine semantic divergence is never silently equivalent
# --------------------------------------------------------------------------- #
def _authority_trace(*, grade_changed, artifact_ref):
    return {"phases": [
        {"phase": "DIRECTIVE", "detail": {
            "event_id": "EV_DIRECTIVE_1",
            "evidence_grade_before": "WEAK",
            "evidence_grade_after": "STRONG" if grade_changed else "WEAK",
            "evidence_grade_unchanged": (not grade_changed),
            "preserved": {"evidence_refs": [artifact_ref]}}}],
        "canonical_state": {"before": {"evidence_grades": {"CLAIM_1": "WEAK"}}},
        "terminal_phase": "WATCH"}


def test_seeded_cross_machine_semantic_contradiction_is_detected(contract):
    """A machine-local comparison would call these two traces identical — same
    phase vocabulary, same terminal token. The shared conceptual projection must
    separate them, and the F2 comparison must record the divergence instead of
    reporting equivalence."""
    clean = CP.project("AUTHORITY", _authority_trace(grade_changed=False,
                                                    artifact_ref="EV_KEPT"),
                       "SYN:CONCEPT:CLEAN")
    dirty = CP.project("AUTHORITY", _authority_trace(grade_changed=True,
                                                    artifact_ref="EV_KEPT"),
                       "SYN:CONCEPT:DIRTY")
    assert clean.outcome_token != dirty.outcome_token
    assert clean.values["conceptual_authority_not_empirical"] == "PRESERVED"
    assert dirty.values["conceptual_authority_not_empirical"] == "VIOLATED"
    left = _obs(contract, "SYN:CONCEPT:CLEAN", family_id="F2", state_machine="M-CONCEPT",
                object_class="INSTITUTIONAL_CONCEPT",
                raw_outcome_token=clean.outcome_token, vector_values=dict(clean.values))
    right = _obs(contract, "SYN:CONCEPT:DIRTY", family_id="F2", state_machine="M-CONCEPT",
                 object_class="INSTITUTIONAL_CONCEPT",
                 raw_outcome_token=dirty.outcome_token, vector_values=dict(dirty.values))
    assert left.outcome_mapped and right.outcome_mapped
    result = compare_observations(contract, left, right, mandated=True)
    assert result.verdict != "CONSISTENT", result.to_dict()
    assert result.differing_fields
    assert "conceptual_authority_not_empirical" in result.differing_fields


def test_the_projection_adapters_refuse_a_sealed_truth_trace():
    with pytest.raises(ValueError):
        CP.project("AUTHORITY", {**{k: "x" for k in ("expected_outcome",)}},
                   "SYN:SEALED")


# --------------------------------------------------------------------------- #
# R-G8-01..09 — the red evidence is EXECUTABLE, not a static annex
# --------------------------------------------------------------------------- #
def test_the_pre_repair_red_transcript_still_reproduces_every_finding():
    """Reruns the committed harness against the pre-repair commit and requires
    every finding to be RED by the harness's OWN declared criteria. This is what
    makes the red evidence survive: a reviewer runs this test, or the harness
    directly, rather than trusting an archived file.

    The criteria are NOT restated here (STRESS-G8ARCH6): they live with the
    harness that produces the observations, and the row-evidence resolver reads
    the same map, so a control, a matrix row and a resolver cannot hold three
    opinions about what RED means.
    """
    text = RED.transcript()
    assert "PROBE EXIT" not in text, "the probe must run clean against the old tree"
    verdicts = RED.verdicts(text, RED.PRE_REPAIR_HEAD)
    assert set(verdicts) == set(RED.PROBE_IDS)
    assert set(verdicts.values()) == {"RED"}, verdicts
    # every declared probe must carry the observations that demonstrate it, and
    # the committed annex must agree with the live run
    assert all(RED.RED_CRITERIA[p] for p in RED.PROBE_IDS)
    # a three-valued verdict: a probe that renders no line is ABSENT, which a row
    # may not cite either ("not rendered" is not "not red")
    renamed = text.replace("R-G8-03:", "R-G8-03RENAMED:")
    assert RED.verdicts(renamed, RED.PRE_REPAIR_HEAD)["R-G8-03"] == "ABSENT"
    # R-G8-09 also rests on the annex's Git section, which is a snapshot of the
    # history rather than probe output, so it is asserted here and NOT as a probe
    # criterion (counting it there made the probe read GREEN: the resolver caught
    # exactly that when it was first asked to re-derive the row)
    # full object name: a short abbreviation is chosen per repository, so
    # asserting one would make this regression depend on which clone it ran in
    assert "f5482e3e77e49ee279e4ecf5e58db5a2a694f5bb STRESS-G8P0" in text


def test_the_red_transcript_artifact_on_disk_matches_the_harness():
    """The committed annex must be the harness's own PROBE output, so it cannot
    drift. Only the probe section is compared byte-for-byte: the annex's Git
    section is a snapshot of the history as of its archive commit, and it grows
    (correctly) whenever the contract is amended again."""
    archived = (ROOT / "evidence" / "G8_PRE_REPAIR_RED_TRANSCRIPT.md").read_text(
        encoding="utf-8")
    marker = "## Git evidence for R-G8-09"
    assert marker in archived, "the annex must record the contract's Git history"
    assert archived.split(marker)[0].rstrip() == \
        RED.transcript(with_git_log=False).rstrip()


# =========================================================================== #
# STRESS-G8ARCH5 — durable red evidence for the passes AFTER the closure matrix,
# and the canonicalization rule pinned to its definition.
#
# The red proofs for these passes were originally run in a scratch directory and
# deleted, which left them in prose. The mission requires red regressions or
# executable transcripts, and a deleted file is neither, so the ARCH harness is
# committed and these two controls rerun it live.
# =========================================================================== #
def test_the_arch_red_transcript_still_reproduces_every_finding():
    """Every ARCH-era finding must still be RED against the code that carried it
    and GREEN against the tree being published. The harness extracts each named
    pre-pass commit read-only and runs the SAME probes against both, so this is
    rerunnable red evidence rather than a description of one."""
    text = ARCH.transcript()
    assert "PROBE EXIT" not in text, "a probe must run clean against every tree"
    for head in (h for _, h in ARCH.PRE_PASS_HEADS):
        before = ARCH.verdicts(text, head)
        assert set(before) == set(ARCH.PROBE_IDS), head

    # the head before the tree rule existed: no lag rule at all, and a citation
    # verified with an empty declared tree that defaulted to ""
    before_arch3 = ARCH.verdicts(text, ARCH.PRE_PASS_HEADS[0][1])
    assert before_arch3["ARCH-B"] == "RED"
    assert before_arch3["ARCH-E"] == "RED"
    assert before_arch3["ARCH-F"] == "RED"

    # the head before the omission-hazard repair: every hazard still present, and
    # the lag rule itself working (so ARCH-E and ARCH-F are genuinely different
    # findings rather than one repeated)
    before_arch4 = ARCH.verdicts(text, ARCH.PRE_PASS_HEADS[1][1])
    for probe in ("ARCH-A", "ARCH-B", "ARCH-C", "ARCH-D", "ARCH-F", "ARCH-G"):
        assert before_arch4[probe] == "RED", probe
    assert before_arch4["ARCH-E"] == "GREEN"

    # the tree being published: nothing RED, and the underivable tree refuses
    now = ARCH.verdicts(text)
    assert set(now) == set(ARCH.PROBE_IDS)
    assert set(now.values()) == {"GREEN"}, now
    assert "unverifiable tested tree" in text
    # the must-refuse control: a tree with no Git is refused, not reviewed
    assert "reviewer command exit=1 accepted=False" in text
    assert "derived tested tree: ''" in text or "no derivation available" in text


def test_the_arch_red_transcript_artifact_on_disk_matches_the_harness():
    """The committed ARCH annex must be the harness's own output, so the matrix's
    ARCH rows cannot cite red evidence that no longer reproduces. The annex has no
    Git-history section, so this comparison is byte-for-byte in full."""
    archived = (ROOT / "evidence" /
                "G8_ARCH_PRE_REPAIR_RED_TRANSCRIPT.md").read_text(encoding="utf-8")
    assert archived.rstrip() == ARCH.transcript().rstrip()


def test_no_exit_status_is_published_because_none_can_be_observed(
        sealed_test_evidence, tmp_path):
    """RED BEFORE REPAIR (ARCH-C, live: `to_dict()['exit_status'] == 0`): the
    reader took `exit_status: int = 0`, so the emitter published a successful run
    outcome it had never observed -- an unobserved value read as a favourable one.
    A JUnit document cannot show the producing process's exit code, so the claim is
    gone and the refusal it drove is driven by the counts MEASURED from the
    artifact instead."""
    cited = sealed_test_evidence.to_dict()
    assert "exit_status" not in cited
    assert "exit_status" not in inspect.signature(read_test_evidence).parameters
    assert cited["honest_baseline"] is True
    # a failing run still refuses, on measurement rather than on a claim
    tree = tmp_path / "measured"
    path = tree / ARTIFACT_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(junit_document(cases=4, failures=1,
                                   tested_sha=sealed_test_evidence.tested_sha),
                    encoding="utf-8")
    with pytest.raises(UnverifiableTestEvidence) as err:
        read_test_evidence(path, expected_tested_sha=sealed_test_evidence.tested_sha,
                           repo_root=tree)
    assert "failing baseline" in str(err.value)


def test_a_closure_row_can_only_cite_evidence_that_is_red_at_the_head_it_names(
        tmp_path):
    """RED BEFORE REPAIR (STRESS-G8ARCH6). The row-evidence check was a SUBSTRING
    SCAN inside the emitter, so it accepted a row claiming RED where an annex
    rendered GREEN at the head it named, and a head string that merely OCCURRED
    anywhere in the transcript (`'a'*40`, the synthetic probe tree). Both are the
    "no detected violation therefore proved" pattern this gate exists to forbid --
    the same class as R-G8-01, where merely invoking the comparator counted as
    coverage.

    The rule now has ONE owner and re-derives the verdict from the harnesses'
    declared heads and their parsed verdicts. Each tamper below is refused, and
    the real rows all resolve.
    """
    arch4 = ARCH.PRE_PASS_HEADS[1][1]
    rows = list(EMIT._AUDIT_CLOSURE)

    def tampered(**kw):
        edited = list(rows)
        edited[15] = {**edited[15], **kw}
        return edited

    # the shipped rows resolve, and the ANNEX is DERIVED rather than declared:
    # no row carries an annex name at all, so the eight literal copies are gone
    resolved = CLOSURE.require(rows, ROOT / "evidence")
    assert len(resolved) == len(rows) == 16
    assert [e for e in rows if "red_annex" in e] == []
    assert resolved[0]["red_annex"] == RED.ANNEX
    assert resolved[15]["red_annex"] == ARCH.ANNEX
    assert resolved[15]["annex_verdict"] == "RED"
    assert resolved[15]["red_head"] == ARCH.PRE_PASS_HEADS[1][1]

    def reason(edited, evidence=None):
        found = CLOSURE.problems(edited, evidence or (ROOT / "evidence"))
        assert found, "this tamper must be refused"
        return found[0]

    # a probe id no harness declares
    assert "not declared by any red-evidence harness" in reason(
        tampered(red_probe="ARCH-ZZ"))
    # a head the harness never ran against
    assert "is not declared by" in reason(tampered(red_head="f" * 40))
    # a head that merely OCCURS in the transcript text
    assert "is not declared by" in reason(tampered(red_head="a" * 40))
    # a probe the annex renders GREEN at the head the row names
    green = reason(tampered(red_probe="ARCH-E", red_head=arch4))
    assert "renders GREEN there" in green and "ARCH-E" in green
    # a probe whose line is absent from its annex
    evdir = tmp_path / "ev"
    evdir.mkdir()
    for harness in (RED, ARCH):
        text = (ROOT / "evidence" / harness.ANNEX).read_text(encoding="utf-8")
        if harness is ARCH:
            text = "\n".join(ln for ln in text.splitlines()
                              if not ln.startswith("ARCH-A:")) + "\n"
        (evdir / harness.ANNEX).write_text(text, encoding="utf-8", newline="\n")
    assert "renders ABSENT there" in reason([rows[9]], evdir)
    # an annex that cannot be found is a diagnostic, not a bare KeyError: the row
    # no longer names one, so the lookup that raised KeyError cannot be reached
    assert "is absent from" in reason([rows[9]], tmp_path / "nowhere")
    # a row may not cite an ambiguous harness without naming a head
    assert "must name one of" in reason(tampered(red_head=""))
    # The GREEN half is resolved by the SAME call (STRESS-G8ARCH7). RED BEFORE
    # REPAIR, live: `resolve_closure_rows` ACCEPTED all three of these ("16 rows
    # accepted") while the emitter's own write path refused the first two, so a
    # maintainer calling the resolver named resolve got false assurance that the
    # row was fully resolved. The rule now has one answer.
    assert "is not in the test module" in reason(
        tampered(green_tests=("test_this_regression_does_not_exist",)))
    assert "does not exist" in reason(
        tampered(artifacts=("G8_NO_SUCH_ARTIFACT.md",)))
    assert "cites no green regression" in reason(tampered(green_tests=()))
    # ...and the same refusal comes from the single-row entry point, not only from
    # the aggregate one, because that is the call a maintainer reaches for.
    with pytest.raises(ValueError) as err:
        CLOSURE.resolve(tampered(green_tests=("test_this_regression_does_not_exist",))[15],
                        ROOT / "evidence")
    assert "is not in the test module" in str(err.value)


def test_the_row_resolver_derives_each_row_exactly_once(monkeypatch):
    """RED BEFORE REPAIR (STRESS-G8ARCH7, live: 14 verdict derivations for 7 ARCH
    rows). `require` called `problems` -- one resolve per row -- and then resolved
    every row AGAIN, so each row was evaluated twice and the rows it returned were
    the second evaluation's, which the aggregate refusal had never inspected.
    """
    calls = {"n": 0}
    # patch the harness object the RESOLVER holds -- the suite imports these
    # scripts both top-level and as package members, and the resolver is the
    # consumer whose derivation count this test is about.
    harness = CLOSURE.ARCH
    real = harness.verdicts

    def counted(text, head=None):
        calls["n"] += 1
        return real(text, head)

    monkeypatch.setattr(harness, "verdicts", counted)
    rows = list(EMIT._AUDIT_CLOSURE)
    arch_rows = [r for r in rows if r["red_probe"].startswith("ARCH-")]
    resolved = CLOSURE.require(rows, ROOT / "evidence")
    assert len(resolved) == len(rows)
    assert calls["n"] == len(arch_rows)
    # the survival controls are resolved by the same gate, and a control the suite
    # does not collect is refused there too.
    assert CLOSURE.survival_problems() == []
    assert CLOSURE.survival_problems("def test_something_else():") != []


def test_the_canonical_rule_name_resolves_to_its_declared_definition_and_pinned_fingerprint(
        monkeypatch):
    """RED BEFORE REPAIR (ARCH-G, live: `resolvable definition=False`): the
    published `artifact_canonicalization_rule` was a LABEL. Nothing resolved it, so
    the definition could move while the published name stayed put and the receipt
    would keep describing a rule it no longer used.

    The name is now a version whose DEFINITION is data, whose fields drive the
    implementation, and whose fingerprint is published and pinned here. Changing
    any declared field requires a new name.
    """
    assert ARTIFACT_CANONICALIZATION_RULE in CANONICALIZATION_RULES
    definition = canonical_rule()
    pinned = "0aa12afabf2ecfedbc401ff14de4eae6e551a7bc28c4cb997ee92edd3049f670"
    assert canonical_rule_fingerprint() == pinned
    # documentation is NOT part of the pin (STRESS-G8ARCH6): a prose-only edit
    # must not move the fingerprint, because hashing prose would make a typo fix
    # demand a new rule NAME -- inverting the point of pinning a name to a
    # definition. The note is published beside the rule, not inside it.
    assert ARTIFACT_CANONICALIZATION_RULE in CANONICALIZATION_RULE_NOTES
    monkeypatch.setitem(CANONICALIZATION_RULE_NOTES,
                        ARTIFACT_CANONICALIZATION_RULE,
                        "reworded for clarity, behaviour unchanged")
    assert canonical_rule_fingerprint() == pinned
    # the declaration is not decorative: the attributes it names are the ones the
    # implementation strips, and attribute ORDER cannot change the canonical bytes
    one = b'<testsuite name="tests" tests="0" time="0.1" hostname="h">' \
          b'<properties><property name="tested_sha" value="a"/></properties></testsuite>'
    two = b'<testsuite hostname="h" time="0.2" name="tests" tests="0">' \
          b'<properties><property name="tested_sha" value="a"/></properties></testsuite>'
    assert canonical_junit_bytes(one) == canonical_junit_bytes(two)
    assert b"time=" not in canonical_junit_bytes(one)
    assert b"hostname=" not in canonical_junit_bytes(one)
    # the rule's newline portability is STRUCTURAL, not a configured step: no
    # declaration here promises normalisation, so this asserts the property itself
    # over adversarial documents -- CRLF in character data, and CRLF smuggled in
    # through an attribute value as character references
    for doc in (b'<testsuite name="tests" tests="0">\r\n<properties/>\r\n</testsuite>',
                b'<testsuite name="a&#13;&#10;b" tests="0"><properties/></testsuite>',
                b'<testsuite name="tests" tests="1"><testcase classname="t" '
                b'name="x"><failure message="l1&#13;&#10;l2"/></testcase></testsuite>'):
        assert b"\r" not in canonical_junit_bytes(doc)
    # ... and every declared field DRIVES the implementation: a definition change
    # moves the fingerprint, which is what forces a new name rather than a quiet
    # edit, and the field really is what the digest applies
    monkeypatch.setitem(CANONICALIZATION_RULES, ARTIFACT_CANONICALIZATION_RULE,
                        {**definition, "strips_attributes": ("time",)})
    assert canonical_rule_fingerprint() != pinned
    assert b"hostname" in canonical_junit_bytes(one)
    # an unpublished name refuses rather than defaulting to the declared rule
    with pytest.raises(UnverifiableTestEvidence):
        canonical_rule("NOT_A_DECLARED_RULE")


# =========================================================================== #
# STRESS-G8RX6 — the two enforcement gaps the closure audit proved (F1, F2) and
# the artifact-provenance gap in R-G8-07's baseline citation.
# =========================================================================== #
def test_f1_the_gate_refuses_a_baseline_bound_to_a_different_tree(
        contract, package, sealed_test_evidence):
    """F1 RED BEFORE REPAIR: decide_gate called
    `check_baseline(test_evidence, tested_sha=test_evidence.tested_sha)`, comparing
    the artifact against ITSELF, so a forged tested tree certified and
    baseline.verified stayed True. The declared tree is now a required argument
    and the gate can detect a stale or foreign artifact."""
    params = inspect.signature(decide_gate).parameters
    assert "expected_tested_sha" in params
    assert params["expected_tested_sha"].default is inspect.Parameter.empty, \
        "the declared tree may not default: an inferred tree reintroduces F1"
    families = package["families"]
    guarded = [g for fam in families for g in fam.guarded]
    obs = package["observations"]
    declared = sealed_test_evidence.tested_sha
    ok = decide_gate(contract, families, guarded, [],
                     test_evidence=sealed_test_evidence,
                     expected_tested_sha=declared, observations=obs)
    assert ok["exit"] == "PASS_G8_CROSS_SCENARIO_COHERENCE"
    assert ok["baseline"]["verified"] is True
    forged = replace(sealed_test_evidence, tested_sha="0" * 40)
    bad = decide_gate(contract, families, guarded, [], test_evidence=forged,
                      expected_tested_sha=declared, observations=obs)
    assert bad["exit"] == "BLOCKED_G8_BASELINE_FAILURE"
    assert bad["baseline"]["verified"] is False
    assert bad["declared_tested_sha"] == declared
    assert bad["baseline"]["artifact_bound_tested_sha"] == "0" * 40


def test_f2_a_required_property_that_never_holds_blocks_closure(
        contract, package, sealed_test_evidence):
    """F2 RED BEFORE REPAIR: closure accepted any finding whose derivation_kind was
    not NOT_DERIVABLE, whatever its verdict, so a required property exercised only
    as UNKNOWN_NOT_FAVORABLE satisfied closure and the gate PASSED on
    non-derivations. A HOLDS finding carries its derivation evidence by
    construction, so HOLDS is now the requirement."""
    target = "P5"
    families = package["families"]
    guarded = [g for fam in families for g in fam.guarded]
    obs = package["observations"]
    declared = sealed_test_evidence.tested_sha
    assert any(g.property_id == target and g.verdict == "HOLDS" for g in guarded)
    stripped = [replace(g, value=None, verdict="UNKNOWN_NOT_FAVORABLE",
                        derivation_kind="DIRECT_TRACE")
                if g.property_id == target else g for g in guarded]
    decision = decide_gate(contract, families, stripped, [],
                           test_evidence=sealed_test_evidence,
                           expected_tested_sha=declared, observations=obs)
    assert decision["exit"] == "BLOCKED_G8_MISSING_EVIDENCE"
    cov = decision["guarded_coverage"]
    assert target in cov["unexercised_required_properties"]
    # it was TOUCHED but never held — the distinction F2 turns on
    assert target not in cov["required_never_derived"]
    assert any("never returned HOLDS" in r for r in decision["reasons"])
    # the live package still proves every closure-required property
    live = package["guarded_coverage"]
    assert live["unexercised_required_properties"] == []
    assert "must return HOLDS" in live["closure_rule"]


def test_r07_the_artifact_must_live_inside_the_declared_tree(tmp_path):
    """R-G8-07 provenance gap: the receipt used to cite a machine-local temp path
    with a per-run digest, so no reviewer on another machine could obtain or
    re-check the baseline the gate rested on. An artifact outside the declared
    tree is refused outright.

    STRESS-G8ARCH: the rule has ONE owner. The reader admits only the declared
    evidence path, so no caller -- CLI included -- can publish a citation the
    reader itself would refuse."""
    sha = AUDIT.head_sha()
    doc = junit_document(cases=5, tested_sha=sha)
    outside = tmp_path / "pytest.xml"
    outside.write_text(doc, encoding="utf-8")
    with pytest.raises(UnverifiableTestEvidence):
        read_test_evidence(str(outside), expected_tested_sha=sha,
                           repo_root=ROOT.parent)

    # inside the declared tree, but not at the declared evidence path
    tree = tmp_path / "tree"
    elsewhere = tree / "scenarios" / "pytest.xml"
    elsewhere.parent.mkdir(parents=True)
    elsewhere.write_text(doc, encoding="utf-8")
    with pytest.raises(UnverifiableTestEvidence) as refused:
        read_test_evidence(str(elsewhere), expected_tested_sha=sha, repo_root=tree)
    assert ARTIFACT_RELATIVE_PATH in str(refused.value)

    declared = tree / ARTIFACT_RELATIVE_PATH
    declared.parent.mkdir(parents=True)
    declared.write_text(doc, encoding="utf-8")
    ev = read_test_evidence(str(declared), expected_tested_sha=sha, repo_root=tree)
    assert ev.in_tree and ev.repo_relative_path == ARTIFACT_RELATIVE_PATH
    assert ev.to_dict()["artifact_path"] == ARTIFACT_RELATIVE_PATH
    assert ev.to_dict()["artifact_path_scope"] == "REPO_RELATIVE"
    assert check_baseline(ev, tested_sha=sha)["verified"] is True

    # the same artifact read with no declared tree is parseable but NOT
    # publishable: nothing may rest on a baseline a reviewer cannot reach
    loose = read_test_evidence(str(declared), expected_tested_sha=sha)
    assert loose.in_tree is False
    assert check_baseline(loose, tested_sha=sha)["verified"] is False


def test_r07_the_emitter_refuses_an_artifact_outside_the_declared_tree(tmp_path):
    sha = AUDIT.head_sha()
    p = tmp_path / "pytest.xml"
    p.write_text(junit_document(cases=5, tested_sha=sha), encoding="utf-8")
    undeclared = read_test_evidence(str(p), expected_tested_sha=sha)
    assert undeclared.in_tree is False
    with pytest.raises(UnverifiableTestEvidence):
        EMIT.emit(undeclared)


def test_r07_the_emitted_citation_resolves_in_tree_and_matches_the_bytes(
        tmp_path, monkeypatch):
    """End-to-end on the MECHANISM: emit into a redirected package and check the
    CITATION rather than the prose. The cited path must resolve inside the declared
    tree and its raw digest must equal the digest of the bytes on disk, so the
    baseline is re-checkable without trusting the generator."""
    import hashlib
    from engine.g8_test_evidence import canonical_artifact_digest
    tree = tmp_path / "tree"
    evdir = tree / "stress-suite" / "evidence"
    evdir.mkdir(parents=True)
    doc = evdir / "G8_TEST_RESULTS.xml"
    doc.write_text(junit_document(cases=7, tested_sha=EMIT.TESTED_SHA),
                   encoding="utf-8")
    evidence = read_test_evidence(str(doc), expected_tested_sha=EMIT.TESTED_SHA,
                                 repo_root=tree)
    monkeypatch.setattr(EMIT, "EVIDENCE", evdir)
    out = EMIT.emit(evidence)
    cited = out["receipt"]["test_evidence_artifact"]
    assert cited["artifact_path_scope"] == "REPO_RELATIVE"
    assert cited["artifact_path"] == "stress-suite/evidence/G8_TEST_RESULTS.xml"
    target = tree / cited["artifact_path"]
    assert target.is_file(), "the cited citation must resolve in the declared tree"
    blob = target.read_bytes()
    assert hashlib.sha256(blob).hexdigest() == cited["artifact_digest"]
    assert len(blob) == cited["artifact_bytes"]
    assert canonical_artifact_digest(blob) == cited["artifact_canonical_digest"]
    bound = out["receipt"]["baseline_check"]
    assert bound["declared_tested_sha"] == EMIT.TESTED_SHA
    assert bound["artifact_bound_tested_sha"] == EMIT.TESTED_SHA
    assert bound["artifact_in_tree"] is True


def test_r07_raw_and_canonical_artifact_digests_are_distinct_and_declared(tmp_path):
    """The raw digest is per-RUN (JUnit stamps time/timestamp/hostname) and so
    cannot be reproduced by re-running; the canonical digest applies the declared
    rule and is. Both are published under distinct names, so 'content digest' is
    not silently redefined."""
    from engine.g8_test_evidence import (ARTIFACT_CANONICALIZATION_RULE,
                                         canonical_artifact_digest)
    sha = AUDIT.head_sha()
    base = junit_document(cases=5, tested_sha=sha)
    stamped = []
    for i, (elapsed, host) in enumerate((("1.23", "host-a"), ("9.87", "host-b"))):
        doc = base.replace(
            '<testsuite name="tests" tests="5">',
            f'<testsuite name="tests" tests="5" time="{elapsed}" '
            f'timestamp="2026-01-0{i + 1}T00:00:00" hostname="{host}">')
        # one run per declared tree: the artifact is admitted only at the
        # declared evidence path, so two runs cannot share a tree
        tree = tmp_path / f"run{i}"
        path = tree / ARTIFACT_RELATIVE_PATH
        path.parent.mkdir(parents=True)
        path.write_text(doc, encoding="utf-8")
        stamped.append(read_test_evidence(str(path), expected_tested_sha=sha,
                                         repo_root=tree))
    first, second = stamped
    assert first.artifact_digest != second.artifact_digest, "raw bytes differ per run"
    assert first.artifact_canonical_digest == second.artifact_canonical_digest
    # the published rule is a VERSIONED NAME that must resolve to a definition
    assert ARTIFACT_CANONICALIZATION_RULE in CANONICALIZATION_RULES
    cited = first.to_dict()
    assert cited["artifact_canonicalization_rule_fingerprint"] == \
        canonical_rule_fingerprint()
    assert cited["artifact_digest"] == first.artifact_digest
    assert cited["artifact_canonical_digest"] == first.artifact_canonical_digest
    assert cited["artifact_canonicalization_rule"] == ARTIFACT_CANONICALIZATION_RULE
    assert "RAW sha256" in cited["artifact_digest_semantics"]
    assert canonical_artifact_digest(
        (tmp_path / "run0" / ARTIFACT_RELATIVE_PATH).read_bytes()
    ) == first.artifact_canonical_digest


def test_r07_the_authoritative_command_writes_the_cited_artifact_path():
    """The receipt cites one repo-relative path; the command that produces it must
    name that same path, run from the package directory, so the citation is
    obtainable rather than aspirational.

    STRESS-G8ARCH: the path, the command and the derived artifact command are
    declared ONCE in engine.g8_test_evidence. The emitter publishes those objects;
    it does not restate them (identity, not equality: a rebuilt copy fails here).
    """
    from engine.g8_test_evidence import (ARTIFACT_COMMAND,
                                         AUTHORITATIVE_TEST_COMMAND)
    assert ARTIFACT_RELATIVE_PATH == "stress-suite/evidence/G8_TEST_RESULTS.xml"
    assert AUTHORITATIVE_TEST_COMMAND == \
        "cd stress-suite && PYTHONIOENCODING=utf-8 python -m pytest tests -q"
    assert ARTIFACT_COMMAND == (AUTHORITATIVE_TEST_COMMAND
                                + " --junitxml=evidence/G8_TEST_RESULTS.xml")
    assert EMIT.ARTIFACT_COMMAND is ARTIFACT_COMMAND
    assert EMIT.ARTIFACT_RELATIVE_PATH is ARTIFACT_RELATIVE_PATH


# =========================================================================== #
# STRESS-G8ARCH2 — the two offers the closure audit left open.
#
# (1) A committed artifact whose bytes no longer hash to the digest the package
#     publishes, or whose recorded tree is not the tree the gate rests on, was
#     published and then never re-checked: it must BLOCK, not verify.
# (2) The tested tree the receipt published was a string typed into the emitter --
#     the same self-reporting defect R-G8-07 exists to forbid. It is now derived
#     from Git under the rule declared in engine.g8_test_evidence.
# =========================================================================== #
def _temp_git_repo(tmp_path):
    """A throwaway repository whose code/test tree can be moved at will."""
    repo = tmp_path / "repo"
    (repo / "stress-suite" / "engine").mkdir(parents=True)
    (repo / "stress-suite" / "tests").mkdir(parents=True)
    (repo / "docs").mkdir()
    (repo / "stress-suite" / "engine" / "core.py").write_text(
        "x = 1\n", encoding="utf-8")
    (repo / "docs" / "note.md").write_text("doc\n", encoding="utf-8")

    def _git(*args: str) -> str:
        return subprocess.run(
            ["git", "-c", "user.email=t@example.invalid", "-c", "user.name=t",
             *args], cwd=str(repo), capture_output=True, text=True,
            check=True).stdout.strip()

    _git("init", "-q")
    _git("add", "-A")
    _git("commit", "-q", "-m", "code")
    return repo, _git


def test_the_tested_tree_is_derived_from_git_not_declared_by_hand(tmp_path):
    """RED BEFORE REPAIR: `TESTED_SHA` was a 40-hex literal in the emitter, so the
    package kept claiming whatever revision a human last typed there. It is now the
    newest commit that changed code or tests -- and because the rule names the CODE
    tree, a later commit that touches only docs or evidence cannot move it, which is
    what lets the package regenerate identically from any later commit."""
    repo, git = _temp_git_repo(tmp_path)
    code = derived_tested_tree(repo)
    assert code == git("rev-parse", "HEAD")
    assert derived_tested_tree(repo, require_clean=True) == code

    # a commit that touches ONLY evidence/docs must not move the tested tree
    (repo / "docs" / "note.md").write_text("doc changed\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-q", "-m", "docs: evidence only")
    assert git("rev-parse", "HEAD") != code
    assert derived_tested_tree(repo, require_clean=True) == code

    # ... but an uncommitted change to the CODE tree is not the tested tree
    (repo / "stress-suite" / "tests" / "test_x.py").write_text(
        "def test_x():\n    assert True\n", encoding="utf-8")
    with pytest.raises(UnverifiableTestEvidence) as refused:
        derived_tested_tree(repo, require_clean=True)
    assert "dirty tree" in str(refused.value)
    # the same tree still resolves without the cleanliness requirement, so the
    # sealed fixtures and the read path are unaffected by a dirty working tree
    assert derived_tested_tree(repo) == code


def test_the_tested_tree_has_exactly_one_implementation():
    """STRESS-G8ARCH3. Three layers used to derive this privately -- the emitter, the
    harness (`conftest`, with a DIFFERENT fallback) and the audit entry point (which
    used live HEAD) -- so at an archive commit the audit refused its own package. The
    owner is `scenarios/g8_tested_tree.py`; everyone else consumes it."""
    owner = Path(ROOT / "scenarios" / "g8_tested_tree.py").read_text(encoding="utf-8")
    assert owner.count("def derived_tested_tree(") == 1
    consumers = {
        Path(EMIT.__file__): "from scenarios.g8_tested_tree import derived_tested_tree",
        Path(ROOT / "conftest.py"): "from scenarios.g8_tested_tree import derived_tested_tree",
        Path(ROOT / "scenarios" / "g8_run_audit.py"):
            "from scenarios.g8_tested_tree import derived_tested_tree",
    }
    for path, delegation in consumers.items():
        source = path.read_text(encoding="utf-8")
        assert delegation in source, f"{path.name} does not use the one owner"
        assert 'subprocess.run(["git"' not in source or path.name == "g8_run_audit.py", \
            f"{path.name} still carries its own Git access for the tree rule"


def test_the_emitter_holds_no_hand_typed_tested_tree():
    """Tripwire: a 40-hex literal assigned to TESTED_SHA would reintroduce exactly
    the defect the test above closes, so the assignment must stay derived -- and it
    must be derived by the one owner, not by a private copy in the emitter."""
    source = Path(EMIT.__file__).read_text(encoding="utf-8")
    assert not re.search(r"TESTED_SHA\s*=\s*[\"'][0-9a-f]{40}", source)
    assert "TESTED_SHA = derived_tested_tree()" in source
    assert "def declared_tested_sha" not in source
    assert EMIT.TESTED_SHA == derived_tested_tree(ROOT.parent)
    assert EMIT.TESTED_SHA


def _committed_blob(relative: str) -> bytes:
    """The bytes of a path AS COMMITTED. The reviewer's question is about the
    committed tree, and a pass legitimately regenerates the artifact before it
    re-emits, so comparing against the working tree would be red exactly while the
    package is one emission behind -- and would then block the very run that fixes
    it."""
    return subprocess.run(["git", "show", f"HEAD:{relative}"], cwd=str(ROOT.parent),
                          capture_output=True, check=True).stdout


RECEIPT_REL = "stress-suite/evidence/G8_EVIDENCE_RECEIPT.json"


def _lagging_tested_tree(receipt_tree: str, derived_tree: str) -> str:
    """The one rule for 'the committed package no longer describes the code': empty
    when the package is current, otherwise the problem to report.

    An UNDERIVABLE tree is not a current one (STRESS-G8ARCH4): it used to return ""
    -- i.e. 'I could not check this' was reported as 'nothing to report', which is
    the favourable reading of an unknown. The publish path already refused that
    case (`require_clean`); this guard now refuses it too, instead of standing
    aside for it.
    """
    if not derived_tree:
        return ("unverifiable tested tree: the code/test tree could not be derived, "
                "so the committed package cannot be shown to describe this "
                "checkout. A tree that cannot be derived is not a tree that matches.")
    if receipt_tree == derived_tree:
        return ""
    return (f"lagging tested tree: the committed package names "
            f"{receipt_tree or 'NOTHING'} but the code/test tree is now "
            f"{derived_tree}. Re-produce the artifact at the new tree and re-emit.")


def test_the_lag_rule_detects_a_lagging_tree_and_accepts_a_current_one():
    """The DETECTION LOGIC is exercised in every run, including the artifact-producing
    run where the end-to-end check below must skip: a seeded code commit after the
    archive must be caught, and a current package must not be."""
    derived = derived_tested_tree(ROOT.parent)
    assert derived
    assert _lagging_tested_tree(derived, derived) == ""
    seeded = _lagging_tested_tree("0" * 40, derived)
    assert seeded.startswith("lagging tested tree")
    assert "0" * 40 in seeded and derived in seeded
    assert _lagging_tested_tree("", derived).startswith("lagging tested tree")
    # a tree that cannot be derived is not a match, and it is not a silent pass
    assert _lagging_tested_tree(derived, "").startswith("unverifiable tested tree")
    assert _lagging_tested_tree("", "").startswith("unverifiable tested tree")


def test_the_committed_package_names_the_derived_code_tree(pytestconfig):
    """RED BEFORE REPAIR (proved by seeding a code commit after the archive): the
    committed-citation guard passed `expected_tested_sha` from the CITATION'S OWN
    CLAIM, so it compared bytes against the citation and never the tree against the
    code -- trusting the evidence's own self-report, which is the R-G8-07 defect this
    gate exists to forbid. A code commit after the archive therefore left the whole
    module green while the package lagged.

    One exception, and it is structural rather than convenient: an archive cannot
    exist before the tree it archives. The run that WRITES the artifact (`--junitxml`)
    happens before the re-emission, so the committed package is one emission behind
    by construction there. Every ordinary run -- including a reviewer's clone --
    executes this check, and the detection logic itself is exercised unconditionally
    by the test above.
    """
    if getattr(pytestconfig.option, "xmlpath", None):
        pytest.skip("artifact-producing run: the archive for this tree cannot exist "
                    "yet, so a lag is expected here and is checked by every ordinary "
                    "run (and by test_the_lag_rule_detects_a_lagging_tree_...)")
    receipt = json.loads(_committed_blob(RECEIPT_REL))
    problem = _lagging_tested_tree(receipt["tested_sha"], derived_tested_tree(ROOT.parent))
    assert not problem, problem


def _staged_committed_pair(tmp_path):
    """The COMMITTED receipt and the COMMITTED artifact, staged in a throwaway tree
    at the declared relative path -- what a reviewer gets from a clone."""
    receipt = json.loads(
        _committed_blob("stress-suite/evidence/G8_EVIDENCE_RECEIPT.json"))
    citation = receipt["test_evidence_artifact"]
    staged = tmp_path / "tree"
    target = staged / citation["artifact_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(_committed_blob(citation["artifact_path"]))
    return receipt, citation, staged


def test_the_committed_citation_still_matches_the_bytes_it_cites(tmp_path):
    """The reviewer-facing guard for gap (1): the citation the COMMITTED receipt
    publishes must re-derive from the COMMITTED bytes. Tampering with either half,
    or regenerating one without the other, makes this refuse instead of passing."""
    import hashlib
    receipt, citation, staged = _staged_committed_pair(tmp_path)
    # the tree rested on is the PACKAGE-level declaration, not the citation's own
    # field: two independently written halves of the receipt must agree, and
    # tree-against-code is the lag check's job (STRESS-G8ARCH4).
    assert citation["tested_sha"] == receipt["tested_sha"]
    check = verify_citation(citation, repo_root=staged,
                            expected_tested_sha=receipt["tested_sha"])
    assert check["verified"], check["problems"]
    assert check["artifact_digest"] == citation["artifact_digest"]
    assert hashlib.sha256(
        (staged / citation["artifact_path"]).read_bytes()).hexdigest() \
        == citation["artifact_digest"]
    if receipt["tested_sha"] == EMIT.TESTED_SHA:
        # a receipt naming the CURRENT tested tree is not one emission behind, so
        # it must carry the verdict it publishes. (The emitter's behaviour is
        # proven directly by test_emit_publishes_a_citation_check_it_re_derived,
        # and a receipt regenerated after this commit is covered here.)
        recorded = receipt["citation_check"]
        assert recorded["verified"] is True and recorded["problems"] == []
        assert recorded["artifact_digest"] == check["artifact_digest"]


def test_a_rewritten_artifact_is_a_stale_citation(tmp_path):
    """RED BEFORE REPAIR: the citation was published and never re-checked, so a
    package could keep citing a digest whose bytes no longer existed."""
    _, citation, staged = _staged_committed_pair(tmp_path)
    tree = citation["tested_sha"]

    # 1. the cited bytes change under the citation (a re-run that overwrote the
    #    artifact without re-emitting): the published raw digest no longer holds
    (staged / citation["artifact_path"]).write_text(
        junit_document(cases=7, tested_sha=tree), encoding="utf-8")
    rewritten = verify_citation(citation, repo_root=staged, expected_tested_sha=tree)
    assert rewritten["verified"] is False
    assert any("hash to" in problem for problem in rewritten["problems"])

    # 2. a tampered citation whose digests describe nothing on disk
    _, citation, staged = _staged_committed_pair(tmp_path)
    tampered = dict(citation, artifact_digest="0" * 64)
    check = verify_citation(tampered, repo_root=staged, expected_tested_sha=tree)
    assert check["verified"] is False
    assert any("hash to" in problem for problem in check["problems"])
    canonical = dict(citation, artifact_canonical_digest="0" * 64)
    assert verify_citation(canonical, repo_root=staged,
                           expected_tested_sha=tree)["verified"] is False

    # 3. a citation the reviewer could not resolve at all
    loose = dict(citation, artifact_path_scope="OUTSIDE_DECLARED_TREE")
    outside = verify_citation(loose, repo_root=staged, expected_tested_sha=tree)
    assert outside["verified"] is False
    assert any("outside the declared tree" in p for p in outside["problems"])


def test_a_citation_recorded_against_another_tree_blocks_the_gate(
        contract, package, sealed_test_evidence):
    """'A committed artifact whose recorded tree no longer matches the tree the gate
    is resting on must BLOCK, not verify.' The fixture is bound to the declared
    tree; resting on a different one must refuse it."""
    citation = sealed_test_evidence.to_dict()
    other = "0" * 40
    check = verify_citation(citation, repo_root=sealed_test_evidence.repo_root,
                            expected_tested_sha=other)
    assert check["verified"] is False
    assert any("stale citation" in p for p in check["problems"])

    # and the gate reaches the same refusal WITHOUT being handed one: resting on a
    # different tree blocks for both reasons, because the baseline is bound
    # elsewhere and the citation does not record the tree rested on
    families = package["families"]
    guarded = [g for fam in families for g in fam.guarded]
    decision = decide_gate(contract, families, guarded, [],
                           test_evidence=sealed_test_evidence,
                           expected_tested_sha=other,
                           observations=package["observations"])
    assert decision["exit"] == "BLOCKED_G8_BASELINE_FAILURE"
    assert any("stale-citation" in r for r in decision["reasons"])
    assert decision["citation"]["verified"] is False


def test_a_verifying_citation_keeps_the_gate_passing(contract, package,
                                                     sealed_test_evidence):
    """The control for the block above: a citation that DOES re-derive must not be
    turned into a failure, so the new check is strict without being unconditional."""
    citation = sealed_test_evidence.to_dict()
    check = verify_citation(citation, repo_root=sealed_test_evidence.repo_root,
                            expected_tested_sha=sealed_test_evidence.tested_sha)
    assert check["verified"] is True and check["problems"] == []
    # the SAME call that proves the refusal above supplies no citation verdict at
    # all, so the check that runs here is the one the gate derived itself
    families = package["families"]
    guarded = [g for fam in families for g in fam.guarded]
    decision = decide_gate(contract, families, guarded, [],
                           test_evidence=sealed_test_evidence,
                           expected_tested_sha=sealed_test_evidence.tested_sha,
                           observations=package["observations"])
    assert decision["exit"] == "PASS_G8_CROSS_SCENARIO_COHERENCE"
    assert decision["citation"]["verified"] is True


def test_no_verification_input_can_be_omitted_or_left_empty(
        contract, package, sealed_test_evidence, tmp_path):
    """RED BEFORE REPAIR (STRESS-G8ARCH4). Each of these was a check a caller could
    omit or satisfy with a favourable default while the gate still passed:

      1. `citation_check` was an optional argument -- the CLI omitted it, so the
         citation this package publishes was never verified at all. The parameter
         no longer exists, which is the only form of 'cannot be omitted'.
      2. `verify_citation(expected_tested_sha="")` fell back to the CITATION'S OWN
         recorded tree: it verified the evidence against the evidence's self-report.
      3. `check_baseline(tested_sha="")` SKIPPED the tree comparison, reading an
         undeclared tree as 'any tree will do'.
      4. A record whose citation cannot be resolved on disk could still be rested
         on: the gate must block, not pass, on a citation it cannot re-derive.
    """
    # 1. nothing left to omit: no such parameter exists on either entry point
    assert "citation_check" not in inspect.signature(decide_gate).parameters
    assert "citation_check" not in inspect.signature(AUDIT.build_package).parameters

    # 2. the tree is required with no default, and an empty one refuses
    tree_param = inspect.signature(verify_citation).parameters["expected_tested_sha"]
    assert tree_param.default is inspect.Parameter.empty
    assert tree_param.kind is inspect.Parameter.KEYWORD_ONLY
    unlabelled = verify_citation(sealed_test_evidence.to_dict(),
                                 repo_root=sealed_test_evidence.repo_root,
                                 expected_tested_sha="")
    assert unlabelled["verified"] is False
    assert any("self-report" in p for p in unlabelled["problems"])

    # 3. an undeclared tree refuses the baseline instead of skipping the comparison
    undeclared = check_baseline(sealed_test_evidence, tested_sha="")
    assert undeclared["verified"] is False
    assert any("no tree was declared" in p for p in undeclared["problems"])

    # 4. a citation that cannot be re-derived from disk blocks the gate
    orphaned = replace(sealed_test_evidence,
                       repo_root=str(tmp_path / "tree-without-the-artifact"))
    decision = decide_gate(contract, package["families"],
                           [g for fam in package["families"] for g in fam.guarded],
                           [], test_evidence=orphaned,
                           expected_tested_sha=sealed_test_evidence.tested_sha,
                           observations=package["observations"])
    assert decision["exit"] == "BLOCKED_G8_BASELINE_FAILURE"
    assert any("stale-citation" in r for r in decision["reasons"])
    assert decision["citation"]["verified"] is False


def test_emit_publishes_a_citation_check_it_re_derived(monkeypatch, tmp_path,
                                                       sealed_test_evidence):
    """The package must carry the verdict, not just the claim: emit re-derives the
    citation it is about to publish from the bytes on disk and records that check."""
    evdir = tmp_path / "ev"
    evdir.mkdir()
    monkeypatch.setattr(EMIT, "EVIDENCE", evdir)
    out = EMIT.emit(sealed_test_evidence)
    check = out["receipt"]["citation_check"]
    assert check["verified"] is True and check["problems"] == []
    assert check["recorded_tested_sha"] == sealed_test_evidence.tested_sha
    assert out["decision"]["exit"] == "PASS_G8_CROSS_SCENARIO_COHERENCE"

