"""I14 evidence integration (SENSOR-B3-I04 / I04R1).

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

Parsing is STRICT (I04R1 Repair 4): an unknown or missing controlled value
that a promoted capability requires FAILS CLOSED with a ValueError rather
than being silently defaulted to None.  Only fields the frozen contract
permits to be NULL (e.g. an empty known_hazards list) stay NULL.

Live vs historical separation (I04R1 Repair 3):

- a HISTORICAL-public-REST record sets `historical_mode` to its historical
  surface and leaves `live_mode = NONE` (historical evidence does NOT
  auto-grant a live-production contract);
- a CURRENT_ONLY-public-REST record sets `live_mode = LIVE_REST` and leaves
  `historical_mode = None` (current snapshot surface, no invented history);
- an ARCHIVE_ONLY / THIRD_PARTY_ARCHIVE record is historical-only and never
  implies REST or live capability.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from ..._paths import QUANT_LAB_ROOT
from ...contracts.enums import SensorFamily
from ...probes.enums import PITReadiness, ProviderRole, RedundancyClass
from .enums import (
    ALLOWED_AUTH_MODES,
    AdapterAuthMode,
    FreeOnlyStatus,
    HistoricalMode,
    LiveMode,
)
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
    "ARCHIVE_ONLY": HistoricalMode.PUBLIC_OBJECT_STORAGE,
    "THIRD_PARTY_ARCHIVE": HistoricalMode.THIRD_PARTY_ARCHIVE,
}

#: CURRENT_ONLY public surfaces are current/live acquisition paths.
_CURRENT_ONLY_SURFACES: dict[str, HistoricalMode] = {
    "CURRENT_ONLY": HistoricalMode.LIVE_REST_ONLY,
}

#: access_path string -> auth mode.  Unknown access paths cannot prove free
#: access and FAIL CLOSED unless an explicit auth override is supplied.
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
        if text.endswith("+00:00"):
            text = f"{text[:-6]}T00:00:00+00:00"
        else:
            text = f"{text}T00:00:00"
    return datetime.fromisoformat(text)


def _parse_verified_range(value: str | None) -> tuple[datetime | None, datetime | None]:
    """Parse the ``verified_history`` range ``"START..END"`` (Z = UTC).

    Raises on a malformed range — a promoted capability never silently
    discards its verified-history bound (I04R1 Repair 4).
    """
    if not value:
        return None, None
    parts = str(value).split("..")
    if len(parts) != 2:
        raise ValueError(f"malformed verified_history {value!r} (expected START..END)")
    try:
        start = _parse_datetime_utc(parts[0])
        end = _parse_datetime_utc(parts[1])
    except ValueError as exc:
        raise ValueError(f"malformed verified_history {value!r}: {exc}") from exc
    if start > end:
        raise ValueError(f"verified_history out of order {value!r}")
    return start, end


def _require_str(candidate: dict[str, Any], field: str, description: str) -> str:
    value = candidate.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"promotion candidate missing required {description} field {field!r}"
        )
    return value


def _require_str_list(
    candidate: dict[str, Any], field: str, description: str, *, allow_empty: bool
) -> list[str]:
    value = candidate.get(field)
    if not isinstance(value, list):
        raise ValueError(
            f"promotion candidate missing required {description} list {field!r}"
        )
    items = [str(v) for v in value]
    if not allow_empty and not items:
        raise ValueError(f"promotion candidate {field!r} must not be empty")
    return items


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
    cannot be strictly mapped fails closed (raises) — it is never silently
    widened or defaulted.
    """
    if candidates is None:
        candidates = load_promotion_candidates()

    sensors: dict[SensorFamily, SensorCapability] = {}
    for candidate in candidates:
        provider_candidate = candidate.get("provider")
        if provider_candidate != provider_id:
            continue

        sensor_name = _require_str(
            candidate, "sensor", "sensor"
        )
        try:
            sensor_family = SensorFamily(sensor_name)
        except ValueError:
            raise ValueError(
                f"{provider_id} promotion candidate has unknown sensor {sensor_name!r}"
            ) from None

        history_mode = _require_str(candidate, "history_mode", "history_mode")
        access_path = _require_str(candidate, "access_path", "access_path")

        # ---- strict controlled-value parsing (Repair 4) -----------------
        allowed_role = _parse_enum(
            ProviderRole, "allowed_role", candidate, provider_id, sensor_family
        )
        redundancy = _parse_enum(
            RedundancyClass,
            "redundancy_class",
            candidate,
            provider_id,
            sensor_family,
        )
        pit = _parse_enum(
            PITReadiness, "PIT_requirement", candidate, provider_id, sensor_family
        )

        auth = auth_mode_override or _ACCESS_PATH_AUTH.get(access_path)
        if auth is None or auth not in ALLOWED_AUTH_MODES:
            raise ValueError(
                f"{provider_id}/{sensor_family.value} access_path {access_path!r} "
                "cannot prove free-only access (fail closed)"
            )

        verified_start, verified_end = _parse_verified_range(
            str(candidate.get("verified_history", "") or "")
        )
        evidence_basis = _require_str_list(
            candidate, "evidence_basis", "evidence_basis", allow_empty=False
        )
        hazards = _require_str_list(
            candidate, "known_hazards", "known_hazards", allow_empty=True
        )

        methodology_pin = _require_str(
            candidate, "methodology_pin", "methodology_pin"
        )

        # ---- live/historical separation (Repair 3) ----------------------
        if history_mode in _HISTORY_MODE_SURFACE:
            historical_mode: HistoricalMode | None = _HISTORY_MODE_SURFACE[
                history_mode
            ]
            live_mode = LiveMode.NONE
            archive_mode = history_mode in {"ARCHIVE_ONLY", "THIRD_PARTY_ARCHIVE"}
        elif history_mode in _CURRENT_ONLY_SURFACES:
            historical_mode = _CURRENT_ONLY_SURFACES[history_mode]
            # A CURRENT_ONLY public REST snapshot is a current/live path, with
            # no invented historical depth.
            live_mode = (
                LiveMode.LIVE_REST
                if auth is AdapterAuthMode.NO_AUTH
                or auth is AdapterAuthMode.OPTIONAL_PUBLIC_KEY
                else LiveMode.NONE
            )
            archive_mode = False
        else:
            raise ValueError(
                f"{provider_id}/{sensor_family.value} has unknown history_mode "
                f"{history_mode!r} (fail closed)"
            )

        if (
            pit is not None
            and "PIT_READY" in pit.value
            and verified_start is None
            and history_mode in _HISTORY_MODE_SURFACE
        ):
            raise ValueError(
                f"{provider_id}/{sensor_family.value} PIT-ready historical "
                "capability requires a verified_history bound (fail closed)"
            )

        evidence_ref = AdapterEvidenceRef(
            evidence_id=evidence_basis[0],
            provider_id=provider_id,
            sensor_family=sensor_family,
        )

        sensors[sensor_family] = SensorCapability(
            sensor_family=sensor_family,
            supported=True,
            access_mode=access_path,
            historical_mode=historical_mode,
            live_mode=live_mode,
            archive_mode=archive_mode,
            auth_requirement=auth,
            free_access_status=FreeOnlyStatus.FREE_COMPLIANT,
            verified_history_start=verified_start,
            verified_history_end=verified_end,
            verified_at=verified_end,
            probe_evidence_ref=evidence_ref,
            allowed_role=allowed_role,
            redundancy_class=redundancy,
            pit_requirement=pit,
            methodology_pin=methodology_pin,
            known_hazards=hazards,
            evidence_basis=evidence_basis,
        )

    return ProviderCapabilities(provider_id=provider_id, sensors=sensors)


