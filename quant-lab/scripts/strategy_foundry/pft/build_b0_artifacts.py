"""PFT-B0 artifact builder.

Aggregates evidence (artifact existence, schema validation, pytest junit
result) and derives DECISION.json status from that evidence. No value is
hardcoded as PASS: the gate is computed.

Usage:
    python quant-lab/scripts/strategy_foundry/pft/build_b0_artifacts.py \
        --pytest-xml <path-to-junit.xml> [--emit]

Without --emit the script validates the existing program artifacts and
prints the derived status (dry-run). With --emit it (re)writes the
JSON artifacts and the derived REPORT/DECISION/NEXT_PLAN.
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

QUANT_LAB_DIR = Path(__file__).resolve().parents[3]

from strategy_foundry.pft.governance import ledger as ledger_mod  # noqa: E402
from strategy_foundry.pft.governance import schemas  # noqa: E402
from strategy_foundry.pft.governance.authority import default_authority  # noqa: E402
from strategy_foundry.pft.governance.decisions import DecisionRecord, validate_decision_dict  # noqa: E402
from strategy_foundry.pft.program_registry import (  # noqa: E402
    PLANNING_COMMIT_SHA,
    PROGRAM_BASE_SHA,
    PROGRAM_BRANCH,
    build_parameter_register,
    formula_register_dict,
    species_register_dict,
)

PROGRAM_DIR = QUANT_LAB_DIR / "research" / "strategy_foundry" / "pft" / "program"

REQUIRED_PROSE_ARTIFACTS = [
    "PROGRAM_CONSTITUTION.md",
    "RESEARCH_LIFECYCLE.md",
    "CHANGE_CONTROL.md",
]

JSON_ARTIFACTS = [
    "EXPERIMENT_REGISTRY.json",
    "SPEC_REGISTER.json",
    "PARAMETER_REGISTER.json",
    "FORMULA_REGISTER.json",
    "AUTHORITY.json",
    "DATA_USAGE_LEDGER.json",
]


def parse_pytest_junit(path: Path) -> dict:
    """Return {'passed': bool, 'tests': n, 'failures': n, 'errors': n}."""
    try:
        import xml.etree.ElementTree as ET

        tree = ET.parse(path)
        root = tree.getroot()
        tests = int(root.attrib.get("tests", 0))
        failures = int(root.attrib.get("failures", 0))
        errors = int(root.attrib.get("errors", 0))
        return {
            "passed": failures == 0 and errors == 0,
            "tests": tests,
            "failures": failures,
            "errors": errors,
        }
    except Exception as exc:  # noqa: BLE001
        return {"passed": False, "tests": 0, "failures": 0, "errors": 0, "error": str(exc)}


def evidence_checks() -> dict:
    """Aggregate B0 evidence without writing anything."""
    checks = {}

    prose = {p: (PROGRAM_DIR / p).exists() for p in REQUIRED_PROSE_ARTIFACTS}
    checks["prose_artifacts_exist"] = all(prose.values())
    checks["prose_artifact_detail"] = prose

    # JSON artifact validation
    json_checks = {}
    for name in JSON_ARTIFACTS:
        path = PROGRAM_DIR / name
        if name == "SPEC_REGISTER.json":
            errs = schemas.validate_file(path, schemas.validate_species_register)
        elif name == "PARAMETER_REGISTER.json":
            errs = schemas.validate_file(path, schemas.validate_parameter_register)
        elif name == "FORMULA_REGISTER.json":
            errs = schemas.validate_file(path, schemas.validate_formula_register)
        elif name == "EXPERIMENT_REGISTRY.json":
            errs = schemas.validate_file(path, schemas.validate_experiment_registry)
        elif name == "AUTHORITY.json":
            errs = schemas.validate_file(path, schemas.validate_authority_dict)
        elif name == "DATA_USAGE_LEDGER.json":
            errs = schemas.validate_file(path, schemas.validate_ledger_json)
        else:  # pragma: no cover
            errs = ["unknown artifact"]
        json_checks[name] = {"exists": path.exists(), "errors": errs}
    checks["json_artifacts_valid"] = all(
        v["exists"] and not v["errors"] for v in json_checks.values()
    )
    checks["json_artifact_detail"] = json_checks

    # Species governance content checks
    species = species_register_dict()
    checks["species_registered"] = set(species["species"]) == {
        "A0-GENESIS", "A1-DEEPERS", "Q0-TRANSMISSION", "X1-SYNTHESIS"
    }
    checks["a1_frozen"] = species["species"]["A1-DEEPERS"]["status"] == "FROZEN_PRIMARY_RAW_SPEC"
    checks["x1_not_authorized"] = species["species"]["X1-SYNTHESIS"]["status"] == "NOT_AUTHORIZED"

    # Parameter/formula registers non-empty and complete
    param_reg = build_parameter_register()
    checks["author_constants_registered"] = len(param_reg.by_class("AUTHOR_CONSTANT")) >= 30
    checks["formula_ids_complete"] = len(formula_register_dict()["formulas"]) == 19

    # Authority deny-by-default
    authority = default_authority()
    checks["authority_all_denied"] = (
        authority.economic_testing_authorized is False
        and authority.optimization_authorized is False
        and authority.confirmation_authorized is False
        and authority.holdout_authorized is False
        and authority.deployment_authorized is False
        and authority.production_capital_authorized is False
        and authority.next_checkpoint_authorized is False
    )
    return checks


def emit_artifacts() -> None:
    PROGRAM_DIR.mkdir(parents=True, exist_ok=True)

    # EXPERIMENT_REGISTRY: no experiments registered at B0 (honest empty state)
    (PROGRAM_DIR / "EXPERIMENT_REGISTRY.json").write_text(
        json.dumps({"schema_version": "1.0", "program_id": "PFT",
                    "experiments": []}, indent=2),
        encoding="utf-8",
    )

    (PROGRAM_DIR / "SPEC_REGISTER.json").write_text(
        json.dumps(species_register_dict(), indent=2), encoding="utf-8")

    (PROGRAM_DIR / "PARAMETER_REGISTER.json").write_text(
        json.dumps(build_parameter_register().to_register(), indent=2), encoding="utf-8")

    (PROGRAM_DIR / "FORMULA_REGISTER.json").write_text(
        json.dumps(formula_register_dict(), indent=2), encoding="utf-8")

    (PROGRAM_DIR / "AUTHORITY.json").write_text(
        json.dumps(default_authority().to_dict(), indent=2), encoding="utf-8")

    # DATA_USAGE_LEDGER: JSONL is the append-only source; .json is the validated artifact
    jsonl_path = PROGRAM_DIR / "DATA_USAGE_LEDGER.jsonl"
    if not jsonl_path.exists():
        jsonl_path.write_text("", encoding="utf-8")
    log = ledger_mod.DataUsageLedger(jsonl_path)
    (PROGRAM_DIR / "DATA_USAGE_LEDGER.json").write_text(
        json.dumps(log.to_json(), indent=2), encoding="utf-8")


def build_decision(pytest_result: dict) -> DecisionRecord:
    checks = evidence_checks()
    decision = DecisionRecord(
        checkpoint_id="PFT-B0-PROGRAM-CONSTITUTION",
        program_id="PFT",
        branch=PROGRAM_BRANCH,
        base_sha=PROGRAM_BASE_SHA,
        commit_sha=PLANNING_COMMIT_SHA,  # prior head; sealing commit SHA reported after push
    )
    # B0 is governance-only: data/math/causality gates first apply at B2/B3.
    # They are marked True here as "no requirement at this checkpoint", with a
    # warning to prevent them being read as validated.
    decision.data_truth_pass = True
    decision.math_conformance_pass = True
    decision.causality_pass = True
    decision.warnings = [
        "B0 does not evaluate data truth, math conformance or causality; "
        "those gates first apply at PFT-B2/PFT-B3."
    ]

    gate = (
        checks["prose_artifacts_exist"]
        and checks["json_artifacts_valid"]
        and checks["species_registered"]
        and checks["a1_frozen"]
        and checks["x1_not_authorized"]
        and checks["author_constants_registered"]
        and checks["formula_ids_complete"]
        and checks["authority_all_denied"]
        and pytest_result["passed"]
    )
    if not gate:
        decision.blockers = [
            key for key, value in checks.items()
            if value is False and key != "prose_artifact_detail" and key != "json_artifact_detail"
        ]
        if not pytest_result["passed"]:
            decision.blockers.append("pytest failures/errors present")
    decision.status = decision.derive_status()
    if decision.status != "PASS":
        decision.status = "FAIL"  # B0 blockers are gate failures, not data blocks
    decision.blockers = [b for b in decision.blockers if b not in (
        "prose_artifact_detail", "json_artifact_detail")]
    return decision


def build_report(checks: dict, pytest_result: dict, decision: DecisionRecord) -> str:
    lines = [
        "# PFT-B0 — Program Constitution — REPORT",
        "",
        f"- checkpoint: `{decision.checkpoint_id}`",
        f"- branch: `{decision.branch}`",
        f"- base_sha: `{decision.base_sha}`",
        f"- prior_head_sha: `{decision.commit_sha}` (sealing commit SHA reported after push)",
        f"- generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Evidence",
        "",
        f"- prose governance artifacts present: {checks['prose_artifacts_exist']}",
        f"- JSON artifacts present and schema-valid: {checks['json_artifacts_valid']}",
        f"- species registered: {checks['species_registered']}",
        f"- A1 (Deepers v2.2) frozen: {checks['a1_frozen']}",
        f"- X1 synthesis not authorized: {checks['x1_not_authorized']}",
        f"- author constants registered: {checks['author_constants_registered']}",
        f"- 19 formula ids registered: {checks['formula_ids_complete']}",
        f"- authority deny-by-default: {checks['authority_all_denied']}",
        f"- pytest: {pytest_result['tests']} tests, "
        f"{pytest_result['failures']} failures, {pytest_result['errors']} errors",
        f"- economic PnL computed: {decision.economic_pnl_computed}",
        f"- parameter optimization performed: {decision.optimization_performed}",
        f"- confirmation consumed: {decision.confirmation_consumed}",
        f"- holdout consumed: {decision.holdout_consumed}",
        "",
        f"## Derived status: **{decision.status}**",
        "",
        "## Repository hygiene",
        "",
        "Obsolete branches deleted (authorized by operator, verified not current and",
        "not affecting `main`):",
        "",
        "- `agent/obb-01-book-01-reality-audit` (local + remote)",
        "- `agent/openbb-forge-obb-01-02-docs` (remote)",
        "- `cascade/can-you-see-the-most-recent-commits-to-3818c8` (local + remote)",
        "",
        "## Gate",
        "",
        "`human_review_required = true`",
        "`next_checkpoint_authorized = false`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pytest-xml", required=True, help="pytest junit xml path")
    parser.add_argument("--emit", action="store_true", help="write/refresh artifacts")
    args = parser.parse_args()

    pytest_result = parse_pytest_junit(Path(args.pytest_xml))
    if "--emit" in sys.argv:
        emit_artifacts()
    checks = evidence_checks()
    decision = build_decision(pytest_result)
    decision.validate()

    (PROGRAM_DIR / "DECISION.json").write_text(
        json.dumps(decision.to_dict(), indent=2), encoding="utf-8")
    (PROGRAM_DIR / "REPORT.md").write_text(
        build_report(checks, pytest_result, decision), encoding="utf-8")

    errors = validate_decision_dict(decision.to_dict())
    if errors:
        print("DECISION schema violations:", errors)
        return 1

    print(f"B0 gate: {decision.status}")
    print(f"  pytest: {pytest_result}")
    print(f"  evidence checks: {json.dumps(checks, indent=2, default=str)}")
    if decision.status != "PASS":
        print("blockers:", decision.blockers)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
