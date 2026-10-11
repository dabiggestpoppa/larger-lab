"""SENSOR-B5-I05 - conservative market-availability derivation.

Frozen authority: bloc_05/02 section 4 (two clocks that must never be
substituted), section 5 (the eight ``availability_basis`` values and the
blocking rule), section 6 (the derivation signature quoted here verbatim, with
its conservative examples), section 13 (sensor-family anchors), section 14
(archive rows carry two time layers), section 16 (quality flags), section 18
rules 3/6/7 and bloc_05/06 s1 G2.

The one law everything else serves: **``ingested_at`` is never an input to
``market_available_at``**.  It is not consulted in any branch below, so
changing the ingestion instant cannot change the answer -- the distinction of
meaning survives even when the two values happen to be equal (I05 directive
phase D).

The rule ladder, each rung cited:

1. **Interval declared** (both bounds + a stated convention) ->
   ``PUBLIC_INTERVAL_CLOSE`` at ``max(interval_end_at, published_at)``:
   section 6 requires ``market_available_at >= interval_end_at`` ("Never
   interval start"), and a later publication proves an even later public
   time.  An unknown convention, a half-declared window or missing provider
   semantics fails closed instead.
   ``POINT_SAMPLE`` is the snapshot case: anchored at the sample instant, and
   only when the provider is classified contemporaneous-public (section 6's
   "explicitly classified" license); otherwise it is unplaceable.
2. **Published** (no interval) -> the publication instant, as
   ``PROVIDER_DECLARED_PUBLIC_TIME`` when the registry declares a
   ``PUBLISHED_AT`` field for this family (section 3: "when the provider says
   ..."), otherwise ``DELAYED_PUBLICATION``.  Section 6's funding case: the
   rate may be knowable before it is economically applied.
3. **Archive with contemporaneous-public evidence** -> the EVENT instant,
   labeled ``HISTORICAL_ARCHIVE_RECONSTRUCTION`` with the section 16 label
   flag.  Section 6: reconstruction is allowed ONLY when contemporaneous-
   public semantics are established; a 2026 download of 2022 rows without that
   evidence gets no market time at all.
4. **Classified realtime public source** -> ``REALTIME_PUBLIC_EVENT`` at the
   event instant (section 6 trade example: ``source_event_at`` may anchor
   availability "only when the source is explicitly classified
   contemporaneous-public").
5. **System-side knowledge only** -> ``SYSTEM_ONLY_OBSERVED`` with NO market
   time (section 5 bullet 3; unsupported rows are blocked from strict replay).
6. **Nothing known** -> ``UNKNOWN`` with no time.

Deterministic, pure, and wall-clock free: every input is explicit and the
same inputs always produce the same resolution.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import model_validator

from ...contracts.base import coerce_utc
from ...contracts.enums import SensorFamily
from ..enums import AvailabilityBasis, IntervalTimeConvention, NormalizationQualityFlag
from .enums import TimestampRole
from .models import (
    AvailabilityResolution,
    EvidenceRef,
    TimeEvidenceBase,
    UtcTimestamp,
)
from .semantics_registry import ProviderTimeSemantics

__all__ = [
    "AcquisitionMetadata",
    "derive_market_available_at",
]

_UNPLACEABLE_FLAGS = (
    NormalizationQualityFlag.TIME_INTERVAL_BOUNDARY_UNVERIFIED,
    NormalizationQualityFlag.TIME_MARKET_AVAILABILITY_UNKNOWN,
)
_UNKNOWN_FLAGS = (NormalizationQualityFlag.TIME_MARKET_AVAILABILITY_UNKNOWN,)


class AcquisitionMetadata(TimeEvidenceBase):
    """What WE know about acquisition -- the system clock, never market time.

    Frozen authority: section 3 (``observed_at``/``ingested_at``), section 4
    (the system availability clock), section 14 (T0 acquisition metadata
    proves which file we downloaded) and section 6 (archive reconstruction
    requires established contemporaneous-public semantics).

    ``contemporaneous_public_evidence_refs`` is that established evidence: a
    non-empty tuple means "documentation proves the underlying event was
    public at the time"; empty means we only know when our system saw the
    bytes.  References are durable identifiers, never paths.
    """

    observed_at: UtcTimestamp | None = None
    ingested_at: UtcTimestamp | None = None
    contemporaneous_public_evidence_refs: tuple[EvidenceRef, ...] = ()

    # ``frozen`` + extra=forbid come from TimeEvidenceBase.

    @model_validator(mode="after")
    def _check_evidence(self) -> AcquisitionMetadata:
        refs = self.contemporaneous_public_evidence_refs
        if len(set(refs)) != len(refs):
            raise ValueError("contemporaneous_public_evidence_refs contains duplicates")
        return self


def _resolve(
    sensor_family: SensorFamily,
    basis: AvailabilityBasis,
    market_available_at: datetime | None,
    flags: tuple[NormalizationQualityFlag, ...] = (),
) -> AvailabilityResolution:
    return AvailabilityResolution(
        sensor_family=sensor_family,
        availability_basis=basis,
        market_available_at=market_available_at,
        quality_flags=flags,
    )


def derive_market_available_at(
    *,
    sensor_family: SensorFamily,
    provider_semantics: ProviderTimeSemantics | None,
    event_time: datetime | None,
    interval_start: datetime | None,
    interval_end: datetime | None,
    published_at: datetime | None,
    acquisition_metadata: AcquisitionMetadata,
) -> AvailabilityResolution:
    """bloc_05/02 section 6: derive the earliest DEFENSIBLE market time.

    Conservative by construction: every rung requires positive evidence for
    the claim it makes, and anything less falls through to
    ``SYSTEM_ONLY_OBSERVED`` or ``UNKNOWN`` -- both of which carry no
    ``market_available_at`` and are blocked from strict replay by section 5.

    Naive inputs are refused at the door (section 18 rule 1).
    """
    event = coerce_utc(event_time) if event_time is not None else None
    start = coerce_utc(interval_start) if interval_start is not None else None
    end = coerce_utc(interval_end) if interval_end is not None else None
    published = coerce_utc(published_at) if published_at is not None else None

    if (start is None) != (end is None):
        # A half-declared window is an UNKNOWN window (section 7).
        return _resolve(
            sensor_family, AvailabilityBasis.UNKNOWN, None, _UNPLACEABLE_FLAGS
        )

    if start is not None and end is not None:
        if provider_semantics is None:
            # No declared convention exists, so no close can be justified.
            return _resolve(
                sensor_family, AvailabilityBasis.UNKNOWN, None, _UNPLACEABLE_FLAGS
            )
        convention = provider_semantics.interval_time_convention
        if convention is IntervalTimeConvention.PROVIDER_NATIVE_UNKNOWN:
            return _resolve(
                sensor_family, AvailabilityBasis.UNKNOWN, None, _UNPLACEABLE_FLAGS
            )
        if convention is IntervalTimeConvention.POINT_SAMPLE:
            if start != end:
                return _resolve(
                    sensor_family, AvailabilityBasis.UNKNOWN, None, _UNPLACEABLE_FLAGS
                )
            if not provider_semantics.contemporaneous_public:
                # An unproven snapshot has no defensible public instant.
                return _resolve(
                    sensor_family, AvailabilityBasis.UNKNOWN, None, _UNPLACEABLE_FLAGS
                )
            return _resolve(
                sensor_family, AvailabilityBasis.REALTIME_PUBLIC_SNAPSHOT, start
            )
        anchor = end
        if published is not None and published > anchor:
            anchor = published
        return _resolve(sensor_family, AvailabilityBasis.PUBLIC_INTERVAL_CLOSE, anchor)

    if published is not None:
        declared = False
        if provider_semantics is not None:
            declared = TimestampRole.PUBLISHED_AT in provider_semantics.timestamp_field_roles
        basis = (
            AvailabilityBasis.PROVIDER_DECLARED_PUBLIC_TIME
            if declared
            else AvailabilityBasis.DELAYED_PUBLICATION
        )
        return _resolve(sensor_family, basis, published)

    if event is not None and acquisition_metadata.contemporaneous_public_evidence_refs:
        # Section 6 archive rule: allowed ONLY with established evidence.
        return _resolve(
            sensor_family,
            AvailabilityBasis.HISTORICAL_ARCHIVE_RECONSTRUCTION,
            event,
            (NormalizationQualityFlag.TIME_ARCHIVE_RECONSTRUCTION,),
        )

    if (
        event is not None
        and provider_semantics is not None
        and provider_semantics.contemporaneous_public
    ):
        # Section 6 trade rule: source_event_at anchors only when classified.
        return _resolve(sensor_family, AvailabilityBasis.REALTIME_PUBLIC_EVENT, event)

    if (
        acquisition_metadata.observed_at is not None
        or acquisition_metadata.ingested_at is not None
    ):
        # We know when WE saw it.  That is not market availability (section 4).
        return _resolve(
            sensor_family,
            AvailabilityBasis.SYSTEM_ONLY_OBSERVED,
            None,
            _UNKNOWN_FLAGS,
        )

    return _resolve(sensor_family, AvailabilityBasis.UNKNOWN, None, _UNKNOWN_FLAGS)
