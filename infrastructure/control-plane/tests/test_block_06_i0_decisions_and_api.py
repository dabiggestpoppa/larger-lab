"""B6-I0 extraction decisions and API firewall."""
from __future__ import annotations

import pathlib as _p
import sys as _s

_s.path.insert(0, str(_p.Path(__file__).resolve().parent))
import block_06_i0_support as S  # noqa: E402

ADMISSIBLE = {"EXTRACTABLE_PATTERN", "EXTRACTABLE_WITH_LIMITATION", "DEFERRED_TO_BOOK_6"}
DIST = {"EXTRACTABLE_PATTERN": 7, "EXTRACTABLE_WITH_LIMITATION": 5, "REFERENCE_ONLY": 4,
        "PLATFORM_INTERNAL": 3, "PRIVATE_API": 2, "AUTHORITY_BEARING": 3, "PROHIBITED": 1,
        "DEFERRED_TO_BOOK_6": 1, "NOT_APPLICABLE": 1}


def test_candidate_total_27():
    d = S.load("EXTRACTION_DECISION_FREEZE")
    assert d["candidate_total"] == len(d["candidates"]) == 27
    assert len({r["id"] for r in d["candidates"]}) == 27
    source = S.p0("CANDIDATE_EXTRACTION_DISPOSITION_v1.0.json")
    assert [r["id"] for r in d["candidates"]] == sorted(c["id"] for c in source["candidates"])


def test_arithmetic_rederived():
    d = S.load("EXTRACTION_DECISION_FREEZE")
    rows = d["candidates"]
    computed = {k: sum(1 for r in rows if r["classification"] == k) for k in DIST}
    assert computed == DIST == d["distribution"]
    arith = d["arithmetic"]
    assert arith["total"] == 27
    assert arith["admitted"] == sum(1 for r in rows
                                    if r["decision"] == "ADMITTED_FOR_FUTURE_DESIGN")
    assert arith["refused"] == sum(1 for r in rows if r["decision"] == "REFUSED")
    assert arith["admitted"] + arith["refused"] == 27
    assert arith["extracted"] == 0 and arith["copied_files"] == 0


def test_eligibility_scan():
    rows = S.load("EXTRACTION_DECISION_FREEZE")["candidates"]
    for row in rows:
        if row["classification"] not in ADMISSIBLE:
            assert row["decision"] == "REFUSED", row["id"]
            assert row["rejection_reason"], row["id"]
        elif not row["eligibility"]:
            assert row["decision"] == "REFUSED", row["id"]
    source = {c["id"]: c for c in
              S.p0("CANDIDATE_EXTRACTION_DISPOSITION_v1.0.json")["candidates"]}
    for row in rows:
        assert row["eligibility"] == bool(source[row["id"]]["eligible_for_extraction"])


def test_reference_only_not_copied():
    rows = [r for r in S.load("EXTRACTION_DECISION_FREEZE")["candidates"]
            if r["classification"] == "REFERENCE_ONLY"]
    assert len(rows) == 4
    for row in rows:
        assert row["decision"] == "REFUSED"
        assert row["copied_files"] == 0
        assert row["target_stage"] == "study_only_no_copy"


def test_no_authority_bearing_admitted():
    rows = S.load("EXTRACTION_DECISION_FREEZE")["candidates"]
    for row in rows:
        if row["classification"] in {"AUTHORITY_BEARING", "PROHIBITED"}:
            assert row["decision"] == "REFUSED", row["id"]
            assert row["target_stage"] == "NEVER", row["id"]
            reason = row["rejection_reason"].lower()
            assert "authority" in reason or "prohibited" in reason


def test_zero_extracted_files():
    d = S.load("EXTRACTION_DECISION_FREEZE")
    assert d["arithmetic"]["copied_files"] == 0
    assert all(not r["extracted_at_b6_i0"] for r in d["candidates"])
    added = S.changed_since(S.BASE_SHA)
    copied = [p for p in added if p.startswith("infrastructure/control-plane/src/")]
    assert copied == []


