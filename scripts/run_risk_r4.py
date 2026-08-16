"""Run CR-RISK-BLOCK1 R4 — Static Risk Frontier."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from capital_routing.phases.phase_r4_orchestrator import PhaseR4StaticFrontier  # noqa: E402

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = PhaseR4StaticFrontier(root).run()
    print(json.dumps(result, indent=2, default=str))
