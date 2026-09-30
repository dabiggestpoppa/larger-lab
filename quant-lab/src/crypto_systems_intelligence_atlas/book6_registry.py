"""Book 6 measurement registry — deterministic, offline, in-memory.

Five separated stores (ratified plan v0.2 §29): definitions, methodologies,
measurement records, normalization rules, state rules. No database, no graph
database, no scheduler, no network.

The registry inherits the Book 4 / Book 5 lesson literally:

    REGISTERED THEN != AUTHORITATIVE NOW

``register`` accepts a record without judging its authority; ``resolve_current``
re-resolves it against live Book 2 state at the moment of use, so a measurement
whose cited Book 2 claim decayed stops being authoritative while the record itself
stays queryable as history.
"""

from __future__ import annotations

from typing import Final

from .book6_definitions import CoverageObservation, MetricDefinition
from .book6_normalization import NormalizationRule
from .book6_provenance import Book6Provenance, Book6ProvenanceError
from .book6_records import MeasurementObservation, validate_against_definition
from .book6_states import StateRule, StateRuleRegistry


class Book6RegistryError(ValueError):
    """A Book 6 registry operation is invalid."""


class Book6MeasurementRegistry:
    """Separated deterministic stores with live authority resolution."""

    def __init__(self, provenance: Book6Provenance) -> None:
        self._provenance = provenance
        self._definitions: dict[str, MetricDefinition] = {}
        self._coverage: dict[str, CoverageObservation] = {}
        self._measurements: dict[str, MeasurementObservation] = {}
        self._measurement_order: list[str] = []
        self._normalization_rules: dict[str, NormalizationRule] = {}
        self.state_rules = StateRuleRegistry()

    # -- registration (proves nothing about current authority) ---------------

    def register_definition(self, definition: MetricDefinition) -> MetricDefinition:
        if definition.metric_id in self._definitions:
            raise Book6RegistryError(f"metric {definition.metric_id} already registered")
        self._definitions[definition.metric_id] = definition
        return definition

    def register_coverage(self, coverage: CoverageObservation) -> CoverageObservation:
        if coverage.measurement_id in self._coverage:
            raise Book6RegistryError(
                f"coverage for {coverage.measurement_id} already registered"
            )
        self._coverage[coverage.measurement_id] = coverage
        return coverage

    def register_measurement(self, observation: MeasurementObservation) -> MeasurementObservation:
        """Register a measurement, checking its declared definition shape.

        Registration-time checking is necessary but NOT sufficient: authority is
        re-resolved live by ``resolve_current``.
        """

        if observation.measurement_id in self._measurements:
            raise Book6RegistryError(
                f"measurement {observation.measurement_id} already registered"
            )
        definition = self._definitions.get(observation.metric_definition_ref)
        if definition is None:
            raise Book6RegistryError(
                f"metric definition {observation.metric_definition_ref} is not "
                f"registered; a measurement may not define its own metric"
            )
        validate_against_definition(observation, definition)
        self._measurements[observation.measurement_id] = observation
        self._measurement_order.append(observation.measurement_id)
        return observation

    def register_normalization_rule(self, rule: NormalizationRule) -> NormalizationRule:
        if rule.normalization_rule_id in self._normalization_rules:
            raise Book6RegistryError(
                f"normalization rule {rule.normalization_rule_id} already registered"
            )
        self._normalization_rules[rule.normalization_rule_id] = rule
        return rule

    def register_state_rule(self, rule: StateRule) -> StateRule:
        return self.state_rules.register(rule)

    # -- structural accessors (never authority) ------------------------------

    def registered_measurement(self, measurement_id: str) -> MeasurementObservation:
        try:
            return self._measurements[measurement_id]
        except KeyError as exc:
            raise Book6RegistryError(
                f"measurement {measurement_id} is not registered"
            ) from exc

    def registered_refs(self) -> tuple[str, ...]:
        """Deterministic structural snapshot of registered measurement ids."""

        return tuple(self._measurement_order)

    def measurement_history(self, measurement_id: str) -> tuple[MeasurementObservation, ...]:
        """All observations that supersede-or-are the given measurement."""

        root = self.registered_measurement(measurement_id)
        chain = [root]
        while True:
            successors = [
                obs
                for obs in self._measurements.values()
                if obs.supersedes_measurement_id == chain[-1].measurement_id
            ]
            if not successors:
                break
            if len(successors) > 1:
                raise Book6RegistryError(
                    f"measurement {chain[-1].measurement_id} has multiple "
                    f"successors; supersession must be linear"
                )
            chain.append(successors[0])
        return tuple(chain)

    # -- authority-bearing resolution ---------------------------------------

    def resolve_current(self, measurement_id: str) -> MeasurementObservation:
        """Resolve a measurement's CURRENT authority against live Book 2 state.

        Fails closed when any cited Book 2 claim is unknown, non-current, or has
        detached evidence. The record itself is never mutated or removed — a
        decayed measurement remains registered history.
        """

        observation = self.registered_measurement(measurement_id)
        if not observation.is_value_bearing:
            return observation
        try:
            self._provenance.resolve_source_claim_refs(
                observation.source_claim_refs, require_current=True
            )
        except Book6ProvenanceError as exc:
            raise Book6RegistryError(
                f"measurement {measurement_id} has no current Book 2 authority: "
                f"{exc}"
            ) from exc
        return observation

    def is_authoritative_now(self, measurement_id: str) -> bool:
        """Live currentness check that never raises (structural query)."""

        try:
            self.resolve_current(measurement_id)
        except (Book6RegistryError, Book6ProvenanceError):
            return False
        return True

    def coverage_of(self, measurement_id: str) -> CoverageObservation | None:
        return self._coverage.get(measurement_id)

    def normalized_rule(self, rule_id: str) -> NormalizationRule:
        try:
            return self._normalization_rules[rule_id]
        except KeyError as exc:
            raise Book6RegistryError(
                f"normalization rule {rule_id} is not registered"
            ) from exc

    def definition(self, metric_id: str) -> MetricDefinition:
        try:
            return self._definitions[metric_id]
        except KeyError as exc:
            raise Book6RegistryError(f"metric {metric_id} is not registered") from exc


#: Canonical invariants asserted by the accepted implementation.
REGISTRATION_IS_NOT_AUTHORITY: Final[bool] = True
OFFLINE_IN_MEMORY_ONLY: Final[bool] = True


__all__ = [
    "Book6MeasurementRegistry",
    "Book6RegistryError",
    "OFFLINE_IN_MEMORY_ONLY",
    "REGISTRATION_IS_NOT_AUTHORITY",
]
