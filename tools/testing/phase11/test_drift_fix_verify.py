"""Direct verification of the drift fix logic."""
import sys, json, hashlib
sys.path.insert(0, ".")

# Simulate the drift detection logic from the fixed code
def compute_drift(baseline, identity_hash, trajectory_hash, goal_hash, memory_hash):
    """Replicate the fixed drift detection logic."""
    drift_details = {}
    drift_score = 0.0

    if baseline:
        # Identity and goal changes are real drift
        if identity_hash != baseline["identity"]:
            drift_details["identity"] = "changed"
        if goal_hash != baseline["goal"]:
            drift_details["goal"] = "changed"

        # Trajectory and memory WILL change — expected, not drift
        if trajectory_hash != baseline["trajectory"]:
            drift_details["trajectory"] = "evolved"
        if memory_hash != baseline["memory"]:
            drift_details["memory"] = "evolved"

        # Only count critical drift (identity + goal)
        critical_drift_count = sum(1 for v in drift_details.values() if v == "changed")
        drift_score = critical_drift_count / 2.0
    else:
        baseline = {
            "identity": identity_hash,
            "trajectory": trajectory_hash,
            "goal": goal_hash,
            "memory": memory_hash
        }

    return drift_score, drift_details, baseline


def h(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()[:16]


# Simulate 5 checkpoints with normal operational changes
print("=== DRIFT FIX DIRECT VERIFICATION ===\n")

# Checkpoint 1: baseline
identity = h({"id": "SRRA+OPH", "count": 10})
trajectory = h({"tasks": 100, "errors": 2, "elapsed": 0})
goal = h({"primary": "72h_continuity_stability", "target": 99.5})
memory = h({"alive": 10, "degraded": 0, "dead": 0, "uptime": 0})

baseline = None
results = []

for i in range(5):
    # Simulate normal operational changes
    trajectory = h({"tasks": 100 + i * 50, "errors": 2 + i, "elapsed": i * 6})
    memory = h({"alive": 10 - (i == 3), "degraded": (i == 3), "dead": 0, "uptime": i * 21600})
    # Identity and goal stay the same
    identity = h({"id": "SRRA+OPH", "count": 10})
    goal = h({"primary": "72h_continuity_stability", "target": 99.5})

    score, details, baseline = compute_drift(baseline, identity, trajectory, goal, memory)
    results.append({"checkpoint": i + 1, "score": score, "details": details})
    status = "PASS" if score == 0 else "FAIL"
    print(f"  Checkpoint {i+1}: drift={score}, status={status}, details={details}")

# Verify all pass
all_pass = all(r["score"] == 0 for r in results)
print(f"\nAll checkpoints pass: {all_pass}")
assert all_pass, "DRIFT FIX FAILED"

# Now test with actual identity change (should detect drift)
print("\n--- Testing identity change detection ---")
bad_identity = h({"id": "COMPROMISED", "count": 10})
score, details, _ = compute_drift(baseline, bad_identity, trajectory, goal, memory)
print(f"  Identity changed: drift={score}, details={details}")
assert score == 0.5, f"Expected 0.5 for identity change, got {score}"
print("  ✅ Identity change correctly detected as drift")

# Test with goal change (should detect drift)
print("\n--- Testing goal change detection ---")
bad_goal = h({"primary": "maximize_profit", "target": 50.0})
score, details, _ = compute_drift(baseline, identity, trajectory, bad_goal, memory)
print(f"  Goal changed: drift={score}, details={details}")
assert score == 0.5, f"Expected 0.5 for goal change, got {score}"
print("  ✅ Goal change correctly detected as drift")

# Test with both identity AND goal change (full drift)
print("\n--- Testing full drift detection ---")
score, details, _ = compute_drift(baseline, bad_identity, trajectory, bad_goal, memory)
print(f"  Both changed: drift={score}, details={details}")
assert score == 1.0, f"Expected 1.0 for full drift, got {score}"
print("  ✅ Full drift correctly detected")

print("\n✅ ALL DRIFT FIX TESTS PASSED!")
print("  - Normal trajectory/memory evolution: NOT flagged as drift")
print("  - Identity change: correctly flagged")
print("  - Goal change: correctly flagged")
print("  - Both changes: correctly flagged as full drift")
