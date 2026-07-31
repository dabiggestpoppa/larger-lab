"""
Phase 11.2-3B.4 — Routing Exporter
====================================
Exports route deformation maps.
"""

from __future__ import annotations

from . import export_json, export_csv, EXPORTS_BASE


def export_routing_map(routing_data: dict, label: str = "routing") -> dict:
    """Export routing deformation data."""
    results = {}
    results["json"] = export_json(routing_data, "routing", f"{label}_map.json")

    # Flatten route shifts for CSV
    shifts = routing_data.get("shifts", [])
    if shifts:
        results["csv"] = export_csv(shifts, "routing", f"{label}_shifts.csv")

    return results
