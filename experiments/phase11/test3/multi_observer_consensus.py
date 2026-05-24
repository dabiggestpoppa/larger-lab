"""Multi-observer consensus stress test."""
import json, random
from pathlib import Path
from datetime import datetime, timezone
REPO_ROOT = Path(__file__).resolve().parents[3]
OUTPUT = REPO_ROOT / "experiments" / "phase11" / "test3" / "reports"
OUTPUT.mkdir(parents=True, exist_ok=True)
n_obs, n_rounds = 50, 10
obs = [{"id": f"obs_{i}", "value": random.random(), "weight": random.uniform(0.5, 1.5)} for i in range(n_obs)]
for r in range(n_rounds):
    avg = sum(o["value"] * o["weight"] for o in obs) / sum(o["weight"] for o in obs)
    for o in obs:
        o["value"] = o["value"] * 0.7 + avg * 0.3
    var = sum((o["value"] - avg) ** 2 for o in obs) / n_obs
    if r == n_rounds - 1:
        print(f"Consensus: {var < 0.01}, variance: {var:.8f}")
        with open(OUTPUT / "multi_observer_consensus.json", "w") as f:
            json.dump({"n_obs": n_obs, "n_rounds": n_rounds, "consensus": var < 0.01, "variance": var}, f, indent=2)
