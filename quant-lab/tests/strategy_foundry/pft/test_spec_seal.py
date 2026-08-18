"""PFT-B1 specification seal tests (build prompt sections 16-17).

Every formula must be registered and mapped; every spec parameter must
resolve in the parameter register as RAW-usable; fail-closed behavior
must be enumerated; RAW/TWIN namespaces must be isolated; no economic
capability may exist in the pft source tree.
"""

import json
from pathlib import Path

import pytest

from strategy_foundry.pft.governance import schemas
from strategy_foundry.pft.program_registry import (
    FORMULA_IDS,
    SPECIES_REGISTER,
    build_parameter_register,
    formula_register_dict,
    species_register_dict,
)
from strategy_foundry.pft.spec.a1_v22 import (
    FAIL_CLOSED_TABLE,
    PRECEDENCE,
    build_a1_v22_spec,
    validate_a1_spec,
)
from strategy_foundry.pft.spec.implementation_map import (
    FAILURE_BEHAVIOR,
    IMPLEMENTATION_TARGETS,
    TEST_TARGETS,
    enrich_formula_register,
)

SRC = Path(__file__).resolve().parents[3] / "src"
QUANT_LAB = Path(__file__).resolve().parents[3]
PFT_DIR = QUANT_LAB / "research" / "strategy_foundry" / "pft"


class TestMachineSpec:
    def test_spec_builds_and_validates(self):
        spec = build_a1_v22_spec()
        errors = validate_a1_spec(spec, build_parameter_register())
        assert errors == []

    def test_spec_identity_frozen(self):
        spec = build_a1_v22_spec()
        assert spec["spec_id"] == "A1-DEEPERS-v2.2"
        assert spec["spec_status"] == "FROZEN"
        assert spec["spec_lineage"] == ["v1.x", "v2.0", "v2.1", "v2.2"]

    def test_precedence_chain_frozen(self):
        assert PRECEDENCE == [
            "features", "K1", "K2", "K3", "K4", "FSM", "gross_cap", "fade",
            "drawdown_overlay", "leg_stop", "final_target", "execution",
        ]

    def test_all_kernels_present(self):
        spec = build_a1_v22_spec()
        assert set(spec["kernels"]) == {"K1", "K2", "K3", "K4"}

    def test_unregistered_parameter_rejected(self):
        """Adding an unknown param_ref to the spec must fail validation."""
        spec = build_a1_v22_spec()
        spec["kernels"]["K2"]["gamma"]["param_ref"] = "A1.NOPE"
        errors = validate_a1_spec(spec, build_parameter_register())
        assert any("unregistered parameter" in e for e in errors)

    def test_forbidden_parameter_class_rejected(self):
        """A TWIN/FORBIDDEN parameter referenced by the spec must fail validation."""
        spec = build_a1_v22_spec()
        reg = build_parameter_register()
        spec["kernels"]["K2"]["gamma"]["param_ref"] = "A1.F03.GAMMA_HL_ZERO"
        # swap in a twin-class parameter with the same id
        from strategy_foundry.pft.governance.parameters import Parameter, ParameterRegister

        reg2 = ParameterRegister()
        for p in reg.all():
            reg2.add(p)
        reg2.add(Parameter(
            id="A1.TW.PROBE", name="probe", value=1,
            parameter_class="TWIN_PARAMETER", source_ref="test"))
        spec["kernels"]["K2"]["gamma"]["param_ref"] = "A1.TW.PROBE"
        errors = validate_a1_spec(spec, reg2)
        assert any("non-RAW class" in e for e in errors)

    def test_fail_closed_table_complete(self):
        for kernel in ("K1", "K2", "K3", "K4"):
            assert kernel in FAIL_CLOSED_TABLE, f"no fail-closed entries for {kernel}"
        for overlay in ("FSM", "DRAWDOWN", "LEG_STOP"):
            assert overlay in FAIL_CLOSED_TABLE, f"no fail-closed entries for {overlay}"
        for kernel, rules in FAIL_CLOSED_TABLE.items():
            for rule in rules:
                assert "condition" in rule and "behavior" in rule

    def test_no_pseudoinverse_substitution_in_spec(self):
        spec = build_a1_v22_spec()
        ols = spec["kernels"]["K3"]["ols"]["fail_closed"]
        assert "pseudoinverse" in ols or "TWIN" in ols


