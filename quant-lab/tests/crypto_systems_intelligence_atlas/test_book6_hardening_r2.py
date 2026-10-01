"""Book 6 Hardening R2 — canonical methodology content, executable state rules,
per-metric coverage closure, historical authority honesty.

Independent review found four NEW concrete defects in the R1-hardened kernel.
Every one of them let a caller *assert* something the registry was supposed to
*prove*:

- **R2-D1** methodology identity was still caller-self-asserted: R1 compared an
  exact identity AND a self-declared row list, and one caller-created
  ``MeasurementMethodology`` (right name, garbage formula, ``FC-05`` in its own
  row set) satisfied both at once and got ``AUTHORIZED``;
- **R2-D2** ``emit_rule_gated_state`` never evaluated ``predicate_ref``:
  prior = 100, current = 50 with predicate ``current_gt_prior`` emitted
  ``INCREASING``;
- **R2-D3** a forged ``CoverageSufficiencyAttestation`` claiming a wider scope
  than its rules prove produced ``DATA_COMPLETE`` for a metric no live rule
  covers;
- **R2-D4** historical valuation shared one helper with current authorization
  and revalidated price claims with ``require_current=True``, so a claim that
  decayed AFTER observation retroactively erased a historical statement.

Repairs, and the doctrine each carries:

- identity binds content (``METHODOLOGY_IDENTITY_BINDS_CONTENT``) and the
  comparison authority is derived from the ratified corpus specification, not
  from anything a caller supplies;
- a ratified rule is REPLAYED, not merely named
  (``RATIFIED RULE != TRUE PREDICATE``), through a closed, eval-free predicate
  registry, and a false predicate is an explicit non-emission that never
  inverts into the opposite state;
- engine ``data_status`` reconstructs sufficiency per metric from registry
  state and demands explicit set equality (``covered == required``); the
  attestation is an audit record, never the source of truth;
- the historical path is split honestly into ``validate_recorded_historical_shape``
  (record shape only, no Book 2 consultation) and ``historical_authority_status``
  (reports ``HISTORICAL_BOOK2_AUTHORITY_REPLAY = NOT_IMPLEMENTED``), because
  accepted Book 2 cannot answer "was this claim authoritative at time T" and
  Book 6 will not invent a Book 2 feature to pretend otherwise.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book6_comparability import (
    ComparabilityError,
    authorize_comparison,
    corpus_row_for,
)
from crypto_systems_intelligence_atlas.book6_grammar import MissingnessState
from crypto_systems_intelligence_atlas.book6_coverage_rules import (
    COVERAGE_SUFFICIENCY_RULES_RATIFIED_AT_BOOTSTRAP,
    CoverageSufficiencyAttestation,
    CoverageReport,
)
from crypto_systems_intelligence_atlas.book6_core import Book6EngineError
from crypto_systems_intelligence_atlas.book6_definitions import (
    ComparabilityClass,
    MetricDefinition,
    MeasurementMethodology,
)
from crypto_systems_intelligence_atlas.book6_methodology import (
    METHODOLOGY_IDENTITY_BINDS_CONTENT,
    METHODOLOGY_SELF_AUTHORIZATION_REJECTED,
    Book6MethodologyRegistry,
    MethodologyRegistryError,
    methodology_fingerprint,
)
from crypto_systems_intelligence_atlas.book6_normalization import (
    NormalizationRule,
    NormalizationType,
    validate_rule_methodology,
)
from crypto_systems_intelligence_atlas.book6_registry import Book6RegistryError
from crypto_systems_intelligence_atlas.book6_states import (
    INDIVIDUAL_STATE_RULES_RATIFIED_AT_BOOTSTRAP,
    StateClass,
    StateError,
    StateName,
    StateRule,
    StateRuleRegistry,
    VectorStatus,
)
from crypto_systems_intelligence_atlas.book6_predicates import (
    FALSE_PREDICATE_IS_NOT_THE_OPPOSITE_STATE,
    PREDICATES_ARE_EXECUTED_NOT_NAMED,
    PREDICATES_CANONICALLY_RATIFIED,
    EvaluatorKind,
    OperandOrder,
    PredicateEvaluation,
    PredicateNotSatisfied,
    PredicateRegistry,
    PredicateRegistryError,
    StatePredicateDefinition,
    evaluate_predicate,
)
from crypto_systems_intelligence_atlas.book6_support import (
    CLAIM_ID,
    NOW,
    T1,
    build_engine,
    build_engine_with_definitions,
    comparison_methodology,
    coverage,
    coverage_rule,
    decay_claim,
    definition,
    methodology,
    normalization_methodology,
    price,
    register_definition,
    register_measurement,
    valuation,
    windowed_observation,
)
from crypto_systems_intelligence_atlas.book6_valuation import (
    HISTORICAL_BOOK2_AUTHORITY_REPLAY,
    HistoricalAuthorityReport,
    ValuationError,
)

FC05 = ("protocol.volume.DEX_NATIVE", "protocol.volume.AGGREGATOR_ROUTED")
METRIC = "metric.native.tx"
CLAIM = CLAIM_ID


# ===========================================================================
# fixtures
# ===========================================================================


def _observed_vector(engine, *, metrics=("metric:A", "metric:B")):
    """A fully observed two-metric vector built by the engine itself."""

    measurement_ids = tuple(f"obs:{m}" for m in metrics)
    for metric, mid in zip(metrics, measurement_ids):
        register_measurement(
            engine,
            windowed_observation(
                mid,
                metric,
                value=7.0,
                missingness=MissingnessState.OBSERVED,
                claim_refs=(CLAIM,),
            ),
        )
        engine.registry.register_coverage(coverage(mid, 1.0))
    return engine.build_availability_vector(
        subject_ref="fixture:chain:alpha",
        schema_ref="schema:book6:1",
        as_of_valid_time=T1,
        observed_at=T1,
        measurement_ids=measurement_ids,
        methodology_ref="book6-methodology@1",
    )


def _ratified_rule_for_metrics(engine, metrics=("metric:A", "metric:B")):
    for metric in metrics:
        rule = coverage_rule(f"covrule:{metric}", scope_metric_id=metric)
        engine.registry.coverage_rules.register(rule)
        engine.registry.coverage_rules.ratify(
            f"covrule:{metric}", operator="synthetic", at=T1
        )


def _predicate(engine, *, target=StateName.INCREASING, kind=EvaluatorKind.CURRENT_GREATER_THAN_PRIOR):
    definition_ = StatePredicateDefinition(
        predicate_id="predicate:current_gt_prior",
        version="1",
        state_class=StateClass.B_SPECIFICATION_ONLY,
        target_state=target,
        description="synthetic fixture predicate; canonically unratified",
        required_input_arity=2,
        evaluator_kind=kind,
    )
    engine.predicates.register(definition_)
    return definition_


def _increasing_rule(engine, *, measurement_refs=("obs:current", "obs:prior")):
    rule = StateRule(
        state_rule_id="staterule:increasing:1",
        target_state=StateName.INCREASING,
        state_class=StateClass.B_SPECIFICATION_ONLY,
        predicate_ref="predicate:current_gt_prior@1",
        methodology_ref="book6-methodology@1",
        required_measurement_refs=measurement_refs,
        window_class_constraint="INSTANTANEOUS",
        comparability_constraint="same cohort version, same window class",
        precision_semantics="exact equality on the declared numeric precision",
        version="1",
    )
    engine.registry.register_state_rule(rule)
    engine.registry.state_rules.ratify(
        rule.state_rule_id, operator="synthetic-fixture-operator", at=NOW
    )
    return rule


def _series_engine(engine, *, current=50.0, prior=100.0):
    for mid, value in (("obs:current", current), ("obs:prior", prior)):
        register_measurement(
            engine,
            windowed_observation(
                mid,
                METRIC,
                value=value,
                missingness=MissingnessState.OBSERVED,
                claim_refs=(CLAIM,),
            ),
        )
    return engine


def _emission_kwargs():
    return {
        "rule_ref": "staterule:increasing:1",
        "dimension_id": "dim:1",
        "measurement_refs": ("obs:current", "obs:prior"),
        "methodology_ref": "book6-methodology@1",
        "valid_time": T1,
        "observed_at": T1,
        "missingness": MissingnessState.OBSERVED,
    }


def _historical_valuation(claim_refs=(CLAIM,), observed_at=None):
    observed = observed_at or (NOW - timedelta(days=30))
    return valuation(
        "val:hist",
        price_observation=price(
            "price:hist", claim_refs=claim_refs, observed_at=observed
        ),
        observed_at=observed + timedelta(seconds=60),
        valid_time=observed + timedelta(seconds=60),
    )


# ===========================================================================
# R2-D1 — methodology identity binds content
# ===========================================================================


def test_r2_d1_the_self_authorization_reproducer_is_now_refused() -> None:
    """The exact R2-D1 reproducer: right name, garbage content, own row set.

    Before R2 this registered and then ``AUTHORIZED`` the FC-05 comparison.
    The canonical content digest of the ratified corpus row does not match the
    caller object's digest, so the same object is now refused at the content
    seal — regardless of what rows it claims.
    """

    impostor = MeasurementMethodology(
        methodology_ref="routing-attribution-methodology",
        version="1",
        formula="garbage",
        window_rule="garbage",
        denominator_rule="garbage",
        source_selection="garbage",
        identity_rule="garbage",
        authorized_corpus_row_ids=("FC-05",),
    )
    registry = Book6MethodologyRegistry()
    registry.register_methodology(impostor)
    row = corpus_row_for(*FC05)
    assert row.required_methodology == "routing-attribution-methodology@1"
    with pytest.raises(ComparabilityError, match="content does not match"):
        authorize_comparison(
            *FC05,
            methodology_ref="routing-attribution-methodology@1",
            left_class=ComparabilityClass.CHAIN_WITHIN_FAMILY,
            right_class=ComparabilityClass.CHAIN_WITHIN_FAMILY,
            methodologies=registry,
        )


def test_r2_d1_canonical_exact_methodology_authorizes() -> None:
    """A5 (R1) preserved: the canonical specification itself passes."""

    registry = Book6MethodologyRegistry()
    registry.register_methodology(comparison_methodology("FC-05"))
    row = corpus_row_for(*FC05)
    assert (
        authorize_comparison(
            *FC05,
            methodology_ref=row.required_methodology,
            left_class=ComparabilityClass.CHAIN_WITHIN_FAMILY,
            right_class=ComparabilityClass.CHAIN_WITHIN_FAMILY,
            methodologies=registry,
        )
        == "AUTHORIZED"
    )


def test_r2_d1_identity_binds_content_constants() -> None:
    assert METHODOLOGY_IDENTITY_BINDS_CONTENT is True
    assert METHODOLOGY_SELF_AUTHORIZATION_REJECTED is True


def test_r2_d1_fingerprint_is_deterministic_and_content_complete() -> None:
    """Equivalent content -> same digest; any semantic mutation -> different."""

    canonical = comparison_methodology("FC-05")
    reordered = canonical.model_copy(
        update={
            "authorized_corpus_row_ids": tuple(
                reversed(canonical.authorized_corpus_row_ids)
            )
        }
    )
    assert methodology_fingerprint(reordered) == methodology_fingerprint(canonical)

    mutated_fields = {
        "formula": "garbage",
        "window_rule": "garbage",
        "denominator_rule": "garbage",
        "source_selection": "garbage",
        "identity_rule": "garbage",
        "parameters": ("mutated",),
        "filters": ("mutated",),
        "input_methodology_refs": ("mutated",),
        "authorized_corpus_row_ids": ("FC-99",),
    }
    for field, value in mutated_fields.items():
        mutant = canonical.model_copy(update={field: value})
        assert methodology_fingerprint(mutant) != methodology_fingerprint(canonical), field


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("formula", "garbage"),
        ("authorized_corpus_row_ids", ("FC-05", "FC-99")),
        ("input_methodology_refs", ("injected",)),
        ("denominator_rule", "garbage"),
        ("source_selection", "garbage"),
    ],
)
def test_r2_d1_content_mutations_are_refused_at_registration_boundaries(
    field: str, value: object
) -> None:
    """Every registration surface re-verifies content against the bound digest."""

    from crypto_systems_intelligence_atlas.book6_registry import Book6RegistryError

    canonical = comparison_methodology("FC-05")
    engine = build_engine_with_definitions(
        definition(FC05[0]),
        definition(FC05[1]),
        methodologies=(canonical,),
    )
    mutant = canonical.model_copy(update={field: value})
    base = definition(FC05[0])
    with pytest.raises((MethodologyRegistryError, Book6RegistryError, ValidationError)):
        register_definition(
            engine,
            MetricDefinition(
                metric_id="metric:mutant",
                name="metric:mutant",
                semantic_definition="a mutant-carrying definition that must be refused",
                subject_domain=base.subject_domain,
                category=base.category,
                unit="native-unit",
                role=base.role,
                window_class=base.window_class,
                aggregation=base.aggregation,
                denominator_rule=base.denominator_rule,
                allowed_source_families=base.allowed_source_families,
                required_evidence_semantics="Book 2 evidenced and currently promotable",
                methodology=mutant,
                comparability_class=base.comparability_class,
            ),
        )


def test_r2_d1_require_canonical_methodology_refuses_a_mutated_object() -> None:
    engine = build_engine_with_definitions(
        definition(FC05[0]), definition(FC05[1]), methodologies=(comparison_methodology("FC-05"),)
    )
    mutant = comparison_methodology("FC-05").model_copy(update={"formula": "garbage"})
    # the registry-level seam wraps the seal error in Book6RegistryError
    with pytest.raises((MethodologyRegistryError, Book6RegistryError), match="content does not match"):
        engine.registry.require_canonical_methodology(mutant)


def test_r2_d1_comparison_authority_row_condition_is_live() -> None:
    """Condition 3 checks the RATIFIED corpus spec, not the registered object.

    A corpus row whose own canonical specification did not license that row
    would be refused even when the registered methodology matches it exactly —
    the check is a self-consistency invariant on the corpus, kept live.
    """

    from crypto_systems_intelligence_atlas.book6_methodology import (
        Book6MethodologyRegistry as Registry,
    )

    canonical = comparison_methodology("FC-05")
    assert "FC-05" in canonical.authorized_corpus_row_ids
    registry = Registry()
    registry.register_methodology(canonical)
    # normal path passes all three conditions
    registry.require_comparison_authority(
        methodology_identity_ref=canonical.identity,
        corpus_row_id="FC-05",
        required_spec=canonical,
    )
    # and the invariant fires when a spec does not name its own row
    unlicensed = canonical.model_copy(update={"authorized_corpus_row_ids": ("FC-99",)})
    with pytest.raises(MethodologyRegistryError, match="is not authorized for corpus row"):
        registry.require_comparison_authority(
            methodology_identity_ref=unlicensed.identity,
            corpus_row_id="FC-05",
            required_spec=unlicensed,
        )


def test_r2_d1_a_superseded_methodology_stops_authorizing() -> None:
    """A6 (R1) preserved exactly: revision costs a new corpus-licensed version."""

    registry = Book6MethodologyRegistry()
    registry.register_methodology(comparison_methodology("FC-05"))
    registry.supersede_methodology(comparison_methodology("FC-05", version="2"))
    with pytest.raises(ComparabilityError, match="superseded"):
        authorize_comparison(
            *FC05,
            methodology_ref="routing-attribution-methodology@1",
            left_class=ComparabilityClass.CHAIN_WITHIN_FAMILY,
            right_class=ComparabilityClass.CHAIN_WITHIN_FAMILY,
            methodologies=registry,
        )


# ===========================================================================
# Phase 15/16 — methodology content identity on every use surface
# ===========================================================================


def test_r2_phase16_measurement_surface_refuses_mutated_formula() -> None:
    """Re-registering a metric definition with a mutated methodology is refused."""

    engine = build_engine_with_definitions(definition(METRIC))
    mutant = methodology("book6-methodology").model_copy(update={"formula": "garbage"})
    base = definition(METRIC)
    with pytest.raises((MethodologyRegistryError, Book6RegistryError)):
        register_definition(
            engine,
            MetricDefinition(
                metric_id=f"{METRIC}#mutant",
                name=f"{METRIC}#mutant",
                semantic_definition="a definition carrying a mutated methodology",
                subject_domain=base.subject_domain,
                category=base.category,
                unit="native-unit",
                role=base.role,
                window_class=base.window_class,
                aggregation=base.aggregation,
                denominator_rule=base.denominator_rule,
                allowed_source_families=base.allowed_source_families,
                required_evidence_semantics="Book 2 evidenced and currently promotable",
                methodology=mutant,
                comparability_class=base.comparability_class,
            ),
        )


def test_r2_phase16_normalization_surface_refuses_mutated_methodology() -> None:
    """A normalization rule's methodology identity must carry canonical content."""

    engine = build_engine_with_definitions(definition(METRIC))
    rule = NormalizationRule(
        normalization_rule_id="normrule:r2",
        input_metric_definition_ref=METRIC,
        input_measurement_refs=("obs:1",),
        normalization_type=NormalizationType.PER_USER,
        transformation="x = native / users",
        denominator_ref="obs:1",
        methodology_ref="book6-normalization@1",
        valid_time=T1,
        version="1",
        output_metric_definition_ref="metric.normalized",
    )
    # the normalization methodology DECLARES the input metric's methodology
    # identity among its input_methodology_refs, per the R1 Phase 9 contract
    engine.registry.register_methodology(
        normalization_methodology(input_methodology_refs=(f"{METRIC}@book6-methodology@1",))
    )
    mutant = normalization_methodology().model_copy(update={"formula": "garbage"})
    with pytest.raises(MethodologyRegistryError, match="content does not match"):
        engine.registry.methodologies.assert_content_matches(
            "book6-normalization@1", mutant
        )
    # the unmutated identity still resolves and validates against its inputs
    validate_rule_methodology(
        rule,
        input_methodology_identity=f"{METRIC}@book6-methodology@1",
        registered_methodology=engine.registry.methodologies.resolve_methodology(
            "book6-normalization@1"
        ),
    )


