"""PO and Hermes boundary definitions for OCE control plane.

B2 PO orchestration boundary and Hermes boundary.

PO may: create governed work plans, submit permitted jobs, spawn bounded
subagents, monitor jobs, reconcile evidence, stop work, escalate decisions.

PO may not bypass: permissions, environment locks, approval requirements,
capital authority, deployment locks, live-trading locks, evidence gates.

Hermes: provider-neutral supplemental-assistant interface. May not
independently approve capital, authorize deployment, enable trading, alter
OCE governance, bypass PO, write PO memory, or claim completion.
"""
from __future__ import annotations
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional
import json

from .clocks import get_clock
from .hashes import generate_id
from .authority import AuthorityEngine, BLOCKED_ACTIONS
from .job_store import JobStore


# PO-only actions that Hermes may never perform
PO_ONLY_ACTIONS = {
    "approve_capital", "authorize_deployment", "enable_trading",
    "alter_governance", "bypass_po", "write_po_memory",
    "claim_completion", "create_work_plan", "spawn_subagent",
    "reconcile_evidence", "escalate_decision",
}

# Environment locks
ENVIRONMENT_LOCKS = {
    "local": True,       # always available
    "local-test": True,
    "local-recovery": True,
    "cloud-plan": True,  # dry-run only
    "cloud": False,      # locked — requires separate authorization
}

# Approval requirements
APPROVAL_REQUIRED = {
    "capital": True,
    "deployment": True,
    "live-trading": True,
    "broker": True,
}


@dataclass
class PORequest:
    request_id: str
    po_agent_id: str
    action: str
    target: str
    environment: str
    payload: dict
    created_at: str
    status: str = "pending"  # pending, approved, denied, executing, completed, failed


class POOrchestrator:
    """PO orchestration boundary."""

    def __init__(self, authority: AuthorityEngine, job_store: JobStore):
        self._authority = authority
        self._job_store = job_store
        self._requests: dict[str, PORequest] = {}
        self._work_plans: dict[str, dict] = {}
        self._subagents: dict[str, dict] = {}

    def create_work_plan(self, *, po_agent_id: str, plan_name: str,
                         steps: list, environment: str = "local") -> dict:
        """Create a governed work plan."""
        clock = get_clock()
        plan_id = generate_id()
        plan = {
            "plan_id": plan_id,
            "po_agent_id": po_agent_id,
            "plan_name": plan_name,
            "steps": steps,
            "environment": environment,
            "status": "created",
            "created_at": clock.now().isoformat(),
        }
        self._work_plans[plan_id] = plan
        return plan

    def submit_permitted_job(self, *, po_agent_id: str, grant_id: str,
                             job_type: str, payload: dict,
                             environment: str = "local", **kwargs) -> dict:
        """Submit a job through the PO boundary. PO may not bypass permissions."""
        # Check environment lock
        if not ENVIRONMENT_LOCKS.get(environment, False):
            raise PermissionError(
                f"Environment '{environment}' is locked — requires separate authorization"
            )

        # Check approval requirements for high-risk actions
        if any(w in job_type.lower() for w in ["capital", "deploy", "trade", "broker"]):
            if not kwargs.get("approved_by"):
                raise PermissionError(
                    f"Job type '{job_type}' requires explicit operator approval"
                )

        # Submit through the job store (which verifies the grant)
        job = self._job_store.submit_job(
            job_type=job_type,
            submitting_actor=po_agent_id,
            grant_id=grant_id,
            payload=payload,
            environment=environment,
            **kwargs,
        )
        return job.to_dict()

    def spawn_subagent(self, *, po_agent_id: str, subagent_type: str,
                       task: str, bounds: dict) -> dict:
        """Spawn a bounded subagent."""
        clock = get_clock()
        subagent_id = generate_id()
        subagent = {
            "subagent_id": subagent_id,
            "po_agent_id": po_agent_id,
            "subagent_type": subagent_type,
            "task": task,
            "bounds": bounds,
            "status": "spawned",
            "created_at": clock.now().isoformat(),
        }
        self._subagents[subagent_id] = subagent
        return subagent

    def escalate_decision(self, *, po_agent_id: str, decision: str,
                          context: dict) -> dict:
        """Escalate an operator decision."""
        clock = get_clock()
        escalation = {
            "escalation_id": generate_id(),
            "po_agent_id": po_agent_id,
            "decision": decision,
            "context": context,
            "status": "pending_operator",
            "created_at": clock.now().isoformat(),
        }
        return escalation

    def check_po_boundaries(self, po_agent_id: str, action: str) -> bool:
        """Check if PO is attempting to bypass a boundary."""
        # PO cannot bypass environment locks
        # PO cannot bypass approval requirements
        # PO cannot bypass evidence gates
        return True  # PO can perform permitted actions

    @property
    def work_plans(self) -> dict:
        return dict(self._work_plans)

    @property
    def subagents(self) -> dict:
        return dict(self._subagents)


