"""SENSOR-B5-I01C — negative scope audit for the Bloc 5 normalization base layer.

A checkpoint that proves what it added has also to prove what it did not.  Every
later-checkpoint concern is listed in ``BLOC_05_I01_TYPE_SCOPE_MATRIX.json`` as a
deferred row, and this module turns that deferral into machine-enforced law: the
forbidden modules must not exist, the forbidden imports must not appear in the
production source, and nothing may reach the network or the filesystem.

The audit is deliberately about *source text*, not runtime behaviour: a name
appearing anywhere in the B5-I01 production files is a finding, so a helper can
never be quietly added later without failing here.

OFFLINE.  ``network_calls = 0``.
"""

from __future__ import annotations

import ast
import importlib
import json
import socket
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_SRC = _HERE.parents[2] / "src"
_QUANT_LAB = _HERE.parents[2]
_EVIDENCE = (
    _QUANT_LAB
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_05"
)
SCOPE_MATRIX = _EVIDENCE / "BLOC_05_I01_TYPE_SCOPE_MATRIX.json"

PACKAGE = _SRC / "crypto_sensor_fabric" / "normalization"
PRODUCTION_FILES = (
    PACKAGE / "__init__.py",
    PACKAGE / "enums.py",
    PACKAGE / "models.py",
)


def _sources() -> dict[str, str]:
    return {path.name: path.read_text(encoding="utf-8") for path in PRODUCTION_FILES}


# ---------------------------------------------------------------------------
# The package exists, and is exactly the three authorized modules
# ---------------------------------------------------------------------------


def test_package_exists_with_exactly_three_modules() -> None:
    """§27: __init__.py, enums.py, models.py. No later directory or module."""
    assert PACKAGE.is_dir()
    files = sorted(
        entry.name
        for entry in PACKAGE.iterdir()
        if entry.is_file() and entry.suffix == ".py"
    )
    assert files == ["__init__.py", "enums.py", "models.py"]


def test_no_subpackage_directory_exists() -> None:
    assert not [
        entry
        for entry in PACKAGE.iterdir()
        if entry.is_dir() and entry.name != "__pycache__"
    ]


@pytest.mark.parametrize(
    "forbidden",
    [
        # frozen doc 05 §16 module plans, none of which is authorized at I01
        "identity",
        "time",
        "sensors",
        "common",
        # named explicitly by the B5-I01 directive
        "registry.py",
        "resolver.py",
        "terms.py",
        "conversion.py",
        "aliases.py",
        "lifecycle.py",
        "universe.py",
        "availability.py",
        "intervals.py",
        "revision_policy.py",
        "replay_gate.py",
        "semantics_registry.py",
        "methodologies.py",
        "comparability.py",
        "missingness.py",
        "writer.py",
        "query.py",
        "generations.py",
        "manifests.py",
        "trades.py",
        "liquidations.py",
        "open_interest.py",
        "funding.py",
        "books.py",
        "book_metrics.py",
        "positioning.py",
        "basis.py",
        "provider_side_maps.py",
    ],
)
def test_forbidden_module_is_absent(forbidden: str) -> None:
    assert not (PACKAGE / forbidden).exists(), f"{forbidden} must not exist at B5-I01"


def test_no_sensor_normalizer_or_t1_writer_symbol_exists() -> None:
    normalization = importlib.import_module("crypto_sensor_fabric.normalization")
    for absent in (
        "TradeNormalizer",
        "LiquidationNormalizer",
        "OpenInterestNormalizer",
        "FundingNormalizer",
        "BookNormalizer",
        "BookMetricNormalizer",
        "PositioningNormalizer",
        "BasisNormalizer",
        "write_t1",
        "publish_generation",
        "query_t1",
        "T1Writer",
        "T1Store",
    ):
        assert not hasattr(normalization, absent)


# ---------------------------------------------------------------------------
# Forbidden imports
# ---------------------------------------------------------------------------


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


