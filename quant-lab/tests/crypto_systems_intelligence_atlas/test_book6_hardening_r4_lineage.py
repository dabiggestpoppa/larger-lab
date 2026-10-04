"""Book 6 GAP-7 RUNG 1 — registered lineage facts.

GAP-7 ratified SUPERSESSION_CURRENTNESS_SOURCE as REGISTERED_LINEAGE_TERMINALITY.
This file covers the RUNG 1 machinery that reports those facts, BEFORE the
authority verdict is wired in at RUNG 2:

    direct_successors   the registered supersession edges
    lineage_is_valid    more than one direct successor => invalid  (TERM-4)
    is_terminal         no direct successor at all

Two things are asserted here that are easy to get wrong and expensive later:

    ObservationStatus is never consulted   (B-STRICT)
    scope is PER_RECORD                     (BOOK6-GAP7-SUCCESSOR-CURRENTNESS-v0.1)

Nothing in this file is an authority verdict. Authority arrives at RUNG 2.
"""

from __future__ import annotations

import pytest

from crypto_systems_intelligence_atlas.book6_grammar import (
    MissingnessState,
    ObservationStatus,
    RestatementReason,
)
from crypto_systems_intelligence_atlas.book6_registry import Book6RegistryError
from crypto_systems_intelligence_atlas.book6_support import (
    CLAIM_ID,
    build_engine,
    definition,
    register_definition,
    register_measurement,
    windowed_observation,
)

METRIC = "metric:lineage"
REASON = RestatementReason.INDEXER_CORRECTION


def _engine():
    engine, *_ = build_engine()
    register_definition(engine, definition(METRIC))
    return engine


def _obs(measurement_id, *, supersedes=None, status=ObservationStatus.OBSERVED,
         claim_refs=(CLAIM_ID,)):
    return windowed_observation(
        measurement_id,
        METRIC,
        value=1.0,
        missingness=MissingnessState.OBSERVED,
        claim_refs=claim_refs,
        supersedes=supersedes,
        restatement_reason=REASON if supersedes else None,
        status=status,
    )


# -- terminality (TERM-1) ----------------------------------------------------


def test_lone_measurement_is_terminal() -> None:
    engine = _engine()
    register_measurement(engine, _obs("A"))
    assert engine.registry.is_terminal("A") is True
    assert engine.registry.lineage_is_valid("A") is True
    assert engine.registry.direct_successors("A") == ()


def test_superseded_measurement_is_not_terminal() -> None:
    engine = _engine()
    register_measurement(engine, _obs("A"))
    register_measurement(engine, _obs("B", supersedes="A"))
    assert engine.registry.is_terminal("A") is False
    assert engine.registry.is_terminal("B") is True


def test_three_link_chain_terminality() -> None:
    """TERM-3: A <- B <- C leaves only C terminal."""

    engine = _engine()
    register_measurement(engine, _obs("A"))
    register_measurement(engine, _obs("B", supersedes="A"))
    register_measurement(engine, _obs("C", supersedes="B"))
    assert [m for m in "ABC" if engine.registry.is_terminal(m)] == ["C"]


# -- branching (TERM-4), and its PER_RECORD scope ---------------------------


def test_branched_lineage_is_invalid() -> None:
    engine = _engine()
    register_measurement(engine, _obs("A"))
    register_measurement(engine, _obs("B", supersedes="A"))
    register_measurement(engine, _obs("C", supersedes="A"))
    assert engine.registry.lineage_is_valid("A") is False


def test_successors_of_a_branch_are_unaffected() -> None:
    """TERM-6 groundwork: a branched predecessor does not condemn its successors.

    Ratified scope is PER_RECORD. Refusing B and C here would be component-wide
    fail-closed, which no ratification supplies.
    """

    engine = _engine()
    register_measurement(engine, _obs("A"))
    register_measurement(engine, _obs("B", supersedes="A"))
    register_measurement(engine, _obs("C", supersedes="A"))
    for successor in ("B", "C"):
        assert engine.registry.lineage_is_valid(successor) is True
        assert engine.registry.is_terminal(successor) is True


# -- registration behaviour is NOT changed ----------------------------------


