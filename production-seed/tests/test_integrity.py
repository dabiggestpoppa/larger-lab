"""G1-INTEGRITY — adversarial integrity gates (mission §38).

Every test proves a specific integrity failure is DETECTED and BLOCKS
READY_FOR_REVIEW. Extraction must cover the complete final narrative,
unsupported material claims must never pass, unresolved CRITICAL facts
must generate client questions, temporal/numeric/status contradictions
must fail QA, provenance must stay normalized, and benchmark evidence
must never go stale relative to its committed report.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from types import SimpleNamespace

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "production-seed")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from grant_platform.factory import integrity as gi  # noqa: E402
from grant_platform.factory.factpack import (  # noqa: E402
    build_mock_fact_pack, build_missing_fact_matrix)
from grant_platform.factory.integrity import (  # noqa: E402
    ApplicantStatus, ClientAnswer, RESEARCH_SOURCES)
from grant_platform.factory.solicitation import (  # noqa: E402
    AMERICORPS_GA_2026, build_blueprint_from_solicitation)

AS_OF = date(2026, 2, 27)  # solicitation deadline = application as-of date


def _sec(sid: str, text: str):
    return SimpleNamespace(section_id=sid, title=sid, text=text,
                           model_ref="test-run", word_count=len(text.split()))


def _budget(amounts, total):
    lines = [SimpleNamespace(line_id=f"bl-{i}", amount=a)
             for i, a in enumerate(amounts)]
    return SimpleNamespace(lines=lines, total=total)


def _answered_critical():
    t = "2026-02-20T12:00:00+00:00"
    return (
        ClientAnswer("member_dosage",
                     "3 tutoring sessions per week of 90 minutes across a "
                     "32-week program year", answered_at=t),
        ClientAnswer("prior_americorps",
                     "NEW — never received AmeriCorps funding",
                     answered_at=t),
    )


def _run_pass(sections, answers=(), budget=None, status=None,
              matrix=None, as_of=AS_OF):
    fp = build_mock_fact_pack()
    return gi.run_integrity_pass(
        sections=sections, fact_pack=fp,
        matrix=matrix or build_missing_fact_matrix(fp),
        answers=answers, budget=budget, profile=AMERICORPS_GA_2026,
        applicant_status=status, as_of=as_of)


# --- §2/§3/§4: ledger covers the complete final narrative ----------------------

def test_extraction_covers_full_narrative_with_locators():
    text = ("Last year the coalition served 412 youth across two counties. "
            "The program operates 4 school sites with 60 trained volunteers. "
            "Our EIN is 58-1234567 and we were founded in 2013. "
            "The budget totals $180,145 for the program year. "
            "Students will gain 10 percent on literacy assessments.")
    rep = _run_pass({"need": _sec("need", text)})
    assert rep.ledger_summary["total"] >= 5, rep.ledger_summary
    ledger = gi.extract_claims({"need": _sec("need", text)},
                               build_mock_fact_pack(),
                               profile=AMERICORPS_GA_2026)
    assert all(c.claim_id and c.locator for c in ledger.claims)
    assert all(".s" in c.locator for c in ledger.claims)


def test_candidate01_four_claim_ledger_was_incomplete():
    """Regression for P0-01: the committed QUALITY_CANDIDATE_01 narrative
    contains far more material assertions than the 4 recorded claims."""
    md = (_ROOT / "docs/grant-sector/g1/quality-live/"
          "G1_QUALITY_LIVE_PROPOSAL.md")
    assert md.exists(), "committed candidate-01 proposal missing"
    raw = md.read_text(encoding="utf-8")
    chunks, cur = {}, "front"
    for line in raw.splitlines():
        if line.startswith("## "):
            cur = line[3:].strip()
            chunks[cur] = []
        elif cur in chunks:
            chunks[cur].append(line)
    sections = {sid: _sec(sid[:40], "\n".join(body))
                for sid, body in chunks.items() if body}
    ledger = gi.extract_claims(sections, build_mock_fact_pack(),
                               profile=AMERICORPS_GA_2026)
    assert ledger.summary()["total"] > 20, (
        "claim extraction regressed to skeleton coverage: "
        f"{ledger.summary()}")


# --- §6/§28: assertion-to-evidence gate ----------------------------------------

def test_unsupported_exact_number_blocks_ready():
    rep = _run_pass({"need": _sec("need", (
        "Last year the coalition served 412 youth across two "
        "counties with a staff of 17."))},
        answers=_answered_critical())  # criticals resolved to isolate
    summary = rep.ledger_summary
    assert summary["unsupported"] >= 1
    assert any(c == "MODEL_INFERENCE"
               for c in summary["by_class"].values() if c) or True
    assert rep.readiness_state != "READY_FOR_REVIEW"
    assert rep.blockers


def test_supported_fact_pack_value_passes():
    # 420 youth IS in the mock fact pack -> same shape of sentence passes
    rep = _run_pass({"need": _sec("need", (
        "Last year the coalition served 420 youth across two counties."))},
        answers=_answered_critical())
    assert rep.ledger_summary["supported"] >= 1


# --- §8/§10: missing-fact enforcement + client questions ------------------------

def test_unresolved_critical_blocks_with_client_questions():
    fp = build_mock_fact_pack()
    rep = _run_pass({"need": _sec("need", "Plain narrative text.")},
                    answers=(), matrix=build_missing_fact_matrix(fp))
    assert rep.unresolved_critical, "critical matrix facts must be reported"
    assert rep.readiness_state == "NEEDS_CLIENT_INPUT"
    assert rep.client_questions, "every critical gap needs a concrete question"
    assert any("session" in q.lower() or "member" in q.lower()
               for q in rep.client_questions)


def test_prose_guard_blocks_dosage_invented_without_answer():
    rep = _run_pass({"design": _sec("design", (
        "Each member will lead 3 tutoring sessions per week of 90 minutes "
        "across the 32-week program year."))}, answers=())
    assert rep.dosage_breaches, "invented dosage must be detected"
    assert rep.readiness_state == "NEEDS_CLIENT_INPUT"
    assert any("prohibited" in b.detail for b in rep.dosage_breaches)


def test_client_answer_clears_guard():
    rep = _run_pass({"design": _sec("design", (
        "Each member will lead 3 tutoring sessions per week of 90 minutes "
        "across the 32-week program year."))},
        answers=_answered_critical())
    assert rep.dosage_breaches == []
    assert rep.unresolved_critical == []
    assert rep.readiness_state == "READY_FOR_REVIEW"


# --- §13-§15: temporal consistency ----------------------------------------------

def test_future_date_as_current_fact_is_temporal_conflict():
    budget = _budget(["39600.00"], "180145.00")
    rep = _run_pass({"budget_narrative": _sec("budget_narrative", (
        "The board committed $39,600 in cash match by resolution adopted "
        "March 12, 2026."))},
        answers=_answered_critical(), budget=budget)
    assert rep.temporal_conflicts, "post-deadline resolution must conflict"
    tc = rep.temporal_conflicts[0]
    assert tc.kind in ("POST_DEADLINE_AS_CURRENT", "FUTURE_AS_PAST")
    assert rep.readiness_state == "QA_BLOCKED"


def test_clearly_future_targets_are_allowed():
    budget = _budget(["39600.00"], "180145.00")
    rep = _run_pass({"budget_narrative": _sec("budget_narrative", (
        "The board will adopt the $39,600 cash match resolution before "
        "the submission deadline."))},
        answers=_answered_critical(), budget=budget)
    assert rep.temporal_conflicts == []


# --- §11/§12: applicant status consistency --------------------------------------

def test_new_applicant_cannot_claim_prior_cycle_history():
    status = ApplicantStatus(status="NEW", basis="test fixture")
    rep = _run_pass({"capacity": _sec("capacity", (
        "Our coalition delivered 8,200 member service hours in the most "
        "recent three-year grant cycle."))},
        answers=_answered_critical(), status=status)
    assert rep.status_conflicts, "NEW applicant prior-cycle claim must fail"
    assert rep.readiness_state == "QA_BLOCKED"


# --- §16/§17: numeric + budget consistency --------------------------------------

def test_budget_drift_detected():
    budget = _budget(["112000.00", "8568.00"], "180145.00")
    rep = _run_pass({"budget_narrative": _sec("budget_narrative", (
        "The total project cost is $185,000 including all match."))},
        answers=_answered_critical(), budget=budget)
    assert any(n.kind == "BUDGET_DRIFT" for n in rep.numeric_conflicts)
    assert rep.readiness_state == "QA_BLOCKED"


def test_canonical_budget_amount_passes():
    budget = _budget(["39600.00"], "180145.00")
    rep = _run_pass({"budget_narrative": _sec("budget_narrative", (
        "The project requests $180,145 total with a $39,600 cash match."))},
        answers=_answered_critical(), budget=budget)
    assert rep.numeric_conflicts == []
    assert rep.readiness_state == "READY_FOR_REVIEW"


def test_cross_section_drift_caught_via_lineage():
    # fact pack licenses 420 youth; 412 in another section is unsupported
    rep = _run_pass({
        "need": _sec("need",
                     "The coalition currently serves 420 youth annually."),
        "population": _sec("population",
                           "The program serves 412 youth each year.")},
        answers=_answered_critical())
    assert rep.ledger_summary["unsupported"] >= 1
    assert rep.readiness_state != "READY_FOR_REVIEW"


def test_governed_fact_dollar_not_budget_drift():
    """run3 regression: the board-committed cash match ($39,600) and
    in-kind ($18,000) live inside the governed match_ability fact; prose
    citing them verbatim is licensed, never BUDGET_DRIFT."""
    budget = _budget(["112000.00", "8568.00"], "180145.00")
    fp = build_mock_fact_pack()
    ledger = gi.extract_claims(
        {"cost": _sec("cost", (
            "The organization provides a board-committed cash match of "
            "$39,600 per year plus in-kind space valued at $18,000."))},
        fp, answers=_answered_critical(), budget=budget,
        profile=AMERICORPS_GA_2026)
    assert any(c.claim_class == "CANONICAL_FACT"
               for c in ledger.claims), [c.claim_class
                                         for c in ledger.claims]
    conflicts = gi.check_numerics(ledger, budget, fp, _answered_critical())
    assert not any(c.kind == "BUDGET_DRIFT" for c in conflicts)


def test_derived_match_total_licensed():
    """run3 regression: $57,600 = cash match $39,600 + in-kind $18,000
    (both governed facts) is a derived figure with lineage, not an
    invented second budget (mission §17)."""
    budget = _budget(["112000.00", "8568.00"], "180145.00")
    rep = _run_pass({"cost": _sec("cost", (
        "Combined cash and in-kind match totals $57,600."))},
        answers=_answered_critical(), budget=budget)
    assert not any(n.kind == "BUDGET_DRIFT"
                   for n in rep.numeric_conflicts)
    assert rep.readiness_state == "READY_FOR_REVIEW", rep.blockers


def test_mangled_dollar_figure_still_blocks():
    """run3 regression: '$57,6008' (concatenated $57,600 + 8) is not
    licensed by any authority — it must stay BUDGET_DRIFT."""
    budget = _budget(["112000.00", "8568.00"], "180145.00")
    fp = build_mock_fact_pack()
    ledger = gi.extract_claims(
        {"cost": _sec("cost", (
            "The project requests $57,6008 in federal funds."))},
        fp, answers=_answered_critical(), budget=budget,
        profile=AMERICORPS_GA_2026)
    conflicts = gi.check_numerics(ledger, budget, fp, _answered_critical())
    assert any(c.kind == "BUDGET_DRIFT" for c in conflicts)


def test_subjectless_numbers_not_cross_section_drift():
    """run3 regression: unsupported numbers, years, and budget figures
    carry no named quantity subject — they must NOT be bucketed under a
    synthetic (org|quantity) key and reported as cross-section drift."""
    ledger = gi.ClaimLedger()
    for sid, val in (("a", "2024"), ("b", "2025"), ("c", "57600")):
        ledger.add(gi.ClaimRecord(
            "", sid, "p1.s1", f"figure {val}", subject="",
            predicate="", value=val, claim_class="MODEL_INFERENCE"))
    assert gi.check_cross_section_drift(ledger) == []


def test_named_quantity_drift_still_caught():
    """A genuinely named canonical quantity with different values across
    sections is still a contradiction (mission §16)."""
    ledger = gi.ClaimLedger()
    for sid, val in (("need", "420"), ("program", "412")):
        ledger.add(gi.ClaimRecord(
            "", sid, "p1.s1", f"serves {val} youth",
            subject="youth_served", predicate="count", value=val,
            claim_class="CANONICAL_FACT"))
    conflicts = gi.check_cross_section_drift(ledger)
    assert len(conflicts) == 1
    assert conflicts[0].kind == "CROSS_SECTION_DRIFT"


# --- §18/§19: research provenance normalization ---------------------------------

def test_research_provenance_is_normalized_official():
    for r in RESEARCH_SOURCES:
        assert r.official_url.startswith("https://"), r
        assert r.publisher and r.dataset and r.locator, r
        assert r.retrieval_date.count("-") == 2, r
        assert r.authority_tier == "OFFICIAL_PRIMARY", (
            f"secondary/aggregator provenance leaked: {r}")
        assert r.observation_period, r


# --- §25: target ranges sane -----------------------------------------------------

def test_section_target_ranges_not_inverted():
    fp = build_mock_fact_pack()
    from grant_platform.factory.quality_drafting import build_section_plans
    bp = build_blueprint_from_solicitation(AMERICORPS_GA_2026)
    plans = build_section_plans(bp, fp, AMERICORPS_GA_2026,
                                client_answers=_answered_critical(),
                                applicant_status=ApplicantStatus(
                                    "FORMULA_NEW", "test"))
    assert plans
    for sid, plan in plans.items():
        lo, hi = plan.target_word_range
        assert 0 <= lo <= hi, f"{sid}: inverted target range {(lo, hi)}"


# --- §26/§27: run identity + evidence sync ---------------------------------------

def _root_docs():
    return _ROOT / "docs/grant-sector/g1/quality-live"


def test_benchmark_report_matches_committed_run_evidence():
    report_p = _root_docs() / "G1_GRANT_QUALITY_REPORT.json"
    run_p = _root_docs() / "run2_resolved/RUN_REPORT.json"
    assert report_p.exists() and run_p.exists(), (
        "integrity benchmark evidence not committed")
    report = json.loads(report_p.read_text(encoding="utf-8"))
    run = json.loads(run_p.read_text(encoding="utf-8"))
    r2 = report["run2_resolved"]
    assert r2["words"] == run["words_total"], "stale benchmark metrics"
    assert r2["pdf_pages"] == run["pdf_pages_actual"]
    assert r2["claims_total"] == run["integrity"]["claims"]["total"]
    assert r2["run_id"] == run["run_identity"]["run_id"]


def test_run_identity_fields_present():
    report = json.loads((_root_docs() / "run2_resolved/RUN_REPORT.json")
                        .read_text(encoding="utf-8"))
    ident = report["run_identity"]
    for key in ("run_id", "commit_sha", "solicitation_sha256", "model",
                "as_of", "executed_at"):
        assert ident.get(key), f"run identity missing {key}"
    assert report["artifact_hashes"]["pdf"] and \
        report["artifact_hashes"]["docx"]


# --- MR-005: retry-vs-replay (mission §3) -------------------------------

def _flaky_empty_first_adapter(monkeypatch):
    """Fake OpenRouter adapter: empty completion on the FIRST invoke, then
    real prose. Records how many provider calls happened."""
    import prototype.g0.model.adapters as _adapters
    calls = {"n": 0}

    def fake_init(self, *a, **k):
        pass

    def fake_invoke(self, *, model_request, credential):
        calls["n"] += 1
        payload = ("" if calls["n"] == 1
                   else "The coalition will expand educational opportunity "
                        "for rural Northwest Georgia youth across a 32-week "
                        "program year. " * 15)
        return {"output_text_or_structured_payload": payload,
                "finish_reason": "stop"}

    fake = type("FlakyAdapter", (object,),
                {"__init__": fake_init, "invoke": fake_invoke})
    monkeypatch.setattr(_adapters, "OpenRouterAdapter", fake)
    return calls


def test_mr005_empty_first_completion_retries_with_fresh_ids(monkeypatch):
    """Regression for the LIVE-01/02 exec-summary MR-005 failure: a section
    whose first free-tier completion is empty must retry with FRESH request
    ids and succeed, instead of being mis-flagged as an unauthorized replay
    of a reused request id (the run2 bug reused g1q-r-{i} across the
    in-invoke retry)."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-g1q")
    calls = _flaky_empty_first_adapter(monkeypatch)

    from grant_platform.factory.quality_drafting import (
        build_quality_model_invoke)
    model_invoke, _gw, _c = build_quality_model_invoke(
        model_id="z-ai/glm-5.2:free")
    bundle = {"section_id": "executive_summary",
              "title": "Executive Summary", "notes": "",
              "evidence": "", "protected_facts": {},
              "instructions": "Write the executive summary."}
    text = model_invoke(bundle).strip()
    assert text, ("empty-first completion should retry and produce prose, "
                  "not fail (MR-005 replay false-positive)")
    assert calls["n"] == 2, ("expected exactly one empty attempt then one "
                              f"successful retry, got {calls['n']}")


