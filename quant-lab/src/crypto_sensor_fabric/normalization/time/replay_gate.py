"""SENSOR-B5-I05 - strict replay eligibility: admission, refusal, reasons.

Frozen authority: bloc_05/02 section 15 (the six conditions and the
``replay_eligibility`` field), section 5 (the blocking rule for ``UNKNOWN``
and unsupported ``SYSTEM_ONLY_OBSERVED`` rows), section 11 (revision-mode
compatibility), section 12 (``PIT_REVISION_UNCERTAIN``), section 16 (blocking
quality flags), section 18 rules 2/3/4/7, bloc_05/06 s1 G2 ("strict replay
blocks unknown availability") and section 13 of doc 06.

Shape of the answer: ONE outcome plus the reason that produced it, decided in
the frozen CONDITION ORDER of section 15 -- identity (1), timestamp semantics
(2), market availability (3), revision (4), lineage (5), blocking quality
flags (6) -- so the result never depends on argument order.  Blocking outcomes
win over the ``RETROSPECTIVE_ONLY`` qualification: a row cannot be
"retrospectively usable" AND blocked; it is blocked.

Refusal instead of invention: section 15's last condition blocks on ANY
frozen blocking flag, but the frozen ``ReplayEligibility`` vocabulary has no
member for the semantic/unit flags (those belong to B5-I08/I09/I10
checkpoints).  Rather than mint a seventh member or misfile the flag under a
timestamp/revision bucket, the gate raises
:class:`UnassessableReplayEvidence`.  A gate that cannot express its answer
must not pretend it has one.

Everything here is pure: no wall clock, no I/O, no mutation of the evidence
object, and every input is required -- an omitted field is a refusal, never a
permissive default.
"""

from __future__ import annotations

from ..enums import (
    BLOCKING_QUALITY_FLAGS,
    AvailabilityBasis,
    LineageState,
    NormalizationQualityFlag,
)
from .enums import ReplayEligibility
from .models import (
    AvailabilityConfidenceToken,
    EvidenceRef,
    TimeEvidenceBase,
    UtcTimestamp,
)
from .revision_policy import RevisionSelection

__all__ = [
    "ReplayEligibility",
    "ReplayEvaluation",
    "ReplayEvidence",
    "UnassessableReplayEvidence",
    "assess_replay_eligibility",
]


class UnassessableReplayEvidence(ValueError):
    """The frozen vocabulary cannot express this input (see module docstring)."""


#: Blocking flags with a bucket in the frozen vocabulary, grouped by the
#: section 15 condition they discharge.
_IDENTITY_FLAGS = frozenset(
    {
        NormalizationQualityFlag.IDENTITY_AMBIGUOUS,
        NormalizationQualityFlag.IDENTITY_TERMS_UNVERIFIED,
    }
)
_TIME_FLAGS = frozenset(
    {
        NormalizationQualityFlag.TIME_SEMANTICS_UNVERIFIED,
        NormalizationQualityFlag.TIME_MARKET_AVAILABILITY_UNKNOWN,
    }
)
_LINEAGE_FLAGS = frozenset({NormalizationQualityFlag.LINEAGE_BROKEN})

#: Blocking flags whose frozen outcome does not exist here.  Computed, not
#: hand-listed, so a future addition to BLOCKING_QUALITY_FLAGS cannot silently
#: acquire a made-up bucket.
_UNBUCKETED_FLAGS = (
    frozenset(BLOCKING_QUALITY_FLAGS) - _IDENTITY_FLAGS - _TIME_FLAGS - _LINEAGE_FLAGS
)


class ReplayEvidence(TimeEvidenceBase):
    """Everything section 15 needs, declared rather than inferred.

    The pairing of section 5 is enforced here as a USE-time rule: basis and
    confidence may each be ``None`` on a record that has not been assessed
    yet, but the gate treats either absence as an unplaceable claim and
    blocks.  ``availability_confidence`` is an opaque token (section 5 freezes
    no vocabulary for it) and may never be a number.
    """

    identity_pit_resolved: bool
    timestamp_semantics_verified: bool
    source_evidence_refs: tuple[EvidenceRef, ...]
    availability_basis: AvailabilityBasis | None
    availability_confidence: AvailabilityConfidenceToken | None
    market_available_at: UtcTimestamp | None
    interval_complete: bool
    revision: RevisionSelection | None
    lineage: LineageState
    quality_flags: tuple[NormalizationQualityFlag, ...]

    # ``frozen`` + extra=forbid come from TimeEvidenceBase.


class ReplayEvaluation(TimeEvidenceBase):
    """The outcome and the frozen clause that produced it."""

    eligibility: ReplayEligibility
    reasons: tuple[str, ...]