def test_limitations_binding():
    source = {c["id"]: c for c in
              S.p0("CANDIDATE_EXTRACTION_DISPOSITION_v1.0.json")["candidates"]}
    for row in S.load("EXTRACTION_DECISION_FREEZE")["candidates"]:
        assert row["limitation"] == source[row["id"]]["limitation_or_prohibition"]
        if row["classification"] == "EXTRACTABLE_WITH_LIMITATION":
            assert row["limitation"] not in ("", "none")


def test_operator_decision_pending():
    rows = S.load("EXTRACTION_DECISION_FREEZE")["candidates"]
    assert {r["operator_decision"] for r in rows} <= {"PENDING_OPERATOR_REVIEW", "REFUSED"}
    assert not [r for r in rows if r["operator_decision"] == "APPROVED"]


def test_census_30_rows():
    api = S.load("API_PRINCIPLES_AND_FIREWALL")
    assert api["rows_total"] == len(api["symbols"]) == 30
    sections = {r["section"] for r in api["symbols"] if r["section"] != "PROHIBITED"}
    assert len(sections) == 25
    assert len({r["symbol"] for r in api["symbols"]}) == 30


def test_public_stable_zero():
    api = S.load("API_PRINCIPLES_AND_FIREWALL")
    dist = api["distribution"]
    assert dist["public_stable"] == 0
    assert dist["private"] == 0
    assert dist["public_experimental"] == 8
    assert dist["internal"] == 10
    assert dist["deferred"] == 7
    assert dist["prohibited"] == 5
    assert api["observed"] == {"exports": 0, "public_stable": 0, "implemented_symbols": 0,
                               "packaged": False}


def test_exported_at_p0_historical():
    api = S.load("API_PRINCIPLES_AND_FIREWALL")
    assert api["export_policy"]["exports_at_p0"] == 0
    assert api["export_policy"]["public_stable_symbols"] == 0
    assert not any(r["exported_at_p0"] for r in api["symbols"])
    assert not any(r["exported_at_b6_i0"] for r in api["symbols"])


def test_prohibited_symbols_absent():
    api = S.load("API_PRINCIPLES_AND_FIREWALL")
    prohibited = [r for r in api["symbols"] if r["classification"] == "prohibited"]
    assert len(prohibited) == 5
    assert {r["symbol"] for r in prohibited} == {
        "oce.authority.admit", "oce.recovery.enact", "oce.state.canonical_store",
        "oce.credentials.provider", "oce.scheduler.lease"}
    assert all(r["authority"] == "prohibited" for r in prohibited)
    assert all(r["observed_state"] == "NOT_IMPLEMENTED" for r in prohibited)


def test_no_wildcard_or_private_reexport():
    api = S.load("API_PRINCIPLES_AND_FIREWALL")
    assert not any("*" in r["symbol"] for r in api["symbols"])
    assert "wildcard_export" in api["prohibitions"]
    assert "private_name_reexport" in api["prohibitions"]
    symbolic = [r["symbol"] for r in api["symbols"] if r["symbol"].startswith("oce.")]
    assert len(symbolic) >= 25
    for symbol in symbolic:
        assert symbol.count(".") >= 2, symbol
        assert "._" not in symbol, symbol


def test_public_surface_contract_fields():
    api = S.load("API_PRINCIPLES_AND_FIREWALL")
    public = [r for r in api["symbols"] if r["classification"] == "public_experimental"]
    assert len(public) == 8
    for row in public:
        for field in ("typed_inputs", "typed_outputs", "error_behavior", "refusal_semantics",
                      "version_introduced", "compatibility_promise", "documentation_obligation",
                      "tests_planned", "examples_planned", "dependency_boundary", "owner",
                      "authority"):
            assert row[field] not in (None, "", []), (row["symbol"], field)
        assert row["compatibility_status"] == "UNPROVEN"
        assert row["authority"] == "none"


def test_environment_authority_absent():
    api = S.load("API_PRINCIPLES_AND_FIREWALL")
    assert "environment_variable_authority" in api["prohibitions"]
    assert "hidden_global_state" in api["prohibitions"]
    for script in S.SCRIPTS_I0:
        text = (S.SCRIPTS / script).read_text(encoding="utf-8")
        assert "os.environ" not in text, script
        assert "getenv" not in text, script
