#!/usr/bin/env python3
"""Run all ALT rotation test suites (DATA-0, DATA-0.1, DATA-1).

Note: the DATA-0 determinism test rebuilds the OLD-schema derived outputs
in a scratch copy (never the live data_0 directory), so running this
suite cannot clobber repaired artifacts.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent  # alt_rotation


def main() -> int:
    suites = [
        ("data_0/tests", "test_alt_data_0.py"),
        ("data_0/tests", "test_alt_data_0_1.py"),
        ("data_1/tests", "test_alt_data_1.py"),
    ]
    total = 0
    failed = False
    for d, f in suites:
        p = ROOT / d / f
        print(f"\n===== {d}/{f} =====", flush=True)
        r = subprocess.run([sys.executable, "-m", "pytest", str(p), "-q"],
                           capture_output=True, text=True, cwd=ROOT / d)
        print(r.stdout[-4000:], flush=True)
        if r.returncode != 0:
            failed = True
            print(r.stderr[-2000:], flush=True)
        # parse "N passed" from output
        import re
        m = re.search(r"(\d+) passed", r.stdout)
        if m:
            total += int(m.group(1))
    print(f"\nTOTAL PASSED: {total}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
