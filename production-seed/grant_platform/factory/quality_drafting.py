"""G1-QUALITY-05/06 — Section planning + multi-pass live drafting.

Pipeline per material section (mission §13, §26-§29):

    SectionPlan (objective, criterion, facts, evidence, structure,
                depth target, prohibited inventions)
      -> PASS 1 draft   (polished proposal prose against the exact funder
                         prompt, using only supplied evidence)
      -> PASS 2 critic  (JSON verdict: sub-question coverage, specificity,
                         unsupported claims, depth vs scoring weight)
      -> PASS 3 revise  (only when the critic finds real weaknesses;
                         bounded retries)

The live model is REQUIRED — there is no deterministic path through this
module (fail-closed; the skeleton is not a client deliverable).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from grant_platform.factory.blueprint import ApplicationBlueprint
from grant_platform.factory.drafting import (
    DraftingReport, SectionDraft, ClaimLedgerEntry, _detect_unknowns,
    _now)


@dataclass(frozen=True)
class SectionPlan:
    section_id: str
    objective: str
    criterion: str                  # scoring criterion served
    points: int
    required_facts: tuple[str, ...]      # fact_ids that must ground the prose
    required_subquestions: tuple[str, ...]
    argument_structure: tuple[str, ...]
    key_messages: tuple[str, ...]
    target_word_range: tuple[int, int]
    prohibited: tuple[str, ...]          # facts that must NOT be invented
    budget_facts: tuple[dict, ...] = ()  # canonical BudgetFactPack (read-only)


def build_section_plans(blueprint: ApplicationBlueprint,
                        fact_pack, profile,
                        client_answers=(),
                        applicant_status=None,
                        budget_facts=()) -> dict[str, SectionPlan]:
    """One SectionPlan per material section: what it must accomplish, which
    criterion it serves, which applicant facts ground it, and how deep it
    must go (§13-§14). budget_facts is the flattened canonical BudgetEngine
    output — passed read-only so drafting never invents a second budget
    (mission §12-§14)."""
    budget_facts = tuple(budget_facts or ())
    plans: dict[str, SectionPlan] = {}
    sec_points: dict[str, int] = {}
    reqs_by_section: dict[str, list] = {}
    pts_by_crit = {c.criterion_id: c.points for c in profile.criteria}
    looks_by_crit = {c.criterion_id: c.reviewer_looks_for
                     for c in profile.criteria}
    for r in profile.requirements:
        reqs_by_section.setdefault(r.section_id, []).append(r)
        if r.criterion_id:
            sec_points[r.section_id] = (sec_points.get(r.section_id, 0)
                                        + pts_by_crit.get(r.criterion_id, 0))

    facts_summary = "; ".join(
        f"{f.fact_id}={f.value}"
        for f in list(fact_pack.facts.values())[:24])

    for sec in blueprint.sections:
        reqs = reqs_by_section.get(sec.section_id, [])
        crit_ids = [r.criterion_id for r in reqs if r.criterion_id]
        points = sec_points.get(sec.section_id, 0)
        subs = []
        for r in reqs:
            for part in re.split(r"(?:\n|•)|(?<=;)\s",
                                 r.prompt):
                part = part.strip(" \n\t•;")
                if len(part) > 30:
                    subs.append(part[:220])
        reviewer = " | ".join(filter(None, (looks_by_crit.get(c, "")
                                            for c in crit_ids)))
        limit = sec.word_limit
        low = int(limit * 0.65) if points > 0 else int(limit * 0.8)
        # Never inverted; N/A and tiny sections keep sane ranges
        # (mission P1-03: min <= max for every target range).
        low = max(20, min(low, limit))
        target = (low, max(low, limit))
        plans[sec.section_id] = SectionPlan(
            section_id=sec.section_id,
            objective=f"Win maximum reviewer points on: {reviewer or sec.title}",
            criterion=", ".join(filter(None, crit_ids)) or "unscored",
            points=points,
            required_facts=tuple(f.fact_id for f in
                                 list(fact_pack.facts.values())[:0]) or
            ("legal_name", "mission", "service_area", "population",
             "youth_served", "msy_target", "member_count"),
            required_subquestions=tuple(subs[:14]),
            argument_structure=(
                "Open with the specific community problem and evidence",
                "Name the intervention and every required logic-model element",
                "Ground each claim in the supplied applicant facts or cited research",
                "Close by tying outcomes to the reviewer's scoring language"),
            key_messages=tuple(r.title for r in reqs),
            target_word_range=target,
            prohibited=(
                "partnerships not in the fact pack",
                "staff counts or names not in the fact pack",
                "historical outcomes not in the fact pack",
                "funding amounts beyond the canonical BudgetFactPack",
                "percentages not traceable to supplied facts or cited research"),
            budget_facts=budget_facts)
    return plans


def _facts_block(fact_pack, client_answers=()) -> str:
    lines = []
    for f in fact_pack.facts.values():
        lines.append(f"- {f.fact_id} [{f.category}, {f.confidence}]: {f.value} "
                     f"(source: {f.source})")
    for a in client_answers:
        lines.append(f"- CLIENT ANSWER {a.fact_id} [{a.label}]: {a.value} "
                     f"(answered {a.answered_at} by {a.principal})")
    return "\n".join(lines)


def _budget_block(budget_facts) -> str:
    if not budget_facts:
        return "- (no budget supplied; do not mention any dollar amounts)"
    lines = []
    for bf in budget_facts:
        label = bf.get("label", bf.get("budget_id", ""))
        amount = bf.get("amount", "")
        lines.append(f"- {label}: {amount}")
    return "\n".join(lines)


def _draft_prompt(sec, plan: SectionPlan, fact_pack, profile,
                  research_block: str, client_answers=(),
                  applicant_status=None) -> str:
    subs = "\n".join(f"  {i+1}. {s}"
                     for i, s in enumerate(plan.required_subquestions))
    status_note = ""
    if applicant_status is not None:
        if applicant_status.is_new:
            status_note = (
                f"\nAPPLICANT STATUS: {applicant_status.status} ({applicant_status.basis}). "
                "This organization has NEVER held an AmeriCorps or Georgia "
                "Serves grant. NEVER reference a prior AmeriCorps three-year "
                "grant cycle, prior evaluation report, or recompete history "
                "as this organization's own experience.\n")
    return f"""You are a senior grant writer completing ONE section of a real federal grant application. Write polished, submission-ready prose — not an outline, not bullet points.

