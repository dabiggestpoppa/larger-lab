"""SENSOR-B5-I05 - canonical timestamp evidence and the availability resolution.

Frozen authority: bloc_05/02 section 2/3 (the nine-clock vocabulary), section 5
(availability basis), section 6 (``AvailabilityResolution`` as the derivation
output), section 8 (UTC + declared precision), section 9 (clock skew), section
18 invariants 1/3/5, and bloc_05/07 F8 (no single timestamp silently
substitutes for all meanings).

What this module refuses, and why:

* a naive timestamp (invariant 1) -- local time is not a time;
* a declared precision that the value cannot carry (invariant 5) -- second
  precision cannot hold microseconds, and millisecond precision cannot hold
  microsecond digits, because fabricating sub-millisecond ordering out of
  millisecond input is exactly the failure section 8 forbids;
* a clock-skew methodology with no measured skew (section 9) -- and it never
  applies the skew: ``at`` is always the raw source value;
* a market-availability time paired with ``UNKNOWN`` or with
  ``SYSTEM_ONLY_OBSERVED`` (section 5, invariants 3) -- the two fail-closed
  bases exist precisely to say "this cannot be placed in market time";
* duplicate quality flags -- a flag set is a set.

Immutable (``frozen``): temporal evidence is versioned truth.  Updating it
means producing a new record, never mutating one in place.

``availability_confidence`` is carried as an OPAQUE TOKEN, never as an enum:
bloc_05/02 section 5 names the field but freezes no vocabulary for it, and
``BLOC_05_I01_TYPE_SCOPE_MATRIX.json`` records that gap as ``NOT FROZEN``.
The I03 ``InstrumentAlias.confidence`` precedent applies -- a validated token,
never an invented scale (HIGH/MEDIUM/LOW) and never a fabricated numeric.
"""

from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Annotated, Mapping

