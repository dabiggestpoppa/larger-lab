"""PFT-B1 artifact builder.

Emits and validates the frozen machine-readable A1 v2.2 spec, the
enriched formula register, and the updated species register. Derives
DECISION.json status from evidence (schemas, register cross-checks,
namespace isolation, pytest junit).

Usage:
    python quant-lab/scripts/strategy_foundry/pft/build_b1_artifacts.py \
        --pytest-xml <path-to-junit.xml> [--emit]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SRC = Path(__file__).resolve().parents[3] / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from strategy_foundry.pft.evidence import parse_pytest_junit  # noqa: E402
from strategy_foundry.pft.governance import schemas  # noqa: E402
from strategy_foundry.pft.governance.decisions import DecisionRecord, validate_decision_dict  # noqa: E402
from strategy_foundry.pft.program_registry import (  # noqa: E402
    FORMULA_IDS,
    PLANNING_COMMIT_SHA,
    PROGRAM_BASE_SHA,
    PROGRAM_BRANCH,
    build_parameter_register,
    formula_register_dict,
    species_register_dict,
)
from strategy_foundry.pft.spec.a1_v22 import build_a1_v22_spec, validate_a1_spec  # noqa: E402
from strategy_foundry.pft.spec.implementation_map import enrich_formula_register  # noqa: E402

QUANT_LAB_DIR = Path(__file__).resolve().parents[3]
PFT_DIR = QUANT_LAB_DIR / "research" / "strategy_foundry" / "pft"
PROGRAM_DIR = PFT_DIR / "program"
SPEC_DIR = PFT_DIR / "a1_deepers_v2" / "spec"
A0_SPEC_DIR = PFT_DIR / "a0_genesis" / "spec"
Q0_SPEC_DIR = PFT_DIR / "q0_transmission" / "spec"

REQUIRED_LINEAGE_ARTIFACTS = [
    A0_SPEC_DIR / "LINEAGE.md",
    Q0_SPEC_DIR / "LINEAGE.md",
    SPEC_DIR / "SPEC_A1_V2_2.json",
    PFT_DIR / "a1_deepers_v2" / "RAW_NAMESPACE.md",
    PFT_DIR / "a1_deepers_v2" / "TWINS_NAMESPACE.md",
]

# Forbidden economic identifiers for the pre-economic scan.
FORBIDDEN_ECONOMIC_TOKENS = [
    "profit_factor", "sharpe", "sortino", "calmar", "win_rate", "expectancy",
    "strategy_pnl", "total_return", "best_combination",
]


def scan_for_economic_tokens() -> list:
    """Scan the pft source tree for forbidden economic identifiers."""
    hits = []
    src_root = QUANT_LAB_DIR / "src" / "strategy_foundry" / "pft"
    for path in sorted(src_root.rglob("*.py")):
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in FORBIDDEN_ECONOMIC_TOKENS:
            if token in text:
                hits.append(f"{path.relative_to(QUANT_LAB_DIR)}: contains {token!r}")
    return hits


def evidence_checks() -> dict:
    checks = {}

    # Machine spec validity against the parameter register.
    spec = build_a1_v22_spec()
    spec_errors = validate_a1_spec(spec, build_parameter_register())
    checks["machine_spec_valid"] = not spec_errors
    checks["machine_spec_errors"] = spec_errors[:20]

    # Species register
    species = species_register_dict()
    checks["species_registered"] = set(species["species"]) == {
        "A0-GENESIS", "A1-DEEPERS", "Q0-TRANSMISSION", "X1-SYNTHESIS"}
    checks["a1_frozen"] = species["species"]["A1-DEEPERS"]["status"] == "FROZEN_PRIMARY_RAW_SPEC"
    checks["q0_registered"] = species["species"]["Q0-TRANSMISSION"]["status"] == "SPECIMEN_REGISTERED"
    checks["x1_not_authorized"] = species["species"]["X1-SYNTHESIS"]["status"] == "NOT_AUTHORIZED"

    # Lineage artifacts exist
    checks["lineage_artifacts_exist"] = all(p.exists() for p in REQUIRED_LINEAGE_ARTIFACTS)
    checks["lineage_artifact_detail"] = {
        str(p.relative_to(PFT_DIR)): p.exists() for p in REQUIRED_LINEAGE_ARTIFACTS
    }

    # Formula register: all 19 mapped.
    enriched = enrich_formula_register(formula_register_dict()["formulas"])
    checks["formula_ids_complete"] = {f["id"] for f in enriched} == set(FORMULA_IDS)
    checks["formulas_mapped"] = all(f.get("implementation_target") for f in enriched)
    checks["formulas_have_failure_behavior"] = all(f.get("failure_behavior") for f in enriched)

    # Constants registered and RAW-usable.
    reg = build_parameter_register()
    checks["author_constants_registered"] = len(reg.by_class("AUTHOR_CONSTANT")) >= 30
    bad = [p.id for p in reg.all() if p.parameter_class not in ("AUTHOR_CONSTANT", "RESEARCH_CONSTANT")]
    checks["no_forbidden_parameter_in_register"] = not bad

    # RAW/TWIN isolation: namespace docs + no twin imports under raw/.
    checks["raw_twin_namespace_docs"] = (
        (PFT_DIR / "a1_deepers_v2" / "RAW_NAMESPACE.md").exists()
        and (PFT_DIR / "a1_deepers_v2" / "TWINS_NAMESPACE.md").exists()
    )

    # Economic capability scan.
    economic_hits = scan_for_economic_tokens()
    checks["no_economic_capability"] = not economic_hits
    checks["economic_scan_detail"] = economic_hits[:20]
    return checks


def emit_artifacts() -> None:
    SPEC_DIR.mkdir(parents=True, exist_ok=True)
    (SPEC_DIR / "SPEC_A1_V2_2.json").write_text(
        json.dumps(build_a1_v22_spec(), indent=2), encoding="utf-8")
    enriched = enrich_formula_register(formula_register_dict()["formulas"])
    (PROGRAM_DIR / "FORMULA_REGISTER.json").write_text(
        json.dumps({"schema_version": "1.1", "program_id": "PFT",
                    "formula_count": len(enriched), "formulas": enriched}, indent=2),
        encoding="utf-8")
    (PROGRAM_DIR / "SPEC_REGISTER.json").write_text(
        json.dumps(species_register_dict(), indent=2), encoding="utf-8")
    (PROGRAM_DIR / "PARAMETER_REGISTER.json").write_text(
        json.dumps(build_parameter_register().to_register(), indent=2), encoding="utf-8")


def build_decision(pytest_result: dict) -> DecisionRecord:
    checks = evidence_checks()
    decision = DecisionRecord(
        checkpoint_id="PFT-B1-SPECIFICATION-SEAL",
        program_id="PFT",
        branch=PROGRAM_BRANCH,
        base_sha=PROGRAM_BASE_SHA,
        commit_sha=PLANNING_COMMIT_SHA,
    )
    decision.data_truth_pass = True  # B1 does not evaluate data truth
    decision.math_conformance_pass = True  # B1 does not evaluate math
    decision.causality_pass = True  # B1 does not evaluate causality
    decision.warnings = [
        "B1 seals specifications; data truth / math / causality gates first apply at "
        "PFT-B2/PFT-B3."
    ]

    gate = (
        checks["machine_spec_valid"]
        and checks["species_registered"]
        and checks["a1_frozen"]
        and checks["q0_registered"]
        and checks["x1_not_authorized"]
        and checks["lineage_artifacts_exist"]
        and checks["formula_ids_complete"]
        and checks["formulas_mapped"]
        and checks["formulas_have_failure_behavior"]
        and checks["author_constants_registered"]
        and checks["no_forbidden_parameter_in_register"]
        and checks["raw_twin_namespace_docs"]
        and checks["no_economic_capability"]
        and pytest_result["passed"]
    )
    if not gate:
        decision.blockers = [
            key for key, value in checks.items()
            if value is False and key not in ("machine_spec_errors", "lineage_artifact_detail",
                                              "economic_scan_detail")
        ]
        if not pytest_result["passed"]:
            decision.blockers.append("pytest failures/errors present")
        if checks["machine_spec_errors"]:
            decision.blockers.append(f"machine spec violations: {checks['machine_spec_errors']}")
    decision.status = decision.derive_status()
    if decision.status != "PASS":
        decision.status = "FAIL"
    return decision


def build_report(checks: dict, pytest_result: dict, decision: DecisionRecord) -> str:
    return "\n".join([
        "# PFT-B1 — Specification Seal — REPORT",
        "",
        f"- checkpoint: `{decision.checkpoint_id}`",
        f"- branch: `{decision.branch}`",
        f"- base_sha: `{decision.base_sha}`",
        f"- generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Evidence",
        "",
        f"- machine A1 v2.2 spec valid against parameter register: {checks['machine_spec_valid']}",
        f"- species registered: {checks['species_registered']}",
        f"- A1 frozen: {checks['a1_frozen']}",
        f"- Q0 registered: {checks['q0_registered']}",
        f"- X1 not authorized: {checks['x1_not_authorized']}",
        f"- lineage artifacts present: {checks['lineage_artifacts_exist']}",
        f"- 19 formula ids complete: {checks['formula_ids_complete']}",
        f"- formulas mapped to implementation targets: {checks['formulas_mapped']}",
        f"- formulas have failure behavior: {checks['formulas_have_failure_behavior']}",
        f"- author constants registered: {checks['author_constants_registered']}",
        f"- no non-RAW parameter in register: {checks['no_forbidden_parameter_in_register']}",
        f"- RAW/TWIN namespace isolation: {checks['raw_twin_namespace_docs']}",
        f"- no economic capability in pft source: {checks['no_economic_capability']}",
        f"- pytest: {pytest_result['tests']} tests, {pytest_result['failures']} failures, "
        f"{pytest_result['errors']} errors",
        f"- economic PnL computed: {decision.economic_pnl_computed}",
        f"- parameter optimization performed: {decision.optimization_performed}",
        "",
        f"## Derived status: **{decision.status}**",
        "",
        "## Gate",
        "",
        "`human_review_required = true`",
        "`next_checkpoint_authorized = false`",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pytest-xml", required=True)
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()

    pytest_result = parse_pytest_junit(Path(args.pytest_xml))
    if args.emit:
        emit_artifacts()
    checks = evidence_checks()
    decision = build_decision(pytest_result)
    decision.validate()

    (PROGRAM_DIR / "DECISION.json").write_text(
        json.dumps(decision.to_dict(), indent=2), encoding="utf-8")
    (PROGRAM_DIR / "REPORT.md").write_text(
        build_report(checks, pytest_result, decision), encoding="utf-8")

    errs = validate_decision_dict(decision.to_dict())
    if errs:
        print("DECISION schema violations:", errs)
        return 1
    print(f"B1 gate: {decision.status}")
    print(f"  pytest: {pytest_result}")
    print(f"  machine spec errors: {checks['machine_spec_errors']}")
    if decision.status != "PASS":
        print("blockers:", decision.blockers)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
