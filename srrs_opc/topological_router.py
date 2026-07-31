"""
Topological Router
===================
Phase 3: Routes messages between patches using entropy-based path selection.

Instead of fixed pipelines, routing optimizes for:
- Lowest entropy (most stable path)
- Shortest stabilization path
- Highest recoverability

Uses Dijkstra's algorithm on the coupling graph.
"""

import heapq
import json
from typing import Dict, Any, List, Optional, Tuple
from .dynamic_coupling import DynamicCouplingEngine


class Route:
    """A route between two patches."""

    def __init__(self, path: List[str], total_entropy: float,
                 hops: int, confidence: float):
        self.path = path
        self.total_entropy = total_entropy
        self.hops = hops
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "total_entropy": round(self.total_entropy, 3),
            "hops": self.hops,
            "confidence": round(self.confidence, 3),
        }


class TopologicalRouter:
    """
    Routes messages between patches using the coupling topology.

    Entropy = 1 - edge_weight (higher weight = lower entropy = better path)
    """

    def __init__(self, coupling_engine: DynamicCouplingEngine):
        self.coupling = coupling_engine

    def find_best_route(self, source: str, target: str) -> Optional[Route]:
        """
        Find the lowest-entropy path from source to target.
        Uses Dijkstra's algorithm.
        """
        if source == target:
            return Route([source], 0.0, 0, 1.0)

        # Priority queue: (entropy, patch, path)
        pq = [(0.0, source, [source])]
        visited = set()

        while pq:
            entropy, current, path = heapq.heappop(pq)

            if current in visited:
                continue
            visited.add(current)

            if current == target:
                confidence = 1.0 / (1.0 + entropy)
                return Route(path, entropy, len(path) - 1, confidence)

            # Explore neighbors
            for edge in self.coupling._edges.values():
                neighbor = None
                if edge.patch_a == current and edge.patch_b not in visited:
                    neighbor = edge.patch_b
                    edge_entropy = 1.0 - edge.weight
                elif edge.patch_b == current and edge.patch_a not in visited:
                    neighbor = edge.patch_a
                    edge_entropy = 1.0 - edge.weight

                if neighbor:
                    new_entropy = entropy + edge_entropy
                    new_path = path + [neighbor]
                    heapq.heappush(pq, (new_entropy, neighbor, new_path))

        return None  # No route found

    def find_all_routes(self, source: str, target: str,
                        max_routes: int = 3) -> List[Route]:
        """Find multiple routes (for redundancy)."""
        routes = []

        # Find primary route
        primary = self.find_best_route(source, target)
        if primary:
            routes.append(primary)

        # Find alternative routes by temporarily weakening primary edges
        if primary and len(primary.path) > 2:
            for i in range(len(primary.path) - 1):
                a, b = primary.path[i], primary.path[i + 1]
                original_weight = self.coupling.get_edge_weight(a, b)

                # Temporarily weaken this edge
                key = self.coupling._key(a, b)
                if key in self.coupling._edges:
                    self.coupling._edges[key].weight = 0.05

                alt = self.find_best_route(source, target)
                if alt and alt.path != primary.path:
                    routes.append(alt)

                # Restore original weight
                if key in self.coupling._edges:
                    self.coupling._edges[key].weight = original_weight

                if len(routes) >= max_routes:
                    break

        return routes

    def get_routing_table(self, patches: List[str]) -> Dict[str, Any]:
        """Build a full routing table for all patch pairs."""
        table = {}
        for src in patches:
            for dst in patches:
                if src != dst:
                    route = self.find_best_route(src, dst)
                    if route:
                        table[f"{src}->{dst}"] = route.to_dict()
        return table

    def stress_test(self, patches: List[str],
                    kill_patch: str = None) -> Dict[str, Any]:
        """
        Stress test: verify system reroutes when a patch is killed.
        """
        results = {
            "killed_patch": kill_patch,
            "routes_before": {},
            "routes_after": {},
            "rerouted": [],
            "failed": [],
        }

        # Routes before kill
        active = [p for p in patches if p != kill_patch] if kill_patch else patches
        for src in active:
            for dst in active:
                if src != dst:
                    route = self.find_best_route(src, dst)
                    results["routes_before"][f"{src}->{dst}"] = (
                        route.to_dict() if route else None
                    )

        if kill_patch:
            # Remove all edges connected to killed patch
            edges_to_remove = []
            for key, edge in self.coupling._edges.items():
                if edge.patch_a == kill_patch or edge.patch_b == kill_patch:
                    edges_to_remove.append(key)
            for key in edges_to_remove:
                del self.coupling._edges[key]

            # Routes after kill
            surviving = [p for p in patches if p != kill_patch]
            for src in surviving:
                for dst in surviving:
                    if src != dst:
                        route = self.find_best_route(src, dst)
                        results["routes_after"][f"{src}->{dst}"] = (
                            route.to_dict() if route else None
                        )
                        if route:
                            results["rerouted"].append(f"{src}->{dst}")
                        else:
                            results["failed"].append(f"{src}->{dst}")

        return results


if __name__ == "__main__":
    from .dynamic_coupling import DynamicCouplingEngine

    coupling = DynamicCouplingEngine()

    # Set up topology
    coupling.record_interaction("planner", "execution")
    coupling.record_interaction("planner", "execution")
    coupling.record_interaction("execution", "memory")
    coupling.record_interaction("memory", "repair")
    coupling.record_interaction("repair", "planner")
    coupling.record_interaction("execution", "repair")

    router = TopologicalRouter(coupling)

    # Find best route
    route = router.find_best_route("planner", "repair")
    if route:
        print(f"Best route planner->repair: {json.dumps(route.to_dict(), indent=2)}")

    # All routes
    routes = router.find_all_routes("planner", "repair")
    print(f"\nAll routes ({len(routes)}):")
    for r in routes:
        print(f"  {r.to_dict()}")

    # Stress test
    print("\nStress test (kill 'execution'):")
    results = router.stress_test(
        ["planner", "execution", "memory", "repair"],
        kill_patch="execution"
    )
    print(f"  Rerouted: {len(results['rerouted'])}")
    print(f"  Failed: {len(results['failed'])}")