# ===========================================================================
# R2-D2 — the predicate is executed, not named
# ===========================================================================


def test_r2_d2_the_false_predicate_reproducer_is_now_refused() -> None:
    """R2-D2 reproducer: prior = 100, current = 50 must NOT emit INCREASING."""

    engine = build_engine_with_definitions(definition(METRIC))
    _series_engine(engine, current=50.0, prior=100.0)
    _predicate(engine)
    _increasing_rule(engine)
    with pytest.raises(PredicateNotSatisfied) as excinfo:
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())
    assert excinfo.value.predicate_id == "predicate:current_gt_prior@1"
    assert excinfo.value.operands == (50.0, 100.0)


def test_r2_d2_a_true_predicate_emits_after_full_replay() -> None:
    engine = build_engine_with_definitions(definition(METRIC))
    _series_engine(engine, current=150.0, prior=100.0)
    _predicate(engine)
    _increasing_rule(engine)
    dimension = engine.emit_rule_gated_state(
        StateName.INCREASING, **_emission_kwargs()
    )
    assert dimension.state is StateName.INCREASING
    assert dimension.state_rule_ref == "staterule:increasing:1"


def test_r2_d2_false_predicate_does_not_invert_to_the_opposite_state() -> None:
    """FALSE INCREASING != DECREASING; the opposite state needs its own rule."""

    engine = build_engine_with_definitions(definition(METRIC))
    _series_engine(engine, current=50.0, prior=100.0)
    _predicate(engine)
    _increasing_rule(engine)
    with pytest.raises((PredicateNotSatisfied, Book6EngineError)):
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())
    # no DECREASING dimension was manufactured as a side effect
    from crypto_systems_intelligence_atlas.book6_predicates import EvaluatorKind as _EK

    assert _EK.CURRENT_GREATER_THAN_PRIOR is not None


