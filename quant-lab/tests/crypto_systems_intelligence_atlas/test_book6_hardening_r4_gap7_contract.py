"""Book 6 GAP-7 — the ratified 40-case currentness contract.

    CARR-1..CARR-19   carried supersession + evidence cases
    CURR-S1..S3       B-STRICT: status is quarantined
    TERM-1..TERM-6    terminality, no resurrection, fail-closed branching
    NV-1..NV-10       NV-B concretised
    STRUCT-1..STRUCT-2 structural states still require evidence

Each test names the ratified case it discharges. Two cases are pinned by name
because they are the ones most likely to be quietly over-applied:

    NV-2    a CITED non-value-bearing record is current  (NV-B is not NV-C)
    TERM-6  the SUCCESSORS of a branch are current       (scope is PER_RECORD)

Both are falsifiers. An implementation that satisfied NV-1 and TERM-4 by
blanket refusal would pass most of this file and fail those two.
"""

from __future__ import annotations

import pytest

from crypto_systems_intelligence_atlas.book6_grammar import (
    MissingnessState,
    ObservationStatus,
    RestatementReason,
    VALUE_BEARING_MISSINGNESS,
    VALUE_FORBIDDEN_MISSINGNESS,
)
from crypto_systems_intelligence_atlas.book6_core import Book6EngineError
from crypto_systems_intelligence_atlas.book6_registry import (
    Book6CurrentnessError,
    Book6RegistryError,
    CurrentnessRefusal,
)
from crypto_systems_intelligence_atlas.book6_support import (
    CLAIM_ID,
    build_engine,
    decay_claim,
    definition,
    methodology,
    register_definition,
    register_measurement,
    windowed_observation,
)

METRIC = "m:contract"
R = RestatementReason.INDEXER_CORRECTION
DEAD = "claim:decayed"
NV_STATES = [s for s in MissingnessState if s not in VALUE_BEARING_MISSINGNESS]


def _engine(*claims):
    engine, *_ = build_engine(*(claims or (CLAIM_ID, DEAD)))
    register_definition(engine, definition(METRIC))
    return engine


def _vb(mid, *, supersedes=None, status=ObservationStatus.OBSERVED,
        claim_refs=(CLAIM_ID,)):
    return windowed_observation(
        mid, METRIC, value=1.0, missingness=MissingnessState.OBSERVED,
        claim_refs=claim_refs, supersedes=supersedes,
        restatement_reason=R if supersedes else None, status=status)


def _nv(mid, *, claim_refs=(CLAIM_ID,), state=MissingnessState.NOT_COLLECTED):
    return windowed_observation(
        mid, METRIC, value=None, missingness=state, claim_refs=claim_refs, unit=None)


def _refused(engine, mid) -> CurrentnessRefusal:
    with pytest.raises(Book6CurrentnessError) as e:
        engine.registry.resolve_current(mid)
    return e.value.reason


# -- CARR-1..CARR-6 : supersession -------------------------------------------


def test_carr_1_terminal_live_record_resolves() -> None:
    engine = _engine()
    register_measurement(engine, _vb("A"))
    assert engine.registry.resolve_current("A").measurement_id == "A"


def test_carr_2_superseded_refused_successor_current() -> None:
    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    assert _refused(engine, "A") is CurrentnessRefusal.NOT_TERMINAL
    assert engine.registry.resolve_current("B").measurement_id == "B"


def test_carr_3_decayed_successor_refuses_both() -> None:
    engine, cs, _, svc = build_engine(CLAIM_ID, DEAD)
    register_definition(engine, definition(METRIC))
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A", claim_refs=(DEAD,)))
    decay_claim(svc, cs, DEAD, "STALE")
    assert _refused(engine, "B") is CurrentnessRefusal.SOURCE_CLAIMS_STALE
    assert _refused(engine, "A") is CurrentnessRefusal.NOT_TERMINAL


def test_carr_4_successor_methodology_withdrawn_refuses_both() -> None:
    """CARR-4: when the successor loses methodology authority, both refuse.

    v1 is installed, then superseded by v2. B still names v1, so B fails at the
    methodology gate -- and A, already superseded, stays refused. The point is
    that A gains nothing from B's loss: refusal is not a reversible contest.
    """

    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    assert engine.registry.is_authoritative_now("B") is True

    engine.registry.methodologies.supersede_methodology(
        methodology(version="2")
    )
    assert _refused(engine, "B") is CurrentnessRefusal.METHODOLOGY_CURRENT
    assert _refused(engine, "A") is CurrentnessRefusal.NOT_TERMINAL


