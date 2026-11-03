"""SENSOR-B5-I11E1 - scope audit for the liquidation-normalizer checkpoint.

A checkpoint that proves what it added has also to prove what it did not.  This
is the I11 counterpart of the I01/I02/I03/I05/I08/I09/I10 scope audits: the
``normalization/sensors/`` tree is exactly the four authorized modules (the
three I10 modules plus the disclosed ``liquidation.py``), no later-sensor module
has appeared, the ratified 24-symbol I01 API is unchanged, the sealed
identity/terms/time/common trees and the frozen plan are byte-identical to the
I11 base, no duplicate-collapse engine exists, and no program gate is promoted.

OFFLINE.  No network, no wall clock, no filesystem writes.
"""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_QUANT_LAB = _HERE.parents[2]
_PACKAGE = _QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization"
_SENSORS = _PACKAGE / "sensors"
_EVIDENCE = (
    _QUANT_LAB / "research" / "crypto_foundry" / "sensor_fabric" / "evidence" / "bloc_05"
)

#: Directive-required starting HEAD == this checkpoint's custody base.
I11_BASE_HEAD = "82e44cf0ed8b8edca42eb4427db4cd6d659dd79a"

#: The authorized surface: the I10 three plus the disclosed I11 module.
FROZEN_MODULES = ["__init__.py", "liquidation.py", "side_maps.py", "trade.py"]

#: Sensor families that must NOT have a normalizer module yet (I12+).
UNAUTHORIZED_MODULE_STEMS = [
    "funding",
    "open_interest",
    "positioning",
    "book",
    "book_metric",
    "basis",
]


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=_QUANT_LAB,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout


def _sources() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(_SENSORS.glob("*.py"))
    }


# ---------------------------------------------------------------------------
# A11-03 -- exact implementation scope
# ---------------------------------------------------------------------------


def test_sensors_package_is_exactly_the_four_authorized_modules() -> None:
    files = sorted(entry.name for entry in _SENSORS.iterdir() if entry.suffix == ".py")
    assert files == FROZEN_MODULES


def test_no_later_sensor_normalizer_was_added() -> None:
    present = {entry.stem for entry in _SENSORS.glob("*.py")}
    for stem in UNAUTHORIZED_MODULE_STEMS:
        assert stem not in present, f"I12+ module leaked into I11: {stem}"


def test_no_module_was_added_to_common_or_the_package_root() -> None:
    common = sorted(
        entry.name for entry in (_PACKAGE / "common").iterdir() if entry.suffix == ".py"
    )
    assert common == [
        "__init__.py",
        "comparability.py",
        "conversion.py",
        "methodologies.py",
        "numeric.py",
        "semantic_registry.py",
        "units.py",
    ]
    top = sorted(entry.name for entry in _PACKAGE.iterdir() if entry.suffix == ".py")
    assert top == ["__init__.py", "enums.py", "models.py"]


def test_the_ratified_root_api_is_unchanged() -> None:
    import crypto_sensor_fabric.normalization as normalization

    assert len(normalization.__all__) == 24
    for absent in ("normalize_liquidation", "T1LiquidationRecord"):
        assert absent not in normalization.__all__
        assert not hasattr(normalization, absent)


def test_the_unfinished_composite_envelope_is_still_not_exported() -> None:
    import crypto_sensor_fabric.normalization.sensors as sensors

    assert "T1ObservationEnvelope" not in sensors.__all__
    assert not hasattr(sensors, "T1ObservationEnvelope")


def test_the_liquidation_surface_is_exported_explicitly() -> None:
    import crypto_sensor_fabric.normalization.sensors as sensors

    for name in (
        "normalize_liquidation",
        "T1LiquidationRecord",
        "LiquidationObservationInput",
        "LiquidationAggregationScope",
        "LiquidationPositionSide",
        "LiquidationZeroIntervalState",
    ):
        assert name in sensors.__all__, name
        assert hasattr(sensors, name), name


def test_sealed_trees_are_untouched_relative_to_the_i11_base() -> None:
    diff = _git(
        "diff",
        I11_BASE_HEAD,
        "--",
        "src/crypto_sensor_fabric/normalization/identity",
        "src/crypto_sensor_fabric/normalization/terms",
        "src/crypto_sensor_fabric/normalization/time",
        "src/crypto_sensor_fabric/normalization/common",
        "src/crypto_sensor_fabric/normalization/__init__.py",
        "src/crypto_sensor_fabric/normalization/enums.py",
        "src/crypto_sensor_fabric/normalization/models.py",
        "src/crypto_sensor_fabric/registry",
        "src/crypto_sensor_fabric/schemas",
        "config/crypto_sensor_fabric",
    )
    assert diff == "", f"sealed tree changed:\n{diff}"


