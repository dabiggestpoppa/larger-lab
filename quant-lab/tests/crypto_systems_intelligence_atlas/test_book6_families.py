"""Book 6 metric families — schema capability for the ratified 6A families.

Book 6 implements the DEFINITION surface for the five ratified families and no
collector, no acquisition path and no default metric. Each family is a slot for
fully specified definitions, and a subject outside a metric's declared
architecture applicability is ``NOT_SUPPORTED`` — never zero (Axiom 1; plan
v0.2 §28).
"""

from __future__ import annotations

import pytest

from crypto_systems_intelligence_atlas.book6_definitions import (
    METRIC_FAMILY_BY_SUBJECT_DOMAIN,
    NOT_SUPPORTED_IS_NOT_ZERO,
    NO_DEFAULT_METRIC_EXISTS,
    RATIFIED_METRIC_FAMILIES,
    SourceFamily,
)
from crypto_systems_intelligence_atlas.book6_grammar import (
    ArchitectureFamily,
    MeasurementRole,
    SubjectDomain,
)
from crypto_systems_intelligence_atlas.book6_records import MeasurementRecordError
from crypto_systems_intelligence_atlas.book6_states import StateName
from crypto_systems_intelligence_atlas.book6_support import (
    T1,
    build_engine,
    definition,
    windowed_observation,
)
from crypto_systems_intelligence_atlas.book6_grammar import MissingnessState

CLAIM = "fixture:claim:measurement"

#: One synthetic definition per ratified family, with the source families each
#: family is permitted to draw on.
FAMILY_FIXTURES: tuple[tuple[str, SubjectDomain, SourceFamily], ...] = (
    ("metric.family.chain.tx", SubjectDomain.CHAIN, SourceFamily.NATIVE_CHAIN),
    ("metric.family.protocol.volume", SubjectDomain.PROTOCOL, SourceFamily.OFFICIAL_PROTOCOL),
    ("metric.family.token.supply", SubjectDomain.TOKEN, SourceFamily.NATIVE_CHAIN),
    (
        "metric.family.capital.staked",
        SubjectDomain.CAPITAL,
        SourceFamily.BOOK5_CAPITAL_RECORD,
    ),
    (
        "metric.family.developer.contributors",
        SubjectDomain.DEVELOPER,
        SourceFamily.OFFCHAIN_REPOSITORY,
    ),
)


def _engine():
    engine, *_ = build_engine()
    for metric_id, domain, family in FAMILY_FIXTURES:
        engine.registry.register_definition(
            definition(metric_id, subject_domain=domain, source_families=(family,))
        )
    return engine


# -- the five ratified families exist as schema, not as collectors ------------


def test_the_five_ratified_families_are_present() -> None:
    assert RATIFIED_METRIC_FAMILIES == ("6A.1", "6A.2", "6A.3", "6A.4", "6A.5")


def test_every_subject_domain_maps_to_exactly_one_family() -> None:
    assert set(METRIC_FAMILY_BY_SUBJECT_DOMAIN) == set(SubjectDomain)
    assert len(METRIC_FAMILY_BY_SUBJECT_DOMAIN) == 5


@pytest.mark.parametrize(
    ("metric_id", "domain", "family"), FAMILY_FIXTURES, ids=[f[0] for f in FAMILY_FIXTURES]
)
def test_each_family_accepts_a_fully_specified_definition(
    metric_id: str, domain: SubjectDomain, family: SourceFamily
) -> None:
    engine = _engine()
    registered = engine.registry.definition(metric_id)
    assert registered.subject_domain is domain
    assert family in registered.allowed_source_families
    assert registered.methodology.identity == "book6-methodology@1"
    assert registered.comparability_class is not None
    assert registered.applies_to_architectures == ()


def test_no_default_metric_is_shipped() -> None:
    """A family is a slot, not a reason to invent a metric."""

    engine = build_engine()[0]
    assert engine.registry.registered_refs() == ()
    with pytest.raises(Exception):
        engine.registry.definition("active_addresses")


def test_no_default_metric_constant_is_true() -> None:
    assert NO_DEFAULT_METRIC_EXISTS is True


