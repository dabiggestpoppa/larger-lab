"""G8 — guarded-property derivations (revision R3, STRESS-G8R2).

Every guarded property is derived here from an OBSERVABLE surface that the run
actually exposes. Each derivation returns a `GuardedPropertyValue` carrying the
evidence contract the engine validates:

    value · derivation_kind · evidence_refs · before_state · after_state ·
    decision_surface · reason

Nothing in this module searches prose, matches a key name, branches on a scenario
identifier or returns an unconditional literal. Where the surface does not expose
the relation, the derivation returns `not_derivable(...)` — which the engine
reports as UNKNOWN_NOT_FAVORABLE, never as a pass (review findings R-G8-02 through
R-G8-06).

Review mapping:

  R-G8-02  P5 no longer ends in `... or True`; a validated profit-bearing item
           with no exercised (or with a materially failed) gate surface is a
           VIOLATION, not a pass.
  R-G8-03  P7 requires a CONCRETE retained provenance reference to a declared
           retention surface; a key name or the literal 'UNKNOWN' is not evidence.
  R-G8-04  P11 requires a real paired baseline/runtime-replacement execution with
           two fingerprints; a scenario identifier proves nothing.
  R-G8-05  P1/P8/P9 compare canonical before/after state. Observing a refusal
           somewhere does not establish P1; a literal True cannot establish P8;
           recognising AVAILABLE/UNAVAILABLE cannot establish P9.
  R-G8-06  P6 inspects the ACTUAL resulting disposition, so a count-driven
           transformation is a VIOLATION.
"""
from __future__ import annotations

import json
import re
from typing import Any, Iterable, Mapping, Sequence, Tuple

from engine.g8_contradiction import GuardedPropertyValue, not_derivable

# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
#: values that are not a reference. A field whose VALUE is one of these carries no
#: provenance, however promising its KEY NAME looks (review finding R-G8-03).
_PLACEHOLDERS = frozenset({"", "UNKNOWN", "NONE", "NULL", "N/A", "NA", "TBD",
                           "NOT_SET", "UNDEFINED"})
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_REF_LIKE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:/#-]{0,127}$")

#: performance values that make a candidate "profit-bearing" for P5
_HIGH_ECONOMIC_VALUE = frozenset({"EXTREME", "HIGH", "VERY_HIGH"})
_PROFIT_KEYS = ("profit", "pnl", "cumulative_return", "sharpe", "expected_return",
                "net_return")

#: dispositions that mean the validation state was SATISFIED
_VALIDATED_TOKENS = frozenset({"VALIDATED", "VALIDATION_PASSED", "ACCEPTED",
                               "ADMITTED", "PROMOTED", "APPROVED"})

#: dispositions that mean raw count WAS promoted into independence/transformation
_COUNT_PROMOTED_TOKENS = frozenset({
    "INDEPENDENTLY_SUPPORTED", "INDEPENDENT_SUPPORT", "TRANSFORMATION_ADMITTED",
    "NEW_STABLE_ESTABLISHED", "ONTOLOGY_EXPLORATION_CANDIDATE",
    "PLURAL_MODEL_STATE",
})

#: centrality levels P12 must exercise
_CENTRALITY_LEVELS = ("LEAF", "MID", "CORE")


def _ref(value: Any) -> str:
    """Return the concrete reference a value IS, or '' when it is not one."""
    if isinstance(value, str):
        s = value.strip()
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    else:
        return ""
    return "" if s.upper() in _PLACEHOLDERS else (s if _REF_LIKE.match(s) else "")


def concrete_references(values: Iterable[Any]) -> Tuple[str, ...]:
    """The concrete references among `values` — never a key name, never a
    placeholder. Order-independent by construction."""
    out = {_ref(v) for v in values}
    out.discard("")
    return tuple(sorted(out))


def _stable(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))


