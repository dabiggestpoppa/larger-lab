"""SENSOR-B5-I03 - RED negative-scope audit for the identity subpackage.

Machine-enforced law for what B5-I03 does NOT build: no contract conversion
(B5-I04), no time-semantics/availability/revision machinery (B5-I05..I07), no
fuzzy matching, no network, no filesystem.  Plus evidence-artifact structure
checks over the I03 authority matrix, RED until the I03D artifacts exist.

Source-text based, mirroring the I01/I02 audit discipline.  OFFLINE.
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
VOCAB_MATRIX = _EVIDENCE / "BLOC_05_I03_VOCABULARY_AUTHORITY_MATRIX.json"
I02_VOCAB_MATRIX = _EVIDENCE / "BLOC_05_I02_VOCABULARY_AUTHORITY_MATRIX.json"

_IDENTITY = _QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization" / "identity"


def _identity_sources() -> dict[str, str]:
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(_IDENTITY.glob("*.py"))
    }


# ---------------------------------------------------------------------------
# Package shape (I03 authorized modules only)
# ---------------------------------------------------------------------------


def test_identity_package_is_exactly_the_authorized_modules() -> None:
    """I02-frozen modules + the four authorized B5-I03 modules (plan section 16
    subset; resolver.py/enums.py/lifecycle.py/aliases.py).  RED until B5-I03B/C.
    """
    files = sorted(entry.name for entry in _IDENTITY.iterdir() if entry.suffix == ".py")
    assert files == [
        "__init__.py",
        "aliases.py",
        "enums.py",
        "lifecycle.py",
        "models.py",
        "registry.py",
        "resolver.py",
    ]


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
        "fuzzy.py",
        "manual_mapping.py",
    ],
)
def test_forbidden_b5_i04_plus_module_is_absent(forbidden: str) -> None:
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
    """Resolution is pure: registry snapshot in, answer out.  No storage."""
    imported = _imported_modules()
    for forbidden in ("pathlib", "os", "glob", "duckdb", "sqlite3", "shutil"):
        assert forbidden not in imported, forbidden


def test_no_id_generation_or_wall_clock() -> None:
    """No identity minting and no wall-clock defaults: the resolver takes only
    explicit times (directive 35/36/37)."""
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


def test_no_fuzzy_or_backcast_behavior() -> None:
    for name, text in _identity_sources().items():
        for forbidden in (
            "difflib",
            "rapidfuzz",
            "fuzzywuzzy",
            "Levenshtein",
            "latest(",
            "current(",
            "fallback_to_current",
            ".lower() ==",
        ):
            assert forbidden not in text, f"{name} references {forbidden}"


def test_no_path_or_open_calls_in_source_text() -> None:
    for name, text in _identity_sources().items():
        for forbidden in ("open(", "Path(", "os.path", "read_text", "write_text"):
            assert forbidden not in text, f"{name} references {forbidden}"


# ---------------------------------------------------------------------------
# B5-I04+ vocabulary stays out of I03 sources
# ---------------------------------------------------------------------------


def test_b5_i04_plus_vocabulary_is_absent_from_identity_sources() -> None:
    sources = "\n".join(_identity_sources().values())
    for absent in (
        "class ContractTerm",
        "class T1Writer",
        "def write_t1",
        "def query_t1",
        "effective_at",
        "market_available_at",
        "replay_eligibility",
        "AS_KNOWN_THEN",
        "MULTI_VENUE_AGGREGATE",
    ):
        assert absent not in sources, absent


def test_no_usdt_equals_usd_clause() -> None:
    """Stablecoin firewall (I03 directive 21 / bloc_05/01 section 12): no
    identity substitution logic may exist in source."""
    sources = "\n".join(_identity_sources().values())
    for absent in (
        "USDT\") == \"USD",
        "\"USD\") == \"USDT",
        "substitute_quote",
        "fiat_equivalent",
    ):
        assert absent not in sources, absent


# ---------------------------------------------------------------------------
# Vocabulary authority matrix is the contract (I03 directive 3)
# ---------------------------------------------------------------------------


def test_i03_vocabulary_matrix_is_self_consistent() -> None:
    matrix = json.loads(VOCAB_MATRIX.read_text(encoding="utf-8"))
    rows = matrix["rows"]
    assert len(rows) == matrix["summary"]["audited_vocabularies"]
    frozen = [row for row in rows if row["frozen_vocabulary_exists"]]
    assert len(frozen) == matrix["summary"]["frozen_vocabularies_implemented"]
    for row in rows:
        assert row["decision"], row["field_name"]


def test_i03_confidence_stays_opaque() -> None:
    """Directive 8: no invented confidence scale anywhere in plan-adjacent
    evidence or code."""
    matrix = json.loads(VOCAB_MATRIX.read_text(encoding="utf-8"))
    assert matrix["summary"]["confidence_frozen_vocabulary_found"] is False
    sources = "\n".join(_identity_sources().values())
    for invented in ("HIGH", "MEDIUM", "LOW", "0.8", "0-100"):
        if invented in ("HIGH", "MEDIUM", "LOW"):
            assert invented not in sources or _in_comment_or_token_only(sources, invented)
    assert "confidence_scale" not in sources


def _in_comment_or_token_only(sources: str, token: str) -> bool:
    """HIGH/MEDIUM/LOW must never appear as identifiers that drive behavior."""
    tree_lines = [
        line for line in sources.splitlines()
        if token in line and not line.strip().startswith("#")
    ]
    identifier_hits = [
        line for line in tree_lines
        if f'"{token}"' in line and ("Enum" in line or "class " in line)
    ]
    return not identifier_hits


# ---------------------------------------------------------------------------
# Enum member laws RED until B5-I03B (vocabulary discipline)
# ---------------------------------------------------------------------------


def test_lifecycle_enum_members_red() -> None:
    identity = _identity_sources_import()
    state = getattr(identity, "LifecycleState", None)
    assert state is not None, "RED: LifecycleState not implemented yet"
    assert [m.value for m in state] == [
        "PRE_LISTING",
        "ACTIVE",
        "SUSPENDED",
        "DELISTING_ANNOUNCED",
        "DELISTED",
        "RELISTED_NEW_INSTANCE",
        "UNKNOWN",
    ]  # bloc_05/01 section 6 / F4


def test_alias_type_enum_members_red() -> None:
    identity = _identity_sources_import()
    at = getattr(identity, "AliasType", None)
    assert at is not None, "RED: AliasType not implemented yet"
    assert [m.value for m in at] == [
        "API_SYMBOL",
        "ARCHIVE_SYMBOL",
        "WEBSOCKET_SYMBOL",
        "DISPLAY_SYMBOL",
        "LEGACY_SYMBOL",
        "PROVIDER_INTERNAL_ID",
    ]  # bloc_05/01 section 8


def test_resolution_status_enum_members_red() -> None:
    identity = _identity_sources_import()
    st = getattr(identity, "IdentityResolutionStatus", None)
    assert st is not None, "RED: IdentityResolutionStatus not implemented yet"
    assert [m.value for m in st] == [
        "RESOLVED_EXACT",
        "RESOLVED_ALIAS",
        "RESOLVED_WITH_WARNING",
        "AMBIGUOUS",
        "NOT_YET_LISTED",
        "DELISTED",
        "UNKNOWN_SYMBOL",
        "TERMS_UNVERIFIED",
        "PIT_KNOWLEDGE_BLOCKED",
    ]  # bloc_05/01 section 9


def _identity_sources_import():
    import importlib

    return importlib.import_module("crypto_sensor_fabric.normalization.identity")


# ---------------------------------------------------------------------------
# Registry extension laws RED until B5-I03B (I03 directive 30/31)
# ---------------------------------------------------------------------------


def test_registry_snapshot_still_defaults_to_no_aliases() -> None:
    """Backward compatibility: IdentityRegistrySnapshot() without aliases keeps
    working (RED until 3.7 field defaults land)."""
    import importlib

    identity = importlib.import_module("crypto_sensor_fabric.normalization.identity")
    snap = identity.IdentityRegistrySnapshot(registry_version="v")
    assert tuple(snap.aliases) == ()
    assert tuple(snap.lifecycle_events) == ()


def test_alias_referential_integrity_red() -> None:
    """Aliases must reference registered instances and venues (RED until
    the B5-I03B integrity sweep)."""
    identity = _identity_sources_import()
    AliasType = getattr(identity, "AliasType", None)
    InstrumentAlias = getattr(identity, "InstrumentAlias", None)
    IdentityRegistrySnapshot = getattr(identity, "IdentityRegistrySnapshot", None)
    assert AliasType is not None and InstrumentAlias is not None, "RED: I03B models absent"
    al = InstrumentAlias(
        alias_id="AL-1",
        provider="P",
        venue="V",
        alias_text="X",
        alias_type=AliasType.API_SYMBOL,
        contract_instance_id="CI-NOPE",
        valid_from=T0_SAFE,
        valid_to=None,
        known_from=T0_SAFE,
        source_evidence_refs=("provider-docs:x",),
        confidence="operator-curated",
    )
    from crypto_sensor_fabric.normalization.identity import (
        CanonicalAsset,
        ContractInstance,
        EconomicContract,
        Venue,
        VenueInstrument,
    )
    from crypto_sensor_fabric.normalization.enums import PayoffType
    from datetime import datetime, timezone
    from decimal import Decimal

    t0 = datetime(2023, 1, 1, tzinfo=timezone.utc)
    sha256 = "3f79bb7b435b05321651daefd374cdc681dc06faa65e374e38337b88ca4c6a11"
    with pytest.raises(Exception):
        IdentityRegistrySnapshot(
            registry_version="v",
            assets=(CanonicalAsset(
                asset_id="BTC", symbol_canonical="BTC", asset_type="CRYPTO",
                metadata_version="1",
            ),),
            venues=( Venue(venue_id="V"),),
            economic_contracts=(EconomicContract(
                economic_contract_id="EC",
                underlying_asset_id="BTC",
                quote_asset_id="BTC",
                settlement_asset_id="BTC",
                instrument_type="PERPETUAL_FUTURE",
                perpetual_or_delivery="PERPETUAL",
                payoff_type=PayoffType.LINEAR,
            ),),
            venue_instruments=(VenueInstrument(
                provider="P", venue="V", native_symbol="X",
                instrument_type="PERPETUAL_FUTURE", native_metadata_hash=sha256,
                first_seen_at=t0, last_seen_at=t0,
            ),),
            contract_instances=(ContractInstance(
                contract_instance_id="CI-1",
                provider="P",
                venue="V",
                native_symbol="X",
                economic_contract_id="EC",
                valid_from=t0,
                known_from=t0,
                contract_multiplier=Decimal("1"),
                multiplier_unit="CONTRACT",
                price_unit="USDT",
                quantity_unit="BTC",
                settlement_asset_id="BTC",
                payoff_type=PayoffType.LINEAR,
                inverse_flag=False,
                quanto_flag=False,
                tick_size=Decimal("0.1"),
                lot_size=Decimal("0.0001"),
                contract_terms_version="1",
                source_evidence_refs=("provider-docs:ci",),
            ),),
            aliases=(al,),
        )


T0_SAFE = __import__("datetime").datetime(2023, 1, 1, tzinfo=__import__("datetime").timezone.utc)


def test_i02_vocabulary_matrix_untouched() -> None:
    """Custody: the I02 matrix stays as built."""
    matrix = json.loads(I02_VOCAB_MATRIX.read_text(encoding="utf-8"))
    assert matrix["summary"]["audited_fields"] == 10
