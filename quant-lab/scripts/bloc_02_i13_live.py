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
import re
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

#: Provider/sensor scopes that are CURRENT-ONLY surfaces (book snapshots,
# latest-only recent-trade): historical checkpoints are NOT attempted for
# these and their era cells read CURRENT_ONLY (I13R1 §4).  Trade scopes with
# documented historical routes (OKX history-trades, Deribit include_old,
# Kraken /history) are NOT current-only.
CURRENT_ONLY_SCOPES = frozenset(
    {
        ("KRAKEN_FUTURES", "MECHANICAL_BOOK_SNAPSHOT"),
        ("GATE_FUTURES", "MECHANICAL_BOOK_SNAPSHOT"),
        ("GATE_FUTURES", "MECHANICAL_TRADE"),
        ("BYBIT_LINEAR", "MECHANICAL_BOOK_SNAPSHOT"),
        ("BYBIT_LINEAR", "MECHANICAL_TRADE"),
        ("BINANCE_USDM", "MECHANICAL_BOOK_SNAPSHOT"),
        ("BINANCE_USDM", "MECHANICAL_TRADE"),
        ("OKX_SWAP", "MECHANICAL_BOOK_SNAPSHOT"),
        ("DERIBIT", "MECHANICAL_BOOK_SNAPSHOT"),
    }
)

#: Provider/sensor pairs whose HISTORICAL window is already proven bounded by a
# VERIFIED retention boundary (Gate contract_stats 180-day limit observed at
# the 2022 checkpoint: "from time exceeds 180-day limit").  Older dates are
# synthesized as HISTORY_BLOCKED_BY_VERIFIED_RETENTION_BOUNDARY, never probed
# or shown UNATTEMPTED (I13R1 §4).
VERIFIED_RETENTION_BOUNDARY_SCOPES = frozenset(
    {
        ("GATE_FUTURES", "MECHANICAL_OPEN_INTEREST"),
        ("GATE_FUTURES", "MECHANICAL_LIQUIDATION"),
        ("GATE_FUTURES", "MECHANICAL_POSITIONING"),
        # funding_rate shares the rolling 180-day boundary (live-observed: older
        # `from` -> "from time exceeds 180-day limit"; 2026-06-15 works in seconds)
        ("GATE_FUTURES", "MECHANICAL_FUNDING"),
    }
)

#: Provider/sensor pairs whose RECENT control already hard-blocked the whole
# surface (geo/auth): older eras are NOT reattempted and are synthesized with
# the same surface-level status, not UNATTEMPTED (I13R1 §4).
SURFACE_BLOCKED_RECENT_SCOPES = frozenset(
    {
        ("BINANCE_USDM", "MECHANICAL_OPEN_INTEREST"),
        ("BINANCE_USDM", "MECHANICAL_TRADE"),
        ("BINANCE_USDM", "MECHANICAL_FUNDING"),
        ("BINANCE_USDM", "MECHANICAL_BOOK_SNAPSHOT"),
        ("BYBIT_LINEAR", "MECHANICAL_OPEN_INTEREST"),
        ("BYBIT_LINEAR", "MECHANICAL_TRADE"),
        ("BYBIT_LINEAR", "MECHANICAL_FUNDING"),
        ("BYBIT_LINEAR", "MECHANICAL_BOOK_SNAPSHOT"),
    }
)

