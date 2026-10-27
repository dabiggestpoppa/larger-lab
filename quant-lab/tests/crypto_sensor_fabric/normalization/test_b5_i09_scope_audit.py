"""SENSOR-B5-I09E1 - scope audit + evidence determinism (SEM-A01..SEM-A09).

The I09 counterpart of the I08 scope audit: the frozen ``common/`` surface now
carries the I09 modules (03 §21's remaining required modules, 06 §19's I09
title), and NOTHING else changed -- not the ratified I01 top-level API, not the
identity/terms/time packages, not the sealed Bloc 1 registry surface, not the
frozen plan, and no program gate.

The single authorized extension to pre-existing tests is disclosed here on the
established I02/I04A/I05/I08 precedent: the I08 scope audit's frozen module
set grows from four to seven and its deferred-module list loses exactly the
three modules this directive owns; the I05 scope audit's staged allowlist gains
``test_b5_i09``.

OFFLINE.  No network, no wall clock, no filesystem writes.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_QUANT_LAB = _HERE.parents[2]
_PACKAGE = _QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization"
_COMMON = _PACKAGE / "common"
_EVIDENCE = (
    _QUANT_LAB / "research" / "crypto_foundry" / "sensor_fabric" / "evidence" / "bloc_05"
)

#: The frozen common/ module set AFTER the disclosed I09 extension (I08's four
#: plus the three modules 06 §19 assigns to I09).  ``envelope.py`` and
#: ``missingness.py`` stay deliberately ABSENT (BOOK 00 Q4; readiness §6
#: re-export law).
FROZEN_MODULES = [
    "__init__.py",
    "comparability.py",
    "conversion.py",
    "methodologies.py",
    "numeric.py",
    "semantic_registry.py",
    "units.py",
]

#: I09 custody base.
I09_BASE_HEAD = "1f7a0fa6ab55b022ce3a9900717b6d3c657cc477"


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


def test_sem_a01_common_package_is_exactly_the_frozen_modules() -> None:
    """03 §21's eight required modules, as scoped across I08 + I09: exactly
    seven files, no eighth."""
    assert _COMMON.is_dir()
    files = sorted(entry.name for entry in _COMMON.iterdir() if entry.suffix == ".py")
    assert files == FROZEN_MODULES


def test_sem_a02_only_deliberately_absent_modules_remain_absent() -> None:
    """Q4 keeps the frozen composite name unexported; 05 §12 keeps missingness
    a reuse, not a fork; the sensor normalizers stay I10+."""
    for forbidden in (
        "envelope.py",
        "missingness.py",
        "sensors",
        "lineage",
        "duplicates",
        "quality",
        "storage",
        "query",
    ):
        assert not (_PACKAGE / forbidden).exists(), forbidden
        assert not (_COMMON / forbidden).exists(), forbidden


def test_sem_a03_ratified_i01_top_level_api_is_unchanged() -> None:
    import crypto_sensor_fabric.normalization as normalization

    assert len(normalization.__all__) == 24
    for absent in ("NormalizationMethodology", "ProviderSemanticMapping", "MethodologyRef"):
        assert absent not in normalization.__all__, absent


def test_sem_a04_sealed_trees_are_untouched_relative_to_the_i09_base() -> None:
    """06 §20 custody: the identity/terms/time packages, the top-level modules
    and the Bloc 1 registry surface are byte-identical to the I09 base."""
    diff = _git(
        "diff",
        I09_BASE_HEAD,
        "--",
        "src/crypto_sensor_fabric/normalization/identity",
        "src/crypto_sensor_fabric/normalization/terms",
        "src/crypto_sensor_fabric/normalization/time",
        "src/crypto_sensor_fabric/normalization/__init__.py",
        "src/crypto_sensor_fabric/normalization/models.py",
        "src/crypto_sensor_fabric/normalization/enums.py",
        "src/crypto_sensor_fabric/registry",
        "config/crypto_sensor_fabric",
    )
    assert diff == "", f"sealed tree changed:\n{diff}"


def test_sem_a05_prior_evidence_artifacts_are_untouched() -> None:
    """No prior checkpoint's evidence artifact is rewritten by I09 -- including
    the ratified ``bloc_05_unit_validation.json`` and the I05/I06 artifacts
    whose pins the disclosed allowlist cascade re-measures (the cascade
    regenerates only what its own disclosed inventory change forces)."""
    for name in (
        "bloc_05_unit_validation.json",
        "BLOC_05_I08_OPERATOR_RATIFICATION.md",
        "BLOC_05_I09_READINESS_ASSESSMENT.md",
        "BLOC_05_I05_OPERATOR_RATIFICATION.md",
        "BLOC_05_I06_OPERATOR_RATIFICATION.md",
    ):
        diff = _git("diff", I09_BASE_HEAD, "--", f"research/crypto_foundry/sensor_fabric/evidence/bloc_05/{name}")
        assert diff == "", f"{name} changed:\n{diff}"


def test_sem_a06_no_program_gate_is_claimed() -> None:
    matrix = json.loads(
        (_EVIDENCE / "BLOC_05_I01_TYPE_SCOPE_MATRIX.json").read_text(encoding="utf-8")
    )
    gates = matrix["bloc_05_blocking_gates"]
    for gate, verdict in gates.items():
        if gate == "note":
            continue
        assert verdict == "NOT_YET_EARNED", gate


def test_sem_a07_producer_exists_is_tracked_and_has_no_scratch_dependency() -> None:
    """The I09 producer is tracked, imports nothing from a scratch tree, and
    its artifact provenance names the tracked script (I06 provenance law)."""
    import ast

    script = (
        _QUANT_LAB
        / "research"
        / "crypto_foundry"
        / "sensor_fabric"
        / "scripts"
        / "b5_i09_semantics.py"
    )
    assert script.is_file(), "the tracked I09 evidence producer is missing"
    text = script.read_text(encoding="utf-8")
    tree = ast.parse(text)
    offending_imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            offending_imports.extend(
                alias.name for alias in node.names if ".bu_tmp" in alias.name
            )
        elif isinstance(node, ast.ImportFrom) and node.module and ".bu_tmp" in node.module:
            offending_imports.append(node.module)
    assert offending_imports == [], offending_imports
    artifact = json.loads(
        (_EVIDENCE / "bloc_05_semantic_validation.json").read_text(encoding="utf-8")
    )
    provenance = artifact["generator"] + "".join(
        entry["generator"] for entry in artifact["extensions"]
    )
    assert ".bu_tmp" not in provenance, provenance
    assert "b5_i09_semantics.py" in provenance, provenance
    for forbidden in ("datetime.now(", "datetime.utcnow(", "date.today(", "time.time("):
        assert forbidden not in text, forbidden
    listed = _git(
        "ls-files",
        "--error-unmatch",
        "research/crypto_foundry/sensor_fabric/scripts/b5_i09_semantics.py",
    )
    assert listed.strip().endswith("b5_i09_semantics.py"), listed


def test_sem_a08_semantic_validation_evidence_is_deterministic() -> None:
    """The tracked producer emits byte-identical bytes across invocations and
    ``--check`` exits 0 against the committed artifact."""
    import os
    import sys

    script = (
        _QUANT_LAB / "research" / "crypto_foundry" / "sensor_fabric" / "scripts" / "b5_i09_semantics.py"
    )
    outputs = []
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, str(script), "--check"],
            cwd=_QUANT_LAB,
            capture_output=True,
            check=False,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        assert result.returncode == 0, result.stdout.decode("utf-8", "replace") + result.stderr.decode(
            "utf-8", "replace"
        )
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1], "producer output is not deterministic"
    sha = json.loads(outputs[0].decode("utf-8"))["artifact_sha256"]
    import hashlib

    artifact = _EVIDENCE / "bloc_05_semantic_validation.json"
    measured = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert sha == measured, "committed artifact does not match the producer hash"


def test_sem_a09_no_network_or_backend_import_reached_the_pure_layer() -> None:
    import ast

    package = _QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization" / "common"
    found: set[str] = set()
    for module in ("methodologies.py", "semantic_registry.py", "comparability.py", "__init__.py"):
        tree = ast.parse((package / module).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                found.add(node.module)
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib.request",
        "urllib3",
        "websockets",
        "ccxt",
        "duckdb",
        "pyarrow",
        "pandas",
        "sqlite3",
        "crypto_sensor_fabric.providers",
    ):
        assert forbidden not in found, forbidden