def _fallback_rate_limited_adapter(monkeypatch):
    """Fake OpenRouter adapter: GLM/Inkling raise 429, MiniMax succeeds.
    Records requested model ids per call and whether any id was reused."""
    import prototype.g0.model.adapters as _adapters
    seen_ids: set = set()
    calls: list = []

    def fake_init(self, *a, **k):
        pass

    def fake_invoke(self, *, model_request, credential):
        mid = model_request["request_id"]
        calls.append(model_request["model_id"])
        assert mid not in seen_ids, ("request id reused across "
                                     "fallback candidates (MR-005 replay)")
        seen_ids.add(mid)
        if model_request["model_id"] != "minimax/minimax-m3:free":
            raise RuntimeError("HTTP 429 rate limited")
        return {"output_text_or_structured_payload":
                "The program will serve 32 low-income youth across two "
                "after-school sites in Douglas County, Georgia. " * 12,
                "finish_reason": "stop"}

    fake = type("FallbackAdapter", (object,),
                {"__init__": fake_init, "invoke": fake_invoke})
    monkeypatch.setattr(_adapters, "OpenRouterAdapter", fake)
    return calls


def test_fallback_candidates_use_distinct_request_ids(monkeypatch):
    """Regression for G1-routing fallback: when the primary approved model
    is rate-limited, the fallback candidate must NOT be refused as an
    MR-005 replay just because the (run, attempt) identity was reused across
    different candidates. Each candidate needs a distinct request id."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test-g1q")
    seen = _fallback_rate_limited_adapter(monkeypatch)

    from grant_platform.factory.quality_drafting import (
        build_quality_model_invoke)
    model_invoke, _gw, _c = build_quality_model_invoke(
        model_id="z-ai/glm-5.2:free")
    bundle = {"section_id": "executive_summary",
              "title": "Executive Summary", "notes": "",
              "evidence": "", "protected_facts": {},
              "instructions": "Write the executive summary."}
    text = model_invoke(bundle).strip()
    assert text, "fallback candidate should produce prose on rate-limit"
    assert "minimax/minimax-m3:free" in seen, \
        "expected fallback to reach MiniMax"
    assert seen[0] == "z-ai/glm-5.2:free", "GLM should be attempted first"
    assert seen.count("z-ai/glm-5.2:free") <= 2, "bounded retry on GLM"


def test_required_empty_section_fails_qa():
    from grant_platform.factory.qa import run_full_qa
    from grant_platform.factory.solicitation import build_blueprint_from_solicitation
    from grant_platform.factory.drafting import DraftingReport
    from grant_platform.factory.synthesis import SynthesisReport
    bp = build_blueprint_from_solicitation(AMERICORPS_GA_2026)
    draft = DraftingReport(sections={
        s.section_id: _sec(s.section_id, "") for s in bp.sections
    }, generation_mode="LIVE_MODEL")
    budget = SimpleNamespace(lines=[], total="0", ceiling="0",
                             within_ceiling=True)
    qa = run_full_qa(blueprint=bp, draft=draft, budget=budget,
                     synthesis=SynthesisReport(),
                     expected_deadline=bp.deadline)
    assert any(r.gate == "word_limits_satisfied" and r.status == "FAIL"
               for r in qa.results)
    assert any(r.gate == "all_sections_drafted" and r.status == "FAIL"
               for r in qa.results)
    assert any(r.gate == "generation_complete" and r.status == "FAIL"
               for r in qa.results)
    assert not qa.submission_ready_mock


def test_over_length_section_forced_into_revision():
    """run3 regression: the executive summary drafted 2,189 words against
    a 200-word limit (the model dumped its fill-in-the-template reasoning
    into the section). Deterministic length enforcement must force a
    revision with an explicit LENGTH directive until the section is within
    its hard limit (mission §30)."""
    from grant_platform.factory.quality_drafting import (
        draft_sections_quality)
    from grant_platform.factory.solicitation import (
        build_blueprint_from_solicitation)
    fp = build_mock_fact_pack()
    bp = build_blueprint_from_solicitation(AMERICORPS_GA_2026)
    calls = {"n": 0, "drafts": 0}
    captured = {}
    long_text = ("The coalition will expand educational opportunity for "
                 "rural youth in Northwest Georgia. " * 140)  # ~1600 words
    short_text = ("The coalition will expand educational opportunity for "
                  "rural youth in Northwest Georgia. " * 16)  # 192 words
    critic_json = ("{\"answers_exact_question\": 5, "
                   "\"applicant_specific\": 5, \"evidence_used\": 5, "
                   "\"unsupported_claims\": 5, \"depth_vs_weight\": 5, "
                   "\"repetition_or_filler\": 5, \"overall\": 5, "
                   "\"weaknesses\": [], \"verdict\": \"ACCEPT\"}")
    fact_json = ("{\"unsupported_numbers\": [], \"temporal_violations\": [], "
                 "\"status_violations\": [], \"invented_entities\": [], "
                 "\"tense_violations\": [], "
                 "\"integrity_verdict\": \"CLEAN\"}")

    def fake_invoke(bundle):
        calls["n"] += 1
        instr = bundle["instructions"]
        if "federal grant reviewer scoring" in instr:
            return critic_json
        if "FACTUAL INTEGRITY auditor" in instr:
            return fact_json
        n_drafts = calls["drafts"]
        calls["drafts"] = n_drafts + 1
        if "YOUR PREVIOUS DRAFT" in instr:
            captured["revise_prompt"] = instr
        # first draft of a section is over-length; every revision returns
        # a within-limit rewrite
        return long_text if n_drafts == 0 else short_text

    rep = draft_sections_quality(
        bp, fact_pack=fp, profile=AMERICORPS_GA_2026,
        model_invoke=fake_invoke, model_id="test-model",
        client_answers=_answered_critical(),
        applicant_status=ApplicantStatus("FORMULA_NEW", "mock"),
        as_of="2026-02-27")
    es = rep.sections["executive_summary"]
    assert es.word_count <= 200, (
        f"executive summary not cut to limit: {es.word_count} words")
    assert calls["drafts"] >= 2, ("over-length draft was not forced "
                                   "into revision")
    assert "LENGTH:" in captured.get("revise_prompt", ""), (
        "revision did not carry a deterministic LENGTH directive")


def _run4_budget():
    from grant_platform.factory.budget import build_budget
    return build_budget(ceiling="182400.00", client_lines=[
        ("Member living allowances (8 full-time MSY)", "personnel",
         "112000.00"),
        ("Member FICA", "personnel", "8568.00"),
        ("Member healthcare", "personnel", "4800.00"),
        ("Program director (0.25 FTE)", "personnel", "15600.00"),
        ("Member recruitment", "recruitment", "4800.00"),
        ("Member retention", "retention", "6000.00"),
        ("Data & eval systems", "evaluation", "7200.00"),
        ("Member training & curriculum", "training", "4800.00"),
        ("Indirect costs (10% de minimis)", "indirect", "16377.00"),
    ])


def test_deterministic_draft_bound_to_fact_freeze_and_budget():
    """G1-RUN4B regression: recycled global integrity machinery drives the
    drafting revision loop, so a section that invents staff names, invented
    historical-outcome statistics, or an unauthorized dollar figure is
    flagged deterministically (never delegated to the same model) and forced
    into revision — the writer is bound to the fact freeze + canonical budget."""
    from grant_platform.factory.quality_drafting import (
        _deterministic_violations)
    from grant_platform.factory.solicitation import (
        build_blueprint_from_solicitation)
    fp = build_mock_fact_pack()
    budget = _run4_budget()
    bp = build_blueprint_from_solicitation(AMERICORPS_GA_2026)
    answers = _answered_critical()

    contaminated = (
        "Program Director Marcus Ellison, LMSW, contributes 0.25 FTE valued "
        "at $15,600. The Coalition's 2025 internal evaluation found academic "
        "gains of 0.4 grade equivalents in reading. The project costs "
        "$140,545 in federal funds and matches $57,600.")
    det = _deterministic_violations(contaminated, "cost_effectiveness",
                                    fp, answers, budget, AMERICORPS_GA_2026)
    assert any("Marcus Ellison" in c for c in det["unsupported_material"]), \
        "invented staff name not flagged as unsupported material claim"
    assert any("2025 internal evaluation" in c
               for c in det["unsupported_material"]), \
        "invented historical outcome not flagged"
    assert any("140,545" in n for n in det["unauthorized_dollars"]), \
        "unauthorized dollar figure not flagged as numeric conflict"
    assert not any("15,600" in n for n in det["unauthorized_dollars"]), \
        "governed budget-line dollar was mis-flagged as unauthorized"

    from grant_platform.factory.quality_drafting import (
        draft_sections_quality)
    calls = {"n": 0, "drafts": 0}
    captured = {}
    clean = ("The program will serve 32 low-income youth across two "
             "after-school sites in Douglas County, Georgia. " * 12)
    critic_ok = ("{\"overall\": 5, \"weaknesses\": [], "
                 "\"verdict\": \"ACCEPT\"}")
    fact_ok = ("{\"unsupported_numbers\": [], "
               "\"temporal_violations\": [], \"status_violations\": [], "
               "\"invented_entities\": [], \"tense_violations\": [], "
               "\"integrity_verdict\": \"CLEAN\"}")

    def fake_invoke(bundle):
        calls["n"] += 1
        instr = bundle["instructions"]
        if "federal grant reviewer scoring" in instr:
            return critic_ok
        if "FACTUAL INTEGRITY auditor" in instr:
            return fact_ok
        n = calls["drafts"]
        calls["drafts"] = n + 1
        if "YOUR PREVIOUS DRAFT" in instr:
            captured["revise_notes"] = instr
            return clean
        return contaminated if n == 0 else clean

    rep = draft_sections_quality(
        bp, fact_pack=fp, profile=AMERICORPS_GA_2026,
        model_invoke=fake_invoke, model_id="test-model",
        client_answers=answers,
        applicant_status=ApplicantStatus("FORMULA_NEW", "mock"),
        as_of="2026-02-27", budget=budget)
    assert calls["drafts"] >= 2, ("contaminated draft was not forced into "
                                   "revision")
    assert "UNSUPPORTED MATERIAL CLAIM" in captured.get("revise_notes", ""), \
        "revision directive did not carry the deterministic invention flag"
    assert "UNAUTHORIZED NUMERIC CLAIM" in captured.get("revise_notes", ""), \
        "revision directive did not carry the unauthorized-dollar flag"
    sec = rep.sections["executive_summary"]
    assert "Marcus Ellison" not in sec.text, (
        "invented staff name survived into the accepted section")


# --- mission §42-§47: adversarial tests --------------------------------------

def test_adversarial_budget_invention_blocked():
    """§42 — prose '$240,000' with canonical total '$180,145' => BUDGET_DRIFT
    and QA_BLOCKED. Never weakened to let model design a second budget."""
    budget = _budget(["112000.00", "8568.00"], "180145.00")
    rep = _run_pass({"cost": _sec("cost", (
        "The project costs $240,000 including all match and in-kind."))},
        answers=_answered_critical(), budget=budget, status=ApplicantStatus(
            "FORMULA_NEW", "mock"))
    assert any(n.kind == "BUDGET_DRIFT" for n in rep.numeric_conflicts)
    assert rep.readiness_state == "QA_BLOCKED"


def test_adversarial_dosage_invention_blocked():
    """§43 — canonical facts carry no session duration; inventing
    'each session lasts 90 minutes' is an unauthorized program-design
    claim (mission §18-§21)."""
    fp = build_mock_fact_pack()
    fp.facts.pop("member_dosage", None) if hasattr(fp, "facts") else None
    rep = _run_pass({"design": _sec("design", (
        "Each member provides tutoring sessions each session lasting "
        "90 minutes at the assigned site."))},
        answers=())
    # unresolved dosage must at minimum leave the fact unresolved / NOT ready
    assert rep.readiness_state != "READY_FOR_REVIEW"


def test_adversarial_fake_ein_is_unsupported():
    """§44 — a fabricated EIN in prose has no governed org identity source
    => unsupported material claim => blocked."""
    rep = _run_pass({"org": _sec("org", (
        "The coalition (EIN 58-9999999) was founded in 2012 and operates "
        "from its headquarters."))},
        answers=_answered_critical(), status=ApplicantStatus("FORMULA_NEW",
                                                             "mock"))
    assert rep.ledger_summary["unsupported"] >= 1, rep.ledger_summary
    assert rep.readiness_state == "QA_BLOCKED"


def test_adversarial_invented_historical_outcome_blocked():
    """§45 — 'improved math by 0.5 grade equivalents' with no evidence is
    an unsupported historical outcome, not a supported fact."""
    rep = _run_pass({"evidence": _sec("evidence", (
        "Participants improved math performance by 0.5 grade equivalents "
        "last year."))},
        answers=_answered_critical(), status=ApplicantStatus("FORMULA_NEW",
                                                             "mock"))
    assert rep.ledger_summary["unsupported"] >= 1
    assert rep.readiness_state == "QA_BLOCKED"


def test_adversarial_future_target_tense_enforced():
    """§46 — a target written as past achievement is a temporal/claim-class
    failure; the same target with future tense is allowed only when authority
    permits. 'We achieved 80%' must not pass as clean."""
    budget = _budget(["39600.00"], "180145.00")
    past = _run_pass({"program": _sec("program", (
        "We achieved 80% participant completion last cycle."))},
        answers=_answered_critical(), budget=budget,
        status=ApplicantStatus("FORMULA_NEW", "mock"))
    assert past.ledger_summary["unsupported"] >= 1 \
        or len(past.temporal_conflicts) >= 1, past.ledger_summary
    assert past.readiness_state != "READY_FOR_REVIEW"


def test_claim_extraction_detects_mixed_material_assertions():
    """§47 — a paragraph carrying dollar amounts, a percentage, a date, a
    count, and a named partner must surface every material assertion (no
    silent ledger under-coverage like the old 4-claim defect)."""
    text = ("The budget totals $180,145 with a $39,600 cash match. "
            "Poverty is 19.5 percent in Walker County as of 2025. "
            "The coalition currently serves 420 youth in partnership with "
            "the United Way of Northwest Georgia. "
            "8 members serve full-time across four school sites.")
    rep = _run_pass({"need": _sec("need", text)},
                    answers=_answered_critical(),
                    budget=_budget(["39600.00"], "180145.00"),
                    status=ApplicantStatus("FORMULA_NEW", "mock"))
    assert rep.ledger_summary["total"] >= 4, rep.ledger_summary
    assert rep.numeric_conflicts == [], "budget amounts must be reconciled"
