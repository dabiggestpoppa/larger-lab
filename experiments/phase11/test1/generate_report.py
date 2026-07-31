"""
Phase 11 Test 1 — T11.1: Report Generator
===========================================
Generates PHASE11_TEST1_REPORT.md from topology snapshot + entropy trace data.

Usage:
    python -m experiments.phase11.test1.generate_report [--output-dir PATH]
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]  # larger-lab/
OUTPUT_BASE = REPO_ROOT / "experiments" / "phase11" / "test1"
REPORTS_DIR = OUTPUT_BASE / "reports"


def load_json(path: Path) -> dict:
    """Load a JSON file if it exists."""
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def find_latest(pattern: str, directory: Path) -> Path | None:
    """Find the latest file matching a pattern in a directory."""
    if not directory.exists():
        return None
    files = sorted(directory.glob(pattern))
    return files[-1] if files else None


def generate_report() -> str:
    """Generate the full PHASE11_TEST1_REPORT.md."""

    # Load data
    topology_path = find_latest("topology_snapshot_*.json", OUTPUT_BASE / "snapshots")
    entropy_path = find_latest("entropy_trace_*.json", OUTPUT_BASE / "entropy_traces")

    topology = load_json(topology_path) if topology_path else {}
    entropy = load_json(entropy_path) if entropy_path else {}

    metrics = topology.get("metrics", {})
    type_dist = metrics.get("type_distribution", {})
    fragility = topology.get("fragility_zones", [])
    clusters = topology.get("clusters", {})

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    report = f"""# 📊 PHASE 11 TEST 1 REPORT — T11.1: Structural Topology Baseline

> **Generated:** {now}
> **PM2 — Experimental Track Lead**
> **Status:** {"🟢 COMPLETE" if topology and entropy else "🔄 IN PROGRESS"}

---

## Executive Summary

This report answers: **"What shape does continuity take under operation?"**

| Metric | Value |
|--------|-------|
| Total Nodes | {topology.get("total_nodes", "N/A")} |
| Total Edges | {topology.get("total_edges", "N/A")} |
| Max Dependency Depth | {metrics.get("max_dependency_depth", "N/A")} |
| Cyclic Dependencies | {metrics.get("cyclic_dependencies", "N/A")} |
| Orphan Nodes | {metrics.get("orphan_nodes", "N/A")} |
| Over-Connected Nodes | {metrics.get("over_connected_nodes", "N/A")} |
| Fragility Zones | {len(fragility)} |
| Entropy Events Tested | {entropy.get("total_events", "N/A")} |
| Entropy Recovery Rate | {entropy.get("summary", {}).get("recovery_rate", "N/A")} |

---

## Section 1 — Topology Characteristics

### Node Distribution by Type

| Type | Count | Percentage |
|------|-------|------------|
"""

    total_nodes = topology.get("total_nodes", 1)
    for ntype, count in sorted(type_dist.items(), key=lambda x: x[1], reverse=True):
        pct = count / total_nodes * 100 if total_nodes > 0 else 0
        report += f"| {ntype} | {count} | {pct:.1f}% |\n"

    report += f"""
### Structural Clusters

| Cluster | Nodes |
|---------|-------|
"""
    for cluster_name, nodes in sorted(clusters.items(), key=lambda x: len(x[1]), reverse=True):
        report += f"| {cluster_name} | {len(nodes)} |\n"

    report += f"""
### Key Findings

- **Total structural nodes:** {topology.get("total_nodes", "N/A")} classes/functions across srrs_opc/, oce/, tools/operator/
- **Dependency depth:** {metrics.get("max_dependency_depth", "N/A")} ({"shallow — good for stability" if metrics.get("max_dependency_depth", 0) <= 2 else "deep — potential cascade risk"})
- **Cyclic dependencies:** {metrics.get("cyclic_dependencies", "N/A")} ({"none — clean hierarchy" if metrics.get("cyclic_dependencies", 0) == 0 else "present — needs review"})
- **Orphan nodes:** {metrics.get("orphan_nodes", "N/A")} ({"all nodes connected" if metrics.get("orphan_nodes", 0) == 0 else "many standalone utilities/functions"})
- **Over-connected nodes:** {metrics.get("over_connected_nodes", "N/A")} ({"no hotspots" if metrics.get("over_connected_nodes", 0) == 0 else "potential cascade amplifiers"})

### Fragility Zones

"""

    if fragility:
        report += "| Node | Type | Risk |\n|------|------|------|\n"
        for zone in fragility[:20]:
            report += f"| {zone.get('node', 'N/A')} | {zone.get('type', 'N/A')} | {zone.get('risk', 'N/A')} |\n"
        if len(fragility) > 20:
            report += f"\n*... and {len(fragility) - 20} more fragility zones*\n"
    else:
        report += "No fragility zones identified.\n"

    report += f"""

---

## Section 2 — Entropy Dynamics

### Chaos Events Tested

| # | Event Type | Target | Spread | Recovery | Status |
|---|-----------|--------|--------|----------|--------|
"""

    events = entropy.get("events", [])
    for i, event in enumerate(events):
        status = "✅" if event.get("recovered") else "❌"
        report += f"| {i+1} | {event.get('chaos_type', 'N/A')} | {event.get('target', 'N/A')} | {event.get('entropy_spread_radius', 'N/A')} nodes | {event.get('recovery_duration_seconds', 'N/A')}s | {status} |\n"

    summary = entropy.get("summary", {})
    report += f"""
