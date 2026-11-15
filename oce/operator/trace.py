"""End-to-end failure and cost trace across incident, identity, workflow and cost.

Composes the four B6-I4 surfaces into one governed trace. Each node names a real record, carries a
digest and links to the previous node, so a broken link, a cross-app owner or an unknown reference
is refused instead of inferred.
"""
from __future__ import annotations

from .model import OperatorRefusal, digest, object_digest

KINDS = ("incident", "identity", "workflow", "cost")
NODE_FIELDS = ("kind", "ref", "sha256", "parent")


def failure_cost_trace(nodes, registry, incidents, runs, cost_refs, app, root):
    """Verify an incident -> owner -> workflow -> cost trace end-to-end for one application."""
    if [node.get("kind") for node in nodes] != list(KINDS):
        raise OperatorRefusal("REFUSED_BROKEN_TRACE", "kind sequence incomplete")
    identities = (registry or {}).get("identities") or {}
    incident_index = {}
    for row in incidents:
        if row["id"] in incident_index:
            raise OperatorRefusal("REFUSED_DUPLICATE_INCIDENT", row["id"])
        incident_index[row["id"]] = row
    run_index = {row["run_id"]: row for row in runs}
    cost_index = set(cost_refs)
    previous = None
    seen = set()
    incident_owners = set()
    rows = []
    for node in nodes:
        for key in NODE_FIELDS:
            if key not in node:
                raise OperatorRefusal("REFUSED_INVALID_RECORD", key)
        if node["ref"] in seen:
            raise OperatorRefusal("REFUSED_BROKEN_TRACE", f"duplicate ref {node['ref']}")
        seen.add(node["ref"])
        if previous is None:
            if node["parent"] != root:
                raise OperatorRefusal("REFUSED_BROKEN_TRACE", "root link")
        elif node["parent"] != previous:
            raise OperatorRefusal("REFUSED_BROKEN_TRACE", node["ref"])
        if node["sha256"] != digest(f"{node['kind']}:{node['ref']}"):
            raise OperatorRefusal("REFUSED_BROKEN_TRACE", f"digest {node['ref']}")
        kind = node["kind"]
        if kind == "incident":
            incident = incident_index.get(node["ref"])
            if incident is None:
                raise OperatorRefusal("REFUSED_INVALID_RECORD", node["ref"])
            incident_owners = set(incident.get("owners") or [])
        elif kind == "identity":
            identity = identities.get(node["ref"])
            if identity is None:
                raise OperatorRefusal("REFUSED_UNKNOWN_IDENTITY", node["ref"])
            if identity["app"] != app:
                raise OperatorRefusal("REFUSED_CROSS_APP", f"{identity['app']} != {app}")
            if node["ref"] not in incident_owners:
                raise OperatorRefusal("REFUSED_UNOWNED_INCIDENT", node["ref"])
        elif kind == "workflow":
            run = run_index.get(node["ref"])
            if run is None:
                raise OperatorRefusal("REFUSED_INVALID_RECORD", f"unknown run {node['ref']}")
            if run["cancelled"]:
                raise OperatorRefusal("REFUSED_CANCELLED", node["ref"])
        elif kind == "cost":
            if node["ref"] not in cost_index:
                raise OperatorRefusal("REFUSED_INVALID_RECORD", f"unknown cost {node['ref']}")
        rows.append({key: node[key] for key in NODE_FIELDS})
        previous = node["sha256"]
    doc = {
        "schema": "oce.operator.failure_cost_trace.v1",
        "status": "TRACE_OK",
        "app": app,
        "root": root,
        "nodes": rows,
        "node_count": len(rows),
    }
    doc["digest"] = object_digest(doc)
    return doc