# --------------------------------------------------------------------------- #
# P1 — no authority escalation
# --------------------------------------------------------------------------- #
def p1_authority_not_escalated(surface: Mapping[str, Any]) -> GuardedPropertyValue:
    """P1: an actor's authority may rise only through a governed path.

    Derived by CANONICAL_STATE_COMPARISON over the run's canonical authority
    projection plus its declared authority-event accounting. An escalation that
    was applied without a governed authorization basis is a VIOLATION even when
    the same trace contains refusals — observing a refusal somewhere does not
    prove that authority never escalated (review finding R-G8-05).
    """
    events = dict(surface.get("authority_events") or {})
    before = surface.get("authority_before")
    after = surface.get("authority_after")
    applied = list(surface.get("applied_escalations") or [])
    if not events and before is None and after is None:
        return not_derivable(
            "P1: the run surface exposes no authority projection and no authority "
            "event accounting, so no authority escalation can be observed")

    escalations = int(events.get("ratifications", 0) or 0) \
        + int(events.get("registry_issues", 0) or 0)
    governed = concrete_references(surface.get("governed_basis") or ())
    ungoverned = [e for e in applied
                  if isinstance(e, Mapping)
                  and e.get("authorized_by_governed_basis") is False]
    changed = before is not None and after is not None and _stable(before) != _stable(after)
    refs = tuple(sorted(
        set(governed)
        | {str(e.get("event", "")) for e in applied
           if isinstance(e, Mapping) and e.get("event")}
        | {str(a) for a in (before or {}) if str(a)}
        | {str(a) for a in (after or {}) if str(a)}))
    if not refs:
        return not_derivable(
            "P1: the authority surface cites no concrete actor, grant or event "
            "reference, so nothing about the escalation can be adjudicated")
    reason_bits = [f"authority projection changed={changed}",
                   f"applied escalations={escalations}",
                   f"governed authorization bases={len(governed)}",
                   f"explicitly ungoverned escalations={len(ungoverned)}"]
    if ungoverned:
        return GuardedPropertyValue(
            value=False, derivation_kind="CANONICAL_STATE_COMPARISON",
            evidence_refs=refs, before_state=_stable(before),
            after_state=_stable(after),
            decision_surface="authority_before/authority_after + authority_events + applied_escalations",
            reason="P1 VIOLATED: " + "; ".join(reason_bits)
                   + " — an authority escalation was applied without a governed "
                     "authorization basis")
    if escalations > 0 and not governed:
        return GuardedPropertyValue(
            value=False, derivation_kind="CANONICAL_STATE_COMPARISON",
            evidence_refs=refs, before_state=_stable(before),
            after_state=_stable(after),
            decision_surface="authority_before/authority_after + authority_events + governed_basis",
            reason="P1 VIOLATED: " + "; ".join(reason_bits)
                   + " — authority-mutating events were applied with no declared "
                     "governed authorization basis")
    return GuardedPropertyValue(
        value=True, derivation_kind="CANONICAL_STATE_COMPARISON",
        evidence_refs=refs, before_state=_stable(before), after_state=_stable(after),
        decision_surface="authority_before/authority_after + authority_events + governed_basis",
        reason="P1 HOLDS: " + "; ".join(reason_bits))


# --------------------------------------------------------------------------- #
# P2 — an authority action never fabricates empirical evidence status
# --------------------------------------------------------------------------- #
def p2_evidence_status_not_fabricated(surface: Mapping[str, Any]) -> GuardedPropertyValue:
    """P2, derived ONLY where the run reports an evidence grade before AND after
    an authority/directive step. A grade field merely being present is not a
    grade change."""
    steps = list(surface.get("authority_steps") or [])
    if not steps:
        return not_derivable(
            "P2: the run executes no authority/directive step, so no authority "
            "action can be observed touching an empirical grade")
    checked = 0
    refs = set()
    for step in steps:
        if not isinstance(step, Mapping):
            continue
        for key in ("directive_id", "evidence_id", "grant_id", "phase"):
            if _ref(step.get(key)):
                refs.add(str(step[key]))
                break
    if not refs:
        return not_derivable(
            "P2: the authority steps cite no concrete directive, evidence or grant "
            "reference, so the empirical-grade relation cannot be adjudicated")
    for step in steps:
        if not isinstance(step, Mapping):
            continue
        if step.get("evidence_grade_unchanged") is False:
            return GuardedPropertyValue(
                value=False, derivation_kind="DIRECT_TRACE",
                evidence_refs=tuple(sorted(refs)),
                before_state=str(step.get("evidence_grade_before", "")),
                after_state=str(step.get("evidence_grade_after", "")),
                decision_surface="authority/directive step details: evidence_grade_before/_after/_unchanged",
                reason="P2 VIOLATED: an authority step reports the empirical "
                       "evidence grade CHANGED")
        if step.get("evidence_grade_before") is not None \
                and step.get("evidence_grade_after") is not None:
            checked += 1
            if step["evidence_grade_before"] != step["evidence_grade_after"]:
                return GuardedPropertyValue(
                    value=False, derivation_kind="DIRECT_TRACE",
                    evidence_refs=tuple(sorted(refs)),
                    before_state=str(step["evidence_grade_before"]),
                    after_state=str(step["evidence_grade_after"]),
                    decision_surface="authority/directive step details: evidence_grade_before/_after",
                    reason="P2 VIOLATED: an authority step changed the empirical "
                           "evidence grade")
    if not checked:
        return not_derivable(
            "P2: authority steps executed but none reports the empirical grade "
            "before and after, so the relation is not observable")
    return GuardedPropertyValue(
        value=True, derivation_kind="DIRECT_TRACE",
        evidence_refs=tuple(sorted(refs)),
        before_state="grade before each authority step", after_state="same grade after each authority step",
        decision_surface="authority/directive step details: evidence_grade_before/_after/_unchanged",
        reason=f"P2 HOLDS: {checked} authority step(s) report an unchanged "
               "empirical evidence grade")