def test_second_successor_registration_is_still_accepted() -> None:
    """The accepted kernel accepts branching; GAP-7 does not govern registration.

    This is a load-bearing negative. If this ever starts refusing, a registration
    policy has been invented without ratification.
    """

    engine = _engine()
    register_measurement(engine, _obs("A"))
    register_measurement(engine, _obs("B", supersedes="A"))
    register_measurement(engine, _obs("C", supersedes="A"))
    assert engine.registry.registered_measurement("C").measurement_id == "C"
    assert engine.registry.registered_measurement("B").measurement_id == "B"


def test_measurement_history_still_refuses_branching() -> None:
    """The pre-existing accessor refusal is preserved unchanged."""

    engine = _engine()
    register_measurement(engine, _obs("A"))
    register_measurement(engine, _obs("B", supersedes="A"))
    register_measurement(engine, _obs("C", supersedes="A"))
    with pytest.raises(Book6RegistryError):
        engine.registry.measurement_history("A")


# -- status is never consulted (B-STRICT) -----------------------------------


@pytest.mark.parametrize(
    ("status_a", "status_b", "status_c"),
    [
        (ObservationStatus.OBSERVED, ObservationStatus.OBSERVED, ObservationStatus.OBSERVED),
        (ObservationStatus.SUPERSEDED, ObservationStatus.OBSERVED, ObservationStatus.OBSERVED),
        (ObservationStatus.OBSERVED, ObservationStatus.SUPERSEDED, ObservationStatus.SUPERSEDED),
        (ObservationStatus.SUPERSEDED, ObservationStatus.SUPERSEDED, ObservationStatus.SUPERSEDED),
    ],
)
def test_status_permutation_does_not_change_lineage_facts(
    status_a: ObservationStatus,
    status_b: ObservationStatus,
    status_c: ObservationStatus,
) -> None:
    """All four status assignments, one structural fixture, one answer.

    ``Z`` exists so that ``A`` carries an outgoing supersession edge. Without it
    ``A`` is a root, and the accepted record validator refuses ``A.status =
    SUPERSEDED`` outright ("a SUPERSEDED observation must name the observation it
    superseded"). That is the deferred lifecycle incoherence, recorded out of
    GAP-7 scope in
    CSIA_BOOK_6_STATUS_VALIDATOR_LIFECYCLE_AMENDMENT_DEFERRED_v0.1.md.

    Giving ``A`` an incoming history keeps the permutation constructible without
    touching the validator, and changes nothing under test: terminality is a
    function of A's INCOMING edges, which status never touches.
    """

    engine = _engine()
    register_measurement(engine, _obs("Z"))
    register_measurement(engine, _obs("A", supersedes="Z", status=status_a))
    register_measurement(engine, _obs("B", supersedes="A", status=status_b))
    register_measurement(engine, _obs("C", supersedes="A", status=status_c))
    assert engine.registry.lineage_is_valid("A") is False
    assert engine.registry.is_terminal("A") is False
    assert engine.registry.lineage_is_valid("B") is True
    assert engine.registry.is_terminal("C") is True


def test_superseded_status_on_a_root_is_refused_by_the_record_validator() -> None:
    """A construction boundary, recorded rather than worked around.

    The accepted kernel cannot express "this root was superseded" on the status
    field, because the validator pairs SUPERSEDED with the OUTGOING edge. This is
    the recorded lifecycle incoherence. It is NOT an authority defect: status is
    not consulted anywhere in the lineage facts above.
    """

    with pytest.raises(Exception, match="SUPERSEDED observation must name"):
        _obs("A", status=ObservationStatus.SUPERSEDED)


# -- determinism and refusal -------------------------------------------------


def test_direct_successors_are_deterministic_in_registration_order() -> None:
    engine = _engine()
    register_measurement(engine, _obs("A"))
    register_measurement(engine, _obs("B", supersedes="A"))
    register_measurement(engine, _obs("C", supersedes="A"))
    ids = [o.measurement_id for o in engine.registry.direct_successors("A")]
    assert ids == ["B", "C"]


def test_unknown_measurement_is_refused_not_reported_empty() -> None:
    engine = _engine()
    for accessor in (
        engine.registry.direct_successors,
        engine.registry.lineage_is_valid,
        engine.registry.is_terminal,
    ):
        with pytest.raises(Book6RegistryError):
            accessor("nope")
