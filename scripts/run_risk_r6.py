"""Run the R6 episode/heat-sizing study (CR-RISK-BLOCK2-R6)."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from capital_routing.phases.phase_r6_orchestrator import PhaseR6HeatSizing

if __name__ == "__main__":
    t0 = time.time()
    res = PhaseR6HeatSizing(ROOT).run()
    print(json.dumps({"elapsed_seconds": round(res["elapsed_seconds"], 1),
                      "n_events": res["n_events"], "pass": res["pass"]},
                     indent=2))
    print(f"total wall time {time.time() - t0:.1f}s")