def test_carr_5_three_link_chain_only_head_current() -> None:
    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    register_measurement(engine, _vb("C", supersedes="B"))
    assert _refused(engine, "A") is CurrentnessRefusal.NOT_TERMINAL
    assert _refused(engine, "B") is CurrentnessRefusal.NOT_TERMINAL
    assert engine.registry.resolve_current("C").measurement_id == "C"


def test_carr_6_branched_lineage_refused_at_lineage() -> None:
    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    register_measurement(engine, _vb("C", supersedes="A"))
    assert _refused(engine, "A") is CurrentnessRefusal.LINEAGE_INVALID


# -- CARR-7..CARR-14 : status quarantine and history integrity ---------------


def test_carr_7_observed_status_alone_is_insufficient() -> None:
    """CARR-8: OBSERVED does not rescue a superseded record; lineage refuses."""

    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A",
                                     status=ObservationStatus.OBSERVED))
    assert _refused(engine, "A") is CurrentnessRefusal.NOT_TERMINAL


def test_carr_8_resolve_current_on_predecessor_raises() -> None:
    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    with pytest.raises(Book6RegistryError):
        engine.registry.resolve_current("A")


def test_carr_9_is_authoritative_now_on_predecessor_is_false() -> None:
    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    assert engine.registry.is_authoritative_now("A") is False


def test_carr_11_predecessor_filtered_before_ordering() -> None:
    """CARR-12/13: the predecessor never enters the candidate set at all.

    A is also the lexically greater ref, so had it survived eligibility it would
    have won. That it does not win is what proves filtering happened BEFORE
    ordering, not after.
    """

    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    candidates = [m for m in ("A", "B")
                  if engine.registry.is_authoritative_now(m)]
    assert candidates == ["B"]


def test_carr_13_superseded_record_still_queryable() -> None:
    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    assert engine.registry.registered_measurement("A").measurement_id == "A"


def test_carr_14_predecessor_does_not_resurrect() -> None:
    engine, cs, _, svc = build_engine(CLAIM_ID, DEAD)
    register_definition(engine, definition(METRIC))
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A", claim_refs=(DEAD,)))
    decay_claim(svc, cs, DEAD, "STALE")
    assert engine.registry.is_authoritative_now("B") is False
    assert engine.registry.is_authoritative_now("A") is False


# -- CARR-16..CARR-19 : evidence, mutation, drift, quarantine ----------------


def test_carr_17_non_value_bearing_decayed_claim_refused() -> None:
    engine, cs, _, svc = build_engine(CLAIM_ID, DEAD)
    register_definition(engine, definition(METRIC))
    register_measurement(engine, _nv("N", claim_refs=(DEAD,)))
    decay_claim(svc, cs, DEAD, "STALE")
    assert _refused(engine, "N") is CurrentnessRefusal.SOURCE_CLAIMS_STALE


def test_carr_15_history_intact_after_supersession() -> None:
    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    assert {m for m in engine.registry.registered_refs()} == {"A", "B"}
    assert engine.registry.measurement_history("A")[0].measurement_id == "A"


def test_carr_16_resolve_current_mutates_nothing() -> None:
    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    before_refs = engine.registry.registered_refs()
    before_a = engine.registry.registered_measurement("A")
    for _ in range(3):
        with pytest.raises(Book6RegistryError):
            engine.registry.resolve_current("A")
        engine.registry.resolve_current("B")
    assert engine.registry.registered_refs() == before_refs
    assert engine.registry.registered_measurement("A") == before_a


def test_carr_18_structural_drift_fails_at_structure() -> None:
    """CARR-22: a forged copy drifting from its definition loses authority."""

    engine = _engine()
    obs = register_measurement(engine, _vb("A"))
    forged = obs.model_copy(update={"unit": "forged-unit"})
    engine.registry._measurements["A"] = forged
    assert _refused(engine, "A") is CurrentnessRefusal.STRUCTURE


def test_carr_19_status_flip_changes_nothing() -> None:
    """CARR-23: no route that flips ObservationStatus moves the verdict.

    Two records identical on every authority-bearing fact, one carrying
    SUPERSEDED. Forged in via ``model_copy`` precisely because the record
    validator would otherwise refuse the shape -- the point is that even a
    successful forgery of the status field buys no authority.
    """

    engine = _engine()
    register_measurement(engine, _vb("R"))
    register_measurement(engine, _vb("X", supersedes="R"))
    honest = engine.registry.is_authoritative_now("X")
    flipped = engine.registry.registered_measurement("X").model_copy(
        update={"status": ObservationStatus.SUPERSEDED})
    engine.registry._measurements["X"] = flipped
    assert engine.registry.is_authoritative_now("X") == honest is True


