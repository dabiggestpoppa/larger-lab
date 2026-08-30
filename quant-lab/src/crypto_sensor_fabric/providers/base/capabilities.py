"""I14 evidence integration (SENSOR-B3-I04 / I04R1 / I04R2).

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

Parsing is STRICT (I04R1 Repair 4 / I04R2 Issue 6): an unknown or missing
controlled value, or a structurally malformed promotion file, FAILS CLOSED
with a ValueError.  Nothing is silently filtered or defaulted; the promotion
file is a control artifact.

Live vs historical separation (I04R1 Repair 3 / I04R2 Issues 8-9):

- `HistoryScope` carries the coarse I14 frozen label (HISTORICAL /
  CURRENT_ONLY / ARCHIVE_ONLY / THIRD_PARTY_ARCHIVE) unchanged.
- `SensorCapability.historical_mode` (the EXACT native acquisition mode) is
  NOT inferred from the coarse label — the base layer never manufactures
  e.g. REST_RANGE from HISTORICAL.  A provider adapter supplies the exact
  native mode later from its own Bloc 2 evidence.
- a HISTORICAL record sets `live_mode = NONE` (historical evidence does NOT
  auto-grant a live-production contract);
- a CURRENT_ONLY-public-REST record sets `live_mode = LIVE_REST` (current
  snapshot surface) with no invented historical depth;
- an ARCHIVE_ONLY / THIRD_PARTY_ARCHIVE record is historical-only, never
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
    HistoryScope,
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

#: Supported promotion-file schema versions.
_SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({"2.0"})

#: coarse I14 history label -> HistoryScope.  Unknown labels fail closed.
_HISTORY_SCOPE: dict[str, HistoryScope] = {
    "HISTORICAL": HistoryScope.HISTORICAL,
    "CURRENT_ONLY": HistoryScope.CURRENT_ONLY,
    "ARCHIVE_ONLY": HistoryScope.ARCHIVE_ONLY,
    "THIRD_PARTY_ARCHIVE": HistoryScope.THIRD_PARTY_ARCHIVE,
}

#: coarse scope labels that imply an archive/object-storage acquisition class.
_ARCHIVE_SCOPES: frozenset[str] = frozenset(
    {"ARCHIVE_ONLY", "THIRD_PARTY_ARCHIVE"}
)

#: access_path string -> auth mode.  Unknown access paths cannot prove free
#: access and FAIL CLOSED (I04R2 Issue 7 — no auth override can change this).
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
    """Parse the ``verified_history`` range ``\"START..END\"`` (Z = UTC).

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
    """Load + structurally validate the I14 promotion-candidate list.

    The promotion file is a CONTROL ONLY input list.  Structural ambiguity is
    a HARD failure (I04R2 Issue 6): nothing is silently filtered or repaired.
    Validates the root mapping, schema version, the candidates list shape, and
    that every candidate carries provider + sensor.  (Duplicate/detailed field
    validation happens in `capabilities_from_promotion` post filtering.)
    """
    config_path = path or DEFAULT_PROMOTION_FILE
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError(
            f"promotion file {config_path} root must be a mapping, got "
            f"{type(data).__name__}"
        )

    schema_version = data.get("schema_version")
    if not isinstance(schema_version, str) or not schema_version:
        raise ValueError(
            f"promotion file {config_path} missing required field 'schema_version'"
        )
    if schema_version not in _SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(
            f"promotion file {config_path} unsupported schema_version "
            f"{schema_version!r} (supported={sorted(_SUPPORTED_SCHEMA_VERSIONS)})"
        )

    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError(
            f"promotion file {config_path} has no non-empty 'candidates' list"
        )

    validated: list[dict[str, object]] = []
    for index, item in enumerate(candidates):
        if not isinstance(item, dict):
            raise ValueError(
                f"promotion file {config_path} candidate[{index}] is not a mapping "
                f"({type(item).__name__})"
            )
        for field in ("provider", "sensor"):
            value = item.get(field)
            if not isinstance(value, str) or not value:
                raise ValueError(
                    f"promotion file {config_path} candidate[{index}] missing "
                    f"required field {field!r}"
                )
        validated.append(item)
    return validated


