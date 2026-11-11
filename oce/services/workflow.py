"""C3.S2 workflow service: versioned state machines, leases, retries, cancellations, approvals.

Deterministic and offline. Every operation takes an explicit integer ``now`` and returns a fresh
run document; nothing is mutated in place. Replayed events are idempotent, so a crash-and-replay
never advances a run twice, and an illegal transition is refused rather than coerced.
"""
from __future__ import annotations

from ..operator.model import OperatorRefusal, object_digest

DEFINITION_FIELDS = ("id", "version", "initial", "states", "transitions", "terminal")
TRANSITION_FIELDS = ("event", "from", "to")


def define_workflow(definition):
    """Validate and normalize a versioned state machine."""
    for key in DEFINITION_FIELDS:
        if key not in definition:
            raise OperatorRefusal("REFUSED_INVALID_WORKFLOW", key)
    if int(definition["version"]) < 1:
        raise OperatorRefusal("REFUSED_INVALID_WORKFLOW", "version")
    states = list(definition["states"])
    if len(set(states)) != len(states) or not states:
        raise OperatorRefusal("REFUSED_INVALID_WORKFLOW", "states")
    if definition["initial"] not in states:
        raise OperatorRefusal("REFUSED_INVALID_WORKFLOW", "initial")
    terminal = list(definition["terminal"])
    if any(state not in states for state in terminal):
        raise OperatorRefusal("REFUSED_INVALID_WORKFLOW", "terminal")
    transitions = []
    seen = set()
    for transition in definition["transitions"]:
        for key in TRANSITION_FIELDS:
            if key not in transition:
                raise OperatorRefusal("REFUSED_INVALID_WORKFLOW", key)
        if transition["from"] not in states or transition["to"] not in states:
            raise OperatorRefusal("REFUSED_INVALID_WORKFLOW", "transition state")
        key = (transition["from"], transition["event"])
        if key in seen:
            raise OperatorRefusal("REFUSED_INVALID_WORKFLOW", f"duplicate transition {key}")
        seen.add(key)
        transitions.append({"event": transition["event"], "from": transition["from"],
                            "to": transition["to"]})
    doc = {
        "schema": "oce.services.workflow_definition.v1",
        "id": definition["id"],
        "version": int(definition["version"]),
        "initial": definition["initial"],
        "states": states,
        "terminal": terminal,
        "transitions": sorted(transitions, key=lambda row: (row["from"], row["event"])),
    }
    doc["digest"] = object_digest(doc)
    return doc


def start_run(definition, run_id, now):
    """Start a run at the initial state of the frozen definition version."""
    return {
        "schema": "oce.services.workflow_run.v1",
        "run_id": run_id,
        "definition_id": definition["id"],
        "version": definition["version"],
        "state": definition["initial"],
        "cancelled": False,
        "lease": None,
        "history": [],
        "applied_events": [],
        "retries": 0,
    }


def acquire_lease(run, owner, now, ttl):
    """Acquire (or renew) the single active lease for a run."""
    if run["cancelled"]:
        raise OperatorRefusal("REFUSED_CANCELLED", run["run_id"])
    lease = run["lease"]
    if lease is not None and lease["owner"] != owner and int(now) < int(lease["expires_at"]):
        raise OperatorRefusal("REFUSED_LEASE_HELD", lease["owner"])
    updated = dict(run)
    updated["lease"] = {"owner": owner, "expires_at": int(now) + int(ttl)}
    return updated


def advance_run(definition, run, event_id, event, actor, now):
    """Advance a run along one legal transition, idempotent on a replayed event id."""
    if event_id in run["applied_events"]:
        return dict(run)
    if run["cancelled"]:
        raise OperatorRefusal("REFUSED_CANCELLED", run["run_id"])
    lease = run["lease"]
    if lease is None or lease["owner"] != actor or int(now) >= int(lease["expires_at"]):
        raise OperatorRefusal("REFUSED_LEASE_OWNER", run["run_id"])
    if run["state"] in definition["terminal"]:
        raise OperatorRefusal("REFUSED_ILLEGAL_TRANSITION", run["state"])
    target = None
    for transition in definition["transitions"]:
        if transition["from"] == run["state"] and transition["event"] == event:
            target = transition["to"]
            break
    if target is None:
        raise OperatorRefusal("REFUSED_ILLEGAL_TRANSITION", f"{run['state']}:{event}")
    updated = dict(run)
    updated["state"] = target
    updated["history"] = list(run["history"]) + [{"event_id": event_id, "event": event,
                                                  "from": run["state"], "to": target,
                                                  "at": int(now)}]
    updated["applied_events"] = list(run["applied_events"]) + [event_id]
    updated["lease"] = None
    return updated


def cancel_run(run, actor, now):
    """Cancel a run; cancellation is terminal and refuses any further advance."""
    updated = dict(run)
    updated["cancelled"] = True
    updated["lease"] = None
    updated["history"] = list(run["history"]) + [{"event_id": f"cancel:{actor}",
                                                  "event": "CANCEL", "from": run["state"],
                                                  "to": run["state"], "at": int(now)}]
    return updated


def retry_run(run, max_retries):
    """Record one retry, refusing once the frozen bound is exceeded."""
    if run["cancelled"]:
        raise OperatorRefusal("REFUSED_CANCELLED", run["run_id"])
    if int(run["retries"]) + 1 > int(max_retries):
        raise OperatorRefusal("REFUSED_RETRY_EXCEEDED", run["retries"])
    updated = dict(run)
    updated["retries"] = int(run["retries"]) + 1
    return updated
