"""I14 evidence integration (SENSOR-B3-I04).

The common capability layer references I14 evidence through
`source_promotion_candidates.yaml` — the ONLY input list Bloc 3 adapter work
may consume.  This module builds `ProviderCapabilities` from that file and
binds every declared capability to the authoritative I14 fields:

    allowed_role / history_mode / verified_history / redundancy_class /
    PIT_requirement / methodology_pin / known_hazards / evidence_basis

A capability may NEVER be upgraded beyond these bounds during Bloc 3:

- CURRENT_ONLY stays CURRENT_ONLY (no historical surface)
- ARCHIVE_ONLY is not production REST
- MECHANISM_MICROSCOPE is not interval aggregate truth
- PIT_READY_WITH_METHOD_VERSION keeps its methodology pin
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

from ..._paths import QUANT_LAB_ROOT
from ...contracts.enums import SensorFamily
from ...probes.enums import PITReadiness, ProviderRole, RedundancyClass
from .enums import AdapterAuthMode, FreeOnlyStatus, HistoricalMode, LiveMode
from .models import AdapterEvidenceRef, ProviderCapabilities, SensorCapability

DEFAULT_PROMOTION_FILE = (
    QUANT_LAB_ROOT
    / "research"
    / "crypto_foundry"
    / "sensor_fabric"
    / "evidence"
    / "bloc_02"
    / "source_promotion_candidates.yaml"
)

#: history_mode string -> base historical surface.  Unknown modes fail closed.
_HISTORY_MODE_SURFACE: dict[str, HistoricalMode] = {
    "HISTORICAL": HistoricalMode.REST_RANGE,
    "CURRENT_ONLY": HistoricalMode.LIVE_REST_ONLY,
    "ARCHIVE_ONLY": HistoricalMode.PUBLIC_OBJECT_STORAGE,
    "THIRD_PARTY_ARCHIVE": HistoricalMode.THIRD_PARTY_ARCHIVE,
}

#: access_path string -> auth mode (best-effort; overridable).
_ACCESS_PATH_AUTH: dict[str, AdapterAuthMode] = {
    "PUBLIC_REST": AdapterAuthMode.NO_AUTH,
    "FREE_API_KEY": AdapterAuthMode.FREE_API_KEY,
    "PUBLIC_ARCHIVE": AdapterAuthMode.NO_AUTH,
    "COMMUNITY_ARCHIVE": AdapterAuthMode.NO_AUTH,
}


def _parse_datetime_utc(value: str) -> datetime:
    """Parse an ISO timestamp that may be date-only (Z = UTC).

    `datetime.fromisoformat` silently drops the timezone on date-only
    strings (e.g. ``2024-06-15+00:00``), which would poison UTC ordering
    invariants; append a midnight time component when none is present.
    """
    text = str(value).strip().replace("Z", "+00:00")
    if "T" not in text and " " not in text:
        # date-only form with a trailing offset: insert a midnight time
        # component before the offset (fromisoformat would otherwise drop
        # the timezone on date-only strings, poisoning UTC ordering).
        if text.endswith("+00:00"):
            text = f"{text[:-6]}T00:00:00+00:00"
        else:
            text = f"{text}T00:00:00"
    return datetime.fromisoformat(text)


def _parse_verified_range(value: str | None) -> tuple[datetime | None, datetime | None]:
    """Parse the ``verified_history`` range ``"START..END"`` (Z = UTC)."""
    if not value:
        return None, None
    parts = str(value).split("..")
    try:
        start = _parse_datetime_utc(parts[0])
        end = _parse_datetime_utc(parts[1])
    except (ValueError, IndexError):
        return None, None
    return start, end


def load_promotion_candidates(
    path: Path | None = None,
) -> list[dict[str, object]]:
    """Load the I14 promotion-candidate list (the ONLY Bloc 3 input list)."""
    config_path = path or DEFAULT_PROMOTION_FILE
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    candidates = data.get("candidates", [])
    if not isinstance(candidates, list) or not candidates:
        raise ValueError(
            f"promotion candidates {config_path} has no candidates list"
        )
    return [c for c in candidates if isinstance(c, dict)]


def capabilities_from_promotion(
    provider_id: str,
    candidates: list[dict[str, object]] | None = None,
    *,
    auth_mode_override: AdapterAuthMode | None = None,
) -> ProviderCapabilities:
    """Build `ProviderCapabilities` for one provider from I14 candidates.

    Every declared capability is bound by the I14 fields.  A candidate that
    cannot be mapped fails closed (raises) — it is never silently widened.
    """
    if candidates is None:
        candidates = load_promotion_candidates()

    sensors: dict[SensorFamily, SensorCapability] = {}
    for candidate in candidates:
        if candidate.get("provider") != provider_id:
            continue
        sensor_name = str(candidate.get("sensor", ""))
        try:
            sensor_family = SensorFamily(sensor_name)
        except ValueError:
            raise ValueError(
                f"{provider_id} promotion candidate has unknown sensor {sensor_name!r}"
            ) from None

        history_mode = str(candidate.get("history_mode", ""))
        surface = _HISTORY_MODE_SURFACE.get(history_mode)
        if surface is None:
            raise ValueError(
                f"{provider_id}/{sensor_family.value} has unmapped history_mode "
                f"{history_mode!r} (fail closed)"
            )

        role_raw = str(candidate.get("allowed_role", ""))
        role = (
            ProviderRole(role_raw)
            if role_raw and role_raw in {r.value for r in ProviderRole}
            else None
        )
        redundancy_raw = str(candidate.get("redundancy_class", ""))
        redundancy = (
            RedundancyClass(redundancy_raw)
            if redundancy_raw and redundancy_raw in {r.value for r in RedundancyClass}
            else None
        )
        pit_raw = str(candidate.get("PIT_requirement", ""))
        pit = (
            PITReadiness(pit_raw)
            if pit_raw and pit_raw in {p.value for p in PITReadiness}
            else None
        )

        verified_start, verified_end = _parse_verified_range(
            str(candidate.get("verified_history", "") or "")
        )
        evidence_basis = [
            str(e) for e in candidate.get("evidence_basis", []) if isinstance(e, str)
        ]
        hazards = [
            str(h) for h in candidate.get("known_hazards", []) if isinstance(h, str)
        ]

        access_path = str(candidate.get("access_path", ""))
        auth = (
            auth_mode_override
            or _ACCESS_PATH_AUTH.get(access_path, AdapterAuthMode.UNVERIFIED)
        )

        evidence_ref = (
            AdapterEvidenceRef(
                evidence_id=evidence_basis[0],
                provider_id=provider_id,
                sensor_family=sensor_family,
            )
            if evidence_basis
            else None
        )

        sensors[sensor_family] = SensorCapability(
            sensor_family=sensor_family,
            supported=True,
            access_mode=access_path,
            historical_mode=surface,
            live_mode=(
                LiveMode.LIVE_REST
                if history_mode == "HISTORICAL"
                else LiveMode.NONE
            ),
            auth_requirement=auth,
            free_access_status=FreeOnlyStatus.FREE_COMPLIANT,
            verified_history_start=verified_start,
            verified_history_end=verified_end,
            verified_at=verified_end,
            probe_evidence_ref=evidence_ref,
            allowed_role=role,
            redundancy_class=redundancy,
            pit_requirement=pit,
            methodology_pin=str(candidate.get("methodology_pin", "") or None) or None,
            known_hazards=hazards,
            evidence_basis=evidence_basis,
        )

    return ProviderCapabilities(provider_id=provider_id, sensors=sensors)


def promotion_provider_ids(candidates: list[dict[str, object]]) -> list[str]:
    """Distinct promoted provider ids, in file order."""
    seen: list[str] = []
    for candidate in candidates:
        provider = str(candidate.get("provider", ""))
        if provider and provider not in seen:
            seen.append(provider)
    return seen
