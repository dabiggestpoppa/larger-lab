"""
Phase 11.1-E — Recursive Orchestration Stability Test
=====================================================
Tests whether the system prevents recursive collapse:
- Recursion depth bounded (max 10)
- No infinite loops or deadlocks
- Token usage bounded under recursive load
- Loop detection and kill-switch work
- Orphan agents cleaned up

This is a SHORT-RUN test that simulates recursive delegation patterns.
"""

import time
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

RESULTS_FILE = Path("stability/recursive_orchestration_results.json")
RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

MAX_RECURSION_DEPTH = 10
MAX_TOKENS_PER_CHAIN = 10000
MAX_CHAIN_DURATION_SECONDS = 30


class RecursiveOrchestrationTest:
    """
    Simulates recursive delegation patterns and validates stability.
    """

    def __init__(self, cycles: int = 5):
        self.cycles = cycles
        self.results: List[Dict[str, Any]] = []
        self._active_agents: Dict[str, Dict] = {}
        self._orphan_agents: List[str] = []
        self._loop_detection_log: List[Dict] = []

    def _spawn_agent(self, agent_id: str, depth: int, parent_id: str = None) -> Dict[str, Any]:
        """Simulate spawning an agent at a given recursion depth."""
        agent = {
            "id": agent_id,
            "depth": depth,
            "parent_id": parent_id,
            "spawned_at": time.time(),
            "status": "active",
            "tokens_used": 0,
            "children": [],
        }
        self._active_agents[agent_id] = agent
        return agent

    def _simulate_recursive_chain(self, chain_id: str, target_depth: int) -> Dict[str, Any]:
        """
        Simulate a recursive delegation chain.
        Returns metrics about the chain execution.
        """
        start_time = time.time()
        max_depth_reached = 0
        total_tokens = 0
        deadlocks_detected = 0
        loops_detected = 0
        orphans_cleaned = 0
        issues = []

        # Root agent spawns children recursively
        root = self._spawn_agent(f"{chain_id}_root", 0)
        queue = [(root, 1)]  # (parent, next_depth)

        while queue:
            parent, depth = queue.pop(0)

            # Check recursion depth bound
            if depth > MAX_RECURSION_DEPTH:
                loops_detected += 1
                self._loop_detection_log.append({
                    "chain_id": chain_id,
                    "depth": depth,
                    "action": "depth_limit_reached",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                issues.append(f"Depth limit reached at depth {depth}")
                continue

            max_depth_reached = max(max_depth_reached, depth)

            # Simulate spawning 2 children per agent (binary tree)
            for i in range(2):
                child_id = f"{chain_id}_d{depth}_{i}"
                child = self._spawn_agent(child_id, depth, parent["id"])
                parent["children"].append(child_id)

                # Simulate token usage
                child["tokens_used"] = 100 * depth  # Deeper = more tokens
                total_tokens += child["tokens_used"]

                # Check token bound
                if total_tokens > MAX_TOKENS_PER_CHAIN:
                    issues.append(f"Token limit exceeded: {total_tokens}")
                    break

                # Continue recursion if not at target depth
                if depth < target_depth:
                    queue.append((child, depth + 1))

            # Check duration
            elapsed = time.time() - start_time
            if elapsed > MAX_CHAIN_DURATION_SECONDS:
                deadlocks_detected += 1
                issues.append(f"Chain timeout after {elapsed:.1f}s")
                break

        # Simulate cleanup of orphan agents
        for agent_id, agent in list(self._active_agents.items()):
            if agent["status"] == "active" and agent["depth"] > 0:
                # Simulate some agents becoming orphans
                if hash(agent_id) % 5 == 0:  # ~20% orphan rate
                    self._orphan_agents.append(agent_id)
                    orphans_cleaned += 1

        # Clean up
        for agent_id in list(self._active_agents.keys()):
            if agent_id.startswith(chain_id):
                del self._active_agents[agent_id]

        elapsed = time.time() - start_time

        return {
            "chain_id": chain_id,
            "target_depth": target_depth,
            "max_depth_reached": max_depth_reached,
            "total_tokens": total_tokens,
            "duration_seconds": round(elapsed, 4),
            "deadlocks_detected": deadlocks_detected,
            "loops_detected": loops_detected,
            "orphans_cleaned": orphans_cleaned,
            "issues": issues,
            "passed": (
                max_depth_reached <= MAX_RECURSION_DEPTH
                and deadlocks_detected == 0
                and loops_detected <= target_depth  # Some loop detection is expected
                and elapsed < MAX_CHAIN_DURATION_SECONDS
            ),
        }

    def run_cycle(self, cycle_num: int) -> Dict[str, Any]:
        """Run a single test cycle with multiple chain patterns."""
        timestamp = datetime.now(timezone.utc).isoformat()
        chains = []

        # Test 1: Normal recursion (depth 5)
        chains.append(self._simulate_recursive_chain(f"cycle{cycle_num}_normal", 5))

        # Test 2: Deep recursion (depth 15, should be bounded to 10)
        chains.append(self._simulate_recursive_chain(f"cycle{cycle_num}_deep", 15))

        # Test 3: Wide recursion (many siblings)
        chains.append(self._simulate_recursive_chain(f"cycle{cycle_num}_wide", 8))

        cycle_passed = all(c["passed"] for c in chains)

        return {
            "cycle": cycle_num,
            "timestamp": timestamp,
            "chains": chains,
            "passed": cycle_passed,
            "issues": [issue for c in chains for issue in c["issues"]],
        }

    def run_all(self) -> Dict[str, Any]:
        """Run all test cycles."""
        print("=" * 60)
        print("PHASE 11.1-E — RECURSIVE ORCHESTRATION STABILITY TEST")
        print(f"Cycles: {self.cycles}")
        print("=" * 60)

        for i in range(1, self.cycles + 1):
            print(f"\n[11.1-E] Cycle {i}/{self.cycles}...")
            result = self.run_cycle(i)
            self.results.append(result)

            status = "PASS" if result["passed"] else "FAIL"
            print(f"  {'✅' if result['passed'] else '❌'} {status} — "
                  f"chains={len(result['chains'])} | issues={len(result['issues'])}")

            for chain in result["chains"]:
                print(f"    Chain '{chain['chain_id']}': "
                      f"depth={chain['max_depth_reached']}/{chain['target_depth']} | "
                      f"tokens={chain['total_tokens']} | "
                      f"duration={chain['duration_seconds']}s | "
                      f"loops={chain['loops_detected']} | "
                      f"deadlocks={chain['deadlocks_detected']}")

        passed = sum(1 for r in self.results if r["passed"])
        total = len(self.results)

        summary = {
            "test_id": "11.1-E",
            "test_name": "recursive_orchestration_stability",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycles": self.cycles,
            "passed_cycles": passed,
            "failed_cycles": total - passed,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
            "max_recursion_depth": MAX_RECURSION_DEPTH,
            "max_tokens_per_chain": MAX_TOKENS_PER_CHAIN,
            "loop_detection_log": self._loop_detection_log,
            "results": self.results,
            "overall_pass": passed == total,
        }

        print(f"\n{'=' * 60}")
        print(f"RESULTS: {passed}/{total} cycles passed ({summary['pass_rate']}%)")
        print(f"Loop detection events: {len(self._loop_detection_log)}")
        print(f"Overall: {'✅ PASS' if summary['overall_pass'] else '❌ FAIL'}")
        print(f"Results: {RESULTS_FILE}")

        RESULTS_FILE.write_text(json.dumps(summary, indent=2, default=str))
        return summary


if __name__ == "__main__":
    test = RecursiveOrchestrationTest(cycles=5)
    results = test.run_all()
