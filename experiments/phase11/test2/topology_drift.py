"""Topology drift test — runs for 60s, tracks changes."""
import sys, json, time, random, hashlib
from pathlib import Path
from datetime import datetime, timezone
REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
OUTPUT = REPO_ROOT / "experiments" / "phase11" / "test2" / "drift_snapshots"
OUTPUT.mkdir(parents=True, exist_ok=True)
from core.observability.observer_registry import get_registry, ObserverState, InteractionType
reg = get_registry()
baseline = reg.get_observer_graph()
bh = hashlib.md5(json.dumps(baseline, sort_keys=True, default=str).encode()).hexdigest()[:16]
print(f"Baseline: {baseline['total_observers']} obs, hash={bh}")
start = time.time()
changes = 0
while time.time() - start < 60:
    if random.random() < 0.3:
        obs_list = list(reg._observers.keys())
        if obs_list:
            reg.set_observer_state(random.choice(obs_list), random.choice(list(ObserverState)), random.uniform(0, 0.5))
            changes += 1
    if random.random() < 0.2:
        obs_list = list(reg._observers.keys())
        if len(obs_list) >= 2:
            s, t = random.sample(obs_list, 2)
            reg.record_interaction(s, t, random.choice(list(InteractionType)), random.uniform(1, 100), random.choice(["synced", "desynced"]))
            changes += 1
    time.sleep(0.5)
final = reg.get_observer_graph()
fh = hashlib.md5(json.dumps(final, sort_keys=True, default=str).encode()).hexdigest()[:16]
print(f"Final: {final['total_observers']} obs, hash={fh}, drift={bh != fh}, changes={changes}")
with open(OUTPUT / f"drift_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
    json.dump({"baseline_hash": bh, "final_hash": fh, "drift": bh != fh, "changes": changes}, f, indent=2)
print("Drift test complete.")
