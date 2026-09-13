"""Semantic-equivalence registry tests (B1-T40 .. B1-T43)."""

from __future__ import annotations

import pytest
from crypto_sensor_fabric.contracts.enums import (
    SemanticEquivalence,
    SensorFamily,
)
from crypto_sensor_fabric.registry.semantic_equivalence import (
    EquivalenceMapping,
    is_poolable,
    load_semantic_equivalence,
)
from pydantic import ValidationError

DEFAULT_EQUIVALENCE = load_semantic_equivalence()


def _mapping(**overrides) -> dict:
    payload = {
        "provider": "P",
        "source_metric": "metric",
        "canonical_sensor": SensorFamily.MECHANICAL_LIQUIDATION,
        "canonical_field": "field",
        "equivalence": SemanticEquivalence.NORMALIZABLE_COMPARABLE,
        "methodology_id": "METH_V1",
        "evidence_reference": "PROBE-1",
        "version": "1",
        "source_definition": "some definition",
        "transformation_method": "some method",
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# B1-T40 — equivalence required
# ---------------------------------------------------------------------------


def test_t40_equivalence_required():
    with pytest.raises(ValidationError):
        EquivalenceMapping.model_validate(_mapping(equivalence=None))


def test_t40_equivalence_must_be_controlled_value():
    with pytest.raises(ValidationError):
        EquivalenceMapping.model_validate(_mapping(equivalence="SOMEHOW_SAME"))


@pytest.mark.parametrize(
    "value",
    [
        SemanticEquivalence.EXACT_EQUIVALENT,
        SemanticEquivalence.NORMALIZABLE_COMPARABLE,
        SemanticEquivalence.CORROBORATION_ONLY,
        SemanticEquivalence.NOT_COMPARABLE,
    ],
)
def test_t40_all_frozen_classes_validate(value: SemanticEquivalence):
    mapping = EquivalenceMapping.model_validate(_mapping(equivalence=value))
    assert mapping.equivalence is value


# ---------------------------------------------------------------------------
# B1-T41 — comparable mapping needs method
# ---------------------------------------------------------------------------


def test_t41_comparable_requires_methodology_id():
    with pytest.raises(ValidationError, match="methodology_id"):
        EquivalenceMapping.model_validate(
            _mapping(equivalence=SemanticEquivalence.NORMALIZABLE_COMPARABLE, methodology_id=None)
        )


def test_t41_comparable_with_methodology_validates():
    mapping = EquivalenceMapping.model_validate(
        _mapping(
            equivalence=SemanticEquivalence.NORMALIZABLE_COMPARABLE,
            methodology_id="LIQ_USD_NATIVE_PROVIDER_V1",
        )
    )
    assert mapping.methodology_id == "LIQ_USD_NATIVE_PROVIDER_V1"


def test_t41_corroboration_does_not_need_methodology():
    mapping = EquivalenceMapping.model_validate(
        _mapping(equivalence=SemanticEquivalence.CORROBORATION_ONLY, methodology_id=None)
    )
    assert mapping.equivalence is SemanticEquivalence.CORROBORATION_ONLY


# ---------------------------------------------------------------------------
# B1-T42 — corroboration cannot be pooled by default
# ---------------------------------------------------------------------------


def test_t42_corroboration_not_poolable():
    assert not is_poolable(SemanticEquivalence.CORROBORATION_ONLY)


def test_t42_not_comparable_not_poolable():
    assert not is_poolable(SemanticEquivalence.NOT_COMPARABLE)


@pytest.mark.parametrize(
    "value", [SemanticEquivalence.EXACT_EQUIVALENT, SemanticEquivalence.NORMALIZABLE_COMPARABLE]
)
def test_t42_exact_and_normalizable_are_poolable(value: SemanticEquivalence):
    assert is_poolable(value)


# ---------------------------------------------------------------------------
# B1-T43 — exact equivalence requires evidence
# ---------------------------------------------------------------------------


def test_t43_exact_requires_evidence():
    with pytest.raises(ValidationError, match="evidence_reference"):
        EquivalenceMapping.model_validate(
            _mapping(equivalence=SemanticEquivalence.EXACT_EQUIVALENT, evidence_reference=None)
        )


def test_t43_exact_with_evidence_validates():
    mapping = EquivalenceMapping.model_validate(
        _mapping(
            equivalence=SemanticEquivalence.EXACT_EQUIVALENT,
            evidence_reference="PROBE-2024-001",
        )
    )
    assert mapping.evidence_reference == "PROBE-2024-001"


# ---------------------------------------------------------------------------
# Default registry integrity
# ---------------------------------------------------------------------------


def test_default_registry_loads():
    assert len(DEFAULT_EQUIVALENCE.mappings) >= 4


def test_default_mappings_all_carry_evidence_reference():
    for mapping in DEFAULT_EQUIVALENCE.mappings:
        assert mapping.evidence_reference, mapping.provider


def test_default_mappings_with_methodology_are_registered():
    from crypto_sensor_fabric.registry.methodology_registry import (
        load_methodology_registry,
    )

    methodologies = load_methodology_registry()
    for mapping in DEFAULT_EQUIVALENCE.mappings:
        if mapping.methodology_id:
            assert mapping.methodology_id in methodologies.methodologies, (
                f"{mapping.provider}/{mapping.source_metric} references unknown "
                f"methodology {mapping.methodology_id}"
            )


def test_default_mappings_are_provisional_not_exact():
    # No EXACT_EQUIVALENT may be claimed before probes produce evidence (T43).
    for mapping in DEFAULT_EQUIVALENCE.mappings:
        assert mapping.equivalence is not SemanticEquivalence.EXACT_EQUIVALENT
