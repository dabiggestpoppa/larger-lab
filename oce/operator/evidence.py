"""C2.S3 evidence explorer: reconcile intent to plan to task to artifact to evaluation to gate."""
from __future__ import annotations

from .model import OperatorRefusal, digest, object_digest

STAGES = ("intent", "plan", "task", "artifact", "evaluation", "gate")
NODE_FIELDS = ("id", "stage", "sha256", "bytes", "source", "parent")


def reconcile_chain(nodes, manifest, sources, root=None):
    """Verify every node against the immutable manifest and the parent chain."""
    if [node.get("stage") for node in nodes] != list(STAGES):
        raise OperatorRefusal("REFUSED_BROKEN_CHAIN", "stage sequence incomplete")
    allowed_sources = set(sources)
    previous = None
    rows = []
    for node in nodes:
        for key in NODE_FIELDS:
            if key not in node:
                raise OperatorRefusal("REFUSED_INVALID_RECORD", key)
        entry = manifest.get(node["id"])
        if entry is None:
            raise OperatorRefusal("REFUSED_UNKNOWN_NODE", node["id"])
        if entry.get("sha256") != node["sha256"] or int(entry.get("bytes", -1)) != int(node["bytes"]):
            raise OperatorRefusal("REFUSED_DIGEST", node["id"])
        if node["source"] not in allowed_sources:
            raise OperatorRefusal("REFUSED_SOURCE_SPOOF", node["source"])
        if previous is not None and node["parent"] != previous:
            raise OperatorRefusal("REFUSED_BROKEN_CHAIN", node["id"])
        if previous is None and root is not None and node["parent"] != root:
            raise OperatorRefusal("REFUSED_BROKEN_CHAIN", node["id"])
        rows.append({key: node[key] for key in NODE_FIELDS})
        previous = node["sha256"]
    doc = {
        "schema": "oce.operator.evidence_reconciliation.v1",
        "status": "RECONCILED",
        "root": root,
        "nodes": rows,
        "node_count": len(rows),
        "stages": list(STAGES),
    }
    doc["digest"] = object_digest(doc)
    return doc


def sample_nodes(nodes, manifest_digest, k):
    """Deterministically select k nodes, independent of input order and never random."""
    if not 0 < int(k) <= len(nodes):
        raise OperatorRefusal("REFUSED_INVALID_RECORD", "sample size")
    ranked = sorted(nodes, key=lambda node: digest(f"{manifest_digest}:{node['id']}"))
    return [node["id"] for node in ranked[: int(k)]]
