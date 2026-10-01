"""Book 6 Hardening R1 — methodology authority, valuation provenance, rule closure.

External review found four concrete authority defects and one related gap in the
accepted Book 6 kernel. Every one of them shared a single root cause: an
authority-bearing check was satisfied by a bare string, a self-declared field, or
a caller-supplied number instead of by registry-resolved, decision-time state.

- **R1-D1** a CONDITIONAL comparison needed only a non-empty ``methodology_ref``;
- **R1-D2** a price's ``source_ref`` was an attribution, never Book 2 evidence;
- **R1-D3** ``authorize_valuation`` never consulted ``is_stale``;
- **R1-D4** any non-empty coverage-sufficiency ref produced ``DATA_COMPLETE``;
- **R1-D5** the methodology registry required by the design did not exist;
- **R1-D6** a caller-supplied normalized value was authorized unverified;
- **R1-D7** a ``model_copy``-forged ``RATIFIED`` rule could be registered.

This suite is the permanent record: each defect is reproduced as a refusal, and
each repair is asserted at the boundary a caller can actually reach.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas.book6_comparability import (
    CONDITIONAL_ROW_IDS,
    FALSE_COMPARISON_CORPUS,
    ComparabilityError,
    authorize_comparison,
    corpus_row_for,
)
from crypto_systems_intelligence_atlas.book6_coverage_rules import (
    COVERAGE_SUFFICIENCY_RULES_RATIFIED_AT_BOOTSTRAP,
    COVERAGE_RULE_REF_IS_NOT_AUTHORITY,
    NUMERIC_COVERAGE_IS_NOT_SUFFICIENCY,
    CoverageRuleError,
    CoverageRuleRegistry,
    CoverageSufficiencyAttestation,
)
from crypto_systems_intelligence_atlas.book6_core import Book6EngineError
from crypto_systems_intelligence_atlas.book6_definitions import (
    NO_DEFAULT_METRIC_EXISTS,
    CoverageRuleRatificationStatus,
    MeasurementMethodology,
)
from crypto_systems_intelligence_atlas.book6_grammar import MissingnessState, NormalizationType
from crypto_systems_intelligence_atlas.book6_methodology import (
    METHODOLOGY_IDENTITY_IS_VERSIONED,
    METHODOLOGY_REGISTRY_PRESENT,
    NO_FREE_STRING_METHODOLOGY_AUTHORITY,
    Book6MethodologyRegistry,
    MethodologyRegistryError,
    methodology_identity,
    parse_methodology_identity,
)
from crypto_systems_intelligence_atlas.book6_normalization import (
    BASE_RELATIVE_NORMALIZATIONS,
    NORMALIZED_VALUE_IS_RECOMPUTED,
    NormalizationRule,
    NormalizedMeasurement,
    compute_normalized_value,
)
from crypto_systems_intelligence_atlas.book6_provenance import Book6ProvenanceError
from crypto_systems_intelligence_atlas.book6_ratification import (
    NO_DELEGATED_RATIFICATION_AUTHORITY,
    OBJECT_STATUS_IS_NOT_AUTHORITY,
    RatificationError,
    RatificationLedger,
)
from crypto_systems_intelligence_atlas.book6_registry import Book6RegistryError
from crypto_systems_intelligence_atlas.book6_states import (
    DATA_COMPLETE_REQUIRES_ATTESTED_SUPPORT,
    INDIVIDUAL_STATE_RULES_RATIFIED_AT_BOOTSTRAP,
    RULE_OBJECT_STATUS_IS_NOT_AUTHORITY,
    FundamentalStateVector,
    RuleRatificationStatus,
    StateClass,
    StateName,
    StateRule,
    StateRuleRegistry,
    VectorStatus,
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
    register_measurement,
    valuation,
    windowed_observation,
)
from crypto_systems_intelligence_atlas.book6_valuation import (
    NO_GLOBAL_PRICE_SOURCE_CLASS,
    PRICE_AUTHORITY_IS_PURPOSE_SPECIFIC,
    PriceObservation,
    PriceObservationClass,
    ValuationError,
    ValuationPurpose,
)

METRIC = "metric.native.native_transactions"
NORMALIZED_METRIC = "metric.normalized.transactions_per_user"
PRICE_CLAIM = "fixture:claim:price"
FC05 = ("protocol.volume.DEX_NATIVE", "protocol.volume.AGGREGATOR_ROUTED")
FC07 = ("capital.staked_principal", "capital.restaked_claims")


# ===========================================================================
# R1-D1 / R1-D5 — conditional comparison methodology spoof
# ===========================================================================


def _pair_registry() -> Book6MethodologyRegistry:
    registry = Book6MethodologyRegistry()
    for row_id in CONDITIONAL_ROW_IDS:
        registry.register_methodology(comparison_methodology(row_id))
    return registry


def _authorize(left: str, right: str, methodology_ref: str | None, registry) -> str:
    from crypto_systems_intelligence_atlas.book6_definitions import ComparabilityClass

    same = ComparabilityClass.CHAIN_WITHIN_FAMILY
    return authorize_comparison(
        left,
        right,
        methodology_ref=methodology_ref,
        left_class=same,
        right_class=same,
        methodologies=registry,
    )


def test_r1_d1_a1_fake_methodology_ref_is_refused_for_fc05() -> None:
    """A1 reproducer: FC-05 with ``methodology_ref="fake:anything"``.

    Before R1 this returned ``AUTHORIZED``.
    """

    with pytest.raises(ComparabilityError, match="requires methodology"):
        _authorize(*FC05, "fake:anything", _pair_registry())


def test_r1_d1_a2_the_wrong_named_methodology_is_refused_for_fc07() -> None:
    """A2: FC-07 requires lineage-dedup, not routing-attribution."""

    with pytest.raises(ComparabilityError, match="requires methodology"):
        _authorize(*FC07, "routing-attribution-methodology@1", _pair_registry())


def test_r1_d1_a3_the_correct_name_but_unregistered_is_refused() -> None:
    """A3: the right name resolves to nothing."""

    with pytest.raises(ComparabilityError, match="not registered"):
        _authorize(*FC05, "routing-attribution-methodology@1", Book6MethodologyRegistry())


def test_r1_d1_a4_a_registered_unrelated_methodology_is_refused() -> None:
    """A4: registered, current, but not this row's methodology."""

    registry = Book6MethodologyRegistry()
    registry.register_methodology(methodology("routing-attribution-methodology", "1"))
    with pytest.raises(ComparabilityError, match="requires methodology"):
        _authorize(*FC05, "routing-attribution-methodology@1", registry)


def test_r1_d1_a5_the_exact_required_methodology_authorizes() -> None:
    """A5: exact identity, registered, current, and authorized for the row."""

    assert (
        _authorize(*FC05, "routing-attribution-methodology@1", _pair_registry()) == "AUTHORIZED"
    )


def test_r1_d1_a5b_identity_alone_is_not_enough_without_row_authority() -> None:
    """A5's second half: the methodology must declare the row itself.

    A methodology that resolves and matches the required name exactly, but does
    not carry the canonical row authority, is still refused.

    R2 tightened the reason this fires. Under R1 a caller-built object reached
    the row-authority gate at all; under R2 a mutated ``authorized_corpus_row_ids``
    is part of the CONTENT DIGEST, so it is caught one condition earlier, at the
    canonical-content seal. The claim under test is unchanged and in fact
    stronger: the identity alone licenses nothing. The row-authority condition
    itself is exercised directly in ``test_book6_hardening_r2.py``.
    """

    registry = Book6MethodologyRegistry()
    registry.register_methodology(methodology("routing-attribution-methodology", "1"))
    with pytest.raises(ComparabilityError, match="content does not match"):
        _authorize(*FC05, "routing-attribution-methodology@1", registry)