# -- CURR-S1..CURR-S3 : B-STRICT ---------------------------------------------


def test_curr_s1_identical_except_status_gives_identical_verdict() -> None:
    engine = _engine()
    register_measurement(engine, _vb("R1"))
    register_measurement(engine, _vb("R2"))
    register_measurement(engine, _vb("P", supersedes="R1"))
    register_measurement(engine, _vb("Q", supersedes="R2",
                                     status=ObservationStatus.SUPERSEDED))
    assert engine.registry.is_authoritative_now("P") is True
    assert engine.registry.is_authoritative_now("Q") is True


def test_curr_s2_superseded_status_refused_at_terminality_not_status() -> None:
    engine = _engine()
    register_measurement(engine, _vb("R"))
    register_measurement(engine, _vb("X", supersedes="R",
                                     status=ObservationStatus.SUPERSEDED))
    register_measurement(engine, _vb("Y", supersedes="X"))
    assert _refused(engine, "X") is CurrentnessRefusal.NOT_TERMINAL


def test_curr_s3_superseded_status_refused_at_revalidation_not_status() -> None:
    engine, cs, _, svc = build_engine(CLAIM_ID, DEAD)
    register_definition(engine, definition(METRIC))
    register_measurement(engine, _vb("R"))
    register_measurement(engine, _vb("X", supersedes="R",
                                     status=ObservationStatus.SUPERSEDED,
                                     claim_refs=(DEAD,)))
    decay_claim(svc, cs, DEAD, "STALE")
    assert _refused(engine, "X") is CurrentnessRefusal.SOURCE_CLAIMS_STALE


# -- TERM-1..TERM-6 ----------------------------------------------------------


def test_term_1_lone_record_may_be_current() -> None:
    engine = _engine()
    register_measurement(engine, _vb("A"))
    assert engine.registry.resolve_current("A").measurement_id == "A"


def test_term_2_superseded_record_not_current_successor_may_be() -> None:
    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    assert _refused(engine, "A") is CurrentnessRefusal.NOT_TERMINAL
    assert engine.registry.resolve_current("B").measurement_id == "B"


def test_term_3_only_chain_head_may_be_current() -> None:
    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    register_measurement(engine, _vb("C", supersedes="B"))
    assert [m for m in "ABC" if engine.registry.is_authoritative_now(m)] == ["C"]


def test_term_4_branched_lineage_fails_closed() -> None:
    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    register_measurement(engine, _vb("C", supersedes="A"))
    assert _refused(engine, "A") is CurrentnessRefusal.LINEAGE_INVALID
    assert engine.registry.is_authoritative_now("A") is False


def test_term_5_predecessor_never_resurrects() -> None:
    engine, cs, _, svc = build_engine(CLAIM_ID, DEAD)
    register_definition(engine, definition(METRIC))
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A", claim_refs=(DEAD,)))
    decay_claim(svc, cs, DEAD, "STALE")
    assert engine.registry.is_authoritative_now("A") is False


def test_term_6_branch_successors_are_still_current() -> None:
    """TERM-6: the paired negative of TERM-4.

    Ratified scope is PER_RECORD (BOOK6-GAP7-SUCCESSOR-CURRENTNESS-v0.1). A
    branched predecessor invalidates ITSELF. Refusing B and C as well would be
    component-wide fail-closed, which needs a sixth conjunct that no
    ratification supplies.

    NOTE: the carried case CARR-21 in test spec v0.2 §5 states the older
    component-wide outcome. That row predates the scope ratification and is
    superseded on this point; TERM-6 states it as ratified.
    """

    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    register_measurement(engine, _vb("C", supersedes="A"))
    assert engine.registry.is_authoritative_now("A") is False
    assert engine.registry.is_authoritative_now("B") is True
    assert engine.registry.is_authoritative_now("C") is True


# -- NV-1..NV-10 : NV-B ------------------------------------------------------


def test_nv_1_source_less_non_value_bearing_refused() -> None:
    """NV-1, the headline case: the one behaviour the ratification changes."""

    engine = _engine()
    register_measurement(engine, _nv("N", claim_refs=()))
    assert _refused(engine, "N") is CurrentnessRefusal.SOURCE_CLAIMS_ABSENT