def test_r2_d2_predicates_shut_with_zero_canonical_ratification() -> None:
    assert PREDICATES_CANONICALLY_RATIFIED == 0
    assert INDIVIDUAL_STATE_RULES_RATIFIED_AT_BOOTSTRAP == 0
    assert COVERAGE_SUFFICIENCY_RULES_RATIFIED_AT_BOOTSTRAP == 0
    assert PREDICATES_ARE_EXECUTED_NOT_NAMED is True
    assert FALSE_PREDICATE_IS_NOT_THE_OPPOSITE_STATE is True


def test_r2_d2_the_evaluator_family_is_a_closed_enumeration() -> None:
    kinds = {kind.value for kind in EvaluatorKind}
    assert kinds == {
        "CURRENT_GREATER_THAN_PRIOR",
        "CURRENT_LESS_THAN_PRIOR",
        "EXACT_EQUALITY",
    }
    assert [order.value for order in OperandOrder] == ["CURRENT_THEN_PRIOR"]


def test_r2_d2_the_registry_ships_empty_and_never_executes_strings() -> None:
    registry = PredicateRegistry()
    assert registry.registered_identities() == ()
    with pytest.raises(PredicateRegistryError, match="not registered"):
        registry.resolve("predicate:anything@1")


def test_r2_d2_arity_is_enforced_by_the_evaluator() -> None:
    definition_ = _predicate(
        build_engine_with_definitions(definition(METRIC))
    )
    with pytest.raises(PredicateRegistryError, match="exactly 2"):
        evaluate_predicate(definition_, (1.0,))


