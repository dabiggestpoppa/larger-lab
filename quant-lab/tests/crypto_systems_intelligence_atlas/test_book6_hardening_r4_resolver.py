"""Book 6 GAP-7 RUNG 2 — resolve_current authority resolution.

The ratified resolver order (clarification v0.3 §8) now runs end to end for
every record, with no authority-bearing early return:

    1 registered lookup     2 lineage validity   3 terminality
    4 definition lookup     5 structural         6 methodology
    7 source_claim_refs != ()                    8 cited claims current
    9 return record

Covered here: the gates refuse with their OWN reason, NV-B holds uniformly
across every non-value-bearing state, terminality is permanent, status is
never consulted, and fail-closed scope stays PER_RECORD.
"""

from __future__ import annotations

import pytest

from crypto_systems_intelligence_atlas.book6_grammar import (
    MissingnessState,
    ObservationStatus,
    RestatementReason,
    VALUE_BEARING_MISSINGNESS,
)
from crypto_systems_intelligence_atlas.book6_registry import (
    Book6CurrentnessError,
    CurrentnessRefusal,
)
from crypto_systems_intelligence_atlas.book6_support import (
    CLAIM_ID,
    build_engine,
    decay_claim,
    definition,
    register_definition,
    register_measurement,
    windowed_observation,
)

METRIC = "m:resolver"
REASON = RestatementReason.INDEXER_CORRECTION
NON_VALUE_STATES = [s for s in MissingnessState if s not in VALUE_BEARING_MISSINGNESS]


def _engine(*claims):
    engine, *_ = build_engine(*(claims or (CLAIM_ID,)))
    register_definition(engine, definition(METRIC))
    return engine


def _obs(mid, *, supersedes=None, status=ObservationStatus.OBSERVED,
         claim_refs=(CLAIM_ID,), missingness=MissingnessState.OBSERVED, value=1.0):
    return windowed_observation(
        mid,
        METRIC,
        value=value,
        missingness=missingness,
        claim_refs=claim_refs,
        supersedes=supersedes,
        restatement_reason=REASON if supersedes else None,
        status=status,
    )


def _reason(engine, mid) -> CurrentnessRefusal:
    with pytest.raises(Book6CurrentnessError) as excinfo:
        engine.registry.resolve_current(mid)
    return excinfo.value.reason


# -- terminality gate (TERM-2, TERM-3) --------------------------------------


def test_terminal_record_resolves() -> None:
    engine = _engine()
    register_measurement(engine, _obs("A"))
    assert engine.registry.resolve_current("A").measurement_id == "A"


def test_superseded_record_is_refused_at_terminality() -> None:
    engine = _engine()
    register_measurement(engine, _obs("A"))
    register_measurement(engine, _obs("B", supersedes="A"))
    assert _reason(engine, "A") is CurrentnessRefusal.NOT_TERMINAL
    assert engine.registry.resolve_current("B").measurement_id == "B"


def test_superseded_predecessor_never_resurrects() -> None:
    """TERM-5: losing the successor's authority does not restore the predecessor.

    A naive repair that answered "is this current?" from the record's OWN gates
    would resurrect A the moment B decayed. The correct reading is that A lost
    authority when B was registered, and losing B's authority restores nothing.
    """

    engine, claim_store, evidence_store, service = build_engine(CLAIM_ID, "claim:other")
    register_definition(engine, definition(METRIC))
    register_measurement(engine, _obs("A"))
    register_measurement(engine, _obs("B", supersedes="A", claim_refs=("claim:other",)))
    assert _reason(engine, "A") is CurrentnessRefusal.NOT_TERMINAL

    # B loses its Book 2 authority.
    decay_claim(service, claim_store, "claim:other", "STALE")
    assert _reason(engine, "B") is CurrentnessRefusal.SOURCE_CLAIMS_STALE

    # A stays non-terminal. No resurrection.
    assert _reason(engine, "A") is CurrentnessRefusal.NOT_TERMINAL
    assert engine.registry.is_authoritative_now("A") is False


# -- lineage gate (TERM-4) and its PER_RECORD scope (TERM-6) -----------------


def test_branched_record_is_refused_at_lineage() -> None:
    engine = _engine()
    register_measurement(engine, _obs("A"))
    register_measurement(engine, _obs("B", supersedes="A"))
    register_measurement(engine, _obs("C", supersedes="A"))
    assert _reason(engine, "A") is CurrentnessRefusal.LINEAGE_INVALID


def test_branch_successors_still_resolve_current() -> None:
    """TERM-6, the paired negative of TERM-4.

    Refusing B and C here would be component-wide fail-closed. Ratified scope is
    PER_RECORD (BOOK6-GAP7-SUCCESSOR-CURRENTNESS-v0.1).
    """

    engine = _engine()
    register_measurement(engine, _obs("A"))
    register_measurement(engine, _obs("B", supersedes="A"))
    register_measurement(engine, _obs("C", supersedes="A"))
    assert engine.registry.resolve_current("B").measurement_id == "B"
    assert engine.registry.resolve_current("C").measurement_id == "C"
    assert engine.registry.is_authoritative_now("B") is True
    assert engine.registry.is_authoritative_now("C") is True