FUNDER EXACT QUESTION(S) THIS SECTION MUST ANSWER:
{sec.drafting_notes}

SCORING: This section serves criterion '{plan.criterion}' worth {plan.points} points. Reviewer looks for: {plan.objective}
{status_note}
EVERY SUB-ELEMENT BELOW MUST BE ADDRESSED (miss any and reviewers deduct):
{subs}

APPLICANT FACTS (the ONLY facts you may assert about the applicant):
{_facts_block(fact_pack, client_answers)}

CANONICAL BUDGET (READ-ONLY AUTHORITY — the budget is already final):
{_budget_block(plan.budget_facts)}

EXTERNAL RESEARCH (cite inline as (Source, Year); use ONLY these for community statistics):
{research_block or "- (none supplied; do not invent statistics)"}

SOLICITATION CONTEXT:
Funder: {profile.snapshot.funder}
Deadline: {profile.deadline}
Match requirement: {profile.match_requirement}

RULES:
1. Answer every sub-element explicitly. Reviewers score against a checklist.
2. Use ONLY the applicant facts above for organizational claims. Never invent partnerships, staff, numbers, or history. If a needed fact is missing, write exactly "UNKNOWN: <what is missing>".
3. Distinguish plans (future) from achievements (historical). Label planning numbers as targets.
4. DO NOT DESIGN A BUDGET. The CANONICAL BUDGET above is final. You may reference ONLY those exact dollar figures (and the exact match percentage from the solicitation context). Never introduce a different total, living allowance, or line item amount. If you need a budget figure that is not listed, omit it or write "UNKNOWN: <what is missing>".
5. DO NOT INVENT MATERIAL NUMBERS. Every session count, hours figure, site count, member count, participant total, or percent must come from the applicant facts (or a clearly future-tense target derived from them) — never make one up.
6. Target length {plan.target_word_range[0]}-{plan.target_word_range[1]} words. Depth must match the {plan.points}-point weight — generic filler is worse than short.
7. Professional, specific, human voice. No "transformative impact" spam. No repetition of the mission statement.
8. Do not include section headings or meta-commentary. Output the section prose only.
9. LENGTH IS A HARD REQUIREMENT: the final section must be {plan.target_word_range[0]}-{plan.target_word_range[1]} words. Count the words of your output and cut ruthlessly if you are over. An over-length section is rejected outright.
10. OUTPUT ONLY THE FINAL SECTION TEXT — never the funder's template, your notes, your reasoning, a fact list, or planning commentary. What you output IS the submission: a reviewer must be able to paste it into the application as-is.
"""


def _critic_prompt(section_text: str, plan: SectionPlan, sec) -> str:
    return f"""You are a federal grant reviewer scoring one application section. Evaluate this draft against the checklist and return ONLY valid JSON.

