"""SENSOR-B5-I05 - RED-first provider time-semantics registry suite.

Frozen authority: bloc_05/02 s2/s7/s8 (role vocabulary, interval declaration,
precision), s5/s6 (fail-closed availability), s17 (the registry module and its
``provider_time_semantics.yaml``), s18.7 (unknown provider timestamp semantics
fail closed for strict replay), bloc_05/06 s1 G2.

The governing scope law for this checkpoint is the I05 directive phase C:
"Unknown mappings must fail closed. Do not create invented mappings for real
exchanges. Synthetic fixtures may be used for tests."  The committed
configuration therefore carries ZERO real-exchange rows, and that emptiness is
itself asserted here -- a silently populated registry would be guessed data.

OFFLINE.  No network, no wall clock, no filesystem writes.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from crypto_sensor_fabric.contracts.enums import SensorFamily
from crypto_sensor_fabric.normalization.enums import (
    IntervalTimeConvention,
    TimestampPrecision,
)
from crypto_sensor_fabric.normalization.time import (
    ProviderTimeSemantics,
    ProviderTimeSemanticsRegistry,
    TimestampRole,
    UnknownProviderTimeSemantics,
    parse_provider_time_semantics_yaml,
    serialize_provider_time_semantics_yaml,
)

_HERE = Path(__file__).resolve().parent
_QUANT_LAB = _HERE.parents[2]
CONFIG = _QUANT_LAB / "config" / "crypto_sensor_fabric" / "provider_time_semantics.yaml"

#: The frozen Bloc 1 provider candidate set (config/provider_registry.yaml).
REAL_PROVIDERS = (
    "KRAKEN_FUTURES",
    "GATE_FUTURES",
    "BINANCE_USDM",
    "BYBIT_LINEAR",
    "OKX_SWAP",
    "DERIBIT",
    "COINALYZE",
    "BITFINEX_COMMUNITY_ARCHIVE",
)

SYNTH = """\
schema_version: "1.0"
semantics:
  - provider: SYNTHETIC_EXCHANGE_A
    sensor_family: MECHANICAL_OPEN_INTEREST
    timestamp_field_roles:
      SOURCE_EVENT_AT: "timestamp"
      INTERVAL_START_AT: "start"
      INTERVAL_END_AT: "end"
    interval_time_convention: LEFT_CLOSED_RIGHT_OPEN
    precision: MILLISECOND
    contemporaneous_public: true
    source_evidence_refs:
      - "provider-docs:synthetic-a-public-feed"
  - provider: SYNTHETIC_EXCHANGE_A
    sensor_family: MECHANICAL_TRADE
    timestamp_field_roles: {}
    interval_time_convention: POINT_SAMPLE
    precision: MICROSECOND
    contemporaneous_public: false
    source_evidence_refs: []
