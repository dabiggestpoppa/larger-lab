"""Deribit — I14-bounded capability + native acquisition-mode freeze.

This is the SENSOR-B3-I08 capability/contract freeze.  The Deribit package is
bound strictly to the I14 promotion set for DERIBIT (EXACTLY FOUR paths):

    MECHANICAL_BOOK_SNAPSHOT  (CURRENT_ONLY)
    MECHANICAL_FUNDING        (SECONDARY, HISTORICAL)
    MECHANICAL_LIQUIDATION    (MECHANISM_MICROSCOPE, HISTORICAL)
    MECHANICAL_TRADE          (MECHANISM_MICROSCOPE, HISTORICAL)

The promoted production instrument is BTC-PERPETUAL for all four paths (from
the committed 08_HISTORY_BOUNDARIES.csv per-instrument evidence).  Everything
else that Deribit may offer is typed `CapabilityUnavailable` under the CURRENT
I14 freeze:

    MECHANICAL_BASIS, MECHANICAL_BOOK_METRIC, MECHANICAL_OPEN_INTEREST,
    MECHANICAL_POSITIONING

I05R1-style boundary hardening separates the Bloc 2 PROBE universe (probe
`NATIVE_INSTRUMENTS`: BTC/ETH/SOL-PERPETUAL) from PRODUCTION instrument
support.  Production symbol scope is derived ONLY from the committed
structured coverage artifact `08_HISTORY_BOUNDARIES.csv` (provider x sensor x
instrument rows), never from the probe map.  MID_TAIL_CONTROL is deliberately
NOT mapped (probe §10.7 narrower universe).

SEMANTIC HAZARD (mechanism microscope): Deribit trade/liquidation is
TRADE-LEVEL EXECUTION / LIQUIDATION ANATOMY.  The liquidation sensor is NOT a
second numerical copy of the trade stream and is NEVER numerically merged with
interval liquidation totals (T2-SEM-06).  The same physical
`get_last_trades_by_instrument` endpoint supports two sensor views — the raw
payload is preserved BEFORE any sensor-specific projection.

Native acquisition surface (grounded in committed Bloc 2 evidence,
live_probe_contracts.yaml + probe.py):

- MECHANICAL_TRADE + MECHANICAL_LIQUIDATION:
  GET `/api/v2/public/get_last_trades_by_instrument` with
  `instrument_name`, `start_timestamp`, `end_timestamp` (epoch ms),
  `count` (<= 1000), `include_old=true` (REQUIRED for historical depth).
  Result envelope carries `has_more`; rows live under `result.trades`.
  Continuation beyond the evidenced single window is NOT proven by committed
  I13 evidence, so production constrains acquisition to a single
  evidence-backed request window with truthful completion semantics.
- MECHANICAL_FUNDING:
  GET `/api/v2/public/get_funding_rate_history` with `instrument_name`,
  `start_timestamp`, `end_timestamp` (epoch ms), `count` (<= 1000).
  Observed LIVE: `result` is a RAW LIST (NOT `{data:[...]}`) — frozen here.
- MECHANICAL_BOOK_SNAPSHOT:
  GET `/api/v2/public/get_order_book` with `instrument_name`, `depth=25`.
  CURRENT snapshot only — no start/end/cursor/historical replay.

Timestamps are provider-native epoch MILLISECOND INTEGERS (strict `type(x) is
int`, bool rejected).

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

PROVIDER_ID = "DERIBIT"

#: Structured per-instrument coverage artifact (I13R1 runtime evidence).  This
#: is the authoritative machine-readable provider x sensor x instrument map;
#: production symbol scope is derived from it, never hand-maintained.
DERIBIT_HISTORY_BOUNDARIES_FILE = (
    QUANT_LAB_ROOT
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_02"
    / "08_HISTORY_BOUNDARIES.csv"
)

#: Full Bloc 2 probe/control universe (probe.NATIVE_INSTRUMENTS: BTC/ETH/SOL;
#: MID_TAIL_CONTROL deliberately NOT mapped).  Kept intact for characterization
#: history; NOT production support (I05R1 boundary, applied here for Deribit).
DERIBIT_PROBE_INSTRUMENT_SCOPE: list[str] = [
    "BTC-PERPETUAL",
    "ETH-PERPETUAL",
    "SOL-PERPETUAL",
]

#: Canonical promoted-sensor order used for stable production-scope ordering.
_PROMOTED_ORDER: tuple[SensorFamily, ...] = (
    SensorFamily.MECHANICAL_BOOK_SNAPSHOT,
    SensorFamily.MECHANICAL_FUNDING,
    SensorFamily.MECHANICAL_LIQUIDATION,
    SensorFamily.MECHANICAL_TRADE,
)

#: The exact set of promoted Deribit production sensors (from I14).  Used for
#: the exact-set completeness test: declared production set == this set.
DERIBIT_PROMOTED_SENSORS: frozenset[SensorFamily] = frozenset(_PROMOTED_ORDER)

#: Endpoint families for fingerprint / provenance identity.
DERIBIT_LAST_TRADES_PATH = "/api/v2/public/get_last_trades_by_instrument"
DERIBIT_FUNDING_RATE_HISTORY_PATH = "/api/v2/public/get_funding_rate_history"
DERIBIT_ORDER_BOOK_PATH = "/api/v2/public/get_order_book"
DERIBIT_REST_BASE = "www.deribit.com"


def deribit_endpoint_family(sensor: SensorFamily) -> str:
    """Endpoint/provenance family for a promoted Deribit sensor."""
    if sensor in (
        SensorFamily.MECHANICAL_TRADE,
        SensorFamily.MECHANICAL_LIQUIDATION,
    ):
        # ONE physical surface, TWO logical sensor views (never a combined
        # state): trade events vs forced-liquidation events.
        return "deribit-get-last-trades-by-instrument"
    if sensor is SensorFamily.MECHANICAL_FUNDING:
        return "deribit-get-funding-rate-history"
    # BOOK_SNAPSHOT (the only remaining promoted path)
    return "deribit-get-order-book"


def deribit_symbol_scopes_from_evidence(
    path: Path | None = None,
) -> dict[SensorFamily, tuple[str, ...]]:
    """Per-promoted-sensor PRODUCTION symbol scope from committed evidence.

    Reads `08_HISTORY_BOUNDARIES.csv` (I13R1 runtime artifact, provider x
    sensor x instrument rows) and returns the instrument list for each
    promoted Deribit sensor in file order (deduplicated).  Fails CLOSED on a
    missing/malformed artifact or a promoted sensor with no boundary rows — a
    production symbol is never invented from the probe map.
    """
    config_path = path or DERIBIT_HISTORY_BOUNDARIES_FILE
    try:
        handle = open(config_path, encoding="utf-8", newline="")
    except OSError as exc:
        raise ValueError(
            f"Deribit history-boundaries artifact missing at {config_path}: {exc}"
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
DERIBIT_SYMBOL_SCOPES: dict[SensorFamily, tuple[str, ...]] = (
    deribit_symbol_scopes_from_evidence()
)

#: PRODUCTION instrument union derived from evidence (configured production
#: scope — NOT live provider discovery).  Probe-only symbols never appear.
def _production_union() -> list[str]:
    union: list[str] = []
    for sensor in _PROMOTED_ORDER:
        for symbol in DERIBIT_SYMBOL_SCOPES.get(sensor, ()):
            if symbol not in union:
                union.append(symbol)
    return union


DERIBIT_PRODUCTION_INSTRUMENT_SCOPE: list[str] = _production_union()

#: Evidence-backed current snapshot request depth (probe.books depth=25).
DERIBIT_BOOK_DEPTH = 25

#: Evidence-backed page cap for the trades/liquidation + funding history
#: surfaces (live_probe_contracts.yaml count bound <= 1000).
DERIBIT_PAGE_LIMIT = 1000


def deribit_native_evidence(
    promotion_candidates: list[dict[str, object]] | None = None,
) -> dict[SensorFamily, ProviderNativeCapabilityEvidence]:
    """Build the exact native acquisition-mode evidence per promoted sensor.

    Only promoted sensors get a grant.  Trade, liquidation and funding are
    HISTORICAL window acquisitions; BOOK_SNAPSHOT is CURRENT_ONLY and gets NO
    historical grant (its `historical_mode` stays None — a CURRENT_ONLY surface
    cannot be given a historical/rest acquisition mode).

    Evidence ids are taken from each candidate's own `evidence_basis`, so every
    grant resolves to committed Bloc 2 evidence.  `instruments` (the production
    symbol scope the grant proves) comes from the committed
    08_HISTORY_BOUNDARIES.csv artifact — never from the Bloc 2 probe universe.

    `start_timestamp` / `end_timestamp` are epoch MILLISECONDS (request unit).
    Trade/liquidation rows `timestamp` are epoch MILLISECONDS (response unit);
    the same unit happens to apply to request and response for Deribit (unlike
    Gate contract_stats), but the units are still declared explicitly.
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
        if sensor_family not in DERIBIT_PROMOTED_SENSORS:
            continue
        if sensor_family is SensorFamily.MECHANICAL_BOOK_SNAPSHOT:
            # CURRENT_ONLY: no historical/rest native grant (never inferred).
            continue
        evidence_list = cast(list[object], candidate.get("evidence_basis", []))
        basis = [str(e) for e in evidence_list]
        pin = str(candidate.get("methodology_pin", ""))
        access = str(candidate.get("access_path", "PUBLIC_REST"))
        instruments = DERIBIT_SYMBOL_SCOPES[sensor_family]

        if sensor_family is SensorFamily.MECHANICAL_FUNDING:
            evidence[sensor_family] = ProviderNativeCapabilityEvidence(
                provider_id=PROVIDER_ID,
                sensor_family=sensor_family,
                historical_mode=HistoricalMode.REST_RANGE,
                pagination_mode=PaginationMode.TIME_RANGE,
                endpoint_family=deribit_endpoint_family(sensor_family),
                start_param="start_timestamp",
                start_unit="epoch_milliseconds (request unit)",
                end_param="end_timestamp",
                end_unit="epoch_milliseconds (request unit)",
                interval_param=None,
                interval_mechanics=(
                    "hourly funding records (1h/8h series preserved natively); "
                    "no bar-resampling interval param"
                ),
                completion_rule=(
                    "explicit start/end window + count<=1000; completeness "
                    "only when committed evidence proves the request "
                    "exhaustively satisfies the window (single window today)"
                ),
                resume_mechanic=(
                    "window bounded; deterministic continuation beyond the "
                    "evidenced single window NOT proven -> constrained to one "
                    "request window with truthful completion semantics"
                ),
                evidence_ids=tuple(basis),
                methodology_pin=pin,
                access_path=access,
                instruments=instruments,
            )
        else:  # MECHANICAL_TRADE / MECHANICAL_LIQUIDATION
            evidence[sensor_family] = ProviderNativeCapabilityEvidence(
                provider_id=PROVIDER_ID,
                sensor_family=sensor_family,
                historical_mode=HistoricalMode.REST_RANGE,
                pagination_mode=PaginationMode.TIME_RANGE,
                endpoint_family=deribit_endpoint_family(sensor_family),
                start_param="start_timestamp",
                start_unit="epoch_milliseconds (request unit)",
                end_param="end_timestamp",
                end_unit="epoch_milliseconds (request unit)",
                interval_param=None,
                interval_mechanics="raw trade-level events; no bar interval",
                completion_rule=(
                    "explicit start/end window + count<=1000 + has_more flag; "
                    "completeness only when committed evidence proves the "
                    "returned page satisfies the window (single window today)"
                ),
                resume_mechanic=(
                    "has_more flag present but continuation mechanics beyond "
                    "the evidenced single window NOT proven -> constrained to "
                    "one request window with truthful completion semantics"
                ),
                evidence_ids=tuple(basis),
                methodology_pin=pin,
                access_path=access,
                instruments=instruments,
            )
    return evidence


def build_deribit_capabilities(
    promotion_candidates: list[dict[str, object]] | None = None,
) -> ProviderCapabilities:
    """Build the Deribit production capability set from I14 + native refinement.

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
    native = deribit_native_evidence(candidates)

    refined_sensors: dict[SensorFamily, Any] = {}
    for sensor, cap in bases.sensors.items():
        if cap.supported and sensor in native:
            cap = apply_native_evidence(cap, native[sensor], provider_id=PROVIDER_ID)
        elif cap.supported:
            # No native historical grant (CURRENT_ONLY BOOK_SNAPSHOT): keep the
            # I14 CURRENT_ONLY surface and apply the evidence-derived symbol
            # scope directly (never broaden history/role).
            if DERIBIT_SYMBOL_SCOPES.get(sensor):
                data = cap.model_dump()
                data["symbol_scope"] = list(DERIBIT_SYMBOL_SCOPES[sensor])
                cap = type(cap).model_validate(data)
        refined_sensors[sensor] = cap

    return ProviderCapabilities(provider_id=PROVIDER_ID, sensors=refined_sensors)