def test_r1_d1_a6_a_superseded_methodology_stops_authorizing() -> None:
    """A6: authority decays on a methodology revision; it does not carry over."""

    registry = _pair_registry()
    assert _authorize(*FC05, "routing-attribution-methodology@1", registry) == "AUTHORIZED"
    registry.supersede_methodology(comparison_methodology("FC-05", version="2"))
    with pytest.raises(ComparabilityError, match="superseded"):
        _authorize(*FC05, "routing-attribution-methodology@1", registry)
    # A new methodology version does NOT inherit the comparison. The corpus row
    # names one exact identity, so licensing a new version is an explicit
    # operator act on the corpus, never a side effect of a version bump.
    with pytest.raises(ComparabilityError, match="requires methodology"):
        _authorize(*FC05, "routing-attribution-methodology@2", registry)


def test_r1_d1_a6b_a_locally_invalidated_methodology_stops_authorizing() -> None:
    registry = _pair_registry()
    registry.invalidate_methodology(
        "routing-attribution-methodology@1", reason="vendor restated the attribution window"
    )
    with pytest.raises(ComparabilityError, match="invalidated locally"):
        _authorize(*FC05, "routing-attribution-methodology@1", registry)


def test_r1_d1_no_substring_or_alias_matching() -> None:
    """A near-miss name is not the required methodology."""

    registry = _pair_registry()
    for near_miss in (
        "routing-attribution",
        "routing-attribution-methodology-v2",
        "RoutING-attribution-methodology@1",
        "routing-attribution-methodology@",
        "@1",
    ):
        with pytest.raises(ComparabilityError):
            _authorize(*FC05, near_miss, registry)


def test_r1_d5_the_five_separated_stores_all_exist() -> None:
    engine, *_ = build_engine()
    registry = engine.registry
    assert hasattr(registry, "_definitions")  # definition registry
    assert isinstance(registry.methodologies, Book6MethodologyRegistry)  # methodology registry
    assert hasattr(registry, "_measurements")  # measurement records
    assert hasattr(registry, "_normalization_rules")  # normalization rules
    assert isinstance(registry.state_rules, StateRuleRegistry)  # state rules
    assert METHODOLOGY_REGISTRY_PRESENT is True


def test_r1_d5_methodology_identity_is_versioned_and_exact() -> None:
    assert METHODOLOGY_IDENTITY_IS_VERSIONED is True
    assert methodology_identity("m", "2") == "m@2"
    assert parse_methodology_identity("a@b@3") == ("a@b", "3")
    assert parse_methodology_identity("bare") == ("bare", None)
    with pytest.raises(MethodologyRegistryError):
        methodology_identity("m", "")
    with pytest.raises(MethodologyRegistryError):
        parse_methodology_identity("@1")


def test_r1_d5_an_empty_methodology_ref_resolves_to_nothing() -> None:
    with pytest.raises(MethodologyRegistryError, match="empty string"):
        _pair_registry().resolve_methodology("")


def test_r1_d5_a_metric_definition_may_not_name_an_unregistered_methodology() -> None:
    engine, *_ = build_engine()
    unresolvable = definition(METRIC).model_copy(
        update={"methodology": methodology("never:registered")}
    )
    with pytest.raises(Book6RegistryError, match="not registered"):
        engine.registry.register_definition(unresolvable)


def test_r1_d5_a_measurement_may_not_name_an_unregistered_methodology() -> None:
    engine = build_engine_with_definitions(definition(METRIC))
    observation = windowed_observation(
        "obs:1",
        METRIC,
        value=7.0,
        missingness=MissingnessState.OBSERVED,
        claim_refs=(CLAIM_ID,),
        methodology_ref="never:registered",
    )
    with pytest.raises(Book6RegistryError, match="not registered"):
        engine.registry.register_measurement(observation)


def test_r1_d5_a_measurement_loses_authority_when_its_methodology_is_invalidated() -> None:
    engine = build_engine_with_definitions(definition(METRIC))
    register_measurement(
        engine,
        windowed_observation(
            "obs:1", METRIC, value=7.0, missingness=MissingnessState.OBSERVED, claim_refs=(CLAIM_ID,)
        ),
    )
    assert engine.current_value("obs:1") == 7.0
    engine.registry.methodologies.invalidate_methodology(
        "book6-methodology@1", reason="methodology withdrawn"
    )
    with pytest.raises(Book6RegistryError, match="invalidated"):
        engine.current_value("obs:1")


def test_r1_d5_no_free_string_methodology_authority_constant() -> None:
    assert NO_FREE_STRING_METHODOLOGY_AUTHORITY is True


def test_r1_d1_every_conditional_row_requires_a_versioned_identity() -> None:
    """Phase 11: ``required_methodology`` is mechanically meaningful."""

    for row in FALSE_COMPARISON_CORPUS:
        if row.required_methodology is None:
            continue
        ref, version = parse_methodology_identity(row.required_methodology)
        assert ref and version, row.row_id
        assert row.row_id.startswith("FC-")


def test_r1_d1_corpus_row_lookup_is_symmetric() -> None:
    assert corpus_row_for(*FC05).row_id == "FC-05"
    assert corpus_row_for(FC05[1], FC05[0]).row_id == "FC-05"


# ===========================================================================
# R1-D2 — price source has no Book 2 authority
# ===========================================================================


def _valuation_engine(*claim_ids: str):
    engine, claim_store, _evidence, service = build_engine(*(claim_ids or (CLAIM_ID,)))
    return engine, claim_store, service


def test_r1_d2_a_price_observation_must_cite_book_2_claims() -> None:
    """The field is required, so an unattributed price cannot be built."""

    assert PriceObservation.model_fields["source_claim_refs"].is_required()
    with pytest.raises(ValidationError):
        PriceObservation(
            price_observation_id="price:1",
            price_class=PriceObservationClass.MARKET_OBSERVATION,
            source_ref="venue:index",
            price=1.0,
            valid_time=NOW,
            observed_at=NOW,
            coverage=1.0,
        )


def test_r1_d2_an_empty_claim_ref_tuple_is_refused() -> None:
    with pytest.raises(ValidationError):
        price("price:1", claim_refs=())


def test_r1_d2_the_fake_price_source_reproducer_is_now_refused() -> None:
    """R1-D2 reproducer: ``source_ref="fake:oracle"`` with no Book 2 backing.

    Before R1 this authorized a protocol collateral mark. Now the cited claim is
    resolved through the Book 2 provenance adapter at authority time, so a
    fabricated attribution carries nothing regardless of its string.
    """

    engine, *_ = _valuation_engine("fixture:claim:absent")
    forged = valuation(
        "val:1",
        price_observation=price(
            "price:1",
            source_ref="fake:oracle",
            claim_refs=("fixture:claim:never-registered",),
        ),
    )
    with pytest.raises(ValuationError, match="no current Book 2 authority"):
        engine.authorize_current_valuation(forged, as_of=NOW)


def test_r1_d2_a_source_ref_string_alone_is_never_epistemic_evidence() -> None:
    engine, *_ = _valuation_engine()
    good = valuation("val:1", price_observation=price("price:1"))
    assert engine.authorize_current_valuation(good, as_of=NOW) is good
    # the source_ref is unchanged and irrelevant to authority: only the Book 2
    # claim behind it decides
    assert good.price.source_ref == "venue:index"


