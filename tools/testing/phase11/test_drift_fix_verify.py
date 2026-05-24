"""Quick verification that the drift fix works."""
import sys, json
sys.path.insert(0, ".")
from tools.testing.long_horizon.test_11_1_b import Test11_1BRunner

# Run a short test (120s total, 20s intervals = 6 checkpoints)
test = Test11_1BRunner(duration_hours=1)
test.duration_seconds = 120
test.state.checkpoint_interval = 20

result = test.run_blocking()

print("=== DRIFT FIX VERIFICATION ===")
print(f"Overall pass: {result['overall_pass']}")
print(f"Checkpoints: {result['total_checkpoints']}")
print(f"Passed: {result['passed_checkpoints']}")
print(f"Failed: {result['failed_checkpoints']}")
print(f"Max drift score: {result['max_drift_score']}")
print()
for cp in result["checkpoints"]:
    print(f"  {cp['checkpoint_id']}: drift={cp['drift_score']}, status={cp['status']}, details={cp['drift_details']}")

# Verify: all checkpoints should pass
assert result["overall_pass"], "DRIFT FIX FAILED — checkpoints still failing!"
assert result["max_drift_score"] == 0.0, f"Drift score should be 0, got {result['max_drift_score']}"
print("\n✅ DRIFT FIX VERIFIED — all checkpoints pass!")