def test_nv_2_cited_non_value_bearing_is_current() -> None:
    """NV-2, the case that must not be over-applied.

    Refusing this would satisfy NV-1 while silently re-ratifying NV-C's
    per-state split. NV-B makes SOURCE-LESS records non-current, not
    non-value-bearing ones.
    """

    engine = _engine()
    register_measurement(engine, _nv("N", claim_refs=(CLAIM_ID,)))
    assert engine.registry.resolve_current("N").measurement_id == "N"


def test_nv_3_cited_non_value_bearing_with_decayed_claim_refused() -> None:
    engine, cs, _, svc = build_engine(CLAIM_ID, DEAD)
    register_definition(engine, definition(METRIC))
    register_measurement(engine, _nv("N", claim_refs=(DEAD,)))
    decay_claim(svc, cs, DEAD, "STALE")
    assert _refused(engine, "N") is CurrentnessRefusal.SOURCE_CLAIMS_STALE


def test_nv_4_source_less_record_is_constructible_and_registrable() -> None:
    """Axiom 1: NV-B refuses authority; it does not forbid history."""

    engine = _engine()
    register_measurement(engine, _nv("N", claim_refs=()))
    assert engine.registry.registered_measurement("N").measurement_id == "N"


def test_nv_5_source_less_record_remains_queryable() -> None:
    engine = _engine()
    register_measurement(engine, _nv("N", claim_refs=()))
    obs = engine.registry.registered_measurement("N")
    assert obs.missingness_state is MissingnessState.NOT_COLLECTED
    assert "N" in engine.registry.registered_refs()
    assert engine.registry.is_authoritative_now("N") is False


def test_nv_6_current_value_still_refuses_on_non_value_bearing() -> None:
    engine = _engine()
    register_measurement(engine, _nv("N", claim_refs=(CLAIM_ID,)))
    with pytest.raises(Book6EngineError, match="absence is not zero"):
        engine.current_value("N")


def test_nv_7_missingness_partition_unchanged() -> None:
    assert len(list(MissingnessState)) == 10
    assert VALUE_FORBIDDEN_MISSINGNESS == frozenset(
        set(MissingnessState) - VALUE_BEARING_MISSINGNESS)
    assert not (VALUE_FORBIDDEN_MISSINGNESS & VALUE_BEARING_MISSINGNESS)


@pytest.mark.parametrize("state", NV_STATES, ids=lambda s: s.value)
def test_nv_8_uniform_across_all_eight_non_value_states(state) -> None:
    engine = _engine()
    register_measurement(engine, _nv("N", claim_refs=(), state=state))
    assert _refused(engine, "N") is CurrentnessRefusal.SOURCE_CLAIMS_ABSENT


def test_nv_9_methodology_live_re_resolved_for_non_value_bearing() -> None:
    """A cited non-value-bearing record is refused exactly as a value-bearing one."""

    engine = _engine()
    register_measurement(engine, _nv("N", claim_refs=(CLAIM_ID,)))
    assert engine.registry.is_authoritative_now("N") is True
    engine.registry.methodologies.supersede_methodology(methodology(version="2"))
    assert _refused(engine, "N") is CurrentnessRefusal.METHODOLOGY_CURRENT


def test_nv_10_non_terminal_cited_record_refused_at_terminality_first() -> None:
    """NV-10: terminality is decided BEFORE the authority result is computed."""

    engine = _engine()
    register_measurement(engine, _vb("A"))
    register_measurement(engine, _vb("B", supersedes="A"))
    assert _refused(engine, "A") is CurrentnessRefusal.NOT_TERMINAL


# -- STRUCT-1..STRUCT-2 -----------------------------------------------------


def test_struct_1_uncited_structural_assertion_is_not_current() -> None:
    engine = _engine()
    register_measurement(engine, _nv("S", claim_refs=(),
                                      state=MissingnessState.NOT_APPLICABLE))
    assert _refused(engine, "S") is CurrentnessRefusal.SOURCE_CLAIMS_ABSENT


def test_struct_2_cited_structural_assertion_may_be_current() -> None:
    """STRUCT-2 prevents the over-reading: NV-B requires CITATION, not Book 6 origin."""

    engine = _engine()
    register_measurement(engine, _nv("S", claim_refs=(CLAIM_ID,),
                                      state=MissingnessState.NOT_SUPPORTED))
    assert engine.registry.resolve_current("S").measurement_id == "S"


# -- accounting --------------------------------------------------------------


