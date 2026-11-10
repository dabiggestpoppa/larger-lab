"""B6-I3 C2.S3 evidence reconciliation and deterministic sampling."""
from __future__ import annotations

import pytest

from oce.operator import OperatorRefusal, digest, reconcile_chain, sample_nodes
from oce.operator.evidence import STAGES


def chain():
    contents = {stage: f"{stage}-content".encode("utf-8") for stage in STAGES}
    manifest = {f"{stage}:1": {"sha256": digest(contents[stage]), "bytes": len(contents[stage])}
                for stage in STAGES}
    root = digest(b"manifest-root")
    nodes = []
    parent = root
    for stage in STAGES:
        node = {
            "stage": stage,
            "id": f"{stage}:1",
            "sha256": manifest[f"{stage}:1"]["sha256"],
            "bytes": manifest[f"{stage}:1"]["bytes"],
            "source": "builder",
            "parent": parent,
        }
        nodes.append(node)
        parent = node["sha256"]
    return nodes, manifest, {"builder", "ci"}, root


def test_chain_reconciles():
    nodes, manifest, sources, root = chain()
    doc = reconcile_chain(nodes, manifest, sources, root)
    assert doc["status"] == "RECONCILED"
    assert doc["node_count"] == 6
    assert doc["stages"] == list(STAGES)
    assert doc["digest"]


def test_digest_mismatch_refused():
    nodes, manifest, sources, root = chain()
    nodes[3]["sha256"] = digest(b"tampered")
    with pytest.raises(OperatorRefusal) as exc:
        reconcile_chain(nodes, manifest, sources, root)
    assert exc.value.code == "REFUSED_DIGEST"


def test_broken_link_refused():
    nodes, manifest, sources, root = chain()
    nodes[2]["parent"] = digest(b"wrong-parent")
    with pytest.raises(OperatorRefusal) as exc:
        reconcile_chain(nodes, manifest, sources, root)
    assert exc.value.code == "REFUSED_BROKEN_CHAIN"


def test_source_spoof_refused():
    nodes, manifest, sources, root = chain()
    nodes[4]["source"] = "intruder"
    with pytest.raises(OperatorRefusal) as exc:
        reconcile_chain(nodes, manifest, sources, root)
    assert exc.value.code == "REFUSED_SOURCE_SPOOF"


def test_unknown_node_refused():
    nodes, manifest, sources, root = chain()
    nodes[5]["id"] = "gate:ghost"
    with pytest.raises(OperatorRefusal) as exc:
        reconcile_chain(nodes, manifest, sources, root)
    assert exc.value.code == "REFUSED_UNKNOWN_NODE"


def test_deterministic_sample():
    nodes, _, _, root = chain()
    first = sample_nodes(nodes, root, 3)
    second = sample_nodes(list(reversed(nodes)), root, 3)
    assert first == second and len(first) == 3 and len(set(first)) == 3


def test_duplicate_node_refused():
    nodes, manifest, sources, root = chain()
    nodes[1]["id"] = nodes[0]["id"]
    nodes[1]["sha256"] = nodes[0]["sha256"]
    nodes[1]["bytes"] = nodes[0]["bytes"]
    with pytest.raises(OperatorRefusal) as exc:
        reconcile_chain(nodes, manifest, sources, root)
    assert exc.value.code == "REFUSED_BROKEN_CHAIN"
