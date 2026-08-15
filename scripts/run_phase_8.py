"""Run the Phase 8 CEREBUS overlay discovery pipeline."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from capital_routing.phases.phase_8_orchestrator import Phase8Orchestrator  # noqa: E402

if __name__ == "__main__":
    t0 = time.time()
    orch = Phase8Orchestrator(ROOT, ROOT / "artifacts" / "phase_08")
    manifest = orch.run()
    print(f"phase 8 complete in {time.time() - t0:.1f}s")
    print(json.dumps(manifest["decision"], indent=2))
