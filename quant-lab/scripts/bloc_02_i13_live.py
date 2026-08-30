"""SENSOR-B2-I13 — first controlled live capability evidence run.

Executes the authorized live probe against free/public provider surfaces using
the frozen `live_probe_contracts.yaml` + endpoint registry as the request
authority.  This is CAPABILITY CHARACTERIZATION ONLY — not production ingestion,
backfill, normalization, or signal generation.

Principles honoured here:
- primary rule: WRONG REQUEST != PROVIDER UNSUPPORTED.  Requests are built by the
  probe modules from the corrected contracts, never improvised from memory.
- RECENT_CONTROL first; a hard-blocked recent control suppresses historical
  probes for the same scope.
- sequential, low concurrency; bounded retries with exponential backoff; no
  retry on hard blocks/geo/auth/deterministic archive holes.
- no bypass (no VPN/proxy/geo-spoof/credentials/payment).
- lightweight capability evidence only; no artifact >100MB bandwidth.
- Coinalyze: no API key configured -> CREDENTIAL_NOT_CONFIGURED (never AUTH_BLOCKED).
- Bitfinex: GitHub/LFS metadata + LFS OID only; NEVER the ~355MB DuckDB download.

Every executed step emits one or more immutable CapabilityProbeAttempt records.
Sanitized raw attempts are persisted under quant-lab/data/crypto_sensor_fabric/i13
(gitignored); the sanitized evidence packet (01-11 in evidence/bloc_02) is written
from the collected attempts via the offline write_reports surface.

Run from the `quant-lab` directory:
    python scripts/bloc_02_i13_live.py [--run-id NAME] [--dry-run]

Exit code 0 on completion regardless of provider outcomes (blocked sources are
valid scientific results).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import requests
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from crypto_sensor_fabric.contracts.enums import SensorFamily  # noqa: E402
from crypto_sensor_fabric.probes.enums import (  # noqa: E402
    AccessMode,
    CapabilityStatus,
    Granularity,
    PITReadiness,
    ProbeFailureClass,
    ProbeRunStatus,
    ProviderRole,
    QueryMode,
    RedundancyClass,
    ResponseStatusClass,
)
from crypto_sensor_fabric.probes.evidence import synthesize_claim  # noqa: E402
from crypto_sensor_fabric.probes.models import (  # noqa: E402
    CapabilityClaim,
    CapabilityProbeAttempt,
    CapabilityProbeRequest,
    DocumentationRuntimeContradiction,
    FailureRecord,
    ProbeRunResult,
    ProviderSensorCoverage,
    SensorRedundancySummary,
)
from crypto_sensor_fabric.probes.reports import write_reports  # noqa: E402
from crypto_sensor_fabric.providers import (  # noqa: E402
    bitfinex_archive,
    binance,
    bybit,
    coinalyze,
    deribit,
    gate,
    kraken,
    okx,
)

LIVE_MANIFEST = (
    REPO_ROOT / "config" / "crypto_sensor_fabric" / "live_probe_contracts.yaml"
)
LIVE_OUTPUT_ROOT = REPO_ROOT / "data" / "crypto_sensor_fabric" / "i13"
PACKET_DIR = (
    REPO_ROOT
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_02"
)

COINALYZE_CONFIGURED = bool(
    os.environ.get("COINALYZE_API_KEY")
    or os.environ.get("COINALYZE_KEY")
    or os.environ.get("COINALYZE_APIKEY")
)

#: provider_id -> probe class
PROBES = {
    "KRAKEN_FUTURES": kraken.KrakenCapabilityProbe,
    "GATE_FUTURES": gate.GateCapabilityProbe,
    "BYBIT_LINEAR": bybit.BybitCapabilityProbe,
    "BINANCE_USDM": binance.BinanceCapabilityProbe,
    "OKX_SWAP": okx.OkxCapabilityProbe,
    "DERIBIT": deribit.DeribitCapabilityProbe,
    "COINALYZE": coinalyze.CoinalyzeCapabilityProbe,
    "BITFINEX_COMMUNITY_ARCHIVE": bitfinex_archive.BitfinexArchiveCapabilityProbe,
}

ACCESS = {
    "KRAKEN_FUTURES": AccessMode.PUBLIC_REST,
    "GATE_FUTURES": AccessMode.PUBLIC_REST,
    "BYBIT_LINEAR": AccessMode.PUBLIC_REST,
    "BINANCE_USDM": AccessMode.PUBLIC_REST,
    "OKX_SWAP": AccessMode.PUBLIC_REST,
    "DERIBIT": AccessMode.PUBLIC_REST,
    "COINALYZE": AccessMode.FREE_API_KEY,
    "BITFINEX_COMMUNITY_ARCHIVE": AccessMode.COMMUNITY_ARCHIVE,
}

#: per-sensor granularity + query-mode defaults for the capability scope.
SENSOR_SPEC: dict[str, tuple[Granularity, QueryMode]] = {
    "MECHANICAL_OPEN_INTEREST": (Granularity.G1H, QueryMode.TIME_RANGE),
    "MECHANICAL_FUNDING": (Granularity.G1H, QueryMode.TIME_RANGE),
    "MECHANICAL_BASIS": (Granularity.G1H, QueryMode.TIME_RANGE),
    "MECHANICAL_POSITIONING": (Granularity.G1H, QueryMode.TIME_RANGE),
    "MECHANICAL_BOOK_METRIC": (Granularity.G1H, QueryMode.TIME_RANGE),
    "MECHANICAL_LIQUIDATION": (Granularity.G1H, QueryMode.TIME_RANGE),
    "MECHANICAL_TRADE": (Granularity.RAW_EVENT, QueryMode.CURSOR),
    "MECHANICAL_BOOK_SNAPSHOT": (Granularity.BOOK_SNAPSHOT, QueryMode.LATEST_ONLY),
}

ERAS = ("RECENT_CONTROL", "2021", "2022", "2024", "2026")

# ---------------------------------------------------------------------------
# SCOPE — lightweight capability matrix (BTC primary, ETH where breadth matters)
# ---------------------------------------------------------------------------
SCOPE: dict[str, list[dict[str, Any]]] = {
    "KRAKEN_FUTURES": [
        {"sensor": "MECHANICAL_OPEN_INTEREST", "assets": ("BTC", "ETH"), "eras": ("RECENT_CONTROL", "2022", "2024")},
        {"sensor": "MECHANICAL_FUNDING", "assets": ("BTC",), "eras": ("RECENT_CONTROL", "2022", "2024")},
        {"sensor": "MECHANICAL_BASIS", "assets": ("BTC",), "eras": ("RECENT_CONTROL", "2022")},
        {"sensor": "MECHANICAL_POSITIONING", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_BOOK_METRIC", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_TRADE", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_BOOK_SNAPSHOT", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
    ],
    "GATE_FUTURES": [
        {"sensor": "MECHANICAL_OPEN_INTEREST", "assets": ("BTC",), "eras": ("RECENT_CONTROL", "2022")},
        {"sensor": "MECHANICAL_LIQUIDATION", "assets": ("BTC",), "eras": ("RECENT_CONTROL", "2022")},
        {"sensor": "MECHANICAL_POSITIONING", "assets": ("BTC",), "eras": ("RECENT_CONTROL", "2022")},
        {"sensor": "MECHANICAL_FUNDING", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_TRADE", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
    ],
    "BYBIT_LINEAR": [
        {"sensor": "MECHANICAL_OPEN_INTEREST", "assets": ("BTC",), "eras": ("RECENT_CONTROL", "2022")},
        {"sensor": "MECHANICAL_FUNDING", "assets": ("BTC",), "eras": ("RECENT_CONTROL", "2022")},
        {"sensor": "MECHANICAL_TRADE", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_BOOK_SNAPSHOT", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
    ],
    "BINANCE_USDM": [
        {"sensor": "MECHANICAL_OPEN_INTEREST", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_TRADE", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_FUNDING", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_BOOK_SNAPSHOT", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "ARCHIVE_METRICS", "assets": ("BTC",), "eras": ("2022",)},
        {"sensor": "ARCHIVE_AGGTRADES", "assets": ("BTC",), "eras": ("2022",)},
    ],
    "OKX_SWAP": [
        {"sensor": "MECHANICAL_FUNDING", "assets": ("BTC",), "eras": ("RECENT_CONTROL", "2022")},
        {"sensor": "MECHANICAL_TRADE", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_BOOK_SNAPSHOT", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
    ],
    "DERIBIT": [
        {"sensor": "MECHANICAL_TRADE", "assets": ("BTC",), "eras": ("RECENT_CONTROL", "2022")},
        {"sensor": "MECHANICAL_LIQUIDATION", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_FUNDING", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_BOOK_SNAPSHOT", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
    ],
    "COINALYZE": [
        {"sensor": "MECHANICAL_OPEN_INTEREST", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_LIQUIDATION", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_FUNDING", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_POSITIONING", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
    ],
    "BITFINEX_COMMUNITY_ARCHIVE": [
        {"sensor": "MECHANICAL_LIQUIDATION", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
    ],
}

PROVIDER_PRIORITY = [
    "KRAKEN_FUTURES",
    "GATE_FUTURES",
    "BYBIT_LINEAR",
    "BINANCE_USDM",
    "OKX_SWAP",
    "DERIBIT",
    "COINALYZE",
    "BITFINEX_COMMUNITY_ARCHIVE",
]

CHECKPOINT_DATES = {
    "2021": datetime(2021, 6, 15, tzinfo=UTC),
    "2022": datetime(2022, 6, 15, tzinfo=UTC),
    "2024": datetime(2024, 6, 15, tzinfo=UTC),
    "2026": datetime(2026, 6, 15, tzinfo=UTC),
}
WINDOWS = {
    Granularity.G1H: timedelta(days=7),
    Granularity.RAW_EVENT: timedelta(hours=1),
    Granularity.BOOK_SNAPSHOT: timedelta(hours=1),
}

HARD_BLOCKS: frozenset = frozenset(
    {
        ProbeFailureClass.F_ACCESS_GEO,
        ProbeFailureClass.F_ACCESS_AUTH,
        ProbeFailureClass.F_ACCESS_PAYMENT,
        ProbeFailureClass.F_ENDPOINT_REMOVED,
        ProbeFailureClass.F_ARCHIVE_NOT_FOUND,
        ProbeFailureClass.F_UNSUPPORTED_SENSOR,
    }
)
RETRYABLE: frozenset = frozenset(
    {
        ProbeFailureClass.F_NETWORK_TIMEOUT,
        ProbeFailureClass.F_NETWORK_DNS,
        ProbeFailureClass.F_NETWORK_TLS,
        ProbeFailureClass.F_SERVER_5XX,
        ProbeFailureClass.F_ACCESS_RATE_LIMIT,
    }
)


# ---------------------------------------------------------------------------
# request construction
# ---------------------------------------------------------------------------
def build_request(
    probe: Any,
    provider_id: str,
    sensor: SensorFamily,
    asset: str,
    era: str,
    probe_run_id: str,
) -> CapabilityProbeRequest:
    gran, qmode = SENSOR_SPEC[sensor.value]
    if provider_id == "BITFINEX_COMMUNITY_ARCHIVE":
        # community Git-LFS archive probe has no native instrument mapping
        instrument_native = asset
    else:
        instrument_native = probe.native_instrument(asset)
    window = WINDOWS.get(gran, timedelta(hours=1))
    if era == "RECENT_CONTROL":
        # a RECENT window must END at now; a future `to` can make bucket APIs
        # return empty-valid (observed on Kraken analytics) — recent != future
        now = datetime.now(UTC)
        start, end = now - window, now
        requested_end = end
    else:
        start = CHECKPOINT_DATES.get(era, datetime.now(UTC))
        requested_end = start + window
    return CapabilityProbeRequest.model_validate(
    {
        "provider_id": provider_id,
        "sensor_family": sensor,
        "venue_market": provider_id,
        "instrument_native": instrument_native,
        "canonical_asset_hint": asset,
        "requested_start": start,
        "requested_end": requested_end,
            "requested_granularity": gran,
            "access_mode": ACCESS[provider_id],
            "query_mode": qmode,
            "probe_run_id": probe_run_id,
            "provider_hints": {"era": era},
        }
    )


def _body_or_text(resp: requests.Response) -> Any:
    ct = (resp.headers.get("content-type") or "").lower()
    if "json" in ct:
        try:
            return resp.json()
        except ValueError:  # pragma: no cover - defensive
            return resp.text
    return resp.text


# ---------------------------------------------------------------------------
# execution
# ---------------------------------------------------------------------------
def exec_rest(
    probe: Any,
    request: CapabilityProbeRequest,
    session: requests.Session,
    *,
    timeout: int,
    retries: int,
    backoff_base: float,
    extra_params: dict[str, Any] | None = None,
) -> list[CapabilityProbeAttempt]:
    query = probe.build_probe_request(request)
    url = query.get("url")
    params = dict(query.get("params", {}))
    if extra_params:
        params.update(extra_params)
    fingerprint = url + (("?" + "&".join(f"{k}={v}" for k, v in sorted(params.items()))) if params else "")
    attempt = None
    for i in range(retries + 1):
        resp = session.get(url, params=params, timeout=timeout)
        status = resp.status_code
        body = _body_or_text(resp)
        attempt = probe.characterize(request, status, body)
        attempt = attempt.model_copy(
            update={
                "request_method": "GET",
                "request_fingerprint": fingerprint,
            }
        )
        rate = str(resp.headers.get("Retry-After", ""))
        if rate:
            attempt = attempt.model_copy(
                update={"rate_limit_metadata": {"retry_after": rate}}
            )
        if not (attempt.error_class is not None and attempt.error_class in RETRYABLE):
            break
        wait = backoff_base * (2**i)
        print(f"    retry({i+1}) {request.provider_id}/{request.sensor_family.value} after {wait}s")
        time.sleep(wait)
    return [attempt]


def binance_archive_attempt(
    probe: Any,
    request: CapabilityProbeRequest,
    session: requests.Session,
    *,
    kind: str,
    date: str,
) -> CapabilityProbeAttempt:
    file_url = probe.archive_file_url(request.instrument_native, date, kind)
    csum_url = probe.archive_checksum_url(request.instrument_native, date, kind)
    file_status = session.head(file_url, timeout=20).status_code
    checksum_status = "unverified"
    if file_status == 200:
        checksum_status = "present" if session.head(csum_url, timeout=20).status_code == 200 else "missing"
    return probe.characterize_archive(
        request,
        kind=kind,
        date=date,
        file_status=file_status,
        checksum_status=checksum_status,
    )


def credential_missing_attempt(request: CapabilityProbeRequest) -> CapabilityProbeAttempt:
    """Produce a NOT_ATTEMPTED record for a missing LOCAL free-key prerequisite."""
    from crypto_sensor_fabric.providers.coinalyze import PROVIDER_ID as CID

    return CapabilityProbeAttempt.model_validate(
        {
            "probe_id": (
                f"{CID.lower()}_{request.sensor_family.value.lower().replace('mechanical_', '')}"
                f"_{request.instrument_native.lower()}_{request.era_hint or 'unera'}_crednote"
            ),
            "probe_run_id": request.probe_run_id,
            "provider_id": CID,
            "sensor_family": request.sensor_family,
            "venue_market": "COINALYZE",
            "instrument_native": request.instrument_native,
            "canonical_asset_hint": request.canonical_asset_hint,
            "requested_start": request.requested_start,
            "requested_end": request.requested_end,
            "requested_granularity": request.requested_granularity,
            "access_mode": AccessMode.FREE_API_KEY,
            "query_mode": request.query_mode,
            "request_method": "GET",
            "response_status_class": ResponseStatusClass.NOT_ATTEMPTED,
            "error_detail_redacted": (
                "CREDENTIAL_NOT_CONFIGURED — FREE_API_KEY not configured locally; "
                "a local run prerequisite, never a provider failure / AUTH_BLOCKED"
            ),
            "rate_limit_metadata": {"credential_prereq": "CREDENTIAL_NOT_CONFIGURED"},
            "era_hint": request.era_hint,
            "probe_version": "coinalyze-probe-v2",
        }
    )


def derive_coinalyze_attempt(
    probe: Any,
    request: CapabilityProbeRequest,
    session: requests.Session,
    *,
    timeout: int,
    retries: int,
    backoff_base: float,
) -> list[CapabilityProbeAttempt]:
    if not COINALYZE_CONFIGURED:
        return [credential_missing_attempt(request)]
    key = (
        os.environ.get("COINALYZE_API_KEY")
        or os.environ.get("COINALYZE_KEY")
        or os.environ.get("COINALYZE_APIKEY")
    )
    return exec_rest(
        probe,
        request,
        session,
        timeout=timeout,
        retries=retries,
        backoff_base=backoff_base,
        extra_params={"apikey": key},
    )


def exec_bitfinex_repo(
    probe: Any,
    request: CapabilityProbeRequest,
    session: requests.Session,
) -> list[CapabilityProbeAttempt]:
    api = session.get(probe.repository_api_url(), timeout=20)
    repo_status = api.status_code
    repo_present = repo_status == 200
    rev = {}
    if repo_present:
        data = api.json()
        rev["upstream_commit"] = data.get("default_branch")
    license_text = read_url_if_ok(session, probe.license_url())
    readme_text = read_url_if_ok(session, probe.readme_url())
    gitattributes_text = read_url_if_ok(session, probe.gitattributes_url())
    lfs_pointer_text = read_url_if_ok(session, probe.dump_pointer_url())
    try:
        if lfs_pointer_text:
            pointer = probe.parse_lfs_pointer(lfs_pointer_text)
            rev["lfs_pointer_text"] = pointer["oid_digest"] if pointer else None
    except Exception:  # pragma: no cover - defensive
        pass
    return [
        probe.characterize_repository(
            request,
            repo_status=repo_status,
            repo_present=repo_present,
            license_text=license_text,
            readme_text=readme_text,
            gitattributes_text=gitattributes_text,
            lfs_pointer_text=lfs_pointer_text,
            upstream_commit=rev.get("upstream_commit"),
        )
    ]


def read_url_if_ok(session: requests.Session, url: str) -> str | None:
    try:
        resp = session.get(url, timeout=20)
        return resp.text if resp.status_code == 200 else None
    except requests.RequestException:
        return None


# ---------------------------------------------------------------------------
# evidence synthesis (claims / coverages / failures / contradictions)
# ---------------------------------------------------------------------------
def attempts_to_records(
    attempts: list[CapabilityProbeAttempt],
) -> tuple[list[CapabilityClaim], list[ProviderSensorCoverage], list[FailureRecord]]:
    claims: list[CapabilityClaim] = []
    coverages: list[ProviderSensorCoverage] = []
    failures: list[FailureRecord] = []
    by_scope: dict[tuple[str, str], list[CapabilityProbeAttempt]] = {}
    for a in attempts:
        by_scope.setdefault((a.provider_id, a.sensor_family.value), []).append(a)
    idx = 0
    for (pid, sensor_name), group in sorted(by_scope.items()):
        sensor = SensorFamily(sensor_name)
        idx += 1
        claim = synthesize_claim(
            claim_id=f"claim_bloc2_{pid.lower()}_{sensor.value.lower()}_{idx:03d}_live",
            provider_id=pid,
            sensor_family=sensor,
            venue_market=pid,
            access_mode=group[0].access_mode,
            attempts=group,
        )
        claims.append(claim)
        era_status: dict[str, CapabilityStatus] = {}
        for a in group:
            era = a.era_hint or "RECENT_CONTROL"
            era_status[era] = _attempt_status(a)
        verified_dates = [
            a.requested_start
            for a in group
            if a.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
        ]
        coverages.append(
            ProviderSensorCoverage.model_validate(
                {
                    "provider_id": pid,
                    "sensor_family": sensor,
                    "venue_market": pid,
                    "instrument_scope": sorted({a.instrument_native for a in group}),
                    "access_mode": group[0].access_mode,
                    "era_status": era_status,
                    "earliest_verified_history": min(verified_dates) if verified_dates else None,
                    "latest_verified_history": max(verified_dates) if verified_dates else None,
                    "PIT_readiness": claim.PIT_readiness,
                    "evidence_level": claim.evidence_level,
                    "provider_role": ProviderRole.REFERENCE_ONLY,
                    "promotion_eligible": False,
                    "blocking_reason": (
                        None
                        if verified_dates
                        else "no live verified sample yet (E0/UNVERIFIED or blocked)"
                    ),
                }
            )
        )
        for a in group:
            if a.error_class is not None:
                failures.append(
                    FailureRecord.model_validate(
                        {
                            "failure_id": f"f_{a.probe_id}",
                            "probe_id": a.probe_id,
                            "provider_id": pid,
                            "sensor_family": sensor,
                            "failure_class": a.error_class,
                            "provider_native_message_redacted": (a.error_detail_redacted or "")[:200],
                            "retryable": a.error_class in RETRYABLE,
                            "hard_block": a.error_class in HARD_BLOCKS,
                            "evidence_ref": a.probe_id,
                        }
                    )
                )
    return claims, coverages, failures


def _attempt_status(a: CapabilityProbeAttempt) -> CapabilityStatus:
    if a.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE:
        return CapabilityStatus.VERIFIED
    if a.response_status_class is ResponseStatusClass.EMPTY_VALID:
        return CapabilityStatus.VERIFIED_LIMITED
    if a.error_class is ProbeFailureClass.F_ACCESS_GEO:
        return CapabilityStatus.GEO_BLOCKED
    if a.error_class is ProbeFailureClass.F_ACCESS_AUTH:
        return CapabilityStatus.AUTH_BLOCKED
    if a.error_class is ProbeFailureClass.F_ACCESS_PAYMENT:
        return CapabilityStatus.PAYMENT_BLOCKED
    if a.error_class is ProbeFailureClass.F_ENDPOINT_REMOVED:
        return CapabilityStatus.ACCESS_BLOCKED
    if a.error_class is ProbeFailureClass.F_UNSUPPORTED_SENSOR:
        return CapabilityStatus.UNSUPPORTED
    if a.response_status_class is ResponseStatusClass.FAILED:
        return CapabilityStatus.TRANSIENT_FAILURE
    return CapabilityStatus.UNVERIFIED


def redundancy_summaries(coverages: list[ProviderSensorCoverage]) -> list[SensorRedundancySummary]:
    from crypto_sensor_fabric.contracts.enums import SensorFamily

    by_sensor: dict[str, list[ProviderSensorCoverage]] = {}
    for c in coverages:
        verified = any(
            v in (CapabilityStatus.VERIFIED, CapabilityStatus.VERIFIED_LIMITED)
            for v in c.era_status.values()
        )
        if verified:
            by_sensor.setdefault(c.sensor_family.value, []).append(c)
    out: list[SensorRedundancySummary] = []
    for sensor in sorted(by_sensor):
        rows = by_sensor[sensor]
        if len(rows) >= 3:
            _class = RedundancyClass.R3_THREE_PLUS_INDEPENDENT
        elif len(rows) == 2:
            _class = RedundancyClass.R2_TWO_INDEPENDENT
        else:
            _class = RedundancyClass.R1_SINGLE_INDEPENDENT
        out.append(
            SensorRedundancySummary.model_validate(
                {
                    "sensor_family": SensorFamily(sensor),
                    "verified_provider_count": len(rows),
                    "verified_venues": sorted({r.provider_id for r in rows}),
                    "redundancy_class": _class,
                    "first_party_count": len(
                        [
                            r
                            for r in rows
                            if r.access_mode != AccessMode.FREE_API_KEY
                            and r.access_mode != AccessMode.COMMUNITY_ARCHIVE
                        ]
                    ),
                    "aggregator_count": len(
                        [r for r in rows if r.access_mode == AccessMode.FREE_API_KEY]
                    ),
                    "community_count": len(
                        [r for r in rows if r.access_mode == AccessMode.COMMUNITY_ARCHIVE]
                    ),
                    "PIT_ready_provider_count": len(
                        [
                            r
                            for r in rows
                            if r.PIT_readiness
                            in (PITReadiness.PIT_READY, PITReadiness.PIT_READY_WITH_METHOD_VERSION)
                        ]
                    ),
                    "gap_status": "PARTIAL" if rows else "UNVERIFIED",
                    "notes": "live-verified during SENSOR-B2-I13 (roles not frozen)",
                }
            )
        )
    return out


def free_only_rows() -> list[dict[str, Any]]:
    from crypto_sensor_fabric._paths import CONFIG_DIR

    data = yaml.safe_load((CONFIG_DIR / "provider_probe_endpoints.yaml").read_text(encoding="utf-8"))
    rows = []
    for pid, entry in data["providers"].items():
        access = entry.get("access", "")
        keyed = access in ("FREE_API_KEY", "COMMUNITY_ARCHIVE")
        rows.append(
            {
                "provider_id": pid,
                "sensor_family": "|".join(sorted(entry.get("endpoints", {}))) or "",
                "access_mode": access,
                "api_key_required": bool(keyed),
                "account_required": False,
                "payment_method_required": False,
                "paid_subscription_required": False,
                "staking_required": False,
                "transaction_required": False,
                "free_quota": "CREDENTIAL_NOT_CONFIGURED" if pid == "COINALYZE" and not COINALYZE_CONFIGURED else "UNVERIFIED",
                "access_class": access,
                "eligible_required_runtime": "(pending I14 decision)",
                "evidence_refs": "live I13 attempted",
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="i13_first_controlled")
    parser.add_argument("--dry-run", action="store_true", help="build scope but do not execute")
    parser.add_argument("--force", action="store_true", help="re-run live even if attempts exist")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--retries", type=int, default=2)
    args = parser.parse_args()

    run_id = args.run_id
    probe_run_id = f"bloc02_i13_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    out_dir = LIVE_OUTPUT_ROOT / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    attempts_path = out_dir / "attempts.jsonl"
    if attempts_path.exists() and not args.force:
        print(f"resuming from {attempts_path} (use --force to re-run live)")
        all_attempts = [
            CapabilityProbeAttempt.model_validate(json.loads(line))
            for line in attempts_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        _finish(
            all_attempts,
            run_id,
            probe_run_id,
            len(all_attempts),
            len(all_attempts),
            hard_blocked=set(),
        )
        return 0

    session = requests.Session()
    session.headers.update({"User-Agent": "codebuff-crypto-sensor-fabric-bloc2-i13/1.0 (capability characterization)"})

    all_attempts: list[CapabilityProbeAttempt] = []
    planned = 0
    executed = 0
    hard_blocked: set[tuple[str, str]] = set()

    for pid in PROVIDER_PRIORITY:
        if pid not in PROVIDER_PRIORITY:
            continue
        print(f"\n## {pid}")
        probe_cls = PROBES[pid]
        probe = probe_cls()
        scopes = SCOPE.get(pid, [])
        for scope in scopes:
            sensor = SensorFamily(scope["sensor"]) if not scope["sensor"].startswith("ARCHIVE_") else scope["sensor"]
            for asset in scope["assets"]:
                for era in scope["eras"]:
                    if (pid, scope["sensor"]) in hard_blocked and era != "RECENT_CONTROL":
                        print(f"  skip {scope['sensor']}/{asset}/{era} (recent hard-blocked)")
                        continue
                    planned += 1
                    if args.dry_run:
                        continue
                    sr = scope["sensor"]
                    if sr.startswith("ARCHIVE_"):
                        kind = "metrics" if sr == "ARCHIVE_METRICS" else "aggTrades"
                        req = build_request(probe, pid, SensorFamily.MECHANICAL_OPEN_INTEREST if sr == "ARCHIVE_METRICS" else SensorFamily.MECHANICAL_TRADE, asset, era, probe_run_id)
                        date = "2022-06-15"
                        try:
                            attempt = binance_archive_attempt(probe, req, session, kind=kind, date=date)
                            all_attempts.append(attempt)
                        except requests.RequestException as exc:
                            all_attempts.append(_network_failed(req, exc))
                        executed += 1
                        continue
                    req = build_request(probe, pid, sensor, asset, era, probe_run_id)
                    try:
                        if pid == "COINALYZE":
                            atts = derive_coinalyze_attempt(probe, req, session, timeout=args.timeout, retries=args.retries, backoff_base=1.0)
                        elif pid == "BITFINEX_COMMUNITY_ARCHIVE":
                            atts = exec_bitfinex_repo(probe, req, session)
                        else:
                            atts = exec_rest(probe, req, session, timeout=args.timeout, retries=args.retries, backoff_base=1.0)
                    except requests.RequestException as exc:
                        atts = [_network_failed(req, exc)]
                    all_attempts.extend(atts)
                    executed += 1
                    last = atts[-1]
                    label = last.response_status_class.value
                    err = last.error_class.value if last.error_class else ""
                    print(f"  {sr}/{asset}/{era}: {label} {err}".rstrip())
                    if last.response_status_class is ResponseStatusClass.FAILED:
                        if last.error_class is not None and last.error_class in HARD_BLOCKS and era == "RECENT_CONTROL":
                            hard_blocked.add((pid, sr))

    print(f"\nplanned={planned} executed={executed} attempts={len(all_attempts)}")

    if args.dry_run:
        return 0

    # persist sanitized raw attempts (gitignored)
    (out_dir / "attempts.jsonl").write_text(
        "\n".join(a.model_dump_json() for a in all_attempts) + ("\n" if all_attempts else ""),
        encoding="utf-8",
    )
    (out_dir / "_manifest.yaml").write_text(
        yaml.safe_dump({"run_id": run_id, "probe_run_id": probe_run_id, "planned": planned, "executed": executed, "attempts": len(all_attempts)}),
        encoding="utf-8",
    )
    _finish(all_attempts, run_id, probe_run_id, planned, executed, hard_blocked=hard_blocked)
    return 0


def _finish(
    all_attempts: list[CapabilityProbeAttempt],
    run_id: str,
    probe_run_id: str,
    planned: int,
    executed: int,
    *,
    hard_blocked: set[tuple[str, str]],
) -> None:
    claims, coverages, failures = attempts_to_records(all_attempts)
    skipped = [f"{p}/{s}" for p, s in sorted(hard_blocked)]
    run = ProbeRunResult.model_validate(
        {
            "probe_run_id": probe_run_id,
            "run_status": ProbeRunStatus.COMPLETE_WITH_LIMITATIONS,
            "attempts": all_attempts,
            "planned_but_skipped": skipped,
            "started_at": datetime.now(UTC),
            "finished_at": datetime.now(UTC),
            "probe_version": "sensor-probe-v1-live",
            "notes": [
                "SENSOR-B2-I13 first controlled live capability run",
                "blocked sources are valid scientific results; no bypass used",
            ],
        }
    )
    expected_sensors = [
        SensorFamily.MECHANICAL_TRADE,
        SensorFamily.MECHANICAL_LIQUIDATION,
        SensorFamily.MECHANICAL_OPEN_INTEREST,
        SensorFamily.MECHANICAL_FUNDING,
        SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
        SensorFamily.MECHANICAL_BOOK_METRIC,
        SensorFamily.MECHANICAL_POSITIONING,
        SensorFamily.MECHANICAL_BASIS,
    ]
    written = write_reports(
        output_dir=str(PACKET_DIR),
        run=run,
        attempts=all_attempts,
        claims=claims,
        coverages=coverages,
        redundancies=redundancy_summaries(coverages),
        contradictions=i13_findings_contradictions(),
        free_only_audit=free_only_rows(),
        failures=failures,
        provider_ids=list(PROBES),
        expected_sensors=expected_sensors,
    )
    print(f"\nwrote {len(written)} packet reports -> {PACKET_DIR}")
    print(f"sanitized raw attempts -> {LIVE_OUTPUT_ROOT / run_id / 'attempts.jsonl'}")
    _print_summary(all_attempts, claims)


def i13_findings_contradictions() -> list[DocumentationRuntimeContradiction]:
    """High-value docs/runtime contradictions observed during SENSOR-B2-I13.

    These are recorded, not hidden — even where the probe was corrected so the
    path could continue (a corrected contract is still a documented finding).
    """
    return [
        DocumentationRuntimeContradiction.model_validate(
            {
                "contradiction_id": "contr_i13_gate_contract_stats_interval_unit",
                "provider_id": "GATE_FUTURES",
                "sensor_family": SensorFamily.MECHANICAL_OPEN_INTEREST,
                "documentation_claim": "contract_stats interval is epoch seconds",
                "documentation_source_ref": "live_probe_contracts.yaml (pre-I13)",
                "runtime_observation": (
                    "HTTP 400 INVALID_PARAM_VALUE for interval=3600; a STRING bucket "
                    "(\"1h\") is required.  Probe corrected; `from` remains Unix seconds."
                ),
                "severity": "MATERIAL",
                "resolution_status": "RESOLVED",
                "notes": "contract corrected during I13 run",
            }
        ),
        DocumentationRuntimeContradiction.model_validate(
            {
                "contradiction_id": "contr_i13_deribit_funding_result_shape",
                "provider_id": "DERIBIT",
                "sensor_family": SensorFamily.MECHANICAL_FUNDING,
                "documentation_claim": "funding history result envelope {data: [...]}",
                "documentation_source_ref": "deribit probe model (pre-I13)",
                "runtime_observation": (
                    "get_funding_rate_history returns result as a RAW list; probe "
                    "corrected to parse result-as-list."
                ),
                "severity": "MATERIAL",
                "resolution_status": "RESOLVED",
                "notes": "schema corrected during I13 run",
            }
        ),
        DocumentationRuntimeContradiction.model_validate(
            {
                "contradiction_id": "contr_i13_bybit_region_block",
                "provider_id": "BYBIT_LINEAR",
                "sensor_family": SensorFamily.MECHANICAL_OPEN_INTEREST,
                "documentation_claim": "public market endpoints reachable without account",
                "documentation_source_ref": "bybit probe model",
                "runtime_observation": (
                    "HTTP 403 CloudFront 'blocked access from your country' on market "
                    "endpoints -> F_ACCESS_GEO (was mis-mapped to auth; classifier fixed)."
                ),
                "severity": "BLOCKING",
                "resolution_status": "OPEN",
                "notes": "regional geo block; no bypass attempted",
            }
        ),
        DocumentationRuntimeContradiction.model_validate(
            {
                "contradiction_id": "contr_i13_kraken_analytics_history_reach",
                "provider_id": "KRAKEN_FUTURES",
                "sensor_family": SensorFamily.MECHANICAL_OPEN_INTEREST,
                "documentation_claim": "Market Analytics is a deep historical mechanical source",
                "documentation_source_ref": "I12R1 contract review",
                "runtime_observation": (
                    "OI/funding analytics VERIFIED for recent+2024 but return EMPTY_VALID "
                    "at the 2022 checkpoint — historical reach appears limited, not deep."
                ),
                "severity": "MATERIAL",
                "resolution_status": "OPEN",
                "notes": "current-only/limited reach characterization a key I13 finding",
            }
        ),
    ]


def _network_failed(
    request: CapabilityProbeRequest, exc: requests.RequestException
) -> CapabilityProbeAttempt:
    cls = ProbeFailureClass.F_NETWORK_TIMEOUT
    if isinstance(exc, requests.exceptions.ConnectionError):
        cls = ProbeFailureClass.F_NETWORK_DNS
    return CapabilityProbeAttempt.model_validate(
        {
            "probe_id": (f"{request.provider_id.lower()}_{request.sensor_family.value.lower().replace('mechanical_', '')}_netfail"),
            "probe_run_id": request.probe_run_id,
            "provider_id": request.provider_id,
            "sensor_family": request.sensor_family,
            "venue_market": request.provider_id,
            "instrument_native": request.instrument_native,
            "canonical_asset_hint": request.canonical_asset_hint,
            "requested_start": request.requested_start,
            "requested_end": request.requested_end,
            "requested_granularity": request.requested_granularity,
            "access_mode": request.access_mode,
            "query_mode": request.query_mode,
            "request_method": "GET",
            "response_status_class": ResponseStatusClass.FAILED,
            "error_class": cls,
            "error_detail_redacted": "network error (no response)",
            "era_hint": request.era_hint,
            "probe_version": "sensor-probe-v1-live",
        }
    )


def _print_summary(attempts, claims) -> None:
    from collections import Counter

    counts = Counter(a.response_status_class.value for a in attempts)
    errs = dict(
        Counter(a.error_class.value for a in attempts if a.error_class is not None)
    )
    verified = sum(1 for a in attempts if a.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE)
    print("\n==== I13 SUMMARY ====")
    print(f"attempts by status: {dict(counts)}")
    print(f"failure classes: {errs}")
    print(f"verified samples (E2/E3/E4): {verified}")
    print(f"claims synthesized: {len(claims)}")


if __name__ == "__main__":
    raise SystemExit(main())