def test_the_registry_ships_no_pre_registered_definitions() -> None:
    """Every definition must be registered explicitly by a caller."""

    engine = build_engine()[0]
    for metric_id, _, _ in FAMILY_FIXTURES:
        with pytest.raises(Exception, match="is not registered"):
            engine.registry.definition(metric_id)


# -- architecture applicability is explicit (Phase 28) -----------------------


def test_architecture_agnostic_definitions_apply_everywhere() -> None:
    engine = _engine()
    registered = engine.registry.definition("metric.family.chain.tx")
    for family in ArchitectureFamily:
        assert registered.applies_to(family.value) is True


def test_a_scoped_definition_is_not_supported_outside_its_architectures() -> None:
    engine, *_ = build_engine()
    engine.registry.register_definition(
        definition("metric.family.chain.pos_validators", applies_to=("POS",))
    )
    registered = engine.registry.definition("metric.family.chain.pos_validators")
    assert registered.applies_to("POS") is True
    assert registered.applies_to(ArchitectureFamily.UTXO.value) is False
    assert registered.applies_to(ArchitectureFamily.MODULAR_ROLLUP.value) is False


def test_not_supported_is_not_zero() -> None:
    """A metric that does not exist natively for a subject is absent, not 0."""

    engine, *_ = build_engine()
    engine.registry.register_definition(
        definition("metric.family.chain.pos_validators", applies_to=("POS",))
    )
    with pytest.raises(MeasurementRecordError, match="NOT_SUPPORTED"):
        engine.registry.register_measurement(
            windowed_observation(
                "obs:wrong",
                "metric.family.chain.pos_validators",
                value=0.0,
                missingness=MissingnessState.ZERO_OBSERVED,
                claim_refs=(CLAIM,),
                architecture_family=ArchitectureFamily.UTXO.value,
            )
        )
    assert NOT_SUPPORTED_IS_NOT_ZERO is True


def test_a_scoped_definition_requires_a_declared_architecture_family() -> None:
    engine, *_ = build_engine()
    engine.registry.register_definition(
        definition("metric.family.chain.pos_validators", applies_to=("POS",))
    )
    with pytest.raises(MeasurementRecordError, match="declares no architecture family"):
        engine.registry.register_measurement(
            windowed_observation(
                "obs:blank",
                "metric.family.chain.pos_validators",
                value=1.0,
                missingness=MissingnessState.OBSERVED,
                claim_refs=(CLAIM,),
                architecture_family=None,
            )
        )


def test_an_out_of_family_measurement_resolves_to_not_applicable() -> None:
    engine, *_ = build_engine()
    engine.registry.register_definition(
        definition("metric.family.chain.pos_validators", applies_to=("POS",))
    )
    engine.registry.register_measurement(
        windowed_observation(
            "obs:pos",
            "metric.family.chain.pos_validators",
            value=3.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
            architecture_family="POS",
        )
    )
    assert engine.availability_state("obs:pos") is StateName.RULE_NOT_RATIFIED


def test_measurement_roles_remain_distinct_across_families() -> None:
    engine = _engine()
    assert engine.registry.definition("metric.family.chain.tx").role is MeasurementRole.NATIVE
    engine.registry.register_definition(
        definition(
            "metric.family.protocol.fees_per_user",
            subject_domain=SubjectDomain.PROTOCOL,
            role=MeasurementRole.NORMALIZED,
        )
    )
    assert (
        engine.registry.definition("metric.family.protocol.fees_per_user").role
        is MeasurementRole.NORMALIZED
    )


def test_every_family_fixture_declares_its_window_and_valid_time() -> None:
    engine = _engine()
    engine.registry.register_measurement(
        windowed_observation(
            "obs:chain",
            "metric.family.chain.tx",
            value=100.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
        )
    )
    observation = engine.registry.registered_measurement("obs:chain")
    assert observation.valid_time == T1
    assert observation.observed_at == T1
    assert observation.window_class.value == "INSTANTANEOUS"
    assert observation.methodology_identity == "book6-methodology@1"
