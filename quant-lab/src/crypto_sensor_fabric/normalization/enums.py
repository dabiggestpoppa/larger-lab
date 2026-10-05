"""SENSOR-B5-I01 — frozen Bloc 5 normalization vocabularies (base layer only).

Every member set in this module is copied from a frozen Bloc 5 planning
document; the docstring of each enum names that document.  Adding a member is
a plan change requiring operator review, never a convenience.  This is the same
freeze discipline `storage/enums.py` and `contracts/enums.py` already follow.

**This module resolves nothing.**  There is no registry lookup, no alias
matching, no unit conversion, no timestamp derivation and no provider behavior
here, because all of those belong to later frozen checkpoints (B5-I02..I23).
See `BLOC_05_I01_TYPE_SCOPE_MATRIX.json` for the full A/B split.

**Nothing here duplicates an accepted upstream vocabulary.**  The base layer
consumes, and never re-declares:

* ``SensorFamily``            -- ``crypto_sensor_fabric.contracts.enums``
* ``Granularity``             -- ``crypto_sensor_fabric.probes.enums``
* ``CoverageState``           -- ``crypto_sensor_fabric.storage`` (public)
* ``RevisionState``           -- ``crypto_sensor_fabric.storage`` (public)
* ``SourceUnitState`` / ``SourceUnitVariability`` / ``SourceUnitContract`` /
  ``SourceUnitEvidence``      -- ``crypto_sensor_fabric.storage`` (public)

Two frozen vocabularies are deliberately NOT collapsed, because the plan spells
them differently and the difference is meaningful:

* status (bloc_05/03 §15):   ``BLOCKED_IDENTITY``
* missingness (bloc_05/05 §12): ``IDENTITY_BLOCKED``

``BLOCKED_STATUS_MISSINGNESS_REASON`` states the correspondence as frozen data
instead of renaming one side to match the other.
"""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Mapping

__all__ = [
    "BLOCKED_STATUS_MISSINGNESS_REASON",
    "BLOCKING_QUALITY_FLAGS",
    "AvailabilityBasis",
    "IntervalTimeConvention",
    "LineageState",
    "MissingnessReason",
    "NormalizationQualityFlag",
    "NormalizationStatus",
    "PayoffType",
    "QuarantineReason",
    "QualityDimensionState",
    "TimestampPrecision",
]


