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
    """B5-I03B/C reconciliation (I03 directive 54 custody law: the only history
    permitted to touch this file is the module-list update): the package now
    holds the sealed I02 set PLUS the four exactly-frozen I03 modules.  The
    I03 negative-scope suite (test_b5_i03_scope_audit.py) now owns the live
    module-list law; this file keeps guarding the I04+ tree."""
    files = sorted(
        entry.name for entry in _IDENTITY.iterdir() if entry.suffix == ".py"
    )
    assert files == [
        "__init__.py",
        "aliases.py",   # B5-I03
        "enums.py",     # B5-I03 (frozen I03 vocabularies)
        "lifecycle.py",  # B5-I03
        "models.py",
        "registry.py",
        "resolver.py",  # B5-I03
    ]


def test_no_enums_module_exists() -> None:
    """RECONCILED in B5-I03B: no fully frozen I02-owned vocabulary existed at
    I02, so no enums.py was created then (payoff_type is the reused I01 enum).
    B5-I03's three exactly-frozen vocabularies now live in identity/enums.py;
    the audit trail lives in BLOC_05_I03_VOCABULARY_AUTHORITY_MATRIX.json.
    The law that remains I02-owned: the I02 audited fields (asset_type etc.)
    must STILL be opaque tokens, never new enum members here."""
    assert (_IDENTITY / "enums.py").exists()  # now the I03 frozen vocabularies
    sources = "\n".join(_identity_sources().values())
    for still_opaque in ("class AssetType", "class InstrumentType", "class PerpetualOrDelivery"):
        assert still_opaque not in sources, still_opaque


@pytest.mark.parametrize(
    "forbidden",
    [
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
def test_forbidden_b5_i04_plus_module_is_absent(forbidden: str) -> None:
    """RECONCILED in B5-I03C: resolver.py/lifecycle.py/aliases.py are now the
    IMPLEMENTED B5-I03 modules; the I04+ tree (terms/universe/evidence/
    conversion/availability/replay/writer/query) must not exist yet."""
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
# B5-I03 vocabulary (IMPLEMENTED by B5-I03B/C, reconciled); B5-I04+ stays out
# (directive §24-§27 as amended by the I03 authorization)
# ---------------------------------------------------------------------------


def test_b5_i04_plus_classes_are_absent_from_identity_sources() -> None:
    """RECONCILED in B5-I03C: the I03 classes (InstrumentAlias, AliasType,
    LifecycleState, IdentityResolution*, resolve_instrument, lifecycle values)
    are now IMPLEMENTED law.  What this I02-owned audit keeps enforcing: the
    B5-I04+ machinery (universe, terms snapshots, writer, T1 writers) and the
    VenueScope / MULTI_VENUE_AGGREGATE vocabulary (still a I02-matrix
    operator-decision boundary) stay absent."""
    sources = "\n".join(_identity_sources().values())
    for absent in (
        "class UniverseMembership",
        "class ContractTermsSnapshot",
        "class InstrumentLifecycleState",  # never renamed; LifecycleState is frozen
        "class T1Writer",
        "def write_t1",
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
