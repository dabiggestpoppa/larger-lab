"""Bloc 1 quality state model and conservative flag→state aggregation.

Individual record `quality_flags` are additive (Bloc 1 §12).  Runtime health
states (`QualityState`) are a separate, coarser layer consumed by later blocs;
full `SensorHealth` aggregation arrives in Bloc 6.  This module only provides
the base contract and the conservative downgrade rules that Bloc 6 will build on.

Hard rules:

- (B1-T53) a record flagged `STALE_SOURCE` must never aggregate to
  `QualityState.GOOD`.
- (repair SENSOR-B1-R03) hard blocking flags (`BLOCKING_QUALITY_FLAGS`)
  dominate every non-blocking downgrade and resolve to `QualityState.BLOCKED`.
"""

from __future__ import annotations

from collections.abc import Iterable

from .enums import QualityFlag, QualityState

#: Ordered downgrade rules.  First matching flag wins; order matters because
#: staleness is the most severe non-blocked condition.
_QUALITY_DOWNGRADES: tuple[tuple[QualityFlag, QualityState], ...] = (
    (QualityFlag.STALE_SOURCE, QualityState.STALE),
    (QualityFlag.PROVIDER_DEGRADED, QualityState.DEGRADED),
    (QualityFlag.PARTIAL_INTERVAL, QualityState.PARTIAL),
    (QualityFlag.HISTORICAL_DEPTH_UNVERIFIED, QualityState.UNVERIFIED),
    (QualityFlag.ACCESS_CLASS_UNVERIFIED, QualityState.UNVERIFIED),
)

#: Flags that indicate the record is not trustworthy enough to be presented as
#: a healthy, ready observation without explicit downstream consent.
BLOCKING_QUALITY_FLAGS: frozenset[QualityFlag] = frozenset(
    {
        QualityFlag.PIT_RISK,
        QualityFlag.INSTRUMENT_ID_UNRESOLVED,
        QualityFlag.UNIT_NORMALIZATION_UNAVAILABLE,
        QualityFlag.VENUE_NOT_DECOMPOSABLE,
    }
)


def derive_quality_state(flags: Iterable[QualityFlag]) -> QualityState:
    """Conservative flag→state aggregation (B1-T53, SENSOR-B1-R03).

    Hard blocking flags dominate everything and resolve to BLOCKED before any
    STALE / DEGRADED / PARTIAL / UNVERIFIED downgrade is evaluated.  Otherwise
    returns the most severe downgrade matching any flag, defaulting to GOOD.
    Downstream layers may only preserve or further downgrade this state — they
    may never upgrade it (global acceptance principle 14).
    """
    flag_set = frozenset(flags)
    if flag_set & BLOCKING_QUALITY_FLAGS:
        return QualityState.BLOCKED
    for flag, state in _QUALITY_DOWNGRADES:
        if flag in flag_set:
            return state
    return QualityState.GOOD


def has_blocking_flag(flags: Iterable[QualityFlag]) -> bool:
    """True when any hard-blocking quality flag is present.

    Hard failures (integrity/PIT/semantic) must block rather than average into
    an attractive aggregate number (Bloc 1 §15 doctrine).
    """
    return bool(frozenset(flags) & BLOCKING_QUALITY_FLAGS)
