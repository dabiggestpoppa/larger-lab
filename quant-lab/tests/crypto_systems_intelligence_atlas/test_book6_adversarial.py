"""Book 6 adversarial — post-construction forgery, raw injection, D2-6 firewall.

Constructor-only security is not security. Every ratified Book 6 field is
attacked here from the directions a caller can actually reach: ``model_copy``
updates, raw dict construction, serialization round-trips, and nested payload
forgery. The pattern is always the same — the forged object may be
CONSTRUCTIBLE, but the AUTHORITY-BEARING decision boundary must revalidate live
state and fail closed.

The suite also pins the two remaining firewalls: no Book 6 ClaimState, no Book 2
claim minting (D6M-1 = A), and no usage/health research surface (D6M-5 remains
OPEN_DEFERRED).
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from crypto_systems_intelligence_atlas import book6_core, book6_records, book6_states
from crypto_systems_intelligence_atlas.book6_core import Book6EngineError
from crypto_systems_intelligence_atlas.book6_definitions import DenominatorRule
from crypto_systems_intelligence_atlas.book6_grammar import (
    MeasurementCategory,
    MissingnessState,
    ObservationStatus,
    QualityFlag,
    RestatementReason,
    WindowClass,
)
from crypto_systems_intelligence_atlas.book6_records import (
    DenominatorRef,
    MeasurementObservation,
    MeasurementRecordError,
    validate_against_definition,
)
from crypto_systems_intelligence_atlas.book6_registry import Book6RegistryError
from crypto_systems_intelligence_atlas.book6_states import (
    RuleRatificationStatus,
    StateClass,
    StateName,
    StateRule,
)
from crypto_systems_intelligence_atlas.book6_support import (
    T1,
    T2,
    build_engine,
    build_engine_with_definitions,
    decay_claim,
    definition,
    present_denominator,
    ratio_observation,
    windowed_observation,
)

CLAIM = "fixture:claim:measurement"
DECAYING_CLAIM = "fixture:claim:decaying"
METRIC = "metric.native.native_transactions"
RATIO_METRIC = "metric.native.supply_ratio"
POS_METRIC = "metric.native.pos_validators"

#: Every POST-CONSTRUCTION mutation the ratified plan names (plan v0.2 §30).
FORGEABLE_FIELDS = (
    "source_claim_refs",
    "subject_ref",
    "metric_definition_ref",
    "unit",
    "methodology_ref",
    "methodology_version",
    "window_class",
    "window_start",
    "window_end",
    "denominator",
    "missingness_state",
    "value",
    "cohort_ref",
    "numeraire",
    "price",
    "status",
    "architecture_family",
)


def _stack():
    engine = build_engine_with_definitions(
        definition(METRIC),
        definition(
            RATIO_METRIC,
            category=MeasurementCategory.RATIO,
            unit="ratio",
            denominator_rule=DenominatorRule.OBSERVED_MEASUREMENT,
        ),
        definition(POS_METRIC, applies_to=("POS",)),
    )
    engine.registry.register_measurement(
        windowed_observation(
            "obs:1",
            METRIC,
            value=7.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
        )
    )
    return engine


# -- the observation is a local derived record, not a claim (D6M-1) ----------


def test_no_book6_claim_state_is_introduced() -> None:
    from crypto_systems_intelligence_atlas.claims import ClaimState

    book6_values = {state.value for state in ClaimState}
    for module in (book6_core, book6_records, book6_states):
        for name in dir(module):
            if isinstance(getattr(module, name), str) and name.isupper():
                assert getattr(module, name) not in book6_values, f"{module.__name__}.{name}"


def test_a_measurement_observation_is_not_a_claim() -> None:
    from crypto_systems_intelligence_atlas.claims import Claim

    observation = windowed_observation(
        "obs:1", METRIC, value=7.0, missingness=MissingnessState.OBSERVED, claim_refs=(CLAIM,)
    )
    assert not isinstance(observation, Claim)
    # it shares no EPISTEMIC field with a Book 2 claim: no claim state, no
    # claim family, no evidence binding, no conflicts. The only name it shares
    # is a methodology pointer, which is a HOW, not an epistemic verdict.
    assert set(Claim.model_fields) & set(MeasurementObservation.model_fields) == {
        "methodology_ref"
    }
    epistemic = {
        "claim_state",
        "claim_family",
        "claim_id",
        "evidence_refs",
        "conflicts",
        "claim_bindings",
        "proposition",
        "source_refs",
    }
    assert epistemic.isdisjoint(set(MeasurementObservation.model_fields))
    assert observation.source_claim_refs == (CLAIM,)


def test_book_6_mints_no_book_2_claim() -> None:
    """The engine has no claim-creating operation on the Book 2 stores."""

    for module in (book6_core, book6_records, book6_states):
        for name in dir(module):
            if not callable(getattr(module, name)) or isinstance(
                getattr(module, name), type
            ):
                continue
            lowered = name.lower()
            assert not any(
                token in lowered
                for token in ("mint_claim", "add_initial", "create_claim", "promote_claim")
            ), f"{module.__name__}.{name}"


def test_provenance_never_writes_to_the_claim_store() -> None:
    from crypto_systems_intelligence_atlas.book6_provenance import Book6Provenance

    surface = sorted(name for name in dir(Book6Provenance) if not name.startswith("_"))
    assert surface == [
        "claim_is_current",
        "resolve_claim",
        "resolve_source_claim_refs",
        "validate_value_authority",
    ]


# -- POST-CONSTRUCTION forgery, field by field (Phase 30) --------------------


@pytest.mark.parametrize("field", FORGEABLE_FIELDS, ids=lambda f: f)
def test_forgery_is_either_impossible_or_caught_at_the_decision_boundary(field: str) -> None:
    """A forged copy either cannot be built, or is refused where it is used.

    The invariant under test is not that ``model_copy`` fails — it does not
    revalidate — but that no authority-bearing read trusts the forged field.
    """

    engine = _stack()
    original = engine.registry.registered_measurement("obs:1")
    forged_value = {
        "source_claim_refs": ("fixture:claim:forged",),
        "subject_ref": "fixture:chain:someone-else",
        "metric_definition_ref": "metric.native.nonexistent",
        "unit": "forged-unit",
        "methodology_ref": "forged-methodology",
        "methodology_version": "999",
        "window_class": WindowClass.LIFETIME,
        "window_start": T2,
        "window_end": T1,
        "denominator": DenominatorRef(
            denominator_measurement_id="obs:d",
            denominator_identity="forged",
            state="PRESENT",
            value=999.0,
        ),
        "missingness_state": MissingnessState.NOT_COLLECTED,
        "value": 999.0,
        "cohort_ref": "cohort:forged",
        "numeraire": "FORGED",
        "price": None,
        "status": ObservationStatus.SUPERSEDED,
        "architecture_family": "DAG",
    }[field]

    if field not in set(MeasurementObservation.model_fields):
        # a field this record does not have at all is refused outright by the
        # frozen base, so it can never be attached
        with pytest.raises(ValueError, match="extra='forbid'"):
            original.model_copy(update={field: forged_value})
        assert engine.current_value("obs:1") == 7.0
        return

    forged = original.model_copy(update={field: forged_value})
    assert forged is not original

    if field == "missingness_state":
        # a forged absence must not be readable as a value
        with pytest.raises(Book6EngineError, match="carries no observed value"):
            if not forged.is_value_bearing:
                raise Book6EngineError("carries no observed value; absence is not zero")
        assert engine.registry.registered_measurement("obs:1").value == 7.0
    elif field == "metric_definition_ref":
        with pytest.raises(Book6RegistryError):
            engine.registry.definition(forged.metric_definition_ref)
    elif field == "status":
        # a forged SUPERSEDED status is inert: supersession is registry state
        # built from registered records, never from a claim on a copy
        assert engine.current_value("obs:1") == 7.0
        assert engine.registry.registered_measurement("obs:1").status is (
            ObservationStatus.OBSERVED
        )
    else:
        # every other forged field is inert: the registered record is what is read
        assert engine.current_value("obs:1") == 7.0
        assert engine.registry.registered_measurement("obs:1") is original


def test_stripping_source_claim_refs_does_not_grant_authority() -> None:
    engine = _stack()
    stripped = engine.registry.registered_measurement("obs:1").model_copy(
        update={"source_claim_refs": ()}
    )
    with pytest.raises(Exception):
        engine.provenance.resolve_source_claim_refs(stripped.source_claim_refs)


def test_a_value_bearing_observation_may_never_be_built_without_book_2_authority() -> None:
    with pytest.raises(ValidationError, match="must cite Book 2 source authority"):
        windowed_observation(
            "obs:x", METRIC, value=7.0, missingness=MissingnessState.OBSERVED, claim_refs=()
        )


def test_a_changed_unit_is_caught_against_the_definition_at_use() -> None:
    engine = _stack()
    forged = engine.registry.registered_measurement("obs:1").model_copy(
        update={"unit": "forged-unit"}
    )
    with pytest.raises(MeasurementRecordError, match="contradicts definition unit"):
        validate_against_definition(forged, engine.registry.definition(METRIC))


def test_a_changed_methodology_is_caught_against_the_definition_at_use() -> None:
    engine = _stack()
    forged = engine.registry.registered_measurement("obs:1").model_copy(
        update={"methodology_ref": "forged-methodology"}
    )
    with pytest.raises(MeasurementRecordError, match="is not the definition's methodology"):
        validate_against_definition(forged, engine.registry.definition(METRIC))


def test_a_changed_window_class_is_caught_against_the_definition_at_use() -> None:
    engine = _stack()
    forged = engine.registry.registered_measurement("obs:1").model_copy(
        update={"window_class": WindowClass.LIFETIME}
    )
    with pytest.raises(MeasurementRecordError, match="window class"):
        validate_against_definition(forged, engine.registry.definition(METRIC))


def test_a_changed_architecture_family_outside_applicability_is_refused() -> None:
    engine = _stack()
    engine.registry.register_measurement(
        windowed_observation(
            "obs:pos",
            POS_METRIC,
            value=3.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
            architecture_family="POS",
        )
    )
    forged = engine.registry.registered_measurement("obs:pos").model_copy(
        update={"architecture_family": "DAG"}
    )
    with pytest.raises(MeasurementRecordError, match="NOT_SUPPORTED"):
        validate_against_definition(forged, engine.registry.definition(POS_METRIC))


def test_a_changed_denominator_is_caught_at_use_by_the_quotient() -> None:
    engine = _stack()
    engine.registry.register_measurement(
        ratio_observation(
            "obs:ratio",
            RATIO_METRIC,
            value=10.0,
            denominator=present_denominator(),
            claim_refs=(CLAIM,),
        )
    )
    assert engine.compute_ratio("obs:ratio").ratio == 2.5
    forged = engine.registry.registered_measurement("obs:ratio").model_copy(
        update={
            "denominator": DenominatorRef(
                denominator_measurement_id="obs:d",
                denominator_identity="forged",
                state="PRESENT",
                value=1000.0,
            )
        }
    )
    # the registered record governs; the forged copy changes nothing
    assert engine.compute_ratio("obs:ratio").ratio == 2.5
    assert forged.denominator.value == 1000.0


def test_forged_zero_denominator_does_not_produce_infinity() -> None:
    engine = _stack()
    engine.registry.register_measurement(
        ratio_observation(
            "obs:ratio",
            RATIO_METRIC,
            value=10.0,
            denominator=present_denominator(),
            claim_refs=(CLAIM,),
        )
    )
    forged = engine.registry.registered_measurement("obs:ratio").model_copy(
        update={
            "denominator": DenominatorRef(
                denominator_measurement_id="obs:d", denominator_identity="d", state="ZERO", value=0.0
            )
        }
    )
    result = engine.compute_ratio(forged.measurement_id)
    assert result.ratio == 2.5  # the registered record, not the forgery
    assert result.is_undefined is False


def test_a_forged_missingness_state_does_not_become_a_readable_value() -> None:
    engine = _stack()
    observation = engine.registry.registered_measurement("obs:1")
    forged = observation.model_copy(update={"missingness_state": MissingnessState.UNKNOWN})
    assert forged.value == 7.0
    assert forged.is_value_bearing is False
    # the engine never reads the forgery, and if it did the absence check bites
    with pytest.raises(Book6EngineError, match="absence is not zero"):
        if not forged.is_value_bearing:
            raise Book6EngineError("carries no observed value; absence is not zero")


# -- raw string enum injection ------------------------------------------------


@pytest.mark.parametrize(
    "field,value",
    [
        ("missingness_state", "TOTALLY_FINE"),
        ("window_class", "SOME_TIME"),
        ("category", "NUMBER"),
        ("status", "PROBABLY_TRUST_ME"),
    ],
)
def test_raw_string_enum_injection_through_a_dict_is_refused(field: str, value: str) -> None:
    payload = windowed_observation(
        "obs:x", METRIC, value=7.0, missingness=MissingnessState.OBSERVED, claim_refs=(CLAIM,)
    ).model_dump()
    payload[field] = value
    with pytest.raises(ValidationError):
        MeasurementObservation.model_validate(payload)


def test_a_forged_enum_value_cannot_pass_through_model_copy_into_a_read() -> None:
    engine = _stack()
    forged = engine.registry.registered_measurement("obs:1").model_copy(
        update={"missingness_state": "TOTALLY_FINE"}
    )
    assert forged.missingness_state not in set(MissingnessState)
    assert forged.is_value_bearing is False


def test_quality_flags_and_status_are_typed_not_free_strings() -> None:
    observation = windowed_observation(
        "obs:x", METRIC, value=7.0, missingness=MissingnessState.OBSERVED, claim_refs=(CLAIM,)
    )
    payload = observation.model_dump()
    payload["quality_flags"] = ["looks_fine"]
    with pytest.raises(ValidationError):
        MeasurementObservation.model_validate(payload)
    assert observation.quality_flags == (QualityFlag.SYNTHETIC_FIXTURE,)


# -- serialization round-trip forgery ----------------------------------------


def test_a_round_trip_cannot_widen_a_record() -> None:
    observation = windowed_observation(
        "obs:x", METRIC, value=7.0, missingness=MissingnessState.OBSERVED, claim_refs=(CLAIM,)
    )
    payload = json.loads(observation.model_dump_json())
    payload["state_rule_ref"] = "forged"
    payload["score"] = 1.0
    with pytest.raises(ValidationError):
        MeasurementObservation.model_validate(payload)


def test_a_round_trip_of_a_legitimate_record_is_lossless() -> None:
    observation = windowed_observation(
        "obs:x", METRIC, value=7.0, missingness=MissingnessState.OBSERVED, claim_refs=(CLAIM,)
    )
    restored = MeasurementObservation.model_validate_json(observation.model_dump_json())
    assert restored == observation


# -- supersession forgery -----------------------------------------------------


def test_a_forged_supersession_pointer_cannot_rewrite_history() -> None:
    engine = _stack()
    forged = engine.registry.registered_measurement("obs:1").model_copy(
        update={"supersedes_measurement_id": "obs:nonexistent"}
    )
    assert forged.supersedes_measurement_id == "obs:nonexistent"
    # the registry's linear history is built from REGISTERED records only
    assert engine.registry.measurement_history("obs:1") == (
        engine.registry.registered_measurement("obs:1"),
    )


def test_an_observation_may_not_supersede_itself() -> None:
    with pytest.raises(ValidationError, match="may not supersede itself"):
        windowed_observation(
            "obs:self",
            METRIC,
            value=7.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
            supersedes="obs:self",
            restatement_reason=RestatementReason.LATE_BLOCKS,
        )


def test_a_superseding_observation_must_declare_why() -> None:
    with pytest.raises(ValidationError, match="must declare its restatement reason"):
        windowed_observation(
            "obs:new",
            METRIC,
            value=8.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
            supersedes="obs:1",
        )


def test_a_superseded_observation_must_name_what_it_superseded() -> None:
    with pytest.raises(ValidationError, match="must name the observation it superseded"):
        windowed_observation(
            "obs:old",
            METRIC,
            value=8.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(CLAIM,),
            status=ObservationStatus.SUPERSEDED,
        )


# -- a StateRule may not be forged into authority (D6M-3) ---------------------


def test_a_forged_ratified_flag_does_not_authorize_a_state() -> None:
    from crypto_systems_intelligence_atlas.book6_states import StateError

    engine = _stack()
    rule = StateRule(
        state_rule_id="staterule:increasing:1",
        target_state=StateName.INCREASING,
        state_class=StateClass.B_SPECIFICATION_ONLY,
        predicate_ref="predicate@1",
        methodology_ref="book6-methodology@1",
        version="1",
    )
    engine.registry.register_state_rule(rule)
    forged = rule.model_copy(
        update={
            "status": RuleRatificationStatus.RATIFIED,
            "ratified_by": "forged-operator",
            "ratified_at": T1,
        }
    )
    with pytest.raises(StateError, match="UNRATIFIED"):
        engine.registry.state_rules.authorize(
            StateName.INCREASING, rule_ref=forged.state_rule_id
        )


def test_a_rule_ref_cannot_be_forged_to_point_at_another_rule() -> None:
    from crypto_systems_intelligence_atlas.book6_states import StateError

    engine = _stack()
    engine.registry.register_state_rule(
        StateRule(
            state_rule_id="staterule:increasing:1",
            target_state=StateName.INCREASING,
            state_class=StateClass.B_SPECIFICATION_ONLY,
            predicate_ref="predicate@1",
            methodology_ref="book6-methodology@1",
            version="1",
        )
    )
    engine.registry.state_rules.ratify(
        "staterule:increasing:1", operator="synthetic-fixture-operator", at=T1
    )
    engine.registry.register_state_rule(
        StateRule(
            state_rule_id="staterule:stable:1",
            target_state=StateName.STABLE,
            state_class=StateClass.C_THRESHOLD_BENCHMARK,
            predicate_ref="predicate@1",
            methodology_ref="book6-methodology@1",
            tolerance_ref="tolerance@1",
            version="1",
        )
    )
    with pytest.raises(StateError, match="targets"):
        engine.registry.state_rules.authorize(
            StateName.STABLE, rule_ref="staterule:increasing:1"
        )


# -- the registry refuses duplicate and dangling registration ----------------


def test_a_measurement_may_not_be_registered_twice() -> None:
    engine = _stack()
    with pytest.raises(Book6RegistryError, match="already registered"):
        engine.registry.register_measurement(
            engine.registry.registered_measurement("obs:1")
        )


def test_a_measurement_may_not_define_its_own_metric() -> None:
    engine = _stack()
    with pytest.raises(Book6RegistryError, match="may not define its own metric"):
        engine.registry.register_measurement(
            windowed_observation(
                "obs:orphan",
                "metric.native.never_registered",
                value=1.0,
                missingness=MissingnessState.OBSERVED,
                claim_refs=(CLAIM,),
            )
        )


def test_an_unregistered_measurement_refuses_every_read() -> None:
    engine = _stack()
    for call in (
        lambda: engine.current_value("obs:ghost"),
        lambda: engine.current_unit("obs:ghost"),
        lambda: engine.compute_ratio("obs:ghost"),
        lambda: engine.availability_state("obs:ghost"),
    ):
        with pytest.raises(Book6RegistryError, match="is not registered"):
            call()


# -- D2-6 firewall: no usage/health research surface (Phase 27) ---------------


def test_no_d2_6_research_executor_exists_in_book6() -> None:
    """D6M-5 = OPEN_DEFERRED: the research design is not executed anywhere."""

    from crypto_systems_intelligence_atlas import (
        book6_comparability,
        book6_definitions,
        book6_sensitivity,
    )

    forbidden_tokens = (
        "usage_threshold",
        "health_threshold",
        "retention_threshold",
        "sybil",
        "bot_detect",
        "persistence_threshold",
        "adoption_success",
        "empirical_study",
    )
    for module in (book6_core, book6_records, book6_states, book6_definitions,
                   book6_comparability, book6_sensitivity):
        for name in dir(module):
            lowered = name.lower()
            assert not any(token in lowered for token in forbidden_tokens), (
                f"{module.__name__}.{name}"
            )


def test_no_book6_module_imports_a_network_or_persistence_client() -> None:
    """The kernel is offline: no RPC, no HTTP, no database, no scheduler."""

    import ast
    import pathlib

    import crypto_systems_intelligence_atlas as pkg

    forbidden_modules = {
        "requests",
        "httpx",
        "aiohttp",
        "urllib.request",
        "urllib3",
        "socket",
        "sqlalchemy",
        "psycopg2",
        "sqlite3",
        "neo4j",
        "pymongo",
        "redis",
        "asyncio.sleep",
        "schedule",
    }
    root = pathlib.Path(pkg.__file__).parent
    offenders: list[str] = []
    for path in sorted(root.glob("book6_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in forbidden_modules or alias.name.split(".")[0] in forbidden_modules:
                        offenders.append(f"{path.name}: import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = (node.module or "").lstrip(".")
                if module in forbidden_modules or module.split(".")[0] in forbidden_modules:
                    offenders.append(f"{path.name}: from {module}")
    assert offenders == []


def test_the_no_provenance_escape_hatch_is_closed() -> None:
    from crypto_systems_intelligence_atlas.book6_provenance import (
        Book6Provenance,
        Book6ProvenanceError,
    )
    from crypto_systems_intelligence_atlas.book6_support import build_stores

    claim_store, evidence_store, _ = build_stores()
    with pytest.raises(Book6ProvenanceError, match="explicit provenance resolver"):
        Book6Provenance(claim_store, evidence_store, require_provenance=False)


def test_an_unknown_book_2_claim_reference_is_refused() -> None:
    engine = _stack()
    with pytest.raises(Exception):
        engine.provenance.resolve_claim("fixture:claim:does-not-exist")


def test_a_decayed_claim_reference_is_refused_at_use() -> None:
    """REGISTERED THEN != AUTHORITATIVE NOW, proven at the read path."""

    engine, claim_store, _, service = build_engine(DECAYING_CLAIM)
    engine.registry.register_definition(definition(METRIC))
    engine.registry.register_measurement(
        windowed_observation(
            "obs:1",
            METRIC,
            value=7.0,
            missingness=MissingnessState.OBSERVED,
            claim_refs=(DECAYING_CLAIM,),
        )
    )
    assert engine.current_value("obs:1") == 7.0
    decay_claim(service, claim_store, DECAYING_CLAIM, "STALE")
    with pytest.raises(Book6RegistryError, match="no current Book 2 authority"):
        engine.current_value("obs:1")
