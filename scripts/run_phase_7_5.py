#!/usr/bin/env python
"""Run the Phase 7.5 baseline seal (CR-P7.5-ROUTING-BASELINE-SEAL-01)."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from capital_routing.phases.phase_7_5_orchestrator import Phase7_5BaselineSeal

if __name__ == "__main__":
    summary = Phase7_5BaselineSeal(ROOT).run()
    print("\n=== P7.5 COMPLETE ===")
    print(f"frozen_policy: {summary['frozen_policy']}")
    for k, v in summary["verdicts"].items():
        print(f"  {k}: {v['verdict']}")
    sys.exit(0)