# --------------------------------------------------------------------------- #
# P3 — no forced classification
# --------------------------------------------------------------------------- #
def p3_no_forced_classification(surface: Mapping[str, Any]) -> GuardedPropertyValue:
    """P3: an unclassifiable fact stays representable. Derived from the run's own
    classification failures and the channels it nevertheless assigned."""
    failures = list(surface.get("classification_failures") or [])
    unresolved = list(surface.get("unresolved_events") or [])
    forced = list(surface.get("forced_channels") or [])
    if not failures and not unresolved:
        return not_derivable(
            "P3: the run emits no unclassifiable/unresolved governance event, so "
            "forced classification cannot be observed")
    refs = concrete_references(surface.get("event_ids") or ())
    if not refs:
        return not_derivable(
            "P3: the unclassifiable events carry no concrete identifier, so forced "
            "classification cannot be adjudicated")
    before = f"unresolved facts presented={len(unresolved)}"
    after = f"classification failures recorded={len(failures)}; forced channels={len(forced)}"
    if forced:
        return GuardedPropertyValue(
            value=False, derivation_kind="DIRECT_TRACE", evidence_refs=refs,
            before_state=before, after_state=after,
            decision_surface="governance event classification failures + assigned channels",
            reason="P3 VIOLATED: an unclassifiable fact was forced into a "
                   f"declared channel {sorted(forced)}")
    return GuardedPropertyValue(
        value=True, derivation_kind="DIRECT_TRACE", evidence_refs=refs,
        before_state=before, after_state=after,
        decision_surface="governance event classification failures + assigned channels",
        reason="P3 HOLDS: every unclassifiable fact remained representable and "
               "none was forced into a declared channel")


# --------------------------------------------------------------------------- #
# P4 — no plural collapse
# --------------------------------------------------------------------------- #
def p4_no_plural_collapse(surface: Mapping[str, Any]) -> GuardedPropertyValue:
    """P4: where a run terminates holding more than one live model/knowledge
    state, none may be collapsed into a single winner."""
    states = dict(surface.get("observed_terminal_states") or {})
    if not states:
        return not_derivable(
            "P4: the run reports no terminal model/knowledge state set, so a "
            "plural state cannot be observed")
    live = sorted(k for k, v in states.items()
                  if str(v).upper() in {"ACTIVE", "PLURAL", "RETAINED", "HELD"})
    refs = tuple(sorted(states))
    before = f"states presented={sorted(states)}"
    after = f"live states retained={live}"
    if surface.get("forced_single_winner") is True and len(live) > 1:
        return GuardedPropertyValue(
            value=False, derivation_kind="CANONICAL_STATE_COMPARISON",
            evidence_refs=refs, before_state=before, after_state=after,
            decision_surface="terminal model/knowledge state projection + declared single-winner assertion",
            reason="P4 VIOLATED: the run asserts a single winner while more than one "
                   "non-dominated state is still live")
    if len(live) > 1:
        return GuardedPropertyValue(
            value=True, derivation_kind="CANONICAL_STATE_COMPARISON",
            evidence_refs=refs, before_state=before, after_state=after,
            decision_surface="terminal model/knowledge state projection",
            reason=(f"P4 HOLDS: {len(live)} non-dominated states are still live at "
                    "termination; no single winner was forced"))
    return not_derivable(
        "P4: fewer than two non-dominated states are live at termination, so this "
        "run does not present a plurality that could be collapsed — recorded as an "
        "evidence gap, never as a pass. Whether a plurality was presented and then "
        "resolved is not observable on this surface.")


