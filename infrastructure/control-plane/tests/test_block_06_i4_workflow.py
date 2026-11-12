"""B6-I4 C3.S2 workflow state machine, leases, replay, cancellation and retries."""
from __future__ import annotations

import pytest

from oce.operator.model import OperatorRefusal
from oce.services.workflow import (
    acquire_lease,
    advance_run,
    cancel_run,
    define_workflow,
    retry_run,
    start_run,
)

DEFINITION = {
    "id": "wf.deploy",
    "version": 3,
    "initial": "new",
    "states": ["new", "running", "done"],
    "transitions": [{"event": "go", "from": "new", "to": "running"},
                    {"event": "finish", "from": "running", "to": "done"}],
    "terminal": ["done"],
}


def workflow():
    return define_workflow(DEFINITION)


def running(owner="id:op"):
    run = start_run(workflow(), "run-1", 0)
    return acquire_lease(run, owner, 0, 10)


def test_definition_versioned_and_valid():
    doc = workflow()
    assert doc["version"] == 3 and doc["initial"] == "new"
    assert doc["digest"]
    with pytest.raises(OperatorRefusal) as exc:
        define_workflow({**DEFINITION, "transitions": [
            {"event": "go", "from": "new", "to": "ghost"}]})
    assert exc.value.code == "REFUSED_INVALID_WORKFLOW"


def test_illegal_transition_refused():
    doc = workflow()
    run = running()
    with pytest.raises(OperatorRefusal) as exc:
        advance_run(doc, run, "e0", "finish", "id:op", 1)
    assert exc.value.code == "REFUSED_ILLEGAL_TRANSITION"


def test_lease_owner_required():
    doc = workflow()
    run = start_run(doc, "run-1", 0)
    with pytest.raises(OperatorRefusal) as exc:
        advance_run(doc, run, "e1", "go", "id:op", 1)
    assert exc.value.code == "REFUSED_LEASE_OWNER"


def test_lease_reacquire_after_expiry():
    with pytest.raises(OperatorRefusal) as exc:
        acquire_lease(running("id:op"), "id:other", 5, 10)
    assert exc.value.code == "REFUSED_LEASE_HELD"
    renewed = acquire_lease(running("id:op"), "id:other", 20, 10)
    assert renewed["lease"]["owner"] == "id:other"


def test_replay_preserves_state():
    doc = workflow()
    run = running()
    once = advance_run(doc, run, "e1", "go", "id:op", 1)
    twice = advance_run(doc, once, "e1", "go", "id:op", 2)
    assert once["state"] == "running" == twice["state"]
    assert twice["history"] == once["history"]
    assert len(once["applied_events"]) == 1


def test_cancelled_run_advance_refused():
    doc = workflow()
    run = cancel_run(running(), "id:op", 2)
    assert run["cancelled"] is True and run["lease"] is None
    with pytest.raises(OperatorRefusal) as exc:
        advance_run(doc, run, "e1", "go", "id:op", 3)
    assert exc.value.code == "REFUSED_CANCELLED"


def test_retry_bounded():
    run = running()
    once = retry_run(run, 1)
    assert once["retries"] == 1
    with pytest.raises(OperatorRefusal) as exc:
        retry_run(once, 1)
    assert exc.value.code == "REFUSED_RETRY_EXCEEDED"


def test_advance_definition_mismatch_refused():
    v1 = define_workflow({**DEFINITION, "version": 1})
    v2 = define_workflow({**DEFINITION, "version": 2})
    run = acquire_lease(start_run(v1, "run-1", 0), "id:op", 0, 10)
    with pytest.raises(OperatorRefusal) as exc:
        advance_run(v2, run, "e1", "go", "id:op", 1)
    assert exc.value.code == "REFUSED_WORKFLOW_MISMATCH"
    assert run["state"] == "new" and run["applied_events"] == [] and run["history"] == []
    other = define_workflow({**DEFINITION, "id": "wf.other"})
    with pytest.raises(OperatorRefusal) as exc:
        advance_run(other, run, "e1", "go", "id:op", 1)
    assert exc.value.code == "REFUSED_WORKFLOW_MISMATCH"