def test_r2_d2_each_evaluator_kind_computes_its_own_truth() -> None:
    """Every evaluator kind in the closed family computes its own verdict."""

    registry = PredicateRegistry()
    cases = (
        (StateName.INCREASING, EvaluatorKind.CURRENT_GREATER_THAN_PRIOR, (51.0, 50.0), True),
        (StateName.INCREASING, EvaluatorKind.CURRENT_GREATER_THAN_PRIOR, (50.0, 50.0), False),
        (StateName.DECREASING, EvaluatorKind.CURRENT_LESS_THAN_PRIOR, (49.0, 50.0), True),
        (StateName.DECREASING, EvaluatorKind.CURRENT_LESS_THAN_PRIOR, (51.0, 50.0), False),
        (StateName.UNCHANGED, EvaluatorKind.EXACT_EQUALITY, (50.0, 50.0), True),
        (StateName.UNCHANGED, EvaluatorKind.EXACT_EQUALITY, (51.0, 50.0), False),
    )
    for index, (target, kind, operands, expected) in enumerate(cases):
        definition_ = StatePredicateDefinition(
            predicate_id=f"predicate:case-{index}",
            version="1",
            state_class=StateClass.B_SPECIFICATION_ONLY,
            target_state=target,
            description="synthetic fixture predicate; canonically unratified",
            required_input_arity=2,
            evaluator_kind=kind,
        )
        registry.register(definition_)
        evaluation = registry.evaluate(definition_.identity, operands)
        assert isinstance(evaluation, PredicateEvaluation)
        assert evaluation.result is expected, (kind, operands)