# --------------------------------------------------------------------------- #
# P5 — profit / novelty / volume never weakens validation
# --------------------------------------------------------------------------- #
def _profit_bearing(item: Mapping[str, Any], artifacts_profit: bool) -> bool:
    perf = item.get("performance") if isinstance(item.get("performance"), Mapping) else {}
    if str(perf.get("economic_value_class", "")).upper() in _HIGH_ECONOMIC_VALUE:
        return True
    for key in _PROFIT_KEYS:
        val = item.get(key, perf.get(key))
        if isinstance(val, (int, float)) and not isinstance(val, bool) and val > 0:
            return True
    return artifacts_profit


def p5_profit_did_not_weaken_validation(surface: Mapping[str, Any]) -> GuardedPropertyValue:
    """P5: profit, novelty or candidate volume never weakens a validation
    requirement.

    A validated profit-bearing claim whose material gate surface FAILED, or which
    exposes no gate surface at all, is a VIOLATION. Previously this returned True
    through a `... or True` tautology for exactly that construction (review
    finding R-G8-02).
    """
    items = [i for i in (surface.get("items") or []) if isinstance(i, Mapping)]
    if not items:
        return not_derivable(
            "P5: the run exposes no candidate item surface, so the relation "
            "between profit and the validation state is not observable")
    artifacts_profit = any(
        isinstance(surface.get(k), (int, float)) and not isinstance(surface.get(k), bool)
        and surface.get(k) > 0 for k in _PROFIT_KEYS)
    profit_items = [i for i in items if _profit_bearing(i, artifacts_profit)]
    if not profit_items:
        return not_derivable(
            "P5: no candidate carries a declared profit/novelty magnitude, so "
            "profit cannot be shown to have weakened validation or not")

    refs = tuple(sorted(concrete_references(
        [i.get("candidate_id") for i in profit_items])))
    if not refs:
        return not_derivable(
            "P5: the profit-bearing candidates carry no concrete candidate "
            "reference, so the validation state they reached cannot be adjudicated")
    observed = 0
    for item in profit_items:
        gates = [g for g in (item.get("gate_vector") or []) if isinstance(g, Mapping)]
        disposition = str(item.get("disposition", "") or item.get("outcome", "")).upper()
        validated = any(disposition.startswith(t) for t in _VALIDATED_TOKENS)
        material_failures = [g.get("gate_id") for g in gates
                            if g.get("passed") is False and g.get("material") is True]
        if not validated and gates:
            observed += 1
            continue
        if validated and (not gates or material_failures):
            return GuardedPropertyValue(
                value=False, derivation_kind="DIRECT_TRACE",
                evidence_refs=refs,
                before_state=f"profit-bearing claim disposition={disposition or 'UNSET'}",
                after_state=("material gate failures="
                             f"{material_failures or 'NO_GATE_SURFACE_EVALUATED'}"),
                decision_surface="candidate item gate_vector + disposition",
                reason="P5 VIOLATED: a profit-bearing claim reached a VALIDATED "
                       "disposition although its required validation state was "
                       "weakened (material gate failed, or no gate surface was "
                       "evaluated at all)")
    if not observed:
        return not_derivable(
            "P5: every profit-bearing candidate was validated on an exercised "
            "gate surface, so 'profit did not weaken validation' is not what this "
            "run demonstrates")
    return GuardedPropertyValue(
        value=True, derivation_kind="DIRECT_TRACE", evidence_refs=refs,
        before_state="profit-bearing candidate with an exercised gate surface",
        after_state="no material gate failure was waived",
        decision_surface="candidate item gate_vector + disposition",
        reason=f"P5 HOLDS: {observed} profit-bearing candidate(s) were held to "
               "their material gate surface and none was validated through it")


