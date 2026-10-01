"""Book 6 metric definitions, measurement methodologies, and coverage.

A metric NAME is not a definition. ``MetricDefinition`` binds a name to a
semantic definition, a subject domain, a unit, a measurement category, a
window rule, an aggregation rule, a denominator rule, permitted source families,
required evidence, a methodology identity, a comparability class and an explicit
architecture applicability — so "active addresses" cannot exist as a bare label
(ratified plan v0.2 §3; grammar v0.1 §3.1).

``MeasurementMethodology`` carries the versioned HOW (formula, parameters,
window, filters, denominator rule, source selection, identity rule). Normalization
is deliberately NOT an untyped flag on either object: it is the separate
``NormalizationRule`` contract (ratified D6M-2 = B).

``CoverageObservation`` records an observed coverage fraction and its basis. It
deliberately carries NO sufficiency verdict: coverage sufficiency is rule-gated
(``CoverageSufficiencyRule``) and no such rule is ratified, so no numeric value
here can ever assert SUFFICIENT / INSUFFICIENT / DATA_COMPLETE.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Final

from pydantic import ConfigDict, Field, model_validator

from .book6_frozen import Book6FrozenModel

from .book6_grammar import (
    MeasurementCategory,
    MeasurementRole,
    SubjectDomain,
    WindowClass,
)


class MetricDefinitionError(ValueError):
    """A metric definition is incomplete or internally inconsistent."""


class CoverageSufficiencyRuleError(ValueError):
    """A coverage-sufficiency rule is malformed or claims its own ratification."""


class SourceFamily(str, Enum):
    """Permitted evidence source families for a metric (grammar v0.1 §3.2)."""

    NATIVE_CHAIN = "NATIVE_CHAIN"
    OFFICIAL_PROTOCOL = "OFFICIAL_PROTOCOL"
    INDEPENDENT_INDEXER = "INDEPENDENT_INDEXER"
    SECONDARY_ANALYTICS = "SECONDARY_ANALYTICS"
    BOOK5_CAPITAL_RECORD = "BOOK5_CAPITAL_RECORD"
    BOOK4_DEPENDENCY_GRAPH = "BOOK4_DEPENDENCY_GRAPH"
    OFFCHAIN_REPOSITORY = "OFFCHAIN_REPOSITORY"


class AggregationSemantics(str, Enum):
    """How repeated observations of the same window aggregate."""

    NONE = "NONE"
    SUM = "SUM"
    MEAN = "MEAN"
    LAST = "LAST"
    DISTRIBUTION = "DISTRIBUTION"


class ComparabilityClass(str, Enum):
    """Cohort family within which a metric is comparable (grammar v0.1 §3.2).

    A class narrower than ``CROSS_ARCHITECTURE`` is the mechanism that makes
    most cross-architecture comparisons structurally impossible.
    """

    CHAIN_WITHIN_FAMILY = "CHAIN_WITHIN_FAMILY"
    PROTOCOL_WITHIN_MODEL = "PROTOCOL_WITHIN_MODEL"
    CAPITAL_SAME_UNIT = "CAPITAL_SAME_UNIT"
    DEVELOPER_OFFCHAIN = "DEVELOPER_OFFCHAIN"
    CROSS_ARCHITECTURE = "CROSS_ARCHITECTURE"
    NOT_COMPARABLE = "NOT_COMPARABLE"


class DenominatorRule(str, Enum):
    """How a metric obtains its denominator (grammar v0.1 §4)."""

    NOT_APPLICABLE = "NOT_APPLICABLE"
    OBSERVED_MEASUREMENT = "OBSERVED_MEASUREMENT"
    COHORT_TOTAL = "COHORT_TOTAL"


class MeasurementMethodology(Book6FrozenModel):
    """Versioned HOW of a measurement (grammar v0.1 §7).

    A value without methodology identity is incomplete: the same metric name
    under a different methodology is a different comparable observation.

    R1: a methodology is structural Book 6 authority and must be REGISTERED in
    ``Book6MethodologyRegistry`` before it may authorize anything — a bare
    ``"methodology:whatever"`` string is no longer authority. Two fields make
    that binding checkable rather than documentary:

    - ``input_methodology_refs`` — the methodology identities this methodology
      is defined OVER, so a normalization rule can be refused when its
      methodology does not match the inputs it claims to normalize;
    - ``authorized_corpus_row_ids`` — the exact false-comparison corpus rows
      this methodology is authorized to license.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    methodology_ref: str = Field(min_length=1)
    version: str = Field(min_length=1)
    formula: str = Field(min_length=1)
    parameters: tuple[tuple[str, str], ...] = ()
    window_rule: str = Field(min_length=1)
    filters: tuple[str, ...] = ()
    denominator_rule: str = Field(min_length=1)
    source_selection: str = Field(min_length=1)
    identity_rule: str = Field(min_length=1)
    #: Methodology identities (``ref@version``) this methodology consumes.
    input_methodology_refs: tuple[str, ...] = ()
    #: False-comparison corpus row ids this methodology is authorized for.
    authorized_corpus_row_ids: tuple[str, ...] = ()

    @property
    def identity(self) -> str:
        """Fully-qualified methodology identity (ref + version)."""

        return f"{self.methodology_ref}@{self.version}"

    def authorizes_row(self, corpus_row_id: str) -> bool:
        """Whether this methodology declares authority for a corpus row."""

        return corpus_row_id in self.authorized_corpus_row_ids