class TestFormulaRegister:
    def test_nineteen_formulas_registered(self):
        formulas = formula_register_dict()["formulas"]
        assert [f["id"] for f in formulas] == FORMULA_IDS
        assert len(set(FORMULA_IDS)) == 19

    def test_every_formula_mapped(self):
        enriched = enrich_formula_register(formula_register_dict()["formulas"])
        assert len(enriched) == 19
        for f in enriched:
            assert f["implementation_target"], f["id"]
            assert f["test_target"], f["id"]
            assert f["failure_behavior"], f["id"]
            assert f["implementation_status"] == "MAPPED"

    def test_mapping_cover_all_formula_ids(self):
        assert set(IMPLEMENTATION_TARGETS) == set(FORMULA_IDS)
        assert set(FAILURE_BEHAVIOR) == set(FORMULA_IDS)
        assert set(TEST_TARGETS) == set(FORMULA_IDS)

    def test_formula_register_schema_with_mapping(self):
        enriched = enrich_formula_register(formula_register_dict()["formulas"])
        data = {"schema_version": "1.1", "formulas": enriched}
        assert schemas.validate_formula_register(data) == []

    def test_emitted_artifact_validates(self):
        path = PFT_DIR / "a1_deepers_v2" / "spec" / "SPEC_A1_V2_2.json"
        if not path.exists():
            pytest.skip("artifact not emitted in this run")
        spec = json.loads(path.read_text(encoding="utf-8"))
        assert validate_a1_spec(spec, build_parameter_register()) == []


class TestSpeciesSeal:
    def test_species_statuses(self):
        assert SPECIES_REGISTER["A0-GENESIS"]["status"] == "SPECIMEN_REGISTERED"
        assert SPECIES_REGISTER["A1-DEEPERS"]["status"] == "FROZEN_PRIMARY_RAW_SPEC"
        assert SPECIES_REGISTER["Q0-TRANSMISSION"]["status"] == "SPECIMEN_REGISTERED"
        assert SPECIES_REGISTER["X1-SYNTHESIS"]["status"] == "NOT_AUTHORIZED"

    def test_species_register_schema(self):
        assert schemas.validate_species_register(species_register_dict()) == []

    def test_lineage_docs_exist(self):
        assert (PFT_DIR / "a0_genesis" / "spec" / "LINEAGE.md").exists()
        assert (PFT_DIR / "q0_transmission" / "spec" / "LINEAGE.md").exists()
        assert (PFT_DIR / "a1_deepers_v2" / "RAW_NAMESPACE.md").exists()
        assert (PFT_DIR / "a1_deepers_v2" / "TWINS_NAMESPACE.md").exists()


class TestRawTwinIsolation:
    def test_raw_does_not_import_twins(self):
        raw_root = PFT_DIR / "a1_deepers_v2" / "raw"
        src_raw = SRC / "strategy_foundry" / "pft"
        forbidden = ("twins", "TWINS")
        for root in (raw_root, src_raw):
            if not root.exists():
                continue
            for path in sorted(root.rglob("*.py")):
                text = path.read_text(encoding="utf-8", errors="replace")
                for token in forbidden:
                    assert token not in text, f"{path} references {token}"


class TestEvidenceParsing:
    """Guards the junit parsing bug class found at B1: counts live on the
    inner <testsuite> element, not the outer <testsuites> wrapper."""

    def test_parses_wrapped_testsuites(self, tmp_path):
        xml_path = tmp_path / "junit.xml"
        xml_path.write_text(
            '<?xml version="1.0" encoding="utf-8"?>'
            '<testsuites name="pytest tests">'
            '<testsuite name="pytest" errors="1" failures="2" tests="66"/>'
            '</testsuites>',
            encoding="utf-8",
        )
        from strategy_foundry.pft.evidence import parse_pytest_junit

        result = parse_pytest_junit(xml_path)
        assert result == {"passed": False, "tests": 66, "failures": 2, "errors": 1}

    def test_parses_plain_testsuite_root(self, tmp_path):
        xml_path = tmp_path / "junit.xml"
        xml_path.write_text(
            '<testsuite name="pytest" errors="0" failures="0" tests="48"/>',
            encoding="utf-8",
        )
        from strategy_foundry.pft.evidence import parse_pytest_junit

        result = parse_pytest_junit(tmp_path / "junit.xml")
        assert result["passed"] is True
        assert result["tests"] == 48

    def test_missing_file_fails_closed(self, tmp_path):
        from strategy_foundry.pft.evidence import parse_pytest_junit

        result = parse_pytest_junit(tmp_path / "does-not-exist.xml")
        assert result["passed"] is False
        assert "error" in result


class TestNoEconomicCapability:
    FORBIDDEN = [
        "profit_factor", "sharpe", "sortino", "calmar", "win_rate",
        "expectancy", "strategy_pnl", "total_return", "best_combination",
    ]

    def test_pft_src_has_no_economic_identifiers(self):
        src_root = SRC / "strategy_foundry" / "pft"
        for path in sorted(src_root.rglob("*.py")):
            text = path.read_text(encoding="utf-8", errors="replace")
            for token in self.FORBIDDEN:
                assert token not in text, f"{path} contains forbidden token {token!r}"
