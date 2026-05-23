"""
Phase 11 Test 1 — T11.1: Structural Topology Baseline
======================================================
Extracts structural graph of the SRRA+OPH system:
- Observer interactions
- Repair chains
- Routing dependencies
- Continuity structure
- Entropy propagation paths

This is PURE OBSERVATION — does NOT modify runtime behavior.

Outputs:
    experiments/phase11/test1/snapshots/topology_snapshot_001.json
    experiments/phase11/test1/snapshots/observer_graph_001.json
    experiments/phase11/test1/snapshots/routing_graph_001.json

Usage:
    python -m experiments.codegraph.topology_snapshot [--output-dir PATH] [--label LABEL]
"""

from __future__ import annotations

import ast
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── Configuration ───────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[2]  # larger-lab/
SRRA_ROOT = REPO_ROOT / "srrs_opc"
OCE_ROOT = REPO_ROOT / "oce"
TOOLS_ROOT = REPO_ROOT / "tools" / "operator"

SCAN_DIRS = {
    "srrs_opc": SRRA_ROOT,
    "oce": OCE_ROOT,
    "tools/operator": TOOLS_ROOT,
}

OUTPUT_BASE = REPO_ROOT / "experiments" / "phase11" / "test1" / "snapshots"

# ─── Data Structures ────────────────────────────────────────────────────────

@dataclass
class CodeNode:
    """Represents a single node in the topology graph."""
    id: str
    name: str
    module: str
    node_type: str  # "observer", "router", "repair", "memory", "field", "signal", "other"
    file_path: str
    line_number: int
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    entropy_sensitivity: float = 0.0  # 0.0-1.0, estimated from error handling density
    coupling_strength: float = 0.0  # estimated from import frequency
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TopologyGraph:
    """Complete topology snapshot of the system."""
    label: str
    timestamp: str
    total_nodes: int = 0
    total_edges: int = 0
    nodes: dict[str, dict] = field(default_factory=dict)
    edges: list[dict] = field(default_factory=list)
    clusters: dict[str, list[str]] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    fragility_zones: list[dict] = field(default_factory=dict)


# ─── Node Type Classifier ───────────────────────────────────────────────────

OBSERVER_KEYWORDS = {"observer", "monitor", "watch", "detect", "sense", "probe", "track"}
ROUTER_KEYWORDS = {"router", "route", "dispatch", "forward", "relay", "channel"}
REPAIR_KEYWORDS = {"repair", "fix", "recover", "restore", "heal", "patch", "rebuild"}
MEMORY_KEYWORDS = {"memory", "store", "cache", "state", "persist", "anchor", "checkpoint"}
FIELD_KEYWORDS = {"field", "resonance", "topology", "manifold", "attractor", "coherence"}
SIGNAL_KEYWORDS = {"signal", "event", "message", "packet", "pulse", "wave"}


def classify_node(name: str, file_path: str) -> str:
    """Classify a code node by its name and file path."""
    combined = f"{name} {file_path}".lower()

    scores = {
        "observer": sum(1 for kw in OBSERVER_KEYWORDS if kw in combined),
        "router": sum(1 for kw in ROUTER_KEYWORDS if kw in combined),
        "repair": sum(1 for kw in REPAIR_KEYWORDS if kw in combined),
        "memory": sum(1 for kw in MEMORY_KEYWORDS if kw in combined),
        "field": sum(1 for kw in FIELD_KEYWORDS if kw in combined),
        "signal": sum(1 for kw in SIGNAL_KEYWORDS if kw in combined),
    }

    best_type = max(scores, key=scores.get)
    return best_type if scores[best_type] > 0 else "other"


# ─── AST-based Topology Extractor ───────────────────────────────────────────

