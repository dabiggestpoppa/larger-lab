"""B2-R6: service-boundary authorization on read endpoints (audit gap 9).

The ControlPlaneAPI façade must not expose read endpoints without a valid
grant — permission checks happen at the service boundary, never only in
the UI. Health/readiness stay unauthenticated per the runtime contract.
Container-backed HTTP proof lives in test_http_api_integration.py.
"""
import sys
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "src"))


@pytest.fixture
def clock():
    from oce_control.clocks import TestClock, reset_clock, set_test_clock
    c = TestClock()
    set_test_clock(c)
    yield c
    reset_clock()


@pytest.fixture
def plane(clock):
    from oce_control.plane import ControlPlane
    return ControlPlane(test_clock=clock)


def _read_grant(plane, actor="po-test01"):
    return plane.authority.issue_grant(actor_id=actor, action="read", target="default")


def test_health_and_readiness_need_no_grant(plane):
    assert plane.api.health().ok
    assert plane.api.readiness().ok


def test_read_endpoints_denied_without_grant(plane):
    assert plane.api.inspect_job(grant_id="bogus", actor_id="attacker",
                                 job_id="j1").status == "denied"
    assert plane.api.list_schedules(grant_id="bogus", actor_id="attacker").status == "denied"
    assert plane.api.list_workers(grant_id="bogus", actor_id="attacker").status == "denied"
    assert plane.api.system_state(grant_id="bogus", actor_id="attacker").status == "denied"
    assert plane.api.audit_history(grant_id="bogus", actor_id="attacker").status == "denied"


def test_read_denials_are_recorded(plane):
    plane.api.system_state(grant_id="bogus", actor_id="attacker")
    denials = plane.authority.denials
    assert len(denials) >= 1
    assert denials[-1].requested_action == "system_state"


def test_read_endpoints_allowed_with_read_grant(plane):
    grant = _read_grant(plane)
    assert plane.api.inspect_job(grant_id=grant.grant_id, actor_id="po-test01",
                                 job_id="missing").status == "not_found"
    assert plane.api.list_schedules(grant_id=grant.grant_id,
                                    actor_id="po-test01").status == "success"
    assert plane.api.list_workers(grant_id=grant.grant_id,
                                  actor_id="po-test01").status == "success"
    assert plane.api.system_state(grant_id=grant.grant_id,
                                  actor_id="po-test01").status == "success"
    assert plane.api.audit_history(grant_id=grant.grant_id,
                                   actor_id="po-test01").status == "success"


def test_submit_grant_does_not_authorize_reads(plane):
    """A submit grant must not unlock read endpoints (least privilege)."""
    submit = plane.authority.issue_grant(actor_id="po-test01",
                                         action="submit_job", target="default")
    assert plane.api.system_state(grant_id=submit.grant_id,
                                  actor_id="po-test01").status == "denied"


def test_inspect_requires_read_grant_after_submit(plane):
    submit = plane.authority.issue_grant(actor_id="po-test01",
                                         action="submit_job", target="default")
    job = plane.api.submit_job(grant_id=submit.grant_id, actor_id="po-test01",
                               job_type="test_job", payload={"data": 1})
    assert job.ok
    # no read grant -> denied
    denied = plane.api.inspect_job(grant_id=submit.grant_id, actor_id="po-test01",
                                   job_id=job.data["job_id"])
    assert denied.status == "denied"
    # with read grant -> success
    read = _read_grant(plane)
    ok = plane.api.inspect_job(grant_id=read.grant_id, actor_id="po-test01",
                               job_id=job.data["job_id"])
    assert ok.status == "success"
    assert ok.data["job_id"] == job.data["job_id"]
