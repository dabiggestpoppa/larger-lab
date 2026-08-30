#!/usr/bin/env python3
"""OCE Book 2 local lifecycle CLI (B2-R7). Thin wrapper around
oce_control.local_lifecycle — keeps all logic importable/testable.

    python scripts/oce_local.py <command> [options]
    configure | doctor | start | migrate | wait-ready | smoke |
    restart | recover | stop | destroy
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from oce_control.local_lifecycle import main  # noqa: E402

if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    sys.exit(main())