@pytest.mark.parametrize("decayed_state", ["STALE", "CONTESTED", "REJECTED"])
def test_r1_d2_and_d4_price_book2_decay_propagates(decayed_state: str) -> None:
    """Phase 14: a decayed price claim removes current valuation authority.

    The record is never deleted or rewritten; only the authority decays.
    """

    engine, claim_store, service = _valuation_engine(PRICE_CLAIM)
    good = valuation("val:1", price_observation=price("price:1", claim_refs=(PRICE_CLAIM,)))
    assert engine.authorize_current_valuation(good, as_of=NOW) is good
    decay_claim(service, claim_store, PRICE_CLAIM, decayed_state)
    with pytest.raises(ValuationError, match="no current Book 2 authority"):
        engine.authorize_current_valuation(good, as_of=NOW)
    # history is preserved: the observation is unchanged and still readable
    assert good.price.source_claim_refs == (PRICE_CLAIM,)
    assert good.price.price == 100.0


def test_r1_d4_price_authority_restores_when_book_2_restores() -> None:
    """Rejection is not an irreversible tombstone."""

    engine, claim_store, service = _valuation_engine(PRICE_CLAIM)
    good = valuation("val:1", price_observation=price("price:1", claim_refs=(PRICE_CLAIM,)))
    decay_claim(service, claim_store, PRICE_CLAIM, "STALE")
    with pytest.raises(ValuationError):
        engine.authorize_current_valuation(good, as_of=NOW)
    decay_claim(service, claim_store, PRICE_CLAIM, "OBSERVED", at=NOW + timedelta(days=2))
    assert engine.authorize_current_valuation(good, as_of=NOW) is good


def test_r1_d2_evidence_cited_by_a_price_claim_must_not_be_detached() -> None:
    engine, claim_store, _service = _valuation_engine(PRICE_CLAIM)
    forged = valuation("val:1", price_observation=price("price:1", claim_refs=(PRICE_CLAIM,)))
    detached = claim_store.require(PRICE_CLAIM).model_copy(
        update={"evidence_refs": ("book6-detached-evidence",)}
    )
    claim_store._versions[PRICE_CLAIM] = [detached]  # type: ignore[attr-defined]
    with pytest.raises(ValuationError, match="no current Book 2 authority"):
        engine.authorize_current_valuation(forged, as_of=NOW)


# ===========================================================================
# Phase 4 — price source / purpose context are two separate requirements
# ===========================================================================


def test_r1_d4_valid_book2_claim_with_the_wrong_price_class_is_refused() -> None:
    """Book 2 evidence is necessary but not sufficient: purpose still decides."""

    engine, *_ = _valuation_engine(PRICE_CLAIM)
    with pytest.raises((ValidationError, ValuationError), match="not admissible"):
        valuation(
            "val:1",
            purpose=ValuationPurpose.REDEMPTION_ACCOUNTING.value,
            price_observation=price(
                "price:1", price_class=PriceObservationClass.MARKET_OBSERVATION.value
            ),
        )
    # and at the decision boundary, by swapping the class on an existing record
    good = valuation(
        "val:1",
        purpose=ValuationPurpose.REDEMPTION_ACCOUNTING.value,
        price_observation=price(
            "price:1",
            price_class=PriceObservationClass.OFFICIAL_REDEMPTION_VALUE.value,
            claim_refs=(PRICE_CLAIM,),
        ),
    )
    forged = good.model_copy(
        update={
            "price": good.price.model_copy(
                update={"price_class": PriceObservationClass.MARKET_OBSERVATION}
            )
        }
    )
    with pytest.raises(ValuationError, match="not admissible"):
        engine.authorize_current_valuation(forged, as_of=NOW)


def test_r1_d4_correct_price_class_with_a_fake_book2_claim_is_refused() -> None:
    engine, *_ = _valuation_engine("fixture:claim:other")
    forged = valuation(
        "val:1",
        purpose=ValuationPurpose.REDEMPTION_ACCOUNTING.value,
        price_observation=price(
            "price:1",
            price_class=PriceObservationClass.OFFICIAL_REDEMPTION_VALUE.value,
            claim_refs=("fixture:claim:invented",),
        ),
    )
    with pytest.raises(ValuationError, match="no current Book 2 authority"):
        engine.authorize_current_valuation(forged, as_of=NOW)


def test_r1_d4_both_requirements_met_authorizes() -> None:
    engine, *_ = _valuation_engine(PRICE_CLAIM)
    good = valuation(
        "val:1",
        purpose=ValuationPurpose.REDEMPTION_ACCOUNTING.value,
        price_observation=price(
            "price:1",
            price_class=PriceObservationClass.OFFICIAL_REDEMPTION_VALUE.value,
            claim_refs=(PRICE_CLAIM,),
        ),
    )
    assert engine.authorize_current_valuation(good, as_of=NOW) is good


def test_r1_d4_evidence_exists_is_not_admissible_for_purpose() -> None:
    assert PRICE_AUTHORITY_IS_PURPOSE_SPECIFIC is True
    assert NO_GLOBAL_PRICE_SOURCE_CLASS is True


def test_r1_d4_a_valuation_may_not_name_an_unregistered_conversion_methodology() -> None:
    engine, *_ = _valuation_engine()
    forged = valuation("val:1", conversion_methodology_ref="never:registered@1")
    with pytest.raises(ValuationError, match="resolves to nothing"):
        engine.authorize_current_valuation(forged, as_of=NOW)


# ===========================================================================
# R1-D3 — stale current price, and bitemporal preservation
# ===========================================================================


def test_r1_d3_the_stale_current_valuation_reproducer_is_now_refused() -> None:
    """R1-D3 reproducer: a 30-day-old price with a 1-hour staleness bound.

    Before R1 ``authorize_valuation`` returned this valuation unchanged.
    """

    engine, *_ = _valuation_engine(PRICE_CLAIM)
    stale = valuation(
        "val:stale",
        price_observation=price("price:stale", claim_refs=(PRICE_CLAIM,), observed_at=NOW - timedelta(days=30)),
        observed_at=NOW,
        staleness_bound_seconds=3600,
    )
    assert stale.is_stale_at(NOW) is True
    with pytest.raises(ValuationError, match="stale"):
        engine.authorize_current_valuation(stale, as_of=NOW)


def test_r1_d3_a_fresh_price_at_the_same_instant_authorizes() -> None:
    engine, *_ = _valuation_engine(PRICE_CLAIM)
    fresh = valuation(
        "val:fresh",
        price_observation=price("price:fresh", claim_refs=(PRICE_CLAIM,), observed_at=NOW - timedelta(seconds=60)),
        observed_at=NOW,
    )
    assert engine.authorize_current_valuation(fresh, as_of=NOW) is fresh


def test_r1_d3_staleness_is_evaluated_at_the_explicit_as_of_not_wall_clock() -> None:
    """No hidden clock: the same valuation is fresh or stale by ``as_of`` alone."""

    engine, *_ = _valuation_engine(PRICE_CLAIM)
    observed = valuation(
        "val:1",
        price_observation=price("price:1", claim_refs=(PRICE_CLAIM,), observed_at=NOW),
        observed_at=NOW,
        staleness_bound_seconds=3600,
    )
    assert engine.authorize_current_valuation(observed, as_of=NOW + timedelta(seconds=60))
    with pytest.raises(ValuationError, match="stale"):
        engine.authorize_current_valuation(observed, as_of=NOW + timedelta(seconds=7200))


