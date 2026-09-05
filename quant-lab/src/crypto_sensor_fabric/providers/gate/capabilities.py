"""Gate Futures — I14-bounded capability + native acquisition-mode freeze.

This is the SENSOR-B3-I06 capability/contract freeze.  The Gate package is
bound strictly to the I14 promotion set for GATE_FUTURES (exactly four paths):

    MECHANICAL_FUNDING, MECHANICAL_LIQUIDATION, MECHANICAL_OPEN_INTEREST,
    MECHANICAL_POSITIONING

All four are SECONDARY providers over the PUBLIC v4 REST surface
(`api.gateio.ws/api/v4/futures/usdt`).  MECHANICAL_TRADE and
MECHANICAL_BOOK_SNAPSHOT are NOT promoted and remain typed
`CapabilityUnavailable` through the common protocol.

Structure of the acquisition surfaces (Bloc 2 I13 / I13R1 runtime evidence):

- MECHANICAL_OPEN_INTEREST / MECHANICAL_LIQUIDATION / MECHANICAL_POSITIONING
  come from the PUBLIC single `GET /api/v4/futures/usdt/contract_stats`
  surface.  The same physical provider payload carries fields relevant to all
  three, but Bloc 3 keeps each as a SEPARATE sensor contract — no synthetic
  cross-sensor state, no combined OI/liquidation/positioning feature.
- MECHANICAL_FUNDING comes from the single-contract public
  `GET /api/v4/futures/usdt/funding_rate` (rows `{r, t}`, from/to in epoch
  seconds).  The plural batch `POST /funding_rates` route is NOT a production
  path (its earlier probe result was adjudicated REQUEST_CONTRACT_INVALID, not
  a provider auth requirement).

I05R1-style boundary hardening separates the Bloc 2 PROBE universe
(`NATIVE_INSTRUMENTS`: BTC_USDT / ETH_USDT / SOL_USDT / DOGE_USDT) from
PRODUCTION instrument support.  The structured coverage artifact
`evidence/bloc_02/08_HISTORY_BOUNDARIES.csv` evidences BTC_USDT for all four
promoted Gate paths; only those are granted production symbol scope.  ETH /
SOL / DOGE stay probe/control instruments.

The native-mode grant is REQUIRED before the adapter may set a concrete
`historical_mode` (SENSOR-B3-I05 seam), and it is grounded in each promotion
candidate's own I14 `evidence_basis`.
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

PROVIDER_ID = "GATE_FUTURES"

#: Structured per-instrument coverage artifact (I13R1 runtime evidence).  This
#: is the authoritative machine-readable provider x sensor x instrument map;
#: production symbol scope is derived from it, never hand-maintained.
GATE_HISTORY_BOUNDARIES_FILE = (
    QUANT_LAB_ROOT
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_02"
    / "08_HISTORY_BOUNDARIES.csv"
)

#: Full Bloc 2 probe/control universe (probe.NATIVE_INSTRUMENTS: BTC/ETH/SOL/
#: MID_TAIL_CONTROL).  Kept intact for characterization history; NOT production
#: support (I05R1 boundary, applied here for Gate).
GATE_PROBE_INSTRUMENT_SCOPE: list[str] = [
    "BTC_USDT",
    "ETH_USDT",
    "SOL_USDT",
    "DOGE_USDT",
]

#: Canonical promoted-sensor order used for stable production-scope ordering.
_PROMOTED_ORDER: tuple[SensorFamily, ...] = (
    SensorFamily.MECHANICAL_FUNDING,
    SensorFamily.MECHANICAL_LIQUIDATION,
    SensorFamily.MECHANICAL_OPEN_INTEREST,
    SensorFamily.MECHANICAL_POSITIONING,
)

#: The exact set of promoted Gate production sensors (from I14).  Used for the
#: exact-set completeness test: declared production set == this set.
GATE_PROMOTED_SENSORS: frozenset[SensorFamily] = frozenset(_PROMOTED_ORDER)

#: Endpoint family supported by the public v4 USD-settled futures surface.
GATE_USDT_BASE = "api.gateio.ws/api/v4/futures/usdt"
GATE_CONTRACT_STATS_PATH = "/contract_stats"
GATE_FUNDING_RATE_PATH = "/funding_rate"


def gate_endpoint_family(sensor: SensorFamily) -> str:
    """Endpoint/provenance family for a promoted Gate sensor (no private path)."""
    if sensor is SensorFamily.MECHANICAL_FUNDING:
        return "gate-futures-funding_rate"
    # OI / LIQUIDATION / POSITIONING all ride the PUBLIC contract_stats surface.
    return "gate-futures-contract_stats"


def gate_symbol_scopes_from_evidence(
    path: Path | None = None,
) -> dict[SensorFamily, tuple[str, ...]]:
    """Per-promoted-sensor PRODUCTION symbol scope from committed evidence.

    Reads `08_HISTORY_BOUNDARIES.csv` (I13R1 runtime artifact, provider x
    sensor x instrument rows) and returns the instrument list for each
    promoted Gate sensor in file order (deduplicated).  Fails CLOSED on a
    missing/malformed artifact or a promoted sensor with no boundary rows — a
    production symbol is never invented from the probe map.
    """
    config_path = path or GATE_HISTORY_BOUNDARIES_FILE
    try:
        handle = open(config_path, encoding="utf-8", newline="")
    except OSError as exc:
        raise ValueError(
            f"Gate history-boundaries artifact missing at {config_path}: {exc}"
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
GATE_SYMBOL_SCOPES: dict[SensorFamily, tuple[str, ...]] = (
    gate_symbol_scopes_from_evidence()
)


def _production_union() -> list[str]:
    """PRODUCTION instrument union from evidence (configured scope, NOT discovery)."""
    union: list[str] = []
    for sensor in _PROMOTED_ORDER:
        for symbol in GATE_SYMBOL_SCOPES.get(sensor, ()):
            if symbol not in union:
                union.append(symbol)
    return union


GATE_PRODUCTION_INSTRUMENT_SCOPE: list[str] = _production_union()


def gate_native_evidence(
    promotion_candidates: list[dict[str, object]] | None = None,
) -> dict[SensorFamily, ProviderNativeCapabilityEvidence]:
    """Build the exact native acquisition-mode evidence per promoted sensor.

    Only promoted sensors get a grant (an unpromoted sensor could never resolve
    an evidence grant because it has no I14 evidence_basis).  Evidence ids are
    taken from each candidate's own `evidence_basis`, so every grant resolves
    to committed Bloc 2 evidence.  `instruments` (the production symbol scope
    the grant proves) comes from the committed 08_HISTORY_BOUNDARIES.csv
    artifact — never from the Bloc 2 probe universe.
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
        if sensor_family not in GATE_PROMOTED_SENSORS:
            continue
        evidence_list = cast(list[object], candidate.get("evidence_basis", []))
        basis = [str(e) for e in evidence_list]
        pin = str(candidate.get("methodology_pin", ""))
        access = str(candidate.get("access_path", "PUBLIC_REST"))
        instruments = GATE_SYMBOL_SCOPES[sensor_family]

        if sensor_family is SensorFamily.MECHANICAL_FUNDING:
            # GET /funding_rate?contract=..&from=&to= (epoch seconds); rows
            # {r, t}; no interval param (event/effective records, not bars).
            evidence[sensor_family] = ProviderNativeCapabilityEvidence(
                provider_id=PROVIDER_ID,
                sensor_family=sensor_family,
                historical_mode=HistoricalMode.REST_RANGE,
                pagination_mode=PaginationMode.TIME_RANGE,
                endpoint_family=gate_endpoint_family(sensor_family),
                start_param="from",
                start_unit="epoch_seconds",
                end_param="to",
                end_unit="epoch_seconds",
                interval_param=None,
                interval_mechanics=None,
                completion_rule="from/to bounded single-request window",
                resume_mechanic=None,
                evidence_ids=tuple(basis),
                methodology_pin=pin,
                access_path=access,
                instruments=instruments,
            )
        else:
            # OI / LIQUIDATION / POSITIONING: shared PUBLIC /contract_stats.
            # from=epoch SECONDS, interval=provider STRING bucket ("1h"), limit;
            # NO `to` is invented.  Traversal is from/interval/limit bounded.
            evidence[sensor_family] = ProviderNativeCapabilityEvidence(
                provider_id=PROVIDER_ID,
                sensor_family=sensor_family,
                historical_mode=HistoricalMode.REST_RANGE,
                pagination_mode=PaginationMode.TIME_RANGE,
                endpoint_family=gate_endpoint_family(sensor_family),
                start_param="from",
                start_unit="epoch_seconds",
                end_param="none",
                end_unit="n/a (no `to`; from/interval/limit bounded window)",
                interval_param="interval",
                interval_mechanics="provider STRING bucket; evidence: 1h (G1H -> '1h')",
                completion_rule="single bounded request window (from/interval/limit)",
                resume_mechanic=(
                    "unresolved; single-request window (no invented from+interval "
                    "advancement)"
                ),
                evidence_ids=tuple(basis),
                methodology_pin=pin,
                access_path=access,
                instruments=instruments,
            )
    return evidence


def build_gate_capabilities(
    promotion_candidates: list[dict[str, object]] | None = None,
) -> ProviderCapabilities:
    """Build the Gate production capability set from I14 + native refinement.

    Base capabilities come from `source_promotion_candidates.yaml` (strict); the
    exact native `historical_mode` / `pagination_mode` are applied ONLY through
    a valid NativeEvidence grant (never inferred).
    """
    candidates = (
        promotion_candidates
        if promotion_candidates is not None
        else load_promotion_candidates()
    )
    bases = capabilities_from_promotion(PROVIDER_ID, candidates)
    native = gate_native_evidence(candidates)

    refined_sensors: dict[SensorFamily, Any] = {}
    for sensor, cap in bases.sensors.items():
        if cap.supported and sensor in native:
            cap = apply_native_evidence(cap, native[sensor], provider_id=PROVIDER_ID)
        refined_sensors[sensor] = cap

    return ProviderCapabilities(provider_id=PROVIDER_ID, sensors=refined_sensors)