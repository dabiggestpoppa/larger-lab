"""Run CR-RISK-BLOCK2-R5-FAMILY-QUALITY-ALLOCATION."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from capital_routing.phases.phase_r5_orchestrator import PhaseR5FamilyAllocation

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    res = PhaseR5FamilyAllocation(root).run()
    print(f"pass={res['pass']} events={res['n_events']} ({res['elapsed_seconds']:.0f}s)")
