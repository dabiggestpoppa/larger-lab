"""SENSOR-B5-I09E1 - RED-first semantic/methodology registry tests (SEM-01..SEM-36).

The I09 counterpart of the U08 suite: every test names the frozen clause it
enforces and the matrix row (``BLOC_05_I09_IMPLEMENTATION_EVIDENCE.md`` §2)
that owns it.  Written FIRST, against a ``common/`` package that does not yet
contain ``methodologies.py`` / ``semantic_registry.py`` / ``comparability.py``
(the RED record is the collection error this file alone produces).

Clause map:

* 03 §16 / 07 §4 / 07 F14  -> the ``NormalizationMethodology`` object + versioning
* 03 §11 / 07 F15          -> the ``ProviderSemanticMapping`` object + class law
* 03 §12 / 06 §5           -> the provider semantic registry (eight-provider schema)
* 03 §13                   -> the semantic-confidence ladder
* 03 §18                   -> the eight-condition comparability gate
* 05 §11 / 05 §12 / 03 §14 -> missingness + quality-flag REUSE (never fork)
* 07 F16 / 07 F24          -> provider-native evidence + no cross-venue synthesis
* BOOK 00 Q1/Q2/Q4/Q6/Q7/Q8 -> the operator decisions recorded as laws

OFFLINE.  No network, no wall clock, no filesystem writes.  The two live Bloc 1
configs are READ as text (they are the projection source); nothing writes them.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

_HERE = Path(__file__).resolve().parent
_QUANT_LAB = _HERE.parents[2]
_CONFIG = _QUANT_LAB / "config" / "crypto_sensor_fabric"
METHODOLOGY_YAML = _CONFIG / "methodology_registry.yaml"
SEMANTIC_YAML = _CONFIG / "semantic_equivalence.yaml"

#: The Bloc 1 commit that introduced the live registries (readiness §2).
BLOC1_REGISTRY_COMMIT = "8b2162a1184bdd885b09f5a0efaae4adeb4f7c9a"

#: The evidence-reference token that means "no probe has proven this mapping".
PENDING_EVIDENCE = "BLOC2_PROBE_PENDING"


def _methodology_text() -> str:
    return METHODOLOGY_YAML.read_text(encoding="utf-8")


def _full_methodology(**overrides: object) -> object:
    from crypto_sensor_fabric.normalization.common import NormalizationMethodology

    payload: dict[str, object] = {
        "methodology_id": "SYNTHETIC_LINEAR_OI_USD_V1",
        "version": "1",
        "sensor_family": "MECHANICAL_OPEN_INTEREST",
        "description": "Synthetic fixture: contract-count OI to USD via multiplier and mark price.",
        "formula_or_algorithm": "oi_usd = oi_native * contract_multiplier * mark_price",
        "required_inputs": ("oi_native", "contract_multiplier", "pit_mark_price"),
        "output_units": ("USD",),
        "PIT_requirements": "mark price effective_at and market_available_at <= knowledge cutoff",
        "known_limitations": ("requires a PIT-valid reference price; refuses float inputs",),
        "introduced_at": BLOC1_REGISTRY_COMMIT,
        "deprecated_at": None,
    }
    payload.update(overrides)
    return NormalizationMethodology.model_validate(payload)


def _full_mapping(**overrides: object) -> object:
    from crypto_sensor_fabric.normalization.common import ProviderSemanticMapping

    payload: dict[str, object] = {
        "provider": "BINANCE_USDM",
        "provider_field": "openInterest",
        "canonical_sensor": "MECHANICAL_OPEN_INTEREST",
        "canonical_field": "oi_native",
        "semantic_equivalence_class": "NORMALIZABLE_COMPARABLE",
        "native_definition": "Synthetic fixture: open interest in contracts at sample time.",
        "transformation": "preserve native; normalize only via a registered methodology",
        "methodology_id": "SYNTHETIC_LINEAR_OI_USD_V1",
        "blocking_assumptions": ("semantics unverified in this repository",),
        "known_limitations": ("probe evidence pending",),
        "source_endpoint_or_archive": "synthetic structural fixture (not a provider claim)",
        "data_type": "DECIMAL_STRING",
        "native_unit": "CONTRACTS",
        "timestamp_meaning": "sampled at request time (synthetic fixture)",
        "interval_data_scope": "POINT_SNAPSHOT",
        "direction_side_convention": "not applicable to open interest",
        "evidence_reference": PENDING_EVIDENCE,
        "semantic_confidence": "AMBIGUOUS",
        "last_verified_date": None,
        "version": "1",
    }
    payload.update(overrides)
    return ProviderSemanticMapping.model_validate(payload)


def _facts(label: str, **overrides: object) -> object:
    from crypto_sensor_fabric.normalization.common import ComparableFieldFacts

    payload: dict[str, object] = {
        "label": label,
        "sensor_family": "MECHANICAL_OPEN_INTEREST",
        "canonical_field": "oi_usd",
        "economic_definition": "total long+short contracts open, marked to USD",
        "interval_data_scope": "POINT_SNAPSHOT",
        "unit": "USD",
        "asset_id": None,
        "conversion_registered": False,
        "conversion_methodology_id": None,
        "venue_scope": "SYNTHETIC_VENUE_SCOPE",
        "identity_resolved": True,
        "quality_flags": (),
        "equivalence_class": "NORMALIZABLE_COMPARABLE",
    }
    payload.update(overrides)
    return ComparableFieldFacts.model_validate(payload)


# ---------------------------------------------------------------------------
# SEM-01..SEM-03 -- 03 §16 / 07 §4 / 07 F14: NormalizationMethodology
# ---------------------------------------------------------------------------


def test_sem01_methodology_frozen_field_set_and_immutability() -> None:
    """03 §16 freezes exactly eleven fields; the record is immutable."""
    row = _full_methodology()
    assert tuple(type(row).model_fields) == (
        "methodology_id",
        "version",
        "sensor_family",
        "description",
        "formula_or_algorithm",
        "required_inputs",
        "output_units",
        "PIT_requirements",
        "known_limitations",
        "introduced_at",
        "deprecated_at",
    )
    with pytest.raises(ValidationError):
        row.methodology_id = "OTHER"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        _full_methodology(unexpected_field="refused")


def test_sem02_f14_versioning_law() -> None:
    """07 F14: same (id, version) redefinition refused; a bump is a new row and
    the historical row stays resolvable; an unversioned lookup with two live
    versions fails closed instead of picking."""
    from crypto_sensor_fabric.normalization.common import (
        NormalizationMethodologyRegistry,
    )

    original = _full_methodology()
    registry = NormalizationMethodologyRegistry.model_validate(
        {"schema_version": "1.0", "methodologies": [original.model_dump(mode="json")]}
    )
    assert registry.resolve("SYNTHETIC_LINEAR_OI_USD_V1", "1") == original
    assert registry.versions("SYNTHETIC_LINEAR_OI_USD_V1") == ("1",)

    bumped = _full_methodology(
        version="2",
        formula_or_algorithm="oi_usd = oi_native * multiplier * index_price",
    )
    grown = NormalizationMethodologyRegistry.model_validate(
        {
            "schema_version": "1.0",
            "methodologies": [
                original.model_dump(mode="json"),
                bumped.model_dump(mode="json"),
            ],
        }
    )
    assert grown.resolve("SYNTHETIC_LINEAR_OI_USD_V1", "1") is not None
    assert grown.resolve("SYNTHETIC_LINEAR_OI_USD_V1", "2") is not None
    assert grown.resolve("SYNTHETIC_LINEAR_OI_USD_V1") is None
    assert (
        grown.require("SYNTHETIC_LINEAR_OI_USD_V1", "1").formula_or_algorithm
        == original.formula_or_algorithm
    )

    with pytest.raises(ValidationError, match="duplicate"):
        NormalizationMethodologyRegistry.model_validate(
            {
                "schema_version": "1.0",
                "methodologies": [
                    original.model_dump(mode="json"),
                    original.model_dump(mode="json"),
                ],
            }
        )


def test_sem03_typed_refusal_never_a_default() -> None:
    """Unknown methodology -> None from resolve, typed LookupError from require;
    no synthesized row, no guessed default (06 §1 G9)."""
    from crypto_sensor_fabric.normalization.common import (
        NormalizationMethodologyRegistry,
        UnknownNormalizationMethodology,
    )

    registry = NormalizationMethodologyRegistry.model_validate(
        {"schema_version": "1.0", "methodologies": []}
    )
    assert registry.resolve("ANYTHING", "1") is None
    with pytest.raises(UnknownNormalizationMethodology):
        registry.require("ANYTHING", "1")
    assert registry.version_token() == "1.0"


def test_sem03b_methodology_registry_text_round_trip() -> None:
    """Text-in/text-out YAML: serialize is independent of input row order and
    parse(serialize(x)) reproduces x byte-identically (determinism)."""
    from crypto_sensor_fabric.normalization.common import (
        NormalizationMethodologyRegistry,
        parse_normalization_methodology_registry_yaml,
        serialize_normalization_methodology_registry_yaml,
    )

    rows = [
        _full_methodology().model_dump(mode="json"),
        _full_methodology(
            methodology_id="SYNTHETIC_FUNDING_8H_V1",
            sensor_family="MECHANICAL_FUNDING",
            formula_or_algorithm="rate_8h = rate_native * (28800 / interval_seconds)",
        ).model_dump(mode="json"),
    ]
    forward = NormalizationMethodologyRegistry.model_validate(
        {"schema_version": "1.0", "methodologies": rows}
    )
    reverse = NormalizationMethodologyRegistry.model_validate(
        {"schema_version": "1.0", "methodologies": list(reversed(rows))}
    )
    text_a = serialize_normalization_methodology_registry_yaml(forward)
    text_b = serialize_normalization_methodology_registry_yaml(reverse)
    assert text_a == text_b, "canonical serialization must not depend on input order"
    reparsed = parse_normalization_methodology_registry_yaml(text_a)
    assert serialize_normalization_methodology_registry_yaml(reparsed) == text_a
    assert reparsed.model_dump(mode="json") == forward.model_dump(mode="json")


# ---------------------------------------------------------------------------
# SEM-04..SEM-06 -- 03 §11 / 07 F15: ProviderSemanticMapping
# ---------------------------------------------------------------------------


def test_sem04_mapping_frozen_field_set_and_immutability() -> None:
    """03 §11's eight names are preserved verbatim, 03 §12's record attributes
    complete the frozen 07 §4 object, extra fields are refused."""
    row = _full_mapping()
    fields = tuple(type(row).model_fields)
    for frozen_name in (
        "provider_field",
        "canonical_field",
        "semantic_equivalence_class",
        "native_definition",
        "transformation",
        "methodology_id",
        "blocking_assumptions",
        "known_limitations",
    ):
        assert frozen_name in fields, frozen_name
    for record_name in (
        "source_endpoint_or_archive",
        "data_type",
        "native_unit",
        "timestamp_meaning",
        "interval_data_scope",
        "direction_side_convention",
        "evidence_reference",
        "semantic_confidence",
        "last_verified_date",
    ):
        assert record_name in fields, record_name
    with pytest.raises(ValidationError):
        row.canonical_field = "other"  # type: ignore[misc]
    with pytest.raises(ValidationError):
        _full_mapping(surprise="refused")


def test_sem05_bloc1_laws_re_enforced_and_missing_assumptions_refused() -> None:
    """B1-T41/T43 survive the upgrade; readiness §10 stop 1 refuses a mapping
    that cannot state its blocking assumptions or known limitations."""
    from crypto_sensor_fabric.normalization.common import ProviderSemanticMapping

    with pytest.raises(ValidationError, match="methodology_id"):
        _full_mapping(methodology_id=None, semantic_equivalence_class="NORMALIZABLE_COMPARABLE")
    with pytest.raises(ValidationError, match="evidence_reference"):
        _full_mapping(evidence_reference=None, semantic_equivalence_class="EXACT_EQUIVALENT")
    base = _full_mapping().model_dump(mode="json")
    with pytest.raises(ValidationError):
        ProviderSemanticMapping.model_validate({**base, "blocking_assumptions": []})
    with pytest.raises(ValidationError):
        ProviderSemanticMapping.model_validate({**base, "known_limitations": []})


def test_sem06_mapping_serialization_is_deterministic() -> None:
    """Two orders of the same rows serialize byte-identically; parse -> serialize
    -> parse is the identity (06 §1 G8 reproducibility)."""
    from crypto_sensor_fabric.normalization.common import (
        ProviderSemanticRegistry,
        parse_provider_semantic_registry_yaml,
        serialize_provider_semantic_registry_yaml,
    )

    rows = [
        _full_mapping().model_dump(mode="json"),
        _full_mapping(
            provider="KRAKEN_FUTURES",
            provider_field="funding_rate",
            canonical_sensor="MECHANICAL_FUNDING",
            canonical_field="funding_rate_native",
            native_unit="RATE_PER_INTERVAL",
        ).model_dump(mode="json"),
    ]
    forward = ProviderSemanticRegistry.model_validate({"schema_version": "1.0", "mappings": rows})
    reverse = ProviderSemanticRegistry.model_validate(
        {"schema_version": "1.0", "mappings": list(reversed(rows))}
    )
    text_a = serialize_provider_semantic_registry_yaml(forward)
    text_b = serialize_provider_semantic_registry_yaml(reverse)
    assert text_a == text_b
    reparsed = parse_provider_semantic_registry_yaml(text_a)
    assert serialize_provider_semantic_registry_yaml(reparsed) == text_a


# ---------------------------------------------------------------------------
# SEM-07..SEM-09 -- 03 §12: registry ordering, refusal, no synthesis
# ---------------------------------------------------------------------------


def test_sem07_registry_duplicate_key_refused_and_order_is_canonical() -> None:
    from crypto_sensor_fabric.normalization.common import ProviderSemanticRegistry

    row = _full_mapping().model_dump(mode="json")
    with pytest.raises(ValidationError, match="duplicate"):
        ProviderSemanticRegistry.model_validate({"schema_version": "1.0", "mappings": [row, row]})
    registry = ProviderSemanticRegistry.model_validate(
        {"schema_version": "1.0", "mappings": [row]}
    )
    keys = [
        (m.provider, m.canonical_sensor.value, m.provider_field) for m in registry.mappings
    ]
    assert keys == sorted(keys)


def test_sem08_unknown_provider_field_and_mapping_fail_closed() -> None:
    """An unknown (provider, field) pair resolves to None and requires a typed
    refusal; an unknown PROVIDER token is refused at construction (Q6)."""
    from crypto_sensor_fabric.contracts.enums import SensorFamily
    from crypto_sensor_fabric.normalization.common import (
        ProviderSemanticRegistry,
        UnknownProviderSemanticMapping,
    )

    registry = ProviderSemanticRegistry.model_validate(
        {"schema_version": "1.0", "mappings": [_full_mapping().model_dump(mode="json")]}
    )
    assert (
        registry.resolve("BINANCE_USDM", "not_a_field", SensorFamily.MECHANICAL_OPEN_INTEREST)
        is None
    )
    with pytest.raises(UnknownProviderSemanticMapping):
        registry.require("BINANCE_USDM", "not_a_field", SensorFamily.MECHANICAL_OPEN_INTEREST)
    with pytest.raises(ValidationError):
        _full_mapping(provider="INVENTED_EXCHANGE")


def test_sem09_no_default_synthesis_from_a_similar_row() -> None:
    """The same field NAME on another sensor family never cross-fills a missing
    mapping (bloc_01 §13: same field name never establishes comparability)."""
    from crypto_sensor_fabric.contracts.enums import SensorFamily
    from crypto_sensor_fabric.normalization.common import ProviderSemanticRegistry

    registry = ProviderSemanticRegistry.model_validate(
        {"schema_version": "1.0", "mappings": [_full_mapping().model_dump(mode="json")]}
    )
    assert (
        registry.resolve("BINANCE_USDM", "openInterest", SensorFamily.MECHANICAL_FUNDING) is None
    )


# ---------------------------------------------------------------------------
# SEM-10..SEM-12 -- 03 §13: semantic confidence ladder
# ---------------------------------------------------------------------------


def test_sem10_confidence_ladder_is_frozen_and_ambiguous_blocks() -> None:
    from crypto_sensor_fabric.normalization.common import (
        SemanticConfidence,
        admits_critical_t1_use,
    )

    assert [member.value for member in SemanticConfidence] == [
        "VERIFIED_FIRST_PARTY",
        "VERIFIED_SECONDARY",
        "RECONSTRUCTED_FROM_FIRST_PARTY_FIELDS",
        "COMMUNITY_DOCUMENTED",
        "AMBIGUOUS",
    ]
    assert admits_critical_t1_use(SemanticConfidence.AMBIGUOUS) is False
    for member in SemanticConfidence:
        if member is not SemanticConfidence.AMBIGUOUS:
            assert admits_critical_t1_use(member) is True


def test_sem11_community_evidence_never_masquerades_as_first_party() -> None:
    """03 §13: community evidence supports corroboration but can never be
    first-party semantics; the confidence/evidence coherence law refuses a
    VERIFIED_* claim that still points at pending evidence (Q7)."""
    from crypto_sensor_fabric.normalization.common import (
        SemanticConfidence,
        is_first_party_grade,
    )

    assert is_first_party_grade(SemanticConfidence.VERIFIED_FIRST_PARTY) is True
    assert is_first_party_grade(SemanticConfidence.COMMUNITY_DOCUMENTED) is False
    assert is_first_party_grade(SemanticConfidence.AMBIGUOUS) is False
    with pytest.raises(ValidationError):
        _full_mapping(
            semantic_confidence="VERIFIED_FIRST_PARTY", evidence_reference=PENDING_EVIDENCE
        )
    with pytest.raises(ValidationError):
        _full_mapping(semantic_confidence="COMMUNITY_DOCUMENTED", evidence_reference=None)


def test_sem12_equivalence_vocabulary_integrity_and_refusal() -> None:
    """The four frozen classes are exactly the upstream enum; NOT_COMPARABLE
    and CORROBORATION_ONLY never pool (B1-T42 via the upstream law)."""
    from crypto_sensor_fabric.contracts.enums import SemanticEquivalence
    from crypto_sensor_fabric.registry.semantic_equivalence import is_poolable

    assert [member.value for member in SemanticEquivalence] == [
        "EXACT_EQUIVALENT",
        "NORMALIZABLE_COMPARABLE",
        "CORROBORATION_ONLY",
        "NOT_COMPARABLE",
    ]
    assert is_poolable(SemanticEquivalence.EXACT_EQUIVALENT) is True
    assert is_poolable(SemanticEquivalence.NORMALIZABLE_COMPARABLE) is True
    assert is_poolable(SemanticEquivalence.CORROBORATION_ONLY) is False
    assert is_poolable(SemanticEquivalence.NOT_COMPARABLE) is False


# ---------------------------------------------------------------------------
# SEM-13/SEM-14 -- 05 §11/§12 reuse (never fork)
# ---------------------------------------------------------------------------


def test_sem13_missingness_vocabulary_is_reused_not_forked() -> None:
    """05 §12's thirteen members are the operative vocabulary; the I01 enum is
    imported, never re-declared, and 03 §14's SEMANTICS_UNVERIFIED is a quality
    flag, not a missingness reason."""
    from crypto_sensor_fabric.normalization.enums import (
        MissingnessReason,
        NormalizationQualityFlag,
    )

    frozen_05_12 = {
        "NOT_REPORTED",
        "NOT_SUPPORTED",
        "NOT_YET_LISTED",
        "DELISTED",
        "HISTORY_UNAVAILABLE",
        "PROVIDER_EMPTY",
        "ACCESS_BLOCKED",
        "SOURCE_GAP",
        "IDENTITY_BLOCKED",
        "TIME_BLOCKED",
        "SEMANTICS_BLOCKED",
        "CONVERSION_BLOCKED",
        "QUARANTINED",
    }
    assert {member.value for member in MissingnessReason} == frozen_05_12
    assert "SEMANTICS_UNVERIFIED" not in {member.value for member in MissingnessReason}
    assert NormalizationQualityFlag.SEMANTICS_UNVERIFIED.value == "SEMANTICS_UNVERIFIED"


def test_sem14_a_refusal_carries_a_typed_missingness_cause() -> None:
    """Readiness §6: a semantic refusal states WHICH cause applies, never a
    generic bool; the decision is typed so null stays distinguishable from a
    verified zero."""
    from crypto_sensor_fabric.normalization.common import (
        ComparabilityCondition,
        evaluate_comparability,
    )
    from crypto_sensor_fabric.normalization.enums import (
        MissingnessReason,
        NormalizationQualityFlag,
    )

    decision = evaluate_comparability(_facts("left"), _facts("right", identity_resolved=False))
    assert decision.admitted is False
    assert decision.missingness_reason is MissingnessReason.IDENTITY_BLOCKED
    flagged = evaluate_comparability(
        _facts("left", quality_flags=(NormalizationQualityFlag.SEMANTICS_UNVERIFIED,)),
        _facts("right"),
    )
    assert ComparabilityCondition.NO_BLOCKING_QUALITY_FLAGS in flagged.refused_conditions
    assert flagged.missingness_reason is MissingnessReason.SEMANTICS_BLOCKED


# ---------------------------------------------------------------------------
# SEM-15..SEM-24 -- 03 §18: the eight-condition gate, one negative per condition
# ---------------------------------------------------------------------------


def test_sem15_condition_1_sensor_family_must_match() -> None:
    from crypto_sensor_fabric.normalization.common import (
        ComparabilityCondition,
        evaluate_comparability,
    )

    decision = evaluate_comparability(
        _facts("left"), _facts("right", sensor_family="MECHANICAL_FUNDING")
    )
    assert ComparabilityCondition.SENSOR_FAMILY_SAME in decision.refused_conditions
    assert decision.admitted is False


def test_sem16_condition_2_same_canonical_quantity_and_stated_definitions() -> None:
    from crypto_sensor_fabric.normalization.common import (
        ComparabilityCondition,
        evaluate_comparability,
    )

    different_quantity = evaluate_comparability(
        _facts("left", canonical_field="oi_usd"),
        _facts("right", canonical_field="funding_rate_8h_equivalent"),
    )
    assert (
        ComparabilityCondition.ECONOMIC_DEFINITION_COMPATIBLE
        in different_quantity.refused_conditions
    )
    undefined = evaluate_comparability(
        _facts("left", economic_definition=None), _facts("right")
    )
    assert ComparabilityCondition.ECONOMIC_DEFINITION_COMPATIBLE in undefined.refused_conditions


def test_sem17_condition_3_interval_semantics_must_be_compatible() -> None:
    from crypto_sensor_fabric.normalization.common import (
        ComparabilityCondition,
        evaluate_comparability,
    )

    cumulative = evaluate_comparability(
        _facts("left", interval_data_scope="CUMULATIVE"),
        _facts("right", interval_data_scope="POINT_SNAPSHOT"),
    )
    assert ComparabilityCondition.INTERVAL_SEMANTICS_COMPATIBLE in cumulative.refused_conditions
    unknown = evaluate_comparability(
        _facts("left", interval_data_scope="PROVIDER_NATIVE_UNKNOWN"), _facts("right")
    )
    assert ComparabilityCondition.INTERVAL_SEMANTICS_COMPATIBLE in unknown.refused_conditions, (
        "an unclassified interval convention is a refusal, never a compatibility"
    )


def test_sem18_condition_4_units_need_an_explicit_registered_conversion() -> None:
    from crypto_sensor_fabric.normalization.common import (
        ComparabilityCondition,
        evaluate_comparability,
    )

    unregistered = evaluate_comparability(_facts("left", unit="USD"), _facts("right", unit="USDT"))
    assert (
        ComparabilityCondition.UNITS_COMPATIBLE_AFTER_EXPLICIT_CONVERSION
        in unregistered.refused_conditions
    )
    registered = evaluate_comparability(
        _facts("left", unit="USD"),
        _facts(
            "right",
            unit="USDT",
            conversion_registered=True,
            conversion_methodology_id="B5_I08_UNITS_V1",
        ),
    )
    assert registered.admitted is True
    # L2 posture: an asset-required unit without asset identity is refused.
    bare = evaluate_comparability(
        _facts("left", unit="BASE_ASSET", asset_id=None),
        _facts("right", unit="BASE_ASSET", asset_id=None),
    )
    assert (
        ComparabilityCondition.UNITS_COMPATIBLE_AFTER_EXPLICIT_CONVERSION
        in bare.refused_conditions
    )
    qualified = evaluate_comparability(
        _facts("left", unit="BASE_ASSET", asset_id="BTC"),
        _facts("right", unit="BASE_ASSET", asset_id="BTC"),
    )
    assert qualified.admitted is True


def test_sem19_condition_5_venue_scope_must_be_declared() -> None:
    from crypto_sensor_fabric.normalization.common import (
        ComparabilityCondition,
        evaluate_comparability,
    )

    decision = evaluate_comparability(_facts("left", venue_scope=None), _facts("right"))
    assert ComparabilityCondition.VENUE_SCOPE_KNOWN in decision.refused_conditions


def test_sem20_condition_6_identity_must_be_resolved() -> None:
    from crypto_sensor_fabric.normalization.common import (
        ComparabilityCondition,
        evaluate_comparability,
    )

    decision = evaluate_comparability(_facts("left", identity_resolved=False), _facts("right"))
    assert ComparabilityCondition.IDENTITY_RESOLVED in decision.refused_conditions


def test_sem21_condition_7_blocking_quality_flags_refuse() -> None:
    from crypto_sensor_fabric.normalization.common import (
        ComparabilityCondition,
        evaluate_comparability,
    )
    from crypto_sensor_fabric.normalization.enums import (
        BLOCKING_QUALITY_FLAGS,
        MissingnessReason,
        NormalizationQualityFlag,
    )

    assert NormalizationQualityFlag.SEMANTICS_UNVERIFIED in BLOCKING_QUALITY_FLAGS
    assert NormalizationQualityFlag.TIME_ARCHIVE_RECONSTRUCTION not in BLOCKING_QUALITY_FLAGS
    label_only = evaluate_comparability(
        _facts("left", quality_flags=(NormalizationQualityFlag.TIME_ARCHIVE_RECONSTRUCTION,)),
        _facts("right"),
    )
    assert label_only.admitted is True, "label-only flags must not block (enums law)"
    broken = evaluate_comparability(
        _facts("left", quality_flags=(NormalizationQualityFlag.LINEAGE_BROKEN,)),
        _facts("right"),
    )
    assert ComparabilityCondition.NO_BLOCKING_QUALITY_FLAGS in broken.refused_conditions
    assert broken.missingness_reason is MissingnessReason.QUARANTINED


def test_sem22_condition_8_equivalence_class_must_permit() -> None:
    from crypto_sensor_fabric.normalization.common import (
        ComparabilityCondition,
        evaluate_comparability,
    )

    for refused_class in ("CORROBORATION_ONLY", "NOT_COMPARABLE"):
        decision = evaluate_comparability(
            _facts("left", equivalence_class=refused_class), _facts("right")
        )
        assert (
            ComparabilityCondition.EQUIVALENCE_CLASS_PERMITS_COMPARISON
            in decision.refused_conditions
        )
        assert decision.admitted is False


def test_sem23_all_eight_conditions_satisfied_admits() -> None:
    from crypto_sensor_fabric.normalization.common import (
        ComparabilityCondition,
        evaluate_comparability,
    )

    decision = evaluate_comparability(_facts("left"), _facts("right"))
    assert decision.admitted is True
    assert decision.refused_conditions == ()
    assert len(decision.verdicts) == len(ComparabilityCondition)
    assert all(verdict.satisfied for verdict in decision.verdicts)
    assert decision.missingness_reason is None


def test_sem24_missing_facts_fail_closed_without_raising() -> None:
    """A comparison is admitted only when EVERY required condition is supported:
    an unset fact is a refusal with a reason, never an exception and never a
    default (06 §1 G9)."""
    from crypto_sensor_fabric.normalization.common import (
        ComparableFieldFacts,
        ComparabilityCondition,
        evaluate_comparability,
    )

    empty = ComparableFieldFacts.model_validate({"label": "empty"})
    decision = evaluate_comparability(empty, _facts("right"))
    assert decision.admitted is False
    # An empty quality-flag set is a legitimate declared value ("no flags"),
    # so condition 7 alone is satisfied; every other condition needs a fact
    # the empty side did not declare.
    assert set(decision.refused_conditions) == set(ComparabilityCondition) - {
        ComparabilityCondition.NO_BLOCKING_QUALITY_FLAGS
    }
    assert all(verdict.reason for verdict in decision.verdicts)
    no_class = evaluate_comparability(_facts("left", equivalence_class=None), _facts("right"))
    assert (
        ComparabilityCondition.EQUIVALENCE_CLASS_PERMITS_COMPARISON
        in no_class.refused_conditions
    )


# ---------------------------------------------------------------------------
# SEM-25..SEM-28 -- Q4/Q2/F24/F16
# ---------------------------------------------------------------------------


def test_sem25_methodology_ref_and_registry_version_token_without_envelope() -> None:
    """Q4: I09 supplies the two methodology fields' typed interfaces and the
    registry version token, and does NOT release the frozen composite name."""
    import crypto_sensor_fabric.normalization as normalization
    from crypto_sensor_fabric.normalization.common import (
        MethodologyRef,
        NormalizationMethodologyRegistry,
    )

    row = _full_methodology()
    ref = MethodologyRef.from_methodology(row)
    assert ref.methodology_id == row.methodology_id and ref.version == row.version
    with pytest.raises(ValidationError):
        MethodologyRef(methodology_id="", version="1")
    registry = NormalizationMethodologyRegistry.model_validate(
        {"schema_version": "2026.10-i09", "methodologies": []}
    )
    assert registry.version_token() == "2026.10-i09"
    assert len(normalization.__all__) == 24
    assert "T1ObservationEnvelope" not in normalization.__all__
    assert "T1ObservationEnvelope" not in dir(normalization)


def test_sem26_the_i08_identifier_is_preserved_and_held_unresolved() -> None:
    """Q2 fail-closed branch: the adapter CAN hold B5_I08_UNITS_V1 when an
    operator supplies a sensor-family ruling, but the I09 evidence producer
    records it UNRESOLVED because sensor_family is not establishable from
    accepted evidence for a cross-family unit methodology."""
    from crypto_sensor_fabric.normalization.common import (
        NormalizationMethodologyRegistry,
    )

    registry = NormalizationMethodologyRegistry.model_validate(
        {
            "schema_version": "1.0",
            "methodologies": [
                _full_methodology(
                    methodology_id="B5_I08_UNITS_V1",
                    sensor_family="MECHANICAL_OPEN_INTEREST",
                ).model_dump(mode="json")
            ],
        }
    )
    assert registry.resolve("B5_I08_UNITS_V1", "1") is not None
    assert "B5_I08_UNITS_V1" not in _methodology_text(), (
        "the live config must not gain an I09 row (Q1: preserve, do not edit)"
    )


def test_sem27_cross_venue_comparison_is_a_decision_never_a_synthesis() -> None:
    """07 F24: the gate returns admissibility only -- no value, no merged
    record; cross-venue fields may be comparable while remaining unpooled."""
    from crypto_sensor_fabric.normalization.common import (
        ComparabilityDecision,
        evaluate_comparability,
    )

    decision = evaluate_comparability(
        _facts("binance_side", venue_scope="BINANCE_USDM:USD-M"),
        _facts("bybit_side", venue_scope="BYBIT_LINEAR:linear"),
    )
    assert decision.admitted is True
    fields = set(ComparabilityDecision.model_fields)
    for forbidden in ("value", "merged", "pooled", "consensus", "synthesized_value"):
        assert forbidden not in fields


def test_sem28_provider_native_analytics_stay_evidence() -> None:
    """07 F16 / 03 §19: a CORROBORATION_ONLY provider-native analytic is stored
    as evidence and refused for cross-provider canonical use."""
    from crypto_sensor_fabric.normalization.common import admits_critical_t1_use
    from crypto_sensor_fabric.registry.semantic_equivalence import is_poolable

    row = _full_mapping(
        provider="DERIBIT",
        provider_field="trade.liquidation",
        canonical_sensor="MECHANICAL_LIQUIDATION",
        canonical_field="liquidation_role",
        semantic_equivalence_class="CORROBORATION_ONLY",
        methodology_id="DERIBIT_TRADE_LIQ_TAG_V1",
        native_unit="COUNT",
    )
    assert row.evidence_reference == PENDING_EVIDENCE
    assert is_poolable(row.semantic_equivalence_class) is False
    assert admits_critical_t1_use(row.semantic_confidence) is False


# ---------------------------------------------------------------------------
# SEM-29..SEM-36 -- Q1/Q6/Q7 projection laws over the LIVE configs
# ---------------------------------------------------------------------------


def test_sem29_live_configs_are_intact_and_projection_ready() -> None:
    """Q1: the live Bloc 1 configs carry the nine planning methodology ids and
    the six pending mappings; every mapping's methodology_id resolves upstream
    before I09 projects anything."""
    from crypto_sensor_fabric.registry.methodology_registry import load_methodology_registry
    from crypto_sensor_fabric.registry.semantic_equivalence import load_semantic_equivalence

    bloc1_methodologies = load_methodology_registry(METHODOLOGY_YAML)
    bloc1_mappings = load_semantic_equivalence(SEMANTIC_YAML)
    assert len(bloc1_methodologies.methodologies) == 9
    assert len(bloc1_mappings.mappings) == 6
    for mapping in bloc1_mappings.mappings:
        assert mapping.evidence_reference == PENDING_EVIDENCE
        assert mapping.methodology_id in bloc1_methodologies.methodologies
        assert mapping.version == "1"


def test_sem30_projected_mappings_stay_ambiguous_and_pending() -> None:
    """Q7: the projection adapter preserves class, methodology_id, evidence
    reference and version, and refuses any confidence upgrade while the
    evidence reference is still pending."""
    from crypto_sensor_fabric.normalization.common import (
        SemanticConfidence,
        project_planning_mapping,
    )
    from crypto_sensor_fabric.registry.semantic_equivalence import load_semantic_equivalence

    bloc1 = load_semantic_equivalence(SEMANTIC_YAML)
    for mapping in bloc1.mappings:
        projected = project_planning_mapping(
            mapping,
            source_endpoint_or_archive="synthetic structural fixture (I09-a)",
            data_type="DECIMAL_STRING",
            native_unit="UNVERIFIED_NATIVE_UNIT",
            timestamp_meaning="unverified; see the provider time-semantics registry",
            interval_data_scope="PROVIDER_NATIVE_UNKNOWN",
            direction_side_convention="unverified (BLOC2_PROBE_PENDING)",
            blocking_assumptions=(
                "provider semantics unverified: evidence_reference is BLOC2_PROBE_PENDING "
                "and no first-party documentation exists in this repository "
                "(03 §13 AMBIGUOUS; barred from critical T1 normalized fields)",
            ),
            known_limitations=(
                "provisional planning mapping only; class, methodology_id and version are "
                "preserved from the Bloc 1 registry and may not be upgraded without "
                "documentary proof (BOOK 00 Q7)",
            ),
        )
        assert projected.semantic_confidence is SemanticConfidence.AMBIGUOUS
        assert projected.evidence_reference == mapping.evidence_reference
        assert projected.semantic_equivalence_class is mapping.equivalence
        assert projected.methodology_id == mapping.methodology_id
        assert projected.version == mapping.version
        assert projected.canonical_field == mapping.canonical_field
        assert projected.provider_field == mapping.source_metric
        assert projected.native_definition == mapping.source_definition
        assert projected.transformation == mapping.transformation_method
    with pytest.raises(ValidationError):
        project_planning_mapping(
            bloc1.mappings[0],
            source_endpoint_or_archive="x",
            data_type="x",
            native_unit="x",
            timestamp_meaning="x",
            interval_data_scope="PROVIDER_NATIVE_UNKNOWN",
            direction_side_convention="x",
            blocking_assumptions=("x",),
            known_limitations=("x",),
            semantic_confidence="VERIFIED_FIRST_PARTY",
        )


def test_sem31_empty_registry_resolves_nothing_and_names_the_missing_cause() -> None:
    """Q6: an unknown (provider, field) fails closed with the provider named in
    the typed refusal, and the blocked comparison names its MissingnessReason."""
    from crypto_sensor_fabric.contracts.enums import SensorFamily
    from crypto_sensor_fabric.normalization.common import (
        ProviderSemanticRegistry,
        UnknownProviderSemanticMapping,
    )
    from crypto_sensor_fabric.normalization.enums import MissingnessReason

    registry = ProviderSemanticRegistry.model_validate({"schema_version": "1.0", "mappings": []})
    with pytest.raises(UnknownProviderSemanticMapping) as excinfo:
        registry.require("GATE_FUTURES", "long_liq_usd", SensorFamily.MECHANICAL_LIQUIDATION)
    assert "GATE_FUTURES" in str(excinfo.value)
    assert MissingnessReason.SEMANTICS_BLOCKED.value == "SEMANTICS_BLOCKED"


def test_sem32_bloc1_registry_surfaces_are_untouched() -> None:
    """Q1 custody: no byte of the live Bloc 1 registry implementation or its
    config changed on disk relative to the I09 custody base."""
    import subprocess

    result = subprocess.run(
        [
            "git",
            "diff",
            "1f7a0fa6ab55b022ce3a9900717b6d3c657cc477",
            "--",
            "quant-lab/src/crypto_sensor_fabric/registry",
            "quant-lab/config/crypto_sensor_fabric",
        ],
        cwd=_QUANT_LAB.parent,
        capture_output=True,
        encoding="utf-8",
        check=False,
    )
    assert result.stdout == "", f"sealed Bloc 1 surface changed:\n{result.stdout}"


def test_sem33_the_eight_provider_schema_is_the_live_provider_set() -> None:
    """Q6 structural contract: the eight-provider schema I09 validates against
    is the live, consumed PROVIDER_IDS tuple -- reused, never forked."""
    from crypto_sensor_fabric.normalization.common import ProviderSemanticMapping
    from crypto_sensor_fabric.registry.provider_registry import PROVIDER_IDS

    assert len(PROVIDER_IDS) == 8
    adapter = TypeAdapter(ProviderSemanticMapping)
    for provider in PROVIDER_IDS:
        adapter.validate_python({**_full_mapping().model_dump(mode="json"), "provider": provider})


def test_sem34_no_methodology_row_is_invented_for_the_unresolved_ids() -> None:
    """Q2/stop 9: the live methodology config still carries the nine Bloc 1
    planning ids only -- I09 adds no config row and invents no alias."""
    from crypto_sensor_fabric.registry.methodology_registry import load_methodology_registry

    ids = set(load_methodology_registry(METHODOLOGY_YAML).methodologies)
    assert "B5_I08_UNITS_V1" not in ids
    assert "STABLECOIN_USD_PIT_V1" not in ids
    assert len(ids) == 9


def test_sem35_pure_layer_imports_nothing_heavy() -> None:
    """The three I09 modules stay pure: no network, no filesystem, no hashing,
    no wall clock inside the normalization interfaces (BOOK 03 law; the
    evidence producer owns hashing and paths)."""
    import ast

    package = _QUANT_LAB / "src" / "crypto_sensor_fabric" / "normalization" / "common"
    for module in ("methodologies.py", "semantic_registry.py", "comparability.py"):
        text = (package / module).read_text(encoding="utf-8")
        for forbidden in (
            "requests",
            "httpx",
            "socket",
            "urllib",
            "pathlib",
            "duckdb",
            "pandas",
            "hashlib",
            "uuid",
            "datetime.now",
            "time.time",
            "random",
        ):
            assert forbidden not in text, f"{module} references {forbidden}"
        ast.parse(text)


def test_sem36_condition_order_and_names_are_frozen() -> None:
    """The eight 03 §18 conditions keep their order and identity; the decision
    reports all eight verdicts in that order."""
    from crypto_sensor_fabric.normalization.common import (
        ComparabilityCondition,
        evaluate_comparability,
    )

    assert [member.value for member in ComparabilityCondition] == [
        "SENSOR_FAMILY_SAME",
        "ECONOMIC_DEFINITION_COMPATIBLE",
        "INTERVAL_SEMANTICS_COMPATIBLE",
        "UNITS_COMPATIBLE_AFTER_EXPLICIT_CONVERSION",
        "VENUE_SCOPE_KNOWN",
        "IDENTITY_RESOLVED",
        "NO_BLOCKING_QUALITY_FLAGS",
        "EQUIVALENCE_CLASS_PERMITS_COMPARISON",
    ]
    decision = evaluate_comparability(_facts("left"), _facts("right"))
    assert [verdict.condition for verdict in decision.verdicts] == list(ComparabilityCondition)