def _parse_enum(
    enum_cls: type[Any],
    field: str,
    candidate: dict[str, Any],
    provider_id: str,
    sensor_family: SensorFamily,
) -> Any:
    raw = candidate.get(field)
    valid = {e.value for e in enum_cls}
    if not isinstance(raw, str) or raw not in valid:
        raise ValueError(
            f"{provider_id}/{sensor_family.value} field {field!r} has unknown "
            f"value {raw!r} (strict promotion parsing fails closed)"
        )
    return enum_cls(raw)


def promotion_provider_ids(candidates: list[dict[str, object]]) -> list[str]:
    """Distinct promoted provider ids, in file order."""
    seen: list[str] = []
    for candidate in candidates:
        provider = str(candidate.get("provider", ""))
        if provider and provider not in seen:
            seen.append(provider)
    return seen


def promotion_bound_violations(
    declared: SensorCapability,
    bound: SensorCapability,
) -> list[str]:
    """Enforce the I14 promotion bounds for ONE provider/sensor (Repair 1).

    Returns a list of human-readable violations.  A provider adapter FAILS
    conformance when any violation exists — it may not widen or change any
    material I14 capability contract.  No provider-ranking hierarchy is
    invented here: every dimension is compared one-to-one against the bound.
    """
    violations: list[str] = []
    sensor = declared.sensor_family.value

    # 1. sensor must exist in the promotion file when supported
    if declared.supported and not bound.supported:
        violations.append(f"{sensor}: supported but not in promotion file")

    # 2. supported cannot be widened (nothing beyond the bound)
    if not bound.supported:
        return violations  # nothing else to bind against

    # 3. allowed_role cannot be upgraded or changed
    if declared.allowed_role != bound.allowed_role:
        violations.append(
            f"{sensor}: allowed_role {declared.allowed_role} != "
            f"bound {bound.allowed_role}"
        )

    # 4. historical_mode cannot be widened or changed
    if declared.historical_mode != bound.historical_mode:
        violations.append(
            f"{sensor}: historical_mode {declared.historical_mode} != "
            f"bound {bound.historical_mode}"
        )

    # 5. verified_history_start cannot move earlier than I14 evidence
    if (
        declared.verified_history_start is not None
        and bound.verified_history_start is not None
        and declared.verified_history_start < bound.verified_history_start
    ):
        violations.append(
            f"{sensor}: verified_history_start {declared.verified_history_start} "
            f"earlier than bound {bound.verified_history_start}"
        )

    # 6. verified_history_end cannot claim beyond the verified bound
    if (
        declared.verified_history_end is not None
        and bound.verified_history_end is not None
        and declared.verified_history_end > bound.verified_history_end
    ):
        violations.append(
            f"{sensor}: verified_history_end {declared.verified_history_end} "
            f"beyond bound {bound.verified_history_end}"
        )

    # 7. PIT requirement cannot be upgraded (fail closed ordering based on
    #    the frozen rubric: PIT_READY* must not exceed the bound)
    if declared.pit_requirement != bound.pit_requirement:
        violations.append(
            f"{sensor}: PIT requirement {declared.pit_requirement} != "
            f"bound {bound.pit_requirement}"
        )

    # 8. methodology_pin must match exactly when I14 requires one
    if bound.methodology_pin and declared.methodology_pin != bound.methodology_pin:
        violations.append(
            f"{sensor}: methodology_pin {declared.methodology_pin!r} != "
            f"bound {bound.methodology_pin!r}"
        )

    # 9. redundancy_class must match the frozen I14 classification
    if declared.redundancy_class != bound.redundancy_class:
        violations.append(
            f"{sensor}: redundancy_class {declared.redundancy_class} != "
            f"bound {bound.redundancy_class}"
        )

    # 10. access/auth cannot exceed the I14 access contract
    if declared.auth_requirement not in ALLOWED_AUTH_MODES:
        violations.append(
            f"{sensor}: auth_requirement {declared.auth_requirement} is not free-only"
        )

    # 11. known hazards must not be silently removed
    removed_hazards = set(bound.known_hazards) - set(declared.known_hazards)
    if removed_hazards:
        violations.append(
            f"{sensor}: known hazards removed: {sorted(removed_hazards)}"
        )

    # 12. evidence basis must resolve to I14 evidence
    if not set(bound.evidence_basis) <= set(declared.evidence_basis):
        violations.append(
            f"{sensor}: evidence basis does not resolve to the promotion file"
        )

    # 13. CURRENT_ONLY must remain CURRENT_ONLY (no invented history)
    if bound.historical_mode == HistoricalMode.LIVE_REST_ONLY and (
        declared.historical_mode != HistoricalMode.LIVE_REST_ONLY
    ):
        violations.append(
            f"{sensor}: CURRENT_ONLY bound widened to historical "
            f"{declared.historical_mode}"
        )

    # 14. MECHANISM_MICROSCOPE must not become general aggregate truth
    if (
        bound.allowed_role == ProviderRole.MECHANISM_MICROSCOPE
        and declared.allowed_role != ProviderRole.MECHANISM_MICROSCOPE
    ):
        violations.append(
            f"{sensor}: MECHANISM_MICROSCOPE role widened to "
            f"{declared.allowed_role}"
        )

    # 15. one provider/sensor may not silently inherit another sensor's role —
    #     already handled because every declared capability is compared to the
    #     bound for THAT sensor (role equality above).

    return violations