from pydantic import (
    AfterValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from ...contracts.base import coerce_utc
from ...contracts.enums import SensorFamily
from ..enums import (
    AvailabilityBasis,
    NormalizationQualityFlag,
    TimestampPrecision,
)
from ..models import NormalizationModelBase, OpaqueIdentifier
from .enums import TimestampRole

__all__ = [
    "TIMESTAMP_ROLE_FIELD",
    "AvailabilityConfidenceToken",
    "AvailabilityResolution",
    "CanonicalTimestamp",
    "EvidenceRef",
    "TimeEvidenceBase",
]


def _reject_blank(value: str) -> str:
    if not value.strip():
        raise ValueError("must not be blank")
    return value


def _require_unpadded(value: str) -> str:
    if value != value.strip():
        raise ValueError(f"must not carry leading/trailing whitespace: {value!r}")
    return value


def _reject_path_shaped(value: str) -> str:
    """Evidence names durable identifiers, never files (bloc_05/01 section 17)."""
    if (
        "/" in value
        or "\\" in value
        or re.match(r"^[A-Za-z]:", value)
        or value.startswith(".")
    ):
        raise ValueError(f"source evidence must be a durable identifier, not a path: {value!r}")
    return value


def _reject_numeric(value: str) -> str:
    """No fabricated numerics: confidence is a declared claim, not a score."""
    try:
        float(value)
    except ValueError:
        return value
    raise ValueError(f"confidence must not be numeric: {value!r}")


def _require_unique(values: tuple[str, ...]) -> tuple[str, ...]:
    if len(set(values)) != len(values):
        raise ValueError("contains duplicate references")
    return values


class TimeEvidenceBase(NormalizationModelBase):
    """Immutable, fail-closed base for every I05 temporal record."""

    model_config = ConfigDict(extra="forbid", frozen=True)


#: Timezone-aware UTC datetime; naive input is refused outright (s18.1).
UtcTimestamp = Annotated[datetime, AfterValidator(coerce_utc)]

#: A durable source-evidence identifier (never a filesystem path).
EvidenceRef = Annotated[
    str,
    StringConstraints(min_length=1, pattern=r"\S"),
    AfterValidator(_reject_blank),
    AfterValidator(_require_unpadded),
    AfterValidator(_reject_path_shaped),
]

#: ``bloc_05/02`` section 5 names this field and freezes NO vocabulary for it.
#: It is therefore an opaque validated token, exactly like the I03 alias
#: ``confidence``: non-blank, unpadded, and never a number.
AvailabilityConfidenceToken = Annotated[
    str,
    StringConstraints(min_length=1, pattern=r"\S"),
    AfterValidator(_reject_blank),
    AfterValidator(_require_unpadded),
    AfterValidator(_reject_numeric),
]

#: The frozen section 2 field for each role -- frozen DATA, not a lookup the
#: caller can influence.  It is what makes "the timestamp means X" checkable
#: against the ratified ``ObservationTimeEnvelope`` field of the same name.
TIMESTAMP_ROLE_FIELD: Mapping[TimestampRole, str] = MappingProxyType(
    {
        TimestampRole.SOURCE_EVENT_AT: "source_event_at",
        TimestampRole.INTERVAL_START_AT: "interval_start_at",
        TimestampRole.INTERVAL_END_AT: "interval_end_at",
        TimestampRole.EFFECTIVE_AT: "effective_at",
        TimestampRole.PUBLISHED_AT: "published_at",
        TimestampRole.MARKET_AVAILABLE_AT: "market_available_at",
        TimestampRole.OBSERVED_AT: "observed_at",
        TimestampRole.INGESTED_AT: "ingested_at",
        TimestampRole.NORMALIZED_AT: "normalized_at",
    }
)


def _validate_declared_precision(precision: TimestampPrecision, at: datetime) -> None:
    """section 8 / invariant 5: the declared precision must be truthful."""
    micro = at.microsecond
    if precision is TimestampPrecision.SECOND and micro != 0:
        raise ValueError(
            "SECOND precision cannot carry a sub-second component "
            f"({at.isoformat()}); declaring it fabricates ordering"
        )
    if precision is TimestampPrecision.MILLISECOND and micro % 1000 != 0:
        raise ValueError(
            "MILLISECOND precision cannot carry microsecond digits "
            f"({at.isoformat()}); section 8 forbids fabricating microsecond "
            "ordering from millisecond input"
        )
    if precision is TimestampPrecision.DATE_ONLY and (
        at.hour or at.minute or at.second or micro
    ):
        raise ValueError(
            "DATE_ONLY precision requires a midnight value "
            f"({at.isoformat()}); a time component is not date-only truth"
        )


class CanonicalTimestamp(TimeEvidenceBase):
    """One timestamp whose meaning, precision and provenance are declared.

    Fields and their frozen authority:

    * ``at`` -- the RAW source timestamp in UTC (section 8; invariant 1);
    * ``role`` -- which of the nine canonical clocks it is (section 2/3);
    * ``precision`` -- the source precision, declared evidence (section 8);
    * ``clock_skew_ms`` / ``clock_skew_methodology_id`` -- the section 9
      quality fields, both optional, never applied to ``at``.

    Laws (fail closed): naive input refused; declared precision must be
    truthful for the value; a methodology without a measured skew is refused
    (section 9: correction requires a documented methodology, so a methodology
    with nothing to correct is an orphaned claim); and the record is immutable.
    """

    at: UtcTimestamp
    role: TimestampRole
    precision: TimestampPrecision
    clock_skew_ms: Decimal | None = None
    clock_skew_methodology_id: OpaqueIdentifier | None = None

    @model_validator(mode="after")
    def _check_precision(self) -> CanonicalTimestamp:
        _validate_declared_precision(self.precision, self.at)
        return self

    @model_validator(mode="after")
    def _check_skew(self) -> CanonicalTimestamp:
        if (
            self.clock_skew_methodology_id is not None
            and self.clock_skew_ms is None
        ):
            raise ValueError(
                "clock_skew_methodology_id without a measured clock_skew_ms "
                "(bloc_05/02 section 9: a correction methodology must name a "
                "measured discrepancy)"
            )
        return self


class AvailabilityResolution(TimeEvidenceBase):
    """The conservative output of ``availability.derive_market_available_at``.

    Frozen authority: bloc_05/02 section 6 names the function and this return
    type; section 5 defines ``availability_basis``; section 16 supplies the
    quality flags.

    Pairing laws (invariants 3, section 5):

    * ``UNKNOWN`` and ``SYSTEM_ONLY_OBSERVED`` may never carry a
      ``market_available_at`` -- they are the two "this cannot be placed in
      market time" states, and pairing them with a time is the exact
      ingestion-substitution failure the plan forbids;
    * every OTHER basis must carry a time -- a defensible basis with no time
      is an unfinished claim, and section 5 requires replay-relevant rows to
      carry both;
    * ``quality_flags`` is a duplicate-free tuple of the frozen section 16
      vocabulary -- labels are disclosed, never silently dropped.
    """

    sensor_family: SensorFamily
    availability_basis: AvailabilityBasis
    market_available_at: UtcTimestamp | None = None
    quality_flags: tuple[NormalizationQualityFlag, ...] = Field(default=())

    @model_validator(mode="after")
    def _check_pairing(self) -> AvailabilityResolution:
        unplaceable = (
            AvailabilityBasis.UNKNOWN,
            AvailabilityBasis.SYSTEM_ONLY_OBSERVED,
        )
        if self.availability_basis in unplaceable and self.market_available_at is not None:
            raise ValueError(
                f"{self.availability_basis.value} may not be paired with "
                "market_available_at (bloc_05/02 section 5/section 18 rule 3: "
                "an unplaceable availability claim must not be presented as a "
                "market-availability time)"
            )
        if (
            self.availability_basis not in unplaceable
            and self.market_available_at is None
        ):
            raise ValueError(
                f"{self.availability_basis.value} requires market_available_at "
                "(bloc_05/02 section 5: a defensible basis without a time is an "
                "unfinished availability claim)"
            )
        flags = tuple(self.quality_flags)
        if len(set(flags)) != len(flags):
            raise ValueError("quality_flags contains duplicates")
        return self