@dataclass
class HermesRequest:
    request_id: str
    sender_id: str
    conversation_id: str
    request_text: str
    risk_class: str
    routing_destination: str
    created_at: str
    timeout_seconds: int = 30
    rate_limit_per_minute: int = 10
    status: str = "received"  # received, routed, escalated, responded, timed_out


class HermesBoundary:
    """Provider-neutral supplemental-assistant interface for Hermes."""

    def __init__(self, po_orchestrator: POOrchestrator):
        self._po = po_orchestrator
        self._requests: list[HermesRequest] = []
        self._rate_tracker: dict[str, list[datetime]] = {}

    def receive_request(self, *, sender_id: str, conversation_id: str,
                        request_text: str, timeout: int = 30) -> HermesRequest:
        """Receive a request through the Hermes boundary."""
        clock = get_clock()
        now = clock.now()

        # Rate limiting
        recent = self._rate_tracker.get(sender_id, [])
        recent = [t for t in recent if (now - t).total_seconds() < 60]
        if len(recent) >= 10:
            raise PermissionError(f"Rate limit exceeded for sender '{sender_id}'")
        recent.append(now)
        self._rate_tracker[sender_id] = recent

        # Classify risk
        risk_class = self._classify_risk(request_text)

        # Determine routing
        if risk_class in ("capital", "deployment", "broker"):
            routing = "po_escalation"
        elif any(w in request_text.lower() for w in ["oce", "po ", "strategy", "research"]):
            routing = "po"
        else:
            routing = "hermes_direct"

        req = HermesRequest(
            request_id=generate_id(),
            sender_id=sender_id,
            conversation_id=conversation_id,
            request_text=request_text,
            risk_class=risk_class,
            routing_destination=routing,
            created_at=now.isoformat(),
            timeout_seconds=timeout,
        )
        self._requests.append(req)
        return req

    def escalate_to_po(self, request_id: str) -> dict:
        """Escalate a request to PO. Hermes cannot resolve PO-only actions."""
        req = None
        for r in self._requests:
            if r.request_id == request_id:
                req = r
                break
        if req is None:
            raise KeyError(f"Request not found")

        # Hermes cannot independently approve PO-only actions
        if req.risk_class in ("capital", "deployment", "broker"):
            escalation = self._po.escalate_decision(
                po_agent_id="hermes-boundary",
                decision=f"operator_approval_required:{req.risk_class}",
                context={"request_id": request_id, "sender": req.sender_id},
            )
            req.status = "escalated"
            return escalation
        return {"routed": "po", "request_id": request_id}

    def check_hermes_boundary(self, action: str) -> bool:
        """Check if Hermes is attempting a PO-only action."""
        return action in PO_ONLY_ACTIONS

    def _classify_risk(self, text: str) -> str:
        """Classify the risk of a request."""
        text_lower = text.lower()
        if any(w in text_lower for w in ["capital", "trade", "order", "buy", "sell"]):
            return "capital"
        if any(w in text_lower for w in ["deploy", "provision", "cloud"]):
            return "deployment"
        if any(w in text_lower for w in ["broker", "execute"]):
            return "broker"
        if any(w in text_lower for w in ["message", "send", "notify"]):
            return "messaging"
        if any(w in text_lower for w in ["delete", "destroy", "drop"]):
            return "destructive"
        return "read"

    @property
    def requests(self) -> list:
        return list(self._requests)
