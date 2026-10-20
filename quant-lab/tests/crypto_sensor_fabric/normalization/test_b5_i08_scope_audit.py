"""SENSOR-B5-I08E1 - RED-first scope audit + evidence determinism (U08-19/U08-20).

A checkpoint that proves what it added has also to prove what it did not.
This is the I08 counterpart of the I01/I02/I03/I05 scope audits: the frozen
``common/`` surface (bloc_05/03 §21 read against 06 §19's I08 title and the
I08-Q1 scope split recorded in ``BLOC_05_I08_IMPLEMENTATION_EVIDENCE.md``)
is present, and NOTHING else changed -- not the ratified I01 top-level API,
not the identity/terms/time packages, not the sealed I04B conversion module,
not the frozen plan, and no program gate.

The single authorized extension to pre-existing tests is disclosed here on
the established I02/I04A/I05 precedent: the B5-I01 and B5-I05 scope audits'
subpackage allowlists now name ``common`` (bloc_05/03 §21 freezes
``normalization/common/`` as required I08 surface).

U08-20 additionally re-measures the deterministic unit-validation evidence
producer: two invocations emit byte-identical JSON.

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
_COMMON = _PACKAGE / "common"
_EVIDENCE = (
    _QUANT_LAB
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_05"
)
_PRODUCTION_FILES = (
    _COMMON / "__init__.py",
    _COMMON / "units.py",
    _COMMON / "numeric.py",
    _COMMON / "conversion.py",
)

#: I08's frozen module set.  envelope.py is deliberately ABSENT: bloc_05/03
#: §2's full ``T1ObservationEnvelope`` requires methodology identity owned by
#: I09 (06 §19), so the frozen-name composite stays unexported exactly as the
#: I01 base layer records.  methodologies.py / semantic_registry.py are I09's
#: (06 §19: "methodology + semantic-equivalence registries").  comparability.py
#: and missingness.py are not part of the I08 directive scope.
FROZEN_MODULES = ["__init__.py", "conversion.py", "numeric.py", "units.py"]

#: Directive custody base for this checkpoint.
I08_BASE_HEAD = "88373c01cbfc41ac8edda5fe082d9e9d3db5f234"


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
    return {path.name: path.read_text(encoding="utf-8") for path in _PRODUCTION_FILES}


def _imported_modules() -> set[str]:
    found: set[str] = set()
    for text in _sources().values():
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    found.add(f".{node.module or ''}")
                elif node.module:
                    found.add(node.module)
    return found


# ---------------------------------------------------------------------------
# U08-19 -- the frozen surface is exactly what the plan froze, and nothing more
# ---------------------------------------------------------------------------


def test_common_package_exists() -> None:
    assert _COMMON.is_dir(), "bloc_05/03 §21 requires normalization/common/"


def test_common_package_is_exactly_the_frozen_modules() -> None:
    files = sorted(entry.name for entry in _COMMON.iterdir() if entry.suffix == ".py")
    assert files == FROZEN_MODULES


def test_i09_and_deferred_modules_are_absent() -> None:
    """06 §19 gives I09 the methodology + semantic-equivalence registries;
    comparability/missingness are out of I08 scope; a bare module beside the
    package would shadow the authorized subpackage."""
    for forbidden in (
        "methodologies.py",
        "semantic_registry.py",
        "comparability.py",
        "missingness.py",
        "envelope.py",
        "sensors",
        "lineage",
        "duplicates",
        "quality",
        "storage",
        "query",
    ):
        assert not (_PACKAGE / forbidden).exists(), forbidden
        assert not (_COMMON / forbidden).exists(), forbidden


def test_ratified_i01_top_level_api_is_unchanged() -> None:
    """The top-level normalization surface stays the ratified 24 symbols;
    I08 names are reached only through ``...normalization.common``."""
    import crypto_sensor_fabric.normalization as normalization

    assert len(normalization.__all__) == 24
    for absent in (
        "CanonicalQuantityUnit",
        "convert_stablecoin_to_usd",
        "CrossCurrencyResult",
    ):
        assert absent not in normalization.__all__


def test_terms_time_identity_packages_are_untouched_by_i08() -> None:
    """Sealed I02/I04B/I05 trees: no I08 edit reached them."""
    diff = _git("diff", I08_BASE_HEAD, "--", "src/crypto_sensor_fabric/normalization")
    changed_paths = sorted(
        line
        for line in diff.splitlines()
        if line.startswith("diff --git")
    )
    for line in changed_paths:
        assert "/common/" in line, f"non-common source change: {line}"


def test_no_network_or_provider_import() -> None:
    imported = _imported_modules()
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
    """Units/numeric conversion are pure: value in, answer out."""
    imported = _imported_modules()
    for forbidden in (
        "pathlib",
        "os",
        "glob",
        "duckdb",
        "pyarrow",
        "pandas",
        "sqlite3",
        "shutil",
    ):
        assert forbidden not in imported, forbidden


def test_no_hashing_id_generation_or_wall_clock() -> None:
    for name, text in _sources().items():
        for forbidden in (
            "hashlib",
            "sha256(",
            "uuid",
            "uuid4",
            "datetime.now",
            "datetime.utcnow",
            "time.time",
            "random",
            "secrets",
        ):
            assert forbidden not in text, f"{name} references {forbidden}"


def test_no_program_gate_is_claimed() -> None:
    """Eight gates stay NOT_YET_EARNED; UNIT_GATE is earned by the acceptance
    layer (06 §21), never by an implementation checkpoint."""
    matrix = json.loads(
        (_EVIDENCE / "BLOC_05_I01_TYPE_SCOPE_MATRIX.json").read_text(encoding="utf-8")
    )
    gates = matrix["bloc_05_blocking_gates"]
    for gate, verdict in gates.items():
        if gate == "note":
            continue
        assert verdict == "NOT_YET_EARNED", gate


# ---------------------------------------------------------------------------
# U08-20 -- deterministic unit-validation evidence
# ---------------------------------------------------------------------------


def test_unit_validation_evidence_is_deterministic(tmp_path: Path) -> None:
    """The tracked producer emits byte-identical bytes across invocations."""
    script = (
        _QUANT_LAB
        / "research"
        / "crypto_foundry"
        / "sensor_fabric"
        / "scripts"
        / "b5_i08_units.py"
    )
    assert script.is_file(), "the tracked I08 evidence producer is missing"
    outputs = []
    import os
    import sys

    for _ in range(2):
        result = subprocess.run(
            [sys.executable, str(script), "--check"],
            cwd=_QUANT_LAB,
            capture_output=True,
            check=False,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        assert result.returncode == 0, result.stdout.decode(
            "utf-8", "replace"
        ) + result.stderr.decode("utf-8", "replace")
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1], "producer output is not deterministic"
    sha = json.loads(outputs[0].decode("utf-8"))["artifact_sha256"]
    artifact = _EVIDENCE / "bloc_05_unit_validation.json"
    import hashlib

    measured = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert sha == measured, "committed artifact does not match the producer hash"