def test_refused_record_remains_registered_history() -> None:
    engine = _engine()
    register_measurement(engine, _obs("A"))
    register_measurement(engine, _obs("B", supersedes="A"))
    register_measurement(engine, _obs("C", supersedes="A"))
    assert engine.registry.registered_measurement("A").measurement_id == "A"
    assert engine.registry.is_authoritative_now("A") is False


# -- NV-B: uniform, no per-state split (NV-8) --------------------------------


@pytest.mark.parametrize("state", NON_VALUE_STATES, ids=lambda s: s.value)
def test_every_non_value_state_without_sources_is_not_current(state) -> None:
    """NV-8: one rule for all eight, not a per-state split (NV-C not adopted)."""

    engine = _engine()
    register_measurement(
        engine,
        windowed_observation(
            "obs:na",
            METRIC,
            value=None,
            missingness=state,
            claim_refs=(),
            unit=None,
        ),
    )
    # constructible, registrable, queryable
    assert engine.registry.registered_measurement("obs:na").measurement_id == "obs:na"
    # but never current-authoritative
    assert _reason(engine, "obs:na") is CurrentnessRefusal.SOURCE_CLAIMS_ABSENT


def test_non_value_state_with_sources_is_not_current_for_a_different_reason() -> None:
    """A sourced absence clears step 7 and is refused at the absence read."""

    engine = _engine()
    register_measurement(
        engine,
        windowed_observation(
            "obs:na", METRIC, value=None, missingness=MissingnessState.NOT_COLLECTED,
            claim_refs=(CLAIM_ID,), unit=None,
        ),
    )
    # passes NV-B: resolution succeeds; the value read is what refuses
    assert engine.registry.resolve_current("obs:na").measurement_id == "obs:na"


# -- B-STRICT: status is never consulted -------------------------------------


@pytest.mark.parametrize("status", list(ObservationStatus))
def test_status_alone_does_not_change_the_verdict(status: ObservationStatus) -> None:
    """CURR-S1: identical on every authority-bearing fact except status."""

    engine = _engine()
    register_measurement(engine, _obs("R"))
    register_measurement(engine, _obs("X", supersedes="R", status=status))
    # same verdict whatever the status
    assert engine.registry.resolve_current("X").measurement_id == "X"
    assert engine.registry.is_authoritative_now("X") is True


@pytest.mark.parametrize("status", list(ObservationStatus))
def test_superseded_status_record_is_refused_at_terminality_not_status(
    status: ObservationStatus,
) -> None:
    """CURR-S2: a SUPERSEDED-status record that is non-terminal.

    The falsifier that keeps CURR-S1 honest. Without it, a resolver could satisfy
    CURR-S1 by refusing everything carrying SUPERSEDED.
    """

    engine = _engine()
    register_measurement(engine, _obs("R"))
    register_measurement(engine, _obs("X", supersedes="R", status=status))
    register_measurement(engine, _obs("Y", supersedes="X", status=status))
    assert _reason(engine, "X") is CurrentnessRefusal.NOT_TERMINAL


def test_stale_claim_refusal_is_not_a_status_refusal() -> None:
    """CURR-S3: a SUPERSEDED-status record whose cited claim decayed."""

    engine, claim_store, evidence_store, service = build_engine(CLAIM_ID, "claim:stale")
    register_definition(engine, definition(METRIC))
    register_measurement(engine, _obs("R"))
    register_measurement(
        engine,
        _obs(
            "X",
            supersedes="R",
            status=ObservationStatus.SUPERSEDED,
            claim_refs=("claim:stale",),
        ),
    )
    decay_claim(service, claim_store, "claim:stale", "STALE")
    assert _reason(engine, "X") is CurrentnessRefusal.SOURCE_CLAIMS_STALE


def test_is_authoritative_now_inherits_the_resolver() -> None:
    """The delegated check follows the central fix with no separate edit."""

    engine = _engine()
    register_measurement(engine, _obs("A"))
    assert engine.registry.is_authoritative_now("A") is True
    register_measurement(engine, _obs("B", supersedes="A"))
    assert engine.registry.is_authoritative_now("A") is False


def test_unknown_measurement_refuses_at_step_one() -> None:
    engine = _engine()
    assert _reason(engine, "nope") is CurrentnessRefusal.NOT_REGISTERED


def test_refusal_vocabulary_is_closed_and_status_free() -> None:
    """No refusal reason reads ObservationStatus, and none names registration.

    The closed vocabulary is what makes "status is not authority" checkable
    rather than merely asserted: there is no status-flavoured reason to hide
    behind, and no registration reason to smuggle a write-time policy in on.
    """

    reasons = {r.value for r in CurrentnessRefusal}
    assert not any("STATUS" in r or "OBSERVATION" in r for r in reasons)
    assert not any("REGISTR" in r for r in reasons)
    assert reasons == {
        "NOT_REGISTERED",
        "LINEAGE_INVALID",
        "NOT_TERMINAL",
        "DEFINITION_UNKNOWN",
        "STRUCTURE",
        "METHODOLOGY_CURRENT",
        "SOURCE_CLAIMS_ABSENT",
        "SOURCE_CLAIMS_STALE",
    }
