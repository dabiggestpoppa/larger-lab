"""Rung 4 — the comparison / change contracts.

Two authority-bearing classes, their closed vocabularies, and the invariants
that are decidable from a record's own shape. Each test names the ratified
clause it discharges, so a later rung can point at what already holds.

The tests that matter most here are the negative ones. A comparison contract
is easy to get right by permitting too much; these pin the refusals.

Note on assertion style: the contract validators run inside pydantic, so a
refusal surfaces as ``pydantic.ValidationError`` wrapping the
``ComparisonContractError`` message. :func:`refused` asserts on that message,
which is the part carrying the ratified reason.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book6_comparison_contracts import (
    EXECUTABLE_BASELINE_SELECTOR,
    RESERVED_NOT_EXECUTABLE_SELECTORS,
    BaselineOrderingPolicy,
    BaselineSelectorKind,
    BaselineSelectorSpec,
    ChangeAxis,
    ChangeKind,
    ChangeObservation,
    ComparisonContractError,
    ComparisonRule,
    CoverageObservationState,
    CoverageRequirementStatus,
    CoverageVerdict,
    DeltaOperator,
    TemporalComparabilityStatus,
)
from crypto_systems_intelligence_atlas.book6_frozen import Book6FrozenModel
from crypto_systems_intelligence_atlas.book6_grammar import WindowClass

NOW = datetime(2026, 10, 5, tzinfo=timezone.utc)
METRIC = "metric.tx"
FP = "fp:metric-tx"
RULE = "cmp:1"
SEL_FP = "fp:selector"
R = "book6-methodology@1"


def refused(match: str, factory, *args, **kwargs):
    """Assert that constructing a contract is refused, and says why.

    The contract validators are pydantic ``mode="after"`` model validators, so
    pydantic wraps ``ComparisonContractError`` (a ``ValueError``) into a
    ``ValidationError``. The wrapper is an implementation detail of how the
    refusal travels; the ratified reason inside it is the contract.
    """

    with pytest.raises(ValidationError) as excinfo:
        factory(*args, **kwargs)
    text = str(excinfo.value)
    assert match in text, f"expected refusal containing {match!r}, got:\n{text}"
    return text


def _selector(kind=BaselineSelectorKind.PRIOR_COMPARABLE_WINDOW, **kw):
    return BaselineSelectorSpec(
        selector_kind=kind,
        window_compatibility=(WindowClass.INSTANTANEOUS,),
        methodology_compatibility=(R,),
        **kw,
    )


def _rule(**kw):
    base = dict(
        comparison_rule_id=RULE,
        version=1,
        metric_definition_ref=METRIC,
        metric_definition_semantic_fingerprint=FP,
        baseline_selector=_selector(),
        delta_operator=DeltaOperator.ABSOLUTE_DELTA,
        compatible_methodology_refs=(R,),
        unit_requirements="count",
        window_compatibility=(WindowClass.INSTANTANEOUS,),
        missingness_requirements=("OBSERVED",),
        output_semantics="ABSOLUTE_DELTA",
        coverage_requirement_status=CoverageRequirementStatus.UNRESOLVED,
    )
    base.update(kw)
    return ComparisonRule(**base)


def _change(**kw):
    base = dict(
        change_observation_id="chg:1",
        subject_ref="subject:1",
        valid_time=NOW,
        metric_definition_ref=METRIC,
        metric_definition_semantic_fingerprint=FP,
        comparison_rule_ref=RULE,
        comparison_rule_version=1,
        comparison_rule_fingerprint="fp:rule",
        derivation_binding_ref="binding:1",
        baseline_selector_spec_fingerprint=SEL_FP,
        baseline_measurement_refs=("obs:b",),
        comparison_measurement_refs=("obs:c",),
        selected_baseline_measurement_ref="obs:b",
        absolute_delta=1.0,
        relative_delta=0.5,
        delta_operator=DeltaOperator.ABSOLUTE_DELTA,
        change_kind=ChangeKind.INCREASE,
        unit="count",
        source_measurement_refs=("obs:b", "obs:c"),
        measurement_methodology_refs=(R,),
        coverage_requirement_status=CoverageRequirementStatus.UNRESOLVED,
        coverage_observation_state=CoverageObservationState.NOT_APPLICABLE,
        coverage_verdict=CoverageVerdict.UNKNOWN,
        missingness="OBSERVED",
        comparability_status=TemporalComparabilityStatus.COMPARABLE,
    )
    base.update(kw)
    return ChangeObservation(**base)


# -- scope: exactly two authority-bearing classes ---------------------------


def test_exactly_two_authority_bearing_classes() -> None:
    """G-8: contract count == 2; HIDDEN_THIRD_CONTRACT == NONE."""

    from crypto_systems_intelligence_atlas import book6_comparison_contracts as m

    models = {
        name: obj
        for name, obj in vars(m).items()
        if isinstance(obj, type)
        and issubclass(obj, Book6FrozenModel)
        and obj is not Book6FrozenModel
        and obj.__module__ == m.__name__
    }
    assert set(models) == {
        "BaselineSelectorSpec",
        "ChangeObservation",
        "ComparisonRule",
    }, f"unexpected model classes: {sorted(models)}"
    # Two of the three are authority-bearing; the selector is nested content.
    authority = set(models) - {"BaselineSelectorSpec"}
    assert authority == {"ComparisonRule", "ChangeObservation"}


def test_baseline_selector_spec_is_not_authority_bearing() -> None:
    """5E: the selector is nested rule content, not a third contract class."""

    spec = _selector()
    for forbidden in ("register", "ratify", "lookup", "version", "supersedes_ref"):
        assert not hasattr(spec, forbidden), f"selector must not have {forbidden}"
    assert not hasattr(spec, "comparison_rule_id")
    assert _rule().baseline_selector == spec


def test_comparison_contract_error_is_the_single_error_type() -> None:
    assert issubclass(ComparisonContractError, ValueError)
    assert {ChangeAxis.MEASUREMENT_CHANGE} == set(ChangeAxis)


# -- GAP-5: reserved selector names are refused at construction -----------


@pytest.mark.parametrize("kind", sorted(RESERVED_NOT_EXECUTABLE_SELECTORS, key=str))
def test_reserved_selector_kinds_are_rejected(kind) -> None:
    """grammar v0.6 §2.2.3: reserved names carry no placeholder behaviour."""

    refused("RESERVED_NOT_EXECUTABLE", _selector, kind=kind)


def test_reserved_kind_is_also_refused_through_the_rule() -> None:
    """The refusal is structural, so naming one through a rule also fails."""

    refused(
        "RESERVED_NOT_EXECUTABLE",
        lambda: _rule(baseline_selector=_selector(kind=BaselineSelectorKind.ROLLING_MEAN)),
    )


def test_only_one_selector_is_executable() -> None:
    assert EXECUTABLE_BASELINE_SELECTOR is BaselineSelectorKind.PRIOR_COMPARABLE_WINDOW
    assert len(RESERVED_NOT_EXECUTABLE_SELECTORS) == 4
    assert not (RESERVED_NOT_EXECUTABLE_SELECTORS & {EXECUTABLE_BASELINE_SELECTOR})


def test_ordering_policy_is_single_valued() -> None:
    """grammar v0.6 §2.2.4: the only permitted ordering policy."""

    assert len(list(BaselineOrderingPolicy)) == 1
    assert _selector().ordering_policy is (
        BaselineOrderingPolicy.LATEST_PRIOR_VALID_TIME_END_THEN_START_THEN_LEXICAL_REF
    )


# -- GAP-1: closed operator set, finite stored values ---------------------


def test_delta_operator_set_is_closed() -> None:
    assert {d.value for d in DeltaOperator} == {"ABSOLUTE_DELTA", "RELATIVE_DELTA"}


def test_delta_formula_basis_is_not_a_free_string() -> None:
    """AC-18: no free-form formula, no expression language."""

    for banned in ("delta_formula_basis", "formula", "expression"):
        assert banned not in ComparisonRule.model_fields
        assert banned not in ChangeObservation.model_fields
    refused("Extra inputs", _rule, delta_formula_basis="post - baseline")


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
@pytest.mark.parametrize("field", ["absolute_delta", "relative_delta"])
def test_non_finite_deltas_are_refused(bad, field) -> None:
    """GAP-1: finite input required; no sentinel that reads as a result."""

    refused("finite", _change, **{field: bad})


def test_absent_delta_is_never_zero() -> None:
    """AC-17: absence is single-meaning, and distinct from a computed 0."""

    obs = _change(change_kind=ChangeKind.CHANGE_UNDEFINED,
                  absolute_delta=None, relative_delta=None)
    assert obs.absolute_delta is None
    zero = _change(change_kind=ChangeKind.NO_CHANGE,
                   absolute_delta=0.0, relative_delta=None)
    assert zero.absolute_delta == 0.0 and zero.absolute_delta is not None


def test_no_change_requires_exact_canonical_equality() -> None:
    """plan v0.4 §5: NO_CHANGE means exact equality, not insignificance."""

    assert _change(change_kind=ChangeKind.NO_CHANGE, absolute_delta=0.0,
                   relative_delta=None).change_kind is ChangeKind.NO_CHANGE
    for banned in ("epsilon", "tolerance", "materiality", "significance"):
        assert banned not in ChangeObservation.model_fields
        assert banned not in ComparisonRule.model_fields


# -- GAP-2: same-metric exact-unit identity --------------------------------


def test_no_unit_conversion_surface() -> None:
    """2D: a rule may cite unit requirements and never redefine mathematics."""

    assert "unit_requirements" in ComparisonRule.model_fields
    for banned in ("unit_divisibility_policy", "unit_conversion"):
        assert banned not in ComparisonRule.model_fields


# -- R-5: supersession single meaning --------------------------------------


def test_first_version_must_not_declare_supersession() -> None:
    refused("must not carry", _rule, version=1, supersedes_ref="cmp:1@v1")


def test_later_version_must_declare_supersession() -> None:
    refused("must declare", _rule, version=2)
    assert _rule(version=2, supersedes_ref="cmp:1@v1").version == 2


# -- R-2 / R-3: coverage single meaning ------------------------------------


@pytest.mark.parametrize(
    "status",
    [CoverageRequirementStatus.REQUIRED, CoverageRequirementStatus.NOT_APPLICABLE],
)
def test_coverage_source_ref_required_when_a_determination_is_asserted(status) -> None:
    refused("coverage_applicability_source_ref is required", _rule,
            coverage_requirement_status=status)


def test_coverage_rule_ref_only_when_required() -> None:
    refused("coverage_sufficiency_rule_ref is required", _rule,
            coverage_requirement_status=CoverageRequirementStatus.REQUIRED,
            coverage_applicability_source_ref="cov:src")
    ok = _rule(coverage_requirement_status=CoverageRequirementStatus.REQUIRED,
               coverage_applicability_source_ref="cov:src",
               coverage_sufficiency_rule_ref="cov:rule")
    assert ok.coverage_sufficiency_rule_ref == "cov:rule"
    refused("must be absent", _rule,
            coverage_requirement_status=CoverageRequirementStatus.UNRESOLVED,
            coverage_sufficiency_rule_ref="cov:rule")


def test_coverage_observation_ref_iff_present() -> None:
    """R-3: the discriminator and the ref are one fact, not two."""

    refused("required when", _change,
            coverage_observation_state=CoverageObservationState.PRESENT)
    ok = _change(coverage_observation_state=CoverageObservationState.PRESENT,
                 coverage_observation_ref="cov:obs")
    assert ok.coverage_observation_ref == "cov:obs"
    for absent in (CoverageObservationState.UNAVAILABLE,
                   CoverageObservationState.NOT_APPLICABLE):
        refused("must be absent", _change,
                coverage_observation_state=absent,
                coverage_observation_ref="cov:obs")


def test_not_applicable_is_a_real_state_not_an_absence() -> None:
    """AC-17: NOT_APPLICABLE is never an absence encoding."""

    assert {s.value for s in CoverageObservationState} == {
        "PRESENT",
        "UNAVAILABLE",
        "NOT_APPLICABLE",
    }


def test_coverage_verdict_is_closed() -> None:
    assert {v.value for v in CoverageVerdict} == {
        "SUFFICIENT",
        "INSUFFICIENT",
        "UNKNOWN",
    }


# -- GAP-4: temporal comparability has a domain and a producer -------------


def test_temporal_comparability_status_is_closed_three() -> None:
    assert {s.value for s in TemporalComparabilityStatus} == {
        "COMPARABLE",
        "NOT_COMPARABLE",
        "UNRESOLVED",
    }


def test_unresolved_never_maps_to_not_comparable() -> None:
    """grammar v0.5 §3.4: absence of basis is not a structural failure."""

    refused("never mapped to NOT_COMPARABLE", _change,
            comparability_status=TemporalComparabilityStatus.UNRESOLVED,
            change_kind=ChangeKind.NOT_COMPARABLE,
            comparability_refusal_reasons=(("coverage", "UNRESOLVED"),))


def test_unresolved_maps_to_insufficient_data() -> None:
    obs = _change(comparability_status=TemporalComparabilityStatus.UNRESOLVED,
                  change_kind=ChangeKind.INSUFFICIENT_DATA,
                  selected_baseline_measurement_ref=None,
                  absolute_delta=None, relative_delta=None,
                  comparability_refusal_reasons=(("coverage_applicability", "UNRESOLVED"),))
    assert obs.change_kind is ChangeKind.INSUFFICIENT_DATA


def test_not_comparable_maps_to_not_comparable() -> None:
    obs = _change(comparability_status=TemporalComparabilityStatus.NOT_COMPARABLE,
                  change_kind=ChangeKind.NOT_COMPARABLE,
                  selected_baseline_measurement_ref=None,
                  absolute_delta=None, relative_delta=None,
                  comparability_refusal_reasons=(("unit", "mismatch"),))
    assert obs.change_kind is ChangeKind.NOT_COMPARABLE


def test_comparable_cannot_carry_a_non_comparable_kind() -> None:
    refused("contradictory", _change, change_kind=ChangeKind.NOT_COMPARABLE)
    refused("contradictory", _change, change_kind=ChangeKind.INSUFFICIENT_DATA)


@pytest.mark.parametrize(
    "status,kind,baseline",
    [
        (TemporalComparabilityStatus.NOT_COMPARABLE, ChangeKind.NOT_COMPARABLE, None),
        (TemporalComparabilityStatus.UNRESOLVED, ChangeKind.INSUFFICIENT_DATA, None),
    ],
)
def test_a_decision_status_requires_a_producer(status, kind, baseline) -> None:
    """GAP-4 closes the v0.4 defect: the status must name its producing gate."""

    refused("producing gate", _change,
            comparability_status=status, change_kind=kind,
            selected_baseline_measurement_ref=baseline,
            absolute_delta=None, relative_delta=None,
            comparability_refusal_reasons=())


def test_a_recording_status_needs_no_refusal_reason() -> None:
    assert _change().comparability_refusal_reasons == ()


# -- baseline presence ------------------------------------------------------


def test_selected_baseline_presence_tracks_resolution() -> None:
    refused("selected_baseline_measurement_ref is required", _change,
            selected_baseline_measurement_ref=None)
    refused("selected_baseline_measurement_ref must be absent", _change,
            change_kind=ChangeKind.INSUFFICIENT_DATA,
            comparability_status=TemporalComparabilityStatus.UNRESOLVED,
            comparability_refusal_reasons=(("baseline", "UNRESOLVED"),))


@pytest.mark.parametrize("field", ["baseline_measurement_refs", "comparison_measurement_refs"])
def test_baseline_and_comparison_refs_are_non_empty(field) -> None:
    refused("at least 1", _change, **{field: ()})


# -- the four removed policy surfaces --------------------------------------


def test_removed_policy_fields_do_not_exist() -> None:
    """plan v0.4 §0: four policy surfaces deleted, one reduced to an enum."""

    for banned in (
        "direction_derivation",
        "zero_baseline_policy",
        "unit_divisibility_policy",
        "rounding_precision_policy",
    ):
        assert banned not in ComparisonRule.model_fields
        assert banned not in ChangeObservation.model_fields


def test_phantom_benchmark_field_does_not_exist() -> None:
    """boundary v0.4: the phantom benchmark field was removed, not re-added."""

    for banned in ("baseline_selection_methodology_ref", "benchmark_rule_ref",
                   "benchmark_methodology_ref"):
        assert banned not in ComparisonRule.model_fields
        assert banned not in ChangeObservation.model_fields


def test_display_metadata_is_presentation_only() -> None:
    """plan v0.4 §0 repair 5: display precision is outside every derivation."""

    rule = _rule(display_metadata={"decimals": 2})
    obs = _change(display_metadata={"decimals": 2})
    assert rule.display_metadata["decimals"] == 2
    assert obs.display_metadata["decimals"] == 2
    # Presentation lives in its own field; nothing above reads it.
    assert "display_metadata" in ComparisonRule.model_fields


# -- immutability -----------------------------------------------------------


def test_records_are_frozen() -> None:
    rule = _rule()
    with pytest.raises(ValidationError):
        rule.version = 2  # type: ignore[misc]


def test_records_forbid_extra_fields() -> None:
    refused("Extra inputs", _rule, score=0.9)
    refused("Extra inputs", _change, health_score=1.0)


def test_model_copy_cannot_smuggle_a_field() -> None:
    """The anti-score firewall must hold against model_copy, not just __init__."""

    with pytest.raises(ValueError, match="extra='forbid'"):
        _rule().model_copy(update={"score": 0.9})
    with pytest.raises(ValueError, match="extra='forbid'"):
        _change().model_copy(update={"health_score": 1.0})
    assert math.isclose(_change().absolute_delta, 1.0)
