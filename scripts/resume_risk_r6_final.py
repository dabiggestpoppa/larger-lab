"""Resume the R6 pipeline's final three steps from already-generated CSVs.

The full pipeline (phase_r6_orchestrator.run) is deterministic but takes
~20 minutes (dependency-aware MC). If it is interrupted after the complexity
matrix, this script finishes the evidence matrix, report and decision from
the CSVs already on disk. It never re-derives policy results.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from capital_routing.phases.phase_r6_common import load_r6_inputs
from capital_routing.phases.phase_r6_orchestrator import PhaseR6HeatSizing


def main():
    t0 = time.time()
    R6 = ROOT / "artifacts" / "risk_block2" / "r6"
    print("[resume] loading frozen inputs ...", flush=True)
    load = load_r6_inputs(ROOT)

    def rd(name: str) -> pd.DataFrame:
        return pd.read_csv(R6 / name)

    frontier = rd("R6_HEAT_POLICY_FRONTIER.csv")
    mc = rd("R6_HEAT_POLICY_MONTE_CARLO.csv")
    edge = rd("R6_HEAT_EDGE_DEGRADATION.csv")
    tail = rd("R6_HEAT_TAIL_STRESS.csv")
    nd = rd("R6_NONDOMINATED_HEAT_FRONTIER.csv")
    ep_pol = rd("R6_EPISODE_POLICY_RESULTS.csv")
    do = rd("R6_DIRECTIONAL_OVERLAP.csv")
    fes = rd("R6_FAMILY_EPISODE_STRUCTURE.csv")
    summary = rd("R6_POLICY_ADMISSION_SUMMARY.csv")
    eff = rd("R6_HEAT_EFFICIENCY.csv")
    rej = rd("R6_REJECTED_EVENT_AUDIT.csv")
    ts = rd("R6_HEAT_TEMPORAL_STABILITY.csv")
    adv = rd("R6_ADVERSARIAL_EPISODE_TESTS.csv")
    print(f"[resume] inputs loaded in {time.time() - t0:.1f}s", flush=True)

    # regenerate the cheap anatomy studies (they may have been produced by an
    # earlier code revision); all other CSVs are treated as authoritative.
    from capital_routing.phases.phase_r6_analysis import (directional_overlap,
                                                          family_episode_structure,
                                                          overlap_anatomy)
    print("[resume] regenerate anatomy studies ...", flush=True)
    overlap_anatomy(load, 0.5, 0.5).to_csv(R6 / "R6_OVERLAP_ANATOMY.csv", index=False)
    directional_overlap(load, 0.5, 0.5).to_csv(R6 / "R6_DIRECTIONAL_OVERLAP.csv", index=False)
    family_episode_structure(load, 0.5, 0.5).to_csv(
        R6 / "R6_FAMILY_EPISODE_STRUCTURE.csv", index=False)
    oa = rd("R6_OVERLAP_ANATOMY.csv")
    do = rd("R6_DIRECTIONAL_OVERLAP.csv")
    fes = rd("R6_FAMILY_EPISODE_STRUCTURE.csv")

    orch = PhaseR6HeatSizing(ROOT)
    git_sha = orch._git_sha()

    print("[resume] evidence matrix ...", flush=True)
    evm = orch._evidence_matrix(load, frontier, mc, edge, tail, nd, ep_pol,
                                do, fes, summary)
    evm.to_csv(R6 / "R6_EVIDENCE_STATUS_MATRIX.csv", index=False)

    print("[resume] report ...", flush=True)
    report = orch._report(load, frontier, mc, edge, tail, nd, ep_pol, do,
                          fes, summary, eff, rej, ts, adv)
    (R6 / "R6_REPORT.md").write_text(report, encoding="utf-8")

    print("[resume] decision ...", flush=True)
    decision = orch._decision(load, frontier, mc, edge, tail, nd, summary,
                              evm, git_sha)
    (R6 / "R6_DECISION.json").write_text(
        json.dumps(decision, indent=2, default=str), encoding="utf-8")

    print(f"[resume] complete in {time.time() - t0:.1f}s "
          f"pass={decision['r6_episode_heat_sizing_pass']}", flush=True)


if __name__ == "__main__":
    main()
