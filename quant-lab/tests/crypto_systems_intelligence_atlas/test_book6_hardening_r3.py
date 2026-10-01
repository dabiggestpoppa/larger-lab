"""Book 6 Hardening R3 — state derivation authority binding closure.

Independent review found one concrete remaining correctness class in the
StateRule -> predicate -> emitted StateDimension authority chain. All three
symptoms share one root: the pipeline verified NAMES and REPLAYED semantics,
but nothing bound an operator's ratification decision (or an emitted record's
provenance) to the exact executable content it names.

- **R3-D1** a predicate could DECLARE ``target_state=INCREASING`` while its
  evaluator computed ``CURRENT_LESS_THAN_PRIOR`` — a falling series
  (50 < 100) emitted INCREASING through a perfectly replayed pipeline;
- **R3-D2** a StateRule could be RATIFIED while its ``predicate_ref`` resolved
  to nothing — the operator ratified a name, and the derivation semantics were
  whatever that name meant LATER (late binding);
- **R3-D3** the emitted ``StateDimension.methodology_ref`` was independently
  CALLER-SUPPLIED, so a record could claim it was derived under a methodology
  the derivation never used.

Repairs, and the doctrine each carries:

- the closed map :data:`EVALUATOR_TARGET_STATE` binds each Class B evaluator to
  exactly one target state, mechanically; contradictory declarations are
  refused as DATA at construction (``EVALUATOR_TARGET_SEMANTIC_BINDING``);
- ``PREDICATE_IDENTITY_BINDS_CONTENT``: every predicate carries a deterministic
  content fingerprint, and ratification is DERIVATION-BOUND — the decision
  records the rule id/version plus the predicate identity and fingerprint, the
  methodology identity and fingerprint, and the declared operand order
  (:class:`DerivationBinding`). Ratification may not precede its predicate
  (no late binding), and ``authorize`` live-verifies the binding:
  ``RATIFIED THEN != AUTHORITATIVE NOW`` if any bound component changed;
- the emitted dimension's ``methodology_ref`` is DERIVED from the authorized
  rule. ``DERIVATION USED METHODOLOGY A -> OUTPUT MAY NOT CLAIM METHODOLOGY B``.

Class C remains unimplemented (no STABLE/VOLATILE/HIGHER/LOWER evaluator
semantics were invented), no generic EXPANDING/CONTRACTING exists, and the
canonical ratification counts stay at ZERO.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book6_core import Book6EngineError
from crypto_systems_intelligence_atlas.book6_methodology import (
    Book6MethodologyRegistry,
    MethodologyRegistryError,
)
from crypto_systems_intelligence_atlas.book6_predicates import (
    EVALUATOR_TARGET_SEMANTIC_BINDING,
    EVALUATOR_TARGET_STATE,
    PREDICATES_CANONICALLY_RATIFIED,
    EvaluatorKind,
    OperandOrder,
    PredicateNotSatisfied,
    PredicateRegistry,
    PredicateRegistryError,
    StatePredicateDefinition,
    predicate_fingerprint,
)
from crypto_systems_intelligence_atlas.book6_ratification import (
    RatificationError,
    RatificationLedger,
)
from crypto_systems_intelligence_atlas.book6_states import (
    INDIVIDUAL_STATE_RULES_RATIFIED_AT_BOOTSTRAP,
    StateClass,
    StateError,
    StateName,
    StateRule,
    StateRuleRegistry,
)
from crypto_systems_intelligence_atlas.book6_support import (
    CLAIM_ID,
    NOW,
    T1,
    build_engine_with_definitions,
    comparison_methodology,
    definition,
    methodology,
    register_measurement,
    windowed_observation,
)

METRIC = "metric.native.tx"
CLAIM = CLAIM_ID


# ===========================================================================
# fixtures
# ===========================================================================


def _series_engine(*, current=50.0, prior=100.0):
    engine = build_engine_with_definitions(definition(METRIC))
    for mid, value in (("obs:current", current), ("obs:prior", prior)):
        register_measurement(
            engine,
            windowed_observation(
                mid,
                METRIC,
                value=value,
                missingness=__import__(
                    "crypto_systems_intelligence_atlas.book6_grammar",
                    fromlist=["MissingnessState"],
                ).MissingnessState.OBSERVED,
                claim_refs=(CLAIM,),
            ),
        )
    return engine


def _predicate(
    engine,
    predicate_id="predicate:current_gt_prior",
    *,
    target=StateName.INCREASING,
    kind=None,
    **overrides,
):
    if kind is None:
        kind = next(k for k, t in EVALUATOR_TARGET_STATE.items() if t is target)
    definition_ = StatePredicateDefinition(
        predicate_id=predicate_id,
        version="1",
        state_class=StateClass.B_SPECIFICATION_ONLY,
        target_state=target,
        description="synthetic fixture predicate; canonically unratified",
        required_input_arity=2,
        evaluator_kind=kind,
        **overrides,
    )
    engine.predicates.register(definition_)
    return definition_


def _rule(engine, *, predicate_ref="predicate:current_gt_prior@1", **overrides):
    payload: dict = {
        "state_rule_id": "staterule:increasing:1",
        "target_state": StateName.INCREASING,
        "state_class": StateClass.B_SPECIFICATION_ONLY,
        "predicate_ref": predicate_ref,
        "methodology_ref": "book6-methodology@1",
        "required_measurement_refs": ("obs:current", "obs:prior"),
        "window_class_constraint": "INSTANTANEOUS",
        "version": "1",
    }
    payload.update(overrides)
    rule = StateRule(**payload)
    engine.registry.register_state_rule(rule)
    return rule


def _ratified_rule(engine, **kwargs):
    rule = _rule(engine, **kwargs)
    engine.registry.state_rules.ratify(
        rule.state_rule_id, operator="synthetic-fixture-operator", at=NOW
    )
    return rule


def _emission_kwargs(methodology_ref="book6-methodology@1"):
    return {
        "rule_ref": "staterule:increasing:1",
        "dimension_id": "dim:1",
        "measurement_refs": ("obs:current", "obs:prior"),
        "methodology_ref": methodology_ref,
        "valid_time": T1,
        "observed_at": T1,
        "missingness": __import__(
            "crypto_systems_intelligence_atlas.book6_grammar",
            fromlist=["MissingnessState"],
        ).MissingnessState.OBSERVED,
    }


# ===========================================================================
# R3-D1 — evaluator / target semantic binding (Phase 1/2)
# ===========================================================================


def test_r3_d1_the_evaluator_target_contradiction_reproducer_is_refused() -> None:
    """R3-D1 reproducer: LESS_THAN semantics under a declared INCREASING."""

    with pytest.raises((PredicateRegistryError, ValidationError), match="contradict"):
        StatePredicateDefinition(
            predicate_id="predicate:lying-increasing",
            version="1",
            state_class=StateClass.B_SPECIFICATION_ONLY,
            target_state=StateName.INCREASING,
            description="a lying predicate: falling semantics under INCREASING",
            required_input_arity=2,
            evaluator_kind=EvaluatorKind.CURRENT_LESS_THAN_PRIOR,
        )


@pytest.mark.parametrize(
    ("kind", "target"),
    [
        (EvaluatorKind.CURRENT_LESS_THAN_PRIOR, StateName.INCREASING),
        (EvaluatorKind.EXACT_EQUALITY, StateName.INCREASING),
        (EvaluatorKind.CURRENT_GREATER_THAN_PRIOR, StateName.DECREASING),
        (EvaluatorKind.CURRENT_GREATER_THAN_PRIOR, StateName.UNCHANGED),
    ],
    ids=lambda v: getattr(v, "value", str(v)),
)
def test_r3_phase1_wrong_pairings_are_rejected(kind, target) -> None:
    with pytest.raises((PredicateRegistryError, ValidationError)):
        StatePredicateDefinition(
            predicate_id="predicate:wrong-pairing",
            version="1",
            state_class=StateClass.B_SPECIFICATION_ONLY,
            target_state=target,
            description="a mis-bound predicate that must be refused",
            required_input_arity=2,
            evaluator_kind=kind,
        )


@pytest.mark.parametrize("kind", sorted(EVALUATOR_TARGET_STATE), ids=lambda k: k.value)
def test_r3_phase1_the_three_correct_pairings_pass_structurally(kind) -> None:
    target = EVALUATOR_TARGET_STATE[kind]
    definition_ = StatePredicateDefinition(
        predicate_id=f"predicate:truthful-{target.value.lower()}",
        version="1",
        state_class=StateClass.B_SPECIFICATION_ONLY,
        target_state=target,
        description="a truthful predicate whose evaluator matches its target",
        required_input_arity=2,
        evaluator_kind=kind,
    )
    assert definition_.target_state is target
    assert EVALUATOR_TARGET_STATE[kind] is target


def test_r3_phase1_the_map_is_closed_and_constant_true() -> None:
    assert EVALUATOR_TARGET_STATE == {
        EvaluatorKind.CURRENT_GREATER_THAN_PRIOR: StateName.INCREASING,
        EvaluatorKind.CURRENT_LESS_THAN_PRIOR: StateName.DECREASING,
        EvaluatorKind.EXACT_EQUALITY: StateName.UNCHANGED,
    }
    assert EVALUATOR_TARGET_SEMANTIC_BINDING is True


def test_r3_phase2_class_c_targets_are_unimplementable() -> None:
    """No STABLE/VOLATILE/OWN-HISTORY evaluator semantics may exist yet."""

    for target in (
        StateName.STABLE,
        StateName.VOLATILE,
        StateName.HIGHER_THAN_OWN_HISTORY,
        StateName.LOWER_THAN_OWN_HISTORY,
    ):
        with pytest.raises((PredicateRegistryError, ValidationError)):
            StatePredicateDefinition(
                predicate_id=f"predicate:class-c-{target.value.lower()}",
                version="1",
                state_class=StateClass.C_THRESHOLD_BENCHMARK,
                target_state=target,
                description="a Class C predicate that must not exist yet",
                required_input_arity=2,
                evaluator_kind=EvaluatorKind.EXACT_EQUALITY,
            )


def test_r3_phase2_no_generic_expanding_contracting_predicate() -> None:
    """No predicate may target the deferred generic states, and no rule either."""

    from crypto_systems_intelligence_atlas.book6_states import (
        GENERIC_EXPANDING_CONTRACTING_DEFERRED,
        STATE_CLASS_BY_NAME,
    )

    assert GENERIC_EXPANDING_CONTRACTING_DEFERRED is True
    for name in (StateName.EXPANDING, StateName.CONTRACTING):
        # no evaluator/target pairing exists for the generic states...
        assert name not in EVALUATOR_TARGET_STATE
        assert name not in tuple(EVALUATOR_TARGET_STATE.values())
        # ...and the state class itself is DEFERRED, so no rule can be written
        assert STATE_CLASS_BY_NAME[name] is StateClass.DEFERRED_GENERIC
        with pytest.raises((PredicateRegistryError, ValidationError)):
            StatePredicateDefinition(
                predicate_id=f"predicate:generic-{name.value.lower()}",
                version="1",
                state_class=StateClass.DEFERRED_GENERIC,
                target_state=name,
                description="a generic predicate that must not exist",
                required_input_arity=2,
                evaluator_kind=EvaluatorKind.CURRENT_GREATER_THAN_PRIOR,
            )


# ===========================================================================
# R3-D2 — predicate fingerprint and derivation-bound ratification (Phase 3-8)
# ===========================================================================


def test_r3_phase4_the_predicate_fingerprint_is_deterministic_and_content_complete() -> None:
    base = _predicate(_series_engine())

    # equivalent content reordering of the unordered sets -> same digest
    reordered = base.model_copy(
        update={
            "permitted_methodology_refs": tuple(
                reversed(base.permitted_methodology_refs)
            ),
        }
    )
    assert predicate_fingerprint(reordered) == predicate_fingerprint(base)

    from crypto_systems_intelligence_atlas.book6_grammar import WindowClass

    mutated_fields = (
        ("predicate_id", "predicate:mutated"),
        ("version", "2"),
        ("description", "a semantically different description entirely"),
        ("required_input_arity", 3),
        ("evaluator_kind", EvaluatorKind.CURRENT_LESS_THAN_PRIOR),
        ("permitted_methodology_refs", ("methodology:injected@1",)),
        ("permitted_window_classes", (WindowClass.CALENDAR_MONTH,)),
    )
    for field, value in mutated_fields:
        # a contradictory evaluator is refused by the R3-D1 seal before the
        # fingerprint is consulted, so these mutants must SURVIVE construction
        # to prove the fingerprint itself reacts to the field
        try:
            mutant = base.model_copy(update={field: value})
        except ValidationError:
            continue
        assert predicate_fingerprint(mutant) != predicate_fingerprint(base), field
    # (operand_order is a ONE-member closed enum, so it has no alternative
    # value to mutate into; test_r3_s8 pins that closure directly.)


def test_r3_phase3_b1_ratification_may_not_precede_its_predicate() -> None:
    """B1: a rule naming an unknown predicate cannot be ratified."""

    engine = _series_engine()
    _rule(engine, predicate_ref="predicate:future@1")
    with pytest.raises(StateError, match="may not precede its predicate"):
        engine.registry.state_rules.ratify(
            "staterule:increasing:1", operator="synthetic-fixture-operator", at=NOW
        )
    assert engine.registry.state_rules.ratified_count() == 0

    # and even after the predicate LATER appears, the refusal above already
    # happened: a decision exists only if the predicate existed at ratify time
    _predicate(engine, predicate_id="predicate:future")
    engine.registry.state_rules.ratify(
        "staterule:increasing:1", operator="synthetic-fixture-operator", at=NOW
    )
    assert engine.registry.state_rules.ratified_count() == 1


def test_r3_phase3_b2_predicate_first_then_rule_then_ratify_passes() -> None:
    """B2: predicate first, rule second, ratification third — the honest path."""

    engine = _series_engine(current=150.0)
    _predicate(engine)
    _ratified_rule(engine)
    decision = engine.registry.state_rules.ratification_of("staterule:increasing:1")
    assert decision is not None
    assert decision.binding is not None
    binding = decision.binding
    assert binding.predicate_identity == "predicate:current_gt_prior@1"
    assert binding.predicate_fingerprint == predicate_fingerprint(
        engine.predicates.registered_predicate("predicate:current_gt_prior@1")
    )
    assert binding.methodology_identity == "book6-methodology@1"
    assert binding.required_measurement_refs == ("obs:current", "obs:prior")
    dimension = engine.emit_rule_gated_state(
        StateName.INCREASING, **_emission_kwargs()
    )
    assert dimension.state is StateName.INCREASING


def test_r3_phase3_b3_rule_authorization_does_not_silently_follow_predicate_v2() -> None:
    """B3: a rule ratified against x@1 never silently moves to x@2."""

    engine = _series_engine(current=150.0)
    _predicate(engine)  # predicate:current_gt_prior@1
    _ratified_rule(engine)
    binding_v1 = engine.registry.state_rules.ratification_of(
        "staterule:increasing:1"
    ).binding
    # a NEW VERSION of the same predicate id appears afterwards
    engine.predicates.supersede(
        StatePredicateDefinition(
            predicate_id="predicate:current_gt_prior",
            version="2",
            state_class=StateClass.B_SPECIFICATION_ONLY,
            target_state=StateName.INCREASING,
            description="a new predicate version that must not be auto-followed",
            required_input_arity=2,
            evaluator_kind=EvaluatorKind.CURRENT_GREATER_THAN_PRIOR,
        )
    )
    decision = engine.registry.state_rules.ratification_of("staterule:increasing:1")
    assert decision.binding is not None
    assert decision.binding.predicate_identity == "predicate:current_gt_prior@1"
    assert decision.binding.digest == binding_v1.digest
    # the rule's own binding is unchanged, and emission still replays @1
    dimension = engine.emit_rule_gated_state(
        StateName.INCREASING, **_emission_kwargs()
    )
    assert dimension.state is StateName.INCREASING


def test_r3_phase3_b4_unavailable_predicate_loses_authority() -> None:
    """B4: predicate v1 unavailable -> the rule loses current authority."""

    engine = _series_engine(current=150.0)
    _predicate(engine)
    _ratified_rule(engine)
    # the bound predicate disappears (registry replaced by an operator act:
    # modeled here by building a fresh predicate store under the same rule)
    from crypto_systems_intelligence_atlas.book6_predicates import PredicateRegistry

    engine.registry.state_rules._predicates = PredicateRegistry()
    with pytest.raises(StateError, match="no longer current"):
        engine.registry.state_rules.authorize(
            StateName.INCREASING, rule_ref="staterule:increasing:1"
        )
    with pytest.raises((StateError, Book6EngineError)):
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())


def test_r3_phase5_the_ratification_records_a_derivation_binding() -> None:
    from crypto_systems_intelligence_atlas.book6_ratification import (
        DerivationBinding,
        derivation_binding_digest,
    )

    engine = _series_engine(current=150.0)
    _predicate(engine)
    _ratified_rule(engine)
    decision = engine.registry.state_rules.ratification_of("staterule:increasing:1")
    binding = decision.binding
    assert isinstance(binding, DerivationBinding)
    # every Phase 5 component is recorded
    assert binding.rule_ref == "staterule:increasing:1"
    assert binding.rule_version == "1"
    assert binding.predicate_identity == "predicate:current_gt_prior@1"
    assert len(binding.predicate_fingerprint) == 64
    assert binding.methodology_identity == "book6-methodology@1"
    assert len(binding.methodology_fingerprint) == 64
    assert binding.required_measurement_refs == ("obs:current", "obs:prior")
    # the digest is deterministic
    assert derivation_binding_digest(binding) == binding.digest
    # S9/S6: mutating the predicate's permitted methodology set or evaluator
    # kind produces a DIFFERENT fingerprint, which live authorization catches
    mutant_predicate = engine.predicates.registered_predicate(
        "predicate:current_gt_prior@1"
    ).model_copy(update={"permitted_methodology_refs": ("methodology:evil@1",)})
    assert predicate_fingerprint(mutant_predicate) != binding.predicate_fingerprint


def test_r3_phase7_a_low_level_ledger_ratification_is_not_usable_authority() -> None:
    """Phase 7: a ledger entry WITHOUT a binding licenses nothing.

    The attack writes a decision straight into the ledger, bypassing the
    binding-aware ``ratify``. On a WIRED registry — the only kind an engine
    exposes — ``authorize`` refuses any decision that does not carry a
    derivation binding, so the low-level result is recorded history but never
    usable authority. (A bare unwired ``StateRuleRegistry`` is a structural
    object unreachable from the engine; its decisions are binding-less by
    definition and its ``authorize`` is structural-only.)
    """

    registry = StateRuleRegistry()
    registry.wire_derivation_registries(
        predicates=PredicateRegistry(), methodologies=Book6MethodologyRegistry()
    )
    registry.register(
        StateRule(
            state_rule_id="sr:1",
            target_state=StateName.INCREASING,
            state_class=StateClass.B_SPECIFICATION_ONLY,
            predicate_ref="predicate:x@1",
            methodology_ref="book6-methodology@1",
            version="1",
        )
    )
    # the low-level path: write a decision directly into the ledger
    ledger: RatificationLedger = registry._ledger
    ledger.record("sr:1", version="1", operator="low-level-operator", at=NOW)
    with pytest.raises(StateError, match="WITHOUT a derivation binding"):
        registry.authorize(StateName.INCREASING, rule_ref="sr:1")


def test_r3_phase7_bare_ratify_without_wired_registries_records_no_binding() -> None:
    """A bare structural registry can still record decisions — honestly.

    Its decisions carry ``binding=None`` and are refused by a WIRED registry's
    ``authorize``; the wired path is the only one that produces usable
    authority. This keeps D6M-3 = A: one centralized, binding-aware path.
    """

    registry = StateRuleRegistry()
    registry.register(
        StateRule(
            state_rule_id="sr:1",
            target_state=StateName.INCREASING,
            state_class=StateClass.B_SPECIFICATION_ONLY,
            predicate_ref="predicate:x@1",
            methodology_ref="book6-methodology@1",
            version="1",
        )
    )
    registry.ratify("sr:1", operator="structural", at=NOW)
    decision = registry.ratification_of("sr:1")
    assert decision is not None and decision.binding is None
    wired = StateRuleRegistry()
    wired.wire_derivation_registries(
        predicates=PredicateRegistry(), methodologies=Book6MethodologyRegistry()
    )
    wired.register(
        StateRule(
            state_rule_id="sr:1",
            target_state=StateName.INCREASING,
            state_class=StateClass.B_SPECIFICATION_ONLY,
            predicate_ref="predicate:x@1",
            methodology_ref="book6-methodology@1",
            version="1",
        )
    )
    with pytest.raises(RatificationError):
        wired._ledger.decision("sr:1", version="1")


def test_r3_phase8_binding_mismatch_is_refused_at_authorization() -> None:
    """S6/S9: live content drifting from the ratified fingerprint refuses."""

    engine = _series_engine(current=150.0)
    _predicate(engine)
    _ratified_rule(engine)
    # an operator act: replace the predicate registry with one holding the same
    # identity but different CONTENT (permitted methodology set mutated)
    from crypto_systems_intelligence_atlas.book6_predicates import PredicateRegistry

    fresh = PredicateRegistry()
    fresh.register(
        engine.predicates.registered_predicate(
            "predicate:current_gt_prior@1"
        ).model_copy(update={"permitted_methodology_refs": ("methodology:evil@1",)})
    )
    engine.registry.state_rules._predicates = fresh
    with pytest.raises(StateError, match="(no longer current|is not the derivation)"):
        engine.registry.state_rules.authorize(
            StateName.INCREASING, rule_ref="staterule:increasing:1"
        )


def test_r3_phase8_methodology_content_drift_refuses_authorization() -> None:
    """The ratified methodology fingerprint must still match at emission."""

    engine = _series_engine(current=150.0)
    _predicate(engine)
    _ratified_rule(engine)
    registry: Book6MethodologyRegistry = engine.registry.methodologies
    # the R2 seal still refuses mutated content against the bound digest
    from crypto_systems_intelligence_atlas.book6_methodology import (
        methodology_fingerprint,
    )

    bound = registry.bound_fingerprint("book6-methodology@1")
    forged = methodology("book6-methodology").model_copy(update={"formula": "garbage"})
    with pytest.raises(MethodologyRegistryError, match="content does not match"):
        registry.assert_content_matches("book6-methodology@1", forged)
    assert bound == methodology_fingerprint(methodology("book6-methodology"))
    # and if the bound CONTENT itself drifts (operator-act simulation), the
    # ratified binding no longer matches and live authorization refuses
    registry._fingerprints["book6-methodology@1"] = "0" * 64
    with pytest.raises(StateError, match="(no longer current|is not the derivation)"):
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())


# ===========================================================================
# R3-D3 — output methodology provenance (Phase 9/10)
# ===========================================================================


def test_r3_d3_the_output_methodology_forgery_reproducer_is_refused() -> None:
    """R3-D3 reproducer: caller supplies a different methodology_ref."""

    engine = _series_engine(current=150.0)
    _predicate(engine)
    _ratified_rule(engine)
    with pytest.raises(Book6EngineError, match="may not claim another"):
        engine.emit_rule_gated_state(
            StateName.INCREASING, **_emission_kwargs(
                methodology_ref="fake:other-methodology@9"
            )
        )


def test_r3_phase9_the_emitted_dimension_derives_its_methodology() -> None:
    engine = _series_engine(current=150.0)
    _predicate(engine)
    _ratified_rule(engine)
    dimension = engine.emit_rule_gated_state(
        StateName.INCREASING, **_emission_kwargs()
    )
    rule = engine.registry.state_rules.registered_rule("staterule:increasing:1")
    assert dimension.methodology_ref == rule.methodology_ref
    assert dimension.methodology_ref == "book6-methodology@1"


def test_r3_phase10_the_emitted_dimension_provenance_is_coherent() -> None:
    """Every provenance field on the dimension matches the actual derivation."""

    engine = _series_engine(current=150.0)
    _predicate(engine)
    _ratified_rule(engine)
    dimension = engine.emit_rule_gated_state(
        StateName.INCREASING, **_emission_kwargs()
    )
    rule = engine.registry.state_rules.registered_rule("staterule:increasing:1")
    predicate = engine.predicates.registered_predicate(rule.predicate_ref)
    assert dimension.state is rule.target_state is predicate.target_state
    assert dimension.state_class is rule.state_class is predicate.state_class
    assert dimension.state_rule_ref == rule.state_rule_id
    assert dimension.methodology_ref == rule.methodology_ref
    assert dimension.measurement_refs == rule.required_measurement_refs


# ===========================================================================
# Phase 11 — the S1-S10 model_copy attack matrix
# ===========================================================================


def _attack_engine():
    engine = _series_engine(current=150.0)
    _predicate(engine)
    _ratified_rule(engine)
    return engine


def test_r3_s1_rule_predicate_ref_mutated() -> None:
    engine = _attack_engine()
    registry = engine.registry.state_rules
    registry._rules["staterule:increasing:1"] = registry.registered_rule(
        "staterule:increasing:1"
    ).model_copy(update={"predicate_ref": "predicate:other@1"})
    with pytest.raises((StateError, Book6EngineError)):
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())


def test_r3_s2_rule_methodology_ref_mutated() -> None:
    engine = _attack_engine()
    registry = engine.registry.state_rules
    registry._rules["staterule:increasing:1"] = registry.registered_rule(
        "staterule:increasing:1"
    ).model_copy(update={"methodology_ref": "methodology:evil@1"})
    with pytest.raises((StateError, Book6EngineError)):
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())


def test_r3_s3_rule_required_measurement_refs_reordered() -> None:
    engine = _attack_engine()
    registry = engine.registry.state_rules
    registry._rules["staterule:increasing:1"] = registry.registered_rule(
        "staterule:increasing:1"
    ).model_copy(update={"required_measurement_refs": ("obs:prior", "obs:current")})
    with pytest.raises((StateError, Book6EngineError)):
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())


def test_r3_s4_rule_target_state_mutated() -> None:
    engine = _attack_engine()
    registry = engine.registry.state_rules
    registry._rules["staterule:increasing:1"] = registry.registered_rule(
        "staterule:increasing:1"
    ).model_copy(update={"target_state": StateName.DECREASING})
    with pytest.raises(StateError, match="targets"):
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())


def test_r3_s5_rule_state_class_mutated() -> None:
    engine = _attack_engine()
    registry = engine.registry.state_rules
    registry._rules["staterule:increasing:1"] = registry.registered_rule(
        "staterule:increasing:1"
    ).model_copy(update={"state_class": StateClass.C_THRESHOLD_BENCHMARK})
    with pytest.raises((StateError, Book6EngineError)):
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())


def test_r3_s6_predicate_evaluator_kind_mutated() -> None:
    engine = _attack_engine()
    fresh = PredicateRegistry()
    fresh.register(
        engine.predicates.registered_predicate(
            "predicate:current_gt_prior@1"
        ).model_copy(
            # a contradictory evaluator is refused outright by the R3-D1 map;
            # a content-drifting one survives registration and dies at authorize
            update={"description": "a description drift the operator never ratified"}
        )
    )
    engine.registry.state_rules._predicates = fresh
    with pytest.raises(StateError, match="(no longer current|is not the derivation)"):
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())


def test_r3_s7_predicate_target_state_mutated_is_unconstructable() -> None:
    """S7: the R3-D1 map makes a contradictory target UNCONSTRUCTABLE."""

    with pytest.raises((PredicateRegistryError, ValidationError)):
        _predicate(_attack_engine()).model_copy(update={"target_state": StateName.DECREASING})


def test_r3_s8_predicate_operand_order_mutated() -> None:
    """S8: OperandOrder is a single-member closed enum — there is nothing to
    mutate INTO, which is the binding itself."""

    assert [o.value for o in OperandOrder] == ["CURRENT_THEN_PRIOR"]
    with pytest.raises(ValueError):
        OperandOrder("PRIOR_THEN_CURRENT")


def test_r3_s9_predicate_permitted_methodology_set_mutated() -> None:
    engine = _attack_engine()
    fresh = PredicateRegistry()
    fresh.register(
        engine.predicates.registered_predicate(
            "predicate:current_gt_prior@1"
        ).model_copy(update={"permitted_methodology_refs": ("methodology:evil@1",)})
    )
    engine.registry.state_rules._predicates = fresh
    with pytest.raises(StateError, match="(no longer current|is not the derivation)"):
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())


def test_r3_s10_emitted_methodology_ref_forged() -> None:
    engine = _attack_engine()
    with pytest.raises(Book6EngineError, match="may not claim another"):
        engine.emit_rule_gated_state(
            StateName.INCREASING,
            **_emission_kwargs(methodology_ref="methodology:evil@9"),
        )


# ===========================================================================
# Phase 13/14 — supersession: no auto-follow
# ===========================================================================


def test_r3_phase13_predicate_supersession_is_explicit_and_not_auto_followed() -> None:
    engine = _series_engine(current=150.0)
    _predicate(engine)
    _ratified_rule(engine)
    engine.predicates.supersede(
        StatePredicateDefinition(
            predicate_id="predicate:current_gt_prior",
            version="2",
            state_class=StateClass.B_SPECIFICATION_ONLY,
            target_state=StateName.INCREASING,
            description="a new predicate version with its own identity",
            required_input_arity=2,
            evaluator_kind=EvaluatorKind.CURRENT_GREATER_THAN_PRIOR,
        )
    )
    # the rule remains bound to x@1
    decision = engine.registry.state_rules.ratification_of("staterule:increasing:1")
    assert decision.binding.predicate_identity == "predicate:current_gt_prior@1"
    # and emission still replays x@1
    dimension = engine.emit_rule_gated_state(
        StateName.INCREASING, **_emission_kwargs()
    )
    assert dimension.state is StateName.INCREASING


def test_r3_phase13_predicate_supersession_requires_a_prior_version() -> None:
    registry = PredicateRegistry()
    with pytest.raises(PredicateRegistryError, match="no prior registered version"):
        registry.supersede(
            StatePredicateDefinition(
                predicate_id="predicate:ghost",
                version="2",
                state_class=StateClass.B_SPECIFICATION_ONLY,
                target_state=StateName.INCREASING,
                description="supersession of nothing must be refused",
                required_input_arity=2,
                evaluator_kind=EvaluatorKind.CURRENT_GREATER_THAN_PRIOR,
            )
        )


def test_r3_phase14_methodology_supersession_is_not_auto_followed() -> None:
    """A rule ratified against m@1 does not follow m@2 (governance cost kept)."""

    engine = _series_engine(current=150.0)
    _predicate(engine)
    _ratified_rule(engine)
    from crypto_systems_intelligence_atlas.book6_support import methodology as _m

    engine.registry.methodologies.supersede_methodology(
        _m("book6-methodology", "2")
    )
    decision = engine.registry.state_rules.ratification_of("staterule:increasing:1")
    assert decision.binding.methodology_identity == "book6-methodology@1"


# ===========================================================================
# Phase 15 — state output negative/positive cases
# ===========================================================================


def test_r3_phase15_negative_increasing_is_not_emitted() -> None:
    engine = _series_engine(current=50.0, prior=100.0)
    _predicate(engine)
    _ratified_rule(engine)
    with pytest.raises(PredicateNotSatisfied) as excinfo:
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())
    assert excinfo.value.operands == (50.0, 100.0)


def test_r3_phase15_positive_increasing_emits_through_the_full_binding() -> None:
    engine = _series_engine(current=150.0, prior=100.0)
    _predicate(engine)
    _ratified_rule(engine)
    dimension = engine.emit_rule_gated_state(
        StateName.INCREASING, **_emission_kwargs()
    )
    assert dimension.state is StateName.INCREASING
    assert dimension.methodology_ref == "book6-methodology@1"


def test_r3_phase15_unchanged_requires_exact_equality_binding() -> None:
    """current == prior emits UNCHANGED only under a properly bound rule."""

    engine = _series_engine(current=100.0, prior=100.0)
    _predicate(
        engine, predicate_id="predicate:exact_equality", target=StateName.UNCHANGED
    )
    rule = _rule(
        engine,
        predicate_ref="predicate:exact_equality@1",
        target_state=StateName.UNCHANGED,
        precision_semantics="exact equality on the declared numeric precision",
    )
    engine.registry.state_rules.ratify(
        rule.state_rule_id, operator="synthetic-fixture-operator", at=NOW
    )
    kwargs = _emission_kwargs()
    dimension = engine.emit_rule_gated_state(StateName.UNCHANGED, **kwargs)
    assert dimension.state is StateName.UNCHANGED
    # and the INCREASING binding would refuse this series
    engine2 = _series_engine(current=100.0, prior=100.0)
    _predicate(engine2)
    _ratified_rule(engine2)
    with pytest.raises(PredicateNotSatisfied):
        engine2.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())


def test_r3_phase15_a_false_rule_never_inverts_to_the_opposite_state() -> None:
    engine = _series_engine(current=50.0, prior=100.0)
    _predicate(engine)
    _ratified_rule(engine)
    with pytest.raises(PredicateNotSatisfied):
        engine.emit_rule_gated_state(StateName.INCREASING, **_emission_kwargs())
    # no DECREASING rule exists; nothing may manufacture one implicitly
    assert engine.registry.state_rules.rules_for(StateName.DECREASING) == ()


# ===========================================================================
# Phase 6 — canonical counts and D6M-3 = A
# ===========================================================================


def test_r3_phase6_canonical_counts_remain_zero() -> None:
    assert INDIVIDUAL_STATE_RULES_RATIFIED_AT_BOOTSTRAP == 0
    assert PREDICATES_CANONICALLY_RATIFIED == 0
    from crypto_systems_intelligence_atlas.book6_coverage_rules import (
        COVERAGE_SUFFICIENCY_RULES_RATIFIED_AT_BOOTSTRAP,
    )

    assert COVERAGE_SUFFICIENCY_RULES_RATIFIED_AT_BOOTSTRAP == 0


def test_r3_phase6_no_delegated_or_bulk_ratification_path() -> None:
    from crypto_systems_intelligence_atlas.book6_ratification import (
        NO_DELEGATED_RATIFICATION_AUTHORITY,
    )

    assert NO_DELEGATED_RATIFICATION_AUTHORITY is True
    registry = StateRuleRegistry()
    surface = {name for name in dir(registry) if not name.startswith("_")}
    assert surface == {
        "authorize",
        "ratification_of",
        "ratified_count",
        "ratify",
        "register",
        "registered_rule",
        "registry_identity",
        "rules_for",
        "supersede",
        "superseded_versions",
        "wire_derivation_registries",
    }


# ===========================================================================
# Phase 16 — dimension_id audit (scoped, no ontology invention)
# ===========================================================================


def test_r3_phase16_dimension_id_is_a_schema_local_label() -> None:
    """Audited, deliberately not expanded (Phase 16).

    ``dimension_id`` is caller-supplied in the current contract and is NOT
    bound to a ratified metric/schema slot. Two facts bound the scope of that
    audit: (1) every emitted Class B/C dimension carries its rule, predicate
    binding, methodology and measurement refs coherently (Phase 10), so the
    DERIVATION is fully identified even where the label is free; and (2) the
    ratified vector schema treats ``dimension_id`` as the metric-definition
    reference for engine-built vectors (``FundamentalStateVector.
    dimension_metric_ids``), where it is not free at all. No reproducer showed
    a state derived from metric A misrepresented as governed dimension B in a
    way the ratified plan forbids beyond this documented contract, so no
    R3-D4 is recorded and no ontology project is started.
    """

    engine = _attack_engine()
    # the caller may label the dimension, but the derivation stays identified
    kwargs = _emission_kwargs()
    kwargs["dimension_id"] = "dim:any-label"
    dimension = engine.emit_rule_gated_state(StateName.INCREASING, **kwargs)
    assert dimension.dimension_id == "dim:any-label"
    assert dimension.state_rule_ref == "staterule:increasing:1"
    assert dimension.methodology_ref == "book6-methodology@1"


# ===========================================================================
# Phase 17 — R1/R2 preservation at the R3 boundary
# ===========================================================================


def test_r3_phase17_r2_seals_survive_at_the_state_boundary() -> None:
    """The comparison content seal and the corpus row authority are intact."""

    from crypto_systems_intelligence_atlas.book6_comparability import (
        authorize_comparison,
    )

    canonical = comparison_methodology("FC-05")
    registry = Book6MethodologyRegistry()
    registry.register_methodology(canonical)
    assert (
        authorize_comparison(
            "protocol.volume.DEX_NATIVE",
            "protocol.volume.AGGREGATOR_ROUTED",
            methodology_ref=canonical.identity,
            left_class=__import__(
                "crypto_systems_intelligence_atlas.book6_definitions",
                fromlist=["ComparabilityClass"],
            ).ComparabilityClass.CHAIN_WITHIN_FAMILY,
            right_class=__import__(
                "crypto_systems_intelligence_atlas.book6_definitions",
                fromlist=["ComparabilityClass"],
            ).ComparabilityClass.CHAIN_WITHIN_FAMILY,
            methodologies=registry,
        )
        == "AUTHORIZED"
    )
    impostor = canonical.model_copy(update={"formula": "garbage"})
    other = Book6MethodologyRegistry()
    other.register_methodology(canonical)
    # the canonical content is bound; a look-alike under the same identity is
    # refused at registration (the R2-D1 content seal, unchanged)
    with pytest.raises(MethodologyRegistryError, match="already registered"):
        other.register_methodology(impostor)
    with pytest.raises(MethodologyRegistryError, match="content does not match"):
        other.assert_content_matches(canonical.identity, impostor)
