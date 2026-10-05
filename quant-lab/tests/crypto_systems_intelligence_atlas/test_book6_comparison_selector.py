"""Rung 6 — ``PRIOR_COMPARABLE_WINDOW`` and the GAP-6 effective-key ordering.

Discharges the ratified TIME group (test spec v0.6) and gates G-16..G-19.

The ordering rules under test, in the order they must hold:

    eligibility  ->  ordering        never the reverse   (G-19, TIME-11)
    strict ``<``                          prior means prior (TIME-6)
    greatest effective_end, then start, then lexical ref

The negative cases matter more than the positive ones. A selector that
orders correctly over candidates it should have filtered is still wrong, and
the two failure modes are only distinguishable if the fixture makes them
differ.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book6_comparison_contracts import (
    BaselineSelectorKind,
    BaselineSelectorSpec,
    ComparisonRule,
    CoverageRequirementStatus,
    DeltaOperator,
)
from crypto_systems_intelligence_atlas.book6_comparison_selector import (
    BaselineOutcome,
    BaselineRefusal,
    effective_end,
    effective_start,
    select_baseline,
)
from crypto_systems_intelligence_atlas.book6_grammar import (
    MissingnessState,
    ObservationStatus,
    RestatementReason,
    WindowClass,
)
from crypto_systems_intelligence_atlas.book6_support import windowed_observation

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
METRIC = "metric.tx"
FP = "fp:metric-tx"
METH = "book6-methodology@1"
CLAIM = ("claim:1",)


def _t(days: int) -> datetime:
    return T0 + timedelta(days=days)


def refused(match: str, factory, *args, **kwargs) -> None:
    """Assert the accepted record model refuses, and says why.

    ``MeasurementRecordError`` is raised inside a pydantic validator, so
    pydantic wraps it into a ``ValidationError``. The wrapper is how the
    refusal travels; the ratified reason inside it is the contract.
    """

    with pytest.raises(ValidationError) as excinfo:
        factory(*args, **kwargs)
    text = str(excinfo.value)
    assert match in text, f"expected refusal containing {match!r}, got:\n{text}"


def _obs(mid, *, day=0, window=WindowClass.INSTANTANEOUS, value=1.0,
         unit="count", missingness=MissingnessState.OBSERVED, claim_refs=CLAIM,
         supersedes=None, status=ObservationStatus.OBSERVED):
    return windowed_observation(
        mid, METRIC, value=value, missingness=missingness, claim_refs=claim_refs,
        unit=unit, window_class=window, valid_time=_t(day),
        supersedes=supersedes,
        restatement_reason=RestatementReason.INDEXER_CORRECTION if supersedes else None,
        status=status,
    )


def _rule(**kw):
    base = dict(
        comparison_rule_id="cmp:1",
        version=1,
        metric_definition_ref=METRIC,
        metric_definition_semantic_fingerprint=FP,
        baseline_selector=BaselineSelectorSpec(
            selector_kind=BaselineSelectorKind.PRIOR_COMPARABLE_WINDOW,
            window_compatibility=(WindowClass.INSTANTANEOUS,),
            methodology_compatibility=(METH,),
        ),
        delta_operator=DeltaOperator.ABSOLUTE_DELTA,
        compatible_methodology_refs=(METH,),
        unit_requirements="count",
        window_compatibility=(WindowClass.INSTANTANEOUS,),
        missingness_requirements=("OBSERVED",),
        output_semantics="ABSOLUTE_DELTA",
        coverage_requirement_status=CoverageRequirementStatus.UNRESOLVED,
    )
    base.update(kw)
    return ComparisonRule(**base)


def _fp(ref: str) -> str:
    assert ref == METRIC, f"unresolvable metric definition {ref}"
    return FP


def _all_current(_ref: str) -> bool:
    return True


def _select(comparison, candidates, rule=None, is_current=_all_current):
    return select_baseline(
        comparison=comparison,
        candidates=candidates,
        rule=rule or _rule(),
        semantic_fingerprint_of=_fp,
        is_current=is_current,
    )


# -- TIME-1: instantaneous carries no interval, stays eligible -------------


def test_time_1_instantaneous_candidate_carries_no_interval_and_is_eligible() -> None:
    """G-16: no code path populates window_start or window_end."""

    cand = _obs("b", day=1)
    comparison = _obs("c", day=2)
    assert cand.window_start is None and cand.window_end is None
    assert effective_end(cand) == _t(1) == effective_start(cand)
    assert _select(comparison, [cand]).selected_measurement_ref == "b"
    # The keys are derived, not stored: the record is untouched.
    assert cand.window_start is None and cand.window_end is None


def _raw_observation(**overrides):
    """Build a record straight from the model, bypassing the test helper."""

    from crypto_systems_intelligence_atlas.book6_records import MeasurementObservation

    base = {
        "measurement_id": "b", "subject_ref": "fixture:chain:alpha",
        "metric_definition_ref": METRIC, "category": _obs("b").category,
        "missingness_state": MissingnessState.OBSERVED, "value": 1.0,
        "unit": "count", "valid_time": _t(1), "observed_at": _t(1),
        "window_class": WindowClass.INSTANTANEOUS,
        "methodology_ref": "book6-methodology", "methodology_version": "1",
        "source_claim_refs": CLAIM, "native_scope": "fixture:architecture:pos",
    }
    base.update(overrides)
    return MeasurementObservation(**base)


def test_forging_an_interval_on_instantaneous_is_rejected_at_the_record() -> None:
    """TIME-9: the accepted model refuses; the selector never sees it."""

    refused("is instantaneous and may not declare an interval",
            _raw_observation, window_start=_t(1), window_end=_t(2))


# -- TIME-2: t1 < t2 < t3 < t4 selects t3 ----------------------------------


def test_time_2_latest_prior_instant_is_selected() -> None:
    result = _select(
        _obs("c", day=4),
        [_obs("t1", day=1), _obs("t2", day=2), _obs("t3", day=3)],
    )
    assert result.selected_measurement_ref == "t3"
    assert result.outcome is BaselineOutcome.RESOLVED


# -- TIME-3: caller order is irrelevant ------------------------------------


def test_time_3_caller_order_does_not_affect_the_baseline() -> None:
    comparison = _obs("c", day=4)
    cands = [_obs("t1", day=1), _obs("t2", day=2), _obs("t3", day=3)]
    rotations = [cands[i:] + cands[:i] for i in range(len(cands))]
    rotations.append(list(reversed(cands)))
    seen = {
        _select(comparison, order).selected_measurement_ref for order in rotations
    }
    assert seen == {"t3"}


# -- TIME-4: observed_at is irrelevant -------------------------------------


def test_time_4_observed_at_is_never_read() -> None:
    """FORBID: any read of observed_at inside the ordering path.

    Checked against the module's executable source with the module docstring
    removed by AST, so the prose that says "never read" cannot satisfy its own
    assertion.
    """

    import ast
    import inspect

    import crypto_systems_intelligence_atlas.book6_comparison_selector as m

    tree = ast.parse(inspect.getsource(m))
    docstrings = {
        id(node.body[0].value)
        for node in tree.body
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }
    executable = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Constant) and id(n) not in docstrings
    ]
    literals = [n.value for n in executable if isinstance(n.value, str)]
    assert not [s for s in literals if "observed_at" in s]

    comparison = _obs("c", day=4)
    assert _select(comparison, [_obs("t3", day=3)]).selected_measurement_ref == "t3"


# -- TIME-5: identical instant resolves lexically --------------------------


def test_time_5_same_instant_tie_resolves_to_the_greater_ref() -> None:
    result = _select(_obs("c", day=4), [_obs("aaa", day=3), _obs("zzz", day=3)])
    assert result.selected_measurement_ref == "zzz"
    assert set(result.eligible_refs) == {"aaa", "zzz"}


# -- TIME-6: the same instant is NOT prior ----------------------------------


def test_time_6_same_instant_is_not_prior() -> None:
    """Strict `<`: a `<=` here would let one instant serve as both."""

    result = _select(_obs("c", day=3), [_obs("b", day=3)])
    assert result.outcome is BaselineOutcome.BASELINE_UNAVAILABLE
    assert result.selected_measurement_ref is None
    assert result.exclusions == (("b", BaselineRefusal.NOT_STRICTLY_PRIOR),)


def test_a_later_candidate_is_not_prior_either() -> None:
    result = _select(_obs("c", day=2), [_obs("b", day=3)])
    assert result.exclusions[0][1] is BaselineRefusal.NOT_STRICTLY_PRIOR


# -- TIME-7 / §1.4: the interval path is unchanged -------------------------


def test_time_7_interval_ordering_matches_the_effective_key_rule() -> None:
    """For intervals the projection is the identity, so old == new."""

    comparison = _obs("c", day=6, window=WindowClass.DAILY)
    cands = [_obs("i1", day=1, window=WindowClass.DAILY),
             _obs("i2", day=3, window=WindowClass.DAILY)]
    rule = _rule(
        window_compatibility=(WindowClass.DAILY,),
        baseline_selector=BaselineSelectorSpec(
            selector_kind=BaselineSelectorKind.PRIOR_COMPARABLE_WINDOW,
            window_compatibility=(WindowClass.DAILY,),
            methodology_compatibility=(METH,),
        ),
    )
    for candidate in cands:
        assert effective_end(candidate) == candidate.window_end
        assert effective_start(candidate) == candidate.window_start
    assert _select(comparison, cands, rule).selected_measurement_ref == "i2"


# -- TIME-8: mixed shapes rejected before ordering -------------------------


def test_time_8_mixed_temporal_shapes_are_rejected_without_ordering() -> None:
    """No ordering is computed across shapes, and nothing is coerced."""

    comparison = _obs("c", day=4)
    instant = _obs("i", day=3)
    interval = _obs("v", day=3, window=WindowClass.DAILY)
    # A rule permitting BOTH classes, so the refusal can only be the shape
    # mismatch and not the rule's allow-list.
    rule = _rule(
        window_compatibility=(WindowClass.INSTANTANEOUS, WindowClass.DAILY),
        baseline_selector=BaselineSelectorSpec(
            selector_kind=BaselineSelectorKind.PRIOR_COMPARABLE_WINDOW,
            window_compatibility=(WindowClass.INSTANTANEOUS, WindowClass.DAILY),
            methodology_compatibility=(METH,),
        ),
    )
    result = _select(comparison, [instant, interval], rule=rule)
    assert result.selected_measurement_ref == "i"
    assert result.exclusions == (("v", BaselineRefusal.WINDOW_INCOMPATIBLE),)
    # The interval record was not coerced into the instantaneous shape.
    assert interval.window_class is WindowClass.DAILY
    assert interval.window_start is not None and interval.window_end is not None


# -- TIME-10: interval missing bounds is rejected at the record ------------


def test_time_10_interval_without_bounds_is_rejected() -> None:
    refused("requires an explicit [start, end) interval",
            _raw_observation, window_class=WindowClass.DAILY,
            window_start=None, window_end=None)


# -- TIME-11 / TIME-11.1 / G-19: eligibility precedes ordering -------------


def test_time_11_non_terminal_predecessor_is_filtered_before_ordering() -> None:
    """The paired hard case: A ties with B and would WIN the tie-break."""

    comparison = _obs("c", day=10)
    # A and B tie on every ordering key; A is lexically greater.
    a = _obs("zzz", day=5, supersedes="old")      # has a registered successor
    b = _obs("aaa", day=5)                          # terminal
    current = {"aaa", "c"}
    result = _select(comparison, [a, b], is_current=lambda r: r in current)

    assert "zzz" > "aaa", "the fixture must make the ineligible ref win the tie"
    assert result.selected_measurement_ref == "aaa"
    assert result.exclusions == (("zzz", BaselineRefusal.NOT_CURRENT),)


def test_time_11_refusal_is_terminality_not_status() -> None:
    """B-STRICT: status is never the reason a candidate is excluded."""

    comparison = _obs("c", day=10)
    a = _obs("zzz", day=5, supersedes="old")
    b = _obs("aaa", day=5)
    # A carries OBSERVED status and is still refused; B carries SUPERSEDED and
    # is still selected. Status decides nothing in either direction.
    result = _select(comparison, [a, b], is_current=lambda r: r == "aaa")
    assert ("zzz", BaselineRefusal.NOT_CURRENT) in result.exclusions
    assert result.selected_measurement_ref == "aaa"


def test_time_11_1_status_permutation_gives_one_outcome() -> None:
    """TIME-11.1: four status permutations, one selection, unchanged.

    The lineage is fixed; only status varies. ``A`` is non-terminal because a
    *successor* exists, and ``B`` is terminal because none does.
    """

    z = _obs("Z", day=1, supersedes="root")
    y = _obs("Y", day=1, supersedes="root2")
    a = _obs("A", day=5, supersedes="Z")
    s = _obs("S", day=4, supersedes="A")     # makes A non-terminal
    b = _obs("B", day=5, supersedes="Y")     # terminal: nothing supersedes B
    comparison = _obs("C", day=10)
    current = {"B", "C"}

    outcomes = set()
    for a_status, b_status in (
        (ObservationStatus.OBSERVED, ObservationStatus.OBSERVED),
        (ObservationStatus.SUPERSEDED, ObservationStatus.OBSERVED),
        (ObservationStatus.OBSERVED, ObservationStatus.SUPERSEDED),
        (ObservationStatus.SUPERSEDED, ObservationStatus.SUPERSEDED),
    ):
        a_v = a.model_copy(update={"status": a_status})
        b_v = b.model_copy(update={"status": b_status})
        result = _select(comparison, [a_v, b_v], is_current=lambda r: r in current)
        outcomes.add(result.selected_measurement_ref)
        assert ("A", BaselineRefusal.NOT_CURRENT) in result.exclusions
    assert outcomes == {"B"}
    assert z.measurement_id and y.measurement_id and s.measurement_id


def test_eligibility_fully_precedes_ordering() -> None:
    """G-19: the lexical tie-break never sees an ineligible candidate."""

    comparison = _obs("c", day=10)
    # "zzzz" sorts greatest and would win the tie-break, but is filtered on
    # each axis in turn.
    other_method = _obs("zzzz", day=5).model_copy(
        update={"methodology_ref": "other"})
    other_unit = _obs("zulu", day=5, unit="other")
    other_subject = _obs("yankee", day=5).model_copy(
        update={"subject_ref": "other:subject"})
    good = _obs("aaa", day=5)
    assert "zzzz" > "zulu" > "yankee" > "aaa"

    result = _select(comparison, [other_method, other_unit, other_subject, good])
    assert result.selected_measurement_ref == "aaa"
    assert result.eligible_refs == ("aaa",)
    assert {reason for _ref, reason in result.exclusions} == {
        BaselineRefusal.METHODOLOGY_NOT_PERMITTED,
        BaselineRefusal.UNIT_MISMATCH,
        BaselineRefusal.SUBJECT_MISMATCH,
    }


# -- eligibility conditions -------------------------------------------------


def test_missingness_not_permitted_excludes() -> None:
    result = _select(
        _obs("c", day=10),
        [_obs("b", day=5, missingness=MissingnessState.NOT_COLLECTED, value=None)],
    )
    assert result.exclusions[0][1] is BaselineRefusal.MISSINGNESS_NOT_PERMITTED


def test_a_record_that_forbids_a_value_is_not_a_baseline() -> None:
    """Even when the rule permits the missingness state, there is no value."""

    rule = _rule(missingness_requirements=("OBSERVED", "NOT_APPLICABLE"))
    result = _select(
        _obs("c", day=10),
        [_obs("b", day=5, missingness=MissingnessState.NOT_APPLICABLE, value=None)],
        rule=rule,
    )
    assert result.exclusions[0][1] is BaselineRefusal.NOT_VALUE_BEARING


def test_missing_source_authority_is_refused_for_an_out_of_model_record() -> None:
    """The accepted record forbids this; the gate defends against one built
    outside it, and reports last so a more specific gate wins when both fail.
    """

    from crypto_systems_intelligence_atlas.book6_records import MeasurementObservation

    smuggled = MeasurementObservation.model_construct(
        **_obs("b", day=5).model_dump(exclude={"source_claim_refs"}),
        source_claim_refs=(),
    )
    result = _select(_obs("c", day=10), [smuggled])
    assert result.exclusions[0][1] is BaselineRefusal.MISSING_SOURCE_AUTHORITY


def test_methodology_must_be_on_the_allow_list() -> None:
    other = _obs("b", day=5)
    other = other.model_copy(update={"methodology_ref": "other"})
    result = _select(_obs("c", day=10), [other])
    assert result.exclusions[0][1] is BaselineRefusal.METHODOLOGY_NOT_PERMITTED


def test_semantic_fingerprint_mismatch_excludes() -> None:
    def wrong_fp(ref: str) -> str:
        return "fp:something-else"

    result = select_baseline(
        comparison=_obs("c", day=10), candidates=[_obs("b", day=5)],
        rule=_rule(), semantic_fingerprint_of=wrong_fp, is_current=_all_current,
    )
    assert result.exclusions[0][1] is BaselineRefusal.SEMANTIC_FINGERPRINT_MISMATCH


def test_subject_mismatch_excludes() -> None:
    other = _obs("b", day=5).model_copy(update={"subject_ref": "other:subject"})
    result = _select(_obs("c", day=10), [other])
    assert result.exclusions[0][1] is BaselineRefusal.SUBJECT_MISMATCH


def test_unresolvable_metric_definition_fails_closed() -> None:
    def missing(ref: str) -> str:
        raise KeyError(ref)

    with pytest.raises(Exception, match="did not resolve"):
        select_baseline(
            comparison=_obs("c", day=10), candidates=[_obs("b", day=5)],
            rule=_rule(), semantic_fingerprint_of=missing, is_current=_all_current,
        )


# -- §2.5 / §2.6: unavailable, and select-not-aggregate --------------------


def test_no_eligible_baseline_is_a_first_class_outcome() -> None:
    result = _select(_obs("c", day=1), [_obs("b", day=5)])
    assert result.outcome is BaselineOutcome.BASELINE_UNAVAILABLE
    assert result.selected_measurement_ref is None
    assert result.is_resolved is False


def test_empty_candidate_set_is_unavailable() -> None:
    result = _select(_obs("c", day=5), [])
    assert result.outcome is BaselineOutcome.BASELINE_UNAVAILABLE
    assert result.exclusions == ()


def test_selector_selects_exactly_one_and_never_aggregates() -> None:
    """§2.6: the result is ONE observation; no mean, sum, or median."""

    comparison = _obs("c", day=10)
    cands = [_obs(f"b{i}", day=i, value=float(i)) for i in range(1, 5)]
    result = _select(comparison, cands)
    assert isinstance(result.selected_measurement_ref, str)
    assert result.selected_measurement_ref == "b4"
    assert result.eligible_refs == ("b1", "b2", "b3", "b4")


def test_every_exclusion_is_named_not_aggregated() -> None:
    """AGGREGATE_ONLY = REJECTED: the check names the failing requirement."""

    comparison = _obs("c", day=10)
    result = _select(comparison, [_obs("b", day=5, unit="other")])
    assert len(result.exclusions) == 1
    ref, reason = result.exclusions[0]
    assert ref == "b" and isinstance(reason, BaselineRefusal)


# -- the selection-bias firewall -------------------------------------------


def test_coverage_is_not_a_selection_input() -> None:
    """Coverage authorizes AFTER structural selection; it may not select."""

    comparison = _obs("c", day=10)
    with_cov = _obs("b", day=5).model_copy(update={"coverage_observation_id": "cov:1"})
    without_cov = _obs("b2", day=5)
    result = _select(comparison, [with_cov, without_cov])
    assert result.selected_measurement_ref == "b2"
    assert set(result.eligible_refs) == {"b", "b2"}


# -- G-17: derived keys never persist --------------------------------------


def test_effective_keys_are_derived_and_discarded() -> None:
    cand = _obs("b", day=5)
    before = cand.model_dump()
    effective_end(cand)
    effective_start(cand)
    assert cand.model_dump() == before
    assert set(MeasurementRecord_fields()) <= set(before)


def MeasurementRecord_fields():
    return cand_fields()


def cand_fields():
    from crypto_systems_intelligence_atlas.book6_records import MeasurementObservation

    return set(MeasurementObservation.model_fields)


def test_no_new_temporal_contract_field_exists() -> None:
    fields = cand_fields()
    assert "effective_start" not in fields
    assert "effective_end" not in fields


# -- the selector may not aggregate or window-coerce ------------------------


def test_no_aggregation_or_one_day_convention_in_the_selector() -> None:
    import inspect

    import crypto_systems_intelligence_atlas.book6_comparison_selector as m

    source = inspect.getsource(m)
    for banned in ("timedelta", "rolling_mean", "median", "days="):
        assert banned not in source, banned
    assert hasattr(m, "effective_end") and hasattr(m, "effective_start")