def test_no_provider_adapter_or_network_library_is_imported() -> None:
    """§29/§30: no provider call, no HTTP client, no socket, no live network."""
    imported = _imported_modules()
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "urllib.request",
        "urllib3",
        "socket",
        "http",
        "ftplib",
        "smtplib",
        "websockets",
        "ccxt",
        "aiofiles",
    ):
        assert forbidden not in imported, f"network import {forbidden}"
    for forbidden in ("crypto_sensor_fabric.providers", "crypto_sensor_fabric.probes.runner"):
        assert forbidden not in imported, f"provider import {forbidden}"


def test_no_storage_backend_or_path_module_is_imported() -> None:
    """§29: only accepted public contract TYPES, never a backend or a path."""
    imported = _imported_modules()
    for forbidden in (
        "pathlib",
        "os",
        "glob",
        "duckdb",
        "pyarrow",
        "pandas",
        "psycopg",
        "sqlalchemy",
        "sqlite3",
        "shutil",
    ):
        assert forbidden not in imported, f"filesystem/backend import {forbidden}"


def test_no_private_bloc4_module_is_imported() -> None:
    """bloc_04/I17 §12/§13: the public surface is the whole dependency."""
    imported = _imported_modules()
    for forbidden in (
        "crypto_sensor_fabric.storage.checksums",
        "crypto_sensor_fabric.storage.duckdb_catalog",
        "crypto_sensor_fabric.storage.models",
        "crypto_sensor_fabric.storage.blob_store",
        "crypto_sensor_fabric.storage.catalog",
        "crypto_sensor_fabric.storage.paths",
        "crypto_sensor_fabric.storage.manifests",
        "crypto_sensor_fabric.storage.query",
        "crypto_sensor_fabric.storage.replay",
        "crypto_sensor_fabric._paths",
    ):
        assert forbidden not in imported, f"private Bloc 4 import {forbidden}"


def test_only_accepted_public_bloc4_names_are_consumed() -> None:
    """Every accepted upstream import must be a documented public symbol."""
    imported = _imported_modules()
    allowed = {
        ".contracts.base",
        ".contracts.enums",
        ".probes.enums",
        ".storage",
        ".enums",
        ".models",
        "__future__",
        "json",
        "re",
        "datetime",
        "decimal",
        "enum",
        "types",
        "typing",
        "pydantic",
    }
    assert imported <= allowed, f"unexpected imports: {sorted(imported - allowed)}"


def test_storage_is_consumed_through_its_public_package() -> None:
    import crypto_sensor_fabric.storage as storage

    imported = _imported_modules()
    assert ".storage" in imported
    # The three storage names the base layer consumes are public contract.
    for name in (
        "CoverageState",
        "RevisionState",
        "SourceUnitContract",
        "SourceUnitEvidence",
    ):
        assert name in storage.__all__


def test_no_filesystem_or_catalog_knowledge_appears_in_the_source() -> None:
    """§29 / bloc_04/I17 §12: no path, layout or DuckDB knowledge in text."""
    for name, text in _sources().items():
        for forbidden in (
            "duckdb",
            "parquet",
            "blob_root",
            "manifest_path",
            "catalog_dir",
            "os.path",
            "Path(",
            "open(",
        ):
            assert forbidden not in text, f"{name} references {forbidden}"


def test_no_hashing_or_id_generation_is_present() -> None:
    """§18/§19: no identity algorithm and no generation checksum at I01."""
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


# ---------------------------------------------------------------------------
# Zero network
# ---------------------------------------------------------------------------


def test_importing_the_package_makes_no_connection(monkeypatch: pytest.MonkeyPatch) -> None:
    """§30: importing the base layer must not touch the network at all."""
    calls: list[object] = []

    def _refuse(*args: object, **kwargs: object) -> None:
        calls.append((args, kwargs))
        raise AssertionError("network access attempted during import")

    monkeypatch.setattr(socket, "socket", _refuse)
    monkeypatch.setattr(socket, "create_connection", _refuse)
    for module_name in list(sys.modules):
        if module_name.startswith("crypto_sensor_fabric.normalization"):
            monkeypatch.delitem(sys.modules, module_name, raising=False)
    module = importlib.import_module("crypto_sensor_fabric.normalization")
    assert module.T1BaseEnvelope is not None
    assert calls == []