def test_r1_d3_current_unavailable_is_not_historically_invalid() -> None:
    """Phase 5: the two authorities are separate and both are explicit."""

    engine, *_ = _valuation_engine(PRICE_CLAIM)
    historical = valuation(
        "val:1",
        price_observation=price(
            "price:1", claim_refs=(PRICE_CLAIM,), observed_at=NOW - timedelta(days=30)
        ),
        observed_at=NOW - timedelta(days=30),
        valid_time=NOW - timedelta(days=30),
    )
    with pytest.raises(ValuationError, match="stale"):
        engine.authorize_current_valuation(historical, as_of=NOW)
    # the price was fresh when the valuation was observed, so the HISTORICAL
    # record's shape stands
    assert engine.validate_recorded_historical_shape(historical) is historical


def test_r1_d3_a_valuation_already_stale_when_observed_is_not_historically_valid() -> None:
    engine, *_ = _valuation_engine(PRICE_CLAIM)
    bogus = valuation(
        "val:1",
        price_observation=price("price:1", claim_refs=(PRICE_CLAIM,), observed_at=NOW - timedelta(days=30)),
        observed_at=NOW,
    )
    with pytest.raises(ValuationError, match="already stale"):
        engine.validate_recorded_historical_shape(bogus)


def test_r1_d3_historical_validation_still_requires_book_2_authority() -> None:
    """R1 asserted the historical path re-checks Book 2 CURRENT authority.

    R2-D4 REVERSED this on purpose, and that reversal is the point of the R2
    round. Re-checking ``require_current=True`` on the historical path meant a
    price claim that was valid at observation time and later went REJECTED
    retroactively erased a historical statement - which is exactly the
    conflation ``CURRENT UNAVAILABLE != HISTORICALLY INVALID`` forbids.

    The historical path now proves RECORD SHAPE only and refuses to claim
    epistemic backing it cannot establish; the CURRENT authority question is
    reported separately and labelled. Both halves are asserted below, and the
    current path still hard-requires Book 2 authority.
    """

    engine, claim_store, service = _valuation_engine(PRICE_CLAIM)
    observed = NOW - timedelta(days=30)
    historical = valuation(
        "val:1",
        price_observation=price("price:1", claim_refs=(PRICE_CLAIM,), observed_at=observed),
        observed_at=observed + timedelta(seconds=60),
        valid_time=observed + timedelta(seconds=60),
    )
    assert engine.validate_recorded_historical_shape(historical) is historical
    assert engine.historical_authority_status(historical).current_claims_backed is True

    decay_claim(service, claim_store, PRICE_CLAIM, "REJECTED")

    # the record is preserved...
    assert engine.validate_recorded_historical_shape(historical) is historical
    report = engine.historical_authority_status(historical)
    # ...but Book 6 makes NO claim that it is revalidated authority
    assert report.current_claims_backed is False
    assert report.replay_available is False
    assert report.replay_capability == "NOT_IMPLEMENTED"

    # and the CURRENT path still refuses outright
    with pytest.raises(ValuationError, match="no current Book 2 authority"):
        engine.authorize_current_valuation(historical, as_of=NOW)


def test_r1_d3_the_ambiguous_single_api_is_gone() -> None:
    """Explicit, separate authorities - not one overloaded method."""

    engine, *_ = _valuation_engine()
    public = {
        name for name in dir(engine) if not name.startswith("_")
    }
    valuation_surface = sorted(
        name
        for name in public
        if callable(getattr(engine, name))
        and (
            "valuation" in name.lower()
            or "historical" in name.lower()
        )
    )
    assert valuation_surface == [
        "authorize_current_valuation",
        "historical_authority_status",
        "validate_recorded_historical_shape",
    ]


# ===========================================================================
# R1-D4 — fake coverage-sufficiency rule can create DATA_COMPLETE
# ===========================================================================


def _observed_dimension(dimension_id: str = METRIC):
    from crypto_systems_intelligence_atlas.book6_states import StateDimension

    return StateDimension(
        dimension_id=dimension_id,
        state=StateName.INSUFFICIENT_DATA,
        state_class=StateClass.A_AVAILABILITY,
        measurement_refs=("obs:1",),
        methodology_ref="book6-methodology@1",
        valid_time=T1,
        observed_at=T1,
        missingness=MissingnessState.OBSERVED,
        coverage_observation_id="cov:1",
    )


def _vector(**overrides: object) -> FundamentalStateVector:
    payload: dict[str, object] = {
        "subject_ref": "fixture:chain:alpha",
        "schema_ref": "schema:book6:1",
        "as_of_valid_time": T1,
        "dimensions": (_observed_dimension(),),
        "coverage_sufficiency_rule_refs": ("fake:rule",),
    }
    payload.update(overrides)
    return FundamentalStateVector(**payload)  # type: ignore[arg-type]


def test_r1_d4_the_fake_coverage_rule_reproducer_is_now_refused() -> None:
    """R1-D4 reproducer: ``coverage_sufficiency_rule_refs=("fake:rule",)``.

    Before R1 this produced ``DATA_COMPLETE`` with zero ratified sufficiency
    rules in existence.
    """

    assert _vector().data_status is VectorStatus.DATA_INCOMPLETE


@pytest.mark.parametrize(
    "ref",
    ["fake:rule", "covrule:synthetic:1", "", "anything", "csia:book6:coverage-rule-registry:1"],
)
def test_r1_d4_no_arbitrary_ref_reaches_data_complete(ref: str) -> None:
    vector = _vector(coverage_sufficiency_rule_refs=(ref,) if ref else ())
    assert vector.data_status is VectorStatus.DATA_INCOMPLETE


def test_r1_d4_an_attestation_alone_is_not_enough() -> None:
    """Phase 8: the raw refs still have to agree with the attestation."""

    vector = _vector(
        coverage_sufficiency_rule_refs=(),
        sufficiency_attestation=CoverageSufficiencyAttestation(
            rule_ids=("fake:rule",), scope_metric_ids=(METRIC,), attested_at=T1, registry_identity="x"
        ),
    )
    assert vector.data_status is VectorStatus.DATA_INCOMPLETE


def test_r1_d4_a_scope_that_misses_a_dimension_fails_closed() -> None:
    vector = _vector(
        coverage_sufficiency_rule_refs=("covrule:synthetic:1",),
        sufficiency_attestation=CoverageSufficiencyAttestation(
            rule_ids=("covrule:synthetic:1",),
            scope_metric_ids=("metric.other",),
            attested_at=T1,
            registry_identity="x",
        ),
    )
    assert vector.data_status is VectorStatus.DATA_INCOMPLETE


def test_r1_d4_coverage_rule_bootstrap_count_is_zero() -> None:
    assert COVERAGE_SUFFICIENCY_RULES_RATIFIED_AT_BOOTSTRAP == 0
    assert INDIVIDUAL_STATE_RULES_RATIFIED_AT_BOOTSTRAP == 0
    engine, *_ = build_engine()
    assert engine.registry.coverage_rules.ratified_count() == 0
    assert engine.registry.state_rules.ratified_count() == 0


def test_r1_d4_registration_is_not_ratification() -> None:
    registry = CoverageRuleRegistry()
    registry.register(coverage_rule("covrule:1", scope_metric_id=METRIC))
    assert registry.ratified_count() == 0
    assert registry.registered_rule("covrule:1").status is CoverageRuleRatificationStatus.UNRATIFIED
    assert COVERAGE_RULE_REF_IS_NOT_AUTHORITY is True


def test_r1_d4_an_unratified_rule_cannot_authorize_sufficiency() -> None:
    registry = CoverageRuleRegistry()
    registry.register(coverage_rule("covrule:1", scope_metric_id=METRIC))
    with pytest.raises(CoverageRuleError, match="not ratified"):
        registry.authorize(metric_id=METRIC, rule_ref="covrule:1")
    assert registry.is_sufficient(metric_id=METRIC, rule_ref="covrule:1") is False


