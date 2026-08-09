"""
Runner for the Phase 4 latent FX factor engine.
CR-P4-LATENT-FACTOR-ENGINE-01
"""
from __future__ import annotations

import sys
from pathlib import Path

from capital_routing.phases.phase_4_orchestrator import Phase4FactorEngine, write_gate
from capital_routing.phases.phase_4_report import generate_phase4_report


def main() -> None:
    base = Path(__file__).resolve().parents[1]  # capital-routing/
    p3 = base / "artifacts" / "phase_03"
    out = base / "artifacts" / "phase_04"
    engine = Phase4FactorEngine(p3, out)
    result = engine.run(write=True)
    report = generate_phase4_report(out)
    gate = write_gate(out)
    print("Phase 4 gate:", gate["gate_passed"])
    print("Report:", report)
    print("Factor rows H1:", result["meta"]["factor_rows_h1"])
    print("Clearance:", gate["phase_5_cleared"])


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    main()