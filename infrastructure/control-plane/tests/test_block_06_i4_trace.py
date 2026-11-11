"""B6-I4 end-to-end failure and cost trace across incident, identity, workflow and cost."""
from __future__ import annotations

import pytest

from oce.operator.model import OperatorRefusal, digest
from oce.operator.trace import failure_cost_trace
from oce.services.identity import identity_registry
from oce.services.workflow import acquire_lease, start_run

APP = "app-a"


def fixtures():
    incident = {"id": "INC-1", "severity": "SEV2", "impact": {"scope": "app"},
                "containment": [{"action": "rollback", "owner": "id:oncall", "at": 2}],
                "owners": ["id:oncall"], "timeline": [{"at": 1, "event": "detected"}],
                "recovery": "CONTAINED", "unresolved_risk": ["risk-1"]}
    registry = identity_registry([{"id": "id:oncall", "kind": "actor", "app": APP,
                                   "credential_reference": {"id": "cr-1", "kind": "token",
                                                            "rotated_at": 0, "revoked": False}}])
    run = start_run({"id": "wf", "version": 1, "initial": "new", "states": ["new", "done"],
                     "transitions": [{"event": "go", "from": "new", "to": "done"}],
                     "terminal": ["done"]}, "run-1", 0)
    run = acquire_lease(run, "id:oncall", 0, 10)
    return incident, registry, run, ["cost-1"]


def build_nodes(root, override=None):
    nodes = []
    parent = root
    for kind, ref in (("incident", "INC-1"), ("identity", "id:oncall"),
                      ("workflow", "run-1"), ("cost", "cost-1")):
        node = {"kind": kind, "ref": ref, "sha256": digest(f"{kind}:{ref}"), "parent": parent}
        nodes.append(node)
        parent = node["sha256"]
    if override:
        override(nodes)
    return nodes


def test_trace_end_to_end_ok():
    incident, registry, run, cost_refs = fixtures()
    root = digest(b"trace-root")
    doc = failure_cost_trace(build_nodes(root), registry, [incident], [run], cost_refs, APP, root)
    assert doc["status"] == "TRACE_OK" and doc["node_count"] == 4 and doc["digest"]


def test_trace_broken_link_refused():
    incident, registry, run, cost_refs = fixtures()
    root = digest(b"trace-root")
    nodes = build_nodes(root)
    nodes[2]["parent"] = digest(b"wrong-parent")
    with pytest.raises(OperatorRefusal) as exc:
        failure_cost_trace(nodes, registry, [incident], [run], cost_refs, APP, root)
    assert exc.value.code == "REFUSED_BROKEN_TRACE"


def test_trace_cross_app_refused():
    incident, registry, run, cost_refs = fixtures()
    root = digest(b"trace-root")
    with pytest.raises(OperatorRefusal) as exc:
        failure_cost_trace(build_nodes(root), registry, [incident], [run], cost_refs, "app-b", root)
    assert exc.value.code == "REFUSED_CROSS_APP"