def capabilities_from_promotion(
    provider_id: str,
    candidates: list[dict[str, object]] | None = None,
) -> ProviderCapabilities:
    """Build `ProviderCapabilities` for one provider from I14 candidates.

    Every declared capability is bound by the I14 fields.  A candidate that
    cannot be strictly mapped fails closed (raises) — it is never silently
    widened or defaulted.  Duplicate provider×sensor candidates (with or
    without conflicting values) are a structural error — a later row NEVER
    overwrites an earlier one in the generated capability map.

    No `auth_mode_override` exists here: the I14 `access_path` alone is
    authoritative for the acquisition auth contract, and that contract may
    never be changed by a caller (I04R2 Issue 7).
    """
    if candidates is None:
        candidates = load_promotion_candidates()

    sensors: dict[SensorFamily, SensorCapability] = {}
    seen_sensors: set[SensorFamily] = set()

    for candidate in candidates:
        provider_candidate = candidate.get("provider")
        if provider_candidate != provider_id:
            continue

        sensor_name = _require_str(candidate, "sensor", "sensor")
        try:
            sensor_family = SensorFamily(sensor_name)
        except ValueError:
            raise ValueError(
                f"{provider_id} promotion candidate has unknown sensor {sensor_name!r}"
            ) from None

        if sensor_family in seen_sensors:
            raise ValueError(
                f"{provider_id} has duplicate promotion candidates for sensor "
                f"{sensor_name!r} (later rows never overwrite earlier ones)"
            )

        history_label = _require_str(candidate, "history_mode", "history_mode")
        access_path = _require_str(candidate, "access_path", "access_path")
        scope = _HISTORY_SCOPE.get(history_label)
        if scope is None:
            raise ValueError(
                f"{provider_id}/{sensor_family.value} has unknown history_mode "
                f"{history_label!r} (fail closed)"
            )

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

        # Access contract derives ONLY from the authoritative I14 access_path
        # (Issue 7).  Unknown paths cannot prove free-only access -> fail.
        auth = _ACCESS_PATH_AUTH.get(access_path)
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

        # ---- coarse scope -> live/archive derivation (Issues 8-9) -------
        # The coarse label survives verbatim as `history_scope`; the exact
        # native historical_mode is NEVER inferred here (left None for the
        # provider's own Bloc 2 evidence later).
        archive_mode = scope in _ARCHIVE_SCOPES

        if (
            pit is not None
            and "PIT_READY" in pit.value
            and verified_start is None
            and scope is HistoryScope.HISTORICAL
        ):
            raise ValueError(
                f"{provider_id}/{sensor_family.value} PIT-ready historical "
                "capability requires a verified_history bound (fail closed)"
            )

        if scope in _ARCHIVE_SCOPES:
            # archive-only surfaces never imply REST or live capability
            live_mode = LiveMode.NONE
        elif scope is HistoryScope.CURRENT_ONLY:
            # a CURRENT_ONLY public REST snapshot is a current/live path with
            # no invented historical depth
            live_mode = (
                LiveMode.LIVE_REST
                if auth
                in (AdapterAuthMode.NO_AUTH, AdapterAuthMode.OPTIONAL_PUBLIC_KEY)
                else LiveMode.NONE
            )
        else:  # HISTORICAL
            # historical evidence does NOT auto-grant a live-production contract
            live_mode = LiveMode.NONE

        evidence_ref = AdapterEvidenceRef(
            evidence_id=evidence_basis[0],
            provider_id=provider_id,
            sensor_family=sensor_family,
        )

        sensors[sensor_family] = SensorCapability(
            sensor_family=sensor_family,
            supported=True,
            access_mode=access_path,
            # exact native historical mode is provider-supplied, not inferred
            historical_mode=None,
            history_scope=scope,
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
        seen_sensors.add(sensor_family)

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

    I04R2 (Issues 4/9) additionally binds live/archive/access/auth surfaces
    and the coarse history scope, so a provider cannot silently flip surfaces
    (CURRENT_ONLY->historical, archive->REST, historical->live, non-archive->
    archive).
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

    # 4. coarse history scope cannot change (CURRENT_ONLY->historical, etc.)
    if declared.history_scope != bound.history_scope:
        violations.append(
            f"{sensor}: history_scope {declared.history_scope} != "
            f"bound {bound.history_scope}"
        )

    # 5. exact native historical_mode cannot be manufactured or widened.
    #    If the bound's exact mode is unknown (None), the declared MUST also be
    #    None — the base layer never invents a native mode from a coarse label
    #    (Issue 8/9).  If the bound pins a mode, the declared must match it.
    if bound.historical_mode is None:
        if declared.historical_mode is not None:
            violations.append(
                f"{sensor}: manufactured native historical_mode "
                f"{declared.historical_mode} from a coarse scope (bound has "
                "no exact native mode)"
            )
    elif declared.historical_mode != bound.historical_mode:
        violations.append(
            f"{sensor}: historical_mode {declared.historical_mode} != "
            f"bound {bound.historical_mode}"
        )

    # 6. live mode must match the bound exactly (historical never auto-grants
    #    live; CURRENT_ONLY keeps its live snapshot surface).
    if declared.live_mode != bound.live_mode:
        violations.append(
            f"{sensor}: live_mode {declared.live_mode} != bound {bound.live_mode}"
        )

    # 7. archive mode cannot change (archive-only can't become REST; a
    #    non-archive surface can't silently become archive).
    if declared.archive_mode != bound.archive_mode:
        violations.append(
            f"{sensor}: archive_mode {declared.archive_mode} != "
            f"bound {bound.archive_mode}"
        )

    # 8. the acquisition access path itself is scientific provenance.
    if declared.access_mode != bound.access_mode:
        violations.append(
            f"{sensor}: access_path {declared.access_mode} != "
            f"bound {bound.access_mode}"
        )

    # 9. verified_history_start cannot move earlier than I14 evidence
    if (
        declared.verified_history_start is not None
        and bound.verified_history_start is not None
        and declared.verified_history_start < bound.verified_history_start
    ):
        violations.append(
            f"{sensor}: verified_history_start {declared.verified_history_start} "
            f"earlier than bound {bound.verified_history_start}"
        )

    # 10. verified_history_end cannot claim beyond the verified bound
    if (
        declared.verified_history_end is not None
        and bound.verified_history_end is not None
        and declared.verified_history_end > bound.verified_history_end
    ):
        violations.append(
            f"{sensor}: verified_history_end {declared.verified_history_end} "
            f"beyond bound {bound.verified_history_end}"
        )

    # 11. PIT requirement cannot be upgraded (bound must never be exceeded)
    if declared.pit_requirement != bound.pit_requirement:
        violations.append(
            f"{sensor}: PIT requirement {declared.pit_requirement} != "
            f"bound {bound.pit_requirement}"
        )

    # 12. methodology_pin must match exactly when I14 requires one
    if bound.methodology_pin and declared.methodology_pin != bound.methodology_pin:
        violations.append(
            f"{sensor}: methodology_pin {declared.methodology_pin!r} != "
            f"bound {bound.methodology_pin!r}"
        )

    # 13. redundancy_class must match the frozen I14 classification
    if declared.redundancy_class != bound.redundancy_class:
        violations.append(
            f"{sensor}: redundancy_class {declared.redundancy_class} != "
            f"bound {bound.redundancy_class}"
        )

    # 14. auth/access cannot exceed the I14 access contract (Issue 4/7)
    if declared.auth_requirement != bound.auth_requirement:
        violations.append(
            f"{sensor}: auth_requirement {declared.auth_requirement} != "
            f"bound {bound.auth_requirement}"
        )
    if declared.auth_requirement not in ALLOWED_AUTH_MODES:
        violations.append(
            f"{sensor}: auth_requirement {declared.auth_requirement} is not free-only"
        )

    # 15. free-only status must stay at least as strict as the bound
    if declared.free_access_status != bound.free_access_status:
        violations.append(
            f"{sensor}: free_access_status {declared.free_access_status} != "
            f"bound {bound.free_access_status}"
        )

    # 16. known hazards must not be silently removed
    removed_hazards = set(bound.known_hazards) - set(declared.known_hazards)
    if removed_hazards:
        violations.append(
            f"{sensor}: known hazards removed: {sorted(removed_hazards)}"
        )

    # 17. evidence basis must resolve to I14 evidence (not silently replaced)
    if not set(bound.evidence_basis) <= set(declared.evidence_basis):
        violations.append(
            f"{sensor}: evidence basis does not resolve to the promotion file"
        )

    # 18. CURRENT_ONLY must remain CURRENT_ONLY (no invented history)
    if bound.history_scope is HistoryScope.CURRENT_ONLY and (
        declared.history_scope != HistoryScope.CURRENT_ONLY
    ):
        violations.append(
            f"{sensor}: CURRENT_ONLY bound widened to historical "
            f"({declared.history_scope})"
        )

    # 19. MECHANISM_MICROSCOPE must not become general aggregate truth
    if (
        bound.allowed_role == ProviderRole.MECHANISM_MICROSCOPE
        and declared.allowed_role != ProviderRole.MECHANISM_MICROSCOPE
    ):
        violations.append(
            f"{sensor}: MECHANISM_MICROSCOPE role widened to "
            f"{declared.allowed_role}"
        )

    # 20. one provider/sensor may not silently inherit another sensor's role —
    #     already handled because every declared capability is compared to the
    #     bound for THAT sensor (role equality above).

    return violations