def test_r1_d4_an_unknown_rule_ref_cannot_authorize_sufficiency() -> None:
    registry = CoverageRuleRegistry()
    with pytest.raises(CoverageRuleError, match="not registered"):
        registry.authorize(metric_id=METRIC, rule_ref="fake:rule")


def test_r1_d4_a_wrong_metric_scope_cannot_authorize_sufficiency() -> None:
    registry = CoverageRuleRegistry()
    registry.register(coverage_rule("covrule:1", scope_metric_id="metric.other"))
    registry.ratify("covrule:1", operator="synthetic", at=NOW)
    with pytest.raises(CoverageRuleError, match="scoped to"):
        registry.authorize(metric_id=METRIC, rule_ref="covrule:1")


def test_r1_d4_a_superseded_rule_loses_its_ratification() -> None:
    registry = CoverageRuleRegistry()
    registry.register(coverage_rule("covrule:1", scope_metric_id=METRIC, version="1"))
    registry.ratify("covrule:1", operator="synthetic", at=NOW)
    assert registry.ratified_count() == 1
    registry.supersede(coverage_rule("covrule:1", scope_metric_id=METRIC, version="2"))
    assert registry.ratified_count() == 0
    with pytest.raises(CoverageRuleError, match="not ratified"):
        registry.authorize(metric_id=METRIC, rule_ref="covrule:1")
    assert [r.version for r in registry.superseded_versions("covrule:1")] == ["1"]


def test_r1_d4_a_valid_synthetic_ratified_rule_reaches_data_complete() -> None:
    """Phase 8: a locally ratified synthetic rule MAY produce DATA_COMPLETE."""

    engine = build_engine_with_definitions(definition(METRIC))
    register_measurement(
        engine,
        windowed_observation(
            "obs:1", METRIC, value=7.0, missingness=MissingnessState.OBSERVED, claim_refs=(CLAIM_ID,)
        ),
    )
    engine.registry.register_coverage(coverage("obs:1", 1.0))
    engine.registry.coverage_rules.register(coverage_rule("covrule:1", scope_metric_id=METRIC))
    engine.registry.coverage_rules.ratify("covrule:1", operator="synthetic", at=T1)

    vector = engine.build_availability_vector(
        subject_ref="fixture:chain:alpha",
        schema_ref="schema:book6:1",
        as_of_valid_time=T1,
        observed_at=T1,
        measurement_ids=("obs:1",),
        methodology_ref="book6-methodology@1",
    )
    assert vector.sufficiency_attestation is not None
    assert engine.data_status(vector) is VectorStatus.DATA_COMPLETE


def test_r1_d4_bootstrap_data_status_fails_closed() -> None:
    """Same stack, no ratified coverage rule: DATA_INCOMPLETE."""

    engine = build_engine_with_definitions(definition(METRIC))
    register_measurement(
        engine,
        windowed_observation(
            "obs:1", METRIC, value=7.0, missingness=MissingnessState.OBSERVED, claim_refs=(CLAIM_ID,)
        ),
    )
    engine.registry.register_coverage(coverage("obs:1", 1.0))
    vector = engine.build_availability_vector(
        subject_ref="fixture:chain:alpha",
        schema_ref="schema:book6:1",
        as_of_valid_time=T1,
        observed_at=T1,
        measurement_ids=("obs:1",),
        methodology_ref="book6-methodology@1",
    )
    assert vector.sufficiency_attestation is None
    assert engine.data_status(vector) is VectorStatus.DATA_INCOMPLETE


def test_r1_d4_a_full_coverage_fraction_alone_never_reaches_data_complete() -> None:
    """``observed_fraction=1.0`` is not a sufficiency verdict."""

    engine = build_engine_with_definitions(definition(METRIC))
    register_measurement(
        engine,
        windowed_observation(
            "obs:1", METRIC, value=7.0, missingness=MissingnessState.OBSERVED, claim_refs=(CLAIM_ID,)
        ),
    )
    engine.registry.register_coverage(coverage("obs:1", 1.0, sufficiency_rule_ref="fake:rule"))
    assert engine.availability_state("obs:1") is StateName.RULE_NOT_RATIFIED
    vector = engine.build_availability_vector(
        subject_ref="fixture:chain:alpha",
        schema_ref="schema:book6:1",
        as_of_valid_time=T1,
        observed_at=T1,
        measurement_ids=("obs:1",),
        methodology_ref="book6-methodology@1",
    )
    assert engine.data_status(vector) is VectorStatus.DATA_INCOMPLETE
    assert NUMERIC_COVERAGE_IS_NOT_SUFFICIENCY is True
    assert DATA_COMPLETE_REQUIRES_ATTESTED_SUPPORT is True


def test_r1_d6_coverage_rule_constants() -> None:
    assert COVERAGE_RULE_REF_IS_NOT_AUTHORITY is True
    assert NUMERIC_COVERAGE_IS_NOT_SUFFICIENCY is True
    assert NO_DEFAULT_METRIC_EXISTS is True


# ===========================================================================
# R1-D6 — normalized value integrity
# ===========================================================================


def _normalization_stack():
    engine = build_engine_with_definitions(
        definition(METRIC),
        definition(NORMALIZED_METRIC, unit="per-user"),
        methodologies=(normalization_methodology(),),
    )
    for measurement_id, value in (("obs:native", 10.0), ("obs:divisor", 2.0)):
        register_measurement(
            engine,
            windowed_observation(
                measurement_id,
                METRIC,
                value=value,
                missingness=MissingnessState.OBSERVED,
                claim_refs=(CLAIM_ID,),
            ),
        )
    rule = NormalizationRule(
        normalization_rule_id="normrule:1",
        input_metric_definition_ref=METRIC,
        input_measurement_refs=("obs:native",),
        normalization_type=NormalizationType.PER_USER,
        transformation="x = native / users",
        denominator_ref="obs:divisor",
        methodology_ref="book6-normalization@1",
        valid_time=T1,
        version="1",
        output_metric_definition_ref=NORMALIZED_METRIC,
    )
    engine.registry.register_normalization_rule(rule)
    return engine, rule


def _product(value: float) -> NormalizedMeasurement:
    return NormalizedMeasurement(
        normalized_measurement_id="norm:1",
        normalization_rule_id="normrule:1",
        native_measurement_refs=("obs:native",),
        normalized_metric_definition_ref=NORMALIZED_METRIC,
        value=value,
        unit="per-user",
        valid_time=T1,
    )


def test_r1_d6_the_forged_normalized_value_reproducer_is_now_refused() -> None:
    """R1-D6 reproducer: native 10 / divisor 2 (5.0) asserted as 999.

    Before R1 the engine authorized 999 without looking at the inputs.
    """

    engine, rule = _normalization_stack()
    with pytest.raises(Book6EngineError, match="deterministic function of its inputs"):
        engine.normalize(_product(999.0), rule)


def test_r1_d6_the_correctly_derived_value_authorizes() -> None:
    engine, rule = _normalization_stack()
    product = _product(5.0)
    assert engine.normalize(product, rule) is product
    assert NORMALIZED_VALUE_IS_RECOMPUTED is True


def test_r1_d6_a_near_miss_value_is_still_refused() -> None:
    engine, rule = _normalization_stack()
    for wrong in (4.9, 5.1, 0.0, -5.0):
        with pytest.raises(Book6EngineError):
            engine.normalize(_product(wrong), rule)