#: FULL frozen checkpoint matrix per scope (I13R1 §4): RECENT + 2021 + 2022 +
# 2024 + 2026 for every provider/sensor where recent control succeeds AND the
# source claims/supports historical querying.  Short-circuits: current-only
# sensors probe RECENT only; retention-boundary scopes probe RECENT + the era
# inside the rolling window (2026) and synthesize older dates as the verified
# boundary; geo/auth surface-blocked REST probes RECENT only (archive routes
# are planned independently).
SCOPE: dict[str, list[dict[str, Any]]] = {
    "KRAKEN_FUTURES": [
        {"sensor": "MECHANICAL_OPEN_INTEREST", "assets": ("BTC", "ETH"), "eras": ERAS},
        {"sensor": "MECHANICAL_FUNDING", "assets": ("BTC",), "eras": ERAS},
        {"sensor": "MECHANICAL_BASIS", "assets": ("BTC",), "eras": ERAS},
        {"sensor": "MECHANICAL_POSITIONING", "assets": ("BTC",), "eras": ERAS},
        {"sensor": "MECHANICAL_BOOK_METRIC", "assets": ("BTC",), "eras": ERAS},
        {"sensor": "MECHANICAL_LIQUIDATION", "assets": ("BTC",), "eras": ERAS, "analytics_type": "liquidation-volume"},
        {"sensor": "MECHANICAL_TRADE", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_BOOK_SNAPSHOT", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
    ],
    "GATE_FUTURES": [
        {"sensor": "MECHANICAL_OPEN_INTEREST", "assets": ("BTC",), "eras": ("RECENT_CONTROL", "2026")},
        {"sensor": "MECHANICAL_LIQUIDATION", "assets": ("BTC",), "eras": ("RECENT_CONTROL", "2026")},
        {"sensor": "MECHANICAL_POSITIONING", "assets": ("BTC",), "eras": ("RECENT_CONTROL", "2026")},
        {"sensor": "MECHANICAL_FUNDING", "assets": ("BTC",), "eras": ("RECENT_CONTROL", "2026")},
        {"sensor": "MECHANICAL_TRADE", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_BOOK_SNAPSHOT", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
    ],
    "BYBIT_LINEAR": [
        {"sensor": "MECHANICAL_OPEN_INTEREST", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_FUNDING", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_TRADE", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_BOOK_SNAPSHOT", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
    ],
    "BINANCE_USDM": [
        {"sensor": "MECHANICAL_OPEN_INTEREST", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_TRADE", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_FUNDING", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "MECHANICAL_BOOK_SNAPSHOT", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
        {"sensor": "ARCHIVE_METRICS", "assets": ("BTC",), "eras": ("2021", "2022", "2024", "2026")},
        {"sensor": "ARCHIVE_AGGTRADES", "assets": ("BTC",), "eras": ("2021", "2022", "2024", "2026")},
    ],
    "OKX_SWAP": [
        {"sensor": "MECHANICAL_FUNDING", "assets": ("BTC",), "eras": ERAS},
        {"sensor": "MECHANICAL_TRADE", "assets": ("BTC",), "eras": ERAS},
        {"sensor": "MECHANICAL_BOOK_SNAPSHOT", "assets": ("BTC",), "eras": ("RECENT_CONTROL",)},
    ],
    "DERIBIT": [
        {"sensor": "MECHANICAL_TRADE", "assets": ("BTC",), "eras": ERAS},
        {"sensor": "MECHANICAL_LIQUIDATION", "assets": ("BTC",), "eras": ("RECENT_CONTROL", "2022")},
        {"sensor": "MECHANICAL_FUNDING", "assets": ("BTC",), "eras": ERAS},
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
    hints: dict[str, Any] = {"era": era}
    # I13R1: Kraken liquidation probes the bucketed `liquidation-volume`
    # Market Analytics surface (analytics_type hint) while the offline default
    # stays trade-level /history anatomy.
    if provider_id == "KRAKEN_FUTURES" and sensor is SensorFamily.MECHANICAL_LIQUIDATION:
        hints["analytics_type"] = "liquidation-volume"
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
            "provider_hints": hints,
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
#: PIT timestamp-semantics facts per (provider, sensor) for verified scopes
# (I13R1 §6).  Values are the DOCUMENTED/OBSERVED semantics for scopes whose
# data semantics were verified live; everything defaults to unresolved
# (fail closed).  A scope only becomes PIT_READY_* when its facts are True.
#
# Keys: effective_ts, observation_ts, publication_delay (True/None),
# forward_info, forward_resolved, publication_affects_reconstruction.
_PIT_FACTS: dict[tuple[str, str], dict[str, Any]] = {
    ("KRAKEN_FUTURES", "MECHANICAL_OPEN_INTEREST"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("KRAKEN_FUTURES", "MECHANICAL_FUNDING"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("KRAKEN_FUTURES", "MECHANICAL_BASIS"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("KRAKEN_FUTURES", "MECHANICAL_POSITIONING"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("KRAKEN_FUTURES", "MECHANICAL_BOOK_METRIC"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("KRAKEN_FUTURES", "MECHANICAL_LIQUIDATION"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("GATE_FUTURES", "MECHANICAL_OPEN_INTEREST"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("GATE_FUTURES", "MECHANICAL_LIQUIDATION"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("GATE_FUTURES", "MECHANICAL_POSITIONING"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("GATE_FUTURES", "MECHANICAL_FUNDING"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("OKX_SWAP", "MECHANICAL_FUNDING"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("OKX_SWAP", "MECHANICAL_TRADE"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("OKX_SWAP", "MECHANICAL_BOOK_SNAPSHOT"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("DERIBIT", "MECHANICAL_TRADE"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("DERIBIT", "MECHANICAL_LIQUIDATION"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("DERIBIT", "MECHANICAL_FUNDING"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
    ("DERIBIT", "MECHANICAL_BOOK_SNAPSHOT"): {
        "effective_ts": True, "observation_ts": True, "publication_delay": None,
        "forward_info": False, "forward_resolved": True, "pub_affects": False,
    },
}


#: Scopes whose data semantics were NOT verified live (metadata/existence only)
#: — never count toward verified redundancy, never PIT-ready (I13R1 §8-9).
METADATA_ONLY_SCOPES = frozenset(
    {
        ("BITFINEX_COMMUNITY_ARCHIVE", "MECHANICAL_LIQUIDATION"),
        ("BINANCE_USDM", "MECHANICAL_OPEN_INTEREST"),  # archive existence only
        ("BINANCE_USDM", "MECHANICAL_TRADE"),  # archive existence only
    }
)


#: Canonical scope universe = the frozen provider_probe_endpoints.yaml registry
# (34 provider/sensor scopes, I13R1 §3).  A scope with NO attempts still
# appears in every report as UNATTEMPTED/E0 — NO ATTEMPT != NO CAPABILITY NODE.
def canonical_scope_universe() -> list[tuple[str, SensorFamily]]:
    from crypto_sensor_fabric._paths import CONFIG_DIR

    data = yaml.safe_load(
        (CONFIG_DIR / "provider_probe_endpoints.yaml").read_text(encoding="utf-8")
    )
    out: list[tuple[str, SensorFamily]] = []
    for pid, entry in data["providers"].items():
        for sensor_name in entry.get("endpoints", {}):
            out.append((pid, SensorFamily(sensor_name)))
    return out


def _pit_facts_for(pid: str, sensor: SensorFamily) -> dict[str, Any]:
    return _PIT_FACTS.get((pid, sensor.value), {})


def _scope_blocking_reason(
    pid: str, sensor: SensorFamily, verified_dates: list, recent_status: CapabilityStatus | None
) -> str | None:
    if verified_dates:
        return None
    if (pid, sensor.value) in CURRENT_ONLY_SCOPES:
        return "CURRENT_ONLY surface (no historical window to verify)"
    if recent_status is CapabilityStatus.GEO_BLOCKED:
        return "surface geo-blocked from operator region (no bypass)"
    if recent_status is CapabilityStatus.AUTH_BLOCKED:
        return "auth-gated surface (no credentials required for Sensor Fabric)"
    if (pid, sensor.value) in VERIFIED_RETENTION_BOUNDARY_SCOPES:
        return "verified retention boundary (rolling window); older dates not probed"
    if pid == "COINALYZE":
        return "CREDENTIAL_NOT_CONFIGURED (free key not configured locally)"
    return "no live verified sample yet (E0/UNVERIFIED or blocked)"


def _era_status_for_scope(
    pid: str,
    sensor: SensorFamily,
    group: list[CapabilityProbeAttempt],
) -> dict[str, CapabilityStatus]:
    """Per-era status across the FULL frozen matrix (RECENT + 2021-2026).

    Every canonical scope carries all five era cells (I13R1 §4): never fewer
    rows because an era was not attempted.  Short-circuits:
    - CURRENT_ONLY scopes: historical cells read CURRENT_ONLY (not attempted).
    - VERIFIED retention-boundary scopes: older cells read
      HISTORY_BLOCKED_BY_VERIFIED_RETENTION_BOUNDARY.
    - surface-blocked (geo/auth) scopes: all historical cells read the same
      surface status (not UNATTEMPTED — the block is region/surface-wide).
    - otherwise unattempted cells read UNATTEMPTED.
    """
    attempt_by_era: dict[str, list[CapabilityProbeAttempt]] = {}
    for a in group:
        attempt_by_era.setdefault(a.era_hint or "RECENT_CONTROL", []).append(a)
    recent_status = (
        _attempt_status(attempt_by_era["RECENT_CONTROL"][-1])
        if attempt_by_era.get("RECENT_CONTROL")
        else None
    )
    surface_status = None
    if recent_status in (CapabilityStatus.GEO_BLOCKED, CapabilityStatus.AUTH_BLOCKED):
        surface_status = recent_status
    out: dict[str, CapabilityStatus] = {}
    for era in list(ERAS):
        if attempt_by_era.get(era):
            if (
                (pid, sensor.value) in VERIFIED_RETENTION_BOUNDARY_SCOPES
                and all(_is_retention_boundary_evidence(a) for a in attempt_by_era[era])
            ):
                # the provider itself proved the rolling boundary at this date
                out[era] = CapabilityStatus.HISTORY_BLOCKED_BY_VERIFIED_RETENTION_BOUNDARY
            else:
                out[era] = _attempt_status(attempt_by_era[era][-1])
            continue
        if era == "RECENT_CONTROL":
            out[era] = CapabilityStatus.UNATTEMPTED
            continue
        if (pid, sensor.value) in CURRENT_ONLY_SCOPES:
            out[era] = CapabilityStatus.CURRENT_ONLY
        elif (pid, sensor.value) in VERIFIED_RETENTION_BOUNDARY_SCOPES:
            out[era] = CapabilityStatus.HISTORY_BLOCKED_BY_VERIFIED_RETENTION_BOUNDARY
        elif surface_status is not None:
            out[era] = surface_status
        else:
            out[era] = CapabilityStatus.UNATTEMPTED
    return out


def attempts_to_records(
    attempts: list[CapabilityProbeAttempt],
) -> tuple[list[CapabilityClaim], list[ProviderSensorCoverage], list[FailureRecord]]:
    """Synthesize claims/coverages over the CANONICAL 34-scope universe.

    The universe comes from the frozen registry; observed attempts overlay it.
    A scope with no attempts stays UNATTEMPTED/E0 and never disappears from the
    reports (I13R1 §3).  Claims E2+ carry their attempt evidence_ids (I13R1 §7).
    """
    claims: list[CapabilityClaim] = []
    coverages: list[ProviderSensorCoverage] = []
    failures: list[FailureRecord] = []
    by_scope: dict[tuple[str, str], list[CapabilityProbeAttempt]] = {}
    for a in attempts:
        by_scope.setdefault((a.provider_id, a.sensor_family.value), []).append(a)
    universe = canonical_scope_universe()
    for idx, (pid, sensor) in enumerate(sorted(universe), start=1):
        group = by_scope.get((pid, sensor.value), [])
        claim = synthesize_claim(
            claim_id=f"claim_bloc2_{pid.lower()}_{sensor.value.lower()}_{idx:03d}_live",
            provider_id=pid,
            sensor_family=sensor,
            venue_market=pid,
            access_mode=ACCESS[pid],
            attempts=group,
        )
        era_status = _era_status_for_scope(pid, sensor, group)
        verified_dates = [
            a.requested_start
            for a in group
            if a.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE
        ]
        facts = _pit_facts_for(pid, sensor)
        effective_ts = facts.get("effective_ts")
        observation_ts = facts.get("observation_ts")
        metadata_only = (pid, sensor.value) in METADATA_ONLY_SCOPES
        data_semantics_verified = bool(verified_dates) and not metadata_only
        if metadata_only or not verified_dates:
            effective_ts = False
            observation_ts = False
        from crypto_sensor_fabric.probes.evidence import assess_pit_readiness

        pit_readiness, pit_reason = assess_pit_readiness(
            effective_ts_understood=effective_ts,
            observation_ts_understood=observation_ts,
            publication_delay_understood=facts.get("publication_delay"),
            forward_info_required=bool(facts.get("forward_info")),
            forward_availability_resolved=facts.get("forward_resolved"),
            publication_affects_reconstruction=facts.get("pub_affects"),
        )
        recent_status = era_status.get("RECENT_CONTROL")
        blocking = _scope_blocking_reason(pid, sensor, verified_dates, recent_status)
        coverage = ProviderSensorCoverage.model_validate(
            {
                "provider_id": pid,
                "sensor_family": sensor,
                "venue_market": pid,
                "instrument_scope": sorted({a.instrument_native for a in group}) or [],
                "access_mode": ACCESS[pid],
                "era_status": era_status,
                "earliest_verified_history": min(verified_dates) if verified_dates else None,
                "latest_verified_history": max(verified_dates) if verified_dates else None,
                "granularity_scope": sorted(
                    {a.requested_granularity for a in group}, key=lambda g: g.value
                ),
                "PIT_readiness": pit_readiness,
                "evidence_level": claim.evidence_level,
                "provider_role": ProviderRole.REFERENCE_ONLY,
                "promotion_eligible": False,
                "blocking_reason": blocking,
                "pit_effective_ts_understood": effective_ts,
                "pit_observation_ts_understood": observation_ts,
                "pit_publication_delay_understood": facts.get("publication_delay"),
                "pit_forward_info_required": bool(facts.get("forward_info")),
                "pit_forward_availability_resolved": facts.get("forward_resolved"),
                "pit_publication_affects_reconstruction": facts.get("pub_affects"),
                "pit_blocking_reason": pit_reason,
                "data_semantics_verified": data_semantics_verified,
            }
        )
        # keep claim PIT + data-semantics consistent with the coverage
        claim = claim.model_copy(
            update={
                "PIT_readiness": pit_readiness,
                "pit_effective_ts_understood": effective_ts,
                "pit_observation_ts_understood": observation_ts,
                "pit_publication_delay_understood": facts.get("publication_delay"),
                "pit_forward_info_required": bool(facts.get("forward_info")),
                "pit_forward_availability_resolved": facts.get("forward_resolved"),
                "pit_publication_affects_reconstruction": facts.get("pub_affects"),
                "pit_blocking_reason": pit_reason,
                "data_semantics_verified": data_semantics_verified,
                "known_gaps": _known_gaps(pid, sensor, group, era_status),
                "limitations": _limitations(pid, sensor, group, era_status),
            }
        )
        claims.append(claim)
        coverages.append(coverage)
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


def _known_gaps(
    pid: str,
    sensor: SensorFamily,
    group: list[CapabilityProbeAttempt],
    era_status: dict[str, CapabilityStatus],
) -> list[str]:
    gaps: list[str] = []
    for era in ("2021", "2022", "2024", "2026"):
        if era_status.get(era) is CapabilityStatus.HISTORY_BLOCKED_BY_VERIFIED_RETENTION_BOUNDARY:
            gaps.append(f"{era} beyond verified {pid} retention boundary (rolling window)")
        elif era_status.get(era) in (CapabilityStatus.UNATTEMPTED, CapabilityStatus.CURRENT_ONLY):
            gaps.append(f"{era} not attempted ({era_status[era].value})")
    empty_eras = sorted(
        {
            (a.era_hint or "RECENT_CONTROL")
            for a in group
            if a.response_status_class is ResponseStatusClass.EMPTY_VALID
        }
    )
    if empty_eras:
        gaps.append(f"EMPTY_VALID at {', '.join(empty_eras)} (valid request, no rows)")
    return gaps


def _limitations(
    pid: str,
    sensor: SensorFamily,
    group: list[CapabilityProbeAttempt],
    era_status: dict[str, CapabilityStatus],
) -> list[str]:
    limitations: list[str] = []
    if (pid, sensor.value) in METADATA_ONLY_SCOPES and any(
        a.response_status_class is ResponseStatusClass.VERIFIED_SAMPLE for a in group
    ):
        limitations.append(
            "SOURCE_AVAILABILITY_VERIFIED only — row timestamps/schema not "
            "inspected (metadata/existence evidence)"
        )
    if pid == "COINALYZE":
        limitations.append("CREDENTIAL_NOT_CONFIGURED (no local free key)")
    return limitations


def _attempt_key(a: CapabilityProbeAttempt) -> tuple[str, str, str, str]:
    """Stable merge key: (provider, sensor, asset, era).

    Binance archive attempts record the mechanical sensor they characterize
    (MECHANICAL_OPEN_INTEREST / MECHANICAL_TRADE) but plan under
    ARCHIVE_METRICS / ARCHIVE_AGGTRADES — normalize via the recorded
    `archive_kind` so merge-on-resume does not re-execute archive probes.
    """
    sensor = a.sensor_family.value
    if a.provider_id == "BINANCE_USDM" and a.access_mode is AccessMode.PUBLIC_ARCHIVE:
        kind = (a.native_units_summary or {}).get("archive_kind")
        if kind == "metrics":
            sensor = "ARCHIVE_METRICS"
        elif kind == "aggTrades":
            sensor = "ARCHIVE_AGGTRADES"
    return (
        a.provider_id,
        sensor,
        a.canonical_asset_hint or a.instrument_native,
        a.era_hint or "RECENT_CONTROL",
    )


def _plan_count() -> int:
    """Total planned probe count from SCOPE (dry-run / summary)."""
    return sum(
        len(scope["assets"]) * len(scope["eras"])
        for scopes in SCOPE.values()
        for scope in scopes
    )


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
    if a.error_class is ProbeFailureClass.F_CLIENT_4XX:
        # deterministic client error (e.g. wrong units / retention rejection) —
        # never a transient failure
        return CapabilityStatus.UNVERIFIED
    if a.response_status_class is ResponseStatusClass.FAILED:
        return CapabilityStatus.TRANSIENT_FAILURE
    return CapabilityStatus.UNVERIFIED


def _is_retention_boundary_evidence(a: CapabilityProbeAttempt) -> bool:
    """True when a failed attempt is explicit provider retention-boundary
    evidence (e.g. Gate "from time exceeds 180-day limit"), which the operator
    directive maps to HISTORY_BLOCKED_BY_VERIFIED_RETENTION_BOUNDARY (§4)."""
    if a.error_class is not ProbeFailureClass.F_CLIENT_4XX:
        return False
    detail = (a.error_detail_redacted or "").lower()
    return any(k in detail for k in ("limit", "retention", "range")) and any(
        k in detail for k in ("exceeds", "180", "beyond", "too far", "outside")
    )


def redundancy_summaries(
    coverages: list[ProviderSensorCoverage],
    claims: list[CapabilityClaim],
) -> list[SensorRedundancySummary]:
    """Verified-only, evidence-aware redundancy (I13R1 §8).

    A provider counts toward VERIFIED redundancy only when its claim is at
    least E2_LIVE_RECENT_VERIFIED AND its data semantics were verified.  E0,
    blocked, unattempted, schema-unusable and EMPTY_VALID-only scopes NEVER
    count.  Community/aggregator sources stay correctly typed (diversity only).
    """
    from crypto_sensor_fabric.contracts.enums import SensorFamily

    from crypto_sensor_fabric.probes.enums import EvidenceLevel as EvL

    claim_by_scope = {(c.provider_id, c.sensor_family.value): c for c in claims}
    by_sensor: dict[str, list[ProviderSensorCoverage]] = {}
    for c in coverages:
        claim = claim_by_scope.get((c.provider_id, c.sensor_family.value))
        if claim is None:
            continue
        verified_enough = (
            claim.evidence_level
            in (EvL.E2_LIVE_RECENT_VERIFIED, EvL.E3_HISTORICAL_CHECKPOINT_VERIFIED, EvL.E4_MULTI_ERA_VERIFIED, EvL.E5_REPRODUCIBLE_COVERAGE_VERIFIED)
            and claim.data_semantics_verified
        )
        if verified_enough:
            by_sensor.setdefault(c.sensor_family.value, []).append(c)
    out: list[SensorRedundancySummary] = []
    for sensor in sorted(by_sensor):
        rows = by_sensor[sensor]
        first_party_rows = [
            r
            for r in rows
            if r.access_mode not in (AccessMode.FREE_API_KEY, AccessMode.COMMUNITY_ARCHIVE)
        ]
        independent_venues = {r.venue_market for r in first_party_rows}
        if len(independent_venues) >= 3:
            _class = RedundancyClass.R3_THREE_PLUS_INDEPENDENT
        elif len(independent_venues) == 2:
            _class = RedundancyClass.R2_TWO_INDEPENDENT
        elif len(independent_venues) == 1:
            _class = RedundancyClass.R1_SINGLE_INDEPENDENT
        else:
            _class = RedundancyClass.R0_NONE
        out.append(
            SensorRedundancySummary.model_validate(
                {
                    "sensor_family": SensorFamily(sensor),
                    "verified_provider_count": len(rows),
                    "verified_venues": sorted({r.venue_market for r in rows}),
                    "redundancy_class": _class,
                    "first_party_count": len(first_party_rows),
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
                    "gap_status": "ADEQUATE" if len(independent_venues) >= 2 else ("SINGLE_SOURCE" if len(independent_venues) == 1 else "INSUFFICIENT"),
                    "notes": "verified data-semantics only (I13R1); roles not frozen",
                }
            )
        )
    return out


def free_only_rows() -> list[dict[str, Any]]:
    """Free-only audit from the registry + live evidence (I13R1 §11).

    Bitfinex community GitHub/LFS source is PUBLIC: no API key, no account, no
    payment.  Only FREE_API_KEY providers (Coinalyze) require a key.
    """
    from crypto_sensor_fabric._paths import CONFIG_DIR

    data = yaml.safe_load((CONFIG_DIR / "provider_probe_endpoints.yaml").read_text(encoding="utf-8"))
    rows = []
    for pid, entry in data["providers"].items():
        access = entry.get("access", "")
        api_key_required = access == "FREE_API_KEY"
        rows.append(
            {
                "provider_id": pid,
                "sensor_family": "|".join(sorted(entry.get("endpoints", {}))) or "",
                "access_mode": access,
                "api_key_required": api_key_required,
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
    all_attempts: list[CapabilityProbeAttempt] = []
    if attempts_path.exists() and not args.force:
        # MERGE-ON-RESUME (I13R1): keep prior attempts and execute ONLY the
        # newly planned probes (restored scopes + full frozen checkpoint
        # matrix).  No blind re-hit of already-recorded requests.
        print(f"merging with existing {attempts_path} (use --force to re-run live)")
        all_attempts = [
            CapabilityProbeAttempt.model_validate(json.loads(line))
            for line in attempts_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        # I13R1 §10: supersede ONLY attempts made under a REQUEST_CONTRACT_INVALID
        # contract (Gate funding probed on the plural batch POST /funding_rates
        # under a GET-style model -> INVALID_CREDENTIALS; then funding+trades on
        # the single GET with ms from/to -> EMPTY; live smoke + first-party docs
        # proved from/to are Unix SECONDS).  Attempts already recorded under the
        # corrected seconds contract are NOT superseded — merges stay idempotent.
        superseded: list[CapabilityProbeAttempt] = []
        for a in all_attempts:
            if a.provider_id != "GATE_FUTURES" or a.sensor_family not in (
                SensorFamily.MECHANICAL_FUNDING,
                SensorFamily.MECHANICAL_TRADE,
            ):
                continue
            fp = a.request_fingerprint or ""
            plural_batch = "/funding_rates" in fp
            ms_window = bool(
                re.search(r"from=[0-9]{13}", fp) or re.search(r"to=[0-9]{13}", fp)
            )
            if plural_batch or ms_window:
                superseded.append(a)
        if superseded:
            print(
                f"  superseding {len(superseded)} Gate funding/trade attempt(s) under an "
                "obsolete request contract (REQUEST_CONTRACT_INVALID: plural batch "
                "route or ms from/to; live + docs prove Unix SECONDS) "
                "-> corrected seconds-based requests will be probed"
            )
            all_attempts = [a for a in all_attempts if a not in superseded]
        if args.dry_run:
            planned = _plan_count()
            print(f"merge-mode dry run: existing={len(all_attempts)} planned={planned}")
            return 0

    session = requests.Session()
    session.headers.update({"User-Agent": "codebuff-crypto-sensor-fabric-bloc2-i13/1.0 (capability characterization)"})

    executed = 0
    skipped_merged = 0
    hard_blocked: set[tuple[str, str]] = set()
    existing_keys = {_attempt_key(a) for a in all_attempts}

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
                    key = (pid, scope["sensor"], asset, era)
                    if key in existing_keys:
                        skipped_merged += 1
                        continue
                    if (pid, scope["sensor"]) in hard_blocked and era != "RECENT_CONTROL":
                        print(f"  skip {scope['sensor']}/{asset}/{era} (recent hard-blocked)")
                        continue
                    if args.dry_run:
                        continue
                    sr = scope["sensor"]
                    if sr.startswith("ARCHIVE_"):
                        kind = "metrics" if sr == "ARCHIVE_METRICS" else "aggTrades"
                        req = build_request(probe, pid, SensorFamily.MECHANICAL_OPEN_INTEREST if sr == "ARCHIVE_METRICS" else SensorFamily.MECHANICAL_TRADE, asset, era, probe_run_id)
                        date = CHECKPOINT_DATES[era].date().isoformat()
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

    planned = _plan_count()
    print(f"\nplanned={planned} executed_new={executed} merged_skipped={skipped_merged} attempts={len(all_attempts)}")

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
    from crypto_sensor_fabric.probes.evidence import validate_claims_lineage

    violations = validate_claims_lineage(claims, all_attempts)
    if violations:
        raise SystemExit(
            "evidence lineage violations (I13R1 §7):\n  " + "\n  ".join(violations)
        )
    written = write_reports(
        output_dir=str(PACKET_DIR),
        run=run,
        attempts=all_attempts,
        claims=claims,
        coverages=coverages,
        redundancies=redundancy_summaries(coverages, claims),
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
                "contradiction_id": "contr_i13_gate_funding_plural_route_auth",
                "provider_id": "GATE_FUTURES",
                "sensor_family": SensorFamily.MECHANICAL_FUNDING,
                "documentation_claim": "funding history is a public no-auth route",
                "documentation_source_ref": "live_probe_contracts.yaml + gate docs (funding_rate single-contract GET)",
                "runtime_observation": (
                    "The previous probe used the PLURAL batch POST /funding_rates under a "
                    "GET-style model -> HTTP 401 INVALID_CREDENTIALS.  That attempt is a "
                    "REQUEST_CONTRACT_INVALID, NOT a provider auth failure.  Corrected to "
                    "single-contract GET /funding_rate?contract=... (no auth) (I13R1 §10)."
                ),
                "severity": "MATERIAL",
                "resolution_status": "RESOLVED",
                "notes": "funding contract corrected during I13R1; old F_ACCESS_AUTH not preserved as capability truth",
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