def test_the_frozen_plan_is_byte_identical_to_the_i11_base() -> None:
    diff = _git("diff", I11_BASE_HEAD, "--", "research/crypto_foundry/sensor_fabric/bloc_05")
    assert diff == "", diff


# ---------------------------------------------------------------------------
# A11-05/A11-06 -- the four-way side vocabulary is not re-declared
# ---------------------------------------------------------------------------


def test_no_frozen_enum_is_duplicated_in_the_sensor_tree() -> None:
    for name, text in _sources().items():
        for forbidden in (
            "class AggressorSide(",
            "class SensorFamily(",
            "class AggregationType(",
            "class LiquidationRole(",
            "class NormalizationStatus(",
            "class MissingnessReason(",
            "class NormalizationQualityFlag(",
        ):
            assert forbidden not in text, f"{name} re-declares {forbidden}"


def test_the_frozen_position_side_and_scope_tokens_are_exact() -> None:
    from crypto_sensor_fabric.normalization.sensors import (
        LiquidationAggregationScope,
        LiquidationPositionSide,
    )

    assert sorted(member.value for member in LiquidationPositionSide) == [
        "LONG",
        "SHORT",
        "UNKNOWN",
    ]
    assert sorted(member.value for member in LiquidationAggregationScope) == [
        "EVENT_LEVEL",
        "INTERVAL_AGGREGATE",
        "PROVIDER_MULTI_EVENT_AGGREGATE",
        "TRADE_LEVEL",
        "UNKNOWN",
    ]


# ---------------------------------------------------------------------------
# Purity, dependency firewall, and the I17 boundary
# ---------------------------------------------------------------------------


def test_no_network_or_provider_import() -> None:
    imported: set[str] = set()
    for text in _sources().values():
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    imported.add("." * node.level + (node.module or ""))
                elif node.module:
                    imported.add(node.module)
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib.request",
        "urllib3",
        "websockets",
        "ccxt",
        "crypto_sensor_fabric.providers",
        "crypto_sensor_fabric.probes.runner",
    ):
        assert forbidden not in imported, forbidden


def test_no_filesystem_or_backend_import() -> None:
    for name, text in _sources().items():
        for forbidden in (
            "import pathlib",
            "import os",
            "import duckdb",
            "import pyarrow",
            "import pandas",
            "import sqlite3",
            "import yaml",
        ):
            assert forbidden not in text, f"{name} imports {forbidden}"


def test_no_hashing_id_generation_or_wall_clock() -> None:
    for name, text in _sources().items():
        for forbidden in (
            "hashlib",
            "sha256(",
            "uuid4",
            "datetime.now",
            "datetime.utcnow",
            "time.time",
            "date.today",
            "import random",
            "import secrets",
        ):
            assert forbidden not in text, f"{name} references {forbidden}"


def test_no_duplicate_collapse_engine_exists() -> None:
    for name, text in _sources().items():
        for forbidden in (
            "def collapse",
            "def dedupe",
            "def deduplicate",
            "def fingerprint",
        ):
            assert forbidden not in text, f"{name} ships {forbidden}"


def test_the_liquidation_module_never_derives_side_from_price() -> None:
    """F17: a side is evidence, never a function of the tape (04 section 3.1)."""
    text = (_SENSORS / "liquidation.py").read_text(encoding="utf-8")
    for forbidden in (
        "price >",
        "price <",
        "price >=",
        "price <=",
        "sign(",
        "momentum",
    ):
        assert forbidden not in text, forbidden


def test_no_gate_language_in_the_sensor_tree() -> None:
    for name, text in _sources().items():
        for forbidden in ("OPERATOR_ACCEPTED", "IMPLEMENTATION_PASS", "_GATE ="):
            assert forbidden not in text, f"{name} references {forbidden}"


# ---------------------------------------------------------------------------
# A11-23 -- no program gate promotion
# ---------------------------------------------------------------------------


def test_no_program_gate_is_promoted() -> None:
    matrix = json.loads(
        (_EVIDENCE / "BLOC_05_I01_TYPE_SCOPE_MATRIX.json").read_text(encoding="utf-8")
    )
    gates = matrix["bloc_05_blocking_gates"]
    for gate, verdict in gates.items():
        if gate == "note":
            continue
        assert verdict == "NOT_YET_EARNED", gate
    assert "PASS" not in json.dumps(gates)


def test_i11_adds_no_generated_bloc_05_json_artifact() -> None:
    before = {
        line.rsplit("/", 1)[-1]
        for line in _git(
            "ls-tree",
            "-r",
            "--name-only",
            I11_BASE_HEAD,
            "--",
            "research/crypto_foundry/sensor_fabric/evidence/bloc_05",
        ).splitlines()
        if line.strip()
    }
    after = {path.name for path in _EVIDENCE.iterdir()}
    added = {
        name for name in after - before if name.startswith("bloc_05_") and name.endswith(".json")
    }
    assert added == set(), f"invented evidence artifacts: {sorted(added)}"