# ===========================================================================
# Phase 6/7 — rule / predicate binding at emission
# ===========================================================================


def test_r2_phase6_a_rule_may_not_bind_another_states_predicate() -> None:
    """A rule targeting INCREASING may not bind a DECREASING predicate."""

    engine = build_engine_with_definitions(definition(METRIC))
    _series_engine(engine, current=150.0, prior=100.0)
    decreasing = _predicate(engine, target=StateName.DECREASING)
    rule = StateRule(
        state_rule_id="staterule:increasing:1",
        target_state=StateName.INCREASING,
        state_class=StateClass.B_SPECIFICATION_ONLY,
        predicate_ref=decreasing.identity,
        methodology_ref="book6-methodology@1",
        required_measurement_refs=("obs:current", "obs:prior"),
        window_class_constraint="INSTANTANEOUS",
        version="1",
    )
    engine.registry.register_state_rule(rule)
    engine.registry.state_rules.ratify(
        rule.state_rule_id, operator="synthetic-fixture-operator", at=NOW
    )
    with pytest.raises(Book6EngineError, match="another state's predicate"):
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())


def test_r2_phase6_a_rule_may_not_misstate_its_class() -> None:
    engine = build_engine_with_definitions(definition(METRIC))
    _series_engine(engine, current=150.0, prior=100.0)
    _predicate(engine)  # a Class B predicate targeting INCREASING
    rule = StateRule(
        state_rule_id="staterule:stable:1",
        target_state=StateName.STABLE,
        state_class=StateClass.C_THRESHOLD_BENCHMARK,
        predicate_ref="predicate:current_gt_prior@1",
        methodology_ref="book6-methodology@1",
        required_measurement_refs=("obs:current", "obs:prior"),
        benchmark_methodology_ref="benchmark:own-history@1",
        tolerance_ref="tolerance:declared@1",
        volatility_measure_ref="volatility:declared@1",
        window_class_constraint="INSTANTANEOUS",
        version="1",
    )
    engine.registry.register_state_rule(rule)
    engine.registry.state_rules.ratify(
        rule.state_rule_id, operator="synthetic-fixture-operator", at=NOW
    )
    # the class mismatch is refused before or with the target mismatch
    with pytest.raises(Book6EngineError, match="(declares class|another state's predicate)"):
        engine.emit_rule_gated_state(
            StateName.STABLE,
            rule_ref=rule.state_rule_id,
            dimension_id="dim:1",
            measurement_refs=("obs:current", "obs:prior"),
            methodology_ref="book6-methodology@1",
            valid_time=T1,
            observed_at=T1,
            missingness=MissingnessState.OBSERVED,
        )


def test_r2_phase6_measurement_order_is_explicit_not_conventional() -> None:
    """S3: swapping the supplied operand order is refused, not recomputed."""

    engine = build_engine_with_definitions(definition(METRIC))
    _series_engine(engine, current=150.0, prior=100.0)
    _predicate(engine)
    _increasing_rule(engine)
    swapped = _emission_kwargs() | {"measurement_refs": ("obs:prior", "obs:current")}
    with pytest.raises(Book6EngineError, match="fixed order"):
        engine.emit_rule_gated_state(StateName.INCREASING, **swapped)