def test_no_marked_network_test_exists_in_this_package() -> None:
    """A base layer has no live path to opt into.

    The marker name appears in this very module (as the thing being banned), so
    this file names what it forbids and is itself excluded; the check applies to
    every OTHER module in the package.
    """
    for path in sorted(_HERE.glob("test_*.py")):
        if path.name == Path(__file__).name:
            continue
        text = path.read_text(encoding="utf-8")
        assert "@pytest.mark.sensor_network_smoke" not in text, path.name
        assert "SENSOR_NETWORK_SMOKE" not in text, path.name


# ---------------------------------------------------------------------------
# The type-scope matrix is the contract, and it agrees with the source
# ---------------------------------------------------------------------------


def test_scope_matrix_is_committed_and_self_consistent() -> None:
    assert SCOPE_MATRIX.exists(), "the B5-I01 type-scope matrix is missing"
    matrix = json.loads(SCOPE_MATRIX.read_text(encoding="utf-8"))
    rows = matrix["rows"]
    assert len(rows) == matrix["summary"]["rows_total"]
    assert sum(1 for row in rows if row["needed_for_I01"]) == (
        matrix["summary"]["needed_for_I01_true"]
    )
    assert sum(1 for row in rows if not row["needed_for_I01"]) == (
        matrix["summary"]["needed_for_I01_false"]
    )
    names = [row["type_name"] for row in rows]
    assert len(set(names)) == len(names), "duplicate type_name row"
    for row in rows:
        assert row["kind"] in {"enum", "model", "data", "type", "helper"}
        assert row["source_plan_section"], row["type_name"]
        assert row["reason"], row["type_name"]
        if row["needed_for_I01"]:
            assert row["deferred_checkpoint"] == ""
        else:
            assert row["deferred_checkpoint"].startswith("SENSOR-B5-I")


def test_every_implemented_public_symbol_has_a_matrix_row() -> None:
    normalization = importlib.import_module("crypto_sensor_fabric.normalization")
    matrix = json.loads(SCOPE_MATRIX.read_text(encoding="utf-8"))
    implemented = {row["type_name"] for row in matrix["rows"] if row["needed_for_I01"]}
    for name in normalization.__all__:
        assert name in implemented, f"{name} is exported but not justified by the matrix"


def test_every_deferred_type_is_absent_from_the_source() -> None:
    """A deferred row must not be quietly implemented anyway."""
    matrix = json.loads(SCOPE_MATRIX.read_text(encoding="utf-8"))
    sources = "\n".join(_sources().values())
    for row in matrix["rows"]:
        if row["needed_for_I01"]:
            continue
        name = row["type_name"]
        # A prefix collision (T1Lineage vs T1LineageRef) must not read as an
        # implementation, so require the declaration form itself.
        assert f"class {name}(" not in sources, f"deferred model {name} was implemented"
        assert f"class {name}:" not in sources, f"deferred model {name} was implemented"


def test_all_eight_bloc5_gates_are_recorded_as_not_yet_earned() -> None:
    """§34: vocabulary earns no gate, and claiming one would be a lie."""
    matrix = json.loads(SCOPE_MATRIX.read_text(encoding="utf-8"))
    gates = matrix["bloc_05_blocking_gates"]
    assert set(gates) - {"note"} == {
        "IDENTITY_GATE",
        "TIME_GATE",
        "SEMANTIC_GATE",
        "UNIT_GATE",
        "LINEAGE_GATE",
        "DUPLICATE_REVISION_GATE",
        "REPLAY_SAFETY_GATE",
        "GOLDEN_T0_T1_GATE",
    }
    for gate, verdict in gates.items():
        if gate == "note":
            continue
        assert verdict == "NOT_YET_EARNED", f"{gate} must not be claimed at B5-I01"
    assert "PASS" not in json.dumps(gates)


def test_matrix_records_the_measured_vocabulary_gaps_instead_of_inventing() -> None:
    """§41: a gap requiring an operator choice is recorded, not filled."""
    matrix = json.loads(SCOPE_MATRIX.read_text(encoding="utf-8"))
    deferred = {
        row["type_name"]: row for row in matrix["rows"] if not row["needed_for_I01"]
    }
    for gap in ("AvailabilityConfidence", "VenueScope"):
        assert gap in deferred
        assert "NOT FROZEN" in deferred[gap]["reason"]