class MetricDefinition(Book6FrozenModel):
    """A complete, audited metric definition (grammar v0.1 §3)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    semantic_definition: str = Field(min_length=8)
    subject_domain: SubjectDomain
    category: MeasurementCategory
    unit: str = Field(min_length=1)
    role: MeasurementRole
    window_class: WindowClass
    aggregation: AggregationSemantics
    denominator_rule: DenominatorRule
    allowed_source_families: tuple[SourceFamily, ...] = Field(min_length=1)
    required_evidence_semantics: str = Field(min_length=8)
    methodology: MeasurementMethodology
    comparability_class: ComparabilityClass
    applies_to_architectures: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _check_consistency(self) -> "MetricDefinition":
        if self.denominator_rule is not DenominatorRule.NOT_APPLICABLE:
            if self.category is not MeasurementCategory.RATIO:
                raise MetricDefinitionError(
                    "a denominator rule on a non-ratio metric contradicts the "
                    "denominator doctrine"
                )
        elif self.category is MeasurementCategory.RATIO:
            raise MetricDefinitionError(
                "a ratio metric must declare how it obtains its denominator"
            )
        if self.comparability_class is ComparabilityClass.CROSS_ARCHITECTURE:
            if len(self.applies_to_architectures) > 1:
                raise MetricDefinitionError(
                    "a cross-architecture comparability class must not be scoped "
                    "to specific architecture families"
                )
        return self

    def applies_to(self, architecture_family: str) -> bool:
        """Whether this metric is natively applicable to an architecture family.

        An empty ``applies_to_architectures`` means the metric is architecture
        agnostic. A non-empty tuple is an explicit allow-list: a subject outside
        it is ``NOT_SUPPORTED``, never zero.
        """

        if not self.applies_to_architectures:
            return True
        return architecture_family in self.applies_to_architectures


class CoverageObservation(Book6FrozenModel):
    """Observed population coverage plus its basis — never a sufficiency verdict.

    ``observed_fraction`` records what was seen. ``sufficiency_rule_ref`` is the
    ONLY place sufficiency may come from, and it is empty until an operator
    ratifies a coverage-sufficiency rule. There is no ``sufficiency`` field:
    a numeric coverage value must never be able to assert SUFFICIENT,
    INSUFFICIENT or DATA_COMPLETE (plan v0.2 §5; state-vector v0.2 §5).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    measurement_id: str = Field(min_length=1)
    observed_fraction: float = Field(ge=0.0, le=1.0)
    basis: str = Field(min_length=8)
    sufficiency_rule_ref: str | None = None
    valid_time: datetime

    @property
    def names_a_sufficiency_rule(self) -> bool:
        """Whether this observation NAMES a sufficiency rule ref.

        Deliberately named for what it is: a structural string predicate with
        NO authority. R1 removed the old ``sufficiency_known`` property, which
        returned ``True`` for any non-empty string and therefore let a free
        string assert sufficiency. Whether a named rule is actually ratified
        and in scope is decided by ``CoverageRuleRegistry`` at decision time,
        never by this object.
        """

        return bool(self.sufficiency_rule_ref)