# --------------------------------------------------------------------------- #
# P6 — raw count never creates transformation
# --------------------------------------------------------------------------- #
def p6_count_did_not_create_transformation(surface: Mapping[str, Any]) -> GuardedPropertyValue:
    """P6: derived from the ACTUAL resulting disposition, not from the count
    conditions alone (review finding R-G8-06)."""
    facts = surface.get("facts") if isinstance(surface.get("facts"), Mapping) else {}
    raw = surface.get("raw_reviewer_count", facts.get("raw_reviewer_count"))
    lineages = surface.get("distinct_source_lineages",
                           facts.get("distinct_source_lineages"))
    disposition = str(surface.get("disposition", "")).upper()
    if raw is None or lineages is None or not disposition:
        return not_derivable(
            "P6: the run surface does not expose both the raw count, its distinct "
            "lineage count and the resulting disposition")
    try:
        raw_n, lineage_n = int(raw), int(lineages)
    except (TypeError, ValueError):
        return not_derivable("P6: raw count or lineage count is not an integer")
    if raw_n <= 1 or lineage_n > 1:
        return not_derivable(
            f"P6: this run does not exercise the relation (raw count={raw_n}, "
            f"distinct source lineages={lineage_n}); the count is not being used "
            "over a single lineage")
    refs = concrete_references([surface.get("claim_id"),
                               surface.get("disposition_rule"),
                               surface.get("policy_id")])
    if not refs:
        return not_derivable(
            "P6: the run cites no concrete claim or policy reference for the "
            "resulting disposition, so the count->transformation relation cannot be "
            "adjudicated")
    before_state = f"raw count={raw_n} over {lineage_n} distinct source lineage(s)"
    after_state = f"resulting disposition={disposition}"
    if any(disposition.startswith(t) for t in _COUNT_PROMOTED_TOKENS):
        return GuardedPropertyValue(
            value=False, derivation_kind="DIRECT_TRACE", evidence_refs=refs,
            before_state=before_state, after_state=after_state,
            decision_surface="raw reviewer count + distinct source lineages + resulting disposition",
            reason="P6 VIOLATED: a raw count over a single source lineage produced "
                   f"an independence/transformation disposition ({disposition})")
    return GuardedPropertyValue(
        value=True, derivation_kind="DIRECT_TRACE", evidence_refs=refs,
        before_state=before_state, after_state=after_state,
        decision_surface="raw reviewer count + distinct source lineages + resulting disposition",
        reason=f"P6 HOLDS: {raw_n} raw reviewers over one source lineage produced "
               f"the non-transformation disposition {disposition}")


# --------------------------------------------------------------------------- #
# P7 — provenance preserved
# --------------------------------------------------------------------------- #
def p7_provenance_preserved(surface: Mapping[str, Any]) -> GuardedPropertyValue:
    """P7: what the run ATTACHES must resolve to a concrete retained reference.

    A field named `evidence_provenance` whose value is the string 'UNKNOWN', or a
    key name with no record behind it, is NOT provenance evidence (review finding
    R-G8-03)."""
    attached = concrete_references(surface.get("attached_references") or ())
    retained = set(concrete_references(surface.get("retained_references") or ()))
    if attached and not retained:
        return not_derivable(
            "P7: the run exposes no independent retention surface, so whether the "
            "attached references were retained cannot be established")
    if not attached:
        return not_derivable(
            "P7: the run attaches no CONCRETE provenance/lineage reference (only "
            "key names, empty values or placeholders such as 'UNKNOWN'), so the "
            "retention of provenance cannot be established")
    detached = sorted(r for r in attached if r not in retained)
    before_state = f"attached references={list(attached)}"
    after_state = f"retained references={sorted(retained)}"
    if detached:
        return GuardedPropertyValue(
            value=False, derivation_kind="CANONICAL_STATE_COMPARISON",
            evidence_refs=attached, before_state=before_state, after_state=after_state,
            decision_surface="attached provenance/lineage references vs the run's retention surface",
            reason=f"P7 VIOLATED: attached provenance references {detached} are "
                   "absent from the run's retention surface")
    return GuardedPropertyValue(
        value=True, derivation_kind="CANONICAL_STATE_COMPARISON",
        evidence_refs=attached, before_state=before_state, after_state=after_state,
        decision_surface="attached provenance/lineage references vs the run's retention surface",
        reason=f"P7 HOLDS: all {len(attached)} attached concrete reference(s) are "
               "still retained after the run")


