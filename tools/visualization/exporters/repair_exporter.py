"""
Phase 11.2-3B.4 — Repair Exporter
===================================
Exports repair propagation chains.
"""

from __future__ import annotations

from . import export_json, export_csv, EXPORTS_BASE


def export_repair_chains(chains: list[list[dict]], label: str = "repair") -> dict:
    """Export repair chains for timeline visualization."""
    results = {}
    results["json"] = export_json(chains, "repair", f"{label}_chains.json")

    # Flatten for CSV
    flat = []
    for chain in chains:
        for event in chain:
            flat.append(event)
    if flat:
        results["csv"] = export_csv(flat, "repair", f"{label}_events.csv")

    return results