class CoverageRuleRatificationStatus(str, Enum):
    """Per-rule coverage-sufficiency ratification status (D6M-3 = A).

    R1: this is an enum rather than a bare ``str``, and ``RATIFIED`` may not be
    set at construction at all. Authority lives in the registry's ratification
    ledger, so a caller cannot manufacture a ratified rule by setting a field.
    """

    UNRATIFIED = "UNRATIFIED"
    RATIFIED = "RATIFIED"
    SUPERSEDED = "SUPERSEDED"


class CoverageSufficiencyRule(Book6FrozenModel):
    """A candidate coverage-sufficiency rule. None is ratified.

    The object exists so the contract can be represented without smuggling a
    threshold into a numeric field. R1: it may only be CONSTRUCTED as
    ``UNRATIFIED`` — ratification is a registry decision recorded by
    ``CoverageRuleRegistry.ratify``, so ``model_copy``-forged or directly
    constructed ``RATIFIED`` rules carry no authority.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    rule_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    required_fraction: float = Field(ge=0.0, le=1.0)
    scope_metric_id: str = Field(min_length=1)
    rationale: str = Field(min_length=8)
    status: CoverageRuleRatificationStatus = CoverageRuleRatificationStatus.UNRATIFIED

    @model_validator(mode="after")
    def _check_not_self_ratified(self) -> "CoverageSufficiencyRule":
        if self.status is not CoverageRuleRatificationStatus.UNRATIFIED:
            raise CoverageSufficiencyRuleError(
                f"coverage sufficiency rule {self.rule_id} may not declare itself "
                f"{self.status.value}; ratification is an individual operator "
                f"decision recorded by the registry, never a field on the rule"
            )
        return self


#: The five ratified metric families and their subject domains (plan v0.2 §28).
#: This is SCHEMA capability only — there is no production collector, no
#: acquisition path and no default metric in any family. A family is a slot for
#: fully specified definitions, never a reason to invent one.
METRIC_FAMILY_BY_SUBJECT_DOMAIN: Final[dict[SubjectDomain, str]] = {
    SubjectDomain.CHAIN: "6A.1",
    SubjectDomain.PROTOCOL: "6A.2",
    SubjectDomain.TOKEN: "6A.3",
    SubjectDomain.CAPITAL: "6A.4",
    SubjectDomain.DEVELOPER: "6A.5",
}

#: The ratified family identifiers, for evidence and registry introspection.
RATIFIED_METRIC_FAMILIES: Final[tuple[str, ...]] = tuple(
    sorted(METRIC_FAMILY_BY_SUBJECT_DOMAIN.values())
)


#: The canonical invariant asserted by the accepted implementation.
COVERAGE_OBSERVATION_IS_NOT_SUFFICIENCY: Final[bool] = True
NO_DEFAULT_METRIC_EXISTS: Final[bool] = True
NOT_SUPPORTED_IS_NOT_ZERO: Final[bool] = True


__all__ = [
    "AggregationSemantics",
    "COVERAGE_OBSERVATION_IS_NOT_SUFFICIENCY",
    "ComparabilityClass",
    "CoverageObservation",
    "CoverageRuleRatificationStatus",
    "CoverageSufficiencyRule",
    "CoverageSufficiencyRuleError",
    "DenominatorRule",
    "METRIC_FAMILY_BY_SUBJECT_DOMAIN",
    "MeasurementMethodology",
    "MetricDefinition",
    "MetricDefinitionError",
    "NOT_SUPPORTED_IS_NOT_ZERO",
    "NO_DEFAULT_METRIC_EXISTS",
    "RATIFIED_METRIC_FAMILIES",
    "SourceFamily",
]
