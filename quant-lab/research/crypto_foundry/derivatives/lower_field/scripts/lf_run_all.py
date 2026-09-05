#!/usr/bin/env python3
"""LF — run the full analysis pipeline in dependency order."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = [
    "lf_build_panel.py",
    "lf_analysis_events.py",
    "lf_analysis_structure.py",
    "lf_analysis_lenses_state.py",
    "lf_perturbations.py",
    "lf_plots.py",
]


def main() -> int:
    for step in STEPS:
        t0 = time.time()
        print(f"\n=== {step} ===", flush=True)
        r = subprocess.run([sys.executable, str(HERE / step)], cwd=HERE)
        if r.returncode != 0:
            print(f"STEP FAILED: {step}", flush=True)
            return r.returncode
        print(f"=== {step} done in {time.time()-t0:.0f}s ===", flush=True)
    print("PIPELINE COMPLETE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
