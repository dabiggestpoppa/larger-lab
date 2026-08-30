"""Live-probe contract manifest tests (SENSOR-B2-I12R1C, section 10-11).

The manifest at config/crypto_sensor_fabric/live_probe_contracts.yaml is the
operator-readable plan for I13.  These tests freeze its structure and the
corrected contract facts so a wrong URL/unit/access assumption can never slip
into the live plan unseen.

All offline.  Every live_probe_enabled flag MUST stay False until the operator
authorizes SENSOR-B2-I13 (no live requests in ordinary tests).
"""

from __future__ import annotations

from pathlib import Path

import yaml

CONFIG = (
    Path(__file__).resolve().parents[3]
    / "config"
    / "crypto_sensor_fabric"
    / "live_probe_contracts.yaml"
)

REQUIRED_SENSOR_KEYS = {
    "absolute_url",
    "method",
    "auth",
    "start_param",
    "start_unit",
    "end_param",
    "end_unit",
    "pagination",
    "native_unit_notes",
    "historical",
    "evidence_source_url",
    "documentation_last_reviewed",
    "live_probe_enabled",
}


def _load() -> dict:
    assert CONFIG.exists(), f"manifest missing: {CONFIG}"
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def _sensors() -> list[tuple[str, str, dict]]:
    data = _load()
    out: list[tuple[str, str, dict]] = []
    for provider_id, entry in data.items():
        if provider_id in ("schema_version", "generated_at_checkpoint", "documentation_reviewed_on", "primary_rule", "global_probe_rule"):
            continue
        for sensor, spec in entry.get("sensors", {}).items():
            out.append((provider_id, sensor, spec))
    return out


def test_manifest_loads() -> None:
    data = _load()
    assert data["schema_version"] == "1.0"
    assert data["documentation_reviewed_on"]
    assert "KRAKEN_FUTURES" in data
    assert "GATE_FUTURES" in data


def test_every_sensor_carries_full_contract_shape() -> None:
    for provider_id, sensor, spec in _sensors():
        missing = REQUIRED_SENSOR_KEYS - set(spec)
        assert not missing, f"{provider_id}/{sensor} missing {sorted(missing)}"


def test_no_live_probe_enabled_before_i13() -> None:
    for provider_id, sensor, spec in _sensors():
        assert spec["live_probe_enabled"] is False, (
            f"{provider_id}/{sensor} must stay disabled until I13 is authorized"
        )


def test_every_sensor_has_documented_evidence_url() -> None:
    for provider_id, sensor, spec in _sensors():
        assert spec["evidence_source_url"].startswith("https://"), (
            f"{provider_id}/{sensor} evidence URL must be https"
        )


# ---------------------------------------------------------------------------
# Required contract facts (golden frozen) — section 10/11
# ---------------------------------------------------------------------------


def _sensor(provider: str, sensor: str) -> dict:
    data = _load()
    return data[provider]["sensors"][sensor]


def test_kraken_oi_uses_market_analytics_open_interest() -> None:
    spec = _sensor("KRAKEN_FUTURES", "MECHANICAL_OPEN_INTEREST")
    assert "/api/charts/v1/analytics" in spec["absolute_url"]
    assert "open-interest" in spec["absolute_url"]
    assert spec["start_unit"] == "epoch_seconds"
    assert "seconds" in spec["interval_unit"]
    assert "604800" in spec["interval_unit"]  # supported resolutions enumerated
    assert "tickers" not in spec["absolute_url"]


def test_gate_positioning_uses_public_contract_stats() -> None:
    spec = _sensor("GATE_FUTURES", "MECHANICAL_POSITIONING")
    assert "/api/v4/futures/usdt/contract_stats" in spec["absolute_url"]
    assert spec["auth"] == "NO_AUTH"
    assert "positions" not in spec["absolute_url"]
    assert spec["start_unit"] == "epoch_seconds"


def test_binance_oi_absolute_route() -> None:
    spec = _sensor("BINANCE_USDM", "MECHANICAL_OPEN_INTEREST")
    assert (
        spec["absolute_url"]
        == "https://fapi.binance.com/futures/data/openInterestHist"
    )
    # Negative: not composed beneath /fapi/v1
    assert "/fapi/v1/futures/data/openInterestHist" not in (spec["absolute_url"] + " ")


def test_bybit_oi_category_and_interval() -> None:
    spec = _sensor("BYBIT_LINEAR", "MECHANICAL_OPEN_INTEREST")
    assert "/v5/market/open-interest" in spec["absolute_url"]
    assert "category=linear" in spec["query"]
    assert "intervalTime" in spec["query"]


def test_okx_funding_public_namespace() -> None:
    spec = _sensor("OKX_SWAP", "MECHANICAL_FUNDING")
    assert "/api/v5/public/funding-rate-history" in spec["absolute_url"]
    # Negative: never composed as /market/funding-rate-history
    assert "/api/v5/market/funding-rate-history" not in spec["absolute_url"]


def test_okx_funding_pagination_keyed_on_funding_time() -> None:
    spec = _sensor("OKX_SWAP", "MECHANICAL_FUNDING")
    assert "fundingTime" in spec["pagination"]
    assert "NOT trade ids" in spec["pagination"]


def test_coinalyze_credential_prereq_not_auth_blocked() -> None:
    spec = _sensor("COINALYZE", "MECHANICAL_OPEN_INTEREST")
    assert "CREDENTIAL_NOT_CONFIGURED" in spec["credential_prereq"]
    assert "never AUTH_BLOCKED" in spec["credential_prereq"]


def test_bitfinex_no_huge_download_planned() -> None:
    spec = _sensor("BITFINEX_COMMUNITY_ARCHIVE", "MECHANICAL_LIQUIDATION")
    assert spec.get("dump_download_planned") is False
    # The 355MB LFS artifact is the one planned artifact > start of the 100MB
    # range; the contract mandates it is NOT downloaded during probing.
    assert spec.get("dump_download_planned") is False
    note = spec.get("no_download_gt100mb_note", "")
    assert "NOT downloaded during probing" in note
    assert "355217408" in note