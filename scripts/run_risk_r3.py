"""Run CR-RISK-BLOCK1 R3 — Profit Anatomy."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from capital_routing.phases.phase_r3_orchestrator import PhaseR3ProfitAnatomy  # noqa: E402

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = PhaseR3ProfitAnatomy(root).run()
    print(json.dumps(result, indent=2, default=str))
