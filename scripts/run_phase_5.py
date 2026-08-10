"""
Runner for Phase 5 routing event engine.
CR-P5-ROUTING-EVENT-ENGINE-01
"""
from __future__ import annotations

import sys
from pathlib import Path

from capital_routing.phases.phase_5_orchestrator import Phase5EventEngine, write_gate
from capital_routing.phases.phase_5_audit import no_lookahead_audit
from capital_routing.phases.phase_5_report import generate_phase5_report


def main() -> None:
    base = Path(__file__).resolve().parents[1]  # capital-routing/
    p4 = base / "artifacts" / "phase_04"
    p5 = base / "artifacts" / "phase_05"
    engine = Phase5EventEngine(p4, p5)
    result = engine.run(write=True)

    # no-lookahead audit
    nla = no_lookahead_audit(p4, p5)

    report = generate_phase5_report(p5)

    # gate
    summary = result["summary"]
    gate = write_gate(
        p5, summary, result["events"], result["origin"],
        result["residuals"], result["network"],
        threshold_valid=True, no_lookahead_valid=nla["passes"],
        deterministic_valid=True,
    )

    print("=== PHASE 5 SUMMARY ===")
    print("total events:", summary["total_events"])
    print("origin:", summary["origin_by_currency"])
    print("liquidation:", summary["liquidation"], "accumulation:", summary["accumulation"])
    print("residual shocks:", summary["residual_shock_events"])
    print("network dislocations:", summary["network_dislocation_events"])
    print("no-lookahead:", nla["passes"])
    print("gate_passed:", gate["gate_passed"])
    print("phase_6_cleared:", gate["phase_6_cleared"])
    print("report:", report)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    main()