"""
Phase 11.2-3B.4 — Topology Exporter
====================================
Exports observer graph for visualization.
"""

from __future__ import annotations

from pathlib import Path
from . import export_json, export_graphml, EXPORTS_BASE


def export_topology(graph_data: dict, label: str = "topology") -> dict[str, Path]:
    """Export observer graph in multiple formats."""
    nodes = [
        {"id": nid, "label": info.get("type", nid), "type": info.get("type", "unknown"),
         "state": info.get("state", "unknown"), "entropy": info.get("entropy", 0)}
        for nid, info in graph_data.get("nodes", {}).items()
    ]

    edges = [
        {"source": e["source"], "target": e["target"],
         "type": e.get("type", "unknown"), "weight": e.get("frequency", 1)}
        for e in graph_data.get("edges", [])
    ]

    results = {}
    results["json"] = export_json(graph_data, "topology", f"{label}.json")
    results["graphml"] = export_graphml(nodes, edges, "topology", f"{label}.graphml")

    return results
