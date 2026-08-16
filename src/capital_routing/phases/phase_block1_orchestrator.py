"""Block-I foundation seal orchestrator: gathers R1-R4 artifacts, runs the
synthesis, and emits all BLOCK1_* doctrine/decision/manifest outputs."""
from __future__ import annotations

import sys
from pathlib import Path

from .phase_block1_seal import Block1Seal


def run_seal(root: Path) -> dict:
    seal = Block1Seal(root)
    return seal.run()


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    res = run_seal(root)
    print(json_dumps := __import__("json").dumps(res, indent=2, default=str))
