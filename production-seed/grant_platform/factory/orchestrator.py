"""G1 Wave 4 — full Grant factory orchestrator (G1.7/G1.8).

End-to-end: blueprint -> section drafting -> synthesis -> budget -> full QA
-> DOCX/PDF rendering -> SUBMISSION_READY_MOCK package.

The orchestrator is the composition boundary the Wave 5 API drives. It
takes an optional governed model_invoke callable; None selects the honest
deterministic lane (labeled as such, never passed off as model output).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from grant_platform.factory.blueprint import ApplicationBlueprint, build_blueprint
from grant_platform.factory.budget import BudgetReport, build_budget
from grant_platform.factory.drafting import DraftingReport, draft_sections
from grant_platform.factory.qa import FullQAReport, run_full_qa
from grant_platform.factory.render import render_docx, render_pdf
from grant_platform.factory.synthesis import SynthesisReport, synthesize

SUBMISSION_READY_MOCK = "SUBMISSION_READY_MOCK"
BLOCKED = "BLOCKED"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class FactoryPackage:
    blueprint: ApplicationBlueprint
    draft: DraftingReport
    synthesis: SynthesisReport
    budget: BudgetReport
    qa: FullQAReport
    docx: object
    pdf: object
    project_id: str
    revision_id: str
    status: str
    model_runs: list[dict] = field(default_factory=list)
    generated_at: str = ""
    integrity: object | None = None

    @property
    def readiness_state(self) -> str:
        """Explicit readiness outcome: never claim READY when gaps remain.
        Integrity pass outranks the writer-level claim scan (mission §28)."""
        if self.integrity is not None:
            return self.integrity.readiness_state
        unresolved = self.draft.unsupported_material_claims()
        if self.qa.failures:
            return "QA_BLOCKED"
        if unresolved:
            return "NEEDS_CLIENT_INPUT"
        return "READY_FOR_REVIEW"

    @property
    def artifact_label(self) -> str:
        """DRAFT_BLOCKED when not ready — drafts are kept, never deleted
        (mission §32)."""
        return ("DRAFT_READY_FOR_REVIEW" if self.readiness_state
                == "READY_FOR_REVIEW" else "DRAFT_BLOCKED")

    def summary(self) -> dict:
        unresolved = self.draft.unsupported_material_claims()
        claim_counts: dict[str, int] = {}
        for c in self.draft.claims:
            claim_counts[c.classification] = claim_counts.get(c.classification, 0) + 1
        return {
            "project_id": self.project_id,
            "revision_id": self.revision_id,
            "status": self.status,
            "readiness_state": self.readiness_state,
            "generation_mode": self.draft.generation_mode,
            "sections": len(self.draft.sections),
            "word_count": sum(s.word_count
                              for s in self.draft.sections.values()),
            "claims": (self.integrity.ledger_summary.get("total")
                       if self.integrity else len(self.draft.claims)),
            "claim_counts": (self.integrity.ledger_summary.get("by_class")
                             if self.integrity else claim_counts),
            "unsupported": len(unresolved),
            "qa_pass": self.qa.pass_count,
            "qa_fail": len(self.qa.failures),
            "budget_total": self.budget.total,
            "ceiling": self.budget.ceiling,
            "within_ceiling": self.budget.within_ceiling,
            "docx_pages": self.docx.page_count_estimate,
            "pdf_pages": self.pdf.page_count_estimate,
            "submission_enabled": False,
            "generated_at": self.generated_at,
        }


def run_factory(*, project_id: str = "proj-1",
                revision_id: str = "opp_rev_ga_501_1",
                deadline: str | None = "2026-10-15",
                ceiling: str | None = "50000.00",
                model_invoke: Callable | None = None,
                model_id: str | None = None,
                client_budget_lines: list | None = None,
                blueprint: ApplicationBlueprint | None = None,
                fact_pack=None,
                profile=None,
                missing_matrix=None,
                client_answers=(),
                applicant_status=None,
                as_of=None) -> FactoryPackage:
    """Run the full factory. Returns a SUBMISSION_READY_MOCK package when
    all QA hard gates AND the global integrity pass hold, BLOCKED
    otherwise (never fake-ready).

    Quality path (G1-QUALITY): when a solicitation profile and organization
    fact pack are supplied with a live model_invoke, sections are planned,
    drafted, critiqued, and revised against the REAL funder requirements
    (draft_sections_quality). Otherwise the plain lane applies.

    G1-INTEGRITY: after synthesis, the complete final narrative goes
    through claim extraction + temporal/numeric/status gates + missing-
    fact enforcement. Unresolved CRITICAL facts force NEEDS_CLIENT_INPUT;
    integrity contradictions force QA_BLOCKED (artifact labeled
    DRAFT_BLOCKED)."""
    bp = blueprint or build_blueprint(
        revision_id=revision_id, deadline=deadline,
        funding_ceiling=ceiling)
    effective_revision = bp.opportunity_revision_id or revision_id
    effective_deadline = bp.deadline or deadline
    if profile is not None and fact_pack is not None and model_invoke is not None:
        from grant_platform.factory.quality_drafting import draft_sections_quality
        from grant_platform.factory.integrity import build_budget_fact_pack
        research = getattr(bp, "research_block", "")
        # Canonical budget is final BEFORE drafting so budget prose never
        # invents a second budget (mission §12-§14). Build it now and pass
        # the flattened BudgetFactPack to the drafting lane read-only.
        budget = build_budget(ceiling=ceiling or "50000.00",
                              client_lines=client_budget_lines)
        budget_facts = build_budget_fact_pack(budget)
        draft = draft_sections_quality(
            bp, fact_pack=fact_pack, profile=profile,
            research_block=research,
            model_invoke=model_invoke, model_id=model_id,
            client_answers=client_answers,
            applicant_status=applicant_status,
            as_of=(as_of.isoformat() if as_of else ""),
            budget_facts=budget_facts,
            budget=budget)
    else:
        draft = draft_sections(bp, model_invoke=model_invoke,
                               model_id=model_id)
        budget = build_budget(ceiling=ceiling or "50000.00",
                              client_lines=client_budget_lines)
    synthesis = synthesize(bp, draft)
    qa = run_full_qa(blueprint=bp, draft=draft, budget=budget,
                     synthesis=synthesis,
                     expected_deadline=effective_deadline or "",
                     expected_revision=effective_revision)

    # --- Global integrity pass (G1-INTEGRITY, mission §31) -------------
    from grant_platform.factory.integrity import run_integrity_pass
    from grant_platform.factory.factpack import build_missing_fact_matrix
    integrity = None
    if fact_pack is not None:
        # As-of date (mission §14): the application's factual present is
        # the submission deadline unless the caller overrides it.
        effective_as_of = as_of
        if effective_as_of is None and bp.deadline:
            import re as _re
            from datetime import date as _date
            m = _re.match(r"(\d{4})-(\d{2})-(\d{2})", bp.deadline)
            mon = dict(zip(("January", "February", "March", "April",
                            "May", "June", "July", "August", "September",
                            "October", "November", "December"), range(1, 13)))
            if m:
                effective_as_of = _date(int(m.group(1)), int(m.group(2)),
                                        int(m.group(3)))
            else:
                mm = _re.match(
                    r"(January|February|March|April|May|June|July|August"
                    r"|September|October|November|December)\s+(\d{1,2}),?\s+"
                    r"((?:19|20)\d{2})", bp.deadline)
                if mm:
                    effective_as_of = _date(int(mm.group(3)),
                                            mon[mm.group(1)],
                                            int(mm.group(2)))
        matrix = missing_matrix or build_missing_fact_matrix(fact_pack)
        integrity = run_integrity_pass(
            sections=draft.sections, fact_pack=fact_pack,
            matrix=matrix, answers=client_answers, budget=budget,
            profile=profile, applicant_status=applicant_status,
            as_of=effective_as_of)
        # Integrity gates join the hard-gate set (mission §28).
        if integrity.unresolved_critical:
            qa.results.append(type(qa.results[0])(
                "no_unresolved_critical_facts", "FAIL",
                f"unresolved CRITICAL facts: "
                f"{[m.fact_id for m in integrity.unresolved_critical]}"))
        if integrity.dosage_breaches:
            qa.results.append(type(qa.results[0])(
                "no_prohibited_claim_breaches", "FAIL",
                f"{len(integrity.dosage_breaches)} prohibited claim(s) "
                f"asserted while fact unresolved"))
        if integrity.temporal_conflicts:
            qa.results.append(type(qa.results[0])(
                "temporal_consistency", "FAIL",
                f"{len(integrity.temporal_conflicts)} temporal "
                f"contradiction(s) as-of {integrity.as_of}"))
        if integrity.numeric_conflicts:
            qa.results.append(type(qa.results[0])(
                "numeric_consistency", "FAIL",
                f"{len(integrity.numeric_conflicts)} numeric "
                f"contradiction(s)"))
        if integrity.derived_conflicts:
            qa.results.append(type(qa.results[0])(
                "derived_arithmetic", "FAIL",
                f"{len(integrity.derived_conflicts)} derived-arithmetic "
                f"contradiction(s)"))
        if integrity.drift_conflicts:
            qa.results.append(type(qa.results[0])(
                "cross_section_drift", "FAIL",
                f"{len(integrity.drift_conflicts)} cross-section "
                f"quantity-drift contradiction(s)"))
        if integrity.status_conflicts:
            qa.results.append(type(qa.results[0])(
                "applicant_status_consistency", "FAIL",
                f"{len(integrity.status_conflicts)} status "
                f"contradiction(s)"))
    # per-section protected facts are a hard gate for LIVE_MODEL sections
    model_sections = [s for s in draft.sections.values()
                      if s.generation_mode == "LIVE_MODEL"]
    if any(not s.protected_facts_preserved for s in model_sections):
        qa.results.append(type(qa.results[0])(
            "protected_facts_live_lane", "FAIL",
            "live lane altered a protected fact"))

    if qa.submission_ready_mock and (
            integrity is None or
            integrity.readiness_state == "READY_FOR_REVIEW"):
        status = SUBMISSION_READY_MOCK
    else:
        status = BLOCKED

    docx = render_docx(draft.sections,
                       artifact_version_id=f"av-{project_id}-{_now()}",
                       project_ref=project_id, revision_ref=effective_revision)
    pdf = render_pdf(draft.sections,
                     artifact_version_id=f"av-{project_id}-{_now()}",
                     project_ref=project_id, revision_ref=effective_revision)

    return FactoryPackage(
        blueprint=bp, draft=draft, synthesis=synthesis, budget=budget,
        qa=qa, docx=docx, pdf=pdf, project_id=project_id,
        revision_id=revision_id, status=status,
        model_runs=draft.model_runs, generated_at=_now(),
        integrity=integrity)
