"""Provider-native acquisition-mode evidence (SENSOR-B3-I05 seam).

I04R2 deliberately froze `HistoryScope` (the coarse I14 label) separately from
`SensorCapability.historical_mode` (the EXACT native acquisition surface), and
left the exact native mode `None` until a provider resolves it from its own
Bloc 2 evidence.  This module is that resolution seam.

A PRODUCTION adapter may only set a concrete native historical/pagination mode
when it carries a `ProviderNativeCapabilityEvidence` object grounded in its own
committed Bloc 2 evidence.  Native evidence may REFINE acquisition mechanics
only:

    which historical surface (REST_RANGE / REST_CURSOR / archive / ...)
    which pagination mode
    endpoint/archive family
    timestamp/start unit + end semantics
    interval mechanics
    completion rule + resume mechanic
    evidence provenance

It may NEVER broaden or change:

    history_scope (coarse I14 label)
    verified date range
    role
    PIT requirement
    methodology pin
    access path / auth contract
    live mode
    archive status
    the promoted sensor set

Missing refinement evidence => leave the exact field UNKNOWN (None) or fail
provider conformance — never infer (I04R2 Issue 8 remains).
"""

from __future__ import annotations

from dataclasses import dataclass

from ...contracts.enums import SensorFamily
from .enums import HistoryScope, HistoricalMode, PaginationMode
from .models import SensorCapability

#: Historical modes that describe a bulk/object-storage archive surface.
_ARCHIVE_HISTORICAL_MODES: frozenset[HistoricalMode] = frozenset(
    {
        HistoricalMode.BULK_ARCHIVE_DAILY,
        HistoricalMode.BULK_ARCHIVE_MONTHLY,
        HistoricalMode.PUBLIC_OBJECT_STORAGE,
        HistoricalMode.THIRD_PARTY_ARCHIVE,
    }
)


@dataclass(frozen=True)
class ProviderNativeCapabilityEvidence:
    """Provider-supplied, Bloc-2-evidence-backed native acquisition mode.

    This is the machine-readable justification for setting an exact
    `historical_mode` / `pagination_mode` on a promoted capability.  It is a
    dataclass (not a stored data model): it is the *contract object* used to
    prove a refinement at conformance time, not a persisted acquisition
    artifact.
    """

    provider_id: str
    sensor_family: SensorFamily
    historical_mode: HistoricalMode
    pagination_mode: PaginationMode
    endpoint_family: str
    start_param: str
    start_unit: str
    end_param: str
    end_unit: str
    interval_param: str | None = None
    interval_mechanics: str | None = None
    completion_rule: str = ""
    resume_mechanic: str | None = None
    evidence_ids: tuple[str, ...] = ()
    methodology_pin: str = ""
    access_path: str = ""
    #: Provider-native PRODUCTION symbol scope proven by Bloc 2 evidence for
    #: this provider x sensor x instrument (SENSOR-B3-I05R1).  A production
    #: capability may only carry symbols the grant proves; probe/control-only
    #: instruments (e.g. Kraken SOL/DOGE) are never granted this way.
    instruments: tuple[str, ...] = ()
    verification_head: str | None = None


def _archive_compatible(evidence: ProviderNativeCapabilityEvidence) -> bool:
    return evidence.historical_mode in _ARCHIVE_HISTORICAL_MODES


def native_evidence_violations(
    provider_id: str,
    evidence: ProviderNativeCapabilityEvidence,
    bound: SensorCapability,
) -> list[str]:
    """Return violations between native evidence and the I14 promotion bound.

    Empty list means the evidence is a legitimate, scope-respecting refinement
    of the coarse I14 capability.  Violations fail production conformance —
    native evidence may never broaden a frozen I14 contract.
    """
    violations: list[str] = []
    sensor = evidence.sensor_family.value

    if evidence.provider_id != provider_id:
        violations.append(
            f"{sensor}: native evidence provider {evidence.provider_id!r} != "
            f"adapter {provider_id!r}"
        )
    if evidence.sensor_family != bound.sensor_family:
        violations.append(
            f"{sensor}: native evidence sensor {evidence.sensor_family} != "
            f"bound {bound.sensor_family.value}"
        )
    if not bound.supported:
        violations.append(f"{sensor}: native evidence on an unsupported sensor")

    # ---- evidence must resolve to the I14 lineage ---------------------
    missing = [
        eid for eid in evidence.evidence_ids if eid not in bound.evidence_basis
    ]
    if missing:
        violations.append(
            f"{sensor}: native evidence ids not in the I14 evidence_basis: {missing}"
        )

    # ---- coarse scope may not be broadened ----------------------------
    if bound.history_scope is HistoryScope.CURRENT_ONLY:
        violations.append(
            f"{sensor}: native historical evidence on a CURRENT_ONLY scope "
            "(CURRENT_ONLY must stay current)"
        )
    if bound.archive_mode and not _archive_compatible(evidence):
        violations.append(
            f"{sensor}: native historical mode {evidence.historical_mode} is not "
            "an archive surface for an ARCHIVE_ONLY bound"
        )
    if not bound.archive_mode and _archive_compatible(evidence):
        violations.append(
            f"{sensor}: native evidence switched a non-archive bound to archive "
            f"({evidence.historical_mode})"
        )

    # ---- access path + methodology must match the I14 contract --------
    if bound.access_mode and evidence.access_path and (
        evidence.access_path != bound.access_mode
    ):
        violations.append(
            f"{sensor}: native evidence access_path {evidence.access_path!r} != "
            f"bound {bound.access_mode!r}"
        )
    if bound.methodology_pin and evidence.methodology_pin != bound.methodology_pin:
        violations.append(
            f"{sensor}: native evidence methodology_pin "
            f"{evidence.methodology_pin!r} != bound {bound.methodology_pin!r} "
            "(methodology cannot change)"
        )

    # ---- production symbol scope must be proven by the grant ----------
    # A symbol may NOT reach a production capability merely because the Bloc 2
    # probe universe contains it: every production symbol must resolve to
    # evidence for this provider x sensor x instrument (SENSOR-B3-I05R1).
    if bound.symbol_scope:
        if not evidence.instruments:
            violations.append(
                f"{sensor}: symbol_scope declared but native evidence proves "
                "no instruments"
            )
        else:
            unproven = sorted(set(bound.symbol_scope) - set(evidence.instruments))
            if unproven:
                violations.append(
                    f"{sensor}: symbol_scope {unproven} not proven by native "
                    "evidence instruments"
                )

    return violations


def apply_native_evidence(
    capability: SensorCapability,
    evidence: ProviderNativeCapabilityEvidence,
    *,
    provider_id: str,
) -> SensorCapability:
    """Refine a promoted capability with exact native acquisition mechanics.

    Raises `ValueError` when the evidence would broaden the I14 contract.  On
    success the returned capability carries `historical_mode` / `pagination_mode`
    (and interval mechanics), all other I14 fields preserved.  Validation goes
    through `model_validate` so any residual invariant violation fails closed.
    """
    violations = native_evidence_violations(provider_id, evidence, capability)
    if violations:
        raise ValueError("native evidence violates I14 bounds: " + "; ".join(violations))
    data = capability.model_dump()
    data["historical_mode"] = evidence.historical_mode
    data["pagination_mode"] = evidence.pagination_mode
    if evidence.instruments:
        # the grant proves the production symbol scope; never inferred from
        # the probe universe or any other secondary list
        data["symbol_scope"] = list(evidence.instruments)
    return SensorCapability.model_validate(data)