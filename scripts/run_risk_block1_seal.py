"""Run the CR-RISK-BLOCK1-FOUNDATION-SEAL synthesis checkpoint."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from capital_routing.phases.phase_block1_orchestrator import run_seal

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    res = run_seal(root)
    print(f"sealed={res['block1_foundation_sealed']} outputs={len(res['outputs'])} "
          f"({res['elapsed_seconds']:.1f}s)")