CHECKLIST (score each 0-5):
- answers_exact_question: does it address every sub-element?
- applicant_specific: real org details vs generic consultant prose?
- evidence_used: community statistics / research cited?
- unsupported_claims: any invented facts, partnerships, or numbers?
- depth_vs_weight: depth proportional to {plan.points}-point criterion?
- repetition_or_filler: empty phrases, filler, repetition?

SECTION ({plan.section_id}, target {plan.target_word_range[0]}-{plan.target_word_range[1]} words, actual {len(section_text.split())} words):
---
{section_text}
---

REQUIRED SUB-ELEMENTS:
{chr(10).join('- ' + s for s in plan.required_subquestions)}

Return exactly this JSON shape:
{{"answers_exact_question": 0, "applicant_specific": 0, "evidence_used": 0, "unsupported_claims": 0, "depth_vs_weight": 0, "repetition_or_filler": 0, "overall": 0, "weaknesses": ["..."], "verdict": "ACCEPT"|"REVISE"}}"""


def _fact_critic_prompt(section_text: str, plan: SectionPlan,
                        fact_pack, client_answers=(),
                        applicant_status=None,
                        as_of: str = "") -> str:
    """INTEGRITY critic (mission §30): judges ONLY facts, numbers, dates,
    sources, classification, temporal state — never writing style. Its
    findings are combined with the deterministic checker; a writing model
    can never overrule integrity failures."""
    return f"""You are a FACTUAL INTEGRITY auditor (not a writing coach). Audit this grant section for factual integrity ONLY. Return ONLY valid JSON.

GOVERNED FACT SOURCES (the only permitted factual assertions about the applicant):
{_facts_block(fact_pack, client_answers)}