class TopologyExtractor:
    """Extracts topology from Python source files using AST."""

    def __init__(self, scan_dirs: dict[str, Path]):
        self.scan_dirs = scan_dirs
        self.nodes: dict[str, CodeNode] = {}
        self.edges: list[dict] = []
        self._import_map: dict[str, list[str]] = {}  # module -> [imported_modules]

    def extract(self) -> TopologyGraph:
        """Run full topology extraction."""
        self._scan_files()
        self._resolve_dependencies()
        self._compute_metrics()

        graph = TopologyGraph(
            label=f"topology_snapshot_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        graph.nodes = {nid: asdict(node) for nid, node in self.nodes.items()}
        graph.edges = self.edges
        graph.total_nodes = len(self.nodes)
        graph.total_edges = len(self.edges)
        graph.clusters = self._detect_clusters()
        graph.metrics = self._compute_graph_metrics()
        graph.fragility_zones = self._identify_fragility_zones()

        return graph

    def _scan_files(self):
        """Scan all Python files in target directories."""
        for label, dir_path in self.scan_dirs.items():
            if not dir_path.exists():
                print(f"  [WARN] Directory not found: {dir_path}")
                continue

            for py_file in sorted(dir_path.rglob("*.py")):
                if py_file.name.startswith("test_") or py_file.name == "__init__.py":
                    continue
                self._parse_file(py_file, label)

    def _parse_file(self, file_path: Path, module_label: str):
        """Parse a single Python file and extract nodes."""
        try:
            source = file_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"  [WARN] Could not parse {file_path}: {e}")
            return

        rel_path = str(file_path.relative_to(REPO_ROOT))
        module_name = rel_path.replace(os.sep, ".").replace(".py", "")

        # Extract classes
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                node_id = f"{module_name}.{node.name}"
                node_type = classify_node(node.name, rel_path)
                code_node = CodeNode(
                    id=node_id,
                    name=node.name,
                    module=module_label,
                    node_type=node_type,
                    file_path=rel_path,
                    line_number=node.lineno,
                )

                # Extract base classes as dependencies
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        code_node.dependencies.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        code_node.dependencies.append(base.attr)

                # Estimate entropy sensitivity from try/except density
                try_count = sum(1 for _ in ast.walk(node) if isinstance(_, ast.Try))
                total_methods = sum(1 for _ in ast.walk(node) if isinstance(_, (ast.FunctionDef, ast.AsyncFunctionDef)))
                if total_methods > 0:
                    code_node.entropy_sensitivity = min(1.0, try_count / total_methods)

                self.nodes[node_id] = code_node

            elif isinstance(node, ast.FunctionDef) and node.col_offset == 0:
                # Top-level functions
                node_id = f"{module_name}.{node.name}"
                node_type = classify_node(node.name, rel_path)
                code_node = CodeNode(
                    id=node_id,
                    name=node.name,
                    module=module_label,
                    node_type=node_type,
                    file_path=rel_path,
                    line_number=node.lineno,
                )
                self.nodes[node_id] = code_node

        # Extract imports
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        self._import_map[module_name] = imports

    def _resolve_dependencies(self):
        """Resolve cross-module dependencies from AST analysis."""
        # Build name -> node_id index for fast lookup
        name_to_nodes: dict[str, list[str]] = {}
        for node_id, node in self.nodes.items():
            name_to_nodes.setdefault(node.name, []).append(node_id)
            name_to_nodes.setdefault(node.name.lower(), []).append(node_id)

        # Resolve inheritance dependencies (from AST base classes)
        for node_id, node in self.nodes.items():
            resolved_deps = []
            for dep_name in node.dependencies:
                # Match by exact name or lowercase
                matches = name_to_nodes.get(dep_name, []) or name_to_nodes.get(dep_name.lower(), [])
                for match_id in matches:
                    if match_id != node_id and match_id not in resolved_deps:
                        resolved_deps.append(match_id)
                        # Add bidirectional link
                        if node_id not in self.nodes[match_id].dependents:
                            self.nodes[match_id].dependents.append(node_id)
                        self.edges.append({
                            "source": node_id,
                            "target": match_id,
                            "type": "inheritance",
                        })
            node.dependencies = resolved_deps

        # Resolve import-based edges (only within scanned modules)
        for module_name, imports in self._import_map.items():
            # Find nodes in this module
            module_nodes = [nid for nid, n in self.nodes.items() if module_name in n.file_path]
            for imp in imports:
                # Only create edges for imports that match scanned modules
                for other_id, other_node in self.nodes.items():
                    other_module = other_node.file_path.replace("/", ".").replace(".py", "")
                    if other_module.endswith(imp) or imp.endswith(other_module.split(".")[-1]):
                        for nid in module_nodes:
                            if nid != other_id:
                                self.edges.append({
                                    "source": nid,
                                    "target": other_id,
                                    "type": "import",
                                })

    def _compute_metrics(self):
        """Compute coupling strength for each node."""
        for node_id, node in self.nodes.items():
            # Coupling = number of unique connections / total possible
            unique_connections = len(set(node.dependencies + node.dependents))
            total_nodes = len(self.nodes)
            if total_nodes > 1:
                node.coupling_strength = round(unique_connections / (total_nodes - 1), 4)

    def _detect_clusters(self) -> dict[str, list[str]]:
        """Detect node clusters by module and type."""
        clusters: dict[str, list[str]] = {}
        for node_id, node in self.nodes.items():
            # Cluster by module
            module_key = f"module:{node.module}"
            clusters.setdefault(module_key, []).append(node_id)

            # Cluster by type
            type_key = f"type:{node.node_type}"
            clusters.setdefault(type_key, []).append(node_id)

        return clusters

    def _compute_graph_metrics(self) -> dict[str, Any]:
        """Compute overall graph metrics."""
        if not self.nodes:
            return {"error": "no_nodes_found"}

        # Dependency depth (longest chain)
        max_depth = 0
        for node_id in self.nodes:
            depth = self._depth_from(node_id, set())
            max_depth = max(max_depth, depth)

        # Cyclic dependencies
        cycles = self._find_cycles()

        # Orphan nodes (no connections)
        orphans = [
            nid for nid, n in self.nodes.items()
            if not n.dependencies and not n.dependents
        ]

        # Over-connected nodes (>2 std devs above mean coupling)
        couplings = [n.coupling_strength for n in self.nodes.values()]
        mean_coupling = sum(couplings) / len(couplings) if couplings else 0
        std_coupling = (sum((c - mean_coupling) ** 2 for c in couplings) / len(couplings)) ** 0.5 if couplings else 0
        over_connected = [
            nid for nid, n in self.nodes.items()
            if n.coupling_strength > mean_coupling + 2 * std_coupling
        ]

        # Type distribution
        type_dist: dict[str, int] = {}
        for n in self.nodes.values():
            type_dist[n.node_type] = type_dist.get(n.node_type, 0) + 1

        # Entropy sensitivity distribution
        entropy_nodes = sorted(
            [(nid, n.entropy_sensitivity) for nid, n in self.nodes.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "max_dependency_depth": max_depth,
            "cyclic_dependencies": len(cycles),
            "orphan_nodes": len(orphans),
            "over_connected_nodes": len(over_connected),
            "mean_coupling_strength": round(mean_coupling, 4),
            "type_distribution": type_dist,
            "top_entropy_sensitive": entropy_nodes,
            "cycles": cycles[:5],  # First 5 cycles
            "orphan_list": orphans[:10],
            "over_connected_list": over_connected[:10],
        }

    def _find_cycles(self) -> list[list[str]]:
        """Find cyclic dependencies using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node_id: str, path: list[str]):
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            node = self.nodes.get(node_id)
            if node:
                for dep in node.dependencies:
                    if dep not in visited:
                        dfs(dep, path.copy())
                    elif dep in rec_stack:
                        cycle_start = path.index(dep) if dep in path else -1
                        if cycle_start >= 0:
                            cycles.append(path[cycle_start:] + [dep])

            rec_stack.discard(node_id)

        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id, [])

        return cycles

    def _depth_from(self, node_id: str, visited: set[str]) -> int:
        """Compute max dependency depth from a node."""
        if node_id in visited:
            return 0
        visited.add(node_id)

        node = self.nodes.get(node_id)
        if not node or not node.dependencies:
            return 0

        max_child = 0
        for dep in node.dependencies:
            if dep in self.nodes:
                max_child = max(max_child, 1 + self._depth_from(dep, visited.copy()))

        return max_child

    def _identify_fragility_zones(self) -> list[dict]:
        """Identify potentially fragile areas of the topology."""
        zones = []

        # High coupling + high entropy sensitivity = fragile
        for node_id, node in self.nodes.items():
            if node.coupling_strength > 0.3 and node.entropy_sensitivity > 0.5:
                zones.append({
                    "node": node_id,
                    "type": "high_coupling_high_entropy",
                    "coupling": node.coupling_strength,
                    "entropy": node.entropy_sensitivity,
                    "risk": "cascade_failure",
                })

        # Orphan observers = blind spots
        for node_id, node in self.nodes.items():
            if node.node_type == "observer" and not node.dependents:
                zones.append({
                    "node": node_id,
                    "type": "orphan_observer",
                    "risk": "unmonitored_failure",
                })

        return zones


# ─── Main Entry Point ───────────────────────────────────────────────────────

def main():
    """Run topology snapshot extraction."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract structural topology of SRRA+OPH")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_BASE),
                        help="Output directory for snapshot files")
    parser.add_argument("--label", type=str, default=None,
                        help="Label for this snapshot")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🔬 Phase 11 Test 1 — T11.1: Structural Topology Baseline")
    print("=" * 60)
    print(f"Scanning directories: {list(SCAN_DIRS.keys())}")
    print(f"Output: {output_dir}")
    print()

    extractor = TopologyExtractor(SCAN_DIRS)
    graph = extractor.extract()

    if args.label:
        graph.label = args.label

    # Save full topology
    topology_path = output_dir / f"{graph.label}.json"
    with open(topology_path, "w") as f:
        json.dump(asdict(graph), f, indent=2, default=str)
    print(f"✅ Full topology: {topology_path}")

    # Save observer graph (filtered)
    observer_nodes = {nid: n for nid, n in graph.nodes.items() if n.get("node_type") == "observer"}
    observer_graph = {
        "label": f"observer_{graph.label}",
        "timestamp": graph.timestamp,
        "total_observers": len(observer_nodes),
        "observers": observer_nodes,
    }
    observer_path = output_dir / f"observer_graph_{graph.label}.json"
    with open(observer_path, "w") as f:
        json.dump(observer_graph, f, indent=2, default=str)
    print(f"✅ Observer graph: {observer_path}")

    # Save routing graph (filtered)
    routing_nodes = {nid: n for nid, n in graph.nodes.items() if n.get("node_type") in ("router", "signal")}
    routing_graph = {
        "label": f"routing_{graph.label}",
        "timestamp": graph.timestamp,
        "total_routing_nodes": len(routing_nodes),
        "routing_nodes": routing_nodes,
    }
    routing_path = output_dir / f"routing_graph_{graph.label}.json"
    with open(routing_path, "w") as f:
        json.dump(routing_graph, f, indent=2, default=str)
    print(f"✅ Routing graph: {routing_path}")

    # Print summary
    print()
    print("─── Topology Summary ───")
    print(f"  Total nodes:    {graph.total_nodes}")
    print(f"  Total edges:    {graph.total_edges}")
    print(f"  Clusters:       {len(graph.clusters)}")
    print(f"  Max depth:      {graph.metrics.get('max_dependency_depth', 'N/A')}")
    print(f"  Cycles:         {graph.metrics.get('cyclic_dependencies', 'N/A')}")
    print(f"  Orphans:        {graph.metrics.get('orphan_nodes', 'N/A')}")
    print(f"  Over-connected: {graph.metrics.get('over_connected_nodes', 'N/A')}")
    print(f"  Fragility zones: {len(graph.fragility_zones)}")
    print()

    # Type distribution
    type_dist = graph.metrics.get("type_distribution", {})
    if type_dist:
        print("─── Type Distribution ───")
        for ntype, count in sorted(type_dist.items(), key=lambda x: x[1], reverse=True):
            print(f"  {ntype:12s}: {count}")
        print()

    # PASS/FAIL assessment
    print("─── Pass/Fail Assessment ───")
    failures = []

    if graph.metrics.get("orphan_nodes", 0) > 0:
        failures.append(f"  ⚠️  {graph.metrics['orphan_nodes']} orphan nodes detected")
    else:
        print("  ✅ No orphan nodes")

    if graph.metrics.get("cyclic_dependencies", 0) > 0:
        failures.append(f"  ⚠️  {graph.metrics['cyclic_dependencies']} cyclic dependencies")
    else:
        print("  ✅ No cyclic dependencies")

    if graph.metrics.get("over_connected_nodes", 0) > 0:
        failures.append(f"  ⚠️  {graph.metrics['over_connected_nodes']} over-connected nodes")
    else:
        print("  ✅ No over-connected nodes")

    if graph.fragility_zones:
        failures.append(f"  ⚠️  {len(graph.fragility_zones)} fragility zones identified")
    else:
        print("  ✅ No fragility zones")

    for f in failures:
        print(f)

    print()
    if not failures:
        print("🟢 PASS: All observer relationships traceable, no hidden dependency chains")
    else:
        print("🟡 CONDITIONAL PASS: Topology measurable but has areas of concern")
        print("   Review fragility zones and orphan nodes for potential issues")

    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