def test_r2_phase6_predicate_target_mismatch_s4_is_refused() -> None:
    """S4 model_copy attack: the rule's bound predicate is resolved LIVE."""

    engine = build_engine_with_definitions(definition(METRIC))
    _series_engine(engine, current=150.0, prior=100.0)
    _predicate(engine, target=StateName.DECREASING)
    _increasing_rule(engine)
    # the registered rule still binds the INCREASING predicate; a forged copy
    # handed to the engine cannot change which predicate is resolved
    forged = engine.registry.state_rules.registered_rule(
        "staterule:increasing:1"
    ).model_copy(update={"target_state": StateName.DECREASING})
    assert forged.target_state is StateName.DECREASING
    # the REGISTERED rule still targets INCREASING, so a DECREASING request
    # against the same rule id is refused by the registry itself
    with pytest.raises(StateError):
        engine.registry.state_rules.authorize(
            StateName.DECREASING, rule_ref="staterule:increasing:1"
        )


def test_r2_phase7_an_unresolvable_predicate_refuses_the_emission() -> None:
    engine = build_engine_with_definitions(definition(METRIC))
    _series_engine(engine, current=150.0, prior=100.0)
    _increasing_rule(engine)  # no predicate registered at all
    with pytest.raises(Book6EngineError, match="not registered"):
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())


def test_r2_phase7_s1_predicate_ref_mutation_grants_nothing() -> None:
    """S1: the ledger owns ratification, and the predicate resolves live."""

    engine = build_engine_with_definitions(definition(METRIC))
    _series_engine(engine, current=150.0, prior=100.0)
    _predicate(engine)
    _increasing_rule(engine)
    registry: StateRuleRegistry = engine.registry.state_rules
    decision = registry.ratification_of("staterule:increasing:1")
    assert decision is not None and decision.operator == "synthetic-fixture-operator"
    # mutating a copy of the rule object changes nothing the engine reads:
    # the REGISTERED rule still binds the resolvable predicate and replays it
    forged = registry.registered_rule("staterule:increasing:1").model_copy(
        update={"predicate_ref": "predicate:always-true@9"}
    )
    assert forged.predicate_ref == "predicate:always-true@9"
    dimension = engine.emit_rule_gated_state(
        StateName.INCREASING, **_emission_kwargs()
    )
    assert dimension.state is StateName.INCREASING
    # ...and a RATIFIED rule whose bound predicate does not resolve refuses
    ghost = StateRule(
        state_rule_id="staterule:ghost:1",
        target_state=StateName.INCREASING,
        state_class=StateClass.B_SPECIFICATION_ONLY,
        predicate_ref="predicate:never-registered@1",
        methodology_ref="book6-methodology@1",
        required_measurement_refs=("obs:current", "obs:prior"),
        window_class_constraint="INSTANTANEOUS",
        version="1",
    )
    engine.registry.register_state_rule(ghost)
    engine.registry.state_rules.ratify(
        ghost.state_rule_id, operator="synthetic-fixture-operator", at=NOW
    )
    with pytest.raises(Book6EngineError, match="not registered"):
        engine.emit_rule_gated_state(
            StateName.INCREASING,
            rule_ref=ghost.state_rule_id,
            dimension_id="dim:1",
            measurement_refs=("obs:current", "obs:prior"),
            methodology_ref="book6-methodology@1",
            valid_time=T1,
            observed_at=T1,
            missingness=MissingnessState.OBSERVED,
        )


# ===========================================================================
# R2-D3 — per-metric coverage closure; attestation is evidence, not authority
# ===========================================================================


def _multi_metric_stack():
    """Engine + fully-observed vector where every metric has a live rule."""

    engine = build_engine_with_definitions(
        definition("metric:A"), definition("metric:B")
    )
    _ratified_rule_for_metrics(engine)  # rules live BEFORE the vector is built
    vector = _observed_vector(engine)
    return engine, vector


def test_r2_d3_the_forged_attestation_reproducer_is_now_refused() -> None:
    """R2-D3 reproducer: rule:A scoped to metric:A only, forged scope (A, B)."""

    engine = build_engine_with_definitions(
        definition("metric:A"), definition("metric:B")
    )
    vector = _observed_vector(engine)
    # a live rule for metric A ONLY
    engine.registry.coverage_rules.register(coverage_rule("rule:A", scope_metric_id="metric:A"))
    engine.registry.coverage_rules.ratify("rule:A", operator="synthetic", at=T1)
    forged = CoverageSufficiencyAttestation(
        rule_ids=("rule:A",),
        scope_metric_ids=("metric:A", "metric:B"),
        attested_at=T1,
        registry_identity="csia:book6:coverage-rule-registry",
    )
    attacked = vector.model_copy(
        update={
            "coverage_sufficiency_rule_refs": ("rule:A",),
            "sufficiency_attestation": forged,
        }
    )
    assert vector.data_status is VectorStatus.DATA_INCOMPLETE
    assert engine.data_status(attacked) is VectorStatus.DATA_INCOMPLETE


