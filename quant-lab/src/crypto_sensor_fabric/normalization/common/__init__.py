"""SENSOR-B5-I09 - common units / numeric / conversion / methodology / semantic surface.

The ``common/`` package (bloc_05/03 §21), scoped across the I08E1 and I09E1
directives:

* ``units`` (I08) -- the frozen 13-unit quantity vocabulary and the
  asset-identity law (§4);
* ``numeric`` (I08) -- the §3 precision policy: precision declared, widening
  measured, rounding absent;
* ``conversion`` (I08) -- the §9/§10 stablecoin-fiat + cross-currency
  conversion over caller-supplied PIT rate evidence (depeg-preserving,
  fail-closed);
* ``methodologies`` (I09) -- the frozen ``NormalizationMethodology`` object
  (§16), its versioned registry (07 F14) and the Bloc 1 projection adapter;
* ``semantic_registry`` (I09) -- the frozen ``ProviderSemanticMapping`` object
  (§11/§12), the §13 confidence ladder and the per-provider registry;
* ``comparability`` (I09) -- the library-level eight-condition §18 gate, whose
  condition 8 delegates to the ratified Bloc 1 ``is_poolable``.

Deliberately ABSENT from this package:

* ``envelope.py`` -- bloc_05/03 §2's full ``T1ObservationEnvelope`` needs
  I02/I06/I19-owned fields as well as I09's two, so the frozen-name composite
  stays unexported exactly as the I01 base layer records (I09E1 directive
  BOOK 00 Q4: I09 unblocks the envelope, it does not release it).  I09's two
  fields are typed by ``MethodologyRef`` plus the registry version tokens;
* ``missingness.py`` -- the §14/§12 null/zero laws and the thirteen-member
  vocabulary already live in the ratified I01 base
  (``normalization.enums`` / ``normalization.models``); re-declaring them
  here would fork a single source of truth, so I09 imports and reuses.

Only the symbols below are public contract for this package.  The top-level
``crypto_sensor_fabric.normalization`` surface stays the ratified 24 I01
symbols; I08 and I09 names are reached only through
``...normalization.common``.

No network, no wall clock, no filesystem access: value in, answer out.  The
committed configuration is read by callers (tests, evidence producer) as TEXT.
"""

from __future__ import annotations

from .comparability import (
    ComparableFieldFacts,
    ComparabilityCondition,
    ComparabilityDecision,
    ConditionVerdict,
    evaluate_comparability,
)
from .conversion import (
    METHODOLOGY_VERSION,
    ConversionRateObservation,
    CrossCurrencyResult,
    StablecoinConversionResult,
    convert_stablecoin_to_usd,
    cross_convert_via_usd,
)
from .methodologies import (
    MethodologyRef,
    NormalizationMethodology,
    NormalizationMethodologyRegistry,
    UnknownNormalizationMethodology,
    parse_normalization_methodology_registry_yaml,
    project_planning_methodology,
    serialize_normalization_methodology_registry_yaml,
)
from .numeric import (
    PrecisionRecord,
    decimal_places,
    precision_widened,
)
from .semantic_registry import (
    PENDING_EVIDENCE_REFERENCE,
    IntervalDataScope,
    ProviderSemanticMapping,
    ProviderSemanticRegistry,
    SemanticConfidence,
    UnknownProviderSemanticMapping,
    admits_critical_t1_use,
    is_first_party_grade,
    parse_provider_semantic_registry_yaml,
    project_planning_mapping,
    serialize_provider_semantic_registry_yaml,
)
from .units import (
    ASSET_IDENTITY_REQUIRED,
    SELF_IDENTIFYING,
    CanonicalQuantityUnit,
    QuantityUnitIdentity,
)

__all__ = [
    "ASSET_IDENTITY_REQUIRED",
    "METHODOLOGY_VERSION",
    "PENDING_EVIDENCE_REFERENCE",
    "SELF_IDENTIFYING",
    "ComparableFieldFacts",
    "CanonicalQuantityUnit",
    "ComparabilityCondition",
    "ComparabilityDecision",
    "ConditionVerdict",
    "ConversionRateObservation",
    "CrossCurrencyResult",
    "IntervalDataScope",
    "MethodologyRef",
    "NormalizationMethodology",
    "NormalizationMethodologyRegistry",
    "PrecisionRecord",
    "ProviderSemanticMapping",
    "ProviderSemanticRegistry",
    "QuantityUnitIdentity",
    "SemanticConfidence",
    "StablecoinConversionResult",
    "UnknownNormalizationMethodology",
    "UnknownProviderSemanticMapping",
    "admits_critical_t1_use",
    "convert_stablecoin_to_usd",
    "cross_convert_via_usd",
    "decimal_places",
    "evaluate_comparability",
    "is_first_party_grade",
    "parse_normalization_methodology_registry_yaml",
    "parse_provider_semantic_registry_yaml",
    "precision_widened",
    "project_planning_mapping",
    "project_planning_methodology",
    "serialize_normalization_methodology_registry_yaml",
    "serialize_provider_semantic_registry_yaml",
]