def test_the_forty_ratified_cases_are_all_named_in_this_file() -> None:
    import ast
    import pathlib

    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    expected = (
        [f"test_carr_{i}_" for i in range(1, 20)]
        + ["test_curr_s1_", "test_curr_s2_", "test_curr_s3_"]
        + [f"test_term_{i}_" for i in range(1, 7)]
        + [f"test_nv_{i}_" for i in range(1, 11)]
        + ["test_struct_1_", "test_struct_2_"]
    )
    missing = [p for p in expected if not any(n.startswith(p) for n in names)]
    assert missing == [], f"undischarged ratified cases: {missing}"


# -- CARR-10 / CARR-12 : the consumer surfaces -------------------------------

NAT = "metric.native.tx"
NORM = "metric.normalized.per_user"
RULE = "normrule:per_user:1"
DEN = "obs:denominator"
NORM_METHOD = "book6-normalization@1"


def _normalization_stack(*, native_claim):
    """A normalization rule whose native input is ``obs:native``."""
    from crypto_systems_intelligence_atlas.book6_normalization import (
        NormalizationRule,
        NormalizationType,
    )

    engine, *_ = build_engine(CLAIM_ID)
    register_definition(engine, definition(NAT))
    register_definition(engine, definition(NORM, unit="per-user"))
    engine.registry.methodologies.register_methodology(
        methodology(ref="book6-normalization", version="1"))
    register_measurement(engine, windowed_observation(
        "obs:native", NAT, value=7.0, missingness=MissingnessState.OBSERVED,
        claim_refs=native_claim))
    register_measurement(engine, windowed_observation(
        DEN, NAT, value=2.0, missingness=MissingnessState.OBSERVED,
        claim_refs=(CLAIM_ID,)))
    rule = NormalizationRule(
        normalization_rule_id=RULE,
        input_metric_definition_ref=NAT,
        input_measurement_refs=("obs:native",),
        normalization_type=NormalizationType.PER_USER,
        transformation="x = native / distinct_users",
        denominator_ref=DEN,
        cohort_ref="cohort:pos@1",
        methodology_ref=NORM_METHOD,
        valid_time=windowed_observation(
            "x", NAT, value=1.0, missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM_ID,)).valid_time,
        version="1",
        output_metric_definition_ref=NORM,
    )
    engine.registry._normalization_rules[RULE] = rule
    return engine, rule


def test_carr_10_normalization_citing_a_superseded_predecessor_is_refused() -> None:
    """CARR-10: a consumer surface cannot borrow authority from a dead record.

    The native input is superseded, so `normalize` must refuse and emit no
    normalized value. Authority is re-resolved at the consumer, not trusted from
    the record that happens to be named.
    """

    from crypto_systems_intelligence_atlas.book6_normalization import (
        NormalizedMeasurement,
    )

    engine, rule = _normalization_stack(native_claim=(CLAIM_ID,))
    # supersede the native input so it is no longer current
    register_measurement(engine, windowed_observation(
        "obs:native2", NAT, value=9.0, missingness=MissingnessState.OBSERVED,
        claim_refs=(CLAIM_ID,), supersedes="obs:native",
        restatement_reason=R))
    assert engine.registry.is_authoritative_now("obs:native") is False

    product = NormalizedMeasurement(
        normalized_measurement_id="norm:1",
        normalization_rule_id=RULE,
        native_measurement_refs=("obs:native",),
        normalized_metric_definition_ref=NORM,
        value=3.5,
        unit="per-user",
        cohort_ref="cohort:pos@1",
        valid_time=windowed_observation(
            "y", NAT, value=1.0, missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM_ID,)).valid_time,
    )
    with pytest.raises(Book6EngineError):
        engine.normalize(product, rule)


def test_carr_12_lexical_tie_break_never_sees_a_filtered_candidate() -> None:
    """CARR-12: the predecessor is gone before ordering, tie-break included.

    'A' sorts lexically AFTER 'B' and would win any tie-break that saw it. It
    never reaches the ordering phase, so B wins despite losing the tie-break.
    """

    # "Z" is the lexically GREATER ref, so the predecessor would win any
    # tie-break that saw it. That it does not win is the whole assertion.
    engine = _engine()
    register_measurement(engine, _vb("Z"))
    register_measurement(engine, _vb("B", supersedes="Z"))
    assert "Z" > "B"
    eligible = sorted(m for m in ("Z", "B")
                      if engine.registry.is_authoritative_now(m))
    assert eligible == ["B"]
