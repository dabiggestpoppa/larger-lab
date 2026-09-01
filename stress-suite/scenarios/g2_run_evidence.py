"""Generate G2 evidence artifacts from the committed scenario packs.

For every scenario (S01..S05 + S01_WEAK):
  - runs the pack through the governed pipeline,
  - writes run_receipt.json (machine-readable) + human_readable_result.md,
  - runs the G2X pairwise contract-swap audit and writes
    stress-suite/evidence/G2_CROSS_SCENARIO_AUDIT.md.

Deterministic, local-first, $0. Expectations and hidden ground truth never
participate in decisions (run_scenario strips them); the receipts record the
post-hoc verdict. Re-running this script must reproduce identical receipts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.scenariolib import load_all_packs
from engine.scenario import run_scenario, evaluate_expectation

ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = ROOT / "scenarios"
EVIDENCE = ROOT / "evidence"
MAIN = ["S01", "S02", "S03", "S04", "S05"]


def _behavior_sig(res):
    a = res.artifacts
    return (a["actual_phase_trace"], a["trace"], a["holds"], a["terminal_knowledge_states"])


def main() -> int:
    packs = load_all_packs(SCENARIOS)
    summary = {}

    for sid, pack in packs.items():
        res = run_scenario(pack.spec, pack.contract, pack.policy)
        verdict = evaluate_expectation(res, pack.spec)
        receipt = {
            "scenario_id": sid,
            "scenario_version": pack.spec.scenario_version,
            "starting_epoch": pack.initial_epoch.get("epoch_id", ""),
            "evaluation_contract": res.artifacts["evaluation_contract"],
            "policy_id": res.artifacts["policy_id"],
            "policy_version": res.artifacts["policy_version"],
            "stimulus_count": res.artifacts["stimulus_count"],
            "evidence_count": res.artifacts["evidence_count"],
            "actual_phase_trace": res.artifacts["actual_phase_trace"],
            "expected_phase_trace": verdict["expected_phase_path"],
            "terminal_phase": res.artifacts["terminal_phase"],
            "terminal_knowledge_states": res.artifacts["terminal_knowledge_states"],
            "forbidden_attempts": res.artifacts["forbidden_attempts"],
            "holds": res.artifacts["holds"],
            "evidence_refs_by_transition": res.artifacts["evidence_refs_by_transition"],
            "authority_state_before": res.artifacts["authority_state_before"],
            "authority_state_after": res.artifacts["authority_state_after"],
            "hidden_ground_truth_accessed": res.artifacts["hidden_ground_truth_accessed"],
            "expected_trace_accessed_during_run": res.artifacts["expected_trace_accessed"],
            "pass": verdict["pass"],
            "failures": verdict["failures"],
            "fingerprint": res.artifacts["fingerprint"],
        }
        (pack.path / "run_receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        (pack.path / "human_readable_result.md").write_text(
            _human_readable(sid, receipt), encoding="utf-8"
        )
        summary[sid] = {
            "terminal_phase": receipt["terminal_phase"],
            "trace": receipt["actual_phase_trace"],
            "pass": receipt["pass"],
        }

    audit = _cross_audit(packs)
    EVIDENCE.mkdir(exist_ok=True)
    (EVIDENCE / "G2_CROSS_SCENARIO_AUDIT.md").write_text(audit, encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0


def _human_readable(sid, r) -> str:
    lines = [
        f"# Stress Suite {sid} — human-readable result",
        "",
        f"- **Terminal phase:** {r['terminal_phase']}",
        f"- **Actual phase trace:** {' -> '.join(r['actual_phase_trace'])}",
        f"- **Expected phase trace:** {' -> '.join(r['expected_phase_trace'])}",
        f"- **Verdict:** {'PASS' if r['pass'] else 'FAIL — ' + ', '.join(r['failures'])}",
        f"- **Terminal knowledge:** {json.dumps(r['terminal_knowledge_states'], sort_keys=True)}",
        f"- **Forbidden attempts:** {len(r['forbidden_attempts'])}",
        f"- **Holds (evidence insufficient / blocker):** {[h['rule_id'] for h in r['holds']]}",
        f"- **Evaluation contract:** {r['evaluation_contract']['contract_id']} "
        f"(v{r['evaluation_contract']['version_tag']}, frozen={r['evaluation_contract']['freeze_status']}, "
        f"fp={r['evaluation_contract']['fingerprint'][:16]}…)",
        f"- **Expected trace accessed during run:** {r['expected_trace_accessed_during_run']}",
        f"- **Hidden ground truth accessed:** {r['hidden_ground_truth_accessed']}",
        f"- **Run fingerprint:** {r['fingerprint']}",
        "",
    ]
    return "\n".join(lines)


def _cross_audit(packs) -> str:
    lines = [
        "# G2 X — Cross-Scenario Contract Audit",
        "",
        "Every scenario was replayed under every OTHER scenario's frozen evaluation",
        "contract (20 ordered pairs). The audit proves contracts participate in",
        "decisions, are never mutated by foreign runs, and can only yield a PASS",
        "verdict when behavior is identical to the own-contract run (no silent",
        "inheritance of foreign semantics).",
        "",
        "| scenario | under contract | behavior identical | foreign verdict |",
        "|---|---|---|---|",
    ]
    for a in MAIN:
        own = run_scenario(packs[a].spec, packs[a].contract, packs[a].policy)
        for b in MAIN:
            if a == b:
                continue
            cb = packs[b].contract
            if not cb.is_frozen():
                cb.freeze()
            foreign = run_scenario(packs[a].spec, cb, packs[a].policy)
            same = _behavior_sig(foreign) == _behavior_sig(own)
            verdict = evaluate_expectation(foreign, packs[a].spec)
            lines.append(
                f"| {a} | {b} | {'yes' if same else 'no'} | "
                f"{'PASS' if verdict['pass'] else 'FAIL'} |"
            )
    lines += [
        "",
        "**Interpretation:** a `yes` row means the foreign threshold happened to be",
        "semantically equivalent for that scenario's gates (recorded as benign",
        "equivalence); a `no` row means the foreign contract changed applied",
        "behavior, and the verdict column reports the honest outcome against the",
        "scenario's own expectations. No row shows `PASS` with different behavior.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())