# --------------------------------------------------------------------------- #
# P8 — capability is not authority
# --------------------------------------------------------------------------- #
def p8_capability_not_authority(surface: Mapping[str, Any]) -> GuardedPropertyValue:
    """P8: a capability/confidence change does not change the authority map.

    Derived by PAIRED_COUNTERFACTUAL over the capability before/after and the
    canonical authority before/after. A literal `True` cannot certify this
    (review finding R-G8-05)."""
    changes = [c for c in (surface.get("capability_changes") or [])
               if isinstance(c, Mapping)]
    moved = [c for c in changes
             if str(c.get("reliability_before")) != str(c.get("reliability_after"))]
    if not moved:
        return not_derivable(
            "P8: no capability/confidence entry actually changed in this run, so "
            "the capability->authority relation is not exercised")
    before = surface.get("authority_before")
    after = surface.get("authority_after")
    if before is None or after is None:
        return not_derivable(
            "P8: capability changed but the run exposes no canonical authority "
            "projection to compare against")
    refs = concrete_references([c.get("worker_id") for c in moved])
    if not refs:
        return not_derivable(
            "P8: the capability changes cite no concrete worker reference, so the "
            "capability->authority relation cannot be adjudicated")
    basis = " ".join(str(t) for t in (surface.get("escalation_basis_texts") or ())).lower()
    authority_changed = _stable(before) != _stable(after)
    before_state = f"authority={_stable(before)}; capability={_stable(changes)}"
    after_state = f"authority={_stable(after)}"
    if authority_changed:
        return GuardedPropertyValue(
            value=False, derivation_kind="PAIRED_COUNTERFACTUAL", evidence_refs=refs,
            before_state=before_state, after_state=after_state,
            decision_surface="capability entry reliability before/after vs canonical authority before/after",
            reason="P8 VIOLATED: capability/confidence changed and the canonical "
                   "authority map moved with it"
                   + (" (an applied escalation cites capability as its basis)"
                      if "capability" in basis else ""))
    return GuardedPropertyValue(
        value=True, derivation_kind="PAIRED_COUNTERFACTUAL", evidence_refs=refs,
        before_state=before_state, after_state=after_state,
        decision_surface="capability entry reliability before/after vs canonical authority before/after",
        reason=f"P8 HOLDS: {len(moved)} capability change(s) left the canonical "
               "authority map unchanged")


# --------------------------------------------------------------------------- #
# P9 — operator availability is not empirical truth
# --------------------------------------------------------------------------- #
def p9_operator_availability_not_empirical(
        surface: Mapping[str, Any]) -> GuardedPropertyValue:
    """P9: availability changes what may execute, never the empirical evidence
    state.

    Derived by PAIRED_COUNTERFACTUAL: the surface must show the availability
    perturbation actually MOVING the action dimension and the empirical
    projection standing still. Recognising the token AVAILABLE/UNAVAILABLE is not
    a derivation (review finding R-G8-05)."""
    pair = surface.get("availability_pair")
    if not isinstance(pair, Mapping):
        return not_derivable(
            "P9: the run exposes no operator-availability perturbation pair, so "
            "the availability->empirical relation is not exercised")
    available = pair.get("available") if isinstance(pair.get("available"), Mapping) else {}
    unavailable = pair.get("unavailable") if isinstance(pair.get("unavailable"), Mapping) else {}
    if not available or not unavailable:
        return not_derivable(
            "P9: the availability perturbation pair is incomplete (a baseline or "
            "a perturbed run is missing)")
    action_before = str(available.get("action_verdict", ""))
    action_after = str(unavailable.get("action_verdict", ""))
    emp_before = _stable(available.get("evidence_projection"))
    emp_after = _stable(unavailable.get("evidence_projection"))
    refs = concrete_references(list(available.get("evidence_refs") or ())
                               + list(unavailable.get("evidence_refs") or ()))
    if not refs:
        return not_derivable(
            "P9: the availability pair exposes no concrete evidence reference on "
            "either side, so the empirical state it compares is empty")
    if action_before == action_after:
        return not_derivable(
            "P9: the availability perturbation did not change what the run could "
            "execute, so the relation is not exercised")
    before_state = f"operator AVAILABLE -> action={action_before}; empirical={emp_before}"
    after_state = f"operator UNAVAILABLE -> action={action_after}; empirical={emp_after}"
    if emp_before != emp_after:
        return GuardedPropertyValue(
            value=False, derivation_kind="PAIRED_COUNTERFACTUAL", evidence_refs=refs,
            before_state=before_state, after_state=after_state,
            decision_surface="availability perturbation pair: action verdict vs empirical evidence projection",
            reason="P9 VIOLATED: the operator-availability perturbation changed "
                   "the empirical evidence state")
    return GuardedPropertyValue(
        value=True, derivation_kind="PAIRED_COUNTERFACTUAL", evidence_refs=refs,
        before_state=before_state, after_state=after_state,
        decision_surface="availability perturbation pair: action verdict vs empirical evidence projection",
        reason="P9 HOLDS: the availability perturbation changed what could "
               "execute and left the empirical evidence projection unchanged")


