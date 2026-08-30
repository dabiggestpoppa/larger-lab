"""Kraken Futures — I14-bounded capability + native acquisition-mode freeze.

This is the SENSOR-B3-I05 capability/contract freeze.  The Kraken package is
bound strictly to the I14 promotion set for KRAKEN_FUTURES (exactly six paths):

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

This native-mode grant is REQUIRED before the adapter may set a concrete
`historical_mode` (SENSOR-B3-I05 seam); it is grounded in the I14 evidence_basis
of each promotion candidate, so it can refine acquisition mechanics but never
broaden scope/role/PIT/methodology/access/live/archive.
"""

from __future__ import annotations

from typing import Any, cast

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

#: Configured native instrument scope (Bloc 2 probe map, NOT endpoint discovery).
#: OI is evidence-backed for both PI_XBTUSD and PI_ETHUSD; the other promoted
#: sensors are evidence-backed on PI_XBTUSD.  This is a configured scope, not an
#: invented instrument-discovery endpoint (I05 does not fabricate discovery).
KRAKEN_INSTRUMENT_SCOPE: list[str] = [
    "PI_XBTUSD",
    "PI_ETHUSD",
    "PI_SOLUSD",
    "PI_DOGEUSD",
]

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
    committed Bloc 2 evidence.
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