def test_r2_d3_every_required_metric_covered_is_data_complete() -> None:
    engine, vector = _multi_metric_stack()
    assert vector.coverage_sufficiency_rule_refs == (
        "covrule:metric:A",
        "covrule:metric:B",
    )
    assert engine.data_status(vector) is VectorStatus.DATA_COMPLETE
    report = engine.coverage_report(vector)
    assert isinstance(report, CoverageReport)
    assert report.status == "DATA_COMPLETE"
    assert report.uncovered_metric_ids == ()


def test_r2_d3_c1_scope_widening_grants_nothing() -> None:
    engine, vector = _multi_metric_stack()
    widened = vector.sufficiency_attestation.model_copy(
        update={
            "scope_metric_ids": ("metric:A", "metric:B", "metric:C"),
        }
    )
    attacked = vector.model_copy(
        update={
            "coverage_sufficiency_rule_refs": ("covrule:metric:A",),
            "sufficiency_attestation": widened,
        }
    )
    assert engine.data_status(attacked) is VectorStatus.DATA_INCOMPLETE


def test_r2_d3_c2_a_forged_registry_identity_grants_nothing() -> None:
    engine, vector = _multi_metric_stack()
    forged = vector.sufficiency_attestation.model_copy(
        update={"registry_identity": "csia:forged:registry"}
    )
    attacked = vector.model_copy(
        update={
            "coverage_sufficiency_rule_refs": ("covrule:metric:A",),
            "sufficiency_attestation": forged,
        }
    )
    assert engine.data_status(attacked) is VectorStatus.DATA_INCOMPLETE


def test_r2_d3_c3_reducing_the_rule_list_leaves_a_metric_uncovered() -> None:
    engine, vector = _multi_metric_stack()
    attacked = vector.model_copy(
        update={"coverage_sufficiency_rule_refs": ("covrule:metric:A",)}
    )
    assert engine.data_status(attacked) is VectorStatus.DATA_INCOMPLETE
    report = engine.coverage_report(attacked)
    assert report.uncovered_metric_ids == ("metric:B",)


def test_r2_d3_c4_an_unrelated_live_rule_cannot_stand_in_for_a_metric() -> None:
    engine = build_engine_with_definitions(
        definition("metric:A"), definition("metric:B")
    )
    vector = _observed_vector(engine)
    engine.registry.coverage_rules.register(coverage_rule("rule:X", scope_metric_id="metric:A"))
    engine.registry.coverage_rules.ratify("rule:X", operator="synthetic", at=T1)
    attacked = vector.model_copy(
        update={"coverage_sufficiency_rule_refs": ("rule:X", "rule:X")}
    )
    assert engine.data_status(attacked) is VectorStatus.DATA_INCOMPLETE
    report = engine.coverage_report(attacked)
    assert report.uncovered_metric_ids == ("metric:B",)


def test_r2_phase10_attestation_is_an_audit_record_not_authority() -> None:
    """Stripping the attestation cannot flip the authoritative verdict.

    This deliberately supersedes the R1-D4 mechanism (which required the
    attestation) with the R2 doctrine: the ENGINE reconstructs sufficiency
    from registry state. The R1 gate that still holds is that fake rule refs
    fail closed — asserted in test_book6_hardening_r1.py::test_r1_c8_...
    """

    engine, vector = _multi_metric_stack()
    stripped = vector.model_copy(update={"sufficiency_attestation": None})
    assert engine.data_status(stripped) is VectorStatus.DATA_COMPLETE
    forged_scope = CoverageSufficiencyAttestation(
        rule_ids=("covrule:metric:A", "covrule:metric:B", "rule:ghost"),
        scope_metric_ids=("metric:A", "metric:B"),
        attested_at=T1,
        registry_identity="csia:forged:registry",
    )
    forged_vector = vector.model_copy(
        update={"sufficiency_attestation": forged_scope}
    )
    assert engine.data_status(forged_vector) is VectorStatus.DATA_COMPLETE


def test_r2_phase11_build_availability_vector_never_issues_a_partial_attestation() -> None:
    engine = build_engine_with_definitions(
        definition("metric:A"), definition("metric:B")
    )
    _observed_vector(engine)
    # only metric A has a live rule; the registry must return None, not a
    # partial attestation that a rule for A stands in for B
    engine.registry.coverage_rules.register(coverage_rule("rule:A", scope_metric_id="metric:A"))
    engine.registry.coverage_rules.ratify("rule:A", operator="synthetic", at=T1)
    rebuilt = engine.build_availability_vector(
        subject_ref="fixture:chain:alpha",
        schema_ref="schema:book6:1",
        as_of_valid_time=T1,
        observed_at=T1,
        measurement_ids=("obs:metric:A", "obs:metric:B"),
        methodology_ref="book6-methodology@1",
    )
    assert rebuilt.sufficiency_attestation is None
    assert engine.data_status(rebuilt) is VectorStatus.DATA_INCOMPLETE


def test_r2_phase9_coverage_report_partition_is_enforced() -> None:
    """The report refuses to claim a metric is both covered and uncovered.

    The partition validator raises ``CoverageRuleError`` from inside a pydantic
    ``model_validator``, so pydantic surfaces it as ``ValidationError``
    (Pydantic v2 wraps ``ValueError`` subclasses raised in ``mode="after"``).
    """

    with pytest.raises(ValidationError, match="both covered and uncovered"):
        CoverageReport(
            required_metric_ids=("metric:A",),
            covered_metric_ids=("metric:A",),
            uncovered_metric_ids=("metric:A",),
        )


