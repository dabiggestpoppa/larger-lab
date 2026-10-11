"""SENSOR-B5-I05 - interval topology, boundaries and the completion law.

Frozen authority: bloc_05/02 section 7 (every interval observation must
DECLARE ``interval_closed`` and ``interval_time_convention``; never guess
whether ``12:00`` starts, ends or samples a window), section 6
(``market_available_at >= interval_end_at`` -- never the start), section 18
rule 2 (no completed interval becomes available before its justified close)
and bloc_05/06 s1 G2.

Design consequences of those clauses:

* membership is decided at the exact edges, per convention, and
  ``PROVIDER_NATIVE_UNKNOWN`` makes it UNDECIDABLE -- the answer is an
  exception, never a default side;
* ``earliest_justified_availability()`` refuses an unclosed window (there is
  no justified close yet) and refuses an unknown convention (there is no
  justified boundary), which is what makes "available before the close"
  structurally impossible rather than merely discouraged;
* ``POINT_SAMPLE`` is a zero-width instant by construction, so a snapshot can
  never masquerade as a window, and a window can never masquerade as a point.

:func:`earliest_justified_availability_from` consumes the ratified B5-I01
``ObservationTimeEnvelope`` read-only: the envelope already carries the two
declaration fields, so I05 reads them and never writes them.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import model_validator

from ..enums import IntervalTimeConvention
from ..models import ObservationTimeEnvelope
from .models import TimeEvidenceBase, UtcTimestamp

__all__ = [
    "IntervalWindow",
    "UndecidableIntervalBoundary",
    "earliest_justified_availability_from",
]


class UndecidableIntervalBoundary(ValueError):
    """Raised when a boundary convention is declared UNKNOWN (section 7).

    Not a ``False``: "we do not know which side the boundary is on" and "the
    point is outside the window" are different answers, and collapsing them
    would be the guess section 7 forbids.
    """


class IntervalWindow(TimeEvidenceBase):
    """One interval with its boundary semantics declared up front.

    Laws (fail closed):

    * ``interval_end_at >= interval_start_at`` (the universally valid
      ordering, matching the B5-I01 envelope);
    * an ordered convention requires a STRICT window -- a zero-width
      ``LEFT_CLOSED_RIGHT_OPEN`` window is a point sample wearing the wrong
      declaration, and section 7 exists to prevent exactly that confusion;
    * ``POINT_SAMPLE`` requires ``start == end``.
    """

    interval_start_at: UtcTimestamp
    interval_end_at: UtcTimestamp
    interval_closed: bool
    interval_time_convention: IntervalTimeConvention

    @model_validator(mode="after")
    def _check_span(self) -> IntervalWindow:
        start, end = self.interval_start_at, self.interval_end_at
        if self.interval_time_convention is IntervalTimeConvention.POINT_SAMPLE:
            if start != end:
                raise ValueError(
                    "POINT_SAMPLE requires a zero-width window "
                    f"({start.isoformat()} != {end.isoformat()}): a sampled "
                    "instant is not an interval (bloc_05/02 section 7)"
                )
            return self
        if end <= start:
            raise ValueError(
                "an ordered interval convention requires interval_end_at > "
                f"interval_start_at ({end.isoformat()} <= {start.isoformat()})"
            )
        return self

    def contains(self, at: UtcTimestamp) -> bool:
        """Membership at the exact edges of the declared convention.

        Raises :class:`UndecidableIntervalBoundary` for
        ``PROVIDER_NATIVE_UNKNOWN`` -- membership is never guessed.
        """
        if self.interval_time_convention is IntervalTimeConvention.PROVIDER_NATIVE_UNKNOWN:
            raise UndecidableIntervalBoundary(
                "membership is undecidable under PROVIDER_NATIVE_UNKNOWN "
                "(bloc_05/02 section 7): declare the provider convention "
                "instead of assuming a side"
            )
        if self.interval_time_convention is IntervalTimeConvention.POINT_SAMPLE:
            return at == self.interval_start_at
        if self.interval_time_convention is IntervalTimeConvention.LEFT_CLOSED_RIGHT_OPEN:
            return self.interval_start_at <= at < self.interval_end_at
        return self.interval_start_at < at <= self.interval_end_at

    def earliest_justified_availability(self) -> datetime:
        """The earliest instant this window's value may claim market presence.

        section 6: ``market_available_at >= interval_end_at`` for an ordered
        window -- the start is never an answer -- and section 18 rule 2 adds
        that an UNCLOSED window has no justified close at all.
        """
        if not self.interval_closed:
            raise ValueError(
                "an interval that is not closed has no justified completion "
                "time (bloc_05/02 section 18 rule 2): wait for the close or "
                "model the partial updates separately (section 6)"
            )
        if self.interval_time_convention is IntervalTimeConvention.PROVIDER_NATIVE_UNKNOWN:
            raise UndecidableIntervalBoundary(
                "completion time is undecidable under PROVIDER_NATIVE_UNKNOWN "
                "(bloc_05/02 section 7/section 18 rule 2)"
            )
        if self.interval_time_convention is IntervalTimeConvention.POINT_SAMPLE:
            return self.interval_start_at
        return self.interval_end_at


def earliest_justified_availability_from(envelope: ObservationTimeEnvelope) -> datetime:
    """Read the I01 envelope's declarations and apply the completion law.

    Read-only: ``envelope`` is never mutated.  Every undeclared element is a
    refusal -- bounds without a convention, bounds without an explicit closure
    flag, an open window, or no bounds at all all raise instead of defaulting.
    """
    start, end = envelope.interval_start_at, envelope.interval_end_at
    if start is None or end is None:
        raise ValueError(
            "interval_start_at and interval_end_at are both required "
            "(bloc_05/02 section 7)"
        )
    if envelope.interval_time_convention is None:
        raise ValueError(
            "interval_time_convention must be declared; None is a guess "
            "(bloc_05/02 section 7)"
        )
    if envelope.interval_closed is None:
        raise ValueError(
            "interval_closed must be declared explicitly; None is not a "
            "substitute for declaring it (bloc_05/02 section 7)"
        )
    window = IntervalWindow(
        interval_start_at=start,
        interval_end_at=end,
        interval_closed=envelope.interval_closed,
        interval_time_convention=envelope.interval_time_convention,
    )
    return window.earliest_justified_availability()
