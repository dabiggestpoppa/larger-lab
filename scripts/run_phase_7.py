#!/usr/bin/env python
"""Run the Phase 7 routing-translation study (CR-P7-ROUTING-TRANSLATION-01)."""
import os
import sys
from pathlib import Path

# Ensure this checkout's src is imported (a pip-installed capital_routing may
# point at a different checkout).
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from capital_routing.phases.phase_7_orchestrator import Phase7RoutingTranslation

if __name__ == "__main__":
    summary = Phase7RoutingTranslation(ROOT).run()
    print("\n=== PHASE 7 COMPLETE ===")
    print(f"gate_status: {summary['gate_status']}")
    print(f"promoted: {summary['promoted']}")
    print(f"configs: {summary['configs']}")
    print(f"validation: {summary['validation']}")
    sys.exit(0)
