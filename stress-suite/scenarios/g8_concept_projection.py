"""G8 — cross-machine conceptual projection (revision R3, finding R-G8-01).

The mandated relationships "plural models versus authoritative doctrine",
"evidence contradiction versus operator preference" and "operator preference
versus unknown governance" are CONCEPTUAL relationships. They were never about
comparing one machine's terminal string to another machine's terminal string —
rule N8 forbids that, and the first G8 pass produced five NOT_COMPARABLE results
while still reporting the pairs as covered.

This module implements the honest middle: each participating machine projects its
observable trace onto a SHARED conceptual vocabulary whose five members genuinely
mean the same thing in every machine:

    conceptual_unresolved_representable      an unresolved/ambiguous fact stays representable
    conceptual_plural_not_collapsed          a non-dominated plurality is not collapsed
    conceptual_authority_not_empirical       an authority action does not change the empirical state
    conceptual_provenance_attached           the observation keeps a concrete origin reference
    conceptual_preference_not_empirical      operator preference cannot rewrite the empirical state

Adapters read only declared structural facts of the run's own trace. They never
read an expected outcome, a fixture name or hidden ground truth, and they never
branch on a scenario identifier. When a machine's surface does not exercise a
concept the value is NOT_EXERCISED / NOT_APPLICABLE, which the engine treats as
non-exercising and NEVER as favourable; if no concept is exercised on either side
of a mandatory pair the comparison is an evidence gap that blocks.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Sequence, Tuple

#: conceptual fields, in declared order
CONCEPT_FIELDS = ("conceptual_unresolved_representable",
                  "conceptual_plural_not_collapsed",
                  "conceptual_authority_not_empirical",
                  "conceptual_provenance_attached",
                  "conceptual_preference_not_empirical")

#: values that VIOLATE the concept they belong to
_VIOLATING = frozenset({"VIOLATED", "COLLAPSED", "ABSENT"})

#: values that mean the run surface did not exercise the concept
NON_EXERCISING = frozenset({"NOT_EXERCISED", "NOT_APPLICABLE", "UNKNOWN"})

#: machine-local outcome tokens that themselves represent a HELD / OPEN state.
#: A declared vocabulary, not a scenario predicate.
_HELD_TOKENS = frozenset({
    "WATCH", "UNRESOLVED", "UNRESOLVED_GOVERNANCE_EVENT", "OPERATOR_HOLD",
    "TRANSFORMATION_CANDIDATE", "PLURAL_MODEL_STATE", "REPAIR_LOCAL",
})

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_PLACEHOLDERS = frozenset({"", "UNKNOWN", "NONE", "NULL", "N/A", "NA"})


def _concrete(values: Sequence[Any]) -> Tuple[str, ...]:
    out = set()
    for v in values:
        if isinstance(v, str) and v.strip() and v.strip().upper() not in _PLACEHOLDERS:
            out.add(v.strip())
    return tuple(sorted(out))


@dataclass(frozen=True)
class ConceptualProjection:
    machine: str
    source_ref: str
    values: Dict[str, str]
    outcome_token: str
    evidence_refs: Tuple[str, ...] = ()
    decision_surface: str = ""
    adapter: str = ""
    notes: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {"machine": self.machine, "source_ref": self.source_ref,
                "adapter": self.adapter, "outcome_token": self.outcome_token,
                "values": {k: self.values[k] for k in sorted(self.values)},
                "evidence_refs": list(self.evidence_refs),
                "decision_surface": self.decision_surface,
                "notes": list(self.notes)}


def _outcome_token(values: Mapping[str, str]) -> str:
    """CONCEPTUAL_VIOLATION > UNDER_EXERCISED > PARTIAL_COVERAGE > COHERENT."""
    if any(values.get(f) in _VIOLATING for f in CONCEPT_FIELDS):
        return "CONCEPTUAL_VIOLATION"
    exercised = [f for f in CONCEPT_FIELDS if values.get(f) not in NON_EXERCISING]
    if not exercised:
        return "CONCEPTUAL_UNDER_EXERCISED"
    if len(exercised) < len(CONCEPT_FIELDS):
        return "CONCEPTUAL_PARTIAL_COVERAGE"
    return "CONCEPTUAL_COHERENT"


# --------------------------------------------------------------------------- #
# Adapter: M5_PHASE (the G2 phase machine)
# --------------------------------------------------------------------------- #
def project_m5_phase(trace: Mapping[str, Any], source_ref: str) -> ConceptualProjection:
    terminal_phase = str(trace.get("terminal_phase", ""))
    states = {str(k): str(v)
              for k, v in (trace.get("observed_terminal_states") or {}).items()}
    transitions = [t for t in (trace.get("transitions") or []) if isinstance(t, Mapping)]
    reached = {str(t.get("to", "")) for t in transitions} | {terminal_phase}
    refs = _concrete(list(trace.get("registry_ids") or ()))
    unresolved_refs = sorted(r for r in
                            [t.get("evidence_refs") for t in transitions] if r)

    values: Dict[str, str] = {}
    held = sorted(reached & _HELD_TOKENS)
    values["conceptual_unresolved_representable"] = ("PRESERVED" if held
                                                     else "NOT_EXERCISED")

    if len(states) > 1:
        live = [k for k, v in states.items() if v.upper() in {"ACTIVE", "PLURAL"}]
        values["conceptual_plural_not_collapsed"] = ("PRESERVED" if len(live) > 1
                                                     else "COLLAPSED")
    else:
        values["conceptual_plural_not_collapsed"] = "NOT_APPLICABLE"

    # the phase machine records authority_level but no empirical grade, so it
    # cannot exercise 'authority does not change the empirical state'
    values["conceptual_authority_not_empirical"] = "NOT_EXERCISED"

    resolved = [t.get("evidence_refs_resolved") for t in transitions
                if t.get("evidence_refs")]
    if resolved:
        values["conceptual_provenance_attached"] = ("PRESERVED"
                                                    if all(r is True for r in resolved)
                                                    else "ABSENT")
    elif refs:
        values["conceptual_provenance_attached"] = "PRESERVED"
    else:
        values["conceptual_provenance_attached"] = "NOT_EXERCISED"

    values["conceptual_preference_not_empirical"] = "NOT_EXERCISED"

    return ConceptualProjection(
        machine="M5_PHASE", source_ref=source_ref, values=values,
        outcome_token=_outcome_token(values), evidence_refs=refs,
        decision_surface=("terminal phase + terminal model/knowledge states + "
                          "transition evidence-ref resolution"),
        adapter="project_m5_phase",
        notes=tuple([f"held/open states reached: {held}",
                     f"terminal states: {sorted(states)}"]))


# --------------------------------------------------------------------------- #
# Adapter: DOMAIN_MACHINE (the G5 domain machine)
# --------------------------------------------------------------------------- #
def project_domain_machine(trace: Mapping[str, Any],
                           source_ref: str) -> ConceptualProjection:
    contradictions = [c for c in (trace.get("contradictions") or [])
                      if isinstance(c, Mapping)]
    claims = [c for c in (trace.get("doctrine_claims") or []) if isinstance(c, Mapping)]
    items = [i for i in (trace.get("items") or []) if isinstance(i, Mapping)]
    patterns = [p for p in (trace.get("patterns") or []) if isinstance(p, Mapping)]
    mechanism = trace.get("mechanism") if isinstance(trace.get("mechanism"), Mapping) else {}
    card = mechanism.get("mechanism_card") if isinstance(
        mechanism.get("mechanism_card"), Mapping) else {}
    rewritten = trace.get("manual_claim_rewritten")
    results = [r for r in (trace.get("observed_results") or []) if isinstance(r, Mapping)]

    refs = _concrete([c.get("claim_id") for c in claims]
                     + [p.get("pattern_id") for p in patterns]
                     + [i.get("candidate_id") for i in items])

    values: Dict[str, str] = {}
    open_route = [c for c in contradictions
                  if "CONTRADICTION_OPEN" in str(c.get("route", "")).upper()]
    candidate = [p for p in patterns
                 if "CANDIDATE" in str(p.get("disposition", "")).upper()]
    values["conceptual_unresolved_representable"] = (
        "PRESERVED" if (open_route or candidate) else "NOT_EXERCISED")

    alternatives = [str(a) for a in (card.get("alternative_explanations") or ())]
    preserved_sides = [c for c in contradictions
                       if "PRESERVED" in str(c.get("route", "")).upper()]
    if open_route or alternatives:
        values["conceptual_plural_not_collapsed"] = (
            "PRESERVED" if (preserved_sides or alternatives) else "NOT_EXERCISED")
    else:
        values["conceptual_plural_not_collapsed"] = "NOT_APPLICABLE"

    material_failures = [g for i in items for g in (i.get("gate_vector") or [])
                         if isinstance(g, Mapping) and g.get("passed") is False
                         and g.get("material") is True]
    if rewritten is True:
        values["conceptual_authority_not_empirical"] = "VIOLATED"
    elif rewritten is False or material_failures:
        values["conceptual_authority_not_empirical"] = "PRESERVED"
    else:
        values["conceptual_authority_not_empirical"] = "NOT_EXERCISED"

    digests = _concrete([c.get("source_fingerprint") for c in claims])
    paths = _concrete([c.get("source_path") for c in claims])
    result_refs = _concrete([r for res in results for r in (res.get("source_refs") or [])])
    mech_refs = _concrete(list(card.get("evidence_refs") or ()))
    if digests or paths or result_refs or mech_refs:
        values["conceptual_provenance_attached"] = "PRESERVED"
    elif refs:
        values["conceptual_provenance_attached"] = "PRESERVED"
    else:
        values["conceptual_provenance_attached"] = "NOT_EXERCISED"

    values["conceptual_preference_not_empirical"] = "NOT_EXERCISED"

    return ConceptualProjection(
        machine="DOMAIN_MACHINE", source_ref=source_ref, values=values,
        outcome_token=_outcome_token(values),
        evidence_refs=refs or digests,
        decision_surface=("open contradiction routes + retained alternative "
                          "explanations + manual-claim rewrite flag + doctrine "
                          "source fingerprints/source paths + material gate outcomes"),
        adapter="project_domain_machine",
        notes=tuple([f"open contradictions: {len(open_route)}",
                     f"candidate patterns: {len(candidate)}",
                     f"manual_claim_rewritten: {rewritten}"]))


# --------------------------------------------------------------------------- #
# Adapter: AUTHORITY (the G6 governance machine)
# --------------------------------------------------------------------------- #
def project_authority(trace: Mapping[str, Any], source_ref: str) -> ConceptualProjection:
    phases = [p for p in (trace.get("phases") or []) if isinstance(p, Mapping)]
    names = [str(p.get("phase", "")) for p in phases]
    evidence = dict((trace.get("canonical_state") or {}).get("before", {})
                    .get("evidence_grades") or {})
    events = _concrete([str((p.get("detail") or {}).get("event_id", "")) for p in phases])
    preserved_payload_refs = _concrete(
        [r for p in phases
         for r in ((p.get("detail") or {}).get("preserved") or {}).get("evidence_refs") or ()])

    values: Dict[str, str] = {}
    held = sorted({n for n in names if n in _HELD_TOKENS})
    values["conceptual_unresolved_representable"] = ("PRESERVED" if held
                                                     else "NOT_EXERCISED")
    values["conceptual_plural_not_collapsed"] = "NOT_APPLICABLE"

    steps = [p for p in phases
             if "DIRECTIVE" in str(p.get("phase")) or "AUTHORITY" in str(p.get("phase"))]
    graded = [s for s in steps
              if (s.get("detail") or {}).get("evidence_grade_before") is not None]
    if graded:
        changed = [s for s in graded
                   if (s.get("detail") or {}).get("evidence_grade_unchanged") is False
                   or (s.get("detail") or {}).get("evidence_grade_before")
                   != (s.get("detail") or {}).get("evidence_grade_after")]
        values["conceptual_authority_not_empirical"] = ("VIOLATED" if changed
                                                        else "PRESERVED")
    else:
        values["conceptual_authority_not_empirical"] = "NOT_EXERCISED"

    if evidence or preserved_payload_refs:
        values["conceptual_provenance_attached"] = "PRESERVED"
    else:
        values["conceptual_provenance_attached"] = "NOT_EXERCISED"

    # an operator-preference surface is exercised when the run executes a
    # directive; the concept is that such a directive cannot rewrite the
    # empirical state, so it is VIOLATED exactly when a graded directive changed it
    directives = [p for p in phases if str(p.get("phase", "")).startswith("DIRECTIVE")]
    if directives:
        values["conceptual_preference_not_empirical"] = (
            "VIOLATED" if values["conceptual_authority_not_empirical"] == "VIOLATED"
            else "PRESERVED" if values["conceptual_authority_not_empirical"] == "PRESERVED"
            else "NOT_EXERCISED")
    else:
        values["conceptual_preference_not_empirical"] = "NOT_EXERCISED"

    return ConceptualProjection(
        machine="AUTHORITY", source_ref=source_ref, values=values,
        outcome_token=_outcome_token(values), evidence_refs=events or preserved_payload_refs,
        decision_surface=("governance phase vocabulary + graded directive steps "
                          "+ canonical evidence-grade projection + retained event payload"),
        adapter="project_authority",
        notes=tuple([f"held phases: {held}", f"graded directive steps: {len(graded)}"]))


ADAPTERS = {"M5_PHASE": project_m5_phase,
            "DOMAIN_MACHINE": project_domain_machine,
            "AUTHORITY": project_authority}


def project(machine: str, trace: Mapping[str, Any],
            source_ref: str) -> ConceptualProjection:
    """Project one machine-local trace onto the shared conceptual vocabulary.

    Only declared structural facts of the trace are read: no expected outcome, no
    fixture name, no hidden ground truth, and no scenario identifier reaches any
    adapter.
    """
    from engine.g8_contradiction import SEALED_KEYS
    leaked = SEALED_KEYS & set(trace)
    if leaked:
        raise ValueError(
            f"conceptual projection refuses a trace carrying sealed truth: "
            f"{sorted(leaked)}")
    return ADAPTERS[machine](trace, source_ref)
