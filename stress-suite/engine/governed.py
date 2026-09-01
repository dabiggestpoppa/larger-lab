"""GovernedTransitionExecutor (G1R-07).

The authoritative execution path for stress evidence. It composes, generically:

  1. topology legality (M4/M5 pure machines);
  2. evaluation-contract version binding / freeze (contract_version mismatch
     fails closed, documented policy: a supplied version MUST match the active
     edge contract, and blank means "use the active contract" — smoke only);
  3. cross-cutting forbidden-transition rules (engine.forbidden);
  4. authority firewall (capability != authority, no self-ratification);
  5. evidence / provenance recording.

NO S01–S24-specific logic lives here. Low-level pure state machines remain unit
testable; the Scenario/Replay path used for stress evidence MUST go through this
executor so constitutional rules cannot be bypassed by calling a lower API.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .base import MutationClass, deterministic_hex
from .authority import AuthorityState, AuthorityViolation
from .evidence import EvidenceRecord
from .forbidden import ForbiddenTransitionValidator as F
from .lifecycle import LifecycleEngine
from .phase import PhaseDecisionError, PhaseStateMachine


@dataclass(frozen=True)
class TraceEntry:
    seq: int
    machine: str
    event_type: str
    from_state: str
    to_state: str
    allowed: bool
    applied: bool
    rule_ids: Tuple[str, ...]
    rationale: str
    kind: str   # OK / TOPOLOGY_DENIED / FORBIDDEN / CONTRACT_VERSION_MISMATCH / AUTHORITY_INVALID / UNKNOWN_RECORD / UNKNOWN_MACHINE / ADVISORY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seq": self.seq,
            "machine": self.machine,
            "event_type": self.event_type,
            "from": self.from_state,
            "to": self.to_state,
            "allowed": self.allowed,
            "applied": self.applied,
            "rule_ids": list(self.rule_ids),
            "rationale": self.rationale,
            "kind": self.kind,
        }


class GovernedTransitionExecutor:
    def __init__(self, phase: PhaseStateMachine, lifecycle: LifecycleEngine, authority: Optional[AuthorityState] = None):
        self.phase = phase
        self.lifecycle = lifecycle
        self.authority = authority or AuthorityState()
        self.evidence: List[EvidenceRecord] = []      # governed evidence registry
        self.advisory: List[dict] = []                # operator_preference / profit — NEVER evidence
        self._f = F

    # ------------------------------------------------------------------ #
    # dispatch (duck-typed event: seq, machine, event_type, payload, contract_version)
    # ------------------------------------------------------------------ #
    def execute(self, event) -> TraceEntry:
        machine = getattr(event, "machine", "")
        if machine == "phase":
            return self._run_phase(event)
        if machine == "lifecycle":
            return self._run_lifecycle(event)
        if machine == "authority":
            return self._run_authority(event)
        if machine == "evidence":
            return self._run_evidence(event)
        if machine == "policy":
            return self._run_policy(event)
        return TraceEntry(
            seq=event.seq, machine=machine or "?", event_type=getattr(event, "event_type", ""),
            from_state="", to_state="", allowed=False, applied=False, rule_ids=(),
            rationale="unknown machine", kind="UNKNOWN_MACHINE",
        )

    # ------------------------------------------------------------------ #
    # actor / authority identity binding (G2-P0-A / P0-B)
    # ------------------------------------------------------------------ #
    def _bind(self, event, declared_level=None):
        """Validate that a governed action is driven by a REGISTERED actor whose
        claimed authority level matches AuthorityState. Returns
        (registered_level, None) on success, or (None, TraceEntry) on a
        fail-closed rejection.

        Policy (chosen, documented): governed phase/lifecycle/authority actions
        are attributed to event.actor. A payload `authority_level` claim must
        EXACTLY equal AuthorityState.level(actor) or be omitted (then derived
        from AuthorityState). The payload authority level is NEVER trusted
        independently — a WORKER cannot self-declare GOVERNOR. Unknown actors
        cannot drive governed actions at all.
        """
        actor = event.actor
        if actor not in self.authority.actors:
            return None, TraceEntry(
                event.seq, event.machine, event.event_type, "", "",
                False, False, ("AUTHORITY_ACTOR_UNKNOWN",),
                f"actor {actor!r} is not registered in AuthorityState; governed action rejected",
                "AUTHORITY_INVALID",
            )
        registered = self.authority.level(actor)
        if declared_level is not None and declared_level != registered:
            return None, TraceEntry(
                event.seq, event.machine, event.event_type, "", "",
                False, False, ("AUTHORITY_LEVEL_MISMATCH",),
                f"actor {actor!r} is registered as {registered} but claimed {declared_level}",
                "AUTHORITY_INVALID",
            )
        return registered, None

    # ------------------------------------------------------------------ #
    # phase
    # ------------------------------------------------------------------ #
    def _run_phase(self, event) -> TraceEntry:
        p = event.payload or {}
        to_state = p.get("to_state", "")
        mutation_class = p.get("mutation_class", MutationClass.READ_ONLY.value)
        from_state = self.phase.state

        # 1) contract version must match active phase edge contract (fail closed)
        if event.contract_version and event.contract_version != self.phase.edge_table.contract_version:
            return TraceEntry(
                event.seq, "phase", event.event_type, from_state, to_state,
                False, False, ("CONTRACT_VERSION_MISMATCH",),
                f"phase event expects contract {event.contract_version} but active is {self.phase.edge_table.contract_version}",
                "CONTRACT_VERSION_MISMATCH",
            )

        # 2) G2-P0-A identity binding: a governed phase step is attributed to
        #    event.actor; a payload authority_level claim must exactly equal the
        #    actor's registered level (or be omitted and derived).
        bound, entry = self._bind(event, p.get("authority_level"))
        if entry is not None:
            return entry
        level = bound

        # 3) authority validity: exception BEFORE ledger mutation (documented policy),
        #    converted to a deterministic invalid replay event here.
        try:
            provisional = self.phase.evaluate(
                seq=event.seq, actor=event.actor, to_state=to_state,
                evidence_vector=p.get("evidence_vector", {}), authority_level=level,
                mutation_class=mutation_class, operator_required=p.get("operator_required", False),
                evidence_refs=p.get("evidence_refs", []), reason=p.get("reason", ""),
            )
        except PhaseDecisionError as exc:
            return TraceEntry(
                event.seq, "phase", event.event_type, from_state, to_state,
                False, False, ("AUTHORITY_INVALID",), str(exc), "AUTHORITY_INVALID",
            )

        # 3) cross-cutting forbidden rules
        rule_ids: List[str] = []
        if provisional.allowed:
            r = self._f.watch_to_architecture_mutation(from_state, mutation_class)
            if r.violation:
                rule_ids.append(r.rule_id)
            r = self._f.window_to_capital(from_state, mutation_class)  # redundant w/ capital; recorded
            if r.violation:
                rule_ids.append(r.rule_id)

        if rule_ids:
            blurb = "; ".join(rule_ids)
            decision = replace(provisional, allowed=False, rationale=f"forbidden: {blurb}", rule_ids=rule_ids)
        else:
            decision = provisional

        self.phase.apply_authoritative(decision)
        kind = "OK" if decision.allowed else ("FORBIDDEN" if rule_ids else "TOPOLOGY_DENIED")
        return TraceEntry(
            event.seq, "phase", event.event_type, from_state, to_state,
            decision.allowed, decision.allowed, tuple(decision.rule_ids),
            decision.rationale, kind,
        )

    # ------------------------------------------------------------------ #
    # lifecycle
    # ------------------------------------------------------------------ #
    def _run_lifecycle(self, event) -> TraceEntry:
        p = event.payload or {}
        to_state = p.get("to_state", "")
        record_id = event.target

        if event.contract_version and event.contract_version != self.lifecycle.edge_table.contract_version:
            return TraceEntry(
                event.seq, "lifecycle", event.event_type, "", to_state, False, False,
                ("CONTRACT_VERSION_MISMATCH",), f"lifecycle expects {event.contract_version} but active is {self.lifecycle.edge_table.contract_version}",
                "CONTRACT_VERSION_MISMATCH",
            )

        # G2-P0-A: lifecycle state changes are attributed to a registered actor
        # whose claimed level matches AuthorityState.
        bound, entry = self._bind(event, p.get("authority_level"))
        if entry is not None:
            return entry
        level = bound

        action = p.get("action")
        # cross-cutting policy rejections for knowledge/ontology actions
        if action == "PROMOTE_ONTOLOGY":
            evidence_sufficient = p.get("evidence_sufficient", False)
            admissible = p.get("admissible", False)
            rule = self._f.unresolved_to_ontology(p.get("record_kind", "UNRESOLVED_PATTERN"), evidence_sufficient, admissible)
            return self._policy_result(event, rule)

        # normal lifecycle transition through the ENGINE's active edge table,
        # which now returns explicit allowed/applied/violation (G1R-03/G1R-05)
        if record_id not in self.lifecycle.records:
            return TraceEntry(event.seq, "lifecycle", event.event_type, "", to_state, False, False,
                              ("UNKNOWN_RECORD",), f"unknown knowledge record {record_id}", "UNKNOWN_RECORD")

        # cross-cutting RULE-10 (dormant -> active) checked before applying
        current = self.lifecycle.records[record_id].state
        rule10 = self._f.dormant_to_active(current, to_state)
        if rule10.violation:
            tr = self.lifecycle.records[record_id].transition(
                seq=event.seq, to_state=to_state, actor=event.actor,
                authority_basis=p.get("authority_basis", ""), authority_level=level,
                reason=p.get("reason", ""), evidence_refs=p.get("evidence_refs", []),
            )  # records the refused attempt with explicit violation, no state change
            return TraceEntry(event.seq, "lifecycle", event.event_type, current, to_state,
                              False, False, ("RULE-10",), tr.violation or rule10.reason, "FORBIDDEN")

        tr = self.lifecycle.transition(
            record_id, seq=event.seq, to_state=to_state, actor=event.actor,
            authority_basis=p.get("authority_basis", ""), authority_level=level,
            reason=p.get("reason", ""), evidence_refs=p.get("evidence_refs", []),
        )
        kind = "OK" if tr.allowed else "TOPOLOGY_DENIED"
        return TraceEntry(event.seq, "lifecycle", event.event_type, tr.from_state, tr.to_state,
                          tr.allowed, tr.applied, (), tr.violation or p.get("reason", ""), kind)

    # ------------------------------------------------------------------ #
    # authority
    # ------------------------------------------------------------------ #
    def _run_authority(self, event) -> TraceEntry:
        p = event.payload or {}
        action = p.get("action", "REQUEST_AUTHORITY")
        if action == "REQUEST_AUTHORITY":
            # G2-P0-A: the requesting actor must be registered.
            _bound, entry = self._bind(event)
            if entry is not None:
                return entry
            # RULE-06: capability gain must not self-expand authority (S21)
            rule = self._f.capability_to_authority(
                capability_gain=p.get("capability_gain", False),
                authority_gain=p.get("authority_gain", False),
            )
            if rule.violation:
                return self._policy_result(event, rule, from_state=event.actor)
            # a proposal is representable; ratification is governed separately
            try:
                self.authority.propose_authority_change(event.actor, p.get("target", event.actor),
                                                        _dummy_grant(event))
                return TraceEntry(event.seq, "authority", event.event_type, event.actor,
                                  "proposed", True, True, (), "authority change proposed (not ratified)", "OK")
            except AuthorityViolation as exc:
                return TraceEntry(event.seq, "authority", event.event_type, event.actor,
                                  "rejected", False, False, ("AUTHORITY_FIREWALL",), str(exc), "FORBIDDEN")
        elif action == "RATIFY":
            # G2-P0-A: the ratifier must be a registered actor.
            _bound, entry = self._bind(event)
            if entry is not None:
                return entry
            # G2-P0-B: ratifier identity is bound to event.actor — a worker cannot
            # submit event.actor=WORKER_1 with payload.ratifier=OPERATOR.
            ratifier = event.actor
            declared_ratifier = p.get("ratifier", ratifier)
            if declared_ratifier != ratifier:
                return TraceEntry(
                    event.seq, "authority", event.event_type, p.get("target", ""),
                    "rejected", False, False, ("AUTHORITY_RATIFIER_MISMATCH",),
                    f"declared ratifier {declared_ratifier!r} != event.actor {ratifier!r}",
                    "AUTHORITY_INVALID",
                )
            try:
                self.authority.ratify_authority_change(ratifier, p.get("proposer", ""),
                                                       p.get("target", ""), _dummy_grant(event))
                return TraceEntry(event.seq, "authority", event.event_type, p.get("target", ""),
                                  "ratified", True, True, (), "ratified", "OK")
            except AuthorityViolation as exc:
                return TraceEntry(event.seq, "authority", event.event_type, p.get("target", ""),
                                  "rejected", False, False, ("AUTHORITY_FIREWALL",), str(exc), "FORBIDDEN")
        return TraceEntry(event.seq, "authority", event.event_type, "", "", False, False, (),
                          "unknown authority action", "UNKNOWN_MACHINE")

    # ------------------------------------------------------------------ #
    # evidence
    # ------------------------------------------------------------------ #
    def _run_evidence(self, event) -> TraceEntry:
        p = event.payload or {}
        action = p.get("action", "RECORD")
        if action == "RECORD":
            actual_kind = p.get("actual_kind", p.get("kind", "OBSERVATION"))
            claimed_kind = p.get("claimed_kind", actual_kind)
            rule = self._f.agent_confidence_to_confirmation(actual_kind, claimed_kind)
            if rule.violation:
                return self._policy_result(event, rule)
            ev = EvidenceRecord.make(event.seq, p.get("claim", ""), kind=actual_kind, source_label=p.get("source_label", ""))
            self.evidence.append(ev)
            return TraceEntry(event.seq, "evidence", event.event_type, "", ev.record_id, True, True,
                              (), "evidence recorded", "OK")
        return TraceEntry(event.seq, "evidence", event.event_type, "", "", False, False, (), "unknown evidence action", "UNKNOWN_MACHINE")

    # ------------------------------------------------------------------ #
    # policy advisory — operator preference / profit MUST NOT touch evidence or grants
    # ------------------------------------------------------------------ #
    def _run_policy(self, event) -> TraceEntry:
        p = event.payload or {}
        action = p.get("action", "operator_preference")
        before_grants = {a: [g.grant_id for g in self.authority.registry.grants(a)] for a in self.authority.actors}
        before_evidence = len(self.evidence)
        # advisory only: recorded outside the evidence registry
        self.advisory.append({"seq": event.seq, "action": action, "detail": p.get("detail", "")})
        unchanged_grants = {a: [g.grant_id for g in self.authority.registry.grants(a)] for a in self.authority.actors} == before_grants
        unchanged_evidence = len(self.evidence) == before_evidence
        never_evidence = action in ("operator_preference", "profit_report") and unchanged_evidence and unchanged_grants
        return TraceEntry(event.seq, "policy", event.event_type, "", action, True, True, (),
                          "advisory recorded; evidence/grants untouched" if never_evidence else "advisory",
                          "ADVISORY")

    # ------------------------------------------------------------------ #
    # helper for forbidden-rule rejections with rule_id preserved
    # ------------------------------------------------------------------ #
    def _policy_result(self, event, rule, from_state=""):
        return TraceEntry(
            event.seq, event.machine, event.event_type, from_state, "",
            False, False, (rule.rule_id,), rule.reason, "FORBIDDEN",
        )


def _dummy_grant(event):
    """A minimal grant object for authority FIFO bookkeeping in the governed
    executor. Real capability grants come from the registry's make()."""
    from .authority import CapabilityGrant
    p = event.payload or {}
    return CapabilityGrant(
        grant_id=deterministic_hex("grant", event.seq, p.get("actor", ""), p.get("target", ""), p.get("action", "")),
        actor=p.get("target", p.get("actor", "?")),
        action=p.get("grant_action", "capability"),
        target=p.get("target_scope", "local-test"),
        environment="local-test",
        risk_class=p.get("risk_class", "read"),
        issued_by=p.get("ratifier", event.actor),
    )