class _StrEnum(str, Enum):
    """Deterministic string-valued enum base (values equal member names)."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class PayoffType(_StrEnum):
    """Economic payoff semantics (bloc_05/01 §3; bloc_05/07 F5).

    Frozen set: ``LINEAR``, ``INVERSE``, ``QUANTO``, ``SPOT``, ``UNKNOWN``.

    ``QUANTO`` exists so a resolver can refuse to force an unfamiliar contract
    into linear/inverse semantics, and ``UNKNOWN`` is the fail-closed state
    (bloc_05/01 §3: unverified payoff semantics give ``payoff_type = UNKNOWN``
    and block normalization) rather than a best guess.

    This is deliberately NOT the pre-existing Bloc 1 ``ContractType``: that enum
    is LINEAR/INVERSE/QUANTO/OTHER and has no SPOT and no UNKNOWN, so reusing
    it would erase both the spot case and the fail-closed state.  The two answer
    different questions (construction vs. economic payoff) and stay separate.

    At B5-I01 this is a vocabulary only.  ``payoff_type`` is an attribute of
    ``ContractInstance`` (bloc_05/01 §2.5), which is B5-I02, so no envelope
    field carries it yet.
    """

    LINEAR = "LINEAR"
    INVERSE = "INVERSE"
    QUANTO = "QUANTO"
    SPOT = "SPOT"
    UNKNOWN = "UNKNOWN"


class NormalizationStatus(_StrEnum):
    """Row-level canonical observation status (bloc_05/03 §15; bloc_05/07 F3).

    Frozen set: ``NORMALIZED``, ``PARTIALLY_NORMALIZED``, ``NATIVE_ONLY``,
    ``BLOCKED_IDENTITY``, ``BLOCKED_TIME``, ``BLOCKED_SEMANTICS``,
    ``BLOCKED_CONVERSION``, ``QUARANTINED``.

    A ``NATIVE_ONLY`` row is retained evidence that is excluded from
    cross-provider analysis -- retaining it is not the same as verifying it.

    The four ``BLOCKED_*`` members keep the frozen doc 03 §15 spelling.  The
    ``*_BLOCKED`` spelling of the same four concepts belongs to
    :class:`MissingnessReason` (bloc_05/05 §12) and is preserved there; see
    :data:`BLOCKED_STATUS_MISSINGNESS_REASON`.
    """

    NORMALIZED = "NORMALIZED"
    PARTIALLY_NORMALIZED = "PARTIALLY_NORMALIZED"
    NATIVE_ONLY = "NATIVE_ONLY"
    BLOCKED_IDENTITY = "BLOCKED_IDENTITY"
    BLOCKED_TIME = "BLOCKED_TIME"
    BLOCKED_SEMANTICS = "BLOCKED_SEMANTICS"
    BLOCKED_CONVERSION = "BLOCKED_CONVERSION"
    QUARANTINED = "QUARANTINED"


class MissingnessReason(_StrEnum):
    """Typed T1 missingness (bloc_05/05 §12; bloc_05/07 F13).

    Frozen set of 13 members.  Missingness is a *typed cause*, never a bool and
    never a numeric zero: bloc_05/03 §14 and bloc_05/05 §9 both require that a
    missing payload stay distinguishable from a verified economic ``0``.

    This deliberately does NOT reuse the accepted Bloc 1 ``MissingReason`` or
    the probe-layer ``CapabilityMissingness``.  Those describe why a *fetch*
    produced nothing; these describe why a *normalized value* is absent, which
    includes the four normalization-owned blocking causes
    (``IDENTITY_BLOCKED`` .. ``CONVERSION_BLOCKED``) that neither upstream
    vocabulary has.  The upstream vocabularies are untouched and remain
    reachable; the mapping between them is a later-stage concern, not an I01
    behaviour.
    """

    NOT_REPORTED = "NOT_REPORTED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    NOT_YET_LISTED = "NOT_YET_LISTED"
    DELISTED = "DELISTED"
    HISTORY_UNAVAILABLE = "HISTORY_UNAVAILABLE"
    PROVIDER_EMPTY = "PROVIDER_EMPTY"
    ACCESS_BLOCKED = "ACCESS_BLOCKED"
    SOURCE_GAP = "SOURCE_GAP"
    IDENTITY_BLOCKED = "IDENTITY_BLOCKED"
    TIME_BLOCKED = "TIME_BLOCKED"
    SEMANTICS_BLOCKED = "SEMANTICS_BLOCKED"
    CONVERSION_BLOCKED = "CONVERSION_BLOCKED"
    QUARANTINED = "QUARANTINED"


class NormalizationQualityFlag(_StrEnum):
    """Generic row-level quality flags for T1 (union of three frozen lists).

    Union of bloc_05/05 §11 (the canonical T1 list) with bloc_05/01 §14 (identity
    flags) and bloc_05/02 §16 (time flags) -- 36 members in total.  doc 05 §11
    says "minimum", and its 4 identity + 4 time members are strict subsets of
    docs 01/02, so keeping the supersets adds information and removes none.

    **Declaration order is canonical.**  It is the doc 05 §11 order first (the
    T1 authority), then the additive doc 01 §14 members, then the additive doc
    02 §16 members, each group in its own document order.  ``T1BaseEnvelope``
    requires ``quality_flags`` to arrive in exactly this order with no
    duplicates, so a serialized envelope cannot depend on caller's iteration
    order.

    Sensor-family-specific blocking errors (bloc_05/04 §16 -- aggressor side,
    OI unit, funding interval, ...) are deliberately absent: adding them to a
    generic base vocabulary would be premature sensor normalization (B5-I10..I15).
    """

    # --- bloc_05/05 §11 canonical T1 flags (24) ---
    IDENTITY_ALIAS_USED = "IDENTITY_ALIAS_USED"
    IDENTITY_LIFECYCLE_BOUNDARY = "IDENTITY_LIFECYCLE_BOUNDARY"
    IDENTITY_AMBIGUOUS = "IDENTITY_AMBIGUOUS"
    IDENTITY_TERMS_UNVERIFIED = "IDENTITY_TERMS_UNVERIFIED"
    TIME_SEMANTICS_UNVERIFIED = "TIME_SEMANTICS_UNVERIFIED"
    TIME_ARCHIVE_RECONSTRUCTION = "TIME_ARCHIVE_RECONSTRUCTION"
    TIME_MARKET_AVAILABILITY_UNKNOWN = "TIME_MARKET_AVAILABILITY_UNKNOWN"
    PIT_REVISION_UNCERTAIN = "PIT_REVISION_UNCERTAIN"
    SEMANTICS_UNVERIFIED = "SEMANTICS_UNVERIFIED"
    UNIT_NATIVE_ONLY = "UNIT_NATIVE_ONLY"
    UNIT_CONVERSION_BLOCKED = "UNIT_CONVERSION_BLOCKED"
    STABLECOIN_CONVERSION_UNAVAILABLE = "STABLECOIN_CONVERSION_UNAVAILABLE"
    REFERENCE_PRICE_UNAVAILABLE = "REFERENCE_PRICE_UNAVAILABLE"
    DUPLICATE_CONFIRMED = "DUPLICATE_CONFIRMED"
    DUPLICATE_CANDIDATE = "DUPLICATE_CANDIDATE"
    REVISION_PRESENT = "REVISION_PRESENT"
    SOURCE_DISAGREEMENT = "SOURCE_DISAGREEMENT"
    NO_SAFE_DEDUPE_KEY = "NO_SAFE_DEDUPE_KEY"
    BOOK_SEQUENCE_GAP = "BOOK_SEQUENCE_GAP"
    BOOK_PARTIAL_ONLY = "BOOK_PARTIAL_ONLY"
    BOOK_DEPTH_UNKNOWN = "BOOK_DEPTH_UNKNOWN"
    LINEAGE_COMPLETE = "LINEAGE_COMPLETE"
    LINEAGE_PARTIAL = "LINEAGE_PARTIAL"
    LINEAGE_BROKEN = "LINEAGE_BROKEN"
    # --- additive bloc_05/01 §14 identity flags (6) ---
    IDENTITY_SYMBOL_REUSED = "IDENTITY_SYMBOL_REUSED"
    IDENTITY_RELISTED = "IDENTITY_RELISTED"
    IDENTITY_CURRENT_METADATA_BACKCAST_RISK = "IDENTITY_CURRENT_METADATA_BACKCAST_RISK"
    IDENTITY_PROVIDER_ID_MISSING = "IDENTITY_PROVIDER_ID_MISSING"
    IDENTITY_MANUAL_OVERRIDE = "IDENTITY_MANUAL_OVERRIDE"
    IDENTITY_STABLECOIN_DISTINCT = "IDENTITY_STABLECOIN_DISTINCT"
    # --- additive bloc_05/02 §16 time flags (6) ---
    TIME_INTERVAL_BOUNDARY_UNVERIFIED = "TIME_INTERVAL_BOUNDARY_UNVERIFIED"
    TIME_CLOCK_SKEW = "TIME_CLOCK_SKEW"
    TIME_PRECISION_COARSE = "TIME_PRECISION_COARSE"
    TIME_SEQUENCE_MISSING = "TIME_SEQUENCE_MISSING"
    PIT_LATE_CORRECTION = "PIT_LATE_CORRECTION"
    PIT_PROVIDER_BACKFILL = "PIT_PROVIDER_BACKFILL"


class QualityDimensionState(_StrEnum):
    """Per-dimension T1 quality state (bloc_05/05 §10; bloc_05/07 §6).

    Frozen set: ``VERIFIED``, ``ACCEPTABLE_WITH_FLAGS``, ``PARTIAL``,
    ``UNKNOWN``, ``BLOCKED``, ``QUARANTINED``.

    Quality belongs to dimensions, not to one magical score (bloc_05/05 §10), so
    this enum is applied per dimension by :class:`~crypto_sensor_fabric.
    normalization.models.T1Quality` and is never aggregated here -- deriving
    operational scores is Bloc 6, which may read the component truth but must
    not overwrite it.

    ``UNKNOWN`` is a real state, not a placeholder for an undeclared value:
    "not determined" and "declared healthy" are different answers, and the base
    layer refuses to guess between them.
    """

    VERIFIED = "VERIFIED"
    ACCEPTABLE_WITH_FLAGS = "ACCEPTABLE_WITH_FLAGS"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    BLOCKED = "BLOCKED"
    QUARANTINED = "QUARANTINED"


class LineageState(_StrEnum):
    """Completeness of the T1 -> T0 evidence chain (bloc_05/05 §3, §11, §23).

    Frozen set: ``LINEAGE_COMPLETE``, ``LINEAGE_PARTIAL``, ``LINEAGE_BROKEN``.

    ``LINEAGE_BROKEN`` is blocking (bloc_05/05 §11) and therefore a member of
    :data:`BLOCKING_QUALITY_FLAGS`.  The same three names are also flags in
    bloc_05/05 §11; both are kept, and ``T1BaseEnvelope`` requires the state and
    the matching flag to agree so the two cannot drift apart.
    """

    LINEAGE_COMPLETE = "LINEAGE_COMPLETE"
    LINEAGE_PARTIAL = "LINEAGE_PARTIAL"
    LINEAGE_BROKEN = "LINEAGE_BROKEN"


class QuarantineReason(_StrEnum):
    """Typed quarantine causes (bloc_05/05 §20).

    Frozen set, one member per cause the document enumerates.  Quarantine is
    retention, not deletion (bloc_05/05 §20), and it is *reasoned*: a
    ``QUARANTINED`` row without a cause would erase the reason the row was
    pulled out of the canonical set, so the base layer requires one.

    Quarantine STORAGE (holding quarantined rows out of canonical queries) is
    B5-I18 and is deliberately not implemented here.
    """

    SCHEMA_FAILURE = "SCHEMA_FAILURE"
    IDENTITY_AMBIGUOUS = "IDENTITY_AMBIGUOUS"
    LINEAGE_BREAK = "LINEAGE_BREAK"
    IMPOSSIBLE_UNITS = "IMPOSSIBLE_UNITS"
    INVALID_SIDE_MAPPING = "INVALID_SIDE_MAPPING"
    BOOK_SEQUENCE_CORRUPTION = "BOOK_SEQUENCE_CORRUPTION"
    SOURCE_REVISION_CONFLICT = "SOURCE_REVISION_CONFLICT"


class IntervalTimeConvention(_StrEnum):
    """Interval boundary semantics (bloc_05/02 §7; bloc_05/07 F8).

    Frozen set: ``LEFT_CLOSED_RIGHT_OPEN``, ``LEFT_OPEN_RIGHT_CLOSED``,
    ``PROVIDER_NATIVE_UNKNOWN``, ``POINT_SAMPLE``.

    Exists because bloc_05/02 §7 forbids guessing whether a timestamp like
    ``12:00`` means a window starting, a window ending, or a snapshot sampled at
    that instant.  It is a vocabulary: the provider time-semantics REGISTRY
    that populates it is B5-I05.
    """

    LEFT_CLOSED_RIGHT_OPEN = "LEFT_CLOSED_RIGHT_OPEN"
    LEFT_OPEN_RIGHT_CLOSED = "LEFT_OPEN_RIGHT_CLOSED"
    PROVIDER_NATIVE_UNKNOWN = "PROVIDER_NATIVE_UNKNOWN"
    POINT_SAMPLE = "POINT_SAMPLE"


class AvailabilityBasis(_StrEnum):
    """Why a market-availability time is defensible (bloc_05/02 §5; F9, F10).

    Frozen set of 8 members.

    ``UNKNOWN`` and ``SYSTEM_ONLY_OBSERVED`` are the fail-closed members: they
    mean the row cannot be placed in strict historical market replay, which is
    why ``ObservationTimeEnvelope`` refuses ``market_available_at`` presented
    with an ``UNKNOWN`` basis.  ``HISTORICAL_ARCHIVE_RECONSTRUCTION`` is the
    labeled archive path, not a hidden one (bloc_05/02 F10).

    ``availability_confidence`` from the same paragraph is NOT implemented here:
    bloc_05/02 §5 names the field but never freezes its vocabulary, and
    inventing one would be an operator decision (see the type-scope matrix).
    """

    REALTIME_PUBLIC_EVENT = "REALTIME_PUBLIC_EVENT"
    REALTIME_PUBLIC_SNAPSHOT = "REALTIME_PUBLIC_SNAPSHOT"
    PUBLIC_INTERVAL_CLOSE = "PUBLIC_INTERVAL_CLOSE"
    DELAYED_PUBLICATION = "DELAYED_PUBLICATION"
    HISTORICAL_ARCHIVE_RECONSTRUCTION = "HISTORICAL_ARCHIVE_RECONSTRUCTION"
    PROVIDER_DECLARED_PUBLIC_TIME = "PROVIDER_DECLARED_PUBLIC_TIME"
    SYSTEM_ONLY_OBSERVED = "SYSTEM_ONLY_OBSERVED"
    UNKNOWN = "UNKNOWN"


class TimestampPrecision(_StrEnum):
    """Source timestamp precision, preserved verbatim (bloc_05/02 §8).

    Frozen set: ``SECOND``, ``MILLISECOND``, ``MICROSECOND``, ``NANOSECOND``,
    ``DATE_ONLY``, ``UNKNOWN``.

    bloc_05/02 §3 forbids fabricating microsecond ordering out of millisecond
    input.  Precision cannot be recovered from the value itself, so it has to be
    declared as evidence: ``DATE_ONLY`` timestamps that happen to render with a
    midnight component are still date-only.
    """

    SECOND = "SECOND"
    MILLISECOND = "MILLISECOND"
    MICROSECOND = "MICROSECOND"
    NANOSECOND = "NANOSECOND"
    DATE_ONLY = "DATE_ONLY"
    UNKNOWN = "UNKNOWN"


#: Canonical position of each flag in ``NormalizationQualityFlag`` declaration
#: order.  Used by the envelope to require canonical, duplicate-free ordering.
_FLAG_ORDER: Mapping[NormalizationQualityFlag, int] = MappingProxyType(
    {flag: index for index, flag in enumerate(NormalizationQualityFlag)}
)

#: Frozen correspondence between a blocked normalization status (bloc_05/03 §15)
#: and its typed missingness cause (bloc_05/05 §12).
#:
#: The plan spells the same four concepts in opposite order in the two
#: documents.  Keeping both vocabularies exactly as frozen and stating the
#: correspondence here means an envelope can require a real cause
#: (``BLOCKED_IDENTITY`` forces ``IDENTITY_BLOCKED``) instead of accepting a
#: generic "missing" bool, while neither vocabulary is renamed.
#:
#: Read-only by construction (``MappingProxyType``): this is frozen plan data,
#: not per-run state.
BLOCKED_STATUS_MISSINGNESS_REASON: Mapping[NormalizationStatus, MissingnessReason] = (
    MappingProxyType(
        {
            NormalizationStatus.BLOCKED_IDENTITY: MissingnessReason.IDENTITY_BLOCKED,
            NormalizationStatus.BLOCKED_TIME: MissingnessReason.TIME_BLOCKED,
            NormalizationStatus.BLOCKED_SEMANTICS: MissingnessReason.SEMANTICS_BLOCKED,
            NormalizationStatus.BLOCKED_CONVERSION: MissingnessReason.CONVERSION_BLOCKED,
        }
    )
)

#: Flags each of which a frozen document ties to a FAILED gate, so a row
#: carrying one cannot simultaneously claim a verified canonical status.
#:
#: Membership is minimal and each entry has an explicit citation, because a
#: blocking set is a claim about evidence and a convenient one is worthless:
#:
#: * ``IDENTITY_AMBIGUOUS`` / ``IDENTITY_TERMS_UNVERIFIED`` -- bloc_05/01 §9
#:   ("block T1 economic normalization"), bloc_05/06 §1 G1, bloc_05/07 F3;
#: * ``TIME_SEMANTICS_UNVERIFIED`` -- bloc_05/02 §18, bloc_05/06 §1 G2/G9;
#: * ``TIME_MARKET_AVAILABILITY_UNKNOWN`` -- bloc_05/02 §5 ("blocked from
#:   strict historical market replay");
#: * ``SEMANTICS_UNVERIFIED`` -- bloc_05/03 §13, bloc_05/06 §1 G9;
#: * ``UNIT_CONVERSION_BLOCKED`` / ``REFERENCE_PRICE_UNAVAILABLE`` --
#:   bloc_05/03 §8;
#: * ``STABLECOIN_CONVERSION_UNAVAILABLE`` -- bloc_05/03 §9, bloc_05/06 §1 G5;
#: * ``LINEAGE_BROKEN`` -- bloc_05/05 §11 ("``LINEAGE_BROKEN`` is blocking").
#:
#: Label-only flags are deliberately excluded.  ``TIME_ARCHIVE_RECONSTRUCTION``
#: labels evidence, ``NO_SAFE_DEDUPE_KEY`` and ``DUPLICATE_CANDIDATE`` warn about
#: dedupe, ``UNIT_NATIVE_ONLY`` states that no canonical unit was attempted:
#: none of them makes the row unverifiable.
BLOCKING_QUALITY_FLAGS: frozenset[NormalizationQualityFlag] = frozenset(
    {
        NormalizationQualityFlag.IDENTITY_AMBIGUOUS,
        NormalizationQualityFlag.IDENTITY_TERMS_UNVERIFIED,
        NormalizationQualityFlag.TIME_SEMANTICS_UNVERIFIED,
        NormalizationQualityFlag.TIME_MARKET_AVAILABILITY_UNKNOWN,
        NormalizationQualityFlag.SEMANTICS_UNVERIFIED,
        NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED,
        NormalizationQualityFlag.STABLECOIN_CONVERSION_UNAVAILABLE,
        NormalizationQualityFlag.REFERENCE_PRICE_UNAVAILABLE,
        NormalizationQualityFlag.LINEAGE_BROKEN,
    }
)