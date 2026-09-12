"""Authority engine for OCE control plane.

B3.C2 / B2-C2 — capability grants, risk classes, approval gates,
revocation/expiry, denial evidence.

Every consequential action must have a valid, unexpired, non-revoked grant.
Agents cannot approve their own requests. Unknown authority fails closed.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field, asdict
import json

from .clocks import get_clock
from .hashes import generate_id
from .state_machines import is_valid_transition, assert_transition


# Risk classification (B3.C2.S2)
RISK_CLASSES = {
    "read": {"level": 0, "requires_approval": False},
    "local-write": {"level": 1, "requires_approval": False},
    "external-write": {"level": 2, "requires_approval": True},
    "deployment": {"level": 3, "requires_approval": True},
    "destructive": {"level": 4, "requires_approval": True},
    "messaging": {"level": 2, "requires_approval": True},
    "broker": {"level": 4, "requires_approval": True},
    "capital": {"level": 5, "requires_approval": True},
}

# Actions that are always blocked for certain agents
BLOCKED_ACTIONS = {
    "hermes": {"approve_capital", "authorize_deployment", "enable_trading",
               "alter_governance", "bypass_po", "write_po_memory",
               "claim_completion"},
}


@dataclass
class CapabilityGrant:
    grant_id: str
    actor_id: str
    action: str
    target: str
    environment: str
    risk_class: str
    limits: dict = field(default_factory=dict)
    approval_context: dict = field(default_factory=dict)
    idempotency_required: bool = True
    evidence_obligations: list = field(default_factory=list)
    issued_at: str = ""
    expires_at: str = ""
    revoked_at: str = ""
    status: str = "active"
    schema_version: str = "1.0.0"

    def is_expired(self, now: datetime) -> bool:
        if not self.expires_at:
            return False
        exp = datetime.fromisoformat(self.expires_at)
        return now > exp

    def is_active(self, now: datetime) -> bool:
        return self.status == "active" and not self.is_expired(now) and not self.revoked_at


@dataclass
class DenialEnvelope:
    denial_id: str
    reason_code: str
    actor_id: str
    requested_action: str
    requested_target: str
    policy_version: str
    denied_at: str
    remediation: str = ""
    schema_version: str = "1.0.0"

    def to_dict(self) -> dict:
        return asdict(self)


class AuthorityEngine:
    """Verifies grants at admission and before side effects."""

    def __init__(self):
        self._grants: dict[str, CapabilityGrant] = {}
        self._denials: list[DenialEnvelope] = []
        self._policy_version = "2.0.0"
        # Track seen idempotency keys to prevent replay
        self._seen_keys: dict[str, str] = {}  # key -> grant_id that used it

    def issue_grant(self, *, actor_id: str, action: str, target: str,
                    environment: str = "local", risk_class: Optional[str] = None,
                    approved_by: Optional[str] = None, ttl_seconds: int = 3600,
                    **kwargs) -> CapabilityGrant:
        """Issue a capability grant. Capital/deployment/etc require approval."""
        clock = get_clock()
        now = clock.now()

        # Determine risk class if not provided
        if risk_class is None:
            risk_class = self._classify_risk(action)

        # Check blocked actions for this agent type
        agent_type = self._agent_type(actor_id)
        if action in BLOCKED_ACTIONS.get(agent_type, set()):
            raise PermissionError(
                f"Agent '{actor_id}' ({agent_type}) is blocked from action '{action}'"
            )

        # High-risk actions require approval
        risk_info = RISK_CLASSES.get(risk_class, {})
        if risk_info.get("requires_approval") and not approved_by:
            raise PermissionError(
                f"Risk class '{risk_class}' requires explicit approval"
            )

        # Self-approval is blocked (B3.C2.S3)
        if approved_by and approved_by == actor_id:
            raise PermissionError("Agents cannot approve their own request")

        grant = CapabilityGrant(
            grant_id=generate_id(),
            actor_id=actor_id,
            action=action,
            target=target,
            environment=environment,
            risk_class=risk_class,
            limits=kwargs.get("limits", {}),
            approval_context={
                "approved_by": approved_by,
                "approved_at": now.isoformat() if approved_by else "",
                "approval_id": generate_id() if approved_by else "",
            },
            idempotency_required=kwargs.get("idempotency_required", True),
            evidence_obligations=kwargs.get("evidence_obligations", []),
            issued_at=now.isoformat(),
            expires_at=(now + _timedelta_seconds(ttl_seconds)).isoformat(),
        )
        self._grants[grant.grant_id] = grant
        return grant

    def verify_grant(self, grant_id: str, action: str, target: str,
                     environment: str = "local") -> CapabilityGrant:
        """Verify a grant at admission. Raises PermissionError on failure."""
        clock = get_clock()
        now = clock.now()

        grant = self._grants.get(grant_id)
        if grant is None:
            raise PermissionError(f"Grant '{grant_id}' not found")

        if grant.status == "revoked":
            raise PermissionError(f"Grant '{grant_id}' has been revoked")

        if grant.is_expired(now):
            raise PermissionError(f"Grant '{grant_id}' has expired")

        if grant.action != action:
            raise PermissionError(
                f"Grant '{grant_id}' authorizes '{grant.action}', not '{action}'"
            )

        if grant.target != target:
            raise PermissionError(
                f"Grant '{grant_id}' targets '{grant.target}', not '{target}'"
            )

        if grant.environment != environment:
            raise PermissionError(
                f"Grant environment '{grant.environment}' != requested '{environment}'"
            )

        return grant

    def revoke_grant(self, grant_id: str) -> None:
        """Revoke a grant."""
        grant = self._grants.get(grant_id)
        if grant is None:
            raise KeyError(f"Grant '{grant_id}' not found")
        assert_transition("grant", grant.status, "revoked")
        clock = get_clock()
        grant.status = "revoked"
        grant.revoked_at = clock.now().isoformat()

    def expire_grants(self) -> int:
        """Expire any grants past their expiry. Returns count expired."""
        clock = get_clock()
        now = clock.now()
        count = 0
        for grant in self._grants.values():
            if grant.status == "active" and grant.is_expired(now):
                grant.status = "expired"
                count += 1
        return count

    def record_denial(self, *, reason_code: str, actor_id: str,
                      requested_action: str, requested_target: str,
                      remediation: str = "") -> DenialEnvelope:
        """Record a denial with safe reason codes."""
        clock = get_clock()
        denial = DenialEnvelope(
            denial_id=generate_id(),
            reason_code=reason_code,
            actor_id=actor_id,
            requested_action=requested_action,
            requested_target=requested_target,
            policy_version=self._policy_version,
            denied_at=clock.now().isoformat(),
            remediation=remediation,
        )
        self._denials.append(denial)
        return denial

    def check_idempotency_replay(self, idempotency_key: str, grant_id: str) -> bool:
        """Check if an idempotency key has been used (replay detection)."""
        if idempotency_key in self._seen_keys:
            return True  # replayed
        self._seen_keys[idempotency_key] = grant_id
        return False

    def _classify_risk(self, action: str) -> str:
        """Classify an action into a risk class."""
        action_lower = action.lower()
        if any(w in action_lower for w in ["deploy", "provision", "cloud"]):
            return "deployment"
        if any(w in action_lower for w in ["delete", "destroy", "drop", "truncate"]):
            return "destructive"
        if any(w in action_lower for w in ["capital", "trade", "order"]):
            return "capital"
        if any(w in action_lower for w in ["broker", "execute_order"]):
            return "broker"
        if any(w in action_lower for w in ["message", "send", "notify", "telegram"]):
            return "messaging"
        if any(w in action_lower for w in ["write", "create", "update", "submit"]):
            return "local-write"
        return "read"

    def _agent_type(self, actor_id: str) -> str:
        """Extract agent type from actor_id."""
        if actor_id.startswith("po-"):
            return "po"
        if actor_id.startswith("hermes-"):
            return "hermes"
        if actor_id.startswith("operator-"):
            return "operator"
        if actor_id.startswith("worker-"):
            return "worker"
        return "service"

    @property
    def grants(self) -> dict:
        return dict(self._grants)

    @property
    def denials(self) -> list:
        return list(self._denials)


def _timedelta_seconds(seconds: int):
    from datetime import timedelta
    return timedelta(seconds=seconds)