"""


def _registry() -> ProviderTimeSemanticsRegistry:
    return parse_provider_time_semantics_yaml(SYNTH)


# ---------------------------------------------------------------------------
# The committed configuration: present, schema-valid, and EMPTY of real rows
# ---------------------------------------------------------------------------


def test_the_frozen_configuration_file_exists() -> None:
    assert CONFIG.is_file(), "bloc_05/02 s17 requires provider_time_semantics.yaml"


def test_committed_configuration_parses_with_the_frozen_schema_version() -> None:
    registry = parse_provider_time_semantics_yaml(CONFIG.read_text(encoding="utf-8"))
    assert registry.schema_version == "1.0"
    assert isinstance(registry, ProviderTimeSemanticsRegistry)


def test_committed_configuration_carries_no_real_exchange_mapping() -> None:
    """No real exchange may be given invented timestamp semantics."""
    text = CONFIG.read_text(encoding="utf-8")
    registry = parse_provider_time_semantics_yaml(text)
    assert registry.semantics == (), (
        "provider_time_semantics.yaml must hold zero verified real-exchange rows "
        "until documentation or probes establish them"
    )
    for provider in REAL_PROVIDERS:
        assert provider not in text, f"{provider} semantics would be an invention"


def test_every_real_provider_lookup_fails_closed() -> None:
    """s18.7: unknown provider timestamp semantics fail closed for strict replay."""
    registry = parse_provider_time_semantics_yaml(CONFIG.read_text(encoding="utf-8"))
    for provider in REAL_PROVIDERS:
        assert registry.resolve(provider, SensorFamily.MECHANICAL_TRADE) is None
        with pytest.raises(UnknownProviderTimeSemantics):
            registry.require(provider, SensorFamily.MECHANICAL_TRADE)


# ---------------------------------------------------------------------------
# Resolution: present rows resolve, absent rows never synthesize a default
# ---------------------------------------------------------------------------


def test_synthetic_row_resolves_with_every_declared_semantic() -> None:
    registry = _registry()
    row = registry.require("SYNTHETIC_EXCHANGE_A", SensorFamily.MECHANICAL_OPEN_INTEREST)
    assert row.provider == "SYNTHETIC_EXCHANGE_A"
    assert row.sensor_family is SensorFamily.MECHANICAL_OPEN_INTEREST
    assert row.interval_time_convention is IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN
    assert row.precision is TimestampPrecision.MILLISECOND
    assert row.contemporaneous_public is True
    assert row.source_evidence_refs == ("provider-docs:synthetic-a-public-feed",)


def test_role_mapping_is_resolved_by_frozen_role_only() -> None:
    registry = _registry()
    assert (
        registry.require_role(
            "SYNTHETIC_EXCHANGE_A",
            SensorFamily.MECHANICAL_OPEN_INTEREST,
            TimestampRole.SOURCE_EVENT_AT,
        )
        == "timestamp"
    )
    assert (
        registry.require_role(
            "SYNTHETIC_EXCHANGE_A",
            SensorFamily.MECHANICAL_OPEN_INTEREST,
            TimestampRole.INTERVAL_END_AT,
        )
        == "end"
    )


def test_unmapped_role_fails_closed_instead_of_guessing_a_field() -> None:
    """bloc_05/02 s7: never guess which field a timestamp came from."""
    registry = _registry()
    row = registry.require("SYNTHETIC_EXCHANGE_A", SensorFamily.MECHANICAL_OPEN_INTEREST)
    assert row.timestamp_field_roles.get(TimestampRole.EFFECTIVE_AT) is None
    assert (
        registry.resolve_role(
            "SYNTHETIC_EXCHANGE_A",
            SensorFamily.MECHANICAL_OPEN_INTEREST,
            TimestampRole.EFFECTIVE_AT,
        )
        is None
    )
    with pytest.raises(UnknownProviderTimeSemantics):
        registry.require_role(
            "SYNTHETIC_EXCHANGE_A",
            SensorFamily.MECHANICAL_OPEN_INTEREST,
            TimestampRole.EFFECTIVE_AT,
        )


def test_unknown_provider_or_family_never_returns_a_default_row() -> None:
    registry = _registry()
    assert registry.resolve("SYNTHETIC_EXCHANGE_B", SensorFamily.MECHANICAL_TRADE) is None
    assert registry.resolve("SYNTHETIC_EXCHANGE_A", SensorFamily.MECHANICAL_BASIS) is None
    with pytest.raises(UnknownProviderTimeSemantics):
        registry.require("SYNTHETIC_EXCHANGE_B", SensorFamily.MECHANICAL_TRADE)


def test_a_row_with_no_role_mapping_is_still_not_a_mapping() -> None:
    registry = _registry()
    row = registry.require("SYNTHETIC_EXCHANGE_A", SensorFamily.MECHANICAL_TRADE)
    assert row.timestamp_field_roles == {}
    assert (
        registry.resolve_role(
            "SYNTHETIC_EXCHANGE_A",
            SensorFamily.MECHANICAL_TRADE,
            TimestampRole.SOURCE_EVENT_AT,
        )
        is None
    )


def test_registry_is_immutable() -> None:
    registry = _registry()
    with pytest.raises(Exception):
        registry.semantics = ()  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Parsing refuses everything the plan does not declare
# ---------------------------------------------------------------------------


def test_duplicate_provider_family_row_is_refused() -> None:
    text = (
        'schema_version: "1.0"\n'
        "semantics:\n"
        "  - provider: SYNTHETIC_EXCHANGE_A\n"
        "    sensor_family: MECHANICAL_TRADE\n"
        "    timestamp_field_roles: {}\n"
        "    interval_time_convention: POINT_SAMPLE\n"
        "    precision: MICROSECOND\n"
        "    contemporaneous_public: false\n"
        "    source_evidence_refs: []\n"
        "  - provider: SYNTHETIC_EXCHANGE_A\n"
        "    sensor_family: MECHANICAL_TRADE\n"
        "    timestamp_field_roles: {}\n"
        "    interval_time_convention: POINT_SAMPLE\n"
        "    precision: MICROSECOND\n"
        "    contemporaneous_public: false\n"
        "    source_evidence_refs: []\n"
    )
    with pytest.raises(ValueError):
        parse_provider_time_semantics_yaml(text)


def test_unknown_interval_convention_token_is_refused() -> None:
    text = SYNTH.replace("LEFT_CLOSED_RIGHT_OPEN", "LEFT_ONLY")
    with pytest.raises(ValueError):
        parse_provider_time_semantics_yaml(text)


def test_unknown_precision_token_is_refused() -> None:
    text = SYNTH.replace("precision: MILLISECOND", "precision: NANOSECONDish")
    with pytest.raises(ValueError):
        parse_provider_time_semantics_yaml(text)


def test_unknown_timestamp_role_key_is_refused() -> None:
    text = SYNTH.replace('      SOURCE_EVENT_AT: "timestamp"', '      EVENT_TIME: "timestamp"')
    with pytest.raises(ValueError):
        parse_provider_time_semantics_yaml(text)


def test_unknown_sensor_family_is_refused() -> None:
    text = SYNTH.replace("MECHANICAL_TRADE", "MECHANICAL_SWAP_RATE")
    with pytest.raises(ValueError):
        parse_provider_time_semantics_yaml(text)


def test_extra_configuration_field_is_refused() -> None:
    text = SYNTH.replace(
        "    precision: MICROSECOND\n",
        "    precision: MICROSECOND\n    latency_ms: 15\n",
    )
    with pytest.raises(ValueError):
        parse_provider_time_semantics_yaml(text)


def test_blank_provider_identifier_is_refused() -> None:
    text = SYNTH.replace("provider: SYNTHETIC_EXCHANGE_A", 'provider: "  "')
    with pytest.raises(ValueError):
        parse_provider_time_semantics_yaml(text)


def test_contemporaneous_public_claim_requires_evidence() -> None:
    """bloc_05/02 s6: public-contemporaneous classification must be evidenced."""
    text = SYNTH.replace('      - "provider-docs:synthetic-a-public-feed"', "      []")
    with pytest.raises(ValueError):
        parse_provider_time_semantics_yaml(text)


def test_path_shaped_evidence_reference_is_refused() -> None:
    text = SYNTH.replace(
        '"provider-docs:synthetic-a-public-feed"', '"docs/realtime.json"'
    )
    with pytest.raises(ValueError):
        parse_provider_time_semantics_yaml(text)


def test_duplicate_evidence_reference_is_refused() -> None:
    text = SYNTH.replace(
        '      - "provider-docs:synthetic-a-public-feed"',
        '      - "provider-docs:synthetic-a-public-feed"\n'
        '      - "provider-docs:synthetic-a-public-feed"',
    )
    with pytest.raises(ValueError):
        parse_provider_time_semantics_yaml(text)


def test_missing_schema_version_is_refused() -> None:
    text = SYNTH.replace('schema_version: "1.0"\n', "")
    with pytest.raises(ValueError):
        parse_provider_time_semantics_yaml(text)


def test_empty_document_is_refused() -> None:
    with pytest.raises(ValueError):
        parse_provider_time_semantics_yaml("")


# ---------------------------------------------------------------------------
# Serialization is deterministic and round-trips
# ---------------------------------------------------------------------------


def test_parse_serialize_round_trip_is_byte_stable() -> None:
    text = SYNTH
    first = serialize_provider_time_semantics_yaml(parse_provider_time_semantics_yaml(text))
    second = serialize_provider_time_semantics_yaml(parse_provider_time_semantics_yaml(text))
    assert first == second
    assert parse_provider_time_semantics_yaml(first) == parse_provider_time_semantics_yaml(text)


def test_serialized_output_is_valid_yaml_with_the_frozen_top_level_keys() -> None:
    payload = yaml.safe_load(
        serialize_provider_time_semantics_yaml(parse_provider_time_semantics_yaml(SYNTH))
    )
    assert set(payload) == {"schema_version", "semantics"}
    assert payload["schema_version"] == "1.0"
    assert isinstance(payload["semantics"], list)


def test_synthetic_row_model_is_immutable_and_explicit() -> None:
    row = _registry().require(
        "SYNTHETIC_EXCHANGE_A", SensorFamily.MECHANICAL_OPEN_INTEREST
    )
    assert isinstance(row, ProviderTimeSemantics)
    with pytest.raises(Exception):
        row.precision = TimestampPrecision.NANOSECOND  # type: ignore[misc]


def test_no_wall_clock_token_appears_in_the_time_package_sources() -> None:
    """bloc_05/02 s18: deterministic behavior; no live-clock dependence."""
    package = _QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization" / "time"
    for path in sorted(package.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for forbidden in ("datetime.now", "datetime.utcnow", "time.time", "date.today"):
            assert forbidden not in text, f"{path.name} references {forbidden}"
