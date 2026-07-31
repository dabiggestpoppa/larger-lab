"""
Phase 11.2-3B.4 — Visualization Export Layer
=============================================
Runtime → Export → Visualize (always this pipeline, never runtime → UI directly)

Exporters:
    topology_exporter   — Observer graph (nodes + edges)
    entropy_exporter    — Entropy states over time
    repair_exporter     — Repair propagation chains
    attractor_exporter  — Convergence regions
    routing_exporter    — Route deformation maps
    timeline_exporter   — Temporal continuity ribbons

Formats: JSON, CSV, graphml (no proprietary formats)
"""

from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]  # larger-lab/
EXPORTS_BASE = REPO_ROOT / "experiments" / "exports"


def _ensure_dir(subdir: str) -> Path:
    d = EXPORTS_BASE / subdir
    d.mkdir(parents=True, exist_ok=True)
    return d


def export_json(data: Any, subdir: str, filename: str) -> Path:
    """Export data as JSON."""
    path = _ensure_dir(subdir) / filename
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    return path


def export_csv(rows: list[dict], subdir: str, filename: str) -> Path:
    """Export data as CSV."""
    path = _ensure_dir(subdir) / filename
    if not rows:
        return path
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return path


def export_graphml(nodes: list[dict], edges: list[dict],
                   subdir: str, filename: str) -> Path:
    """Export as GraphML for tools like Gephi, Cytoscape."""
    path = _ensure_dir(subdir) / filename

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '  <key id="label" for="node" attr.name="label" attr.type="string"/>',
        '  <key id="type" for="node" attr.name="type" attr.type="string"/>',
        '  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>',
        '  <graph id="G" edgedefault="directed">',
    ]

    for node in nodes:
        nid = node.get("id", node.get("observer_id", "unknown"))
        label = node.get("label", node.get("type", nid))
        ntype = node.get("type", "unknown")
        xml_lines.append(f'    <node id="{nid}">')
        xml_lines.append(f'      <data key="label">{label}</data>')
        xml_lines.append(f'      <data key="type">{ntype}</data>')
        xml_lines.append(f'    </node>')

    for i, edge in enumerate(edges):
        src = edge.get("source", "unknown")
        tgt = edge.get("target", "unknown")
        weight = edge.get("weight", edge.get("frequency", 1))
        xml_lines.append(f'    <edge id="e{i}" source="{src}" target="{tgt}">')
        xml_lines.append(f'      <data key="weight">{weight}</data>')
        xml_lines.append(f'    </edge>')

    xml_lines.append('  </graph>')
    xml_lines.append('</graphml>')

    with open(path, "w") as f:
        f.write("\n".join(xml_lines))

    return path