def test_r1_d6_compute_normalized_value_is_deterministic_and_total() -> None:
    rule = NormalizationRule(
        normalization_rule_id="n",
        input_metric_definition_ref="m",
        input_measurement_refs=("obs:1",),
        normalization_type=NormalizationType.PER_USER,
        transformation="x = native / users",
        denominator_ref="obs:d",
        methodology_ref="x@1",
        valid_time=T1,
        version="1",
        output_metric_definition_ref="o",
    )
    assert compute_normalized_value(rule, native_value=10.0, divisor_value=2.0) == 5.0
    from crypto_systems_intelligence_atlas.book6_normalization import NormalizationRuleError

    with pytest.raises(NormalizationRuleError, match="observed-zero divisor"):
        compute_normalized_value(rule, native_value=10.0, divisor_value=0.0)
    with pytest.raises(NormalizationRuleError, match="requires a declared divisor"):
        compute_normalized_value(rule, native_value=10.0)


@pytest.mark.parametrize("kind", sorted(BASE_RELATIVE_NORMALIZATIONS), ids=lambda k: k.value)
def test_r1_d6_base_relative_normalizations_are_computed_not_asserted(kind) -> None:
    payload = {
        "normalization_rule_id": "n",
        "input_metric_definition_ref": "m",
        "input_measurement_refs": ("obs:1",),
        "normalization_type": kind,
        "transformation": "x = native relative to base",
        "methodology_ref": "x@1",
        "valid_time": T1,
        "version": "1",
        "output_metric_definition_ref": "o",
        "base_measurement_ref": "obs:base",
    }
    rule = NormalizationRule(**payload)  # type: ignore[arg-type]
    expected = (10.0 - 4.0) / 4.0 if kind is NormalizationType.GROWTH_RATE else 10.0 / 4.0
    assert compute_normalized_value(rule, native_value=10.0, base_value=4.0) == expected


def test_r1_d6_a_zero_divisor_yields_undefined_not_zero_or_infinity() -> None:
    rule = NormalizationRule(
        normalization_rule_id="n",
        input_metric_definition_ref="m",
        input_measurement_refs=("obs:1",),
        normalization_type=NormalizationType.PER_USER,
        transformation="x = native / users",
        denominator_ref="obs:zero",
        methodology_ref="x@1",
        valid_time=T1,
        version="1",
        output_metric_definition_ref="o",
    )
    from crypto_systems_intelligence_atlas.book6_normalization import NormalizationRuleError

    with pytest.raises(NormalizationRuleError, match="UNDEFINED"):
        compute_normalized_value(rule, native_value=10.0, divisor_value=0.0)


# ===========================================================================
# Phase 9 — normalization methodology and input-metric closure
# ===========================================================================


def test_r1_d9_a_rule_methodology_that_resolves_to_nothing_is_refused() -> None:
    """A registered rule naming an unregistered methodology authorizes nothing."""

    engine = build_engine_with_definitions(
        definition(METRIC),
        definition(NORMALIZED_METRIC, unit="per-user"),
    )
    for measurement_id, value in (("obs:native", 10.0), ("obs:divisor", 2.0)):
        register_measurement(
            engine,
            windowed_observation(
                measurement_id,
                METRIC,
                value=value,
                missingness=MissingnessState.OBSERVED,
                claim_refs=(CLAIM_ID,),
            ),
        )
    rule = NormalizationRule(
        normalization_rule_id="normrule:1",
        input_metric_definition_ref=METRIC,
        input_measurement_refs=("obs:native",),
        normalization_type=NormalizationType.PER_USER,
        transformation="x = native / users",
        denominator_ref="obs:divisor",
        methodology_ref="never:registered@1",
        valid_time=T1,
        version="1",
        output_metric_definition_ref=NORMALIZED_METRIC,
    )
    engine.registry.register_normalization_rule(rule)
    with pytest.raises(Book6EngineError, match="resolves to nothing"):
        engine.normalize(_product(5.0), rule)


def test_r1_d9_a_rule_methodology_that_does_not_declare_its_inputs_is_refused() -> None:
    """A methodology that never declared the input metric cannot reinterpret it."""

    engine, _registered = _normalization_stack()
    engine.registry.register_methodology(
        normalization_methodology(version="2", input_methodology_refs=("some:other@1",))
    )
    mismatched = _registered.model_copy(
        update={
            "normalization_rule_id": "normrule:2",
            "methodology_ref": "book6-normalization@2",
        }
    )
    engine.registry.register_normalization_rule(mismatched)
    product = _product(5.0).model_copy(update={"normalization_rule_id": "normrule:2"})
    with pytest.raises(Book6EngineError, match="does not declare input methodology"):
        engine.normalize(product, mismatched)


def test_r1_d9_a_matching_rule_methodology_continues() -> None:
    engine, rule = _normalization_stack()
    assert engine.normalize(_product(5.0), rule) is not None


def test_r1_d9_a_rule_for_metric_a_may_not_consume_metric_b() -> None:
    engine = build_engine_with_definitions(
        definition(METRIC),
        definition("metric.elsewhere"),
        methodologies=(normalization_methodology(),),
    )
    for measurement_id, metric in (
        ("obs:native", "metric.elsewhere"),
        ("obs:divisor", "metric.elsewhere"),
    ):
        register_measurement(
            engine,
            windowed_observation(
                measurement_id,
                metric,
                value=10.0,
                missingness=MissingnessState.OBSERVED,
                claim_refs=(CLAIM_ID,),
            ),
        )
    rule = NormalizationRule(
        normalization_rule_id="normrule:1",
        input_metric_definition_ref=METRIC,
        input_measurement_refs=("obs:native",),
        normalization_type=NormalizationType.PER_USER,
        transformation="x = native / users",
        denominator_ref="obs:divisor",
        methodology_ref="book6-normalization@1",
        valid_time=T1,
        version="1",
        output_metric_definition_ref="metric.elsewhere",
    )
    engine.registry.register_normalization_rule(rule)
    with pytest.raises(Book6EngineError, match="may not normalize a different metric"):
        engine.normalize(
            NormalizedMeasurement(
                normalized_measurement_id="norm:1",
                normalization_rule_id="normrule:1",
                native_measurement_refs=("obs:native",),
                normalized_metric_definition_ref="metric.elsewhere",
                value=1.0,
                unit="native-unit",
                valid_time=T1,
            ),
            rule,
        )


def test_r1_d9_a_product_unit_may_not_diverge_from_its_output_metric() -> None:
    engine, rule = _normalization_stack()
    wrong_unit = _product(5.0).model_copy(update={"unit": "tokens-per-fortnight"})
    with pytest.raises(Book6EngineError, match="does not match output metric"):
        engine.normalize(wrong_unit, rule)


def test_r1_d6_native_before_normalized_is_still_enforced() -> None:
    """The pre-R1 native-lineage seal is not weakened by the new closures."""

    engine, rule = _normalization_stack()
    stripped = _product(5.0).model_copy(update={"native_measurement_refs": ()})
    with pytest.raises(Exception):
        engine.normalize(stripped, rule)


# ===========================================================================
# Phase 12 — model_copy / post-construction attacks (C1..C10)
# ===========================================================================


def test_r1_c1_comparison_methodology_replaced_by_a_fake_ref() -> None:
    engine = build_engine_with_definitions(
        definition(FC05[0]), definition(FC05[1]), methodologies=(comparison_methodology("FC-05"),)
    )
    assert engine.authorize_comparison(*FC05, methodology_ref="routing-attribution-methodology@1")
    for fake in ("fake:anything", "methodology:whatever", "x@1"):
        with pytest.raises(Exception):
            engine.authorize_comparison(*FC05, methodology_ref=fake)


