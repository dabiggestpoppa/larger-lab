"""SENSOR-B5-I05 - RED-first strict replay eligibility gate.

Frozen authority: bloc_05/02 s15 (the six admission conditions and the
``replay_eligibility`` field), s5 (blocking rule for UNKNOWN and unsupported
SYSTEM_ONLY_OBSERVED rows), s11 (revision-mode compatibility), s12
(PIT_REVISION_UNCERTAIN), s18 (invariants), bloc_05/06 s1 G2 ("strict replay
blocks unknown availability") and s13.

Precedence is the frozen condition ORDER of s15 -- identity, timestamp
semantics, availability, revision, lineage, blocking quality flag -- so the
first failing condition decides the outcome and the result is deterministic.
Blocking outcomes win over the ``RETROSPECTIVE_ONLY`` qualification.

Where the frozen ``ReplayEligibility`` vocabulary has no member for a blocking
flag (semantic/unit flags owned by later checkpoints), the gate REFUSES rather
than mislabeling: inventing a seventh member is an operator decision.

OFFLINE.  No network, no wall clock, no filesystem writes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from crypto_sensor_fabric.normalization.enums import (
    AvailabilityBasis,
    LineageState,
    NormalizationQualityFlag,
)
from crypto_sensor_fabric.normalization.time import (
    ReplayEligibility,
    ReplayEvidence,
    RevisionMode,
    RevisionPolicyCatalog,
    RevisionStatus,
    UnassessableReplayEvidence,
    assess_replay_eligibility,
    parse_revision_policies_yaml,
    select_revisions,
)

UTC = timezone.utc
_HERE = Path(__file__).resolve().parent
_QUANT_LAB = _HERE.parents[2]
CONFIG = _QUANT_LAB / "config" / "crypto_sensor_fabric" / "revision_policies.yaml"

NOW = datetime(2024, 6, 1, hour=12, minute=5, tzinfo=UTC)
KNOWN_2022 = datetime(2022, 5, 12, hour=8, minute=0, tzinfo=UTC)
CUTOFF_2022 = datetime(2022, 5, 12, hour=8, minute=0, tzinfo=UTC)
KNOWN_2025 = datetime(2025, 3, 3, hour=10, tzinfo=UTC)


def _catalog() -> RevisionPolicyCatalog:
    return parse_revision_policies_yaml(CONFIG.read_text(encoding="utf-8"))


def _selection(mode: RevisionMode, cutoff: datetime = CUTOFF_2022):
    from crypto_sensor_fabric.normalization.time import RevisionRecord

    original = RevisionRecord(
        source_revision_id="rev-oi-original",
        normalization_generation=1,
        supersedes_t1_record_id=None,
        revision_status=RevisionStatus.ORIGINAL,
        known_from=KNOWN_2022,
        known_to=None,
    )
    correction = RevisionRecord(
        source_revision_id="rev-oi-corrected",
        normalization_generation=2,
        supersedes_t1_record_id="rev-oi-original",
        revision_status=RevisionStatus.PROVIDER_CORRECTED,
        known_from=KNOWN_2025,
        known_to=None,
    )
    return select_revisions((original, correction), _catalog().policy_for(mode), cutoff)


def _evidence(**overrides: object) -> ReplayEvidence:
    payload: dict[str, object] = {
        "identity_pit_resolved": True,
        "timestamp_semantics_verified": True,
        "source_evidence_refs": ("provider-docs:synth-a-public-feed",),
        "availability_basis": AvailabilityBasis.PUBLIC_INTERVAL_CLOSE,
        "availability_confidence": "EVIDENCE_BACKED_DECLARATION",
        "market_available_at": NOW,
        "interval_complete": True,
        "revision": _selection(RevisionMode.AS_KNOWN_THEN),
        "lineage": LineageState.LINEAGE_COMPLETE,
        "quality_flags": (NormalizationQualityFlag.LINEAGE_COMPLETE,),
    }
    payload.update(overrides)
    return ReplayEvidence(**payload)  # type: ignore[arg-type]


def _assess(**overrides: object) -> ReplayEligibility:
    return assess_replay_eligibility(_evidence(**overrides)).eligibility


# ---------------------------------------------------------------------------
# Admission
# ---------------------------------------------------------------------------


def test_a_fully_evidenced_row_is_eligible() -> None:
    evaluation = assess_replay_eligibility(_evidence())
    assert evaluation.eligibility is ReplayEligibility.ELIGIBLE
    assert evaluation.reasons, "an outcome must always say why"


def test_every_gate_input_is_required_no_silent_defaults() -> None:
    with pytest.raises(ValueError):
        ReplayEvidence()  # type: ignore[call-arg]


def test_availability_confidence_may_not_be_a_number() -> None:
    """No fabricated numerics: confidence is declared evidence, not a score."""
    for value in ("0.9", "95", "1", "3.5"):
        with pytest.raises(ValueError):
            _evidence(availability_confidence=value)


def test_availability_confidence_may_not_be_blank() -> None:
    with pytest.raises(ValueError):
        _evidence(availability_confidence="   ")


def test_availability_confidence_is_optional_but_checked_at_use() -> None:
    """s5 pairs basis and confidence; absence blocks instead of defaulting."""
    assert _assess(availability_confidence=None) is ReplayEligibility.BLOCKED_TIMESTAMP


# ---------------------------------------------------------------------------
# Refusal paths, in the frozen s15 order
# ---------------------------------------------------------------------------


def test_unresolved_identity_blocks_first() -> None:
    evaluation = assess_replay_eligibility(
        _evidence(
            identity_pit_resolved=False,
            timestamp_semantics_verified=False,
            availability_basis=None,
        )
    )
    assert evaluation.eligibility is ReplayEligibility.BLOCKED_IDENTITY


def test_unverified_timestamp_semantics_block() -> None:
    assert _assess(timestamp_semantics_verified=False) is (
        ReplayEligibility.BLOCKED_TIMESTAMP
    )


def test_missing_source_evidence_blocks_as_unverified_semantics() -> None:
    assert _assess(source_evidence_refs=()) is ReplayEligibility.BLOCKED_TIMESTAMP


@pytest.mark.parametrize(
    "basis",
    [None, AvailabilityBasis.UNKNOWN, AvailabilityBasis.SYSTEM_ONLY_OBSERVED],
)
def test_unplaceable_availability_blocks_strict_replay(basis) -> None:
    """bloc_05/02 s5: UNKNOWN and unsupported SYSTEM_ONLY_OBSERVED are blocked."""
    assert _assess(availability_basis=basis) is ReplayEligibility.BLOCKED_TIMESTAMP


def test_missing_market_availability_time_blocks() -> None:
    assert _assess(market_available_at=None) is ReplayEligibility.BLOCKED_TIMESTAMP


def test_incomplete_interval_blocks() -> None:
    assert _assess(interval_complete=False) is ReplayEligibility.BLOCKED_TIMESTAMP


def test_missing_revision_evaluation_blocks() -> None:
    assert _assess(revision=None) is ReplayEligibility.BLOCKED_REVISION


def test_uncertain_pit_revision_blocks() -> None:
    """s12: PIT_REVISION_UNCERTAIN rows must not masquerade as contemporaneous."""
    uncertain = select_revisions(
        (), _catalog().policy_for(RevisionMode.AS_KNOWN_THEN), CUTOFF_2022
    )
    assert uncertain.pit_uncertain is True
    assert _assess(revision=uncertain) is ReplayEligibility.BLOCKED_REVISION


def test_latest_verified_is_retrospective_only_not_eligible() -> None:
    """F05-04: a verified retrospective correction is eligible only there."""
    evaluation = assess_replay_eligibility(
        _evidence(revision=_selection(RevisionMode.LATEST_VERIFIED))
    )
    assert evaluation.eligibility is ReplayEligibility.RETROSPECTIVE_ONLY


def test_broken_lineage_blocks() -> None:
    assert _assess(
        lineage=LineageState.LINEAGE_BROKEN,
        quality_flags=(NormalizationQualityFlag.LINEAGE_BROKEN,),
    ) is ReplayEligibility.BLOCKED_LINEAGE


def test_partial_lineage_is_flagged_but_not_blocking() -> None:
    assert _assess(
        lineage=LineageState.LINEAGE_PARTIAL,
        quality_flags=(NormalizationQualityFlag.LINEAGE_PARTIAL,),
    ) is ReplayEligibility.ELIGIBLE


@pytest.mark.parametrize(
    ("flag", "expected"),
    [
        (NormalizationQualityFlag.IDENTITY_AMBIGUOUS, ReplayEligibility.BLOCKED_IDENTITY),
        (
            NormalizationQualityFlag.IDENTITY_TERMS_UNVERIFIED,
            ReplayEligibility.BLOCKED_IDENTITY,
        ),
        (
            NormalizationQualityFlag.TIME_SEMANTICS_UNVERIFIED,
            ReplayEligibility.BLOCKED_TIMESTAMP,
        ),
        (
            NormalizationQualityFlag.TIME_MARKET_AVAILABILITY_UNKNOWN,
            ReplayEligibility.BLOCKED_TIMESTAMP,
        ),
        (NormalizationQualityFlag.LINEAGE_BROKEN, ReplayEligibility.BLOCKED_LINEAGE),
    ],
)
def test_blocking_flags_map_to_their_frozen_bucket(flag, expected) -> None:
    assert _assess(quality_flags=(flag,)) is expected


@pytest.mark.parametrize(
    "flag",
    [
        NormalizationQualityFlag.SEMANTICS_UNVERIFIED,
        NormalizationQualityFlag.UNIT_CONVERSION_BLOCKED,
        NormalizationQualityFlag.STABLECOIN_CONVERSION_UNAVAILABLE,
        NormalizationQualityFlag.REFERENCE_PRICE_UNAVAILABLE,
    ],
)
def test_blocking_flags_without_a_frozen_bucket_make_the_gate_refuse(flag) -> None:
    """No seventh ReplayEligibility member may be invented to fit a flag."""
    with pytest.raises(UnassessableReplayEvidence):
        assess_replay_eligibility(_evidence(quality_flags=(flag,)))


def test_label_only_flags_never_block() -> None:
    for flag in (
        NormalizationQualityFlag.TIME_ARCHIVE_RECONSTRUCTION,
        NormalizationQualityFlag.TIME_PRECISION_COARSE,
        NormalizationQualityFlag.PIT_LATE_CORRECTION,
        NormalizationQualityFlag.NO_SAFE_DEDUPE_KEY,
    ):
        assert _assess(quality_flags=(flag,)) is ReplayEligibility.ELIGIBLE, flag


def test_precedence_is_the_frozen_condition_order_not_input_order() -> None:
    evaluation = assess_replay_eligibility(
        _evidence(
            identity_pit_resolved=False,
            timestamp_semantics_verified=False,
            interval_complete=False,
            lineage=LineageState.LINEAGE_BROKEN,
        )
    )
    assert evaluation.eligibility is ReplayEligibility.BLOCKED_IDENTITY
    assert any("section 15(1)" in reason for reason in evaluation.reasons)


def test_every_refusal_reason_cites_a_frozen_clause() -> None:
    evaluation = assess_replay_eligibility(
        _evidence(availability_basis=AvailabilityBasis.UNKNOWN)
    )
    assert evaluation.eligibility is ReplayEligibility.BLOCKED_TIMESTAMP
    assert all("bloc_05/02" in reason for reason in evaluation.reasons)
    assert evaluation.reasons


def test_evaluation_is_immutable() -> None:
    evaluation = assess_replay_eligibility(_evidence())
    with pytest.raises(Exception):
        evaluation.eligibility = ReplayEligibility.BLOCKED_REVISION  # type: ignore[misc]


def test_gate_is_pure_and_repeatable() -> None:
    evidence = _evidence()
    first = assess_replay_eligibility(evidence)
    second = assess_replay_eligibility(evidence)
    assert first == second
    assert evidence.market_available_at == NOW
