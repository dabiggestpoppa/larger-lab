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


#: Canonical risk-class vocabulary — mirrors control-plane
#: capability-grant.schema.json ("risk_class" enum): read / local-write /
#: external-write / deployment / destructive / messaging / broker / capital.
#: G2-P0-D: ANY risk_class outside this vocabulary fails closed. Unknown classes
#: must never silently bypass the authority-bearing guard by not matching a
#: hardcoded tuple.
RISK_CLASSES = frozenset({
    "read", "local-write", "external-write", "deployment",
    "destructive", "messaging", "broker", "capital",
})

#: classes whose issue/ratification itself vests authority (no self-ratification)
AUTHORITY_BEARING_RISK_CLASSES = frozenset({"deployment", "destructive", "broker", "capital"})


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

    def __post_init__(self) -> None:
        # G2-P0-D: fail closed at construction — an unknown risk class must not
        # exist as a grant, so no later guard can be bypassed by an unknown label.
        if self.risk_class not in RISK_CLASSES:
            raise AuthorityViolation(
                f"unknown risk_class {self.risk_class!r}; canonical vocabulary: {sorted(RISK_CLASSES)}"
            )

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
        risk_class implies authority (deny-by-default, no self-ratification).

        G2-P0-D: risk_class outside the canonical vocabulary fails closed here
        too (belt), even if the grant object was produced elsewhere."""
        if grant.risk_class not in RISK_CLASSES:
            raise AuthorityViolation(
                f"unknown risk_class {grant.risk_class!r}; canonical vocabulary: {sorted(RISK_CLASSES)}"
            )
        if grant.risk_class in AUTHORITY_BEARING_RISK_CLASSES:
            if ratified_by == grant.actor:
                raise AuthorityViolation("an actor may not self-ratify an authority-bearing grant")
        self._grants[grant.grant_id] = grant
        self._by_actor.setdefault(grant.actor, []).append(grant.grant_id)
        self._events.append(f"ISSUE {grant.grant_id} ratified_by={ratified_by}")

    def revoke(self, grant_id: str, actor: str) -> None:
        g = self._grants.get(grant_id)
        if g and g.actor == actor and g.risk_class == "capital":
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
    """Operational authority projection for a scenario: actor -> level + grants.

    G1R-09: initialization and governed change are explicit two phases.
      - seed_level() may only be used BEFORE freeze_initialization().
      - after freeze, the ONLY legal path to alter an actor's level/grants is a
        governed, ratified change (propose + ratify).
    set_level() is kept as an alias for the seeder so existing fixture init reads
    naturally, but it is equally blocked once initialization is frozen.
    """

    def __init__(self) -> None:
        self.actors: Dict[str, str] = {}          # actor -> AuthorityLevel
        self.registry = AuthorityRegistry()
        self._ratifications: List[Tuple[str, str, str]] = []  # (proposer, target, grant_id)
        self._proposals: List[Tuple[str, str, CapabilityGrant]] = []  # pending proposals (G2R-05)
        self._initialization_frozen = False

    def freeze_initialization(self) -> None:
        self._initialization_frozen = True

    @property
    def initialization_frozen(self) -> bool:
        return self._initialization_frozen

    def seed_level(self, actor: str, level: str) -> None:
        """Fixture-initialization seeding. Forbidden after initialization freeze.

        G2-P0-C: seeding is privileged for SETUP only, not an ontology bypass —
        unknown authority levels are rejected here ("SUPREME_OVERLORD" fails).
        """
        if self._initialization_frozen:
            raise AuthorityViolation(
                "authority initialization is frozen; use the governed ratify/propose path"
            )
        if isinstance(level, AuthorityLevel):
            level = level.value
        if level not in {m.value for m in AuthorityLevel}:
            raise AuthorityViolation(
                f"unknown authority level {level!r}; canonical: {sorted(m.value for m in AuthorityLevel)}"
            )
        self.actors[actor] = level

    def set_level(self, actor: str, level: str) -> None:
        # alias retained for readable fixture init; shares the freeze + enum guards
        self.seed_level(actor, level)

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
        """A worker/agent may PROPOSE an authority change but never self-ratify it.

        G2R-05: every ratification MUST reference a prior proposal. The proposal
        stores the complete grant so a later ratification cannot fabricate a grant
        that was never proposed."""
        self._ratifications.append((proposer, target_actor, grant.grant_id))
        self._proposals.append((proposer, target_actor, grant))

    def pending_proposal(self, proposer: str, target_actor: str, risk_class: Optional[str] = None,
                         grant_id: Optional[str] = None) -> Optional[CapabilityGrant]:
        """Resolve an existing proposal, or None. Used by the governed RATIFY
        path so the ratification applies the PROPOSED grant, never a fabricated
        reconstruction."""
        for p, t, g in self._proposals:
            if p != proposer or t != target_actor:
                continue
            if risk_class is not None and g.risk_class != risk_class:
                continue
            if grant_id is not None and g.grant_id != grant_id:
                continue
            return g
        return None

    def ratify_authority_change(self, ratifier: str, proposer: str, target_actor: str, grant: CapabilityGrant) -> None:
        """Only an actor with OPERATOR (or explicit governor mandate) may ratify;
        only a PRIOR PROPOSAL may be ratified (G2R-05); all authority-bearing risk
        classes (deployment / destructive / broker / capital) require OPERATOR
        ratification consistently."""
        if ratifier == target_actor:
            raise AuthorityViolation("self-ratification of authority change is forbidden")
        if self.pending_proposal(proposer, target_actor, grant_id=grant.grant_id) is None:
            raise AuthorityViolation(
                f"ratification of {grant.grant_id!r} has no PRIOR proposal "
                f"(proposer={proposer!r}, target={target_actor!r}); a grant cannot "
                f"be fabricated at ratification time"
            )
        if grant.risk_class in AUTHORITY_BEARING_RISK_CLASSES:
            if self.level(ratifier) != AuthorityLevel.OPERATOR.value:
                raise AuthorityViolation(
                    f"{ratifier} lacks operator authority to ratify a {grant.risk_class} change"
                )
        # ratification is recorded; the registry only issues AFTER ratification
        self.registry.issue(grant, ratified_by=ratifier)
        self._ratifications.append((ratifier, target_actor, grant.grant_id))