def test_r1_c2_normalization_methodology_replaced() -> None:
    """C2: each fake methodology is refused when the rule is REGISTERED with it.

    Note the boundary: the engine resolves the rule it is given from the
    registry by id, so a mutated copy handed in by a caller cannot change which
    rule is evaluated at all — and the registered rule's own methodology is
    re-resolved live every time.
    """

    for fake in ("never:registered@1", "fake", "methodology:whatever"):
        engine = build_engine_with_definitions(
            definition(METRIC),
            definition(NORMALIZED_METRIC, unit="per-user"),
        )
        for measurement_id, value in (("obs:native", 10.0), ("obs:divisor", 2.0)):
            register_measurement(
                engine,
                windowed_observation(
                    measurement_id,
                    METRIC,
                    value=value,
                    missingness=MissingnessState.OBSERVED,
                    claim_refs=(CLAIM_ID,),
                ),
            )
        rule = NormalizationRule(
            normalization_rule_id="normrule:1",
            input_metric_definition_ref=METRIC,
            input_measurement_refs=("obs:native",),
            normalization_type=NormalizationType.PER_USER,
            transformation="x = native / users",
            denominator_ref="obs:divisor",
            methodology_ref=fake,
            valid_time=T1,
            version="1",
            output_metric_definition_ref=NORMALIZED_METRIC,
        )
        engine.registry.register_normalization_rule(rule)
        with pytest.raises(Book6EngineError, match="resolves to nothing"):
            engine.normalize(_product(5.0), rule)


def test_r1_c2b_a_normalization_rule_copy_cannot_change_the_registered_rule() -> None:
    engine, rule = _normalization_stack()
    impostor = rule.model_copy(update={"methodology_ref": "fake@1", "denominator_ref": "obs:evil"})
    # the engine evaluates the REGISTERED rule, so the impostor changes nothing
    assert engine.normalize(_product(5.0), impostor) is not None
    assert engine.registry.normalized_rule("normrule:1").methodology_ref == "book6-normalization@1"


def test_r1_c3_valuation_conversion_methodology_replaced() -> None:
    engine, *_ = _valuation_engine(PRICE_CLAIM)
    good = valuation("val:1", price_observation=price("price:1", claim_refs=(PRICE_CLAIM,)))
    assert engine.authorize_current_valuation(good, as_of=NOW)
    forged = good.model_copy(update={"conversion_methodology_ref": "fake@1"})
    with pytest.raises(ValuationError, match="resolves to nothing"):
        engine.authorize_current_valuation(forged, as_of=NOW)


def test_r1_c4_price_claim_refs_stripped() -> None:
    engine, *_ = _valuation_engine(PRICE_CLAIM)
    good = valuation("val:1", price_observation=price("price:1", claim_refs=(PRICE_CLAIM,)))
    forged = good.model_copy(
        update={"price": good.price.model_copy(update={"source_claim_refs": ()})}
    )
    with pytest.raises((ValuationError, ValidationError, Book6ProvenanceError)):
        engine.authorize_current_valuation(forged, as_of=NOW)


def test_r1_c5_price_source_swapped() -> None:
    """Swapping the attribution string alone changes nothing."""

    engine, *_ = _valuation_engine(PRICE_CLAIM)
    good = valuation("val:1", price_observation=price("price:1", claim_refs=(PRICE_CLAIM,)))
    swapped = good.model_copy(
        update={"price": good.price.model_copy(update={"source_ref": "fake:oracle"})}
    )
    # still authorized: authority came from the Book 2 claim all along, and the
    # price class remains admissible for the purpose
    assert engine.authorize_current_valuation(swapped, as_of=NOW) is swapped
    forged_claim = swapped.model_copy(
        update={"price": swapped.price.model_copy(update={"source_claim_refs": ("nope:1",)})}
    )
    with pytest.raises(ValuationError, match="no current Book 2 authority"):
        engine.authorize_current_valuation(forged_claim, as_of=NOW)


def test_r1_c6_price_class_swapped() -> None:
    engine, *_ = _valuation_engine(PRICE_CLAIM)
    good = valuation("val:1", price_observation=price("price:1", claim_refs=(PRICE_CLAIM,)))
    forged = good.model_copy(
        update={
            "price": good.price.model_copy(
                update={"price_class": PriceObservationClass.OFFICIAL_REDEMPTION_VALUE}
            )
        }
    )
    with pytest.raises(ValuationError, match="not admissible"):
        engine.authorize_current_valuation(forged, as_of=NOW)


def test_r1_c7_staleness_bound_forged_downward_is_caught_at_the_boundary() -> None:
    """A bound tightened after the fact must be re-read at USE, not trusted."""

    engine, *_ = _valuation_engine(PRICE_CLAIM)
    fresh = valuation(
        "val:1",
        price_observation=price("price:1", claim_refs=(PRICE_CLAIM,), observed_at=NOW),
        observed_at=NOW,
        staleness_bound_seconds=10**9,
    )
    assert engine.authorize_current_valuation(fresh, as_of=NOW + timedelta(days=30)) is fresh
    forged = fresh.model_copy(update={"staleness_bound_seconds": 1})
    with pytest.raises(ValuationError, match="stale"):
        engine.authorize_current_valuation(forged, as_of=NOW + timedelta(days=30))


def test_r1_c8_vector_coverage_rule_refs_replaced_by_fake_refs() -> None:
    engine = build_engine_with_definitions(definition(METRIC))
    register_measurement(
        engine,
        windowed_observation(
            "obs:1", METRIC, value=7.0, missingness=MissingnessState.OBSERVED, claim_refs=(CLAIM_ID,)
        ),
    )
    engine.registry.register_coverage(coverage("obs:1", 1.0))
    engine.registry.coverage_rules.register(coverage_rule("covrule:1", scope_metric_id=METRIC))
    engine.registry.coverage_rules.ratify("covrule:1", operator="synthetic", at=T1)
    vector = engine.build_availability_vector(
        subject_ref="fixture:chain:alpha",
        schema_ref="schema:book6:1",
        as_of_valid_time=T1,
        observed_at=T1,
        measurement_ids=("obs:1",),
        methodology_ref="book6-methodology@1",
    )
    assert engine.data_status(vector) is VectorStatus.DATA_COMPLETE
    assert vector.coverage_sufficiency_rule_refs == ("covrule:1",)
    forged = vector.model_copy(update={"coverage_sufficiency_rule_refs": ("fake:rule",)})
    assert engine.data_status(forged) is VectorStatus.DATA_INCOMPLETE
    # R2-D3 supersedes the R1-D4 mechanism here, deliberately and narrowly:
    # the attestation is now an AUDIT RECORD, not the source of truth, so
    # stripping it cannot flip the authoritative verdict. The engine
    # reconstructs sufficiency from registry state by per-metric set
    # equality, and the forged / overstated / reduced / unrelated-rule
    # attacks this None-attestation assertion used to stand in for are now
    # executed for real against the registry in test_book6_hardening_r2.py.
    stripped = vector.model_copy(update={"sufficiency_attestation": None})
    assert engine.data_status(stripped) is VectorStatus.DATA_COMPLETE
    # The preserved R1 gate itself: fake rule refs still fail closed.
    assert engine.data_status(forged) is VectorStatus.DATA_INCOMPLETE


def test_r1_c9_coverage_rule_status_forged_to_ratified() -> None:
    """C9: ``model_copy(status="RATIFIED")`` grants nothing."""

    unratified = coverage_rule("covrule:1", scope_metric_id=METRIC)
    forged = unratified.model_copy(update={"status": CoverageRuleRatificationStatus.RATIFIED})
    assert forged.status is CoverageRuleRatificationStatus.RATIFIED
    registry = CoverageRuleRegistry()
    with pytest.raises(CoverageRuleError, match="may only be registered UNRATIFIED"):
        registry.register(forged)
    registry.register(unratified)
    assert registry.ratified_count() == 0
    with pytest.raises(CoverageRuleError, match="not ratified"):
        registry.authorize(metric_id=METRIC, rule_ref="covrule:1")