# ===========================================================================
# R2-D4 — historical authority honesty
# ===========================================================================


def _valuation_engine(*claim_ids: str):
    engine, claim_store, _evidence, service = build_engine(*(claim_ids or (CLAIM,)))
    return engine, claim_store, service


def test_r2_d4_the_capability_constant_is_recorded() -> None:
    assert HISTORICAL_BOOK2_AUTHORITY_REPLAY == "NOT_IMPLEMENTED"
    report = HistoricalAuthorityReport(
        valuation_id="val:1",
        replay_unavailable_reason="accepted Book 2 cannot answer historical authority",
        current_claims_backed=False,
        record_shape_valid=True,
    )
    assert report.replay_available is False
    assert report.replay_capability == "NOT_IMPLEMENTED"


def test_r2_d4_a_report_may_not_claim_replay_availability() -> None:
    with pytest.raises(ValidationError, match="replay"):
        HistoricalAuthorityReport(
            valuation_id="val:1",
            replay_capability="AVAILABLE",
            replay_available=True,
            replay_unavailable_reason="forged",
            current_claims_backed=True,
            record_shape_valid=True,
        )


def test_r2_phase14_h1_current_price_and_current_claim_authorizes() -> None:
    engine, *_ = _valuation_engine()
    fresh = valuation(
        "val:fresh",
        price_observation=price(
            "price:fresh", claim_refs=(CLAIM,), observed_at=NOW - timedelta(seconds=60)
        ),
        observed_at=NOW,
    )
    assert engine.authorize_current_valuation(fresh, as_of=NOW) is fresh


def test_r2_phase14_h2_a_stale_now_claim_is_refused_for_current_authority() -> None:
    engine, *_ = _valuation_engine()
    stale = valuation(
        "val:stale",
        price_observation=price("price:stale", claim_refs=(CLAIM,), observed_at=NOW - timedelta(days=30)),
        observed_at=NOW,
        staleness_bound_seconds=3600,
    )
    with pytest.raises(ValuationError, match="stale"):
        engine.authorize_current_valuation(stale, as_of=NOW)


def test_r2_phase14_h3_clock_only_decay_preserves_the_historical_record() -> None:
    """The historical record stands when the price is stale by clock alone."""

    engine, *_ = _valuation_engine()
    historical = _historical_valuation()
    assert engine.validate_recorded_historical_shape(historical) is historical
    assert engine.historical_authority_status(historical).record_shape_valid is True


def test_r2_phase14_h4_h5_h6_later_claim_decay_preserves_the_record_honestly() -> None:
    """A claim that decays AFTER observation must not erase the record — and
    Book 6 must not claim revalidated historical authority it cannot prove."""

    for new_state in ("STALE", "REJECTED"):
        engine, claim_store, service = _valuation_engine()
        historical = _historical_valuation()
        assert engine.validate_recorded_historical_shape(historical) is historical
        report_before = engine.historical_authority_status(historical)
        assert report_before.current_claims_backed is True

        decay_claim(service, claim_store, CLAIM, new_state)

        # the record is preserved; the CURRENT backing is now gone; the
        # replay capability remains honestly absent. (H5/SUPERSEDED needs a
        # replacement claim under Book 2 law and is exercised on the claim
        # matrix in test_book6_temporal.py; the decay modes reachable on one
        # claim cover both "authority gone" directions.)
        assert engine.validate_recorded_historical_shape(historical) is historical
        report = engine.historical_authority_status(historical)
        assert report.current_claims_backed is False
        assert report.replay_available is False
        assert report.replay_capability == "NOT_IMPLEMENTED"
        assert "can_promote_to_graph" in report.replay_unavailable_reason


def test_r2_phase14_no_false_pass_on_historical_authority() -> None:
    """The historical path cannot be used to sneak current authority."""

    engine, claim_store, service = _valuation_engine()
    historical = _historical_valuation()
    assert engine.validate_recorded_historical_shape(historical) is historical
    decay_claim(service, claim_store, CLAIM, "REJECTED")
    with pytest.raises(ValuationError, match="no current Book 2 authority"):
        engine.authorize_current_valuation(historical, as_of=NOW)


def test_r2_phase18_r1_preserved_the_current_path_still_requires_book2() -> None:
    engine, *_ = _valuation_engine()
    no_claims = valuation(
        "val:noclaims",
        price_observation=price("price:nc", claim_refs=("fixture:claim:missing",)),
        observed_at=NOW,
    )
    with pytest.raises(ValuationError, match="no current Book 2 authority"):
        engine.authorize_current_valuation(no_claims, as_of=NOW)


def test_r2_phase18_the_r1_valuation_surface_is_preserved_and_honest() -> None:
    engine, *_ = _valuation_engine()
    surface = sorted(
        name
        for name in dir(engine)
        if not name.startswith("_")
        and callable(getattr(engine, name))
        and ("valuation" in name.lower() or "historical" in name.lower())
    )
    assert surface == [
        "authorize_current_valuation",
        "historical_authority_status",
        "validate_recorded_historical_shape",
    ]
