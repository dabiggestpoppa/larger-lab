"""R1 checks 64-71 (interface purity, generic-package purity, authority drift)."""
from __future__ import annotations

import json
from pathlib import Path

from execution_runtime import interfaces

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_DIR = Path(__file__).resolve().parents[1]
MANIFEST = (
    REPO_ROOT
    / "research"
    / "execution_runtime_foundation"
    / "r1"
    / "QL_EXEC_R1_SOURCE_SHA_MANIFEST.json"
)


def _package_sources() -> str:
    chunks = []
    for p in sorted(PKG_DIR.glob("*.py")):
        chunks.append(p.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _refers_to(src: str, name: str) -> bool:
    import ast

    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == name:
            return True
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == name:
            return True
        if isinstance(node, ast.Import) and any(a.name == name for a in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module == name:
            return True
    return False


def test_64_strategy_adapter_has_no_mt5_dependency():
    src = Path(interfaces.__file__).read_text(encoding="utf-8")
    assert not _refers_to(src, "MetaTrader5")
    assert not _refers_to(src, "mt5")


def test_65_capital_policy_adapter_has_no_translate_heat_to_notional():
    methods = [m for m in dir(interfaces.CapitalPolicyAdapter) if not m.startswith("_")]
    assert "translate_heat_to_notional" not in methods
    assert "admit" in methods
    assert "release" in methods
    assert "reconstruct_reservations" in methods


def test_66_capital_translation_adapter_exists_separately():
    assert hasattr(interfaces, "CapitalTranslationAdapter")
    assert hasattr(interfaces, "CapitalPolicyAdapter")
    assert interfaces.CapitalTranslationAdapter is not interfaces.CapitalPolicyAdapter


def test_67_broker_session_has_no_metatrader5_import():
    src = Path(interfaces.__file__).read_text(encoding="utf-8")
    assert not _refers_to(src, "MetaTrader5")


def test_68_generic_package_has_no_capital_routing_ab_constants():
    src = _package_sources()
    for token in ("24.494897", "A1_70_30", "H1-1.00", "USDJPY"):
        assert token not in src, token


def test_69_generic_package_has_no_tb_z_weight_symbols():
    src = _package_sources()
    for token in ("GBPAUD", "GBPNZD", "AUDNZD", "STOP_Z", "TB-B", "TB-FWD-V1", "TB-FROZEN-CONTROL"):
        assert token not in src, token


def test_70_r1_manifest_records_latest_frozen_tb_authority():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["tb_r0_authority_sha"] == "df5f349e02ac932491cb067df7aff25cb71c50ac"
    assert data["tb_r1_authority_sha"] == "d12005988ce61170d9bc5478089baa5ce54cc2a9"
    assert data["tb_authority_drift_acknowledged"] is True


def test_71_d120_market_recovery_regression_in_future_parity_plan():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["future_r2_r4_parity_includes_market_recovery_regression"] is True
    drift = data["tb_authority_drift"]
    assert "ONLINE_MARKET_CLOSED" in drift or "market recovery" in drift
