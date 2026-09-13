"""OKX Swap — I14-bounded capability + native acquisition-mode freeze.

This is the SENSOR-B3-I07 capability/contract freeze.  The OKX package is
bound strictly to the I14 promotion set for OKX_SWAP (EXACTLY THREE paths):

    MECHANICAL_BOOK_SNAPSHOT  (CURRENT_ONLY)
    MECHANICAL_FUNDING        (PRIMARY, HISTORICAL)
    MECHANICAL_TRADE          (PRIMARY, HISTORICAL)

The promoted production instrument is BTC-USDT-SWAP for all three paths
(from the committed 08_HISTORY_BOUNDARIES.csv per-instrument evidence).
Everything else that OKX may offer is typed `CapabilityUnavailable` under the
CURRENT I14 freeze:

    MECHANICAL_BASIS, MECHANICAL_BOOK_METRIC, MECHANICAL_LIQUIDATION,
    MECHANICAL_OPEN_INTEREST, MECHANICAL_POSITIONING

FUTURE-QUEUE EXCLUSIONS (recorded, NOT production): provider premium/basis and
deeper historical-order-book research are queued for later source-expansion;
they must NOT mutate or broaden I07.  The public traderecords archive is a
Bloc 2 characterization surface and is NOT a production REST substitution.

I05R1-style boundary hardening separates the Bloc 2 PROBE universe (probe
`NATIVE_INSTRUMENTS`: BTC/ETH/SOL/DOGE-USDT-SWAP) from PRODUCTION instrument
support.  Production symbol scope is derived ONLY from the committed
structured coverage artifact `08_HISTORY_BOUNDARIES.csv` (provider x sensor x
instrument rows), never from the probe map.

Native acquisition surface (grounded in committed Bloc 2 evidence,
live_probe_contracts.yaml + probe.py):

- MECHANICAL_FUNDING: GET `/api/v5/public/funding-rate-history`
  (PUBLIC namespace, NOT /market), `instId` + `limit`, after/before keyed
  around `fundingTime` timestamps (epoch ms), NOT trade ids.
- MECHANICAL_TRADE:   GET `/api/v5/market/history-trades`, `instId` + `limit`,
  after/before keyed around provider-native trade ids.
- MECHANICAL_BOOK_SNAPSHOT: GET `/api/v5/market/books`, `instId` + `sz=400`,
  CURRENT snapshot only — no `start`/`end`/`after`/`before`/historical cursor,
  no historical depth (deep book history UNVERIFIED, never claimed).

The exact native historical_mode must be granted through a
`ProviderNativeCapabilityEvidence` validated against the I14 bound; the grant
may REFINE acquisition mechanics but never broaden scope/role/PIT/methodology/
access/live/archive/instrument scope.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, cast

from ..._paths import QUANT_LAB_ROOT
from ...contracts.enums import SensorFamily
from ..base import (
    ProviderCapabilities,
    ProviderNativeCapabilityEvidence,
    apply_native_evidence,
    capabilities_from_promotion,
    load_promotion_candidates,
)
from ..base.enums import HistoricalMode, PaginationMode

PROVIDER_ID = "OKX_SWAP"

#: Structured per-instrument coverage artifact (I13R1 runtime evidence).  This
#: is the authoritative machine-readable provider x sensor x instrument map;
#: production symbol scope is derived from it, never hand-maintained.
OKX_HISTORY_BOUNDARIES_FILE = (
    QUANT_LAB_ROOT
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_02"
    / "08_HISTORY_BOUNDARIES.csv"
)

#: Full Bloc 2 probe/control universe (probe.NATIVE_INSTRUMENTS: BTC/ETH/SOL/
#: MID_TAIL_CONTROL -> DOGE).  Kept intact for characterization history; NOT
#: production support (I05R1 boundary, applied here for OKX).
OKX_PROBE_INSTRUMENT_SCOPE: list[str] = [
    "BTC-USDT-SWAP",
    "ETH-USDT-SWAP",
    "SOL-USDT-SWAP",
    "DOGE-USDT-SWAP",
]

#: Canonical promoted-sensor order used for stable production-scope ordering.
_PROMOTED_ORDER: tuple[SensorFamily, ...] = (
    SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
    SensorFamily.MECHANICAL_FUNDING,
    SensorFamily.MECHANICAL_TRADE,
)

#: The exact set of promoted OKX production sensors (from I14).  Used for the
#: exact-set completeness test: declared production set == this set.
OKX_PROMOTED_SENSORS: frozenset[SensorFamily] = frozenset(_PROMOTED_ORDER)

#: Endpoint families for fingerprint / provenance identity.
OKX_FUNDING_RATE_HISTORY_PATH = "/api/v5/public/funding-rate-history"
OKX_HISTORY_TRADES_PATH = "/api/v5/market/history-trades"
OKX_MARKET_BOOKS_PATH = "/api/v5/market/books"
OKX_REST_BASE = "www.okx.com"


def okx_endpoint_family(sensor: SensorFamily) -> str:
    """Endpoint/provenance family for a promoted OKX sensor."""
    if sensor is SensorFamily.MECHANICAL_FUNDING:
        return "okx-swap-funding-rate-history"
    if sensor is SensorFamily.MECHANICAL_TRADE:
        return "okx-swap-history-trades"
    # BOOK_SNAPSHOT (the only remaining promoted path)
    return "okx-swap-market-books"


def okx_symbol_scopes_from_evidence(
    path: Path | None = None,
) -> dict[SensorFamily, tuple[str, ...]]:
    """Per-promoted-sensor PRODUCTION symbol scope from committed evidence.

    Reads `08_HISTORY_BOUNDARIES.csv` (I13R1 runtime artifact, provider x
    sensor x instrument rows) and returns the instrument list for each
    promoted OKX sensor in file order (deduplicated).  Fails CLOSED on a
    missing/malformed artifact or a promoted sensor with no boundary rows — a
    production symbol is never invented from the probe map.
    """
    config_path = path or OKX_HISTORY_BOUNDARIES_FILE
    try:
        handle = open(config_path, encoding="utf-8", newline="")
    except OSError as exc:
        raise ValueError(
            f"OKX history-boundaries artifact missing at {config_path}: {exc}"
        ) from exc
    with handle:
        try:
            reader = csv.DictReader(handle)
            rows = list(reader)
        except csv.Error as exc:
            raise ValueError(
                f"malformed history-boundaries CSV {config_path}: {exc}"
            ) from exc

    required = {"provider_id", "sensor_family", "instrument"}
    scopes: dict[SensorFamily, list[str]] = {s: [] for s in _PROMOTED_ORDER}
    for row in rows:
        if not required.issubset(row):
            raise ValueError(
                f"history-boundaries CSV {config_path} missing required column "
                f"{sorted(required - set(row))}"
            )
        if row["provider_id"] != PROVIDER_ID:
            continue
        try:
            sensor = SensorFamily(row["sensor_family"])
        except ValueError:
            continue
        if sensor not in scopes:
            continue
        instrument = str(row["instrument"]).strip()
        if instrument and instrument not in scopes[sensor]:
            scopes[sensor].append(instrument)

    for sensor in _PROMOTED_ORDER:
        if not scopes[sensor]:
            raise ValueError(
                f"{PROVIDER_ID}/{sensor.value} has no instrument rows in "
                "08_HISTORY_BOUNDARIES.csv (fail closed: production symbol "
                "scope must come from evidence)"
            )
    return {s: tuple(v) for s, v in scopes.items()}


#: Evidence-backed per-sensor production symbol scopes (frozen once at import;
#: the artifact is a committed control file).
OKX_SYMBOL_SCOPES: dict[SensorFamily, tuple[str, ...]] = (
    okx_symbol_scopes_from_evidence()
)

#: PRODUCTION instrument union derived from evidence (configured production
#: scope — NOT live provider discovery).  Probe-only symbols never appear.
def _production_union() -> list[str]:
    union: list[str] = []
    for sensor in _PROMOTED_ORDER:
        for symbol in OKX_SYMBOL_SCOPES.get(sensor, ()):
            if symbol not in union:
                union.append(symbol)
    return union


OKX_PRODUCTION_INSTRUMENT_SCOPE: list[str] = _production_union()

#: Evidence-backed current snapshot request depth (probe.books sz=400).
OKX_BOOK_SNAPSHOT_SZ = 400

#: Evidence-backed default page for the funding/trade history paths
#: (live_probe_contracts.yaml query uses limit=100).
OKX_PAGE_LIMIT = 100


def okx_native_evidence(
    promotion_candidates: list[dict[str, object]] | None = None,
) -> dict[SensorFamily, ProviderNativeCapabilityEvidence]:
    """Build the exact native acquisition-mode evidence per promoted sensor.

    Only promoted sensors get a grant.  Funding and trade are HISTORICAL
    REST_CURSOR acquisitions; BOOK_SNAPSHOT is CURRENT_ONLY and gets NO
    historical grant (its `historical_mode` stays None — a CURRENT_ONLY surface
    cannot be given a historical/rest acquisition mode).

    Evidence ids are taken from each candidate's own `evidence_basis`, so every
    grant resolves to committed Bloc 2 evidence.  `instruments` (the production
    symbol scope the grant proves) comes from the committed
    08_HISTORY_BOUNDARIES.csv artifact — never from the Bloc 2 probe universe.
    """
    candidates = (
        promotion_candidates
        if promotion_candidates is not None
        else load_promotion_candidates()
    )
    evidence: dict[SensorFamily, ProviderNativeCapabilityEvidence] = {}
    for candidate in candidates:
        if candidate.get("provider") != PROVIDER_ID:
            continue
        sensor_name = candidate.get("sensor")
        try:
            sensor_family = SensorFamily(sensor_name)  # type: ignore[arg-type]
        except ValueError:
            continue
        if sensor_family not in OKX_PROMOTED_SENSORS:
            continue
        if sensor_family is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            # CURRENT_ONLY: no historical/rest native grant (never inferred).
            continue
        evidence_list = cast(list[object], candidate.get("evidence_basis", []))
        basis = [str(e) for e in evidence_list]
        pin = str(candidate.get("methodology_pin", ""))
        access = str(candidate.get("access_path", "PUBLIC_REST"))
        instruments = OKX_SYMBOL_SCOPES[sensor_family]

        if sensor_family is SensorFamily.MECHANICAL_FUNDING:
            evidence[sensor_family] = ProviderNativeCapabilityEvidence(
                provider_id=PROVIDER_ID,
                sensor_family=sensor_family,
                historical_mode=HistoricalMode.REST_CURSOR,
                pagination_mode=PaginationMode.CURSOR,
                endpoint_family=okx_endpoint_family(sensor_family),
                start_param="after",
                start_unit="epoch_milliseconds (fundingTime keyed)",
                end_param="before",
                end_unit="epoch_milliseconds (fundingTime keyed)",
                interval_param=None,
                interval_mechanics=(
                    "no interval param; funding records keyed by fundingTime"
                ),
                completion_rule="single evidence-backed request window (instId+limit)",
                resume_mechanic=(
                    "after/before cursor UNRESOLVED (direction not proven by "
                    "committed I13 evidence) -> constrained to a single "
                    "request window with determinism only"
                ),
                evidence_ids=tuple(basis),
                methodology_pin=pin,
                access_path=access,
                instruments=instruments,
            )
        else:  # MECHANICAL_TRADE
            evidence[sensor_family] = ProviderNativeCapabilityEvidence(
                provider_id=PROVIDER_ID,
                sensor_family=sensor_family,
                historical_mode=HistoricalMode.REST_CURSOR,
                pagination_mode=PaginationMode.CURSOR,
                endpoint_family=okx_endpoint_family(sensor_family),
                start_param="after",
                start_unit="trade-id based cursor (provider tradeId)",
                end_param="before",
                end_unit="trade-id based cursor (provider tradeId)",
                interval_param=None,
                interval_mechanics="raw event records; no bar interval",
                completion_rule="single evidence-backed request window (instId+limit)",
                resume_mechanic=(
                    "after/before cursor UNRESOLVED (direction not proven by "
                    "committed I13 evidence) -> constrained to a single "
                    "request window with determinism only"
                ),
                evidence_ids=tuple(basis),
                methodology_pin=pin,
                access_path=access,
                instruments=instruments,
            )
    return evidence


def build_okx_capabilities(
    promotion_candidates: list[dict[str, object]] | None = None,
) -> ProviderCapabilities:
    """Build the OKX production capability set from I14 + native refinement.

    Base capabilities come from `source_promotion_candidates.yaml` (strict);
    the exact native `historical_mode` / `pagination_mode` are applied ONLY
    through a valid NativeEvidence grant (never inferred).  The CURRENT_ONLY
    BOOK_SNAPSHOT keeps `historical_mode=None` (no historical grant).  The
    evidence-backed production symbol scope is applied to every promoted
    sensor.
    """
    candidates = (
        promotion_candidates
        if promotion_candidates is not None
        else load_promotion_candidates()
    )
    bases = capabilities_from_promotion(PROVIDER_ID, candidates)
    native = okx_native_evidence(candidates)

    refined_sensors: dict[SensorFamily, Any] = {}
    for sensor, cap in bases.sensors.items():
        if cap.supported and sensor in native:
            cap = apply_native_evidence(cap, native[sensor], provider_id=PROVIDER_ID)
        elif cap.supported:
            # No native historical grant (CURRENT_ONLY BOOK_SNAPSHOT): keep the
            # I14 CURRENT_ONLY surface and apply the evidence-derived symbol
            # scope directly (never broaden history/role).
            if OKX_SYMBOL_SCOPES.get(sensor):
                data = cap.model_dump()
                data["symbol_scope"] = list(OKX_SYMBOL_SCOPES[sensor])
                cap = type(cap).model_validate(data)
        refined_sensors[sensor] = cap

    return ProviderCapabilities(provider_id=PROVIDER_ID, sensors=refined_sensors)