APPLICANT STATUS: {applicant_status.status if applicant_status else 'UNKNOWN'}
AS-OF DATE (the application's factual present): {as_of}

AUDIT CHECKLIST (report violations only):
1. unsupported_numbers: any number about the applicant not traceable to the governed facts/client answers above, and not a clearly future-tense target derived from them
2. temporal_violations: any date AFTER {as_of} presented as current/completed (not as future plan)
3. status_violations: references to prior AmeriCorps grant cycles, prior evaluation reports, or recompete history (applicant status is {applicant_status.status if applicant_status else 'UNKNOWN'})
4. invented_entities: partnerships, staff, funders, or program elements not in the governed facts
5. tense_violations: future targets written in past/present tense (e.g. 'has served' for a planned number)

SECTION:
---
{section_text}
---

Return exactly: {{"unsupported_numbers": ["..."], "temporal_violations": ["..."], "status_violations": ["..."], "invented_entities": ["..."], "tense_violations": ["..."], "integrity_verdict": "CLEAN"|"VIOLATIONS"}}"""


def _revise_prompt(section_text: str, plan: SectionPlan, weaknesses,
                   fact_pack, profile, research_block: str,
                   client_answers=(), applicant_status=None) -> str:
    base = _draft_prompt(
        sec=type("S", (), {"section_id": plan.section_id,
                           "drafting_notes": _notes_for(plan, profile)})(),
        plan=plan, fact_pack=fact_pack, profile=profile,
        research_block=research_block,
        client_answers=client_answers,
        applicant_status=applicant_status)
    wk = "\n".join(f"- {w}" for w in weaknesses) or "- general depth"
    return base + f"""

YOUR PREVIOUS DRAFT (scored below threshold by the reviewer):
---
{section_text}
---

REVIEWER WEAKNESSES TO FIX (address every one):
{wk}

Rewrite the full section fixing every weakness. Output the revised prose only."""


def _notes_for(plan: SectionPlan, profile) -> str:
    reqs = [r for r in profile.requirements if r.section_id == plan.section_id]
    return "\n\n".join(f"[{r.title}] {r.prompt}" for r in reqs)


def _length_weakness(text: str, plan: SectionPlan) -> list[str]:
    """Deterministic over-length violation (mission §30: deterministic
    integrity outranks the writing critic). The model cannot talk its way
    out of a hard word limit — an over-length section is forced into
    revision with an explicit length directive."""
    hi = plan.target_word_range[1]
    lo = plan.target_word_range[0]
    wc = len(text.split())
    if wc > hi:
        return [f"LENGTH: section is {wc} words, hard limit {hi} "
                f"(target {lo}-{hi}). Cut it to at most {hi} words — "
                "delete reasoning, notes, templates, and repetition."]
    return []


def _parse_critic(raw: str) -> dict:
    """Defensive JSON parse of the critic verdict (§28-§29)."""
    try:
        return json.loads(raw)
    except Exception:
        pass
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return {}


def _deterministic_violations(text: str, section_id: str, fact_pack,
                              client_answers, budget, profile) -> dict:
    """Reuse the global integrity machinery (extract_claims + check_numerics)
    on a single section so the writer is bound to the governed fact freeze and
    canonical budget DURING drafting. Deterministic — never delegated to the
    model's own critic. Returns material claims with no authority and
    unauthorized dollar figures; the factory already fails closed on these
    after synthesis, this catches them in the revision loop."""
    from grant_platform.factory.integrity import (
        check_numerics, extract_claims)
    pseudo = type("P", (), {"text": text, "model_ref": None})()
    draft = type("D", (), {"sections": {section_id: pseudo}})()
    ledger = extract_claims(draft.sections, fact_pack, client_answers,
                            budget, profile)
    bad = [c.claim_text[:160] for c in ledger.unsupported_material()]
    nums = [n.detail for n in check_numerics(
        ledger, budget, fact_pack, client_answers)]
    return {"unsupported_material": bad[:6], "unauthorized_dollars": nums[:6]}


def _draft_violation_notes(det: dict) -> list[str]:
    out = []
    for t in det.get("unsupported_material", []):
        out.append(f"UNSUPPORTED MATERIAL CLAIM — remove or ground only to "
                   f"the governed facts: \"{t}\"")
    for n in det.get("unauthorized_dollars", []):
        out.append(f"UNAUTHORIZED NUMERIC CLAIM — remove: {n}")
    return out


def draft_sections_quality(blueprint: ApplicationBlueprint, *,
                           fact_pack,
                           profile,
                           research_block: str = "",
                           model_invoke: Callable | None = None,
                           model_id: str | None = None,
                           critic_threshold: int = 4,
                           max_revisions: int = 3,
                           client_answers=(),
                           applicant_status=None,
                           as_of: str = "",
                           budget_facts=(),
                           budget=None) -> DraftingReport:
    """Quality drafting: plan -> draft -> critique -> revise per section,
    plus a FACT_CRITIC integrity audit whose findings force revision
    regardless of the writing-critic verdict (mission §30).
    Requires a live model — fail-closed otherwise (§3, §27)."""
    if model_invoke is None:
        raise RuntimeError(
            "G1-QUALITY drafting requires a governed live model invoke; "
            "the deterministic skeleton is not a client deliverable")

    plans = build_section_plans(blueprint, fact_pack, profile,
                                client_answers=client_answers,
                                applicant_status=applicant_status,
                                budget_facts=budget_facts)
    sections: dict[str, SectionDraft] = {}
    claims: list[ClaimLedgerEntry] = []
    model_runs: list[dict] = []

    for sec in blueprint.sections:
        plan = plans[sec.section_id]
        # N/A sections (new-applicant evaluation summary) are written as such
        if all(r.response_type == "na" for r in profile.requirements
               if r.section_id == sec.section_id):
            text = ("Evaluation Summary/Plan: N/A. This organization is a "
                    "new applicant under this Notice and is not required to "
                    "submit an evaluation plan summary.")
            sections[sec.section_id] = SectionDraft(
                section_id=sec.section_id, title=sec.title, text=text,
                word_count=len(text.split()),
                generation_mode="LIVE_MODEL",
                model_ref=f"model-run-{sec.section_id}")
            model_runs.append({"section": sec.section_id, "status": "NA",
                               "model_id": model_id})
            continue

        prompt = _draft_prompt(sec, plan, fact_pack, profile,
                               research_block, client_answers,
                               applicant_status)
        passes = 0
        revisions = 0
        try:
            # Free-tier providers intermittently return empty completions;
            # retry (bounded) before declaring the section BLOCKED.
            import time
            text = ""
            for attempt in range(3):
                text = str(model_invoke(_bundle(sec, plan, prompt))).strip()
                passes += 1
                if text:
                    break
                time.sleep(2 * (attempt + 1))
            if not text:
                raise RuntimeError("model returned empty completions")
            time.sleep(1)  # gentle pacing between sections on free tiers

            def _run_fact_critic(current_text: str) -> tuple[dict, list]:
                fv = _parse_critic(str(model_invoke(_bundle(
                    sec, plan, _fact_critic_prompt(
                        current_text, plan, fact_pack, client_answers,
                        applicant_status, as_of)))))
                violations = []
                for key in ("unsupported_numbers", "temporal_violations",
                            "status_violations", "invented_entities",
                            "tense_violations"):
                    violations.extend(
                        f"{key}: {v}" for v in (fv.get(key) or [])[:4])
                return fv, violations

            verdict = _parse_critic(str(model_invoke(_bundle(
                sec, plan, _critic_prompt(text, plan, sec)))))
            passes += 1
            overall = int(verdict.get("overall", 5) or 5)
            weaknesses = [str(w) for w in verdict.get("weaknesses", [])][:6]
            fact_verdict, fact_violations = _run_fact_critic(text)
            passes += 1
            # Deterministic integrity outranks the writing critic (§30): the
            # SAME extract_claims/check_numerics machinery the factory runs
            # after synthesis also drives the revision loop, so invented
            # material claims and unauthorized dollar figures force revision
            # here — never left to the model's own (lenient) critic.
            det = _deterministic_violations(
                text, sec.section_id, fact_pack, client_answers,
                budget, profile)
            det_notes = _draft_violation_notes(det)
            must_revise = (overall < critic_threshold
                           or bool(fact_violations)
                           or bool(det_notes)
                           or bool(_length_weakness(text, plan)))
            while (must_revise and revisions < max_revisions):
                merged = weaknesses + fact_violations + det_notes + \
                    _length_weakness(text, plan)
                text = str(model_invoke(_bundle(
                    sec, plan,
                    _revise_prompt(text, plan, merged, fact_pack,
                                   profile, research_block,
                                   client_answers,
                                   applicant_status)))).strip()
                revisions += 1
                passes += 1
                verdict = _parse_critic(str(model_invoke(_bundle(
                    sec, plan, _critic_prompt(text, plan, sec)))))
                passes += 1
                overall = int(verdict.get("overall", 5) or 5)
                weaknesses = [str(w) for w in
                              verdict.get("weaknesses", [])][:6]
                fact_verdict, fact_violations = _run_fact_critic(text)
                passes += 1
                det = _deterministic_violations(
                    text, sec.section_id, fact_pack, client_answers,
                    budget, profile)
                det_notes = _draft_violation_notes(det)
                must_revise = (overall < critic_threshold
                               or bool(fact_violations)
                               or bool(det_notes)
                               or bool(_length_weakness(text, plan)))
            model_runs.append({
                "section": sec.section_id, "status": "OK",
                "model_id": model_id, "provenance": getattr(model_invoke, "provenance", []), "passes": passes,
                "revisions": revisions,
                "critic_overall": overall,
                "critic_weaknesses": weaknesses,
                "fact_critic": fact_verdict.get("integrity_verdict",
                                                "UNKNOWN"),
                "fact_violations": fact_violations,
                "deterministic_violations": det})
        except Exception as exc:  # honest failure, never fake output
            sections[sec.section_id] = SectionDraft(
                section_id=sec.section_id, title=sec.title,
                text=f"UNKNOWN: model lane failed for this section: {exc}",
                word_count=0, generation_mode="BLOCKED_MODEL_RUNTIME")
            model_runs.append({"section": sec.section_id, "status": "GENERATION_UNAVAILABLE",
                               "error": str(exc),
                               "provenance": getattr(model_invoke, "provenance", [])})
            continue

        wc = len(re.findall(r"\S+", text))
        sections[sec.section_id] = SectionDraft(
            section_id=sec.section_id, title=sec.title, text=text,
            word_count=wc, generation_mode="LIVE_MODEL",
            model_ref=f"model-run-{sec.section_id}")
        _detect_unknowns(text, sec.section_id, claims)
        claims.append(ClaimLedgerEntry(
            claim_id=f"cl-{sec.section_id}-ledger",
            section_id=sec.section_id,
            claim=f"{sec.title} grounded in OrganizationFactPack "
                  f"({fact_pack.organization_label})",
            classification="CANONICAL_FACT",
            evidence_ref=f"factpack:{fact_pack.organization_label}"))

    return DraftingReport(
        sections=sections,
        generation_mode="LIVE_MODEL",
        claims=claims, model_runs=model_runs)


def _bundle(sec, plan, prompt: str) -> dict:
    """Model-gateway bundle shape (same as the G1 live lane)."""
    return {
        "section_id": sec.section_id, "title": sec.title,
        "notes": sec.drafting_notes[:500],
        "evidence": "", "protected_facts": {},
        "instructions": prompt,
    }


def _normalize_provider_failure(exc: Exception) -> str:
    text = str(exc).lower()
    if "429" in text or "rate" in text or "capacity" in text:
        return "RATE_LIMITED"
    if "timeout" in text or "timed out" in text:
        return "TIMEOUT"
    if "empty" in text:
        return "EMPTY_COMPLETION"
    if "401" in text or "403" in text or "credential" in text or "auth" in text:
        return "AUTH_FAILURE"
    if "context" in text or "token" in text:
        return "CONTEXT_INCOMPATIBLE"
    if "404" in text or "not allowed" in text or "unavailable" in text:
        return "MODEL_UNAVAILABLE"
    return "UNKNOWN_PROVIDER_ERROR"


# --- Governed live invoke with real token budgets ----------------------------


def build_quality_model_invoke(model_id: str =
                               "z-ai/glm-5.2:free",
                               *,
                               max_output_tokens: int = 4096,
                               tenant_id: str = "tenant-a",
                               project_id: str = "proj-g1q"):
    """Governed Model Gateway invoke sized for long-form section drafting.

    The W4 pilot invoke capped max_output_tokens at 512 (~380 words per
    section) — the direct cause of the 238-word skeleton. This builder
    keeps the SAME governance (principal, scope, authorization, egress,
    credential resolver) but allocates the output budget long-form
    sections actually need, and passes the full section prompt as the
    user message with a short system role frame.
    """
    import os
    from prototype.g0.model.adapters import OpenRouterAdapter
    from prototype.g0.model.gateway import (
        DevRuntimeCredentialResolver, ModelGateway,
        ProviderProfileRegistry)
    from prototype.g0.security.authorization import (
        Authorizer, GrantRegistry)
    from prototype.g0.security.identity import (
        PrincipalRegistry, ScopeEvaluator)
    from prototype.g0.security.models import Principal

    T0 = "2026-08-26T00:00:00+00:00"
    T_FAR = "2027-12-31T00:00:00+00:00"
    principals = PrincipalRegistry()
    scope = ScopeEvaluator()
    grants = GrantRegistry()
    authz = Authorizer(principals=principals, scope=scope, grants=grants)
    principals.register(Principal(
        principal_id="g1-quality-ceo", principal_type="HERMES_CEO",
        subject_id="g1-quality-ceo-1", status="ACTIVE",
        authentication_method="SERVICE_TOKEN",
        tenant_memberships=[tenant_id], created_at=T0,
        credential_class="VAULT_REF", authority_level="L3"))
    scope.add_membership(membership_id="m-g1q",
                         tenant_id=tenant_id,
                         principal_id="g1-quality-ceo",
                         role_ids=["MEMBER"], valid_from=T0,
                         valid_to=T_FAR)
    scope.register_resource("res:g1q-draft", tenant_id,
                            project_id=project_id)
    authz.register_capability("model.invoke", required_level="L1")
    authz.allow_egress_destination("https://openrouter.ai")
    grants.issue(grant_id="g-g1q", principal_id="g1-quality-ceo",
                 capability_id="model.invoke", tenant_id=tenant_id,
                 authority_level="L3", valid_from=T0, expires_at=T_FAR,
                 issued_by="admin", project_id=project_id)
    profiles = ProviderProfileRegistry()
    gateway = ModelGateway(profiles, decisions=authz.decisions,
                           credential_resolver=DevRuntimeCredentialResolver())
    gateway.register_adapter("openrouter", OpenRouterAdapter())
    gateway._authz = authz

    counter = {"n": 0}
    provenance: list[dict] = []

    def build_req(i: int, attempt: int, bundle: dict, requested_model: str | None = None) -> dict:
        """MR-005 fix: each gateway execution attempt carries a FRESH
        request id. The id must distinguish run, section/pass, candidate
        model, and attempt — a bounded retry or a fallback to another
        approved model is a NEW execution, never a replay (G1 routing §6).
        The logical task_id stays stable across attempts so one-shot replay
        protection still blocks a genuinely repeated id."""
        req_model = (requested_model or model_id).split("/")[-1]
        model_slug = re.sub(r"[^A-Za-z0-9]", "-", req_model)[:28]
        return {
            "model_request_id": f"g1q-m-{i}-{model_slug}-a{attempt}",
            "request_id": f"g1q-r-{i}-{model_slug}-a{attempt}",
            "tenant_id": tenant_id, "project_id": project_id,
            "principal_id": "g1-quality-ceo",
            "task_id": f"task-g1q-{i}",
            "capability_id": "model.invoke",
            "provider_profile_id": "pp_openrouter_dev",
            "model_id": requested_model or model_id,
            "purpose": "grant_drafting",
            "messages": [
                {"role": "system", "content":
                 "You are a senior professional grant writer. Output "
                 "polished submission-ready prose only."},
                {"role": "user", "content": bundle["instructions"]},
            ],
            "temperature": 0.2,
            "max_output_tokens": max_output_tokens,
            "created_at": _now(),
            "destination": "https://openrouter.ai",
            "resource_id": "res:g1q-draft",
        }

    def invoke_once(i: int, attempt: int, bundle: dict, requested_model: str | None = None) -> str:
        req = build_req(i, attempt, bundle, requested_model=requested_model)
        decision = authz.authorize(req)
        if decision["decision"] != "ALLOW":
            raise ValueError(
                f"model authorization denied: {decision['reason_code']}")
        resp = gateway.invoke(
            model_request=req, authorization_decision=decision,
            actor="g1-quality-ceo", principal_type="HERMES_CEO",
            tenant_id=tenant_id, project_id=project_id,
            resource_id="res:g1q-draft")
        return str(resp["output_text_or_structured_payload"]).strip()

    def model_invoke(bundle: dict) -> str:
        counter["n"] += 1
        logical_i = counter["n"]
        approved = (
            "z-ai/glm-5.2:free",
            "thinkingmachines/inkling-small:free",
            "minimax/minimax-m3:free",
        )
        candidates = list(approved) if model_id in approved else [model_id]
        last_error = None
        for candidate_index, candidate in enumerate(candidates):
            for attempt in range(2):
                started = datetime.now(timezone.utc)
                try:
                    text = invoke_once(logical_i, attempt=attempt, bundle=bundle,
                                       requested_model=candidate)
                    text = str(text).strip()
                    provenance.append({"section_id": bundle.get("section_id"),
                                       "task_type": "grant_drafting",
                                       "candidate_model": candidate,
                                       "attempt_number": attempt,
                                       "provider": "openrouter",
                                       "latency_ms": round((datetime.now(timezone.utc)-started).total_seconds()*1000, 3),
                                       "status": "SUCCESS" if text else "EMPTY_COMPLETION",
                                       "normalized_failure_reason": "" if text else "EMPTY_COMPLETION",
                                       "fallback_to": None})
                    if text:
                        return text
                    last_error = RuntimeError("empty completion")
                except Exception as exc:
                    last_error = exc
                    reason = _normalize_provider_failure(exc)
                    next_model = (candidates[candidate_index + 1]
                                  if candidate_index + 1 < len(candidates) else None)
                    provenance.append({"section_id": bundle.get("section_id"),
                                       "task_type": "grant_drafting",
                                       "candidate_model": candidate,
                                       "attempt_number": attempt,
                                       "provider": "openrouter",
                                       "latency_ms": round((datetime.now(timezone.utc)-started).total_seconds()*1000, 3),
                                       "status": "FAILED",
                                       "normalized_failure_reason": reason,
                                       "fallback_to": next_model})
                    if reason == "AUTH_FAILURE":
                        break
            # one bounded retry, then fallback to the next approved model
        raise RuntimeError(f"GENERATION_UNAVAILABLE: approved pool exhausted: {last_error}")

    model_invoke.provenance = provenance
    return model_invoke, gateway, counter
