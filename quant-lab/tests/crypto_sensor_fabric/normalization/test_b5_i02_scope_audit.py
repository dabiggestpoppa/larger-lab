"""SENSOR-B5-I02 — negative scope audit for the identity subpackage.

Machine-enforced law for what B5-I02 did NOT build: no resolver, no alias,
no lifecycle, no universe, no terms behavior, no network, no filesystem, no
metadata backcast, and the ratified I01 vocabulary gaps stay gaps.  The
checks are source-text based, mirroring the I01 audit's discipline.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_QUANT_LAB = _HERE.parents[2]
_EVIDENCE = (
    _QUANT_LAB / "research" / "crypto_foundry" / "sensor_fabric" / "evidence" / "bloc_05"
)
I01_SCOPE_MATRIX = _EVIDENCE / "BLOC_05_I01_TYPE_SCOPE_MATRIX.json"
VOCAB_MATRIX = _EVIDENCE / "BLOC_05_I02_VOCABULARY_AUTHORITY_MATRIX.json"

_IDENTITY = _QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization" / "identity"


def _identity_sources() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(_IDENTITY.glob("*.py"))
    }


# ---------------------------------------------------------------------------
# Package shape (directive §28)
# ---------------------------------------------------------------------------


def test_identity_package_is_exactly_the_authorized_modules() -> None:
    files = sorted(
        entry.name for entry in _IDENTITY.iterdir() if entry.suffix == ".py"
    )
    assert files == ["__init__.py", "models.py", "registry.py"]


def test_no_enums_module_exists() -> None:
    """No fully frozen I02-owned vocabulary exists (vocabulary matrix), so no
    identity/enums.py was created; payoff_type is the reused I01 enum."""
    assert not (_IDENTITY / "enums.py").exists()


@pytest.mark.parametrize(
    "forbidden",
    [
        "resolver.py",
        "lifecycle.py",
        "aliases.py",
        "terms.py",
        "universe.py",
        "evidence.py",
        "conversion.py",
        "availability.py",
        "replay_gate.py",
        "writer.py",
        "query.py",
    ],
)
def test_forbidden_b5_i03_plus_module_is_absent(forbidden: str) -> None:
    assert not (_IDENTITY / forbidden).exists()


# ---------------------------------------------------------------------------
# Forbidden imports and behaviors in identity sources
# ---------------------------------------------------------------------------


def _imported_modules() -> set[str]:
    found: set[str] = set()
    for text in _identity_sources().values():
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                found.add(("." * node.level) + module)
    return found


def test_no_network_or_provider_imports() -> None:
    imported = _imported_modules()
    for forbidden in (
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "urllib.request",
        "ccxt",
        "websockets",
        "crypto_sensor_fabric.providers",
    ):
        assert forbidden not in imported, forbidden


def test_no_filesystem_or_backend_imports() -> None:
    """Serialization is text-in/text-out: no path knowledge, no storage."""
    imported = _imported_modules()
    for forbidden in ("pathlib", "os", "glob", "duckdb", "sqlite3", "shutil"):
        assert forbidden not in imported, forbidden


def test_yaml_is_used_only_for_serialization() -> None:
    """The single yaml consumer is registry.py's text serializer."""
    for name, text in _identity_sources().items():
        if name == "registry.py":
            assert "import yaml" in text
        else:
            assert "import yaml" not in text, name


def test_no_id_generation_or_wall_clock() -> None:
    for name, text in _identity_sources().items():
        for forbidden in (
            "hashlib",
            "sha256(",
            "uuid",
            "datetime.now",
            "datetime.utcnow",
            "time.time",
            "random",
            "secrets",
        ):
            assert forbidden not in text, f"{name} references {forbidden}"


def test_no_current_metadata_backcast() -> None:
    """Directive §23: no latest()/current() fallback may answer a historical
    query from current metadata (bloc_05/01 §5/§10)."""
    for name, text in _identity_sources().items():
        for forbidden in ("latest(", "current(", "fallback_to_current", ".latest"):
            assert forbidden not in text, f"{name} references {forbidden}"


def test_no_path_or_open_calls_in_source_text() -> None:
    for name, text in _identity_sources().items():
        for forbidden in ("open(", "Path(", "os.path", "read_text", "write_text"):
            assert forbidden not in text, f"{name} references {forbidden}"


# ---------------------------------------------------------------------------
# B5-I03+ vocabulary stays unimplemented (directive §24/§25/§26/§27)
# ---------------------------------------------------------------------------


def test_b5_i03_plus_classes_are_absent_from_identity_sources() -> None:
    sources = "\n".join(_identity_sources().values())
    for absent in (
        "class InstrumentAlias",
        "class AliasType",
        "class InstrumentLifecycle",
        "class InstrumentLifecycleState",
        "class IdentityResolution",
        "class IdentityResolutionStatus",
        "class UniverseMembership",
        "class ContractTermsSnapshot",
        "class LifecycleState",
        "def resolve_instrument",
        "PRE_LISTING",
        "DELISTING_ANNOUNCED",
        "RELISTED_NEW_INSTANCE",
        "MULTI_VENUE_AGGREGATE",
    ):
        assert absent not in sources, absent


# ---------------------------------------------------------------------------
# Vocabulary authority matrix is the contract (directive §3/§36/§37)
# ---------------------------------------------------------------------------


def test_vocabulary_matrix_is_self_consistent() -> None:
    matrix = json.loads(VOCAB_MATRIX.read_text(encoding="utf-8"))
    rows = matrix["rows"]
    assert len(rows) == matrix["summary"]["audited_fields"]
    frozen = [row for row in rows if row["frozen_vocabulary_exists"]]
    assert len(frozen) == matrix["summary"]["frozen_vocabularies_reused"]
    for row in rows:
        assert row["decision"], row["field_name"]


def test_venuescope_decision_is_recorded_not_implemented() -> None:
    matrix = json.loads(VOCAB_MATRIX.read_text(encoding="utf-8"))
    row = next(r for r in matrix["rows"] if r["field_name"] == "VenueScope")
    assert row["frozen_vocabulary_exists"] is False
    assert row["decision"].startswith("VENUESCOPE_DECISION = NOT_REQUIRED_DEFERRED")
    sources = "\n".join(_identity_sources().values())
    assert "VenueScope" not in sources


def test_payoff_type_is_reused_not_redefined() -> None:
    from crypto_sensor_fabric.normalization.enums import PayoffType as base

    sources = "\n".join(_identity_sources().values())
    assert "class PayoffType" not in sources
    identity = __import__(
        "crypto_sensor_fabric.normalization.identity", fromlist=["ContractInstance"]
    )
    instance_type = identity.ContractInstance.model_fields["payoff_type"].annotation
    assert instance_type is base


def test_i01_matrix_and_gates_untouched() -> None:
    """B5-I02 earns no gate and may not edit the I01 scope matrix."""
    matrix = json.loads(I01_SCOPE_MATRIX.read_text(encoding="utf-8"))
    for gate, verdict in matrix["bloc_05_blocking_gates"].items():
        if gate == "note":
            continue
        assert verdict == "NOT_YET_EARNED", gate