# --------------------------------------------------------------------------- #
# P10 — unobserved is not clean
# --------------------------------------------------------------------------- #
def p10_unobserved_not_clean(surface: Mapping[str, Any]) -> GuardedPropertyValue:
    """P10: a claim held back for missing observation must not read as clean.

    Derived from the run's own blocked/hold records and from whether it resorted to
    synthetic backfill for them — an absent observation must never be repaired into
    a favourable result."""
    blocked = [c for c in (surface.get("blocked_claims") or []) if isinstance(c, Mapping)]
    if not blocked:
        return not_derivable(
            "P10: the run holds back no claim for missing observation, so the "
            "relation is not exercised")
    refs = concrete_references([c.get("claim_ref", c.get("claim_id")) for c in blocked])
    if not refs:
        return not_derivable(
            "P10: the held-back claims cite no concrete claim reference, so the "
            "unobserved-is-not-clean relation cannot be adjudicated")
    held = [c for c in blocked
            if str(c.get("data_availability", "")).upper() == "UNAVAILABLE"
            or c.get("adequate_history") is False
            or str(c.get("adequacy", {}).get("status", "")).upper()
            in {"INADEQUATE", "UNAVAILABLE"}]
    clean = [str(c.get("disposition", c.get("status", ""))) for c in blocked
             if str(c.get("disposition", c.get("status", ""))).upper().startswith(
                 ("VALIDATED", "CLEAN", "VERIFIED", "ACCEPTED"))]
    before_state = f"claims held back for missing observation={len(blocked)}"
    after_state = (f"held-for-observation={len(held)}; dispositions={clean}; "
                   f"synthetic_backfill_used={surface.get('synthetic_backfill_used')}")
    if clean or surface.get("synthetic_backfill_used") is True:
        return GuardedPropertyValue(
            value=False, derivation_kind="DIRECT_TRACE", evidence_refs=refs,
            before_state=before_state, after_state=after_state,
            decision_surface="claims blocked for missing observation + disposition/backfill flags",
            reason=("P10 VIOLATED: an unobserved claim was repaired or read as clean "
                    f"(dispositions={clean}, synthetic_backfill_used="
                    f"{surface.get('synthetic_backfill_used')})"))
    if not held:
        return not_derivable(
            "P10: no held-back claim is actually held for a MISSING observation, so "
            "the relation is not exercised")
    return GuardedPropertyValue(
        value=True, derivation_kind="DIRECT_TRACE", evidence_refs=refs,
        before_state=before_state, after_state=after_state,
        decision_surface="claims blocked for missing observation + disposition/backfill flags",
        reason=(f"P10 HOLDS: {len(held)} claim(s) held for missing observation stay "
                "blocked and none was backfilled into a clean result"))


# --------------------------------------------------------------------------- #
# P11 — runtime identity is not semantics
# --------------------------------------------------------------------------- #
def p11_runtime_identity_not_semantic(surface: Mapping[str, Any]) -> GuardedPropertyValue:
    """P11: runtime/agent renaming cannot change substantive constitutional
    behaviour.

    Requires an actual PAIRED baseline / runtime-replacement execution with two
    fingerprints. Inferring this from a scenario identifier is exactly what the
    review removed (review finding R-G8-04)."""
    pairs = [p for p in (surface.get("runtime_pairs") or []) if isinstance(p, Mapping)]
    usable = [p for p in pairs
              if p.get("baseline_runtime") != p.get("replacement_runtime")
              and _ref(p.get("baseline_fingerprint"))
              and _ref(p.get("replacement_fingerprint"))]
    if not usable:
        return not_derivable(
            "P11: no paired baseline / runtime-replacement execution carrying two "
            "fingerprints is available, so runtime neutrality cannot be "
            "established — declaring it from a scenario identifier proves nothing")
    refs = concrete_references([p.get("artifact_id") for p in usable]) or \
        tuple(sorted(str(p.get("baseline_fingerprint"))[:12] for p in usable))
    mismatch = [p for p in usable if p.get("semantic_fingerprint_equal") is False]
    before_state = "baseline fingerprints=" + _stable(
        sorted(str(p.get("baseline_fingerprint")) for p in usable))
    after_state = "replacement fingerprints=" + _stable(
        sorted(str(p.get("replacement_fingerprint")) for p in usable))
    if mismatch:
        return GuardedPropertyValue(
            value=False, derivation_kind="PAIRED_COUNTERFACTUAL", evidence_refs=refs,
            before_state=before_state, after_state=after_state,
            decision_surface="paired runtime replacement artifacts + their canonical fingerprints",
            reason="P11 VIOLATED: a runtime identity change altered the "
                   "substantive canonical behaviour")
    return GuardedPropertyValue(
        value=True, derivation_kind="PAIRED_COUNTERFACTUAL", evidence_refs=refs,
        before_state=before_state, after_state=after_state,
        decision_surface="paired runtime replacement artifacts + their canonical fingerprints",
        reason=f"P11 HOLDS: {len(usable)} runtime-rename pair(s) preserve the "
               "canonical semantic fingerprint")


