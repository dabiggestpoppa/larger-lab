"""Run CR-RISK-BLOCK1 R1 — Exposure Truth & Portfolio Heat."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from capital_routing.phases.phase_r1_orchestrator import PhaseR1ExposureTruth  # noqa: E402

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    result = PhaseR1ExposureTruth(root).run()
    print(json.dumps(result, indent=2, default=str))
