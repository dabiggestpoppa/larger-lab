"""SENSOR-B5-I05 - the four frozen Bloc 5 time vocabularies (doc 02 sections 2/10/11/15).

Same freeze discipline as ``normalization.enums`` (B5-I01) and
``identity.enums`` (B5-I03): members are copied verbatim from the frozen
planning document named in each docstring, declaration order is canonical, and
adding a member is a plan change requiring operator review -- never a
convenience.

Exactly four NEW vocabularies belong to this checkpoint, because doc 02 names
four member sets that no earlier checkpoint owns:

* :class:`TimestampRole` -- the nine canonical timestamp fields (section 2/3);
* :class:`RevisionStatus` -- the six T1 revision statuses (section 10);
* :class:`RevisionMode` -- the six research revision modes (section 11);
* :class:`ReplayEligibility` -- the six strict-replay outcomes (section 15).

The other time vocabularies are deliberately NOT redeclared here.  They are
B5-I01-owned and are imported by the models that need them:
``AvailabilityBasis`` (section 5), ``TimestampPrecision`` (section 8),
``IntervalTimeConvention`` (section 7) and ``NormalizationQualityFlag``
(section 16) all live in ``crypto_sensor_fabric.normalization.enums``.
Redefining any of them would create two authorities for one frozen meaning.
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "RevisionMode",
    "RevisionStatus",
    "ReplayEligibility",
    "TimestampRole",
    "STRICT_REPLAY_ELIGIBLE",
]


class _StrEnum(str, Enum):
    """Deterministic string-valued enum base (values equal member names)."""

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.value


class TimestampRole(_StrEnum):
    """Which canonical clock a timestamp IS (bloc_05/02 section 2/3; F8).

    Exact frozen member set, in the section 2 declaration order.  The nine
    roles are the nine fields ``ObservationTimeEnvelope`` already carries, and
    ``TIMESTAMP_ROLE_FIELD`` (``models.py``) states that correspondence as
    frozen data so no role can be silently answered by another role's field.

    Section 2: null means "not applicable or not verified", never "same as
    another timestamp" -- so a role is a claim about MEANING, and a row may
    carry any subset of them.
    """

    SOURCE_EVENT_AT = "SOURCE_EVENT_AT"
    INTERVAL_START_AT = "INTERVAL_START_AT"
    INTERVAL_END_AT = "INTERVAL_END_AT"
    EFFECTIVE_AT = "EFFECTIVE_AT"
    PUBLISHED_AT = "PUBLISHED_AT"
    MARKET_AVAILABLE_AT = "MARKET_AVAILABLE_AT"
    OBSERVED_AT = "OBSERVED_AT"
    INGESTED_AT = "INGESTED_AT"
    NORMALIZED_AT = "NORMALIZED_AT"


class RevisionStatus(_StrEnum):
    """How a T1 observation relates to its predecessor (bloc_05/02 section 10).

    Exact frozen member set and order.  Section 10 forbids in-place overwrite
    of a prior T1 generation, so every status names a NEW generation rather
    than a mutation of an old one.  ``ORIGINAL`` versus the five later states
    is exactly the distinction section 12's ``PIT_REVISION_UNCERTAIN`` rule
    turns on: a replay that cannot select an ``ORIGINAL`` row cannot claim
    contemporaneous truth.
    """

    ORIGINAL = "ORIGINAL"
    PROVIDER_CORRECTED = "PROVIDER_CORRECTED"
    SOURCE_MUTATION_REPARSED = "SOURCE_MUTATION_REPARSED"
    NORMALIZATION_REBUILD = "NORMALIZATION_REBUILD"
    IDENTITY_REBUILD = "IDENTITY_REBUILD"
    SEMANTIC_REINTERPRETATION = "SEMANTIC_REINTERPRETATION"


class RevisionMode(_StrEnum):
    """Research/replay revision mode (bloc_05/02 section 11).

    Exact frozen member set and order.  Section 11 defines only the first two
    in prose, and this checkpoint implements exactly those two: the other four
    are declared (because the plan freezes their names) and REFUSED at
    selection time, because inventing their semantics would be B5-I07 work
    performed without authority.
    """

    AS_KNOWN_THEN = "AS_KNOWN_THEN"
    LATEST_VERIFIED = "LATEST_VERIFIED"
    FIRST_SEEN = "FIRST_SEEN"
    EXACT_REVISION = "EXACT_REVISION"
    ALL_REVISIONS = "ALL_REVISIONS"
    ERROR_ON_AMBIGUITY = "ERROR_ON_AMBIGUITY"


class ReplayEligibility(_StrEnum):
    """Strict-replay outcome of a T1 observation (bloc_05/02 section 15).

    Exact frozen member set and order.  There is no seventh member, and no
    member for semantic/unit blocking causes: the gate refuses an input whose
    blocking flag has no bucket in this vocabulary rather than inventing one
    (see ``replay_gate.UnassessableReplayEvidence``).
    """

    ELIGIBLE = "ELIGIBLE"
    RETROSPECTIVE_ONLY = "RETROSPECTIVE_ONLY"
    BLOCKED_TIMESTAMP = "BLOCKED_TIMESTAMP"
    BLOCKED_REVISION = "BLOCKED_REVISION"
    BLOCKED_IDENTITY = "BLOCKED_IDENTITY"
    BLOCKED_LINEAGE = "BLOCKED_LINEAGE"


#: The only outcome that places a row in strict historical market replay.
#: ``RETROSPECTIVE_ONLY`` is admissible solely in an explicitly retrospective
#: run, and the four ``BLOCKED_*`` outcomes are refusals (bloc_05/02 s5/s15).
STRICT_REPLAY_ELIGIBLE = frozenset({ReplayEligibility.ELIGIBLE})
