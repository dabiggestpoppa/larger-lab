"""Book 6 normalization — D6M-2 = B (SEPARATE_NORMALIZATION_RULE).

The ratified doctrine under test:

- normalization is a separate first-class contract, never a flag on a metric
  definition and never an untyped transform hidden inside a methodology;
- ``NORMALIZED_WITHOUT_NATIVE_LINEAGE = INVALID`` — and the lineage may not be
  stripped after construction, nor re-pointed at a different native set;
- ``PERCENTILE_WITHIN_COHORT`` is REJECTED and must not exist as an enum value
  merely because a planning corpus once mentioned ranking;
- cohort-relative and dividing normalizations must name what they are relative
  to, so there is no implicit "all chains" total and no implicit divisor.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book6_core import Book6EngineError
from crypto_systems_intelligence_atlas.book6_grammar import (
    NORMALIZATION_INVALID_FOR,
    NormalizationType,
    WindowClass,
    windows_are_comparable,
)
from crypto_systems_intelligence_atlas.book6_normalization import (
    COHORT_SCOPED_NORMALIZATIONS,
    DIVIDING_NORMALIZATIONS,
    NORMALIZED_WITHOUT_NATIVE_LINEAGE_IS_INVALID,
    PERCENTILE_NORMALIZATION_IS_REJECTED,
    Cohort,
    CohortDimension,
    NormalizationRuleError,
    NormalizationRule,
    NormalizedMeasurement,
    check_normalization_admissibility,
    check_windows_comparable,
    validate_native_lineage,
)
from crypto_systems_intelligence_atlas.book6_support import (
    T1,
    build_engine_with_definitions,
    definition,
    windowed_observation,
)
from crypto_systems_intelligence_atlas.book6_definitions import MetricDefinition
from crypto_systems_intelligence_atlas.book6_grammar import MissingnessState

CLAIM = "fixture:claim:measurement"
NATIVE_OBSERVATION = "obs:native"
NATIVE_METRIC = "metric.native.native_transactions"
NORMALIZED_METRIC = "metric.normalized.transactions_per_user"
RULE_ID = "normrule:per_user:1"


def _rule(**overrides: object) -> NormalizationRule:
    payload: dict[str, object] = {
        "normalization_rule_id": RULE_ID,
        "input_metric_definition_ref": NATIVE_METRIC,
        "input_measurement_refs": (NATIVE_OBSERVATION,),
        "normalization_type": NormalizationType.PER_USER,
        "transformation": "x = native_transactions / distinct_users",
        "denominator_ref": "den:distinct-users",
        "cohort_ref": "cohort:pos@1",
        "methodology_ref": "book6-methodology",
        "valid_time": T1,
        "version": "1",
        "output_metric_definition_ref": NORMALIZED_METRIC,
    }
    payload.update(overrides)
    return NormalizationRule(**payload)  # type: ignore[arg-type]


def _product(**overrides: object) -> NormalizedMeasurement:
    payload: dict[str, object] = {
        "normalized_measurement_id": "norm:tx_per_user:1",
        "normalization_rule_id": RULE_ID,
        "native_measurement_refs": (NATIVE_OBSERVATION,),
        "normalized_metric_definition_ref": NORMALIZED_METRIC,
        "value": 3.5,
        "unit": "transactions-per-user",
        "cohort_ref": "cohort:pos@1",
        "valid_time": T1,
    }
    payload.update(overrides)
    return NormalizedMeasurement(**payload)  # type: ignore[arg-type]


def _stack():
    """A registered native measurement with a live, current Book 2 citation."""

    engine = build_engine_with_definitions(
        definition(NATIVE_METRIC),
        definition(NORMALIZED_METRIC, unit="transactions-per-user"),
    )
    engine.registry.register_measurement(
        windowed_observation(
            NATIVE_OBSERVATION,
            NATIVE_METRIC,
            value=7.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
        )
    )
    return engine


# -- the contract is separate and complete -----------------------------------


def test_normalization_rule_requires_every_ratified_field() -> None:
    """A normalization is not a bare type flag: eleven named fields are bound."""

    fields = set(NormalizationRule.model_fields)
    assert fields == {
        "normalization_rule_id",
        "input_metric_definition_ref",
        "input_measurement_refs",
        "normalization_type",
        "transformation",
        "denominator_ref",
        "cohort_ref",
        "methodology_ref",
        "valid_time",
        "version",
        "output_metric_definition_ref",
    }


def test_normalization_is_not_a_field_on_the_metric_definition() -> None:
    """D6M-2 = B: the definition carries no untyped normalization flag."""

    fields = set(MetricDefinition.model_fields)
    assert "normalized" not in fields
    assert "normalize" not in fields
    assert "normalization" not in fields


def test_normalization_is_not_a_field_on_the_measurement_observation() -> None:
    from crypto_systems_intelligence_atlas.book6_records import MeasurementObservation

    forbidden = {"normalized", "is_normalized", "normalization", "normalization_ref"}
    assert forbidden.isdisjoint(set(MeasurementObservation.model_fields))


def test_normalization_rule_requires_native_input_measurements() -> None:
    with pytest.raises(ValidationError):
        _rule(input_measurement_refs=())


def test_normalized_product_requires_native_lineage_at_construction() -> None:
    with pytest.raises(ValidationError):
        _product(native_measurement_refs=())


# -- dividing normalizations must name their divisor -------------------------


@pytest.mark.parametrize(
    "normalization_type",
    sorted(t for t in NormalizationType if t in DIVIDING_NORMALIZATIONS),
    ids=lambda t: t.value,
)
def test_dividing_normalization_requires_a_denominator(
    normalization_type: NormalizationType,
) -> None:
    payload = {"normalization_type": normalization_type}
    if normalization_type in COHORT_SCOPED_NORMALIZATIONS:
        payload["cohort_ref"] = "cohort:pos@1"
    with pytest.raises(ValidationError, match="divides and"):
        _rule(denominator_ref=None, **payload)


@pytest.mark.parametrize(
    "normalization_type",
    sorted(t for t in NormalizationType if t not in DIVIDING_NORMALIZATIONS),
    ids=lambda t: t.value,
)
def test_non_dividing_normalization_needs_no_denominator(
    normalization_type: NormalizationType,
) -> None:
    payload = {"normalization_type": normalization_type, "denominator_ref": None}
    if normalization_type in COHORT_SCOPED_NORMALIZATIONS:
        payload["cohort_ref"] = "cohort:pos@1"
    rule = _rule(**payload)
    assert rule.denominator_ref is None


# -- cohort-relative normalizations must name the cohort ---------------------


@pytest.mark.parametrize(
    "normalization_type", sorted(COHORT_SCOPED_NORMALIZATIONS), ids=lambda t: t.value
)
def test_cohort_relative_normalization_requires_a_cohort(
    normalization_type: NormalizationType,
) -> None:
    with pytest.raises(ValidationError, match="cohort-relative"):
        _rule(
            normalization_type=normalization_type, cohort_ref=None, denominator_ref="den:x"
        )


def test_share_of_total_is_cohort_relative() -> None:
    assert NormalizationType.SHARE_OF_TOTAL in COHORT_SCOPED_NORMALIZATIONS


# -- NATIVE_BEFORE_NORMALIZED / lineage integrity ----------------------------


def test_validated_lineage_passes() -> None:
    rule = _rule()
    validate_native_lineage(_product(), rule)


def test_lineage_pointed_at_a_different_native_set_is_refused() -> None:
    with pytest.raises(NormalizationRuleError, match="does not match rule inputs"):
        validate_native_lineage(_product(native_measurement_refs=("obs:other",)), _rule())


def test_lineage_cannot_be_widened_by_appending_fabricated_inputs() -> None:
    with pytest.raises(NormalizationRuleError, match="does not match rule inputs"):
        validate_native_lineage(
            _product(native_measurement_refs=("obs:native", "obs:invented")), _rule()
        )


def test_product_citing_another_rule_is_refused() -> None:
    with pytest.raises(NormalizationRuleError, match="cites rule"):
        validate_native_lineage(_product(normalization_rule_id="normrule:other"), _rule())


def test_product_output_metric_must_match_the_rule() -> None:
    with pytest.raises(NormalizationRuleError, match="output metric definition"):
        validate_native_lineage(
            _product(normalized_metric_definition_ref="metric.normalized.something"), _rule()
        )


def test_model_copy_cannot_strip_lineage_and_still_authorize() -> None:
    """``model_copy`` does not revalidate; the decision boundary must."""

    stripped = _product().model_copy(update={"native_measurement_refs": ()})
    with pytest.raises(NormalizationRuleError, match="NORMALIZED_WITHOUT_NATIVE_LINEAGE"):
        validate_native_lineage(stripped, _rule())


def test_model_copy_repointing_lineage_is_refused_at_use() -> None:
    repointed = _product().model_copy(
        update={"native_measurement_refs": ("obs:unrelated",)}
    )
    with pytest.raises(NormalizationRuleError):
        validate_native_lineage(repointed, _rule())


def test_lineage_invariant_constant_is_true() -> None:
    assert NORMALIZED_WITHOUT_NATIVE_LINEAGE_IS_INVALID is True


def test_normalized_without_native_lineage_is_invalid_end_to_end() -> None:
    engine = _stack()
    engine.registry.register_normalization_rule(_rule())
    stripped = _product().model_copy(update={"native_measurement_refs": ()})
    with pytest.raises(Book6EngineError):
        engine.normalize(stripped, _rule())


# -- PERCENTILE_WITHIN_COHORT is rejected ------------------------------------


def test_percentile_is_not_a_normalization_type() -> None:
    assert "PERCENTILE_WITHIN_COHORT" not in {t.value for t in NormalizationType}


def test_no_normalization_member_contains_percentile_or_rank() -> None:
    for member in NormalizationType:
        assert "PERCENTILE" not in member.value
        assert "RANK" not in member.value


def test_percentile_cannot_be_constructed_even_as_a_raw_string() -> None:
    with pytest.raises(ValidationError):
        _rule(normalization_type="PERCENTILE_WITHIN_COHORT")


def test_percentile_cannot_be_injected_by_model_copy() -> None:
    """A forged rule object cannot introduce a rejected normalization type.

    ``model_copy`` does not coerce, so the forged value is not an enum member —
    and the engine does not trust the caller's rule object at all: it
    re-resolves the REGISTERED rule and validates the product against that.
    """
    engine = _stack()
    engine.registry.register_normalization_rule(_rule())
    forged = _rule().model_copy(update={"normalization_type": "PERCENTILE_WITHIN_COHORT"})
    assert forged.normalization_type not in set(NormalizationType)
    # The registered PER_USER rule governs; the forged percentile never reaches
    # the admissibility check and cannot widen what a normalized value may be.
    assert engine.registry.normalized_rule(RULE_ID).normalization_type is (
        NormalizationType.PER_USER
    )
    engine.normalize(_product(), forged)
    product = _product()
    assert engine.normalize(product, _rule()) is product


def test_percentile_rejection_constant_is_true() -> None:
    assert PERCENTILE_NORMALIZATION_IS_REJECTED is True


# -- admissibility is scoped to metric x cohort x methodology -----------------


def test_per_user_is_invalid_for_a_ratio_metric() -> None:
    from crypto_systems_intelligence_atlas.book6_grammar import MeasurementCategory

    with pytest.raises(NormalizationRuleError, match="structurally invalid"):
        check_normalization_admissibility(
            _rule(), input_category=MeasurementCategory.RATIO
        )


def test_per_user_is_valid_for_a_stock_metric() -> None:
    from crypto_systems_intelligence_atlas.book6_grammar import MeasurementCategory

    check_normalization_admissibility(
        _rule(), input_category=MeasurementCategory.STOCK
    )


def test_admissibility_table_covers_the_ratified_categories() -> None:
    from crypto_systems_intelligence_atlas.book6_grammar import MeasurementCategory

    assert set(NORMALIZATION_INVALID_FOR) == {
        MeasurementCategory.RATIO,
        MeasurementCategory.COUNT,
    }


# -- cohort contract ----------------------------------------------------------


def test_cohort_requires_named_dimensions_and_members() -> None:
    with pytest.raises(ValidationError):
        Cohort(cohort_id="c", version="1", dimensions=(), member_refs=("a",))
    with pytest.raises(ValidationError):
        Cohort(cohort_id="c", version="1", dimensions=(CohortDimension.CHAIN_ROLE,), member_refs=())


def test_cohort_membership_is_explicit_not_implicit_all_chains() -> None:
    cohort = Cohort(
        cohort_id="cohort:pos@1",
        version="1",
        dimensions=(CohortDimension.ARCHITECTURE_FAMILY,),
        member_refs=("chain:alpha", "chain:beta"),
    )
    assert cohort.contains("chain:alpha") is True
    assert cohort.contains("chain:gamma") is False


def test_cohort_may_not_list_a_subject_twice() -> None:
    with pytest.raises(ValidationError, match="may not list the same subject twice"):
        Cohort(
            cohort_id="cohort:pos@1",
            version="1",
            dimensions=(CohortDimension.ARCHITECTURE_FAMILY,),
            member_refs=("chain:alpha", "chain:alpha"),
        )


def test_cohort_identity_carries_its_version() -> None:
    cohort = Cohort(
        cohort_id="cohort:pos@1",
        version="1",
        dimensions=(CohortDimension.ARCHITECTURE_FAMILY,),
        member_refs=("chain:alpha",),
    )
    assert cohort.version == "1"
    # a cohort change is a new version and never rewrites prior comparisons
    assert cohort.cohort_id.endswith("@1")


def test_every_ratified_cohort_dimension_exists() -> None:
    assert {d.value for d in CohortDimension} == {
        "ARCHITECTURE_FAMILY",
        "ECONOMIC_FUNCTION",
        "PROTOCOL_ROLE",
        "CHAIN_ROLE",
        "MATURITY_BAND",
        "DEPLOYMENT_ENVIRONMENT",
        "SECURITY_MODEL",
    }


# -- window comparability -----------------------------------------------------


def test_windows_of_the_same_class_are_comparable() -> None:
    assert windows_are_comparable(WindowClass.CALENDAR_MONTH, WindowClass.CALENDAR_MONTH)
    check_windows_comparable(WindowClass.CALENDAR_MONTH, WindowClass.CALENDAR_MONTH)


def test_windows_of_different_classes_are_not_comparable() -> None:
    assert windows_are_comparable(WindowClass.ROLLING, WindowClass.CALENDAR_MONTH) is False
    with pytest.raises(NormalizationRuleError, match="not comparable"):
        check_windows_comparable("ROLLING", "CALENDAR_MONTH")


def test_a_seven_day_window_is_not_a_thirty_day_window() -> None:
    with pytest.raises(NormalizationRuleError, match="not comparable"):
        check_windows_comparable(WindowClass.ROLLING.value, WindowClass.CALENDAR_MONTH.value)


# -- engine authorization -----------------------------------------------------


def test_engine_authorizes_a_fully_lineaged_normalized_product() -> None:
    engine = _stack()
    engine.registry.register_normalization_rule(_rule())
    product = _product()
    assert engine.normalize(product, _rule()) is product


def test_engine_refuses_a_product_whose_native_input_is_not_registered() -> None:
    engine = _stack()
    engine.registry.register_normalization_rule(
        _rule(input_measurement_refs=(NATIVE_OBSERVATION, "obs:missing"))
    )
    with pytest.raises(Exception):
        engine.normalize(_product(), _rule())


def test_engine_refuses_an_unregistered_normalization_rule() -> None:
    engine = _stack()
    with pytest.raises(Exception):
        engine.normalize(_product(), _rule())


def test_engine_refuses_a_forged_rule_identity() -> None:
    engine = _stack()
    engine.registry.register_normalization_rule(_rule())
    forged = _rule().model_copy(update={"normalization_rule_id": "normrule:forged"})
    with pytest.raises(Exception):
        engine.normalize(_product(), forged)


def test_normalized_products_are_never_registered_as_native_measurements() -> None:
    """A normalized product is a distinct role, not a native observation."""

    engine = _stack()
    engine.registry.register_normalization_rule(_rule())
    engine.normalize(_product(), _rule())
    assert engine.registry.registered_refs() == (NATIVE_OBSERVATION,)
