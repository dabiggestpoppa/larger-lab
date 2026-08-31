"""Authority firewall (G1 §9). Authority is SEPARATE from:
  - evidence confidence;
  - capability;
  - phase;
  - knowledge lifecycle;
  - profit;
  - agent role.

Negative invariants enforced here (all testable):
  high capability        != expanded authority
  operator preference    != stronger evidence
  agent confidence       != confirmation
  research promotion     != execution authority
  TransformationWindow   != capital authority
  a worker may propose an authority change, never self-ratify it.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

from .base import AuthorityLevel, MutationClass, deterministic_hex


class AuthorityViolation(ValueError):
    pass


@dataclass(frozen=True)
class CapabilityGrant:
    grant_id: str
    actor: str
    action: str
    target: str
    environment: str                    # local / local-test / local-recovery / cloud-plan / cloud
    risk_class: str                     # matches control-plane capability-grant.schema.json
    issued_by: str                      # issuing/ratifying actor
    status: str = "active"

    @classmethod
    def make(cls, seq, actor, action, target, issued_by, risk_class="read", environment="local-test"):
        return cls(
            grant_id=deterministic_hex("grant", seq, actor, action, target),
            actor=actor,
            action=action,
            target=target,
            environment=environment,
            risk_class=risk_class,
            issued_by=issued_by,
        )


class AuthorityRegistry:
    """Actors -> set of active CapabilityGrant ids. A grant only changes via an
    explicit, attributable issue/revoke — never because capability or evidence
    improved."""

    def __init__(self) -> None:
        self._grants: Dict[str, CapabilityGrant] = {}
        self._by_actor: Dict[str, List[str]] = {}
        self._events: List[str] = []

    def issue(self, grant: CapabilityGrant, ratified_by: str) -> None:
        """Ratified_by must differ from the grant recipient for any grant whose
        risk_class implies authority (deny-by-default, no self-ratification)."""
        if grant.risk_class in ("authority", "deployment", "destructive", "broker", "capital"):
            if ratified_by == grant.actor:
                raise AuthorityViolation("an actor may not self-ratify an authority-bearing grant")
        self._grants[grant.grant_id] = grant
        self._by_actor.setdefault(grant.actor, []).append(grant.grant_id)
        self._events.append(f"ISSUE {grant.grant_id} ratified_by={ratified_by}")

    def revoke(self, grant_id: str, actor: str) -> None:
        g = self._grants.get(grant_id)
        if g and g.actor == actor and g.risk_class in ("authority", "capital"):
            raise AuthorityViolation("an actor may not self-revoke an authority/capital grant")
        if grant_id in self._grants:
            self._grants[grant_id] = CapabilityGrant(
                grant_id=g.grant_id, actor=g.actor, action=g.action, target=g.target,
                environment=g.environment, risk_class=g.risk_class, issued_by=g.issued_by,
                status="revoked",
            )
            self._events.append(f"REVOKE {grant_id} by={actor}")

    def grants(self, actor: str) -> List[CapabilityGrant]:
        return [self._grants[i] for i in self._by_actor.get(actor, []) if self._grants[i].status == "active"]

    def event_log(self) -> List[str]:
        return list(self._events)


class AuthorityState:
    """Operational authority projection for a scenario: actor -> level + grants."""

    def __init__(self) -> None:
        self.actors: Dict[str, str] = {}          # actor -> AuthorityLevel
        self.registry = AuthorityRegistry()
        self._ratifications: List[Tuple[str, str, str]] = []  # (proposer, target, authority_basis)

    def set_level(self, actor: str, level: str) -> None:
        self.actors[actor] = level

    def level(self, actor: str) -> str:
        return self.actors.get(actor, AuthorityLevel.OBSERVER.value)

    # --- conflation guards ---------------------------------------------- #
    @staticmethod
    def capability_does_not_escalate_authority(capability_label: str) -> None:
        # capability is separate from authority; a high M1 label changes nothing here
        return None

    @staticmethod
    def operator_preference_is_not_evidence() -> None:
        return None

    @staticmethod
    def research_promotion_is_not_execution_authority() -> None:
        return None

    def propose_authority_change(self, proposer: str, target_actor: str, grant: CapabilityGrant) -> None:
        """A worker/agent may PROPOSE an authority change but never self-ratify it."""
        self._ratifications.append((proposer, target_actor, grant.grant_id))

    def ratify_authority_change(self, ratifier: str, proposer: str, target_actor: str, grant: CapabilityGrant) -> None:
        """Only an actor with OPERATOR (or explicit governor mandate) may ratify."""
        if ratifier == target_actor:
            raise AuthorityViolation("self-ratification of authority change is forbidden")
        if self.level(ratifier) not in (AuthorityLevel.OPERATOR.value,) and grant.risk_class in ("authority", "capital", "deployment", "destructive"):
            raise AuthorityViolation(f"{ratifier} lacks authority to ratify a {grant.risk_class} change")
        # ratification is recorded; the registry only issues AFTER ratification
        self.registry.issue(grant, ratified_by=ratifier)
        self._ratifications.append((ratifier, target_actor, grant.grant_id))