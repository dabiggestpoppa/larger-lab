"""
Phase 11.2-3B.4 — Timeline Exporter
=====================================
Exports temporal continuity ribbons.
"""

from __future__ import annotations

from . import export_json, export_csv, EXPORTS_BASE


def export_timeline(timeline_data: list[dict], label: str = "timeline") -> dict:
    """Export temporal continuity data."""
    results = {}
    results["json"] = export_json(timeline_data, "timelines", f"{label}.json")
    if timeline_data:
        results["csv"] = export_csv(timeline_data, "timelines", f"{label}.csv")
    return results