def test_r1_c10_coverage_rule_scope_swapped() -> None:
    registry = CoverageRuleRegistry()
    registry.register(coverage_rule("covrule:1", scope_metric_id=METRIC))
    registry.ratify("covrule:1", operator="synthetic", at=NOW)
    assert registry.is_sufficient(metric_id=METRIC, rule_ref="covrule:1") is True
    registry._rules["covrule:1"] = registry.registered_rule("covrule:1").model_copy(
        update={"scope_metric_id": "metric.elsewhere"}
    )
    assert registry.is_sufficient(metric_id=METRIC, rule_ref="covrule:1") is False


# ===========================================================================
# Phase 13 — rule status forgery
# ===========================================================================


def test_r1_d7_a_state_rule_may_not_be_constructed_ratified() -> None:
    with pytest.raises(ValidationError, match="may not declare itself RATIFIED"):
        StateRule(
            state_rule_id="sr:1",
            target_state=StateName.INCREASING,
            state_class=StateClass.B_SPECIFICATION_ONLY,
            predicate_ref="p",
            methodology_ref="book6-methodology@1",
            version="1",
            status=RuleRatificationStatus.RATIFIED,
            ratified_by="operator",
            ratified_at=NOW,
        )


def test_r1_d7_a_forged_ratified_rule_cannot_be_registered() -> None:
    unratified = _unratified_state_rule()
    forged = unratified.model_copy(
        update={
            "status": RuleRatificationStatus.RATIFIED,
            "ratified_by": "operator",
            "ratified_at": NOW,
        }
    )
    registry = StateRuleRegistry()
    with pytest.raises(Exception, match="may only be registered UNRATIFIED"):
        registry.register(forged)
    assert registry.ratified_count() == 0
    # refused at the door, so it is absent rather than unratified
    with pytest.raises(Exception, match="is not registered"):
        registry.authorize(StateName.INCREASING, rule_ref="sr:1")

    # and the legitimate path: register UNRATIFIED, then ratify through the
    # registry. Only then does the state become emittable.
    registry.register(unratified)
    with pytest.raises(Exception, match="no registry ratification decision"):
        registry.authorize(StateName.INCREASING, rule_ref="sr:1")
    registry.ratify("sr:1", operator="operator", at=NOW)
    assert registry.authorize(StateName.INCREASING, rule_ref="sr:1").state_rule_id == "sr:1"


def _unratified_state_rule() -> StateRule:
    return StateRule(
        state_rule_id="sr:1",
        target_state=StateName.INCREASING,
        state_class=StateClass.B_SPECIFICATION_ONLY,
        predicate_ref="predicate:monotone@1",
        methodology_ref="book6-methodology@1",
        version="1",
    )


def test_r1_d7_ratification_authority_lives_in_the_registry_ledger() -> None:
    registry = StateRuleRegistry()
    registry.register(_unratified_state_rule())
    ratified = registry.ratify("sr:1", operator="operator", at=NOW)
    assert ratified.status is RuleRatificationStatus.UNRATIFIED  # the object never claims it
    decision = registry.ratification_of("sr:1")
    assert decision is not None and decision.operator == "operator"
    assert registry.authorize(StateName.INCREASING, rule_ref="sr:1").state_rule_id == "sr:1"


def test_r1_d7_ratification_constants() -> None:
    assert RULE_OBJECT_STATUS_IS_NOT_AUTHORITY is True
    assert OBJECT_STATUS_IS_NOT_AUTHORITY is True
    assert NO_DELEGATED_RATIFICATION_AUTHORITY is True


def test_r1_d7_the_ledger_binds_authority_to_one_version() -> None:
    ledger = RatificationLedger("csia:test")
    ledger.record("r", version="1", operator="op", at=NOW)
    assert ledger.has("r", version="1") is True
    assert ledger.has("r", version="2") is False
    with pytest.raises(RatificationError, match="does not inherit"):
        ledger.decision("r", version="2")
    with pytest.raises(RatificationError, match="already ratified"):
        ledger.record("r", version="1", operator="op", at=NOW)
    with pytest.raises(RatificationError, match="never anonymous"):
        ledger.record("r2", version="1", operator="", at=NOW)
    with pytest.raises(RatificationError, match="no registry ratification decision"):
        ledger.decision("never:ratifed", version="1")
    ledger.revoke("r")
    assert ledger.ratified_count() == 0


def test_r1_d7_there_is_no_bulk_or_delegated_ratification_path() -> None:
    for registry in (StateRuleRegistry(), CoverageRuleRegistry()):
        surface = {
            name
            for name in dir(registry)
            if not name.startswith("_")
            and callable(getattr(registry, name))
            and any(
                token in name.lower()
                for token in ("delegate", "auto", "bulk", "cascade", "ratify_all", "assume")
            )
        }
        assert surface == set(), type(registry).__name__


# ===========================================================================
# Phase 15 — pre-existing seals are not regressed by R1
# ===========================================================================


def test_r1_missing_is_still_not_zero() -> None:
    from crypto_systems_intelligence_atlas.book6_grammar import VALUE_FORBIDDEN_MISSINGNESS

    for state in VALUE_FORBIDDEN_MISSINGNESS:
        with pytest.raises(ValidationError):
            windowed_observation(
                "obs:x",
                METRIC,
                value=0.0,
                missingness=state,
                claim_refs=(CLAIM_ID,),
            )


def test_r1_denominator_still_fails_closed_to_undefined() -> None:
    from crypto_systems_intelligence_atlas.book6_definitions import DenominatorRule
    from crypto_systems_intelligence_atlas.book6_grammar import MeasurementCategory
    from crypto_systems_intelligence_atlas.book6_records import DenominatorRef

    ratio_metric = "metric.ratio.throughput"
    engine = build_engine_with_definitions(
        definition(
            ratio_metric,
            category=MeasurementCategory.RATIO,
            unit="ratio",
            denominator_rule=DenominatorRule.OBSERVED_MEASUREMENT,
        )
    )
    register_measurement(
        engine,
        windowed_observation(
            "obs:ratio",
            ratio_metric,
            value=10.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM_ID,),
            unit="ratio",
            category=MeasurementCategory.RATIO,
            denominator=DenominatorRef(
                denominator_measurement_id="obs:den",
                denominator_identity="den:zero",
                state="ZERO",
                value=0.0,
            ),
        ),
    )
    result = engine.compute_ratio("obs:ratio")
    assert result.is_undefined is True and result.ratio is None


def test_r1_percentile_is_still_not_a_normalization_type() -> None:
    assert "PERCENTILE_WITHIN_COHORT" not in {t.value for t in NormalizationType}
    assert not [t for t in NormalizationType if "PERCENTILE" in t.value or "RANK" in t.value]


def test_r1_fifteen_row_corpus_is_intact() -> None:
    assert len(FALSE_COMPARISON_CORPUS) == 15


def test_r1_no_global_price_source_constant() -> None:
    assert NO_GLOBAL_PRICE_SOURCE_CLASS is True


def test_r1_methodology_is_a_complete_typed_object() -> None:
    m: MeasurementMethodology = methodology()
    assert m.identity == "book6-methodology@1"
    assert m.input_methodology_refs == ()
    assert m.authorized_corpus_row_ids == ()
    assert m.authorizes_row("FC-05") is False
