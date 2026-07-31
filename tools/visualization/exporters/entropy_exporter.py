"""
Phase 11.2-3B.4 — Entropy Exporter
====================================
Exports entropy states and heatmaps.
"""

from __future__ import annotations

from . import export_json, export_csv, EXPORTS_BASE


def export_entropy_timeseries(timeseries: list[dict], label: str = "entropy") -> dict:
    """Export entropy over time."""
    results = {}
    results["json"] = export_json(timeseries, "entropy", f"{label}_timeseries.json")
    results["csv"] = export_csv(timeseries, "entropy", f"{label}_timeseries.csv")
    return results


def export_entropy_heatmap(node_entropy: dict[str, float], label: str = "entropy") -> Path:
    """Export per-node entropy as heatmap data."""
    data = [
        {"node": node, "entropy": entropy}
        for node, entropy in sorted(node_entropy.items(), key=lambda x: x[1], reverse=True)
    ]
    return export_json(data, "entropy", f"{label}_heatmap.json")
