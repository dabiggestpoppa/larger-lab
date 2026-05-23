"""
Phase 11.2-3B.4 — Attractor Exporter
======================================
Exports convergence regions and attractor maps.
"""

from __future__ import annotations

from . import export_json, export_graphml, EXPORTS_BASE


def export_attractor_map(attractor_data: dict, label: str = "attractor") -> dict:
    """Export attractor regions and field resonance."""
    results = {}
    results["json"] = export_json(attractor_data, "attractors", f"{label}_map.json")

    # Export basins as graph if nodes/edges present
    if "basins" in attractor_data:
        basins = attractor_data["basins"]
        nodes = [{"id": b["id"], "label": b.get("label", b["id"]),
                  "type": "basin", "stability": b.get("stability", 0)}
                 for b in basins]
        edges = [{"source": b["id"], "target": r["target"],
                  "weight": r.get("transition_probability", 0)}
                 for b in basins for r in b.get("transitions", [])]
        if nodes and edges:
            results["graphml"] = export_graphml(nodes, edges, "attractors",
                                                 f"{label}_basins.graphml")

    return results