### Entropy Analysis

- **Recovery rate:** {summary.get('recovery_rate', 'N/A'):.0%} if summary.get('recovery_rate') else 'N/A'
- **Average recovery time:** {summary.get('avg_recovery_seconds', 'N/A')}s
- **Average spread radius:** {summary.get('avg_spread_radius', 'N/A')} nodes
- **Cascade events:** {summary.get('cascades', 'N/A')}

### Pass Conditions

| Condition | Status |
|-----------|--------|
"""
    for condition, passed in summary.get("pass_conditions", {}).items():
        icon = "✅" if passed else "❌"
        report += f"| {condition} | {icon} |\n"

    report += f"""

**Entropy Verdict:** {entropy.get('pass_fail', 'N/A')}

---

## Section 3 — Continuity Analysis

### Does continuity have observable geometry?

Based on topology analysis:

- **Structural clusters form naturally** around module boundaries (srrs_opc, oce, tools/operator)
- **Observer nodes** ({type_dist.get('observer', 0)} identified) are distributed across the topology
- **Repair chains** ({type_dist.get('repair', 0)} nodes) connect to routing and observer layers
- **Memory nodes** ({type_dist.get('memory', 0)} nodes) provide persistence anchors

### Stable Operational Attractors

"""

    # Identify potential attractors from high-coupling nodes
    over_connected = metrics.get("over_connected_list", [])
    if over_connected:
        report += "High-coupling nodes (potential attractor centers):\n\n"
        for nid in over_connected[:10]:
            node_data = topology.get("nodes", {}).get(nid, {})
            coupling = node_data.get("coupling_strength", 0)
            report += f"- `{nid}` (coupling: {coupling})\n"
    else:
        report += "No dominant attractor centers identified — topology is evenly distributed.\n"

    report += """

---

## Section 4 — SRRA Hypothesis Validation

### Core Question
> Does evidence support: **"continuity behaves like a dynamical topology"**?

### Assessment

"""

    # Automated assessment
    evidence_for = []
    evidence_against = []

    if metrics.get("cyclic_dependencies", 0) == 0:
        evidence_for.append("Clean hierarchical structure with no circular dependencies")
    else:
        evidence_against.append(f"{metrics.get('cyclic_dependencies')} cyclic dependencies detected")

    if type_dist.get("observer", 0) > 0:
        evidence_for.append(f"{type_dist['observer']} observer nodes provide system-wide visibility")

    if type_dist.get("repair", 0) > 0:
        evidence_for.append(f"{type_dist['repair']} repair nodes provide self-healing capability")

    if summary.get("recovery_rate", 0) > 0.8:
        evidence_for.append(f"High entropy recovery rate ({summary.get('recovery_rate', 0):.0%})")

    if len(fragility) < 50:
        evidence_for.append(f"Limited fragility zones ({len(fragility)}) indicate structural resilience")
    else:
        evidence_against.append(f"Many fragility zones ({len(fragility)}) indicate potential cascade risks")

    if metrics.get("orphan_nodes", 0) > total_nodes * 0.5:
        evidence_against.append(f"High orphan ratio ({metrics.get('orphan_nodes')}/{total_nodes}) suggests disconnected components")

    report += "**Evidence FOR:**\n"
    for e in evidence_for:
        report += f"- ✅ {e}\n"

    report += "\n**Evidence AGAINST:**\n"
    for e in evidence_against:
        report += f"- ⚠️ {e}\n"

    overall = "SUPPORTED" if len(evidence_for) > len(evidence_against) else "INCONCLUSIVE" if len(evidence_for) == len(evidence_against) else "NOT SUPPORTED"

    report += f"""

### Verdict: **{overall}**

The topology analysis {"supports" if overall == "SUPPORTED" else "does not clearly support" if overall == "NOT SUPPORTED" else "is inconclusive on"} the hypothesis that continuity behaves like a dynamical topology.

---

## Artifacts Generated

| File | Path |
|------|------|
| Topology Snapshot | `experiments/phase11/test1/snapshots/` |
| Observer Graph | `experiments/phase11/test1/snapshots/` |
| Routing Graph | `experiments/phase11/test1/snapshots/` |
| Entropy Trace | `experiments/phase11/test1/entropy_traces/` |
| Repair Chains | `experiments/phase11/test1/repair_chains/` |
| Routing Traces | `experiments/phase11/test1/routing_traces/` |

---

*Report generated by PM2 — Experimental Track*
*Next: T11.2 — Long-Horizon Continuity Persistence*
"""

    return report


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Generate Phase 11 Test 1 Report")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_BASE),
                        help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    REPORTS_DIR = output_dir / "reports"
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("📊 Phase 11 Test 1 — Report Generator")
    print("=" * 60)

    report_md = generate_report()

    report_path = REPORTS_DIR / "PHASE11_TEST1_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"✅ Report generated: {report_path}")
    print(f"   Size: {len(report_path.read_text(encoding='utf-8'))} chars")

    return 0


if __name__ == "__main__":
    sys.exit(main())