def assess_replay_eligibility(evidence: ReplayEvidence) -> ReplayEvaluation:
    """Evaluate section 15's six conditions in their frozen order.

    Pure and deterministic: same evidence, same outcome, same reason.
    """
    unbucketed = [
        flag.value for flag in evidence.quality_flags if flag in _UNBUCKETED_FLAGS
    ]
    if unbucketed:
        raise UnassessableReplayEvidence(
            "blocking quality flag(s) "
            + ", ".join(sorted(unbucketed))
            + " have no member in the frozen ReplayEligibility vocabulary "
            "(bloc_05/02 section 15); inventing a seventh member is an "
            "operator decision, so the gate refuses"
        )

    flags = set(evidence.quality_flags)

    if not evidence.identity_pit_resolved:
        return ReplayEvaluation(
            eligibility=ReplayEligibility.BLOCKED_IDENTITY,
            reasons=(
                "bloc_05/02 section 15(1): identity is not PIT-resolved",
            ),
        )

    identity_hits = sorted(flag.value for flag in flags & _IDENTITY_FLAGS)
    if identity_hits:
        return ReplayEvaluation(
            eligibility=ReplayEligibility.BLOCKED_IDENTITY,
            reasons=(
                "bloc_05/02 section 15(6): blocking quality flag "
                + ", ".join(identity_hits),
            ),
        )

    if not evidence.timestamp_semantics_verified:
        return ReplayEvaluation(
            eligibility=ReplayEligibility.BLOCKED_TIMESTAMP,
            reasons=(
                "bloc_05/02 section 15(2): timestamp semantics are not verified",
            ),
        )

    if not evidence.source_evidence_refs:
        return ReplayEvaluation(
            eligibility=ReplayEligibility.BLOCKED_TIMESTAMP,
            reasons=(
                "bloc_05/02 section 15(2): declared timestamp semantics carry "
                "no source evidence",
            ),
        )

    basis = evidence.availability_basis
    if basis in (None, AvailabilityBasis.UNKNOWN):
        return ReplayEvaluation(
            eligibility=ReplayEligibility.BLOCKED_TIMESTAMP,
            reasons=(
                "bloc_05/02 section 5: availability basis is missing or UNKNOWN, "
                "so the row cannot be placed in market time",
            ),
        )
    if basis is AvailabilityBasis.SYSTEM_ONLY_OBSERVED:
        return ReplayEvaluation(
            eligibility=ReplayEligibility.BLOCKED_TIMESTAMP,
            reasons=(
                "bloc_05/02 section 5: SYSTEM_ONLY_OBSERVED is unsupported for "
                "strict historical market replay",
            ),
        )
    if evidence.market_available_at is None:
        return ReplayEvaluation(
            eligibility=ReplayEligibility.BLOCKED_TIMESTAMP,
            reasons=(
                "bloc_05/02 section 5: a defensible basis without "
                "market_available_at is not an availability claim",
            ),
        )
    if evidence.availability_confidence is None:
        return ReplayEvaluation(
            eligibility=ReplayEligibility.BLOCKED_TIMESTAMP,
            reasons=(
                "bloc_05/02 section 5: availability_confidence is required "
                "beside availability_basis on every replay-relevant row",
            ),
        )

    if not evidence.interval_complete:
        return ReplayEvaluation(
            eligibility=ReplayEligibility.BLOCKED_TIMESTAMP,
            reasons=(
                "bloc_05/02 section 18 rule 2: the interval is not complete, "
                "so its value is not yet justified",
            ),
        )

    time_hits = sorted(flag.value for flag in flags & _TIME_FLAGS)
    if time_hits:
        return ReplayEvaluation(
            eligibility=ReplayEligibility.BLOCKED_TIMESTAMP,
            reasons=(
                "bloc_05/02 section 15(6): blocking quality flag "
                + ", ".join(time_hits),
            ),
        )

    revision = evidence.revision
    if revision is None:
        return ReplayEvaluation(
            eligibility=ReplayEligibility.BLOCKED_REVISION,
            reasons=(
                "bloc_05/02 section 15(4): no revision evaluation was supplied, "
                "so cutoff compatibility is unproven",
            ),
        )
    if revision.pit_uncertain:
        return ReplayEvaluation(
            eligibility=ReplayEligibility.BLOCKED_REVISION,
            reasons=(
                "bloc_05/02 section 12: PIT_REVISION_UNCERTAIN -- the original "
                "revision was not available by the replay cutoff",
            ),
        )

    if evidence.lineage is LineageState.LINEAGE_BROKEN:
        return ReplayEvaluation(
            eligibility=ReplayEligibility.BLOCKED_LINEAGE,
            reasons=("bloc_05/02 section 15(5): lineage is broken",),
        )
    lineage_hits = sorted(flag.value for flag in flags & _LINEAGE_FLAGS)
    if lineage_hits:
        return ReplayEvaluation(
            eligibility=ReplayEligibility.BLOCKED_LINEAGE,
            reasons=(
                "bloc_05/02 section 15(6): blocking quality flag "
                + ", ".join(lineage_hits),
            ),
        )

    if not revision.pit_safe:
        return ReplayEvaluation(
            eligibility=ReplayEligibility.RETROSPECTIVE_ONLY,
            reasons=(
                "bloc_05/02 section 11: revision mode "
                + revision.mode.value
                + " is not automatically PIT-safe, so the row is admissible "
                "only in an explicitly retrospective run",
            ),
        )

    return ReplayEvaluation(
        eligibility=ReplayEligibility.ELIGIBLE,
        reasons=("bloc_05/02 section 15: all six conditions satisfied",),
    )