# --------------------------------------------------------------------------- #
# P12 — no permanent incumbent immunity
# --------------------------------------------------------------------------- #
def p12_no_permanent_incumbent_immunity(surface: Mapping[str, Any]) -> GuardedPropertyValue:
    """P12: centrality raises review rigor and never creates immunity. Derived by
    exercising the canonical adjudicator at every centrality level with a strong,
    persistent, independent contradiction."""
    verdicts = surface.get("centrality_verdicts")
    if not isinstance(verdicts, Mapping) or not verdicts:
        return not_derivable(
            "P12: no centrality/contradiction adjudication surface was exercised")
    missing = [c for c in _CENTRALITY_LEVELS if c not in verdicts]
    refs = concrete_references(surface.get("rule_refs") or ())
    if not refs:
        return not_derivable(
            "P12: the centrality adjudication cites no concrete policy/rule "
            "reference, so the immunity relation cannot be adjudicated")
    before_state = f"centrality levels exercised={sorted(verdicts)}"
    after_state = _stable({k: verdicts[k] for k in sorted(verdicts)})
    if missing:
        return not_derivable(
            f"P12: the exercised centrality ladder is incomplete (missing "
            f"{missing}), so immunity across the ladder cannot be established")
    immune = [c for c in _CENTRALITY_LEVELS if verdicts.get(c) != "REVIEW_OPENED"]
    if immune:
        return GuardedPropertyValue(
            value=False, derivation_kind="DIRECT_TRACE", evidence_refs=refs,
            before_state=before_state, after_state=after_state,
            decision_surface="canonical adjudicator verdict at LEAF/MID/CORE with a strong persistent independent contradiction",
            reason=f"P12 VIOLATED: centrality level(s) {immune} retained the "
                   "incumbent against a strong persistent independent "
                   "contradiction — permanent immunity")
    return GuardedPropertyValue(
        value=True, derivation_kind="DIRECT_TRACE", evidence_refs=refs,
        before_state=before_state, after_state=after_state,
        decision_surface="canonical adjudicator verdict at LEAF/MID/CORE with a strong persistent independent contradiction",
        reason="P12 HOLDS: review opens at LEAF, MID and CORE alike for a strong "
               "persistent independent contradiction; centrality raises rigor only")


#: the property-id -> derivation map the observation builders use
DERIVATIONS = {
    "P1": p1_authority_not_escalated,
    "P2": p2_evidence_status_not_fabricated,
    "P3": p3_no_forced_classification,
    "P4": p4_no_plural_collapse,
    "P5": p5_profit_did_not_weaken_validation,
    "P6": p6_count_did_not_create_transformation,
    "P7": p7_provenance_preserved,
    "P8": p8_capability_not_authority,
    "P9": p9_operator_availability_not_empirical,
    "P10": p10_unobserved_not_clean,
    "P11": p11_runtime_identity_not_semantic,
    "P12": p12_no_permanent_incumbent_immunity,
}


def derive(property_id: str, surface: Mapping[str, Any]) -> GuardedPropertyValue:
    """Dispatch to the declared derivation. Every derivation is a pure function of
    the observable surface — no scenario identifier reaches it."""
    return DERIVATIONS[property_id](surface)
