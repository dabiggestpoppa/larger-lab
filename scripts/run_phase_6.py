"""
Runner for Phase 6 forward routing study.
CR-P6-FORWARD-ROUTING-STUDY-01
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure THIS checkout's src is used even when an editable install of
# capital_routing points at a different checkout.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from capital_routing.phases.phase_6_orchestrator import Phase6RoutingStudy  # noqa: E402


def main() -> None:
    base = Path(__file__).resolve().parents[1]  # capital-routing/
    p5 = base / "artifacts" / "phase_05"
    p4 = base / "artifacts" / "phase_04"
    p3 = base / "artifacts" / "phase_03"
    p6 = base / "artifacts" / "phase_06"
    study = Phase6RoutingStudy(p5, p4, p3, p6)
    s = study.run(write=True)

    print("=== PHASE 6 SUMMARY ===")
    print("total events:", s["total_events"])
    print("candidates frozen from development:", s["candidates_frozen"])
    print("holdout labels:", s["holdout_labels"])
    print("theses:", s["theses"])
    print("phase7_eligible:", s["phase7_eligible"])
    print("gate_passed:", s["gate_passed"])
    print("phase_7_cleared:", s["phase_7_cleared"])
    print("report:", s["report"])
    print("elapsed_seconds:", s["elapsed_seconds"])


if __name__ == "__main__":
    main()
    sys.exit(0)  # force clean exit even if a library thread lingers
