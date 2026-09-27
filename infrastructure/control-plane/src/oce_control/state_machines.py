"""State machine definitions for OCE control plane entities.

B3.C3.S2 — legal states/transitions for jobs, grants, artifacts, deployments,
incidents, and strategies. Illegal transitions fail closed.
"""
from __future__ import annotations
from typing import Optional


# Job lifecycle states
JOB_STATES = [
    "pending", "scheduled", "leased", "running",
    "succeeded", "failed", "cancelled", "quarantined", "expired"
]

JOB_TRANSITIONS = {
    "pending": ["scheduled", "cancelled", "expired"],
    "scheduled": ["leased", "cancelled", "expired"],
    # leased -> pending: surrender/abandon returns the job for re-claim
    # (JobStore/PgJobStore surrender_lease and recover_abandoned_leases rely on it)
    "leased": ["pending", "running", "leased", "succeeded", "failed", "cancelled", "expired"],
    "running": ["succeeded", "failed", "cancelled", "quarantined"],
    "succeeded": [],
    "failed": ["pending", "cancelled", "quarantined"],
    "cancelled": [],
    "quarantined": ["pending", "cancelled"],
    "expired": [],
}

# Grant lifecycle states
GRANT_STATES = ["active", "revoked", "expired"]

GRANT_TRANSITIONS = {
    "active": ["revoked", "expired"],
    "revoked": [],
    "expired": [],
}

# Artifact lifecycle states
ARTIFACT_STATES = ["provisional", "verified", "promoted", "superseded", "quarantined"]

ARTIFACT_TRANSITIONS = {
    "provisional": ["verified", "quarantined"],
    "verified": ["promoted", "superseded", "quarantined"],
    "promoted": ["superseded"],
    "superseded": [],
    "quarantined": ["provisional", "verified"],
}

# Incident lifecycle states
INCIDENT_STATES = ["detected", "contained", "resolved", "learned"]

INCIDENT_TRANSITIONS = {
    "detected": ["contained"],
    "contained": ["resolved"],
    "resolved": ["learned"],
    "learned": [],
}


def is_valid_transition(entity_type: str, from_state: str, to_state: str) -> bool:
    """Check if a state transition is legal."""
    transitions_map = {
        "job": JOB_TRANSITIONS,
        "grant": GRANT_TRANSITIONS,
        "artifact": ARTIFACT_TRANSITIONS,
        "incident": INCIDENT_TRANSITIONS,
    }
    table = transitions_map.get(entity_type, {})
    return to_state in table.get(from_state, [])


def assert_transition(entity_type: str, from_state: str, to_state: str) -> None:
    """Assert a transition is legal, raise if not."""
    if not is_valid_transition(entity_type, from_state, to_state):
        raise ValueError(
            f"Illegal {entity_type} transition: {from_state} → {to_state}"
        )


def is_terminal(entity_type: str, state: str) -> bool:
    """Check if a state is terminal (no outgoing transitions)."""
    transitions_map = {
        "job": JOB_TRANSITIONS,
        "grant": GRANT_TRANSITIONS,
        "artifact": ARTIFACT_TRANSITIONS,
        "incident": INCIDENT_TRANSITIONS,
    }
    table = transitions_map.get(entity_type, {})
    return len(table.get(state, [])) == 0
