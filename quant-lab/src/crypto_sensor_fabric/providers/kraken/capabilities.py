"""Kraken Futures — I14-bounded capability + native acquisition-mode freeze.

This is the SENSOR-B3-I05 capability/contract freeze (hardened in
SENSOR-B3-I05R1).  The Kraken package is bound strictly to the I14 promotion
set for KRAKEN_FUTURES (exactly six paths):

    MECHANICAL_BASIS, MECHANICAL_BOOK_METRIC, MECHANICAL_FUNDING,
    MECHANICAL_LIQUIDATION, MECHANICAL_OPEN_INTEREST, MECHANICAL_POSITIONING

MECHANICAL_TRADE and MECHANICAL_BOOK_SNAPSHOT are NOT promoted and remain typed
`CapabilityUnavailable` through the common protocol (Kraken `/history` trade and
old `/orderbook` snapshots are subject to current-surface/schema problems per
Bloc 2 evidence — I13R1 §3).

`kraken_native_evidence` derives the EXACT native acquisition mode per promoted
sensor from the committed Bloc 2 observation that Kraken Market Analytics uses:

    since/to in EPOCH SECONDS, `interval` in seconds, `result.more` -> re-issue
    `since` at the oldest bucket.

I05R1 boundary hardening separates the Bloc 2 PROBE universe from PRODUCTION
instrument support:

- `KRAKEN_PRODUCTION_INSTRUMENT_SCOPE` derives from the committed structured
  coverage artifact `evidence/bloc_02/08_HISTORY_BOUNDARIES.csv` (provider x
  sensor x instrument rows), never from the probe map.
- `KRAKEN_PROBE_INSTRUMENT_SCOPE` keeps the full Bloc 2 probe/control universe
  (incl. PI_SOLUSD / PI_DOGEUSD) available to characterization history WITHOUT
  exposing them as production support.
- Each promoted capability carries a sensor-specific `symbol_scope` proven by
  the grant's `instruments` (OI = PI_XBTUSD + PI_ETHUSD; the other five =
  PI_XBTUSD).

The native-mode grant is REQUIRED before the adapter may set a concrete
`historical_mode` (SENSOR-B3-I05 seam); it is grounded in the I14 evidence_basis
of each promotion candidate, so it can refine acquisition mechanics but never
broaden scope/role/PIT/methodology/access/live/archive.
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

PROVIDER_ID = "KRAKEN_FUTURES"

#: Structured per-instrument coverage artifact (I13R1 runtime evidence).  This
#: is the authoritative machine-readable provider x sensor x instrument map;
#: production symbol scope is derived from it, never hand-maintained.
KRAKEN_HISTORY_BOUNDARIES_FILE = (
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
#: support (SENSOR-B3-I05R1).
KRAKEN_PROBE_INSTRUMENT_SCOPE: list[str] = [
    "PI_XBTUSD",
    "PI_ETHUSD",
    "PI_SOLUSD",
    "PI_DOGEUSD",
]

#: Canonical promoted-sensor order used for stable production-scope ordering.
_PROMOTED_ORDER: tuple[SensorFamily, ...] = (
    SensorFamily.MECHANICAL_BASIS,
    SensorFamily.MECHANICAL_BOOK_METRIC,
    SensorFamily.MECHANICAL_FUNDING,
    SensorFamily.MECHANICAL_LIQUIDATION,
    SensorFamily.MECHANICAL_OPEN_INTEREST,
    SensorFamily.MECHANICAL_POSITIONING,
)

#: Promoted sensor -> Market Analytics `analytics_type`.
KRAKEN_ANALYTICS_TYPES: dict[SensorFamily, str] = {
    SensorFamily.MECHANICAL_OPEN_INTEREST: "open-interest",
    SensorFamily.MECHANICAL_FUNDING: "funding",
    SensorFamily.MECHANICAL_BASIS: "future-basis",
    SensorFamily.MECHANICAL_POSITIONING: "long-short-ratio",
    SensorFamily.MECHANICAL_BOOK_METRIC: "orderbook",
    SensorFamily.MECHANICAL_LIQUIDATION: "liquidation-volume",
}

#: The exact set of promoted Kraken production sensors (from I14).  Used for the
#: exact-set completeness test: declared production set == this set.
KRAKEN_PROMOTED_SENSORS: frozenset[SensorFamily] = frozenset(
    {
        SensorFamily.MECHANICAL_BASIS,
        SensorFamily.MECHANICAL_BOOK_METRIC,
        SensorFamily.MECHANICAL_FUNDING,
        SensorFamily.MECHANICAL_LIQUIDATION,
        SensorFamily.MECHANICAL_OPEN_INTEREST,
        SensorFamily.MECHANICAL_POSITIONING,
    }
)

#: Promoted sensors mapped to their Market Analytics endpoint family (fingerprint
#: / provenance identity), i.e. `kraken-market-analytics/{analytics_type}`.
def kraken_symbol_scopes_from_evidence(
    path: Path | None = None,
) -> dict[SensorFamily, tuple[str, ...]]:
    """Per-promoted-sensor PRODUCTION symbol scope from committed evidence.

    Reads `08_HISTORY_BOUNDARIES.csv` (I13R1 runtime artifact, provider x
    sensor x instrument rows) and returns the instrument list for each
    promoted Kraken sensor in file order (deduplicated).  Fails CLOSED on a
    missing/malformed artifact or a promoted sensor with no boundary rows — a
    production symbol is never invented from the probe map.
    """
    config_path = path or KRAKEN_HISTORY_BOUNDARIES_FILE
    try:
        handle = open(config_path, encoding="utf-8", newline="")
    except OSError as exc:
        raise ValueError(
            f"Kraken history-boundaries artifact missing at {config_path}: {exc}"
        ) from exc
    with handle:
        try:
            reader = csv.DictReader(handle)
            rows = list(reader)
        except csv.Error as exc:
            raise ValueError(f"malformed history-boundaries CSV {config_path}: {exc}") from exc

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
                f"08_HISTORY_BOUNDARIES.csv (fail closed: production symbol "
                "scope must come from evidence)"
            )
    return {s: tuple(v) for s, v in scopes.items()}


#: Evidence-backed per-sensor production symbol scopes (frozen once at import;
#: the artifact is a committed control file).
KRAKEN_SYMBOL_SCOPES: dict[SensorFamily, tuple[str, ...]] = (
    kraken_symbol_scopes_from_evidence()
)

#: PRODUCTION instrument union derived from evidence (configured production
#: scope — NOT live provider discovery).  Probe-only symbols never appear.
def _production_union() -> list[str]:
    union: list[str] = []
    for sensor in _PROMOTED_ORDER:
        for symbol in KRAKEN_SYMBOL_SCOPES.get(sensor, ()):
            if symbol not in union:
                union.append(symbol)
    return union


KRAKEN_PRODUCTION_INSTRUMENT_SCOPE: list[str] = _production_union()


def kraken_endpoint_family(sensor: SensorFamily) -> str:
    analytics_type = KRAKEN_ANALYTICS_TYPES[sensor]
    return f"kraken-market-analytics/{analytics_type}"


def kraken_native_evidence(
    promotion_candidates: list[dict[str, object]] | None = None,
) -> dict[SensorFamily, ProviderNativeCapabilityEvidence]:
    """Build the exact native acquisition-mode evidence per promoted sensor.

    Only promoted sensors get a grant (an unpromoted sensor could never resolve
    an evidence grant because it has no I14 evidence_basis).  Evidence ids are
    taken from each candidate's own `evidence_basis`, so every grant resolves to
    committed Bloc 2 evidence.  `instruments` (the production symbol scope the
    grant proves) comes from the committed 08_HISTORY_BOUNDARIES.csv artifact
    — never from the Bloc 2 probe universe.
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
        if sensor_family not in KRAKEN_PROMOTED_SENSORS:
            continue
        evidence_list = cast(list[object], candidate.get("evidence_basis", []))
        basis = [str(e) for e in evidence_list]
        pin = str(candidate.get("methodology_pin", ""))
        access = str(candidate.get("access_path", "PUBLIC_REST"))
        evidence[sensor_family] = ProviderNativeCapabilityEvidence(
            provider_id=PROVIDER_ID,
            sensor_family=sensor_family,
            historical_mode=HistoricalMode.REST_RANGE,
            pagination_mode=PaginationMode.TIME_RANGE,
            endpoint_family=kraken_endpoint_family(sensor_family),
            start_param="since",
            start_unit="epoch_seconds",
            end_param="to",
            end_unit="epoch_seconds",
            interval_param="interval",
            interval_mechanics=(
                "seconds; supported {60,300,900,1800,3600,14400,43200,86400,604800}"
            ),
            completion_rule="result.more == false -> complete",
            resume_mechanic="result.more true -> re-issue since at oldest bucket",
            evidence_ids=tuple(basis),
            methodology_pin=pin,
            access_path=access,
            instruments=KRAKEN_SYMBOL_SCOPES[sensor_family],
        )
    return evidence


def build_kraken_capabilities(
    promotion_candidates: list[dict[str, object]] | None = None,
) -> ProviderCapabilities:
    """Build the Kraken production capability set from I14 + native refinement.

    Base capabilities come from `source_promotion_candidates.yaml` (strict); the
    exact native `historical_mode` / `pagination_mode` are applied ONLY through a
    valid NativeEvidence grant (never inferred).
    """
    candidates = (
        promotion_candidates
        if promotion_candidates is not None
        else load_promotion_candidates()
    )
    bases = capabilities_from_promotion(PROVIDER_ID, candidates)
    native = kraken_native_evidence(candidates)

    refined_sensors: dict[SensorFamily, Any] = {}
    for sensor, cap in bases.sensors.items():
        if cap.supported and sensor in native:
            cap = apply_native_evidence(cap, native[sensor], provider_id=PROVIDER_ID)
        refined_sensors[sensor] = cap

    return ProviderCapabilities(provider_id=PROVIDER_ID, sensors=refined_sensors)