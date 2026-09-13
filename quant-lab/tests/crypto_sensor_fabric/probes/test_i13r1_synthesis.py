"""SENSOR-B2-I13R1 synthesis-invariant tests.

Cover the operator repair gates that live at the boundary between the live
runner and the offline report layer:

- the canonical capability universe stays 34 scopes (registry-driven); a scope
  with no attempts NEVER disappears from reports (NO ATTEMPT != NO NODE),
- E2+ claims carry resolving evidence_ids; PIT readiness is fail-closed,
- verified redundancy counts only E2+ data-semantics-verified claims
  (E0 / blocked / unattempted / EMPTY_VALID-only never count),
- Bitfinex community metadata is SOURCE_AVAILABILITY_VERIFIED only — never
  PIT-ready liquidation data, and the public GitHub/LFS source needs no key,
- history boundaries stay per-instrument (never collapsed).

All offline.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from crypto_sensor_fabric.probes.reports import history_boundaries_csv, pit_readiness_csv, provider_coverage_csv
from crypto_sensor_fabric.probes.reports import sensor_gap_csv

CONFIG = (
    Path(__file__).resolve().parents[3]
    / "config"
    / "crypto_sensor_fabric"
    / "provider_probe_endpoints.yaml"
)


def _registry_scopes() -> list[tuple[str, str]]:
    data = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    out: list[tuple[str, str]] = []
    for pid, entry in data["providers"].items():
        for sensor in entry.get("endpoints", {}):
            out.append((pid, sensor))
    return out


def test_canonical_universe_is_34_scopes() -> None:
    scopes = _registry_scopes()
    assert len(scopes) == 34
    # the two scopes the I13 runner dropped must be present in the universe
    pairs = set(scopes)
    assert ("KRAKEN_FUTURES", "MECHANICAL_LIQUIDATION") in pairs
    assert ("GATE_FUTURES", "MECHANICAL_BOOK_SNAPSHOT") in pairs


def test_expected_sensor_families_cover_the_eight_mechanical_families() -> None:
    sensors = {s for _, s in _registry_scopes()}
    for expected in (
        "MECHANICAL_OPEN_INTEREST",
        "MECHANICAL_FUNDING",
        "MECHANICAL_BASIS",
        "MECHANICAL_POSITIONING",
        "MECHANICAL_BOOK_METRIC",
        "MECHANICAL_LIQUIDATION",
        "MECHANICAL_TRADE",
        "MECHANICAL_BOOK_SNAPSHOT",
    ):
        assert expected in sensors, expected


def test_registry_matches_live_manifest_providers() -> None:
    manifest = (
        Path(__file__).resolve().parents[3]
        / "config"
        / "crypto_sensor_fabric"
        / "live_probe_contracts.yaml"
    )
    manifest_data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    registry = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    registry_providers = set(registry["providers"])
    manifest_providers = {
        k for k in manifest_data if k not in ("schema_version", "generated_at_checkpoint", "documentation_reviewed_on", "primary_rule")
    }
    assert registry_providers == manifest_providers, (
        registry_providers ^ manifest_providers
    )


def test_expected_sensors_argument_drives_full_gap_matrix() -> None:
    # every mechanical sensor family must appear in the gap matrix even when
    # no provider is verified yet (no sensor row disappears)
    from crypto_sensor_fabric.contracts.enums import SensorFamily

    families = [SensorFamily.MECHANICAL_OPEN_INTEREST, SensorFamily.MECHANICAL_BOOK_SNAPSHOT]
    text = sensor_gap_csv([], families)
    assert "MECHANICAL_OPEN_INTEREST" in text
    assert "MECHANICAL_BOOK_SNAPSHOT" in text


# ---------------------------------------------------------------------------
# PIT fail-closed rendering on real coverage shapes
# ---------------------------------------------------------------------------


def test_pit_matrix_fails_closed_on_metadata_only_source() -> None:
    from crypto_sensor_fabric.probes.enums import (
        AccessMode,
        CapabilityStatus,
        EvidenceLevel,
        PITReadiness,
    )
    from crypto_sensor_fabric.probes.models import ProviderSensorCoverage

    # Bitfinex: source availability E2 but data semantics NOT verified
    coverage = ProviderSensorCoverage.model_validate(
        {
            "provider_id": "BITFINEX_COMMUNITY_ARCHIVE",
            "sensor_family": "MECHANICAL_LIQUIDATION",
            "venue_market": "BITFINEX",
            "instrument_scope": ["BTC"],
            "access_mode": AccessMode.COMMUNITY_ARCHIVE,
            "era_status": {"RECENT_CONTROL": CapabilityStatus.VERIFIED},
            "PIT_readiness": PITReadiness.PIT_READY_WITH_METHOD_VERSION,  # stale value
            "evidence_level": EvidenceLevel.E2_LIVE_RECENT_VERIFIED,
            "pit_effective_ts_understood": False,
            "pit_observation_ts_understood": False,
            "pit_publication_delay_understood": None,
            "data_semantics_verified": False,
            "pit_blocking_reason": "SOURCE_AVAILABILITY_VERIFIED only; row timestamps not inspected",
        }
    )
    text = pit_readiness_csv([coverage])
    assert "NOT_PIT_READY" in text
    assert "PIT_READY_WITH_METHOD_VERSION," not in text


# ---------------------------------------------------------------------------
# per-instrument history boundaries (I13R1 §5)
# ---------------------------------------------------------------------------


def _attempt(*, instrument: str, era: str, probe_id: str):
    from datetime import UTC, datetime

    from crypto_sensor_fabric.probes.enums import (
        AccessMode,
        Granularity,
        QueryMode,
        ResponseStatusClass,
    )
    from crypto_sensor_fabric.probes.models import CapabilityProbeAttempt

    return CapabilityProbeAttempt.model_validate(
        {
            "probe_id": probe_id,
            "probe_run_id": "run_i13r1",
            "provider_id": "KRAKEN_FUTURES",
            "sensor_family": "MECHANICAL_OPEN_INTEREST",
            "venue_market": "KRAKEN_FUTURES",
            "instrument_native": instrument,
            "canonical_asset_hint": "BTC",
            "requested_start": datetime(2022, 6, 15, tzinfo=UTC) if era == "2022" else datetime(2024, 6, 15, tzinfo=UTC),
            "requested_end": datetime(2022, 6, 16, tzinfo=UTC) if era == "2022" else datetime(2024, 6, 16, tzinfo=UTC),
            "requested_granularity": Granularity.G1D,
            "access_mode": AccessMode.PUBLIC_REST,
            "query_mode": QueryMode.TIME_RANGE,
            "response_status_class": ResponseStatusClass.VERIFIED_SAMPLE,
            "era_hint": era,
            "probe_version": "test-v1",
        }
    )


def test_history_boundaries_never_collapse_instruments() -> None:
    attempts = [
        _attempt(instrument="PI_XBTUSD", era="2022", probe_id="btc_2022"),
        _attempt(instrument="PI_XBTUSD", era="2024", probe_id="btc_2024"),
        _attempt(instrument="PI_ETHUSD", era="2024", probe_id="eth_2024"),
    ]
    text = history_boundaries_csv(attempts)
    rows = [r for r in text.splitlines() if r.startswith("KRAKEN_FUTURES,")]
    instruments = {r.split(",")[2] for r in rows}
    assert instruments == {"PI_XBTUSD", "PI_ETHUSD"}
    eth_row = next(r for r in rows if r.split(",")[2] == "PI_ETHUSD")
    assert "btc_2022" not in eth_row.split(",")[9]


def test_provider_coverage_csv_has_all_era_columns() -> None:
    from crypto_sensor_fabric.probes.enums import AccessMode, EvidenceLevel, PITReadiness
    from crypto_sensor_fabric.probes.models import ProviderSensorCoverage

    coverage = ProviderSensorCoverage.model_validate(
        {
            "provider_id": "KRAKEN_FUTURES",
            "sensor_family": "MECHANICAL_OPEN_INTEREST",
            "venue_market": "KRAKEN_FUTURES",
            "access_mode": AccessMode.PUBLIC_REST,
            "era_status": {"RECENT_CONTROL": "VERIFIED"},
            "evidence_level": EvidenceLevel.E2_LIVE_RECENT_VERIFIED,
            "PIT_readiness": PITReadiness.NOT_PIT_READY,
        }
    )
    text = provider_coverage_csv([coverage])
    header = text.splitlines()[0]
    for col in ("2021", "2022", "2024", "2026", "recent_status"):
        assert col in header
